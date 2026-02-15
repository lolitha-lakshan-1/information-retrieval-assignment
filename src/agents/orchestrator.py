"""
Agentic Orchestrator
Coordinates the sync and improvement agents, runs full analysis pipeline,
and manages the overall reasoning flow.
"""
import json
import random
from src.config import STRATEGIC_OBJECTIVES
from src.agents.sync_agent import run_sync_assessment
from src.agents.improvement_agent import run_improvement_analysis
from src.agents.callbacks import ReasoningCallbackHandler
from src.rag.retriever import retrieve_for_objective
from src.rag.chains import (
    generate_executive_summary,
    generate_guidance_messages,
    suggest_improvements,
)
from src.ontology.alignment import get_ontology_mapping, identify_gaps, compute_ontology_alignment


def run_full_analysis(knowledge_graph, progress_callback=None) -> dict:
    """
    Run the complete synchronization analysis across all objectives.
    
    This is the main entry point that coordinates:
    1. Ontology-based alignment computation
    2. Agent-based sync assessment per objective
    3. Agent-based improvement suggestions for weak alignments
    4. Executive summary generation
    5. Guidance message generation
    
    Args:
        knowledge_graph: RDF graph with the knowledge base
        progress_callback: Optional callback(objective_id, status) for progress updates
        
    Returns:
        Complete analysis results dict
    """
    results = {
        "objectives": {},
        "overall_score": 0.0,
        "overall_level": "Partial",
        "executive_summary": "",
        "guidance_messages": {},
        "reasoning_traces": {},
    }
    
    # Step 1: Compute ontology-based alignment
    ontology_alignment = compute_ontology_alignment(knowledge_graph)
    
    # Step 2: Run agent-based analysis per objective
    total_score = 0.0
    
    for obj_id, obj_name in STRATEGIC_OBJECTIVES.items():
        if progress_callback:
            progress_callback(obj_id, "Analyzing...")
        
        # Create tool functions for this objective
        def retrieve_fn(oid=obj_id):
            chunks = retrieve_for_objective(oid, STRATEGIC_OBJECTIVES[oid])
            return "\n\n---\n\n".join([
                f"[Chunk {i+1}] (score: {c.get('score', 'N/A'):.3f})\n{c['text']}"
                for i, c in enumerate(chunks)
            ])
        
        def ontology_fn(oid=obj_id):
            mapping = get_ontology_mapping(knowledge_graph, oid)
            return json.dumps(mapping, indent=2, default=str)
        
        def kpi_coverage_fn(oid=obj_id):
            mapping = get_ontology_mapping(knowledge_graph, oid)
            lines = [f"Objective: {oid} - {STRATEGIC_OBJECTIVES[oid]}"]
            lines.append(f"Total KPIs: {len(mapping.get('kpis', []))}")
            lines.append(f"Total Actions: {len(mapping.get('actions', []))}")
            lines.append("\nKPIs to evaluate (decide if each is adequately covered by the actions):")
            for kpi in mapping.get('kpis', []):
                lines.append(f"  - {kpi.get('id','?')}: {kpi.get('title','?')} (Baseline: {kpi.get('baseline','?')}, Target: {kpi.get('target','?')})")
            lines.append("\nActions available:")
            for act in mapping.get('actions', []):
                lines.append(f"  - {act.get('id','?')}: {act.get('title','?')} (Progress: {act.get('progress','?')}%, Owner: {act.get('owner','?')})")
            return "\n".join(lines)
        
        def gap_fn(oid=obj_id):
            gaps = identify_gaps(knowledge_graph, oid)
            return json.dumps(gaps, indent=2, default=str) if gaps else "No gaps identified."
        
        def suggest_fn(gap_desc):
            return suggest_improvements(
                obj_id, obj_name,
                gaps=gap_desc,
                current_actions=retrieve_fn(),
            )
        
        # Run sync assessment agent
        sync_result = run_sync_assessment(
            obj_id, retrieve_fn, ontology_fn, kpi_coverage_fn
        )
        
        # Recalculate agent score using the agent's KPI coverage findings
        # LLMs are poor at well-calibrated float scores, so we derive it
        covered_kpis = sync_result.get("covered_kpis", [])
        uncovered_kpis = sync_result.get("uncovered_kpis", [])
        total_kpis = len(covered_kpis) + len(uncovered_kpis)
        
        if total_kpis > 0:
            kpi_ratio = len(covered_kpis) / total_kpis
            # Blend: 80% from KPI coverage ratio (objective), 20% from LLM raw score (subjective)
            raw_llm_score = sync_result.get("alignment_score", 0.5)
            agent_score = (0.8 * kpi_ratio) + (0.2 * raw_llm_score)
            
            # Priority Boost removed as requested by user.
            # Scores now reflect raw KPI coverage and content alignment.

                
            agent_score = round(min(1.0, max(0.0, agent_score)), 3)
            sync_result["alignment_score"] = agent_score
            
        else:
            agent_score = sync_result.get("alignment_score", 0.5)
        
        # Combine agent score with ontology score
        ontology_score = ontology_alignment.get(obj_id, {}).get("alignment_score", 0.5)
        # Increased agent weight to 0.8 as LLM semantic understanding is key
        combined_score = (0.8 * agent_score) + (0.2 * ontology_score)
        
        sync_result["combined_score"] = round(combined_score, 3)
        sync_result["ontology_score"] = ontology_score
        sync_result["ontology_data"] = ontology_alignment.get(obj_id, {})

        # Determine alignment level based on combined score
        if combined_score >= 0.8:
            sync_result["alignment_level"] = "Full"
        elif combined_score >= 0.6:
            sync_result["alignment_level"] = "Partial"
        elif combined_score >= 0.4:
            sync_result["alignment_level"] = "Weak"
        else:
            sync_result["alignment_level"] = "Missing"
        
        # Run improvement agent for weak alignments
        improvement_result = None
        if combined_score < 0.7:
            if progress_callback:
                progress_callback(obj_id, "Generating improvements...")
            
            improvement_result = run_improvement_analysis(
                obj_id, gap_fn, retrieve_fn, suggest_fn
            )
        
        # Generate guidance messages
        gaps_str = json.dumps(
            identify_gaps(knowledge_graph, obj_id),
            default=str
        )
        
        guidance = generate_guidance_messages(
            obj_id, obj_name, combined_score,
            sync_result.get("alignment_level", "Partial"),
            gaps_str,
        )
        
        # Store results
        results["objectives"][obj_id] = {
            "sync_assessment": sync_result,
            "improvements": improvement_result,
            "guidance_messages": guidance,
            "combined_score": combined_score,
            "ontology_score": ontology_score,
            "ontology_data": ontology_alignment.get(obj_id, {}),
        }
        
        results["reasoning_traces"][obj_id] = {
            "sync_trace": sync_result.get("reasoning_trace", []),
            "improvement_trace": (
                improvement_result.get("reasoning_trace", [])
                if improvement_result else []
            ),
        }
        
        total_score += combined_score
        
        if progress_callback:
            progress_callback(obj_id, f"Done (score: {combined_score:.1%})")
    
    # Step 3: Compute overall score
    n_objectives = len(STRATEGIC_OBJECTIVES)
    results["overall_score"] = round(total_score / n_objectives, 3) if n_objectives > 0 else 0
    
    if results["overall_score"] >= 0.75:
        results["overall_level"] = "Full"
    elif results["overall_score"] >= 0.50:
        results["overall_level"] = "Partial"
    elif results["overall_score"] >= 0.25:
        results["overall_level"] = "Weak"
    else:
        results["overall_level"] = "Missing"
    
    # Step 4: Generate executive summary
    sync_summary = "\n".join([
        f"- {oid}: {data['combined_score']:.1%} ({data['sync_assessment'].get('alignment_level', 'Unknown')})"
        for oid, data in results["objectives"].items()
    ])
    
    results["executive_summary"] = generate_executive_summary(sync_summary)
    
    # Collect all guidance messages
    results["guidance_messages"] = {
        oid: data.get("guidance_messages", [])
        for oid, data in results["objectives"].items()
    }
    
    return results
