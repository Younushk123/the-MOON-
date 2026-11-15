"""Export the Source Register (with the 6-level status ladder) + a separate manual-verification list.
Nothing here marks a URL/DOI/claim as verified; those stay 'not checked' until a person does it."""
import csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import openpyxl
from src.config import Settings
from src.source_register import build_register

reg = build_register(Settings())
cols = ["source_id", "title", "publisher", "year", "source_type", "identifier_or_doi", "official_url",
        "1_official_source_identified", "2_url_verified", "3_document_downloaded", "4_document_indexed",
        "4b_catalogue_text_indexed_only", "5_raw_data_available", "6_claim_verified", "seed_status_text(not verification)",
        "research_topic", "origin", "manual_flags"]
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Source Register Updated"; ws.append(cols)
manual = []
for sid, e in reg.items():
    ws.append([sid, e.title, e.publisher, e.year, e.source_type, e.identifier, e.url or "",
               "yes (per register class)" if e.official_source_identified else "no/unclear", e.url_verified,
               "yes" if e.downloaded else "no", "yes (real file text)" if e.indexed_document else "no",
               "yes" if (e.catalogue_indexed and not e.indexed_document) else "", e.raw_data_available, e.claim_verified,
               e.seed_status, e.research_topic, e.origin, " | ".join(dict.fromkeys(e.manual_flags))])
    flags = [f for f in dict.fromkeys(e.manual_flags) if not f.startswith("URL/DOI not verified in this run")]
    if flags or e.url_verified == "not checked":
        manual.append([sid, e.title, e.url or "", "; ".join(flags) or "-", "verify URL/DOI/date on the official page"])
wb.save(ROOT / "Source_Register_Updated.xlsx")
with open(ROOT / "manual_verification_list.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["source_id", "title", "url_on_record", "issues_found", "action_needed"]); w.writerows(manual)
print(len(reg), "register entries;", len(manual), "need manual verification")
