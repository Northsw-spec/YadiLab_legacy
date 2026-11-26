# ADR-0002 – Bygg helt ny nätverksmotor; skydda endast verifierbara produktkontrakt

**Datum:** 2026-11-26. **Status:** GODKÄNT ARKITEKTURBESLUT, INTE IMPLEMENTERAT. **Ersätter ADR-0001:s antagande om återanvändning av gamla protokollmotorer.** Bevarar [PT-FULL-001: hela Cisco Packet Tracer och mer](../FULL_PACKET_TRACER_PARITY_CONTRACT.md) och [enda aktiva huvudplanen](../REMEDIATION_PLAN_2026-11-26.md).

## Bindande beslut

**KASTA DEN GAMLA NÄTVERKSMOTORN SOM KODGRUND.** Bygg en egen, fristående, extensibel diskret händelsemotor i `network_core/engine/` med en enda gemensam virtuell tid, port- och device-state, händelsekö, paket-, dataplans- och kontrollplanslogik. Inga importer av `EthernetFabric`, `ArpSession`, `IPv4Trace`, `DhcpSession` eller gamla runtime-registries i nya motorpaketet. Gammal scheduler-wrapper kring hela gamla paketöverföringar är inte tillåten. Inga separata nätverksmotorer får finnas aktiva för samma användarscenario.

**KASTA INTE GAMMAL PRODUKTIONSKOD FÖRE GODKÄND ERSÄTTARE.** Legacy får fortsätta betjäna användaren tills ny motor bevisat minst samma korrekta användarflöden i verkliga testfall och oberoende protokollorakel. Ny motor körs under tiden endast i isolerade testfixturer, med ingen delad mutable state eller produktionsfeatureflag. Gör sedan en tydlig EN-gångs cutover av användarsynlig simulering och pensionera legacy-filer med versionslåsta substitutionskvitton. En cutover får inte ske vid blandad/tvetydig sessionsägare.

## Behåll endast detta – med verifierade gränser

| Del | Beslut | Beviskrav |
|---|---|---|
| `storage.py`, `json_boundary.py` | **Behåll externt projekt-/Save/Open/SHA-kontrakt** | Binär/JSON-källtrogenhet, atomära writes, konflikter, säkerhet och återöppning |
| CSV/XLSX/ODS/import och proveniens | **Behåll gränssnitt och dataförlustskydd** | Oberoende positiva/negativa tester och v1.0–v1.4-kompatibilitet |
| `model.py` | **Behåll befintlig validering för gamla projekt** | Nytt schemav2/device-capabilities måste definieras separat utan att förstöra lagrade dokument |
| `web/` UI, SVG/ELK, Builder, lektioner | **Behåll produktvärdet, inte gamla nätverksresultat** | Riktig Chromium Save/Open, visuell och sessionsmässig regression, inga UI-fabricerade paket |
| Nuvarande Ethernet/ARP/IPv4/ICMP/DHCP bytecodecs | **Enbart referenskandidater tills självständiga RFC-/IEEE-test är godkända** | Kända begränsningar (Ethernet multicast, IPv4 protokoll/fragment/options m.m.) får inte ärvas. Ny motor har egna codecs |
| `ethernet.py`, `arp.py`, `ipv4.py`, `routing.py`, `icmp_ping.py`, `dhcp.py`, `dhcp_registry.py`, `simulation.py` och övriga legacy-protokoll-/sessionsmotorer | **Pensionera efter cutover** | Inte en rad måste räddas för dess egen skull; behåll endast korrekt testad EXTERN semantik |
| Testsvit och Required CI | **Behåll skydd och oberoende orakel** | Gammalt test får ersättas när ersättning täcker relevanta positiva, negativa och motstridiga krav |

**Kända gränser:** Dagens tester bevisar stabila kontrakt inom sin täckning; de kan inte garantera att en framtida motorombyggnad blir regressionsfri. Allt som saknar bevis markeras `NOT_VERIFIED`, inte säkert.

## Ta bort ARTIFICIELLA utvecklingshinder, inte säkerhetsskydd

- **Starta S1-POC0 direkt efter denna ADR/guard-PR:s Required CI/merge.** Fullständig S0-PT-inventering, hela A3/A4-modulariseringen, A5:s samtliga orakel och A7:s slutmatris får utvecklas i egna kort; de är **inte blockerare** för en isolerad scheduler.
- Nya motorpaket får införas under `network_core/engine/`. Arkitekturspärren ska inventera backendkällkod **rekursivt**. Registrerade gamla moduler/tester får pensioneras med ett **append-only retirement receipt**: gammal fil, levande ersättare, registrerat acceptanstest, beslutsdokument som nämner båda. Inget godkänt substitutionskvitto = fortsatt fail-closed.
- Kritiska styr-/säkerhetsfiler, Required checks, oberoende tester, användardata och real Chromium Save/Open får **inte** försvagas för att underlätta migration.
- Ingen produktionscutover förrän nya L2/ARP/IPv4/ICMP/DHCP fungerar ihop på EN klocka/EN state och API-/sessions-/dataregressioner är gröna.

## Föreskriven teknisk leverans

**POC0:** monotont heltals-`time_ns`, stabilt `event_id`, cancel, seeded PRNG, deterministisk trace i skilda processer, overflow- och zero-time-livelock-guards samt resursspärra. **POC1:** självständig host–switch–host TX/RX med flera tidsordnade events, VLAN-isolering, ARP request/reply, port-/länkfel mellan events, separat standardorakel. **Därefter:** ny L2/IPv4/ICMP/DHCP-core i egna delmoduler, go/no-go, EN produktionscutover, revisionssäkra retirement receipts. **Sedan:** S2–S12 med varenda Cisco Packet Tracer-funktion, bättre teknisk korrekthet och öppet redovisade gap tills verifierat.

**Norm:** Bevara produkten och bevisen. **Inte** den gamla simuleringens exekveringskod. Ingen absolut regressionssäkerhet utan provning; ingen falsk Packet Tracer-paritet.
