# 写作模块使用指南

## 生成练习
```bash
uv run python scripts/generate_writing.py --type all --output ./writing/
uv run python scripts/generate_writing.py --type build-sentence
uv run python scripts/generate_writing.py --type email
uv run python scripts/generate_writing.py --type discussion
```

## AI 批改流程

### Build a Sentence
1. 出题（从脚本内置题库或 AI 即时生成）
2. 用户排列单词
3. 比对正确答案：全对 1 分，有误 0 分
4. 讲解文法考点（关系子句、间接问句、倒装等）

### Write an Email（7 分钟计时）
1. 显示题目（scenario + 3 bullets）
2. 用户写完后提交
3. 读取 `references/scoring-rubrics.md` 的 Email 评分标准
4. 逐一检查：3 个要点是否都有回应、语气是否得体、文法错误列表
5. 给出 0-5 分 + 各维度分数 + 具体修改建议
6. 如有范例回答，提供比较

### Academic Discussion（10 分钟计时）
1. 显示教授问题 + 两位学生回复
2. 用户写回应
3. 检查重点：是否有新论点？是否回应了其他学生？字数够吗？
4. 给出 0-5 分 + 修改建议

## 批改输出格式
使用 `references/scoring-rubrics.md` 中定义的标准格式。
