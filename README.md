# toefl

[![Build & Release Skill](https://github.com/htlin222/toefl-skill/actions/workflows/release.yml/badge.svg)](https://github.com/htlin222/toefl-skill/actions/workflows/release.yml)
[![GitHub Release](https://img.shields.io/github/v/release/htlin222/toefl-skill?include_prereleases&label=skill%20version)](https://github.com/htlin222/toefl-skill/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/licenses/MIT)
[![Skills Protocol](https://img.shields.io/badge/protocol-vercel--labs%2Fskills-blue)](https://github.com/vercel-labs/skills)
[![Compatible Agents](https://img.shields.io/badge/agents-40%2B-green)](https://github.com/vercel-labs/skills#supported-agents)

> TOEFL iBT 2026 备考教练与学习系统。在空白文件夹中自动展开完整的 12 周学习计划、每日训练素材、进度追踪、模拟考、Anki 单词卡生成、TTS 听力练习、口语评估、写作批改。

## Install

```bash
npx skills add htlin222/toefl-skill
npx skills add -g htlin222/toefl-skill        # global
```

## What it does

一套 AI 驱动的模块化 TOEFL 备考系统。本技能由 8 个独立模块组成，采用 progressive disclosure——只在需要时才读取对应模块。

## Skill structure

```
toefl/
├── references
│   ├── exam-format-2026.md
│   ├── high-score-patterns.md
│   ├── listening-guide.md
│   ├── reading-guide.md
│   ├── resources-guide.md
│   ├── scoring-rubrics.md
│   ├── speaking-guide.md
│   ├── study-plan-12week.md
│   ├── vocabulary-core.md
│   └── writing-guide.md
├── scripts
│   ├── adaptive.py
│   ├── audio_utils.py
│   ├── daily.py
│   ├── generate_anki.py
│   ├── generate_listening.py
│   ├── generate_reading.py
│   ├── generate_speaking.py
│   ├── generate_writing.py
│   ├── init.py
│   ├── mock_test.py
│   ├── progress.py
│   ├── scaffold.py
│   ├── setup_env.py
│   ├── speaking_coach.py
│   └── writing_grader.py
└── SKILL.md
```

## Protocol

This skill follows the [vercel-labs/skills](https://github.com/vercel-labs/skills) protocol.
Each push to `main` triggers a GitHub Action that packages the skill as a `.skill` file
and creates a release tagged with the commit SHA.

## License

MIT License
