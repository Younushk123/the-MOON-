"""Honest evaluation of T1-T30 + extra tests A-E against the REAL pipeline.

PASS rules (nothing is pre-set to PASS):
  regular test      : expected source(s) in top-3 retrieved register IDs (all groups for comparison tests),
                      generator did not abstain, citations valid (chunk IDs retrieved, quotes verbatim).
  abstention test   : system abstained (or answered a clear 'No'), and the claim contains no invented numbers.
Answer *correctness* is NOT auto-judged: it is recorded as 'HUMAN REVIEW REQUIRED' for every non-abstention test.
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import openpyxl
from rag_pipeline import NASARAG
from src.api_adapter import ask_research

ABSTAIN_TESTS = {"T8", "T21", "T24", "T29", "T30", "TEST_B", "TEST_C", "TEST_D"}
REQUIRE_ALL = {"T23", "T27"}          # multi-source comparison tests: every expected group must be retrieved
EXTRA = [("TEST_A", "What does Friedman say about smoke particle agglomeration in microgravity?", "S5"),
         ("TEST_B", "What is the exact oxygen flammability percentage limit measured for BASS-II samples?", "S13"),
         ("TEST_C", "What were the results of the FLEX-3 experiment?", "none indexed"),
         ("TEST_D", "Does a NASA PSI catalogue entry prove that raw experimental files are downloadable?", "S36/S40"),
         ("TEST_E", "What is the purpose of the NASA-STD-6001B flammability test procedures?", "DOC-STD-6001B")]


EQUIVALENT_SOURCES = {
    "S4": {"S4", "S31", "S39"},       # ICES-2024-365 / NTRS 20240002981
    "S31": {"S4", "S31", "S39"},
    "S21": {"S21", "S56"},             # SAME PSI record & SAME Final Science Report
    "S22": {"S22", "S56"},             # SAME-R PSI record & SAME Final Science Report
    "S32": {"S3", "S32"},              # Both are NTRS 20170001636
    "S3": {"S3", "S32"},
}


def expected_groups(exp: str):
    groups = []
    for part in re.split(r"\s*/\s*", exp):
        ids = set()
        for m in re.finditer(r"S(\d+)(?:\s*-\s*S?(\d+))?", part):
            lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
            ids.update(f"S{i}" for i in range(lo, hi + 1))
        for m in re.finditer(r"DOC-[A-Z0-9-]+", part):
            ids.add(m.group(0))
        expanded = set(ids)
        for i in ids:
            if i in EQUIVALENT_SOURCES:
                expanded.update(EQUIVALENT_SOURCES[i])
        if expanded: groups.append(expanded)
    return groups


def evaluate(tid, out, exp):
    top = [h["register_id"] for h in out["retrieved"]]
    top3 = top[:3]
    groups = expected_groups(exp)
    if groups:
        hit_groups = [any(i in g for i in top3) for g in groups]
        hit = all(hit_groups) if tid in REQUIRE_ALL else any(hit_groups)
        rank = "TOP1" if top and any(top[0] in g for g in groups) else ("TOP3" if hit else "MISS")
        if tid in REQUIRE_ALL and hit: rank = "TOP3 (all groups)"
    else:
        hit, rank = False, "N/A (no expected source)"
    cites_ok = out["validation"]["ok"]
    neg = bool(re.match(r"\s*no\b", out["claim"], re.I))
    is_insufficient = out.get("data_status") in ("Insufficient Evidence", "Raw Data Not Indexed")
    res = dict(retrieval_relevance=rank, citation_correctness="VALID" if cites_ok else "INVALID: " + "; ".join(out["validation"]["problems"])[:200])
    if tid in ABSTAIN_TESTS:
        claim_clean = re.sub(r"\b(?:PSI-\d+|CC\d+-\d+(?:\.\d+)?)\b", "", out["claim"], flags=re.I)
        nums = re.findall(r"\d+(?:\.\d+)?", claim_clean.split("Query asks")[0].split("No indexed evidence")[0])
        ok = (out["abstained"] or neg or is_insufficient) and not nums
        res.update(abstention_correctness="CORRECT" if ok else "FAILED", answer_correctness="N/A (abstention test)",
                   final_status="PASS" if ok else "FAIL")
        res["observations"] = ("Abstained/negative, no invented numbers." if ok else "Did not abstain or produced numbers.")
        if rank == "MISS" and groups: res["observations"] += f" Note: expected source {exp} not in top-3."
    else:
        ok = hit and not out["abstained"] and cites_ok
        res.update(abstention_correctness="N/A", answer_correctness="HUMAN REVIEW REQUIRED (not auto-judged)",
                   final_status="PASS" if ok else "FAIL")
        why = []
        if not hit: why.append(f"expected {exp} not in top-3 {top3}")
        if out["abstained"]: why.append("system abstained although a regular answer was expected")
        if not cites_ok: why.append("citation validation failed")
        res["observations"] = ("Retrieval + citation criteria met; answer quality still needs human check." if ok else "; ".join(why))
    return res


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    rag = NASARAG(mode=mode)
    wb = openpyxl.load_workbook(ROOT / "Investigation_Retrieval_Tests_Clean.xlsx")
    ws = wb["Retrieval Tests"]
    hdr = [c.value for c in ws[1]]
    tests = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        r = dict(zip(hdr, row))
        if r.get("test_id"): tests.append((r["test_id"], r["query"], r["expected_source"] or ""))
    tests += EXTRA
    results = []
    for tid, q, exp in tests:
        out = ask_research(rag, q, None, None, top_k=5)
        ev = evaluate(tid, out, exp)
        results.append({"test_id": tid, "query": q, "expected_source": exp,
                        "actual_retrieved_sources": [h["register_id"] for h in out["retrieved"]],
                        "top_scores": [(h["register_id"], h["score"]) for h in out["retrieved"][:3]],
                        "retrieved_evidence": out["supporting_evidence"], "generated_answer": out["claim"],
                        "data_status": out["data_status"], "evidence_status": out["evidence_status"], **ev,
                        "retrieval_mode": out["retrieval_mode"], "generation_mode": out["generation_mode"]})
    (ROOT / "retrieval_test_results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    # Excel report: original sheets untouched except execution columns; new sheet with the full run
    col = {h: i + 1 for i, h in enumerate(hdr)}
    by = {r["test_id"]: r for r in results}
    for row in range(2, ws.max_row + 1):
        tid = ws.cell(row, 1).value
        if tid in by:
            r = by[tid]
            ws.cell(row, col["top1"], r["actual_retrieved_sources"][0] if r["actual_retrieved_sources"] else "")
            ws.cell(row, col["top3_scores"], ", ".join(f"{s}({v})" for s, v in r["top_scores"]))
            ws.cell(row, col["execution_status"], f"Run 2026-11-14 | {r['generation_mode']} | {r['retrieval_mode'][:40]}")
            ws.cell(row, col["evaluation_notes"], r["observations"])
    ws2 = wb.create_sheet("Executed Run 2026-11-14")
    cols = ["test_id", "query", "expected_source", "actual_retrieved_sources", "top_scores", "retrieval_relevance", "citation_correctness",
            "answer_correctness", "abstention_correctness", "final_status", "observations", "generated_answer", "data_status", "retrieval_mode", "generation_mode"]
    ws2.append(cols)
    for r in results: ws2.append([json.dumps(r[c]) if isinstance(r[c], (list, dict)) else r[c] for c in cols])
    wb.save(ROOT / "Investigation_Retrieval_Tests_Executed.xlsx")
    n = len(results); p = sum(r["final_status"] == "PASS" for r in results)
    print(f"{p}/{n} PASS under strict criteria | mode: {results[0]['retrieval_mode']} | {results[0]['generation_mode']}")
    for r in results:
        print(f"{r['test_id']:7}{r['final_status']:5} {r['retrieval_relevance']:18} exp={r['expected_source'][:22]:22} got={r['actual_retrieved_sources'][:3]}  {r['observations'][:70] if r['final_status']=='FAIL' else ''}")


if __name__ == "__main__":
    main()
