#!/usr/bin/env python3
"""
TOEFL 备考系统 — 初始化模块 (init.py)
首次使用时的引导精灵：问卷、诊断、个人化计划生成。

Usage:
    python init.py --target ./my-study-folder
    python init.py --target . --non-interactive --target-score 5.0 --exam-date 2026-07-15 --daily-minutes 30 --weeks 12

此模块会：
1. 询问用户的基本信息（目标分数、考试日期、每日可用时间、英语程度自评）
2. 生成个人化的 config.json
3. 调用 scaffold.py 生成完整文件夹结构
4. 生成一份简易诊断测验（diagnostic quiz）供用户完成
5. 输出「接下来怎么做」的引导说明
"""

import argparse
import json
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path


def interactive_onboarding() -> dict:
    """Interactive questionnaire for first-time setup."""
    print("=" * 55)
    print("🎯 TOEFL iBT 2026 备考系统 — 初始化精灵")
    print("=" * 55)
    print()

    # Target score
    print("📊 你的目标分数是多少？（新制 1.0–6.0）")
    print("   参考：5.0+ 顶尖大学 / 4.0–4.5 一般大学 / 3.5 基本门槛")
    while True:
        try:
            target_score = float(input("   目标分数 [5.0]: ").strip() or "5.0")
            if 1.0 <= target_score <= 6.0:
                break
            print("   ❌ 请输入 1.0 到 6.0 之间的数字")
        except ValueError:
            print("   ❌ 请输入数字")

    # Exam date
    print("\n📅 你的考试日期是？（格式：YYYY-MM-DD，不确定可跳过）")
    exam_date = input("   考试日期 [留空]: ").strip()
    if exam_date:
        try:
            exam_dt = datetime.strptime(exam_date, "%Y-%m-%d").date()
            days_left = (exam_dt - date.today()).days
            if days_left <= 0:
                print("   ⚠️ 这个日期已过，将设为未定")
                exam_date = ""
            else:
                weeks_available = days_left // 7
                print(f"   ✅ 距离考试 {days_left} 天（约 {weeks_available} 周）")
        except ValueError:
            print("   ⚠️ 日期格式不正确，将设为未定")
            exam_date = ""

    # Daily time
    print("\n⏱️ 你每天可以花多少时间准备？")
    print("   1) 15 分钟（零碎时间）")
    print("   2) 30 分钟（推荐最低）")
    print("   3) 45 分钟")
    print("   4) 60 分钟（密集备考）")
    print("   5) 自订")
    choice = input("   选择 [2]: ").strip() or "2"
    time_map = {"1": 15, "2": 30, "3": 45, "4": 60}
    if choice in time_map:
        daily_minutes = time_map[choice]
    else:
        try:
            daily_minutes = int(input("   请输入分钟数: ").strip())
        except ValueError:
            daily_minutes = 30

    # Self-assessment
    print("\n📝 你目前的英语程度自评：")
    print("   1) 初级 — 日常对话有困难")
    print("   2) 中级 — 能进行基本对话，阅读简单文章")
    print("   3) 中高级 — 能阅读学术文章，听懂大部分演讲")
    print("   4) 高级 — 接近流利，偶有文法或词汇不足")
    print("   5) 不确定（建议做诊断测验）")
    level_choice = input("   选择 [5]: ").strip() or "5"
    level_map = {"1": "beginner", "2": "intermediate", "3": "upper-intermediate", "4": "advanced", "5": "unknown"}
    self_level = level_map.get(level_choice, "unknown")

    # Weak areas
    print("\n🔍 你觉得自己最弱的是哪一科？（可多选，用逗号分隔）")
    print("   R=阅读  L=听力  S=口语  W=写作  ?=不确定")
    weak_input = input("   最弱科目 [?]: ").strip().upper() or "?"
    weak_map = {"R": "reading", "L": "listening", "S": "speaking", "W": "writing", "?": "unknown"}
    weak_areas = [weak_map.get(w.strip(), "unknown") for w in weak_input.split(",")]

    # Study weeks
    if exam_date:
        weeks = min(max(weeks_available, 4), 16)
        print(f"\n📅 根据考试日期，建议 {weeks} 周计划")
    else:
        print("\n📅 你想要几周的计划？")
        print("   建议：8 周（短期冲刺）/ 12 周（标准）/ 16 周（充裕）")
        try:
            weeks = int(input("   周数 [12]: ").strip() or "12")
            weeks = min(max(weeks, 4), 24)
        except ValueError:
            weeks = 12

    # TTS preference
    print("\n🔊 听力练习的 TTS 引擎：")
    print("   1) edge-tts（需网络，品质好，免费）← 推荐")
    print("   2) Kokoro（离线，需下载模型约 200MB）")
    tts_choice = input("   选择 [1]: ").strip() or "1"
    tts_engine = "edge-tts" if tts_choice == "1" else "kokoro"

    return {
        "target_score": target_score,
        "exam_date": exam_date,
        "daily_minutes": daily_minutes,
        "weeks": weeks,
        "self_level": self_level,
        "weak_areas": weak_areas,
        "tts_engine": tts_engine,
    }


def generate_config(target: Path, params: dict):
    """Generate personalized config.json."""
    config = {
        "version": "1.0.0",
        "created": datetime.now().isoformat(),
        "target_score": params["target_score"],
        "exam_date": params.get("exam_date", ""),
        "daily_minutes": params["daily_minutes"],
        "total_weeks": params["weeks"],
        "current_week": 1,
        "current_day": 1,
        "self_level": params.get("self_level", "unknown"),
        "weak_areas": params.get("weak_areas", ["unknown"]),
        "language": "zh-TW",
        "tts_engine": params.get("tts_engine", "edge-tts"),
        "tts_voice": "en-US-AriaNeural",
        "anki_new_cards_per_day": 20,
        "initialized": True,
        "diagnostic_completed": False,
        "phase_schedule": {
            "foundation": {"start": 1, "end": max(1, params["weeks"] // 3)},
            "intensive": {"start": max(2, params["weeks"] // 3 + 1), "end": max(3, params["weeks"] * 2 // 3)},
            "sprint": {"start": max(4, params["weeks"] * 2 // 3 + 1), "end": params["weeks"]},
        },
    }
    with open(target / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config


def generate_diagnostic(target: Path):
    """Generate a diagnostic quiz for baseline assessment."""
    diagnostic = {
        "title": "TOEFL 2026 诊断测验",
        "instructions": "这不是正式模拟考，而是快速评估你的起始程度。每科 5 题，约 15-20 分钟。",
        "sections": {
            "reading": {
                "description": "阅读理解（5 题）",
                "questions": [
                    {
                        "type": "complete_words",
                        "prompt": "The researcher's hyp_th_sis was supported by the experimental data.",
                        "answer": "hypothesis",
                        "explanation": "hypothesis = 假说。注意 y 和 e 的位置。"
                    },
                    {
                        "type": "complete_words",
                        "prompt": "Environmental sust__n_bility requires both individual and collective action.",
                        "answer": "sustainability",
                        "explanation": "sustainability = 永续性。注意 ai 和 a 的位置。"
                    },
                    {
                        "type": "daily_life",
                        "prompt": "Email: 'Hi Alex, The study group for Biology 101 will meet this Thursday at 3 PM in Room 204 instead of our usual time on Wednesday. Please bring your lab notes. — Sarah'",
                        "question": "What change is Sarah informing Alex about?",
                        "options": ["A. The room number", "B. The meeting day and time", "C. The subject being studied", "D. Who will attend"],
                        "answer": "B",
                    },
                    {
                        "type": "academic",
                        "passage": "Coral reefs, often called the rainforests of the sea, support approximately 25 percent of all marine species despite covering less than one percent of the ocean floor. Rising ocean temperatures cause coral bleaching, a process in which corals expel the algae living in their tissues. Without these algae, corals lose their color and their primary food source.",
                        "question": "What is the main cause of coral bleaching according to the passage?",
                        "options": ["A. Ocean pollution", "B. Overfishing", "C. Rising water temperatures", "D. Reduced sunlight"],
                        "answer": "C",
                    },
                    {
                        "type": "academic",
                        "passage": "Coral reefs, often called the rainforests of the sea, support approximately 25 percent of all marine species despite covering less than one percent of the ocean floor. Rising ocean temperatures cause coral bleaching, a process in which corals expel the algae living in their tissues. Without these algae, corals lose their color and their primary food source.",
                        "question": "The phrase 'rainforests of the sea' is used to emphasize:",
                        "options": ["A. Coral reefs are located near tropical forests", "B. Coral reefs have high biodiversity", "C. Coral reefs are endangered", "D. Coral reefs are very large"],
                        "answer": "B",
                    },
                ],
            },
            "writing": {
                "description": "写作能力（2 题）",
                "questions": [
                    {
                        "type": "build_a_sentence",
                        "prompt": "Arrange these words into a correct sentence: [wanted / she / which / to / know / I'm / colleges / considering]",
                        "answer": "She wanted to know which colleges I'm considering.",
                    },
                    {
                        "type": "email",
                        "prompt": "You ordered a laptop online, but it arrived with a cracked screen. Write an email to customer service to: (1) Describe the problem, (2) Explain how it affects you, (3) Request a solution.",
                        "time_limit": "7 minutes",
                        "rubric": "See scoring-rubrics.md — Email section",
                    },
                ],
            },
            "speaking": {
                "description": "口语能力（2 题）— 请录音或打字回答",
                "questions": [
                    {
                        "type": "interview",
                        "prompt": "Think about a teacher who had a significant impact on you. Who was this teacher, and why did they influence you?",
                        "time_limit": "45 seconds",
                    },
                    {
                        "type": "interview",
                        "prompt": "Some people prefer to study alone, while others prefer to study in groups. Which do you prefer, and why?",
                        "time_limit": "45 seconds",
                    },
                ],
            },
        },
    }

    diag_dir = target / "mock-tests" / "diagnostic"
    diag_dir.mkdir(parents=True, exist_ok=True)
    with open(diag_dir / "diagnostic-quiz.json", "w", encoding="utf-8") as f:
        json.dump(diagnostic, f, indent=2, ensure_ascii=False)

    # Also create a human-readable version
    md = "# 🏥 TOEFL 2026 诊断测验\n\n"
    md += "> 约 15–20 分钟，用来评估你的起始程度\n\n"
    md += "---\n\n"

    for section_key, section in diagnostic["sections"].items():
        md += f"## {section['description']}\n\n"
        for i, q in enumerate(section["questions"], 1):
            md += f"### 题 {i} ({q['type']})\n\n"
            if q["type"] == "complete_words":
                md += f"填入缺漏的字母：\n\n`{q['prompt']}`\n\n"
                md += f"<details><summary>答案</summary>\n\n{q['answer']}\n\n{q.get('explanation', '')}\n\n</details>\n\n"
            elif q["type"] == "daily_life":
                md += f"{q['prompt']}\n\n**{q['question']}**\n\n"
                for opt in q["options"]:
                    md += f"- {opt}\n"
                md += f"\n<details><summary>答案</summary>{q['answer']}</details>\n\n"
            elif q["type"] == "academic":
                md += f"> {q['passage']}\n\n**{q['question']}**\n\n"
                for opt in q["options"]:
                    md += f"- {opt}\n"
                md += f"\n<details><summary>答案</summary>{q['answer']}</details>\n\n"
            elif q["type"] == "build_a_sentence":
                md += f"{q['prompt']}\n\n"
                md += f"<details><summary>答案</summary>\n\n{q['answer']}\n\n</details>\n\n"
            elif q["type"] == "email":
                md += f"**情境：** {q['prompt']}\n\n"
                md += f"**时间限制：** {q['time_limit']}\n\n"
                md += "（请在下方或 `writing/drafts/diagnostic-email.md` 中作答）\n\n"
            elif q["type"] == "interview":
                md += f"**题目：** {q['prompt']}\n\n"
                md += f"**时间限制：** {q['time_limit']}\n\n"
                md += "（请录音或在 `speaking/feedback/diagnostic.md` 中打字回答）\n\n"
            md += "---\n\n"

    with open(diag_dir / "diagnostic-quiz.md", "w", encoding="utf-8") as f:
        f.write(md)

    print(f"   📋 诊断测验已生成：{diag_dir}")


def print_next_steps(target: Path, config: dict):
    """Print onboarding complete message with next steps."""
    print()
    print("=" * 55)
    print("✅ 初始化完成！")
    print("=" * 55)
    print()
    print(f"📂 备考文件夹：{target}")
    print(f"🎯 目标分数：{config['target_score']}")
    print(f"📅 考试日期：{config.get('exam_date') or '未设定'}")
    print(f"⏱️ 每日时间：{config['daily_minutes']} 分钟")
    print(f"📅 计划周数：{config['total_weeks']} 周")
    print(f"🔊 TTS 引擎：{config['tts_engine']}")
    print()
    print("📋 接下来的步骤：")
    print()
    print("  1️⃣  完成诊断测验")
    print(f"     打开 mock-tests/diagnostic/diagnostic-quiz.md")
    print(f"     告诉 AI：「我完成诊断测验了，帮我评估」")
    print()
    print("  2️⃣  安装必要工具")
    print(f"     pip install edge-tts genanki")
    print()
    print("  3️⃣  开始每日练习")
    print(f"     告诉 AI：「今天练什么？」")
    print()
    print("  💡 随时可以说：")
    print("     「帮我做口语练习」")
    print("     「批改我的写作」")
    print("     「生成本周 Anki 单词卡」")
    print("     「看我的进度」")
    print("     「做模拟考」")
    print()


def main():
    parser = argparse.ArgumentParser(description="TOEFL 备考系统初始化")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--non-interactive", action="store_true", help="Skip interactive prompts")
    parser.add_argument("--target-score", type=float, default=5.0)
    parser.add_argument("--exam-date", type=str, default="")
    parser.add_argument("--daily-minutes", type=int, default=30)
    parser.add_argument("--weeks", type=int, default=12)
    args = parser.parse_args()

    target = Path(args.target).resolve()

    # Check if already initialized
    config_path = target / "toefl-prep" / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            existing = json.load(f)
        if existing.get("initialized"):
            print("⚠️ 此文件夹已经初始化过了。")
            print(f"   config.json 建立于 {existing.get('created', '?')}")
            choice = input("   要重新初始化吗？(y/N): ").strip().lower()
            if choice != "y":
                print("   取消。")
                return

    # Gather parameters
    if args.non_interactive:
        params = {
            "target_score": args.target_score,
            "exam_date": args.exam_date,
            "daily_minutes": args.daily_minutes,
            "weeks": args.weeks,
            "self_level": "unknown",
            "weak_areas": ["unknown"],
            "tts_engine": "edge-tts",
        }
    else:
        params = interactive_onboarding()

    # Run scaffold
    print("\n🔧 正在建立备考环境...")
    from scaffold import scaffold as run_scaffold

    class ScaffoldArgs:
        pass

    sa = ScaffoldArgs()
    sa.target = str(target)
    sa.weeks = params["weeks"]
    sa.daily_minutes = params["daily_minutes"]
    sa.target_score = params["target_score"]
    sa.exam_date = params.get("exam_date", "")
    run_scaffold(sa)

    prep_dir = target / "toefl-prep"

    # Overwrite config with enriched version
    config = generate_config(prep_dir, params)

    # Generate diagnostic
    print("   📋 正在生成诊断测验...")
    generate_diagnostic(prep_dir)

    # Print next steps
    print_next_steps(prep_dir, config)


if __name__ == "__main__":
    main()
