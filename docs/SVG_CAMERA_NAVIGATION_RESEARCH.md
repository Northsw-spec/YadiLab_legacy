# Kameraoptimering i stora SVG-topologier

**Datum:** 2026-11-22  
**Metod:** Faktisk Chromium via Playwright; syntetiska nätverk med 500/750 och 2 000/5 000 noder/kablar.  
**Basversion:** `809d93d9e6a1edf4bb56923e2715dc289499d4bd`.  
**Omfattning:** Endast kamerans mätning av CSS/SVG-viewport. Ingen ändring av topologiska fakta, ELK, kabeldragning eller projektformat.

## Verifierad mindre förbättring

Tidigare läste `zoom()` både SVG-rektangeln vid koordinatkonverteringen och ännu en gång inne i `setView()` *efter* skrivning av `viewBox`. Panorering upprepade också en redan utförd mätning. En enkel, konservativ ändring använder den redan uppmätta viewport-rektangeln i `toWorld()`, `zoom()`, `setView()` och muspanoreringen. Läsningen sker före skrivning.

Den första riktiga Chromium-mätningen (GitHub Actions **45054968687**) gav vid 2 000 noder och 5 000 kablar:

| 40 synkrona händelser | Basversion | Första kandidat | Förbättring |
|---|---:|---:|---:|
| Zoom | 3 465,1 ms | 3 259,7 ms | **1,06×** |
| Panorering | 3 353,9 ms | 3 076,0 ms | **1,09×** |

Samma test gav helt identiska SHA-256-värden för SVG-markupen, samma nodpositioner och samma pan-/zoomslutkoordinater. Antalet synkrona layoutmätningar halverades, men **prestandaförbättringen är modest**. Den underliggande SVG-ritkostnaden består.

## Hypoteser som inte godkändes

Ett alternativ med `requestAnimationFrame` samlade 40 syntetiska wheel-/pointer-event i en JavaScript-uppgift till en eller två `viewBox`-skrivningar. I detta särskilda burst-test var anropen 14–37 gånger snabbare. **Det innebär inte 14–37 gånger högre bildfrekvens.**

När ett wheel-event i stället levererades per animeringsruta blev den varianten cirka **10–18 % långsammare** än basversionen i de körda mätningarna (körningarna **45055339267**, **45055592070**). En efterföljande tidsheuristik för att skilja burstar från ordinarie event tog bort vinsten för de täta eventserierna (körning **45055855555**).

Båda rAF-varianterna **avvisades** och ingår inte i den konservativa produktändringen. Den färdiga koden behåller omedelbar `viewBox`-uppdatering för alla normala zoom- och panoperationer.

## Testgrindar

- `npm run check` innehåller ett kameratest som kräver en viewportmätning före varje `viewBox`-skrivning vid Fit, zoom och självständigt setView.
- Ett isolerat Chromium-test jämför exakt basversion mot kandidaten med syntetiska projekt och 40 operationer per mätomgång.
- All SVG-markup och kamerageometri ska vara identisk.
- Den dedikerade benchmarken avvisar mer än fem procents försämring i det stora testet; när förbättringen är så liten ska flera oberoende körningar användas före starkare slutsatser.
- Ordinarie CI måste fortsatt klara Python, JavaScript, Chromium Save/Open, X11 och ELK.

**Kvarstående arbete:** För tydligt högre faktisk bildfrekvens krävs en separat lösning för vad webbläsaren behöver rasterisera vid kamerarörelse, exempelvis noggrant verifierad viewport-culling eller ett annat representationslager. Det är inte verifierat här.
