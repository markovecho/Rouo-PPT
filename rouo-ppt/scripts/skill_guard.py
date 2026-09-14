#!/usr/bin/env python3
"""Rouo PPT · Skill Integrity Guard（fail-closed 完整性校验）

校验本 skill 自身的结构契约：
  1. SKILL.md frontmatter 身份字段齐全
  2. 全部承诺的参考文档存在
  3. 网页线资产（骨架 / 动效运行时 / 校验器）存在
  4. SKILL.md 保留对本守卫的自引用
  5. 命名洁净：任何文件名、以及 SKILL.md / references/*.md / assets/*.html /
     scripts/*.mjs 的内容里，不得出现上游技能的血缘标识（本 skill 是独立作者化路线）
  6. 可达性洁净：assets/ 下的骨架不得引用本机不可达的外链主机
  7. 引用完整性：assets/ 骨架里提到的 references/NN-*.md 必须真实存在

纯标准库，零网络。用法：

    python skill_guard.py                     # 校验
    python skill_guard.py --write-manifest    # 对当前树写 SHA-256 清单
    python skill_guard.py --list              # 列出受追踪文件

退出码：0 = 通过；78 = 结构不变量失败（fail-closed）。

可选篡改检测（默认关）：设环境变量 ROUO_GUARD_STRICT=1 时额外校验
SHA-256 清单。正常编辑参考文档后需重算清单，故为可选项。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

_ERROR_MESSAGE = (
    "Rouo PPT skill integrity check failed. The skill bundle is incomplete, "
    "modified, or contaminated: restore missing files, revert local edits, "
    "or rebuild from a clean copy."
)

_SKILL_DIR = Path(__file__).resolve().parent.parent
_MANIFEST_NAME = ".integrity_manifest.json"
_MANIFEST_PATH = _SKILL_DIR / "references" / _MANIFEST_NAME
_SKILL_FILE = "SKILL.md"

# 全部参考文档契约（与 SKILL.md §八索引一一对应）
_REQUIRED_REFERENCES = (
    "01-mainline.md",
    "02-express.md",
    "03-direction-gate.md",
    "04-style-armory.md",
    "05-brand-assets.md",
    "06-taste-rules.md",
    "07-brief-and-lock.md",
    "08-page-craft.md",
    "09-shape-language.md",
    "10-drive-engine.md",
    "11-deck-data-format.md",
    "12-presets-review.md",
    "13-edit-existing.md",
    "14-image-rebuild.md",
    "15-template-system.md",
    "16-motion-voice.md",
    "17-review.md",
    "18-troubleshooting.md",
    "19-environment.md",
    # —— 风格族 + 网页线（v2.0 新增） ——
    "20-style-gate.md",
    "21-style-electronic.md",
    "22-style-minimal.md",
    "23-style-watercolor.md",
    "24-style-variants.md",
    "25-web-deck.md",
    "26-shot-framing.md",
    "27-pptx-assembly.md",
    # —— 上游能力补齐（v2.1 新增）：配图 / 预检 / 动效 / 原生对象 / 画布 / 视频 / 调参 ——
    "28-image-prompts.md",
    "29-preflight-checklist.md",
    "30-motion-recipes.md",
    "31-native-objects.md",
    "32-canvas-formats.md",
    "33-video-storyboard.md",
    "34-web-tweaks.md",
)

# 网页线资产契约：拷走就能用，缺一不可
_REQUIRED_ASSETS = (
    "assets/deck-shell-electronic.html",
    "assets/deck-shell-minimal.html",
    "assets/motion.min.js",
    "scripts/deck_validate.mjs",
    "scripts/notes_validate.mjs",
    "scripts/tools.py",
    "scripts/pptx_assembly.py",
    "scripts/com_drive.py",
    "scripts/extract_bg.py",
    "scripts/omml_math.py",
)

# 本守卫必须仍被 SKILL.md 引用（总纲 §十一）
_SELF_REFERENCE = "scripts/skill_guard.py"

# frontmatter 必需字段
_REQUIRED_FRONTMATTER_FIELDS = ("name", "description")
_REQUIRED_METADATA_LINE = "agent_created: true"

# 血缘洁净：文件名与内容中禁止出现的上游标识（拼接构造，避免自伤）
# 前六个是上游技能名；后一组是上游技能里真实出现过的**文件名主干**——
# 它们最容易随「参考实现」被抄回来（曾出现 validate-swiss-deck.mjs / swiss-layout-lock.md），
# 拼成"库名-构件"形态，本 skill 一旦出现即视为血缘回归。
_LINEAGE_MARKERS = (
    "huashu" + "-" + "design",
    "huashu" + "_" + "design",
    "ppt" + "-" + "master",
    "ppt" + "_" + "master",
    "guizang",
    "歸藏",
    "op7418",
    # —— 上游文件名主干（本 skill 无任何合法出现） ——
    "swiss" + "-" + "layout" + "-" + "lock",
    "swiss" + "-" + "map" + "-" + "component",
    "screenshot" + "-" + "framing",
    "validate" + "-" + "swiss" + "-" + "deck",
    "validate" + "-" + "presenter" + "-" + "mode",
    "layouts" + "-" + "swiss",
    "themes" + "-" + "swiss",
)

# 本机不可达 / 已替换掉的外链主机：出现即视为回归（见 19-environment.md）
# Google Fonts 与 unpkg 在本机都不可达，骨架必须走本地兜底栈 —— 曾经「文档说已降级、
# 骨架里却还挂着 link」的静默不一致，就是靠这份清单兜住的。
_FORBIDDEN_HOSTS = ("unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com")

# 内容洁净扫描范围：文档 + 网页骨架 + node 校验器
_TEXT_SCAN_EXTENSIONS = (".md", ".html", ".mjs")
_TEXT_SCAN_SKIP_DIRS = {"__pycache__"}

# assets/ 里提到的 references/NN-*.md 必须真实存在
_REF_CITATION_RE = re.compile(r"references/([0-9]{2}-[a-z0-9-]+\.md)")


def _read_text(path: Path) -> str:
    """UTF-8 读取并归一换行；拒绝 BOM。"""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _frontmatter(skill_text: str) -> str:
    if not skill_text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = skill_text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    return skill_text[4:end]


def _scannable_text_files() -> list[Path]:
    """全部需要做内容洁净扫描的文本文件。"""
    files: list[Path] = []
    for path in sorted(_SKILL_DIR.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _TEXT_SCAN_SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _TEXT_SCAN_EXTENSIONS:
            files.append(path)
    return files


def check_frontmatter() -> list[str]:
    """校验 SKILL.md 身份字段与自引用，返回问题列表。"""
    problems: list[str] = []
    text = _read_text(_SKILL_DIR / _SKILL_FILE)
    meta = _frontmatter(text)
    lines = meta.splitlines()
    for field in _REQUIRED_FRONTMATTER_FIELDS:
        if not any(
            ln.startswith(f"{field}:") or ln.startswith(f"  {field}:") for ln in lines
        ):
            problems.append(f"frontmatter 缺少字段: {field}")
    if _REQUIRED_METADATA_LINE not in meta:
        problems.append("frontmatter 缺少 agent_created: true")
    if _SELF_REFERENCE not in text:
        problems.append("SKILL.md 丢失对完整性守卫的自引用")
    # 风格门是铁律 6，总纲必须点到它，否则这条铁律会静默失效
    if "20-style-gate.md" not in text:
        problems.append("SKILL.md 丢失对风格门（20-style-gate.md）的引用")
    return problems


def check_files() -> list[str]:
    """校验全部承诺文件存在，返回问题列表。"""
    problems: list[str] = []
    for name in _REQUIRED_REFERENCES:
        if not (_SKILL_DIR / "references" / name).is_file():
            problems.append(f"缺少参考文档: references/{name}")
    for rel in _REQUIRED_ASSETS:
        if not (_SKILL_DIR / rel).is_file():
            problems.append(f"缺少资产/脚本: {rel}")
    return problems


def check_lineage_cleanliness() -> list[str]:
    """校验命名洁净：文件名 + 文本内容无上游血缘标识。"""
    problems: list[str] = []
    # 1) 文件名（整个 skill 树）
    for path in sorted(_SKILL_DIR.rglob("*")):
        if path.is_file():
            rel = path.relative_to(_SKILL_DIR).as_posix()
            for marker in _LINEAGE_MARKERS:
                if marker in rel.lower():
                    problems.append(f"文件名含上游标识: {rel}")
                    break
    # 2) 文本内容（文档 + 骨架 + 校验器）
    for target in _scannable_text_files():
        rel = target.relative_to(_SKILL_DIR).as_posix()
        try:
            content = _read_text(target).lower()
        except (OSError, UnicodeError, ValueError):
            problems.append(f"文件无法读取: {rel}")
            continue
        for marker in _LINEAGE_MARKERS:
            if marker in content:
                problems.append(f"内容含上游标识 {marker!r}: {rel}")
                break
    return problems


def check_reachable_hosts() -> list[str]:
    """校验网页骨架没有 **真正引用** 本机不可达的外链主机。

    只匹配真实的资源引用（`href=` / `src=` 指向 `http(s)://<host>`）。
    注释或说明文字里提到这些主机（例如解释「为何不挂 Google Fonts」）不算回归 ——
    否则文档与守卫会互相打架，人人都学会在注释里说反话。
    """
    problems: list[str] = []
    for rel in _REQUIRED_ASSETS:
        if not rel.startswith("assets/") or not rel.endswith(".html"):
            continue
        target = _SKILL_DIR / rel
        if not target.is_file():
            continue
        content = _read_text(target)
        for host in _FORBIDDEN_HOSTS:
            pattern = re.compile(
                r"""(?:href|src)\s*=\s*["']?https?://""" + re.escape(host),
                re.IGNORECASE,
            )
            if pattern.search(content):
                problems.append(f"{rel} 引用了不可达主机 {host}（应换 jsdelivr）")
    return problems


def check_reference_citations() -> list[str]:
    """校验 assets/ 骨架里引用的 references/NN-*.md 都真实存在。"""
    problems: list[str] = []
    seen: set[str] = set()
    for rel in _REQUIRED_ASSETS:
        if not rel.startswith("assets/") or not rel.endswith(".html"):
            continue
        target = _SKILL_DIR / rel
        if not target.is_file():
            continue
        for cited in _REF_CITATION_RE.findall(_read_text(target)):
            key = f"{rel}->{cited}"
            if key in seen:
                continue
            seen.add(key)
            if not (_SKILL_DIR / "references" / cited).is_file():
                problems.append(f"{rel} 引用了不存在的文档: references/{cited}")
    return problems


def _tracked_paths() -> list[Path]:
    paths = [_SKILL_DIR / _SKILL_FILE, Path(__file__)]
    paths += [_SKILL_DIR / "references" / n for n in _REQUIRED_REFERENCES]
    paths += [_SKILL_DIR / rel for rel in _REQUIRED_ASSETS if not rel.endswith(".py")]
    return paths


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest() -> int:
    import json

    manifest = {
        p.relative_to(_SKILL_DIR).as_posix(): _sha256(p)
        for p in _tracked_paths()
        if p.is_file()
    }
    _MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {_MANIFEST_PATH}")
    return 0


def check_strict_manifest() -> list[str]:
    if os.environ.get("ROUO_GUARD_STRICT") != "1":
        return []
    import json

    if not _MANIFEST_PATH.is_file():
        return ["严格模式：缺少 SHA-256 清单"]
    problems: list[str] = []
    expected: dict[str, str] = json.loads(_read_text(_MANIFEST_PATH))
    for rel, digest in expected.items():
        target = _SKILL_DIR / rel
        if not target.is_file() or _sha256(target) != digest:
            problems.append(f"严格模式：文件被改动或缺失: {rel}")
    return problems


def run_checks() -> list[str]:
    problems: list[str] = []
    for checker in (
        check_frontmatter,
        check_files,
        check_lineage_cleanliness,
        check_reachable_hosts,
        check_reference_citations,
        check_strict_manifest,
    ):
        problems.extend(checker())
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rouo PPT skill integrity guard.")
    parser.add_argument("--write-manifest", action="store_true",
                        help="对当前树写 references/.integrity_manifest.json")
    parser.add_argument("--list", action="store_true", help="列出受追踪文件")
    args = parser.parse_args(argv)

    if args.list:
        for p in _tracked_paths():
            print(p.relative_to(_SKILL_DIR).as_posix())
        return 0
    if args.write_manifest:
        return write_manifest()

    problems = run_checks()
    if problems:
        print(_ERROR_MESSAGE, file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 78

    refs = len(_REQUIRED_REFERENCES)
    assets = len(_REQUIRED_ASSETS)
    print(f"Rouo PPT integrity: OK（{refs} 份参考文档 · {assets} 项资产/脚本）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
