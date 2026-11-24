# YadiLab – riskbaserad källkods- och integritetsrevision

**Datum:** 2026-11-24  
**Reviderad bas:** `main@ed1deb6d3179987b1293e4854d4fb92b19ccf05d` efter dokumentations-PR #110.  
**Korrigering:** PR #111, `audit/strict-json-boundary-20261124`.  
**Status:** **PARTIALLY VERIFIED / OPEN FINDINGS** tills alla obligatoriska kontroller passerat på exakt slutlig PR-HEAD, och även därefter **endast verifierad delmängd**. Detta är **inte** en certifiering av generell eller fullständig korrekthet.  
**Plattform:** Linux. Windows/macOS är UNSUPPORTED.

## 1. Vad som faktiskt granskats

- Hela repositoryts Git-tree inventerades: 187 versionshanterade vanliga filer, däribland `network_core/`, `tests/`, `docs/`, `web/` och GitHub Actions. Ingen trunkering i API-listningen.
- Aktuellt protokoll- och utbildningskontrakt i `AGENTS.md`, `docs/MASTERPROMPT.md`, `docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md` och `docs/IMPLEMENTATION_STATUS.md` har jämförts med identifierade kod- och testmoduler.
- Känsliga implementationsdelar lästes/undersöktes riskbaserat: `network_core/model.py`, `storage.py`, `server.py`, `json_boundary.py`, `import_workbooks.py`, `xlsx_import.py`, `ods_import.py`, `import_inspection.py`, `import_evidence.py`, `import_plan.py`, `simulation.py`, `dhcp_registry.py`, `session_idle.py` och `web`-modulerna för import, DOM, sessionskontext, ELK samt klient-API.
- Exakta obligatoriska CI-steg kontrollerades i `.github/workflows/ci.yml`. Den kör Python `unittest discover`, `npm run check` (JavaScript-syntax och Node-tester), verklig Chromium Save/Open, riktig X11 PRIMARY-regression samt flera Chromium-ELK-tester. Detta är positivt bevis **endast när den enskilda körningen faktiskt slutförts med SUCCESS**; en grön PR innebär inte automatiskt grön ny `main`.
- Befintliga testfiler som rör lagring, HTTP-gränser, import, oberoende protokollvektorer, IP/ICMP/DHCP, sessionsraces, X11 och ELK identifierades. Revisionen har **inte** manuellt exekverat hela kodbasen i en fristående utvecklingsmiljö, och ingen riktig kundutrustning eller produktionsanläggning har provats.

## 2. Bekräftade positiva skydd i kod, inte generella garantier

| Riskområde | Källkodens påvisade skydd | Exakt begränsning |
|---|---|---|
| Konfigurations- och topologifakta | `validate_project` avvisar okända fält, odeklarerade länkar/portar och mycket av otypad/felaktig data; använder explicita identifierare | Stödomfattningen är snäv och versionsstyrd; detta ger inte automatisk kundnätsdiscovery |
| Save och samtidighet | `ProjectStore.save` använder filbaserad låsning, förväntad SHA-256, temporär fil, fsync och atomisk rename | Testade simuleringar av felbehandling är inte en verifiering av hårdvarudiskar eller alla strömavbrott |
| Lokal server | `LabHTTPServer` kräver bindning på `127.0.0.1`. HTTP-koden kontrollerar Host, Origin, Sec-Fetch-Site, Content-Type och max 8 MiB body. Webbfiler serveras från en explicit allowlist | Loopback är **inte** per-process-/per-OS-användarautentisering |
| Dokumentimport | Bounded base64/bytes, antal rader/celler, ZIP-medlems-/expansionsgränser, ZIP-duplicat- och sökvägskontroller, avvisning av XML DOCTYPE/ENTITY | Ingen komplett hostile-file fuzzing, worst-case-minnestopp eller tredjepartsinteroperabilitet har bevisats |
| Frontenddata | Granskad `web/ui/dom.js` använder DOM/textContent för text; asynkrona sessioner har explicita revisions- och stale-guards | En riktad källgranskning är inte ett heltäckande XSS-/racebevis |
| Protokollsimulering | Native kod och separata tester för avgränsad Ethernet/ARP/VLAN/IPv4/ICMP/DHCP, inklusive returväg och negativa felutfall | OSPF/BGP/SNMP/STP/generella ACL/NAT är inte implementerade native; det är kursämnen och externa verktyg är fristående |
| Lokal tredjepartskod | `elkjs 0.13.0` ligger lokalt under `web/vendor` med NOTICE/licens | Versionslåsning och attribution är inte samma sak som en komplett leverantörskedjegranskning |

## 3. Konkreta avvikelser och kontrollstatus

### F-001 – Dubbla JSON-nycklar kan tyst ersätta nätverksfakta (bekräftad kodavvikelse; PR #111)

**Om [observerat]:** Baslinjens `ProjectStore.read` och `Handler._read_json` använde `json.loads` utan `object_pairs_hook`. Exempel: samma JSON-objekt innehåller två olika `name`-värden eller `schemaVersion` två gånger.

**Då [vad det faktiskt betyder]:** Pythons standardavkodare behåller det sista värdet. Det ursprungliga värdet försvinner **innan** `validate_project` får se dokumentet.

**Möjliga orsaker [inte fastställda/hypoteser]:** Motstridig exporterare, skadad projektfil eller avsiktligt manipulerade JSON-bytes; verklig ursprungsorsak är inte fastställd.

**Korrigering:** En gemensam strikt UTF-8 JSON-gräns avvisar dubbla medlemmar även i nästlade objekt, samt icke-UTF-8, ogiltiga surrogater, icke-finita numeriska värden och överskridet explicit nästlingsdjup. Nya negativa tester använder **äkta HTTP** och **äkta temporära projektfiler**. Godkänn endast vid grön CI på exakt HEAD.

### F-002 – Ogiltig Unicode kan nå Save/HTTP-kodning (bekräftad kodavvikelse; PR #111)

**Om [observerat]:** `json.loads` kan avkoda en ensidig `\uD800`-escape till en Python-sträng. Baslinjens namnfältsvaliderare stoppade inte ensamma surrogate codepoints.

**Då [vad det faktiskt betyder]:** `json.dumps(..., ensure_ascii=False).encode("utf-8")` kan då kasta `UnicodeEncodeError` i stället för en kontrollerad valideringsavvisning, med risk för HTTP 500 och nekad Save.

**Korrigering:** Strikt JSON-kontroll vid bytegränsen och namnfältskontroll för direkta Python-anrop. Åtta nya oberoende regressioner inkluderar ett giltigt svenskt Unicode-fall. Inga schemafält eller persistensformat ändras.

### R-001 – Lokal HTTP-API saknar process-/användarautentisering (verifierad säkerhetsbegränsning)

**Om [observerat]:** `Handler._trusted_request` tillåter korrekt Host från lokala klienter utan Origin-header. `/api/projects` och Save/Open-anrop använder ingen ytterligare token eller per-OS-användarbehörighet.

**Då [vad det faktiskt betyder]:** En *annan lokal process som når loopbackporten* kan anropa lokala API:er. Skydd mot DNS rebinding och cross-origin-anrop från webbläsare utgör inte isolation mot andra lokala processer eller en annan inloggad användare på delad Linuxmaskin.

**Risk:** Sekretess och ändringskontroll för riktiga kunddokument på delade eller komprometterade datorer. **Ingen fjärråtkomst över nätverket påstås**; risken gäller lokal åtkomst. Den avsedda lokala single-user-modellen kan vara godtagbar i användarens hotmodell, men detta är inte en autentiserad fleranvändartjänst.

**Ej beslutad här:** Införande av åtkomsttoken, Unix-domain socket, OS-permissionmodell eller systemintegration kräver eget säkerhetskontrakt, hotmodellsprov och Chromium-/CLI-kompatibilitetstest. Att tyst lägga till inloggning skulle kunna bryta befintliga arbetsflöden. Klassificera `NOT_VERIFIED` för delad-värd-isolation; utge inte servern som autentiserad.

### R-002 – Fullständig protokoll- och leverantörsoberoende verifiering saknas

**Om [observerat]:** `QUALITY_003_VERIFICATION_REPORT.md` godkänner en avgränsad mängd oberoende testvektorer; den säger uttryckligen att protokollets alla varianter inte verifierats. Ingen faktisk jämförelsekörning mot routers/switchar eller en separat FRRouting-stack har utförts i denna revision.

**Då [vad det faktiskt betyder]:** Det finns bevis för specificerade simuleringsfall, men **inte** för alla paketsekvenser, nätverksstorlekar eller reella protokollimplementationer. Status utanför delmängden förblir `NOT_VERIFIED` eller `UNSUPPORTED`.

**Nästa steg:** Nya, separat beställda oberoende referensvektorer och negativa tester för exakt stödd motor; externa labb körs separat från YadiLab, inte integrerat.

### R-005 – Echo Request och Reply delar TTL i modellen (verifierad modellbegränsning)

**Om [observerat]:** I `network_core/icmp_ping.py` skickas Echo Request och Reply genom `IPv4Trace.send` med **samma** användarangivna `ttl`. Det beskrivs också uttryckligen i `docs/ICMP_ECHO.md` och prövas av befintliga tester.

**Då [vad det faktiskt betyder]:** Detta är en definierad förenkling, men **inte en generell sanning om verkligt ICMP**. Ett verkligt Echo Reply är ett självständigt IPv4-paket vars avsändare väljer initial TTL oberoende av inkommande Echo Request. På asymmetriska vägar med låg vald request-TTL kan modellen rapportera `REPLY_FAILED` därför att den tvingade reply-TTL:n också är låg; det är då inte bevis för att en riktig server inte skulle kunna svara med en annan TTL.

**Status:** `CONFIRMED_MODEL_LIMITATION`, **inte** en allmän test-/RFC-acceptans eller en obevisad påstådd bugfix. Kräv explicit pedagogisk märkning (infört i `docs/ICMP_ECHO.md` i denna revision). Framtida oberoende responder-TTL kräver separat godkänt protokollkontrakt, negativ regression och gränssnittsbedömning; ingen dold default får introduceras bara för att göra ping grönt.

### R-003 – Testernas täckning och leverantörskedjan är inte fullständigt certifierade

**Om [observerat]:** CI innehåller reella Chromium/X11-/Python-/Node-gates och lokalt licensierad ELK. Det finns däremot ingen påvisad fullständig SAST-/dependencyscan eller oberoende pentest i den granskade obligatoriska `ci.yml`-kedjan. Alla andra `.github/workflows` ingår inte automatiskt i den enda obligatoriska `unit-tests`-grinden.

**Då [vad det faktiskt betyder]:** Grön CI betyder att just de konfigurerade kontrollerna passerat; inte att varje sårbarhet eller varje real driftmiljö har granskats.

**Nästa steg:** Separat hotmodell, en CI-matris som visar required kontra frivilliga workflows, oberoende licens-/dependencygranskning och avgränsade fuzz-/belastningsfall utan att lossa nuvarande kvalitetsgrindar.

### R-004 – Branchskyddet är ännu inte bevisat på alla relevanta negativa vägar

Enligt `QUALITY_IMPROVEMENT_PLAN.md` är QUALITY-002 `CONFIGURED / ENFORCEMENT NOT_VERIFIED`. En avsiktligt röd PR stoppades, men full oberoende policyverifiering återstår. Att vi själva väntar på grön CI bevisar inte att alla tillåtna integrationsvägar saknar bypass.

## 4. Testmatris för PR #111

| Test | Förväntat utfall | Innebörd |
|---|---|---|
| Sparad JSON med dubbelt `name` | `ProjectValidationError`, exakta filbytes kvar | Ingen tyst ersättning |
| Dubbelt fält i nästlat objekt | Avvisas före kanonisk projektvalidering | Samma skydd på alla JSON-nivåer |
| Riktigt HTTP Save med dubbelt `name` | HTTP 422, ingen fil skapas | Ingen felskrivning |
| HTTP med oparad Unicode surrogate | HTTP 422, inte 500 | Kontrollerad användaravvisning |
| Programmatisk Save med oparad surrogate | `ProjectValidationError`, ingen fil | Skydd även utan HTTP |
| UTF-16 eller `NaN`/icke-finit tal | Avvisas som ogiltig extern JSON | Strikt JSON-kontrakt |
| Uttrycklig JSON-nästlingsgräns | Avvisas vid djup större än 64 | Oberoende av CPython recursion limit |
| Normal svensk Unicode | Valideras och kan sparas/läsas | Befintliga positiva användningsfall bevaras |

**Förbjudet:** sänka tester, tysta undantag, automatiskt reparera brutna JSON-fakta, utöka schema eller ändra sparad projektfil för att testet ska bli grönt.

## 4A. Utökad granskning av protokolladressrymd och leverantörskedja, 2026-11-24

- **R-006, korrigerad delmängd:** Den särskilda IPv4-dataplanmodellen saknade explicit avvisning av wire-unicast i 127/8 respektive 0/8 och blockerade inte RFC 3927-trafik via gateway. PR #114 tillför sex oberoende positiva/negativa tester och en minimal fail-closed-korrigering. Båda obligatoriska PR-HEAD-kontrollerna SUCCESS på `7e7179a868a9ca97ae03e941fee4917a65dd99e8`, merge `50772ef42f5284c88ee65aca1d6d128829d8b5d7`. Direkt same-link 169.254/16 fortsätter fungera. Ingen generell IPv4-certifiering följer.
- **R-007, supply-chain-risk:** Fem workflows använde rörliga `actions/*@vN`-refs. En separat CI-säkerhetsändring SHA-låser dessa till specifika commitobjekt hämtade från GitHub; kräver fullständig testkedja på final HEAD innan ACCEPTED. Dessutom införs explicit minimal `GITHUB_TOKEN`-behörighet och oförändrade leverantörsbytes verifieras mot en redan dokumenterad SHA-256. Detta är inte en komplett säkerhetsrevision av actions eller av Pythonpaket.
- **R-008, licensval blockerad:** GitHubs repo-API rapporterar `private=false` och `license=null`; ingen root-`LICENSE`. [Issue #115](https://github.com/Northsw-spec/YadiLab/issues/115) kräver rättighetsinnehavarens uttryckliga licensval. Public GitHub-hosting och separat ELK-vendorlicens räcker inte för att kalla förstapartskoden OSI-licensierad.
- **R-009, operativ gräns:** OSPF, BGP, SNMP, STP, ACL, NAT och Wi-Fi är **UNSUPPORTED som native motorer**. Ingen testvektor kan bevisa korrekthet för icke-implementerade protokoll. Framtida lärandematerial får referera manuella externa verktyg men får inte beskriva dessa som installerade eller integrerade.

## 4B. F-003 – uppladdad JSON kunde normaliseras innan strikt servervalidering

**Om [observerat]:** `prepareImport(kind='project')` i `web/features/projects/transfer.js` använde `JSON.parse` på användarens JSON-/projektfil innan `/api/validate` anropades. `web/features/projects/import-review.js` använde motsvarande mönster för importerade mappningsprofiler och originalkällpaket. `File.text()` kan dessutom ersätta felaktiga UTF-8-sekvenser.

**Då [vad det faktiskt betyder]:** Standard-`JSON.parse` behåller det sista värdet för en duplicerad medlemsnyckel. Serverns nya strikta parser från PR #111 ser därför *inte* originalets två olika värden om browsern redan har ersatt dem – ett faktiskt källtrogenhetsglapp. Ett grönt serversidetest av rå JSON är inte bevis för att användaren får samma avvisning vid import via UI.

**Möjliga orsaker [inte fastställda/hypoteser]:** Ett externt verktyg som skapat tvetydig JSON, exporterarfel eller avsiktlig manipulation. Ingen specifik användares källa eller nätverk pekas ut.

**Avgränsad korrigering:** Läs hela ursprungsfilen som `Uint8Array` och skicka bytesen direkt till samma strikta serverdecoder i `/api/validate`. För mappningsprofiler och källpaket finns ett read-only `/api/json/strict` som returnerar validerat JSON utan att skapa projekt eller persistera. Centrala `web/services/api.js` ska endast acceptera lokala relativa `/api/...`-adresser, inte HTTP(S)/protocol-relative, dot-segment eller query-URL:er. Nio nya Python-/Node-tester provar originalbytes, 422 för duplicerade nycklar/ogiltig UTF-8, positiv giltig JSON och lokala API-gränser. **Status: ACCEPTED för avgränsade testade JSON-importvägar.** PR #119 final HEAD `81337e72a57493a14d94c792f3a93ed8c4988586` hade båda required `unit-tests` SUCCESS, med faktisk Chromium-profilimport efter bevarad ogiltig-UTF-8-dialog; squash-mergad till `main@f6066038ed07fe6f087fb4d654a7d003d7b60b91`. Detta är inte generell certifiering av alla framtida filformat.

## 4C. F-004 – separat ARP-panel kunde simulera otillåtna Ethernet-IP-källor

**Om [observerat]:** `network_core/arp.py::_ipv4` avvisade multicast, all-zero och all-one IPv4 men hade inte uttrycklig loopback-/this-network-kontroll och avvisade inte andra reserverade klasser. Detta är en annan adressvaliderare än den i `IPv4Datagram` som rättades i PR #114.

**Då [vad det faktiskt betyder]:** Ett dokumenterat 127/8- eller 0/8-interface kunde användas i en fristående ARP-övning så att nätverksappen påstod en Ethernet-ARP-transmission/RESOLVED trots ett adressval som inte ska ge vanlig trådkommunikation. Det är ett kod-/protokollfynd, inte bevis för ett fel i något faktiskt kundnät.

**Möjliga orsaker [inte fastställda/hypoteser]:** Flera modulära protokollgränser byggdes i olika etapper och saknade likvärdiga negativa specialadressfall; historisk motivkedja är inte bevisad.

**Korrigering:** Avgränsat stopp på ARP-wire-codec-nivå, nya negativa tester och verifierade positiva same-link 169.254/RFC1918/TEST-NET-fall. Ingen tyst borttagning av användardokumenterad felkonfiguration eller ändring av DHCP:s separata BOOTP-`0.0.0.0`-användning. **Status PENDING tills full obligatorisk CI på PR-HEAD är SUCCESS.** [Issue #120](https://github.com/Northsw-spec/YadiLab/issues/120).

## 5. Beslutsgrind och gräns för uttrycket ”verifierat rent”

För **exakt den testade committen** kan följande hävdas först efter relevanta gröna tester: källkodens definierade JSON-ingångar avvisar ovanstående fall; specificerade tidigare Python/Node/Chromium/X11/ELK-regressioner rapporterar PASS; inga andra filtyper i PR #111 ändras förutom avgränsad kod, nytt test och denna rapport.

För **hela repositoryt** får man fortfarande inte skriva ”garanterat hallucinations- eller bugfritt”, ”alla protokoll verifierade”, ”autentiserad för alla lokala användare” eller ”säker för alla verkliga kundnätverk”. Allmänt tillförlitliga anspråk kräver långvarig regression, oberoende verklig nätverksreferens, hotmodell och tydligt avgränsad stödomfattning.

**Starkaste korrekta omdöme efter grön fullständig CI:** ”YadiLab har verifierad kvalitet för explicit dokumenterade funktioner och testfall på specificerad Linux-/Chromiummiljö, med öppet redovisade begränsningar och kvarvarande revisionspunkter.”