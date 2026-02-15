"""
Recommendations Page
AI-generated improvement suggestions with reasoning chains.
"""
import streamlit as st
from src.config import STRATEGIC_OBJECTIVES


def show():
    st.markdown("# 💡 AI-Powered Recommendations")
    
    results = st.session_state.get("analysis_results")
    
    if not results:
        st.info("Run the analysis pipeline first to see recommendations.")
        return
    
    objectives = results.get("objectives", {})
    
    # ─── Master-Detail Selection ─────────────────────────────────────────
    obj_options = list(STRATEGIC_OBJECTIVES.keys())
    
    st.markdown(
        '<p style="font-size:1.15em;font-weight:700;color:#1a1a2e;margin-bottom:2px;">🎯 Select Strategy</p>',
        unsafe_allow_html=True,
    )
    selected_obj = st.selectbox(
        "Select Strategy",
        obj_options,
        format_func=lambda x: f"{x}: {STRATEGIC_OBJECTIVES[x]}",
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    if selected_obj:
        obj_data = objectives.get(selected_obj, {})
        score = obj_data.get("combined_score", 0)
        improvements = obj_data.get("improvements")
        
        # Color-coded header
        if score >= 0.75:
            color = "#22c55e"
            icon = "✅"
            status_text = "Strong Alignment"
        elif score >= 0.5:
            color = "#eab308"
            icon = "⚠️"
            status_text = "Partial Alignment"
        else:
            color = "#ef4444"
            icon = "🔴"
            status_text = "Weak Alignment"
        
        st.markdown(f"""
        <div class="score-card">
            <span style="font-size: 1.2em;">{icon} <strong>{selected_obj}</strong></span><br>
            <span style="font-size: 1em; color: #666;">{STRATEGIC_OBJECTIVES[selected_obj]}</span>
            <div style="margin-top: 8px;">
                <span style="font-size: 1.5em; color: {color}; font-weight: 700;">{score:.0%}</span>
                <span class="badge-{status_text.split()[0].lower()}" style="margin-left: 10px;">{status_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendations
        if improvements and improvements.get("suggestions"):
            st.markdown("### 💡 Recommended Actions")
            st.markdown(improvements["suggestions"])
            
            # Expanded reasoning trace
            imp_trace = improvements.get("reasoning_trace", [])
            if imp_trace:
                st.markdown("---")
                with st.expander("🤖 View Agent Reasoning for these output"):
                    trace_text = _format_trace_text(imp_trace)
                    st.text(trace_text)
                    
        elif score >= 0.7:
            st.success(f"✅ {selected_obj} is well-aligned. No specific improvements recommended at this time.")
        else:
            st.info(f"ℹ️ No specific improvement data generated for {selected_obj}.")


def _format_trace_text(trace: list[dict]) -> str:
    """Format reasoning trace into a single text block."""
    lines = []
    for step in trace:
        step_type = step.get("step_type", "").upper()
        step_num = step.get("step_number", 0)
        content = step.get("content", "")
        tool = step.get("tool_name", "")
        
        header = f"[{step_num}] {step_type}"
        if tool:
            header += f": {tool}"
        
        lines.append(header)
        lines.append("-" * len(header))
        lines.append(content)
        lines.append("")
        
        if step.get("tool_input"):
            lines.append(f"Input: {step['tool_input']}")
            lines.append("")
        
        lines.append("=" * 40)
        lines.append("")
        
    return "\n".join(lines)
