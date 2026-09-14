# 形状语言 · 原生形状选择与几何技法

> 手写 SVG 时用：当原生轮廓或受支持的形状/文本操作能忠实表达目标对象时，怎么选轮廓、怎么落地成 PowerPoint 可编辑形状。

---

## 一 · 总原则

**先选轮廓，再写语法。** 按对象**要做什么**选几何，不按「哪种 SVG 语法短」选。普通 `<rect>` / `<circle>` / `<ellipse>` / `<line>` 不是「低一档」。

**判断链**：页面工位 → 构图动作 → 轮廓/边缘语言。

**硬规则 —— 语义契合，不是名字联想**：形状名、主题词、隐喻都不是使用证据。卷轴不是通用「手册」载体，闪电不是「价格张力」，`chartX/chartStar` 是分区符号不是图表，流程图符号只属于真正的流程图，动作按钮不产生动作，logo/图标字形**永远不是预设形状**。

---

## 二 · 落地形态（SVG → 原生 PPTX 对应）

| SVG 编写形态 | 导出后的原生结果 |
|---|---|
| 普通 `<rect>` / 圆角 rect / `<circle>` / `<ellipse>` / `<line>` | 对应的可编辑预设几何 / 线条 |
| 完整预设片段（`<g data-pptx-authoring="preset">`） | 一个精确的 `a:prstGeom` 形状，或连接符预设导出为 `p:cxnSp` |
| 布尔结果路径 | 可编辑的 `a:custGeom`（是轮廓，不是可回放的「合并形状」历史） |
| 独立原子 + 内容的语义组 | 一个分组构造，子元素仍可**分别**编辑 |

### 布尔决策门

| 需要的结果 | 构造方式 |
|---|---|
| 已有预设轮廓能表达 | 保留它；**绝不**用操作数重建 |
| 形状重叠但需各自可编辑 | 同一语义组里的独立图元 |
| 一条连续外轮廓 | `union`（`combine` 仅用于刻意的对称负区） |
| 真正的孔 / 切边 / 揭露 | `subtract`，可见主体在前 |
| 只保留公共区域 | `intersect` |
| 独占区与共享区需不同样式 | `fragment`，每个区域各留一个形状 |

⚠️ **合并只用于「必须成为单一轮廓」的几何**——绝不为了简化结构树去合并文字、图片、图标或独立装饰。

---

## 三 · 预设形状词表（按 Office 图库分类概览）

完整注册词表共 187 个预设名，九大类。**这是浏览辅助，不是白名单或配额**——图元、组合构造、必要自由路径或干脆不画，都可能是最佳结果。

| 类目 | 代表族与名字 |
|---|---|
| **1. 线条** | `line` `lineInv` `straightConnector1`；`bentConnector2-5`（1-4 折）；`curvedConnector2-5` |
| **2. 矩形** | `rect` `roundRect`；单/双/对角/圆切角族（`round1Rect` `snip2DiagRect`…） |
| **3. 基本形状** | 三角族 `triangle` `rtTriangle`；斜四边形 `diamond` `parallelogram` `trapezoid`；正多边形 `pentagon`…`dodecagon`；有机 `ellipse` `teardrop`；径向 `pie` `blockArc` `donut` `arc`；框架 `frame` `halfFrame` `corner`；括号/花括号族；字面图形 `cube` `can` `heart` `sun` `cloud` `lightningBolt`；分区符号 `chartX` `chartStar` `chartPlus` |
| **4. 块箭头** | 舞台形 `homePlate` `chevron`；基本方向 `rightArrow`…`downArrow`；多轴 `leftRightArrow` `quadArrow`；折返 `bentArrow` `uturnArrow`；环形 `circularArrow`；曲线 `curvedRightArrow` `swooshArrow`；带文字的 callout 变体 |
| **5. 公式形状** | `mathPlus` `mathMinus` `mathMultiply` `mathDivide` `mathEqual` `mathNotEqual` |
| **6. 流程图** | `flowChartProcess` `flowChartDecision` `flowChartDocument` `flowChartTerminator` 等——**只用于真正的流程图** |
| **7. 星与旗帜** | `star4`…`star32` `irregularSeal1/2`；`ribbon` `ellipseRibbon`；`verticalScroll` `horizontalScroll`；`wave` `doubleWave` |
| **8. 标注** | 指向另一对象的注释体（`wedgeRectCallout` `cloudCallout` 等） |
| **9. 动作按钮** | 只有几何、无动作、无链接 |

**选形流程**：工位（这页为读者做什么）→ 浏览词表按意义缩小候选 → 推理性与性格契合该页的那个轮廓 → 编码落地。

**形状优先的图示规则**：细关系用 `<line>`；标准折/曲用精确连接符预设；实心方向用块箭头预设；只有以上都无法表达关系、数据几何或锁定的手绘风格时，才用开放自由路径。

---

## 四 · 纯几何建模技法（推荐手写，全部可原生导出）

只用普通几何 + 渐变，就能做出有体积感的形状：

### 4.1 明暗交替渐变 = 体积感（最高产出技法）

圆柱、金属带、立体数字、曲面面板，来自**一条 stop 交替「亮·暗·亮」**（三停）或「亮·暗·亮·暗·亮」（五停）的渐变。交替读作「曲面两次受光」；两停渐变永远读作平面。
**要点**：所有 stop 同一色相、只变明度；一页只保留一个光照方向；去掉描边让面干净相接。

### 4.2 手搭倒影（不用「映像」效果）

`transform="translate(0, 2·y_bottom) scale(1, -1)"` 复制翻转 → 只留顶部 10–25% → 上面压一个从「对象底部全透明」渐变到「页面背景色」的矩形 → 整体透明度 60–70%。**不要模糊。** 适合证书行、产品图、logo 瓦片。

### 4.3 fragment 做分层模型

从一个剪影造出**配准**的分层图示：三角形被条切出金字塔层级；圆被两条条切成象限轮——每片继承母轮廓，整体保持配准。切数、位置从已解析的拓扑推导。

### 4.4 渐变替代柔边（不用「柔化边缘」）

| 意图 | 替代构造 |
|---|---|
| 接触阴影 | 椭圆 + radialGradient（中心暗透明 → 边缘透明） |
| 聚光/舞台光池 | 锥形或椭圆，远端渐隐为透明，低透明度压在场景上 |
| 物体融入页面 | 矩形，渐变从透明到**页面背景的确切 hex** |
| 隐藏但保留存活 | 全透明，或与背景配准的填充 |

径向/线性 alpha 渐变在幻灯片尺度读作羽化边，且完整导出。**绝不用堆叠描边轮廓近似柔边。**

### 4.5 地面与承台

漂浮在空画布上的物体看起来像贴上去的。给它一个宽浅椭圆或梯形（渐隐到背景），可选下方加柔暗椭圆接触阴影。梯形向内收 = 远去的地面。**保持低对比**——是承台不是内容。两个形状就能让证书行、产品主视觉「构图立住」。
