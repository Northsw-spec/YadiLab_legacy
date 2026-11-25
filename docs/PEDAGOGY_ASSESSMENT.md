# P6 · Automatiserad utvärdering av P1–P5

Kör från rotkatalogen på Linux med Python, Playwright och verklig Chromium,
som i den obligatoriska CI-körningen.

```sh
python3 tests/run_pedagogy_assessment.py
python3 tests/run_pedagogy_assessment.py --output /tmp/pedagogy-assessment.json
python3 -m unittest discover -s tests -p 'test_pedagogy_assessment.py' -v
```

Utvärderingen kör befintlig motor på den kanoniska ICMP-fixturen och återanvänder
det riktade Chromium-testet över direkt HTTP. Den skriver JSON till
standardutdata och till en rapportfil om en sökväg väljs. En avvikelse, en
avbruten körning eller ett fall som inte kördes ger kod 1. CI visar rapporten
i sitt ordinarie teststeg. Appen hanterar ingen rapportdata.

## Fördefinierade referenser

Förväntningarna är handskrivna före körning. Native-kontrollerna läser
paketspår, gränssnitt, nästa hopp, ARP-sändningar och mottagande i motorn.
Browserkontrollerna väljer fördefinierade test och påståenden i produktionens
elevflöde. De läser ej applikationens facit för att avgöra vad som ska godkännas.

| Referensfall | Förutsättning och initial observation | Skiljande test, motexempel och tillåten slutsats | Efterkontroll och källa |
|---|---|---|---|
| Returroute | Den kanoniska ICMP-fixturen ger fungerande Echo. I en kopia saknas route `b:return-to-a`. Källan får inget matchande svar. | Request når `b/eth0`. Returuppslag ger `NO_ROUTE` före ARP. Nästa hopp är en konkurrerande hypotes, som behöver en matchande route och ett ARP-fel. | Efter verifierad återställning ska matchande Reply nå `a/eth0`. Native, [fixture](../web/fixtures/icmp-echo-lesson.json), [RFC 792](https://www.rfc-editor.org/rfc/rfc792). |
| Fel nästa hopp | Samma symptom. Returroute finns i kopian med det avsiktligt felaktiga nästa hoppet `203.0.113.254`. | Returuppslag ger `MATCH`. Motorn skickar ARP Request och får `NO_REPLY`, utan IPv4-sändning på returen. Saknad route och lyckad leverans avvisas. | Återställ det ursprungliga nästa hoppet och verifiera matchande Reply. Native, samma fixture och [RFC 826](https://www.rfc-editor.org/rfc/rfc826). |
| Testval och reparation | Båda fallen ger misslyckad ping och fungerande uppslag för framvägen. | Fel riktning och port räcker inte. En tekniskt giltig jämförelse för fel intervention styrker ingen reparation av returroutefallet. | Kräv riktig returdiagnostik och färskt Echo efter en giltig reparation. Native och Chromium, [ICMP-kontrakt](ICMP_INVESTIGATION.md). |
| Wireshark | Syntetisk fångst visar ARP-fråga utan svar på en punkt. | Svaret kan ha sänts utanför fångsten eller ha uteblivit. Oberoende fångstpunkter under samma försök skiljer hypoteserna. | Kontrollera samma fråga vid båda punkterna. Statiskt, [Wiresharks ARP-referens](https://www.wireshark.org/docs/dfref/a/arp.html). |
| SuzieQ | Tidsbundet, syntetiskt route- och portunderlag. | Matchande route är inte leverans. Jämför färskt route- och ARP-tillstånd för att skilja föråldrad route från fel i adressupplösningen. | Kontrollera samma VRF och nästa hopp. Statiskt, [analysguide v0.24.0](https://github.com/netenglabs/suzieq/blob/v0.24.0/docs/analyzer.md). |
| Netshot | Två syntetiska snapshots visar en VLAN-diff. | En konfigurationsskillnad bevisar inte driftorsaken. Jämför portläge och paketspår för att skilja VLAN-felet från ett returvägsfel. | Verifiera trafik efter en motiverad åtgärd. Statiskt, [konfigurationshistorik v0.25.2](https://github.com/netshot-net/Netshot/blob/v0.25.2/docs/content/user-guide/devices.md#configuration-history). |
| Batfish | Två syntetiska modellspår visar `ACCEPTED` och `NO_ROUTE`. | En skillnad kan ligga i konfigurationen eller i modellunderlaget. Kontrollera snapshot och tolkning innan riktad paketmätning. | Kontrollera verklig trafik separat. Statiskt, [differentialfrågor](https://batfish.readthedocs.io/en/latest/notebooks/differentialQuestions.html). |
| OSPF | Syntetiskt `Init` vid en punkt. | Ensidig Hello från två punkter stöder asymmetri, ej kabelfel. Två DROther med ömsesidigt Hello och `2-Way` är förenligt med normal design. | Följ roller och stabilitet och pröva dataplan separat. Statiskt, [RFC 2328 §§ 7.5, 10.1, 10.5](https://www.rfc-editor.org/rfc/rfc2328). |
| SNMP | Syntetisk GET-timeout. | Lyckat ICMP utesluter inte SNMP-transportfel. Matchande `noSuchObject` vid omprov talar emot total förlust och motiverar kontroll av OID och läsvy. | Upprepa samma GET och kontroll. Statiskt, [RFC 3416 § 4.2.1](https://www.rfc-editor.org/rfc/rfc3416). |
| ACL | Syntetisk, tillåten Request och uteblivet svar från klientens perspektiv. | Samma Reply i den relevanta drop-regeln stöder ett filterfel. Ett svar på en väg som passerar vid sidan av regeln motsäger det. En konfigurationsrad räcker inte. | Verifiera samma Echo-utbyte och träffar efter styrkt korrigering. Statiskt, [nftables](https://netfilter.org/projects/nftables/manpage.html). |

För P5 ingår också ett otillgängligt test i varje lektion. `NOT_VERIFIED`
ska visas och ingen tolkning, åtgärd eller verifiering ska öppnas för det
testet. Kontrollerna av den egna utvärderingen matar in motsägande svar,
fel destination, falsk återhämtning och avslöjade svar i isolerade tester.

## Läs rapporten

- **defined** är referenslistans storlek. **executed**, **PASS**, **FAIL**
  och **NOT_RUN** redovisas per körning. Om Chromium avbryts visas övriga
  fall som inte körda. Ett avbrott kan också göra att det omslutande
  elevflödet rapporteras underkänt.
- **false_diagnosis** räknar utvärderade fall där en felaktig tolkning
  accepterades. **insufficient_evidence** räknar fall där fortsatt diagnos
  eller verifiering spärrades på grund av otillräcklig evidens. **answer_leak**
  räknar fall med för tidigt facit. Varje mätvärde har nämnaren **checked**.
  Ett fall med flera kontroller bidrar en gång till respektive nämnare.
- **surface** skiljer native-kontroller mot tekniskt facit från Chromium-flöden.
  P4 granskar uttryckliga referenspåståenden. Den automatiska kontrollen
  bedömer varken all svensk prosa eller om externa program ger ett visst utfall.
- Reproducerbarhet redovisas med git-commit, träd, ändringsstatus, kommando,
  operativsystem, Python och faktiskt använd Chromium. Full regression
  gäller även DHCP, andra fel och de övriga delarna av applikationen.

Mänsklig inlärningseffekt är **`NOT_VERIFIED`**. P6 använder inga mänskliga
testpersoner. Underlaget gäller tekniska resultat och undervisningslogik
i de definierade fallen.
