"""Frozen-app acceptance for trailing track numbers and complete folder rendering."""
import json, socket, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.request import Request, urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mixcut import media
from mixcut.server import Store

def main():
 with tempfile.TemporaryDirectory(prefix='mixcut181-') as tmp:
  root=Path(tmp).resolve();music=root/'music';folder=music/'风格一';folder.mkdir(parents=True)
  def ff(*args):subprocess.run(['ffmpeg','-nostdin','-v','error','-y',*args],check=True,capture_output=True,timeout=60)
  video=root/'video.mp4';ff('-f','lavfi','-i','testsrc2=s=640x360:r=24:d=2','-c:v','libx264',str(video))
  tracks=[]
  for n in (4,2,5,1,3):
   path=folder/f'New_Hindi_💙[3Ro180iBBcU]-去重 {n:02d}.m4a'
   ff('-f','lavfi','-i',f'sine=f={220*n}:duration=1','-c:a','aac',str(path));tracks.append(media._asset(path,'music',quick_music=True))
  state=root/'state';Store(state).put('library',{'music_dir':str(music),'scan':{'videos':[media._asset(video,'video')],'music':tracks}})
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  def api(route,body=None):
   with urlopen(Request(f'http://127.0.0.1:{port}'+route,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'}),timeout=20) as response:return json.load(response)
  with (root/'server.log').open('w') as log:
   process=subprocess.Popen([sys.argv[1],'--server','--port',str(port),'--state-dir',str(state)],stdout=log,stderr=log)
   try:
    for _ in range(100):
     try:boot=api('/api/bootstrap');break
     except OSError:time.sleep(.1)
    assert boot['version']=='1.8.1'
    batch=api('/api/plan',{'config':{'duration_basis':'music','music_mode':'folder','count':1,'width':640,'height':360,'fps':24,'hardware':'software_fast','output_dir':str(root/'exports'),'include_track_titles':True}})
    assert batch['config']['nonstop_music'] is False
    item=batch['items'][0]
    assert Path(item['music'][0]['path']).stem.endswith('去重 01')
    assert Path(item['music'][1]['path']).stem.endswith('去重 02')
    assert len(item['music'])==5 and len({s['id'] for s in item['music']})==5
    api(f"/api/batches/{batch['id']}/start",{})
    for _ in range(300):
     batches=api('/api/batches');current=next(b for b in batches if b['id']==batch['id']);item=current['items'][0]
     if item['status']=='failed':raise AssertionError(item.get('error'))
     if item['status']=='success' and item.get('thumbnails',{}).get('status')=='ready':break
     time.sleep(.1)
    else:raise AssertionError('render timeout')
    assert 4.9<item['result']['duration']<5.2
    assert len(item['result']['played_music'])==5
    assert item['result']['played_music'][0]['title'].endswith('去重 01')
    assert item['result']['played_music'][1]['title'].endswith('去重 02')
    ff('-xerror','-i',item['output_path'],'-f','null','-')
    assert all(Path(s['path']).exists() for s in tracks)
    print('V1.8.1 packaged trailing-number acceptance passed: suffix 01/02 first, five songs once, direct join default, video loop, full output decode, original music retained.')
   finally:
    try:api('/api/shutdown',{})
    except Exception:pass
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
if __name__=='__main__':main()
