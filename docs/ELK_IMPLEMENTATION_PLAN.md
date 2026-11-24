# ELK-arkitekturen – historisk kodplan och giltiga layoutinvariants

> **AKTUELL STATUSKORRIGERING 2026-11-24 (LÄS FÖRE ALLA ARBETSKORT):** ELK-06A, ELK-06B och ELK-06C är redan **squash-mergade** genom PR #94–#96 den 2026-11-22. Den tidigare baslinjens påståenden om att strikt CSV/XLSX/ODS fortfarande kräver X/Y, att automatisk första ELK saknas och att export fortfarande skriver X/Y är **historiska och felaktiga som nutidsbeskrivningar**. Äldre ”nästa PR”-instruktioner och prioritetstabeller i denna fil är **arkiverade arbetskort, inte nya exekverbara order**. Kontrollera aktuell kod, [SPREADSHEET_V13.md](SPREADSHEET_V13.md), [AGENTS.md](../AGENTS.md) och tester vid framtida korrigeringar. Bevara bakåtkompatibilitet, kanonisk projektgeometri, importkvitton, ELK-worker, SVG och separat Save. Nya koduppdrag följer fortfarande QUALITY-roadmap och separat användarbeslut. Pedagogikbeslutet [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md](PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) **ändrar inte** ELK-motorn.

**Status:** Historisk ELK-arbetskö från 2026-11-22; tekniska dataintegritets- och layoutinvariants gäller fortsatt, men genomförda 06A–C är INTE framtida arbetsorder.  
**Version:** 2.0, 2026-11-22.  
**Nulägesankare:** `main@eac31c4b8e47b021f1b67dc66aab22165cc83afc`; kontrollera ny HEAD inför varje PR.  
**Prioritering:** **fungerande produktionskod snabbt**, inte fristående forskning, rapporter eller teoretiska prototyper.  
**Styrande överordnade regler:** `AGENTS.md`, `docs/MASTERPROMPT.md`, `docs/IMPORT_SOURCE_CONTRACT.md` och kvalitetsfärdplanen `docs/QUALITY_IMPROVEMENT_PLAN.md`. Denna plan är en **konkret ELK-arbetskö**, inte en andra konkurrerande QUALITY-färdplan.

> **Huvudregel för Codex:** Välj nästa relevanta, specificerade, ännu inte implementerade **användarfunktion eller verifierade felrättning**. Skriv minsta möjliga produktionskod och de tester som bevisar den. Leverera en körbar PR. Avsluta inte en aktiv etapp med enbart en arkitekturrapport, ett forskningsresultat, en test-PR eller en ny lista med hypoteser. Om något redan fungerar: **KEEP och gå direkt vidare**. Ingen fristående forskningsgren utan ett konkret blockerande problem i den aktuella kodändringen.

## Bindande grundregel: källdokument ska inte behöva X/Y

**Externa nätverksdokument (CSV/XLSX/ODS och mappade källtabeller) ska inte behöva innehålla nodkoordinater `x` eller `y`.** Användaren ska aldrig uppmanas att lägga till sådana kolumner, fylla i manuella koordinater eller använda en layoutmall för att få ett giltigt importerat diagram. Källdokument anger nätverksfakta och explicita fysiska kabeländar; **ELK ansvarar för den första användbara visuella placeringen** efter uttryckligt godkänd import. Inget ytterligare layoutklick eller layout-Apply. Endast en senare omorganisation av en manuellt skapad eller redan placerad topologi är valfri.

**Tre skilda koordinatbegrepp får aldrig blandas ihop:**
1. **Källcellsadresser** såsom `B12` eller rad/kolumn i en XLSX-/ODS-/CSV-läsare identifierar var ett dokumenterat faktavärde kommer ifrån. De är *inte* nodernas visuella X/Y.
2. **Kanoniskt projektschema** kräver fortfarande interna nodfält `x/y` för att kunna rendera och validera en projektfil. Den initiala importkandidaten får dessa värden genom en **intern deterministisk presentationsplacering**, aldrig ett krav på källdokumentets kolumner. Bevara historisk `node_layout()`, dess provenance och befintliga replay.
3. **ELK:s beräknade koordinater** är en senare, automatisk presentationsförbättring av den redan godkända och atomärt tillämpade importen. Ingen ändring av nätverksfakta, fysiska länkar eller originalbytes. Separat Save krävs fortfarande.

**HISTORISK BASLINJE – KORRIGERAD I ELK-06A / PR #94:** Vid den ursprungliga 2026-11-22-granskningen krävde strikt CSV/XLSX/ODS-import X/Y. Den bristen har därefter rättats. Aktuell kod accepterar koordinatfria nätverksdokument; äldre kompletta X/Y-par kan fortfarande läsas för kompatibilitet. Den tidigare beskrivningen av en olöst implementeringslucka gäller alltså **inte längre**. Kontrollera aktuell kod och tester innan nya åtgärder.

**Bindande testgrind:** ett verkligt `Devices.csv` och verkliga XLSX-/ODS-arbetsböcker med deklarerade enheter, portar och kablar, men **utan X/Y-kolumner**, ska kunna godkännas i det avsedda importflödet och resultera i ett färdigt automatiskt ELK-diagram. Testa både äldre strikt format och flexibel mappad källimport, även med Save/Open, negativa kabel-/portfall och dokument med celladresser som inte misstolkas som visuella koordinater.

**HISTORISK BASLINJE – KORRIGERAD I ELK-06C / PR #96:** Den ursprungliga granskningen fann att äldre XLSX/ODS-exporter och mallar skrev X/Y. Nya dokumentationsexporter och mallar är numera koordinatfria; kanoniska projektfiler sparar fortsatt presentationskoordinater. Återinför inte obligatoriska X/Y-kolumner i nätverksdokument.

**HISTORISK beroendekedja (baslinje före ELK-06A–C):** Filsymboler och dåvarande uppgifter nedan är arkiverad genomförandeanalys; de beskriver inte automatiskt den aktuella implementationen:
- Strikt CSV: `csv_import.TABLES['Devices.csv']`, `_read_table()`, `_coordinate()`, `import_csv_tables()`.
- Strikt schema 1.0/1.3 XLSX/ODS: `spreadsheet_schema.TABLES/V13`, `columns_for_sheets()`, `import_spreadsheet_tables()`, `xlsx_import._sheet()`, `ods_import._sheet()`. Parserna antar **en fast kolumnbredd innan headern validerats**; enbart ändring av `TABLES` räcker inte.
- Flexibel källimport: `import_plan.node_layout()` skapar **interna** preliminära koordinater; `import_evidence.py` kräver samma historiska värden i replay. **Frys dessa kontrakt**.
- Dokumentexport: `spreadsheet_export._serialize()/export_workbook()` och `spreadsheet_templates.SAMPLE/_cells()/_xlsx()/_ods()` innehåller X/Y. Exportens nuvarande kontroll `restored == canonical` går **inte** att behålla oförändrad när dokumentlayout utelämnas; ersätt med strikt jämförelse av dokumenterbara nätverksfält, inte en försvagad generell acceptans.
- UI: `web/app.js::importProjects()` hanterar strikt import, `web/features/projects/import-review.js::applyCandidate()` hanterar accepterad flexibel källimport. Import av en redan sparad `.yadilab`-/JSON-projektfil **ska inte** automatlayoutas. Befintlig `web/features/layout/elk.js` används, ingen ny motor.

**Ingen tyst omtolkning:** Ett validerat äldre dokument med båda X/Y-kolumnerna får fortsätta läsas för bakåtkompatibilitet, men framtida dokumentation kräver inte koordinater, och vid *ny dokumentationsimport* är ELK den avsedda slutliga placeringen. En ensam X- eller Y-kolumn, okända kolumner eller förlorade nätverksfält ska avvisas. Varken `schemaVersion` 1.0/1.3/1.4 eller historiska importerade kvitton skrivs om för att lösa presentationsfrågan.

## 1. Exakt önskat slutresultat

Användaren ska kunna importera en **fullständigt, explicit och källtroget validerad** nätverksdokumentation och **automatiskt få en första lättläst ELK-layout**, utan extra layoutklick, se kablar som verkligen slutar på de deklarerade portarna, redigera diagrammet med mus och tangentbord, använda samma topologi i simuleringsmotorn, spara och öppna projekt samt förstå vad som sparats och vilka visuella rutter som återberäknas. Stora diagram ska vara hanterbara utan att nätverksfakta eller historiskt importbevis förändras.

**Det är levererad applikationsfunktionalitet som mäts.** Kodrader, forskningsvågor, issue-antal, experimentvarianter och antal PR:er är inte framstegsmått.

## 2. Vad som redan finns – får inte byggas om

Följande är observerat på nulägesankaret, men status måste kontrolleras på aktuell HEAD:

| Befintlig funktion | Ägare | Skydda i varje PR |
|---|---|---|
| Pythonmodell med schema 1.0–1.4 och strikt validering | `network_core/model.py` | Kanoniska ID:n, gränser, okända fält, no implicit cables |
| Historisk flexibel import och källkvitto | `network_core/import_plan.py`, `import_evidence.py`, `web/features/projects/import-review.js` | Originalbytes, källreferenser, `canApply`, fingerprint, historisk replay |
| Lokal ELK 0.13.0 i Worker | `web/features/layout/elk.js`, `web/vendor/` | 2 pass, `MULTI_EDGE`, 0×0 `FIXED_POS`, full outputvalidering, abort, timeout |
| Manuell opt-in Preview → Apply → separat Save för befintliga projekt | `web/app.js`, `web/index.html` | Stale guard, inga writes under preview, Save/Open-kontrakt |
| Automatisk initial ELK-layout efter godkänd import | **GENOMFÖRD i ELK-06A–C, PR #94–#96** | Koordinatfri strikt dokumentimport, första automatiska ELK-layouten och koordinatfria dokumentationsexporter; aktuell kod och tester avgör fortsatt stöd |
| SVG, zoner, portpunkter, kabelbanor och packet playback | `web/canvas.js` | Alla visualiserade kablar har verkliga `link.id` och två portändar |
| Renderings- och kameraoptimering | `web/canvas.js` | PR #91–92 är redan integrerade; upprepa inte dessa projekt |
| Ordinarie CI, Chromium, X11, Save/Open | `.github/workflows/ci.yml`, `tests/` | Testa slutlig PR-HEAD; inga genvägar genom att inaktivera tester |

**Aktuella tekniska fakta:** nodbredd 202; nodhöjd `max(96, 78 + 23 × antal_portar)`; synlig port Y = `node.y + 71 + 23 × portindex`; X är vänster/höger nodkant enligt deklarerad kabelmotparts X. Projekttak i befintligt ELK-flöde: 2 000 noder, 5 000 kablar och 128 portar per nod. X/Y måste ligga inom ±100 000 och **hela nodrektangeln** måste rymmas. Bevara dessa regler tills ett uttryckligen godkänt kontraktsbyte finns.

## 3. Arbetsmetod – direkt kod, inga onyttiga forskningsspår

### 3.1 Obligatorisk arbetssekvens per PR

1. **Hämta verkligt läge en gång:** aktuell `main`-SHA, öppen PR, senaste obligatoriska CI, berörda existerande funktioner. Skapa ingen separat baslinje-PR.
2. **Välj användarnytta:** formulera synligt före-/efterbeteende och ett tydligt fel eller saknad användarfunktion från denna plan. Välj en uppgift som kan lösas utan ny arkitektur.
3. **Förbered direkt kodändringen:** namnge de få produktionsfilerna, nya regressionstesterna och vad som uttryckligen inte berörs.
4. **Implementera nu:** ändra produktionskod och anslut existerande komponenter. Undvik ramverksbyten, nya parallella motorer och att först skriva en lång rapport.
5. **Bevisa beteende:** enhetstest för fel och gränsvärden; riktig Chromium/HTTP/Save/Open där det är relevant; den gemensamma CI-kedjan.
6. **Leverera en PR:** beskriv konkret användarförbättring, faktisk diff, exakta tester, kvarstående begränsning och återskapbart testfall.
7. **Squash-merge enligt `AGENTS.md`:** enbart när hela obligatoriska CI är PASS på exakt HEAD, PR är konfliktfri och alla skyddsregler tillåter merge. Verifiera `main` och avsluta PR:n.
8. **Gå vidare till nästa nytta.** Skapa inte en kompletterande forsknings-PR, eller en ”status-PR”, bara för att ett kapitel finns i planen.

### 3.2 Hårda spärrar

- **Högst en aktiv utvecklings-PR/branch.** Ingen parallell forskning, parallell implementation eller experimentmatta med konkurrerande arkitekturvägar.
- **Ingen fristående forskning/analys/ADR som ordinarie leverans.** Kod och tester i samma PR. Ett enskilt, snävt experiment är tillåtet *inom* den pågående fixens testkörning endast när ett faktiskt kodhinder måste avgöras.
- **Inga ”test-only”-steg för att skjuta upp koden** om en konkret lösning och dess kontrakt redan är känt. Nödvändiga regressionstester följer med samma kod-PR.
- **Ingen gissning:** om en okänd detalj hotar dataintegritet, projektformat eller fysisk topologi ska Codex inte skriva på måfå. Stoppa endast den beroende deluppgiften, redovisa exakt blockerare och fortsätt med nästa oberoende koduppgift i prioriteringsordning.
- **Ingen ny schema-/import-/simuleringsarkitektur** utan separat uttryckligt användargodkännande. Fungerande delar är KEEP.
- **Ingen passiv CI-väntan i Codex-sessionen.** Kör relevanta lokala kontroller; om CI fortfarande körs, lämna PR öppen med exakt HEAD och länk. Ingen polling-loop eller nytt uppdrag för att fylla väntetid.
- **Automatisk initial placering är obligatorisk efter en accepterad import utan källkoordinater.** Den får endast omplacera redan deklarerade noder och beräkna visuell kabelgeometri utifrån redan deklarerade länkar. ELK får aldrig uppfinna kabel, port, nod eller routing utifrån IP, VLAN, zon eller grafnärhet.

### 3.3 Krav för att få säga ”klart”

En etapp är **IMPLEMENTED** endast när den har synlig eller programmässig produktionsfunktion, minst ett relevant positivt och negativt test, ingen känd regression, grön obligatorisk CI på exakt HEAD samt verifierad integrering i `main`. Om befintlig kod redan uppfyller allt: markera **KEEP/ALREADY_IMPLEMENTED** i nästa kod-PR:s notering och **hoppa över** etappen; skapa ingen no-op-PR.

## 4. Historisk leveransordning – 06A–C redan integrerade

Följande är **arbetskort**, inte order om fjorton PR:er. Identifikatorerna ELK-00–ELK-13 behålls för spårbarhet mot tidigare arkitekturdokument. **Arbetskort med ingen kvarvarande kodändring hoppas över.** När två angränsande kort påverkar samma lilla användarflöde får de ingå i **en** begränsad PR; stora ändringar delas.

| Körordning | Arbetskort | Faktisk kodnytta | Startvillkor |
|---|---|---|---|
| 1 | **ELK-06A** | **Koordinatfri strikt dokumentimport:** CSV/XLSX/ODS utan X/Y i schema 1.0/1.3 | Bygg på befintlig parser och atomär validering; riktigt testade importer; historiska filer fortsätter fungera |
| 2 | **ELK-06B** | **Automatisk första ELK-layout** efter accepterad strikt eller flexibel dokumentimport, utan andra klick | 06A merged; återanvänd befintlig Worker och stale-guards; inte för projekfil-Open eller manuellt byggd topologi |
| 3 | **ELK-06C** | **Koordinatfri dokumentexport, mallar och CSV-exempel** utan falskt löfte om exakt projektroundtrip | 06B merged; särskilj dokumenterbara nätverksfakta från intern X/Y och behåll `.yadilab`-backup |
| 4 | **ELK-04 + ELK-05** | Korrekt edit/drag/livscykel: ingen falsk eller föråldrad kabelgeometri | Bevisa ett konkret användarfall som saknar detta; annars KEEP |
| 5 | **ELK-09** | Tangentbord, fokus och begriplig tillgänglig layoutkontroll | Befintliga Builder-flöden granskas *inom samma kod-PR* |
| 6 | **ELK-02 + ELK-03** | Adapter som klarar specificerade felaktiga indata och grafklasser | Lägg bara till kod när ett negativt test visar ett faktiskt gap |
| 7 | **ELK-08** | Responsiv interaktion i stora verkliga vyer | Mät reproducerbart aktuellt flaskhalsfall, åtgärda samma PR |
| 8 | **ELK-07** | Tydlig och korrekt Save/Open-upplevelse för tillfälliga kabelbanor | Behåll nuvarande projektformat; ändra inte schema utan nytt mandat |
| 9 | **ELK-10** | Verifierat självständigt offlinepaket och korrekt licensdistribution | Ingen spontan biblioteksversionhöjning |
| 10 | **ELK-11** | Riktig importerad testkorpus + fungerande slutanvändarflöde | Endast källor med uttryckligt tillstånd och tillåten anonymisering |
| 11 | **ELK-12** | Reproducerbar release, rollback och kort användarmanual | Alla funktionella beroenden gröna |
| 12 | **ELK-13** | Slutlig integrerad acceptans i vanlig CI, utan revision som sidoprojekt | Samtliga relevanta användarscenarier testade |

**ELK-00 och ELK-01 är inte fristående arbetsfaser**: de representerar snabb HEAD-kontroll och oberoende testfacit som bakas in i varje riktig kod-PR. Lägg aldrig upp egna forsknings-/test-PR:er för dem.

## 5. Historiska arbetskort – får inte återstartas utan nytt kontrakt

### ELK-00 – Baslinje ingår i varje koduppdrag, ingen PR

**Gör:** läs `AGENTS.md`, `docs/MASTERPROMPT.md`, detta dokument och berörda modulkontrakt. Kontrollera aktuell HEAD/CI/öppna PR:er. Bekräfta att en tänkt ändring inte redan finns i koden eller tidigare merge.

**Leverans:** 3–6 meningar i kod-PR:n med baseline-SHA, vad som saknas och vad som ska ändras. **Ingen** separerad forskningsfil, inventeringsrapport, issue-bunt, diagramuppsats eller baslinjegren.

**Stopp:** om `main` är röd på ett sätt som direkt påverkar uppgiften: åtgärda det verifierade felet i en egen liten kod-PR. Om annan PR redan pågår: arbeta i den eller avsluta, skapa inte parallell gren.

### ELK-01 – Testfacit byggs tillsammans med produktionskoden, ingen test-only-PR

**Gör:** för varje konkret kodändring lägg in en minimal positiv och en negativ fixtur, med *oberoende* förväntat värde. Exempel: hela rektangeln i ±100 000, portens exakta (x,y), kabelns verkliga `link.id`, samma deklarerade portändpunkter efter Save/Open och att `enabled:false` fortfarande är inaktiv i simuleringen. **Använd aldrig motorns egen output som enda förväntan.**

**Nya tester vid behov:** `tests/elk_layout_adapter_test.mjs`, `tests/browser_elk_layout.py`, ytterligare snäva fall under `tests/` utan att duplicera en fullständig testkorpus.

**Leverans:** test som först reproducerar felet och därefter passerar efter produktionsfixen. **Ingen** fristående rapport eller 200-fixturerskatalog om aktuell ändring gäller två portar.

### ELK-02 – Resilient ELK-adapter och korrekt Worker-livscykel

**Utgångspunkt:** `web/features/layout/elk.js::computeElkPreview` har redan sortering, två pass, Worker, timeout/abort, cloning och outputgrindar. **KEEP tills reproducerat fel finns.**

**När verklig brist observeras:** ändra enbart `web/features/layout/elk.js` och närmast relevanta `tests/elk_layout_adapter_test.mjs`; om felmeddelande måste visas även `web/app.js`. Implementera validering av det felaktiga ELK-svaret eller avbrutet tillstånd. Säkra identiska nod-/port-/link-ID:n, oförändrad 0×0 `FIXED_POS`, finita koordinater, exakt sektion per kabel, ortogonal rutt och rätt portcentrum. Worker ska termineras även vid misslyckande.

**Negativa fall:** extra/noll nod, ändrat port-ID, port-förskjutning, bortfallen kabelsektion, NaN/Infinity, timeout och abort, svar efter workspace-byte. Förväntan: ingen Apply och inga diskändringar.

**DoD:** reproducerat fel avhjälpt, negativ regression grön, riktig Chromium där UI berörs, ingen schemaändring. Om inga sådana fel kvarstår: **KEEP – ingen PR**.

### ELK-03 – Geometrisk kvalitet utan andra layoutmotorn

**Utgångspunkt:** tvåpass-ELK Layered + `MULTI_EDGE` + `ORTHOGONAL` + nollstora `FIXED_POS`-portar. All befintlig layoutkod behålls.

**Konkret kodarbete endast vid fel:** lägg till ett begränsat grafscenario som reproducerar t.ex. portsidans oönskade ändring, kabel genom orelaterad nod, duplicerat ID, icke-ortogonalt segment eller sammanhängande komponent som inte kan godkännas. Justera en dokumenterad ELK-option eller en adapterregel i **samma PR**; inte bygga egen motor. Om ELK inte klarar det: begripligt avslag och fungerande ordinarie SVG-visning, hellre än påhittad kabel.

**Tester:** träd, ring, stjärna, mesh, frånkopplade komponenter, porttät nod och omvänd nod-/länkordning **bara i den omfattning ändringen berör**. Inga universella prestanda-/korsningsmått får hittas på. En ny option måste jämföras på tidigare godkända 3-, 47- och 2 000-nodersfixturer där tillämpligt.

**DoD:** korrekt geometri eller uttryckligt felmeddelande, identiska kanoniska noder/portar/länkar, stabilt gamla funktioner. **KEEP** vid frånvaro av reproducerad defekt.

### ELK-04 – Manuell nodredigering och konsekvent kabelgeometri

**Problem att lösa som produktfunktion:** användaren ska kunna flytta noder utan att gamla ELK-rutter syns som om de fortfarande satt fast vid portarna. Nuvarande design ogiltigförklarar ELK och återgår till standardroutning vid redigering. **Detta beteende är korrekt tills ett alternativ faktiskt implementerats.**

**Kodscope:** `web/app.js` för invalidation och status; `web/canvas.js` för synlig `path.network-edge`, `path.edge-hit`, portpunkter och paketanimation; relaterade browser-tester. Lägg till en tydlig återaktiveringsåtgärd/indikator **endast om ett verifierat UI-gap finns**; återanvänd befintliga knappar i stället för att skapa extra navigationssystem.

**Förbjuden genväg:** anropa ELK Layered som om den skulle omdirigera enbart kanter med absolut låsta manuella nodpositioner. Inte heller introducera Libavoid, Cytoscape eller en egen router i denna PR.

**DoD:** drag slutar vid exakt synligt portcentrum, pek-/träffbanan och paketanimationen överensstämmer, inga falska permanenta ELK-rutter; Save/Open bevarar data. Förbättringen går att använda med mus i riktig Chromium. Om allt redan finns: **hoppa över**.

### ELK-05 – Fullständig Preview/Apply/Cancel/New/Open/Save-race

**Utgångspunkt:** `web/app.js` äger `elkPreview`, `elkAccepted`, `elkBusy`, `elkGeneration`, `workspaceRevision`, `editRevision` och `transferContext/transferCurrent`. Duplicera inte denna state manager.

**Kodscope:** endast berörda handlers i `web/app.js` plus `tests/browser_elk_layout.py` och eventuellt en liten extraherad hjälpfunktion när det minskar faktisk komplexitet. `worker.signal` ska inte medföra skrivning från ett gammalt svar.

**Beteendekrav:**
- Preview måste vara skrivskyddad och får aldrig Save:a.
- Cancel återgår till samma kanoniska projekt och rätt dirty-status.
- Apply kontrollerar aktuell workspace-revision, edit-revision, filnamn och projektfingerprint och uppdaterar bara befintliga X/Y.
- Save under pågående preview blockeras tydligt.
- New/Open/Import/dragning under pågående Worker gör gamla resultat obrukbara.
- Om en asynkron import eller annan mutation sker samtidigt får båda inte vinna atomärt.

**Test:** riktiga HTTP + Chromium-scenarier med fördröjd Worker, Abort, Cancel, Apply, Save/Open och Byte-Of-Project jämförelse. Inga mockresultat som bevis för verklig Save/Open. **Implementera bara en verifierad återstående lucka**; annars KEEP.

### ELK-06 – HISTORISK leverans som redan genomförts i PR #94–#96

**Mål:** En konsultrapport eller dokumentationstabell är nätverksdata, inte en ritning. CSV/XLSX/ODS **utan** nodkolumnerna X/Y ska accepteras när alla nödvändiga nätverksfakta är giltiga. Appen skapar först intern, giltig temporär geometri och använder sedan **ELK automatiskt** för den första synliga layouten efter godkänd import. Senare om-layout av en manuellt ritad eller redan placerad topologi är valfri. Genererade dokumentationstabeller och mallar blir också koordinatfria. **Det kanoniska projektformatets X/Y bevaras** för Save/Open. Inga nya import- eller layoutmotorer.

**Etappindelningen nedan är konkreta kodleveranser, inte forskningsuppdrag.** Utför A → B → C i en PR åt gången. Gör inte en forskning-/rapport-/test-only-PR mellan dem. Slå bara ihop koduppgifter om den sammanhängande diffen fortfarande är liten och samtliga tester redan kan bevisa leveransen. Varje kod-PR ska innehålla negativa tester och full CI-verifiering på exakt HEAD.

#### ELK-06A – HISTORISKT arbetskort; implementerat i PR #94

**Förväntat användarbeteende:** `Devices.csv` och `Devices`-blad får ha **exakt** `id,label,kind,zoneId` i valfri kolumnordning. Kolumnerna `x,y` får **inte krävas**. Alla övriga explicita kolumner, port-ID:n, länkar, VLAN, MAC, IP och routes valideras lika strikt som tidigare. Ett gammalt format med exakt `id,label,kind,x,y,zoneId` får fortsatt accepteras **enbart för bakåtkompatibilitet**, inte för att driva framtida layout. `x` utan `y` eller `y` utan `x` är ogiltigt. Inget gissande från kolumnpositioner, IP, nodnamn eller andra källfält.

**Filer att ändra vid behov:** `network_core/csv_import.py`, `network_core/spreadsheet_schema.py`, `network_core/xlsx_import.py`, `network_core/ods_import.py`. Tydliga positiva och negativa tester i `tests/test_csv_import.py`, `tests/test_xlsx_import.py`, `tests/test_ods_import.py`, `tests/test_web_import_graph.py` och befintliga riktiga ZIP-fixturer. Ingen ny importerare och ingen ny kanonisk schemaVersion.

**Konstruktion och ordning:**
1. Dela *inputheader-kontraktet* i exakt tillåtna koordinatfria och äldre parvisa koordinatbärande `Devices`-header-varianter. Behåll strikta headerkontroller för alla övriga blad. Avvisa extra/dubblerade/halva fält, även när kolumnerna är omordnade. Verifiera data med de faktiska validerade kolumnnamnen, inte genom att anta en given bredd.
2. `csv_import._read_table()` måste kunna välja tillåten `Devices.csv`-variant från den faktiska headern. `spreadsheet_schema.columns_for_sheets()` räcker inte ensamt, eftersom XLSX-/ODS-parserna begränsar kolumnbredd och typkontroller innan headern tolkas: lös det med en **avgränsad header-/variantavläsning i samma parser**, fortsatt begränsad av befintliga maxstorlekar. Inga heuristiska nya kolumner, inga förbikopplade ZIP/XML-skydd, inga felaktiga celladresser.
3. För **koordinatfria** dokument bygger den befintliga importkedjan preliminära **interna** X/Y deterministiskt, i samma tillåtna koordinatintervall och med unik nod-ID-sortering, *före* `validate_project()`. Det är en modellbootstrap/felreserv – **inte en konkurrerande layoutmotor eller nätverksfakta**. Återanvänd redan säker befintlig pure-placement-logik om beroenden tillåter utan cirkulär import; annars minsta isolerade, fullt testade helper med identisk matematisk regel. **Ändra aldrig `import_plan.node_layout()` eller `import_evidence.py`**, eftersom deras historiska fingerprint och replay är skyddade.
4. För äldre kompletta X/Y-filer bevaras tidigare *inputvalidering och formatkompatibilitet*. När ELK-06B är integrerad ska deras första automatiska visuella layout komma från ELK, inte från dokumentkoordinater. Under A får gamla importtester inte försvagas, ändra deras innebörd i tysthet eller låta felaktiga koordinater maskera nätverksfel.
5. Versionsstyrda XLSX/ODS med `Project` och schema 1.3 måste också fungera utan X/Y. `spreadsheet_schema.import_spreadsheet_tables()` får inte återskapa ett 6-kolumners `Devices.csv` ur en koordinatfri, läst tabell eller förlora VLAN/MAC/routes. De övriga fältens typ- och proveniensfel ska fortfarande peka på rätt källcell.
6. Rätta fel-/hjälptexter i samma kod-PR: "lägg till X/Y" är inte längre ett legitimt importfel. Förbli exakt och fail-closed för saknade explicita fysiska endpoints, otillåtna datatyper eller andra nätverksfakta.

**Positiva tester:** riktiga CSV, riktig OOXML-XLSX och riktig ODF-ODS utan X/Y; schema 1.0 **och** 1.3; omordnade headers; flera och 2 000 noder; ren Layer 2 utan krav på IP; explicit port- och kabelregister; ID:n, enabled, VLAN, MAC, IPv4, routes bevarade; validerat kanoniskt projekt med genererade interna ändliga X/Y.

**Negativa tester:** enbart X eller Y; extra/dubblerad kolumn; ogiltig text-/numerisk celltyp; dolda eller fusionerade celler; korrupt ZIP; fel tabellnamn; för många noder; falska kabeländar, dubblerade ID:n, konfliktande VLAN/routes; varken arbetsyta eller disk får bytas på fel. **Regressionsgrind:** gamla kompletta X/Y-filer fungerar fortfarande med deras befintliga strikt validerade kontrakt. Schema 1.4:s historiska kvitton och flexibla importbehållare är oförändrade.

**Klart endast när:** i riktig HTTP/Chromium kan användaren godkänna koordinatfri strikt CSV/XLSX/ODS och se en giltig **temporär intern** placering, utan att systemet frågar efter X/Y; alla obligatoriska Python/JS-/browserregressioner PASS. **A ensam är inte den slutliga ELK-funktionen** och får inte felaktigt markeras som sådan.

#### ELK-06B – HISTORISKT arbetskort; implementerat i PR #95

**Förväntat användarbeteende:** efter att användaren **uttryckligen godkänt en helt giltig** koordinatfri dokumentimport ska **ELK automatiskt beräkna och visa den första layouten utan extra klick eller andra Apply**. Det gäller både äldre strikt import och flexibel källmappning. Befintligt `Föreslå ELK-layout` och Preview/Apply/Cancel för en **redan skapad/manuellt ritad** topologi fortsätter fungera, men är inte en förutsättning för import.

**Filer:** `web/app.js` (befintliga `importProjects()`, `resetProject()`, ELK-/Workspace-state), `web/features/projects/import-review.js` (`applyCandidate()` och minimal lyckad-Apply-callback), `web/features/layout/elk.js` **endast vid bevisad brist**, befintlig UI-status; riktiga browsertester för båda importerarna. Ingen ny state manager eller Worker.

**Konstruktionskontrakt:**
1. Starta Worker bara **efter** godkänd och atomärt tillämpad **dokumentimport**. I strikt import måste `importKind(files) !== 'project'` gälla; att öppna/sätta ett gammalt `.yadilab`-/JSON-projekt är **inte** ny dokumentimport och får aldrig nollställa dess sparade X/Y. I flexibel import krävs `candidate.canApply`, godkänt ersättningsbeslut, exakt färskt fingerprint/projekt och slutförd `replaceProject()`. Ingen start under enbart preview, källa-inspektion, avbrutet urval eller blockerad candidate.
2. Återanvänd en **enda** post-import ELK-hjälpfunktion i `web/app.js`, triggas av båda framgångsvägarna. Befintlig tvåpass-Worker, `MULTI_EDGE`, `FIXED_POS`, endpoint-/overlap-/koordinatvalidering och timeouts måste behållas. Inget extra `layout-preview`-klick, inget ytterligare användar-Apply, ingen import HTTP-dubblett.
3. Vid start fånga workspace-ID/revision, edit-revision, filnamn och **exakt projektsnapshot**. Worker-svar med ändrad kontext, New/Open, annan Import, Builder-redigering eller manuell dragning får **aldrig** skriva över nyare data. Bygg inte två separata stale-guard-system.
4. Vid verifierad workerframgång tillämpas **endast X/Y på befintliga nod-ID:n**, plus giltiga, tillfälliga kabelbanor i presentationen. Jämför projektion med alla kanoniska fält utom X/Y samt objekt-ID-/ändpunktsuppsättning före/efter; ingen fysisk kabel eller port får uppstå eller försvinna. Återanvänd dirtiness, rendering och status i den befintliga ägaren.
5. **Ingen autosave.** Under pågående Worker får Save inte smyga förbi revisionsskyddet eller skriva ett senare ogiltigt svar. Efter lyckad layout sker separat explicit Save; efter ELK-fel visas ett ärligt, märkbart misslyckande och importens **interna deterministiska** reservgeometri ligger kvar. Om Save ska tillåtas efter fel ska användaren tydligt se att den automatiska ELK-layouten **inte** har lyckats. Skapa inte en andra visuell motor för att dölja felet.
6. För schema 1.4 förblir originalsource-bytes, SHA-256, selected units, fingerprint, fieldOrigins, baseline-replay och `importEvidence` oförändrade. UI får redovisa `CHANGED_SINCE_IMPORT` eftersom X/Y i projektets historiska baslinje skiljer sig; detta är **inte** ett påstående att det externa källdokumentet förändrats.
7. För redan öppnat/sparat projekt med X/Y eller **manuellt byggd topologi** körs aldrig initial ELK av sig själv. En senare manuell omplacering sker bara genom existerande Preview → Apply/Cancel och fortsatt separat Save.

**Positiva browsergrindar:** alla tre strikta koordinatfria dokumenttyper och flexibel accepterad källimport; direkt Worker-start efter import-Apply; synliga portexakta kablar utan extra klick; exakt oförändrad nätverkssemantik; Save→Open med samma X/Y; inga nätverkspaket eller routeutfall påverkas av nodpositionen. Kontrollera faktisk projektfil på disk efter explicit Save.

**Negativa browsergrindar:** importfel/avbryt/ej `canApply`, gamla Worker-resultat efter Import→New, Import→Open, Import→Import och manuell dragning, dubbla klick, Worker-throw/timeout/abort, stora grafer och ogiltigt ELK-svar, Save medan Worker körs, öppna tidigare sparad layout utan ändring. Kontrollera att ingen autosave eller stum nätverksmutation inträffar. Riktiga lokala Chromium/HTTP-fall, inte en stub som utges för end-to-end.

**Klart endast när:** **Import → Validate → Accept → auto ELK displayed → explicit Save → Open** passerar på alla stödda dokumentvägar och befintligt manuellt Preview/Apply/Cancel bibehålls.

#### ELK-06C – HISTORISKT arbetskort; implementerat i PR #96

**Varför nödvändigt:** i dag skriver `network_core/spreadsheet_export.py` nod-X/Y till `Devices`-bladet, `network_core/spreadsheet_templates.py` har `SAMPLE` med dessa värden, och `examples/csv/Devices.csv` visar samma äldre kolumner. Den existerande exporteraren beskriver XLSX/ODS som **lossless canonical project interchange** och kräver `restored == canonical`. Den garantin kan **inte matematiskt förenas** med dokumentationsfiler där X/Y inte finns. Detta är en verifierad kontraktskonflikt, inte ett tillstånd att ignorera dataförlust.

**Förväntat användarbeteende:** nygenererade CSV-exempel, nedladdningsbara XLSX-/ODS-mallar och exporterade **nätverksdokument** innehåller **inte** X/Y-kolumner. **Projektbackup** via kanonisk `.yadilab`-/JSON Save/Export behåller däremot X/Y exakt. UI och hjälptext anger tydligt att nätverksdokumentexporten bevarar stödda nätverksfakta men **inte nodplaceringen**; tidigare sparat projekt förblir enda garanterade layoutbackup.

**Filer:** `network_core/spreadsheet_export.py`, `network_core/spreadsheet_templates.py`, `network_core/spreadsheet_schema.py` vid behov, `examples/csv/Devices.csv`, `network_core/server.py`:s befintliga GET-mall-endpoints endast om de behöver anpassas, samt verkliga export-/template-fixturer och de **verifierat befintliga** `tests/test_spreadsheet_export.py`, `tests/test_spreadsheet_templates.py`, `tests/test_spreadsheet_v13.py` och `tests/browser_smoke.py`. Dokumentera målkontraktet efter att koden passerat i `README.md`, `docs/XLSX_IMPORT.md`, `docs/ODS_IMPORT.md`, `docs/SPREADSHEET_V13.md` och `docs/SPREADSHEET_TEMPLATES.md`. Kontrollera även att `GET /api/templates/xlsx` och `GET /api/templates/ods` returnerar nya koordinatfria **riktiga ZIP-bytes** och att deras filnamn/content-disposition inte blivit missvisande. Ändra inte `network_core/model.py` eller det kanoniska projektformatet.

**Exakt kodarbete:**
1. Byt den **externa** `Devices`-rubriken till `id,label,kind,zoneId` i nya mallar och nätverksdokumentexporter. Ändra radernas bredd och XLSX/ODS-skrivarnas fälttypklassificering; skriv inte ut X/Y som text, dolda kolumner, extra blad eller konstruerade nätverksfakta. Behåll alla befintliga andra stödda faktakolumner, inkl. schema 1.3-utökningar.
2. Byt `export_workbook()`-verifiering till **exakt jämförelse av stödda dokumenterbara nätverksfält**, med en ren, avgränsad projektion som först validerar båda projekten och tar bort **endast** X/Y från noder vid jämförelsen. **Använd inte `model.canonical_network_view()` oförändrad**: den behåller X/Y. Släpp inte igenom fältförlust, ändrad identitet, portstatus, VLAN/MAC, IPv4, statiska routes, fysiska endpoints eller ändrad ordning/struktur som produktens dokumentationskontrakt skyddar. Om något annat fält inte kan representeras: behåll befintlig fail-closed-avvisning.
3. Säkerställ att XLSX-/ODS-exportens nya koordinatfria bytes kan återimporteras via **samma riktiga importerare** från ELK-06A och att en godkänd import sedan får första ELK-layouten genom ELK-06B, utan koordinatbegäran. Kontrollera att den nya dokumentfilen faktiskt saknar X/Y-rubriker vid direkt filinspektion.
4. Bevara separat kanonisk projekt-Export/Save/Open där X/Y bevaras. Ändra inte `schemaVersion` och släpp inte omärkligt schema 1.4-`importEvidence` som dokumentexport; den nuvarande schema-begränsningen (1.0/1.3) och uttryckliga avvisningen måste dokumenteras om den kvarstår.
5. Uppdatera mallar och exempel som användare förväntas kopiera. Historiska koordinatbärande källfiler fortsätter **läsas** enligt 06A-kompatibiliteten men nygenererade nätverksdokument **skriver inte ut** X/Y. Dokumentation ska efter kodmerge inte längre säga att externa X/Y krävs.
6. Ändra exportens produkttext från "förlustfri projektbackup i kalkylblad" till korrekt **"nätverksdokumentation – layout sparas endast i projektfil"** när kontraktet faktiskt är verifierat. Gör ingen ny exportmotor.

**Positiva/negativa tester:** faktiska XLSX-/ODS-ZIP-exporter och nytt CSV-exempel utan X/Y; exakt nätverksprojektion efter riktig import; samma ID:n, noder/portar/länkar/VLAN/routes; bevarad kanonisk projektbackup inklusive X/Y; avvisning av irreducerbar fältförlust, felaktig/okänd schema, ogiltiga port-/kabelreferenser och osäkra/korrupta filer; kompatibilitet med äldre koordinatbärande arbetsböcker. Inget semantiskt försvagat testsystem.

**Klart endast när:** inget nyproducerat externt nätverksdokument kräver eller innehåller X/Y; all stödd nätverksinformation återimporteras utan förlust, de kanoniska projektfilerna bevarar den manuella diagramlayouten, och browser-export/återimport/Save/Open + full CI är gröna.

#### ELK-06: sammanhängande slutacceptans innan nästa arbetskort

Samtliga **A, B och C måste vara MERGED med PASS** innan ELK-06 som helhet kan märkas ACCEPTED. Ingen av etapperna får döljas bakom fraser som "fungerar redan" utan exakta negativa och positiva testfall.

| Användarhandling | Obligatoriskt utfall |
|---|---|
| Strikt CSV `Devices.csv` utan X/Y | Accepterad med explicit komplett topologi, intern preliminär plats, sedan automatisk ELK |
| Strikt XLSX/ODS (schema 1.0 + 1.3) utan X/Y | Samma utfall, samma nätverksfakta och korrekt bevarad källcellsfelposition |
| Flexibel källmappning med historiskt kvitto | Samma automatiska ELK utan att skriva om `node_layout()` eller importEvidence |
| Öppna kanonisk projektfil med sparade X/Y | Exakta manuella X/Y bevaras, ingen automatisk re-layout |
| Rita topologi manuellt och tryck inte på ELK | Ingen automatisk omplacering |
| Begär manuell ELK för existerande diagram | Preview → Apply/Cancel, separat Save |
| Exportera nätverksdokument och mallar | Inga X/Y-kolumner, exakta stödda nätverksfakta efter återimport |
| Spara projektfil och öppna igen | X/Y och all nätverksdata bevaras, inga auto-genererade kablar |
| Arbetsbok med ogiltig länk, VLAN eller felaktig källcell | Avvisa källtrogen import, ingen auto-ELK, ingen autosave |
| Worker misslyckas, timeout eller stale svar | Synligt fel; ingen vilseledande ELK-PASS, inga sena koordinatmutationer |

**STOPP och rollback:** om ett steg försvagar redan giltig import, förändrar schema 1.4-evidens, drar upp falska kablar, ändrar verklig nätverkssemantik eller döljer kända källfel: stoppa just den PR:n och återställ dess ändring. Lägg aldrig till en parallell importerare, tyst lagningsheuristik eller ny forskningsgren som "lösning". Alla ändringar måste fungera även i befintlig offline-runtime.


### ELK-07 – Korrekta användarlöften om kabelbanor efter Save/Open

**Befintligt kontrakt:** projektet lagrar endast X/Y. ELK:s kantsektioner är presentationsdata i minnet och går förlorade vid Open/restart eller invalidering. **Behåll detta** om användaren inte uttryckligen har beställt versionsstyrd presentationspersistens.

**Produktionsarbete vid lucka:** gör tydlig svensk status i `web/app.js` vid Apply/Save/Open och, om så behövs, ett informativt UI-element i `web/index.html`. Återanvänd `layout-status` i stället för att uppfinna ett extra lagringsformat. Säkerställ att Save/Open aldrig påstår att den exakta ELK-kabeldragningen lagrats.

**Tester:** Save/Open av schema 1.0 och schema 1.4 med samma kanoniska ID:n och oförändrade `importEvidence`. Test att gamla ELK-paths inte återanvänds efter annan mutation; standardrutt visas tills användaren uttryckligen begär ny layout.

**STOPP vid krav på permanent ELK-rutt:** ingen ny `schemaVersion`, ingen hemlig sidecarfil och ingen migration utan separat uttryckligt godkännande. Fortsätt med övriga arbetskort.

### ELK-08 – Stor topologi: snabb rendering **och** användbar interaction

**Befintligt:** PR #91 gav rejäl förbättring av synkron SVG-uppbyggnad; PR #92 behandlade kamerans path. Räkna inte om redan lösta problem som nya projekt.

**Om verkligt fördröjt beteende kvarstår:** definiera ett konkret scenario, t.ex. markering, panorering, noddragning eller upprepade renderanrop på ett 500-/2 000-nodersprojekt, med samma browser, datum och corpus före/efter. Identifiera **en** flaskhals i riktig prestandaprofil och ändra enbart dess kodväg. Bevara hitbox, portcirklar, highlighting och paketanimation.

**Tänkbara *betingade* kodscope:** `web/canvas.js` (uppdatering i stället för onödig full `render()`), `web/app.js` (samordning och status), befintlig benchmark under `tests/`. Ingen allmän DOM-virtualisering, Canvas2D-migration eller rAF-burst-ombyggnad på spekulation. Den breda rAF-idén har redan prövats och förkastats i `docs/SVG_CAMERA_NAVIGATION_RESEARCH.md`.

**DoD:** användarinteraktionen blir mätbart snabbare i samma körbara testfall, ingen regression av tidigare kamerafunktioner, oförändrad port- och kabelfunktion samt ärlig separat redovisning av render-, paint-, JS-heap- och interaktionstid. Ingen godtycklig 60-fps-garanti.

### ELK-09 – Tangentbord och tillgänglighet som faktisk funktion

**Användarnytta:** ELK Preview/Apply/Cancel och Builder ska gå att använda utan mus där kontrollerna lovar tangentbordsstöd, med meningsfull fokusåtergång och synliga statusmeddelanden.

**Kodscope:** `web/index.html` (semantik och kontrollordning), `web/app.js` (knappens focus state och tangentbordsinteraktion), `web/canvas.js` (endast där en konkret nödvändig interaktion saknas), `web/styles.css` (synlig focus outline), nytt riktat test under `tests/`.

**Tvingande UX-regler:** användarens befintliga projekt får inte ändras av enbart Tab/Enter utan uttrycklig Apply. Skärmläsarens `role=status` ska meddela status utan att stjäla fokus. Stängd preview återställer fokus till korrekt kontroll. Zoom-/pan-kommandon ska inte blockera musens redan fungerande gester.

**DoD:** verklig Chromium-tangentbordsgenomgång med Tab/Shift+Tab/Enter/Esc; minst ett negativt test för oavsiktlig Apply eller fortsatt focus i dolt element. Behåll redan korrekt tillgänglighet (KEEP).

### ELK-10 – Offlinepaket och licens i faktisk distribution

**Utgångspunkt:** ELK 0.13.0 finns redan lokalt i `web/vendor/`. `network_core/server.py` har explicit statisk allowlist. Ändra inte versionen utan mandat.

**Implementera bara det som distributionen saknar:** se till att startad lokal app faktiskt kan ladda `elk-api.js` och `elk-worker.js` utan nät, att licens/NOTICE är med i releaseartefakten och att felaktig Workerfil ger begripligt avslag. Använd befintligt build-/startflöde; inga nya paketplattformar eller installerare utan specificerat krav.

**Tester:** verklig lokal HTTP i browser med blockerade externa requests, deklarerad origin, `Worker`-fel, Save/Open och första ELK-preview efter nystart. Kontrollera licensfilens faktiska bytes/namn mot låst paket.

**DoD:** reproducerbart offline-startpaket med ELK som fungerar i angiven stödd miljö. Ingen npm-CDN-länk i runtime.

### ELK-11 – Verkliga tillåtna dokument som end-to-end-test **i produktens kodkedja**

**Mål:** externa dokument som används av godkända testpersoner ska gå igenom samma riktiga funktion som användarna använder. Inga parallella testimportörer och inga verkliga företagsdokument som publiceras utan tillstånd.

**Testflöde:** koordinatfri CSV/XLSX/ODS (strikt/flexibel) → verkliga filbytes → inspektion/strikt validering → explicit importgodkännande → **automatisk ELK-layout utan extra klick** → Save/Open → koordinatfri dokumentexport och faktisk återimport → separat källverifiering/simulering. Flexibel import med kvitto måste dessutom bevara fingerprint och replay.

**Krav:** minst ett tillåtet anonymiserat exemplar per stödd formatfamilj när sådant finns; annars skriv `NOT_AVAILABLE` och fortsätt med de tillåtna syntetiska browserfixturerna. **Skapa ingen forskningsgren för att leta efter datakällor.** Lägg till den minsta regressionen i samma kod-PR som den felaktiga import-/layoutgränsen rättas.

**STOPP:** en hemlig arbetsbok, obekräftad rättighet att publicera, saknade källbytes eller ofullständig deklarerad fysisk kabel innebär **ingen publicering och ingen påhittad komplettering**. Testa andra kända, tillåtna fall i stället.

### ELK-12 – Slutförd release, rollback och användarstöd

**Kodarbete:** endast befintliga, verifierade nödvändiga paketerings-, start- och integrationssteg samt korrigeringar i `README.md`, `docs/ELK_LAYOUT_CONTRACT.md` och relevanta release-/testfiler. Inga nya planarkiv, breda ADR-serier eller teoretiska designrapporter.

**Verifiera användarens resa:** starta offline; importera fullt giltigt dokument **utan X/Y-kolumner**; godkänn import; se första ELK-layouten visas **automatiskt utan ytterligare klick**; Save; Open utan oönskad nyplacering; ändra nod; prova en senare **frivillig** Preview/Cancel/Apply; simulera; stäng/starta app; förstå att exakta tidigare ELK-kabelböjar inte är beständiga om de inte återberäknats.

**Rollback:** om en release ångras ska tidigare kanoniska projekt kunna öppnas oförändrade. Ingen nedgradering som förlorar schema-1.4-proveniens, kabel-ID eller port-ID. Roller, verktyg och körbara kommandon ska stå kort och konkret i användardokumentationen.

**DoD:** testad paketerad release eller reproducerbar startprocedur; regressioner gröna; inga blockerande dataförlustfall; inga påståenden om OS-matriser som inte körts.

### ELK-13 – Slutacceptans utan forsknings-PR

**Syfte:** säkerställa att appen faktiskt är bättre. Det är en del av den **sista kod-PR:n/releasen**, inte en egen skrivskyddad revisions-PR.

**Minimikrav för ACCEPTED:**

- All ny produktionskod är merged med grön obligatorisk CI på exakt HEAD; slutlig `main` verifierad.
- Explicit import, `canApply`, källreferenser och schema-1.4-evidens är intakta.
- Alla kablar har två deklarerade fysiska portändar; ingen ELK-kurva har blivit nätverkssanning.
- Automatisk initial ELK efter **accepterad** import utan X/Y och senare manuell Preview/Cancel/Apply/New/Open/Save/stale fungerar både positivt och negativt.
- Synliga SVG-banor, interaktionsbanor och paketanimation refererar samma kablar.
- Tangentbordsflöden och fokus har verifierats för implementerade åtgärder.
- Stora, stödda nät ger hanterlig interaktion eller ett korrekt, begripligt resursavslag.
- Offline-Worker och versionslåsta licensfiler fungerar i minst den miljö som release påstås stödja.
- Endast faktiskt verifierad funktionalitet markeras ACCEPTED; övrigt UNSUPPORTED/NOT_VERIFIED och döljs inte.

**Ingen extra forskningscykel efter godkänd release.** Nya behov hanteras som konkret fel/feature i nästa vanliga kod-PR.

## 6. Teknik-, identitets- och sanningstabell

| Data eller effekt | Auktoritativ ägare | När det får ändras | Aldrig tillåtet |
|---|---|---|---|
| Nod-, port-, länk- och zonidentitet | `network_core/model.py` + användarens explicit accepterade modell | Validerad användarändring eller accepterad import | ELK hittar på eller byter objekt |
| Importerade originalceller, fingerprint, historisk replay | `network_core/import_plan.py`, `import_evidence.py` | Endast enligt befintligt versionskontrakt | Byta `node_layout()` för äldre importbevis |
| Layoutberäkning och ELK-Worker-output | `web/features/layout/elk.js` | **Automatiskt efter godkänd ny import**, eller vid användarens senare manuella Preview | Skriva till projektfil eller skapa nätverkslänk |
| Beräknade nodpositioner X/Y | `web/app.js` | **Automatiskt efter lyckad godkänd import** med revisions-/snapshotkontroll; annars manuellt Apply. Enbart separat Save skriver till disk | Ändra sparat projekt vid Open eller skriva över en nyare arbetsyta |
| ELK edge-sektioner | Flyktig presentation i `web/canvas.js` | Visas bara för exakt giltig snapshot | Hävdas vara varaktigt sparade eller fysisk topologi |
| Paket, ARP, VLAN, routing och ICMP | Befintlig Python-simulator, kanonisk topologi | Enligt faktisk protokollmotor | Härledas från ritad kabel eller närhet |
| Projektfil och disk | `network_core/storage.py` | Endast uttrycklig Save | Autosave från Import/ELK/zoom |

**Geometriskt facit:** port Y = `node.y + 71 + 23*i`. X = nodens vänstra eller högra kant, styrt av motpartens X. För varje link är SVG-pathens första och sista punkt just dessa synliga cirklar; `path.edge-hit` ska ha samma bana. Antal fysisk nod/port/kabel och varje ändpunkts-ID ska förbli exakt oförändrat efter endast layoutoperation. Avsaknad av en giltig rutt ska aldrig döljas med en fabricerad kabel.

## 7. Arkiverad etappprioritering (PR #94–#96 redan mergade)

| Prioritet | Börja implementera | Leverera i PR | Sluta inte med |
|---|---|---|---|
| **P1** | **ELK-06A:** koordinatfri strikt CSV/XLSX/ODS-import (schema 1.0/1.3) | Verklig produktionsparser + positiva/negativa tester + Chromium-import utan X/Y | Extra forskningsgren eller nytt dokumentkoordinatkrav |
| **P2** | **ELK-06B:** automatisk ELK efter godkänd strikt/flexibel dokumentimport | Befintlig Worker i två riktiga UI-flöden + Save/Open + stale-race-tester | Andra layoutklick, auto-Save eller separat layoutmotor |
| **P3** | **ELK-06C:** koordinatfri nätverksdokumentexport och mallar | Riktig XLSX/ODS/CSV-utdata utan X/Y, strikt nätverksrundtur; projektbackuper fortsatt med X/Y | Att kalla koordinatfri dokumentexport en lossless projektbackup |
| **P4** | ELK-09: tangentbord, fokus och manövrering | Funktionell kod och riktiga negativa Chromium-tester | Tillgänglighetschecklista utan kod |
| **P5** | ELK-04/05 eller ELK-08: först reproducerad kvarvarande interaktionsbrist | Minimal produktionsfix med mätning och regression | Andra motorer eller breda omskrivningar |

**Arbetsordning är obligatorisk:** börja med 06A, sedan 06B, sedan 06C. Varje kod-PR ska innehålla funktion och relevanta tester, inte enbart dokumentation. Om en etapp redan är bevisat implementerad ska den hoppas över och nästa kodetapp väljas. Ingen parallell forskningsgren, inte 14 PR:er för 14 rubriker.

## 8. ARKIVERAT Codex-direktiv – ELK-06A har redan mergats, FÅR INTE startas om

> **Uppgift (ELK-06A):** Detta är ett **implementationsuppdrag**, inte forskning. Läs `AGENTS.md`, `docs/MASTERPROMPT.md` och ELK-06A/B/C i `docs/ELK_IMPLEMENTATION_PLAN.md`. Kontrollera aktuell `main`, befintliga öppna PR:er och exakt CI en gång. **Ändra produktionskod nu** så att den äldre strikta CSV-/XLSX-/ODS-importen (både schema 1.0 och 1.3) fungerar med helt giltiga nätverksdokument vars `Devices`-tabell endast innehåller `id,label,kind,zoneId` (och alltså **inga X/Y-kolumner**). Gör ett strikt val mellan exakt den nya headern och den tidigare kompletta 6-kolumners-varianten för bakåtkompatibilitet; avvisa en ensam X/Y, okända och dubblerade fält. Härled temporär intern geometri deterministiskt före `validate_project()`, utan att skapa en andra layoutmotor, något nätverksfaktum, någon fysisk kabel eller en ny schemaVersion. Bevara verklig XLSX-/ODS-typvalidering, ZIP/XML-skydd, explicit VLAN/MAC/IP/routes, kanoniska ID:n och alla negativa fel. **Ändra inte `import_plan.node_layout()`, `import_evidence.py` eller historiska importkvitton.** Skriv och kör riktiga positiva/negativa CSV-, OOXML- och ODF-tester (schema 1.0 och 1.3), samt relevant HTTP/Chromium-import/Save/Open. En enda liten PR för verklig kod och dess tester, ingen research- eller test-only-PR. Merge endast när samtliga obligatoriska kontroller PASS på exakt HEAD, annars lämna PR öppen med konkret blockerare. **Fortsätt därefter med ELK-06B**, inte med en rapport.

**Efter 06A:** nästa Codex-uppdrag ska vara **06B (automatisk första ELK-layout)**; därefter **06C (koordinatfri dokumentexport/mallar)**. 06A får inte markeras som färdig ELK-importkedja förrän även B och C är verifierade. **Ingen ny forskningsfas mellan etapperna.**

## 9. Spårbarhet och ändringar av planen

- Ursprunglig detaljerad 2026-11-22-masterplan användes som underlag för etappidentifierare, låsta tekniska gränser och risker. **Dess forskningsvågor, revisions-only-etapper, extra rapporter och förslaget att göra separat ADR-/test-PR är uttryckligen ersatta av detta snabbare arbetskontrakt.** Återinför dem inte utan nytt användaruppdrag.
- Primära repoankare: `AGENTS.md`, `docs/MASTERPROMPT.md`, `docs/ELK_LAYOUT_CONTRACT.md`, `docs/IMPORT_SOURCE_CONTRACT.md`, `web/features/layout/elk.js`, `web/app.js`, `web/canvas.js`, `web/features/projects/import-review.js`, `network_core/model.py`, `network_core/import_plan.py`, `network_core/import_evidence.py` och `.github/workflows/ci.yml`.
- Officiell ELK-dokumentation: `https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html`, `https://eclipse.dev/elk/reference/options/org-eclipse-elk-portConstraints.html`, `https://eclipse.dev/elk/reference/options/org-eclipse-elk-layered-wrapping-strategy.html`; dessa är källor för befintlig adapter, **inte order om att starta ny forskning**.
- Beteende som inte kan verifieras med tillgängliga säkra testdata beskrivs som **NOT_VERIFIED**. Codex får inte påstå PASS eller fabricera data; välj nästa oberoende kodförbättring.
- Planuppdatering sker **enbart när en kod-PR behöver det** och då högst en kort statusrad om vad som verkligen mergats. Ingen separat dokumentationscykel eller framgångsmätning i antal författade rapporter.

**Slutregel:** Om en åtgärd inte förbättrar användarens körbara applikation eller direkt testar den kod som faktiskt ändras, hör den normalt inte hemma i nästa Codex-uppdrag.