"""
Knowledge Graph Visualization Page
Interactive Pyvis/NetworkX graph of ontology relationships.
"""
import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network
from rdflib import RDF
from src.ontology.schema import ISPS


def show():
    st.markdown("# 🕸️ Knowledge Graph Visualization")
    
    kg = st.session_state.get("knowledge_graph")
    
    if not kg:
        st.info("Run the analysis pipeline first to build the knowledge graph.")
        return
    
    # ─── Graph Stats ─────────────────────────────────────────────────────
    from src.ontology.builder import get_graph_stats
    stats = get_graph_stats(kg)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Triples", stats["total_triples"])
    with col2:
        st.metric("Objectives", stats["objectives"])
    with col3:
        st.metric("Actions", stats["actions"])
    with col4:
        st.metric("KPIs", stats["kpis"])
    with col5:
        st.metric("Risks", stats["risks"])
    
    st.markdown("---")
    
    # ─── Filter Options ──────────────────────────────────────────────────
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        show_types = st.multiselect(
            "Show Entity Types",
            ["StrategicObjective", "Action", "KPI", "Risk", "Person"],
            default=["StrategicObjective", "Action", "KPI"],
        )
    
    with col_filter2:
        physics_enabled = st.checkbox("Enable Physics", value=True)
    
    # ─── Build Pyvis Network ─────────────────────────────────────────────
    net = Network(
        height="600px",
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
    
    if not physics_enabled:
        net.toggle_physics(False)
    
    # Color mapping
    colors = {
        "StrategicObjective": "#6366f1",
        "Action": "#f59e0b",
        "KPI": "#22c55e",
        "Risk": "#ef4444",
        "Person": "#8b5cf6",
        "Department": "#06b6d4",
        "StrategicPlan": "#3b82f6",
        "ActionPlan": "#ec4899",
        "Milestone": "#14b8a6",
    }
    
    sizes = {
        "StrategicPlan": 40,
        "ActionPlan": 40,
        "StrategicObjective": 30,
        "Action": 15,
        "KPI": 20,
        "Risk": 18,
        "Person": 12,
    }
    
    # Add nodes
    added_nodes = set()
    for entity_type in show_types:
        for s in kg.subjects(RDF.type, ISPS[entity_type]):
            node_id = str(s).split("#")[-1]
            if node_id not in added_nodes:
                # Get label
                label = node_id
                for title in kg.objects(s, ISPS["hasTitle"]):
                    label = str(title)[:40]
                
                net.add_node(
                    node_id,
                    label=label,
                    color=colors.get(entity_type, "#888"),
                    size=sizes.get(entity_type, 15),
                    title=f"{entity_type}: {label}",
                    shape="dot",
                )
                added_nodes.add(node_id)
    
    # Add edges
    edge_properties = [
        "hasObjective", "hasAction", "hasKPI", "hasMilestone",
        "supportsObjective", "supportsKPI", "ownedBy", "hasRisk",
    ]
    
    edge_colors = {
        "hasObjective": "#6366f1",
        "hasAction": "#f59e0b",
        "hasKPI": "#22c55e",
        "supportsObjective": "#f97316",
        "supportsKPI": "#10b981",
        "ownedBy": "#8b5cf6",
        "hasRisk": "#ef4444",
    }
    
    for prop_name in edge_properties:
        for s, p, o in kg.triples((None, ISPS[prop_name], None)):
            source = str(s).split("#")[-1]
            target = str(o).split("#")[-1]
            if source in added_nodes and target in added_nodes:
                net.add_edge(
                    source, target,
                    label=prop_name,
                    color=edge_colors.get(prop_name, "#555"),
                    width=2,
                    arrows="to",
                )
    
    # ─── Render ──────────────────────────────────────────────────────────
    try:
        import tempfile
        import os
        
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w')
        net.save_graph(tmpfile.name)
        tmpfile.close()
        
        with open(tmpfile.name, 'r') as f:
            html_content = f.read()
        
        components.html(html_content, height=620, scrolling=True)
        os.unlink(tmpfile.name)
        
    except Exception as e:
        st.error(f"Graph rendering error: {e}")
    
    # ─── Legend ───────────────────────────────────────────────────────────
    st.markdown("### Legend")
    legend_cols = st.columns(5)
    for i, (entity_type, color) in enumerate(list(colors.items())[:5]):
        with legend_cols[i]:
            st.markdown(
                f'<span style="color:{color}; font-size:1.2em;">●</span> {entity_type}',
                unsafe_allow_html=True,
            )
