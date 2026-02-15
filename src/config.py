"""
ISPS Configuration Module
Centralizes all configuration: API keys, model settings, file paths, and constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"
ONTOLOGY_DIR = BASE_DIR / "ontology_output"

STRATEGIC_PLAN_PATH = DOCUMENTS_DIR / "strategic_plan.docx"
ACTION_PLAN_PATH = DOCUMENTS_DIR / "action_plan.docx"

# ─── OpenAI ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Models
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# LLM Parameters
LLM_TEMPERATURE = 0.1        # Low temperature for consistent analysis
LLM_MAX_TOKENS = 2000

# ─── Chunking ────────────────────────────────────────────────────────────────
# Fixed/Recursive chunking
CHUNK_SIZE = 800              # characters
CHUNK_OVERLAP = 150           # characters
SEPARATORS = [
    "\n================",      # Major section breaks
    "\n---",                   # Sub-section breaks
    "\n\n",                    # Paragraph breaks
    "\n",                      # Line breaks
    " ",                       # Word breaks
]

# Semantic chunking
SEMANTIC_BREAKPOINT_PERCENTILE = 85

# ─── Vector Store ────────────────────────────────────────────────────────────
CHROMA_COLLECTION_STRATEGIC = "strategic_plan"
CHROMA_COLLECTION_ACTION = "action_plan"
CHROMA_COLLECTION_COMBINED = "combined"

# Retrieval
RETRIEVAL_TOP_K = 10          # Initial retrieval count
RERANK_TOP_K = 5              # After reranking

# ─── Strategic Objectives ────────────────────────────────────────────────────
STRATEGIC_OBJECTIVES = {
    "SO1": "Digital Learning Transformation",
    "SO2": "Research Excellence and Innovation",
    "SO3": "Student Experience and Wellbeing",
    "SO4": "Industry Partnerships and Employability",
    "SO5": "Operational Efficiency and Sustainability",
}

# KPI IDs per strategic objective
OBJECTIVE_KPIS = {
    "SO1": ["D1", "D2", "D3", "D4", "D5", "D6"],
    "SO2": ["R1", "R2", "R3", "R4", "R5", "R6"],
    "SO3": ["S1", "S2", "S3", "S4", "S5", "S6"],
    "SO4": ["I1", "I2", "I3", "I4", "I5", "I6"],
    "SO5": ["O1", "O2", "O3", "O4", "O5", "O6"],
}

# KPI Descriptions map
KPI_DESCRIPTIONS = {
    "D1": "% of modules with tech-enhanced learning",
    "D2": "Student satisfaction with digital learning",
    "D3": "Staff completing digital skills training",
    "D4": "Number of fully online programmes",
    "D5": "LMS daily active users",
    "D6": "WCAG 2.1 AA compliance rate for materials",
    "R1": "Annual research funding secured (£M)",
    "R2": "REF outputs rated 3* or 4*",
    "R3": "Number of active research partnerships",
    "R4": "PhD completions per year",
    "R5": "Spin-out ventures created",
    "R6": "Research publications in top quartile",
    "S1": "Overall NSS satisfaction score",
    "S2": "Counselling service average wait time (days)",
    "S3": "Student retention rate (Year 1 to Year 2)",
    "S4": "Students participating in extracurricular",
    "S5": "Graduate employability (within 15 months)",
    "S6": "Personal tutor meeting completion rate",
    "I1": "Graduate employment rate (15 months)",
    "I2": "Students completing work placements",
    "I3": "Active industry partnerships",
    "I4": "Employer satisfaction with graduates",
    "I5": "Student start-ups launched",
    "I6": "KTPs and collaborative projects",
    "O1": "Carbon emissions reduction (from 2020 base)",
    "O2": "Administrative process automation rate",
    "O3": "International student proportion",
    "O4": "Annual income from exec education (£M)",
    "O5": "Staff satisfaction with admin processes",
    "O6": "Energy consumption reduction per m²",
}

# ─── Ontology ────────────────────────────────────────────────────────────────
ONTOLOGY_NAMESPACE = "http://isps.greenfield.ac.uk/ontology#"
ONTOLOGY_PREFIX = "isps"

# ─── Dashboard ───────────────────────────────────────────────────────────────
DASHBOARD_TITLE = "ISPS — Intelligent Strategic Plan Synchronization System"
DASHBOARD_ICON = "🎯"
DASHBOARD_THEME = "light"
