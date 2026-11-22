#!/usr/bin/env python3
"""Deterministic redline linter for Seedance 2.0 / 2.5 video prompts.

Zero external dependencies (Python 3 stdlib only).
Exit codes:
  0 -> PASS (zero P0 blocking issues; P1 warnings may exist)
  1 -> FAIL (one or more P0 blocking issues detected)
  2 -> Usage / file error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class Issue:
    unit: str
    severity: str  # "P0" | "P1"
    rule_id: str
    message: str
    excerpt: str
    suggestion: str


BANNED_EMOTIONS: List[Tuple[str, str]] = [
    ("彻底崩溃", "改写为眼眶泛红、下颌微颤、呼吸急促与声音哽咽等可见物理微动"),
    ("歇斯底里", "改写为具体发声状态与肩颈紧绷动作，避免夸张扭曲"),
    ("嚎啕大哭", "改写为眼泪滑落、肩头抽动、抬手擦眼等克制物理细节"),
    ("满腹委屈", "改写为眼睑微垂、嘴角轻收、喉结轻咽、视线避开等物理动作"),
    ("悲痛欲绝", "改写为具体肌肉与呼吸变化，禁抽象情绪大词"),
    ("心灰意冷", "改写为笑意平复、闭唇沉默停顿与垂眸动作"),
    ("彻底死心", "改写为嘴角平复、视线移向远方与双肩微沉"),
    ("神情冷漠如水", "改写为面部肌肉放松平直、闭唇沉默、视线平视不动"),
    ("无比宁静", "改写为呼吸舒缓、双肩放松下沉与自然微仰头"),
    ("无比释怀", "改写为双肩松沉、深呼一口气与眼角自然鱼尾纹"),
    ("微微一笑", "改写为“一侧嘴角极轻抬起约两毫米随即收平，紧接下一个动作”"),
    ("极度震惊", "改写为“动作顿住半秒、嘴唇微张无声停住、呼吸停滞一瞬”"),
    ("狂喜", "改写为具体动作与眉眼变化"),
    ("绝望透顶", "改写为肩背塌落、垂眼失焦与缓吐长气"),
    ("气急败坏", "改写为重心前倾、颈侧微绷与具体手部动作"),
    ("暴跳如雷", "改写为具体起身、拍桌或指门等可见肢体链"),
    ("满脸痛苦", "改写为眉心收紧、下唇抿紧与呼吸变化"),
    ("劫后余生", "改写为长舒一口气、肩膀骤松等可见状态"),
    ("充满敬佩", "禁止内心抽象心理词，改为可见眼神与姿态"),
    ("fanatical", "Replace intense abstract emotion with neutral physical cue to avoid glowing eyes"),
    ("extremely shocked", "Replace with physical micro-reaction (hands freeze, breath halts)"),
]

SIMILE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"仿佛|宛如|犹如|恰似|好似"),
    re.compile(r"像[^，。！？\n]{1,12}一样"),
    re.compile(r"如[^，。！？\n]{1,10}般"),
]

PUPIL_COLOR_PATTERN = re.compile(
    r"(?:棕色|蓝色|黑色|灰色|绿色|琥珀色|金色|红色)?(?:瞳孔|虹膜)(?:泛|发|闪|呈|偏|显)?[^\s，。！？\n]{0,4}|"
    r"(?<!无任何)(?<!无)(?<!不)(?:眼部发光|瞳孔发光|双眼发光|眼眸发光)|"
    r"(?<!no )glowing eyes",
    re.IGNORECASE,
)

PRODUCER_LEAK_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\bMASTER-\d+\b"),
    re.compile(r"\bINSERT-\d+\b"),
    re.compile(r"回环复用|后期贴轨|剪映镜像|压屏字幕|建议时长|精剪目标|任务属性|绑定参考"),
]

# Timestamp patterns: [0s-4s], 【0s-3s】, 0s-3s, 0-3s, 0-3秒, [0-3秒] (exclude decimal ranges like 2.5-3秒)
TIMESTAMP_PATTERN = re.compile(
    r"(?:[\[\【]\s*(\d{1,2})\s*(?:s|秒)?\s*[-~～至—–]\s*(\d{1,2})\s*(s|秒)\s*[\]\】]|"
    r"(?<![\d.])(\d{1,2})\s*(?:s|秒)?\s*[-~～至—–]\s*(\d{1,2})\s*(s|秒)(?!\d))"
)

AT_TOKEN_PATTERN = re.compile(r"@([\u4e00-\u9fffA-Za-z0-9_\-]+)")

HIGH_RISK_THREE_VIEW_PATTERN = re.compile(r"@[\u4e00-\u9fffA-Za-z0-9_\-]*三视图")
HIGH_RISK_WHITE_CALM_PATTERN = re.compile(r"#FFFFFF|纯白底|纯白背景|平静头肩|表情网格", re.IGNORECASE)

VISUAL_NEGATIVE_PATTERN = re.compile(
    r"(?:不要|禁止|严禁|绝不|不得|切勿|没有)(?!背景音乐|BGM|bgm|字幕|水印|任何眼部发光|眼部发光|闪烁|对白)[\u4e00-\u9fffA-Za-z0-9]{2,12}|"
    r"\bno\s+(?!subtitles?|bgm|music|background music|watermark|audio|glowing eyes)[a-z][a-z\s-]{2,20}",
    re.IGNORECASE,
)

CHARACTER_PRESENCE_PATTERN = re.compile(r"人物|主角|母亲|父亲|女儿|儿子|丈夫|妻子|男子|女子|老人|面部|侧脸|特写|眼神|肩膀")
LIGHTING_PRESENCE_PATTERN = re.compile(r"光|影|照亮|暗部|吊灯|台灯|吸顶灯|朝阳|日光|天光|路灯|月光|灯|明暗")


@dataclass
class PromptUnit:
    unit_id: str
    declared_assets: List[str]
    body: str


def extract_units(text: str, filename: str) -> List[PromptUnit]:
    """Extract prompt blocks from a handbook markdown file or treat whole text as one unit."""
    units: List[PromptUnit] = []

    # Pattern 1: explicit HTML comment markers <!-- PROMPT_START: U01 --> ... <!-- PROMPT_END -->
    marker_re = re.compile(
        r"<!--\s*PROMPT_START\s*:\s*([^>\s]+)\s*-->(.*?)<!--\s*PROMPT_END\s*-->",
        re.DOTALL,
    )
    matches = list(marker_re.finditer(text))
    if matches:
        for m in matches:
            uid = m.group(1).strip()
            block = m.group(2).strip()
            # Look backward up to 600 chars for a binding header line (**绑定参考...** or 绑定参考：)
            prefix = text[max(0, m.start() - 600) : m.start()]
            declared = _extract_header_bindings(prefix)
            # Strip markdown code fence if wrapped inside marker
            block = _strip_fence(block)
            units.append(PromptUnit(unit_id=uid, declared_assets=declared, body=block))
        return units

    # Pattern 2: fenced blocks labeled ```seedance or ```prompt
    fence_re = re.compile(r"```(?:seedance|prompt)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    fmatches = list(fence_re.finditer(text))
    if fmatches:
        for idx, m in enumerate(fmatches, start=1):
            prefix = text[max(0, m.start() - 600) : m.start()]
            uid = _infer_unit_id(prefix, f"UNIT-{idx:02d}")
            declared = _extract_header_bindings(prefix)
            units.append(PromptUnit(unit_id=uid, declared_assets=declared, body=m.group(1).strip()))
        return units

    # Fallback: treat entire file as one prompt unit
    return [PromptUnit(unit_id=Path(filename).stem, declared_assets=[], body=text.strip())]


def _strip_fence(block: str) -> str:
    m = re.match(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n```$", block.strip(), re.DOTALL)
    return m.group(1).strip() if m else block.strip()


def _infer_unit_id(prefix: str, fallback: str) -> str:
    headings = re.findall(r"^#{2,4}\s+\**([A-Za-z0-9_-]+)", prefix, re.MULTILINE)
    return headings[-1] if headings else fallback


def _extract_header_bindings(prefix: str) -> List[str]:
    # Only scan after the most recent heading to avoid bleeding from previous units
    last_heading = prefix.rfind("\n#")
    scope = prefix[last_heading:] if last_heading != -1 else prefix
    bind_lines = [
        line for line in scope.splitlines()
        if "绑定参考" in line or "绑定资产" in line or "参考素材" in line
    ]
    found: List[str] = []
    for line in bind_lines:
        for tok in AT_TOKEN_PATTERN.findall(line):
            if tok not in found:
                found.append(tok)
    return found


def lint_unit(unit: PromptUnit, model: str) -> List[Issue]:
    issues: List[Issue] = []
    body = unit.body
    uid = unit.unit_id

    # RL-01: Model-specific timestamp validation
    ts_matches = list(TIMESTAMP_PATTERN.finditer(body))
    if model == "2.0":
        for m in ts_matches:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-01",
                    message="Seedance 2.0 不响应精确时间戳，强写易导致画面跳变或异常",
                    excerpt=m.group(0),
                    suggestion="改用「镜头1：」「镜头2：」序号编排，总时长在平台面板选择",
                )
            )
    elif model == "2.5":
        is_edit_or_extend = bool(re.search(r"编辑任务|向后延长|向前延长|延长@视频", body))
        if ts_matches and not is_edit_or_extend:
            intervals = [
                (int(m.group(1) or m.group(4)), int(m.group(2) or m.group(5)), m.group(0))
                for m in ts_matches
            ]
            if intervals[0][0] != 0:
                issues.append(
                    Issue(
                        unit=uid,
                        severity="P0",
                        rule_id="RL-01",
                        message=f"Seedance 2.5 时间线未从 0s 起步（首段起点为 {intervals[0][0]}s）",
                        excerpt=intervals[0][2],
                        suggestion="首段时间戳必须从 0s 开始，确保全时长无空白区",
                    )
                )
            prev_end: Optional[int] = None
            for start, end, raw in intervals:
                if end <= start:
                    issues.append(
                        Issue(
                            unit=uid,
                            severity="P0",
                            rule_id="RL-01",
                            message=f"无效时间戳区间（结束秒 {end} <= 起始秒 {start}）",
                            excerpt=raw,
                            suggestion="修正为递增整数秒区间",
                        )
                    )
                if prev_end is not None and start != prev_end:
                    kind = "断档空白" if start > prev_end else "时间重叠"
                    issues.append(
                        Issue(
                            unit=uid,
                            severity="P0",
                            rule_id="RL-01",
                            message=f"Seedance 2.5 时间线存在{kind}（上段结束 {prev_end}s，本段起始 {start}s）",
                            excerpt=raw,
                            suggestion="确保上一段结束秒 === 下一段起始秒，不重叠不留空",
                        )
                    )
                if end > 30:
                    issues.append(
                        Issue(
                            unit=uid,
                            severity="P0",
                            rule_id="RL-01",
                            message=f"时间戳超出 Seedance 2.5 单次 30s 硬上限（{end}s）",
                            excerpt=raw,
                            suggestion="压缩至 30s 内或拆分为两个独立单元",
                        )
                    )
                prev_end = end

    # RL-02: Banned abstract emotion words
    for word, tip in BANNED_EMOTIONS:
        if re.search(re.escape(word), body, re.IGNORECASE):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-02",
                    message=f"检出禁用抽象情绪大词「{word}」，易引发浮夸 AI 表演或异常反应",
                    excerpt=word,
                    suggestion=tip,
                )
            )

    # RL-03: Similes and pupil/iris color triggers
    for pat in SIMILE_PATTERNS:
        for m in pat.finditer(body):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-03",
                    message="检出比喻污染词，模型易按字面错误生成幻觉画面",
                    excerpt=m.group(0),
                    suggestion="删除比喻，直接写成摄像机可见的物理视觉事实",
                )
            )

    for m in PUPIL_COLOR_PATTERN.finditer(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-03",
                message="检出瞳孔/虹膜颜色或眼部发光触发词，易诱发异常眼神自发光",
                excerpt=m.group(0),
                suggestion="删除瞳孔色彩词，改写为“视线落向XX”",
            )
        )

    # RL-04: Producer metadata leaks
    for pat in PRODUCER_LEAK_PATTERNS:
        for m in pat.finditer(body):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-04",
                    message="制片台账/后期备注词泄漏进纯净视频提示词正文",
                    excerpt=m.group(0),
                    suggestion="彻底移出纯净提交块，仅留在手册的后期备忘栏",
                )
            )

    # RL-05: @Asset binding consistency
    body_tokens = list(dict.fromkeys(AT_TOKEN_PATTERN.findall(body)))
    if unit.declared_assets:
        declared_set = set(unit.declared_assets)
        body_set = set(body_tokens)
        for tok in body_tokens:
            if tok not in declared_set:
                issues.append(
                    Issue(
                        unit=uid,
                        severity="P0",
                        rule_id="RL-05",
                        message=f"正文引用了未在绑定卡声明的资产 @{tok}",
                        excerpt=f"@{tok}",
                        suggestion="补入本单元绑定参考卡，或删去多余引用避免漏传",
                    )
                )
        for tok in unit.declared_assets:
            if tok not in body_set:
                issues.append(
                    Issue(
                        unit=uid,
                        severity="P1",
                        rule_id="RL-05",
                        message=f"绑定卡声明了 @{tok}，但正文未明确引用或指定职责",
                        excerpt=f"@{tok}",
                        suggestion="在正文显式绑定其用途，或移除无需出场的参考图",
                    )
                )

    # RL-06: High-risk asset misuse
    for m in HIGH_RISK_THREE_VIEW_PATTERN.finditer(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-06",
                message="视频提示词直接引用了三视图母档，极易触发多人克隆与画面畸变（ERR-007）",
                excerpt=m.group(0),
                suggestion="替换为中灰底侧光单人图（CHAR-VID）或单人裁切图",
            )
        )

    for m in HIGH_RISK_WHITE_CALM_PATTERN.finditer(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-06",
                message="检出纯白背景/平静头肩照/表情网格关键词，会洗平电影暗调光比或锁死肌肉（ERR-002）",
                excerpt=m.group(0),
                suggestion="改用中灰底侧光单人图 + 光影风格锚，或 S 级剧照首帧驱动",
            )
        )

    # RL-07: Visual negative spam & signal-to-noise length
    neg_matches = list(VISUAL_NEGATIVE_PATTERN.finditer(body))
    if len(neg_matches) > 8:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-07",
                message=f"视觉否定词过多（检出 {len(neg_matches)} 处），会污染模型注意力（官方建议否定词仅用于字幕/音频）",
                excerpt=" / ".join(m.group(0) for m in neg_matches[:5]),
                suggestion="将视觉禁令改写为正向可见状态，仅保留「无背景音乐，无字幕，无水印」",
            )
        )

    char_count = len(re.sub(r"\s+", "", body))
    max_len = 600 if model == "2.0" else 1000
    if char_count < 60:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-07",
                message=f"正文过薄（仅 {char_count} 字），缺少光影、景别与表演物理锚定",
                excerpt=body[:40],
                suggestion="补全核心景别、光照-皮肤交互、物理微动与具体拟音",
            )
        )
    elif char_count > max_len:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-07",
                message=f"正文偏长（{char_count} 字 > {max_len} 字建议上限），过密塞入易致模型乱切或注意力稀释",
                excerpt=f"总字数={char_count}",
                suggestion="删除重复衣物与琐碎枚举，保持高信噪比核心视觉事实",
            )
        )

    # RL-11: Lighting-skin interaction check for character shots
    if CHARACTER_PRESENCE_PATTERN.search(body) and not LIGHTING_PRESENCE_PATTERN.search(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-11",
                message="含人物画面未交代主光源方向与光照落点，易出现“影棚抠图贴片感”",
                excerpt=body[:50],
                suggestion="补写 1 句实用光源方向、受光面与阴影落点描述",
            )
        )

    return issues


def format_markdown(model: str, target: str, units: List[PromptUnit], issues: List[Issue]) -> str:
    p0 = [i for i in issues if i.severity == "P0"]
    p1 = [i for i in issues if i.severity == "P1"]
    verdict = "PASS" if not p0 else f"FAIL（存在 {len(p0)} 项 P0 阻断项，严禁投入即梦生成）"

    lines = [
        f"## 确定性红线扫描报告｜`{target}`｜目标模型：Seedance {model}",
        "",
        f"- **扫描单元数**：{len(units)}（{', '.join(u.unit_id for u in units)}）",
        f"- **机械门禁裁决**：`{verdict}`",
        f"- **统计**：P0 阻断 = {len(p0)}｜P1 告警 = {len(p1)}",
        "",
    ]
    if p0:
        lines.append("### P0 阻断项（必须修正）")
        for idx, item in enumerate(p0, 1):
            lines.append(
                f"{idx}. **[{item.unit}｜{item.rule_id}]** `{item.excerpt}` → {item.message}｜建议：{item.suggestion}"
            )
        lines.append("")
    if p1:
        lines.append("### P1 风险告警（建议优化）")
        for idx, item in enumerate(p1, 1):
            lines.append(
                f"{idx}. **[{item.unit}｜{item.rule_id}]** `{item.excerpt}` → {item.message}｜建议：{item.suggestion}"
            )
        lines.append("")
    if not p0 and not p1:
        lines.append("全部确定性红线检查均已通过，请继续交由独立子 Agent 完成导演/物理语义复核。")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic redline linter for Seedance 2.0/2.5 prompts.")
    parser.add_argument("--model", required=True, choices=["2.0", "2.5"], help="Target Seedance model profile.")
    parser.add_argument("--file", required=True, help="Path to act handbook markdown or raw prompt file.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output structured JSON.")
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    units = extract_units(text, path.name)
    all_issues: List[Issue] = []
    for unit in units:
        all_issues.extend(lint_unit(unit, args.model))

    p0_count = sum(1 for i in all_issues if i.severity == "P0")
    p1_count = sum(1 for i in all_issues if i.severity == "P1")

    if args.as_json:
        payload = {
            "target": str(path),
            "model": args.model,
            "verdict": "PASS" if p0_count == 0 else "FAIL",
            "units_scanned": [u.unit_id for u in units],
            "p0_count": p0_count,
            "p1_count": p1_count,
            "issues": [asdict(i) for i in all_issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(args.model, str(path), units, all_issues))

    return 0 if p0_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
