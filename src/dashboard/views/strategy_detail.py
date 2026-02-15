"""
Strategy Detail Page
Per-objective deep dive with alignment heatmap, matching actions, gap analysis, and reasoning trace.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.config import STRATEGIC_OBJECTIVES, OBJECTIVE_KPIS, KPI_DESCRIPTIONS


def show():
    st.markdown("# 📊 Strategy-wise Synchronization Detail")
    
    results = st.session_state.get("analysis_results")
    
    if not results:
        st.info("Run the analysis pipeline first from the sidebar.")
        return
    
    objectives = results.get("objectives", {})
    
    st.markdown("---")
    
    # ─── Strategy Selector ─────────────────────────────────────────────
    st.markdown(
        '<p style="font-size:1.15em;font-weight:700;color:#1a1a2e;margin-bottom:2px;">🎯 Select Strategy</p>',
        unsafe_allow_html=True,
    )
    selected = st.selectbox(
        "Select Strategy",
        options=list(STRATEGIC_OBJECTIVES.keys()),
        format_func=lambda x: f"{x}: {STRATEGIC_OBJECTIVES[x]}",
        label_visibility="collapsed",
    )
    
    if selected:
        obj_data = objectives.get(selected, {})
        sync = obj_data.get("sync_assessment", {})
        
        # Score overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Combined Score", f"{obj_data.get('combined_score', 0):.0%}")
        with col2:
            st.metric("Agent Score", f"{sync.get('alignment_score', 0):.0%}")
        with col3:
            st.metric("Ontology Score", f"{obj_data.get('ontology_score', 0):.0%}")
        with col4:
            level = sync.get("alignment_level", "Unknown")
            st.metric("Level", level)
        
        # Justification
        st.markdown("#### 💬 Agent Justification")
        st.info(sync.get("justification", "No justification available."))
        
        # Covered / Uncovered KPIs
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### ✅ Covered KPIs")
            covered = sync.get("covered_kpis", [])
            if covered:
                for kpi in covered:
                    # Handle SOx_ prefix if present (e.g., SO1_D1 -> D1)
                    lookup_key = kpi.split("_")[1] if "_" in kpi else kpi
                    desc = KPI_DESCRIPTIONS.get(lookup_key, "Unknown KPI")
                    st.markdown(f"- **✅ {kpi}**: {desc}")
            else:
                st.caption("No covered KPIs reported")
        
        with col_right:
            st.markdown("#### ❌ Uncovered KPIs")
            uncovered = sync.get("uncovered_kpis", [])
            if uncovered:
                for kpi in uncovered:
                    # Handle SOx_ prefix if present
                    lookup_key = kpi.split("_")[1] if "_" in kpi else kpi
                    desc = KPI_DESCRIPTIONS.get(lookup_key, "Unknown KPI")
                    st.markdown(f"- **❌ {kpi}**: {desc}")
            else:
                st.caption("All KPIs covered")
        
        # Ontology data
        ont_data = obj_data.get("ontology_data", {})
        if ont_data:
            st.markdown("#### 🕸️ Ontology Mapping")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Actions Found", ont_data.get("total_actions", 0))
            with col_b:
                st.metric("KPI Coverage", f"{ont_data.get('kpi_coverage', 0):.0%}")
            with col_c:
                st.metric("Avg Progress", f"{ont_data.get('avg_progress', 0):.0f}%")
        
        # Guidance messages
        guidance = obj_data.get("guidance_messages", [])
        if guidance:
            st.markdown("#### 📋 Guidance")
            for msg in guidance:
                st.markdown(f"> {msg}")
        
        # Reasoning trace (expandable at bottom)
        traces = results.get("reasoning_traces", {}).get(selected, {})
        sync_trace = traces.get("sync_trace", [])
        
        if sync_trace:
            st.markdown("---")
            st.markdown("#### 🤖 Agent Reasoning Trace")
            with st.expander("View full reasoning trace", expanded=False):
                trace_text = _format_trace_text(sync_trace)
                st.text(trace_text)


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
