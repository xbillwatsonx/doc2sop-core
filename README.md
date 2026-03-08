# doc2sop-core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Transform messy process notes into professional Standard Operating Procedures**

doc2sop-core is a deterministic document-to-SOP transformation pipeline designed for small businesses, freelancers, and consultants who need clear, actionable procedures without the AI fluff.

## What It Does

Takes unstructured process documentation—brain dumps, scattered notes, informal procedures—and converts them into structured, professional SOPs with:
- **Phase-classified procedures** (Intake, Tracking, Safety, Payment, Execution)
- **Policy extraction** (automatically identifies enforceable rules)
- **Quality validation** (acceptance gates, duplicate detection)
- **Human review workflow** (flags ambiguities, never hallucinates steps)

## Why This Exists

Most SOP generators either:
- Call expensive LLM APIs for every document (costly at scale)
- Hallucinate steps not in the source material (dangerous)
- Produce generic, AI-voice output (unprofessional)

doc2sop-core does none of that. It's **deterministic by default**, runs locally, and never invents steps. The output is boring, accurate, and ready for professional use.

## Current Status

**Beta / Early Access** — Core pipeline stable. Founders and early users testing now. Public release roadmap below.

## Quick Start

```python
from doc2sop_core import pipeline
from pathlib import Path

# Run on a job folder with source files in intake/
result = pipeline.run_pipeline(Path("./my-job"))

# Or use the server wrapper
from doc2sop_core.server_wrapper import Doc2SOPServer

server = Doc2SOPServer()
result = server.generate_sop(process_notes="Your raw process notes here...")
```

## The 8-Stage Pipeline

1. **Normalize** — Extract text from PDF, DOCX, TXT, MD
2. **Structure** — Identify sections, flags, step candidates
3. **Draft** — Create initial SOP with proper headings
4. **Deslop** — Remove AI voice without changing meaning
5. **Acceptance** — Validate output quality (banned phrases, emoji, question lines)
6. **QC Gate** — Human review placeholder
7. **Export** — Package final deliverables

## Roadmap

| Phase | Target | Deliverable |
|-------|--------|-------------|
| **Founder Access** | Now | Core pipeline, deterministic mode, REST API |
| **Beta** | Q2 2026 | LLM-assisted stages (opt-in), PDF/DOCX export, hosted service |
| **Public Launch** | Q3 2026 | SaaS with subscription tiers, API keys, team workspaces |

## Philosophy

- **Deterministic first** — Works without API calls, works offline
- **Boring is good** — Professional tone, no marketing speak
- **Never invent** — If it's not in the source, it doesn't go in the SOP
- **Human in the loop** — Flags for review, not guesswork

## License

MIT — Free to use, modify, and distribute. See [LICENSE](LICENSE).

## Contributing

This repository is currently maintained by the core team. While we appreciate interest, we're not accepting external contributions at this time as we prepare for public launch.

---

**Questions?** Open an issue for bugs or feature requests. For business inquiries: [xbillwatsonx@gmail.com](mailto:xbillwatsonx@gmail.com)
