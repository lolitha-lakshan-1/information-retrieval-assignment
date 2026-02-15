"""
Semantic Chunker
Splits text based on embedding similarity between consecutive sentences.
Groups semantically related content together.
"""
import re
from langchain_openai import OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from src.config import OPENAI_API_KEY, EMBEDDING_MODEL, SEMANTIC_BREAKPOINT_PERCENTILE


def _extract_objective_id(text: str) -> str:
    """Extract strategic objective ID from chunk text."""
    patterns = [
        r"STRATEGIC OBJECTIVE (\d)",
        r"Strategic Objective (\d)",
        r"SO(\d)",
        r"Action Plan:.*?Objective (\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"SO{match.group(1)}"
    return "GENERAL"


def _extract_section_type(text: str) -> str:
    """Identify the type of content in a chunk."""
    text_lower = text.lower()
    if "key performance indicator" in text_lower or "| kpi" in text_lower:
        return "kpi_table"
    elif "timeline" in text_lower or "milestone" in text_lower:
        return "timeline"
    elif "action id" in text_lower or "| action" in text_lower:
        return "action_table"
    elif "risk" in text_lower and "|" in text:
        return "risk_table"
    elif "budget" in text_lower:
        return "budget"
    elif "alignment" in text_lower:
        return "alignment"
    elif "executive summary" in text_lower or "vision" in text_lower:
        return "executive_summary"
    elif "governance" in text_lower:
        return "governance"
    elif "description" in text_lower:
        return "description"
    return "general"


def semantic_chunk(text: str, doc_type: str, source_file: str) -> list[dict]:
    """
    Split text based on semantic similarity between consecutive segments.
    
    Uses OpenAI embeddings to find natural breakpoints where the topic shifts.
    
    Args:
        text: Full document text
        doc_type: 'strategic_plan' or 'action_plan'
        source_file: Source filename
        
    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    
    chunker = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=SEMANTIC_BREAKPOINT_PERCENTILE,
    )
    
    docs = chunker.create_documents([text])
    
    result = []
    for i, doc in enumerate(docs):
        chunk_text = doc.page_content
        objective_id = _extract_objective_id(chunk_text)
        section_type = _extract_section_type(chunk_text)
        
        result.append({
            "text": chunk_text,
            "metadata": {
                "source": source_file,
                "doc_type": doc_type,
                "objective_id": objective_id,
                "section_type": section_type,
                "chunk_strategy": "semantic",
                "chunk_index": i,
            }
        })
    
    return result
