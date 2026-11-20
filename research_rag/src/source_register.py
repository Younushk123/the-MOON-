"""Source Register + corpus assembly.

Preserves every legacy source ID from legacy_seed.py and extends it with the 6-level status ladder:
  1 official_source_identified   2 url_verified   3 downloaded
  4 indexed_document             5 raw_data_available   6 claim_verified
Only (1) can be True from existing data. Everything else is False/'not checked' until a human or the
ingestion pipeline proves it. Seed 'status' text is kept as seed_status and is NOT treated as verification.
"""
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ingestion import DocumentChunk, load_ingested_chunks, load_manifest
from .legacy_seed import SOURCE_REGISTER as SEED_REGISTER, CHUNKS as SEED_CHUNKS


@dataclass
class RegisterEntry:
    source_id: str
    title: str
    publisher: str
    source_type: str
    identifier: str
    year: str
    source_class: str
    seed_status: str
    notes: str
    key_passage: str
    url: Optional[str] = None
    origin: str = "legacy_seed"           # legacy_seed | workbook_added
    research_topic: str = ""
    workbook_note: str = ""
    official_source_identified: bool = False
    url_verified: str = "not checked"
    downloaded: bool = False
    indexed_document: bool = False        # real extracted file chunks exist
    catalogue_indexed: bool = False       # only register/catalogue text indexed
    raw_data_available: str = "not verified"
    claim_verified: str = "no"
    manual_flags: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def _read_workbook_map(path: Path) -> List[Dict[str, Any]]:
    if not Path(path).exists():
        return []
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True)["Investigation Map"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:] if r and r[2]]


def build_register(settings) -> Dict[str, RegisterEntry]:
    wb = {r["register_id"]: r for r in _read_workbook_map(settings.workbook_path)}
    reg: Dict[str, RegisterEntry] = {}
    for sid, s in SEED_REGISTER.items():
        e = RegisterEntry(source_id=sid, title=s.title, publisher=s.publisher, source_type=s.source_type,
                          identifier=s.identifier, year=s.year, source_class=s.source_class,
                          seed_status=s.status, notes=s.notes, key_passage=s.key_passage)
        reg[sid] = e
    for sid, r in wb.items():
        if sid not in reg:   # records the workbook references that the python seed lacked
            reg[sid] = RegisterEntry(
                source_id=sid, title=str(r["investigation"]), publisher="NASA PSI (per workbook record URL)",
                source_type="PSI investigation record (from workbook)", identifier=str(r["investigation_id"]),
                year="", source_class="UNVERIFIED (added from workbook)", seed_status="not in legacy register",
                notes=str(r.get("objective_from_supplied_PSI_listing") or ""), key_passage="",
                origin="workbook_added")
        e = reg[sid]
        e.url = r.get("official_record_or_reference")
        e.research_topic = str(r.get("research_family") or "")
        e.workbook_note = str(r.get("verification_and_data_status") or "")
        e.notes = e.notes or str(r.get("objective_from_supplied_PSI_listing") or "")

    manifest = load_manifest(settings.raw_dir)
    for fn, m in manifest.items():
        rid = m.get("register_id") or m.get("source_id")
        if rid and rid not in reg:
            reg[rid] = RegisterEntry(
                source_id=rid, title=m.get("title", fn), publisher=m.get("publisher", ""),
                source_type=m.get("document_type", "document"), identifier=m.get("identifier", ""),
                year=str(m.get("year", "")), source_class="UNVERIFIED (added from manifest)",
                seed_status="not in legacy register", notes=m.get("note", ""), key_passage="",
                url=m.get("url"), origin="manifest_added")
        if rid in reg and m.get("note"):
            reg[rid].manual_flags.append("Manifest note: " + m["note"])
    downloaded_ids = {m["source_id"] for fn, m in manifest.items() if (settings.raw_dir / fn).exists()}
    indexed_ids = {c.register_id for c in load_ingested_chunks(settings.processed_dir)}

    seen_ident: Dict[str, str] = {}
    for sid, e in reg.items():
        e.official_source_identified = e.source_class.upper().startswith("OFFICIAL")
        e.downloaded = sid in downloaded_ids
        e.indexed_document = sid in indexed_ids
        e.catalogue_indexed = True
        if e.identifier in seen_ident and e.identifier.startswith("NTRS"):
            e.manual_flags.append(f"Same identifier as {seen_ident[e.identifier]} - possible duplicate record")
        seen_ident.setdefault(e.identifier, sid)
        if not e.url:
            e.manual_flags.append("No official URL recorded")
        if not e.downloaded:
            e.manual_flags.append("No source file downloaded/ingested; only catalogue/summary text indexed")
        if "truncated" in e.workbook_note.lower():
            e.manual_flags.append("Workbook: listing text truncated - read full record")
        if e.origin == "workbook_added":
            e.manual_flags.append("Record added from workbook; no seed passage and no metadata check")
        e.manual_flags.append("URL/DOI not verified in this run (no web verification performed)")
    return reg


def catalogue_chunks(reg: Dict[str, RegisterEntry], wb_rows: List[Dict[str, Any]]) -> List[DocumentChunk]:
    """Index each register record as a clearly-typed CATALOGUE chunk (metadata only, never raw data)."""
    wb = {r["register_id"]: r for r in wb_rows}
    out = []
    for sid, e in reg.items():
        parts = [e.title + ".", f"Publisher: {e.publisher}.", f"Type: {e.source_type}.",
                 f"Identifier: {e.identifier}.", f"Year: {e.year}." if e.year else "",
                 e.notes if e.notes.endswith(".") or not e.notes else e.notes + ".", e.key_passage]
        r = wb.get(sid)
        if r:
            parts += [f"Objective (supplied PSI listing): {r.get('objective_from_supplied_PSI_listing')}",
                      f"Approach (supplied PSI listing): {r.get('approach_from_supplied_PSI_listing')}"]
        text = " ".join(p.strip() for p in parts if p and str(p).strip() and str(p) != "None")
        out.append(DocumentChunk(chunk_id=f"cat_{sid}", source_id=sid, register_id=sid, title=e.title,
                                 content=text, page=None, section=None, content_type="catalogue_record",
                                 url=e.url, metadata={"identifier": e.identifier, "origin": e.origin}))
    return out


def seed_chunks(reg) -> List[DocumentChunk]:
    out = []
    for c in SEED_CHUNKS:
        rid = c.metadata.get("source_id", c.source_id)
        out.append(DocumentChunk(chunk_id=c.chunk_id, source_id=c.source_id, register_id=rid, title=c.title,
                                 content=c.content, page=None, section=c.metadata.get("section"),
                                 content_type="seed_summary", url=getattr(reg.get(rid), "url", None),
                                 metadata={**c.metadata, "provenance": "hand-written summary in legacy rag_pipeline.py; "
                                           "NOT extracted from a source file; page numbers unknown"}))
    return out


def build_corpus(settings):
    reg = build_register(settings)
    wb_rows = _read_workbook_map(settings.workbook_path)
    real = load_ingested_chunks(settings.processed_dir)
    real_ids = {c.register_id for c in real}
    # hand-written seed summaries are superseded once the real document for that source is ingested
    seeds = [c for c in seed_chunks(reg) if c.register_id not in real_ids]
    chunks = seeds + catalogue_chunks(reg, wb_rows) + real
    return reg, chunks
