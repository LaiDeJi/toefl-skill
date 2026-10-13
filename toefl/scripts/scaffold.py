#!/usr/bin/env python3
"""
TOEFL iBT 2026 Study Environment Scaffold
Generates the complete folder structure and initial files for a 12-week study plan.

Usage:
    python scaffold.py --target ./my-toefl-prep
    python scaffold.py --target . --weeks 8 --daily-minutes 60 --target-score 5.0 --exam-date 2026-07-15
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


def create_config(target: Path, args):
    """Create the configuration file."""
    config = {
        "created": datetime.now().isoformat(),
        "target_score": args.target_score,
        "exam_date": args.exam_date or "",
        "daily_minutes": args.daily_minutes,
        "total_weeks": args.weeks,
        "current_week": 1,
        "current_day": 1,
        "language": "zh-TW",
        "tts_voice": "en-US-AriaNeural",
        "tts_engine": "edge-tts",
        "anki_new_cards_per_day": 20,
    }
    with open(target / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def create_progress(target: Path, weeks: int):
    """Create the progress tracking file."""
    progress = {
        "last_updated": datetime.now().isoformat(),
        "total_study_minutes": 0,
        "streak_days": 0,
        "longest_streak": 0,
        "baseline_scores": {
            "reading": None,
            "listening": None,
            "speaking": None,
            "writing": None,
            "total": None,
        },
        "latest_scores": {
            "reading": None,
            "listening": None,
            "speaking": None,
            "writing": None,
            "total": None,
        },
        "mock_tests": [],
        "weekly_completion": {f"week-{i:02d}": {"completed": 0, "total": 6} for i in range(1, weeks + 1)},
        "vocabulary": {
            "total_learned": 0,
            "total_reviewed": 0,
            "words_due_today": 0,
        },
        "daily_log": [],
    }
    with open(target / "progress.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


# ── Phase definitions ──────────────────────────────────────────────

PHASES = {
    "foundation": {
        "name": "基础期",
        "weeks": (1, 4),
        "focus": "熟悉题型、建立每日习惯、累积基础词汇",
    },
    "intensive": {
        "name": "强化期",
        "weeks": (5, 8),
        "focus": "弱项加强、计时练习、提升准确度",
    },
    "sprint": {
        "name": "冲刺期",
        "weeks": (9, 12),
        "focus": "模拟考、稳定输出、考前调整",
    },
}


DAILY_TEMPLATES = {
    "reading": "## 阅读练习\n\n- [ ] Complete the Words：5 题\n- [ ] Read in Daily Life：2 篇\n- [ ] Academic Passage：1 篇\n\n### 笔记区\n\n",
    "listening": "## 听力练习\n\n- [ ] Choose a Response：5 题\n- [ ] Conversation：1 段\n- [ ] Announcement：1 段\n- [ ] 笔记练习：记录关键词\n\n### 笔记区\n\n",
    "speaking": "## 口语练习\n\n- [ ] Listen & Repeat：跟读 7 句（shadowing 15 分钟）\n- [ ] Interview：即兴回答 2 题（各 45 秒）\n- [ ] 录音并回听\n\n### 自我评估\n\n| 维度 | 自评 (1-5) | 备注 |\n|------|-----------|------|\n| Fluency | | |\n| Intelligibility | | |\n| Language Use | | |\n| Organization | | |\n\n",
    "writing": "## 写作练习\n\n- [ ] Build a Sentence：10 题\n- [ ] Write an Email 或 Academic Discussion（择一）\n\n### 草稿区\n\n\n### AI 批改结果\n\n（完成后请 AI 批改）\n",
    "vocabulary": "## 单词复习\n\n- [ ] Anki 复习（旧卡）\n- [ ] 学习 20 个新单词\n- [ ] 用新单词造句 5 句\n\n### 今日新单词\n\n| 单词 | 词性 | 定义 | 例句 |\n|------|------|------|------|\n| | | | |\n\n",
    "review": "## 周末复习\n\n- [ ] Anki 全部复习\n- [ ] 重做本周错题\n- [ ] 更新进度追踪\n- [ ] 检查本周目标完成度\n\n### 本周反思\n\n**做得好的：**\n\n**需要改进的：**\n\n**下周重点：**\n\n",
}


# Each day maps to focus areas (R=reading, L=listening, S=speaking, W=writing, V=vocab)
WEEKLY_ROTATION = [
    ["vocabulary", "reading"],       # Day 1
    ["vocabulary", "listening"],     # Day 2
    ["vocabulary", "speaking"],      # Day 3
    ["vocabulary", "writing"],       # Day 4
    ["vocabulary", "reading", "listening"],  # Day 5
    ["vocabulary", "speaking", "writing"],   # Day 6
]


def get_phase(week: int, total_weeks: int) -> str:
    """Determine which phase a week belongs to."""
    third = total_weeks / 3
    if week <= third:
        return "foundation"
    elif week <= 2 * third:
        return "intensive"
    else:
        return "sprint"


def create_weekly_goals(week: int, total_weeks: int) -> str:
    """Generate goals markdown for a specific week."""
    phase = get_phase(week, total_weeks)
    phase_info = PHASES[phase]

    goals = f"# 第 {week} 周 — {phase_info['name']}\n\n"
    goals += f"**阶段重点：** {phase_info['focus']}\n\n"
    goals += "## 本周目标\n\n"

    if phase == "foundation":
        if week == 1:
            goals += "- [ ] 完成诊断模拟考，记录基线分数\n"
            goals += "- [ ] 熟悉所有新制题型\n"
            goals += "- [ ] 建立每日 Anki 习惯\n"
            goals += "- [ ] 累积 30 个新单词\n"
        elif week == 2:
            goals += "- [ ] 阅读三种题型各练习 10 题以上\n"
            goals += "- [ ] 累积 100 个新单词（含拼写）\n"
            goals += "- [ ] Complete the Words 正确率 ≥ 60%\n"
        elif week == 3:
            goals += "- [ ] 听力四种题型各练习 5 题以上\n"
            goals += "- [ ] Listen & Repeat 尝试完整复述 7 句\n"
            goals += "- [ ] 听懂 2 分钟学术短文的主旨\n"
        else:
            goals += "- [ ] Build a Sentence 正确率 ≥ 70%\n"
            goals += "- [ ] 完成一篇 Email + 一篇 Discussion\n"
            goals += "- [ ] 完成第二次模拟考\n"

    elif phase == "intensive":
        if week == 5:
            goals += "- [ ] Module 1 模拟正确率 ≥ 70%\n"
            goals += "- [ ] 限时练习阅读和听力\n"
        elif week == 6:
            goals += "- [ ] 每天 shadowing 15 分钟\n"
            goals += "- [ ] Interview 能稳定说满 40 秒\n"
        elif week == 7:
            goals += "- [ ] Email 和 Discussion 计时完成\n"
            goals += "- [ ] Build a Sentence 正确率 ≥ 90%\n"
        else:
            goals += "- [ ] 完成第三次模拟考\n"
            goals += "- [ ] 分数达到目标 -0.5 以内\n"

    else:  # sprint
        if week == 9:
            goals += "- [ ] 完成 2 次完整模拟考\n"
            goals += "- [ ] 严格计时\n"
        elif week == 10:
            goals += "- [ ] 分析所有模拟考的错误模式\n"
            goals += "- [ ] 针对弱项专项练习\n"
        elif week == 11:
            goals += "- [ ] 最后一次完整模拟考\n"
            goals += "- [ ] 分数稳定在目标范围\n"
        else:
            goals += "- [ ] 轻量练习，保持手感\n"
            goals += "- [ ] 确认考试流程和文件\n"
            goals += "- [ ] 调整作息\n"

    goals += "\n## 本周完成度\n\n"
    goals += "| 日 | 完成 | 备注 |\n|---|------|------|\n"
    for d in range(1, 7):
        goals += f"| Day {d} | [ ] | |\n"
    goals += "| Review | [ ] | |\n"

    return goals


def create_daily_task(week: int, day: int, total_weeks: int, daily_minutes: int) -> str:
    """Generate a daily task markdown file."""
    phase = get_phase(week, total_weeks)
    focus_areas = WEEKLY_ROTATION[day - 1] if day <= 6 else ["review"]

    content = f"# 第 {week} 周・Day {day}\n\n"
    content += f"**日期：** ____年____月____日\n"
    content += f"**预计时间：** {daily_minutes} 分钟\n"
    content += f"**今日重点：** {' + '.join(a.capitalize() for a in focus_areas)}\n\n"
    content += "---\n\n"

    if day == 7:
        content += DAILY_TEMPLATES["review"]
    else:
        for area in focus_areas:
            content += DAILY_TEMPLATES.get(area, "")
            content += "\n---\n\n"

    content += "## 今日完成度\n\n"
    content += "- [ ] 完成所有练习\n"
    content += f"- [ ] 实际花费时间：____ 分钟\n"
    content += "- [ ] 更新 progress.json\n"

    return content


def create_readme(target: Path, args):
    """Create the main README."""
    readme = """# 🎯 TOEFL iBT 2026 备考计划

## Quick Start

1. 每天打开这个文件夹
2. 启动 AI
3. 告诉 AI：「今天练什么？」

## 常用指令

| 指令 | 说明 |
|------|------|
| `今天练什么？` | 查看今日任务 |
| `帮我做口语练习` | 生成口语题目 + 评估 |
| `批改我的写作` | 提交写作草稿让 AI 批改 |
| `生成听力练习` | 用 TTS 生成听力音频 |
| `生成 Anki 单词卡` | 生成本周的 Anki deck |
| `模拟考` | 开始一次完整模拟考 |
| `看进度` | 显示学习进度和统计 |
| `弱项分析` | 分析各科弱项并给建议 |

## 目标

| 项目 | 设定 |
|------|------|
| 目标分数 | {target_score} |
| 考试日期 | {exam_date} |
| 每日时间 | {daily_minutes} 分钟 |
| 总周数 | {weeks} 周 |

## 文件夹说明

- `plan/` — 每周计划和每日任务
- `vocabulary/` — 单词表和 Anki deck
- `reading/` — 阅读练习
- `listening/` — 听力练习（含 TTS 音频）
- `speaking/` — 口语练习和反馈
- `writing/` — 写作练习和批改
- `mock-tests/` — 模拟考

## 工具安装

```bash
pip install edge-tts genanki
```
""".format(
        target_score=args.target_score,
        exam_date=args.exam_date or "未设定",
        daily_minutes=args.daily_minutes,
        weeks=args.weeks,
    )
    with open(target / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


def scaffold(args):
    """Main scaffold function."""
    target = Path(args.target).resolve()
    prep_dir = target / "toefl-prep"
    prep_dir.mkdir(parents=True, exist_ok=True)

    # Create top-level files
    create_config(prep_dir, args)
    create_progress(prep_dir, args.weeks)
    create_readme(prep_dir, args)

    # Create directory structure
    dirs = [
        "plan",
        "vocabulary/word-lists",
        "vocabulary/anki-decks",
        "reading/passages",
        "reading/exercises",
        "listening/audio",
        "listening/transcripts",
        "listening/exercises",
        "speaking/prompts",
        "speaking/recordings",
        "speaking/feedback",
        "writing/prompts",
        "writing/drafts",
        "writing/feedback",
        "mock-tests",
    ]
    for d in dirs:
        (prep_dir / d).mkdir(parents=True, exist_ok=True)

    # Create plan overview
    overview = "# 12 周备考计划总览\n\n"
    for phase_key, phase in PHASES.items():
        w1, w2 = phase["weeks"]
        overview += f"## {phase['name']}（第 {w1}–{w2} 周）\n"
        overview += f"**重点：** {phase['focus']}\n\n"
    with open(prep_dir / "plan" / "overview.md", "w", encoding="utf-8") as f:
        f.write(overview)

    # Create weekly plans
    for week in range(1, args.weeks + 1):
        week_dir = prep_dir / "plan" / f"week-{week:02d}"
        daily_dir = week_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)

        # Weekly goals
        goals = create_weekly_goals(week, args.weeks)
        with open(week_dir / "goals.md", "w", encoding="utf-8") as f:
            f.write(goals)

        # Daily tasks
        for day in range(1, 7):
            task = create_daily_task(week, day, args.weeks, args.daily_minutes)
            with open(daily_dir / f"day-{day}.md", "w", encoding="utf-8") as f:
                f.write(task)

        # Review day
        review = create_daily_task(week, 7, args.weeks, args.daily_minutes)
        with open(daily_dir / "review-day.md", "w", encoding="utf-8") as f:
            f.write(review)

    print(f"✅ TOEFL 备考环境已建立：{prep_dir}")
    print(f"   📅 {args.weeks} 周计划")
    print(f"   ⏱️ 每日 {args.daily_minutes} 分钟")
    print(f"   🎯 目标分数 {args.target_score}")
    print(f"\n下一步：进入 {prep_dir} 文件夹，告诉 AI「今天练什么？」")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOEFL iBT 2026 Study Environment Scaffold")
    parser.add_argument("--target", default=".", help="Target directory (default: current)")
    parser.add_argument("--weeks", type=int, default=12, help="Total study weeks (default: 12)")
    parser.add_argument("--daily-minutes", type=int, default=30, help="Daily study minutes (default: 30)")
    parser.add_argument("--target-score", type=float, default=5.0, help="Target score 1.0-6.0 (default: 5.0)")
    parser.add_argument("--exam-date", type=str, default="", help="Exam date YYYY-MM-DD")
    args = parser.parse_args()
    scaffold(args)
