# QUALITY-003 – Verifieringsprotokoll och återstående begränsningar

**Datum:** 2026-11-23 (ISO)  
**Källbas efter fyra test-PR:er:** `main@a41f9d2dd866dd2069c547bc98677c4dc84505ca`  
**Status 2026-11-23:** **ACCEPTED – VERIFIED SUPPORTED SUBSET**, verifierad mot `main@ba674047e779750f5c8efa7739cf0f80a26fd5d6`, mandatory `unit-tests` SUCCESS i GitHub Actions run `45238708767`. Ingen generell RFC-/IEEE-överensstämmelse utlovas. Rapportens äldre CI-anteckningar nedan är historiska kontrollpunkter; slutresultatet står i §4.

## 1. Metod och källgräns

Oberoende förväntningar för paketspecifika bytes, checksummor och tids-/prefixgränser skrevs i [PROTOCOL_REFERENCE_MATRIX.md](PROTOCOL_REFERENCE_MATRIX.md) före testimplementation och jämfördes i nya `tests/test_protocol_reference_*.py`. De kommer från explicit publicerade RFC-/IEEE-format och manuellt härledda förväntade resultat för deklarerade testtopologier, **inte** från produktionsmotorns egna utdata. Delar som använder befintliga testfixturer är självständiga endast i sina assertions/förväntningar; de är **inte** verifierade mot en separat referensrouter, packet capture eller riktig nätverksutrustning.

Metoden avser endast den **implementerade och uttryckligen begränsade simulatorn**, inte full RFC-/IEEE-konformitet. Inga verkliga kablar, aktiva NIC:ar, nätverk eller företagsunderlag användes.

### CI-spårning — 8/8 obligatoriska push-/PR-körningar SUCCESS

| Del | PR | Exakt PR-HEAD | Push-run | PR-run | Observation |
|---|---|---|---|---|---|
| 1: fasta paketvektorer | #100 | `82fb026185304259a996ea583866cc74b0d75c5b` | `45201982583` | `45202097251` | Båda `unit-tests` SUCCESS, därefter squash merge |
| 2: Ethernet/VLAN/ARP | #101 | `db8524b58b6b03e56841224e20292f369b2a2356` | `45204622062` | `45204688150` | Båda `unit-tests` SUCCESS, därefter squash merge |
| 3: IPv4/ICMP/DHCP | #102 | `7b76369bf947091f4e9a7b252fae34642158918e` | `45207710099` | `45207788245` | Båda `unit-tests` SUCCESS, därefter squash merge |
| 4: prefix/metamorfa tester | #103 | `b2a35f7f61fa133f8b4c0b6fd754d167927e7107` | `45232003251` | `45232018225` | Båda `unit-tests` SUCCESS, därefter squash merge |

**Vad SUCCESS bevisar:** körning av `.github/workflows/ci.yml` på var och en av de fyra verifierade PR-HEAD:arna; det workflowet omfattar full Python unittest discovery, `npm run check`, riktig Chromium/Save-Open, X11 PRIMARY, ELK-browserregressioner. Den här rapporten påstår **inte** att en viss körning på en *annan* SHA var PASS.

**Separat `main`-grind, nu verifierad:** `main@a41f9d2dd866dd2069c547bc98677c4dc84505ca` fick SUCCESS i run `45235004665`; därefter mergades rapport-PR #104 efter båda obligatoriska `unit-tests`-körningarna SUCCESS på HEAD `022434353def6db0b0ae6c8742c3ee708cb04b5b`. Den efterföljande main-commiten `ba674047e779750f5c8efa7739cf0f80a26fd5d6` fick **SUCCESS** i run `45238708767` (GitHub Actions app `15368`). Kontrollerna är skilda och tillskrivs endast respektive exakta SHA. En ny PR för statusuppdatering har alltid egen separat CI-/mergegrind.

## 2. Regelklass: förväntat kontra observerat

| Klass | Oberoende facit / standard | Testfall (ny oberoende testfil) | Observerad testutgång | Gräns |
|---|---|---|---|---|
| **3A Ethernet** | Ethernet II `08 00`, 60 bytes utan FCS; okänd unicast flood `la/lb/lc`, därefter MAC-learning och riktad unicast; urkopplad `lb` ger ingen mottagare `b` | `test_protocol_reference_vectors.py`, `test_protocol_reference_forwarding.py`, `test_protocol_reference_boundaries.py` | Testassertioner uppfyllda i PR #100, #101, #103 | Ingen faktisk 802.1D/STP-lösning; switchloop avvisas |
| **3B VLAN** | IEEE 802.1Q single C-tag `81 00 00 25` för VID 37; VLAN 10/20 separata flood-domäner; blockerad VLAN 20 får `TRUNK_NOT_ALLOWED` | `test_protocol_reference_vectors.py`, `test_protocol_reference_forwarding.py` | Testassertioner uppfyllda i PR #100, #101 | Inget native VLAN, QinQ, STP eller fullständig 802.1Q-stack |
| **3C ARP** | RFC 826: 28-byte Ethernet/IPv4 ARP request; bara nådd matchande adress svarar, cache uppdateras först efter reply, VLAN-isolation kan ge `NO_REPLY` | `test_protocol_reference_vectors.py`, `test_protocol_reference_forwarding.py` | Testassertioner uppfyllda i PR #100, #101 | Inget proxy ARP, gratuitous ARP, automatisk cache-aging |
| **3D IPv4/routing** | RFC 791/1071/1812/3021: checksum, TTL, längsta prefixet; /30 nät- och broadcastgräns, /31 två ändpunkter enligt uttryckligt stöd, /32 exakt host-route; returväg krävs för Echo | `test_protocol_reference_vectors.py`, `test_protocol_reference_l3_dhcp.py`, `test_protocol_reference_boundaries.py` | Testassertioner uppfyllda i PR #100, #102, #103 | Simulatorns /31-test över en uttrycklig switch-topologi bevisar inte allmän RFC 3021 point-to-point-implementering |
| **3E ICMP** | RFC 792: Echo request/reply inkl. ID/sekvens/checksum; exakta 36-byte type 11/0 och 3/0; felmeddelande är inte Echo Reply; falsk `REPLIED` vid saknad returroute förbjuden | `test_protocol_reference_vectors.py`, `test_protocol_reference_l3_dhcp.py`, `test_protocol_reference_boundaries.py` | Testassertioner uppfyllda i PR #100, #102, #103 | Inga andra ICMP-routerfel/-koder eller RTT-mätning |
| **3F DHCP** | RFC 2131: BOOTP/DHCP 300-byte DISCOVER och OFFER-fält, fyra DORA-överföringar; BOUND endast efter ACK; vid 80s lease T1=40s, T2=70s, expiry=80s; ingen klockrörelse utan `advance`; unik IP inom sessionspool | `test_protocol_reference_vectors.py`, `test_protocol_reference_l3_dhcp.py`, `test_protocol_reference_boundaries.py` | Testassertioner uppfyllda i PR #100, #102, #103 | Inget DHCP-relay; realtid, geografisk miljö, produktions-DHCP och godtyckliga RFC-varianter ej verifierade |

**Kompletterande tidigare tester:** `tests/test_ethernet.py`, `test_vlan.py`, `test_arp.py`, `test_connected_routing.py`, `test_ipv4_host_address.py`, `test_ipv4_forwarding.py`, `test_icmp_echo.py`, `test_icmp_errors.py`, `test_dhcp_dora.py`, `test_dhcp_registry.py`, `test_dhcp_renewal.py`, `test_dhcp_link_fault.py`. Dessa täcker fler negativa varianter, men **räknas inte om till oberoende tester** utan att de faktiskt får egna externa facit.

## 3. Metamorfa egenskaper — separat observation

- **Kabelbortfall:** en avstängd nödvändig länk kan inte ge ett lyckat Echo och ingen ersättningskabel får genereras. PR #103 PASS.
- **Irrelevant nod och diagramgeometri:** en oansluten host och ändrade X/Y eller nodordning påverkar inte det deklarerade routing-/dataplansvaret. PR #103 PASS.
- **VLAN-barriär:** VLAN 20 nekas där trunkens ingress bara tillåter VLAN 10; ingen falsk VLAN-övergång. PR #101 PASS.
- **Ingen returroute:** ett levererat Echo Request utan fungerande Echo Reply ska ge `REPLY_FAILED`, inte `REPLIED`. PR #102 PASS.
- **Beständig Save/Open:** separat ny ProjectStore läser samma ID:n och nätverksbeteende; diagnostikkörningarna påverkar inte de sparade bytesen/SHA-256. PR #103 PASS.
- **DHCP state:** utebliven T1/T2-delivery får inte förlänga lease; virtuell tid ändras bara av uttryckligt anrop; pool med två adresser får inte dela ut en tredje. PR #102/#103 PASS.

Alla ovanstående PASS betyder att exakt dessa tester rapporterade godkända assertions i grön CI. De bevisar inte att okända, ej specificerade fel är uteslutna.

## 4. Återstående beslut och acceptans

1. **Obligatorisk slutgrind – UPPFYLLD:** `main@a41f9d2dd866dd2069c547bc98677c4dc84505ca` → run `45235004665`: **SUCCESS**. Efter PR #104: `main@ba674047e779750f5c8efa7739cf0f80a26fd5d6` → run `45238708767`: **SUCCESS**. Båda körningarna har slutförts av rätt GitHub Actions-app.
2. **Rapport-PR – UPPFYLLD:** PR #104, sista HEAD `022434353def6db0b0ae6c8742c3ee708cb04b5b`, hade både push-/PR-`unit-tests` SUCCESS; squash-merge till `ba674047e779750f5c8efa7739cf0f80a26fd5d6`. Ingen produktionskod, testgrind eller protokollmotor ändrades.
3. **Beslut – ACCEPTED för dokumenterad begränsad stödomfattning:** Fyra förhandsdefinierade referensdelar 3A–3F och specificerade metamorfa invarianttester har green checks på respektive exakta HEAD, och efterföljande main-CI har godkänts på rapportens slutcommit. Inga oförklarade avvikelser i dessa tester är kända i den verifierade revisionen. **Alla andra regler/protokollvarianter är NOT_VERIFIED eller UNSUPPORTED**, inte godkända per automatik. Extern packet capture eller referensrouter ingick inte och kan därför inte påstås vara verifierad.
4. **QUALITY-002 är separat oavslutad:** den avsiktligt röda PR #99 stängdes utan merge; GitHub rapporterade `blocked`, men ett icke-muterande regler-/enforcementbevis kunde inte hämtas (403). Status för QUALITY-002 förblir **ENFORCEMENT NOT_VERIFIED**, inte PASS.
5. **Nästa etapp:** QUALITY-004/4A får nu påbörjas som **READ_ONLY-arkitekturrevision** med en spårbar ansvarskarta, KEEP som standard och inga produktionskodändringar utan reproducerad defekt. QUALITY-002:s separata enforcement-grind förblir öppen.

**Känd verifieringslucka:** oberoende laboratoriemätning mot extern referensstack eller riktig utrustning har inte genomförts, inte heller heltäckande fuzz-/kombinatorisk täckning. Dessa resultat får inte beskrivas som PASS. Unsupported: full STP, IPv6 NDP, TCP/UDP-tjänster, NAT, DHCP relay, godtyckliga ICMP-felkoder och verklig nätverkskommunikation. **Linux är enda målplattform; Windows och macOS är UNSUPPORTED.**
