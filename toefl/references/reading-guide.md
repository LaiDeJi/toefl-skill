# 阅读模块使用指南

## 生成练习
```bash
uv run python scripts/generate_reading.py --type all --output ./reading/ --difficulty hard
```

## 题型与脚本对应
| 题型 | 参数 | 难度建议 |
|------|------|----------|
| Complete the Words | `--type complete-words` | Week 1-4: easy → Week 5+: hard |
| Read in Daily Life | `--type daily-life` | 全阶段混合 |
| Academic Passage | `--type academic` | Week 5+: medium/hard |

## AI 引导流程
1. 确认用户本周进度（读 progress.json）
2. 选择对应难度的练习
3. 用户作答后，逐题讲解错误选项为何错
4. Complete the Words 错题 → 加入本周 Anki deck
5. 记录正确率到 progress.json

## 高分要点
- 详见 `references/high-score-patterns.md` 的阅读段落
- Complete the Words 是拉分关键，需要 90%+ 正确率
- Academic Passage 推论题是 4.0 vs 5.0 的分水岭
