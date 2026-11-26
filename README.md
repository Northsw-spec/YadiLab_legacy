# YadiLab – Linuxbaserad nätverkssimulator och pedagogiskt felsökningslabb

**Ny produktvision 2026-11-26:** YadiLab ska bli en fullständig **in-process nätverkssimulator** (inte en VM-/IOS-emulator) med målet att objektivt överträffa Cisco Packet Tracer i teknisk korrekthet, protokollbredd, funktion och pedagogik. Detta är **planerat, inte dagens implementerade stöd**. Den [enda aktiva A0–A10 + S0–S12-planen](docs/REMEDIATION_PLAN_2026-11-26.md), [MASTERPROMPT](docs/MASTERPROMPT.md), [Cisco-gapforskningen](docs/research/PACKET_TRACER_GAP_ANALYSIS_2026-11-26.md), [protokollmatrisen](docs/PROTOCOL_COVERAGE_MATRIX.md) och [simuleringskärnans kontrakt](docs/architecture/DETERMINISTIC_ENGINE_CONTRACT.md) ger konkret implementationsordning och standardkrav. A9-protokollutbyggnad har uttryckligen godkänts; A8-människostudien inte. A3-del 3 [PR #179](https://github.com/Northsw-spec/YadiLab/pull/179) är mergad i main 7dbe2285cde7ea87c08afce1c58d36cd0f5697e7; hela A3 återstår fortfarande.


YadiLab är en **lokal Linux-applikation** för nätverksdokumentation, visualisering och avgränsad simulering. Windows och macOS stöds inte och ska inte bli utvecklingsmål.

**Codex-utvecklingsregler:** [AGENTS.md](AGENTS.md) + [obligatorisk kredit-/CI-optimering](docs/CODEX_EXECUTION_POLICY.md). Inga passiva GitHub Actions-pollingloopar eller dubbla fulla CI på PR-push; ingen release utan Required-grind på exakt HEAD.

**Historiskt A0–A10-stabiliseringsarbete:** detaljerna nedan gäller den befintliga arkitektur-/säkerhetsgrunden; den nya enda aktiva huvudplanen innehåller även S0–S12. **A0 DONE** ([PR #169](https://github.com/Northsw-spec/YadiLab/pull/169)); **A1 DONE** ([PR #170](https://github.com/Northsw-spec/YadiLab/pull/170), [G1–G7-kontrakt](docs/architecture/A1_GUARD_CONTRACT_2026-11-26.md), separat Required `architecture-guard` bevisad via [blockerad negativ PR #173](https://github.com/Northsw-spec/YadiLab/pull/173) med `unit-tests=SUCCESS`). **A2 DONE** ([PR #175](https://github.com/Northsw-spec/YadiLab/pull/175), 10 TCP-abortregressioner, required CI SUCCESS och squash-merge). **A3 IN_PROGRESS:** [del 1, PR #176](https://github.com/Northsw-spec/YadiLab/pull/176) är mergad (dropdown-DOM), [del 2, PR #177](https://github.com/Northsw-spec/YadiLab/pull/177) är verifierat mergad (main `16e6bd67444b1ef9eb96f2448edf04efda2ab17f`) och centraliserar [workspace-/stale-revisioner](docs/architecture/A3_WORKSPACE_REVISIONS_2026-11-26.md); hela A3 är inte DONE. [Granskningsrapport 2026-11-26](docs/reviews/TECHNICAL_REVIEW_2026-11-26.md), [AGENTS.md](AGENTS.md) och [MASTERPROMPT](docs/MASTERPROMPT.md) styr källfakta och exekvering. P0–P7 är formellt CLOSED och får aldrig återaktiveras automatiskt. A8 mänsklig studie kräver separat godkännande; A9:s simulatorutbyggnad är beställd som S0–S12.

## Starta på Linux

Python 3.10+ och en lokal webbläsare behövs.

```bash
python3 -m network_core
```

Normalt används `http://127.0.0.1:8765/`; om porten är upptagen kan en annan lokal port väljas och visas i terminalen. Med explicit port och datakatalog:

```bash
python3 -m network_core --data-dir ~/NetworkProjects --no-browser --port 8765
```

**Lokal API-behörighet:** Vanlig start skapar en ny slumpmässig åtkomstnyckel per körning och visar den i terminalen. När webbläsaren begär åtkomst till sparade projekt eller simulering klistrar du in denna nyckel i appens låsta dialog. Nyckeln finns inte i webbadressen och lagras inte på disk. Obehöriga processer som bara känner till loopbackporten får HTTP 401 för privata API-anrop. `--no-browser` kräver fortfarande nyckel. För en manuell CLI-klient använd `Authorization: Bearer <nyckel>` (mata in nyckeln utan att lägga den i kommandoradshistorik eller URL). Se [lokal API-säkerhet](docs/LOCAL_API_AUTH.md) för hotmodell och begränsningar. Flaggan `--unsafe-test-no-auth` finns enbart för isolerade regressionstester och är osäker i delade miljöer.

Avsluta med Ctrl+C. ELK för layout är medpackat lokalt; [NOTICE](web/vendor/NOTICE.md) och [ELK-licens](web/vendor/ELK-LICENSE.md) bevaras.

## Befintliga avgränsade komponenter

| Område | Finns som avgränsad implementation, inte som total protokollgaranti |
|---|---|
| Builder | Explicita noder, portar, zoner och fysiska länkar; SVG/ELK |
| Layer 2 | Ethernet, MAC-inlärning, ARP, VLAN och access/trunk |
| Layer 3 | IPv4, CIDR, connected/statiska routes, begränsad forwarding, TTL och ICMP |
| DHCPv4 | DORA, leases, T1/T2, tidsförlopp och vissa felövningar |
| Felsökning | Kontrollerad felinjicering, dolda ICMP-/DHCP-fall och återställningskontroll |
| Dokumentation | CSV/XLSX/ODS, explicit mappning/proveniens och projektets Save/Open |

Detta är en **komponentinventering**, inte bevis för full RFC-kompatibilitet eller faktisk kundnätsreachability. OSPF/BGP, STP, generella ACL/NAT, SNMP, DNS, IPv6 med flera är inte därmed inbyggda protokollmotorer. Den nya **sammanhållna pedagogiska arbetsytan är planerad**, inte färdig. OSPF/BGP, STP, TCP/UDP, IPv6, NAT, device-CLI, Wi-Fi och industriella nätverk är fortfarande NOT_NATIVE idag; deras fullständigt testade implementation är framtida S-arbete.

## Tekniska referenser – inga utvecklingsköer

- [Import och källtrohet](docs/IMPORT_SOURCE_CONTRACT.md), [kalkylbladsformat](docs/SPREADSHEET_V13.md), [ELK-kontrakt](docs/ELK_LAYOUT_CONTRACT.md).
- [Ethernet](docs/ETHERNET_FORWARDING.md), [VLAN](docs/VLAN.md), [ARP](docs/ARP.md), [routing](docs/STATIC_ROUTES.md), [IPv4](docs/IPV4_FORWARDING.md), [ICMP](docs/ICMP_ECHO.md).
- [ICMP-felsökning](docs/ICMP_INVESTIGATION.md), [DHCP](docs/DHCP_DORA.md), [kontrollerade fel](docs/TROUBLESHOOTING.md), [sessioner](docs/SIMULATION_SESSION.md).
- [Oberoende testvektorer](tests/test_protocol_reference_vectors.py) och övrig faktisk kod under `tests/`.

En teknisk referens kan beskriva en **enskild moduls** begränsningar; den får aldrig läsas som aktuell fullständig funktionsstatus för hela appen.

## Verifiering

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
npm run check
python3 tests/browser_smoke.py
```

UI-testning behöver riktig Chromium och lämplig Linuxmiljö. Testresultat gäller den **specifika SHA** där de kördes. Dokumentation kan inte garantera frånvaro av programfel.

**Sanningsgräns:** sparad dokumentation är inte observation på ett verkligt nät; en ritad grafväg är inte bevisad paketleverans, och en modellping är inte live-mätning. Inga nätverksfakta får hittas på vid import. Endast uttrycklig Save skriver projekt till disk.
