#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rouo PPT · 量产线 COM 直驱引擎（可执行）

让本机安装的 WPS 或 PowerPoint **可见地**、逐个元素地把 deck 写出来。
不再是文档里的一段待复制代码——这是能直接跑的命令行工具。

用法：
    python com_drive.py probe                          # 探测本机可用的 COM 引擎（逐引擎独立子进程）
    python com_drive.py drive deck_data.json           # 直驱生成（默认可见 + 保留窗口）
    python com_drive.py drive deck_data.json --pace .5 # 每写一个元素停 .5 秒，肉眼看生成过程
    python com_drive.py drive deck_data.json --shot DIR  # 每写完一页导出该页 PNG
    python com_drive.py drive deck_data.json --shot-desktop DIR  # 整屏截图作过程证据
    python com_drive.py drive deck_data.json --shot-window DIR   # 只截文稿窗口自身（推荐）
    python com_drive.py review deck_data.json          # 只跑机器可算的五维质检，不启动 Office

选项：
    --engine auto|wps|ms   引擎选择。auto 优先 WPS（KWPP.Application），回退 MS Office
    --out PATH             输出 pptx 路径，默认 exports/output.pptx
    --pace SEC             每个元素写完后停顿秒数（默认 0，即不等待）
    --shot DIR             每写完一页，用应用自身导出该页 PNG（内容真实、不受遮挡）
    --shot-desktop DIR     每写完一页整屏截图。⚠️ 它记录的是屏幕现状（谁在最前就截到谁），
                           证据力弱于 --shot；要证明「页面已存在于文稿里」请用 --shot
    --shot-window DIR      每写完一页只截「文稿窗口」自身（PrintWindow）。窗口被遮挡或最小化
                           也能拿到画面，并且带标题栏——这是「应用确实开着这份文稿」的最佳凭证
    --png DIR              保存后用应用自身把每页导出 PNG（ScaleWidth 基准）
    --pdf                  同时导出 PDF
    --close                收尾时关闭本引擎创建的演示文稿（默认保留，便于目视）
    --keep-open            收尾时保留应用窗口。默认会退出「本任务独占的实例」，
                           避免 DispatchEx 每次跑都留下一个 WPS/PPT 进程
    --quit                 收尾时退出应用。⚠️ 仅在你确认没有其他未保存文档时使用
    --kill                 启动前强杀 wps/wpp/powerpnt 进程。⚠️ 会丢失未保存内容，默认关闭
    --dry-run              只校验数据与质检，不连接 Office

退出码：0 成功 · 2 数据非法 · 3 找不到可用引擎 · 4 质检不通过（仅 --strict 时）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# COM 常量（不要改成字符串，COM 只认整数）
# ---------------------------------------------------------------------------

MSO_SHAPE_RECTANGLE = 1
MSO_SHAPE_OVAL = 9
MSO_TEXT_ORIENTATION_HORIZONTAL = 1
PP_LAYOUT_BLANK = 12
PP_SAVE_AS_PDF = 32

# 引擎候选链。**不要用 ProgID 判断引擎身份**——WPS 会把「版本无关」的
# PowerPoint.Application 抢到自己名下，所以装了 WPS 的机器上
# Dispatch('PowerPoint.Application') 拿到的往往是 WPS，而不是 MS Office。
# 因此取到实例后必须用 Application.Path 实证（identify_engine）。
# 真 MS Office 要用版本号限定的 ProgID（.16 / .15 / .14）。
ENGINE_CHAINS = {
    "wps": ("KWPP.Application", "WPS.Application", "Wpp.Application"),
    "ms": ("PowerPoint.Application.16", "PowerPoint.Application.15",
           "PowerPoint.Application.14", "PowerPoint.Application"),
}

# auto 的优先级：WPS 优先（与 10-drive-engine.md 的 PROGID 默认值一致）
ENGINE_ORDER = ("wps", "ms")

VENDOR_MARKERS = {
    "wps": ("wps", "kingsoft", "金山"),
    "ms": ("microsoft office",),
}

CANVAS_W, CANVAS_H = 960, 540

# 安全下边界（11-deck-data-format.md §一）——只约束**内容**元素
SAFE_BOTTOM = 518
SAFE_RIGHT = 960

# 满宽出血条豁免：规范里顶/底品牌色条本就落在 y=0 h=4–6 与 y=534 h=4–6，
# 它们是版面框架而非内容，不受 518 约束（否则每次都被误报）。
BLEED_BAR_MIN_Y = 530

# ---------------------------------------------------------------------------
# 设计预设（12-presets-review.md §一）
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict] = {
    "academic": {
        "primary": "#1A3C8B", "accent": "#E67733", "third": "#188050",
        "body": "#222222", "light": "#F5F8FC", "text_on_primary": "#FFFFFF",
        "title_font": "Arial", "body_font": "Microsoft YaHei",
        "title_size": 40, "body_size": 24, "caption_size": 16,
        "max_points": 6, "visual_ratio": 0.60,
    },
    "consultant": {
        "primary": "#003366", "accent": "#00A8E8", "third": "#FF8C00",
        "body": "#222222", "light": "#F2F6FA", "text_on_primary": "#FFFFFF",
        "title_font": "Arial", "body_font": "Microsoft YaHei",
        "title_size": 36, "body_size": 18, "caption_size": 14,
        "max_points": 5, "visual_ratio": 0.50,
    },
    "business": {
        "primary": "#005294", "accent": "#C82828", "third": "#2DA050",
        "body": "#222222", "light": "#F4F7FA", "text_on_primary": "#FFFFFF",
        "title_font": "Arial", "body_font": "Microsoft YaHei",
        "title_size": 36, "body_size": 18, "caption_size": 14,
        "max_points": 6, "visual_ratio": 0.45,
    },
    "tech": {
        "primary": "#00C8FF", "accent": "#FF643C", "third": "#7B61FF",
        "body": "#E8EDF5", "light": "#1A2333", "text_on_primary": "#0F1423",
        "bg": "#0F1423",
        "title_font": "Arial", "body_font": "Microsoft YaHei",
        "title_size": 44, "body_size": 20, "caption_size": 14,
        "max_points": 4, "visual_ratio": 0.55,
    },
}

# ---------------------------------------------------------------------------
# 颜色：hex → COM BGR 整数
# ---------------------------------------------------------------------------

def h2b(value) -> int:
    """'#8C1515' → COM RGB 整数。

    PowerPoint/WPS 的 RGB 属性是 BGR 打包（R + G*256 + B*65536），
    所以左移方向与直觉相反。这里同时容忍 '#' 前缀、简写与已转好的整数。
    """
    if isinstance(value, int):
        return value
    s = str(value).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"颜色格式不对：{value!r}（应为 #RRGGBB）")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return (b << 16) | (g << 8) | r


# ---------------------------------------------------------------------------
# 前端：把 deck_data.json 的 raw 数据解析成「有预设兜底 + 校验过的」中间结构
# ---------------------------------------------------------------------------

class DeckError(Exception):
    pass


def load_deck(path: Path) -> dict:
    if not path.is_file():
        raise DeckError(f"找不到数据文件：{path}")
    try:
        deck = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise DeckError(
            f"{path.name} 不是合法 JSON（第 {e.lineno} 行第 {e.colno} 列）：{e.msg}\n"
            "  常见原因：用了中文引号 “ ” 而不是 \"，或末尾多了逗号。"
        ) from e

    preset_name = deck.get("preset", "business")
    if preset_name not in PRESETS:
        raise DeckError(
            f"未知预设 {preset_name!r}。可用：" + " · ".join(PRESETS))
    theme = dict(PRESETS[preset_name])
    theme.update(deck.get("theme", {}))          # 项目自定义覆盖预设
    theme["bg"] = theme.get("bg", "#FFFFFF")
    deck["_preset"] = preset_name
    deck["_theme"] = theme

    canvas = deck.setdefault("canvas", {})
    canvas.setdefault("w", CANVAS_W)
    canvas.setdefault("h", CANVAS_H)
    if canvas["w"] != CANVAS_W or canvas["h"] != CANVAS_H:
        raise DeckError(
            f"画布必须是 {CANVAS_W}×{CANVAS_H}（16:9），当前 "
            f"{canvas['w']}×{canvas['h']}。改比例请同步改 com_drive.py 的画布常量。")

    if not deck.get("slides"):
        raise DeckError("deck_data.json 里没有任何 slides。")
    for i, page in enumerate(deck["slides"], 1):
        page.setdefault("id", i)
        if not page.get("elements"):
            raise DeckError(f"第 {i} 页（{page.get('title', '未命名')}）没有任何元素。")
    return deck


def fill_theme(obj: dict, theme: dict) -> dict:
    """元素里写 "$primary" / "$body" 之类就取主题色；没写 color 的按 type 给默认。"""
    out = dict(obj)
    for key in ("color", "header_color", "text_color", "line_color"):
        v = out.get(key)
        if isinstance(v, str) and v.startswith("$"):
            token = v[1:]
            if token not in theme:
                raise DeckError(f"元素引用了主题里没有的色标 {v!r}")
            out[key] = theme[token]
    return out


# ---------------------------------------------------------------------------
# 元素路由（11-deck-data-format.md §三）
# ---------------------------------------------------------------------------
# 每个 router 签名统一为 (slide, elem, theme, ctx) —— ctx 提供截图/节奏等旁路能力
# ---------------------------------------------------------------------------

def draw_text(slide, e, theme, ctx):
    align = int(e.get("align", 1))
    fs = float(e.get("fs", theme["body_size"]))
    color = e.get("color", theme["body"])
    font = e.get("font", theme["body_font"])
    t = slide.Shapes.AddTextbox(
        MSO_TEXT_ORIENTATION_HORIZONTAL,
        e["x"], e["y"], e["w"], e["h"])
    tr = t.TextFrame.TextRange
    tr.Text = str(e["text"])
    tr.Font.Size = fs
    tr.Font.Color = h2b(color)
    tr.Font.Name = font
    tr.Font.Bold = bool(e.get("bold", False))
    tr.ParagraphFormat.Alignment = align          # 1=左 2=中 3=右
    try:
        tr.ParagraphFormat.SpaceWithin = float(e.get("line_spacing", 1.3))
    except Exception:
        pass
    try:
        # 命名后便于交付后按名字定位（不做也能跑，失败不致命）
        t.Name = e.get("name", f"text-{e['x']}-{e['y']}")
    except Exception:
        pass
    return t


def draw_image(slide, e, theme, ctx):
    p = Path(e["file"])
    if not p.is_absolute():
        p = ctx["workdir"] / p
    if not p.is_file():
        # 数据格式规范 §三：文件不存在时静默跳过，不崩引擎
        ctx.setdefault("_missing", []).append(str(p))
        return None
    return slide.Shapes.AddPicture(
        str(p), False, True, e["x"], e["y"], e["w"], e["h"])


def draw_shape(slide, e, theme, ctx):
    kind = e.get("shape", "rect")
    color = e.get("color", theme["primary"])
    x, y, w, h = e["x"], e["y"], e["w"], e.get("h", 10)
    if kind == "line":
        s = slide.Shapes.AddLine(x, y, x + w, y + h)
        s.Line.ForeColor.RGB = h2b(color)
        s.Line.Weight = float(e.get("weight", 1.5))
        return s
    shp = slide.Shapes.AddShape(
        MSO_SHAPE_OVAL if kind == "circle" else MSO_SHAPE_RECTANGLE,
        x, y, w, h)
    shp.Fill.ForeColor.RGB = h2b(color)
    shp.Fill.Visible = True
    if e.get("line", False):
        shp.Line.Visible = True
        shp.Line.ForeColor.RGB = h2b(e.get("line_color", theme["primary"]))
    else:
        shp.Line.Visible = False
    return shp


def draw_table(slide, e, theme, ctx):
    """逐格矩形 + 文本框拼表。

    为什么不用 COM 的 Shapes.AddTable：
      AddTable 会带来主题表格样式（边框、条纹、字体），在 WPS 与 Office 里表现
      还不一致，把设计稿配色彻底打乱。逐格自绘可控，且与手作线坐标语义一致。
    """
    rows, cols = int(e["rows"]), int(e["cols"])
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    data = e["data"]
    hdr = e.get("header_color", theme["primary"])
    row_h = max(h // rows, 28)                 # 表格铁律：最小行高 28
    col_w = w // cols
    th_fs = float(e.get("th_fs", 13))
    td_fs = float(e.get("td_fs", 14))
    for r in range(rows):
        for c in range(cols):
            cx, cy = x + c * col_w, y + r * row_h
            is_hdr = (r == 0)
            bg = hdr if is_hdr else (theme["light"] if r % 2 == 0 else "#FFFFFF")
            draw_shape(slide, {"shape": "rect", "x": cx, "y": cy,
                               "w": col_w, "h": row_h, "color": bg}, theme, ctx)
            val = ""
            if r < len(data) and c < len(data[r]):
                val = str(data[r][c])
            if not val:
                continue
            tb = slide.Shapes.AddTextbox(
                MSO_TEXT_ORIENTATION_HORIZONTAL, cx + 4, cy + 3,
                col_w - 8, row_h - 6)
            tr = tb.TextFrame.TextRange
            tr.Text = val
            tr.Font.Size = th_fs if is_hdr else td_fs
            tr.Font.Color = h2b(theme["text_on_primary"] if is_hdr else theme["body"])
            tr.Font.Name = theme["title_font"] if is_hdr else theme["body_font"]
            tr.Font.Bold = is_hdr
            tr.ParagraphFormat.Alignment = 2 if c > 0 else 1
            tb.TextFrame.WordWrap = False       # 表格铁律：强制单行，绝不换行


def draw_card_list_wide(slide, e, theme, ctx):
    items = e["items"]
    sy = int(e.get("start_y", 90))
    ih = int(e.get("item_h", 52))
    limit = 500 - sy
    if len(items) * ih >= limit:
        ctx.setdefault("_warn", []).append(
            f"card_list_wide 溢出：{len(items)} 项 × {ih}pt = {len(items)*ih} "
            f"≥ {limit}（布局硬规则：items × item_h < 500 − start_y）")
    marker = int(e.get("marker_size", 32))
    col_x = int(e.get("marker_x", 100))
    text_x = int(e.get("text_x", 148))
    for i, item in enumerate(items):
        y = sy + i * ih
        c = h2b(theme["primary"] if i % 2 == 0 else theme["body"])
        draw_shape(slide, {"shape": "circle", "x": col_x, "y": y + 4,
                           "w": marker, "h": marker, "color": c}, theme, ctx)
        nb = slide.Shapes.AddTextbox(MSO_TEXT_ORIENTATION_HORIZONTAL,
                                     col_x, y + 4, marker, marker)
        tr = nb.TextFrame.TextRange
        tr.Text = str(item.get("num", ""))
        tr.Font.Size = float(e.get("num_fs", 13))
        tr.Font.Color = h2b(theme["text_on_primary"])
        tr.Font.Name = theme["title_font"]
        tr.Font.Bold = True
        tr.ParagraphFormat.Alignment = 2
        draw_text(slide, {"x": text_x, "y": y + 2, "w": int(e.get("title_w", 280)),
                          "h": 26, "text": item.get("title", ""),
                          "fs": float(e.get("title_fs", 22)),
                          "color": theme["body"], "bold": True,
                          "font": theme["title_font"], "line_spacing": 1.1}, theme, ctx)
        if item.get("sub"):
            draw_text(slide, {"x": text_x, "y": y + 28,
                              "w": int(e.get("sub_w", 700)), "h": 18,
                              "text": item["sub"],
                              "fs": float(e.get("sub_fs", 14)),
                              "color": theme.get("caption", "#555555"),
                              "line_spacing": 1.1}, theme, ctx)


def draw_num_big(slide, e, theme, ctx):
    """三段式：数字 40% + 间隙 10% + 标签 50% —— 绝不重叠。"""
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    num_h, gap, lbl_h = int(h * 0.40), int(h * 0.10), int(h * 0.50)
    color = e.get("color", theme["primary"])
    t1 = slide.Shapes.AddTextbox(MSO_TEXT_ORIENTATION_HORIZONTAL, x, y, w, num_h)
    tr1 = t1.TextFrame.TextRange
    tr1.Text = str(e["num"])
    tr1.Font.Size = float(e.get("fs", 34))
    tr1.Font.Color = h2b(color)
    tr1.Font.Name = e.get("font", "Arial")
    tr1.Font.Bold = True
    tr1.ParagraphFormat.Alignment = 2
    t1.TextFrame.WordWrap = False
    t2 = slide.Shapes.AddTextbox(MSO_TEXT_ORIENTATION_HORIZONTAL,
                                 x, y + num_h + gap, w, lbl_h)
    tr2 = t2.TextFrame.TextRange
    tr2.Text = str(e["label"])
    tr2.Font.Size = float(e.get("label_fs", 13))
    tr2.Font.Color = h2b(e.get("label_color", theme.get("caption", "#666666")))
    tr2.Font.Name = theme["body_font"]
    tr2.ParagraphFormat.Alignment = 2
    t2.TextFrame.WordWrap = False


def draw_tagline_bar(slide, e, theme, ctx):
    y = int(e.get("y", 498))
    h = int(e.get("h", 28))
    x = int(e.get("x", 30))
    w = int(e.get("w", 900))
    draw_shape(slide, {"shape": "rect", "x": x, "y": y, "w": w, "h": h,
                       "color": e.get("color", theme["primary"])}, theme, ctx)
    draw_text(slide, {"x": x + 10, "y": y + 3, "w": w - 20, "h": h - 6,
                      "text": e["text"], "fs": float(e.get("fs", 14)),
                      "color": e.get("text_color", theme["text_on_primary"]),
                      "bold": True, "align": 2, "line_spacing": 1.0}, theme, ctx)


ROUTERS = {
    "text": draw_text,
    "image": draw_image,
    "shape": draw_shape,
    "table": draw_table,
    "card_list_wide": draw_card_list_wide,
    "num_big": draw_num_big,
    "tagline_bar": draw_tagline_bar,
}


def _probe_one(engine: str) -> dict:
    """**在独立子进程里**解析单个引擎。

    为什么必须独立进程：WPS 的 COM 服务器一旦被激活，会抢注 Office 兼容的
    ProgID，此后同进程内解析 PowerPoint.Application* 都会落到 WPS 上。
    实测（本机）：
        只碰 PowerPoint.Application.16              → MS Office 16.0
        先碰 KWPP.Application 再碰 .16              → WPS（另一个实例）
    也就是说「先探 WPS 再探 MS」会自我污染，把可用的 MS Office 报成不可用。
    因此每个引擎各起一个干净进程，结果才可信。
    """
    eng, progid, _app, ident, notes = resolve_engine(engine)
    return {"engine": engine, "progid": progid, "ident": ident, "notes": notes,
            "ok": eng is not None}


def cmd_probe_one(args) -> int:
    """内部用：把单个引擎的解析结果以 JSON 打到 stdout。"""
    import json as _json
    print("@@PROBE@@" + _json.dumps(_probe_one(args.engine), ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# 五维质检 · 机器可算部分（12-presets-review.md §四）
# ---------------------------------------------------------------------------

TEXT_TYPES = {"text", "card_list_wide", "num_big", "tagline_bar"}
VISUAL_TYPES = {"image", "shape", "table"}


def review(deck: dict) -> dict:
    """对每页做元素清单级检查。返回 {'pages': [...], 'average': float, 'warnings': [...]}"""
    theme = deck["_theme"]
    pages, all_warn = [], []

    for page in deck["slides"]:
        pts = 100
        warn = []

        texts = [e for e in page["elements"] if e.get("type") in TEXT_TYPES]
        visuals = [e for e in page["elements"] if e.get("type") in VISUAL_TYPES]

        # 字号：标题 <36 / 正文 <20 / 标注 <14
        for e in texts:
            fs = float(e.get("fs", theme["body_size"]))
            if e.get("type") == "text" and fs >= 30 and fs < 36:
                pts -= 5
                warn.append(f"标题字号 {fs}pt < 36pt（投屏基准）")
            elif e.get("type") in ("text", "card_list_wide") and 15 < fs < 20:
                # 16–19pt 是「本该 20pt 的正文缩了水」，扣分
                pts -= 3
                warn.append(f"正文字号 {fs}pt < 20pt（投屏基准）")
            elif fs < 14:
                # <14pt 才是真过小。14–15pt 是规范里的 Caption，合法，不罚
                pts -= 2
                warn.append(f"标注字号 {fs}pt < 14pt")

        # 密度：文本块数 > 预设要点上限 × 1.5
        cap = theme["max_points"]
        if len(texts) > cap * 1.5:
            pts -= 10
            warn.append(f"文本块 {len(texts)} 个 > 预设上限 {cap} × 1.5")

        # 视觉占比
        total = len(page["elements"])
        ratio = len(visuals) / total if total else 0
        if ratio < theme["visual_ratio"] - 0.2:
            pts -= 5
            warn.append(
                f"视觉元素占比 {ratio:.0%} < 目标 {theme['visual_ratio']:.0%} − 20pp")

        # 一页一主题：标题角色元素 > 1 个（以 ≥36pt 的文字块判断）
        heads = [e for e in texts
                 if e.get("type") in ("text", "num_big")
                 and float(e.get("fs", 0)) >= 36]
        if len(heads) > 1:
            pts -= 10
            warn.append(f"疑似标题元素 {len(heads)} 个 —— 一页只应有一个主题")

        # 边界硬规则（不属于扣分项，属非法）
        for e in page["elements"]:
            if e.get("type") == "tagline_bar":
                continue                     # 固定落位，不参与边界检查
            if (e.get("type") == "shape" and e.get("x") == 0
                    and e.get("w", 0) >= deck["canvas"]["w"]
                    and e.get("y", 0) >= BLEED_BAR_MIN_Y):
                continue                     # 满宽出血条，属版面框架
            if "y" in e and "h" in e and e["y"] + e["h"] > SAFE_BOTTOM:
                warn.append(
                    f"元素超出安全下边界：y+h={e['y']+e['h']} > {SAFE_BOTTOM}"
                    f"（{e.get('type')} @ {e.get('x')},{e.get('y')}）")
            if "x" in e and "w" in e and e["x"] + e["w"] > SAFE_RIGHT:
                warn.append(
                    f"元素超出安全右边界：x+w={e['x']+e['w']} > {SAFE_RIGHT}"
                    f"（{e.get('type')} @ {e.get('x')},{e.get('y')}）")

        # 每页 ≥2 种视觉元素（布局硬规则）
        if len({e.get("type") for e in visuals}) < 2:
            warn.append("视觉元素不足 2 种（布局硬规则：每页 ≥2 种视觉元素）")

        pages.append({"id": page["id"], "title": page.get("title", ""),
                      "score": max(pts, 0), "warnings": warn})
        all_warn.extend(f"P{page['id']} {w}" for w in warn)

    avg = sum(p["score"] for p in pages) / len(pages) if pages else 0
    return {"pages": pages, "average": avg, "warnings": all_warn,
            "preset": deck["_preset"]}


def print_review(rep: dict) -> None:
    print(f"量产线质检 · 预设 {rep['preset']}")
    print("─" * 62)
    for p in rep["pages"]:
        flag = "通过" if p["score"] >= 70 else "★不通过（<70 需返修）"
        print(f"  P{p['id']:>2} {p['title'][:16]:<18s} {p['score']:>3} 分  {flag}")
        for w in p["warnings"]:
            print(f"        · {w}")
    print("─" * 62)
    print(f"  整体 {rep['average']:.1f} 分 / {len(rep['pages'])} 页 / "
          f"{len(rep['warnings'])} 个警告")


# ---------------------------------------------------------------------------
# 连接引擎
# ---------------------------------------------------------------------------

def create_app(progid: str):
    """创建 COM 应用实例。返回 (app, 方式)。

    **必须优先 DispatchEx**，这是本项目最贵的一个教训：
        Dispatch("PowerPoint.Application.16")   → 拿到的是 WPS（实测）
        DispatchEx("PowerPoint.Application.16") → 真 MS Office（实测）
    pywin32 的 Dispatch 会复用「已经在跑的那个实例」，而 WPS 一旦把 COM
    服务器跑起来，就会被复用掉——于是请求 MS Office 却拿到 WPS，且不报错。
    DispatchEx 强制新建实例，ProgID 解析才是确定的。
    附带好处：新建的实例专属于本任务，关掉它不会影响用户正在编辑的文档。
    """
    import win32com.client
    try:
        return win32com.client.DispatchEx(progid), "DispatchEx"
    except Exception:
        return win32com.client.Dispatch(progid), "Dispatch"


def identify_engine(app) -> dict:
    """用 Application.Path 实证引擎身份。

    返回 {'vendor': 'wps'|'ms'|'?', 'path', 'version', 'build'}。
    vendor 为 '?' 表示路径里没有可辨识的厂商特征——此时不采信，继续试下一个。
    """
    def g(attr: str) -> str:
        try:
            return str(getattr(app, attr))
        except Exception:
            return ""

    path = g("Path")
    low = path.lower()
    vendor = "?"
    for v, markers in VENDOR_MARKERS.items():
        if any(m in low for m in markers):
            vendor = v
            break
    return {"vendor": vendor, "path": path, "version": g("Version"),
            "build": g("Build")}


def resolve_engine(want: str = "auto"):
    """按 --engine 语义解析真引擎。

    返回 (engine, progid, app, ident, notes)；解析不到时前四项为 None。
    notes 记录每个被判退的 ProgID 及原因——这是排查「为什么拿到的不是我要的引擎」的关键。
    """
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    order = ENGINE_ORDER if want == "auto" else (want,)
    notes: list[str] = []

    for engine in order:
        for progid in ENGINE_CHAINS[engine]:
            try:
                app, how = create_app(progid)
            except Exception as ex:
                notes.append(f"{progid} → 无法创建（{type(ex).__name__}）")
                continue
            ident = identify_engine(app)
            ident["via"] = how
            if ident["vendor"] == engine:
                return engine, progid, app, ident, notes
            notes.append(
                f"{progid} → 真实身份是 {ident['vendor'].upper()}"
                f"（{ident['path'] or '路径未知'}），与请求的 {engine.upper()} 不符，弃用")
            # 注意：不 Quit。这个实例可能是用户正在用的，退出会丢未保存内容。
    return None, None, None, None, notes


def cmd_probe(_args) -> int:
    import subprocess
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        print("缺少 pywin32：本解释器没装 COM 依赖。\n"
              "  COM 通道请用托管 venv（已装好）：\n"
              "    C:\\Users\\33551\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe\n"
              "  缺依赖时装：<该 venv>\\Scripts\\python.exe -m pip install pywin32 matplotlib numpy pillow",
              file=sys.stderr)
        return 3

    print("本机 COM PPT 引擎探测（身份以 Application.Path 实证，不信 ProgID）")
    print("每个引擎各起一个干净子进程——同进程内先探一个会污染另一个的结果")
    print("─" * 70)
    ok = {}
    for engine in ENGINE_ORDER:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "_probe-one", engine],
            capture_output=True, text=True, encoding="utf-8", timeout=120)
        payload = None
        for line in (proc.stdout or "").splitlines():
            if line.startswith("@@PROBE@@"):
                payload = json.loads(line[len("@@PROBE@@"):])
                break
        if payload is None:
            print(f"  [{engine:3s}] ✗ 探测进程异常退出（code={proc.returncode}）")
            if proc.stderr:
                print(f"        {proc.stderr.strip().splitlines()[-1][:120]}")
            print()
            continue
        if payload["ok"]:
            ident = payload["ident"]
            ok[engine] = (payload["progid"], ident)
            print(f"  [{engine:3s}] ✔ {payload['progid']}")
            print(f"        Vendor={ident['vendor'].upper()}  "
                  f"Version={ident['version']}  Build={ident['build']}"
                  f"  取用方式={ident.get('via', '?')}")
            print(f"        Path={ident['path']}")
        else:
            print(f"  [{engine:3s}] ✗ 没有可用实例")
        for n in payload.get("notes", []):
            print(f"        · 弃用：{n}")
        print()

    print("─" * 70)
    if not ok:
        print("  未发现可用的 WPS / PowerPoint COM 引擎。")
        print("  量产线在本机不可用 → 按 SKILL.md 降级约定，整体切手作线或网页线。")
        return 3
    auto = next((e for e in ENGINE_ORDER if e in ok), None)
    print(f"  --engine auto 会选中：{auto.upper()}"
          f"（{ok[auto][0]}，{ok[auto][1]['path']}）")
    print(f"  可用键：" + " · ".join(ok))
    # 探测用的实例无法确定是否由我们启动，一律不 Quit，避免误杀用户正在用的进程
    return 0


# ---------------------------------------------------------------------------
# 窗口截图（边写边留证据）
# ---------------------------------------------------------------------------

def grab_desktop(path: Path) -> bool:
    """整屏截图——记录「屏幕上的实况」。

    它记录的是**当前屏幕**（谁在最前就截到谁），所以窗口被遮挡时会截到别的东西；
    证据力最弱，是 `grab_window` / `export_slide_png` 都失败时的兜底。

    ⚠️ 别再按类名或面积去挑窗口然后用 `ImageGrab.grab(bbox=...)`：真踩过，截回来的是
    WPS 的 ribbon 条而不是文稿画布（WPS 进程里还挂着 237×39 的伪窗口）。要精确截窗口
    请用 `grab_window`（认 `FrameClass` + PID 差分 + PrintWindow）。
    """
    try:
        from PIL import ImageGrab
        path.parent.mkdir(parents=True, exist_ok=True)
        ImageGrab.grab().save(path)
        return True
    except Exception:
        return False


def _enum_frame_windows():
    """列出所有顶层「文稿框架窗」：(hwnd, pid, title, visible, iconic, area)。

    WPS 与 MS Office 的文稿框架窗类名都以 `FrameClass` 结尾（实测 WPS 为
    `PP12FrameClass`）。WPS **不提供** `Application.HWND`，其他类名/属性又随
    版本漂移，所以只认这一个稳定特征。**不要**用窗口面积或可见性单独挑——
    WPS 里同一进程还挂着若干 237x39 的伪窗口，会挑错。
    """
    import ctypes
    import ctypes.wintypes as wt
    u = ctypes.windll.user32
    u.SetProcessDPIAware()
    out = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(h, _l):
        cls = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(h, cls, 256)
        if "FrameClass" not in cls.value:
            return True
        pid = wt.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        n = u.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, b, n + 1)
        r = wt.RECT()
        u.GetWindowRect(h, ctypes.byref(r))
        out.append((h, int(pid.value), b.value,
                    bool(u.IsWindowVisible(h)), bool(u.IsIconic(h)),
                    max(0, r.right - r.left) * max(0, r.bottom - r.top)))
        return True

    u.EnumWindows(proc(cb), 0)
    return out


def own_frame_hwnd(pids_before: set, name_hint: str = ""):
    """定位**本任务新建实例**的文稿窗口句柄。

    两个判据，按可靠性排序：
      1. 进程差分 —— 接入前不存在的 FrameClass 窗口 PID 一定是我们的
         （`DispatchEx` 起的是独占实例，这是最硬的判据）
      2. 标题匹配 `pres.Name` —— WPS 窗口标题就是文稿名，但标题更新有延迟，仅兜底
    """
    frames = _enum_frame_windows()
    if not frames:
        return None
    fresh = [f for f in frames if f[1] not in pids_before]
    pool = fresh or frames
    want = (name_hint or "").lower()
    if want:
        named = [f for f in pool if f[2].lower().startswith(want)]
        if named:
            pool = named
    pool.sort(key=lambda f: (0 if (f[3] and not f[4]) else 1, -f[5]))
    return pool[0][0] if pool else None


def maximize_window(hwnd) -> bool:
    """把文稿窗口最大化并前置。**只对自己的实例调用**。

    `ShowWindow(SW_MAXIMIZE)` 会顺带把窗口激活到前台——这正是量产线「现场看见」
    想要的；但前台锁仍可能拒绝，返回值不可靠，所以不据此判定成败。
    """
    try:
        import ctypes
        u = ctypes.windll.user32
        h = int(hwnd)
        if not u.IsWindow(h):
            return False
        u.ShowWindow(h, 3)            # SW_MAXIMIZE
        u.SetForegroundWindow(h)      # 前台锁可能拒绝，忽略
        return True
    except Exception:
        return False


def grab_window(path: Path, hwnd) -> bool:
    """只截「文稿窗口」自身（PrintWindow），**不需要**它浮到最前。

    为什么需要：`--shot-desktop` 的整屏截图只反映「谁在最前」，窗口被遮挡或
    最小化时截到的可能是别的东西；而 `Slide.Export` 只有画布、没有「应用确实
    开着这份文稿」的界面证据。`PrintWindow` 让窗口**自己重绘**到位图，不抢
    焦点、不比 Z 序——实测 WPS 的 `PP12FrameClass` 支持 `PW_RENDERFULLCONTENT(2)`。
    最小化时先 `ShowWindow(SW_RESTORE)` 再重绘。任何一步失败都回落整屏截图。
    """
    if not hwnd:
        return grab_desktop(path)
    try:
        import ctypes
        import ctypes.wintypes as wt
        from PIL import Image
    except Exception:
        return grab_desktop(path)
    u, g = ctypes.windll.user32, ctypes.windll.gdi32
    h = int(hwnd)
    if not u.IsWindow(h):
        return grab_desktop(path)
    if u.IsIconic(h):
        u.ShowWindow(h, 9)            # SW_RESTORE：只解除最小化，不抢焦点
        time.sleep(0.5)
    r = wt.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    w, hh = r.right - r.left, r.bottom - r.top
    if w < 320 or hh < 200:
        return grab_desktop(path)
    hdc = u.GetWindowDC(h)
    mdc = g.CreateCompatibleDC(hdc)
    bmp = g.CreateCompatibleBitmap(hdc, w, hh)
    g.SelectObject(mdc, bmp)
    drew = u.PrintWindow(h, mdc, 2)   # 2 = PW_RENDERFULLCONTENT

    class _BIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long),
                    ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                    ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                    ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                    ("biClrImportant", wt.DWORD)]

    bi = _BIH()
    bi.biSize = ctypes.sizeof(_BIH)
    bi.biWidth, bi.biHeight = w, -hh
    bi.biPlanes, bi.biBitCount = 1, 32
    buf = ctypes.create_string_buffer(w * hh * 4)
    g.GetDIBits(mdc, bmp, 0, hh, buf, ctypes.byref(bi), 0)
    g.DeleteObject(bmp)
    g.DeleteDC(mdc)
    u.ReleaseDC(h, hdc)
    if not drew:
        return grab_desktop(path)
    img = Image.frombuffer("RGBA", (w, hh), buf, "raw", "BGRA", 0, 1).convert("RGB")
    if img.getextrema() == ((0, 0), (0, 0), (0, 0)):   # 全黑 ⇒ 抓失败
        return grab_desktop(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        return True
    except Exception:
        return grab_desktop(path)


def export_slide_png(slide, path: Path, width: int = 1920,
                     height: int = 1080) -> bool:
    """让应用**自己**把这一页渲染成 PNG（Slide.Export）。

    这是最可信的「逐页写出来」证据：第 N 页导出成功 ⇒ 前 N 页已经存在于文稿里。
    与 grab_desktop 不同，它不受遮挡、最小化、多显示器影响。
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        slide.Export(str(path), "PNG", width, height)
        return path.is_file() and path.stat().st_size > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 直驱生成
# ---------------------------------------------------------------------------

def cmd_drive(args) -> int:
    deck_path = Path(args.deck).resolve()
    workdir = deck_path.parent
    deck = load_deck(deck_path)

    # ---- 质检先行：不通过就别浪费一次 Office 启动 ----
    rep = review(deck)
    print_review(rep)
    if args.strict and rep["average"] < 70:
        print("\n--strict：整体 <70 分，拒绝生成。", file=sys.stderr)
        return 4
    print()

    if args.dry_run:
        missing = [e["file"] for p in deck["slides"] for e in p["elements"]
                   if e.get("type") == "image"]
        if missing:
            print("image 元素引用的文件（dry-run 不校验存在性）：")
            for m in dict.fromkeys(missing):
                print(f"  {m}  {'✔' if (workdir / m).is_file() else '✗ 缺失'}")
        print("\n--dry-run：数据与质检通过，未连接 Office。")
        return 0

    # ---- 安全：绝不默认 taskkill ----
    if args.kill:
        import subprocess
        print("⚠️  --kill：正在强制结束 WPS / PowerPoint 进程，"
              "其他窗口里未保存的内容会丢失。")
        for exe in ("wps.exe", "wpp.exe", "powerpnt.exe"):
            subprocess.run(["taskkill", "/F", "/IM", exe, "/T"],
                           capture_output=True)
        time.sleep(1.0)

    try:
        import pythoncom
        import win32com.client
    except ImportError:
        print("缺少 pywin32：本解释器没装 COM 依赖。\n"
              "  COM 通道请用托管 venv（已装好）：\n"
              "    C:\\Users\\33551\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe\n"
              "  缺依赖时装：<该 venv>\\Scripts\\python.exe -m pip install pywin32 matplotlib numpy pillow",
              file=sys.stderr)
        return 3

    pythoncom.CoInitialize()

    # 记录接入前的文稿窗口 PID —— 写完后据此精确认出「我们自己那个窗口」
    pids_before = {f[1] for f in _enum_frame_windows()}

    # ---- 引擎选择 ----
    eng_key, progid, app, ident, notes = resolve_engine(args.engine)
    if eng_key is None:
        print(f"找不到可用引擎（--engine {args.engine}）。"
              f"先跑 com_drive.py probe 看本机有什么。", file=sys.stderr)
        for n in notes:
            print(f"  · {n}", file=sys.stderr)
        return 3

    print(f"引擎：{progid}  →  Vendor={ident['vendor'].upper()} "
          f"Version={ident['version']}  （取用方式 {ident.get('via', '?')}）")
    print(f"      Path={ident['path']}")
    for n in notes:
        print(f"      （弃用：{n}）")
    # 请求 MS Office 却只解析到 WPS 时，必须说清楚，别让用户以为拿到的是 MS
    if args.engine == "ms" and ident["vendor"] != "ms":
        print("⚠️  请求的是 MS Office，但实际引擎不是它。已中止，避免"
              "悄悄产出 WPS 的文件。", file=sys.stderr)
        return 3

    # 记录接入前的文稿数：用来判断这份 deck 是不是我们新建的
    try:
        preexisting = int(app.Presentations.Count)
    except Exception:
        preexisting = 0
    # DispatchEx 建出来的实例是本任务独占的，退出它不会波及用户的文档
    own_instance = ident.get("via") == "DispatchEx"

    app.Visible = True                   # 可见模式——量产线存在的意义之一

    pres = app.Presentations.Add()
    pres.PageSetup.SlideWidth = deck["canvas"]["w"]
    pres.PageSetup.SlideHeight = deck["canvas"]["h"]

    # 把文稿窗口提到最前 —— 量产线的意义之一是「现场看到生成过程」，
    # 窗口藏在别的应用后面等于没看见。WPS/MS 对这个调用都容忍失败。
    def activate_window() -> None:
        """把我们这份文稿设为活动文稿，并解除最小化。

        ⚠️ 能力边界（实测）：这能改变 COM 层面的 ActiveWindow，但**不能保证**
        窗口在屏幕上浮到最前——Windows 的前台窗口锁不允许后台进程抢焦点。
        所以「看得见 WPS 在写」不能只靠它：
          · 要证明「页面已写进文稿」→ `--shot`（应用自身 Slide.Export 该页）
          · 要证明「应用确实开着这份文稿」→ `--shot-window`（PrintWindow 抓窗口自身）
        """
        try:
            pres.Windows(1).WindowState = 3       # ppWindowMaximized
        except Exception:
            pass
        try:
            pres.Windows(1).Activate()
        except Exception:
            pass

    activate_window()

    def refresh_hwnd():
        """重新定位我们的窗口句柄（窗口可能被应用重建，所以每次截图前刷新）。"""
        try:
            return own_frame_hwnd(pids_before, pres.Name)
        except Exception:
            return None

    own_hwnd = refresh_hwnd()

    out_path = Path(args.out) if args.out else workdir / "exports" / "output.pptx"
    if not out_path.is_absolute():
        out_path = workdir / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ⚠️ COM 一律吃绝对路径：相对路径下 Slide.Export / SaveAs 会静默失败。
    # 这是本项目第二次踩同一个坑（第一次在 pptx_assembly 的 COM 回导）。
    def _abs(v):
        if not v:
            return None
        q = Path(v)
        return q if q.is_absolute() else (workdir / q)

    shot_dir = _abs(args.shot)
    desktop_dir = _abs(args.shot_desktop)
    window_dir = _abs(args.shot_window)

    # 要留过程证据时，把窗口最大化并前置一次 —— 「现场看见」才是量产线的目的。
    # 只动我们自己 DispatchEx 建的实例，不碰用户其他窗口。
    if (desktop_dir or window_dir) and own_hwnd:
        maximize_window(own_hwnd)
        time.sleep(0.4)
    ctx = {"workdir": workdir, "pres": pres, "eng": eng_key}
    slide_idx = [1]
    t_start = time.time()

    def pace(tag: str = "") -> None:
        if args.pace > 0:
            time.sleep(args.pace)

    for pi, page in enumerate(deck["slides"], 1):
        s = pres.Slides.Add(slide_idx[0], PP_LAYOUT_BLANK)
        slide_idx[0] += 1
        try:                                  # 视图跟着写到哪页就翻到哪页
            app.ActiveWindow.View.GotoSlide(pi)
        except Exception:
            pass
        try:
            s.FollowMasterBackground = False
        except Exception:
            pass
        # 底色 / 底图
        bg_file = page.get("background")
        p_tried = 0
        if bg_file:
            bp = Path(bg_file)
            if not bp.is_absolute():
                bp = workdir / bp
            if bp.is_file():
                try:
                    s.Background.Fill.UserPicture(str(bp))
                    p_tried = 1
                except Exception:
                    p_tried = 0
        if not p_tried:
            try:
                s.Background.Fill.Solid()          # 先定填充类型，再上色
                s.Background.Fill.ForeColor.RGB = h2b(
                    page.get("bg", deck["_theme"]["bg"]))
                s.Background.Fill.Visible = True
            except Exception:
                pass

        n_elem = 0
        for elem in page["elements"]:
            e = fill_theme(elem, deck["_theme"])
            router = ROUTERS.get(e.get("type", "text"))
            if router is None:
                ctx.setdefault("_warn", []).append(
                    f"未知元素类型 {e.get('type')!r}，已跳过")
                continue
            try:
                router(s, e, deck["_theme"], ctx)
                n_elem += 1
            except Exception as ex:
                ctx.setdefault("_fail", []).append(
                    f"P{page['id']} {e.get('type')} @{e.get('x')},{e.get('y')}："
                    f"{type(ex).__name__}: {ex}")
            pace(e.get("type", ""))

        print(f"  P{pi:>2} {page.get('title', ''):<20s} "
              f"写入 {n_elem:>2}/{len(page['elements'])} 个元素")
        if shot_dir:                          # 应用自身渲染该页 → 内容真实
            f = shot_dir / f"slide{pi:02d}.png"
            print(f"       该页导出 {'✔ ' + f.name if export_slide_png(s, f) else '✗ 失败'}")
        if desktop_dir:                       # 整屏 → 记录屏幕上的实况
            activate_window()
            time.sleep(0.25)
            f = desktop_dir / f"desktop{pi:02d}.png"
            print(f"       整屏截图 {'✔ ' + f.name if grab_desktop(f) else '✗ 失败'}")
        if window_dir:                        # 只截文稿窗口自身 → 不受遮挡/最小化影响
            f = window_dir / f"window{pi:02d}.png"
            print(f"       窗口截图 {'✔ ' + f.name if grab_window(f, refresh_hwnd()) else '✗ 失败'}")

    # ---- 保存 ----
    try:
        pres.SaveAs(str(out_path))
        size = out_path.stat().st_size
        print(f"\nPPTX 已保存：{out_path}")
        print(f"  {size:,} bytes（{size/1048576:.2f} MB）"
              + ("  ⚠️ 体积过小，通常是残留进程占用了文件" if size < 100_000 else ""))
    except Exception as ex:
        print(f"保存失败：{ex}", file=sys.stderr)
        return 1

    # WPS 有时对新建文稿不落盘 WPP 之外的东西，二次确认
    if not out_path.is_file() or out_path.stat().st_size == 0:
        print("PPTX 0KB —— 目标文件可能被其他进程占用。"
              "关闭 WPS 里同名文件后重试（或加 --kill，注意会丢未保存内容）。",
              file=sys.stderr)
        return 1

    # 存盘后标题已是文件名，再补一张「带标题栏的成品窗口照」作最终凭证
    if window_dir:
        activate_window()
        time.sleep(0.4)
        f = window_dir / "window_final.png"
        print(f"窗口截图 {'✔ ' + str(f) if grab_window(f, refresh_hwnd()) else '✗ 失败'}")

    if args.pdf:
        pdf_path = out_path.with_suffix(".pdf")
        try:
            pres.SaveAs(str(pdf_path), PP_SAVE_AS_PDF)
            print(f"PDF  已保存：{pdf_path}  "
                  f"({pdf_path.stat().st_size:,} bytes)")
        except Exception as ex:
            print(f"PDF 导出失败（不影响 PPTX）：{ex}")

    if args.png:
        png_dir = Path(args.png)
        if not png_dir.is_absolute():
            png_dir = workdir / png_dir
        png_dir.mkdir(parents=True, exist_ok=True)
        try:
            # 用应用自身导出——与 pptx_assembly 的 COM 回导是两条独立通道
            pres.Export(str(png_dir), "PNG", 1920, 1080)
            # 注意：Windows 的 glob 大小写不敏感，*.PNG 和 *.png 会匹配同一批文件，
            # 相加会把数量翻倍。只 glob 一次。
            files = sorted(png_dir.glob("*.png"))
            print(f"PNG  已导出：{png_dir}（{len(files)} 张）")
            for f in files:
                print(f"       · {f.name}  {f.stat().st_size/1024:.0f} KB")
        except Exception as ex:
            print(f"PNG 导出失败：{ex}")

    # ---- 收尾 ----
    if ctx.get("_warn"):
        print("\n警告：")
        for w in dict.fromkeys(ctx["_warn"]):
            print(f"  · {w}")
    if ctx.get("_missing"):
        print("\n缺失的图片（已跳过，引擎未崩）：")
        for m in dict.fromkeys(ctx["_missing"]):
            print(f"  · {m}")
    if ctx.get("_fail"):
        print("\n绘制失败的元素：")
        for f in dict.fromkeys(ctx["_fail"]):
            print(f"  · {f}")

    elapsed = time.time() - t_start
    total_elem = sum(len(p["elements"]) for p in deck["slides"])
    print(f"\n完成：{len(deck['slides'])} 页 / {total_elem} 个元素 / "
          f"{elapsed:.1f} 秒")

    if args.close:
        try:
            pres.Close()
            print("已关闭本引擎创建的演示文稿。")
        except Exception:
            pass
    else:
        print("演示文稿保留在窗口中（默认行为，便于目视检查）；"
              "用 --close 可自动关闭。")

    # 收尾策略：DispatchEx 建出来的实例专属于本任务，默认退出，避免 WPS 进程堆积；
    # 用 --keep-open 可留住窗口继续目视检查。
    if args.keep_open:
        print("应用实例保留（--keep-open）。")
    elif args.quit or own_instance:
        try:
            app.Quit()
            print("已退出本任务创建的应用实例"
                  + ("（--quit）" if args.quit else "（实例归本任务所有；"
                     "加 --keep-open 可保留窗口）"))
        except Exception as ex:
            print(f"退出应用失败（WPS 的 Quit 常报这个，可忽略）：{ex}")
    else:
        print("应用进程保留。")
    return 0


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="com_drive.py",
        description="Rouo PPT 量产线 · COM 直驱引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("用法：")[1] if "用法：" in __doc__ else "")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="探测本机 COM 引擎")
    p_probe.set_defaults(func=cmd_probe)

    p_one = sub.add_parser("_probe-one", help="内部：单引擎探测（独立进程用）")
    p_one.add_argument("engine", choices=["wps", "ms"])
    p_one.set_defaults(func=cmd_probe_one)

    p_rev = sub.add_parser("review", help="只跑五维质检（机器可算部分）")
    p_rev.add_argument("deck")
    p_rev.set_defaults(func=cmd_review)

    p = sub.add_parser("drive", help="COM 直驱生成 deck")
    p.add_argument("deck", help="deck_data.json 路径")
    p.add_argument("--engine", choices=["auto", "wps", "ms"], default="auto")
    p.add_argument("--out", default=None, help="输出 pptx 路径")
    p.add_argument("--pace", type=float, default=0.0,
                   help="每个元素写完后的停顿秒数（看生成过程用）")
    p.add_argument("--shot", default=None,
                   help="每页写完后让应用导出该页 PNG 到此目录（内容真实）")
    p.add_argument("--shot-desktop", default=None,
                   help="每页写完后整屏截图到此目录（证明应用窗口开着）")
    p.add_argument("--shot-window", default=None,
                   help="每页写完后只截「文稿窗口」自身（PrintWindow，不受遮挡/最小化影响）")
    p.add_argument("--png", default=None, help="用应用自身把每页导出 PNG 到此目录")
    p.add_argument("--pdf", action="store_true", help="同时导出 PDF")
    p.add_argument("--close", action="store_true", help="收尾时关闭本文稿")
    p.add_argument("--quit", action="store_true", help="收尾时退出应用")
    p.add_argument("--keep-open", action="store_true",
                   help="收尾时保留应用窗口（默认：退出本任务独占的实例）")
    p.add_argument("--kill", action="store_true",
                   help="启动前强杀 WPS/PowerPoint 进程（⚠️ 会丢未保存内容）")
    p.add_argument("--strict", action="store_true", help="整体 <70 分则拒绝生成")
    p.add_argument("--dry-run", action="store_true", help="只校验，不连 Office")
    p.set_defaults(func=cmd_drive)

    args = ap.parse_args(argv)
    return args.func(args)


def cmd_review(args) -> int:
    deck = load_deck(Path(args.deck).resolve())
    rep = review(deck)
    print_review(rep)
    return 0 if rep["average"] >= 70 else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
