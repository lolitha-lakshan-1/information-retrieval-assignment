"""
Ontology-Based Alignment Scoring
Uses the knowledge graph to compute alignment between strategic objectives and actions.
"""
from rdflib import Graph, RDF
from src.ontology.schema import ISPS
from src.config import STRATEGIC_OBJECTIVES, OBJECTIVE_KPIS


def compute_ontology_alignment(g: Graph) -> dict:
    """
    Compute alignment scores based on ontology relationships.
    
    For each strategic objective, checks:
    1. How many actions support it
    2. How many KPIs have supporting actions
    3. Average progress of supporting actions
    
    Returns:
        Dict mapping objective IDs to alignment info
    """
    results = {}
    
    for obj_id in STRATEGIC_OBJECTIVES:
        obj_uri = ISPS[obj_id]
        
        # Find all actions supporting this objective
        supporting_actions = list(g.subjects(ISPS["supportsObjective"], obj_uri))
        
        # Find all KPIs for this objective
        kpis = list(g.objects(obj_uri, ISPS["hasKPI"]))
        total_kpis = len(kpis)
        
        # Check which KPIs have supporting actions
        kpis_with_actions = set()
        for action in supporting_actions:
            for kpi in g.objects(action, ISPS["supportsKPI"]):
                kpis_with_actions.add(str(kpi))
        
        # Compute progress stats
        progress_values = []
        for action in supporting_actions:
            for prog in g.objects(action, ISPS["hasProgress"]):
                try:
                    progress_values.append(int(prog))
                except (ValueError, TypeError):
                    pass
        
        avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
        
        # Compute coverage score
        action_count = len(supporting_actions)
        kpi_coverage = len(kpis_with_actions) / total_kpis if total_kpis > 0 else 0
        
        # Overall alignment score: combination of action density and KPI coverage
        # More actions per KPI = better coverage (capped at 1.0)
        # Adjusted density factor to be less strict: target 1.0 actions per KPI
        action_density = min(action_count / (total_kpis * 1.0), 1.0) if total_kpis > 0 else 0
        
        alignment_score = (0.4 * action_density) + (0.4 * kpi_coverage) + (0.2 * avg_progress / 100)
        
        # Classify alignment level
        if alignment_score >= 0.75:
            level = "Full"
        elif alignment_score >= 0.50:
            level = "Partial"
        elif alignment_score >= 0.25:
            level = "Weak"
        else:
            level = "Missing"
        
        results[obj_id] = {
            "objective": STRATEGIC_OBJECTIVES[obj_id],
            "alignment_score": round(alignment_score, 3),
            "alignment_level": level,
            "total_actions": action_count,
            "total_kpis": total_kpis,
            "kpis_covered": len(kpis_with_actions),
            "kpi_coverage": round(kpi_coverage, 3),
            "avg_progress": round(avg_progress, 1),
            "action_details": _get_action_details(g, supporting_actions),
        }
    
    return results


def get_ontology_mapping(g: Graph, objective_id: str) -> dict:
    """
    Get the detailed mapping between a strategic objective and its actions.
    Used as a tool by the sync assessment agent.
    
    Args:
        g: RDF graph
        objective_id: e.g., "SO1"
        
    Returns:
        Dict with mapping details
    """
    obj_uri = ISPS[objective_id]
    
    # Get actions
    actions = []
    for action_uri in g.subjects(ISPS["supportsObjective"], obj_uri):
        action_info = {
            "id": str(action_uri).split("#")[-1],
        }
        for title in g.objects(action_uri, ISPS["hasTitle"]):
            action_info["title"] = str(title)
        for progress in g.objects(action_uri, ISPS["hasProgress"]):
            action_info["progress"] = int(progress)
        for status in g.objects(action_uri, ISPS["hasStatus"]):
            action_info["status"] = str(status)
        for owner in g.objects(action_uri, ISPS["ownedBy"]):
            for name in g.objects(owner, ISPS["hasTitle"]):
                action_info["owner"] = str(name)
        actions.append(action_info)
    
    # Get KPIs
    kpis = []
    for kpi_uri in g.objects(obj_uri, ISPS["hasKPI"]):
        kpi_info = {"id": str(kpi_uri).split("#")[-1]}
        for title in g.objects(kpi_uri, ISPS["hasTitle"]):
            kpi_info["title"] = str(title)
        for target in g.objects(kpi_uri, ISPS["hasTarget"]):
            kpi_info["target"] = str(target)
        for baseline in g.objects(kpi_uri, ISPS["hasBaseline"]):
            kpi_info["baseline"] = str(baseline)
        kpis.append(kpi_info)
    
    return {
        "objective_id": objective_id,
        "objective_name": STRATEGIC_OBJECTIVES.get(objective_id, "Unknown"),
        "actions": actions,
        "kpis": kpis,
        "action_count": len(actions),
        "kpi_count": len(kpis),
    }


def identify_gaps(g: Graph, objective_id: str) -> list[dict]:
    """
    Identify alignment gaps for a specific objective.
    Used as a tool by the improvement agent.
    
    Args:
        g: RDF graph
        objective_id: e.g., "SO1"
        
    Returns:
        List of gap descriptions
    """
    obj_uri = ISPS[objective_id]
    
    # Get all KPIs
    kpis = list(g.objects(obj_uri, ISPS["hasKPI"]))
    
    # Get all actions and what KPIs they support
    actions = list(g.subjects(ISPS["supportsObjective"], obj_uri))
    supported_kpis = set()
    for action in actions:
        for kpi in g.objects(action, ISPS["supportsKPI"]):
            supported_kpis.add(str(kpi))
    
    gaps = []
    for kpi_uri in kpis:
        kpi_id = str(kpi_uri).split("#")[-1]
        if str(kpi_uri) not in supported_kpis:
            kpi_title = ""
            for title in g.objects(kpi_uri, ISPS["hasTitle"]):
                kpi_title = str(title)
            gaps.append({
                "kpi_id": kpi_id,
                "kpi_title": kpi_title,
                "gap_type": "No supporting actions",
                "severity": "High",
            })
    
    # Check for actions with low progress
    for action in actions:
        for prog in g.objects(action, ISPS["hasProgress"]):
            progress = int(prog)
            if progress < 25:
                action_title = ""
                for title in g.objects(action, ISPS["hasTitle"]):
                    action_title = str(title)
                gaps.append({
                    "action_id": str(action).split("#")[-1],
                    "action_title": action_title,
                    "progress": progress,
                    "gap_type": "Low progress",
                    "severity": "Medium",
                })
    
    return gaps


def _get_action_details(g: Graph, action_uris: list) -> list[dict]:
    """Get details for a list of action URIs."""
    details = []
    for action_uri in action_uris:
        info = {"id": str(action_uri).split("#")[-1]}
        for title in g.objects(action_uri, ISPS["hasTitle"]):
            info["title"] = str(title)
        for prog in g.objects(action_uri, ISPS["hasProgress"]):
            info["progress"] = int(prog)
        details.append(info)
    return details
