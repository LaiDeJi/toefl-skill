#!/usr/bin/env python3
"""
TOEFL 备考系统 — 模拟考模块 (mock_test.py)
生成并管理完整的 TOEFL 模拟考。

Usage:
    python mock_test.py --target ./toefl-prep/ --action create   # 生成新模拟考
    python mock_test.py --target ./toefl-prep/ --action score --test 1 --reading 4.5 --listening 5.0 --speaking 4.0 --writing 4.5
    python mock_test.py --target ./toefl-prep/ --action history   # 查看历次成绩
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def create_mock_test(target: str):
    """Create a new mock test directory with all sections."""
    mock_dir = os.path.join(target, "mock-tests")
    os.makedirs(mock_dir, exist_ok=True)

    # Find next test number
    existing = [d for d in os.listdir(mock_dir) if d.startswith("test-") and os.path.isdir(os.path.join(mock_dir, d))]
    test_num = len(existing) + 1
    test_dir = os.path.join(mock_dir, f"test-{test_num:02d}")
    os.makedirs(test_dir, exist_ok=True)

    # Create test instruction file
    instructions = f"""# 📝 TOEFL 模拟考 #{test_num}

**日期：** {datetime.now().strftime('%Y-%m-%d')}
**总时间：** 约 90 分钟

---

## ⚙️ 考试前设定

- [ ] 找一个安静的地方
- [ ] 准备好计时器
- [ ] 准备纸笔（听力笔记用）
- [ ] 关闭手机通知

---

## 📖 Section 1: Reading（18–27 分钟）

请告诉 AI：「开始模拟考阅读」

AI 会生成：
- Complete the Words 题目
- Read in Daily Life 题目
- Academic Passage 题目

**重要：** 模拟 Module 1 → Module 2 的感觉。
前半段认真作答，正确率会影响后半段难度。

---

## 🎧 Section 2: Listening（18–27 分钟）

请告诉 AI：「开始模拟考听力」

AI 会生成音频（需 edge-tts）或念出内容：
- Choose a Response
- Conversations
- Announcements
- Academic Talks（如果进入 Hard 路线）

**重要：** 音频只听一次，不可倒带。

---

## 🎤 Section 3: Speaking（约 10 分钟）

请告诉 AI：「开始模拟考口语」

- Listen & Repeat：7 句跟读
- Take an Interview：4 题即兴回答（每题 45 秒）

**重要：** 没有准备时间！

---

## ✍️ Section 4: Writing（约 23 分钟）

请告诉 AI：「开始模拟考写作」

- Build a Sentence：10 题（约 7 分钟）
- Write an Email：1 题（7 分钟）
- Academic Discussion：1 题（10 分钟）

---

## 📊 考后评分

完成所有科目后，请告诉 AI：「模拟考结束，帮我评分」

AI 会：
1. 批改阅读和听力（客观题）
2. 评估口语（依 rubric）
3. 批改写作（依 rubric）
4. 生成成绩报告
5. 更新 progress.json

---

## 📋 成绩记录

| 科目 | 分数 (1–6) | 备注 |
|------|-----------|------|
| Reading | | |
| Listening | | |
| Speaking | | |
| Writing | | |
| **Total** | | |

## 检讨笔记

### 做得好的：


### 需要改进的：


### 下次模拟考前要特别练习的：

"""

    with open(os.path.join(test_dir, "instructions.md"), "w", encoding="utf-8") as f:
        f.write(instructions)

    # Create section subdirectories
    for section in ["reading", "listening", "speaking", "writing"]:
        os.makedirs(os.path.join(test_dir, section), exist_ok=True)

    # Create result placeholder
    result = {
        "test_number": test_num,
        "date": datetime.now().isoformat(),
        "status": "in_progress",
        "scores": {
            "reading": None,
            "listening": None,
            "speaking": None,
            "writing": None,
            "total": None,
        },
        "notes": "",
    }
    with open(os.path.join(test_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ 模拟考 #{test_num} 已建立：{test_dir}")
    print(f"   打开 instructions.md 开始考试")
    print(f"   或告诉 AI：「开始模拟考」")
    return test_dir


def score_mock_test(target: str, test_num: int, reading: float, listening: float, speaking: float, writing: float):
    """Record scores for a mock test."""
    test_dir = os.path.join(target, "mock-tests", f"test-{test_num:02d}")
    result_path = os.path.join(test_dir, "result.json")

    if not os.path.exists(result_path):
        print(f"❌ 找不到模拟考 #{test_num}")
        return

    result = json.load(open(result_path, "r"))
    total = round((reading + listening + speaking + writing) / 4 * 2) / 2

    result["status"] = "completed"
    result["scores"] = {
        "reading": reading,
        "listening": listening,
        "speaking": speaking,
        "writing": writing,
        "total": total,
    }
    result["completed_date"] = datetime.now().isoformat()

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Update progress.json
    progress_path = os.path.join(target, "progress.json")
    if os.path.exists(progress_path):
        progress = json.load(open(progress_path, "r"))
        progress.setdefault("mock_tests", []).append({
            "test_number": test_num,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reading": reading,
            "listening": listening,
            "speaking": speaking,
            "writing": writing,
            "total": total,
        })
        progress["latest_scores"] = {
            "reading": reading,
            "listening": listening,
            "speaking": speaking,
            "writing": writing,
            "total": total,
        }
        if len(progress["mock_tests"]) == 1:
            progress["baseline_scores"] = progress["latest_scores"].copy()

        progress["last_updated"] = datetime.now().isoformat()
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    # Print report
    print(f"\n📊 模拟考 #{test_num} 成绩报告")
    print("=" * 40)
    print(f"  Reading:   {reading:.1f}")
    print(f"  Listening: {listening:.1f}")
    print(f"  Speaking:  {speaking:.1f}")
    print(f"  Writing:   {writing:.1f}")
    print(f"  ──────────────────")
    print(f"  Total:     {total:.1f}")
    print()

    # CEFR mapping
    if total >= 5.0:
        print("  CEFR: C1 — 流畅学术交流 🌟")
    elif total >= 4.0:
        print("  CEFR: B2 — 独立用户 👍")
    elif total >= 3.0:
        print("  CEFR: B1 — 中级 📚")
    else:
        print("  CEFR: A2/B1 — 需要更多练习 💪")

    # Weak area analysis
    scores = {"reading": reading, "listening": listening, "speaking": speaking, "writing": writing}
    weakest = min(scores, key=scores.get)
    strongest = max(scores, key=scores.get)
    print(f"\n  💪 最强科目：{strongest.capitalize()} ({scores[strongest]:.1f})")
    print(f"  ⚠️  最弱科目：{weakest.capitalize()} ({scores[weakest]:.1f})")
    print(f"  📌 建议：集中加强 {weakest.capitalize()}")


def show_history(target: str):
    """Show mock test history with trends."""
    progress_path = os.path.join(target, "progress.json")
    if not os.path.exists(progress_path):
        print("❌ 找不到 progress.json")
        return

    progress = json.load(open(progress_path, "r"))
    mocks = progress.get("mock_tests", [])

    if not mocks:
        print("📝 还没有模拟考记录。")
        print("   执行 mock_test.py --action create 开始第一次模拟考")
        return

    print("\n📊 模拟考历史")
    print("=" * 65)
    print(f"{'#':<4} {'日期':<12} {'R':<6} {'L':<6} {'S':<6} {'W':<6} {'Total':<6}")
    print("-" * 65)

    for m in mocks:
        print(f"#{m['test_number']:<3} {m['date']:<12} {m['reading']:<6.1f} {m['listening']:<6.1f} {m['speaking']:<6.1f} {m['writing']:<6.1f} {m['total']:<6.1f}")

    if len(mocks) >= 2:
        first = mocks[0]
        last = mocks[-1]
        diff = last["total"] - first["total"]
        print(f"\n📈 进步幅度：{diff:+.1f}（第一次 {first['total']:.1f} → 最新 {last['total']:.1f}）")

        for section in ["reading", "listening", "speaking", "writing"]:
            s_diff = last[section] - first[section]
            emoji = "📈" if s_diff > 0 else "📉" if s_diff < 0 else "➡️"
            print(f"   {emoji} {section.capitalize()}: {s_diff:+.1f}")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 模拟考模块")
    parser.add_argument("--target", default="./toefl-prep/")
    parser.add_argument("--action", choices=["create", "score", "history"], default="create")
    parser.add_argument("--test", type=int, help="Test number (for scoring)")
    parser.add_argument("--reading", type=float)
    parser.add_argument("--listening", type=float)
    parser.add_argument("--speaking", type=float)
    parser.add_argument("--writing", type=float)
    args = parser.parse_args()

    if args.action == "create":
        create_mock_test(args.target)
    elif args.action == "score":
        if all([args.test, args.reading, args.listening, args.speaking, args.writing]):
            score_mock_test(args.target, args.test, args.reading, args.listening, args.speaking, args.writing)
        else:
            print("❌ 需要提供：--test N --reading X --listening X --speaking X --writing X")
    elif args.action == "history":
        show_history(args.target)


if __name__ == "__main__":
    main()
