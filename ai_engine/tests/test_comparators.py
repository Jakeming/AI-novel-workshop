"""
test_comparators.py — TDD for EmotionComparator.
Vertical slices: one behavior per test.
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib
EmotionComparator = importlib.import_module("validation.comparators").EmotionComparator


class TestEmotionCompareDistance(unittest.TestCase):

    def test_identical_texts_zero_distance(self):
        ec = EmotionComparator()
        text = "我很伤心。我哭了。"
        self.assertEqual(ec.compare(text, text), 0.0)

    def test_different_emotions_positive_distance(self):
        ec = EmotionComparator()
        sad = "我很伤心。我哭了。"
        happy = "我很高兴。我笑了。"
        self.assertGreater(ec.compare(sad, happy), 0.0)

    def test_empty_texts_zero_distance(self):
        ec = EmotionComparator()
        self.assertEqual(ec.compare("", ""), 0.0)


class TestEmotionKeywords(unittest.TestCase):

    def setUp(self):
        self.ec = EmotionComparator()

    def test_sadness_keywords(self):
        seq = self.ec._emotion_sequence("我很伤心。悲痛欲绝。哭了很久。")
        self.assertEqual(seq, [0.8, 0.8, 0.8])

    def test_anger_keywords(self):
        seq = self.ec._emotion_sequence("他非常愤怒。气得发抖。")
        self.assertEqual(seq, [0.6, 0.6])

    def test_fear_keywords(self):
        seq = self.ec._emotion_sequence("突然一惊。吓死了。")
        self.assertEqual(seq, [0.5, 0.5])

    def test_love_keywords(self):
        seq = self.ec._emotion_sequence("我很爱他。非常喜欢。")
        self.assertEqual(seq, [0.3, 0.3])

    def test_joy_keywords(self):
        seq = self.ec._emotion_sequence("太快乐了。高兴地笑了。")
        self.assertEqual(seq, [0.0, 0.0])

    def test_no_keywords_defaults_neutral2(self):
        seq = self.ec._emotion_sequence("这是测试内容。")
        self.assertEqual(seq, [0.4])


class TestDTW(unittest.TestCase):

    def test_same_sequences_zero(self):
        ec = EmotionComparator()
        d = ec._dtw([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        self.assertEqual(d, 0.0)

    def test_different_sequences_positive(self):
        ec = EmotionComparator()
        d = ec._dtw([0.0, 0.0], [0.8, 0.8])
        self.assertGreater(d, 0.0)

    def test_different_lengths_handled(self):
        ec = EmotionComparator()
        d = ec._dtw([0.0, 0.8], [0.0, 0.4, 0.8])
        self.assertGreater(d, 0.0)
        # DTW with warping -> shorter path found


if __name__ == "__main__":
    unittest.main()
