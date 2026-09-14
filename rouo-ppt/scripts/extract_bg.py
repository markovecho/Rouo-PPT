#!/usr/bin/env python
"""Rouo PPT · 模板背景提取（用户模板 PPTX → template_bg.png）

量产线工步 1 的配套工具：把用户给的模板 PPTX 的**母版/页面背景**提成一张
`960×540` 的 PNG，供 `deck_data.json` 的 `background` 或 `theme.bg` 使用。

两条路线，**COM 优先**：

  1. **COM 渲染路线（默认）** —— 让 WPS/PowerPoint 自己把指定页渲染成 PNG。
     这是唯一能拿到「母版背景 + 版式背景 + 页面背景」合成结果的方式，
     渐变、图片、纹理、主题色全部正确。
  2. **ZIP 解包路线（--zip-only 或 COM 不可用）** —— 直接从 pptx 里找背景图：
     先按 `p:bg` 里的图片引用顺着 rels 找（优先级：页面 > 版式 > 母版），
     找不到就退化为「media 里面积最大的图」。**拿不到合成效果**，
     渐变/纯色主题背景会失败（那种情况请用 COM 路线）。

用法：

    python extract_bg.py 用户模板.pptx                     # → ./work/template_bg.png
    python extract_bg.py 模板.pptx --page 3 --out work     # 指定页
    python extract_bg.py 模板.pptx --zip-only              # 无 Office 环境
    python extract_bg.py 模板.pptx --size 1920x1080        # 指定输出尺寸

退出码：0 成功 · 1 提取失败 · 2 参数错误 · 3 缺少依赖
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath

DEFAULT_W, DEFAULT_H = 960, 540

_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

_IMG_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp")


# ---------------------------------------------------------------------------
# 路线 1 · COM 渲染
# ---------------------------------------------------------------------------

def _new_engine():
    """独占实例起 WPS / PowerPoint（DispatchEx，避免复用已跑实例）。"""
    import win32com.client

    last = None
    for progid in ("PowerPoint.Application.16", "PowerPoint.Application.15",
                   "PowerPoint.Application.14", "KWPP.Application"):
        try:
            return win32com.client.DispatchEx(progid)
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise RuntimeError(f"无法启动 PowerPoint/WPS COM 引擎：{last}")


def extract_via_com(pptx: Path, out_png: Path, page: int, w: int, h: int) -> bool:
    """让应用渲染指定页为 PNG。返回是否成功。"""
    try:
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401
    except ImportError:
        print("  （COM 路线不可用：缺 pywin32）", file=sys.stderr)
        return False

    app = None
    pres = None
    try:
        app = _new_engine()
        # ⚠️ **不要**设 app.Visible = False：Office 会报
        #    「Application.Visible : Invalid request. Hiding the application window is not allowed.」
        #    隐藏应用窗口是不被允许的；用 Presentations.Open(..., WithWindow=False)
        #    让文稿本身不显示窗口即可（实测踩到）。
        # ⚠️ COM 一律吃绝对路径
        pres = app.Presentations.Open(str(pptx.resolve()), ReadOnly=True,
                                      Untitled=False, WithWindow=False)
        total = int(pres.Slides.Count)
        idx = max(1, min(page, total))
        out_png.parent.mkdir(parents=True, exist_ok=True)
        pres.Slides(idx).Export(str(out_png.resolve()), "PNG", w, h)
        ok = out_png.is_file() and out_png.stat().st_size > 0
        if ok:
            print(f"  COM 渲染第 {idx}/{total} 页 → {out_png.name}  {w}×{h}")
        return ok
    except Exception as exc:  # noqa: BLE001
        print(f"  COM 路线失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return False
    finally:
        if pres is not None:
            try:
                pres.Close()
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()          # 只退我们自己的独占实例
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 路线 2 · ZIP 解包
# ---------------------------------------------------------------------------

def _rels_map(z: zipfile.ZipFile, part: str) -> dict[str, str]:
    """读某个 part 的 rels，返回 rId → 包内路径。

    注意：Target 是**相对 part 目录**的，常见形如 `../media/image1.png`。
    必须用 posixpath.normpath 真正把 `..` 应用到上一级目录 ——
    只把 `..` 段过滤掉会得到 `ppt/slides/media/...` 这种不存在的路径
    （本项目实测踩到，zipfile 直接抛 KeyError）。
    """
    import posixpath

    d = PurePosixPath(part).parent
    rels = (d / "_rels" / (PurePosixPath(part).name + ".rels")).as_posix()
    if rels not in z.namelist():
        return {}
    from lxml import etree

    root = etree.fromstring(z.read(rels))
    out: dict[str, str] = {}
    for rel in root.findall(f"{{{_PKG_REL_NS}}}Relationship"):
        if rel.get("TargetMode") == "External":
            continue
        target = rel.get("Target", "")
        if not target:
            continue
        if target.startswith("/"):
            resolved = target.lstrip("/")
        else:
            resolved = posixpath.normpath((d / target).as_posix())
        out[rel.get("Id")] = resolved
    return out


def _bg_image_in(z: zipfile.ZipFile, part: str) -> str | None:
    """在某个 part 的 **`<p:bg>` 子树内** 找图片引用，返回包内路径。

    ⚠️ 必须限定在 `p:bg` 里找：整个 part 里的 `<a:blip>` 可能是**任何一个形状**的
    图片填充，直接 `iter()` 全文档会把正文里的配图当成背景（实测踩到，
    截回来一张 2522×572 的装饰横条）。
    """
    if part not in z.namelist():
        return None
    from lxml import etree

    try:
        root = etree.fromstring(z.read(part))
    except Exception:
        return None
    rels = _rels_map(z, part)
    for bg in root.iter(f"{{{_P_NS}}}bg"):
        for blip in bg.iter(f"{{{_A_NS}}}blip"):
            rid = blip.get(f"{{{_R_NS}}}embed") or blip.get(f"{{{_R_NS}}}link")
            if not rid:
                continue
            target = rels.get(rid)
            if target and target.lower().endswith(_IMG_EXT):
                return target
    return None


def _slide_aspect(z: zipfile.ZipFile) -> float:
    """从 presentation.xml 的 sldSz 拿到页面宽高比（EMU），默认 16:9。"""
    from lxml import etree

    part = "ppt/presentation.xml"
    if part not in z.namelist():
        return 16 / 9
    try:
        root = etree.fromstring(z.read(part))
        sz = root.find(f"{{{_P_NS}}}sldSz")
        cx, cy = int(sz.get("cx")), int(sz.get("cy"))
        if cx > 0 and cy > 0:
            return cx / cy
    except Exception:
        pass
    return 16 / 9


def extract_via_zip(pptx: Path, out_png: Path) -> bool:
    """从 pptx 里挖背景图。拿不到母版合成效果，仅作无 Office 时的兜底。"""
    try:
        from PIL import Image
    except ImportError:
        print("  （ZIP 路线不可用：缺 pillow）", file=sys.stderr)
        return False

    with zipfile.ZipFile(pptx) as z:
        names = z.namelist()
        candidates: list[str] = []
        # 1) 页面背景（第 1 页优先）
        for part in sorted(n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)):
            hit = _bg_image_in(z, part)
            if hit:
                candidates.append(hit)
        # 2) 版式背景
        for part in sorted(n for n in names if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n)):
            hit = _bg_image_in(z, part)
            if hit:
                candidates.append(hit)
        # 3) 母版背景
        for part in sorted(n for n in names if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n)):
            hit = _bg_image_in(z, part)
            if hit:
                candidates.append(hit)

        chosen = candidates[0] if candidates else None
        if chosen is None:
            # 4) 兜底：在 media 里挑「比例最接近幻灯片」的最大图。
            #    只挑最大的会选到装饰长条（实测：2522×572 的横条被当成背景），
            #    所以先用 presentation.xml 的 sldSz 拿到真实页面比例，用它过滤。
            slide_ar = _slide_aspect(z)
            media = [n for n in names
                     if n.startswith("ppt/media/") and n.lower().endswith(_IMG_EXT)]
            scored = []
            for m in media:
                try:
                    with Image.open(z.open(m)) as im:
                        w, h = im.size
                except Exception:
                    continue
                if not w or not h:
                    continue
                ar = w / h
                scored.append((abs(ar - slide_ar), -w * h, m, ar))
            if not scored:
                print("  模板里没有可用图片背景（纯色/渐变主题请用 COM 路线）",
                      file=sys.stderr)
                return False
            scored.sort()
            dev, _, chosen, ar = scored[0]
            if dev > 0.15:
                print(f"  ⚠️ 模板里没有接近页面比例({slide_ar:.3f})的图；"
                      f"最近的一张是 {ar:.3f}，很可能不是背景图。"
                      f"纯色/渐变母版请用 COM 路线。", file=sys.stderr)
            else:
                print("  未找到 p:bg 图片引用，退化为最接近页面比例的最大媒体图")

        out_png.parent.mkdir(parents=True, exist_ok=True)
        with z.open(chosen) as src, open(out_png, "wb") as dst:
            shutil.copyfileobj(src, dst)
        print(f"  解包 {chosen} → {out_png.name}")
        return True


# ---------------------------------------------------------------------------
# 校验与 CLI
# ---------------------------------------------------------------------------

def report_ratio(png: Path, want_w: int, want_h: int) -> None:
    """报告尺寸与比例是否达标（16:9 / 指定比例）。"""
    try:
        from PIL import Image
    except ImportError:
        return
    try:
        with Image.open(png) as im:
            w, h = im.size
    except Exception:
        return
    ar = w / h if h else 0
    want = want_w / want_h if want_h else 0
    flag = "✔" if abs(ar - want) < 0.02 else "⚠️"
    print(f"  {flag} 实际尺寸 {w}×{h}（比例 {ar:.3f}，目标 {want:.3f}）")
    if flag == "⚠️":
        print("     比例不符：页面上会被拉伸或留边。优先换模板页，"
              "或明确改用 cover/fit-contain 语义（见 28-image-prompts.md §二）")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Rouo PPT · 模板背景提取")
    ap.add_argument("template", help="用户模板 .pptx 路径")
    ap.add_argument("--out", default="work", help="输出目录（默认 ./work）")
    ap.add_argument("--name", default="template_bg.png", help="输出文件名")
    ap.add_argument("--page", type=int, default=1, help="用第几页渲染（默认 1）")
    ap.add_argument("--size", default=f"{DEFAULT_W}x{DEFAULT_H}",
                    help=f"输出尺寸 WxH（默认 {DEFAULT_W}x{DEFAULT_H}）")
    ap.add_argument("--zip-only", action="store_true", help="只用解包路线，不连 Office")
    args = ap.parse_args(argv)

    src = Path(args.template)
    if not src.is_file():
        print(f"模板不存在：{src}", file=sys.stderr)
        return 2
    if src.suffix.lower() != ".pptx":
        print(f"只支持 .pptx（收到 {src.suffix}）。.ppt 请先另存为 .pptx。", file=sys.stderr)
        return 2
    try:
        m = re.fullmatch(r"(\d+)x(\d+)", args.size)
        want_w, want_h = int(m.group(1)), int(m.group(2))
    except Exception:
        print(f"--size 需要 WxH，例如 960x540（收到 {args.size!r}）", file=sys.stderr)
        return 2

    out_png = Path(args.out) / args.name
    print(f"模板：{src}")
    ok = False
    if not args.zip_only:
        ok = extract_via_com(src, out_png, args.page, want_w, want_h)
        if not ok:
            print("  回退到 ZIP 解包路线……")
    if not ok:
        ok = extract_via_zip(src, out_png)
    if not ok:
        print("提取失败：模板可能使用纯色/渐变母版，请确认已装 WPS 或 PowerPoint。",
              file=sys.stderr)
        return 1

    report_ratio(out_png, want_w, want_h)
    print(f"完成：{out_png.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
