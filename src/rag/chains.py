"""
LangChain Chains for ISPS
Provides chains for sync assessment, improvement suggestions, and summarization.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE


# ─── Sync Assessment Chain ───────────────────────────────────────────────────

SYNC_ASSESSMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert strategic alignment analyst for GreenField University.

Given a Strategic Objective and retrieved Action Plan chunks, assess the alignment.

Evaluate:
1. **Coverage**: Are all KPIs addressed by actions?
2. **Depth**: Are the actions detailed enough to achieve the KPI targets?
3. **Timeline Alignment**: Do action deadlines support milestone dates?
4. **Resource Adequacy**: Are sufficient resources/owners assigned?

Provide your response in this EXACT format:
ALIGNMENT_SCORE: [0.0-1.0]
ALIGNMENT_LEVEL: [Full|Partial|Weak|Missing]
COVERED_KPIS: [comma-separated list of KPI IDs that have supporting actions]
UNCOVERED_KPIS: [comma-separated list of KPI IDs without adequate action support]
JUSTIFICATION: [2-3 sentences explaining the score]
CONFIDENCE: [0.0-1.0]"""),
    ("human", """Strategic Objective: {objective_id} - {objective_name}
    
Strategic Objective Details:
{objective_details}

Retrieved Action Plan Chunks:
{action_chunks}

Ontology Mapping:
{ontology_mapping}

Assess the alignment:""")
])


IMPROVEMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a strategic planning advisor for GreenField University.

Given alignment gaps (KPIs without supporting actions or weak coverage),
suggest SPECIFIC, ACTIONABLE improvements.

For each gap, provide:
1. A new action item (with estimated timeline and owner)
2. Why this action would improve alignment
3. Expected impact (High/Medium/Low)
4. Feasibility assessment

Be practical and specific - reference actual departments and realistic timelines."""),
    ("human", """Objective: {objective_id} - {objective_name}

Identified Gaps:
{gaps}

Current Actions:
{current_actions}

Suggest improvements:""")
])


SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an executive report writer for GreenField University.

Given the synchronization analysis results for all strategic objectives,
write a concise executive summary suitable for a dashboard display.

Include:
1. Overall alignment status (one paragraph)
2. Key strengths (3-4 bullet points)
3. Critical gaps requiring attention (3-4 bullet points)  
4. Top 3 priority recommendations

Keep the summary under 300 words. Use clear, actionable language."""),
    ("human", """Synchronization Results:
{sync_results}

Write the executive summary:""")
])


GUIDANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a strategic advisor generating guidance messages for university decision-makers.

Given alignment results for a strategic objective, generate 1-3 SHORT guidance messages.
Each message should be:
- Actionable and specific
- Under 20 words
- Prefixed with an appropriate emoji (✅ for on-track, ⚠️ for warning, 🔴 for critical, 📋 for recommendation)

Format: One message per line."""),
    ("human", """Objective: {objective_id} - {objective_name}
Alignment Score: {alignment_score}
Alignment Level: {alignment_level}
Gaps: {gaps}

Generate guidance messages:""")
])


def get_llm(temperature: float = None) -> ChatOpenAI:
    """Get an LLM instance."""
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=temperature or LLM_TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
    )


def assess_sync(
    objective_id: str,
    objective_name: str,
    objective_details: str,
    action_chunks: str,
    ontology_mapping: str,
) -> dict:
    """Run the sync assessment chain."""
    llm = get_llm(temperature=0.1)
    chain = SYNC_ASSESSMENT_PROMPT | llm
    
    response = chain.invoke({
        "objective_id": objective_id,
        "objective_name": objective_name,
        "objective_details": objective_details,
        "action_chunks": action_chunks,
        "ontology_mapping": ontology_mapping,
    })
    
    return _parse_sync_response(response.content)


def suggest_improvements(
    objective_id: str,
    objective_name: str,
    gaps: str,
    current_actions: str,
) -> str:
    """Run the improvement suggestion chain."""
    llm = get_llm(temperature=0.5)
    chain = IMPROVEMENT_PROMPT | llm
    
    response = chain.invoke({
        "objective_id": objective_id,
        "objective_name": objective_name,
        "gaps": gaps,
        "current_actions": current_actions,
    })
    
    return response.content


def generate_executive_summary(sync_results: str) -> str:
    """Generate executive summary from all sync results."""
    llm = get_llm(temperature=0.3)
    chain = SUMMARY_PROMPT | llm
    response = chain.invoke({"sync_results": sync_results})
    return response.content


def generate_guidance_messages(
    objective_id: str,
    objective_name: str,
    alignment_score: float,
    alignment_level: str,
    gaps: str,
) -> list[str]:
    """Generate guidance messages for decision-makers."""
    llm = get_llm(temperature=0.3)
    chain = GUIDANCE_PROMPT | llm
    
    response = chain.invoke({
        "objective_id": objective_id,
        "objective_name": objective_name,
        "alignment_score": alignment_score,
        "alignment_level": alignment_level,
        "gaps": gaps,
    })
    
    messages = [line.strip() for line in response.content.strip().split("\n") if line.strip()]
    return messages


def _parse_sync_response(response_text: str) -> dict:
    """Parse the structured sync assessment response."""
    result = {
        "alignment_score": 0.5,
        "alignment_level": "Partial",
        "covered_kpis": [],
        "uncovered_kpis": [],
        "justification": "",
        "confidence": 0.5,
        "raw_response": response_text,
    }
    
    for line in response_text.strip().split("\n"):
        line = line.strip()
        if line.startswith("ALIGNMENT_SCORE:"):
            try:
                result["alignment_score"] = float(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        elif line.startswith("ALIGNMENT_LEVEL:"):
            result["alignment_level"] = line.split(":")[1].strip()
        elif line.startswith("COVERED_KPIS:"):
            kpis = line.split(":")[1].strip()
            result["covered_kpis"] = [k.strip() for k in kpis.split(",") if k.strip()]
        elif line.startswith("UNCOVERED_KPIS:"):
            kpis = line.split(":")[1].strip()
            result["uncovered_kpis"] = [k.strip() for k in kpis.split(",") if k.strip()]
        elif line.startswith("JUSTIFICATION:"):
            result["justification"] = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = float(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
    
    
    return result


# ─── Guardrails ──────────────────────────────────────────────────────────────

GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a strict guardrail for the GreenField University ISPS system.
    
    Your job is to classify whether a user query is RELEVANT to the following topics:
    - GreenField University's Strategic Plan or Action Plan
    - Strategic Objectives (SO1-SO5), KPIs, actions, deadlines
    - Alignment scores, gaps, or improvements
    - The ISPS system capabilities
    - General greetings (hello, hi, thanks)
    
    Queries about general knowledge (e.g. "Where is Colombo?", "Who is the president?"), coding, math, weather, or other universities are IRRELEVANT.
    
    Response format: JUST "YES" or "NO"."""),
    ("human", "{query}")
])


def check_relevance(query: str) -> bool:
    """Check if the query is relevant to the domain."""
    llm = get_llm(temperature=0.0)
    chain = GUARDRAIL_PROMPT | llm
    try:
        response = chain.invoke({"query": query})
        return response.content.strip().upper().startswith("YES")
    except Exception:
        # Fail safe: allow query if check fails
        return True
