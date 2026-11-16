#!/usr/bin/env python3
"""08회차 덱 — 페이지 폴트와 Copy-on-Write (output/08-page-fault-cow.pptx)

계획: materials/slide-plans/08-page-fault-cow.md (§2 표 46행 1:1 · §3 앞부분 명세 ·
§4 상태 변화도 명세 · §5 캡처 6종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="08", total=46, slug="08-page-fault-cow",
    part_no="C", part="«메모리»",
    title="08. 페이지 폴트와 Copy-on-Write",
    question="fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?",
    done=7,
    today_line="공유된 읽기 전용 페이지, 첫 쓰기 폴트에 그때 복사 — Copy-on-Write",
    next_lines=[
        "07 → 08   페이지 테이블의 R/W 비트가 0인 공유 페이지를 봤다 → 그 페이지에 쓰면 무슨 일이 일어나는가",
        "08 → 09   fork 뒤 대부분 페이지는 복사되지 않은 채 exec로 이어진다 → exec가 오늘의 do_no_page를 호출한다",
        "09 예고   PID는 그대로인데 프로그램은 어떻게 바뀌는가? — fs/exec.c · include/a.out.h (파트 C를 마치고 파트 D «프로그램의 일생»으로)",
    ],
    road_note=("07회차의 PTE·mem_map 표를 그대로 사용한다 — 오늘은 10단계 전부를 밟는다"
               "(질문부터 정리까지, 빠짐없이)."),
    STRUCT=dict(
        teal=["mm"],
        today=[("mm/page.s", "폴트 진입"),
               ("mm/memory.c", "do_wp_page·do_no_page"),
               ("kernel/fork.c", "verify_area"),
               ("fs/read_write.c", "sys_read")],
        flow="쓰기 접근 → 페이지 폴트(CR2·오류 코드) → page_fault → do_no_page/do_wp_page → 새 페이지",
        up="↑ read() 반환",
        user="sh · 사용자 프로그램",
    ),
)

CHECKS = dict(
    captions={
        5: "src/mm/memory.c:173-184",
        6: "src/kernel/traps.c:196-201",
        7: "src/mm/page.s:25-27",
        12: "src/mm/page.s:14-27",
        13: "src/mm/page.s:28-40",
        14: "src/mm/memory.c:247-259",
        15: "src/mm/memory.c:225-230",
        17: "src/mm/memory.c:261-272",
        18: "src/mm/memory.c:54-55",
        19: "src/mm/memory.c:365-377",
        20: "src/mm/memory.c:274-282",
        21: "src/mm/memory.c:348-361",
        22: "src/mm/memory.c:300-312",
        23: "src/mm/memory.c:380-385",
        24: "src/mm/memory.c:386-396",
        25: "src/mm/page.s:33-40",
    },
    required=[
        "Copy-on-Write", "CR2", "에러 코드", "do_no_page", "do_wp_page",
        "un_wp_page", "verify_area", "write_verify", "try_to_share",
        "share_page", "get_empty_page", "mem_map", "testl $1", "0x41",
        "bread_page", "bmap", "movsl", "do_exit(SIGSEGV)", "요구 적재",
        "Dirty", "LOW_MEM", "start_code", "end_data", "executable",
    ],
    prereq=[
        ("copy_page_tables", "src/mm/memory.c:225-230"),
        ("CR2", "src/mm/page.s:14-27"),
        ("R/W", "src/mm/page.s:28-40"),
    ],
    structure_nodes=["page.s", "memory.c", "system_call.s", "fork.c",
                     "read_write.c"],
    capture_slides=[34, 36, 38, 39, 40],
)


# ── 로컬 도우미 (deckkit 불변) ─────────────────────────────────
def wrap_kr(text, width, size):
    """CJK 포함 텍스트를 width(1/100mm) 안에서 줄바꿈한다.

    ASCII 단어(식별자·파일명 등) 중간에서는 끊지 않는다 — 넘칠 때는
    마지막 공백에서 끊어 단어를 다음 줄로 넘긴다."""
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


def populate(d):
    # ── 배경 05–11 ────────────────────────────────────────────
    # 05 복습: 07회차 끝의 상태
    p = d.slide("복습: 07회차 끝의 상태", K.S_BG,
                "07회차 — copy_page_tables(mm/memory.c:150-189)가 남긴 상태에서 오늘 시작")
    d.code_panel(p, "src/mm/memory.c", 173, 184, 1100, 4400, 19700, 8400,
                 size=10, caption_extra="copy_page_tables 루프 — 177 · 180 · 183")
    nbox(d, p, 22100, 4500, 4800, 1500, "부모 PTE = A | 5", None, K.TEAL)
    nbox(d, p, 27400, 4500, 4800, 1500, "자식 PTE = A | 5", None, K.TEAL)
    arrow(d, p, 23800, 6100, "↓")
    arrow(d, p, 29100, 6100, "↓")
    nbox(d, p, 23400, 7100, 7900, 1700, "물리 페이지 A", "부모·자식이 같은 페이지")
    badge(d, p, 24800, 9200, 5000, "mem_map[A] = 2", K.TEAL)
    para(d, p, 22100, 10200, 10100, 3400,
         "fork는 데이터 페이지를 복사하지 않는다 — PTE만 복사하고 양쪽 모두 "
         "읽기 전용(하위 5)으로 내놓는다. 177: this_page &= ~2 · 180: 부모 PTE "
         "갱신 · 183: mem_map[this_page]++", 15)
    d.banner(p, "여기서 자식이 x = 1을 실행하면? — 오늘 120분의 출발점", 14800, 20)

    # 06 폴트는 4회차에서 본 예외의 하나다
    p = d.slide("폴트는 4회차에서 본 예외의 하나다", K.S_BG,
                "IDT 벡터 14 · kernel/traps.c:57 선언 · kernel/traps.c:199 등록 — 04회차 예외 프레임의 확장")
    nbox(d, p, 1100, 4400, 7000, 1000, "SS : ESP", None, None, K.MUTED)
    nbox(d, p, 1100, 5500, 7000, 1000, "EFLAGS", None, None, K.MUTED)
    nbox(d, p, 1100, 6600, 7000, 1000, "CS : EIP — 폴트를 낸 명령", None,
         None, K.MUTED)
    nbox(d, p, 1100, 7900, 7000, 1100, "에러 코드 4바이트", None, K.ORANGE)
    nbox(d, p, 1100, 9300, 7000, 1000, "page.s가 push한 레지스터·CR2 …",
         None, K.PAPER)
    para(d, p, 8600, 4500, 8100, 1800,
         "4회차 인터럽트 프레임과 같은 순서 — 위 3개는 모든 인터럽트가 CPU에 push", 14)
    para(d, p, 8600, 8000, 8100, 1800,
         "벡터 14 전용 추가분: CPU가 에러 코드를 스택에 남긴다(ORANGE)", 14,
         K.ORANGE, True)
    para(d, p, 8600, 9400, 8100, 1800,
         "iret 전에 반드시 걷어낸다 — page.s:33 addl $8,%esp (12장 트릭)", 14)
    d.code_panel(p, "src/kernel/traps.c", 196, 201, 17400, 4400, 15200, 5700,
                 size=12, caption_extra="trap_gate(14) = #PF")
    para(d, p, 17400, 10300, 15200, 4100,
         "페이지 폴트(#PF)는 벡터 14 — 트랩 게이트로 등록된다.\n"
         "traps.c:57의 void page_fault(void) 선언의 실체는 mm/page.s의 "
         "_page_fault 어셈블리다(12장).\n"
         "4회차 복습: 트랩은 '다음 명령', 폴트는 '같은 명령' 재실행(25장).", 14)

    # 07 CPU가 남기는 정보 (1): CR2
    p = d.slide("CPU가 남기는 정보 (1): CR2 — 폴트를 낸 선형 주소", K.S_BG,
                "#PF가 나면 CPU는 CR2에 주소를, 스택에 에러 코드를 남긴다 — 그 둘이 핸들러의 전부")
    nbox(d, p, 1100, 4400, 15200, 1400, "사용자 명령 — 선형 주소 접근",
         None, K.PAPER)
    arrow(d, p, 7900, 5850, "↓")
    nbox(d, p, 1100, 6300, 15200, 1400,
         "#PF 벡터 14 — CPU가 CR2에 폴트 주소 저장", None, K.ORANGE)
    arrow(d, p, 7900, 7750, "↓")
    nbox(d, p, 1100, 8200, 15200, 1400,
         "movl %cr2,%edx · pushl %edx  (page.s:25-26)", None, K.PAPER)
    arrow(d, p, 7900, 9650, "↓")
    nbox(d, p, 1100, 10100, 15200, 1400,
         "do_no_page / do_wp_page 의 인자 address", None, K.TEAL)
    d.code_panel(p, "src/mm/page.s", 25, 27, 17400, 4400, 15200, 3800,
                 size=12, caption_extra="CR2 → 두 번째 인자")
    para(d, p, 17400, 8600, 15200, 5700,
         "핸들러가 판단에 쓰는 정보는 CR2와 에러 코드 단 둘 — 어떤 선형 주소에서 "
         "무슨 접근이 있었는지 압축해 놓는다.\n\n"
         "CR2의 값은 페이지 변환을 거친 '선형 주소'다 — 논리→선형→물리 관용구는 "
         "07회차 복습(14장 PTE 주소 계산).", 15)

    # 08 CPU가 남기는 정보 (2): 에러 코드 P/W/U
    p = d.slide("CPU가 남기는 정보 (2): 에러 코드 P/W/U", K.S_BG,
                "3비트로 원인을 압축 — 그러나 0.11 핸들러가 보는 비트는 하나다")
    d.cards(p, [
        ("bit0 P — present",
         "0 = 페이지 부재\n매핑 자체가 없다\n→ do_no_page\n\n"
         "1 = 보호 위반\n매핑은 있는데 권한\n→ do_wp_page"),
        ("bit1 W — 쓰기",
         "0 = 읽기 접근\n1 = 쓰기 접근\n\nCOW 판정의 핵심\n(0.11은 직접 안 씀)"),
        ("bit2 U — 모드",
         "0 = 링 0 (커널)\n1 = 링 3 (사용자)\n\n커널이 사용자 버퍼에\n접근 중인지 구분"),
    ], y=4500, h=6200)
    d.text(p, 1100, 11100, 31500, 900,
           "예: 3 = 011b → U=1, W=1, P=1 — 사용자의 쓰기 보호 위반, 바로 COW",
           19, K.ORANGE, True)
    para(d, p, 1100, 12100, 31500, 2300,
         "0.11 page.s가 실제로 보는 비트는 bit0 P 뿐이다(testl $1,%eax) — W/U는 "
         "핸들러가 쓰지 않는다. 8가지 조합 전체는 비교 ①(28장)에서.", 15)

    # 09 80386의 함정
    p = d.slide("80386의 함정: ring 0 쓰기는 R/W 비트를 무시한다", K.S_BG,
                "kernel/fork.c:24-37 · fs/read_write.c:64 — 오늘 비교 ③(30장)의 뿌리")
    d.cards(p, [
        ("80386 — CR0.WP 가 없다",
         "링 0(커널)이 쓰면 페이지 R/W 비트를\n하드웨어가 무시한다 — 폴트가 없다\n\n"
         "read()가 사용자 buf에 복사할 때\n공유 페이지여도 그냥 쓴다\n"
         "→ 부모의 페이지를 덮어쓸 위험"),
        ("486 이후 — CR0.WP 비트",
         "커널 쓰기도 R/W 비트 검사 → #PF\n(에러 코드 U=0, W=1, P=1)\n\n"
         "현대 커널은 이 비트로 COW를 강제\n0.11(1991, 386 전제)은 커널이\n"
         "손수 검사해야 했다"),
    ], y=4400, h=6500)
    para(d, p, 1100, 11200, 31500, 3000,
         "예: sys_read(fd, buf, n)(fs/read_write.c:64) — buf가 fork로 공유 중인 "
         "페이지에 있다면? 386에서는 폴트가 나지 않으므로, sys_read는 복사 전에 "
         "verify_area(buf, count)를 먼저 부른다(17장 코드).", 15)
    d.banner(p, "커널 쓰기는 폴트가 없다 → 커널이 먼저 검사한다 — verify_area · write_verify")

    # 10 요구 적재
    p = d.slide("요구 적재(demand loading): 없으면 그때 가져온다", K.S_BG,
                "mm/memory.c:7-21 Linus 주석(1991.12.01 / 12.02) · fs/exec.c:11-18 주석")
    auto_pane(d, p, 1100, 4400, 16000, 5700,
              "mm/memory.c:7-21 — Linus 주석 (원문)",
              "demand-loading started 01.12.91 - seems it is high\n"
              "on the list of things wanted, and it should be easy\n"
              "to implement. - Linus\n"
              "\n"
              "Ok, demand-loading was easy, shared pages a little\n"
              "bit tricker. Shared pages started 02.12.91, seems\n"
              "to work.\n"
              "\n"
              "Tested sharing by executing about 30 /bin/sh: under\n"
              "the old kernel it would have taken more than the 6M\n"
              "I have free, but it worked well as far as I could see.")
    d.outline(p, 1100, 10500, 16000, 1900, K.ORANGE, 110)
    d.text(p, 1350, 10750, 15500, 800,
           "없으면 그때 가져온다 — 첫 접근(부재 폴트)이 적재 시점", 19, K.ORANGE, True)
    d.text(p, 1350, 11600, 15500, 700,
           "exec는 a.out 헤더만 읽는다 — 코드·데이터 페이지는 두고 온다", 15, K.PAPER)
    para(d, p, 18000, 4400, 14600, 10000,
         "exec는 헤더(1 블록)만 읽고 inode를 current->executable 에 남긴다"
         "(fs/exec.c:11-18 주석 — include/linux/sched.h:100).\n\n"
         "코드·데이터 페이지는 매핑조차 없다 — 첫 접근이 곧 부재 폴트(P=0).\n\n"
         "do_no_page 가 그때 bmap·bread_page 로 채운다(23–24장).\n\n"
         "30개 /bin/sh — 공유 페이지(share_page)까지 더해 6MB 안에서 돌아간 "
         "Linus의 테스트.", 16)

    # 11 오늘 읽을 함수 지도
    p = d.slide("오늘 읽을 함수 지도", K.S_BG,
                "호출 그래프 — 상태 변화도가 아님(상태도는 26·27장) · ● 표시는 오늘 첫 등장 함수 8개")
    nbox(d, p, 1100, 4400, 7400, 1400, "mm/page.s — _page_fault",
         "testl $1,%eax 로 갈림", K.PAPER)
    d.text(p, 4200, 5850, 1400, 700, "↓", 22, K.ORANGE, True)
    nbox(d, p, 1100, 6500, 7400, 1400, "do_wp_page ● (P=1)",
         "mm/memory.c:247 — 쓰기 보호", K.PAPER)
    nbox(d, p, 9200, 6500, 7400, 1400, "do_no_page ● (P=0)",
         "mm/memory.c:365 — 부재", K.PAPER)
    d.text(p, 4200, 7950, 1400, 700, "↓", 22, K.TEAL, True)
    nbox(d, p, 1100, 8600, 7400, 1400, "un_wp_page ●",
         "(a) |=2 승격 / (b) 복사 — 221", K.PAPER)
    d.text(p, 12300, 5850, 1400, 700, "↓", 22, K.ORANGE, True)
    nbox(d, p, 9200, 8600, 7400, 1300, "get_empty_page ●", "274 — 0 페이지", K.PAPER)
    nbox(d, p, 9200, 10100, 7400, 1300, "share_page ● → try_to_share ●",
         "344 / 292 — 공유", K.PAPER)
    nbox(d, p, 9200, 11600, 7400, 1300, "bread_page + put_page",
         "fs/buffer.c:296 · 197 — 디스크", K.PAPER)
    nbox(d, p, 17700, 6500, 13800, 1400,
         "sys_read 등 → verify_area ● (kernel/fork.c:24-37)",
         "폴트 없는 커널 쓰기 경로", K.PAPER)
    nbox(d, p, 17700, 8600, 13800, 1400, "write_verify ● (mm/memory.c:261-272)",
         "present+non-writable 이면 선제 분리", K.PAPER)
    d.text(p, 15700, 9050, 1900, 700, "←", 26, K.ORANGE, True)
    d.text(p, 15600, 9750, 2100, 500, "수렴", 13, K.ORANGE, True)
    para(d, p, 1100, 13400, 30400, 1000,
         "두 경로(폴트·커널 직접) 모두 un_wp_page 하나로 만난다 — 오늘 코드 읽기의 "
         "중심이다. bread_page 는 함수 지도에 먼저 등장하고 본문은 24장.", 15)

    # ── 코드 12–25 (16은 상태도) ──────────────────────────────
    # 12 page.s — 에러 코드를 eax와 바꾸는 트릭
    p = d.slide("코드: page.s — 에러 코드를 eax와 바꾸는 트릭", K.S_CODE,
                "mm/page.s:14-27 — 인터럽트 프레임 위에 에러 코드가 하나 늘었다(6장)")
    d.code_panel(p, "src/mm/page.s", 14, 27, 1100, 4400, 19700, 9450, size=10)
    para(d, p, 22000, 4400, 10000, 5800,
         "xchgl %eax,(%esp) — 스택 top의 에러 코드와 eax를 맞바꾼다\n"
         "push 한 번으로 eax 보관 + 인자 준비를 동시에\n"
         "ds·es·fs = 0x10 — 커널 데이터 세그먼트\n"
         "movl %cr2,%edx → pushl %edx → pushl %eax → C 인자 (error_code, address)",
         15)
    d.text(p, 22100, 10000, 10000, 500,
           "xchgl 직후 · call 직전의 스택 (위 = 낮은 주소)", 11, K.TEAL, True)
    stack = [("error_code — 인자 1", K.ORANGE),
             ("address = CR2 — 인자 2", K.ORANGE),
             ("fs · es · ds · edx · ecx", K.PAPER),
             ("eax — 원래 값 보관", K.PAPER),
             ("에러 코드 · EIP ⋯", K.PAPER)]
    for i, (label, col) in enumerate(stack):
        nbox(d, p, 22500, 10650 + i * 760, 9000, 700, label, None,
             col, K.INK, s1=12)

    # 13 page.s — 어느 핸들러로 가는가
    p = d.slide("코드: page.s — 어느 핸들러로 가는가", K.S_CODE,
                "mm/page.s:28-40 — 보는 비트는 bit0 P 하나 · W/U는 28장 비교 ①에서")
    d.code_panel(p, "src/mm/page.s", 28, 40, 1100, 4400, 19700, 9650,
                 size=11, caption_extra="testl $1 — P 비트만")
    para(d, p, 22000, 4400, 10000, 6600,
         "testl $1,%eax — 보는 비트는 bit0 P 뿐\n"
         "P=0(부재) → _do_no_page · P=1(보호) → _do_wp_page\n"
         "addl $8,%esp — 인자 2개(error_code·address) 제거\n"
         "push 역순 pop → iret — 레지스터 완전 복원(25장)\n"
         "W/U 비트는 보지 않는다 — 8가지 조합은 28장",
         15)
    nbox(d, p, 22300, 11200, 9500, 900, "error_code", None, K.PAPER, s1=13)
    d.text(p, 22400, 12150, 9300, 500, "↓  testl $1,%eax", 13, K.TEAL, True)
    nbox(d, p, 22000, 12800, 4800, 1100, "P=0 → do_no_page", None,
         K.TEAL, s1=13)
    nbox(d, p, 27000, 12800, 4800, 1100, "P=1 → do_wp_page", None,
         K.ORANGE, s1=13)

    # 14 do_wp_page — PTE 주소 계산
    p = d.slide("코드: do_wp_page — PTE 주소 계산", K.S_CODE,
                "mm/memory.c:247-259 · CODE_SPACE 매크로는 memory.c:49-50 — 07회차 관용구 재등장")
    d.code(p, "src/mm/memory.c", 247, 259, wrap_kr(
        "#if 0 — CODE_SPACE 검사는 꺼져 있다\n"
        "(estdio 가 코드 영역에 써서 · 주석 250-251)\n"
        "CODE_SPACE(addr) 는 memory.c:49-50\n"
        "\n"
        "PDE = *((address>>20) & 0xffc)\n"
        "PTE 주소 = (PDE & 0xfffff000)\n"
        "         + ((address>>10) & 0xffc)\n"
        "→ un_wp_page(&PTE) — 실제 일은 다음 장(15)", 9500, 15),
        expl_size=15)
    d.banner(p, "별도 권한 검사는 없다 — 'present 인데 폴트'면 무조건 쓰기 보호로 본다")

    # 15 un_wp_page — 두 갈래
    p = d.slide("코드: un_wp_page — 두 갈래", K.S_CODE,
                "mm/memory.c:221-238 — 판정 226 · (a) 227-229 · (b) 231-237 · 그림은 다음 장(16)")
    d.code_panel(p, "src/mm/memory.c", 225, 230, 1100, 4400, 19700, 4600,
                 size=9, caption_extra="(a) 갈래 — 복사 없음, 제자리 승격 |= 2")
    d.code_panel(p, "src/mm/memory.c", 231, 237, 1100, 9300, 19700, 5100,
                 size=9, caption_extra="(b) 갈래 — 새 페이지 할당·복사")
    para(d, p, 22000, 4400, 10000, 10000,
         "판정(226): old_page >= LOW_MEM && mem_map[MAP_NR(old_page)]==1\n\n"
         "카운트 하나로 복사 여부가 결정된다.\n\n"
         "(a) count=1 — 혼자 쓴다: *table_entry |= 2, invalidate. 상대가 이미 "
         "복사해 갔거나 fork 전 상태.\n\n"
         "(b) count≥2 — 공유 중: get_free_page, mem_map[old]--, PTE=new|7, "
         "invalidate, copy_page(old,new).", 14)

    # 16 핵심 그림: 공유 → 쓰기 폴트 → 분리
    p = d.slide("그림: 공유 페이지가 쓰기 폴트로 분리된다 — un_wp_page 복사 전/후",
                K.S_STATE,
                "대응 코드 mm/memory.c:226-237 · 07회차 PTE·mem_map 도식 언어 재사용 — A·B는 도식 값(실측은 33–36장)")
    cuts = [
        ("① 복사 전 — 공유 읽기 전용", K.TEAL, False, False),
        ("② 자식 쓰기 폴트 — (b) 복사", K.ORANGE, True, False),
        ("③ 부모 쓰기 폴트 — 제자리 승격", K.ORANGE, False, True),
    ]
    for ci, (ctitle, ccol, pf_child, pf_parent) in enumerate(cuts):
        x = 1100 + ci * 10800
        d.text(p, x, 4250, 9900, 650, ctitle, 16, ccol, True)
        if pf_child:
            badge(d, p, x + 5100, 4950, 4700, "x=1 쓰기 → #PF W=1·P=1",
                  K.ORANGE, 620, 12)
        if pf_parent:
            badge(d, p, x + 100, 4950, 4700, "나중 쓰기 → #PF", K.ORANGE, 620, 12)
        parent_pte = "A | 7" if pf_parent else "A | 5"
        child_pte = "B | 7" if ci >= 1 else "A | 5"
        nbox(d, p, x + 100, 5700, 4400, 1300, f"부모 PTE {parent_pte}", None,
             K.ORANGE if pf_parent else K.TEAL, s1=13)
        nbox(d, p, x + 5300, 5700, 4400, 1300, f"자식 PTE {child_pte}", None,
             K.ORANGE if pf_child else (K.PAPER if ci == 2 else K.TEAL), s1=13)
        if ci == 0:
            nbox(d, p, x + 900, 7700, 8200, 1500, "물리 페이지 A",
                 "부모·자식 함께 읽기 전용으로 사용", K.PAPER)
            arrow(d, p, x + 2500, 7050, "↓", 20)
            arrow(d, p, x + 7300, 7050, "↓", 20)
            badge(d, p, x + 2400, 9400, 5200, "mem_map[A] = 2", K.TEAL)
            para(d, p, x, 10400, 9900, 900,
                 "R/W=0 — 누구도 못 쓴다", 15, K.TEAL, True)
        else:
            nbox(d, p, x + 100, 7700, 4400, 1500, "물리 페이지 A", "x = 0",
                 K.PAPER, s1=14, s2=13)
            nbox(d, p, x + 5300, 7700, 4400, 1500, "물리 페이지 B", "x = 1",
                 K.ORANGE if pf_child else K.PAPER, s1=14, s2=13)
            arrow(d, p, x + 2500, 7050, "↓", 20, K.TEAL)
            arrow(d, p, x + 7300, 7050, "↓", 20,
                  K.ORANGE if pf_child else K.TEAL)
            badge(d, p, x + 100, 9400, 4400, "mem_map[A] = 1",
                  K.MUTED if pf_parent else K.ORANGE, 620, 12)
            badge(d, p, x + 5300, 9400, 4400, "mem_map[B] = 1",
                  K.MUTED if pf_parent else K.ORANGE, 620, 12)
            if pf_child:
                para(d, p, x, 10400, 9900, 950,
                     "copy_page(A,B) — rep movsl 4KB, 딱 한 번", 14, K.ORANGE, True)
            else:
                para(d, p, x, 10400, 9900, 950,
                     "· · · 복사 없음 · · ·  |= 2 — A(5)→A(7)", 14,
                     K.ORANGE, True)
        if ci < 2:
            d.text(p, x + 9950, 6500, 800, 900, ">", 28, K.TEAL, True)
    para(d, p, 1100, 11700, 31500, 2700,
         "먼저 쓰는 쪽이 새 페이지를 받는다 — 부모가 먼저일 수도 있다(스케줄 순서).\n"
         "② 자식만 (b) 갈래로 복사, ③ 부모는 이미 count=1이라 (a) 갈래 — 비트만 켜고 끝. "
         "이 세 컷이 41장 답 그림으로 재사용된다.", 15)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # 17 write_verify / verify_area
    p = d.slide("코드: write_verify / verify_area — 폴트 없는 COW", K.S_CODE,
                "kernel/fork.c:24-37 · mm/memory.c:261-272 · 호출처 fs/read_write.c:64 · kernel/sys.c:108·159·224")
    d.code_panel(p, "src/mm/memory.c", 261, 272, 1100, 4400, 15200, 7500,
                 size=9, caption_extra="write_verify — present+non-writable → un_wp_page")
    d.code_panel(p, "src/kernel/fork.c", 24, 37, 16900, 4400, 15700, 9500,
                 size=10, caption_extra="verify_area — 논리→선형 후 4KB마다")
    nbox(d, p, 1100, 12200, 4300, 1100, "논리 주소 addr", "세그먼트 내",
         None, K.MUTED, s1=13, s2=11)
    d.text(p, 5450, 12500, 1500, 700, "→", 20, K.ORANGE, True)
    nbox(d, p, 6950, 12200, 4400, 1100, "선형 주소 start",
         "+ get_base(ldt[2])", None, K.PAPER, s1=13, s2=10)
    d.text(p, 11400, 12500, 1500, 700, "→", 20, K.ORANGE, True)
    nbox(d, p, 12900, 12200, 3400, 1100, "4KB 간격", "write_verify 반복",
         None, K.PAPER, s1=13, s2=11)
    d.banner(p, "sys_read(read_write.c:64) · sys_time·sys_times·sys_uname(sys.c) — 시스템 콜 진입부의 방어")

    # 18 copy_page와 invalidate
    p = d.slide("코드: copy_page와 invalidate", K.S_CODE,
                "mm/memory.c:54-55 · 39-40 · 순서 235-237 — PTE 교체 → TLB 무효화 → 복사")
    d.code_panel(p, "src/mm/memory.c", 54, 55, 1100, 4400, 9900, 3800,
                 size=12, caption_extra="copy_page — 4KB 복사")
    d.code_panel(p, "src/mm/memory.c", 39, 40, 11600, 4400, 9900, 3800,
                 size=12, caption_extra="invalidate — TLB 전체 무효화")
    d.code_panel(p, "src/mm/memory.c", 235, 237, 22100, 4400, 9500, 3800,
                 size=12, caption_extra="un_wp_page 의 호출 순서")
    d.flow(p, [("PTE 교체", "*table_entry = new | 7"),
               ("invalidate", "movl %eax,%cr3 — TLB 무효화"),
               ("copy_page(old,new)", "rep movsl 1024 — 4KB")],
           y=8700, h=2800)
    para(d, p, 1100, 12000, 31500, 2400,
         "PTE를 먼저 갈아끼우고 TLB를 무효화한 뒤 복사한다(235-237) — 복사가 진행 중이어도 "
         "다음 접근부터는 새 페이지가 보인다. 순서가 어긋나면 오래된 TLB 항목으로 "
         "옛 페이지에 접근할 위험이 있다.", 16)
    d.banner(p, "copy_page 1회 = rep movsl 1024회 = 정확히 4KB — 페이지 하나")

    # 19 do_no_page (1/3)
    p = d.slide("코드: do_no_page (1/3) — 어디서 온 폴트인가", K.S_CODE,
                "mm/memory.c:365-377 · include/linux/sched.h:88, 100 — start_code·end_data·executable")
    d.code_panel(p, "src/mm/memory.c", 365, 377, 1100, 4400, 19700, 8900,
                 size=10, caption_extra="태스크 내 오프셋으로 갈림")
    para(d, p, 22000, 4400, 10000, 5800,
         "address &= 0xfffff000 — 페이지 시작으로 정렬\n"
         "tmp = address - current->start_code (sched.h:88)\n"
         "!executable || tmp >= end_data → 코드·데이터 밖 = 스택·bss·힙\n"
         "→ get_empty_page(address) 후 return (20장)",
         15)
    d.shape(p, 22500, 10600, 5400, 900, K.TEAL)
    d.text(p, 22700, 10850, 5000, 500, "start_code … end_data", 13, K.INK, True)
    d.outline(p, 27900, 10600, 1900, 900, K.MUTED, 60)
    d.text(p, 28050, 10850, 1700, 500, "빈 공간", 12, K.MUTED)
    d.outline(p, 29800, 10600, 2200, 900, K.MUTED, 60)
    d.text(p, 29950, 10850, 2000, 500, "스택", 12, K.MUTED)
    para(d, p, 22000, 11800, 10000, 1400,
         "tmp < end_data → 공유·디스크 갈래(21·23장)\ntmp >= end_data → 빈 페이지 갈래(39장)",
         13)
    para(d, p, 22000, 13300, 10000, 1100,
         "sched.h:88 — start_code·end_code·end_data · :100 — executable", 12,
         K.MUTED)

    # 20 get_empty_page
    p = d.slide("코드: get_empty_page", K.S_CODE,
                "mm/memory.c:274-282 · oom 33-37 · include/signal.h:23 SIGSEGV=11")
    d.code_panel(p, "src/mm/memory.c", 274, 282, 1100, 4400, 19700, 6800,
                 size=10, caption_extra="get_free_page + put_page")
    para(d, p, 1100, 11600, 19700, 2700,
         "둘 중 하나라도 실패하면 free_page(tmp) — tmp=0이어도 무시된다"
         "(91행: addr < LOW_MEM → return). 그리고 oom().", 15)
    d.code_panel(p, "src/mm/memory.c", 33, 37, 22000, 4400, 10000, 5000,
                 size=12, caption_extra="oom — 메모리 부족 정책")
    para(d, p, 22000, 9700, 10000, 4600,
         "\"out of memory\" 출력 후 do_exit(SIGSEGV).\n\n"
         "메모리를 회수하지는 않는다 — 프로세스를 죽일 뿐이다(§8). "
         "0.11에는 스왑·회수가 없다.", 15)
    d.banner(p, "메모리 부족 = 프로세스 죽음 — get_empty_page 실패의 끝")

    # 21 do_no_page (2/3)
    p = d.slide("코드: do_no_page (2/3) — 같은 프로그램을 돌리는 다른 태스크와 공유",
                K.S_CODE,
                "mm/memory.c:378-379 + share_page 344-363 · include/linux/sched.h:100 executable")
    d.code_panel(p, "src/mm/memory.c", 348, 361, 1100, 4400, 19700, 9450,
                 size=10, caption_extra="share_page — 같은 executable 탐색")
    nbox(d, p, 22100, 4400, 4700, 1300, "task[NR-1]", "역순 탐색 먼저",
         K.PAPER, s1=14, s2=12)
    d.text(p, 26850, 4800, 1200, 600, "…", 20, K.MUTED, True)
    nbox(d, p, 27400, 4400, 4700, 1300, "task[i]", "executable 같은가?",
         K.PAPER, s1=14, s2=12)
    arrow(d, p, 24200, 5800, "↓", 20, K.ORANGE)
    nbox(d, p, 22100, 6600, 10000, 1300, "try_to_share(address, p)",
         "clean 페이지면 양쪽 RO 로 공유", K.ORANGE, s1=14, s2=12)
    para(d, p, 22000, 8400, 10000, 6000,
         "exec가 inode를 current->executable 에 남겨 둔 이유(10장)가 여기서 쓰인다.\n\n"
         "같은 /bin/sh 를 여러 개 띄워도 코드 페이지는 사본을 만들지 않는다.\n\n"
         "do_no_page 378: share_page(tmp) 성공 → return — 디스크를 읽지 않는다.",
         15)

    # 22 try_to_share
    p = d.slide("코드: try_to_share — clean 페이지만 공유", K.S_CODE,
                "mm/memory.c:292-334 — bit6 = Dirty(Accessed는 bit5, §8) · 내 PDE 없으면 테이블 생성")
    d.code_panel(p, "src/mm/memory.c", 300, 312, 1100, 4400, 15200, 7900,
                 size=9, caption_extra="상대 PTE 계산 + clean 검사 0x41")
    d.code_panel(p, "src/mm/memory.c", 324, 333, 16900, 4400, 15700, 7300,
                 size=10, caption_extra="양쪽 RW=0 공유 + mem_map++")
    para(d, p, 1100, 12500, 15200, 1900,
         "0x41 = Dirty(bit6) + P(bit0) — 값이 정확히 0x01이어야 clean·present로 "
         "공유한다. 내 PDE가 없으면 페이지 테이블을 새로 만든다(to|7).", 14)
    nbox(d, p, 16950, 12000, 7400, 950, "상대 PTE = A | 5", None, K.TEAL, s1=13)
    nbox(d, p, 25050, 12000, 7400, 950, "내 PTE = A | 5", None, K.TEAL, s1=13)
    d.text(p, 20000, 12980, 1400, 600, "↓", 18, K.TEAL, True)
    d.text(p, 28100, 12980, 1400, 600, "↓", 18, K.TEAL, True)
    d.shape(p, 20550, 13600, 8300, 850, K.PAPER)
    d.text(p, 20750, 13720, 7900, 600, "물리 페이지 A — mem_map[A]++", 13, K.INK, True)

    # 23 do_no_page (3/3a)
    p = d.slide("코드: do_no_page (3/3a) — block 계산과 bmap×4", K.S_CODE,
                "mm/memory.c:380-385 · bmap fs/inode.c:140-143 · BLOCK_SIZE = 1024 — 다음 장(24)에서 이어짐")
    d.code_panel(p, "src/mm/memory.c", 380, 385, 1100, 4400, 19700, 5750,
                 size=12, caption_extra="block 산식 — 헤더 1블록 건너뜀")
    d.outline(p, 1100, 10600, 19700, 3500, K.ORANGE, 110)
    d.text(p, 1400, 10900, 19000, 900, "block = 1 + tmp / BLOCK_SIZE", 24,
           K.ORANGE, True)
    d.text(p, 1400, 12000, 19000, 1900,
           "1024B 블록 4개 = 한 페이지(4KB) · 헤더 1블록을 건너뛴 파일 오프셋에서\n"
           "bmap(current->executable, block) — 파일 블록 → 디스크 블록",
           15, K.PAPER)
    d.code_panel(p, "src/fs/inode.c", 140, 143, 22000, 4400, 10000, 4300,
                 size=12, caption_extra="bmap — _bmap(inode,block,0)")
    para(d, p, 22000, 9100, 10000, 5200,
         "bmap — 파일 블록 번호를 디스크 블록 번호로(직접/간접).\n\n"
         "실행 파일의 내용 = 디스크 블록 4개 = 페이지 1개.\n\n"
         "실제 읽는 주체는 다음 장의 bread_page.", 15)

    # 24 do_no_page (3/3b)
    p = d.slide("코드: do_no_page (3/3b) — bread_page·bss 0 채움·put_page", K.S_CODE,
                "mm/memory.c:386-396 · bread_page fs/buffer.c:296-315 · put_page 197-219(복습)")
    d.code_panel(p, "src/mm/memory.c", 386, 396, 1100, 4400, 15200, 8500,
                 size=11, caption_extra="bread_page · 꼬리 0 · put_page")
    d.code_panel(p, "src/fs/buffer.c", 301, 313, 16900, 4400, 15700, 8900,
                 size=10, caption_extra="bread_page — 블록 4개를 한 페이지에")
    nbox(d, p, 1100, 13300, 4800, 1000, "헤더 1블록", "건너뜀", None, K.MUTED,
         s1=12, s2=11)
    for i in range(4):
        nbox(d, p, 6100 + i * 5300, 13300, 5100, 1000, f"a.out 블록 {i + 1}",
             "1024B", K.TEAL, s1=12, s2=11)
    nbox(d, p, 27400, 13300, 4200, 1000, "꼬리 = 0", "end_data 넘는 bss",
         None, K.ORANGE, s1=12, s2=11)

    # 25 폴트 뒤 재실행
    p = d.slide('코드로 본 "폴트 뒤 재실행"', K.S_CODE,
                "mm/page.s:33-40 — 폴트(fault)형 예외: 저장된 EIP는 폴트 명령 자신(4회차 구분 복습)")
    d.flow(p, [("명령 X — 쓰기 접근", "공유 페이지(5)에서 #PF"),
               ("page_fault 실행", "저장 EIP = 명령 X 자신\nCR2·에러 코드만 남고"),
               ("iret 후", "같은 명령 X 재실행 —\n이번에는 PTE 하위 7")],
           y=4500, h=2800)
    d.code_panel(p, "src/mm/page.s", 33, 40, 1100, 8000, 19700, 6300,
                 size=10, caption_extra="레지스터를 모두 본래 값으로 복원")
    para(d, p, 22000, 7600, 10000, 6700,
         "폴트는 fault형 예외 — 트랩(시스템 콜)은 '다음 명령', 폴트는 '같은 명령'을 "
         "다시 실행한다.\n\n"
         "그래서 page.s는 eax·ecx·edx·ds·es·fs 를 모두 복원한다(pop 순서 34-39) — "
         "재실행되는 명령이 본래 환경을 봐야 하므로.\n\n"
         "iret 앞 addl $8,%esp — 인자 2개를 정확히 걷어낸다(6장 프레임).", 16)

    # ── 상태도 26–27 ──────────────────────────────────────────
    # 26 상태 변화도 ①
    p = d.slide("상태 변화도 ①: 선형 페이지(PTE) 한 칸의 상태", K.S_STATE,
                "노드 4개 + 전환 — 유지 조건: 그 물리 페이지를 가리키는 PTE 수 = mem_map 카운트")
    nbox(d, p, 1100, 4600, 6600, 1900, "부재 (0)",
         "매핑 없음 · mem_map=0", None, K.MUTED, s1=17, s2=12)
    nbox(d, p, 12400, 4600, 6600, 1900, "단독 RW (7)",
         "count = 1 · 마음대로 쓰기", K.TEAL, s1=17, s2=11)
    nbox(d, p, 23700, 4600, 7800, 1900, "공유 RO (5)",
         "count ≥ 2 · fork·try_to_share", K.TEAL, s1=17, s2=11)
    d.text(p, 8100, 5500, 1000, 900, "→", 24, K.TEAL, True)
    d.text(p, 7900, 6450, 4400, 700, "put_page (197-219)", 13, K.TEAL, True)
    d.text(p, 19200, 5500, 1000, 900, "→", 24, K.TEAL, True)
    para(d, p, 18900, 6350, 4700, 900,
         "copy_page_tables(177-183)\ntry_to_share(327-332)", 13, K.TEAL, True)
    nbox(d, p, 23700, 7700, 7800, 1900, "RO지만 단독 (5)",
         "count = 1 · 상대만 복사해 감", K.PAPER, s1=17, s2=11)
    d.text(p, 26900, 6600, 1400, 700, "↓", 22, K.ORANGE, True)
    para(d, p, 12400, 7750, 11100, 1450,
         "상대의 쓰기 폴트 un_wp_page(b) — 상대만 새 페이지로 갈아탄다 (231-237)",
         13, K.ORANGE, True)
    para(d, p, 12400, 9250, 11100, 1450,
         "내 쓰기 폴트 un_wp_page(a) — |= 2 제자리 승격, 복사 없음 (227-229)",
         13, K.ORANGE, True)
    nbox(d, p, 1100, 7700, 10000, 1900, "→ 부재로",
         "free_page_tables (105-131) — exit 시 전 매핑 해제·물리 반납",
         None, K.MUTED, s1=14, s2=11)
    d.table(p, 1100, 10750, [9000, 13500, 9000], [
        ["전환", "변경 데이터", "유지 조건"],
        ["put_page (부재→7)", "PTE 1개(0→7) + mem_map 1바이트(0→1)", "count = 1"],
        ["copy_page_tables·try_to_share (7→5)", "PTE 2개 + mem_map +1", "PTE 수(2) = count(2)"],
        ["쓰기 폴트 un_wp_page", "(b) PTE 1개 + mem_map 2바이트 + 4KB 복사 / (a) PTE 1개(+2)만",
         "분리 뒤 각 count = 1"],
    ], row_h=780, size=13)

    # 27 상태 변화도 ②
    p = d.slide("상태 변화도 ②: fork 뒤 쓰기 시나리오의 3자 상태", K.S_STATE,
                "행별 전환 원인 줄 번호 — 캡처 34·36장이 2·3·4행, 38·39장은 do_no_page 쪽")
    d.table(p, 1100, 4700, [8500, 5600, 5600, 5900, 5900], [
        ["전환 (mm/memory.c)", "부모 PTE", "자식 PTE", "물리 A count", "물리 B count"],
        ["fork 전 — 단독", "7", "—", "1", "—"],
        ["fork 후 (copy_page_tables 177·180·183)", "5", "5", "2", "—"],
        ["자식 쓰기 폴트 (un_wp_page 226-237 · (b))", "5", "7 → B", "1", "1"],
        ["부모 쓰기 폴트 (un_wp_page 226-229 · (a))", "7 (제자리)", "7 → B", "1", "1"],
    ], row_h=1100, size=14)
    para(d, p, 1100, 10900, 31500, 3400,
         "PTE 하위 비트: 7 = R/W + US + P · 5 = US + P (R/W=0) · 0 = 부재.\n"
         "3행에서 자식이 copy_page(A,B)로 새 페이지를 받고, 4행에서 부모는 이미 "
         "count=1이라 복사 없이 |= 2 로 승격된다 — 먼저 쓴 쪽이 복사본을 받는다(§8).",
         16)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 비교 28–30 ────────────────────────────────────────────
    # 28 비교 ①: 에러 코드 8가지
    p = d.slide("비교 ①: 에러 코드 P/W/U 8가지", K.S_CMP,
                "mm/page.s:28-40 · kernel/fork.c:24-37 — page.s 가 보는 것은 bit0 P 하나뿐")
    d.table(p, 1100, 4400, [4300, 10600, 7200, 9400], [
        ["(U,W,P)", "의미", "0.11에서 발생?", "가는 곳"],
        ["(1,0,0)", "사용자 모드 읽기 중 부재", "발생 — 아직 안 읽은 코드·데이터", "do_no_page"],
        ["(1,1,0)", "사용자 모드 쓰기 중 부재", "발생 — 스택·bss·힙", "do_no_page"],
        ["(1,1,1)", "사용자 모드 쓰기 보호", "발생 — COW 공유 페이지(5)", "do_wp_page"],
        ["(1,0,1)", "사용자 모드 읽기 보호", "없음 — 0.11 PTE는 모두 US=1", "(발생하지 않음)"],
        ["(0,0,1)", "링0 읽기 보호", "발생 없음", "(발생하지 않음)"],
        ["(0,0,0)", "커널 읽기 중 부재", "발생 — 적재 안 된 버퍼를 read가 채울 때", "do_no_page"],
        ["(0,1,0)", "커널 쓰기 중 부재", "발생 — 위와 같음(쓰기)", "do_no_page"],
        ["(0,1,1)", "커널 쓰기 보호", "386에서는 폴트 자체가 없음(09장)", "verify_area가 대신"],
    ], row_h=950, size=14)
    d.banner(p, "page.s 는 이 8가지를 P 하나로 압축해서 본다 — testl $1,%eax (page.s:28)", 13300, 18)

    # 29 비교 ②: 세 갈래
    p = d.slide("비교 ②: 부재 페이지를 채우는 세 갈래", K.S_CMP,
                "mm/memory.c:365-397 · 274-282 · 344-363 — 순서도 정해져 있다: 빈 페이지 → 공유 → 디스크")
    d.table(p, 1100, 4500, [4800, 9800, 8700, 8200], [
        ["갈래", "조건 (mm/memory.c)", "페이지 내용", "mem_map 영향"],
        ["빈 페이지", "!executable || tmp >= end_data (374-376)", "0으로 채움 — 스택·bss·힙", "+1 (새 페이지)"],
        ["공유", "share_page 성공 (378)", "다른 태스크의 페이지 (RO)", "기존 페이지 +1"],
        ["디스크", "그 외 (380-396)", "a.out 블록 4개 + 꼬리 0", "+1 (새 페이지)"],
    ], row_h=1250, size=15)
    para(d, p, 1100, 10100, 31500, 3400,
         "공유 가능하면 디스크를 읽지 않는다 — 탐색 비용(share_page)이 디스크 읽기"
         "(bmap×4 + bread_page)보다 싸기 때문이다.\n"
         "세 갈래 모두 끝은 put_page 또는 PTE 갱신 — 그리고 iret 후 같은 명령 재실행(25장).\n"
         "캡처 B-1(38장) = 디스크 갈래 · B-2(39장) = 빈 페이지 갈래.", 16)
    d.banner(p, "부재(P=0) 폴트의 선택지는 이 세 가지뿐 — 오늘 학습 목표 3")

    # 30 비교 ③: 두 경로
    p = d.slide("비교 ③: 쓰기 위반을 처리하는 두 경로", K.S_CMP,
                "사용자 코드의 쓰기 / 커널의 사용자 공간 쓰기 — 둘 다 un_wp_page 로 수렴한다")
    d.text(p, 1100, 4250, 31500, 600, "① 사용자 경로 — CPU가 폴트를 낸다", 16, K.ORANGE, True)
    d.flow(p, [("사용자 쓰기", "mov [x],1"), ("CPU #PF", "W=1·P=1 · CR2"),
               ("page.s → do_wp_page", "testl $1 → P=1"), ("un_wp_page", "복사·승격")],
           y=4900, h=2600)
    d.text(p, 1100, 7750, 31500, 600, "② 커널 경로 — 폴트가 없다, 커널이 흉내 낸다", 16, K.ORANGE, True)
    d.flow(p, [("sys_read 등", "read_write.c:64"), ("verify_area", "fork.c:24-37"),
               ("write_verify", "memory.c:261-272"), ("un_wp_page", "같은 함수!")],
           y=8400, h=2600)
    para(d, p, 1100, 11400, 31500, 2900,
         "차이는 '누가 폴트를 냈는가'뿐 — 페이지를 분리하는 일은 un_wp_page 하나가 한다.\n"
         "호출처: sys_read(read_write.c:64) · sys_time(sys.c:108) · sys_times(159) · "
         "sys_uname(224).\n"
         "386에는 CR0.WP가 없어 링0 쓰기가 폴트를 내지 않는다(09장) — read 전에 미리 분리한다.",
         15)

    # 31 숫자로 보는 fork + 자식 쓰기
    p = d.slide("숫자로 보는 fork + 자식 쓰기", K.S_CODE,
                "k 등 수치는 07회차 시연 환경 기준 예시 — 실제 값은 34·36장 캡처로 확정한다")
    d.example_tag(p)
    d.table(p, 1100, 5300, [8300, 10800, 12400], [
        ["항목", "fork 직후", "자식이 스택 한 페이지에 쓴 뒤"],
        ["셸(부모)의 페이지 수", "k개 — 그대로", "k개 — 그대로"],
        ["자식 PTE", "k개 추가 — 전부 하위 5(RO)", "k개 — 1개만 새 페이지(하위 7)"],
        ["그 페이지의 mem_map", "2 (부모·자식 공유)", "A = 1 · B = 1 (분리 완료)"],
        ["실제 복사된 4KB 페이지", "0개", "1개 — 쓴 페이지만"],
        ["쓰기 폴트 처리", "—", "자식: (b) 복사 1 · 부모: (a) 복사 0"],
    ], row_h=1200, size=14)
    para(d, p, 1100, 12900, 31500, 1500,
         "\"복사된 페이지 수 = 실제로 쓴 페이지 수\" — 이것이 fork를 싸게 만든다(42장). "
         "fork 직후 곧 exec하면 대부분 페이지는 복사 한 번 없이 반납된다.", 15)

    # ── 시연 32–40 ────────────────────────────────────────────
    # 32 시연 준비
    p = d.slide("시연 준비: 어떤 쓰기가 첫 폴트를 내는가", K.S_DEMO,
                "테스트 프로그램 없이도 시연 가능 — 셸의 어떤 명령이든 즉시 do_wp_page 가 걸린다")
    para(d, p, 1100, 4300, 15200, 10000,
         "fork에서 돌아온 직후, 사용자 코드의 첫 push / call 이 스택 페이지에 쓴다.\n\n"
         "부모든 자식이든 fork 직후 첫 COW 대상은 스택 페이지다 — 함수 호출 한 번이면 "
         "폴트가 난다.\n\n"
         "따라서 셸 프롬프트에서 아무 명령이나 입력해도 do_wp_page 가 즉시 걸린다.\n\n"
         "전역 변수(데이터 페이지) 쓰기를 명시적으로 보려면 오른쪽 cow.c 를 게스트 "
         "gcc로 컴파일해 돌린다(선택).", 15)
    auto_pane(d, p, 16900, 4300, 15700, 6600,
              "cow.c — 선택 시연 (게스트 gcc)",
              "int x = 0;                 /* .data — fork 후 공유 RO */\n"
              "int main(void)\n"
              "{\n"
              "    int pid = fork();\n"
              "    if (pid == 0)\n"
              "        x = 1;            /* 자식 — 첫 쓰기 폴트 */\n"
              "    printf(\"pid=%d x=%d\\n\", getpid(), x);\n"
              "    return 0;              /* 부모 x=0 · 자식 x=1 */\n"
              "}", start=13)
    d.banner(p, "다음 장부터 lab/ QEMU + GDB — 중단점 un_wp_page · do_no_page · write_verify")

    # 33 시연 A-1
    p = d.slide("시연 A-1: fork 직후 쓰기 폴트 잡기", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 TCG · GDB · 줄 번호는 lab 기준(src와 다를 수 있음)")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — 환경 · 중단점 · 관찰",
              "# lab/ make debug → gdb tools/system · target remote :1234 · c\n"
              "(gdb) b un_wp_page\n"
              "# do_wp_page 보다 낫다 — PTE 포인터 table_entry 를 바로 봄\n"
              "(gdb) c\n"
              "# 셸에 ls 입력 → 셸이 fork → 스택 쓰기 → 정지\n"
              "Breakpoint 1, un_wp_page (table_entry=0x37f8c) at mm/memory.c:221\n"
              "(gdb) p current->pid\n"
              "# 부모 셸 pid인지 자식 pid인지 — 스케줄 순서에 따라 다름\n"
              "(gdb) bt\n"
              "# 기대: un_wp_page ← do_wp_page ← page_fault\n"
              "(gdb) p/x *table_entry\n"
              "# 기대 0x....005 — P+US, RW=0 → A = 값 & 0xfffff000\n"
              "(gdb) p mem_map[(A-0x100000)>>12]\n"
              "# 기대 2 — 아직 공유 중\n"
              "(gdb) p/x $cr2    # 노출 안 되면 up 후 p/x address", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· PTE 하위 5 — COW 대상 확정\n"
         "· A = 값 & 0xfffff000\n"
         "· mem_map[(A-0x100000)>>12] = 2 — 복사 전\n"
         "· bt 3계층 — 12-15장 코드의 실측\n"
         "· p current->pid — 먼저 쓴 쪽은 부모일 수도(§8)\n\n"
         "기대 출력과 캡처 01은 다음 장(34).", 14)

    # 34 캡처 A-1
    p = d.slide("캡처 A-1: 복사 전", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 값은 부팅마다 다름(§8)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) b un_wp_page ; c        # 셸에서 ls → fork\n"
                         "Breakpoint 1, un_wp_page (table_entry=0x37f8c)\n"
                         "    at mm/memory.c:221\n"
                         "(gdb) p current->pid\n"
                         "$1 = 4        # 부모/자식 중 먼저 스케줄된 쪽\n"
                         "(gdb) bt\n"
                         "#0 un_wp_page   mm/memory.c:221\n"
                         "#1 do_wp_page (error_code=3, address=0x427ffe8)  :247\n"
                         "#2 page_fault   mm/page.s:32\n"
                         "(gdb) p/x *table_entry\n"
                         "$2 = 0xd7f005  # 하위 5=P+US(RW=0) → A=0xd7f000\n"
                         "(gdb) p mem_map[(0xd7f000-0x100000)>>12] ; $3 = 2\n"
                         "              # 공유 중 — 복사 전",
                         "01-un-wp-page-before.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· PTE 하위 5 (P+US, RW=0)\n"
         "· mem_map = 2\n"
         "· backtrace — un_wp_page ← do_wp_page ← page_fault\n\n"
         "상태 변화도 ②(27장)의 \"fork 후 (5, 5, 2)\" 행이 바로 이 화면이다.\n\n"
         "어느 쪽 pid가 먼저 걸리는지 꼭 말한다 — '부모=원본' 오해 방지(§8).",
         14)

    # 35 시연 A-2
    p = d.slide("시연 A-2: un_wp_page 통과 후", K.S_DEMO,
                "mm/memory.c:226-237 — (b) 복사 직후와 상대 태스크의 (a) 제자리 승격까지")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — finish 후 재조회 · (a) 갈래 확인",
              "(gdb) finish            # un_wp_page 완료 — 복사 직후\n"
              "(gdb) p/x *(unsigned long *)<PTE 주소>\n"
              "# 기대 하위 7 — RW 켬 · 새 주소 B != A\n"
              "(gdb) p mem_map[(A-0x100000)>>12]   # 기대 1\n"
              "(gdb) p mem_map[(B-0x100000)>>12]   # 기대 1\n"
              "(gdb) x/4wx A ; x/4wx B\n"
              "# 두 페이지 내용 동일 — copy_page 직후\n"
              "(gdb) c\n"
              "# 상대 태스크의 쓰기 폴트 — (a) 갈래인지 확인\n"
              "(gdb) p/x *table_entry\n"
              "# 하위 5 · p mem_map[...]  →  1\n"
              "(gdb) finish ; p/x *(unsigned long *)<같은 PTE 주소>\n"
              "# 하위 7 — 제자리 승격 |= 2, 복사 없음", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· PTE 하위 5 → 7, 주소 A → B\n"
         "· mem_map: A 2→1, B = 1 — 분리 완료\n"
         "· x/4wx A 와 B 동일 — 4KB 복사 직후\n"
         "· 상대 태스크는 (a) 갈래 — 하위 5→7 제자리, 복사 0\n\n"
         "상태 변화도 ②의 3·4행을 이 순서로 본다.\n"
         "캡처 02·03은 다음 장(36).", 14)

    # 36 캡처 A-2
    p = d.slide("캡처 A-2: 복사 후", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 어느 쪽이 먼저 폴트를 냈는지는 스케줄 순서(각주)")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) finish              # 복사 직후 관찰\n"
                         "Value returned is void\n"
                         "(gdb) p/x *(unsigned long *)0x37f8c\n"
                         "$5 = 0xe12007     # 하위 7=RW · B=0xe12000 != A\n"
                         "(gdb) p mem_map[(0xd7f000-0x100000)>>12]  # A\n"
                         "$6 = 1\n"
                         "(gdb) p mem_map[(0xe12000-0x100000)>>12]  # B\n"
                         "$7 = 1\n"
                         "(gdb) x/4wx 0xd7f000 ; x/4wx 0xe12000\n"
                         "# 두 페이지 내용 동일 — copy_page 직후",
                         "02-un-wp-page-after.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) c            # 상대 태스크 쓰기 폴트\n"
                         "Breakpoint 1, un_wp_page (0x35f1c) :221\n"
                         "(gdb) p/x *table_entry\n"
                         "$8 = 0xd7f005      # 하위 5 — 아직 RW=0\n"
                         "(gdb) p mem_map[(0xd7f000-0x100000)>>12]\n"
                         "$9 = 1            # count 1 → (a) 갈래\n"
                         "(gdb) finish\n"
                         "(gdb) p/x *(unsigned long *)0x35f1c\n"
                         "$10 = 0xd7f007     # |= 2 제자리 승격\n"
                         "                   # 복사 없음",
                         "03-un-wp-page-promote.png")
    para(d, p, 1100, 14600, 31500, 1700,
         "왼쪽(02) = 상태 변화도 ② \"자식 쓰기 폴트 (5, 7→B, 1, 1)\" 행 · "
         "오른쪽(03) = \"부모 쓰기 폴트 (7, 7→B, 1, 1)\" 행 — (a)갈래 제자리 승격 병행 게시.",
         14)

    # 37 시연 B
    p = d.slide("시연 B: 요구 적재 — do_no_page 관찰", K.S_DEMO,
                "mm/memory.c:365-397 — lab/ 빌드 · QEMU i386 · GDB · 줄 번호는 lab 기준")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — do_no_page 중단점",
              "(gdb) b do_no_page\n"
              "(gdb) disable 1     # (또는 delete) A의 중단점 해제\n"
              "(gdb) c\n"
              "# 셸에서 새 명령 ls → 자식이 exec → 첫 fetch 부재\n"
              "Breakpoint 2, do_no_page (error_code=4, address=0x4000000)\n"
              "    at mm/memory.c:365\n"
              "(gdb) p/x address ; p/x current->start_code\n"
              "(gdb) p address - current->start_code\n"
              "# 기대 0 — 엔트리 페이지 (a_entry = 0)\n"
              "(gdb) p error_code\n"
              "# 기대 4 또는 6 — U=1, P=0\n"
              "(gdb) p current->executable->i_num\n"
              "(gdb) finish ; x/8xb address\n"
              "# PTE 하위 7 · a.out 코드 바이트\n"
              "(gdb) c            # 다음 정지는 스택 — tmp >= end_data", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "절차\n\n"
         "1. b do_no_page — A는 disable\n"
         "2. 셸에서 새 외부 명령(ls)\n\n"
         "관찰 포인트\n\n"
         "· address - start_code = 0 — 엔트리\n"
         "· error_code 4 또는 6 — U=1, P=0\n"
         "· finish 후 PTE 하위 7 + 코드 바이트\n"
         "· 다음 정지 = 스택(빈 페이지 갈래, 39장)\n\n"
         "캡처 04·05는 38·39장.", 14)

    # 38 캡처 B-1
    p = d.slide("캡처 B-1: 코드 페이지 — 디스크 갈래", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — lab 소스 줄 번호는 src와 다를 수 있음(각주)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) b do_no_page ; disable 1 ; c   # 셸 ls\n"
                         "Breakpoint 2, do_no_page (error_code=4, address=0x4000000)\n"
                         "    at mm/memory.c:365\n"
                         "(gdb) p address - current->start_code\n"
                         "$12 = 0         # 엔트리 페이지 (a_entry = 0)\n"
                         "(gdb) p error_code\n"
                         "$13 = 4         # U=1, P=0 (또는 6: W=1)\n"
                         "(gdb) p current->executable->i_num\n"
                         "$14 = 96        # 실행 파일 inode (예시)\n"
                         "(gdb) finish ; x/8xb 0x4000000\n"
                         "# 55 8b ec ...  a.out 코드 — PTE 하위 7",
                         "04-do-no-page-code.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· 오프셋 0 — a_entry 가 0인 엔트리 페이지\n"
         "· error_code 4 또는 6\n"
         "· finish 후 PTE 7 · 코드 바이트\n\n"
         "비교 ②(29장)의 \"디스크\" 행 — bmap×4 + bread_page 가 "
         "a.out 블록을 채웠다.\n\n"
         "실행 파일 inode 번호 값은 예시(실측 아님).", 14)

    # 39 캡처 B-2
    p = d.slide("캡처 B-2: 스택 페이지 — 빈 페이지 갈래", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — lab 소스 줄 번호는 src와 다를 수 있음(각주)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) c                # 다음 정지 — 스택 페이지\n"
                         "Breakpoint 2, do_no_page (error_code=6, address=0x43fff000)\n"
                         "    at mm/memory.c:365\n"
                         "(gdb) p/x address\n"
                         "$15 = 0x43fff000       # 64MB 칸 끝 근처\n"
                         "(gdb) p/x current->start_code\n"
                         "$16 = 0x4000000\n"
                         "(gdb) p address - current->start_code\n"
                         "$17 = 0x3fff000        # tmp >= end_data\n"
                         "                       # → 빈 페이지 갈래 (374-376)\n"
                         "(gdb) finish           # get_empty_page → 0 페이지",
                         "05-do-no-page-stack.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· 64MB 칸 끝 근처 주소\n"
         "· tmp >= end_data — 데이터 영역 밖\n\n"
         "비교 ②(29장)의 \"빈 페이지\" 행 — 디스크를 읽지 않고 "
         "0으로 채운 새 페이지.\n\n"
         "19장 개념 바(코드·데이터 | 빈 공간 | 스택)의 오른쪽 끝이 여기다.",
         14)

    # 40 시연 C(선택)
    p = d.slide("시연 C(선택): 커널 쓰기는 폴트가 없다", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 줄 번호는 lab 기준(각주) · 실패 시 아래 캡처로 대체")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) b write_verify ; c   # 셸에서 cat + 입력 한 줄\n"
                         "Breakpoint 3, write_verify (address=0x42ffe70)\n"
                         "    at mm/memory.c:261\n"
                         "(gdb) bt\n"
                         "#0 write_verify (address=0x42ffe70) mm/memory.c:261\n"
                         "#1 verify_area (addr=0x2fe70, size=1) kernel/fork.c:24\n"
                         "#2 sys_read (fd=0, buf=0x2fe70, count=1) :64\n"
                         "#3 system_call () kernel/system_call.s\n"
                         "                           # 기대 호출 순서 확인",
                         "06-write-verify-bt.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "절차\n\n"
         "1. b write_verify — 중단점 설정\n"
         "2. 셸에서 cat 실행 후 한 줄 입력 → read() 경로\n"
         "3. bt 로 호출자 확인\n\n"
         "기대: verify_area ← sys_read ← system_call\n\n"
         "비교 ③(30장) ② 경로의 실측 — 폴트 없이 커널이 직접 COW를 흉내 낸다.\n"
         "중단점이 안 걸리면 이 캡처(06)로 대체한다.", 14)

    # ── 정답 41–42 ────────────────────────────────────────────
    # 41 질문의 답 (1)
    p = d.slide("질문의 답 (1): 부모의 값이 그대로인 이유", K.S_ANS,
                "mm/memory.c:150-189(fork) · 221-238(두 쓰기 폴트) — 16장 그림의 최종 컷")
    nbox(d, p, 1100, 4300, 6200, 1300, "부모 PTE = A | 5", None, K.TEAL, s1=15)
    arrow(d, p, 3400, 5700, "↓", 22)
    nbox(d, p, 1100, 6600, 8000, 1600, "물리 페이지 A", "x = 0 — 원래 값",
         K.PAPER, s1=15, s2=13)
    badge(d, p, 1100, 8500, 8000, "mem_map[A] = 1", K.TEAL)
    badge(d, p, 25600, 4300, 6600, "자식: x = 1 → #PF (U=1·W=1·P=1)", K.ORANGE, 620, 12)
    nbox(d, p, 18800, 5100, 6200, 1300, "자식 PTE = B | 7", None, K.ORANGE, s1=15)
    arrow(d, p, 21100, 6500, "↓", 22, K.ORANGE)
    nbox(d, p, 18800, 7400, 8000, 1600, "물리 페이지 B", "x = 1 — 복사해 쓴 값",
         K.ORANGE, s1=15, s2=13)
    badge(d, p, 18800, 9300, 8000, "mem_map[B] = 1", K.ORANGE)
    d.text(p, 8600, 7150, 9600, 700, "copy_page(A,B) →", 17, K.ORANGE, True)
    para(d, p, 1100, 10300, 31500, 4100,
         "1  fork — PTE만 복사, 부모·자식 모두 읽기 전용(하위 5) · mem_map[A] = 2\n"
         "2  자식의 x = 1 — #PF(U=1, W=1, P=1) → page.s → do_wp_page → "
         "un_wp_page(b): 자식 PTE만 새 페이지 B(7)로\n"
         "3  부모의 PTE는 여전히 A를 가리킨다 — 그래서 부모의 x는 그대로 0이다.",
         15, K.PAPER, True)

    # 42 질문의 답 (2)
    p = d.slide("질문의 답 (2): 그래서 fork는 싸다", K.S_ANS,
                "복사되는 것은 '쓴 페이지'뿐 — exec가 곧 따라오면(09회차) 대부분 페이지는 복사되지 않는다")
    d.cards(p, [
        ("복사되는 것 = 쓴 페이지뿐",
         "fork 직후 대부분 페이지는\n공유 RO 로 그대로\n쓰기가 닿은 페이지만\n"
         "un_wp_page(b) 가 복사\n\n31장: 복사 페이지 수\n= 실제로 쓴 페이지 수"),
        ("exec가 따라오면 더 싸진다",
         "셸의 fork → exec:\n자식이 쓴 페이지만 복사\n나머지는 그대로 —\n"
         "exec는 free_page_tables\n로 공유 페이지 반납\n(09회차 fs/exec.c)"),
        ("현대 커널도 같은 원리",
         "fork PTE 복사 +\n첫 쓰기 복사 — 같다\n\n"
         "차이: 486+ CR0.WP 로\n커널 쓰기도 폴트\n(선제 검사 불필요)"),
    ], y=4400, h=8600)
    d.banner(p, "fork는 PTE를 복사하고, 페이지 복사는 첫 쓰기 폴트가 한다 — Copy-on-Write")

    # 43 오늘 코드가 쓰는 데이터 요약
    p = d.slide("오늘 코드가 쓰는 데이터 요약", K.S_WRAP,
                "PTE 하위 비트: 7=RW+US+P · 5=US+P · bit6=Dirty(bit5=Accessed) · sched.h:88·100 — start_code·end_code·end_data·executable")
    d.table(p, 1100, 4400, [6600, 11800, 13100], [
        ["함수", "읽는 것", "바꾸는 것"],
        ["page_fault (page.s)", "CR2, 에러 코드(스택)", "레지스터 보존만 — 데이터 변경 없음"],
        ["do_wp_page", "PDE·PTE(주소 계산 255-257)", "없음 — un_wp_page 에 위임"],
        ["un_wp_page", "mem_map[MAP_NR(page)]", "PTE 1개 · mem_map 1-2바이트 · 복사 시 4KB"],
        ["write_verify", "PDE, PTE 하위 2비트(3&==1)", "un_wp_page 경유"],
        ["verify_area", "current->ldt[2] base(get_base)", "없음 — 페이지마다 write_verify"],
        ["do_no_page", "start_code·end_data·executable·bmap", "PTE 1개(put_page) · 페이지 4KB(디스크)"],
        ["try_to_share", "상대 PTE bit6 Dirty(0x41)", "양쪽 PTE(&=~2) · mem_map++"],
        ["get_empty_page / oom", "—(get_free_page·put_page)", "PTE 1개 · mem_map 1 / do_exit(SIGSEGV)"],
    ], row_h=1000, size=13)

    # 44 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(45) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "page.s 는 에러 코드의 어느 비트만 보고 핸들러를 고르는가? W 비트는 어디서 쓰이는가?",
         K.TEAL, 15)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2",
         "un_wp_page 가 복사 없이 |= 2 만 하는 경우는 언제인가?", K.TEAL, 15)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3",
         "read(fd, buf, n) 에서 buf 가 fork 로 공유 중인 페이지에 있으면 "
         "커널은 어떻게 부모 페이지를 보호하는가?", K.TEAL, 15)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4",
         "exec 직후 프로그램의 첫 명령 페이지는 메모리에 있는가? "
         "없다면 누가 언제 채우는가?", K.TEAL, 15)

    # 45 이해 확인 정답
    p = d.slide("이해 확인 정답", K.S_QUIZ,
                "근거 줄 번호 포함 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "A1",
         "bit0 P만 (testl $1,%eax, page.s:28). W/U 비트는 0.11 핸들러가 쓰지 않는다. "
         "do_wp_page는 'present인데 폴트' = 쓰기 보호 위반으로 가정한다.", K.ORANGE, 14)
    qbox(d, p, 1100, 6850, 31500, 2400, "A2",
         "페이지가 LOW_MEM 이상이고 mem_map[]==1일 때(memory.c:226-229). "
         "상대 태스크가 이미 자기 복사본으로 갈아탔거나, 공유가 끝난 경우.", K.ORANGE, 14)
    qbox(d, p, 1100, 9400, 31500, 2400, "A3",
         "386은 ring 0 쓰기에 R/W 비트를 적용하지 않으므로 폴트가 나지 않는다. "
         "sys_read가 먼저 verify_area(buf,count)(read_write.c:64) → write_verify → "
         "un_wp_page로 미리 분리한다.", K.ORANGE, 14)
    qbox(d, p, 1100, 11950, 31500, 2400, "A4",
         "없다. 첫 명령 fetch가 부재 폴트(P=0)를 내고 do_no_page가 bmap/bread_page로 "
         "a.out 블록 4개를 읽어 put_page한다(memory.c:380-394).", K.ORANGE, 14)

    # 46 정리·다음 회차 예고
    p = d.slide("정리·다음 회차 예고", K.S_WRAP,
                "09회차 — exec()와 프로그램 실행 · 파트 C «메모리» 마무리(07 주소 변환 · 08 폴트·CoW)")
    d.cards(p, [
        ("09회차 예고",
         "PID는 그대로인데\n프로그램은 어떻게 바뀌는가?\n\n"
         "오늘 본 do_no_page가\nexec 직후 프로그램을\n실제로 적재한다"),
        ("미리 볼 파일",
         "fs/exec.c\ninclude/a.out.h\n\n"
         "a.out 헤더에서\nend_code·end_data 계산\n(19장 개념 바의 연장)"),
        ("파트 C «메모리» 마무리",
         "07 주소 변환 —\n페이지 테이블·mem_map\n08 폴트·CoW — 오늘\n\n"
         "두 회차로\n메모리 축 완결"),
    ], y=4400, h=8200)
    d.banner(p, "fork는 PTE만 복사한다 — 페이지 복사는 첫 쓰기 폴트가 한다 · Copy-on-Write")


if __name__ == "__main__":
    K.run(globals())
