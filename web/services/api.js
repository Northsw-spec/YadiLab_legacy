// All application requests must target this process's relative loopback API.
// URL schemes, protocol-relative URLs, dot-segments and query paths are not
// part of the deliberately local API contract.
const LOCAL_API_PATH = /^\/api\/[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/;

export async function api(path, payload = undefined, {rawJson = false} = {}) {
  if (typeof path !== 'string' || !LOCAL_API_PATH.test(path)) {
    throw new Error('Endast lokala /api/-sökvägar är tillåtna.');
  }
  // Raw JSON files must reach the strict server decoder as original bytes.
  // Re-serializing via JSON.parse/stringify would silently erase duplicate keys.
  if (rawJson && (!['/api/validate', '/api/json/strict'].includes(path) ||
                  !(payload instanceof Uint8Array))) {
    throw new Error('Raw JSON kräver originalbytes och godkänd lokal valideringsväg.');
  }
  // Protocol requests carry only the network projection. The full project
  // remains authoritative for editing, revisions, Save/Open and history.
  const protocol = /^\/api\/(?:trace|troubleshoot\/|routing\/|ipv4\/|icmp\/|dhcp\/|simulation\/|diagnostics\/)/.test(path);
  if (protocol && payload?.project?.schemaVersion === '1.4') {
    const {name, zones, nodes, links} = payload.project;
    payload = {...payload, project: {schemaVersion: '1.3', name, zones, nodes, links}};
  }
  const response = await fetch(path, payload === undefined ? undefined : {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: rawJson ? payload : JSON.stringify(payload),
  });
  let data;
  try { data = await response.json(); }
  catch { throw new Error(`Oväntat svar från lokal server (${response.status})`); }
  if (!response.ok) {
    const error = new Error(data.message || 'Åtgärden misslyckades');
    error.code = data.error;
    error.currentSha256 = data.currentSha256;
    throw error;
  }
  return data;
}
