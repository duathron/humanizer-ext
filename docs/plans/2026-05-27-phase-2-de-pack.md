# Phase 2 Implementation Plan — DE Pack (v3.5.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship full German pattern + override pack + DE eval corpus + DE career register, hitting pattern eval ≥ 0.70 (relaxed from 0.85 EN target given Phase 2 is the first language extension), FP edit ratio ≤ 0.15, E2E per-case meaning ≥ 8.0 on all DE domains × 3 runs.

**Architecture:** Adds `patterns/de.md` + `domains/de_overrides.md` + `evals/corpus/de/{patterns,human,e2e}/` + `regex_scorer.PATTERNS_DE` registry entry. Framework (`SKILL.md`) needs zero changes — language detection + per-language pack loading was wired in v3.3.0. New script `evals/scripts/mine_patterns.py` produces candidate patterns from corpus diffs (TF-IDF + log-likelihood-ratio).

**Tech Stack:** Python 3.11+ stdlib + `rapidfuzz` (already a dep) + `requests` (new dep for Wikipedia API + Project Gutenberg fetcher) + `anthropic` SDK (already a dep) + claude CLI for skill invocation. Optional: `openai` SDK + `google-generativeai` SDK for multi-model AI corpus generation.

**Reference spec:** `docs/specs/2026-05-23-humanizer-eval-de-design.md` (locked at v3.3.0 + v3.4.0 + v3.4.1 ship).

**Reference source authority (per saved memory):** [Wikipedia:Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte) (DE seed catalogue).

**Budget:** ~**$0 API spend** for corpus generation (revised from initial $45 estimate — see Task 4 refactor below for the zero-budget approach). ~$5 reserved for E2E judge SDK calls in Task 11. Pro plan subscription for skill CLI calls (free).

**Effort estimate:** 2-3 weeks of focused work split across ~5 sessions. Subagent-driven dispatch keeps Opus context light.

---

## Task 0: Spec refresh + worktree

**Files:**
- Read: `docs/specs/2026-05-23-humanizer-eval-de-design.md`
- Read: `docs/plans/2026-05-23-phase-0-skill-refactor.md`, `2026-05-24-phase-1-eval-infrastructure.md`
- Create: `.claude/worktrees/v3.5.0-de-pack/` (via `EnterWorktree` native tool)

- [ ] **Step 1:** Re-read the existing spec end-to-end. Flag anything that drifted during v3.4.x work (e.g., spec mentions "framework + 5 domains" but we now have 6 with career). If material drift found, update spec inline with a "Drift correction 2026-05-27" note.
- [ ] **Step 2:** Verify reference URL still resolves: `WebFetch https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte`. If 404 / moved, use `WebSearch site:de.wikipedia.org anzeichen ki-generierter inhalte` per saved memory `feedback-url-search-via-search-engine`.
- [ ] **Step 3:** Create `v3.5.0-de-pack` worktree via `EnterWorktree` native tool. Verify baseline: `python3 -m pytest -q` should report 78/78 pass.
- [ ] **Step 4:** Commit worktree setup if any spec drift corrections were made.

---

## Task 1: DE Wikipedia seed catalogue extraction (Phase A)

**Files:**
- Create: `docs/de-seed-catalogue.md`
- Reference: the DE Wikipedia AI-cleanup guide (fetched at run time)

- [ ] **Step 1:** Dispatch a `general-purpose` Sonnet subagent to fetch + summarize the DE Wikipedia AI-cleanup guide. Extract: (a) every named AI tell with example, (b) suggested fix patterns, (c) any DE-specific tells that differ from EN (e.g., "im Rahmen von", "es lässt sich festhalten", "sowie", "vielfältig", "verschiedenartig", "facettenreich", "Anzeichen für", "stellt einen wichtigen Beitrag dar"). Write findings to `docs/de-seed-catalogue.md`.
- [ ] **Step 2:** Cross-reference each DE tell against our existing EN pack:
  - Universal tells (em dash / boldface / emojis / curly quotes / artifacts) → already covered by `patterns/_universal.md` — no DE-specific entry needed
  - Tells with EN equivalent (#7 AI vocabulary, #20 chatbot artifacts, #22 sycophancy) → DE versions go in `patterns/de.md` under same pattern numbers
  - DE-only tells (no EN equivalent) → DE versions go in `patterns/de.md` under pattern IDs **#100+** per spec convention
- [ ] **Step 3:** Commit `docs/de-seed-catalogue.md`.

---

## Task 2: `evals/scripts/mine_patterns.py` script

**Files:**
- Create: `evals/scripts/mine_patterns.py`
- Test: `tests/test_mine_patterns.py`

- [ ] **Step 1: Write the failing test** in `tests/test_mine_patterns.py`:

```python
def test_mine_patterns_extracts_diff_signal():
    """Mining AI-vs-human corpus returns ranked candidate ngrams."""
    from evals.scripts.mine_patterns import mine
    ai_corpus = ["Im Rahmen von KI gestützten Systemen", "Es lässt sich festhalten, dass"]
    human_corpus = ["Künstliche Intelligenz lernt aus Daten.", "Forscher untersuchten den Effekt."]
    candidates = mine(ai_corpus, human_corpus, min_n=2, max_n=4, top_k=10)
    assert any("im rahmen" in c.ngram.lower() for c in candidates)
    assert all(c.llr > 0 for c in candidates)
```

- [ ] **Step 2:** Implement minimal `mine()` using:
  - Tokenization (whitespace + punctuation stripping, language-agnostic)
  - N-gram extraction (configurable `min_n`, `max_n`)
  - Per-ngram counts in both corpora
  - Log-likelihood ratio (LLR) per Dunning 1993 (standard statistical-NLP measure)
  - Return top-k by LLR with positive sign (ngram favors AI corpus)
- [ ] **Step 3:** Run test. Expect PASS.
- [ ] **Step 4:** Add CLI: `python -m evals.scripts.mine_patterns --ai-corpus PATH --human-corpus PATH --lang de --top 50 > candidates.txt`
- [ ] **Step 5:** Commit: "feat(evals): add `mine_patterns.py` for empirical pattern discovery (Phase 2.B prep)"

---

## Task 3: DE human corpus assembly — per-domain real sources

**Goal (revised 2026-05-27 per session /goal "find more human corpus resources for each domain and synthesize as little as possible"):** assemble real-world DE human corpus with per-domain source mapping. Synthetic samples reduced to fallback role — only used where no licensed real-world source exists for a domain.

**Per-domain source map (all $0, all clear-license, all pre-2022 where applicable for AI-contamination safety):**

| Domain | Primary source | License | Why suited |
|--------|----------------|---------|------------|
| **casual** | Wikipedia DE talk pages + project namespace (Wikipedia:, Diskussion:) pre-2022 | CC-BY-SA | Informal register, opinion, varied rhythm — same register profile as blog prose |
| **casual (supplement)** | DE Wikisource autobiographies / personal letters / memoirs (PD pre-1923) | PD | First-person, register variety |
| **academic** | SSOAR (Social Science Open Access Repository — DE social science papers) | CC-BY (most) | Real academic prose, hedging + passive, citation register. URL: `https://www.ssoar.info/` |
| **academic (supplement)** | DNB DE-language open-access dissertations + habilitations | varies (mostly CC) | Real thesis / paper prose |
| **legal** | Bundesgesetzblatt (BGBl) — federal laws | PD per §5 UrhG | Real legal register, shall/may/notwithstanding equivalents |
| **legal (supplement)** | Rechtsprechung-im-Internet — federal court decisions | PD per §5 UrhG | Brief-style prose. URL: `https://www.rechtsprechung-im-internet.de/` |
| **legal (supplement)** | Bundestag plenary protocols (Plenarprotokolle) — parliamentary speeches | PD per §5 UrhG | Formal speech register adjacent to legal. URL: `https://www.bundestag.de/services/opendata` |
| **technical** | ubuntuusers.de Wiki articles pre-2022 | CC-BY-SA | Real DE technical documentation, command-line + step-by-step register. URL: `https://wiki.ubuntuusers.de/` |
| **technical (supplement)** | translatewiki.net DE-translated FOSS software UI strings + docs | various FOSS-compatible | Tech vocabulary, imperative mood. URL: `https://translatewiki.net/wiki/Special:LanguageStats?language=de` |
| **technical (supplement)** | Linuxwiki.de articles + DE man page translations | GFDL / LGPL | Reference-style technical prose |
| **marketing** | Wikipedia DE articles about commercial products + brand launches pre-2022 | CC-BY-SA | Product-positioning prose, feature-focused encyclopedic style. Filter for product / brand / app categories. Best real-world DE marketing-adjacent register available under clear license. |
| **marketing (supplement)** | GitHub READMEs of major DE-language open-source products | MIT / Apache / GPL (per repo) | First-party product marketing copy by definition — READMEs are self-promotion. Tech-marketing register. Filter for repos with German README content (search GitHub for `language:Markdown stars:>100` + DE filter). |
| **marketing (supplement)** | Startnext.com (DE crowdfunding) campaign descriptions pre-2022 | per-campaign (often permissive) | Real product-launch copy at small-business scale — features, audience hook, CTA. Per-page license check; many campaigns explicitly grant reuse. URL: `https://www.startnext.com/` |
| **marketing (supplement)** | Wikipedia DE Wirtschaft / Marken / Werbung articles pre-2022 | CC-BY-SA | Brand-history articles with positioning excerpts (often quoted marketing copy + analysis) |
| **career** | Wikipedia DE Lebensläufe of public figures pre-2022 (politicians / executives / academics / authors) | CC-BY-SA | Real DE career-narrative prose at the third-person remove — "X studierte in Y, arbeitete bei Z, leitet seit 20XX W". Mirror of the register a humanized first-person Lebenslauf should land. Diverse seniority + industry coverage. |
| **career (supplement)** | Bundesregierung.de Lebensläufe of ministers + Staatssekretäre | PD per §5 UrhG | Official factual career biographies. Concise, formal-modest DE register (the opposite of US/UK puffery — exactly the register DE Anschreiben should aim for). |
| **career (supplement)** | GitHub DE profile README files (`<user>/<user>` repos with DE-language content) | typically MIT / per-repo | First-person developer self-positioning — tech stack + role + interests. Real-world DE engineering career voice. |
| **career (supplement)** | Stack Exchange DE user "About me" profile sections | CC-BY-SA | Professional self-description, technical-domain DE. Verbose but authentic. |
| **career (supplement)** | DE faculty `<chair>/personen/<professor>` pages on university websites | per-uni (often PD per §5 if civil servant; per-page check) | Real academic career CV prose, more detailed than Wikipedia bio summaries |

**Files:**
- Create: `evals/scripts/fetch_de_human_corpus.py` — multi-source fetcher (one function per source category)
- Create: `evals/corpus/de/human/wikipedia_de_pre2022/` (general encyclopedic)
- Create: `evals/corpus/de/human/wikisource_de/` (literary + personal-letter PD)
- Create: `evals/corpus/de/human/gutenberg_de/` (PD literary)
- Create: `evals/corpus/de/human/ssoar_academic/` (academic)
- Create: `evals/corpus/de/human/dnb_dissertations/` (academic supplement; optional, larger fetch)
- Create: `evals/corpus/de/human/bgbl_legal/` (legal)
- Create: `evals/corpus/de/human/rechtsprechung_legal/` (legal supplement)
- Create: `evals/corpus/de/human/bundestag_protocols/` (legal/speech supplement; optional)
- Create: `evals/corpus/de/human/ubuntuusers_technical/` (technical)
- Create: `evals/corpus/de/human/translatewiki_technical/` (technical supplement)
- Create: `evals/corpus/de/human/wikipedia_marketing/` (Wikipedia DE product/brand articles)
- Create: `evals/corpus/de/human/github_marketing/` (GitHub README files of DE OSS products)
- Create: `evals/corpus/de/human/startnext_marketing/` (DE crowdfunding campaign descriptions)
- Create: `evals/corpus/de/human/wikipedia_lebenslauf_career/` (Wikipedia DE bios of public figures)
- Create: `evals/corpus/de/human/bundesregierung_career/` (federal minister Lebensläufe)
- Create: `evals/corpus/de/human/github_profile_career/` (GitHub DE profile READMEs)
- Create: `evals/corpus/de/human/synthetic/` — **fallback only** for any domain where the real-world fetcher fails or produces < 3 usable samples after manual quality check. Synthetic count target: **0 if all fetchers succeed; ≤1 per domain otherwise**.
- Create: per-source `_LICENSE` + `_SOURCE` sidecars (license string + URL + fetch date + access conditions)

**Steps:**

- [ ] **Step 1:** Implement `fetch_de_human_corpus.py` with one function per primary source. Schema for each function:
  ```python
  def fetch_<source>() -> list[Document]:
      """Fetch ~5-10 documents from <source>. Returns Document(id, text, license, source_url, fetch_date)."""
  ```
  - `fetch_wikipedia_de_pre2022(n=15)` — Wikipedia DE revisions API, `rvend=2022-11-30T00:00:00Z`, fixed random seed for reproducibility
  - `fetch_wikisource_de(n=10)` — Wikisource API (same MediaWiki schema) limited to PD content
  - `fetch_gutenberg_de(n=10)` — `https://www.projekt-gutenberg.org/` index scrape + author/title sampling
  - `fetch_ssoar_academic(n=10)` — SSOAR OAI-PMH endpoint or REST search API
  - `fetch_bgbl_legal(n=8)` — BGBl bulk download / RSS feed
  - `fetch_ubuntuusers_technical(n=10)` — ubuntuusers.de MediaWiki API (it runs on MediaWiki)
  - `fetch_wikipedia_marketing(n=10)` — Wikipedia DE category fetch (e.g., `Kategorie:Markenname`, `Kategorie:Smartphone`, `Kategorie:Softwareprodukt`) → article body excerpts pre-2022
  - `fetch_github_marketing(n=8)` — GitHub API search for repos with DE README content (`q=language:Markdown+stars:>50` + filter README for DE), fetch README.md raw text
  - `fetch_startnext_marketing(n=8)` — Startnext campaign listing scrape → campaign description + features section
  - `fetch_wikipedia_lebenslauf_career(n=10)` — Wikipedia DE Personenartikel via category (e.g., `Kategorie:Deutscher_Unternehmer`, `Kategorie:Hochschullehrer_(Deutschland)`) → bio + career sections pre-2022
  - `fetch_bundesregierung_career(n=8)` — Bundesregierung.de minister Lebenslauf pages → biographical text
  - `fetch_github_profile_career(n=6)` — GitHub API search for `<user>/<user>` profile repos with DE README → first-person developer narrative

- [ ] **Step 2:** Run fetcher. Per file: trim to representative passage (~200-500 words). Total target: **~300 KB raw text** across all 8+ sources (revised up from 150 KB given broader source mix).

- [ ] **Step 3:** Manual quality check: skim 2-3 samples per source category. Flag any that look LLM-tainted (post-2022 Wikipedia edits, press releases mentioning ChatGPT, etc.). Drop tainted samples.

- [ ] **Step 4 (fallback only):** For any domain where real-source fetch produced < 3 usable samples after Step 3 quality check, write **at most 1** synthetic sample per such domain (~150 words). Source field marked `synthesis: opus_inline` with date. Synthetic samples are explicitly marked so FP eval reports can isolate their contribution.

- [ ] **Step 5:** Commit fetched corpus + sidecar `_LICENSE` + `_SOURCE` files + any fallback synthetic samples. Include in commit message a summary: `corpus N=X files Y KB across Z sources, S synthetic fallbacks`.

**Notes:**
- All primary sources are German federal/government (PD per §5 UrhG) OR CC-BY-SA Wikimedia properties OR explicit CC academic repositories. Zero copyright risk for redistribution as eval corpus.
- Per the `feedback-url-search-via-search-engine` saved memory: if any URL guess fails, use `site:domain.de keywords` via WebSearch before retrying. URLs in the table above are all verified entry points but exact API endpoints may need search-engine confirmation per source.
- DNB OAI-PMH + Bundestag opendata are optional supplements; skip if Step 1 implementation effort exceeds plan budget.

---

## Task 4: DE AI corpus assembly (zero-API-spend version)

**Goal:** ~75-100 DE AI samples across 6 domains at $0 cost. Original $45 paid-API plan was scaled back per session-wide /goal "minimize Phase 2 Task 4 budget while preserving pattern-discovery quality" (2026-05-27).

**Files:**
- Create: `evals/scripts/fetch_de_wikipedia_ai_tagged.py` (wraps Wikipedia API, free)
- Create: `evals/scripts/generate_de_ai_corpus_cli.py` (wraps `claude -p` subprocess via subscription, free)
- Create: `evals/corpus/de/ai/wikipedia_tagged/`, `evals/corpus/de/ai/claude_cli/`, `evals/corpus/de/ai/manual_synthesis/` (directories)

**Three free sources, in quality order:**

- [ ] **Step 1 (Source A — Wikipedia DE AI-Cleanup tagged articles, target ~30 samples, $0):**
  - Fetch articles flagged by the DE Wikipedia AI-cleanup project (search categories like `Vorlage:KI-Inhalt`, `Category:Suspected_AI_content_(de)`, or whatever DE convention exists — find via the seed catalogue from Task 1)
  - These are **real-world AI output already human-verified as AI-generated** — best signal possible, better than any synthetic generation
  - Per pattern-eval design principle: signal > volume
  - Implement `fetch_de_wikipedia_ai_tagged.py` using Wikipedia API + category listing + per-page extract
  - Cost: $0

- [ ] **Step 2 (Source B — Claude CLI subscription generation, target ~30 samples, $0):**
  - `claude -p "Schreibe einen typischen KI-generierten Werbetext über [PRODUKT] (~150 Wörter)"` via subscription auth
  - 5 samples per domain × 6 domains = 30 samples
  - Vary the underlying model with `--model sonnet`, `--model haiku`, `--model opus` for cross-model idiolect diversity (all on same subscription, no extra cost)
  - Wrap `claude -p` subprocess in `generate_de_ai_corpus_cli.py` with prompt templates per domain
  - Strip `ANTHROPIC_API_KEY` from subprocess env (per `_shared.run_skill` convention) so subscription auth is used
  - Cost: $0

- [ ] **Step 3 (Source C — Opus main-thread prototypical synthesis, target ~15-20 samples, $0):**
  - Opus (main conversation thread) writes ~3-4 prototypical DE AI samples per domain inline during a Phase 2 session
  - Inspired by the EN `ai_*.json` corpus pattern (we already have 6 prototypical EN samples)
  - These act as "calibration anchors" — they explicitly contain the AI tells we want to detect, so they're useful for pattern eval `--pattern` per-pattern testing
  - No API call required; main-thread tokens are sunk cost
  - Cost: $0

- [ ] **Step 4:** Commit all three corpus subdirectories + the two fetch / generate scripts.

- [ ] **Step 5 (Optional, deferred to v3.6.0 if needed):** If pattern mining quality (Task 5) surfaces too few distinctive DE-specific ngrams, OR if a single-vendor (Anthropic-only) corpus introduces obvious idiolect bias, add Phase 2.2 with a **$5 paid budget**: ~30 GPT samples via OpenAI Batch API (50% discount) + ~10 Gemini samples via Google API. Decision gated on Task 5 mining output, not pre-committed.

**Trade-offs accepted:**
- Loses ~350 samples vs original $45 plan (450 → ~75-100). Statistical power for mining reduced, but: real-world Wikipedia samples are higher quality than synthetic; signal density compensates for volume.
- Loses guaranteed GPT + Gemini cross-vendor diversity at Step 4. Mitigated by: (a) Wikipedia tagged articles likely include GPT output since ChatGPT is the most common AI tool used in the wild; (b) Step 2 model variance (Sonnet vs Haiku vs Opus) provides intra-Anthropic diversity; (c) Step 5 escape hatch if mining suffers.
- Slightly weaker FR/ES/IT extensibility story (no proven multi-vendor pipeline). Acceptable for v3.5.0 since DE pack is the headline; multi-vendor pipeline can land with v4.0 if a true multi-lingual roadmap commits.

---

## Task 5: Empirical pattern mining (Phase B)

**Files:**
- Modify: `docs/de-seed-catalogue.md` — extend with mined candidates
- Create: `evals/reports/mine_de_20260YYMMDD.{json,md}` (report from script)

- [ ] **Step 1:** Run `mine_patterns.py --ai-corpus evals/corpus/de/ai --human-corpus evals/corpus/de/human --lang de --top 100`. Output: ranked candidate ngrams + per-domain breakdown.
- [ ] **Step 2:** Dispatch 3 writer personas in parallel to review the top-100 candidates: Academic, Marketing Copywriter, Journalist (all already in the persona catalogue). Each votes ✓ apply / ✗ skip / ◐ adjust per ngram. Consolidate to "keep" / "drop" list.
- [ ] **Step 3:** Merge surviving mined candidates with the Phase A seed in `docs/de-seed-catalogue.md`. Mark each entry's provenance: SEED / MINED / MANUAL.
- [ ] **Step 4:** Commit updated seed catalogue.

---

## Task 6: `patterns/de.md` curation (Phase C)

**Files:**
- Create: `patterns/de.md` (DE-specific patterns + DE PERSONALITY AND SOUL)
- Modify: `tests/test_skill_structure.py` — add `DE_PATTERN_IDS` set + `test_de_pack_*` tests parallel to EN

- [ ] **Step 1:** Translate every EN pattern from `patterns/en.md` to DE with DE-specific examples. Pattern IDs stay aligned with EN where the underlying tell is the same. Schema per pattern: `### N. <Name>` → trigger words → before / after examples → domain notes.
- [ ] **Step 2:** Add DE-only patterns starting at **#100** for tells with no EN equivalent (e.g., #100 "Substantivketten" / noun-chain stacking, #101 "Genitiv-Aneinanderreihung", #102 DE-specific formulaic phrases).
- [ ] **Step 3:** Add DE PERSONALITY AND SOUL section — DE casual register is different from EN (less first-person assertion expected, "man" vs "ich" considerations). Mirror EN section structure with DE-appropriate guidance.
- [ ] **Step 4:** Update `tests/test_skill_structure.py`:
  - Add `DE_PATTERN_IDS = {...full DE set including #100+...}`
  - Add `test_de_pack_exists()`, `test_de_pack_contains_expected_patterns()`, `test_de_pack_includes_personality_section()`, `test_de_overrides_pattern_ids_exist_in_packs()`
- [ ] **Step 5:** Run pytest. All new tests should pass.
- [ ] **Step 6:** Commit `patterns/de.md` + test updates.

---

## Task 7: `domains/de_overrides.md` + DE career register

**Files:**
- Create: `domains/de_overrides.md`
- Modify: `SKILL.md` (no behavior change, but description may need DE mention if frontmatter gets refreshed)

- [ ] **Step 1:** Translate `domains/en_overrides.md` to DE:
  - Override matrix mirrors EN column structure (academic / legal / technical / marketing / career)
  - Per-domain guidance paragraphs — translate AND adapt for DE register (e.g., DE academic is even more passive-heavy than EN; DE legal uses "vorliegend", "sofern", "insbesondere"; DE marketing uses different superlatives)
- [ ] **Step 2:** Add DE career section with DE-specific register guidance:
  - DE Anschreiben uses formal "Sie" + factual-modest tone (no "passionate about" equivalent — DE equivalent "leidenschaftlich" is overused but more reserved)
  - DE CV uses tabular structure + present-tense for current role
  - DE specific AI tells: "ich freue mich, Sie kennenzulernen", "Mit großem Interesse habe ich Ihre Stellenanzeige gelesen", "Ich bin überzeugt, dass ich genau die richtige Person für diese Position bin"
  - Cultural-register note: this is reverse of EN career — DE Bewerbung culture rewards understatement
- [ ] **Step 3:** Commit `domains/de_overrides.md`.

---

## Task 8: DE pattern eval corpus

**Files:**
- Create: `evals/corpus/de/patterns/pattern_NNN.json` files (one per DE pattern, including #100+)

- [ ] **Step 1:** Dispatch `seed_pattern_corpus.py` adapted for DE (or extend the existing script to accept `--lang` flag) to auto-extract before/after examples from `patterns/de.md` into per-pattern JSON case files.
- [ ] **Step 2:** Manual fill-in for any pattern whose example format doesn't match the seeder regex (per Phase 1 lessons learned).
- [ ] **Step 3:** Apply meetup workflow: dispatch Academic + Wikipedia-AI-Cleanup-Editor + Journalist personas in parallel to vote on each case. Mark scorable / unscorable / true_negative per the v3.4.0 schema.
- [ ] **Step 4:** Target: ~40-50 DE pattern cases. Commit `evals/corpus/de/patterns/`.

---

## Task 9: DE E2E corpus

**Files:**
- Create: `evals/corpus/de/e2e/ai_{casual,academic,legal,technical,marketing,career}_01.json` (6 cases)

- [ ] **Step 1:** Write 6 prototypical AI-generated DE texts (one per domain). Each ~150-200 words. Career = DE Anschreiben format (Sehr geehrte Damen und Herren, ... mit großem Interesse ...).
- [ ] **Step 2:** Commit DE E2E cases.

---

## Task 10: `regex_scorer.PATTERNS_DE` + registry

**Files:**
- Modify: `evals/scripts/regex_scorer.py`

- [ ] **Step 1:** Add `PATTERNS_DE` dict with regex patterns covering the most reliable DE AI tells (subset of `patterns/de.md` that admit clean regex). Aim for ~15-20 entries (similar density to `PATTERNS_EN`).
- [ ] **Step 2:** Register in `PATTERNS_BY_LANG`: `PATTERNS_BY_LANG = {"en": PATTERNS_EN, "de": PATTERNS_DE}`.
- [ ] **Step 3:** Extend `tests/test_regex_scorer.py` — add ~10 DE-specific tests mirroring EN test structure.
- [ ] **Step 4:** Run `python -m evals.scripts.regex_audit --lang de --audit human` to confirm DE regex doesn't over-fire on human samples (target: all human samples in LOW band).
- [ ] **Step 5:** Commit.

---

## Task 11: DE baseline runs

**Files:**
- Create: `evals/reports/{pattern,false_positive,e2e}_de_*.{json,md}`
- Modify: `evals/reports/summary_latest_de.md` (new)

- [ ] **Step 1:** Run pattern eval: `PYTHONPATH=. python3 evals/scripts/run_pattern_eval.py --lang de`. Wall ~30 min. Target ≥ 0.70 (relaxed from EN 0.85 since this is first DE iteration).
- [ ] **Step 2:** Run FP eval: `python3 evals/scripts/run_false_positive_eval.py --lang de`. Target edit ratio ≤ 0.15.
- [ ] **Step 3:** Run E2E in batched sessions (6 cases × 3 runs = ~36 API calls; can batch 2 cases at a time via `--cases` flag if Pro session limit hits). Target per-case meaning ≥ 8.0 on all 6 domains.
- [ ] **Step 4:** Aggregate → write `summary_latest_de.md` parallel to EN.
- [ ] **Step 5:** Commit baseline reports.

---

## Task 12: Iterate to targets

**Files:**
- Modify: `patterns/de.md`, `domains/de_overrides.md`, `SKILL.md` (only if framework-level rule needs adjustment)

- [ ] **Step 1:** If pattern eval < 0.70: identify weak patterns from per-pattern table → refine wording or add examples. Re-run targeted patterns via `--pattern <id>` flag.
- [ ] **Step 2:** If FP > 0.15: investigate which patterns over-fire on DE human samples → soften via domain overrides or tighten conditions.
- [ ] **Step 3:** If E2E meaning < 8.0 per-case: apply the Phase 1 round-1 + round-2 methodology — meaning-preservation rules likely apply identically to DE; the EN versions in `SKILL.md` + `patterns/en.md` PERSONALITY are language-agnostic (universal).
- [ ] **Step 4:** Iterate until targets met. Each iteration: one focused fix → re-run only the affected eval slice → commit.

---

## Task 13: README + docs update

**Files:**
- Modify: `README.md` — add DE to feature list + add v3.5.0 Version History entry
- Modify: `SKILL.md` — frontmatter description must mention German support + DE Anschreiben support
- Modify: `evals/README.md` — verify the add-a-language-pack recipe matches what we actually did; refine where it drifted

- [ ] **Step 1:** Update README "What's different from upstream" table with DE row.
- [ ] **Step 2:** Bump SKILL.md frontmatter to v3.5.0 + refresh description.
- [ ] **Step 3:** Update `.claude-plugin/plugin.json` + `marketplace.json` to v3.5.0 + DE description (per the v3.4.2-established release-manifest-sync rule — dispatch via `vault-status-updater` agent).
- [ ] **Step 4:** Add v3.5.0 Version History entry to README.
- [ ] **Step 5:** Commit.

---

## Task 14: Vault sync + ship v3.5.0

**Files:**
- Vault docs (via Sonnet doc-agent trio): STATUS.md, SESSION_LOG.md, DECISIONS.md
- Tag + push + GH release

- [ ] **Step 1:** Dispatch 3 Sonnet doc agents in parallel (STATUS / SESSION_LOG / DECISIONS) with v3.5.0 ship payload.
- [ ] **Step 2:** Tag v3.5.0 locally with annotated message; verify SKILL.md frontmatter version matches.
- [ ] **Step 3:** Confirm with user before pushing: per CLAUDE.md tagging convention, push only on explicit OK.
- [ ] **Step 4:** Push `main` + `v3.5.0` to origin.
- [ ] **Step 5:** `gh release create v3.5.0 --title "v3.5.0 — DE pack + DE career register" --notes-file <commit msg path>`.
- [ ] **Step 6:** Update vault `WORKFLOW.md` if any new workflow patterns emerged (e.g., mine-then-meetup workflow for adding a language).

---

## Acceptance Criteria

A v3.5.0 release ships only when ALL of these hold:

- [ ] `patterns/de.md` exists + passes `test_de_pack_contains_expected_patterns`
- [ ] `domains/de_overrides.md` exists + passes `test_de_overrides_*` tests + covers all 6 domains including career
- [ ] `evals/corpus/de/{patterns,human,e2e}/` populated
- [ ] `regex_scorer.PATTERNS_DE` registered in `PATTERNS_BY_LANG`
- [ ] DE pattern eval ≥ 0.70 (relaxed Phase-2 target; EN at 0.85 is post-iteration mature state)
- [ ] DE FP edit ratio ≤ 0.15
- [ ] DE E2E per-case meaning ≥ 8.0 on all 6 domain cases
- [ ] EN baselines NOT regressed (re-run EN pattern + FP + E2E to confirm DE pack addition doesn't bleed into EN runtime — should be byte-equivalent since detection chooses the right pack)
- [ ] All pytest tests pass
- [ ] All 3 release manifest files (SKILL.md frontmatter + `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`) at v3.5.0 with refreshed descriptions
- [ ] README v3.5.0 entry + vault docs trio updated
- [ ] Tag pushed to origin + GH release created

---

## Risks + Decision Points

- **DE Wikipedia AI-cleanup guide may be less mature than EN.** Mitigation: Phase A seed can be thinner than EN; lean harder on Phase B mining + Phase C manual curation via persona meetup.
- **AI corpus generation budget.** Original plan was $45. Refactored to $0 per session /goal (Task 4 above) — Wikipedia tagged articles + Claude CLI subscription + Opus main-thread synthesis. Optional $5 escape hatch at Step 5 if mining quality demands GPT/Gemini diversity.
- **Single-vendor idiolect bias.** Zero-budget corpus is Anthropic-heavy (Source B + C). Mitigated by Source A (Wikipedia tagged = real-world, multi-vendor in origin). If mined patterns over-fit Anthropic style, trigger Step 5 escape hatch.
- **DE career register difference.** EN career persona was built for US/UK assertive register. DE register is markedly different (formal, factual-modest). DE career may need a separate persona file or a DE-specific section in the existing one.
- **Per-language pack proliferation.** Each new language re-loads pack files at runtime. Should be fine for 2-3 languages, may need lazy-load or caching if it grows to 10+. Not Phase 2 concern.
- **Pattern numbering #100+ for DE-only.** Must stay consistent across future packs (FR-only would use #200+, ES-only #300+, etc.). Document this in README + `patterns/de.md` header.

---

## Session Breakdown (Suggested)

- **Session 1** (Tasks 0-2, ~3h): Spec refresh + worktree + DE seed catalogue + `mine_patterns.py` ship
- **Session 2** (Tasks 3-4, ~4h, **$0** API spend per refactored plan): DE corpus assembly (human + AI via 3 free sources)
- **Session 3** (Tasks 5-7, ~5h): Pattern mining + meetup + `patterns/de.md` + `domains/de_overrides.md`
- **Session 4** (Tasks 8-11, ~4h + API budget for E2E): DE eval corpus + baseline runs
- **Session 5** (Tasks 12-14, ~3h): Iterate to targets + ship v3.5.0

Total: ~19h focused work + **$0 corpus budget** (~$5 reserved for E2E judge SDK in Task 11). Original $45 plan superseded.
