// Deterministic late-HTTP regression cases for stale session responses.
// Assertions below define the expected behavior; historical design notes are in Git history.
// This supplements, never replaces, the real Chromium and X11 CI acceptance tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createSimulationSessionController} from '../web/features/sessions/simulation-session.js';
import {createDoraSessionController} from '../web/features/sessions/dora-session.js';
import {createDhcpInvestigationController} from '../web/features/sessions/dhcp-investigation.js';

function deferredTransport(t) {
  const prior = globalThis.fetch;
  const pending = [];
  globalThis.fetch = (path, options = {}) => {
    let resolve, reject;
    const response = new Promise((yes, no) => { resolve = yes; reject = no; });
    pending.push({
      path,
      body: options?.body === undefined ? undefined : JSON.parse(options.body),
      reply(data, status = 200) {
        resolve(new Response(JSON.stringify(data), {
          status, headers: {'Content-Type': 'application/json'},
        }));
      },
      networkFailure(reason = 'synthetic lost response') { reject(new Error(reason)); },
    });
    return response;
  };
  t.after(() => { globalThis.fetch = prior; });
  return {
    next(path) {
      assert.notEqual(pending.length, 0, `Missing simulated HTTP request: ${path}`);
      const item = pending.shift();
      assert.equal(item.path, path);
      return item;
    },
    empty() { assert.equal(pending.length, 0, 'Unaccounted simulated HTTP requests'); },
  };
}

function context() {
  const project = {schemaVersion: '1.3', name: 'Synthetic declared empty network',
    zones: [], nodes: [], links: []};
  return {workspaceRevision: 0, editRevision: 0, projectSnapshot: JSON.stringify(project)};
}
function simulation(ctx) {
  return createSimulationSessionController({getContext: () => ({...ctx}), onChange() {}});
}
function dora(ctx) {
  return createDoraSessionController({getContext: () => ({...ctx}), onChange() {}});
}
function investigation(ctx) {
  return createDhcpInvestigationController({getContext: () => ({...ctx}), onChange() {}});
}
async function startSimulation(c, transport, sessionId = 'session-1') {
  const start = c.start();
  const request = transport.next('/api/simulation/start');
  assert.equal(request.body.project.name, 'Synthetic declared empty network');
  request.reply({sessionId, operationCount: 0});
  await start;
  assert.equal(c.getState().id, sessionId);
}
async function startDora(c, transport, readInputs, sessionId = 'dora-1') {
  const started = c.start({serverNode: 'server', serverPort: 'eth0'}, readInputs);
  const request = transport.next('/api/dhcp/session/start');
  assert.equal(request.body.project.schemaVersion, '1.3');
  request.reply({sessionId, leaseCount: 0, clockSeconds: 0});
  await started;
  assert.equal(c.getState().id, sessionId);
}
async function startInvestigation(c, transport, sessionId = 'investigation-1') {
  const signature = () => 'fixed DHCP investigation selections';
  const started = c.start({
    clientNode: 'client', clientPort: 'eth0',
    serverNode: 'server', serverPort: 'eth0',
    poolStart: '192.0.2.70', poolEnd: '192.0.2.71',
    leaseSeconds: 60,
  }, signature);
  const request = transport.next('/api/dhcp/investigation/start');
  assert.equal(request.body.project.schemaVersion, '1.3');
  request.reply({sessionId, observations: 0, canDiagnose: false, phase: 'RENEWING'});
  await started;
  assert.equal(c.getState().id, sessionId);
}
const flushMicrotasks = async () => {
  for (let i = 0; i < 6; i++) await Promise.resolve();
};

test('5C-S1: late successful simulation Start never attaches to a replaced workspace', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  const started = c.start();
  const oldRequest = transport.next('/api/simulation/start');
  ctx.workspaceRevision += 1;
  ctx.projectSnapshot = JSON.stringify({...JSON.parse(ctx.projectSnapshot), name: 'New workspace'});
  c.invalidate();
  oldRequest.reply({sessionId: 'obsolete-server-id', operationCount: 0});
  await started;
  const stop = transport.next('/api/simulation/stop');
  assert.deepEqual(stop.body, {sessionId: 'obsolete-server-id'});
  stop.reply({status: 'STOPPED'});
  await flushMicrotasks();
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().state, null);
  assert.equal(c.getState().diagnostic, null);
  assert.equal(c.getState().busy, false);
  transport.empty();
});

test('5C-S2: late HTTP 422 after edit and invalidation cannot reintroduce an error', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  await startSimulation(c, transport, 'old-id');
  const pendingRun = c.run('ethernet', 'a', 'eth0', 'b', () => 'old query');
  const request = transport.next('/api/simulation/run');
  ctx.editRevision += 1;
  c.invalidate();
  const stop = transport.next('/api/simulation/stop');
  assert.equal(stop.body.sessionId, 'old-id');
  request.reply({error: 'INVALID_PROJECT', message: 'obsolete 422'}, 422);
  await pendingRun;
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().diagnostic, null);
  assert.deepEqual(c.getState().highlightedLinks, []);
  stop.reply({status: 'STOPPED'});
  await flushMicrotasks();
  transport.empty();
});

test('5C-S3: changed query hides obsolete highlight without erasing server operation state', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  await startSimulation(c, transport);
  let query = 'client-A';
  const pendingRun = c.run('ethernet', 'a', 'eth0', 'target-A', () => query);
  const request = transport.next('/api/simulation/run');
  assert.equal(request.body.target, 'target-A');
  query = 'client-B';
  request.reply({sessionId: 'session-1', operationCount: 1,
    result: {transmissions: [{linkId: 'physical-A'}]}});
  await pendingRun;
  const state = c.getState();
  assert.equal(state.state.operationCount, 1);
  assert.equal(state.diagnostic, null);
  assert.deepEqual(state.highlightedLinks, []);
  assert.equal(state.inFlight, null);
  transport.empty();
});

test('5C-S4: Reset waits for Run acknowledgement before it reaches the server', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  await startSimulation(c, transport);
  const run = c.run('ethernet', 'a', 'eth0', 'b', () => 'same');
  const oldRun = transport.next('/api/simulation/run');
  assert.equal(c.getState().inFlight, 'run');
  const reset = c.reset();
  assert.equal(c.getState().inFlight, 'reset');
  assert.equal(c.getState().busy, true);
  // A reset request before this response could arrive at the server first.
  transport.empty();
  oldRun.reply({sessionId: 'session-1', operationCount: 1,
    result: {transmissions: [{linkId: 'obsolete'}]}});
  await run;
  await flushMicrotasks();
  const resetRequest = transport.next('/api/simulation/reset');
  assert.equal(resetRequest.body.sessionId, 'session-1');
  resetRequest.reply({sessionId: 'session-1', operationCount: 0});
  await reset;
  const state = c.getState();
  assert.equal(state.state.operationCount, 0);
  assert.equal(state.diagnostic, null);
  assert.deepEqual(state.highlightedLinks, []);
  assert.equal(state.busy, false);
  assert.equal(state.inFlight, null);
  transport.empty();
});

test('5C-S4a: failed Run transport cannot authorize Reset on uncertain server state', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  await startSimulation(c, transport);
  const run = c.run('ethernet', 'a', 'eth0', 'b', () => 'same');
  const oldRun = transport.next('/api/simulation/run');
  const reset = c.reset();
  transport.empty();
  oldRun.networkFailure();
  await run;
  await reset;
  const cleanup = transport.next('/api/simulation/stop');
  assert.equal(cleanup.body.sessionId, 'session-1');
  cleanup.reply({status: 'STOPPED'});
  await flushMicrotasks();
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().busy, false);
  assert.match(c.getState().diagnostic.error, /saknar bekräftat serversvar/);
  assert.equal(c.getState().pendingStopCount, 0);
  transport.empty();
});

test('5C-S4b: workspace replacement cancels queued Reset without touching new network', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  await startSimulation(c, transport);
  const run = c.run('ethernet', 'a', 'eth0', 'b', () => 'same');
  const oldRun = transport.next('/api/simulation/run');
  const reset = c.reset();
  ctx.workspaceRevision += 1;
  ctx.projectSnapshot = JSON.stringify({...JSON.parse(ctx.projectSnapshot), name: 'Different'});
  c.invalidate();
  const cleanup = transport.next('/api/simulation/stop');
  cleanup.reply({status: 'STOPPED'});
  oldRun.reply({error: 'INVALID_PROJECT',
    message: 'simulation: unknown or expired session; start a new session'}, 422);
  await run;
  await reset;
  await flushMicrotasks();
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().state, null);
  assert.equal(c.getState().busy, false);
  transport.empty();
});

test('5C-S5: a failed Stop keeps the active ID until explicit server confirmation', async t => {
  const transport = deferredTransport(t), ctx = context(), c = simulation(ctx);
  await startSimulation(c, transport, 'keep-until-confirmed');
  const first = c.stop();
  const unsuccessful = transport.next('/api/simulation/stop');
  assert.equal(unsuccessful.body.sessionId, 'keep-until-confirmed');
  unsuccessful.reply({error: 'INTERNAL', message: 'synthetic stop failure'}, 500);
  await first;
  assert.equal(c.getState().id, 'keep-until-confirmed');
  assert.match(c.getState().diagnostic.error, /Stop på servern/);

  const second = c.stop();
  const confirmed = transport.next('/api/simulation/stop');
  confirmed.reply({status: 'STOPPED'});
  await second;
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().diagnostic, null);
  transport.empty();
});

test('5C-D1: a stale DORA Start is stopped, never attached to a new project', async t => {
  const transport = deferredTransport(t), ctx = context(), c = dora(ctx);
  const started = c.start({serverNode: 'server'}, () => 'client-A');
  const pending = transport.next('/api/dhcp/session/start');
  ctx.workspaceRevision += 1;
  c.invalidate();
  pending.reply({sessionId: 'obsolete-dora', leaseCount: 1,
    leases: [{ipv4: '192.0.2.70', state: 'BOUND'}]});
  await started;
  const stop = transport.next('/api/dhcp/session/stop');
  assert.deepEqual(stop.body, {sessionId: 'obsolete-dora'});
  stop.reply({status: 'STOPPED'});
  await flushMicrotasks();
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().state, null);
  assert.equal(c.getState().trace, null);
  transport.empty();
});

test('5C-D2: changed DHCP selection hides stale result but preserves real server state', async t => {
  const transport = deferredTransport(t), ctx = context(), c = dora(ctx);
  let client = 'client-A';
  await startDora(c, transport, () => client);
  const run = c.run({clientNode: 'client-A', clientPort: 'eth0'}, () => client);
  const pending = transport.next('/api/dhcp/session/run');
  assert.equal(pending.body.clientNode, 'client-A');
  client = 'client-B';
  pending.reply({sessionId: 'dora-1', leaseCount: 1,
    result: {status: 'ACK_RECEIVED', leaseCommitted: true,
      lease: {ipv4: '192.0.2.70', state: 'BOUND'}}});
  await run;
  const state = c.getState();
  assert.equal(state.state.leaseCount, 1);
  assert.equal(state.trace, null);
  assert.equal(state.busy, false);
  transport.empty();
});

test('5C-D3: server-expired DORA session cannot be displayed as a successful lease', async t => {
  const transport = deferredTransport(t), ctx = context(), c = dora(ctx);
  await startDora(c, transport, () => 'client-A');
  const run = c.run({clientNode: 'client-A', clientPort: 'eth0'}, () => 'client-A');
  const pending = transport.next('/api/dhcp/session/run');
  pending.reply({error: 'INVALID_PROJECT',
    message: 'dhcp session: unknown or expired session; start a new session'}, 422);
  await run;
  const state = c.getState();
  assert.equal(state.id, null);
  assert.equal(state.state, null);
  assert.match(state.trace.error, /upphört på servern/);
  assert.equal(state.busy, false);
  transport.empty();
});


test('P7-I1: expired DHCP investigation Stop releases an absent server ID and permits restart', async t => {
  const transport = deferredTransport(t), ctx = context(), c = investigation(ctx);
  await startInvestigation(c, transport, 'expired-investigation');
  const stopped = c.stop();
  const request = transport.next('/api/dhcp/investigation/stop');
  assert.deepEqual(request.body, {sessionId: 'expired-investigation'});
  request.reply({error: 'INVALID_PROJECT',
    message: 'investigation: unknown or expired session'}, 422);
  await stopped;
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().state, null);
  assert.equal(c.getState().busy, false);
  assert.equal(c.getState().pendingStopCount, 0);
  await startInvestigation(c, transport, 'fresh-investigation');
  assert.equal(c.getState().id, 'fresh-investigation');
  transport.empty();
});

test('P7-I2: a malformed HTTP 200 is not a confirmed DHCP investigation Stop', async t => {
  const transport = deferredTransport(t), ctx = context(), c = investigation(ctx);
  await startInvestigation(c, transport, 'unconfirmed-investigation');
  const stopped = c.stop();
  const request = transport.next('/api/dhcp/investigation/stop');
  request.reply({status: 'NOT_STOPPED'});
  await stopped;
  assert.equal(c.getState().id, 'unconfirmed-investigation');
  assert.match(c.getState().error, /avsluta sessionen på servern/);
  assert.equal(c.getState().busy, false);
  assert.equal(c.getState().pendingStopCount, 1);

  const retry = c.stop();
  const confirmed = transport.next('/api/dhcp/investigation/stop');
  assert.deepEqual(confirmed.body, {sessionId: 'unconfirmed-investigation'});
  confirmed.reply({status: 'STOPPED'});
  await retry;
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().pendingStopCount, 0);
  transport.empty();
});

test('P7-I3: an HTTP 500 keeps the DHCP investigation active until later expiry is confirmed', async t => {
  const transport = deferredTransport(t), ctx = context(), c = investigation(ctx);
  await startInvestigation(c, transport, 'temporary-stop-error');
  const failedStop = c.stop();
  const rejected = transport.next('/api/dhcp/investigation/stop');
  rejected.reply({error: 'INTERNAL', message: 'synthetic server failure'}, 500);
  await failedStop;
  assert.equal(c.getState().id, 'temporary-stop-error');
  assert.equal(c.getState().pendingStopCount, 1);

  const retry = c.stop();
  const expired = transport.next('/api/dhcp/investigation/stop');
  expired.reply({error: 'INVALID_PROJECT',
    message: 'investigation: unknown or expired session'}, 422);
  await retry;
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().state, null);
  assert.equal(c.getState().pendingStopCount, 0);
  transport.empty();
});

test('P7-I4: invalidated expired DHCP investigation does not keep an orphaned Stop', async t => {
  const transport = deferredTransport(t), ctx = context(), c = investigation(ctx);
  await startInvestigation(c, transport, 'orphan-expired-investigation');
  c.invalidate();
  const pending = transport.next('/api/dhcp/investigation/stop');
  pending.reply({error: 'INVALID_PROJECT',
    message: 'investigation: unknown or expired session'}, 422);
  await flushMicrotasks();
  assert.equal(c.getState().id, null);
  assert.equal(c.getState().state, null);
  assert.equal(c.getState().pendingStopCount, 0);
  transport.empty();
});
