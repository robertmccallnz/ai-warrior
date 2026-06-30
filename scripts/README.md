# `scripts/` — repo automation

This directory holds repo-level automation scripts that run locally and in CI.

## `reo-lint.py` — te reo Māori QA linter

A first-pass triage tool for te reo Māori HTML pages. It surfaces lines worth a
kaiako's eye — it does **not** make verdicts. Every flag is a candidate for
native-speaker review.

### What it checks

| Category | Severity | Example | What it does |
|---|---|---|---|
| **Missing macrons** | 🔴 high | `kainga` → `kāinga` | Compares words against `reo-glossary.json` macron dictionary. Skips words that already contain any macron, so existing correct forms (e.g. `tāngata`) are not nagged. |
| **Iwi proper nouns** | 🔴 high | `kāi tahu` → `Kāi Tahu` | Iwi, hapū and place names should be capitalised. |
| **Untranslated English** | 🟡 medium | `NZ Council for Educational Research` | Sentences that read as entirely English on a te reo page. Skips zones marked as deliberate multilingual content (Tagalog, Spanish, Mandarin, Sāmoan, Tongan, …). |
| **Terminology drift** | 🟡 medium | `kaiako` vs `pouako` for "teacher" | Cross-file consistency. Flags when a project term has competing translations across pages. |
| **Suggestions** | 🟢 low | Stylistic / glossary hints | Lower-confidence nudges. |

### Scoring

```
score = 100 - (penalty × 100 / max(20, total_words))
weights: high=4, medium=2, low=1
```

Scores are per file and rolled up across the PR. A perfect file is `100/100`.
A score below ~85 is unusual — investigate before merging.

### Running it locally

```bash
# Lint every te reo page in the repo
python scripts/reo-lint.py

# Lint specific files
python scripts/reo-lint.py index-mi.html partners-mi.html

# Lint only what your branch changed vs main
python scripts/reo-lint.py --changed origin/main

# Generate the same markdown the GitHub Action posts
python scripts/reo-lint.py --pr-comment --output /tmp/preview.md

# Fail (non-zero exit) on any high-severity flag — useful for pre-commit hooks
python scripts/reo-lint.py --fail-on high
```

### How the GitHub Action uses it

`.github/workflows/reo-lint.yml` runs on every PR that touches HTML or the
linter itself. It:

1. Fetches the base branch.
2. Runs `reo-lint.py --changed origin/<base> --pr-comment`.
3. Posts (or **updates**) a single comment on the PR keyed by the
   `🪶 Te reo Māori lint report` header — re-runs replace the existing
   comment, they don't spam new ones.
4. The job always succeeds. The linter is advisory; it surfaces issues for
   human review rather than blocking merges. If you want a hard gate, change
   the workflow step to add `--fail-on high`.

### Overriding a flag

The linter is glossary-driven. To silence a flag or teach it a new term, edit
`scripts/reo-glossary.json` — no Python changes needed.

| Want to… | Edit this section |
|---|---|
| Add a word to the macron dictionary | `macron_dictionary` — `{"unmacroned": "macroned"}`. Identity mappings are ignored. |
| Add an iwi / hapū name | `iwi_proper_nouns` — array of strings. Capitalisation is enforced. |
| Lock in a project term | `project_terminology` — `{"english": "te reo"}`. Drives the cross-file consistency check. |
| Keep an English phrase as-is (brand, organisation, citation) | `english_only_keep` — array of substrings. Lines containing any of these are exempt from the "untranslated English" check. |
| Whitelist a known false friend | `false_friends` — array of strings the linter should never flag for macron suggestions. |
| Mark a section as deliberately multilingual | The linter auto-detects this from headings like "Tagalog", "Español", "中文", etc. (200-line suppression window from the heading). If you need a custom language, add it to `multilingual_section_markers` in the glossary. |

### Disagreeing with a flag

The linter is a junior reviewer. If a flag is wrong:

1. **Quick fix** — add the term to the appropriate glossary section above and
   push. The comment will refresh on the next push.
2. **Bug in the linter logic** — open a PR against `scripts/reo-lint.py`. The
   linter is intentionally small (~550 lines, pure stdlib) so it stays easy to
   review and modify.

### What it does **not** do

- It is not a translation oracle. A line scoring 100/100 may still be poor te
  reo. A native speaker's eye is the only gate that matters.
- It does not infer dialect (e.g. Kāi Tahu's `k` for `ng`). The glossary
  encodes the project's chosen forms; if a contributor uses a different valid
  dialect, that's a human discussion, not a lint flag.
- It does not parse JavaScript-rendered content. If a te reo string lives in
  `assets/js/*.js`, add it to the HTML or extend the linter.

---

Last reviewed: 2026-06-30. Maintainer: @robertmccallnz.
