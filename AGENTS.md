# YadiLab – utvecklingskontrakt

**Aktivt beslut 2026-11-26:** [Åtgärdsplanen A0–A10](docs/REMEDIATION_PLAN_2026-11-26.md) är YadiLabs **enda aktiva utvecklingsplan**, uttryckligen godkänd av användaren och giltig tills verifierad A10-slutrevision formellt avslutar den. [Teknisk granskning 2026-11-26](docs/reviews/TECHNICAL_REVIEW_2026-11-26.md) är primärkällan till dess C01–C18. [Pedagogikprogrammet P0–P7](docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md) förblir **CLOSED** och bevaras enbart som historisk roadmap och pedagogiskt kvalitetskontrakt. Inga äldre QUALITY-, ELK-, import- eller fasroadmaps får återaktiveras automatiskt. Detta dokument innehåller operativa regler, inte en parallell plan. [MASTERPROMPT](docs/MASTERPROMPT.md) anger produktmålet.

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

1. **Vid nästa YadiLab-”fortsätt” eller ny konversation:** läs faktisk `main`, öppna PR:er och slutlig CI; läs den [enda aktiva åtgärdsplanen A0–A10](docs/REMEDIATION_PLAN_2026-11-26.md) samt aktuella kontrakt. Hitta första faktiskt ej färdiga godkända arbetskort enligt beroenden; **A0 är DONE** ([PR #169](https://github.com/Northsw-spec/YadiLab/pull/169), main `fcf81716285ef3a4d927d3ac05556b5c2fb6f7f5`). **A1 är IN_PROGRESS**: granska den senaste A1-PR:n, [G1–G7-kontraktet](docs/architecture/A1_GUARD_CONTRACT_2026-11-26.md), negativt testad `architecture-guard` och [aktivt GitHub-ruleset](https://github.com/Northsw-spec/YadiLab/rules/27419615). **A1 är BLOCKED tills `architecture-guard` finns som Required i main-regeln och det har verifierats genom GitHub API**. Påbörja inte A2, A3 eller A4 innan denna spärr är löst; därefter A2/A3/A4/A5/A6/A7 och A10 enligt verkliga beroenden. A8 (mänsklig studie) och A9 (ny protokollmotor) kräver **separat explicit godkännande** och får inte initieras genom ett generellt 'fortsätt'. P0–P7 är CLOSED, inte en alternativ arbetskö.
2. Ha **en aktiv PR åt gången**, begränsad till ett godkänt A-kort med angivna C01–C18-ID, ett konkret scope, positivt och negativt test samt rollback. `KEEP` är utgångspunkt; en större motor-/schema-/plattform-/integrationsförändring kräver separat uttryckligt beslut. Inga onödiga refaktoreringar eller pentest-/säkerhetskampanjer. **Före A3/A4 ska A1:s G1–G7 vara implementerade och separat `architecture-guard` vara Required i branchskyddet.** Dagens ES-importgraf-test räcker inte som anti-monolitspärr; påstå aldrig att G1–G7 finns innan verklig kod, negativa tester och GitHub-regel verifierats.
3. Kräv positivt och negativt test med självständigt tekniskt facit. Vid UI-ändring kontrollera verklig Chromium och relevant X11; vid lagring kontrollera verklig fil, SHA, Save/Open och omstart. Relevanta kommandon: `python3 -m unittest discover -s tests -p 'test_*.py' -v`, `npm run check` och `python3 tests/browser_smoke.py`.
4. Merga normalt med squash först när exakt slutlig PR-HEAD har alla obligatoriska kontroller **SUCCESS**, förväntad main är kontrollerad, PR är mergebar och inga blockerande reviews finns. Användarens stående godkännande gäller dessa villkor, **aldrig** FAIL/PENDING, tvångspush eller kringgånget branchskydd.
5. Rapportera faktisk commit/PR/CI, negativa tester, eventuella arkitekturgränser, berörda C01–C18-ID och **nästa ej färdiga A-kort**. Uppdatera status-/evidenstabellen i den **enda aktiva planen** i samma PR som arbetet färdigställs. Beteckna inte dokumentation eller planad guard som implementerad. Vänta inte passivt på CI; inget arbete i bakgrunden utan verktygsstöd.

**Git-historik får bevara historiska planer, men inga gamla planer eller gamla statusfiler ska finnas i den aktiva dokumentationens styrkedja.**
