import test from 'node:test';
import assert from 'node:assert/strict';
import {TopologyCanvas} from '../web/canvas.js';

const node = (id, x, y) => ({id, x, y, ports: []});
const small = {nodes:[node('a',0,0),node('b',400,0)]};
const large = {nodes:[node('a',0,0),node('b',45000,38000),node('c',1000,37000)]};

function camera(project, presentation = null) {
  // Use the actual camera methods without DOM event listeners; no mock layout
  // engine and no altered production zoom math.
  const canvas = Object.create(TopologyCanvas.prototype);
  canvas.svg = {
    clientWidth: 1200, clientHeight: 750,
    getBoundingClientRect: () => ({left:90, top:35, width:1200, height:750}),
    setAttribute: (name, value) => {if(name === 'viewBox')canvas.viewBox=value;}
  };
  canvas.callbacks = {onScale: () => {}};
  canvas.project = project;
  canvas.presentation = presentation;
  canvas.view = {x:-30,y:-30,w:1200,h:750};
  canvas.zoomOutLimit = 9000;
  return canvas;
}
const close = (a,b) => assert.ok(Math.abs(a-b) < 0.00001, String(a)+' != '+String(b));

test('large fitted layout zooms smoothly rather than snapping to the old 9000 cap', () => {
  const canvas=camera(large);
  canvas.fit();
  const width=canvas.view.w;
  assert.ok(width>45000,'fixture must exceed the old 9000-world-unit cap');
  assert.ok(canvas.zoomOutLimit>=1.5*width);
  canvas.zoom(1.12);
  close(canvas.view.w,width/1.12);
  canvas.zoom(1/1.12);
  close(canvas.view.w,width);
  canvas.zoom(1/1.12);
  close(canvas.view.w,width*1.12);
  assert.ok(canvas.view.w>9000);
});

test('zoom retains world coordinate under noncentral cursor', () => {
  const canvas=camera(large);canvas.fit();
  const cursor={x:380,y:260};
  const old=canvas.toWorld(cursor.x,cursor.y);
  canvas.zoom(1.12,cursor.x,cursor.y);
  const next=canvas.toWorld(cursor.x,cursor.y);
  close(old.x,next.x);close(old.y,next.y);
});

test('preview extent drives zoom without mutating canonical project', () => {
  const source=JSON.stringify(small);
  const canvas=camera(small,{project:large,preview:true,paths:{}});
  canvas.fit();
  const w=canvas.view.w;
  assert.ok(w>9000);
  canvas.zoom(1.12);
  close(canvas.view.w,w/1.12);
  assert.equal(JSON.stringify(small),source);
});

test('new small document resets the large zoom-out allowance', () => {
  const canvas=camera(large);canvas.fit();
  assert.ok(canvas.zoomOutLimit>9000);
  canvas.project=small;
  canvas.presentation=null;
  canvas.fit();
  assert.equal(canvas.zoomOutLimit,9000);
  for(let i=0;i<100;i++)canvas.zoom(1/1.12);
  close(canvas.view.w,9000);
  assert.equal(canvas.viewBox.split(' ').length,4);
});

test('zoom and Fit reuse exactly one pre-write CSS viewport measurement', () => {
  const canvas=camera(large);
  let reads=0, writes=0, freshRect=false;
  const oldRect=canvas.svg.getBoundingClientRect;
  canvas.svg.getBoundingClientRect=()=>{reads++;freshRect=true;return oldRect();};
  canvas.svg.setAttribute=(name,value)=>{
    assert.equal(name,'viewBox');
    assert.equal(freshRect,true,'viewBox write must follow CSS geometry read');
    freshRect=false;
    writes++;
    canvas.viewBox=value;
  };
  canvas.fit();
  assert.equal(reads,1,'Fit should measure viewport once');
  assert.equal(writes,1);
  canvas.zoom(1.12);
  assert.equal(reads,2,'Zoom should reuse rect for toWorld and setView');
  assert.equal(writes,2);
  canvas.zoom(1/1.12,425,315);
  assert.equal(reads,3,'Mouse-anchored zoom should measure once');
  assert.equal(writes,3);
  canvas.setView();
  assert.equal(reads,4,'Standalone setView reads before writing');
  assert.equal(writes,4);
});

test('dense wheel burst commits one SVG viewBox per animation frame', () => {
  const originalRAF = globalThis.requestAnimationFrame;
  const originalCancel = globalThis.cancelAnimationFrame;
  const scheduled = new Map();
  let token=0, cancelled=0;
  globalThis.requestAnimationFrame = callback => {
    const id=++token;
    scheduled.set(id,callback);
    return id;
  };
  globalThis.cancelAnimationFrame = id => {
    if(scheduled.delete(id))cancelled++;
  };
  try {
    const canvas=camera(large);
    canvas.pendingViewFrame=null;
    let writes=0, scales=0;
    canvas.callbacks.onScale=()=>{scales++;};
    const oldWrite=canvas.svg.setAttribute;
    canvas.svg.setAttribute=(name,value)=>{writes++;oldWrite(name,value);};
    canvas.fit();
    const initial={...canvas.view};
    assert.equal(writes,1);
    for(let i=0;i<40;i++)canvas.zoom(i%2===0?1.12:1/1.12,350,250,true);
    assert.equal(writes,2,'first event paints, later same-frame events are coalesced');
    assert.equal(scales,2,'first event scale is immediately visible');
    assert.equal(scheduled.size,1,'only one requestAnimationFrame is queued');
    close(canvas.view.w,initial.w);
    const [id,callback]=[...scheduled.entries()][0];
    scheduled.delete(id);
    callback(1234);
    assert.equal(writes,3);
    assert.equal(scales,3);
    close(canvas.view.w,initial.w);
    assert.equal(canvas.pendingViewFrame,null);

    canvas.zoom(1.12,350,250,true);
    assert.equal(scheduled.size,0,'an isolated new-frame event paints without an rAF');
    assert.equal(writes,4,'new frame begins with immediate paint');
    canvas.zoom(1/1.12,350,250,true);
    assert.equal(scheduled.size,1,'subsequent same-frame event queues one rAF');
    canvas.fit();
    assert.equal(scheduled.size,0,'Fit must cancel obsolete wheel frame');
    assert.equal(cancelled,1);
    assert.equal(writes,5);
    close(canvas.view.w,initial.w);
  } finally {
    globalThis.requestAnimationFrame=originalRAF;
    globalThis.cancelAnimationFrame=originalCancel;
  }
});

test('pending wheel frame is flushed before a new pointer gesture', () => {
  const oldRAF=globalThis.requestAnimationFrame;
  const oldCancel=globalThis.cancelAnimationFrame;
  const pending=new Map();
  let id=0;
  globalThis.requestAnimationFrame=callback=>{pending.set(++id,callback);return id;};
  globalThis.cancelAnimationFrame=key=>{pending.delete(key);};
  try {
    const canvas=camera(large);
    canvas.pendingViewFrame=null;
    let writes=0;
    canvas.svg.setPointerCapture=()=>{};
    canvas.svg.setAttribute=(name,value)=>{writes++;canvas.viewBox=value;};
    canvas.fit();
    canvas.zoom(1.12,390,340,true);
    assert.equal(writes,2,'first pointer event should update the visible camera');
    assert.equal(pending.size,0,'a single wheel event must not schedule an rAF');
    // A second event is deferred; pointer capture must commit it before drag.
    canvas.zoom(1.12,390,340,true);
    assert.equal(pending.size,1);
    assert.equal(writes,2);
    canvas.capture({pointerId:42},{kind:'pan',x:390,y:340,start:{...canvas.view}});
    assert.equal(writes,3);
    assert.equal(pending.size,0);
    assert.equal(canvas.interaction.pointerId,42);
  } finally {
    globalThis.requestAnimationFrame=oldRAF;
    globalThis.cancelAnimationFrame=oldCancel;
  }
});

test('frame-spaced wheel gestures paint immediately without an extra frame', () => {
  const oldRAF=globalThis.requestAnimationFrame,oldCancel=globalThis.cancelAnimationFrame;
  const frames=new Map();
  globalThis.requestAnimationFrame=fn=>{frames.set(1,fn);return 1;};
  globalThis.cancelAnimationFrame=id=>{frames.delete(id);};
  try {
    const canvas=camera(large);
    canvas.pendingViewFrame=null;
    let writes=0;
    canvas.svg.setAttribute=(name,value)=>{writes++;canvas.viewBox=value;};
    canvas.fit();
    for(let i=0;i<8;i++){
      canvas.lastGesturePaintAt=performance.now()-100;
      canvas.zoom(i%2===0?1.12:1/1.12,350,250,true);
      assert.equal(frames.size,0,'a single frame-spaced event must not be deferred');
    }
    assert.equal(writes,9,'Fit plus each of 8 isolated events paints immediately');
  } finally {
    globalThis.requestAnimationFrame=oldRAF;
    globalThis.cancelAnimationFrame=oldCancel;
  }
});
