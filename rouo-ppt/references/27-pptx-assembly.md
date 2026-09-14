# 水彩风 PPTX 装配 · HTML 设计稿 → 原生可编辑 PPTX

> `23-style-watercolor.md` §5.2 只给了原则（「晕染烘图、文字保持原生文本框」）。
> 本文是把它做出来的**完整方法 + 本机实测出来的五个坑**，全部数字来自实机验证。

---

## 一 · 为什么要专门做这件事

水彩风的质感来自 `feTurbulence` + `feDisplacementMap` 的毛边，而 **DrawingML 没有滤镜**。
所以 PPTX 侧只有一条路：**装饰层烘成位图，文字留原生**。

但直接照做会撞上两个反直觉的问题（都实测过）：

| 问题 | 症状 | 原因 |
|---|---|---|
| **烘图爆体积** | 三页 1920×1080@2x 的单张 PNG 合计 **29 MB** | 满版纸纹是极淡噪点（opacity .055），噪点让 PNG 彻底失去可压缩性 |
| **文字位置漂移** | 文字整体偏上或偏下 3–12 px，且不同字号偏得不一样 | HTML 的 `top` 是**行盒顶**，PPTX 的文本框顶到**首行基线**的换算由渲染器自己决定，两者不天然相等 |

本文的解法就是针对这两条。

---

## 二 · 坐标映射（唯一正确的换算）

设计稿 1920×1080 px ↔ 幻灯片 13.333×7.5 in = 12192000×6858000 EMU：

```
1 px = 6350 EMU          （12192000 / 1920，正好整除）
1 px = 0.5 pt            （960 pt / 1920 px，正好整除）
字号 96px → 48pt         行距 1.42 × 96px → Pt(68.16)
```

**这两个数是整的**，不要用 96 DPI 那套（1px=0.75pt），那会让整个 deck 缩到 2/3。

---

## 三 · 装配五步

### 第 1 步 · 烘图拆两层

**不要烘成一张。** 把装饰层拆成互斥的两张，用同一份 HTML 派生（靠 CSS 互斥隐藏），保证像素级对齐：

| 层 | 隐藏什么 | 背景 | 格式 | 理由 |
|---|---|---|---|---|
| **纸纹底** `paper/` | `.wash` + `.content` | **不透明**（纸色） | **JPEG q94, subsampling=0** | 近乎平坦，平坦面看不出 JPEG 损失；体积降一个数量级 |
| **晕染层** `wash/` | `.paper-grain` + `.content` | **透明** | **PNG-8 / 256 色 + alpha** | 大面积透明；且规范说「JPEG 会把毛边变成块噪」针对的正是这一层 |

```python
# 纸纹底：Chrome 正常截图（不透明）
# 晕染层：加 --default-background-color=00000000 得到真透明
chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
       --force-device-scale-factor=2 --window-size=1920,1080 \
       --default-background-color=00000000 --virtual-time-budget=8000 \
       --screenshot=wash.png file:///.../wash/C-1.html
```

**后处理**（这一步不能省）：

```python
from PIL import Image
# 纸纹底 -> JPEG
Image.open(paper_png).convert("RGB").save(jpg, "JPEG", quality=94,
                                          optimize=True, subsampling=0)
# 晕染层 -> 256 色（alpha 一并进调色板），quantize 用 FASTOCTREE + 抖动
im = Image.open(wash_png).convert("RGBA")
im.quantize(colors=256, method=Image.FASTOCTREE,
            dither=Image.FLOYDSTEINBERG).save(wash_png, "PNG", optimize=True)
```

**实测效果**（三页 1920×1080@2x）：

```
                          原始 PNG     处理后
纸纹底 ×3                 3.42 MB/页   0.54 MB/页 (JPEG)
晕染层 ×3                 8.4–11 MB/页 0.18–0.56 MB/页 (PNG-8)
合计                      29 MB        2.68 MB        → 装配后 pptx 1.63 MB
```

量化保真度实测 **PSNR 47–54 dB**（>40 dB 即可察觉阈值以下）。4 倍放大检查毛边无色带、无硬边。

> ⚠️ 别用 `optimize=True` 重存 Chrome 的 PNG —— 实测反而**变大**（2.89 → 3.30 MB）。
> 真正省体积的是**量化**，不是重压缩。

### 第 2 步 · 组装图层顺序

```python
slide.background.fill.solid();  slide.background.fill.fore_color.rgb = PAPER   # 兜底
add_picture(paper_jpg, 0, 0, W, H)     # 纸纹底
add_picture(wash_png,  0, 0, W, H)     # 晕染层
# 然后才是全部原生文本框         ← 文字永远最上层，且下方必须是干净区
```

### 第 3 步 · 文本框必须这样设

```python
box = slide.shapes.add_textbox(emu(left), emu(top + DY[key]), emu(w), emu(h))
tf = box.text_frame
tf.word_wrap = False                      # wrap="none"，防止意外折行
tf.auto_size = MSO_AUTO_SIZE.NONE         # 关掉自动缩放，否则会偷改字号
tf.vertical_anchor = MSO_ANCHOR.TOP
tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
p.line_spacing = Pt(lh_px * 0.5)          # 精确行距（spcPts），不是倍数
p.space_before = Pt(0); p.space_after = Pt(0)
```

**行距必须用精确值**（`Pt(...)` → `a:spcPts`）而不是倍数：
倍数行距会跟字体自带的巨大 CJK 行高（Noto CJK ≈ 1.45em）相乘，行距一变，位置全乱。
给了精确行距，行高就完全确定，`dy` 才可预测、可校正。

**字体必须同时设 latin 与 ea**：

```python
def set_run_font(run, latin, ea, size_px, color, spc):
    f = run.font
    f.name = latin          # ⚠️ python-pptx 的 font.name 只写 a:latin
    f.size = Pt(size_px * 0.5)
    f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):          # 中文由 a:ea 决定，不写就掉成默认字体
        el = rPr.find(qn(tag)) or rPr.makeelement(qn(tag), {})
        el.set("typeface", ea); rPr.append(el)
    rPr.set("spc", str(int(spc)))         # 字距，单位百分之一磅（.30em@19px → 285）
```

### 第 4 步 · 实测回填垂直偏移（关键）

不要试图推导公式——**直接测**。闭环：

```
HTML 截图（基准） ──┐
                    ├─→ 逐元素量墨水包围盒 → dy = pptx_top − ref_top → DY = −dy
PPTX COM 回导 ──────┘                                        ↓
                                         回填 DY → 重建 → 再测，直到 |dy| ≤ 2px
```

```python
# 墨水量测：区域内与纸色的最大通道差 > 45 视为墨水，一行至少 3 像素才算
mask = np.abs(np.asarray(crop, np.int16) - PAPER).max(axis=2) > 45
rows = np.where(mask.sum(axis=1) >= 3)[0]
```

**两个必须注意的地方**：

1. **量测区域必须避开晕染层**。笔触落在区域内会把包围盒顶拉到框边，量出的 dy 全是假的。
   本机实战：第 1、3 页笔触起于 x≈1206 → 文字区 `x1` 收到 1195；第 2 页地平线横贯全宽
   （y 660–810）→ 正文框底收到 640。
2. **`|dy| ≤ 2` 是噪声，别去「修正」它**，否则等于加噪声。

**本机实测的 dy 规律**（Noto Serif SC，仅供参考，**换环境必须重测**）：

| 行距 lh | 实测 dy | 说明 |
|---|---|---|
| 0.86 | −12 px（92px 字号） | Georgia 大数字 |
| 1.42 | −5 ~ −7 px | 断言大字 |
| 1.17 | ≈ 0 | 眉标 / 页脚 |
| 1.95 | +1 px | 正文 |
| 2.05 | +3 px | 清单行 |
| 1.75 | +3 px | 注释 |

即：**行距 ≤1.42 时 PPTX 偏上，≥1.75 时偏下**。不呈简单线性，故逐元素实测。

### 第 5 步 · COM 回导验收

```python
# DispatchEx 起独占实例、ProgID 从高版本起试 —— 避免落到 WPS（详见 10-drive-engine.md §四）
app = next(win32com.client.DispatchEx(p) for p in (
    "PowerPoint.Application.16", "PowerPoint.Application.15",
    "PowerPoint.Application.14", "KWPP.Application", "PowerPoint.Application"
) if _probe(p))
pres = app.Presentations.Open(pptx, ReadOnly=True, Untitled=False, WithWindow=False)
for i, slide in enumerate(pres.Slides, 1):
    slide.Export(str(out / f"slide{i:02d}.png"), "PNG", 1920, 1080)
```

> 实际工具里这个「逐 ProgID 起实例」的逻辑已封成 `scripts/pptx_assembly.py` 的 `_new_engine()`，直接 `pptx-export` 即可，不必手写。

> ⚠️ **`Slide.Export` 的路径必须是绝对路径**。相对路径会被 PowerPoint 按自己的工作目录解析，
> 报 `抱歉，找不到 xxx\slide01.png`。同理 `Presentations.Open` 也要绝对路径。

最终验收口径：**逐元素 `|dx| ≤ 1px`、`|dy| ≤ 1px`**，并出一张「HTML 基准 | PPTX 回导 | 差值×3」
三栏对照图肉眼过一遍。

---

## 四 · 五个坑（都是实机撞出来的）

### 坑 1 · PowerPoint 在 `wrap="none"` 下不应用制表位

想把「标签 + 内容」放进同一段、用 `a:tabLst` 对齐？XML 写得再对（元素次序完全合规）也没用：

```xml
<a:pPr algn="l">
  <a:lnSpc><a:spcPts val="2357"/></a:lnSpc>
  <a:spcBef/><a:spcAft/>
  <a:tabLst><a:tab pos="558800" algn="l"/></a:tabLst>   <!-- 完全合法 -->
</a:pPr>
<a:r>放假</a:r><a:tab/><a:r>10 月 1 日…</a:r>            <!-- 渲染时 tab 零推进 -->
```

**解法：标签列与内容列拆成两个独立文本框。** 代价是两列字号不同 → 首行基线不同，
用第 4 步的实测法分别校正即可（本机实测：标签列需 +9，内容列需 −3，两个文本框都把基线落回同一 y）。

### 坑 2 · 小字号文本框会被自己的字号压扁行距

标签列字号 15px、内容列 23px，但两列**共享同一个行盒**，行距应为 `2.05 × 23 = 47.15px`。
如果按各自的字号算行距，标签列会变成 `2.05 × 15 = 30.75px`——**三行标签占的竖向跨度差了 30%**。

**解法：给文本框一个显式行距参数**，小字号那列强制继承行的统一行距。

### 坑 3 · 可变字体的默认实例

`C:\Windows\Fonts\NotoSerifSC-VF.ttf` 的 `wght` 轴 **默认值是 200（ExtraLight）**，
而设计稿要的是 300/400。理论上 PowerPoint 会取到 ExtraLight。

**但本机实测取到了正常字重**（墨量 HTML 9.20% vs PPTX 9.19%，几乎相同）。
→ **不要照理论推断，一定要实测**。字体名用 `Noto Serif SC` 即可，不要自作聪明改成别的。

> 查询命令：`fontTools.ttLib.TTFont(path)['fvar']` 看 `axes` 与 `instances`。

### 坑 4 · Chrome 截图路径与 Python 路径不是一回事

Git Bash 里 `/tmp/xxx` 会被 Python 解析成 `C:\tmp\xxx`。跨工具传路径时**一律用 Windows 绝对路径**
（`--screenshot="D:\\proj\\bake\\a.png"`、`file:///D:/proj/bake/a.html`）。

### 坑 5 · 别用「重存 PNG」省体积

`Image.save(..., optimize=True, compress_level=9)` 对 Chrome 输出的 PNG **实测变大**
（2.89 → 3.30 MB）。省体积靠**调色板量化**（2.89 → 0.56 MB）。

### 坑 6 · `RGBColor` 是 tuple 子类，不是 int 子类

写规格文件时想把颜色转成字符串，**用 `str(c)`**（得到 `'241F1A'`）：

```python
str(RGBColor(0x24,0x1F,0x1A))     # -> '241F1A'   ✅
int(RGBColor(0x24,0x1F,0x1A))     # TypeError      ❌ 它不是 int
list(("文字", RGBColor(...)))      # ['文字', (36,31,26)]  ❌ json 会写成数组
```

规格里的颜色一律写 `'RRGGBB'` 字符串。`pptx_assembly.py` 的 `_rgb()` 也接受 `[r,g,b]` 三元组。

---

## 五 · 交付自检

- [ ] `|dx| ≤ 1px` 且 `|dy| ≤ 1px`（逐元素实测）
- [ ] PPTX 能在 PowerPoint 打开，文字**双击可改**（不是图）
- [ ] 放大 4 倍看毛边：**无色带、无硬边**（量化没伤到质感）
- [ ] 体积合理（本机三页 1.63 MB）；纸纹底是 JPEG、晕染层是 PNG
- [ ] 图层顺序：纸纹 → 晕染 → 文字（文字在最上层，且下方干净）
- [ ] 三栏对照图（基准 | 回导 | 差值）肉眼过了
- [ ] 已知降级已向用户明说（本机：注释行的中日韩字形在 PPTX 侧为 Noto Serif SC 合成斜体，
      比浏览器宽度略窄 ~4%；CJK 标点在 PPTX 侧略宽）

---

## 六 · 配套脚本

`scripts/pptx_assembly.py` 把上面三步做成了可复用工具：

```bash
python scripts/pptx_assembly.py optimize  <bake_dir>              # 烘图后处理
python scripts/pptx_assembly.py assemble  <spec.json> <out.pptx>  # 装配
python scripts/pptx_assembly.py measure   <ref_dir> <pptx_png_dir> <regions.json>
python scripts/pptx_assembly.py export    <pptx> <out_dir> [width]   # COM 回导
```
