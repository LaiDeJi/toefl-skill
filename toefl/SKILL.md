---
name: toefl
description: >
  TOEFL iBT 2026 备考教练与学习系统。在空白资料夹中自动展开完整的 12 周学习计划、
  每日训练素材、进度追踪、模拟考、Anki 单字卡生成、TTS 听力练习、口说评估、写作批改。
  当使用者提到 TOEFL、托福、英语检定备考、英文考试准备、托福口说练习、托福写作批改、
  托福听力训练、托福阅读练习、托福模拟考、TOEFL mock test、TOEFL study plan、
  /toefl、或任何与 TOEFL 考试相关的学习需求时，务必触发此技能。
  即使使用者只是说「帮我准备英文考试」或「我要考托福」也应触发。
---

# TOEFL iBT 2026 备考教练

一套 AI 驱动的模组化 TOEFL 备考系统。

## 模组总览

本技能由 8 个独立模组组成，采用 progressive disclosure——只在需要时才读取对应模组。

```
toefl/
├── SKILL.md                          ← 你现在在这里（路由器）
├── scripts/
│   ├── init.py                       ← 🏁 初始化模组
│   ├── daily.py                      ← 📅 每日追踪模组
│   ├── scaffold.py                   ← 🔧 资料夹结构产生器（由 init.py 呼叫）
│   ├── progress.py                   ← 📊 进度追踪与统计
│   ├── adaptive.py                   ← 🧠 自适应引擎（动态调整难度与时间分配）
│   ├── speaking_coach.py             ← 🎤 口说教练模组
│   ├── writing_grader.py             ← ✍️ 写作批改模组
│   ├── mock_test.py                  ← 📝 模拟考模组
│   ├── generate_listening.py         ← 🎧 听力素材产生器
│   └── generate_anki.py              ← 📚 Anki 单字卡产生器
└── references/
    ├── exam-format-2026.md           ← 📋 2026 新制完整格式
    ├── study-plan-12week.md          ← 📅 12 周计划模板
    ├── scoring-rubrics.md            ← 📏 ETS 评分标准
    ├── vocabulary-core.md            ← 📖 核心学术字汇
    └── resources-guide.md            ← 🔗 备考素材完整指南（官方+免费+工具）
```

---

## 路由逻辑

根据使用者的意图，选择对应模组：

### 🏁 首次使用 / 初始化
**触发词：** `/toefl`、「开始准备托福」、「建立学习计划」、初次进入空白资料夹
**动作：**
1. 执行 `scripts/init.py`（引导问卷 → 产生 config → 建立资料夹 → 产生诊断考）
2. 如果非互动环境，用 `--non-interactive` 搭配参数

```bash
python scripts/init.py --target .
# 或非互动模式
python scripts/init.py --target . --non-interactive --target-score 5.0 --exam-date 2026-07-15
```

### 📅 每日进入 / 今天练什么
**触发词：** 「今天练什么」、「开始练习」、进入已初始化的资料夹
**动作：**
1. 执行 `scripts/daily.py --target ./toefl-prep/`
2. 显示今日任务、连续天数、倒数计时
3. 引导完成各项练习

```bash
python scripts/daily.py --target ./toefl-prep/           # 显示今日任务
python scripts/daily.py --target ./toefl-prep/ --complete  # 标记完成
python scripts/daily.py --target ./toefl-prep/ --advance   # 推进下一天
python scripts/daily.py --target ./toefl-prep/ --status    # 本周总览
```

### 📊 看进度 / 弱项分析
**触发词：** 「看进度」、「我的成绩」、「弱项分析」
**动作：** 执行 `scripts/progress.py --action show --target ./toefl-prep/`

```bash
python scripts/progress.py --action show --target ./toefl-prep/
python scripts/progress.py --action log --target ./toefl-prep/ --minutes 30 --section reading --score 4.5
```

### 🎤 口说练习
**触发词：** 「口说练习」、「练口说」、「speaking practice」
**动作：**
1. 执行 `scripts/speaking_coach.py` 产生题目
2. 如需音档，执行 `scripts/generate_speaking.py` 产生 TTS（`--type repeat` / `interview`）
3. 使用者完成后，读取 `references/scoring-rubrics.md` 的口说段落进行评估

```bash
python scripts/speaking_coach.py --type full --output ./toefl-prep/speaking/
python scripts/speaking_coach.py --type repeat --output ./toefl-prep/speaking/
python scripts/speaking_coach.py --type interview --output ./toefl-prep/speaking/ --topic technology
```

**AI 评估口说回答时：**
- 读取 `references/scoring-rubrics.md` 的 Speaking 段落
- Listen & Repeat：检查 Repeat Accuracy / Fluency / Intelligibility
- Interview：检查 Fluency / Intelligibility / Language Use / Organization
- 使用标准回馈格式（rubric 档案底部有模板）

### ✍️ 写作练习 / 批改
**触发词：** 「写作练习」、「批改我的写作」、「练写作」、「writing practice」
**动作：**
1. 执行 `scripts/writing_grader.py` 产生题目
2. 使用者完成后，读取 `references/scoring-rubrics.md` 的写作段落进行批改

```bash
python scripts/writing_grader.py --type full --output ./toefl-prep/writing/
python scripts/writing_grader.py --type sentence --output ./toefl-prep/writing/ --count 10
python scripts/writing_grader.py --type email --output ./toefl-prep/writing/
python scripts/writing_grader.py --type discussion --output ./toefl-prep/writing/
```

**AI 批改写作时：**
- 读取 `references/scoring-rubrics.md` 的 Writing 段落
- Email：检查是否涵盖所有要点 / 语气 / 文法 / 拼字
- Discussion：检查观点 / 论证 / 回应他人 / 文法
- 使用标准回馈格式（列出具体错误 + 修正 + 模范回答）

### 🎧 听力练习
**触发词：** 「听力练习」、「练听力」、「listening practice」
**动作：** 执行 `scripts/generate_listening.py` 产生音档和练习题

```bash
python scripts/generate_listening.py --type all --output ./toefl-prep/listening/
python scripts/generate_listening.py --type conversation --output ./toefl-prep/listening/
python scripts/generate_listening.py --type academic --output ./toefl-prep/listening/
python scripts/generate_listening.py --type choose-response --output ./toefl-prep/listening/
```

**依赖：** `pip install edge-tts`

### 📚 单字 / Anki
**触发词：** 「背单字」、「产生 Anki」、「vocabulary」、「单字卡」
**动作：**
1. 读取 `references/vocabulary-core.md` 选择本周单字
2. 执行 `scripts/generate_anki.py` 产生 .apkg

### 📖 推荐素材 / 该用什么来练
**触发词：** 「推荐素材」、「该看什么」、「有什么资源」、「练习素材」、「怎么找听力材料」
**动作：** 读取 `references/resources-guide.md`，根据使用者的程度和弱项推荐对应素材

resources-guide.md 包含：
- 官方 ETS 资源（模拟考、Interactive Sampler）
- 模拟考平台比较（Magoosh、BestMyTest、TestSucceed 等）
- 各科素材来源（按难度分级 Lv1–5）
- Podcast 推荐（入门/中级/进阶）
- YouTube 频道推荐
- 开源工具链（edge-tts 语音选择、语速调整指令）
- 每周素材排程建议
- 避免使用的过时资源清单

```bash
python scripts/generate_anki.py --output ./toefl-prep/vocabulary/anki-decks/ --week 1
```

**依赖：** `pip install genanki`

### 🧠 自适应调整 / 弱项分析
**触发词：** 「弱项分析」、「调整计划」、「重新平衡」、「难度调整」、「里程碑检查」
**动作：** 执行 `scripts/adaptive.py`

```bash
python scripts/adaptive.py --target ./toefl-prep/ --action analyze     # 完整分析报告
python scripts/adaptive.py --target ./toefl-prep/ --action rebalance   # 重新分配时间
python scripts/adaptive.py --target ./toefl-prep/ --action difficulty  # 建议难度等级
python scripts/adaptive.py --target ./toefl-prep/ --action checkpoint  # 里程碑检查
```

**自适应引擎做什么：**
- 从 progress.json 和模拟考数据计算各科差距（gap = 目标分数 - 现有分数）
- 差距越大的科目 → 分配更多每日练习时间（最高 45%，最低 10%）
- 根据现有分数推荐题目难度等级（Lv1 基础 ~ Lv5 高级）
- 侦测分数下降趋势 → 发出警告
- 各科差距 > 1.5 分 → 判定严重不平衡，建议集中补强
- 产生 adaptive.json 供其他模组读取
- 里程碑检查（25%/50%/75%/100% 进度点）

**daily.py 整合：** 
daily.py 会自动读取 adaptive.json（如存在），用自适应建议替换固定计划。

**何时触发 rebalance：**
- 每次模拟考后自动建议
- 使用者主动要求
- 里程碑检查未通过时

### 📝 模拟考
**触发词：** 「模拟考」、「mock test」、「做一次完整测验」
**动作：**
1. 执行 `scripts/mock_test.py --action create` 建立考试资料夹
2. 按科目顺序引导考试（R → L → S → W）
3. 各科目使用对应模组产生题目
4. 完成后评分并更新 progress.json

```bash
python scripts/mock_test.py --target ./toefl-prep/ --action create
python scripts/mock_test.py --target ./toefl-prep/ --action score --test 1 --reading 4.5 --listening 5.0 --speaking 4.0 --writing 4.5
python scripts/mock_test.py --target ./toefl-prep/ --action history
```

---

## 工具链

| 工具 | 用途 | 安装 | 必要性 |
|------|------|------|--------|
| `edge-tts` | TTS 听力素材 + 跟读音档 | `pip install edge-tts` | 听力/口说必要 |
| `genanki` | Anki 单字卡 .apkg | `pip install genanki` | 单字功能必要 |
| `Kokoro TTS` | 离线高品质 TTS | `pip install kokoro` | 选用（替代 edge-tts） |

---

## 2026 新制速查

需要详细资讯时，读取 `references/exam-format-2026.md`。

**计分：** 1.0–6.0（CEFR 对齐），总分 = 四科平均
**自适应：** R/L 的 Module 1 表现决定 Module 2 难度（Hard path 上限 6.0 / Easy path 上限 4.0）

| 科目 | 时间 | 题型 |
|------|------|------|
| Reading | 18–27 min | Complete Words / Daily Life / Academic Passage |
| Listening | 18–27 min | Choose Response / Conversations / Announcements / Academic Talks |
| Speaking | ~10 min | Listen & Repeat (7) + Interview (4)，全 AI 评分 |
| Writing | ~23 min | Build a Sentence (10) + Email (1) + Discussion (1) |

---

## AI 行为准则

1. **首次进入：** 检查 toefl-prep/config.json 是否存在。不存在 → 跑 init.py。存在 → 跑 daily.py。
2. **Progressive disclosure：** 不要一次读取所有 reference 档案。只在需要时才读取对应段落。
3. **语言：** 预设用繁体中文与使用者沟通，但所有 TOEFL 练习内容用英文。
4. **批改时：** 一定要读取 `references/scoring-rubrics.md` 再评分，确保标准一致。
5. **鼓励：** 保持正面态度，强调进步而非缺点。每次练习结束给出 1–2 个具体改进建议。
6. **追踪：** 每次练习后提醒使用者更新 progress.json（或自动帮他更新）。
