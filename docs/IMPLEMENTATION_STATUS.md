# Verifierad implementationsstatus och dokumentationsföreträde

**Datum:** 2026-11-24 (ISO)  
**Kontrollerad utgångspunkt:** `main@b1c6fb0323fc93085084128e3ff4382f2b3a9576` efter mergad PR #109.  
**Avsikt:** Motverka att Codex behandlar äldre planer, begränsade delprotokoll, historiska CI-anteckningar eller forskningsförslag som aktuell kod.  
**VIKTIGT:** Detta är en tidsstämplad verifieringsöversikt, **inte** ett alternativ till att läsa aktuell HEAD, faktisk kod och aktuella CI-resultat. Den får inte uppdateras med antaganden, enbart grön CI, eller slutsatser från ett statiskt dokument.

## 1. Företrädesordning och korrekt tolkning

1. **Senaste uttryckliga användarbeslut och ändringens tydliga scope.** Beslut om framtida mål är inte bevis på att de är implementerade.
2. **`AGENTS.md` och `docs/MASTERPROMPT.md`:** övergripande utvecklingskontrakt, Linux-only, ändringskontroll och sanningstyper.
3. **Aktuell källkod, tekniska kontrakt och exakta testresultat** för påståenden om vad som faktiskt fungerar. Om fakta/kontrakt motsäger varandra: avbryt riskfylld ändring och utred; välj inte en passande formulering.
4. **`docs/IMPORT_SOURCE_CONTRACT.md`** vid extern dokumentimport och fullständighetskrav; **`docs/QUALITY_IMPROVEMENT_PLAN.md`** är enda aktiva kvalitetsroadmap.
5. **`docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md`** normerar undervisningens innehåll, inte nya protokoll, importmoduler, API:er eller utvecklingsetapper.
6. **Äldre dokument och PR-rapporter** är historiska inom det uttryckligen daterade omfånget. Gamla ”nästa PR”, ”inte implementerat”, ”CI PENDING” eller ”ska byggas” får aldrig förvandlas till dagens arbetsorder utan verifiering.

**Kodstatus ≠ teststatus ≠ CI-status ≠ formaliserad etappacceptans.** Skriv separata rader och exakta SHA när det spelar roll.

## 2. Begränsad funktionsinventering vid baslinjen

| Område | Belagd/avgränsad funktion | Bevis att kontrollera före ny kod | Får INTE påstås |
|---|---|---|---|
| Kanonisk nätverksmodell | Explicita noder, gränssnitt, kablar, versionerat schema och strikt validering | `network_core/model.py`, `tests/test_model.py` | Kablar och gateways härleds automatiskt |
| Projekt och Save/Open | Explicit lokal Save, SHA-/konfliktkontroll, projektfiler med presentations-X/Y | `network_core/storage.py`, `docs/ARCHITECTURE.md`, storage/browser-tester | All fysisk datalagring eller strömbortfall är bevisat felfri |
| Dokumentation | Strikt och koordinatfri CSV/XLSX/ODS, samt separat explicit källgranskning/mappning | `network_core/csv_import.py`, `network_core/spreadsheet_schema.py`, `docs/SPREADSHEET_V13.md`, PR #94 | Att varje godtyckligt kunddokument kan tolkas; full fail-closed projekttillämpning är generellt godkänd |
| Diagram | Automatisk initial ELK-layout efter godkänd dokumentimport; sparat projekt behåller X/Y; SVG/Worker och manuell Preview/Apply för omplacering | `docs/ELK_LAYOUT_CONTRACT.md`, PR #94–#96 och ELK browser-tester | ELK skapar nätverksfakta eller måste utvecklas igen som 06A–C |
| Ethernet/ARP/VLAN | Begränsad MAC-inlärning, 802.1Q/access/trunk och ARP via samma simuleringsmotor | `network_core/ethernet.py`, `network_core/arp.py`, `docs/VLAN.md` | STP, LACP, QinQ och alla NIC-varianter fungerar |
| IPv4/ICMP | Connected/static routes, explicit next-hop, TTL, begränsade ICMP Echo och vissa RFC 792-routerfel | `network_core/routing.py`, `network_core/ipv4.py`, `docs/ICMP_ECHO.md`, `docs/ICMP_ROUTER_ERRORS.md` | Routetabellval eller en ritad länk är verifierad verklig reachability |
| DHCPv4 | Avgränsade DORA- och processlokala sessions-/renewal-/tids-/felövningsfunktioner, utan permanenta klientleases | `docs/DHCP_DORA.md` och relevanta kod-/browser-tester | Komplett DHCP-relay, verklig klients nätverkskonfiguration eller alla RFC 2131-varianter |
| Felsökning | Verifierbara baseline/fel/återställningsjämförelser och dolda diagnostikfall i befintlig modell | `network_core/troubleshooting.py`, `docs/ICMP_INVESTIGATION.md`, `docs/TROUBLESHOOTING.md` | Automatisk diagnos av verkliga kundnäts felorsak |
| Ny undervisningsmodell | Niorubriksmallen Om/Då/hypotes etc. är **beslutad design** | `docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md` | Att en ny Incidentverkstad redan finns i UI |
| OSPF, BGP, STP, SNMP, generella ACL/NAT, avancerade stateful brandväggar | **Pedagogiska ämnen; ingen av dessa generella motorer är verifierad som native implementation** | Aktuell `network_core/`, explicita protokollkontrakt; separat dokumentationsgranskning | Att en kursartikel eller ett statiskt kommando innebär ett körbart protokollstöd |
| Externa verktyg | **Endast statiska undervisningsreferenser**, med manuellt fristående labb vid behov | Pedagogikplanen | Batfish, SuzieQ, Netshot, NetXMS, Wireshark, FRRouting, containerlab som installerad, anropad eller integrerad motor |
| Plattform | Linuxdistributioner är enda avsedda målplattform | `AGENTS.md` och QUALITY-009 | Windows/macOS-stöd eller automatisk kompatibilitet med otestade Linuxdistributioner |
| Lokalt medpackat tredjepartspaket | `elkjs 0.13.0` finns lokalt under `web/vendor/` med licens/NOTICE. Ingen extern CDN-installation krävs för runtime | `web/vendor/NOTICE.md`, `docs/ELK_LAYOUT_CONTRACT.md` | Att runtime överhuvudtaget saknar tredjepartskod |

**Översikten är ingen oberoende generell testcertifiering.** Där exakt stödomfattning saknas i tabellen ska den härledas från aktuell kod och negativa tester; markera annars `NOT_VERIFIED`.

## 3. Historiskt verifierad PR- och QUALITY-status

| Område | Konstaterat historiskt läge 2026-11-24 | Inte därmed bevisat |
|---|---|---|
| ELK-06A/06B/06C | PR #94/#95/#96 mergade 2026-11-22 | Att alla framtida dokument/layout-/resursfall fungerar |
| QUALITY-002 | Required check konfigurerad; tvingande enforcement **NOT_VERIFIED** trots observerad blocked negativ PR #99 | Att samtliga branchskyddsinställningar har godkänts oberoende |
| QUALITY-003 | **ACCEPTED för uttryckligen referenstestat supported subset**, se verifieringsrapport och main-CI | Generell RFC-/IEEE-konformitet eller alla protokoll |
| QUALITY-004 | 4A skrivskyddad revision PR #106, final PR HEAD `b8ab356b21be861a2215029b74deb3628b2f31d9`, två `unit-tests` SUCCESS och merge. Endast **4A** är rapporterad/granskad | Att hela QUALITY-004 automatiskt är ACCEPTED |
| QUALITY-005 | Smala deltester för Save/fsync (#107), sena sessionssvar (#108) och parallell lokal HTTP (#109) mergade; två `unit-tests` SUCCESS på exakt PR HEAD för respektive | Att all concurrency, parserresursutarmning eller fysisk strömavbrottssäkerhet verifierats |
| QUALITY-006–011 | Ej automatiskt accepterade genom tidigare framsteg | Att etappnamn är byggorder eller testbevis |
| Dokumentations-PR #110 | Föreslagna pedagogiska styrkontrakt och statuskorrigeringar; verifiera PR:s **nya final HEAD** och både obligatoriska kontroller | Att textändringar redan är på `main` eller att ny pedagogisk UI-funktion existerar |

## 4. Om ett äldre dokument motsäger statusöversikten

- Läs dokumentets **datum, scope och status på den commit där uppgiften verifierades**.
- Kontrollera om en senare PR faktiskt ändrat funktionen; använd **kod + exakta tester**, inte bara en PR-titel.
- Om det är en historisk rapport: behåll ursprungliga mätdata men markera den inaktuella framtidsformen som **historisk** och länka till aktuellt dokument.
- Om det är normerande: korrigera faktapåståendet och verifiera regressioner. Radera aldrig gamla bevis för att få ny text att se konsekvent ut.
- Om kod inte kan avgöra: använd **NOT_VERIFIED**; hitta inte på en implementation, ett API, en payload, ett protokoll, ett referensvärde eller en confidence-procent.
- Upprepa aldrig färdiga ELK-06A–C, importer 4A–4D eller protokolletapper endast för att ett äldre dokument säger ”nästa steg”.
- Dokumentation får aldrig kringgå CI-/mergegrindarna. **Namnkontraktets justerade gräns 2026-11-24:** Markdown-prosa (inklusive `AGENTS.md`, `README.md`, `docs/*.md`) får använda projektnamnet `YadiLab`, utan att detta ändrar det deklarerade UI-namnet. `tests/test_naming_contract.py` förbjuder fortfarande gamla/hårdkodade produktnamn i icke-Markdown-kod/fixturer och i filvägar, samt ytterligare `APP_NAME`-deklarationer. Det tekniska projektformatet `.yadilab` är ett uttryckligt kompatibilitetsundantag. Namn i dokumentation är inte underlag för nya klass-/funktionsnamn.

## 4A. IPv4-scopegrind – verifierad i begränsat omfång genom PR #114

Ytterligare explicit specialadressvalidering enligt RFC 1122, RFC 3927 och IANA har genomförts i **PR #114**, med sex nya oberoende positiva/negativa tester. Båda obligatoriska `unit-tests` på exakt slutlig PR-HEAD `7e7179a868a9ca97ae03e941fee4917a65dd99e8` var **SUCCESS** före squash-merge till `main@50772ef42f5284c88ee65aca1d6d128829d8b5d7`. Motorn avvisar trådburen simulering med 127/8 och 0/8 och förbjuder routertransit för 169.254/16 utan att hindra direkt Ethernet-länk-lokal trafik. Se [IPV4_FORWARDING.md](IPV4_FORWARDING.md) och [PROTOCOL_REFERENCE_MATRIX.md](PROTOCOL_REFERENCE_MATRIX.md). **ACCEPTED endast för detta uttryckligt testade delomfång**, inte allmän IPv4-/RFC-konformitet. Senare `main`-CI kräver separat verifiering.

## 4B. Säkra CI- och licensgränser (2026-11-24)

**Verifierad CI-deländring:** PR #116 låste alla externa Actions i fem workflows till fullständiga commit-SHA, satte minsta explicita tokenbehörighet, avstängd checkout-credentialpersistens och test av lokal ELK-worker mot dokumenterad SHA-256. Båda obligatoriska `unit-tests` på exakt PR-HEAD `6c833ad9aaa3fb4b0bbbb69a973172c838975359` rapporterade **SUCCESS**; squash-commit på `main`: `3d6ff1d1a71b1733e8121606fc47aedd5d42d09c`. **ACCEPTED endast för de specificerade kontrollerna**, inte fullständig dependency-/supply-chain-certifiering.

**Licensbeslut är BLOCKED:** GitHub rapporterade `license=null` och repo-roten har ingen `LICENSE`; README säger att licens inte valts. Vendorns ELK-licens gäller **inte** automatiskt den egna Python-/JavaScript-koden. Se [issue #115](https://github.com/Northsw-spec/YadiLab/issues/115). En publicerad källa är inte automatiskt OSI-licensierad; välj aldrig licens eller upphovsrättsligt ansvar utan rättighetsinnehavarens uttryckliga godkännande.

## 4C. Källtroget JSON-uppladdningsflöde och offline-API – verifierad delmängd PR #119

**Fynd 2026-11-24:** `web/features/projects/transfer.js` läste originalfil genom `JSON.parse` före anropet till `/api/validate`; `web/features/projects/import-review.js` gjorde motsvarande för uppladdade mappningsprofiler och originalkällpaket, och använde delvis `File.text()` som kan ersätta ogiltiga UTF-8-bytes. Det kunde normalisera bort motstridiga JSON-nycklar **före** den strikta servervalideraren från PR #111. Den nya avgränsade kod-PR:en skickar oförändrade uppladdade bytes via ett lokalt `/api/validate` respektive läsande `/api/json/strict` och begränsar `web/services/api.js` till relativa `/api/...`-vägar.

**Status:** **ACCEPTED inom specificerat stödomfång**. PR #119:s båda obligatoriska `unit-tests` var SUCCESS på final PR HEAD `81337e72a57493a14d94c792f3a93ed8c4988586` och squash-mergades till `main@f6066038ed07fe6f087fb4d654a7d003d7b60b91`. Specifika tester: 4 Node och 5 verkliga HTTP-regressioner plus Chromium-profiler, import, X11 och ELK. Senare `main`-CI är separat evidens. Inget nytt nätverksimportschema, inga externa verktygsintegrationer, ingen ändrad projektmodell och ingen automatisk Save. Se [SOURCE_INTEGRITY_AUDIT_2026-11-24.md](SOURCE_INTEGRITY_AUDIT_2026-11-24.md) och negativa HTTP-/Node-tester.

## 4D. ARP Ethernetadressgräns – testad, tillämpad på main

**Verifierat kodfynd:** Den separata ARP-modulen accepterade adresser ur 127/8, 0/8 och reserverade 240/4 som vanliga Ethernet-ARP-källor/mål, även efter IPv4-dataplanets PR #114. För att förhindra falskt ARP-`RESOLVED` läggs ett snävt ARP-protokollvillkor och fyra positiva/negativa tester till. Befintligt sparat projekt ska fortsatt kunna dokumentera ogiltig adresskonfiguration; DHCP-bootsrapporter med `0.0.0.0` använder separat definierad codec och ska inte påverkas. Se [ARP.md](ARP.md), [PROTOCOL_REFERENCE_MATRIX.md](PROTOCOL_REFERENCE_MATRIX.md) och [issue #120](https://github.com/Northsw-spec/YadiLab/issues/120).

**Status:** **ACCEPTED inom explicit testad ARP-delmodell.** PR #121 HEAD `dbb90e131df730d6f9aeb3d05f4d4337496aa29d` hade två `unit-tests` med SUCCESS. Git-trädet `1430cb1ec783b75819f8aede419c4cd549ebe4f5` är identiskt mellan denna HEAD och `main@7e8c423c8823fc3b40dc89b591160d5bb52aec13`. **GitHub-avvikelse:** merge-anropets svar fick timeout efter att main uppdaterats; PR #121 stängdes manuellt och står som `merged=false`, vilket dokumenteras i PR-kommentaren. Issue #120 stängdes separat. Detta är inte generell ARP-/RFC-verifiering; senare main-CI och huvudgrenens governance ska bedömas separat.

## 5. Slutlig gräns för försäkran

**Riskbaserad källkodsrevision, 2026-11-24:** [SOURCE_INTEGRITY_AUDIT_2026-11-24.md](SOURCE_INTEGRITY_AUDIT_2026-11-24.md) redovisar den avgränsade kontrollen av HTTP, JSON, import, lagring, protokollsteg och CI samt öppna fynd. JSON-avvikelserna åtgärdades i PR #111 med båda obligatoriska `unit-tests` **SUCCESS** på final PR-HEAD `9a5b9b0b456185d8ebdb9271dcbfaf1bcaaebeee`, squash-mergad till `main@2c79bb75ec10e80441f6ccff8a349422d23537ac`. Det är ett begränsat verifierat ingångskontrakt; senare `main`-CI och alternativa parseranrop kräver separata kontroller. Lär ut dess uttryckliga ICMP-reply-TTL-begränsning som en modellförenkling, inte som verkligt nätverksfaktum. Rapportens kvarstående lokala API-/interoperabilitetsrisker är ingen automatisk kodorder.

Det går att kontrollera konkreta påståenden och upptäcka kända motsägelser. **Ingen engångsgranskning kan garantera total avsaknad av oupptäckta buggar, felaktiga dokumentationspåståenden eller framtida språkmodellsfel.** För att hindra att de blir produktbeteende krävs scope-begränsning, källbevis, negativa regressioner, faktisk driftverifiering, exakt CI-HEAD och förbud mot att kompensera saknade fakta med gissningar.

**Denna fil ändrar inte någon motor, datamodell, nätverksimport, CI-policy eller användarens lagrade projekt.**