import test from 'node:test';
import assert from 'node:assert/strict';

import {api} from '../web/services/api.js';
import {prepareImport, submitImport} from '../web/features/projects/transfer.js';

const file = (name, raw) => {
  const bytes = typeof raw === 'string' ? new TextEncoder().encode(raw) : raw;
  return {
    name, size: bytes.byteLength,
    async arrayBuffer() {
      return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    },
  };
};

test('project import transmits original ambiguous JSON bytes; never client-normalizes duplicate keys', async () => {
  const original = '{"schemaVersion":"1.3","name":"first","name":"second","zones":[],"nodes":[],"links":[]}';
  const selected = await prepareImport([file('case.yadilab', original)], 'project', 'ignored');
  assert.equal(selected.path, '/api/validate');
  assert.equal(selected.rawJson, true);
  assert.ok(selected.payload instanceof Uint8Array);
  assert.equal(new TextDecoder().decode(selected.payload), original);
  const previous = globalThis.fetch;
  let calls = [];
  globalThis.fetch = async (path, options) => {
    calls.push({path, options});
    return {ok:true, status:200, json:async () => ({project:{}})};
  };
  try {
    await submitImport(selected);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].path, '/api/validate');
    assert.equal(calls[0].options.method, 'POST');
    assert.equal(new TextDecoder().decode(calls[0].options.body), original);
    assert.ok(calls[0].options.body instanceof Uint8Array);
  } finally {
    globalThis.fetch = previous;
  }
});

test('raw-byte project import never silently replaces invalid UTF-8', async () => {
  const raw = new Uint8Array([0x7b, 0x22, 0x6e, 0x22, 0x3a, 0xff, 0x7d]);
  const prepared = await prepareImport([file('corrupt.json', raw)], 'project', 'unused');
  assert.deepEqual(prepared.payload, raw);
  assert.equal(prepared.rawJson, true);
});

test('api rejects external, protocol-relative and path-traversal URLs before any fetch', async () => {
  const prior = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw new Error('fetch must not run'); };
  try {
    for (const path of [
      'https://example.invalid/collect', 'http://127.0.0.2/api/save',
      '//example.invalid/api/save', '/api/../snoop', '/api/./validate',
      '/api//save', '/other/api/save', '../api/save', '/api/save?mode=external',
      '/api/save#hash', '/api/%2e%2e/health', 'javascript:alert(1)', null,
    ]) {
      await assert.rejects(api(path, {value:'x'}), /Endast lokala/);
    }
    assert.equal(calls, 0);
  } finally {
    globalThis.fetch = prior;
  }
});

test('api permits exact local JSON paths and raw-byte parser endpoint only', async () => {
  const previous = globalThis.fetch;
  const captures = [];
  globalThis.fetch = async (path, options) => {
    captures.push({path, options});
    return {ok:true, status:200, json:async () => ({document: {ok:true}})};
  };
  try {
    const raw = new TextEncoder().encode('{"profile":1,"profile":2}');
    const result = await api('/api/json/strict', raw, {rawJson:true});
    assert.deepEqual(result, {document:{ok:true}});
    assert.equal(captures[0].path, '/api/json/strict');
    assert.deepEqual(captures[0].options.body, raw);

    const save = {filename:'lab', project:{schemaVersion:'1.3'}, expectedSha256:null};
    await api('/api/save', save);
    assert.equal(captures[1].options.body, JSON.stringify(save));
    await assert.rejects(api('/api/save', raw, {rawJson:true}), /Raw JSON/);
    await assert.rejects(api('/api/validate', {name:'not bytes'}, {rawJson:true}), /Raw JSON/);
    assert.equal(captures.length, 2);
  } finally {
    globalThis.fetch = previous;
  }
});
