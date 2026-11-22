# ELK-arkitekturen – kodstyrd genomförandeplan

**Status:** bindande genomförandebilaga för ELK och SVG i detta repository.  
**Version:** 2.0, 2026-11-22.  
**Nulägesankare:** `main@eac31c4b8e47b021f1b67dc66aab22165cc83afc`; kontrollera ny HEAD inför varje PR.  
**Prioritering:** **fungerande produktionskod snabbt**, inte fristående forskning, rapporter eller teoretiska prototyper.  
**Styrande överordnade regler:** `AGENTS.md`, `docs/MASTERPROMPT.md`, `docs/IMPORT_SOURCE_CONTRACT.md` och kvalitetsfärdplanen `docs/QUALITY_IMPROVEMENT_PLAN.md`. Denna plan är en **konkret ELK-arbetskö**, inte en andra konkurrerande QUALITY-färdplan.

> **Huvudregel för Codex:** Välj nästa relevanta, specificerade, ännu inte implementerade **användarfunktion eller verifierade felrättning**. Skriv minsta möjliga produktionskod och de tester som bevisar den. Leverera en körbar PR. Avsluta inte en aktiv etapp med enbart en arkitekturrapport, ett forskningsresultat, en test-PR eller en ny lista med hypoteser. Om något redan fungerar: **KEEP och gå direkt vidare**. Ingen fristående forskningsgren utan ett konkret blockerande problem i den aktuella kodändringen.

## 1. Exakt önskat slutresultat

Användaren ska kunna importera en **fullständigt, explicit och källtroget validerad** nätverksdokumentation, välja en lättläst ELK-layout, se kablar som verkligen slutar på de deklarerade portarna, redigera diagrammet med mus och tangentbord, använda samma topologi i simuleringsmotorn, spara och öppna projekt samt förstå vad som sparats och vilka visuella rutter som återberäknas. Stora diagram ska vara hanterbara utan att nätverksfakta eller historiskt importbevis förändras.

**Det är levererad applikationsfunktionalitet som mäts.** Kodrader, forskningsvågor, issue-antal, experimentvarianter och antal PR:er är inte framstegsmått.

## 2. Vad som redan finns – får inte byggas om

Följande är observerat på nulägesankaret, men status måste kontrolleras på aktuell HEAD:

| Befintlig funktion | Ägare | Skydda i varje PR |
|---|---|---|
| Pythonmodell med schema 1.0–1.4 och strikt validering | `network_core/model.py` | Kanoniska ID:n, gränser, okända fält, no implicit cables |
| Historisk flexibel import och källkvitto | `network_core/import_plan.py`, `import_evidence.py`, `web/features/projects/import-review.js` | Originalbytes, källreferenser, `canApply`, fingerprint, historisk replay |
| Lokal ELK 0.13.0 i Worker | `web/features/layout/elk.js`, `web/vendor/` | 2 pass, `MULTI_EDGE`, 0×0 `FIXED_POS`, full outputvalidering, abort, timeout |
| Opt-in read-only Preview → Apply → separat Save | `web/app.js`, `web/index.html` | Stale guard, inga writes under preview, Save/Open-kontrakt |
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
- **Ingen ogrundad automatisk layout:** rita aldrig kabel, port, nod eller routing baserat på IP, VLAN, zon, grafnärhet eller ELK:s estetiska output.

### 3.3 Krav för att få säga ”klart”

En etapp är **IMPLEMENTED** endast när den har synlig eller programmässig produktionsfunktion, minst ett relevant positivt och negativt test, ingen känd regression, grön obligatorisk CI på exakt HEAD samt verifierad integrering i `main`. Om befintlig kod redan uppfyller allt: markera **KEEP/ALREADY_IMPLEMENTED** i nästa kod-PR:s notering och **hoppa över** etappen; skapa ingen no-op-PR.

## 4. Rekommenderad leveransordning

Följande är **arbetskort**, inte order om fjorton PR:er. Identifikatorerna ELK-00–ELK-13 behålls för spårbarhet mot tidigare arkitekturdokument. **Arbetskort med ingen kvarvarande kodändring hoppas över.** När två angränsande kort påverkar samma lilla användarflöde får de ingå i **en** begränsad PR; stora ändringar delas.

| Körordning | Arbetskort | Faktisk kodnytta | Startvillkor |
|---|---|---|---|
| 1 | **ELK-06** | Tydlig ELK-åtgärd direkt efter **godkänd** källtrogen import | Existerande `canApply` och import-Apply fungerar; använd existerande ELK-knapp/adapter |
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

### ELK-06 – Prioritet 1: tydlig kodintegrering efter godkänd import

**Användarnytta:** efter att användaren **uttryckligen accepterat en fullständig, giltig** CSV/XLSX/ODS-import ska ELK-layout vara ett uppenbart, frivilligt *nästa klick*, utan att dokumentationsimport och layout blandas ihop. Detta är det **första föreslagna koduppdraget** om beteendet inte redan finns.

**Filer:** `web/features/projects/import-review.js` (`applyCandidate`, kandidatens giltighet/fingerprint), `web/app.js` (`createImportReview`, `startElkPreview`, `resetProject`, status/knapp), `web/index.html` vid behov för befintlig knapp-/statusyta, `tests/browser_elk_layout.py` och ett riktat browser-importtest. **Rör inte** `network_core/import_plan.py::node_layout()`, `network_core/import_evidence.py` eller importens projektkandidatformat.

**Exakt implementationsordning:**
1. Kontrollera om dagens UI redan gör nästa ELK-steg tydligt efter accepterad import. Om ja: hoppa över kortet; bygg inte en duplicerad knapp.
2. Om inte: koppla befintlig import-Apply-succé till en **synlig, frivillig åtgärd** som återanvänder existerande `layout-preview`/`startElkPreview`. **Starta inte Worker automatiskt** och gör ingen extra HTTP-import.
3. Aktivera åtgärden endast efter att `candidate.canApply` är sann, användaren godkänt ersättning, ny kandidat-fingerprint matchat och `replaceProject` slutförts. Granskningsläge, blockerade kandidatfall och avbruten import får aldrig generera layoutförslag.
4. Visa att layout är *presentation* och att Apply flyttar endast noder, medan Save sker separat. Behåll historisk källproveniens och `BASELINE_MATCH` → `CHANGED_SINCE_IMPORT` där positionsändring medför skillnad.

**Negativa tester:** ogiltig portände, icke accepterad kandidat, avbruten källgranskning, snabb Import→New, kraschad Worker, Cancel och projektfil med historisk schema-1.4-proveniens. Kontrollera att antalet noder/portar/länkar och alla kanoniska icke-koordinatfält är identiska före/efter layout Apply.

**DoD:** riktig användare kan genomföra **Import → Validate → Accept → Click ELK Preview → Cancel/Apply → Save → Open**; ingen auto-Save, inget falskt källbevis och inget parallellt importflöde. Endast den minsta nödvändiga kodändringen.

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

**Testflöde:** filbytes → faktisk inspektion → exakt cellmapping → `canApply` → användar-Apply → historiskt kvitto → ELK-preview → Apply → Save/Open → separat källverifiering och simulering mot samma faktiska länkar.

**Krav:** minst ett tillåtet anonymiserat exemplar per stödd formatfamilj när sådant finns; annars skriv `NOT_AVAILABLE` och fortsätt med de tillåtna syntetiska browserfixturerna. **Skapa ingen forskningsgren för att leta efter datakällor.** Lägg till den minsta regressionen i samma kod-PR som den felaktiga import-/layoutgränsen rättas.

**STOPP:** en hemlig arbetsbok, obekräftad rättighet att publicera, saknade källbytes eller ofullständig deklarerad fysisk kabel innebär **ingen publicering och ingen påhittad komplettering**. Testa andra kända, tillåtna fall i stället.

### ELK-12 – Slutförd release, rollback och användarstöd

**Kodarbete:** endast befintliga, verifierade nödvändiga paketerings-, start- och integrationssteg samt korrigeringar i `README.md`, `docs/ELK_LAYOUT_CONTRACT.md` och relevanta release-/testfiler. Inga nya planarkiv, breda ADR-serier eller teoretiska designrapporter.

**Verifiera användarens resa:** starta offline; öppna projekt; importera fullt giltigt dokument; preview; Cancel; Preview; Apply; Save; Open; ändra nod; simulera; stäng/starta app; förstå varför tidigare kabelböjar visas som standardrutter om ELK inte återberäknats.

**Rollback:** om en release ångras ska tidigare kanoniska projekt kunna öppnas oförändrade. Ingen nedgradering som förlorar schema-1.4-proveniens, kabel-ID eller port-ID. Roller, verktyg och körbara kommandon ska stå kort och konkret i användardokumentationen.

**DoD:** testad paketerad release eller reproducerbar startprocedur; regressioner gröna; inga blockerande dataförlustfall; inga påståenden om OS-matriser som inte körts.

### ELK-13 – Slutacceptans utan forsknings-PR

**Syfte:** säkerställa att appen faktiskt är bättre. Det är en del av den **sista kod-PR:n/releasen**, inte en egen skrivskyddad revisions-PR.

**Minimikrav för ACCEPTED:**

- All ny produktionskod är merged med grön obligatorisk CI på exakt HEAD; slutlig `main` verifierad.
- Explicit import, `canApply`, källreferenser och schema-1.4-evidens är intakta.
- Alla kablar har två deklarerade fysiska portändar; ingen ELK-kurva har blivit nätverkssanning.
- Preview/Cancel/Apply/New/Open/Save/stale fungerar både positivt och negativt.
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
| Layoutförslag, ELK-Worker-output | `web/features/layout/elk.js` | Vid användarens klick på Preview | Skriva till projektfil eller skapa nätverkslänk |
| Godkända nodpositioner X/Y | `web/app.js` | Endast explicit Apply och separat Save | Ändra utan revision-/snapshotkontroll |
| ELK edge-sektioner | Flyktig presentation i `web/canvas.js` | Visas bara för exakt giltig snapshot | Hävdas vara varaktigt sparade eller fysisk topologi |
| Paket, ARP, VLAN, routing och ICMP | Befintlig Python-simulator, kanonisk topologi | Enligt faktisk protokollmotor | Härledas från ritad kabel eller närhet |
| Projektfil och disk | `network_core/storage.py` | Endast uttrycklig Save | Autosave från Import/ELK/zoom |

**Geometriskt facit:** port Y = `node.y + 71 + 23*i`. X = nodens vänstra eller högra kant, styrt av motpartens X. För varje link är SVG-pathens första och sista punkt just dessa synliga cirklar; `path.edge-hit` ska ha samma bana. Antal fysisk nod/port/kabel och varje ändpunkts-ID ska förbli exakt oförändrat efter endast layoutoperation. Avsaknad av en giltig rutt ska aldrig döljas med en fabricerad kabel.

## 7. Etappprioritering utan fördröjning: första tre kodleveranserna

| Prioritet | Börja implementera | Leverera i PR | Sluta inte med |
|---|---|---|---|
| **P1** | ELK-06: direkt, frivilligt layoutflöde efter **accepterad** import | Synlig UI-handling med riktig browser-import → Preview/Apply/Save/Open | Ytterligare importforskningsrapport, importer nummer två |
| **P2** | ELK-09: tangentbordsfokus och manövrering för existerande layoutkontroller | Riktig tangentbordsfunktion med negativa Chromium-tester | Tillgänglighetschecklista utan kod |
| **P3** | ELK-04/05 eller ELK-08: den **först reproducerade** kvarvarande redigerings-/interaktionsbristen | Minimal fix med mätning och regression | Ny ruttmotor, CSS-/SVG-omskrivning utan mätbart problem |

**Om P1 redan är uppfylld:** Codex ska **inte** skapa en redundant knapp eller PR. Redovisa med fil/rad och browserbevis, och gå direkt till P2 **i samma session**. **Om P2 är uppfylld:** gå direkt till P3. Denna rutin förhindrar att projektet fylls med ”forskningsleveranser”.

## 8. Codex-direktiv som ska användas ordagrant för nästa uppdrag

> **Uppgift:** Implementera nästa konkreta produktionsförbättring i `docs/ELK_IMPLEMENTATION_PLAN.md`, börja vid P1 i avsnitt 7. Detta är en **koduppgift**, inte en forsknings-, revisions- eller dokumentationsuppgift. Kontrollera aktuell `main`, CI, en eventuell redan öppen kod-PR och om P1 redan finns. Om P1 saknas: implementera minsta nödvändiga ändring i existerande `web/features/projects/import-review.js`, `web/app.js` och browser-tester så att en **uttryckligt accepterad, helt giltig import** får ett tydligt, **frivilligt** nästa klick till redan befintlig ELK-förhandsvisning; ingen auto-Apply, ingen auto-Save och ingen förändring av `network_core/import_plan.py::node_layout()` eller historiskt källkvitto. Om P1 redan finns: gå **direkt till P2 och implementera fungerande tangentbordsflöde**. Bevara all befintlig kod som fungerar. Inga parallella grenar, ingen ny layout-/importmotor, inga fristående forsknings-PR:er eller statusrapporter som ersätter kod. Skriv produktionskod och relevanta positiva/negativa tester i samma lilla PR; kör befintliga tester. Skriv exakt PR-länk, HEAD, kodändringar och verifiering. Merge endast vid GitHubs normala gröna grind på exakt HEAD och verifiera `main`. Om CI ännu körs, avsluta utan passiv väntan och lämna PR öppen.

## 9. Spårbarhet och ändringar av planen

- Ursprunglig detaljerad 2026-11-22-masterplan användes som underlag för etappidentifierare, låsta tekniska gränser och risker. **Dess forskningsvågor, revisions-only-etapper, extra rapporter och förslaget att göra separat ADR-/test-PR är uttryckligen ersatta av detta snabbare arbetskontrakt.** Återinför dem inte utan nytt användaruppdrag.
- Primära repoankare: `AGENTS.md`, `docs/MASTERPROMPT.md`, `docs/ELK_LAYOUT_CONTRACT.md`, `docs/IMPORT_SOURCE_CONTRACT.md`, `web/features/layout/elk.js`, `web/app.js`, `web/canvas.js`, `web/features/projects/import-review.js`, `network_core/model.py`, `network_core/import_plan.py`, `network_core/import_evidence.py` och `.github/workflows/ci.yml`.
- Officiell ELK-dokumentation: `https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html`, `https://eclipse.dev/elk/reference/options/org-eclipse-elk-portConstraints.html`, `https://eclipse.dev/elk/reference/options/org-eclipse-elk-layered-wrapping-strategy.html`; dessa är källor för befintlig adapter, **inte order om att starta ny forskning**.
- Beteende som inte kan verifieras med tillgängliga säkra testdata beskrivs som **NOT_VERIFIED**. Codex får inte påstå PASS eller fabricera data; välj nästa oberoende kodförbättring.
- Planuppdatering sker **enbart när en kod-PR behöver det** och då högst en kort statusrad om vad som verkligen mergats. Ingen separat dokumentationscykel eller framgångsmätning i antal författade rapporter.

**Slutregel:** Om en åtgärd inte förbättrar användarens körbara applikation eller direkt testar den kod som faktiskt ändras, hör den normalt inte hemma i nästa Codex-uppdrag.