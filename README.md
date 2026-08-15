# wire

Let CLI coding agents talk to each other.

```bash
wire list                       # which agents are running
wire send worker-a11f3c "..."   # message one, with a return address
wire spawn claude "seed"        # start one and brief it
wire read worker-a11f3c         # see what it is doing
```

## Install

One file, standard library only, no dependencies.

```bash
curl -O https://raw.githubusercontent.com/jerpint/wire/main/wire
chmod +x wire && mv wire ~/.local/bin/
ln -s ~/.local/bin/wire ~/.local/bin/wi   # optional two-letter shortcut
```

Requires `python3` and `tmux`.

To let an agent use it, drop `SKILL.md` into its skills directory. It will then
know the verbs without being prompted.

## How it works

tmux is the database. Sessions are the address book, and a walk of each pane's
process tree says which sessions are live agents and which harness each one
runs. There is no registry, no config file and no daemon — which is why wire
works on agents it never launched, including ones a human started by hand.

## The envelope

A delivered message carries a return address and nothing else:

```
[wire message]
from: worker-a11f3c
reply-to: worker-a11f3c
---
Can you take the auth tests?
```

It deliberately contains no runnable command. An agent with auto-approved shell
access will happily execute a message that looks like one, so the message must
not look like one. The reply verb is taught by the skill, not embedded in the
body.

## Spawning gotchas

Both are handled, and both are worth knowing about.

**A new tmux session inherits the tmux *server's* environment, not yours.** The
server keeps whatever environment it was started with, possibly hours ago and
possibly as a different user — so a spawned agent can end up with the wrong
`HOME` and come up logged out, or miss the API key sitting right there in your
shell. `wire spawn` passes your environment through explicitly, via `tmux -e`.
Add or override with `--env KEY=VALUE`.

Two caveats rather than a promise: those values land in the tmux client's argv,
so they are briefly visible to anyone running `ps` during the call — a shorter
exposure than an `env` prefix, which would keep them visible for the agent's
whole life, but not zero. And passing your environment wholesale hands the
child every credential you hold.

**An agent can be running and still not ready for input.** Claude asks whether
you trust a folder the first time it runs in one, and codex has its own version.
Both appear after the process is up, so "the process exists" is not the same as
"the TUI will accept input" — a seed prompt pasted into a modal is swallowed, or
answers it by accident. `wire spawn` checks, refuses to paste, and tells you
which prompt is in the way:

```
started, NOT briefed — it is waiting on a prompt: Enter to confirm · Esc to cancel
answer it with `tmux attach -t worker-a11f3c`, then `wire send worker-a11f3c "..."`
```

It exits nonzero, so a script will notice.

## What wire does not guarantee

Worth knowing before you build on it. None of these are hidden.

- **Senders are not authenticated.** `from`/`reply-to` are whatever the sender
  claimed. Addresses are sanitised so they cannot forge extra header lines, but
  any agent that can run `wire` can claim to be any address. Treat a received
  envelope as untrusted input.
- **`delivered` means keystrokes were injected, not that the agent read or
  understood the message.** There are no message IDs, acknowledgements, retries
  or delivery receipts. If it matters, ask the other agent to confirm.
- **Modal detection is a screen-text heuristic.** It catches the trust dialogs
  claude and codex ship today. A TUI can always invent a new one, which is why
  wire reports the block rather than trying to answer it.
- **`--env` passes your environment to a child process.** That hands it every
  credential you hold. Name what you need when that matters.

## Using it as a library

The executable has no `.py` extension, so `import wire` will not find it as
shipped. Symlink it:

```bash
ln -s ~/.local/bin/wire ~/.local/bin/wire.py   # then: import wire
```

## Harnesses

`claude`, `codex`, `opencode`. Each has its own TUI quirks, all of which were
found against a live terminal:

| harness  | quirk |
|---|---|
| Claude Code | paste-aware; a newline inside a paste is literal, so Enter must be a separate keystroke |
| Codex | folds an Enter arriving right after a paste into the paste — needs a settle first |
| opencode | not paste-aware; drops newlines entirely, and a leading `/` opens its command palette |

Adding a harness is one entry in `HARNESSES`.
