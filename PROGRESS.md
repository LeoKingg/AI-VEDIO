# AI-VEDIO 项目进度与里程碑总账（`PROGRESS.md`）

> **定位**：本仓库跨对话、跨阶段的**持久化里程碑与活跃剧目进度台账**。
> **规范去重声明（V3.0 铁律）**：本文件**只记录里程碑、实战进度与后续计划，不再承载任何规范细则**；所有通用制片规范统一以 `docs/`、`presets/` 与 `skills/` 为唯一事实来源（SSOT）。
> **最后更新**：2026-11-26

---

## 一、系统演进里程碑总览

| 阶段 | 内容 | 当前状态 | 关键提交 / 说明 |
| :---: | :--- | :---: | :--- |
| **Phase 1** | 搭建 V2.0 三层架构、`docs/`、4 大初代 Skills、`lint_prompt.py` 与 `_template` | `已完成` | `a1e7eca` |
| **Phase 2A** | Pilot 剧目《今天谁过生日》（`mama-birthday`）**第一幕**全套资产、Prompt 与 12 条成片验收 | `已封存对照` | `10/12` 可用/微裁可用；保留作 V2.0 历史对照 |
| **Phase 2B** | 《今天谁过生日》**第二幕**试水并演进至 V2.4 闭唇实景母帧方案（24 块 Prompt + 零失步工作台） | `已封存对照` | `7351f72`（保留作 V2.x 历史基线对照，不覆盖） |
| **Phase 3** | **V3.0 工业化制片系统重构**：`Seedance 2.5` 主力切换 + `STUDIO_CONSTITUTION` + `SOP_V3.0` + 4 个可插拔 `presets/` + **7 个专家 Skills** + 双目标跨文件 `lint_prompt.py` + `build_workbench.py` + `init_project.py` + **7 Skills 全局注册** | `已完成（已推送 origin/main）` | V2.4 全部实战经验与官方 2.5 机制已 100% 正式合入 `docs/` & `skills/` |
| **Phase 4** | **V3.0 首次七大专家实战验证（Option A2）**：用 3 波次 7-Agent 流水线 + `Seedance 2.5` 完成 `mama-birthday` **第二幕 `SEQ-Multi` 重构** | `已封存对照` | 验证 5 模路由可行后，启动 `mama-birthday-v3` 从零重制 |
| **Phase 5** | **V3.1 `CHAR-SHEET` 一卡双区资产瘦身 + `SCENE-LAYOUT` 空间线稿前置 + `mama-birthday-v3` 第一幕从零开机**：合入 `ERR-029`（禁代写）与 `ERR-030`（单卡双区淘汰三锚）；5 角色 15 张图压缩为 `5` 张 `CHAR-SHEET`（偏重方案 A），复杂非对称空景补 `SCENE-LAYOUT-01` 线稿骨架，第一幕 **31 单元（23 生图 + 8 视频）** 全数双审 `PASS` 并编译工作台 | `双审 PASS（待首轮 19 图 + 6 视频实测）` | `e983d02` / `e378e13` → `SCENE-LAYOUT-01` 增补待提交 |

---

## 二、V2.4 / V3.1 实战经验合入结项清单（已全部清账入库）

- [x] **第 0.5 步《剧情与改编讨论分镜表》**：已正式合入 `docs/SOP_V3.0.md`、`skills/director-showrunner/` 与 `projects/_template/00_project_brief.md`。
- [x] **五模式生成路由（告别单镜拼接）与 `Seedance 2.5` 主力化**：已正式合入 `docs/SOP_V3.0.md`、`skills/seedance-compiler/references/profile-seedance-2.5.md`（保留 `profile-seedance-2.0.md` 降级兼容）。
- [x] **彻底禁绝外来 `STYLE-REF` 进视频 + `SHOT-MASTER` 闭唇实景母帧 + V3.1 `CHAR-SHEET` 一卡双区（1 人 1 张淘汰三连跳）+ `SCENE-LAYOUT` 非对称空景线稿骨架 + 30 天写实人脸信任窗**：已合入 `docs/VISUAL_BIBLE_GUIDE.md`、`skills/art-asset-pipeline/`、`skills/seedance-compiler/` 与 `lint_prompt.py`（`RL-06 / RL-18`）。
- [x] **防空椅穿帮 / 视锥邻座守恒 / 反粉红大象 / 双层坐标系分离（360°→2D） / 身体-头部-视线三层锁**：已合入 `docs/CINEMATOGRAPHY_AND_TRANSITIONS.md`、`skills/cinematography-blocking/`、`manifest.json` 与 `lint_prompt.py`（`RL-26 / RL-27` P0 拦截）。
- [x] **Seedream 5.5 极简正向规范（`≤260/280` 字、零图文对抗、否定词 `≤1`、人物先于空景）**：已合入 `skills/art-asset-pipeline/` 与 `lint_prompt.py`（`RL-21` P0 拦截）。
- [x] **官方声音四分隔符 `{台词}` `<音效>` `(音乐)` `【字幕】`、防老年数字人三铁律、全身动力学微动链、情绪极性双锚与跨幕边界交接卡**：已合入 `skills/performance-sound-director/`、`skills/redline-auditor/` 与 `projects/_template/03_act_handbook_template.md`。
- [x] **480p 试样→1080p 精修 + 2-Strike 止损律 + 7 维质检卡 + L1–L4 救片树 + 五步院线化 Finishing（-14 LUFS 四轨混音、前切 6 帧后切 1 帧、`0.15s` 淡出、色彩匹配先于 LUT）**：已合入 `docs/STUDIO_CONSTITUTION.md`、`docs/POST_JIANYING_GUIDE.md` 与 `skills/post-qa-finishing/`。
- [x] **全套 7 个 V3.x Skills 全局同步 + `ERR-029` / `ERR-030` 铁律入库**。

---

## 三、当前活跃剧目进度：《今天谁过生日》V3.1 从零重制版（`projects/mama-birthday-v3/`）

> 历史 V2.x/A2 试水基线目录 `projects/mama-birthday/` 保持原样封存不修改，供横向对照。

### 第一幕（V3.1 一卡双区瘦身 + 空间线稿骨架定稿，待即梦开机实测）
- [x] 全流程 7 工位按 `ERR-029` 分工完成，并由站 3 / 站 2 / 站 5 / 站 1 协同落地 V3.1 `CHAR-SHEET` 单卡双区（偏重方案 A）与 `SCENE-LAYOUT-01` 无字空间透视线稿驱动 `SCENE-01-S0`。
- [x] 站 6 机械扫描 `lint_prompt.py --model 2.5`（**31 单元 = 23 生图 + 8 视频**）`P0=0, P1=0` + 独立只读隔离盲审 `PASS`。
- [x] 自动编译零失步网页工作台 [`workbench_act01.html`](projects/mama-birthday-v3/workbench_act01.html)（含首轮锚点过滤：`19 图 + 6 视频`）。
- [ ] **下一步实测**：在即梦优先生成首轮 **`19` 张锚点图**（含 5 张 `CHAR-SHEET` 与 `#9 SCENE-LAYOUT-01` → `#10 SCENE-01-S0`）→ Pre-Vis → **`480p` 试拍 `6` 个首轮视频锚点**（重点盯防 `A1-06` 零笑意与 `A1-07B` 呼吸停顿，若飘脸则同账号零积分裁切对应 `CHAR-SHEET` 右半幅），验收达标后出 `1080p`。

### 第二幕 ～ 第五幕（按第 1 幕实测反馈顺序推进）
- [ ] **第二幕**：第 1 幕实测验证通过后，依托第 1 幕已冻结的 5 张 `CHAR-SHEET` 与 4 张 `SHOT-MASTER` 无缝续接第 2 幕。
- [ ] **第三幕 ～ 第五幕**：依 `00_project_brief.md` 大纲逐幕 3 波次流水线展开。
