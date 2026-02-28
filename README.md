# doc2sop-core

Core pipeline for transforming messy client documents into clean, consistent SOP deliverables.

## Installation

```bash
pip install -e .
```

## Usage

```python
from doc2sop_core import pipeline
from pathlib import Path

# Run full pipeline on a job folder
pipeline.run_pipeline(Path("/path/to/job"))
```

## Server Usage

```python
from doc2sop_core.server_wrapper import Doc2SOPServer

server = Doc2SOPServer()
result = server.generate_sop(process_notes="Your notes here...")
```

## Stages

1. **Normalize** - Extract text from various formats (txt, md, pdf, docx)
2. **Structure** - Identify sections, flags, step candidates
3. **Draft** - Create initial SOP with proper headings
4. **Deslop** - Remove AI voice without changing meaning
5. **Acceptance** - Validate output quality
6. **QC** - Human review placeholder
7. **Export** - Package final deliverables
