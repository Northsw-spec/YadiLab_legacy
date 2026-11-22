// Presentation-only ELK adapter. Canonical project and historical receipts are never modified.
const WIDTH = 202;
const nodeHeight = node => Math.max(96, 78 + node.ports.length * 23);
const portKey = (nodeId, portId) => JSON.stringify([nodeId, portId]);
const cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const sameEndpoint = (a, b) => a.node === b.node && a.port === b.port;
const isFiniteNumber = value => typeof value === 'number' && Number.isFinite(value);
const boundedPoint = point => point && isFiniteNumber(point.x) && isFiniteNumber(point.y);
const fail = message => { throw new Error('ELK-layout avvisad: ' + message); };

function validateGraph(input, output, nodeIds, links) {
  if (!output || !Array.isArray(output.children) || !Array.isArray(output.edges)) {
    fail('ofullständigt svar från layoutmotorn');
  }
  const children = new Map();
  for (const node of output.children) {
    if (typeof node.id !== 'string' || children.has(node.id) ||
        !boundedPoint(node)) fail('dubbel, okänd eller ogiltig nod');
    children.set(node.id, node);
  }
  if (children.size !== nodeIds.size || [...nodeIds.values()].some(id => !children.has(id))) {
    fail('nodidentiteter har förändrats');
  }
  const edgeIds = new Set(links.map((_, index) => 'e' + index));
  const edges = new Map();
  for (const edge of output.edges) {
    if (!edgeIds.has(edge.id) || edges.has(edge.id)) fail('okänd eller duplicerad kabel');
    edges.set(edge.id, edge);
  }
  if (edges.size !== links.length) fail('kabelmängden har förändrats');
  // The layout engine may only reposition existing objects. Node dimensions,
  // virtual port identities and exact FIXED_POS offsets must survive intact.
  const inputs = new Map(input.children.map(node => [node.id, node]));
  for (const [id, outputNode] of children) {
    const expected = inputs.get(id);
    if (!expected || outputNode.width !== expected.width ||
        outputNode.height !== expected.height) fail('nodstorleken ändrades');
    if (expected.ports) {
      if (!Array.isArray(outputNode.ports) ||
          outputNode.ports.length !== expected.ports.length) {
        fail('portmängden ändrades');
      }
      const expectedPorts = new Map(expected.ports.map(port => [port.id, port]));
      const seen = new Set();
      for (const port of outputNode.ports) {
        const original = expectedPorts.get(port.id);
        if (seen.has(port.id) || !original || !boundedPoint(port) ||
            port.width !== original.width || port.height !== original.height ||
            port.x !== original.x || port.y !== original.y) {
          fail('portidentiteten eller FIXED_POS-positionen ändrades');
        }
        seen.add(port.id);
      }
    }
  }
  return {children, edges};
}

function validateRectangles(nodes) {
  const byX = [...nodes].sort((a, b) => a.x - b.x);
  for (let i = 0; i < byX.length; i++) {
    const a = byX[i];
    const h = nodeHeight(a);
    if (a.x < -100000 || a.y < -100000 ||
        a.x + WIDTH > 100000 || a.y + h > 100000) {
      fail('en nodrektangel ligger utanför koordinatgränserna');
    }
    for (let j = i + 1; j < byX.length && byX[j].x < a.x + WIDTH; j++) {
      const b = byX[j];
      if (Math.min(a.y + h, b.y + nodeHeight(b)) > Math.max(a.y, b.y)) {
        fail('överlapppande nodrektanglar');
      }
    }
  }
}

function prepare(source) {
  if (!source || !Array.isArray(source.nodes) || !Array.isArray(source.links) ||
      source.nodes.length === 0 || source.nodes.length > 2000 || source.links.length > 5000) {
    fail('projektet måste innehålla 1–2 000 noder och högst 5 000 deklarerade kablar');
  }
  const sortedNodes = [...source.nodes].sort((a, b) => cmp(a.id, b.id));
  const sortedLinks = [...source.links].sort((a, b) => cmp(a.id, b.id));
  const nodeIds = new Map(sortedNodes.map((n, i) => [n.id, 'n' + i]));
  if (nodeIds.size !== sortedNodes.length) fail('duplicerade noder');
  const ports = new Map();
  const linkedEnds = new Map();
  for (const node of sortedNodes) {
    if (!Array.isArray(node.ports) || node.ports.length > 128) fail('ogiltigt antal portar');
    node.ports.forEach((p, i) => {
      const key = portKey(node.id, p.id);
      if (ports.has(key)) fail('duplicerad port');
      ports.set(key, {node, port: p, index: i});
    });
  }
  for (const link of sortedLinks) {
    if (!nodeIds.has(link.a.node) || !nodeIds.has(link.b.node) ||
        !ports.has(portKey(link.a.node, link.a.port)) ||
        !ports.has(portKey(link.b.node, link.b.port))) fail('okänd kabelände');
    for (const [a, b] of [[link.a, link.b], [link.b, link.a]]) {
      const key = portKey(a.node, a.port);
      if (linkedEnds.has(key)) fail('flera kablar använder samma port');
      linkedEnds.set(key, b.node);
    }
  }
  return {sortedNodes, sortedLinks, nodeIds, ports, linkedEnds};
}

function graphFor(source, data, sides = null) {
  const {sortedNodes, sortedLinks, nodeIds, ports} = data;
  const portIds = new Map();
  const children = sortedNodes.map((node, i) => {
    const record = {id: nodeIds.get(node.id), width: WIDTH, height: nodeHeight(node)};
    if (sides) {
      record.layoutOptions = {'elk.portConstraints': 'FIXED_POS'};
      record.ports = node.ports.map((port, j) => {
        const key = portKey(node.id, port.id);
        const id = 'p' + i + '_' + j;
        portIds.set(key, id);
        const side = sides.get(key);
        return {id, width: 0, height: 0, x: side === 'left' ? 0 : WIDTH,
          y: 71 + j * 23,
          layoutOptions: {'elk.port.side': side === 'left' ? 'WEST' : 'EAST'}};
      });
    }
    return record;
  });
  const edges = sortedLinks.map((link, index) => {
    const [from, to] = [link.a, link.b].sort((a, b) =>
      cmp(a.node, b.node) || cmp(a.port, b.port));
    return {id: 'e' + index,
      sources: [sides ? portIds.get(portKey(from.node, from.port)) : nodeIds.get(from.node)],
      targets: [sides ? portIds.get(portKey(to.node, to.port)) : nodeIds.get(to.node)]};
  });
  return {
    graph: {id: 'root', layoutOptions: {
      'elk.algorithm': 'layered', 'elk.direction': 'RIGHT',
      'elk.edgeRouting': 'ORTHOGONAL',
      'elk.spacing.nodeNode': '55',
      'elk.layered.spacing.nodeNodeBetweenLayers': '90',
      'elk.layered.wrapping.strategy': 'MULTI_EDGE',
      // A wider target keeps the documented four-node chain out of a wrapped
      // same-column edge that crashes ELK's fixed-port crossing minimizer.
      'elk.aspectRatio': '3',
    }, children, edges}, portIds
  };
}

function chooseSides(data, preliminary) {
  const sides = new Map();
  for (const [key, info] of data.ports) {
    const otherNode = data.linkedEnds.get(key);
    const local = preliminary.children.get(data.nodeIds.get(info.node.id));
    const remote = otherNode && preliminary.children.get(data.nodeIds.get(otherNode));
    sides.set(key, remote && remote.x < local.x ? 'left' : 'right');
  }
  return sides;
}

function makeProposal(source, data, graph, response, sides) {
  const {children, edges} = validateGraph(graph.graph, response, data.nodeIds, data.sortedLinks);
  const geometry = new Map();
  for (const node of data.sortedNodes) {
    const el = children.get(data.nodeIds.get(node.id));
    geometry.set(node.id, {x: Math.round(el.x), y: Math.round(el.y)});
  }
  const left = Math.min(...data.sortedNodes.map(n => geometry.get(n.id).x));
  const right = Math.max(...data.sortedNodes.map(n => geometry.get(n.id).x + WIDTH));
  const top = Math.min(...data.sortedNodes.map(n => geometry.get(n.id).y));
  const bottom = Math.max(...data.sortedNodes.map(n => geometry.get(n.id).y + nodeHeight(n)));
  const dx = -Math.round((left + right) / 2);
  const dy = -Math.round((top + bottom) / 2);
  const project = {...source, nodes: source.nodes.map(n =>
    ({...n, x: geometry.get(n.id).x + dx, y: geometry.get(n.id).y + dy}))};
  validateRectangles(project.nodes);

  const nodeById = new Map(project.nodes.map(n => [n.id, n]));
  const portAt = endpoint => {
    const info = data.ports.get(portKey(endpoint.node, endpoint.port));
    if (!info) fail('okänd visuell port');
    const node = nodeById.get(endpoint.node);
    const remoteId = data.linkedEnds.get(portKey(endpoint.node, endpoint.port));
    const remote = remoteId && nodeById.get(remoteId);
    const side = remote && remote.x < node.x ? 'left' : 'right';
    if (sides.get(portKey(endpoint.node, endpoint.port)) !== side) {
      fail('portens sida ändrades mellan layoutpassen');
    }
    return {x: node.x + (side === 'left' ? 0 : WIDTH), y: node.y + 71 + info.index * 23};
  };
  const pointsById = {};
  const routes = {};
  for (let index = 0; index < data.sortedLinks.length; index++) {
    const link = data.sortedLinks[index];
    const result = edges.get('e' + index);
    if (!Array.isArray(result.sections) || result.sections.length !== 1) {
      fail('kabeln saknar en entydig rutt');
    }
    const section = result.sections[0];
    if (!Array.isArray(section.bendPoints) && section.bendPoints !== undefined) {
      fail('ogiltiga böjpunkter');
    }
    let points = [section.startPoint, ...(section.bendPoints || []), section.endPoint];
    if (!points.every(boundedPoint)) fail('ogiltiga kabelkoordinater');
    const [first] = [link.a, link.b].sort((a, b) =>
      cmp(a.node, b.node) || cmp(a.port, b.port));
    if (!sameEndpoint(first, link.a)) points = points.reverse();
    points = points.map(p => ({x: Math.round(p.x) + dx, y: Math.round(p.y) + dy}));
    const a = portAt(link.a), b = portAt(link.b);
    if (points[0].x !== a.x || points[0].y !== a.y ||
        points.at(-1).x !== b.x || points.at(-1).y !== b.y) {
      fail('kabeln når inte de verkliga portcirklarna');
    }
    for (let i = 1; i < points.length; i++) {
      if (points[i].x !== points[i - 1].x && points[i].y !== points[i - 1].y) {
        fail('icke-ortogonalt kabelsegment');
      }
    }
    const route = 'M ' + points[0].x + ' ' + points[0].y +
      points.slice(1).map(p => ' L ' + p.x + ' ' + p.y).join('');
    routes[link.id] = route;
    pointsById[link.id] = points;
  }
  return {project, paths: routes, nodeCount: project.nodes.length, linkCount: project.links.length};
}

// Resolves only after both actual ELK passes finish and the returned geometry is validated.
// Abort or timeout stops the dedicated Worker. No fallback to a main-thread bundled layout.
export async function computeElkPreview(source, {
  ELKClass = globalThis.ELK, workerUrl = '/vendor/elk-worker.js',
  signal = null, timeoutMs = 45000, requireWorker = true,
} = {}) {
  if (requireWorker && typeof Worker !== 'function') fail('webbläsaren stöder inte Web Worker');
  if (typeof ELKClass !== 'function') fail('den lokala ELK-motorn är inte installerad');
  if (signal?.aborted) fail('förhandsvisningen avbröts');
  const before = JSON.stringify(source);
  const input = JSON.parse(before);
  const data = prepare(input);
  const instance = new ELKClass({workerUrl});
  let timer, onAbort;
  const stop = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error('ELK-layouten överskred tidsgränsen')), timeoutMs);
    onAbort = () => reject(new Error('ELK-layouten avbröts'));
    signal?.addEventListener('abort', onAbort, {once: true});
  });
  const run = graph => Promise.race([instance.layout(graph), stop]);
  try {
    const first = graphFor(input, data);
    const preliminary = validateGraph(first.graph, await run(structuredClone(first.graph)), data.nodeIds, data.sortedLinks);
    const sides = chooseSides(data, preliminary);
    const second = graphFor(input, data, sides);
    const result = makeProposal(input, data, second, await run(structuredClone(second.graph)), sides);
    if (before !== JSON.stringify(source)) fail('projektet ändrades under beräkningen');
    return result;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onAbort);
    instance.terminateWorker?.();
  }
}
