# Utvecklingskontrakt för nätverksapplikationen

## Verifierad status och dokumentationsföreträde

**Licensgräns:** Repositoryt är publikt men har **ännu ingen vald licens för förstapartskoden**; README och [GitHub-issue #115](https://github.com/Northsw-spec/YadiLab/issues/115) beskriver detta. Kalla inte hela appen juridiskt open-source-licensierad och lägg inte till en root-LICENSE utan rättighetsinnehavarens godkännande. Vendorlicensen för `elkjs` är separat.

**Läs [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)** före ny planering, felsökning eller protokollimplementering. Dokumentet förklarar tidsstämplad kod-/PR-status och vilka äldre anteckningar som är historik. Det ersätter **inte** aktuell källkod, tekniska kontrakt, användarbeslut eller CI-HEAD. Vid konflikt mellan gammal text och verklig kod: stoppa den riskabla ändringen, verifiera, rätta dokumentationen – gissa inte. Pedagogikplanen beskriver en beslutad framtida funktion, inte en befintlig komplett Incidentverkstad.

## Samlad kvalitetsfärdplan mot 10/10

Den enda aktuella etappindelade kvalitetsfärdplanen finns i [docs/QUALITY_IMPROVEMENT_PLAN.md](docs/QUALITY_IMPROVEMENT_PLAN.md). Den omfattar QUALITY-000–011, oberoende protokollreferenser, dataintegritet, import, skalning, användbarhet, distribution och slutrevision. Kontrollera faktisk HEAD/CI och uppdatera verifieringslägen innan en etapp startas. Historiken finns separat i `docs/QUALITY_IMPROVEMENT_HISTORY.md`. Planen **kompletterar**, men ersätter aldrig detta utvecklingskontrakt, [docs/MASTERPROMPT.md](docs/MASTERPROMPT.md), [docs/IMPORT_SOURCE_CONTRACT.md](docs/IMPORT_SOURCE_CONTRACT.md) eller tekniska protokollkontrakt.

## Plattformskontrakt – applikationen är endast för Linux

**Bindande användarbeslut:** applikationen är en **Linux-exklusiv applikation**, avsedd för Linuxdistributioner. **Windows och macOS är uttryckligen UNSUPPORTED och får inte bli utvecklings-, test-, paket-, release- eller supportmål.** Bygg inte Windows-/macOS-kompatibilitet, operativsystemsabstraktioner, portar, installers, särskilda kodvägar eller CI-matriser för dessa system. QUALITY-009 innebär **endast kompatibilitet mellan uttryckligen verifierade Linuxdistributioner**, Linuxarkitekturer och Linuxmiljöer (t.ex. X11/Wayland när verifierat), inte generell plattformsportabilitet. Icke-Linux-förslag klassificeras OUT_OF_SCOPE och får inte påbörjas. Att kod oavsiktligt kan starta på ett annat OS medför inte stöd eller en skyldighet att anpassa den. Se [QUALITY-009](docs/QUALITY_IMPROVEMENT_PLAN.md).

## ELK-/dokumentstatus – tidigare etapper är genomförda

**Korrigerad status 2026-11-24:** ELK-06A, ELK-06B och ELK-06C är **redan integrerade** genom mergade PR #94, #95 och #96 (2026-11-22). Koden accepterar koordinatfria strikta CSV-/XLSX-/ODS-dokument (med äldre kompletta X/Y-par som kompatibilitet), kör initial automatisk ELK-layout efter godkänd dokumentationsimport och exporterar/mallar nätverksdokument utan källkrav på X/Y. Projektfiler sparar fortsatt interna presentationskoordinater. Detta är kontrollerat mot kod, testkatalog och mergehistorik på granskad bas; kontrollera ny HEAD och CI vid framtida ändringar.

**VARNING:** Framåtblickande ELK-06-uppgifter och ”nästa PR”-texter i den daterade [ELK-planen](docs/ELK_IMPLEMENTATION_PLAN.md) är **historiska arbetskort**, inte giltiga order att återimplementera 06A–C. Behåll befintlig Worker, ELK, SVG, identiteter, importproveniens, Save/Open och stale-guards. Nya ELK-fixar kräver separat konstaterat problem, uttryckligt scope, test och befintliga kvalitetsgrindar. Förvandla inte historisk plan till en ny konkurrerande roadmap.

**Källdokumentkontrakt:** Externa nätverksdokument kräver aldrig X/Y som indata; källcellernas rad-/kolumnadresser är proveniens, inte nodgeometri. Ingen ELK-layout får lägga till, ta bort eller ändra nätverksnoder, portar, fysiska länkar eller routing. Automatisk första layout efter godkänd dokumentimport är inte automatisk sparning och ska inte tillämpas när ett sparat projekt med egna koordinater öppnas.

## Bindande pedagogisk arkitektur – Om → Då → hypotes → bevis

**Användarbeslut 2026-11-24:** [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md](docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) är normerande **för innehåll och sanningskrav i framtida undervisning**, men inte för PR-prioritet, schema eller nya motorer. **Befintlig funktionalitet är KEEP.** Studentens mål är att kunna tolka observationer, pröva konkurrerande förklaringar och verifiera åtgärder. En förklaring ska alltid skilja mellan källfaktum, protokolldefinierad betydelse, hypotes, native-simulering och verkligt verifierat nätverk.

**Exakta första rubriker:** "**Om [observerat]:**", "**Då [vad det faktiskt betyder]:**", "**Möjliga orsaker [inte fastställda/hypoteser]:**". Den kompletta niorubriks-mallen och regler för motbevisande tester finns i pedagogikplanen; visa den stegvis för nybörjare. En icke-fastställd grundorsak får inte formuleras som ett faktum. Använd inga påhittade konfidensprocent; elevens självskattning märks tydligt som sådan.

**INGEN tredjepartsintegration:** SuzieQ, Batfish, Netshot, Wireshark, NetXMS, FRRouting och containerlab får förklaras med verifierade statiska undervisningsexempel och frivilliga manuella labbinstruktioner. De får **inte** installeras, köras, anropas, importeras, skannas med, orkestreras eller inkluderas som källkod, SDK, API-adaptrar, container- eller runtimeberoenden i applikationen med stöd av denna plan. OSPF/BGP/SNMP/STP/ACL/NAT som kursämnen betyder **inte** att de finns i applikationens native motor eller att ny sådan motor har beställts. Inga nya importerare, shellkommandokörning, kundnätprober, schemaändringar eller automatiserade utvecklingssteg följer av detta dokument.

**Kvalitetsordning oförändrad:** [QUALITY_IMPROVEMENT_PLAN.md](docs/QUALITY_IMPROVEMENT_PLAN.md) är fortfarande enda gällande kvalitetsroadmap. Pedagogikplanens P0–P7 är **idéer som kräver separata uttryckliga uppdrag**, inte en andra ”fortsätt”-kö. Granska nuvarande kod, tester och CI före varje implementation.

## Permanent Masterprompt

**Läs [docs/MASTERPROMPT.md](docs/MASTERPROMPT.md) före varje utvecklingsetapp.** Den är projektets långsiktiga utvecklingsdirektiv fram till användarens slutgodkännande. Denna AGENTS-fil anger korta, operativa regler; den fullständiga målbilden, prioriteringen, acceptanskriterierna och rapporteringskontraktet finns i Masterprompten. Vid konflikt ska den senaste uttryckliga användarinstruktionen följas och aktuell källkod/CI kontrolleras.

## Projektgräns

- Detta är en **ny, fristående implementation**, inte en fork eller ompaketering av äldre produktkod.
- Kopiera inte källfiler, komponentträd, bakåtkompatibilitetslager eller testkod från äldre projekt utan ett separat uttryckligt beslut baserat på verifierad funktionalitet.
- Undvik parallella arkitekturer. En kanonisk dokumentationsmodell och en presentationsväg.
- Körbar nytta prioriteras över mängden kod, projektbeteckningar eller antalet passerade kontroller.

- **Produktnamn och dokumentationsundantag (2026-11-24):** `APP_NAME` i `network_core/config.py` är den **enda deklarationen av applikationens visningsnamn**. UI, HTML, fönstertitel, loggar, hälsosvar och terminal ska hämta namn från den variabeln – inga hårdkodade produktnamn i exekverbar kod, JS, HTML, CSS, konfiguration eller testfixturer. Klasser, funktioner, paket, moduler och källfilnamn ska vara neutrala och generiska. **Människoläsbar Markdown-dokumentation (`AGENTS.md`, `README.md`, `docs/*.md` och andra `*.md`) får däremot använda projektnamnet `YadiLab` i rubriker och beskrivande brödtext.** Det är en historisk/projektmässig referens, **inte** en ny deklaration av UI-namnet. Dokumentationen får inte instruera Codex att skapa produktnamnsbundna källkodsidentifierare. Inga källkodsfiler eller andra icke-Markdown-filer undantas från namnkontrollen; även filvägar kontrolleras. Den tekniska filändelsen `.yadilab` bevaras för bakåtkompatibilitet. Båda kontrollerna i `tests/test_naming_contract.py` ska fortsatt passera. Senare byte av `APP_NAME` kräver ingen omskrivning av projektnamn i Markdown.

## Bindande importgrind: inga bristfälliga nätverksprojekt

**Applikationen ska inte acceptera ett nätverksprojekt som saknar de uppgifter som krävs för att programmet ska kunna arbeta korrekt med det.**

- **Källgranskning är inte projektimport.** Inspektion får visa saknade/inkonsekventa fakta men aldrig automatiskt skapa ett delvis användbart projekt.
- **Inga antagna anslutningar.** För varje fysisk kabel krävs båda explicita nod-/portändpunkterna. Saknas de, eller andra data som är nödvändiga för den deklarerade topologin och avsedda stödda funktionerna, ska projekttillämpning blockeras. Importera inte en vald delmängd som döljer kända relevanta fel.
- **Ingen övervalidering av frivilliga protokollfält.** En topologi avsedd enbart för Layer 2 behöver inte IPv4 eller routes; kraven styrs av faktisk modell och avsett arbete.
- **Fail-closed och atomärt.** Redovisa källposition och saknad uppgift, låt användaren komplettera uttryckligen, validera om hela valda projektet, tillämpa först efter explicit godkännande och spara endast efter separat Save. Vid blockerare ändras varken arbetsyta eller disk.
- **Regleringen är ett målkontrakt, inte ett påstående att dagens kod redan uppfyller det.** Inga smygändringar i importkod; implementering och negativa end-to-end-tester krävs separat. Detaljer: [docs/IMPORT_SOURCE_CONTRACT.md](docs/IMPORT_SOURCE_CONTRACT.md), avsnittet ”Bindande huvudregel för extern nätverksprojektimport”.

## Oförhandlingsbara funktionella invariants

1. **Inga implicita länkar:** IP-adresser, default gateways, geografisk zon, nodposition och liknande får aldrig skapa en kabel, router eller enhet.
2. **Förlustfri eller avvisad import:** okända eller ogiltiga data får inte tyst försvinna; avvisa hellre formatet med ett begripligt fel.
3. **Äkta identiteter:** noder, portar, zoner och länkar ska överleva Save/Open med exakt samma identifierare och deklarerade ändpunkter.
4. **Begränsa sanningsanspråk:** topologisk grafväg är inte verklig Layer-2-/Layer-3-reachability. Bygg aldrig en generisk ping-PASS ovanpå BFS.
5. **Avgränsa nya funktioner:** lägg till en beteenderegel och ett negativt test före en ny integrationsväg.
6. **Beständighet:** skriv bara efter användarens uttryckliga Save. Ingen autosave, dold overwrite eller falsk verifiering av webbläsarnedladdning.
7. **Ingen skönmålning i tester:** riktiga negativa tester, riktig fil på disk och omstart ska skiljas från en simulerad filväljare eller syntetisk stub.

## Scope och process

- Fokus är korrekt funktionalitet, begripliga användarflöden och borttagning av onödig eller felaktig kod. Starta inte pentest eller separata säkerhetshärdningsprojekt utan användarens begäran.
- Gör så små verifierbara ändringar som möjligt. Ha bara en aktiv utvecklingsgren/PR. **KEEP är standard** för fungerande kod; varje QUALITY-etapp måste följa tillståndsgrindarna i kvalitetsplanens avsnitt 1A. Etappnamn, REWRITE/DELETE-etiketter, radantal eller grönt CI ger aldrig i sig tillstånd till bred refaktorering, kontraktsändring eller borttagen funktion.
- Kör `python3 -m unittest discover -s tests -p 'test_*.py' -v`, `npm run check` och `python3 tests/browser_smoke.py` före kodleverans när miljön tillåter.
- Om webbläsaren blockerar lokal HTTP kan browser_smoke använda sin uttryckligt märkta bro, men det är **inte** bevis för normal direkt HTTP i den miljön.
- **Stående användargodkännande för automatisk merge:** Merga varje färdig och avgränsad PR automatiskt via GitHubs normala mergeflöde när den exakta PR-HEAD har PASS på alla obligatoriska CI-kontroller, negativa/funktionella tester är verifierade, PR är konfliktfri och mergebar, inga blockerande reviews finns och `main` fortfarande är förväntad bas. Använd squash när lämpligt. Begär inte nytt mergegodkännande per PR. **Merga aldrig** vid FAIL/PENDING/okänd CI-status, konflikter, oklara ändringar, obehörighet eller när branchskydd skulle behöva kringgås. Rapportera hindret i stället. Automatiken innebär ett beslut vid varje körning, inte ett påstående om obevakad bakgrundskörning.

## Codex Credits: ingen passiv väntan på GitHub Actions

- **Minimera förbrukning av Codex Credits.** När en GitHub Actions-körning har startats får Codex inte sitta inaktivt och invänta resultatet. Förbjudet: `sleep`, polling-loopar, återkommande statusförfrågningar eller annan väntan vars enda syfte är att hålla Codex-sessionen öppen medan CI kör.
- **Välj produktivt arbete eller avsluta direkt:** Om det finns en tydlig, relevant och oberoende uppgift som kan utföras utan det pågående CI-resultatet, fortsätt med den. Det kan vara lokal verifiering, granskning, negativ testning eller dokumentation inom samma godkända scope. Påstå aldrig att pågående CI är godkänd. Om arbete ändrar PR-HEAD måste de obligatoriska kontrollerna verifieras på den **nya** exakta HEAD:en.
- **Om inget meningsfullt oberoende arbete återstår:** Avsluta Codex-sessionen omedelbart efter en kort slutrapport. Ange PR-länk, exakt PR-HEAD, CI-körningens länk och aktuella status, genomförda tester, kvarvarande grind och nästa konkreta åtgärd. Lämna PR öppen när CI fortfarande är PENDING eller okänd. Be inte användaren hålla sessionen aktiv.
- **Kontrollera CI i en ny session:** Användaren eller ett senare uttryckligt uppdrag kan kontrollera den färdiga körningen och, om samtliga regler i mergekontraktet är uppfyllda, utföra normal squash-merge. Codex får förstås direkt agera på ett CI-resultat som redan finns tillgängligt utan väntan.
- **Ingen genväg runt kvalitetsgrindarna:** Credits-besparingen berättigar inte till merge vid PENDING/FAIL, ignorerade tester, tysta scopeändringar eller påhittade verifieringsresultat. Endast själva passiva väntan ska elimineras.

## Styrd importspecificering för etapp 4

Vid arbete med dokumentationsläsning eller import måste `docs/IMPORT_SOURCE_CONTRACT.md` läsas före design, kodning, PR och slutsatser. De historiska importetapperna 4A–4D har redan integrerats; **4A är inte längre ett nästa byggsteg och får inte genomföras om av misstag**. Deras blotta existens bevisar inte att fullständighets-/provenienskontraktet är uppfyllt. Gällande vidare verifiering sker enligt QUALITY-006 i `docs/QUALITY_IMPROVEMENT_PLAN.md`. Chatthypoteser och forskningsuppsatser är inte importkontrakt; nya importbeteenden får inte gissas eller införas som parallell kodväg.

## Explicit CSV-import

- Använd endast `network_core/csv_import.py` för de namngivna tabellerna Devices/Interfaces/Links/Zones. Ingen heuristisk import och ingen implicit kabelskapning.
- Validera hela importen före användarens uttryckliga godkännande att ersätta arbetsytan; ingen autosave.
- Funktionella negativa tester ska omfatta saknade, dubblerade, okända och inkonsekventa uppgifter. Verifiera också verklig browser-import och Save/Open.
