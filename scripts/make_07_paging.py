#!/usr/bin/env python3
"""07회차 덱 — 주소 변환과 페이지 관리 (output/07-paging.pptx)

계획: materials/slide-plans/07-paging.md (§2 표 47행 1:1 · §3 앞부분 명세 ·
§4 다이어그램 목록 · §5 캡처 11종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="07", total=47, slug="07-paging",
    part_no="C", part="«메모리»",
    title="07. 주소 변환과 페이지 관리",
    question="같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가?",
    done=6,
    today_line="논리 → 선형(LDT 베이스) → 물리(페이지 테이블)\n— 주소 세 단계와 물리 페이지 장부 mem_map (파트 C «메모리» 첫 회차)",
    next_lines=[
        "06 → 07   fork가 copy_mem·copy_page_tables로 무언가를 복사해 두었다 → 07: 그것이 건드린 페이지 디렉터리·테이블 구조를 정면으로 해부한다",
        "07 → 08   오늘 RW=0(&~2)으로 읽기 전용 공유한 페이지에 쓰면 무슨 일이 벌어지는가 — 페이지 폴트",
        "08(COW)·09(exec)가 오늘의 세 표(LDT · pg_dir · mem_map)를 그대로 쓴다",
    ],
    road_note=("세 표가 오늘의 답 재료다 — LDT(태스크별 베이스) · pg_dir+페이지 테이블(선형→물리) · "
               "mem_map(물리 페이지 장부). 이 회차는 질문·지도·배경·코드·상태도·비교·시연·정답·확인·정리 "
               "10단계 전부를 다룬다."),
    STRUCT=dict(
        teal=["mm"],
        today=[("mm/memory.c", "get_free_page · mem_map"),
               ("boot/head.s", "setup_paging · pg_dir"),
               ("include/linux/sched.h", "ldt[3] · tss.cr3")],
        flow="논리 주소 → LDT → 선형 주소 → 페이지 디렉터리·테이블 → 물리 주소",
        user="sh · 사용자 프로그램",
    ),
)

CHECKS = dict(
    captions={
        11: "src/boot/head.s:198-212",
        12: "src/boot/head.s:213-219",
        13: "src/mm/memory.c:177-178",
        14: "src/include/linux/sched.h:123-131",
        15: "src/kernel/fork.c:39-52",
        16: "src/kernel/fork.c:53-61",
        17: "src/include/linux/sched.h:188-198",
        18: "src/mm/memory.c:43-57",
        19: "src/mm/memory.c:399-411",
        20: "src/mm/memory.c:63-69",
        21: "src/mm/memory.c:70-83",
        22: "src/mm/memory.c:89-99",
        23: "src/mm/memory.c:207-216",
        24: "src/mm/memory.c:150-163",
        25: "src/mm/memory.c:173-183",
        26: "src/mm/memory.c:105-118",
    },
    required=[
        "논리 주소", "선형 주소", "물리 주소", "CR3", "LDT", "GDT", "pg_dir",
        "mem_map", "start_code", "0x4000000", "0xfff007", "identity mapping",
        "get_free_page", "free_page", "put_page", "copy_page_tables",
        "free_page_tables", "mem_init", "calc_mem", "setup_paging", "scasb",
        "0x9f", "MAP_NR", "USED", "invalidate", "0xA0", "640KB", "0x1234",
        "관찰", "추론", "LOW_MEM",
    ],
    prereq=[
        ("copy_page_tables", "src/boot/head.s:198-212"),
        ("LDT", "src/boot/head.s:198-212"),
        ("pg_dir", "src/include/linux/sched.h:123-131"),
    ],
    structure_nodes=["memory.c", "head.s", "sched.h", "system_call.s", "LDT"],
    capture_slides=[35, 37, 39, 40],
)


# ── 로컬 도우미 (deckkit 불변) ─────────────────────────────────
def wrap_kr(text, width, size):
    """CJK 포함 텍스트를 width(1/100mm) 안에서 줄바꿈한다.
    ASCII 단어(식별자·파일명 등) 중간에서는 끊지 않는다."""
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


def cexpl(d, p, text, size=15):
    """code() 오른쪽 해설 자리 — 자동 줄바꿈."""
    d.text(p, 22000, 4700, 10000, 9500, wrap_kr(text, 9500, size), size,
           K.PAPER)


def populate(d):
    # ── 배경 05–10 ────────────────────────────────────────────
    # 05 주소는 세 번 바뀐다
    p = d.slide("1회차에서 본 그림을 다시: 주소는 세 번 바뀐다", K.S_BG,
                "include/linux/sched.h:104-106 · boot/head.s:198-219, 234-238 — 1회차 15장(선형/물리 구분)의 확장")
    para(d, p, 1100, 4200, 31500, 1000,
         "프로그램이 쓰는 숫자는 아직 주소가 아니다 — 관문 두 개를 지나야 RAM 셀이 정해진다.")
    nbox(d, p, 1100, 5700, 8400, 2500, "논리 주소 (선택자:오프셋)",
         "프로그램이 쓰는 숫자\n예: 0x0f:0x1234 — 컴파일러·링커가 만든 값", s1=17)
    arrow(d, p, 9750, 6500, "→", 30)
    nbox(d, p, 10900, 5700, 6800, 2500, "선형 주소 (32비트)",
         "세그먼트 베이스 + 오프셋\n예: 0x8001234", s1=17)
    arrow(d, p, 17850, 6500, "→", 30)
    nbox(d, p, 19000, 5700, 13600, 2500, "물리 주소 (RAM)",
         "페이지 표가 골라 준 실제 셀\n예: 0x00abc000 + 0x234", s1=17)
    d.text(p, 5950, 8450, 10000, 700, "▲ 세그먼트 유닛 — LDT/GDT의 베이스를 더한다",
           13, K.TEAL, True)
    d.text(p, 14050, 8450, 10000, 700, "▲ 페이징 유닛 — CR3 → 디렉터리·테이블 조회",
           13, K.TEAL, True)
    para(d, p, 1100, 9600, 31500, 2900,
         "오늘의 로드맵: 두 화살표를 차례로 연다 — 1단계(선택자 → 베이스)는 06장, "
         "2단계(선형 → 물리)는 07장부터. 세 표(LDT, pg_dir, mem_map)가 관문마다 쓰는 표다.",
         17)
    d.banner(p, "int x; 의 주소 0x1234가 셸과 ls에서 서로 다른 RAM 셀인 이유 — 오늘 120분의 질문")

    # 06 선택자 0x17
    p = d.slide("1단계: 선택자 0x17이 베이스가 되는 과정", K.S_BG,
                "include/linux/sched.h:104-106, 188-231 · include/linux/head.h:4-9 — 02회차 디스크립터 그림 재사용")
    d.text(p, 1100, 4250, 15700, 600, "선택자 0x17 분해 — DS(데이터·스택)", 16,
           K.TEAL, True)
    d.text(p, 1100, 4950, 15700, 800, "0x17 = 0001 0111b", 24, K.PAPER, True)
    nbox(d, p, 1100, 6100, 5600, 2400, "bits 15:3 → index 2",
         "현재 LDT의 3번 항목\nldt[2] — 데이터·스택", s1=15)
    nbox(d, p, 7100, 6100, 4800, 2400, "bit 2 → TI = 1",
         "LDT에서 찾는다\n(0이면 GDT)", s1=15)
    nbox(d, p, 12000, 6100, 4800, 2400, "bits 1:0 → RPL = 3",
         "요청 권한 수준\n사용자 모드", s1=15)
    para(d, p, 1100, 8900, 15700, 3200,
         "CPU는 현재 LDT의 2번 항목에서 베이스·리밋을 읽는다 — 02회차에서 본 디스크립터 "
         "8바이트에 베이스 비트가 흩어져 있는 이유로 _get_base가 그것을 조립한다(17장).\n\n"
         "그 LDT가 태스크마다 다르다는 것이 오늘 질문의 절반이다(42장).", 15)
    d.text(p, 17400, 4250, 15200, 600, "LDT[2] 디스크립터 8바이트 — 베이스는 흩어져 있다",
           16, K.TEAL, True)
    bytes_spec = [("0 limit 0-7", 0), ("1 limit 8-15", 0), ("2 base 0-7", 1),
                  ("3 base 8-15", 1), ("4 base 16-23", 1), ("5 P·DPL·S·type", 0),
                  ("6 G·D·limit", 0), ("7 base 24-31", 1)]
    bw = (15200 - 7 * 120) // 8
    for i, (label, hot) in enumerate(bytes_spec):
        bx = 17400 + i * (bw + 120)
        if hot:
            nbox(d, p, bx, 5100, bw, 1700, label, None, K.TEAL, K.INK, s1=10)
        else:
            nbox(d, p, bx, 5100, bw, 1700, label, None, None, K.MUTED, s1=10)
    para(d, p, 17400, 7200, 15200, 3400,
         "TEAL 칸(바이트 2·3·4·7)이 베이스 32비트다 — desc_struct는 ulong a·b 두 개(head.h:4-6). "
         "_set_base/_get_base(sched.h:188-231)의 movb가 이 바이트들을 나르고 모은다(17장 코드). "
         "02회차 디스크립터 그림의 재사용.", 15)
    d.banner(p, "선택자 해석의 결과는 '베이스 + 리밋' 한 쌍 — 이 베이스가 태스크마다 다르다")

    # 07 선형 주소 32비트 분해
    p = d.slide("2단계: 선형 주소 32비트의 분해", K.S_BG,
                "boot/head.s:198-219 · mm/memory.c:150-189 — 페이지 = 4KB(2^12), 386 하드웨어 규격")
    nbox(d, p, 1100, 4700, 11800, 1700, "[31:22] 디렉터리 인덱스",
         "10비트 · 0~1023", K.TEAL, s1=16)
    nbox(d, p, 12900, 4700, 10800, 1700, "[21:12] 테이블 인덱스",
         "10비트 · 0~1023", K.TEAL, s1=16)
    nbox(d, p, 23700, 4700, 8900, 1700, "[11:0] 오프셋",
         "12비트 · 페이지 안 위치", K.PAPER, s1=16)
    pane(d, p, 1100, 6900, 19700, 3600, "예 — 0x04001234 분해",
         "0x04001234 = 0000 0100 0000 0000 0001 0010 0011 0100b\n"
         "디렉터리 인덱스 = 0x04001234 >> 22             = 16\n"
         "테이블 인덱스   = (0x04001234 >> 12) & 0x3ff  = 1\n"
         "오프셋         = 0x234", 14)
    nbox(d, p, 21500, 6900, 11100, 1700, "1024 × 1024 × 4KB = 4GB",
         "디렉터리 하나가 선형 공간 전체를 덮는다", s1=16)
    para(d, p, 21500, 8900, 11100, 1600,
         "비트를 세 쪽으로 자르는 것은 하드웨어다 — 소스는 그 인덱스로 표를 찾아간다(08-09장).",
         14)
    para(d, p, 1100, 10900, 19700, 1500,
         "dir 16 = 태스크 1의 첫 4MB 칸(10장) — 예시 주소는 태스크 1의 논리 주소 0x1234에 해당한다.",
         14, K.MUTED)
    d.banner(p, "10비트 + 10비트 + 12비트 — 선형 주소 한 줄이 표를 여는 열쇠 셋")

    # 08 CR3 → 디렉터리 → 테이블 → 페이지
    p = d.slide("2단계 계속: CR3 → 디렉터리 → 테이블 → 페이지", K.S_BG,
                "include/linux/sched.h:113-131 · include/linux/head.h:4-9 · boot/head.s:15-16, 213-219")
    chain = [("CR3 — 디렉터리 시작 물리 주소", None),
             ("pg_dir[1024] — 물리 0번지", "head.s:16 _pg_dir · head.h:8"),
             ("PDE — pg_dir[디렉터리 인덱스]", "예: pg_dir[16] = 0x00202007"),
             ("페이지 테이블 — 물리 = PDE & 0xfffff000", "예: 0x202000 · 항목 1024개"),
             ("PTE → 물리 페이지 + 오프셋", "예: 0x00abc005 → 0xabc000 + 0x234")]
    for i, (l1, l2) in enumerate(chain):
        y = 4400 + i * 1750
        nbox(d, p, 1100, y, 15200, 1250, l1, l2, K.PAPER, s1=14, s2=11)
        if i < 4:
            arrow(d, p, 8100, y + 1280, "↓", 20)
    para(d, p, 1100, 13300, 15200, 1200,
         "디렉터리 항목 하나 = 4MB · 테이블 항목 하나 = 4KB — 두 단계 색인 구조.", 15)
    nbox(d, p, 17400, 4400, 15200, 1500, "0.11 — 디렉터리 하나를 모든 태스크가 공유",
         None, K.TEAL, s1=16)
    para(d, p, 17400, 6200, 15200, 4200,
         "CR3 = 0 고정 — tss.cr3 = &pg_dir(sched.h:128)이고 pg_dir는 물리 0(head.s:15-16).\n\n"
         "태스크마다 바뀌는 것은 LDT 베이스(64MB 칸)뿐이다(10장). 프로세스마다 디렉터리를 "
         "바꾸는 것은 현대 리눅스의 방식이다(43장, 한 줄 대비).", 16)
    pane(d, p, 17400, 10700, 15200, 3700, "같은 그림, 숫자로",
         "pg_dir[16] = 0x00202007 → 테이블 물리 0x202000\n"
         "테이블[1]  = 0x00abc005 → 페이지 물리 0xabc000\n"
         "선형 0x04001234 → 물리 0x00abc234", 13)
    d.banner(p, "CR3는 디렉터리를 가리킬 뿐 — '누구의 디렉터리인가'는 0.11에서 성립하지 않는 질문")

    # 09 관용구
    p = d.slide("0.11 소스의 관용구: (addr>>20)&0xffc, (addr>>10)&0xffc", K.S_BG,
                "mm/memory.c:115, 160-161, 207, 255-257 — 코드 읽기 부담을 미리 줄인다")
    nbox(d, p, 1100, 4400, 6600, 1400, "(addr >> 22) × 4", None, K.PAPER, s1=16)
    d.text(p, 8000, 4750, 1500, 800, "≡", 26, K.TEAL, True)
    nbox(d, p, 9700, 4400, 8200, 1400, "(addr >> 20) & 0xffc", None, K.TEAL,
         s1=16)
    d.text(p, 18200, 4750, 14400, 800, "← 디렉터리 항목의 바이트 오프셋", 15,
           K.PAPER, True)
    nbox(d, p, 1100, 6100, 6600, 1400, "(addr >> 12) & 0x3ff × 4", None, K.PAPER,
         s1=15)
    d.text(p, 8000, 6450, 1500, 800, "≡", 26, K.TEAL, True)
    nbox(d, p, 9700, 6100, 8200, 1400, "(addr >> 10) & 0xffc", None, K.TEAL,
         s1=16)
    d.text(p, 18200, 6450, 14400, 800, "← 테이블 항목의 바이트 오프셋", 15,
           K.PAPER, True)
    pane(d, p, 1100, 7900, 19700, 3200, "왜 같은가 — 비트로 보기",
         "idx = addr >> 22                     # 0 ~ 1023\n"
         "idx * 4 = (addr >> 22) << 2 = addr >> 20   # 4의 배수 = &0xffc 범위\n"
         "표의 시작 주소(0) + idx*4  →  그대로 포인터로 쓴다(pg_dir = 물리 0 덕)", 13)
    para(d, p, 1100, 11400, 19700, 2800,
         "이 식이 memory.c 곳곳에서 반복된다 — 115(free_page_tables) · 160-161(copy_page_tables) · "
         "207(put_page) · 255-257(do_wp_page, 08회차). 오른쪽 칸 표기가 나오면 '인덱스×4'로 읽으면 된다.",
         16)
    nbox(d, p, 21500, 7900, 11100, 6300, "약속 세 가지",
         "· _pg_dir = 물리 0(head.s:15-16)\n· identity 매핑 — 선형=물리(0~16MB)\n· 커널 세그먼트 베이스 0\n\n→ 물리 주소를 그대로 포인터처럼 쓸 수 있다", s1=16, s2=13)
    d.banner(p, ">>20 &0xffc를 보면 '아, 디렉터리 항목 주소구나' — 인덱스 ×4와 같은 뜻")

    # 10 64MB 칸
    p = d.slide("왜 64MB씩인가: 태스크 번호가 곧 선형 공간 위치", K.S_BG,
                "kernel/fork.c:39-61 · include/linux/sched.h:88 — NR_TASKS=64(sched.h:4), 최대 64태스크")
    cells = [("nr0\n0~64MB", "실제 사용 640KB(리밋)", 0),
             ("nr1\n64~128MB", "init", 1),
             ("nr2\n128~192MB", "셸·자식들", 1),
             ("nr3\n192~256MB", "", 0),
             ("…", "64칸 = 4GB", 0),
             ("nr63", "마지막 칸", 0)]
    cw = [5200, 5200, 5200, 5200, 5200, 5500]
    cx = 1100
    for (l1, l2, hot), w in zip(cells, cw):
        nbox(d, p, cx, 4800, w, 1900, l1, l2,
             K.TEAL if hot else K.PAPER, s1=15, s2=11)
        cx += w
    nbox(d, p, 1100, 7300, 9900, 2100, "64MB = 0x4000000",
         "fork.c:52 — new_data_base = nr * 0x4000000", s1=17)
    nbox(d, p, 11300, 7300, 9900, 2100, "디렉터리 항목 16개",
         "64MB = 4MB × 16 — 태스크당 PDE 16칸", s1=17)
    nbox(d, p, 21500, 7300, 11100, 2100, "start_code",
         "sched.h:88 — 이 칸의 시작을 기록", s1=17)
    para(d, p, 1100, 9800, 31500, 3600,
         "태스크 번호 nr이 곧 선형 공간의 위치다 — 태스크 0은 0~64MB(리밋 640KB), 1은 64MB~, "
         "2는 128MB~ … 최대 64개(NR_TASKS=64).\n\n"
         "오늘 질문의 절반이 여기서 풀린다: 논리 주소가 같아도 LDT 베이스가 nr×64MB로 다르면 "
         "선형 주소부터 갈라선다(42장). 배정하는 코드는 15-16장 copy_mem.", 17)
    d.banner(p, "nr * 0x4000000 — 태스크 번호 하나로 선형 공간 64MB가 통째로 정해진다")

    # ── 코드 11–26 ────────────────────────────────────────────
    # 11 setup_paging (1/2)
    p = d.slide("코드: head.s setup_paging (1/2) 테이블 채우기", K.S_CODE,
                "boot/head.s:15-16, 108-124, 198-212 — _pg_dir=물리0 · pg0~pg3=.org 0x1000~0x4000")
    d.code_panel(p, "src/boot/head.s", 198, 212, 1100, 4400, 18400, 9600,
                 size=10)
    d.text(p, 19900, 4400, 12700, 600, "결과 — 16MB identity mapping", 16,
           K.TEAL, True)
    rows = ["pg_dir[0] = 0x00001007 → pg0 (물리 0x1000)",
            "pg_dir[1] = 0x00002007 → pg1 (물리 0x2000)",
            "pg_dir[2] = 0x00003007 → pg2 (물리 0x3000)",
            "pg_dir[3] = 0x00004007 → pg3 (물리 0x4000)"]
    for i, r in enumerate(rows):
        nbox(d, p, 19900, 5100 + i * 1050, 12700, 900, r, None, K.PAPER, s1=12)
    d.text(p, 19900, 9500, 12700, 1700,
           "pg0[0]     = 0x000007 → 물리 0x000000\npg3[1023] = 0xfff007 → 물리 0xfff000",
           13, K.PAPER, mono=True)
    badge(d, p, 19900, 11500, 12700, "선형 0~16MB ≡ 물리 0~16MB — identity mapping",
          K.TEAL, 800, 14)
    para(d, p, 19900, 12600, 12700, 1800,
         "뒤에서부터 채운다(210행) — 0xfff007에서 0x1000씩 빼며 PTE 기록.", 13)
    d.banner(p, "rep stosl 5페이지 0으로 → 디렉터리 4항목 → PTE 4096개 — 16MB 일대일 매핑 완성")

    # 12 setup_paging (2/2)
    p = d.slide("코드: head.s setup_paging (2/2) 켜기", K.S_CODE,
                "boot/head.s:135-141, 213-219 — 1회차 27장과 같은 코드, 이제 비트의 의미를 다 안다")
    d.code_panel(p, "src/boot/head.s", 213, 219, 1100, 4400, 15200, 5200,
                 size=10, caption_extra="켜기 — CR3 적재 · PG 비트")
    d.code_panel(p, "src/boot/head.s", 135, 141, 1100, 9900, 15200, 4400,
                 size=8, caption_extra="after_page_tables — _main을 밀어 둔 곳")
    para(d, p, 16900, 4400, 15700, 10000,
         "xorl %eax,%eax · movl %eax,%cr3 — 디렉터리 시작 = 물리 0. pg_dir가 0번지라는 "
         "약속(15-16행)이 여기 쓰인다.\n\n"
         "orl $0x80000000,%eax · movl %eax,%cr0 — CR0.PG = 1. 이 순간부터 모든 주소가 "
         "페이지 변환을 지난다.\n\n"
         "ret — 스택 top은 135-141에서 push해 둔 _main. setup_paging의 ret가 main()으로 "
         "'돌아간다'.\n\n"
         "1회차 27장에서 이 코드를 실행만 봤다 — 이제 7(P·RW·US)과 0xfff007의 의미를 "
         "읽을 수 있다(13장).", 16)
    d.banner(p, "켜기는 세 줄 — 어려운 부분은 이미 지난 장(테이블 채우기)이었다")

    # 13 PTE 비트
    p = d.slide("코드: PTE 한 항목의 비트: P / RW / US", K.S_CODE,
                "boot/head.s:198-219 · mm/memory.c:173-189, 197-219 — 08회차 CoW가 재사용하는 그림")
    nbox(d, p, 1100, 4500, 22000, 1600, "[31:12] 페이지 물리 주소 (20비트)",
         None, K.TEAL, s1=16)
    nbox(d, p, 23100, 4500, 2800, 1600, "bit2 U/S", None, K.PAPER, s1=14)
    nbox(d, p, 25900, 4500, 2800, 1600, "bit1 R/W", None, K.PAPER, s1=14)
    nbox(d, p, 28700, 4500, 2800, 1600, "bit0 P", None, K.ORANGE, s1=14)
    d.text(p, 1100, 6250, 31500, 500,
           "P = present(페이지 있음) · R/W = 읽기/쓰기 · U/S = 사용자(1)/관리자(0) 접근", 13,
           K.MUTED)
    nbox(d, p, 1100, 7100, 9900, 1800, "+7 = 111b — P+RW+US",
         "head.s 0xfff007 · put_page:213,216", K.TEAL, s1=15)
    nbox(d, p, 11300, 7100, 9900, 1800, "+5 = 101b — P+US (RW=0)",
         "copy_page_tables 결과(25장)", K.PAPER, s1=15)
    nbox(d, p, 21500, 7100, 11100, 1800, "&= ~2 — RW만 끈다",
         "memory.c:177 — 읽기 전용 공유", K.PAPER, s1=15)
    d.code_panel(p, "src/boot/head.s", 207, 208, 1100, 9400, 15200, 2600,
                 size=10, caption_extra="뒤에서부터 — 0xfff007에서 시작")
    d.code_panel(p, "src/mm/memory.c", 177, 178, 1100, 12200, 15200, 2300,
                 size=10, caption_extra="copy_page_tables — RW 비트 제거")
    para(d, p, 16900, 9400, 15700, 5100,
         "0.11이 만드는 하위 비트 조합은 0 / 5 / 7 세 가지뿐이다 — 비교 ②(31장).\n\n"
         "US=0(커널 전용) 페이지는 0.11에 없다 — 커널 보호는 세그먼트 DPL이 담당한다(§8).\n\n"
         "08회차 Copy-on-Write가 바로 이 bit1(R/W) 하나로 동작한다.", 15)
    d.banner(p, "비트 하나가 정책이다 — 오늘 25장에서 이 비트를 끄고, 08회차에서 다시 켠다")

    # 14 INIT_TASK LDT
    p = d.slide("코드: 태스크 0의 LDT — INIT_TASK", K.S_CODE,
                "include/linux/sched.h:113-131 — 주석 줄(125·128)은 발췌 표시에서 빈 줄이 된다(아래 패널에 원문)")
    d.code_panel(p, "src/include/linux/sched.h", 123, 131, 1100, 4400, 15500,
                 6300, size=10, caption_extra="ldt[3] + tss 시작부")
    pane(d, p, 1100, 11000, 15500, 2500,
         "주석 앞이라 잘리는 두 줄 원문 (sched.h)",
         "125  /* ldt */ {0x9f,0xc0fa00}, \\\n"
         "128  /*tss*/ {0,PAGE_SIZE+(long)&init_task,0x10,0,…,(long)&pg_dir,\\",
         12)
    d.table(p, 17600, 4400, [3600, 5100, 7000], [
        ["항목", "값", "해독"],
        ["ldt[0]", "{0,0}", "null — index 0 선택자용"],
        ["ldt[1] cs", "{0x9f,0xc0fa00}", "베이스 0 · 리밋 640KB · 코드 DPL3"],
        ["ldt[2] ds", "{0x9f,0xc0f200}", "베이스 0 · 리밋 640KB · 데이터 DPL3"],
        ["tss.cr3", "(long)&pg_dir", "CR3 = 물리 0 — 전 태스크 공유"],
    ], row_h=1050, size=13)
    d.code_panel(p, "src/boot/head.s", 234, 238, 17600, 10100, 15000, 3800,
                 size=9, caption_extra="GDT — 커널 코드/데이터(베이스 0, 16MB)")
    para(d, p, 1100, 14100, 31500, 1600,
         "해독 — 0xfa/0xf2 = P·DPL3·코드/데이터 · byte6 0xc0 = G(4KB 단위) → 리밋 (0x9f+1)×4KB = 640KB · 베이스 0.\n"
         "태스크 0은 베이스 0 — 논리 주소 = 선형 주소. 다른 태스크는 베이스가 nr×64MB(15-16장).",
         14, K.PAPER, True)

    # 15 copy_mem (1/2)
    p = d.slide("코드: fork.c copy_mem (1/2) — 자식 칸 배정 계산", K.S_CODE,
                "kernel/fork.c:39-61 전반 · include/linux/sched.h:188-231(get_base/get_limit) — 06회차 복습 위치")
    d.code(p, "src/kernel/fork.c", 39, 52, "", expl_size=15)
    cexpl(d, p,
          "get_limit(0x0f) / get_limit(0x17)\n부모의 코드·데이터 리밋 조사 — 0x0f=cs, 0x17=ds 선택자(lsll, 17장)\n\n"
          "get_base(current->ldt[1])\n부모 LDT에서 베이스 읽기. cs·ds 베이스가 다르면 panic(48-49) — 분리 공간 미지원\n\n"
          "new_data_base = new_code_base = nr * 0x4000000 (52행)\n자식의 64MB 칸 계산 — 10장 그림의 숫자\n\n"
          "p->start_code = new_data_base (53행)\ntask_struct 필드(sched.h:88)에 기록 — 08회차 do_no_page가 읽는다", 15)
    d.banner(p, "자식의 칸은 '부모 것'이 아니라 nr로 새로 계산한다 — 배정은 이 넉 줄로 끝")

    # 16 copy_mem (2/2)
    p = d.slide("코드: fork.c copy_mem (2/2) — 베이스 설치와 테이블 복사", K.S_CODE,
                "kernel/fork.c:39-61 후반 · mm/memory.c:150-189 — 설치(set_base)와 복사(copy_page_tables)")
    d.code_panel(p, "src/kernel/fork.c", 53, 61, 1100, 4400, 15500, 6300,
                 size=10, caption_extra="set_base 설치 → copy_page_tables → 실패 롤백")
    para(d, p, 1100, 11000, 15500, 3400,
         "set_base(p->ldt[1]/[2]) — 자식 LDT 디스크립터에 새 베이스 설치(17장 매크로).\n"
         "copy_page_tables(old, new, limit) — 선형 공간 복사(24-25장).\n"
         "실패 시 free_page_tables(new_data_base, limit)로 되돌리고 -ENOMEM.", 15)
    nbox(d, p, 16900, 4400, 15700, 1700, "부모 (nr=1) — 베이스 0x4000000",
         "old_data_base · LDT는 부모 것", K.TEAL, s1=16)
    arrow(d, p, 24000, 6250, "↓", 26, K.ORANGE)
    d.text(p, 17400, 6300, 14600, 700,
           "copy_page_tables(0x4000000, 0x8000000, data_limit)", 14, K.ORANGE,
           True)
    nbox(d, p, 16900, 7300, 15700, 1700, "자식 (nr=2) — 베이스 0x8000000",
         "start_code · LDT 베이스 교체 완료", K.TEAL, s1=16)
    nbox(d, p, 16900, 9400, 15700, 1500, "실패 → free_page_tables(0x8000000, limit) → -ENOMEM",
         None, None, K.MUTED, s1=13)
    para(d, p, 16900, 11200, 15700, 3200,
         "copy_process(fork.c:111)은 tss.ldt = _LDT(nr)로 자식의 LDT를 GDT에 등록(129-130) — "
         "스케줄러가 자식을 실행하면 자동으로 이 베이스가 걸린다.", 15)
    d.banner(p, "copy_mem 12줄 요약 — 칸 계산(15장) + LDT 설치·테이블 복사(이 장)")

    # 17 베이스 꺼내기/넣기
    p = d.slide("코드: 디스크립터에서 베이스 꺼내기/넣기", K.S_CODE,
                "include/linux/sched.h:188-198(_set_base) · 214-226(_get_base) · 228-231(get_limit=lsll) — 읽기용")
    d.code_panel(p, "src/include/linux/sched.h", 188, 198, 1100, 4400, 12200,
                 6800, size=9, caption_extra="_set_base — 바이트 2·4·7에 분해 저장")
    d.text(p, 1100, 11500, 12200, 500, "베이스 32비트가 흩어져 사는 곳", 13,
           K.TEAL, True)
    for i, (label, hot) in enumerate(bytes_spec):
        bx = 1100 + i * (1420 + 110)
        nbox(d, p, bx, 12200, 1420, 1300, label, None,
             K.TEAL if hot else None, K.INK if hot else K.MUTED, s1=9)
    d.text(p, 1100, 13650, 12200, 700,
           "movb 한 개가 한 바이트씩 나른다 — 베이스는 2·3·4·7에, 리밋은 0·1·6에", 12,
           K.MUTED)
    d.code_panel(p, "src/include/linux/sched.h", 214, 226, 17600, 4400, 15000,
                 6900, size=8, caption_extra="_get_base — 바이트 7·4·2·3을 모아 32비트")
    d.code_panel(p, "src/include/linux/sched.h", 228, 231, 17600, 11500, 15000,
                 3100, size=8, caption_extra="get_limit — lsll 명령(17행 어셈블리 아님)")
    d.banner(p, "읽기만 한다, 암기하지 않는다 — '베이스가 왜 이렇게 복잡한가'에 답하는 슬라이드")

    # 18 mem_map
    p = d.slide("코드: mem_map — 물리 페이지 장부", K.S_CODE,
                "mm/memory.c:39-57 — invalidate()는 CR3 재적재 = TLB 무효화(§8: '캐시 비우기'라 말하지 않는다)")
    d.code_panel(p, "src/mm/memory.c", 43, 57, 1100, 4400, 18400, 9600,
                 size=10)
    para(d, p, 19900, 4400, 12700, 1400,
         "물리 페이지 한 장당 바이트 하나 — 3840칸 짜리 무편 장부.", 16)
    nbox(d, p, 19900, 6000, 3900, 2500, "0~1MB", "커널·BIOS\n장부 밖", None,
         K.MUTED, s1=14)
    nbox(d, p, 13900, 6000, 8700, 2500, "1MB~16MB — 장부 대상",
         "15MB = 3840페이지 (PAGING_PAGES)", K.TEAL, s1=13)
    nbox(d, p, 19900, 8900, 12700, 1500, "mem_map[3840]",
         "MAP_NR(addr) = (addr − 0x100000) >> 12", K.PAPER, s1=14)
    para(d, p, 19900, 10800, 12700, 3200,
         "칸 값: USED=100(커널·버퍼, 해제 불가) · 0(미사용) · 1(단독) · n≥2(공유).\n\n"
         "1MB 아래는 장부에 없다 — 공유해도 세지 않고 free_page도 무시한다(22장).", 14)
    d.banner(p, "LOW_MEM=0x100000(1MB) · PAGING_MEMORY=15MB — 장부는 '1MB 위 물리 페이지'만 다룬다")

    # 19 mem_init
    p = d.slide("코드: mem_init — 장부 초기화", K.S_CODE,
                "mm/memory.c:399-411 · init/main.c:112-126 — memory_end 최대 16MB · 버퍼 경계는 main.c가 정한다")
    nbox(d, p, 1100, 4300, 6000, 1400, "0~1MB — USED", "커널·BIOS", None,
         K.MUTED, s1=13)
    nbox(d, p, 7200, 4300, 7500, 1400, "1MB~4MB — USED", "버퍼 캐시(buffer_memory_end)",
         None, K.MUTED, s1=13)
    nbox(d, p, 14800, 4300, 17800, 1400, "4MB~16MB — 0 (할당 가능)",
         "main_memory_start ~ memory_end · 3072페이지", K.TEAL, s1=13)
    d.text(p, 1100, 3900, 31500, 400,
           "mem_init(main_memory_start, memory_end) 직후 mem_map 상태 — QEMU 기본 16MB · 버퍼 4MB 기준",
           11, K.MUTED)
    d.code_panel(p, "src/mm/memory.c", 399, 411, 1100, 6000, 15200, 7750,
                 size=9, caption_extra="전부 USED → start_mem..end_mem만 0")
    d.code_panel(p, "src/init/main.c", 112, 126, 16900, 6000, 15700, 7900,
                 size=8, caption_extra="memory_end·buffer_memory_end 결정 → mem_init 호출")
    d.banner(p, "장부의 '0 칸'은 4MB~16MB뿐 — get_free_page가 줄 수 있는 페이지의 전부다")

    # 20 get_free_page (1/2)
    p = d.slide('코드: get_free_page (1/2) — "첫 번째(사실은 마지막)" 빈 페이지 찾기', K.S_CODE,
                "mm/memory.c:63-83 전반 — 인라인 어셈블리를 줄 단위로 · 06회차 copy_process도 이 함수 사용")
    d.code_panel(p, "src/mm/memory.c", 63, 69, 1100, 4400, 15200, 5200,
                 size=10, caption_extra="탐색 — std ; repne ; scasb")
    d.text(p, 1100, 10100, 15200, 600, "mem_map 탐색 방향 — 끝(index 3839)에서부터 앞으로",
           14, K.TEAL, True)
    d.shape(p, 1100, 10900, 15200, 900, K.INK)
    for i in range(16):
        d.shape(p, 1100 + i * 950, 10900, 20, 900, K.LINE)
    d.text(p, 3600, 12050, 11000, 700, "◀◀◀  repne scasb — al(0)과 다르면 계속, 뒤로",
           15, K.TEAL, True)
    d.text(p, 1100, 13000, 15200, 1400,
           "첫 0에서 정지 — scasb가 지난 칸의 다음(1(%edi))을 1로 표시. 그 인덱스가 곧 페이지 번호다.",
           14, K.PAPER)
    para(d, p, 16900, 4400, 15700, 10000,
         "std — DF=1, scasb가 주소를 줄여 가며 검사(뒤로).\n\n"
         "repne scasb — al(=0)과 비교해 다르면 반복. ecx는 PAGING_PAGES(3840)부터 감소.\n\n"
         "jne 1f — 끝까지 0이 없으면 점프. eax는 입력 제약 \"0\"(0) 그대로 → 0 반환.\n\n"
         "movb $1,1(%%edi) — 찾은 칸을 1로 표시(할당).\n\n"
         "\"D\" (mem_map+PAGING_PAGES-1) — 탐색 시작 주소 = 배열의 마지막 칸.", 15)
    d.banner(p, "주석의 'first'와 달리 실제로는 마지막(높은 주소)부터 찾는다 — Linus 주석(60행)")

    # 21 get_free_page (2/2)
    p = d.slide("코드: get_free_page (2/2) — 물리 주소를 만들어 반환", K.S_CODE,
                "mm/memory.c:63-83 후반 — 반환값이 물리 주소라는 점이 오늘의 함정(§8)")
    d.code_panel(p, "src/mm/memory.c", 70, 83, 1100, 4400, 19700, 9050,
                 size=10, caption_extra="물리 주소 계산 + 4KB 0 채움 + 반환")
    steps = ["ecx(남은 카운터) = 3840 − idx", "sall $12 → idx × 4096",
             "addl LOW_MEM → + 0x100000", "= 물리 주소 (edx에 보관)",
             "rep stosl 1024 → 4KB를 0으로", "eax = edx — 물리 주소 반환"]
    for i, s in enumerate(steps):
        nbox(d, p, 21600, 4500 + i * 1350, 11000, 1150, s, None,
             K.TEAL if i in (2, 5) else K.PAPER, s1=14)
    para(d, p, 1100, 13700, 19700, 800,
         "반환값 0 = 실패 — 호출자(copy_process·put_page 등)가 즉시 검사한다.", 14, K.MUTED)
    d.banner(p, "반환값은 물리 주소다 — 커널이 바로 포인터처럼 쓰는 것은 identity 매핑 덕이다")

    # 22 free_page
    p = d.slide("코드: free_page — 감소시키고, 0이면 panic", K.S_CODE,
                "mm/memory.c:89-99 — 공유 카운트가 줄어드는 유일한 곳 · HIGH_MEMORY 첫 등장")
    d.code(p, "src/mm/memory.c", 89, 99, "", expl_size=15)
    cexpl(d, p,
          "addr < LOW_MEM — 그냥 반환. 커널·BIOS 영역(1MB 아래)은 장부 밖이다\n\n"
          "addr >= HIGH_MEMORY — panic(\"trying to free nonexistent page\")\n\n"
          "addr −= LOW_MEM; addr >>= 12 — 물리 주소 → mem_map 인덱스(MAP_NR 손계산)\n\n"
          "mem_map[addr]-- 후 0이 아니면(잔존) 반환 — 아직 누가 쓰고 있다\n\n"
          "이미 0이었으면(−1 됨): mem_map[addr]=0 복구 후 panic(\"trying to free free page\")\n\n"
          "copy_page_tables가 카운트를 올리고(183) 여기서 내린다", 15)
    d.banner(p, "'해제'가 아니라 '카운트 감소'다 — 0이 되는 순간이 빈 페이지")

    # 23 put_page
    p = d.slide("코드: put_page — 선형 주소에 물리 페이지 붙이기", K.S_CODE,
                "mm/memory.c:197-219 — 디렉터리 항목 없으면 테이블을 새로 만든다 · 08회차 do_no_page가 계속 부른다")
    d.code_panel(p, "src/mm/memory.c", 203, 206, 1100, 4400, 15500, 3500,
                 size=10, caption_extra="사전 검사 — page 범위·mem_map 일치")
    d.code_panel(p, "src/mm/memory.c", 207, 216, 1100, 8200, 15500, 6300,
                 size=9, caption_extra="PDE 분기 → PTE = page|7")
    nbox(d, p, 16900, 4400, 15700, 1000, "page_table = (address>>20)&0xffc — PDE 주소(09장 관용구)",
         None, K.PAPER, s1=13)
    nbox(d, p, 16900, 5600, 7300, 1700, "PDE 없음(P=0)",
         "get_free_page()로 새 테이블\n*page_table = tmp|7", K.TEAL, s1=14)
    nbox(d, p, 25100, 5600, 7300, 1700, "PDE 있음(P=1)",
         "테이블 재사용\n0xfffff000 & *page_table", K.PAPER, s1=14)
    arrow(d, p, 20200, 7350, "↓", 20)
    arrow(d, p, 28400, 7350, "↓", 20)
    nbox(d, p, 16900, 8300, 15700, 1200,
         "page_table[(address>>12)&0x3ff] = page|7 — PTE 기록(216)", None,
         K.TEAL, s1=14)
    para(d, p, 16900, 9900, 15700, 4600,
         "\"no need for invalidate\"(217) — 새로 생긴 항목은 TLB에 있던 적이 없다. "
         "기존 항목을 바꿀 때만 CR3 재적재가 필요하다(25장 187행).\n\n"
         "put_page의 인자 page는 get_free_page가 준 물리 주소다(21장).", 15)
    d.banner(p, "물리 페이지(page)를 선형 주소(address)의 PTE에 |7로 붙인다 — 디렉터리는 공짜로 따라온다")

    # 24 copy_page_tables (1/2)
    p = d.slide("코드: copy_page_tables (1/2) — 디렉터리 단위 복사", K.S_CODE,
                "mm/memory.c:150-172 — 복사 단위 = 디렉터리 항목 하나 = 4MB · 06회차 fork가 호출")
    d.code(p, "src/mm/memory.c", 150, 163, "", expl_size=15)
    cexpl(d, p,
          "158-159 — from·to는 4MB(0x3fffff) 정렬, 아니면 panic\n\n"
          "160-161 — 관용구 (addr>>20)&0xffc로 from_dir/to_dir(09장)\n\n"
          "162 — size를 4MB 단위 개수로 환산\n\n"
          "164-165 — 자식 항목 이미 있으면 panic(\"already exist\")\n\n"
          "166-167 — 부모 항목 없으면 continue\n\n"
          "루프 몸통(164-172) — get_free_page 새 테이블(169) · *to_dir = table|7(171) · "
          "nr = (from==0)?0xA0:1024(172) — 태스크 0에서 복사할 땐 160페이지=640KB만", 14)
    d.banner(p, "복사의 단위는 '디렉터리 항목 = 4MB' — 부모의 테이블을 한 칸씩 통째로")

    # 25 copy_page_tables (2/2)
    p = d.slide("코드: copy_page_tables (2/2) — PTE 복사와 공유 카운트", K.S_CODE,
                "mm/memory.c:173-189 — 177(&~2) · 180(부모 PTE) · 183(mem_map++) · 187(invalidate)")
    d.code_panel(p, "src/mm/memory.c", 173, 183, 1100, 4400, 15500, 6800,
                 size=9, caption_extra="PTE 루프 — RW 제거 후 양쪽에 기록")
    para(d, p, 1100, 11400, 15500, 3000,
         "this_page &= ~2 — RW 비트 제거(177) 후 자식 PTE에 기록(178).\n"
         "LOW_MEM 이상이면 부모 PTE도 같은 값으로(180) — 양쪽 모두 읽기 전용.\n"
         "mem_map[this_page]++ — 공유 카운트(183).\n"
         "루프 뒤 invalidate() — CR3 재적재로 TLB 무효화(187, 아래 패널).", 14)
    nbox(d, p, 16900, 4400, 7300, 1200, "부모 PTE = A|5", None, K.TEAL, s1=14)
    nbox(d, p, 25300, 4400, 7300, 1200, "자식 PTE = A|5", None, K.TEAL, s1=14)
    arrow(d, p, 19900, 5700, "↓", 20)
    arrow(d, p, 28300, 5700, "↓", 20)
    nbox(d, p, 16900, 6200, 15700, 1400, "물리 페이지 A — 내용은 하나, PTE는 둘",
         None, K.PAPER, s1=15)
    badge(d, p, 18900, 7900, 11700, "mem_map[MAP_NR(A)] = 2 — 공유 카운트", K.TEAL, 800, 14)
    d.code_panel(p, "src/mm/memory.c", 184, 189, 16900, 9900, 15700, 4300,
                 size=9, caption_extra="루프 탈출 — invalidate 후 0 반환")
    d.banner(p, "복사되는 것은 페이지 테이블(PTE)뿐 — 데이터 페이지는 공유된다(§8). 실제 복사는 08회차")

    # 26 free_page_tables
    p = d.slide("코드: free_page_tables — 4MB 단위로 전부 반납", K.S_CODE,
                "mm/memory.c:105-131 — exit(10회차)·exec(09회차)가 호출 · 태스크 0(from=0)은 해제 금지")
    d.code(p, "src/mm/memory.c", 105, 118, "", expl_size=15)
    cexpl(d, p,
          "110-111 — 4MB 정렬 검사, 아니면 panic\n\n"
          "112-113 — from==0(태스크 0)이면 panic(\"Trying to free up swapper memory space\")\n\n"
          "114 — size를 4MB 단위 개수로\n\n"
          "115 — dir = (from>>20)&0xffc, 관용구 재등장\n\n"
          "117-118 — 빈 디렉터리 항목은 continue\n\n"
          "몸통(119-131) — present 페이지 free_page(121-122) · 테이블도 free_page(126) · "
          "PDE=0(127) · invalidate()(129)", 14)
    d.banner(p, "태스크가 사라질 때 선형 공간 전체를 반납 — 페이지 단위 해제는 free_page 하나가 한다")

    # ── 상태도 27–28 ──────────────────────────────────────────
    # 27 물리 페이지 상태
    p = d.slide("상태 변화도 ①: 물리 페이지 한 장의 일생", K.S_STATE,
                "mm/memory.c:39-57, 63-99, 150-189, 399-411 — 상태 = mem_map[MAP_NR] 바이트 하나의 값")
    nbox(d, p, 1100, 4600, 6800, 1800, "USED = 100", "커널·버퍼 영역 — 영구",
         None, K.MUTED, s1=18)
    nbox(d, p, 9400, 4600, 6800, 1800, "0", "미사용 — get_free_page의 표적",
         K.PAPER, s1=18)
    nbox(d, p, 17700, 4600, 6800, 1800, "1", "단독 소유 — 마음대로 쓰기",
         K.TEAL, s1=18)
    nbox(d, p, 26000, 4600, 6600, 1800, "n ≥ 2", "공유 — PTE 수만큼",
         K.TEAL, s1=18)
    d.text(p, 2500, 6600, 12500, 900, "get_free_page:69 — 0 → 1 (뒤에서 첫 0)",
           14, K.TEAL, True)
    d.text(p, 16200, 6600, 12500, 900, "copy_page_tables:183 — 1 → 2 · RW=0으로",
           14, K.TEAL, True)
    d.text(p, 2500, 7600, 12500, 900, "free_page:96 — 1 → 0", 14, K.ORANGE, True)
    d.text(p, 16200, 7600, 12500, 900, "free_page:96 — n → n−1 (0이면 panic)",
           14, K.ORANGE, True)
    d.table(p, 1100, 8900, [6600, 10600, 6600, 7700], [
        ["전환", "원인 — 함수 (src 줄)", "mem_map 바이트", "비고"],
        ["전체 USED → 0 구간", "mem_init (399-411)", "USED → 0 (start_mem..end_mem)", "부팅 시 1회"],
        ["0 → 1", "get_free_page:69", "0 → 1", "뒤에서 첫 0"],
        ["1 → 2", "copy_page_tables:183", "+1", "양쪽 PTE RW=0"],
        ["n → n−1 → 0", "free_page:96-98", "−1 (0이면 panic)", "exit·exec 경유"],
        ["(08 예고) 분리", "un_wp_page (memory.c:221-238)", "−1 · 새 페이지 +1", "첫 쓰기 폴트"],
    ], row_h=900, size=13)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)
    d.banner(p, "유지 조건 — 카운트 = 그 물리 페이지를 가리키는 PTE 수(1MB 이상만 집계)", 15000, 16)

    # 28 태스크 선형 공간 상태
    p = d.slide("상태 변화도 ②: 태스크 선형 공간의 상태", K.S_STATE,
                "kernel/fork.c:39-61 · mm/memory.c:105-131, 150-189, 197-219 — 호출 순서도가 아니라 상태 표다")
    nbox(d, p, 1100, 4600, 6800, 2000, "비어 있음",
         "PDE 16칸 모두 0\n태스크 슬롯만 존재", K.PAPER, s1=17)
    nbox(d, p, 9400, 4600, 6800, 2000, "배정됨",
         "copy_mem — LDT 베이스 = nr×64MB\n테이블 복사(모든 PTE RW=0)", K.TEAL, s1=17)
    nbox(d, p, 17700, 4600, 6800, 2000, "사용 중",
         "put_page · 08 폴트로\nPTE 추가(RW=1)", K.TEAL, s1=17)
    nbox(d, p, 26000, 4600, 6600, 2000, "해제됨",
         "free_page_tables —\n테이블·페이지 반납 → 비어 있음으로", K.PAPER, s1=17)
    d.text(p, 1650, 6900, 7000, 600, "copy_mem →", 13, K.TEAL, True)
    d.text(p, 9950, 6900, 7000, 600, "put_page / #PF(08) →", 13, K.TEAL, True)
    d.text(p, 18250, 6900, 7000, 600, "free_page_tables →", 13, K.ORANGE, True)
    d.text(p, 26550, 6900, 6400, 600, "다시 '비어 있음'", 13, K.MUTED)
    d.table(p, 1100, 8000, [5600, 15200, 10700], [
        ["상태 전환", "변경 데이터", "코드"],
        ["비어 있음 → 배정됨", "ldt[1]·ldt[2] 베이스 · start_code · pg_dir[16nr..16nr+15] 테이블 · mem_map(+)", "fork.c:39-61 · memory.c:150-189"],
        ["배정됨 → 사용 중", "해당 PTE 1개(0→7) · mem_map +1", "memory.c:197-219 · mm/page.s(08)"],
        ["사용 중 → 해제됨", "PTE 전부 0 · PDE 0 · mem_map −n", "memory.c:105-131"],
    ], row_h=1400, size=14)
    para(d, p, 1100, 13800, 31500, 1000,
         "exec(09)·exit(10)은 '해제됨'으로, 08회차 폴트는 '사용 중'으로 간다 — 상태도 ①은 물리 페이지 시점, 여기는 태스크 시점.", 14)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 비교 29–32 ────────────────────────────────────────────
    # 29 비교 ① (1/2)
    p = d.slide("비교 ① (1/2): 논리 / 선형 / 물리 주소 — 누가 만들고 어느 표로", K.S_CMP,
                "kernel/fork.c:52-55 · boot/head.s:198-212 · mm/memory.c:197-219, 399-411 — 축 앞 2개(분할 사유 §10)")
    d.table(p, 1100, 4500, [6600, 9000, 9000, 6900], [
        ["주소", "누가 만드나", "어느 표로 다음 단계로", "오늘 시연 값(예)"],
        ["논리 — 선택자:오프셋", "컴파일러·링커 (프로그램 안의 숫자)", "LDT·GDT — 세그먼트 베이스·리밋", "0x0f:0x0000 (셸)"],
        ["선형 — 32비트 한 줄", "CPU 세그먼트 유닛 (베이스 + 오프셋)", "pg_dir + 페이지 테이블 — PDE/PTE", "0x8000000"],
        ["물리 — 실제 RAM 주소", "CPU 페이징 유닛 (표 조회)", "없음 — 여기가 도착점", "캡처로 확정(37장)"],
    ], row_h=1500, size=14)
    para(d, p, 1100, 11000, 31500, 3200,
         "같은 '주소'라는 말이 세 개를 가리킨다 — 오늘 질문의 '같은 숫자 주소'는 논리 주소다.\n"
         "논리는 프로그램이, 선형은 세그먼트 유닛이, 물리는 페이징 유닛이 만든다 — 화살표마다 담당이 다르다(05장).\n"
         "나머지 두 축(설정 코드 · GDB 보는 법)은 다음 장.", 16)
    d.banner(p, "주어(char)가 같아도 서술어가 셋 — 어느 주소인지 먼저 묻는 습관")

    # 30 비교 ① (2/2)
    p = d.slide("비교 ① (2/2): 논리 / 선형 / 물리 주소 — 설정 코드와 GDB", K.S_CMP,
                "kernel/fork.c:52-55 · boot/head.s:198-212 · mm/memory.c:197-219, 399-411 — 시연(34-40장)이 이 열을 그대로 쓴다")
    d.table(p, 1100, 4400, [4200, 13000, 14300], [
        ["주소", "0.11에서 설정하는 코드", "GDB에서 보는 법"],
        ["논리", "fork.c:52-55 — nr*0x4000000을 ldt 베이스로", "p/x task[n]->start_code — 그 태스크의 베이스 확인"],
        ["선형", "head.s:198-212(디렉터리·테이블) · memory.c:197-219(put_page)", "x/wx 0x80 등 — 선형 주소로 PDE/PTE 직접 읽기"],
        ["물리", "mem_init(memory.c:399-411) — mem_map으로 관리", "PTE & 0xfffff000 · x/16xb 물리 — identity 덕에 커널 선형으로 읽음"],
    ], row_h=1800, size=14)
    para(d, p, 1100, 12000, 31500, 2600,
         "오른쪽 열을 시연(34-40장)에서 그대로 쓴다 — 캡처마다 '이 값이 어느 축의 주소인지' 먼저 묻는다.\n"
         "물리 주소로 GDB가 읽히는 것은 0~16MB identity 매핑 덕이다(§8: '가상 주소'라 부르지 않는다).", 16)
    d.banner(p, "세 주소를 코드로 설정하고 GDB로 확인한다 — 오늘 시연의 뼈대")

    # 31 비교 ② PTE 하위 비트
    p = d.slide("비교 ②: 0.11이 실제로 만드는 PTE 하위 비트 조합", K.S_CMP,
                "mm/memory.c:105-131, 150-189, 197-219 · boot/head.s:198-219 — '다른 조합은 0.11이 만들지 않는다'")
    d.table(p, 1100, 4400, [3000, 5400, 11600, 11500], [
        ["값", "비트 (P,RW,US)", "누가 만드나", "의미"],
        ["0", "000", "free_page_tables(PDE/PTE=0) · 초기 상태", "부재 — 08회차 do_no_page의 출발점"],
        ["5", "101", "copy_page_tables:177-180 · try_to_share(08)", "present + 사용자, 읽기 전용 — COW 대기"],
        ["7", "111", "head.s:208(0xfff007) · put_page:213,216 · un_wp_page(08)", "present + 읽기/쓰기 + 사용자"],
    ], row_h=1600, size=14)
    para(d, p, 1100, 11200, 31500, 3400,
         "이 세 조합(0 / 5 / 7) 외에 0.11 커널은 만들지 않는다.\n\n"
         "US=0(커널 전용 페이지)는 없다 — 커널 보호는 세그먼트 DPL(GDT 0x08·0x10, DPL=0)이 담당한다(§8).\n"
         "RW=1·US=0 같은 조합도 head.s가 만든 적이 없다 — 5와 7의 차이는 bit1(RW)뿐이다(13장 그림).", 16)
    d.banner(p, "PTE 하위 비트는 사실상 '0 / 5 / 7'의 세 글자 — 다음 회차 내내 이 세 글자로 읽는다")

    # 32 비교 ③ GDT vs LDT
    p = d.slide("비교 ③: 선택자가 참조하는 표 — GDT와 LDT", K.S_CMP,
                "boot/head.s:234-238 · include/linux/sched.h:153-158 · kernel/sched.c:385-405 · include/asm/system.h:65-66")
    d.table(p, 1100, 4400, [4200, 13300, 14000], [
        ["항목", "GDT", "LDT"],
        ["내용", "커널 코드(0x08)·데이터(0x10) + _TSS(n)·_LDT(n) 디스크립터", "태스크별 코드(0x0f)·데이터(0x17) — ldt[3](sched.h:104-106)"],
        ["베이스", "0 · 리밋 16MB — head.s:234-238", "nr × 0x4000000 — fork.c:54-55가 set_base로 설치"],
        ["만든 곳·등록", "head.s:234-238 · sched.c:385-405(set_tss/ldt_desc, ltr(0)·lldt(0))", "fork.c copy_mem · copy_process:129-130(GDT에 TSS/LDT 등록)"],
        ["언제 바뀌나", "부팅 후 고정(lgdt)", "switch_to의 태스크 전환마다 — TSS의 ldt 필드가 가리키는 LDT로"],
    ], row_h=1700, size=13)
    para(d, p, 1100, 13300, 31500, 1400,
         "선택자의 TI 비트(06장)가 어느 표를 볼지 정한다 — 0x08·0x10은 GDT(TI=0), 0x0f·0x17은 현재 LDT(TI=1).\n"
         "같은 0x17이어도 '현재 LDT'가 태스크마다 다르다 — 이것이 질문의 답 1단(42장).", 15)

    # ── 시연 33–41 ────────────────────────────────────────────
    # 33 시연 준비
    p = d.slide("시연 준비: lab 환경과 심볼 이름", K.S_DEMO,
                "lab/ 은 yuan-xy 빌드(GNU as) — 심볼에 _가 없다 · 코드 캡션 줄 번호는 원본 src/ 기준(§11)")
    auto_pane(d, p, 1100, 4300, 15200, 10100,
              "터미널 — 환경 준비",
              "$ cd lab\n"
              "$ make debug\n"
              "#  → QEMU(i386 TCG) 부팅 · gdbstub :1234 대기\n"
              "$ gdb tools/system\n"
              "(gdb) target remote :1234\n"
              "(gdb) c\n"
              "#  셸 프롬프트까지 부팅 → Ctrl-C 로 정지\n"
              "#  중단점 없음 — 정지 상태에서 관찰만(§5)\n"
              "(gdb) set pagination off\n"
              "(gdb) p/x pg_dir[0]\n"
              "#  심볼에 밑줄 없음: pg_dir, mem_map, task, current", 13)
    para(d, p, 16900, 4300, 15700, 10100,
         "심볼 이름 주의\nlab/ 빌드(GNU as)는 심볼에 밑줄이 없다 — pg_dir, mem_map, task, current "
         "(src/의 _pg_dir와 대응).\n\n"
         "코드 캡션의 줄 번호는 원본 src/ 기준 — lab/ 소스와 줄이 다를 수 있으므로 캡처마다 각주로 병기한다.\n\n"
         "캡처 각주 양식(§5)\n\"lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜\"\n\n"
         "오늘 캡처 11종(01-11) — materials/07-paging/captures/\n"
         "01 CR3 · 02 x/4wx 0 · 03 task2 start_code · 04 PDE/PTE · 05 물리 16바이트 · "
         "06 선형 16바이트 · 07 mem_map 조회 · 08 태스크1 PDE/PTE · 09 커널 첫 바이트 · "
         "10 태스크1 선형 첫 바이트 · 11 calc_mem 출력\n"
         "확보 전에는 예상 출력 패널(실측 아님)로 대체한다.", 15)
    d.banner(p, "모든 시연은 '부팅 완료 후 정지' 상태에서 — 중단점 없음(§5)")

    # 34 시연 A-1
    p = d.slide("시연 A-1: CR3와 페이지 디렉터리 읽기", K.S_DEMO,
                "boot/head.s:198-219(기대값 근거 203-206) · lab/ 빌드 · QEMU i386 · GDB · 수정 없음")
    auto_pane(d, p, 1100, 4300, 15200, 10100,
              "GDB — CR3 · pg_dir[0..3]",
              "(gdb) monitor info registers\n"
              "CR0 = 0x80000011    # bit31 PG 켜짐\n"
              "CR3 = 0x00000000    # 디렉터리 = 물리 0\n"
              "#  p/x $cr3 는 gdbstub 버전에 따라 없을 수 있음\n"
              "\n"
              "(gdb) x/4wx 0\n"
              "0x0 <pg_dir>: 0x00001007 0x00002007\n"
              "              0x00003007 0x00004007\n"
              "\n"
              "(gdb) x/wx 0x40      # pg_dir[16] — 태스크 1\n"
              "(gdb) x/wx 0x80      # pg_dir[32] — 태스크 2\n"
              "#  둘 다 0이 아닌 값(…|7)이면 성공", 13)
    para(d, p, 16900, 4300, 15700, 10100,
         "관찰 포인트\n\n"
         "· CR3 = 0 — 08장 그림의 실측\n"
         "· CR0의 PG 비트 — 페이징 켜짐(12장)\n"
         "· pg_dir[0..3] = pgN+7 — head.s:203-206 기대값 그대로\n"
         "· 0x40·0x80이 0이 아니다 = 태스크 1·2의 테이블이 존재(copy_mem의 결과)\n\n"
         "기대 출력 근거: head.s:198-219 · 캡처는 다음 장(35)", 15)

    # 35 캡처 A-1
    p = d.slide("캡처 A-1: info registers / x/4wx 0", K.S_DEMO,
                "각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 사전 캡처는 '기존 기록' 라벨(§5)")
    d.placeholder_output(p, 1100, 4300, 15200, 5600,
                         "(gdb) monitor info registers\n"
                         "EAX=… EBX=… ECX=… EDX=…\n"
                         "CR0 = 0x80000011   # bit31 PG=1\n"
                         "CR3 = 0x00000000   # 디렉터리 = 물리 0",
                         "01-info-registers-cr3.png")
    d.placeholder_output(p, 16900, 4300, 15700, 5600,
                         "(gdb) x/4wx 0\n"
                         "0x0 <pg_dir>: 0x00001007 0x00002007\n"
                         "              0x00003007 0x00004007\n"
                         "(gdb) x/wx 0x40 ; x/wx 0x80\n"
                         "# 0x00202007(태스크1) · 0x00302007(태스크2)",
                         "02-x4wx-0-pg-dir.png")
    pane(d, p, 1100, 10200, 15200, 2400, "손 계산 — 0x00001007",
         "테이블 물리 주소 = 0x00001000 (= 값 & 0xfffff000)\n"
         "하위 7 = 111b = P + RW + US (13장 비트 그림)", 13)
    para(d, p, 16900, 10200, 15700, 4200,
         "\"head.s:203-206의 결과를 지금 눈으로 확인\" — 값의 형태(하위 007, 4칸 연속)가 "
         "기대와 같은지 본다.\n\n"
         "구체 숫자는 부팅마다 달라질 수 있다 — 슬라이드 기대값은 '형태'다(§8).", 15)
    d.banner(p, "CR3=0 · PG=1 · pg_dir[0..3]=pgN+7 — 오늘 그림(08·11장)의 첫 실측", 14800, 18)

    # 36 시연 A-2
    p = d.slide("시연 A-2: 한 주소를 손으로 변환하기", K.S_DEMO,
                "kernel/fork.c:52-53 — start_code = nr*0x4000000 · 캡처는 다음 장(37)")
    auto_pane(d, p, 1100, 4300, 15200, 10100,
              "GDB — 태스크 2(셸)의 논리 주소 0",
              "(gdb) p task[2]->pid\n"
              "$1 = 2                # 셸이 아니면 탐색(§5)\n"
              "(gdb) p/x task[2]->start_code\n"
              "$2 = 0x8000000        # fork.c:52-53\n"
              "(gdb) p task[2]->executable->i_num\n"
              "$3 = …                # 실행 파일 inode\n"
              "\n"
              "# 논리 0 → 선형 0x8000000 → dir = 32\n"
              "(gdb) x/wx 0x80\n"
              "0x80: 0x00302007  → T = 0x302000\n"
              "(gdb) x/wx 0x302000\n"
              "0x302000: 0x00abc005  → F = 0xabc000\n"
              "\n"
              "(gdb) x/16xb 0xabc000    # 물리 경로\n"
              "(gdb) x/16xb 0x8000000   # 선형 경로 — 같은가?", 12)
    steps = ["논리 0x0000 (DS=0x17)", "+ LDT 베이스 0x8000000",
             "선형 0x8000000 · dir 32", "x/wx 0x80 → PDE → 테이블 T",
             "x/wx T → PTE → 물리 F = 값 & 0xfffff000",
             "x/16xb F  vs  x/16xb 0x8000000"]
    for i, s in enumerate(steps):
        nbox(d, p, 16900, 4400 + i * 1700, 15700, 1400, s, None,
             K.TEAL if i in (2, 5) else K.PAPER, s1=14)
    d.banner(p, "여섯 걸음 — 논리→선형(한 덧셈) → PDE→PTE(표 두 번) → 물리 바이트 대조")

    # 37 캡처 A-2
    p = d.slide("캡처 A-2: 두 경로로 읽은 같은 16바이트", K.S_DEMO,
                "각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · 관찰값은 부팅마다 다를 수 있음(§8)")
    d.placeholder_output(p, 1100, 4300, 15200, 4800,
                         "(gdb) p task[2]->pid\n"
                         "$1 = 2\n"
                         "(gdb) p/x task[2]->start_code\n"
                         "$2 = 0x8000000",
                         "03-task2-start-code.png")
    d.placeholder_output(p, 16900, 4300, 15700, 4800,
                         "(gdb) x/wx 0x80\n"
                         "0x80: 0x00302007     # PDE\n"
                         "(gdb) x/wx 0x302000\n"
                         "0x302000: 0x00abc005 # PTE → F=0xabc000",
                         "04-task2-pde-pte.png")
    d.placeholder_output(p, 1100, 9300, 15200, 4800,
                         "(gdb) x/16xb 0xabc000\n"
                         "0xabc000: 0x55 0x8b 0xec 0x83 …\n"
                         "# a.out 텍스트 첫 바이트 (물리 경로)",
                         "05-physical-16bytes.png")
    d.placeholder_output(p, 16900, 9300, 15700, 4800,
                         "(gdb) x/16xb 0x8000000\n"
                         "0x8000000: 0x55 0x8b 0xec 0x83 …\n"
                         "# 05와 같은 바이트열 (선형 경로)",
                         "06-linear-16bytes.png")
    para(d, p, 1100, 14300, 31500, 2200,
         "물리 주소로 읽을 수 있는 이유 = 커널이 0~16MB를 identity 매핑(head.s:198-212).\n"
         "\"같은 내용\"은 추론이 아니라 캡처다 — 관찰/추론 구분은 41장.", 14)

    # 38 시연 B
    p = d.slide("시연 B: 두 태스크의 같은 논리 주소 비교", K.S_DEMO,
                "mm/memory.c:142-148(nr=0xA0 주석) · 150-189(177 &~2) — 캡처는 다음 장(39)")
    auto_pane(d, p, 1100, 4300, 15200, 10100,
              "GDB — 태스크 1(init)의 논리 주소 0",
              "(gdb) p/x task[1]->start_code\n"
              "$4 = 0x4000000\n"
              "(gdb) x/wx 0x40        # dir 16\n"
              "0x40: 0x00202007 → T1 = 0x202000\n"
              "(gdb) x/wx 0x202000\n"
              "0x202000: 0x00000005\n"
              "# 물리 0x00000000 · RW=0 (memory.c:177 &~2)\n"
              "\n"
              "# 태스크 2(셸) 값은 36장에서 이미 읽었다\n"
              "#  → 같은 '논리 0'의 PTE가 다르다!", 13)
    d.table(p, 16900, 4400, [4400, 5600, 5700], [
        ["논리 주소 0", "태스크 1 (init)", "태스크 2 (셸)"],
        ["선형 주소", "0x4000000", "0x8000000"],
        ["디렉터리 인덱스", "16 (x/wx 0x40)", "32 (x/wx 0x80)"],
        ["PTE → 물리", "0x00000000 (하위 5)", "≥ 0x400000 영역 (예 0xabc000)"],
        ["mem_map", "장부 밖 (<1MB)", "1 또는 ≥2 (07 캡처)"],
    ], row_h=1300, size=13)
    para(d, p, 16900, 11400, 15700, 3000,
         "태스크 1은 copy_page_tables의 nr=0xA0 특례(memory.c:142-148 주석)로 "
         "커널 저지대(1MB 아래)를 공유 — '버그'가 아니라 의도된 설계다(§8).\n"
         "\"숫자 0이 두 번 나오지만 PTE가 다르다\" — 오늘 질문의 실측 버전.", 14)

    # 39 캡처 B
    p = d.slide("캡처 B: 태스크 1 vs 태스크 2 PTE", K.S_DEMO,
                "각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · 관찰값은 부팅 시점마다 다를 수 있음(§8)")
    d.placeholder_output(p, 1100, 4300, 15200, 4800,
                         "(gdb) p/x task[1]->start_code\n"
                         "$4 = 0x4000000\n"
                         "(gdb) x/wx 0x40 ; x/wx 0x202000\n"
                         "0x202000: 0x00000005  # 물리 0 · P+US",
                         "08-task1-pde-pte.png")
    d.placeholder_output(p, 16900, 4300, 15700, 4800,
                         "(gdb) x/8xb 0\n"
                         "0x0 <pg_dir>: 0xb8 0x10 0x00 0x00 0x00 …\n"
                         "# startup_32: movl $0x10,%eax (head.s:18)",
                         "09-kernel-first-bytes.png")
    d.placeholder_output(p, 1100, 9300, 15200, 4800,
                         "(gdb) x/8xb 0x4000000\n"
                         "0x4000000: 0xb8 0x10 0x00 0x00 0x00 …\n"
                         "# 09와 같은 바이트열 — 커널 저지대 공유",
                         "10-task1-linear-first-bytes.png")
    d.placeholder_output(p, 16900, 9300, 15700, 4800,
                         "(gdb) p mem_map[(0xabc000-0x100000)>>12]\n"
                         "$5 = 1\n"
                         "# 단독(1) · 공유 중이면 ≥2",
                         "07-mem-map-lookup.png")
    para(d, p, 1100, 14300, 31500, 2200,
         "태스크 1의 물리 0 페이지는 LOW_MEM 아래 — mem_map에 없다. free_page가 무시하는 이유(91행).\n"
         "셸 페이지의 mem_map 값(07)은 실행 파일 공유 여부에 따라 1 또는 ≥2.", 14)

    # 40 시연 C
    p = d.slide("시연 C(선택): calc_mem 호출로 장부 요약 보기", K.S_DEMO,
                "mm/memory.c:413-430 — 실패(함수 호출 중 트랩)하면 Ctrl-C 후 return, 사전 캡처(11)로 대체(§5)")
    auto_pane(d, p, 1100, 4300, 15200, 10100,
              "GDB — calc_mem",
              "(gdb) call calc_mem()\n"
              "3019 pages free (of 3840)\n"
              "Pg-dir[2] uses 1024 pages\n"
              "Pg-dir[3] uses 1024 pages\n"
              "Pg-dir[16] uses 6 pages\n"
              "Pg-dir[32] uses 24 pages\n"
              "…\n"
              "# 인덱스는 16의 배수(그리고 2·3)만 나온다\n"
              "# 트랩이 나면 Ctrl-C → (gdb) return → 사전 캡처로", 13)
    d.placeholder_output(p, 16900, 4300, 15700, 6800,
                         "3019 pages free (of 3840)\n"
                         "Pg-dir[2] uses 1024 pages\n"
                         "Pg-dir[3] uses 1024 pages\n"
                         "Pg-dir[16] uses 6 pages\n"
                         "Pg-dir[32] uses 24 pages\n"
                         "… (인덱스는 16의 배수만)",
                         "11-calc-mem-output.png")
    para(d, p, 16900, 11400, 15700, 3000,
         "기대 — 태스크마다 디렉터리 인덱스 16·32·48…에만 항목 = 64MB 간격(10장)의 실측.\n"
         "Pg-dir[2]·[3] 1024페이지 = 커널 identity 매핑(4~12·12~16MB 구간). "
         "Pg-dir[0]·[1]은 루프가 2부터 시작해 출력되지 않는다(memory.c:421).", 14)

    # 41 관찰 vs 추론
    p = d.slide("관찰 vs 추론 — 오늘 시연에서 무엇을 직접 보았나", K.S_DEMO,
                "00-common §7 구분 규칙 — 관찰(캡처)과 추론(소스 읽기)을 섞지 않는다")
    qbox(d, p, 1100, 4300, 15200, 8600, "관찰 — 캡처로 직접 본 것",
         "CR3 = 0 · CR0의 PG 켜짐 (01)\n"
         "pg_dir[0..3] = 0x00001007 … 0x00004007 (02)\n"
         "태스크 2 start_code = 0x8000000 · PDE/PTE 값 (03·04)\n"
         "물리 F와 선형 0x8000000의 같은 16바이트 (05·06)\n"
         "태스크 1 논리 0의 PTE = 물리 0 (08-10)\n"
         "mem_map 조회 값 (07)", K.TEAL, 15)
    qbox(d, p, 16900, 4300, 15700, 8600, "추론 — 소스 읽기로 대응시킨 것",
         "그 값들은 head.s:198-219(setup_paging)의 결과다\n"
         "0x40·0x80의 항목은 fork.c:39-61(copy_mem)이 만들었다\n"
         "하위 5와 mem_map=2는 memory.c:150-189(&~2 · ++)의 결과다\n"
         "물리 주소로 읽힌 것은 identity 매핑(198-212) 덕이다", K.ORANGE, 15)
    para(d, p, 1100, 13300, 31500, 1400,
         "유의 — PTE 값·mem_map 값은 부팅마다 달라질 수 있다. 슬라이드 기대값은 '형태'이고, "
         "구체 숫자는 캡처에서 읽는다(00-common §7).", 15)

    # ── 정답 42–43 ────────────────────────────────────────────
    # 42 질문의 답 (1)
    p = d.slide("질문의 답 (1): 선택자는 같아도 LDT가 다르다", K.S_ANS,
                "kernel/fork.c:39-61 · include/linux/sched.h:104-106, 153-158 — 답의 절반, 세그먼트 유닛")
    nbox(d, p, 8600, 4300, 16400, 1400,
         "논리 주소 0x1234 — CS=0x0f · DS=0x17 (두 프로세스 모두 같은 선택자)",
         None, K.PAPER, s1=15)
    arrow(d, p, 7300, 5900, "↙", 26)
    arrow(d, p, 25300, 5900, "↘", 26)
    nbox(d, p, 1100, 6900, 14600, 2900, "태스크 1 — init · LDT[2] 베이스 0x4000000",
         "선형 주소 = 0x4000000 + 0x1234 = 0x4001234", K.TEAL, s1=16)
    nbox(d, p, 26900, 6900, 14600, 2900, "태스크 2 — 셸 · LDT[2] 베이스 0x8000000",
         "선형 주소 = 0x8000000 + 0x1234 = 0x8001234", K.TEAL, s1=16)
    pane(d, p, 1100, 10200, 31500, 1700, "한 줄 요약",
         "같은 0x1234  →  0x4001234 (디렉터리 인덱스 16)  ·  0x8001234 (디렉터리 인덱스 32)", 16)
    para(d, p, 1100, 12200, 31500, 2300,
         "lldt로 걸려 있는 LDT가 태스크마다 다르다 — switch_to의 태스크 전환마다 TSS.ldt가 가리키는 "
         "LDT로 교체되고(sched.h:153-158), 그 베이스는 fork.c:52(nr×64MB)가 정했다.\n"
         "따라서 선형 주소부터 다르다 — '같은 숫자'가 갈라지는 최초의 지점이다.", 15)
    d.banner(p, "답의 절반 — 주소가 갈라지는 곳은 첫 번째 화살표(세그먼트 유닛)이다")

    # 43 질문의 답 (2)
    p = d.slide("질문의 답 (2): 선형이 달라서 PDE/PTE도 다르다", K.S_ANS,
                "mm/memory.c:150-189 — 답의 나머지 절반, 페이징 유닛 · '다른 메모리'가 되는 순간은 08회차")
    nbox(d, p, 1100, 4300, 14600, 1300, "0x4001234 → pg_dir[16] → 테이블 A",
         None, K.TEAL, s1=15)
    arrow(d, p, 7300, 5700, "↓", 22)
    nbox(d, p, 1100, 6200, 14600, 1300, "→ 물리 페이지 X (태스크 1의 것)",
         None, K.PAPER, s1=15)
    nbox(d, p, 16900, 4300, 14600, 1300, "0x8001234 → pg_dir[32] → 테이블 B",
         None, K.TEAL, s1=15)
    arrow(d, p, 23100, 5700, "↓", 22)
    nbox(d, p, 16900, 6200, 14600, 1300, "→ 물리 페이지 Y (태스크 2의 것)",
         None, K.PAPER, s1=15)
    nbox(d, p, 1100, 8200, 31500, 1600,
         "단, fork 직후에는 같은 물리 페이지를 RW=0으로 공유한다(mem_map = 2)",
         "copy_page_tables:177(&~2) · 183(mem_map++) — 25장 그림", K.PAPER,
         s1=16, s2=12)
    para(d, p, 1100, 10300, 31500, 4200,
         "디렉터리 인덱스 16과 32는 서로 다른 페이지 테이블 → 원칙적으로 서로 다른 물리 페이지.\n\n"
         "그러나 fork에서 복사된 페이지는 당장은 '같은 페이지, 다른 PTE'다 — 진짜 '다른 메모리'가 되는 "
         "순간은 첫 쓰기 폴트(08회차 un_wp_page)를 기다려야 한다.\n\n"
         "현대 리눅스는 LDT 대신 프로세스마다 CR3(디렉터리)를 바꾼다 — 0.11은 CR3=0 하나를 공유하고 "
         "LDT 베이스로 구분한다(§8, 이 한 줄만).", 15)
    d.banner(p, "나머지 절반 — 갈라진 선형 주소가 다른 표를 지나 다른 물리 페이지에 닿는다")

    # ── 정리 44–47 ────────────────────────────────────────────
    # 44 데이터 요약
    p = d.slide("오늘 코드가 쓰는 데이터 한 장 요약", K.S_WRAP,
                "include/linux/head.h:4-9 · include/linux/sched.h:88, 104-106 · mm/memory.c:39-57 · boot/head.s:15-16, 108-124")
    d.table(p, 1100, 4400, [7300, 8100, 16100], [
        ["데이터", "정의(크기)", "쓰는 함수"],
        ["ldt[1..2] — 세그먼트 디스크립터", "sched.h:104-106 (task_struct 안)", "copy_mem — set_base(54-55) · get_base(46-47)"],
        ["start_code", "sched.h:88", "copy_mem:53 기록 · 08회차 do_no_page가 읽음"],
        ["pg_dir[1024] — 물리 0", "head.h:8 · head.s:15-16", "setup_paging · copy/free_page_tables · put_page · calc_mem"],
        ["페이지 테이블 — pg0~pg3 + 새로 만든 것", "head.s:108-124 (0x1000~0x4000)", "setup_paging · put_page:211 · copy_page_tables:169"],
        ["mem_map[3840]", "memory.c:57 (15MB/4KB)", "mem_init · get_free_page · free_page · copy_page_tables:183"],
        ["HIGH_MEMORY", "memory.c:52", "mem_init:403 설정 · free_page:92 상한"],
    ], row_h=1250, size=13)
    d.banner(p, "세 표가 오늘의 답을 만들었다 — LDT(어느 선형 칸) · pg_dir+테이블(어느 물리 페이지) · mem_map(몇 명 것인가)")

    # 45 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(46) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "태스크 번호 3의 사용자 논리 주소 0x1000은 선형 주소 얼마인가? 디렉터리 인덱스는?",
         K.TEAL, 15)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2",
         "get_free_page()의 반환값은 선형 주소인가 물리 주소인가? 커널이 그 값을 바로 포인터처럼 쓸 수 있는 이유는?",
         K.TEAL, 15)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3",
         "copy_page_tables가 자식 PTE뿐 아니라 부모 PTE에서도 RW 비트를 끄는 이유는? 그 줄은?",
         K.TEAL, 15)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4",
         "mem_map[]에 1MB 아래 페이지가 없는데, free_page(0x5000)을 부르면 어떻게 되는가?",
         K.TEAL, 15)

    # 46 이해 확인 정답
    p = d.slide("이해 확인 정답", K.S_ANS,
                "근거 줄 번호를 정답 옆에 표기 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "A1",
         "베이스 3×0x4000000 = 0xC000000 → 선형 0xC001000. 디렉터리 인덱스 = 0xC001000>>22 = 48 · "
         "테이블 인덱스 1 (fork.c:52 · 슬라이드 07·10)", K.ORANGE, 14)
    qbox(d, p, 1100, 6850, 31500, 2400, "A2",
         "물리 주소다(memory.c:70-71 sall $12; addl LOW_MEM) — 커널 세그먼트 베이스 0 + 0~16MB "
         "identity 매핑이라 선형=물리로 바로 접근 가능", K.ORANGE, 14)
    qbox(d, p, 1100, 9400, 31500, 2400, "A3",
         "둘 중 누가 먼저 쓰든 폴트가 나서 복사(COW)가 일어나게 하려고 — memory.c:177 "
         "this_page &= ~2 · 180 *from_page_table = this_page. 단 LOW_MEM 아래는 제외(179 조건)",
         K.ORANGE, 14)
    qbox(d, p, 1100, 11950, 31500, 2400, "A4",
         "addr < LOW_MEM이면 그냥 반환(memory.c:91) — 커널·BIOS 영역은 장부 밖이고 해제되지 않는다",
         K.ORANGE, 14)

    # 47 정리·다음 회차 예고
    p = d.slide("정리·다음 회차 예고", K.S_WRAP,
                "08회차 — 페이지 폴트와 Copy-on-Write · 파트 C «메모리» 둘째 회차(07 주소 변환 · 08 폴트·CoW)")
    nbox(d, p, 1100, 4400, 9900, 2600, "LDT",
         "태스크별 베이스 nr×0x4000000\n같은 선택자, 다른 선형 주소", K.TEAL, s1=18)
    nbox(d, p, 11300, 4400, 9900, 2600, "pg_dir + 테이블",
         "선형→물리 · CR3=0 하나 공유\nPTE 하위비트 0 / 5 / 7", K.TEAL, s1=18)
    nbox(d, p, 21500, 4400, 11100, 2600, "mem_map",
         "물리 페이지 장부 — 0/1/n/USED\n오늘의 세 표가 답의 재료였다", K.TEAL, s1=18)
    d.text(p, 1100, 7600, 31500, 1000,
           "08회차 — fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?", 22,
           K.ORANGE, True)
    para(d, p, 1100, 8900, 31500, 3400,
         "오늘 본 &~2(RW 끄기)와 mem_map[]++(카운트 올리기)가 페이지 폴트 핸들러에서 어떻게 풀리는지.\n"
         "copy_page_tables는 PTE만 복사했다 — 데이터 페이지 복사의 주인공은 다음 회차다(§8).\n"
         "시연 A-2의 PTE 하위 5가 다음 시간에 7로 바뀌는 장면을 직접 보게 된다.", 16)
    d.flow(p, [("미리 볼 파일 1", "mm/page.s — 폴트 진입 어셈블리"),
               ("미리 볼 파일 2", "mm/memory.c:221-272 — un_wp_page·write_verify"),
               ("복습", "오늘 13장 PTE 비트 그림 · 25장 공유 그림")],
           y=12400, h=2200)
    d.banner(p, "세 표는 계속 쓰인다 — 08(COW)·09(exec)가 오늘의 표를 그대로 가져간다", 14800, 16)


if __name__ == "__main__":
    K.run(globals())
