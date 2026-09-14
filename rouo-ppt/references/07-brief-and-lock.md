# 设计简报 + 设计锁（模板与规则）

> 手作线立约阶段的产物模板。`design-brief.md` 是设计的唯一事实来源；`design-lock.md` 是每页执笔前的必读。
> 两者都是 Gate 文件——执笔前必须存在。

---

## 一 · `design-brief.md` 模板

> 保持英文小节标题与字段名（内容值可用中文）。
> §IX 页面队列是**有序队列**：一条 = 一页最终幻灯片，id 与顺序完全一致，绘制中**永不增删、合并、拆分、重排**。

```markdown
# {{PROJECT_NAME}} · Design Brief

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | {{PROJECT_NAME}} |
| Canvas Format | {{CANVAS_NAME}} ({{CANVAS_DIMENSIONS}}) |
| Page Count | [必须与 §IX 的 Slide 块数一致] |
| Target Audience | [fill] |
| Communication Intent | [fill] |
| Desired Audience Outcome | [fill] |
| Core Message / Ask / Action | [fill] |
| Delivery Context | [fill] |
| Reading Mode | [fill] |
| Viewing Distance | [fill: 10cm 手机 / 1m 笔记本 / 10m 投屏] |
| Design Style | [fill — 方向门选定后的方向] |
| Speaker Notes | [fill enabled/disabled] |
| Created Date | {{CREATED_DATE}} |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Dimensions | {{CANVAS_DIMENSIONS}} |
| viewBox | `{{VIEWBOX}}` |
| Margins | [fill] |
| Content Area | [fill] |
| Footer Band Height | [fill — **由出处牌高度决定，不是正文**] |

> ⚠️ 先算页脚带高度，再倒推每页内容能到哪个 y——否则最后几页必然压字。

## III. Visual Theme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | [fill] | [fill] |
| Primary | [fill] | [fill] |
| Accent | [fill] | [fill] |
| Body text | [fill] | [fill] |

> 所有颜色从品牌资产 / 内容真图 / `brand-kit.md` 来，不凭空发明。

## IV. Typography System

| Role | Primary | Fallback tail |
| --- | --- | --- |
| Title | [fill] | [fill] |
| Body | [fill] | [fill] |
| Mono（数值/编号/微标签） | [fill] | [fill] |

| Purpose | Size |
| --- | --- |
| Body / Page title / Subtitle / Annotation / Footnote | [fill] |

> 投屏（10m）正文 ≥24px、标题 60–120px；笔记本 ≥16px；手机 ≥14px。

## V. Layout Principles

- Hierarchy direction / Composition tendency / Cross-page continuity / Spacing posture: [fill]

## VI. Icon Usage Specification

| Icon Path | Suitable Scenarios |
| --- | --- |
| [fill] | [fill] |

## VII. Chart / Table Plan

| Page | Type | Data source | Notes |
| --- | --- | --- | --- |
| [fill] | chart/table | [fill] | [fill] |

> 图表由**真实数据现算**，不手绘不估算；数据来源写进页脚出处牌。

## VIII. Image Resource List

| Filename | Dimensions | Purpose | Acquire Via | Status | page_role |
| --- | --- | --- | --- | --- | --- |
| [fill] | | | | | |

## IX. Content Outline（页面队列 = 有序队列）

> 一个 `#### Slide NN` 块 = 一页最终幻灯片。每块必须含 `Page role`、`rhythm`、`Core message`。
> ⚠️ 空/缺失的条目是立约时的**刻意信号**（该页不需要那项），不是遗漏。

### Part 1: [fill]

#### Slide 01 - [fill]

- **Audience move**: [这一页把读者从哪带到哪]
- **Page role**: [hero / 过渡 / 数据 / 引语 / 拆解 / 结论 / 结尾]
- **rhythm**: [`anchor` 立论 | `dense` 密集 | `breathing` 呼吸]
- **Layout inheritance**: [继承自哪一版式，或省略]
- **Chart reference**: [引用 §VII 的哪一项，或省略]
- **Title**: [fill]
- **Core message**: [这一页唯一的那句结论]
- **Content**: [fill]

#### Slide 02 - …（同上结构）

## X. Speaker Notes Requirements

- **Generation**: [enabled or disabled]
```

**填写规则**：
1. §I 的 Page Count 必须与 §IX 块数、最终 SVG 数一致
2. `rhythm` 三值语义：`anchor` 立住一个观点、`dense` 承载密集信息、`breathing` 呼吸过渡。同一份 deck 至少分布 3 种节奏——**不要全是 dense**（会变成卡片网格）
3. `Page role` 说不清 → 形式必然发散。先定角色再定形式（载体菜单见 `08-page-craft.md`）

---

## 二 · `design-lock.md` 模板

```markdown
# Execution Lock

## canvas
- viewBox: {{VIEWBOX}}
- format: {{CANVAS_NAME}}

## communication
- primary_language: [fill]
- audience: [fill]
- objective: [fill]
- core_message: [fill]
- consumption_mode: [fill]

## visual_style
- visual_style: [fill — 选定风格名或 custom]

## colors
- bg: [fill]
- primary: [fill]
- accent: [fill]
- text: [fill]
- secondary_text: [fill]
- divider: [fill]

## typography
- font_family: [fill — 正文/默认兼容栈]
- title_family: [fill]
- body_family: [fill]
- body: [fill — 无单位 px]
- title: [fill]

## icons
- library: [fill — 图标风格或 none]
- inventory: [fill — 策展后的图标池索引]
- stroke_width: [仅线性图标时填 1.5 / 2 / 3]

## page_rhythm
- P01: [anchor | dense | breathing]
- P02: [fill]

## pptx_structure
- mode: flat

## forbidden
- mask, <style>, class, external CSS, <foreignObject>, textPath, @font-face, <animate*>, <set>, <script> / event attributes, <iframe>
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
- [用户的禁区原话，逐字引用并以 (user) 结尾]
```

### 结构规则

1. **只允许 `##` 段 + `- key: value` 行**（`forbidden` 段例外——字面规则）。绝不把指导性段落抄进锁里。
2. **基础段必备**：`canvas`（viewBox+format）、`communication`（语言/受众/目标/核心信息）、`visual_style`、`colors`（语义色角色）、`typography`（族+号锚点）、`icons`、`page_rhythm`（每页一行）、`pptx_structure`、`forbidden`。
3. **字段语法**：
   - `page_rhythm`：`P` + 至少两位数字 + 三值枚举
   - 字体族字段：非空、PPT 安全的导出族名栈
   - 非字体族的 typography 值：正有限无单位 px
   - `forbidden` 的 `(user)` 行是**用户原句**，不是转述
4. **锚点与扩展**：稳定跨页锚点 = 已确认的核心色板角色 + 所有字体族/字号角色。页面局部 tint、渐变 stop、一次性效果**不需要行**；当临场值变成复现的语义角色（或未声明的 display 字号出现第三次）才补一行，回读并校验受影响的规划片段。**锁的编辑表达的是复用或身份，不是随手写字面值。**

### 执笔纪律

- **每生成一页 SVG 前重读一次本锁**——所有色彩/字体/图标/图片从锁里取。这条存在是为了：① 抵抗长 deck 上的**上下文压缩漂移**；② 打破「每页都是卡片网格」的默认惰性。
- P05、P10、P15… 之后若还有下一页 → 下一页前完整重读一次（纯重锚定，不跑质检不停顿）。

---

## 三 · 机器校验（可选）

```bash
python "…/rouo-ppt/scripts/tools.py" validate <project_path>
```

报告未填占位、未知段/字段、非法枚举、页键格式、缺失目录资产。它不改写锁、不检查语义。
