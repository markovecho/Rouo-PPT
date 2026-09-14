# 原生编辑已有 PPTX

> 用户带来一个**已有 `.pptx` 且其设计必须存活**：填模板、部分重写、改某几页保住其余、加备注/旁白/切换。**绝不从零重生成，绝不跑生成管线。**

---

## 何时走这条线

| 用户想要 | 路线 |
|---|---|
| 把原始 PPTX 填新内容保住设计；改写某几页；删/重排/重复页；加备注/旁白/切换 | **本路线** |
| 用全新视觉重生成每一页 | 手作线 `01-mainline.md` |
| 拆分/合并成新 deck | 生成路线，PPTX 当源材料 |
| 造可复用模板 | `15-template-system.md` |

**硬规则**：不跑模板导入器、项目初始化、SVG 后处理器，不建 `svg_output/`。往返工作区**就是**项目。

---

## 一 · 输入

🚧 **GATE**：源 PPTX（必需，原生设计权威）；内容变化时的新材料（文本/文档/URL 先转 Markdown：`python "…/scripts/tools.py" source <file>`）；可选交付意图（受众、页数、必留/必删页、备注、切换）。

**硬规则 —— 事实**：每页/每条备注的实质断言都来自用户材料；内容映射里没写来源的页**删掉**；模板占位文字**绝不**变成输出内容。

---

## 二 · 导入往返工作区

```bash
python "…/scripts/tools.py" import-pptx "<source.pptx>" -o "projects/<slug>_<日期>" --inheritance-mode both --roundtrip
```

| 路径 | 内容 | 读取规则 |
|---|---|---|
| `authoring-svg-flat/slide_NN.svg` | 每张源页一张紧凑可编辑 SVG | **只打开**要编辑或判断复用的页 |
| `authoring-svg-flat/authoring_summary.json` | 每页画布/文字/图片计数 | **先读它**做规划 |
| `images/` `notes/` | 源媒体与备注 | 保留文件名；字节一变引用页全重建 |
| `native-payloads/` `analysis/` | 不可变原生底座 | **不要读、改或引用** |

**硬规则 —— 源代理是原子的**：`<image data-pptx-source-proxy="native-restore">` 代表不受支持的原生对象（SmartArt、复杂效果）。**留着让它还原原对象**；编辑代理会导致导出失败。

---

## 三 · 规划输出 deck

**默认把清单当「幻灯片库」而非大纲**——源页版式已编码一种「修辞形状」，按结构逻辑匹配目标信息；目标故事决定顺序；源页可移动/省略/重复。

### 3.1 页面计划

仅当输出**不同于**源清单（子集、重排、重复）时，写 `page_plan.json`：

```json
{
  "schema": "roundtrip-page-plan.v1",
  "pages": [
    {"source_slide": 1},
    {"source_slide": 4, "svg": "chapter_market.svg"},
    {"source_slide": 7}
  ]
}
```

- 要复用同一源页两次 → 复制其 SVG 为新名并列出副本
- **合并页**：一个输出页只有一个骨架；从别的页搬对象**只用 adopt 命令**，绝不直接粘原始 SVG
- **新页**：复制最接近的源页为骨架，删掉页内内容，空画布上编写

### 3.2 增强模块

| 模块 | 默认 | 载体 |
|---|---|---|
| 演讲者备注 | 源备注随页走；只在计划处新增/改写 | `notes/<svg-stem>.md` |
| 旁白音频 | 请求时才开（隐含每页都要备注） | `16-motion-voice.md` |
| 页面切换/对象动画 | 保留源；仅在请求时替换/编写 | 导出 flag / `animations.json` |
| 原生图表/表格数据 | 源数据，除非计划改它 | 导出带 `--native-charts-and-tables` |

### 3.3 ⛔ BLOCKING 确认

在任何编辑/写备注/导出前，摆出计划并等明确确认：输出清单（每页→源页→引用/编辑/新副本+一行理由）、内容映射、模块开关。确认后写 `page_plan.json`。

---

## 四 · 编辑页面

首次编辑前读 `08-page-craft.md` 的技术契约部分。

**硬规则**：
- **只编辑计划内的页**——被引用的页绝不打开写
- **就地编辑、保留身份**——改文字/画法/位置时，**保留所有不想改的对象上的 `data-pptx-*` 属性**

| 编辑 | 规则 |
|---|---|
| 文字替换 | 按槽位**视觉容量**（几何+字号）适配，不按旧占位长度；溢出走「改短 → 拆页 → 更大源版式」，缩小字号是最后手段 |
| 封面/章节页 | 只替换标题/副标题/作者/章节标签 |
| 密集内容页 | 压到该页槽位数 |
| 原生表格/图表 | 编辑内联 JSON 的单元格/系列值，保留源结构 |
| 图片 | `<image>` 指向 `images/` 新文件，保留画框 |
| 来自别页的对象 | **只用** adopt 命令；代理不能移动 |

**编辑后必做**：刷新摘要 + 容量门质检：

```bash
python "…/scripts/tools.py" refresh-summary "projects/<slug>"
python "…/scripts/tools.py" check "projects/<slug>" --roundtrip
```

🚧 **GATE**：按画框估算被编辑文字；错误阻塞导出直到改写/拆分/移到更大版式。

---

## 五 · 导出与验证

```bash
python "…/scripts/tools.py" export "projects/<slug>" --roundtrip
```

可选：`--recorded-narration audio --use-narration-timings`（旁白+自动前进）、`--animation-config animations.json`（逐页动效）、`--native-charts-and-tables`（图表数据被编辑时）。

导出回执：`Round-trip export summary: output_pages=N passthrough=P cloned_passthrough=C patched=M rebuilt=R`

- `passthrough` = 恒等页、原始 XML
- `patched` = 保留源形状 XML，顺序/备注/切换变了
- `rebuilt` = 可见内容变了——**纯交付任务必须 rebuilt=0**

**验证**：交付检查 + 读回（页数等于计划长度、关键标题存在、备注数匹配）。

---

## 六 · 当前边界

**支持**：逐字节引用未改页；选定页编辑文字/画法/图片/原生表格图表数据；新元素写成紧凑 SVG；SmartArt/复杂效果保留为原子代理；备注/旁白/切换/动画按页叠加。

**不支持**：删除复制页上继承的源备注；编辑源代理；改幻灯片尺寸；添加 Master/Layout 结构（走 `15-template-system.md`）。
