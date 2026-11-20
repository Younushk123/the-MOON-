from src.config import Settings
from src.source_register import build_corpus
from src.retrieval import HybridRetriever
from src.entities import match_entities
from src.chunking import chunk_text

S = Settings()
REG, CH = build_corpus(S)
R = HybridRetriever(CH, REG, S)          # BM25 + entity only (no embedder)


def test_chunking_nonempty_and_bounded():
    text = " ".join(f"Sentence number {i} is about flames." for i in range(200))
    chunks = chunk_text(text, 50, 10)
    assert chunks and all(0 < len(c.split()) <= 60 for c in chunks)


def test_bass2_does_not_trigger_generic_bass():
    ids, labels = match_entities("What did BASS-II measure?", REG)
    assert "bass-ii" in labels and "bass" not in labels


def test_english_word_same_does_not_trigger_SAME_experiment():
    ids, _ = match_entities("is it the same thing?", REG)
    assert "S21" not in ids and "S22" not in ids


def test_saffire_iii_query_ranks_s20_first():
    assert R.retrieve("Saffire III data from the Cygnus OA-7 flight", 3)[0].chunk.register_id == "S20"


def test_mode_is_honest_about_missing_semantic():
    assert "NOT active" in R.mode
