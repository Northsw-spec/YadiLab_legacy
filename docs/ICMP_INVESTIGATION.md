# ICMP/IPv4: dolt fel och evidensstyrd felsökningsövning

## Funktionellt kontrakt

Övningen genomför *inte* en generisk grafbaserad reachability-kontroll.
`EchoExchange` skickar ett riktigt serialiserat ICMP Echo Request
genom den dokumenterade `IPv4Trace`, `ConnectedRoutingTable`,
`ARPResolver` och `EthernetFabric`. För en giltig **baslinje**
krävs också ett korrekt matchat Echo Reply på ursprunglig klientport.
Utan en sådan faktiskt verifierad referens avvisas övningen med HTTP 422.

Övningen fungerar mellan routade nät och mellan två hosts i samma
dokumenterade subnät via en uttryckligen deklarerad switch. I LAN
används direktansluten route lookup utan statisk route eller router.
Endast fel från existerande dokumenterad konfigurering erbjuds:
`LINK_DISABLED`, `PORT_DISABLED` (på använd, aktiverad switchport),
`ACCESS_VLAN_CHANGED`, `IPV4_HOST_ADDRESS_CHANGED`,
`IPV4_PREFIX_CHANGED`, `STATIC_ROUTE_REMOVED` och
`STATIC_NEXT_HOP_CHANGED`. I LAN kan kabel, switchport, access-VLAN,
destinationshostens IPv4-adress eller hostens nätmask bli det enda
dolda felet. Ett annat dokumenterat VLAN krävs för VLAN-fel.
Statiska route- och next-hop-fel hör till routade fall.
Motorn bygger kandidater utifrån baslinjens
faktiskt använda kablar, aktiva switchportar och dokumenterade switch-VLAN/statiska routes.
Prefixfel får bara väljas på ett uttryckligt aktivt IPv4-gränssnitt
längs en faktiskt observerad ICMP-paketväg. Kandidaten väljer den
minsta snävare nätmask (högst /30) som gör att minst en tidigare
on-link peer med dokumenterad IPv4 faller utanför gränssnittets
subnät. Om masken ogiltiggör en statisk next-hop eller inte bryter ett
verkligt simulerat Echo Request/Reply avvisas kandidaten. IP-adressen
ändras inte och inga nya gateways, routes eller kablar uppfinns. En
snävare mask som fortfarande tillåter Echo, till exempel `/24` till
`/25` för `192.168.10.10` och `192.168.10.20`, avvisas. Felet kan
ligga på käll- eller destinationshosten: i det senare fallet kan
Request levereras trots att returvägen ger `NO_ROUTE`. Då skickas
ingen ARP-förfrågan i den riktningen. `MATCH` i en riktning bevisar
inte att Echo Reply kan återvända.

Fel värdadress behåller prefixet men gör att ARP till den ursprungliga
destinationsadressen saknar svar. Kabelavbrott och fel access-VLAN
påverkar den deklarerade Layer 2-vägen. Slutrapporten namnger den
verifierade konfigurationsändringen och visar uppmätt `NO_ROUTE`
eller ARP-status.

Ett **felaktigt statiskt next-hop** väljs endast för en uttryckligt
konfigurerad route som den riktiga lyckade ICMP-baslinjen faktiskt
använde. Ett begränsat urval av oanvända *unicast*-värdadresser inom
routens deklarerade utgångsgränssnitts subnät prövas deterministiskt.
Den valda alternativa adressen är en avsiktligt felaktig konfiguration,
**inte** ett påstått existerande nätverksobjekt eller dokumenterad
gateway. Redan dokumenterade gränssnittsadresser, egen IPv4, nät-/
broadcastadress, ursprungligt next-hop och ogiltiga on-link-adresser
utesluts. Om inget tillåtet alternativ finns startas inget sådant
felcase. Kandidaten kräver därutöver en faktisk modellbaserad
`ARP_FAILED` med `NO_REPLY`; route lookup `MATCH` betyder
aldrig att nästa hopp svarar.

En kandidat accepteras bara om den existerande `compare_fault`
bekräftar en lyckad baslinje, misslyckad paketleverans med just det
felet och återställd verklig Echo-kommunikation i en **oberoende
paketinstans**. Orelaterade, ogiltiga eller redundant konfigurerade
förändringar kan inte bli övningar. Slumpningen väljer endast bland
redan verifierade kandidater och exponerar inte felvalet.

Ingen projektdokumentation ändras av simuleringen. Det dolda felet
injekteras bara på en validerad privat kopia av den ursprungliga
kanoniska modellen. Klientens privata felnamn och målpunkt är
oåtkomliga via publika start-/probe-/diagnose-svar.

## Guidad kursbank (P3)

De neutrala elevvalen **Fall A** och **Fall B** använder samma kanoniska
[övningsprojekt](../web/fixtures/icmp-echo-lesson.json). Baslinjen
och den oberoende återställningen ska båda ge ett matchande Echo Reply från
`b/eth0` till `a/eth0`. Öppningen för båda fallen visar att ett giltigt
Echo Reply uteblev. Paketens riktning och stoppunkt visas först vid mätning.

| Handledarens facit | Ping i felkopian | Uppslag från `b` till `192.0.2.10` |
|---|---|---|
| A. Saknad statisk returroute | Request `DELIVERED`, Reply `NO_ROUTE` före ARP | `NO_ROUTE` |
| B. Fel nästa hopp i samma statiska returroute | Request `DELIVERED`, Reply `ARP_FAILED`. Ett retur-ARP skickas och ger `NO_REPLY`. | `MATCH` via `203.0.113.254` |

I B ändras bara nästa hopp i övningskopian. Adressen är en avsiktligt
felaktig parameter från det befintliga Echo-regressionstestet. Den
representerar ingen deklarerad enhet. `MATCH` bekräftar valet av route
och ARP-spåret visar vad som hände vid adressupplösningen.

Startanropet använder frivilligt `lesson` med det neutrala ID:t
`echo-reply` (A) eller `echo-reply-b` (B). Utelämnat fält ger ordinarie
dold övning. Båda fallen kräver simulerat Echo, returuppslaget ovan och
portkontroll på `b/eth0`. Proberna visar mätvärden. Feltypens facit,
auktoritativt route-ID och åtgärd visas efter verifierad återställning.
Elevens hypotes, val av första test och anteckning hör till den
tillfälliga webbsessionen.

[Motor- och HTTP-tester](../tests/test_icmp_lesson.py) · [Chromium-test för båda fallen](../tests/browser_icmp_lesson.py)

## Begäran och observerbara svar

`POST /api/icmp/investigation/start` kräver exakt:

```json
{
  "project": {},
  "sourceNode": "a",
  "sourcePort": "eth0",
  "destinationIpv4": "203.0.113.20",
  "ttl": 5
}
```

Projektobjektet måste valideras mot den kanoniska modellen.
`sourceNode` och `sourcePort` måste identifiera ett verkligt
dokumenterat, aktivt och MAC/IP-konfigurerat gränssnitt.
`ttl` måste vara ett *äkta* heltal 2..255, inte bool/string. Det är **Echo Request TTL**. De oberoende Echo Reply-paketen använder simulatorns öppet deklarerade **syntetiska responder-TTL 64** i detta övningsflöde; det är inte ett verkligt OS-/leverantörsvärde och det beror inte på Request TTL.
Måladressen måste vara en giltig och av motorn faktiskt nåbar
IPv4-destination innan felinjektion. En lyckad start ger ett opakt
`sessionId`, käll-/mål-ID:n, mätantal, hypotesstatus, DHCP-bevisläge,
samt `ephemeral=true`. **Ingen** intern feltyp, reparationsoperation
eller simulerad felpunkt exponeras.

`POST /api/icmp/investigation/probe` kräver exakt
`sessionId`, ursprungligt `project`, `probe` och `target`.

| `probe` | `target` | Resultat |
|---|---|---|
| `address` | `{}` | Dokumenterad IPv4 och portstatus; adressursprung `UNKNOWN` och DHCP-kontroll `NOT_VERIFIED` |
| `ping` | `{}` | Simulerat ICMP Echo: Request/Reply-status, route-/ARP-steg, VLAN-drops och simulerade transmissioner på deklarerade kablar. `routerError` är antingen `null` eller en separat typ/kod och returevidens för ett av motorn genererat ICMP-routerfel. `receivedAtSource=true` kräver faktisk simulerad returleverans; ett genererat men förlorat fel får aldrig presenteras som observerat av källan. |
| `route` | `{"nodeId":"a","destinationIpv4":"203.0.113.20"}` | Simulerad longest-prefix route lookup samt separat dokumenterade statiska routes med route-ID/next-hop, för att skilja `NO_ROUTE` från `MATCH` med ARP-fel |
| `link` | `{"linkId":"la"}` | Dokumenterat jämfört med simulerat länktillstånd och deklarerade ändpunkter |
| `port` | `{"nodeId":"sw-left","portId":"a"}` | Dokumenterat kontra simulerat administrativt portläge och IPv4/CIDR (eller null för port utan IP); inte live-telemetri |
| `vlan` | `{"nodeId":"sw-left","portId":"a"}` | Dokumenterad kontra simulerad explicit VLAN-konfiguration |

`route` får endast slå upp **källans eller destinationens egen IP**
inom samma övning och på faktiskt existerande host/router. Detta
möjliggör att särskilt granska returvägen från destinationen mot
ursprungsklienten. Inga generiska rutter eller graf-baserade hop
påstås vara verifierade. `documentedStaticRoutes` är en kopia av
projektets uttryckliga statiska routes; `routes` är den aktuella
simulerade routingtabellen. De kan jämföras med identifierare utan
att ett borttaget route-ID misstas för ett felaktigt next-hop.
Alla observationer kommer från den
faktiskt felinjicerade simulerade nätverkskopian och anges
`SIMULATED` eller `SIMULATED_CONFIG`.

### DHCP är inte automatiskt uteslutet

Projektets dokumenterade IPv4/CIDR-fält anger **inte** om adressen
har lagts in statiskt eller kommit via DHCP. Det är därför otillåtet
att härleda att DHCP är friskt eller felaktigt bara från en redan
konfigurerad adress. Övningen redovisar alltid
`dhcpAddressOrigin=UNKNOWN` och `dhcpCheck=NOT_VERIFIED`.
Separata DHCP-sessioner kan användas för att diagnostisera ett
DHCP-lease/DORA-problem, men de skapar inte nya routade länkar och
kopplas inte implicit in i detta ICMP-felsökningsfall.

## Diagnos och verifierad reparation

`POST /api/icmp/investigation/diagnose` kräver exakt
`sessionId`, `project`, `diagnosis`, där en enda av
`CABLE_DOWN`, `PORT_SHUTDOWN`, `VLAN_MISMATCH`,
`STATIC_ROUTE_MISSING`, `IPV4_PREFIX_MISMATCH`,
`STATIC_NEXT_HOP_UNREACHABLE`, `IPV4_HOST_ADDRESS_MISMATCH` är tillåtna.
Den självständiga övningen kräver ett misslyckat Echo och ett
routeuppslag på den dokumenterade väg och i den riktning där utbytet
misslyckas. Mätningen måste dessutom visa en relevant avvikelse mellan
dokumenterat och simulerat tillstånd. För kabel, port, VLAN och IPv4
mäts motsvarande länk eller port. För statiska routefel visar
routeuppslaget på berörd nod att routen saknas eller att det valda
nästa hoppet har ändrats. De guidade lektionerna använder den
fasta uppsättningen mätningar ovan. Otillräckliga mätningar ger
HTTP 422 före hypotesförsöket. Fel gissning ger `correct=false`.
Högst 3 hypotesförsök accepteras.
Inga dolda feluppgifter skickas till webbläsaren förrän efter en
verkligt verifierad reparation.

`POST /api/icmp/investigation/repair` kräver exakt
`sessionId` och `project`, och endast en korrekt diagnos
tillåter åtgärden. Den injicerade felkopian måste fortfarande
misslyckas i ett färskt faktiskt Echo-utbyte. Den ursprungliga
kanoniska kopian måste sedan ge `REPLIED` och
`replyMatched=true` i en annan färsk paketinstans. Först då
får resultatet `status=RECOVERED` och den bekräftade feltypen
samt simulerade reparationspunkten med
`scope=PREVIEW_ONLY`. Om återhämtningen inte är bevisad visas
`NOT_VERIFIED`, inte en konstruerad lyckad ping.

`POST /api/icmp/investigation/stop` kräver bara `sessionId`
och kastar den processlokala övningen. Backend begränsar antalet
till **16 samtidiga övningar**, **48 mätningar per övning**,
**3 gissningar**. Snapshoten kontrolleras före varje åtgärd och
serveromstart utplånar sessionerna. Ett ogiltigt ID, fel nycklar,
ogiltig IPv4/TTL, överskriden budget eller förändrat projekt
avvisas med HTTP 422 utan positiva slutsatser och utan skrivning
till projektfil. Builder ogiltigförklarar alla sena webbsvar
efter projektändring.

## Vad övningen INTE bevisar

- Den kontrollerar inte verkliga switchar, routrar, kablar eller NIC.
- Den är begränsad till befintlig statisk IPv4-routing och dokumenterat VLAN.
- Den simulerar ingen DHCP-tilldelning för den dokumenterade
  IPv4-källan och vet inte varifrån dess adress kommer.
- Ett ändrat static next-hop är avsiktligt injicerat och verifierat
  *endast* i den begränsade ARP-/ICMP-modellen. Att en adress saknas i
  dokumentationen bevisar inte att den är oanvänd på ett riktigt nät.
- IPv4/CIDR-mätningen visar simulerad konfiguration mot dokumenterad
  baslinje, inte live-kontroll av faktisk nätmask på en riktig NIC.
- Den ger ingen DNS-analys, TCP-test, NAT, dynamisk routing,
  brandväggspolicy, RTT, automatiska felläkningar eller internetstatus.
- En ensam route lookup är aldrig liktydig med paketrechability,
  och en framgångsrik Request utan Reply är inte en godkänd ping.

Den existerande `compare_fault`-funktionen ger tre
oberoende paketutbyten: baseline, fel, återställning.
Det nya övnings-API:t återanvänder detta bevis vid scenario-urval
och gör därpå användarstyrda, fristående observerbara
paket-/konfigurationsmätningar för en pedagogisk diagnos.
