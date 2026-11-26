import test from 'node:test';
import assert from 'node:assert/strict';
import {setupWorkspacePanels} from '../web/ui/workspace-panels.js';

class FakeNode {
  constructor(tag, name = '') {
    this.tagName = tag;
    this.name = name;
    this.children = [];
    this.dataset = {};
    this.attributes = {};
    this.listeners = new Map();
    this.open = false;
    this.textContent = '';
    this.className = '';
    this.replaced = 0;
    this.lookup = {};
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; this.replaced += 1; }
  addEventListener(type, handler) {
    const existing = this.listeners.get(type) || [];
    this.listeners.set(type, [...existing, handler]);
  }
  fire(type) { for (const handler of this.listeners.get(type) || []) handler(); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
  querySelector(selector) { return this.lookup[selector] ?? null; }
  querySelectorAll(selector) { return this.lookup[selector] ?? []; }
}

function makeDom(t) {
  const previous = {document: globalThis.document, Node: globalThis.Node};
  t.after(() => {
    if (previous.document === undefined) delete globalThis.document;
    else globalThis.document = previous.document;
    if (previous.Node === undefined) delete globalThis.Node;
    else globalThis.Node = previous.Node;
  });
  globalThis.Node = FakeNode;
  const byId = new Map();
  const element = name => new FakeNode('div', name);
  for (const key of ['node-list', 'link-list', 'zone-list', 'toggle-dropdowns']) {
    byId.set(key, element(key));
  }
  const inventory = element('inventory');
  const headings = ['nodes', 'links', 'zones'].map(element);
  const intro = element('intro');
  const stats = element('stats');
  const actions = element('actions');
  const saved = element('saved');
  inventory.lookup[':scope > .list-header'] = headings;
  inventory.lookup['.panel-section:not(.action-stack)'] = intro;
  inventory.lookup['.stats'] = stats;
  inventory.lookup['.action-stack'] = actions;
  inventory.lookup['.left-bottom'] = saved;

  const tools = element('right');
  const inspectorTitle = element('inspectorTitle');
  const inspectorBody = element('inspectorBody');
  const pingPanel = element('ping');
  const tracePanel = element('trace');
  const pingHeader = element('ping-header');
  pingHeader.textContent = '  ICMP  ';
  pingPanel.lookup.h3 = pingHeader;
  tracePanel.setAttribute('aria-label', 'Trace evidens');
  tools.lookup[':scope > .trace-panel'] = [pingPanel, tracePanel];
  tools.lookup[':scope > .inspector-title'] = inspectorTitle;
  tools.lookup[':scope > .inspector-body'] = inspectorBody;
  const cards = [];
  globalThis.document = {
    querySelector(selector) {
      return {'.left-panel': inventory, '.right-panel': tools}[selector] ?? null;
    },
    querySelectorAll(selector) {
      if (selector === '.dropdown-card[data-dropdown-card="true"]') {
        return cards.filter(card => card.dataset.dropdownCard === 'true');
      }
      return [];
    },
    getElementById(id) { return byId.get(id) ?? null; },
    createElement(tag) {
      const node = new FakeNode(tag);
      if (tag === 'details') cards.push(node);
      return node;
    },
    createTextNode(value) {
      const node = new FakeNode('#text');
      node.textContent = String(value);
      return node;
    },
  };
  return {inventory, tools, byId, cards, headings, intro, stats, actions, saved,
          inspectorTitle, inspectorBody, pingPanel, tracePanel};
}

function title(card) {
  const summary = card.children[0];
  return summary.children.map(child => child.textContent).join('');
}

test('workspace panel extraction retains source DOM identity and grouping', t => {
  const dom = makeDom(t);
  setupWorkspacePanels();
  assert.equal(dom.inventory.replaced, 1);
  assert.equal(dom.tools.replaced, 1);
  assert.equal(dom.cards.length, 5);
  assert.deepEqual(dom.cards.map(title), [
    'Inventering', 'Sparade projekt och mallar', 'Inspektör / egenskaper',
    'ICMP', 'Trace evidens',
  ]);
  assert.deepEqual(dom.inventory.children, dom.cards.slice(0, 2));
  assert.deepEqual(dom.tools.children, dom.cards.slice(2));
  const firstBody = dom.cards[0].children[1];
  assert.deepEqual(firstBody.children, [dom.intro, dom.stats, dom.actions,
    dom.headings[0], dom.byId.get('node-list'), dom.headings[1],
    dom.byId.get('link-list'), dom.headings[2], dom.byId.get('zone-list')]);
  assert.deepEqual(dom.cards[1].children[1].children, [dom.saved]);
  assert.deepEqual(dom.cards[2].children[1].children,
    [dom.inspectorTitle, dom.inspectorBody]);
  assert.deepEqual(dom.cards[3].children[1].children, [dom.pingPanel]);
  assert.deepEqual(dom.cards[4].children[1].children, [dom.tracePanel]);
  assert.equal(dom.byId.get('toggle-dropdowns').attributes['aria-pressed'], 'false');
});

test('toggle is registered once; open/partial-open states project to aria-pressed', t => {
  const dom = makeDom(t);
  setupWorkspacePanels();
  const button = dom.byId.get('toggle-dropdowns');
  assert.equal((button.listeners.get('click') || []).length, 1);
  assert.ok(dom.cards.every(card => (card.listeners.get('toggle') || []).length === 1));
  button.fire('click');
  assert.ok(dom.cards.every(card => card.open));
  assert.equal(button.attributes['aria-pressed'], 'true');
  dom.cards[1].open = false;
  dom.cards[1].fire('toggle');
  assert.equal(button.attributes['aria-pressed'], 'false');
  button.fire('click');
  assert.ok(dom.cards.every(card => card.open));
  assert.equal(button.attributes['aria-pressed'], 'true');
  button.fire('click');
  assert.ok(dom.cards.every(card => !card.open));
  assert.equal(button.attributes['aria-pressed'], 'false');
});
