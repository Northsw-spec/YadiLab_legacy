import test from 'node:test';
import assert from 'node:assert/strict';

import {createWorkspaceRevisions} from '../web/features/projects/workspace-revisions.js';
import {prepareSave} from '../web/features/projects/persistence.js';

const project = () => ({
  schemaVersion: '1.3', name: 'Documented LAN', nodes: [], links: [], zones: [],
});

test('one owner starts at zero and advances edit/workspace tokens independently', () => {
  const state = createWorkspaceRevisions();
  assert.deepEqual(state.versions(), {workspaceRevision: 0, editRevision: 0});
  assert.ok(Object.isFrozen(state));
  const first = state.versions();
  state.markEdit();
  assert.deepEqual(state.versions(), {workspaceRevision: 0, editRevision: 1});
  assert.equal(state.matches(first), false);
  state.replace();
  assert.deepEqual(state.versions(), {workspaceRevision: 1, editRevision: 1});
  state.markEdit();
  assert.deepEqual(state.versions(), {workspaceRevision: 1, editRevision: 2});
  const independent = createWorkspaceRevisions();
  assert.deepEqual(independent.versions(), {workspaceRevision: 0, editRevision: 0});
});

test('session context is an immutable-in-time project snapshot and never copies canonical ownership', () => {
  const state = createWorkspaceRevisions();
  const network = project();
  const old = state.sessionContext(network);
  assert.deepEqual(old, {workspaceRevision: 0, editRevision: 0,
    projectSnapshot: JSON.stringify(network)});
  network.name = 'Edited documented LAN';
  assert.notEqual(old.projectSnapshot, JSON.stringify(network));
  state.markEdit();
  assert.equal(state.matches(old), false);
});

test('asynchronous Open/transfer drops old responses on edit, replacement and filename changes', () => {
  const state = createWorkspaceRevisions();
  const network = project();
  const original = state.capture(network, 'lab');
  assert.equal(state.isCurrent(original, network, 'lab'), true);
  assert.equal(state.isCurrent(original, network, 'other'), false);
  network.nodes.push({id: 'n1'});
  assert.equal(state.isCurrent(original, network, 'lab'), false,
    'in-place edit without a revision bump must not approve an old response');
  network.nodes.pop();
  assert.equal(state.isCurrent(original, network, 'lab'), true);
  state.markEdit();
  assert.equal(state.isCurrent(original, network, 'lab'), false);
  const afterEdit = state.capture(network, 'lab');
  state.replace();
  assert.equal(state.isCurrent(afterEdit, network, 'lab'), false);
  assert.equal(state.isCurrent(state.capture(network, 'lab'), network, 'lab'), true);
});

test('Builder late validation cannot overwrite another attempt with the same version', () => {
  const state = createWorkspaceRevisions();
  const network = project();
  const first = state.beginValidation(network, 'lab');
  assert.ok(state.validationCurrent(first, network, 'lab'));
  const newer = state.beginValidation(network, 'lab');
  assert.equal(state.validationCurrent(first, network, 'lab'), false,
    'later Builder attempt supersedes older request without an edit');
  assert.equal(state.validationCurrent(newer, network, 'lab'), true);
  assert.equal(state.validationCurrent(newer, project(), 'lab'), false,
    'different canonical object with equal JSON is still a new Builder context');
  network.name = 'In-place change';
  assert.equal(state.validationCurrent(newer, network, 'lab'), false);
  const next = state.beginValidation(network, 'lab');
  state.markEdit();
  assert.equal(state.validationCurrent(next, network, 'lab'), false);
  const last = state.beginValidation(network, 'lab');
  state.replace();
  assert.equal(state.validationCurrent(last, network, 'lab'), false);
});

test('Save request preserves version, serialized data and SHA contract; late reply is stale', () => {
  const state = createWorkspaceRevisions();
  const network = project();
  const request = prepareSave({
    filename: 'lab', project: network, ...state.versions(),
    savedName: 'lab', savedSha: 'a'.repeat(64),
  });
  assert.equal(request.workspaceRevision, 0);
  assert.equal(request.editRevision, 0);
  assert.equal(request.expectedSha256, 'a'.repeat(64));
  assert.equal(request.serializedProject, JSON.stringify(network));
  assert.ok(Object.isFrozen(request));
  network.nodes.push({id: 'later'});
  assert.equal(state.matches(request), true,
    'Save must separately compare serialized snapshot when no edit token was recorded');
  assert.notEqual(request.serializedProject, JSON.stringify(network));
  state.markEdit();
  assert.equal(state.matches(request), false,
    'stale conflict-approval callback must not approve a changed workspace');
  state.replace();
  assert.equal(state.workspace, 1);
  assert.equal(state.matches(request), false,
    'late SHA from another workspace must not attach to the current project');
});

test('tokens protect independently racing diagnostics, even after identical data restored', () => {
  const state = createWorkspaceRevisions();
  const network = project();
  const pending = state.capture(network, 'lab');
  state.markEdit();
  const next = state.capture(network, 'lab');
  assert.equal(state.matches(pending), false);
  assert.ok(state.isCurrent(next, network, 'lab'));
  state.replace();
  state.markEdit();
  assert.equal(state.matches(next), false,
    'a newer workspace cannot accept an older diagnostic response after Open');
  const session = state.sessionContext(network);
  assert.deepEqual([session.workspaceRevision, session.editRevision], [1, 2]);
});
