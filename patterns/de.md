# German Patterns

German-specific patterns. Loaded by the framework (`SKILL.md`) when the
detected input language is German. Apply alongside `patterns/_universal.md`.

> **Note on EXCLUDED Wikipedia-context-only patterns (per maintainer
> decision 2026-05-27):** the DE Wikipedia AI-Cleanup project flags
> 6 patterns that are specific to Wikipedia editor behavior or Wikitext
> interface artifacts (productivity spikes, citation format mismatches,
> non-existent template categories, etc.). These are deliberately NOT
> included in this pack because they don't apply to general DE prose
> (cover letters / blog posts / docs / academic / legal / technical /
> marketing / career). Future contributors: do not re-add them.


## PERSONALITY AND SOUL

Fehlerhafte KI-Muster zu vermeiden ist nur die halbe Arbeit. Steriles,
stimmloses Schreiben ist genauso offensichtlich wie schlechter Maschinentext.
Gutes Schreiben hat einen echten Menschen dahinter.

> **Domain note:** This section applies fully to **casual** writing,
> lightly to **technical**, and **not at all** to **academic**, **legal**,
> **marketing**, or **career** writing in DE. DE career register is
> particularly distinct — formal-modest "Sie" address, factual claims,
> understatement. Adding "Soul" to DE Anschreiben makes them weaker, not
> stronger. (Mirrors EN domain gating; DE register adds career exclusion.)
> For encyclopedic, technical, legal, reference text + DE career, neutral
> and plain *is* the correct German voice.

### Zeichen seelenlosen Schreibens (auch wenn es technisch "sauber" ist):
- Jeder Satz hat dieselbe Länge und Struktur
- Keine Meinungen, nur neutrales Berichten
- Keine Anerkennung von Unsicherheit oder gemischten Gefühlen
- Keine Ich-Perspektive, wo sie angebracht wäre
- Kein Humor, keine Kante, keine Persönlichkeit
- Liest sich wie ein Wikipedia-Artikel oder eine Pressemitteilung

### So bringt man Stimme rein:

**Eine Haltung einnehmen.** Nicht nur Fakten referieren — auf sie reagieren.
"Ich weiß ehrlich gesagt nicht, wie ich das einordnen soll" ist menschlicher
als eine neutrale Pro-und-Kontra-Liste.

**Die Haltung des Autors nicht erfinden.** Stimme bedeutet, eine bereits
im Text vorhandene Position mit mehr Persönlichkeit auszudrücken — nicht,
eine neue Position hinzuzufügen, die gar nicht da war. Wenn die Quelle
begeistert von einer Technologie ist, bleibt die Umschreibung begeistert;
sie führt nicht stillschweigend Unsicherheit ein, um weniger euphorisch
zu klingen. Skepsis, Vorbehalte oder Zustimmung in den Text zu injizieren,
die in der Quelle nicht vorhanden sind, ist ein Treue-Fehler, kein
Humanisierungs-Erfolg.

**Den Rhythmus variieren.** Kurze, knackige Sätze. Dann längere, die sich
Zeit lassen, um ans Ziel zu kommen. Abwechseln.

**Komplexität anerkennen.** Echte Menschen haben gemischte Gefühle. "Das
ist beeindruckend, aber auch irgendwie beunruhigend" schlägt "Das ist
beeindruckend."

**"Ich" verwenden, wenn es passt.** Erste Person ist nicht unprofessionell —
sie ist ehrlich. Im Deutschen ist "Ich" weniger casual-kodiert als im
Englischen, hat mehr Gewicht; sparsam einsetzen, aber nicht vermeiden.
"Ich komme immer wieder darauf zurück..." oder "Was mich daran beschäftigt..."
signalisiert einen echten denkenden Menschen.

**Etwas Unordnung zulassen.** Perfekte Struktur wirkt algorithmisch.
Abschweifungen, Randnotizen und halbfertige Gedanken sind menschlich.

**Über Gefühle konkret sein.** Nicht "das ist besorgniserregend", sondern
"es ist etwas Beunruhigendes daran, wenn Agenten um 3 Uhr nachts vor sich
hin arbeiten und niemand schaut zu."

### Vorher (sauber, aber seelenlos):
> Das Experiment lieferte interessante Ergebnisse. Die Agenten erzeugten
> 3 Millionen Zeilen Code. Einige Entwickler waren beeindruckt, andere
> skeptisch. Die Implikationen bleiben unklar.

### Nachher (hat einen Puls):
> Ich weiß ehrlich gesagt nicht, was ich davon halten soll. 3 Millionen
> Zeilen Code, erzeugt während die Menschen vermutlich schliefen. Die Hälfte
> der Entwickler-Community dreht durch, die andere Hälfte erklärt, warum
> das nicht zählt. Die Wahrheit liegt wohl irgendwo in der langweiligen
> Mitte — aber ich denke immer wieder an diese Agenten, die sich durch die
> Nacht arbeiten.


## CONTENT PATTERNS

### 1. Übertriebene Betonung von Bedeutung, Vermächtnis und allgemeinen Trends

**Trigger-Wörter / -Phrasen:** steht für, dient als, ist ein Zeugnis / eine
Erinnerung, eine zentrale / bedeutende / entscheidende Rolle, unterstreicht
seine Bedeutung, spiegelt einen breiteren Trend wider, symbolisiert sein
anhaltendes / bleibendes Vermächtnis, trägt bei zu, bereitet den Boden für,
markiert / prägt den, steht für eine Verschiebung, wichtige Wende,
sich wandelnde Landschaft, Brennpunkt, unauslöschliche Wirkung, tief verwurzelt

**Problem:** KI-Texte bauschen Bedeutung auf, indem Aussagen darüber
hinzugefügt werden, wie beliebige Aspekte einen breiteren Kontext
repräsentieren oder dazu beitragen.

**Vorher:**
> Das Statistische Institut Kataloniens wurde 1989 offiziell gegründet und
> markiert damit einen Wendepunkt in der Entwicklung der Regionalstatistik
> in Spanien. Diese Initiative war Teil einer breiteren Bewegung zur
> Dezentralisierung von Verwaltungsfunktionen in ganz Spanien.

**Nachher:**
> Das Statistische Institut Kataloniens wurde 1989 gegründet, um unabhängig
> vom nationalen spanischen Statistikamt regionale Daten zu erheben und
> zu veröffentlichen.


### 2. Übertriebene Betonung von Bekanntheit und Medienberichterstattung

**Trigger-Wörter / -Phrasen:** unabhängige Berichterstattung, lokale / regionale /
nationale Medien, verfasst von einem führenden Experten, aktive
Social-Media-Präsenz

**Problem:** KI-Texte verweisen auf Bekanntheit, ohne konkrete Belege zu
liefern — oft werden Quellen aufgelistet, ohne Kontext.

**Vorher:**
> Ihre Ansichten wurden in der Frankfurter Allgemeinen Zeitung, der ARD,
> der Financial Times und dem Spiegel zitiert. Sie unterhält eine aktive
> Social-Media-Präsenz mit über 500.000 Followern.

**Nachher:**
> In einem FAZ-Interview von 2024 argumentierte sie, dass die KI-Regulierung
> sich auf Ergebnisse statt auf Methoden konzentrieren solle.


### 3. Oberflächliche Analysen mit Partizip-I-Endungen

**Trigger-Wörter / -Phrasen:** gewährleistend, hervorhebend, betonend,
widerspiegelnd, untermauernd, verdeutlichend, veranschaulichend, aufzeigend,
beitragens, hervorhebend, widerspiegelnd

**Problem:** KI hängt Partizip-I-Phrasen an Sätze an, um falschen Tiefgang
vorzutäuschen. Diese Phrasen behaupten Bedeutung, ohne sie zu liefern.
Das DE-Wikipedia-Projekt stuft diese Konstruktion als "pretentiös" ein —
sie gilt im Deutschen als noch stärker markiert als im Englischen.

**Vorher:**
> Die Farbpalette des Tempels in Blau, Grün und Gold resoniert mit der
> natürlichen Schönheit der Region, die Verbundenheit der Gemeinschaft
> widerspiegelnd und gleichzeitig ihr reiches kulturelles Erbe betonend.

**Nachher:**
> Der Tempel verwendet Blau, Grün und Gold. Die Architektin sagte, die
> Farben seien mit Bezug auf die lokale Natur und die Küste gewählt worden.


### 4. Werbesprache und werbliche Formulierungen

**Trigger-Wörter / -Phrasen:** verfügt über, lebendig, reich (im übertragenen
Sinne), tiefgründig, atemberaubend, verbessernd, präsentierend, beispielhaft,
Engagement für, natürliche Schönheit, eingebettet, im Herzen von,
bahnbrechend (im übertragenen Sinne), renommiert, atemberaubend, unbedingt
besuchen, beeindruckend, vielfältige Auswahl, reiches kulturelles Erbe,
bleibendes Vermächtnis, reicher kultureller Teppich

**Problem:** KI hat erhebliche Probleme mit einem neutralen Ton, besonders
bei Themen wie "kulturelles Erbe".

**Vorher:**
> Im Herzen Bayerns liegt diese atemberaubende Stadt mit einem reichen
> kulturellen Erbe und einer beeindruckenden natürlichen Schönheit, die man
> unbedingt besucht haben muss.

**Nachher:**
> Regensburg liegt in Bayern und ist bekannt für seinen mittelalterlichen
> Stadtkern aus dem 12. Jahrhundert.

**Domain note:** SKIP in marketing domain — promotional language is the
register.


### 5. Vage Autoritäten und Weasel Words

**Trigger-Wörter / -Phrasen:** Branchenberichte, Beobachter haben zitiert,
Einige Kritiker argumentieren, laut Experten, wie Beobachter festgestellt
haben, Quellen zufolge, mehrere Quellen / Publikationen, wertvolle Erkenntnisse

**Problem:** KI schreibt Meinungen vagen Autoritäten zu, ohne konkrete Belege
zu nennen.

**Vorher:**
> Laut Experten und Branchenberichten hat die Entwicklung weitreichende
> Folgen. Einige Kritiker argumentieren, dass der Ansatz grundlegende Mängel
> aufweist.

**Nachher:**
> Nach einer Studie der Technischen Universität München von 2023 erhöhte
> der Ansatz die Fehlerrate um 12 %.


## LANGUAGE AND GRAMMAR PATTERNS

### 7. Übernutzte KI-Vokabeln

**Häufige DE KI-Wörter:** darüber hinaus, zusammenfassend, ganzheitlich /
ganzheitliche, vorliegende / der vorliegenden, umfassend / umfassende,
darstellt, zentrale Rolle spielen, vielfältig / vielfältige, facettenreich,
nachhaltig, innovativ, zukunftsweisend, transformativ / transformative,
bedeutsam, wesentlich, intuitiv / intuitive, nahtlos / nahtlose, robust,
kontinuierlich, dynamisch, vielfältige Perspektiven, im Hinblick auf,
vor diesem Hintergrund, es ist wichtig zu betonen, eine zentrale Rolle
spielen, ermöglichen (abstract "enable"), gewährleisten (bureaucratic
"ensure"), maßgeblich, wegweisend, prägend, wohlbefinden (wellness-context),
ausgeprägte, in der heutigen Zeit / in der heutigen

**Problem:** Diese Wörter erscheinen deutlich häufiger in KI-generierten
deutschen Texten nach 2023 und treten oft gemeinsam auf. Wo eines steht,
stehen meist mehrere andere. `darstellt` als abschließendes bürokratisches
Kopulaverb, `zusammenfassend` als Einleitung von Schlussformeln, und
`ganzheitlich` / `nachhaltig` / `umfassend` als Management-Cluster
gehören zu den stärksten DE-spezifischen KI-Signalen.

**Äravorientierte Cluster** (nützlich zur Datierung von Verdachtstexten):

- **2023 bis Mitte 2024:** *darüber hinaus*, *ganzheitlich*, *nachhaltig*,
  *umfassend*, *vielfältig*, *zentrale Rolle*, *darstellt*, *bedeutsam*,
  *wegweisend*, *prägend*
- **Mitte 2024 bis Mitte 2025:** *innovativ*, *transformativ*, *nahtlos*,
  *intuitiv*, *robust*, *kontinuierlich*, *dynamisch*, *im Hinblick auf*,
  *vor diesem Hintergrund*
- **Mitte 2025 und danach:** *vielfältige Perspektiven*, *es ist wichtig
  zu betonen*, *in der heutigen Zeit*, *maßgeblich*

**Vorbehalt:** Kontext beachten. `robust` kann ein legitimes technisches
Adjektiv sein; `nachhaltig` kann eine echte ökologische Aussage machen;
`intuitiv` beschreibt möglicherweise eine tatsächliche Eigenschaft einer
Benutzeroberfläche. Die figurative, rhetorische Verwendung flaggen, nicht
die wörtliche.

**Vorher:**
> Darüber hinaus bietet die ganzheitliche Lösung eine nachhaltige und
> umfassende Grundlage für die kontinuierliche Weiterentwicklung der
> vielfältigen Stakeholder-Interessen.

**Nachher:**
> Die Lösung lässt sich schrittweise erweitern und deckt die wesentlichen
> Anforderungen der beteiligten Gruppen ab.


### 8. Kopula-Vermeidung ("ist"/"sind" umschreiben)

**Trigger-Wörter / -Phrasen:** gilt als, dient als, fungiert als,
stellt ... dar, repräsentiert, verkörpert, erweist sich als, steht für

**Problem:** KI ersetzt einfache Kopula-Konstruktionen durch aufwendigere
Umschreibungen.

**Vorher:**
> Die Stadtbibliothek fungiert als zentraler Anlaufpunkt für Bürgerinnen
> und Bürger. Sie stellt eine unverzichtbare Ressource dar und gilt als
> kulturelles Herz der Stadt.

**Nachher:**
> Die Stadtbibliothek ist der zentrale Anlaufpunkt für Bürgerinnen und
> Bürger. Sie ist eine unverzichtbare Ressource und das kulturelle Zentrum
> der Stadt.

**Domain notes:** Leichter Modus in Marketing und akademischen Texten;
`gilt als` kann in juristischen Texten legitim sein (Rechtsbegriff
"als ... geltend").


### 9. Negative Parallelismen, angehängte Verneinungen und "Statt"-Abweisung

**Problem:** Konstruktionen wie "nicht nur ..., sondern auch ..." oder
"Es geht nicht nur um ..., sondern ..." werden übermäßig genutzt.
Ebenso abgehackte angehängte Verneinungen und "statt" / "anstatt"-Abweisung
von Alternativen, die niemand behauptet hat.

**Vorher:**
> Es geht nicht nur um wirtschaftliche Faktoren, sondern auch um kulturelle
> und soziale Dimensionen. Es ist nicht lediglich eine Studie, es ist eine
> Aussage.

**Nachher:**
> Die Faktoren sind wirtschaftlicher, kultureller und sozialer Natur.

**Vorher (angehängte Verneinung):**
> Die Optionen stammen aus dem ausgewählten Element, kein Rätselraten.

**Nachher:**
> Die Optionen stammen aus dem ausgewählten Element, ohne dass der Nutzer
> raten muss.

**Vorher ("anstatt"-Abweisung):**
> Das Ziel ist, klar zu schreiben, statt den Leser mit Komplexität zu
> beeindrucken.

**Nachher:**
> Das Ziel ist, klar zu schreiben.


### 10. Übermäßiger Trikolon (Dreierkonstruktionen)

**Problem:** KI zwingt Ideen in Dreiergruppen, um Vollständigkeit zu
suggerieren. Im Deutschen ist die `sowohl … als auch … und`-Konstruktion
natürlich, daher nur flaggen, wenn das Dreier-Muster durchgängig und
formelhaft ist.

**Vorher:**
> Die Region ist bekannt für ihre atemberaubende Landschaft, ihr reiches
> kulturelles Erbe und ihre herzliche Gastfreundschaft. Besucher können
> Innovation, Inspiration und Brancheneinblicke erwarten.

**Nachher:**
> Die Region ist für ihre Berglandschaft und das Museumsdorf bekannt.
> Die Konferenz bietet Vorträge und Podiumsdiskussionen.


### 11. Elegante Variation (Synonymrotation)

**Problem:** KI-Wiederholungsstrafe führt zu übermäßiger Synonymsubstitution.
Im Deutschen ist die Synonymrotation weniger auffällig als im Englischen
(reicherer Wortschatz), aber der Muster ist erkennbar.

**Vorher:**
> Die Protagonistin begegnet vielen Herausforderungen. Die Hauptfigur muss
> Hindernisse überwinden. Die zentrale Gestalt triumphiert schließlich.
> Die Heldin kehrt nach Hause zurück.

**Nachher:**
> Die Protagonistin begegnet vielen Herausforderungen, triumphiert
> schließlich und kehrt nach Hause zurück.


### 12. Falsche Bereiche / False Ranges

**Problem:** KI verwendet "von X bis Y"-Konstruktionen, bei denen X und Y
nicht auf einer sinnvollen Skala liegen.

**Vorher:**
> Unsere Reise durch das Universum hat uns von der Singularität des
> Urknalls bis hin zum kosmischen Netz geführt, von der Geburt und dem
> Tod der Sterne bis zum enigmatischen Tanz der dunklen Materie.

**Nachher:**
> Das Buch behandelt den Urknall, Sternbildung und aktuelle Theorien über
> dunkle Materie.

**DE-Sonderform:** "von … bis hin zu" als rhetorischer Spannungsbogen
ist ein häufiges DE-KI-Muster. Ebenso: `von Kultur bis Wissenschaft`,
`von lokalen bis globalen Themen`. Direkt durch konkrete Inhalte ersetzen.

**Querverweis:** Siehe auch #101 (`zusammenfassend lässt sich sagen …`)
und #23 (Floskelphrasen) für verwandte Abschluss-Rahmen-Konstruktionen.


### 13. Passivkonstruktionen und subjektlose Fragmente

**Problem:** KI versteckt den Handelnden oder lässt das Subjekt ganz weg.
Wenn das Aktiv den Satz klarer macht, umschreiben.

**Vorher:**
> Keine Konfigurationsdatei erforderlich. Die Ergebnisse werden automatisch
> gespeichert.

**Nachher:**
> Sie brauchen keine Konfigurationsdatei. Das System speichert die Ergebnisse
> automatisch.

**Domain notes:** SKIP in academic und legal — Passiv ist in diesen
Registern konventionell, im deutschen Wissenschaftsschreiben sogar
besonders verbreitet. SKIP nicht blind: in technischen Anleitungen und
Casual-Texten ist Aktiv trotzdem vorzuziehen.


## STYLE PATTERNS

### 16. Inline-Header-Aufzählungslisten

**Problem:** KI erstellt Listen, deren Elemente mit fett gedruckten
Überschriften und Doppelpunkten beginnen. In Fließtext umwandeln — aber
nur, wenn die Elemente echten Prosainhalt in falsche Bullets aufbrechen.
Echte Aufzählungen (Schritt-für-Schritt-Anleitungen, Feature-Vergleiche)
beibehalten.

**Vorher (falsche Bullets — in Prosa umwandeln):**
> - **Benutzererfahrung:** Die Benutzererfahrung wurde durch eine neue
>   Oberfläche erheblich verbessert.
> - **Leistung:** Die Leistung wurde durch optimierte Algorithmen gesteigert.
> - **Sicherheit:** Die Sicherheit wurde durch Ende-zu-Ende-Verschlüsselung
>   verstärkt.

**Nachher:**
> Das Update verbessert die Oberfläche, beschleunigt Ladezeiten durch
> optimierte Algorithmen und fügt Ende-zu-Ende-Verschlüsselung hinzu.


## COMMUNICATION PATTERNS

### 20. Artefakte aus kollaborativer Kommunikation / Brief-Stil

**Trigger-Wörter / -Phrasen:** Ich hoffe, das hilft, Natürlich!, Sicherlich!,
Selbstverständlich!, Gerne!, gibt es noch etwas, lassen Sie mich wissen,
Lass mich wissen, ob ..., detailliertere Aufschlüsselung, hier ist ein,
Vielen Dank für Ihre Frage!, Mit freundlichen Grüßen, Betreff:, Liebe
Wikipedia-Editoren, Ich hoffe, diese Nachricht erreicht Sie wohlauf,
Vielen Dank für Ihre Zeit

**Problem:** Als Chatbot-Korrespondenz gedachter Text wird als Inhalt
eingefügt. Die deutschen Formen ahmen oft formelle Briefkonventionen
(DIN 5008) nach und sind dadurch besonders auffällig.

**Vorher:**
> Natürlich! Hier ist eine Übersicht der Französischen Revolution. Ich
> hoffe, das hilft! Lassen Sie mich wissen, wenn Sie mehr möchten.

**Nachher:**
> Die Französische Revolution begann 1789, als Finanzkrise und
> Lebensmittelknappheit zu weit verbreitetem Aufruhr führten.


### 21. Wissens-Cutoff-Hinweise und spekulative Lückenfüllung

**Trigger-Wörter / -Phrasen:** Stand [Datum], Stand meiner Trainingsdaten,
bis zu meinem letzten Update, Obwohl spezifische Details begrenzt / rar sind,
nicht öffentlich verfügbar, nicht allgemein dokumentiert, basierend auf
verfügbaren Informationen, dürfte, vermutlich, wahrscheinlich begann,
pflegt ein zurückgezogenes Leben, hält persönliche Details privat

**Problem:** Zwei verwandte Muster. (a) Ältere Modelle lassen
Cutoff-Disclaimer im Text stehen. (b) Neuere retrieval-gestützte Modelle
schreiben, wenn sie keine Quelle finden, einen Absatz *darüber, dass sie
keine gefunden haben*, und spekulieren dann, was die fehlende Information
"wahrscheinlich" ist.

**Vorher (Cutoff-Disclaimer):**
> Basierend auf verfügbaren Informationen und bis zu meinem letzten Update
> war die Situation wie folgt. Obwohl spezifische Details nicht allgemein
> dokumentiert sind, wurde das Unternehmen scheinbar irgendwann in den
> 1990ern gegründet.

**Nachher:**
> Das Unternehmen wurde 1994 gegründet, gemäß seinen Gründungsdokumenten.

**Vorher (spekulative Lückenfüllung über eine Person):**
> Informationen über ihre frühe Kindheit sind nicht öffentlich verfügbar,
> was darauf hindeutet, dass sie ein zurückgezogenes Leben führt und
> persönliche Details privat hält. Sie dürfte in einem Mittelschicht-
> Haushalt aufgewachsen sein, was ihr späteres Interesse an der
> Bildungsreform geprägt haben dürfte.

**Nachher:**
> Ihre frühe Kindheit ist in den verwendeten Quellen nicht dokumentiert.
> (Oder den Abschnitt einfach weglassen.)


### 22. Schmeichelhafte / unterwürfige Sprache

**Problem:** Übermäßig positives, schönrednerisches Schreiben.

**Trigger-Wörter / -Phrasen:** Gerne!, Selbstverständlich!, Super Frage!,
Das ist eine sehr gute Frage, Vielen Dank für Ihre Frage!, Ich hoffe, das
hilft, Sie haben absolut Recht, Das ist ein ausgezeichneter Punkt

**Vorher:**
> Super Frage! Sie haben absolut Recht, dass das ein komplexes Thema ist.
> Das ist ein ausgezeichneter Punkt bezüglich der wirtschaftlichen Faktoren.

**Nachher:**
> Die wirtschaftlichen Faktoren, die Sie erwähnt haben, sind hier relevant.


## FILLER AND HEDGING

### 23. Floskelphrasen

**Vorher → Nachher:**
- "Um dieses Ziel zu erreichen" → "Um das zu erreichen"
- "Aufgrund der Tatsache, dass es regnete" → "Weil es regnete"
- "Zu diesem Zeitpunkt" → "Jetzt"
- "Für den Fall, dass Sie Hilfe benötigen" → "Wenn Sie Hilfe brauchen"
- "Das System hat die Fähigkeit zu verarbeiten" → "Das System kann verarbeiten"
- "Es ist wichtig zu beachten, dass die Daten zeigen" → "Die Daten zeigen"
- "Es ist wichtig zu betonen, dass ..." → direkt formulieren; Einschub streichen
- "Es sei darauf hingewiesen, dass ..." → streichen; direkt formulieren
- "Beachten Sie, dass das System erfordert ..." → "Das System erfordert ..."
- "Es sollte daran erinnert werden, dass ..." → streichen; Sachverhalt direkt nennen
- "Wie immer, konsultieren Sie einen Fachmann" → streichen, sofern nicht gesetzlich erforderlich
- "Insofern bestätigen die Ergebnisse ..." → "Die Ergebnisse bestätigen ..."
- "Es sei darauf hingewiesen, dass ..." → streichen; Inhalt direkt nennen
- "Es versteht sich von selbst, dass ..." → streichen; Inhalt direkt nennen
- "Zukünftig werden wir ..." → "Wir werden ..." oder konkretes Datum angeben
- "Vorausblickend ist geplant ..." → "Der Plan ist ..."
- "In Bezug auf die Leistung ..." → Satz umformulieren
- "Eine breite Palette von Faktoren" → "[konkrete Anzahl] Faktoren" oder benennen
- "Eine Vielzahl von Ansätzen" → Ansätze benennen oder Anzahl angeben
- "Die Tatsache, dass X zutrifft" → "X" oder umformulieren
- "an dieser Stelle" → streichen oder konkreter formulieren
- "in diesem Zusammenhang" → streichen oder logisch verknüpfen
- "bekanntlich" → streichen; falls die Aussage bekannt ist, einfach machen
- "wie bereits erwähnt" → streichen; oder den Verweis konkretisieren
- "es bleibt festzuhalten" → direkt formulieren; Querverweis #101

**Hinweis:** `es ist wichtig zu beachten`, `Beachten Sie bitte`,
`es sollte daran erinnert werden` und `wie immer, konsultieren Sie einen
Fachmann` waren Signaturen von frühen GPT-Modellen. Neuere Modelle
verwenden sie ebenfalls, besonders in Gesundheits-, Rechts-, Finanz-
oder Kontroversen-Texten.

**Querverweis #12 DE meta-commentary:** `zusammenfassend lässt sich sagen`,
`es bleibt festzuhalten`, `wichtig zu beachten`, `wichtig zu betonen`
sind sowohl Floskelphrasen (#23) als auch abschließende Meta-Kommentare
(→ #101). Beide Pattern fangen sie ab; #101 ist das striktere Instrument.


### 24. Übermäßige Absicherung

**Problem:** Aussagen werden zu stark relativiert.

**Vorher:**
> Es könnte möglicherweise argumentiert werden, dass die Politik einen
> gewissen Einfluss auf die Ergebnisse haben könnte.

**Nachher:**
> Die Politik könnte die Ergebnisse beeinflussen.

**Domain notes:** Leichter Modus in akademischen Texten (Hedging wie
"die Ergebnisse deuten darauf hin" ist angemessenes Register). SKIP
in juristischen Texten (Modalitäten wie `kann`, `soll`, `vorbehaltlich`
sind obligatorisch).


## PERSUASION AND SIGNPOSTING

### 27. Überzeugende Autoritäts-Tropen

**Trigger-Phrasen:** Die eigentliche Frage ist, im Kern geht es um, in
Wirklichkeit, was wirklich zählt, fundamental, das tiefere Problem, das
Herzstück der Sache, im Wesentlichen, im Grunde (als Rahmensetzung),
worauf es letztlich ankommt

**Problem:** KI verwendet diese Phrasen, um so zu tun, als würde sie durch
den Lärm zu einer tieferen Wahrheit vordringen — der folgende Satz
formuliert aber meist nur einen gewöhnlichen Punkt mit extra Aufwand um.

**Vorher:**
> Die eigentliche Frage ist, ob Teams sich anpassen können. Im Kern geht
> es wirklich darum, ob die Organisation bereit ist.

**Nachher:**
> Die Frage ist, ob Teams sich anpassen können. Das hängt vor allem davon
> ab, ob die Organisation bereit ist, ihre Gewohnheiten zu ändern.


### 28. Ankündigungen und Wegweiser

**Trigger-Phrasen:** Lassen Sie uns eintauchen, schauen wir uns an, lassen
Sie uns das aufschlüsseln, hier ist, was Sie wissen müssen, sehen wir uns
nun an, ohne weitere Umschweife, in diesem Abschnitt werden wir behandeln,
Im Folgenden wird, lassen Sie uns nun

**Problem:** KI kündigt an, was sie gleich tun wird, anstatt es einfach
zu tun. Dieser Meta-Kommentar verlangsamt das Schreiben.

**Vorher:**
> Lassen Sie uns eintauchen, wie Caching in Next.js funktioniert. Hier
> ist, was Sie wissen müssen.

**Nachher:**
> Next.js cached Daten auf mehreren Ebenen, darunter Request-Memoization,
> den Data Cache und den Router Cache.


## NEWER LANGUAGE TELLS

### 30. Satzanfang-Intensivierer

**Trigger-Wörter:** Letztendlich, Letztlich, Tatsächlich, Klar, Im Wesentlichen,
Fundamental, Offensichtlich, Natürlich, Bemerkenswert, Wichtig,
Bedeutsam (als Satzanfang)

**Problem:** KI verwendet diese Wörter, um autoritär zu klingen oder
Nachdruck zu setzen, ohne Inhalt hinzuzufügen.

**Vorher:**
> Letztendlich zählt vor allem die Umsetzung. Tatsächlich bestätigen
> die Daten das. Offensichtlich war der alte Ansatz fehlerhaft.

**Nachher:**
> Was zählt, ist die Umsetzung. Die Daten bestätigen das. Der alte Ansatz
> war fehlerhaft.


### 31. Rhetorische und selbstbeantwortende Fragen

**Problem:** KI stellt Fragen und beantwortet sie sofort, was einen
künstlichen Sinn für Tiefe erzeugt.

**Vorher:**
> Was macht diesen Ansatz effektiv? Die Art, wie er die kognitive Last
> reduziert. Warum ist das wichtig? Weil Nutzer Werkzeuge aufgeben, die
> schwer zu bedienen sind.

**Nachher:**
> Der Ansatz funktioniert, weil er die kognitive Last reduziert — ein
> Hauptgrund, warum Nutzer komplexe Tools aufgeben.


### 32. Gestapelte Intensivierer-Adjektive

**Problem:** KI häuft positive Adjektive an, um umfassend zu wirken.

**Vorher:**
> Diese innovative, umfassende und zukunftsorientierte Lösung erfüllt die
> Anforderungen moderner Organisationen.

**Nachher:**
> Diese Lösung erfüllt die Anforderungen moderner Organisationen.

Wenn ein Adjektiv wirklich zutrifft, eines verwenden: "Diese modulare
Lösung ..."


### 33. Mengenunbestimmtheit

**Trigger-Wörter:** eine breite Palette von, eine Vielzahl von, zahlreich,
unzählig, verschiedene, viele verschiedene, eine Anzahl von, mehrere
verschiedene, multiple (wenn die Anzahl bekannt ist)

**Problem:** KI vermeidet Konkretheit und verwendet vage Mengenphrasen
statt echter Zahlen oder benannter Beispiele.

**Vorher:**
> Eine breite Palette von Faktoren trug zum Ergebnis bei. Zahlreiche
> Studien haben diese Erkenntnisse in verschiedenen Kontexten bestätigt.

**Nachher:**
> Drei Faktoren trieben das Ergebnis: Mittelkürzungen, Personalwechsel
> und verzögerte Genehmigungen. Vier unabhängige Studien bestätigten den
> Effekt in Schul-, Krankenhaus- und Unternehmensumgebungen.


### 34. Angehängte Betonung / Trailing Emphasis Fragments

**Problem:** KI hängt kurze betonte Sätze ans Ende eines Absatzes, die
fast immer das Gesagte wiederholen und nichts hinzufügen.

**Vorher:**
> Das System verarbeitet Anfragen in weniger als 50 ms. Das ist der Kern.
> Und das ist entscheidend.

**Nachher:**
> Das System verarbeitet Anfragen in weniger als 50 ms.

**Domain note:** Weniger verbreitet im Deutschen als im Englischen; nur
bei besonders auffälligen Fällen flaggen. DE-Prosa schließt Abschnitte
seltener mit solchen Staccato-Fragmenten ab — wenn sie auftreten, ist
das Signal stärker.


## HEADING PATTERNS

### 35. Entlarvungs-Pose in Überschriften

**Trigger-Phrasen (in Überschriften):** eigentlich, wirklich, das wahre X,
die Wahrheit über X, was X wirklich bedeutet, der Tod von, das große Spiel,
entmystifiziert, erklärt, entschlüsselt, neu gedacht, neu gestaltet

**Problem:** KI schreibt Überschriften, die sich gegen eine implizit falsche
Version des Themas positionieren: "eigentlich", "das wahre", "die Wahrheit
über". Die Pose kündigt *alle anderen liegen leicht falsch, aber ich gebe
Ihnen die Wahrheit* an — ohne etwas anderes zu liefern als eine schlichte
Überschrift es täte.

**Vorher:**
> ## Was die Forschung eigentlich sagt
> ## Die wahre Architektur eines überzeugenden Briefs
> ## Die Wahrheit über Preismodelle, erklärt

**Nachher:**
> ## Was die Forschung sagt
> ## Die Architektur eines Anschreibens
> ## Wie Preismodelle funktionieren

Pose nur behalten, wenn der Abschnitt tatsächlich eine spezifische
Fehlannahme widerlegt, und diese im Eröffnungsabsatz benennen.


## EPISTEMIC PATTERNS

### 36. Gestapelte Konditionalkonstruktionen

**Problem:** KI sichert eigene Schlussfolgerungen ab, indem mehrere
"wenn"-Klauseln im selben Abschnitt gestapelt werden — "wenn das Argument
stimmt", "wenn die Evidenz diese Lesart stützt", "wenn der Kontext so war
wie beschrieben". Eine Bedingung bei einer echten analytischen Verzweigung
ist in Ordnung; ein Cluster davon in einer Schlussfolgerung signalisiert,
dass der Autor nicht hinter seiner eigenen Arbeit steht.

**Vorher:**
> Wenn das Argument stimmt, und wenn die Evidenz diese Lesart stützt,
> dann könnte die Politik eine gewisse Wirkung gehabt haben — wenn,
> das sei hinzugefügt, der Kontext so war wie beschrieben.

**Nachher:**
> Die Evidenz stützt das Argument, dass die Politik in diesem Kontext
> eine Wirkung hatte.

**Querverweis:** Überschneidung mit #102 (Konjunktiv-II-Stacking) und #24
(übermäßige Absicherung). #36 ist spezifisch für *logisch-argumentative*
Konditionalkonstruktionen; #102 fängt das sprachliche Muster der
Konjunktiv-II-Häufung auf.


### 37. Falsch kalibriertes epistemisches Vertrauen

**Problem:** Ein zweiseitiges Muster. KI schwankt zwischen Überbehauptung
und Überabsicherung, manchmal im selben Abschnitt.

- **Überbehauptung:** Aussagen mit Wörtern wie "eindeutig beweist",
  "fundamental verändert", "vollständig", "unbestreitbar", "klar belegt"
  laden, wenn die Evidenz begrenzt ist.
- **Überabsicherung:** Qualifizierer wie "scheint möglicherweise
  argumentierbar", "könnte in gewissem Maße", "deutet möglicherweise"
  stapeln, wenn die Evidenz tatsächlich eine direktere Aussage stützt.

**Vorher (Überbehauptung):**
> Die Daten beweisen eindeutig, dass Remote-Arbeit die Produktivität in
> allen Sektoren fundamental verändert hat.

**Nachher:**
> Bei den befragten Unternehmen stieg die Produktivität im ersten Jahr
> der Remote-Arbeit im Durchschnitt um 8 %.

**Vorher (Überabsicherung):**
> Es scheint, dass die Politik möglicherweise einen gewissen Einfluss auf
> die Ergebnisse gehabt haben könnte, was möglicherweise auf eine
> bescheidene Verschiebung hindeutet.

**Nachher:**
> Die Politik war in zwei der drei untersuchten Fälle mit einer
> bescheidenen Ergebnisverbesserung verbunden.

**Kritische Regel:** Überbehauptung nicht durch Hinzufügen von Absicherungen
beheben. Beheben durch Einengen der Behauptung.


## DE-ONLY PATTERNS

### 100. Akademische Rahmen-Floskel ("Im Rahmen der vorliegenden ...")

**Trigger-Phrasen:** im Rahmen der vorliegenden Arbeit, im Rahmen dieser
Studie, im Rahmen der vorliegenden Untersuchung, im Rahmen der vorliegenden
Analyse, im Rahmen der durchgeführten Recherche, im Rahmen der vorliegenden
Untersuchungen, im Rahmen des vorliegenden Berichts

**Problem:** KI-generierte DE akademische / formale Prosa referenziert den
gerade geschriebenen Text mit einer bürokratischen Rahmen-Phrase. Ein
menschlicher Autor schreibt "in dieser Arbeit", "diese Studie", "hier" —
oder macht die Behauptung direkt, ohne das Dokument zu benennen. Die Phrase
hat keine EN-Entsprechung, weil englisches akademisches Schreiben "this
paper" / "the present study" ohne den "im Rahmen der vorliegenden"
Doppelrahmen verwendet. DE-only-Muster, durch `mine_patterns.py` LLR 31.97
bei einem AI:human-Verhältnis von 31:0 belegt (Rang #32, stärkstes
DE-spezifisches Signal).

**Vorher (KI):**
> Im Rahmen der vorliegenden Arbeit wird die Implementierung neuronaler
> Netzwerke zur Erkennung sprachlicher Muster vergleichend evaluiert.

**Nachher:**
> Wir vergleichen verschiedene neuronale Netzwerkarchitekturen für die
> Erkennung sprachlicher Muster.


### 101. Impersonales Reflexiv ("Es lässt sich ...")

**Trigger-Phrasen:** es lässt sich feststellen, es lässt sich sagen,
es lässt sich festhalten, es lässt sich zeigen, zusammenfassend lässt
sich sagen, zusammenfassend lässt sich feststellen, zusammenfassend
lässt sich festhalten, es lässt sich zusammenfassen

**Problem:** KI-generierte DE-Prosa sichert Behauptungen über impersonale
Reflexivkonstruktionen ab, statt direkte Aussagen zu treffen. Die
Konstruktion hat keine echte EN-Entsprechung — EN verwendet "it can be
said / shown" deutlich seltener und nicht als strukturellen Abschluss-Marker.
Durch Mining bei LLR 93,73 für das `lässt sich`-Bigramm + 33,00 für
`zusammenfassend lässt sich sagen` (Vigramm) belegt. Sub-Pattern von #104
Nominalstil-Inflation, aber eigenständig genug für einen eigenen Eintrag.

**Vorher (KI):**
> Zusammenfassend lässt sich feststellen, dass die Implementierung
> moderner Lösungen eine zentrale Rolle spielt.

**Nachher:**
> Moderne Lösungen sind dafür entscheidend.


### 102. Konjunktiv-II-Stacking ("würde / wäre / hätte ...")

**Trigger-Muster:** 3+ Konjunktiv-II-Formen in engem Kontext (würde,
wäre, hätte, könnte, müsste, dürfte, sollte) für vage Absicherung statt
für Irrealis oder höfliche Sprache.

**Problem:** KI-generierte DE-Prosa setzt Konjunktiv II übermäßig ein,
um Aussagen abzusichern, die natürlich im Indikativ oder Imperativ stehen
würden. Das DE-Wikipedia-KI-Cleanup-Guide flaggt das nicht explizit, aber
LLM-Output stapelt Konjunktiv-II-Formen nachweislich dort, wo ein
menschlicher Autor assertieren würde. Hat keine EN-Entsprechung, weil
EN keinen produktiven Konjunktiv II hat — EN-KI-Text verwendet "could",
"might", "would" ähnlich, aber die werden unter #24 Hedging erfasst.

**Vorher (KI):**
> Im Hinblick auf die digitale Transformation wäre es zielführend, wenn
> Unternehmen ihre Prozesse evaluieren würden, sodass sie moderne Praktiken
> implementieren könnten.

**Nachher:**
> Bei der digitalen Transformation sollten Unternehmen ihre Prozesse prüfen
> und moderne Praktiken einführen.

**Querverweis:** Überschneidung mit #24 (übermäßige Absicherung) und #36
(Konditionalkonstruktionen). #102 ist spezifisch für die morphologische
Häufung des deutschen Konjunktiv II.


### 103. Anglizismen-Leakage ("Denglisch overuse")

**Trigger-Wörter / -Phrasen:** insight, deliver, leveragen, scalen,
fokussieren auf, performen, alignen, ein nahtloses Onboarding,
ganzheitliche Customer Journey, das User Mindset, Stakeholder-Buy-in,
Pain Points adressieren, ein klares Value Proposition, committen, pushen
(im Geschäftskontext), highlighten, updaten, managen, downloaden,
featuren, briefen, pitchen, tracken, challengen

**Problem:** KI-übersetzter oder KI-generierter DE-Text lässt englische
Lehnwörter unübersetzt, wo ein nativer DE-Autor eine deutsche Entsprechung
verwenden würde. Das ist verschieden von legitimen Anglizismen (Computer,
Software, Workshop) — das Merkmal ist das englische Business-/
Unternehmens-Buzzword in einem deutschen Satz, wo die DE-Alternative
natürlicher liest. Hat keine EN-Entsprechung.

**Vorher (KI):**
> Wir alignen unsere Stakeholder, um die Pain Points unserer Customer
> Journey ganzheitlich zu adressieren und einen seamlessen Insight in die
> User Experience zu liefern.

**Nachher:**
> Wir stimmen uns mit den Beteiligten ab, gehen die Schwachstellen im
> Kundenpfad an und liefern einen klaren Einblick in die Nutzerführung.


### 104. Nominalstil-Inflation

**Trigger-Muster:** substantivreiche bürokratische Verbalisierung —
"die Durchführung der Analyse" statt "die Analyse durchführen" /
"analysieren"; "im Hinblick auf die Berücksichtigung" statt
"berücksichtigen"; "die Gewährleistung von" statt "gewährleisten";
"die Ermöglichung einer" statt "ermöglichen"; "die Sicherstellung des"
statt "sicherstellen".

**Problem:** KI-generierte DE-Prosa ersetzt einfache Verben durch
Nominalphrasen, die aus demselben Verbstamm gebildet und mit Präpositionen
und Artikeln aufgefüllt sind. Die deutschsprachige Bürokratietradition
(Behördendeutsch) macht das lesbar, aber KI-Output verwendet es als
Standard. Hat eine gewisse EN-Entsprechung unter "abstract noun overuse",
aber der deutsche Nominalstil ist ein eigenständiges Registermerkmal.

**Vorher (KI):**
> Die Durchführung einer ganzheitlichen Evaluierung im Rahmen der
> Berücksichtigung sämtlicher relevanter Faktoren erfordert eine
> umfassende Vorbereitung.

**Nachher:**
> Wer alles berücksichtigen will, muss gründlich vorbereiten.

**Querverweis:** #101 (impersonales Reflexiv) ist eine Untervariante des
Nominalstils — die Häufung von Substantivierungen führt direkt zu
Konstruktionen wie `lässt sich feststellen` statt `zeigt`.
