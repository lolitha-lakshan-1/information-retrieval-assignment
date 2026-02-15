"""
Chat Interface Page
Free-form chat with the ISPS system, with live reasoning sidebar.
"""
import streamlit as st
from src.config import OPENAI_API_KEY, LLM_MODEL, STRATEGIC_OBJECTIVES


def show():
    st.markdown("# 💬 Chat with ISPS")
    
    results = st.session_state.get("analysis_results")
    
    if not results:
        st.info("Run the analysis pipeline first to enable the chat interface.")
        return
    
    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm the ISPS assistant. Ask me anything about the strategic plan synchronization. For example:\n\n- *What's the alignment score for SO5?*\n- *Which KPIs are missing actions?*\n- *What improvements do you suggest for Digital Learning?*"}
        ]
    
    # ─── Layout ──────────────────────────────────────────────────────────
    chat_col, reasoning_col = st.columns([3, 2])
    
    with chat_col:
        # Display chat history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about strategic plan alignment..."):
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response, trace = _generate_response(prompt, results)
                    st.markdown(response)
                    
                    # Store trace
                    st.session_state.chat_reasoning_trace = trace
            
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    with reasoning_col:
        st.markdown("### 🤖 Agent Reasoning")
        
        trace = st.session_state.get("chat_reasoning_trace", [])
        
        if trace:
            for step in trace:
                step_type = step.get("step_type", "")
                content = step.get("content", "")
                
                emoji = {"thought": "💭", "action": "🔧", "observation": "👁️", "final_answer": "📊"}.get(step_type, "•")
                css_class = {
                    "thought": "thought-step",
                    "action": "action-step",
                    "observation": "observation-step",
                    "final_answer": "final-step",
                }.get(step_type, "")
                
                st.markdown(f'<div class="{css_class}"><strong>{emoji}</strong> {content[:200]}</div>', unsafe_allow_html=True)
        else:
            pass


def _generate_response(query: str, results: dict) -> tuple[str, list]:
    """Generate a response using RAG retrieval + analysis results as context."""
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    import json
    
    trace = []
    trace.append({"step_type": "thought", "content": f"User asked: '{query}'", "step_number": 1})
    
    # ─── Step 0: Guardrail Check ──────────────────────────────────────────
    try:
        from src.rag.chains import check_relevance
        is_relevant = check_relevance(query)
        
        if not is_relevant:
            trace.append({"step_type": "thought", "content": "Guardrail Check: Query is IRRELEVANT to the domain.", "step_number": 2})
            trace.append({"step_type": "final_answer", "content": "Refused out-of-domain query.", "step_number": 3})
            return (
                "I'm designed specifically to assist with GreenField University's Strategic Plan and Action Plan analysis. I can help you with alignment scores, KPI tracking, action progress, gap analysis, and improvement recommendations. Could you ask me something about those topics?",
                trace
            )
        else:
            trace.append({"step_type": "thought", "content": "Guardrail Check: Query is RELEVANT.", "step_number": 2})
            
    except Exception as e:
        # Fail open if guardrail fails
        trace.append({"step_type": "thought", "content": f"Guardrail check failed: {str(e)}. Proceeding.", "step_number": 2})

    # ─── Step 1: RAG retrieval from ChromaDB ──────────────────────────────
    retrieved_chunks = []
    try:
        from src.rag.retriever import retrieve_chunks
        trace.append({"step_type": "action", "content": "Searching vector database for relevant document chunks (strategic plan + action plan)", "step_number": 2})
        
        retrieved_chunks = retrieve_chunks(
            query=query,
            collection_name="combined",
            top_k=8,
            use_hyde=True,
            use_multi_query=True,
        )
        
        chunk_summary = f"Retrieved {len(retrieved_chunks)} relevant chunks"
        if retrieved_chunks:
            strategies = set()
            for c in retrieved_chunks:
                s = c.get("metadata", {}).get("chunk_strategy", "unknown")
                strategies.add(s)
            chunk_summary += f" (strategies: {', '.join(strategies)})"
        
        trace.append({"step_type": "observation", "content": chunk_summary, "step_number": 3})
    except Exception as e:
        trace.append({"step_type": "observation", "content": f"RAG retrieval failed: {str(e)[:100]}. Using analysis results only.", "step_number": 3})
    
    # ─── Step 2: Build context ────────────────────────────────────────────
    context_parts = []
    
    # Add retrieved document chunks (primary source for factual questions)
    if retrieved_chunks:
        context_parts.append("=== RELEVANT DOCUMENT EXCERPTS ===")
        context_parts.append("(Use these for factual questions about deadlines, actions, KPIs, owners, progress)")
        for i, chunk in enumerate(retrieved_chunks, 1):
            meta = chunk.get("metadata", {})
            doc = meta.get("doc_type", "unknown")
            obj = meta.get("objective_id", "")
            strategy = meta.get("chunk_strategy", "")
            context_parts.append(f"\n[Chunk {i} | {doc} | {obj} | {strategy}]")
            context_parts.append(chunk["text"])
    
    # Add analysis results (for assessment/alignment questions)
    context_parts.append("\n=== ANALYSIS RESULTS ===")
    context_parts.append("(Use these for alignment scores, levels, and improvement suggestions)")
    context_parts.append(f"Overall Sync Score: {results.get('overall_score', 0):.0%}")
    context_parts.append(f"Overall Level: {results.get('overall_level', 'Unknown')}")
    
    for obj_id, obj_data in results.get("objectives", {}).items():
        score = obj_data.get("combined_score", 0)
        level = obj_data.get("sync_assessment", {}).get("alignment_level", "Unknown")
        justification = obj_data.get("sync_assessment", {}).get("justification", "")
        context_parts.append(f"\n{obj_id} ({STRATEGIC_OBJECTIVES.get(obj_id, '')}): {score:.0%} - {level}")
        if justification:
            context_parts.append(f"  Justification: {justification}")
        
        improvements = obj_data.get("improvements")
        if improvements and improvements.get("suggestions"):
            context_parts.append(f"  Improvements: {improvements['suggestions'][:300]}...")
    
    context = "\n".join(context_parts)
    
    # ─── Step 3: Generate LLM response ────────────────────────────────────
    trace.append({"step_type": "action", "content": "Generating response with RAG context + analysis results", "step_number": 4})
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the ISPS (Intelligent Strategic Plan Synchronization) chat assistant for GreenField University.

**DOMAIN RESTRICTION — STRICTLY ENFORCED:**
You MUST ONLY answer questions related to:
- GreenField University's Strategic Plan and Action Plan
- Strategic Objectives (SO1–SO5), KPIs, actions, milestones, deadlines, owners
- Synchronization analysis, alignment scores, gaps, and improvement suggestions
- The ISPS system itself (what it does, how it works)

You MAY also respond to:
- Basic greetings (hello, hi, thank you, goodbye, etc.) — respond warmly and remind the user what you can help with.

For ANY question outside this domain (e.g. weather, general knowledge, coding, math, news, personal advice, or anything unrelated to the strategic/action plans):
→ Politely decline: "I'm designed specifically to assist with GreenField University's Strategic Plan and Action Plan analysis. I can help you with alignment scores, KPI tracking, action progress, gap analysis, and improvement recommendations. Could you ask me something about those topics?"
→ Do NOT attempt to answer the off-topic question, even partially.

You have access to two types of information:
1. **Document excerpts** from the Strategic Plan and Action Plan — use these for factual questions about specific deadlines, action items, KPIs, owners, progress status, and dates.
2. **Analysis results** — use these for questions about alignment scores, sync levels, gaps, and improvement suggestions.

Guidelines:
- For questions about deadlines, actions, KPIs, or specific data: cite the exact information from document excerpts.
- For questions about alignment or scores: use the analysis results.
- Present data in clean tables when showing multiple items.
- Be specific — cite action IDs (e.g. A1.3), dates, owners, and percentages.
- If information is not available in the context, say so clearly.

Context:
{context}"""),
        ("human", "{query}")
    ])
    
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.3,
        openai_api_key=OPENAI_API_KEY,
        request_timeout=30,
    )
    
    chain = prompt | llm
    response = chain.invoke({"context": context, "query": query})
    
    trace.append({"step_type": "final_answer", "content": response.content[:200], "step_number": 5})
    
    return response.content, trace

