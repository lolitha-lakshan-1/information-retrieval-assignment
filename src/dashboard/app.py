"""
ISPS Dashboard — Main Application
Intelligent Strategic Plan Synchronization System
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import DASHBOARD_TITLE, DASHBOARD_ICON

st.set_page_config(
    page_title=DASHBOARD_TITLE,
    page_icon=DASHBOARD_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Light premium theme */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 50%, #f1f5f9 100%);
        color: #000000;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.1);
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #000000 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #0f172a !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(90deg, #1e1b4b, #312e81, #4338ca);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* Cards */
    .score-card {
        background: #ffffff;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: all 0.3s ease;
    }
    .score-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
    }
    
    /* Status badges */
    .badge-full { 
        background: #dcfce7; 
        color: #052e16; 
        padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;
        border: 1px solid #86efac;
    }
    .badge-partial { 
        background: #fef9c3; 
        color: #422006; 
        padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;
        border: 1px solid #fde047;
    }
    .badge-weak { 
        background: #ffedd5; 
        color: #7c2d12; 
        padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;
        border: 1px solid #fdba74;
    }
    .badge-missing { 
        background: #fee2e2; 
        color: #7f1d1d; 
        padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;
        border: 1px solid #fca5a5;
    }
    
    /* Reasoning trace */
    .thought-step { 
        border-left: 3px solid #60a5fa; padding-left: 1rem; margin: 0.5rem 0;
        background: #eff6ff; border-radius: 0 8px 8px 0; padding: 0.8rem;
        color: #000000;
    }
    .action-step { 
        border-left: 3px solid #f59e0b; padding-left: 1rem; margin: 0.5rem 0;
        background: #fffbeb; border-radius: 0 8px 8px 0; padding: 0.8rem;
        color: #000000;
    }
    .observation-step { 
        border-left: 3px solid #22c55e; padding-left: 1rem; margin: 0.5rem 0;
        background: #f0fdf4; border-radius: 0 8px 8px 0; padding: 0.8rem;
        color: #000000;
    }
    .final-step { 
        border-left: 3px solid #8b5cf6; padding-left: 1rem; margin: 0.5rem 0;
        background: #f5f3ff; border-radius: 0 8px 8px 0; padding: 0.8rem;
        color: #000000;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eff6ff !important;
        color: #1e3a8a !important;
        border-color: #bfdbfe !important;
    }
    
    /* General Text */
    p, li, span {
        color: #000000;
    }
    
    /* Force text color in code blocks and expanders */
    code, pre, .stMarkdown, .stText {
        color: #000000 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Selectbox styling - AGGRESSIVE FIX */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cbd5e1 !important;
    }
    
    /* The selected value text specifically */
    div[data-baseweb="select"] div {
        color: #000000 !important;
    }
    
    /* Verified Dropdown Overlay */
    div[data-baseweb="popover"], div[data-baseweb="popover"] div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    div[data-baseweb="unknown"] {
        background-color: #ffffff !important;
    }
    
    /* Options in the dropdown */
    li[data-baseweb="option"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Expander / Agent Reasoning styling */
    .streamlit-expanderHeader {
        color: #000000 !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderHeader p {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 8px 8px;
    }
    
    /* Force all paragraph text to black to catch any stragglers */
    .stMarkdown p {
        color: #000000 !important;
    }
""", unsafe_allow_html=True)

# ─── Initialize Session State ────────────────────────────────────────────────
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "knowledge_graph" not in st.session_state:
    st.session_state.knowledge_graph = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "pipeline_run" not in st.session_state:
    st.session_state.pipeline_run = False
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False

# ─── Auto-load cached results on startup ─────────────────────────────────────
if not st.session_state.pipeline_run and not st.session_state.pipeline_running:
    from src.ingestion.pipeline_cache import load_pipeline_cache
    cached = load_pipeline_cache()
    if cached:
        st.session_state.analysis_results = cached.get("analysis_results")
        st.session_state.chunks = cached.get("chunks")
        st.session_state.eval_results = cached.get("eval_results")
        st.session_state.pipeline_run = True
        # Rebuild KG from docs if needed (lightweight)
        if st.session_state.knowledge_graph is None:
            try:
                from src.ingestion.document_loader import load_all_documents
                from src.ontology.builder import build_knowledge_graph
                docs = load_all_documents()
                kg = build_knowledge_graph(docs["strategic_plan"], docs["action_plan"])
                st.session_state.knowledge_graph = kg
            except Exception:
                pass  # KG is optional for basic functionality

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🎯 ISPS")
    st.markdown("**Intelligent Strategic Plan**\n**Synchronization System**")
    st.markdown("---")
    
    page = st.radio(
        "📑 Navigate",
        [
            "🏠 Overview",
            "💬 Chat",
            "📊 Strategy Detail & Guidance",
            "💡 Recommendations",
            "📋 Ground Truth",
        ],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    # Pipeline controls
    force_rerun = st.checkbox("Force re-run (discard cache)", value=False)
    if st.button("🚀 Run Full Analysis", use_container_width=True, type="primary"):
        if force_rerun:
            from src.ingestion.pipeline_cache import clear_pipeline_cache
            clear_pipeline_cache()
            st.session_state.pipeline_run = False
            st.session_state.analysis_results = None
            st.session_state.chunks = None
            st.session_state.knowledge_graph = None
        st.session_state.run_pipeline = True
    
    if st.session_state.pipeline_run:
        st.success("✅ Pipeline complete")
        if st.session_state.analysis_results:
            score = st.session_state.analysis_results.get("overall_score", 0)
            st.metric("Overall Sync", f"{score:.0%}")
    
    st.markdown("---")
    st.caption("GreenField University")
    st.caption("Strategic Plan 2024-2029")

# ─── Pipeline Runner ─────────────────────────────────────────────────────────
if st.session_state.get("run_pipeline") and not st.session_state.get("pipeline_running"):
    st.session_state.run_pipeline = False
    st.session_state.pipeline_running = True
    
    with st.spinner("🔄 Running full analysis pipeline..."):
        progress_bar = st.progress(0, text="Initializing...")
        
        try:
            # Step 1: Load documents
            progress_bar.progress(5, text="📄 Loading documents...")
            from src.ingestion.document_loader import load_all_documents
            docs = load_all_documents()
            
            # Step 2: Run chunking
            progress_bar.progress(10, text="✂️ Fixed chunking — strategic plan...")
            from src.chunking.fixed_chunker import fixed_chunk
            from src.chunking.semantic_chunker import semantic_chunk
            # from src.chunking.agentic_chunker import agentic_chunk # Commented out
            
            sp_text = docs["strategic_plan"]
            ap_text = docs["action_plan"]
            
            sp_fixed = fixed_chunk(sp_text, "strategic_plan", "strategic_plan.docx")
            progress_bar.progress(13, text="✂️ Fixed chunking — action plan...")
            ap_fixed = fixed_chunk(ap_text, "action_plan", "action_plan.docx")
            
            progress_bar.progress(16, text="🔗 Semantic chunking — strategic plan...")
            sp_semantic = semantic_chunk(sp_text, "strategic_plan", "strategic_plan.docx")
            progress_bar.progress(20, text="🔗 Semantic chunking — action plan...")
            ap_semantic = semantic_chunk(ap_text, "action_plan", "action_plan.docx")
            
            progress_bar.progress(25, text="🤖 Agentic chunking — strategic plan (LLM-driven, may take a minute)...")
            # sp_agentic = agentic_chunk(sp_text, "strategic_plan", "strategic_plan.docx")
            sp_agentic = []
            progress_bar.progress(35, text="🤖 Agentic chunking — action plan (LLM-driven, may take a minute)...")
            # ap_agentic = agentic_chunk(ap_text, "action_plan", "action_plan.docx")
            ap_agentic = []
            
            all_sp_chunks = sp_fixed + sp_semantic + sp_agentic
            all_ap_chunks = ap_fixed + ap_semantic + ap_agentic
            
            st.session_state.chunks = {
                "strategic_plan": all_sp_chunks,
                "action_plan": all_ap_chunks,
            }
            
            # Step 3: Ingest into vector store
            progress_bar.progress(45, text="💾 Ingesting into ChromaDB...")
            from src.ingestion.vector_store import clear_all_collections, ingest_all_chunks
            clear_all_collections()
            counts = ingest_all_chunks(all_sp_chunks, all_ap_chunks)
            
            # Step 4: Build knowledge graph
            progress_bar.progress(55, text="🕸️ Building knowledge graph...")
            from src.ontology.builder import build_knowledge_graph
            kg = build_knowledge_graph(sp_text, ap_text)
            st.session_state.knowledge_graph = kg
            
            # Step 5: Run agent analysis
            progress_bar.progress(65, text="🤖 Running agent analysis (this takes a few minutes)...")
            from src.agents.orchestrator import run_full_analysis
            
            def update_progress(obj_id, status):
                from src.config import STRATEGIC_OBJECTIVES
                obj_ids = list(STRATEGIC_OBJECTIVES.keys())
                idx = obj_ids.index(obj_id) if obj_id in obj_ids else 0
                pct = 65 + int((idx / len(obj_ids)) * 25)
                progress_bar.progress(pct, text=f"🤖 {obj_id}: {status}")
            
            results = run_full_analysis(kg, progress_callback=update_progress)
            st.session_state.analysis_results = results
            
            # Step 6: Run evaluation
            progress_bar.progress(95, text="📈 Running evaluation...")
            from src.evaluation.evaluator import run_evaluation
            eval_results = run_evaluation(
                results,
                chunks=st.session_state.chunks,
            )
            st.session_state.eval_results = eval_results
            
            # Save to disk cache
            progress_bar.progress(98, text="💾 Saving results to cache...")
            from src.ingestion.pipeline_cache import save_pipeline_cache
            save_pipeline_cache(
                analysis_results=results,
                chunks=st.session_state.chunks,
                eval_results=eval_results,
            )
            
            progress_bar.progress(100, text="✅ Complete!")
            st.session_state.pipeline_run = True
            st.session_state.pipeline_running = False
            st.success("✅ Pipeline completed successfully! Navigate the sidebar to explore results.")
            
        except Exception as e:
            st.session_state.pipeline_running = False
            st.error(f"Pipeline error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ─── Page Routing ────────────────────────────────────────────────────────────
# ─── Page Routing ────────────────────────────────────────────────────────────
from src.dashboard.views import (
    overview,
    strategy_detail,
    knowledge_graph,
    recommendations,
    evaluation,
    chat_page,
)

if page == "🏠 Overview":
    overview.show()
elif page == "💬 Chat":
    chat_page.show()
elif page == "📊 Strategy Detail & Guidance":
    strategy_detail.show()
elif page == "🕸️ Knowledge Graph":
    knowledge_graph.show()
elif page == "💡 Recommendations":
    recommendations.show()
elif page == "📋 Ground Truth":
    evaluation.show()
