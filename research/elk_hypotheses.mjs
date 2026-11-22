// Isolated YadiLab/ELK hypothesis experiments. No project mutation or GitHub write here.
import fs from "node:fs";
import {performance} from "node:perf_hooks";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const ELK=require("elkjs");
const elk=new ELK();
const date=new Date().toISOString();
const numbers=(xs)=>({min:Math.min(...xs),max:Math.max(...xs),mean:xs.reduce((s,x)=>s+x,0)/xs.length});
const fix=(x)=>Math.round(x*1000)/1000;
const height=(node)=>Math.max(96,78+node.ports.length*23);
function project(n, targetEdges, kind="tree"){
  const nodes=Array.from({length:n},(_,i)=>({id:"N"+String(i).padStart(5,"0"),label:"Node "+i,kind:"switch",
    x:110+260*(i%Math.ceil(Math.sqrt(n))),y:110+220*Math.floor(i/Math.ceil(Math.sqrt(n))),
    zoneId:null,ports:[]}));
  const pairs=[];
  if(kind==="star") for(let i=1;i<n;i++) pairs.push([0,i]);
  else if(kind==="tree") for(let i=1;i<n;i++) pairs.push([Math.floor((i-1)/2),i]);
  else if(kind==="ring") for(let i=0;i<n;i++) pairs.push([i,(i+1)%n]);
  else for(let i=1;i<n;i++) pairs.push([i-1,i]);
  const seen=new Set(pairs.map(([a,b])=>[Math.min(a,b),Math.max(a,b)].join("-")));
  if(targetEdges>pairs.length) {
    outer: for(let distance=2;distance<n;distance++) for(let i=0;i<n;i++){
      const j=(i+distance)%n, key=[Math.min(i,j),Math.max(i,j)].join("-");
      if(i===j || seen.has(key)) continue;
      seen.add(key);pairs.push([i,j]);
      if(pairs.length>=targetEdges) break outer;
    }
  }
  const links=pairs.slice(0,targetEdges).map(([a,b],i)=>{
    const aid="p"+nodes[a].ports.length, bid="p"+nodes[b].ports.length;
    nodes[a].ports.push({id:aid,name:aid,enabled:true,ipv4:null});
    nodes[b].ports.push({id:bid,name:bid,enabled:true,ipv4:null});
    return {id:"L"+i,a:{node:nodes[a].id,port:aid},b:{node:nodes[b].id,port:bid},enabled:true};
  });
  return {schemaVersion:"1.0",name:"synthetic "+kind+" "+n,zones:[],nodes,links};
}
const rect=(n)=>({x:n.x,y:n.y,w:202,h:height(n)});
const overlaps=(p)=>{
  let count=0; for(let i=0;i<p.nodes.length;i++){const a=rect(p.nodes[i]);
    for(let j=i+1;j<p.nodes.length;j++){const b=rect(p.nodes[j]);if(Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)&&Math.min(a.y+a.h,b.y+b.h)>Math.max(a.y,b.y))count++;}}
  return count;
};
function adapter(p,ports=false){
  const nodes=[...p.nodes].sort((a,b)=>a.id.localeCompare(b.id));
  const idMap=new Map(nodes.map((n,i)=>[n.id,"n"+i]));
  const portMap=new Map(), portRoles=new Map();
  const links=[...p.links].sort((a,b)=>a.id.localeCompare(b.id));
  for(const link of links){
    const sorted=[link.a,link.b].sort((a,b)=>a.node.localeCompare(b.node)||a.port.localeCompare(b.port));
    portRoles.set(sorted[0].node+"|"+sorted[0].port,"EAST");
    portRoles.set(sorted[1].node+"|"+sorted[1].port,"WEST");
  }
  const children=nodes.map((n,i)=>{
    const c={id:idMap.get(n.id),width:202,height:height(n)};
    if(ports){
      c.layoutOptions={"elk.portConstraints":"FIXED_SIDE"};
      c.ports=n.ports.map((port,j)=>{
        const id="p"+i+"_"+j;
        portMap.set(n.id+"|"+port.id,id);
        return {id,width:6,height:6,layoutOptions:{"elk.port.side":portRoles.get(n.id+"|"+port.id)||"EAST"}};
      });
    }
    return c;
  });
  const edges=links.map((l,i)=>{
    const ends=[l.a,l.b].sort((a,b)=>a.node.localeCompare(b.node)||a.port.localeCompare(b.port));
    return {id:"e"+i,sources:[ports?portMap.get(ends[0].node+"|"+ends[0].port):idMap.get(ends[0].node)],
      targets:[ports?portMap.get(ends[1].node+"|"+ends[1].port):idMap.get(ends[1].node)]};
  });
  return {graph:{id:"root",layoutOptions:{"elk.algorithm":"layered","elk.direction":"RIGHT",
    "elk.edgeRouting":"ORTHOGONAL","elk.spacing.nodeNode":"55",
    "elk.layered.spacing.nodeNodeBetweenLayers":"90"},children,edges},
    sourceIds:nodes.map(n=>n.id), sourceLinkIds:links.map(l=>l.id),idMap,portMap};
}
function validate(p, out, adap){
  if(!out.children || out.children.length!==p.nodes.length) throw Error("Missing/extra ELK nodes");
  if(!out.edges || out.edges.length!==p.links.length) throw Error("Missing/extra ELK links");
  const originals=new Set(adap.graph.children.map(n=>n.id)), next=new Set(out.children.map(n=>n.id));
  if(originals.size!==next.size||[...originals].some(id=>!next.has(id))) throw Error("Node IDs differ");
  const expectedEdges=new Set(adap.graph.edges.map(e=>e.id));
  if(out.edges.some(e=>!expectedEdges.has(e.id))) throw Error("Unknown ELK links");
  const coordinateMap=new Map(out.children.map(n=>[n.id,[Math.round(n.x),Math.round(n.y)]]));
  const placed=structuredClone(p);
  placed.nodes.forEach(n=>{const [x,y]=coordinateMap.get(adap.idMap.get(n.id));
    if(!Number.isFinite(x)||!Number.isFinite(y)||x< -100000||y< -100000||
      x+202>100000||y+height(n)>100000) throw Error("Coordinates out of bounds");
    n.x=x;n.y=y;});
  return placed;
}
function endpoint(p,ep){
  const n=p.nodes.find(x=>x.id===ep.node),idx=n.ports.findIndex(x=>x.id===ep.port);
  if(idx<0)throw Error("Unknown port");
  const l=p.links.find(l=>(l.a.node===ep.node&&l.a.port===ep.port)||(l.b.node===ep.node&&l.b.port===ep.port));
  const remote=l&&p.nodes.find(n=>n.id===(l.a.node===ep.node?l.b.node:l.a.node));
  const side=remote&&remote.x+101<n.x+101?"left":"right";
  return {x:n.x+(side==="left"?0:202),y:n.y+66+idx*23+5,side};
}
function routePoints(a,b){
  const da=a.side==="right"?1:-1,db=b.side==="right"?1:-1;
  if(da===-db&&(a.x-b.x)*da<0) {
    if(a.y===b.y) return [a,b];
    const x=(a.x+b.x)/2;return [a,{x,y:a.y},{x,y:b.y},b];
  }
  const xa=a.x+da*36,xb=b.x+db*36,ym=(a.y+b.y)/2+(a.y===b.y?28:0);
  return [a,{x:xa,y:a.y},{x:xa,y:ym},{x:xb,y:ym},{x:xb,y:b.y},b];
}
function hitsRect(pts,r){
  for(let i=1;i<pts.length;i++){
    const a=pts[i-1],b=pts[i];
    if(a.x===b.x && a.x>r.x && a.x<r.x+r.w && Math.max(a.y,b.y)>r.y && Math.min(a.y,b.y)<r.y+r.h) return true;
    if(a.y===b.y && a.y>r.y && a.y<r.y+r.h && Math.max(a.x,b.x)>r.x && Math.min(a.x,b.x)<r.x+r.w) return true;
  }
  return false;
}
function cableObstacles(p,limit=100){
  if(p.nodes.length>limit)return null;
  let count=0,hitEdges=0;
  for(const l of p.links){
    const pts=routePoints(endpoint(p,l.a),endpoint(p,l.b));
    const hits=p.nodes.filter(n=>n.id!==l.a.node&&n.id!==l.b.node&&hitsRect(pts,rect(n))).length;
    count+=hits;if(hits)hitEdges++;
  }
  return {nodeCrossings:count,hitEdges};
}
async function layout(p,ports=false){
  const source=JSON.stringify(p),a=adapter(p,ports),t=performance.now();
  const out=await elk.layout(a.graph);
  const durationMs=performance.now()-t;
  if(JSON.stringify(p)!==source)throw Error("Source project mutated");
  const placed=validate(p,out,a);
  return {placed,out,ms:fix(durationMs),overlaps:overlaps(placed),graph:a};
}
function summary(p,r){return {nodes:p.nodes.length,links:p.links.length,ms:r.ms,
  originalOverlaps:overlaps(p),newOverlaps:r.overlaps,
  originalCableCollisions:cableObstacles(p),newCableCollisions:cableObstacles(r.placed)};}
const record={date,elkVersion:require("elkjs/package.json").version,node:process.version,results:{},errors:{}};
async function test(id,callback){try {record.results[id]=await callback();console.log(id+" "+JSON.stringify(record.results[id]));}
 catch(e){record.errors[id]=String(e.stack||e);console.error(id+" ERROR "+String(e));}}
if(process.argv.includes("--stress")){
 await test("H7_stress_2000_5000",async()=>summary(project(2000,5000,"mesh"),await layout(project(2000,5000,"mesh"))));
}else{
 await test("H1_real_elk_three_node_adapter",async()=>{
   const p=JSON.parse(fs.readFileSync("examples/explicit-three-device-demo.yadilab","utf8"));
   const r=await layout(p);return {inputUnchanged:true,exactNodeAndLinkIds:true,...summary(p,r)};
 });
 for(const kind of ["tree","star","ring","mesh"]){
   await test("H2_node_only_"+kind,async()=>{
      const p=project(47,kind==="mesh"?180:(kind==="ring"?47:46),kind),r=await layout(p);
      return summary(p,r);
   });
 }
 await test("H3_explicit_port_and_edge_sections",async()=>{
   const p=project(10,12,"mesh"),r=await layout(p,true);
   const sectionCount=r.out.edges.reduce((s,e)=>s+(e.sections?.length||0),0);
   if(!sectionCount)throw Error("No ELK routed edge sections returned");
   return {...summary(p,r),edgeSections:sectionCount,portsMapped:r.graph.portMap.size,
     returnedPortCount:r.out.children.reduce((s,n)=>s+(n.ports?.length||0),0)};
 });
 await test("H6_coordinate_replay",async()=>{
   const p=project(47,46,"tree"),coordinates=[],times=[];
   for(let i=0;i<7;i++){
     const q=structuredClone(p);
     if(i%2){q.nodes.reverse();q.links.reverse();q.links=q.links.map(l=>({...l,a:l.b,b:l.a}));}
     const r=await layout(q);times.push(r.ms);
     coordinates.push(JSON.stringify(r.placed.nodes.sort((a,b)=>a.id.localeCompare(b.id)).map(n=>[n.id,n.x,n.y])));
   }
   return {identicalRuns:coordinates.filter(s=>s===coordinates[0]).length,totalRuns:coordinates.length,
      timesMs:numbers(times)};
 });
 await test("H8_synthetic_47_not_original_workbook",async()=>{
   const p=project(47,46,"tree"),r=await layout(p);return {...summary(p,r),
     warning:"NOT real Arvidsjaur workbook; cannot validate user's original 47-node lab"};});
}
fs.mkdirSync("research/elk-results",{recursive:true});
fs.writeFileSync("research/elk-results/"+(process.argv.includes("--stress")?"stress":"node")+".json",JSON.stringify(record,null,2));
if(Object.keys(record.errors).length)process.exitCode=1;
