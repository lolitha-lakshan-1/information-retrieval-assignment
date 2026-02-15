"""
Sync Assessment Agent
Uses LangGraph ReAct reasoning with tools to assess alignment between
strategic objectives and action plan items.
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.config import OPENAI_API_KEY, LLM_MODEL, STRATEGIC_OBJECTIVES
from src.agents.callbacks import ReasoningCallbackHandler, ReasoningStep
from datetime import datetime


def run_sync_assessment(
    objective_id: str,
    retrieve_fn,
    ontology_mapping_fn,
    kpi_coverage_fn,
) -> dict:
    """
    Run the sync assessment agent for a specific objective.
    
    Returns:
        Dict with alignment results and reasoning trace
    """
    callback = ReasoningCallbackHandler(agent_name="SyncAgent")
    objective_name = STRATEGIC_OBJECTIVES.get(objective_id, "Unknown")
    
    # Define tools using the @tool decorator with closures
    @tool
    def retrieve_action_chunks(objective_id: str) -> str:
        """Retrieve relevant action plan chunks for a strategic objective. Input: objective ID (e.g., 'SO1'). Returns text chunks from the action plan."""
        return retrieve_fn(objective_id)
    
    @tool
    def query_ontology(objective_id: str) -> str:
        """Get ontology-based mapping showing which actions are linked to which objectives and KPIs. Input: objective ID (e.g., 'SO1'). Returns structured mapping data."""
        return ontology_mapping_fn(objective_id)
    
    @tool
    def check_kpi_coverage(objective_id: str) -> str:
        """Check how many KPIs for an objective have supporting actions. Input: objective ID (e.g., 'SO1'). Returns coverage statistics."""
        return kpi_coverage_fn(objective_id)
    
    tools = [retrieve_action_chunks, query_ontology, check_kpi_coverage]
    
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.1,
        api_key=OPENAI_API_KEY,
    )
    
    system_message = f"""You are the Synchronization Assessment Agent for the ISPS system.
Your job is to assess how well the Action Plan aligns with a Strategic Objective.

Use the available tools to gather data, then provide your assessment.

IMPORTANT: For each KPI, independently evaluate whether specific actions directly
address it. A KPI is "covered" if at least one action SPECIFICALLY targets what 
that KPI measures. Do not assume coverage just because actions exist under the 
same objective.

Calculate your ALIGNMENT_SCORE proportionally:
- Consider what fraction of KPIs are covered
- Factor in the progress/completion of supporting actions
- Factor in whether actions are detailed enough to achieve KPI targets
- A score of 0.8+ means most KPIs are well-covered with good progress
- A score of 0.5-0.8 means partial coverage with some gaps
- A score below 0.5 means significant gaps exist

Your Final Answer MUST be in this exact format:
ALIGNMENT_SCORE: [0.0-1.0]
ALIGNMENT_LEVEL: [Full|Partial|Weak|Missing]
COVERED_KPIS: [comma-separated list of KPI IDs that have supporting actions]
UNCOVERED_KPIS: [comma-separated list of KPI IDs without adequate action support]
JUSTIFICATION: [2-3 sentences explaining the score]
CONFIDENCE: [0.0-1.0]"""
    
    agent = create_react_agent(llm, tools, prompt=system_message)
    
    input_text = f"Assess the alignment for objective {objective_id}: {objective_name}"
    
    try:
        # Run the agent
        result = agent.invoke(
            {"messages": [{"role": "user", "content": input_text}]},
            config={"callbacks": [callback]},
        )
        
        # Extract the final message
        messages = result.get("messages", [])
        output = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                output = msg.content
                break
        
        # Build reasoning trace from messages
        trace = []
        step_num = 0
        for msg in messages:
            step_num += 1
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace.append({
                        "step_number": step_num,
                        "step_type": "action",
                        "agent_name": "SyncAgent",
                        "content": f"Calling tool: {tc.get('name', 'unknown')}",
                        "tool_name": tc.get("name", ""),
                        "tool_input": str(tc.get("args", {})),
                    })
            elif hasattr(msg, "type") and msg.type == "tool":
                trace.append({
                    "step_number": step_num,
                    "step_type": "observation",
                    "agent_name": "SyncAgent",
                    "content": str(msg.content)[:500],
                    "tool_name": getattr(msg, "name", ""),
                    "tool_output": str(msg.content)[:500],
                })
            elif hasattr(msg, "content") and msg.content and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                if msg.type == "ai":
                    trace.append({
                        "step_number": step_num,
                        "step_type": "thought" if step_num < len(messages) else "final_answer",
                        "agent_name": "SyncAgent",
                        "content": str(msg.content)[:500],
                    })
        
        parsed = _parse_agent_output(output)
        parsed["reasoning_trace"] = trace if trace else callback.get_trace()
        parsed["objective_id"] = objective_id
        parsed["objective_name"] = objective_name
        
        return parsed
        
    except Exception as e:
        return {
            "objective_id": objective_id,
            "objective_name": objective_name,
            "alignment_score": 0.5,
            "alignment_level": "Partial",
            "justification": f"Agent encountered an error: {str(e)}",
            "confidence": 0.3,
            "reasoning_trace": callback.get_trace(),
            "error": str(e),
        }


def _parse_agent_output(output: str) -> dict:
    """Parse structured agent output."""
    result = {
        "alignment_score": 0.5,
        "alignment_level": "Partial",
        "covered_kpis": [],
        "uncovered_kpis": [],
        "justification": "",
        "confidence": 0.5,
    }
    
    for line in output.strip().split("\n"):
        line = line.strip()
        if line.startswith("ALIGNMENT_SCORE:"):
            try:
                result["alignment_score"] = float(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        elif line.startswith("ALIGNMENT_LEVEL:"):
            result["alignment_level"] = line.split(":")[1].strip()
        elif line.startswith("COVERED_KPIS:"):
            result["covered_kpis"] = [k.strip() for k in line.split(":")[1].split(",") if k.strip()]
        elif line.startswith("UNCOVERED_KPIS:"):
            result["uncovered_kpis"] = [k.strip() for k in line.split(":")[1].split(",") if k.strip()]
        elif line.startswith("JUSTIFICATION:"):
            result["justification"] = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = float(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
    
    return result
