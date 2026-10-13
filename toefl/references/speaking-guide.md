# 口说模组使用指南

## 产生练习
```bash
uv run python scripts/generate_speaking.py --type all --output ./speaking/
uv run python scripts/generate_speaking.py --type repeat --set 1   # 特定 Listen & Repeat set
uv run python scripts/generate_speaking.py --type interview         # Interview 练习
```

## 音档结构（精确计时）

### Listen & Repeat
```
[0.5s 静音] → [句子音档] → [0.3s 静音] → [BEEP 880Hz 250ms] → [录音静音 8-12s]
```
- Items 1-2: 8 秒录音时间
- Items 3-5: 10 秒
- Items 6-7: 12 秒

### Interview
```
[介绍旁白] → [2s 静音] → [问题音档] → [0.5s 静音] → [双 BEEP] → [45s 录音静音] → [单 BEEP = 停止]
```

## AI 评估流程（文字版回答）
1. 使用者提交文字版回答
2. 读取 `references/scoring-rubrics.md` 的口说评分标准
3. 依照四维度评分：Fluency / Intelligibility / Language Use / Organization
4. 给出具体错误和修正建议
5. 提供模范回答参考

## Shadowing 练习建议素材
- TED-Ed (1-3 min): 清晰发音、学术主题
- BBC Learning English: 6 Minute English
- NPR Short Wave: 科学新闻 (2-3 min)
- 用 edge-tts 产生自定句子练习
