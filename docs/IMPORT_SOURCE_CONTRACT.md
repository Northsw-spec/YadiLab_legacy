# Tekniskt importkontrakt – källtrogen dokumentationshantering

**2026-11-24:** Detta är ett **tekniskt kontrakt**, inte en plan eller automatisk beställning av ny importerare. Den **enda aktiva utvecklingsplanen** är [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md](PEDAGOGICAL_TROUBLESHOOTING_PLAN.md). Faktiskt stöd bestäms av aktuell kod, test och CI på exakt commit, inte av denna text.

## Ägarskap och format

- `network_core/model.py::validate_project` är enda slutliga validator för den kanoniska nätverksmodellen. `network_core/storage.py` äger explicit filskrivning, SHA-256 och konfliktkontroll.
- `network_core/csv_import.py` hanterar namngivna CSV-filer (`Devices`, `Interfaces`, `Links`, `Zones`). `xlsx_import.py`, `ods_import.py` och `spreadsheet_schema.py` hanterar deras uttryckligt stödda kalkylblad/format.
- `import_inspection.py` läser källor, `import_plan.py` hanterar explicita mappningsbeslut, `import_evidence.py` och `import_verification.py` hanterar proveniens/källkontroller inom befintligt schema. `web/features/projects/import-review.js` äger UI-valen.
- `.yadilab`/JSON-projekt, mappningsprofiler och originalkällpaket har egna strikta importvägar. Uppladdade originalbytes måste nå serverns strikta UTF-8-JSON-parser innan browserns `JSON.parse` normaliserar data: dubbla nycklar eller ogiltig Unicode ska avvisas.

Detaljer om kalkylblad: [SPREADSHEET_V13.md](SPREADSHEET_V13.md), [XLSX_IMPORT.md](XLSX_IMPORT.md) och [ODS_IMPORT.md](ODS_IMPORT.md). Inga godtyckliga kundfilformat eller heuristiska mappningar är därmed automatiskt implementerade.

## Normativ fail-closed-gräns

**Läsning/inspektion är inte godkänd projekttillämpning.** Ofullständiga källor får granskas men får inte bli simulerbart projekt om nödvändiga fakta saknas.

1. Alla noder, portar, länkar och nätverksfält som **krävs för den uttryckligt avsedda topologin och funktionen** ska vara fullständiga och källspårbara. En fysisk kabel kräver båda **uttryckligt angivna nod-/portändpunkterna**. IP, gateway, placering, zon, hostname eller LLDP-indikation får inte skapa syntetiska portar eller kablar.
2. Relevant blockerande, motsägelsefull eller olöst källdata får inte tyst exkluderas för att skapa en falskt godkänd deltopologi. En uttryckligen vald, helt självständig och **fullständig** annan topologi måste vara separat avgränsad och godkänd av användaren.
3. Kräv inte irrelevanta protokollfält. Ett rent Layer 2-projekt behöver exempelvis inte IPv4 eller statiska routes.
4. Visa blockerande källposition, fält, beroende och orsak där sådan källinformation finns. Vid blockering får **varken arbetsyta eller sparad fil ändras**.
5. Vid uttrycklig komplettering av data ska **hela kandidatprojektet valideras igen** genom `validate_project`. Tillämpning kräver separat godkännande av arbetsytebyte; **disklagring kräver därefter separat Save**.
6. Rad/kolumn, källhash, käll-ID, explicita transformationer och importbeslut är proveniens där befintlig implementation stöder dem. ELK-koordinater är enbart presentation och aldrig källa för fysisk topologi.

**Implementationsstatus:** Dessa är målkrav för korrekt import. Dokumentet påstår **inte** att samtliga nuvarande UI-/API-vägar har bevisats uppfylla fullständighetsgrinden. Där negativa end-to-end-tester saknas gäller `NOT_VERIFIED`.

## Regressioner före importkodändring

Testa originalbytes, riktiga fel och verklig HTTP/UI: saknad kabelport; motsägelsefulla relationer; blockerad delimport; positivt rent L2-fall; explicit komplettering och ny validering; bevarade ID:n, källpositioner, projektrevision och Save/Open efter omstart. Exakta förväntade resultat ska vara självständigt motiverade, inte härledda från motorn under test.

Ingen ny importfunktion, kopierad kodbas, andra schemamotor eller egen utvecklingskö skapas av detta dokument. Följ [AGENTS.md](../AGENTS.md) och [MASTERPROMPT.md](MASTERPROMPT.md).
