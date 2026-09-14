# 风格族 2 · 极简风（瑞士国际主义）

> 美学锚点：像 Massimo Vignelli + *Helvetica Forever*。
> 骨架：`assets/deck-shell-minimal.html`
> 违反下面任何一条，画面会**瞬间从瑞士掉到 PowerPoint**。

---

## 一 · 六条灵魂（先记这个）

1. **单一锚点色** —— 一份 deck 只用一个 accent，不允许多色高亮拼贴
2. **极致字号对比** —— 主标题与正文比例 **≥ 8:1**；KPI 必须是 Data Hero（屏幕宽度 18–22%）
3. **无衬线只此一家** —— Inter / Helvetica / Noto Sans SC，**出现任何衬线都是错的**
4. **直角纯色** —— 不允许渐变 / 阴影 / 圆角（rule 横线除外）
5. **网格至上** —— 所有元素吸附 12 栏网格，左对齐 + 大幅留白做非对称美学
6. **Hairline 是手术刀** —— 1px 极细分割线就够，不加粗、不加阴影

> 点阵装饰只在 hero 页透出，正文页保持纯净底色。

---

## 二 · 四套主题色（只能选，不能自定义）

**替换变量共 10 个**：`--paper` `--paper-rgb` `--ink` `--ink-rgb` `--grey-1/2/3` `--accent` `--accent-rgb` `--accent-on` `--accent-bright`

> ⚠️ **`--accent-bright` 是暗底高亮色**（暗色页上的 accent 提亮版）。上游预设清单只给了 9 个变量、漏了它，**切主题时必须一并改**，否则暗色页的高亮会沿用上一套主题的颜色。骨架里的注释也标了它。

**灰阶 4 套完全一致，不要改**（这是校过色的"高级灰"，改成纯白/纯黑会丢失克制质感）：

| 变量 | 值 | 用途 |
|---|---|---|
| `--paper` | `#fafaf8` | 主底色（极浅暖白） |
| `--grey-1` | `#f0f0ee` | 浅灰底（区块底） |
| `--grey-2` | `#d4d4d2` | 中灰（分割线 / border） |
| `--grey-3` | `#737373` | 暗灰（辅助文字 / meta） |
| `--ink` | `#0a0a0a` | 文字主色（近黑） |

| # | 主题 | 适合 | `--accent` | `--accent-on` | `--accent-bright` |
|---|---|---|---|---|---|
| 1 | 🔵 **克莱因蓝** IKB | 通用 / 商业发布 / AI 科技 / 设计。最经典，绝不出错 | `#002FA7` | `#ffffff` | `#5B7BFF` |
| 2 | 🟡 **柠檬黄** | 年轻 / 运动 / 零售 / 消费品 / Y2K | `#FFD500` | `#0a0a0a` | `#FFE566` |
| 3 | 🟢 **柠檬绿** | 生态 / 可持续 / 健康 / Z 世代 / AI 创业 | `#C5E803` | `#0a0a0a` | `#D6F451` |
| 4 | 🟠 **安全橙** | 工业 / 警示 / 运动 / 汽车 / 转折点页 | `#FF6B35` | `#ffffff` | `#FF9A6B` |

**可读性要点**：
- 柠檬黄、柠檬绿是**浅色高饱和 → `--accent-on` 必须用纯黑**，黄底放白字会糊掉
- 安全橙介于明暗之间 → 白字勉强可读，**字号要加粗到 `font-weight:600` 以上**
- IKB 泛滥就掉档，**不要满屏蓝**；橙色满屏刺眼，只做局部高亮

---

## 三 · 字号字重阶梯（越大越细，不是感性描述）

| 字号区间 | 字重 | 典型场景 |
|---|---|---|
| ≥ 8vw | **200** ExtraLight | 封面大字、巨号 KPI、h-statement |
| 4–7.9vw | 200–300 | 章节标题、大编号 |
| 1.8–3.9vw | 300–400 | 中型标题、takeaway 标题、中号数字 |
| 1–1.7vw / 16–20px | 400–500 | 正文段落、卡片描述 |
| 13–15px | 500–600 | meta、kicker、角标、图表标签 |

**硬规则**：
- 同一页内，**字号越小的元素字重必须 ≥ 字号越大的元素**（不允许 16px 正文用 300 而标题用 500）
- 16px 左右的小字**拒绝 weight 300**（太细不可读），最低 400，推荐 500
- 封面 / IKB 反白大标题内的强调字用 `italic + weight 300`，**不要用 accent 色**（蓝压蓝看不见）
- **大字字重 200 是灵魂**，禁止 600/700/800 大字

### 演示最小字号（投屏硬下限）

| 文本类型 | 最小 |
|---|---|
| 正文段落 / 主要说明 | **18px** |
| 卡片描述 / 列表 / 时间线说明 / caption / 图注 | **16px** |
| meta / kicker / mono 标签 / 图表标签 | **14px** |

放不下就**先删文案、拆两页、换版式**，不要把字号压到 10/11/12/13px。

### 中文大标题字号分档（必做）

中文方块字视觉面积大，不能直接套英文的 6.8–7vw：

| 标题形态 | 字号 |
|---|---|
| 1 行，≤ 8 个中文字 | `min(6.4vw,11.2vh)` |
| 2 行，每行 ≤ 8 字 | `min(5.8vw,10.2vh)` |
| 2 行，任一行 9–12 字 | `min(5.2vw,9.2vh)` |
| 3 行或更长 | 优先改写标题；不得已用 `min(4.6vw,8.2vh)` |

**大字号必须双约束限高** `font-size:min(Xvw,Yvh)` —— 只用 vw 在标准 16:9 屏会溢出。
标题挤占图片或正文时：**先压缩文案，再降字号**，不要靠把下方内容推到底硬塞。

---

## 四 · 版式锁：正文页只能用登记的 22 式

**瑞士主题默认进入 locked mode**：

- 正文页只能使用登记版式 `S01`–`S22`；新增首页/尾页只能用 `SWISS-COVER-ASCII` / `SWISS-CLOSING-ASCII`
- 每个 `<section class="slide">` **必须写 `data-layout="Sxx"`**，没有 `data-layout` 视为未登记版式
- **不允许临时发明** `P23` / `P24` / `Swiss Image Split` 这类结构（除非用户明确要实验版式）
- 顶部中文标题**默认左对齐**、处在左上内容轴。不要把小标题放左列、大标题放右列造成视觉居中；只有 statement / split 版式允许强中心叙事
- **SVG 只负责几何图形，不要在 SVG 里写文字标签** —— 所有标签改用 HTML 网格 / 卡片 / caption
- 地理 / 历史 / 路线 / 地点关系页用 **`S08 + 地图组件`**（先读骨架里 S08 右槽的 MapLibre 实现），仍保留 `data-layout="S08"`

| Layout | 用途 | | Layout | 用途 |
|---|---|---|---|---|
| S01 Index Cover | 原始索引封面 | | S12 Manifesto + Ink Banner | 阶段性结论 |
| S02 Vertical Timeline + KPI | 演化对比 / 年代变迁 | | S13 Three Forces | 3 个对等概念 |
| S03 Split Statement | 核心论点 / 左右分屏 | | S14 Loop Form | 自学闭环 / 自动化 |
| S04 Six Cells | 6 项概念定义 | | S15 Matrix + Hero Stat | 8–12 项矩阵 + 总数据 |
| S05 Three Layers | 三层架构 | | S16 Multi-card Brief | 6 项快讯小卡 |
| S06 KPI Tower | 4 项数据视觉化高度差 | | S17 System Diagram | 三层架构 / 生态地图 |
| S07 H-Bar Chart | 5–10 项排名比较 | | S18 Why Now | 三论点 + 数据支撑 |
| S08 Duo Compare | Before / After 对照 | | S19 Four Cards | 4 项等权特性 |
| S09 Dot Matrix Statement | 大引述 / statement | | S20 Stacked KPI Ledger | 纵向账单数据 |
| S10 Split Closing | 收束页 | | S21 Tech Spec Sheet | 产品规格 / benchmark |
| S11 Horizontal Timeline | 4–7 步流程 | | S22 Image Hero | 21:9 顶图 + 标题块 + 三列 KPI |

**版式多样性硬规则**：
- 7–8 页 deck 至少用 **6 个不同 S 编号**；10 页以上至少 **8 个**
- 不允许连续 3 页同一主体结构（例如连着三页 `head + grid + card`）
- 图片页**不能偷懒发明新结构**：2–3 张图用 S15/S16 的原始网格改造成图片格；单张大图用 S22
- 开写 HTML 前先列一张 `页码 → data-layout → 选用理由 → 图片槽位` 草稿

**通用 / 专用要分清**：S03 / S08 / S11 / S19 较通用；S06 / S07 / S20 / S21 / S22 是**数据/案例专用**；S14 / S15 / S17 是**结构专用**。别把数据专用版式拿来讲概念，也别把可选组件堆成装饰。

---

## 五 · 组件硬规则

| 规则 | 说明 |
|---|---|
| 卡片四类互斥 | `card-ink` / `card-accent` / `card-fill` / `card-outlined` **不能混用**（禁止"蓝底+蓝描边"、"灰底+描边"） |
| 多卡并列统一 | 3–12 张卡用同一类（优先 `card-fill` 灰底）；只突出一项时单独换 `card-accent`，且**只允许一张** |
| 直角到底 | 任何 `border-radius` 都不允许；装饰用 **8×8 直角小方块**，不要 9px 圆形点 |
| 图标 | `<i data-lucide="name">` + `lucide.createIcons()`，**选棱角风格**（避免圆胖），**不自己画 SVG** |
| 时间线对齐 | axis 列固定 12px + dot 绝对定位，**不要用 grid `justify-self`**（会与虚线错位） |
| 章节标题间距 | 章节级标题与内容间距 **≥ 9vh**，避免拥挤 |
| 装饰元素 | bars 矩阵 / 点阵 / ring-mat **严格在 grid 内**，不能贴边或溢出 |
| 底部安全区 | nav 在 ~97vh，内容收尾**不要过 93vh**；需要贴底用 `.nav-safe-bottom` / `.nav-safe-bottom-tight`，**不要手写 `bottom:2vh`** |
| 每页一个语义化动效 | 数字 scale 弹入 / bar scaleY 拉起 / SVG stroke 描线 / 节点序列点亮；**禁止所有页用同一个 generic 配方** |
| reveal 容器 | `[data-anim]` 容器先强制 `opacity:1`，配方内再用 motion `{opacity:[0,1]}` 覆盖，否则有些页会"看不见" |
| ESC 索引页 | cloned slide 必须有 CSS override 让 `[data-anim]` 在缩略图里 `opacity:1` |
| 中文字体兜底 | Windows 没有"苹方"，必须 fallback 到 `"Microsoft YaHei UI","Noto Sans SC"`（骨架已配） |
| 低功耗键 | 右下角必须提示 `B 静态`；按 `B` 切换 `body.low-power`，停掉 WebGL / ASCII canvas 的 RAF 和入场动画 |

### 字体变量（跨主题固定，骨架已配）

```css
--sans:    "Inter","Helvetica Neue","Helvetica","Arial","Segoe UI Variable","Segoe UI",system-ui,sans-serif;
--sans-zh: "PingFang SC","Hiragino Sans GB","Source Han Sans SC","Noto Sans SC","Microsoft YaHei UI","Microsoft YaHei",sans-serif;
--mono:    "JetBrains Mono","IBM Plex Mono","SF Mono","Cascadia Code","Consolas",ui-monospace,monospace;
```

**本机降级**：Google Fonts 不可达 → 拉丁文字落到 Helvetica / Arial / Segoe UI，中文落到 Noto Sans SC / 微软雅黑，等宽落到 Consolas。**全是无衬线，风格不破**，观感影响很小。间距 token `--sp-3`…`--sp-13`（8 到 160px，8px 基线）不受影响。

---

## 六 · 图片规则（瑞士风专属）

- 单张大图用 **S22**；多图用 S15 / S16 原始卡片网格改造，**不要用未登记的 P23/P24**
- 生成图片前先写 `data-image-slot`：`s22-hero-21x9` / `s15-grid-21x9` / `s16-brief-21x9`
- S22 配图默认 **21:9**，提示词必须含 `subject centered in the safe middle area`；照片容器用 `object-position:center 35%`，**不要用 `top center`**
- 图片容器**必须直角、无阴影、无圆角**；默认背景用白 `var(--paper)`，**不要用灰底包白底信息图**
- 白底信息图 / 流程图 / UI 图**默认不要加外框描边**，不要随手套 `.swiss-keyline`；要强调只用 `.swiss-lined` 的顶部 accent 线
- UI / 文字密集的原始截图用 `.fit-contain`；已按槽位重生成的图用 `.frame-img.r-21x9` / `.r-16x10` **铺满容器**，不要固定 `height:18vh` 把图缩小成小贴片
- 多图同组**统一槽位、比例、高度、边距、线条粗细**，不能一张 `contain` 另一张 `cover`

**图片比例规范**：S22 顶图 `21:9`（主体放中央安全区）· 多图格统一 `21:9` 或统一 `16:10`（不混用）· 全屏主视觉 `16:9` + `max-height:64vh` · 图文混排小图 `3:2` / `3:4`

---

## 七 · 图文混排决策树

先判断图片在这页的角色，再决定容器、比例、裁切：

- **证据截图 / UI / 代码 / dashboard** → 保真优先，关键文字和数据不能被裁；统一比例时用程序化背景画布 + `.fit-contain`，不要为了铺满而裁掉 UI
- **已按槽位重生成的信息图 / 插图** → 按槽位铺满，不要再用短高度缩小
- **照片 / 产品图 / 人物图** → 标准比例 + 明确 `object-position`；主体、人脸、产品不能被标题、caption 或裁切压住
- **文字压图 / 全屏主视觉** → 先做 quiet-zone 判断，图里至少要有约 **30% 低细节区域**承载文字；不通过就换图、换裁切或改分栏。只在必要时加局部 tint，**不要整页套黑/白遮罩**
- **多图组** → 统一比例、高度、容器处理、caption 密度
- **生成图是素材，不是整页 slide** → 图片内部不要自带页眉、页脚、页码、logo、主标题、装饰边框或署名，避免和 deck chrome 重复

---

## 八 · 生成后校验

```bash
node <SKILL_ROOT>/scripts/deck_validate.mjs index.html
```

校验器会做：登记版式检查（`data-layout` 是否在 S01–S22）、图片槽位、SVG 文字、标题对齐；环境中能解析到 Playwright 时还会做**真实渲染后的测量**：

| 测量项 | 含义 |
|---|---|
| `M1 DOM/visual overflow` | 超出多少 px，最低/最高问题元素 |
| `M1 bottom whitespace` | 底部空白多少 px，active content height 占比 |
| `M1 nav-safe` | 最低内容是否进入底部分页安全线 |
| `M2 title gap` | 标题和下一块内容之间的实际距离 |

### 先量后改：修正阶梯

| 超出 | 动作 |
|---|---|
| 1–40px | 只微调，上移内容组或收紧一个 gap/padding。**不要删内容** |
| 40–90px | 局部压间距或模块高度，仍优先保留内容 |
| 90–160px | 轻微压标题或压缩一段正文，必要时拆页 |
| 160px+ | 才考虑换版式、合并模块或删内容 |

修完再跑一次。**如果 `bottom whitespace` 变大，说明修过头了** —— 恢复部分间距、放大最后一块，或把内容组向下回调。

---

## 九 · 交付前必查（24 条精华）

1. **全程无衬线** —— 出现任何衬线都是错的（查 `font-family` 有没有误用 `--serif`）
2. **只有一个 accent 色** —— 不能同时出现 IKB + 柠檬黄 + 安全橙
3. **不允许渐变 / 阴影 / 圆角** —— 任何 `box-shadow` / `linear-gradient` / `border-radius>0` 都砍掉（rule 横线除外）
4. 极致字号对比 —— 主标题与正文 **≥ 8:1**
5. 大字号**双约束限高** `min(Xvw,Yvh)`
6. 大字字重 **200**，禁止 600/700/800 大字
7. 卡片填充四类**互斥**，不混用
8. 多卡并列统一样式；只突出一项时 `card-accent` **只允许一张**
9. **直角到底** —— 装饰用 8×8 直角方块，不要 9px 圆点
10. 图标用 Lucide，不自己画 SVG，选棱角风格
11. 时间线 axis 列固定 12px + dot 绝对定位，不用 grid `justify-self`
12. 章节级标题与内容间距 **≥ 9vh**
13. **每页一个语义化动效配方**，禁止全部 generic
14. `[data-anim]` 入口 reveal 容器先 `opacity:1`
15. ESC 索引页里 `[data-anim]` 可见
16. 中文字体兜底到 `"Microsoft YaHei UI","Noto Sans SC"`
17. 字重体例：大字 200 / 正文 300 / `t-cat` 600 / `t-meta` mono uppercase
18. 保留低功耗键 `B 静态`
19. 装饰元素严格在 grid 内，不贴边不溢出
20. 底部内容预留 nav 空间，收尾不过 93vh
21. 图片容器直角无阴影；边界只用 hairline
22. S15/S16/S22 同组图片比例、高度、边距、线条粗细一致
23. 组件角色正确 —— S15/S16 图片格需要 caption 锚点；S22 的 KPI/说明是必选；**数据专用版式必须有真实数据，不能靠文案硬填**
24. 通用 / 专用版式分清，不拿数据版式讲概念

---

## 十 · 能力边界

| 交付格式 | 支持 | 说明 |
|---|---|---|
| **网页 deck** | ✅ **原生** | WebGL 网格/点阵背景 + 横滑 + 演讲者模式 + 低功耗键 |
| **原生 PPTX** | ✅ 可翻译 | 直角纯色 + hairlines + 大字重 200 这套语言，翻到 PPTX 后**风格损失最小**（本风格是本机唯一"两栖"都很强的） |
| **PDF** | ✅ | |
| **数据密集页** | ✅ | KPI Tower / H-Bar / Stacked Ledger / Tech Spec 是它的支柱版式 |

**注意**：本风格的"数据专用版式"必须喂真实数据。没有数据时改用 S03 / S13 / S19 这类概念版式，不要拿 S06/S07 硬填文案。
