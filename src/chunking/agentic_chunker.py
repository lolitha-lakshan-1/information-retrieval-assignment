"""
Agentic Chunker
Uses an LLM to extract atomic propositions from text and group them
into thematically coherent chunks. Best for complex structured content.
"""
import re
import json
import time
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.config import OPENAI_API_KEY, LLM_MODEL

# ─── Logging setup ────────────────────────────────────────────────────────────
logger = logging.getLogger("isps.agentic_chunker")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)

# ─── Timeout (seconds) for each LLM call ─────────────────────────────────────
LLM_TIMEOUT = 60


PROPOSITION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at extracting factual propositions from organizational documents.

Given a section of text, extract atomic factual propositions. Each proposition should:
1. Be a single, self-contained factual statement
2. Include relevant context (who, what, when, how much)
3. Be understandable on its own without the original text

Format each proposition on its own line, prefixed with "- ".
Extract ALL important facts including KPIs, targets, deadlines, responsibilities, and actions."""),
    ("human", "Extract propositions from this text:\n\n{text}")
])

GROUPING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at organizing information about strategic and action plans.

Given a list of propositions, group them into thematic chunks. Each chunk should contain
related propositions about the same topic, objective, or theme.

Return the groups as JSON array of objects with 'theme' and 'propositions' keys.
Example:
[
  {{"theme": "SO1 Digital Learning KPIs", "propositions": ["prop1", "prop2"]}},
  {{"theme": "SO1 Digital Learning Timeline", "propositions": ["prop3", "prop4"]}}
]

Keep groups focused - each should cover one coherent sub-topic."""),
    ("human", "Group these propositions:\n\n{propositions}")
])


def _extract_objective_id(text: str) -> str:
    """Extract strategic objective ID from chunk text."""
    patterns = [
        r"SO(\d)", r"STRATEGIC OBJECTIVE (\d)", r"Strategic Objective (\d)",
        r"Objective (\d)", r"[DRISOE](\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            digit = match.group(1)
            if digit in "123456":
                return f"SO{digit}"
    return "GENERAL"


def agentic_chunk(text: str, doc_type: str, source_file: str) -> list[dict]:
    """
    Use LLM to extract propositions and group them into thematic chunks.
    
    Process:
    1. Split text into manageable sections (by major headings)
    2. For each section, LLM extracts atomic propositions
    3. LLM groups propositions into thematic clusters
    4. Each cluster becomes a chunk with rich metadata
    
    Args:
        text: Full document text
        doc_type: 'strategic_plan' or 'action_plan'
        source_file: Source filename
        
    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    logger.info("═" * 60)
    logger.info(f"Starting agentic chunking for '{doc_type}' ({source_file})")
    logger.info(f"Document length: {len(text):,} characters")
    overall_start = time.time()

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
        request_timeout=LLM_TIMEOUT,
    )
    
    # Split by major sections first
    sections = re.split(r'={50,}', text)
    sections = [s.strip() for s in sections if s.strip() and len(s.strip()) > 100]
    logger.info(f"Split into {len(sections)} major section(s)")
    
    all_chunks = []
    chunk_index = 0
    total_sub_sections = 0
    
    for sec_idx, section in enumerate(sections, 1):
        # Limit section size for LLM context
        if len(section) > 4000:
            sub_sections = re.split(r'-{3,}', section)
            sub_sections = [s.strip() for s in sub_sections if s.strip() and len(s.strip()) > 50]
        else:
            sub_sections = [section]
        
        logger.info(f"  Section {sec_idx}/{len(sections)}: {len(sub_sections)} sub-section(s), "
                     f"{len(section):,} chars")

        for sub_idx, sub_section in enumerate(sub_sections, 1):
            total_sub_sections += 1
            preview = sub_section[:80].replace("\n", " ").strip()
            logger.info(f"    Sub-section {sub_idx}/{len(sub_sections)} "
                         f"({len(sub_section):,} chars) — \"{preview}…\"")
            
            try:
                # Step 1: Extract propositions
                t0 = time.time()
                logger.info(f"      → Extracting propositions (LLM call 1/2)…")
                prop_chain = PROPOSITION_PROMPT | llm
                prop_response = prop_chain.invoke({"text": sub_section[:3000]})
                propositions = prop_response.content
                t1 = time.time()
                prop_count = propositions.count("\n- ") + (1 if propositions.startswith("- ") else 0)
                logger.info(f"      ✓ Extracted {prop_count} propositions in {t1 - t0:.1f}s")
                
                # Step 2: Group propositions
                logger.info(f"      → Grouping propositions (LLM call 2/2)…")
                group_chain = GROUPING_PROMPT | llm
                group_response = group_chain.invoke({"propositions": propositions})
                t2 = time.time()
                logger.info(f"      ✓ Grouping complete in {t2 - t1:.1f}s")
                
                # Parse JSON response
                groups_text = group_response.content
                groups_text = re.sub(r'```json\s*', '', groups_text)
                groups_text = re.sub(r'```\s*', '', groups_text)
                
                groups = json.loads(groups_text)
                logger.info(f"      ✓ Parsed {len(groups)} thematic group(s)")
                
                for group in groups:
                    theme = group.get("theme", "General")
                    props = group.get("propositions", [])
                    chunk_text = f"[{theme}]\n" + "\n".join(f"- {p}" for p in props)
                    
                    objective_id = _extract_objective_id(chunk_text)
                    
                    all_chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "source": source_file,
                            "doc_type": doc_type,
                            "objective_id": objective_id,
                            "section_type": "agentic_propositions",
                            "chunk_strategy": "agentic",
                            "chunk_index": chunk_index,
                            "theme": theme,
                        }
                    })
                    chunk_index += 1
                    
            except Exception as e:
                logger.warning(f"      ✗ Error on sub-section {sub_idx}: {e}")
                logger.warning(f"        Falling back to raw section as chunk")
                objective_id = _extract_objective_id(sub_section)
                all_chunks.append({
                    "text": sub_section,
                    "metadata": {
                        "source": source_file,
                        "doc_type": doc_type,
                        "objective_id": objective_id,
                        "section_type": "agentic_fallback",
                        "chunk_strategy": "agentic",
                        "chunk_index": chunk_index,
                        "error": str(e),
                    }
                })
                chunk_index += 1

    elapsed = time.time() - overall_start
    logger.info(f"Agentic chunking complete for '{doc_type}': "
                f"{len(all_chunks)} chunks from {total_sub_sections} sub-sections "
                f"in {elapsed:.1f}s")
    logger.info("═" * 60)
    return all_chunks
