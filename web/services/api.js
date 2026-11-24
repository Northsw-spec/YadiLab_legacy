// All application requests must target this process's relative loopback API.
// URL schemes, protocol-relative URLs, dot-segments and query paths are not
// part of the deliberately local API contract.
const LOCAL_API_PATH = /^\/api\/[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/;

// The default CLI exposes no project API to other localhost processes
// without its per-run bearer capability. Never place that key in a URL,
// static HTML, localStorage, or an exported project. It lives in this module.
let localAccessKey = '';
let pendingAccessKey = null;

function promptForLocalAccessKey() {
  if (pendingAccessKey) return pendingAccessKey;
  pendingAccessKey = new Promise((resolve, reject) => {
    if (typeof document === 'undefined') {
      reject(new Error('Lokal åtkomstnyckel krävs. Använd giltig Authorization-header.'));
      return;
    }
    const dialog = document.getElementById('local-api-auth-dialog');
    const form = document.getElementById('local-api-auth-form');
    const input = document.getElementById('local-api-access-key');
    const feedback = document.getElementById('local-api-auth-feedback');
    if (!dialog || !form || !input || !feedback) {
      reject(new Error('Det säkra autentiseringsformuläret saknas.'));
      return;
    }
    feedback.textContent = '';
    const cleanup = () => {
      form.removeEventListener('submit', submit);
      dialog.removeEventListener('cancel', cancel);
      input.value = '';
    };
    const submit = event => {
      event.preventDefault();
      const candidate = input.value.trim();
      if (!/^[A-Za-z0-9_-]{40,128}$/.test(candidate)) {
        feedback.textContent = 'Ange en fullständig lokal åtkomstnyckel från terminalen.';
        return;
      }
      cleanup();
      localAccessKey = candidate;
      dialog.close();
      resolve(candidate);
    };
    const cancel = event => {
      event.preventDefault();
      cleanup();
      dialog.close();
      reject(new Error('Lokal åtkomstnyckel krävs för denna åtgärd.'));
    };
    form.addEventListener('submit', submit);
    dialog.addEventListener('cancel', cancel);
    dialog.showModal();
    input.focus();
  }).finally(() => { pendingAccessKey = null; });
  return pendingAccessKey;
}

function fetchWithCapability(path, options, token) {
  if (!token) return fetch(path, options);
  return fetch(path, {
    ...(options || {}),
    headers: {...(options?.headers || {}), Authorization: 'Bearer ' + token},
  });
}

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
  const options = payload === undefined ? undefined : {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: rawJson ? payload : JSON.stringify(payload),
  };
  const priorKey = localAccessKey;
  let response = await fetchWithCapability(path, options, priorKey);
  if (response.status === 401) {
    // A process restart rotates the token. Do not let a stale in-flight
    // response erase a newer key acquired by a concurrent request.
    if (localAccessKey === priorKey) localAccessKey = '';
    if (!localAccessKey) await promptForLocalAccessKey();
    response = await fetchWithCapability(path, options, localAccessKey);
    if (response.status === 401) {
      localAccessKey = '';
      throw new Error('Fel lokal åtkomstnyckel. Kontrollera den aktuella terminalsessionen.');
    }
  }
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
