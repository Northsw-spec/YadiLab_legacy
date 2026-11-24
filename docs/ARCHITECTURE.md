# Applikationsarkitektur 0.1 — medvetet liten

> **Historisk arkitekturöversikt (statuskorrigering 2026-11-24):** Beskrivningar av ”nästa steg”, ”inte implementerat” eller tidigare funktionsbegränsningar i denna fil är historiska. De senare avgränsade IPv4/ICMP/DHCP-funktionerna och ELK-06A–C tillkom senare; se kod och respektive protokolldokument. Det [bindande pedagogiska kontraktet](PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) kompletterar arkitekturen **utan** en andra nätverksmodell, extern motor eller runtimeintegration. Verifiera faktisk kod och CI innan utvecklingsbeslut. Dokumentationsimport ska följa [det aktuella bindande importkontraktet](IMPORT_SOURCE_CONTRACT.md) och [verifierad statusöversikt](IMPLEMENTATION_STATUS.md); ingen ny importfunktion är färdig genom att den har dokumenterats.

## Varför en ny implementation?

Applikationen är ett nytt kodträd med en tydlig, begränsad kedja:

```
Användarens explicita fakta
        │
        ▼
network_core/model.py  ← schema och genomskinlig validering
        │
        ├── network_core/storage.py → verklig .yadilab på disk
        ├── network_core/server.py  → loopback HTTP och explicit Save/Open
        └── web/model.js, web/canvas.js, web/app.js
             └── SVG av EXAKT samma nod-/port-/länk-ID:n
```

Visningsnamnet deklareras endast i **`network_core/config.py`** som `APP_NAME`. Runtime-paketet `network_core` är avsiktligt generiskt och behåller sitt tekniska namn vid omprofilering. Pythonserverns vanliga lokala start kräver ingen separat nedladdad tredjepartsmodul. Webbläsardelen har däremot den **medpackade tredjepartskomponenten `elkjs`**; se [NOTICE](../web/vendor/NOTICE.md). Det vore fel att påstå att hela runtime saknar tredjepartskod.

## Modulgränser

| Modul | Ansvar | Gör inte |
|---|---|---|
| `model.py` | Schema, referenser, explicit grafspårning | Routing, ping, fysisk sanning |
| `storage.py` | Verkliga filer, SHA-256, förväntad föregående version | Autosave, tyst overwrite |
| `csv_import.py` | Explicit fyrtabells-CSV till verifierad kanonisk modell | Implicita kablar, heuristisk kolumnmappning, filskrivning |
| `xlsx_import.py` | Strikt OOXML ZIP-läsare för namngivna tabeller i schema 1.0 eller explicit 1.3 | Formler, dolda blad, makron, okända kalkylblad, filskrivning |
| `ods_import.py` | Strikt ODF/ODS ZIP-/manifestläsare för namngivna tabeller i schema 1.0 eller explicit 1.3 | Formler, dolda blad/rader, makron, filskrivning |
| `spreadsheet_schema.py` | Delad versionsmappning för XLSX/ODS; befintlig CSV-parser + schema 1.3-validering används för MAC, VLAN och statiska routes | Implicita länkar, tyst datatapp eller ny konkurrerande modell |
| `spreadsheet_templates.py` | Gemensamma binära XLSX-/ODS-skrivare för demo och exporterad dokumentation; delar tabellkontrakt men inte importlogik | Projektfiler, autosave, påstådd verklig nätverksinventering |
| `spreadsheet_export.py` | Läs-only serialisering av validerad arbetsmodell i schema 1.0/1.3, med faktisk återimport för roundtrip-validering före nedladdning | Förlust av valfria null-fält, versionsuppgradering, filskrivning, implicita länkar |
| `arp.py` | Explicit Ethernet/IPv4 ARP-request/reply över `EthernetFabric` med sparade 1.2-VLAN eller sessions-VLAN, flyktig cache och enskild HTTP/UI-diagnostik | Ingen IP-routing, ping, proxy-ARP eller varaktig ARP-session i UI |
| `ethernet.py` | Flyktig MAC-inlärning, explicit v1.1-port-MAC samt VLAN-forwarding på deklarerade kablar med 1.2-konfiguration eller sessionstillägg | ARP-protokoll, ping, IP, STP, NIC-acceptans eller lagring av inlärda tabeller |
| `server.py` | Lokal UI, API, validering, ARP, sessioner, routingtabell, IPv4-/ICMP Echo-diagnostik och temporär kabelbrottsjämförelse | Tolka källdata som topologi, spara diagnostik eller påstå extern nätverksreachability |
| `simulation.py` | Begränsat processlokalt sessionsregister som återanvänder en `ArpSession`/`EthernetFabric` mellan ARP- och Ethernetoperationer och validerar oförändrat projekt | Beständig session, IP-routing, ICMP eller delad projektmodell |
| `routing.py` | Read-only IPv4-tabell per nod med connected och explicit statiska routes, on-link next-hop och deterministisk longest-prefix match | IP-paketframföring sker inte här; ingen metric eller ECMP |
| `ipv4_packet.py` | Validerat minimalt RFC 791-datagram, headerchecksumma, TTL, experimentellt protokoll 253 och ICMP-protokoll 1 | IPv4-options, fragmentering, transport |
| `icmp.py` | Strikt RFC 792 Echo Request/Reply typ 8/0 och typ 0/0, checksumma, ID, sekvens och payload | Andra ICMP-typer, timeoutmätning, applikationsstack |
| `icmp_ping.py` | Riktig tur-och-retur-bunden ICMP Echo och routerursprungliga felpaket över samma `IPv4Trace` med befintlig ARP-/Ethernetmotor | Automatiska gateways, brandväggsregler, RTT, fler ICMP-felkoder |
| `icmp_errors.py` | RFC 792 typ 11/kod 0 och typ 3/kod 0, strikta bytes, originalcitat, checksumma och skydd mot rekursiva ICMP-fel | Andra ICMP-fel, godtycklig quoted payload eller obehörig generering |
| `troubleshooting.py` | Gemensam read-only jämförelse för en deklarerad kabel-/port-/VLAN-felinjicering eller en IPv4-prefix-/statisk-route-/next-hop-ändring, med exakt återställning och tre oberoende Echo-utbyten | Ändra arbetsdokument, automatiska reparationer, orsaksanspråk utan fungerande referens eller nya protokollmotorer |
| `ipv4.py` | Enspårig IPv4-leverans över samma ARP- och Ethernetmotor, explicit next-hop per routesteg, TTL per transitrouter och matchad mottagarport | Returtrafik orkestreras separat i `icmp_ping.py`; inga ICMP-fel, NAT, ACL eller fragmentering |
| `web/model.js` | Explicit UI-modell, enhets- och portkommandon | Adressbaserad länkförutsägelse |
| `web/canvas.js` | SVG-geometri och direktträff på portpunkter | Ändra noders eller länkars identitet |
| `web/app.js` | Användarinteraktion, read-only routingtabell/lookup, fel, Save/Open | Egen implementation av Layer 2/Layer 3-protokoll |

## Testkontrakt

- **Regressionssvit:** schema, negativ input, 47/46/15-identiteter, grafspårning, L2, sessionsbaserad ARP/MAC, read-only route lookup, riktiga filbytes, hash, atomär uppdatering, konflikter och HTTP.
- **Chromiumacceptans:** skapa enheter och portar, skapa exakt en deklarerad kabel, verifiera SVG-portändpunkter, inaktivera kabel, spara, stäng programprocess och browser, öppna igen, kontrollera SHA-256 och exakt projektinnehåll. Direkt webbläsarnätverk eller uttryckligt märkt testbro enligt miljön.
- Tester får inte påstå att simuleringsprotokoll fungerar när den funktionen inte finns.

## Historiska utvecklingssteg – ingen aktiv implementationslista

Den tidigare texten om att först bygga IPv4 forwarding, ICMP Echo och routerfel avsåg en äldre utvecklingsfas och är inte längre en aktuell byggorder. Dessa **avgränsade** mekanismer har senare fått egna kontrakt och kod i `network_core/`. Kontrollera senaste HEAD och tester innan någon ny funktion utlovas. Den äldre beskrivningen av importformat och Layer 2 är också tidsbunden.

**Nuvarande arkitekturprinciper:** En kanonisk modell; explicita portar och kablar; granskade källfakta; en befintlig simuleringskedja; inga gissade uppgifter; separat Save; Linux-exklusiv miljö. För planerad utbildning gäller [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md](PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) och för samlad kvalitetsordning [QUALITY_IMPROVEMENT_PLAN.md](QUALITY_IMPROVEMENT_PLAN.md). Ett framtida ”Incidentverkstaden”-UI är planerat undervisningsinnehåll, **inte** verifierat implementerad produktfunktion.
