# YadiLab – åtgärdsplan för granskningsbrister och hållbar modularisering

**Datum:** 2026-11-26  
**Status:** GODKÄND / AKTIV PLAN – **A0 levererad i PR #169, formellt DONE först när PR #169 är squash-mergad med required CI SUCCESS**; nästa godkända arbetskort är A1  
**Utgångspunkt:** Granskningsrapporten *Teknisk granskning av YadiLab – 2026-11-26* (hela avsnitt 1–6), användarens observation om försvunnen modularisering samt en separat kodinventering på `main@82fca139cc43e12ff8c21bbb3427ab4f87588fd5`.  
**Syfte:** Åtgärda påvisade fel och underhållsbrister; verifiera kvarstående osäkerheter; ge dokumenterade simulatorbegränsningar ett explicit beslut; återvinna och skydda modulariseringen.  
**Styrning:** P0–P7 är formellt avslutat. **Den här A0–A10-planen är nu ensam aktiv utvecklingsplan** genom uttryckligt användarbeslut 2026-11-26, inte en återaktivering av P7. A0–A7 och A10 omfattas av beslutet enligt beroenden och acceptanskrav. **A8 och A9 är villkorade och kräver separata uttryckliga godkännanden**; ingen ny native-protokollmotor, empirisk studie eller annan utökning är automatiskt beställd.


## 0. Operativ startpunkt för kommande konversationer (beslutad 2026-11-26)

**LÄS FÖRST:** `AGENTS.md` → **den här enda aktiva planen** → `docs/MASTERPROMPT.md` → `docs/IMPORT_SOURCE_CONTRACT.md` → historisk `docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md` endast för fortsatt pedagogiskt kvalitetskontrakt. Primärgranskning ordagrant: [Teknisk granskning 2026-11-26](reviews/TECHNICAL_REVIEW_2026-11-26.md). Välj aldrig uppgift ur den avslutade P0–P7-planen eller andra äldre roadmaps.

**A0 – Rebaslinje & forensisk modulgranskning:** [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169) levererar [forensisk rapport](architecture/A0_FORENSIC_BASELINE_2026-11-26.md), [exakt fil-/testmanifest](../architecture/a0_baseline.json), [ES-importgraf](../architecture/a0_frontend_imports.json) och positiva/negativa manifesttester. Kontrollera att #169 är **MERGED och att dess slutliga HEAD hade required SUCCESS** innan A0 räknas som DONE. **Nästa konkreta uppgift efter verifierad A0-merge: A1 – Arkitekturspärrar G1–G7 (NEXT / NOT_STARTED).** A1 måste installera, negativt testa och göra `architecture-guard` required i GitHub branchskyddet **innan** A3/A4-modularisering. A0-dokumentation är inte en installerad architecture-guard.

**Fortsättningsregel:** När användaren säger `fortsätt` om YadiLab ska nästa **ej slutförda, godkända A-kort** väljas utifrån beroenden och verifierad GitHub-status; inte gamla P7-steg, inte en ny påhittad fas och inte ett valfritt nytt protokoll. Max en aktiv ändrings-PR. Utlovad automatisk bakgrundskörning förekommer inte. Bekräfta exakt PR-HEAD, alla required checks `SUCCESS`, oskadad main och squash före merge. Dokumentera varje färdigt A-kort och påverkat C01–C18-ID i planen eller en evidenslänk som planen refererar till.

**Statusregel:** `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `ACCEPTED_LIMITATION`, `DECISION_REQUIRED` och `NOT_VERIFIED` betyder olika saker. Ändra aldrig till `DONE` från enbart dokumentation eller CI-symbol. Länkad PR + resultat/negativt test + arkitekturdelta + återstående risk krävs. När en uppgift slutförts uppdateras tabellen **i samma PR** så att nästa konversation inte behöver gissa.

| Arbetskort | Utgångsstatus vid aktivering | Kommentar |
|---|---|---|
| **A0** | **DONE efter verifierad merge av PR #169** | C02–C05: arkitekturhistorik, ägarskap, data- och regressionsmanifest; ingen produktkod ändrad |
| **A1** | **NEXT / NOT_STARTED (efter A0-merge)** | G1–G7 och `architecture-guard` Required före A3/A4 |
| A2 | NOT_STARTED | HTTP-disconnect och sekundär felhantering |
| A3 | NOT_STARTED | Frontend-modularisering skyddad av A1 |
| A4 | NOT_STARTED | Backend-import/ICMP-modularisering skyddad av A1 |
| A5 | NOT_STARTED | Oberoende referenser och komplexa topologier |
| A6 | NOT_STARTED | Pedagogisk funktion och testad elevresa |
| A7 | NOT_STARTED | Tydlig support-/begränsningsmatris |
| A8 | DECISION_REQUIRED / OPTIONAL | Empirisk mänsklig studie kräver separat godkännande |
| A9 | DECISION_REQUIRED / OPTIONAL | Nya protokoll eller fysikmodell kräver separat godkännande |
| A10 | NOT_STARTED | Slutrevision och stängningsbeslut när föregående grindar klarats |

**Avslutsregel:** Planen får först markeras `CLOSED` efter A10:s verifierade slutrapport och full spårning av C01–C18. Valfria A8/A9 kan redovisas som `DECISION_REQUIRED` eller `NOT_VERIFIED` utan att någon obeställd implementation krävs. Ingen oberoende mänsklig pedagogisk effekt eller fullständig RFC-certifiering får då påstås utan faktisk evidens.

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
| A9 | Eventuell protokollbredd (separata kodkort) | P3 / spärrad | A7 + separat uttryckligt beslut | En avgränsad motor i taget, oberoende facit, ingen dold emulering |
| A10 | Slutrevision, rollback och beslut om avslut | P0 som slutgrind | Relevanta A-kort | Slutrapport C01–C18, oförändrade invariants, grön CI |

**Tidsplanering:** Ordningen ovan är beroendestyrd; ingen kalenderdeadline eller ”alla protokoll färdiga” utlovas utan kapacitetsunderlag och uttryckliga omfångsbeslut. A0–A2 är första leveransgruppen. A3 delas i små, funktionellt begränsade PR:er. Backenddelning och nya referensfall bör inte kombineras i samma PR. A9 är en reserverad beslutsgrind, inte en automatisk beställning.

## 5. Detaljerade arbetskort

### A0. Forensik och bevisad nollpunkt

**Leveransevidens:** [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169), [A0-rapport](architecture/A0_FORENSIC_BASELINE_2026-11-26.md), [Git-manifest](../architecture/a0_baseline.json) och [exakt ES-importgraf](../architecture/a0_frontend_imports.json). Test: `tests/test_a0_forensic_manifest.py` med negativt ändrad modul, orphan/cykel, missad import och falskt Git-blobbevis. Räckvidd: statisk inventering, ingen runtimeändring och ingen installerad A1-spärr. **Status: PR #169 levererad; merge/CI-beroende.**

**Utför:** Läs exakt aktuell `main`, samtliga aktiva PR:er och senaste CI. Dokumentera commit där varje modul extraherades, vilka moduler som fortfarande finns och vilka ansvar som åter dykt upp i `app.js`. Ta fram callgraph/importgraf, state- och eventkarta, antalet direkta DOM-beröringar, funktioner med hög komplexitet samt sessionernas generations-/stale-guards. Lägg samtliga regressionsfall och filbytes i ett versionsbundet manifest.

**Acceptans:** skillnaden mellan 3E (`app.js` 2 237) och nuvarande 2 978 har förklarats i termer av funktion/ansvar, inte endast antal rader; modulnivåer finns dokumenterade; ingen kod har ändrats före arkitekturbaslinjen.

### A1. Arkitekturspärrar före ny extraktion

**Utför:** Implementera G1–G7. Lägg till automatiserat test för `architecture/baseline.json`, förbjudna beroenden, svällande entrypoint, modulförsvinnande och kopierad sessionsstate. Skapa kompatibel uppdateringsprocess: budget får sänkas automatiskt men höjning kräver separat, granskad ändring. Gör den obligatoriska checken *required* i GitHub branch rules innan A3.

**Negativ provning:** simulerat borttagen `features/sessions/icmp-investigation.js`, cirkelimport, flyttad ping-presentation till `app.js`, förbjuden import från presentation till storage, falskt höjd radbudget och borttagen testfil ska alla ge röd kontroll. Ett rent refaktoreringsexempel ska passera.

**Acceptans:** faktisk branchregel blockerar merge på `architecture-guard=FAIL`, även om vanliga enhetstester passerar. Bevara nuvarande `test_web_import_graph.py` och utöka, ersätt inte med svagare test.

### A2. HTTP-resiliens vid klientavbrott

**Utför:** Reproducera serverns `ConnectionResetError`/`BrokenPipeError` i en isolerad HTTP-integration med klient som stänger socket före/under svar. Hantera fel vid både `end_headers`, `wfile.write` och relevanta statiska svarsvägar; avbryt fortsatt skrivning på samma stängda socket. Undvik att en exceptionshanterare försöker skriva JSON-fel på en redan bruten anslutning. Klassificera förväntad frånkoppling utan att dölja verkliga serverfel.

**Negativa fall:** icke-bruten klient får fortsatt exakt samma HTTP-status/body; felaktig JSON får korrekt 4xx; oväntad serverexception syns som avvikelse; avbruten klient orsakar inte retried Save eller dubbla mutationer. Jämför sparade SHA före/efter.

**Acceptans:** reproducerbart disconnect-test PASS utan oönskad traceback; befintliga behörighets-, lagrings- och HTTP-tester förblir gröna. Dokumentera om eventuellt kvarvarande enskilda `BrokenPipeError` i extern miljö endast är loggstörning eller verkligt fel.

### A3. Frontendmodularisering som faktiskt håller

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

### A9. Valbara nya protokoll eller fysikmodeller – endast särskilt beslut

**Separata förslag:** (a) STP-förklarande/liten deterministisk loopmodell; (b) IPv4-fragmentering; (c) DHCP relay och serverkonkurrens; (d) avgränsad TCP/UDP; (e) kö/bandbredd/fördröjning; (f) IPv6; (g) ACL/NAT; (h) OSPF/BGP. Var och en kräver explicit produktkontrakt, definierade stödda/avvisade fall, verifierad referens, resursbudget, säkerhetsgenomgång och separat användargodkännande. **Att lista ett protokoll här ger inte mandat att implementera det.** En heltäckande emulator likställd med GNS3/EVE-NG är inte realistisk acceptans för denna reparationsplan.

### A10. Slutrevision och stängning

**Utför:** kör alla obligatoriska testgrindar på sista PR-HEAD, verifiera ren squashhistorik och jämför `main` efter merge. Kontrollera arkitekturrapporten och prov att framtida återmonolitisering blockeras. Sammanställ C01–C18: status, bevis, risk, explicit omfångsbeslut och eventuell restpunkt. Genomför separat riskbaserad kodgranskning och relevant långkörning; beskriv klart det som inte testats.

**Acceptans:** inga P0/P1-fel öppna, alla aktiverade A-kort har reproducerbart resultat, inget skydd är avaktiverat, både funktionell CI och `architecture-guard` är `SUCCESS`, sparad data oförändrad när ingen Save gjorts, dokumentationen beskriver faktiska gränser, och ny modularisering överlever minst en efterföljande funktions-PR med skydden aktiva.

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
- [ ] `architecture-guard` är obligatoriskt i branchskyddet, negativt testat och går inte att kringgå via ändrad PR-scope.
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

**Statusnot (2026-11-26):** Planen är godkänd och aktiv. **A0:s rena revisionsleverans finns i PR #169**, med versionsbunden käll-/testmanifestering och negativa manifesttester. A0 blir formellt DONE först efter kontrollerad squash-merge på grön slutlig PR-HEAD. **A1 är nästa utvecklingskort; G1–G7 och `architecture-guard` är ännu INTE installerade.** All senare `DONE`-status kräver kod-/test-/CI-evidens.