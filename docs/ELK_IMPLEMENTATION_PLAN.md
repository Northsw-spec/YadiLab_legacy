# ELK-arkitekturen – kodstyrd genomförandeplan

**Status:** bindande genomförandebilaga för ELK och SVG i detta repository.  
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

**Verifierad implementeringslucka på baslinje-HEAD:** den gamla *strikta* fyrtabellsimporten i `network_core/csv_import.py` kräver faktiskt `Devices.csv: id,label,kind,x,y,zoneId`. `network_core/spreadsheet_schema.py`, `xlsx_import.py` och `ods_import.py` återanvänder den strukturen. Detta är **befintlig teknisk skuld som ska rättas i ELK-06** – inte ett giltigt krav att kunder ska skriva koordinater i dokument. Den flexibla, källbaserade `network_core/import_plan.py::node_layout()` härleder däremot koordinater internt. **Påstå aldrig att den strikta vägen redan fungerar utan X/Y innan ett verkligt test passerar.** Utöka inputstödet utan att förstöra redan stödda historiska filer eller schema 1.0–1.4; gamla X/Y-dokument kan fortsatt accepteras för kompatibilitet men får aldrig vara ett obligatoriskt formatkrav. Ingen ny nätverksmodell eller separat importerare.

**Bindande testgrind:** ett verkligt `Devices.csv` och verkliga XLSX-/ODS-arbetsböcker med deklarerade enheter, portar och kablar, men **utan X/Y-kolumner**, ska kunna godkännas i det avsedda importflödet och resultera i ett färdigt automatiskt ELK-diagram. Testa både äldre strikt format och flexibel mappad källimport, även med Save/Open, negativa kabel-/portfall och dokument med celladresser som inte misstolkas som visuella koordinater.

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
| Automatisk initial ELK-layout efter godkänd import | **Ska implementeras i ELK-06** | Mål: inga X/Y-kolumner krävs i källdokument. **Äldre strikt CSV/XLSX/ODS-import kräver ännu X/Y och måste korrigeras.** Flexibel källimport genererar preliminära X/Y internt |
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

## 4. Rekommenderad leveransordning

Följande är **arbetskort**, inte order om fjorton PR:er. Identifikatorerna ELK-00–ELK-13 behålls för spårbarhet mot tidigare arkitekturdokument. **Arbetskort med ingen kvarvarande kodändring hoppas över.** När två angränsande kort påverkar samma lilla användarflöde får de ingå i **en** begränsad PR; stora ändringar delas.

| Körordning | Arbetskort | Faktisk kodnytta | Startvillkor |
|---|---|---|---|
| 1 | **ELK-06** | **Automatisk första ELK-layout direkt efter godkänd import – inget extra layoutklick** | Existerande `canApply`, import-Apply och ELK-Worker finns; återanvänd befintlig adapter med stale-skydd |
| 2 | **ELK-04 + ELK-05** | Korrekt edit/drag/livscykel: ingen falsk eller föråldrad kabelgeometri | Bevisa ett konkret användarfall som saknar detta; annars KEEP |
| 3 | **ELK-09** | Tangentbord, fokus och begriplig tillgänglig layoutkontroll | Befintliga Builder-flöden granskas *inom samma kod-PR* |
| 4 | **ELK-02 + ELK-03** | Adapter som klarar specificerade felaktiga indata och grafklasser | Lägg bara till kod när ett negativt test visar ett faktiskt gap |
| 5 | **ELK-08** | Responsiv interaktion i stora verkliga vyer | Mät reproducerbart aktuellt flaskhalsfall, åtgärda samma PR |
| 6 | **ELK-07** | Tydlig och korrekt Save/Open-upplevelse för tillfälliga kabelbanor | Behåll nuvarande projektformat; ändra inte schema utan nytt mandat |
| 7 | **ELK-10** | Verifierat självständigt offlinepaket och korrekt licensdistribution | Ingen spontan biblioteksversionhöjning |
| 8 | **ELK-11** | Riktig importerad testkorpus + fungerande slutanvändarflöde | Endast källor med uttryckligt tillstånd och tillåten anonymisering |
| 9 | **ELK-12** | Reproducerbar release, rollback och kort användarmanual | Alla funktionella beroenden gröna |
| 10 | **ELK-13** | Slutlig integrerad acceptans i vanlig CI, utan revision som sidoprojekt | Samtliga relevanta användarscenarier testade |

**ELK-00 och ELK-01 är inte fristående arbetsfaser**: de representerar snabb HEAD-kontroll och oberoende testfacit som bakas in i varje riktig kod-PR. Lägg aldrig upp egna forsknings-/test-PR:er för dem.

## 5. Arbetskort med exakt implementation och acceptans

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

### ELK-06 – Prioritet 1: automatisk initial ELK-layout efter godkänd import

**Användarnytta och bindande UX-krav:** dokumentationstabeller för CSV/XLSX/ODS förutsätts **inte innehålla X/Y-koordinater**. När användaren uttryckligen godkänt en **fullständig och giltig** import måste appen **automatiskt beräkna och visa första layouten med befintlig ELK-Worker**. Användaren ska **inte** behöva klicka på en ytterligare ELK-knapp, godkänna layoutens koordinater separat eller välja en layoutmetod för att få ett användbart diagram. Detta är obligatoriskt implementationsarbete om det inte redan fungerar. **Manuell Preview/Apply/Cancel finns kvar för senare omorganisering**, inte för nödvändig initial placering.

**Filer:** `network_core/csv_import.py` och `network_core/spreadsheet_schema.py` för den äldre strikta importeraren; kontrollera motsvarande gränssnitt i `network_core/xlsx_import.py` och `network_core/ods_import.py` (ändra bara vid faktiskt behov). `web/features/projects/import-review.js` för lyckad flexibel `applyCandidate`, `web/app.js` för båda importvägarnas atomära projektbyte, befintlig `computeElkPreview`/Worker, revisionskontroller, status och rendering; `web/index.html` vid behov. Tester: `tests/test_csv_import.py`, `tests/test_xlsx_import.py`, `tests/test_ods_import.py`, `tests/browser_elk_layout.py` och ett verkligt browser-importtest. **Ändra inte** `network_core/import_plan.py::node_layout()`, `network_core/import_evidence.py`, befintliga schema-1.4-kvitton eller källbytes. Återanvänd befintlig adapter och tillståndsägare.

**Exakt implementationsordning:**
1. **Ta bort källdokumentkravet på X/Y i den äldre strikta fyrtabellsimporten**, utan att göra fysiska nätverksfakta valfria. Interna preliminära X/Y måste härledas deterministiskt **före** befintlig `validate_project()` för att uppfylla det interna kanoniska schemat; gamla koordinatbärande indata får inte tyst korrumperas. Testa riktig CSV/XLSX/ODS utan X/Y. Ingen ny importerare eller separat modell.
2. Återanvänd båda befintliga giltiga importvägarna: strikt `web/app.js::importProjects` efter validering och bekräftelse samt flexibel `web/features/projects/import-review.js::applyCandidate` endast när `canApply` är sann, kandidatens fingerprint matchar och användaren godkänt projektbytet. **Ingen ELK-start** under källinspektion, mapping, avvisad/avbruten import eller när en kandidat saknar giltigt nätverk.
3. När respektive importvägs atomära **projektbyte faktiskt lyckats** och den importerade arbetsytan skapats, starta **automatiskt** layoutberäkningen från en **gemensam efter-import-hook** med befintlig lokal ELK-Worker; inget extra användarklick och ingen ny HTTP-import. Visa tydlig beräkningsstatus. Lägg inte till en parallell import-/layoutmotor.
4. Beräkna bara **X/Y och visuella edge-sektioner** för de faktiskt importerade noderna, portarna och de explicit deklarerade kablarna. Använd befintlig tvåpass-ELK och `MULTI_EDGE`/`FIXED_POS`; byt inte node-/port-/link-ID, nätverkskonfiguration eller importkvitto.
5. Stale-skydd: bind beräkningen till importens `workspaceRevision`, `editRevision` och projektsnapshot. New/Open/ny import/manuell redigering under Worker måste ogiltigförklara resultatet. **Ingen sen automatisk layout** får skriva över en senare användarändring.
6. När layouten validerats ska dess X/Y **tillämpas automatiskt i den nyimporterade arbetsytan**, och de giltiga ELK-kabelbanorna visas direkt. Ingen andra Apply-knapp. Ingen autosave till disk: användaren väljer fortfarande separat **Spara**. Hantera redan etablerad dirty-status och historisk importproveniens korrekt: källkvitto och replay ändras aldrig; en layoutbaserad avvikelse från baslinjen får inte presenteras som ändrat källdokument.
7. Om ELK misslyckas, avbryts eller överskrider resursgränsen: **visa ett tydligt fel/otillgänglig layout**, låt den redan godkända importens existerande deterministiska nodplacering ligga kvar och bevara originalfakta. Påstå inte att ELK-layout lyckades, fabricera inga kablar och skriv inget till disk. Gör inte en tyst andra layoutmotor som framstår som ELK.
8. Vid Open av ett redan sparat projekt med befintliga X/Y ska ingen automatisk nyplacering ske; användarens sparade layout bevaras. En senare frivillig om-layout använder fortfarande befintligt manuellt Preview/Apply/Cancel.

**Positiva tester:** verklig *strikt* CSV/XLSX/ODS-import med **inga X/Y-kolumner** samt flexibel källmappning i befintligt HTTP/Chromium-gränssnitt; importacceptans → Worker startar själv → direkt färdigt diagram utan extra klick → exakt bibehållen nod-/port-/länkidentitet → Save → Open med samma godkända interna X/Y. Separata regressioner för redan stödda historiska koordinatbärande CSV-/arbetsboksfiler, men **aldrig** ett nytt krav på koordinater i källdokument. Kontrollera att den synliga och klickbara kabelns ändpunkter möter rätt portcentrum. Bekräfta att historiska importkvitton behåller samma bytes/hash.

**Negativa tester:** frånvarande X/Y ska **inte** blockera en i övrigt giltig dokumentation; ofullständiga/ogiltiga länkar, avvisad eller avbruten import, `canApply=false`, stale fingerprint, Import→New/Open/annan import under Worker, Worker-fel, timeout, stora/ogiltiga koordinater, historisk schema-1.4-proveniens och öppning av redan sparat projekt. Ingen sen Worker får flytta ett nytt eller manuellt modifierat projekt. Inget projekt får autosparas och inget dokumenterat nätverksfält ändras av layouten.

**DoD:** både strikt CSV/XLSX/ODS och flexibel dokumentationsimport stöder **Import (utan X/Y-kolumner) → Validate → Accept → automatic ELK layout displayed → Save → Open** i riktig Chromium utan extra layoutklick eller koordinatfält i källdokumentet. Felvägar ger ärlig status utan dataförlust. Den manuella valbara layoutkontrollen för befintliga projekt fungerar fortsatt och regressionssviten är grön.

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

**Testflöde:** filbytes → faktisk inspektion → exakt cellmapping → `canApply` → användarens import-Apply → historiskt kvitto → **automatisk ELK-layout utan extra klick** → Save/Open → separat källverifiering och simulering mot samma faktiska länkar.

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

## 7. Etappprioritering utan fördröjning: första tre kodleveranserna

| Prioritet | Börja implementera | Leverera i PR | Sluta inte med |
|---|---|---|---|
| **P1** | ELK-06: **ta bort obligatoriska X/Y-fält från gammal strikt import och kör automatisk initial ELK-layout efter accepterad import** (ingen extra knapp) | Strikt CSV/XLSX/ODS **och** flexibel browser-import utan X/Y → automatisk ELK-rendering → Save/Open | Ytterligare layoutklick, importforskningsrapport eller importer nummer två |
| **P2** | ELK-09: tangentbordsfokus och manövrering för existerande layoutkontroller | Riktig tangentbordsfunktion med negativa Chromium-tester | Tillgänglighetschecklista utan kod |
| **P3** | ELK-04/05 eller ELK-08: den **först reproducerade** kvarvarande redigerings-/interaktionsbristen | Minimal fix med mätning och regression | Ny ruttmotor, CSS-/SVG-omskrivning utan mätbart problem |

**Om P1 redan är uppfylld:** Codex ska **inte** skapa en redundant knapp eller PR. Redovisa med fil/rad och browserbevis, och gå direkt till P2 **i samma session**. **Om P2 är uppfylld:** gå direkt till P3. Denna rutin förhindrar att projektet fylls med ”forskningsleveranser”.

## 8. Codex-direktiv som ska användas ordagrant för nästa uppdrag

> **Uppgift:** Implementera nästa konkreta produktionsförbättring i `docs/ELK_IMPLEMENTATION_PLAN.md`, börja vid P1 i avsnitt 7. Detta är en **koduppgift**, inte en forsknings-, revisions- eller dokumentationsuppgift. Kontrollera aktuell `main`, CI, en eventuell redan öppen kod-PR och om P1 redan finns. Om P1 saknas: **eliminera först kravet på X/Y-kolumner i äldre strikt CSV/XLSX/ODS** via befintliga `network_core/csv_import.py` och `network_core/spreadsheet_schema.py` samt relevanta importtester, med bevarad kompatibilitet för äldre källfiler. Integrera sedan båda befintliga importvägarna med minsta nödvändiga ändring i `web/features/projects/import-review.js`, `web/app.js` och riktiga browser-tester så att **varje uttryckligt accepterad, helt giltig dokumentationsimport utan koordinatkolumner automatiskt får sin första ELK-layout**, utan ett andra knapptryck eller separat layout-Apply. Återanvänd befintlig tvåpass-Worker, validera resultatet och tillämpa X/Y i den aktuella arbetsytan under strikt stale-/revisionskontroll. **Ingen autosave** och ingen ändring av `network_core/import_plan.py::node_layout()` eller historiskt källkvitto. Efter Open av ett sparat projekt ska dess X/Y bevaras, medan frivillig manuell Preview/Apply/Cancel används för senare omplacering. Worker-fel ska visas tydligt och importens existerande deterministiska initialplacering bevaras. Om P1 redan finns: gå **direkt till P2 och implementera fungerande tangentbordsflöde**. Bevara all befintlig kod som fungerar. Inga parallella grenar, ingen ny layout-/importmotor, inga fristående forsknings-PR:er eller statusrapporter som ersätter kod. Skriv produktionskod och relevanta positiva/negativa tester i samma lilla PR; kör befintliga tester. Skriv exakt PR-länk, HEAD, kodändringar och verifiering. Merge endast vid GitHubs normala gröna grind på exakt HEAD och verifiera `main`. Om CI ännu körs, avsluta utan passiv väntan och lämna PR öppen.

## 9. Spårbarhet och ändringar av planen

- Ursprunglig detaljerad 2026-11-22-masterplan användes som underlag för etappidentifierare, låsta tekniska gränser och risker. **Dess forskningsvågor, revisions-only-etapper, extra rapporter och förslaget att göra separat ADR-/test-PR är uttryckligen ersatta av detta snabbare arbetskontrakt.** Återinför dem inte utan nytt användaruppdrag.
- Primära repoankare: `AGENTS.md`, `docs/MASTERPROMPT.md`, `docs/ELK_LAYOUT_CONTRACT.md`, `docs/IMPORT_SOURCE_CONTRACT.md`, `web/features/layout/elk.js`, `web/app.js`, `web/canvas.js`, `web/features/projects/import-review.js`, `network_core/model.py`, `network_core/import_plan.py`, `network_core/import_evidence.py` och `.github/workflows/ci.yml`.
- Officiell ELK-dokumentation: `https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html`, `https://eclipse.dev/elk/reference/options/org-eclipse-elk-portConstraints.html`, `https://eclipse.dev/elk/reference/options/org-eclipse-elk-layered-wrapping-strategy.html`; dessa är källor för befintlig adapter, **inte order om att starta ny forskning**.
- Beteende som inte kan verifieras med tillgängliga säkra testdata beskrivs som **NOT_VERIFIED**. Codex får inte påstå PASS eller fabricera data; välj nästa oberoende kodförbättring.
- Planuppdatering sker **enbart när en kod-PR behöver det** och då högst en kort statusrad om vad som verkligen mergats. Ingen separat dokumentationscykel eller framgångsmätning i antal författade rapporter.

**Slutregel:** Om en åtgärd inte förbättrar användarens körbara applikation eller direkt testar den kod som faktiskt ändras, hör den normalt inte hemma i nästa Codex-uppdrag.