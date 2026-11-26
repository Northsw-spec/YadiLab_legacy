# YadiLab – ändrings- och evidenschecklista

**ABSOLUT PT-FULL-001-OMFÅNG:** [full funktionsparitet](../docs/FULL_PACKET_TRACER_PARITY_CONTRACT.md) gäller varje PR och framtida release. **Alla** PT-protokoll, devices/moduler, CLI/GUI, fysisk/logisk workspace, simulatorläge/PDU, utbildnings-/examensfunktioner, IoT/OT, multiuser, scripting, extensions, filformat och kvarvarande PT-funktioner är obligatoriska i slutversionen. Endast Linux-only och inget särskilt keyboard/accessibility-mål undantas. Ange vilka PT-F-ID/underfall som faktiskt verifieras av PR:n, vad som fortfarande saknas, och vilken standard/PT-version oraklen gäller. Ingen COMPLETE-etikett med öppna gap.


**Ensam aktiv plan:** [A0–A10 + S0–S12](../docs/REMEDIATION_PLAN_2026-11-26.md), [MASTERPROMPT](../docs/MASTERPROMPT.md), [Packet Tracer-forskning](../docs/research/PACKET_TRACER_GAP_ANALYSIS_2026-11-26.md), [protokollmatris](../docs/PROTOCOL_COVERAGE_MATRIX.md), [eventmotorkontrakt](../docs/architecture/DETERMINISTIC_ENGINE_CONTRACT.md). P0–P7 CLOSED. A9-expansion godkänd 2026-11-26; A8 mänsklig studie separat.

## Arbetskort och verkligt beteende

- A? eller S?, C??/protokollrad, exakt variant/standard/errata:
- Faktisk main/PR-HEAD och kontrollerade beroenden:
- Konkret fel/scope, åtgärd och uttryckligt ej ändrat:
- Kanoniskt schema och ägare för config, state och timers:
- Oberoende positivt, negativt och motsägande protokollorakel:
- Råpaket/header, state transitions, packet/parent event-ID, expected drop:
- Simulerad tid, seed, event-/memory-budget, skalprofil:
- Migration för gamla projekt samt provenance, Save/Open/SHA:
- Rättslig/licensmässig gräns och explicit unsupported:
- Packet Tracer-versionslåst referens, PT_DOK vs PT_VERIFIED_COMPARISON:
- Arkitektureffekt, preflight, rollback, nästa beroendeupplåsta kort:

## Codex-, arkitektur- och CI-säkerhet

Följ [obligatorisk kredit- och CI-policy](../docs/CODEX_EXECUTION_POLICY.md).
- [ ] Ett avgränsat A-/S-kort i en enda PR; S1-kod börjar först efter A3/A4/A5/A7.
- [ ] Endast en kanonisk projektvalidator och en motor, inga VM/IOS/emulering/externa runtimeprocesser.
- [ ] Verklig standardversion, packet-/state-/time-semantik och oberoende negativa motexempel.
- [ ] Riktad billig testtrappa, ingen dubbel full svit eller passiv Actions-polling.
- [ ] Full Required funktionell CI för runtime/test/workflow, docs-only enbart verifierad fail-closed.
- [ ] Riktig Chromium/X11 vid UI, explicit SHA/fil/omstart vid Save/Open.
- [ ] Ingen CLI-förmåga utan backendfunktion; inget falskt påstående om protokoll/paritet.
- [ ] Ingen tyst schema-/import-/projekt-/sessionmigration eller automatiskt Save.
- [ ] Required unit-tests + architecture-guard samt tillämpliga extra checks SUCCESS på exakt final PR-HEAD.
- [ ] Ingen blockerande review, verifierad main/mergebarhet och tillåten squash utan bypass.
- [ ] Uppdatera en enda roadmap och protokollmatris med faktisk PASS/FAIL/NOT_VERIFIED-evidens.

**Main-ruleset #27419615:** strict required unit-tests + architecture-guard. Dokumentation är ingen implementerad protokollfunktion.
