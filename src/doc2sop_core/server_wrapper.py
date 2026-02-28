"""Server wrapper for doc2sop-core pipeline.

Provides a clean API for the Flask server to use the pipeline.
"""

import json
import tempfile
from pathlib import Path
from typing import Optional

from . import pipeline


class Doc2SOPServer:
    """Server-side interface to doc2sop pipeline."""
    
    def __init__(self, use_llm: bool = False):
        """Initialize server wrapper.
        
        Args:
            use_llm: Whether to use Ollama LLM stages (default: False)
        """
        self.use_llm = use_llm
    
    def generate_sop(
        self,
        process_notes: str,
        source_format: str = "txt",
    ) -> dict:
        """Generate SOP from raw process notes.
        
        Args:
            process_notes: Raw text describing the process
            source_format: Format hint (txt, md, etc.)
        
        Returns:
            Dict with sop text, flags, acceptance report
        """
        # Create temporary job folder
        with tempfile.TemporaryDirectory() as tmpdir:
            job_path = Path(tmpdir)
            p = pipeline.mkpaths(job_path)
            pipeline.ensure_dirs(p)
            
            # Write source to intake
            source_file = p.intake / f"source.{source_format}"
            source_file.write_text(process_notes, encoding="utf-8")
            
            # Run pipeline
            result = pipeline.run_pipeline(
                job_path,
                use_llm=self.use_llm,
            )
            
            # Read outputs
            deliverable = (p.final / "deliverable.md").read_text(encoding="utf-8")
            flags = (p.structure / "flags.md").read_text(encoding="utf-8")
            
            return {
                "sop": deliverable,
                "flags": flags,
                "acceptance": result["acceptance"],
            }
    
    def generate_sop_from_files(
        self,
        files: list[tuple[str, str, bytes]],
    ) -> dict:
        """Generate SOP from uploaded files.
        
        Args:
            files: List of (filename, content_type, content_bytes) tuples
        
        Returns:
            Dict with sop text, flags, acceptance report
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            job_path = Path(tmpdir)
            p = pipeline.mkpaths(job_path)
            pipeline.ensure_dirs(p)
            
            # Write files to intake
            for filename, content_type, content in files:
                dest = p.intake / filename
                if isinstance(content, bytes):
                    dest.write_bytes(content)
                else:
                    dest.write_text(content, encoding="utf-8")
            
            # Run pipeline
            result = pipeline.run_pipeline(
                job_path,
                use_llm=self.use_llm,
            )
            
            # Read outputs
            deliverable = (p.final / "deliverable.md").read_text(encoding="utf-8")
            flags = (p.structure / "flags.md").read_text(encoding="utf-8")
            
            return {
                "sop": deliverable,
                "flags": flags,
                "acceptance": result["acceptance"],
            }
    
    def validate_sop(self, sop_text: str) -> dict:
        """Validate SOP text for quality issues.
        
        Args:
            sop_text: The SOP markdown to validate
        
        Returns:
            Validation report
        """
        lower = sop_text.lower()
        procedure_steps = pipeline.extract_procedure_steps(sop_text)
        
        checks = {
            "banned_phrases": [ph for ph in pipeline.BANNED_PHRASES if ph in lower],
            "has_emoji": bool(pipeline.EMOJI_RE.search(sop_text)),
            "has_question_lines": any(pipeline.QUESTION_RE.search(line) for line in sop_text.splitlines()),
            "procedure_step_count": len(procedure_steps),
        }
        
        ok = (
            (not checks["banned_phrases"]) and
            (not checks["has_emoji"]) and
            (not checks["has_question_lines"]) and
            (checks["procedure_step_count"] >= 1)
        )
        
        return {
            "ok": ok,
            "checks": checks,
        }
