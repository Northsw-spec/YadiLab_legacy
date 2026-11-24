# YadiLab – Linuxbaserad nätverkssimulator och pedagogiskt felsökningslabb

YadiLab är en **lokal Linux-applikation** för nätverksdokumentation, visualisering och avgränsad simulering. Windows och macOS stöds inte och ska inte bli utvecklingsmål.

**Enda aktiva utvecklingsplan:** [Pedagogisk arkitektur (P0–P7)](docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md). [MASTERPROMPT](docs/MASTERPROMPT.md) beskriver produktens mål och [AGENTS.md](AGENTS.md) skyddar utvecklingsprocessen. Ingen annan Markdown-fil är en roadmap. Äldre dokument och statusnoteringar finns bara i Git-historiken.

## Starta på Linux

Python 3.10+ och en lokal webbläsare behövs.

```bash
python3 -m network_core
```

Normalt används `http://127.0.0.1:8765/`; om porten är upptagen kan en annan lokal port väljas och visas i terminalen. Med explicit port och datakatalog:

```bash
python3 -m network_core --data-dir ~/NetworkProjects --no-browser --port 8765
```

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

Detta är en **komponentinventering**, inte bevis för full RFC-kompatibilitet eller faktisk kundnätsreachability. OSPF/BGP, STP, generella ACL/NAT, SNMP, DNS, IPv6 med flera är inte därmed inbyggda protokollmotorer. Den nya **sammanhållna pedagogiska arbetsytan är planerad**, inte färdig.

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
