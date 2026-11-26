# YadiLab – utvecklingskontrakt

**Beslut 2026-11-26:** [Pedagogisk felsökningsarkitektur](docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) med steg **P0–P7 är formellt avslutad genom användarbeslut**. **Ingen aktiv utvecklingsetapp finns.** Inga äldre QUALITY-, ELK-, import- eller fasroadmaps får återaktiveras som nästa PR utan nytt uttryckligt användarbeslut. Detta dokument är en **operativ regeluppsättning**, inte en parallell plan. [MASTERPROMPT](docs/MASTERPROMPT.md) anger produktmålet.

**Sanningsföreträde:** Senaste uttryckliga användarbeslutet och aktuell kod/test/CI på exakt SHA avgör vad som faktiskt är beslutat respektive implementerat. Dokumentation och gammal PR-historik är aldrig bevis för ett nytt runtimebeteende. Vid konflikt eller saknade fakta: redovisa `UNKNOWN`, `NOT_VERIFIED` eller `UNSUPPORTED`, och avstå från gissningar.

## Plattform och modell

- YadiLab är en **Linux-app**. Windows och macOS är **UNSUPPORTED**: inga portar, builds, kompatibilitetslager, CI-matriser eller supportmål för icke-Linux.
- Bevara **en kanonisk nätverksmodell** och `network_core/model.py::validate_project` som slutlig projektvalidator. All explicit kabel- och portidentitet ska bevaras. Inga påhittade kablar, nätverksenheter, MAC, gateways, VLAN, routes eller IP-adresser baserat på diagramposition, namn, subnät, zon eller LLDP-hypoteser.
- `network_core/config.py::APP_NAME` är enda körbara visningsnamnet. Hårdkoda inte produktnamn i källkod, sökvägar eller fixturer; `.yadilab` bevaras av kompatibilitetsskäl. Projektnamnet får beskrivas i Markdown.
- Bevara befintlig SVG/ELK, Builder, koordinatfria dokumentationsimporter/exporter, VLAN/Ethernet/ARP/IPv4/ICMP/DHCP, existerande felövningar, sessioner, stale-guards och Save/Open. Ny pedagogik får inte skapa en andra simuleringsmotor eller ett nytt generellt datalager.

## Sanning och undervisning

- Lägg **pedagogiskt undervisningslager ovanpå befintlig motor**, inte ett konkurrerande nätverk. Skilj dokumenterad konfiguration, simulerade paket, hypoteser, protokolldefinierade fakta och verkliga kundnätsobservationer.
- En ritad väg eller route lookup bevisar inte paketleverans. Ett ARP-svar är inte ett Echo Reply; en simulerad packet trace är inte live-nätverksdata. Inga fabricerade tabeller, terminalutdata, konfidensprocent eller ”verifierade” slutsatser.
- Följ pedagogikplanens nio exakta rubriker och krav på konkurrerande hypoteser, diagnostiskt motbevisande test och försenat facit. Återanvänd de faktiskt implementerade ICMP-/DHCP-felsökningsmodulerna.
- OSPF/BGP, STP, SNMP, ACL, NAT, IPv6, DNS och liknande kursämnen är **inte därmed native implementerade**. Wireshark, SuzieQ, Batfish, Netshot, NetXMS, FRRouting, containerlab och CLI är bara granskade **statiska utbildningsexempel** eller **frivilliga separata manuella labb**. Ingen exekvering, nätverksskanning, SDK, shell, API-adapter eller runtimeintegration enligt denna plan.

## Import, lagring och UI

- Läs [tekniskt importkontrakt](docs/IMPORT_SOURCE_CONTRACT.md). Läsning av ofullständigt dokument är inte godkänd import. Saknade nödvändiga fakta eller blockerade relationer ska inte trollas bort. Kabel kräver två uttryckliga nod-/portändpunkter. Ett rent L2-projekt ska inte tvingas ha onödiga IPv4-fält.
- Uppladdade JSON-originalbytes ska valideras strikt före normaliserande browserparser; tillåt inga tyst överskrivna dubbla JSON-nycklar. Visa källcell, proveniens, beslut och olösta fel där stödet finns.
- ELK ändrar enbart **presentation**, aldrig deklarerad nätverkstopologi. Ändra inte sparad projektfil utan **uttrycklig Save**. Skydda ID:n, filbytes, SHA-/konfliktskydd, sessionslivscykel och atomärt arbetsytebyte.

## GitHub-arbetsprocess

1. Vid nästa utvecklingsuppdrag: läs faktisk `main`, öppna PR:er, pedagogikplanen, relevant teknisk kod och teststatus. **P0–P7 är CLOSED och ger ingen automatisk nästa uppgift.** Arbeta enbart inom det nya uttryckliga användaruppdragets avgränsning; återaktivera inte äldre roadmap eller historiskt arbetskort.
2. Ha **en aktiv PR åt gången**. `KEEP` är utgångspunkt; en större motor-/schema-/plattform-/integrationsförändring kräver separat uttryckligt beslut. Inga onödiga refaktoreringar eller pentest-/säkerhetskampanjer.
3. Kräv positivt och negativt test med självständigt tekniskt facit. Vid UI-ändring kontrollera verklig Chromium och relevant X11; vid lagring kontrollera verklig fil, SHA, Save/Open och omstart. Relevanta kommandon: `python3 -m unittest discover -s tests -p 'test_*.py' -v`, `npm run check` och `python3 tests/browser_smoke.py`.
4. Merga normalt med squash först när exakt slutlig PR-HEAD har alla obligatoriska kontroller **SUCCESS**, förväntad main är kontrollerad, PR är mergebar och inga blockerande reviews finns. Användarens stående godkännande gäller dessa villkor, **aldrig** FAIL/PENDING, tvångspush eller kringgånget branchskydd.
5. Rapportera faktisk commit/PR/CI, negativa tester, avgränsningar och nästa pedagogiska steg. Vänta inte passivt på CI; inget arbete i bakgrunden utan verktygsstöd.

**Git-historik får bevara historiska planer, men inga gamla planer eller gamla statusfiler ska finnas i den aktiva dokumentationens styrkedja.**
