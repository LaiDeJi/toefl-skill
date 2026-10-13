#!/usr/bin/env python3
"""
TOEFL 备考系统 — 每日追踪模组 (daily.py)
每天开启资料夹时的进入点：显示今日任务、追踪完成度、推进天数。

Usage:
    python daily.py --target ./toefl-prep/                    # 显示今日任务
    python daily.py --target ./toefl-prep/ --complete          # 标记今日完成
    python daily.py --target ./toefl-prep/ --advance           # 推进到下一天
    python daily.py --target ./toefl-prep/ --log-minutes 30    # 记录今日学习时间
    python daily.py --target ./toefl-prep/ --status            # 显示本周状态总览
"""

import argparse
import json
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_greeting():
    """Time-based greeting."""
    hour = datetime.now().hour
    if hour < 6:
        return "🌙 深夜好"
    elif hour < 12:
        return "☀️ 早安"
    elif hour < 18:
        return "🌤️ 午安"
    else:
        return "🌙 晚安"


def show_today(target: str):
    """Main daily check-in: show status + today's tasks."""
    config_path = os.path.join(target, "config.json")
    progress_path = os.path.join(target, "progress.json")

    if not os.path.exists(config_path):
        print("❌ 找不到 config.json。请先执行 init.py 初始化。")
        return

    config = load_json(config_path)
    progress = load_json(progress_path)

    week = config.get("current_week", 1)
    day = config.get("current_day", 1)
    daily_min = config.get("daily_minutes", 30)
    target_score = config.get("target_score", 5.0)
    exam_date = config.get("exam_date", "")
    streak = progress.get("streak_days", 0)
    total_min = progress.get("total_study_minutes", 0)

    # Header
    greeting = get_greeting()
    print(f"\n{greeting}！欢迎回来 📚")
    print("=" * 50)

    # Countdown
    if exam_date:
        try:
            exam_dt = datetime.strptime(exam_date, "%Y-%m-%d").date()
            days_left = (exam_dt - date.today()).days
            if days_left > 0:
                print(f"⏳ 距离考试：{days_left} 天")
        except ValueError:
            pass

    # Streak & stats
    streak_emoji = "🔥" if streak >= 7 else "✨" if streak >= 3 else "💪"
    print(f"{streak_emoji} 连续学习：{streak} 天 | 累计 {total_min} 分钟")
    print(f"🎯 目标：{target_score} | 📅 第 {week} 周 Day {day}")

    # Phase info
    phases = config.get("phase_schedule", {})
    current_phase = "unknown"
    for phase_name, phase_range in phases.items():
        if phase_range["start"] <= week <= phase_range["end"]:
            current_phase = phase_name
            break
    phase_names = {"foundation": "基础期 🌱", "intensive": "强化期 💪", "sprint": "冲刺期 🚀"}
    print(f"📌 阶段：{phase_names.get(current_phase, current_phase)}")
    print()

    # Diagnostic reminder
    if not config.get("diagnostic_completed", False):
        print("⚠️  你还没完成诊断测验！")
        print("   请先打开 mock-tests/diagnostic/diagnostic-quiz.md")
        print("   完成后告诉 AI：「我完成诊断测验了」")
        print()

    # Today's task
    if day <= 6:
        task_path = os.path.join(target, "plan", f"week-{week:02d}", "daily", f"day-{day}.md")
    else:
        task_path = os.path.join(target, "plan", f"week-{week:02d}", "daily", "review-day.md")

    print("📋 今日任务")
    print("-" * 50)

    if os.path.exists(task_path):
        with open(task_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Show just the checklist items
        for line in content.split("\n"):
            if line.strip().startswith("- ["):
                print(f"  {line.strip()}")
    else:
        print(f"  找不到 {task_path}")
        print(f"  请确认 plan/week-{week:02d}/daily/ 资料夹存在")

    print()
    print("💡 可用指令：")
    print("   「开始练习」— 按顺序引导今日练习")
    print("   「完成了」  — 标记今日完成并推进")
    print("   「看进度」  — 查看完整进度报告")
    print("   「弱项分析」— 分析需要加强的地方")

    # Show adaptive recommendation if available
    adaptive_path = os.path.join(target, "adaptive.json")
    if os.path.exists(adaptive_path):
        adaptive = load_json(adaptive_path)
        template = adaptive.get("daily_template")
        if template:
            print()
            print("🧠 自适应建议（基于你的表现数据）：")
            print("-" * 50)
            primary = template.get("primary", {})
            secondary = template.get("secondary", {})
            print(f"  📚 单字：{template.get('vocabulary', 5)} min")
            print(f"  🔴 主练 {primary.get('section', '?').capitalize()}：{primary.get('minutes', '?')} min")
            print(f"  🟡 副练 {secondary.get('section', '?').capitalize()}：{secondary.get('minutes', '?')} min")

            diff_levels = adaptive.get("difficulty_levels", {})
            if diff_levels:
                lvs = [f"{s[:1].upper()}=Lv{l}" for s, l in diff_levels.items()]
                print(f"  📏 难度：{' / '.join(lvs)}")


def mark_complete(target: str, minutes: int = None):
    """Mark today as complete and log study time."""
    config_path = os.path.join(target, "config.json")
    progress_path = os.path.join(target, "progress.json")

    config = load_json(config_path)
    progress = load_json(progress_path)

    week = config.get("current_week", 1)
    day = config.get("current_day", 1)
    daily_min = config.get("daily_minutes", 30)
    actual_min = minutes or daily_min

    today_str = date.today().isoformat()

    # Log entry
    progress.setdefault("daily_log", []).append({
        "date": today_str,
        "week": week,
        "day": day,
        "minutes": actual_min,
        "completed": True,
    })

    # Update totals
    progress["total_study_minutes"] = progress.get("total_study_minutes", 0) + actual_min

    # Update streak
    logs = progress.get("daily_log", [])
    dates = sorted(set(l["date"] for l in logs if l.get("completed")))
    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
        d2 = datetime.strptime(dates[i - 1], "%Y-%m-%d").date()
        if (d1 - d2).days == 1:
            streak += 1
        else:
            break
    progress["streak_days"] = streak
    progress["longest_streak"] = max(progress.get("longest_streak", 0), streak)

    # Update weekly completion
    week_key = f"week-{week:02d}"
    if week_key in progress.get("weekly_completion", {}):
        progress["weekly_completion"][week_key]["completed"] = min(
            progress["weekly_completion"][week_key].get("completed", 0) + 1,
            progress["weekly_completion"][week_key].get("total", 6),
        )

    progress["last_updated"] = datetime.now().isoformat()
    save_json(progress_path, progress)

    print(f"✅ 第 {week} 周 Day {day} 完成！（{actual_min} 分钟）")
    print(f"🔥 连续 {streak} 天")

    # Milestone checks
    total = progress.get("total_study_minutes", 0)
    milestones = [60, 300, 600, 1200, 1800, 3600]
    for m in milestones:
        if total - actual_min < m <= total:
            hours = m // 60
            print(f"🏆 里程碑达成：累计学习 {hours} 小时！")


def advance_day(target: str):
    """Move to the next day."""
    config_path = os.path.join(target, "config.json")
    config = load_json(config_path)

    week = config.get("current_week", 1)
    day = config.get("current_day", 1)
    total_weeks = config.get("total_weeks", 12)

    if day >= 7:  # End of week
        if week >= total_weeks:
            print("🎉 恭喜你完成了所有周的计划！")
            print("   接下来专注模拟考和考前调整吧。")
            return
        config["current_week"] = week + 1
        config["current_day"] = 1
        print(f"📅 推进到第 {week + 1} 周 Day 1")

        # Phase transition check
        phases = config.get("phase_schedule", {})
        for phase_name, phase_range in phases.items():
            if phase_range["start"] == week + 1:
                phase_names = {"foundation": "基础期 🌱", "intensive": "强化期 💪", "sprint": "冲刺期 🚀"}
                print(f"🎯 进入新阶段：{phase_names.get(phase_name, phase_name)}")
    else:
        config["current_day"] = day + 1
        print(f"📅 推进到第 {week} 周 Day {day + 1}")

    save_json(config_path, config)


def show_week_status(target: str):
    """Show weekly completion overview."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))

    week = config.get("current_week", 1)
    total_weeks = config.get("total_weeks", 12)

    print(f"\n📊 本周状态（第 {week} 周）")
    print("=" * 40)

    # Goals
    goals_path = os.path.join(target, "plan", f"week-{week:02d}", "goals.md")
    if os.path.exists(goals_path):
        with open(goals_path, "r", encoding="utf-8") as f:
            for line in f.read().split("\n"):
                if line.strip().startswith("- ["):
                    print(f"  {line.strip()}")

    # Weekly progress bar
    print()
    weekly = progress.get("weekly_completion", {})
    for wk in range(max(1, week - 2), min(total_weeks + 1, week + 3)):
        wk_key = f"week-{wk:02d}"
        w = weekly.get(wk_key, {"completed": 0, "total": 6})
        completed = w.get("completed", 0)
        total = w.get("total", 6)
        bar = "█" * completed + "░" * (total - completed)
        marker = " ◄ 目前" if wk == week else ""
        print(f"  Week {wk:2d}: [{bar}] {completed}/{total}{marker}")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 每日追踪模组")
    parser.add_argument("--target", default="./toefl-prep/")
    parser.add_argument("--complete", action="store_true", help="Mark today as complete")
    parser.add_argument("--advance", action="store_true", help="Advance to next day")
    parser.add_argument("--log-minutes", type=int, help="Log study minutes")
    parser.add_argument("--status", action="store_true", help="Show weekly status")
    args = parser.parse_args()

    if args.complete:
        mark_complete(args.target, args.log_minutes)
    elif args.advance:
        advance_day(args.target)
    elif args.status:
        show_week_status(args.target)
    elif args.log_minutes:
        mark_complete(args.target, args.log_minutes)
    else:
        show_today(args.target)


if __name__ == "__main__":
    main()
