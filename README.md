# AI-VEDIO｜V3.0 工业化 AI 剧情短片制片系统（`1→100` 精品线）

面向单人/小团队创作者的**全链路工业化 AI 剧情短片制片工作室**，从“单镜试错补漏洞（`0→1`）”全面升级为**「七大专家分工 + 五模式智能路由 + 双目标机械门禁 + 五步院线化收口」**（`1→100`），默认以 **`Seedream 5.5`（生图）+ `Seedance 2.5`（主力生视频，向下兼容 `2.0`）+ 剪映专业版（Finishing 收口）** 为核心生产栈。

---

## 一、V3.0 核心架构原则

1. **三层物理解耦 + 可插拔题材/平台预设**：
   - **Layer 1（`docs/` + `presets/`）**：制片总宪法、6 阶段 SOP、光影圣经、视听运镜、院线化后期与 28 条实战复盘库；题材与平台规则解耦到 `presets/`（现实主义剧情 / 悬疑惊悚 × 抖音 16:9 黑边 / 9:16 原生竖屏）。
   - **Layer 2（`skills/`）**：**7 个 1:1 对应独立子 Agent 的专业 Skill**，严格遵循 `agentskills.io` 规范，按 **3 波次协同调度**（含定点修补模式，拒绝全链路空转）。
   - **Layer 3（`projects/` + `manifest.json`）**：具体剧目物理隔离，通过机器可读 `manifest.json` 锁定资产命名、场景状态（`S0→S1`）与已移除物体（防粉红大象）。
2. **以 `Seedance 2.5` 连续多镜为主力，彻底告别默认 4s 单镜拼接**：
   - 采用 **五模式路由矩阵**：`SEQ-Multi`（`10–25s` 连续多镜，主力甜区 `10–20s`）、`SEQ-Grid`（≤15 格无字线稿分镜格）、`M-Master`（同源闭唇实景母帧驱动特写演技）、`V-Ref`（参考视频强动作迁移）、`S-Struct / E-Edit`（首尾帧锁构图 & `MOV` 单拍多机原生编辑重拍）。
   - 严格推行 **Pre-Vis 动态分镜预演 → `480p` 首轮锚点试样 → `1080p` 精修成片** 与 **2-Strike 止损律**，把 80% 废片成本拦在算力消耗之前。
3. **双目标确定性红线门禁 + 零失步自动工作台**：
   - `lint_prompt.py` 同时扫描 **`Seedream 5.5` 生图块 + `Seedance 2.5/2.0` 视频块 + `manifest.json` 跨文件状态**（拦截外来 `STYLE-REF` 进视频、360° 钟面词泄漏、粉红大象、生图超长/否定词超限、2.5 时间戳断档、台词超速等）。
   - `build_workbench.py` 一键将任意 `03_actXX_handbook.md` 编译为 **100% 逐字节零失步** 的可交互 HTML 复制工作台。

---

## 二、七大专家 Skills 与三波次调度矩阵

| 波次 | Skill 目录（1:1 子 Agent） | 核心职责 |
| :---: | :--- | :--- |
| **Wave 1 · 定底座（叙事/空间/视觉）** | `skills/director-showrunner/` | 双入口编剧拆解、第 0.5 步讨论表、潜台词与留存钩子、五模式路由 |
| **Wave 1 · 定底座（叙事/空间/视觉）** | `skills/cinematography-blocking/` | 动机运镜、Z 轴纵深与移焦、360°→2D 空间转译、视锥邻座守恒、平台安全区 |
| **Wave 1 · 定底座（叙事/空间/视觉）** | `skills/art-asset-pipeline/` | 视觉圣经、`CHAR-FACE 70%` / `SHOT-MASTER` / `GRID-LINEART`、Seedream `≤255` 字纯正向模板、Pre-Vis 预演 |
| **Wave 2 · 精雕编译（表演/声学/视频）** | `skills/performance-sound-director/` | 潜台词物理演技链、防老年数字人三铁律、视频动作参考、四轨声学点位与多情绪干声 |
| **Wave 2 · 精雕编译（表演/声学/视频）** | `skills/seedance-compiler/` | 中间层规格 → `Seedance 2.5`（主力整数秒时间戳 / 编辑重拍）或 `2.0`（镜号制兼容）纯净 Prompt |
| **Wave 3 · 独立门禁与终剪** | `skills/redline-auditor/` | 双目标机械扫描（`lint_prompt.py`）+ 独立隔离上下文跨幕盲审（只判 `PASS / FAIL`，严禁代改文风） |
| **Wave 3 · 独立门禁与终剪** | `skills/post-qa-finishing/` | 7 维成片质检打分卡、L1–L4 救片决策树、五步院线化收口（-14 LUFS 四轨混音 / 色彩匹配 / 超分 / 双交付） |

---

## 三、仓库目录结构

```text
AI-VEDIO/
├── README.md                              # 本文件（V3.0 总览与 CLI 指南）
├── PROGRESS.md                            # 跨对话里程碑与活跃剧目进度总账
├── docs/                                  # Layer 1：通用影视制片底座（SSOT）
│   ├── STUDIO_CONSTITUTION.md             # 工作室总宪法（冲突仲裁 / 3 波次调度 / 预算止损律）
│   ├── SOP_V3.0.md                        # V3.0 六阶段工业化制片总纲与五模式路由矩阵
│   ├── VISUAL_BIBLE_GUIDE.md              # 视觉圣经、9 类 SSOT 资产与 30 天写实人脸信任窗
│   ├── CINEMATOGRAPHY_AND_TRANSITIONS.md  # 动机运镜、Show Don't Tell、双层坐标系与安全区
│   ├── POST_JIANYING_GUIDE.md             # 五步院线化 Finishing 收口与四轨 -14 LUFS 混音规范
│   └── ERROR_PLAYBOOK.md                  # 实战复盘库（ERR-001 ~ ERR-028，含生命周期标记）
├── presets/                               # 可插拔题材与平台预设
│   ├── genre_realistic_drama.md           # 现实主义情感剧情预设
│   ├── genre_suspense_thriller.md         # 悬疑惊悚类型预设
│   ├── platform_douyin_letterbox.md       # 抖音 16:9 横屏上下黑边封装预设
│   └── platform_vertical_916.md           # 原生 9:16 竖屏短剧安全区预设
├── skills/                                # Layer 2：7 个符合 agentskills.io 规范的专家 Skills
│   ├── director-showrunner/
│   ├── cinematography-blocking/
│   ├── art-asset-pipeline/
│   ├── performance-sound-director/
│   ├── seedance-compiler/
│   ├── redline-auditor/                   # 内置 scripts/lint_prompt.py & test_lint_prompt.py
│   └── post-qa-finishing/
├── scripts/                               # 零依赖自动化工具链（Python 3 stdlib）
│   ├── init_project.py                    # 一键按题材/平台预设初始化新剧与 manifest.json
│   ├── build_workbench.py                 # 将 03_actXX_handbook.md 零失步编译为 HTML 复制工作台
│   └── validate_skills.py                 # 7 Skills 规范 + 链接完整性 + _template 自检门禁
└── projects/                              # Layer 3：具体剧目实例隔离区
    ├── _template/                         # V3.0 标准脚手架（含 manifest.json，通过自检 P0=0/P1=0）
    └── mama-birthday/                     # Pilot 剧目《今天谁过生日》（Act 1–2 为 V2.x 历史基线）
```

---

## 四、快速开拍与 CLI 工具链

### 1. 一键初始化新剧（默认 `Seedance 2.5`）
```bash
python3 scripts/init_project.py \
  --name my-short-drama \
  --genre realistic_drama \
  --platform douyin_letterbox \
  --model 2.5
```

### 2. 双目标 + 跨文件确定性红线门禁（每幕必跑）
```bash
python3 skills/redline-auditor/scripts/lint_prompt.py \
  --model 2.5 \
  --manifest projects/my-short-drama/manifest.json \
  --file projects/my-short-drama/03_act01_handbook.md
```

### 3. 自动编译零失步 HTML 执行工作台
```bash
python3 scripts/build_workbench.py \
  --handbook projects/my-short-drama/03_act01_handbook.md \
  --output projects/my-short-drama/act01_workbench.html
```

### 4. 仓库全量健康自检与单元测试
```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s skills/redline-auditor/scripts -p "test_*.py" -v
```
