#!/usr/bin/env python3
"""03회차 덱 — 부팅과 커널 초기화 (output/03-boot-init.pptx)

계획: materials/slide-plans/03-boot-init.md (§2 표 47행 1:1 · §3 앞부분 명세 ·
§4 상태 변화 표 12행 상세 명세 · §5 캡처 9종 · §6 이해 확인 6문항 · §8 오해 금지).
캡처 미확보 — 캡처 슬라이드는 placeholder_output(기대 출력), 슬라이드 11만
build/boot.png 를 tag="기존 기록"으로 사용(부팅 회차 특례, 00-common §7).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="03", total=47, slug="03-boot-init",
    part_no="A", part="«입문·부팅»",
    title="03. 부팅과 커널 초기화",
    question="부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?",
    done=2,
    today_line="부트 섹터 512바이트에서 main()까지 —\n네 비트 PE/PG/IF/CPL이 어느 명령에서 바뀌는지 줄 번호로 추적한다",
    next_lines=[
        "02 → 03   02: 선택자·GDT라는 표의 구조를 익혔다 → 03: 그 표가 만들어지는 때를 본다 — setup.s 임시 표와 head.s의 표, '같은 표를 두 번 만드는' 이유까지",
        "03 → 04   03: main()이 초기화를 마치고 move_to_user_mode로 셸이 살아난다 → 04: 게이트 통과 — 셸의 write가 도착할 곳 = 오늘 sched_init이 연 게이트 0x80",
    ],
    road_note=("이 회차는 10단계 전부를 밟는다 — 상태도 19·25·36 · 비교 07·31·32 · 시연 37-42 · "
               "정답 45 · 확인 44.\n강의 끝에 상태 변화 표(36)와 GDB 시연 A/B/C로 네 비트 "
               "PE/PG/IF/CPL의 전환을 눈으로 확인한다."),
    STRUCT=dict(
        teal=["main"],
        today=[("boot/bootsect.s", "0x7c00→0x90000"),
               ("boot/setup.s", "0x90200 · PE=1"),
               ("boot/head.s", "0x0 · PG=1")],
        flow="int 0x19 → bootsect.s → setup.s → head.s → main()",
        up="↑ fork/exec → 셸",
        user="init · sh — move_to_user_mode 뒤 셸",
    ),
)

CHECKS = dict(
    captions={
        5: "src/Makefile:41-43",
        6: "src/boot/bootsect.s:34-43",
        7: "src/boot/bootsect.s:151-196",
        9: "src/boot/bootsect.s:46-62",
        10: "src/boot/bootsect.s:67-79",
        11: "src/boot/bootsect.s:92-110",
        12: "src/boot/bootsect.s:151-196",
        13: "src/boot/bootsect.s:117-139",
        14: "src/boot/setup.s:36-105",
        15: "src/boot/setup.s:113-126",
        16: "src/boot/setup.s:205-224",
        17: "src/boot/setup.s:138-144",
        18: "src/boot/setup.s:191-193",
        20: "src/boot/head.s:17-36",
        22: "src/boot/head.s:43-65",
        23: "src/boot/head.s:135-144",
        24: "src/boot/head.s:198-218",
        28: "src/mm/memory.c:399-411",
        29: "src/kernel/traps.c:181-208",
        30: "src/kernel/sched.c:385-412",
    },
    required=[
        "0xAA55", "SYSSIZE", "jmpi 0,8", "lmsw", "A20", "identity mapping",
        "LATCH", "ignore_int", "mem_init", "trap_init", "sched_init",
        "buffer_init", "move_to_user_mode", "EXT_MEM_K", "_syscall0", "L6",
        "PE 1회", "PG 1회", "IF 2회", "CPL 1회",
    ],
    prereq=[
        ("0xAA55", "src/boot/bootsect.s:34-43"),
        ("INITSEG", "src/boot/bootsect.s:46-62"),
        ("jmpi", "src/boot/bootsect.s:117-139"),
        ("lmsw", "src/boot/head.s:43-65"),
        ("CR3", "src/mm/memory.c:399-411"),
        ("cli", "src/kernel/sched.c:385-412"),
    ],
    structure_nodes=["bootsect.s", "setup.s", "head.s", "main.c",
                     "system_call.s", "IRQ"],
    capture_slides=[11, 38, 40, 42],
)


# ── 로컬 도우미 (deckkit 불변) ─────────────────────────────────
def wrap_kr(text, width, size):
    """CJK 포함 텍스트를 width(1/100mm) 안에서 줄바꿈한다.
    ASCII 식별자 중간에서는 끊지 않는다 — 넘칠 때 마지막 공백에서 끊는다."""
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


def cards_fit(d, p, cards, y=4700, h=8500, body=18):
    """deckkit.cards 와 같은 카드 3열 — 본문 크기 지정 가능(43·46장용).
    본문 줄수×body×52 ≤ h-2800 이 되도록 호출 쪽에서 h·body를 정한다."""
    gap, total = 600, 31500
    width = (total - gap * (len(cards) - 1)) // len(cards)
    for i, (title, btxt) in enumerate(cards):
        x = 1100 + i * (width + gap)
        d.shape(p, x, y, width, h, K.PAPER)
        d.shape(p, x, y, width, 150, K.TEAL if i % 2 == 0 else K.ORANGE)
        tsize = K.fit_size(title, 21, width - 1100)
        d.text(p, x + 550, y + 650, width - 1100, 1600, title, tsize, K.INK, True)
        d.text(p, x + 550, y + 2600, width - 1100, h - 2800, btxt, body, K.INK)


def cp(d, p, path, s, e, x, y, w, size=11, extra="", h=None):
    """code_panel 래퍼 — 킷과 같은 높이 공식으로 자동 산출."""
    n = e - s + 1
    hh = h if h else 1750 + n * size * 55
    d.code_panel(p, path, s, e, x, y, w, hh, size=size, caption_extra=extra)
    return hh


def state_table(d, p, x, y, widths, rows, row_h=780, size=12, hl=frozenset()):
    """§4 상태 변화 표 렌더러 — 값이 바뀌는 칸(hl)만 TEAL 굵게, 나머지 MUTED.
    빈 칸은 '〃'(이전 행과 동일)으로 회색 처리."""
    for r, row in enumerate(rows):
        head = r == 0
        fill = K.TEAL if head else (0x183340 if r % 2 else 0x142E3A)
        cx = x
        for c, cell in enumerate(row):
            d.shape(p, cx, y + r * row_h, widths[c], row_h, fill)
            txt = cell if cell else "〃"
            on = (r, c) in hl
            col = K.INK if head else (K.TEAL if on else K.MUTED)
            csize = K.fit_size(txt, size, widths[c] - 460, min_size=8)
            d.text(p, cx + 230, y + r * row_h + (row_h - 680) // 2,
                   widths[c] - 460, 680, txt, csize, col, head or on)
            cx += widths[c]


STATE_COLS = [5800, 1500, 1500, 1500, 1900, 5400, 5400, 8500]
# 36장용 좁은 열 — 왼쪽 타임라인(2800) 옆 28700 폭
STATE_COLS_NARROW = [5200, 1400, 1400, 2400, 1500, 5000, 4900, 6900]


def state_rows(first, last):
    """§4 종합 12행 표에서 행 번호(1-based, 헤더 제외) first..last 발췌."""
    rows = [
        ["단계", "PE", "PG", "IF", "CPL", "CS:EIP 위치", "스택", "전환 원인(줄)"],
        ["BIOS → bootsect 진입", "0", "0", "1", "— (real)", "0x07c0:0",
         "BIOS 것", "int 0x19"],
        ["bootsect 이동 후", "0", "0", "1", "—", "0x9000:go",
         "0x9000:0xFF00", "bootsect.s:56,61-62"],
        ["setup 진입", "0", "0", "1", "—", "0x9020:0", "", "bootsect.s:139"],
        ["setup cli", "0", "0", "0", "—", "", "", "setup.s:109"],
        ["setup lmsw", "1", "0", "0", "0", "0x9020:…", "", "setup.s:191-192"],
        ["jmpi 0,8", "1", "0", "0", "0", "0x0008:0", "아직 없음", "setup.s:193"],
        ["head lss _stack_start", "1", "0", "0", "0", "",
         "0x10:user_stack 끝", "head.s:23"],
        ["head setup_paging", "1", "1", "0", "0", "", "", "head.s:214-217"],
        ["main() 진입", "1", "1", "0", "0", "0x0008:main", "L6,0,0,0 위",
         "head.s:218 ret"],
        ["sti()", "1", "1", "1", "0", "", "", "main.c:136"],
        ["move_to_user_mode", "1", "1", "1", "3", "0x000f:1f",
         "0x17:같은 esp", "system.h:2-8"],
        ["fork() 진입", "1", "1", "0(게이트) → 1", "0 → 3", "", "TSS esp0",
         "main.c:138, unistd.h:137"],
    ]
    return [rows[0]] + rows[first:last + 1]


# 값이 바뀌는 칸(행, 열) — 헤더 제외 데이터 행 번호(1-12)
STATE_HL = {(2, 5), (2, 6), (3, 5), (4, 3), (5, 1), (5, 4), (6, 5), (6, 6),
            (7, 6), (8, 2), (9, 5), (9, 6), (10, 3), (11, 4), (11, 5),
            (11, 6), (12, 3), (12, 4), (12, 6)}


def populate(d):
    # ── 배경 05–08 ────────────────────────────────────────────
    # 05 디스크 이미지의 배치
    p = d.slide("디스크 이미지의 배치", K.S_BG,
                "Makefile:41-43 — tools/build가 bootsect·setup·system을 이 순서로 Image에 기록한다")
    cp(d, p, "src/Makefile", 41, 43, 1100, 4400, 14500, size=8,
       extra="Image 빌드 규칙")
    cp(d, p, "src/boot/bootsect.s", 249, 253, 1100, 7900, 14500, size=11,
       extra=".org 508 — root_dev·boot_flag")
    nbox(d, p, 17000, 4400, 15600, 2300, "섹터 1 — bootsect",
         "510바이트 코드+데이터 · .org 508 root_dev(508-509)\n"
         "boot_flag 0xAA55(511-512) — 부트 섹터 서명", K.PAPER, s1=17, s2=12)
    nbox(d, p, 17000, 6900, 15600, 1900, "섹터 2-5 — setup",
         "SETUPLEN = 4섹터(bootsect.s:34)", K.PAPER, s1=15, s2=12)
    nbox(d, p, 17000, 9000, 15600, 1900, "섹터 6부터 — system",
         "head.s + main.c … · SYSSIZE 0x3000 클릭 = 0x30000 바이트(196kB) 한계",
         K.PAPER, s1=15, s2=12)
    badge(d, p, 17000, 11100, 15600, "BIOS는 섹터 1만 읽어 0x7c00에 내려놓는다",
          K.TEAL, 800, 14)
    para(d, p, 1100, 12900, 14500, 1600,
         "나머지 두 덩어리는 bootsect가 스스로 읽어 올린다(09-13장).", 15)
    d.banner(p, "오늘 강의 = 이 세 덩어리가 각각 어디로 옮겨져 실행되는가", 14800, 19)

    # 06 메모리 지도 (적재 전후)
    p = d.slide("메모리 지도 (적재 전후)", K.S_BG,
                "src/boot/setup.s:113-126 — setup이 system을 0x00000으로 이동 · 스택 0x9000:0xFF00")
    cp(d, p, "src/boot/bootsect.s", 34, 43, 1100, 4400, 12000, size=11,
       extra="적재 주소 상수")
    para(d, p, 1100, 12400, 12000, 2000,
         "INITSEG 0x9000 · SETUPSEG 0x9020 · SYSSEG 0x1000 —\n"
         "즉 0x90000 · 0x90200 · 0x10000. ENDSEG = SYSSEG + SYSSIZE.", 14)
    d.text(p, 13800, 4150, 9000, 550, "적재 전 (BIOS 직후)", 15, K.TEAL, True)
    nbox(d, p, 15600, 4800, 7300, 1900, "0x07c00 bootsect 512B",
         "BIOS가 내려놓음", K.PAPER, s1=13, s2=11)
    nbox(d, p, 15600, 6900, 7300, 850, "0x10000 (빈)", None, None, K.MUTED,
         s1=12)
    nbox(d, p, 15600, 7900, 7300, 850, "0x90000 (빈)", None, None, K.MUTED,
         s1=12)
    nbox(d, p, 15600, 8900, 7300, 850, "0x00000 (빈)", None, None, K.MUTED,
         s1=12)
    d.text(p, 23200, 4150, 9400, 550, "적재 후 (bootsect+setup 완료)", 15,
           K.TEAL, True)
    nbox(d, p, 23400, 4800, 9100, 2450, "0x90000 bootsect + 0x90200 setup",
         "0x90000-0x901FF는 뒤에\nBIOS 파라미터 영역(14장)", K.PAPER,
         s1=13, s2=11)
    nbox(d, p, 23400, 7450, 9100, 1900, "0x9FF00 스택",
         "0x9000:0xFF00 (bootsect.s:61-62)", K.PAPER, s1=13, s2=11)
    nbox(d, p, 23400, 9550, 9100, 1900, "0x10000 system (SYSSEG)",
         "read_it가 쌓는다", K.TEAL, s1=13, s2=11)
    nbox(d, p, 23400, 11650, 9100, 1900, "0x00000 ← system 이동 예정",
         "setup do_move(15장)", None, K.ORANGE, s1=13, s2=11, edge=K.ORANGE)
    d.banner(p, "0x7c00는 잠시 머물러 가는 자리 — 세 덩어리의 최종 주소가 오늘의 지도", 14800, 18)

    # 07 적재 단계 비교 (비교 1)
    p = d.slide("적재 단계 비교", K.S_CMP,
                "비교 1 — 세 단계는 저마다 다른 세그먼트에서, 다른 적재자에 의해, 다른 모드로 실행된다")
    d.table(p, 1100, 4400, [3600, 6600, 6600, 5400, 4600, 4700], [
        ["단계", "적재 주소", "적재자", "크기 제한", "실행 모드", "어셈블러"],
        ["bootsect", "0x07c0 → 0x9000\n(0x7c00→0x90000)",
         "BIOS(int 0x19)가 내려놓고\n스스로 0x90000으로 복사",
         "512바이트\n(510 + 0xAA55)", "16비트 real", "as86"],
        ["setup", "0x9020 (=0x90200)",
         "bootsect — int 0x13\n서비스 2, 4섹터", "SETUPLEN 4섹터",
         "16비트 real", "as86"],
        ["system", "0x1000 → 0x0000\n(0x10000→0x00000)",
         "bootsect read_it 적재 +\nsetup do_move 이동",
         "SYSSIZE 0x3000 클릭\n= 0x30000 바이트", "32비트 protected",
         "GNU as"],
    ], row_h=1900, size=14)
    para(d, p, 1100, 12200, 31500, 1000,
         "근거: src/boot/bootsect.s:151-196 (read_it) · src/boot/setup.s:113-126 (do_move) — "
         "상수는 bootsect.s:34-43, 적재는 67-79·117-139.", 14)
    d.banner(p, "같은 '적재'라도 셋 다르다 — 누가 옮기는가, 어디로, 몇 바이트까지", 13400, 18)

    # 08 추적 대상 네 비트 다시 보기
    p = d.slide("추적 대상 네 비트 다시 보기", K.S_BG,
                "1회차 18장 참조표 재게시 — 이 네 비트가 상태 표(19·25·36)의 열 머리글이다")
    d.table(p, 1100, 4400, [3200, 4700, 16600, 7000], [
        ["비트", "어디에", "어느 명령이 바꾸는가 (파일:줄)", "오늘 횟수"],
        ["PE", "CR0 비트0", "lmsw ax — setup.s:192", "1회"],
        ["PG", "CR0 비트31", "orl $0x80000000,%eax → movl %eax,%cr0 — head.s:216-217", "1회"],
        ["IF", "EFLAGS 비트9", "cli — setup.s:109 (1→0) · sti — main.c:136 (0→1)", "2회"],
        ["CPL", "CS 하위 2비트(RPL)", "iret — system.h:5 pushl $0x0f (0→3)", "1회"],
    ], row_h=1500, size=15)
    para(d, p, 1100, 12000, 31500, 2300,
         "강의 중 상태 표를 다시 열 때마다 이 네 비트를 세어 본다 — 오늘 안에 바뀌는 횟수는 "
         "딱 정해져 있다(종합 표 36장에서 확인). IF는 표시 지점의 값으로 읽는다.", 16)
    d.banner(p, "추적 대상 네 비트 — PE 1회 · PG 1회 · IF 2회 · CPL 1회", 14800, 19)

    # ── 코드 09–13: bootsect.s ────────────────────────────────
    # 09 자기 복사
    p = d.slide("bootsect.s: 자기 복사", K.S_CODE,
                "주석 bootsect.s:10-11 — system을 0x10000에 적재하려면 자리를 비켜야 한다")
    d.text(p, 1100, 4050, 12000, 350,
           "발췌 — src/boot/bootsect.s:46-62", 12, K.TEAL, True)
    cp(d, p, "src/boot/bootsect.s", 46, 56, 1100, 4400, 12000, size=11,
       extra="rep movw — 512바이트 복사")
    cp(d, p, "src/boot/bootsect.s", 57, 62, 13900, 4400, 8700, size=10,
       extra="go: — 세그먼트 재설정")
    para(d, p, 13900, 9600, 8700, 3200,
         "go: — CS=0x9000 기준으로 다시 실행\n스택 ss:sp = 0x9000:0xFF00\n"
         "(0x9FF00 — 512바이트 위, 임의값)", 14)
    nbox(d, p, 1100, 12900, 4800, 1800, "0x07c0:0x0000", "복사 원본",
         None, K.MUTED, s1=14, s2=10)
    arrow(d, p, 6100, 13250, "→", 22)
    nbox(d, p, 7500, 12900, 5600, 1800, "0x9000:go", "복사본 — 이후 여기서 실행",
         K.PAPER, K.TEAL, s1=14, s2=10)
    para(d, p, 13300, 12900, 19200, 1600,
         "rep movsw 256워드 = 512바이트 전체\njmpi go,INITSEG — CS까지 갱신", 14)
    d.banner(p, "자기 복사 후 원래 자리 0x7c00는 버려진다", 14800, 18)

    # 10 setup 적재
    p = d.slide("bootsect.s: setup 적재", K.S_CODE,
                "bootsect.s:21-23 주석 — 계속 읽기 실패하면 'Reboot by hand'(무한루프)")
    d.code(p, "src/boot/bootsect.s", 67, 79,
           "int 0x13 ah=2 — 디스크 읽기 서비스\nES:BX = 0x9000:0x0200 = 0x90200\n"
           "섹터 2부터 SETUPLEN 4개\n\n실패해도(jnc 실패) ah=0 리셋 후\n"
           "그대로 재시도 — 실패 처리가 없는\n최소 코드다", expl_size=16)
    d.banner(p, "BIOS 서비스 int 0x13은 real mode에서만 쓸 수 있다 — 지금이 마지막 기회", 14800, 18)

    # 11 "Loading system ..."
    p = d.slide('bootsect.s: "Loading system ..."', K.S_CODE,
                "캡처: build/boot.png (기존 기록) — lab/ 빌드 · QEMU i386 · 캡처 날짜는 파일 기준")
    d.picture(p, str(K.ROOT / "build/boot.png"), 1100, 4400, 12800, 10100,
              tag="기존 기록")
    d.text(p, 14600, 4150, 16800, 550,
           "발췌 — src/boot/bootsect.s:92-110 · msg1 원문 244-247", 14, K.TEAL, True)
    cp(d, p, "src/boot/bootsect.s", 92, 102, 14600, 4750, 8100, size=8,
       extra="① 커서 읽고 문자열 출력")
    cp(d, p, "src/boot/bootsect.s", 104, 110, 22900, 4750, 8100, size=8,
       extra="② read_it 개시")
    pane(d, p, 14600, 11600, 16400, 1800, "msg1 — bootsect.s:244-247",
         '13,10 "Loading system ..." 13,10,13,10', 12)
    para(d, p, 14600, 13600, 16400, 1000,
         "int 0x10 ah=0x03(커서) · ah=0x13(문자열) — 화면 출력도 BIOS다", 13)
    d.banner(p, "이 문자열이 보이면 bootsect가 살아 움직이고 있다는 뜻", 14800, 17)

    # 12 read_it 흐름
    p = d.slide("bootsect.s: system 적재 루프 read_it", K.S_CODE,
                "강사 참조 흐름도 — src/boot/bootsect.s:151-196 전체를 읽지 않고 구조만 짚는다")
    d.flow(p, [("sread·head·track", "상태 변수 (147-149)"),
               ("64KB 경계 검사", "test ax,#0x0fff (152-154)"),
               ("read_track", "int 0x13 한 트랙씩 (198-226)"),
               ("ES += 0x1000", "다음 64KB (192-194)"),
               ("ENDSEG → ret", "적재 완료 (158-160)")],
           y=4400, h=2700)
    cp(d, p, "src/boot/bootsect.s", 151, 160, 1100, 7400, 12000, size=9,
       extra="진입 검사 · 루프 머리")
    cp(d, p, "src/boot/bootsect.s", 192, 196, 13900, 7400, 8700, size=10,
       extra="ES가 0x1000씩 전진")
    para(d, p, 13900, 11900, 8700, 2600,
         "한 트랙씩 읽어 bx가 넘치면\nES += 0x1000 — 64KB 단위로\nsystem을 0x10000 위에 쌓는다",
         14)
    d.banner(p, "read_it = 'ES가 0x1000씩 전진'하는 이중 루프 — 디스크 지오메트리 추적은 읽지 않는다", 14700, 17)

    # 13 루트 장치와 setup 점프
    p = d.slide("bootsect.s: 루트 장치와 setup 점프", K.S_CODE,
                "root_dev 저장: bootsect.s:249-253 (.org 508 → 0x901FC) — 원문 src/boot/bootsect.s:117-139")
    cp(d, p, "src/boot/bootsect.s", 117, 127, 1100, 4400, 12000, size=10,
       extra="root_dev 결정")
    cp(d, p, "src/boot/bootsect.s", 128, 139, 13900, 4400, 8700, size=9,
       extra="undef_root · jmpi")
    para(d, p, 1100, 12500, 12000, 2100,
         "root_dev==0이면 sectors(15/18)로 플로피 종류 결정 — 1.2Mb(0x0208)·1.44Mb(0x021c)\n"
         "둘 다 아니면 undef_root 무한루프 · 결정값은 0x901FC(.org 508)",
         14)
    nbox(d, p, 13900, 12400, 8700, 1500, "jmpi 0,SETUPSEG",
         "CS=0x9020 · EIP=0 — 여전히 real mode, IF=1", K.PAPER, K.TEAL,
         s1=15, s2=11)
    d.banner(p, "bootsect의 임무 종료 — 제어는 setup으로", 14800, 18)

    # ── 코드 14–18: setup.s ───────────────────────────────────
    # 14 BIOS에게 묻기
    p = d.slide("setup.s: BIOS에게 묻기", K.S_CODE,
                "원문 src/boot/setup.s:36-105 — 0x90000-0x901FF는 bootsect가 있던 '안전한 장소'(주석 8-12)")
    d.table(p, 1100, 4400, [9200, 3100, 12800, 6400], [
        ["BIOS 서비스", "저장", "main.c / 소비자", "줄"],
        ["int 0x10 ah=03 — 커서 위치", "[0]", "ORIG_X·ORIG_Y — con_init(console.c)", "setup.s:36-41"],
        ["int 0x15 ah=0x88 — 확장 메모리 kB", "[2]", "EXT_MEM_K 0x90002 (main.c:58)", "setup.s:43-47"],
        ["int 0x10 ah=0f·12 — 비디오", "[4..12]", "ORIG_VIDEO_* — tty.h 테이블", "setup.s:49-63"],
        ["int 0x41 벡터 — hd0 파라미터 16B", "[0x80]", "DRIVE_INFO 0x90080 (main.c:59)", "setup.s:65-75"],
        ["int 0x46 벡터 — hd1 (int 0x13으로 존재 확인)", "[0x90]", "hd.c — 없으면 0으로 지움", "setup.s:77-104"],
    ], row_h=1050, size=13)
    cp(d, p, "src/init/main.c", 58, 60, 1100, 11100, 14500, size=10,
       extra="main.c가 읽는 매크로")
    para(d, p, 16200, 11100, 16400, 3400,
         "왜 지금 모아두는가 — protected 모드로 넘어가면 BIOS 호출이 불가능하다"
         "(setup.s:146-152·181-182 주석).\n\nsetup이 남긴 값은 main()이 맨 먼저 읽는다(26장).",
         15)
    d.banner(p, "BIOS 작별 인사 — 필요한 정보를 전부 긁어 두고 넘어간다", 14800, 18)

    # 15 cli와 system 이동
    p = d.slide("setup.s: cli와 system 이동", K.S_CODE,
                "왜 0으로: head.s:10-12 주석 — startup은 0x00000000, 그 자리에 페이지 디렉터리도 생긴다")
    d.code(p, "src/boot/setup.s", 113, 126,
           "setup.s:109 cli — IF=0\nBIOS 인터럽트 이제 사용 불가\n\n"
           "do_move — 64KB씩 앞으로 복사\nds(원본 0x10000+) → es(0x0000+)\n"
           "0x9000 직전까지(cmp ax,#0x9000)", expl_size=16)
    d.banner(p, "cli(109) → do_move(113-126) → head.s가 기다리는 주소 0으로", 14800, 18)

    # 16 임시 GDT·IDT
    p = d.slide("setup.s: 임시 GDT·IDT", K.S_CODE,
                "원문 src/boot/setup.s:205-224 — '같은 표를 두 번' 만든다(첫 번째: 임시 표)")
    cp(d, p, "src/boot/setup.s", 205, 216, 1100, 4400, 15200, size=10,
       extra="gdt — dummy + code/data 8Mb")
    cp(d, p, "src/boot/setup.s", 130, 134, 17400, 4400, 13900, size=11,
       extra="lidt 0,0 · lgdt gdt_48")
    cp(d, p, "src/boot/setup.s", 218, 224, 17400, 9300, 13900, size=9,
       extra="idt_48(0,0) · gdt_48")
    para(d, p, 1100, 12800, 15200, 1700,
         "임시 gdt — code/data 8Mb·base 0 (205-216)\n"
         "idt_48(0,0) · gdt_48 base 0x9xxxx (218-224)\n"
         "↔ head.s GDT(234-236) — 16Mb·커널 이미지 안(_gdt)",
         13)
    d.banner(p, "임시 표는 8Mb 한계·0x9xxxx 위치 — 8Mb 한계 문제는 이해 확인 3번(44장)으로", 14800, 17)

    # 17 A20과 8259
    p = d.slide("setup.s: A20과 8259", K.S_CODE,
                "A20은 주소 버스 21번째 선 · 8042는 키보드 컨트롤러 — ICW1-4·마스크: src/boot/setup.s:154-179")
    cp(d, p, "src/boot/setup.s", 138, 144, 1100, 4400, 9800, size=10,
       extra="A20 활성화 (8042)")
    cp(d, p, "src/boot/setup.s", 154, 165, 11300, 4400, 9800, size=9,
       extra="ICW1-2 · 벡터 0x20/0x28")
    cp(d, p, "src/boot/setup.s", 166, 179, 21500, 4400, 10800, size=8,
       extra="ICW3-4 · 마스크 0xFF")
    badge(d, p, 1100, 10200, 9800, "A20 — 켜야 1MB 넘는 주소 접근", K.TEAL, 700, 13)
    para(d, p, 1100, 11100, 9800, 3300,
         "0xD1(명령 쓰기) → 0xDF(A20 on)를\n8042 포트 0x64/0x60에 출력.\n"
         "empty_8042로 준비 상태 확인(198-203).", 13)
    para(d, p, 11300, 12600, 21000, 1900,
         "8259A 재프로그래밍 — IRQ를 인텔 예약 구간 뒤 0x20-0x2F로 옮기고(ICW1-4), "
         "마스크 0xFF로 전부 차단(176-179).\n"
         ".word 0x00eb = jmp $+2 지연. 마스크 0xFF는 main()의 초기화 함수가 하나씩 여는 초기 상태다(31장).",
         14)
    d.banner(p, "하드웨어 인터럽트는 전부 닫은 채 넘어간다 — 문은 main()이 연다", 14800, 18)

    # 18 lmsw와 jmpi 0,8
    p = d.slide("setup.s: lmsw와 jmpi 0,8", K.S_CODE,
                "인용은 191-193 — 186-190은 주석(기존 01 자료 186-193 표기의 정정)")
    d.code(p, "src/boot/setup.s", 191, 193,
           "mov ax,#0x0001\nPE 비트(비트0)만 세운 값\n\n"
           "lmsw ax\nCR0 하위 16비트 적재 — PE=1\n\n"
           "jmpi 0,8\nCS=0x0008(임시 GDT 1번),\nEIP=0 — 32비트 코드 시작\n\n"
           "lmsw 직후에도 세그먼트 레지스터는\n옛값 — far jump로 다시 실어야\n한다(1회차 25-26장 복습)",
           size=15, expl_size=16)
    d.banner(p, "3줄이 real → protected 전환의 전부다", 14800, 19)

    # ── 상태도 19 (중간 1) ─────────────────────────────────────
    p = d.slide("상태도(중간 1): real → protected", K.S_STATE,
                "§4 종합 표의 상단 6행 — 종합(36장)의 미리보기 · 값이 바뀌는 칸만 TEAL 굵게")
    state_table(d, p, 1100, 4400, STATE_COLS, state_rows(1, 6),
                row_h=900, size=12,
                hl={(r, c) for (r, c) in STATE_HL if r <= 6})
    para(d, p, 1100, 10900, 31500, 2200,
         "전환 원인은 모두 줄 번호로 읽는다 — int 0x19(BIOS) · bootsect.s:56,61-62(복사·스택) · "
         "bootsect.s:139(jmpi setup) · setup.s:109(cli) · setup.s:191-192(lmsw) · setup.s:193(jmpi 0,8).\n"
         "real mode에는 권한 수준이 없다 — CPL은 '—'로 표기한다(§8).", 15)
    d.banner(p, "여기까지 PE만 1이 됐다 — PG는 아직, IF는 꺼졌다", 13400, 18)

    # ── 코드 20–24: head.s ────────────────────────────────────
    # 20 첫 32비트 명령
    p = d.slide("head.s: 첫 32비트 명령", K.S_CODE,
                "원문 src/boot/head.s:17-36 — startup_32 · lss _stack_start · A20 검사 루프")
    cp(d, p, "src/boot/head.s", 17, 23, 1100, 4400, 9700, size=11,
       extra="startup_32 — 세그먼트·스택")
    cp(d, p, "src/boot/head.s", 26, 31, 11900, 4400, 9700, size=11,
       extra="setup_gdt 뒤 재적재")
    cp(d, p, "src/kernel/sched.c", 67, 72, 22700, 4400, 8600, size=10,
       extra="user_stack · stack_start")
    para(d, p, 1100, 10900, 31500, 3400,
         "ds·es·fs·gs = 0x10 — 임시 GDT 2번(데이터)으로 재적재. CS는 jmpi 0,8의 0x0008을 유지.\n"
         "lss _stack_start,%esp — SS:ESP를 메모리에서 한 번에 적재. user_stack 끝(sched.c:67-72), ss=0x10 — 커널 스택이 생겨난다.\n"
         "PG는 아직 0 — 주소 0에서 실행 중이다. 그 뒤 A20 검사 루프(33-36): 0x100000에 쓰고 다시 읽어 확인.", 15)
    d.banner(p, "32비트 첫 순서 — 데이터 세그먼트 재적재, 스택 확보", 14800, 18)

    # 21 IDT/GDT 다시 만들기
    p = d.slide("head.s: IDT/GDT 다시 만들기", K.S_CODE,
                "src/boot/head.s:24-31 (호출) · src/boot/head.s:78-93 · src/boot/head.s:105-107 — 재로드 이유는 02회차 상태도 1")
    cp(d, p, "src/boot/head.s", 78, 86, 1100, 4400, 9800, size=9,
       extra="setup_idt ① — 게이트 값 조립")
    cp(d, p, "src/boot/head.s", 87, 93, 11500, 4400, 9800, size=9,
       extra="setup_idt ② — 256항목 채움")
    cp(d, p, "src/boot/head.s", 105, 107, 21900, 4400, 10400, size=11,
       extra="setup_gdt")
    para(d, p, 21900, 8200, 10400, 2200,
         "selector 0x0008 · type 0x8E00\n= 인터럽트 게이트, DPL 0, present", 13)
    para(d, p, 1100, 10900, 31500, 3400,
         "setup_idt — 256개 항목 전부 ignore_int로 채우고 lidt. setup_gdt는 lgdt 한 줄 — setup.s의 임시 표를 "
         "커널 이미지 안의 표(idt_descr/gdt_descr 222-229, _idt/_gdt 232-238)로 교체한다.\n"
         "ignore_int(150-170)는 \"Unknown interrupt\"를 printk하는 기본 핸들러 — 04회차 trap_init이 덮어쓴다.\n"
         "call setup_idt·setup_gdt 뒤 세그먼트를 다시 적재하는 것도 잊지 않는다(24-31).", 15)
    d.banner(p, "임시 표(16장)는 여기서 폐기 — 커널 이미지 안의 표가 정식 표다", 14800, 17)

    # 22 CR0와 x87
    p = d.slide("head.s: CR0와 x87", K.S_CODE,
                "원문 src/boot/head.s:43-65 — CR0 전체 값은 FPU 유무로 달라진다(관찰로만 말한다, §8)")
    cp(d, p, "src/boot/head.s", 43, 49, 1100, 4400, 15200, size=11,
       extra="andl $0x80000011 · orl $2")
    cp(d, p, "src/boot/head.s", 54, 65, 17400, 4400, 13900, size=9,
       extra="check_x87 — 287/387 검사")
    # 태그 4개는 왼쪽 패널 폭(x 1100-17290) 안에만 — 오른쪽 코드 패널(x≥17400)과 겹치지 않게
    badge(d, p, 1100, 10600, 3980, "bit31 PG 보존", K.MUTED, 700, 13)
    badge(d, p, 5170, 10600, 3980, "bit4 ET 보존", K.MUTED, 700, 13)
    badge(d, p, 9240, 10600, 3980, "bit1 MP 설정(orl $2)", K.TEAL, 700, 13)
    badge(d, p, 13310, 10600, 3980, "bit0 PE 보존", K.MUTED, 700, 13)
    para(d, p, 1100, 11500, 15200, 2900,
         "andl $0x80000011 — PG·PE·ET 보존, orl $2 — MP 설정\n"
         "FPU 있음 → CR0 ≈ 0x…13 · 없으면 xorl $6 (MP 끄고 EM) ≈ 0x…15\n"
         "진입 시 0x…11까지 — 하위 바이트 0x11/0x13/0x15, 시연 B(40장)에서 관찰로만",
         13)
    para(d, p, 17400, 12300, 13900, 2200,
         "check_x87 — fninit/fstsw로 287/387 검사.\nFPU가 없으면 CR0을 다시 쓴다(59-61).", 13)
    d.banner(p, "CR0을 단정하지 않는다 — 387 유무가 값을 바꾼다", 14800, 18)

    # 23 main 호출 프레임
    p = d.slide("head.s: main 호출 프레임", K.S_CODE,
                "head.s:218 ret가 _main을 pop — call이 아니라 ret로 main에 들어간다")
    d.code(p, "src/boot/head.s", 135, 144,
           "pushl $0 ×3 — main의 인자\n(envp, argv, argc 전부 0)\n\n"
           "pushl $L6 — 복귀 주소\nL6은 무한루프(142-143)\n\n"
           "pushl $_main — 진입 주소\n\njmp setup_paging\n그 ret(218)가 스택의\n"
           "_main을 pop한다", expl_size=16)
    d.banner(p, "main이 반환해도 재부팅이 아니다 — L6 무한루프에 머문다(§8)", 14800, 18)

    # 24 setup_paging
    p = d.slide("head.s: setup_paging", K.S_CODE,
                "원문 src/boot/head.s:198-218 · 배치 pg0~pg3 = .org 0x1000-0x4000 (head.s:114-133)")
    cp(d, p, "src/boot/head.s", 198, 206, 1100, 4400, 15200, size=10,
       extra="5페이지 클리어 · pg_dir[0..3]")
    cp(d, p, "src/boot/head.s", 207, 218, 17400, 4400, 13900, size=8,
       extra="0xfff007부터 거꾸로 · CR3 · PG")
    pages = [("pg_dir", "0x0000", K.TEAL), ("pg0", "0x1000", K.PAPER),
             ("pg1", "0x2000", K.PAPER), ("pg2", "0x3000", K.PAPER),
             ("pg3", "0x4000", K.PAPER)]
    for i, (nm, ad, col) in enumerate(pages):
        nbox(d, p, 1100 + i * 6250, 11550, 6000, 1850, nm,
             f"{ad} — pg_dir[{i}]", col, s1=14, s2=10)
    para(d, p, 1100, 13480, 31500, 1250,
         "pg_dir[0..3] = pgN+7 · 0xfff007에서 0x1000씩 줄이며 채운다 — 선형=물리 16MB identity mapping. "
         "CR3=0, CR0.PG=1(214-217) — pg_dir이 startup 코드를 덮어쓴다(head.s:10-12).", 12)

    # ── 상태도 25 (중간 2) ─────────────────────────────────────
    p = d.slide("상태도(중간 2): head.s 구간", K.S_STATE,
                "§4 종합 표의 head~main 진입 행(jmpi 행은 들어올 때 참조) — 19장과 같은 형식")
    state_table(d, p, 1100, 4400, STATE_COLS, state_rows(6, 9),
                row_h=900, size=12,
                hl={(r - 5, c) for (r, c) in STATE_HL if 6 <= r <= 9})
    d.flow(p, [("jmpi 0,8", "CS=0x0008 · 스택 없음"),
               ("lss _stack_start", "head.s:23 — 커널 스택 생성"),
               ("setup_paging", "head.s:217 — PG 0→1"),
               ("ret → main()", "head.s:218 — L6,0,0,0 위")],
           y=9200, h=3200)
    para(d, p, 1100, 12480, 31500, 1900,
         "head 구간은 상태가 거의 그대로다 — PE=1·IF=0·CPL 0 유지, 바뀌는 것은 PG 하나(0→1)와 스택·실행 주소.\n"
         "main() 진입의 전환 원인은 head.s:218 ret(23장 프레임).", 15)
    d.banner(p, "네 비트 중 head.s가 바꾸는 것은 PG 하나뿐이다", 14800, 18)

    # ── main() 26–35 ──────────────────────────────────────────
    # 26 setup이 남긴 값과 메모리 경계
    p = d.slide("main(): setup이 남긴 값 읽기와 메모리 경계", K.S_CODE,
                "main.c:58-60이 읽는 주소 = setup.s가 저장한 0x90000-0x901FF (14장 연결)")
    cp(d, p, "src/init/main.c", 110, 122, 1100, 4400, 19700, size=11,
       extra="ROOT_DEV·drive_info·메모리 경계")
    cp(d, p, "src/init/main.c", 58, 60, 22000, 4300, 10000, size=11,
       extra="setup이 남긴 값")
    nbox(d, p, 22000, 7950, 4900, 1800, "[0, 1MB)", "커널", K.TEAL, s1=13, s2=10)
    nbox(d, p, 27100, 7950, 4900, 1800, "[1MB, buffer_end)",
         "버퍼 — buffer_init", K.PAPER, s1=13, s2=10)
    nbox(d, p, 22000, 9800, 10000, 1800,
         "[main_memory_start, memory_end)", "페이지 풀 — mem_init", K.PAPER,
         s1=13, s2=10)
    para(d, p, 22000, 11650, 10000, 3100,
         "memory_end는 EXT_MEM_K(0x90002)로\n계산 — setup이 int 0x15로 얻은 값.\n\n"
         "mm/memory.c:43 LOW_MEM=0x100000 —\n1MB 이상만 페이지 풀이다(28장).", 12)
    d.banner(p, "main()의 첫 일 — setup이 모아 둔 숫자로 메모리 지도를 그린다", 14800, 17)

    # 27 초기화 함수 범주표
    p = d.slide("main(): 초기화 9함수 범주표", K.S_BG,
                "main.c:126-135 호출 순서 — chr_dev_init은 빈 함수(tty_io.c:347-349)라 실질 9 · 이 표가 28-33장의 목차")
    d.table(p, 1100, 4400, [4700, 4400, 14600, 7800], [
        ["함수", "범주", "채우는 자료구조", "대표 줄"],
        ["mem_init", "메모리", "mem_map[] — USED(100) 뒤 가용 0", "mm/memory.c:399-411"],
        ["trap_init", "게이트", "IDT 0-16·45·39 게이트", "kernel/traps.c:181-208"],
        ["blk_dev_init", "장치 표", "request[32] dev=-1", "ll_rw_blk.c:157-165"],
        ["chr_dev_init", "(장치 표)", "빈 함수 — 내용 없음", "tty_io.c:347-349"],
        ["tty_init", "장치", "rs_init + con_init — 게이트·화면", "tty_io.c:105-109"],
        ["time_init", "시간", "startup_time — CMOS 읽기", "main.c:76-96"],
        ["sched_init", "스케줄러", "GDT TSS0·LDT0 · task[] · 게이트 0x20·0x80", "kernel/sched.c:385-412"],
        ["buffer_init", "버퍼", "버퍼 헤더·데이터 블록 · hash_table", "fs/buffer.c:348-381"],
        ["hd_init", "블록 장치", "게이트 0x2E · request_fn", "hd.c:343-349"],
        ["floppy_init", "블록 장치", "게이트 0x26 · request_fn", "floppy.c:457-462"],
    ], row_h=880, size=13)
    d.banner(p, "범주(메모리/게이트/장치/시간/스케줄러/버퍼/블록) × 채우는 자료구조 — 암기가 아니라 분류", 14400, 17)

    # 28 mem_init
    p = d.slide("mem_init", K.S_CODE,
                "상수 mm/memory.c:43-47 · mem_map은 memory.c:57 — 슬라이드 26의 페이지 풀 구간과 연결")
    cp(d, p, "src/mm/memory.c", 399, 411, 1100, 4400, 19700, size=11,
       extra="mem_map — USED 뒤 0으로")
    cp(d, p, "src/mm/memory.c", 43, 47, 22000, 4300, 10000, size=10,
       extra="상수")
    nbox(d, p, 22000, 8950, 10000, 1800, "mem_map[0..3839] = 100",
         "일단 전부 사용중으로", None, K.MUTED, s1=13, s2=10)
    # 화살표는 두 상자 왼쪽 여백(x 21100-22000)에 세로로 — 상자 본문을 가리지 않는다
    arrow(d, p, 21100, 9500, "↓", 20, K.TEAL, w=900, h=1500)
    nbox(d, p, 22000, 10900, 10000, 1800, "[start_mem,end_mem) = 0",
         "페이지 풀만 가용 표시", K.TEAL, s1=13, s2=10)
    para(d, p, 22000, 12750, 10000, 1900,
         "start_mem = main_memory_start(26장)\nend_mem = memory_end — "
         "가용 페이지는 1MB 이상만.", 12)
    d.banner(p, "페이지 풀의 원장(mem_map)을 여는 함수 — 뒤는 get_free_page가 쓴다", 14800, 17)

    # 29 trap_init
    p = d.slide("trap_init", K.S_CODE,
                "원문 src/kernel/traps.c:181-208 — 0-16 개별 설치 · 17-47 reserved 루프 · 45·39 덮어쓰기")
    cp(d, p, "src/kernel/traps.c", 185, 197, 1100, 4400, 15200, size=9,
       extra="벡터 0-11 게이트")
    cp(d, p, "src/kernel/traps.c", 198, 208, 17400, 4400, 13900, size=10,
       extra="12-16 · reserved · 45 · 마스크")
    para(d, p, 1100, 12800, 31500, 1600,
         "예외 0-16 개별 설치(0 divide · 14 page_fault 등) · 3-5만 시스템 게이트(DPL 3)\n"
         "17-47 reserved 루프 → 45(irq13)·39(parallel)만 덮어쓰기 · IRQ2·IRQ13 해제(205-206) — 31장", 14)
    d.banner(p, "게이트 3종(set_trap/set_intr/set_system)의 차이는 32장 비교 3에서", 14800, 17)

    # 30 sched_init
    p = d.slide("sched_init", K.S_CODE,
                "원문 src/kernel/sched.c:385-412 · LATCH = 1193180/HZ (sched.c:46) — 02회차 30장 GDT 캡처 참조")
    cp(d, p, "src/kernel/sched.c", 385, 397, 1100, 4400, 15200, size=9,
       extra="TSS0·LDT0 · task[] NULL")
    cp(d, p, "src/kernel/sched.c", 398, 412, 17400, 4400, 13900, size=9,
       extra="NT 클리어 · 8253 · 게이트 0x20·0x80")
    para(d, p, 1100, 12900, 31500, 1500,
         "task_union(sched.c:53-72) — task_struct+커널 스택 1페이지 · GDT 4·5번 TSS0·LDT0 · task[1..] NULL · ltr/lldt(0)\n"
         "8253 LATCH=1193180/HZ · 게이트 0x20(timer)+IRQ0 해제(410) · 게이트 0x80(system_call, DPL3)(411) — 04회차", 14)
    d.banner(p, "task_union(sched.c:53-72) — task_struct와 커널 스택을 1페이지에 겹친다", 14800, 17)

    # ── 비교 31–32 ────────────────────────────────────────────
    # 31 IRQ 0~15
    p = d.slide("비교 2: IRQ 0~15 전체와 열리는 순서", K.S_CMP,
                "마스크 초기값은 setup.s:176-179 전부 1(차단) — main()의 초기화 함수가 여는 IRQ만 0이 된다")
    irq_rows = [
        ["IRQ", "장치", "초기 마스크", "여는 함수·줄", "게이트", "게이트 종류·설치 줄"],
        ["0", "타이머(8253)", "1 (차단)", "sched.c:410", "0x20", "intr — sched.c:409"],
        ["1", "키보드", "1", "console.c:684", "0x21", "trap — console.c:683"],
        ["2", "캐스케이드(PIC)", "1", "traps.c:205 · hd.c:347", "0x22", "trap(reserved) — traps.c:202"],
        ["3", "시리얼 2", "1", "serial.c:43", "0x23", "intr — serial.c:40"],
        ["4", "시리얼 1", "1", "serial.c:43", "0x24", "intr — serial.c:39"],
        ["5", "LPT2", "1", "마스크 유지", "—", "—"],
        ["6", "플로피", "1", "floppy.c:461", "0x26", "trap — floppy.c:460"],
        ["7", "LPT1", "1", "마스크 유지", "—", "—"],
        ["8-12", "RTC·예약", "1", "마스크 유지", "—", "—"],
        ["13", "수학(FPU 오류)", "1", "traps.c:206", "0x2D", "trap — traps.c:204 (45=irq13)"],
        ["14", "하드디스크", "1", "hd.c:348", "0x2E", "intr — hd.c:346"],
        ["15", "LPT3", "1", "마스크 유지", "—", "—"],
    ]
    hl = {(r, c) for r in range(1, 13) for c in (3, 4, 5)
          if irq_rows[r][3] != "마스크 유지"}
    state_table(d, p, 1100, 4300, [2300, 4500, 2900, 7300, 3200, 11300],
                irq_rows, row_h=770, size=12, hl=hl)
    d.banner(p, "여덟 개만 열린다 — 0·1·2·3·4·6·13·14 · 미사용 5·7·8-12·15는 오늘 끝까지 닫혀 있다", 14400, 17)

    # 32 게이트 3종
    p = d.slide("비교 3: main()이 설치하는 게이트 3종", K.S_CMP,
                "02회차 게이트 비교(type·DPL)를 '누가 언제'로 확장 — 어느 함수가 어느 매크로를 쓰는가")
    d.table(p, 1100, 4400, [5600, 2600, 2600, 20700], [
        ["매크로", "type", "DPL", "사용 함수·벡터"],
        ["set_trap_gate", "15", "0",
         "traps.c:185-187, 189-203 (0-2·6-16, 17-47 reserved, 45·39) · console.c:683 (0x21) · floppy.c:460 (0x26)"],
        ["set_intr_gate", "14", "0",
         "sched.c:409 (0x20 timer) · hd.c:346 (0x2E) · serial.c:39-40 (0x23·0x24)"],
        ["set_system_gate", "15", "3",
         "traps.c:188-190 (3 int3 · 4 overflow · 5 bounds) · sched.c:411 (0x80 system_call)"],
    ], row_h=1800, size=14)
    para(d, p, 1100, 11900, 31500, 2600,
         "type 15 = 트랙션 없는 386 트랩 게이트, type 14 = 인터럽트 게이트(IF 자동 클리어).\n"
         "'왜 timer는 intr, 키보드는 trap인가'는 오늘 사실만 표시한다 — 04·13회차 본편에서 설명한다.\n"
         "DPL 3인 것은 시스템 게이트뿐 — 사용자 명령 int3·int $0x80이 통과할 수 있는 문이다.", 15)
    d.banner(p, "게이트 0x80은 set_system_gate — DPL 3, 셸의 write가 들어올 문(04회차)", 14800, 17)

    # 33 buffer_init·hd_init·floppy_init
    p = d.slide("buffer_init·hd_init·floppy_init", K.S_CODE,
                "원문 src/fs/buffer.c:348-381 · hd.c:343-349 · floppy.c:457-462 — 상세는 11회차, 오늘은 관찰만")
    cp(d, p, "src/fs/buffer.c", 348, 358, 1100, 4400, 15200, size=9,
       extra="버퍼 헤더(앞) · 데이터(뒤)")
    cp(d, p, "src/kernel/blk_drv/hd.c", 343, 349, 17400, 4400, 13900, size=10,
       extra="게이트 0x2E · IRQ2/14")
    cp(d, p, "src/kernel/blk_drv/floppy.c", 457, 462, 17400, 10200, 13900,
       size=8, extra="게이트 0x26 · IRQ6")
    nbox(d, p, 1100, 11750, 7300, 1800, "헤더 h → h++",
         "start_buffer에서 앞으로", K.PAPER, s1=13, s2=10)
    arrow(d, p, 8500, 12200, "↔", 22)
    nbox(d, p, 9900, 11750, 6400, 1800, "데이터 b -= 1024",
         "buffer_end에서 거꾸로", K.PAPER, s1=13, s2=10)
    para(d, p, 1100, 13600, 16100, 1100,
         "만나는 지점에서 정지 — b==0x100000이면 0xA0000로 점프(372-373) · free_list 환형(375-378) · hash_table NULL(379-380)",
         10)
    d.banner(p, "범주표(27장)의 칸을 채우는 관찰 — 버퍼 상세는 11회차가 한다", 14800, 17)

    # 34 sti와 move_to_user_mode
    p = d.slide("sti()와 move_to_user_mode", K.S_CODE,
                "main.c:136-137 sti() 후 move_to_user_mode() — system.h:16 sti 매크로")
    cp(d, p, "src/include/asm/system.h", 1, 14, 1100, 4400, 19700, size=9,
       extra="iret 프레임 — push 5워드")
    # 스택 상자 5개 — 부제 한 줄(11pt)까지 들어가는 높이 1900, 간격 120
    nbox(d, p, 22000, 4300, 10000, 1900, "SS 0x17", "사용자 데이터", None,
         K.MUTED, s1=13, s2=11)
    nbox(d, p, 22000, 6320, 10000, 1900, "ESP (push한 값)", "move 전후 같은 값",
         None, K.MUTED, s1=13, s2=11)
    nbox(d, p, 22000, 8340, 10000, 1900, "EFLAGS", "", None, K.MUTED, s1=13, s2=11)
    nbox(d, p, 22000, 10360, 10000, 1900, "CS 0x0f", "RPL 3 — CPL 0→3", K.TEAL,
         s1=13, s2=11)
    nbox(d, p, 22000, 12380, 10000, 1900, "EIP 1f (system.h:8)", "iret 후 이어 실행",
         K.TEAL, s1=13, s2=11)
    # 해설은 코드 패널 아래 왼쪽 단으로 — 같은 문구를 2줄로 재배열(오른쪽 단은 상자가 채운다)
    para(d, p, 1100, 13200, 20800, 1500,
         "sti() — IF 0→1 (main.c:136) · CPL 0→3 · CS 0x0008→0x000f · SS 0x10→0x17 · ESP 그대로\n"
         "새 프로세스·새 스택이 아니라 task 0이 user_stack을 CPL 3에서 계속 쓴다(§8).", 12)
    d.banner(p, "iret 한 번으로 링 0 → 링 3 — 커널이 사용자 모드로 내려간다", 14800, 17)

    # 35 첫 fork()와 pause()
    p = d.slide("첫 fork()와 pause()", K.S_CODE,
                "main.c:11-22 주석 — 커널 공간 fork는 COW가 없다 → main()은 스택을 쓰면 안 된다(inline 시스템 콜)")
    cp(d, p, "src/include/unistd.h", 133, 145, 1100, 4400, 15200, size=10,
       extra="_syscall0 — int $0x80")
    cp(d, p, "src/init/main.c", 23, 26, 17400, 4400, 13900, size=10,
       extra="inline 선언 — 스택 없이")
    cp(d, p, "src/init/main.c", 138, 141, 17400, 8500, 13900, size=10,
       extra="첫 fork · init · pause")
    para(d, p, 1100, 13500, 15200, 1000,
         "int $0x80, eax = __NR_name — 반환값이 음수면 errno 후 -1.", 13)
    para(d, p, 17400, 12650, 13900, 1900,
         "첫 fork() — 실패 처리 없음(main.c:138 주석). 자식은 init(), 부모는 for(;;) pause().\n"
         "int $0x80 도착지 system_call.s:80-94(04회차) · _sys_fork→copy_process(208-219, 06회차 예고).",
         13)
    d.banner(p, "main이 끝나도 시스템은 멈추지 않는다 — fork가 첫 프로세스를 만든다", 14800, 17)

    # ── 상태도 36 (종합) ───────────────────────────────────────
    p = d.slide("상태 변화도(종합): 부트 섹터에서 fork까지", K.S_STATE,
                "변경되는 데이터: CR0·EFLAGS·CS/SS 선택자·ESP · 유지 조건: 다음 전환 명령까지 · IF는 표시 지점 값 · 빈 칸은 이전 행과 동일")
    d.text(p, 1100, 3880, 31500, 450,
           "이 표가 핵심 질문의 답(45장) 재료 — 바뀌는 칸만 TEAL: PE 1회 · PG 1회 · IF 2회 · CPL 1회",
           14, K.ORANGE, True)
    state_table(d, p, 3900, 4400, STATE_COLS_NARROW, state_rows(1, 12),
                row_h=780, size=11, hl=STATE_HL)
    # 왼쪽 타임라인 눈금 — 칩 폭 1500('bootsect'가 한 줄에 들어가는 폭), 축은 x 2800
    d.shape(p, 2800, 4500, 60, 9900, K.LINE)
    marks = [("ROM", 4790), ("bootsect", 5960), ("setup", 7900),
             ("head.s", 10240), ("main()", 12580)]
    for nm, cy in marks:
        d.shape(p, 1100, cy - 330, 1500, 660, 0x203D4B)
        d.text(p, 1150, cy - 240, 1450, 500, nm,
               K.fit_size(nm, 11, 1450, min_size=8), K.TEAL, True)
        d.shape(p, 2730, cy - 60, 220, 120, K.TEAL)
    d.banner(p, "부팅 전체가 12행이다 — 19장(전반 6행)·25장(head 구간)의 합본", 14550, 17)

    # ── 시연·캡처 37–42 ───────────────────────────────────────
    # 37 시연 A
    p = d.slide("시연 A: QEMU -S 직후부터 setup까지", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 TCG · GDB + QEMU 모니터 · 줄 번호·심볼은 lab 기준(src/와 다를 수 있음)")
    auto_pane(d, p, 1100, 4300, 19700, 10200,
              "QEMU 모니터 + GDB — 명령·중단점",
              "# lab/ — 시작 정지 + gdbstub + 모니터\n"
              "qemu-system-i386 -drive file=Image,format=raw \\\n"
              "    -s -S -monitor stdio\n"
              "        # -s: gdbstub :1234 · -S: 시작 정지\n\n"
              "# 터미널 2 — GDB\n"
              "(gdb) target remote :1234\n"
              "(gdb) b *0x7c00            # bootsect\n"
              "(gdb) c\n"
              "(qemu) info registers      # Ctrl-Alt-2 모니터\n"
              "(gdb) b *0x90200           # setup\n"
              "(gdb) c\n"
              "(qemu) info registers", start=12)
    para(d, p, 22000, 4300, 10000, 10200,
         "관찰 대상\n\n"
         "· CR0=00000010 — PE=0\n"
         "· EFL의 IF 비트(0x200)\n"
         "· CS =07c0 → =9020\n"
         "· SS:SP = 0x9000:0xFF00\n"
         "  (bootsect.s:61-62)\n\n"
         "주의 — SeaBIOS가 0x7c00으로\n"
         "점프하는 CS:IP 표기는 BIOS\n"
         "구현에 따라 다르다(각주).\n\n"
         "캡처 3종은 다음 장(38).", 14)

    # 38 캡처 A
    p = d.slide("캡처 A: 실주소 모드 레지스터", K.S_DEMO,
                "각주: lab/ 빌드 · QEMU i386 · QEMU 모니터 info registers 형식 · 수정 없음 · 캡처 날짜 — (1) 정지 직후 (2) 0x7c00 (3) 0x90200")
    d.placeholder_output(p, 1100, 4600, 9900, 9600,
                         "(qemu) info registers\n"
                         "EIP=0000fff0\n"
                         "CS =0000 00000000 ffff\n"
                         "      # reset 직후\n"
                         "CR0=00000010\n"
                         "      # PE=0 · PG=0\n"
                         "EFL=00000002\n"
                         "      # IF=0 (reset 값)\n"
                         "SS =0030 … ESP=…\n"
                         "      # BIOS 것",
                         "02-a1-reset-registers.png")
    d.placeholder_output(p, 11900, 4600, 9900, 9600,
                         "(gdb) b *0x7c00 ; c\n"
                         "(qemu) info registers\n"
                         "EIP=00007c00\n"
                         "CS =07c0 00007c00 …\n"
                         "  # 또는 0000:7c00\n"
                         "  # — BIOS 따라 다름\n"
                         "EFL=00000202  IF=1\n"
                         "  # cli(109) 이전\n"
                         "CR0=00000010  PE=0\n"
                         "SS:SP — BIOS가 준 값",
                         "03-a2-bootsect-0x7c00.png")
    d.placeholder_output(p, 22700, 4600, 9900, 9600,
                         "(gdb) b *0x90200 ; c\n"
                         "(qemu) info registers\n"
                         "EIP=00000000\n"
                         "CS =9020 00090200 …\n"
                         "  # jmpi 0,SETUPSEG 직후\n"
                         "SS =9000 …\n"
                         "ESP=0000ff00\n"
                         "  # bootsect.s:61-62\n"
                         "EFL=00000202  IF=1\n"
                         "  # 아직 cli 전",
                         "04-a3-setup-0x90200.png")
    para(d, p, 1100, 14400, 31500, 1400,
         "CS 표기 차이(07c0 vs 0000:7c00)는 관찰 사실 — 어느 쪽이든 다음 단계 0x9020:0에서 같아진다.", 14)

    # 39 시연 B
    p = d.slide("시연 B: PE·PG 켜지는 순간", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB p/x $cr0 — gdbstub이 cr0을 못 주면 monitor info registers로 대체(§11)")
    auto_pane(d, p, 1100, 4300, 19700, 10200,
              "GDB — CR0 비트0·비트31",
              "# 페이징 전 — head 진입 (setup.s:193 직후)\n"
              "(gdb) b *0x0\n"
              "(gdb) c\n"
              "(gdb) p/x $cr0\n"
              "     # bit0=1(PE) · bit31=0(PG)\n"
              "     # 하위 바이트 0x11/0x13/0x15\n"
              "     # — FPU 여부(head.s:43-61)\n\n"
              "(gdb) b *setup_paging    # lab 심볼 확인(§11)\n"
              "(gdb) c\n"
              "(gdb) si          # ret(head.s:218) 직전까지\n"
              "(gdb) p/x $cr0    # 0x8000xxxx — bit31=1\n"
              "(gdb) p/x $cr3    # 0\n"
              "(gdb) d           # 주소 0 중단점 삭제 —\n"
              "                 # 페이징 뒤 pg_dir이 덮어씀\n"
              "                 # (head.s:10-12)", start=12)
    para(d, p, 22000, 4300, 10000, 10200,
         "관찰 포인트\n\n"
         "· CR0 bit0 — setup.s:192 lmsw\n"
         "· CR0 bit31 — head.s:217\n"
         "· CR3 = 0 (pg_dir)\n"
         "· ret 후 EIP = main\n"
         "  (23장 프레임 실측)\n\n"
         "주의 — 주소 0 근처 중단점은\n"
         "반드시 페이징 전에 소비하고\n"
         "삭제한다(d).\n\n"
         "캡처 2종은 다음 장(40).", 14)

    # 40 캡처 B
    p = d.slide("캡처 B: CR0 비트0·비트31", K.S_DEMO,
                "각주: lab/ 빌드 · QEMU i386 · GDB p/x 형식 · 수정 없음 · 캡처 날짜 — CR0 전체 값은 관찰 결과로만 말한다")
    d.placeholder_output(p, 1100, 4600, 15200, 9600,
                         "(gdb) b *0x0 ; c        # head 진입 — 페이징 전\n"
                         "(gdb) p/x $cr0\n"
                         "$1 = 0x11\n"
                         "     # bit0=1 (PE) · bit31=0\n"
                         "     # FPU 있으면 0x13 · 없으면 0x15\n"
                         "     # — head.s:43-61 결과값\n"
                         "(gdb) p/x $cr3\n"
                         "$2 = 0x0",
                         "05-b1-head-entry-cr0.png")
    d.placeholder_output(p, 16900, 4600, 15700, 9600,
                         "(gdb) b *setup_paging ; c\n"
                         "(gdb) si        # ret 직전까지 반복\n"
                         "(gdb) p/x $cr0\n"
                         "$3 = 0x80000011\n"
                         "     # bit31=1 — PG 켜짐 (head.s:217)\n"
                         "(gdb) p/x $pc\n"
                         "$4 = … <_main>   # ret가 _main을 pop\n"
                         "                 # lab 심볼 _ 접두 확인(§11)\n"
                         "(gdb) d          # 주소 0 중단점 삭제",
                         "06-b2-after-paging-cr0.png")
    para(d, p, 1100, 14400, 31500, 1400,
         "왼쪽 = head 진입 직후(PE=1, PG=0) · 오른쪽 = setup_paging ret 직후(PG=1, EIP=main) — 22장 값 관찰로 확정.", 14)

    # 41 시연 C
    p = d.slide("시연 C: main → sti → 사용자 모드 → fork", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB — b init/main.c:138 은 lab 줄 번호 확인 후 설정(§11)")
    auto_pane(d, p, 1100, 4300, 19700, 10200,
              "GDB — main 진입부터 int $0x80까지",
              "(gdb) b main ; c\n"
              "(gdb) info registers\n"
              "     # cs=0x0008 · IF=0 (sti 전)\n\n"
              "(gdb) b init/main.c:138   # lab 줄 번호 확인\n"
              "(gdb) c\n"
              "(gdb) info registers\n"
              "     # cs=0x000f · ss=0x0017 · IF=1\n"
              "(gdb) x/8xw $esp   # ESP 같은 값(system.h:2,4)\n\n"
              "(gdb) si           # int $0x80 진입 직후\n"
              "(gdb) info registers\n"
              "     # cs=0x0008 · esp ≈ init_task 페이지 끝\n"
              "     # — TSS esp0 (sched.h:128)\n"
              "(gdb) finish       # copy_process는 안 들어감\n"
              "(gdb) p $eax       # 부모: 자식 pid (0이 아님)", start=11)
    para(d, p, 22000, 4300, 10000, 10200,
         "관찰 포인트\n\n"
         "· cs 0x0008 → 0x000f\n"
         "  (CPL은 CS 하위 2비트)\n"
         "· ss 0x10 → 0x0017\n"
         "· IF 0 → 1 (main.c:136)\n"
         "· ESP — 사용자 모드 진입\n"
         "  전후 같은 값\n"
         "· int 0x80 뒤 esp는 TSS의\n"
         "  esp0로 교체(sched.h:128)\n\n"
         "fork 내부(copy_process)는\n"
         "06회차 — 오늘은 finish로\n"
         "반환값만 본다.\n\n"
         "캡처 3종은 다음 장(42).", 14)

    # 42 캡처 C
    p = d.slide("캡처 C: 사용자 모드 진입과 int 0x80", K.S_DEMO,
                "각주: lab/ 빌드 · QEMU i386 · GDB info registers 형식 · 수정 없음 · 캡처 날짜 — ESP 교체는 int 0x80 뒤에만 일어난다")
    d.placeholder_output(p, 1100, 4600, 9900, 9600,
                         "(gdb) b main ; c\n"
                         "(gdb) info registers\n"
                         "cs     0x0008   # CPL 0\n"
                         "ss     0x0010\n"
                         "eflags 0x2      # IF=0\n"
                         "   # 아직 sti 전\n"
                         "esp    0x1a0b8 …",
                         "07-c1-main-entry-registers.png")
    d.placeholder_output(p, 11900, 4600, 9900, 9600,
                         "(gdb) b init/main.c:138 ; c\n"
                         "(gdb) info registers\n"
                         "cs     0x000f   # CPL 3\n"
                         "ss     0x0017\n"
                         "eflags 0x202    # IF=1\n"
                         "(gdb) x/8xw $esp\n"
                         "  # move_to_user_mode 전후\n"
                         "  # 같은 값(system.h:2,4)",
                         "08-c2-user-mode-registers.png")
    d.placeholder_output(p, 22700, 4600, 9900, 9600,
                         "(gdb) si     # int $0x80 직후\n"
                         "(gdb) info registers\n"
                         "cs     0x0008   # 게이트 → CPL 0\n"
                         "esp    0x1a4f8\n"
                         "  # init_task 페이지 끝 근처\n"
                         "  # — TSS esp0(sched.h:128)\n"
                         "(gdb) finish ; p $eax\n"
                         "$5 = 2   # 부모: 자식 pid",
                         "09-c3-int80-entry-registers.png")
    para(d, p, 1100, 14400, 31500, 1400,
         "세 장을 나란히 — CS 하위 2비트로 CPL이 보이고, ESP가 바뀌는 순간은 int 0x80 진입뿐이다.", 14)

    # 43 관찰 vs 추론
    p = d.slide("관찰 vs 추론", K.S_BG,
                "캡처 각주 5항목 재확인 — lab/ 빌드 · QEMU i386 · GDB/모니터 · 수정 없음/있음 · 캡처 날짜 (00-common §7)")
    cards_fit(d, p, [
        ("관찰 — 캡처로 본 것",
         "CR0 · CS/SS · EFLAGS\n스택 덤프(p/x, x/8xw)\n\n"
         "QEMU 모니터와 GDB는\n출력 형식이 다르다 —\n캡처마다 어느 쪽인지 표기"),
        ("추론 — 코드로 추론한 것",
         "BIOS 내부 동작\nint 0x13 디스크 읽기 내부\nCPU 캐시·프리페치 큐\niret의 권한 검사\n\n"
         "근거는 src/ 원문 줄 번호"),
    ], y=4400, h=8000, body=16)
    para(d, p, 1100, 12450, 31500, 2300,
         "lab과 src는 다른 텍스트다 — lab 빌드의 심볼(_main·_stack_start 등)과 줄 번호는 캡처 각주에 lab 기준으로만 적는다.\n"
         "슬라이드 코드 인용은 전부 src/ 원본 기준 — 두 체계를 한 문장에 섞지 않는다.\n"
         "관찰로 확정한 값(캡처 B의 CR0 등)과 코드에서 읽은 값(상태 표)을 말할 때도 출처를 구분해 밝힌다.", 15)
    d.banner(p, "본 것과 읽은 것을 구분한다 — 이것이 시연의 규칙", 14800, 18)

    # 44 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "정답(클릭 후 표시) — ① 자리 확보 ② lmsw ax·setup.s:192 ③ 임시 표 0x9xxxx·8Mb → head.s 16Mb 표 ④ 아니오, ret 진입·복귀 L6 ⑤ main.c:136 sti() ⑥ 아니오, 같은 esp·SS만 0x17")
    qs = [
        ("Q1", "bootsect가 자신을 0x90000으로 옮기는 이유는?"),
        ("Q2", "PE 비트를 1로 만드는 명령과 파일:줄은?"),
        ("Q3", "GDT를 두 번 만드는 이유는?"),
        ("Q4", "main()은 call로 호출되는가?"),
        ("Q5", "IF가 0에서 1이 되는 지점은?"),
        ("Q6", "move_to_user_mode 뒤 ESP 값은 바뀌는가?"),
    ]
    for i, (tag, body) in enumerate(qs):
        qbox(d, p, 1100, 4300 + i * 1620, 31500, 1470, tag, body, K.TEAL, 16)
    d.banner(p, "6문항 — 계획 §6 원문 그대로 · 정답 공개 후 45장으로", 14400, 17)

    # 45 핵심 질문의 답
    p = d.slide("핵심 질문의 답", K.S_ANS,
                "부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가? — 상태 표(36)의 네 강조 칸")
    para(d, p, 1100, 4300, 31500, 2400,
         "\"PE는 setup.s:192, PG는 head.s:217, IF는 setup.s:109에서 0·main.c:136에서 1, "
         "CPL은 system.h:8에서 3\"", 21, K.ORANGE, True)
    d.flow(p, [("PE 1회", "setup.s:192 lmsw"),
               ("PG 1회", "head.s:217 movl %eax,%cr0"),
               ("IF 2회", "setup.s:109 cli →\nmain.c:136 sti"),
               ("CPL 1회", "system.h:8 pushl $0x0f\n→ iret")],
           y=7100, h=2800)
    d.table(p, 1100, 10400, [4400, 11600, 6400, 9100], [
        ["비트", "전환", "값", "36장에서의 칸"],
        ["PE", "setup.s:192", "0 → 1", "5행 lmsw"],
        ["PG", "head.s:217", "0 → 1", "8행 setup_paging"],
        ["IF", "setup.s:109 · main.c:136", "1 → 0 → 1", "4행 cli · 10행 sti"],
        ["CPL", "system.h:8 (iret)", "0 → 3", "11행 move_to_user_mode"],
    ], row_h=780, size=13)
    d.banner(p, "네 비트의 전환 횟수 — PE 1회 · PG 1회 · IF 2회 · CPL 1회", 14400, 18)

    # 46 정리
    p = d.slide("정리", K.S_WRAP,
                "세 단계 · 두 번의 GDT · 네 비트의 전환 횟수 · main의 9함수 · 첫 fork")
    cards_fit(d, p, [
        ("세 단계의 역할",
         "bootsect — 512B 로더\nsetup·system 적재,\n자기 자신은 0x90000으로\n\n"
         "setup — BIOS 값 수집\nsystem 0x10000→0 이동\nPE=1 · A20 · 8259 재설정\n\n"
         "head — IDT/GDT 재구성\n16MB 페이징, ret 진입"),
        ("두 번의 GDT와 네 비트",
         "setup.s 임시 표(8Mb·0x9xxxx)\n→ head.s 표(16Mb·커널 안)\n— '같은 표를 두 번'\n\n"
         "전환 횟수 —\nPE 1회 · PG 1회\nIF 2회 · CPL 1회\n\n"
         "답의 네 주소(45장)"),
        ("main의 9함수와 첫 fork",
         "범주: 메모리·게이트·장치·\n시간·스케줄러·버퍼·블록 —\n각자 채우는 자료구조(27장)\n\n"
         "sti → move_to_user_mode\n→ 첫 fork\n\n"
         "main이 끝난 뒤의 세계 —\n04회차가 이어 받는다"),
    ], y=4100, h=10600, body=14)
    d.banner(p, "부트 섹터 512바이트 → main() → fork — 파트 A «입문·부팅»의 완결", 14800, 18)

    # 47 04회차 예고
    p = d.slide("04회차 예고", K.S_WRAP,
                "kernel/sched.c:411 — 오늘 sched_init이 연 게이트 0x80 · include/unistd.h:133-145 — _syscall0의 int $0x80")
    d.flow(p, [("셸 write(1, …)", "사용자 공간 CPL 3"),
               ("int $0x80", "_syscall0 — unistd.h:137"),
               ("게이트 0x80", "오늘 sched_init이 연 문"),
               ("system_call.s", "04회차 본편")],
           y=4400, h=3000)
    d.cards(p, [
        ("04회차 핵심 질문",
         "\"write(1, ...) 한 줄이\"\n어떻게 커널 코드에 도착하고\n돌아오는가? — 오늘 연 게이트\n0x80 통과가 곧 출발점"),
        ("오늘 남긴 무대",
         "sched_init — 게이트 0x80\n(system_call.s 진입)\ntrap_init — 예외 게이트 ·\nmain의 9함수가 만든 무대"),
        ("다음 회차 읽을 소스",
         "kernel/system_call.s\nkernel/asm.s\nkernel/traps.c\nunistd.h · sys.h (include/)"),
    ], y=7900, h=6300)
    d.banner(p, "파트 A «입문·부팅» 마무리 — 04회차부터 파트 B «실행의 길»", 14800, 18)


if __name__ == "__main__":
    K.run(globals())
