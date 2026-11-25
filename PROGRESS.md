# AI-VEDIO 项目进度与里程碑总账（`PROGRESS.md`）

> **定位**：本仓库跨对话、跨阶段的**持久化里程碑与活跃剧目进度台账**。
> **规范去重声明（V3.0 铁律）**：本文件**只记录里程碑、实战进度与后续计划，不再承载任何规范细则**；所有通用制片规范统一以 `docs/`、`presets/` 与 `skills/` 为唯一事实来源（SSOT）。
> **最后更新**：2026-11-25

---

## 一、系统演进里程碑总览

| 阶段 | 内容 | 当前状态 | 关键提交 / 说明 |
| :---: | :--- | :---: | :--- |
| **Phase 1** | 搭建 V2.0 三层架构、`docs/`、4 大初代 Skills、`lint_prompt.py` 与 `_template` | `已完成` | `a1e7eca` |
| **Phase 2A** | Pilot 剧目《今天谁过生日》（`mama-birthday`）**第一幕**全套资产、Prompt 与 12 条成片验收 | `主流程已跑通` | `10/12` 可用/微裁可用；待补 `U03B` 重抽与终剪回填 |
| **Phase 2B** | 《今天谁过生日》**第二幕**试水并演进至 V2.4 闭唇实景母帧方案（24 块 Prompt + 零失步工作台） | `已完成（V2.x 基线封存）` | `7351f72`（保留作 V2.x 历史基线对照，不覆盖） |
| **Phase 3** | **V3.0 工业化制片系统重构**：`Seedance 2.5` 主力切换 + `STUDIO_CONSTITUTION` + `SOP_V3.0` + 4 个可插拔 `presets/` + **7 个专家 Skills** + 双目标跨文件 `lint_prompt.py` + `build_workbench.py` + `init_project.py` + **7 Skills 全局注册** | `已完成（已推送 origin/main）` | V2.4 全部实战经验与官方 2.5 机制已 100% 正式合入 `docs/` & `skills/` |
| **Phase 4** | **V3.0 首次七大专家实战验证（Option A2）**：用 3 波次 7-Agent 流水线 + `Seedance 2.5` 完成《今天谁过生日》**第二幕 `SEQ-Multi` A/B 重构**（`03_act02_v3_seedance25_handbook.md` + `manifest.json` + 交互工作台） | `双审 PASS（待 480p 首轮 3 锚点实测）` | 11 镜/10 缝压缩至 6 单元/5 缝；18 张 V2.4 静帧 100% 零浪费复用 |

---

## 二、V2.4 历史实战经验合入结项清单（已全部清账入库 V3.0）

- [x] **第 0.5 步《剧情与改编讨论分镜表》**：已正式合入 `docs/SOP_V3.0.md`、`skills/director-showrunner/` 与 `projects/_template/00_project_brief.md`。
- [x] **五模式生成路由（告别单镜拼接）与 `Seedance 2.5` 主力化**：已正式合入 `docs/SOP_V3.0.md`、`skills/seedance-compiler/references/profile-seedance-2.5.md`（保留 `profile-seedance-2.0.md` 降级兼容）。
- [x] **彻底禁绝外来 `STYLE-REF` 进视频 + `SHOT-MASTER` 闭唇实景母帧 + `CHAR-FACE 70%` 双锚 + 30 天写实人脸信任窗**：已合入 `docs/VISUAL_BIBLE_GUIDE.md`、`skills/art-asset-pipeline/` 与 `lint_prompt.py`（`RL-18` P0 拦截）。
- [x] **防空椅穿帮 / 视锥邻座守恒 / 反粉红大象 / 双层坐标系分离（360°→2D） / 身体-头部-视线三层锁**：已合入 `docs/CINEMATOGRAPHY_AND_TRANSITIONS.md`、`skills/cinematography-blocking/`、`manifest.json` 与 `lint_prompt.py`（`RL-26 / RL-27` P0 拦截）。
- [x] **Seedream 5.5 极简正向规范（`≤260/280` 字、零图文对抗、否定词 `≤1`、人物先于空景）**：已合入 `skills/art-asset-pipeline/` 与 `lint_prompt.py`（`RL-21` P0 拦截）。
- [x] **官方声音四分隔符 `{台词}` `<音效>` `(音乐)` `【字幕】`、防老年数字人三铁律、全身动力学微动链、情绪极性双锚与跨幕边界交接卡**：已合入 `skills/performance-sound-director/`、`skills/redline-auditor/` 与 `projects/_template/03_act_handbook_template.md`。
- [x] **480p 试样→1080p 精修 + 2-Strike 止损律 + 7 维质检卡 + L1–L4 救片树 + 五步院线化 Finishing（-14 LUFS 四轨混音、前切 6 帧后切 1 帧、`0.15s` 淡出、色彩匹配先于 LUT）**：已合入 `docs/STUDIO_CONSTITUTION.md`、`docs/POST_JIANYING_GUIDE.md` 与 `skills/post-qa-finishing/`。
- [x] **全套 7 个 V3.0 Skills 全局注册（`save_skill`）**：已完成注册与验证。
- [x] **推送至 GitHub 远端（`origin/main`）**：已推送至 `origin/main`（后续本地新提交按需同步推送）。

---

## 三、活跃剧目进度：《今天谁过生日》（`projects/mama-birthday/`）

### 第一幕（V2.0 样板闭环收尾中）
- [x] 全套资产与 12 条成片人工验收完成（7 条直接可用 + 3 条剪映微裁可用；`U03B` 必重抽、`U02B-1` 建议局部编辑/重抽）。
- [ ] 待收齐 `U03B`（及 `U02B-1` `E-Edit` 修复）成片后，按 V3.0 7 维台账回填 `05_test_log.md` 与 `04_post_jianying_memo.md`。

### 第二幕（V2.4 基线封存 + V3.0 `Seedance 2.5` A/B 重构就绪）
- [x] V2.4 基线 [03_act02_handbook.md](projects/mama-birthday/03_act02_handbook.md)（24 块 Prompt）保留封存（`7351f72`）。
- [x] **V3.0 A2 重构版 [03_act02_v3_seedance25_handbook.md](projects/mama-birthday/03_act02_v3_seedance25_handbook.md)** + [`manifest.json`](projects/mama-birthday/manifest.json) 已跑通三波次 7-Agent 协同与双审 `PASS`（8 单元 `P0=0, P1=0`）。
- [ ] **下一步实测**：跑 Pre-Vis → 先用 **`480p`** 实测 3 个锚点单元（`M2V3-01` / `M2V3-03` / `M2V3-06`），由站 7 `post-qa-finishing` 执行 7 维质检后转 `1080p` 与全量生成。

### 第三幕 ～ 第五幕（全面切换 V3.0 七大专家 + `Seedance 2.5` 生产）
- [ ] **第三幕**（独立厨房停火解围裙 → 餐厅反问）：先由 `director-showrunner` 产出第 0.5 步剧情讨论表并拍板，再跑 3 波次流水线。
- [ ] **第四幕**（牵手甩开 → 玄关暖壁灯侧逆光离场）
- [ ] **第五幕**（方桌冷场 → 纯冷蓝厨房孤锅空镜 → 尾板金句）
