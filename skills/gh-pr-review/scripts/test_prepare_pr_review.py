import unittest

from prepare_pr_review import build_lens_hints


class BuildLensHintsTest(unittest.TestCase):
    def test_root_level_diff_is_assigned_to_maintainability_without_gaps(self) -> None:
        # Given: 変更ファイルが root-level の設定ファイルだけ
        files = [
            {"path": "package.json", "additions": 12, "deletions": 3},
            {"path": "pnpm-lock.yaml", "additions": 40, "deletions": 20},
        ]

        # When: lens hints を構築する
        lens_hints = build_lens_hints(files)

        # Then: maintainability が root-level diff 全体を担当し coverage gap を残さない
        self.assertEqual(lens_hints["recommended_lenses"], ["maintainability"])
        self.assertEqual(
            lens_hints["lenses"]["maintainability"]["focus_files"],
            ["package.json", "pnpm-lock.yaml"],
        )
        self.assertEqual(lens_hints["coverage_gaps"], [])


if __name__ == "__main__":
    unittest.main()
