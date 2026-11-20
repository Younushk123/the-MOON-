"""Pre-generation sufficiency gates + post-generation validation. Generic rules - no per-question answers."""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from .retrieval import tokenize, STOP

# ---- intent detectors (generic) -------------------------------------------------------------
_THRESH = re.compile(r"\b(exact|precise|specific|single|measured?)\b.*\b(threshold|limit|percentage|concentration|value)\b"
                     r"|\b(threshold|limit)\b.*\b(exact|precise|measured?)\b", re.I)
_PROOF = re.compile(r"\b(catalog(ue)?|listing|landing page|investigation (page|record|entry)|psi (entry|record))\b.*"
                    r"\b(prove|proof|establish|guarantee|alone)\b|\b(prove|proof)\b.*\b(raw|files?|data)\b.*\b(download|available|indexed)",
                    re.I)
_NAMED = re.compile(r"\b[A-Za-z][A-Za-z0-9]*[- ](?:[IVX]{1,4}|\d{1,3})\b")
_PRONOUN_MODALS = {"can", "may", "shall", "could", "would", "should", "do", "did", "if", "when",
                   "how", "what", "where", "why", "which", "as", "that", "whether", "and", "or"}


def asks_exact_measurement(q: str) -> bool:
    return bool(_THRESH.search(q))


def asks_catalogue_proof(q: str) -> bool:
    return bool(_PROOF.search(q))


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[-_]", " ", t.lower())).strip()


@dataclass
class Sufficiency:
    ok: bool
    reason: str = ""
    kind: str = ""           # missing_entity | low_coverage | measurement_not_indexed | ''


def check_sufficiency(query: str, hits, min_coverage: float) -> Sufficiency:
    texts = [_norm(f"{h.chunk.title} {h.chunk.content} {h.chunk.register_id}") for h in hits]
    # 1. named identifiers in the query (e.g. 'Saffire-IV', 'PSI-77') must appear in retrieved evidence
    for m in _NAMED.finditer(query):
        tok = _norm(m.group(0))
        parts = tok.split()
        if tok.startswith(("test ", "top ", "t ")) or (len(parts) == 2 and parts[0] in _PRONOUN_MODALS and parts[1] == "i"):
            continue
        if not any(re.search(rf"\b{re.escape(tok)}\b", t) for t in texts):
            return Sufficiency(False, f"No indexed evidence mentions '{m.group(0)}'.", "missing_entity")
    # 2. exact measured values need a measurement table, not catalogue/summary text
    if asks_exact_measurement(query) and not any(h.chunk.content_type == "measurement_table" for h in hits):
        return Sufficiency(False, "Query asks for an exact measured value, but no indexed measurement table/"
                           "raw data file is available (only catalogue records, summaries or documents).",
                           "measurement_not_indexed")
    # 3. distinctive query terms must be covered by the retrieved evidence
    q_terms = {t for t in tokenize(_norm(query)) if t not in STOP and len(t) > 2}
    if q_terms:
        blob = " ".join(texts)
        cov = sum(1 for t in q_terms if t in blob) / len(q_terms)
        if cov < min_coverage:
            return Sufficiency(False, f"Only {cov:.0%} of distinctive query terms appear in retrieved evidence.", "low_coverage")
    return Sufficiency(True)


# ---- post-generation validation ---------------------------------------------------------------
_NUM = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class ValidationReport:
    ok: bool
    problems: List[str] = field(default_factory=list)


def parse_evidence_lines(evidence: str):
    out = []
    for ln in [l.strip() for l in evidence.splitlines() if l.strip()]:
        m = re.match(r"^\[([^\]]+)\]\s+(.+)$", ln)
        out.append((m.group(1), m.group(2)) if m else (None, ln))
    return out


def validate_answer(
    answer,
    cited_chunk_ids: List[str],
    hits,
    abstained: bool,
    query: str,
    require_verbatim_claim: bool = False,
) -> ValidationReport:
    problems = []
    by_id = {h.chunk.chunk_id: h.chunk for h in hits}
    claim_quotes = []
    for cid in cited_chunk_ids:
        if cid not in by_id:
            problems.append(f"cited chunk '{cid}' was not retrieved (invented citation)")
    if abstained:
        nums = _NUM.findall(answer.claim)
        if nums and asks_exact_measurement(query):
            problems.append(f"abstention claim contains numbers {nums} for an exact-measurement query")
        return ValidationReport(not problems, problems)
    ev_numbers = set()
    for cid, quote in parse_evidence_lines(answer.evidence):
        if cid is None or cid not in by_id:
            problems.append(f"evidence line without a valid retrieved [chunk_id]: {quote[:60]!r}")
            continue
        if _norm(quote.strip('"')) not in _norm(by_id[cid].content):
            problems.append(f"evidence quote is not verbatim in {cid}: {quote[:60]!r}")
        elif cid in cited_chunk_ids:
            claim_quotes.append(quote)
        ev_numbers.update(_NUM.findall(quote))
    if require_verbatim_claim:
        expected_claims = {_norm(" ".join(claim_quotes))}
        if asks_catalogue_proof(query):
            expected_claims.add(_norm("No. " + " ".join(claim_quotes)))
        if _norm(answer.claim) not in expected_claims:
            problems.append("claim is not copied verbatim from the cited evidence")
    pool = " ".join(c.content for c in by_id.values())
    pool_nums = set(_NUM.findall(pool))
    for n in _NUM.findall(answer.claim):
        if n not in ev_numbers and n not in pool_nums:
            problems.append(f"number '{n}' in claim appears in no retrieved evidence (possible invented value)")
    if not cited_chunk_ids:
        problems.append("no cited chunks for a non-abstaining answer")
    return ValidationReport(not problems, problems)
