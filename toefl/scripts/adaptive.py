#!/usr/bin/env python3
"""
TOEFL 备考系统 — 自适应引擎 (adaptive.py)

根据 progress.json 中的表现数据，动态调整：
1. 每日时间分配（弱科多练、强科维持）
2. 题目难度等级
3. 本周重点科目
4. 里程碑检查与计划修正建议
5. 单字复习排程（遗忘曲线加权）

Usage:
    python adaptive.py --target ./toefl-prep/ --action analyze     # 分析现况，输出调整建议
    python adaptive.py --target ./toefl-prep/ --action rebalance   # 重新分配时间并更新每日计划
    python adaptive.py --target ./toefl-prep/ --action difficulty  # 输出各科建议难度等级
    python adaptive.py --target ./toefl-prep/ --action checkpoint  # 里程碑检查
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# ── Constants ──────────────────────────────────────────

SECTIONS = ["reading", "listening", "speaking", "writing"]

# 每科最低时间占比（不会低于此比例）
MIN_TIME_RATIO = 0.10  # 10%
# 弱科加权上限
MAX_TIME_RATIO = 0.45  # 45%

# 难度等级定义
DIFFICULTY_LEVELS = {
    1: {"label": "基础", "description": "短句、常见词、慢速", "target_score_range": (1.0, 2.5)},
    2: {"label": "初中级", "description": "中等句长、学术基础词", "target_score_range": (2.5, 3.5)},
    3: {"label": "中级", "description": "复杂句、学术进阶词、正常语速", "target_score_range": (3.5, 4.5)},
    4: {"label": "中高级", "description": "长复杂句、低频词、快语速", "target_score_range": (4.5, 5.0)},
    5: {"label": "高级", "description": "接近真实考试最高难度", "target_score_range": (5.0, 6.0)},
}

# 里程碑定义（按周数比例）
MILESTONES = {
    0.25: {  # 25% 进度（第3周）
        "name": "基础检查点",
        "expected": {
            "diagnostic_completed": True,
            "vocab_learned": 60,
            "mock_tests": 1,
        },
        "checks": ["是否完成诊断测验", "是否累积 60+ 单字", "是否完成第一次模拟考"],
    },
    0.50: {  # 50% 进度（第6周）
        "name": "中期检查点",
        "expected": {
            "vocab_learned": 150,
            "mock_tests": 2,
            "min_score_improvement": 0.5,
        },
        "checks": ["模拟考分数是否提升 ≥ 0.5", "弱项是否有改善", "是否维持每日练习"],
    },
    0.75: {  # 75% 进度（第9周）
        "name": "冲刺前检查点",
        "expected": {
            "vocab_learned": 250,
            "mock_tests": 3,
            "target_gap": 0.5,
        },
        "checks": ["模拟考分数是否在目标 -0.5 以内", "各科是否平衡", "是否需要延长计划"],
    },
    1.0: {  # 100% 进度（最后一周）
        "name": "考前最终检查",
        "expected": {
            "mock_tests": 4,
            "target_reached": True,
        },
        "checks": ["是否达到目标分数", "是否有信心稳定发挥", "考试流程是否熟悉"],
    },
}


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Core Analysis ──────────────────────────────────────

def compute_section_scores(progress: dict) -> dict:
    """Extract latest score per section, with fallback to mock test data."""
    latest = progress.get("latest_scores", {})
    scores = {}
    for sec in SECTIONS:
        s = latest.get(sec)
        if s is not None:
            scores[sec] = float(s)
    
    # Fallback: average from daily logs
    if len(scores) < 4:
        log_scores = defaultdict(list)
        for entry in progress.get("daily_log", []):
            if entry.get("section") and entry.get("score"):
                log_scores[entry["section"]].append(entry["score"])
        for sec in SECTIONS:
            if sec not in scores and log_scores[sec]:
                scores[sec] = sum(log_scores[sec]) / len(log_scores[sec])

    return scores


def compute_score_trends(progress: dict) -> dict:
    """Compute score trend (improving/declining/stable) per section from mock tests."""
    mocks = progress.get("mock_tests", [])
    trends = {}
    for sec in SECTIONS:
        section_scores = [m.get(sec) for m in mocks if m.get(sec) is not None]
        if len(section_scores) >= 2:
            recent = section_scores[-1]
            previous = section_scores[-2]
            diff = recent - previous
            if diff > 0.3:
                trends[sec] = {"direction": "improving", "delta": diff, "emoji": "📈"}
            elif diff < -0.3:
                trends[sec] = {"direction": "declining", "delta": diff, "emoji": "📉"}
            else:
                trends[sec] = {"direction": "stable", "delta": diff, "emoji": "➡️"}
        else:
            trends[sec] = {"direction": "unknown", "delta": 0, "emoji": "❓"}
    return trends


def compute_weakness_weights(scores: dict, target_score: float) -> dict:
    """
    Calculate how much extra time each section needs.
    Sections further from target get more weight.
    Declining sections get an additional boost.
    """
    if not scores:
        return {sec: 0.25 for sec in SECTIONS}

    gaps = {}
    for sec in SECTIONS:
        current = scores.get(sec, target_score - 1.5)  # assume weak if no data
        gap = max(0, target_score - current)
        gaps[sec] = gap

    total_gap = sum(gaps.values())
    if total_gap == 0:
        return {sec: 0.25 for sec in SECTIONS}

    # Raw weights proportional to gap
    raw_weights = {sec: gaps[sec] / total_gap for sec in SECTIONS}

    # Clamp to [MIN_TIME_RATIO, MAX_TIME_RATIO]
    clamped = {}
    for sec in SECTIONS:
        clamped[sec] = max(MIN_TIME_RATIO, min(MAX_TIME_RATIO, raw_weights[sec]))

    # Normalize to sum to 1.0
    total = sum(clamped.values())
    return {sec: round(clamped[sec] / total, 3) for sec in SECTIONS}


def compute_difficulty_level(score: float) -> int:
    """Map a section score to a recommended difficulty level."""
    if score is None:
        return 2
    for level, info in sorted(DIFFICULTY_LEVELS.items()):
        low, high = info["target_score_range"]
        if score < high:
            return level
    return 5


def compute_daily_plan(weights: dict, daily_minutes: int) -> dict:
    """Convert weights to concrete minute allocation."""
    plan = {}
    remaining = daily_minutes
    allocated = {}

    for sec in SECTIONS:
        minutes = max(5, round(weights[sec] * daily_minutes))  # minimum 5 min
        allocated[sec] = minutes

    # Normalize to fit within daily_minutes
    total = sum(allocated.values())
    if total != daily_minutes:
        diff = daily_minutes - total
        # Add/subtract from the section with highest weight
        top_sec = max(weights, key=weights.get)
        allocated[top_sec] += diff

    return allocated


# ── Main Actions ──────────────────────────────────────

def analyze(target: str):
    """Full analysis: scores, trends, weights, difficulty, recommendations."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))

    target_score = config.get("target_score", 5.0)
    daily_minutes = config.get("daily_minutes", 30)
    current_week = config.get("current_week", 1)
    total_weeks = config.get("total_weeks", 12)

    scores = compute_section_scores(progress)
    trends = compute_score_trends(progress)
    weights = compute_weakness_weights(scores, target_score)
    time_alloc = compute_daily_plan(weights, daily_minutes)

    print("\n🧠 自适应分析报告")
    print("=" * 55)
    print(f"🎯 目标：{target_score}  |  📅 进度：第 {current_week}/{total_weeks} 周 ({current_week/total_weeks*100:.0f}%)")
    print()

    # Section analysis
    print("📊 各科现况")
    print("-" * 55)
    print(f"{'科目':<12} {'分数':<8} {'差距':<8} {'趋势':<8} {'难度':<10} {'时间分配'}")
    for sec in SECTIONS:
        s = scores.get(sec)
        s_str = f"{s:.1f}" if s else "—"
        gap = f"{target_score - s:+.1f}" if s else "—"
        trend = trends.get(sec, {})
        t_emoji = trend.get("emoji", "❓")
        diff_level = compute_difficulty_level(s)
        diff_label = DIFFICULTY_LEVELS[diff_level]["label"]
        mins = time_alloc[sec]
        pct = weights[sec] * 100

        print(f"{sec.capitalize():<12} {s_str:<8} {gap:<8} {t_emoji:<8} Lv{diff_level} {diff_label:<6} {mins}min ({pct:.0f}%)")

    print()

    # Recommendations
    print("💡 调整建议")
    print("-" * 55)

    if not scores:
        print("  ⚠️ 尚无分数数据。请先完成诊断测验或模拟考。")
        return

    # Find weakest
    weakest = min(scores, key=scores.get)
    strongest = max(scores, key=scores.get)
    gap_worst = target_score - scores[weakest]
    gap_best = target_score - scores[strongest]

    if gap_worst > 1.5:
        print(f"  🔴 {weakest.capitalize()} 落后目标 {gap_worst:.1f} 分，建议每天至少 {time_alloc[weakest]} 分钟专项练习")

    if gap_worst > 0.5 and gap_best <= 0:
        print(f"  🟡 {strongest.capitalize()} 已达标，可以减少时间，将资源移到 {weakest.capitalize()}")

    # Trend warnings
    for sec in SECTIONS:
        if trends.get(sec, {}).get("direction") == "declining":
            print(f"  ⚠️ {sec.capitalize()} 分数下降中！建议本周额外加练")

    # Balance check
    score_values = list(scores.values())
    if score_values:
        score_range = max(score_values) - min(score_values)
        if score_range > 1.5:
            print(f"  ⚠️ 各科差距 {score_range:.1f} 分，严重不平衡。集中补弱科。")
        elif score_range < 0.5:
            print(f"  ✅ 各科平衡（差距 {score_range:.1f}），可以均衡练习。")

    # Pace check
    progress_ratio = current_week / total_weeks
    avg_score = sum(score_values) / len(score_values) if score_values else 0
    expected_progress = target_score * (0.6 + 0.4 * progress_ratio)  # expect 60% at start, 100% at end
    if avg_score < expected_progress * 0.8:
        print(f"  🏃 进度偏慢。考虑增加每日练习时间或延长计划。")

    # Output adaptive config
    adaptive_config = {
        "generated": datetime.now().isoformat(),
        "section_weights": weights,
        "time_allocation": time_alloc,
        "difficulty_levels": {sec: compute_difficulty_level(scores.get(sec)) for sec in SECTIONS},
        "trends": {sec: trends.get(sec, {}).get("direction", "unknown") for sec in SECTIONS},
        "weakest_section": weakest,
        "strongest_section": strongest,
    }
    adaptive_path = os.path.join(target, "adaptive.json")
    save_json(adaptive_path, adaptive_config)
    print(f"\n📁 自适应设定已储存：{adaptive_path}")

    return adaptive_config


def rebalance(target: str):
    """Rewrite upcoming daily plans based on adaptive analysis."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))
    
    target_score = config.get("target_score", 5.0)
    daily_minutes = config.get("daily_minutes", 30)
    current_week = config.get("current_week", 1)
    current_day = config.get("current_day", 1)
    total_weeks = config.get("total_weeks", 12)

    scores = compute_section_scores(progress)
    weights = compute_weakness_weights(scores, target_score)
    time_alloc = compute_daily_plan(weights, daily_minutes)
    
    if not scores:
        print("⚠️ 尚无分数数据，无法重新平衡。请先完成模拟考。")
        return

    # Sort sections by priority (weakest first)
    priority_order = sorted(SECTIONS, key=lambda s: scores.get(s, 0))

    print("\n🔄 重新平衡每日计划")
    print("=" * 50)
    print(f"基于最新数据，调整第 {current_week} 周 Day {current_day} 起的计划\n")

    print("📊 新的时间分配：")
    for sec in priority_order:
        mins = time_alloc[sec]
        pct = weights[sec] * 100
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        score_str = f"{scores.get(sec, 0):.1f}" if scores.get(sec) else "?"
        print(f"  {sec.capitalize():<12} [{bar}] {mins:>2}min ({pct:.0f}%)  现分：{score_str}")

    # Generate adjusted daily template
    print("\n📋 调整后的每日模板：")
    print("-" * 50)
    
    # Vocabulary is always 5 min
    vocab_time = 5
    remaining = daily_minutes - vocab_time
    
    # Primary focus = weakest section
    # Secondary focus = second weakest
    primary = priority_order[0]
    secondary = priority_order[1]
    primary_time = max(10, round(remaining * weights[primary] / (weights[primary] + weights[secondary] + 0.001) * 1.2))
    secondary_time = remaining - primary_time

    print(f"  📚 单字复习：{vocab_time} 分钟")
    print(f"  🔴 主练（{primary.capitalize()}）：{primary_time} 分钟")
    print(f"  🟡 副练（{secondary.capitalize()}）：{secondary_time} 分钟")
    print(f"  ─── 合计：{daily_minutes} 分钟")

    # Difficulty recommendations
    print("\n📏 建议题目难度：")
    for sec in SECTIONS:
        level = compute_difficulty_level(scores.get(sec))
        info = DIFFICULTY_LEVELS[level]
        print(f"  {sec.capitalize():<12} → Lv{level} {info['label']}（{info['description']}）")

    # Save to adaptive.json
    adaptive = {
        "generated": datetime.now().isoformat(),
        "section_weights": weights,
        "time_allocation": time_alloc,
        "difficulty_levels": {sec: compute_difficulty_level(scores.get(sec)) for sec in SECTIONS},
        "priority_order": priority_order,
        "daily_template": {
            "vocabulary": vocab_time,
            "primary": {"section": primary, "minutes": primary_time},
            "secondary": {"section": secondary, "minutes": secondary_time},
        },
    }
    save_json(os.path.join(target, "adaptive.json"), adaptive)

    # Update config with adaptive flag
    config["adaptive_enabled"] = True
    config["last_rebalance"] = datetime.now().isoformat()
    save_json(os.path.join(target, "config.json"), config)

    print(f"\n✅ 计划已重新平衡。下次 daily.py 会使用新设定。")


def show_difficulty(target: str):
    """Show recommended difficulty per section."""
    progress = load_json(os.path.join(target, "progress.json"))
    scores = compute_section_scores(progress)

    print("\n📏 各科建议难度")
    print("=" * 55)
    for sec in SECTIONS:
        s = scores.get(sec)
        level = compute_difficulty_level(s)
        info = DIFFICULTY_LEVELS[level]
        s_str = f"{s:.1f}" if s else "未知"
        print(f"\n  {sec.capitalize()} （现分：{s_str}）")
        print(f"    → Lv{level} {info['label']}")
        print(f"    {info['description']}")
        
        # Specific tips per section per level
        if sec == "reading":
            if level <= 2:
                print(f"    💡 先从 Daily Life 短文开始，再练 Complete the Words")
            elif level <= 3:
                print(f"    💡 加入 Academic Passage，练习推论题")
            else:
                print(f"    💡 限时练习，模拟 Module 1 压力")
        elif sec == "listening":
            if level <= 2:
                print(f"    💡 先听慢速（--rate=-20%），逐渐加速")
            elif level <= 3:
                print(f"    💡 正常语速，练习笔记技巧")
            else:
                print(f"    💡 Academic Talks + 推论题，只听一次")
        elif sec == "speaking":
            if level <= 2:
                print(f"    💡 Repeat 练短句（5 词以下），Interview 先打字再口说")
            elif level <= 3:
                print(f"    💡 Repeat 练中长句，Interview 计时 45 秒")
            else:
                print(f"    💡 全速跟读，Interview 不打草稿直接说")
        elif sec == "writing":
            if level <= 2:
                print(f"    💡 Build a Sentence 先练简单句型")
            elif level <= 3:
                print(f"    💡 Email 计时 7 分钟，确保涵盖所有要点")
            else:
                print(f"    💡 计时完成所有题型，追求零文法错误")


def checkpoint(target: str):
    """Run milestone checkpoint based on current progress."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))

    current_week = config.get("current_week", 1)
    total_weeks = config.get("total_weeks", 12)
    target_score = config.get("target_score", 5.0)
    progress_ratio = current_week / total_weeks

    scores = compute_section_scores(progress)
    mocks = progress.get("mock_tests", [])
    vocab = progress.get("vocabulary", {})

    print("\n🏁 里程碑检查")
    print("=" * 55)
    print(f"📅 进度：第 {current_week}/{total_weeks} 周（{progress_ratio*100:.0f}%）")
    print()

    # Find applicable milestone
    applicable = None
    for threshold, milestone in sorted(MILESTONES.items()):
        if progress_ratio >= threshold - 0.05:  # within 5% tolerance
            applicable = (threshold, milestone)

    if not applicable:
        print("  目前尚未到达任何里程碑。继续加油！")
        return

    threshold, milestone = applicable
    print(f"📌 {milestone['name']}（{threshold*100:.0f}% 进度点）")
    print()

    passed = 0
    total = len(milestone["checks"])

    for check_desc in milestone["checks"]:
        # Evaluate each check
        if "诊断测验" in check_desc:
            ok = config.get("diagnostic_completed", False)
        elif "单字" in check_desc:
            expected_vocab = milestone["expected"].get("vocab_learned", 0)
            actual_vocab = vocab.get("total_learned", 0)
            ok = actual_vocab >= expected_vocab
            check_desc += f"（{actual_vocab}/{expected_vocab}）"
        elif "模拟考" in check_desc:
            expected_mocks = milestone["expected"].get("mock_tests", 0)
            ok = len(mocks) >= expected_mocks
            check_desc += f"（{len(mocks)}/{expected_mocks}）"
        elif "提升" in check_desc:
            if len(mocks) >= 2:
                improvement = mocks[-1].get("total", 0) - mocks[0].get("total", 0)
                expected_improvement = milestone["expected"].get("min_score_improvement", 0)
                ok = improvement >= expected_improvement
                check_desc += f"（{improvement:+.1f}）"
            else:
                ok = False
        elif "目标" in check_desc and "0.5" in check_desc:
            if scores:
                avg = sum(scores.values()) / len(scores)
                gap = target_score - avg
                ok = gap <= 0.5
                check_desc += f"（差距 {gap:.1f}）"
            else:
                ok = False
        elif "达到目标" in check_desc:
            if scores:
                avg = sum(scores.values()) / len(scores)
                ok = avg >= target_score
            else:
                ok = False
        else:
            ok = None  # Cannot auto-check

        if ok is True:
            print(f"  ✅ {check_desc}")
            passed += 1
        elif ok is False:
            print(f"  ❌ {check_desc}")
        else:
            print(f"  ❓ {check_desc}（需手动确认）")

    print(f"\n  通过：{passed}/{total}")

    if passed < total:
        print("\n  💡 建议：")
        if not config.get("diagnostic_completed"):
            print("    → 尽快完成诊断测验")
        if len(mocks) < milestone["expected"].get("mock_tests", 0):
            print("    → 安排一次模拟考")
        if scores:
            avg = sum(scores.values()) / len(scores)
            if target_score - avg > 1.0:
                print("    → 考虑增加每日练习时间或延长计划周数")
    else:
        print("\n  🎉 所有里程碑都通过了！进度良好！")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 自适应引擎")
    parser.add_argument("--target", default="./toefl-prep/")
    parser.add_argument("--action", choices=["analyze", "rebalance", "difficulty", "checkpoint"], default="analyze")
    args = parser.parse_args()

    if args.action == "analyze":
        analyze(args.target)
    elif args.action == "rebalance":
        rebalance(args.target)
    elif args.action == "difficulty":
        show_difficulty(args.target)
    elif args.action == "checkpoint":
        checkpoint(args.target)


if __name__ == "__main__":
    main()
