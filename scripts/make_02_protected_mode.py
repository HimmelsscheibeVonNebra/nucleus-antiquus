#!/usr/bin/env python3
"""02회차 덱 — x86 보호 모드와 소스 읽기 도구 (output/02-protected-mode.pptx)

계획: materials/slide-plans/02-protected-mode.md (§2 표 46행 1:1 · §3 앞부분 명세 ·
§4 다이어그램 목록 · §5 캡처 10종 — materials/02-protected-mode/captures/ 미확보 →
전 캡처 슬라이드는 예상 출력 패널 · §6 이해 확인 6문항 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="02", total=46, slug="02-protected-mode",
    part_no="A", part="«입문·부팅»",
    title="02. x86 보호 모드와 소스 읽기 도구",
    question="선택자 하나가 어떻게 주소가 되는가? GDB로 커널을 멈추면 무엇이 보이는가?",
    done=1,
    today_line="보호 모드의 표 — 선택자·GDT·IDT를 읽고 GDB로 직접 확인한다",
    next_lines=[
        "01 → 02   01: 부팅 흐름(bootsect→setup→head)을 따라가며 보호 모드 진입까지만 봤다 → 02: 그 보호 모드가 주소를 만드는 선택자·GDT 설명표를 읽는다",
        "02 → 03   02: 설명표가 '무엇'인지 해독했다 → 03: 그 표들이 '언제' 만들어지는가 — setup.s 임시 GDT → head.s GDT → sched_init TSS/LDT",
    ],
    road_note=("오늘의 길(05장부터) — 배경 05–06·11·18·20·23·25–28·40 · 코드 08–10·12–15·17·19·21"
               "· 상태도 19·24·30 · 비교 07·16·22 · 시연·캡처 29·31–39 · 정답 41–42 · 확인 44 · "
               "정리 43·45–46. 질문(02)·지도(03–04)는 앞부분에서 이미 밟았다."),
    STRUCT=dict(
        teal=[],
        today=[("head.h", "include/linux/"),
               ("head.s", "boot/ · GDT·IDT 설치"),
               ("system.h", "include/asm/ — 매크로"),
               ("sched.h", "include/linux/ — LDT·TSS"),
               ("sched.c", "kernel/ — sched_init GDT 4·5번")],
        flow="논리 주소 → 선택자 → GDT/LDT → 선형 주소 · 이벤트 → IDT → CPL0 핸들러",
        user="sh · 사용자 프로그램 — 선택자 0x0f·0x17",
    ),
)

CHECKS = dict(
    captions={
        8: "src/boot/head.s:222-229",
        9: "src/boot/setup.s:205-224",
        10: "src/boot/head.s:232-238",
        12: "src/include/asm/system.h:42-50",
        13: "src/include/linux/sched.h:103-106",
        14: "src/include/linux/sched.h:188-231",
        15: "src/include/asm/system.h:52-66",
        17: "src/include/linux/sched.h:51-76",
        19: "src/boot/head.s:17-31",
        21: "src/include/asm/system.h:22-31",
    },
    required=[
        "선택자", "설명자", "GDT", "LDT", "IDT", "GDTR", "DPL", "CPL", "RPL",
        "TSS", "게이트", "세그먼트 캐시", "선형 주소", "lgdt", "lldt",
        "gdbstub", "target remote", "x/8xw", "0x00c09a0000000fff", "0x8E00",
    ],
    prereq=[
        ("선택자", "src/boot/head.s:222-229"),
        ("설명자", "src/boot/head.s:222-229"),
        ("GDTR", "src/boot/head.s:222-229"),
    ],
    structure_nodes=["head.h", "head.s", "system.h", "sched.h", "sched.c",
                     "GDT", "IDT"],
    capture_slides=[29, 31, 32, 33, 34, 35, 36, 37, 38, 39],
)


# ── 로컬 도우미 (deckkit 불변) ─────────────────────────────────
def wrap_kr(text, width, size):
    out, line, w = [], "", 0.0
    for ch in text:
        if ch == "\n":
            out.append(line)
            line, w = "", 0.0
            continue
        cw = K.text_width(ch, size)
        if w + cw > width and line:
            brk = line.rfind(" ")
            if ch != " " and brk > 0 and line[brk + 1:] == line[brk + 1:].lstrip(" "):
                nxt = line[brk + 1:] + ch
                out.append(line[:brk].rstrip())
                line, w = nxt, K.text_width(nxt, size)
            else:
                out.append(line)
                line, w = ch, cw
        else:
            line += ch
            w += cw
    out.append(line)
    return "\n".join(out)


def para(d, p, x, y, w, h, text, size=16, color=K.PAPER, bold=False):
    d.text(p, x, y, w, h, wrap_kr(text, w * 0.97, size), size, color, bold)


def pane(d, p, x, y, w, h, caption, body, size=12, cap=K.TEAL):
    d.shape(p, x, y, w, h, 0x071A24)
    d.text(p, x + 350, y + 250, w - 700, 600, caption,
           K.fit_size(caption, 12, w - 700, min_size=9), cap)
    d.text(p, x + 350, y + 1150, w - 700, h - 1450, body, size, K.PAPER,
           mono=True)


def auto_pane(d, p, x, y, w, h, caption, text, start=12, cap=K.TEAL):
    lines = text.split("\n")

    def fits(s):
        return (1150 + len(lines) * s * 58 <= h - 150
                and max((K.text_width(l, s) for l in lines), default=0)
                <= (w - 800) * 1.12)
    size = start
    while size > 8 and not fits(size):
        size -= 1
    pane(d, p, x, y, w, h, caption, text, size, cap)


def nbox(d, p, x, y, w, h, l1, l2=None, fill=K.PAPER, c1=K.INK, c2=None,
         edge=None, s1=15, s2=11):
    if fill is None:
        d.outline(p, x, y, w, h, edge or K.MUTED, 90)
    else:
        d.shape(p, x, y, w, h, fill)
        if edge:
            d.outline(p, x, y, w, h, edge, 160)
    c2v = c1 if c2 is None else c2
    s1v = K.fit_size(l1, s1, w - 500, min_size=9)
    ty = y + 220 if l2 else y + (h - 700) // 2
    d.text(p, x + 250, ty, w - 500, 750, l1, s1v, c1, True)
    if l2:
        d.text(p, x + 250, ty + 820, w - 500, h - (ty - y) - 900, l2,
               K.fit_size(l2, s2, w - 500, min_size=9), c2v)


def badge(d, p, x, y, w, text, fill=K.ORANGE, h=700, size=13):
    d.shape(p, x, y, w, h, fill)
    d.text(p, x + 150, y + (h - 520) // 2, w - 300, 520, text,
           K.fit_size(text, size, w - 300, min_size=9), K.INK, True)


def arrow(d, p, x, y, glyph, size=24, color=K.TEAL, w=1400, h=900):
    d.text(p, x, y, w, h, glyph, size, color, True)


def qbox(d, p, x, y, w, h, tag, body, tag_color, size=14):
    d.shape(p, x, y, w, h, K.INK)
    d.shape(p, x, y, w, 130, tag_color)
    d.text(p, x + 250, y + 320, w - 500, 500, tag, 15, tag_color, True)
    para(d, p, x + 250, y + 950, w - 500, h - 1150, body, size, K.PAPER)


def byte_map(d, p, y, cells, bar_labels):
    """설명자 8바이트 레이아웃 — cells=[(필드명, 채움)], bar_labels=[a범위,b범위]"""
    half = ["a — 낮은 4바이트 (desc_struct.a)", "b — 높은 4바이트 (desc_struct.b)"]
    for i, (label,) in enumerate(bar_labels):
        d.text(p, 1200 + i * 15300, y, 15000, 550, half[i], 12, K.MUTED, True)
    w, gap, x0 = 3690, 90, 1200
    for i, (field, fill) in enumerate(cells):
        x = x0 + i * (w + gap)
        if fill is None:
            d.outline(p, x, y + 650, w, 2100, K.MUTED, 60)
            col = K.MUTED
        else:
            d.shape(p, x, y + 650, w, 2100, fill)
            col = K.INK
        d.text(p, x + 150, y + 780, w - 300, 500, f"바이트 {i}", 10,
               col if fill else K.MUTED, True)
        d.text(p, x + 150, y + 1400, w - 300, 1250, wrap_kr(field, w - 400, 11),
               11, col, True)
    d.outline(p, x0, y + 620, 8 * w + 7 * gap, 2160, K.LINE, 60)


def populate(d):
    # ── 배경 05–06 ────────────────────────────────────────────
    # 05 1회차 복습: 두 주소 모델
    p = d.slide("1회차 복습: 두 주소 모델", K.S_BG,
                "모델 전환은 setup→head 사이 — 01회차 부팅 흐름(bootsect→setup→head→main) 복기 · 순서는 03회차")
    d.text(p, 1100, 4200, 15200, 600, "실주소 모드 (real mode)", 17, K.TEAL, True)
    nbox(d, p, 1100, 4900, 15200, 1300, "세그먼트 : 오프셋 — 0x2000:0x0001", None,
         K.PAPER, s1=16)
    arrow(d, p, 8000, 6280, "↓", 20)
    nbox(d, p, 1100, 6900, 15200, 1300, "seg × 16 + off — 0x2000×16 + 1", None,
         K.PAPER, s1=16)
    arrow(d, p, 8000, 8280, "↓", 20)
    nbox(d, p, 1100, 8900, 15200, 1300, "주소 0x20001 — 공간 1MB", None,
         K.PAPER, s1=16)
    para(d, p, 1100, 10500, 15200, 1600,
         "세그먼트 값 자체가 주소 계산에 들어간다 — 표 조회가 없다", 15, K.MUTED)
    d.text(p, 16900, 4200, 15700, 600, "보호 모드 (protected mode)", 17, K.TEAL, True)
    nbox(d, p, 16900, 4900, 15700, 1300, "선택자 : 오프셋 — 0x17:0x1234", None,
         K.PAPER, s1=16)
    arrow(d, p, 23900, 6280, "↓", 20, K.ORANGE)
    nbox(d, p, 16900, 6900, 15700, 1300, "LDT[2] 설명자 — base·limit·권한", None,
         K.ORANGE, s1=16)
    arrow(d, p, 23900, 8280, "↓", 20, K.ORANGE)
    nbox(d, p, 16900, 8900, 15700, 1300, "base + 0x1234 = 선형 주소", None,
         K.PAPER, s1=16)
    para(d, p, 16900, 10500, 15700, 1600,
         "선택자는 표의 색인 — 주소가 아니다(§8)", 15, K.ORANGE, True)
    d.text(p, 1100, 11650, 31500, 500,
           "01회차 부팅 흐름 — 이 전환이 일어나는 구간", 14, K.TEAL, True)
    d.flow(p, [("bootsect", "512B · BIOS 적재"), ("setup", "장치 조사"),
               ("head", "표·페이징"), ("main", "C 코드 시작")],
           y=12250, h=2100, title_size=14)
    d.banner(p, "같은 '세그먼트:오프셋' 표기가 두 모드에서 전혀 다르게 해석된다")

    # 06 선택자 16비트 해부
    p = d.slide("선택자 16비트 해부", K.S_BG,
                "근거 — boot/head.s:18 · include/asm/system.h:3-6 (0x0f) · include/linux/sched.h:130 (0x17)")
    d.shape(p, 1200, 4400, 19500, 1600, K.PAPER)
    d.text(p, 1450, 4750, 19000, 950, "index — 13비트 (표 안 위치, 최대 8192)", 17,
           K.INK, True)
    d.shape(p, 21000, 4400, 5500, 1600, K.TEAL)
    d.text(p, 21250, 4750, 5000, 950, "TI — 1비트", 17, K.INK, True)
    d.shape(p, 26800, 4400, 5500, 1600, K.ORANGE)
    d.text(p, 27050, 4750, 5000, 950, "RPL — 2비트", 17, K.INK, True)
    d.text(p, 1200, 6150, 19500, 800, "0 0 0 0 0 0 0 0 0 0 0 1 0", 20, K.PAPER,
           True, mono=True)
    d.text(p, 21000, 6150, 5500, 800, "1", 20, K.PAPER, True, mono=True)
    d.text(p, 26800, 6150, 5500, 800, "1 1", 20, K.PAPER, True, mono=True)
    d.text(p, 1200, 6950, 31500, 600, "↑ 예: 0x17 = 0000 0000 0001 0111b",
           14, K.MUTED, True)
    d.table(p, 1100, 7700, [3800, 3600, 4900, 3900, 15300], [
        ["값", "index", "TI", "RPL", "가리키는 곳 (0.11)"],
        ["0x08", "1", "0 — GDT", "00", "GDT[1] 커널 코드 — head.s:234"],
        ["0x10", "2", "0 — GDT", "00", "GDT[2] 커널 데이터 — head.s:236"],
        ["0x0f", "1", "1 — LDT", "11", "LDT[1] 사용자 코드 — system.h:6 move_to_user_mode"],
        ["0x17", "2", "1 — LDT", "11", "LDT[2] 사용자 데이터·스택 — sched.h:130"],
    ], row_h=1080, size=14)
    para(d, p, 1100, 13200, 31500, 1100,
         "0x0f·0x17은 'GDT 1·2번'이 아니라 LDT 항목 — TI 비트가 표를 고른다(§8)",
         15, K.ORANGE, True)
    d.banner(p, "선택자는 주소가 아니라 표의 색인이다 — index·TI·RPL 세 조각")

    # ── 비교 07 ───────────────────────────────────────────────
    # 07 설명표 비교: GDT / LDT / IDT
    p = d.slide("설명표 비교: GDT / LDT / IDT", K.S_CMP,
                "80386의 세 표를 전부 다룬다 — 근거 boot/head.s:78-93·105-107 · kernel/sched.c:385-412")
    d.table(p, 1100, 4400, [5300, 8700, 8700, 8800], [
        ["항목", "GDT", "LDT", "IDT"],
        ["로드 명령", "lgdt (head.s:106)", "lldt (sched.c:405)", "lidt (head.s:92)"],
        ["CPU 레지스터", "GDTR", "LDTR", "IDTR"],
        ["선택 방식", "선택자의 TI=0", "선택자의 TI=1", "벡터 번호 (int n · IRQ)"],
        ["항목 크기", "8바이트", "8바이트", "8바이트"],
        ["0.11 항목 수", "256 (head.s:238)", "태스크당 3 (sched.h:104)", "256 (head.s:232)"],
        ["들어가는 것", "세그먼트·TSS·LDT 설명자", "코드·데이터 설명자", "게이트 설명자"],
    ], row_h=1120, size=14)
    para(d, p, 1100, 12800, 31500, 1500,
         "세 표 모두 0.11이 사용한다 — GDT·IDT는 head.s가 만들고(08-10장), 태스크별 LDT 설치는 "
         "sched_init이 한다(sched.c:392-405, 15장).", 15)
    d.banner(p, "lgdt/lldt/lidt — 표의 시작 주소와 길이를 CPU 레지스터에 알리는 명령")

    # ── 코드 08–10 ────────────────────────────────────────────
    # 08 GDTR·IDTR의 실제 값
    p = d.slide("GDTR·IDTR의 실제 값 — head.s", K.S_CODE,
                "boot/head.s:222-229 — lgdt/lidt가 읽는 것은 메모리의 6바이트(limit 2 + base 4)")
    d.code(p, "src/boot/head.s", 222, 229,
           "① .word 256*8-1 — limit\n   항목 256 × 8바이트 − 1\n\n"
           "② .long _idt / _gdt — base\n   표의 시작 주소\n\n"
           "③ lgdt/lidt는 이 6바이트를\n   GDTR/IDTR에 그대로 적재\n\n"
           "④ .word 0 — 정렬 패딩")
    nbox(d, p, 1100, 12550, 14100, 1950,
         "idt_descr = limit 2바이트 + base 4바이트", "합계 6바이트 — 표 등록자 값",
         K.PAPER, s1=14, s2=12)
    arrow(d, p, 15600, 12950, "→", 24)
    nbox(d, p, 17400, 12550, 14100, 1950, "lidt → IDTR · lgdt → GDTR",
         "CPU가 참조할 표가 지정된다", K.TEAL, s1=14, s2=12)
    d.banner(p, "설명표의 위치는 변수 하나(_idt/_gdt)와 등록자 하나(descr)로 결정된다")

    # 09 표는 두 번 만들어진다 — setup.s 대조
    p = d.slide("표는 두 번 만들어진다 — setup.s 대조", K.S_CODE,
                "근거 — src/boot/setup.s:205-224 · src/boot/head.s:222-229 · 이 순서는 03회차(43장 연결)")
    d.code_panel(p, "src/boot/setup.s", 218, 224, 1100, 4400, 15200, 6400,
                 size=12, caption_extra="idt_48 · gdt_48 — setup 임시 등록자")
    para(d, p, 1100, 10900, 15200, 3300,
         "임시 gdt(205-216): 코드 0x9A00 · 데이터 0x9200 · limit 0x07FF → 8Mb · base 0.\n"
         "gdt_48: limit 0x800 · base 0x9xxxx — setup 세그먼트 안. idt_48: limit 0 — 빈 표.",
         14)
    d.code_panel(p, "src/boot/head.s", 222, 229, 16900, 4400, 15700, 7100,
                 size=12, caption_extra="본 표 등록자 — 08장과 같은 코드")
    para(d, p, 16900, 11800, 15700, 2500,
         "같은 lgdt가 두 번 실행된다 — setup은 임시 표(8Mb)로, head.s는 본 표(16Mb·256항목)로 교체한다.\n"
         "'표는 두 번 만들어진다' — 03회차가 이 순서를 시간축으로 다룬다.", 14)
    d.banner(p, "임시 표(setup, 8Mb) → 본 표(head.s, 16Mb) — 교체 뒤 세그먼트 재로드가 필수(19장)")

    # 10 head.s의 GDT 원문
    p = d.slide("head.s의 GDT 원문", K.S_CODE,
                "boot/head.s:232-238 · sched.h:149-151 주석 — 252칸 여유는 LDT·TSS 자리")
    d.code(p, "src/boot/head.s", 232, 238,
           "_idt — 256 × 8바이트 0\n(uninitialized)\n\n"
           "_gdt 항목1 코드 0x00c09a…\n항목2 데이터 0x00c092…\n항목3 TMP — 쓰지 마라\n\n"
           ".fill 252,8,0 — TSS·LDT\n여유 칸 (다음 장 해독)",
           expl_size=16)
    d.text(p, 1100, 11700, 31500, 550,
           "GDT 256 슬롯 × 8바이트 — 번호 = 선택자의 index", 14, K.TEAL, True)
    slots = [("0 NULL", K.PAPER), ("1 코드", K.PAPER), ("2 데이터", K.PAPER),
             ("3 TMP", None), ("4 TSS0", K.TEAL), ("5 LDT0", K.TEAL),
             ("6 TSS1", None), ("7 LDT1", None), ("… 여유 252칸", None)]
    for i, (label, fill) in enumerate(slots):
        nbox(d, p, 1100 + i * 3460, 12250, 3350, 1350, label, None, fill,
             K.INK if fill else K.MUTED, s1=13)
    d.banner(p, "252개 여유가 LDT·TSS 자리 — sched_init이 4·5번을 채운다(15장) · 36장 시연 B-3")

    # ── 배경 11 ───────────────────────────────────────────────
    # 11 세그먼트 설명자 64비트 해부
    p = d.slide("세그먼트 설명자 64비트 해부 — 비트 배치", K.S_BG,
                "include/asm/system.h:42-50 (_set_seg_desc)가 만드는 배치 — 80386 세그먼트 설명자 규격")
    byte_map(d, p, 4250,
             [("limit 7..0", K.PAPER), ("limit 15..8", K.PAPER),
              ("base 7..0", K.TEAL), ("base 15..8", K.TEAL),
              ("base 23..16", K.TEAL), ("P·DPL·S·type", K.ORANGE),
              ("G·D/B·0·AVL\nlimit 19..16", K.ORANGE),
              ("base 31..24", K.TEAL)],
             ["a", "b"])
    para(d, p, 1100, 7450, 31500, 1300,
         "base 32비트는 바이트 2·3·4·7에, limit 20비트는 바이트 0·1과 6의 상위 4비트에 "
         "흩어져 있다 — 8바이트 안의 비선형 배치", 16, K.ORANGE, True)
    d.table(p, 1100, 9100, [6300, 3300, 8500, 13400], [
        ["필드", "비트 수", "위치 (바이트)", "역할"],
        ["base", "32", "2 · 3 · 4 · 7", "세그먼트 시작 선형 주소 — 흩어져 있다"],
        ["limit", "20", "0 · 1 + 6의 상위 절반", "크기−1 — G=1이면 4KB 배율"],
        ["P·DPL·S·type", "8", "5", "존재 · 요구 권한 · 종류(S) · 형식"],
        ["G·D/B·0·AVL", "8", "6", "배율(G) · 32비트 기본(D/B) · limit 상위"],
    ], row_h=1000, size=14)
    d.banner(p, "다음 장(12) — 이 그림으로 0x00c09a0000000fff 를 해독한다")

    # ── 코드 12–15 · 비교 16 · 코드 17 · 배경 18 ─────────────
    # 12 GDT 코드·데이터 설명자 해독
    p = d.slide("GDT 코드·데이터 설명자 해독", K.S_CODE,
                "boot/head.s:232-238 · include/asm/system.h:42-50 — _set_seg_desc 의 OR 식과 1:1 대응")
    d.code_panel(p, "src/include/asm/system.h", 42, 50, 1100, 4400, 19700, 6700,
                 size=10, caption_extra="_set_seg_desc — C 표현")
    d.code_panel(p, "src/boot/head.s", 234, 236, 22000, 4400, 10500, 4500,
                 size=12, caption_extra="GDT 항목 1·2")
    para(d, p, 22000, 9100, 10500, 2300,
         "0x92 = 데이터 r/w — 같은 절차.\n"
         "0x00408000(system.h:47) = P·D/B·S·G 기본값.", 14)
    d.table(p, 1100, 11600, [7700, 3300, 6100, 6900, 7500], [
        ["설명자", "base", "limit (G=1)", "P·DPL·S·type", "의미"],
        ["0x00c09a0000000fff", "0", "0xfff → 16MB", "1·0·1·A(1010)", "커널 코드 — exec/read"],
        ["0x00c0920000000fff", "0", "0xfff → 16MB", "1·0·1·2(0010)", "커널 데이터 — r/w"],
    ], row_h=700, size=13)
    d.banner(p, "base=0·limit=16MB — 커널 세그먼트에서는 선형 주소 = 오프셋 그 자체(18장)")

    # 13 task_struct 안의 LDT
    p = d.slide("task_struct 안의 LDT", K.S_CODE,
                "include/linux/sched.h:103-106 · 123-133(INIT_TASK 발췌 123-127) — limit 주석 sched.h:111")
    d.code_panel(p, "src/include/linux/sched.h", 103, 106, 1100, 4400, 15200, 4600,
                 size=13, caption_extra="ldt[3] — 주석 원문")
    d.code_panel(p, "src/include/linux/sched.h", 123, 127, 1100, 9300, 15200, 5100,
                 size=12, caption_extra="INIT_TASK 의 ldt 부분")
    d.table(p, 16900, 4400, [3100, 2500, 3400, 4200, 2500], [
        ["항목", "a", "b", "바이트5 해독", "limit"],
        ["ldt[1] cs", "0x9f", "0xc0fa00", "P1·DPL3·S1·type A", "640KB"],
        ["ldt[2] ds&ss", "0x9f", "0xc0f200", "P1·DPL3·S1·type 2", "640KB"],
        ["ldt[0]", "0", "0", "빈 설명자(NUL)", "—"],
    ], row_h=1000, size=12)
    para(d, p, 16900, 8900, 15700, 5300,
         "base = 0 — 바이트 2·3·4·7이 전부 0. task 0은 base 0, limit 0x9f+1 페이지 = 640KB"
         "(sched.h:111 주석).\n\n"
         "'왜 DPL 3인가?' — 사용자 코드가 이 세그먼트로 실행되기 때문. "
         "답은 23장(권한)·41장(답 1)에서.", 15)
    d.banner(p, "태스크마다 자기 LDT — fork가 자식 base를 nr*0x4000000 로 바꾼다(fork.c:54-55, 06회차 예고)")

    # 14 설명자 필드를 만지는 매크로
    p = d.slide("설명자 필드를 만지는 매크로", K.S_CODE,
                "범위 — src/include/linux/sched.h:188-231 (발췌 _set_base 188-197 · set_base/set_limit 211-212) · kernel/fork.c:46-55(발췌 52-55)")
    d.code_panel(p, "src/include/linux/sched.h", 188, 197, 1100, 4400, 15200, 6700,
                 size=9, caption_extra="_set_base — rorl 회전")
    d.code_panel(p, "src/include/linux/sched.h", 211, 212, 16900, 4400, 15700, 3100,
                 size=12, caption_extra="set_base / set_limit 래퍼")
    d.code_panel(p, "src/kernel/fork.c", 52, 55, 16900, 7900, 15700, 4200,
                 size=11, caption_extra="copy_mem — 자식 LDT base (06회차)")
    para(d, p, 16900, 12400, 15700, 1900,
         "set_limit은 (limit-1)>>12 로 페이지 단위로 바꿔 저장(199-209) · get_base(214-226)는 조립의 "
         "역방향 · get_limit은 lsll 명령(228-231).", 14)
    d.text(p, 1100, 11400, 15200, 550, "설명자 8바이트에서 _set_base가 쓰는 곳", 13,
           K.TEAL, True)
    for i in range(8):
        x = 1100 + i * 1900
        base_byte = i in (2, 4, 7)
        nbox(d, p, x, 12000, 1800, 1100, f"+{i}", None,
             K.TEAL if base_byte else None, K.INK if base_byte else K.MUTED, s1=13)
    para(d, p, 1100, 13300, 15200, 1000,
         "base 바이트 +2·+4·+7 — rorl $16 회전으로 edx의 상·하위 바이트를 분해해 한 바이트씩 붙인다",
         13, K.ORANGE, True)
    d.banner(p, "설명자는 흩어진 바이트 조각 — C 매크로가 회전(rorl)으로 조립한다")

    # 15 시스템 설명자: TSS·LDT
    p = d.slide("시스템 설명자: TSS·LDT", K.S_CODE,
                "include/asm/system.h:52-66 · include/linux/sched.h:149-158 · kernel/sched.c:385-412(발췌 392-405) — 상세는 03·05회차")
    d.code_panel(p, "src/include/asm/system.h", 52, 66, 1100, 4400, 19700, 10000,
                 size=10, caption_extra="_set_tssldt_desc + set_tss/ldt_desc")
    d.code_panel(p, "src/include/linux/sched.h", 153, 158, 22000, 4400, 10500, 5600,
                 size=10, caption_extra="_TSS/_LDT — FIRST_TSS_ENTRY 4")
    para(d, p, 22000, 10350, 10500, 1350,
         "주석(sched.h:150-152): 0-nul, 1-cs, 2-ds, 3-syscall, 4-TSS0, 5-LDT0, 6-TSS1 …",
         13, K.MUTED)
    nbox(d, p, 22000, 11900, 10500, 850, "선택자 0x20 = GDT[4] TSS0 — ltr(0)",
         None, K.TEAL, s1=13)
    nbox(d, p, 22000, 12900, 10500, 850, "선택자 0x28 = GDT[5] LDT0 — lldt(0)",
         None, K.TEAL, s1=13)
    d.banner(p, "TSS type 0x89 · LDT 0x82 — limit 104(0x68) = tss_struct 크기 · 태스크 n마다 _TSS(n)=16n+32 · _LDT(n)=16n+40 (sched.c:404-405)")

    # 16 설명자 분류 비교
    p = d.slide("설명자 분류 비교", K.S_CMP,
                "S 비트 하나로 갈린다 — 근거 include/asm/system.h:42-66 · include/linux/sched.h:103-106")
    d.table(p, 1100, 4400, [4900, 2300, 3900, 9200, 11200], [
        ["분류", "S", "type", "0.11 생성 매크로", "사용처"],
        ["코드 설명자", "1", "…1010 (A)", "_set_seg_desc (system.h:42)", "GDT[1] head.s:235 · LDT[1] sched.h:125"],
        ["데이터 설명자", "1", "…0010 (2)", "_set_seg_desc (system.h:42)", "GDT[2] head.s:236 · LDT[2] sched.h:126"],
        ["TSS", "0", "0x89", "_set_tssldt_desc (system.h:65)", "sched.c:392 — GDT[4]"],
        ["LDT", "0", "0x82", "_set_tssldt_desc (system.h:66)", "sched.c:393 — GDT[5]"],
        ["게이트", "0", "5·14·15", "_set_gate (system.h:22)", "IDT — traps.c:185-203 · sched.c:409-411"],
    ], row_h=1120, size=14)
    para(d, p, 1100, 11700, 31500, 2400,
         "세그먼트 설명자와 게이트는 모두 8바이트 — 하지만 필드 배치가 다르다(11장 vs 20장).\n"
         "태스크 게이트(type 5)는 0.11이 만들지 않는다 — '존재하지만 안 쓴다'까지만 말한다(§8).",
         15)
    d.banner(p, "S=1 세그먼트 / S=0 시스템 — '어떤 매크로가 만드는지'로 기억한다")

    # 17 tss_struct와 "숨은 스택"
    p = d.slide('tss_struct와 "숨은 스택"', K.S_CODE,
                "구조체 전체 — src/include/linux/sched.h:51-76 (발췌 51-63·67-74) · INIT_TASK sched.h:128 · kernel/sched.c:53-58 task_union")
    d.code_panel(p, "src/include/linux/sched.h", 51, 63, 1100, 4400, 15200, 8200,
                 size=9, caption_extra="back_link … esp (esp0·ss0 포함)")
    para(d, p, 1100, 12850, 15200, 1500,
         "i387(75) — FPU 상태 저장 영역 · trace_bitmap(74) — 디버그 추적용. "
         "esp0·ss0이 다음 상태도(24장)의 주인공이다.", 13, K.MUTED)
    d.code_panel(p, "src/include/linux/sched.h", 67, 74, 16900, 4400, 15700, 6600,
                 size=11, caption_extra="세그먼트 레지스터·ldt")
    para(d, p, 16900, 11400, 15700, 2900,
         "INIT_TASK tss(sched.h:128): esp0 = PAGE_SIZE + &init_task, ss0 = 0x10 — "
         "union task_union(sched.c:53-56) 페이지의 끝.\n\n"
         "CPL0 진입 시 CPU가 TSS의 esp0/ss0을 자동 로드한다(24장). 커널 스택은 페이지 끝에서 "
         "아래로 자란다.", 14)
    d.banner(p, "커널 스택의 위치는 TSS가 기억한다 — 태스크마다 페이지 하나(task_union)")

    # 18 선택자 → 선형 → 물리: 전체 경로
    p = d.slide("선택자 → 선형 → 물리: 전체 경로", K.S_BG,
                "핵심 질문 1의 답 구도 — sched.h:188-231(get_base) · head.s:232-238 · 페이징은 07회차")
    chain = [
        ("0x17 : 0x1234", "논리 주소 — 세그먼트:오프셋", K.PAPER, None),
        ("TI=1 → LDTR", "현재 태스크의 LDT 선택", K.PAPER, None),
        ("LDT[2].base = 0", "설명자 조회 (06·13장)", K.TEAL, None),
        ("0 + 0x1234", "= 선형 주소 0x1234", K.ORANGE, None),
        ("CR3 · 페이지 테이블", "물리 주소 — 07회차", None, K.ORANGE),
    ]
    for i, (t, s, fill, edge) in enumerate(chain):
        x = 1100 + i * 6350
        nbox(d, p, x, 4500, 5750, 2700, t, s, fill, K.INK if fill else K.ORANGE,
             edge=edge, s1=15, s2=11)
        if i < 4:
            d.text(p, x + 5800, 5500, 600, 900, ">", 26, K.TEAL, True)
    d.text(p, 26200, 7350, 6400, 500, "점선 = 오늘 범위 밖", 11, K.ORANGE, True)
    d.cards(p, [
        ("커널 세그먼트 — base 0",
         "GDT 1·2번(base=0, 16MB)\n선형 주소 = 오프셋 그대로\n\nhead.s:235-236 (12장 해독)"),
        ("사용자 세그먼트 — LDT",
         "base = 태스크 시작 주소\ntask 0은 0 · 자식은 nr*0x4000000\n(fork.c:54-55, 06회차)\nlimit 640KB (sched.h:111)"),
    ], y=8300, h=5500)
    d.banner(p, "오늘은 선형 주소까지 — 선형→물리(페이징)은 07회차가 연다 · 이 그림은 41장 답에서 재사용")

    # ── 상태도 19 · 배경 20 · 코드 21 · 비교 22 · 배경 23 · 상태도 24 ─
    # 19 상태 변화도 1
    p = d.slide("상태 변화도 1: 세그먼트 레지스터의 두 부분", K.S_STATE,
                "재로드 코드 — src/boot/head.s:17-31 (특히 26-31) · setup_gdt src/boot/head.s:105-107 — 'reload all the segment registers'")
    d.code_panel(p, "src/boot/head.s", 17, 31, 1100, 4400, 19700, 10000,
                 size=10, caption_extra="startup_32 — 26-31이 재로드")
    nbox(d, p, 22000, 4400, 10500, 1300, "보이는 부분 — 선택자 0x10 (16비트)",
         None, K.PAPER, s1=13)
    para(d, p, 22000, 5900, 10500, 800,
         "GDB info registers 에 보이는 것은 여기까지", 13, K.MUTED)
    nbox(d, p, 22000, 6800, 10500, 1600, "숨은 세그먼트 캐시",
         "base 0 · limit 16MB · 속성 — 다음 로드까지 유지, GDB에 안 보임", K.TEAL, s1=14, s2=11)
    para(d, p, 22000, 8700, 10500, 1200,
         "lgdt — GDTR만 바꾼다, 캐시 불변 ✗\nmov %ax,%ds — 표를 다시 읽어 캐시 갱신 ✓",
         14, K.ORANGE, True)
    d.table(p, 22000, 10100, [6300, 4200], [
        ["명령", "캐시"],
        ["lgdt gdt_descr", "변화 없음"],
        ["mov %ax,%ds", "DS 갱신"],
        ["jmpi (원거리 점프)", "CS 갱신"],
        ["lss …,%esp", "SS 갱신"],
    ], row_h=800, size=12)
    d.banner(p, "표를 갈아끼운(lgdt) 뒤에는 반드시 세그먼트 레지스터를 다시 로드한다 — head.s:26-31 주석")

    # 20 IDT 게이트 64비트 해부
    p = d.slide("IDT 게이트 64비트 해부 — 비트 배치", K.S_BG,
                "include/asm/system.h:22-31 · boot/head.s:78-93 — 세그먼트 설명자(11장)와 같은 8바이트, 다른 배치")
    byte_map(d, p, 4250,
             [("offset 7..0", K.PAPER), ("offset 15..8", K.PAPER),
              ("선택자 15..0", K.TEAL), ("offset 23..16", K.PAPER),
              ("offset 31..24", K.PAPER), ("P·DPL·0·type", K.ORANGE),
              ("0000 — 미사용", None), ("offset 39..32\n(386: 0)", None)],
             ["a", "b"])
    para(d, p, 1100, 7450, 31500, 1300,
         "같은 8바이트 — 세그먼트 설명자는 base·limit를 담고, 게이트는 핸들러 선택자·offset를 담는다",
         16, K.ORANGE, True)
    d.table(p, 1100, 9100, [6300, 3300, 8500, 13400], [
        ["필드", "크기", "위치 (바이트)", "역할"],
        ["offset", "32", "0 · 1 · 3 · 4 · 7", "핸들러 시작 주소 (EIP)"],
        ["선택자", "16", "2", "핸들러 코드 세그먼트 — 0.11은 0x0008"],
        ["P·DPL·type", "13", "5", "존재 · 권한 · 게이트 종류(22장)"],
    ], row_h=1000, size=14)
    d.banner(p, "다음 장(21) — _set_gate 매크로가 이 배치 그대로 비트를 만든다")

    # 21 _set_gate와 setup_idt의 0x8E00
    p = d.slide("_set_gate와 setup_idt의 0x8E00", K.S_CODE,
                "include/asm/system.h:22-31 · boot/head.s:78-93(발췌 78-85) — C 매크로와 어셈블리가 같은 비트를 만든다")
    d.code_panel(p, "src/include/asm/system.h", 22, 31, 1100, 4400, 15200, 7250,
                 size=10, caption_extra="_set_gate")
    para(d, p, 1100, 12000, 15200, 2300,
         "%0 = 0x8000+(dpl<<13)+(type<<8) — 컴파일 시간 상수.\n"
         "eax = 0x00080000 → 게이트의 선택자 = 0x0008 (GDT[1] 커널 코드).", 14)
    d.code_panel(p, "src/boot/head.s", 78, 85, 16900, 4400, 15700, 6150,
                 size=10, caption_extra="setup_idt 앞부분 — 0x8E00")
    d.table(p, 16900, 10900, [4700, 5300, 5700], [
        ["식 (system.h:28)", "만들어지는 비트", "의미"],
        ["0x8000 + dpl<<13", "P=1 · DPL 0/3", "존재 + 요구 권한"],
        ["type<<8", "14 · 15", "인터럽트 / 트랩 게이트"],
        ["a = 0x00080000", "선택자 0x0008", "커널 코드 (head.s:81)"],
        ["head.s:82 — 0x8E00", "P1·DPL0·type14", "같은 비트 — 어셈과 C 일치"],
    ], row_h=700, size=12)
    d.banner(p, "0x8E00 = P1·DPL0·type14 — C 매크로(_set_gate)와 setup_idt가 독립적으로 같은 값을 만든다")

    # 22 게이트 종류 비교
    p = d.slide("게이트 종류 비교 (IDT, 80386)", K.S_CMP,
                "include/asm/system.h:33-40 — 태스크(5)·인터럽트(14)·트랩(15) 전부 소개, 0.11 사용은 14·15")
    d.table(p, 1100, 4400, [5000, 2400, 4200, 8900, 11000], [
        ["종류", "type", "진입 시 IF", "0.11 매크로 (dpl)", "사용처"],
        ["태스크 게이트", "5", "— 태스크 전환", "없음", "0.11 미사용 — 존재만 인지(§8)"],
        ["인터럽트 게이트", "14", "클리어 (IF=0)", "set_intr_gate(n,addr) — 0", "IRQ — 타이머 0x20 (sched.c:409)"],
        ["트랩 게이트", "15", "유지", "set_trap_gate(n,addr) — 0", "예외 0-16 (traps.c:185-203)"],
        ["트랩(시스템)", "15", "유지", "set_system_gate(n,addr) — 3", "int3 (traps.c:188) · 0x80 (sched.c:411)"],
    ], row_h=1200, size=14)
    para(d, p, 1100, 10900, 31500, 2800,
         "인터럽트 게이트는 진입 시 IF를 클리어 — 핸들러 도중 인터럽트 겹침을 막는다. "
         "트랩 게이트는 IF 유지 — 시스템 콜 복귀 뒤에도 인터럽트가 열려 있어야 한다.\n"
         "콜 게이트는 IDT가 아니라 GDT/LDT용 — 오늘 범위 밖, 이름만 알아둔다.", 15)
    d.banner(p, "0.11이 IDT에 심는 것은 인터럽트(14)·트랩(15) 둘뿐 — 태스크 게이트는 만들지 않는다")

    # 23 권한: CPL / DPL / RPL
    p = d.slide("권한: CPL / DPL / RPL", K.S_BG,
                "include/asm/system.h:33-40 · kernel/sched.c:411 · kernel/traps.c:188 — CPU 모드(실주소/보호)와는 다른 축(§8)")
    d.cards(p, [
        ("CPL — 현재 특권",
         "지금 실행 중인 코드의 권한\nCS 선택자 하위 2비트\n커널 = 0 · 사용자 = 3"),
        ("DPL — 설명자·게이트의 문턱",
         "설명자: 이 권한 이상만 접근\n게이트: 이 권한 이하만 통과\n'방향'이 서로 다르다 — 표 참고"),
        ("RPL — 요청 권한",
         "선택자에 실린 2비트\n낮은 권한으로 접근을 제한\n0.11에서는 사실상 CPL과 같음"),
    ], y=4400, h=5300)
    d.table(p, 1100, 10100, [7300, 9400, 14800], [
        ["검사", "규칙", "0.11 예"],
        ["데이터 세그먼트", "max(CPL, RPL) ≤ DPL", "사용자(3) → LDT[2] DPL 3 접근 가능 (sched.h:126)"],
        ["게이트 통과", "CPL ≤ 게이트 DPL", "int $0x80 — 게이트 DPL 3 (set_system_gate, sched.c:411)"],
        ["코드 진입", "CPL = DPL (게이트 경유)", "conforming 세그먼트는 예외 — 0.11에는 없음"],
    ], row_h=1050, size=13)
    d.banner(p, "int $0x80이 CPL3에서 되는 이유 — 게이트 DPL이 3이기 때문(sched.c:411). int3도 같다(traps.c:188)")

    # 24 상태 변화도 2
    p = d.slide("상태 변화도 2: 권한 전환과 스택", K.S_STATE,
                "변경 데이터 — SS·ESP·CS·EIP·EFLAGS · 근거 sched.h:53-54(esp0/ss0) · fork.c:93-94 · system.h:1-14 (01회차 연결)")
    steps = [
        ("CPL3 사용자 코드 — int $0x80", K.PAPER),
        ("게이트 DPL 검사 통과 (23장)", K.PAPER),
        ("TSS.ss0/esp0 로드 — 커널 스택 전환", K.ORANGE),
        ("CPU push — SS,ESP,EFLAGS,CS,EIP", K.ORANGE),
        ("핸들러 실행 — CPL0 (인터럽트 게이트면 IF=0)", K.PAPER),
        ("iret — 역순 pop → CPL3 복귀", K.PAPER),
    ]
    for i, (t, fill) in enumerate(steps):
        y = 4400 + i * 1550
        nbox(d, p, 1100, y, 15200, 1300, t, None, fill, s1=14)
        if i < 5:
            d.text(p, 15400, y + 1280, 900, 500, "↓", 14, K.ORANGE, True)
    d.text(p, 16900, 4200, 15700, 550, "커널 스택(새 스택) — 위가 높은 주소", 14,
           K.TEAL, True)
    frame = [("SS — 사용자 스택 세그먼트 (0x17)", K.TEAL),
             ("ESP — 사용자 스택 포인터", K.TEAL),
             ("EFLAGS", K.PAPER),
             ("CS = 0x0f — 사용자 코드", K.PAPER),
             ("EIP — int 다음 명령", K.ORANGE)]
    for i, (t, fill) in enumerate(frame):
        nbox(d, p, 16900, 4750 + i * 900, 15700, 840, t, None, fill, s1=12)
    d.text(p, 16900, 9400, 15700, 500, "push 순서: SS → ESP → EFLAGS → CS → EIP",
           13, K.ORANGE, True)
    para(d, p, 16900, 10100, 15700, 4200,
         "move_to_user_mode(system.h:1-14)는 이 프레임을 '거꾸로' 만들어 iret으로 CPL3에 진입한다 — "
         "01회차에서 본 코드.\n\n"
         "자식 태스크도 같은 모양의 프레임을 만들어 태어난다 — fork.c:93-94: tss.ss0=0x10, "
         "tss.esp0 = PAGE_SIZE+(long)p (17장).", 14)
    d.banner(p, "커널 스택 포인터는 TSS에서 온다 — 이해 확인 질문 5의 답 · push 순서는 아키텍처 문서 근거(§8)")

    # ── 배경 25–28 · 캡처 29 · 상태도 30 ──────────────────────
    # 25 lab/ 환경 지도
    p = d.slide("lab/ 환경 지도", K.S_BG,
                "src/는 인용 기준 원본 · lab/는 yuan-xy/Linux-0.11 기반 수정본(현대 GCC·QEMU i386) — 실행 화면은 전부 lab/")
    auto_pane(d, p, 1100, 4300, 15200, 8100, "src/ — Kernel.org 원본 (이 강의의 줄 번호)",
              "boot/    bootsect.s · setup.s · head.s\n"
              "include/ linux/ sched.h head.h … · asm/ system.h …\n"
              "init/    main.c\n"
              "kernel/  sched.c fork.c traps.c system_call.s\n"
              "mm/      memory.c page.s\n"
              "fs/      namei.c inode.c buffer.c exec.c\n"
              "blk_drv/ chr_drv/ lib/", start=13)
    auto_pane(d, p, 16900, 4300, 15700, 8100, "lab/ — 실행·디버깅용 (yuan-xy 기반 수정본)",
              "Makefile · run/debug 실행 스크립트\n"
              "tools/system — 커널 ELF (GDB 심볼)\n"
              "Image — 부팅 이미지\n"
              "System.map — 심볼 주소표\n"
              "현대 GCC로 빌드 · QEMU i386(TCG)로 실행\n"
              "-s -S 디버깅 구성 포함", start=13)
    d.outline(p, 1100, 12600, 31500, 2000, K.ORANGE, 110)
    para(d, p, 1350, 12850, 31000, 1600,
         "심볼·줄 번호가 다를 수 있다 — main vs _main, lab init/main.c의 줄 번호. "
         "슬라이드 인용은 src/ 원본, 실행 캡처는 lab/ 기준임을 계속 명시한다(§11).",
         14, K.ORANGE, True)
    d.banner(p, "읽는 곳 src/ · 돌리는 곳 lab/ — 두 세계를 오가며 확인한다")

    # 26 QEMU -s -S
    p = d.slide("QEMU -s -S", K.S_BG,
                "lab/ 실행 스크립트 기준 — qemu-system-i386 … -s -S · TCG(하드웨어 가속 없음)")
    d.cards(p, [
        ("-s — gdbstub 개통",
         "TCP :1234 로 GDB 원격 접속 대기\n-gdb tcp::1234 와 같은 뜻\n이 포트로 target remote 접속(27장)"),
        ("-S — CPU 정지 시작",
         "전원 인가 상태에서 CPU 멈춤\n첫 명령 전 — BIOS 리셋 벡터부터\n단계별 관찰이 가능하다"),
    ], y=4400, h=5400)
    nbox(d, p, 1100, 10100, 31500, 1900,
         "정지 직후 — real mode · CS=0xf000 · EIP=0xfff0 (BIOS 리셋 벡터, 아직 커널 전)",
         "보호 모드 진입은 한참 뒤 — setup.s의 lmsw(01회차)", K.PAPER, s1=15, s2=12)
    para(d, p, 1100, 12250, 31500, 2400,
         "재설정 — QEMU 모니터에서 system_reset · 종료 — quit(모니터) 또는 터미널 Ctrl-a x.\n"
         "모니터 진입 — 명령행 -monitor stdio 또는 그래픽 창 Ctrl-Alt-2 (34장 시연 B-1에서 사용).",
         15)
    d.banner(p, "정지 상태에서 GDB가 붙는다 — 연결 절차는 27장, 세션 흐름은 30장 상태도")

    # 27 GDB 연결과 실행 제어 명령
    p = d.slide("GDB 연결과 실행 제어 명령", K.S_BG,
                "gdb lab/tools/system — ELF 심볼을 먼저 띄우면 원격에서도 함수명·줄 번호가 보인다")
    d.table(p, 1100, 4400, [8300, 11600, 11600], [
        ["명령", "하는 일", "오늘 어디서"],
        ["gdb tools/system", "커널 ELF 로드 — 심볼·디버깅 정보", "시연 A 준비 (31장)"],
        ["target remote :1234", "QEMU gdbstub(:1234)에 접속", "31장"],
        ["b main", "main 에 중단점 — 원본 기준 init/main.c:104", "시연 A-1 (31장)"],
        ["c (continue)", "중단점까지 실행", "31 · 36장"],
        ["si / n", "한 명령씩(si) / 한 줄씩(n) 실행", "시연 C-3 (39장)"],
        ["bt", "백트레이스 — 호출 프레임", "08회차에서 사용"],
        ["finish", "현재 함수 끝까지 실행 후 복귀", "시연 B-3 (36장)"],
    ], row_h=1080, size=14)
    d.banner(p, "실행 제어 — b · c · si/n · bt · finish — 이것만으로 오늘 시연 전부를 돌린다")

    # 28 GDB 관찰 명령
    p = d.slide("GDB 관찰 명령 — 무엇을 읽는가", K.S_BG,
                "p/x $cr3 등 일부 레지스터 노출 여부는 gdbstub 구현에 따라 다르다(§11) — 없으면 QEMU 모니터(34장)")
    d.table(p, 1100, 4400, [7400, 9400, 8400, 6300], [
        ["명령", "읽는 대상", "보이는 것", "오늘 어디서"],
        ["info registers", "CPU 레지스터", "선택자 값(cs·ds) · eflags · cr*", "32 · 39장"],
        ["x/8xw $esp", "스택 메모리 (8워드)", "복귀 주소 · push된 값", "33장"],
        ["x/8xw &gdt", "커널 데이터 메모리", "GDT 설명자 원시 값", "35장"],
        ["p &gdt · p &user_stack", "심볼의 주소", "데이터 위치 확인", "33 · 34장"],
        ["p/x $cr0", "제어 레지스터", "PE·PG 비트 (노출 시)", "32장"],
    ], row_h=1100, size=14)
    para(d, p, 1100, 11400, 31500, 2700,
         "x/8xw 형식 — 8개를 16진수(x)로 워드(w=4바이트)단위. &심볼은 주소, $레지스터는 값.\n"
         "보이지 않는 것도 있다 — 세그먼트 캐시(base/limit)와 TLB는 info registers 어디에도 없다(19·42장).",
         15)
    d.banner(p, "관찰 — info registers · x · p — 명령을 낼 때마다 '무엇을 읽는가'를 묻는다")

    # 29 VS Code 연결 (캡처)
    p = d.slide("VS Code 연결", K.S_DEMO,
                "launch.json — gdb remote :1234 · program = lab/tools/system (ELF) · 캡처 예정 01-vscode-debug-panels.png")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "// .vscode/launch.json — lab/ 핵심 항목\n"
                         "{\n"
                         "  \"type\": \"cppdbg\",\n"
                         "  \"request\": \"launch\",\n"
                         "  \"name\": \"kernel-0.11 (QEMU remote)\",\n"
                         "  \"program\": \"${workspaceFolder}/tools/system\",\n"
                         "  \"MIMode\": \"gdb\",\n"
                         "  \"miDebuggerPath\": \"/usr/bin/gdb\",\n"
                         "  \"miDebuggerServerAddress\": \"localhost:1234\",\n"
                         "  \"stopAtEntry\": false,\n"
                         "  \"preLaunchTask\": \"make\"   // 선택\n"
                         "}",
                         "01-vscode-debug-panels.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· BREAKPOINTS — 중단점 목록·활성화\n"
         "· WATCH — 변수·수식 관찰\n"
         "· REGISTERS — 레지스터 전개\n"
         "· MEMORY(16진 뷰어) — &gdt 덤프\n\n"
         "터미널 GDB와 같은 gdbstub을 다르게 보여줄 뿐 — 정보는 같다(27·28장).\n\n"
         "캡처는 세 패널이 함께 보이는 화면으로 준비한다.", 14)
    d.banner(p, "같은 gdbstub, 다른 피부 — VS Code 디버그 UI도 결국 27·28장의 명령들이다")

    # 30 상태 변화도 3: GDB 세션
    p = d.slide("상태 변화도 3: GDB 세션", K.S_STATE,
                "QEMU -s -S · GDB — 세션 전체의 상태 흐름 · 상태마다 쓸 수 있는 명령이 다르다")
    states = [
        ("QEMU -S 정지", "real mode\nCS=0xf000 · EIP=0xfff0\n→ target remote"),
        ("연결됨", "심볼 로드(gdb tools/system)\n→ b main · b sched_init"),
        ("실행 중 (c)", "CPU가 달린다 — 화면 정적\n→ Ctrl-C 로 강제 정지"),
        ("중단점 정지", "보호 모드 · 페이징 ON\n→ info registers · x · p · si"),
        ("종료", "detach/quit — QEMU 계속\n또는 함께 종료"),
    ]
    for i, (t, s) in enumerate(states):
        x = 1100 + i * 6350
        nbox(d, p, x, 4500, 5750, 3100, t, s,
             K.ORANGE if i == 3 else K.PAPER, s1=14, s2=11)
        if i < 4:
            d.text(p, x + 5800, 5600, 600, 900, ">", 26, K.TEAL, True)
    d.table(p, 1100, 8300, [7800, 9000, 14700], [
        ["상태 전환", "명령", "CPU 모드 변화"],
        ["정지 → 연결", "target remote :1234", "없음 — 아직 real mode"],
        ["연결 → 실행", "c (continue)", "BIOS → bootsect → setup — real → 보호"],
        ["실행 → 중단", "중단점 도달 (b main)", "이 시점엔 보호 모드 + 페이징 ON (head.s 통과 후)"],
        ["중단 → 진행", "si / n — 한 걸음 · c — 계속", "main 의 C 코드 진행"],
    ], row_h=1050, size=13)
    d.banner(p, "'중단점 정지'가 오늘 시연의 관찰 창 — 이 상태에서 레지스터·메모리를 읽는다(28장)")

    # ── 시연·캡처 31–39 ───────────────────────────────────────
    # 31 시연 A-1
    p = d.slide("시연 A-1: b main 도달", K.S_DEMO,
                "lab/ 수정본 · QEMU i386 TCG · b main — 원본 기준 init/main.c:104 · 캡처 속 줄 번호 NN은 lab 기준(§11)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "# 터미널 1 — lab/ 실행 스크립트\n"
                         "$ ./run.sh -s -S   # qemu-system-i386 … -s -S\n"
                         "\n"
                         "# 터미널 2 — GDB\n"
                         "$ gdb tools/system\n"
                         "(gdb) target remote :1234\n"
                         "Remote debugging using :1234\n"
                         "0x0000fff0 in ?? ()\n"
                         "(gdb) b main\n"
                         "Breakpoint 1 at 0x649d: file init/main.c, line 105.\n"
                         "(gdb) c\n"
                         "Continuing.\n"
                         "\n"
                         "Breakpoint 1, main () at init/main.c:105\n"
                         "(gdb)",
                         "02-gdb-break-main.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "절차\n\n"
         "1. 터미널1 — QEMU -s -S (26장)\n"
         "2. 터미널2 — gdb tools/system →\n    target remote :1234\n"
         "3. b main → c\n\n"
         "관찰(§5)\n"
         "· Breakpoint 1, main () at init/main.c:NN 도달\n"
         "· 정지 시점 = 보호 모드 + 페이징 ON (30장 상태 4)\n\n"
         "각주 — lab 수정본이라 원본 src/init/main.c:104와 줄 번호가 다를 수 있다. "
         "사전 캡처 대체: build/gdb-main.txt(준비 전).", 14)
    d.banner(p, "main에 도달했다 = head.s·startup_32 전 과정 통과 — 05장 전환 지점의 끝")

    # 32 시연 A-2
    p = d.slide("시연 A-2: info registers", K.S_DEMO,
                "boot/head.s:17-31(세그먼트 로드) · 43-61(cr0 MP/EM/ET — FPU 유무) — cr0 전체 값은 '관찰 결과'로만(§8)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) info registers\n"
                         "eax    0x0        0\n"
                         "ecx    0x0        0\n"
                         "…\n"
                         "eflags 0x2      [ ]      ← IF=0 (아직 cli 상태)\n"
                         "cs     0x0008    8       ← GDT[1] 커널 코드\n"
                         "ss     0x0010    16\n"
                         "ds     0x0010    16\n"
                         "es     0x0010    16\n"
                         "fs     0x0010    16\n"
                         "gs     0x0010    16      ← 전부 GDT[2] 커널 데이터\n"
                         "cr0    0x80000011 [PG PE ET MP]  ← PE=1 · PG=1\n"
                         "cr2    0x0        0\n"
                         "cr3    0x0        0       ← pg_dir (head.s:214)",
                         "03-info-registers.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· cs=0x0008 — GDT[1] 커널 코드\n"
         "· ds·es·fs·gs·ss=0x0010 — GDT[2]\n"
         "· eflags IF=0 — 인터럽트 아직 허용 전\n"
         "· cr0 — PE=1(보호) · PG=1(페이징) · cr3=0(pg_dir)\n\n"
         "06장 해독표와 대조 — 선택자 값이 그대로 보인다.\n\n"
         "MP/EM/ET는 FPU 유무에 따라 다르다(head.s:43-61) — cr0 전체 값을 미리 단정하지 않는다(§8).",
         14)
    d.banner(p, "06장 해독표의 실측 — 0x08·0x10이 세그먼트 레지스터에 그대로 들어 있다")

    # 33 시연 A-3
    p = d.slide("시연 A-3: x/8xw $esp", K.S_DEMO,
                "boot/head.s:136-140 (pushl $0 ×3 · $L6 · $_main) · kernel/sched.c:67-72 (user_stack · stack_start)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) x/8xw $esp\n"
                         "0x5fec:  0x0000662c  0x00000000\n"
                         "0x5ff4:  0x00000000  0x00000000\n"
                         "0x5ffc:  0x00000000  0x00000000\n"
                         "0x6004:  0x00000000  0x00000000\n"
                         "(gdb) p &user_stack\n"
                         "$1 = (long (*)[1024]) 0x5000 <user_stack>\n"
                         "(gdb) p/x $esp\n"
                         "$2 = 0x5fec\n"
                         "\n"
                         "# 첫 워드 0x662c = L6 — main의 '복귀 주소'\n"
                         "# esp = user_stack 끝(0x6000) − 20",
                         "04-stack-dump-esp.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· $esp 첫 워드 = L6 복귀 주소(head.s:139-140 — main은 돌아오면 안 된다)\n"
         "· 이어 0, 0, 0 — main(void)의 가짜 인자 3개(head.s:136-138)\n"
         "· esp ≈ user_stack 끝 — sched.c:67-72 stack_start = {&user_stack[PAGE_SIZE>>2], 0x10}\n"
         "· head.s:23 lss _stack_start,%esp 가 이 스택을 로드(19장)\n\n"
         "p &user_stack 으로 '스택의 정체'를 확인한다.", 14)
    d.banner(p, "main의 스택은 user_stack — main을 'call'한 것은 setup_paging의 ret 한 줄이다")

    # 34 시연 B-1
    p = d.slide("시연 B-1: GDT 베이스 찾기", K.S_DEMO,
                "boot/head.s:222-229 — GDTR이 가리키는 곳이 &_gdt 인지 확인 · GDB 원격에서 GDTR 미노출 시 QEMU 모니터(§11)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "# QEMU 모니터 — Ctrl-Alt-2 (또는 -monitor stdio)\n"
                         "(qemu) info registers\n"
                         "EAX=00000000 EBX=00000000 …\n"
                         "GDT=     00005cb0  000007ff\n"
                         "IDT=     00005e00  000007ff\n"
                         "LDT=     00000000  00000000\n"
                         "TR =     00000060  00000068\n"
                         "\n"
                         "# GDB — 같은 곳을 가리키는가\n"
                         "(gdb) p &gdt\n"
                         "$1 = (desc_table *) 0x5cb0 <gdt>\n"
                         "# 0x5cb0 == GDTR base → 일치",
                         "05-gdt-base-monitor-vs-gdb.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "절차\n\n"
         "1. QEMU 모니터 info registers — GDT= 줄(base·limit)\n"
         "2. GDB p &gdt — 심볼 주소\n"
         "3. 두 값이 같은지 대조\n\n"
         "관찰(§5)\n"
         "· GDTR base == &gdt (head.s:229 .long _gdt)\n"
         "· limit 0x7ff = 256×8−1 (08장)\n\n"
         "GDB 원격 프로토콜은 GDTR을 직접 안 보여줄 수 있다 — 그래서 모니터를 함께 쓴다(§11).",
         14)
    d.banner(p, "GDTR = gdt_descr이 실은 6바이트 — 08장 코드의 실측 대조")

    # 35 시연 B-2
    p = d.slide("시연 B-2: x/8xw &gdt (main 진입 시점)", K.S_DEMO,
                "boot/head.s:232-238 — 원문 .quad와 1:1 대조 · 리틀엔디언 순서(낮은 dword 먼저) 주의")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) x/8xw &gdt\n"
                         "0x5cb0 <gdt>:    0x00000000  0x00000000\n"
                         "0x5cb8 <gdt+8>:  0x00000fff  0x00c09a00\n"
                         "0x5cc0 <gdt+16>: 0x00000fff  0x00c09200\n"
                         "0x5cc8 <gdt+24>: 0x00000000  0x00000000\n"
                         "\n"
                         "# [0] NULL      [3] TMP — 비어 있음\n"
                         "# [1] a=0x00000fff b=0x00c09a00\n"
                         "#     → 0x00c09a0000000fff (10·12장)\n"
                         "# [2] → 0x00c0920000000fff\n"
                         "# [4][5] 아직 0 — sched_init 전(36장)",
                         "06-gdt-dump-at-main.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· 워드 순서 = 리틀엔디언 — a(낮은 dword)가 먼저 인쇄된다\n"
         "· 항목 1·2의 8바이트가 head.s:234-237 의 .quad와 정확히 일치\n"
         "· 항목 4·5 = 0 — 아직 sched_init 전(다음 장에서 채워짐)\n\n"
         "12장 해독표를 덤프에 겹쳐 읽는다 — b:a 순서로 이어 붙이면 .quad 값.\n\n"
         "기대 출력 전체(§5): 0x00000000 0x00000000 0x00000fff 0x00c09a00 0x00000fff 0x00c09200 0x00000000 0x00000000",
         14)
    d.banner(p, "코드의 .quad가 메모리 덤프로 보인다 — 해독(12장)의 실측")

    # 36 시연 B-3
    p = d.slide("시연 B-3: sched_init 이후 GDT", K.S_DEMO,
                "kernel/sched.c:392-393(발췌) · include/asm/system.h:52-66 — 항목 4 TSS0(0x89) · 항목 5 LDT0(0x82) · 전후 비교")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) b sched_init\n"
                         "(gdb) c\n"
                         "Breakpoint 2, sched_init () at kernel/sched.c:NN\n"
                         "(gdb) finish\n"
                         "Value returned is void\n"
                         "(gdb) x/4xw &gdt[4]\n"
                         "0x5cd0 <gdt+32>:  0x0cd00068  0x00008900\n"
                         "0x5cd8 <gdt+40>:  0x0cc40068  0x00008200\n"
                         "\n"
                         "# [4] TSS0 — limit 0x68(=104) · type 0x89\n"
                         "# [5] LDT0 — type 0x82 (system.h:53·65-66)",
                         "07-gdt-dump-after-sched-init.png")
    d.text(p, 22000, 4150, 10000, 550, "전후 비교 — 10장 슬롯 그림", 14, K.TEAL, True)
    for i, (label, filled) in enumerate([("4 TSS0", True), ("5 LDT0", True)]):
        nbox(d, p, 22000 + i * 5100, 4800, 4900, 1900, label,
             "0 → 0x89/0x82" if filled else "", K.TEAL, s1=14, s2=11)
    para(d, p, 22000, 6750, 10000, 7600,
         "전(35장): gdt[4]·gdt[5] = 0\n후(이번): TSS0·LDT0 설명자가 채워짐\n\n"
         "· limit 0x68 = 104 = tss_struct 크기(system.h:53)\n"
         "· type 0x89 TSS available / 0x82 LDT(15장)\n"
         "· sched.c:392-393 set_tss_desc·set_ldt_desc 가 쓴 자리\n\n"
         "10장 슬롯 그림의 빈 칸 2개가 이 순간 채워진다.", 14)
    d.banner(p, "빈 칸 2개가 시스템 설명자로 채워진다 — 10장 슬롯 그림·15장 매크로의 실측")

    # 37 시연 C-1
    p = d.slide("시연 C-1: LDT 항목 읽기", K.S_DEMO,
                "include/linux/sched.h:125-126 — INIT_TASK ldt {0x9f,0xc0fa00}·{0x9f,0xc0f200} (13장 해독 대조)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) p/x init_task.task.ldt\n"
                         "$1 = {{a = 0x0, b = 0x0},\n"
                         "      {a = 0x9f, b = 0xc0fa00},\n"
                         "      {a = 0x9f, b = 0xc0f200}}\n"
                         "(gdb) x/6xw &init_task.task.ldt\n"
                         "0x5d94 <init_task+148>: 0x00000000  0x00000000\n"
                         "0x5d9c <init_task+156>: 0x0000009f  0x00c0fa00\n"
                         "0x5da4 <init_task+164>: 0x0000009f  0x00c0f200\n"
                         "\n"
                         "# ldt[1] cs — ldt[2] ds&ss (sched.h:104 주석)",
                         "08-init-task-ldt.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· ldt[1] {0x9f, 0xc0fa00} — cs\n"
         "· ldt[2] {0x9f, 0xc0f200} — ds&ss\n"
         "· 13장 해독표와 1:1 — base 0 · limit 640KB · DPL 3\n\n"
         "init_task는 심볼로 접근 — 구조체 배열을 통째로 인쇄한다.\n\n"
         "lab/에서 심볼명이 _init_task 등으로 다를 수 있음(§11) — 접두사 차이는 각주로 처리.",
         14)
    d.banner(p, "데이터 안의 설명자 — task_struct 안에 태스크의 LDT가 그대로 들어 있다(13장)")

    # 38 시연 C-2
    p = d.slide("시연 C-2: IDT 항목 읽기", K.S_DEMO,
                "sched_init 이후 · include/asm/system.h:22-40 — idt[0x80] 상위 0xEF00(DPL3·트랩) · idt[0x20] 0x8E00(인터럽트)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) x/2xw &idt[0x80]    # set_system_gate — DPL 3\n"
                         "0x5e80 <idt+1024>:  0x0008c69a  0x0000ef00\n"
                         "(gdb) x/2xw &idt[0x20]    # set_intr_gate — DPL 0\n"
                         "0x5f80 <idt+256>:   0x0008a2bc  0x00008e00\n"
                         "\n"
                         "# [0x80] 선택자 0x0008 · offset = system_call\n"
                         "#        상위 0xEF00 = P1 · DPL3 · type15 (트랩)\n"
                         "# [0x20] timer_interrupt · 0x8E00 = P1 · DPL0 · type14\n"
                         "#        → 인터럽트 게이트 (21·22장)",
                         "09-idt-entries-0x80-0x20.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· idt[0x80] 하위 워드의 상위 16비트 = 선택자 0x0008\n"
         "· 상위 워드 0xEF00 — P1·DPL3·type15\n"
         "   = set_system_gate(0x80, &system_call), sched.c:411\n"
         "· idt[0x20] 0x8E00 — P1·DPL0·type14 인터럽트 게이트\n"
         "   = set_intr_gate(0x20, &timer_interrupt), sched.c:409\n\n"
         "21장 비트 대응·22장 게이트 비교의 실측 — 같은 8바이트, 다른 DPL·type.",
         14)
    d.banner(p, "게이트 2종이 한 화면에 — 0xEF00(트랩·DPL3)과 0x8E00(인터럽트·DPL0)")

    # 39 시연 C-3
    p = d.slide("시연 C-3: 선택자 로드 추적", K.S_DEMO,
                "선택 항목 — boot/head.s:17-31 · b *0 부근(페이징 전)은 불안정할 수 있다(§11) · 실패 시 사전 캡처로 전환")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) b *0            # 또는 lab의 startup 심볼\n"
                         "(gdb) c\n"
                         "0x00000000 in ?? ()\n"
                         "(gdb) info registers ds   # head.s:19 실행 전\n"
                         "ds    0x0    0\n"
                         "(gdb) si              # movl $0x10,%eax\n"
                         "(gdb) si              # mov %ax,%ds ← 실행\n"
                         "(gdb) info registers ds\n"
                         "ds    0x10   16           # 값만 바뀐다\n"
                         "\n"
                         "# base/limit 캐시 변화는 여전히 보이지 않는다 (19장)",
                         "10-heads-segment-reload.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· ds 0 → 0x10 — '보이는 값'만 바뀐다\n"
         "· base/limit 캐시 — info registers 어디에도 없음\n\n"
         "19장 상태도 1 확인: 보이는 선택자는 바뀌고, 숨은 세그먼트 캐시는 보이지 않는다.\n\n"
         "주소 0 근처 중단은 페이징 전이라 GDB가 불안정할 수 있다 — 실패 시 사전 캡처로 전환(선택 항목, §11).",
         14)
    d.banner(p, "값은 보이고 캐시는 안 보인다 — 19장 상태도의 체감")

    # ── 배경 40 · 정답 41–42 · 정리 43 · 확인 44 · 정리 45–46 ─
    # 40 관찰 vs 추론
    p = d.slide("관찰 vs 추론", K.S_BG,
                "§8 — 세그먼트 캐시 갱신·CPU의 push 순서·권한 검사는 GDB로 직접 본 것이 아니다")
    d.table(p, 1100, 4400, [15750, 15750], [
        ["관찰 — 캡처로 본 것 (31–39장)", "추론 — 소스·아키텍처 문서 근거"],
        ["레지스터 값 — cs 0x0008 · ds 0x0010 · cr0 · eflags (32장)",
         "세그먼트 캐시의 갱신 시점 (19장 — head.s:26-31 재로드 코드)"],
        ["스택 메모리 — L6 복귀 주소 · 0,0,0 (33장)",
         "CPU의 push 순서 SS,ESP,EFLAGS,CS,EIP (24장 — 386 문서)"],
        ["GDT·LDT·IDT 메모리 덤프 (35–38장)",
         "권한 검사 max(CPL,RPL) ≤ DPL 등 (23장 — 명세)"],
        ["선택자 값 변화 ds 0 → 0x10 (39장)",
         "페이징 선형→물리 동작 (07회차)"],
    ], row_h=1250, size=14)
    para(d, p, 1100, 11100, 31500, 3000,
         "말할 때 구분한다 — '우리가 본 것' / '코드가 그렇게 쓰여 있다' / '아키텍처가 그렇게 정의한다'.\n"
         "'0.11 사용자 주소 = 물리 주소' 같은 단정도 금지 — 페이징은 오늘 범위 밖이다(§8).", 15)
    d.banner(p, "관찰은 정확히, 추론은 근거를 밝혀서 — 이 구분이 앞으로의 실습 태도가 된다")

    # 41 답 1
    p = d.slide("답 1: 선택자가 주소가 되는 법", K.S_ANS,
                "06·11–12·18장 종합 — include/linux/sched.h:123-133 · kernel/fork.c:54-55 (06회차 예고)")
    chain = [
        ("0x17 : 0x1234", "논리 주소"),
        ("index 2 · TI=1", "LDTR → 현재 LDT"),
        ("LDT[2].base", "설명자에서 base"),
        ("base + 0x1234", "= 선형 주소"),
        ("CR3 · 페이지 테이블", "07회차"),
    ]
    for i, (t, s) in enumerate(chain):
        x = 1100 + i * 6350
        nbox(d, p, x, 4400, 5750, 2700, t, s,
             None if i == 4 else K.PAPER, K.ORANGE,
             edge=K.ORANGE if i == 4 else None, s1=14, s2=11)
        if i < 4:
            d.text(p, x + 5800, 5400, 600, 900, ">", 26, K.TEAL, True)
    d.cards(p, [
        ("task 0 (init)",
         "LDT base = 0 — INIT_TASK ldt\n(b=0xc0fa00 · 0xc0f200)\n\n"
         "선형 주소 = 오프셋 그대로 · 640KB"),
        ("다른 태스크 (fork)",
         "base = nr × 0x4000000 (64MB 칸)\n\n"
         "fork.c:54-55 set_base(p->ldt[1..2])\n— 06회차가 읽는다"),
    ], y=7500, h=5600)
    d.banner(p, "선택자는 색인 → 설명자가 base → base+오프셋 = 선형 주소 — 핵심 질문 1의 답")

    # 42 답 2
    p = d.slide("답 2: 멈춘 커널에서 보이는 것", K.S_ANS,
                "시연 A·B·C 관찰 종합 — 40장의 구분(관찰/추론) 그대로")
    d.table(p, 1100, 4400, [15750, 15750], [
        ["보이는 것", "보이지 않는 것"],
        ["레지스터 — 선택자(cs·ds) · CR0 · EFLAGS (32장)",
         "세그먼트 캐시 — base·limit·속성 (19·39장)"],
        ["스택 — 복귀 주소 · 인자 (33장)",
         "TLB — 페이지 변환 캐시 (07회차)"],
        ["설명표 — GDT·LDT·IDT 메모리 덤프 (35–38장)",
         "CPU 내부 권한 검사 과정 (23장 — 결과만 폴트로 보임)"],
    ], row_h=1300, size=14)
    para(d, p, 1100, 10100, 31500, 3400,
         "GDB가 보여주는 것은 메모리와 레지스터의 '보이는 값' — CPU 안에 숨은 상태(캐시·TLB)는 "
         "소스와 아키텍처 명세로 추론한다(§8).\n"
         "그래서 오늘은 코드 읽기(08–24장)와 관찰(31–39장)을 짝지어 진행했다.", 15)
    d.banner(p, "핵심 질문 2의 답 — 보이는 것은 값, 숨는 것은 상태(캐시·TLB)")

    # 43 다음 회차와의 연결
    p = d.slide("다음 회차와의 연결", K.S_WRAP,
                "03회차 — setup.s 임시 GDT → head.s GDT → sched_init TSS/LDT · 04회차 — 게이트를 '통과'하는 순간")
    d.flow(p, [("setup.s", "임시 gdt · idt_48 · gdt_48\n(09장)"),
               ("head.s", "setup_idt · setup_gdt\n본 표 (08·10장)"),
               ("main → sched_init", "TSS0·LDT0 설치\nltr·lldt (15·36장)"),
               ("03회차", "이 순서를 시간축으로\n재배열한다")],
           y=4500, h=3100, title_size=17)
    d.cards(p, [
        ("03회차 — 표는 언제 만들어지는가",
         "\"부트 섹터 512바이트에서 main()까지\nCPU 상태는 어떻게 바뀌는가?\"\n"
         "오늘의 표들이 순서대로 놓인다"),
        ("04회차 — 게이트를 통과하는 순간",
         "인터럽트·예외 프레임의 실체\n24장 상태도가 코드가 된다\n(system_call.s · traps.c)"),
    ], y=8100, h=5300)
    d.banner(p, "02→03 — 설명표가 '무엇'인지 해독했다 → 그 표들이 '언제' 만들어지는지 따라간다")

    # 44 이해 확인 질문 (6문항 정답 포함)
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "6문항 — 정답 포함, 원문 그대로(계획 §6) · 근거 슬라이드 번호 병기 · 개인 묵상 후 함께 풀이")
    quiz = [
        ("Q1", "선택자 0x17을 index/TI/RPL로 나누면? — index 2, TI=1(LDT), RPL=3. (0001 0111b)"),
        ("Q2", "lgdt를 실행하면 DS가 가리키는 세그먼트의 base가 바로 바뀌는가? — 아니오. "
                "세그먼트 레지스터를 다시 로드해야 캐시가 갱신된다(head.s:26-31). (근거 슬라이드 19)"),
        ("Q3", "0x00c09a0000000fff에서 limit는 몇 바이트인가? — 0xfff+1 페이지 × 4KB = 16MB (G=1). (근거 슬라이드 12)"),
        ("Q4", "set_system_gate와 set_trap_gate의 유일한 차이는? — DPL 3 vs 0 (system.h:36-40). "
                "둘 다 type 15(트랩 게이트). (근거 슬라이드 21·22)"),
        ("Q5", "CPL3에서 int $0x80으로 진입할 때 커널 스택 포인터는 어디서 오는가? — 현재 태스크 TSS의 "
                "ss0/esp0 (sched.h:53-54). (근거 슬라이드 17·24)"),
        ("Q6", "GDB info registers에서 보이지 않는 세그먼트 정보는? — 설명자 캐시(base/limit/attr). "
                "선택자 값만 보인다. (근거 슬라이드 19·42)"),
    ]
    for i, (tag, body) in enumerate(quiz):
        col, row = i % 2, i // 2
        qbox(d, p, 1100 + col * 16100, 4250 + row * 3350, 15400, 3150, tag,
             body, K.TEAL if tag in ("Q1", "Q3", "Q5") else K.ORANGE, 13)
    d.banner(p, "여섯 문항 전부 오늘 밟은 길 안에 있다 — 틀린 문항은 근거 슬라이드로 돌아간다")

    # 45 정리
    p = d.slide("정리", K.S_WRAP,
                "선택자→설명자→base · 세 표 · 게이트 3종 · 권한 3필드 · GDB 5명령 — 오늘 전체 요약")
    d.table(p, 1100, 4400, [6300, 25200], [
        ["주제", "한 줄 정리"],
        ["선택자", "16비트 = index(13)·TI(1)·RPL(2) — 표의 색인, 주소가 아니다 (06장)"],
        ["설명자", "8바이트 — base 32·limit 20·G·DPL·S·type, 필드는 흩어져 있다 (11–12장)"],
        ["세 표", "GDT(전역) · LDT(태스크별) · IDT(벡터) — lgdt·lldt·lidt (07장)"],
        ["게이트 3종", "태스크 5(미사용) · 인터럽트 14(IF 클리어) · 트랩 15 — 0x8E00·0xEF00 (20–22장)"],
        ["권한 3필드", "CPL(현재) · DPL(문턱) · RPL(요청) — 게이트 DPL 3이 int 0x80을 연다 (23장)"],
        ["GDB 5명령", "b · c · si/n · bt · finish + 관찰 info registers·x·p (27–28장)"],
    ], row_h=1300, size=14)
    d.banner(p, "두 핵심 질문에 답했다 — 선택자→설명자→base·선형 주소 / 멈춘 커널의 보이는 것과 숨은 것")

    # 46 03회차 예고
    p = d.slide("03회차 예고", K.S_WRAP,
                "course-plan 03 절 — 파트 A «입문·부팅»의 마지막 회차")
    d.text(p, 1100, 4700, 31500, 3900,
           "\"부트 섹터 512바이트에서 main()까지\nCPU 상태는 어떻게 바뀌는가?\"",
           30, K.ORANGE, True)
    para(d, p, 1100, 9100, 31500, 2600,
         "03회차가 오늘의 표들에 시간축을 얹는다 — setup.s 임시 GDT → head.s GDT·IDT → sched_init TSS/LDT.\n"
         "04회차는 게이트를 '통과'하는 순간 — 오늘 24장 상태도가 코드가 된다.", 17)
    auto_pane(d, p, 1100, 12100, 31500, 2300, "미리 볼 파일 (03회차)",
              "boot/bootsect.s · boot/setup.s · boot/head.s · init/main.c", start=14)
    d.banner(p, "02→03 — 설명표의 '무엇'을 읽었다 → '언제' 만들어지는지 따라간다")


if __name__ == "__main__":
    K.run(globals())
