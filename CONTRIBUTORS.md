# Contributors

humanizer-ext is an extended fork of [blader/humanizer](https://github.com/blader/humanizer). The list below credits people whose code, ideas, or feedback shaped the fork beyond the upstream base.

## Maintainer

- **Christian Huhn** ([@duathron](https://github.com/duathron)) — fork maintainer; v3.0.0–v3.4.0 changes (domain awareness, mode selector, density preflight, detection guidance, multi-lingual architecture, eval infrastructure)

## Contributors

- **Asaf Lecht** ([@Seithx](https://github.com/Seithx)) — `evals/scripts/regex_scorer.py` — deterministic regex-based AI-tell scorer (v3.4.0). Per-paragraph density, sentence-rhythm CV, and the `--compare` rewrite-diff mode. Provided as the basis for the medium integration that added language-pack registration and the `--lang` flag.

## Upstream

- [blader/humanizer](https://github.com/blader/humanizer) — original skill (v2.5.1 was the fork point). Specific upstream PRs cherry-picked into v3.2.0: #113, #112, #111, #116, #85; PR #115 was adapted rather than merged verbatim.
- [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (EN) — community-curated pattern catalogue; the basis for `patterns/_universal.md` + `patterns/en.md`.
- [Wikipedia:Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte) (DE) — DE-community equivalent; will be the Phase A seed for `patterns/de.md` in v3.5.0.
- [Aide:Identifier l'usage d'une IA générative](https://fr.wikipedia.org/wiki/Aide:Identifier_l'usage_d'une_IA_g%C3%A9n%C3%A9rative) (FR) — FR-community equivalent; future Phase A seed for `patterns/fr.md`.

## How to be added

Open a PR that meaningfully changes the skill (new pattern, new language pack, new eval runner, substantial bug fix, doc that someone else relies on). Add yourself to this file in the same PR.
