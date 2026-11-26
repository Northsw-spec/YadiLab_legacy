# A0 – Forensisk modul- och regressionsbaslinje

**Datum:** 2026-11-26  
**Historisk nollpunkt – A0 DONE:** [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169) är verifierat squash-mergad. Nedanstående mått beskriver dåtidens källversion. Framtida Codex-arbete följer [CODEX_EXECUTION_POLICY.md](../CODEX_EXECUTION_POLICY.md) (ingen passiv CI-väntan, oförändrad Required-mergegrind).  
**Granskad main:** `f36435dd7b108756bdac6e3919c1cb1c61cf58d7` (PR #168 redan mergad; inga öppna PR:er vid A0-start).  
**Historisk jämförelse:** 3E, [PR #59](https://github.com/Northsw-spec/YadiLab/pull/59), squash `17acb51c8c64c3b4b7a1026514cb8b0a2177a127`.  
**Koppling:** [Godkänd åtgärdsplan A0–A10](../REMEDIATION_PLAN_2026-11-26.md); främst **C02–C05** och beredning för C06–C09.  
**Maskinläsbart:** [versionsbunden fil-/testinventering](../../architecture/a0_baseline.json) och [ES-importgraf](../../architecture/a0_frontend_imports.json).  
**Källbegränsning:** statisk källgranskning, Git-träd/blobbar och faktiska GitHub CI-statusar. Detta är inte en fullständig statisk dataflödesanalys, runtimeprofilering eller oberoende simulatorcertifiering.

## 1. Verifierad kod- och CI-nollpunkt

Vid start var `main` `f36435dd7b108756bdac6e3919c1cb1c61cf58d7`, med **noll öppna PR:er**. Aktuell `main` hade `unit-tests: SUCCESS`; föregående [PR #168](https://github.com/Northsw-spec/YadiLab/pull/168) hade två fullständiga CI-körningar `SUCCESS` på exakt `7648ca724614436969813617d83f365f0f21483e`. Resultat avser dessa SHA:er, inte en otestad kommande refaktorering.

| Källa | 3E | A0-nollpunkt på main | Tolkning |
|---|---:|---:|---|
| `web/app.js`, jämförbara fysiska rader | 2 237 | 2 977 | **+740 / +33,1 %** |
| `web/app.js`, äldre rapporters `split("\\n")`-tal | 2 238 | 2 978 | **+740** (en virtuell sista post vid avslutande radbrytning) |
| `web/app.js`, Git blob-byte | 110 148 | 142 243 | +32 095 byte |
| Namngivna toppnivåfunktioner i `app.js` (regex) | 85 | 116 | +31 |
| Direkta `.addEventListener(` i `app.js` (textmatchning) | 70 | 96 | +26 |
| Grov DOM-referens-/skrivningsheuristik i `app.js` | 76 | 104 | +28, **inte** exakt antal DOM-mutationer |
| Förstaparts-ES-modulfiler i `web/` exklusive vendorer | 14 | 18 | Alla **14 tidigare filvägar finns fortfarande** |
| `network_core/import_plan.py`, visningsrader | ej med i 3E | 967 (966 fysiska) | stor senare importmodul |
| `network_core/icmp_investigation.py`, visningsrader | ej jämförd här | 844 (843 fysiska) | stor utrednings-/sessionsmodul |

**Korrigering av tidigare beräkning:** Den aktiva planens preliminära `+741` blandade historiska 2 237 *fysiska* rader med nuvarande 2 978 *visningsrader*. **Enhetligt räknat är ökningen +740 rader.** Radantal mäter inte ensamt arkitekturkvalitet.

## 2. Modulariseringens faktiska historia och kvarvarande gränser

| Leverans | Bekräftad historisk squash | Vad som faktiskt extraherades/bevaras |
|---|---|---|
| [PR #53, 3C](https://github.com/Northsw-spec/YadiLab/pull/53) | `2916ca7c9c3f3c5edf7dbb5d07a35f97f632dcb8` | `features/diagnostics/queries.js` och `presenters.js`; appen äger fortfarande projekt/revisioner |
| [PR #54, 3D1](https://github.com/Northsw-spec/YadiLab/pull/54) | `9ebe4b5d9939f68a4764f96031c3487e925db967` | DHCP Investigation-controller |
| [PR #55, 3D-SGC](https://github.com/Northsw-spec/YadiLab/pull/55) | `9f913a889d1928359490fc7955ed8279c79da14b` | serverns städning av övergivna sessioner |
| [PR #56, 3D2](https://github.com/Northsw-spec/YadiLab/pull/56) | `d34f912f882f66ad9a6dcc4522816c0d6618045d` | ICMP Investigation-controller med generationsskydd |
| [PR #57, 3D3](https://github.com/Northsw-spec/YadiLab/pull/57) | `f70a0d1980894d6e8f944387269ee79680c165ca` | DHCP/DORA-controller |
| [PR #58, 3D4](https://github.com/Northsw-spec/YadiLab/pull/58) | `5687b63d72e2bb60928ccbe38627cf3836847e4b` | ARP/Ethernet-sessionscontroller |
| [PR #59, 3E](https://github.com/Northsw-spec/YadiLab/pull/59) | `17acb51c8c64c3b4b7a1026514cb8b0a2177a127` | separat ICMP-panel, ES-importgraf-test; appen kvar som kompositionsrot |

**Forensisk slutsats:** användarens upplevelse av att vara tillbaka vid ruta ett är motiverad av återväxten i huvudfilens ansvar, men tidigare moduler har **inte** försvunnit som filer. Samtliga 14 förstaparts-ES-modulfiler från 3E finns på nollpunkten. Fyra nya modulvägar har tillkommit: `features/diagnostics/protocol-lessons.js`, `features/layout/elk.js`, `features/projects/import-review.js` och `features/projects/mapping-profiles.js`. Filsystemnärvaro bevisar inte i sig att ansvarsgränserna är rätt – därför A1:s ägarskapskontroller.

## 3. Var de cirka 740 raderna tillkommit (funktions-/ansvarsnivå)

Jämförelsen mellan 3E och nuvarande `app.js` visar **31 nytillkomna namngivna toppnivåfunktioner**, plus utökningar av redan befintliga funktioner och fler registrerade händelser:

- **Arbetsytepaneler och presentation:** `panelCard`, `dropdownCards`, `syncDropdownButton`, `setupWorkspacePanels`.
- **Adressbindningar/portval:** `hostIpv4`, `topologyIpv4Choices`, `portForAddressValue`, `normalizedAddress`, `sameAddress`, `updateBoundAddress`, `syncBoundAddresses`, `requireBoundAddresses`, `arrangeFromToRows`, `setupAddressBindings`, `copyIpv4`.
- **Topologikontextmeny:** `hideTopologyMenu`, `setupTopologyContextMenu`.
- **ELK-/layoutorkestrering:** `layoutStatus`, `invalidateElk`, `startElkPreview`, `applyElkPreview`, `cancelElkPreview`, `networkWithoutCoordinates`, `layoutImportedProject`. Geometriberäkningen ligger redan separat i `features/layout/elk.js`; appens layoutlivscykel är däremot fortfarande tätt kopplad till workspace.
- **Paketresa:** `forgetJourney`, `replayJourney`, `presentJourney`.
- **Builder-kontroller:** `validateBuilderAttempt`.
- **Guidad ICMP-lektion:** `loadIcmpLesson`, `startIcmpLesson`.
- **Källförhandsgranskning:** `previewCurrent`; merparten av de sista cirka 240 *lexikala* raderna är dock **topplevel-händelseregistrering och asynkrona inline-callbacks**, inte den korta funktionen `previewCurrent` i sig.

Detta förklarar återväxten på ansvarsnivå men är ingen exakt rad-för-rad-attribution till enskilda PR:er; att härleda exakt vilket senare merge som införde varje rad kräver ytterligare `git blame`/patchgranskning och hör inte till ett påstående om verifierad härkomst i denna baslinje.

## 4. Modul- och tillståndsägarkarta

| Område | Nuvarande ansvarig kod | Faktisk ägare/stale-koppling | A1/A3/A4-risk |
|---|---|---|---|
| Kanoniskt projekt, Builder, urval, sparad SHA, workspace-/edit-revisioner | `web/app.js` | appen äger projekt och sparat/olagrat tillstånd; `changed()` invaliderar vyer och sessioner | delad ägare eller förlorad stale-guard vid extraktion |
| L2-/ARP-/IPv4-/ICMP-diagnostik | `app.js`, `features/diagnostics/queries.js`, `presenters.js` | appen håller resultat och per-diagnosgeneration; frågor/presentation stateless utanför | dubbel resultatstate, gammalt HTTP-fel ersätter ny slutsats |
| DHCP Investigation | `features/sessions/dhcp-investigation.js` | controller äger id, state, generation, busy, logg, verdict, recovery, error | förlorat Stop-svar, stale id eller för tidigt facit |
| ICMP Investigation | `features/sessions/icmp-investigation.js` och panelen `features/diagnostics/icmp-investigation-panel.js` | controller äger id/generation/busy/probe-/diagnosstate; panelen presenterar | dold facitläcka, sent svar, gammal session efter arbetsytebyte |
| DHCP/DORA-session | `features/sessions/dora-session.js` | controller äger id/generation/busy/trace/fault | fel tid/lease eller förlorad Stop-cleanup |
| ARP/Ethernet-session | `features/sessions/simulation-session.js` | controller äger id/generation/busy/diagnostik | ihopblandad session/replay efter projektbyte |
| Dokumentimport och förhandsgranskning | `features/projects/import-review.js`, `transfer.js`, `mapping-profiles.js`, `app.js` | import-review har egna revisions-/generationstokens; appen äger slutligt projektbyte | importfilens SHA/källrader och projekt-SHA får inte blandas |
| Layout/geometri | `features/layout/elk.js`, `canvas.js`, `app.js` | separat geometri, appen äger förslagets workspace-kontext och explicit Save | sen ELK-commit ändrar fel projekt eller dess nätverksfakta |
| HTTP och autentisering | `web/services/api.js`, `network_core/server.py` | API-token/HTTP-gräns, serverns projektsessionsregister | avbruten klient får sekundärt felsvar, se A2 |
| Importplan och kandidatbeslut | `network_core/import_plan.py`, `import_evidence.py`, `import_inspection.py` | en slutlig `model.validate_project`, uttryckliga källclaims/proveniens | ny parallell validator, tyst dataförlust, fel dependency |
| ICMP-övningens fel och evidens | `network_core/icmp_investigation.py`, `icmp_ping.py`, `troubleshooting.py` | samma Echo-motor, separat Registry/IdleSessions, dolt fel och evidensprojektor | dubbla motorer eller leak av dold felorsak |

**Viktigt:** `dhcpGeneration`/`doraGeneration` i `app.js` gäller snabba diagnostiska vyer; dessa ska **inte** feltolkas som samma tillstånd som sessionscontroller-modulernas privata `generation`. Sådan sammanblandning vore en ny regression.

## 5. Verifierbar, representativ anrops- och importgraf

**Exakt statisk ES-importgraf på nollpunkten:** `index.html` har en `/app.js`-entrypoint. [Manifestet](../../architecture/a0_frontend_imports.json) visar **18 förstapartsmoduler, 29 direkta ES-importkanter, 18 nåbara moduler, 0 saknade importmål, 0 cykler och 0 orphan-filer**. Det befintliga `tests/test_web_import_graph.py` kontrollerar redan motsvarande grafstruktur. Detta skyddar **inte** mot monolittillväxt eller duplicerad state.

**Representativa statiska anropsvägar, inte fullständig runtime-callgraph:**

```text
app.js :: changed / resetProject / openProject
  → invalidering av diagnostik, workspace- och server-/sessionscontrollers
  → render() / canvas (projektsnapshot; ingen implicit disk-Save)

app.js :: runPing / runRouteLookup / runIPv4Trace / runArp
  → features/diagnostics/queries.js → services/api.js → server.py
  → befintliga Ethernet/ARP/IPv4/ICMP-motorer
  → features/diagnostics/presenters.js → appens resultatstate

app.js :: ICMP/DHCP/DORA/Simulation-sessionåtgärd
  → create*Controller(...) med fångat session-ID och generation
  → services/api.js → serverns Registry/IdleSessions
  → controller.snapshot/vy → relevant panel

app.js :: källimport / förhandsgranskning
  → features/projects/transfer.js / import-review.js
  → server.py → import_inspection/import_plan/import_evidence
  → model.validate_project (en auktoritativ slutvalidator)

app.js :: startElkPreview / layoutImportedProject
  → features/layout/elk.js (presentationslayout)
  → kompositionsrotens stale-/workspace-grind
  → canvas/render; sparad fil ändras först vid explicit Save
```

En framtida A1-anrop-/beroendeanalys bör mäta förbjudna kanter som `features/diagnostics/* → persistence`, `sessions/* → app.js`, importlogik `→` UI-state och återinförd rendering i appen. Detta dokument är **underlag**, inte bevis för att sådana framtida spärrar redan är implementerade.

## 6. Hög-riskfunktioner och öppna gränser

Följande är **lexikala funktions-/klassblock**, inte Cyclomatic Complexity-värden; de inkluderar i vissa fall kommentarer/blankrader och omgivande registrering:

| Modul / funktion | Ungefärlig storlek vid A0 | Varför relevant |
|---|---:|---|
| `web/app.js::renderDoraSession` | 302 rader | DORA-sessionens presentation och DOM |
| `web/app.js::renderInspector` | 217 | Builder/port/rutt/val och projektmutation |
| `web/app.js::renderInvestigation` | 151 | DHCP-felsökningspanelens presentation |
| `web/app.js::renderTroubleshooting` | 136 | felinspektion, val och presentation |
| `web/app.js::previewCurrent` + efterföljande eventkod | 243 *lexikalt intervall* | asynkron källförhandsgranskning och många listeners; själva funktionen är kort |
| `network_core/import_plan.py::build_plan` | 331 | orkestrering, claims, konflikter, dependency |
| `network_core/import_plan.py::_candidate` | 176 | kanoniska importkandidater/portkrockar |
| `network_core/import_plan.py::_claim` | 143 | källclaims och proveniens |
| `network_core/icmp_investigation.py::IcmpInvestigation` | 541 *klassintervall* | observations-, evidens- och sessionsansvar |
| `IcmpInvestigation.probe` | 179 | observation, router-ICMP, route, länk, port, VLAN |
| `network_core/icmp_investigation.py::_candidates` | 162 | deterministiskt motiverade felkandidater |

Den redan existerande `features/projects/import-review.js` är **885 visningsrader**, vilket är ytterligare ett delningskandidatämne – men den ska inte förstoras eller flyttas enbart för en radbudget. Ingen av ovanstående siffror bevisar en runtimebugg.

## 7. Versionsbundet regressions-/filmanifest och evidensnivå

[Filmanifestet](../../architecture/a0_baseline.json) innehåller Git-trädets **52** förstapartsmoduler i `network_core/` och `web/` (Python/JS utan vendorer), samt **94** incheckade filer under `tests/**` och `web/fixtures/**`, vardera med **Git blob-SHA och exakt byteantal**. Därmed kan varje fil identifieras om den ändras eller tas bort. En fil är inte samma sak som ett testfall: ett filmanifest bevisar inte att ett visst antal testmetoder exekverats. Fullständiga metodlistor och observerade antal hör till respektive versionslåst CI-jobb.

Minsta verifieringskedja för varje relevant A-kort:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
npm run check
python3 tests/browser_smoke.py
python3 tests/run_pedagogy_assessment.py
python3 tests/browser_api_capability.py
xvfb-run -a python3 tests/browser_primary_selection_x11.py
python3 tests/browser_elk_layout.py
python3 tests/browser_elk_import.py
python3 tests/browser_canvas_large_zoom.py
```

- **Positiv A0-kontroll:** manifestet innehåller angivna revisions-ID, samtliga historiska 3E-modulvägar, giltiga blob-SHA och fullständiga reproducerbara importkanter. Tidigare CI är `SUCCESS` på sina **egna** SHA.
- **Negativ A0-kontroll:** syntetiskt saknad modul, syntetisk orphan, bruten grafkant och felaktigt SHA/byteantal ska gå att upptäcka vid manifestvalidering. Detta är **inte** en körande A1-arkitekturspärr på nuvarande `main`.
- **Avgränsning:** inga projektfiler, runtime-API:er, simulatorprotokoll, databärare eller UI-element ändras av A0. Historik och observerad nollpunkt bevaras även när ny kod senare ändras.

## 8. A0-överlämning: exakt nästa arbetskort

**A1 – G1–G7, arkitekturspärrar före ny extraktion** är nästa *godkända* arbetskort efter verifierad A0-merge:

1. Baserat på de **verifierade** JSON-manifesten införa `architecture/baseline.json` och reproducerbar maskinell trend/ratchet; avvisa växande `app.js` och förlorade nödvändiga moduler utan explicit granskad budgetändring.
2. Separat, automatiserat `architecture-guard`-jobb med **obligatorisk** required-status i GitHub branch rules (kontrollera faktisk regel via API; en grön frivillig check är otillräcklig).
3. Negativt testa borttagen ICMP-sessionmodul, orphan/cykel, förbjudet beroende från presentation till lagring, kopierad sessionsstate, otillåten budgethöjning och tyst borttagen skyddstestfil. En riktig beteendebevarande extraktion ska förbli grön.
4. Rapportera arkitekturdiff och G1–G7-status per PR; skyddet måste förbli aktivt genom minst en efterföljande funktionell PR.
5. **Ingen A3/A4-modularisering** innan A1:s negativa tester **och** erforderlig branchregel verifierats.

**Rollback:** vid fel eller otillräcklig evidens lämnas A0 omergad; eventuella rättningar görs i samma PR och samtliga required-kontroller körs på ny slutlig HEAD. Befintligt projektschema och källkod är oförändrade.

**Aktuell A0-status:** separat forensisk leverans; inte en fullständigt installerad arkitekturspärr.
