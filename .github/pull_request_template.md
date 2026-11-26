# YadiLab – ändrings- och evidenschecklista

**Ensam aktiv roadmap:** [Åtgärdsplan A0–A10](../docs/REMEDIATION_PLAN_2026-11-26.md) · [ursprunglig teknisk granskning](../docs/reviews/TECHNICAL_REVIEW_2026-11-26.md). P0–P7 är avslutad och får inte återstartas automatiskt.

## Arbetskort och bevis
- A-kort: `A?`
- Berörda gransknings-ID: `C??`
- Bevisad brist/scope: 
- Utgångspunkt: `main@<sha>` och öppna PR:er:
- Berörda moduler, ansvar och state-ägare:
- Vad får uttryckligen **inte** ändras:
- Oberoende förväntat resultat och negativa/motsägande fall:
- Varje C-ID:s status/evidenslänk efter detta arbete:

## Codex-arbetsform – kredit- och CI-effektivitet

Följ [obligatorisk produktivitets-/CI-policy](../docs/CODEX_EXECUTION_POLICY.md).
- [ ] Fastställ faktisk main SHA, enda öppna PR, scope och minsta oberoende positiva/negativa tester före tung körning.
- [ ] Riktad billig preflight före allomfattande browser; ingen duplicerad full CI på PR-branchpush.
- [ ] Vid PENDING: ingen passiv Actions-polling, sleep-loop eller statusspamming; arbeta säkert inom samma PR eller lämna exakt HEAD/status/handoff.
- [ ] Docs-only påstås endast om `tools/ci_change_scope.py` verifierat ren Markdown-diff; annars full Required-matris.
- [ ] Endast faktiska korrigeringar ger ny commit/full körning. Ingen falsk auto-merge eller bakgrundskörning.

## Verifiering och säker ändring
- [ ] En PR åt gången; inget nytt projektschema, andra motorer eller oannonserade protokoll
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py' -v`
- [ ] `npm run check`
- [ ] Riktig Chromium och relevant X11 när berörd kod/UI ändras
- [ ] Save/Open, SHA-256, omstart och stale-response-skydd när berörda
- [ ] API-/protokollsemantik, positiva och negativa tester samt användaridentiteter bevaras
- [ ] Arkitekturdifferens mot godkänd budget/modulägare (ingen tyst återmonolitisering)
- [ ] Från och med **A1**: separat `architecture-guard` REQUIRED och grön; G1–G7 negativt testade
- [ ] Dokumentera rollback och synliga restbrister utan ogrundad DONE-status
- [ ] Uppdatera A-kortets status/nästa arbetskort i **samma** roadmap, inte i ny planfil
- [ ] Alla required checks på **exakt slutlig PR-HEAD** = SUCCESS; förväntad main oförändrad
- [ ] Inga blockerande reviews; squash-merge utan kringgånget branchskydd

**Aktuell realitet:** Main-ruleset #27419615 kräver **både** `unit-tests` och `architecture-guard` (GitHub Actions app 15368, strict); separat blockering verifierades i ej mergad PR #173. Att Codex inte väntar passivt innebär **aldrig** bypass eller påstådd merge före exakta Required-checks SUCCESS. A8-studie och A9-protokollutökning kräver nytt uttryckligt användargodkännande.
