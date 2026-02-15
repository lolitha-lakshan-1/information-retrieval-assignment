"""
Ground Truth Alignment Mappings
Hand-crafted from the alignment matrix in the Action Plan.
Maps KPIs to supporting actions with expected alignment levels.
"""

# Ground truth: for each KPI, which actions should support it
# Derived from the Alignment Matrix in action_plan.txt
GROUND_TRUTH = {
    # SO1: Digital Learning Transformation
    "SO1_D1": {"actions": ["A1.3", "A1.8", "A1.10", "A1.12"], "coverage": "Full"},
    "SO1_D2": {"actions": ["A1.3", "A1.5", "A1.6", "A1.8"], "coverage": "Full"},
    "SO1_D3": {"actions": ["A1.1", "A1.2", "A1.4", "A1.7"], "coverage": "Full"},
    "SO1_D4": {"actions": ["A1.4", "A1.9", "A1.11"], "coverage": "Full"},
    "SO1_D5": {"actions": ["A1.5", "A1.6", "A1.10"], "coverage": "Full"},
    "SO1_D6": {"actions": ["A1.1", "A1.2", "A1.7", "A1.9", "A1.11", "A1.12"], "coverage": "Full"},
    
    # SO2: Research Excellence and Innovation
    "SO2_R1": {"actions": ["A2.1", "A2.3"], "coverage": "Partial"},
    "SO2_R2": {"actions": ["A2.2", "A2.4", "A2.6"], "coverage": "Full"},
    "SO2_R3": {"actions": ["A2.5", "A2.7", "A2.8"], "coverage": "Full"},
    "SO2_R4": {"actions": ["A2.9", "A2.10"], "coverage": "Full"},
    "SO2_R5": {"actions": ["A2.4", "A2.6", "A2.11"], "coverage": "Full"},
    "SO2_R6": {"actions": ["A2.2", "A2.12"], "coverage": "Full"},
    
    # SO3: Student Experience and Wellbeing
    "SO3_S1": {"actions": ["A3.1", "A3.2", "A3.5"], "coverage": "Full"},
    "SO3_S2": {"actions": ["A3.3", "A3.6"], "coverage": "Full"},
    "SO3_S3": {"actions": ["A3.4", "A3.7", "A3.8"], "coverage": "Full"},
    "SO3_S4": {"actions": ["A3.9", "A3.10"], "coverage": "Full"},
    "SO3_S5": {"actions": ["A3.7", "A3.11"], "coverage": "Partial"},
    "SO3_S6": {"actions": ["A3.8", "A3.10", "A3.12"], "coverage": "Full"},
    
    # SO4: Industry Partnerships and Employability
    "SO4_I1": {"actions": ["A4.1", "A4.4", "A4.6"], "coverage": "Full"},
    "SO4_I2": {"actions": ["A4.2", "A4.5"], "coverage": "Full"},
    "SO4_I3": {"actions": ["A4.3", "A4.7", "A4.8"], "coverage": "Full"},
    "SO4_I4": {"actions": [], "coverage": "Missing"},  # Deliberate gap: employer satisfaction
    "SO4_I5": {"actions": ["A4.9", "A4.10"], "coverage": "Full"},
    "SO4_I6": {"actions": ["A4.11", "A4.12"], "coverage": "Full"},
    
    # SO5: Operational Efficiency and Sustainability  
    "SO5_O1": {"actions": ["A5.1", "A5.2", "A5.5"], "coverage": "Full"},
    "SO5_O2": {"actions": ["A5.3", "A5.6", "A5.7"], "coverage": "Full"},
    "SO5_O3": {"actions": [], "coverage": "Missing"},  # Deliberate gap: international recruitment
    "SO5_O4": {"actions": [], "coverage": "Missing"},  # Deliberate gap: exec education
    "SO5_O5": {"actions": ["A5.8"], "coverage": "Weak"},  # Deliberate gap: staff satisfaction
    "SO5_O6": {"actions": ["A5.9", "A5.10", "A5.11", "A5.12"], "coverage": "Full"},
    
    # SO6: Diversity, Equity and Inclusion
    "SO6_E1": {"actions": ["A6.1", "A6.2", "A6.4"], "coverage": "Full"},
    "SO6_E2": {"actions": ["A6.3", "A6.5", "A6.6"], "coverage": "Full"},
    "SO6_E3": {"actions": ["A6.7", "A6.8"], "coverage": "Full"},
    "SO6_E4": {"actions": ["A6.9", "A6.10"], "coverage": "Full"},
    "SO6_E5": {"actions": ["A6.5", "A6.11"], "coverage": "Full"},
    "SO6_E6": {"actions": ["A6.12"], "coverage": "Partial"},
}

# Expected alignment level per objective
EXPECTED_ALIGNMENT = {
    "SO1": {"level": "Full", "min_score": 0.85},
    "SO2": {"level": "Full", "min_score": 0.80},
    "SO3": {"level": "Full", "min_score": 0.80},
    "SO4": {"level": "Partial", "min_score": 0.60},
    "SO5": {"level": "Partial", "min_score": 0.50},
    "SO6": {"level": "Full", "min_score": 0.80},
}

# Known gaps that the system should detect
EXPECTED_GAPS = [
    {"kpi": "SO4_I4", "type": "Missing", "description": "Employer satisfaction - no supporting actions"},
    {"kpi": "SO5_O3", "type": "Missing", "description": "International student recruitment revenue - no actions"},
    {"kpi": "SO5_O4", "type": "Missing", "description": "Executive education income - no actions"},
    {"kpi": "SO5_O5", "type": "Weak", "description": "Staff satisfaction - only one supporting action"},
    {"kpi": "SO2_R1", "type": "Partial", "description": "Research income - limited action coverage"},
]


def get_objective_kpi_coverage(objective_id: str, action_map: dict = None) -> dict:
    """
    Get ground truth KPI coverage for a specific objective.
    
    Args:
        objective_id: Strategic Objective ID (e.g., "SO1")
        action_map: Optional dict mapping Action IDs (e.g., "A1.1") to Titles.
    """
    prefix = f"{objective_id}_"
    kpis = {k: v for k, v in GROUND_TRUTH.items() if k.startswith(prefix)}
    
    total = len(kpis)
    full = sum(1 for v in kpis.values() if v["coverage"] == "Full")
    partial = sum(1 for v in kpis.values() if v["coverage"] == "Partial")
    weak = sum(1 for v in kpis.values() if v["coverage"] == "Weak")
    missing = sum(1 for v in kpis.values() if v["coverage"] == "Missing")
    
    # Generate detailed breakdown if requested
    kpi_details = []
    if action_map:
        for kpi_id, data in kpis.items():
            expected_actions = []
            for action_id in data["actions"]:
                # action_map is expected to use "A1.1" format
                title = action_map.get(action_id, "Description not found")
                expected_actions.append({"id": action_id, "title": title})
            
            kpi_details.append({
                "kpi_id": kpi_id,
                "coverage": data["coverage"],
                "expected_actions": expected_actions
            })
    
    return {
        "objective_id": objective_id,
        "total_kpis": total,
        "full": full,
        "partial": partial,
        "weak": weak,
        "missing": missing,
        "coverage_pct": (full + 0.5 * partial + 0.25 * weak) / total if total > 0 else 0,
        "kpi_details": kpi_details
    }
