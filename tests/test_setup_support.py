from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import setup_support as ss


class SetupSupportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def make_source_skill_dir(self) -> Path:
        skill_dir = self.root / "source" / "skill-debug-codex-requests"
        (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
        (skill_dir / "locales").mkdir(parents=True, exist_ok=True)
        (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (skill_dir / ".git").mkdir(parents=True, exist_ok=True)
        (skill_dir / "references").mkdir(parents=True, exist_ok=True)

        (skill_dir / "README.md").write_text("readme\n", encoding="utf-8")
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: debug-codex-requests\n"
            "description: English source description\n"
            "triggers:\n"
            '  - "debug codex requests"\n'
            "---\n\n"
            "# Sample Skill\n",
            encoding="utf-8",
        )
        (skill_dir / "agents" / "openai.yaml").write_text(
            'interface:\n'
            '  display_name: "Debug Codex Requests"\n'
            '  short_description: "English Short"\n'
            '  default_prompt: "Use $debug-codex-requests in English."\n',
            encoding="utf-8",
        )
        (skill_dir / "locales" / "metadata.json").write_text(
            json.dumps(
                {
                    "locales": {
                        "en": {
                            "description": "English localized description",
                            "display_name": "Debug Codex Requests",
                            "short_description": "English Short",
                            "default_prompt": "Use $debug-codex-requests in English.",
                            "local_prefix": "[local] ",
                        },
                        "ru": {
                            "description": "Русское описание",
                            "display_name": "Debug Codex Requests",
                            "short_description": "Русский Short",
                            "default_prompt": "Используй $debug-codex-requests по-русски.",
                            "local_prefix": "[локально] ",
                        },
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (skill_dir / ".skill_triggers").mkdir(parents=True, exist_ok=True)
        (skill_dir / ".skill_triggers" / "en.md").write_text(
            "- debug-codex-requests\n- debug codex requests\n- inspect codex request\n- capture codex api request\n- codex proxy log\n- codex request payload\n- codex system prompt\n",
            encoding="utf-8",
        )
        (skill_dir / ".skill_triggers" / "ru.md").write_text(
            "- отладка codex запросов\n- проверить запросы codex\n- поймать запросы codex\n- лог запроса codex\n- payload codex\n- system_prompt codex\n- схема инструментов codex\n",
            encoding="utf-8",
        )
        (skill_dir / ".git" / "config").write_text("", encoding="utf-8")
        return skill_dir

    def test_render_skill_metadata_dual_mode_merges_trigger_lists(self) -> None:
        skill_dir = self.make_source_skill_dir()

        ss.render_skill_metadata(skill_dir, "ru-en", "local")

        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        openai_yaml = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn(
            'description: "Русское описание Триггеры: \\"отладка codex запросов\\", \\"проверить запросы codex\\", \\"поймать запросы codex\\", \\"лог запроса codex\\", \\"payload codex\\", \\"system_prompt codex\\". / English localized description Triggers: \\"debug-codex-requests\\", \\"debug codex requests\\", \\"inspect codex request\\", \\"capture codex api request\\", \\"codex proxy log\\", \\"codex request payload\\"."',
            skill_text,
        )
        self.assertIn('  - "отладка codex запросов"\n', skill_text)
        self.assertIn('  - "debug-codex-requests"\n', skill_text)
        self.assertIn('display_name: "[локально] Debug Codex Requests"', openai_yaml)
        self.assertIn('short_description: "[локально] Русский Short"', openai_yaml)

    def test_render_skill_metadata_uses_markdown_triggers_as_single_source(self) -> None:
        skill_dir = self.make_source_skill_dir()

        ss.render_skill_metadata(skill_dir, "en", "local")

        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('  - "debug-codex-requests"\n', skill_text)
        self.assertIn(
            'description: "English localized description Triggers: \\"debug-codex-requests\\", \\"debug codex requests\\", \\"inspect codex request\\", \\"capture codex api request\\", \\"codex proxy log\\", \\"codex request payload\\"."',
            skill_text,
        )
        self.assertNotIn('[local] English localized description', skill_text)

    def test_load_metadata_catalog_rejects_trigger_lists_in_metadata_json(self) -> None:
        source_dir = self.make_source_skill_dir()
        metadata_path = source_dir / "locales" / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["locales"]["en"]["triggers"] = ["legacy trigger"]
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(ss.SetupError) as exc:
            ss.load_metadata_catalog(source_dir)

        self.assertIn("must define triggers only in", str(exc.exception))

    def test_perform_global_install_registers_skill_entry_name(self) -> None:
        source_dir = self.make_source_skill_dir()
        home_dir = self.root / "home"
        xdg_data_home = self.root / "xdg-data"
        trigger_instructions = home_dir / ".agents" / ".instructions" / ss.SKILL_TRIGGERS_INCLUDE_NAME
        trigger_instructions.parent.mkdir(parents=True, exist_ok=True)
        (home_dir / ".agents" / ".instructions" / "AGENTS.md").write_text(
            f"@.agents/.instructions/{ss.SKILL_TRIGGERS_INCLUDE_NAME}\n",
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"HOME": str(home_dir), "XDG_DATA_HOME": str(xdg_data_home)}, clear=False):
            result = ss.perform_install(
                source_dir=source_dir,
                install_mode="global",
                requested_locale="ru",
                bootstrap_runner=lambda _: None,
            )

        self.assertEqual(result.runtime_dir, xdg_data_home / "agents" / "skills" / "skill-debug-codex-requests")
        manifest = json.loads((result.runtime_dir / ss.MANIFEST_FILENAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["source_dir"], str(source_dir.resolve()))
        self.assertTrue(result.claude_link.is_symlink())
        self.assertTrue(result.codex_link.is_symlink())
        trigger_text = trigger_instructions.read_text(encoding="utf-8")
        self.assertIn("debug-codex-requests", trigger_text)
        self.assertNotIn("Load `skill-debug-codex-requests`", trigger_text)

    def test_perform_local_install_creates_project_copy_and_agents_modules(self) -> None:
        source_dir = self.make_source_skill_dir()
        repo_root = self.root / "repo"
        repo_root.mkdir(parents=True, exist_ok=True)

        with mock.patch.object(ss, "resolve_repo_root", return_value=repo_root.resolve()):
            result = ss.perform_install(
                source_dir=source_dir,
                install_mode="local",
                requested_locale="ru",
                bootstrap_runner=lambda _: None,
                repo_root=repo_root,
            )

        self.assertEqual(
            result.runtime_dir.resolve(),
            (repo_root / ".skills" / "skill-debug-codex-requests").resolve(),
        )
        self.assertTrue((repo_root / ".agents" / ".instructions" / "INSTRUCTIONS_TESTING.md").exists())
        self.assertIn(
            "@.agents/.instructions/INSTRUCTIONS_TESTING.md",
            (repo_root / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((repo_root / ".claude" / "skills" / "skill-debug-codex-requests").is_symlink())
        self.assertTrue((repo_root / ".codex" / "skills" / "skill-debug-codex-requests").is_symlink())


if __name__ == "__main__":
    unittest.main()
