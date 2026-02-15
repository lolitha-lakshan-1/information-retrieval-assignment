"""
Evaluation Pipeline
Runs the complete evaluation process and compiles results.
"""
import json
from src.evaluation.ground_truth import GROUND_TRUTH, EXPECTED_ALIGNMENT, get_objective_kpi_coverage
from src.evaluation.metrics import (
    evaluate_alignment_accuracy,
    evaluate_gap_detection,
    compute_chunking_quality,
)
from src.config import STRATEGIC_OBJECTIVES


def run_evaluation(system_results: dict, chunks: dict = None) -> dict:
    """
    Run the complete evaluation pipeline.
    
    Args:
        system_results: Output from orchestrator.run_full_analysis()
        chunks: Optional dict of {"strategic": [...], "action": [...]} for chunk quality
        
    Returns:
        Complete evaluation results
    """
    eval_results = {
        "alignment_accuracy": {},
        "gap_detection": {},
        "ground_truth_comparison": {},
        "chunking_quality": {},
    }
    
    # 1. Alignment accuracy vs ground truth
    objectives_data = system_results.get("objectives", {})
    eval_results["alignment_accuracy"] = evaluate_alignment_accuracy(objectives_data)
    
    # 2. Gap detection evaluation
    eval_results["gap_detection"] = evaluate_gap_detection(objectives_data)
    
    # 3. Ground truth comparison table
    for obj_id in STRATEGIC_OBJECTIVES:
        sys_data = objectives_data.get(obj_id, {})
        
        # Build action map from ontology data (A1_1 -> A1.1)
        action_map = {}
        ontology_data = sys_data.get("ontology_data", {})
        
        if ontology_data:
            details = ontology_data.get("action_details", [])
            for action in details:
                # Normalize ID: "A1_1" -> "A1.1"
                normalized_id = action["id"].replace("_", ".")
                action_map[normalized_id] = action["title"]
        
        # Pass map to get detailed breakdown
        gt_coverage = get_objective_kpi_coverage(obj_id, action_map=action_map)
        
        eval_results["ground_truth_comparison"][obj_id] = {
            "objective": STRATEGIC_OBJECTIVES[obj_id],
            "ground_truth": gt_coverage,
            "system_score": sys_data.get("combined_score", 0),
            "system_level": sys_data.get("sync_assessment", {}).get("alignment_level", "Unknown"),
            # Pass through the covered KPIs for detailed comparison
            "covered_kpis": sys_data.get("sync_assessment", {}).get("covered_kpis", []) 
        }
    
    # 4. Chunking quality (if chunks provided)
    if chunks:
        for doc_type, chunk_list in chunks.items():
            eval_results["chunking_quality"][doc_type] = compute_chunking_quality(chunk_list)
    
    return eval_results
