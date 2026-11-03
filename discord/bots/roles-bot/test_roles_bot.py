import json
import unittest
from pathlib import Path

from roles_bot import MESSAGE_MARKER, diff, render


class RolesBotTest(unittest.TestCase):
    def test_diff(self):
        add, remove = diff({"a", "b"}, {"b", "c"})
        self.assertEqual(add, {"a"})
        self.assertEqual(remove, {"c"})

    def test_diff_nothing_to_do(self):
        self.assertEqual(diff({"a"}, {"a"}), (set(), set()))

    def test_render_uses_config_and_marker(self):
        config = json.loads(Path(__file__).with_name("roles.json").read_text(encoding="utf-8"))
        text = render(config, {r["role"]: "123" for r in config["roles"]})
        self.assertIn(MESSAGE_MARKER, text)
        self.assertIn("🎯 → <@&123>", text)


if __name__ == "__main__":
    unittest.main()
