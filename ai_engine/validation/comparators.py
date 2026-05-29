"""
comparators.py — Deep sub-modules for check_similarity.
Each comparator: one seam, one testable thing.
"""
from dataclasses import dataclass
import math


# --- 1. Skeleton comparator (triple extraction + Jaccard) ---

@dataclass
class SkeletonTriple:
    subject: str
    action: str
    obj: str


class SkeletonComparator:
    """Compare narrative skeletons via (role, event, target) triple Jaccard."""

    # Multi-char verbs tried first, then single-char verb stems
    _MULTI_VERBS = frozenset([
        "出发", "启程", "战斗", "作战", "决战", "对决",
        "胜利", "获胜", "击败", "打败", "战胜",
        "拿起", "拿起", "杀死", "杀掉", "救下", "拯救",
        "发现", "找到", "得到", "获得", "夺取", "抢走",
        "来到", "进入", "前往", "逃离", "离开", "回到",
        "帮助", "保护", "背叛", "原谅",
        "求婚", "结婚", "分手", "重逢",
        "穿越", "重生", "觉醒",
        "睡觉", "吃饭", "喝水", "说话",
        "思考", "犹豫", "决定",
    ])

    _SINGLE_VERBS = frozenset("杀拿打走说看想来去用吃喝跑飞跳救赢败助护骂追逃哭笑")

    _VERB_STEM_MAP = {
        "拿起": "拿", "拿起": "拿",
        "杀死": "杀", "杀掉": "杀",
        "救下": "救", "拯救": "救",
        "来到": "来", "进入": "进", "回到": "回",
        "找到": "找", "得到": "得",
        "启程": "出发", "离开": "出发",
        "作战": "战斗", "决战": "战斗", "对决": "战斗",
        "获胜": "胜利", "击败": "胜利", "打败": "胜利", "战胜": "胜利",
        "说话": "说",
        "思考": "想",
    }
    _ROLE_MAP = {
        "小明": "主角", "小红": "主角", "小李": "主角", "小张": "主角",
        "英雄": "主角", "勇士": "主角", "骑士": "主角", "勇者": "主角",
        "反派": "对手", "魔王": "对手", "敌人": "对手", "怪物": "对手",
        "师父": "导师", "师傅": "导师", "老师": "导师",
        "公主": "目标", "王子": "目标",
    }

    def compare(self, orig_text: str, imit_text: str) -> float:
        triples_a = self._extract_triples(orig_text)
        triples_b = self._extract_triples(imit_text)
        if not triples_a and not triples_b:
            return self._bigram_fallback(orig_text, imit_text)
        inter = triples_a & triples_b
        union = triples_a | triples_b
        return len(inter) / len(union) if union else 0.0

    def _extract_triples(self, text: str) -> set[tuple[str, str, str]]:
        if not text or not text.strip():
            return set()
        for sep in "。！？\n":
            text = text.replace(sep, "|")
        sents = [s.strip() for s in text.split("|") if s.strip()]
        triples = set()
        for sent in sents:
            t = self._extract_one(sent)
            if t:
                triples.add(t)
        return triples

    def _extract_one(self, sent: str) -> tuple[str, str, str] | None:
        """Try multi-char verbs first, then single-char stems."""
        # 1. Try multi-character verbs
        for verb in sorted(self._MULTI_VERBS, key=len, reverse=True):
            idx = sent.find(verb)
            if idx < 0:
                continue
            subj = self._normalize(sent[:idx].strip() or "角色")
            obj = self._normalize(sent[idx + len(verb):].strip() or "目标")
            return (subj, self._normalize_verb(verb), obj)
        # 2. Try single-character verb stems
        for i, ch in enumerate(sent):
            if ch in self._SINGLE_VERBS:
                subj = self._normalize(sent[:i].strip() or "角色")
                obj = self._normalize(sent[i + 1:].strip() or "目标")
                return (subj, ch, obj)
        return None

    def _normalize(self, word: str) -> str:
        return self._ROLE_MAP.get(word, word)

    def _normalize_verb(self, verb: str) -> str:
        return self._VERB_STEM_MAP.get(verb, verb)

    def _bigram_fallback(self, a: str, b: str) -> float:
        def _bg(t: str) -> set[str]:
            t = t.replace(" ", "").replace("\n", "")
            return {t[i:i+2] for i in range(len(t) - 1)}
        ba, bb = _bg(a), _bg(b)
        if not ba and not bb:
            return 0.0
        inter = ba & bb
        union = ba | bb
        return len(inter) / len(union) if union else 0.0


# --- 2. Emotion comparator (sequence + DTW) ---

class EmotionComparator:
    """Interface: compare(orig_text, imit_text) -> distance float [0,1]."""

    _LABEL_MAP = {
        "joy": 0.0, "surprise": 0.2, "love": 0.3,
        "fear": 0.5, "anger": 0.6, "sadness": 0.8, "neutral": 0.4,
    }

    def compare(self, orig_text: str, imit_text: str) -> float:
        seq_a = self._emotion_sequence(orig_text)
        seq_b = self._emotion_sequence(imit_text)
        if not seq_a and not seq_b:
            return 0.0
        d = self._dtw(seq_a, seq_b)
        max_possible = max(len(seq_a), len(seq_b)) * 1.0
        return min(d / max_possible, 1.0) if max_possible > 0 else 0.0

    def _emotion_sequence(self, text: str) -> list[float]:
        for sep in "!?。！？\n":
            text = text.replace(sep, ".")
        sents = [s.strip() for s in text.split(".") if s.strip()]
        if not sents:
            return [0.4]
        return [self._LABEL_MAP.get(self._label(s), 0.4) for s in sents]

    def _label(self, sentence: str) -> str:
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

    def __init__(self, embed_fn=None):
        self._embed_fn = embed_fn or self._dummy_embed

    def compare(self, answer_text: str, reference_text: str) -> float:
        emb_a = self._embed_fn(answer_text)
        emb_b = self._embed_fn(reference_text)
        return self._cosine(emb_a, emb_b)

    def _dummy_embed(self, text: str) -> list[float]:
        return [hash(text) % 1000 / 1000.0]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
