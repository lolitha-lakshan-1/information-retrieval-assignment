"""
Evaluation Results Page
Displays precision/recall, gap detection, alignment accuracy, and chunking quality.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.config import STRATEGIC_OBJECTIVES


def show():
    st.markdown("# 📋 Ground Truth & Testing Results")
    
    eval_results = st.session_state.get("eval_results")
    results = st.session_state.get("analysis_results")
    
    if not eval_results:
        st.info("Run the analysis pipeline first to see evaluation results.")
        return
    
    # ─── Tab Layout ──────────────────────────────────────────────────────
    tab1, tab2 = st.tabs([
        "📋 Ground Truth",
        "✂️ Chunking Quality",
    ])
    
    # ─── Tab 1: Ground Truth ─────────────────────────────────────────────
    with tab1:
        st.markdown("### 📋 Ground Truth Comparison")
        
        st.info("""
**How to read this table:**

*   **Ground Truth Score (Ideal)**: Derived manually from the *Action Plan's Alignment Matrix*. It represents the "ideal" coverage based on mapped actions (often 100%).
*   **AI Score**: The system's calculated semantic alignment score based on content analysis of the provided documents.
*   **Deviation**: The difference between AI assessment and manual baseline.
    *   **Small Gap (< 10%)**: AI agrees with the plan.
    *   **Large Negative Gap (> 40%)**: **Missing Evidence**. The plan claims to support this objective, but the AI could not find sufficient evidence in the document text to verify the expected actions. Check the "Reasoning" section below to see exactly what was missed.
        """)
        
        gt_comparison = eval_results.get("ground_truth_comparison", {})
        
        if gt_comparison:
            rows = []
            for obj_id, data in gt_comparison.items():
                gt = data.get("ground_truth", {})
                
                # Calculate scores
                sys_score = data.get("system_score", 0)
                gt_score = gt.get("coverage_pct", 0)
                deviation = sys_score - gt_score
                
                # Format counts summary
                counts = []
                if gt.get("full"): counts.append(f"{gt['full']} Full")
                if gt.get("partial"): counts.append(f"{gt['partial']} Part")
                if gt.get("weak"): counts.append(f"{gt['weak']} Weak")
                if gt.get("missing"): counts.append(f"{gt['missing']} Miss")
                gt_summary = ", ".join(counts)
                
                # Generate explanation
                if deviation > 0.1:
                    explanation = "AI detected broader semantic coverage than manual mapping."
                elif deviation < -0.1:
                    explanation = "AI scoring is stricter than manual baseline."
                else:
                    explanation = "High alignment between AI and Ground Truth."

                rows.append({
                    "Objective": f"{obj_id}",
                    "🤖 AI Score": sys_score * 100,
                    "✅ Ground Truth Score": gt_score * 100,
                    "⚡ Deviation": deviation * 100,
                    "Coverage Details": gt_summary,
                })
            
            # Helper to style deviation
            def color_deviation(val):
                if isinstance(val, str) and val.endswith("%"):
                    val_float = float(val.strip('%+'))
                    if abs(val_float) < 10: return "color: green"
                    return "color: red"
                return ""

            df = pd.DataFrame(rows)
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "🤖 AI Score": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                    "✅ Ground Truth Score": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                    "⚡ Deviation": st.column_config.NumberColumn(format="%.1f%%"),
                }
            )

            st.write("")
            st.markdown("### 🔍 Reasoning")
            st.caption("Expand each objective to see a summary of what was verified and what evidence is missing.")

            from src.config import KPI_DESCRIPTIONS

            for obj_id, data in gt_comparison.items():
                gt = data.get("ground_truth", {})
                details = gt.get("kpi_details", [])
                covered_kpis = data.get("covered_kpis", [])

                # Build a quick summary line
                verified = []
                missing = []
                for kpi in details:
                    kpi_id = kpi["kpi_id"]
                    kpi_title = KPI_DESCRIPTIONS.get(kpi_id.split("_")[1], "Unknown KPI")
                    if kpi_id in covered_kpis:
                        verified.append(kpi_title)
                    else:
                        missing.append(kpi_title)

                summary_label = f"**{obj_id}: {data['objective']}** — ✅ {len(verified)} verified, ❌ {len(missing)} missing"

                with st.expander(summary_label):
                    if not details:
                        st.write("No detailed breakdown available.")
                        continue

                    if verified:
                        st.markdown("<p style='font-size:0.85em; margin-bottom:4px;'><b>✅ Verified KPIs:</b></p>", unsafe_allow_html=True)
                        bullets = "".join([f"<li>{v}</li>" for v in verified])
                        st.markdown(f"<ul style='font-size:0.8em; margin-top:0; padding-left:1.2em;'>{bullets}</ul>", unsafe_allow_html=True)

                    if missing:
                        st.markdown("<p style='font-size:0.85em; margin-bottom:4px;'><b>❌ Missing Evidence:</b></p>", unsafe_allow_html=True)
                        missing_items = []
                        for kpi in details:
                            kpi_id = kpi["kpi_id"]
                            kpi_title = KPI_DESCRIPTIONS.get(kpi_id.split("_")[1], "Unknown KPI")
                            if kpi_id not in covered_kpis:
                                actions_str = ", ".join([f"{a['id']}" for a in kpi["expected_actions"]])
                                missing_items.append(f"<li>{kpi_title} <span style='color:#888;'>(needs: {actions_str})</span></li>")
                        st.markdown(f"<ul style='font-size:0.8em; margin-top:0; padding-left:1.2em;'>{''.join(missing_items)}</ul>", unsafe_allow_html=True)

                    if not missing:
                        st.success("All KPIs fully verified.", icon="🎯")
    
    # ─── Tab 2: Chunking Quality ─────────────────────────────────────────
    with tab2:
        st.markdown("### Chunking Quality Analysis")
        
        chunk_quality = eval_results.get("chunking_quality", {})
        
        if chunk_quality:
            for doc_type, stats in chunk_quality.items():
                st.markdown(f"#### {doc_type.replace('_', ' ').title()}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Chunks", stats.get("total_chunks", 0))
                with col2:
                    st.metric("Avg Length", f"{stats.get('avg_length', 0):.0f} chars")
                with col3:
                    st.metric("Min Length", f"{stats.get('min_length', 0)} chars")
                with col4:
                    st.metric("Max Length", f"{stats.get('max_length', 0)} chars")
                
                # Per-strategy breakdown
                per_strategy = stats.get("per_strategy", {})
                if per_strategy:
                    rows = []
                    for strategy, s_data in per_strategy.items():
                        rows.append({
                            "Strategy": strategy,
                            "Count": s_data.get("count", 0),
                            "Avg Length": f"{s_data.get('avg_length', 0):.0f} chars",
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No chunking quality data available.")
