#!/usr/bin/env python3
"""06회차 덱 — fork()와 프로세스 생성 (output/06-fork.pptx)

계획: materials/slide-plans/06-fork.md (§2 표 48행 1:1 · §3 앞부분 명세 ·
§4 다이어그램 목록 · §5 캡처 4종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="06", total=48, slug="06-fork",
    part_no="B", part="«실행의 길»",
    title="06. fork()와 프로세스 생성",
    question="fork() 이후 부모와 자식은 어디에서 다시 실행되는가?",
    done=5,
    today_line="여섯째 태스크를 만드는 copy_process — TSS에 출발점을 심는다",
    next_lines=[
        "05 → 06   05: switch_to가 TSS를 통째로 복원한다 → 06: 그 TSS를 새로 채우는 곳, 여섯째 태스크를 만드는 copy_process",
        "06 → 07   06: copy_page_tables가 페이지를 어떻게 복사하는가(오늘은 결과만) → 07: 주소 변환 — 같은 숫자 주소가 왜 다른 메모리를 가리키는가",
        "뒷이야기   08: this_page &= ~2 뒤 자식이 쓰면? · 09 exec · 10 exit/wait — 모두 fork의 뒤를 받는다",
    ],
    road_note=("답 예고 — 둘 다 int $0x80 다음 명령, 단 EAX가 다르다(시연 C·41장 캡처로 확인).\n"
               "오늘은 질문→정리 10단계 전부를 진행한다 — 비워 두는 단계는 없다.\n"
               "재료 — 04회차(시스템 콜 진입 프레임) · 05회차(TSS·switch_to): 오늘은 그 위에 fork를 얹는다."),
    STRUCT=dict(
        teal=["proc", "mm"],
        today=[("kernel/fork.c", "copy_process"),
               ("kernel/system_call.s", "sys_fork 진입"),
               ("mm/memory.c", "copy_page_tables")],
        flow="sys_fork → verify_area → copy_process → copy_mem → copy_page_tables",
        up="↑ fork() 반환: 부모 pid · 자식 0",
        user="init · sh — 오늘의 출발점: fork() 호출",
    ),
)

CHECKS = dict(
    captions={
        5: "src/init/main.c:179-188",
        6: "src/init/main.c:137-140",
        7: "src/include/unistd.h:133-144",
        8: "src/kernel/system_call.s:80-94",
        9: "src/kernel/system_call.s:208-219",
        10: "src/kernel/system_call.s:208-211",
        11: "src/kernel/system_call.s:212-219",
        12: "src/kernel/fork.c:68-71",
        14: "src/kernel/fork.c:135-147",
        16: "src/kernel/fork.c:77-81",
        17: "src/kernel/fork.c:82-91",
        18: "src/kernel/fork.c:92-97",
        19: "src/kernel/fork.c:98-112",
        20: "src/include/linux/sched.h:171-184",
        21: "src/kernel/fork.c:39-52",
        23: "src/kernel/fork.c:120-128",
        24: "src/kernel/fork.c:129-132",
        25: "src/mm/memory.c:163-172",
        31: "src/include/linux/fs.h:116-122",
    },
    required=[
        "copy_process", "find_empty_process", "copy_mem", "copy_page_tables",
        "verify_area", "last_pid", "sys_call_table", "switch_to",
        "ret_from_sys_call", "iret", "int $0x80", "tss.eax", "tss.eip",
        "tss.esp0", "_TSS(nr)", "_LDT(nr)", "0x4000000", "mem_map",
        "f_count", "i_count", "f_pos", "-EAGAIN", "-ENOMEM",
        "TASK_UNINTERRUPTIBLE", "TASK_RUNNING", "*p = *current",
        "doesn't copy the supervisor stack", "pushl %eax", "0xA0", "&= ~2",
        "p->counter = p->priority",
    ],
    prereq=[
        ("switch_to", "src/kernel/fork.c:92-97"),
        ("TSS", "src/kernel/system_call.s:80-94"),
        ("sys_call_table", "src/kernel/fork.c:68-71"),
        ("int $0x80", "src/kernel/system_call.s:80-94"),
    ],
    structure_nodes=["fork.c", "system_call.s", "memory.c", "sys_call_table"],
    capture_slides=[35, 37, 39, 41],
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
    # ── 배경 05–07 · 15 · 22 · 26 ─────────────────────────────
    # 05 fork()의 약속
    p = d.slide("fork()의 약속", K.S_BG,
                "init/main.c:179-188 — 최초 사용자 프로세스 init()이 fork를 쓰는 모양이 곧 fork의 약속이다")
    d.code_panel(p, "src/init/main.c", 179, 188, 1100, 4400, 19700, 8900,
                 size=13, caption_extra="init() — 반환값으로 부모/자식 분기")
    nbox(d, p, 22000, 4400, 10000, 2000, "부모 — pid > 0",
         "if (pid>0)\nwhile (pid != wait(&i))\n자식이 끝날 때까지 기다린다",
         K.TEAL, s1=16, s2=13)
    nbox(d, p, 22000, 6700, 10000, 2000, "자식 — 0",
         "if (!(pid=fork()))\nexecve(\"/bin/sh\",argv_rc,envp_rc)\n실패하면 _exit(2)",
         K.ORANGE, s1=16, s2=13)
    para(d, p, 22000, 9000, 10000, 3600,
         "한 번 부르면 두 번 돌아온다.\n반환값 — 부모: 자식 pid · 자식: 0 · 실패: -1(errno)", 15)
    d.banner(p, "같은 코드, 같은 지점, 다른 값 — 오늘 120분의 표어")

    # 06 최초의 fork: main.c
    p = d.slide("최초의 fork: main.c", K.S_CODE,
                "init/main.c:12-24(주석) · 137-140 — task 0이 fork로 task 1(init)을 낳는 최초의 fork")
    d.code_panel(p, "src/init/main.c", 12, 24, 1100, 4400, 19700, 8900,
                 size=10, caption_extra="주석 — fork가 inline이어야 하는 이유")
    d.code_panel(p, "src/init/main.c", 137, 140, 22000, 4400, 10500, 4400,
                 size=12, caption_extra="move_to_user_mode 직후")
    para(d, p, 22000, 9100, 10500, 5200,
         "주석 요지 — 커널 공간에서의 fork는 COW가 없다: task 0의 사용자 스택을 자식과 "
         "공유하게 된다.\n\nmain()은 fork 뒤 스택을 쓰면 안 되고, 함수 호출도 스택을 쓰므로 "
         "fork조차 inline로 박는다.\n\ntask 0의 특수성 자체는 05회차에서 다뤘다.", 14)
    d.banner(p, "if (!fork()) { init(); } — 반환값 0 = 자식: 최초의 분기 (137-140)")

    # 07 _syscall0(int,fork)
    p = d.slide("_syscall0(int,fork)", K.S_CODE,
                "include/unistd.h:62(__NR_fork=2) · 133-144 전개 · include/linux/sys.h:74 — 04회차 _syscall3와 골격 동일")
    d.code_panel(p, "src/include/unistd.h", 133, 144, 1100, 4400, 19700, 9700,
                 size=12, caption_extra="_syscall0 전개 — 인자 없는 시스템 콜")
    para(d, p, 22000, 4400, 10000, 5400,
         "__NR_fork = 2(62행) → sys_call_table[2] = sys_fork(sys.h:74)\n\n"
         "int $0x80 — eax에 번호 2를 실어 80번 인터럽트\n\n"
         "\"=a\"(__res) — 커널의 반환도 eax로 받는다\n\n"
         "04회차 _syscall3와 다른 점은 인자가 없다는 것뿐", 15)
    nbox(d, p, 22000, 10200, 10000, 1600, "unistd.h:62",
         "#define __NR_fork 2", None, K.TEAL, K.TEAL, s1=13, s2=12)
    nbox(d, p, 22000, 12100, 10000, 1600, "sys.h:74",
         "sys_call_table[] = { sys_setup, sys_exit, sys_fork, … }",
         None, K.TEAL, K.TEAL, s1=13, s2=12)
    d.banner(p, "fork() 한 줄 = int $0x80 (EAX=2) — 04회차 프레임의 재입구")

    # 08 04회차 프레임 다시
    p = d.slide("04회차 프레임 다시 — 스택 12슬롯", K.S_CODE,
                "kernel/system_call.s:17-31(주석 그림) · 80-94 — 이 스택이 자식의 TSS 재료가 된다(12장 예고)")
    slots = [("eax — 95행 pushl %eax(sys_fork 뒤)", "none"),
             ("ebx", "sc"), ("ecx", "sc"), ("edx", "sc"),
             ("fs", "sc"), ("es", "sc"), ("ds", "sc"),
             ("eip", "cpu"), ("cs", "cpu"), ("eflags", "cpu"),
             ("oldesp = 사용자 esp", "cpu"), ("oldss = 사용자 ss", "cpu")]
    fills = {"sc": (K.TEAL, K.INK), "cpu": (K.ORANGE, K.INK), "none": (None, K.MUTED)}
    for i, (label, kind) in enumerate(slots):
        fill, col = fills[kind]
        nbox(d, p, 1100, 4700 + i * 620, 5600, 560, label, None,
             fill, col, edge=K.MUTED, s1=12)
    d.text(p, 1100, 12200, 6400, 600, "0(%esp) = 위 · 2C(%esp) = 아래", 11, K.MUTED)
    para(d, p, 1100, 12800, 6400, 1500,
         "주석 17-31의 배치 그대로 — 낮은 주소가 위.", 12, K.MUTED)
    d.code_panel(p, "src/kernel/system_call.s", 80, 94, 7300, 4400, 24400,
                 10000, size=10, caption_extra="직전 6개 push와 call")
    d.banner(p, "예고 — 이 스택이 그대로 자식 TSS의 재료가 된다(12장)")

    # 09 sys_fork는 C 함수가 아니다
    p = d.slide("sys_fork는 C 함수가 아니다", K.S_CODE,
                "include/linux/sys.h:3(선언) · kernel/system_call.s:208-219(정의) — C 컴파일러가 못 하는 push 4개")
    d.code_panel(p, "src/include/linux/sys.h", 1, 4, 1100, 4400, 9400, 3400,
                 size=12, caption_extra="선언(3행) — 정의는 없다")
    para(d, p, 1100, 8100, 9400, 5000,
         "sys.h:3 extern int sys_fork(); — 선언뿐이다.\n\n"
         "정의는 system_call.s:208-219 어셈블리.\n\n"
         "이유 — copy_process에 넘겨야 할 gs·esi·edi·ebp는 _system_call이 push하지 "
         "않은 값이다. 어셈블리가 직접 push해야 슬롯이 정확히 만들어진다(11장).", 14)
    d.code_panel(p, "src/kernel/system_call.s", 208, 219, 11400, 4400, 21300,
                 9010, size=11, caption_extra="_sys_fork 본체 12줄")
    d.banner(p, "sys_fork의 본체는 system_call.s:208-219 — 어셈블리 12줄")

    # 10 _sys_fork (1)
    p = d.slide("_sys_fork 한 줄씩 (1): nr 확보와 실패 복귀", K.S_CODE,
                "kernel/system_call.s:208-211 · include/errno.h:30(EAGAIN=11) — find_empty_process 내부는 14장")
    d.code_panel(p, "src/kernel/system_call.s", 208, 211, 1100, 4400, 19700,
                 4600, size=13, caption_extra="첫 두 단계")
    d.flow(p, [("call _find_empty_process", "eax = nr\n빈 task[] 인덱스"),
               ("testl %eax,%eax", "부호 검사만"),
               ("js 1f", "음수 = 실패"),
               ("1: ret", "-EAGAIN 그대로\n사용자 반환 경로로")],
           y=9500, h=3300)
    para(d, p, 1100, 13200, 31500, 1300,
         "실패값 -EAGAIN(errno.h:30)은 find_empty_process가 만든다 — ret하면 "
         "_system_call:95로 돌아가 pushl %eax 후 그대로 사용자로 돌아간다.", 15)
    d.banner(p, "성공이든 실패든 eax가 핵심 — nr 또는 -EAGAIN")

    # 11 _sys_fork (2)
    p = d.slide("_sys_fork 한 줄씩 (2): 5개 push와 call _copy_process", K.S_CODE,
                "kernel/system_call.s:212-219 · 95 — push 5개가 copy_process의 인자를 완성한다")
    d.code_panel(p, "src/kernel/system_call.s", 212, 219, 1100, 4400, 19700,
                 7100, size=12, caption_extra="push 5개 · call · 정리 · ret")
    d.text(p, 22000, 4300, 10000, 600, "push할 때마다 스택이 아래로 성장", 13, K.TEAL, True)
    pushes = [("… (기존 프레임 — ebx가 여기)", "old"),
              ("gs", "new"), ("esi", "new"), ("edi", "new"),
              ("ebp", "new"), ("eax = nr", "top"),
              ("복귀 주소(218행) — call이 push", "ret")]
    pfill = {"old": (None, K.MUTED), "new": (K.TEAL, K.INK),
             "top": (K.ORANGE, K.INK), "ret": (None, K.MUTED)}
    for i, (label, kind) in enumerate(pushes):
        fill, col = pfill[kind]
        nbox(d, p, 22000, 5000 + i * 680, 10000, 620, label, None,
             fill, col, edge=K.MUTED, s1=12)
    para(d, p, 22000, 10000, 10000, 4200,
         "push 순서 gs→esi→edi→ebp→eax — 마지막에 push한 eax(nr)가 스택 top = "
         "첫 번째 인자.\n\n218 addl $20,%esp — 5개(20바이트) 정리.\n"
         "219 ret → _system_call:95 pushl %eax(반환값 보관).", 14)
    d.banner(p, "push 5개 = copy_process 인자 앞부분(nr,ebp,edi,esi,gs)")

    # 12 17개 인자 = 슬롯 17슬롯
    p = d.slide("17개 인자 = 스택 17슬롯", K.S_CODE,
                "kernel/fork.c:68-71 · system_call.s:17-31,80-94,208-219 — C 함수는 그저 스택을 인자로 읽는다")
    groups = [("nr", "sf"), ("ebp", "sf"), ("edi", "sf"), ("esi", "sf"),
              ("gs", "sf"), ("none ← call이 남긴 복귀 주소", "no"),
              ("ebx", "sc"), ("ecx", "sc"), ("edx", "sc"), ("fs", "sc"),
              ("es", "sc"), ("ds", "sc"),
              ("eip", "cp"), ("cs", "cp"), ("eflags", "cp"),
              ("esp", "cp"), ("ss", "cp")]
    gfill = {"sf": (K.TEAL, K.INK), "no": (K.ORANGE, K.INK),
             "sc": (K.PAPER, K.INK), "cp": (0x183340, K.PAPER)}
    for i, (label, kind) in enumerate(groups):
        fill, col = gfill[kind]
        nbox(d, p, 1100, 4300 + i * 580, 8600, 540,
             f"{i * 4 + 4:02x}(%esp)  {label}", None, fill, col, s1=12)
    d.code_panel(p, "src/kernel/fork.c", 68, 71, 10200, 4300, 22500, 3600,
                 size=13, caption_extra="시그니처 17개 — eax는 없다")
    legend = [("TEAL — _sys_fork push(212-216): nr, ebp, edi, esi, gs", K.TEAL),
              ("ORANGE — none: call _sys_call_table(94)가 남긴 복귀 주소", K.ORANGE),
              ("밝은 칸 — _system_call push(83-88): ebx, ecx, edx, fs, es, ds", None),
              ("어두운 칸 — CPU push(int 0x80): eip, cs, eflags, esp, ss", None)]
    for i, (t, kind) in enumerate(legend):
        if kind == K.TEAL:
            nbox(d, p, 10200, 8300 + i * 820, 22500, 720, t, None,
                 K.TEAL, s1=13)
        elif kind == K.ORANGE:
            nbox(d, p, 10200, 8300 + i * 820, 22500, 720, t, None,
                 K.ORANGE, s1=13)
        else:
            nbox(d, p, 10200, 8300 + i * 820, 22500, 720, t, None,
                 None, K.MUTED, s1=13)
    para(d, p, 10200, 11700, 22500, 2400,
         "C 함수는 그저 스택을 인자로 읽을 뿐이다 — copy_process의 인자 목록 어디에도 "
         "eax가 없다(시연 A·35장에서 눈으로 확인). 00(%esp)는 call이 남긴 복귀 주소(13장).", 15)
    d.banner(p, "17슬롯 = 17인자 1:1 — 세 그룹이 만나는 곳이 copy_process")

    # 13 none의 정체
    p = d.slide("none의 정체", K.S_CODE,
                "kernel/system_call.s:94(call) · 217(call) · fork.c:68-71 — call 두 번이 남긴 복귀 주소 자리")
    d.text(p, 1100, 4250, 4000, 500, "높은 주소 ↑", 12, K.MUTED)
    d.text(p, 28200, 4250, 4000, 500, "↓ 낮은 주소", 12, K.MUTED)
    cols = [(1100, 4300, "CPU push\n(int 0x80)", "eip · cs\neflags · esp · ss", "cpu"),
            (5800, 4300, "_system_call push\n(83-88)", "ebx · ecx · edx\nfs · es · ds", "sc"),
            (10500, 6100, "call _sys_call_table(94)가 push\n= 복귀 주소(_system_call:95)",
             "none — copy_process가\n받기만 하고 무시", "no"),
            (17100, 4300, "_sys_fork push\n(212-216)", "gs · esi · edi\nebp · eax(nr)", "sf"),
            (21900, 6100, "call _copy_process(217)가 push\n= 복귀 주소(218행)",
             "copy_process 자신의\n복귀 주소 — 인자 아님", "ret")]
    cfill = {"cpu": (0x183340, K.PAPER), "sc": (K.PAPER, K.INK),
             "no": (K.ORANGE, K.INK), "sf": (K.TEAL, K.INK),
             "ret": (None, K.MUTED)}
    for x, w, head, body, kind in cols:
        fill, col = cfill[kind]
        d.text(p, x, 4900, w, 900, head, 12, K.TEAL if kind != "no" else K.ORANGE, True)
        nbox(d, p, x, 5900, w, 2300, body, None, fill, col, edge=K.MUTED, s1=13)
    d.text(p, 5550, 6600, 900, 700, "→", 20, K.TEAL, True)
    d.text(p, 16850, 6600, 900, 700, "→", 20, K.TEAL, True)
    para(d, p, 1100, 8500, 31500, 1500,
         "call은 '돌아올 주소'를 스택에 남긴다 — 두 번의 call이 각각 자리를 만든다. "
         "copy_process가 보는 스택에서 ebx 바로 아래(높은 주소)에 있는 첫 번째 복귀 주소가 "
         "인자 none이다.", 15)
    d.code_panel(p, "src/kernel/system_call.s", 93, 95, 1100, 10300, 15200,
                 3900, size=13, caption_extra="call(94)과 pushl %eax(95)")
    para(d, p, 17400, 10300, 15300, 3900,
         "fork.c:68-71의 none — 받기만 하고 본문에서 쓰이지 않는다.\n\n"
         "두 번째 복귀 주소(218행)는 nr 아래(낮은 주소) — copy_process가 return하면 "
         "_sys_fork로 돌아가는 수단일 뿐 인자가 아니다.", 14)
    d.banner(p, "'none'도 결국 스택의 한 슬롯 — call이 만든 자리")

    # 14 find_empty_process
    p = d.slide("find_empty_process", K.S_CODE,
                "kernel/fork.c:135-147 · 22(last_pid) — pid 발급과 빈 슬롯 탐색은 별개의 두 루프")
    d.code_panel(p, "src/kernel/fork.c", 135, 147, 1100, 4400, 19700, 8900,
                 size=10, caption_extra="repeat 루프와 두 번째 for")
    steps = [("++last_pid", "음수 넘침 시 1로(140)\nlast_pid는 전역(22행)"),
             ("repeat: 중복 검사", "살아 있는 task 중 같은 pid가\n있으면 다시 증가(141-142)"),
             ("빈 task[i] 탐색", "i = 1…63 — NULL인 첫 칸\n반환(143-145)"),
             ("없으면 -EAGAIN", "errno.h:30 · 146행", K.ORANGE)]
    for i, (t, b, *rest) in enumerate(steps):
        fill = rest[0] if rest else K.PAPER
        nbox(d, p, 22000, 4400 + i * 1800, 10000, 1500, t, b, fill,
             s1=15, s2=12)
    para(d, p, 22000, 11900, 10000, 1800,
         "pid(전역 번호)와 슬롯 nr(task[] 인덱스)은 다른 값 — 다음 장 비교 표.", 14)
    d.banner(p, "last_pid는 재부팅마다 0부터 — pid와 nr은 별개 번호 체계")

    # 15 pid vs nr
    p = d.slide("pid vs nr", K.S_BG,
                "kernel/fork.c:135-147 · 52 · include/linux/sched.h:155-156 — 이해 확인 4번·07회차 예고의 기초")
    d.table(p, 1100, 4500, [5600, 12900, 13000], [
        ["", "pid", "nr — task[] 인덱스"],
        ["발급", "last_pid 전역 증가 + 중복 검사(139-142)", "task[1..63] 중 첫 빈 칸(143-145)"],
        ["범위", "1 이상 — 음수 넘침 시 1로 리셋(140)", "1–63 (0은 task 0 전용)"],
        ["용도", "getpid · wait 등 사용자에게 보이는 번호", "GDT 선택자 _TSS(nr)·_LDT(nr) · 선형 base nr*0x4000000"],
        ["보이는 주체", "사용자 공간(stdout · ps)", "커널 안(GDT · LDT · copy_mem)"],
    ], row_h=1900, size=15)
    d.banner(p, "pid 100번대도 nr은 2일 수 있다 — 이 대응의 의미는 07회차가 답한다")

    # ── 코드 16–27 ────────────────────────────────────────────
    # 16 copy_process (1)
    p = d.slide("copy_process (1): 페이지 하나 = task_struct + 커널 스택", K.S_CODE,
                "kernel/fork.c:77-81 · mm/memory.c:63(get_free_page) — 구조체 대입 한 줄과 비어 있는 스택")
    d.code_panel(p, "src/kernel/fork.c", 77, 81, 1100, 4400, 19700, 5400,
                 size=13, caption_extra="페이지 확보 · 구조체 통째 복사")
    badge(d, p, 22300, 4400, 9400, "p = get_free_page() — 4 KiB 정확히 한 장",
          K.TEAL, 800, 13)
    d.outline(p, 22600, 5700, 8800, 5300, K.LINE, 90)
    nbox(d, p, 22900, 5900, 8200, 2300, "task_struct 복사본",
         "*p = *current (81)", K.PAPER, s1=14, s2=12)
    nbox(d, p, 22900, 8450, 8200, 2300, "커널 스택 — 비어 있다",
         "복사되지 않았다(주석)", None, K.MUTED, K.MUTED, s1=14, s2=12)
    d.text(p, 31700, 5900, 900, 600, "↑ p", 15, K.TEAL, True)
    d.text(p, 30800, 10300, 1900, 600, "↑ esp0", 15, K.TEAL, True)
    para(d, p, 1100, 10300, 19700, 3400,
         "주석 원문 — \"doesn't copy the supervisor stack\": 구조체 대입 한 줄이 부모의 "
         "task_struct 전체를 복사하지만, 같은 페이지 뒤쪽의 커널 스택은 복사하지 않는다.\n\n"
         "따라서 자식은 커널 안의 어디로도 '돌아갈' 곳이 없다 — TSS의 eip/esp로 곧장 사용자 "
         "모드로 간다(20장).", 15)
    d.banner(p, "task_struct + 빈 커널 스택 — 정확히 4 KiB 한 페이지(fork.c:93)")

    # 17 copy_process (2)
    p = d.slide("copy_process (2): 덮어쓰는 필드", K.S_CODE,
                "kernel/fork.c:82-91 — 복사(81) 다음에 자기 것으로 덮어쓰는 필드들")
    d.code_panel(p, "src/kernel/fork.c", 82, 91, 1100, 4400, 19700, 8400,
                 size=12, caption_extra="state·pid·father·counter·시간 …")
    nbox(d, p, 22000, 4400, 10000, 5700, "덮어쓴다 (82-91)",
         "state = TASK_UNINTERRUPTIBLE (82)\npid = last_pid (83)\n"
         "father = current->pid (84)\np->counter = p->priority (85)\n"
         "signal = 0 · alarm = 0 (86-87)\nleader = 0 (88)\n"
         "utime·stime·cutime·cstime = 0 (89-90)\nstart_time = jiffies (91)",
         K.ORANGE, s1=15, s2=12)
    nbox(d, p, 22000, 10400, 10000, 3100, "복사된 채 남는 것",
         "priority · blocked · sigaction[]\nuid/gid · umask · tty\nclose_on_exec · "
         "filp[] 포인터 · ldt · tss", K.TEAL, s1=15, s2=12)
    d.banner(p, "state=UNINTERRUPTIBLE — 아직 schedule()이 고르면 안 된다(131행)")

    # 18 copy_process (3) TSS (1)
    p = d.slide("copy_process (3): TSS 채우기 — esp0·ss0·eip·eflags·eax", K.S_CODE,
                "kernel/fork.c:92-97 · include/linux/sched.h:51-76(tss_struct, 05 복습) — 채움 지도 (1)")
    d.code_panel(p, "src/kernel/fork.c", 92, 97, 1100, 4400, 19700, 6100,
                 size=13, caption_extra="esp0·ss0·eip·eflags·eax")
    tss1 = [("tss.esp0 ← PAGE_SIZE+(long)p", "자기 페이지 끝 = 커널 스택(05 복습)", K.PAPER),
            ("tss.ss0 ← 0x10", "커널 데이터 세그먼트", K.PAPER),
            ("tss.eip ← [스택 eip]", "int $0x80 다음 명령(부모와 같은 값)", K.PAPER),
            ("tss.eflags ← [스택 eflags]", "플래그 그대로", K.PAPER),
            ("tss.eax ← 0 (97행)", "\"자식은 0을 받는다\"의 시드", K.ORANGE)]
    for i, (t, b, fill) in enumerate(tss1):
        nbox(d, p, 22000, 4400 + i * 1350, 10000, 1200, t, b, fill,
             s1=14, s2=12)
    para(d, p, 1100, 10900, 19700, 2900,
         "05회차 tss_struct(sched.h:51-76)의 필드 이름 그대로다 — esp0은 05에서 본 "
         "'커널로 들어올 때의 스택 포인터' 자리. 97행 tss.eax = 0이 시연 B-2(38-39장)에서 "
         "눈으로 보는 값이다.", 15)
    d.banner(p, "tss.eax = 0 (fork.c:97) — 자식의 fork() 반환값 0은 여기서 심는다")

    # 19 copy_process (3) TSS (2)
    p = d.slide("copy_process (3): TSS 채우기 — 범용 레지스터·세그먼트·ldt", K.S_CODE,
                "kernel/fork.c:98-112 · sched.h:155-156 — 채움 지도 (2): 값의 출처는 전부 스택")
    d.code_panel(p, "src/kernel/fork.c", 98, 112, 1100, 4400, 19700, 10000,
                 size=10, caption_extra="ecx…edi · 세그먼트 & 0xffff · ldt")
    tss2 = [("[ebx][ecx][edx] → tss.ebx·ecx·edx", "스택 값 그대로(98-100)"),
            ("[esp] → tss.esp", "부모의 사용자 ESP 그대로(101)"),
            ("[ebp][esi][edi] → tss.ebp·esi·edi", "스택 값 그대로(102-104)"),
            ("es·cs·ss·ds·fs·gs & 0xffff", "상위 16비트 버림(105-110)"),
            ("tss.ldt = _LDT(nr) · trace_bitmap", "자기 LDT 선택자(111-112) — sched.h:155-156")]
    for i, (t, b) in enumerate(tss2):
        nbox(d, p, 22000, 4400 + i * 1750, 10000, 1550, t, b, K.PAPER,
             s1=14, s2=12)
    d.banner(p, "값의 출처는 전부 부모 스택 스냅숏 — 단 ldt만 자기 것(_LDT(nr))")

    # 20 왜 tss.eax = 0이 되는가
    p = d.slide("왜 tss.eax = 0이 \"자식은 0을 받는다\"가 되는가", K.S_CODE,
                "sched.h:171-184(switch_to, 05 재게시) · unistd.h:133-144 · system_call.s:95,121")
    d.code_panel(p, "src/include/linux/sched.h", 171, 184, 1100, 4400, 19700,
                 9500, size=10, caption_extra="switch_to — ljmp TSS 전환")
    nbox(d, p, 22000, 4400, 10000, 1300, "ljmp %0", "TSS 디스크립터로 점프(177)", K.PAPER, s1=14, s2=12)
    nbox(d, p, 22000, 5950, 10000, 1600, "CPU가 TSS를 전부 로드",
         "eax·ecx·…·eip·esp·eflags·ldt\n통째로 레지스터가 된다", K.PAPER, s1=14, s2=12)
    nbox(d, p, 22000, 7800, 10000, 1500, "CS=0x0f · EIP = int $0x80 다음 · EAX = 0",
         None, K.ORANGE, s1=14)
    nbox(d, p, 22000, 9550, 10000, 1500, "_syscall0 뒷부분",
         "\"=a\"(__res) → __res = 0 → return 0", K.PAPER, s1=14, s2=12)
    nbox(d, p, 22000, 11300, 10000, 1700, "부모는 다른 길",
         "system_call.s:95 pushl %eax(last_pid)\n→ ret_from_sys_call:121 popl %eax\n→ 128 iret — EAX = pid",
         K.TEAL, s1=14, s2=12)
    d.banner(p, "자식은 ret_from_sys_call을 지나지 않는다 — TSS 복원으로 곧장 사용자")

    # 21 copy_mem
    p = d.slide("copy_process (4): copy_mem", K.S_CODE,
                "kernel/fork.c:39-61 · sched.h:211-212,226(set/get_base) · errno.h:31(ENOMEM) — kernel/에서 mm/로 건너는 다리")
    d.code_panel(p, "src/kernel/fork.c", 39, 52, 1100, 4400, 15200, 9500,
                 size=10, caption_extra="한계·base 확인 → panic 검사 → new_base")
    d.code_panel(p, "src/kernel/fork.c", 53, 61, 17400, 4400, 15300, 7300,
                 size=11, caption_extra="start_code · set_base · copy_page_tables")
    para(d, p, 17400, 12000, 15300, 2400,
         "52: new_base = nr * 0x4000000(64 MiB × nr)\n53-55: p->start_code · "
         "set_base(ldt[1]/[2])\n56: copy_page_tables 실패 시 57 free_page_tables "
         "되돌림 + -ENOMEM", 14)
    d.banner(p, "copy_mem — kernel/fork.c에서 mm/memory.c로 건너는 다리(04장 흐름도)")

    # 22 nr × 64 MiB
    p = d.slide("자식의 주소 공간은 \"번호 × 64 MiB\"", K.S_BG,
                "kernel/fork.c:52-55 — 같은 논리 주소가 태스크별 선형 주소로 갈라진다(07회차 예고)")
    cells = [("nr=0\ntask 0\n0x0", "t0"), ("nr=1\n0x4000000", "par"),
             ("nr=2\n0x8000000", "chi"), ("nr=3\n0xC000000", "mut"),
             ("nr=4", "mut"), ("nr=5", "mut"), ("nr=6", "mut"), ("…\n4 GiB", "mut")]
    cw = (31500 - 7 * 200) // 8
    for i, (label, kind) in enumerate(cells):
        x = 1100 + i * (cw + 200)
        if kind == "t0":
            nbox(d, p, x, 4700, cw, 1900, label, None, K.TEAL, s1=13)
        elif kind == "par":
            nbox(d, p, x, 4700, cw, 1900, label, "부모(예)", K.TEAL, s1=13, s2=11)
        elif kind == "chi":
            nbox(d, p, x, 4700, cw, 1900, label, "자식(예)", K.ORANGE, s1=13, s2=11)
        else:
            nbox(d, p, x, 4700, cw, 1900, label, None, None, K.MUTED, s1=13)
    d.text(p, 1100, 6750, 31500, 600,
           "선형 주소 공간 4 GiB — 태스크별 64 MiB 칸(base = nr * 0x4000000, fork.c:52)",
           13, K.TEAL, True)
    nbox(d, p, 1100, 7800, 9400, 1500, "논리 주소 0x1000",
         "모든 태스크의 코드가 쓰는 같은 숫자", K.PAPER, s1=14, s2=12)
    nbox(d, p, 12400, 7800, 9400, 1500, "부모(nr=1) 선형 0x4001000",
         "LDT base 0x4000000 + 0x1000", K.TEAL, s1=13, s2=12)
    nbox(d, p, 23300, 7800, 9400, 1500, "자식(nr=2) 선형 0x8001000",
         "LDT base 0x8000000 + 0x1000", K.ORANGE, s1=13, s2=12)
    d.text(p, 10650, 8100, 1500, 700, "→", 22, K.TEAL, True)
    d.text(p, 21900, 8100, 1500, 700, "→", 22, K.ORANGE, True)
    para(d, p, 1100, 9900, 31500, 4000,
         "사용자 코드의 주소 0(논리)은 LDT base 덕에 태스크마다 다른 선형 주소가 된다.\n\n"
         "\"같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가\"(07회차 핵심 질문)의 "
         "절반이 여기서 결정된다 — 페이징(선형→물리)은 07로 넘긴다.\n\n"
         "base·한계는 copy_mem이 set_base로 심는다(53-55) — 세그먼트 관용구는 02회차 복습.", 15)
    d.banner(p, "자식의 주소 공간 = nr × 64 MiB 칸 하나 — 논리 주소는 그대로")

    # 23 공유 카운트
    p = d.slide("copy_process (5): 공유 카운트", K.S_CODE,
                "kernel/fork.c:120-128 · include/linux/fs.h:107,119 — 포인터는 이미 복사됐다, 카운트만 올린다")
    d.code_panel(p, "src/kernel/fork.c", 120, 128, 1100, 4400, 19700, 7300,
                 size=11, caption_extra="f_count++ · i_count++")
    nbox(d, p, 22000, 4400, 4800, 1500, "부모 task_struct", "filp[i] 포인터",
         K.TEAL, s1=13, s2=11)
    nbox(d, p, 27200, 4400, 4500, 1500, "자식 task_struct", "같은 포인터 값",
         K.TEAL, s1=13, s2=11)
    d.text(p, 23800, 5950, 1200, 700, "↓", 20, K.TEAL, True)
    d.text(p, 28800, 5950, 1200, 700, "↓", 20, K.TEAL, True)
    nbox(d, p, 22000, 6700, 10000, 1300, "struct file — f_count++",
         "fs.h:119 · 같은 객체 하나", K.PAPER, s1=13, s2=12)
    nbox(d, p, 22000, 8300, 10000, 1300, "pwd·root·executable → m_inode",
         "i_count++ (fs.h:107)", K.PAPER, s1=13, s2=12)
    para(d, p, 1100, 12000, 19700, 2400,
         "*p = *current가 filp[]·pwd·root·executable 포인터를 이미 복사했다(81) — 같은 객체를 "
         "가리키므로 복사 대신 카운트만 증가시킨다(120-128). 해제는 do_exit의 sys_close·iput가 "
         "대칭으로 되돌린다(exit.c:115-123, 10회차).", 14)
    d.banner(p, "복사가 아니라 참조 세기 — f_count·i_count가 공유의 증표")

    # 24 GDT 등록·RUNNING·반환
    p = d.slide("copy_process (6): GDT 등록·RUNNING·반환", K.S_CODE,
                "kernel/fork.c:129-132 · sched.h:155-156 · asm/system.h:65-66 — GDT에 자리 잡고 마지막에 RUNNING")
    d.code_panel(p, "src/kernel/fork.c", 129, 132, 1100, 4400, 19700, 4200,
                 size=11, caption_extra="set_tss_desc·set_ldt_desc·RUNNING·return")
    para(d, p, 22000, 4400, 10000, 4700,
         "129-130 GDT에 TSS·LDT 설명자 등록(set_tss_desc·set_ldt_desc, system.h:65-66)\n\n"
         "_TSS(nr)·_LDT(nr) = (nr<<4)+(4<<3 / 5<<3)(sched.h:155-156)\n\n"
         "131 state=TASK_RUNNING — 주석 \"do this last, just in case\"\n\n"
         "132 return last_pid — 부모 EAX의 재료", 13)
    gdt = ["0 nul", "1 코드", "2 데이터", "3 syscall", "4 TSS0", "5 LDT0",
           "6 TSS1", "7 LDT1", "8 TSS2", "9 LDT2"]
    gw = (31500 - 9 * 105) // 10
    for i, label in enumerate(gdt):
        x = 1100 + i * (gw + 105)
        if i >= 8:
            nbox(d, p, x, 9700, gw, 1600, label, "nr=2 예 — 오늘의 자식",
                 K.ORANGE, s1=12, s2=10)
        elif i >= 4:
            nbox(d, p, x, 9700, gw, 1600, label, None, K.PAPER, s1=12)
        else:
            nbox(d, p, x, 9700, gw, 1600, label, None, None, K.MUTED, s1=12)
    para(d, p, 1100, 11600, 31500, 2600,
         "TSS·LDT가 GDT에 등록되어야 switch_to의 ljmp가 자식을 찾을 수 있다(05 복습).\n"
         "state=TASK_RUNNING을 마지막에 바꾸는 이유 — 준비가 끝나기 전에 schedule()에 "
         "선택되면 안 되므로(28장 상태도).", 15)
    d.banner(p, "\"do this last\" — GDT 등록 뒤에야 실행 가능이 된다")

    # 25 copy_page_tables 결과만
    p = d.slide("copy_page_tables — 결과만 (참고)", K.S_CODE,
                "mm/memory.c:150-189 중 읽는 줄만 · 39(invalidate) — 비트 뜻은 07회차, 쓰기는 08회차")
    d.code_panel(p, "src/mm/memory.c", 163, 172, 1100, 4400, 15200, 7900,
                 size=11, caption_extra="디렉터리·새 페이지 테이블·0xA0")
    d.code_panel(p, "src/mm/memory.c", 174, 187, 17400, 4400, 15300, 9500,
                 size=10, caption_extra="항목 복사·읽기 전용·mem_map++·invalidate")
    para(d, p, 1100, 12600, 15200, 1700,
         "163-171: 디렉터리 항목 검사 · 새 페이지 테이블 한 장(get_free_page) · *to_dir |= 7.\n"
         "172: from==0이면 0xA0(160)개 = task 0의 640 KiB만 — 첫 fork 특례.", 14)
    d.banner(p, "결과만 — 항목 복사 + 쓰기 금지(&= ~2) + mem_map++ + invalidate()")

    # 26 표 vs 페이지
    p = d.slide("복사된 것은 \"표\", 공유된 것은 \"페이지\"", K.S_BG,
                "mm/memory.c:163-184 — fork는 메모리를 복사하지 않는다, 페이지 테이블(표)을 복사한다")
    nbox(d, p, 7300, 4400, 19000, 1200, "페이지 디렉터리 하나 — 모든 태스크가 공유",
         "sched.h:128 tss.cr3 = &pg_dir · 07회차에서 다시", None, K.MUTED, K.MUTED,
         edge=K.LINE, s1=14, s2=11)
    nbox(d, p, 2500, 6200, 12000, 1100, "부모 영역 항목(from)", None, K.TEAL, s1=13)
    nbox(d, p, 19300, 6200, 12000, 1100, "자식 영역 항목(to) — 새로 추가(|7)",
         None, K.ORANGE, s1=13)
    d.text(p, 8300, 7350, 1400, 600, "↓", 20, K.TEAL, True)
    d.text(p, 25100, 7350, 1400, 600, "↓", 20, K.ORANGE, True)
    nbox(d, p, 2500, 7900, 12000, 1300, "부모 페이지 테이블", None, K.TEAL, s1=13)
    nbox(d, p, 19300, 7900, 12000, 1300, "자식 페이지 테이블 — 새 페이지 한 장",
         "항목을 복사해 담는다(163-171)", K.ORANGE, s1=13, s2=11)
    d.text(p, 8300, 9250, 1400, 600, "↓", 20, K.TEAL, True)
    d.text(p, 25100, 9250, 1400, 600, "↓", 20, K.ORANGE, True)
    nbox(d, p, 8500, 9800, 17000, 1400, "물리 페이지 A — 양쪽 모두 읽기 전용",
         "this_page &= ~2 · 부모 항목도 읽기 전용으로(177·180)", K.PAPER, s1=14, s2=12)
    badge(d, p, 11600, 11400, 10800, "mem_map[A] = 2 (179-184)", K.TEAL, 800, 14)
    para(d, p, 1100, 12600, 31500, 1900,
         "\"fork는 메모리를 복사하지 않는다\"의 정확한 의미 — 새로 만드는 것은 페이지 테이블(표)뿐이고 "
         "물리 페이지는 읽기 전용으로 공유한다. 실제 복사는 첫 쓰기 시점(08회차 예고).", 15)
    d.banner(p, "복사된 것은 '표' — 공유된 것은 '페이지'")

    # 27 자식의 첫 실행 경로
    p = d.slide("자식의 첫 실행 경로", K.S_CODE,
                "kernel/sched.c:104-142(schedule) · sched.h:171-184(switch_to) · unistd.h:133-144")
    d.flow(p, [("schedule()", "counter=priority로\n가득 — 곧 선택(05)"),
               ("switch_to(nr)", "ljmp — 자식 TSS로"),
               ("CS:EIP", "0x0f : (int 0x80 다음)"),
               ("EAX = 0", "tss.eax 값 그대로"),
               ("_syscall0 뒷부분", "if (__res>=0)\nreturn 0"),
               ("사용자 모드", "ret_from_sys_call\n경유 없음")],
           y=4500, h=3200)
    para(d, p, 1100, 8300, 31500, 5700,
         "schedule(sched.c:104-142)은 state==TASK_RUNNING이고 counter가 가장 큰 태스크를 "
         "고른다 — 자식은 counter = p->priority로 가득 차 있으므로(85행) 곧 선택될 가능성이 높다.\n\n"
         "switch_to의 ljmp가 CPU에게 자식 TSS 전체를 로드시킨다(sched.h:171-184) — EIP는 "
         "int $0x80 다음 명령, CS=0x0f, EAX=0.\n\n"
         "자식은 ret_from_sys_call을 거치지 않는다 — 커널 스택이 비어 있어 되돌아갈 프레임이 "
         "없다(fork.c:81 주석). UNINTERRUPTIBLE(82)은 이 준비가 끝나기 전에 선택되는 일을 막는다.", 15)
    d.banner(p, "자식의 첫 실행 — 커널 명령 하나 없이 TSS에서 사용자로 곧장")

    # ── 상태도 28–29 ──────────────────────────────────────────
    # 28 상태 변화도
    p = d.slide("상태 변화도: task[nr] 슬롯의 탄생", K.S_STATE,
                "kernel/fork.c:77-132 — 새 태스크 슬롯의 생애 초기 · 유지 조건: UNINTERRUPTIBLE 동안 schedule()이 고르지 않는다")
    row1 = [("① 비어 있음", "task[nr]==NULL (이전 상태)", None, K.MUTED),
            ("② 예약됨", "find_empty_process nr 반환(135-147) · 아직 NULL", K.PAPER, K.INK),
            ("③ 페이지 확보", "get_free_page(77) · task[nr]=p(80) — 4 KiB", K.PAPER, K.INK),
            ("④ 부모 복사본", "*p=*current(81) · UNINTERRUPTIBLE(82)", K.PAPER, K.INK)]
    row2 = [("실패 전환 — copy_mem 실패(115-118)", "task[nr]=NULL · free_page(p) · -EAGAIN → ①로", None, K.ORANGE),
            ("⑦ 자식 실행 중", "schedule → switch_to(nr) — 사용자 · EAX=0", K.ORANGE, K.INK),
            ("⑥ 실행 가능", "state=TASK_RUNNING(131) — \"do this last\"", K.TEAL, K.INK),
            ("⑤ 자식 준비", "TSS(92-112) · copy_mem(52-59) · 카운트(120-128) · GDT(129-130)", K.PAPER, K.INK)]
    bw4, gap4 = 7300, 866
    for i, (t, b, fill, col) in enumerate(row1):
        x = 1100 + i * (bw4 + gap4)
        nbox(d, p, x, 4600, bw4, 1300, t, None, fill, col,
             edge=K.MUTED if fill is None else None, s1=15)
        para(d, p, x, 6050, bw4, 1150, b, 10,
             col if fill is not None else K.MUTED)
        if i < 3:
            d.text(p, x + bw4 + 130, 4800, 620, 800, "→", 22, K.TEAL, True)
    for i, (t, b, fill, col) in enumerate(row2):
        x = 1100 + i * (bw4 + gap4)
        nbox(d, p, x, 7900, bw4, 1300, t, None, fill, col,
             edge=K.ORANGE if fill is None else None, s1=13)
        para(d, p, x, 9350, bw4, 1200, b, 10,
             col if fill is not None else K.ORANGE)
        if i < 3:
            d.text(p, x + bw4 + 130, 8100, 620, 800, "←", 22, K.TEAL, True)
    x4 = 1100 + 3 * (bw4 + gap4)
    d.text(p, x4 + bw4 // 2 - 300, 7480, 700, 500, "↓", 18, K.TEAL, True)
    d.text(p, 1300, 7480, 700, 500, "↑", 18, K.ORANGE, True)
    para(d, p, 1100, 11100, 31500, 3200,
         "유지 조건 — ④ 동안 state가 TASK_RUNNING이 아니므로 schedule()의 선택 후보에서 빠진다"
         "(sched.c:127).\n변경 데이터 — 단계마다 task[nr] · state · tss.*(92-112) · ldt[].base(52-55) · "
         "f_count·i_count(120-128) · GDT 항목(129-130)이 이 순서로 갱신된다.\n"
         "실패 전환(왼쪽 ORANGE)은 ⑤ 직전의 copy_mem 실패 한 곳뿐 — 확보했던 페이지와 슬롯을 되돌린다.", 13)
    d.banner(p, "task[nr] 슬롯의 탄생 — NULL에서 실행 중까지 copy_process 한 번으로")

    # 29 두 태스크가 다시 실행되는 지점
    p = d.slide("두 태스크가 다시 실행되는 지점", K.S_STATE,
                "kernel/fork.c:92-97,132 · system_call.s:95,208-219 · sched.h:171-184 — 상태도가 아닌 '호출 순서도'")
    d.text(p, 1100, 4200, 14000, 700, "부모 — 지금 이어지는 길", 17, K.TEAL, True)
    parent = ["copy_process return last_pid — fork.c:132",
              "_sys_fork 219 ret — 어셈블리 종료",
              "_system_call:95 pushl %eax — 반환값 보관",
              "ret_from_sys_call:121 popl %eax",
              "128 iret — 커널 스택 소진",
              "사용자 모드 — EAX = pid(자식 번호)"]
    for i, t in enumerate(parent):
        fill = K.TEAL if i == 5 else K.PAPER
        nbox(d, p, 1100, 5100 + i * 1180, 14000, 1000, t, None, fill, s1=13)
        if i < 5:
            d.text(p, 7800, 5880 + i * 1180, 700, 500, "↓", 16, K.TEAL, True)
    d.text(p, 18200, 4200, 13500, 700, "자식 — 나중에 켜지는 길", 17, K.ORANGE, True)
    child = [("(fork와 별개로 시간이 흐른 뒤) schedule()", "sched.c:104-142 — counter 가득"),
             ("switch_to(nr) — ljmp", "sched.h:171-184 · TSS 전환"),
             ("커널 스택 프레임 없음", "되감을 것이 없다(fork.c:81 주석)"),
             ("사용자 모드 — EAX = 0 · 같은 EIP·ESP 값", "tss.eax(97) · tss.eip(95)")]
    for i, (t, b) in enumerate(child):
        fill = K.ORANGE if i == 3 else K.PAPER
        nbox(d, p, 18200, 5100 + i * 1700, 13500, 1500, t, b, fill, s1=13, s2=12)
        if i < 3:
            d.text(p, 24400, 6480 + i * 1700, 700, 500, "↓", 16, K.ORANGE, True)
    nbox(d, p, 1100, 12100, 30600, 1500,
         "도착점 — 같은 EIP(int $0x80 다음) · 같은 ESP 값 · 같은 EFLAGS",
         "단 논리 주소는 LDT base(nr × 64 MiB)가 달라 다른 선형 주소 → 다른 페이지 테이블 항목(22장)",
         K.INK, K.PAPER, K.PAPER, s1=16, s2=12)
    d.banner(p, "부모는 스택을 되감고(iret), 자식은 TSS에서 곧장 — 도착점은 같은 명령")

    # ── 비교 30 · 32 ──────────────────────────────────────────
    # 30 자원 처리 비교
    p = d.slide("비교: 자식이 받는 자원의 처리 방식", K.S_CMP,
                "kernel/fork.c:56,77-128 · mm/memory.c:177-184 · kernel/exit.c:20-33,106-123 — CPU 모드·태스크 상태와 섞지 않는다")
    d.table(p, 1100, 4400, [7300, 6200, 5600, 6800, 5600], [
        ["자원", "처리 방식", "소스 줄", "자식이 바꾸면 부모에 보이는가", "해제 대칭 (exit.c)"],
        ["task_struct 본문·시그널·시간", "① 값 복사 후 일부 덮어씀", "fork.c:81-91",
         "아니오 — 각자 자기 구조체", "release 20-33: task[i]=NULL · free_page"],
        ["커널 스택·TSS·pid·LDT base", "② 새로 만듦(스택은 비어 있음)", "fork.c:77 · 92-112 · 52-55",
         "아니오", "free_page_tables 106-107 — 표 반납"],
        ["filp[]·pwd·root·executable", "③ 참조 공유 + 카운트 증가", "fork.c:120-128",
         "예 — 같은 struct file의 f_pos 공유", "sys_close 115-117 · iput 118-123"],
        ["사용자 코드·데이터 페이지", "④ 테이블 복사 + R/O 공유", "fork.c:56 · memory.c:177-184",
         "쓰기 불가(08 전까지) — 쓰면 분리", "free_page_tables — 매핑·mem_map 되돌림"],
    ], row_h=2000, size=13)
    d.banner(p, "①복사 ②신규 ③공유+카운트 ④표복사+R/O — 네 방식이 오늘의 요약")

    # 31 f_count
    p = d.slide("f_count가 뜻하는 것", K.S_CODE,
                "include/linux/fs.h:116-122 · kernel/fork.c:120-122 · kernel/exit.c:115-117 — 열린 파일의 오프셋은 프로세스별이 아니다")
    d.code_panel(p, "src/include/linux/fs.h", 116, 122, 1100, 4400, 15200,
                 6400, size=12, caption_extra="struct file — f_count·f_pos")
    d.code_panel(p, "src/kernel/fork.c", 120, 122, 17400, 4400, 15300, 3900,
                 size=13, caption_extra="fork — 카운트만 증가")
    d.code_panel(p, "src/kernel/exit.c", 115, 117, 17400, 8700, 15300, 3900,
                 size=13, caption_extra="do_exit — sys_close로 감소")
    nbox(d, p, 1100, 10950, 7200, 900, "부모 filp[fd]", None, K.TEAL, s1=13)
    nbox(d, p, 9100, 10950, 7200, 900, "자식 filp[fd]", None, K.TEAL, s1=13)
    d.text(p, 4300, 11900, 1000, 500, "↓", 16, K.TEAL, True)
    d.text(p, 12300, 11900, 1000, 500, "↓", 16, K.TEAL, True)
    nbox(d, p, 1100, 12500, 15200, 900,
         "struct file — f_count ≥ 2 · f_pos 하나", None, K.PAPER, s1=13)
    para(d, p, 1100, 13550, 15200, 900,
         "부모의 write → f_pos 이동 → 자식의 다음 read도 그 오프셋부터.", 12)
    d.banner(p, "같은 struct file — 한쪽의 write가 다른 쪽 read 지점을 옮긴다(12회차)")

    # 32 반환값 세 가지
    p = d.slide("비교: fork() 반환값 세 가지", K.S_CMP,
                "kernel/fork.c:79,97,118,132,146 · include/unistd.h:142-143 · init/main.c:179-186")
    d.table(p, 1100, 4500, [4600, 5200, 6600, 7600, 7500], [
        ["경우", "값", "출처 줄", "EAX가 되는 경로", "사용자 코드 분기(main.c:179-186)"],
        ["부모", "last_pid (>0)", "fork.c:132",
         "return → _sys_fork ret → :95 pushl %eax → :121 popl %eax → iret",
         "if (pid>0) — wait(&i)로 자식 대기"],
        ["자식", "0", "fork.c:97 tss.eax",
         "switch_to TSS 복원 — 레지스터 EAX=0",
         "if (!(pid=fork())) — execve·_exit"],
        ["실패", "-1 (errno=EAGAIN 11)", "find_empty_process:146 · get_free_page:79 · copy_mem:118",
         "_syscall0:142-143 errno=-__res; return -1",
         "pid<0 — \"Fork failed in init\" 재시도(190-192)"],
    ], row_h=2400, size=13)
    d.banner(p, "같은 명령에서 세 갈래 — 값을 만드는 곳이 저마다 다르다")

    # ── 시연·캡처 33–42 ───────────────────────────────────────
    # 33 시연 환경
    p = d.slide("시연 환경", K.S_DEMO,
                "lab/ 빌드 · QEMU i386(-s -S) · GDB target remote :1234 — 심볼명은 lab 기준(src와 다를 수 있음)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — 환경 · 중단점",
              "# lab/ QEMU -s -S 기동 후\n"
              "(gdb) target remote :1234\n"
              "(gdb) c              # 셸 프롬프트까지 부팅\n"
              "(gdb) info functions copy_process\n"
              "# 심볼 확인 — lab 빌드는 _ 접두 등 차이 가능\n"
              "(gdb) break copy_process\n"
              "(gdb) c              # 게스트 셸에서 ls 한 번 → 정지", start=13)
    para(d, p, 22000, 4300, 10000, 10100,
         "트리거 — 셸이 명령을 실행할 때마다 fork(copy_process)가 불린다: 게스트에서 "
         "ls 한 번이면 충분하다.\n\n"
         "심볼은 lab 빌드 기준 — info functions 으로 먼저 확인한다.\n\n"
         "부팅·중단점 실패 시 사전 캡처(materials/06-fork/captures 01-04)로 대체한다.\n\n"
         "오늘 시연 — A(34-35) 인자 · B(36-39) 구조체·TSS · C(40-41) 재개 지점.", 15)
    d.banner(p, "오늘 시연 3종 — A 인자 · B 부모/자식 비교 · C 재개 지점")

    # 34 시연 A
    p = d.slide("시연 A: break copy_process — 인자 확인", K.S_DEMO,
                "kernel/fork.c:68-71 · system_call.s:17-31 — 인자에 eax가 없음을 눈으로 확인(실화면 투영)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — 진입과 info args",
              "(gdb) c            # 게스트 셸에서 ls\n"
              "Breakpoint 1, copy_process (nr=3, ebp=…, edi=…,\n"
              "    esi=…, gs=…, none=…, ebx=…, ecx=…, edx=…,\n"
              "    fs=…, es=…, ds=…, eip=0x…, cs=0xf,\n"
              "    eflags=0x…, esp=0x…, ss=0x17)\n"
              "    at kernel/fork.c:68\n"
              "(gdb) info args\n"
              "(gdb) p/x cs        # 0xf — 사용자 코드\n"
              "(gdb) p/x ss        # 0x17 — 사용자 데이터\n"
              "(gdb) p/x eip       # 사용자 주소 — int 0x80 다음\n"
              "(gdb) p/x esp\n"
              "(gdb) p nr          # 빈 task[] 인덱스 (예: 2~4)\n"
              "(gdb) p last_pid    # 곧 자식 pid", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· 인자 17개 — eax가 없다(12장 그림의 실측)\n"
         "· cs=0xf · ss=0x17 — 사용자 세그먼트\n"
         "· none은 커널 주소(_system_call 안 95행)\n"
         "· eip·esp는 사용자 공간 값(셸 바이너리 내부)\n"
         "· nr은 작은 인덱스 · last_pid가 곧 자식 pid\n\n"
         "캡처는 다음 장(35).", 15)

    # 35 캡처 A
    p = d.slide("캡처 A: info args — 17개 인자", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 값은 부팅마다 다름(각주)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) c                      # 게스트 셸에서 ls\n"
                         "Breakpoint 1, copy_process (nr=3, ebp=…, edi=…,\n"
                         "    esi=…, gs=…, none=0x…, ebx=…, ecx=…, edx=…,\n"
                         "    fs=…, es=…, ds=…, eip=0xae2, cs=0xf,\n"
                         "    eflags=0x…, esp=0xf7fe0, ss=0x17)\n"
                         "(gdb) p/x cs ; p/x ss\n"
                         "$1 = 0xf      $2 = 0x17     # 사용자\n"
                         "(gdb) p/x none\n"
                         "$3 = 0x…      # 커널 주소 — _system_call:95\n"
                         "(gdb) p nr ; p last_pid\n"
                         "$4 = 3        $5 = 12       # 곧 자식 pid\n"
                         "# 인자 목록에 eax가 없다 — 12장 스택 그림과 1:1",
                         "01-info-args-17params.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· cs=0xf · ss=0x17 — 사용자\n"
         "· none은 커널 주소(_system_call 안)\n"
         "· eip·esp는 사용자 공간 값\n"
         "· nr은 비어 있던 작은 인덱스(예: 2~4)\n"
         "· last_pid = 곧 자식 pid\n"
         "· 인자에 eax 없음\n\n"
         "12장 17슬롯 그림과 슬롯별로 대조한다.", 14)

    # 36 시연 B-1
    p = d.slide("시연 B-1: 두 task_struct 비교", K.S_DEMO,
                "kernel/fork.c:82-91,120-128 — finish로 반환값(pid)을 받고 부모·자식 필드 대조(실화면 투영)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — finish 후 필드 비교",
              "(gdb) finish\n"
              "# Value returned is 12   ← last_pid = 자식 pid\n"
              "(gdb) set $c = task[nr]      # nr은 시연 A 값\n"
              "(gdb) p current->pid\n"
              "(gdb) p $c->pid              # 다르다 — last_pid\n"
              "(gdb) p $c->father           # == current->pid\n"
              "(gdb) p $c->state            # 0 (TASK_RUNNING)\n"
              "(gdb) p $c->counter ; p $c->priority   # 같다\n"
              "(gdb) p $c->filp[0] ; p current->filp[0]\n"
              "# 같은 주소 — 같은 struct file\n"
              "(gdb) p $c->filp[0]->f_count # ≥ 2", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· pid 다름 · father = 부모 pid(84)\n"
         "· state = 0 — TASK_RUNNING(131)\n"
         "· counter == priority(85)\n"
         "· filp[0] 두 값이 같은 주소(81 포인터 복사)\n"
         "· f_count ≥ 2(120-122)\n\n"
         "구조체 통째 인쇄(p *task[nr])는 크기가 크므로 필드 지정 프린트로 좁힌다.\n\n"
         "캡처는 다음 장(37).", 14)

    # 37 캡처 B-1
    p = d.slide("캡처 B-1: 부모·자식 필드 대조", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 값은 예시(부팅마다 다름)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "필드              current(부모)   task[nr](자식)\n"
                         "------------------------------------------------\n"
                         "pid               4               12\n"
                         "father            1               4      ← 부모 pid\n"
                         "state             0               0      ← RUNNING\n"
                         "counter           6               15     ← = priority\n"
                         "priority          15              15\n"
                         "start_time        1234            5678   ← jiffies(91)\n"
                         "filp[0]           0x1e7c8         0x1e7c8 ← 같은 주소\n"
                         "filp[0]->f_count  3               3      ← fork 후 +1",
                         "02-task-parent-vs-child.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· pid 다름 · father == 부모 pid\n"
         "· state 둘 다 0\n"
         "· counter(자식) = priority(85)\n"
         "· filp[0] 같은 주소 — 하나의 struct file\n"
         "· f_count ≥ 2\n\n"
         "17장(덮어쓰는 필드)·23장(공유 카운트)의 실측에 해당한다.", 14)

    # 38 시연 B-2
    p = d.slide("시연 B-2: tss.eax == 0, tss.eip", K.S_DEMO,
                "kernel/fork.c:92-112 — 자식 TSS에 심어 둔 출발점을 확인한다(실화면 투영)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — 자식 TSS 필드",
              "(gdb) p $c->tss.eax          # 0 (fork.c:97)\n"
              "(gdb) p/x $c->tss.eip        # == 시연 A의 eip\n"
              "(gdb) p/x $c->tss.esp\n"
              "(gdb) p/x $c->tss.cs         # 0xf\n"
              "(gdb) p/x $c->tss.esp0       # == (long)$c + 0x1000\n"
              "(gdb) p/x $c->tss.ldt        # (nr<<4)+(5<<3)\n"
              "(gdb) p/x $c->ldt[2]         # base 비트에 nr*0x4000000\n"
              "(gdb) p/x current->tss.eax\n"
              "# 부모의 tss.eax은 마지막으로 저장된 값 —\n"
              "# 아직 자식으로 전환 전이라 지금 의미 없음", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· tss.eax == 0(97)\n"
         "· tss.eip == 시연 A의 eip(95)\n"
         "· tss.esp0 == task 페이지 + 4096(93)\n"
         "· tss.ldt == (nr<<4)+(5<<3)(111)\n"
         "· ldt[2] base에 nr*0x4000000(52-55)\n\n"
         "current->tss.eax는 전환 전 값 — 해석 주의(§8과 동일 맥락).\n\n"
         "캡처는 다음 장(39).", 14)

    # 39 캡처 B-2
    p = d.slide("캡처 B-2: 자식 TSS", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 값은 예시(부팅마다 다름)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) p $c->tss.eax\n"
                         "$5 = 0\n"
                         "(gdb) p/x $c->tss.eip\n"
                         "$6 = 0xae2      # 시연 A의 eip와 동일\n"
                         "(gdb) p/x $c->tss.esp0\n"
                         "$7 = 0x1c001000 # (long)$c + 0x1000 (93행)\n"
                         "(gdb) p/x $c->tss.cs\n"
                         "$8 = 0xf\n"
                         "(gdb) p/x $c->tss.ldt\n"
                         "$9 = 0x50       # (2<<4)+(5<<3) — nr=2(111행)",
                         "03-child-tss.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· tss.eax = 0\n"
         "· tss.eip == 시연 A eip\n"
         "· tss.esp0 == task[nr] + 4096\n"
         "· tss.ldt == (nr<<4)+(5<<3)\n\n"
         "18·19장(TSS 채움 지도)의 실측 — 이 값들이 switch_to가 복원할 내용물이다.", 14)

    # 40 시연 C
    p = d.slide("시연 C: 자식이 처음 실행되는 순간", K.S_DEMO,
                "sched.h:171-184 — 같은 사용자 EIP에 중단점, 두 번 정지(실화면 투영)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — 사용자 주소 중단점",
              "(gdb) break *0xae2   # 시연 B-2의 tss.eip 값\n"
              "(gdb) delete 1       # copy_process 중단점 해제\n"
              "(gdb) c\n"
              "Breakpoint 2, 0x00000ae2 in ?? ()\n"
              "(gdb) p/x $eax ; p/x $cs\n"
              "# 한 번은 pid, 한 번은 0 — cs=0xf\n"
              "(gdb) c\n"
              "Breakpoint 2, 0x00000ae2 in ?? ()\n"
              "(gdb) p/x $eax ; p/x $cs\n"
              "# 순서는 실행마다 다르다(미리 말한다)\n"
              "# 주의 — 같은 선형 주소를 쓰는 다른 태스크에도\n"
              "# 걸릴 수 있다: $eax·current->pid로 걸러낸다", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "절차\n\n"
         "1. break *<tss.eip 값> — 나머지 delete\n"
         "2. 정지할 때마다 p/x $eax · $cs\n\n"
         "관찰 포인트\n\n"
         "· 부모도 같은 EIP를 지난다 — 걸릴 때마다 $eax: pid / 0\n"
         "· 자식 counter가 가득이라 자식이 먼저인 경우가 많으나 보장 아님(§8)\n\n"
         "캡처는 다음 장(41).", 14)

    # 41 캡처 C
    p = d.slide("캡처 C: 같은 EIP, 다른 EAX", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 정지 순서는 실행마다 다름(§8)")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "1번째 정지\n"
                         "(gdb) p/x $eip\n"
                         "$10 = 0xae2\n"
                         "(gdb) p/x $eax\n"
                         "$11 = 0xc   ← pid 12(부모)\n"
                         "(gdb) p/x $cs\n"
                         "  = 0xf", "04-same-eip-two-eax.png")
    d.placeholder_output(p, 16900, 4150, 15800, 10300,
                         "2번째 정지\n"
                         "(gdb) p/x $eip\n"
                         "$12 = 0xae2   ← 같은 주소\n"
                         "(gdb) p/x $eax\n"
                         "$13 = 0x0     ← 자식\n"
                         "(gdb) p/x $cs\n"
                         "  = 0xf", "04-same-eip-two-eax.png")
    para(d, p, 1100, 14600, 31500, 1700,
         "같은 $eip · 다른 $eax — 핵심 질문에 대한 실물 답. 관찰(EIP·EAX 값)과 추론(TSS 로드 "
         "순서)을 구분해 말한다(다음 장).", 14)

    # 42 관찰 vs 추론
    p = d.slide("관찰 vs 추론", K.S_DEMO,
                "캡처 각주 필수(00-common §7): lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음 · 캡처 날짜")
    d.table(p, 1100, 4400, [15600, 15900], [
        ["관찰 — 캡처 01-04에서 읽은 값", "추론 — 코드로 설명하는 이유"],
        ["cs=0xf · ss=0x17 · eip·esp는 사용자 주소 · none은 커널 주소 (01)",
         "int 0x80 진입 프레임 — CPU와 _system_call:83-94가 push(08장)"],
        ["인자 17개에 eax가 없다 (01)",
         "자식의 EAX는 tss.eax = 0으로 심는다 — fork.c:97 · 부모는 :95 pushl %eax"],
        ["tss.eax==0 · tss.eip==시연 A eip · esp0=task+0x1000 (03)",
         "fork.c:93-97이 TSS에 출발점을 기록 — switch_to가 통째로 복원(sched.h:171-184)"],
        ["filp[0] 같은 주소 · f_count ≥ 2 (02)",
         "*p=*current의 포인터 복사 + f_count++ — fork.c:81, 120-122"],
        ["같은 $eip에서 $eax가 pid / 0 (04)",
         "부모: ret_from_sys_call→iret · 자식: TSS 복원 — 순서는 schedule()·counter에 달림(sched.c:104-142)"],
    ], row_h=1600, size=13)
    d.banner(p, "관찰은 화면에서, 추론은 코드에서 — 서로 바꿔 말하지 않는다")

    # ── 정답·정리 43–48 ───────────────────────────────────────
    # 43 질문의 답
    p = d.slide("질문의 답", K.S_ANS,
                "kernel/system_call.s:95,121,208-219 · fork.c:92-97,132 · sched.h:171-184 — 41장 캡처가 실물 근거")
    d.text(p, 1100, 4200, 31500, 2500,
           "둘 다 int $0x80 다음 명령에서. 부모는 ret_from_sys_call → iret로, "
           "자식은 switch_to → TSS 복원으로 도착하며, 차이는 EAX(pid vs 0)와 "
           "LDT base(선형 주소)뿐이다.", 20, K.ORANGE, True)
    d.text(p, 1100, 7100, 14000, 700, "부모 — 시스템 콜 프레임을 되감는다", 15, K.TEAL, True)
    ans1 = ["copy_process return last_pid (fork.c:132)",
            "_sys_fork ret (system_call.s:219)",
            "_system_call:95 pushl %eax → :121 popl %eax",
            "iret (128) — 사용자 모드, EAX = pid"]
    for i, t in enumerate(ans1):
        nbox(d, p, 1100, 7900 + i * 1150, 14000, 1000, t, None,
             K.TEAL if i == 3 else K.PAPER, s1=13)
    d.text(p, 18200, 7100, 13500, 700, "자식 — TSS에서 곧장 켜진다", 15, K.ORANGE, True)
    ans2 = [("switch_to(nr) — ljmp TSS 전환", "sched.h:171-184 · schedule이 자식 선택"),
            ("TSS 복원 — EAX=0 · EIP=int 0x80 다음", "fork.c:95-97이 심은 값"),
            ("사용자 모드 — ret_from_sys_call 경유 없음", "커널 스택이 비어 있다(fork.c:81 주석)")]
    for i, (t, b) in enumerate(ans2):
        nbox(d, p, 18200, 7900 + i * 1500, 13500, 1350, t, b,
             K.ORANGE if i == 2 else K.PAPER, s1=13, s2=12)
    d.banner(p, "차이는 EAX와 LDT base뿐 — 같은 것은 EIP·ESP 값·EFLAGS(29장 그림)")

    # 44 fork가 하지 않는 일
    p = d.slide("fork가 하지 않는 일", K.S_WRAP,
                "kernel/fork.c:56,77-81,120-128 · mm/memory.c:150-189 — 각 항목에 해당 회차 번호")
    d.table(p, 1100, 4500, [6800, 14200, 10500], [
        ["하지 않는 일", "실제", "언제 다루나"],
        ["메모리 복사", "페이지 테이블만 복사 — 물리 페이지는 R/O 공유", "08회차 — 첫 쓰기 폴트가 그때 복사"],
        ["커널 스택 복사", "비어 있다 — TSS로 사용자 직행", "오늘 20장 · 05회차(TSS) 복습"],
        ["struct file 복사", "공유 + f_count — 같은 f_pos", "12회차 — inode와 함께"],
        ["프로그램 교체", "fork는 복사만 한다 — exec가 다른 이야기", "09회차 — execve"],
    ], row_h=1750, size=14)
    d.banner(p, "fork는 '복제'가 아니라 표 복사 + 참조 세기 + 출발점 심기다")

    # 45 흔한 오해
    p = d.slide("흔한 오해 바로잡기", K.S_WRAP,
                "§8 원문 계승 — 오해/실제 대조 4행")
    d.table(p, 1100, 4400, [11800, 19700], [
        ["오해", "실제"],
        ["\"자식은 copy_process에서 반환해 돌아온다\"",
         "커널 스택이 없다 — switch_to의 TSS 복원으로 사용자 모드에 곧장 도착한다(fork.c:81 주석 · 97)"],
        ["\"fork는 메모리를 복제한다\"",
         "페이지 테이블을 복사하고 물리 페이지는 R/O로 공유(memory.c:177-184) — 복사는 쓰기 시점(08)"],
        ["\"pid = task 인덱스\"",
         "별개다 — pid는 사용자에게 보이는 번호, nr은 task[] 인덱스·GDT·선형 base(fork.c:135-147 · 52)"],
        ["\"*p=*current가 전부 복사하니 파일도 복사된다\"",
         "포인터 복사 = 같은 객체 공유 — f_count·i_count만 증가한다(120-128)"],
    ], row_h=1900, size=14)
    d.banner(p, "'얕은 복사'라고만 말하면 공유 결과를 반드시 덧붙인다(§8)")

    # 46 현대 커널 한 줄
    p = d.slide("현대 커널 한 줄", K.S_WRAP,
                "원본 src/ 밖 — 현대 커널 참고 · 상세 비교는 14회차")
    d.cards(p, [
        ("이름은 남아 있다",
         "현대 Linux의 fork·clone에도\ncopy_process라는 이름과\nCOW(쓰기 시 복사) 원리가\n그대로 남아 있다"),
        ("달라진 것 — 첫 실행",
         "현대: 자식은 ret_from_fork\n커널 스택 프레임으로 돌아간다\n\n0.11: TSS 전환(ljmp)으로\n곧장 사용자 모드"),
        ("상세는 14회차",
         "clone 플래그·자원 공유 선택\nvfork·스레드까지 비교는\n14회차 «종합·실습»에서\n오늘은 이 한 줄뿐"),
    ], y=4400, h=6600)
    d.banner(p, "'Linux 0.11에는 없다/다르다' — 현대 비교는 14회차까지 보류")

    # 47 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답은 강사 구두 공개 후 계획 §6 원문으로 정리 · 관련 시연·캡처 = 34-41장")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1 (관련 18·20·43)",
         "copy_process의 인자에 eax가 없는데 자식의 EAX는 어떻게 정해지는가? 부모의 반환 EAX는?",
         K.TEAL, 15)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2 (관련 16)",
         "*p = *current(fork.c:81) 한 줄이 복사하는 것과 복사하지 않는 것을 하나씩.", K.TEAL, 15)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3 (관련 31)",
         "부모가 fork 직후 write(fd,…)를 두 번 하면 자식의 fd 오프셋은?", K.TEAL, 15)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4 (관련 22·26)",
         "copy_mem이 nr*0x4000000을 base로 쓰는데, 자식이 사용자 주소 0x1000을 읽으면 "
         "선형 주소는? 이 주소의 물리 페이지는 부모와 같은가?", K.TEAL, 15)

    # 48 정리와 다음 회차
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "07회차 — 주소 변환(파트 C «메모리» 시작) · 08회차 — 페이지 폴트·Copy-on-Write")
    d.cards(p, [
        ("진입 경로",
         "_syscall0\n→ sys_call_table[2]\n→ _sys_fork(어셈블리)\n→ copy_process(17인자 = 스택)"),
        ("자원 4종",
         "① 값 복사 — task_struct\n② 새로 만듦 — 스택·TSS·pid·LDT\n③ 참조 공유 — filp·inode\n④ 표 복사 — R/O 페이지"),
        ("첫 실행",
         "자식 — TSS 복원, EAX=0\n커널 스택 없이 사용자 직행\n\n부모 — ret_from_sys_call\n→ iret, EAX=last_pid"),
    ], y=4400, h=6200)
    nbox(d, p, 1100, 11200, 15300, 2600, "07회차 예고 — 주소 변환",
         "nr*0x4000000 base와 copy_page_tables가 만든 표 — 같은 숫자 주소가 두 "
         "프로세스에서 왜 다른 메모리를 가리키는가?", None, K.TEAL, K.TEAL, s1=15, s2=13)
    nbox(d, p, 17200, 11200, 15400, 2600, "08회차 예고 — Copy-on-Write",
         "this_page &= ~2 뒤 자식이 쓰면? — 첫 쓰기 폴트가 그때 복사한다",
         None, K.ORANGE, K.ORANGE, s1=15, s2=13)
    d.banner(p, "fork = 표 복사 + 참조 세기 + TSS에 출발점 심기 — 다음은 그 표를 읽는 법(07)")


if __name__ == "__main__":
    K.run(globals())
