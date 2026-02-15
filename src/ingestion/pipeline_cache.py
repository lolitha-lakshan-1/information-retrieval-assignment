"""
Pipeline Cache Module
Persists pipeline results to disk so they survive Streamlit page refreshes.
"""
import json
import logging
from pathlib import Path
from src.config import BASE_DIR

logger = logging.getLogger("isps.pipeline_cache")

CACHE_DIR = BASE_DIR / "cache"
CACHE_FILE = CACHE_DIR / "pipeline_cache.json"


def save_pipeline_cache(
    analysis_results: dict,
    chunks: dict,
    eval_results: dict,
    kg_summary: dict | None = None,
) -> None:
    """
    Save pipeline results to disk as JSON.

    Args:
        analysis_results: The full analysis results dict
        chunks: Dict of {doc_type: [chunk_dicts]}
        eval_results: Evaluation results dict
        kg_summary: Optional knowledge graph summary (nodes/edges counts)
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "analysis_results": analysis_results,
        "chunks": chunks,
        "eval_results": eval_results,
        "kg_summary": kg_summary,
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, default=str)

    logger.info(f"Pipeline cache saved to {CACHE_FILE}")


def load_pipeline_cache() -> dict | None:
    """
    Load cached pipeline results from disk.

    Returns:
        Dict with keys: analysis_results, chunks, eval_results, kg_summary
        or None if cache is missing/corrupt
    """
    if not CACHE_FILE.exists():
        logger.info("No pipeline cache found")
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate required keys
        if "analysis_results" not in data or "chunks" not in data:
            logger.warning("Pipeline cache is incomplete, ignoring")
            return None

        logger.info(f"Pipeline cache loaded from {CACHE_FILE}")
        return data

    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load pipeline cache: {e}")
        return None


def clear_pipeline_cache() -> None:
    """Delete the cache file."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        logger.info("Pipeline cache cleared")
