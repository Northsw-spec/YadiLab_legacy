"""Real HTTP + Chromium: opt-in ELK preview, guarded Apply, Save/Open and stale responses."""
from __future__ import annotations
import copy
import json
import socket
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore

ROOT=Path(__file__).resolve().parents[1]

def port_dot(page, node, port):
    return page.evaluate("""([node, port])=>{
      const svg=document.querySelector('#topology');
      const dot=[...svg.querySelectorAll('circle.port-dot')]
        .find(e=>e.dataset.portNode===node&&e.dataset.portId===port);
      if(!dot)throw Error('missing SVG port dot');
      const m=dot.closest('g.network-node').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);
      return {x:Number(m[1])+Number(dot.getAttribute('cx')),
              y:Number(m[2])+Number(dot.getAttribute('cy'))};
    }""",[node,port])

def paths_match_visible_ports(page,project):
    result=page.evaluate("""project=>{
      const svg=document.querySelector('#topology');
      const dots=new Map([...svg.querySelectorAll('circle.port-dot')].map(dot=>{
        const m=dot.closest('g.network-node').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);
        return [JSON.stringify([dot.dataset.portNode,dot.dataset.portId]),
          {x:Number(m[1])+Number(dot.getAttribute('cx')),
           y:Number(m[2])+Number(dot.getAttribute('cy'))}];
      }));
      let maxError=0,count=0;
      for(const link of project.links){
        const path=[...svg.querySelectorAll('path.network-edge')]
          .find(p=>p.dataset.linkId===link.id);
        if(!path)throw Error('missing path '+link.id);
        const a=path.getPointAtLength(0),b=path.getPointAtLength(path.getTotalLength());
        for(const [point,ep] of [[a,link.a],[b,link.b]]){
          const dot=dots.get(JSON.stringify([ep.node,ep.port]));
          if(!dot)throw Error('missing port '+JSON.stringify(ep));
          maxError=Math.max(maxError,Math.hypot(point.x-dot.x,point.y-dot.y));
          count++;
        }
      }
      return {maxError,endpointCount:count};
    }""",project)
    assert result["maxError"] < 0.01,result
    return result

def run():
    with tempfile.TemporaryDirectory() as directory:
        store=ProjectStore(Path(directory))
        demo=json.loads((ROOT/"examples/explicit-three-device-demo.yadilab").read_text())
        store.save("elk_example",demo)
        server=LabHTTPServer(("127.0.0.1",0),store)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        url=f"http://127.0.0.1:{server.server_port}/"
        records={}
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1440,"height":900})
                page.set_default_timeout(45000)
                js_errors=[]
                page.on("pageerror",lambda exc:js_errors.append(str(exc)))
                page.goto(url,wait_until="domcontentloaded")
                page.locator('#saved-projects option[value="elk_example"]').wait_for()
                page.locator("#saved-projects").select_option("elk_example")
                page.locator("#open-project").click()
                page.get_by_text("Öppnade verklig projektfil",exact=False).wait_for()
                before=copy.deepcopy(store.read("elk_example"))
                page.locator("#layout-preview").click()
                page.locator("#layout-apply").wait_for(state="visible")
                page.wait_for_function("!document.querySelector('#layout-apply').disabled")
                assert store.read("elk_example")["sha256"]==before["sha256"],"Preview wrote to disk"
                records["previewDiskUnchanged"]=True
                records["previewGeometry"]=paths_match_visible_ports(page,demo)

                # Save before explicit Apply must be blocked; no disk mutation.
                page.locator("#save-project").click()
                assert store.read("elk_example")["sha256"]==before["sha256"],"Preview silently saved"
                records["prematureSaveBlocked"]=True

                # Cancel must restore the saved canonical project, without making it dirty.
                page.locator("#layout-cancel").click()
                assert page.locator("#layout-apply").is_disabled()
                assert "Sparat" in page.locator("#save-indicator").inner_text()
                records["cancelNoMutation"]=True

                page.locator("#layout-preview").click()
                page.wait_for_function("!document.querySelector('#layout-apply').disabled")
                records["secondPreviewGeometry"]=paths_match_visible_ports(page,demo)
                page.locator("#layout-apply").click()
                assert "Osparade" in page.locator("#save-indicator").inner_text()
                assert store.read("elk_example")["sha256"]==before["sha256"]
                records["applyIsUnsaved"]=True
                page.locator("#save-project").click()
                page.wait_for_function("'Sparat'===document.querySelector('#save-indicator').textContent.split(' · ')[0]")
                after=store.read("elk_example")
                assert after["sha256"]!=before["sha256"],"Expected saved coordinates to change"
                assert len(after["project"]["nodes"])==len(before["project"]["nodes"])
                assert after["project"]["links"]==before["project"]["links"]
                assert after["project"]["zones"]==before["project"]["zones"]
                assert not any("layout" in key.lower() for key in after["project"]),after["project"].keys()
                records["durableCoordsOnly"]=True

                # Open from a new browser page: temporary routed paths do not persist.
                fresh=browser.new_page(viewport={"width":1440,"height":900})
                fresh.goto(url,wait_until="domcontentloaded")
                fresh.locator('#saved-projects option[value="elk_example"]').wait_for()
                fresh.locator("#saved-projects").select_option("elk_example")
                fresh.locator("#open-project").click()
                fresh.get_by_text("Öppnade verklig projektfil",exact=False).wait_for()
                assert fresh.locator("#layout-controls").is_hidden()
                assert fresh.locator("#layout-apply").is_disabled()
                assert fresh.locator("path.network-edge").count()==2
                records["afterOpenUsesUnversionedCanonicalGeometry"]=True

                # Invalidate an in-flight proposal by changing the workspace.
                # Delayed ELK.layout ensures there is an async result to invalidate.
                fresh.evaluate("""()=>{
                  const Original=window.ELK;
                  window.ELK=class extends Original{
                    layout(graph){return new Promise((resolve,reject)=>{
                      setTimeout(()=>super.layout(graph).then(resolve,reject),400);
                    });}
                  };
                }""")
                fresh.locator("#layout-preview").click()
                fresh.locator("#new-project").click()
                fresh.wait_for_function("document.querySelector('#count-nodes').textContent==='0'")
                assert fresh.locator("#layout-apply").is_disabled()
                fresh.wait_for_timeout(1200)
                assert fresh.locator("#count-nodes").inner_text()=="0"
                assert fresh.locator("#layout-apply").is_disabled()
                records["staleResponseRejected"]=True
                assert not js_errors,js_errors
                records["pageErrors"]=[]
                fresh.close()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=4)
        print("ELK_BROWSER_ACCEPTANCE",json.dumps(records,ensure_ascii=False))
        return records

if __name__=="__main__":
    run()
