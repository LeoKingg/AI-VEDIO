#!/usr/bin/env python3
"""Unit tests for lint_prompt.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_prompt  # noqa: E402


CLEAN_20_PROMPT = """
中国当代现实主义院线电影质感，16:9横屏，ARRI Alexa Mini LF 35mm电影胶片细微颗粒。@客厅餐厅夜景空景 是本场家庭餐厅，仅提供空间布局与光影氛围，不复刻其全景构图；将@母亲单人图 定义为坐在餐桌左侧身穿旧条纹衬衫的母亲（使用@母亲干声 声线）。

镜头1：85mm浅景深面部近景，固定机位。头顶单盏暖黄吊灯照亮母亲额头与颧骨，眼窝沉在自然阴影里，木桌微弱反光映在下颌下方。母亲眼眶泛红蓄泪，下唇抿紧半秒后微微发颤，胸口急促起伏，视线直盯餐桌左侧低声沙哑质问：“凭啥这辈子都得我让着？”说完手指顺势攥住桌沿，饭菜微弱热气缓缓升起，保留一秒沉默喘息。

全程保留老旧吊扇低频底噪、布料轻响与克制哽咽换气声。全程无背景音乐，无字幕，无水印，画面流畅无闪烁。
""".strip()

CLEAN_25_PROMPT = """
【参考绑定】按出场顺序绑定：@图1 为S级餐厅首帧（作为开场首帧，已锁定光影与构图）；@音频1 为母亲参考干声。

【一句话总纲】中国当代现实主义院线电影质感，16:9横屏，ARRI Alexa Mini LF 35mm胶片细微颗粒，夜晚低照度暖黄吊灯下母亲在旧餐桌边沉默转折的一镜到底，画面严格共计2人。

【连续时间线】
[0s-4s] 85mm浅景深侧脸近景，固定机位。头顶低照度暖黄吊灯照亮额头与鼻梁，脸颊背光侧沉入冷灰阴影，下颌承接木桌微弱暖光反射。母亲原本舒展的嘴角一寸寸平复静止，闭唇沉默停顿两秒，视线从对方脸上缓缓移向桌面，碗边极淡热气缓缓升起。
[4s-9s] 极缓微推镜。她喉结轻咽，指尖无意识摩挲瓷杯边缘，深吸半口气后声音极轻地问：“还有别的事吗？”
[9s-11s] 保持固定机位。她垂眼合拢手边旧账本，双肩微微松沉，保留一秒无台词静默余韵。

【一致性与声音收尾】全程保持统一低照度暖黄实用光、细微胶片颗粒与人物骨相一致，眼神自然正常，无任何眼部发光特效。仅保留室内夜间环境底噪与翻页轻响。无背景音乐，无字幕，无水印。
""".strip()


class LintPromptTests(unittest.TestCase):
    def test_clean_20_passes(self) -> None:
        unit = lint_prompt.PromptUnit(
            unit_id="U01",
            declared_assets=["客厅餐厅夜景空景", "母亲单人图", "母亲干声"],
            body=CLEAN_20_PROMPT,
        )
        issues = lint_prompt.lint_unit(unit, "2.0")
        self.assertEqual([], issues, f"Expected clean pass, got: {issues}")

    def test_clean_25_passes(self) -> None:
        unit = lint_prompt.PromptUnit(
            unit_id="U01",
            declared_assets=["图1", "音频1"],
            body=CLEAN_25_PROMPT,
        )
        issues = lint_prompt.lint_unit(unit, "2.5")
        self.assertEqual([], issues, f"Expected clean pass, got: {issues}")

    def test_20_rejects_timestamps(self) -> None:
        unit = lint_prompt.PromptUnit("U01", [], CLEAN_25_PROMPT)
        issues = lint_prompt.lint_unit(unit, "2.0")
        rule_ids = {i.rule_id for i in issues if i.severity == "P0"}
        self.assertIn("RL-01", rule_ids)

    def test_25_rejects_timeline_gap_and_over_30s(self) -> None:
        bad = (
            "中国当代现实主义电影，头顶暖黄吊灯光照亮人物面部。\n"
            "[0s-4s] 镜头一人物抬眼。\n"
            "[6s-32s] 镜头二人物起身离席。无字幕，无背景音乐。"
        )
        issues = lint_prompt.lint_unit(lint_prompt.PromptUnit("U02", [], bad), "2.5")
        p0_msgs = [i.message for i in issues if i.severity == "P0" and i.rule_id == "RL-01"]
        self.assertTrue(any("断档空白" in m for m in p0_msgs))
        self.assertTrue(any("30s" in m for m in p0_msgs))

    def test_rejects_abstract_emotion_simile_pupil_and_leaks(self) -> None:
        bad = (
            "中国当代现实主义电影，MASTER-01 回环复用，暖黄灯光照亮人物面部。"
            "母亲彻底崩溃，仿佛天塌下来，棕色瞳孔闪动，微微一笑后离席。无字幕，无背景音乐。"
        )
        issues = lint_prompt.lint_unit(lint_prompt.PromptUnit("U03", [], bad), "2.0")
        p0_rules = {i.rule_id for i in issues if i.severity == "P0"}
        self.assertTrue({"RL-02", "RL-03", "RL-04"}.issubset(p0_rules))

    def test_rejects_three_view_white_bg_and_unbound_asset(self) -> None:
        bad = (
            "中国当代现实主义电影，纯白背景#FFFFFF，头顶暖黄吊灯光照亮面部。"
            "使用@母亲三视图 和 @未声明道具 在客厅对峙，动作自然连贯。无字幕，无背景音乐。"
        )
        unit = lint_prompt.PromptUnit("U04", declared_assets=["母亲三视图"], body=bad)
        issues = lint_prompt.lint_unit(unit, "2.0")
        p0_rules = {i.rule_id for i in issues if i.severity == "P0"}
        self.assertIn("RL-05", p0_rules)
        self.assertIn("RL-06", p0_rules)

    def test_handbook_extraction_with_markers(self) -> None:
        handbook = (
            "## U01｜测试单元\n"
            "- **绑定参考**：`@客厅餐厅夜景空景`、`@母亲单人图`、`@母亲干声`\n\n"
            "<!-- PROMPT_START: U01 -->\n"
            "```seedance\n"
            f"{CLEAN_20_PROMPT}\n"
            "```\n"
            "<!-- PROMPT_END -->\n"
        )
        units = lint_prompt.extract_units(handbook, "act1.md")
        self.assertEqual(1, len(units))
        self.assertEqual("U01", units[0].unit_id)
        self.assertEqual(["客厅餐厅夜景空景", "母亲单人图", "母亲干声"], units[0].declared_assets)
        self.assertEqual([], lint_prompt.lint_unit(units[0], "2.0"))

    def test_no_false_positives_on_decimals_and_normal_wu_words(self) -> None:
        text = (
            "中国当代现实主义电影，16:9横屏，头顶暖黄吊灯照亮人物侧脸。"
            "镜头1：固定机位，母亲无声停顿约1.5秒，手指无意识摩挲杯沿，望向窗外无垠夜色，"
            "嘴角平复，保留约0.8秒沉默余韵。无背景音乐，无字幕，无水印。"
        )
        issues = lint_prompt.lint_unit(lint_prompt.PromptUnit("U05", [], text), "2.0")
        self.assertEqual([], issues, f"Unexpected false positives: {issues}")

    def test_rejects_redundant_style_anchor_with_scene_or_start_frame(self) -> None:
        bad = (
            "中国当代现实主义电影，16:9横屏，头顶暖黄吊灯照亮父亲侧脸。"
            "延续@风格光影锚_餐厅夜 与@餐厅夜景空景，将@爸爸单人图 定义为父亲。"
            "无背景音乐，无字幕，无水印。"
        )
        unit = lint_prompt.PromptUnit(
            "U01B",
            declared_assets=["风格光影锚_餐厅夜", "餐厅夜景空景", "爸爸单人图"],
            body=bad,
        )
        issues = lint_prompt.lint_unit(unit, "2.0")
        p0_rules = {i.rule_id for i in issues if i.severity == "P0"}
        self.assertIn("RL-18", p0_rules)


if __name__ == "__main__":
    unittest.main()
