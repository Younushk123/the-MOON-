import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.api import answer_question

res = answer_question("Why is combustion different in microgravity?", top_k=5)
print("=== Corrected Result for Test 1 ===")
print("### Claim")
print(res["claim"])
print("\n### Source")
print(", ".join(res["sources"]))
print("\n### Evidence")
for ev in res["evidence"]:
    print(f"[{ev['chunk_id']}] (Page {ev['page']}): {ev['evidence_text']}")
print("\n### Conditions")
print(res["conditions"])
print("\n### Uncertainty")
print(res["limitations"])
print("\n### Data Status")
print(res["data_status"])
