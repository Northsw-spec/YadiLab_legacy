# Deterministisk simuleringskärna – tekniskt arkitekturkontrakt

**NYTT BINDANDE FÖRETRÄDE:** [ADR-0002](ADR_0002_FRESH_ENGINE_2026-11-26.md). Ny motorn är självständig och får aldrig importera gamla Ethernet-/ARP-/IPv4-/ICMP-/DHCP-runtimeklasser. Text nedan om att återanvända gammal engine avser endast historiska externa regressioner och är upphävd som implementationsregel. S1-POC0 startar efter guard/ADR utan färdig hela S0. Endast EN produktionsmotor per scenario före/efter cutover.


**INTEGRATIONSSCOPE:** [PT-FULL-001](../FULL_PACKET_TRACER_PARITY_CONTRACT.md) kräver ALL Packet Tracer-kompatibel funktionalitet. Den gemensamma DES-kärnan måste därför stödja riktiga packets, timers, fysiska länk- och enhetstillstånd, multiuser/federering när användaren aktiverar det, isolerat IoT/OT/scripting och fulla device-/CLI-scenarier utan att en parallell motor skapas. Inget generellt förbud mot all autentiserad peer-kommunikation får reducera Multiuser till OPTIONAL. Enbart Linux; accessibility/keyboard-only inte mål.


**Arkitekturbeslut 2026-11-26:** [ADR-0001](ADR_0001_CORE_REPLACEMENT_2026-11-26.md) fastslår selektiv nybyggnad av EXEKVERINGSKÄRNAN, inte av hela produkten. Bevara korrekta bytecodecs, UI, import/data och testsanning; pensionera synkron bulk-forwarding och separata klockor. Test-only S1-POC tillåts efter S0 utan dubbel användarsynlig engine.


**Status:** målkontrakt, NOT_IMPLEMENTED på main 7dbe2285cde7ea87c08afce1c58d36cd0f5697e7. **Ägare:** enda in-process backendmotorn; all faktisk utbyggnad beslutas i [enda aktiva roadmapen](../REMEDIATION_PLAN_2026-11-26.md), kort S1 och följande S-kort. **Inte** en begäran att lägga till en konkurrerande motor eller ny emulator.

## Kärninvariant och gränser

Det finns en **auktoritativ explicit projektkonfiguration**, en final validator och ett exekverings-/sessionslager av runtime state. Nuvarande `model.py::validate_project` kan initialt bevara gamla projektfilers externa valideringskontrakt. Nya Ethernet/ARP/IPv4/ICMP/DHCP-funktioner implementeras självständigt från standard-orakel; gamla motorklasser återanvänds inte. Förbjud två oberoende dataplan som ger olika nätverkssvar för samma scenario. Inga VM:ar, gästande OS, Cisco IOS-images, GNS3/EVE-NG, containers, FRRouting- eller ns-3-runtimeprocesser, nätverkspaketsändning på host NIC eller verkliga nätverkskontakter.

En **discrete-event kernel** kör protokoll/state transitions i en process, gärna med en prioriterad stabil kö med (simulated_time_ns, monotonically_increasing_event_id), heltalsnanosekunder och en seedad PRNG. Odefinierad/slumpmässig ordning, väggklockstid, DOM-animationshastighet och fysisk nätverkstid får aldrig påverka semantiska resultat. Ett aktivt event får schemalägga nya events. Explicit max events/time/memory, watchdog för zero-time livelock, ev.cancel samt resursgränser krävs.

## Strikt datamodell, runtime-state och provenance

1. Konfiguration: device IDs, porttyper/capabilities, adresser, VLAN, routes, protokollinställningar, kablar och länkprofiler. Manuell Builder får skapa explicita objekt; dokumentimport får **aldrig** fylla luckor tyst. Ett användarvalt auto-template måste visa exakt genererad konfiguration och kräva aktiv acceptans innan den blir projektdata.
2. Runtime state: separata instanser för MAC/FDB, ARP/ND, RIB, FIB, OSPF LSDB, BGP Adj-RIB-In/Loc-RIB/Adj-RIB-Out, TCP control blocks, NAT conntrack, DHCP leases och appserver-state. Allt ägs av samma simuleringssession och binds till en konfigurationsrevision och scenario-ID.
3. Tidsmodell: återkommande Hello/aging/retransmission/lease/queue events. En verklig packet send skapar explicit TX start, propagation, RX, parser, protocol transition, decision, förlust eller next hop; packet_id och parent_event_id bildar en **orsakskedja**.
4. Save/Open: endast explicit Save ändrar användarens dokument. Simulerad runtime-state lagras inte implicit. Om ett senare scenario-snapshot tillåts krävs separat versionssatt, explicit valt artefaktformat och bitidentitet/återspelning.
5. Konfigurationsmigration: schema 1.0–1.4 förblir läsbara utan tyst värdeförlust. Nya fält och deviceprofiler får introduceras endast med en dedikerad migrations-/kompatibilitets-PR, strict reject för inkompatibla fält, negativa importtest och bevarad legacy Save/Open/SHA. Modell kan växa utan ogrundade inferenser.

## Paket och referensobjekt

- Packet/header layer: byte-/fältkällor, validering, checksums, length/MTU och dokumenterad codec. Payload får vara modellförenklad när det är explicit märkt och inte ger falskt stöd för en standard.
- Physical/link: medium, duplex, fiber, upp-/nedstatus, bitrate, propagation-delay, serialization-delay, drop och queue policy. RTT får bara uppstå från en implementerad tidsmodell; utan sådan visas UNKNOWN.
- Network/control plane: RIB ≠ FIB ≠ framgångsrikt mottaget paket; neighbor state, timer och policy bestämmer paketen. En routingtabellsrad är inte nåbarhetsgaranti.
- Session/API: Start/Stop/Reset, pause/step/run-to/event replay, event budgets, snapshot revisions och sena HTTP-svar. UI är endast projektion av backend-events och ska inte beräkna ett parallellt facit.
- Device profiles: generiska och versionslåsta capabilities, CLI-kommandon endast när simuleringsmotorn kan exekvera semantiken; "unsupported" avvisas synligt. Kända leverantörsspecifika beteenden är separata profiler med laglig dokumentation.

## Acceptanskriterier för S1

En isolerad, testbar scheduler måste uppfylla alla dessa kontroller:

1. Samma konfiguration + seed + eventschema ger **exakt samma ordnade eventbytes och state-hash** över minst två separata processstarter. Om osorterad mapordning ger avvikelse = FAIL.
2. Lika tidsstämpel avgörs strikt av event-ID; avbrutna timers körs aldrig; omplanering och återstart av simulation-session läcker ingen gammal callback.
3. Event- och simulerad tidsbudget är fail-closed; zero-time-loop, negativ tid, overflow, okänt event/target och extrema payloads stoppas reproducerbart med maskinläsbar orsak.
4. Konkret positivt Ethernet/ARP/IPv4/ICMP-trafikspår måste beräknas av NY engine med verkliga tidsordnade events, och en VLAN-isolerad negativ motfixtur förblir avvisad. Gammal engine är separat legacy-comparator i test, aldrig ett schedulerberoende.
5. Kausalkedjan kan granskas: parent_event, packet_id, in-/utport, header, tabellbeslut, drop reason, timers, time_ns. Dolda UI-filter påverkar **inte** simuleringsresultat.
6. Riktig webbläsare kan pausa/steppa/återspela ett exakt scenario; att ändra en aktiv arbetsytesnapshot invaliderar gammal session, och Save/Open/SHA förblir oförändrade.
7. Arkitektur- och modulägargrind förhindrar ny monolit, duplikat validator och andra simulation engine; Required CI på exakt PR-HEAD PASS, plus oberoende benchmark/negativa tester.

## Orakelstrategi för varje efterföljande protokoll

Varje S-protokoll kräver ett **versionerat protokollkontrakt**: källa och errata, parsning av råbyte, state machine, tids-/fel-/retry/expiryfall, multi-hop/race/topologi, avvisade fall, security/risk, standardtabell, referensimplementation eller isolerad testfixture, UI-semantik, budget och prestanda. Minst en positiv, en negativ och ett **motsägande** scenario ska ha oberoende förväntat resultat. Differentialtester kan använda referensstackar offline som test-orakel men inte länkas in i appen. Fastställ konvergens/resultat efter tidsbudget, inte bara lyckad funktion efter oändlig väntan.

CI rapporterar PASS/FAIL/NOT_RUN med nämnare och versionslåst SHA. Dokumentation kan aldrig uppgradera stödetiketten; endast implementering med oberoende validering kan det. Riktad testtrappa före full Required CI enligt [Codex-policyn](../CODEX_EXECUTION_POLICY.md).

## Säkerhet och licens

Simulatorn är **offline först**, ingen trafik injiceras i riktiga nät, inga riktiga ICS/PLC-kontroller styrs. Lägre tillförlitliga scenariodata körs aldrig som godtycklig Python/JS/shell/CLI i hosten. Behåll strikta JSON-/schema-/fil-/API-behörighetsgränser och resursgränser. Simulerad SSH/IPsec får inte marknadsföras som säker kryptografi om ingen korrekt kryptomodell med testade algoritmer verkligen används. Cisco och tredje parters produktnamn, varumärken, proprietära CLI/IOS eller patentlicenser kräver egen juridisk granskning före distribution.
