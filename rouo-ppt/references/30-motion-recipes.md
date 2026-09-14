# 动效配方与决策树 · 网页 deck 的动效纪律

> 什么时候读：网页线**每一页**动工前。动效不是「加得越多越高级」，是**预算制**——
> 每页只用一种 recipe，服务于这一页的**表达意图**。
>
> 运行时已在骨架里内建，**不要去改 JS**。你只做两件事：给 `<section>` 选一个 recipe，
> 给要揭示的元素标一个角色。

---

## 一 · 两个数据属性（唯一需要掌握的接口）

| 属性 | 挂在哪 | 作用 | 取值 |
|---|---|---|---|
| `data-animate="<recipe>"` | `<section class="slide">` | **整页的揭示配方**。一页只能一个 | 见 §二 配方表 |
| `data-anim="<role>"` | 页内任意元素 | **这个元素参与揭示**，并按角色决定初始位移 | 见 §三 角色表 |

没有 `data-animate` 的页走默认配方 `cascade`（顺序淡入上浮）。

```html
<section class="slide accent" data-animate="hero" data-slide-id="cover">
  <div data-anim="kicker" class="t-meta">…</div>
  <h1 data-anim="title">…</h1>
  <div data-anim="lead">…</div>
</section>
```

**三条兜底机制（已内建，别自己再加）**：

1. 动效运行时加载失败 → 所有 `[data-anim]` **直接可见**，不破坏阅读
2. `body.low-power` → 全站动效关闭（低功耗/弱设备开关，键名见 `34-web-tweaks.md`）
3. 总览模式下 `[data-anim]` 强制可见（总览是「看全局」，不是「放动画」）

---

## 二 · 配方表（21 个已注册 recipe）

**recipe 与版式是一一对应的**：先按内容选版式（`22-style-minimal.md` §四 的登记版式），
recipe 跟着版式走，**不要自创 recipe 名**（不在下表的名字 = 不生效，静默退回 `cascade`）。

| recipe | 对应页面意图 | 揭示节奏 |
|---|---|---|
| `hero` | 封面 / 章节幕封 | 索引线 → 标题 → 底部信息，三段 |
| `progression` | 递进（1× → 10× → 1000×） | 头行先立，数字逐级放大 |
| `statement` | 极简陈述 / 大宣言 | 逐行 600ms 淡入，一行一个节拍 |
| `grid-reveal` | 多格定义（六格 / 四列） | 逐格揭示，行列有序 |
| `stack-build` | 层叠构建 | 由下往上堆叠出现 |
| `measure-up` | 指标爬升 | 数值/柱从零长到位 |
| `bar-grow` | 柱状对比 | 柱体依次生长 |
| `duo-mirror` | 双轨对照（A vs B） | 左右镜像同时进场 |
| `split-statement` | 左右分栏宣言 | 左半先立，右半跟上 |
| `timeline-walk` | 纵向时间轴 | 沿时间轴逐节点走 |
| `manifesto` | 收束宣言 | 整段压轴，最慢一拍 |
| `three-forces` | 三力卡片 | 三张三段进 |
| `loop-form` | 闭环流程 | 沿环逐段显影 |
| `matrix-fill` | 矩阵 / 同心圆系统图 | 由中心向外或由格到格 |
| `field-notes` | 要点清单 / 观察笔记 | 行级递进，最克制 |
| `system-diagram` | 系统关系图 | 节点先于连线 |
| `why-now` | 三列递进 + 巨数 | 列先立，巨数后落 |
| `four-cards` | 四列均分卡 | 四张同步错峰 |
| `stacked-ledger` | 台账 / 账本行 | 自上而下逐行入账 |
| `tech-spec` | 规格表 / 参数表 | 表头先落，行数据跟进 |
| `image-hero` | 顶部横幅主图 | 图先铺，文字压上 |

### 选 recipe 的决策树

```
这页的核心表达是什么？
├─ 一个「时刻」的定场（封面/幕封/收束）        → hero / manifesto
├─ 一个「顺序」（流程/时间/步骤/台账）           → timeline-walk / loop-form / stacked-ledger / pipeline
├─ 一个「对比」（A/B、旧/新、多方案）            → duo-mirror / bar-grow / four-cards
├─ 一个「结构」（网格/矩阵/系统）                → grid-reveal / matrix-fill / system-diagram
├─ 一个「数字」（指标/巨数）                     → measure-up / progression / why-now
├─ 一段「文字」（陈述/清单/规格）                → statement / field-notes / tech-spec
└─ 一张「图」（横幅/证据）                       → image-hero
```

**一页只用一种 recipe。** 需要两种节奏，说明这一页承载了两个意图——**拆页**，不要叠配方。

---

## 三 · 角色表（`data-anim` 取值）

**方向类**（决定初始位移，其余交给 recipe）：

| 取值 | 初始状态 |
|---|---|
| `line` | 上浮 10px + 淡入（最常用，行级文字） |
| `left` / `right` | 左右 24px 滑入（分栏、对照） |
| `left\|right` | 中缝先后向两侧展开（分隔线场景） |

**语义类**（表达力更强，recipe 会按语义给不同权重与顺序）：

`kicker` · `title` · `title-block` · `lead` · `hero` · `img` · `bottom` · `foot` ·
`kpi` · `bars` · `step` · `arrow` · `ledger` · `rules` · `manifesto` · `signature`

**什么元素该加 `data-anim`**：

- ✅ 版式的**结构骨架**：页眉角标、大标题、引子、主体块、底部信息
- ✅ 数字矩阵的每一格、时间轴的每个节点、流程的每一段
- ❌ 装饰性发丝线、背景纹理、已由 recipe 接管的容器
- ❌ 已有 `data-anim` 的父元素的子元素（**嵌套标记 = 双重位移，会飘**）

---

## 四 · 节奏与缓动（叙事五段）

动效的**总时长**远不如**顺序**重要。一个 deck 的动效节奏按叙事弧走（`12-presets-review.md` §三）：

| 叙事段 | 动效性格 | 建议 |
|---|---|---|
| 钩子（封面） | 稳、慢、有仪式感 | `hero`，总揭示 1.2–2.0s |
| 背景 / 问题 | 克制，信息优先 | `statement` / `field-notes`，≤ 1.0s |
| 方法 / 结构 | 有秩序感，按结构顺序 | `grid-reveal` / `loop-form`，按格/段递进 |
| 结果 / 数据 | 干脆，数字要有「落下」的实体感 | `measure-up` / `bar-grow` / `why-now` |
| 收束 | 最慢一拍，留呼吸 | `manifesto`，≥ 1.5s |

**缓动原则（通用）**：

- 入场用 **ease-out**（快起慢停），出场用 ease-in
- 不要用弹簧/回弹（bounce/elastic）——那是 demo 感，不是杂志感
- 位移距离小（10–24px）、时长中（400–800ms）；**距离大 + 时长短 = 廉价**

---

## 五 · 动效常见坑（都是真踩过的）

### 1. 叠层坐标系

**规则**：任何包含 `position: absolute` 子元素的容器，**必须**显式 `position: relative`。

**为什么**：不给 relative，absolute 子元素会以更外层的定位祖先为坐标系——真踩过，
包着 3 个绝对定位子元素的容器没设 relative，子元素直接飘到画布外 200px。

**自查**：每写一个 `position: absolute`，往上数祖先，确认最近的**定位**祖先就是你想要的那个坐标系。

### 2. 稀有 Unicode 字符变豆腐

**规则**：**不依赖稀有字形**。可视化「空格 token」用了 `␣`（U+2423 OPEN BOX），
本机字体全都没有这个字形 → 渲染成空白或豆腐块，观众什么都看不到。

**自查**：只使用常规标点与汉字/拉丁字母；需要特殊符号时**用图形画**，不要赌字体。

### 3. 动效把元素停在半路

页面切换时若前一个 recipe 的动画还在跑，元素会停在中间态。骨架已在切页时先复位
（`resetAnims` + 取消在跑动画）。**不要**为了「更顺」自己再叠一层动画。

### 4. 动效与备注错位（演讲者模式）

动效的推进节拍**必须**和备注分段对齐：一处停顿对应一个 beat。备注怎么写见 `25-web-deck.md` §五。

### 5. `prefers-reduced-motion`

尊重系统的减弱动效偏好：动效关闭时，页面必须**依然完整可读**（骨架的兜底已保证）。
不要写「不动效就不显示」的样式。

### 6. 动效吃性能

同页元素超过 ~20 个都加 `data-anim` 时，低端机会掉帧。**选择性标记结构骨架**，
不要把每个 `<span>` 都标上。

---

## 六 · 与另外两条线的分工

| 场景 | 走哪 |
|---|---|
| 网页 deck 逐页揭示 | 本文件（`data-animate` / `data-anim`） |
| 备注 / 旁白 / 音频 / 导出视频 | `16-motion-voice.md` |
| 视频的**镜头运动**（zoom/pan/parallax）与分镜 | `33-video-storyboard.md` |
| 原生 PPTX 的动画（对象动画 / 切换效果） | `16-motion-voice.md`，走 COM `AddEffect` |
| 交付前动效是否「有 bug」的测量 | `29-preflight-checklist.md` |

> 一句话记法：**元素怎么动看本文件，镜头怎么动看 33，声音和旁白看 16。**
