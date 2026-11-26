# MASTERPROMPT – pedagogisk nätverksapplikation

**Operativ kreditregel:** Codex/agenten ska följa [CODEX_EXECUTION_POLICY.md](CODEX_EXECUTION_POLICY.md). Leverera konkret kod och oberoende testbevis, undvik passiv väntan/polling på GitHub Actions och osakligt upprepade långa tester; full Required CI och säker squash på exakt sista PR-HEAD får aldrig förbigås. Ingen bakgrundskörning utlovas utan faktisk mekanism.

**Nytt användarbeslut 2026-11-26:** [REMEDIATION_PLAN_2026-11-26.md](REMEDIATION_PLAN_2026-11-26.md) är **enda aktiva utvecklingsplanen (A0–A10)** för att åtgärda hela granskningsrapporten, motverka återmonolitisering och förbättra verifieringen. [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md](PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) innehåller den **formellt avslutade** P0–P7-roadmapen och fortsatt pedagogiskt kvalitetskontrakt. Detta dokument är ett **produktkontrakt**, inte en andra roadmap. [AGENTS.md](../AGENTS.md) innehåller operativa regler. Senaste uttryckliga användarinstruktion och faktisk kod, tester och GitHub-HEAD har företräde framför äldre statuspåståenden.

## Produktmål

YadiLab ska vara en **Linux-exklusiv**, lokal utbildningsapp där en blivande IT-/nätverkskonsult lär sig att:

1. granska explicit dokumenterad topologi och förstå vad som faktiskt är känt,
2. observera ett symptom och skilja det från en gissad grundorsak,
3. härleda **endast den tekniska betydelse som faktiskt följer av observationen**,
4. formulera flera konkurrerande hypoteser och välja ett test som kan motbevisa dem,
5. följa verkligt beräknade paket- och beslutsspår från befintlig stödd Layer 2/3/DHCP-motor,
6. föreslå rätt åtgärd först när övningsorsaken är styrkt,
7. verifiera före/fel/efter och dokumentera begränsningar utan falsk säkerhet.

Undervisningens **nio ordagranna rubriker**, tre hjälpnivåer, negativa tester och P0–P7 definieras enbart i pedagogikplanen. Ett sammanhållet framtida undervisnings-UI är **planerat**, inte automatiskt befintligt.

## Tekniska invariants

- **En auktoritativ projektmodell:** `network_core/model.py::validate_project`; explicita objekt och fysisk port-till-port-länk. Ingen implicit enhet, kabel, next hop eller IP utifrån geometri, namn eller nätverksantaganden.
- **En sammanhållen simuleringskedja:** återanvänd redan implementerade Ethernet, MAC-inlärning, VLAN, ARP, IPv4, connected/statiska routes, ICMP och begränsad DHCP, inklusive aktiva/icke-aktiva länkar och verifierbara felövningar. Skapa inte parallell protokoll- eller dataplanmotor.
- **Skilda bevisnivåer:** grafväg ≠ L2-trafik ≠ routingtabellmatch ≠ lyckad returtrafik ≠ verklig nätverksmätning. `DOCUMENTED`, `CONFIGURED`, `SIMULATED`, `UNKNOWN`, `UNSUPPORTED`, `NOT_VERIFIED` används enbart med faktisk innebörd. Ingen påhittad terminalutdata eller sannolikhet.
- **Sparad data är användarens:** dataintegritet, exakt projektidentitet, källproveniens, sessionsinvalidering, stale guards, ELK/SVG-layout och Save/Open bevaras. Endast explicit Save skriver till disk. Projektformat uppgraderas inte tyst.
- **Källimport är fail-closed enligt tekniskt kontrakt:** [IMPORT_SOURCE_CONTRACT.md](IMPORT_SOURCE_CONTRACT.md). Källdokument får inspekteras trots brister; en ofullständig avsedd topologi får inte utges som lyckad import. CSV/XLSX/ODS/JSON hanteras endast inom faktisk uttrycklig stödomfattning.
- **ELK är presentation:** layouten får flytta X/Y men inte ändra nod, port, kabel, VLAN, IP eller route. Gamla ELK-etapper är redan utförda och får inte återimplementeras genom äldre arbetskort.
- **Endast Linux:** Windows/macOS får aldrig bli målplattform, installatör, support eller CI-bana. Andra Linuxmiljöer stöds bara när de är testade.
- **Inga utlovade native protokoll utan kod och oberoende test:** OSPF/BGP, STP, ACL/NAT, SNMP, DNS, IPv6 etc. kan undervisas som granskade statiska exempel, inte fabricerade runtime-implementationer.
- **Tredjepartsprogram stannar utanför runtime:** Wireshark/tcpdump, FRRouting/containerlab, Batfish, SuzieQ, Netshot och NetXMS får beskrivas i statiska kurskort eller manuella separata labb; ingen installerare, SDK, shellkörning, API-adapter, importer, scanner eller liveanslutning är godkänd.

## Pedagogiskt tillägg till existerande funktioner

Använd `network_core/icmp_investigation.py`, `dhcp_investigation.py` och `troubleshooting.py` samt nuvarande webbsessioner som faktiska underlag för guidade och självständiga felsökningsövningar. Eleven får se observationer, själv formulera tolkningar och hypoteser, begära en mätning och därefter analysera motbevis. Dolt facit får inte läcka i API, UI eller animation. Reparation ska vara reversibel i övningsmodellen; användarens dokument och disk ändras inte implicit.

De guidade ICMP-fallen är **implementerade och täcks av regressionstester**: `echo-reply` undersöker saknad returroute (`NO_ROUTE`), medan `echo-reply-b` undersöker en matchande returroute med oåtkomligt nästa hopp (`ARP_FAILED`). Båda återanvänder den befintliga ICMP-simuleringsmotorn; se `network_core/icmp_investigation.py` och `tests/browser_icmp_lesson.py` för implementation respektive verkligt Chromium-test. Eleven får först ett neutralt Echo-symptom; rotorsaken ska styrkas av relevanta mätningar innan diagnos och reparation, och återställningen verifieras separat. Detta gäller simulerade övningar, inte observationer i verkliga nät.

## Utveckling och acceptans

När användaren ber att fortsätta YadiLab: kontrollera senaste `main`, öppna PR:er, båda Required-checks i [main-ruleset #27419615](https://github.com/Northsw-spec/YadiLab/rules/27419615), och aktuell kod/test/CI. Följ **nästa ej färdiga godkända A0–A10-kort** i [enda aktiva planen](REMEDIATION_PLAN_2026-11-26.md). **A0 DONE** via [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169). **A1 DONE** via [PR #170](https://github.com/Northsw-spec/YadiLab/pull/170), G1–G7 och [separat Required-negativt test i blockerad, ej mergad PR #173](https://github.com/Northsw-spec/YadiLab/pull/173), där `unit-tests` gick grönt och `architecture-guard` rött. **A2 DONE** via [PR #175](https://github.com/Northsw-spec/YadiLab/pull/175) efter verifierad required CI och squash `73a3fe0fb490ec8a7dbd5487ba8c4527ac9ea2ea`. **A3 IN_PROGRESS:** [PR #176](https://github.com/Northsw-spec/YadiLab/pull/176) är mergad efter 5 gröna CI-körningar; [PR #177](https://github.com/Northsw-spec/YadiLab/pull/177) har verifierat mergats efter 5 gröna CI-körningar (main `16e6bd67444b1ef9eb96f2448edf04efda2ab17f`) och centraliserar [arbetsyterevisioner/stale-spärrar](architecture/A3_WORKSPACE_REVISIONS_2026-11-26.md). Hela A3 kräver fortfarande explicit UI-invalidering och stale-`finally`, Builder/inspector, diagnos och import-/Save/Open-presentation. A8/A9 är bara valbara beslutsgrindar, inte beställningar. Välj aldrig något nytt P0–P7-steg, eftersom programmet är avslutat. Implementera godkända kort separat, med positiva/negativa tester, verklig Chromium för UI, riktig Save/Open/SHA för data, och båda Required-checks `SUCCESS` på exakt slutlig PR-HEAD före squash-merge.

Ett större nytt protokoll, annat schema, extern integration, annan OS-familj eller brytande omdesign kräver separat uttryckligt beslut. Det är inte implicit tillåtet av A0–A10-planen eller det avslutade pedagogikprogrammet.

**Målet är en tekniskt korrekt, begriplig och oberoende verifierbar utbildningsapp inom dokumenterat stödomfång – inte fler dokument, fler funktioner eller obevisad generell felfrihet.**
