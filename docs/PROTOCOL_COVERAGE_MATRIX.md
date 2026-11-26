# YadiLab – protokoll- och produktparitetsmatris

**ABSOLUT SLUTKRAV:** [PT-FULL-001](FULL_PACKET_TRACER_PARITY_CONTRACT.md) är den bindande, obegränsade funktionsparitetskatalogen. **ALL** Cisco Packet Tracer-funktionalitet och ALLA faktiska protokoll-/enhets-/tjänstevarianter på Linux ska finnas och vara testade innan S12/full paritet: inklusive physical/logical, alla deviceprofiler/moduler, full CLI, realtime/simulation, PDU/OSI, Activity Wizard/script/score, IoT/OT, multiuser, extensions och PT-format. **Två enda undantag: inget Windows/macOS-stöd och inget ytterligare tillgänglighets-/keyboard-only-krav.** Alla andra saknade poster är GAP eller BLOCKED tills faktiskt implementerade. Tillfälligt NOT_NATIVE får ALDRIG accepteras som slutstatus. Protokolltabellen nedan är en början, inte ett komplett inventarium av PT.


**Baseline:** main 7dbe2285cde7ea87c08afce1c58d36cd0f5697e7, 2026-11-26. **PT-referens:** Ciscos offentliga [Introduction](https://tutorials.ptnetacad.net/help/default/intro.htm), [Simulation Mode](https://tutorials.ptnetacad.net/help/default/mode_simulation.htm), [What's New 9.0](https://tutorials.ptnetacad.net/help/default/whatsNew.htm), [OT-katalog](https://tutorials.ptnetacad.net/help/default/industrial_otFeatures.htm) samt [8.2 FAQ](https://prelogin-authoring.netacad.com/sites/default/files/cisco-packet-tracer-faq.pdf) för äldre kompletteringar. Detta är en **mål-/gapmatris**, inte ett testresultat på Packet Tracer-installation eller på ännu ej byggda moduler.

**Klassning:** LIMITED_NATIVE = faktisk men avgränsad implementation; NOT_NATIVE = ingen verifierad native motor; NOT_VERIFIED = test/versionsstöd ej självständigt kontrollerat; PLANNED = uttryckligt framtida produktkrav; VERIFIED_NATIVE = endast efter standardförankrade, oberoende positiva/negativa testvektorer och Required CI. PT_DOK = Cisco listar funktionen; betyder inte komplett interoperabilitet. S-nivåer refererar [enda aktiva masterplanen](REMEDIATION_PLAN_2026-11-26.md).

| Domän | Packet Tracer dokumenterad funktion | YadiLab baseline | YadiLab leveransspår och omfångsvillkor |
|---|---|---|---|
| Topologi | Logical workspace, många enheter, device config | LIMITED_NATIVE, fyra kind-typer | S0/S1/S10 – modulära profiler och validerad explicit config |
| Länkar/fysik | Physical workspace, koppar/fiber/längder | LIMITED_NATIVE, explicit up/down-kabel | S1/S7/S10 – längd/fiber/duplex/felmodell med verkliga enheter som referens |
| Ethernet 802.3 | Frames och switching | LIMITED_NATIVE | S2 – FCS/aging/köer endast efter separat definierad fysik |
| VLAN 802.1Q | Access/trunk | LIMITED_NATIVE | S2 – native VLAN, allowed/pruning, dubbel tagg om explicit scope |
| MAC-tabell | Inlärning och forwarding | LIMITED_NATIVE | S2 – aging, flush, portflytt och konkurrerande trafik |
| STP/RSTP | Switchloop-kontroll | NOT_NATIVE, loop avvisas | S2 – BPDU, root/portval, timers, topologiförändring |
| LACP / EtherChannel | Aggregation | NOT_NATIVE | S2 – 802.1AX, bundle-fel, hash och minimilänkar |
| PAgP / DTP / VTP | Cisco-specifika L2-protokoll | NOT_NATIVE | S8 – lagligt specificerade delmängder eller explicit begränsning |
| CDP / LLDP | Neighbor discovery | NOT_NATIVE | S8 – LLDP först, CDP-profil separat |
| 802.1X/EAP | Portautentisering | NOT_NATIVE | S6 – avgränsad tillståndsmaskin med explicita AAA-beslut |
| ARP | IPv4-to-MAC | LIMITED_NATIVE | S2/S3 – cache aging, duplicate IP, timeout, gratuitous ARP |
| IPv4 / CIDR | Forwarding, route lookup | LIMITED_NATIVE | S3 – korrekt forwarding, errors, MTU/fragmentering, ECMP efter beslut |
| ICMPv4 | Echo, errors | LIMITED_NATIVE | S3 – fler typer/koder, error-suppression och korrekt returväg |
| IPv6 / ICMPv6 | L3 + v6 | NOT_NATIVE, schema avvisar v6 | S3 – IPv6, link-local, ND/DAD/SLAAC, RA |
| DHCPv4 | Discover/Offer/Request/Ack | LIMITED_NATIVE | S4 – relay, flera servrar, reservations, decline, renew, expiry |
| DHCPv6 | Stateful/stateless | NOT_NATIVE | S4 – RFC 8415, RA-interaktion, prefix delegation om explicit |
| UDP | Generell datagramtransport | NOT_NATIVE (DHCP har dedikerad codec) | S4 – portar, checksum/length, socketsim, ICMP unreachable |
| TCP | Sessioner, handskakning, tillstånd | NOT_NATIVE | S4 – RFC 9293 state, seq/ack/window, loss/retransmit/teardown |
| DNS | Queries/service | NOT_NATIVE | S4 – A/AAAA/CNAME/MX, TTL/cache, NXDOMAIN, UDP/TCP |
| HTTP / HTTPS | Applikationsflöden | NOT_NATIVE | S4 – HTTP över korrekt TCP; TLS separat testbart kontrakt, aldrig falsk kryptering |
| FTP/TFTP | Filöverföring | NOT_NATIVE | S4 – avgränsade kommando-/datakanaler |
| SMTP/POP3 | E-post | NOT_NATIVE | S4 – protokolltransaktioner över TCP, inte faktisk internetleverans |
| Telnet / SSH | CLI-access | NOT_NATIVE | S4/S10 – inga falska kryptografipåståenden |
| SNMP / Syslog | Management/telemetri | NOT_NATIVE | S4/S8 – MIB/OID, timeouts, logging, counters |
| NTP | Tidssynkronisering | NOT_NATIVE | S4/S8 – simulerade klockor, drift och validerad NTP-beräkning |
| MQTT | Pub/sub IoT | NOT_NATIVE | S4/S9 – transport och broker state |
| RTP/VoIP/H.323/SCCP | Röst/protokoll | NOT_NATIVE | S4/S9 – protokollspecifik delmängd, konvergens och köer |
| RIP v1/v2/ng | Distance vector | NOT_NATIVE | S5 – timers, split-horizon, poisoning, loops, converge |
| OSPFv2/v3 | Link state, multiarea | NOT_NATIVE | S5 – Hello/adjacencies/LSDB/SPF/area/DR/BDR, riktig paketkausalitet |
| EIGRP/EIGRPv6 | DUAL-liknande beteende | NOT_NATIVE | S5 – licens/IP-kontroll, dokumenterad version/avgränsning |
| BGP-4 | eBGP, policy | NOT_NATIVE | S5 – TCP-session, FSM, UPDATE, AS_PATH, eBGP/iBGP, withdraw, filters |
| Route redistribution | Flera routingprotokoll | NOT_NATIVE | S5 – RIB/FIB/AD/metric/policy och loopskydd |
| Multilayer switching / CEF | L3 switch, forwarding | NOT_NATIVE | S3/S5 – RIB/FIB-separation, port/VLAN/SVI |
| ACL / firewall | Standard/extended/named, ZBF, CBAC | NOT_NATIVE | S6 – ordning, implicit deny, direction, stateful tracking |
| NAT/PAT/NATv6 | Translation | NOT_NATIVE | S6 – 5-tuple, hairpin/expiry, ICMP checksum/fragmentgränser |
| GRE / IPsec / ISAKMP | Tunnlar och säkerhet | NOT_NATIVE | S6 – tunnel/MTU, kryptografisk realism deklarerad; ingen låtsas-IPsec |
| AAA / RADIUS / TACACS | Identitet | NOT_NATIVE | S6 – policy, autentisering/auktorisation, failure/timeout |
| QoS L2/L3 | Queues, policing, DiffServ | NOT_NATIVE | S1/S7 – integrerade bytes/länkser/queues/drops, inte fejkad RTT |
| WAN PPP/PPPoE/HDLC/Frame Relay/DSL | Punkt-till-punkt/WAN | NOT_NATIVE | S7 – timers, link handshakes, MTU, avgränsade accessmodeller |
| Trådlöst 802.11/WPA | AP, klient, roaming | NOT_NATIVE | S7 – explicit RF-/kanalmodell, association, kryptogränser |
| Mobil 3G/4G/5G | Accessmodeller | NOT_NATIVE | S7/S9 – pedagogiskt verifierad abstraktion, ingen utlovad mobilstack |
| HSRP / VRRP | Redundant gateway | NOT_NATIVE | S8 – VRRP standardprioritet, HSRP leverantörsavgränsning |
| SPAN/RSPAN, NetFlow | Spegling och flöden | NOT_NATIVE | S8 – härledd från verkliga simulerade paket |
| REP / PRP / PTP | Industriell redundans och tid | NOT_NATIVE | S8/S9 – standard/leverantörsprofil och klockprecision |
| L2NAT | Industriell translation | NOT_NATIVE | S8/S9 – explicit regel, mätbar korrekt pakettransformation |
| Modbus TCP | OT-protokoll, PT9 | NOT_NATIVE | S9 – klient/server register/exception och tidsordning |
| PROFINET | PLC och IO, PT9 | NOT_NATIVE | S9 – kontrollerade delprotokoll och cykeltid, ingen falsk realtidsnoggrannhet |
| CIP EtherNet/IP | Identitet/objekt, PT9 | NOT_NATIVE | S9 – explicit ODVA-objektgräns |
| IEC 61850 GOOSE/SV/MMS | OT/utility, PT9 | NOT_NATIVE | S9 – IEC-standardversion, tids-/länkfel |
| OPC UA | OT-datatjänster, PT9 | NOT_NATIVE | S9 – sessioner, identitet, säkerhetsprofil tydligt klassad |
| PLC / HMI / ladder logic | OT-undervisning, PT9 | NOT_NATIVE | S9/S10 – ofarlig lokal symbolisk process, aldrig anslutning till verklig PLC |
| CLI / konfigurationskommandon | IOS-inspirerad CLI | NOT_NATIVE | S10 – semantiskt kopplad CLI med mode/error/show, ingen IOS-emulator |
| OSI-/PDU-inspektor | Stegvis paketinformation | LIMITED_NATIVE, smal spårvy | S1/S10 – orsaks-ID, bytes, headers, state- och drop-orsaker |
| Realtid/simulation mode | Eventbaserad tid/animation | LIMITED_NATIVE, ingen global event scheduler | S1/S10 – pause/step/replay, deterministisk tid och separat visual speed |
| Aktivitetsskapande / autorättning | Instructor/lab/feedback | LIMITED_NATIVE, enskilda lektioner | S10 – lab authoring, dolda facit, invariants och automatiserad bedömning |
| Multiuser/kollaboration | Samverkande remote clouds, port visibility, offline remote save, autentisering | NOT_NATIVE | S10/S12 + PT-F23 – OBLIGATORISK paritet; säker, användaraktiverad federering på Linux |
| Offline/Linux | Linux-stöd, även andra OS i PT | Linux-only med lokal server | S0/S12 – behåll Linux-only om inte nytt användarbeslut |

## Bindande uppdateringsregel

Varje tillkommande protokoll får en egen rad med: exakt variant/version, RFC/IEEE/IEC eller trovärdig källa, dokumenterat stödomfång, device-profile, state machine, positivt/negativt referensorakel, gränser, fel-/tidsmodell, head-SHA, CI-länk, oberoende jämförelse samt resultatklass. Ingen rad ändras till VERIFIED_NATIVE från enbart plan, mock, logg, diagram eller marknadsföring. Matchad produktparitet kräver att **hela jämförbara övningen** kan genomföras, inte bara att ett paketnamn syns i GUI.

**PT-resultat:** PT_DOK är förhandsinventering. Körbara konkurrentjämförelser med precis Packet Tracer-version och exakt jämförbar labbkonfiguration får markeras VERIFIED_COMPARISON först efter verklig körning; annars NOT_VERIFIED. Ingen tillgång till Ciscos källkod eller upphovsrättsskyddade IOS behövs eller får antas.

## Produktomfattning: alla 29 bindande PT-funktionsfamiljer

Dessa är överordnade grupp-ID, **inte** fulltäckande underfall. S0 ska kartlägga alla dokumenterade och i PT 9.0.1 praktiskt verifierade varianter, kommandon och enheter och ge var och en ett eget testbart under-ID. Ingen funktion försvinner genom att den saknas i denna första tabell. **Alla är GATE_REQUIRED** för FULL_PARITY och S12, utom explicit Linux/keyboard-undantag enligt [PT-FULL-001](FULL_PACKET_TRACER_PARITY_CONTRACT.md).

| ID | PT-funktion som måste nå full paritet | YadiLab aktuell källbas | S-ägare | Slutgrind |
|---|---|---|---|---|
| PT-F01 | Logical workspace, kluster, annotation, diagram | LIMITED_NATIVE | S10 | REQUIRED |
| PT-F02 | Physical workspace, rack, byggnader, plats/ström | NOT_NATIVE | S7/S10 | REQUIRED |
| PT-F03 | Alla modeller och enhetsprofiler | LIMITED_NATIVE | S2–S10 | REQUIRED |
| PT-F04 | Alla moduler, portar, medier, kablar | LIMITED_NATIVE | S2/S7/S10 | REQUIRED |
| PT-F05 | Power-on, reboot, startup/running config | NOT_NATIVE | S1/S10 | REQUIRED |
| PT-F06 | Full PT-device CLI/GUI semantik | NOT_NATIVE | S10 | REQUIRED |
| PT-F07 | Realtime/Simulation mode med eventkontroll | LIMITED_NATIVE | S1/S10 | REQUIRED |
| PT-F08 | Simple/Complex/Periodic PDUs, flera scenarios | LIMITED_NATIVE | S1/S10 | REQUIRED |
| PT-F09 | OSI/PDU header/device status och eventlogg | LIMITED_NATIVE | S1/S10 | REQUIRED |
| PT-F10 | PKT/PKZ/PKA format och versionsinteroperabilitet | NOT_VERIFIED | S10 | REQUIRED |
| PT-F11 | Activity Wizard, scripting, scoring, password | LIMITED_NATIVE | S10 | REQUIRED |
| PT-F12 | IoT Things, smart home/city/industrial/power | NOT_NATIVE | S9/S10 | REQUIRED |
| PT-F13 | MCU/SBC, sensorer, analog/digital, Python/JS | NOT_NATIVE | S9/S10 | REQUIRED |
| PT-F14 | OT PLC/HMI/historian/Cyber Observer | NOT_NATIVE | S9/S10 | REQUIRED |
| PT-F15 | OT Modbus, PROFINET, CIP, IEC61850, PTP, PRP | NOT_NATIVE | S8/S9 | REQUIRED |
| PT-F16 | Ethernet, VLAN, L2, STP/RSTP/LACP, IPv4/v6, ND/ICMP | LIMITED_NATIVE | S2/S3 | REQUIRED |
| PT-F17 | RIP/EIGRP/OSPF/BGP/redistribution | NOT_NATIVE | S5 | REQUIRED |
| PT-F18 | TCP/UDP/DHCP/DNS/HTTP/VoIP/alla PT-apps | LIMITED_NATIVE | S4/S10 | REQUIRED |
| PT-F19 | ACL/NAT, firewall, AAA, GRE/IPsec/IPS | NOT_NATIVE | S6 | REQUIRED |
| PT-F20 | CDP/LLDP/SNMP/Syslog/NTP/NetFlow/HA | NOT_NATIVE | S4/S8 | REQUIRED |
| PT-F21 | WAN/PPP/Frame Relay/DSL, Wi-Fi, mobil, radio | NOT_NATIVE | S7 | REQUIRED |
| PT-F22 | QoS, köer, överföring, delay, shaping | NOT_NATIVE | S7 | REQUIRED |
| PT-F23 | Multiuser remote networks / save / port view | NOT_NATIVE | S10 | REQUIRED |
| PT-F24 | Extensions / ExApps / utvecklar-API | NOT_NATIVE | S10 | REQUIRED |
| PT-F25 | Labb/exam/assessment/script/inbyggda övningar | LIMITED_NATIVE | S10 | REQUIRED |
| PT-F26 | Miljö/fysik/ström/IoT-automation | NOT_NATIVE | S7/S9/S10 | REQUIRED |
| PT-F27 | Komplexa nät och reproducerbar skalning | NOT_VERIFIED | S11 | REQUIRED |
| PT-F28 | Linux installation, backup, export, full appflöde | LIMITED_NATIVE | S10/S12 | REQUIRED |
| PT-F29 | Alla återstående PT-underfall med upptäcktskrav | NOT_VERIFIED | S0/S11/S12 | REQUIRED |

**Inga tillåtna slutundantag:** S12 får inte godkännas så länge något ID eller något faktiskt deltest är OPEN, NOT_NATIVE, PARTIAL, NOT_VERIFIED eller BLOCKED. Öppna licens-/formatproblem gör FULL_PARITY omöjlig att påstå tills de löses lagligt. RFC-/IEEE-/IEC-testorakel plus verkligen körda jämförbara Packet Tracer-scenarier krävs, inte endast hänvisning till en marknadsföringslista. Uppdatera varje post med exakt YadiLab SHA, PT-build, evidenslänk och PASS/FAIL.
