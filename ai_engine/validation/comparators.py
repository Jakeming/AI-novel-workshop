"""
comparators.py — Deep sub-modules for check_similarity.
Each comparator: one seam, one testable thing.
"""
from dataclasses import dataclass


# --- 1. Skeleton comparator (triple extraction + Jaccard) ---

@dataclass
class SkeletonTriple:
    subject: str
    action: str
    obj: str  # "object" would shadow builtin


class SkeletonComparator:
    """Interface: compare(orig_text, imit_text) -> similarity float [0,1]."""
    interface = "SkeletonComparator"

    def compare(self, orig_text: str, imit_text: str) -> float:
        """Jaccard similarity of extracted (subject, action, obj) triples."""
        orig_triples = self._extract_triples(orig_text)
        imit_triples = self._extract_triples(imit_text)
        if not orig_triples and not imit_triples:
            return 0.0
        intersection = orig_triples & imit_triples
        union = orig_triples | imit_triples
        return len(intersection) / len(union) if union else 0.0

    def _extract_triples(self, text: str) -> set[tuple[str, str, str]]:
        """
        Extract (subject, action, obj) triples.
        Shallow parse for MVP — LLM-based extraction or spaCy can replace later.
        """
        # Placeholder: in MVP, we rely on LLM pre-extraction stored in session.
        # Actual impl uses dependency parsing or LLM call.
        return set()  # Override in subclass for real extraction


# --- 2. Emotion comparator (sequence + DTW) ---

import math


class EmotionComparator:
    """Interface: compare(orig_text, imit_text) -> distance float [0,1]."""
    interface = "EmotionComparator"

    # Emotion label -> numeric mapping for DTW
    _LABEL_MAP = {
        "joy": 0.0, "surprise": 0.2, "love": 0.3,
        "fear": 0.5, "anger": 0.6, "sadness": 0.8, "neutral": 0.4,
    }

    def compare(self, orig_text: str, imit_text: str) -> float:
        """DTW distance between emotion sequences, normalized to [0,1]."""
        seq_a = self._emotion_sequence(orig_text)
        seq_b = self._emotion_sequence(imit_text)
        if not seq_a and not seq_b:
            return 0.0
        dtw_dist = self._dtw(seq_a, seq_b)
        # Normalize by sequence length
        max_possible = max(len(seq_a), len(seq_b)) * 1.0
        return min(dtw_dist / max_possible, 1.0) if max_possible > 0 else 0.0

    def _emotion_sequence(self, text: str) -> list[float]:
        """Split text into sentences, classify each -> numeric value."""
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").replace("。", ".").replace("！", ".").split(".") if s.strip()]
        if not sentences:
            return [0.4]  # default neutral
        # For MVP: use keyword-based heuristic
        result = []
        for sent in sentences:
            label = self._heuristic_label(sent)
            result.append(self._LABEL_MAP.get(label, 0.4))
        return result

    def _heuristic_label(self, sentence: str) -> str:
        """Keyword-based emotion classifier. Pluggable — swap for model later."""
        s = sentence.lower()
        if any(w in s for w in ["伤心", "悲", "哭", "泪"]):
            return "sadness"
        if any(w in s for w in ["怒", "愤", "气"]):
            return "anger"
        if any(w in s for w in ["惊", "吓"]):
            return "fear"
        if any(w in s for w in ["爱", "喜欢"]):
            return "love"
        if any(w in s for w in ["惊喜", "突然"]):
            return "surprise"
        if any(w in s for w in ["快乐", "高兴", "笑"]):
            return "joy"
        return "neutral"

    def _dtw(self, a: list[float], b: list[float]) -> float:
        """Dynamic Time Warp distance."""
        n, m = len(a), len(b)
        dtw = [[math.inf] * (m + 1) for _ in range(n + 1)]
        dtw[0][0] = 0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(a[i - 1] - b[j - 1])
                dtw[i][j] = cost + min(dtw[i - 1][j], dtw[i][j - 1], dtw[i - 1][j - 1])
        return dtw[n][m]


# --- 3. Embedding comparator (LLM-as-judge for three questions) ---

class EmbeddingComparator:
    """Compare user answers to original via cosine similarity on embeddings."""
    interface = "EmbeddingComparator"

    def __init__(self, embed_fn=None):
        self._embed_fn = embed_fn or self._dummy_embed

    def compare(self, answer_text: str, reference_text: str) -> float:
        """Cosine similarity of two texts' embeddings."""
        emb_a = self._embed_fn(answer_text)
        emb_b = self._embed_fn(reference_text)
        return self._cosine(emb_a, emb_b)

    def _dummy_embed(self, text: str) -> list[float]:
        """Placeholder — replace with text-embedding-3-small call."""
        return [hash(text) % 1000 / 1000.0]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
