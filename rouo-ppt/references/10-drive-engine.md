# 量产线 · COM 直驱引擎

> 量产线是数据驱动的产线：把事实与数据整理成页面 JSON，用元素路由 + COM 直驱，让本机安装的 WPS 或 PowerPoint **可见地**把整个 deck 生成出来。
> 适合：数据密集、模板统一、机构介绍/招生/汇报、一次出多份同构 deck。
> **引擎是随 skill 发布的脚本 `scripts/com_drive.py`**，不是文档里一段待复制的代码 —— 直接跑即可。
> 页面数据格式 → `11-deck-data-format.md`；设计预设与质检 → `12-presets-review.md`。
> PPTX 装配的通用坑（烘图、图层、体积）→ `27-pptx-assembly.md`。

---

## 一 · 引擎与项目的关系

引擎只有一份，在 skill 里；项目目录只放**内容**与**素材**：

```
rouo-ppt/scripts/com_drive.py      ← 引擎（随 skill 发布，不要拷进项目）
project/
├── gen_charts.py        ← 图表工厂（生成所有透明底 PNG）
├── images/              ← 图表输出
│   ├── chart_nums.png
│   └── chart_week.png
├── deck_data.json       ← 页面数据：主题 + 每页 elements[]
├── template_bg.png      ← 母版底图（可选；不给就用 theme.bg 纯色）
└── exports/             ← 引擎产出（pptx / pdf / png）
```

**为什么引擎不进项目**：

| 拷进项目 | 引擎留在 skill |
|---|---|
| 每个项目一份 300 行代码，修 bug 要改 N 处 | 改一处，全部项目受益 |
| 项目之间版本漂移，行为不一致 | 行为统一 |
| 换机构要重写全部代码 | **只改 `deck_data.json` + 主题色 = 新 deck** |

**批量出同构 deck**：一个实例一个子目录，共用同一个引擎和同一个 `gen_charts.py` 模板，改数据即可。

**为什么图表工厂必须与 deck 解耦**：图表可单独重跑（改数据不重跑 deck），deck 也可单独重跑（图上没问题时），互不牵连。

---

## 二 · 五工步标准工序

### 工步 1 · 采料

- **事实核验**（铁律 1）：`WebSearch` 核每一个要写进页面的数据，结果落 `facts.md`。**禁止编造**
- **主题色**：从品牌资产提取，写进 `deck_data.json` 的 `theme`（用户品牌 > 预设）
- **母版底图**（可选）：从用户模板 PPTX 里提媒体图，或不要底图、用纯色

```python
# extract_bg.py — 从用户模板 PPTX 提取母版背景为 PNG
import zipfile, os, shutil
pptx_path, out_dir = r"用户模板.pptx", r"./work"
os.makedirs(out_dir, exist_ok=True)
with zipfile.ZipFile(pptx_path) as z:
    media = sorted(n for n in z.namelist()
                   if "media" in n and n.lower().endswith((".png", ".jpg", ".jpeg")))
    if media:
        shutil.copyfileobj(z.open(media[0]), open(os.path.join(out_dir, "template_bg.png"), "wb"))
```

> 验证：`template_bg.png` 存在且为 16:9。不提底图时，页面用 `theme.bg` 铺纯色，同样成立。

### 工步 2 · 图表工厂（matplotlib）

**铁律（违反则图表不可用）**：

| 规则 | 正确 | 错误 |
|---|---|---|
| 背景 | `rcParams["savefig.transparent"] = True` | 白底/有色底，会盖住模板 |
| 文字颜色 | `#333` 系深色 | 白色（白底看不见）、`#888`（投影对比不足） |
| 品牌色用途 | **只用于色块** | 用于文字（投影看不清） |
| DPI | 250 | <150（放大模糊） |
| 字体 | SimHei / Microsoft YaHei，**显式指定并校验已安装** | 系统默认（中文变方框） |

**校验透明度的正确姿势**（这条是踩坑换来的）：

```python
# ✗ 形同虚设：图四周留白本就透明，坐标区是白底时最小值照样 < 255
alpha.getextrema()[0] < 255

# ✓ 看透明像素占比 + 抽查中心区
transparent_ratio = (alpha 采样中 < 8 的比例)     # 应 > 0.30
center_opaque     = (中心 40% 区域中 > 250 的比例)  # 不应接近 1.0
```

**尺寸对照**：

| 图表类型 | figsize | PPT 中建议尺寸 (pt) |
|---|---|---|
| 四列数字卡 | (10, 2.2) | 800 × 176 |
| 单张柱状图 | (7, 3) | 490 × 210 |
| 横向柱状图 | (7, 3.2) | 490 × 260 |
| 六列宽图 | (10, 3) | 840 × 250 |

> 验证：`images/` 下图表齐全、全部透明底、dpi=250。

### 工步 3 · 编排页面数据

逐页写 `deck_data.json`（格式 → `11-deck-data-format.md`）。布局硬规则：

- 每页 ≤80 中文字 + **≥2 种视觉元素**（图表/表格/形状）
- 标题结束 y≈52 → 第一个内容元素 **y≥76–90**（≥24pt 间隙），**绝不让内容紧贴标题**
- 内容元素 `y+h ≤518`、`x+w ≤960`（顶/底满宽出血条不受此限）
- 目录 `items 数 × item_h < 500 − start_y`

### 工步 4 · 直驱生成

**前置检查**：

```bash
# 探测本机可用的引擎（逐引擎独立子进程，结果才可信）
python scripts/com_drive.py probe
```

**先跑质检，不通过就别浪费一次 Office 启动**：

```bash
python scripts/com_drive.py review deck_data.json   # 只算分，不连 Office
python scripts/com_drive.py drive deck_data.json --dry-run   # 校验数据 + 图片存在性
```

**直驱生成**：

```bash
python scripts/com_drive.py drive deck_data.json \
    --engine wps \                  # auto（默认，WPS 优先）| wps | ms
    --out exports/deck.pptx \
    --pace 0.45 \                   # 每写一个元素停 0.45 秒 —— 肉眼看生成过程
    --shot shots \                  # 每写完一页，让应用自己导出该页 PNG
    --shot-window shots/window \    # 每写完一页只截「文稿窗口」自身（带标题栏）
    --png exports/png \             # 存盘后导出每页 PNG
    --pdf \                         # 同时导出 PDF
    --keep-open                     # 保留窗口以便目视
```

**关键选项语义**：

| 选项 | 说明 |
|---|---|
| `--pace SEC` | 每元素停顿秒数。设 0.3–0.5 就能看清「一个元素一个元素长出来」 |
| `--shot DIR` | **应用自身把该页渲染成 PNG**。第 N 页导出成功 ⇒ 前 N 页已存在于文稿里，这是「逐页写出来」的硬证据 |
| `--shot-window DIR` | 只截**文稿窗口自身**（`PrintWindow`，窗口被遮挡/最小化也行）。带标题栏与缩略图栏 → 「应用确实开着这份文稿」的最佳凭证 |
| `--shot-desktop DIR` | 整屏截图。⚠️ 记录的是屏幕现状（谁在最前就截到谁），证据力最弱 |
| `--keep-open` | 默认会退出「本任务独占的实例」避免进程堆积；要留窗口检查就加它 |
| `--kill` | ⚠️ 强杀 wps/wpp/powerpnt。**默认关闭**，会丢未保存内容，别轻易用 |

> 验证：PPTX 体积正常（>100KB）、页数与数据一致、`--shot` 每页都有 PNG。
> 「现场感」的推荐组合：`--pace 0.15 --shot-window DIR`（每页一张带标题栏的窗口照）。

**元素路由**：7 种元素类型（`text` / `image` / `shape` / `table` / `card_list_wide` / `num_big` / `tagline_bar`）全部由引擎内置实现，项目侧只写数据。详见 `11-deck-data-format.md`。

**引擎内置的两条安全设计**：

1. **身份实证**：取到实例后用 `Application.Path` 核对厂商，与请求不符就**中止并报错**，绝不偷偷给你另一个引擎的文件。
2. **不动你的进程**：不再无脑 `taskkill`。实例用 `DispatchEx` 独占创建，退出它不会波及你正在编辑的文档。

### 工步 5 · 五维质检

```bash
python scripts/com_drive.py review deck_data.json   # 机器可算部分，<70 分返修
python scripts/com_drive.py drive deck_data.json --strict   # 不达标直接拒绝生成
```

人工目视重点（完整维度 → `12-presets-review.md`）：标题颜色统一、图文间距 ≥24pt、表格文字单行不换行、大数字与标签不重叠、背景未被遮挡、每页 ≤80 字 + ≥2 种视觉元素。

---

## 三 · 元素与布局的对应（数据侧视角）

14 种版式的结构安排见 `12-presets-review.md`。在数据里，它们表现为元素组合：

| 版式 | 元素组合 |
|---|---|
| `cover` 封面 | 顶底出血条 + 大标题 + 副标题 + 数字卡图 |
| `toc` 目录 | `card_list_wide` |
| `timeline` 时间轴 | 时间轴图 + `card_list_wide` / 文字节点 |
| `stats` 数字统计 | 多个 `num_big` + 说明文字 |
| `data_table` 数据表格 | `table` + 文字解读 |
| `chart_page` 图表页 | `image`（图表）+ 要点行 |
| `closing` 结语 | 满版色块 + 总结文字 |

**每页收尾用 `tagline_bar`**：一句话把该页结论钉死。

---

## 四 · 本机实测踩过的坑（全部带复现结果）

> 这一节是这份文档最有价值的部分。每一条都在本机（Windows + WPS 12.1 + MS Office 16）真实复现过。

### 坑 1 · ProgID 不足以判断引擎身份 —— 而且顺序会改变结果

WPS 会把「版本无关」的 Office 兼容 ProgID 抢到自己名下：

| 场景（同一进程内） | `PowerPoint.Application.16` 落到 |
|---|---|
| 只碰 `.16` | ✅ MS Office 16.0 |
| 先碰 `KWPP.Application`，再碰 `.16` | ❌ WPS（而且是另一个 WPS 实例） |

**推论**：`probe` 若在**同一进程**里先探 WPS 再探 MS，会自我污染，把可用的 MS Office 报成不可用（本机真报过）。
**对策**：每个引擎在**独立子进程**里探测；取到实例后用 `Application.Path` 实证身份。

### 坑 2 · `Dispatch` 会复用已在跑的实例，`DispatchEx` 才不会

这是最贵的一条：

| 取用方式 | 结果 |
|---|---|
| `win32com.client.Dispatch("PowerPoint.Application.16")` | ❌ WPS（复用已有实例） |
| `win32com.client.DispatchEx("PowerPoint.Application.16")` | ✅ 真 MS Office 16.0 |

请求 MS Office 却拿到 WPS，**且不报任何错**。引擎必须用 `DispatchEx`，并保留身份实证作为兜底。

### 坑 3 · COM 一律吃绝对路径，相对路径**静默失败**

`Slide.Export("shots/slide01.png", "PNG", 1920, 1080)` 返回成功但文件不存在；换成绝对路径立刻正常。
本项目在**两处**独立踩到（`pptx_assembly.py` 的 COM 回导、`com_drive.py` 的逐页导出）。
**对策**：所有传给 COM 的路径先 `resolve()`。

### 坑 4 · 截「窗口」别按类名/面积挑，要用 **PID 差分 + PrintWindow**

先记踩错的版本：`ImageGrab.grab(bbox=窗口矩形)` 截回来的是 WPS 的 **ribbon 条**而不是文稿画布 ——
按类名（`KLiteMainWindowShadowBorder`、`Chrome_WidgetWin_0`、`Qt5QWindowIcon`、`OpusApp`…）或按面积挑都挑错了，
而 WPS **不提供** `Application.HWND`（调用报「找不到成员」）。同进程里还挂着多个伪窗口（如 237×39 的 `PROME-TASKBAR`）。

**可行解**（已封进 `--shot-window`）：

1. 只认类名含 **`FrameClass`** 的顶层窗（WPS 实测 `PP12FrameClass`，MS 同族）
2. 用**接入前后的 PID 差分**认领自己的窗口 —— `DispatchEx` 起的是独占实例，新出现的 PID 一定是我们的；
   标题匹配 `pres.Name` 仅兜底（WPS 标题更新有延迟，中途可能还叫「演示文稿1」）
3. 最小化先 `ShowWindow(SW_RESTORE)`，再 `PrintWindow(hwnd, mdc, 2)`（`PW_RENDERFULLCONTENT`）
   让窗口**自己重绘**到位图 —— 不抢焦点、不比 Z 序
4. 全黑即视为失败，回落整屏截图

> ⚠️ 附带纠正一条早期误记：**不是**「WPS 顶层窗口全部 `IsWindowVisible=0`」。实测 `PP12FrameClass` 会报**可见**，
> 报 0 的是那些伪窗口。当时据此下的「只能整屏」结论过窄，现已改为可精确截窗口。

### 坑 5 · 「浮到最前」做不到 —— 但取证不必依赖前台

`pres.Windows(1).WindowState = 3` + `.Activate()` 只改变 **COM 层的 `ActiveWindow`**（实测读回来确实切换了），
**不能**让窗口在屏幕上盖过其他应用 —— Windows 前台锁不允许后台进程抢焦点。

**对策**：承诺「引擎会打开应用并逐元素写入」，**不要承诺「窗口一定跳到最前」**。取证走三条通道：
`--shot`（页面内容，最硬）· `--shot-window`（窗口自身，带标题栏与缩略图栏）· `--shot-desktop`（整屏，最弱）。
要「现场看见」可再叠 `ShowWindow(SW_MAXIMIZE)`（`--shot-window` / `--shot-desktop` 已自动做一次）。

### 坑 6 · `Presentation.Export` 与 `Slide.Export` 参数不同

- `Presentation.Export(dir, "PNG", w, h)` —— 导出全部页到目录
- `Slide.Export(file, "PNG", w, h)` —— 导出单页到文件；**只给一个路径参数会报「无效的参数数目」**

### 坑 7 · Windows 下 `glob` 大小写不敏感，计数会翻倍

`len(glob("*.PNG")) + len(glob("*.png"))` 会把同一批文件数两遍（本机真报过「3 张」显示成「6 张」）。
**对策**：只 glob 一次。

### 坑 8 · 质检规则本身也会误报，别改数据去迁就它

引擎第一版质检把两类合法元素误判为违规：

| 误报 | 真相 | 正确规则 |
|---|---|---|
| 底部品牌出血条 `y+h=540 > 518` | 规范里顶/底出血条本就在 y=534 | 满宽出血条**豁免** 518 约束（它属版面框架，不是内容） |
| 注释行 14pt「正文字号 <20pt」 | 规范里 Caption 就是 14–15pt | 只有 **16–19pt** 才是「本该 20pt 的正文缩了水」，14–15pt 合法 |

**教训**：质检器报警时，先判断是数据错还是规则错。规则错就**修规则**。

---

## 五 · 常见报错速查

| 报错 | 原因 | 解决 |
|---|---|---|
| 请求 ms 却报「真实身份是 WPS」 | 用了 `Dispatch` 而非 `DispatchEx` | 引擎已内置 `DispatchEx`；若仍报，说明该 ProgID 在本机确实指向 WPS |
| `Slide.Export` 成功但文件不存在 | 传了相对路径 | 用绝对路径 |
| `Quit` AttributeError | WPS 的 COM 退出信号 | `try/except` 包裹，忽略 |
| `'int' object has no attribute 'lstrip'` | 颜色已被提前转成整数 | 只对 hex 字符串调 `h2b()` |
| 图片不显示 | 相对路径 / 文件不存在 | 引擎按工作目录解析绝对路径；缺失时静默跳过并汇总上报 |
| 中文显示方框 | 未装 SimHei | 换 Microsoft YaHei |
| PPTX 0KB | 目标文件被其他进程占用 | 关掉 WPS 里同名文件后重试 |
| 数字和标签重叠 | `num_big` 间隙不足 | 引擎用三段式（40%+10%+50%），别手改 |
| 表格文字换行遮挡 | 未设 `WordWrap=False` | 引擎已强制单行 |
| JSON 语法错误 | 中文引号 `“”` | 用 ASCII 双引号；引擎会报出**具体行列**与常见原因 |
| 元素被静默跳过 | 类型名写错 | 引擎会汇总「未知元素类型」并在收尾打印 |

---

## 六 · 与另外两条线的关系

- **同享底座**：事实核验、品牌资产、反平庸守则、Gate 文件（`facts.md` / 品牌资产）三线都要
- **方向决策**：模板底图 / 主题色 / 版式基调确认后才批量生成。确认载体可以是一次方案说明，但**停轮等确认**是硬要求
- **接力**：量产线生成后若某几页需要定制设计，把那几页交给手作线重做，最后合并；**同一页不混用两套视觉规范**
- **降级**：无 WPS/Office 的机器上量产线不可用 → 整体切手作线或网页线，向用户明说原因
