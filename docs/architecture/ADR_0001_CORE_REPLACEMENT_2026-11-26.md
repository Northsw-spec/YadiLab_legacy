# ADR-0001 – Selektiv ombyggnad av nätverkssimuleringskärnan

**HISTORISKT, ERSATT VÄGVAL:** [ADR-0002](ADR_0002_FRESH_ENGINE_2026-11-26.md) har tolkningsföreträde och byter selektiv gammal nätverkskodåteranvändning mot en självständig ny motor. För behållbara produktdelar och historiskt källunderlag är detta ADR fortfarande relevant. Ingen gammal runtime importeras i ny engine.


**ABSOLUT FUNKTIONALITETSMÅL:** [PT-FULL-001](../FULL_PACKET_TRACER_PARITY_CONTRACT.md) kräver ALL Packet Tracer-funktionalitet och alla protokoll, inte bara en bättre DHCP/ICMP-routermodell. Detta ADR väljer **ny DES-kärna + bevarad produkt**, inte ett mindre slutmål. S1-POC0/POC1 är endast teknikriskreducering; kommande S2–S12 får inte godkännas förrän enheter, kommandomodeller, IoT/OT, Activity Wizard, multiuser, filformat och API/extensionflöden också är verifierade. Endast Linux/nya accessibility-/keyboard-krav är explicit undantagna.


**Datum:** 2026-11-26. **Status:** BESLUTAT ARKITEKTURVÄGVAL; dokumentations-PR #180, inte bevis för implementerad DES och inte MERGED före Required CI. **Granskad kodbas:** [main 7dbe2285cde7ea87c08afce1c58d36cd0f5697e7](https://github.com/Northsw-spec/YadiLab/tree/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7). Underordnad [enda aktiva masterplanen](../REMEDIATION_PLAN_2026-11-26.md).

## Beslut – vilket av de tre vägvalen är bäst?

**VÄLJ C: behåll YadiLabs projekt, produktgränssnitt, import, dataintegritet, codecs som kan verifieras och regressionstester; bygg däremot en NY in-process diskret händelsekärna och ERSÄTT stegvis synkron exekvering i gamla protokollmotorer.** Slutprodukten ska ha EN auktoritativ motor, EN scenario-tidslinje och EN per-device runtime-state. Kod från dagens motor får pensioneras när dess nya implementering bevisats standardkorrekt.

**AVVISA A – kasta hela kodbasen:** kräver att användarens import/proveniens, atomära Save/Open, SHA-256-konfliktskydd, HTML/JS/SVG/ELK, Builder, pedagogik, Chromium/X11, säkerhetsgräns och stora testsvit återskapas. Inget i dessa delar hindrar i sig en ny diskret händelsemotor.

**AVVISA B – bara lägga en scheduler runt nuvarande synkrona protokollanrop:** ett enskilt event som levererar ett helt frame genom alla switchar, kör samtliga ARP Request/Reply eller går igenom upp till 32 routerhopp är INTE en korrekt eventdriven simulering; mellanliggande packets, timers, portstate och konvergens kan inte påverka pågående överföring.

## Våg 1 – verifierad kod-/testinventering

Git-trädet innehåller **219 filer**, varav **34 network_core**, **100 tests** och **27 web**; nätverks-backend är cirka **479 kB**, testfiler cirka **1,55 MB**. Web innehåller cirka 5,37 MB, men omkring 4,90 MB är paketerad ELK worker. Detta är filstorlek, inte arbetstidsmätning eller kodtäckningsstatistik.

[PR #179 funktionell CI](https://github.com/Northsw-spec/YadiLab/actions/runs/45878863040) visade **839 Python-tester, 55 JavaScript-tester**, verklig Chromium/Save/Open och X11 samt ELK-kontroller PASS på dåvarande exakta PR-HEAD. [Arkitekturcheck](https://github.com/Northsw-spec/YadiLab/actions/runs/45878863045) visade 20 godkända arkitekturtest med negativa fall. I ett direkt granskat urval om 16 testfiler fanns 226 testmetoder inklusive explicit RFC-/IEEE-referens, motexempel för VLAN och kablar samt processkonkurrens för lagring. Detta styrker befintlig regressionstillgång, **inte full RFC-konformans**.

## Våg 2 – vad måste konstrueras om?

- [EthernetFabric.inject()](https://github.com/Northsw-spec/YadiLab/blob/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7/network_core/ethernet.py) utför hela L2-forwarding via intern deque/while innan det återkommer. Byt exekvering mot separat TX-start, länk, RX, FDB-beslut och nästa event; bibehåll observerade korrekta VLAN-/portregler.
- [ArpSession.resolve()](https://github.com/Northsw-spec/YadiLab/blob/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7/network_core/arp.py) skickar Request, finner responder och skickar Reply i ett synkront anrop. Byt till ARP-state, köade frame, tidsgränser och RX-beroende respons.
- [IPv4Trace.send()](https://github.com/Northsw-spec/YadiLab/blob/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7/network_core/ipv4.py) loopar ARP/forwarding genom upp till 32 routerhopp i ett anrop. Byt till lokala per-node IP-beslut, explicit packet-id och kausal TX/RX-kedja.
- [DhcpSession.run()](https://github.com/Northsw-spec/YadiLab/blob/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7/network_core/dhcp.py) genomför DORA stegvis men synkront, med egen EthernetFabric. [DhcpLabSession](https://github.com/Northsw-spec/YadiLab/blob/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7/network_core/dhcp_registry.py) har egen manuellt avancerad clock_seconds. Byt ut separata klockor/timers och isolerade DHCP-FDB mot en gemensam eventkö och runtime-state.
- [LabHTTPServer](https://github.com/Northsw-spec/YadiLab/blob/7dbe2285cde7ea87c08afce1c58d36cd0f5697e7/network_core/server.py) håller separata simulation-, DHCP- och två investigation-register. Slutmålet är en canonical simulation-session med versionsbundna kompatibilitetsadapters. Inga två parallellt aktiva engines i samma användarsession.

## Våg 3 – exakt återanvändningsmatris

| Källfamilj | Beslut | Avgränsning |
|---|---|---|
| storage.py och json_boundary.py | BEHÅLL | Atomärt sparande, OS-lock, originalbytes/JSON, SHA-256 och konfliktkontroll |
| model.py | BEHÅLL EN final validator, NYA versionssatta schemafunktioner | Äldre 1.0–1.4 måste läsas utan tyst databortfall; explicit schema-/migreringstest för nya deviceprofiler |
| import-plan, CSV/XLSX/ODS, källproveniens | BEHÅLL och modulera vid konkreta behov | Ingen automatisk inferens eller osynlig koppling till simulatorns klocka |
| HTTP auth, server, API-kontrakt | BEHÅLL, ersätt active session owner bakom adapter | HTTP-funktionskontrakt och säkerhetsgränser är värda att skydda |
| web Builder, SVG, ELK, lektioner och tester | BEHÅLL och bygg vidare | Reell produkt-/utbildningsfunktion och omfattande regressioner |
| Ethernet/ARP/IPv4/ICMP/DHCP bytes-codecs | ÅTERANVÄND om standardkorrekta; BYT där de är för snäva | Tester ska visa riktig header och negativa cases, inte bevara fel |
| EthernetFabric.inject, ArpSession.resolve, IPv4Trace.send, DhcpSession.run | ERSÄTT EXEKVERING | Synkron bulk-forwarding har fel tids-/interleavingsemantik |
| ConnectedRoutingTable | ÅTERANVÄND LPM-principen; NY gemensam RIB/FIB | Nuvarande tabell är snapshot av statiska/connected routes, inte dynamisk router-state |
| Session/clock/registries | ERSÄTT successivt | En simuleringsklocka och delad scenario-state, inte fyra autonoma labbmotorer |
| Hela regression-/CI- och architecture-guard-kedjan | BEHÅLL och UTÖKA | Legacy-karakterisering + oberoende standardorakel måste vara separata bevisnivåer |

**Viktiga verifierade codec-hinder:** ethernet_frame.py avvisar multicastdestinationer, annan PCP/DEI och flera VLAN-taggar; IPv4Datagram i ipv4_packet.py tillåter bara IPv4-protokollnummer **1 och 253**, inte generell TCP=6, UDP=17, OSPF=89, fragmentering eller options. Därför kan inte befintliga codecs lovas vara oförändrade ens om deras nuvarande tester är korrekta.

## Våg 4 – etablerad arkitektur och riskhantering

[ns-3 Events](https://www2.nsnam.org/docs/release/3.45/manual/html/events.html), [Node/NetDevices](https://www2.nsnam.org/docs/models/html/network-overview.html) och [Point-to-point channel](https://www2.nsnam.org/docs/models/html/point-to-point.html) bekräftar betydelsen av eventordning, device-/länk-/protokollseparation, TX-köer och bitrate/delay. [OMNeT++](https://doc.omnetpp.org/manual/ch-introduction) visar modulär, meddelandebaserad simulatordesign. [Martin Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html) och [AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) motiverar en stegvis ersättningsstrategi över en stor redan fungerande produkt; detta är INTE ett uppmätt procenttal för YadiLab.

## Ändrad genomförandeordning för lägsta onödiga omarbete

1. Slutför S0/PR #180 med Required CI och säker squash. Ändra inte nuvarande produktexekvering genom docs-PR.
2. **S1-POC0 i en liten isolerad PR:** ny scheduler med integer virtual-time, monotonic event id, seedad PRNG, cancel, eventbudget, overflow-/zero-time-skydd och reproducerbar trace över två självständiga processer. Inga nya användar-API, ingen parallell aktiv motor.
3. **S1-POC1 i en separat liten PR:** korrekt sekvenserad host → switch → host TX/RX samt ARP Request/Reply som flera separata events i en isolerad test-fixtur. Negativt port-/länk-/VLAN-fel och interleaving: länkdown mellan TX och RX ändrar relevant effekt. Gamla bulk-anrop får INTE vara en enda scheduler-handler.
4. **Tydlig go/no-go före produktionscutover:** verifiera avgränsade integration seams, deterministiskt beteende, oberoende RFC-/IEEE-orakel, maximal event-/minneskostnad, ingen duplicerad aktiv state, ändrings-/session-/Save/Open-integritet och Required CI. Vid hinder justera DES-design; kasta inte hela produkten utan data som faktiskt motiverar det.
5. **Migrera vertikalt med kompatibilitetsadapters:** byt EN aktiv L2, ARP, IPv4/ICMP och DHCP-väg per granskad PR. Old engine får finnas som **isolerad test-referens**, inte parallellt aktiv i samma scenario. Strikta befintliga API-/schema- och tidskontrakt bevaras eller explicit versioneras; gammal synkron motor tas bort när v2 täcker den.
6. A3/A4 frontend-/importmodularisering görs i de gränser där den faktiskt minskar integrationsrisk, inte som onödigt fullständigt block för scheduler-POC. A5:s oberoende protokollorakel och A7:s sanningsmatris är viktiga för produktionscutover. Full native expansion S2–S9 väntar tills EN motor verkligen beräknar L2/ARP/IPv4/ICMP/DHCP tillsammans.

**Beslutskommentar:** Tid för ren rewrite jämfört med hybrid är INTE empiriskt uppmätt. Vi har granskat aktuell källkod och tidigare CI, men **ingen ny DES-POC körts och lokal klon var inte tillgänglig i granskningens miljö**. Ingen procentsats, tidsbudget eller ovillkorlig garanti om CodeX-effektivitet är verifierad. Ändå är vägvalet välgrundat av att dataintegritet/UI/tester är frikopplingsbara tillgångar medan den gamla synkrona exekveringen är explicit identifierad som ett separat designhinder. Om en verklig POC motsäger gränserna krävs ett evidensbaserat nytt ADR-beslut.

**Sammanfattning:** Behåll produkten. Nybygg simuleringsexekveringen. Skydda och återanvänd sanningsenliga paket-/datakontrakt. Begränsa övergångsfasen. Ett användarscenario får alltid bara ha EN aktiv nätverksverklighet.
