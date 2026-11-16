#!/usr/bin/env python3
"""Build the 48-slide session-01 deck (Linux 0.11 커널 강좌) via LibreOffice UNO.

기준 계획: materials/slide-plans/01-overview.md (48장)
공통 규격: materials/slide-plans/00-common.md — Linux 0.11 배지·푸터, 표준 앞부분
01–04(표지/질문/로드맵/구조도), 본문 상단 10단계 미니 지도.
산출물: output/01-overview.pptx 하나뿐 (CLAUDE.md — PDF/ODP/HTML 만들지 않음).
"""

import argparse
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException


ROOT = Path(__file__).resolve().parents[1]
NAVY, INK, PAPER = 0x102532, 0x183340, 0xF4F1E9
TEAL, ORANGE, MUTED = 0x75D5C5, 0xFFB66B, 0xABC0CB
LINE = 0x2A4653
FONT = "Noto Sans CJK KR"
STAGES = ["질문", "지도", "배경", "코드", "상태도", "비교", "시연", "정답", "확인", "정리"]
TOTAL = 48
SESSION = "01/15"
SLUG = "01-overview"
FOOTER = f"Linux 0.11 커널 강좌 · {SESSION} · {SLUG}"
CAPTURES = ROOT / "materials/01-overview/captures"
FALLBACK = ROOT / "build/boot.png"
# 스테이지 인덱스 (00-common §3)
S_Q, S_MAP, S_BG, S_CODE, S_STATE, S_CMP, S_DEMO, S_ANS, S_QUIZ, S_WRAP = range(10)


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"))


class Deck:
    def __init__(self, doc):
        self.doc = doc
        self.pages = doc.getDrawPages()
        self.count = 0
        first = self.pages.getByIndex(0)
        while first.getCount():
            first.remove(first.getByIndex(0))

    def shape(self, page, x, y, w, h, fill=None):
        shape = self.doc.createInstance("com.sun.star.drawing.RectangleShape")
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
        page.add(shape)
        shape.LineStyle = uno.Enum("com.sun.star.drawing.LineStyle", "NONE")
        shape.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        shape.FillColor = fill if fill is not None else NAVY
        return shape

    def outline(self, page, x, y, w, h, color=MUTED, width=60):
        shape = self.doc.createInstance("com.sun.star.drawing.RectangleShape")
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
        page.add(shape)
        shape.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "NONE")
        shape.LineStyle = uno.Enum("com.sun.star.drawing.LineStyle", "SOLID")
        shape.LineColor = color
        shape.LineWidth = width
        return shape

    def rounded(self, page, x, y, w, h, fill=ORANGE, radius=300):
        shape = self.doc.createInstance("com.sun.star.drawing.CustomShape")
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
        page.add(shape)
        shape.CustomShapeGeometry = uno.Any(
            "[]com.sun.star.beans.PropertyValue", (prop("PresetType", "roundRect"),))
        shape.LineStyle = uno.Enum("com.sun.star.drawing.LineStyle", "NONE")
        shape.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        shape.FillColor = fill
        return shape

    def text(self, page, x, y, w, h, text, size=20, color=PAPER, bold=False, mono=False):
        shape = self.doc.createInstance("com.sun.star.drawing.TextShape")
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
        page.add(shape)
        shape.TextAutoGrowHeight = False
        shape.TextAutoGrowWidth = False
        shape.TextLeftDistance = shape.TextRightDistance = 0
        shape.TextUpperDistance = shape.TextLowerDistance = 0
        shape.setString(text)
        shape.TextVerticalAdjust = uno.Enum("com.sun.star.drawing.TextVerticalAdjust", "TOP")
        cursor = shape.getText().createTextCursor()
        cursor.gotoStart(False)
        cursor.gotoEnd(True)
        cursor.CharFontName = cursor.CharFontNameAsian = (
            "DejaVu Sans Mono" if mono else FONT)
        cursor.CharHeight = cursor.CharHeightAsian = float(size)
        cursor.CharColor = color
        cursor.CharWeight = cursor.CharWeightAsian = 150.0 if bold else 100.0
        return shape

    def slide(self, title, stage=None, note=""):
        page = (self.pages.getByIndex(0) if self.count == 0
                else self.pages.insertNewByIndex(self.pages.getCount()))
        self.count += 1
        page.Width, page.Height = 33867, 19050
        bg = self.doc.createInstance("com.sun.star.drawing.Background")
        bg.FillColor = NAVY
        page.Background = bg
        number = self.pages.getCount()
        page.Name = f"{number:02d} {title}"
        self.text(page, 1100, 400, 22000, 500,
                  "LINUX 0.11 / SOURCE WALKTHROUGH", 11, TEAL)
        self.text(page, 1100, 1150, 31400, 1500, title, 28, PAPER, True)
        if stage is not None:
            self.stage_strip(page, stage, 2950, 750, 13)
        if note:
            self.text(page, 1100, 16850, 29500, 750, note, 10, MUTED)
        self.shape(page, 1100, 17750, 31500, 35, LINE)
        self.text(page, 1100, 18000, 24000, 600, FOOTER, 10, MUTED)
        self.text(page, 30200, 17950, 2400, 650, f"{number:02d} / {TOTAL}", 13, TEAL)
        return page

    def stage_strip(self, page, stage, y=2950, h=750, size=13):
        gap = 250
        w = (31500 - (len(STAGES) - 1) * gap) // len(STAGES)
        for i, label in enumerate(STAGES):
            x = 1100 + i * (w + gap)
            active = i == stage
            self.shape(page, x, y, w, h, ORANGE if active else 0x203D4B)
            self.text(page, x + 160, y + (h - 480) // 2, w - 320, 480,
                      f"{i + 1:02d} {label}", size, INK if active else MUTED, active)

    def cards(self, page, cards, y=4700, h=8500):
        gap, total = 600, 31500
        width = (total - gap * (len(cards) - 1)) // len(cards)
        for i, (title, body) in enumerate(cards):
            x = 1100 + i * (width + gap)
            self.shape(page, x, y, width, h, PAPER)
            self.shape(page, x, y, width, 150, TEAL if i % 2 == 0 else ORANGE)
            self.text(page, x + 550, y + 650, width - 1100, 1600, title, 21, INK, True)
            self.text(page, x + 550, y + 2600, width - 1100, h - 2800, body, 18, INK)

    def banner(self, page, text, y=14800, size=20, color=ORANGE):
        self.text(page, 1400, y, 30500, 1700, text, size, color, True)

    def flow(self, page, items, y=5300, h=3000, title_size=19):
        n = len(items)
        w = (31500 - (n - 1) * 1100) // n
        for i, (title, body) in enumerate(items):
            x = 1100 + i * (w + 1100)
            self.shape(page, x, y, w, h, PAPER)
            self.text(page, x + 300, y + 350, w - 600, 950, title, title_size, INK, True)
            self.text(page, x + 300, y + 1400, w - 600, h - 1450, body, 15, INK)
            if i < n - 1:
                self.text(page, x + w + 150, y + 800, 850, 1000, ">", 28, TEAL, True)

    def code_panel(self, page, path, start, end, x, y, w, h, size=13, caption_extra=""):
        lines = (ROOT / path).read_text().splitlines()
        displayed = []
        limit = min(76, 18000 // int(size * 27.5))
        for i in range(start, end + 1):
            line = lines[i - 1].expandtabs(4)
            line = line.split("!" if path.endswith(".s") else "/*", 1)[0].rstrip()
            shown = f"{i:3}  {line}"
            if len(shown) > limit:
                shown = shown[:limit - 2].rstrip() + " …"
            displayed.append(shown)
        self.shape(page, x, y, w, h, 0x071A24)
        caption = f"{path}:{start}-{end}  / 인라인 주석 생략"
        if caption_extra:
            caption += f"  ·  {caption_extra}"
        self.text(page, x + 350, y + 250, w - 700, 600, caption, 12, TEAL)
        shape = self.text(page, x + 350, y + 1150, w - 700, h - 1450,
                          "\n".join(displayed), size, PAPER, mono=True)
        return shape

    def code(self, page, path, start, end, explanation, size=14, expl_size=19, panel_h=10200):
        self.code_panel(page, path, start, end, 1100, 4400, 19700, panel_h, size)
        self.text(page, 22000, 4700, 10000, 9800, explanation, expl_size)

    def table(self, page, x, y, widths, rows, row_h=1200, size=15):
        for r, row in enumerate(rows):
            head = r == 0
            fill = TEAL if head else (0x183340 if r % 2 else 0x142E3A)
            cx = x
            for c, cell in enumerate(row):
                self.shape(page, cx, y + r * row_h, widths[c], row_h, fill)
                self.text(page, cx + 280, y + r * row_h + (row_h - 850) // 2,
                          widths[c] - 560, 850, cell, size, INK if head else PAPER, head)
                cx += widths[c]

    def picture(self, page, path, x, y, w, h, tag=None):
        iw, ih = png_size(path)
        scale = min(w / iw, h / ih)
        dw, dh = int(iw * scale), int(ih * scale)
        dx, dy = x + (w - dw) // 2, y + (h - dh) // 2
        shape = self.doc.createInstance("com.sun.star.drawing.GraphicObjectShape")
        shape.GraphicURL = Path(path).resolve().as_uri()
        page.add(shape)
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", dx, dy))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", dw, dh))
        self.outline(page, dx, dy, dw, dh, LINE, 90)
        if tag:
            ty = max(3750, dy - 1050)
            self.shape(page, dx + dw - 3200, ty, 3200, 900, ORANGE)
            self.text(page, dx + dw - 3200, ty + 160, 3200, 600, tag, 15, INK, True)
        return shape

    def example_tag(self, page, text="설명용 예시 (실측 아님)"):
        self.rounded(page, 26200, 4200, 6400, 1000, 0x0E2A36, 200)
        self.outline(page, 26200, 4200, 6400, 1000, TEAL, 60)
        self.text(page, 26300, 4430, 6200, 550, text, 13, TEAL, True)


def capture(name):
    target = CAPTURES / name
    if target.exists():
        return target, None
    return FALLBACK, "기존 기록"


def title_slide(d):
    p = d.slide("01. CPU·어셈블리 입문과 부팅부터 셸까지", None,
                "1991년 12월 공개 — 이 강의의 모든 줄 번호와 동작은 Linux 0.11 기준")
    d.shape(p, 27600, 900, 4800, 2100, ORANGE)
    d.text(p, 27850, 1200, 4400, 900, "Linux 0.11", 24, INK, True)
    d.text(p, 27850, 2200, 4400, 600, "1991", 15, INK, True)
    d.text(p, 1100, 4300, 30000, 3900,
           "01. CPU·어셈블리 입문과\n부팅부터 셸까지", 38, PAPER, True)
    d.text(p, 1100, 8300, 30000, 1500, "셸이 나오기 전에 누가 실행되는가?", 28, ORANGE, True)
    d.text(p, 1100, 10000, 30000, 900,
           "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)", 17, MUTED)
    d.text(p, 1100, 11200, 30000, 900, f"{SESSION} · 파트 A «입문·부팅»", 17, TEAL, True)
    d.text(p, 1100, 13000, 30000, 3200,
           "현대 커널 자료와의 혼동을 막는다 — 현대 이야기가 나올 때마다\n"
           "'Linux 0.11에는 없다 / 다르다'고 명시한다.\n"
           "코드 인용 줄 번호는 모두 src/ 원본 기준, 실행 화면은 lab/ 수정본이다.", 18, PAPER)


def question_slide(d):
    p = d.slide("핵심 질문과 오늘의 길", None,
                "오늘은 10단계 전부를 지난다 — 부팅 전체 경로를 1회 통과한다")
    d.text(p, 1100, 4500, 30000, 1500, "셸이 나오기 전에 누가 실행되는가?", 32, ORANGE, True)
    d.text(p, 1100, 6300, 30000, 1000,
           "이 질문 하나로 오늘 120분을 진행한다. 답은 45장에서 다시 만난다.", 18, PAPER)
    d.text(p, 1100, 7900, 30000, 700, "오늘의 길 — 10단계 (전 단계 진행)", 16, TEAL, True)
    gap = 280
    w = (31500 - 9 * gap) // 10
    for i, label in enumerate(STAGES):
        x = 1100 + i * (w + gap)
        d.shape(p, x, 8900, w, 1500, TEAL)
        d.text(p, x + 120, 9060, w - 240, 560, f"{i + 1:02d}", 15, INK, True)
        d.text(p, x + 120, 9680, w - 240, 560, label, 15, INK, True)
    d.text(p, 1100, 11200, 31500, 4200,
           "지도 03–04 (로드맵·구조도) → 배경 05–10 · 14–23 → 코드 28–30 · 35–36 · 38–42\n"
           "상태도 12–13 · 31 → 비교 11 · 15 · 32–34 · 40 → 시연 24–25 · 43–44\n"
           "정답 45 · 47 → 확인 46 → 정리 48 — 매 슬라이드 상단 띠에서 현재 단계를 확인한다.", 16, MUTED)


def roadmap_slide(d):
    p = d.slide("과정 로드맵 — 오늘의 위치", None,
                "첫 회차 — 완료 표시 없음 · 회차가 지날수록 이 지도가 채워진다 (공통 규격 §2)")
    d.text(p, 1100, 3880, 31500, 700,
           "15회차 · 7개 파트 — 오늘은 파트 A «입문·부팅»의 첫 회차", 14, TEAL, True)
    box_w, box_gap, part_gap = 1850, 160, 1300

    def draw_row(parts, y, start_no):
        widths = [n * box_w + (n - 1) * box_gap for _, n in parts]
        total = sum(widths) + part_gap * (len(parts) - 1)
        x = 1100 + (31500 - total) // 2
        no = start_no
        for (label, n), w in zip(parts, widths):
            d.outline(p, x - 220, y - 520, w + 440, 1220 + 520 + 220, LINE, 60)
            d.text(p, x, y - 460, w + 700, 420, label, 12, TEAL, True)
            bx = x
            for _ in range(n):
                if no == 1:
                    d.shape(p, bx, y, box_w, 1200, ORANGE)
                    d.outline(p, bx, y, box_w, 1200, PAPER, 150)
                    d.text(p, bx, y + 160, box_w, 520, f"{no:02d}", 20, INK, True)
                    d.text(p, bx, y + 740, box_w, 380, "오늘", 11, INK, True)
                else:
                    d.outline(p, bx, y, box_w, 1200, MUTED, 60)
                    d.text(p, bx, y + 360, box_w, 520, f"{no:02d}", 18, MUTED)
                bx += box_w + box_gap
                no += 1
            x += w + part_gap
        return x

    draw_row([("A «입문·부팅»", 3), ("B «실행의 길»", 3),
              ("C «메모리»", 2), ("D «프로그램의 일생»", 2)], 5150, 1)
    draw_row([("E «파일·저장»", 2), ("F «터미널»", 1), ("G «종합·실습»", 2)], 8900, 11)
    d.text(p, 1100, 6750, 23000, 1200,
           "셸이 나오기 전에 누가 실행되는가 —\nBIOS부터 셸까지 전체 경로를 한 번에 통과하는 첫 회차", 16, ORANGE, True)
    d.text(p, 1100, 11100, 31500, 3400,
           "01 → 02   오늘: 부팅 전체 경로와 PE·PG·CPL·iret 프레임을 처음 만났다\n"
           "다음 회차 «x86 보호 모드와 소스 읽기 도구» — 선택자 하나가 어떻게 주소가 되는가,\n"
           "보호 모드를 GDB로 확대해 본다", 15, PAPER)
    d.text(p, 15800, 15600, 3600, 600, "■ 완료", 12, TEAL, True)
    d.text(p, 19400, 15600, 3600, 600, "▶ 오늘", 12, ORANGE, True)
    d.text(p, 23000, 15600, 9600, 600, "□ 이후 · Linux 0.11 커널 강좌", 12, MUTED)


def structure_slide(d):
    p = d.slide("커널 전체 구조 — 오늘의 범위", None,
                "오늘 범위 = TEAL · 오늘의 흐름 = ORANGE · 범위 밖 = 실루엣으로 남긴다 (공통 규격 §2)")
    d.outline(p, 1100, 4300, 31500, 1900, LINE, 80)
    d.text(p, 1400, 4420, 9000, 460, "사용자 공간 (CPL=3)", 14, TEAL, True)
    d.text(p, 1400, 4940, 13000, 900, "init · sh — 오늘 경로의 도착점", 18, ORANGE, True)
    d.text(p, 20000, 5030, 12300, 800, "응용 프로그램 (init/main.c 가 fork/exec 로 생성)", 13, MUTED)
    d.text(p, 1100, 6250, 22000, 520,
           "▽  int 0x80 (번호: include/unistd.h) · read()/write() 라이브러리 stub  ▽", 12, MUTED)
    d.text(p, 25600, 6230, 5800, 560, "↑  main → 셸", 14, ORANGE, True)
    d.outline(p, 1100, 6800, 31500, 7000, LINE, 120)
    d.text(p, 1400, 6900, 9000, 460, "커널 공간 (CPL=0)", 14, TEAL, True)
    d.outline(p, 1400, 7400, 30800, 850, MUTED, 50)
    d.text(p, 1650, 7530, 30300, 560,
           "진입: kernel/system_call.s · sys_call_table (include/linux/sys.h)", 13, MUTED)
    subs = [("프로세스 (kernel/)", "sched.c fork.c\nexit.c signal.c"),
            ("메모리 (mm/)", "memory.c\npage.s"),
            ("파일 시스템 (fs/)", "namei.c inode.c\nbuffer.c exec.c"),
            ("블록 장치 (blk_drv/)", "ll_rw_blk.c hd.c\nfloppy.c ramdisk.c"),
            ("문자 장치 (chr_drv/)", "console.c tty_io.c\nkeyboard.S serial.c")]
    w = (30800 - 4 * 350) // 5
    for i, (t, b) in enumerate(subs):
        x = 1400 + i * (w + 350)
        d.outline(p, x, 8450, w, 1900, MUTED, 50)
        d.text(p, x + 250, 8570, w - 500, 440, t, 12, MUTED, True)
        d.text(p, x + 250, 9080, w - 500, 1150, b, 11, MUTED)
    bw, bgap = 4400, 550
    bx = 1400
    for i, (t, sub) in enumerate([("boot/bootsect.s", "부트 섹터"),
                                  ("boot/setup.s", "보호 모드 진입"),
                                  ("boot/head.s", "페이징·main 준비")]):
        d.shape(p, bx, 10650, bw, 1500, TEAL)
        d.text(p, bx + 200, 10780, bw - 400, 500, t, 12, INK, True)
        d.text(p, bx + 200, 11400, bw - 400, 500, sub, 12, INK)
        if i < 2:
            d.text(p, bx + bw + 30, 11000, 520, 600, "→", 22, ORANGE, True)
        bx += bw + bgap
    d.text(p, bx, 11000, 560, 600, "↗", 24, ORANGE, True)
    bx += 640
    d.shape(p, bx, 10650, 4200, 1500, TEAL)
    d.text(p, bx + 200, 10780, 3800, 500, "init/main.c", 13, INK, True)
    d.text(p, bx + 200, 11400, 3800, 500, "main() · init()", 11, INK)
    bx += 4200 + 420
    d.outline(p, bx, 10650, 3900, 1500, TEAL, 90)
    d.text(p, bx + 220, 10780, 3500, 480, "lib/", 13, TEAL, True)
    d.text(p, bx + 220, 11400, 3500, 500, "string.c 등", 12, TEAL)
    d.text(p, 1100, 13860, 31500, 520, "▽  IRQ  ▽", 12, MUTED)
    d.outline(p, 1100, 14400, 31500, 1300, MUTED, 50)
    d.text(p, 1400, 14560, 30800, 900,
           "하드웨어 — 8259A PIC · 8253 타이머(IRQ 0) · 키보드(IRQ 1) · 하드디스크(IRQ 14) · CGA/MDA 화면", 13, MUTED)
    d.text(p, 1100, 15950, 31500, 600,
           "Linux 0.11 · 오늘 01회차는 커널→사용자 두 계층을 모두 지나는 첫 경로다", 13, TEAL)


def populate(d):
    title_slide(d)            # 01
    question_slide(d)         # 02
    roadmap_slide(d)          # 03
    structure_slide(d)        # 04

    p = d.slide("컴퓨터의 네 가지 역할", S_BG,
                "CPU=중앙 처리 장치 / x86=명령 체계 계열, 80386=이번 대상 CPU / 캐시·배선은 생략")
    d.cards(p, [("CPU: 명령 실행", "명령을 읽고 계산한다.\n레지스터: CPU 안의 작은 저장소\n\n메모리에 있는 코드와\n데이터를 사용한다."),
                ("메모리와 디스크", "RAM: 실행 중 코드·데이터\n디스크: 파일의 지속 저장\n\n디스크의 프로그램을\n메모리로 읽어 실행한다."),
                ("입출력 장치", "키보드: 입력\n화면: 출력\n디스크 제어기: 저장 장치 연결\n\n커널이 장치 접근을 관리한다.")])
    d.banner(p, "CPU는 C 소스 파일을 직접 읽지 않는다. 메모리의 기계어 명령을 실행한다.")

    p = d.slide("bit·byte·16진수", S_BG,
                "0x와 #, $는 서로 다른 역할 / 0x는 숫자 진법을 나타내는 표기")
    d.cards(p, [("bit와 byte", "bit: 0 또는 1\nbyte: 8 bits\n\n16비트: 2 bytes\n32비트: 4 bytes"),
                ("16진수 읽기", "한 자리: 0~9, A~F\n0x10 = 십진수 16\n0x17 = 십진수 23\n\n주소·비트 패턴에 편리하다."),
                ("제어 비트", "여러 비트 중 하나가\n기능의 켜짐·꺼짐을 표현한다.\n\n예: PE는 보호 기능\nPG는 페이징 기능")])
    d.banner(p, "32비트라는 말은 모든 명령이 4바이트이거나 RAM이 4GB라는 뜻이 아니다.")

    p = d.slide("주소와 값", S_BG, "단순 byte 주소 예제 / 주소는 위치, 그 위치에 든 내용은 값")
    d.cards(p, [("주소: 저장 위치", "주소 0x1000: 값 7\n주소 0x1001: 값 9\n\n포인터는 위치를 가리킨다.\n주소 자체와 저장된 값을 구분."),
                ("읽기와 쓰기", "읽기: 해당 위치의 값을 가져옴\n쓰기: 해당 위치의 값을 바꿈\n\n메모리 쓰기는 곧\n디스크 파일 저장이 아니다.")], h=7800)
    d.flow(p, [("변경 전", "[0x1000] = 7"), ("쓰기 동작", "주소 0x1000에 12 저장"),
               ("변경 후", "[0x1000] = 12")], y=12900, h=2300)
    d.banner(p, "확인 질문: [0x1000]을 12로 바꾸면 주소도 12가 되는가? — 아니오, 별개다.", y=15500, size=15)

    p = d.slide("다섯 레지스터 이름", S_BG,
                "x86의 이번 수업용 최소 집합 / 레지스터 전체 목록을 암기하지 않는다")
    d.cards(p, [("EAX / AX", "계산·임시 값 등에 사용\nEAX: 32비트\nAX: EAX의 하위 16비트\n\nAX 변경은 EAX 일부 변경"),
                ("EIP / ESP", "EIP: 다음 명령 위치의 기준\nCS와 함께 실행 위치 결정\n\nESP: 스택 꼭대기 위치\nSS와 함께 스택 위치 결정"),
                ("EFLAGS / 제어", "EFLAGS: 상태·제어 비트\nIF: 일반 IRQ 허용 여부\n\nCR0: PE·PG 등 CPU 설정\nCR3: 페이지 변환표 위치")])
    d.banner(p, "C의 변수와 레지스터는 1:1 대응이 아니다. 컴파일러가 배치를 결정한다.")

    p = d.slide("읽기→해석→실행 모델과 jump", S_BG, "실제 CPU 내부 파이프라인을 생략한 순차 실행 모델")
    d.flow(p, [("명령 읽기", "현재 실행 위치의\n기계어를 가져온다."),
               ("명령 해석", "복사·계산·분기 등\n수행할 일을 판단한다."),
               ("명령 실행", "레지스터·메모리 변경\n다음 실행 위치 결정")], h=4000)
    d.text(p, 1400, 10200, 30500, 3300,
           "보통은 다음 명령으로 진행한다.\njump는 다음 위치를 바꾸고, call은 돌아올 위치를 남긴다.\n"
           "CPU는 이 과정을 반복한다. 운영체제도 결국 같은 CPU 명령으로 실행된다.", 22)
    d.banner(p, "상태 = 현재 레지스터 값 + 관련 메모리 내용 + CPU 제어 설정")

    p = d.slide("CPU는 기계어를 실행한다", S_BG, "개념적인 빌드 경로 / 실제 프로젝트의 도구와 세부 단계는 별도 확인")
    d.flow(p, [("C 소스", "사람이 쓰는 함수·변수\n컴파일러가 번역"),
               ("어셈블리", "CPU 명령의 텍스트 표기\n어셈블러가 번역"),
               ("기계어·실행 이미지", "숫자 바이트의 명령\n링크 후 적재·실행")], h=4200)
    d.text(p, 1400, 10300, 30500, 3200,
           ".c: C 소스, .s: 어셈블리 소스, .o: 중간 목적 파일\n"
           "부팅 코드는 C 실행에 필요한 스택·실행 환경을 먼저 준비한다.\n"
           "따라서 일부 시작 코드는 어셈블리로 직접 작성되어 있다.", 22)
    d.banner(p, "어셈블리는 다른 CPU가 아니라, CPU 명령을 사람이 읽기 위한 표기다.")

    p = d.slide("as86과 AT&T 문법", S_CMP, "두 표기는 같은 복사 동작 / 예시는 설명용이며 원본 발췌가 아니다")
    d.cards(p, [("setup.s의 as86 표기", "mov ax,#0x0001\n\nmov: 값을 복사\nax: 목적 레지스터\n#0x0001: 즉시 값 1\n\n순서: 목적지, 원본"),
                ("head.s의 GNU AT&T", "movl $0x00000001,%eax\n\nmovl: 32비트 값 복사\n$1: 즉시 값 1\n%eax: 레지스터 이름\n\n순서: 원본, 목적지")], h=8500)
    d.banner(p, "주의: 피연산자 순서가 반대다. 파일의 문법을 먼저 확인한다.")

    p = d.slide("mov/add가 바꾸는 것 — EAX와 플래그", S_STATE,
                "설명용 AT&T 예제 / 이 예제의 명령 실행은 QEMU에서 측정한 결과가 아니다")
    d.example_tag(p)
    d.flow(p, [("시작", "EAX 값은 미정"), ("movl $1,%eax", "EAX = 1\n메모리 쓰기 없음"),
               ("addl $2,%eax", "EAX = 3\n산술 상태 비트도 변경")], h=4200)
    d.text(p, 1400, 10500, 30500, 3000,
           "mov는 원본을 지우는 이동이 아니라 값을 복사하는 동작이다.\n"
           "$1은 숫자 1이고, 메모리 주소 1에서 읽으라는 뜻이 아니다.\n"
           "일반적인 mov는 산술 플래그를 바꾸지 않고 add는 바꾼다.", 22)
    d.banner(p, "확인 질문: movl $1,%eax 뒤 EAX는 주소일까, 숫자 1일까?")

    p = d.slide("push/pop·call/ret와 ESP", S_STATE,
                "32비트 push/pop 예제 / x86 스택은 낮은 주소 방향으로 자란다")
    d.example_tag(p)
    d.flow(p, [("시작", "ESP = 0x1000"), ("pushl $7", "ESP = 0x0FFC\n[0x0FFC] = 7"),
               ("popl %eax", "EAX = 7\nESP = 0x1000")], h=4200)
    d.text(p, 1400, 10500, 30500, 3000,
           "pushl: ESP를 4 줄인 뒤 저장. popl: 읽고 4 증가.\n"
           "call: 돌아올 명령 위치를 스택에 남기고 이동. ret: 그 위치로 돌아간다.\n"
           "pop을 해도 메모리 값이 지워지지는 않는다.", 22)
    d.banner(p, "이후 iret는 실행 위치뿐 아니라 권한 복귀에 필요한 상태도 복원한다.")

    p = d.slide("왜 보호가 필요한가", S_BG, "보호의 목적을 먼저 이해한 뒤 x86 구현 용어를 도입한다")
    d.cards(p, [("사용자 프로그램", "셸·편집기·일반 명령\n실수나 오류가 생길 수 있다.\n\n다른 프로그램의 메모리나\n장치를 마음대로 바꾸면 위험"),
                ("커널", "메모리·CPU·장치를 관리\n요청을 검사하고 처리한다.\n\n사용자는 시스템 콜이라는\n정해진 경로로 서비스를 요청")])
    d.banner(p, "역할 분담만으로는 부족하다. CPU가 접근 권한을 검사해야 한다.")

    p = d.slide("실주소 모드 vs 보호 모드", S_CMP,
                "보호 모드와 사용자 권한은 다른 분류 / 보호 모드가 모든 오류를 자동 방지하지는 않음")
    d.cards(p, [("실주소 모드", "초기 PC와의 호환 환경\n세그먼트×16 + 오프셋으로\n주소를 만드는 기본 모델\n\n보호 모드식 권한 분리 없음"),
                ("보호 모드", "세그먼트 설명표 참조\n주소 범위·접근 권한 검사\n권한 수준으로 동작 구분\n\n페이징은 별도로 켤 수 있음")])
    d.banner(p, "실주소 모드를 '아무 한계가 없는 모드'라고 부르지 않는다.\nLinux 0.11의 커널과 사용자 프로그램은 둘 다 보호 모드에서 실행한다.")

    p = d.slide("선택자와 GDT/LDT/IDT", S_BG,
                "GDT = Global Descriptor Table / LDT·IDT 상세는 다음 회차에서 확대")
    d.flow(p, [("CS의 선택자", "예: 8 = 0x0008\n메모리 주소 자체가 아님"),
               ("GDT의 항목", "시작 주소·범위·권한\n코드/데이터 등 기록"),
               ("주소와 검사", "시작 주소 + 오프셋\n범위·권한을 검사")], h=4300)
    d.text(p, 1400, 10600, 30500, 3000,
           "CS: 코드 세그먼트 선택자, DS: 데이터, SS: 스택에 사용한다.\n"
           "GDT는 전역 세그먼트 설명표, LDT는 태스크별 설명표,\n"
           "IDT는 인터럽트·예외 진입 정보의 표다 — 오늘은 한 줄 소개로 끝낸다.", 21)
    d.banner(p, "선택자는 주소가 아니라 설명표 항목을 찾는 값이다.")

    p = d.slide("선형 주소와 물리 주소", S_BG, "설명용 매핑 예제 / 실제 0.11 초기 매핑과 구분한다")
    d.flow(p, [("프로그램의 위치", "세그먼트 규칙 적용\n선형 주소 0x2000"),
               ("페이지 변환표", "0x2000을 포함한 페이지\n→ 물리 페이지 0x9000"),
               ("실제 RAM 위치", "물리 주소 0x9000\n이 위치의 데이터 사용")], h=4300)
    d.text(p, 1400, 10600, 30500, 3000,
           "페이징 꺼짐: 선형 주소를 페이지 표로 변환하지 않는다.\n"
           "페이징 켜짐: 페이지 디렉터리·테이블을 거쳐 물리 주소를 구한다.\n"
           "0.11의 초기 설정은 0~16 MiB의 선형·물리 주소를 같게 매핑한다(identity).", 21)
    d.banner(p, "CR3는 변환표의 시작 위치, CR0.PG는 변환 기능을 켜는 비트다. 4 KiB 페이지는 7회차에서 확대.")

    p = d.slide("이벤트 세 가지", S_BG, "이번 경로에서 구분할 사건 / IDT의 구체 형식과 예외 분류는 4회차")
    d.cards(p, [("하드웨어 인터럽트", "타이머·키보드 등 장치 신호\n현재 명령 흐름과 별개로 발생\n\nIRQ: 장치의 인터럽트 요청\nIF로 일반 IRQ 허용 제어"),
                ("예외", "명령 실행 중 CPU가 감지\n예: 0으로 나눔·페이지 폴트\n\n페이지 폴트는\n항상 프로그램 버그는 아님"),
                ("시스템 콜", "프로그램이 의도적으로 요청\n예: 파일 읽기·프로세스 생성\n\n0.11에서는 int $0x80 사용\n정해진 커널 경로로 진입")])
    d.banner(p, "'인터럽트는 모두 장치에서 온다'고 말하지 않는다 — 시스템 콜도 소프트웨어 인터럽트로 진입한다.")

    p = d.slide("문맥과 iret", S_BG, "iret = interrupt return / 초기 사용자 문맥 진입에도 복원 형식을 활용")
    d.flow(p, [("복원할 정보 준비", "EIP·CS: 코드 위치\nEFLAGS: 상태 비트"),
               ("권한도 바뀐다면", "ESP·SS: 사용자 스택\n추가 정보도 준비"),
               ("iret 실행", "저장된 실행 상태 복원\n해당 권한·위치로 진행")], h=4300)
    d.text(p, 1400, 10600, 30500, 3000,
           "일반 ret와 달리 iret는 실행 상태와 권한 복귀 규칙을 처리한다.\n"
           "처음 사용자 영역으로 갈 때도 '복귀할 상태'를 인위적으로 만들어 사용한다.\n"
           "범용 레지스터 모두를 iret 한 명령이 자동 복원하는 것은 아니다.", 21)
    d.banner(p, "문맥은 실행 위치·스택·상태다 — 소스 파일 이름이 아니다.")

    p = d.slide("PE·PG·IF·CPL 참조표", S_BG, "이후 원본 코드 옆에 다시 찾아볼 참조표 / 서로 다른 축인지 확인한다")
    d.cards(p, [("CR0.PE / CR0.PG", "CR0: CPU 제어 레지스터\nPE=0: 실주소 모드\nPE=1: 보호 환경\n\nPG=0: 페이징 안 함\nPG=1: 페이징 사용"),
                ("CPL / EFLAGS.IF", "CPL: 현재 권한 수준 0~3\n0: 커널 / 3: 사용자 주 경로\n\nIF=0: 일반 IRQ 억제\nIF=1: 일반 IRQ 허용\nNMI·예외는 별도")], h=8500)
    d.banner(p, "보호 모드 진입, 사용자 권한 진입, 페이징 활성화는 서로 다른 상태 변화다.")

    p = d.slide("호스트·QEMU(TCG)·게스트", S_BG, "실행 환경의 층을 구분한다 / QEMU는 게스트 커널 자체가 아니다")
    d.cards(p, [("호스트", "강사의 PC 운영체제\n터미널과 편집기\nQEMU 프로세스 실행"),
                ("가상 하드웨어", "QEMU TCG\nx86 CPU·메모리\n플로피·IDE·화면"),
                ("게스트", "Linux 0.11 커널\n루트 파일 시스템\n/bin/sh와 명령")])
    d.banner(p, "현대 호스트 커널과 Linux 0.11을 혼동하지 않는다.\n현대 호스트 위에서도 게스트가 실행하는 코드는 Linux 0.11이다.")

    p = d.slide("src·lab·build", S_BG, "build/source-changes.patch 및 build/UPSTREAM.md로 수정 이력 확인")
    d.cards(p, [("src/  원본", "boot/    부팅\ninit/      초기화\nkernel/ 태스크·진입\nmm/     메모리\nfs/        파일 시스템"),
                ("lab/  실행 수정본", "현대 빌드 환경 대응\nImage: 부팅 이미지\nhdc-0.11.img: 루트 디스크\n수정·재빌드 대상"),
                ("scripts/ · build/", "run.sh: QEMU 실행\nbuild.sh: Docker 빌드\ndebug.sh: 디버깅 준비\nbuild/: 차이와 기존 기록")])
    d.banner(p, "해설은 src/ 기준, 시연은 lab/ 기준. 차이를 숨기지 않는다.")

    p = d.slide("전체 제어 흐름 지도", S_MAP,
                "호출·제어 이전의 개략도 / 상태 변화는 31장의 별도 그림에서 설명")
    d.flow(p, [("bootsect.s", "setup·system 적재"), ("setup.s", "하드웨어 준비\n보호 모드 진입"),
               ("head.s", "초기 테이블\n페이징·main 진입"), ("main.c", "커널 초기화\ninit·셸 생성")], h=3800)
    d.text(p, 1500, 10200, 30000, 3500,
           "이후 명령 실행은 일방향 부팅 흐름과 다르다.\n"
           "사용자 프로그램은 시스템 콜로 커널에 들어가고, 처리 후 복귀한다.\n"
           "이 지도의 각 상자는 뒤 코드 슬라이드(28–42)와 색 대응된다.", 22)
    d.banner(p, "지도 읽기 질문: 지금 누가 실행 중이며, 다음 단계의 준비 조건은 무엇인가?")

    p = d.slide("시연 A — QEMU 부팅부터 셸까지", S_DEMO,
                "상세 절차: materials/01-overview/demo.md / GDB는 02회차부터 — 이번 회차 없음")
    d.cards(p, [("호스트 터미널", "qemu-system-i386 --version\nbash scripts/run.sh\n\nTCG · RAM 16 MiB\n플로피 부팅 · IDE 루트\n네트워크 없음 · snapshot"),
                ("게스트 셸", "echo boot-ok\nls /\n\n명령 반환과 디렉터리 확인\n관찰한 것만 성공으로 기록")], h=7800)
    d.text(p, 1400, 13000, 30500, 2600,
           "관찰: BIOS 메시지 → \"Loading system ...\" → 버퍼/메모리 출력 → # 프롬프트\n"
           "run.sh 설정은 암기 대상이 아니다. 게스트 exit은 셸 재생성될 뿐 QEMU 종료가 아니다(종료는 창 닫기).", 16)
    d.banner(p, "셸 화면만으로 PE·PG·CPL 값이나 모든 장치 동작을 검증한 것이 아님을 명시한다.")

    path, tag = capture("01-qemu-boot.png")                    # 25
    p = d.slide("부팅·echo/ls 캡처", S_DEMO,
                "계획: materials/01-overview/captures/01-qemu-boot.png · 02-echo-ls.png — 미확보 시 build/boot.png")
    d.picture(p, path, 1100, 4300, 19000, 11500, tag=tag)
    d.text(p, 21800, 4500, 10800, 800, "기대 출력", 18, TEAL, True)
    d.text(p, 21800, 5400, 10800, 5200,
           "Loading system ...\nNNN buffers = NNN bytes buffer space\nFree mem: ... bytes\n\n# 프롬프트\n# echo boot-ok\nboot-ok\n# ls /", 15, PAPER, mono=True)
    d.text(p, 21800, 11000, 10800, 4800,
           "각주: lab/ 빌드(yuan-xy 기반 수정본) ·\nQEMU i386 TCG · 수정 없음 · 캡처 날짜\n\n화면·문자열은 루트 이미지에 따라 다르다.", 13, MUTED)
    d.banner(p, "화면은 lab/ 수정본에서 얻었고, 슬라이드의 코드 줄 번호는 src/ 원본 기준이다.", y=15600, size=15)

    p = d.slide("legacy BIOS와 부트 섹터", S_BG,
                "이 프로젝트의 legacy BIOS 부팅 기준 / UEFI 일반 강의로 범위를 확장하지 않는다")
    d.flow(p, [("전원·리셋", "CPU가 정해진 위치에서\n펌웨어 실행 시작"),
               ("BIOS", "하드웨어 초기 준비\n부트 섹터를 RAM에 적재"),
               ("부트 섹터", "작은 시작 코드 실행\n나머지 커널 코드를 적재")], h=4300)
    d.text(p, 1400, 10500, 30500, 3000,
           "BIOS는 커널이 아니라 PC 펌웨어다 — 커널 이전에 실행된다.\n"
           "부트 섹터는 디스크에서 읽는 시작 영역이며, 전통적인 크기는 512바이트다.\n"
           "작은 부트 코드가 더 큰 커널 코드를 읽는 단계적 구성이 필요하다.", 22)
    d.banner(p, "QEMU는 이 부팅에 필요한 가상 PC와 펌웨어 실행 환경을 제공한다.")

    p = d.slide("bootsect·setup·head의 책임", S_BG,
                "src/boot/bootsect.s · setup.s · head.s / 오늘은 단계별 책임에 집중")
    d.cards(p, [("1  bootsect.s", "BIOS가 부트 섹터 실행\n자기 코드 이동\nsetup과 system 읽기\nsetup으로 제어 이전"),
                ("2  setup.s", "BIOS 정보 수집\n커널 위치 정리\nGDT·A20·PIC 준비\n보호 모드로 진입"),
                ("3  head.s", "32비트 코드 실행\nGDT·IDT 설정\n초기 페이지 테이블\nmain()으로 제어 이전")])
    d.banner(p, "A20은 주소선 호환 처리, PIC는 장치 인터럽트 제어기 — 오늘은 용어 풀이만.")

    p = d.slide("setup.s 3줄 — 보호 모드 진입", S_CODE,
                "캡션 줄 번호는 src/ 원본 기준 / 기존 자료의 186-193 인용을 191-193으로 정정")
    d.code(p, "src/boot/setup.s", 191, 193,
           "① mov ax,#0x0001\n준비: AX에 PE 비트 값 1\n\n② lmsw ax\nCR0 하위 비트 반영 — PE=1\n\n③ jmpi 0,8\n선택자 8·오프셋 0으로\nCS까지 바꿔 이동\n\n보호 모드 진입 =\n비트 설정 + 문맥 교체",
           expl_size=15, panel_h=4000)
    d.banner(p, "보호 모드 자체가 항상 32비트 코드를 뜻하지는 않는다 — 여기서는 32비트 항목으로 이동한다.")

    p = d.slide("3줄 상태 추적", S_CODE, "각 줄을 읽고 변경된 상태를 묻는다 — 안 바뀌는 것도 함께 짚는다")
    d.table(p, 1100, 4500, [6400, 6600, 10000, 8500], [
        ["명령 (setup.s:191-193)", "바뀌는 것", "바뀐 뒤 상태", "안 바뀌는 것"],
        ["mov ax,#0x0001", "AX = 1", "PE=0 · 실주소 모드 그대로", "CPU 모드·메모리"],
        ["lmsw ax", "CR0.PE: 0 → 1", "보호 모드 진입 · CPL=0", "코드 위치(다음 명령)·PG=0"],
        ["jmpi 0,8", "CS 선택자=8 · EIP=0", "head.s의 32비트 코드 실행", "PE=1·권한(CPL 0) 유지"],
    ], row_h=1900)
    d.banner(p, "질문: 세 줄 사이 CPU는 무엇을 잊지 않는가? — EIP는 항상 다음 명령을 가리킨다.", y=13000)

    p = d.slide("setup_paging과 main 진입 준비 — 심화", S_CODE,
                "페이지를 만든 뒤(head.s) 그 위에서 main()이 시작된다 · 심화 — 이해가 늦어지면 강사용 참조로.")
    d.code_panel(p, "src/boot/head.s", 198, 218, 1100, 4300, 15200, 12000, size=10)
    d.code_panel(p, "src/boot/head.s", 135, 144, 17200, 4300, 15400, 6600, size=11)
    d.text(p, 17200, 11300, 15400, 4800,
           "CR3 = 0 (페이지 디렉터리 = pg_dir)\nCR0.PG: 0 → 1 (orl $0x80000000)\n"
           "ret — after_page_tables 가 쌓아 둔\n_main 주소로 복귀 = main() 진입\n\n"
           "xorl %eax,%eax — 두 피연산자가 같아 EAX=0", 15, PAPER)

    p = d.slide("부팅 단계별 상태 변화도", S_STATE,
                "IF는 표시한 지점의 값 — 전체 부팅 구간 값이 아니다 / 전환 원인은 각 명령")
    d.table(p, 1100, 4300, [7300, 1500, 1500, 1500, 1500, 18200], [
        ["단계 · 전환 원인", "PE", "PG", "CPL", "IF", "변경 데이터"],
        ["BIOS 시작 (펌웨어)", "0", "0", "—", "1", "—"],
        ["setup: cli", "0", "0", "—", "0", "EFLAGS.IF → 0"],
        ["setup.s:192  lmsw ax", "1", "0", "0", "0", "CR0.PE → 1 (보호 모드)"],
        ["head.s:218  movl %eax,%cr0", "1", "1", "0", "0", "CR0.PG → 1 · CR3 = pg_dir"],
        ["main.c:136  sti()", "1", "1", "0", "1", "EFLAGS.IF → 1"],
        ["system.h:1-14  move_to_user_mode()", "1", "1", "3", "1", "CS·SS 선택자 → 사용자"],
    ], row_h=1450, size=14)
    d.banner(p, "CPU 모드 ≠ 권한 수준 ≠ 페이징 상태 ≠ 인터럽트 허용 — 네 축을 섞지 않는다.", y=15200, size=16)

    p = d.slide("80386 모드 비교", S_CMP,
                "현대 x86-64 long mode·SMM은 80386 범위 밖 / 세 가지 선택지를 빠짐없이 소개한다")
    d.cards(p, [("Real-Address", "PE=0\n초기 부팅 경로에서 사용\n실주소 방식의 실행 환경\n\n보호 모드 진입 전 단계"),
                ("Protected", "PE=1, VM=0\n보호·권한 검사와 테이블\n선택적으로 페이징 사용\n\nLinux 0.11 주 실행 환경"),
                ("Virtual-8086", "PE=1, EFLAGS.VM=1\n보호 환경에서 8086 실행\n주로 CPL 3 수준의 제약\n\n오늘의 부팅 경로는 미사용")])
    d.banner(p, "실제 경로: Real → Protected. 사용자 프로그램도 Protected에서 실행한다.")

    p = d.slide("CPL 0–3 비교", S_CMP, "CPL 0~3 모두 비교한다 — 1·2도 존재하지만 0.11의 주 경로는 0/3이다")
    d.cards(p, [("Ring 0", "커널 코드\n높은 권한"), ("Ring 1", "중간 권한\n주 경로 미사용"),
                ("Ring 2", "중간 권한\n주 경로 미사용"), ("Ring 3", "사용자 코드\n제한된 권한")], h=5000)
    d.text(p, 1400, 10400, 30500, 3300,
           "Ring 3 → Ring 0: 시스템 콜·인터럽트·예외의 진입 경로\n"
           "Ring 0 → Ring 3: 저장된 문맥으로 복귀하거나 초기 사용자 문맥을 구성\n"
           "사용자 권한(CPL 3)은 real mode가 아니다 — 보호 모드 안의 권한 수준이다.", 22)
    d.banner(p, "'모드 전환'이라는 말만 쓰지 말고, 어떤 축이 바뀌는지 명시한다.")

    p = d.slide("PG·IF 비교", S_CMP, "보호 모드에서의 PG 비교 / IF는 마스크 가능한 하드웨어 인터럽트에 관한 비트")
    d.cards(p, [("페이징: CR0.PG", "0: 페이지 변환 미사용\n1: 페이지 테이블로 변환\n\n부팅 중 0 → 1\n사용자 실행 중에도 1 유지"),
                ("인터럽트: EFLAGS.IF", "0: 마스크 가능한 IRQ 억제\n1: 해당 IRQ 허용\n\ncli로 0, sti로 1\n예외·NMI까지 차단하지 않음")])
    d.banner(p, "네 조합의 의미는 서로 독립적이다. PG=1이 곧 IF=1을 뜻하지 않고, IF=1이 모든 IRQ의 무조건 전달을 보장하지도 않다(PIC 마스크 등).")

    p = d.slide("main()의 초기화와 sti", S_CODE,
                "src/init/main.c:126-137 / 호출 순서는 원본 소스에서 직접 추출")
    d.code(p, "src/init/main.c", 126, 137,
           "메모리 관리 준비 — mem_init\n\n예외·장치·터미널 준비 —\ntrap_init · blk_dev_init\nchr_dev_init · tty_init\n\n시간·스케줄러 —\ntime_init · sched_init\n\n버퍼·디스크 —\nbuffer_init · hd_init · floppy_init\n\nsti() — 일반 IRQ 허용 (IF 0→1)\nmove_to_user_mode() — 다음 장", expl_size=16, panel_h=9900)
    d.banner(p, "모든 함수 내부를 읽지 않는다 — 범주로 묶어 '무엇을 준비했는지' 본다.")

    p = d.slide("move_to_user_mode — iret 프레임 — 심화", S_CODE,
                "src/include/asm/system.h:1-14 / 심화 — 같은 태스크의 권한 변화다")
    d.code(p, "src/include/asm/system.h", 1, 14,
           "iret 프레임 (push 순서)\n\n$0x17 — 사용자 SS\n%eax — 사용자 ESP\npushfl — EFLAGS\n$0x0f — 사용자 CS\n$1f — 사용자 EIP\n\niret → CPL 0 → 3\n이후 movw $0x17 로\nDS/ES/FS/GS 교체", size=12, expl_size=17, panel_h=9900)
    d.banner(p, "새 프로세스 생성이 아니라 같은 task의 권한 변경 — fork가 아니다.")

    p = d.slide("프로그램·프로세스·PID", S_BG,
                "0.11에서는 task라는 표현도 사용 / 프로세스 내부 구조는 5~6회차에서 확대")
    d.cards(p, [("프로그램", "디스크의 실행 파일\n예: /bin/sh\n\n같은 파일을 여러 번\n실행할 수 있다."),
                ("프로세스 / PID", "실행 중인 프로그램의 단위\n메모리·실행 상태를 보유\nPID: 프로세스 식별 번호\n\n부모와 자식은 별개 프로세스"),
                ("세 가지 연산", "fork: 자식 프로세스 생성\nexec: 프로그램 이미지 교체\nwait: 자식 종료 상태 회수\n\nCPU 모드 전환과는 다름")])
    d.banner(p, "셸도 사용자 프로그램이다. 커널 자체가 명령 문자열을 해석하는 것은 아니다.")

    p = d.slide("첫 fork와 task 0의 pause 루프", S_CODE,
                "src/init/main.c:138-148 / 원본은 첫 fork 성공을 가정한다")
    d.code(p, "src/init/main.c", 138, 148,
           "fork() 반환값\n\n> 0  부모(task 0)\n→ for(;;) pause();\n\n= 0  자식\n→ init()\n\n< 0  실패 — 복구하지 않음\n\nmain.c:138 주석:\n\"we count on this going ok\"", size=12, expl_size=16, panel_h=9300)
    d.banner(p, "task 0의 pause()는 죽지 않는 대기 루프 — 스케줄러와의 관계는 5회차.")

    p = d.slide("init — rc 자식과 셸 재생성", S_CODE,
                "전체는 src/init/main.c:168-209 — 여기서는 루프 부분 발췌")
    d.code_panel(p, "src/init/main.c", 178, 187, 1100, 4400, 15200, 7800, size=12,
                 caption_extra="rc 자식")
    d.code_panel(p, "src/init/main.c", 188, 199, 17200, 4400, 15400, 7800, size=12,
                 caption_extra="대화형 셸 자식")
    d.text(p, 1100, 12300, 31500, 600,
           "왼쪽: rc 자식이 /etc/rc 실행 뒤 종료 · 오른쪽: 대화형 셸 자식 — fork → exec /bin/sh",
           13, TEAL, True)
    d.flow(p, [("init (PID 1)", "살아서 wait"), ("rc 자식", "/etc/rc 실행 뒤 종료"),
               ("셸 자식", "fork → exec /bin/sh"), ("wait → 회수", "종료 확인 → 새 셸 fork")], y=13100, h=2400)
    d.banner(p, "task 0과 PID 1은 별개 흐름이다 — init 자신은 셸로 교체되지 않는다.", y=15800, size=14)

    p = d.slide("fd와 open 접근 모드", S_CMP,
                "fd = file descriptor / tty는 터미널 장치 / 나머지 open 플래그는 12회차 범위")
    d.code_panel(p, "src/include/fcntl.h", 7, 10, 1100, 4400, 12200, 3200, size=14)
    d.table(p, 14200, 4400, [1700, 5300, 8500], [
        ["fd", "연결 (관례)", "init의 연결 (main.c:172-175)"],
        ["0", "표준 입력", "open(\"/dev/tty0\",O_RDWR,0)"],
        ["1", "표준 출력", "dup(0)"],
        ["2", "표준 오류", "dup(0)"],
    ], row_h=800, size=14)
    d.table(p, 1100, 8300, [4800, 2200, 8200, 16300], [
        ["접근 모드 (fcntl.h)", "값", "의미", "등장 예"],
        ["O_RDONLY", "00", "읽기 전용", "open(\"/etc/rc\",O_RDONLY,0) — init의 rc 자식"],
        ["O_WRONLY", "01", "쓰기 전용", "— (오늘 경로에서는 등장하지 않음)"],
        ["O_RDWR", "02", "읽기·쓰기", "open(\"/dev/tty0\",O_RDWR,0) — init·셸의 tty 연결"],
    ], row_h=1500)
    d.banner(p, "dup는 파일 내용이 아니라 fd 번호를 복제한다. 번호 0/1/2 자체가 장치는 아니다.")

    p = d.slide("init의 tty 연결 — open/dup", S_CODE,
                "src/init/main.c:172-175 / fd와 wait는 뒤 회차에서 확대")
    d.code(p, "src/init/main.c", 172, 175,
           "setup() — 디스크·루트 준비\n(앞 줄 171)\n\nopen(\"/dev/tty0\",O_RDWR,0)\n— tty를 fd 0에 연결\n\ndup(0) ×2 — fd 1, 2도\n같은 열린 파일로\n\nfd 0부터 순서 할당은\n이 초기 '전부 성공' 경로의\n조건이다", expl_size=16, panel_h=4400)
    d.banner(p, "실패하면 (void)로 무시된다 — 뒤의 출력이 안 나올 뿐, 여기서 멈추지 않는다.")

    p = d.slide("exec — PID 유지·이미지 교체", S_CODE,
                "src/init/main.c:194-200 / 성공은 이전 코드로 복귀하지 않는다")
    d.code(p, "src/init/main.c", 194, 200,
           "before — 셸용 자식\ninit이 fork한 자식\ninit의 코드·주소 공간\n\n↓ execve(\"/bin/sh\",\nargv,envp)\n\nafter — /bin/sh\n같은 PID, 새 이미지\n\n성공: 새 진입점에서 실행\n실패: _exit() 로 종료", expl_size=16, panel_h=6500)
    d.banner(p, "fork(생성)와 exec(이미지 교체)를 하나의 함수·하나의 상태 변화로 설명하지 않는다.")

    p = d.slide("시연 B — 셸 명령 짧은 시연", S_DEMO,
                "게스트 명령 실행은 관찰 / 구체적인 시스템 콜 목록은 이 시연에서 측정하지 않음")
    d.flow(p, [("셸 입력", "cd (내장 명령)\nls (외부 명령)"), ("사용자 실행", "내장 명령 또는\n외부 프로그램"),
               ("커널 서비스", "요청에 따라\n파일·터미널·태스크"), ("화면 결과", "출력과 명령 반환\n다음 프롬프트")], h=3900)
    d.text(p, 1400, 9700, 30500, 3800,
           "관찰 대상은 결과 화면뿐이다 — fork/exec 여부는 소스 추론임을 명시한다.\n"
           "23장 전체 지도와 결과를 약 3분간 연결한다.\n"
           "모든 명령이 fork/exec를 수행한다고 가정하지 않는다 — 내장 명령은 다르다.", 20)
    d.banner(p, "이 화면은 사용자 프로그램이 동작한다는 증거이지, CPU 제어 비트나 모든 커널 기능을 검증한 결과는 아니다.")

    path, tag = capture("03-shell-commands.png")               # 44
    p = d.slide("셸 명령 캡처와 관찰 vs 추론", S_DEMO,
                "계획: materials/01-overview/captures/03-shell-commands.png — 미확보 시 build/boot.png")
    d.picture(p, path, 1100, 4300, 17600, 11400, tag=tag)
    rx, rw = 19600, 13000
    d.shape(p, rx, 4300, rw, 5400, PAPER)
    d.shape(p, rx, 4300, rw, 150, TEAL)
    d.text(p, rx + 500, 4900, rw - 1000, 900, "관찰 (화면)", 20, INK, True)
    d.text(p, rx + 500, 6000, rw - 1000, 3400,
           "명령 반환\n디렉터리 목록\n프롬프트 재등장\n\n— 이 화면이 증거", 17, INK)
    d.shape(p, rx, 10000, rw, 5400, PAPER)
    d.shape(p, rx, 10000, rw, 150, ORANGE)
    d.text(p, rx + 500, 10600, rw - 1000, 900, "추론 (소스)", 20, INK, True)
    d.text(p, rx + 500, 11700, rw - 1000, 3400,
           "fork·exec 동작\n내장/외부 명령 차이\n\n— 소스 기반 해석이지\n화면 증거가 아니다", 17, INK)
    d.text(p, 1100, 15900, 30500, 700,
           "각주: lab/ 빌드(yuan-xy 기반 수정본) · QEMU i386 TCG · 수정 없음 · 캡처 날짜", 13, MUTED)

    p = d.slide("핵심 질문의 답", S_ANS,
                "질문 재게시 — 학습 목표 4의 경로 문장으로 답한다")
    d.text(p, 1100, 4200, 30000, 900, "셸이 나오기 전에 누가 실행되는가?", 22, ORANGE, True)
    d.flow(p, [("BIOS", "펌웨어"), ("bootsect", "512B 시작 코드"), ("setup", "보호 모드 진입"),
               ("head", "페이징·main 준비"), ("main→task0", "초기화 뒤 pause"),
               ("init→셸", "fork·exec /bin/sh")], y=5300, h=3100, title_size=16)
    d.text(p, 1100, 9000, 31500, 1100,
           "BIOS → bootsect → setup → head → main() → task 0/init → 셸", 24, PAPER, True)
    d.text(p, 1100, 10500, 31500, 4200,
           "BIOS — 커널 이전 펌웨어\n부트 3단 — bootsect(적재) · setup(보호 모드) · head(페이징·main 준비)\n"
           "main() — 초기화·sti 뒤 move_to_user_mode, 첫 fork\n"
           "task 0 — for(;;) pause() · init — rc 자식과 대화형 셸 생성\n셸 — init 자식에서 exec된 /bin/sh", 16, MUTED)
    d.banner(p, "같은 질문을 02회차부터는 더 작은 단위(선택자·GDT·GDB 관찰)로 다시 묻는다.", y=15200, size=15)

    p = d.slide("이해 확인 질문 — 8문항", S_QUIZ,
                "정답은 다음 장 / 강의 중 확인 질문은 본문 07·13·29장에 배치했다")
    d.table(p, 1100, 4300, [2600, 28900], [
        ["번호", "문항"],
        ["1", "CPU가 직접 실행하는 것은?"],
        ["2", "[0x1000]의 값을 12로 바꾸면 주소도 바뀌는가?"],
        ["3", "as86 mov ax,#1 과 AT&T movl $1,%eax 의 차이는?"],
        ["4", "사용자 프로그램은 어느 CPU 모드에서 실행되는가?"],
        ["5", "첫 fork의 부모(task 0)는 무엇을 하는가?"],
        ["6", "셸은 누가 실행하는가?"],
        ["7", "exec 뒤 PID는?"],
        ["8", "셸이 종료되면 누가 회수하는가?"],
    ], row_h=1300, size=16)

    p = d.slide("이해 확인 정답", S_ANS, "8문항 — 질문(46장)과 대응한다")
    d.table(p, 1100, 4300, [9500, 22000], [
        ["문항 요지", "정답"],
        ["CPU가 직접 실행하는 것", "기계어 — C 문자열이 아니다"],
        ["[0x1000] 값 변경과 주소", "별개 — 주소는 위치, 값은 내용"],
        ["두 어셈블리 문법", "피연산자 순서가 반대 (목적지,원본 / 원본,목적지)"],
        ["사용자 프로그램의 CPU 모드", "보호 모드 (CPL 3) — real mode가 아니다"],
        ["첫 fork의 부모", "task 0: for(;;) pause(); 루프 (main.c:148)"],
        ["셸을 실행하는 주체", "init이 fork한 자식에서 execve(\"/bin/sh\") (main.c:194-200)"],
        ["exec 뒤 PID", "유지 — 주소 공간·실행 이미지만 교체"],
        ["셸 종료의 회수", "init의 wait 루프 (main.c:202-206) → 새 셸 fork"],
    ], row_h=1300, size=14)

    p = d.slide("정리·다음 회차 예고", S_WRAP,
                "02회차 «x86 보호 모드와 소스 읽기 도구» — GDB로 커널을 멈춰 본다")
    d.flow(p, [("BOOT", "적재·보호 모드\n페이징"), ("MAIN", "자원·장치 초기화\n사용자 권한 전환"),
               ("INIT", "tty·rc 준비\nfork·exec·wait"), ("SHELL", "사용자 명령\n커널 진입과 복귀")], y=4300, h=3100)
    d.text(p, 1100, 7900, 30500, 3200,
           "기억할 세 가지\n"
           "1. 현재 실행 위치와 권한을 함께 말한다.\n"
           "2. 호출 흐름과 상태 변화를 구분한다.\n"
           "3. 원본 소스(src/)와 실행 수정본(lab/)를 구분한다.", 18)
    d.outline(p, 1100, 11400, 31500, 4200, ORANGE, 120)
    d.text(p, 1500, 11700, 30600, 3400,
           "다음 02회차 «x86 보호 모드와 소스 읽기 도구»\n"
           "오늘 처음 만난 선택자·GDT·iret 프레임을 확대하고, GDB로 커널을 멈춰 무엇이 보이는지 본다\n"
           "01 → 02 · Linux 0.11 커널 강좌", 17, PAPER)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nucleus-slides-") as temp:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen([
            "libreoffice", "--headless", "--nologo", "--nodefault", "--norestore",
            f"-env:UserInstallation={Path(temp).as_uri()}",
            f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
        ], stdout=subprocess.DEVNULL)
        doc = None
        desktop = None
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", local)
            for _ in range(120):
                try:
                    ctx = resolver.resolve(
                        f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
                    break
                except NoConnectException:
                    if process.poll() is not None:
                        raise RuntimeError("LibreOffice exited before connection")
                    time.sleep(0.25)
            else:
                raise RuntimeError("LibreOffice connection timed out")
            desktop = ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", ctx)
            doc = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0,
                                               (prop("Hidden", True),))
            deck = Deck(doc)
            populate(deck)
            target = (args.output_dir / f"{SLUG}.pptx").resolve()
            doc.storeToURL(target.as_uri(), (prop("FilterName", "Impress MS PowerPoint 2007 XML"),
                                             prop("Overwrite", True)))
            print(f"Created {target} ({deck.pages.getCount()} slides)")
            assert deck.pages.getCount() == TOTAL, "slide count mismatch"
        finally:
            if doc is not None:
                doc.close(True)
            if desktop is not None:
                desktop.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
