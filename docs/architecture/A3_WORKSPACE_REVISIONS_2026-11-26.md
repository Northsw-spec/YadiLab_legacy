# A3 del 2 – en ägare för workspace-, edit- och Builder-generationer

**Datum:** 2026-11-26  
**Leverans:** [PR #177](https://github.com/Northsw-spec/YadiLab/pull/177) (delarbete, inte hela A3)  
**Styrning:** [enda aktiva A0–A10-planen](../REMEDIATION_PLAN_2026-11-26.md), framför allt C03–C05  
**Status:** **Del 2 DONE** efter [PR #177](https://github.com/Northsw-spec/YadiLab/pull/177), squash `16e6bd67444b1ef9eb96f2448edf04efda2ab17f` med två Required `unit-tests`, två Required `architecture-guard` och fokuserad ELK SUCCESS. **Hela A3 IN_PROGRESS**. Framtida Codex-arbeten följer [CODEX_EXECUTION_POLICY.md](../CODEX_EXECUTION_POLICY.md) utan passiv CI-väntan.

## Felskyddets tidigare spridning

Före ändringen ägde `web/app.js` tre separata räknare: `workspaceRevision`, `editRevision` och `builderValidationGeneration`. Enskilda funktioner upprepade kontrollerna i Builder-HTTP-validering, `Open`, `Save`, import/ELK-överföring, DHCP/DORA och de synliga ARP/IPv4/ICMP-diagnoserna. Vid ett försenat asynkront svar krävs att rätt workspace, redigeringsversion, projektsnapshot och – för Builder – objektidentitet och försökets generation fortfarande matchar.

En generell `getContext` utan versionskontroll skulle ha kunnat återskapa observerade racefel. En modul som äger en **andra** kopia av projektet eller sparad SHA hade varit lika felaktig.

## Avgränsad lösning och bibehållna kontrakt

Ny `web/features/projects/workspace-revisions.js` exporterar en enda factory: `createWorkspaceRevisions()`. Varje instans äger exklusivt monotona workspace-, edit- och Builder-generationer; inga globala variabler eller projektdata dupliceras.

Gränssnittet:
- `versions()` och `matches(context)`: jämför exakt `workspaceRevision` + `editRevision` i den avsedda request-/sessionskontexten.
- `markEdit()` och `replace()`: explicita versionsökningar. Vid `resetProject` sker samma sekvens som tidigare: workspace ökar före `changed()`, vars editrevision ökar; vid lyckad `Open` ökar båda utan anrop av `changed()`.
- `capture(project, filename)` och `isCurrent(context, project, filename)`: versions- och kanoniskt JSON-snapshot/filnamn jämförs före async-commit eller DOM-presentation. Därmed spärras även omodellerade in-place-ändringar som inte fått revisionsbump.
- `sessionContext(project)`: ger de befintliga session controllers samma kontrakt `{workspaceRevision, editRevision, projectSnapshot}`. Sessioners privatägda generationslogik ändras inte.
- `beginValidation(project, filename)` och `validationCurrent(...)`: Builder är fortfarande skyddad av nyare försök, objektidentitet, filnamn, revisionsvärden och serialiserat projektsnapshot. Nya försök kan inte accepterats i fel ordning bara för att workspace är oförändrat.

`web/app.js` förblir kompositionsrot med **ett** referensbundet revisionsobjekt, men **äger inte de tre räknarna längre**. De äldre `changed()`-/`invalidateElk()`-/`importReview.onEdit()`-sidoeffekterna, arbetsytans data, urval, DOM och HTTP-anrop är kvar på samma plats och i samma ordning. En senare A3-PR får separera *invalideringens sidoeffekter* endast med tester för late `finally`, session cleanup, Builder och riktig Chromium. Denna PR påstår alltså **inte** att alla UI-invalideringar flyttats.

## Mätbar arkitekturförändring

| Mått | Före | Efter | Förändring |
|---|---:|---:|---:|
| `web/app.js` fysiska rader | 2 926 | 2 913 | **−13** |
| Appens namngivna toppnivåfunktioner | 112 | 112 | 0 |
| Appens egna toppnivåbindings | 46 | 44 | **−2** |
| Direkta `addEventListener` | 94 | 94 | 0 |
| DOM-heuristik | 98 | 98 | 0 |
| Förstaparts ES-moduler | 19 | 20 | **+1** |

`architecture/baseline.json` ratchet-sänker `web/app.js` till 2 913 rader, tar bort `editRevision` och `builderValidationGeneration` från appens eget bindningskontrakt samt registrerar ny projektsmodul med en enda export och inga modulimporter. Ingen tidigare budget höjs, och historisk A0-baslinje förblir oförändrad.

## Oberoende positiv/negativ regressionsevidens

Ny `tests/workspace_revisions_test.mjs` kör sex deterministiska Node-fall: korrekt versionsförlopp och instansisolering; sessionssnapshot utan kopierat live-projekt; stale `Open`/transfer efter ändring, in-place-mutering, filbyte och workspace-byte; två överlappande Builder-HTTP-valideringar där den första måste förkastas även om modellen är oförändrad; Save-kontraktets snapshot/SHA och förbud att fästa sent Save-kvitto till ny workspace; sena diagnostiksvar efter nytt workspace. `prepareSave`-testet använder befintlig produktfunktion, inte en kopia.

`tests/test_architecture_guard.py` får ytterligare två negativa tester: borttagen ny ägarmodul ska fallera, och återinfört fristående `let editRevision` i appen ska fallera på `APP_STATE_OWNERSHIP_DRIFT`. `npm run check` syntaxkontrollerar den nya ES-modulen och kör alla sex testerna. Strikt statisk HTTP-allowlist och `tests/test_http_boundary.py` omfattar den nya modulen. Befintliga Chromium, X11, ELK, Save/Open, lagrings-SHA och sessionstester måste förbli gröna.

**Risk och rollback:** Denna statiska refaktorering är inte ett fullständigt formellt bevis för att alla möjliga asynkrona callbacks är säkra. Särskilt sena `finally` i diagnostik samt UI-invalideringarnas ordning behöver egna senare A3-deltester. Inget nytt format, ingen ändring av backendnätverksmotor eller automatiska Save-retries. Återställ vid regression genom revert av just PR #177.

**Slutgrind för del 2:** Required `unit-tests` + `architecture-guard` **SUCCESS på exakt slutlig PR-HEAD**, faktisk Chromium/X11/ELK/Save/Open, inga blockerande reviews, strict main-regel och verifierad squash-merge. Om inte, **del 2 ej accepterad** och A3 fortsatt IN_PROGRESS.
