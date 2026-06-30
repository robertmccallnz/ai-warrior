#!/usr/bin/env python3
"""
reo-lint.py — Te reo Māori linter for the AI Warrior project.

Scans HTML files (especially `*-mi.html`) for likely te reo Māori errors:
  - Missing macrons (e.g. 'whanau' → 'whānau')
  - Inconsistent terminology across pages
  - Untranslated English on lang="mi" pages
  - Common usage flags (uncapitalised iwi names, etc.)

Usage:
  python scripts/reo-lint.py [FILE ...]              # lint specific files
  python scripts/reo-lint.py --changed origin/main   # lint files changed vs base
  python scripts/reo-lint.py --pr-comment            # output markdown for a PR comment

This is FIRST-PASS triage. Every flag is a candidate for native-speaker review,
not a verdict. The kaupapa is to surface lines worth a kaiako's eye — not to
replace one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_PATH = Path(__file__).resolve().parent / "reo-glossary.json"

# ---------- Models ----------

SEVERITY_HIGH = "high"      # almost certainly an error
SEVERITY_MEDIUM = "medium"  # needs native-speaker eye
SEVERITY_LOW = "low"        # suggestion only

SEVERITY_WEIGHTS = {SEVERITY_HIGH: 4, SEVERITY_MEDIUM: 2, SEVERITY_LOW: 1}


@dataclass
class Flag:
    file: str
    line: int
    severity: str
    category: str
    snippet: str
    message: str
    suggestion: str = ""


@dataclass
class FileReport:
    path: str
    lang: str = ""
    flags: list[Flag] = field(default_factory=list)
    word_count_total: int = 0
    word_count_reo: int = 0


# ---------- HTML text extraction ----------


class _TextOnly(HTMLParser):
    """Strip tags but keep an accurate (line, column) for each text node."""

    SKIP_TAGS = {"script", "style", "code", "pre", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        # Each entry: (line_number_in_source, text)
        self.fragments: list[tuple[int, str]] = []
        self.lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag.lower() == "html":
            for k, v in attrs:
                if k.lower() == "lang" and v:
                    self.lang = v

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if data.strip():
            line, _col = self.getpos()
            self.fragments.append((line, data))


def extract_text(html: str) -> tuple[list[tuple[int, str]], str]:
    p = _TextOnly()
    p.feed(html)
    p.close()
    return p.fragments, p.lang


# ---------- Glossary loading ----------


def load_glossary(path: Path = GLOSSARY_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


# ---------- Helpers ----------

# A "word" for our purposes is a token of letters (incl. macron vowels) only.
WORD_RE = re.compile(r"[A-Za-zĀĒĪŌŪāēīōū']+")

# Vowels including macrons, used to tell whether a token "looks" Māori.
MAORI_VOWELS = set("aeiouāēīōūAEIOUĀĒĪŌŪ")
MAORI_CONSONANTS = set("hkmnprtwŋHKMNPRTWŊ")  # plus digraphs wh, ng


def looks_like_maori_word(word: str) -> bool:
    """A weak heuristic: word uses only Māori-legal letters (a-e-i-o-u, h, k, m, n, p, r, t, w + macrons),
    has at least one vowel, and doesn't contain letters that are illegal in te reo (b, c, d, f, g, j, l, q, s, v, x, y, z — except in 'ng' / 'wh' digraphs already covered)."""
    if not word or len(word) < 2:
        return False
    bad = set("bcdfgjlqsvxyzBCDFGJLQSVXYZ")
    # Allow 'g' only when adjacent to 'n' (ng digraph)
    chars = list(word)
    for i, ch in enumerate(chars):
        if ch in bad:
            if ch.lower() == "g":
                prev = chars[i - 1].lower() if i > 0 else ""
                if prev == "n":
                    continue
            return False
    # Must contain at least one vowel
    if not any(c in MAORI_VOWELS for c in word):
        return False
    return True


def normalise_for_match(s: str) -> str:
    """Strip macrons + lowercase for dictionary lookup."""
    table = str.maketrans("ĀĒĪŌŪāēīōū", "AEIOUaeiou")
    return s.translate(table).lower()


def find_line(text_fragments: list[tuple[int, str]], needle: str) -> int:
    """Return the source line number where 'needle' first appears in any fragment."""
    for line, frag in text_fragments:
        if needle in frag:
            return line
    return 0


# ---------- Lint rules ----------


def lint_missing_macrons(report: FileReport, fragments: list[tuple[int, str]], glossary: dict) -> None:
    """Flag words that match a known macron-required word in its unmacroned form."""
    macron_dict = {k: v for k, v in glossary["macrons"].items() if not k.startswith("_")}
    false_friends = {k for k in glossary["false_friends"] if not k.startswith("_")}

    # Build a reverse lookup keyed by unmacroned-lowercase form
    needs_macron: dict[str, str] = {}
    for unmac, mac in macron_dict.items():
        needs_macron[normalise_for_match(unmac)] = mac

    seen_at: set[tuple[int, str]] = set()  # dedupe (line, word)

    for line, frag in fragments:
        for m in WORD_RE.finditer(frag):
            word = m.group(0)
            wl = word.lower()
            if wl in false_friends:
                continue
            # Skip if this token already contains any macron — we never suggest removing macrons.
            if any(c in "ĀĒĪŌŪāēīōū" for c in word):
                continue
            key = normalise_for_match(word)
            if key in needs_macron:
                target = needs_macron[key]
                # Identity-mapping (no macron needed at all)? Skip.
                if normalise_for_match(target) == target.lower():
                    continue
                # Already correct? Skip.
                if word == target or word.lower() == target.lower():
                    continue
                # Real macron miss
                dedupe_key = (line, word)
                if dedupe_key in seen_at:
                    continue
                seen_at.add(dedupe_key)
                report.flags.append(
                    Flag(
                        file=report.path,
                        line=line,
                        severity=SEVERITY_HIGH,
                        category="missing-macron",
                        snippet=word,
                        message=f"'{word}' is likely missing macron(s)",
                        suggestion=target,
                    )
                )


def lint_untranslated_english(report: FileReport, fragments: list[tuple[int, str]], glossary: dict) -> None:
    """For -mi.html files, flag sentences that contain no Māori words at all (likely missed translation)."""
    if not report.path.endswith("-mi.html"):
        return
    if report.lang and report.lang.lower() not in ("mi", "mi-nz"):
        # Already explicitly tagged as another language, skip
        return

    keep_english = set(glossary["english_only_keep"]["items"])
    keep_lower = {x.lower() for x in keep_english}

    macron_dict = {normalise_for_match(k) for k in glossary["macrons"] if not k.startswith("_")}
    macron_dict |= {normalise_for_match(v) for v in glossary["macrons"].values() if isinstance(v, str)}

    # Build a small list of common te reo function words to spot Māori-ness without needing the full dict
    function_words = {
        "te", "ngā", "nga", "he", "ko", "ka", "kua", "kei", "i", "a", "o", "no",
        "mō", "mo", "me", "ai", "anō", "ano", "rā", "ra", "ki", "tā", "tō", "to", "ta",
        "ana", "ai", "rānei", "ranei", "tērā", "tera", "tēnei", "tenei",
    }

    # Known multilingual section markers — the AI Warrior site has Tagalog, Spanish, etc. social-kit sections.
    # Once we see one of these on a line, skip flagging the next ~30 fragments as 'untranslated English'.
    OTHER_LANG_MARKERS = re.compile(r"\b(Tagalog|Español|Spanish|Mandarin|中文|Hindi|Samoan|Tongan|French|Français|Bahasa|Vietnamese|Russian|Arabic|Korean|한국어|Japanese|日本語)\b")
    other_lang_zone_until = -1

    # Group fragments by line, then check each one.
    for line, frag in fragments:
        if OTHER_LANG_MARKERS.search(frag):
            # Suppress flags for the next chunk of the document — this is a deliberately non-reo section.
            other_lang_zone_until = line + 200
            continue
        if line <= other_lang_zone_until:
            continue
        sentence = frag.strip()
        if len(sentence) < 25:
            continue
        words = [w for w in WORD_RE.findall(sentence) if len(w) >= 2]
        if not words:
            continue
        # Strip whitelisted English (proper nouns)
        words_filtered = [w for w in words if w.lower() not in keep_lower]
        if not words_filtered:
            continue
        reo_hits = 0
        for w in words_filtered:
            wl = w.lower()
            if wl in function_words:
                reo_hits += 1
            elif normalise_for_match(w) in macron_dict:
                reo_hits += 1
            elif "ā" in w or "ē" in w or "ī" in w or "ō" in w or "ū" in w:
                reo_hits += 1
        # If a long-ish sentence has 0 Māori signal, flag it
        if reo_hits == 0 and len(words_filtered) >= 5:
            report.flags.append(
                Flag(
                    file=report.path,
                    line=line,
                    severity=SEVERITY_MEDIUM,
                    category="untranslated-english",
                    snippet=sentence[:140] + ("…" if len(sentence) > 140 else ""),
                    message="Sentence appears entirely English on a te reo page — likely needs translation",
                    suggestion="",
                )
            )


def lint_iwi_capitalisation(report: FileReport, fragments: list[tuple[int, str]], glossary: dict) -> None:
    """Flag iwi names that appear unmacroned or uncapitalised."""
    iwi = glossary["iwi_proper_nouns"]
    for canonical, variants in iwi.items():
        if canonical.startswith("_"):
            continue
        for variant in variants:
            pattern = re.compile(r"\b" + re.escape(variant) + r"\b")
            for line, frag in fragments:
                if pattern.search(frag):
                    report.flags.append(
                        Flag(
                            file=report.path,
                            line=line,
                            severity=SEVERITY_HIGH,
                            category="iwi-capitalisation",
                            snippet=variant,
                            message=f"Iwi name '{variant}' should be written as '{canonical}'",
                            suggestion=canonical,
                        )
                    )


def lint_terminology_consistency(reports: list[FileReport], glossary: dict) -> dict[str, list[tuple[str, int]]]:
    """Cross-file: when the same English glossary term is rendered different ways, flag the drift.

    Returns a dict mapping `english_term -> [(rendering, count), ...]` for the PR comment.
    """
    # This is a heuristic — we look for the canonical te reo rendering AND any near-variants.
    drift: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    canon = {k: v for k, v in glossary["glossary"].items() if not k.startswith("_")}
    if not canon:
        return {}

    # Build a search pattern for each canonical rendering (and trivial variants — case, macron-stripped)
    for report in reports:
        if not report.path.endswith("-mi.html"):
            continue
        with open(report.path, "r", encoding="utf-8") as fp:
            text = fp.read()
        for en_term, canonical_mi in canon.items():
            if not canonical_mi:
                continue
            # Canonical match
            if canonical_mi in text:
                drift[en_term][canonical_mi] += text.count(canonical_mi)
            # Macron-stripped variant of the canonical
            stripped = normalise_for_match(canonical_mi)
            if stripped != canonical_mi.lower() and re.search(r"\b" + re.escape(stripped) + r"\b", text, re.IGNORECASE):
                drift[en_term][stripped] += 1

    out: dict[str, list[tuple[str, int]]] = {}
    for en_term, renderings in drift.items():
        if len(renderings) > 1:
            out[en_term] = sorted(renderings.items(), key=lambda kv: -kv[1])
    return out


# ---------- Reporting ----------


def score_file(report: FileReport) -> int:
    """0-100. Starts at 100, subtract weighted penalties, never below 0."""
    if not report.flags:
        return 100
    penalty = sum(SEVERITY_WEIGHTS[f.severity] for f in report.flags)
    # Normalise against file size — a long file with 10 flags is better than a short one with 10
    fragments_factor = max(20, report.word_count_total)
    score = 100 - int((penalty * 100) / fragments_factor)
    return max(0, min(100, score))


def render_markdown(reports: list[FileReport], drift: dict[str, list[tuple[str, int]]]) -> str:
    lines: list[str] = []
    lines.append("## 🪶 Te reo Māori lint report\n")
    lines.append(
        "Automated first-pass triage. Every flag is a candidate for native-speaker review, "
        "not a verdict. The kaupapa is to surface lines worth a kaiako's eye.\n"
    )

    total_flags = sum(len(r.flags) for r in reports)
    if not reports:
        lines.append("_No HTML files were checked._")
        return "\n".join(lines)

    # Header table
    lines.append("### Summary\n")
    lines.append("| File | Score | High | Medium | Low | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    overall_score = 0
    for r in reports:
        sev_counts = defaultdict(int)
        for f in r.flags:
            sev_counts[f.severity] += 1
        score = score_file(r)
        overall_score += score
        lines.append(
            f"| `{r.path}` | **{score}/100** | {sev_counts[SEVERITY_HIGH]} | "
            f"{sev_counts[SEVERITY_MEDIUM]} | {sev_counts[SEVERITY_LOW]} | {len(r.flags)} |"
        )
    if reports:
        overall_score = overall_score // len(reports)
    lines.append(f"\n**Overall score:** **{overall_score}/100** across {len(reports)} file(s), {total_flags} flag(s).\n")

    # Per-file details
    for r in reports:
        if not r.flags:
            lines.append(f"### `{r.path}` — clean ✅\n")
            continue
        lines.append(f"### `{r.path}`\n")
        # Group by category
        by_cat: dict[str, list[Flag]] = defaultdict(list)
        for f in r.flags:
            by_cat[f.category].append(f)
        for cat, flags in by_cat.items():
            sev = flags[0].severity
            emoji = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(sev, "•")
            lines.append(f"#### {emoji} {cat.replace('-', ' ')} ({len(flags)})\n")
            # Show up to 15 per category to keep the comment readable
            shown = flags[:15]
            lines.append("| Line | Found | Suggested | Note |")
            lines.append("|---:|---|---|---|")
            for f in shown:
                snippet = f.snippet.replace("|", "\\|")
                suggestion = (f.suggestion or "—").replace("|", "\\|")
                message = f.message.replace("|", "\\|")
                lines.append(f"| {f.line} | `{snippet}` | `{suggestion}` | {message} |")
            if len(flags) > 15:
                lines.append(f"\n_… and {len(flags) - 15} more in this category._\n")
            lines.append("")

    # Terminology drift
    if drift:
        lines.append("### ⚠️ Terminology drift across files\n")
        lines.append("The same English term has been rendered different ways across the te reo pages. Pick one canonical form and align the rest.\n")
        lines.append("| English | Renderings found |")
        lines.append("|---|---|")
        for en, renderings in drift.items():
            rendered = ", ".join(f"`{r}` ({c})" for r, c in renderings)
            lines.append(f"| **{en}** | {rendered} |")
        lines.append("")

    # Native-speaker review list
    needs_review = [f for r in reports for f in r.flags if f.severity in (SEVERITY_MEDIUM, SEVERITY_LOW)]
    if needs_review:
        lines.append("### 👁️ Needs native-speaker review\n")
        lines.append("These flags are lower-confidence — the linter wants a kaiako's eye, not a fix.\n")
        for f in needs_review[:25]:
            lines.append(f"- **`{f.file}:{f.line}`** — {f.message}: `{f.snippet}`")
        if len(needs_review) > 25:
            lines.append(f"\n_… and {len(needs_review) - 25} more._\n")
        lines.append("")

    lines.append("---")
    lines.append(
        "_Generated by [`scripts/reo-lint.py`](scripts/reo-lint.py) against "
        "[`scripts/reo-glossary.json`](scripts/reo-glossary.json). "
        "Run locally: `python scripts/reo-lint.py <file>`. "
        "Improve the linter by PRing changes to the glossary._"
    )
    return "\n".join(lines)


def render_text(reports: list[FileReport], drift: dict[str, list[tuple[str, int]]]) -> str:
    out: list[str] = []
    out.append("Te reo Māori lint report")
    out.append("=" * 40)
    total = sum(len(r.flags) for r in reports)
    out.append(f"{len(reports)} file(s), {total} flag(s)\n")
    for r in reports:
        score = score_file(r)
        out.append(f"{r.path}  score={score}/100  flags={len(r.flags)}")
        for f in r.flags:
            out.append(f"  [{f.severity:6}] L{f.line}: {f.message}  ({f.snippet} → {f.suggestion or '?'})")
        out.append("")
    if drift:
        out.append("Terminology drift:")
        for en, renderings in drift.items():
            out.append(f"  {en}: " + ", ".join(f"{r}({c})" for r, c in renderings))
    return "\n".join(out)


# ---------- File discovery ----------


def _is_reo_html(path: Path) -> bool:
    """True if the file is a te reo Māori page (by filename convention or lang attr)."""
    name = path.name.lower()
    if name.endswith("-mi.html") or name == "index-mi.html":
        return True
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fp:
            head = fp.read(2048)
    except OSError:
        return False
    return bool(re.search(r'<html[^>]*\blang\s*=\s*"mi"', head, re.IGNORECASE))


def changed_html_files(base_ref: str) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"],
            capture_output=True, text=True, check=True, cwd=str(ROOT),
        )
    except subprocess.CalledProcessError as e:
        print(f"git diff failed: {e.stderr}", file=sys.stderr)
        return []
    files = [Path(ROOT / line.strip()) for line in result.stdout.splitlines() if line.strip().endswith(".html")]
    return [f for f in files if f.exists() and _is_reo_html(f)]


# ---------- Main ----------


def lint_file(path: Path, glossary: dict) -> FileReport:
    with open(path, "r", encoding="utf-8") as fp:
        html = fp.read()
    fragments, lang = extract_text(html)
    rel = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    report = FileReport(path=rel, lang=lang)
    total_words = sum(len(WORD_RE.findall(frag)) for _, frag in fragments)
    report.word_count_total = total_words

    lint_missing_macrons(report, fragments, glossary)
    lint_iwi_capitalisation(report, fragments, glossary)
    lint_untranslated_english(report, fragments, glossary)

    # Dedupe identical (line, category, snippet)
    seen: set[tuple[int, str, str]] = set()
    deduped: list[Flag] = []
    for f in report.flags:
        key = (f.line, f.category, f.snippet)
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    report.flags = deduped
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="Files to lint (default: all *-mi.html)")
    parser.add_argument("--changed", help="Lint files changed vs the given git ref (e.g. origin/main)")
    parser.add_argument("--pr-comment", action="store_true", help="Output as a markdown PR comment")
    parser.add_argument("--output", help="Write output to a file instead of stdout")
    parser.add_argument("--fail-on", choices=["high", "medium", "low", "never"], default="never",
                        help="Exit with non-zero if a flag at or above this severity is found")
    args = parser.parse_args()

    glossary = load_glossary()

    # Resolve files
    files: list[Path] = []
    used_changed_mode = False
    if args.changed:
        files = changed_html_files(args.changed)
        used_changed_mode = True
    if args.files:
        files.extend(Path(f).resolve() for f in args.files)
    if not files and not used_changed_mode:
        # default: all -mi.html under repo root
        files = sorted((ROOT).glob("*-mi.html"))

    files = [f for f in files if f.exists() and f.suffix == ".html"]
    if not files:
        msg = "No HTML files to lint."
        if args.pr_comment:
            print("## 🪶 Te reo Māori lint report\n\n_No te reo HTML files changed in this PR._")
        else:
            print(msg)
        return 0

    reports = [lint_file(p, glossary) for p in files]
    drift = lint_terminology_consistency(reports, glossary)

    output = render_markdown(reports, drift) if args.pr_comment else render_text(reports, drift)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    # Exit code
    if args.fail_on != "never":
        thresholds = {"high": [SEVERITY_HIGH], "medium": [SEVERITY_HIGH, SEVERITY_MEDIUM],
                      "low": [SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW]}
        block = thresholds[args.fail_on]
        for r in reports:
            for f in r.flags:
                if f.severity in block:
                    return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
