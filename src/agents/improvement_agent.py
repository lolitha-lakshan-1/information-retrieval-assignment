"""
Improvement Agent
Uses LangGraph ReAct reasoning to identify alignment gaps and suggest actionable improvements.
"""
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.config import OPENAI_API_KEY, LLM_MODEL, STRATEGIC_OBJECTIVES
from src.agents.callbacks import ReasoningCallbackHandler


def run_improvement_analysis(
    objective_id: str,
    gap_identifier_fn,
    retrieve_fn,
    suggest_fn,
) -> dict:
    """
    Run the improvement agent for a specific objective.
    
    Returns:
        Dict with improvement suggestions and reasoning trace
    """
    callback = ReasoningCallbackHandler(agent_name="ImprovementAgent")
    objective_name = STRATEGIC_OBJECTIVES.get(objective_id, "Unknown")
    
    @tool
    def identify_gaps(objective_id: str) -> str:
        """Identify alignment gaps (KPIs without actions, low progress areas). Input: objective ID (e.g., 'SO1'). Returns list of gaps."""
        return gap_identifier_fn(objective_id)
    
    @tool
    def retrieve_context(objective_id: str) -> str:
        """Retrieve existing action plan context for reference. Input: objective ID. Returns relevant action plan chunks."""
        return retrieve_fn(objective_id)
    
    @tool
    def generate_suggestion(gap_description: str) -> str:
        """Generate a specific improvement suggestion for a gap. Input: description of the gap. Returns detailed suggestion."""
        return suggest_fn(gap_description)
    
    tools = [identify_gaps, retrieve_context, generate_suggestion]
    
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.5,
        api_key=OPENAI_API_KEY,
    )
    
    system_message = f"""You are the Improvement Suggestion Agent for the ISPS system.
Your job is to identify alignment gaps and suggest specific, actionable improvements
for the GreenField University strategic plan synchronization.

For each gap found, provide:
- GAP: [description]
- SUGGESTED_ACTION: [specific new action]
- OWNER: [suggested responsible person/department]
- TIMELINE: [realistic timeline]
- IMPACT: [High|Medium|Low]
- REASONING: [why this improvement would help]"""
    
    agent = create_react_agent(llm, tools, prompt=system_message)
    
    input_text = f"Identify gaps and suggest improvements for {objective_id}: {objective_name}"
    
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": input_text}]},
            config={"callbacks": [callback]},
        )
        
        # Extract the final message
        messages = result.get("messages", [])
        output = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and getattr(msg, "type", "") == "ai":
                output = msg.content
                break
        
        # Build trace
        trace = []
        step_num = 0
        for msg in messages:
            step_num += 1
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace.append({
                        "step_number": step_num,
                        "step_type": "action",
                        "agent_name": "ImprovementAgent",
                        "content": f"Calling tool: {tc.get('name', 'unknown')}",
                        "tool_name": tc.get("name", ""),
                    })
            elif hasattr(msg, "type") and msg.type == "tool":
                trace.append({
                    "step_number": step_num,
                    "step_type": "observation",
                    "agent_name": "ImprovementAgent",
                    "content": str(msg.content)[:500],
                    "tool_output": str(msg.content)[:500],
                })
            elif hasattr(msg, "content") and msg.content and getattr(msg, "type", "") == "ai":
                trace.append({
                    "step_number": step_num,
                    "step_type": "final_answer" if msg == messages[-1] else "thought",
                    "agent_name": "ImprovementAgent",
                    "content": str(msg.content)[:500],
                })
        
        return {
            "objective_id": objective_id,
            "objective_name": objective_name,
            "suggestions": output,
            "reasoning_trace": trace if trace else callback.get_trace(),
        }
        
    except Exception as e:
        return {
            "objective_id": objective_id,
            "objective_name": objective_name,
            "suggestions": f"Agent encountered an error: {str(e)}",
            "reasoning_trace": callback.get_trace(),
            "error": str(e),
        }
