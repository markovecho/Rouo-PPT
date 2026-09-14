# 截图与素材适配

> 把用户提供的产品截图、网页截图、代码截图、设计稿截图，处理成符合模板槽位比例、且风格统一的图片资产。
> 目标类似 CleanShot X 的"截图居中 + 背景托底 + 统一比例"，**核心原则是保真，不是重画**。

---

## 一 · 三条优先级（按顺序判断）

1. **程序化适配优先** —— 截图内容、文字、UI 细节需要保真时，**不要重画**。建目标比例画布 → 原截图等比缩放 → 放入画布
2. **生成模型只做重构** —— 只有原图过长 / 过窄 / 信息太乱 / 需要 UI 情景化或概念化表达时，才用生成模型做"截图再设计"
3. **模板槽位先行** —— 先确定版式和图片槽位比例，再决定适配参数

---

## 二 · 动手前必须问清（5 问）

只要用户提到产品截图、网页截图、代码截图、设计稿、dashboard、旧 PPT 截图或"帮我美化截图"，先问：

1. **截图在哪个文件夹？** 是否包含网页、App、代码、dashboard、设计稿或旧 PPT？
2. **这批截图要保真展示、统一美化、重新设计成 UI 情景图，还是混合处理？**
3. **最终放进哪些槽位？** 21:9 顶图 / 16:10 主图 / 4:3 侧图 / 1:1 方图 / 多图网格？
4. **是否必须保留全部文字和数据？** 有无账号、头像、项目名等敏感信息要遮挡？
5. **构图希望居中、左上、右下，还是根据页面内容自动判断？**

---

## 三 · 七个语义参数（每次处理前先定这七个）

| 参数 | 可选值 | 判断方式 |
|---|---|---|
| `ratio` | `21:9` / `16:10` / `16:9` / `4:3` / `1:1` | **跟随模板槽位，不跟随原截图比例** |
| `background` | `plain` / `gradient` / `paper` / `blurred` / `grid` / `dot-matrix` | 跟随当前风格族与主题色 |
| `padding` | `compact` / `standard` / `spacious` | 普通截图 `standard`；文字密集或高截图 `spacious`；小图组 `compact` |
| `inset` | `none` / `subtle` / `balanced` | 需要从背景"浮出来"用 `balanced`；极简风 / 蓝图风多用 `none` / `subtle` |
| `shadow` | `none` / `soft` / `editorial` | 电子风可 `soft` / `editorial`；极简风与蓝图风**默认 `none`** |
| `corners` | `square` / `small` / `medium` | 极简风 / 蓝图风 `square`；电子风 / 水彩风 `small` / `medium` |
| `alignment` | `center` / `top-left` / `top-right` / `bottom-left` / `bottom-right` | **跟随页面构图，不是永远居中** |

**默认不要裁掉截图内容。** 只有截图已按目标槽位重新生成、或用户明确允许裁切时，才用 `cover` 裁切。

---

## 四 · 五族风格映射

### 电子风
- 背景：`paper` / `blurred` / 低饱和 `gradient`
- 质感：纸张、墨水、胶片颗粒、暖白、低对比
- 截图：可用**小圆角和轻微阴影**，但不要做成 SaaS 营销卡片
- 推荐语义：
  ```text
  ratio:16:10, background:paper, padding:standard, inset:balanced,
  shadow:editorial, corners:small, alignment:center
  ```

### 极简风
- 背景：`plain` / `grid` / `dot-matrix`
- 色彩：**只允许当前 anchor 色以极低占比出现**，不要大面积亮色块
- 截图：**直角、无阴影、无圆角**，少量 hairline 或顶部 accent 线
- 推荐语义：
  ```text
  ratio:21:9, background:grid, padding:standard, inset:subtle,
  shadow:none, corners:square, alignment:center
  ```

### 水彩风
- 背景：`paper`（暖白纸纹）+ 一角极淡晕染
- 色彩：只用当前色板的**主颜料**，一层淡晕即可，不要铺满
- 截图：`small` 圆角 + `soft` 阴影；**不要让晕染边缘压到截图内容**
- 推荐语义：
  ```text
  ratio:16:10, background:paper, padding:spacious, inset:subtle,
  shadow:soft, corners:small, alignment:center
  ```
- ⚠️ 截图本身是**锐利的**，和水彩质感天然冲突。**让截图"贴在纸上"**（纸纹底 + 一圈淡晕），别试图给截图加毛边

### 编辑风
- 背景：`paper`，**无渐变无网格**
- 截图：直角或 `small`，**无阴影**；可加 1px 细边或细 caption 线
- 推荐语义：
  ```text
  ratio:3:2, background:paper, padding:spacious, inset:none,
  shadow:none, corners:square, alignment:center
  ```

### 蓝图风
- 背景：`grid`（跟随 2 套制图底之一）
- 截图：**直角无阴影**；建议给截图叠一层极淡网格或统一去色，让它像制图附件
- 推荐语义：
  ```text
  ratio:16:9, background:grid, padding:standard, inset:none,
  shadow:none, corners:square, alignment:center
  ```

---

## 五 · 背景强度规则

**截图背景是"托底"，不是主视觉。**

- `alignment` 不确定时，**背景中心和四角都必须安静**，不放显眼色块
- 截图放右下角，右下角就不能有强色块（其他位置同理）
- 极简风的 anchor 色**只做 5%–8% 视觉占比**的淡线、点阵或极浅几何场 —— **不要高亮蓝条、大色块、霓虹渐变**
- 背景**不能有**文字、logo、图标、人物、设备、边框、明显主体或方向性构图
- 背景必须 **crop-safe**：裁成 `21:9` / `16:10` / `4:3` / `1:1` 都不能暴露"被裁掉"的痕迹

---

## 六 · 程序化合成（本项目做法）

**不要为每张截图临时生成一种背景。** 按风格用代码生成"托底画布"，把截图放进去：

### 6.1 极简风 · 网格 / 点阵底

```python
# 纯 SVG，无外部资产；输出与槽位同尺寸
def minimal_canvas(w, h, accent, mode="grid"):
    if mode == "grid":
        # 16 列细网格，accent 只在线条上以极低透明度出现
        step = w / 16
        lines = "".join(
            f'<line x1="{i*step:.1f}" y1="0" x2="{i*step:.1f}" y2="{h}" '
            f'stroke="{accent}" stroke-opacity="0.07" stroke-width="1"/>'
            for i in range(17)
        )
    else:  # dot-matrix
        step = w / 48
        lines = "".join(
            f'<circle cx="{x*step:.1f}" cy="{y*step:.1f}" r="1" fill="{accent}" fill-opacity="0.12"/>'
            for x in range(48) for y in range(int(round(h/step)))
        )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="#fafaf8"/>{lines}</svg>')
```

### 6.2 电子风 · 纸感底

纸纹用**灰噪点**（`feTurbulence` baseFrequency≈0.8，`opacity .05`）+ 极淡的径向明暗，**不要用渐变**（渐变会显廉价）。底色取当前主题的 `--paper`。

### 6.3 水彩风 · 纸纹 + 一角淡晕

纸色底 + 四角之一放**单个**低透明度晕染（三层叠加，见 `23-style-watercolor.md` §5.1）。晕染只出现在**截图不出现在的那一角**。

### 6.4 蓝图风 · 制图网格底

主格 48px（`opacity .10`）+ 次格 12px（`opacity .05`），线色 = 制图底的前景线色。四角加 L 形视口括角。

### 6.5 合成步骤

1. 建目标比例画布（`ratio` 决定），背景 cover 铺满
2. 截图按 `padding` 等比缩放（**保真 → 用 contain，绝不 cover 裁内容**）
3. 按 `alignment` 落位
4. 按 `corners` / `shadow` 加处理（多数风格 `shadow:none`）
5. 导出：**JPG（照片/截图，q88）** 或 **PNG（透明 UI / 图表）**，单张 ≥ 1600px 宽

**本机工具**：图片批量处理走调度器 `tools.py image-treat`；需要新配图先 `tools.py image-search` 找可用素材，取不到再考虑生成。

---

## 七 · 截图类型决策

| 原始素材 | 推荐处理 |
|---|---|
| 普通网页 / App / 桌面截图 | 程序化适配到目标比例 |
| 产品 UI 细节很重要 | 程序化适配 + `fit-contain`，**不重画** |
| 长网页截图 | 截关键区域，或拆成 2–3 张同尺寸面板 |
| 极窄 / 极高截图 | 先试 `spacious + 侧位对齐`；仍太小才重构 |
| 代码截图 | 电子风用纸感背景；极简风用浅网格背景；**文字必须可读** |
| 概念解释用的 UI 情景图 | 可以让生成模型重新设计 |
| 旧 PPT 截图 | 按上面判断；若整页都要重建 → 走图像重建线（见 `14-image-rebuild.md`） |

### 生成图的三条纪律

- **提示词保持简短**：只框定主题、用途、风格、比例，不要写长篇摄影指导
- **图片内部不要自带**页眉、页脚、页码、logo、主标题、装饰边框或署名 —— 会和 deck chrome 重复
- **信息图 / 图表 / 截图再设计里的文字语言必须跟随 deck 语言**：中文 deck 用中文，英文 deck 用英文

### 比例必须匹配最终落位

主视觉 `16:9` · 左文右图 `16:10` / `4:3` · 信息图 `16:9` / `16:10` · 截图再设计 `16:10` · 图文混排小图 `3:2` / `3:4` · 网格图统一高度裁切

---

## 八 · 需要新背景资产时的提示词

只有现有做法都不匹配时才用。两个模板：

**电子风 / 编辑风（纸墨系）**
```text
16:9 crop-safe screenshot background for an editorial magazine / e-ink deck system.
Warm off-white paper texture, subtle ink wash, fine film grain, low contrast, quiet center
and quiet corners, no text, no logo, no objects, no border, no focal subject.
Suitable for cropping to 21:9, 16:10, 4:3, or 1:1.
```

**极简风 / 蓝图风（网格系）**
```text
16:9 crop-safe screenshot background for a Swiss International Style deck system.
Pure off-white base, ultra-subtle 16-column grid and sparse dot matrix, one accent color only:
[主题色], used at very low opacity as thin lines or tiny dots, no large bright color blocks.
Quiet center and quiet corners, no text, no logo, no objects, no border, no focal subject.
Suitable for cropping to 21:9, 16:10, 4:3, or 1:1.
```

**背景图不是单张 slide。** 内部不能有标题、页脚、边框、logo、人物或明显主体。
