"""
test_skeleton.py — TDD for SkeletonComparator.
Triple-based Jaccard similarity with verb normalization.
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib
SkeletonComparator = importlib.import_module("validation.comparators").SkeletonComparator


class TestSkeletonCompare(unittest.TestCase):

    def test_identical_texts_similarity_1(self):
        sc = SkeletonComparator()
        self.assertEqual(sc.compare("主角战斗", "主角战斗"), 1.0)

    def test_empty_texts_similarity_0(self):
        sc = SkeletonComparator()
        self.assertEqual(sc.compare("", ""), 0.0)

    def test_one_empty_other_full(self):
        sc = SkeletonComparator()
        self.assertEqual(sc.compare("", "abc"), 0.0)

    def test_synonym_normalization_matches(self):
        """启程→出发, 作战→战斗, 获胜→胜利 should produce identical triples."""
        sc = SkeletonComparator()
        sim = sc.compare("主角出发。主角战斗。主角胜利。",
                         "英雄启程。英雄作战。英雄获胜。")
        self.assertEqual(sim, 1.0)

    def test_verb_stem_normalization(self):
        """拿起→拿, 杀死→杀 should normalize to same stem."""
        sc = SkeletonComparator()
        sim = sc.compare("小明拿起剑。", "小红拿刀。")
        self.assertEqual(sim, 0.0)  # same verb but different objects

    def test_no_known_verbs_falls_back_to_bigram(self):
        """Texts without known verbs use char bigram fallback."""
        sc = SkeletonComparator()
        sim = sc.compare("今天天气很好", "今天天气很好")
        self.assertEqual(sim, 1.0)

    def test_partial_reuse_gives_partial_similarity(self):
        """1/3 triples identical -> Jaccard = 0.333."""
        sc = SkeletonComparator()
        sim = sc.compare("主角杀龙。主角救公主。",
                         "主角杀怪。主角救公主。")
        self.assertAlmostEqual(sim, 0.333, places=2)


if __name__ == "__main__":
    unittest.main()
