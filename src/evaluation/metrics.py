"""
Evaluation Metrics
Computes precision, recall, F1, and other metrics for the alignment system.
"""
import numpy as np
from src.evaluation.ground_truth import GROUND_TRUTH, EXPECTED_ALIGNMENT, EXPECTED_GAPS


def compute_retrieval_metrics(
    retrieved_actions: list[str],
    relevant_actions: list[str],
    k: int = 5,
) -> dict:
    """
    Compute retrieval metrics for a single query.
    
    Args:
        retrieved_actions: List of retrieved action IDs
        relevant_actions: List of relevant action IDs (ground truth)
        k: Cutoff for @K metrics
    """
    retrieved_set = set(retrieved_actions[:k])
    relevant_set = set(relevant_actions)
    
    if not relevant_set:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "f1_at_k": 0.0}
    
    true_positives = len(retrieved_set & relevant_set)
    
    precision = true_positives / len(retrieved_set) if retrieved_set else 0
    recall = true_positives / len(relevant_set) if relevant_set else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(recall, 4),
        "f1_at_k": round(f1, 4),
    }


def compute_mrr(ranked_results: list[list[str]], relevant_items: list[list[str]]) -> float:
    """
    Compute Mean Reciprocal Rank across multiple queries.
    """
    reciprocal_ranks = []
    
    for retrieved, relevant in zip(ranked_results, relevant_items):
        relevant_set = set(relevant)
        rr = 0.0
        for i, item in enumerate(retrieved):
            if item in relevant_set:
                rr = 1.0 / (i + 1)
                break
        reciprocal_ranks.append(rr)
    
    return round(np.mean(reciprocal_ranks), 4) if reciprocal_ranks else 0.0


def evaluate_alignment_accuracy(system_results: dict) -> dict:
    """
    Compare system alignment scores against ground truth.
    
    Args:
        system_results: Dict mapping objective IDs to system scores
        
    Returns:
        Evaluation metrics dict
    """
    metrics = {
        "per_objective": {},
        "overall": {},
    }
    
    correct_levels = 0
    total_mae = 0.0
    
    for obj_id, expected in EXPECTED_ALIGNMENT.items():
        system_data = system_results.get(obj_id, {})
        system_score = system_data.get("combined_score", 0.5)
        system_level = system_data.get("sync_assessment", {}).get("alignment_level", "Partial")
        expected_level = expected["level"]
        expected_min_score = expected["min_score"]
        
        level_match = system_level == expected_level
        if level_match:
            correct_levels += 1
        
        # Mean Absolute Error for score
        gt_score = expected_min_score
        mae = abs(system_score - gt_score)
        total_mae += mae
        
        metrics["per_objective"][obj_id] = {
            "system_score": round(system_score, 3),
            "expected_min_score": expected_min_score,
            "system_level": system_level,
            "expected_level": expected_level,
            "level_match": level_match,
            "score_error": round(mae, 3),
        }
    
    n = len(EXPECTED_ALIGNMENT)
    metrics["overall"] = {
        "level_accuracy": round(correct_levels / n, 3) if n > 0 else 0,
        "mean_absolute_error": round(total_mae / n, 3) if n > 0 else 0,
        "correct_levels": correct_levels,
        "total_objectives": n,
    }
    
    return metrics


def evaluate_gap_detection(system_results: dict) -> dict:
    """
    Evaluate how well the system detects known alignment gaps.
    """
    detected_gaps = []
    missed_gaps = []
    
    for gap in EXPECTED_GAPS:
        kpi_id = gap["kpi"]
        obj_id = kpi_id.split("_")[0]
        
        # Check if system detected this gap
        obj_data = system_results.get(obj_id, {})
        sync_data = obj_data.get("sync_assessment", {})
        uncovered = sync_data.get("uncovered_kpis", [])
        
        kpi_suffix = kpi_id.split("_")[1]
        detected = any(kpi_suffix in u for u in uncovered) if uncovered else False
        
        if detected:
            detected_gaps.append(gap)
        else:
            missed_gaps.append(gap)
    
    total = len(EXPECTED_GAPS)
    return {
        "total_expected_gaps": total,
        "detected": len(detected_gaps),
        "missed": len(missed_gaps),
        "detection_rate": round(len(detected_gaps) / total, 3) if total > 0 else 0,
        "detected_gaps": detected_gaps,
        "missed_gaps": missed_gaps,
    }


def compute_chunking_quality(chunks: list[dict]) -> dict:
    """
    Compute quality metrics for a set of chunks.
    """
    lengths = [len(c["text"]) for c in chunks]
    strategies = {}
    for c in chunks:
        strategy = c["metadata"].get("chunk_strategy", "unknown")
        if strategy not in strategies:
            strategies[strategy] = []
        strategies[strategy].append(len(c["text"]))
    
    return {
        "total_chunks": len(chunks),
        "avg_length": round(np.mean(lengths), 1) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "std_length": round(np.std(lengths), 1) if lengths else 0,
        "per_strategy": {
            strategy: {
                "count": len(lens),
                "avg_length": round(np.mean(lens), 1),
            }
            for strategy, lens in strategies.items()
        },
    }
