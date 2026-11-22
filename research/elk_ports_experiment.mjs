// Isolated experiment B: ELK ports and full cable routes against unchanged YadiLab SVG geometry.
// Run: node research/elk_ports_experiment.mjs
import fs from "node:fs";
import {performance} from "node:perf_hooks";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const ELK=require("elkjs");
const elk=new ELK(),WIDTH=202,HEAD=66,ROW=23;
const height=n=>Math.max(96,HEAD+ROW*n.ports.length+12);
const round=x=>Math.round(x*1000)/1000;
function makeProject(n,target,kind){
  const nodes=Array.from({length:n},(_,i)=>({id:"N"+String(i).padStart(3,"0"),
    label:"N"+i,kind:"switch",x:0,y:0,zoneId:null,ports:[]}));
  const pair=[];
  if(kind==="star")for(let i=1;i<n;i++)pair.push([0,i]);
  else if(kind==="tree")for(let i=1;i<n;i++)pair.push([Math.floor((i-1)/2),i]);
  else if(kind==="ring")for(let i=0;i<n;i++)pair.push([i,(i+1)%n]);
  else for(let i=1;i<n;i++)pair.push([i-1,i]);
  const seen=new Set(pair.map(([a,b])=>[Math.min(a,b),Math.max(a,b)].join("-")));
  outer:for(let dist=2;pair.length<target && dist<n;dist++)for(let i=0;i<n;i++){
    const j=(i+dist)%n,key=[Math.min(i,j),Math.max(i,j)].join("-");
    if(i===j||seen.has(key))continue;
    seen.add(key);pair.push([i,j]);
    if(pair.length>=target)break outer;
  }
  const links=pair.slice(0,target).map(([a,b],i)=>{
    const ap="p"+nodes[a].ports.length,bp="p"+nodes[b].ports.length;
    nodes[a].ports.push({id:ap,name:ap,enabled:true,ipv4:null});
    nodes[b].ports.push({id:bp,name:bp,enabled:true,ipv4:null});
    return {id:"L"+i,a:{node:nodes[a].id,port:ap},b:{node:nodes[b].id,port:bp},enabled:true};
  });
  return {schemaVersion:"1.0",name:"synthetic "+kind,zones:[],nodes,links};
}
const specs=[
  {name:"repo_example",p:JSON.parse(fs.readFileSync("examples/explicit-three-device-demo.yadilab","utf8"))},
  {name:"star_17",p:makeProject(17,16,"star")},
  {name:"tree_47",p:makeProject(47,46,"tree")},
  {name:"ring_47",p:makeProject(47,47,"ring")},
  {name:"mesh_47",p:makeProject(47,180,"mesh")}
];
function endpoint(p,ep){
  const n=p.nodes.find(n=>n.id===ep.node),i=n?.ports.findIndex(q=>q.id===ep.port);
  if(!n||i<0)throw Error("Missing port");
  const link=p.links.find(l=>(l.a.node===ep.node && l.a.port===ep.port)||
     (l.b.node===ep.node&&l.b.port===ep.port));
  const remote=link&&p.nodes.find(n=>n.id===(link.a.node===ep.node?link.b.node:link.a.node));
  const side=remote && remote.x+WIDTH/2<n.x+WIDTH/2?"left":"right";
  return {x:n.x+(side==="left"?0:WIDTH),y:n.y+HEAD+i*ROW+5,side};
}
function graph(p,mode,assumedSides=null){
  const nodes=[...p.nodes].sort((a,b)=>a.id.localeCompare(b.id));
  const links=[...p.links].sort((a,b)=>a.id.localeCompare(b.id));
  const nodeIds=new Map(nodes.map((n,i)=>[n.id,"n"+i]));
  const portIds=new Map(),portOrigin=new Map();
  const children=nodes.map((n,i)=>{
    const c={id:nodeIds.get(n.id),width:WIDTH,height:height(n)};
    if(mode!=="node_only"){
      c.layoutOptions={"elk.portConstraints":mode.startsWith("fixed_pos")?"FIXED_POS":"FIXED_SIDE"};
      c.ports=n.ports.map((port,j)=>{
        const id="p"+i+"_"+j,key=n.id+"|"+port.id,side=assumedSides.get(key)||"right";
        portIds.set(key,id);portOrigin.set(id,key);
        if(mode==="fixed_side")return {id,width:6,height:6,
          layoutOptions:{"elk.port.side":side==="left"?"WEST":"EAST"}};
        const size=mode==="fixed_pos_zero"?0:12;
        return {id,width:size,height:size,
          x:(side==="left"?0:WIDTH)-size/2,y:HEAD+j*ROW+5-size/2,
          layoutOptions:{"elk.port.side":side==="left"?"WEST":"EAST"}};
      });
    }
    return c;
  });
  const edges=links.map((l,i)=>{
    // Stable presentation edge direction; NEVER changes the original undirected cable.
    const ends=[l.a,l.b].sort((a,b)=>a.node.localeCompare(b.node)||a.port.localeCompare(b.port));
    return {id:"e"+i,
      sources:[mode==="node_only"?nodeIds.get(ends[0].node):portIds.get(ends[0].node+"|"+ends[0].port)],
      targets:[mode==="node_only"?nodeIds.get(ends[1].node):portIds.get(ends[1].node+"|"+ends[1].port)]};
  });
  const root={id:"root",layoutOptions:{"elk.algorithm":"layered","elk.direction":"RIGHT",
    "elk.edgeRouting":"ORTHOGONAL","elk.spacing.nodeNode":"55",
    "elk.layered.spacing.nodeNodeBetweenLayers":"90"},children,edges};
  return {root,portIds,portOrigin,nodeIds,links,mode};
}
function makePlaced(p,g,out){
  if(!out.children||out.children.length!==p.nodes.length||!out.edges||out.edges.length!==p.links.length)
    throw Error("Different number of nodes/links");
  const all=new Set(out.children.map(n=>n.id));
  if(g.nodeIds.size!==all.size||[...g.nodeIds.values()].some(id=>!all.has(id)))
    throw Error("Node identity changed");
  const edgeIds=new Set(g.root.edges.map(e=>e.id));
  if(out.edges.some(e=>!edgeIds.has(e.id)))throw Error("Unknown edge");
  const xy=new Map(out.children.map(n=>[n.id,{x:Math.round(n.x),y:Math.round(n.y)}]));
  return {...p,nodes:p.nodes.map(n=>({...n,...xy.get(g.nodeIds.get(n.id))}))};
}
function sidePolicy(p){
  const m=new Map();
  for(const n of p.nodes)for(const port of n.ports)
    m.set(n.id+"|"+port.id,endpoint(p,{node:n.id,port:port.id}).side);
  return m;
}
function rayCross(a,b,rect){
  if(a.x===b.x)return a.x>rect.x && a.x<rect.x+rect.w&&
    Math.max(a.y,b.y)>rect.y&&Math.min(a.y,b.y)<rect.y+rect.h;
  if(a.y===b.y)return a.y>rect.y&&a.y<rect.y+rect.h&&
    Math.max(a.x,b.x)>rect.x&&Math.min(a.x,b.x)<rect.x+rect.w;
  return false;
}
function analyze(p,g,out,placed,assumedSides) {
  const origin=new Map([...g.nodeIds.entries()].map(([id,elkId])=>[elkId,id]));
  const els=new Map(out.children.map(n=>[n.id,n]));
  const centers=new Map(),entries=[];
  for(const n of out.children)for(const port of n.ports||[]){
    const id=g.portOrigin.get(port.id),sizeX=port.width||0,sizeY=port.height||0;
    if(!id)throw Error("ELK invented unknown port "+port.id);
    const val={x:n.x+port.x+sizeX/2,y:n.y+port.y+sizeY/2};
    centers.set(port.id,val);entries.push({id,val});
  }
  if(entries.length!==[...p.nodes].reduce((a,n)=>a+n.ports.length,0))
    throw Error("Port identity/cardinality changed");
  let mismatched=0,max=0,sidesChanged=0,endpointBad=0,endpointMax=0;
  for(const n of placed.nodes)for(const port of n.ports){
    const key=n.id+"|"+port.id,pid=g.portIds.get(key),expected=endpoint(placed,{node:n.id,port:port.id});
    const actual=centers.get(pid);if(!actual)throw Error("Missing port mapping "+key);
    const distance=Math.hypot(actual.x-expected.x,actual.y-expected.y);
    max=Math.max(max,distance);if(distance>0.51)mismatched++;
    if(assumedSides && assumedSides.get(key)!==expected.side)sidesChanged++;
  }
  let sections=0,obstacles=0,nonOrthogonalSegments=0;
  const index=new Map(placed.nodes.map(n=>[n.id,n]));
  const edgeIndex=new Map(g.root.edges.map((e,i)=>[e.id,i]));
  for(const edge of out.edges){
    const idx=edgeIndex.get(edge.id);
    if(idx===undefined)throw Error("Unknown edge id "+edge.id);
    const expected=g.root.edges[idx],wire=g.links[idx];
    if(!expected||!wire)throw Error("Missing edge identity");
    for(const section of edge.sections||[]){
      sections++;
      const pts=[section.startPoint,...section.bendPoints||[],section.endPoint];
      const start=centers.get(expected.sources[0]),end=centers.get(expected.targets[0]);
      const a=Math.hypot(pts[0].x-start.x,pts[0].y-start.y);
      const b=Math.hypot(pts[pts.length-1].x-end.x,pts[pts.length-1].y-end.y);
      endpointMax=Math.max(endpointMax,a,b);if(a>0.51||b>0.51)endpointBad++;
      for(let i=1;i<pts.length;i++)
        if(Math.abs(pts[i].x-pts[i-1].x)>0.1&&Math.abs(pts[i].y-pts[i-1].y)>0.1)nonOrthogonalSegments++;
      for(const n of placed.nodes)if(n.id!==wire.a.node&&n.id!==wire.b.node)
        for(let i=1;i<pts.length;i++)
          if(rayCross(pts[i-1],pts[i],{x:n.x,y:n.y,w:WIDTH,h:height(n)})){obstacles++;break;}
    }
  }
  return {nodeCount:p.nodes.length,linkCount:p.links.length,portCount:entries.length,
    sections,mismatchedYadiLabPortCenters:mismatched,maxYadiLabPortCenterError:round(max),
    unstableSides:sidesChanged,sectionEndpointMismatch: endpointBad,
    maxSectionEndpointError:round(endpointMax),nonOrthogonalSegments,
    edgeSegmentsThroughOtherNodes:obstacles,
    truePortGeometricCompatibility:mismatched===0&&endpointBad===0,
    note:"SVG renderer still uses endpoint(project, port); no production UI change"};
}
const results={experiment:"ELK FIXED_POS vs YadiLab port endpoint geometry",elkVersion:require("elkjs/package.json").version,
  date:new Date().toISOString(),cases:{},errors:{}};
for(const spec of specs){
  results.cases[spec.name]={};
  const src=JSON.stringify(spec.p);
  try{
    const baseG=graph(spec.p,"node_only");
    const before=performance.now(),baseOut=await elk.layout(baseG.root);
    const preliminary=makePlaced(spec.p,baseG,baseOut),sides=sidePolicy(preliminary);
    results.cases[spec.name].preliminaryNodeOnlyMs=round(performance.now()-before);
    for(const mode of ["fixed_side","fixed_pos_12","fixed_pos_zero"]){
      try {
        const g=graph(spec.p,mode,sides),t=performance.now(),out=await elk.layout(g.root);
        const placed=makePlaced(spec.p,g,out),metrics=analyze(spec.p,g,out,placed,sides);
        results.cases[spec.name][mode]={...metrics,elapsedMs:round(performance.now()-t)};
        console.log("PORTS",spec.name,mode,JSON.stringify(results.cases[spec.name][mode]));
      }catch(e) {
        results.errors[spec.name+"_"+mode]=String(e.stack||e);
        console.error("PORTS_ERROR",spec.name,mode,String(e));
      }
    }
    if(JSON.stringify(spec.p)!==src)throw Error("Original source project mutated");
  }catch(e){results.errors[spec.name+"_base"]=String(e.stack||e);}
}
fs.mkdirSync("research/elk-results",{recursive:true});
fs.writeFileSync("research/elk-results/ports.json",JSON.stringify(results,null,2)+"\n");
console.log("PORT_VERDICT",JSON.stringify({
  matches:Object.entries(results.cases).map(([key,c])=>({case:key,
    fixedPos12:c.fixed_pos_12?.truePortGeometricCompatibility||false,
    fixedPos0:c.fixed_pos_zero?.truePortGeometricCompatibility||false})),
  errors:Object.keys(results.errors)}));
if(Object.keys(results.errors).length)process.exitCode=1;
