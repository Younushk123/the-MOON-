from src.config import Settings
from src.source_register import build_corpus
from src.retrieval import HybridRetriever
from src.generator import ExtractiveGenerator, DataStatus

S = Settings()
REG, CH = build_corpus(S)
R = HybridRetriever(CH, REG, S)
G = ExtractiveGenerator(REG, S)


def ask(q):
    return G.generate(q, R.retrieve(q, 5))


def test_exact_oxygen_threshold_abstains_without_numbers():
    res = ask("What exact oxygen threshold did BASS-II measure for ignition?")
    assert res.abstained and res.answer.data_status in (DataStatus.RAW_NOT_INDEXED, DataStatus.INSUFFICIENT)
    assert not any(ch.isdigit() for ch in res.answer.claim.split("insufficient")[0])


def test_unindexed_experiment_abstains():
    res = ask("What were the results of the FLEX-3 experiment?")
    assert res.abstained and res.gate == "missing_entity"


def test_supported_question_does_not_abstain_and_validates():
    res = ask("Why does the ISS fire alarm protocol turn off forced air flow?")
    assert not res.abstained and res.validation.ok
