from uuid import uuid4


def new_id(prefix: str) -> str:
    """Generate an ID for a computed result, e.g. ANALYSIS-3F9A1C02B7DE."""
    return f"{prefix}-{uuid4().hex[:12].upper()}"
