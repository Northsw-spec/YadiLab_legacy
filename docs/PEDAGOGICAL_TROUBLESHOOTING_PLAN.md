# YadiLab – pedagogisk felsökningsarkitektur: evidens, orsak och lärande

**Nytt produktbeslut 2026-11-26:** P0–P7 förblir historiskt CLOSED och dess nio rubriker är ett kvalitetskontrakt, men [enda aktiva masterplanen A0–A10 + S0–S12](REMEDIATION_PLAN_2026-11-26.md) har nu uttryckligen beställt ett Packet Tracer-plus-simuleringsuppdrag. Se [MASTERPROMPT](MASTERPROMPT.md), [protokollmatrisen](PROTOCOL_COVERAGE_MATRIX.md), [motorarkitekturen](architecture/DETERMINISTIC_ENGINE_CONTRACT.md) och [Codex-policyn](CODEX_EXECUTION_POLICY.md). Historiska ord om att inga nya protokoll är beställda gäller inte längre för S-korten.


**Datum:** 2026-11-24 (ISO)  
**Operativ agentprocess:** [CODEX_EXECUTION_POLICY.md](CODEX_EXECUTION_POLICY.md) gäller allt framtida Codex-arbete. Detta dokument är historiskt, inte en ny uppgiftskö; undvik passiv Actions-väntan och återstart av P0–P7.

**Beslut 2026-11-26:** P0–P7-programmet är **formellt avslutat genom uttryckligt användarbeslut**. Dokumentet bevaras som historisk genomförandeplan och fortsatt bindande pedagogiskt kvalitetskontrakt; **ingen P0–P7-etapp eller P8 är aktiv/beslutad**. Separat därefter är [REMEDIATION_PLAN_2026-11-26.md](REMEDIATION_PLAN_2026-11-26.md) uttryckligen godkänd som en del av den **enda aktiva huvudplanen A0–A10 + S0–S12**.  
**Status:** P0–P7 **CLOSED (2026-11-26)**. Den formella avslutningen är ett projektbeslut, inte bevis för att samtliga tidigare idéer implementerats eller att YadiLab är felfritt. Den sammanhållna nya undervisningsarbetsytan ska fortfarande behandlas som **PLANNED / NOT_VERIFIED** där faktiskt kod- och teststöd saknas. Befintliga funktioner fastställs endast från aktuell kod och tester. Native utbyggnad inom den senare godkända S0–S12-planen är nu beställd, men får inte beskrivas som redan implementerad. Ytterligare utbyggnad utanför detta scope kräver nytt beslut.  
**Historisk granskad bas:** `main@b1c6fb0323fc93085084128e3ff4382f2b3a9576`. Läs om aktuell HEAD/CI före varje ändring.  
**Plattform:** Linuxdistributioner endast. Windows och macOS är UNSUPPORTED.

> **LÄS FÖRST – avslutad roadmap.** P0–P7 beskriver ett avslutat utvecklingsprogram och får inte längre användas för att automatiskt välja nästa uppgift. Aktuella åtgärdskort och deras status finns **endast** i [den aktiva reparationsplanen A0–A10](REMEDIATION_PLAN_2026-11-26.md). Inget nytt steg, protokoll, API, schema, datalager, OS-stöd, extern integration eller stor UI-ombyggnad är beslutat. Operativa regler: `AGENTS.md`; produktkontrakt: `docs/MASTERPROMPT.md`; importgräns: `docs/IMPORT_SOURCE_CONTRACT.md`. Vid konflikt gäller senaste uttryckliga användarbeslut och verifierad kod/test på aktuell HEAD.

## 1. Produktmål och orubbliga avgränsningar

**Mål:** En blivande IT-konsult ska kunna se och förstå nätverksfel, tillstånd och orsakskedjor: studera dokumenterad topologi; observera eller simulera ett symptom; välja rimlig diagnostik; tolka svar; jämföra hypoteser; pröva ett motbevisande test; föreslå en avgränsad åtgärd; verifiera återställning; och dokumentera slutsatsen. Undervisningen ska överföra kunskapen mellan olika tillverkare och utrustningstyper.

**Kvalitetsmål för framtida undervisning:** Applikationen ska kunna förklara korrekt vad en given observation eller en stödd simulerad mekanism innebär *inom sina uttryckliga förutsättningar*. Applikationen lovar inte automatisk förståelse av alla kundnätverk, att varje faktisk felorsak går att hitta, att alla protokoll simuleras eller att någon blir senior genom enbart appanvändning. Påståenden om ”världens bästa” får inte användas som verifierad produktstatus utan en oberoende och reproducerbar jämförelse.

**Beslut om externa program – INGEN integration:** SuzieQ, Batfish, Netshot, NetXMS, Wireshark, FRRouting, containerlab, Linux CLI-verktyg m.fl. är **fristående verktyg för undervisning och separat praktiskt arbete**. Applikationen får förklara när de används, visa expertgranskade *statiska exempel*, förklara kommandon och utdata samt hänvisa till officiell dokumentation. Applikationen får **inte inom denna arkitektur** installera, paketera, köra, anropa, automatiskt importera från, skanna med, läsa live-utdata från eller orkestrera dessa verktyg. Inga SDK:er, API-adaptrar, containermotorer, SSH-/SNMP-klienter, automatiska CLI-anrop, PCAP-insamlare, externa NMS-/analysmotorer, forks eller kopierad källkod införs. Ett nytt, annorlunda framtida användarbeslut skulle kräva eget kontrakt; detta dokument är inte ett sådant mandat.

**Bevara befintlig funktionalitet:** En kanonisk nätverksmodell och en befintlig IPv4/ARP/Ethernet/VLAN/ICMP/DHCP-motor med redan stödda funktioner. Bevara dokumentimport, källproveniens, uttryckliga fysiska portändpunkter, ELK/SVG/Worker, Builder, simuleringssessioner, dolda felövningar, Save/Open, branchskydd och testsvit. Ingen andra simulering, konkurrerande projektmodell, ny importkedja eller automatisk live-discovery som följd av pedagogikplanen. All lagring kräver befintlig uttrycklig Save.

## 2. De nio rubrikerna – ORDAGRANN, bindande svensk mall

Varje genomarbetad diagnoslektion använder följande rubriker **exakt, inklusive hakparenteser och skiljetecken**:

1. **Om [observerat]:**
2. **Då [vad det faktiskt betyder]:**
3. **Möjliga orsaker [inte fastställda/hypoteser]:**
4. **Vad detta inte bevisar:**
5. **Nästa diagnostiska steg:**
6. **Förväntat resultat och tolkning:**
7. **Åtgärd [först efter fastställd orsak]:**
8. **Verifiering [fungerar det nu?]:**
9. **Beviskälla och begränsningar:**

**UI-regel:** Visa de tre första för nybörjaren, men låt resterande sex öppnas stegvis. Ingen skyldighet att visa nio stora kort samtidigt. Samma sanningskrav gäller i guidade, halvstyrda och självständiga övningar. Rubriksträngarna är kurs-/UI-text, **inte** ett beslut att lägga nio fält i projektfilen eller skapa en ny JSON-parser.

### 2.1 Innehållskontrakt per rubrik

| Rubrik | Ska alltid kunna besvara | Förbjudet |
|---|---|---|
| Om | Exakt vilket symptom/tillstånd syns; av vilken källa, tid, enhet, port, riktning och scope? | Falskt ”live” på statiska/beräknade data |
| Då | Vilken *nödvändig* teknisk slutsats följer av observationen, givet angivna förutsättningar? | Smuggla in en antagen grundorsak |
| Möjliga orsaker | Minst relevanta, konkurrerande hypoteser; alla tydligt märkta som hypoteser | Slå fast fel kabel/VLAN/OSPF-policy utan skiljande bevis |
| Vad detta inte bevisar | Vilka närliggande slutsatser stöds **inte** av datat? | Förtiga exempelvis att route lookup inte är paketleverans |
| Nästa diagnostiska steg | Ett minst möjligt, säkert test som kan skilja två hypoteser åt; varför just det? | Slumpmässiga kommandon som saknar diagnostisk fråga |
| Förväntat resultat och tolkning | Vad betyder såväl positivt som negativt eller motsägande testutfall? | Förutbestämd ”sanning” oberoende av mätresultat |
| Åtgärd | Bara en åtgärd som kan härledas till fastställd modellorsak; annars ”inte fastställd” | Automatiskt ändra produktionsnät eller lova framgång |
| Verifiering | Hur jämförs före/fel/efter och begäran/svar i relevant scope? | Godkänna bara en synlig kabel eller en enkel rutttabellmatch |
| Beviskälla | RFC/standard/dokument/test/PCAP/simulering, tidpunkt, avgränsning, verifieringsnivå | Påhittade terminalutdata eller påstådd extern körning |

**Viktig metodregel:** Studenten ska också få frågan *”Vilken observation skulle tala emot din hypotes?”*. Diagnostik är uteslutning och prövning, inte en lista med bekräftande symptom.

### 2.2 Direkt bevis kontra hypotes kontra verifierad felorsak

- **Direkt observation:** Exempelvis `operational state: down` i ett *verifierat, tidsstämplat* verktygsresultat. Det bevisar det rapporterade tillståndet i mätningens scope, inte kabelorsaken.
- **Protokolldefinierat ”Då”:** Exempelvis OSPF `Init` har en specifik definierad protokollbetydelse i RFC 2328. Det bevisar inte varför tillståndet uppstod.
- **Modellberäknat:** Resultat från applikationens uttryckligen stödda simuleringsmotor, med projektets identiteter och faktiska paketspår. Inte observation av verkligt kundnät.
- **Hypotes:** En möjlig orsak som ännu inte särskilts från alternativen.
- **Fastställd orsak inom övningen:** Bevisad endast när en validerad isolerad feländring ger ett relevant fel, originalet fungerar och oberoende återställning fungerar enligt den befintliga motorn. Denna beviskedja får inte överföras automatiskt till ett verkligt kundnätverk.
- **Verklig verifiering:** Kräver separata, tillåtna och faktiskt utförda observationer på det aktuella nätverket. Pedagogikexempel är aldrig sådan verifiering.

Applikationens redan beslutade sanningsklasser enligt `MASTERPROMPT.md` gäller där de används: `DOCUMENTED`, `CONFIGURED`, `SIMULATED`, `UNKNOWN`, `UNSUPPORTED` och `NOT_VERIFIED`. Skapa inga nya programstatusar eller API-fält enbart för pedagogiktext. ”Observerat”, ”hypotes” och ”motbevisat” kan vara pedagogiska beskrivningar, inte automatiskt schematyper.

### 2.3 Konfidensprocent

**Förbjudet:** godtyckliga `85 %`, `95 %` eller andra numeriska sannolikheter för felorsaker eller protokolltolkningar. Procent från LLM-utfall, generiska internetsiffror eller enbart antal symptom är inte kalibrerade.

**Tillåtet:** studentens **egna självskattade säkerhet i procent**, tydligt märkt ”Elevens självskattning – inte applikationens sannolikhet”. Eventuella framtida statistiskt beräknade felorsakssannolikheter kräver särskilt explicit godkännande, uppmätt representativt underlag, definierad population/beroenden, metod och **extern kalibrering**; denna plan godkänner ingen sådan modell.

När ett villkor är logiskt/protokollmässigt bestämt inom en specificerad kontext: skriv den precisa betydelsen utan en artificiell konfidenssiffra. När fakta saknas: skriv `UNKNOWN` eller `NOT_VERIFIED` och föreslå ett avgränsat test.

## 3. Exakt exempel: OSPF-granne i Init (EXTERNT UNDERVISNINGSEXEMPEL)

**Om [observerat]:**

En router som enligt topologins design ska uppnå full OSPF-adjacency rapporterar grannen i `Init` i ett angivet kommandoresultat/snapshot.

**Då [vad det faktiskt betyder]:**

Routern har tagit emot minst ett OSPF Hello-paket från den rapporterade grannen men ser ännu inte sitt eget Router ID i det mottagna Hello-paketets grannlista. Tvåvägsigenkänning har därmed inte bekräftats av det observerade tillståndet. Detta är en **protokolltolkning**, inte en diagnos av fysisk orsak.

**Möjliga orsaker [inte fastställda/hypoteser]:**

Exempelvis envägsförmedling av Hello-paket, filtrering, felaktiga gränssnitts-/OSPF-inställningar eller ett tillfälligt övergångstillstånd. Vilken orsak som gäller är **inte** fastställd.

**Vad detta inte bevisar:**

Det bevisar inte trasig kabel, att all trafik stoppats, att en viss router är skyldig eller att en statisk route saknas. Ett `2-Way`-tillstånd kan dessutom vara normalt mellan vissa OSPF-grannar på broadcastnät när de inte ska bilda full adjacency; design och nätverkstyp måste vara kända.

**Nästa diagnostiska steg:**

Jämför faktisk OSPF-grannstatus på båda sidor och undersök, i separat tillåtet labb, mottagna Hello-paket samt relevanta interface-/OSPF-konfigurationer. Visa syftet med varje kommando och vilka utfall som skiljer hypoteserna åt.

**Förväntat resultat och tolkning:**

Om ett mottaget Hello saknar den lokala routerns Router ID i grannlistan är tvåvägsigenkänning ännu inte etablerad. Om förväntad adjacency blir `Full` och förblir stabil efter senare observation kan den första avläsningen ha avspeglat ett övergående tillstånd; en äldre snapshot bevisar inte permanenta problem.

**Åtgärd [först efter fastställd orsak]:**

Ingen generell automatisk konfigurationsändring följer av `Init`. Korrigera endast den särskilt styrkta orsaken i ett isolerat labb efter kontroll av sidoeffekter.

**Verifiering [fungerar det nu?]:**

Kontrollera rätt grannstatus för den aktuella nätverkstypen, stabilitet över tid, förväntade rutter och, separat, relevant faktisk eller laboratoriemodellerad trafik.

**Beviskälla och begränsningar:**

RFC 2328, särskilt OSPF Neighbor State Machine och Hello processing: https://www.rfc-editor.org/rfc/rfc2328 . Detta är statiskt pedagogiskt exempel, inte en av applikationen genomförd OSPF-simulering eller live-sampling.

## 4. Den befintliga simuleringsmotorns gränser

**Vid granskad baslinje finns källkod för:** deklarerade noder/portar/kablar, importerade nätverksfakta med validering och proveniens, SVG/ELK-rendering, ARP/Ethernet/MAC-inlärning, explicita VLAN, connected och statiska IPv4-routes, IPv4-forwarding/ICMP Echo och begränsade router-ICMP-fel, DHCPv4 DORA/sessionsfall, kontrollerade feljämförelser samt dolda ICMP- och DHCP-utredningar. **Detta är en kodinventering, inte nytt bevis för generell protokollkorrekthet eller fullständigt stödda implementationer.** Se `network_core/`, `docs/ICMP_INVESTIGATION.md`, `docs/DHCP_DORA.md`, `docs/TROUBLESHOOTING.md`, `tests/test_protocol_reference_vectors.py` och relevanta tester; kontrollera aktuell HEAD.

**Inte tillåtet att utge som native-simulering med detta dokument:** godtyckligt OSPF/BGP, STP, generella ACL eller stateful-brandväggspolicys, NAT, VRF, IPv6, generell TCP/UDP-session, DNS, Wi-Fi, VPN, nätverksskanning, SNMP-övervakning och okända tillverkares exakta CLI-semantik. En fungerande route lookup innebär inte ett lyckat ping; en ritad kabel är inte ett verkligt datapakets transmission; en exporterad konfiguration är inte ett observerat driftstillstånd.

**Kodskydd:** `network_core/model.py` och `validate_project` förblir enda auktoritativa projektvalidering; gamla och aktuella filformat och användar-ID:n bevaras; ingen implicit LLDP-kabel; ingen syntetisk gateway; ingen mapping från en OSPF-inlärd RIB-rad till en statisk route. Projektimportens fail-closed-kontrakt och separata Save gäller även i alla lärflöden.

## 5. Pedagogisk arbetsyta – föreslagen framtida funktion, INTE befintlig status

Ett framtida arbetsflöde kan byggas **ovanpå** existerande Builder/topologi och incidentmotor, utan ny protokollmotor:

1. **Uppdrag:** Incident, mål, avgränsning och vilka uppgifter som kommer från dokumentation kontra modell.
2. **Om:** Student ser symptom och tids-/källkontext; eventuellt en liten granskad CLI-/Wireshark-/SuzieQ-bild märkt `STATISKT EXEMPEL`.
3. **Då:** Efter att studenten själv tolkat observationen visas korrekt, källbunden protokollbetydelse och dess förutsättningar.
4. **Hypoteser:** Studenten väljer bland rimliga alternativ samt anger ett test som kan motbevisa sin första hypotes.
5. **Diagnostik:** Använd redan existerande befintliga appdiagnoser när underliggande mekanism är implementerad. För OSPF/BGP/ACL m.m. visa *endast* externa verktygsanvisningar och granskade statiska data; inga påhittade native-prober.
6. **Paket- och beslutssteg:** Återge bara verkligt beräknade ARP/Ethernet/IPv4/ICMP-transmissioner från applikationens motor, med skilda request/reply och felorsaker. Extern packet capture visas enbart som separat, märkt referensmaterial.
7. **Orsak och test:** Jämför alternativa hypoteser med resultat. Avslöja inte dolt övningsfacit innan studenten undersökt.
8. **Åtgärd och verifiering:** Använd endast existerande reversibla fel-/återställningsmekanismer för native-simulering. Visa före/fel/efter, ingen förändring av originalprojektet utan uttryckligt godkännande och Save.
9. **Efteranalys:** Förklara *varför* en hypotes var korrekt/felaktig, vilka observationer som saknades och hur man dokumenterar en driftincident utan gissning.

**Tre hjälpnivåer:** Nybörjare: färdigt genomarbetat fall och ledtrådar. Fortsättning: välj diagnostik och tolkning innan förklaring. Avancerad: välj ordning, utvärdera alternativ och dokumentera osäkerhet. Svårighetsnivå får aldrig ändra protokollets sanningsregler eller dölja nödvändigt negativa utfall.

**UI-kontrakt:** inga nya globala menyer eller massiv redesign utan godkänt kodkort och verkligt UX-behov. Återanvänd nuvarande diagram, From/To, labbsessioner, portval, stale guards, paketanimation, identifierare och reset/replay. Framtida pedagogiskt innehåll ska lagras som granskade textresurser/komponenter inom ett separat godkänt feature-scope; ingen ny generell kursparser eller ändrad `.yadilab`-schema är beslutad.

## 6. Kompetenskarta: vad studenter ska lära sig, inte vad applikationen redan simulerar

| Område | Centralt diagnostiskt kunnande | Undervisningstyp i detta beslut |
|---|---|---|
| OSI/TCP-IP, lager och dataplan/kontrollplan/managementplan | Var i kedjan kan felet uppstå? | Begrepp + stödda native-labb |
| Fysisk länk, optics, MTU, felräknare, duplex | Admin up kontra operational up, counters, L1/L2-fel | Verktygskort/statiska exempel; native port-disable där stödd |
| Ethernet, MAC/FDB, ARP, VLAN, 802.1Q | Inlärning, broadcast, access/trunk, L2-isolering | Native simuleringsfunktion när stödd, med oberoende referenser |
| IPv4, CIDR, gateway, connected/static routing | Longest prefix, return path, TTL, ARP next-hop | Native simuleringsfunktion inom verifierad modell |
| ICMP, DHCPv4, grundläggande UDP | Ping request/reply, DHCP DORA/lease, fel och tidsförlopp | Native där stödd, annars teori/statiska exempel |
| STP/RSTP/LACP/portchannels | Fysiska kontra logiska vägar, blocked/forwarding, aggregation | Statiska exempel eller fristående Linux-labb |
| OSPF/IS-IS/BGP | Neighbors, states, LSDB/LSA, SPF/metric, BGP-policy/RIB/FIB | FRRouting/containerlab separat; verifierat statiskt innehåll |
| ACL, NAT, stateful firewall, TCP/UDP-portar | Regelordning, matchning, session state, returväg | Batfish eller isolerat nftables-labb separat |
| SNMP, syslog, telemetri, NetFlow/sFlow | Observera räknare, larm, datakvalitet och samplingsscope | Separata verktyg; **SNMP är inte routing** |
| DNS, DHCP-relay, NTP, AAA | Namnuppslagning, tidsberoenden och autentisering | Separate labs + verktygskort |
| IPv6/SLAAC/ND, VRF, VPN, overlays | Dubbelstack, segmentering, virtualisering, tunnlar | Separata lärlabb, inte native-utfästelser |
| Wi-Fi, cloudnät, brandväggszoner, QoS | Rörliga klienter, policys, trängsel och abstraktioner | Separat referensmaterial; explicit coverage |
| Drift, förändringskontroll, automation, säkerhet | Inventering, backup, behörighet, rollback, incidentlogg | Metodik, inte autonom hantering av kundnät |

**Förväxla aldrig SNMP med OSPF:** SNMP är ett protokoll för övervakning/management av bland annat interfaces och counters, medan OSPF är ett dynamiskt routingprotokoll. LLDP beskriver rapporterade grannrelationer och portinformation men är inte automatiskt ett fullständigt, validerat fysisk-kabelbevis. BGP och OSPF ger olika slags routinginformation; routing och faktisk packet forwarding skiljer sig från topologisk närhet.

**Leverantörsoberoende nivå:** Lära studenten fråga ”varför står gränssnittet down?”, ”vilken route väljs?”, ”var blockerar policyn?”, ”kommer svaret tillbaka?” snarare än memorera en leverantörs syntax. Vendor CLI-exempel måste märkas med plattform/version när relevant och ha alternativ på Linux/andra leverantörer. Inga påståenden att en viss kommandosträng finns i alla operativsystem.

## 7. Externa verktyg – pedagogiska kort, aldrig runtimeintegration

| Verktyg | Bra fråga studenten får lära sig ställa | Vad det inte automatiskt bevisar |
|---|---|---|
| SuzieQ | Vilka interface, LLDP-grannar, RIB/FIB-tillstånd och protokollgrannar observerades vid snapshot? | Inte full generell ACL-/framtida ändringssimulering |
| Batfish | Tillåts ett specificerat flöde av inläst konfiguration/policy; hur påverkar en snapshot-ändring? | Inte observerad live-trafik eller komplett discovery |
| Netshot | Vilka konfigurationer samlades och hur skiljer sig snapshots? | Inte det aktuella forwardingläget i varje enhet |
| NetXMS | Vilka enheter och förbindelser rapporterar discovery/övervakning? | Inte en fullständig digital tvilling av kundnätet |
| Wireshark/tcpdump | Vilka ramar/paket syntes på vald mätpunkt under given period? | Att icke-fångade paket inte fanns någon annanstans |
| FRRouting + containerlab | Hur bildar riktiga, isolerade Linux-routingprocesser OSPF/BGP-neighbors och ändrar routing? | Att varje fysisk leverantör eller kundnät beter sig identiskt |
| Linux `ip`, `bridge`, `ss`, `traceroute`, `dig` | Vilka lokala interface, grannar, rutter, lyssnande socketar, hop och DNS-resultat finns? | Automatisk förklaring av hela nätverket |
| SNMP-klient separat | Vilket värde rapporterar OID/MIB och vilket access-/mätfel finns? | Att ett SNMP-fel innebär paketförlust eller L3-fel |

**Verktygskort ska ange:** syfte; förutsättningar och nödvändigt tillstånd; exempelkommando med relevant plattform; vilka fält man läser; ett korrekt om–då-exempel; minst en felaktig vanlig tolkning; nästa skiljande test; datasäkerhet; originalreferens och verifieringsstatus. Använd enbart granskade, syntetiska eller uttryckligen tillåtna anonymiserade exempel. Verktygsexempel ska märkas `STATISKT ÖVNINGSEXEMPEL – EJ KÖRT I APPEN`. Visa aldrig credential, verkliga hemligheter eller kundidentifierande konfigurationer.

**Säkerhet:** Inga exekverade shellkommandon från applikationen, ingen dold fjärranslutning, scanning eller PCAP-läsning. Terminalkommandon är pedagogiska förslag som studenten manuellt kan använda i *egen isolerad labbmiljö* eller uttryckligen godkänd miljö med lägsta rimliga rättigheter. Konfigurationsändringar i produktion kräver egen ändringsprocess.

## 8. Sanningslager och testbar spårbarhet

Separera i all presentation:

1. **Källdokument:** angiven och validerad topologi/konfiguration, med källrad, cell, tidsstämpel och proveniens i den mån datat faktiskt innehåller detta.
2. **Native simulerat:** resultat från existerande simuleringsmotor, exakt scenario/kanoniskt projekt och observerade simulerade steg.
3. **Externt statiskt exempel:** explicit markerade förberedda verktygsresultat och tillverkar-/versionsscope.
4. **Verkligt observerat:** får endast sägas när det finns faktisk tillåten mätning från real utrustning, inte bara en skärmdump i kursen.
5. **Okänt eller ej stött:** får inte ersättas med plausibla gissningar eller positiva standardvärden.

Använd inte diagramposition, subnät, hostnamn, routerroll, ritade pilar eller en LLDP-indikation för att hitta på kablar, routes, MAC eller trafik. Ett fungerande ICMP Echo under modellen visar endast lyckad kommunikation enligt modellen; ACL/NAT/OSPF/STP på verkligt nät får inte ignoreras om slutsatsen sägs avse verklig reachability.

## 9. Historisk genomförandeordning – P0–P7 (formellt avslutad 2026-11-26)

**P0–P7 är CLOSED, inte en aktiv uppgiftskö.** Ordningen nedan bevaras för spårbarhet och förklarar tidigare prioriteringar; den ger inte mandat att automatiskt starta ett nytt arbetskort eller återuppta historiska planer. Vid framtida användaruppdrag kontrolleras aktuell kod, `main`, PR och CI, men ny utveckling kräver ett nytt uttryckligt avgränsat mål. Tidigare implementerade funktioner ska inte återskapas. Nya protokoll, schema, runtimeintegrationer och brytande redesign kräver separat uttryckligt beslut.

**P0 – kort, skrivskyddad evidensgrind:** Kontrollera senaste huvudgren, aktiv PR, CI, existerande funktioner och förankra en första liten övning i befintliga `icmp_investigation.py` / `troubleshooting.py` eller `dhcp_investigation.py`. Inga påhittade protokoll.

**P1 – ett komplett Om–Då-case:** Visa exempelvis ”Echo Request når fram men Reply saknar returroute” med nio rubriker, en skillnad mellan direkt observation och hypotes, ett motbevisande test och både rätt/negativt resultat. Återanvänd befintliga API-svar; **ingen andra ICMP-motor**.

**P2 – elevhypotes och minsta test:** Studentens hypotes registreras i övningens tillfälliga UI-tillstånd; visa självskattad säkerhet separat om särskilt beslutat. Inget projektfält eller automatisk kunddiagnos.

**P3 – liten granskad kursbank:** Minst två olika felorsaker ska kunna ge samma ytsymptom; case med fungerande baseline, skadad kopia och återställning; negativa och alternativa utfall. Ingen generell generativ text som facit.

**P4 – statiska externa verktygskort:** Enstaka genomarbetade SuzieQ-, Wireshark-, Netshot- och Batfish-exempel som överensstämmer med officiella verktygsdata. Ingen installerare, exekvering, importerare, API eller livekontroll.

**P5 – OSPF/SNMP/ACL-bredd utan falsk motor:** Expertgranskade om–då-fall med korrekta undantag, motsägande observationer och valfria instruktioner till helt separata FRRouting/containerlab-labb. Inget påstående att applikationen simulerar OSPF, ACL eller SNMP.

**P6 – automatiserad effekt- och kvalitetsmätning (Codex; inga mänskliga testpersoner):** Utveckla ett litet reproducerbart, automatiserat utvärderingspaket som använder befintliga P1–P5-fall, den faktiska simuleringsmotorn där den är stödd och separat granskade, statiska facit där native-protokoll saknas. **Ingen rekrytering, extern elevpanel, nätverksexpertpanel, användarstudie eller annan mänsklig testning krävs i P6.** Codex ska implementera och testa följande:

- **Definierade fall och oberoende facit:** Reproducerbara positiva, negativa och alternativa diagnosfall med uttryckliga förutsättningar, motbevisande observationer och kontroll av samma ytsymptom med olika grundorsaker. Facit får inte härledas enbart från det resultat som ska kontrolleras.
- **Diagnostisk precision:** Mät hur många definierade testfall som bedöms rätt eller fel mot facit. Avvisa otillräckligt stödda slutsatser, felklassificeringar och för tidigt avslöjat facit. Visa faktiska antal med tydlig nämnare, inte uppfunna elevresultat eller konfidensprocent.
- **Testval och motexempel:** Kontrollera maskinellt att ett valt test kan skilja relevanta hypoteser åt, att alternativa utfall hanteras och att orsak, åtgärd och återställning förblir avgränsade till tillgänglig evidens.
- **Tid och reproducerbarhet:** Mät bara faktiskt instrumenterad exekverings-/testtid eller registrerade händelser i automatiserade flöden. Kalla inte detta mänsklig tid till relevant test eller mänsklig begriplighet. Redovisa miljö, körning, antal och begränsningar.
- **Codex-leverans:** Implementera minsta nödvändiga testharness/rapportering inom befintlig arkitektur, med positiva och negativa tester, riktig Chromium vid UI, bibehållna stale guards och projektintegritet, samt obligatorisk CI på exakt PR-HEAD. Ingen ny projektmodell, ingen dold telemetri, inga externa integrationer och ingen automatisk persistens.
- **Rapportens sanningsgräns:** Rapportera enbart faktiskt körda testresultat, täckning, regressioner och identifierade brister. Automatiska tester kan ge evidens för teknisk korrekthet och undervisningslogik, **inte empiriskt fastställa inlärningseffekt hos människor**. Sådan effekt är `NOT_VERIFIED` och utgör **ingen leverans- eller mergegrind** i P6.

**P6 är komplett när Codex levererat det reproducerbara automatiserade paketet, verifierat positiva/negativa utfall och passerat ordinarie CI-grindar.** Ingen extern mänsklig utvärdering behövs för att gå vidare till P7.

**P7 – vidare kursbredd (AVSLUTAD):** Inriktningen var faktiskt mätta pedagogiska brister, relevanta felsökningsuppgifter och tydliga begränsningar utan orealistisk helhetsgaranti. **Formellt avslutsbeslut 2026-11-26:** Användaren har uttryckligen beslutat att P7 och därmed P0–P7 ska stängas. De sista verifierade P7-leveranserna omfattar [PR #165](https://github.com/Northsw-spec/YadiLab/pull/165) och [PR #166](https://github.com/Northsw-spec/YadiLab/pull/166), båda mergade. Beslutet är **inte** en utfästelse att varje möjlig pedagogisk förbättring är genomförd, att elevinlärning empiriskt är verifierad eller att all simulatorlogik är felfri. **Nästa etapp: INGEN BESLUTAD.**

## 10. Acceptans och negativa tester för framtida pedagogiska kodändringar

Varje framtida konkret PR ska enligt `AGENTS.md` och `MASTERPROMPT.md` ha en avgränsad funktionsdefinition, positiva och negativa tester, nödvändigt browser- och Save/Open-bevis på **exakt slutlig PR-HEAD**, grön obligatorisk CI och separat relevant användargodkännande om produktkontrakt/schema/motor ändras.

**Minsta negativa regressionsmatris för undervisning:**

1. `NO_ROUTE` med saknad returroute får aldrig märkas som lyckat Echo Reply.
2. Samma ping-symptom kan ha både VLAN-, port-, ARP-, IPv4- och route-relaterade orsaker; ingen ensam symptomregel får hävda en unik fysisk grundorsak.
3. OSPF `Init` ska inte automatiskt ”diagnostiseras” som kabelbrott; `2-Way` ska inte automatiskt vara fel när nätverksdesignen inte kräver `Full` mellan just de grannarna.
4. `SNMP timeout` är inte ett bevis för att dataplanet eller routing är nere.
5. Ett Wireshark-spår utan synligt ARP Reply är inte ett bevis för att inget svar existerade utanför fångstpunkten.
6. En dokumenterad route eller Batfish-config-trace får inte presenteras som faktisk live reachability.
7. Inga verktygsexempel eller statiska utdata får märkas `LIVE`, `NATIVE_SIMULATED` eller `VERIFIED_NETWORK`.
8. Saknad förklaringsdata ska visa `UNKNOWN`/`NOT_VERIFIED`, aldrig improvisera en artikel, port, regel, orsak, sannolikhetsprocent eller nästa hop.
9. Eleven får inte få en dold felorsak avslöjad i API, animation eller feedback före relevant pedagogiskt steg.
10. Ändrad arbetsyta och sent HTTP-svar ska ogiltigförklara visat resultat enligt befintligt stale-guard-kontrakt.
11. En pedagogisk vy får inte ändra projekt, noder, kablar, routes, importkvitto, filbytes eller sessionernas livscykel ofrivilligt.
12. Utan externa appar installerade ska applikationen och dess befintliga simulator fortsätta fungera fullt enligt aktuellt kontrakt.
13. Ett t.ex. `85 %`-påstående om sannolik felorsak utan validerad statistisk modell ska avvisas vid innehållsgranskning.
14. Ingen ny Windows/macOS-bana, generisk discovery, extern motor, runtimeberoende eller automatiskt systemkommando.

**Innehållsgranskning före merge:** Varje pedagogiskt faktapåstående har en verifierbar referens (RFC, officiell dokumentation, explicit projektkod med test eller en korrekt märkt syntetisk fixture), förutsättningar, motexempel/undantag samt status. Inga vendor-specifika terminalutdata skrivs som påhittade observationer. Expertgranskning av protokollsemantik rekommenderas; om den inte skett skriv `NOT_VERIFIED`. Inga särskilda sanningsklasser eller automatiska ”intelligensmotorer” uppfinns.

## 11. Samspel med andra styrdokument

- `AGENTS.md`: operativa regler, Linux-only, inga hallucinerade kablar, en PR åt gången, obligatoriska kvalitetsgrindar.
- `docs/MASTERPROMPT.md`: produktmål, en modell, korrekt motor, verifierbar funktionalitet, utbildningsarkitektur och statusklasser.
- **Detta dokument**: formellt avslutad P0–P7-roadmap och fortsatt pedagogiskt kvalitetskontrakt; inga äldre eller nya etapper är därmed aktiva byggorder.
- `docs/IMPORT_SOURCE_CONTRACT.md`: enda importkontraktet med fail-closed och källproveniens.
- `docs/ELK_LAYOUT_CONTRACT.md`: bevarat tekniskt layoutkontrakt, inte en separat ELK-roadmap.
- `docs/ICMP_INVESTIGATION.md`, `docs/TROUBLESHOOTING.md`, `docs/DHCP_DORA.md`: befintliga native diagnoser, inte OSPF-/brandväggsemulering.
- `tests/test_protocol_reference_vectors.py` och andra negativa referenstester: stödda avgränsade fall, ingen generell RFC-certifiering.

När äldre text säger ”nästa PR”, ”inte implementerat” eller ”ny feature” måste aktuell kod, historiska PR-merge och exakt CI kontrolleras. En daterad plan är inte en körbar order. Nya problem får dokumenteras som verifierade fynd eller förslag, aldrig lösas genom gissning. **Denna fil är inte längre en automatisk prioriteringslista för nya PR:er. Nytt arbete kräver uttryckligt användarbeslut; verifierad kod/CI har fortsatt företräde i tekniska faktapåståenden.**

## 12. Källor och verifieringsnivå

**Kontrollerade interna källor:**  
- [../AGENTS.md](../AGENTS.md)  
- [MASTERPROMPT.md](MASTERPROMPT.md)  
- [ICMP_INVESTIGATION.md](ICMP_INVESTIGATION.md)  
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)  
- [DHCP_DORA.md](DHCP_DORA.md)  
- [../tests/test_protocol_reference_vectors.py](../tests/test_protocol_reference_vectors.py)  

**Externa referenser för egna undersökningar och kursgranskning (inte integrationsberoenden):**  
- OSPF RFC 2328: https://www.rfc-editor.org/rfc/rfc2328  
- ARP RFC 826: https://www.rfc-editor.org/rfc/rfc826  
- ICMP RFC 792: https://www.rfc-editor.org/rfc/rfc792  
- DHCP RFC 2131: https://www.rfc-editor.org/rfc/rfc2131  
- SuzieQ: https://github.com/netenglabs/suzieq  
- Batfish: https://github.com/batfish/batfish  
- Netshot: https://github.com/netshot-net/Netshot  
- Wireshark: https://www.wireshark.org/docs/  
- FRRouting: https://docs.frrouting.org/en/latest/  
- containerlab: https://containerlab.dev/

**Verifieringsstatus för detta dokument:** Arkitekturbeslut och föreslagen undervisningsmodell; ingen ny runtimekod har implementerats eller testats genom dokumentet. Kontrollera framtida källor, versioner, CI och beteenden före varje kursleverans.