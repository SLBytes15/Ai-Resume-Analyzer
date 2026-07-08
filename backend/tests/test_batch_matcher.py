import unittest
from pathlib import Path

from services.batch_matcher import run_candidate_matcher


class BatchMatcherTests(unittest.TestCase):
    def test_run_candidate_matcher_returns_ranked_candidates(self):
        profiles_dir = Path(__file__).resolve().parents[1] / "candidate_profiles"
        jd = {
            "jd_id": "jd_test",
            "role": "Full Stack Developer",
            "skills": ["React", "Node.js", "TypeScript", "PostgreSQL"],
            "minimum_years": 4,
        }

        results = run_candidate_matcher(
            jd_data=jd,
            profiles_dir=str(profiles_dir),
            chroma_db_path=str(profiles_dir.parent / "chroma_db"),
        )

        self.assertTrue(results, "Expected at least one ranked candidate")
        self.assertEqual(results[0]["id"], "cand_001")
        self.assertIn("React", results[0]["matched_skills"])


if __name__ == "__main__":
    unittest.main()
