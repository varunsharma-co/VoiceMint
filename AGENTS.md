## Apps

VoiceMint started as a Linux app. That code is in [`linux/`](linux/). The macOS app we are developing is in [`macOS/`](macOS/), and it is run from that directory. Put every macOS code file there.

Open [`linux/`](linux/) only when the user asks you to check it. Use it as a quick behavior reference if needed, but write the macOS-specific version in [`macOS/`](macOS/).

## Agent skills

### Issue tracker

Issues and specs live as GitHub issues in `varunsharma-co/VoiceMint`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context. See `docs/agents/domain.md`.
