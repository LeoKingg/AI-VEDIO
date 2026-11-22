# AI-VEDIO｜抖音 16:9 电影感 AI 现实主义剧情短片工作流

面向单人/小团队创作者的**工业化 AI 剧情短片制片系统**，聚焦**抖音 16:9 横屏电影感情感中视频（1.5–3 分钟，3–5 天精品周更）**，以即梦 **`Seedream 5.5`（生图）+ `Seedance 2.0 / 2.5`（生视频）+ 剪映专业版（后期）** 为主力闭环。

## 核心设计原则

1. **三层物理解耦**：通用影视制片底座（`docs/`）与具体 AI 模型语法分离，标准化生产技能（`skills/`）与具体剧目实例（`projects/`）物理隔离，杜绝私人项目设定污染通用规范。
2. **电影感前置到静态图**：通过「视觉圣经 + 全片光影参考图 + 中灰底（`#555A64`）定向侧光角色图 + S 级镜头剧照首帧」，把 80% 审美试错留在低成本的 `Seedream 5.5` 生图阶段。
3. **模型无关中间层 + 双版本编译**：先产出模型无关的《导演分镜规格表》，再按目标模型编译为 `Seedance 2.0`（镜号制、4–15s）或 `Seedance 2.5`（整数秒时间戳、4–30s、复合运镜、多关键帧）纯净 Prompt。
4. **双保险独立红线门禁**：`scripts/lint_prompt.py` 毫秒级确定性扫描硬违规 + 独立子 Agent 隔离上下文输出 `PASS / FAIL` 清单（只报错、严禁擅改文风）。

## 仓库目录结构

```text
AI-VEDIO/
├── README.md                              # 本文件
├── docs/                                  # Layer 1：通用影视制片知识底座（SSOT）
│   ├── SOP_V2.0.md                        # 全流程 5 步制片总纲
│   ├── VISUAL_BIBLE_GUIDE.md              # 摄影指导(DP)视觉圣经与光影规范
│   ├── CINEMATOGRAPHY_AND_TRANSITIONS.md  # 导演镜头语法、表演微动与视听转场规范
│   ├── POST_JIANYING_GUIDE.md             # 剪映专业版调色、声桥、急救与抖音黑边包装
│   └── ERROR_PLAYBOOK.md                  # 版本化实战错误复盘库（ERR-001~012+）
├── skills/                                # Layer 2：4 个符合 agentskills.io 规范的核心 Skills
│   ├── director-storyboard/               # [站1] 双入口编剧拆解 + 抖音3秒钩子 + 导演分镜与转场
│   ├── visual-bible-art/                  # [站2] 视觉圣经 + Seedream 5.5 资产与 S 级剧照首帧
│   ├── seedance-prompt-writer/            # [站3] 中间层规格 → Seedance 2.0/2.5 双版本视频 Prompt
│   └── prompt-redline-auditor/            # [站4] Python 确定性 Lint + 独立子 Agent 红线审查
├── projects/                              # Layer 3：具体项目实例物理隔离区
│   └── _template/                         # 新剧标准脚手架
└── scripts/
    └── validate_skills.py                 # agentskills.io 规范与防污染自检脚本
```

## 快速开拍一部新剧（5 步闭环）

1. **初始化项目**：复制 `projects/_template/` 为 `projects/<你的项目名>/`，填写 `00_project_brief.md`（对标爆款链接/逐字稿，或原创故事大纲）。
2. **站 1 · 导演分镜与转场**（`skills/director-storyboard/`）：完成双入口剧本定稿、抖音前 3 秒钩子质检、分幕《导演分镜规格表》（含每镜 S/A 分级、设计理由与出入点转场）。
3. **站 2 · 视觉圣经与生图**（`skills/visual-bible-art/`）：定全片光影色卡参考图 → 仅锁核心主角底座与共享空景 → 按幕用 `Seedream 5.5` 产出中灰底侧光单人图、纯净空景与 S 级剧照首帧。
4. **站 3 + 站 4 · 编译与红线门禁**（`skills/seedance-prompt-writer/` + `skills/prompt-redline-auditor/`）：按 `2.0` 或 `2.5` 适配器编译纯净视频 Prompt，先跑确定性脚本再过独立审查：
   ```bash
   python3 skills/prompt-redline-auditor/scripts/lint_prompt.py \
     --model 2.5 \
     --file projects/<你的项目名>/03_act01_handbook.md
   ```
5. **即梦出片与剪映收口**：按 `docs/POST_JIANYING_GUIDE.md` 完成黑位压实、统一电影 LUT、35mm 细微颗粒、环境底噪贯通切点、J/L-Cut 与抖音上下黑边标题/字幕封装；新踩的坑随时追加进 `docs/ERROR_PLAYBOOK.md`。

## 仓库规范自检

```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s skills/prompt-redline-auditor/scripts -p "test_*.py" -v
```
