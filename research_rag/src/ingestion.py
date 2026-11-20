"""Real PDF/DOCX ingestion.

Add a document WITHOUT touching code:
  1. drop the file into data/raw_documents/
  2. add an entry to data/raw_documents/manifest.json:
     {"file.pdf": {"source_id": "S2", "title": "...", "publisher": "...", "url": "...", "doi": "..."}}
Files with no manifest entry are skipped (we refuse to guess a Source ID).
Only fields present in the manifest / file are stored; nothing is invented.
"""
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chunking import chunk_text


@dataclass
class DocumentChunk:
    chunk_id: str
    source_id: str            # original id as ingested (may be a DOC-* id)
    register_id: str          # id used for register lookup / citation
    title: str
    content: str
    page: Optional[int] = None
    section: Optional[str] = None
    content_type: str = "document"   # document | seed_summary | catalogue_record | measurement_table
    url: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self):
        d = asdict(self)
        d["metadata"] = d["metadata"] or {}
        return d


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def clean_text(text: str) -> str:
    text = text.replace("­", "")                       # soft hyphen
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)            # de-hyphenate line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)            # single newlines -> space
    return re.sub(r"\s+", " ", text).strip()


_HEADING = re.compile(r"^(\d+(\.\d+)*\.?)\s+[A-Z][^\n]{2,80}$")


def extract_pdf(path: Path) -> List[Dict[str, Any]]:
    import fitz  # PyMuPDF
    pages = []
    with fitz.open(path) as doc:
        raw = [p.get_text("text") for p in doc]
    # drop running headers/footers: short lines repeated on >50% of pages
    counts = Counter()
    for t in raw:
        # header/footer candidates must look like headers: >=15 chars. (Short repeated lines such as 'of'/'the'
        # are ordinary words in PDFs that put one word per line - dropping them corrupts the text.)
        for ln in {l.strip() for l in t.splitlines() if 15 <= len(l.strip()) < 80}:
            counts[ln] += 1
    repeated = {l for l, c in counts.items() if len(raw) >= 4 and c > len(raw) / 2}
    section = None
    for i, t in enumerate(raw, start=1):
        lines = []
        for l in t.splitlines():
            if l.strip() in repeated:
                continue
            if _HEADING.match(l.strip()):
                section = l.strip()
            lines.append(l)
        pages.append({"page": i, "section": section, "text": clean_text("\n".join(lines))})
    return pages


def extract_docx(path: Path) -> List[Dict[str, Any]]:
    """DOCX has no fixed pages -> page stays None (not invented). Sections come from Heading styles."""
    import docx
    d = docx.Document(str(path))
    blocks, section = [], None
    for p in d.paragraphs:
        if not p.text.strip():
            continue
        if (p.style.name or "").lower().startswith("heading"):
            section = p.text.strip()
        blocks.append({"page": None, "section": section, "text": p.text})
    for t in d.tables:
        for row in t.rows:
            blocks.append({"page": None, "section": section,
                           "text": " | ".join(c.text.strip() for c in row.cells)})
    # merge consecutive blocks sharing a section so chunking sees continuous text
    merged: List[Dict[str, Any]] = []
    for b in blocks:
        if merged and merged[-1]["section"] == b["section"]:
            merged[-1]["text"] += "\n\n" + b["text"]
        else:
            merged.append(dict(b))
    for m in merged:
        m["text"] = clean_text(m["text"])
    return merged


def load_manifest(raw_dir: Path) -> Dict[str, Dict[str, Any]]:
    mf = raw_dir / "manifest.json"
    return json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}


def ingest_directory(raw_dir: Path, processed_dir: Path, chunk_words=180, overlap=30,
                     force=False) -> Dict[str, Any]:
    raw_dir, processed_dir = Path(raw_dir), Path(processed_dir)
    docs_dir = processed_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reg_path = processed_dir / "ingested.json"
    ingested = json.loads(reg_path.read_text()) if reg_path.exists() else {}
    manifest = load_manifest(raw_dir)
    report = {"ingested": [], "skipped_duplicate": [], "skipped_no_manifest": [], "failed": []}

    for path in sorted(raw_dir.iterdir()):
        if path.suffix.lower() not in (".pdf", ".docx"):
            continue
        meta = manifest.get(path.name)
        if not meta or not meta.get("source_id"):
            report["skipped_no_manifest"].append(path.name)
            continue
        digest = sha256_file(path)
        if digest in ingested and not force:
            report["skipped_duplicate"].append(path.name)
            continue
        try:
            pages = extract_pdf(path) if path.suffix.lower() == ".pdf" else extract_docx(path)
        except Exception as e:  # corrupted/encrypted file etc.
            report["failed"].append({"file": path.name, "error": repr(e)})
            continue
        chunks = []
        for pg in pages:
            for j, piece in enumerate(chunk_text(pg["text"], chunk_words, overlap)):
                cid = f"{meta['source_id']}_{digest[:8]}_p{pg['page'] or 'na'}_{len(chunks)}"
                chunks.append(DocumentChunk(
                    chunk_id=cid, source_id=meta["source_id"],
                    register_id=meta.get("register_id", meta["source_id"]),
                    title=meta.get("title") or path.stem, content=piece, page=pg["page"],
                    section=pg["section"], content_type=meta.get("content_type", "document"),
                    url=meta.get("url"),
                    metadata={k: v for k, v in meta.items() if k in ("publisher", "doi", "year")}
                             | {"file": path.name, "sha256": digest},
                ).to_dict())
        (docs_dir / f"{digest}.json").write_text(json.dumps(chunks, indent=1), encoding="utf-8")
        ingested[digest] = {"file": path.name, "source_id": meta["source_id"], "n_chunks": len(chunks)}
        report["ingested"].append({"file": path.name, "chunks": len(chunks)})
    reg_path.write_text(json.dumps(ingested, indent=1))
    return report


def load_ingested_chunks(processed_dir: Path) -> List[DocumentChunk]:
    out = []
    for f in sorted((Path(processed_dir) / "docs").glob("*.json")):
        for d in json.loads(f.read_text(encoding="utf-8")):
            out.append(DocumentChunk(**d))
    return out
