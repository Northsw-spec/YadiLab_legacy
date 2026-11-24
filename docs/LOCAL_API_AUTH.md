# Lokal API-behörighet på Linux

**Status 2026-11-24:** Normal start via `python3 -m network_core` skyddar projekt-API:t med en processunik, kryptografiskt slumpmässig Bearer-nyckel. Det är en behörighetsgräns för lokala HTTP-klienter, inte ett påstående om generell Linux-processisolering.

## Normal start

Vid start skriver programmet en tillfällig `Local API access key` i terminalen. Den öppnade webbläsaradressen är en vanlig `http://127.0.0.1:<port>/`, utan nyckel i URL, fragment eller HTML. När appen första gången begär tillgång till privata API-anrop visas en dialog där användaren manuellt anger nyckeln. Nyckeln finns bara i den aktuella JavaScript-modulens minne och försvinner vid omladdning eller omstart; den sparas inte i projektfil, `localStorage` eller annan beständig webbläsarlagring.

En extern CLI-klient behöver motsvarande `Authorization: Bearer <nyckel från terminalen>` på privata `/api/`-anrop. Undvik att ange nyckeln i shellhistorik eller i kommandoradsargument som kan synas via `/proc`. Var försiktig med delade terminaler och logginsamling som kan fånga startutskriften.

**Skyddade API:** projektlistor, öppning av projekt, Save, validering, importer, exporter, diagnoser och sessioner. Utan giltig nyckel returneras HTTP 401 innan privat projektdata läses eller begäranskroppen hanteras. Flera Authorization-headers, felaktig eller gammal nyckel och ogiltig Host/Origin/Sec-Fetch-Site avvisas.

**Offentliga resurser utan projektdata:** `/api/health`, syntetiska exempelmallar `/api/templates/xlsx` och `/api/templates/ods`, samt statiska webbresurser. Dessa får aldrig innehålla privata projekt, sparade filer eller åtkomstnyckeln.

`--no-browser` behåller behörighetskravet. Flaggan `--unsafe-test-no-auth` är ett **uttryckligt osäkert undantag endast för isolerade CI-/regressionstester** och får inte användas på delade eller obetrodda Linuxvärdar. Att instansiera `LabHTTPServer` direkt utan `auth_token` är ett lågnivåtestgränssnitt, inte den rekommenderade säkra applikationsstarten.

## Hotmodell och kvarvarande begränsningar

En annan lokal process kan känna till loopbackporten men kan inte läsa eller skriva privata projekt över API:t utan nyckeln. Detta isolerar **inte** mot komprometterad kod som körs som samma Linuxanvändare och redan kan läsa terminalen, mot XSS i själva webbläsarens same-origin-app, privilegierade processer eller direkta läsningar av oskyddade filer på disk. Det är inte Unix-UID-autentisering över TCP, inte krypterad fjärråtkomst och inte en ersättning för korrekt ägarskap/rättigheter på datakatalogen. Servern är fortsatt strikt bunden till `127.0.0.1`; exponera inte porten via tunnel/proxy.

Verifiering: Python/HTTP-regressioner för saknad, felaktig och duplicerad nyckel, exakt Host/Origin, privat Save/Open, offentliga syntetiska mallar, plus riktig Chromium-dialog, nyckelns frånvaro i HTML/URL och uttrycklig Save/Open. Giltig access-nyckel garanterar inte nätverkssimulatorns logiska korrekthet.
