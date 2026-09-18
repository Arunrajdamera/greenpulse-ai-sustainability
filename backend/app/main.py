from __future__ import annotations

import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "data" / "knowledge"
AREAS = ["Block A", "Block B", "Library", "Hostel"]
TYPES = [("Electricity", "kWh", 240), ("Water", "kL", 72), ("Paper", "sheets", 850), ("Waste", "kg", 42)]

def seed_records():
    records = []
    start = date.today() - timedelta(days=27)
    for i in range(28):
        for t_idx, (kind, unit, base) in enumerate(TYPES):
            for a_idx, area in enumerate(AREAS):
                variation = ((i * 7 + a_idx * 11 + t_idx * 5) % 19) - 9
                value = base + base * variation / 100 + a_idx * base * .04
                # Deliberate, labelled demo anomaly for evaluator walkthrough.
                if kind == "Electricity" and area == "Block A" and i >= 24:
                    value += 105
                if kind == "Water" and area == "Hostel" and i == 26:
                    value += 42
                records.append({"date": str(start + timedelta(days=i)), "location": area,
                    "resource_type": kind, "consumption": round(value, 1), "unit": unit,
                    "dataset": "Demo Dataset – Simulated Resource Data"})
    return records

RECORDS = seed_records()

def initialize_demo_database():
    """Persist the simulated seed for an inspectable, dependency-free SQLite demo store."""
    db_path = ROOT / "data" / "campus_demo.db"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE IF NOT EXISTS resource_records (date TEXT, location TEXT, resource_type TEXT, consumption REAL, unit TEXT, dataset TEXT)")
    if connection.execute("SELECT COUNT(*) FROM resource_records").fetchone()[0] == 0:
        connection.executemany("INSERT INTO resource_records VALUES (:date,:location,:resource_type,:consumption,:unit,:dataset)", RECORDS)
        connection.commit()
    connection.close()

initialize_demo_database()

def chunks():
    result = []
    for file in sorted(KNOWLEDGE.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        for part in re.split(r"\n\s*\n", text):
            clean = part.strip().replace("# ", "")
            if clean:
                result.append({"source": file.name, "text": clean})
    return result

TOPIC_KEYWORDS = {
    "energy.md": {
        "electricity", "energy", "power", "lighting", "light", "hvac", "air", "conditioning",
        "equipment", "classroom", "building", "buildings", "load", "loads", "baseload", "occupancy",
        "hours", "sdg 7", "clean energy",
    },
    "water.md": {"water", "water usage", "leak", "leaks", "plumbing", "wastage", "fixture", "fixtures"},
    "materials.md": {
        "paper", "printing", "print", "documents", "document", "duplex", "waste", "recycling",
        "recycle", "bins", "bin", "segregation", "sorting", "sdg 12", "responsible consumption",
        "waste reduction",
    },
}

def _normalise_query(query: str) -> tuple[set[str], set[str]]:
    """Return query terms and topic sources, making the lightweight retrieval explainable."""
    normalised = query.lower().replace("air-conditioning", "air conditioning")
    terms = set(re.findall(r"[a-z]{3,}", normalised))
    matched_sources = set()
    for source, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in normalised for keyword in keywords):
            matched_sources.add(source)
    return terms, matched_sources

def retrieve(query: str, limit: int = 3):
    query_words, topic_sources = _normalise_query(query)
    scored = []
    for item in chunks():
        # Once the query maps to a recognised domain, do not dilute grounded
        # context with chunks that only share generic words such as "campus".
        if topic_sources and item["source"] not in topic_sources:
            continue
        words = set(re.findall(r"[a-z]{3,}", item["text"].lower()))
        lexical_score = len(query_words & words)
        # A clear domain match outranks incidental shared words such as "campus".
        topic_boost = 100 if item["source"] in topic_sources else 0
        score = topic_boost + lexical_score
        if score:
            scored.append((score, item))
    return [x[1] for x in sorted(scored, key=lambda x: (x[0], x[1]["source"]), reverse=True)[:limit]]

def analyze(resource_type: str | None = None):
    records = [r for r in RECORDS if not resource_type or r["resource_type"].lower() == resource_type.lower()]
    groups = defaultdict(list)
    for r in records: groups[(r["resource_type"], r["location"])].append(r)
    findings = []
    for (kind, area), rows in groups.items():
        rows.sort(key=lambda x: x["date"])
        baseline = sum(x["consumption"] for x in rows[:-4]) / max(1, len(rows)-4)
        current = sum(x["consumption"] for x in rows[-4:]) / min(4, len(rows))
        change = (current - baseline) / baseline * 100 if baseline else 0
        if change >= 12 or max(x["consumption"] for x in rows) > baseline * 1.25:
            priority = "High" if change >= 25 else "Medium"
            findings.append({"id": f"{kind}-{area}".replace(" ", "-").lower(), "resource_type": kind,
             "location": area, "observed_value": round(current, 1), "baseline_value": round(baseline, 1),
             "unit": rows[0]["unit"], "difference_percent": round(change, 1), "priority": priority,
             "reason": f"Recent average is {abs(change):.1f}% above the earlier demo-data baseline.",
             "finding": f"{kind} usage in {area} is unusually high in the simulated dataset."})
    return sorted(findings, key=lambda x: (x["priority"] != "High", -x["difference_percent"]))

def recommendation_for(finding):
    actions = {"Electricity": "Review lighting, HVAC schedules, standby loads and equipment use; verify meter readings before changing operations.",
      "Water": "Inspect fixtures and plumbing for leaks, confirm readings, and ask occupants to report persistent wastage.",
      "Paper": "Review print defaults, enable duplex printing and promote digital-first submissions.",
      "Waste": "Check bin placement and sorting guidance, then identify avoidable waste streams with facilities staff."}
    source_query = finding["resource_type"] + " conservation"
    source = retrieve(source_query, 1)
    return {"finding": finding["finding"], "resource_category": finding["resource_type"], "recommendation": actions[finding["resource_type"]],
      "priority": finding["priority"], "reason": finding["reason"], "supporting_knowledge": source[0]["source"] if source else "No matching knowledge item", "status": "Suggested / Pending Review",
      "responsible_ai_note": "Demo-data decision support only. Verify locally with an appropriate human before implementation."}

app = FastAPI(title="Sustainable Campus Resource Assistant", version="1.0.0")
frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "https://greenpulse-ai-sustainability-1.onrender.com"
).rstrip("/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://greenpulse-ai-sustainability-1.onrender.com",
        "https://greenpulse-ai-sustainability.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel): resource_type: str | None = Field(default=None, max_length=30)
class ChatRequest(BaseModel): message: str = Field(min_length=3, max_length=500)
class RecommendationRequest(BaseModel): resource_type: str | None = Field(default=None, max_length=30)

@app.get("/health")
def health(): return {"status":"ok", "ai_mode":"Demo AI Mode", "provider": os.getenv("LLM_PROVIDER", "demo")}

@app.get("/api/resources")
def resources(resource_type: str | None = None):
    return {"dataset":"Demo Dataset – Simulated Resource Data", "items":[r for r in RECORDS if not resource_type or r["resource_type"].lower()==resource_type.lower()]}

@app.get("/api/resources/summary")
def summary():
    counts = Counter(r["resource_type"] for r in RECORDS)
    return {"dataset":"Demo Dataset – Simulated Resource Data", "total_records":len(RECORDS), "by_resource":counts, "high_consumption_alerts":len(analyze()), "recommendations_generated":len(analyze()), "sustainability_actions":4}

@app.get("/api/resources/trends")
def trends():
    daily = defaultdict(lambda: defaultdict(float))
    for r in RECORDS: daily[r["date"]][r["resource_type"]] += r["consumption"]
    return {"dataset":"Demo Dataset – Simulated Resource Data", "items":[{"date":d, **{k:round(v,1) for k,v in vals.items()}} for d,vals in sorted(daily.items())]}

@app.post("/api/analyze")
def analysis(payload: AnalysisRequest): return {"dataset":"Demo Dataset – Simulated Resource Data", "findings": analyze(payload.resource_type)}

@app.post("/api/recommendations")
def recommendations(payload: RecommendationRequest): return {"workflow":["Resource Analysis Agent","Knowledge Retrieval Agent","Recommendation Agent","Responsible AI Check"], "items":[recommendation_for(f) for f in analyze(payload.resource_type)]}

@app.post("/api/chat")
def chat(payload: ChatRequest):
    context = retrieve(payload.message)
    if not context:
        answer = "I could not find a close match in the local knowledge base. In this demo, please review campus-specific data with facilities staff before acting."
    else:
        answer = "Based on the local sustainability knowledge base: " + " ".join(x["text"] for x in context[:2]) + " This is a demo-mode, grounded response; confirm conditions locally."
    return {"mode":"Demo AI Mode", "answer":answer, "sources":[x["source"] for x in context], "responsible_ai_note":"Grounded in local knowledge where available; not a substitute for human review."}

@app.get("/api/knowledge")
def knowledge():
    category_names = {"energy.md": "Energy", "water.md": "Water", "materials.md": "Materials / Paper / Waste"}
    grouped = defaultdict(list)
    for item in chunks():
        grouped[item["source"]].append(item["text"])
    items = [{"source": source, "category": category_names.get(source, "Sustainability"),
              "description": " ".join(parts)[:260], "chunk_count": len(parts)}
             for source, parts in sorted(grouped.items())]
    return {"items": items, "document_count": len(items), "chunk_count": len(chunks())}

@app.get("/api/sdgs")
def sdgs(): return {"primary":{"number":"12","title":"Responsible Consumption and Production","description":"Supports resource awareness, waste reduction and data-informed decisions."},"secondary":[{"number":"7","title":"Affordable and Clean Energy","description":"Promotes energy efficiency."},{"number":"11","title":"Sustainable Cities and Communities","description":"Supports sustainable institutional environments."},{"number":"13","title":"Climate Action","description":"Encourages climate-conscious resource use."}]}

@app.get("/api/responsible-ai")
def responsible_ai(): return {"principles":["Transparency: demo mode and simulated data are labelled.","Explainability: alerts show observed values and baselines.","Privacy: no personal data is collected.","Grounding: chat returns local knowledge sources.","Human oversight: review recommendations before implementation.","Limitations: this prototype does not represent real campus consumption."]}




