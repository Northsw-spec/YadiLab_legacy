"""Independent Python/real YadiLab acceptance for ELK 2000/5000 coordinate proposal."""
import json, hashlib, tempfile, copy
from pathlib import Path
from network_core.model import validate_project, ProjectValidationError
from network_core.storage import ProjectStore

root=Path(__file__).resolve().parents[1]
results=root/"research/elk-results"
source=results/"wrapped_candidate.json"
project=json.loads(source.read_text(encoding="utf-8"))
original=copy.deepcopy(project)
assert len(project["nodes"])==2000,len(project["nodes"])
assert len(project["links"])==5000,len(project["links"])
assert project["schemaVersion"]=="1.0"

# Independent oracle: compare rectangles, not only top-left coordinates.
def size(n):
    return 202, max(96,78+len(n["ports"])*23)
def overlaps(nodes):
    ordered=sorted(nodes,key=lambda x:x["x"])
    hits=0
    for i,a in enumerate(ordered):
        aw,ah=size(a)
        for b in ordered[i+1:]:
            if b["x"]>=a["x"]+aw:break
            bw,bh=size(b)
            if min(a["y"]+ah,b["y"]+bh)>max(a["y"],b["y"]):hits+=1
    return hits
assert overlaps(project["nodes"])==0,"Overlapping rectangle"

# Deliberate negative control: independent oracle must detect overlap.
bad=copy.deepcopy(project)
bad["nodes"][1]["x"]=bad["nodes"][0]["x"]
bad["nodes"][1]["y"]=bad["nodes"][0]["y"]
assert overlaps(bad["nodes"])>0,"Geometry oracle failed negative control"

rect_bounds=[]
for n in project["nodes"]:
    w,h=size(n)
    rect_bounds.append((n["x"],n["y"],n["x"]+w,n["y"]+h))
assert all(-100000<=x0<=100000 and -100000<=y0<=100000
        and x1<=100000 and y1<=100000 for x0,y0,x1,y1 in rect_bounds),"Out of range"

validated=validate_project(project)
assert validated==original,"Canonical validator silently changed network data"
assert len({n["id"] for n in validated["nodes"]})==2000
assert len({l["id"] for l in validated["links"]})==5000

with tempfile.TemporaryDirectory() as path:
    store=ProjectStore(Path(path))
    receipt=store.save("elk_bounds_test",validated)
    reopened=store.read("elk_bounds_test")
    assert reopened["sha256"]==receipt["sha256"]
    assert reopened["project"]==validated
    assert len(reopened["project"]["links"])==5000
    assert len(reopened["project"]["nodes"])==2000

# Fail-closed: a stored coordinate outside canonical model limit must be refused.
invalid=copy.deepcopy(project)
invalid["nodes"][0]["x"]=100001
try:
    validate_project(invalid)
except ProjectValidationError:
    pass
else:
    raise AssertionError("Canonical validator admitted invalid x")

evidence={"verdict":"PASS","modelValidation":True,"saveOpen":True,
    "nodeCount":2000,"linkCount":5000,"rectOverlaps":0,
    "rectBounds":[min(r[0] for r in rect_bounds),min(r[1] for r in rect_bounds),
                  max(r[2] for r in rect_bounds),max(r[3] for r in rect_bounds)],
    "negativeOverlapControl":True,"negativeInvalidXControl":True,
    "provenance":"Synthetic schema-1.0 project; no historical import evidence"}
(results/"bounds_native_validator.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
print("NATIVE_BOUNDS_VALIDATION",json.dumps(evidence,ensure_ascii=False))
