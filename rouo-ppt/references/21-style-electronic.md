# 风格族 1 · 电子风（电子杂志 × 电子墨水）

> 美学锚点：像 *Monocle* 杂志贴上了代码。
> 骨架：`assets/deck-shell-electronic.html`

---

## 一 · 三段式字体分工（本风格最重要的规则）

**衬线 = 视觉重音，非衬线 = 信息密度，等宽 = 装饰节奏。** 严禁混用。

| Class | 用途 | 字体 / 字号 |
|---|---|---|
| `.display` | 超大英文（hero 页） | Playfair Display 700 · 11vw |
| `.display-zh` | 超大中文标题 | Noto Serif SC 700 · 7.8vw |
| `.h1-zh` | 页面主标题 | Noto Serif SC 700 · 4.6vw |
| `.h2-zh` | 副标题 | Noto Serif SC 600 · 3.2vw |
| `.h3-zh` | 流水线步骤标题 | Noto Serif SC 500 · 1.9vw |
| `.lead` | 引导段 | Noto Serif SC 400 · 1.9vw |
| `.body-zh` | **正文 / 描述** | Noto Sans SC 400 · 1.22vw |
| `.body-serif` | 正文（衬线变体） | Noto Serif SC 400 · 1.3vw |
| `.kicker` | 标题上方小提示 | IBM Plex Mono · 12px uppercase |
| `.meta` | 元信息标签 | IBM Plex Mono · 0.88vw uppercase |
| `.big-num` | 巨型数字 | Playfair Display 800 · 10vw |
| `.mid-num` | 中号数字 | Playfair Display 700 · 5.5vw |

**强调两个动作**：
- `<em class="en">English word</em>` → 渲染成 Playfair Display 斜体，中文稿里嵌英文词的杀手锏
- `<em style="opacity:.65">后半段</em>` → 标题后半段淡出，制造呼吸

### ⚠️ 本机字体（必须知道）

骨架**不挂 Google Fonts `<link>`** —— `fonts.googleapis.com` 在本机不可达，挂了也只是阻塞超时。实际渲染直接落到下面这套**本地兜底栈**（见 19-environment.md 的适配改动 3）：

| 变量 | 兜底字体 | 效果 |
|---|---|---|
| `--serif-en` | Georgia, serif | Playfair Display → **Georgia**，仍是衬线，观感成立 |
| `--serif-zh` | Noto Serif SC | 本机已装，**满血** |
| `--sans-zh` | Noto Sans SC | 本机已装，**满血** |
| `--mono` | ui-monospace → Consolas | IBM Plex Mono → Consolas |

**结论：中文排版不受影响，英文 display 从 Playfair 降级为 Georgia。** 这是可接受的（Georgia 本身是高雅衬线），但要在交付说明里讲清楚，别让用户以为是 bug。要满血 Playfair，需先把字体文件放到项目本地并用 `@font-face` 指向。

---

## 二 · 五套主题色（只能选，不能自定义）

**硬规则**：一份 deck 只用一套；不接受用户给的任意 hex（委婉拒绝并展示五套）；**不允许混搭**（ink 取一套、paper 取另一套会彻底违和）。

替换方式：打开骨架的 `<style>`，找到 `:root{` 里标着"主题色"的六行整体替换即可，其余 CSS 全走 `var(--ink-rgb)` / `var(--paper-rgb)`，不用逐处改。

| # | 主题 | 适合 | `--ink` | `--paper` |
|---|---|---|---|---|
| 1 | 🖋 **墨水经典** | 通用 / 商业发布 / 不知道选啥的默认 | `#0a0a0b` | `#f1efea` |
| 2 | 🌊 **靛蓝瓷** | 科技 / 研究 / 数据 / 技术发布会 | `#0a1f3d` | `#f1f3f5` |
| 3 | 🌿 **森林墨** | 自然 / 可持续 / 文化 / 非虚构 | `#1a2e1f` | `#f5f1e8` |
| 4 | 🍂 **牛皮纸** | 怀旧 / 人文 / 文学 / 独立杂志 | `#2a1e13` | `#eedfc7` |
| 5 | 🌙 **沙丘** | 艺术 / 设计 / 创意 / 画廊 | `#1f1a14` | `#f0e6d2` |

完整六行变量（`--ink` / `--ink-rgb` / `--paper` / `--paper-rgb` / `--paper-tint` / `--ink-tint`）：

```css
/* 🖋 墨水经典 */
--ink:#0a0a0b;      --ink-rgb:10,10,11;
--paper:#f1efea;    --paper-rgb:241,239,234;
--paper-tint:#e8e5de;  --ink-tint:#18181a;

/* 🌊 靛蓝瓷 */
--ink:#0a1f3d;      --ink-rgb:10,31,61;
--paper:#f1f3f5;    --paper-rgb:241,243,245;
--paper-tint:#e4e8ec;  --ink-tint:#152a4a;

/* 🌿 森林墨 */
--ink:#1a2e1f;      --ink-rgb:26,46,31;
--paper:#f5f1e8;    --paper-rgb:245,241,232;
--paper-tint:#ece7da;  --ink-tint:#253d2c;

/* 🍂 牛皮纸 */
--ink:#2a1e13;      --ink-rgb:42,30,19;
--paper:#eedfc7;    --paper-rgb:238,223,199;
--paper-tint:#e0d0b6;  --ink-tint:#3a2a1d;

/* 🌙 沙丘 */
--ink:#1f1a14;      --ink-rgb:31,26,20;
--paper:#f0e6d2;    --paper-rgb:240,230,210;
--paper-tint:#e3d7bf;  --ink-tint:#2d2620;
```

---

## 三 · 主题节奏（和类名预检同等重要）

每页必须是 `slide light` / `slide dark` / `slide light hero` / `slide dark hero` 之一。**不要只写 `hero`。**

**强制规则**：

- 每 2–3 页切换一次明暗，**连续 3 页以上同色 = 视觉疲劳，不允许**
- 8 页以上必须有 ≥1 个 `hero dark` + ≥1 个 `hero light`
- 整个 deck 不能只有 `light` 正文页，必须有 `dark` 正文页制造呼吸
- 每 3–4 页插 1 个 hero 页（封面 / 幕封 / 问题 / 大引用）

生成后自检：`grep 'class="slide' index.html`，逐个确认节奏合理再交付。

### hero 页的三层背景

骨架已内建，不要自己重写：

1. `slide::before` — 遮罩层。普通页 78% 不透明 + 3px 模糊；`hero` 页降到 `light 16%` / `dark 12%` 且**去掉模糊**
2. `slide.hero::after` — 上下渐变压暗，保证文字可读
3. WebGL canvas — 流体 / 等高线 / 色散，**只在 hero 页透出**

> **哲学第 1 条：克制优于炫技。** WebGL 只在 hero 页可见，普通页几乎看不见。hero 页因此不能放太多文字。

---

## 四 · 十种版式骨架

不要从零写 slide，从 `references/` 对应骨架改文案和图片路径。

| Layout | 用途 |
|---|---|
| 1 开场封面 | 第 1 页 |
| 2 章节幕封 | 每幕开场 |
| 3 数据大字报 | 抛硬数据 |
| 4 左文右图（Quote + Image） | 身份反差 / 故事 |
| 5 图片网格 | 多图对比 / 截图实证 |
| 6 两列流水线（Pipeline） | 工作流程 |
| 7 悬念收束 / 问题页 | 幕末 / 收尾 |
| 8 大引用页（Big Quote） | 衬线金句 / takeaway |
| 9 并列对比（Before / After） | 旧模式 vs 新模式 |
| 10 图文混排（Lead Image + Side Text） | 信息密集的图文页 |

**叙事弧**（没大纲时用它搭骨架）：

```
钩子 Hook     → 1 页    : 反差 / 问题 / 硬数据，让人停下来
定调 Context  → 1–2 页  : 背景 / 你是谁 / 为什么讲这个
主体 Core     → 3–5 页  : 核心内容，用 Layout 4/5/6/9/10 穿插
转折 Shift    → 1 页    : 打破预期 / 提出新观点
收束 Takeaway → 1–2 页  : 金句 / 悬念 / 行动建议
```

---

## 五 · 组件速查

| 组件 | 类名 | 要点 |
|---|---|---|
| 页眉页脚 | `.chrome` / `.foot` | 几乎每页都要有；`chrome.right` 固定放 `NN / TOTAL` |
| 引用框 | `.callout` + `.q-big` + `.cite` | hero 页上要加 `position:relative;z-index:2` 防被遮罩盖住 |
| 数字矩阵 | `.grid-6` / `.grid-4` / `.grid-3` + `.stat` | 三段式：`.m` 等宽标签 → `.n` 巨数字 → `.l` 描述；单位用 `<em style="font-size:.4em;opacity:.5">` |
| 平台卡 | `.plat` | `.sub` / `.name` / `.nb` 三行 |
| 表格行 | `.rowline` | `.k` 衬线关键词 · `.v` 正文 · `.m` 右对齐等宽标签 |
| 支柱卡 | `.pillar` | `.ic` 可以是序号也可以是 Lucide 图标 |
| 荧光标记 | `.hi` | 只对关键 1–3 个词用，别大面积 |
| 巨型背景字 | `.ghost` | 34vw / opacity .06；用了要给其他内容加 `z-index:2` |
| 图标 | `<i data-lucide="name">` | **严禁 emoji** |

**常用 Lucide**：判断 `compass target crosshair` · 关系 `share-2 users network link` · 品牌 `crown gem award star` · 流程 `workflow route repeat` · 数据 `bar-chart-3 trending-up activity` · 审美 `palette brush eye sparkles` · 对错 `check-circle x-circle`

---

## 六 · 图片规则（血泪经验）

1. **网格里必须用 `height:Nvh` 固定高度，不要用 `aspect-ratio`** → 会撑破父容器导致图片堆叠
   推荐档位：`.h-16` `.h-18` `.h-22` `.h-26` `.h-28`
   同一组图**必须同一高度**，不许一张 25vh 一张 21vh
2. **`object-position:top center`**（骨架已设）→ 只允许裁底部，**严禁裁左右和顶部**（那是图片的身份信息区）
3. 只用标准比例：`16:10` / `4:3` / `3:2` / `1:1` / `16:9`。不要复制原图的奇葩比例（如 2592/1798）
4. 网格多图用**内联 grid**，不要用 `.grid-3`
5. **不要给图片加 `align-self:end`** → 会滑到页底撞翻页组件。用 grid + 顶对齐
6. 信息图 / 截图再设计：给 `.frame-img` 同时加 `.fit-contain`，防图内文字被裁
7. 图片没到位时用占位符 `.img-slot`，**占位符优于烂实现**

---

## 七 · 动效五配方

由 Motion One 驱动，骨架已内建加载器（先试本地 `assets/motion.min.js` → 回落 jsdelivr → 都失败则强制 `opacity:1`，**内容永远可读**）。

你只需在 HTML 加 `data-animate`（给 section，选配方）和 `data-anim`（给叶子元素）。

| 配方 | 触发 | 行为 | 对应版式 |
|---|---|---|---|
| `cascade` | 默认 | 逐元素 stagger 淡入，75ms/step | 3 / 4 / 5 / 10 |
| `hero` | `.hero` 页自动 | 慢节奏 stagger，160ms/step，仪式感更强 | 1 / 2 / 7 |
| `quote` | `data-animate="quote"` | 其他元素先出，`data-anim="line"` 的行 550ms 间隔逐句揭示 | 8 |
| `directional` | `data-animate="directional"` | `left` 从左滑入 → divider → `right` 从右滑入 | 9 |
| `pipeline` | `data-animate="pipeline"` | `step` 保持 15% 透明，按 → 逐个点亮，**最后一步才放行翻页** | 6 |

**加在哪**：✅ 每个有独立语义的块（kicker / h1 / lead / callout / stat / figure / rowline）、多列的每一列
**不要加在**：容器（`.grid-6` / `.frame`）、每个 `<li>`、整页不想动就不要加任何标记

---

## 八 · 交付前必查（P0，全过才算完）

1. **大标题必须是衬线** —— 显示成非衬线 = 类名预检没做，骨架里漏了定义
2. 图片网格只用 `height:Nvh`，**没有 `aspect-ratio`**
3. 图片没有堆到页底（无 `align-self:end`）
4. 图片只用标准比例
5. 中文大标题 ≤ 5 字且 `nowrap`（避免 1 字 1 行）
6. **用 Lucide，不用 emoji**
7. 衬线标题 / 非衬线正文 / 等宽元数据，三分工没有混

---

## 九 · 能力边界

| 交付格式 | 支持 | 说明 |
|---|---|---|
| **网页 deck** | ✅ **原生** | 这是本风格的主场：WebGL 背景 + 横滑翻页 + 演讲者模式 |
| **原生 PPTX** | ⚠️ 降级 | 可以把排版翻译成 SVG→PPTX，**但 WebGL 动态背景会变成静态底图**，翻页动画也没了 |
| **PDF** | ✅ | 网页 deck 浏览器打印，或从 PPTX 导出 |
| **MP4** | ⚠️ | 网页 deck 录屏，或转 PPTX 后导出 |

**要 WebGL 就必须是网页 deck。** 这个取舍要在风格门第 3 问里跟用户讲清楚。
