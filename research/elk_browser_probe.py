"""Browser probes for local ELK assets and YadiLab's unchanged SVG TopologyCanvas."""
import json, subprocess, time, socket, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/"research/elk-results"
OUT.mkdir(parents=True,exist_ok=True)
HTML=BASE/"research/_elk_browser_probe.html"
HTML.write_text("""<!doctype html><meta charset="utf-8">
<style>body{margin:0;}svg{display:block;width:1200px;height:800px}</style>
<svg id="topology" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"></svg>
<script src="/node_modules/elkjs/lib/elk-api.js"></script>
""",encoding="utf-8")
server=subprocess.Popen([sys.executable,"-m","http.server","8765","--bind","127.0.0.1","--directory",str(BASE)],
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
result={"environment":{"browser":"chromium","http_origin":"127.0.0.1","external_requests":[]},"tests":{},"errors":{}}
try:
    for attempt in range(40):
        try:
            with socket.create_connection(("127.0.0.1",8765),timeout=0.3):break
        except OSError:time.sleep(.1)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1400,"height":900})
        page.on("request",lambda request: result["environment"]["external_requests"].append(request.url)
          if not request.url.startswith("http://127.0.0.1:8765/") else None)
        page.goto("http://127.0.0.1:8765/research/_elk_browser_probe.html",wait_until="load")
        # H4: ELK worker from the same local origin, with no external runtime assets.
        try:
            ans=page.evaluate("""async ()=>{
              if(typeof window.ELK!=='function')throw Error('ELK API asset not loaded');
              const elk=new ELK({workerUrl:'/node_modules/elkjs/lib/elk-worker.js'});
              const graph={id:'g',layoutOptions:{'elk.algorithm':'layered'},children:[
                {id:'A',width:202,height:96},{id:'B',width:202,height:96}],
                edges:[{id:'e',sources:['A'],targets:['B']}]};
              const t=performance.now();
              const out=await Promise.race([elk.layout(graph),new Promise((_,reject)=>setTimeout(()=>reject(Error('worker_timeout_12000ms')),12000))]);
              const ms=performance.now()-t;
              const result={workerApi:true,placedNodes:out.children.length,routedEdges:out.edges.length,ms};
              elk.terminateWorker();
              return result;
            }""")
            time.sleep(.1)
            workers=[w.url for w in page.workers]
            ans["observedWorkerUrls"]=workers
            ans["sameOriginWorkerObserved"]=any(u.startswith("http://127.0.0.1:8765/") and "elk-worker" in u for u in workers)
            result["tests"]["H4_offline_local_worker"]=ans
        except Exception as exc:result["errors"]["H4_offline_local_worker"]=str(exc)

        # H5: visual animation frame opportunities while a worker layout is running.
        try:
            result["tests"]["H5_worker_raf"]=page.evaluate("""async ()=>{
              const elk=new ELK({workerUrl:'/node_modules/elkjs/lib/elk-worker.js'});
              const children=Array.from({length:500},(_,i)=>({id:'N'+i,width:202,height:96}));
              const edges=Array.from({length:850},(_,i)=>({
                id:'E'+i,sources:['N'+(i%499)],targets:['N'+((i+1+Math.floor(i/499))%500)]}));
              let done=false,frames=0; const start=performance.now();
              const work=elk.layout({id:'g',layoutOptions:{'elk.algorithm':'layered'},children,edges})
                .then(()=>{done=true;}).catch(e=>{done=true;throw e;});
              const monitor=new Promise(resolve=>{
                function tick(){if(done){resolve();return;}frames++;requestAnimationFrame(tick);}
                requestAnimationFrame(tick);
              });
              await Promise.race([Promise.all([work,monitor]),new Promise((_,reject)=>
                setTimeout(()=>reject(Error('H5 timeout 25000ms')),25000))]);
              const output={framesDuringPendingLayout:frames,durationMs:performance.now()-start};
              elk.terminateWorker();return output;
            }""")
        except Exception as exc:result["errors"]["H5_worker_raf"]=str(exc)

        # H10: use YadiLab's original canvas.js (not a replacement renderer).
        for n, links in [(47,46),(500,750),(2000,5000)]:
            key="H10_actual_svg_render_"+str(n)
            try:
                rendered=page.evaluate("""async ([n,target])=>{
                  const {TopologyCanvas}=await import('/web/canvas.js');
                  let canvas=window.__yadiCanvas;
                  if(!canvas)canvas=window.__yadiCanvas=new TopologyCanvas(document.querySelector('#topology'),{
                    onSelect:()=>{},onPort:()=>{},onMove:()=>{},onEndMove:()=>{},onScale:()=>{}});
                  const nodes=Array.from({length:n},(_,i)=>({
                    id:'N'+i,label:'Node '+i,kind:'switch',
                    x:110+260*(i%Math.ceil(Math.sqrt(n))),y:110+220*Math.floor(i/Math.ceil(Math.sqrt(n))),
                    zoneId:null,ports:[]}));
                  const links=[];const seen=new Set();
                  let step=1;
                  while(links.length<target && step<n){
                    for(let i=0;i<n && links.length<target;i++){
                      const j=(i+step)%n;if(i===j)continue;
                      const key=[Math.min(i,j),Math.max(i,j)].join('-');
                      if(seen.has(key))continue;
                      seen.add(key);
                      const a=nodes[i],b=nodes[j],ap='p'+a.ports.length,bp='p'+b.ports.length;
                      a.ports.push({id:ap,name:ap,enabled:true,ipv4:null});
                      b.ports.push({id:bp,name:bp,enabled:true,ipv4:null});
                      links.push({id:'L'+links.length,a:{node:a.id,port:ap},b:{node:b.id,port:bp},enabled:true});
                    }step++;
                  }
                  const p={name:'synthetic',schemaVersion:'1.0',zones:[],nodes,links};
                  const t0=performance.now();canvas.setData(p,null,null,[]);
                  const jsMs=performance.now()-t0;
                  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                  const endMs=performance.now()-t0;
                  return {nodes:n,links:links.length,jsSvgRebuildMs:jsMs,throughNextPaintMs:endMs,
                    pathCount:document.querySelectorAll('path.network-edge').length,
                    portCircleCount:document.querySelectorAll('circle.port-dot').length};
                }""",[n,links],timeout=60000)
                result["tests"][key]=rendered
            except Exception as exc:result["errors"][key]=str(exc)
        browser.close()
finally:
    server.terminate()
    try:server.wait(timeout=5)
    except subprocess.TimeoutExpired:server.kill()
    HTML.unlink(missing_ok=True)
(OUT/"browser.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
if result["errors"]:sys.exit(1)
