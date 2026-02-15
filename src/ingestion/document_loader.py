"""
Document Loader & Preprocessor
Reads strategic plan and action plan .txt files, applies light preprocessing.
"""
from pathlib import Path
from src.config import STRATEGIC_PLAN_PATH, ACTION_PLAN_PATH


import docx
import pypdf

def load_document(path: Path) -> str:
    """Load a document (txt, docx, pdf) and return its content."""
    if not path.exists():
        raise FileNotFoundError(f"Document not found at {path}")
        
    ext = path.suffix.lower()
    
    if ext == ".docx":
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        doc = docx.Document(path)
        text = []
        for element in doc.element.body:
            if element.tag.endswith('p'): # Paragraph
                para = Paragraph(element, doc)
                text.append(para.text)
            elif element.tag.endswith('tbl'): # Table
                table = Table(element, doc)
                for row in table.rows:
                    cells = [cell.text for cell in row.cells]
                    text.append(" | ".join(cells))
        return "\n".join(text)
        
    elif ext == ".pdf":
        reader = pypdf.PdfReader(path)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
        
    else:
        # Default to text
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def preprocess_text(text: str) -> str:
    """Light preprocessing while preserving document structure."""
    # Normalize whitespace but keep structure markers
    lines = text.split("\n")
    cleaned = []
    prev_blank = False
    
    for line in lines:
        stripped = line.rstrip()
        is_blank = len(stripped) == 0
        
        # Collapse multiple blank lines into one
        if is_blank and prev_blank:
            continue
        
        cleaned.append(stripped)
        prev_blank = is_blank
    
    return "\n".join(cleaned)


def load_strategic_plan() -> str:
    """Load and preprocess the strategic plan document."""
    raw = load_document(STRATEGIC_PLAN_PATH)
    return preprocess_text(raw)


def load_action_plan() -> str:
    """Load and preprocess the action plan document."""
    raw = load_document(ACTION_PLAN_PATH)
    return preprocess_text(raw)


def load_all_documents() -> dict[str, str]:
    """Load both documents and return as a dictionary."""
    return {
        "strategic_plan": load_strategic_plan(),
        "action_plan": load_action_plan(),
    }
