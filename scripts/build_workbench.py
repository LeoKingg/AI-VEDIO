#!/usr/bin/env python3
"""Compile any V3.0 act handbook markdown into a zero-drift interactive HTML Copy Workbench.

Zero external dependencies (Python 3 stdlib only).
Guarantees 100% byte-level parity between handbook prompt blocks and the HTML workbench.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "redline-auditor" / "scripts"))
import lint_prompt as lp  # noqa: E402


def _extract_card_meta(scope: str, uid: str) -> Dict[str, Any]:
    lines = scope.splitlines()
    heading = ""
    for line in lines:
        if line.lstrip().startswith("#"):
            heading = re.sub(r"^#+\s*", "", line).strip()
            heading = heading.replace("`", "").replace("**", "")
    bind = ""
    check = ""
    for line in lines:
        if any(k in line for k in ("绑定参考", "绑定资产", "参考图")):
            bind = re.sub(r"^-\s*\*\*[^*]+\*\*[：:]\s*", "", line).strip().replace("`", "")
        elif any(k in line for k in ("验收要点", "剪映", "备注")):
            check = re.sub(r"^-\s*\*\*[^*]+\*\*[：:]\s*", "", line).strip().replace("`", "")

    is_anchor = bool(re.search(r"锚点|★", heading + " " + bind))
    mode_match = re.search(r"(SEQ-Multi|SEQ-Grid|M-Master|V-Ref|S-Struct|E-Edit)", heading)
    mode = mode_match.group(1) if mode_match else ("生图" if uid.upper().startswith(lp.IMAGE_PREFIXES) else "视频")
    return {
        "title": heading or uid,
        "bind": bind or "见手册绑定说明",
        "check": check or "按 V3.0 红线门禁与 7 维质检标准验收",
        "anchor": is_anchor,
        "badge": f"★ 锚点 · {mode}" if is_anchor else mode,
        "badgeTone": "primary" if is_anchor else ("success" if mode.startswith(("SEQ", "M-")) else "muted"),
    }


def parse_handbook(handbook_path: Path) -> Dict[str, Any]:
    text = handbook_path.read_text(encoding="utf-8")
    doc_title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    doc_title = doc_title_m.group(1).strip().replace("`", "") if doc_title_m else handbook_path.stem

    marker_re = re.compile(
        r"<!--\s*PROMPT_START\s*:\s*([^>\s]+)\s*-->(.*?)<!--\s*PROMPT_END\s*-->",
        re.DOTALL,
    )
    images: List[Dict[str, Any]] = []
    videos: List[Dict[str, Any]] = []

    for idx, m in enumerate(marker_re.finditer(text), start=1):
        uid = m.group(1).strip()
        prompt = lp._strip_fence(m.group(2).strip())
        scope = lp._extract_unit_scope(text, m.start())
        kind, _ = lp._classify_unit(uid)
        meta = _extract_card_meta(scope, uid)
        item = {
            "id": f"{kind}-{idx}-{uid}",
            "uid": uid,
            "title": meta["title"],
            "badge": meta["badge"],
            "badgeTone": meta["badgeTone"],
            "anchor": meta["anchor"],
            "bind": meta["bind"],
            "check": meta["check"],
            "prompt": prompt,
        }
        if kind == "image":
            images.append(item)
        else:
            videos.append(item)

    return {
        "docTitle": doc_title,
        "sourceFile": handbook_path.name,
        "images": images,
        "videos": videos,
    }


def render_html(data: Dict[str, Any]) -> str:
    title_esc = html.escape(data["docTitle"])
    total = len(data["images"]) + len(data["videos"])
    img_anchors = sum(1 for x in data["images"] if x["anchor"])
    vid_anchors = sum(1 for x in data["videos"] if x["anchor"])
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title_esc}｜V3.0 执行工作台</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-4 md:p-6 m-0">
  <div class="max-w-5xl mx-auto space-y-5">
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 md:p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h1 class="text-lg font-bold tracking-tight">{title_esc}</h1>
          <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-[var(--primary)] text-[var(--primary-foreground)]">V3.0 自动编译 · 零失步</span>
        </div>
        <p class="text-xs text-[var(--muted-foreground)]">
          由 <code class="text-[var(--code-foreground)]">scripts/build_workbench.py</code> 直接编译自 <code class="text-[var(--code-foreground)]">{html.escape(data["sourceFile"])}</code>（100% 逐字节一致）｜粘贴后删除纯文本 <code class="text-[var(--code-foreground)]">@资产名</code> 并用即梦 <code class="text-[var(--code-foreground)]">@</code> 弹窗按序重绑。
        </p>
      </div>
      <div class="flex items-center gap-3 text-xs shrink-0">
        <div class="px-3 py-1.5 rounded-lg bg-[var(--content)] border border-[var(--border)]">
          已完成：<span id="progress-count" class="font-bold tabular-nums">0 / {total}</span>
        </div>
        <button id="reset-progress" type="button" class="px-2.5 py-1.5 rounded-lg border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition cursor-pointer">
          清空勾选
        </button>
      </div>
    </header>

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
      <div class="flex items-center gap-2 flex-wrap">
        <button type="button" data-tab="videos" class="tab-btn px-3.5 py-2 rounded-lg text-xs font-semibold transition">
          ① 视频生成（{len(data["videos"])} 条）
        </button>
        <button type="button" data-tab="images" class="tab-btn px-3.5 py-2 rounded-lg text-xs font-semibold transition">
          ② Seedream 5.5 生图（{len(data["images"])} 张）
        </button>
      </div>
      <label class="inline-flex items-center gap-2 text-xs text-[var(--muted-foreground)] cursor-pointer select-none">
        <input id="only-anchors" type="checkbox" class="w-3.5 h-3.5 accent-[var(--primary)] cursor-pointer" />
        <span>只看首轮锚点（{img_anchors} 图 + {vid_anchors} 视频）</span>
      </label>
    </div>

    <main id="panel-videos" class="space-y-4"></main>
    <main id="panel-images" class="space-y-4 hidden"></main>
  </div>

  <script>
    const DATA = {data_json};
    const STORAGE_KEY = 'ai_vedio_v3_wb_' + DATA.sourceFile;
    let doneMap = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
    const totalCount = DATA.images.length + DATA.videos.length;

    function updateProgress() {{
      const done = Object.values(doneMap).filter(Boolean).length;
      document.getElementById('progress-count').textContent = `${{done}} / ${{totalCount}}`;
    }}

    function toneClasses(tone) {{
      if (tone === 'success') return 'bg-[var(--card)] text-[var(--success)] border border-[var(--success)]';
      if (tone === 'warning') return 'bg-[var(--card)] text-[var(--warning)] border border-[var(--warning)]';
      if (tone === 'primary') return 'bg-[var(--primary)] text-[var(--primary-foreground)]';
      return 'bg-[var(--content)] text-[var(--muted-foreground)] border border-[var(--border)]';
    }}

    function createCard(item, meta1Label, meta2Label) {{
      const card = document.createElement('section');
      card.className = 'bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 space-y-3';

      const header = document.createElement('div');
      header.className = 'flex items-start justify-between gap-3 flex-wrap';

      const left = document.createElement('div');
      left.className = 'flex items-center gap-2.5 flex-wrap';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = Boolean(doneMap[item.id]);
      cb.className = 'w-4 h-4 accent-[var(--primary)] cursor-pointer';
      cb.addEventListener('change', () => {{
        doneMap[item.id] = cb.checked;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(doneMap));
        updateProgress();
      }});

      const h3 = document.createElement('h3');
      h3.className = 'text-sm font-semibold';
      h3.textContent = item.title;

      const badge = document.createElement('span');
      badge.className = `px-2 py-0.5 text-xs rounded-full font-medium ${{toneClasses(item.badgeTone)}}`;
      badge.textContent = item.badge;

      const lenEl = document.createElement('span');
      lenEl.className = 'text-[11px] text-[var(--muted-foreground)] tabular-nums';
      lenEl.textContent = `${{item.prompt.replace(/\\s+/g, '').length}} 字`;

      left.append(cb, h3, badge, lenEl);

      const copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 transition shrink-0 cursor-pointer';
      copyBtn.textContent = '复制 Prompt';
      copyBtn.addEventListener('click', async () => {{
        try {{
          await navigator.clipboard.writeText(item.prompt);
        }} catch {{
          const ta = document.createElement('textarea');
          ta.value = item.prompt;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }}
        copyBtn.textContent = '已复制 ✓';
        setTimeout(() => {{ copyBtn.textContent = '复制 Prompt'; }}, 1500);
      }});

      header.append(left, copyBtn);

      const meta = document.createElement('div');
      meta.className = 'space-y-1 text-xs text-[var(--muted-foreground)]';
      const d1 = document.createElement('div');
      d1.innerHTML = `<span class="font-semibold text-[var(--foreground)]">${{meta1Label}}：</span>`;
      d1.append(document.createTextNode(item.bind));
      const d2 = document.createElement('div');
      d2.innerHTML = `<span class="font-semibold text-[var(--foreground)]">${{meta2Label}}：</span>`;
      d2.append(document.createTextNode(item.check));
      meta.append(d1, d2);

      const pre = document.createElement('pre');
      pre.className = 'bg-[var(--content)] border border-[var(--border)] rounded-lg p-3 text-xs leading-relaxed whitespace-pre-wrap break-words font-sans select-all text-[var(--foreground)]';
      pre.textContent = item.prompt;

      card.append(header, meta, pre);
      return card;
    }}

    function renderAll() {{
      const onlyAnchors = document.getElementById('only-anchors').checked;
      const vidPanel = document.getElementById('panel-videos');
      const imgPanel = document.getElementById('panel-images');
      vidPanel.innerHTML = '';
      imgPanel.innerHTML = '';

      const vList = onlyAnchors ? DATA.videos.filter(x => x.anchor) : DATA.videos;
      const iList = onlyAnchors ? DATA.images.filter(x => x.anchor) : DATA.images;

      vList.forEach(v => vidPanel.appendChild(createCard(v, '即梦绑定参考', '验收与剪映备注')));
      iList.forEach(i => imgPanel.appendChild(createCard(i, '绑定参考与画幅', '验收要点')));
    }}

    function switchTab(name) {{
      ['videos', 'images'].forEach(t => {{
        document.getElementById(`panel-${{t}}`).classList.toggle('hidden', t !== name);
      }});
      document.querySelectorAll('.tab-btn').forEach(btn => {{
        const active = btn.dataset.tab === name;
        btn.className = `tab-btn px-3.5 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${{
          active
            ? 'bg-[var(--primary)] text-[var(--primary-foreground)]'
            : 'bg-[var(--card)] text-[var(--muted-foreground)] border border-[var(--border)] hover:text-[var(--foreground)]'
        }}`;
      }});
    }}

    document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));
    document.getElementById('only-anchors').addEventListener('change', renderAll);
    document.getElementById('reset-progress').addEventListener('click', () => {{
      doneMap = {{}};
      localStorage.setItem(STORAGE_KEY, JSON.stringify(doneMap));
      renderAll();
      updateProgress();
    }});

    renderAll();
    switchTab('videos');
    updateProgress();
  </script>
</body>
</html>
"""


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compile V3.0 act handbook into zero-drift HTML Copy Workbench.")
    parser.add_argument("--handbook", required=True, help="Path to 03_actXX_handbook.md")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    args = parser.parse_args(argv)

    hb = Path(args.handbook)
    if not hb.is_file():
        print(f"Error: handbook not found: {hb}", file=sys.stderr)
        return 2

    data = parse_handbook(hb)
    html_text = render_html(data)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    print(f"[OK] Built workbench {out} ({len(data['images'])} images + {len(data['videos'])} videos = {len(data['images']) + len(data['videos'])} prompts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
