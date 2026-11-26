#!/usr/bin/env python3
"""Comprehensive unit tests for V3.0 dual-target lint_prompt.py."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import lint_prompt as lp  # noqa: E402


def _make_video(uid: str, body: str, declared=None, duration=None, state=None) -> lp.PromptUnit:
    return lp.PromptUnit(
        unit_id=uid,
        kind="video",
        is_keyframe_still=False,
        declared_assets=declared or [],
        declared_duration=duration,
        declared_state=state,
        body=body,
    )


def _make_image(uid: str, body: str, declared=None, state=None, is_kf=True) -> lp.PromptUnit:
    return lp.PromptUnit(
        unit_id=uid,
        kind="image",
        is_keyframe_still=is_kf,
        declared_assets=declared or [],
        declared_duration=None,
        declared_state=state,
        body=body,
    )


class TestLintPromptV3(unittest.TestCase):
    def test_clean_seedance_25_multishot_passes(self):
        unit = _make_video(
            "U01",
            "@场景空景 锁定暗暖餐厅空间；将 @爸爸单人图 定义为爸爸（音色使用 @爸爸干声 低沉严厉男声）。\n"
            "[0s-4s] 50mm中近景固定机位，上方暖黄吊灯照亮额颊，半颊沉入冷灰暗影。爸爸坐居画面左三分之一，侧身向右拍桌震响瓷碗，喝道：{把碗放下！}\n"
            "[4s-8s] 硬切85mm近景，男孩居右三分之一，三分之二侧脸朝左咬紧下颌，回道：{凭什么！}尾留一秒沉默。\n"
            "全程保留<拍桌木响与室内底噪>。全程无背景音乐，无字幕，无水印。",
            declared=["场景空景", "爸爸单人图", "爸爸干声"],
            duration=8,
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertEqual([], issues)

    def test_clean_seedance_20_passes(self):
        unit = _make_video(
            "U01",
            "@U01首帧 为首帧起点，参考 @爸爸单人图 保持相貌衣着，音色紧锁 @爸爸干声。\n"
            "镜头1：50mm中近景固定机位，上方暖黄吊灯照亮额颊，半颊沉入暗影。男人坐居画面左侧，右手拍桌震响瓷碗喝道：{坐下！}\n"
            "全程保留<拍桌木响与底噪>。全程无背景音乐，无字幕，无水印。",
            declared=["U01首帧", "爸爸单人图", "爸爸干声"],
            duration=5,
        )
        issues = lp.lint_unit(unit, "2.0")
        self.assertEqual([], issues)

    def test_rl01_20_rejects_timestamps(self):
        unit = _make_video(
            "U01",
            "[0s-4s] 50mm近景固定机位，上方暖黄吊灯照亮侧脸，男子低头沉默不语，留一秒余韵。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.0")
        self.assertTrue(any(i.rule_id == "RL-01" and i.severity == "P0" for i in issues))

    def test_rl01_25_rejects_shot_syntax_without_timestamps(self):
        unit = _make_video(
            "U01",
            "镜头1：50mm近景固定机位，上方暖黄吊灯照亮侧脸，男子坐居左侧低头沉默。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-01" and i.severity == "P0" for i in issues))

    def test_rl01_25_rejects_gap_and_over_30s(self):
        unit = _make_video(
            "U01",
            "[0s-5s] 上方暖黄吊灯照亮男人侧脸。[7s-32s] 男子低头沉默，保留室内底噪。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.5")
        rl01 = [i for i in issues if i.rule_id == "RL-01" and i.severity == "P0"]
        self.assertGreaterEqual(len(rl01), 2)

    def test_rl02_rejects_abstract_emotions_and_glowing_triggers(self):
        unit = _make_video(
            "U01",
            "[0s-4s] 上方暖黄吊灯照亮男人，他彻底崩溃且眼里冒火地盯着前方。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.5")
        rl02 = [i for i in issues if i.rule_id == "RL-02" and i.severity == "P0"]
        self.assertGreaterEqual(len(rl02), 2)

    def test_rl03_rejects_similes_and_pupil_color(self):
        unit = _make_video(
            "U01",
            "[0s-4s] 上方暖黄吊灯照亮侧脸，眼神宛如寒冰，琥珀色瞳孔微缩。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.5")
        rl03 = [i for i in issues if i.rule_id == "RL-03" and i.severity == "P0"]
        self.assertGreaterEqual(len(rl03), 2)

    def test_rl04_rejects_producer_and_raw_ref_leaks(self):
        unit = _make_video(
            "U01",
            "[0s-4s] 上方暖黄吊灯照亮侧脸，参考图1人物在 MASTER-01 的 S1 阶段做后期贴轨处理。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.5")
        rl04 = [i for i in issues if i.rule_id == "RL-04" and i.severity == "P0"]
        self.assertGreaterEqual(len(rl04), 4)

    def test_rl04_allows_at_tu_keyframes_and_state_named_assets(self):
        unit = _make_video(
            "U01",
            "按顺序将 @图1 至 @图4 作为关键帧，场景光比沿用 @主场景_S1 。\n"
            "[0s-5s] 50mm中近景固定机位，头顶暖黄吊灯切亮主角额颊，半颊沉入暗影，角色低头沉默留白一秒。全程无背景音乐，无字幕，无水印。",
            declared=["图1", "图4", "主场景_S1"],
            duration=5,
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertEqual([], issues)

    def test_rl05_detects_undeclared_and_unused_assets(self):
        unit = _make_video(
            "U01",
            "[0s-4s] @未声明图 为首帧起点，上方暖黄吊灯照亮男人侧脸，沉默一秒。全程无背景音乐，无字幕，无水印。",
            declared=["已声明未用图"],
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-05" and i.severity == "P0" for i in issues))
        self.assertTrue(any(i.rule_id == "RL-05" and i.severity == "P1" for i in issues))

    def test_rl06_scans_declared_header_for_three_view(self):
        unit = _make_video(
            "U01",
            "镜头1：上方暖黄吊灯照亮男子额颊，沉默坐定留一秒余韵。全程无背景音乐，无字幕，无水印。",
            declared=["主角三视图母档"],
        )
        issues_20 = lp.lint_unit(unit, "2.0")
        issues_25 = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-06" and i.severity == "P0" for i in issues_20))
        self.assertTrue(any(i.rule_id == "RL-06" and i.severity == "P1" for i in issues_25))

    def test_rl11_bugfix_does_not_false_pass_on_dianying_or_muguang(self):
        unit = _make_video(
            "U01",
            "[0s-4s] 院线电影质感，85mm近景固定机位，男子居左三分之一，目光平静看向右侧，沉默两秒不语。全程无背景音乐，无字幕，无水印。",
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-11" and i.severity == "P1" for i in issues))

    def test_rl15_edit_task_warns_on_reference_video_phrasing(self):
        unit = _make_video(
            "E01",
            "编辑任务：参考 @视频1 将第3秒右侧背景替换为素净暗灰墙，上方暖黄顶光保持一致。全程无背景音乐，无字幕，无水印。",
            declared=["视频1"],
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-15" and i.severity == "P1" for i in issues))

    def test_rl18_bans_foreign_style_anchor_in_video(self):
        unit = _make_video(
            "U01",
            "[0s-4s] 参考 @主角A单人图 与 @风格光影锚_夜 ，上方暖黄吊灯照亮侧脸。全程无背景音乐，无字幕，无水印。",
            declared=["主角A单人图", "风格光影锚_夜"],
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-18" and i.severity == "P0" for i in issues))

    def test_rl21_seedream_length_negatives_camera_buzzwords_and_order(self):
        long_bad = (
            "16:9横屏，8K超高清极致细节，缓慢推镜拍向主角。绝不复刻空椅，严禁出现冰箱，绝无多余人物。"
            + "暖黄顶光切亮额颊与桌面，" * 26
            + "无字无水印。"
        )
        unit = _make_image(
            "SHOT-START-M01",
            long_bad,
            declared=["主场景空景", "主角A单人图"],
            is_kf=True,
        )
        issues = lp.lint_unit(unit, "2.5")
        rl21_msgs = [i.message for i in issues if i.rule_id == "RL-21" and i.severity == "P0"]
        self.assertTrue(any("运镜词" in m for m in rl21_msgs))
        self.assertTrue(any("吹水词" in m for m in rl21_msgs))
        self.assertTrue(any("超长" in m for m in rl21_msgs))
        self.assertTrue(any("视觉否定词" in m for m in rl21_msgs))
        self.assertTrue(any("第 1 顺位" in m for m in rl21_msgs))

    def test_rl21_clean_seedream_master_passes(self):
        body = (
            "16:9横屏，中国当代现实主义85mm平视单人近景剧照。"
            "@主角A单人图 提供38岁男性相貌与深灰夹克， @主场景_空桌心 提供同房间暗暖光比与素净冷暗米灰墙面。"
            "男性坐居画面左侧三分之一，右侧留暗部空间；躯干微侧朝右、三分之二侧脸朝右直盯画外右侧，双唇自然轻闭蓄势，右手轻搭桌沿。"
            "暖黄顶光切亮额颊，暗侧冷灰，胶片质感，无字无水印。"
        )
        unit = _make_image("SHOT-MASTER-R02", body, declared=["主角A单人图", "主场景_空桌心"], is_kf=True)
        issues = lp.lint_unit(unit, "2.5")
        self.assertEqual([], issues)

    def test_rl26_blocks_clock_face_but_allows_aspect_ratios_and_dialogue_time(self):
        bad = _make_image(
            "SHOT-MASTER-R01",
            "16:9横屏， @主角A单人图 站在3:30位置，背靠9点素净灰墙，看向8点半方向，无字无水印。",
            declared=["主角A单人图"],
            is_kf=True,
        )
        bad_issues = lp.lint_unit(bad, "2.5")
        rl26 = [i for i in bad_issues if i.rule_id == "RL-26" and i.severity == "P0"]
        self.assertEqual(len(rl26), 3)

        good = _make_video(
            "U02",
            "[0s-5s] 9:16竖屏，上方暖黄吊灯照亮男子额颊，他轻声说：{晚上8点半记得回家。}说完垂眸停顿一秒。全程无背景音乐，无字幕，无水印。",
            duration=5,
        )
        good_issues = lp.lint_unit(good, "2.5")
        self.assertFalse(any(i.rule_id == "RL-26" for i in good_issues))

    def test_rl27_rl17_rl19_manifest_cross_checks(self):
        manifest = {
            "current_state": "S1",
            "removed_objects": ["旧铁壶", "壶位"],
            "assets": {
                "主场景_初始态": {"state": "S0"},
                "主场景_空桌心": {"state": "S1"},
                "主角A单人图": {"state": "ANY"},
            },
        }
        unit = _make_image(
            "SHOT-START-M02",
            "16:9横屏， @主角A单人图 坐居左侧， @主场景_初始态 提供桌面与中央空壶位， @漏登记图 辅助参考，暖黄顶光，无字无水印。",
            declared=["主角A单人图", "主场景_初始态", "漏登记图"],
            state="S1",
            is_kf=True,
        )
        issues = lp.lint_unit(unit, "2.5", manifest=manifest)
        rules = {i.rule_id for i in issues if i.severity == "P0"}
        self.assertIn("RL-17", rules)
        self.assertIn("RL-19", rules)
        self.assertIn("RL-27", rules)

    def test_rl27_ignores_dialogue_mentions_of_removed_object(self):
        manifest = {
            "current_state": "S1",
            "removed_objects": ["旧铁壶"],
            "assets": {"M01首帧": {"state": "S1"}},
        }
        unit = _make_video(
            "U01",
            "[0s-5s] @M01首帧 为首帧起点，上方暖黄吊灯照亮男子额颊，他低声问：{那把旧铁壶你收哪儿去了？}尾留一秒。全程无背景音乐，无字幕，无水印。",
            declared=["M01首帧"],
            duration=5,
            state="S1",
        )
        issues = lp.lint_unit(unit, "2.5", manifest=manifest)
        self.assertEqual([], issues)

    def test_rl28_flags_overloaded_dialogue_pacing(self):
        unit = _make_video(
            "U03",
            "[0s-4s] 上方暖黄吊灯照亮男子侧脸，他急促连续说道：{你今天到底为什么要把这件事情闹到全家人都不愉快而且还不给所有人留半点余地呢？}全程无背景音乐，无字幕，无水印。",
            duration=4,
        )
        issues = lp.lint_unit(unit, "2.5")
        self.assertTrue(any(i.rule_id == "RL-28" and i.severity == "P1" for i in issues))

    def test_extract_units_ignores_parenthetical_warning_and_long_header(self):
        filler = "这是一段超过七百字的导演备忘。" * 60
        md = (
            "### M01｜测试单元（状态：`S1`｜时长：`5s`）\n"
            f"- **说明**：{filler}\n"
            "- **绑定参考**：1 `@M01首帧` + 2 `@主角A单人图`（严禁加挂 `@主角B单人图`）\n"
            "<!-- PROMPT_START: M01 -->\n"
            "```text\n"
            "[0s-5s] @M01首帧 为首帧起点，参考 @主角A单人图 ，上方暖黄吊灯照亮侧脸，沉默两秒。全程无背景音乐，无字幕，无水印。\n"
            "```\n"
            "<!-- PROMPT_END -->\n"
        )
        units = lp.extract_units(md, "handbook.md")
        self.assertEqual(len(units), 1)
        u = units[0]
        self.assertEqual(u.declared_assets, ["M01首帧", "主角A单人图"])
        self.assertEqual(u.declared_duration, 5)
        self.assertEqual(u.declared_state, "S1")
        self.assertEqual([], lp.lint_unit(u, "2.5"))

    def test_v31_char_sheet_image_and_video_pass(self):
        img_unit = _make_image(
            "CHAR-SHEET-R01",
            "复合角色设定卡，纯色中深冷灰#555A64无缝影棚背景，30度暖色侧光。画幅左半幅为三十岁中国男子正面全身站立略微侧身，穿深蓝夹克与黑裤皮鞋；画幅右半幅占过半面积为同一人物高清纯头部特写，嘴唇平直轻闭。画面内无文字，无分隔线。",
            is_kf=False,
        )
        self.assertEqual([], lp.lint_unit(img_unit, "2.5"))

        vid_unit = _make_video(
            "M01",
            "@M01母帧 为首帧起点；@主角A设定卡（左全身+右半幅高清面部特征）锁死主角体貌与皱纹细节，成片中仅有此一位主角，音色紧锁 @主角A干声。\n"
            "[0s-5s] 85mm特写固定机位，上方暖黄吊灯照亮额颊，半颊沉入暗影。主角居画面左三分之一垂眸沉默一秒后抬头低语：{我没事。}尾留一秒沉默。\n"
            "全程保留<室内底噪>。全程无背景音乐，无字幕，无水印。",
            declared=["M01母帧", "主角A设定卡", "主角A干声"],
            duration=5,
            state="S1",
        )
        self.assertEqual([], lp.lint_unit(vid_unit, "2.5"))


if __name__ == "__main__":
    unittest.main()
