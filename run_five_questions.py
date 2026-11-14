import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.api import answer_question

questions = [
    ("Q1", "Why is combustion different in microgravity?"),
    ("Q2", "What was the objective of BASS-II?"),
    ("Q3", "What did Saffire VI investigate?"),
    ("Q4", "How are smoke particles studied in microgravity?"),
    ("Q5", "What can microgravity combustion research teach us about spacecraft fire safety?")
]

for q_id, q in questions:
    res = answer_question(q, top_k=5)
    print(f"=== {q_id}: {q} ===")
    print("### Claim")
    print(res["claim"])
    print("\n### Source")
    print(", ".join(res["sources"]))
    print("\n### Evidence")
    for ev in res["evidence"][:3]:
        print(f"[{ev['chunk_id']}] (Page {ev['page']}): {ev['evidence_text']}")
    print("\n### Conditions")
    print(res["conditions"])
    print("\n### Uncertainty")
    print(res["limitations"])
    print("\n### Data Status")
    print(res["data_status"])
    print("="*70 + "\n")
