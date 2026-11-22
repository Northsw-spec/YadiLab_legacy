# Forsknings- och genomförandeplan: automatisk nätverkslayout utan ELK

**Status:** PROPOSED / PLANNING ONLY – ingen implementationsauktorisation  
**Datum:** 2026-11-22  
**Forskningsbas:** `main` `d19612a21d590b7a5d86ae40a2b14feb64a13e3f` (main-CI SUCCESS, Actions #44961768870).  
**Mål:** YadiLab ska på sikt kunna skapa en begriplig, stabil topologivy för användarbekräftad nätverksdokumentation utan att externa dokument måste ange YadiLab-specifika X/Y-koordinater. **Ingen ELK, Graphviz, Dagre eller annan extern layoutmotor som standard.**

> **Mandat och prioritet:** Detta är ett **tekniskt, kompletterande forskningsunderlag**, inte en konkurrerande övergripande färdplan och inte en order att skriva kod. `docs/QUALITY_IMPROVEMENT_PLAN.md` (QUALITY-000–011), `AGENTS.md`, `docs/MASTERPROMPT.md` och `docs/IMPORT_SOURCE_CONTRACT.md` fortsätter styra. Kvalitetsplanens ordning gäller om användaren inte uttryckligen prioriterar om. Varje LA-etapp nedan kräver **separat uttryckligt implementationsmandat** och egen avgränsad PR. Denna dokument-PR får aldrig tolkas som godkännande att starta LA-01–LA-06.

## 1. Fyra verifieringsvågor

### Våg 1 – aktuell källkod och ägarskap

| Komponent | Verifierad uppgift på forsknings-HEAD | Bindande konsekvens |
|---|---|---|
| `network_core/import_plan.py::node_layout` | Sorterar valda nod-ID:n och placerar dem i ett heltalsrutnät: `cols=1+isqrt(n-1)`, `x=110+260*(i%cols)`, `y=110+220*(i//cols)`. Max 2 000 noder. | Behåll **historisk v1-funktion ordagrant**, dess ordning och testvektorer. |
| `network_core/import_plan.py::_candidate` | Använder `node_layout` för nya schema-1.4-kandidater och markerar X/Y som `derived_layout`. | En befintlig kandidat är inte tillstånd att tyst använda en ny algoritm. |
| `network_core/import_evidence.py` | Återskapar samma `node_layout` och avvisar historisk layout som avviker. | En ändrad v1-algoritm kan ge validerings-/replayfel på gamla filer. |
| `network_core/import_verification.py` och `network_core/model.py::canonical_network_view` | Baslinje/replay innefattar nätverkets sparade X/Y och SHA-256. | Positionsändring är en dokumenterad projektändring, inte osynlig kosmetik. |
| `network_core/csv_import.py`, `spreadsheet_schema.py`, `xlsx_import.py`, `ods_import.py` | Strikta schema-1.0/1.3-tabeller har obligatoriska X/Y. | Ge aldrig gammal strikt import en ny dold tolkning. |
| `network_core/model.py::validate_project` | Kanoniska noder kräver ändliga X/Y inom [-100000,100000], högst 2 000 noder och högst 5 000 länkar. | En ny importväg måste skapa **presentationsvärden före validering**, inte försvaga modellen. |
| `web/canvas.js` | SVG: nodbredd `202`, höjd `max(96,66+23*portantal+12)`, portcentrum från faktiska portindex. Befintlig `route()` ger ortogonal SVG-bana. | Algoritmen måste använda **verklig nodstorlek**, och exakta portcirklar måste fortsatt möta kabelns ändpunkter. |
| `web/canvas.js::packetJourneyFrames` och `TopologyCanvas` | Reella, deklarerade kabel-ID:n används för animation; rendering/zoom/pan/drag fungerar i befintlig SVG-väg. | Inga parallella kabel- eller animationsträd. |
| `web/app.js` | Äger projekt, `workspaceRevision`, `editRevision`, Save/Open, fördröjda svar och canvas. | Ingen ny konkurrerande projekt-/session-state-manager; inget automatiskt omplacera-vid-render. |
| `docs/IMPORT_SOURCE_CONTRACT.md` | Skiljer källfakta från `derived_layout` och förbjuder härledda fysiska förbindelser. | Ett saknat kabelregister får inte fyllas i av grafisk layout. |

**Verifierad konkret geometririsk:** v1-rutnätets radavstånd är 220. En nod med 10 portar blir 308 hög och en med 128 portar 3 022 hög enligt aktuell SVG. Därför kan v1-noder överlappa trots korrekt nätverksimport. Detta är en geometriobservation, inte bevis för att hela renderern är felaktig.

### Våg 2 – extern algoritmforskning, inte bibliotekskopiering

- ELK Layered delar grafritning i bl.a. lager, nodordning, koordinattilldelning och kabeldragning; den stöder faktiskt ortogonal routing och explicita portar. Det finns därför **inget stöd** för att kalla ELK generellt oförmögen att dra ortogonala linjer. Källa: https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html och https://eclipse.dev/elk/blog/posts/2025/25-08-21-layered.html .
- OGDF:s översikt beskriver komponentpaketering, hierarkisk ordning och barycenter-/medianheuristiker. Exakt minimering av korsningar är i allmänhet ett svårt optimeringsproblem; **lovar inte optimalt minimum**. Källa: https://www.ogdf.uni-osnabrueck.de/wp-content/uploads/2019/04/ogdf.pdf (avsnitt om Sugiyama Framework).
- Graphviz dokumenterar begränsningar för ortogonal `splines=ortho` med portar. En extern biblioteksintegration är därför inte en bevisad genväg runt YadiLabs egna port-/SVG-kontrakt. Källa: https://graphviz.org/docs/attrs/splines/ .
- Föreslagen riktning är ett **litet, deterministiskt och begränsat algoritmflöde**: validerade explicita relationer → sammanhängande komponenter → stabil ordning/lager → storleksmedveten placering → mätning → befintlig SVG. Barycenter eller lokal omordning är villkorliga, mätstyrda optimeringar – inte ett automatiskt krav.

### Våg 3 – historiska risker och verifieringsgap

1. **Replay och SHA:** v1 ska vara byte-/semantikkompatibel; den gamla `node_layout()` får inte ändras, flyttas till annan semantik eller få nya standardparametrar. Historiska schema-1.4-kvitton ska fortsatt verifieras mot v1.
2. **Geometriskt kontrakt:** Pythonlayout och SVG måste dela verifierad nodstorlekssemantik. Undvik osynkroniserade, otestade dimensioner; inför om nödvändigt en liten, uttrycklig, versionsstyrd geometrispecifikation och paritetstest, **inte** en ny generell renderingsarkitektur.
3. **Klipp/zoom:** `canvas.fit()` och `zoom()` har andra begränsningar än modellens [-100000,100000]. Testa hela layoutens synlighet vid 2 000 noder i Chromium; numeriskt giltiga X/Y är inte samma sak som användbar skärmvy.
4. **Stora nät:** 2 000 noder/5 000 länkar och upp till 128 portar per nod kräver begränsad tid/minne. Undvik obegränsade kraftbaserade iterationer, korsningsjämförelser och djup rekursion.
5. **Tidigare ELK-historik:** äldre `YadiLab-n` och dess exakta felcommits har **inte** kunnat läsas via aktuell GitHub-anslutning. Inga specifika orsaker i den historiska implementationen anges därför som verifierade.

### Våg 4 – oförändrade regressionsgrindar

Utgångspunkt: huvudgrenens fulla Python-testsvit, `npm run check`, verklig Chromium/`tests/browser_smoke.py`, verkligt X11/`tests/browser_primary_selection_x11.py`, riktiga projektfiler och historisk Save/Open. Grön CI bevisar inte att ny layout är visuellt bra: nya geometritester och visuellt kontrollerade representativa fall behövs. Ingen av dessa grindar får försvagas.

## 2. Målkontrakt

**Måste fungera för en separat godkänd ny importväg:**
1. Användaren tillhandahåller och bekräftar **nätverksfakta**: deklarerade enheter, portar, kablar, VLAN, IP, routes, zoner inom det stöd som faktiskt finns. X/Y saknas tillåtet **i en framtida uttryckligt versionsstyrd importväg**.
2. YadiLab kan skapa en visualiseringslayout utan att hitta på några nätverksfakta. Enheter utan dokumenterade länkar får placeras som isolerade.
3. Samma validerade ingång, algoritmversion och parametrar ger samma heltalskoordinater, oberoende av filordning eller Python-hashordning. Ingen slump utan explicit, bevisat deterministisk strategi.
4. Placeringen ska respektera faktiska SVG-nodrektanglar, portantal och marginaler; **inga nodrektangelöverlappningar** på godkända representativa testfall. Om gränser gör problemet omöjligt: explicit layoutfel, ingen partiell success eller nodförlust.
5. Topologin ska framgå läsbart inom en avgränsad ambitionsnivå; lägre kabelkorsningsantal är ett mätvärde, inte garantin om globalt optimum.
6. Alla ursprungliga node-/port-/link-ID:n, ordning och aktiv/inaktiv-status bevaras. Kabelsidesval och animation använder samma synliga portpunkter och befintliga deklarerade länkar.
7. Före explicit användargodkännande: **ingen mutation** av projekt, baseline, lagrade filer, revisioner eller sessioner. Vid godkännande tillämpas endast de avsedda presentationskoordinaterna; Save är fortfarande separat.
8. Ingen omplacering vid `render()`, vanlig Open, Save, protokollberäkning, felsimulering, scroll, pan/zoom eller historisk replay.
9. Äldre schema-1.0/1.3-strikta importer, alla v1.4-kvitton och redan sparade projekt måste ge samma resultat enligt de gamla kontrakten.

**Utanför scope:** nya nättopologier, automatisk port-/kabelupptäckt, LLDP-inferens, protokollmotor, geografisk eller rackfysisk placering, grafdatabas, ELK/Graphviz/Dagre, React/React Flow, ny eventbus, ny state manager, nytt Save-flöde, generell refaktor av `app.js`, `canvas.js` eller `import_plan.py`. Zon och nodtyp får användas som **visuella heuristiker**, aldrig som nätverksbevis.

## 3. Arkitektur som Codex måste bevara

**En beräkning, en ägare:** Ny v2-layout ska vara en **ren, isolerad presentationsfunktion** med explicit gräns, exempelvis en ny `network_core/presentation_layout_v2.py` för serverberäknade importkandidater. Namn/filsökväg är endast en kandidat, inte tillstånd att ändra importmotorn i LA-01. Ingen dold JS-kopia av samma algoritm. Frontend är ansvarig för SVG-rendering, preview och godkännande; backend fortsätter ansvara för kanonisk importvalidering och historisk replay.

**Ingång (framtida funktionskontrakt):** Kopior av explicit godkända nod-ID:n, nodtyper, zonmedlemskap, portantal/verifierad nodgeometri samt **endast deklarerade** länkar med exakta ändpunkter. Länkar får användas som visuella relationer även när deras `enabled=false`; de är då fortfarande deklarerade kablar och får aldrig tolkas som aktiv paketreachability. Utan länklista: diskreta/fristående noder och deterministisk rutnätslayout. Ingen datainsamling från okända IP-adresser, etiketter eller visningspositioner.

**Utgång:** sorterad, komplett `nodeId → {x:int,y:int}`-mappning + begränsad diagnostik/metrik + versionsidentitet. Inga okända ID:n, inga ofullständiga positioner, inga icke-ändliga tal, inga sidoeffekter. Fel ger status/diagnostik, aldrig “PASS med gamla eller halva resultat”. Bevisa modelgränsen [-100000,100000] och att layoutens rektanglar ryms inom vald verifierad arbetsyta.

**Dimensioner:** Lås en prövbar paritetsregel mot den befintliga `canvas.js`-geometrin (`WIDTH=202`, `HEIGHT=max(96,66+23*portantal+12)`, portindex samt portpunkternas offset). Innan v2 används i import måste Python och Chromium ha testad samma storlekssemantik; välj minsta möjliga synkroniseringsmekanism efter en isolerad analys. Ingen automatisk plattforms-/ramverksmigration.

## 4. Etappindelning – en liten PR åt gången

### LA-00 – skrivskyddad baslinje och oberoende negativa tester

**Tillstånd:** AUDIT + TEST/EVIDENCE, inte NARROW_FIX. Förankras i QUALITY-000, -006 och -008.

- Dokumentera faktisk dataflödeskarta: inspektionsdata → importplan → v1 `node_layout` → validated project → `importEvidence` → `canvas.js` → Save/Open/replay.
- Ta fram sanerade, syntetiska referensfall: isolerade noder, kedja, stjärna, träd, ring, meshnät, redundanta länkar, avstängd kabel, flera zoner, validerad nod med 0/10/128 portar, oordnade ID:n, 47/92/46-liknande teststorlek, 100, 500 och 2 000 noder samt upp till 5 000 länkar.
- Bevisa observerad v1-överlappning (minst två högre noder i samma kolumn) utan att ändra koden. Dokumentera hur zone-rects, fit, pan och portar beter sig.
- Golden-tests: exakt v1-koordinatsekvens; gamla giltiga schema-1.4-projekt och `evidence_status`/`verify_sources`; historiskt `baselineNetworkSha256`, plan-fingerprint; strikt CSV/XLSX/ODS; identiska filbytes utan Save. Ingen verklig företagsdokumentation i GitHub.
- Mät initial beräkningstid/minne, faktisk Chromium-visualisering och canvas-geometri; inga påhittade prestandavärden.

**Acceptans:** referensmatris och minst ett reproducerbart geometriskt problem eller tydlig förbättringshypotes. Om sådan evidens saknas: STOP/NOT_VERIFIED, inte kod på chans.

### LA-01 – ren storleksmedveten layout v2, utan anropare

**Tillstånd:** separat uttryckligt godkänd NARROW_FEATURE/CONTRACT-ändring, enbart ny isolerad modul och dess nya testmodul.

- Ingen redigering av `node_layout` eller de fem kanoniska import-/proveniens-/storage-komponenterna. Inga nya beroenden.
- Börja med deterministisk storleksmedveten rad-/kolumnpackning. Marginaler och radavstånd måste utgå från maximal verklig nodhöjd i respektive rad, inte fast 220.
- Testa samma-ID-flera-gånger, okänt ID, nodmängd över gräns, omkastad källordning, 0/10/128 portar, negativa koordinater, precision, 2 000 noder, upprepade beräkningar.
- Output kontrolleras oberoende av implementationen med en rektangelöverlappnings-orakel och numerisk validator. Nära resursgränser får `LAYOUT_UNSUPPORTED` eller motsvarande definierat fel, inte osynlig nedskalning.
- Jämför alla godkända exempel med v1: zero overlap och mätbar utveckling; bevara v1 orörd.

**Acceptans:** fullständig, stabil koordinatmappning utan sidoeffekter. Inget UI, inget API, ingen ändring av import- eller sparbeteende.

### LA-02 – topologimedveten placering som valbar v2-strategi

**Tillstånd:** egen separat PR, endast efter LA-01 verifierats.

- Utgå från endast deklarerade länkar; bygg en **oriktad presentationsgraf** med stabil komponentidentifiering (inklusive fristående noder). Riktnings-/hierarkival är visuell heuristik, aldrig en påstådd nätverksroll.
- Prova på representativa fall en stabil BFS-/centrumbaserad lagerindelning eller en enkel komponentbaserad strategi. Sortering och tie-break avgörs uttryckligen, inte av objektordning/slump.
- Använd port-/nodstorlekar och komponentmarginaler. Begränsade (först efter mätning högst ett fåtal) barycenter-/medianpass kan optimera ordning när det **mätbart** minskar korsningar utan att öka nodöverlappningar.
- Ingen generell kraftsimulator, okontrollerad rekursion, exponential backtracking eller O(E²)-optimering för stora nät. Alla loopar/gränser tydligt specificerade och mätbara.
- Om topologimetoden inte kan ge bättre eller lika säker layout på ett fall: returnera verifierat v2-storleksrutnät eller explicit layoutdiagnostik **med synlig metodidentitet**, inte tyst “perfekt” resultat.

**Acceptans:** för varje representativ klass inga förlorade noder/länkar, inga nodöverlappningar, determinism och förklarlig presentation; en faktisk förbättring mot LA-01 på fastställd referenskorpus krävs innan komplexitet accepteras.

### LA-03 – isolerad förhandsvisning och explicit “Ordna automatiskt”

**Tillstånd:** egen UI-/API-PR efter LA-02 eller stabil LA-01. Ingen importkontraktsändring än.

- Planera ett skrivskyddat layoutförslag från en **fullständigt validerad kopia** av det nuvarande projektet; kontrollera att förslagets node-ID:n exakt matchar snapshot.
- Integrera endast via nuvarande `app.js`-ägarskap. Snapshot + `workspaceRevision` + `editRevision` + projektfingerprint måste matcha både när svar mottas och vid användarens godkännande; föråldrat svar får inte tillämpas. Testa ändring, New, Open, Import, fel, cancel och två överlappande förslag.
- Preview får inte ändra arbetsyteprojekt, Save-baslinje, urklipp, selektion, diagnostiksessionslivscykel eller sparade filer. Godkännande är **en explicit koordinatredigering**: ändra bara X/Y en gång, kör etablerad revisions-/dirty-logik och lämna Save separat.
- Om ett befintligt schema-1.4-projekt med historiskt kvitto arrangeras om är `CHANGED_SINCE_IMPORT` ett **korrekt och öppet redovisat** utfall; gör inte om historiskt kvitto för att påstå oförändrad källa.
- Använd befintlig `TopologyCanvas`; ingen automatisk omplacering vid `render`, Open, Save, zoom eller ping. Ingen parallell SVG-kopia får bli den auktoritativa projektmodellen.

**Acceptans:** riktiga Chromium-interaktioner och manuell godkännande-/avbryt-konsekvens; exakt oförändrade nätverksfält utom valda X/Y; oförändrade sparade bytes utan Save; fulla regressioner.

### LA-04 – verklig X/Y-fri dokumentationsimport med versionsstyrd proveniens

**Tillstånd: CONTRACT/BREAKING_CHANGE – **kräver en separat uttrycklig användarorder och ny normativ importspecificering**, även om LA-01–03 är gröna. Ingen implicit implementering.**

- Bevara exakt befintlig strikt schema-1.0/1.3-import med obligatoriska X/Y och befintlig schema-1.4 layout-/replaysemantik.
- Föreslå en **tydligt valbar ny importprofil/version** där externa inventeringsblad saknar X/Y, men explicita nätverksobjekt, användarbekräftad mappning och fullständig fail-closed-validering kvarstår. Återanvänd befintlig källinspektion, `ImportPlan`, claims, konfliktgrindar och kanonisk `validate_project`; skapa inte ny parallell importmotor.
- Den nya versionen ska beräkna layout från exakt validerad och uttryckligen vald kandidat, inte från oklara avvisade eller exkluderade källrader. Ingen IP-adress, namn, zon, LLDP-text eller position får skapa nätverkslänk.
- **Versionsväljning för kvitto/replay måste beslutas före kod**: t.ex. en uttrycklig ny layoutPolicy/import-/evidence-version eller ett nytt projektschema efter användargodkänt kontrakt. Gamla kvitton måste alltid dispatchas till oförändrad v1-kod, nya till versionerad v2 med stabila parametrar. Inga automatiska migrationer och ingen tyst omskrivning av `baselineNetworkSha256`.
- Negative gates: saknade ID:n/portar/kablar som behövs för avsett arbete ger BLOCKED, inte en fullt fungerande men påhittad simulatortopologi. Valfria koordinater ersätter **inte** krav på faktiska nätverksuppgifter.

**Acceptans:** nya X/Y-fria, anonymiserade syntetiska XLSX/ODS/CSV-exempel importeras via godkänd ny väg och labbas enligt deklarerad nätverksmodell. Gamla strict/importEvidence-filer fungerar byte-identiskt. Historisk återspelning ger MATCH enligt rätt layoutversion; i annat fall STOP, inte migration i smyg.

### LA-05 – villkorlig förbättring av ortogonal kabeldragning

**Tillstånd:** INTE automatiskt planerad kod; endast om konkreta testbevis visar att befintlig `route()` är otillräcklig efter nya nodpositioner.

- Behåll exakta portcentrum och varje befintlig kabels identitet. Om ett problem finns: börja med en liten ren routningsfunktion eller geometrisk korrigering, utan egen paketmodell.
- SVG-banan för synlig kabel och `getPointAtLength()`-uppspelning måste avse samma verkligt deklarerade länk. Kontrollera båda ändpunkter geometriskt i faktisk Chromium-render, även efter pan/zoom, nodflyttning, inaktiva länkar och nya layoutförslag.
- Inga nya påståenden om garanterat korsningsfri routing. Om kabeln korsar en nod, mät och dokumentera; inför inte global ortogonal router utan isolerad ny auktorisation och bevis för nytta.

### LA-06 – oberoende slutgrind och releasebeslut

- Oberoende korrekthetsgranskare jämför gamla och nya projekt, VLAN/ARP/IPv4/ICMP/DHCP, Save/Open, source-replay, kopplade kablar, geometri och användarkontroller före/efter.
- Fullt testmatrix: 1,4,5,10,50,100,500,2000 noder; upp till 5000 länkar; 0,10,128 portar; stjärna, kedja, träd, ring, mesh, parallella deklarerade länkar, fristående noder, flera zoner, inaktiva länkar, samma filer i omkastad rad-/ZIP-ordning. Alla ligger inom uttryckligen stödda modellgränser.
- Prestandamål bestäms först efter LA-00-baslinjen. Separera mål för serverns layouttid, minne och Chromium-interaktivitet. `2 000` är en valideringsgräns, **inte** bevis för att varje tänkbar 2 000/5 000-topologi blir snabbt och läsbart på en skärm.
- Kör `python3 -m unittest discover -s tests -p 'test_*.py' -v`, `npm run check`, riktiga `tests/browser_smoke.py`, och `xvfb-run -a python3 tests/browser_primary_selection_x11.py` där den är relevant; obligatorisk GitHub Actions på exakt PR-HEAD och efterföljande squash-merge-SHA på skyddad `main`.
- Inga gamla positiva/negativa regressioner får raderas, “xfail”-märkas eller ge fallback till mockad browser. Visuella geometrikrav måste kontrolleras maskinellt **och** med representativa skärmbilder; skärmbilder ensamma är inget facit.

## 5. Absoluta stoppregler för Codex

1. **Ingen direkt ändring av** `import_plan.py::node_layout`, `import_evidence.py` eller `canonical_network_view` för att “snabbt slå på v2”. Historisk import ska alltid kunna återskapas.
2. **Ingen gruppändring** av import + historisk proveniens + format + `app.js` + `canvas.js` + routing i en PR. Varje kod-PR har exakt ett syfte och en namngiven testbar acceptans.
3. **Ingen ny komplett grafmotor** eller ELK/Graphviz/Dagre/React Flow, inga dynamiska import-/renderingsberoenden, ingen ny projektmodell.
4. **Ingen härledning av nätverksfakta från layout** – inga uppfunna kablar, portar, IP-adresser, gateways, VLAN, routes, upptäckt/fungerande reachability.
5. **Ingen tyst layout vid render/Open/Save/replay**; manuellt placerade noder ska stå kvar. Ingen dold uppgradering av sparade projekt eller källkvitton.
6. **Inga självbekräftande geometriska tester.** Oberoende rektangelkollision, bevarade ID:n, exakta SVG-portpunkter, gränsvärden och reella browserflöden krävs.
7. **Ingen automatisk performance-success.** Stopp vid överdriven beräkning, minne, gräns eller otillräckligt resultat. Returnera diagnostik, inte halvt projekt.
8. **Ingen försvagning** av Python/JS/Chromium/X11, GitHub ruleset, CI, Safe Save, SHA-256, konfliktkontroll, importblockerare eller stale-response-skydd.
9. **Ingen obehörig kunddata i repository**. Testning använder artificiella, anonymiserade filer.
10. **Ingen etappeskalering utan separat användarbeslut.** Om LA-01 inte kan nå sina mål: rapportera FAIL/NOT_VERIFIED, föreslå begränsad åtgärd och stoppa. Om LA-04 kräver nytt schema: inhämta uttryckligt godkänt kontrakt före ändring.

## 6. Krav på varje Codex-rapport/PR

Ange `BASE_SHA`, exakt `HEAD_SHA`, modifierade filer, vilket avgränsat problem som avhjälpts, icke-mål, beroenden, testdata (syntetiska/avidentifierade), geometriska mätningar före/efter, identitets-/proveniens-/Save-/simuleringsinvarians, CI-URL och verklig status, återställningssätt och separat nästa beslut. PASS, FAIL, NOT_VERIFIED och UNSUPPORTED ska skiljas. En dokument-PR får inte rapporteras som en implementerad layoutfunktion.

**Rekommenderad första implementationsorder – först efter användarens uttryckliga godkännande:** LA-00, skrivskyddad och testspecifik kartläggning av verkliga nodöverlappar och historiska kvitton. **Ingen ELK-installation, ingen importändring och ingen ombyggd canvas.**
