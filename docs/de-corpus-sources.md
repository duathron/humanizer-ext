# DE Human Corpus — Per-Domain Source Registry

**Purpose:** define register-accurate real-world DE text sources per domain for Phase 2 (`v3.5.0`) human corpus assembly. Replaces the first-wave fetcher attempt whose `wikipedia_casual` + `wikipedia_marketing` sub-fetchers returned encyclopedia content at the wrong register.

**License model (per maintainer decision 2026-05-27):** hybrid.

- `evals/corpus/de/human/redistributable/` — CC / PD sources only. Committed to git. Safe for downstream redistribution.
- `evals/corpus/de/human/research_only/` — fair-use research excerpts (~200-300 words per source, attribution required) from copyrighted sources. **Gitignored.** Used locally for mining + FP eval; eval reports cite ngrams + statistics only, not full text. Each `_LICENSE` sidecar states the fair-use claim + attribution + non-redistribution clause.

Mining (`mine_patterns.py`) operates on both subdirectories; output is ngram statistics, which is publication-safe even from research_only sources.

---

## casual — informal first-person opinion / blog register

| Source | URL | License | Subdir |
|--------|-----|---------|--------|
| Travel blogs | https://www.sommertage.com (user example), https://www.fernweh-aktuell.de, https://www.weltreize-traveltipps.de, https://abenteuer-und-reisen.de | copyright | `research_only/travel_blogs_casual/` |
| Lifestyle / entertainment blogs | https://lilies-diary.com, https://journelles.com, https://decogirl.com | copyright | `research_only/lifestyle_blogs_casual/` |
| Reference example: Content Forge guides | https://content-forge-alpha.vercel.app/guides/casual (sample DE casual register) | per-page | `research_only/content_forge_casual/` |
| Wikivoyage DE | https://de.wikivoyage.org/wiki/Hauptseite — destination guides, first-person travel register | CC-BY-SA-3.0 | `redistributable/wikivoyage_casual/` |
| Mastodon DE instances (toot.community, social.tchncs.de) | per-instance | CC0 / CC-BY varies | `redistributable/mastodon_casual/` (only CC0/CC-BY toots) |
| Reddit r/de top posts | https://www.reddit.com/r/de/top/ | per-post (ToS restrictive) | `research_only/reddit_casual/` (small excerpts) |

**Volume target:** ~12 docs total (8 research_only + 4 redistributable).

---

## academic — research register, hedging + passive + citation discipline

| Source | URL | License | Subdir |
|--------|-----|---------|--------|
| SSOAR (Social Science Open Access Repository) | https://www.ssoar.info/ssoar/ — DE social science papers | CC-BY (most) | `redistributable/ssoar_academic/` |
| DNB OpenData DE dissertations | https://www.dnb.de/EN/Professionell/Services/WissenschaftundForschung/DNBLab/dnblab.html | varies (often CC) | `redistributable/dnb_academic/` |
| Wikipedia DE Wissenschafts-Artikel pre-2022 | https://de.wikipedia.org/wiki/Kategorie:Wissenschaft | CC-BY-SA-3.0 | `redistributable/wikipedia_academic/` (already fetched, 8 docs) |
| arXiv DE-language papers (rare; humanities) | https://arxiv.org/ | per-paper (often CC) | optional |

**Volume target:** ~10 docs (5 SSOAR + 8 existing Wikipedia + 2 DNB).

---

## legal — formal precision, hedging mandatory, defined terms

| Source | URL | License | Subdir |
|--------|-----|---------|--------|
| Bundesgesetzblatt (BGBl) federal laws | https://www.recht.bund.de/ | PD per §5 UrhG | `redistributable/bgbl_legal/` |
| Rechtsprechung-im-Internet (court decisions) | https://www.rechtsprechung-im-internet.de/ | PD per §5 UrhG | `redistributable/rechtsprechung_legal/` |
| Bundestag plenary protocols | https://www.bundestag.de/services/opendata | PD per §5 UrhG | `redistributable/bundestag_legal/` |
| Gesetze-im-Internet (consolidated law texts) | https://www.gesetze-im-internet.de/ | PD per §5 UrhG | `redistributable/gesetze_legal/` |

**Volume target:** ~10 docs across 2-3 source types.

---

## technical — docs convention, imperative mood, code-block scaffolding

| Source | URL | License | Subdir |
|--------|-----|---------|--------|
| Linuxwiki.de | https://linuxwiki.de/ | GFDL | `redistributable/linuxwiki_technical/` |
| ubuntuusers.de wiki | https://wiki.ubuntuusers.de/ — needs API URL discovery (first attempt 301'd) | CC-BY-SA-3.0 | `redistributable/ubuntuusers_technical/` |
| Wikipedia DE technical articles | Kategorie:Informatik, Kategorie:Programmiersprache | CC-BY-SA-3.0 | `redistributable/wikipedia_technical/` |
| Heise developer / c't articles | https://www.heise.de/developer/ | copyright | `research_only/heise_technical/` |
| GitHub DE-language project READMEs | https://github.com search topic:deutsch language:Markdown | per-repo (mostly MIT/Apache) | `redistributable/github_oss_technical/` |
| translatewiki.net DE FOSS UI strings | https://translatewiki.net/ | various FOSS-compatible | `redistributable/translatewiki_technical/` |

**Volume target:** ~12 docs across 3-4 source types.

---

## marketing — feature promotion, product positioning, brand voice

| Source | URL | License | Subdir |
|--------|-----|---------|--------|
| Apple DE product pages | https://www.apple.com/de/iphone-17/ (user example), https://www.apple.com/de/macbook-air/, https://www.apple.com/de/ipad-pro/ | copyright | `research_only/apple_marketing/` |
| Samsung DE product pages | https://www.samsung.com/de/smartphones/, https://www.samsung.com/de/tvs/ | copyright | `research_only/samsung_marketing/` |
| Microsoft DE product pages | https://www.microsoft.com/de-de/surface/, https://www.microsoft.com/de-de/microsoft-365/ | copyright | `research_only/microsoft_marketing/` |
| DE startup landing pages (curated list) | e.g., https://www.celonis.com/de/, https://www.personio.com/de/, https://www.n26.com/de-de/ | copyright | `research_only/de_startups_marketing/` |
| Startnext crowdfunding campaign descriptions | https://www.startnext.com/ | per-campaign (often permissive) | `research_only/startnext_marketing/` (license per page) |
| Wikipedia DE Markenartikel (brand articles with quoted positioning copy) | Kategorie:Markenname, Kategorie:Konsumgüter | CC-BY-SA-3.0 | `redistributable/wikipedia_marketing/` (re-targeted from current bad fetch) |

**Volume target:** ~14 docs (10 research_only + 4 redistributable). The 8 currently-fetched wikipedia_marketing docs (historical companies, register mismatch) will be re-targeted to current brand articles with marketing-style "Beschreibung" / "Produktportfolio" sections.

---

## career — calibrated confidence, achievement metrics, formal-modest DE register

| Source | URL | License | Subdir |
|--------|-----|---------|--------|
| Bundesregierung minister Lebensläufe | https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett (each minister's Lebenslauf page) | PD per §5 UrhG | `redistributable/bundesregierung_career/` |
| Wikipedia DE Personenartikel of public figures pre-2022 | already fetched, 8 docs | CC-BY-SA-3.0 | `redistributable/wikipedia_career/` (keep existing) |
| Stack Exchange DE user "About me" sections | https://de.stackoverflow.com/users/, https://stackexchange.com/users/?tab=top (DE users) | CC-BY-SA-4.0 | `redistributable/stackexchange_career/` |
| karrierebibel.de Anschreiben examples | https://karrierebibel.de/anschreiben-muster/ | copyright | `research_only/karrierebibel_career/` |
| bewerbung.com sample Anschreiben + CVs | https://www.bewerbung.com/anschreiben/muster | copyright | `research_only/bewerbung_career/` |
| GitHub DE profile READMEs (`<user>/<user>`) with DE first-person content | github.com user profile repos | per-repo (mostly MIT) | `redistributable/github_profile_career/` |
| University faculty pages | per-university (varies, often PD §5 if civil servants) | varies | `research_only/faculty_career/` (per-page check) |

**Volume target:** ~16 docs (8 redistributable existing + 4 new redistributable + 4 research_only).

---

## Implementation plan

**File:** revise `evals/scripts/fetch_de_human_corpus.py` to:
1. New CLI: `--target redistributable|research_only|all`
2. Re-organize output paths under `redistributable/` or `research_only/` per source
3. Add new fetchers per source category above (one function per row in the tables)
4. Each source category emits per-doc YAML frontmatter with explicit `license_class: redistributable|research_only` field
5. Each `_LICENSE` sidecar includes attribution, source URL, fetch date, license identifier, fair-use claim if applicable

**Gitignore:**
- Add `evals/corpus/de/human/research_only/` to `.gitignore`

**Re-fetch plan:**
- Keep existing 16 good docs (wikipedia_academic + wikipedia_career — both register-appropriate)
- Move existing 16 bad-fetch docs (wikipedia_casual + wikipedia_marketing) to `redistributable/wikipedia_general/` neutral pool — still useful as DE Wikipedia background prose for mining baseline
- Add new register-targeted sources per registry above

---

## Total target volume

- Redistributable (committed): ~50 docs, ~400 KB
- Research-only (gitignored): ~50 docs, ~400 KB
- Combined for mining: ~100 docs, ~800 KB

Comfortably enough signal volume for `mine_patterns.py` LLR scoring against the Task 4 AI corpus (~75-100 samples).

---

## Maintainer decisions log (2026-05-27)

- **OQ1 Mastodon:** SKIP. Per-toot license tedious; register already covered.
- **OQ2 Faculty pages:** SKIP. Wikipedia bios + Bundesregierung + GitHub profiles cover career register.
- **OQ4 Wikivoyage:** SKIP. Travel blogs (research_only) only — register accuracy wins over redistributable backbone for casual.
- **OQ5 Volume balance:** 50/50 split as drafted.

**Net effect on tables above:**
- casual: drop Wikivoyage row + Mastodon row. Travel blogs + lifestyle blogs + Reddit + Content Forge guide remain (all research_only).
- career: drop faculty-pages row.
- legal / technical / marketing / academic: unchanged.
