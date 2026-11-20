"""Canonical Experiment Mapping module for NASA Spacecraft Fire Safety RAG.

Maps between:
- Dashboard Canonical IDs: EXP-001, EXP-002, ..., EXP-010 (and MOCK-EXP-001..003)
- PSI Experiment Codes / Aliases: PSI-25 (BASS-II), Saffire-VI, SAME, SPICE (PSI-107), SLICE (PSI-106), etc.
- Primary Indexed NASA Research Sources: S28, S29, S31, S56, S24, S23, S50, S51, S52, etc.

Maintains strict separation of concerns:
- Research RAG Module: Provides scientific explanations, combustion physics, qualitative evidence passages, and literature citations.
- Scientific Data Module: Provides quantitative sensor telemetry, units, calculations, and measured values.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_MAP_FILE = Path(__file__).resolve().parents[1] / "source_register" / "experiment_mapping.json"

_CACHED_MAPPINGS: Optional[List[Dict[str, Any]]] = None
_INDEX_BY_KEY: Optional[Dict[str, Dict[str, Any]]] = None


def get_all_mappings() -> List[Dict[str, Any]]:
    """Return full list of canonical experiment mappings."""
    global _CACHED_MAPPINGS
    if _CACHED_MAPPINGS is None:
        if _MAP_FILE.exists():
            _CACHED_MAPPINGS = json.loads(_MAP_FILE.read_text(encoding="utf-8"))
        else:
            _CACHED_MAPPINGS = []
    return _CACHED_MAPPINGS


def _get_lookup_index() -> Dict[str, Dict[str, Any]]:
    """Build normalized lookup index by canonical_id, psi_id, and aliases."""
    global _INDEX_BY_KEY
    if _INDEX_BY_KEY is None:
        index = {}
        for entry in get_all_mappings():
            cid = entry.get("canonical_id", "").upper()
            if cid:
                index[cid] = entry
            psi_id = entry.get("psi_id", "").upper()
            if psi_id:
                index[psi_id] = entry
            for alias in entry.get("aliases", []):
                index[alias.upper()] = entry
        _INDEX_BY_KEY = index
    return _INDEX_BY_KEY


def resolve_experiment(identifier: str) -> Optional[Dict[str, Any]]:
    """Resolve an experiment ID, PSI ID, or alias to canonical mapping."""
    if not identifier:
        return None
    key = identifier.strip().upper()
    return _get_lookup_index().get(key)


def get_experiment_sources(identifier: str) -> List[str]:
    """Return primary research source IDs (e.g. ['S28', 'S29']) for an experiment."""
    rec = resolve_experiment(identifier)
    return rec.get("primary_sources", []) if rec else []


def resolve_experiment_ids_to_sources(experiment_ids: List[str]) -> Dict[str, Any]:
    """Resolve a list of experiment IDs to target sources and canonical records.

    Returns:
      target_sources: list of unique S-ids to focus retrieval
      resolved: list of resolved canonical experiment records
      unresolved: list of unmapped IDs
    """
    target_sources = []
    resolved = []
    unresolved = []
    seen_src = set()
    seen_cid = set()

    for eid in experiment_ids:
        rec = resolve_experiment(eid)
        if rec:
            cid = rec["canonical_id"]
            if cid not in seen_cid:
                seen_cid.add(cid)
                resolved.append(rec)
            for s in rec.get("primary_sources", []):
                if s not in seen_src:
                    seen_src.add(s)
                    target_sources.append(s)
        else:
            unresolved.append(eid)

    return {
        "target_sources": target_sources,
        "resolved_experiments": resolved,
        "unresolved_ids": unresolved,
    }
