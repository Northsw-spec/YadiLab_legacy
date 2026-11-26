# YadiLab – enda masterplan: arkitekturstabilisering A0–A10 och komplett nätverkssimulator S0–S12

**SENASTE BESLUT, har företräde:** [ADR-0002 – helt ny egen nätverksmotor](architecture/ADR_0002_FRESH_ENGINE_2026-11-26.md). Gammal nätverksexekveringskod ska inte migreras in i den nya motorn; den ska ersättas från standard-/scenario-orakel. Bevara endast verifierade externa produktkontrakt och regressionstest. **S1-POC0 får börja direkt efter guard-/ADR-PR:ns godkännande utan att invänta fullständig S0-katalog eller samtliga A3/A4/A5/A7-kort.** Legacy finns tillfälligt kvar för användare tills EN verifierad cutover, då avvecklas den via registrerade retirement receipts. Required CI, användardataintegritet och sanningskrav kvarstår.


**ABSOLUT UPPDRAG 2026-11-26: INGEN SAKNAD CISCO PACKET TRACER-FUNKTION VID SLUTLEVERANS.** YadiLab ska göra ALLT Packet Tracer gör på Linux: varje protokoll, protokollvariant, enhet/modul, CLI/GUI, fysiskt/logiskt nät, simulation/realtime/PDU, IoT, OT, Activity Wizard, automatiserad rättning/scripting, multiuser, extension/API, projekt-/aktivitetsformat och övriga användarflöden; därefter verifierat överträffa Packet Tracer i alla relevanta kvalitetsområden. **Exakt två användarbeslutade undantag: inget krav på Windows/macOS och inget nytt produktkrav på tillgänglighet/keyboard-only-tjänster.** Inga andra luckor eller permanenta "out-of-scope" tillåtna. Se [PT-FULL-001: bindande 29-familjers fullständighetskontrakt](FULL_PACKET_TRACER_PARITY_CONTRACT.md). Äldre etapptext om begränsad paritet, frivilligt multiuser, smal protokollbredd eller godtagbara slutluckor är upphävd för S12. En juridisk/teknisk blockerare står kvar som blockerad, aldrig som godkänd fullständighet.


**Datum:** 2026-11-26  
**Status:** GODKÄND / AKTIV PLAN – **NYTT UTTRYCKLIGT PRODUKTBESLUT 2026-11-26:** Fullständig, exakt, in-process nätverkssimulator utan VM/emulering, med objektiv ambition att överträffa Cisco Packet Tracer. **A9 PROTOKOLLUTBYGGNAD ÄR GODKÄND SOM S0–S12-OMFÅNG; A8 MÄNSKLIG STUDIE KRÄVER FORTFARANDE SEPARAT BESLUT.** S0 strategi/arkitektur IN_PROGRESS, ingen ny protokollmotor levererad av denna plan-PR.

**Historisk A-status (ska bevaras):** **A0 DONE** ([PR #169](https://github.com/Northsw-spec/YadiLab/pull/169)); **A1 DONE** ([PR #170](https://github.com/Northsw-spec/YadiLab/pull/170), separat Required-negativ [#173](https://github.com/Northsw-spec/YadiLab/pull/173)); **A2 DONE** ([PR #175](https://github.com/Northsw-spec/YadiLab/pull/175)); **A3 IN_PROGRESS**, del 1 [PR #176](https://github.com/Northsw-spec/YadiLab/pull/176) och del 2 [PR #177](https://github.com/Northsw-spec/YadiLab/pull/177) är squash-mergade med samtliga Required-checks SUCCESS (senaste main `16e6bd67444b1ef9eb96f2448edf04efda2ab17f`); fortsatt A3: UI-invalidering och sena `finally`, Builder/inspector, diagnostik och import-UI.  
**Utgångspunkt:** Granskningsrapporten *Teknisk granskning av YadiLab – 2026-11-26* (hela avsnitt 1–6), användarens observation om försvunnen modularisering samt en separat kodinventering på `main@82fca139cc43e12ff8c21bbb3427ab4f87588fd5`.  
**Syfte:** Åtgärda påvisade fel och underhållsbrister; verifiera kvarstående osäkerheter; ge dokumenterade simulatorbegränsningar ett explicit beslut; återvinna och skydda modulariseringen.  
**Styrning:** P0–P7 förblir CLOSED. **Denna fil är YadiLabs ENDA aktiva backlog:** A0–A10 = kvalitet/arkitekturgrund; S0–S12 = nu uttryckligen beställd full simulatorplattform. **A8 och A9 har olika beslut:** A8 (empirisk människostudie) = DECISION_REQUIRED; A9:s tidigare godkännandespärr har upphävts för det exakt definierade S-omfånget. Tidigare snäva förbud i denna fils historiska A-avsnitt är underställda de nya avsnitten 10–11. [MASTERPROMPT](MASTERPROMPT.md), [Packet Tracer-forskning](research/PACKET_TRACER_GAP_ANALYSIS_2026-11-26.md), [protokollmatris](PROTOCOL_COVERAGE_MATRIX.md) och [simulatorkontrakt](architecture/DETERMINISTIC_ENGINE_CONTRACT.md) är underordnade specifikationer, inte egna roadmaps.


## 0. Operativ startpunkt för kommande konversationer (beslutad 2026-11-26)

**OBLIGATORISKT för Codex och övriga kodagenter:** [Codex-produktivitet, CI-optimering och handoff](CODEX_EXECUTION_POLICY.md). Det dokumentet är **operativ exekveringspolicy**, inte en andra roadmap. **Ingen passiv Actions-väntan**: produktiva, säkra kod-/test-/arkitekturuppgifter inom samma PR medan kontrollen körs; om endast extern CI återstår, rapportera exakt HEAD/status och avsluta i stället för credits-slösande polling. Riktade preflighttester före full kod-acceptans; dokumentationssnabbväg endast vid maskinellt verifierad ren Markdown-diff. Exakt Required-grind, squash, A-kortsbeslut och branchskydd bevaras utan undantag.


**LÄS FÖRST:** `AGENTS.md` → **den här enda aktiva planen** → `docs/MASTERPROMPT.md` → `docs/IMPORT_SOURCE_CONTRACT.md` → historisk `docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md` endast för fortsatt pedagogiskt kvalitetskontrakt. Primärgranskning ordagrant: [Teknisk granskning 2026-11-26](reviews/TECHNICAL_REVIEW_2026-11-26.md). Välj aldrig uppgift ur den avslutade P0–P7-planen eller andra äldre roadmaps.

**A0 – Rebaslinje & forensisk modulgranskning:** [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169) är verifierat MERGED med required CI SUCCESS; [A0-forensik](architecture/A0_FORENSIC_BASELINE_2026-11-26.md) och [manifest](../architecture/a0_baseline.json) kvarstår. **A1 – Arkitekturspärrar G1–G7 är DONE:** [PR #170](https://github.com/Northsw-spec/YadiLab/pull/170) implementerade 17 testade negativa/positiva spärrar, modulkontrakt, ägarskap, trendrapport och separata workflowjobb. GitHub [main-ruleset #27419615](https://github.com/Northsw-spec/YadiLab/rules/27419615) kräver nu uttryckligen båda `unit-tests` och `architecture-guard` (app 15368; strict). [PR #173](https://github.com/Northsw-spec/YadiLab/pull/173) gav **grön `unit-tests` + röd separat `architecture-guard` i båda körningar + GitHub `mergeable_state=blocked`**; stängd utan merge. [Evidens i Issue #171](https://github.com/Northsw-spec/YadiLab/issues/171#issuecomment-7197176467). **A2 är DONE** ([PR #175](https://github.com/Northsw-spec/YadiLab/pull/175), C06); **A3 är IN_PROGRESS** med den första DOM-extraktionen i [PR #176](https://github.com/Northsw-spec/YadiLab/pull/176).

**Fortsättningsregel:** Vid YadiLab-"fortsätt": välj nästa beroendeupplåsta **A- eller S-kort i just denna fil** efter faktisk GitHub/CI. S0-design får färdigställas nu, sedan får **S1-POC0/POC1 utföras test-only efter S0 och A1** utan att vänta på all A3/A4-frontend/importmodularisering. Produktionscutover kräver POC-go/no-go, faktiska berörda A-grindar och oberoende standardorakel. Se [ADR-0001](architecture/ADR_0001_CORE_REPLACEMENT_2026-11-26.md). Alla protokoll får egna versionsbundna S-del-PR med dokumenterade standarder, oberoende positiva/negativa/motsägande tester och gemensam motor. Ingen ny parallell roadmap eller gammal P7-etapp. Max en aktiv ändrings-PR. Utlovad automatisk bakgrundskörning förekommer inte. Bekräfta exakt PR-HEAD, alla required checks `SUCCESS`, oskadad main och squash före merge. Dokumentera varje färdigt A-kort och påverkat C01–C18-ID i planen eller en evidenslänk som planen refererar till.

**Statusregel:** `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `ACCEPTED_LIMITATION`, `DECISION_REQUIRED` och `NOT_VERIFIED` betyder olika saker. Ändra aldrig till `DONE` från enbart dokumentation eller CI-symbol. Länkad PR + resultat/negativt test + arkitekturdelta + återstående risk krävs. När en uppgift slutförts uppdateras tabellen **i samma PR** så att nästa konversation inte behöver gissa.

| Arbetskort | Utgångsstatus vid aktivering | Kommentar |
|---|---|---|
| **A0** | **DONE – PR #169 / main@fcf8171** | C02–C05: arkitekturhistorik, ägarskap, data- och regressionsmanifest; all required CI SUCCESS på PR-HEAD |
| **A1** | **DONE – PR #170 + negativt Required-test #173** | C03–C05: [G1–G7-kontrakt](architecture/A1_GUARD_CONTRACT_2026-11-26.md); två Required-checks API-verifierade; `unit-tests=SUCCESS` och `architecture-guard=FAILURE` gav `mergeable_state=blocked` i ej mergad #173 |
| **A2** | **DONE – PR #175 / main@73a3fe0** | C06: [HTTP-robusthetskontrakt](architecture/A2_HTTP_DISCONNECT_2026-11-26.md); 10 regressioner med riktiga TCP RST, 200/4xx/500-paritet, en Save och återläst SHA; båda Required-checks SUCCESS på exakt sista PR-HEAD; ingen ändrad nätverksmotor |
| **A3** | **IN_PROGRESS – del 1 #176, del 2 #177 och del 3 #179 DONE** | C03–C05: [del 1 DOM](architecture/A3_WORKSPACE_PANELS_2026-11-26.md), [del 2 workspace-/stale-revision](architecture/A3_WORKSPACE_REVISIONS_2026-11-26.md), main `16e6bd67444b1ef9eb96f2448edf04efda2ab17f`; inga nya A3-delar utan positivt/negativt orakel, korrekt Required CI, säker squash. UI-invalidering/sena `finally`, inspector, diagnos/import kvarstår |
| A4 | NOT_STARTED | Backend-import/ICMP-modularisering skyddad av A1 |
| A5 | NOT_STARTED | Oberoende referenser och komplexa topologier |
| A6 | NOT_STARTED | Pedagogisk funktion och testad elevresa |
| A7 | NOT_STARTED | Tydlig support-/begränsningsmatris |
| A8 | DECISION_REQUIRED / OPTIONAL | Empirisk mänsklig studie kräver separat godkännande |
| A9 | APPROVED_SCOPE / IMPLEMENTATION_NOT_STARTED | Full protokollutbyggnad godkänd som S-kort; ingen native ny motor påstås färdig |
| A10 | NOT_STARTED | Slutrevision och stängningsbeslut när föregående grindar klarats |

**Avslutsregel:** A0–A10-stabiliseringen får markeras CLOSED efter A10:s verifierade slutrapport och full spårning C01–C18, men **den beställda S0–S12-produktresan förblir aktiv** tills S12:s verkliga slutgrindar. A8 mänsklig studie kan vara DECISION_REQUIRED/NOT_VERIFIED; A9:s godkända S-utbyggnad får inte felmärkas som valfri eller färdig. Ingen fullständig RFC-certifiering eller mänsklig pedagogisk effekt får påstås utan evidens.

## Beslutssammanfattning

1. **Först: arkitekturspärrar och forensisk jämförelse.** Ingen stor moduluppdelning får påbörjas innan ett automatiskt regressionsskydd kan upptäcka att kod flyttas tillbaka till monoliten, att moduler tas bort eller att tillståndsägare dupliceras.
2. **Därefter: åtgärda bekräftad HTTP-robusthetsbrist** och återställ ett smalare frontend-entrypoint. Bryt ner backendmodulerna successivt – utan ändrade kontrakt, projektschema eller protokollsemantik.
3. **Parallellt: stärkt oberoende bevisning** genom fristående testvektorer, negativa/motsägande fall, större topologier och sparad före/efter-evidens. Testgrönt är ett nödvändigt villkor, inte protokollcertifiering.
4. **Sedan: utbildningsnytta och uttryckliga omfattningsbeslut.** Ett sammanhållet undervisningsflöde och en separat, etiskt genomförd användarstudie behandlas som olika leveranser. Saknade protokoll och realtidsfunktioner ska inte beskrivas som buggar i ett påstått stöd som aldrig beslutats.
5. **Slutlig acceptans:** gemensam CI, arkitekturbudget, verklig Chromium/X11, Save/Open/SHA, semantiska referensfall, dokumenterad rollback och inga öppna blockerande brister. Varje senare PR måste skyddas av samma spärrar.

## 1. Omfattning, sanningsklasser och historik

### 1.1 Rapportens faktiska utgångspunkt

Rapporten beskriver YadiLab som en deterministisk, avgränsad nätverkssimulator: Ethernetkodning, MAC-inlärning, VLAN, ARP, explicit IPv4-routing, ICMP med returväg och DHCP DORA är verkliga funktioner. **Dessa är tillgångar att bevara – inte problem som ska ersättas med en ny motor.** Rapporten har historiska CI-resultat **789/789 Python, 47/47 JavaScript och 29/29 pedagogiska fall**, och ett samlat kvalitativt betyg **8,2/10**. Siffrorna avser rapportens granskade SHA/PR och är **inte** en ny mätning av dagens `main` eller ett fastställt mål för ett framtida betyg.

Rapportens avsnitt 4 innehåller två typer av punkter: (a) faktisk underhålls-/robusthetsbrist, och (b) avsiktligt begränsat stödomfång eller otillräcklig extern evidens. Denna plan täcker båda, men använder inte ordet ”fel” för ett protokoll som programmet aldrig utgett sig för att simulera. Bedömningen att ingen ny *kritisk falskt positiv nätverksleverans* verifierades i rapporten ska också bevaras.

### 1.2 Viktigt: modulariseringens återfall

Användarens erfarenhet är att modulariseringen ”helt försvann” och måste genomföras på nytt. Den nuvarande kodinventeringen visar en **mer preciserad teknisk bild**: tidigare utdragna frontendmoduler finns fortfarande (bland annat `features/diagnostics/`, `features/sessions/`, `features/projects/` och `features/layout/`), men monolitens omfattning har åter ökat. I den historiska 3E-ändringen minskade `web/app.js` från cirka 2 421 till **2 237 fysiska rader**. På A0:s versionsbundna `main@f36435dd7b108756bdac6e3919c1cb1c61cf58d7` är den **2 977 fysiska rader** (**2 978 vid `split('\n')`-visning) – alltså **740 jämförbara rader mer (+33,1 %)** än den historiska slutpunkten. Den tidigare uppskattningen 741 blandade två olika räknemetoder. Detta är mätbar *återväxt i en central koordinator*, inte ett verifierat påstående om att samtliga tidigare moduler har raderats.

Även `network_core/import_plan.py` (**967 rader**) och `network_core/icmp_investigation.py` (**844 rader på nuvarande main; rapporten angav cirka 829**) kräver förvaltningsbar uppdelning. Radantalet är en riskindikator, inte självständigt bevis för buggar. En tidigare ES-modulgrafkontroll finns redan (`tests/test_web_import_graph.py`), men kontrollerar främst importer, nåbarhet och cykler – **inte** att kod inte samlas tillbaka i `app.js`. Därför behövs ett separat *anti-regressionskontrakt*.

### 1.3 Ej ändringsbara principer

- En kanonisk projektmodell, `validate_project` som slutlig validator och uttryckliga nod-/port-/kabelidentiteter.
- Ingen uppfunnen gateway, kabel, route, MAC eller IP; dokumenterat och simulerat skiljs från verkligt observerat.
- Samma protokollutfall före/efter rena refaktoreringar; inget nytt nätverkssimuleringslager.
- Oförändrat projektformat, importkontrakt, API-kontrakt, explicit Save, SHA-256, atomär lagring och stale-response-skydd tills separat ändring uttryckligen beslutats.
- Linux som enda stödda plattform. Externa verktyg kan användas som *separata, manuellt kontrollerade referenslaboratorier*, inte bli dolda runtimeberoenden.
- En PR i taget; ingen merge vid FAIL/PENDING, ingen kringgång av main-skydd.

## 2. Fullständig täckningsmatris för rapporten

| ID | Rapportområde / observation | Klass | Åtgärd eller beslut | Verifieringskrav |
|---|---|---|---|---|
| C01 | Ethernet/MAC/VLAN, ARP, IPv4, ICMP, DHCP är verkligt implementerade | Bevara styrka | Skydda befintlig motor, negativ evidens och persistens vid samtliga ändringar | Referensfall, kontrakts- och regressionstester |
| C02 | Historiskt gröna 789/47/29 samt Chromium/X11/ELK | Bevara evidens | Registrera SHA och környckel; skilj historiska resultat från nya | Komplett CI på varje slutlig PR-HEAD |
| C03 | `web/app.js` cirka 2 978 rader | Arkitekturrisk | Frys tillväxt, extrahera ansvar, tunn koordinator | Modulägarskap, radbudget, dependency- och beteendetest |
| C04 | `import_plan.py` 967 rader och `icmp_investigation.py` cirka 829 i rapporten | Arkitekturrisk | Dela interna ansvar utan andra validatorer, motorer eller scheman | Före/efter-testvektorer, API-/persistensparitet |
| C05 | Tidigare modularisering har förlorat sin praktiska effekt | Nyckelregression | Forensisk inventering + arkitekturspärrar; förhindra återföring | CI ska fälla återmonolitisering och modulbortfall |
| C06 | ConnectionResetError/BrokenPipeError vid avbruten HTTP-klient | Observerat robusthetsfel | Säkra skrivväg och klientavbrott utan sekundärt felsvar | Reproducerat disconnect-test utan oönskad traceback |
| C07 | Otillräcklig oberoende protokollvalidering | Verifieringslucka | Nya fristående orakel, RFC-vektorer och separat labbjämförelse | Versionslåsta indata, utdata och avvikelselogg |
| C08 | Komplexa topologier och gränsfall ej systematiskt uttestade | Verifieringslucka | Matris för multi-hop, asymmetri, VLAN, session/race och import | Positiva, negativa och motsägande tester |
| C09 | Sammanhållet undervisnings-UI ofullständigt | Produktlucka | Inventera faktisk UI-funktion, specificera minsta flöde | Browser- och pedagogiska korrekthetstester |
| C10 | Mänsklig inlärningseffekt ej empiriskt mätt | Forskningslucka | Separat valfri studie; rapportera NOT_VERIFIED tills data finns | Förregistrerad metod, samtycke, jämförelsegrupp |
| C11 | Switchloopar avvisas utan STP | Dokumenterad begränsning | Behåll tydlig avvisning; separat beslut om STP-motor | Negativt test och ärlig UI-etikett |
| C12 | IPv4-fragmentering saknas | Dokumenterad begränsning | Ange unsupported; överväg separat RFC-avgränsat kodkort | Fragmentgränser och ingen falsk leverans |
| C13 | Generell TCP/UDP, köer, bandbredd, tidsfördröjning saknas | Dokumenterad begränsning | Beslutsmatris: avgränsa, extern labbreferens eller ny motor | Ingen syntetisk RTT/kapacitet utan modell |
| C14 | DHCP relay och flera servrar saknas | Dokumenterad begränsning | Skriv explicit supportmatris; designa separat eventuell utökning | DORA/lease-regression och konflikttester |
| C15 | OSPF/BGP/STP/IPv6/NAT/ACL m.m. saknas som native | Omfångsgap, ej verifierat fel | Ingen tyst implementation; välj enskilt per användarbeslut | Oförändrade unsupported-kontrakt tills godkänt |
| C16 | Betyg 8,2/8,3/8,0/8,4/3,0 och samlat 8,2 | Kvalitativ baslinje | Bevara värden och deras begränsningar; skapa kvantifierbara mått | Ny oberoende granskning, ej automatiskt ”höjt betyg” |
| C17 | Ej full rad-för-rad, långtids-/lasttest eller verklig maskinvalid. | Granskningsbegränsning | Täck med riskbaserad fördjupning och transparens | Tydlig verifierad/ej verifierad scope |
| C18 | Rapportens goda historiska felrättningar och nej till svagare validering | Bevara process | Avvisa testförsvagning, regressionsborttag och genvägar | Branchregler, review, diffgranskning |

**Krav på spårbarhet:** Inget ID C01–C18 får stängas som `DONE` enbart därför att en text har ändrats. Varje ID måste ha kod-/testbevis, ett uttryckligt `SUPPORTED/UNSUPPORTED`-beslut eller en dokumenterad `NOT_VERIFIED`-begränsning. Samtliga ID återkopplas i slutrapporten.

## 3. Arkitektur: återuppbyggnad utan nytt återfall

### 3.1 Nollpunkt – mät ansvar före flytt

Skapa en maskinläsbar arkitekturinventering från `main` med fil, ansvar, import/export, tillståndsägare, antal rader, cykliskt beroende, statiska HTTP-sökvägar och testtäckning. Jämför mot historiska modulariseringscommits (bl.a. 3C/3D/3E) och aktuella `app.js`. Inventeringen måste identifiera **vilka konkreta funktioner som återförts eller tillkommit**. Dra inga slutsatser om kodförlust enbart från radantal. Spara godkänd baslinje i repo och kräv PR-diff mot denna.

### 3.2 Ägarskapsgränser som inte får blandas ihop

| Del | Ska äga | Ska inte äga |
|---|---|---|
| `web/app.js` | bootstrap, uppkoppling av moduler, övergripande samordning | domänberäkningar, omfattande panelrendering, duplicerad sessionslogik |
| Workspace-/state-modul (föreslagen) | kanoniskt projekt, revisioner, snapshot, invalidering | nätverksprotokoll och DOM-specifik presentation |
| `features/projects/*` | importflöde, mapping, Save/Open och konflikthantering | alternativ projektvalidator eller bakgrunds-save |
| `features/diagnostics/*` | API-frågor, förklaring och panelrendering | nya nätverksfakta som inte kommer från motorn |
| `features/sessions/*` | sessions-ID, generation, busy/Stop, stale guards | kanonisk projektmodell och projektskrivning |
| `features/layout/*`, `canvas.js` | visuell layout och kamera | ändring av fysisk topologi |
| `network_core/import_*` | tydliga delar av en enda importpipeline | alternativ validering, implicit skapade kablar |
| `network_core/icmp_investigation*` | kandidatval, evidens, diagnos, livscykel med en motor | duplikat av `EchoExchange` och läckta facit |
| `network_core/server.py` | HTTP-gräns, felklassificering och avbrott | förvanskning av domänresultat |

### 3.3 Obligatoriska skydd mot att modularisering ”försvinner igen”

**G1 – Baslinje och ratchet:** Inför exempelvis `architecture/baseline.json` med filradantal, maxstorlekar, modullista och godkänd graf. En PR får inte öka `web/app.js`, `import_plan.py` eller `icmp_investigation.py` över *senast accepterad* budget; minskade budgetar följer med `main` och kan inte tyst återställas. Radantal är en kompletterande spärr, aldrig enda kvalitetsmåttet.

**G2 – Innehållsliga gränser:** Kontroller utöver dagens importer-/cykeltest ska avvisa förbjudna modulberoenden, duplicerad state ownership, session/diagnostiklogik direkt i `app.js` och återinförd DOM-/API-formatering där separata moduler äger den. Använd AST-baserad analys där det går; ordsökning ensam duger inte som kvalitetsgaranti.

**G3 – Modulkontrakt:** Varje utbruten modul får dokumenterade input/output, tillåtna beroenden, ansvar, utpekade tester och ett offentligt API. Ändrad eller borttagen modul kräver godkänt migrationsbeslut och paritetstest, inte bara borttagen import.

**G4 – Obligatorisk CI-status:** Ett separat `architecture-guard`-jobb ska vara *required* i branchskyddet tillsammans med funktionell CI. Det får inte kunna `skip`-passera när relevanta filer ändras. Testa spärren med avsiktligt ogiltiga fixtures: borttagen modul, cirkelimport, återinförd koordinatorlogik, otillåtet beroende och överskriden budget.

**G5 – Granskningskrav:** CODEOWNERS eller namngiven ansvarig för `web/app.js`, `web/features/**`, `network_core/import_*`, `icmp_investigation*`, `AGENTS.md` och arkitekturbaslinjen. Ändringar som höjer budget, tar bort moduler eller försvagar skydd kräver särskilt uttryckligt godkännande. Branchregler ska förhindra otestad direktpush.

**G6 – Beteendeparitet:** Samma fixtures och konkreta utdata före och efter flytt (inkl. JSON-kontrakt, svensk UI-text där relevant, Save/Open SHA, stale responses, Stop, replay, arbetsytebyte). Inga mocks som ensamt facit för det som motorn ska bevisa.

**G7 – Långsiktig övervakning:** Publicera en liten per-PR arkitekturrapport med trend för tre stora filer, totalt antal moduler, ansvarsfördelning och `architecture-guard`-status. En senare feature-PR som försämrar gränserna blockeras innan merge. Mät igen efter varje 5:e merge eller större feature-batch.

### 3.4 Målnivåer och praktisk kompromiss

Föreslagna *förvaltningsmål*, inte bevis för korrekt kod: `app.js` under **1 500 rader** i första konsolideringen och långsiktigt **cirka 900 eller färre** när ansvar faktiskt flyttats; `import_plan.py` och `icmp_investigation.py` under **500–600 rader vardera** endast efter meningsfull delning. Ingen tillåten förändring bara för att jaga radsiffror. Först låses aktuell budget; varje PR ska ratcheta ned den. Ett undantag kräver synligt arkitekturbeslut, ny budget och parallell skyddstestning.

## 4. Arbetsprogram och beroenden

| Ordning | Arbetskort | Prioritet | Förutsättning | Leverans och exit-kriterium |
|---|---|---|---|---|
| A0 | Rebaslinje & forensisk modulgranskning | P0 | Nytt användaruppdrag godkänt | Inventering, PR-historik, drift-/testmanifest, modul-/ansvarskarta |
| A1 | Arkitekturspärrar (G1–G7) | P0 | A0 | Required CI, negativt testad budget-/import-/ägarskapsspärr |
| A2 | HTTP-klientavbrott & BrokenPipe | P1 | A1 | Reproducerad brist, kontrollerad disconnect, icke-duplicerat svar |
| A3 | Frontend: demontera återväxt i `app.js` | P1 | A1 | Smalare entrypoint, modulparitet, Chromium + race + SHA |
| A4 | Backend: modulgränser för import & ICMP | P1 | A1, delvis A3 | Samma parser/validator, samma API, samma felkoder, mindre koppling |
| A5 | Oberoende referenser och gränsfall | P1 | A2–A4 kan löpa delvis parallellt | Nya fristående referensfall, komplexitetsmatris, avvikelser lösta |
| A6 | Pedagogiskt UI och uppföljning | P2 | A3, A5 | Ett verkligt användarflöde som ej läcker facit; negativ testmatris |
| A7 | Explicit begränsnings- och protokollbeslut | P2 | A5 | Full `SUPPORTED/UNSUPPORTED/DECISION_REQUIRED`-matris |
| A8 | Separat empirisk användarstudie (valfri) | P2 | A6 och särskilt godkännande | Metod eller fortsatt tydlig `NOT_VERIFIED` |
| A9 | Godkänd native protokollutbyggnad genom S0–S12 | P1 produktmål | S-kortens teknik-/testberoenden och A7 | En avgränsad motor i taget, oberoende facit, ingen dold emulering |
| A10 | Slutrevision, rollback och beslut om avslut | P0 som slutgrind | Relevanta A-kort | Slutrapport C01–C18, oförändrade invariants, grön CI |

**Tidsplanering:** Ordningen ovan är beroendestyrd; ingen kalenderdeadline eller ”alla protokoll färdiga” utlovas utan kapacitetsunderlag och uttryckliga omfångsbeslut. A0–A2 är första leveransgruppen. A3 delas i små, funktionellt begränsade PR:er. Backenddelning och nya referensfall bör inte kombineras i samma PR. A9 är en reserverad beslutsgrind, inte en automatisk beställning.

## 5. Detaljerade arbetskort

### A0. Forensik och bevisad nollpunkt

**Leveransevidens:** [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169), [A0-rapport](architecture/A0_FORENSIC_BASELINE_2026-11-26.md), [Git-manifest](../architecture/a0_baseline.json) och [exakt ES-importgraf](../architecture/a0_frontend_imports.json). Test: `tests/test_a0_forensic_manifest.py` med negativt ändrad modul, orphan/cykel, missad import och falskt Git-blobbevis. Räckvidd: statisk inventering, ingen runtimeändring och ingen installerad A1-spärr. **Status: A0 DONE – PR #169 verifierad squash-merge, CI SUCCESS.**

**Utför:** Läs exakt aktuell `main`, samtliga aktiva PR:er och senaste CI. Dokumentera commit där varje modul extraherades, vilka moduler som fortfarande finns och vilka ansvar som åter dykt upp i `app.js`. Ta fram callgraph/importgraf, state- och eventkarta, antalet direkta DOM-beröringar, funktioner med hög komplexitet samt sessionernas generations-/stale-guards. Lägg samtliga regressionsfall och filbytes i ett versionsbundet manifest.

**Acceptans:** skillnaden mellan 3E (`app.js` 2 237) och nuvarande 2 978 har förklarats i termer av funktion/ansvar, inte endast antal rader; modulnivåer finns dokumenterade; ingen kod har ändrats före arkitekturbaslinjen.

### A1. Arkitekturspärrar före ny extraktion

**Leveransevidens A1 (DONE):** [PR #170](https://github.com/Northsw-spec/YadiLab/pull/170) (`main@b55cdad861e88839924c91f0e09f5e48529e4427`), [A1:s G1–G7-kontrakt](architecture/A1_GUARD_CONTRACT_2026-11-26.md), `architecture/baseline.json`, `tools/architecture_guard.py`, 17 positiva/negativa tester i `tests/test_architecture_guard.py`, `.github/workflows/architecture_guard.yml`, CODEOWNERS och kontinuerlig trendrapport. [Main-ruleset #27419615](https://github.com/Northsw-spec/YadiLab/rules/27419615) kräver **både** `architecture-guard` och `unit-tests` från GitHub Actions (integration 15368); strict aktiverad. **Oberoende skarpt negativt test:** [PR #173](https://github.com/Northsw-spec/YadiLab/pull/173), HEAD `90e5ab61e23ee8a824c42f48f253d33e28cd76ce`, ändrade endast det fristående arbetsflödet med avsiktlig `exit 17`. Båda `unit-tests` blev SUCCESS medan båda separata `architecture-guard` blev FAILURE; GitHub svarade `mergeable_state=blocked` och PR:n stängdes **utan merge**. [Reproducerbar CI-evidens #171](https://github.com/Northsw-spec/YadiLab/issues/171#issuecomment-7197176467). Ingen ändring av motor, schema eller Save/Open. **Begränsning:** statisk JavaScript-modul/ansvarskontroll är inte fullständigt AST- eller dataflödesbevis; fulla beteendetester och kodgranskning krävs fortsatt.

**Utför:** Implementera G1–G7. Lägg till automatiserat test för `architecture/baseline.json`, förbjudna beroenden, svällande entrypoint, modulförsvinnande och kopierad sessionsstate. Skapa kompatibel uppdateringsprocess: budget får sänkas automatiskt men höjning kräver separat, granskad ändring. Gör den obligatoriska checken *required* i GitHub branch rules innan A3.

**Negativ provning:** simulerat borttagen `features/sessions/icmp-investigation.js`, cirkelimport, flyttad ping-presentation till `app.js`, förbjuden import från presentation till storage, falskt höjd radbudget och borttagen testfil ska alla ge röd kontroll. Ett rent refaktoreringsexempel ska passera.

**Acceptans:** faktisk branchregel blockerar merge på `architecture-guard=FAIL`, även om vanliga enhetstester passerar. Bevara nuvarande `test_web_import_graph.py` och utöka, ersätt inte med svagare test.

### A2. HTTP-resiliens vid klientavbrott

**Leverans-/acceptansevidens (C06):** [PR #175](https://github.com/Northsw-spec/YadiLab/pull/175), [detaljerad teknisk rapport](architecture/A2_HTTP_DISCONNECT_2026-11-26.md), `network_core/server.py` och 10 fall i `tests/test_http_disconnect.py` registrerade i den obligatoriska arkitekturtestinventeringen. Riktiga TCP-RST före svar och under JSON/statisk/XLSX-body, aborterat men atomiskt utfört Save (exakt ett anrop och stabil SHA), felaktig JSON 422, oväntad intern exception 500 och `OSError(EIO)` verifierar att endast frånkopplingar undertrycks. **Status: A2 DONE – [PR #175](https://github.com/Northsw-spec/YadiLab/pull/175) squash-mergad efter Required-checks SUCCESS på exakt PR-HEAD; main `73a3fe0fb490ec8a7dbd5487ba8c4527ac9ea2ea`.** Ingen kod för nätverkssimulering eller projektformat ändras. Vid tappad kvittens efter utförd Save krävs explicit återläsning av SHA, aldrig automatisk retry.

**Utför:** Reproducera serverns `ConnectionResetError`/`BrokenPipeError` i en isolerad HTTP-integration med klient som stänger socket före/under svar. Hantera fel vid både `end_headers`, `wfile.write` och relevanta statiska svarsvägar; avbryt fortsatt skrivning på samma stängda socket. Undvik att en exceptionshanterare försöker skriva JSON-fel på en redan bruten anslutning. Klassificera förväntad frånkoppling utan att dölja verkliga serverfel.

**Negativa fall:** icke-bruten klient får fortsatt exakt samma HTTP-status/body; felaktig JSON får korrekt 4xx; oväntad serverexception syns som avvikelse; avbruten klient orsakar inte retried Save eller dubbla mutationer. Jämför sparade SHA före/efter.

**Acceptans:** reproducerbart disconnect-test PASS utan oönskad traceback; befintliga behörighets-, lagrings- och HTTP-tester förblir gröna. Dokumentera om eventuellt kvarvarande enskilda `BrokenPipeError` i extern miljö endast är loggstörning eller verkligt fel.

### A3. Frontendmodularisering som faktiskt håller

**Accepterad leverans (del 1):** [PR #176](https://github.com/Northsw-spec/YadiLab/pull/176) extraherade dropdown-DOM till `web/ui/workspace-panels.js` ([A3-dokument](architecture/A3_WORKSPACE_PANELS_2026-11-26.md)) efter **alla fem CI-körningar SUCCESS** på sista PR-HEAD, squash `35ed34bd76551849ca79ebc5ca75813f2540e5d1`. 2 977→2 926 app-rader. **Accepterad leverans (del 2):** [PR #177](https://github.com/Northsw-spec/YadiLab/pull/177), [revisionskontrakt](architecture/A3_WORKSPACE_REVISIONS_2026-11-26.md), verifierat squash-mergad som `16e6bd67444b1ef9eb96f2448edf04efda2ab17f` efter fem Required/ELK-körningar SUCCESS på exakt PR-HEAD. Workspace-, edit- och Builder-generationerna har en projektägd modul utan duplicerat kanoniskt projekt; samma stale-regler används av Save/Open, import, sessioner och diagnostik. **Detta slutför inte A3:** UI-invalideringens sidoeffekter, sena `finally`, inspector, diagnostik och import-/Save/Open-presentation återstår i separata PR:er.

**Utför i små PR:er:** (1) flytta arbetsyterevisioner och invalideringslogik till en enda explicit ägare; (2) flytta Builder/inspector-handlingar och detaljpresentation till granskade moduler; (3) separera diagnosorkestrering från formattering; (4) flytta import-/mapping-/Save/Open UI-trådarnas presentation och statesynk till egna features; (5) lämna `app.js` som kompositionsrot. Detaljerad ordning avgörs av A0:s beroendegraf, inte efter filstorlek ensam.

**Skydda:** eventlyssnare registreras en gång; sena HTTP-svar och gamla `finally` får inte skriva i ny workspace/session; urval, paketanimation, zoom/ELK, kabelankare, snapshot och dataexport har före/efter-paritet.

**Acceptans per PR:** någon ansvarsfunktion flyttas på riktigt; minskad arkitekturbudget och väl definierat API; minst ett positivt och ett negativt test; riktig Chromium; Save/Open med samma SHA; ingen cirkulär modulimport; samma distributionssökvägar och Linux-beteende. A1-spärren ska kvarstå grön.

### A4. Backendmodularisering utan andra sanningar

**Import:** dela `import_plan.py` efter ansvarsgränser som källa/mapping, kandidatbyggnad, konflikt- och beroendeanalys, dokumenterad proveniens och slutligt godkänd plan. Slutlig `validate_project` förblir en och samma. Testa strikt JSON, dubblettnycklar, käll-ID, utelämnade kablar, VLAN/IP/ruttberoenden, avvisade konflikter samt gamla importkvitton.

**ICMP:** dela `icmp_investigation.py` efter kandidatupptäckt, observationsprojektion, övnings-/evidensregler och sessionslivscykel; ingen andra Echo-motor och inget avslöjat dolt facit. Testa mottaget ICMP-routerfel kontra inget fel, TTL, uteblivet Echo Reply, diagnosspärrar, återställning och utgångna sessioner.

**Acceptans:** byte-för-byte-kompatibla API-/rapportsvar där ordning är kontraktsbunden; i andra fall semantiskt identiska normaliserade resultat. Inget nytt projektschema, inga nya interna felklasser som ändrar klienternas semantik utan separat godkännande.

### A5. Oberoende nätverksvalidering och topologiskt djup

**Utför:** bygg tabeller med förutbestämda indata och *oberoende* förväntat utfall från standardspecifikation, handverifierade paket och i förekommande fall separata referenslabb. Förväntat resultat får inte härledas från YadiLabs egen utskrift. Prioritera Ethernet/VLAN/MAC, ARP med cache, IPv4 longest-prefix & next-hop, TTL och returväg, ICMP 3/0 och 11/0, DHCP DORA/T1/T2, ogiltig data och kontradiktoriska dokument.

**Topologier:** flera switchar och routrar, asymmetrisk retur, nedstängd mellanport, korsade VLAN, två möjliga rutter, saknat explicit next-hop, upprepade sessionsstarter, konkurrerande Save/Open och stora importtabeller. En loop utan STP ska **avvisas tydligt**, inte simuleras som om STP fanns.

**Acceptans:** publicera antal referensfall och faktiska PASS/FAIL med nämnare, ursprung och versionslås; för varje avvikelse ange `BUG`, `MODEL_LIMITATION` eller `ORACLE_ERROR` efter analys; ingen automatisk ”RFC-certifierad”-etikett.

### A6. Sammanhållet men källärligt undervisningsflöde

**Utför:** inventera befintliga ICMP-/DHCP-lektioner och mät exakt vilka steg som saknas i det större UI. Utforma ett smalt arbetsflöde med nio tidigare beslutade pedagogiska rubriker, konkurrerande hypotes, test som kan motbevisa elevens hypotes, positivt/negativt utfall, återställning och efteranalys. Håll `DOCUMENTED`, `SIMULATED`, `UNKNOWN` och `NOT_VERIFIED` tydligt åtskilda; förbjud att facit läcker via API, DOM eller animerad trace före rätt steg.

**Acceptans:** verklig Chromium med komplett elevresa, alternativ felorsak för samma symptom, tidigare felaktig hypotes och korrekt återhämtning; rapportering med sparad projektintegritet. Utvärdering av pedagogisk logik i automatiserade fall är *inte* bevis för mänsklig inlärningseffekt.

### A7. Transparent stödmatris för allt som inte simuleras

**Utför:** inventera explicit följande poster: OSPF, BGP, STP, IPv6, NAT, ACL, generell TCP/UDP, IPv4-fragmentering, DHCP relay, multi-server DHCP, köer, bandbredd, jitter och faktisk fördröjning. För varje post välj: `UNSUPPORTED + korrekt dokumentation/avvisning`, `STATISKT UNDERVISNINGSEXEMPEL`, `SEPARAT MANUELLT LABB`, eller `FÖRSLAG OM NY NATIVE FUNKTION – REQUIRES_APPROVAL`.

**Acceptans:** test som avvisar falskt påstående om native support; UI/dokumentation stämmer med faktiskt kodstöd; inga externa verktyg installeras eller körs av appen genom denna plan.

### A8. Pedagogisk effekt – valfri empirisk verifiering

**Utför först efter separat beslut:** ange en förregistrerad hypotes, rekryteringskriterier, jämförelse mot alternativ metod, före-/eftertest av nätverksfelsökning, rimlig bias-/bortfallshantering och dataskydd/samtycke. Mät faktiska prestationer, inte ”AI-konfidens” eller generiska sannolikheter. Om ingen studie genomförs ska kunskapsluckan **fortsätta markeras NOT_VERIFIED** utan att blockerande omfång utökas.

### A9. Explicit godkänd protokoll-/motorutbyggnad, nu genom S-spåret

**Användarens nya beslut 2026-11-26:** YadiLab ska få STP/RSTP, IPv6, DHCP-relay/multiserver, generell TCP/UDP, OSPF/BGP/EIGRP, ACL/NAT, säkerhet, tidsmodell, WAN/trådlöst, applikationer och Packet Tracer 9.0:s industriella protokoll med verkligt källförankrat stöd. A9 är alltså APPROVED_SCOPE men IMPLEMENTATION_NOT_STARTED. Allt delas i S1–S12 med separata, små verifierade PR:er, och endast efter respektive beroendegrind. VM, emulator, Cisco IOS, externa protokollprocesser och live scan är fortsatt förbjudna. A8:s mänskliga studie är INTE beställd.

### A10. Slutrevision och stängning

**Utför:** kör alla obligatoriska testgrindar på sista PR-HEAD, verifiera ren squashhistorik och jämför `main` efter merge. Kontrollera arkitekturrapporten och prov att framtida återmonolitisering blockeras. Sammanställ C01–C18: status, bevis, risk, explicit omfångsbeslut och eventuell restpunkt. Genomför separat riskbaserad kodgranskning och relevant långkörning; beskriv klart det som inte testats.

**Acceptans:** inga blockerande P0/P1-fel, alla aktiverade A-kort reproducerbara, Required CI utan bypass, explicit Save/Open och riktiga unsupported-etiketter. **A10 avslutar enbart A-stabiliseringsspåret, inte den beställda S0–S12-resan.**

## 6. Gemensam test- och acceptansmatris

| Testkategori | Positivt obligatoriskt utfall | Negativt obligatoriskt utfall |
|---|---|---|
| Topologi och schema | Explicit kabel och port fungerar | Antagen kabel/gateway/route avvisas |
| L2, ARP och VLAN | Korrekt MAC-lärande och ARP-svar | VLAN-isolering, ARP-miss, loop utan STP |
| IPv4 och ICMP | Verifierad Request + Reply och korrekt router-ICMP | Saknad returroute, TTL-expiry, genererat men ej mottaget fel |
| DHCP | DORA/lease/T1/T2 inom stödd modell | Saknad relay/multi-server hävdas inte som fungerande |
| Import och lagring | Samma importbeslut, explicit Save/SHA och återstart | Dubbel JSON-nyckel, trasig källrelation och stale Save |
| Frontend/session | Normal render/Stop och återspelning | Sena svar, ändrat mål, byte av workspace, förlorat Stop-svar |
| HTTP | Komplett klient får korrekt status och svar | Disconnect ger ej sekundärt felsvar eller okontrollerad traceback |
| Modularkitektur | Entrypoint minskar och godkända beroenden består | Monolittillväxt, borttagen modul, cykel, kopierad state fäller CI |
| Pedagogik | Flera rimliga hypoteser och motbevisande test | Inget förtida facit, inga påhittade live-resultat |
| Distribution | GitHub required checks och Linux Chromium/X11 PASS | Fail/pending/skip kan inte mergas förbi skydd |

## 7. Prioritering, ansvar, risk och ändringskontroll

**Prioritetsdefinition:** P0 = blockerar säker förvaltning eller korrekt slutstatus; P1 = verifierat fel/hög arkitekturrisk; P2 = produktlucka eller verifieringslucka; P3 = större utökning som måste beställas separat. Föreslagna roller: arkitekturansvarig granskar G1–G7; backendansvarig granskar import/ICMP/HTTP; frontendansvarig granskar sessioner och UI; oberoende testgranskare granskar referensorakel; projektägaren beslutar uttryckligen om nya protokoll och forskning. Roller är ansvarstyper, inte namngivna personer.

| Risk | Signal | Förebyggande åtgärd |
|---|---|---|
| Monoliten återväxer efter modularisering | Fler ansvar/ökad budget i `app.js` | Required ratchet + ägarskapskontroll + CODEOWNERS |
| Refaktorering ändrar simuleringsresultat | Avvikande referensvektor eller API | Fixture-paritet, browser, negativt test; rollback |
| Testsvit blir ”grön” efter försvagning | Borttagna assertions/skip eller ny mock | Granskning av testdiff, skyddade negativa fall |
| HTTP-fix döljer verkliga undantag | Alla undantag loggas som disconnect | Smal exceptionklassificering och separat serverfelstest |
| Stödmatris förvandlas till tyst protokollscope | Ny endpoint/motor utan beslut | Approval-grind i A7/A9; `UNSUPPORTED` tills testad |
| Pedagogiskt innehåll påstår livebevis | UI säger ”verklig” om simulering | Källmärkning och konsekvent negativt påståendetest |
| Mänsklig effekt förväxlas med automatisk kvalitet | 29/29 citeras som elevresultat | `NOT_VERIFIED` tills empirisk studie finns |

**PR-mall:** problem/rapport-ID; exakta före-/eftergränser; berörda moduler och ägare; vilket tillstånd som får ändras; oberoende positivt och negativt facit; arkitekturdelta och budget; testkommando och resultat; sparad SHA; rollback; explicit deklaration att inget unsupported protokoll blivit ”native”.

**Mergebeslut:** A0/A1 låser först baseline och skydd. Varje efterföljande PR gör endast ett avgränsat arbete. All required CI måste vara `SUCCESS` på *exakt slutlig PR-HEAD*, PR mergebar, förväntad `main` oförändrad och inga blockerande reviews. Squash. Gör nytt test på ändrad HEAD. Vid blockerande skillnad: ingen merge, rapportera `BLOCKED` och åtgärda i samma PR.

**Rollback:** återställ med ny PR som återinför senast fungerande innehåll, inte otestad direktpush. Arkitektur- och säkerhetsgrindar får inte samtidigt sänkas för att underlätta rollback. Bevara migrerings-/kompatibilitetstester, fixtures och logglänkar så det går att visa att regressionsskydden fortfarande är aktiva.

## 8. Definition av färdigt arbete

- [ ] Rapporterade konkret observerade fel och stora arkitekturrisker C03–C08 är stängda med evidens.
- [x] `architecture-guard` är obligatoriskt i branchskyddet; [PR #173](https://github.com/Northsw-spec/YadiLab/pull/173) visade blockerad merge trots `unit-tests=SUCCESS` (test-PR stängd utan merge).
- [ ] `app.js` är en verklig tunnare koordinator med minskad accepterad budget; backendmoduler är ansvarsmässigt uppdelade.
- [ ] Tidigare utdragna moduler har fortsatt en ägare och skyddad import-/kontraktsgräns efter *minst en efterföljande feature-PR*.
- [ ] Oberoende referenstester, större topologier och robust HTTP-disconnect har dokumenterade resultat.
- [ ] Sammanhållet pedagogiskt flöde har verifierats i riktig Chromium **eller** klassificerats som restpunkt som kräver nytt beslut.
- [ ] Empirisk elevinlärning och samtliga unsupported protokoll har sanningsenlig status; inga obevisade förbättringspåståenden.
- [ ] C01–C18 har slutstatus: `DONE`, `ACCEPTED_LIMITATION`, `DECISION_REQUIRED` eller `NOT_VERIFIED`, med motivering och spårbar evidens.
- [ ] Dokumenterad risklista, rollback och kvarstående osäkerheter är accepterade.
- [ ] Ingen ny utvecklingsetapp har aktiverats utan uttryckligt användarbeslut.

## 9. Källor och versionsgränser

**Primär rapport:** *Teknisk granskning av YadiLab – 2026-11-26*, bifogad av användaren, samtliga avsnitt 1–6. Framför allt avsnitt 2 (historiska CI-resultat), avsnitt 3 (bevarade styrkor), avsnitt 4 (brister/risker), avsnitt 5 (kvalitativa betyg) och avsnitt 6 (slutbedömning). Rapportens SHA `fe111c5368d4a4758bc86123b06447f34ba2a02e` är historisk, inte aktuell.

**Aktuell verifierad kodinventering:** `Northsw-spec/YadiLab`, `main@82fca139cc43e12ff8c21bbb3427ab4f87588fd5` (vid planens tillkomst). Följande har kontrollerats: `web/app.js` (2 978 rader), `network_core/import_plan.py` (967), `network_core/icmp_investigation.py` (844), befintliga `web/features/*`, `tests/test_web_import_graph.py`, `.github/workflows/ci.yml` och `AGENTS.md`.

**Historiska modulariseringsspår:** 3C/PR #53, commit `2916ca7c9c3f3c5edf7dbb5d07a35f97f632dcb8`; 3D2/PR #56, commit `d34f912f882f66ad9a6dcc4522816c0d6618045d`; 3E/PR #59, commit `17acb51c8c64c3b4b7a1026514cb8b0a2177a127` (efter extraktion 2 237 rader i `app.js`). Historiska beskrivningar ska dubbelkontrolleras mot faktisk kod och CI innan något cherry-pickas.

**Direktlänkar:** https://github.com/Northsw-spec/YadiLab ; https://github.com/Northsw-spec/YadiLab/commit/17acb51c8c64c3b4b7a1026514cb8b0a2177a127 ; https://github.com/Northsw-spec/YadiLab/blob/82fca139cc43e12ff8c21bbb3427ab4f87588fd5/tests/test_web_import_graph.py ; https://github.com/Northsw-spec/YadiLab/blob/82fca139cc43e12ff8c21bbb3427ab4f87588fd5/network_core/server.py .

**A3 del 3, diagnostisk UI-race (IN_PROGRESS):** DHCP Discover/Offer och read-only DORA måste frigöra busy när relevant indata invalidideras och tillåta nytt försök utan att invänta ett gammalt HTTP-svar. Endast det aktuella generations-ID:t får frigöra busy i `finally`. Två verkliga Chromium-regressioner håller det första svaret tillbaka tills ett andra försök startat och bevisar att det gamla svaret inte återaktiverar UI, läcker gammal diagnostik eller ändrar projektdata. Denna del är inte DONE före båda Required-kontrollerna på exakt HEAD och verifierad squash-merge. Ingen motor-/schemamutation.

**Uppdaterad statusnot (2026-11-26):** A0 DONE (#169), A1 DONE (#170 + separat Required-negativ #173), A2 DONE (#175). A3:s del 1 #176, del 2 #177 och del 3 #179 är verifierat squash-mergade (main efter #179: 7dbe2285cde7ea87c08afce1c58d36cd0f5697e7), men **hela A3 IN_PROGRESS**; fortsätt Builder/Inspector, diagnos/import. Codex följer [exekveringspolicyn](CODEX_EXECUTION_POLICY.md) och får inte vänta passivt på CI. **A8 DECISION_REQUIRED**, **A9 APPROVED_SCOPE** genom S0–S12, P0–P7 CLOSED.

---

## 10. Det nya huvuduppdraget – full simulator, inte emulator

**Beslut:** YadiLab ska bli en **komplett, tekniskt korrekt, precis, pedagogisk Linuxbaserad nätverkssimulator**, med målet att mätbart överträffa Cisco Packet Tracer 9.0. Den får INTE köra VM, gästande OS, Cisco IOS binärer, emulera maskinvara, starta FRRouting/GNS3/EVE-NG/ns-3 som runtime, skanna riktiga nät eller skapa en parallell "låtsasmotor". De befintliga riktiga Ethernet/ARP/IPv4/ICMP/DHCP-funktionerna ska återanvändas och migreras kontrollerat. Ciscos [officiella protokoll- och UI-katalog](https://tutorials.ptnetacad.net/help/default/intro.htm) och [9.0-industrinyheter](https://tutorials.ptnetacad.net/help/default/whatsNew.htm) är konkurrensbaslinje, medan standarder och oberoende orakel avgör teknisk korrekthet. Se [tre forskningsvågor](research/PACKET_TRACER_GAP_ANALYSIS_2026-11-26.md).

**En enda aktiv plan:** denna fil; A0–A10 = kvalitet och arkitekturstabilisering, S0–S12 = nu beslutad produktutbyggnad. [MASTERPROMPT](MASTERPROMPT.md) = övergripande produkt- och kodagentkontrakt. [PROTOCOL_COVERAGE_MATRIX](PROTOCOL_COVERAGE_MATRIX.md) = paritet på feature- och versionsnivå. [Deterministiskt simulatorkontrakt](architecture/DETERMINISTIC_ENGINE_CONTRACT.md) = norm för S1 och efterföljande motor. Dessa är INTE egna arbetsköer.

**Nya statusdefinitioner:** APPROVED_SCOPE betyder att användaren har beställt funktionen som mål; NOT_STARTED att kod ej finns; LIMITED_NATIVE att verifierbar men avgränsad implementation finns; VERIFIED_NATIVE först när standardspecifikation, egen kod, oberoende referensvektor och Required CI stöder ett exakt definierat beteende; PT_DOK = Ciscos dokumentation, INTE jämförd konkurrentkörning; PT_VERIFIED_COMPARISON kräver samma verkliga labb körda på exakta båda versioner. Ändra aldrig stödstatus via enbart Markdown.

**Beroendelås enligt ADR-0001:** S0 docs först; **S1-POC0/POC1 tillåts efter S0 + A1 + riktade orakel**, utan att ändra produktionsmotorn. **Produktionscutover kräver PASS vid go/no-go och berörda A3/A4/A5/A7-kontrakt**; A3/A4:s hela UI-/importrefaktorering är inte automatiskt scheduler-blockerare. A6/A10 fortsätter enligt egna kriterier. S1 blockerar övrig native protokollutbyggnad; varje S-kort efter S1 kan delas i mindre PR, ett åt gången. A8 mänsklig forskning kräver fortfarande separat uttryckligt beslut. A9:s produktutbyggnad är nu uttryckligen godkänd i detta S-omfång, inte en licens för godtycklig teknikstack.

### 10.1 Prioriterad produktväg och blockerande beroenden

| Kort | Status | Leverans | Blockerande föregångare |
|---|---|---|---|
| S0 | IN_PROGRESS – masterdesign / docs | Fullständig PT 9.0.1-inventering: PT-F01–PT-F29, alla enheter, protokoll, kommandon, medier, appar, IoT/OT, multiuser, script, format, källor och testfall | A1 och användarbeslut |
| S1 | NOT_STARTED | Helt NY fristående DES-motor: POC0→POC1→ny Ethernet/ARP/IPv4/ICMP/DHCP-stack→EN testad cutover→retire legacy | POC0: ADR-0002/guard Required PASS; POC1: POC0 PASS; cutover: oberoende orakel+API/Save/Open+CI |
| S2 | NOT_STARTED | Full L2/VLAN, FDB aging, STP/RSTP, LACP/EtherChannel, kontrollerade loopar | S1 |
| S3 | NOT_STARTED | IPv4/v6, ICMPv6, ND/SLAAC/DAD, MTU/fragment, RIB/FIB/SVI | S1/S2 |
| S4 | NOT_STARTED | UDP, TCP FSM, DHCPv4/v6 relay/multiserver, DNS och appprotokoll | S1/S2/S3 |
| S5 | NOT_STARTED | RIP, OSPFv2/v3, EIGRP, BGP-4, redistribution och konvergens | S1–S4, TCP före BGP |
| S6 | NOT_STARTED | ACL, NAT/PAT, stateful firewall, GRE/IPsec, AAA/802.1X | S1–S5 relevanta paketvägar |
| S7 | NOT_STARTED | Bandbredd, fördröjning, jitter, köer/QoS, WAN/fiber/wireless | S1–S4 |
| S8 | NOT_STARTED | HSRP/VRRP, LLDP/CDP, SPAN/RSPAN/NetFlow, REP/PRP/PTP | S1–S5/S7 |
| S9 | NOT_STARTED | Industriellt nätverk: Modbus TCP, PROFINET, CIP, OPC UA, IEC 61850, PLC/HMI | S4/S7/S8 |
| S10 | NOT_STARTED | ALL produktparitet: logical/physical, device/moduler, power, GUI/CLI, OSI/PDU/scenarios, Activity Wizard/scoring/scripts, IoT-programmering, multiuser, extensions/API, PKT/PKZ/PKA och fulla användarflöden | S1, S2–S9, PT-F01–PT-F29 |
| S11 | NOT_STARTED | FULLT PT-F01–PT-F29-provregister med varje underfall, oberoende RFC-/IEEE-/IEC-orakel och verklig versionerad PT-labbjämförelse, inklusive filer/CLI/UI/OT/IoT/multiuser | S2–S10; PT-FULL-001 G0–G3 |
| S12 | NOT_STARTED | NOLL öppna Cisco PT-protokoll-/funktionsluckor, verifierad full paritet och därutöver verifierad överlägsenhet, ingen kompromiss-etikett COMPLETE | S0–S11; PT-FULL-001 G0–G5 |

### S0. Källbaserad design och sanningsmatris

Håll [Packet Tracer 9.0-katalogen](research/PACKET_TRACER_GAP_ANALYSIS_2026-11-26.md) versionslåst; äldre 8.2-FAQ kan vara historiskt komplement men inte automatiskt intyg för 9.0-stöd. Inventera **varje** protokollvariant i [täckningsmatrisen](PROTOCOL_COVERAGE_MATRIX.md). Dokumentera dagens kod, gaps, mål, standardversioner, licensfrågor och framtida jämförelseorakel. Acceptans: en canonical masterplan, ömsesidiga länkar, ingen unsupported som felaktigt kallas native, Required governance/architecture PASS. Denna PR ändrar ingen runtime.

### S1. Den gemensamma in-process simuleringskärnan

**Vägval enligt [ADR-0002](architecture/ADR_0002_FRESH_ENGINE_2026-11-26.md): BYGG HELT NY nätverksexekvering utan gamla motorimports.** Gammal EthernetFabric/ArpSession/IPv4Trace/DhcpSession blir endast tillfällig legacy-referens och pensioneras efter EN verifierad produktionscutover. Kompatibilitet med korrekta externa observationer krävs, inte kodåteranvändning. S1-POC0/POC1 i isolerade testfixture får föregå fullständig A3/A4; full cutover kräver endast en aktiv auktoritativ motor och Required CI.

Bygg **en** prioriterad händelsekö ordnad på (integer virtual_time_ns, monotont event_id), per-scenario seedad PRNG, avbrytbara timers, resurs-/eventbudget, fail-closed zero-time loop- och overflowguard, och oföränderliga packet-/eventrecords med parent_event_id och packet_id. Simulerad tid är skild från väggklocka och GUI-animation. Varje riktig packet TX → link serialization → propagation → RX → parser → protocol state transition → route/FDB/ACL/queue decision → nästa hop/drop. Gemensam sessionstate äger FDB, ARP/ND, RIB/FIB, TCP, DHCP, OSPF/BGP och NAT enligt capability.

**Acceptans:** två oberoende processstarter + samma konfiguration/seed ger identisk eventhash; samtidiga events har stabil tie-break; cancelled events kan inte utföras, ogiltig tid/zero-time-loop ger kontrollerat fel, gamla sessioner kan inte uppdatera ny workspace, och befintlig IPv4/ARP/ICMP/DHCP-beteendeparitet kvarstår. Inga två parallella motorer. [Detaljerat kontrakt](architecture/DETERMINISTIC_ENGINE_CONTRACT.md).

### S2. Ethernet, VLAN, switchloopar och L2-konvergens

Utöka befintlig EthernetFabric, MAC aging/flush och explicit portstate; 802.1Q native/allowed VLAN; STP/RSTP med BPDU root election, portroller, timers/topology change, LACP/EtherChannel med förhandling och linkfailover. Senare separata profiler för VTP/DTP/PAgP och andra proprietära tekniker. Positiva/negativa tester: fysiska loopar utan tyst falsk leverans, två potentiella roots, VLAN isolation, portdown, broadcast-storm-budget, STP-rekonvergens, LACP mismatch.

### S3. IPv4/v6 dataplan och riktig routning

Bakåtkompatibel, explicit projektmigration; RFC-stödd IPv4-fragmentering/DF/PMTUD där relevant; IPv6 headers och multicast/link-local scope; ND/RA/SLAAC/DAD, ICMPv6, ARP/ND aging, routing/RIB/FIB, inter-VLAN/SVI/router-on-a-stick. Negativa fall: nät-/broadcastadresser, no route, ND duplicate, wrong hop limit, TTL expiry, MTU, error suppression. Ingen IPv6-adress gissas från importerade dokument.

### S4. TCP/UDP, DHCP och verklig applikationstrafik

Generell UDP checksum/portdelivery; TCP enligt [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293) med SYN/ACK, seq/window, retransmission, FIN/RST och simulerade timers; DHCPv4 relay/multiserver/renew/expiry, DHCPv6 RFC 8415, DNS query/cache/TTL. Därefter HTTP, TFTP/FTP, SMTP/POP3, SSH/Telnet, SNMP/Syslog/NTP/MQTT och RTP/VoIP i små dokumenterade kort. Varje tjänst måste kräva verkligt simulerad L2–L4-framväg och retur, aldrig statisk "request success". TLS/SSH/IPsec får aldrig hävda kryptografisk säkerhet som inte implementerats.

### S5. Dynamiska routingprotokoll

RIP v1/v2/ng, OSPFv2/v3 Hello/neighbor FSM/LSDB/SPF/areas, EIGRP DUAL med licens-/rättighetsbedömning, BGP4 över simulatorns riktiga TCP med OPEN/KEEPALIVE/UPDATE/withdrawal, AS_PATH, eBGP/iBGP/policy. Gemensam RIB/FIB install/uninstall, route preferences, redistribution och loopskydd. Negativa standardfall: ensidig Hello blir inte Full, flappande adjacency, withdrawn route, AS loop, BGP TCP fail, saknad retur, ECMP och policyfel.

### S6. Säkerhet och tunnelsanning

ACL ordning/direction/implicit deny, NAT/PAT och conntrack, stateful firewall/ZBF/CBAC, GRE/IPsec/IKE, AAA/RADIUS/TACACS/802.1X och IDS/IPS med tydlig begränsning. Korrekt filter/translation på simulerade packets, ingen "show access-list" utan motsvarande tillstånd. Falska security guarantees förbjudna.

### S7. Tid, köer, WAN och radio

Portbitrates, serialization/propagation, bandwidth, queue limit, delay/jitter/loss, DSCP/QoS, link types och fiber-/duplexfel; PPP/PPPoE/HDLC/Frame Relay/DSL, 802.11 association/roaming och uttryckligen avgränsade 3G/4G/5G-profiler. RTT och throughput ska beräknas ur verklig simulerad händelsekedja, aldrig ospecifik fast gissning. Fysiska lägen kräver uttrycklig linkprofil, inte avstånd på SVG.

### S8. Hög tillgänglighet, management, avancerat L2

VRRP/HSRP med unik aktiv gateway, LLDP/CDP, SPAN/RSPAN, NetFlow, NTP/PTP och REP/PRP/L2NAT; varje implementation med explicit standard och state. Negativt test: inga dubbla masters utan definierad split-brainmodell, korrekta timers vid failover, speglade packets och flow counters härledda från faktisk trafik.

### S9. OT/IoT och isolerad industriell simulering

Packet Tracer 9.0 stöder förenklade [Modbus TCP, PROFINET, CIP, IEC 61850, OPC-UA, PTP/PRP och PLC/HMI](https://tutorials.ptnetacad.net/help/default/industrial_otFeatures.htm). YadiLab ska erbjuda egna standardspecifika, versionsmärkta in-process delmodeller, korrekta exception-/register-/sequence-/timerfall och pedagogiska cyberobservatörer. Ingen kontakt med verklig PLC, inga host scripts, inga falska realtidsgarantier. IEC/ODVA/licenser granskas innan ny implementation.

### S10. ALL Packet Tracer-produktfunktionalitet: UI, enheter, format, scripting, multiuser och undervisning

Logisk och fysisk workspace, enhetspalett/profil och explicit kablage, riktig konfigurations-CLI som anropar samma backendmotor, device tables, OSI/PDU/header/timeline med exakta orsaksförklaringar, filter/step/pause/replay, importproveniens, labb-/övningsförfattande, automatisk bedömning, konkurrerande hypoteser, fördröjt facit och stöd för samma elevresa som konkurrenten. CLI-kommandon utan native semantik ska ge synligt UNSUPPORTED, aldrig tyst godkännande. Inga animerade eller fejkade leveransbevis.

### S11. Standardefterlevnad, differential och benchmarks

Fristående RFC/IEEE/IEC-orakel med råbytesfacit, state-/timergränser, positiva/negativa/motsägande fall, property/fuzz/metamorphic tests och reproducerade multi-hop, failover, race, loop och stora topologier. Referensimplementationer och isolerade jämförbara Packet Tracer-labb får användas **test-only**, aldrig runtime. Spåra SHA, seed, versionsnummer, maskin, PASS/FAIL/NOT_RUN och orakelproveniens. Föreslagna RELEASEMÅL (ej uppmätta): noll kända falskt positiva packet deliveries i låst negativ corpus, samtliga deklarerat stödda referensfall PASS, inga öppna P0/P1, deterministisk reproducerbarhet och minst ett end-to-end-scenario för varje deklarerad PT-paritetsfunktion. Skalmål beslutas först efter mätning, inte efter gissning.

### S12. Absolut slutgrind: alla PT-funktioner och protokoll samt verifierad överlägsenhet

Kräv helt ny oberoende code/architecture/security/protocol review; jämför samma versionslåsta labb i Packet Tracer och YadiLab där laglig körning finns; redovisa korrekta/inkorrekta/unsupported scenarier, faktisk teknisk precision, pedagogisk mätning och resurskostnad. En mänsklig lärstudie ingår bara om separat A8-godkännande. **Ingen "bättre än Cisco", 10/10, 100 % RFC-kompatibel eller COMPLETE** förrän relevant evidens är både mätt och publicerad. Brister klassas BUG/MODEL_LIMITATION/NOT_VERIFIED/UNSUPPORTED.

## 11. Operativ MASTERPROMPT för alla framtida agentkörningar

1. Läs senaste GitHub main/PR/CI, AGENTS.md, denna ENDA plan, [MASTERPROMPT](MASTERPROMPT.md) och relevant matris-/motorkontrakt. S0 är det aktiva designkortet fram till dokument-PR:s Required+merge. **Efter S0: starta S1-POC0 och POC1 i små separata PR enligt [ADR-0001](architecture/ADR_0001_CORE_REPLACEMENT_2026-11-26.md), därefter go/no-go.** A3/A4/A5/A7 skyddar de faktiska produktionsintegrationerna. A6/A10 enligt egna acceptanskriterier.
2. Leverera minsta meningsfulla positiva nätverksbeteende med tillhörande **negativt och motsägande oberoende orakel**, explicit standardversion, state ownership, virtual clock, resource budget, fullfidelity packet/drop trace, migrations- och rollbacktest där relevant. Separera underliggande dokumenterade konfigfakta från simulerade resultat.
3. En enda motor och en final validator. Ingen VM/emulering/extern runtime, ingen falsk route/CLI/packet och ingen tyst import-/Save-förändring. Bevara Linux-only, exact source provenance, SHA-256, sessionsgenerationsstopp, A1-arkitekturspärr och anti-monolitkontrakt.
4. Använd riktad snabb testtrappa, därefter full Required functional + architecture CI vid kodändring. Vid passiv CI-väntan, arbeta bara inom samma PR eller avsluta med exakta SHA/status; inga pollingsloopar/Codex-slöseri. Max en PR. Squash-merge enbart på exakt senaste grön HEAD utan blockerande reviews.
5. Uppdatera **denna** A-/S-status och [protokollmatrisen](PROTOCOL_COVERAGE_MATRIX.md) utifrån faktiskt utförd evidens, inte vad en plan lovar. Läs inte gamla A9-förbud som veto mot användarens nya, uttryckliga S-godkännande. Markera okänt NOT_VERIFIED.

**Tolkningsföreträde:** De äldre A0–A10-avsnitten beskriver den ursprungliga reparationsplanens begränsade omfång och bevaras för revisionsspår. För nya protokoll och ny produktvision gäller användarens uttryckliga beslut och avsnitt 10–11. A8 separat godkännande, A9 beslutad utbyggnad; inga redan godkända Required-kontroller får försvagas.

## 13. Nytt entydigt slutkriterium – NO FEATURE LEFT BEHIND

**S12 får endast stängas när [PT-FULL-001](FULL_PACKET_TRACER_PARITY_CONTRACT.md) G0–G5 är verifierade och alla PT-F01–PT-F29-underfall är PASS.** Inte enbart nätverksprotokoll: protokollvarianter, enhetsprofiler, anslutningar, CLI/GUI, fysisk/logisk arbetsyta, power, realtime/simulation, PDU, IoT, OT, Multiuser, scripting, Activity Wizard, scoring, extensions och PT-filformat är obligatoriska. Enstaka exempel räcker inte. En legal/specifika blockerare förblir blockerad slutgrind, inte accepterat undantag. Linux-only och ingen särskild keyboard/accessibility-nyutveckling är de enda uttryckliga undantagen; befintliga fungerande beteenden får inte slås sönder. Att S1–S11 kan ha delvis stöd är endast tillfälligt och ingen rätt att leverera mindre än Packet Tracer.

**Fortsatt teknisk väg:** bevara YadiLab som produkt, nybygg DES-exekveringen selektivt enligt [ADR-0001](architecture/ADR_0001_CORE_REPLACEMENT_2026-11-26.md), börja med isolerad S1-POC0/POC1 efter S0 och bygg varje vidare lager utan parallella motorer. Ingen total omskrivning av UI/lagring som rutin. S0 måste utöka sin funktionsinventering tills varje faktiskt PT-underfall och lagligt verifierbar firmware-/filformatkompatibilitet har individuellt spårbart bevis. 
