"""doc2sop-core: Document to SOP transformation pipeline."""

from .pipeline import run_pipeline, mkpaths, ensure_dirs, Paths

__all__ = ["run_pipeline", "Paths", "mkpaths", "ensure_dirs"]
__version__ = "0.1.0"
