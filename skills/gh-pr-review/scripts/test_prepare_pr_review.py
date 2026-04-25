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

    def test_api_route_diff_uses_specialized_risk_lenses(self) -> None:
        # Given: API route, auth helper, and tests changed together
        files = [
            {"path": "app/api/users/route.ts", "additions": 80, "deletions": 10},
            {"path": "lib/auth/authorizer.ts", "additions": 30, "deletions": 8},
            {"path": "tests/app/api/users/route.test.ts", "additions": 40, "deletions": 2},
        ]

        # When: lens hints を構築する
        lens_hints = build_lens_hints(files)

        # Then: access/scope と failure handling は汎用 security/correctness から独立して選定される
        self.assertIn("access-control", lens_hints["recommended_lenses"])
        self.assertIn("failure-modes", lens_hints["recommended_lenses"])
        self.assertIn("api-contract", lens_hints["recommended_lenses"])
        self.assertIn("tests", lens_hints["recommended_lenses"])
        self.assertIn("app/api/users/route.ts", lens_hints["lenses"]["access-control"]["focus_files"])
        self.assertIn("app/api/users/route.ts", lens_hints["lenses"]["failure-modes"]["focus_files"])
        self.assertEqual(lens_hints["coverage_gaps"], [])

    def test_migration_diff_uses_data_integrity_lens(self) -> None:
        # Given: destructive migration と migration test が変更されている
        files = [
            {
                "path": "supabase/migrations/20260425120000_retire_old_table.sql",
                "additions": 180,
                "deletions": 0,
            },
            {
                "path": "tests/config/retire-old-table-migration.test.ts",
                "additions": 90,
                "deletions": 0,
            },
        ]

        # When: lens hints を構築する
        lens_hints = build_lens_hints(files)

        # Then: migration/backfill/drop は data-integrity が明示的に担当する
        self.assertIn("data-integrity", lens_hints["recommended_lenses"])
        self.assertIn("tests", lens_hints["recommended_lenses"])
        self.assertIn(
            "supabase/migrations/20260425120000_retire_old_table.sql",
            lens_hints["lenses"]["data-integrity"]["focus_files"],
        )
        self.assertEqual(lens_hints["coverage_gaps"], [])


if __name__ == "__main__":
    unittest.main()
