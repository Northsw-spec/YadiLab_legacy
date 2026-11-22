"""Real Chromium proof: ELK fixed zero-size ports + routed SVG paths + packet animation.
This is an isolated research-only DOM adapter; production canvas.js is unchanged.
"""
import json, time, threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
results=root/"research/elk-results"
results.mkdir(parents=True,exist_ok=True)
fixture=root/"research/_elk_fixed_port_fixture.html"
fixture.write_text('''<!doctype html><meta charset="utf-8">
<style>body{margin:0} svg{display:block;width:1500px;height:950px}</style>
<svg id="topology" xmlns="http://www.w3.org/2000/svg"></svg>
<script src="/node_modules/elkjs/lib/elk-api.js"></script>''',encoding="utf-8")
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(root),**kwargs)
    def log_message(self,*args):
        return
server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
base=f"http://127.0.0.1:{server.server_address[1]}"
evidence={"cases":{},"externalRequests":[],"workerUrls":[],"errors":{}}
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1550,"height":1050})
        page.set_default_timeout(45000)
        page.on("worker",lambda w:evidence["workerUrls"].append(w.url))
        page.on("request",lambda r:evidence["externalRequests"].append(r.url)
                if not r.url.startswith(base+"/") else None)
        page.goto(base+"/research/_elk_fixed_port_fixture.html")
        for kind in ("tree","ring"):
            try:
                output=page.evaluate("""async (kind)=>{
                  const svg=document.getElementById('topology');
                  const {TopologyCanvas}=await import('/web/canvas.js');
                  if(!window.__researchCanvas)window.__researchCanvas=new TopologyCanvas(svg,{
                    onSelect:()=>{},onPort:()=>{},onMove:()=>{},onEndMove:()=>{},onScale:()=>{}});
                  const canvas=window.__researchCanvas;
                  const W=202,HEAD=66,ROW=23;
                  const height=n=>Math.max(96,78+n.ports.length*23);
                  const nodes=Array.from({length:47},(_,i)=>({id:'N'+i,label:'Node '+i,
                    kind:'switch',zoneId:null,ports:[],x:0,y:0}));
                  const links=[];
                  for(let i=1;i<47;i++){
                    const a=nodes[kind==='ring'?i-1:Math.floor((i-1)/2)],b=nodes[i];
                    const ap='p'+a.ports.length,bp='p'+b.ports.length;
                    a.ports.push({id:ap,name:ap,ipv4:null,enabled:true});
                    b.ports.push({id:bp,name:bp,ipv4:null,enabled:true});
                    links.push({id:'L'+links.length,a:{node:a.id,port:ap},b:{node:b.id,port:bp},enabled:true});
                  }
                  if(kind==='ring'){
                    const a=nodes[46],b=nodes[0],ap='p'+a.ports.length,bp='p'+b.ports.length;
                    a.ports.push({id:ap,name:ap,ipv4:null,enabled:true});
                    b.ports.push({id:bp,name:bp,ipv4:null,enabled:true});
                    links.push({id:'L'+links.length,a:{node:a.id,port:ap},b:{node:b.id,port:bp},enabled:true});
                  }
                  const p={schemaVersion:'1.0',name:'synthetic '+kind, zones:[],nodes,links};
                  const old=JSON.stringify(p);
                  const ordered=[...nodes].sort((a,b)=>a.id.localeCompare(b.id));
                  const nid=new Map(ordered.map((n,i)=>[n.id,'n'+i]));
                  const opts={'elk.algorithm':'layered','elk.direction':'RIGHT',
                    'elk.edgeRouting':'ORTHOGONAL','elk.spacing.nodeNode':'55',
                    'elk.layered.spacing.nodeNodeBetweenLayers':'90'};
                  const elk=new ELK({workerUrl:'/node_modules/elkjs/lib/elk-worker.js'});
                  const initial=await elk.layout({id:'g',layoutOptions:opts,
                    children:ordered.map(n=>({id:nid.get(n.id),width:W,height:height(n)})),
                    edges:links.map((l,i)=>({id:'e'+i,sources:[nid.get(l.a.node)],targets:[nid.get(l.b.node)]}))});
                  const initialX=new Map(initial.children.map(n=>[n.id,n.x]));
                  const side=new Map();
                  for(const l of links){
                    for(const [ep,other] of [[l.a,l.b],[l.b,l.a]])
                      side.set(ep.node+'|'+ep.port,
                        initialX.get(nid.get(other.node))<initialX.get(nid.get(ep.node))?'left':'right');
                  }
                  const portID=new Map();
                  const elkNodes=ordered.map((n,i)=>({id:nid.get(n.id),width:W,height:height(n),
                    layoutOptions:{'elk.portConstraints':'FIXED_POS'},
                    ports:n.ports.map((port,j)=>{
                      const k=n.id+'|'+port.id,id='p'+i+'_'+j;
                      portID.set(k,id);
                      return {id,x:side.get(k)==='left'?0:W,y:HEAD+j*ROW+5,
                        width:0,height:0,layoutOptions:{'elk.port.side':
                        side.get(k)==='left'?'WEST':'EAST'}};
                    })}));
                  const out=await elk.layout({id:'g',layoutOptions:opts,children:elkNodes,
                    edges:links.map((l,i)=>({id:'e'+i,
                      sources:[portID.get(l.a.node+'|'+l.a.port)],
                      targets:[portID.get(l.b.node+'|'+l.b.port)]}))});
                  elk.terminateWorker();
                  const outN=new Map(out.children.map(n=>[n.id,n]));
                  const placed={...p,nodes:p.nodes.map(n=>({...n,x:Math.round(outN.get(nid.get(n.id)).x),
                    y:Math.round(outN.get(nid.get(n.id)).y)}))};
                  canvas.setData(placed,null,null,[]);
                  canvas.fit();
                  const dot=(ep)=>{
                    const el=svg.querySelector('[data-port-node="'+ep.node+'"][data-port-id="'+ep.port+'"]');
                    if(!el)throw Error('Missing port dot');
                    const mat=el.closest('g.network-node').getAttribute('transform').match(/translate\(([\d.-]+) ([\d.-]+)\)/);
                    if(!mat)throw Error('Invalid node transform');
                    return {x:Number(mat[1])+Number(el.getAttribute('cx')),
                      y:Number(mat[2])+Number(el.getAttribute('cy'))};
                  };
                  const byPort=new Map();
                  for(const n of out.children)for(const ep of n.ports)
                    byPort.set(ep.id,{x:n.x+ep.x,y:n.y+ep.y});
                  let dotErrors=0,maxDotError=0,endErrors=0,maxEndError=0,invalidRoutes=0;
                  for(const l of links){
                    for(const ep of [l.a,l.b]){
                      const a=dot(ep),b=byPort.get(portID.get(ep.node+'|'+ep.port));
                      const d=Math.hypot(a.x-b.x,a.y-b.y);
                      maxDotError=Math.max(maxDotError,d);if(d>0.51)dotErrors++;
                    }
                  }
                  for(const [i,e] of out.edges.entries()){
                    const link=links[i],sec=e.sections?.[0];
                    if(!sec)throw Error('Missing ELK path');
                    const pts=[sec.startPoint,...(sec.bendPoints||[]),sec.endPoint];
                    const d='M '+pts[0].x+' '+pts[0].y+pts.slice(1).map(p=>' L '+p.x+' '+p.y).join('');
                    const path=svg.querySelector('path.network-edge[data-link-id="'+link.id+'"]');
                    const hit=svg.querySelector('path.edge-hit[data-link-hit="'+link.id+'"]');
                    if(!path||!hit)throw Error('Missing original topology editor SVG path');
                    path.setAttribute('d',d); hit.setAttribute('d',d);
                    const from=path.getPointAtLength(0),to=path.getPointAtLength(path.getTotalLength());
                    for(const [a,b] of [[from,dot(link.a)],[to,dot(link.b)]]){
                      const diff=Math.hypot(a.x-b.x,a.y-b.y);
                      maxEndError=Math.max(maxEndError,diff);if(diff>0.51)endErrors++;
                    }
                    if(!(path.getTotalLength()>0))invalidRoutes++;
                  }
                  if(JSON.stringify(p)!==old)throw Error('Original project mutated');
                  if(!links.length||svg.querySelectorAll('path.network-edge').length!==links.length)
                    throw Error('Missing rendered edges');
                  // The existing animation must still consume the very same network-edge path.
                  const first=links[0];
                  let playbackProgress=false;
                  canvas.playJourney([{linkId:first.id,from:first.a,to:first.b,stage:'test',reverse:false}],{
                    onFrame:()=>{playbackProgress=true}});
                  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
                  const markerVisible=Boolean(svg.querySelector('circle.packet-marker'));
                  canvas.stopJourney({quiet:true});
                  return {kind,nodes:placed.nodes.length,links:placed.links.length,
                    routesReplacedWithActualElkSections:out.edges.length,
                    dotErrors,maxDotError,endErrors,maxEndError,invalidRoutes,
                    actualSvgPaths:svg.querySelectorAll('path.network-edge').length,
                    markerVisible,playbackProgress,originalProjectUnchanged:true,
                    source:'isolated DOM adapter; production source not modified'};
                }""",kind)
                evidence["cases"][kind]=output
                page.locator("#topology").screenshot(path=str(results/f"fixed_port_{kind}.png"))
                print("PORT_BROWSER",kind,json.dumps(output))
            except Exception as exc:
                evidence["errors"][kind]=str(exc)
                print("PORT_BROWSER_FAIL",kind,str(exc))
        browser.close()
finally:
    server.shutdown()
    server.server_close()
    fixture.unlink(missing_ok=True)
(results/"ports_browser.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
assert not evidence["externalRequests"],"Unexpected external dependency"
assert not evidence["errors"],"Chromium JS failure"
assert len(evidence["cases"])==2
for case in evidence["cases"].values():
    assert case["dotErrors"]==0 and case["endErrors"]==0,case
    assert case["markerVisible"] and case["playbackProgress"],case
    assert case["invalidRoutes"]==0
print("PORT_BROWSER_VERDICT PASS")
