# 听力模组使用指南

## 产生练习
```bash
uv run python scripts/generate_listening.py --type all --output ./listening/ --difficulty hard
```

## 题型与脚本对应
| 题型 | 参数 | 音档设计 |
|------|------|----------|
| Choose a Response | `--type choose-response` | 语句 → 2s 停顿 → beep |
| Conversation | `--type conversation` | 每句间 0.8s 停顿 |
| Announcement | `--type announcement` | 正式语速 -8% |
| Academic Talk | `--type academic` | [PAUSE] 标记 → 1.2s 自然停顿 |

## AI 引导流程
1. 播放音档前提醒：「只播放一次，做好笔记准备」
2. 播放后出题（题目在 questions.md）
3. 使用者作答后对答案，讲解错误原因
4. 如有需要，提供逐字稿（transcript.md）让使用者比对
5. 分析笔记问题：是听力问题、还是题型理解问题、还是笔记不足？

## 笔记教学重点
- 用缩写和符号，不逐字抄
- 记结构而非细节：主题 → 论点 → 例子 → 结论
- 特别注意结尾的「下次课」暗示
