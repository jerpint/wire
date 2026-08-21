import importlib.machinery
import importlib.util
import pathlib
import subprocess
import unittest
from unittest.mock import patch


def load_wire():
    path = pathlib.Path(__file__).with_name("wire")
    loader = importlib.machinery.SourceFileLoader("wire_under_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


wire = load_wire()


class SpawnTests(unittest.TestCase):
    def test_claude_waits_between_paste_and_submit(self):
        self.assertEqual(wire.get_harness("claude")["paste_settle"], 0.2)

    def test_split_of_starts_and_tracks_exact_new_pane(self):
        calls = []

        def run(cmd, check=True):
            calls.append(cmd)
            if "display-message" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "%9:work\n", "")
            if "split-window" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "%10\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            patch.object(wire, "_run", side_effect=run),
            patch.object(wire, "agents", return_value=[]),
            patch.object(wire, "tmux_sessions", return_value=[]),
            patch.object(wire, "_tmux_supports_session_env", return_value=True),
            patch.object(wire, "_env_args", return_value=[]) as env_args,
            patch.object(wire, "wait_ready", return_value=True) as ready,
            patch.object(wire, "pane_blocked", return_value=""),
            patch.object(wire, "paste") as paste,
            patch.object(wire.time, "sleep"),
        ):
            result = wire.spawn(
                "claude", "hello", name="reviewer", model="sonnet",
                split_of="%9",
            )

        split = next(cmd for cmd in calls if "split-window" in cmd)
        self.assertEqual(split[:8], [
            "tmux", "split-window", "-d", "-t", "%9", "-P", "-F",
            "#{pane_id}",
        ])
        self.assertEqual(split[-1], "claude --model sonnet")
        self.assertIn(
            ["tmux", "set", "-p", "-t", "%10", "@wire_name", "reviewer"],
            calls,
        )
        ready.assert_called_once_with("%10", "claude")
        env_args.assert_called_once_with(None, inherit=False)
        paste.assert_called_once()
        self.assertEqual(result["session"], "work")
        self.assertEqual(result["pane"], "%10")
        self.assertEqual(result["addr"], "reviewer")
        self.assertTrue(result["briefed"])

    def test_regular_spawn_captures_the_new_pane(self):
        calls = []

        def run(cmd, check=True):
            calls.append(cmd)
            if "new-session" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "%20\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with (
            patch.object(wire, "_run", side_effect=run),
            patch.object(wire, "agents", return_value=[]),
            patch.object(wire, "tmux_sessions", return_value=[]),
            patch.object(wire, "_tmux_supports_session_env", return_value=False),
        ):
            result = wire.spawn("codex", name="worker", inherit_env=False)

        new_session = next(cmd for cmd in calls if "new-session" in cmd)
        self.assertIn("-P", new_session)
        self.assertIn("#{pane_id}", new_session)
        self.assertEqual(result["pane"], "%20")
        self.assertEqual(result["session"], "worker")

    def test_split_of_rejects_an_unknown_target(self):
        error = subprocess.CalledProcessError(
            1, ["tmux"], stderr="can't find pane: %999\n"
        )
        with (
            patch.object(wire, "agents", return_value=[]),
            patch.object(wire, "tmux_sessions", return_value=[]),
            patch.object(wire, "_run", side_effect=error),
        ):
            with self.assertRaisesRegex(wire.WireError, "no tmux pane"):
                wire.spawn("claude", split_of="%999")


if __name__ == "__main__":
    unittest.main()
