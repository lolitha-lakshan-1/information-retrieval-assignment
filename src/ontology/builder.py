"""
Ontology Graph Builder
Parses strategic plan and action plan documents to extract entities
and build an RDF knowledge graph.
"""
import re
from rdflib import Graph, Literal, RDF, XSD
from src.ontology.schema import ISPS, create_ontology_graph
from src.config import STRATEGIC_OBJECTIVES, OBJECTIVE_KPIS


def build_knowledge_graph(strategic_text: str, action_text: str) -> Graph:
    """
    Build a knowledge graph from the strategic and action plan documents.
    
    Args:
        strategic_text: Full strategic plan text
        action_text: Full action plan text
        
    Returns:
        Populated RDF graph
    """
    g = create_ontology_graph()
    
    # ─── Create Plan Instances ───────────────────────────────────────────────
    sp = ISPS["GreenFieldStrategicPlan"]
    ap = ISPS["GreenFieldActionPlan"]
    g.add((sp, RDF.type, ISPS["StrategicPlan"]))
    g.add((sp, ISPS["hasTitle"], Literal("GreenField University Strategic Plan 2024-2029")))
    g.add((ap, RDF.type, ISPS["ActionPlan"]))
    g.add((ap, ISPS["hasTitle"], Literal("GreenField University Action Plan 2024-2029")))
    
    # ─── Extract Strategic Objectives ────────────────────────────────────────
    for obj_id, obj_title in STRATEGIC_OBJECTIVES.items():
        obj_uri = ISPS[obj_id]
        g.add((obj_uri, RDF.type, ISPS["StrategicObjective"]))
        g.add((obj_uri, ISPS["hasTitle"], Literal(obj_title)))
        g.add((sp, ISPS["hasObjective"], obj_uri))
        
        # Extract description
        desc = _extract_objective_description(strategic_text, obj_id)
        if desc:
            g.add((obj_uri, ISPS["hasDescription"], Literal(desc)))
    
    # ─── Extract KPIs ────────────────────────────────────────────────────────
    _extract_kpis(g, strategic_text)
    
    # ─── Extract Actions ─────────────────────────────────────────────────────
    _extract_actions(g, action_text, ap)
    _extract_addendum_actions(g, action_text, ap)
    
    # ─── Extract Risks ───────────────────────────────────────────────────────
    _extract_risks(g, action_text, ap)
    
    # ─── Extract Departments & People ────────────────────────────────────────
    _extract_people(g, action_text)
    
    return g


def _extract_objective_description(text: str, obj_id: str) -> str | None:
    """Extract the description for a strategic objective."""
    obj_num = obj_id.replace("SO", "")
    pattern = rf"STRATEGIC OBJECTIVE {obj_num}.*?Description:\s*(.*?)(?=Key Performance Indicators|Timeline|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        desc = match.group(1).strip()
        # Trim to first paragraph
        desc = desc.split("\n\n")[0].strip()
        return desc[:500]  # Limit length
    return None


def _extract_kpis(g: Graph, text: str):
    """Extract KPIs from the strategic plan and add to graph."""
    for obj_id, kpi_ids in OBJECTIVE_KPIS.items():
        obj_uri = ISPS[obj_id]
        
        for kpi_id in kpi_ids:
            full_kpi_id = f"{obj_id}_{kpi_id}"
            kpi_uri = ISPS[full_kpi_id]
            g.add((kpi_uri, RDF.type, ISPS["KPI"]))
            g.add((obj_uri, ISPS["hasKPI"], kpi_uri))
            
            # Try to extract KPI details
            kpi_info = _extract_kpi_details(text, kpi_id, obj_id)
            if kpi_info:
                g.add((kpi_uri, ISPS["hasTitle"], Literal(kpi_info.get("name", kpi_id))))
                if kpi_info.get("baseline"):
                    g.add((kpi_uri, ISPS["hasBaseline"], Literal(kpi_info["baseline"])))
                if kpi_info.get("target"):
                    g.add((kpi_uri, ISPS["hasTarget"], Literal(kpi_info["target"])))


def _extract_kpi_details(text: str, kpi_id: str, obj_id: str) -> dict | None:
    """Extract details for a specific KPI."""
    # Look for table rows with the KPI ID
    pattern = rf"\|\s*{kpi_id}\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    if match:
        return {
            "name": match.group(1).strip(),
            "baseline": match.group(2).strip(),
            "target": match.group(3).strip(),
        }
    return None


def _extract_actions(g: Graph, text: str, action_plan_uri):
    """Extract actions from the action plan and link them to objectives."""
    # Pattern to match action table rows
    pattern = r"\|\s*(A\d+\.\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(\d+)%?\s*\|"
    matches = re.finditer(pattern, text)
    
    current_obj = "SO1"
    
    for match in matches:
        action_id = match.group(1).strip()
        action_desc = match.group(2).strip()
        owner = match.group(3).strip()
        deadline = match.group(4).strip()
        progress = match.group(5).strip()
        
        # Determine which objective this action belongs to
        obj_num = action_id.split(".")[0].replace("A", "")
        if obj_num in "123456":
            current_obj = f"SO{obj_num}"
        
        action_uri = ISPS[action_id.replace(".", "_")]
        g.add((action_uri, RDF.type, ISPS["Action"]))
        g.add((action_uri, ISPS["hasTitle"], Literal(action_desc[:200])))
        g.add((action_uri, ISPS["hasDeadline"], Literal(deadline)))
        g.add((action_uri, ISPS["hasProgress"], Literal(int(progress), datatype=XSD.integer)))
        g.add((action_uri, ISPS["hasStatus"], Literal(_progress_to_status(int(progress)))))
        
        # Link to plan and objective
        g.add((action_plan_uri, ISPS["hasAction"], action_uri))
        g.add((action_uri, ISPS["supportsObjective"], ISPS[current_obj]))

        # Link action to all KPIs of its parent objective
        for kpi_id in OBJECTIVE_KPIS.get(current_obj, []):
            kpi_uri = ISPS[f"{current_obj}_{kpi_id}"]
            g.add((action_uri, ISPS["supportsKPI"], kpi_uri))
        
        # Link to owner
        if owner:
            owner_uri = ISPS[_uri_safe(owner)]
            g.add((action_uri, ISPS["ownedBy"], owner_uri))

def _extract_addendum_actions(g: Graph, text: str, action_plan_uri):
    """Extract actions from the addendum section (format: [KPI_ID] Action text)."""
    # Pattern: [SO1_D1] Action text...
    # We want to match: [SO1_D1] Ensure 100% of modules...
    pattern = r"\[(SO\d+_[A-Z]\d+)\]\s*(.*?)(?=\n|\[|$)"
    matches = re.finditer(pattern, text)
    
    for i, match in enumerate(matches):
        kpi_id = match.group(1).strip()
        action_desc = match.group(2).strip()
        
        # Generate a synthetic ID
        obj_id = kpi_id.split("_")[0]
        action_id = f"{obj_id}_ADD_{i+1}"
        
        action_uri = ISPS[action_id]
        g.add((action_uri, RDF.type, ISPS["Action"]))
        g.add((action_uri, ISPS["hasTitle"], Literal(action_desc[:300])))
        g.add((action_uri, ISPS["hasDeadline"], Literal("2029"))) # Default for addendum
        g.add((action_uri, ISPS["hasProgress"], Literal(20, datatype=XSD.integer))) # Assume started
        g.add((action_uri, ISPS["hasStatus"], Literal("In Progress")))
        
        
        # Link to plan and objective
        g.add((action_plan_uri, ISPS["hasAction"], action_uri))
        g.add((action_uri, ISPS["supportsObjective"], ISPS[obj_id]))
        
        # Link explicit KPI
        full_kpi_id = kpi_id # e.g. SO1_D1
        kpi_uri = ISPS[full_kpi_id]
        g.add((action_uri, ISPS["supportsKPI"], kpi_uri))
        
        # Also owner?
        owner_uri = ISPS["Strategic_Planning_Team"]
        g.add((action_uri, ISPS["ownedBy"], owner_uri))


def _extract_risks(g: Graph, text: str, action_plan_uri):
    """Extract risks from the risk register section."""
    pattern = r"\|\s*(RISK-\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|"
    matches = re.finditer(pattern, text)
    
    for match in matches:
        risk_id = match.group(1).strip()
        risk_desc = match.group(2).strip()
        likelihood = match.group(3).strip()
        impact = match.group(4).strip()
        
        risk_uri = ISPS[risk_id.replace("-", "_")]
        g.add((risk_uri, RDF.type, ISPS["Risk"]))
        g.add((risk_uri, ISPS["hasTitle"], Literal(risk_desc[:200])))
        g.add((risk_uri, ISPS["hasLikelihood"], Literal(likelihood)))
        g.add((risk_uri, ISPS["hasRiskLevel"], Literal(impact)))
        g.add((action_plan_uri, ISPS["hasRisk"], risk_uri))


def _extract_people(g: Graph, text: str):
    """Extract people/departments from the action plan."""
    # Common owner patterns in our action plan
    owners = set()
    pattern = r"\|\s*A\d+\.\d+\s*\|.*?\|\s*(.*?)\s*\|"
    for match in re.finditer(pattern, text):
        owner = match.group(1).strip()
        if owner and len(owner) > 2 and not owner.startswith("-"):
            owners.add(owner)
    
    for owner in owners:
        owner_uri = ISPS[_uri_safe(owner)]
        g.add((owner_uri, RDF.type, ISPS["Person"]))
        g.add((owner_uri, ISPS["hasTitle"], Literal(owner)))


def _progress_to_status(progress: int) -> str:
    """Convert progress percentage to status label."""
    if progress >= 100:
        return "Completed"
    elif progress >= 50:
        return "In Progress"
    elif progress > 0:
        return "Started"
    return "Not Started"


def _uri_safe(text: str) -> str:
    """Convert text to a URI-safe string."""
    return re.sub(r'[^a-zA-Z0-9]', '_', text).strip('_')


def export_graph(g: Graph, filepath: str, format: str = "turtle"):
    """Export the graph to a file."""
    g.serialize(destination=filepath, format=format)


def get_graph_stats(g: Graph) -> dict:
    """Get statistics about the knowledge graph."""
    stats = {
        "total_triples": len(g),
        "objectives": 0,
        "actions": 0,
        "kpis": 0,
        "risks": 0,
        "people": 0,
    }
    
    for class_name, key in [
        ("StrategicObjective", "objectives"),
        ("Action", "actions"),
        ("KPI", "kpis"),
        ("Risk", "risks"),
        ("Person", "people"),
    ]:
        stats[key] = len(list(g.subjects(RDF.type, ISPS[class_name])))
    
    return stats
