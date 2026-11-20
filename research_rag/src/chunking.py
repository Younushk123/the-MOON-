"""Sentence-aware word-window chunking. Never crosses page boundaries, so page numbers stay correct."""
import re
from typing import List

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[0-9])")


def split_sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT.split(text) if s.strip()]


def chunk_text(text: str, max_words: int = 180, overlap_words: int = 30) -> List[str]:
    """Pack whole sentences into windows of <= max_words, carrying ~overlap_words into the next window."""
    sentences = split_sentences(text)
    chunks, cur, cur_n = [], [], 0
    for s in sentences:
        n = len(s.split())
        if cur and cur_n + n > max_words:
            chunks.append(" ".join(cur))
            tail, tail_n = [], 0
            for prev in reversed(cur):          # build overlap from trailing sentences
                pn = len(prev.split())
                if tail_n + pn > overlap_words:
                    break
                tail.insert(0, prev)
                tail_n += pn
            cur, cur_n = tail, tail_n
        cur.append(s)
        cur_n += n
    if cur:
        last = " ".join(cur)
        if not chunks or last != chunks[-1]:
            chunks.append(last)
    return chunks
