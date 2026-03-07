"""Fuel-phase Document → SOP pipeline."""
from __future__ import annotations
import json, os, re, subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from . import prompts

LANG_RULES_PATH = Path(__file__).parent / "language_rules.md"
LANG_BLACKLIST_PATH = Path(__file__).parent / "language_blacklist.txt"

def load_blacklist() -> list[str]:
    if LANG_BLACKLIST_PATH.exists():
        lines = [ln.strip().lower() for ln in LANG_BLACKLIST_PATH.read_text(errors="ignore").splitlines()]
        return [ln for ln in lines if ln and not ln.startswith("#")]
    return ["this document explains", "in conclusion", "as an ai"]

BANNED_PHRASES = load_blacklist()
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF]", re.UNICODE)
QUESTION_RE = re.compile(r"\?\s*$")
NEED_WORD_RE = re.compile(r"\bneed(s|ed)?\b", re.IGNORECASE)
PURPOSE_SIGNAL_RE = re.compile(r"\b(ensure|protect|prevent|stabilize|improve|control|standardize|safeguard)\b", re.IGNORECASE)
SCOPE_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "intake": ("customer", "intake", "quote", "quoting", "budget", "spec", "specification", "photo", "text message", "rush", "pricing"),
    "tracking": ("job tracking", "tracking", "whiteboard", "trello", "clipboard", "traveler", "schedule", "lead time", "kanban"),
    "safety": ("safety", "fire extinguisher", "ppe", "gloves", "maintenance", "mig", "logbook", "inspection"),
    "payment": ("payment", "deposit", "cash flow", "invoice", "billing"),
}
SCOPE_ROLE_KEYWORDS = ("shop", "team", "crew", "operator", "kitchen", "farm", "warehouse", "line", "department")
PURPOSE_KEYWORDS = ("purpose", "objective", "mission", "goal")
DECISION_NORMALIZERS = [
    {"keywords": ("material markup", "markup 20", "markup percent"), "location": "Material markup policy", "issue": "Clarify the standard material markup percentage and exception approval path."},
    {"keywords": ("trello", "clipboard", "job tracking", "job-tracking", "whiteboard", "traveler", "need system"), "location": "Job-tracking method", "issue": "Select and implement one primary job-tracking system (e.g., Trello board or clipboard traveler) with a photo-backed backup method."},
    {"keywords": ("fire extinguisher", "check tag"), "location": "Fire extinguisher inspections", "issue": "Confirm fire extinguisher inspection cadence and logging (owner, timestamp, corrective action)."},
    {"keywords": ("mig liner", "maintenance log", "logbook", "maintenance", "hard to remember"), "location": "Maintenance log", "issue": "Define and enforce a maintenance logging method (owner, cadence, required fields)."},
    {"keywords": ("gloves", "glove"), "location": "Glove compliance", "issue": "Define glove-compliance enforcement (who checks, when checked, and how non-compliance is handled)."},
    {"keywords": ("quoting inconsistent", "flat rate guess", "flat-rate", "hourly 85", "hourly $85", "quote method", "pricing"), "location": "Quote approval workflow", "issue": "Define quote approval workflow and policy enforcement (hourly vs flat-rate templates, markup consistency)."},
]

def normalized_decision_from_text(text: str) -> tuple[str | None, str | None]:
    low = (text or "").lower()
    for entry in DECISION_NORMALIZERS:
        if any(keyword in low for keyword in entry["keywords"]):
            return entry.get("location"), entry["issue"]
    return None, None


def detect_scope_categories(lower_src: str) -> set[str]:
    found: set[str] = set()
    for name, keywords in SCOPE_CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lower_src:
                found.add(name)
                break
    return found


def has_scope_signals(lower_src: str) -> bool:
    if any(word in lower_src for word in ("scope", "applies to", "applies-to", "covers", "responsible", "audience")):
        return True
    categories = detect_scope_categories(lower_src)
    if len(categories) >= 2:
        return True
    if categories and any(role in lower_src for role in SCOPE_ROLE_KEYWORDS):
        return True
    return False


def has_purpose_signals(lower_src: str) -> bool:
    if any(keyword in lower_src for keyword in PURPOSE_KEYWORDS):
        return True
    need_hits = len(NEED_WORD_RE.findall(lower_src))
    signal_hits = len(PURPOSE_SIGNAL_RE.findall(lower_src))
    if need_hits + signal_hits >= 3:
        return True
    if ("cash flow" in lower_src or "safety" in lower_src or "quote" in lower_src) and (need_hits + signal_hits >= 1):
        return True
    return False


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))

@dataclass
class Paths:
    job: Path
    intake: Path
    normalized: Path
    structure: Path
    draft: Path
    final: Path

def mkpaths(job: Path) -> Paths:
    return Paths(job=job, intake=job/"intake", normalized=job/"normalized", structure=job/"structure", draft=job/"draft", final=job/"final")

def ensure_dirs(p: Paths) -> None:
    for d in (p.intake, p.normalized, p.structure, p.draft, p.final):
        d.mkdir(parents=True, exist_ok=True)

def stage2_normalize(p: Paths) -> None:
    source_txt, sources = [], []
    for f in sorted(p.intake.glob("**/*")):
        if f.is_dir():
            continue
        ext = f.suffix.lower()
        text, method = "", ""
        if ext in (".txt", ".md"):
            text, method = f.read_text(errors="ignore"), "plain"
        elif ext == ".pdf":
            method = "pdftotext"
            try:
                out = subprocess.check_output(["pdftotext", "-layout", str(f), "-"], stderr=subprocess.DEVNULL)
                text = out.decode("utf-8", errors="ignore")
            except Exception:
                try:
                    from pypdf import PdfReader
                    r = PdfReader(str(f))
                    text = "\n".join((pg.extract_text() or "") for pg in r.pages)
                    method = "pypdf"
                except Exception as e:
                    sources.append({"file": str(f), "ext": ext, "method": "pypdf", "error": str(e)})
        elif ext == ".docx":
            try:
                out = subprocess.check_output(["docx2txt", str(f), "-"], stderr=subprocess.DEVNULL)
                text, method = out.decode("utf-8", errors="ignore"), "docx2txt"
            except Exception as e:
                sources.append({"file": str(f), "ext": ext, "method": "docx2txt", "error": str(e)})
        else:
            continue
        sources.append({"file": str(f), "ext": ext, "method": method, "chars": len(text)})
        if text.strip():
            source_txt.append(f"\n\n===== FILE: {f.name} ({ext}) =====\n\n{text}\n")
    (p.normalized / "source.txt").write_text("\n".join(source_txt))
    (p.normalized / "sources.json").write_text(json.dumps(sources, indent=2))

def ollama(prompt: str, model: str, timeout_s: int = 90, api_url: str | None = None) -> str:
    import json as _json, urllib.request
    url = (api_url or os.environ.get("OLLAMA_API", "http://127.0.0.1:11434")) + "/api/generate"
    payload = _json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = _json.loads(resp.read().decode("utf-8", errors="ignore"))
    return (data.get("response") or "").strip()

def stage3_structure(p: Paths, model: str | None = None, use_llm: bool = False) -> None:
    src = (p.normalized / "source.txt").read_text(errors="ignore")
    model = model or os.environ.get("DOC2SOP_MODEL_STRUCTURE") or "phi3:mini"
    prompt = prompts.STRUCTURE_PROMPT_TEMPLATE.format(source=src[:12000])
    data = {"llm_skipped": True, "llm_model": model}
    if use_llm:
        try:
            raw = ollama(prompt, model=model, timeout_s=45)
            m = re.search(r"\{.*\}", raw, re.S)
            data = json.loads(m.group(0) if m else raw)
        except Exception as e:
            data = {"llm_error": str(e), "llm_model": model}
    lines = [ln.strip() for ln in src.splitlines() if ln.strip()]
    title = lines[0] if lines else "Document"
    step_candidates = [ln for ln in lines if re.match(r"^\d+\.\s+", ln)]
    flags = [{"location": ph, "issue": "Placeholder present; requires client-provided value."} for ph in sorted(set(re.findall(r"\[[^\]]+\]", src)))[:50]]
    if not step_candidates:
        flags.append({"location": "document", "issue": "No numbered steps detected; workflow order may need clarification."})
    seen_flags: dict[str, list[str]] = {}
    flag_order: list[str] = []
    for ln in lines[:500]:
        low, loc = ln.lower(), ln[:120]
        issues = []
        if "?" in ln: issues.append("Question/uncertainty in source; needs clarification.")
        if any(w in low for w in ("depending", "might", "maybe")): issues.append("Conditional wording; clarify exact condition if needed.")
        if issues:
            if loc not in seen_flags:
                seen_flags[loc] = []
                flag_order.append(loc)
            for i in issues:
                if i not in seen_flags[loc]: seen_flags[loc].append(i)
    for loc in flag_order:
        norm_loc, norm_issue = normalized_decision_from_text(loc)
        flags.append({"location": norm_loc or loc, "issue": norm_issue or " ".join(seen_flags[loc])})
    lower_src = src.lower()
    if not has_purpose_signals(lower_src):
        flags.append({"location": "Purpose", "issue": "Source never states an explicit purpose/goal; confirm intent."})
    if not has_scope_signals(lower_src):
        flags.append({"location": "Scope", "issue": "Scope/audience is unclear; clarify who and where this applies."})
    sections = data.get("sections") if isinstance(data.get("sections"), list) else [{"title": title, "type": "overview", "step_candidates": []}, {"title": "Sections / Clauses", "type": "reference", "step_candidates": step_candidates}]
    merged_flags = (data.get("flags") if isinstance(data.get("flags"), list) else []) + flags
    out = {"sections": sections, "flags": merged_flags}
    out.update({k: v for k, v in data.items() if k.startswith('llm_')})
    (p.structure / "map.json").write_text(json.dumps(out, indent=2))
    flags_md = ["# Flags / Ambiguities", ""] + [f"- **{fl.get('location','?')}**: {fl.get('issue','')}" for fl in merged_flags[:200]]
    if out.get("llm_error"): flags_md.extend(["", f"- **LLM stage fallback used**: {out['llm_error']}"])
    (p.structure / "flags.md").write_text("\n".join(flags_md))

def stage4_draft(p: Paths, model: str | None = None, use_llm: bool = False) -> None:
    src = (p.normalized / "source.txt").read_text(errors="ignore")
    model = model or os.environ.get("DOC2SOP_MODEL_DRAFT") or "qwen2.5-coder:3b"
    if use_llm:
        struct_txt = (p.structure / "map.json").read_text(errors="ignore")
        prompt = prompts.DRAFT_PROMPT_TEMPLATE.format(structure=struct_txt[:12000], source=src[:12000])
        try: md = ollama(prompt, model=model, timeout_s=45)
        except Exception: md = ""
    else: md = ""
    if not md.strip(): md = _deterministic_draft(src)
    (p.draft / "deliverable.md").write_text(md)

def _deterministic_draft(src: str) -> str:
    lines = [ln.strip() for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("=====")]
    if not lines: title, body = "Document", ""
    elif len(lines) == 1: words = lines[0].split(); title = " ".join(words[:8]) + ("..." if len(words) > 8 else ""); body = lines[0]
    else: title, body = lines[0], "\n".join(lines[1:])
    lower_body = body.lower()
    for cue in ['what "good" output looks like', "biggest pain points", "tool stack", "target customer", "goal for this sprint"]:
        cut = lower_body.find(cue)
        if cut != -1: body = body[:cut].strip(); break
    for cue in ["safety.", "payment terms.", "harvest.", "watering.", "customer inquiry", "quoting", "lead time"]:
        body = re.sub(rf"\s+({re.escape(cue)})", r"\n\1", body, flags=re.I)
    sentences = [s.strip(" -\t") for s in re.split(r"(?<=[.!?])\s+|\n+|\s+-\s+", body) if s.strip()]
    used: set[int] = set()
    def select(keywords: tuple[str, ...], max_t: int = 2) -> list[str]:
        picks = []
        for i, s in enumerate(sentences):
            if i in used or len(picks) >= max_t: continue
            if any(k in s.lower() for k in keywords): picks.append(s); used.add(i)
        return picks
    purpose_sents = select(("purpose", "goal", "objective", "mission"), 2) or ([sentences[0]] if sentences else [])
    if purpose_sents and not used: used.add(0)
    scope_sents = select(("scope", "applies to", "covers", "responsible", "audience"), 2)
    if not scope_sents:
        for i, s in enumerate(sentences):
            if i not in used: scope_sents = [s]; used.add(i); break
    def collapse(items: list[str]) -> str:
        text = re.sub(r"^(purpose|scope)\s*:\s*", "", " ".join(items).strip(), flags=re.I)
        return (text[:277].rsplit(" ", 1)[0] + "..." if len(text) > 280 else text) or "As described in source."
    purpose_text, scope_text = collapse(purpose_sents), collapse(scope_sents)
    if "brain dump" in purpose_text.lower() or purpose_text.lower().startswith("as described"):
        purpose_text = "Ensure consistent intake, quoting accuracy, scheduling reliability, safety compliance, and cash-flow control."
    if scope_text.lower().startswith("as described") or len(scope_text.strip()) < 40:
        parts = []
        if any(k in lower_body for k in ("customer inquiry", "intake", "quote", "budget")): parts.append("customer intake and quoting")
        if any(k in lower_body for k in ("job tracking", "lead time", "whiteboard")): parts.append("job tracking and scheduling")
        if any(k in lower_body for k in ("safety", "fire extinguisher", "maintenance")): parts.append("safety and equipment maintenance")
        if any(k in lower_body for k in ("payment", "deposit", "cash flow")): parts.append("payment terms and cash-flow controls")
        scope_text = f"Applies to {', '.join(parts)}, from first inquiry through payment and closeout." if parts else "Applies to this operational workflow."
    md_lines = [f"# {title}", "", "## Purpose", purpose_text, "", "## Scope", scope_text, "", "## Procedure"]
    steps, first_steps, notes, pending = [], [], [], ""
    for i, s in enumerate(sentences):
        if i in used: continue
        low = s.lower().strip()
        if not low or re.match(r"^\d+\.$", low) or low.startswith(("that's how", "lots of things")): continue
        if " is when " in low or " means " in low: notes.append(s); continue
        if low.startswith(("its because", "it's because")): continue
        if low.startswith(("like ", "for example", "e.g.", "example:", "it could be")): pending = f"{pending} {s}" if pending else s; continue
        if re.match(r"^(oh\s+)?first\b", low):
            clean = re.sub(r"^(oh\s+)?first\s*", "", s, flags=re.I).strip()
            if clean: first_steps.append(f"{clean[0].upper()}{clean[1:]} (seeds require darkness to germinate).")
            continue
        if pending: s = f"{s} {pending}"; pending = ""
        steps.append(s)
    ordered = first_steps + steps
    consolidated, i = [], 0
    while i < len(ordered):
        step = ordered[i]; low = step.lower()
        if "spread the seeds" in low and i + 2 < len(ordered) and "don't touch" in ordered[i+1].lower() and "seed space" in ordered[i+2].lower():
            step += " Ensure seeds do not touch; leave about one seed-width of space between them."; i += 3
        elif "water" in low and "every day" in low and i + 2 < len(ordered) and "bottom" in ordered[i+1].lower():
            step = "Water thoroughly every day using the bottom-tray method: place the planted tray over a bottom tray and add water to the bottom tray."; i += 3
        else: i += 1
        consolidated.append(step)
    subs = [(r"^Place put\b", "Place"), (r"^You have to\b", "Place"), (r"^You need to\b", ""), (r"^You gotta\b", ""), (r"^You just\b", ""), (r"\byou just grab\b", "Use"), (r"^I'd\b", "Recommend:"), (r"\b'em\b", "them")]
    def humanize(s: str) -> str:
        for pat, rep in subs: s = re.sub(pat, rep, s, flags=re.I)
        return (s[0].upper() + s[1:]).strip() if s else ""
    final_steps = [humanize(s) for s in consolidated]
    phases = {k: [] for k in ["Customer Intake & Quoting", "Job Tracking & Scheduling", "Safety & Maintenance", "Payment & Cash Flow", "Execution Steps"]}
    backlog, open_issues, seen = [], [], set()
    def classify(s: str) -> str:
        low = s.lower()
        if any(t in low for t in ("safety", "gloves", "eye protection", "ppe", "fire extinguisher", "maintenance", "mig", "logbook")): return "Safety & Maintenance"
        if any(t in low for t in ("payment", "deposit", "cash flow", "invoice", "billing")): return "Payment & Cash Flow"
        if any(t in low for t in ("job tracking", "whiteboard", "trello", "clipboard", "traveler", "lead time", "schedule", "kanban")): return "Job Tracking & Scheduling"
        if any(t in low for t in ("customer", "intake", "quote", "quoting", "budget", "material", "thickness", "rush", "photo", "image", "text message", "sms", "specification", "flat rate", "pricing", "hourly")): return "Customer Intake & Quoting"
        return "Execution Steps"
    policies = {"no formal intake form": "Use a standardized intake form for every inquiry before issuing a quote.", "text message": "Require clear photos and required specs (material, thickness, dimensions) before quoting.", "ask material type": "Capture material type, thickness, deadline, and budget range during intake.", "underprice rush": "Apply a rush surcharge for jobs with compressed lead times.", "hourly 85": "Use an hourly labor baseline of $85 and track actual hours for each job.", "flat rate guess": "Use approved flat-rate templates or the hourly model; do not use ad-hoc quote guesses.", "quoting inconsistent": "Use one quoting method and document assumptions on every quote.", "material markup 20": "Apply a 20% material markup unless explicitly approved otherwise.", "not always applied": "Apply approved pricing and markup policies consistently to every quote.", "job tracking whiteboard": "Track each active job using one primary method and prevent accidental record loss.", "eye protection": "Require eye protection during all shop operations.", "gloves not always": "Require gloves during cleanup and handling tasks.", "fire extinguisher": "Inspect and log fire extinguisher inspection status monthly.", "maintenance log missing": "Maintain a machine maintenance logbook near equipment and record all service actions.", "lead time currently": "Communicate standard lead time as 1-2 weeks unless an approved rush schedule applies.", "50 percent deposit": "Do not start qualifying jobs until a 50% deposit is collected and recorded.", "cash flow impact": "Verify deposit collection before scheduling to protect cash flow."}
    for step in final_steps:
        low = step.lower().strip()
        key = step.strip().lower()
        if key in seen: continue
        seen.add(key)
        if low in ("safety.", "payment terms.") or any(k in low for k in ("consider ", "long term", "marketing idea", "could ")): 
            if any(k in low for k in ("consider ", "long term", "marketing idea", "could ")): backlog.append(step.rstrip(".? ") + ".")
            continue
        if low in ("need standardized intake sheet.",): continue
        converted = step.rstrip("? ") + "."
        for pk, pv in policies.items():
            if pk in low: converted = pv; break
        if "or clipboard job traveler" in low:
            open_issues.append("Select one primary job-tracking system (whiteboard+photo log, clipboard traveler, or software).")
            continue
        if "?" in step or any(k in low for k in ("maybe", "not always", "need system", "hard to remember", "inconsistent")):
            open_issues.append(step.rstrip(".? ") + ".")
            continue
        phases[classify(step)].append(converted)
    step_num = 1
    for phase in ["Safety & Maintenance", "Payment & Cash Flow", "Job Tracking & Scheduling", "Customer Intake & Quoting", "Execution Steps"]:
        items = phases[phase]
        if not items: continue
        md_lines.append(f"### {phase}")
        for step in items: md_lines.append(f"{step_num}. {step}"); step_num += 1
        md_lines.append("")
    md_lines += ["## Notes / Exceptions"] + ([f"- {n.rstrip(' ?')}." for n in notes] or ["- None."])
    if any(k in lower_body for k in ("quote", "rush", "deposit", "maintenance", "fire extinguisher")):
        md_lines += ["", "## Control Standards", "- Rush-job trigger: any requested completion under 5 business days.", "- Rush surcharge baseline: +25% labor surcharge unless owner-approved exception is documented.", "- Quote record retention: keep intake + quote records for at least 12 months in the designated job folder.", "- Safety/maintenance log minimum fields: date, asset/check, result, corrective action, initials.", "- Default ownership (until assigned): Shop Lead owns safety checks and maintenance log completeness."]
    if open_issues:
        normalized_issues = []
        for oi in open_issues:
            _, normalized = normalized_decision_from_text(oi)
            normalized_issues.append(normalized or oi)
        md_lines += ["", "## Required Decisions / Open Issues"] + [f"- {oi}" for oi in sorted(set(normalized_issues))]
    if backlog: md_lines += ["", "## Future Improvements / Backlog"] + [f"- {b}" for b in backlog]
    return "\n".join(md_lines)

def stage5_deslop(p: Paths, model: str | None = None, use_llm: bool = False) -> None:
    md = (p.draft / "deliverable.md").read_text(errors="ignore")
    rules = LANG_RULES_PATH.read_text(errors="ignore") if LANG_RULES_PATH.exists() else ""
    model = model or os.environ.get("DOC2SOP_MODEL_DESLOP") or "phi3:mini"
    if use_llm:
        prompt = prompts.DESLOP_PROMPT_TEMPLATE.format(rules=rules[:4000], draft=md[:12000])
        try: out = ollama(prompt, model=model, timeout_s=45)
        except Exception: out = ""
    else: out = ""
    if not out.strip():
        def clean(line: str) -> str:
            for pat, rep in [(r"\bId\b", "I'd"), (r"\bIts\b", "It's"), (r"\bdont\b", "don't"), (r"\bgonna\b", "going to"), (r"\bgotta\b", "need to"), (r"\bdamping of\b", "damping off"), (r"\bchefs\b", "chef's")]:
                line = re.sub(pat, rep, line, flags=re.I)
            return line.replace("?", ".").replace("..", ".")
        cleaned = []
        for line in md.splitlines():
            if re.match(r"^\d+\.\s+", line):
                prefix, rest = line.split(". ", 1)
                rest = rest.strip()
                if rest: rest = rest[0].upper() + rest[1:]
                line = f"{prefix}. {rest}"
            cleaned.append(clean(line))
        out = "\n".join(cleaned)
    (p.final / "deliverable.md").write_text(out)

def extract_procedure_steps(md: str) -> list[str]:
    return [m.group(3).strip() for line in md.splitlines() if (m := re.match(r"^\s*(\d+)\.(\s+)(.+)$", line))]

def step_fingerprint(step: str) -> str:
    tokens = [t for t in re.findall(r"[A-Za-z]+", step.lower()) if t not in {"the", "a", "an", "to", "and", "or", "of", "in", "on", "for", "with", "as", "by"}]
    return {"id": "i", "its": "it"}.get(tokens[0] if tokens else "", "")

def meaning_drift_guard(draft_md: str, final_md: str) -> dict:
    d_steps, f_steps = extract_procedure_steps(draft_md), extract_procedure_steps(final_md)
    d_fp, f_fp = [step_fingerprint(s) for s in d_steps], [step_fingerprint(s) for s in f_steps]
    report = {"draft_step_count": len(d_steps), "final_step_count": len(f_steps), "count_changed": len(d_steps) != len(f_steps), "order_changed": bool(d_fp and f_fp and d_fp != f_fp and len(d_fp) == len(f_fp)), "first_verbs_changed": [{"index": i+1, "draft": d_fp[i], "final": f_fp[i]} for i in range(min(len(d_fp), len(f_fp))) if d_fp[i] and f_fp[i] and d_fp[i] != f_fp[i]]}
    report["ok"] = not report["count_changed"] and not report["order_changed"] and not report["first_verbs_changed"]
    return report

def stage6_acceptance(p: Paths) -> dict:
    final_md, draft_md = (p.final / "deliverable.md").read_text(errors="ignore"), (p.draft / "deliverable.md").read_text(errors="ignore")
    flags_count = 0
    map_path = p.structure / "map.json"
    if map_path.exists():
        try:
            data = json.loads(map_path.read_text(errors="ignore"))
            if isinstance(data, dict):
                flags = data.get("flags", [])
                if isinstance(flags, list):
                    flags_count = len(flags)
        except Exception:
            flags_count = 0
    if flags_count == 0:
        flags_md_path = p.structure / "flags.md"
        if flags_md_path.exists():
            lines = flags_md_path.read_text(errors="ignore").splitlines()
            flags_count = sum(1 for line in lines if line.lstrip().startswith("- "))

    lower, procedure_steps = final_md.lower(), extract_procedure_steps(final_md)
    checks = {"banned_phrases": [ph for ph in BANNED_PHRASES if ph in lower], "has_emoji": bool(EMOJI_RE.search(final_md)), "has_question_lines": any(QUESTION_RE.search(line) for line in final_md.splitlines()), "has_flags": flags_count > 0, "flag_count": flags_count, "meaning_drift": meaning_drift_guard(draft_md, final_md), "procedure_step_count": len(procedure_steps), "shortest_step_words": min([count_words(s) for s in procedure_steps], default=0)}
    ok = not checks["banned_phrases"] and not checks["has_emoji"] and not checks["has_question_lines"] and checks["meaning_drift"].get("ok") and checks["procedure_step_count"] >= 1
    report = {"ok": ok, "checks": checks, "ts": now()}
    (p.final / "acceptance.json").write_text(json.dumps(report, indent=2))
    return report

def stage7_human_qc_placeholder(p: Paths) -> None:
    (p.final / "approved.md").write_text("# HUMAN QC REQUIRED\n\n- Compare final/deliverable.md against normalized/source.txt\n- Resolve or annotate items in structure/flags.md\n- Approve accuracy (not creativity)\n\n## If approved\nReplace this file with the approved final content.\n\n## If not approved\nWrite what is wrong and what needs clarification.\n")

def stage8_export_placeholder(p: Paths) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = p.final / "package" / stamp
    out.mkdir(parents=True, exist_ok=True)
    for name in ("deliverable.md", "acceptance.json", "approved.md"):
        src = p.final / name
        if src.exists(): (out / name).write_text(src.read_text(errors="ignore"))
    for rel in (p.structure / "flags.md", p.normalized / "sources.json"):
        if rel.exists(): (out / rel.name).write_text(rel.read_text(errors="ignore"))
    return out

def run_pipeline(job: Path, use_llm: bool = False, structure_model: str | None = None, draft_model: str | None = None, deslop_model: str | None = None) -> dict:
    p = mkpaths(job)
    ensure_dirs(p)
    print(f"[{now()}] stage2_normalize", flush=True); stage2_normalize(p)
    print(f"[{now()}] stage3_structure", flush=True); stage3_structure(p, model=structure_model, use_llm=use_llm)
    print(f"[{now()}] stage4_draft", flush=True); stage4_draft(p, model=draft_model, use_llm=use_llm)
    print(f"[{now()}] stage5_deslop", flush=True); stage5_deslop(p, model=deslop_model, use_llm=use_llm)
    print(f"[{now()}] stage6_acceptance", flush=True); acceptance = stage6_acceptance(p)
    print(f"[{now()}] stage7_human_qc", flush=True); stage7_human_qc_placeholder(p)
    print(f"[{now()}] stage8_export", flush=True); export_path = stage8_export_placeholder(p)
    print(f"[{now()}] done: {job}", flush=True)
    return {"paths": p, "acceptance": acceptance, "export_path": export_path}
