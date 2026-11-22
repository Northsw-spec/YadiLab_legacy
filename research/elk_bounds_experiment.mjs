// Isolated experiment A: fit real ELK 0.13.0 layouts inside YadiLab coordinates.
// Run: node research/elk_bounds_experiment.mjs
// Does not modify project files, import history or production code.
import fs from "node:fs";
import {performance} from "node:perf_hooks";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const ELK=require("elkjs");
const elk=new ELK();
const WIDTH=202;
const height=n=>Math.max(96,78+n.ports.length*23);
const round=x=>Math.round(x*1000)/1000;
function makeProject(n=2000, target=5000) {
  const nodes=Array.from({length:n},(_,i)=>({
    id:"N"+String(i).padStart(5,"0"), label:"Node "+i,kind:"switch",zoneId:null,
    x:110+260*(i%Math.ceil(Math.sqrt(n))),y:110+220*Math.floor(i/Math.ceil(Math.sqrt(n))),ports:[]}));
  const pairs=[];
  for(let i=1;i<n;i++)pairs.push([i-1,i]);
  const seen=new Set(pairs.map(([a,b])=>a+"-"+b));
  outer:for(let distance=2;distance<n;distance++)for(let i=0;i<n;i++){
    const j=(i+distance)%n,key=[Math.min(i,j),Math.max(i,j)].join("-");
    if(i===j||seen.has(key))continue;
    seen.add(key);pairs.push([i,j]);
    if(pairs.length>=target)break outer;
  }
  const links=pairs.slice(0,target).map(([a,b],i)=>{
    const p="p"+nodes[a].ports.length,q="p"+nodes[b].ports.length;
    nodes[a].ports.push({id:p,name:p,enabled:true,ipv4:null});
    nodes[b].ports.push({id:q,name:q,enabled:true,ipv4:null});
    return {id:"L"+i,a:{node:nodes[a].id,port:p},b:{node:nodes[b].id,port:q},enabled:true};
  });
  return {schemaVersion:"1.0",name:"synthetic 2000 5000",zones:[],nodes,links};
}
function rootsBfs(project) {
  const adj=new Map(project.nodes.map(n=>[n.id,[]]));
  for(const l of project.links) {
    adj.get(l.a.node).push(l.b.node);
    adj.get(l.b.node).push(l.a.node);
  }
  for(const a of adj.values())a.sort();
  const bfs=start=>{
    const dist=new Map([[start,0]]),queue=[start];
    for(let i=0;i<queue.length;i++)for(const other of adj.get(queue[i]))
      if(!dist.has(other)){dist.set(other,dist.get(queue[i])+1);queue.push(other);}
    const far=[...dist.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))[0];
    return {dist,far,parents:queue.length};
  };
  const initial=[...adj.keys()].sort()[0],first=bfs(initial).far[0];
  const b=bfs(first),otherEnd=b.far[0],c=bfs(otherEnd);
  // Midpoint of a diameter-like sweep: minimize maximum graph distance to two far endpoints.
  const start=[...adj.keys()].sort((x,y)=>Math.max(b.dist.get(x),c.dist.get(x))-Math.max(b.dist.get(y),c.dist.get(y))||x.localeCompare(y))[0];
  const fromCenter=bfs(start);
  if(fromCenter.dist.size!==project.nodes.length)throw Error("BFS corpus unexpectedly disconnected");
  return {dist:fromCenter.dist,center:start,maxDepth:Math.max(...fromCenter.dist.values())};
}
function buildGraph(p,option) {
  const sorted=[...p.nodes].sort((a,b)=>a.id.localeCompare(b.id));
  const idByName=new Map(sorted.map((n,i)=>[n.id,"n"+i]));
  const edges=[...p.links].sort((a,b)=>a.id.localeCompare(b.id));
  let info={orientation:"documented A/B"};
  let ranks=null;
  if(option.orient==="bfs"){
    info=rootsBfs(p); ranks=info.dist;
  }
  const elkEdges=edges.map((l,i)=>{
    let a=l.a.node,b=l.b.node;
    if(ranks) {
      const ca=ranks.get(a),cb=ranks.get(b);
      if(ca>cb || (ca===cb && a.localeCompare(b)>0)) [a,b]=[b,a];
    }
    return {id:"e"+i,sources:[idByName.get(a)],targets:[idByName.get(b)]};
  });
  const graph={
    id:"root",
    layoutOptions:{
      "elk.algorithm":"layered",
      "elk.direction":"RIGHT",
      "elk.edgeRouting":"ORTHOGONAL",
      "elk.spacing.nodeNode":"55",
      "elk.layered.spacing.nodeNodeBetweenLayers":"90",
      ...(option.layoutOptions||{})
    },
    children:sorted.map(n=>({id:idByName.get(n.id),width:WIDTH,height:height(n)})),
    edges:elkEdges
  };
  return {graph,sorted,idByName,edgeIds:edges.map(e=>e.id),orientation:info};
}
function collisionCount(nodes){
  let hits=0;
  const ordered=[...nodes].sort((a,b)=>a.x-b.x);
  for(let i=0;i<ordered.length;i++) {
    const a=ordered[i];
    for(let j=i+1;j<ordered.length;j++){
      const b=ordered[j];
      if(b.x>=a.x+a.width)break;
      if(Math.min(a.y+a.height,b.y+b.height)>Math.max(a.y,b.y))hits++;
    }
  }
  return hits;
}
function analyze(p,model,out,ms){
  if(out.children.length!==p.nodes.length||out.edges.length!==p.links.length)
    throw Error("Output changed node/edge count");
  const expected=new Set(model.graph.children.map(n=>n.id));
  const actual=new Set(out.children.map(n=>n.id));
  if(expected.size!==actual.size||[...expected].some(id=>!actual.has(id)))
    throw Error("Node IDs not preserved");
  const expectedE=new Set(model.graph.edges.map(e=>e.id));
  if(new Set(out.edges.map(e=>e.id)).size!==expectedE.size||
     out.edges.some(e=>!expectedE.has(e.id))) throw Error("Edge ID mismatch");
  const raw=out.children.map(n=>({...n,x:Math.round(n.x),y:Math.round(n.y)}));
  const xLo=Math.min(...raw.map(n=>n.x)),yLo=Math.min(...raw.map(n=>n.y));
  const xHi=Math.max(...raw.map(n=>n.x+n.width)),yHi=Math.max(...raw.map(n=>n.y+n.height));
  const dx=-Math.round((xLo+xHi)/2),dy=-Math.round((yLo+yHi)/2);
  const normalized=raw.map(n=>({...n,x:n.x+dx,y:n.y+dy}));
  const invalidBefore=raw.filter(n=>!Number.isFinite(n.x)||!Number.isFinite(n.y)||
    n.x< -100000||n.y< -100000||n.x+n.width>100000||n.y+n.height>100000).length;
  const invalidAfter=normalized.filter(n=>n.x< -100000||n.y< -100000||
    n.x+n.width>100000||n.y+n.height>100000).length;
  const overlaps=collisionCount(normalized);
  const maxPerDimension=Math.max(xHi-xLo,yHi-yLo);
  return {durationMs:round(ms),layoutBounds:{minX:xLo,minY:yLo,maxX:xHi,maxY:yHi,
      width:xHi-xLo,height:yHi-yLo},normalization:{dx,dy,invalidBefore,invalidAfter,
      fitsWithoutScaling:invalidAfter===0},rectOverlaps:overlaps,
    identitiesPreserved:true,fullRectFits:invalidAfter===0,maxPerDimension,
    canvasZoomNote:"fit may require viewBox > 9000 (current zoom clamp); readability NOT verified",
    edgeSectionCount:out.edges.reduce((s,e)=>s+(e.sections?.length||0),0)};
}
const p=makeProject(),before=JSON.stringify(p);
const scenarios=[
  {name:"baseline",orient:"original"},
  {name:"wrapped_single",orient:"original",layoutOptions:{
    "elk.layered.wrapping.strategy":"SINGLE_EDGE","elk.aspectRatio":"1.6"}},
  {name:"wrapped_multi",orient:"original",layoutOptions:{
    "elk.layered.wrapping.strategy":"MULTI_EDGE","elk.aspectRatio":"1.6"}},
  {name:"bfs_orientation",orient:"bfs",layoutOptions:{
    "elk.spacing.nodeNode":"30","elk.layered.spacing.nodeNodeBetweenLayers":"45"}},
  {name:"bfs_plus_wrapped_multi",orient:"bfs",layoutOptions:{
    "elk.spacing.nodeNode":"30","elk.layered.spacing.nodeNodeBetweenLayers":"45",
    "elk.layered.wrapping.strategy":"MULTI_EDGE","elk.aspectRatio":"1.6"}}
];
const results={experiment:"ELK bounds + no-resize translation",date:new Date().toISOString(),
  elkVersion:require("elkjs/package.json").version,exactCorpus:{nodes:2000,edges:5000},scenarios:{},failures:{}};
for(const option of scenarios){
  try {
    const model=buildGraph(p,option);
    const started=performance.now();
    const out=await elk.layout(model.graph);
    const metric=analyze(p,model,out,performance.now()-started);
    results.scenarios[option.name]={...metric,orientation:option.orient,
      rooting:option.orient==="bfs"?{center:model.orientation.center,
      maxDepth:model.orientation.maxDepth}:undefined,
      layoutOptions:model.graph.layoutOptions};
    if(option.name==="wrapped_multi" && metric.fullRectFits && metric.rectOverlaps===0){
      const byElkId=new Map(out.children.map(n=>[n.id,n]));
      const proposed=structuredClone(p);
      for(const n of proposed.nodes){
        const en=byElkId.get(model.idByName.get(n.id));
        if(!en)throw Error("Missing node when exporting accepted-coordinate proposal");
        n.x=Math.round(en.x)+metric.normalization.dx;
        n.y=Math.round(en.y)+metric.normalization.dy;
      }
      fs.mkdirSync("research/elk-results",{recursive:true});
      fs.writeFileSync("research/elk-results/wrapped_candidate.json",JSON.stringify(proposed)+"\n");
      results.scenarios[option.name].candidatePath="research/elk-results/wrapped_candidate.json";
    }
    if(JSON.stringify(p)!==before)throw Error("Source project mutated");
    console.log("BOUNDS",option.name,JSON.stringify(results.scenarios[option.name]));
  } catch(error){
    results.failures[option.name]=String(error.stack||error);
    console.error("BOUNDS_ERROR",option.name,String(error));
  }
}
const outdir="research/elk-results";fs.mkdirSync(outdir,{recursive:true});
fs.writeFileSync(outdir+"/bounds.json",JSON.stringify(results,null,2)+"\n");
console.log("BOUNDS_VERDICT",JSON.stringify({
  anyValid:Object.values(results.scenarios).some(x=>x.fullRectFits&&x.rectOverlaps===0),
  scenarios:Object.keys(results.scenarios),
  failures:Object.keys(results.failures)}));
if(Object.keys(results.scenarios).length!==scenarios.length)process.exitCode=1;
