"""The JSON Schema files in shared/schemas/ must match the Pydantic models."""

from app.schema_export import DEFAULT_OUT_DIR, SUFFIX, generate

REGENERATE = "Run `python -m app.schema_export` from backend/ to regenerate."


def test_shared_schemas_are_up_to_date():
    expected = generate()
    on_disk = {p.name: p.read_text(encoding="utf-8") for p in DEFAULT_OUT_DIR.glob(f"*{SUFFIX}")}
    assert set(on_disk) == set(expected), REGENERATE
    for name, text in expected.items():
        assert on_disk[name] == text, f"{name} is stale. {REGENERATE}"
