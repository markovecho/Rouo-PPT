#!/usr/bin/env python3
"""Rouo PPT · 工具调度器

统一入口：把本 skill 文档里的语义命令（check / export / source …）转发给
本机已部署的 SVG→PPTX 转换工具链。

设计要点：
- 底层工具路径不在任何文档里硬编码——本脚本启动时按「签名文件」自动发现
  部署位置（也可用环境变量 ROUO_TOOLCHAIN 指定），跨版本目录重命名仍可用。
- 参数原样透传，底层工具的 flag 语义不变。
- 纯标准库，零网络。

用法：
    python tools.py <命令> [参数…]
    python tools.py whereis              # 打印发现的底层工具路径（排查部署用）
    python tools.py list                 # 列出工具链里全部原始脚本
    python tools.py raw <script.py> …    # 命令表没覆盖时的直通逃生舱
    python tools.py deck-check  index.html     # 极简风版式锁 + 排版测量（走 node）
    python tools.py notes-check index.html     # 页面 ID 与演讲备注一致性（走 node）
    python tools.py com-probe                   # 探测本机 WPS / PowerPoint 的 COM 引擎
    python tools.py com-drive  deck_data.json   # 量产线：COM 直驱可见生成 deck
    python tools.py extract-bg 模版.pptx        # 量产线工步 1：提模板背景为 template_bg.png
    python tools.py math-check                  # 原生公式链路自检（LaTeX → Office Math）
    python tools.py math-omml  "E=mc^2"         # LaTeX → OMML XML

命令表见 references/19-environment.md §八。
com-* / extract-bg / math-* / assemble / pptx-* 走的是本 skill 自带的 scripts/，不需要底层工具链。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 工具链发现
# ---------------------------------------------------------------------------

# 签名文件：一个目录同时含有这两个脚本，即认定为转换工具链部署点
_SIGNATURE_FILES = ("svg_to_pptx.py", "svg_quality_checker.py")


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("ROUO_TOOLCHAIN")
    if env:
        roots.append(Path(env))
    skills_root = Path.home() / ".workbuddy" / "skills"
    if skills_root.is_dir():
        for child in sorted(skills_root.iterdir()):
            if child.is_dir():
                roots.append(child / "scripts")
    return roots


def discover_toolchain() -> Path | None:
    """按签名文件发现本机部署的转换工具链目录。"""
    for root in _candidate_roots():
        if all((root / name).is_file() for name in _SIGNATURE_FILES):
            return root
    return None


# ---------------------------------------------------------------------------
# 命令注册：语义命令 -> (底层脚本, 前置参数)
# ---------------------------------------------------------------------------

COMMANDS: dict[str, tuple[str, list[str]]] = {
    # —— 手作线主线：SVG 编写 → 质检 → 导出 ——
    "check":           ("svg_quality_checker.py", []),
    "export":          ("svg_to_pptx.py", []),
    "adopt":           ("svg_authoring_view.py", []),
    "refresh-summary": ("svg_authoring_view.py", ["--refresh-summary"]),
    "authoring":       ("authoring_roundtrip.py", []),
    "svg-finalize":    ("finalize_svg.py", []),
    "svg-compat":      ("svg_compatibility.py", []),
    "svg-position":    ("svg_position_calculator.py", []),
    "svg-compact":     ("compact_svg_coordinates.py", []),
    "svg-contract":    ("svg_authoring_contract.py", []),
    "preset-shape":    ("preset_shape_svg.py", []),
    "shape-boolean":   ("shape_boolean_svg.py", []),
    "semantic-table":  ("semantic_table.py", []),
    "text-measure":    ("text_measure.py", []),
    "latex":           ("latex_render.py", []),
    # —— 素材与可视化 ——
    "source":          ("source_to_md.py", []),
    "image-search":    ("image_search.py", []),
    "image-treat":     ("image_treat.py", []),
    "image-gen":       ("image_gen.py", []),
    "icon-sync":       ("icon_sync.py", []),
    "chart-recall":    ("chart_recall.py", []),
    "viz-recall":      ("visualization_recall.py", []),
    "viz-catalog":     ("visualization_catalog.py", []),
    # —— 模板体系 ——
    "template-apply":    ("apply_template.py", []),
    "template-register": ("register_template.py", []),
    "template-preview":  ("template_preview_pptx.py", []),
    "template-slots":    ("template_text_slots.py", []),
    "template-import":   ("pptx_template_import.py", []),
    # —— 交付校验与原生编辑 ——
    "validate":        ("project_manager.py", ["validate"]),
    "batch-validate":  ("batch_validate.py", []),
    "delivery-check":  ("pptx_delivery_check.py", []),
    "opc-validate":    ("pptx_opc_validation.py", []),
    "intake":          ("pptx_intake.py", []),
    "import-pptx":     ("pptx_to_svg.py", []),
    "visual-review":   ("visual_review.py", []),
    "native-payloads": ("native_payloads.py", []),
    "pptx-anim":       ("pptx_animations.py", []),
    "pptx-effects":    ("pptx_effects.py", []),
    "pptx-transitions": ("pptx_transitions.py", []),
    "pptx-gradients":  ("pptx_gradients.py", []),
    "pptx-fonts":      ("pptx_embedded_fonts.py", []),
    "hyperlinks":      ("hyperlink_contract.py", []),
    # —— 讲述、配音、视频 ——
    "notes-split":     ("total_md_split.py", []),
    "notes-audio":     ("notes_to_audio.py", []),
    "narration":       ("narration_sync.py", []),
    "sound-sync":      ("sound_sync.py", []),
    "anim-groups":     ("animation_config.py", ["list-groups"]),
    "anim-validate":   ("animation_config.py", ["validate"]),
    "video":           ("powerpoint_video.py", []),
    "video-plan":      ("video_motion_plan.py", []),
    "video-subtitles": ("video_subtitles.py", []),
    "video-mix":       ("video_sound_mix.py", []),
    # —— 上下文 ——
    "page-context":    ("page_context.py", []),
    "slide-roster":    ("slide_roster.py", []),
}


# ---------------------------------------------------------------------------
# 网页 deck 校验器：走 node，脚本随本 skill 发布，不依赖转换工具链
# ---------------------------------------------------------------------------

_SKILL_DIR = Path(__file__).resolve().parent.parent

NODE_COMMANDS: dict[str, str] = {
    "deck-check":  "deck_validate.mjs",    # 极简风版式锁 + 排版测量
    "notes-check": "notes_validate.mjs",   # 页面 ID 与演讲备注一致性
}

# 技能自带的 Python 工具（与 NODE_COMMANDS 一样不需要底层工具链）
LOCAL_COMMANDS: dict[str, tuple[str, list[str]]] = {
    "com-probe":     ("com_drive.py", ["probe"]),
    "com-drive":     ("com_drive.py", ["drive"]),
    "com-review":    ("com_drive.py", ["review"]),
    "assemble":      ("pptx_assembly.py", ["assemble"]),
    "pptx-optimize": ("pptx_assembly.py", ["optimize"]),
    "pptx-export":   ("pptx_assembly.py", ["export"]),
    "pptx-measure":  ("pptx_assembly.py", ["measure"]),
    "extract-bg":    ("extract_bg.py", []),        # 模板背景提取（量产线工步 1）
    "math-check":    ("omml_math.py", ["check"]),  # 原生公式链路自检
    "math-omml":     ("omml_math.py", ["omml"]),   # LaTeX → OMML
    "math-demo":     ("omml_math.py", ["demo"]),   # 生成公式样例用于目视验证
}

# 这些命令要走 COM（pywin32）。裸的托管解释器没有 pywin32，所以单独挑解释器。
_COM_COMMANDS = {"com-probe", "com-drive", "pptx-export", "extract-bg"}
_PY_CANDIDATES = [
    sys.executable,
    r"C:\Users\33551\.workbuddy\binaries\python\envs\default\Scripts\python.exe",
    r"C:\Users\33551\.workbuddy\binaries\python\versions\3.13.12\python.exe",
    r"D:\python\python.exe",
]


def _com_python() -> str:
    """返回首个能 import pywin32 的解释器；全不行则回落 sys.executable（由脚本自己报错）。"""
    for cand in dict.fromkeys(_PY_CANDIDATES):  # 去重且保序
        if not cand or not Path(cand).is_file():
            continue
        if Path(cand) == Path(sys.executable):
            try:
                import win32com.client  # noqa: F401
                return sys.executable
            except ImportError:
                continue
        if subprocess.run([cand, "-c", "import win32com.client"],
                          capture_output=True).returncode == 0:
            return cand
    return sys.executable


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) < 1 or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        nodes = " · ".join(sorted(NODE_COMMANDS))
        local = " · ".join(sorted(LOCAL_COMMANDS))
        print("工具链命令：", " · ".join(sorted(COMMANDS)))
        print("自带命令：  ", f"{nodes} · {local} · whereis / list / raw")
        return 0

    command, rest = argv[0], argv[1:]

    # —— 网页 deck 校验器：走 node，用一个本 skill 自带的脚本 ——
    if command in NODE_COMMANDS:
        script = _SKILL_DIR / "scripts" / NODE_COMMANDS[command]
        if not script.is_file():
            print(f"缺少 {NODE_COMMANDS[command]}，部署不完整。", file=sys.stderr)
            return 3
        return subprocess.run(["node", str(script), *rest]).returncode

    # —— 技能内 Python 工具：不依赖底层工具链，必须先于工具链发现处理 ——
    if command in LOCAL_COMMANDS:
        script, prefix = LOCAL_COMMANDS[command]
        target = _SKILL_DIR / "scripts" / script
        if not target.is_file():
            print(f"缺少 scripts/{script}，部署不完整。", file=sys.stderr)
            return 3
        py = _com_python() if command in _COM_COMMANDS else sys.executable
        return subprocess.run([py, str(target), *prefix, *rest]).returncode

    if command == "whereis":
        root = discover_toolchain()
        if root is None:
            print("未发现工具链部署。可用环境变量 ROUO_TOOLCHAIN 指定其 scripts 目录。")
            return 1
        print(f"工具链目录: {root}")
        for name, (script, _) in sorted(COMMANDS.items()):
            print(f"  {name:18s} -> {script}")
        print("  （以下命令走本 skill 自带脚本，无需工具链）")
        for name, script in sorted(NODE_COMMANDS.items()):
            print(f"  {name:18s} -> node scripts/{script}")
        for name, (script, prefix) in sorted(LOCAL_COMMANDS.items()):
            tail = (" " + " ".join(prefix)) if prefix else ""
            print(f"  {name:18s} -> python scripts/{script}{tail}")
        return 0

    root = discover_toolchain()
    if root is None:
        print(
            "未发现本机部署的 SVG→PPTX 转换工具链（找含 "
            + " / ".join(_SIGNATURE_FILES)
            + " 的 scripts 目录）。\n"
              "请安装工具链，或设置环境变量 ROUO_TOOLCHAIN 指向其 scripts 目录。\n"
              "注意：com-* / assemble / pptx-* / deck-check / notes-check "
              "不依赖工具链，本机仍可用。",
            file=sys.stderr,
        )
        return 3

    # 列出工具链里的全部原始脚本（排查找不到的能力时用）
    if command == "list":
        for path in sorted(root.glob("*.py")):
            print(path.name)
        return 0

    # 直通：tools.py raw <script.py> [args…] —— 命令表没覆盖时的逃生舱
    if command == "raw":
        if not rest:
            print("用法: tools.py raw <script.py> [参数…]", file=sys.stderr)
            return 2
        script = rest[0]
        target = root / script
        if not target.is_file():
            print(f"工具链里没有 {script}。用 `tools.py list` 查看可用脚本。", file=sys.stderr)
            return 3
        return subprocess.run([sys.executable, str(target), *rest[1:]]).returncode

    if command not in COMMANDS:
        # 兜底：命令本身就是脚本名（带不带 .py 都行）
        target = root / (command if command.endswith(".py") else command + ".py")
        if target.is_file():
            return subprocess.run([sys.executable, str(target), *rest]).returncode
        print(f"未知命令: {command}", file=sys.stderr)
        print("可用命令：", " · ".join(sorted(COMMANDS)), file=sys.stderr)
        print("提示：还有 whereis / list / raw 三个元命令。", file=sys.stderr)
        return 2

    script, prefix = COMMANDS[command]
    target = root / script
    if not target.is_file():
        print(f"工具链缺少 {script}，部署不完整。", file=sys.stderr)
        return 3

    cmd = [sys.executable, str(target), *prefix, *rest]
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
