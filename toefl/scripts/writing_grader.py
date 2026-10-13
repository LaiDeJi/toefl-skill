#!/usr/bin/env python3
"""
TOEFL 备考系统 — 写作批改模块 (writing_grader.py)
生成写作题目（Build a Sentence / Email / Academic Discussion），
提供 AI 批改框架和评分标准。

Usage:
    python writing_grader.py --type sentence --output ./writing/ --count 10
    python writing_grader.py --type email --output ./writing/
    python writing_grader.py --type discussion --output ./writing/
    python writing_grader.py --type full --output ./writing/   # 完整一回
"""

import argparse
import json
import os
import random
from datetime import datetime
from pathlib import Path

# ── Build a Sentence 题库 ──────────────────────────────

BUILD_SENTENCES = [
    {"words": ["she", "wanted", "to", "know", "which", "colleges", "I'm", "considering"], "extra": None, "answer": "She wanted to know which colleges I'm considering.", "grammar_point": "间接问句（wh- clause）"},
    {"words": ["the", "tour", "guides", "who", "showed", "us", "around", "were", "fantastic"], "extra": "the old city", "answer": "The tour guides who showed us around the old city were fantastic.", "grammar_point": "关系子句（who）"},
    {"words": ["have", "you", "decided", "where", "to", "go", "for", "vacation", "yet"], "extra": None, "answer": "Have you decided where to go for vacation yet?", "grammar_point": "疑问句 + 间接问句"},
    {"words": ["the", "professor", "explained", "how", "the", "experiment", "should", "be", "conducted"], "extra": None, "answer": "The professor explained how the experiment should be conducted.", "grammar_point": "间接问句 + 被动语态"},
    {"words": ["students", "are", "required", "to", "submit", "their", "assignments", "by", "Friday"], "extra": None, "answer": "Students are required to submit their assignments by Friday.", "grammar_point": "被动语态 + 不定词"},
    {"words": ["the", "building", "that", "was", "constructed", "in", "1920", "needs", "renovation"], "extra": None, "answer": "The building that was constructed in 1920 needs renovation.", "grammar_point": "关系子句 + 被动语态"},
    {"words": ["I", "wonder", "whether", "the", "library", "is", "open", "on", "weekends"], "extra": None, "answer": "I wonder whether the library is open on weekends.", "grammar_point": "间接问句（whether）"},
    {"words": ["the", "research", "findings", "suggest", "that", "sleep", "affects", "memory"], "extra": "significantly", "answer": "The research findings suggest that sleep significantly affects memory.", "grammar_point": "名词子句 + 副词位置"},
    {"words": ["neither", "the", "students", "nor", "the", "teacher", "was", "satisfied", "with", "the", "results"], "extra": None, "answer": "Neither the students nor the teacher was satisfied with the results.", "grammar_point": "neither...nor 主词动词一致"},
    {"words": ["it", "is", "essential", "that", "every", "participant", "sign", "the", "consent", "form"], "extra": None, "answer": "It is essential that every participant sign the consent form.", "grammar_point": "假设语气（subjunctive）"},
    {"words": ["the", "more", "you", "practice", "the", "better", "your", "pronunciation", "will", "become"], "extra": None, "answer": "The more you practice, the better your pronunciation will become.", "grammar_point": "the more...the more 比较句型"},
    {"words": ["had", "I", "known", "about", "the", "deadline", "I", "would", "have", "submitted", "earlier"], "extra": None, "answer": "Had I known about the deadline, I would have submitted earlier.", "grammar_point": "倒装假设语气（第三条件句）"},
]

# ── Email 题库 ──────────────────────────────────────

EMAIL_PROMPTS = [
    {
        "scenario": "You recently attended a workshop at the career center but found the content outdated and not relevant to your field. You want to provide constructive feedback.",
        "recipient": "Career Center Director",
        "bullets": [
            "Describe what you expected from the workshop",
            "Explain what was disappointing about the content",
            "Suggest improvements for future workshops",
        ],
        "tone": "formal-polite",
    },
    {
        "scenario": "Your roommate has been playing loud music late at night, and it's affecting your sleep and studies. You've tried talking to them but nothing changed.",
        "recipient": "Resident Advisor (RA)",
        "bullets": [
            "Describe the noise problem",
            "Explain how it has affected you",
            "Ask the RA to help resolve the situation",
        ],
        "tone": "semi-formal",
    },
    {
        "scenario": "You ordered a textbook online for your class, but the wrong edition was delivered. The class starts next week.",
        "recipient": "Online Bookstore Customer Service",
        "bullets": [
            "Explain what you ordered vs. what you received",
            "Describe why the correct edition is urgent",
            "Request a specific solution (replacement or refund)",
        ],
        "tone": "formal-polite",
    },
    {
        "scenario": "You want to volunteer at a local animal shelter you found online. You have some experience with pets.",
        "recipient": "Volunteer Coordinator",
        "bullets": [
            "Introduce yourself and explain your interest",
            "Describe any relevant experience you have",
            "Ask about the application process and schedule",
        ],
        "tone": "semi-formal",
    },
    {
        "scenario": "You missed an important exam due to a family emergency. You need to arrange a make-up exam.",
        "recipient": "Professor Chen",
        "bullets": [
            "Explain why you missed the exam",
            "Provide any documentation you can offer",
            "Request a make-up exam and suggest possible dates",
        ],
        "tone": "formal-polite",
    },
]

# ── Academic Discussion 题库 ──────────────────────────

DISCUSSION_PROMPTS = [
    {
        "professor": "Professor Williams",
        "topic": "Many universities now offer fully online degree programs. Do you think online degrees should be valued the same as traditional in-person degrees by employers? Why or why not?",
        "student_a": {"name": "Maria", "position": "I think online degrees should be equally valued. The course content is the same, and online students often demonstrate strong self-discipline and time management skills that employers should appreciate."},
        "student_b": {"name": "James", "position": "I disagree. In-person education offers networking opportunities, hands-on lab work, and face-to-face discussions that online programs simply cannot replicate. Employers have reason to prefer traditional degrees."},
    },
    {
        "professor": "Professor Kim",
        "topic": "Some cities are banning single-use plastic bags to reduce environmental pollution. Do you think this is an effective policy, or are there better alternatives?",
        "student_a": {"name": "Tanya", "position": "Banning plastic bags is a great first step. It forces consumers to adopt reusable alternatives and sends a clear message that environmental protection matters."},
        "student_b": {"name": "David", "position": "While I support reducing plastic waste, outright bans can be inconvenient and may lead to other problems, like increased paper bag production. I think a small tax on plastic bags would be more effective."},
    },
    {
        "professor": "Professor Patel",
        "topic": "Should high school students be required to do community service hours in order to graduate? Some argue it builds character, while others say it should be voluntary.",
        "student_a": {"name": "Lin", "position": "Required community service teaches students responsibility and exposes them to different parts of their community. It can even help them discover passions they didn't know they had."},
        "student_b": {"name": "Sophie", "position": "Forcing students to volunteer defeats the purpose of volunteerism. If it's mandatory, students may just do the minimum and learn nothing meaningful from the experience."},
    },
    {
        "professor": "Professor Garcia",
        "topic": "With the rise of artificial intelligence, some experts predict that many jobs will become automated in the next decade. Should universities change their curricula to prepare students for an AI-driven job market?",
        "student_a": {"name": "Chen", "position": "Absolutely. Universities should add more courses on AI literacy, data analysis, and critical thinking so graduates can work alongside AI rather than be replaced by it."},
        "student_b": {"name": "Omar", "position": "I think universities should focus on uniquely human skills like creativity, empathy, and leadership. These are harder for AI to replicate and will remain valuable regardless of technological change."},
    },
]


def generate_sentence_exercises(output_dir: str, count: int = 10):
    """Generate Build a Sentence exercises."""
    exercise_dir = os.path.join(output_dir, "prompts", f"sentences-{datetime.now().strftime('%Y%m%d-%H%M')}")
    os.makedirs(exercise_dir, exist_ok=True)

    selected = random.sample(BUILD_SENTENCES, min(count, len(BUILD_SENTENCES)))

    md = "# Build a Sentence 练习\n\n"
    md += "**规则：** 将打乱的单词排列成正确的句子。可能有一个多余的干扰词。\n"
    md += "**计分：** 全对 1 分，有任何错误 0 分。\n\n"

    for i, s in enumerate(selected, 1):
        words = s["words"][:]
        if s.get("extra"):
            words.append(s["extra"])
        random.shuffle(words)

        md += f"### 第 {i} 题\n\n"
        md += f"**单词：** {' / '.join(words)}\n\n"
        md += f"**我的答案：** ________________________________\n\n"
        md += f"<details><summary>正确答案</summary>\n\n"
        md += f"{s['answer']}\n\n"
        md += f"**文法考点：** {s['grammar_point']}\n\n</details>\n\n---\n\n"

    # Score summary
    md += "## 成绩\n\n"
    md += f"答对：____ / {len(selected)}\n\n"

    with open(os.path.join(exercise_dir, "exercise.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ Build a Sentence 练习已生成：{exercise_dir}（{len(selected)} 题）")
    return exercise_dir


def generate_email_exercise(output_dir: str, prompt_index: int = None):
    """Generate Write an Email exercise."""
    exercise_dir = os.path.join(output_dir, "prompts", f"email-{datetime.now().strftime('%Y%m%d-%H%M')}")
    os.makedirs(exercise_dir, exist_ok=True)

    if prompt_index is not None and 0 <= prompt_index < len(EMAIL_PROMPTS):
        prompt = EMAIL_PROMPTS[prompt_index]
    else:
        prompt = random.choice(EMAIL_PROMPTS)

    md = "# Write an Email 练习\n\n"
    md += f"**时间限制：** 7 分钟\n"
    md += f"**目标字数：** 100–180 字\n\n"
    md += "---\n\n"
    md += f"## 情境\n\n{prompt['scenario']}\n\n"
    md += f"**收件人：** {prompt['recipient']}\n\n"
    md += "**请在 email 中涵盖以下要点：**\n\n"
    for b in prompt["bullets"]:
        md += f"- {b}\n"
    md += f"\n**建议语气：** {prompt['tone']}\n\n"
    md += "---\n\n"
    md += "## 我的回答\n\n"
    md += "To: _______________\n\n"
    md += "Subject: _______________\n\n"
    md += "Dear _______________,\n\n"
    md += "\n\n\n\n"
    md += "Best regards,\n[Your Name]\n\n"
    md += "---\n\n"
    md += "## 批改结果\n\n（完成后请 AI 批改：「帮我批改这篇 email」）\n"

    with open(os.path.join(exercise_dir, "exercise.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ Email 练习已生成：{exercise_dir}")
    return exercise_dir


def generate_discussion_exercise(output_dir: str, prompt_index: int = None):
    """Generate Academic Discussion exercise."""
    exercise_dir = os.path.join(output_dir, "prompts", f"discussion-{datetime.now().strftime('%Y%m%d-%H%M')}")
    os.makedirs(exercise_dir, exist_ok=True)

    if prompt_index is not None and 0 <= prompt_index < len(DISCUSSION_PROMPTS):
        prompt = DISCUSSION_PROMPTS[prompt_index]
    else:
        prompt = random.choice(DISCUSSION_PROMPTS)

    md = "# Write for an Academic Discussion 练习\n\n"
    md += f"**时间限制：** 10 分钟\n"
    md += f"**目标字数：** 120+ 字\n\n"
    md += "---\n\n"
    md += f"## {prompt['professor']}'s Question\n\n"
    md += f"{prompt['topic']}\n\n"
    md += f"---\n\n"
    md += f"### {prompt['student_a']['name']}:\n\n"
    md += f"{prompt['student_a']['position']}\n\n"
    md += f"### {prompt['student_b']['name']}:\n\n"
    md += f"{prompt['student_b']['position']}\n\n"
    md += "---\n\n"
    md += "## 我的回答\n\n"
    md += "（请加入自己的观点，可以同意或反对任一学生，但要提出新的论点）\n\n\n\n\n\n"
    md += "---\n\n"
    md += "## 批改结果\n\n（完成后请 AI 批改：「帮我批改这篇 discussion」）\n"

    with open(os.path.join(exercise_dir, "exercise.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ Academic Discussion 练习已生成：{exercise_dir}")
    return exercise_dir


def generate_full_writing(output_dir: str):
    """Generate a complete writing practice set."""
    print("✍️ 生成完整写作练习（模拟真实考试）\n")
    s = generate_sentence_exercises(output_dir, 10)
    print()
    e = generate_email_exercise(output_dir)
    print()
    d = generate_discussion_exercise(output_dir)
    print(f"\n📝 完整写作练习已生成！")
    print(f"   顺序：Build a Sentence → Email → Discussion")
    return s, e, d


def main():
    parser = argparse.ArgumentParser(description="TOEFL 写作批改模块")
    parser.add_argument("--type", choices=["sentence", "email", "discussion", "full"], default="full")
    parser.add_argument("--output", default="./writing/")
    parser.add_argument("--count", type=int, default=10, help="Number of sentence exercises")
    args = parser.parse_args()

    if args.type == "sentence":
        generate_sentence_exercises(args.output, args.count)
    elif args.type == "email":
        generate_email_exercise(args.output)
    elif args.type == "discussion":
        generate_discussion_exercise(args.output)
    elif args.type == "full":
        generate_full_writing(args.output)


if __name__ == "__main__":
    main()
