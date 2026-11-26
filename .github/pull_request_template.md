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

**Aktuell realitet:** `architecture-guard` och dess branchskydd ska införas i A1; denna mall är inte bevis att spärren redan finns. A8-studie och A9-protokollutökning kräver nytt uttryckligt användargodkännande.
