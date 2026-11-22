"""H9: Real YadiLab historical receipt + Save/Open with accepted coordinate-only change."""
import copy, json, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
from test_import_verification import candidate
from network_core.storage import ProjectStore
from network_core.import_verification import evidence_status,verify_sources

request, original=candidate()
orig=copy.deepcopy(original)
with tempfile.TemporaryDirectory() as directory:
    store=ProjectStore(Path(directory))
    first=store.save("elk_snapshot",original)
    loaded=store.read("elk_snapshot")
    assert evidence_status({"project":loaded["project"]})["baselineStatus"]=="BASELINE_MATCH"
    assert loaded["project"]["importEvidence"]==orig["importEvidence"]

    # Read-only preview only touches an independent copy, not storage or original.
    proposed=copy.deepcopy(loaded["project"])
    assert proposed["nodes"],"Expected imported candidate nodes"
    proposed["nodes"][0]["x"]+=20
    proposed["nodes"][0]["y"]+=30
    assert store.read("elk_snapshot")["sha256"]==loaded["sha256"]
    assert original==orig
    assert evidence_status({"project":proposed})["baselineStatus"]=="CHANGED_SINCE_IMPORT"
    historical=verify_sources({"project":proposed,"sources":request["sources"]})
    assert historical["sourceStatus"]=="SOURCE_VERIFIED",historical
    assert historical["replayStatus"]=="MATCH",historical
    assert proposed["importEvidence"]==orig["importEvidence"]

    # Accepted change and explicit Save persist only X/Y, retaining original receipt.
    saved=store.save("elk_snapshot",proposed,expected_sha256=loaded["sha256"])
    after=store.read("elk_snapshot")
    assert after["project"]["nodes"][0]["x"]==proposed["nodes"][0]["x"]
    assert after["project"]["nodes"][0]["y"]==proposed["nodes"][0]["y"]
    assert after["project"]["importEvidence"]==orig["importEvidence"]
    assert evidence_status({"project":after["project"]})["baselineStatus"]=="CHANGED_SINCE_IMPORT"
    replay=verify_sources({"project":after["project"],"sources":request["sources"]})
    assert replay["replayStatus"]=="MATCH"
    expected_network=copy.deepcopy(orig)
    expected_network["nodes"][0]["x"]=proposed["nodes"][0]["x"]
    expected_network["nodes"][0]["y"]=proposed["nodes"][0]["y"]
    assert after["project"]==expected_network,"Unexpected project field mutation"
    print(json.dumps({"H9_verdict":"PASS_for_coordinate_only_explicit_Save_Open",
       "previewUnchangedOnDisk":True,"sourceReplay":replay["replayStatus"],
       "baselineAfterAcceptedChange":"CHANGED_SINCE_IMPORT",
       "immutableEvidence":True,"projectFieldsChanged":["nodes[0].x","nodes[0].y"],
       "note":"ELK proposal not yet wired to UI; test deliberately models accepted coordinate-only edit"},
       indent=2))
