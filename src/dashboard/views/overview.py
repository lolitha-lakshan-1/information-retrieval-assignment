"""
Overview Page
Displays overall sync score, radar + knowledge graph, objective scores, and sync summary.
"""
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from src.config import STRATEGIC_OBJECTIVES


def _render_knowledge_graph_mini(show_types):
    """Render a compact knowledge graph for embedding in the overview."""
    kg = st.session_state.get("knowledge_graph")
    if not kg:
        st.caption("Knowledge graph not available yet.")
        return

    from pyvis.network import Network
    from rdflib import RDF
    from src.ontology.schema import ISPS

    net = Network(
        height="380px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=True,
    )
    net.force_atlas_2based(
        gravity=-50,
        central_gravity=0.01,
        spring_length=200,
        spring_strength=0.08,
    )

    colors = {
        "StrategicObjective": "#6366f1",
        "Action": "#f59e0b",
        "KPI": "#22c55e",
        "Risk": "#ef4444",
        "Person": "#8b5cf6",
    }
    sizes = {
        "StrategicObjective": 30,
        "Action": 15,
        "KPI": 20,
        "Risk": 18,
        "Person": 12,
    }

    added_nodes = set()
    for entity_type in show_types:
        for s in kg.subjects(RDF.type, ISPS[entity_type]):
            node_id = str(s).split("#")[-1]
            if node_id not in added_nodes:
                label = node_id
                for title in kg.objects(s, ISPS["hasTitle"]):
                    label = str(title)[:30]
                net.add_node(
                    node_id,
                    label=label,
                    color=colors.get(entity_type, "#888"),
                    size=sizes.get(entity_type, 15),
                    title=f"{entity_type}: {label}",
                    shape="dot",
                )
                added_nodes.add(node_id)

    edge_properties = [
        "hasObjective", "hasAction", "hasKPI",
        "supportsObjective", "supportsKPI", "hasRisk",
    ]
    edge_colors = {
        "hasObjective": "#6366f1",
        "hasAction": "#f59e0b",
        "hasKPI": "#22c55e",
        "supportsObjective": "#f97316",
        "supportsKPI": "#10b981",
        "hasRisk": "#ef4444",
    }
    for prop_name in edge_properties:
        for s, p, o in kg.triples((None, ISPS[prop_name], None)):
            source = str(s).split("#")[-1]
            target = str(o).split("#")[-1]
            if source in added_nodes and target in added_nodes:
                net.add_edge(
                    source, target,
                    color=edge_colors.get(prop_name, "#555"),
                    width=1.5,
                    arrows="to",
                )

    try:
        import tempfile, os
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w')
        net.save_graph(tmpfile.name)
        tmpfile.close()
        with open(tmpfile.name, 'r') as f:
            html_content = f.read()
        components.html(html_content, height=400, scrolling=False)
        os.unlink(tmpfile.name)
    except Exception as e:
        st.error(f"Graph rendering error: {e}")


def show():
    st.markdown("# 🏠 Strategic Plan Synchronization Overview")

    # ─── Custom Styling for Tags ──────────────────────────────────────────
    st.markdown("""
    <style>
    /* Change multiselect tag color to light green to match theme */
    span[data-baseweb="tag"] {
      background-color: #dcfce7 !important;
      color: #166534 !important;
      border: 1px solid #86efac !important;
    }
    </style>
    """, unsafe_allow_html=True)

    results = st.session_state.get("analysis_results")

    if not results:
        st.info("👈 Click **'🚀 Run Full Analysis'** in the sidebar to start the pipeline.")
        st.markdown("""
        ### What this system does:
        1. **Chunks** both documents using 3 strategies (fixed, semantic, agentic)
        2. **Indexes** chunks in ChromaDB vector database
        3. **Builds** an RDF knowledge graph with ontology
        4. **Analyzes** alignment using ReAct AI agents
        5. **Generates** recommendations and guidance
        """)
        return

    # ─── Overall Score Gauge ─────────────────────────────────────────────
    # ─── Overall Score Gauge ─────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    overall_score = results.get("overall_score", 0)
    
    with col1:
        st.metric("Overall Sync Score", f"{overall_score:.0%}")
    
    with col2:
        n_objectives = len(results.get("objectives", {}))
        st.metric("Strategies Analyzed", n_objectives)
        
    with col3:
        weak_count = sum(
            1 for obj in results.get("objectives", {}).values()
            if obj.get("combined_score", 0) < 0.6
        )
        st.metric("⚠️ Needs Attention", weak_count)

    st.markdown("---")

    # ─── Row 1: Radar + Knowledge Graph side by side ─────────────────────
    objectives = results.get("objectives", {})

    col_radar, col_kg = st.columns(2)

    with col_radar:
        st.markdown("### Synchronization Radar")

        categories = []
        scores = []

        for obj_id in STRATEGIC_OBJECTIVES:
            obj_data = objectives.get(obj_id, {})
            categories.append(obj_id)
            scores.append(obj_data.get("combined_score", 0) * 100)

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(99, 102, 241, 0.2)',
            line=dict(color='rgb(99, 102, 241)', width=2),
            marker=dict(size=8),
            name='Sync Score',
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10, color='#555'),
                    gridcolor='rgba(0,0,0,0.08)',
                ),
                angularaxis=dict(
                    tickfont=dict(size=13, color='#1a1a2e', family='Inter, sans-serif'),
                    gridcolor='rgba(0,0,0,0.08)',
                ),
                bgcolor='rgba(0,0,0,0)',
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a2e'),
            showlegend=False,
            height=420,
            margin=dict(l=60, r=60, t=30, b=30),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_kg:
        st.markdown("### Knowledge Graph")
        kg_types = st.multiselect(
            "Entity Types",
            ["StrategicObjective", "Action", "KPI", "Risk", "Person"],
            default=["StrategicObjective", "Action", "KPI"],
            key="overview_kg_types",
        )
        _render_knowledge_graph_mini(kg_types)

    # ─── Row 2: Synchronization Score — horizontal cards ─────────────────
    st.markdown("### Synchronization Score")

    obj_cols = st.columns(len(STRATEGIC_OBJECTIVES))
    for i, obj_id in enumerate(STRATEGIC_OBJECTIVES):
        obj_data = objectives.get(obj_id, {})
        score = obj_data.get("combined_score", 0)
        level = obj_data.get("sync_assessment", {}).get("alignment_level", "Unknown")
        badge_color = {"full": "#22c55e", "partial": "#f59e0b", "weak": "#ef4444", "missing": "#94a3b8"}.get(level.lower(), "#94a3b8")
        obj_name = STRATEGIC_OBJECTIVES[obj_id]

        with obj_cols[i]:
            st.markdown(
                f'<div style="text-align:center;padding:10px 4px;border:1px solid #e2e8f0;border-radius:10px;background:#fff;">'
                f'<div style="font-size:0.75em;color:#555;font-weight:600;">{obj_id}</div>'
                f'<div style="font-size:0.65em;color:#888;margin:2px 0 4px;line-height:1.2;">{obj_name}</div>'
                f'<div style="font-size:1.4em;font-weight:800;color:#1a1a2e;">{score:.0%}</div>'
                f'<span style="background:{badge_color};color:#fff;padding:1px 8px;border-radius:10px;font-size:0.65em;font-weight:600;">{level}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ─── Synchronization Summary ─────────────────────────────────────────
    st.markdown("### 📝 Synchronization Summary")
    summary = results.get("executive_summary", "")

    if summary:
        # Strip the "Executive Summary: ..." line if present (handles bold, heading, plain text)
        import re
        lines = summary.strip().split("\n")
        filtered = []
        for line in lines:
            clean = re.sub(r'[#*_]+', '', line).strip().lower()
            if clean.startswith("executive summary"):
                continue
            filtered.append(line)
        cleaned = "\n".join(filtered)
        # Rename subheadings per user request
        cleaned = cleaned.replace("Critical Gaps Requiring Attention:", "Critical Gaps:")
        cleaned = cleaned.replace("Top 3 Priority Recommendations:", "Top 3 Recommendations:")
        st.markdown(cleaned)
    else:
        if st.button("🤖 Generate Synchronization Summary"):
            with st.spinner("Generating summary..."):
                from src.rag.chains import generate_executive_summary
                sync_summary = "\n".join([
                    f"- {oid}: {data.get('combined_score', 0):.1%} ({data.get('sync_assessment', {}).get('alignment_level', 'Unknown')})"
                    for oid, data in objectives.items()
                ])
                summary = generate_executive_summary(sync_summary)
                st.session_state.analysis_results["executive_summary"] = summary
                st.rerun()

    st.markdown("---")

    # ─── Agent Reasoning Trace ────────────────────────────────────────────
    st.markdown("### 🤖 Agent Reasoning Trace")
    all_traces = results.get("reasoning_traces", {})

    if all_traces:
        for obj_id in STRATEGIC_OBJECTIVES:
            traces = all_traces.get(obj_id, {})
            sync_trace = traces.get("sync_trace", [])
            if sync_trace:
                with st.expander(f"{obj_id}: {STRATEGIC_OBJECTIVES[obj_id]}", expanded=False):
                    trace_lines = []
                    for step in sync_trace:
                        step_type = step.get("step_type", "").upper()
                        step_num = step.get("step_number", 0)
                        content = step.get("content", "")
                        tool = step.get("tool_name", "")
                        header = f"[{step_num}] {step_type}"
                        if tool:
                            header += f": {tool}"
                        trace_lines.append(header)
                        trace_lines.append("-" * len(header))
                        trace_lines.append(content)
                        trace_lines.append("")
                        if step.get("tool_input"):
                            trace_lines.append(f"Input: {step['tool_input']}")
                            trace_lines.append("")
                        trace_lines.append("=" * 40)
                        trace_lines.append("")
                    st.text("\n".join(trace_lines))
    else:
        st.caption("No reasoning traces available. Run the analysis pipeline to generate traces.")
