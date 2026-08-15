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

## Harnesses

`claude`, `codex`, `opencode`. Each has its own TUI quirks, all of which were
found against a live terminal:

| harness  | quirk |
|---|---|
| Claude Code | paste-aware; a newline inside a paste is literal, so Enter must be a separate keystroke |
| Codex | folds an Enter arriving right after a paste into the paste — needs a settle first |
| opencode | not paste-aware; drops newlines entirely, and a leading `/` opens its command palette |

Adding a harness is one entry in `HARNESSES`.
