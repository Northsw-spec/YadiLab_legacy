# SVG-renderingens prestanda: indexerad projektion

**Datum:** 2026-11-22  
**Status:** Avgränsad optimering för stora nätverksdiagram; detta dokument redovisar körda tester och begränsningar.  
**Baseline:** `main@fda26052be5ba5376e64793cb780079f7e841718`, `web/canvas.js` hämtad med `git show`.  
**Experiment:** `perf/svg-indexed-render-2026-11-22`, `elkjs` och befintlig projekt-/importsemantik lämnas orörda.  
**Mätmiljö:** GitHub Actions Ubuntu 24.04, riktig headless Chromium, Node 22 och Playwright 1.57.0.  
**Bevis:** [Chromium-mätning 45051779956](https://github.com/Northsw-spec/YadiLab/actions/runs/45051779956).

## Teknisk förändring

Den äldre renderaren anropade `project.nodes.find` och `project.links.find` för varje kabelände och varje synlig port, samt filtrerade alla noder på nytt per zon och genomsökte markeringar per kabel. De upprepade sökningarna gav kvadratisk beräkningskostnad i stora projekt.

Den uppdaterade renderaren skapar **ett tillfälligt uppslagsindex per omrendering**: nod-ID, portindex, första deklarerade motpart per fysisk port, medlemskap i befintliga zoner och redan beräknade portcentra. Highlight-ID:n konverteras till en `Set`. SVG-objekten byggs först i ett frikopplat `DocumentFragment` och växlas sedan in i samma SVG. Indexen varken lagras i projektfil eller tillför nätverksfakta.

Vänster-/högerregeln för portar, nodstorlekar, kabelrutternas punkter, ordning, objektens attribut och deras pekhändelser är oförändrade.

## Uppmätt renderingstid

Median av tre upprepade synkrona `TopologyCanvas.setData()`-anrop efter uppvärmning. Tiderna avser JavaScript + DOM-uppbyggnad, **inte** hela användarupplevelsen eller garanterad frame/paint-latens.

| Projektstorlek | Tid tidigare | Tid optimerad | Hastighetsfaktor | SVG-DOM-element |
|---|---:|---:|---:|---:|
| 50 noder, 90 kablar | 3,9 ms | 2,7 ms | 1,44× | 896 |
| 500 noder, 750 kablar | 46,4 ms | 21,4 ms | 2,17× | 8 020 |
| 2 000 noder, 5 000 kablar | 965,3 ms | 121,3 ms | **7,96×** | 44 030 |

Testen är syntetiska men utgår från YadiLabs verkliga Canvas, ritmått och deklarerade port-/kabelobjekt. Källprojekten verifierades oförändrade.

## Visualisering, semantik och minne

- Den gamla och nya renderaren gav **samma SHA-256 av hela SVG-markupen** i alla tre fall.
- Antalet DOM-element var identiskt för varje test.
- Klick på deklarerad port och kabel gav identisk callback och ID.
- 40 zoomkommandon gav återgång till exakt samma vybredd; inga webbläsarundantag rapporterades.
- JavaScript-heap avlästes efter **explicit garbage collection** i Chromium (inte samma sak som hela processens minne eller SVG:s native-minne). Vid 2 000/5 000 var resultatet **5 057 480 bytes före** respektive **5 024 534 bytes efter**. Vid 500/750: 1 772 437 respektive 1 843 666 bytes. Skillnaderna är små och inte statistiskt säkerställda.
- Den separata viewport-mätningen vid 2 000/5 000 tog **3 862,9 ms före** respektive **3 674,8 ms efter** för 40 upprepade zoomkommandon. Det visar **ingen jämförbar zoomprestandaförbättring**. Omkörning och mätning av faktisk bildfrekvens under användarinteraktion bör prioriteras separat.

## Kontrakt som ska bevaras

- Inga syntetiska kablar, portar, zoner eller noder. Indexen avspeglar endast redan deklarerad topologi.
- Inga ändringar i kanonisk lagring, importkvitton, simulering, IP/VLAN, routing eller Save/Open.
- ELK:s `FIXED_POS`-portar och flyktiga SVG-kabelrutter ska kunna ritas med identisk geometri som tidigare.
- Befintliga nätverkstester, Browser ELK-acceptans, Chromium Save/Open och X11 PRIMARY-regression förblir obligatoriska.
- Ingen viewport-culling eller aggressiv SVG-sammanslagning i denna PR: portcirklar, hit-testning och paketanimation kräver separata verifierade kontrakt.

## Reproduktion

Från repositoryts rot, med tillgång till Playwright Chromium:

```bash
git show fda26052be5ba5376e64793cb780079f7e841718:web/canvas.js > web/canvas-baseline.mjs
python3 tests/browser_svg_performance.py
```

Testet tar bort sin tillfälliga baselinefil och sparar `research/svg-perf-results/benchmark.json`.
Den dedikerade CI-körningen laddar upp samma JSON som artefakt och avvisar ändringar som:
- ger en annan SVG-hash eller antal DOM-element,
- ändrar callback-identiteter eller muterar projektdata,
- inte når minst 1,5× renderingsförbättring vid 2 000/5 000,
- ökar den GC-rensade heapen över 125 % av baslinjen i det stora testet,
- ökar zoomkostnaden över 135 % av baslinjen i det stora testet.

De två sista gränserna är **regressionsgrindar för denna testmiljö**, inte löften om minnes- eller bildfrekvenskrav på alla användares datorer.
