#!/usr/bin/env python3
"""V3.0 Deterministic Dual-Target Redline Linter (Seedream 5.5 + Seedance 2.5 / 2.0).

Zero external dependencies (Python 3 stdlib only).
Supports:
  - Seedream 5.5 image units (CHAR-*, SHOT-START-*, SHOT-MASTER-*, KEYFRAME-*, SCENE-*, PROP-*, GRID-*)
  - Seedance 2.5 (primary) and 2.0 (fallback) video units
  - Optional cross-file validation against project manifest.json (--manifest)

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
from typing import Any, Dict, List, Optional, Tuple


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
    ("狂热", "改写为自然专注神态（防 Seedance 2.5 瞳孔异常发光）"),
    ("眼里冒火", "改写为眉心紧锁与咬肌绷紧（防 Seedance 2.5 瞳孔发光特效）"),
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
    re.compile(r"\b(?:SEG|EDIT|S0|S1)\b"),
    re.compile(r"(?<![@\w])参考图[0-9](?!至)"),
    re.compile(r"回环复用|后期贴轨|剪映镜像|压屏字幕|建议时长|精剪目标|任务属性|绑定参考"),
]
VIDEO_RAW_TU_PATTERN = re.compile(r"(?<![@\w])图[0-9](?!至)")

# Timestamp patterns: [0s-4s], 【0s-3s】, 0s-3s, 0-3s, 0-3秒, [0-3秒] (exclude decimal ranges like 2.5-3秒)
TIMESTAMP_PATTERN = re.compile(
    r"(?:[\[\【]\s*(\d{1,2})\s*(?:s|秒)?\s*[-~～至—–]\s*(\d{1,2})\s*(s|秒)\s*[\]\】]|"
    r"(?<![\d.])(\d{1,2})\s*(?:s|秒)?\s*[-~～至—–]\s*(\d{1,2})\s*(s|秒)(?!\d))"
)

SHOT_NUMBER_PATTERN = re.compile(r"镜头\s*[1-9]\s*[：:]")
EDIT_OR_EXTEND_PATTERN = re.compile(r"编辑任务|严格编辑|向后延长|向前延长|延长\s*@?视频")
REF_VIDEO_IN_EDIT_PATTERN = re.compile(r"参考\s*@?视频\d*")

AT_TOKEN_PATTERN = re.compile(r"@([\u4e00-\u9fffA-Za-z0-9_\-]+)")
DIALOGUE_BLOCK_PATTERN = re.compile(r"\{([^{}]+)\}")

# Clock-face leaks: 6点 / 8点半 / 9点 / 10点 / 12点 / 8:30 / 10:00 (avoids 9:16, 16:9, 4:3 aspect ratios)
CLOCK_FACE_PATTERN = re.compile(
    r"(?<![0-9:])(?:[1-9]|1[0-2])点(?:半|钟)?(?![0-9])|"
    r"(?<![0-9])(?:[1-9]|1[0-2]):(?:00|30)(?![0-9])"
)

THREE_VIEW_TOKEN_PATTERN = re.compile(r"(?:三视图|CHAR[-_]?BASE|母档)", re.IGNORECASE)
HIGH_RISK_WHITE_CALM_PATTERN = re.compile(r"#FFFFFF|纯白底|纯白背景|平静头肩|表情网格", re.IGNORECASE)
STYLE_ANCHOR_TOKEN_PATTERN = re.compile(r"(?:风格光影锚|风格锚|光影锚|STYLE[-_]?REF)", re.IGNORECASE)
SCENE_TOKEN_PATTERN = re.compile(r"(?:空景|SCENE)", re.IGNORECASE)
CHAR_TOKEN_PATTERN = re.compile(r"(?:设定卡|单人图|面部特写|三视图|CHAR)", re.IGNORECASE)

# Seedream still-image specific redlines
STILL_CAMERA_MOVE_PATTERN = re.compile(r"缓慢推镜|慢推镜|推镜头|拉镜头|环绕拍摄|环绕镜头|跟拍|摇镜|一镜到底|甩镜头")
STILL_BUZZWORD_PATTERN = re.compile(r"\b4K\b|\b8K\b|\b16K\b|ultra\s*detailed|masterpiece|超高清极致细节", re.IGNORECASE)
HEX_COLOR_PATTERN = re.compile(r"#[0-9A-Fa-f]{6}\b")
STILL_VISUAL_NEG_PATTERN = re.compile(
    r"(?:不要|禁止|严禁|绝不|不得|切勿|绝无|不出现|无画|无窗|无电器)"
    r"(?!背景音乐|BGM|bgm|字幕|水印|文字|字|分隔线|杂物|蜡|磨皮)"
)

VIDEO_VISUAL_NEG_PATTERN = re.compile(
    r"(?:不要|禁止|严禁|绝不|不得|切勿|没有)(?!背景音乐|BGM|bgm|字幕|水印|任何眼部发光|眼部发光|闪烁|对白|假笑)[\u4e00-\u9fffA-Za-z0-9]{2,12}|"
    r"\bno\s+(?!subtitles?|bgm|music|background music|watermark|audio|glowing eyes)[a-z][a-z\s-]{2,20}",
    re.IGNORECASE,
)

CHARACTER_PRESENCE_PATTERN = re.compile(r"人物|主角|母亲|父亲|妈妈|爸爸|奶奶|爷爷|姑姑|男孩|女孩|男子|女子|老人|面部|侧脸|特写|肩膀")
# Fixed RL-11: concrete lighting phrases (never single-char 光/影/灯 that falsely match 电影/目光)
LIGHTING_PRESENCE_PATTERN = re.compile(
    r"顶光|侧光|逆光|吊灯|台灯|吸顶灯|日光|天光|窗光|路灯|月光|光照|光源|暖光|冷光|"
    r"照亮|打亮|斜照|勾亮|暗影|阴影|反光|光比|暗部|冷灰影|补光"
)

IMAGE_PREFIXES = ("CHAR-", "SHOT-START-", "SHOT-MASTER-", "KEYFRAME-", "SCENE-", "PROP-", "GRID-", "STYLE-")
KEYFRAME_STILL_PREFIXES = ("SHOT-START-", "SHOT-MASTER-", "KEYFRAME-")

FACELESS_SHOT_PATTERN = re.compile(r"俯拍桌面|高角度俯拍|极近手部特写|纯手部|头肩均处于画幅之外|头部均处于画幅之外|无人物面部|禁止出现人物头部|不出现任何人脸|严禁出现人物面部|不可出现人物面部")
VOICE_ASSET_PATTERN = re.compile(r"(?:干声|VOICE[-_]?REF)", re.IGNORECASE)
SPATIAL_INHERIT_PALETTE_PATTERN = re.compile(r"(?:提供|延续|继承)[^。；\n]{0,28}(?:木纹|材质|光比|门框)")
SPATIAL_LAYOUT_LOCK_PATTERN = re.compile(r"布局|透视|摆位|方位|结构|局部[^。；\n]{0,16}(?:虚化|素墙|餐边柜|桌面)|裁出画外|平桌微仰")
DECIMAL_SEC_PATTERN = re.compile(r"(?<![A-Za-z0-9.])\d+\.\d+\s*(?:s|秒)")
SFX_BLOCK_PATTERN = re.compile(r"<([^<>]+)>")
VIDEO_REDUNDANT_PARAM_PATTERN = re.compile(r"16:9横屏|9:16竖屏|画面流畅无闪烁")


@dataclass
class PromptUnit:
    unit_id: str
    kind: str  # "image" | "video"
    is_keyframe_still: bool
    declared_assets: List[str]
    declared_duration: Optional[int]
    declared_state: Optional[str]
    body: str


def _classify_unit(uid: str) -> Tuple[str, bool]:
    upper = uid.upper()
    if upper.startswith(IMAGE_PREFIXES):
        return "image", upper.startswith(KEYFRAME_STILL_PREFIXES)
    return "video", False


def _strip_fence(block: str) -> str:
    m = re.match(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n```$", block.strip(), re.DOTALL)
    return m.group(1).strip() if m else block.strip()


def _infer_unit_id(prefix: str, fallback: str) -> str:
    headings = re.findall(r"^#{2,4}\s+\**([A-Za-z0-9_-]+)", prefix, re.MULTILINE)
    return headings[-1] if headings else fallback


def _extract_unit_scope(text: str, pos: int) -> str:
    # Look back up to 2000 chars and slice from the nearest markdown heading (fixes 600-char cutoff bug)
    window = text[max(0, pos - 2000) : pos]
    last_heading = window.rfind("\n#")
    if last_heading != -1:
        return window[last_heading + 1 :]
    if window.startswith("#"):
        return window
    return window


def _extract_header_meta(scope: str) -> Tuple[List[str], Optional[int], Optional[str]]:
    declared: List[str] = []
    duration: Optional[int] = None
    state: Optional[str] = None

    lines = scope.splitlines()
    for line in lines:
        if any(k in line for k in ("绑定参考", "绑定资产", "参考素材", "参考图")):
            # Ignore negative parenthetical warnings like （严禁加挂 @主角A单人图）
            cleaned = re.sub(r"[（(][^）)]*(?:严禁|禁止|不挂|切勿)[^）)]*[）)]", "", line)
            for tok in AT_TOKEN_PATTERN.findall(cleaned):
                if tok not in declared:
                    declared.append(tok)
        if duration is None:
            dm = re.search(r"(?:生成|时长)[：:\s`]*(\d{1,2})\s*s", line)
            if dm:
                duration = int(dm.group(1))
        if state is None:
            sm = re.search(r"(?:状态[：:\s`]*|\b)(S[0-9])\b", line)
            if sm:
                state = sm.group(1)

    return declared, duration, state


def extract_units(text: str, filename: str) -> List[PromptUnit]:
    """Extract prompt blocks from a handbook markdown file or treat whole text as one unit."""
    units: List[PromptUnit] = []

    marker_re = re.compile(
        r"<!--\s*PROMPT_START\s*:\s*([^>\s]+)\s*-->(.*?)<!--\s*PROMPT_END\s*-->",
        re.DOTALL,
    )
    matches = list(marker_re.finditer(text))
    if matches:
        for m in matches:
            uid = m.group(1).strip()
            block = _strip_fence(m.group(2).strip())
            scope = _extract_unit_scope(text, m.start())
            declared, duration, state = _extract_header_meta(scope)
            kind, is_kf = _classify_unit(uid)
            units.append(
                PromptUnit(
                    unit_id=uid,
                    kind=kind,
                    is_keyframe_still=is_kf,
                    declared_assets=declared,
                    declared_duration=duration,
                    declared_state=state,
                    body=block,
                )
            )
        return units

    fence_re = re.compile(r"```(?:seedance|prompt)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    fmatches = list(fence_re.finditer(text))
    if fmatches:
        for idx, m in enumerate(fmatches, start=1):
            scope = _extract_unit_scope(text, m.start())
            uid = _infer_unit_id(scope, f"UNIT-{idx:02d}")
            declared, duration, state = _extract_header_meta(scope)
            kind, is_kf = _classify_unit(uid)
            units.append(
                PromptUnit(
                    unit_id=uid,
                    kind=kind,
                    is_keyframe_still=is_kf,
                    declared_assets=declared,
                    declared_duration=duration,
                    declared_state=state,
                    body=m.group(1).strip(),
                )
            )
        return units

    uid = Path(filename).stem
    kind, is_kf = _classify_unit(uid)
    return [
        PromptUnit(
            unit_id=uid,
            kind=kind,
            is_keyframe_still=is_kf,
            declared_assets=[],
            declared_duration=None,
            declared_state=None,
            body=text.strip(),
        )
    ]


def _lint_common(unit: PromptUnit, manifest: Optional[Dict[str, Any]]) -> List[Issue]:
    issues: List[Issue] = []
    body = unit.body
    uid = unit.unit_id
    body_tokens = list(dict.fromkeys(AT_TOKEN_PATTERN.findall(body)))

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

    # RL-04: Producer metadata leaks (strip @asset tokens so @scene_S1 / @图1 don't false-trigger)
    body_no_at = AT_TOKEN_PATTERN.sub("", body)
    for pat in PRODUCER_LEAK_PATTERNS:
        for m in pat.finditer(body_no_at):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-04",
                    message="制片台账/后期备注词或原始图号泄漏进纯净提示词正文",
                    excerpt=m.group(0),
                    suggestion="改用正式 @资产名，并将台账备注移出纯净提交块",
                )
            )

    if unit.kind == "video":
        for m in VIDEO_RAW_TU_PATTERN.finditer(body_no_at):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-04",
                    message="视频纯净正文泄漏未绑定 @ 的裸图号，请改用即梦 @资产名",
                    excerpt=m.group(0),
                    suggestion="改用正式 @资产名（多关键帧序列仅用 @图1 至 @图N）",
                )
            )

    # RL-05: @Asset binding consistency
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

    # RL-26: Clock-face coordinate leaks (strip {dialogue} so characters mentioning time aren't false positives)
    body_visual = DIALOGUE_BLOCK_PATTERN.sub("", body)
    for m in CLOCK_FACE_PATTERN.finditer(body_visual):
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-26",
                message="检出 360° 钟面方位词泄漏进模型 Prompt，易致 3D/2D 错乱或中文时间先验劫持（ERR-022）",
                excerpt=m.group(0),
                suggestion="改用 2D 画面空间四要素与三层朝向锁（如画面左三分之一、身后素净灰墙）",
            )
        )

    # Manifest cross-file checks: RL-19 (asset registry), RL-17 (S0/S1 state), RL-27 (Pink Elephant)
    if manifest:
        assets_map: Dict[str, Any] = manifest.get("assets", {})
        all_tokens = list(dict.fromkeys(list(unit.declared_assets) + body_tokens))
        if assets_map:
            for tok in all_tokens:
                if tok not in assets_map:
                    issues.append(
                        Issue(
                            unit=uid,
                            severity="P0",
                            rule_id="RL-19",
                            message=f"引用的 @{tok} 未在项目 manifest.json 资产账本中注册",
                            excerpt=f"@{tok}",
                            suggestion="先在 manifest.json 与 02_asset_registry.md 注册该资产并核对派生溯源",
                        )
                    )
                else:
                    meta = assets_map[tok]
                    asset_state = meta.get("state") if isinstance(meta, dict) else None
                    # Check S1 unit referencing S0 asset (allow SCENE-S1 editing units that intentionally transform S0 -> S1)
                    is_s1_editor = uid.upper().startswith("SCENE-") and "S1" in uid.upper()
                    effective_state = unit.declared_state or manifest.get("current_state")
                    if effective_state == "S1" and asset_state == "S0" and not is_s1_editor:
                        issues.append(
                            Issue(
                                unit=uid,
                                severity="P0",
                                rule_id="RL-17",
                                message=f"S1 状态单元违规引用了 S0 旧状态资产 @{tok}（ERR-016）",
                                excerpt=f"@{tok}",
                                suggestion="切换为成对局部编辑后的 S1 状态空景或首帧资产",
                            )
                        )

        removed_objects: List[str] = manifest.get("removed_objects", [])
        is_s1_editor = uid.upper().startswith("SCENE-") and "S1" in uid.upper()
        if removed_objects and not is_s1_editor:
            # Strip both @asset tags and {dialogue} lines before scanning visual prose
            body_clean = AT_TOKEN_PATTERN.sub("", body_visual)
            for term in removed_objects:
                if term and term in body_clean:
                    issues.append(
                        Issue(
                            unit=uid,
                            severity="P0",
                            rule_id="RL-27",
                            message=f"检出已移除物体粉红大象触发词「{term}」（ERR-023）",
                            excerpt=term,
                            suggestion="删除已移除物体名称，改写为纯粹正向物理状态（如平整空旷原木桌面）",
                        )
                    )

    return issues


def _lint_image(unit: PromptUnit) -> List[Issue]:
    issues: List[Issue] = []
    body = unit.body
    uid = unit.unit_id
    char_count = len(re.sub(r"\s+", "", body))

    # RL-21: Still camera-move & buzzword bans (all Seedream image prompts)
    for m in STILL_CAMERA_MOVE_PATTERN.finditer(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-21",
                message="静态生图 Prompt 混入视频运镜词，易导致构图畸变",
                excerpt=m.group(0),
                suggestion="删除运镜词，仅保留镜头焦段与静态视角",
            )
        )

    for m in STILL_BUZZWORD_PATTERN.finditer(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-21",
                message="生图 Prompt 含无效画质吹水词，易诱发过度数码锐化与假纹理",
                excerpt=m.group(0),
                suggestion="替换为真实摄影机/胶片颗粒与哑光皮肤肌理描写",
            )
        )

    # Keyframe / Angle Master official Seedream 5.5 gates (<=300 Chinese chars recommended, <=5 guardrails)
    if unit.is_keyframe_still:
        if char_count > 380:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-21",
                    message=f"Seedream 首帧/母帧过长（{char_count} 字 > 380 字，信息易分散漏元素，ERR-024）",
                    excerpt=f"总字数={char_count}",
                    suggestion="拆块精简至官方建议 ≤300 汉字连贯完整短句（用途分工→主体动作→光影融合→护栏）",
                )
            )
        elif char_count > 320:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P1",
                    rule_id="RL-07",
                    message=f"Seedream 首帧/母帧略超官方 300 汉字建议区（{char_count} 字）",
                    excerpt=f"总字数={char_count}",
                    suggestion="精简冗余词或改单轮局部微调，保持高信噪比与连贯完整句子",
                )
            )

        still_negs = list(STILL_VISUAL_NEG_PATTERN.finditer(body))
        if len(still_negs) > 5:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-21",
                    message=f"Seedream 首帧/母帧否定护栏过多（检出 {len(still_negs)} 处 > 5 处上限，ERR-024）",
                    excerpt=" / ".join(m.group(0) for m in still_negs[:6]),
                    suggestion="保持正面写满为主，文末仅留 ≤5 条精准相机/防泄漏护栏",
                )
            )

        # Character-first priority rule: never put empty SCENE at slot #1 alongside characters
        if len(unit.declared_assets) >= 2:
            first_asset = unit.declared_assets[0]
            has_char = any(CHAR_TOKEN_PATTERN.search(a) for a in unit.declared_assets[1:])
            if SCENE_TOKEN_PATTERN.search(first_asset) and has_char:
                issues.append(
                    Issue(
                        unit=uid,
                        severity="P0",
                        rule_id="RL-21",
                        message=f"含人首帧/母帧将无人空景 @{first_asset} 排在第 1 顺位，易复刻空椅构图",
                        excerpt=f"1 @{first_asset}",
                        suggestion="将人物参考图排在前顺位，真实空景退居末位仅借光比与环境材质",
                    )
                )

    # RL-33: Warn against raw hex color codes in still prompts (avoid text-rendering / rigid color artifacts; skip #FFFFFF handled by RL-06)
    for m_hex in HEX_COLOR_PATTERN.finditer(body):
        if m_hex.group(0).upper() == "#FFFFFF":
            continue
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-33",
                message=f"生图正文含十六进制色码 {m_hex.group(0)}，5.5 强文字能力下易渲染错字或色块偏差（ERR-035）",
                excerpt=m_hex.group(0),
                suggestion="改用自然语言色彩描写（如“纯色无纹理的中深冷灰背景”）",
            )
        )

    # RL-32: Spatial layout lock for wide/medium structural stills & CHAR-SHEET seamless margins
    if uid.upper().startswith(("SHOT-START", "KEYFRAME")):
        has_scene_ref = any(
            SCENE_TOKEN_PATTERN.search(a) or "餐厅" in a or "场景" in a
            for a in unit.declared_assets
        )
        m_palette = SPATIAL_INHERIT_PALETTE_PATTERN.search(body)
        if has_scene_ref and m_palette and not SPATIAL_LAYOUT_LOCK_PATTERN.search(body):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P1",
                    rule_id="RL-32",
                    message="空间首帧把 @SCENE 弱化为材质/光比色卡，未显式锁定同房间空间布局与门柜桌椅摆位（ERR-031）",
                    excerpt=m_palette.group(0),
                    suggestion="精简冗余词并改为“继承 @实景空景 同房间空间布局、门柜桌椅摆位与暗暖光比”",
                )
            )

    if uid.upper().startswith("CHAR-") and "双区" in body and "留白" not in body:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-32",
                message="角色设定卡含“双区”且缺左右占比与鞋底留白锁，易诱发分隔线或右图挤压左侧全身（ERR-031）",
                excerpt="双区",
                suggestion="改为“横向无缝并排：左半幅占约40%画宽留足头顶与鞋底纯灰留白，右半幅占约55%画宽无缝融入纯灰背景”",
            )
        )

    return issues


def _lint_video(unit: PromptUnit, model: str) -> List[Issue]:
    issues: List[Issue] = []
    body = unit.body
    uid = unit.unit_id
    body_tokens = list(dict.fromkeys(AT_TOKEN_PATTERN.findall(body)))
    all_assets = list(dict.fromkeys(list(unit.declared_assets) + body_tokens))
    is_edit_or_extend = bool(EDIT_OR_EXTEND_PATTERN.search(body))

    # RL-01: Model-specific timestamp validation (2.0 vs 2.5 strict isolation)
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
        if not ts_matches and not is_edit_or_extend and SHOT_NUMBER_PATTERN.search(body):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-01",
                    message="Seedance 2.5 模式误用了 2.0「镜头1：」语法且缺失整数秒时间戳",
                    excerpt=SHOT_NUMBER_PATTERN.search(body).group(0),  # type: ignore[union-attr]
                    suggestion="改用连续整数秒时间戳（如 [0s-4s] [4s-9s]）精准控拍",
                )
            )
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

        # RL-15: Edit/extend verb check
        if is_edit_or_extend and REF_VIDEO_IN_EDIT_PATTERN.search(body):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P1",
                    rule_id="RL-15",
                    message="编辑/延长任务出现“参考@视频”措辞，易被 2.5 误判为普通全能参考任务",
                    excerpt=REF_VIDEO_IN_EDIT_PATTERN.search(body).group(0),  # type: ignore[union-attr]
                    suggestion="改为直接指代目标视频（如“严格编辑 @视频1”或“向后延长 @视频1”）",
                )
            )

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

    # RL-06: High-risk asset misuse (scan BOTH declared_assets and body!)
    for tok in all_assets:
        if THREE_VIEW_TOKEN_PATTERN.search(tok):
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0" if model == "2.0" else "P1",
                    rule_id="RL-06",
                    message=f"视频单元绑定了老式三视图/母档 @{tok}，易触发人物克隆与畸变（ERR-007）",
                    excerpt=f"@{tok}",
                    suggestion="替换为 V3.1 一卡双区复合角色设定卡（CHAR-SHEET，左全身+右50%+大头）或同源闭唇实景母帧（SHOT-MASTER）",
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
                suggestion="改用 #555A64 侧光一卡双区 CHAR-SHEET 复合设定卡 + 同源闭唇实景母帧驱动",
            )
        )

    # RL-18: V3.0 Total ban on external STYLE-REF entering any video task (ERR-021)
    style_tokens = [tok for tok in all_assets if STYLE_ANCHOR_TOKEN_PATTERN.search(tok)]
    if style_tokens:
        issues.append(
            Issue(
                unit=uid,
                severity="P0",
                rule_id="RL-18",
                message=f"视频任务违规挂载外来风格锚 @{style_tokens[0]}，会导致前后画风突变（ERR-021）",
                excerpt=f"@{style_tokens[0]}",
                suggestion="彻底移除外来风格锚，改由同源实景空景或闭唇实景母帧 SHOT-MASTER 驱动",
            )
        )

    # RL-07: Visual negative spam & signal-to-noise length
    neg_matches = list(VIDEO_VISUAL_NEG_PATTERN.finditer(body))
    if len(neg_matches) > 6:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-07",
                message=f"视觉否定词过多（检出 {len(neg_matches)} 处 > 6 处），易污染注意力",
                excerpt=" / ".join(m.group(0) for m in neg_matches[:5]),
                suggestion="将视觉禁令改写为正向可见状态，仅保留「无背景音乐，无字幕，无水印」",
            )
        )

    char_count = len(re.sub(r"\s+", "", body))
    if model == "2.0":
        max_len = 550
    else:
        max_len = 700 if (unit.declared_duration and unit.declared_duration >= 15) else 550
    if char_count < 60:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-07",
                message=f"正文过薄（仅 {char_count} 字），缺少光影、景别与表演物理锚定",
                excerpt=body[:40],
                suggestion="补全核心景别、光照-皮肤交互、物理后果链与具体拟音",
            )
        )
    elif char_count > max_len:
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-07",
                message=f"正文偏长（{char_count} 字 > {max_len} 字建议上限，官方建议 ≤500 汉字），过密塞入易致注意力稀释",
                excerpt=f"总字数={char_count}",
                suggestion="遵循任务分配法删除图中已锁定静态复述与冗长前置声明，保持高信噪比",
            )
        )

    # RL-11: Lighting-skin interaction check (fixed false-pass bug!)
    if CHARACTER_PRESENCE_PATTERN.search(body) and not LIGHTING_PRESENCE_PATTERN.search(body):
        issues.append(
            Issue(
                unit=uid,
                severity="P1",
                rule_id="RL-11",
                message="含人物画面未交代主光源方向与光照落点，易出现“影棚抠图贴片感”",
                excerpt=body[:50],
                suggestion="补写 1 句实用光源方向、受光面与阴影落点（如暖黄顶光切亮额颊、半颊入暗影）",
            )
        )

    # RL-28: Dialogue pacing density check against declared duration
    dialogues = DIALOGUE_BLOCK_PATTERN.findall(body)
    if dialogues and unit.declared_duration and unit.declared_duration > 0:
        spoken_chars = sum(len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", d)) for d in dialogues)
        rate = spoken_chars / unit.declared_duration
        if rate > 4.8:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P1",
                    rule_id="RL-28",
                    message=f"台词密度偏高（{spoken_chars} 字 / {unit.declared_duration}s = {rate:.1f} 字/秒 > 4.8），易抢拍或口型漂移",
                    excerpt=" / ".join(dialogues[:2]),
                    suggestion="适当延长生成秒数（留出 ~1s 整数气口余量）或精简台词",
                )
            )

    # RL-31: Faceless / overhead POV video units must not bind voice refs or {dialogue} (ERR-033)
    m_faceless = FACELESS_SHOT_PATTERN.search(body)
    if m_faceless:
        voice_toks = [tok for tok in all_assets if VOICE_ASSET_PATTERN.search(tok)]
        if dialogues or voice_toks:
            excerpt = f"@{voice_toks[0]}" if voice_toks else f"{{{dialogues[0]}}}"
            issues.append(
                Issue(
                    unit=uid,
                    severity="P0",
                    rule_id="RL-31",
                    message="无脸镜头视频端违规绑定 @干声 或写入 {台词}，易诱发模型拉远或虚构嘴巴做口型（ERR-033）",
                    excerpt=excerpt,
                    suggestion="走 Route C 后期贴轨：视频 Prompt 删除 @干声 与 {台词}，仅保留动作与物理拟音",
                )
            )

    # RL-34: Official Seedance 2.5 timing, inline single-SFX, and redundant parameter checks (ERR-037)
    if model == "2.5":
        body_visual = DIALOGUE_BLOCK_PATTERN.sub("", body)
        dec_match = DECIMAL_SEC_PATTERN.search(body_visual)
        if dec_match:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P1",
                    rule_id="RL-34",
                    message="Seedance 2.5 以 1 秒整数为基本单位，正文含小数秒微时序易失效或自相矛盾（ERR-037）",
                    excerpt=dec_match.group(0),
                    suggestion="改为整数秒切片或自然节奏描写（如“停顿一拍”“留足一秒静默”）",
                )
            )

        for m_sfx in SFX_BLOCK_PATTERN.finditer(body):
            sfx_text = m_sfx.group(1)
            if sfx_text.count("、") >= 2:
                issues.append(
                    Issue(
                        unit=uid,
                        severity="P1",
                        rule_id="RL-34",
                        message="单个 <音效> 打包了 3 项以上跨时刻/跨切镜音效，易导致声音错位（ERR-037）",
                        excerpt=f"<{sfx_text[:28]}...>" if len(sfx_text) > 28 else f"<{sfx_text}>",
                        suggestion="拆分为单个独立 <音效> 并内嵌到对应动作的时间戳切片中",
                    )
                )

        m_red = VIDEO_REDUNDANT_PARAM_PATTERN.search(body_visual)
        if m_red:
            issues.append(
                Issue(
                    unit=uid,
                    severity="P1",
                    rule_id="RL-34",
                    message=f"视频正文含冗余画幅参数或泛化尾句「{m_red.group(0)}」（ERR-037）",
                    excerpt=m_red.group(0),
                    suggestion="画幅由平台面板指定，删除冗余词并用首尾双写强禁 BGM 枚举替代泛化尾句",
                )
            )

    return issues


def lint_unit(
    unit: PromptUnit, model: str, manifest: Optional[Dict[str, Any]] = None
) -> List[Issue]:
    issues = _lint_common(unit, manifest)
    if unit.kind == "image":
        issues.extend(_lint_image(unit))
    else:
        issues.extend(_lint_video(unit, model))
    return issues


def format_markdown(model: str, target: str, units: List[PromptUnit], issues: List[Issue]) -> str:
    p0 = [i for i in issues if i.severity == "P0"]
    p1 = [i for i in issues if i.severity == "P1"]
    img_count = sum(1 for u in units if u.kind == "image")
    vid_count = sum(1 for u in units if u.kind == "video")
    verdict = "PASS" if not p0 else f"FAIL（存在 {len(p0)} 项 P0 阻断项，严禁投入即梦生成）"

    lines = [
        f"## V3.0 双目标确定性红线扫描报告｜`{target}`｜模型：Seedance {model} + Seedream 5.5",
        "",
        f"- **扫描单元数**：{len(units)}（生图 {img_count} + 视频 {vid_count}：{', '.join(u.unit_id for u in units)}）",
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
        lines.append("全部确定性红线检查（生图 + 视频 + 跨文件）均已通过，请继续交由独立隔离审查子 Agent 完成跨幕与语义盲审。")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="V3.0 deterministic dual-target redline linter for Seedream 5.5 + Seedance 2.5/2.0."
    )
    parser.add_argument("--model", default="2.5", choices=["2.0", "2.5"], help="Target Seedance model (default: 2.5).")
    parser.add_argument("--file", required=True, help="Path to act handbook markdown or raw prompt file.")
    parser.add_argument("--manifest", help="Optional path to project manifest.json for cross-file state/asset checks.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output structured JSON.")
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    manifest: Optional[Dict[str, Any]] = None
    if args.manifest:
        mpath = Path(args.manifest)
        if not mpath.is_file():
            print(f"Error: manifest not found: {mpath}", file=sys.stderr)
            return 2
        try:
            manifest = json.loads(mpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in manifest {mpath}: {exc}", file=sys.stderr)
            return 2

    text = path.read_text(encoding="utf-8")
    units = extract_units(text, path.name)
    all_issues: List[Issue] = []
    for unit in units:
        all_issues.extend(lint_unit(unit, args.model, manifest))

    p0_count = sum(1 for i in all_issues if i.severity == "P0")
    p1_count = sum(1 for i in all_issues if i.severity == "P1")

    if args.as_json:
        payload = {
            "target": str(path),
            "model": args.model,
            "manifest": args.manifest,
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
