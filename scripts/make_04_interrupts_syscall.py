#!/usr/bin/env python3
"""04회차 덱 — 인터럽트·예외·시스템 콜 (output/04-interrupts-syscall.pptx)

계획: materials/slide-plans/04-interrupts-syscall.md (§2 표 48행 1:1 · §3 앞부분 명세 ·
§4 시각자료 · §5 캡처 5종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="04", total=48, slug="04-interrupts-syscall",
    part_no="B", part="«실행의 길»",
    title="04. 인터럽트·예외·시스템 콜",
    question="write(1, ...) 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?",
    done=3,
    today_line="write(1, ...) 한 줄이 int $0x80으로 커널에 들어가 "
               "iret로 돌아오는 길을 통째로 따라간다",
    next_lines=[
        "03 → 04   03: main()이 trap_init/sched_init으로 IDT를 채웠다 → 04: main이 끝나고 셸이 살지만 그 순간부터 틱·입력이 도착한다",
        "04 → 05   04: int 0x80 진입과 ret_from_sys_call 복귀를 봤다 → 05: ret_from_sys_call에서 이어지는 스케줄 — _timer_interrupt가 do_timer를 불러 schedule()로 가면 돌아오는 태스크가 바뀐다",
    ],
    road_note=("오늘은 10단계 전부를 밟는 회차다 — 상태도(21) · 비교(13·14·27) · 정답(43) · "
               "확인(47), 없는 단계 없음.\n오늘 끝에 GDB 화면(캡처 A-1·A-2·B)으로 핵심 질문의 "
               "답을 직접 확인한다."),
    STRUCT=dict(
        teal=["proc", "entry"],
        today=[("system_call.s", "시스템 콜 진입"),
               ("traps.c", "예외 처리"),
               ("asm.s", "예외 진입 어셈블리")],
        flow="write() → int 0x80 → sys_call_table[4] → sys_write → iret",
        up="↑ iret · EAX = 쓴 바이트",
        user="sh · 사용자 프로그램 — write(1, …)",
    ),
)

CHECKS = dict(
    captions={
        7: "src/boot/head.s:78-93",
        8: "src/boot/head.s:150-162",
        9: "src/init/main.c:126-136",
        10: "src/include/asm/system.h:22-31",
        11: "src/include/asm/system.h:33-40",
        12: "src/boot/head.s:79-84",
        15: "src/lib/write.c:7-10",
        16: "src/include/unistd.h:172-183",
        17: "src/include/unistd.h:133-144",
        18: "src/include/unistd.h:60-66",
        20: "src/kernel/system_call.s:35-46",
        22: "src/kernel/system_call.s:80-94",
        23: "src/fs/read_write.c:83-94",
        24: "src/kernel/system_call.s:95-100",
        25: "src/kernel/system_call.s:101-114",
        26: "src/kernel/system_call.s:121-128",
        28: "src/kernel/traps.c:185-201",
        29: "src/kernel/asm.s:19-34",
        30: "src/kernel/asm.s:97-112",
        31: "src/kernel/traps.c:63-74",
        32: "src/kernel/sched.c:406-410",
        33: "src/kernel/system_call.s:176-188",
    },
    required=[
        "set_intr_gate", "set_trap_gate", "set_system_gate", "_set_gate",
        "0x8E00", "0x8F00", "0xEF00", "0x00080000", "DPL", "게이트",
        "ignore_int", "idt_descr", "sys_call_table", "nr_system_calls",
        "__NR_write", "_syscall3", "int $0x80", "bad_sys_call",
        "reschedule", "ret_from_sys_call", "OLDESP", "OLDSS", "iret",
        "tss.esp0", "do_divide_error", "no_error_code", "error_code",
        "do_exit(11)", "EOI", "jiffies", "LATCH", "rw_char", "do_timer",
        "sys_write", "divide error", "move_to_user_mode", "xchgl",
        "0x17", "0x0f", "가짜 오류 코드",
    ],
    prereq=[
        ("게이트", "src/boot/head.s:78-93"),
        ("#GP", "src/include/asm/system.h:22-31"),
        ("sys_call_table", "src/kernel/system_call.s:80-94"),
        ("int $0x80", "src/lib/write.c:7-10"),
    ],
    structure_nodes=["system_call.s", "asm.s", "traps.c", "unistd.h", "sys.h"],
    capture_slides=[36, 37, 39, 41],
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


def cards_sz(d, p, cards, y, h, t_size=17, b_size=14):
    """d.cards 와 같은 모양 — 본문 글자 크기·줄수에 맞춘 카드 (deckkit 불변).

    본문은 wrap_kr 로 미리 줄바꿈해 줄수를 예측 가능하게 한다.
    카드 높이는 2500(제목대) + 줄수×b_size×52 + 300 이상이어야 한다."""
    gap, total = 600, 31500
    width = (total - gap * (len(cards) - 1)) // len(cards)
    for i, (title, body) in enumerate(cards):
        x = 1100 + i * (width + gap)
        d.shape(p, x, y, width, h, K.PAPER)
        d.shape(p, x, y, width, 150, K.TEAL if i % 2 == 0 else K.ORANGE)
        tsize = min((K.fit_size(line, t_size, width - 1100, min_size=10)
                     for line in title.split("\n")), default=t_size)
        d.text(p, x + 550, y + 650, width - 1100, 1700, title, tsize, K.INK, True)
        d.text(p, x + 550, y + 2500, width - 1100, h - 2700,
               wrap_kr(body, (width - 1100) * 0.97, b_size), b_size, K.INK)


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


def code_h(n, size):
    """code_panel 높이 — n줄 size pt."""
    return 1350 + n * size * 58


def populate(d):
    # ── 배경 05–06 · 19 ───────────────────────────────────────
    # 05 왜 call sys_write가 안 되는가
    p = d.slide("왜 call sys_write가 안 되는가", K.S_BG,
                "include/asm/system.h:1-14(move_to_user_mode) · init/main.c:137 — 01·02회차 CPL/DPL 표 재사용")
    para(d, p, 1100, 4200, 31500, 1800,
         "셸의 write() stub가 sys_write 를 직접 call 할 수 없다 — 목적지는 커널 코드 세그먼트"
         "(0x08, DPL 0)에 있고 호출자는 CPL 3이다. CPL 이 낮은 쪽으로의 직접 점프·call 은 "
         "#GP(13번)로 막힌다.")
    d.table(p, 1100, 6300, [5200, 12900, 13400], [
        ["항목", "사용자 (셸)", "커널"],
        ["코드 세그먼트", "CS = 0x0f — LDT, CPL 3", "CS = 0x08 — GDT, DPL 0"],
        ["스택 세그먼트", "SS = 0x17 — LDT", "SS = 0x10 — GDT"],
        ["데이터 접근", "DS·ES = 0x17", "DS·ES = 0x10 · FS = 0x17 (사용자 데이터)"],
        ["직접 far call 시도", "목적지 DPL 0 < CPL 3 → #GP", "게이트를 통해서만 진입 가능"],
    ], row_h=1350, size=15)
    para(d, p, 1100, 13600, 31500, 900,
         "반대 방향(0→3)은 이미 봤다 — main.c:137 의 move_to_user_mode() (system.h:1-14) 가 "
         "iret 로 처음 CPL 3 으로 내려갔다. 3→0 을 여는 열쇠가 오늘의 IDT 게이트다.", 15)
    d.banner(p, "오늘의 질문 재정의 — 커널에 들어가는 통로가 곧 IDT 게이트다")

    # 06 세 가지 진입 원인
    p = d.slide("세 가지 진입 원인 — 하나의 IDT로 모두 받는다", K.S_BG,
                "kernel/traps.c:181-208 · kernel/sched.c:385-412 · include/unistd.h:133-144")
    d.cards(p, [
        ("하드웨어 인터럽트",
         "장치 → 8259A PIC → CPU\n번호 0x20~0x2F (IRQ+0x20)\n\n"
         "타이머 0x20 · 키보드 0x21\n하드디스크 0x2E · 플로피 0x26\n\n"
         "언제: 장치가 준비되었을 때\n주체: 장치 (명령과 무관)"),
        ("CPU 예외",
         "명령 실행 중 CPU가 감지\n번호 0~16\n\n"
         "0 나누기(#DE) · #GP(13)\n페이지 폴트(14) · …\n\n"
         "언제: 바로 그 명령에서\n일부는 오류 코드를 push"),
        ("소프트웨어 인터럽트",
         "int n 명령이 일으킴\n0x80 = 시스템 콜\n\n"
         "사용자 프로그램이 원할 때\nunistd.h stub 안의 int $0x80\n\n"
         "언제: 프로그램 마음대로\n주체: 프로그램 자신"),
    ], y=4500, h=9900)
    d.banner(p, "공통점 — 셋 다 번호 하나로 IDT를 찾아간다 · 차이 — 발생 시점과 오류 코드 유무")

    # ── 코드 07–12 (게이트 만들기) ────────────────────────────
    # 07 IDT 한 항목 = 8바이트 게이트
    p = d.slide("IDT 한 항목 = 8바이트 게이트", K.S_CODE,
                "2회차 IDT 복습 — boot/head.s:78-93 setup_idt 가 256개를 전부 ignore_int 로 채운다")
    d.code_panel(p, "src/boot/head.s", 78, 93, 1100, 4150, 19700, 10250,
                 size=9, caption_extra="idt_descr 222-224 · _idt 232")
    d.text(p, 22000, 4150, 10600, 600, "게이트 8바이트 필드", 16, K.TEAL, True)
    nbox(d, p, 22000, 5150, 5050, 1700, "오프셋 하위 16비트", "bits 15…0", K.PAPER, s1=13, s2=11)
    nbox(d, p, 27400, 5150, 5300, 1700, "선택자 0x0008", "bits 31…16 — 커널 코드", K.TEAL, s1=13, s2=11)
    d.text(p, 22000, 6950, 10600, 500, "↑ 하위 4바이트 — *gate_addr", 12, K.MUTED)
    nbox(d, p, 22000, 7630, 5050, 1700, "P · DPL · type", "bits 23…16 = 0x8E 계열", K.TEAL, s1=13, s2=11)
    nbox(d, p, 27400, 7630, 5300, 1700, "오프셋 상위 16비트", "bits 47…32", K.PAPER, s1=13, s2=11)
    d.text(p, 22000, 9430, 10600, 500, "↑ 상위 4바이트 — gate_addr+4", 12, K.MUTED)
    para(d, p, 22000, 10300, 10600, 6200,
         "수업 시작 순간 모든 번호(0~255)가 같은 진입점 ignore_int 를 가리킨다.\n\n"
         "idt_descr(222-224): 한계 256*8-1 · 기준 _idt · lidt 로 로드.\n"
         "_idt(232): .fill 256,8,0 — 2KB 표.\n\n"
         "이후 trap_init · sched_init · 장치 init 이 필요한 칸만 덮어쓴다(09장).", 14)

    # 08 ignore_int
    p = d.slide("ignore_int — 모든 번호의 기본 핸들러", K.S_CODE,
                "boot/head.s:150-170 — \"Unknown interrupt\" 출력 후 iret · setup_idt 가 256칸 전부에 연결")
    d.code_panel(p, "src/boot/head.s", 150, 162, 1100, 4150, 19700, 8950,
                 size=10, caption_extra="진입 — 저장")
    d.code_panel(p, "src/boot/head.s", 163, 170, 22000, 4150, 10600, 6500,
                 size=11, caption_extra="복귀 — iret")
    para(d, p, 22000, 11000, 10600, 3200,
         "eax·ecx·edx·ds·es·fs 를 push 하고 printk 후 역순 pop — 진입 코드의 "
         "기본형이다(27장 비교의 한 축).\n\n"
         "부팅 중 오지 않은 번호가 울리면 이 메시지가 콘솔에 찍힌다.", 14)
    d.banner(p, "정상 부팅 뒤에는 대부분의 칸이 진짜 핸들러로 덮여 있다 — 덮어쓰기 주체는 다음 장")

    # 09 누가 언제 IDT를 덮어쓰는가
    p = d.slide("누가 언제 IDT를 덮어쓰는가", K.S_CODE,
                "init/main.c:126-136 — trap_init(127) 먼저 · sched_init(132) 나중 · 이후 장치 init")
    d.code_panel(p, "src/init/main.c", 126, 136, 1100, 4150, 14200, 8400, size=11)
    d.table(p, 15900, 4250, [2300, 4100, 4400, 5000], [
        ["번호", "매크로", "핸들러", "소스:줄"],
        ["0x20", "set_intr_gate", "timer_interrupt", "sched.c:409"],
        ["0x80", "set_system_gate", "system_call", "sched.c:411"],
        ["0x21", "set_trap_gate", "keyboard_interrupt", "chr_drv/console.c:683"],
        ["0x23·24", "set_intr_gate", "rs2·rs1", "chr_drv/serial.c:39-40"],
        ["0x2E", "set_intr_gate", "hd_interrupt", "blk_drv/hd.c:346"],
        ["0x26", "set_trap_gate", "floppy_interrupt", "blk_drv/floppy.c:460"],
        ["0~16", "trap·system_gate", "divide_error 등", "traps.c:185-201"],
    ], row_h=900, size=12)
    para(d, p, 1100, 12900, 30400, 1400,
         "tty_init → con_init(console.c:683) · rs_init(serial.c:39) · hd_init(hd.c:346, main.c:134) · "
         "floppy_init(floppy.c:460, main.c:135) — 초기화 순서가 곧 IDT가 채워지는 순서다. "
         "17~47은 reserved 로 채운 뒤 45(irq13)·39(parallel)만 덮는다(traps.c:202-207).", 14)

    # 10 _set_gate 매크로 해부
    p = d.slide("_set_gate 매크로 해부", K.S_CODE,
                "include/asm/system.h:22-31 — 8바이트를 eax·edx 두 쌍으로 조립해 그대로 저장")
    d.code_panel(p, "src/include/asm/system.h", 22, 31, 1100, 4150, 19700, 8300, size=12)
    d.text(p, 22000, 4150, 10600, 600, "조립 결과", 16, K.TEAL, True)
    d.text(p, 22000, 5050, 10600, 500, "하이 DWORD = *gate_addr", 12, K.MUTED)
    nbox(d, p, 22000, 5750, 5050, 1700, "오프셋 하위 16", "\"a\"(0x00080000) → eax 상위",
         K.PAPER, s1=13, s2=10)
    nbox(d, p, 27400, 5750, 5300, 1700, "선택자 0x0008", "movw %dx,%ax 로 끼워 넣음",
         K.TEAL, s1=13, s2=10)
    d.text(p, 22000, 7550, 10600, 500, "상위 DWORD = gate_addr+4", 12, K.MUTED)
    nbox(d, p, 22000, 8250, 5050, 1700, "P=1 · DPL · type", "0x8000+(dpl<<13)+(type<<8)",
         K.TEAL, s1=13, s2=10)
    nbox(d, p, 27400, 8250, 5300, 1700, "오프셋 상위 16", "edx 상위 16비트가 그대로",
         K.PAPER, s1=13, s2=10)
    para(d, p, 22000, 10100, 10600, 4700,
         "P 비트 = 1 (0x8000) — 항상 켠다.\nDPL 은 bit 14-13, type 은 bit 11-8.\n\n"
         "asm 제약 \"i\" 로 상수를, \"d\"·\"a\" 로 주소를 전달 — 런타임 계산 없이 "
         "mov 4번으로 게이트가 완성된다.", 14)

    # 11 세 매크로의 차이는 두 숫자뿐
    p = d.slide("세 매크로의 차이는 두 숫자뿐", K.S_CODE,
                "include/asm/system.h:33-40 — (type, DPL) 두 숫자가 게이트의 성격 전부다")
    d.code_panel(p, "src/include/asm/system.h", 33, 40, 1100, 4150, 19700, 8350,
                 size=15)
    d.table(p, 22000, 4250, [4000, 3300, 3300], [
        ["매크로", "type", "DPL"],
        ["set_intr_gate", "14", "0"],
        ["set_trap_gate", "15", "0"],
        ["set_system_gate", "15", "3"],
    ], row_h=1000, size=15)
    para(d, p, 22000, 8700, 10500, 5800,
         "type 14 vs 15 — 진입 시 EFLAGS.IF 를 끄는가(14 = 인터럽트 게이트).\n\n"
         "DPL 0 vs 3 — 사용자 모드(CPL 3)의 int n 을 허용하는가.\n\n"
         "나머지 7바이트는 세 매크로가 완전히 같다.", 15)

    # 12 게이트 설명자 비트 배치
    p = d.slide("상위 워드 값 계산 — 0x8E00·0x8F00·0xEF00", K.S_CODE,
                "boot/head.s:79-84 의 $0x8E00 이 _set_gate 식과 같은 값임을 확인한다")
    d.code_panel(p, "src/boot/head.s", 79, 84, 1100, 4150, 14200, 4900,
                 size=12, caption_extra="head.s:82 — $0x8E00")
    d.table(p, 15900, 4150, [4600, 7500, 4300], [
        ["매크로", "0x8000+(dpl<<13)+(type<<8)", "상위 워드"],
        ["set_intr_gate", "0x8000 + 0 + (14<<8)", "0x8E00"],
        ["set_trap_gate", "0x8000 + 0 + (15<<8)", "0x8F00"],
        ["set_system_gate", "0x8000 + (3<<13) + (15<<8)", "0xEF00"],
    ], row_h=1050, size=13)
    auto_pane(d, p, 1100, 9600, 14200, 4700, "0x8E00 비트 분해 (상위 워드)",
              "0x8E00 = 1000 1110 0000 0000\n"
              "          ^   ^^^^\n"
              "          P=1 DPL=00  type=1110(14)\n"
              "0xEF00 = 1110 1111 … type 15, DPL 3", start=13)
    para(d, p, 15900, 9600, 16600, 4700,
         "head.s:82 는 게이트를 어셈블리 상수로 직접 만든다 — setup_idt 의 256개 "
         "ignore_int 게이트는 전부 (type 14, DPL 0) 인터럽트 게이트.\n\n"
         "같은 식을 C 매크로 _set_gate(10장)가 만든다 — 두 경로가 같은 0x8E00 을 "
         "낸다는 것이 오늘의 확인 포인트.", 15)

    # ── 비교 13–14 ────────────────────────────────────────────
    # 13 게이트 종류 비교
    p = d.slide("비교 ①: IDT에 넣을 수 있는 게이트 종류", K.S_CMP,
                "범위 = IDT 게이트 종류 — kernel/sched.c:409·411 · chr_drv/serial.c:39-43 · blk_drv/hd.c:346-348 · traps.c:181-208 · console.c:683-684 · floppy.c:460-461")
    d.table(p, 1100, 4300, [4600, 9000, 9200, 8700], [
        ["축", "인터럽트 게이트", "트랩 게이트", "태스크 게이트"],
        ["type", "14 (0xE)", "15 (0xF)", "5"],
        ["0.11 사용", "O — IRQ 일부", "O — 예외·0x80·IRQ 일부", "X — 0.11 미사용"],
        ["진입 시 IF", "자동 클리어 (IF=0)", "그대로 유지", "(해당 없음)"],
        ["DPL", "0", "0 또는 3", "—"],
        ["매크로", "set_intr_gate", "set_trap_gate / set_system_gate", "(매크로 없음)"],
        ["사용 예", "0x20 타이머 · 0x2E hd", "예외 0~16 · 0x80", "TSS 전환 — x86 기능만"],
        ["관련 소스", "sched.c:409 · hd.c:346", "traps.c:185 · sched.c:411", "—"],
    ], row_h=1150, size=14)
    para(d, p, 1100, 13300, 31500, 1000,
         "태스크 게이트는 핸들러 진입 대신 TSS 를 갈아끼우는 방식 — 0.11 코드 어디에서도 "
         "쓰지 않는다(\"0.11은 사용 안 함\").", 15)
    d.banner(p, "IF 를 끄느냐(type 14) 유지하느냐(type 15) — 게이트 종류의 차이는 사실 이것 하나다")

    # 14 게이트 DPL 비교
    p = d.slide("비교 ②: 게이트 DPL 0 vs 3", K.S_CMP,
                "범위 = 게이트 DPL — kernel/traps.c:181-208(188-190) · kernel/sched.c:411")
    d.table(p, 1100, 4300, [5300, 13100, 13100], [
        ["항목", "DPL 0", "DPL 3"],
        ["의미", "소프트웨어 int n 을 CPL 0 에서만 허용", "사용자(CPL 3)의 int n 도 허용"],
        ["사용자의 int n", "#GP(13번) → general_protection → die()", "정상 진입"],
        ["0.11의 번호", "대부분의 예외 · 장치 IRQ 전부", "3·4·5 (traps.c:188-190) · 0x80 (sched.c:411)"],
        ["매크로", "set_intr_gate · set_trap_gate", "set_system_gate — 네 개뿐"],
    ], row_h=1500, size=15)
    para(d, p, 1100, 12200, 31500, 2200,
         "set_system_gate 을 쓴 번호는 3(int3)·4(overflow)·5(bounds)·0x80(시스템 콜) 네 개뿐이다 — "
         "trap_init/sched_init 을 처음 끝까지 훑으면 확인된다.\n"
         "주의 — DPL 검사는 소프트웨어 int 명령에만 적용된다. 하드웨어 인터럽트·CPU 예외는 "
         "DPL 과 무관하게 들어온다(§8: \"DPL0이면 장치 인터럽트가 안 들어온다\"는 오해 금지).", 15)

    # ── 코드 15–18 (사용자 쪽) ────────────────────────────────
    # 15 lib/write.c
    p = d.slide("사용자 쪽 출발점 — lib/write.c", K.S_CODE,
                "lib/write.c:7-10 · include/unistd.h:58 (#ifdef __LIBRARY__) — write 라는 함수는 매크로 전개 결과다")
    d.code(p, "src/lib/write.c", 7, 10,
           "7행 #define __LIBRARY__ 가\nunistd.h:58 의 #ifdef 블록을\n연다 — __NR_* 번호와\n"
           "_syscall0~3 매크로가\n드러난다.\n\n"
           "10행 한 줄이 write 함수의\n전부다 — 본문은 없다.\n전개 결과는 다음 장(16).",
           size=15)

    # 16 _syscall3 전개
    p = d.slide("_syscall3 전개 — 손으로 쓴 코드", K.S_CODE,
                "include/unistd.h:172-183 — 매크로와 그 전개 결과를 나란히 놓는다")
    d.code_panel(p, "src/include/unistd.h", 172, 183, 1100, 4150, 19700, 9750, size=12)
    auto_pane(d, p, 22000, 4150, 10600, 9750, "전개 결과 — write(int fd, const char *buf, off_t count)",
              "int write(int fd, const char *buf,\n          off_t count)\n"
              "{\n    long __res;\n"
              "    asm volatile(\"int $0x80\"\n"
              "        : \"=a\"(__res)\n"
              "        : \"0\"(4), \"b\"(fd),\n"
              "          \"c\"(buf), \"d\"(count));\n"
              "    if (__res >= 0)\n"
              "        return (int)__res;\n"
              "    errno = -__res;\n"
              "    return -1;\n"
              "}", start=11)

    # 17 레지스터 약속
    p = d.slide("_syscall3 전개 — 레지스터 약속", K.S_CODE,
                "include/unistd.h:133-144 (_syscall0) — \"0\" 제약이 진입 번호를, \"=a\"가 반환값을 받는다")
    d.code_panel(p, "src/include/unistd.h", 133, 144, 1100, 4150, 19700, 9750, size=12)
    d.table(p, 22000, 4250, [2300, 4000, 4300], [
        ["레지스터", "역할", "write(1,buf,3) 값"],
        ["EAX 진입", "시스템 콜 번호", "__NR_write = 4"],
        ["EBX", "인자 1", "fd = 1"],
        ["ECX", "인자 2", "buf 주소"],
        ["EDX", "인자 3", "count = 3"],
        ["EAX 복귀", "\"=a\"(__res)", "쓴 바이트 수 / 음수"],
    ], row_h=950, size=13)
    para(d, p, 22000, 10400, 10600, 3800,
         "_syscall0 의 \"0\"(__NR_##name) — '0' 제약은 출력 \"=a\" 와 같은 레지스터라는 뜻. "
         "번호를 eax 에 실어 두고 int $0x80.\n\n"
         "반환값이 음수면 errno = -__res 하고 -1 을 돌려준다(0.11 관용구).", 14)

    # 18 __NR_write = 4
    p = d.slide("__NR_write = 4 — 번호와 표의 4번 칸", K.S_CODE,
                "include/unistd.h:60-66 · include/linux/sys.h:74-78 · kernel/system_call.s:61 — 표 길이 72")
    d.code_panel(p, "src/include/unistd.h", 60, 66, 1100, 4150, 15200, 5500,
                 size=12, caption_extra="번호 정의 — 0~6")
    d.code_panel(p, "src/include/linux/sys.h", 74, 78, 16900, 4150, 15700, 5500,
                 size=12, caption_extra="fn_ptr sys_call_table[]")
    for i, (nr, fn) in enumerate([("0", "sys_setup"), ("1", "sys_exit"),
                                  ("2", "sys_fork"), ("3", "sys_read"),
                                  ("4", "sys_write")]):
        bx = 1100 + i * 6200
        hot = nr == "4"
        nbox(d, p, bx, 10200, 5700, 1700, f"[{nr}] {fn}",
             "__NR 쪽 == 표쪽" if not hot else "오늘의 길 — sys_call_table[4]",
             K.ORANGE if hot else None, K.INK if hot else K.INK, s1=14, s2=11)
        if i < 4:
            arrow(d, p, bx + 5800, 10700, "→", 20)
    para(d, p, 1100, 12250, 31500, 2700,
         "system_call.s:61 nr_system_calls = 72 — 표 길이는 0~71, 마지막은 sys_setregid(71, unistd.h:131).\n"
         "양쪽 순서가 어긋나면 번호가 다른 함수를 부르게 된다 — 번호 체계는 커널과 라이브러리의 약속이다.\n"
         "72 이상의 번호는 bad_sys_call 로 간다(22장).", 15)

    # 19 int $0x80 실행 순간 (배경)
    p = d.slide("int $0x80 실행 순간 CPU가 하는 일", K.S_BG,
                "kernel/system_call.s:17-31(주석) · kernel/sched.c:411 — 트랩 게이트라 IF 는 유지된다")
    d.flow(p, [
        ("① IDT[0x80] 읽기", "0x80*8 위치의\n8바이트 게이트"),
        ("② 권한 검사", "DPL 3 ≥ CPL 3 —\n통과 (14장)"),
        ("③ TSS 로드", "ss0 = 0x10 ·\nesp0 = tss.esp0"),
        ("④ 5개 push", "SS·ESP·EFLAGS\nCS·EIP — 순서 주목"),
        ("⑤ CS·EIP 교체", "CS=0x08 ·\nEIP=_system_call"),
    ], y=4500, h=3500)
    nbox(d, p, 1100, 8300, 15200, 1600, "스택이 바뀐다 — 사용자 스택 → 커널 스택",
         "ESP = tss.esp0 — 태스크 구조체가 있는 페이지의 끝(05회차 예고)", K.ORANGE, s1=16, s2=13)
    nbox(d, p, 17500, 8300, 15100, 1600, "트랩 게이트라 IF 는 그대로",
         "인터럽트 게이트였다면 여기서 IF=0 (13장 비교)", None, K.TEAL, s1=16, s2=13)
    para(d, p, 1100, 10300, 31500, 3600,
         "int $0x80 은 \"특별한 call\"이 아니다(§8) — 스택·CPL·세그먼트가 모두 바뀐다.\n"
         "CPU가 push 하는 5개(SS·ESP·EFLAGS·CS·EIP)는 iret 가 되돌릴 목록 그 자체다. "
         "순서는 하드웨어가 정한다 — 소프트웨어는 결정 못 한다.\n"
         "이 순간 커널에 있는 정보는 \"누가 어디서 왔는가\"뿐 — 나머지 레지스터는 진입 코드가 직접 저장한다(20·22장).", 15)
    d.banner(p, "여기까지가 하드웨어가 하는 일 — 다음부터는 system_call.s 의 코드가 하는 일")

    # 20 프레임 그림
    p = d.slide("프레임 그림 — ret_from_sys_call 시점의 12 슬롯", K.S_CODE,
                "kernel/system_call.s:17-31 주석 그대로 · 오프셋 정의 35-53 — 37장 GDB x/12xw $esp 와 대조한다")
    d.text(p, 1100, 4050, 9800, 500, "CPU가 push (int $0x80 — 19장 ④)", 13, K.TEAL, True)
    slots = [("0x2C  OLDSS — 커널에 들어오기 직전 SS = 0x17", K.TEAL),
             ("0x28  OLDESP — 사용자 스택 포인터", K.TEAL),
             ("0x24  EFLAGS — IF 포함 · 트랩 게이트라 유지", K.TEAL),
             ("0x20  CS — 0x0f · 하위 2비트 3 = 왔던 곳 CPL", K.TEAL),
             ("0x1C  EIP — int $0x80 다음 명령", K.TEAL),
             ("0x18  DS — push 83 · 사용자 DS(0x17) 값", K.PAPER),
             ("0x14  ES — push 84", K.PAPER),
             ("0x10  FS — push 85 · 사용자 데이터 접근용", K.PAPER),
             ("0x0C  EDX — push 86 · count", K.PAPER),
             ("0x08  ECX — push 87 · buf", K.PAPER),
             ("0x04  EBX — push 88 · fd", K.PAPER),
             ("0x00  EAX — pushl %eax 95 · sys_write 반환값", K.ORANGE)]
    for i, (t, col) in enumerate(slots):
        y = 4600 + i * 730
        nbox(d, p, 1100, y, 9800, 680, t, None, col, K.INK, s1=12)
    d.code_panel(p, "src/kernel/system_call.s", 35, 46, 21500, 4300, 11100, 8350,
                 size=10, caption_extra="오프셋 심볼 정의")
    para(d, p, 21500, 13000, 11100, 1300,
         "OLDESP = 0x28 · OLDSS = 0x2C — ret_from_sys_call(105-108)가 이 두 값을 검사해 "
         "\"사용자에서 왔는가\"를 판단한다.", 13)

    # ── 상태도 21 ─────────────────────────────────────────────
    # 21 상태 변화도
    p = d.slide("상태 변화도 — 한 번의 시스템 콜", K.S_STATE,
                "kernel/system_call.s:80-128 · fs/read_write.c:83-103 — 유지 조건: IF 유지 · 커널 스택 = 태스크 페이지 끝")
    states1 = [("① 사용자 실행", "CPL 3 · CS 0x0f · SS 0x17\nwrite() stub — 사용자 스택", K.MUTED, None),
               ("② 커널 진입 프레임", "CPL 0 · CS 0x08 · SS 0x10\nESP=tss.esp0 · 레지스터 미저장", K.ORANGE, None),
               ("③ C 호출 가능", "DS·ES = 0x10 · FS = 0x17\npush 6개 완료 (83-88)", K.PAPER, None),
               ("④ sys_write 실행 중", "ebx·ecx·edx = fd·buf·count\nEAX = 반환값", K.PAPER, None)]
    for i, (t, sub, fill, edge) in enumerate(states1):
        x = 1100 + i * 8050
        nbox(d, p, x, 4350, 7250, 2150, t, sub, fill,
             K.INK if fill != K.MUTED else K.MUTED, edge, s1=15, s2=11)
        if i < 3:
            arrow(d, p, x + 7300, 4900, "→", 22, K.ORANGE, w=700)
    d.text(p, 1800, 6600, 7000, 500, "int $0x80 (unistd.h:177)", 11, K.ORANGE, True)
    d.text(p, 9900, 6600, 7000, 500, "push ds es fs edx ecx ebx", 11, K.ORANGE, True)
    d.text(p, 17900, 6600, 7300, 500, "call _sys_call_table(,eax,4)", 11, K.ORANGE, True)
    states2 = [("⑥ 사용자 실행 복귀", "CS 0x0f · SS 0x17 · ESP 복원\nEAX = 쓴 바이트 수", K.TEAL, None),
               ("⑤ ret_from_sys_call", "시그널 검사(109-120) · EAX 슬롯 확정(95)\npop 7개 직전(121)", K.PAPER, None)]
    for i, (t, sub, fill, edge) in enumerate(states2):
        x = 5100 + i * 14000
        nbox(d, p, x, 7250, 13500, 1800, t, sub, fill, K.INK, edge, s1=15, s2=11)
    arrow(d, p, 29000, 6450, "↓", 24, K.ORANGE, w=900, h=800)
    d.text(p, 17600, 9150, 15000, 500,
           "ret (sys_write 복귀) · pushl %eax (95) · 96-100 검사", 12,
           K.ORANGE, True)
    arrow(d, p, 18300, 7700, "←", 24, K.ORANGE, w=900, h=800)
    d.text(p, 5300, 9250, 12000, 500, "pop 7개 + iret (121-128)", 11, K.ORANGE, True)
    d.table(p, 1100, 10000, [4600, 9300, 9300, 8300], [
        ["전환", "원인 명령 (소스:줄)", "바뀌는 데이터", "유지 조건"],
        ["①→②", "int $0x80 — unistd.h:177", "CS·SS·ESP·CPL + 5 push", "IF 유지 · 커널 스택 = tss.esp0"],
        ["②→③", "push 6개 — system_call.s:83-88", "ESP −24B · 슬롯 6개", "CPL 0 · FS=0x17 사용자 데이터"],
        ["③↔④", "call(94) / ret", "EIP — C 함수 진입·복귀", "eax = 반환값 → pushl %eax(95)"],
        ["⑤→⑥", "pop 7개 + iret (121-128)", "EIP·CS·EFLAGS·ESP·SS 복원", "범용 레지스터 중 EAX만 새 값"],
    ], row_h=950, size=13)

    # ── 코드 22–26 (커널 쪽) ──────────────────────────────────
    # 22 _system_call (1)
    p = d.slide("_system_call 한 줄씩 (1) — 80-94", K.S_CODE,
                "kernel/system_call.s:80-94 · bad_sys_call(72-74) — 15줄 전체")
    d.code(p, "src/kernel/system_call.s", 80, 94,
           "81-82  eax > 71 → bad_sys_call\n  (72-74: eax=-1, iret)\n\n"
           "83-88  push ds es fs edx ecx ebx\n  — ebx·ecx·edx가 C 인자\n\n"
           "89-93  ds=es=0x10 · fs=0x17\n\n"
           "94  call _sys_call_table(,%eax,4)\n  = sys_call_table[eax]()", 17)

    # 23 sys_write 도착
    p = d.slide("sys_write 에 도착 — 도착지 분기만 본다", K.S_CODE,
                "fs/read_write.c:83-103 · fs/char_dev.c:95 (rw_char) — 내부는 13회차, 오늘은 \"도착했다\"까지")
    d.code_panel(p, "src/fs/read_write.c", 83, 94, 1100, 4150, 19700, 9050,
                 size=11, caption_extra="인자 = 스택의 ebx·ecx·edx")
    d.code_panel(p, "src/fs/read_write.c", 95, 103, 22000, 4150, 10600, 6700,
                 size=10, caption_extra="장치 종류별 분기")
    para(d, p, 22000, 11100, 10600, 3200,
         "fd 1 → current->filp[1] → 콘솔 inode → S_ISCHR → rw_char(WRITE, …)(95-96).\n\n"
         "반환값은 그대로 eax 로 돌아간다 — _system_call 의 call 다음 줄(95)로.", 14)
    d.banner(p, "오늘은 \"sys_call_table[4] 의 그 함수에 도착했다\"까지만 — pipe·char·blk·reg 4갈래는 각 회차에서")

    # 24 _system_call (2)
    p = d.slide("_system_call 한 줄씩 (2) — 95-100", K.S_CODE,
                "kernel/system_call.s:95-100 · reschedule(76-78) — 05회차 스케줄링으로 이어지는 갈림길")
    d.code_panel(p, "src/kernel/system_call.s", 95, 100, 1100, 4150, 19700, 5900,
                 size=13, caption_extra="반환값 저장 · 재스케줄 검사")
    d.code_panel(p, "src/kernel/system_call.s", 72, 78, 22000, 4150, 10600, 5850,
                 size=11, caption_extra="bad_sys_call · reschedule")
    para(d, p, 22000, 10300, 10600, 3800,
         "95  pushl %eax — 반환값을 프레임\n EAX 슬롯(20장)에 보관\n\n"
         "96-100  state≠0 또는 counter==0\n → reschedule : ret_from_sys_call\n 주소를 push 하고 jmp _schedule", 14)
    para(d, p, 1100, 10400, 19700, 3600,
         "reschedule(76-78)의 뜻 — schedule() 이 돌아오면(05회차 switch_to) ret_from_sys_call 부터 계속한다. "
         "돌아오는 태스크가 내가 아닐 수 있다는 점이 05회차의 핵심 질문이다. 오늘은 이 갈림길의 존재만 기억한다.", 15)

    # 25 ret_from_sys_call
    p = d.slide("ret_from_sys_call — 시그널 검사 후 복귀", K.S_CODE,
                "kernel/system_call.s:101-128 · do_signal(kernel/signal.c:82) — 시그널 상세는 10회차")
    d.code_panel(p, "src/kernel/system_call.s", 101, 114, 1100, 4150, 15200, 8700,
                 size=9, caption_extra="검사 — task[0]·CS·OLDSS·시그널")
    d.code_panel(p, "src/kernel/system_call.s", 115, 128, 16900, 4150, 15700, 8700,
                 size=9, caption_extra="do_signal 호출 · pop 7 · iret")
    para(d, p, 1100, 13100, 31500, 1200,
         "102-104 task[0] 은 시그널 없음 · 105-108 CS=0x0f·OLDSS=0x17 — \"사용자에서 왔을 때만\" 시그널 처리 · "
         "109-120 signal & ~blocked 최하위 비트 → do_signal(10회차) · 121-128 pop 7개 → iret", 14)

    # 26 iret
    p = d.slide("iret 가 되돌리는 것 — 그리고 되돌리지 않는 것", K.S_CODE,
                "kernel/system_call.s:121-128 · include/unistd.h:172-183(\"=a\") — 1회차 노트와 일관")
    d.code_panel(p, "src/kernel/system_call.s", 121, 128, 1100, 4150, 19700, 7400,
                 size=13, caption_extra="pop 7개 → iret")
    nbox(d, p, 22000, 4150, 10600, 1900, "코드가 먼저 pop (121-127)",
         "eax·ebx·ecx·edx·fs·es·ds — iret 는 범용 레지스터를 복원하지 않으므로", None, K.TEAL, s1=14, s2=12)
    nbox(d, p, 22000, 6300, 10600, 1900, "iret (128) 가 pop",
         "EIP·CS·EFLAGS — CPL 이 바뀌므로 OLDESP·OLDSS 까지 5개", None, K.TEAL, s1=14, s2=12)
    nbox(d, p, 22000, 8450, 10600, 1900, "EAX — 유일하게 새 값",
         "sys_write 반환값 → \"=a\"(__res) → __res · 음수면 errno=-__res", K.ORANGE, s1=14, s2=12)
    d.banner(p, "iret 가 복원하는 것은 5개뿐 — 그래서 pop 이 먼저다 · EAX 만은 결과를 싣고 사용자로 돌아간다")

    # ── 비교 27 ───────────────────────────────────────────────
    # 27 저장 코드 4종 비교
    p = d.slide("비교 ③: 진입 직후 레지스터 저장 코드 4종", K.S_CMP,
                "범위 = IDT 진입 직후 저장 코드 — system_call.s:80-94·176-183 · asm.s:19-39·97-117 · mm/page.s:14-27")
    d.table(p, 1100, 4200, [5900, 9800, 8200, 7600], [
        ["경로", "push 목록", "호출 규약", "복귀"],
        ["_system_call\n(80-94)", "ds es fs edx ecx ebx\n(eax는 95에서 반환값 슬롯)", "call _sys_call_table(,eax,4)", "95-100 검사 후\nret_from_sys_call"],
        ["_timer_interrupt\n(176-183)", "ds es fs edx ecx ebx eax\n— 7개 전부", "call _do_timer(CPL)", "jmp ret_from_sys_call"],
        ["asm.s no_error_code\n(19-39)", "ebx ecx edx edi esi ebp\nds es fs + 가짜 오류 코드 0", "call *%eax →\ndo_xxx(esp, 0)", "자체 pop 9개 + iret"],
        ["asm.s error_code\n(97-117)", "xchgl 로 오류 코드↔eax\nebx(함수) ecx edx edi esi ebp\nds es fs + 오류 코드", "call *%ebx →\ndo_xxx(esp, error_code)", "자체 pop + iret"],
        ["mm/page.s _page_fault\n(14-27)", "xchgl 오류 코드↔eax\necx edx ds es fs + CR2(edx)", "call do_no_page /\ndo_wp_page(ec, addr)", "자체 pop + iret"],
    ], row_h=1850, size=13)
    para(d, p, 1100, 15600, 31500, 1000,
         "시스템 콜·타이머는 ret_from_sys_call 공용 복귀 — 나머지는 자체 pop+iret (시그널 검사 없음, 파일 상단 NOTE 참조).", 13)

    # ── 코드 28–33 (예외·타이머) ──────────────────────────────
    # 28 trap_init
    p = d.slide("trap_init — 예외 0~16 게이트 등록", K.S_CODE,
                "kernel/traps.c:185-201 · 202-207(reserved→45·39) · 7번 진입은 system_call.s:148 · 14번은 mm/page.s")
    d.code_panel(p, "src/kernel/traps.c", 185, 201, 1100, 4150, 19700, 10250, size=9)
    d.table(p, 22000, 4250, [1900, 4400, 4100], [
        ["번호", "핸들러", "게이트"],
        ["0", "divide_error", "trap"],
        ["3·4·5", "int3·overflow·bounds", "system (DPL3)"],
        ["7", "device_not_available", "trap — sys_call.s:148"],
        ["13", "general_protection", "trap"],
        ["14", "page_fault", "trap — mm/page.s"],
        ["16", "coprocessor_error", "trap"],
        ["17~47", "reserved · 45·39만", "trap (202-207)"],
    ], row_h=900, size=12)
    para(d, p, 22000, 11900, 10600, 2300,
         "예외는 전부 트랩 게이트(type 15, DPL 0) — 0x80 과 같은 종류, 다른 DPL.\n"
         "3·4·5만 set_system_gate — 사용자가 int3 등을 직접 쓸 수 있다(14장).", 14)

    # 29 no_error_code
    p = d.slide("오류 코드 없는 예외 — no_error_code 공통 경로", K.S_CODE,
                "kernel/asm.s:19-51 — 0·1·2·3·4·5·6·7·9·16이 이쪽 · pushl $0 로 프레임 모양을 맞춘다")
    d.code_panel(p, "src/kernel/asm.s", 19, 34, 1100, 4150, 19700, 9750,
                 size=9, caption_extra="_divide_error 진입 + 저장")
    d.code_panel(p, "src/kernel/asm.s", 35, 45, 22000, 4150, 10600, 7150,
                 size=9, caption_extra="세그먼트 교체 · C 핸들러 호출")
    para(d, p, 22000, 11600, 10600, 2700,
         "20행 pushl $_do_divide_error —\n핸들러 주소를 스택에 실은 뒤\n22행 xchgl 로 eax 와 맞바꾼다.\n\n"
         "32행 pushl $0 — 가짜 오류 코드.\n40행 addl $8,%esp 로 두 개 제거,\n46-51 pop 역순 + iret — 완전 복원.", 13)

    # 30 error_code
    p = d.slide("오류 코드 있는 예외 — error_code 공통 경로", K.S_CODE,
                "kernel/asm.s:97-129 · traps.c:87-100 — 8·10·11·12·13·14이 이쪽 · do_xxx(esp, error_code)")
    d.code_panel(p, "src/kernel/asm.s", 97, 112, 1100, 4150, 19700, 9750,
                 size=9, caption_extra="_double_fault 진입 + 저장")
    d.code_panel(p, "src/kernel/asm.s", 113, 125, 22000, 4150, 10600, 8200,
                 size=9, caption_extra="세그먼트 교체 · 호출 · pop")
    para(d, p, 22000, 12700, 10600, 1700,
         "126-128 popl %ebx·%eax, 129 iret.\n100행 xchgl %eax,4(%esp) — CPU가 push 한 오류 코드를 eax 로.\n"
         "111행 lea 44(%esp) — 두 경로 모두 esp 포인터를 둘째 인자로 넘긴다.", 12)

    # 31 die()
    p = d.slide("die() — 예외의 끝", K.S_CODE,
                "kernel/traps.c:63-85 · do_exit(11) — esp[0..4] = EIP·CS·EFLAGS·ESP·SS (20장 상위 5슬롯과 동일 배치)")
    d.code_panel(p, "src/kernel/traps.c", 63, 74, 1100, 4150, 19700, 8350,
                 size=10, caption_extra="68-70 printk — 출력 형식")
    d.code_panel(p, "src/kernel/traps.c", 75, 85, 22000, 4150, 10600, 7150,
                 size=9, caption_extra="스택 덤프 · 종료")
    para(d, p, 22000, 11600, 10600, 3000,
         "출력 순서가 프레임 배치 그 자체다 —\nEIP: 000f:… · ESP: 0017:… (41장 캡처와 대조).\n"
         "마지막 do_exit(11) — 프로세스 종료,\n셸 프롬프트로 돌아온다.", 13)
    d.banner(p, "die() 의 printk 가 읽는 esp[0..4] 는 CPU가 push 한 5워드 — 20장 그림의 위쪽 절반")

    # 32 타이머·PIC 설정
    p = d.slide("하드웨어 인터럽트 — 타이머와 PIC 설정", K.S_CODE,
                "kernel/sched.c:406-410 · LATCH = 1193180/HZ (sched.c:46) — 392-405 TSS·LDT 설정은 05회차")
    d.code(p, "src/kernel/sched.c", 406, 410,
           "406  포트 0x43 — 채널 0,\n 모드 3(사각파) 지정\n\n"
           "407-408  LATCH 값 LSB·MSB\n → 포트 0x40 — 100Hz\n\n"
           "409  set_intr_gate(0x20,\n &timer_interrupt)\n\n"
           "410  IRQ0 마스크 해제\n outb(inb_p(0x21)&~0x01,0x21)")
    d.code_panel(p, "src/kernel/sched.c", 45, 47, 1100, 10400, 19700, 3500,
                 size=12, caption_extra="LATCH 정의 — sched.c:46")
    d.banner(p, "set_intr_gate(0x20) — 인터럽트 게이트라 진입 순간 IF=0 · 이 인터럽트가 05회차 스케줄러의 심장이다")

    # 33 _timer_interrupt
    p = d.slide("_timer_interrupt 한 줄씩", K.S_CODE,
                "kernel/system_call.s:176-197 — 상세(do_timer·schedule)는 05회차 · 오늘은 진입·복귀만")
    d.code_panel(p, "src/kernel/system_call.s", 176, 188, 1100, 4150, 19700, 8950,
                 size=10, caption_extra="저장 7개 — eax까지")
    d.code_panel(p, "src/kernel/system_call.s", 189, 197, 22000, 4150, 10600, 6700,
                 size=10, caption_extra="jiffies · EOI · do_timer")
    para(d, p, 22000, 11200, 10600, 3200,
         "189  incl _jiffies — 틱 카운터\n"
         "190-191  EOI — 포트 0x20 에 0x20, PIC 에 \"처리 끝\" 통보\n"
         "192-194  CS(%esp) 하위 2비트 = CPL 을 do_timer 인자로\n"
         "197  jmp ret_from_sys_call — 시스템 콜과 같은 복귀 길", 11)
    d.banner(p, "타이머도 시스템 콜도 ret_from_sys_call 로 나간다 — system_call.s 파일 주석(NOTE)이 그 이유를 말한다")

    # ── 시연·캡처 34–42 ───────────────────────────────────────
    # 34 시연 환경
    p = d.slide("시연 환경 — lab/ QEMU + GDB", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 (TCG) · GDB 원격 — 슬라이드 줄 번호는 src/ 기준, 심볼은 lab 빌드 기준(§8)")
    auto_pane(d, p, 1100, 4150, 19700, 10250, "GDB — 환경 준비",
              "# QEMU를 -s -S (gdbstub, 시작 정지)로 기동\n"
              "qemu-system-i386 -s -S [lab/ 실행 스크립트]\n"
              "\n"
              "# 다른 터미널에서 GDB — 커널 심볼 로드 후 연결\n"
              "(gdb) target remote :1234\n"
              "(gdb) file tools/system\n"
              "(gdb) c            # 부팅 → 셸 프롬프트까지\n"
              "\n"
              "# 셸이 뜬 뒤 중단점 설정\n"
              "(gdb) info functions system_call\n"
              "# lab 심볼 확인 — _ 접두 유무는 빌드 기준\n"
              "(gdb) b system_call", start=13)
    para(d, p, 22000, 4150, 10600, 10250,
         "규칙(§8)\n\n"
         "· 캡처·심볼은 lab/ 기준, 슬라이드 코드 인용은 src/ 원본 기준 — 섞지 않는다.\n\n"
         "· src/ 줄 번호와 lab/ 빌드의 줄 번호는 다를 수 있다.\n\n"
         "· 시연 전 info functions system_call 으로 심볼명(_system_call 등)을 확인한다.\n\n"
         "· gdbstub 에서 $cs·$ss·$esp 노출이 안 되면 monitor info registers 로 대체(§11).\n\n"
         "실패 시 — 사전 캡처 build/04-A-frame.png 로 대체한다.", 14)

    # 35 시연 A
    p = d.slide("시연 A: break system_call — 진입 직후", K.S_DEMO,
                "kernel/system_call.s:80-94 — 셸의 내부 동작상 write 이전 다른 시스템 콜이 먼저 걸릴 수 있다 → cond")
    auto_pane(d, p, 1100, 4150, 19700, 10250, "GDB — 시연 A",
              "(gdb) b system_call\n"
              "(gdb) c\n"
              "# 게스트 셸에서 echo hi 입력 → 정지\n"
              "Breakpoint 1, system_call () at kernel/system_call.s:80\n"
              "\n"
              "# 다른 콜이 먼저 걸리면 조건 부여\n"
              "(gdb) cond 1 $eax == 4\n"
              "(gdb) c\n"
              "\n"
              "(gdb) p/x $eax    # 0x4  = __NR_write\n"
              "(gdb) p/x $ebx    # 0x1  = fd (stdout)\n"
              "(gdb) p/x $ecx    # buf — 사용자 선형 주소\n"
              "(gdb) p/x $edx    # 3    = \"hi\\n\" 길이\n"
              "(gdb) p/x $cs     # 0x8  — CPL 0\n"
              "(gdb) p/x $ss     # 0x10 — 커널 스택", start=13)
    para(d, p, 22000, 4150, 10600, 10250,
         "관찰 포인트\n\n"
         "· EAX = 4 — 17장 레지스터 약속 실측\n"
         "· EBX = 1, ECX = buf, EDX = 3\n\n"
         "· CS = 0x8 — 이미 커널(CPL 0)\n"
         "· SS = 0x10 — 스택도 커널 것\n"
         " (19장 ③④의 결과)\n\n"
         "· 진입 첫 명령(81행) 실행 전 —\n push 는 아직 없다\n\n"
         "기대 화면은 다음 장(36).", 14)

    # 36 캡처 A-1
    p = d.slide("캡처 A-1: 진입 직후 레지스터", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 주솟값은 부팅마다 다름(예시)")
    d.placeholder_output(p, 1100, 4150, 19700, 10250,
                         "(gdb) c            # 게스트 셸: echo hi\n"
                         "Breakpoint 1, system_call () at kernel/system_call.s:80\n"
                         "(gdb) p/x $eax\n"
                         "$1 = 0x4          # __NR_write (unistd.h:64)\n"
                         "(gdb) p/x $ebx\n"
                         "$2 = 0x1          # fd = 1 (stdout)\n"
                         "(gdb) p/x $ecx\n"
                         "$3 = 0x83f4a0     # buf — 사용자 선형 주소(예시)\n"
                         "(gdb) p/x $edx\n"
                         "$4 = 0x3          # \"hi\\n\"\n"
                         "(gdb) p/x $cs\n"
                         "$5 = 0x8          # 커널 코드 — CPL 0\n"
                         "(gdb) p/x $ss\n"
                         "$6 = 0x10         # 커널 스택 세그먼트",
                         "01-a1-entry-registers.png")
    para(d, p, 22000, 4150, 10600, 10250,
         "관찰 대상(§5)\n\n"
         "· EAX = 4 = __NR_write\n"
         "· EBX = 1 — write(1, …) 의 첫 인자\n"
         "· ECX = 버퍼 주소 — 사용자 선형 주소\n"
         "· EDX = 길이 3\n\n"
         "17장 레지스터 약속 표의 실측.\n\n"
         "CS = 0x8·SS = 0x10 — int $0x80 이\n 이미 일어났다는 증거(19장).", 14)

    # 37 캡처 A-2
    p = d.slide("캡처 A-2: x/5xw $esp — CPU가 쌓은 5워드", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 20장 프레임 그림의 위쪽 5슬롯과 병치")
    d.placeholder_output(p, 1100, 4150, 19700, 10250,
                         "(gdb) x/5xw $esp\n"
                         "0x1e4fc: 0x00000e5a   # EIP — int $0x80 다음 명령\n"
                         "0x1e500: 0x0000000f   # CS — 0x0f = LDT 코드\n"
                         "0x1e504: 0x00000202   # EFLAGS — IF=1 유지\n"
                         "0x1e508: 0x000fc38    # OLDESP — 사용자 스택\n"
                         "0x1e50c: 0x00000017   # OLDSS — 0x17 = LDT 스택",
                         "02-a2-stack-5words.png")
    d.text(p, 22000, 4150, 10600, 600, "20장 그림 — 위쪽 5슬롯", 15, K.TEAL, True)
    for i, (t, sub, col) in enumerate([
            ("0x2C OLDSS = 0x17", "사용자 스택 세그먼트", K.TEAL),
            ("0x28 OLDESP", "사용자 스택 포인터", K.TEAL),
            ("0x24 EFLAGS", "IF=1 — 트랩 게이트", K.TEAL),
            ("0x20 CS = 0x0f", "하위 2비트 3 = CPL 3", K.ORANGE),
            ("0x1C EIP", "int $0x80 다음 명령", K.TEAL)]):
        nbox(d, p, 22000, 4900 + i * 780, 10600, 700, t, sub, col, K.INK, s1=13, s2=10)
    para(d, p, 22000, 9000, 10600, 5300,
         "CS 하위 2비트 = 3 — \"왔던 곳의 CPL\".\nret_from_sys_call(105-108)가 검사하는 바로 그 값이다.\n\n"
         "IF=1 — 트랩 게이트라 진입 시 꺼지지 않았다(13장 비교의 실측).\n\n"
         "이 5워드는 iret 가 되돌릴 목록 그 자체(26장).", 14)

    # 38 시연 B
    p = d.slide("시연 B: sys_write 반환과 ret_from_sys_call", K.S_DEMO,
                "fs/read_write.c:83-103 · kernel/system_call.s:95·101-128 — 12슬롯 전체와 iret 통과")
    auto_pane(d, p, 1100, 4150, 19700, 10250, "GDB — 시연 B",
              "(gdb) b sys_write\n"
              "(gdb) c            # 셸: echo hi\n"
              "Breakpoint 2, sys_write (fd=1, buf=0x83f4a0, count=3)\n"
              "    at fs/read_write.c:83\n"
              "(gdb) finish\n"
              "Value returned is $7 = 3     # 쓴 바이트 수\n"
              "\n"
              "(gdb) b ret_from_sys_call\n"
              "(gdb) c\n"
              "(gdb) x/12xw $esp   # 첫 워드 = EAX 슬롯 = 3\n"
              "\n"
              "# stepi 반복으로 iret(128) 통과 직후\n"
              "(gdb) p/x $cs     # 0x0f\n"
              "(gdb) p/x $ss     # 0x17\n"
              "(gdb) p/x $esp    # 사용자 스택 복귀\n"
              "(gdb) p/x $eax    # 3 — 그대로", start=13)
    para(d, p, 22000, 4150, 10600, 10250,
         "절차\n\n"
         "1. b sys_write → finish —\n 반환값 확인\n"
         "2. b ret_from_sys_call →\n x/12xw $esp — 20장 12슬롯 실측\n"
         "3. stepi 로 iret 통과 —\n CS·SS·ESP 변화 관찰\n\n"
         "관찰 포인트\n\n"
         "· 12워드 중 첫 워드(EAX 슬롯)\n = 쓴 길이\n"
         "· iret 후 CS=0xf·SS=0x17,\n EAX 불변(26장)\n\n"
         "기대 화면은 다음 장(39).", 14)

    # 39 캡처 B
    p = d.slide("캡처 B: iret 직전·직후", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 변한 것: CS·SS·ESP·EIP · 안 변한 것: EAX")
    d.placeholder_output(p, 1100, 4150, 15200, 10250,
                         "# iret 직전 (pop 7개 완료 후)\n"
                         "(gdb) p/x $cs\n"
                         "$8 = 0x8        # 아직 커널\n"
                         "(gdb) p/x $ss\n"
                         "$9 = 0x10\n"
                         "(gdb) p/x $esp\n"
                         "$10 = 0x1e4fc   # 커널 스택\n"
                         "(gdb) p/x $eax\n"
                         "$11 = 0x3       # 반환값",
                         "03-b1-before-iret.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10250,
                         "# stepi … iret 통과 직후\n"
                         "(gdb) p/x $cs\n"
                         "$12 = 0xf       # 사용자 코드\n"
                         "(gdb) p/x $ss\n"
                         "$13 = 0x17      # 사용자 스택\n"
                         "(gdb) p/x $esp\n"
                         "$14 = 0xfc38    # 사용자 스택\n"
                         "(gdb) p/x $eax\n"
                         "$15 = 0x3       # 불변 — 결과",
                         "04-b2-after-iret.png")
    para(d, p, 1100, 14600, 31500, 1600,
         "왕복이 닫혔다 — write(1, …) 가 int $0x80 으로 들어가 sys_write 를 지나 iret 로 돌아왔다. "
         "EAX 의 3 이 stub 의 __res 가 된다(16장 전개 코드 마지막 줄).", 14)

    # 40 시연 C
    p = d.slide("시연 C: 예외 — 0으로 나누기 (#DE)", K.S_DEMO,
                "kernel/asm.s:19-51 · kernel/traps.c:87-100 — lab에 div0 이 없으면 시연 생략, 캡처(41)로 설명")
    auto_pane(d, p, 1100, 4150, 19700, 10250, "GDB — 시연 C",
              "# lab 루트 이미지의 div0 실행 (또는 셸에서 재현)\n"
              "# ./div0\n"
              "\n"
              "(gdb) b do_divide_error\n"
              "(gdb) c\n"
              "Breakpoint 3, do_divide_error (esp=0x1e4c0,\n"
              "    error_code=0) at kernel/traps.c:97\n"
              "\n"
              "# no_error_code 가 만든 프레임 관찰\n"
              "(gdb) p/x ((long*)$esp)[1]   # = die 의 esp_ptr\n"
              "(gdb) x/5xw ((long*)$esp)[1]\n"
              "# EIP · CS(0x0f) · EFLAGS · ESP · SS(0x17)\n"
              "\n"
              "(gdb) c   # die() 출력 → do_exit(11) → 셸 복귀", start=13)
    para(d, p, 22000, 4150, 10600, 10250,
         "절차\n\n"
         "1. 사용자 프로그램으로 #DE 유발\n"
         "2. b do_divide_error — C 핸들러\n"
         "3. 두 번째 인자 esp — 29장 lea 44(%esp)\n 가 가리킨 바로 그 프레임\n"
         "4. 콘솔 die() 출력과 대조(41장)\n\n"
         "관찰 포인트\n\n"
         "· error_code = 0 — 가짜(29장 32행)\n"
         "· EIP 세그먼트 0x0f·SS 0x17 —\n 사용자에서 온 예외\n"
         "· 이후 do_exit(11) — 프로세스 종료", 14)

    # 41 캡처 C
    p = d.slide("캡처 C: divide error: 0000", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음(테스트 프로그램 div0 은 lab 추가분 — 원본 src 에 없음) · 캡처 날짜")
    d.placeholder_output(p, 1100, 4150, 19700, 10250,
                         "divide error: 0000\n"
                         "EIP:    000f:000012a4\n"
                         "EFLAGS: 00000202\n"
                         "ESP:    0017:000fc20\n"
                         "fs: 0017\n"
                         "base: 00000000, limit: 0009ffff\n"
                         "Stack: 00687300 6f6e2f2e ...\n"
                         "Pid: 8, process nr: 4\n"
                         "30 36 00 00 00 00 00 00 00 00\n"
                         "# 이후 do_exit(11) — 셸 프롬프트 복귀",
                         "05-c-divide-error-console.png")
    para(d, p, 22000, 4150, 10600, 10250,
         "관찰 대상(§5)\n\n"
         "· \"divide error: 0000\" — traps.c:68\n printk(\"%s: %04x\", …)\n"
         "· EIP 세그먼트 000f — 사용자\n 코드(하위 2비트 3 = CPL 3)\n"
         "· ESP 세그먼트 0017 — 사용자\n 스택\n\n"
         "31장 die() 68-70 출력 형식과\n 정확히 같은 배치 — esp[0..4].\n\n"
         "테스트 프로그램은 lab 추가분임을\n 각주로 밝힌다(§11).", 14)

    # 42 관찰 vs 추론
    p = d.slide("관찰 vs 추론 — 오늘 시연의 경계", K.S_DEMO,
                "캡처 각주 5항목 재확인 — lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜")
    qbox(d, p, 1100, 4150, 15400, 10250, "관찰 — lab/ 캡처에서 본 것",
         "· 진입 직후 EAX=4·EBX=1·CS=0x8·SS=0x10 (A-1)\n"
         "· 스택 5워드 — EIP·CS=0xf·EFLAGS·OLDESP·OLDSS=0x17 (A-2)\n"
         "· 12워드 전체와 EAX 슬롯 = 반환값 (B)\n"
         "· iret 전후 — CS 0x8→0xf · SS 0x10→0x17 · ESP 교체, EAX 불변 (B)\n"
         "· 콘솔 \"divide error: 0000\" · EIP: 000f:… · ESP: 0017:… (C)",
         K.TEAL, 15)
    qbox(d, p, 17000, 4150, 15600, 10250, "추론 — src/ 코드 읽기로 아는 것",
         "· TSS 에서 ss0/esp0 를 읽어 스택을 갈아타는 순서 (19장 — 하드웨어 동작)\n"
         "· 트랩 게이트라 IF 가 유지된다는 사실 (13장 type 15)\n"
         "· reschedule 경로 — schedule() 후 ret_from_sys_call 로 계속 (96-100)\n"
         "· 가짜 오류 코드 push 로 프레임 모양을 맞춘 설계 (asm.s:32)\n\n"
         "구분 규칙 — 화면에 찍힌 것만 관찰, 나머지는 전부 코드 추론.",
         K.ORANGE, 15)

    # ── 정답 43 ───────────────────────────────────────────────
    # 43 질문의 답
    p = d.slide("질문의 답 — write(1, …) 의 왕복", K.S_ANS,
                "lib/write.c:7-10 · unistd.h:172-183 · sched.c:411 · system_call.s:80-128 · sys.h:74-86 · read_write.c:83-103")
    d.flow(p, [
        ("write()", "lib/write.c:10\n_syscall3 전개"),
        ("int $0x80", "unistd.h:177\nEAX=4, 인자 3개"),
        ("IDT[0x80]", "sched.c:411\n트랩 게이트 (15, DPL3)"),
        ("_system_call", "system_call.s\n:80-94 · push 6"),
        ("sys_call_table[4]", "sys.h:74-86\ncall *(,%eax,4)"),
    ], y=4150, h=3550)
    arrow(d, p, 1450, 7720, "↓", 20, K.ORANGE, w=1400, h=850)
    d.flow(p, [
        ("sys_write", "fs/read_write.c\n:83-103 · rw_char"),
        ("pushl %eax", "system_call.s:95\nEAX 슬롯 = 반환값"),
        ("ret_from_sys_call", ":101-128\n시그널 검사 후"),
        ("pop 7 + iret", ":121-128\nCS·SS·ESP 복원"),
        ("__res", "unistd.h:178-183\n\"=a\" — EAX=3 반환"),
    ], y=8600, h=3550)
    d.banner(p, "번호 4와 인자 3개를 건네고 EAX 의 3 을 돌려받는다 — sys_write 내부(rw_char → 콘솔)는 13회차")

    # ── 정리 44–48 ────────────────────────────────────────────
    # 44 세 입구
    p = d.slide("같은 메커니즘, 다른 세 입구", K.S_WRAP,
                "kernel/system_call.s:80-100·176-197 · asm.s:19-51·97-129 · traps.c:63-85 · sched.c:385-412 — 오늘 본 소스 3열 정리")
    d.table(p, 1100, 4300, [5000, 8800, 8800, 8900], [
        ["축", "소프트웨어 int 0x80", "CPU 예외", "하드웨어 IRQ"],
        ["발생 주체", "사용자 프로그램의 명령", "CPU 가 강제", "장치 (8259A PIC)"],
        ["번호", "0x80", "0~16", "0x20~0x2F"],
        ["게이트·DPL", "트랩 15 · DPL 3", "트랩 15 · DPL 0", "인터럽트 14 · DPL 0 (키보드·플로피는 트랩)"],
        ["오류 코드", "없음", "있는 것도(8·10~14)", "없음"],
        ["진입 코드", "system_call.s:80", "asm.s · page.s", "system_call.s:176 + 드라이버"],
        ["복귀", "ret_from_sys_call → iret", "die()→do_exit 또는 pop+iret", "ret_from_sys_call(타이머)·자체"],
        ["특기", "EAX=번호, EBX·ECX·EDX=인자", "같은 명령 재실행(폴트형)", "EOI 필요 · 사용자 복귀 시 스케줄 가능"],
    ], row_h=1150, size=13)

    # 45 흔한 오해
    p = d.slide("흔한 오해 바로잡기", K.S_WRAP,
                "include/asm/system.h:33-40 · kernel/system_call.s:121-128 · mm/page.s:14-40 — §8 원문 계승")
    cards_sz(d, p, [
        ("\"int 0x80 은 특별한 call 이다\"",
         "아니다 — 스택이 커널 스택\n(tss.esp0) 으로 바뀌고\nCPL 과 세그먼트가 바뀐다.\n\n"
         "그것이 본질이다(19장)."),
        ("\"iret 는 모든 레지스터를\n복원한다\"",
         "복원하는 것은 5개 —\nEIP·CS·EFLAGS·\nOLDESP·OLDSS\n\n"
         "범용 레지스터는 진입 코드가\npush 했으니 코드가 pop 한다\n(121-127). 1회차 노트와 일관."),
        ("\"트랩 게이트는\n인터럽트를 끈다\"",
         "반대다 — 인터럽트 게이트\n(type 14)가 IF 를 끈다.\n\n"
         "트랩 게이트(type 15)는\nIF 를 그대로 둔다\n(system.h:33-40)."),
        ("\"예외 = 에러다\"",
         "page_fault(14) 는\n정상 동작의 일부다 —\n요구 적재·CoW 의 핵심 진입점.\n\n"
         "07·08회차에서 다룬다.\n오늘은 \"예외 목록의 하나\"로만."),
    ], y=4500, h=10000, t_size=17, b_size=14)

    # 46 현대 커널 연결
    p = d.slide("현대 커널과의 연결 — 구조는 그대로", K.S_BG,
                "x86-64 Linux — 진입 명령과 레지스터만 바뀌었다 · 자세한 비교는 14회차(오늘은 이 1장뿐)")
    d.table(p, 1100, 4300, [5300, 13100, 13100], [
        ["축", "Linux 0.11 (1991 · i386)", "현대 x86-64 Linux"],
        ["진입 명령", "int $0x80 — IDT 게이트", "syscall — MSR(LSTAR) 지정"],
        ["번호 레지스터", "EAX = __NR_*", "RAX = __NR_*"],
        ["인자 레지스터", "EBX · ECX · EDX", "RDI · RSI · RDX · R10 · R8 · R9"],
        ["호출 표", "sys_call_table (include/linux/sys.h)", "sys_call_table (arch/x86)"],
        ["복귀", "iret — ret_from_sys_call", "sysret"],
    ], row_h=1400, size=15)
    para(d, p, 1100, 13100, 31500, 1400,
         "\"번호 → 표 → 함수, 반환값 → 레지스터\" — 34년 전과 같은 구조다. 바뀐 것은 진입 명령과 레지스터 배치뿐.\n"
         "sysret·entry_64.S 이야기는 오늘 하지 않는다(14회차).", 15)

    # 47 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항(계획 §6 원문) — 정답은 강의 중 공개 · 근거: sched.c:409·411 · system.h:33-40 · system_call.s:83-95·121-128 · console.c:683-684")
    qs = [
        ("Q1", "set_system_gate(0x80,…) 대신 set_trap_gate(0x80,…) 를 쓰면 사용자 프로그램의 "
               "write() 는 어떻게 되는가?",
         "정답 — 게이트 DPL 이 0이 되어 CPL 3 의 int $0x80 이 #GP(13) → general_protection → die() → "
         "do_exit(11). 시스템 콜이 아니라 프로세스 종료가 된다."),
        ("Q2", "_system_call 이 edx·ecx·ebx 순서로 push 하는 이유는?",
         "정답 — C 호출 규약에서 첫 인자가 가장 낮은 주소(ESP 바로 위)에 있어야 한다. 마지막에 push 한 "
         "ebx 가 fd, ecx 가 buf, edx 가 count 가 된다."),
        ("Q3", "iret 뒤 사용자 코드의 EAX 에는 무엇이 있는가?",
         "정답 — sys_write 의 반환값. pushl %eax(95) 로 프레임 EAX 슬롯에 저장했다가 popl %eax(121) 로 "
         "꺼낸 값이며 \"=a\"(__res) 가 이를 받는다. 음수면 errno = -__res."),
        ("Q4", "타이머(0x20, intr)와 키보드(0x21, trap) — 진입 직후 EFLAGS.IF 값은 각각?",
         "정답 — 0x20 은 IF=0 (다른 IRQ 차단), 0x21 은 IF 유지(핸들러 중 타이머 인터럽트 가능). "
         "system.h:33-37 · sched.c:409 · console.c:683."),
    ]
    for i, (tag, q, a) in enumerate(qs):
        y = 4100 + i * 2680
        qbox(d, p, 1100, y, 31500, 2580, tag, q, K.TEAL, 14)
        d.text(p, 1450, y + 1780, 30800, 760,
               wrap_kr(a, 30500, 11), 11, K.MUTED)

    # 48 정리와 다음 회차
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "05회차 — 태스크와 스케줄링 · 파트 B «실행의 길» 계속 · kernel/system_call.s:96-100·176-197 이 연결 고리")
    cards_sz(d, p, [
        ("오늘 정리",
         "게이트 = 번호 → 진입점 + 권한 조건(type·DPL)\n\n"
         "int $0x80 → 5 push → _system_call →\nsys_call_table[4] → sys_write\n\n"
         "ret_from_sys_call → iret, EAX = 반환값\n\n"
         "세 입구는 같은 IDT — 다른 진입·복귀 코드"),
        ("05 예고 — 스케줄링",
         "_timer_interrupt 가 do_timer 를\n불러 schedule() 로 가면\nret_from_sys_call 로\n돌아오는 태스크가 바뀐다\n\n— 어떻게?\n\n"
         "counter·priority·switch_to\nkernel/sched.c"),
        ("떠나기 전 확인",
         "· 게이트 8바이트의 두 숫자\n  (type, DPL) 를 말할 수 있는가\n"
         "· 12슬롯 프레임을 그릴 수\n  있는가(20장)\n"
         "· iret 와 pop 의 분업을\n  설명할 수 있는가\n\n"
         "GDB 로 다시 확인 — 34-41장"),
    ], y=4300, h=9800, t_size=18, b_size=13)
    d.banner(p, "write(1, ...) 한 줄의 왕복을 통째로 따라갔다 — 다음은 이 길 위에서 누가 언제 교체되는가")


if __name__ == "__main__":
    K.run(globals())
