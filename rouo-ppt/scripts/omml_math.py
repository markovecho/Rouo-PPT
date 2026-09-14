#!/usr/bin/env python
"""Rouo PPT · 原生公式（LaTeX → Office Math / OMML）

把 LaTeX 转成 PowerPoint / WPS **原生可编辑**的公式对象（OMML），
按行内或块级注入 pptx 文本框——双击就能改，不是图片。

链路（三段，全部实测可用）：

    LaTeX --latex2mathml--> MathML --MML2OMML.XSL--> OMML(<m:oMath>) --注入--> pptx

为什么不用「截图公式」：公式是学术/课件 deck 里最常被要求改的东西，
一张图等于把返工成本推给用户。铁律 3「原生可编辑」对公式同样成立。

依赖：latex2mathml · lxml · python-pptx
      OMML 转换表用本机 Office 自带（或 LibreOffice 的 math.xsl）。
      装依赖（走镜像，本机 PyPI 直连不稳）：
        <venv>\\Scripts\\python.exe -m pip install latex2mathml \\
            -i https://pypi.tuna.tsinghua.edu.cn/simple

子命令：
    omml   <latex>            打印 OMML XML
    mathml <latex>            打印 MathML
    check                     检查依赖与转换表是否就绪
    demo   <out.pptx>         生成一个含公式的样例，用于目视验证

库用法（在 python-pptx 项目里）：

    from omml_math import append_math
    append_math(text_frame, r"E = mc^{2} + \\frac{a}{b}", size_pt=24)   # → 块级，新段
    append_math(text_frame, r"O(n\\log n)", size_pt=18, inline=True)     # → 行内，接在本段尾
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# MML2OMML.XSL 的常见位置（Office 各版本 + LibreOffice）
_XSL_CANDIDATES = (
    r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL",
    r"C:\Program Files (x86)\Microsoft Office\Office16\MML2OMML.XSL",
    r"C:\Program Files\LibreOffice\share\config\math.xsl",
)


def find_xsl() -> Path | None:
    """定位 MathML → OMML 的 XSL 转换表。"""
    env = os.environ.get("ROUO_MML2OMML_XSL")
    if env and Path(env).is_file():
        return Path(env)
    for cand in _XSL_CANDIDATES:
        if Path(cand).is_file():
            return Path(cand)
    # 兜底：在 Office 根目录里扫一遍（版本号会变）
    for root in (r"C:\Program Files\Microsoft Office", r"C:\Program Files (x86)\Microsoft Office",
                 r"C:\Program Files\LibreOffice"):
        p = Path(root)
        if p.is_dir():
            for hit in p.rglob("MML2OMML.XSL"):
                return hit
            for hit in p.rglob("math.xsl"):
                return hit
    return None


def latex_to_mathml(latex: str) -> str:
    import latex2mathml.converter as conv

    return conv.convert(latex)


def mathml_to_omml(mathml: str) -> str:
    """MathML → OMML 片段（返回 `<m:oMath>` 的 XML 字符串）。"""
    from lxml import etree

    xsl = find_xsl()
    if xsl is None:
        raise RuntimeError(
            "找不到 MathML->OMML 转换表。装 Office 会自带 MML2OMML.XSL；"
            "或用环境变量 ROUO_MML2OMML_XSL 指到该文件。"
        )
    transform = etree.XSLT(etree.parse(str(xsl)))
    result = transform(etree.fromstring(mathml.encode("utf-8")))
    return etree.tostring(result, encoding="unicode")


def latex_to_omml(latex: str) -> str:
    return mathml_to_omml(latex_to_mathml(latex))


def _merge_into_nsmap(elem, nsmap_extra):
    """把命名空间声明合并进元素（lxml 不支持改已建元素的 nsmap，故重建）。"""
    from lxml import etree

    nsmap = dict(elem.nsmap)
    nsmap.update({k: v for k, v in nsmap_extra.items() if k})
    return etree.fromstring(etree.tostring(elem), parser=etree.XMLParser(remove_blank_text=False))


def append_math(text_frame, latex: str, size_pt: float | None = None,
                inline: bool = False, bold: bool = False):
    """把 LaTeX 公式作为**原生 Office Math** 注入 python-pptx 的文本框。

    inline=False（默认）：新起一段放块级公式
    inline=True      ：接在当前最后一段的尾部（行内公式）

    返回承载公式的 `a:p` 元素。
    """
    from lxml import etree

    omml_xml = latex_to_omml(latex)

    if inline and len(text_frame.paragraphs) > 0:
        p = text_frame.paragraphs[-1]._p
    else:
        para = text_frame.add_paragraph()
        p = para._p

    # 段落级默认字号（公式本体没有显式字号时按它渲染）
    if size_pt:
        _set_para_default_size(p, size_pt, bold)

    a14 = etree.SubElement(p, f"{{{A14_NS}}}m")
    omath_para = etree.SubElement(a14, f"{{{M_NS}}}oMathPara")
    omath = etree.fromstring(omml_xml.encode("utf-8"))
    if size_pt:
        _apply_run_size(omath, size_pt, bold)
    omath_para.append(omath)
    return p


def _set_para_default_size(p, pt: float, bold: bool) -> None:
    """写 a:pPr/a:defRPr/@sz（百分之一磅）。"""
    from lxml import etree

    A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
    ppr = p.find(f"{{{A_NS}}}pPr")
    if ppr is None:
        ppr = etree.Element(f"{{{A_NS}}}pPr")
        p.insert(0, ppr)
    defrpr = ppr.find(f"{{{A_NS}}}defRPr")
    if defrpr is None:
        defrpr = etree.SubElement(ppr, f"{{{A_NS}}}defRPr")
    defrpr.set("sz", str(int(round(pt * 100))))
    if bold:
        defrpr.set("b", "1")


def _apply_run_size(omath, pt: float, bold: bool) -> None:
    """给每个 m:r 前置 w:rPr（字号/加粗）。OMML 的尺寸用的是 Word 的 w 命名空间。"""
    from lxml import etree

    for r in omath.iter(f"{{{M_NS}}}r"):
        rpr = etree.Element(f"{{{W_NS}}}rPr")
        sz = etree.SubElement(rpr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", str(int(round(pt * 2))))   # w:sz 是半磅
        if bold:
            b = etree.SubElement(rpr, f"{{{W_NS}}}b")
            b.set(f"{{{W_NS}}}val", "1")
        r.insert(0, rpr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_check() -> int:
    problems = []
    try:
        import latex2mathml  # noqa: F401
        print("✔ latex2mathml")
    except ImportError:
        problems.append("缺 latex2mathml：<venv> -m pip install latex2mathml "
                        "-i https://pypi.tuna.tsinghua.edu.cn/simple")
    try:
        import lxml  # noqa: F401
        print("✔ lxml")
    except ImportError:
        problems.append("缺 lxml")
    try:
        import pptx  # noqa: F401
        print("✔ python-pptx")
    except ImportError:
        problems.append("缺 python-pptx")
    xsl = find_xsl()
    if xsl:
        print(f"✔ 转换表 {xsl}")
    else:
        problems.append("找不到 MML2OMML.XSL")
    if problems:
        for p in problems:
            print(f"✗ {p}", file=sys.stderr)
        return 1
    print("原生公式链路就绪。")
    return 0


def cmd_demo(out: str) -> int:
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(5.5))
    tf = box.text_frame
    tf.word_wrap = True

    tf.text = "原生公式样例 · 双击可编辑"
    tf.paragraphs[0].font.size = Pt(28)

    append_math(tf, r"E = mc^{2} + \frac{a}{b}", size_pt=32)
    append_math(tf, r"\int_{0}^{\infty} e^{-x^{2}}\,dx = \frac{\sqrt{\pi}}{2}", size_pt=28)
    append_math(tf, r"\sum_{k=1}^{n} k = \frac{n(n+1)}{2}", size_pt=24)
    append_math(tf, r"O(n\log n)", size_pt=20, inline=True)

    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(p))
    print(f"已写出：{p}")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "check":
        return cmd_check()
    if cmd == "omml":
        if not rest:
            print("用法：omml <latex>", file=sys.stderr)
            return 2
        print(latex_to_omml(rest[0]))
        return 0
    if cmd == "mathml":
        if not rest:
            print("用法：mathml <latex>", file=sys.stderr)
            return 2
        print(latex_to_mathml(rest[0]))
        return 0
    if cmd == "demo":
        return cmd_demo(rest[0] if rest else "exports/_math_demo.pptx")
    print(f"未知子命令：{cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
