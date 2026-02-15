"""
Agent Reasoning Callbacks
Custom LangChain callback handler that captures every Thought → Action → Observation
step for display on the Streamlit dashboard.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from langchain_core.callbacks import BaseCallbackHandler


@dataclass
class ReasoningStep:
    """A single step in the agent's reasoning trace."""
    step_number: int
    step_type: str          # "thought" | "action" | "observation" | "final_answer"
    agent_name: str         # "SyncAgent" | "ImprovementAgent" | "Orchestrator"
    content: str            # The actual text
    tool_name: str | None = None
    tool_input: dict | None = None
    tool_output: str | None = None
    confidence: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type,
            "agent_name": self.agent_name,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_input": str(self.tool_input) if self.tool_input else None,
            "tool_output": self.tool_output[:500] if self.tool_output else None,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class ReasoningCallbackHandler(BaseCallbackHandler):
    """
    Captures agent reasoning steps for dashboard display.
    
    Collects Thought/Action/Observation steps from the ReAct agent loop
    and stores them as ReasoningStep objects.
    """
    
    def __init__(self, agent_name: str = "Agent"):
        self.agent_name = agent_name
        self.steps: list[ReasoningStep] = []
        self.step_counter = 0
        self._current_tool_name = None
        self._current_tool_input = None
    
    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs: Any) -> None:
        pass
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Capture the agent's thought/reasoning."""
        try:
            text = response.generations[0][0].text
            if text.strip():
                # Parse thought from ReAct output
                lines = text.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line.lower().startswith("thought:"):
                        self.step_counter += 1
                        self.steps.append(ReasoningStep(
                            step_number=self.step_counter,
                            step_type="thought",
                            agent_name=self.agent_name,
                            content=line.replace("Thought:", "").strip(),
                        ))
                    elif line.lower().startswith("final answer:"):
                        self.step_counter += 1
                        self.steps.append(ReasoningStep(
                            step_number=self.step_counter,
                            step_type="final_answer",
                            agent_name=self.agent_name,
                            content=line.replace("Final Answer:", "").strip(),
                        ))
        except (IndexError, AttributeError):
            pass
    
    def on_tool_start(self, serialized: dict, input_str: str, **kwargs: Any) -> None:
        """Capture the action (tool call)."""
        self._current_tool_name = serialized.get("name", "unknown_tool")
        self._current_tool_input = input_str
        
        self.step_counter += 1
        self.steps.append(ReasoningStep(
            step_number=self.step_counter,
            step_type="action",
            agent_name=self.agent_name,
            content=f"Calling tool: {self._current_tool_name}",
            tool_name=self._current_tool_name,
            tool_input={"input": input_str},
        ))
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Capture the observation (tool output)."""
        self.step_counter += 1
        self.steps.append(ReasoningStep(
            step_number=self.step_counter,
            step_type="observation",
            agent_name=self.agent_name,
            content=str(output)[:1000],
            tool_name=self._current_tool_name,
            tool_output=str(output)[:1000],
        ))
    
    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Capture the final answer if not already captured."""
        try:
            output = finish.return_values.get("output", "")
            if output and not any(s.step_type == "final_answer" for s in self.steps):
                self.step_counter += 1
                self.steps.append(ReasoningStep(
                    step_number=self.step_counter,
                    step_type="final_answer",
                    agent_name=self.agent_name,
                    content=str(output),
                ))
        except AttributeError:
            pass
    
    def get_trace(self) -> list[dict]:
        """Get the full reasoning trace as a list of dicts."""
        return [step.to_dict() for step in self.steps]
    
    def clear(self):
        """Clear the trace for a new run."""
        self.steps = []
        self.step_counter = 0
