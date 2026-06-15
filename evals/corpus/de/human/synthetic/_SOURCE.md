# Source & provenance — DE synthetic clean Anschreiben corpus

These eight `anschreiben_*.md` files are **synthetic, Opus-generated** clean
German cover letters (Anschreiben), written for the humanizer-ext
**false-positive (over-edit) eval**. They represent the DACH gold standard of
human career writing: formal-modest register, understated, concrete, with real
metrics and zero AI tells / zero Bewerbungs-Floskeln.

## Purpose
They are **true negatives** for the humanizer skill. The eval verifies that the
skill **PRESERVES** this prose (low edit ratio) rather than rewriting it. If the
humanizer edits these heavily, it is over-editing genuine human-quality writing.

## Provenance / copyright
- **Not scraped** from Muster-/Vorlagen-Bewerbungssites or any third-party
  source. No third-party copyright attaches.
- Authored synthetically by the Opus career-writer persona for this corpus.
- Released under MIT, consistent with the parent project and the EN synthetic
  corpus.

## Known caveat
Same caveat as the EN synthetic corpus: these are **synthetic, not sourced
human prose**. They are written to read as authentic human Anschreiben, but they
were not collected from real applicants. Treat as a curated stand-in for genuine
DACH human writing, not as field-sampled ground truth.

## The eight
| File | Role / scenario |
|------|-----------------|
| `anschreiben_swe_einsteiger_01.md` | Softwareentwickler, Berufseinsteiger nach dem Studium |
| `anschreiben_projektmanagement_01.md` | Projektleiter, erfahren, Stellenwechsel |
| `anschreiben_pflege_01.md` | Pflegefachkraft, erfahren |
| `anschreiben_vertrieb_quereinstieg_01.md` | Quereinsteiger in den Vertrieb |
| `anschreiben_ausbildung_industriekauffrau_01.md` | Auszubildende Industriekauffrau, Schulabgängerin |
| `anschreiben_marketing_senior_01.md` | Senior Marketing Manager B2B |
| `anschreiben_elektroniker_01.md` | Elektroniker für Betriebstechnik, Facharbeiter |
| `anschreiben_data_analyst_01.md` | Data Analyst, Quereinstieg aus der Wissenschaft |
