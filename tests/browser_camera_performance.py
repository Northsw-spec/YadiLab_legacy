"""Real Chromium camera study: event bursts, paint commits and frame-spaced input.

The baseline is pinned git-show main canvas in canvas-baseline.mjs.
This tests identical topology, SVG markup and final world geometry for the
synchronous old handler and the animation-frame-coalesced candidate. Burst
cost is NOT equivalent to FPS or to 40 physically separate wheel gestures.
"""
from __future__ import annotations
import json
import threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/"web"
HTML=WEB/"_camera_perf_fixture.html"
BASELINE=WEB/"canvas-baseline.mjs"
OUT=ROOT/"research"/"camera-perf-results"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(WEB),**kwargs)
    def log_message(self,*args):
        pass

def run():
    assert BASELINE.is_file(),"Exact pinned baseline missing"
    OUT.mkdir(parents=True,exist_ok=True)
    HTML.write_text('<!doctype html><meta charset="utf-8"><body></body>',encoding="utf-8")
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    outcome={"browser":"real Chromium","methods":["40 wheel events in one JS task",
      "40 pan pointermove events in one JS task",
      "8 wheel events spaced across animation frames"],
      "cases":[],"errors":[],"limitations":[
      "Burst-handler speedups quantify event coalescing, not the achieved frame rate.",
      "Frame-spaced times include scheduler and browser paint overhead; not guaranteed user FPS.",
      "JS heap excludes native SVG and browser GPU allocations."]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--enable-precise-memory-info","--js-flags=--expose-gc"])
            page=browser.new_page(viewport={"width":1380,"height":900})
            page.set_default_timeout(120000)
            errors=[]
            page.on("pageerror",lambda exc:errors.append(str(exc)))
            page.goto(f"http://127.0.0.1:{server.server_address[1]}/_camera_perf_fixture.html")
            for n,link_count in [(500,750),(2000,5000)]:
                record=page.evaluate("""async ([nodeCount,linkCount])=>{
                  const {TopologyCanvas:Old}=await import('/canvas-baseline.mjs');
                  const {TopologyCanvas:New}=await import('/canvas.js');
                  const NS='http://www.w3.org/2000/svg';
                  const nodes=Array.from({length:nodeCount},(_,i)=>({
                    id:'N'+String(i).padStart(5,'0'),kind:['switch','router','host'][i%3],
                    label:'Node '+i,zoneId:null,x:100+260*(i%70),
                    y:100+220*Math.floor(i/70),ports:[]}));
                  const links=[];
                  for(let i=0;i<linkCount;i++){
                    const a=nodes[i%nodeCount],next=(i*7+31)%nodeCount;
                    const b=nodes[next===i%nodeCount?(next+1)%nodeCount:next];
                    const aid='p'+a.ports.length,bid='p'+b.ports.length;
                    a.ports.push({id:aid,name:aid,enabled:true,ipv4:null});
                    b.ports.push({id:bid,name:bid,enabled:true,ipv4:null});
                    links.push({id:'L'+i,a:{node:a.id,port:aid},
                      b:{node:b.id,port:bid},enabled:true});
                  }
                  const source={schemaVersion:'1.0',name:'synthetic',zones:[],nodes,links};
                  const sourceText=JSON.stringify(source);
                  const hash=async text=>{
                    const bytes=new TextEncoder().encode(text);
                    const d=await crypto.subtle.digest('SHA-256',bytes);
                    return Array.from(new Uint8Array(d)).map(x=>x.toString(16).padStart(2,'0')).join('');
                  };
                  const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
                  const settle=async()=>{await frame();await frame();};
                  const close=(a,b)=>Math.abs(a-b)<1e-5;
                  const measure=async (Class,name)=>{
                    // Each instance owns an independent SVG to avoid duplicate
                    // event handlers from prior candidates/rounds.
                    const svg=document.createElementNS(NS,'svg');
                    svg.style.cssText='display:block;width:1180px;height:720px';
                    document.body.replaceChildren(svg);
                    let lastScale=null,scaleCount=0,rectReads=0,viewWrites=0;
                    const canvas=new Class(svg,{onSelect:()=>{},onPort:()=>{},
                      onMove:()=>{},onEndMove:()=>{},onScale:x=>{lastScale=x;scaleCount++;}});
                    canvas.setData(source,null,null,[]);
                    const svgHash=await hash(svg.innerHTML);
                    const svgChildren=svg.querySelectorAll('*').length;
                    canvas.fit();
                    const start={...canvas.view};
                    const r=svg.getBoundingClientRect();
                    const px=r.left+r.width*.31,py=r.top+r.height*.27;
                    const anchor=canvas.toWorld(px,py);
                    const oldRect=svg.getBoundingClientRect.bind(svg);
                    const oldSet=svg.setAttribute.bind(svg);
                    svg.getBoundingClientRect=()=>{rectReads++;return oldRect();};
                    svg.setAttribute=(key,value)=>{
                      if(key==='viewBox')viewWrites++;
                      return oldSet(key,value);
                    };
                    const wheel=delta=>svg.dispatchEvent(new WheelEvent('wheel',{
                      bubbles:true,cancelable:true,deltaY:delta,clientX:px,clientY:py}));
                    const t0=performance.now();
                    for(let i=0;i<40;i++)wheel(i%2===0?-120:120);
                    const wheelSyncMs=performance.now()-t0;
                    const wheelWritesBeforeFrame=viewWrites;
                    await settle();
                    const wheelWrites=viewWrites;
                    const wheelReads=rectReads;
                    const zoom={...canvas.view};
                    const finalAnchor=canvas.toWorld(px,py);
                    const zoomViewBox=svg.getAttribute('viewBox');
                    if(!close(zoom.w,start.w)||!close(zoom.h,start.h)||
                      !close(anchor.x,finalAnchor.x)||!close(anchor.y,finalAnchor.y))
                      throw Error(name+' wheel world coordinates did not round-trip');
                    const zoomScale=lastScale;
                    canvas.fit();
                    viewWrites=0;rectReads=0;
                    const panStart={...canvas.view};
                    canvas.interaction={kind:'pan',pointerId:7,
                      x:px,y:py,start:panStart};
                    const t1=performance.now();
                    for(let i=0;i<40;i++)
                      svg.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,
                        pointerId:7,clientX:px+(i+1)*2,clientY:py+(i+1)}));
                    const panSyncMs=performance.now()-t1;
                    const panWritesBeforeFrame=viewWrites;
                    await settle();
                    const panWrites=viewWrites,panReads=rectReads;
                    const pan={...canvas.view},panViewBox=svg.getAttribute('viewBox');
                    canvas.interaction=null;
                    const panScale=lastScale;

                    // A separate workload with one event per animation frame
                    // reveals if this approach improves actual frame throughput.
                    canvas.fit();
                    viewWrites=0;
                    const t2=performance.now();
                    for(let i=0;i<8;i++){
                      wheel(i%2===0?-120:120);
                      await frame();
                    }
                    await settle();
                    const spacedWheelMs=performance.now()-t2;
                    const spacedWrites=viewWrites;
                    const spacedViewBox=svg.getAttribute('viewBox');
                    const spacedFinal={...canvas.view};
                    if(!close(spacedFinal.w,start.w)||!close(spacedFinal.h,start.h))
                      throw Error(name+' frame-spaced wheel geometry changed');
                    if(typeof window.gc==='function'){window.gc();window.gc();}
                    const heap=performance.memory?.usedJSHeapSize??null;
                    svg.getBoundingClientRect=oldRect;
                    svg.setAttribute=oldSet;
                    svg.remove();
                    return {name,svgHash,svgChildren,sourceUnchanged:JSON.stringify(source)===sourceText,
                      wheel:{syncMs:wheelSyncMs,writesBeforeFrame:wheelWritesBeforeFrame,
                        writes:wheelWrites,reads:wheelReads,world:zoom,
                        viewBox:zoomViewBox,lastScale:zoomScale},
                      pan:{syncMs:panSyncMs,writesBeforeFrame:panWritesBeforeFrame,
                        writes:panWrites,reads:panReads,world:pan,
                        viewBox:panViewBox,lastScale:panScale},
                      frameSpaced:{durationMs:spacedWheelMs,writes:spacedWrites,
                        viewBox:spacedViewBox,world:spacedFinal},
                      heapAfterGc:heap,scaleCallbacks:scaleCount};
                  };
                  const samples={old:[],optimized:[]};
                  for(let rep=0;rep<3;rep++){
                    const ordered=rep%2?[['optimized',New],['old',Old]]:
                      [['old',Old],['optimized',New]];
                    for(const [name,Class] of ordered)samples[name].push(await measure(Class,name));
                  }
                  const median=list=>[...list].sort((a,b)=>a-b)[1];
                  const a=samples.old,b=samples.optimized;
                  const identical=(field)=>{
                    for(let i=0;i<3;i++){
                      const x=a[i],y=b[i];
                      if(x.svgHash!==y.svgHash||x.svgChildren!==y.svgChildren||
                        !x.sourceUnchanged||!y.sourceUnchanged)
                        throw Error('SVG identity/immutability changed');
                      if(x[field].viewBox!==y[field].viewBox)
                        throw Error(field+' viewBox did not match baseline');
                      if(x[field].lastScale!==y[field].lastScale)
                        throw Error(field+' reported scale does not match');
                    }
                  };
                  identical('wheel');identical('pan');
                  for(let i=0;i<3;i++){
                    if(a[i].frameSpaced.viewBox!==b[i].frameSpaced.viewBox)
                      throw Error('Spaced wheel result differs');
                  }
                  const stats = name=>({
                    wheelSyncMs:samples[name].map(x=>+x.wheel.syncMs.toFixed(3)),
                    panSyncMs:samples[name].map(x=>+x.pan.syncMs.toFixed(3)),
                    spacedMs:samples[name].map(x=>+x.frameSpaced.durationMs.toFixed(3)),
                    wheelViewBoxWrites:samples[name][2].wheel.writes,
                    panViewBoxWrites:samples[name][2].pan.writes,
                    spacedViewBoxWrites:samples[name][2].frameSpaced.writes,
                    heapAfterGc:samples[name].map(x=>x.heapAfterGc),
                    wheelMedianMs:median(samples[name].map(x=>x.wheel.syncMs)),
                    panMedianMs:median(samples[name].map(x=>x.pan.syncMs)),
                    spacedMedianMs:median(samples[name].map(x=>x.frameSpaced.durationMs)),
                    svgHash:samples[name][2].svgHash,
                    svgChildren:samples[name][2].svgChildren});
                  const old=stats('old'),optimized=stats('optimized');
                  return {nodeCount,linkCount,old,optimized,identicalGeometry:true,
                    wheelBurstSpeedup:+(old.wheelMedianMs/optimized.wheelMedianMs).toFixed(2),
                    panBurstSpeedup:+(old.panMedianMs/optimized.panMedianMs).toFixed(2),
                    frameSpacedSpeedup:+(old.spacedMedianMs/optimized.spacedMedianMs).toFixed(2)};
                }""",[n,link_count])
                assert record["identicalGeometry"],record
                assert record["old"]["svgHash"]==record["optimized"]["svgHash"]
                assert record["optimized"]["wheelViewBoxWrites"]<=2,record
                assert record["optimized"]["panViewBoxWrites"]<=2,record
                assert record["old"]["wheelViewBoxWrites"]>=40,record
                assert record["old"]["panViewBoxWrites"]>=40,record
                outcome["cases"].append(record)
                print("CAMERA_BENCHMARK",json.dumps(record,ensure_ascii=False),flush=True)
            assert not errors,errors
            browser.close()
    except Exception as exc:
        outcome["errors"].append(str(exc))
        raise
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        HTML.unlink(missing_ok=True)
        BASELINE.unlink(missing_ok=True)
        (OUT/"camera.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    large=outcome["cases"][-1]
    assert large["wheelBurstSpeedup"]>=2.0,("Wheel burst gain below 2x",large)
    assert large["panBurstSpeedup"]>=2.0,("Pan burst gain below 2x",large)
    assert large["optimized"]["spacedMedianMs"]<=1.35*large["old"]["spacedMedianMs"],(
        "Frame-spaced gesture regression",large)
    print("CAMERA_BENCHMARK_PASS",json.dumps({
      "wheelBurstSpeedup":large["wheelBurstSpeedup"],
      "panBurstSpeedup":large["panBurstSpeedup"],
      "frameSpacedSpeedup":large["frameSpacedSpeedup"],
      "note":"Burst throughput is not physical frame rate."},ensure_ascii=False),flush=True)

if __name__=="__main__":
    run()
