# QUALITY-004/4A – Skrivskyddad arkitekturrevision och ansvarskarta

**Datum:** 2026-11-23 (ISO)  
**Kodbas:** `main@f243a626ff0943090d9216ac6eb1d4d84e431317` efter #105  
**Metod:** Läsning av aktuella GitHub-källfiler, funktioner och befintlig test-/CI-konfiguration; ingen ny lokal instrumentering, paketfångst eller produktionsändring  
**Status:** **4A READ_ONLY REVIEW COMPLETED / PR CI PENDING**. Ej automatiskt formellt QUALITY-004 ACCEPTED förrän detta dokumentets PR och dess senare main-CI har verifierats  
**Plattform:** **endast Linuxdistributioner**. Windows och macOS är UNSUPPORTED och aldrig utvecklingsmål  
**Skyddskontrakt:** [QUALITY_IMPROVEMENT_PLAN.md](QUALITY_IMPROVEMENT_PLAN.md) §1A och §8; `AGENTS.md`, `docs/MASTERPROMPT.md`, separata import-/protokollkontrakt. `KEEP` är standard. Inget nytt kontrakt eller implementeringsuppdrag.

## 1. Exakt baslinje och tidigare arbete

- #105, slutlig PR-HEAD `bc134adf40ef186c4fa2cde1a573a6dfd0e1498a`, två obligatoriska GitHub Actions `unit-tests` SUCCESS, squash-mergad till `main@f243a626ff0943090d9216ac6eb1d4d84e431317`. QUALITY-003 är ACCEPTED **endast för specificerade, referenstestade 3A–3F-regler**, inte full RFC-/IEEE-konformitet.
- Föregående main `ba674047e779750f5c8efa7739cf0f80a26fd5d6`: run `45238708767` slutförd SUCCESS. Ny main-run `45242895692` var **IN_PROGRESS** när 4A-revisionen påbörjades; **ingen** PASS på denna senare SHA påstås här.
- Tidigare uppdelningar av lagring, frontend-sessioner, protokoll och import finns i dagens repository. Historiska 3A–3E/3D-SGC och historiska importsteg 4A–4D får **inte** återupprepas. Namnen är inte nya arbetsorder.

## 2. Spårbar ansvarskarta

| Källa och belagd kodposition | Ansvar, in-/utdata och sidoeffekter | Skydd/beroenden och verifieringshänvisning | Beslut |
|---|---|---|---|
| `network_core/model.py:157–311` | `blank_project`, `validate_project`, `canonical_network_view`: validerar och normaliserar explicit kanoniskt projekt, inklusive noder, portar, länkar och adresser. Avvisar ogiltig eller ofullständig data; äger ingen filskrivning. | Projektformatet har en enda valideringskälla. `tests/test_model.py`, `tests/test_ipv4_host_address.py`. | **KEEP** |
| `web/app.js:17–43,418–438,1954–1965` | Ensam ägare av `project`, `selection`, `filename`, `savedSha`, `editRevision`, `workspaceRevision`; `changed()` invaliderar gamla diagnostik-, import- och sessionsvyer. | Utskick till controllers via kontext/callbacks; ingen andra kanonisk frontendmodell. | **KEEP** |
| `web/app.js:1644–1664,2025–2066` | Builder-validering, sen `Open` och stale-guard jämför snapshot, revision, namn och generation innan ersättning av projekt. | Avvisar inaktuella asynkrona svar. `tests/browser_smoke.py` kontrollerar riktiga Chromium-flöden. Race-robusthet vidare i QUALITY-005. | **KEEP** |
| `web/features/projects/persistence.js:1–37` + `web/app.js:1967–2013` | `prepareSave` fryser JSON och förväntad SHA; `saveSnapshot` använder explicit konfliktdialog via callback. Levande UI-workspace/SHA stannar i `app.js`. | Separat snapshot- kontra live-state. Ingen autosave. | **KEEP** |
| `network_core/storage.py:23–109` | `ProjectStore` läser/sparar verkliga projekt; Linux `fcntl.flock`, SHA-256-villkor, temporär fil, `fsync` och atomisk `os.replace`. | `tests/test_storage_http.py`, `tests/test_storage_concurrency.py`; kvalitet under samtidiga writes hör till QUALITY-005. | **KEEP** |
| `web/features/projects/transfer.js` | Transport, lokal läsning och förberedelse för CSV/XLSX/ODS/JSON-inspektion, import/export; *inte* kanonisk projektägare. | Tjänstelager och `web/app.js` separerar transport från beslut att tillämpa. | **KEEP** |
| `web/features/projects/import-review.js:73–103,686–738` | Sammanhållen transient controller för `sources/views/plan/candidate/revision/sourceGeneration`; kontrollerar källhash, fingerprint, val och samtidiga granskningsanrop innan tillämpning. | Vid applicering byggs aktuell kandidat om; nytt svar jämförs med gammalt; UI-kontroll och separat godkännande. Importens faktiska dokumentfullständighet hör till QUALITY-006. | **KEEP** |
| `network_core/import_plan.py:30–74,636–967` | Bygger härledda claims, dependency/konfliktstatus, provenance, fingerprints och kandidat från explicit källinformation; lämnar slutlig normalisering åt `validate_project`. | `tests/test_import_plan.py`, integrations-/verifieringstester och importkontrakt. Begränsad JSON-payload. | **KEEP** |
| `network_core/server.py:48–100,146–525` | Lokal HTTP-gräns för routning, requestvalidering, sessionsregister, felkoder; delegerar motorns handlingar. | Binder `127.0.0.1`, verifierar Host/Content-Type, avvisar otillåten CORS. Session cleanup-loop. | **KEEP** |
| `network_core/simulation.py`, `dhcp_registry.py`, andra sessionsregister | Processlokala sessions-ID, kanoniska projektsignaturer, sessionstillstånd och explicit Start/Run/Reset/Stop; inte fil eller DOM. | `tests/test_simulation_sessions.py`, `test_session_idle.py`, `test_dhcp_registry.py`. | **KEEP** |
| `web/features/sessions/dora-session.js:4–178`, `simulation-session.js:4–162` | Klient-side `generation`, `busy`, `pendingStops`, stale-kontroll och session-snapshot, server-API. Ingen kanonisk projektmutation. | Callback ägs av `app.js`; sena sessionstart-svar stoppas/ignoreras, serverstop kan upprepas. | **KEEP** |
| `network_core/ethernet.py`, `arp.py`, `ipv4.py`, `icmp_ping.py`, `dhcp.py`, `routing.py` | Specialiserade, redan separerade nätverksprotokollmotorer, exekveras över deklarerad topologi och oberoende validerad kanonisk data. | `tests/test_protocol_reference_*.py`, PR #100–#103 och [QUALITY_003_VERIFICATION_REPORT.md](QUALITY_003_VERIFICATION_REPORT.md). | **KEEP** |
| `web/canvas.js`, `web/features/layout/elk.js`, `web/app.js:441–563` | Transient layout/ELK-preview, ritning och explicit X/Y-Apply, inte auktoritativa kablar eller routes; Save är separat. | Integrerade browserregressioner och stale-/generation-skydd. | **KEEP** |
| `web/features/diagnostics/icmp-investigation-panel.js:63–191` | Befintlig fristående ICMP-renderer; läser `project` och kopierad sessionsvy, äger inte liveprojekt. | Jämförelse för möjlig DORA-rendering; aldrig ny state owner. | **KEEP** |
| `tests/browser_smoke.py` | Omfattande riktig Chromium-acceptans och Save/Open, används i obligatorisk `unit-tests`-CI. | Får inte ersättas med mock/stub eller förlora någon assertion. | **KEEP / INVESTIGATE** endast testorganisation |

**Systemgräns:** `web/app.js` håller endast arbetsytans kanoniska UI-state; `network_core/model.py` kontrollerar giltigt nätverksformat; `ProjectStore` äger beständig fil; `import_plan.py` äger källfaktatolkning inom importkontraktet; sessionsregister äger processlokal simulering; nätverksmotorerna äger protokollbeteende; DOM/rendering/layout äger presentation. Att flera lager läser en projektsnapshot är inte bevis för parallella kanoniska modeller.

## 3. KEEP kontra hypotetisk extraktion: konkreta risker och beroenden

### A. `web/app.js::renderDoraSession()` (ca 1004–1305) — INVESTIGATE, ej godkänd kodkandidat

**Observerat:** presenterar DORA-start, kabel-/port-/VLAN-fel, sessionsstatus och lease-förnyelse genom DOM-element; läser projektdokument och kopierad session från separat `createDoraSessionController`. Närliggande render-/eventbindningar stannar i `app.js`. ICMP-panelen har redan separat presentationsfunktion.

**KEEP:** noll nya modulgränser, inga nya callbacks, ingen risk att dela transient sessionstate, revisionsräknare eller DOM-event. **Extraktion:** teoretiskt färre visningsrader i entrypoint men sannolikt fler DOM-element som argument eller callbacks; event- och nätverksstate måste fortfarande styras från `app.js`. Inga före-/eftermätningar eller bevisad nettofördel finns. **Beslut: ingen 4B-kodändring.** Separat mätning krävs före framtida förslag.

### B. `web/features/projects/import-review.js` — KEEP

Koden har ett enda sammanhållet `guard()/valid()` med `revision`, `sourceGeneration`, källhashar, mappningsval och fingerprint; kandidat måste nyberäknas vid `applyCandidate()`. En uppdelning av controllern kan införa nya synkroniseringspunkter och konkurrerande review-ägare. Ingen reproducerad dubbel regel eller mätbar oberoende rendergräns. **KEEP**, inte kandidat.

### C. `network_core/import_plan.py` och `network_core/server.py` — KEEP

Importflödets claims/ursprung/dependency/kandidat är redan logiskt sammanhängande; HTTP-handlern är en explicit lokalt begränsad dispatchgräns, inte en alternativ protokollmotor. Att filerna är stora bevisar inte duplicerad ansvarskonflikt. En extraktion skulle introducera nya call-gränser utan uppmätt förbättring och samtidigt riskera proveniens-/felkoder. **KEEP**.

### D. `tests/browser_smoke.py` — KEEP / INVESTIGATE

Enskild lång acceptanskörning är verifierbart del av obligatorisk CI, men radantal ger inte tillstånd att automatiskt dela testet. Potentiell organisationsförändring hör till QUALITY-010 och kräver identisk reell Chromium DIRECT_HTTP, exakt samma positiva/negativa tester och oförändrad Save/Open, omstart och X11-krav. **Ingen kodändring här.**

### E. Sessionskontroller, lagring, protokoll och ELK — KEEP

Dessa separata gränser är redan etablerade och deras regressionskontrakt skyddade. En möjlig concurrency-/filintegritetsfråga ska undersökas som isolerat QUALITY-005-problem, inte användas för bred ommodularisering i QUALITY-004. Ingen ny protokollmotor, session registry, eventbus eller generell HTTP-router.

## 4. Revisionsfynd och beslutstabell

| Bedömning | Utfall | Vad som skulle krävas för annan åtgärd |
|---|---|---|
| **Bekräftad produktionsarkitekturdefekt** | **NONE CONFIRMED** av 4A:s skrivskyddade granskning; okända buggar kan finnas | Exakt reproduktion, avvikelse mot specifikt kontrakt, riskklass och negativ regression |
| **Befintliga gränser** | **KEEP** i samtliga granskade produktionsmoduler | Bevisad ansvarskonflikt eller nettomätbar och ekvivalent extraktion |
| **DORA-renderern** | **INVESTIGATE** (ingen `SMALL_EXTRACTION_CANDIDATE`) | Ren gräns med få explicita argument, inga nya state owners, före-/efterberoenden och Chromium-evidens |
| **Browser-smoke-organisation** | **INVESTIGATE / DEFER QUALITY-010** | Testfallsmatris med 1:1-scenarioekvivalens och oförändrad verklig CI |
| **Protokollbeteende** | **KEEP** inom QUALITY-003:s verifierade stödomfattning | Ny individuell reproducerad avvikelse; separat regressionsfix |
| **QUALITY-002 ruleset-enforcement** | **ENFORCEMENT NOT_VERIFIED** efter stängda negativa #99 | Icke-muterande GitHub-regelstatus som uttryckligen bevisar enforcement; aldrig riskfylld merge av röd PR |
| **Övrigt** | **NOT_VERIFIED** där reell belastning, extern utrustning och breda kombinationer inte testats | QUALITY-005–011 enligt egna separata acceptansgrindar |

## 5. Uppföljning, stoppregel och rekommenderat beslut

**4A-resultat:** *READ_ONLY REVIEW COMPLETED; KEEP är grundbeslut för den granskade produktionsarkitekturen.* Inga verifierade problem motiverar 4B-/4C-kodextraktion. En rapport med noll produktionskodändringar är ett godtagbart QUALITY-004-utfall enligt kvalitetsplanen. Att `renderDoraSession()` är lång är inte ett självständigt argument för refaktorering.

**Inga nya produktions- eller testerändringar:** ingen modell, API, session, import, layout, protokoll, filsemantik, CI, JS/Python-toolchain eller Linux-policy ändras i denna revisions-PR. Rapporten baseras på faktiskt läst kod; **inga** nya PASS, Chromiumkörningar, belastningstester eller runtime-captures påstås. Kommande CI på rapport-PR och dess main-merge måste verifieras på egna exakta SHA.

**Stoppregel:** om ingen reproducerbar ansvarskonflikt eller oberoende mätbar nettovinst påvisas, behåll koden. Ny hypotetisk idé blir endast INVESTIGATE; ingen REWRITE/DELETE. Först efter att denna 4A-rapport integrerats och verifierats kan QUALITY-004 formellt godkännas i separat statusbeslut. Därefter **QUALITY-005 – dataintegritet och samtidighet**, enbart isolerade, temporära testfiler/serverinstanser; inga verkliga projekt berörs.

**Plattformsavgränsning:** Endast Linuxdistributioner, i synnerhet de faktiskt testade Linuxmiljöerna. Windows och macOS är **UNSUPPORTED**.
