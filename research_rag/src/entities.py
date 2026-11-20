"""Investigation entity matching (replaces the old raw '+8.0 substring' boost).
Rules are matched longest/most-specific first and the matched span is masked, so 'BASS-II' does not
also trigger the generic 'BASS' rule. Matching is exact on register IDs (the old code used substring
matching, so tag 's2' also hit 's20'/'s21')."""
import re
from typing import Dict, List, Set, Tuple

# (label, regex, flags, register ids) - ORDER = specificity
RULES: List[Tuple[str, str, int, List[str]]] = [
    ("bass-ii", r"\bBASS[- ]?II\b", re.I, ["S13", "S29"]),
    ("bass", r"\bBASS\b", re.I, ["S12"]),
    ("saffire-vi", r"\bsaffire[- ]?(vi|6)\b", re.I, ["S31", "S4"]),
    ("saffire-iii", r"\bsaffire[- ]?(iii|3)\b", re.I, ["S20"]),
    ("saffire-ii", r"\bsaffire[- ]?(ii|2)\b", re.I, ["S19"]),
    ("saffire-i", r"\bsaffire[- ]?(i|1)\b", re.I, ["S18"]),
    ("saffire", r"\bsaffire\b", re.I, ["S3", "S7", "S18", "S19", "S20", "S31", "S4"]),
    ("same-r", r"\bSAME[- ]R\b", re.I, ["S22"]),
    ("same", r"\bSAME\b", 0, ["S21", "S22"]),          # case-sensitive: the English word 'same' must not match
    ("daft", r"\bDAFT(-2)?\b", re.I, ["S15"]),
    ("flex-2", r"\bFLEX[- ]?2\b", re.I, ["S17"]),
    ("flex", r"\bFLEX\b", re.I, ["S16", "S17"]),
    ("cfi-g", r"\bCFI[- ]G\b", re.I, ["S25"]),
    ("cfi", r"\bCFI\b|\bcool flames?\b", re.I, ["S14"]),
    ("e-field", r"\be-?field\b|\belectric field", re.I, ["S10"]),
    ("s-flame", r"\bs-flame\b", re.I, ["S11"]),
    ("cld", r"\bCLD\b", 0, ["S9"]),
    ("slice", r"\bSLICE\b", 0, ["S23"]),
    ("spice", r"\bSPICE\b", re.I, ["S24"]),
    ("sofie-gel", r"\bsofie[- ]gel\b|\bGEL\b", 0, ["S48"]),
    ("sofie-mist", r"\bsofie[- ]mist\b|\bMIST\b", 0, ["S49"]),
    ("sofie", r"\bsofie\b", re.I, ["S47", "S48", "S49"]),
    ("bre", r"\bBRE\b", 0, ["S8", "S38"]),
    ("acme", r"\bACME\b", re.I, ["S38", "S8", "S9", "S10", "S11", "S34", "S25"]),
    ("flame design", r"\bflame design\b", re.I, ["S34"]),
    ("psi-repo", r"\bdownload\w*\s+(the\s+)?raw\b|\braw (combustion |experiment )*data\b|\bPSI (catalogue|catalog|listing)\b", re.I, ["S1", "S40", "S36"]),
    ("std-6001", r"\bNASA-STD-6001\b|\bTest 1\b", re.I, ["DOC-STD-6001B"]),
]
_PSI = re.compile(r"\bPSI-(\d+)\b", re.I)
_SID = re.compile(r"\bS(\d{1,2})\b")


def match_entities(query: str, register: Dict[str, object]) -> Tuple[Set[str], List[str]]:
    work, ids, labels = query, set(), []
    for label, pat, flags, rids in RULES:
        m = re.search(pat, work, flags)
        if m:
            labels.append(label)
            ids.update(rids)
            work = work[:m.start()] + " " * (m.end() - m.start()) + work[m.end():]
    for m in _PSI.finditer(query):           # generic PSI-NN -> register entries whose identifier contains it
        tag = f"PSI-{m.group(1)}".lower()
        for sid, e in register.items():
            if re.search(rf"\b{re.escape(tag)}\b", str(e.identifier).lower()):
                ids.add(sid); labels.append(tag)
    for m in _SID.finditer(query):
        sid = f"S{m.group(1)}"
        if sid in register:
            ids.add(sid); labels.append(sid)
    return ids, labels
