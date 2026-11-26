# A2 – HTTP-resiliens vid frånkopplad klient (C06)

**Datum:** 2026-11-26  
**Aktiv plan:** [A0–A10](../REMEDIATION_PLAN_2026-11-26.md)  
**Leverans:** [PR #175](https://github.com/Northsw-spec/YadiLab/pull/175), Linux-lokal HTTP-server  
**Acceptansstatus:** **DONE (2026-11-26)**. [PR #175](https://github.com/Northsw-spec/YadiLab/pull/175) squash-mergades till main som `73a3fe0fb490ec8a7dbd5487ba8c4527ac9ea2ea` efter två Required `unit-tests` SUCCESS och två `architecture-guard` SUCCESS på exakt slutlig HEAD `3bcdf6d869a79e1fd3c4d4c117fa0a6b1e8a9f9b`.

## Problem och felklass

[Granskningens C06](../reviews/TECHNICAL_REVIEW_2026-11-26.md) observerade `ConnectionResetError` och därefter `BrokenPipeError` i Chromium-/serverloggar efter klientavbrott, trots att CI i övrigt passerade. Orsaken i tidigare `network_core/server.py` var att `_json` och statiska/binära svar kallade `end_headers` och `wfile.write` direkt; `do_GET`/`do_POST` hanterade transportexception som en generell domän-/serverexception och `_respond_error` försökte skicka ett andra JSON-felsvar till samma stängda socket.

C06 är ett transportrobusthetsfel, **inte ett belagt fel i VLAN/IPv4/ICMP/DHCP-motorn**.

## Ändring och motivering

1. `Handler._finish_response` är **enda utgående body-/headerflush-vägen** för JSON-svar, publika XLSX/ODS-mallar och tillåtna statiska frontendfiler. Den skyddar både `end_headers()` och `wfile.write()` mot igenkända socketfrånkopplingar.
2. `Handler._expected_peer_disconnect` klassificerar endast `BrokenPipeError`, `ConnectionResetError`, `ConnectionAbortedError` och Linux-transportkoder `EPIPE`, `ECONNRESET`, `ECONNABORTED`, `ENOTCONN`, `ESHUTDOWN`. Okända `OSError` ignoreras inte.
3. Endast klassificerat transportfel översätts till `ClientDisconnected`, sätter `close_connection=True` och **stoppar varje ytterligare svarsförsök**. `_respond_error` gör därför **ingen extra `_json(500)`** efter förlorad klient. `handle_one_request` skyddar också avbrott i tidigare HTTP-gränser före domäntry-blocket, t.ex. för `401` och OPTIONS.
4. `_read_json` avbryter säkert vid reset under bodyläsning eller EOF före deklarerad Content-Length. Ett partiellt JSON-dokument får aldrig tolkas som ett helt request eller användas som Save-underlag.
5. Inga automatiska retries införs, och lagringsmotorn `ProjectStore.save`, SHA-256, optimismbaserad konfliktkontroll och explicit användar-Save är **oförändrade**. Om en klient tappar anslutningen **efter** att Save har committat kan servern inte bevisa att klienten hann se resultatet. Klienten måste då uttryckligen läsa filen och dess SHA och eventuellt själv besluta om nästa Save; tyst automatisk dublettskrivning är förbjuden.

## Testorakel – `tests/test_http_disconnect.py`

| Testfall | Oberoende förväntat resultat |
|---|---|
| Verklig TCP RST under JSON-svar på `/api/health` | Ingen sekundär JSON eller uncaught traceback; senare korrekt hälsosvar 200 |
| Verklig TCP RST under statisk `/app.js` | Inget fel-JSON efter påbörjat JS-svar; resursen kan fortfarande hämtas |
| Verklig TCP RST under publik XLSX-mall | Inget fel-JSON efter binärt svar; senare intakta ZIP-bytes och MIME |
| Verklig TCP RST under `/api/save`-svar | Exakt **ett** Save-anrop; en korrekt atomisk .yadilab-fil; faktisk SHA-256 matchar återläsning; ingen implicit retry |
| Verklig TCP RST **mitt i** POST-body | Ingen tolkning/sparning av partiell JSON; ingen unhandled exception; fortsatt hälsosvar |
| Verklig RST under tidigt `401`-svar | Ingen traceback via trust-boundary före normal request try/except |
| Injicerat `BrokenPipeError(EPIPE)` vid `end_headers` | En enda svarsförsök, inget sekundärt 500, senare normalt 200 |
| Fullständig men ogiltig JSON | Korrekt 422, JSON-felkontrakt bevarat, ingen projektfil |
| Verkligt applikationsundantag | 500 `INTERNAL`, synlig serverdiagnos, inte tyst maskerat |
| Oväntad `OSError(EIO)` | Inte klassad som klientdisconnect; serverfel fortsatt 500 och loggas |

Reella nätverksfall använder loopback TCP och Linux `SO_LINGER(1,0)` för RST. I tester efter svarshuvuden synkroniseras servern med `threading.Event` så att klienten kopplar ifrån **före** verklig `wfile.write`, vilket reducerar tidsberoende race. Unga false positives förhindras genom att testerna kräver en upptäckt `ClientDisconnected` där den normala domänfelhanteringen ska observera felet; `ObservedServer.handle_error` registrerar all annars okontrollerad traceback. Den fulla suite-körningen ska även skydda real Chromium, X11 PRIMARY, ELK, API-access, Save/Open och projektkontraktet.

## Före/efter, arkitektur och risk

- **Ändrade produktfiler:** endast `network_core/server.py`.
- **Tillagd testfil:** `tests/test_http_disconnect.py`, registrerad i `architecture/baseline.json` så A1:s guard bevarar den.
- **Ingen ändring:** frontend ES-moduler, `web/app.js`, nätverks-/simuleringsmotor, datalager, kanonisk schema/version, API-paths/status för intakta klienter, behörighets-/Origin-kontroller eller lagrings- och SHAfunktioner.
- **Begränsning:** En peer-reset kan fortfarande vara en faktisk osäker leverans av ett **redan utfört** svar. En server kan inte dra tillbaka en atomiskt genomförd Save bara för att klientens TCP-session dör vid kvittens. Registret ger explicit SHA-återläsning men lovar inte garanterad leverans via HTTP.
- **Återställning:** Revert av PR #175, om regressionsskydd kräver det; gör inte en nystartad motor eller nya protokoll.
- **Om extern logg senare visar enstaka BrokenPipeError:** kontrollera exakt stack och socketläge. En verklig app-/diskexception får inte tyst sorteras som förväntad reset.

**Obligatorisk slutgrind:** exakt sista PR-HEAD med Required `unit-tests=SUCCESS`, `architecture-guard=SUCCESS`, mergeable PR, inga blockerande reviews och oförändrad bas-main innan squash-merge. Efter verifierad merge sätt A2 DONE och A3 NEXT i den enda aktiva planen.
