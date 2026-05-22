#!/usr/bin/env python3
"""
GitHub Actions 构建脚本
读取当前目录下所有 .md 选题卡 → 生成 dist/index.html
"""

import os
import re
import json
from datetime import datetime

TOPIC_DIR = "."
OUTPUT = "dist/index.html"


def parse_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    topic = {
        "filename": os.path.basename(filepath),
        "状态": "待执行", "平台": "-", "优先级": "中",
        "创建日期": "", "来源": "", "title": "", "core_point": "", "opening": "",
    }

    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                topic[k.strip()] = v.strip()

    for field, pattern in [("title", r'## 标题假设\n+(.+)'),
                             ("core_point", r'## 核心观点\n+(.+)'),
                             ("opening", r'## 开头第一句\n+(.+)')]:
        m = re.search(pattern, content)
        if m:
            topic[field] = m.group(1).strip()

    if not topic["title"]:
        topic["title"] = os.path.splitext(os.path.basename(filepath))[0]

    return topic


def load_topics():
    topics = []
    for fname in sorted(os.listdir(TOPIC_DIR)):
        if fname.endswith(".md") and not fname.startswith("【模板】") and not fname.startswith("."):
            try:
                topics.append(parse_md(os.path.join(TOPIC_DIR, fname)))
            except Exception as e:
                print(f"跳过 {fname}: {e}")
    return topics


def generate_html(topics):
    topics_json = json.dumps(topics, ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(topics)
    waiting = sum(1 for t in topics if t["状态"] == "待执行")
    writing = sum(1 for t in topics if t["状态"] == "写作中")
    done = sum(1 for t in topics if t["状态"] == "已发布")
    sources = sorted(set(t["来源"] for t in topics if t["来源"]))
    source_options = "\n".join(f'<option value="{s}">{s}</option>' for s in sources)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>选题看板</title>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#fff;--text:#1c1c1e;--text2:#3a3a3c;--muted:#8e8e93;--sep:rgba(0,0,0,.08);--blue:#007aff;--orange:#ff9500;--green:#34c759;--red:#ff3b30}}
    body{{font-family:-apple-system,"SF Pro Display",BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;-webkit-font-smoothing:antialiased}}
    .topbar{{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.75);backdrop-filter:saturate(200%) blur(24px);-webkit-backdrop-filter:saturate(200%) blur(24px);border-bottom:.5px solid var(--sep);padding:0 32px;height:48px;display:flex;align-items:center;justify-content:space-between}}
    .topbar-name{{font-size:.88rem;font-weight:600;letter-spacing:-.2px}}
    .topbar-time{{font-size:.78rem;color:var(--muted)}}
    .hero{{padding:52px 32px 36px;max-width:1060px;margin:0 auto;border-bottom:.5px solid var(--sep)}}
    .hero h1{{font-size:3rem;font-weight:700;letter-spacing:-1.5px;line-height:1.1;margin-bottom:28px}}
    .hero-stats{{display:flex;gap:10px;flex-wrap:wrap}}
    .stat{{background:#f5f5f7;border-radius:14px;padding:16px 22px;flex:1;min-width:100px;display:flex;flex-direction:column;gap:4px}}
    .stat-n{{font-size:2rem;font-weight:700;letter-spacing:-1px;line-height:1;color:var(--text)}}
    .stat-n.b{{color:var(--blue)}}.stat-n.o{{color:var(--orange)}}.stat-n.g{{color:var(--green)}}
    .stat-l{{font-size:.75rem;color:var(--muted);font-weight:500}}
    .container{{max-width:1060px;margin:0 auto;padding:28px 32px 60px}}
    .toolbar{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;align-items:center}}
    .sw{{flex:1;min-width:220px;display:flex;align-items:center;gap:8px;background:#f5f5f7;border-radius:12px;padding:10px 14px}}
    .sw svg{{color:var(--muted);flex-shrink:0}}
    .sw input{{border:none;background:transparent;outline:none;font-family:inherit;font-size:.92rem;color:var(--text);width:100%}}
    .sw input::placeholder{{color:var(--muted)}}
    .seg{{display:flex;background:#f5f5f7;border-radius:10px;padding:3px;gap:2px}}
    .sb{{border:none;background:transparent;cursor:pointer;font-family:inherit;font-size:.84rem;font-weight:500;color:var(--muted);padding:6px 14px;border-radius:8px;transition:all .15s}}
    .sb.on{{background:#fff;color:var(--text);font-weight:600;box-shadow:0 1px 6px rgba(0,0,0,.1)}}
    .ps{{appearance:none;-webkit-appearance:none;background:#f5f5f7;border:none;outline:none;cursor:pointer;font-family:inherit;font-size:.84rem;font-weight:500;color:var(--text);padding:9px 32px 9px 14px;border-radius:10px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%238e8e93' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center}}
    .rc{{margin-left:auto;font-size:.8rem;color:var(--muted);font-weight:500}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1px;background:rgba(0,0,0,.06);border-radius:18px;overflow:hidden}}
    .card{{background:#fff;padding:22px 22px 18px;cursor:pointer;transition:background .12s}}
    .card:hover{{background:#fafafa}}.card:active{{background:#f5f5f7}}
    .card-tags{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:12px}}
    .tag{{font-size:.68rem;font-weight:600;letter-spacing:.15px;padding:3px 8px;border-radius:6px}}
    .t-待执行{{background:rgba(255,149,0,.1);color:#b36800}}
    .t-写作中{{background:rgba(0,122,255,.1);color:var(--blue)}}
    .t-已发布{{background:rgba(52,199,89,.12);color:#1f7a3a}}
    .t-搁置{{background:#f0f0f0;color:#888}}
    .t-高{{background:rgba(255,59,48,.1);color:#c0392b}}
    .t-中{{background:rgba(0,122,255,.08);color:var(--blue)}}
    .t-低{{background:#f0f0f0;color:#888}}
    .t-p{{background:#f0f0f0;color:#444}}
    .card-title{{font-size:1.02rem;font-weight:600;line-height:1.45;letter-spacing:-.25px;margin-bottom:7px}}
    .card-body{{font-size:.84rem;color:var(--muted);line-height:1.55;margin-bottom:10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
    .card-hook{{font-size:.81rem;color:#555;background:rgba(0,122,255,.06);border-radius:8px;padding:8px 12px;line-height:1.5;font-style:italic;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
    .card-meta{{font-size:.72rem;color:var(--muted);margin-top:14px}}
    .empty{{grid-column:1/-1;background:#fff;text-align:center;padding:80px 20px;color:var(--muted);border-radius:18px}}
    .overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.3);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);z-index:200;align-items:center;justify-content:center;padding:20px}}
    .overlay.on{{display:flex}}
    .sheet{{background:#fff;border-radius:22px;max-width:580px;width:100%;max-height:86vh;overflow-y:auto;box-shadow:0 32px 80px rgba(0,0,0,.22);position:relative}}
    .sh{{padding:28px 28px 0;position:sticky;top:0;z-index:1;background:rgba(255,255,255,.95);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:22px 22px 0 0}}
    .sc{{position:absolute;top:18px;right:18px;width:30px;height:30px;border-radius:50%;background:#f0f0f0;border:none;cursor:pointer;font-size:.9rem;color:#666;display:flex;align-items:center;justify-content:center}}
    .sc:hover{{background:#e5e5e5}}
    .st{{font-size:1.25rem;font-weight:700;line-height:1.4;letter-spacing:-.4px;padding-right:36px;margin-bottom:12px}}
    .stags{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:18px}}
    .sr{{height:.5px;background:rgba(0,0,0,.08);margin:0 -28px}}
    .sb2{{padding:22px 28px 32px}}
    .srow{{margin-bottom:22px}}
    .slbl{{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:7px;display:block}}
    .stxt{{font-size:.96rem;line-height:1.68;color:var(--text2)}}
    .sq{{background:rgba(0,122,255,.06);border-radius:12px;padding:14px 16px;font-style:italic;font-size:.93rem;line-height:1.6;color:#444}}
    .sf{{font-size:.77rem;color:var(--muted);padding-top:18px;border-top:.5px solid rgba(0,0,0,.08);display:flex;gap:14px;flex-wrap:wrap}}
  </style>
</head>
<body>
<div class="topbar"><span class="topbar-name">选题看板</span><span class="topbar-time">更新于 {now}</span></div>
<div class="hero">
  <h1>选题库</h1>
  <div class="hero-stats">
    <div class="stat"><span class="stat-n b">{total}</span><span class="stat-l">全部选题</span></div>
    <div class="stat"><span class="stat-n o">{waiting}</span><span class="stat-l">待执行</span></div>
    <div class="stat"><span class="stat-n b">{writing}</span><span class="stat-l">写作中</span></div>
    <div class="stat"><span class="stat-n g">{done}</span><span class="stat-l">已发布</span></div>
  </div>
</div>
<div class="container">
  <div class="toolbar">
    <div class="sw"><svg width="14" height="14" viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="6.5" stroke="currentColor" stroke-width="1.8"/><path d="M14 14L18 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><input type="text" id="search" placeholder="搜索选题..." oninput="render()"/></div>
    <div class="seg" id="seg"><button class="sb on" data-v="" onclick="pick(this)">全部</button><button class="sb" data-v="待执行" onclick="pick(this)">待执行</button><button class="sb" data-v="写作中" onclick="pick(this)">写作中</button><button class="sb" data-v="已发布" onclick="pick(this)">已发布</button></div>
    <select class="ps" id="fPri" onchange="render()"><option value="">全部优先级</option><option value="高">高</option><option value="中">中</option><option value="低">低</option></select>
    <select class="ps" id="fPlt" onchange="render()"><option value="">全部平台</option><option value="公众号">公众号</option><option value="小红书">小红书</option><option value="两个都发">两个都发</option></select>
    <select class="ps" id="fSrc" onchange="render()"><option value="">全部来源</option>{source_options}</select>
    <span class="rc" id="cnt"></span>
  </div>
  <div class="grid" id="grid"></div>
</div>
<div class="overlay" id="overlay" onclick="closeSheet(event)">
  <div class="sheet"><div class="sh"><button class="sc" onclick="closeSheet()">✕</button><div class="st" id="s-title"></div><div class="stags" id="s-tags"></div><div class="sr"></div></div><div class="sb2" id="s-body"></div></div>
</div>
<script>
const D={topics_json};let sf='';
function pick(b){{document.querySelectorAll('#seg .sb').forEach(x=>x.classList.remove('on'));b.classList.add('on');sf=b.dataset.v;render();}}
function render(){{
  const q=document.getElementById('search').value.toLowerCase();
  const pr=document.getElementById('fPri').value;
  const pl=document.getElementById('fPlt').value;
  const src=document.getElementById('fSrc').value;
  let list=D.filter(t=>{{
    if(sf&&t['状态']!==sf)return false;
    if(pr&&t['优先级']!==pr)return false;
    if(pl&&!t['平台'].includes(pl))return false;
    if(src&&t['来源']!==src)return false;
    if(q&&!(t.title+t.core_point+t.opening+t['来源']).toLowerCase().includes(q))return false;
    return true;
  }});
  const ord={{'高':0,'中':1,'低':2}};
  list.sort((a,b)=>(ord[a['优先级']]??1)-(ord[b['优先级']]??1));
  document.getElementById('cnt').textContent=list.length+' 个选题';
  const g=document.getElementById('grid');
  if(!list.length){{g.innerHTML='<div class="empty"><div style="font-size:2.5rem;opacity:.5;margin-bottom:10px">📭</div><p>没有符合条件的选题</p></div>';return;}}
  g.innerHTML=list.map((t,_,arr)=>`<div class="card" onclick="openSheet(${{D.indexOf(t)}})"><div class="card-tags"><span class="tag t-${{t['状态']}}">${{t['状态']}}</span><span class="tag t-${{t['优先级']}}">${{t['优先级']}}</span><span class="tag t-p">${{t['平台']}}</span></div><div class="card-title">${{t.title||t.filename}}</div>${{t.core_point?`<div class="card-body">${{t.core_point}}</div>`:''}}`+`${{t.opening?`<div class="card-hook">${{t.opening}}</div>`:''}}<div class="card-meta">${{t['创建日期']}}${{t['来源']?'  ·  '+t['来源']:''}}</div></div>`).join('');
}}
function openSheet(i){{
  const t=D[i];
  document.getElementById('s-title').textContent=t.title||t.filename;
  document.getElementById('s-tags').innerHTML=`<span class="tag t-${{t['状态']}}">${{t['状态']}}</span><span class="tag t-${{t['优先级']}}">${{t['优先级']}}</span><span class="tag t-p">${{t['平台']}}</span>`;
  document.getElementById('s-body').innerHTML=`${{t.core_point?`<div class="srow"><span class="slbl">核心观点</span><p class="stxt">${{t.core_point}}</p></div>`:''}}`+`${{t.opening?`<div class="srow"><span class="slbl">开头第一句</span><div class="sq">${{t.opening}}</div></div>`:''}}<div class="sf">${{t['创建日期']?`<span>${{t['创建日期']}}</span>`:''}}</div>`;
  document.getElementById('overlay').classList.add('on');
}}
function closeSheet(e){{if(!e||e.target===document.getElementById('overlay'))document.getElementById('overlay').classList.remove('on');}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeSheet();}});
render();
</script>
</body></html>"""


if __name__ == "__main__":
    print("扫描选题卡...")
    topics = load_topics()
    print(f"找到 {len(topics)} 张选题卡")
    os.makedirs("dist", exist_ok=True)
    html = generate_html(topics)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUTPUT}")
