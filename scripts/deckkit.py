#!/usr/bin/env python3
"""deckkit — Linux 0.11 커널 강좌 공통 슬라이드 프레임 (LibreOffice UNO).

scripts/make_NN_<slug>.py 계열이 import 한다. 회차별 스크립트 구조:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import deckkit as K

    SESSION = dict(
        no="02",                       # 두 자리 회차 번호
        total=46,                      # 총 장수 (계획 §2 표 행 수와 일치해야 한다)
        slug="02-protected-mode",      # output/<slug>.pptx
        part_no="A", part="«입문·부팅»",   # 15회차 지도 7파트
        title="02. x86 보호 모드와 소스 읽기 도구",
        question="선택자 하나가 어떻게 주소가 되는가? …",   # 핵심 질문 원문
        done=1,                        # 오늘 이전에 완료된 회차 수
        today_line="…한 줄…",          # 로드맵 오늘 상자 아래 문구 (최대 2줄)
        next_lines=["…", "…"],         # 로드맵 연결 문구 (최대 3줄)
        STRUCT=dict(                   # 04 커널 구조도 설정 (아래 STRUCT_KEYS)
            teal=["fs", "blk"],        # 강조할 하위시스템: proc,mm,fs,blk,chr,entry,main,lib
            today=[("fs/buffer.c", "버퍼 캐시"), …],  # 오늘 파일 TEAL 행 (선택, 최대 5)
            flow="bread → getblk → …",  # 오늘의 데이터 흐름 (ORANGE, 계층 경계선)
            up="↑ read() 반환",         # 커널→사용자 방향 화살표 문구 (선택)
            user="sh · 사용자 프로그램", # 사용자 공간 강조 문구
        ),
    )
    CHECKS = dict(                     # scripts/check_deck.py 가 읽는다
        captions={28: "src/boot/setup.s:191-193"},   # 슬라이드번호 → 코드 캡션
        required=["핵심 문자열", …],
        prereq=[("선수개념", "src/…첫 캡션…")],
        structure_nodes=["system_call.s", …],          # 04장에 반드시 등장할 문자열
        capture_slides=[25, 44],                       # 캡처/예상출력 슬라이드 번호
    )

    def populate(d):                   # 슬라이드 05부터 (01–04는 프레임이 그린다)
        p = d.slide("제목", K.S_BG, "하단 각주")
        …

    if __name__ == "__main__":
        K.run(globals())

레이아웃 규칙 (도우미가 강제):
- 본문 y 4100–14600 · 배너 기본 y14800 · 각주 16850 · 코드 패널 하단 14400 이내(자동)
- 모든 텍스트 위쪽 정렬 · 긴 텍스트는 자동 축소 · 코드 줄은 폭 초과 시 말줄임
- 강조색 ORANGE는 '오늘/현재' 전용, 일반 강조 TEAL.
"""

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
(S_Q, S_MAP, S_BG, S_CODE, S_STATE, S_CMP, S_DEMO, S_ANS, S_QUIZ, S_WRAP) = range(10)
PARTS = [("A", "«입문·부팅»", 3), ("B", "«실행의 길»", 3), ("C", "«메모리»", 2),
         ("D", "«프로그램의 일생»", 2), ("E", "«파일·저장»", 2), ("F", "«터미널»", 1),
         ("G", "«종합·실습»", 2)]
SUBS = [("proc", "프로세스 (kernel/", "sched.c fork.c\nexit.c signal.c"),
        ("mm", "메모리 (mm/", "memory.c\npage.s"),
        ("fs", "파일 시스템 (fs/", "namei.c inode.c\nbuffer.c exec.c"),
        ("blk", "블록 장치 (blk_drv/", "ll_rw_blk.c hd.c\nfloppy.c ramdisk.c"),
        ("chr", "문자 장치 (chr_drv/", "console.c tty_io.c\nkeyboard.S serial.c")]


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


WIDE_EXTRA = set("→↗↘↑↓▽△▶◀■□«»—≠≈")   # 전각 폭으로 렌더링되는 기호


def text_width(text, size):
    """텍스트 예상 폭 (1/100 mm). 대략적 추정 — 자동 축소용."""
    units = size * 35.3
    width = 0.0
    for ch in text:
        if ord(ch) >= 0x2E80 or ch in WIDE_EXTRA:   # CJK·전각 기호
            width += units
        elif ch in " .,:;'|!ijltf()[]-":
            width += units * 0.34
        else:
            width += units * 0.62
    return width


def fit_size(text, size, width, min_size=11):
    while size > min_size and text_width(text, size) > width / 1.12:
        size -= 1
    return size


class Deck:
    def __init__(self, doc, session):
        self.doc = doc
        self.S = session
        self.pages = doc.getDrawPages()
        self.count = 0
        first = self.pages.getByIndex(0)
        while first.getCount():
            first.remove(first.getByIndex(0))

    # ── 기본 도형 ────────────────────────────────────────────
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
        shape.TextVerticalAdjust = uno.Enum(
            "com.sun.star.drawing.TextVerticalAdjust", "TOP")
        cursor = shape.getText().createTextCursor()
        cursor.gotoStart(False)
        cursor.gotoEnd(True)
        cursor.CharFontName = cursor.CharFontNameAsian = (
            "DejaVu Sans Mono" if mono else FONT)
        cursor.CharHeight = cursor.CharHeightAsian = float(size)
        cursor.CharColor = color
        cursor.CharWeight = cursor.CharWeightAsian = 150.0 if bold else 100.0
        return shape

    # ── 페이지 공통 프레임 ────────────────────────────────────
    def slide(self, title, stage=None, note="", show_title=True):
        page = (self.pages.getByIndex(0) if self.count == 0
                else self.pages.insertNewByIndex(self.pages.getCount()))
        self.count += 1
        page.Width, page.Height = 33867, 19050
        bg = self.doc.createInstance("com.sun.star.drawing.Background")
        bg.FillColor = NAVY
        page.Background = bg
        number = self.pages.getCount()
        page.Name = f"{number:02d} {title}"
        s = self.S
        self.text(page, 1100, 400, 22000, 500, "LINUX 0.11 / SOURCE WALKTHROUGH", 11, TEAL)
        if show_title:
            tsize = fit_size(title, 28, 31400, min_size=20)
            self.text(page, 1100, 1150, 31400, 1500, title, tsize, PAPER, True)
        if stage is not None:
            self.stage_strip(page, stage)
        if note:
            self.text(page, 1100, 16850, 29500, 750, note, 10, MUTED)
        self.shape(page, 1100, 17750, 31500, 35, LINE)
        self.text(page, 1100, 18000, 24000, 600,
                  f"Linux 0.11 커널 강좌 · {s['no']}/15 · {s['slug']}", 10, MUTED)
        self.text(page, 30200, 17950, 2400, 650,
                  f"{number:02d} / {s['total']}", 13, TEAL)
        return page

    def stage_strip(self, page, stage, y=2950, h=750, size=13):
        gap = 250
        w = (31500 - (len(STAGES) - 1) * gap) // len(STAGES)
        for i, label in enumerate(STAGES):
            x = 1100 + i * (w + gap)
            active = i == stage
            self.shape(page, x, y, w, h, ORANGE if active else 0x203D4B)
            label_size = fit_size(f"{i + 1:02d} {label}", size, w - 320)
            self.text(page, x + 160, y + (h - 480) // 2, w - 320, 480,
                      f"{i + 1:02d} {label}", label_size, INK if active else MUTED, active)

    # ── 내용 도우미 ──────────────────────────────────────────
    def cards(self, page, cards, y=4700, h=8500):
        gap, total = 600, 31500
        width = (total - gap * (len(cards) - 1)) // len(cards)
        for i, (title, body) in enumerate(cards):
            x = 1100 + i * (width + gap)
            self.shape(page, x, y, width, h, PAPER)
            self.shape(page, x, y, width, 150, TEAL if i % 2 == 0 else ORANGE)
            tsize = fit_size(title, 21, width - 1100)
            self.text(page, x + 550, y + 650, width - 1100, 1600, title, tsize, INK, True)
            self.text(page, x + 550, y + 2600, width - 1100, h - 2800, body, 18, INK)

    def banner(self, page, text, y=14800, size=20, color=ORANGE):
        self.text(page, 1400, y, 30500, 1700, text, size, color, True)

    def flow(self, page, items, y=5300, h=3000, title_size=19):
        n = len(items)
        w = (31500 - (n - 1) * 1100) // n
        for i, (title, body) in enumerate(items):
            x = 1100 + i * (w + 1100)
            self.shape(page, x, y, w, h, PAPER)
            tsize = fit_size(title, title_size, w - 600)
            self.text(page, x + 300, y + 350, w - 600, 950, title, tsize, INK, True)
            self.text(page, x + 300, y + 1400, w - 600, h - 1450, body, 15, INK)
            if i < n - 1:
                self.text(page, x + w + 150, y + 800, 850, 1000, ">", 28, TEAL, True)

    def code_lines(self, path, start, end, size):
        lines = (ROOT / path).read_text().splitlines()
        limit = min(76, 18000 // int(size * 27.5))
        shown = []
        for i in range(start, end + 1):
            line = lines[i - 1].expandtabs(4)
            for marker in ("!", "/*", "//"):   # as86(!)·gas(/*)·C(//) 주석 제거
                line = line.split(marker, 1)[0]
            if line.lstrip().startswith("*"):  # 블록 주석 연속 줄
                line = ""
            entry = f"{i:3}  {line}".rstrip()
            if len(entry) > limit:
                entry = entry[:limit - 2].rstrip() + " …"
            shown.append(entry)
        return shown

    def code_panel(self, page, path, start, end, x, y, w, h, size=13, caption_extra=""):
        shown = self.code_lines(path, start, end, size)
        self.shape(page, x, y, w, h, 0x071A24)
        caption = f"{path}:{start}-{end}  / 인라인 주석 생략"
        if caption_extra:
            caption += f"  ·  {caption_extra}"
        csize = fit_size(caption, 12, w - 700, min_size=9)
        self.text(page, x + 350, y + 250, w - 700, 600, caption, csize, TEAL)
        shape = self.text(page, x + 350, y + 1150, w - 700, h - 1450,
                          "\n".join(shown), size, PAPER, mono=True)
        return shape

    def code(self, page, path, start, end, explanation, size=14, expl_size=19,
             panel_h=None):
        """코드(좌) + 해설(우) + 배너 자리 확보. 패널 높이·글자 크기 자동 조정."""
        while True:
            n = len(self.code_lines(path, start, end, size))
            needed = 1750 + n * size * 55
            if needed <= 10000 or size <= 10:
                break
            size -= 1
        if needed > 10000:
            raise ValueError(f"{path}:{start}-{end} — 15줄 초과, 발췌를 나누라")
        h = min(panel_h or needed, 10000)
        h = max(h, min(needed, 10000))
        self.code_panel(page, path, start, end, 1100, 4400, 19700, h, size)
        self.text(page, 22000, 4700, 10000, 9500, explanation, expl_size)

    def table(self, page, x, y, widths, rows, row_h=1200, size=15):
        for r, row in enumerate(rows):
            head = r == 0
            fill = TEAL if head else (0x183340 if r % 2 else 0x142E3A)
            cx = x
            for c, cell in enumerate(row):
                self.shape(page, cx, y + r * row_h, widths[c], row_h, fill)
                csize = fit_size(cell, size, widths[c] - 560, min_size=10)
                self.text(page, cx + 280, y + r * row_h + (row_h - 850) // 2,
                          widths[c] - 560, 850, cell, csize,
                          INK if head else PAPER, head)
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

    def placeholder_output(self, page, x, y, w, h, expected, capture_name):
        """캡처 미확보 시: 기대 출력 텍스트 패널 + '예상 출력 — 실측 아님' 태그."""
        self.shape(page, x, y, w, h, 0x071A24)
        tsize = fit_size(expected.split("\n")[0], 14, w - 700)
        self.text(page, x + 350, y + 250, w - 700, 600,
                  f"예상 출력 — 실측 아님 · 캡처 예정: materials/{self.S['slug']}/captures/{capture_name}",
                  11, TEAL)
        self.text(page, x + 350, y + 1150, w - 700, h - 1450, expected,
                  min(tsize, 14), PAPER, mono=True)

    def example_tag(self, page, text="설명용 예시 (실측 아님)"):
        self.outline(page, 26200, 4200, 6400, 1000, TEAL, 60)
        self.text(page, 26300, 4430, 6200, 550, text, 13, TEAL, True)


# ── 표준 앞부분 01–04 ────────────────────────────────────────
def title_slide(d):
    s = d.S
    p = d.slide(s["title"], None,
                "1991년 12월 공개 — 이 강의의 모든 줄 번호와 동작은 Linux 0.11 기준",
                show_title=False)
    d.shape(p, 27600, 900, 4800, 2100, ORANGE)
    d.text(p, 27850, 1200, 4400, 900, "Linux 0.11", 24, INK, True)
    d.text(p, 27850, 2200, 4400, 600, "1991", 15, INK, True)
    tsize = fit_size(s["title"].replace("\n", ""), 36, 29500, min_size=26)
    d.text(p, 1100, 4300, 30000, 3900, s["title"], tsize, PAPER, True)
    qsize = fit_size(s["question"], 26, 29500, min_size=18)
    d.text(p, 1100, 8300, 30000, 1500, s["question"], qsize, ORANGE, True)
    d.text(p, 1100, 10000, 30000, 900,
           "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)", 17, MUTED)
    d.text(p, 1100, 11200, 30000, 900,
           f"{s['no']}/15 · 파트 {s['part_no']} {s['part']}", 17, TEAL, True)
    d.text(p, 1100, 13000, 30000, 3200,
           "현대 커널 자료와의 혼동을 막는다 — 현대 이야기가 나올 때마다\n"
           "'Linux 0.11에는 없다 / 다르다'고 명시한다.\n"
           "코드 인용 줄 번호는 모두 src/ 원본 기준, 실행 화면은 lab/ 수정본이다.", 18, PAPER)


def question_slide(d, note=""):
    s = d.S
    p = d.slide("핵심 질문과 오늘의 길", None,
                note or "오늘의 10단계 구성은 계획 §2 목록과 같다")
    qsize = fit_size(s["question"], 30, 29500, min_size=20)
    d.text(p, 1100, 4500, 30000, 1500, s["question"], qsize, ORANGE, True)
    d.text(p, 1100, 6300, 30000, 1000,
           "이 질문을 오늘 120분 동안 따라간다. 답은 뒤의 '정답' 단계에서 다시 만난다.", 18, PAPER)
    d.text(p, 1100, 7900, 30000, 700, "오늘의 길 — 10단계", 16, TEAL, True)
    gap = 280
    w = (31500 - 9 * gap) // 10
    for i, label in enumerate(STAGES):
        x = 1100 + i * (w + gap)
        d.shape(p, x, 8900, w, 1500, TEAL)
        d.text(p, x + 120, 9060, w - 240, 560, f"{i + 1:02d}", 15, INK, True)
        d.text(p, x + 120, 9680, w - 240, 560, label, 15, INK, True)
    if s.get("road_note"):
        d.text(p, 1100, 11200, 31500, 3600, s["road_note"], 16, MUTED)


def roadmap_slide(d):
    s = d.S
    p = d.slide("과정 로드맵 — 오늘의 위치", None,
                f"완료 {s['done']}회차 · 회차가 지날수록 이 지도가 채워진다 (공통 규격 §2)")
    d.text(p, 1100, 3880, 31500, 700,
           f"15회차 · 7개 파트 — 오늘은 파트 {s['part_no']} {s['part']} · {s['no']}/15",
           14, TEAL, True)
    box_w, box_gap, part_gap = 1850, 380, 1300
    today = int(s["no"])

    def draw_row(parts, y, start_no):
        widths = [n * box_w + (n - 1) * box_gap for _, _, n in parts]
        total = sum(widths) + part_gap * (len(parts) - 1)
        x = 1100 + (31500 - total) // 2
        no = start_no
        boxes = {}
        for (pno, label, n), w in zip(parts, widths):
            d.outline(p, x - 220, y - 520, w + 440, 2060, LINE, 60)
            lsize = fit_size(f"{pno} {label}", 12, w + 700)
            d.text(p, x, y - 590, w + 700, 470, f"{pno} {label}", lsize, TEAL, True)
            bx = x
            for _ in range(n):
                boxes[no] = (bx, y)
                if no == today:
                    d.shape(p, bx, y, box_w, 1300, ORANGE)
                    d.outline(p, bx, y, box_w, 1300, PAPER, 150)
                    d.text(p, bx, y + 120, box_w, 450, f"{no:02d}", 18, INK, True)
                    d.text(p, bx, y + 860, box_w, 400, "오늘", 10, INK, True)
                elif no <= s["done"]:
                    d.shape(p, bx, y, box_w, 1300, TEAL)
                    d.text(p, bx, y + 380, box_w, 520, f"{no:02d}", 18, INK, True)
                else:
                    d.outline(p, bx, y, box_w, 1300, MUTED, 60)
                    d.text(p, bx, y + 380, box_w, 520, f"{no:02d}", 18, MUTED)
                bx += box_w + box_gap
                no += 1
            x += w + part_gap
        return boxes

    b1 = draw_row(PARTS[:4], 5150, 1)
    b2 = draw_row(PARTS[4:], 8900, 11)
    boxes = {**b1, **b2}

    def arrow(a, b):
        if a in boxes and b in boxes:
            (ax, ay), (bx, by) = boxes[a], boxes[b]
            if ay == by and bx > ax:
                d.text(p, ax + box_w + 20, ay + 480, 340, 500, "▶", 9, ORANGE, True)

    arrow(today - 1, today)
    arrow(today, today + 1)
    row1 = today <= 10
    d.text(p, 1100, 6750 if row1 else 10450, 23000, 1200,
           s["today_line"], 16, ORANGE, True)
    d.text(p, 1100, 11100 if row1 else 11900, 31500, 3400,
           "\n".join(s["next_lines"]), 15, PAPER)
    d.text(p, 15800, 15600, 3600, 600, "■ 완료", 12, TEAL, True)
    d.text(p, 19400, 15600, 3600, 600, "▶ 오늘", 12, ORANGE, True)
    d.text(p, 23000, 15600, 9600, 600, "□ 이후 · Linux 0.11 커널 강좌", 12, MUTED)


def structure_slide(d):
    s = d.S
    cfg = s["STRUCT"]
    teal = set(cfg.get("teal", []))
    p = d.slide("커널 전체 구조 — 오늘의 범위", None,
                "오늘 범위 = TEAL · 오늘의 흐름 = ORANGE · 범위 밖 = 실루엣으로 남긴다 (공통 규격 §2)")
    d.outline(p, 1100, 4300, 31500, 1900, LINE, 80)
    d.text(p, 1400, 4420, 9000, 460, "사용자 공간 (CPL=3)", 14, TEAL, True)
    d.text(p, 1400, 4940, 15000, 900, cfg.get("user", "sh · 응용 프로그램"), 17, ORANGE, True)
    d.text(p, 21000, 5030, 11300, 800, "응용 프로그램 (init/main.c 가 fork/exec 로 생성)", 13, MUTED)
    d.text(p, 1100, 6250, 23000, 520,
           "▽  int 0x80 (번호: include/unistd.h) · read()/write() 라이브러리 stub  ▽", 12, MUTED)
    if cfg.get("up"):
        d.text(p, 25400, 6230, 6000, 560, cfg["up"], 13, ORANGE, True)
    d.outline(p, 1100, 6800, 31500, 7000, LINE, 120)
    d.text(p, 1400, 6900, 9000, 460, "커널 공간 (CPL=0)", 14, TEAL, True)
    if cfg.get("flow"):
        fsize = fit_size(cfg["flow"], 14, 16500)
        d.text(p, 15500, 6880, 16000, 560, cfg["flow"], fsize, ORANGE, True)
    entry_fill = TEAL if "entry" in teal else None
    if entry_fill:
        d.shape(p, 1400, 7450, 30800, 850, TEAL)
        d.text(p, 1650, 7580, 30300, 560,
               "진입: kernel/system_call.s · sys_call_table (include/linux/sys.h)", 13, INK, True)
    else:
        d.outline(p, 1400, 7450, 30800, 850, MUTED, 50)
        d.text(p, 1650, 7580, 30300, 560,
               "진입: kernel/system_call.s · sys_call_table (include/linux/sys.h)", 13, MUTED)
    w = (30800 - 4 * 350) // 5
    for i, (key, t, b) in enumerate(SUBS):
        x = 1400 + i * (w + 350)
        if key in teal:
            d.shape(p, x, 8450, w, 1900, TEAL)
            tcol, bcol = INK, INK
        else:
            d.outline(p, x, 8450, w, 1900, MUTED, 50)
            tcol = bcol = MUTED
        tsize = fit_size(t + ")", 12, w - 500)
        d.text(p, x + 250, 8560, w - 500, 560, t + ")", tsize, tcol, True)
        d.text(p, x + 250, 9180, w - 500, 1050, b, 11, bcol)
    today = cfg.get("today", [])
    n = len(today)
    fixed = (4200 + 420) + (3900 + 420)
    avail = 30800 - 640 - fixed if n else 30800
    bw = min(7000, (avail - (n - 1) * 550) // n) if n else 0
    bx = 1400
    for i, (t, sub) in enumerate(today):
        d.shape(p, bx, 10650, bw, 1500, TEAL)
        tsize = fit_size(t, 12, bw - 400, min_size=9)
        ssize = fit_size(sub, 12, bw - 400, min_size=9)
        d.text(p, bx + 200, 10780, bw - 400, 500, t, tsize, INK, True)
        d.text(p, bx + 200, 11400, bw - 400, 500, sub, ssize, INK)
        if i < n - 1:
            d.text(p, bx + bw + 70, 11080, 440, 460, "→", 12, ORANGE, True)
        bx += bw + 550
    if n:
        d.text(p, bx - 130, 10960, 900, 620, "↗", 22, ORANGE, True)
        bx += 640
    if "main" in teal:
        d.shape(p, bx, 10650, 4200, 1500, TEAL)
        d.text(p, bx + 200, 10780, 3800, 500, "init/main.c", 13, INK, True)
        d.text(p, bx + 200, 11400, 3800, 500, "main() · init()", 11, INK)
    else:
        d.outline(p, bx, 10650, 4200, 1500, MUTED, 50)
        d.text(p, bx + 200, 10780, 3800, 500, "init/main.c", 13, MUTED)
        d.text(p, bx + 200, 11400, 3800, 500, "main() · init()", 11, MUTED)
    bx += 4200 + 420
    if "lib" in teal:
        d.outline(p, bx, 10650, 3900, 1500, TEAL, 90)
        d.text(p, bx + 220, 10780, 3500, 480, "lib/", 13, TEAL, True)
        d.text(p, bx + 220, 11400, 3500, 500, "string.c 등", 12, TEAL)
    else:
        d.outline(p, bx, 10650, 3900, 1500, MUTED, 50)
        d.text(p, bx + 220, 10780, 3500, 480, "lib/", 13, MUTED)
        d.text(p, bx + 220, 11400, 3500, 500, "string.c 등", 12, MUTED)
    d.text(p, 1100, 13860, 31500, 520, "▽  IRQ  ▽", 12, MUTED)
    d.outline(p, 1100, 14400, 31500, 1300, MUTED, 50)
    d.text(p, 1400, 14560, 30800, 900,
           "하드웨어 — 8259A PIC · 8253 타이머(IRQ 0) · 키보드(IRQ 1) · 하드디스크(IRQ 14) · CGA/MDA 화면",
           13, MUTED)
    d.text(p, 1100, 15950, 31500, 600,
           f"Linux 0.11 · 오늘 {d.S['no']}회차 — 누적 강조는 지난 회차 파일을 옅은 TEAL로 남긴다",
           13, TEAL)


def build_frame(d):
    """슬라이드 01–04 (표준 앞부분). populate()보다 먼저 호출한다."""
    title_slide(d)
    question_slide(d)
    roadmap_slide(d)
    structure_slide(d)


def run(ns, output_dir=None):
    """UNO로 덱을 만들어 output/<slug>.pptx 로 저장한다. ns = deck 모듈의 globals()."""
    session = ns["SESSION"]
    out = Path(output_dir) if output_dir else ROOT / "output"
    out.mkdir(parents=True, exist_ok=True)
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
            deck = Deck(doc, session)
            build_frame(deck)
            ns["populate"](deck)
            target = (out / f"{session['slug']}.pptx").resolve()
            doc.storeToURL(target.as_uri(),
                           (prop("FilterName", "Impress MS PowerPoint 2007 XML"),
                            prop("Overwrite", True)))
            print(f"Created {target} ({deck.pages.getCount()} slides)")
            assert deck.pages.getCount() == session["total"], \
                f"slide count {deck.pages.getCount()} != planned {session['total']}"
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
