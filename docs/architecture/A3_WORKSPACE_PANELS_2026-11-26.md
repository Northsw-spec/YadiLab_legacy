# A3 del 1 – Arbetsytans dropdown-paneler i ägd DOM-modul

**Datum:** 2026-11-26  
**Leverans:** [PR #176](https://github.com/Northsw-spec/YadiLab/pull/176)  
**Aktiv roadmap:** [A0–A10](../REMEDIATION_PLAN_2026-11-26.md), C03–C05  
**Status:** **Del 1 DONE** efter [PR #176](https://github.com/Northsw-spec/YadiLab/pull/176), squash `35ed34bd76551849ca79ebc5ca75813f2540e5d1` med två Required `unit-tests`, två Required `architecture-guard` och fokuserad ELK SUCCESS. **Hela A3 är fortfarande IN_PROGRESS**. Framtida Codex-arbeten följer [CODEX_EXECUTION_POLICY.md](../CODEX_EXECUTION_POLICY.md).

## Avgränsning

A0-forensiken visade att \`web/app.js\` hade återtagit DOM-ansvar för arbetsytans dropdown-paneler och dess händelselyssnare. Detta är en **presentationsuppgift**, inte en del av canonical project, Save/Open, nätverksmotor, workspace revision eller session controllers.

Den exakta gruppen \`panelCard\`, \`dropdownCards\`, \`syncDropdownButton\` och \`setupWorkspacePanels\` har flyttats till **\`web/ui/workspace-panels.js\`**. Den nya modulen importerar endast \`$ / el\` från \`web/ui/dom.js\` och exporterar endast \`setupWorkspacePanels\`. \`web/app.js\` gör en vanlig ES-import och anropar setup i samma gamla bootstrap-position.

All ursprunglig DOM-mappning, ordning, etiketter, länkar, enhets-/zon-/länklistor, panelernas \`<details>\` och eventhantering är bevarade. Inget runtime- eller workspace-tillstånd kopieras; \`web/app.js\` äger fortsatt projektets revisioner, selection, Save/Open, diagnostik, state och callbacks. Strikt HTTP-allowlist i \`network_core/server.py\` inkluderar enbart den nya modulsökvägen som ytterligare statiskt JavaScript.

## Mätbar architecture ratchet (A1 guard)

| Statiskt mått | main före PR | PR #176 | Delta |
|---|---:|---:|---:|
| \`web/app.js\` fysiska rader | 2 977 | 2 926 | **−51** |
| Direkta \`.addEventListener(\` i \`app.js\` | 96 | 94 | **−2** |
| DOM-åtkomst/sidoeffektheuristik | 104 | 98 | **−6** |
| Namngivna top-level-funktioner i \`app.js\` | 116 | 112 | **−4** |
| Top-level bindings i \`app.js\` | 46 | 46 | **0** |
| Förstaparts ES-moduler | 18 | 19 | **+1** |
| Statiska första-part-importkanter | 29 | 31 | **+2** |

Dessa värden är statiska mått, inte semantisk eller runtimecertifiering. \`architecture/baseline.json\` ratchets **neråt** för rader, events och DOM och innehåller nytt ägarkontrakt: \`owner=dom\`, \`imports=[web/ui/dom.js]\`, \`exports=[setupWorkspacePanels]\`. Historiskt A0-manifest bevaras oförändrat. Den gamla positiva A1-kontrollen som hårdkodade exakt 18 moduler har gjorts dynamisk mot det versionsstyrda modulkontraktet utan att någon negativ kontroll tas bort; ett nytt negativt A3-test avvisar borttagen ny modul.

## Beteendetester och negativ evidens

\`tests/workspace_panels_test.mjs\` körs från \`npm run check\` och är registrerad i Required-testmanifestet. Två oberoende JavaScript-fall mäter följande:

1. **Positivt DOM-orakel:** exakt samma redan existerande node-/link-/zone-/inspector-/trace-DOM-objekt flyttas till samma panelgrupper med intakta identiteter, etiketter och ordning; inga påhittade nätverksobjekt.
2. **Positiv/negativ UI-state:** exakt en \`click\`-listener på \`toggle-dropdowns\` och en \`toggle\`-listener per panel. All-open ger \`aria-pressed=true\`, en manuellt stängd panel ger **false**, och nästa knapptyck återöppnar alla; därefter stängs alla med **false**.

\`tests/test_http_boundary.py\` kontrollerar också att den nya statiska modulen kan hämtas via loopbackservern; den lägger inte till någon kataloglistning eller dynamisk sökväg. Tidigare \`browser_smoke.py\` och acceptanstester på riktig Chromium täcker faktisk rendering, Save/Open, X11, ELK och bibehållen SHA utan att projektet skrivs till disk implicit.

## Kvarstående A3

Detta är **inte** ett försök att avsluta hela A3 med endast 51 färre rader. Fortsatt arbete i separata, granskade PR:er: en enda explicit ägare av workspace-/edit-revisioner och invalidering; Builder-/inspector-presentation, diagnosorkestrering, import-/mapping-/Save/Open-UI samt tillhörande stale-response-/session- och layoutparitet. Ingen andra simulator, ingen duplicerad app-state, inga ospecificerade nätverksfakta.

**Slutvillkor för del-PR:** Required \`unit-tests\` och \`architecture-guard\` SUCCESS på exakt HEAD, inga blockerande reviews, main oförändrad, squash-merge och därefter kontroll av ny main/CI. Om något av detta saknas: del-PR **NOT_ACCEPTED**, A3 fortsatt IN_PROGRESS. Återställning genom revert av enbart del-PR #176.
