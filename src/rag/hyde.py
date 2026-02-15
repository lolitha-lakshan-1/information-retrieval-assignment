"""
HyDE (Hypothetical Document Embeddings) Query Generator
Generates hypothetical ideal answers to bridge the semantic gap between
strategic language and operational language.
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from src.config import OPENAI_API_KEY, LLM_MODEL, EMBEDDING_MODEL


HYDE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert in strategic planning and organizational alignment.
Given a strategic objective or query about a university's strategic plan alignment,
generate a HYPOTHETICAL ideal action plan response that would perfectly answer the query.

The hypothetical response should:
- Describe specific, concrete actions that would ideally support the objective
- Include relevant KPIs, timelines, and responsible parties
- Be written in the same style as an organizational action plan
- Be approximately 200-300 words
- Sound like a real action plan document, not a summary

This hypothetical document will be used for semantic search, so make it rich with
relevant terms and concepts that would appear in actual action plan entries."""),
    ("human", "{query}")
])


MULTI_QUERY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at reformulating queries for information retrieval.
Given a query about strategic plan alignment, generate 3 alternative versions of the query
that might retrieve different relevant information.

Each query should approach the topic from a slightly different angle:
1. A more specific, detailed version
2. A broader, conceptual version  
3. A version focusing on metrics/KPIs/outcomes

Return ONLY the 3 queries, one per line, numbered 1-3."""),
    ("human", "{query}")
])


def generate_hyde_document(query: str) -> str:
    """
    Generate a hypothetical document for a given query using HyDE.
    
    Args:
        query: The user's query or strategic objective description
        
    Returns:
        Hypothetical document text
    """
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
    )
    
    chain = HYDE_PROMPT | llm
    response = chain.invoke({"query": query})
    return response.content


def get_hyde_embedding(query: str) -> list[float]:
    """
    Generate HyDE embedding for a query.
    
    Process:
    1. Generate hypothetical document from query
    2. Embed the hypothetical document
    3. Return the embedding (which captures operational language)
    
    Args:
        query: The user's query
        
    Returns:
        Embedding vector for the hypothetical document
    """
    hypothetical_doc = generate_hyde_document(query)
    
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    
    return embeddings.embed_query(hypothetical_doc)


def generate_multi_queries(query: str) -> list[str]:
    """
    Generate multiple query variants for broader retrieval.
    
    Args:
        query: Original query
        
    Returns:
        List of 3-4 query variants (including original)
    """
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.3,
        openai_api_key=OPENAI_API_KEY,
    )
    
    chain = MULTI_QUERY_PROMPT | llm
    response = chain.invoke({"query": query})
    
    # Parse numbered queries
    variants = [query]  # Include original
    for line in response.content.strip().split("\n"):
        line = line.strip()
        if line and len(line) > 5:
            # Remove numbering
            cleaned = line.lstrip("0123456789.-) ").strip()
            if cleaned:
                variants.append(cleaned)
    
    return variants[:4]  # Cap at 4 total
