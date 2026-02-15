"""
Fixed/Recursive Text Chunker
Uses RecursiveCharacterTextSplitter with document-aware separators.
"""
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import CHUNK_SIZE, CHUNK_OVERLAP, SEPARATORS


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


def fixed_chunk(text: str, doc_type: str, source_file: str) -> list[dict]:
    """
    Split text using RecursiveCharacterTextSplitter with document-aware separators.
    
    Args:
        text: Full document text
        doc_type: 'strategic_plan' or 'action_plan'
        source_file: Source filename
        
    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = splitter.split_text(text)
    
    result = []
    for i, chunk_text in enumerate(chunks):
        objective_id = _extract_objective_id(chunk_text)
        section_type = _extract_section_type(chunk_text)
        
        result.append({
            "text": chunk_text,
            "metadata": {
                "source": source_file,
                "doc_type": doc_type,
                "objective_id": objective_id,
                "section_type": section_type,
                "chunk_strategy": "fixed_recursive",
                "chunk_index": i,
            }
        })
    
    return result
