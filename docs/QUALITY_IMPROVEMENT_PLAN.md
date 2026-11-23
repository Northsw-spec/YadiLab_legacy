# Masterplan för källkodskvalitet 10/10

**Dokumentversion:** 1.1 – förstärkta skydds- och etappgrindar  
**Datum:** 2026-11-21 (ISO)  
**Repository:** [Repositoryts rot](../)  
**Historisk, ursprungligen verifierad bascommit (inte aktuell HEAD):** `32bcefdf3eff25bc6a4f7986a7d88c05f704214c`  
**Mål:** Högsta möjliga verifierbara källkodskvalitet inom appens uttryckligen stödda omfattning.  
**Status:** QUALITY-001 ACCEPTED; QUALITY-002 CONFIGURED / ENFORCEMENT NOT_VERIFIED (röd PR #99 stängd utan merge); QUALITY-003 **ACCEPTED (VERIFIED SUPPORTED SUBSET)** på `main@ba674047e779750f5c8efa7739cf0f80a26fd5d6` med main-CI SUCCESS; QUALITY-004–011 inte accepterade.

> **Gällande styrning:** `AGENTS.md` och `docs/MASTERPROMPT.md` gäller övergripande. För import gäller dessutom `docs/IMPORT_SOURCE_CONTRACT.md` och tillhörande tekniska kontrakt. Denna fil är den **enda aktuella samlade kvalitetsfärdplanen**, inte en ersättning för dessa kontrakt. Faktisk kod, CI och den senaste uttryckliga användarinstruktionen avgör aktuell implementationsstatus. Äldre etappanteckningar har bevarats oförändrade i [QUALITY_IMPROVEMENT_HISTORY.md](QUALITY_IMPROVEMENT_HISTORY.md); deras historiska framtidsuttalanden är **inte** aktuella order eller verifierade nulägesuppgifter.

## 1. Syfte och kvalitetsprinciper

Applikationen ska gå från en användbar simulator till en kodbas vars korrekthet, underhållbarhet och tillförlitlighet kan bedömas oberoende. 10/10 är ett **krävande revisionsmål**, aldrig något som deklareras därför att CI är grön eller en viss mängd kod levererats. Det kräver inte stöd för alla nätverksprotokoll eller operativsystem. En smal, korrekt modell är bättre än ett brett system med falska resultat.

Bindande invariants:

1. **En auktoritativ kanonisk nätverksmodell** för deklarerade noder, portar, länkar och zoner.
2. **Inga implicit skapade kablar, gateways, routes, enheter eller MAC-adresser** utifrån namn, placering eller antaganden.
3. **Ingen falsk simulatorframgång:** grafväg, route lookup och ARP är inte automatiskt IP-reachability eller ICMP Reply.
4. **Förlustfri eller avvisad import:** källfakta, cellidentiteter och proveniens får inte tyst tappas.
5. **Beständighet först efter uttrycklig Save:** exakta objekt-ID, bytes, SHA-256, konfliktskydd och omstart måste fungera.
6. **Protokollbeteende testas mot oberoende referenser**, inte enbart mot utfall beräknade av samma produktionskod.
7. **Minsta sammanhängande ändring** per PR. Ingen parallell motor, datamodell eller omotiverad abstraktion.
8. **Tester ska kunna misslyckas av verkliga fel**; positiva och negativa regressioner är obligatoriska.
9. **CI och branchregler måste blockera felaktig merge**, inte enbart observeras frivilligt.
10. **Ärlig status:** VERIFIED, NOT_VERIFIED, UNSUPPORTED eller CONFIRMED_DEFECT. Ingen oprecis PASS.
11. **Begränsningar dokumenteras**, inte döljs bakom allmänna produktpåståenden.
12. **Inga nya funktioner utan motiverad nytta** och en separat verifierbar funktionsdefinition.

### 1A. Gemensamt skyddskontrakt – vad Codex får och inte får göra

Detta skyddskontrakt gäller **QUALITY-000–011, alla del-PR:er, diagnostiska experiment, ändringar i tester/CI och eventuella byggartefakter**. Det ger inga nya utvecklingsuppdrag. Den senast uttryckliga användarinstruktionen och de bindande funktions-/importkontrakten gäller fortfarande; oklara eller motstridiga instruktioner får **inte** lösas genom att anta bredare ändringstillstånd. Fortsätt i stället med skrivskyddad analys, dokumentera konflikten och avstå från den riskabla ändringen.

**Ändringstillstånd är en trappa, inte en följd av att en etapp nämns:**

| Nivå | Tillåtet | Inte tillåtet |
|---|---|---|
| AUDIT / READ_ONLY | Läsa, analysera, jämföra referenser, inventera och rapportera; versionshantera avgränsad revisionsdokumentation | Ändra produktionskod eller tolka misstanke som verifierad defekt |
| TEST / EVIDENCE | Lägga till isolerade positiva/negativa tester och fixturer, med verifierad förväntan och säker testdata | Ändra produktionskoden för att göra ett svagt test grönt; avaktivera befintliga kontroller |
| NARROW_FIX | En liten ändring med konkret reproducerad defekt/kontraktsavvikelse, före-/efterbevis och relevanta regressioner, inom aktuell etapps uttryckliga tillstånd | Allmän cleanup, ombyggnad av närliggande kod, byte av arkitektur, implicit feature-utveckling |
| CONTRACT / BREAKING_CHANGE | **Endast ett separat, uttryckligen godkänt uppdrag** med migrations-, kompatibilitets- och rollbackplan | Ändrad kanonisk schema-/filsemantik, API-brott, importregler, borttagen funktion, nytt protokoll, ändrad platform-support eller CI-/rulesetförsvagning under förevändning att kvaliteten förbättras |

**Innan någon kod skrivs måste Codex kunna redovisa:** (1) exakt observerad avvikelse och riskklass eller specificerat accepterat förbättringsmål; (2) stödd förväntad semantik från kontrakt/oberoende facit; (3) minsta relevanta filer/funktioner och icke-mål; (4) en regressionskontroll som kan fallera av den aktuella avvikelsen; (5) skydd för identiteter, befintliga användarflöden och asynkrona/atomära garantier; (6) verifierings- och återställningsplan. Saknas något: **AUDIT / NOT_VERIFIED**, ingen improviserad implementation.

**Absoluta spärrar utan särskilt uttryckligt mandat:**

- Ingen massrefaktor, automatisk uppdelning efter radantal, allmän formatering av orörda filer, namnbyte, omskrivning från grunden, ”modernisering” av alla moduler eller borttagning av så kallad AI-/legacy-kod utifrån misstanke.
- Ingen ny parallell kanonisk modell, importmotor, protokollmotor, sessionslagring, eventbus, generell HTTP-router eller state manager. Inga gissade enheter/länkar/rutter och inget påstått protokoll-PASS byggt på enbart grafväg.
- Ingen oombedd installation eller uppgradering av runtimebibliotek, JavaScript-ramverk, Python-/Node-versioner, schema-/projektformat eller annan plattformspolicy. Reproducerbar testmiljö får beskrivas och byggas isolerat inom avtalat scope.
- Ingen tyst ändring av GitHub rulesets, branchskydd, nödvändiga CI-checks, workflow-triggers, GitHub Actions-permissions, testtäckning eller testtimeouts för att kringgå ett FAIL. Förslag ska redovisas separat; en försvagning kräver nytt uttryckligt uppdrag.
- Ingen force-push, direktpush till skyddad main, merge av avsiktligt röd test-PR, historikomskrivning eller destruktiva kommandon mot användarens riktiga filer/arbetskatalog. För experiment: separata temporära kataloger och fiktiva testprojekt; bevara originalbytes och kontrollsummor.
- Ingen falsk verifiering: ”CI grön”, headless Chromium, isolerad stub, syntetisk fixtur, lyckad kompilering eller en äldre körnings artefakt får **inte** ersätta aktuell, relevant, verklig end-to-end-verifiering. Tester får aldrig raderas, markeras skip/xfail, göras tautologiska eller få lösare assertions bara för att slippa regressionsfel.
- Ingen obehörig publicering av riktiga kund-/företagsdokument, identifierande infrastrukturnamn, IP-planer, personuppgifter, inloggningar eller hemligheter. Använd uttryckligt tillåtna och avidentifierade, artificiella eller lokalt skyddade underlag; notera när anonymisering kan ändra det som testas.
- Ingen tyst ”scope creep”: om nya behov, okända fakta eller problem upptäcks, skriv ett separat ISSUE/FINDING-förslag med evidens och lämplig QUALITY-etapp. P0/P1 får prioriteras före ordningen, men **endast som egen minimal korrigerings-PR**, inte som tillstånd att renovera hela delsystemet.

**Obligatorisk ändringsgranskning före PR:** redovisa tillåtna filer, alla faktiskt ändrade filer, diffstatistik och varför varje ändring behövs; följ beroendegrafen; kontrollera att ingen oavsiktlig fil, låsfil, testdefinition, dokumenterad garanti eller byggskript ändrats. En större diff än vad det enda problemet kräver ska avbrytas eller delas i mindre självständigt verifierbara PR:er. **Lägg inte ett fungerande systems tidigare regressioner som pant för renare kodstil.**

**Acceptans och självkontroll:** en etapp kan slutföras som endast en revisionsrapport, med alla kodområden **KEEP**, eller stanna som NOT_VERIFIED med tydlig blockerare. Status på kod, tester, CI, ruleset och release redovisas separat på exakt SHA; en av dem får aldrig antas från en annan. Det finns inget krav på ett visst antal kodrader, commits, refaktoreringar, nya funktioner, testfall eller höjt självvalt betyg.

## 2. Verifierad utgångspunkt per 2026-11-21

**Historisk ögonblicksbild från planens tillkomst, inte en aktuell CI-/PR-status.** Codex ska inför varje steg kontrollera ny exakt main-SHA, aktiva PR:er, utfall på just den SHA:n, workflow- och rulesetstatus. Ändra aldrig ett statusfält utifrån förmodad eller äldre PASS. Vid senare verifierad merge kompletteras historiken spårbart i QUALITY-000, inte genom att det ursprungliga facit suddas ut.

| Kontroll | Verifierat läge |
|---|---|
| `main` | `32bcefdf3eff25bc6a4f7986a7d88c05f704214c` |
| Senaste main-CI | [#44904476735](../actions/runs/44904476735): SUCCESS på exakt commit |
| Öppna PR:er | 0 vid planens verifiering |
| Python | 636 tester PASS i verifierad CI |
| JavaScript | 10 Node-tester PASS, `npm run check` ingår i CI |
| Chromium | PASS i DIRECT_HTTP, med riktig Save/Open |
| Aktivt main-ruleset | ID 27419615; required status check `unit-tests` **CONFIGURED** |
| Rulesetets blockerande effekt | **NOT_VERIFIED** genom negativ test-PR |
| Strict up-to-date-krav | `strict_required_status_checks_policy=false`; ska riskbedömas |

Redan korrigerade fel: PR #76 (importacceptans), #77 (stale Builder HTTP-svar), #78 (IPv4 host network/broadcast), #79 (VLAN-statistik och full JS-CI). Dessa ska skyddas med regressioner, inte implementeras om.

**Kända riskområden, inte automatiskt belagda buggar:** otillräcklig oberoende protokolljämförelse; okända variationer i verkliga företagsdokument; komplexa större moduler; stora och oregelbundna nät; otestade plattformar; historiskt missvisande README/arkitekturstatus; tangentbordsberoende delar av Builder.

## 3. Etappöversikt och beroenden

| Etapp | Mål | Prioritet | Status |
|---|---|---|---|
| QUALITY-000 | Spårbar baslinje för kod, tester och risker | Hög | DELVIS |
| QUALITY-001 | VLAN-kandidatstatistik + full JS-CI | Hög | ACCEPTED |
| QUALITY-002 | Bevisat obligatoriskt GitHub-mergeskydd | Kritisk | CONFIGURED / ENFORCEMENT NOT_VERIFIED |
| QUALITY-003 | Oberoende nätverksprotokollverifiering | Kritisk | ACCEPTED – VERIFIED SUPPORTED SUBSET; broader cases NOT_VERIFIED/UNSUPPORTED |
| QUALITY-004 | Skrivskyddad arkitekturrevision; endast verifierat motiverade små extraktioner (KEEP som standard) | Hög | NEXT: READ_ONLY 4A; NOT_STARTED |
| QUALITY-005 | Dataintegritet, samtidighet och robusthet | Kritisk | PLANNED |
| QUALITY-006 | Verklig dokumentationsimport och proveniens | Hög | PLANNED |
| QUALITY-007 | Prestanda, skalning och resursgränser | Hög | PLANNED |
| QUALITY-008 | Frontend, pedagogik och tillgänglighet | Medel–hög | PLANNED |
| QUALITY-009 | Linux-exklusiv distribution och Linuxkompatibilitet | Medel–hög | PLANNED |
| QUALITY-010 | Aktuell dokumentation och reproducerbar QA | Hög | PLANNED |
| QUALITY-011 | Oberoende slutrevision och betyg | Kritisk | PLANNED |

**Rekommenderad ordning:** QUALITY-002 → QUALITY-003 → QUALITY-004 → QUALITY-005 → QUALITY-006 → QUALITY-007 → QUALITY-008 → QUALITY-009 → QUALITY-010 → QUALITY-011, med QUALITY-000-baslinjen uppdaterad löpande. Ett nytt bekräftat P0/P1-fel bryter ordningen och korrigeras först. Protokollverifiering ska ske före större motorrefaktorering. Etapper får delas i små verifierade del-PR:er; bara en aktiv utvecklingsgren/PR åt gången.

## 4. QUALITY-000 – Kvalitetsbaslinje och spårbarhet

**Syfte:** Skapa objektiva mätpunkter före förändringar.

**Arbete:** inventera produktionsmoduler, ansvar, importgraf, HTTP-gränser, kanonisk projektmutation, asynkrona anrop/stale-guards, duplicering, testtäckning per funktion, bekräftad teknisk skuld, deklarerade plattformar och resursgränser. Mät filstorlek och komplexitet endast som observation, aldrig som automatisk defekt.

**Leverans:** versionshanterad modul-/ansvarskarta, testmatris, lista över bekräftade defekter och osäkerheter, prestandabaslinje, riskrankning. Klassificera allt VERIFIED / NOT_VERIFIED / UNSUPPORTED / CONFIRMED_DEFECT.

**Acceptans:** en oberoende utvecklare kan identifiera en enda sanningskälla för varje funktion samt vilka positiva/negativa kontrakt som redan är verifierade.

## 5. QUALITY-001 – VLAN-statistik och komplett JavaScript-CI

**Status: IMPLEMENTED, PR #79 MERGED, main-CI SUCCESS.**

- Kandidatens VLAN-statistik läser kanonisk `port.vlan`, inte `port.vlanMode`.
- Chromium kontrollerar importerad kandidat med 0, access, trunk och två VLAN-portar.
- Node-test täcker `null`, frånvarande fält och giltiga VLAN.
- GitHub Actions kör hela `npm run check` som del av `unit-tests`.
- Python, Node, Chromium och riktig Save/Open har passerat på integrerad commit.

**Acceptans:** `VLAN CANDIDATE METRICS: PASS`; `FULL JAVASCRIPT CI: PASS`. Ingen ny implementation utan ny reproducerad regression.

## 6. QUALITY-002 – GitHub som verklig kvalitetsgrind

**Status: CONFIGURED, ENFORCEMENT NOT_VERIFIED.**

**2A – Inventering:** verifiera aktiva `main`-regler: PR-krav, linjär historik, deletion/non-fast-forward-skydd, obligatoriska `unit-tests` från rätt GitHub Actions-app. Inga bypass-aktörer får oavsiktligt tillkomma.

**2B – Negativ enforcement-verifiering:** skapa en tydligt namngiven tillfällig testbranch och test-PR med avsiktligt misslyckad `unit-tests`, **utan ändring av produktionskod och utan ändring av regler/obligatoriska workflow-definitioner**. Test-PR:n får **ALDRIG** mergas, läggas i mergekö, försöksmergas via PUT/GraphQL/CLI eller användas för riskfylld direktpush. Samla separat (a) FAIL på exakt PR-HEAD från rätt GitHub Actions-app och (b) GitHubs **icke-muterande regler-/mergekravsstatus** som uttryckligen rapporterar blockeringen. Enbart `mergeable=true/false`, konfliktstatus eller workflow-FAIL bevisar **inte** ruleset-enforcement. Om tillgängliga läs-API:er inte kan fastställa blockeringen: **ENFORCEMENT NOT_VERIFIED**, aldrig simulerat PASS och inget riskfyllt mergeförsök. PENDING/missing testas bara om det kan göras säkert utan att försvaga CI. Stäng negativa test-PR:n utan merge, återställ/ta bort endast dess uttryckligt tillfälliga branch och bevisa att `main` inte ändrats. Under den negativa testen får ingen annan utvecklings-PR pågå.

**2C – Strict-policy:** riskbedöm `strict_required_status_checks_policy=false` jämfört med krav på uppdaterad branch. Bedöm både race mellan bas och PR-HEAD samt extra CI-kostnad. Behåll alltid den befintliga manuella grinden för förväntad bas.

**2D – Policy:** förbjud direktcommit, force-push, bypass, merge på FAIL/PENDING/UNKNOWN och tyst CI-bortkoppling.

**Acceptans:** `REQUIRED STATUS CHECKS: ENFORCED` först efter ett otvetydigt **icke-destruktivt GitHub-blockeringsbevis** för en verkligt röd PR från rätt integrationskälla. Inga merge-API-försök på test-PR tillåts. Räcker inte verktygsinformationen: NOT_VERIFIED och stopp med exakt saknat bevis, inte PASS.

## 7. QUALITY-003 – Oberoende protokollverifiering

**Acceptansbeslut 2026-11-23 (begränsad till uttryckligen stödda regler):** Fyra avgränsade oberoende test-PR:er #100–#103 mergades efter båda obligatoriska `unit-tests`-kontrollerna SUCCESS på **exakt respektive PR-HEAD**. Verifieringsrapporten #104 mergades efter samma grind. Slutlig obligatorisk main-CI på exakt `ba674047e779750f5c8efa7739cf0f80a26fd5d6`, [run #45238708767](../actions/runs/45238708767), har **completed / SUCCESS** från GitHub Actions app `15368`, inklusive det obligatoriska jobbet `unit-tests`. Därmed: **QUALITY-003 ACCEPTED – VERIFIED SUPPORTED SUBSET (3A–3F:s dokumenterade referensfall)**. Detta är inte generell RFC-/IEEE-certifiering; ej täckta varianter förblir **NOT_VERIFIED** och funktioner utanför simulatorns kontrakt förblir **UNSUPPORTED**. Exakta testförväntningar, observationer och avgränsningar finns i [QUALITY_003_VERIFICATION_REPORT.md](QUALITY_003_VERIFICATION_REPORT.md). QUALITY-002 är **ENFORCEMENT NOT_VERIFIED** och påverkas inte av detta beslut. Denna acceptans ger inget nytt ändringstillstånd för protokollmotorer, scheman eller CI-skydd.


**Prioritet: KRITISK.** Referensmatrisen ska fastställa förväntat utfall **före** den granskade motorns körning. Förväntade svar får inte genereras av testad produktionskod.

**3A Ethernet / Layer 2:** source-MAC-inlärning, known/unknown unicast, flooding, broadcast, tabeller, kabel-/portfel, alternativa vägar och explicita loop-/STP-begränsningar. Visuella koordinater får aldrig ändra forwarding.

**3B VLAN:** access/trunk, tillåtna VLAN, tagg-/isolationssemantik inom stödd modell, dropporsaker, broadcast och inlärning per korrekt VLAN. Oimplementerade features får ej antas.

**3C ARP (RFC 826):** Request/Reply, MAC- och IP-identitet, cache, svarslös ARP, ogiltigt paket, dubblerad adress, fel VLAN, kabelbrott.

**3D IPv4/routing (RFC 791, RFC 1812, RFC 3021 och relevanta adressregler):** subnät, /30-/31-/32-semantik, connected/static, longest-prefix match, next-hop, fel interface, TTL, returväg, ingen route och paketleverans. Route lookup är inte bevis på reachability.

**3E ICMP (RFC 792):** Echo Request/Reply, korrekta checksummor, type/code, identifierare, sekvens, payload, routerfel inom stödd omfattning; fall med framåtväg utan returväg får aldrig ge REPLIED.

**3F DHCP (RFC 2131):** Discover/Offer/Request/ACK, lease, renewal, felaktig Layer 2-väg, tillstånd, sessioner och separering av virtuell DHCP-tid från processklocka.

**Referensmetoder:** publicerade standarder, oberoende beräkningar av paketbytes och checksummor, referensimplementationer och/eller kontrollerade paketfångster från extern testmiljö. Minst en verkligt oberoende förväntanskälla per stödd regelklass; dokumentera källversion och avgränsning.

**Metamorfa negativa tester:** en raderad nödvändig kabel ska inte förbättra reachability; irrelevant nod ska inte förändra en isolerad väg; nodposition ska inte påverka routing; ogiltig VLAN-övergång ska inte passera; saknad returroute ska aldrig ge Echo Reply; Save/Open får inte ändra nätverkets betydelse.

**Leverans:** `Protocol Reference Matrix` med standard, scenario, förväntad och observerad observation, testkod, avvikelse, status samt dokumenterat UNSUPPORTED.

**Implementationsspärr QUALITY-003:** börja med oberoende facit och **nya tester**, inte med ombyggnad av protokollmotorerna. Om ett test påvisar reproducerbar avvikelse får endast en isolerad, negativt testad korrigering inom existerande protokollkontrakt föreslås/genomföras i **egen liten PR**. Stöds inte protokollfunktionen ska den märkas UNSUPPORTED, inte automatiskt implementeras eller emuleras. Inga nya protokoll, automatiska antaganden eller kompatibilitetslöften.

**Acceptans:** alla avtalade oberoende referensfall PASS utan oförklarade avvikelser; inga kända falskt positiva dataplanresultat; full lokal och CI-regression PASS.

## 8. QUALITY-004 – Begränsad arkitekturrevision och endast bevisat motiverad modularisering

**Status: NEXT – QUALITY-003:s verifierade stödomfattning är accepterad; börja med skrivskyddad QUALITY-004/4A. Inga kodändringar godkända.** QUALITY-004 är **inte** en beställning av ny allmän modularisering, totalrenovering eller automatisk refaktorering. Syftet är att bedöma om någon *konkret* återstående ansvarskonflikt, duplicerad affärsregel eller testbarhetsbrist medför påvisbar underhålls- eller regressionsrisk. **KEEP är grundbeslutet. Noll ändrade rader produktionskod är ett fullt godkänt resultat.**

### 4A – Obligatorisk, skrivskyddad nulägesrevision före kodförändring

1. Verifiera aktuell `main`, CI, aktiva PR:er och de bindande kontrakten. Gör en ny modulkarta och skilj **historiskt redan genomförd modularisering** från faktiskt återstående problem. 3A–3E och 3D-SGC från den historiska färdplanen är integrerade arbeten, **inte** etapper som ska göras om. Bekräfta faktiska gränser i koden; anta inte att gammal dokumentation är aktuell.
2. Kartlägg ägarskap för kanoniskt projekt, val/ändringsrevisioner, asynkrona stale-guards, Save/Open, import/proveniens, presentationsansvar, API-kontrakt, sessionernas tillstånd och nätverksmotorernas ansvar. För en tänkt ändring: visa berörda funktioner/rader, faktiska in- och utdata, sidoeffekter, beroenden, testfall och **ett konkret problem eller en reproducerbar risk**.
3. Klassificera varje granskat område som **KEEP**, **INVESTIGATE** eller **SMALL_EXTRACTION_CANDIDATE**. `REWRITE` och `DELETE` får enbart förekomma som *separata förslag* med verifierad skadeverkan och tydlig motivering, **aldrig som tillstånd att genomföra ändringen inom QUALITY-004**. Saknas evidens: **KEEP / NOT_VERIFIED**, inte spekulativ kodändring.
4. Redovisa jämförelsen mellan att **låta koden vara** och att extrahera den: hur många ansvar/beroenden försvinner, tillkommer nya callbacks/abstraktioner, eller uppstår ytterligare synkroniseringsrisk? Endast ett nettobättre och mätbart alternativ får gå vidare. Radantal, filstorlek, funktionens ålder, stil, AI-misstanke eller önskan om symmetriska moduler är **aldrig tillräckliga skäl**.
5. 4A levererar en **versionshanterad revisionsrapport** med spårbara KEEP-/kandidatbeslut. Den får avslutas utan kod-PR. Att hitta ett nytt möjligt område ger bara en granskningspost, **inte** automatiskt utökat implementationsscope.

### Avgränsade områden att granska – inte automatiska arbetsorder

| Område | Bekräftad utgångspunkt / fråga att pröva | Tillåten riktning | Grundbeslut |
|---|---|---|---|
| `web/app.js` | Entrypoint och sammanhållande projektägare; fortfarande omfattande rendering och UI-händelser. `renderDoraSession()` hanterar flera presentationsdelar. | **Endast ren, självständig DORA-presentation** eller annan lika väl belagd ren visningsfunktion med få explicita argument; behåll projekt, revisionsräknare, mutation, val, handlers och samordning i befintlig ägare. Följ den redan etablerade ICMP-panelmodellen om den faktiskt förenklar. | INVESTIGATE |
| `web/features/projects/import-review.js` | Granskningsflödet har redan ett gemensamt ägarskap för källor, val, proveniens, generationer och asynkrona skydd. | Högst en **ren tabell-/diagnostikrenderer** om oberoende data och tydlig gräns kan visas. **Dela inte granskningsläget eller dess controllers** enbart för att modulen är lång. | KEEP; villkorlig utredning |
| `network_core/import_plan.py` | Sammanhängande claims, källursprung, konflikter, beroenden och kandidatbygge; inspektion, evidens och källverifiering är redan separerade. | **Ingen större uppdelning under 4A/4B**. Om en verifierad duplicerad *ren regel* påvisas: dokumentera den för separat riskbedömning **efter** oberoende kontrakts-/provenienstester. | KEEP / hög regressionsrisk |
| `network_core/server.py` | Explicit HTTP-gräns och routes delegerar faktiskt protokollarbete till befintliga moduler. | **Ingen generell router-/dispatch-omskrivning**, ingen ny API-abstraktionsstack. Endast konkret reproducerat gränsproblem kan föreslås separat. | KEEP |
| `tests/browser_smoke.py` | Verkliga Chromium-flöden och regressionskontroller är omfattande och delvis samlade i en lång körfunktion. | Möjlig **testorganisatorisk** uppdelning som *egen* liten PR, alternativt QUALITY-010, bara om alla scenarier, negativa fall, DIRECT_HTTP, riktiga filer, omstart och körningssemantik bevaras exakt. Aldrig ersätta browser med stubs för att minska testtid. | INVESTIGATE; inte produktionsrefaktor |
| Befintliga `network_core`-protokollmoduler, lagring, sessionregister och `web/features/sessions/*` | Ethernet, ARP, IPv4, ICMP, DHCP, routing, Save/Open och livscykelcontrollers har redan separata ansvar och regressioner. | **Ingen ommodularisering utan individuellt reproducerad defekt eller verifierad ansvarskonflikt.** Problem i protokollsemantik hör först till QUALITY-003; race, datatapp och serverrobusthet hör till QUALITY-005. | KEEP |

Ovanstående är **undersökningsprioriteringar, inte bekräftade designfel**. Tidigare uppmätta radantal är endast bakgrundsdata, aldrig ett minskningsmål. Övriga moduler har **KEEP som standard**. Om 4A upptäcker en hittills okänd allvarlig defekt ska den dokumenteras med exakt reproduktion, klassificeras efter risk och hanteras enligt planens ordning för P0/P1 – inte användas för att smyga in en bred refaktorering.

### 4B–4C – Strikt villkorade små ändringar, inte generell ombyggnad

**Startgrind:** 4A måste först visa minst ett verifierat avgränsat problem och en smal ändring som *mätbart* förbättrar läsbarhet, ansvarsgräns, testbarhet eller faktisk regelduplicering. För varje förslag krävs en kort förändringsspecifikation: konkret problem, exakt scope (filer/funktioner), varför KEEP inte räcker, före-/efterberoenden, mätbar vinst, risker, negativa tester, och en rollback-plan. **Utan detta: inga 4B-/4C-kodändringar.**

- Tillåt **högst ett sammanhängande ansvar per liten PR**: exempelvis extraktion av en *ren* renderer med explicita argument och utan egen kopia av projekt-/sessionstillstånd. Behåll eventbindning och ägarskap där de hör hemma. Om den nya modulen behöver många callbacks, nya state managers, dubbla revisioner eller ökar beroenden: **avbryt och behåll ursprungskoden**.
- Gemensam hjälpfunktion får införas **endast för dokumenterad reell duplicering**, med semantiskt identiska kontrakt. Samma metodnamn, liknande kod eller upprepat formulärutseende är inte tillräckligt. Ingen opportunistisk "cleanup" i närliggande kod.
- **Uttryckligt förbjudet inom denna etapp:** massflytt, automatiska split-by-lines-verktyg, omskrivning från grunden, nya bibliotek/ramverk eller state-managementsystem, alternativa datamodeller, ny motor, gemensam allmän eventbus, generisk serverrouter, migration av projektformat, ändrade protokoll-/importregler eller ändrad användarupplevelse.
- **Förbjuden förlust:** inga borttagna valideringar, felkoder, negativa tester, stale-/race-guards, identiteter, proveniensfält, bytes-/SHA-256-kontrakt, sessionslivscykler, visuella port-/kabelförbindelser, keyboard-/pointerbeteenden eller explicita Save/Open-grindar.
- `REWRITE`, `DELETE` eller omstrukturering av motor-/importkärnan kräver **en ny separat uttrycklig användarorder med eget verifierat kontrakt** och ingår inte i QUALITY-004 genom implicit mandat.
- Om en ny idé eller ett oklart problem uppstår: markera **NOT_VERIFIED**, dokumentera och fortsätt inte med implementation på antaganden. Detta gäller även sådant som inte uttryckligen räknas upp i tabellen.

### 4D – Bevis för ekvivalens och tydlig stoppregel

Före en eventuell kod-PR: etablera referensutfall, riktade positiva och negativa tester på det *gamla* beteendet samt mätningar som visar den avsedda strukturella vinsten. Efter ändring: verifiera **samma** publika beteende och felbeteende, inklusive identiska kanoniska projekt-/källfakta, Save/Open och SHA-256, CSV/XLSX/ODS/JSON-import, proveniens, VLAN/ARP/IPv4/ICMP/DHCP, sessionsinvalidation, sena HTTP-svar och faktisk Chromium-interaktion där relevanta.

Kör minst `python3 -m unittest discover -s tests -p 'test_*.py' -v`, `npm run check` och `python3 tests/browser_smoke.py`; för gränser som berörs tillkommer motsvarande riktade race-, import-, binär-/X11- eller integrationsregressioner. Inga tester får raderas, försvagas, hoppas över eller ersättas med mockframgång. Samma CI- och branchskyddsgrindar som i avsnitt 16 gäller exakt PR-HEAD.

**Omedelbar stoppregel:** om extraktionen ändrar beteende, inför konkurrerande tillstånd, försvagar en garanti, ökar komplexiteten utan bevisad nytta eller saknar jämförbart testunderlag, ska kodändringen återtas och området klassificeras KEEP / NOT_VERIFIED. Grön CI ensam är inte arkitekturekvivalens.

**Acceptans:** en publicerad 4A-rapport med spårbar ansvarskarta och motiverade KEEP-beslut räcker om inga säkra förbättringar finns. Om små kodändringar verkligen görs krävs dessutom uppmätt *minskning* av det angivna konkreta problemet, beteendeekvivalens, full regression och dokumentation av kvarstående risker. **QUALITY-004 får inte ges "PASS" på grund av antal flyttade funktioner, färre kodrader eller fler moduler.**

## 9. QUALITY-005 – Dataintegritet, samtidighet och robusthet

**5A Projekt:** exakta ID, länkändpunkter, schema 1.0–1.4, ogiltiga/okända fält, dubbletter, referenser och ofullständiga objekt; ingen tyst sanering.

**5B Lagring:** atomisk Save, bytes/SHA-256, samtidiga sparningar, namnbyte, filkonflikt, avbrott, projektbyte, äldre fil och full processomstart. Ingen autosave.

**5C Frontend:** kartlägg alla HTTP-svar som kan påverka projekt, diagnos, session eller UI. Testa sena 200/422, överlappande anrop, förändrade indata, New/Open/Import, Stop/Start, Reset/Run, timeout och förlorade svar. Bevara PR #77:s Builder-korrigering.

**5D Server:** registerlås, sessionskapacitet, utgångna ID:n, cleanup, parallella API-anrop, avbruten operation och korrekt processavslut. Flyktiga paket/cache får inte ändra lagrad modell.

**5E Parsergränser:** stora och korrupta filer, ZIP/ODS/XLSX/CSV-kantfall, numeriska och parsergränser, begränsad RAM/CPU och tydlig avvisning utan truncering.

**Dataskydd QUALITY-005:** alla krasch-, race-, avbrotts-, korrumperings- och samtidighetstester ska köras mot uttryckliga **temporära kopior och isolerade testservrar**, aldrig mot användarens riktiga data-dir, projektfiler, home-katalog, riktiga network shares eller produktionsprojekt. Först mät/skydda data, därefter avgränsad defektfix. Förbjud sänkta timeout-/racekrav eller skippade tester som lösning.

**Acceptans:** inget reproducerat tyst datatapp, inkonsekvent Save-status, föråldrad UI-återställning eller falskt lyckad sessionsoperation. Okända race klassificeras och planeras.

## 10. QUALITY-006 – Verklig dokumentationsimport och proveniens

**Syfte:** pröva källtrogen import av oberoende insamlade, anonymiserade arbetsböcker och CSV-filer som **inte** skapats utifrån applikationens egna mallar.

**6A Korpus:** CSV, XLSX, ODS, flera blad/roller, tomma eller oregelbundna rader, avvikande rubriker, partiella och motsägelsefulla port-/VLAN-/länkfakta samt dokumentfamiljer med olika organisationskonventioner. Avidentifiera före offentlig incheckning.

**6B Manuellt facit:** separera direkta cellfakta från användarval, saknade uppgifter, konflikter och ej stödda format. Facit ska bestämmas oberoende av importmotorn.

**Korpus-/integritetsspärr:** externa arbetsböcker får användas bara med uttrycklig rätt att behandla dem och efter dokumenterad anonymisering; inga reala hemligheter eller identifierande kundnät i publik Git. Om underlaget saknas: NOT_VERIFIED, aldrig påhittat företagscase eller dold källa. Ingen ny inferens om kablar/portkopplingar, ingen ändring av importkontrakt eller schema utan separat godkänt uppdrag.

**6C Test:** exakta source IDs, cellpositioner, MappingViews, ImportPlan, beroenden, valda atomära beslut, historisk importEvidence, replay, källhash, schema 1.4, verklig Save/Open och omstart. Inga implicit skapade kablar.

**6D Användarflöde:** observera verkliga mappningsbeslut och begriplighet. En förenkling får aldrig ersätta källfakta med gissningar.

### Obligatorisk acceptansgrind: ingen import av bristfällig topologi

**Applikationen ska inte acceptera ett nätverksprojekt som saknar de uppgifter som krävs för att programmet ska kunna arbeta korrekt med det.**

- Read-only inspektion av ofullständiga källor är tillåten men får inte räknas som lyckad projektimport.
- Projektets explicit avsedda nätverksstruktur måste vara komplett enligt den kanoniska modellen och de funktioner som ska användas; kabel kräver två verifierbart uttryckligen angivna portändpunkter.
- Relevanta olösta/konflikterande källfakta får inte tyst exkluderas för att ge ett falskt lyckat delprojekt.
- Utan nödvändiga data: blockerad tillämpning, källpositionsbundet fel, ingen förändring av arbetsyta eller sparat projekt.
- Efter uttryckliga användarkorrigeringar krävs helt ny validering och separat bekräftelse samt Save. Irrelevanta valfria protokollfält, exempelvis IPv4 i ett enbart Layer 2-labb, ska inte krävas.
- Obligatoriska negativa end-to-end-tester av ofullständiga kablar, bortvalda blockerade relationer, verklig komplettering, ren L2-topologi, atomärt arbetsytebyte och Save/Open. **Befintlig implementation uppfyller inte automatiskt regeln bara för att texten införs.**


**Acceptans:** importerad kandidat innehåller exakt uttryckligen valda och verifierbara fakta; olösta nödvändiga källuppgifter blockerar projekttillämpning. Enbart läsbar dokumentation eller en vald delmängd som döljer kända nödvändiga relationer får inte godkännas som fungerande nätverksprojekt. Ingen tyst datatapp; proveniens kan återverifieras.

## 11. QUALITY-007 – Prestanda, skalbarhet och resursgränser

**Teststorlekar:** flera punkter såsom 3, 47, 100, 500, 1 000 och upp till faktisk deklarerad maxgräns, även varierande port-/länk-/cellantal. Hårdkoda inte specialbeteende för en teststorlek.

**Topologier:** stjärna, kedja, träd, förgrenad routing, segmenterade VLAN, frånkopplade delar och oregelbundna nät. Loopar prövas enligt dokumenterat stöd/avvisning.

**Mät:** validering, importinspektion, kandidatbyggnad, Save/Open, minnes- och CPU-användning, svarstid, SVG-rendering, Builder-interaktion och simuleringsanrop. Dokumentera maskin, OS, Python/Node/Chromium-version, profiler och reproducerbara kommandon.

**Beslutsregel:** bestäm acceptabla budgetar **efter baslinjemätning men före optimering**. Ta inte siffror ur luften. Prestanda får aldrig köpas med utelämnade objekt, förändrade ID:n, avstängd validering eller fabricerade paket.

**Resursspärr:** använd tempdata, mätgränser, tids-/minnesbudget och avbrytbara belastningstester; kör aldrig okontrollerad oändlig eller destruktiv last mot användarmiljö, GitHub-runners eller riktiga nät. Optimera bara en verifierad flaskhals i egen liten PR, med exakt beteendeekvivalens och synlig före-/eftermetrik.

**Acceptans:** uppfyllda reproducerbara budgetar inom uttalade gränser; utanför gräns tydligt fel utan datatapp.

## 12. QUALITY-008 – Frontend, pedagogik och tillgänglighet

**8A Builder:** förståelig port-/kabelgeometri, tydliga valideringsfel, exakta projektmutationer, rätt Save-indikator och skiljelinje mellan dokumenterat fakta och temporär simulering.

**8B Diagnostik:** visa observationer och stöd för slutsatser. Separera NO_ROUTE, ARP_FAILED, VLAN-drop, felaktig returväg och UNSUPPORTED. Inga orsakspåståenden utan evidens.

**8C Pedagogiska uppgifter:** junior IT-tekniker ska kunna tolka symptom, välja undersökning, pröva hypotes, identifiera stödd orsak och verifiera återställd kommunikation; inte bara klicka fram förprogrammerat PASS.

**8D Tillgänglighet:** testa och rätta centrala tangentbordsflöden, särskilt fokuserbart portval och kabelskapande, samt tydliga namn/feedback. Verifiera fullt arbetsflöde i Chromium.

**8E Oberoende användarprov:** låt personer som inte utvecklat appen utföra realistiska uppgifter. Registrera faktisk uppgiftsframgång, feltolkningar och behov av stöd utan påhittade frekvenser.

**UI-spärr:** ett kvalitetsmål medger inte automatisk redesign, nytt navigeringssystem eller ny användarfunktion. Varje korrigering måste utgå från ett reproducerat hinder i en redan stödd uppgift, bevara data/val, tangentbord, pointer, From/To, kopiering, fullbreddstopologi och motordrivna paketresor. Endast smala ändringar med riktiga Chromium-regressioner; användarstudier får inte fabriceras.

**Acceptans:** UI avspeglar alltid kanoniskt tillstånd, begränsningar och faktiska simuleringsresultat; kärnuppgifter kräver inte rå JSON.

## 13. QUALITY-009 – Linux-exklusiv distribution och kompatibilitet mellan Linuxdistributioner

**Bindande plattformspolicy – ENDAST LINUX:** applikationen är en **Linuxapplikation**. Endast Linuxdistributioner är avsedda målplattformar. **Windows och macOS är uttryckligen exkluderade (UNSUPPORTED), inte alternativa, kommande eller valfria supportmål.** Denna etapp får inte användas för att porta, anpassa, paketera, testa eller lägga till kompatibilitetslager för Windows, macOS eller andra operativsystem utanför Linux. Ingen Windows-/macOS-CI, installerare, plattformsspecifik fallback eller plattformsoberoende ombyggnad får införas i QUALITY-009. Om en åtgärd skulle kräva sådant arbete: stoppa den som **OUT_OF_SCOPE**, inte som en uppgift att lösa. Eventuell oavsiktlig exekverbarhet på ett annat OS ger varken supportåtagande eller utvecklingsmål; ingen särskild saboterande OS-spärr ingår i detta dokumentationsuppdrag.

**Syfte:** verifiera reproducerbar installation, drift och distribution **inom Linux-ekosystemet**. Kompatibilitetsmatrisen får innehålla enbart uttryckligt testade Linuxdistributioner och Linuxmiljöer, t.ex. specificerad distribution/version, x86_64 eller annan faktiskt byggd Linuxarkitektur, glibc-/runtimekrav, webbläsarversion samt X11/Wayland när respektive fönstersystem har verifierats. Ej testade Linuxkombinationer anges **NOT_VERIFIED**, inte PASS. Windows och macOS hör inte hemma i en möjlig framtida supportmatris.

**Verifierad plattformsrisk:** `network_core/storage.py` importerar Unix-specifika `fcntl`. Detta är inte ett skäl att införa Windows-/macOS-abstraktioner. Linux-binärer från separata bygg-/artifact-branches bevisar inte att varje framtida `main`-SHA är releasetestad.

**X11-regressionens CI-grind (introducerad i PR #86):** Den tidigare branchbundna X11-testningen ingick inte i obligatorisk `main`-CI. Det verkliga testet `xvfb-run -a python3 tests/browser_primary_selection_x11.py` är nu ett okonditionellt steg i det redan obligatoriska GitHub Actions-jobbet `unit-tests` i `.github/workflows/ci.yml`, för både `push` och `pull_request`. Det äldre fristående workflowet är endast manuell diagnostik, inte en alternativ kvalitetsgrind. **Verifiering måste göras per exakt SHA:** teststeget ska ha SUCCESS på slutlig PR-HEAD och efterföljande `main`-SHA för att anses godkänt; FAIL, SKIPPED eller PENDING betyder att grinden inte är godkänd. Äldre körningar räknas aldrig som verifiering av en ny release-SHA. X11-PASS bevisar varken Wayland-stöd eller generell kompatibilitet mellan Linuxdistributioner.

**Linux-supportkontrakt:** definiera stödda Linuxdistributioner och versioner, CPU-arkitekturer, libc-/runtimeberoenden, lokalt filsystem, webbläsare och fönstersystem, installation, uppstart, nedstängning och uppgradering. Om en del av Linuxmiljön inte är verifierad markeras den NOT_VERIFIED. **Inget** stödarbete för Windows eller macOS får tolkas in i ord som ”plattformskompatibilitet”, ”portabilitet” eller ”supportkontrakt”.

För varje **verifierad Linuxkombination**: ren installation, skapa topologi, import, simulering, Save, processstopp, återstart och Open av exakt samma fil med oförändrade ID:n/bytes. Ange exakta versioner, byggmiljö och begränsningar.

**Paketeringsspärr:** märk enbart binärer för uttryckligen verifierade **Linux-OS/arkitekturkombinationer**. Bygg från exakt redovisad käll-SHA; kontrollera kedjan source → build-logg → artefakt → SHA-256 → verklig start, HTTP, Save/Open och portkonflikt. Bygggrenar, ändrade workflows, lokala proxyer och äldre artefakter får inte användas som oberoende bevis för `main` utan verifierad identisk källkod och relevant testning. Inga Windows-/macOS-byggen, cross-platform-installerare eller portar ingår.

**Acceptans:** reproducerbar ren installation och verkliga integrationstester på de **specifikt angivna Linuxdistributionerna**. Andra Linuxmiljöer märks NOT_VERIFIED; Windows/macOS märks alltid UNSUPPORTED och är utanför projektets plattformsmål.

## 14. QUALITY-010 – Dokumentation och reproducerbar QA

**10A Dokumentationsrevision:** synkronisera README, ARCHITECTURE, denna kvalitetsplan, AGENTS, MASTERPROMPT, import- och protokollkontrakt. Historiska påståenden om ”ännu inte implementerat” ska inte utges för aktuella fakta.

**Dokumentationsspärr:** rätta endast källbelagda sakfel och tydliggör skillnaden mellan historik, normativt kontrakt, mål och verifierat implementerat beteende. Ändra inte normativa protokoll-/import-/projektspecifikationer eller utgå från att ett passerat test gör en gammal historisk kommentar aktuell. Bevara revisionsspår och hänvisa till exakt kod/CI när status ändras.

**10B Funktionsmatris:** IMPLEMENTED / PARTIALLY_SUPPORTED / UNSUPPORTED / NOT_VERIFIED per central funktion, med kod/testreferens och begränsningar.

**10C Reproducerbara tester:** exakta kommandon, Python/Node/Chromium-versioner, beroenden, miljö, direkt-HTTP-verifiering, faktisk processomstart och förväntade fel.

**10D Kompletterande analys:** överväg Python-typning, JS-kontroller, oanvänd kod, importcykler, duplicering och komplexitet endast med verifierad nytta. Linter-PASS är inte beteendebevis.

**10E Kostnadseffektiv CI:** undvik onödiga upprepningar, men bevara alla obligatoriska negativa och riktiga integrationstester. Ändra inte CI för att dölja fel.

**Acceptans:** en oberoende utvecklare kan följa aktuell dokumentation och reproducera verifierad funktion på ren miljö.

## 15. QUALITY-011 – Oberoende slutrevision och 10/10-mål

**11A Scope:** granska exakt release-`main`: kanonisk modell, Ethernet/VLAN/ARP/IPv4/ICMP/DHCP, import och proveniens, sessionslogik, frontend, persistens, CI-regler, deklarerad distribution och dokumentation.

**11B Nya oberoende scenarier:** använd testfall som inte bara kopierar utvecklarens fixturer: alternativa topologier, felaktiga paket och källfiler, överlappande UI-anrop, gränsvärden, omstarter och prestanda.

**11C Defektklasser:** P0 katastrofalt/systemiskt fel; P1 allvarlig falsk framgång eller tyst datatapp; P2 betydande stödd funktionsbrist; P3 mindre defekt/UX/dokumentation. P0/P1 och materiella P2 ska vara korrigerade före slutgodkännande.

**11D Bedömningsram:**

| Dimension | Vikt |
|---|---:|
| Protokoll- och nätverkskorrekthet | 25 % |
| Kanonisk modell och persistens | 15 % |
| Import och proveniens | 15 % |
| Tester och CI-skydd | 15 % |
| Arkitektur och underhållbarhet | 10 % |
| Robusthet, samtidighet och prestanda | 10 % |
| Frontend och tillgänglighet | 5 % |
| Dokumentation och distribution | 5 % |
| **Totalt** | **100 %** |

Varje dimension betygsätts 0–10 med evidens; viktningen ger ett samlat bedömningsunderlag, inte ett automatiskt pris. 

**11E Krav för ett välmotiverat 10/10:** inga kända P0/P1, inga väsentliga kända P2 inom stödd omfattning, oberoende protokollfall utan oförklarade avvikelser, bevisad dataintegritet och verklig Save/Open, negativa import- och race-tester, verifierat GitHub-mergestopp vid FAIL, dokumenterad prestanda och plattformskompatibilitet, ingen omotiverad duplicering/hallucinerad motor, reproducerbar ren miljö och extern kritisk granskare som anser att kvaliteten är högsta nivå. Absolut frånvaro av framtida fel kan aldrig garanteras.

Om granskningen finner 9/10 redovisas evidens, återstående brister och nya avgränsade åtgärder. Självdeklarerad 10/10 utan oberoende belägg är förbjuden.

**Oberoendekrav:** Codex kan förbereda rapporter och hitta fel men får **inte** kalla sin egen granskning extern eller själv utfärda oberoende 10/10-intyg. Om extern kompetent granskare saknas är den grinden NOT_VERIFIED. Slutrevisionen ger inte mandat till bred kodomskrivning; varje upptäckt defekt blir en separat prioriterad, reproducerbar åtgärd.

## 16. Gemensam process och acceptansgrindar per PR

**Före kod:** läs AGENTS, MASTERPROMPT och relevant kontrakt; kontrollera aktuell `main`, CI, öppna grenar/PR:er; välj verifierat problem; skriv testbar positiv/negativ DoD.

**Scopegrind:** kontrollera skyddskontraktet i 1A. Visa tillåtna filer/operationer och icke-mål före första ändringen. Om planerad diff ändrar annan del än det evidensbaserade problemet: STOP, skriv fynd i rapport och fortsätt endast med den godkända kärnan. Ändringar i CI/rulesets, scheman, import-/protokollkontrakt, runtimeberoenden och officiella releasekommandon får aldrig gömmas i vanlig funktions- eller dokumentations-PR.

**Under kod:** minsta sammanhängande lösning, ingen parallell datamodell, inga tysta mutationer, dokumentera nya begränsningar; regressionsfall ska först kunna påvisa problemet.

**Lokala kontroller:**

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`
- `npm run check`
- `python3 tests/browser_smoke.py`
- `git diff --check`
- Etappens egna oberoende verifieringsfall.

**Före squash-merge:** exakt PR-HEAD, samtliga obligatoriska checkar SUCCESS, clean/mergeable, inga blockerande reviews, förväntad `main`-bas och aktiva skyddsregler. Ingen merge vid pending/unknown/fail, konflikt eller behörighetsproblem.

**Efter merge:** verifiera squash-SHA och `main`; kontrollera efterföljande main-CI på exakt SHA innan FINAL ACCEPTED. Misslyckad main-CI kräver separat korrigering; inget falskt godkännande.

**En aktiv utvecklingsgren/PR åt gången.** Separera produktionskod från dokumentations-/mätetapper så att varje PR kan granskas.

## 17. Permanent regel: spara Codex Credits

Codex får aldrig vänta passivt på GitHub Actions.

När kod och lokala tester är färdiga: publicera PR, kontrollera CI **en gång**, merga endast om exakt HEAD redan är godkänd och samtliga andra grindar uppfyllts. Om CI är PENDING/IN_PROGRESS eller okänd: utför endast verkligt produktivt arbete oberoende av CI, annars **avsluta sessionen direkt** med PR-länk, HEAD, run-länk, aktuella resultat och nästa grind.

Förbjudet: `sleep` för CI-väntan, polling-loop, `gh run watch`, upprepade statuskontroller eller tom väntan. CI kontrolleras i separat senare session. Credits-sparande berättigar aldrig bypass av kvalitetskraven.

## 18. Genomförandeordning och avbrottsregler

1. Slutför QUALITY-002 med negativt GitHub-enforcementbevis utan att mergea test-PR.
2. Genomför QUALITY-003 med oberoende protokollreferensmatris och nya negativa tester.
3. Genomför QUALITY-004 efter att motorns förväntade beteende är externt förankrat.
4. Genomför QUALITY-005 dataintegritet, race och resursrobusthet.
5. Genomför QUALITY-006 med autentiskt varierade, anonymiserade externa dokument.
6. Genomför QUALITY-007 med baslinje och deklarerade prestandabudgetar.
7. Genomför QUALITY-008 med verkliga användaruppgifter och tillgänglighet.
8. Genomför QUALITY-009 med en deklarerad, verifierad matris **endast för Linuxdistributioner**; Windows och macOS är utanför projektets supportmål.
9. Genomför QUALITY-010 med aktuellt och reproducerbart dokument-/QA-underlag.
10. Genomför QUALITY-011 som oberoende slutrevision på exakt release-SHA.

QUALITY-000:s spårbarhet och risklista uppdateras vid varje etapp. Vid P0/P1 stoppas den normala ordningen tills felet är hanterat. Dokumentation/CI får aldrig hävda mer än det som testats.

## 19. Obligatorisk rapport per etapp

| Fält | Minimikrav |
|---|---|
| Etapp och bas | QUALITY-ID, exakt före-HEAD |
| Ändringar | Filnamn, varför och faktiskt beteende |
| Reproduktion | Ursprungligt bevis eller dokumenterat förbättringsbehov |
| Positiva och negativa tester | Exakta PASS/FAIL och testnamn |
| Oberoende verifiering | Standard/referens, metod, avgränsning |
| Chromium | DIRECT_HTTP eller ärligt angivet annat testläge |
| Persistens | Verkliga bytes, Save/Open, omstart när relevant |
| CI | Exakt HEAD, körningslänk och status |
| GitHub | PR, merge YES/NO, squash-SHA och main-CI |
| Återstående | Kända P0–P3, NOT_VERIFIED, UNSUPPORTED |
| Acceptans | ACCEPTED / PENDING / FAILED |
| Nästa etapp | Konkreta återstående verifieringsgrindar |

Inga hypotetiska PASS, inga uppfunna täckningssiffror, inga påståenden att en pågående Action är godkänd.

## 20. Slutdirektiv

**Applikationen ska inte bli 10/10 genom att bli större.** Målet är verifierbart korrekt, deterministisk, begriplig, användbar, databevarande och lättunderhållen kod inom ärligt stödda gränser.

Endast faktisk evidens, negativ testning och kritisk oberoende revision kan motivera högsta betyg. Ett känt fel får aldrig döljas för att höja resultatet.
