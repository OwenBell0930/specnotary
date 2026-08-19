#!/usr/bin/env python3
"""Generate README diagrams as SVG (no cairo required)."""
from __future__ import annotations

import os

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
os.makedirs(OUT, exist_ok=True)

BLUE = "#0B6BCB"
BLUE_LIGHT = "#E8F3FF"
BLUE_DARK = "#074A8C"
ORANGE = "#D97706"
GREEN = "#159947"
RED = "#DC2626"
GRAY = "#64748B"
GRAY_LIGHT = "#F8FAFC"
WHITE = "#FFFFFF"
TEXT = "#0F172A"
TEXT_MUTED = "#475569"
BORDER = "#CBD5E1"


def header(w=1280, h=720, bg=GRAY_LIGHT):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<defs>
  <filter id="shadow" x="-2%" y="-2%" width="104%" height="104%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.10"/>
  </filter>
  <marker id="arrow" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 9 3.5, 0 7" fill="{BLUE}"/>
  </marker>
  <marker id="arrow-green" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 9 3.5, 0 7" fill="{GREEN}"/>
  </marker>
  <marker id="arrow-red" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 9 3.5, 0 7" fill="{RED}"/>
  </marker>
</defs>
<rect width="{w}" height="{h}" fill="{bg}"/>
'''


def footer():
    return "</svg>\n"


def box(x, y, w, h, title, sub="", fill=WHITE, stroke=BLUE, title_size=16):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2" filter="url(#shadow)"/>'
    if sub:
        s += f'<text x="{x+w/2}" y="{y+h/2-8}" text-anchor="middle" fill="{TEXT}" font-family="Helvetica Neue,Arial,sans-serif" font-size="{title_size}" font-weight="700">{title}</text>'
        s += f'<text x="{x+w/2}" y="{y+h/2+14}" text-anchor="middle" fill="{TEXT_MUTED}" font-family="Helvetica Neue,Arial,sans-serif" font-size="13">{sub}</text>'
    else:
        s += f'<text x="{x+w/2}" y="{y+h/2}" text-anchor="middle" dominant-baseline="middle" fill="{TEXT}" font-family="Helvetica Neue,Arial,sans-serif" font-size="{title_size}" font-weight="700">{title}</text>'
    return s


def label(x, y, text, size=22, bold=True, anchor="middle", color=TEXT):
    weight = "700" if bold else "400"
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-family="Helvetica Neue,Arial,sans-serif" font-size="{size}" font-weight="{weight}">{text}</text>'


def line(x1, y1, x2, y2, marker="arrow", color=BLUE):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5" marker-end="url(#{marker})"/>'


def flow():
    svg = header(1280, 560)
    svg += label(640, 42, "SpecNotary Flow / 规格工程主流程", 26)
    svg += label(640, 72, "Machine-first · Generate human view · Hard gate (CLI) or degraded Skill", 14, bold=False, color=TEXT_MUTED)

    y = 130
    items = [
        (40, "1. Inputs", "原料 / 坏稿 / 反推"),
        (300, "2. Machine YAML", "机读唯一准据 · SSOT"),
        (560, "3. Human MD", "人读施工图 · Generated"),
        (820, "4. CLI Gate", "hard PASS/FAIL"),
        (1040, "5. Ready", "可开发 · Dev-ready"),
    ]
    for x, t, s in items:
        w = 200 if x < 1000 else 200
        fill = BLUE_LIGHT if "Machine" in t else WHITE
        stroke = BLUE_DARK if "Machine" in t else BLUE
        svg += box(x, y, w, 100, t, s, fill=fill, stroke=stroke, title_size=15)

    for i in range(4):
        x1 = 40 + i * 260 + 200
        svg += line(x1, y + 50, x1 + 60, y + 50)

    # secondary row
    svg += box(300, 320, 280, 90, "Skill (optional)", "起草机读 / 无运行时降级检查", fill="#FFF7ED", stroke=ORANGE)
    svg += box(700, 320, 280, 90, "Runtime", "python3 唯一硬门禁 · Node Deferred", fill=WHITE, stroke=GRAY)
    svg += line(440, 230, 440, 320, marker="arrow", color=ORANGE)
    svg += line(840, 230, 840, 320, marker="arrow", color=GRAY)

    svg += label(640, 470, "核心：自动化以机读为准；人读由机读生成，禁止长期只改人读", 15, bold=False, color=TEXT_MUTED)
    svg += footer()
    path = os.path.join(OUT, "flow.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(path)


def before_after():
    svg = header(1280, 640)
    svg += label(640, 36, "Case demo: Fake-detailed PRD → Dev-ready machine spec", 24)
    svg += label(640, 64, "案例：假详细需求 → 可开发机读规格（节选对照）", 14, bold=False, color=TEXT_MUTED)

    # left bad
    svg += f'<rect x="40" y="100" width="560" height="480" rx="16" fill="#FEF2F2" stroke="{RED}" stroke-width="2"/>'
    svg += label(320, 130, "BEFORE / 改造前", 20, color=RED)
    bad_lines = [
        "「支持智能搜索」",
        "「体验要好、尽量快」",
        "「权限按角色区分」——未列角色",
        "「异常要有提示」——未写文案/码",
        "无默认值 · 无空结果 · 无验收",
        "→ 研发只能猜，Agent 会瞎补",
    ]
    yy = 175
    for line_t in bad_lines:
        svg += label(70, yy, "• " + line_t, 16, bold=False, anchor="start", color=TEXT)
        yy += 42

    # right good
    svg += f'<rect x="680" y="100" width="560" height="480" rx="16" fill="#ECFDF5" stroke="{GREEN}" stroke-width="2"/>'
    svg += label(960, 130, "AFTER / 改造后（机读字段）", 20, color=GREEN)
    good_lines = [
        "search.fields: [title, id]",
        "search.match: fuzzy",
        "actors: [admin, member]",
        "empty_state: 「无匹配结果」",
        "defaults.page_size: 20",
        "acceptance: Given/When/Then × N",
        "→ CLI hard gate: PASS",
    ]
    yy = 175
    for line_t in good_lines:
        svg += label(710, yy, "• " + line_t, 16, bold=False, anchor="start", color=TEXT)
        yy += 42

    svg += line(600, 340, 680, 340, marker="arrow-green", color=GREEN)
    svg += footer()
    path = os.path.join(OUT, "before-after.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(path)


def architecture():
    svg = header(1280, 620)
    svg += label(640, 40, "What's in the box / 套件里有什么", 26)

    svg += box(60, 100, 360, 140, "Scaffold 脚手架", "templates · examples · docs", fill=BLUE_LIGHT)
    svg += box(460, 100, 360, 140, "CLI 硬门禁", "check · human · report · sync", fill=WHITE)
    svg += box(860, 100, 360, 140, "Skill 辅", "起草 / 降级检查", fill="#FFF7ED", stroke=ORANGE)

    svg += box(60, 300, 560, 160, "Machine source (YAML/JSON)", "唯一准据 · object_ai 权重可声明", fill=WHITE, stroke=BLUE_DARK)
    svg += box(660, 300, 560, 160, "Human view (Markdown)", "由机读生成 · 中英可工作", fill=WHITE)

    svg += line(240, 240, 240, 300)
    svg += line(640, 240, 640, 300)
    svg += line(1040, 240, 940, 300, color=ORANGE)

    svg += label(640, 530, "Python 硬门禁 · Node Deferred · 优先 YAML", 15, bold=False, color=TEXT_MUTED)
    svg += footer()
    path = os.path.join(OUT, "architecture.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(path)


def terminal_mock():
    svg = header(1280, 420, bg="#0B1220")
    svg += label(640, 36, "CLI preview / 命令行预览", 22, color=WHITE)
    svg += f'<rect x="80" y="70" width="1120" height="300" rx="14" fill="#020617" stroke="#334155" stroke-width="2"/>'
    lines = [
        ("$ specnotary check examples/case-order-cancel-bad/machine/spec.yaml", "#93C5FD"),
        ("gate_mode: hard", "#FBBF24"),
        ("FAIL: behavior B1: then-clause too vague for ready", "#FCA5A5"),
        ("FAIL: acceptance AC-01: not observable", "#FCA5A5"),
        ("RESULT: FAIL", "#F87171"),
        ("$ specnotary check examples/case-order-cancel-bad/machine/spec.fixed.yaml", "#93C5FD"),
        ("FAIL_COUNT: 0", "#94A3B8"),
        ("RESULT: PASS", "#4ADE80"),
    ]
    y = 110
    for text, color in lines:
        svg += f'<text x="110" y="{y}" fill="{color}" font-family="Menlo,Consolas,monospace" font-size="16">{text}</text>'
        y += 32
    svg += footer()
    path = os.path.join(OUT, "cli-preview.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(path)


def gate_layers():
    svg = header(1280, 460)
    svg += label(640, 42, "Gate Layers · FAIL / WARN / Pending", 26)
    svg += label(640, 72, "任意 1 条 FAIL → RESULT: FAIL；WARN 不否决但须清零或显式接受", 14, bold=False, color=TEXT_MUTED)

    svg += f'<rect x="60" y="110" width="1160" height="86" rx="12" fill="#FEF2F2" stroke="{RED}" stroke-width="2" filter="url(#shadow)"/>'
    svg += label(120, 146, "FAIL", 20, color=RED, anchor="start")
    svg += label(120, 176, "Schema 非法 · 引用断裂 · 空话 then/AC · 占位 ui/defaults · 原料缺失 · 人读/原型漂移", 15, bold=False, anchor="start", color=TEXT)

    svg += f'<rect x="60" y="216" width="1160" height="86" rx="12" fill="#FFFBEB" stroke="{ORANGE}" stroke-width="2" filter="url(#shadow)"/>'
    svg += label(120, 252, "WARN", 20, color=ORANGE, anchor="start")
    svg += label(120, 282, "缺 empty_states · 缺 step_id · legacy cancel_matrix · assumption 待确认", 15, bold=False, anchor="start", color=TEXT)

    svg += f'<rect x="60" y="322" width="1160" height="86" rx="12" fill="#EFF6FF" stroke="{BLUE}" stroke-width="2" filter="url(#shadow)"/>'
    svg += label(120, 358, "Pending", 20, color=BLUE, anchor="start")
    svg += label(120, 388, "五字段 id/missing/impact/owner/status · 挂在 ready 上未闭合 → FAIL", 15, bold=False, anchor="start", color=TEXT)

    svg += footer()
    path = os.path.join(OUT, "gate-layers.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(path)


if __name__ == "__main__":
    flow()
    before_after()
    architecture()
    terminal_mock()
    gate_layers()
