# 量产线 · 页面数据格式与元素路由

> `deck_data.json` 的完整规范：画布坐标系、字号体系、元素类型、表格铁律、布局硬规则、主题与预设。
> 引擎（skill 自带 `scripts/com_drive.py`）→ `10-drive-engine.md`。
> 校验命令：`python scripts/com_drive.py review deck_data.json`

---

## 一 · 画布坐标系（960 × 540 pt，16:9）

### 全局硬规则

- 顶部品牌色条 `y=0, h=4–6`；底部品牌色条 `y=535, h=4–6`
- 标题 `y=14, h=38–44`，SimHei 40–48pt，品牌色，居中，**无装饰线**
- 标题结束于 y≈52 → **第一个内容元素必须起始于 y≥76–90**（≥24pt 间隙，约 3–4 行空白）。**绝不让内容紧贴标题！**
- 底部总结条 `y=498, h=28`，品牌色底 + 白字
- **安全下边界**：所有元素 `y+h ≤518`；`x+w ≤960`

### 精确坐标表

| 元素 | x | y | w | h | 字体 | 字号 | 颜色 |
|---|---|---|---|---|---|---|---|
| 标题 | 60 | 14 | 840 | 38–44 | SimHei | 40–48pt | 品牌色 |
| 内容起始 | — | **≥90** | — | — | — | — | — |
| 左图 | 30–50 | 90–100 | 440–520 | 210–260 | — | — | — |
| 右文每行 | 545–580 | 92+ | 350–420 | 22–26 | YaHei | 18–24pt | #333333 |
| 右文行间距 | — | +34~36 | — | — | — | — | — |
| 底部总结条 | 30 | 498 | 900 | 28 | YaHei | 14pt | 白字品牌底 |

### 2×3 卡片坐标（三列卡片）

| 列 1 x=22 | 列 2 x=332 | 列 3 x=642 |
|---|---|---|
| 行 1: y=80 | 行 1: y=80 | 行 1: y=80 |
| 行 2: y=225 | 行 2: y=225 | 行 2: y=225 |

每卡 w=295，顶部 4–5pt 彩色细线（**无灰色填充**）+ 标题 + 说明。

---

## 二 · 字号体系

| 层级 | 字体 | 字号 | 颜色 | 用途 |
|---|---|---|---|---|
| H1 | SimHei | 40–48pt | 品牌色 | 页面标题 |
| H2 | YaHei | 24–26pt | 品牌色 | 段落标题 |
| H3 | YaHei | 20–22pt | 品牌色/黑 | 目录标题 |
| Body | YaHei | 18–20pt | #333333 | 正文 |
| Body-S | YaHei | 16–17pt | #333333 | 卡片说明 |
| Caption | YaHei | 14–15pt | #666666 | 数据来源/注释 |
| Table | YaHei/SimHei | 13–15pt | #333333/白 | 表格文字 |
| Number | Arial | 28–36pt | 品牌色/黑 | 大数字 |
| Number-Label | YaHei | 13pt | #666666 | 数字下方标签 |
| Tagline | YaHei | 14pt | 白色 | 底部总结条 |

---

## 三 · 元素类型完整规范

每个元素是一个 `{"type": "...", ...}` 对象，引擎按 type 路由到对应绘制函数。

### `text` — 通用文字
```json
{"type": "text", "x": 545, "y": 92, "w": 385, "h": 26,
 "text": "文字内容", "fs": 20, "color": "#333333",
 "bold": false, "align": 1, "font": "Microsoft YaHei", "line_spacing": 1.3}
```
`align`：1=左 2=中 3=右。

### `image` — 插入图片
```json
{"type": "image", "x": 30, "y": 92, "w": 490, "h": 230,
 "file": "images/chart_rank.png"}
```
路径相对于工作目录；文件不存在时静默跳过（不崩引擎）。

### `shape` — 矩形/圆形/线条
```json
{"type": "shape", "shape": "rect", "x": 0, "y": 0, "w": 960, "h": 5, "color": "#8C1515"}
```
`shape` 取 `rect` / `circle` / `line`。

### `table` — 数据表格
```json
{"type": "table", "x": 30, "y": 92, "w": 440, "h": 270,
 "rows": 9, "cols": 2, "header_color": "#8C1515",
 "th_fs": 13, "td_fs": 14,
 "data": [["列1标题", "列2标题"], ["数据1", "数据2"]]}
```

**表格铁律**：

| 规则 | 说明 |
|---|---|
| **单行强制** | `WordWrap=False`，绝不换行。文字过长被截断而非换行 |
| 最小行高 | 28pt，保证 14pt 文字完整显示 |
| 列宽 | 文字不超过列宽−4pt；超长应缩减或拆表 |
| 行数上限 | 10 行以内（含表头）；超过拆为两页或两栏 |
| 列数上限 | 3 列以内；超过投影端难读 |
| 表头 | 品牌色底 + 白字 + SimHei |
| 数据行 | 奇数白底 + 偶数浅色底（#F5F0ED）+ YaHei 黑字 |

### `card_list_wide` — 目录编号列表
```json
{"type": "card_list_wide", "start_y": 90, "item_h": 52,
 "items": [{"num": "01", "title": "板块名称", "sub": "简要说明"}]}
```
建议 6–8 项；编号圆品牌色/黑交替。

### `num_big` — 大数字 + 标签（三段式，绝不重叠）
```json
{"type": "num_big", "x": 80, "y": 355, "w": 180, "h": 65,
 "num": "8,180", "label": "英亩校园面积", "color": "#8C1515", "fs": 34}
```
内部布局：数字 40% + 间隙 10% + 标签 50%。

### `tagline_bar` — 底部总结条
```json
{"type": "tagline_bar", "text": "总结文字 · 关键数据 · 核心信息"}
```
固定位置 y=498, h=28，品牌色底 + 白字。

### 页面骨架示例（带主题，可直接改）

```json
{
  "preset": "business",
  "canvas": {"w": 960, "h": 540},
  "theme": {
    "primary": "#8C1515", "accent": "#3F6B5C",
    "body": "#241F1A", "light": "#F1EAE0", "bg": "#FAF7F2",
    "caption": "#6B6257", "text_on_primary": "#FFFFFF",
    "title_font": "SimHei", "body_font": "Microsoft YaHei",
    "title_size": 36, "body_size": 20, "caption_size": 14,
    "max_points": 6, "visual_ratio": 0.45
  },
  "slides": [
    {
      "id": 1, "title": "封面",
      "elements": [
        {"type": "shape", "shape": "rect", "x": 0, "y": 0, "w": 960, "h": 6, "color": "$primary"},
        {"type": "shape", "shape": "rect", "x": 0, "y": 534, "w": 960, "h": 6, "color": "$primary"},
        {"type": "text", "x": 60, "y": 130, "w": 840, "h": 104, "text": "XX 大学",
         "fs": 48, "color": "$primary", "bold": true, "align": 2, "font": "SimHei"},
        {"type": "image", "x": 80, "y": 312, "w": 800, "h": 181, "file": "images/chart_nums.png"},
        {"type": "num_big", "x": 80, "y": 355, "w": 180, "h": 65,
         "num": "1885", "label": "建校年份", "color": "$primary", "fs": 36}
      ]
    }
  ]
}
```

**色标引用**：`color` / `header_color` / `text_color` / `line_color` 的值可以写 `"$primary"` 这类令牌，
引擎在绘制前替换成 `theme` 里的实际颜色。好处是**换一套主题 = 换一份 deck**，不必逐元素改 hex。
写不存在的令牌引擎会直接报错（不静默画成黑色），这是有意的。

**预设**：`preset` 取 `academic` / `consultant` / `business` / `tech`（详见 `12-presets-review.md`）。
`theme` 里的键会覆盖预设同名键；`preset` 只提供起点，用户品牌色优先。

**页面级背景**：每页可选 `"background": "template_bg.png"`（母版底图，16:9）；
不给就用 `"bg"`，再不给就用 `theme.bg` 铺纯色。

---

## 四 · 布局硬规则汇总

| 规则 | 标准 |
|---|---|
| 背景 | 模板底图铺满，**绝不遮挡** |
| 标题 | 居中，SimHei 40–48pt，品牌色，无装饰线，**最多 4 字**为宜 |
| 标题-内容间距 | **≥24pt**（约 2 行）。绝不让内容紧贴标题 |
| 卡片 | 仅顶部 4–5pt 彩色细线，**无灰色填充** |
| 表格 | 品牌色表头白字 + 隔行交替着色 |
| 图表 | matplotlib transparent=True（图表铁律见 `10-drive-engine.md` 工步 2） |
| 底部条 | tagline_bar y≈498, h≈28 |
| 内容密度 | 每页 **≤80 中文字 + ≥2 种视觉元素** |
| 元素边界 | `y+h ≤518`，`x+w ≤960` |
| 目录 | items 数 × item_h < 500 − start_y |

---

## 五 · 主题键速查

| 键 | 用途 | 谁在用 |
|---|---|---|
| `primary` | 品牌主色，标题 / 表头 / 出血条 | `text.bold` 标题、`table.header_color`、`tagline_bar` |
| `accent` | 辅色，用于第二强调 | 眉标、点缀形状 |
| `body` | 正文黑 | `text` 默认色 |
| `light` | 浅底色 | `table` 隔行交替 |
| `bg` | 页面底色 | 无底图时铺满 |
| `caption` | 注释灰 | `card_list_wide` 的 sub、`num_big` 的 label |
| `text_on_primary` | 主色底上的字色 | 表头、编号圆、tagline 文字 |
| `title_font` / `body_font` | 字体族 | 标题 / 正文 |
| `title_size` / `body_size` / `caption_size` | 字号基准 | 元素未写 `fs` 时的默认 |
| `max_points` | 每页要点上限 | 质检密度项 |
| `visual_ratio` | 视觉元素占比目标 | 质检视觉占比项 |

> `academic` / `consultant` / `business` / `tech` 四套预设的具体取值见 `12-presets-review.md §一`。
> `tech` 是暗色预设，会自带 `bg`。

---

## 六 · 编排纪律

1. **内容全部真实**：每个数字、排名、名称来自 `facts.md`，**禁止编造**（铁律 1）
2. **每页一句结论**：先想这页让读者记住什么，再排元素
3. **视觉元素成对**：图表 + 表格、卡片 + 编号圆、大数字 + 图——单一大段文字页禁止
4. **改数据不改引擎**：调整内容只动 `deck_data.json`；换实例动主题色常量 + 数据 + 底图
