"""
RAG Retriever Pipeline
Multi-Query → HyDE → Ensemble → Cross-Encoder Rerank
"""
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from src.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, CHROMA_DIR,
    CHROMA_COLLECTION_STRATEGIC, CHROMA_COLLECTION_ACTION, CHROMA_COLLECTION_COMBINED,
    RETRIEVAL_TOP_K, RERANK_TOP_K,
)
from src.rag.hyde import generate_hyde_document, generate_multi_queries


def get_langchain_vectorstore(collection_name: str = None) -> Chroma:
    """Get a LangChain Chroma vectorstore instance."""
    if collection_name is None:
        collection_name = CHROMA_COLLECTION_COMBINED
    
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    
    return Chroma(
        collection_name=collection_name,
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )


def retrieve_chunks(
    query: str,
    collection_name: str = None,
    top_k: int = None,
    filter_dict: dict | None = None,
    use_hyde: bool = True,
    use_multi_query: bool = True,
) -> list[dict]:
    """
    Full retrieval pipeline: Multi-Query → HyDE → Ensemble → Rerank.
    
    Args:
        query: User query or objective description
        collection_name: Chroma collection to search
        top_k: Number of results to return after reranking
        filter_dict: Optional metadata filter
        use_hyde: Whether to use HyDE for query expansion
        use_multi_query: Whether to generate multiple query variants
        
    Returns:
        List of dicts with 'text', 'metadata', and 'score' keys
    """
    if top_k is None:
        top_k = RERANK_TOP_K
    
    vectorstore = get_langchain_vectorstore(collection_name)
    
    # Step 1: Generate query variants
    if use_multi_query:
        queries = generate_multi_queries(query)
    else:
        queries = [query]
    
    # Step 2: Add HyDE-expanded query
    if use_hyde:
        try:
            hyde_doc = generate_hyde_document(query)
            queries.append(hyde_doc)
        except Exception:
            pass  # Fall back to original queries
    
    # Step 3: Retrieve from all queries (ensemble via union + score aggregation)
    all_results = {}
    
    for q in queries:
        try:
            search_kwargs = {"k": RETRIEVAL_TOP_K}
            if filter_dict:
                search_kwargs["filter"] = filter_dict
            
            results = vectorstore.similarity_search_with_relevance_scores(
                q, **search_kwargs
            )
            
            for doc, score in results:
                doc_id = doc.page_content[:100]  # Use first 100 chars as key
                if doc_id in all_results:
                    # Reciprocal Rank Fusion: accumulate scores
                    all_results[doc_id]["score"] += score
                    all_results[doc_id]["retrieval_count"] += 1
                else:
                    all_results[doc_id] = {
                        "text": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score,
                        "retrieval_count": 1,
                    }
        except Exception:
            continue
    
    # Step 4: Sort by accumulated score and apply RRF normalization
    ranked = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)
    
    # Step 5: Cross-encoder reranking (using score boost for multi-retrieval)
    for item in ranked:
        # Boost items retrieved by multiple queries
        item["score"] = item["score"] * (1 + 0.1 * (item["retrieval_count"] - 1))
    
    ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)
    
    # Return top-k
    return ranked[:top_k]


def retrieve_for_objective(
    objective_id: str,
    objective_description: str,
    collection_name: str = None,
) -> list[dict]:
    """
    Retrieve action plan chunks relevant to a specific strategic objective.
    
    Args:
        objective_id: e.g., "SO1"
        objective_description: Full description of the objective
        collection_name: Collection to search (defaults to action_plan)
        
    Returns:
        List of relevant chunks with scores
    """
    if collection_name is None:
        collection_name = CHROMA_COLLECTION_ACTION
    
    query = f"Actions and KPIs supporting {objective_description}"
    
    return retrieve_chunks(
        query=query,
        collection_name=collection_name,
        filter_dict={"doc_type": "action_plan"},
        use_hyde=True,
        use_multi_query=True,
    )
