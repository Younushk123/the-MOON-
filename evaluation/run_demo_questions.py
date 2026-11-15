"""Run the 5 integration demo questions. Saves raw output; correctness is NOT auto-judged: human_verified stays null
until a person checks each answer against the original source."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag_pipeline import NASARAG
from src.api_adapter import ask_research

QS = [("Why is combustion different in microgravity?", None),
      ("What was the objective of BASS-II?", ["PSI-25"]),
      ("What did Saffire VI investigate?", None),
      ("How are smoke particles studied in microgravity?", None),
      ("What can microgravity combustion research teach us about spacecraft fire safety?", None)]
mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
rag = NASARAG(mode=mode)
out = []
for q, eids in QS:
    r = ask_research(rag, q, eids)
    r["human_verified"] = None
    out.append(r)
Path(__file__).with_name("demo_questions_results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for r in out:
    print("\nQ:", r["question"]); print(" status:", r["evidence_status"], "| data_status:", r["data_status"], "| abstained:", r["abstained"])
    print(" retrieved:", [(x["register_id"], x["score"]) for x in r["retrieved"][:4]])
    print(" claim:", r["claim"][:330])
    print(" evidence src:", [(e["register_id"], e["content_type"]) for e in r["supporting_evidence"]])
    print(" validation:", r["validation"])
