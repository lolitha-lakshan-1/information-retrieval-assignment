"""
Vector Store Module
Manages ChromaDB collections for storing and retrieving document chunks.
"""
import chromadb
from chromadb.utils import embedding_functions
from src.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, CHROMA_DIR,
    CHROMA_COLLECTION_STRATEGIC, CHROMA_COLLECTION_ACTION, CHROMA_COLLECTION_COMBINED,
)


def get_chroma_client() -> chromadb.PersistentClient:
    """Create or connect to persistent ChromaDB instance."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_embedding_function():
    """Get OpenAI embedding function for Chroma."""
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL,
    )


def get_or_create_collection(client: chromadb.PersistentClient, name: str):
    """Get or create a ChromaDB collection with OpenAI embeddings."""
    ef = get_embedding_function()
    return client.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_chunks(chunks: list[dict], collection_name: str) -> int:
    """
    Ingest a list of chunks into a ChromaDB collection.
    
    Args:
        chunks: List of {'text': str, 'metadata': dict}
        collection_name: Name of the Chroma collection
        
    Returns:
        Number of chunks ingested
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    
    # Prepare batch data
    ids = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{collection_name}_{chunk['metadata'].get('chunk_strategy', 'unknown')}_{i}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        # Ensure all metadata values are strings (Chroma requirement)
        meta = {k: str(v) for k, v in chunk["metadata"].items()}
        metadatas.append(meta)
    
    # Ingest in batches of 100
    batch_size = 100
    total_batches = (len(ids) + batch_size - 1) // batch_size
    
    import logging
    logger = logging.getLogger("isps.vector_store")
    logger.info(f"Ingesting {len(ids)} chunks into '{collection_name}' in {total_batches} batches")
    
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        batch_num = (start // batch_size) + 1
        try:
            logger.info(f"  Batch {batch_num}/{total_batches}: items {start} to {min(end, len(ids))}...")
            collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
            logger.info(f"  Batch {batch_num} success")
        except Exception as e:
            logger.error(f"  Batch {batch_num} failed: {e}")
            raise e
    
    return len(ids)


def ingest_all_chunks(
    strategic_chunks: list[dict],
    action_chunks: list[dict],
) -> dict[str, int]:
    """
    Ingest chunks from both documents into their respective collections
    and a combined collection.
    
    Returns:
        Dict with counts per collection
    """
    counts = {}
    
    # Individual collections
    counts["strategic_plan"] = ingest_chunks(
        strategic_chunks, CHROMA_COLLECTION_STRATEGIC
    )
    counts["action_plan"] = ingest_chunks(
        action_chunks, CHROMA_COLLECTION_ACTION
    )
    
    # Combined collection
    all_chunks = strategic_chunks + action_chunks
    counts["combined"] = ingest_chunks(
        all_chunks, CHROMA_COLLECTION_COMBINED
    )
    
    return counts


def query_collection(
    collection_name: str,
    query_text: str,
    n_results: int = 10,
    where_filter: dict | None = None,
) -> dict:
    """
    Query a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to query
        query_text: Text to search for
        n_results: Number of results to return
        where_filter: Optional metadata filter (e.g. {"doc_type": "action_plan"})
        
    Returns:
        ChromaDB query results dict
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    
    kwargs = {
        "query_texts": [query_text],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        kwargs["where"] = where_filter
    
    return collection.query(**kwargs)


def get_collection_stats(collection_name: str) -> dict:
    """Get statistics about a ChromaDB collection."""
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    count = collection.count()
    return {
        "name": collection_name,
        "count": count,
    }


def clear_all_collections():
    """Delete all collections (for re-ingestion)."""
    client = get_chroma_client()
    for name in [CHROMA_COLLECTION_STRATEGIC, CHROMA_COLLECTION_ACTION, CHROMA_COLLECTION_COMBINED]:
        try:
            client.delete_collection(name)
        except Exception:
            pass
