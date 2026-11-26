# MASTERPROMPT – pedagogisk nätverksapplikation

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

När användaren ber att fortsätta YadiLab: kontrollera senaste `main`/PR/CI och aktuell implementation, följ **nästa ej färdiga godkända arbetskort A0–A10** i [den aktiva reparationsplanen](REMEDIATION_PLAN_2026-11-26.md), dokumentera bevis för aktuella C01–C18-ID och bevara gammal funktion. **A0:s forensiska dokumentation och manifest levereras i [PR #169](https://github.com/Northsw-spec/YadiLab/pull/169); kontrollera merge och exakt CI innan DONE. Därefter är A1 nästa arbetskort**, med verifierade G1–G7 och Required `architecture-guard` **innan** någon ny A3/A4-modularisering får påbörjas. **A8 och A9 är endast valbara beslutsgrindar**, inga beställningar av mänsklig studie eller nya protokoll. **Välj aldrig automatiskt nytt eller kvarvarande P0–P7-steg** eftersom det programmet är avslutat. Implementera varje godkänt arbetskort i en avgränsad PR och genomför positiva/negativa tester. Verklig Chromium vid UI, riktig Save/Open/omstart vid dataändring och obligatorisk GitHub-CI på **exakt sista PR-HEAD** krävs. Normal squash-merge endast om alla kontroller är godkända och branchskydd följs. Inga gamla QUALITY-/ELK-/import- eller generella fasplaner får trumfa detta beslut.

Ett större nytt protokoll, annat schema, extern integration, annan OS-familj eller brytande omdesign kräver separat uttryckligt beslut. Det är inte implicit tillåtet av A0–A10-planen eller det avslutade pedagogikprogrammet.

**Målet är en tekniskt korrekt, begriplig och oberoende verifierbar utbildningsapp inom dokumenterat stödomfång – inte fler dokument, fler funktioner eller obevisad generell felfrihet.**
