# **Teknisk granskning av YadiLab – 2026-11-26**

Repository: [Northsw-spec/YadiLab](https://github.com/Northsw-spec/YadiLab?utm_source=chatgpt.com) | Granskad huvudgren: `fe111c5368d4a4758bc86123b06447f34ba2a02e`

## **1. Är YadiLab en riktig nätverkssimulator?**

**Ja. YadiLab innehåller en verkligt implementerad, deterministisk nätverkssimulator med avgränsad protokollfunktionalitet. Det är inte en applikation som enbart hittar på plausibla nätverksresultat.**

Min granskning av de centrala Python-modulerna visar att programmet faktiskt beräknar nätverksbeteenden:

- Ethernetramar serialiseras och avkodas.
- Switchar lär sig MAC-adresser från simulerad trafik.
- VLAN avgör vilka ramar som kan vidarebefordras.
- ARP använder simulerade förfrågningar och svar.
- IPv4-routing använder deklarerade gränssnitt och rutter.
- ICMP Echo kräver fungerande trafik i både fram- och returriktningen.
- DHCP genomför avgränsade DORA-utbyten med simulerade leases.

Det är en betydande skillnad mot en simulator som bara kontrollerar om två noder är förbundna med en ritad linje.

**Men YadiLab är inte en fullständig nätverksemulator.** Den kan inte ersätta GNS3, EVE-NG eller riktig nätverksutrustning för generell protokoll- och konfigurationsverifiering. Den saknar bland annat native OSPF, BGP, STP, IPv6, allmän NAT/ACL och fullständig TCP/UDP-simulering.

Den viktiga kvalitetsfrågan är därför inte bara hur många protokoll som saknas, utan **om det som faktiskt stöds fungerar korrekt och om programmet avstår från att påstå sådant som det inte kan bevisa.**

## **2. Testresultat och verifieringsstyrka**

Jag har granskat GitHub Actions-loggen för PR #164, inte bara den gröna statussymbolen.

# **789/789**

Python-tester godkända

# **47/47**

JavaScript-tester godkända

# **29/29**

Pedagogiska bedömningsfall godkända

**Obligatorisk CI: SUCCESS**

Granskad körning: [GitHub Actions #45740771632](https://github.com/Northsw-spec/YadiLab/actions/runs/45740771632?utm_source=chatgpt.com) på PR-HEAD `d17e957b…`, före squash-merge till main.

Dessutom passerade tester med riktig Chromium för användargränssnitt, Save/Open, API-behörighet, ELK-layout och Linux/X11-beteende.

Detta ger relativt stark evidens för att de testade funktionerna är reproducerbara. Framför allt innehåller testerna negativa nätverksfall: VLAN-isolering, felaktig ARP, utebliven returroute, trasiga kablar och ogiltiga IPv4-adresser.

**Begränsning:** Testerna bevisar inte att alla tänkbara nätverksscenarier fungerar korrekt. Jag har läst källkod och CI-loggar, men har inte kört en egen fullständig testsvit eller verifierat ett fristående långtids- eller belastningstest i denna granskning.

## **3. Källkodsgranskning: vad håller tekniskt?**

| Område                      | Bedömning                                                                                               | Källkod                                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Datamodell och topologi** | Stark. Kräver explicita noder, portar, kablar och adresser. Avvisar många motstridiga uppgifter.        | [model.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/model.py?utm_source=chatgpt.com)         |
| **Ethernet, MAC och VLAN**  | Genomtänkt, avgränsad L2-modell med faktiskt simulerad vidarebefordran och MAC-inlärning.               | [ethernet.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/ethernet.py?utm_source=chatgpt.com)   |
| **ARP**                     | Stark. Kräver simulerad request/reply innan en adress anses upplöst. Hanterar VLAN-isolering och cache. | [arp.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/arp.py?utm_source=chatgpt.com)             |
| **IPv4 och routing**        | Tekniskt seriös men begränsad. Kontrollerar routes, ARP, Ethernetleverans och TTL.                      | [ipv4.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/ipv4.py?utm_source=chatgpt.com)           |
| **ICMP**                    | Stark för stödda Echo-fall. Verifierar returvägen separat, inklusive matchande paketidentitet.          | [icmp_ping.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/icmp_ping.py?utm_source=chatgpt.com) |
| **DHCP**                    | Genuin DORA-modell med kodade DHCP/UDP/IP-paket, virtuella leases och avgränsad T1/T2-hantering.        | [dhcp.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/dhcp.py?utm_source=chatgpt.com)           |
| **Lagring och import**      | Stark dataintegritetsdesign med strikt JSON, explicita importbeslut, SHA-256 och atomär Save.           | [storage.py](https://github.com/Northsw-spec/YadiLab/blob/main/network_core/storage.py?utm_source=chatgpt.com)     |

En särskilt viktig detalj finns i IPv4-motorn. YadiLab nöjer sig inte med att en route matchar destinationen. Den försöker även lösa nästa hopp med ARP och överföra ett kodat IPv4-paket över den simulerade Ethernetstrukturen. Mottagande gränssnitts MAC- och IP-identitet kontrolleras innan resultatet får status `DELIVERED`.

Detta är **riktig simuleringslogik**, även om den inte omfattar hela nätverksstacken.

### **Varför jag bedömer hallucinationsrisken som relativt låg**

Koden har flera mekanismer som uttryckligen motverkar falska positiva slutsatser. En grafväg utges inte för att vara fungerande IP-kommunikation. Ett ARP-svar utges inte för att vara lyckad ping. En skickad ICMP-felram utges inte automatiskt för att vara mottagen.

Dessutom skapas inte gateways, MAC-adresser, kablar eller statiska rutter enbart för att det skulle göra ett scenario fungerande.

**Jag har inte hittat något som tyder på att de granskade nätverksmotorerna använder generativ AI för att hitta på sina resultat.** De bygger på deterministisk programlogik.

Det betyder inte att alla möjliga utfall är korrekta. En deterministisk simulator kan fortfarande innehålla logikfel eller förenklingar.

## **4. Brister och risker jag identifierat**

**Stor komplexitet i vissa moduler**

`web/app.js` omfattar cirka 2 978 rader, `network_core/import_plan.py` 967 rader och `network_core/icmp_investigation.py` 829 rader. Det är inte i sig ett fel, men det ökar risken för oavsiktliga beroenden, tillståndsfel och kostsamt underhåll. Det finns redan historiska PR:er som korrigerat frontend-race conditions.

**Begränsad simulering av verkliga nätverksförhållanden**

Switchloopar avvisas i stället för att hanteras med STP. IPv4-fragmentering, generell TCP/UDP, köer, bandbredd och verkliga tidsfördröjningar modelleras inte. DHCP saknar bland annat relay och fullständigt stöd för flera servrar. Detta är i huvudsak dokumenterade begränsningar, inte påvisade hallucinationer.

**Konkret mindre serverbrist i CI-loggen**

Under Chromium-testningen registrerades `ConnectionResetError` följt av `BrokenPipeError` när en klient avbröt en HTTP-anslutning. Testkörningen lyckades trots detta. Serverns felhantering bör behandla frånkopplade klienter utan att försöka skriva ett nytt felsvar till den stängda anslutningen. Jag klassar detta som ett mindre robusthetsproblem, inte som ett bevis på felaktig nätverkssimulering.

**Begränsad oberoende validering**

Det finns tester mot externa RFC-referenser och handskrivna protokollvektorer, vilket är positivt. Men en helt fristående systematisk jämförelse med verklig nätverksutrustning eller en etablerad referensimplementation har inte verifierats här. Att kodens egna tester passerar ger inte fullständig protokollcertifiering.

**Pedagogisk effekt är ännu inte empiriskt fastställd**

Det finns guidade ICMP- och DHCP-övningar och automatiska bedömningsfall. Men det planerade sammanhållna undervisningsgränssnittet är inte färdigt och det saknas verifierade studier som visar hur mycket bättre elever faktiskt lär sig av YadiLab.

### **Vad historiken säger om kodkvaliteten**

Granskningen av PR #111–#164 visar att riktiga fel har identifierats och korrigerats, exempelvis felaktigt accepterade IPv4-adresser, DHCP-adresser, ogiltiga ICMP-felpaket och tillståndsproblem i frontend.

Detta visar två saker samtidigt: programmet har haft betydande korrekthetsbrister, men utvecklingsprocessen har också blivit alltmer testdriven och restriktiv. Att PR #162 stängdes utan merge när en föreslagen ändring försvagade nätverksvalideringen är ett positivt exempel.

Jag har **inte verifierat något nytt kritiskt fel som gör att den aktuella motorn felaktigt rapporterar lyckad nätverkskommunikation**. Det är inte detsamma som att bevisa att sådana fel saknas.

## **5. Mina betyg**

Källkodens kvalitet

Arkitektur, validering, testbarhet och underhåll

## **8,2/10**

Teknisk korrekthet

Inom de faktiskt implementerade protokollfallen

## **8,3/10**

Tillförlitlighet

Reproducerbarhet, felhantering och dataintegritet

## **8,0/10**

Pedagogiskt värde för junior IT-konsult

Potential och nuvarande undervisningsfunktioner

## **8,4/10**

Bredd som generell nätverkssimulator

Protokoll, enhetsemulering och verklighetstrogen drift

## **3,0/10**

### **Samlat betyg inom YadiLabs utbildningssyfte**

Min kvalitativa bedömning, inte ett certifierat mätresultat

# **8,2/10**

Det praktiska värdet är störst när användaren vill förstå orsakskedjor inom Ethernet, ARP, VLAN, IPv4-routing, ICMP och DHCP. Värdet är betydligt lägre om målet är att verifiera en verklig företagskonfiguration med dynamiska routingprotokoll och avancerade brandväggsregler.

## **6. Slutbedömning**

**YadiLab är en tekniskt seriös, relativt tillförlitlig och tydligt avgränsad nätverkssimulator. Jag bedömer inte den aktuella versionen som hallucinerad.**

Dess starkaste egenskap är att nätverksresultat i betydande utsträckning kan härledas genom faktiska kodade paket, explicita gränssnitt, switchbeslut och verifierade fram- och returvägar.

Dess största svaghet är inte uppenbar fabricering av nätverksresultat, utan begränsad protokollbredd, omfattande programkomplexitet och att fullständig oberoende korrekthetsvalidering ännu saknas.

**Min prioritering för nästa kvalitetsnivå** är att verifiera de befintliga protokollmotorerna mot ytterligare fristående referensfall, testa mer komplicerade topologier och gränsfall, förbättra HTTP-robustheten och gradvis minska frontendens komplexitet utan att förlora den nuvarande testtäckningen.

Det skulle stärka YadiLabs viktigaste löfte: att eleven kan lita på att ett visat simuleringsresultat faktiskt följer av den modell som programmet säger sig använda.

Granskningens räckvidd: central backend- och protokollkod läst direkt från GitHub, arkitektur för import, sessioner och frontend undersökt, relevanta testmoduler och historiska rättningar granskade samt full CI-logg kontrollerad. Ingen fullständig rad-för-rad-certifiering av samtliga repositoryfiler, och ingen separat lokal exekvering genomförd.
