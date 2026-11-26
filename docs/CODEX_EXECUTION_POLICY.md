# Codex – obligatoriskt produktivitets- och CI-kontrakt

**Utökat bindande uppdrag 2026-11-26:** [enda huvudplanen A0–A10 + S0–S12](REMEDIATION_PLAN_2026-11-26.md), [MASTERPROMPT](MASTERPROMPT.md), [protokollmatris](PROTOCOL_COVERAGE_MATRIX.md) och [simuleringskontrakt](architecture/DETERMINISTIC_ENGINE_CONTRACT.md) styr nu Packet Tracer-plus-målet. **A9:s native protokoll-/eventmotorutbyggnad är beställd som S-kort; A8:s mänskliga studie kräver fortfarande separat godkännande.** Äldre regler om enbart A0–A10 eller förbud mot nya protokoll är upphävda för det nya explicita S-omfånget, inte för CI-säkerhet eller emulering. Kredit-, test-, Required- och squashreglerna nedan gäller oförändrade även för S-kod.


**Status:** Normativ operativ instruktion från 2026-11-26. **Gäller allt Codex-/agentarbete i YadiLab** genom [AGENTS.md](../AGENTS.md), [MASTERPROMPT](MASTERPROMPT.md), [enda aktiva A0–A10 + S0–S12-planen](REMEDIATION_PLAN_2026-11-26.md) och [PR-mallen](../.github/pull_request_template.md). Detta är **inte en ny roadmap**, inte ett mandat att ändra omfång och inte en ersättning för GitHubs tekniska branchskydd.

**Primärregel: maximera verifierade kod-/arkitektur-/buggfixleveranser per Codex-credit, inte antal verktygsanrop eller hur länge en session förblir öppen. Ingen passiv väntan på GitHub Actions.** Ett CI-jobb körs på GitHubs infrastruktur oberoende av att agenten fortsätter fråga om status. Skilj Codex-credits från GitHub Actions-minuter; de är inte samma resurs.

## 1. Arbetsordning som alltid gäller

1. **Engångsinventering:** Läs senaste `main` SHA, aktiv PR (högst en), Required-regler, aktuellt A-kort och relevanta källfiler/tester. Läs inte hela historiska dokumentationsarkivet igen utan ett konkret beroende. Återanvänd redan verifierade SHA-/PR-/filfakta tills något faktiskt ändrats.
2. **Leverera minsta meningsfulla kodenheten:** Identifiera ett avgränsat fel/ansvar; skriv fix/extraktion samt minst ett positivt och ett negativt oberoende test. Följ exakt befintliga projekt- och API-kontrakt. Undvik omläggning av opåverkade delar och kosmetiska ändringar som saknar tekniskt värde.
3. **Snabb lokal återkoppling:** Kontrollera syntax, berörd modul, riktade regressioner och arkitekturspärr **innan** en dyr browser-/end-to-end-kedja. Först när den billiga grinden passerat får relevanta bredare tester beställas. Kör inte samma fulla svit igen utan ny kod/nytt felunderlag.
4. **Ett granskningsbart PR-head:** Samla logiskt samhörande kod, tester, arkitekturbudget, rollback, relevanta styrdokument och status i **en** PR för godkänt A-kort. Undvik en rad onödiga mikropushar som startar om CI. Följ den enda aktiva planen, inte äldre P0–P7.
5. **Asynkron acceptans:** När PR finns ska CI få köras oberoende. Fortsätt med **arbete som faktiskt förbättrar samma PR**: granska diff och gränsfall, rätta verkliga analysfel, verifiera negativa orakel, kontrollera berörda dokumentlänkar, förbered ett sakligt evidens-/handoffunderlag. Inga nya oberoende PR:er när en är aktiv.
6. **Inget sysselsättningsarbete:** När det inte återstår säkert, oberoende arbete under samma A-kort: gör högst en motiverad aktuell CI-statuskontroll, rapportera exakt PR/HEAD, PASS/FAIL/PENDING och nästa beroende och **avsluta den aktiva körningen**. Det är bättre att lämna en tydlig PR för fortsatt granskning än att förbruka credits med tomma statusfrågor.
7. **Slutgrind vid merge:** Färdigställ med squash **först** när exakta senaste PR-HEAD har Required `unit-tests` och `architecture-guard` `SUCCESS`, alla tillämpliga extra checks `SUCCESS`, PR är mergebar, reviews godkända enligt branchregeln och `main`/base är verifierad. **Aldrig** bypass/force/merge på FAIL/PENDING. Verifiera ny main/merge SHA och stäng inga beroenden före faktiskt bevis.
8. **Ny session efter extern väntan:** Läs PR HEAD och kontroller **en gång**, agera på faktiskt resultat (åtgärda fel, merge om säkert eller rapportera blockering) och fortsätt med nästa godkända del. Återstarta inte redan färdigställda steg eller gamla CI-körningar.

## 2. Förbjudna credit- och CI-slöserier

- **Ingen pollingloop:** inga `sleep`, täta upprepade API-anrop, långa väntande verktygskörningar, omtag av samma oförändrade status, tomma ”fortsätt vänta”-resonemang eller permanent upptagen agentsession enbart för GitHub Actions. En extra kontroll motiveras endast av verklig ny signal (avslutat jobb, ändrad SHA, relevant fel eller användarens uttryckliga kontrollbegäran).
- **Inga onödiga omkörningar:** inga dubbla fulla lokala unittest/npm/Chromium-sviter när riktade tester räcker för ett förhandsbeslut. Ingen ny push bara för att ”få grön ikon”; utan verifierad ändring finns inget att omtesta. Rerun av misslyckat jobb endast med dokumenterad transient orsak; kodfel rättas i källkod och får **ny** exakt HEAD.
- **Ingen chansad felsökning:** Läs först exakta felraden/loggen och den faktiska berörda koden. Sänk aldrig arkitekturbudgetspärrar eller ta bort negativa tester för att få grönt. Misstänkta regressionsrisker prioriteras framför snygga statusrapporter.
- **Ingen onödig kontextinläsning:** hämta relevanta filavsnitt, diffs, loggradsutdrag och senaste beslut, inte samma stora dokument/logg gång på gång. Gör ett tool-anrop när data behövs, inte för att fylla väntetid.
- **Inga falska asynkrona löften:** agenten arbetar bara under ett aktivt tillåtet anrop. Om ingen automation/auto-merge faktiskt är konfigurerad: skriv inte att du ”fortsätter i bakgrunden”, ”kommer tillbaka senare” eller har bokat en framtida leverans.

## 3. Testtrappa – minsta säkra körning, sedan full acceptans

| Ändring | Före PR / vid utveckling | Required GitHub-gate |
|---|---|---|
| Ren Markdown i godkända styr-/docs-sökvägar | Dokumentlänkar, styrkontrakt, arkitekturgranskning | `architecture-guard` + `unit-tests` med verifierad **docs-only** governance-/supply-chain-svit |
| Python backend/API/storage | Riktad `unittest`, felaktiga/positiva fall, relevant modell-/SHA-orakel | **Fullständig** `unit-tests` och `architecture-guard` |
| JavaScript/Builder/Canvas/ELK/Save/Open | `node --check`, berörd Node-svit, riktad browser/HTTP-acceptans | **Fullständig** Chromium, X11, ELK, Save/Open/SHA och Required-checks |
| Workflows, Python-tester, `tools/**`, `architecture/**`, `package.json`, andra icke-dokumentfiler eller okänd diff | Riktad CI-/guard-negativfixture och kodgranskning | **Fullständig** Required CI, ingen docs-only-genväg |

**Fail-closed docs-only:** `tools/ci_change_scope.py` läser exakt Git-diff mot PR-basen (på `main` mot första föräldern). Endast *tillägg eller ändring av vanliga Markdown-blobbar* i `docs/**/*.md`, `AGENTS.md`, `README.md`, `.github/pull_request_template.md` eller `.github/copilot-instructions.md` ger `docs_only=true`. Borttagning, rename, symlink, okänd/ogiltig SHA, tom diff, saknad Git-historik och varje runtime-/test-/workflow-/vendorändring ger **full** testväg. Docs-only får **aldrig** hoppa över `architecture-guard`, arkitekturbackupen i `unit-tests` eller riktade styr-/integritetstester. `unit-tests` förblir en faktiskt godkänd Required-status för exakt PR-HEAD.

**Dubbla CI-körningar:** Required-workflows kör **pull_request på varje PR-HEAD** och **push endast till `main`** – inte en identisk full svit också för varje push till PR-grenen. Äldre PR-run avbryts vid ny synkroniserad commit genom workflow-scoped `concurrency`; `main`-körningar avbryts inte. Fokuserade ELK/SVG-jobb behåller sin egna path-specifika säkerhetsroll, men äldre PR-fokuskörningar kan avbrytas när HEAD ersätts.

**Auto-merge:** använd bara om GitHub-repot faktiskt har stöd **och** squash, branchskydd, exakt latest HEAD och övriga tillämpliga checks garanteras. Slå aldrig på okänt merge-läge eller kringgå skydd. Annars dokumentera PR/HEAD/checks och avsluta sessionen utan passivt väntande.

## 4. Produktivitet när extern kontroll fortfarande kör

Arbetskö inom **samma** godkända A-kort, rangordnad efter faktisk nytta: (a) reproducera/avgränsa verifierade buggar, (b) förbättra den redan påbörjade koden med bibehållen API-/modulgräns, (c) skapa självständiga positiva/negativa orakel, (d) granska oavsiktliga beroenden och data-/securityregressioner, (e) säkerställ Save/Open/SHA, stale-asynkronitet, att lyssnare inte dubblas och korrekt projektmodell, (f) uppdatera nödvändig PR-/roadmapevidens och tydlig rollback. **Ändra inte ny HEAD efter godkänd finalgrind** utan en verifierad anledning: varje ny commit kräver nya Required-checks och kan skapa mer arbete än nytta.

Om nästa steg kräver en extern händelse och inga säkra parallella uppgifter finns: lämna en kort **återupptagningspunkt** med ansvarig PR, sista commit, rapporterade checks, faktiskt blockerande händelse, och exakt första åtgärd nästa session. Ange `PENDING` som `PENDING`, aldrig `DONE`.

## 5. Hårt bevarade säkerhets- och arkitekturgränser

- Max **en aktiv PR**. Nästa oberoende A-kort börjar först efter verifierad merge/stängning av pågående PR; säker analys får fortsätta men ingen konkurrerande PR.
- Enda giltiga backlog: [A0–A10 + S0–S12](REMEDIATION_PLAN_2026-11-26.md). A8/A9 har nu olika beslut: A8 kräver separat godkännande, A9:s fullständiga simuleringsutbyggnad har redan godkänts uttryckligen och genomförs inom S1–S12 efter beroendegrindar. Historiska P0–P7 är CLOSED.
- Varje faktisk ändring ska förbättra buggsäkerhet, beteendetest, arkitekturägarskap, användarnytta eller spårbarhet. **Ingen refaktorering bara för färre rader** och ingen onödig funktionalitet utanför scope.
- Skydda en explicit nätverksmodell/en validator och sanningsenliga paket/RFC-bevis. S-kortens nya protokoll är nu godkända i princip, men kräver riktig referensorakel, säker migration, gemensam eventmotor, state-ägare och negativa tester. Ingen VM, emulator, extern runtime eller annan OS-familj utan nytt uttryckligt beslut.
- Required branchregler `unit-tests` och `architecture-guard` från GitHub Actions gäller fortsatt. Inga path-filter, skippade jobb, borttagna tester eller manuellt kringgående av `main`-skyddet.
- **Styrningens tekniska gräns:** Markdown kan instruera Codex, men kan inte ensam tvinga en agent att förbruka färre credits eller garantera framtida agentbeteende. Maskinella tester i `tests/test_codex_governance.py` och `tests/test_ci_integrity.py` upprätthåller länkar och CI-avgränsningar; beteende i själva agentsessionen kräver att agenten följer denna instruktion.

## 6. Obligatorisk avsluts-/överlämningsrad

Rapportera konkret och kort: **kod-/dokumentdiff, testfall, PR/HEAD, Required-status, oberoende bevis, arkitekturdelta, blockerare eller verifierad merge SHA, nästa godkända delkort**. Skilj `MERGED`, `OPEN+CHECKS_PENDING`, `BLOCKED` och `NOT_STARTED`. Upprepa inte statusfrågor efter en handoff utan verklig ny information.
