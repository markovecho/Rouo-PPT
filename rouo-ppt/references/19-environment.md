# 本机环境实测 + 工具链登记

> 本机 **Windows + 受限网络** 的实测结论，**直接复用别重复试错**。
> 文末是本机已部署的工具链登记表——所有脚本调用统一经 `scripts/tools.py` 调度器，不要直接拼路径。

---

## 一 · 出网严格受限（最容易踩、代价最高）

### 1.1 稳定可达

| 域名 | 用途 |
|---|---|
| `cdn.simpleicons.org` | 单色品牌 glyph，可直接按品牌色上色——**logo 首选取图源** |
| `api.iconify.design` | 图标集 API |
| `cdn.jsdelivr.net` | JS/CSS/字体 CDN |
| `registry.npmmirror.com` | npm 镜像 |

### 1.2 不可达（别空转）

| 域名 / 服务 | 症状 |
|---|---|
| Wikimedia Commons | 连不上 |
| Clearbit logo API | 连不上 |
| Google favicon 服务 | 连不上——「拿不到 logo 就用 favicon 兜底」在本机是死路 |
| `fonts.googleapis.com` / `fonts.gstatic.com` | 连不上——网页里别写 Google Fonts `<link>`，一律本地字体 |

### 1.3 假阳性陷阱（返回 200 但没内容）

`wsrv.nl` 这类图片代理会返回 **HTTP 200 但 body 为 0 字节**。**不要只看状态码**——下载后务必核对：

```bash
file <downloaded>            # 确认是真 SVG/PNG
head -c 90 <downloaded>.svg  # 应以 <svg 开头
wc -c <downloaded>           # 明显偏小（~106 字节）= 占位，丢弃
```

---

## 二 · npm 装包必须走镜像

```bash
npm install <pkg> --registry=https://registry.npmmirror.com
```

---

## 三 · 已装字体（别去下 Google Fonts）

| 字体 | font-family 写法 | 用途 |
|---|---|---|
| **Noto Sans SC**（可变字重） | `"Noto Sans SC"` | 中文正文/标题 |
| **Noto Serif SC**（可变字重） | `"Noto Serif SC"` | 中文衬线/编辑感标题 |
| **Consolas** | `Consolas` | 数值/编号/微标签（配 `tabular-nums`） |
| **Georgia** | `Georgia` | 西文衬线 |
| **Segoe UI** | `"Segoe UI"` | 西文无衬线 |

⚠️ display 字体不用 Inter/Roboto/Arial/system（反平庸底线，品牌规范明确要求除外）。

量产线 COM 生成侧字体：SimHei（标题）/ Microsoft YaHei（正文）/ Arial（大数字）——由 Office/WPS 渲染，与本表 HTML 侧字体是两套体系。

---

## 四 · 截图：系统 Chrome headless（不必装 playwright 浏览器）

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu \
  --hide-scrollbars --force-device-scale-factor=1 --window-size=1920,1080 \
  --virtual-time-budget=6000 --screenshot="<Windows绝对路径>.png" "file:///D:/..."
```

- `--screenshot` **必须给 Windows 路径**（`D:\proj\out.png`），`/tmp` 这类 POSIX 路径会报错
- `file:///` URL 用正斜杠（`file:///D:/proj/page.html`）
- deck 场景 `--window-size=1920,1080`；网页/信息图 `1440,900`
- `--virtual-time-budget=6000` 给页面渲染留时间

## 五 · Chrome 超时与批量

- 单次调用超过约 120s 会被 SIGTERM——批量截图**拆成每张一次调用**
- `--print-to-pdf` 处理多 iframe 页会超时 → `run_in_background=true` 跑

## 六 · Windows python.exe 不认 Git Bash 的 POSIX 路径

传参一律用 Windows 反斜杠路径：
```bash
python "C:\Users\33551\..." --out "D:\proj\out.json"
```

## 七 · COM 直驱（量产线）

**引擎是 `scripts/com_drive.py`（随本 skill 发布，不要拷进项目）**。先探测再驱动：

```bash
python scripts/com_drive.py probe                                            # 逐引擎独立子进程
python scripts/com_drive.py drive deck_data.json --engine wps --pace 0.45 --shot shots
```

**本机实测的 ProgID 真相**（完整复现记录 → `10-drive-engine.md §四`）：

| ProgID | 实际指向 |
|---|---|
| `KWPP.Application` | WPS 12.1（金山 WPS Office 的 office6 目录） |
| `PowerPoint.Application` | ⚠️ 常落到 **WPS** —— 金山抢注了版本无关的 Office 兼容 ProgID |
| `PowerPoint.Application.16` | MS Office 16.0（Program Files 下的 Microsoft Office\Root\Office16） |

**三条硬约束**（每条都是踩坑换来的）：

1. **必须用 `DispatchEx`，不能用 `Dispatch`** —— 后者会复用已在跑的实例；
   实测 `Dispatch("PowerPoint.Application.16")` 拿到 WPS，`DispatchEx` 才拿到 MS Office，且前者**不报错**
2. **必须用 `Application.Path` 实证身份** —— ProgID 不足以判断引擎
3. **COM 只吃绝对路径** —— 相对路径下 `Slide.Export` / `SaveAs` **静默失败**（本项目两处独立踩到）

**不要无脑 `taskkill`**：本机实测 WPS 里可能同时开着**用户自己的文档**（真发生过，2 份文稿并行）。
`com_drive.py` 的 `--kill` 默认关闭；引擎用 `DispatchEx` 独占实例，退出它不会波及用户文档。

**过程证据（三层，证据力递减）**：

1. `--shot` —— 应用自身 `Slide.Export` 每页 PNG。**最硬**：第 N 页导出成功 ⇒ 前 N 页已在文稿里，不受遮挡/最小化影响。
2. `--shot-window` —— 只截「文稿窗口」自身（`PrintWindow` + `PW_RENDERFULLCONTENT`）。带标题栏与缩略图栏，
   是「应用确实开着这份文稿」的最佳凭证；**窗口被遮挡或最小化也拿得到画面**（先 `ShowWindow(SW_RESTORE)` 再重绘）。
3. `--shot-desktop` —— 整屏截图。只反映「谁在最前」，被遮挡时截到的是别的东西，证据力最弱。

**窗口定位（实测）**：WPS **不提供** `Application.HWND`（调用报「找不到成员」）；文稿框架窗类名都以 `FrameClass`
结尾（实测 WPS `PP12FrameClass`、MS `PP12FrameClass` 同族）。用「接入前后 FrameClass 窗口的 **PID 差分**」认领自己的
窗口——`DispatchEx` 起的是独占实例，新出现的 PID 一定是我们的；标题匹配 `pres.Name` 仅兜底（WPS 标题更新有延迟）。
**别按面积或可见性单挑**：WPS 进程里还挂着若干 237×39 的伪窗口（`PROME-TASKBAR` 等），会挑错。

**前台限制仍在**：`WindowState=3 + Activate()` 只改 COM 层的 `ActiveWindow`，后台进程抢不到前台焦点。
但**截图不再依赖前台**——`PrintWindow` 让窗口自己重绘到位图；要「现场看见」再叠加 `ShowWindow(SW_MAXIMIZE)`。

**依赖**：`pywin32`（COM 通道）· `matplotlib` + `numpy`（图表工厂）· `pillow`（截图/图表校验）。
**运行 python（关键）**：COM 与图表工厂都必须用**装了 pywin32 的解释器**。本机托管 venv 已装好：

```
C:\Users\33551\.workbuddy\binaries\python\envs\default\Scripts\python.exe
```

> ⚠️ **Windows 的 venv 入口在 `Scripts\` 下**，`envs\default\python.exe`（无 `Scripts\`）在 Windows 上**不存在** —— 别照 POSIX 习惯写。
> 裸的托管解释器 `...\python\versions\3.13.12\python.exe` **没有 pywin32**，直接跑 `com-probe` / `com-drive` 会报「缺少 pywin32」。
> 装依赖用该 venv 自己：`...\envs\default\Scripts\python.exe -m pip install pywin32 matplotlib numpy pillow`。


### 自带命令（不依赖工具链）

这些走的是本 skill 自己的 `scripts/`，**机器上没装转换工具链也能用**：

| 调度命令 | 底层脚本 | 用途 |
|---|---|---|
| `com-probe` | `com_drive.py probe` | 探测本机 WPS / PowerPoint 的 COM 引擎（逐引擎独立子进程） |
| `com-review <deck.json>` | `com_drive.py review` | 量产线五维质检的机器可算部分，<70 分返修 |
| `com-drive <deck.json> [flags]` | `com_drive.py drive` | 量产线 COM 直驱可见生成 PPTX/PDF/PNG |
| `assemble <spec.json> <out.pptx>` | `pptx_assembly.py assemble` | 手作线：纸底 + 晕染层 + 原生文本框装配 |
| `pptx-optimize <bake_dir>` | `pptx_assembly.py optimize` | 烘图层转 JPEG + PNG 调色板量化（压体积） |
| `pptx-export <pptx> <png_dir> [w]` | `pptx_assembly.py export` | 用应用 COM 把 PPTX 回导成 PNG（校验用） |
| `pptx-measure <ref_dir> <ppt_dir> <regions.json>` | `pptx_assembly.py measure` | 逐元素量墨水包围盒偏移 |
| `extract-bg <pptx> <out_dir>` | `extract_bg.py` | 模板背景提取（量产线工步 1）· COM 优先、ZIP 兜底 |
| `math-check` | `omml_math.py check` | 原生公式链路自检（定位 MML2OMML.XSL + 依赖） |
| `math-omml <latex> [size]` | `omml_math.py omml` | LaTeX → OMML（<m:oMath>）片段 |
| `math-demo [out.pptx]` | `omml_math.py demo` | 生成带原生公式的样例 pptx（目视验证） |
| `deck-check <index.html>` | `deck_validate.mjs`（node） | 极简风版式锁 + 排版测量 |
| `notes-check <index.html>` | `notes_validate.mjs`（node） | 页面 ID 与演讲备注一致性 |

---

## 八之二 · 网页 deck 骨架与校验器（assets / scripts）

网页线（`25-web-deck.md`）用到的可运行资产，随本 skill 一起发布，**不要改动**：

| 文件 | 是什么 | 怎么用 |
|---|---|---|
| `assets/deck-shell-electronic.html` | 电子风骨架（完整可运行：WebGL 背景 + 横滑翻页 + 演讲者模式 + 观众屏同步 + 计时排练） | 拷成项目的 `index.html` |
| `assets/deck-shell-minimal.html` | 极简风骨架（同上，另含 22 式版式锁与低功耗静态模式） | 拷成项目的 `index.html` |
| `assets/motion.min.js` | 入场动效运行时（Motion One 本地副本，约 64KB，离线兜底） | 拷成项目的 `assets/motion.min.js` |
| `scripts/notes_validate.mjs` | 备注与页面 ID 校验 | `node scripts/notes_validate.mjs index.html [--target-minutes 30]` |
| `scripts/deck_validate.mjs` | 极简风版式锁 + 排版测量（能用 Playwright 时做真实渲染测量） | `node scripts/deck_validate.mjs index.html` |
| `scripts/com_drive.py` | 量产线 COM 直驱引擎（探测 / 质检 / 可见生成，内含 7 种元素路由 + 4 套预设） | `python scripts/com_drive.py probe` |
| `scripts/pptx_assembly.py` | 手作线 PPTX 装配器（烘图优化 / 装配 / 回导 / 逐元素量测） | `python scripts/pptx_assembly.py assemble spec.json out.pptx` |
| `scripts/extract_bg.py` | 模板背景提取（COM `Slide.Export` 优先做全合成底；无 Office 时降级到 ZIP 解包找 `<p:bg>` 图） | `python scripts/extract_bg.py template.pptx ./bg-out` |
| `scripts/omml_math.py` | LaTeX → Office 原生公式（OMML）注入；`append_math(text_frame, latex, size_pt)` | `python scripts/omml_math.py check` |

**适配本机的三处改动**（已做，别改回去）：

1. **Lucide 图标从 `unpkg.com` 换到 `cdn.jsdelivr.net`** —— 本机 unpkg 不可达，jsdelivr 可达
2. **运行时标识符自有化** —— 骨架里的 localStorage 键名与 postMessage 协议名（`rouo-deck-*` / `__rouoDeckSync`）是本 skill 的前缀，两个骨架保持一致才能相互同步
3. **两个骨架都不再挂 Google Fonts `<link>`** —— 本机 `fonts.googleapis.com` / `fonts.gstatic.com` 不可达，外链只会换来一段阻塞超时。骨架的字体全部走 CSS 变量里的**本地兜底栈**；要换字体改 CSS 变量，别加 `<link>`。这条由守卫的「可达性洁净」检查兜住（只拦真实 `href/src` 引用，注释里说明原因不算）。

**字体观感**：本地兜底栈下中文排版满血（Noto Serif SC / Noto Sans SC / 微软雅黑），英文 display 从 Playfair Display 降级为 Georgia（仍是高雅衬线，观感成立）。要满血 Playfair，需把字体文件放本地并用 `@font-face` 指向 —— 但**不要**改回 CDN `<link>`。

**两个骨架的 `assets/motion.min.js` 路径是相对的**：拷骨架时必须同时把 `motion.min.js` 拷到项目 `assets/` 下，否则动效会走 CDN 兜底（断网则退化为无动画但内容可读）。

---

## 九 · 速查小结

```
✅ 可达   : cdn.simpleicons.org · api.iconify.design · cdn.jsdelivr.net · registry.npmmirror.com
❌ 不可达 : Wikimedia · Clearbit · google favicon · fonts.googleapis.com/gstatic · unpkg.com
⚠️ 假 200 : wsrv.nl 类代理（下完必 file + wc -c 核对）
字体     : Noto Sans/Serif SC · Consolas · Georgia · Segoe UI（本地已装）
         ↳ 骨架不挂 Google Fonts <link>，一律本地兜底；中文满血，英文 display 为 Georgia
截图     : 系统 Chrome headless，Windows 绝对路径，单次 <120s
npm      : --registry=https://registry.npmmirror.com
py 路径  : Windows 反斜杠，别用 POSIX
COM      : 引擎 scripts/com_drive.py；必须 DispatchEx + 用 Application.Path 验证身份
           KWPP.Application→WPS · PowerPoint.Application.16→MS · .Application→可能是WPS
           绝对路径；别无脑 taskkill；需 pywin32 的解释器（托管 venv）
取证     : --shot(页面内容,最硬) · --shot-window(窗口自身,PrintWindow) · --shot-desktop(整屏,最弱)
           窗口定位：FrameClass 类名 + PID 差分；别按类名/面积乱挑；前台锁仍抢不到"浮到最前"
工具链   : 统一走 scripts/tools.py 调度器（另有 com-* / assemble / pptx-* 自带命令）
网页骨架 : assets/deck-shell-{electronic,minimal}.html + assets/motion.min.js
网页校验 : node scripts/notes_validate.mjs · node scripts/deck_validate.mjs
```
