import test from 'node:test';
import assert from 'node:assert/strict';
import {computeElkPreview} from '../web/features/layout/elk.js';

const fixture = () => ({
  schemaVersion: '1.0', name: 'Test topology', zones: [],
  nodes: [
    {id: 'a', kind: 'switch', label: 'A', x: 110, y: 110, zoneId: null,
      ports: [{id: 'p0', name: 'p0', enabled: true, ipv4: null}]},
    {id: 'b', kind: 'switch', label: 'B', x: 370, y: 110, zoneId: null,
      ports: [{id: 'p1', name: 'p1', enabled: true, ipv4: null}]}
  ],
  links: [{id: 'cable', a: {node: 'a', port: 'p0'}, b: {node: 'b', port: 'p1'}, enabled: true}]
});

function fakeClass({spacing = 500, mutate = null, never = false} = {}) {
  return class FakeELK {
    static last = null;
    constructor() {this.stopped = false;this.calls = 0;this.constructor.last = this;}
    terminateWorker() {this.stopped = true;}
    async layout(graph) {
      this.calls += 1;
      if (never) return new Promise(() => {});
      const children = graph.children.map((node, index) =>
        ({...node, x: 12 + index * spacing, y: 12}));
      const ports = new Map(children.flatMap(n => (n.ports || [])
        .map(p => [p.id, {x:n.x + p.x, y:n.y + p.y}])));
      const edges = graph.edges.map(edge => {
        const start = ports.get(edge.sources[0]);
        const end = ports.get(edge.targets[0]);
        return {...edge, ...(start && end ? {sections:[{
          startPoint:start, bendPoints: start.y === end.y ? [] : [
            {x:(start.x+end.x)/2,y:start.y}, {x:(start.x+end.x)/2,y:end.y}],
          endPoint:end}]} : {})};
      });
      const result = {children, edges};
      mutate?.(result, this.calls);
      return result;
    }
  };
}

test('two-pass ELK preserves all network fields and produces exact port routes', async () => {
  const source=fixture(), before=JSON.stringify(source);
  const ELKClass=fakeClass();
  const result=await computeElkPreview(source, {ELKClass, requireWorker:false});
  assert.equal(JSON.stringify(source),before);
  assert.equal(result.project.nodes.length,2);
  assert.equal(result.project.links[0].id,'cable');
  assert.equal(result.nodeCount,2);
  assert.equal(result.linkCount,1);
  const a=result.project.nodes[0],b=result.project.nodes[1];
  assert.equal(result.paths.cable,'M '+(a.x+202)+' '+(a.y+71)+' L '+b.x+' '+(b.y+71));
  assert.equal(ELKClass.last.calls,2);
  assert.equal(ELKClass.last.stopped,true);
});
test('unknown or extra output node fails closed without mutation', async () => {
  const src=fixture(),before=JSON.stringify(src);
  const ELKClass=fakeClass({mutate:(out,pass)=>{if(pass===2)out.children.push({...out.children[0],id:'alien'});}});
  await assert.rejects(computeElkPreview(src,{ELKClass,requireWorker:false}),/nodidentiteter/);
  assert.equal(JSON.stringify(src),before);
  assert.equal(ELKClass.last.stopped,true);
});
test('undeclared physical cable endpoint fails closed', async () => {
  const src=fixture();src.links[0].b.port='unknown';
  const ELKClass=fakeClass();
  await assert.rejects(computeElkPreview(src,{ELKClass,requireWorker:false}),/okänd kabelände/);
});
test('out-of-bounds output is rejected, never scaled or clipped', async () => {
  const src=fixture(), before=JSON.stringify(src);
  const ELKClass=fakeClass({spacing:400000});
  await assert.rejects(computeElkPreview(src,{ELKClass,requireWorker:false}),/koordinatgränserna/);
  assert.equal(JSON.stringify(src),before);
});
test('invalid output coordinate fails closed', async () => {
  const src=fixture();
  const ELKClass=fakeClass({mutate:(out,pass)=>{if(pass===2)out.children[1].x=NaN;}});
  await assert.rejects(computeElkPreview(src,{ELKClass,requireWorker:false}),/ogiltig nod/);
});
test('layout must not silently flip a port side after the first pass', async () => {
  const src=fixture();
  const ELKClass=fakeClass({mutate:(out,pass)=>{if(pass===2){
    out.children[1].x=-400;
    const ports=new Map(out.children.flatMap(n=>(n.ports||[]).map(p=>[p.id,{x:n.x+p.x,y:n.y+p.y}])));
    for(const e of out.edges) e.sections[0].endPoint=ports.get(e.targets[0]);
  }}});
  await assert.rejects(computeElkPreview(src,{ELKClass,requireWorker:false}),/portens sida/);
});
test('abort kills the layout worker and does not modify the project', async () => {
  const src=fixture(),before=JSON.stringify(src),controller=new AbortController();
  const ELKClass=fakeClass({never:true});
  const promise=computeElkPreview(src,{ELKClass,signal:controller.signal,timeoutMs:300,requireWorker:false});
  controller.abort();
  await assert.rejects(promise,/avbröts/);
  assert.equal(JSON.stringify(src),before);
  assert.equal(ELKClass.last.stopped,true);
});
test('empty topology cannot produce an implicit network', async () => {
  const src=fixture();src.nodes=[];src.links=[];
  await assert.rejects(computeElkPreview(src,{ELKClass:fakeClass(),requireWorker:false}),/1–2 000/);
});
