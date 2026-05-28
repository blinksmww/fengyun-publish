# 风云公众号封面 风格规范(权威 Style Block)

> **2026-05-27 W7 重写 —— 无模板**。封面 prompt 由 `huashu-image-curator` **Mode 3 cover** 花叔自著(**中文**);本文件只定**权威 Style Block** 供 cover mode 引用做单一真源。
> 旧 5/7 固定模板 prompt 段已删除(与代码分叉 + `generate_cover_by_template.py` / `cover_dedup.py` 已物理删除)。

---

## 一、无模板流程(一句话)

花叔 cover mode 读这一篇文章自著中文 Seedream prompt(结构化自由:Style Block 锁品牌色 + 手绘风,**主体 metaphor 放给 AI** 按内容写)→ 薄客户端 `tools/seedream_client.py` 透传出图(retry ×3 指数退避 + placeholder fallback 全内藏)。

- 谁写 prompt:`huashu-image-curator` **Mode 3 cover**(花叔 taste,跟内文图 Mode 2 同一套眼睛 + style_anchor 衔接)
- 责任 subagent:`fengyun-cover`(Stage 4)
- 出图:`tools/seedream_client.py --prompt "<中文 prompt>" --aspect <16:9|2.35:1> --out <...>-cover.png --style-anchor "<anchor>"`
- 标题文字:**模型内渲染**(Seedream 中文渲字强项,Phase 7 实测 100%),用**轻量中文指令**,**不要 5 层英文加固**(已删)

---

## 二、权威 Style Block(每张封面必锁,cover mode 引用)

| 维度 | 规则 |
|---|---|
| **底色** | 暖米 `#F8F0E0`(纸纹 / paper grain) |
| **唯一彩色** | 陶土橙 `#D97757`(Anthropic 同族;整张封面只允许这一个彩色家族) |
| **高亮** | 黄高亮 `#F6AD55`(标题底 / 关键词强调,克制用) |
| **风格** | 手绘 sketchnote(轻微纸质纹理 / 笔触 wobble) |
| **人物** | **无人物**(no human figure / no cartoon character) |
| **元素数** | **≤3 个主视觉元素**(主体突出,留白足够) |
| **缩略图友好** | 主体在中心 + 留白充分,缩略图缩到列表尺寸仍可识别 |
| **签名** | **无签名**(2026-05-27 W7 删除云签名 —— 缩略图零识别,删) |

**铁律**:只 1 个彩色家族(陶土橙)。其余全是暖中性色 + 黑。不许蓝 / 红 / 绿 / 紫的饱和大色块。

### style_anchor(英文,供内文图 Mode 2 复用)

cover mode 输出 `style_anchor` 字段(英文),`seedream_client.py` 经 `--style-anchor` 写 sidecar `<cover>.style_anchor.txt`,Step 7.2 内文图 Mode 2 读它继承封面风格(篇内一致)。基底示例(**无 cloud signature**):

```
warm sketchnote hand-drawn, cream paper #F8F0E0, terracotta #D97757 accent line, no human face, editorial illustration
```

---

## 三、辅助色板(取自 Refero Design System Claude/Anthropic)

| 角色 | 名称 | Hex |
|---|---|---|
| 主强调 | Clay | `#D97757` |
| 悬停强调 | Accent Ember | `#C6613F` |
| 黄高亮 | Highlight | `#F6AD55` |
| 底色 | Cream(W7 主底) | `#F8F0E0` |
| 次级底 | Ivory Medium | `#F0EEE6` |
| 燕麦卡片 | Oat | `#E3DACC` |
| 弱化分割线 | Cloud Light | `#D1CFC5` |
| 弱化文字 | Cloud Medium | `#B0AEA5` |
| 主文字 | Slate Dark | `#141413` |
| 橄榄绿(辅,点缀) | Olive | `#788C5D` |

---

## 四、cover mode 输出契约(JSON)

花叔 Mode 3 cover 读 `article_md + title(≤14) + subtitle(≤22)`,输出:

```json
{
  "prompt": "横幅 16:9,手绘 sketchnote 风格封面。暖米 #F8F0E0 纸纹底,陶土橙 #D97757 为唯一彩色线条…<主体 metaphor 由花叔按内容写>…标题「<TITLE>」清晰准确渲染,副标「<SUBTITLE>」。≤3 个主视觉元素,主体突出,留白足够缩略图清晰。",
  "aspect": "16:9",
  "style_anchor": "warm sketchnote hand-drawn, cream paper #F8F0E0, terracotta #D97757 accent line, no human face, editorial illustration",
  "metaphor_note": "一句话:为什么这个视觉最能表达这篇 + 骗点击"
}
```

- `prompt`:**中文**,只有「主体 metaphor + 情绪」随文章变,Style Block(品牌色 + 手绘 + 无人物 + ≤3 元素 + 无签名)锁死
- `aspect`:`16:9`(默认)或 `2.35:1`(影院横幅,叙事 / 人物 / 重磅时)
- `style_anchor`:英文,供内文图复用
- `metaphor_note`:花叔的一句话理由

---

## 五、工具调用优先级链

| 层级 | 工具 | 触发条件 |
|---|---|---|
| **主力 + retry ×3** | 花叔 Mode 3 cover 自著中文 prompt → 豆包 Seedream 5.0(火山引擎方舟,`.env` 已配 `VOLCENGINE_IMAGE_KEY`);`seedream_client.py` 内藏 retry ×3 指数退避(1/2/4s) | 默认 |
| **应急** | 风云手工写 prompt + `--seed N` 重跑 | retry 全失败仍想调 |
| **兜底** | `baoyu-cover-image` skill / `assets/placeholder-sketch.png` placeholder(seedream_client 内藏,≥5KB,Round 25 硬约束) | 国内 API 全挂 |

**为什么主力是豆包 Seedream(火山引擎)**:
- 用户 `.env` 已配 `VOLCENGINE_IMAGE_KEY`,直接可用
- 完全国内 + 测试期免费,符合「国内 + 免费 / 极低成本」硬约束
- Seedream 中文渲字是强项(标题模型内渲染);中文 prompt 原生优化

---

## 六、Step 7 自动化接入

- `huashu-image-curator` **Mode 3 cover**:读文章自著中文 prompt(引用本文件 Style Block)
- `tools/seedream_client.py`:薄客户端,`--prompt` 透传(无 TEMPLATES replace)→ 出图 + 写 sidecar;失败走 placeholder fallback
- `fengyun-cover` subagent / `references/stage_04_publish.md` Step 7 已指向上述无模板流程

---

## 七、变更日志

| 日期 | 变更 |
|---|---|
| 2026-05-22 | 初版 → v2 sketch-notes 翻转 → 5/7 模板矩阵(已废) |
| **2026-05-27** | **W7 slim 重写:无模板。删 5/7 模板 prompt 段 + 删云签名 + 删 5 层英文加固;本文件只定权威 Style Block,prompt 由花叔 Mode 3 cover 自著(中文)** |
