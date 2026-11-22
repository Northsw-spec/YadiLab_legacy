"""Real Chromium regression: huge ELK-like topology must not jump to 9000 world units on zoom."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore

def run():
    with tempfile.TemporaryDirectory() as directory:
        server=LabHTTPServer(("127.0.0.1",0),ProjectStore(Path(directory)))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with sync_playwright() as browser_tool:
                browser=browser_tool.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1440,"height":900})
                page.goto(f"http://127.0.0.1:{server.server_port}/",wait_until="domcontentloaded")
                assert page.locator("#topology").count()==1
                result=page.evaluate("""async ()=>{
                  const {TopologyCanvas}=await import('/canvas.js');
                  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
                  svg.id='zoom-large-regression';
                  svg.style.cssText='position:fixed;top:30px;left:30px;width:1150px;height:730px;z-index:20;pointer-events:auto;background:#101928';
                  document.body.append(svg);
                  const canvas=new TopologyCanvas(svg,{
                    onSelect:()=>{},onPort:()=>{},onMove:()=>{},onEndMove:()=>{},onScale:()=>{}
                  });
                  const mk=(id,x,y)=>({id,kind:'switch',label:id,zoneId:null,x,y,ports:[]});
                  const small={schemaVersion:'1.0',name:'small',zones:[],links:[],nodes:[mk('s',0,0)]};
                  const large={schemaVersion:'1.0',name:'large',zones:[],links:[],
                    nodes:[mk('A',0,0),mk('B',45000,38000),mk('C',3000,37000)]};
                  canvas.setData(small,null,null,[],{project:large,preview:true,paths:{}});
                  canvas.fit();
                  const before={...canvas.view};
                  const pointerX=svg.getBoundingClientRect().left+320;
                  const pointerY=svg.getBoundingClientRect().top+180;
                  const worldBefore=canvas.toWorld(pointerX,pointerY);
                  svg.dispatchEvent(new WheelEvent('wheel',{bubbles:true,cancelable:true,
                    deltaY:-120,clientX:pointerX,clientY:pointerY}));
                  const afterIn={...canvas.view},worldAfter=canvas.toWorld(pointerX,pointerY);
                  svg.dispatchEvent(new WheelEvent('wheel',{bubbles:true,cancelable:true,
                    deltaY:120,clientX:pointerX,clientY:pointerY}));
                  const afterBack={...canvas.view};
                  svg.dispatchEvent(new WheelEvent('wheel',{bubbles:true,cancelable:true,
                    deltaY:120,clientX:pointerX,clientY:pointerY}));
                  const afterOut={...canvas.view};
                  canvas.setData(small,null,null,[],null);
                  canvas.fit();
                  const reset={...canvas.view},resetLimit=canvas.zoomOutLimit;
                  return {before,afterIn,afterBack,afterOut,worldBefore,worldAfter,
                    reset,resetLimit,canonicalPreviewDidNotMutate:small.nodes[0].x===0,
                    viewport:svg.getAttribute('viewBox')};
                }""")
                width=result["before"]["w"]
                assert width>9000,result
                assert abs(result["afterIn"]["w"]-width/1.12)<1e-6,result
                assert abs(result["afterBack"]["w"]-width)<1e-6,result
                assert abs(result["afterOut"]["w"]-width*1.12)<1e-6,result
                for axis in ("x","y"):
                    assert abs(result["worldBefore"][axis]-result["worldAfter"][axis])<1e-6,result
                assert result["resetLimit"]==9000,result
                assert result["canonicalPreviewDidNotMutate"],result
                print("CANVAS_LARGE_ZOOM_PASS",json.dumps({
                    "fittedWorldWidth":round(width,2),
                    "zoomInWorldWidth":round(result["afterIn"]["w"],2),
                    "zoomOutWorldWidth":round(result["afterOut"]["w"],2),
                    "preservedPointerAnchor":True,
                    "resetZoomCap":result["resetLimit"],
                    "previewDidNotMutateCanonicalProject":True
                }),flush=True)
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

if __name__ == "__main__":
    run()
