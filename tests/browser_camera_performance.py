"""Differential camera benchmark in real Chromium; same canonical SVG, two camera versions.

Baseline is exactly the pre-optimization canvas module from the pinned main
commit; no DOM virtualization or network semantic changes are introduced.
Tests real zoom() and pointermove pan handlers with 40 events per trial.
"""
from __future__ import annotations
import json
import statistics
import tempfile
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
    assert BASELINE.is_file(),"Exact pinned main baseline is required"
    OUT.mkdir(parents=True,exist_ok=True)
    HTML.write_text('<!doctype html><meta charset="utf-8"><svg id="topology" '
        'style="display:block;width:1180px;height:720px"></svg>',encoding="utf-8")
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    outcome={"browser":"real Chromium", "method":"same SVG, 40 synchronous zoom/pan events x 3 repeats",
      "cases":[],"errors":[],"limitations":[
        "Synchronous JS event cost is not total browser paint time or FPS.",
        "JavaScript heap is not total native SVG/browser process memory."]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--enable-precise-memory-info","--js-flags=--expose-gc"])
            page=browser.new_page(viewport={"width":1380,"height":900})
            page.set_default_timeout(120000)
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/_camera_perf_fixture.html")
            for n,edge_count in [(500,750),(2000,5000)]:
                record=page.evaluate("""async ([nodeCount,linkCount])=>{
                  const {TopologyCanvas:Baseline}=await import('/canvas-baseline.mjs');
                  const {TopologyCanvas:Candidate}=await import('/canvas.js');
                  const svg=document.getElementById('topology');
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
                  const source={schemaVersion:'1.0',name:'camera fixture',zones:[],nodes,links};
                  const before=JSON.stringify(source);
                  const samples={baseline:{zoom:[],pan:[],heap:[]},
                    candidate:{zoom:[],pan:[],heap:[]}};
                  const signatures={};
                  let geometryMismatch=0, pointerAnchorError=0, rectReadCounts={};
                  const almost=(a,b)=>Math.abs(a-b)<1e-5;
                  const digest=async text=>{
                    const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
                    return Array.from(new Uint8Array(hash)).map(b=>b.toString(16).padStart(2,'0')).join('');
                  };
                  const ops=(Class,name)=>{
                    let scaleEvents=0;
                    const canvas=new Class(svg,{
                      onSelect:()=>{},onPort:()=>{},onMove:()=>{},onEndMove:()=>{},
                      onScale:()=>{scaleEvents++;}
                    });
                    canvas.setData(source,null,null,[]);
                    const geometry=svg.innerHTML;
                    canvas.fit();
                    const initialView={...canvas.view};
                    let boundingReads=0;
                    const realGetRect=svg.getBoundingClientRect.bind(svg);
                    svg.getBoundingClientRect=()=>{
                      boundingReads++;
                      return realGetRect();
                    };
                    // Measure programmatic zoom over a large, fully populated real SVG.
                    const rect=svg.getBoundingClientRect();
                    const px=rect.left+rect.width*0.31, py=rect.top+rect.height*0.27;
                    const initialAnchor=canvas.toWorld(px,py);
                    const t0=performance.now();
                    for(let i=0;i<40;i++)
                      canvas.zoom(i%2===0?1.12:1/1.12,px,py);
                    const zoomMs=performance.now()-t0;
                    const zoomReads=boundingReads;
                    const lastAnchor=canvas.toWorld(px,py);
                    if(!almost(lastAnchor.x,initialAnchor.x)||
                       !almost(lastAnchor.y,initialAnchor.y)||
                       !almost(canvas.view.w,initialView.w)||
                       !almost(canvas.view.h,initialView.h))throw Error('Camera pointer anchor/round-trip changed');
                    canvas.fit();
                    boundingReads=0;
                    const panStart={...canvas.view};
                    canvas.interaction={kind:'pan',pointerId:7,
                      x:px,y:py,start:panStart};
                    const t1=performance.now();
                    for(let i=0;i<40;i++)
                      svg.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,
                        pointerId:7,clientX:px+2*(i+1),clientY:py+(i+1)}));
                    const panMs=performance.now()-t1;
                    const panReads=boundingReads;
                    const finalPan={...canvas.view};
                    canvas.interaction=null;
                    svg.getBoundingClientRect=realGetRect;
                    if(!Number.isFinite(finalPan.x)||!Number.isFinite(finalPan.y))throw Error('Bad pan');
                    if(typeof window.gc==='function'){window.gc();window.gc();}
                    const heap=performance.memory?.usedJSHeapSize??null;
                    return {zoomMs,panMs,zoomReads,panReads,heap,geometry,
                      finalPan,initialView,scaleEvents};
                  };
                  const result={nodeCount,linkCount,sourceUnchanged:null,
                    hashes:{},viewDeltas:[],scaleCounts:{},rectReads:{}};
                  for(let rep=0;rep<3;rep++){
                    // Alternate test order to reduce JIT/cache ordering effects.
                    const order=rep%2===0?[['baseline',Baseline],['candidate',Candidate]]:
                      [['candidate',Candidate],['baseline',Baseline]];
                    for(const [name,Class] of order){
                      const datum=ops(Class,name);
                      samples[name].zoom.push(+datum.zoomMs.toFixed(3));
                      samples[name].pan.push(+datum.panMs.toFixed(3));
                      samples[name].heap.push(datum.heap);
                      rectReadCounts[name]={zoom:datum.zoomReads,pan:datum.panReads};
                      signatures[name]=datum;
                      result.hashes[name]=await digest(datum.geometry);
                      result.scaleCounts[name]=datum.scaleEvents;
                    }
                    const a=signatures.baseline,b=signatures.candidate;
                    if(result.hashes.baseline!==result.hashes.candidate)throw Error('Different SVG geometry');
                    for(const field of ['x','y','w','h']){
                      if(!almost(a.finalPan[field],b.finalPan[field]))
                        throw Error('Different pointer pan geometry for '+field);
                      if(!almost(a.initialView[field],b.initialView[field]))
                        throw Error('Different fitted viewport geometry for '+field);
                    }
                    result.viewDeltas.push(a.finalPan.x-b.finalPan.x);
                  }
                  const median = a => [...a].sort((a,b)=>a-b)[1];
                  for(const name of ['baseline','candidate']){
                    result[name]={zoomMs:samples[name].zoom,
                      panMs:samples[name].pan,
                      zoomMedian:median(samples[name].zoom),
                      panMedian:median(samples[name].pan),
                      heapAfterGc:samples[name].heap,
                      getBoundingClientRectCalls:rectReadCounts[name],
                      scaleEvents:result.scaleCounts[name]};
                  }
                  result.zoomSpeedup=+(result.baseline.zoomMedian/result.candidate.zoomMedian).toFixed(2);
                  result.panSpeedup=+(result.baseline.panMedian/result.candidate.panMedian).toFixed(2);
                  result.sourceUnchanged=JSON.stringify(source)===before;
                  return result;
                }""",[n,edge_count])
                assert record["sourceUnchanged"],"Canonical project was mutated"
                assert record["hashes"]["baseline"]==record["hashes"]["candidate"],"SVG markup differs"
                assert all(abs(v)<1e-5 for v in record["viewDeltas"]),"Pan geometry differs"
                for mode in ("zoom","pan"):
                    assert record["candidate"]["getBoundingClientRectCalls"][mode] <= (
                        record["baseline"]["getBoundingClientRectCalls"][mode]//2+2),(
                        "Extra geometry reads remained",mode,record)
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
        t.join(timeout=5)
        HTML.unlink(missing_ok=True)
        BASELINE.unlink(missing_ok=True)
        (OUT/"camera.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    large=outcome["cases"][-1]
    assert large["zoomSpeedup"]>=1.3,("Large zoom improvement below 1.3x",large["zoomSpeedup"])
    assert large["panSpeedup"]>=1.3,("Large pan improvement below 1.3x",large["panSpeedup"])
    print("CAMERA_BENCHMARK_PASS",json.dumps({
      "zoomSpeedup":large["zoomSpeedup"],
      "panSpeedup":large["panSpeedup"],"identicalGeometry":True},ensure_ascii=False),flush=True)

if __name__=="__main__":
    run()
