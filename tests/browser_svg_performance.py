"""Differential Chromium microbenchmark: original versus indexed SVG canvas.

Run only as a dedicated research/CI probe. The baseline is the exact
git-show copy at web/canvas-baseline.mjs (never committed to product).
Both variants render identical deterministic projects. Tests DOM geometry,
declared endpoints, click events, viewport interaction, runtime, and
approximate JS heap use. Timing measurements are environment-specific.
"""
from __future__ import annotations
import json
import statistics
import sys
import tempfile
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/"web"
FIXTURE=WEB/"_canvas_perf_fixture.html"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):
        super().__init__(*a,directory=str(WEB),**kw)
    def log_message(self,*a):
        return

def run():
    assert (WEB/"canvas-baseline.mjs").is_file(), "Missing exact old-canvas baseline. Use git show to prepare it."
    FIXTURE.write_text("""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
      <svg id="performance-svg" xmlns="http://www.w3.org/2000/svg"
        style="width:1200px;height:750px;display:block" viewBox="0 0 1200 750"></svg>
      </body></html>""",encoding="utf-8")
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    summary={"cases":[],"checks":[],"browser":"Chromium","method":"performance.now synchronous setData; 3 repeats; DOM SHA-256","errors":[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--enable-precise-memory-info","--js-flags=--expose-gc"])
            page=browser.new_page(viewport={"width":1380,"height":900})
            page.set_default_timeout(120000)
            page.goto(f"http://127.0.0.1:{server.server_port}/_canvas_perf_fixture.html")
            page_errors=[]
            page.on("pageerror",lambda error:page_errors.append(str(error)))
            for n,e,z in ((50,90,3),(500,750,10),(2000,5000,15)):
                data=page.evaluate("""async ([nodeCount,edgeCount,zoneCount])=>{
                  const {TopologyCanvas:Baseline}=await import('/canvas-baseline.mjs');
                  const {TopologyCanvas:Optimized}=await import('/canvas.js');
                  const root=document.getElementById('performance-svg');
                  const nodes=Array.from({length:nodeCount},(_,i)=>({
                    id:'N'+String(i).padStart(5,'0'),
                    kind:['switch','router','host','firewall'][i%4],
                    label:'Node '+i, x:110+260*(i%70),
                    y:110+220*Math.floor(i/70), zoneId:'Z'+(i%zoneCount),ports:[]}));
                  const links=[];
                  for(let i=0;i<edgeCount;i++){
                    const a=nodes[i%nodeCount],bi=(i*7+31)%nodeCount;
                    const b=nodes[bi===i%nodeCount?(bi+1)%nodeCount:bi];
                    const ap='p'+a.ports.length,bp='p'+b.ports.length;
                    a.ports.push({id:ap,name:ap,enabled:true,ipv4:null});
                    b.ports.push({id:bp,name:bp,enabled:true,ipv4:null});
                    links.push({id:'L'+i,a:{node:a.id,port:ap},b:{node:b.id,port:bp},enabled:true});
                  }
                  const zones=Array.from({length:zoneCount},(_,i)=>({id:'Z'+i,label:'Zone '+i}));
                  const original={schemaVersion:'1.0',name:'Performance fixture',zones,nodes,links};
                  const before=JSON.stringify(original);
                  const take=async (Class,label)=>{
                    const callbacks={selected:null,port:null};
                    const canvas=new Class(root,{
                      onSelect:v=>{callbacks.selected=v;},
                      onPort:v=>{callbacks.port=v;},
                      onMove:()=>{},onEndMove:()=>{},onScale:()=>{}});
                    const samples=[],heap=[];
                    // Warm once without including JIT and first-time layout in the statistic.
                    canvas.setData(original,null,null,[]);
                    for(let i=0;i<3;i++){
                      const t=performance.now();
                      canvas.setData(original,null,null,[]);
                      samples.push(performance.now()-t);
                      heap.push(performance.memory?.usedJSHeapSize??null);
                    }
                    // Compare retained heap after explicit GC. Without this, the
                    // second implementation inherits allocations from the first
                    // and heapUsedSize is not an interpretable memory measure.
                    if(typeof window.gc!=='function')throw Error('Chromium GC instrumentation unavailable');
                    window.gc();window.gc();
                    const heapAfterGc=performance.memory?.usedJSHeapSize??null;
                    const childCount=root.querySelectorAll('*').length;
                    const domBytes=new TextEncoder().encode(root.innerHTML);
                    const digest=await crypto.subtle.digest('SHA-256',domBytes);
                    const hash=Array.from(new Uint8Array(digest)).map(v=>v.toString(16).padStart(2,'0')).join('');
                    const dot=root.querySelector('circle.port-dot');
                    const path=root.querySelector('path.edge-hit');
                    if(!dot||!path)throw Error('Missing expected interactive SVG objects');
                    dot.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));
                    const port=callbacks.port;
                    path.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));
                    const selected=callbacks.selected;
                    const zoomStart=performance.now();
                    canvas.fit();
                    const startWidth=canvas.view.w;
                    for(let i=0;i<40;i++)canvas.zoom(i%2===0?1.12:1/1.12);
                    const zoomMs=performance.now()-zoomStart;
                    const finalWidth=canvas.view.w;
                    root.replaceChildren();
                    return {variant:label,samplesMs:samples.map(v=>+v.toFixed(3)),
                      medianMs:[...samples].sort((a,b)=>a-b)[1],
                      heapUsedBytes:heapAfterGc,heapPreGcBytes:heap.at(-1),
                      domChildren:childCount,svgHash:hash,
                      port,selected,zoomMs,zoomStartWidth:startWidth,zoomEndWidth:finalWidth};
                  };
                  const first=await take(Baseline,'baseline');
                  const second=await take(Optimized,'optimized');
                  return {nodeCount,edgeCount,zoneCount,portCount:nodes.reduce((s,n)=>s+n.ports.length,0),
                    sourceUnmodified:before===JSON.stringify(original),baseline:first,optimized:second};
                }""",[n,e,z])
                assert data["sourceUnmodified"],"Benchmark altered canonical project"
                a,b=data["baseline"],data["optimized"]
                assert a["svgHash"]==b["svgHash"],f"SVG DOM changed for {n}/{e}"
                assert a["domChildren"]==b["domChildren"],f"DOM object count changed for {n}/{e}"
                assert a["port"]==b["port"] and a["selected"]==b["selected"],"Pointer semantics differ"
                assert a["heapUsedBytes"] is not None and b["heapUsedBytes"] is not None
                assert a["port"]=={"node":"N00000","port":"p0"},a["port"]
                assert a["selected"]=={"type":"link","id":"L0"},a["selected"]
                assert a["port"]["node"] in (data["baseline"]["port"]["node"],),a["port"]
                for v in (a,b):
                    assert abs(v["zoomStartWidth"]-v["zoomEndWidth"])<1e-5,v
                data["speedup"]=round(a["medianMs"]/max(0.001,b["medianMs"]),2)
                data["baseline"]["medianMs"]=round(a["medianMs"],3)
                data["optimized"]["medianMs"]=round(b["medianMs"],3)
                summary["cases"].append(data)
                print("SVG_PERF_CASE",json.dumps(data,ensure_ascii=False),flush=True)
            assert not page_errors,page_errors
            summary["checks"]=["byte-identical SVG markup hash","identical DOM size",
                               "same link and port pointer callbacks","canonical project unchanged",
                               "stable zoom world width","no browser page errors"]
            browser.close()
    except Exception as exc:
        summary["errors"].append(str(exc))
        raise
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        FIXTURE.unlink(missing_ok=True)
        (WEB/"canvas-baseline.mjs").unlink(missing_ok=True)
        results=ROOT/"research"/"svg-perf-results"
        results.mkdir(parents=True,exist_ok=True)
        (results/"benchmark.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    assert summary["cases"][-1]["speedup"]>=1.5, "Large corpus must be at least 1.5x faster"
    print("SVG_PERF_PASS",json.dumps({"speedup2000x5000":summary["cases"][-1]["speedup"],
      "checks":summary["checks"]},ensure_ascii=False),flush=True)

if __name__=="__main__":
    run()
