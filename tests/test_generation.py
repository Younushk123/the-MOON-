"""Groq path tested with a FAKE client: checks validation catches invented citations/quotes. No network."""
import json
from types import SimpleNamespace
from src.config import Settings
from src.source_register import build_corpus
from src.retrieval import HybridRetriever
from src.generator import GroqGenerator, SixPartAnswer

S = Settings()
REG, CH = build_corpus(S)
R = HybridRetriever(CH, REG, S)
Q = "Why does the ISS fire alarm protocol turn off forced air flow?"


def fake_client(payload):
    def create(**kw):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_invented_chunk_id_is_rejected_and_withheld():
    bad = {"abstain": False, "claim": "Made up.", "conditions": "x", "uncertainty": "y",
           "evidence": [{"chunk_id": "chunk_does_not_exist", "quote": "invented"}]}
    res = GroqGenerator(REG, S, client=fake_client(bad)).generate(Q, R.retrieve(Q, 5))
    assert res.abstained and res.gate == "validation_failed" and not res.validation.ok


def test_non_verbatim_quote_is_rejected():
    hits = R.retrieve(Q, 5)
    cid = hits[0].chunk.chunk_id
    bad = {"abstain": False, "claim": "Ventilation is shut off.", "conditions": "x", "uncertainty": "y",
           "evidence": [{"chunk_id": cid, "quote": "this text is not in the chunk at all"}]}
    res = GroqGenerator(REG, S, client=fake_client(bad)).generate(Q, hits)
    assert res.abstained and res.gate == "validation_failed"


def test_verbatim_quote_is_accepted():
    hits = R.retrieve(Q, 5)
    c = hits[0].chunk
    quote = c.content.split(". ")[0]
    good = {"abstain": False, "claim": "As quoted.", "conditions": "stated in passage", "uncertainty": "summary only",
            "evidence": [{"chunk_id": c.chunk_id, "quote": quote}]}
    res = GroqGenerator(REG, S, client=fake_client(good)).generate(Q, hits)
    assert not res.abstained and res.validation.ok


def test_six_fields_required():
    import pytest
    with pytest.raises(Exception):
        SixPartAnswer(claim="x", source="", evidence="e", conditions="c", uncertainty="u", data_status="Verified Document")
