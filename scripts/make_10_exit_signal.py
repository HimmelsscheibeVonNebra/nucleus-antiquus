#!/usr/bin/env python3
"""10회차 덱 — 종료·대기·시그널 (output/10-exit-signal.pptx)

계획: materials/slide-plans/10-exit-signal.md (§2 표 46행 1:1 · §3 앞부분 명세 ·
§4 상태 변화도·처분 분기·스택 전후 명세 · §5 캡처 6종 · §6 이해 확인 · §8 오해 금지).
유형→단계: 배경→S_BG · 코드→S_CODE · 상태도→S_STATE · 비교→S_CMP ·
시연/캡처→S_DEMO · 정답→S_ANS · 확인→S_QUIZ · 정리→S_WRAP.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="10", total=46, slug="10-exit-signal",
    part_no="D", part="«프로그램의 일생»",
    title="10. 종료·대기·시그널",
    question="자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?",
    done=9,
    today_line="자원은 스스로 반납하고 껍데기는 부모가 거둔다 — 종료·대기·시그널",
    next_lines=[
        "09 → 10   fork로 만들고 exec로 갈아끼운 프로그램 → 어떻게 끝나는가 — 06 fork → 09 exec → 10 exit/wait/signal로 «프로세스 생애» 축 완성",
        "10 → 11   do_exit가 부른 iput·sys_close의 뒤편 → 프로세스가 죽어도 남는 것 — 열어둔 파일과 버퍼 캐시",
        "이후 — I/O 축: 11 버퍼 캐시·블록 · 12 파일 시스템 · 13 터미널 (오늘로 파트 D «프로그램의 일생» 마무리)",
    ],
    road_note=("세 단어 _exit(코드) · wait(비교) · signal(상태도·비교) — 오늘은 10단계 전부를 "
               "빠짐없이 밟는다. 핵심 질문의 답은 40·41장 '정답'에서 다시 만난다."),
    STRUCT=dict(
        teal=["proc"],
        today=[("kernel/exit.c", "do_exit·waitpid"),
               ("kernel/signal.c", "do_signal"),
               ("kernel/system_call.s", "ret_from_sys_call")],
        flow="_exit → do_exit → ZOMBIE → waitpid 회수 · Ctrl-C → tty_intr → SIGINT 전달",
        up="↑ exit_code·자식 pid 반환",
        user="sh · fork+wait 셸 · kill(1)",
    ),
)

CHECKS = dict(
    captions={
        5: "src/init/main.c:179-187",
        7: "src/include/linux/sched.h:19-23",
        8: "src/lib/_exit.c:10-13",
        10: "src/kernel/exit.c:102-107",
        11: "src/kernel/exit.c:108-114",
        12: "src/kernel/exit.c:128-135",
        13: "src/kernel/exit.c:83-94",
        15: "src/kernel/exit.c:142-152",
        16: "src/kernel/exit.c:165-170",
        17: "src/kernel/exit.c:184-194",
        22: "src/kernel/exit.c:35-44",
        24: "src/kernel/system_call.s:189-197",
        25: "src/kernel/system_call.s:101-108",
        26: "src/kernel/system_call.s:109-120",
        27: "src/kernel/signal.c:96-103",
        29: "src/kernel/signal.c:104-118",
        32: "src/kernel/signal.c:50-53",
        33: "src/kernel/signal.c:48-61",
        34: "src/kernel/fork.c:84-89",
        35: "src/kernel/chr_drv/tty_io.c:111-120",
    },
    required=[
        "TASK_ZOMBIE", "tell_father", "sys_waitpid", "do_signal",
        "ret_from_sys_call", "send_sig", "sys_kill", "SIGCHLD", "0x10000",
        "WNOHANG", "WUNTRACED", "SIG_DFL", "SIG_IGN", "sa_restorer",
        "SIGKILL", "tty_intr", "INTMASK", "put_fs_long", "bsfl", "btrl",
        "SA_ONESHOT", "SA_NOMASK", "release", "exit_code",
        "TASK_INTERRUPTIBLE", "-ECHILD", "WEXITSTATUS", "kill_session",
        "verify_area", "1<<(SIGCHLD-1)", "(error_code&0xff)<<8", "0x7f",
        "고아", "좀비", "pending", "free_page",
    ],
    prereq=[
        ("fork", "src/init/main.c:179-187"),
        ("exec", "src/kernel/exit.c:102-107"),
        ("task_struct", "src/include/linux/sched.h:19-23"),
        ("SIGCHLD", "src/kernel/exit.c:108-114"),
    ],
    structure_nodes=["system_call.s", "exit.c", "signal.c", "tty_io.c",
                     "sched.c", "fork.c"],
    capture_slides=[20, 37, 39],
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
    # ── 배경 05–09 · 21 · 42–43 ───────────────────────────────
    # 05 9회차 복습: 셸의 3단계 빈칸
    p = d.slide("9회차 복습: 셸이 명령을 실행하는 3단계", K.S_BG,
                "init/main.c:179-187 — init도 같은 구조(fork → wait(&i) 루프) · "
                "오늘 세 단어가 세 번째 칸을 채운다")
    nbox(d, p, 1100, 4400, 9400, 2300, "① fork()",
         "셸이 자기 본사본을 만든다\n부모=셸 · 자식=명령 (06회차)", K.PAPER, s1=17)
    d.text(p, 10750, 5100, 900, 900, ">", 28, K.TEAL, True)
    nbox(d, p, 11800, 4400, 9400, 2300, "② execve()",
         "자식이 /bin/ls 로 갈아끼움\nPID는 그대로 (09회차)", K.PAPER, s1=17)
    d.text(p, 21450, 5100, 900, 900, ">", 28, K.ORANGE, True)
    nbox(d, p, 22500, 4400, 9100, 2300, "③ …끝남?",
         "셸은 프롬프트를 내놓지 않고 기다린다\n'끝남'을 커널이 알리는가? — 오늘",
         None, K.ORANGE, K.ORANGE, K.ORANGE, 17, 12)
    d.code_panel(p, "src/init/main.c", 179, 187, 1100, 7300, 19700, 7300,
                 size=11, caption_extra="init의 fork → wait(&i) 루프")
    para(d, p, 22000, 7300, 9600, 7300,
         "셸의 wait 도 09회차에 본 것과 같은 구다: fork → exec → (기다림).\n\n"
         "init/main.c:179-187 — init 도 첫 자식(/etc/rc 셸)을 wait(&i) 로 "
         "기다린 뒤, 189행부터 로그인 셸을 반복 fork 한다.\n\n"
         "오늘 세 단어가 이 빈칸을 채운다:\n"
         "· _exit — 자식이 끝나는 순간 (10–13장)\n"
         "· wait — 부모가 아는 방법 (15–18장)\n"
         "· signal — 그 사신의 운반 방식 (21–35장)", 15)

    # 06 왜 종료는 두 단계인가
    p = d.slide("왜 종료는 두 단계인가 — 자원 반납과 껍데기 수거", K.S_BG,
                "kernel/exit.c:102-135 · include/linux/sched.h:19-23 — "
                "첫 등장 용어: 좀비(TASK_ZOMBIE=3, §7)")
    para(d, p, 1100, 4300, 31500, 1500,
         "프로세스는 자기 task_struct 페이지(= 커널 스택 그 자체) 위에서 실행 중이다 — "
         "스스로 그 페이지를 해제하면서 실행을 계속할 수 없다. 그래서 둘로 나뉜다.", 16)
    nbox(d, p, 1100, 6000, 14000, 2500, "1단계 — 자원 반납 (스스로)",
         "do_exit (kernel/exit.c:102-129)\n페이지 테이블 · fd · inode · tty 반납", K.TEAL)
    d.text(p, 15300, 6800, 900, 900, ">", 28, K.ORANGE, True)
    nbox(d, p, 16400, 6000, 15200, 2500, "2단계 — 껍데기 수거 (남이)",
         "부모의 sys_waitpid → release (exit.c:19-33)\ntask[i]=NULL · free_page(task_struct)",
         K.ORANGE)
    qbox(d, p, 1100, 9000, 19700, 2900, "좀비(ZOMBIE, TASK_ZOMBIE = 3) — 첫 등장 용어",
         "자원은 반납했지만 task[] 슬롯과 exit_code 를 가진 채 부모의 wait 를 "
         "기다리는 상태. 버그가 아니라 설계다 — 회수 주체를 보장하는 방법이다.",
         K.ORANGE, 15)
    d.code_panel(p, "src/include/linux/sched.h", 19, 23, 22000, 9000, 10600,
                 5100, size=12, caption_extra="태스크 상태 5종")
    para(d, p, 22000, 14300, 10600, 500,
         "STOPPED(4)는 0.11에서 만드는 코드가 없다(18장)", 12, K.MUTED)
    d.banner(p, "오늘 상태 변화도(14장)의 개념 틀 — 반납과 수거를 분리하면 "
                "ZOMBIE 는 필연이 된다")

    # 07 task_struct 오늘 필드
    p = d.slide("task_struct에서 오늘 쓰는 필드", K.S_CODE,
                "include/linux/sched.h:19-23(상태) · 83-89(오늘 필드) — "
                "구조체 전체 모양은 05회차 · 오늘 필드만 색칠")
    d.code_panel(p, "src/include/linux/sched.h", 19, 23, 1100, 4400, 9900,
                 5050, size=12, caption_extra="상태 5종")
    d.code_panel(p, "src/include/linux/sched.h", 83, 89, 11600, 4400, 9900,
                 5600, size=10, caption_extra="오늘 쓰는 필드")
    para(d, p, 1100, 10400, 20400, 700,
         "아래 색칠 = 오늘 상태 변화도(14·31장)·비교(18·23·28장)가 전부 이 필드들로 "
         "표현된다:", 13, K.TEAL, True)
    today_fields = ["state", "signal", "sigaction[32]", "blocked", "exit_code",
                    "pid", "father", "pgrp", "session", "leader"]
    for i, f in enumerate(today_fields):
        x = 1100 + (i % 5) * 4050
        y = 11300 + (i // 5) * 1200
        nbox(d, p, x, y, 3900, 1050, f, None, K.TEAL, s1=13)
    for i, f in enumerate(["start_code…", "filp[NR_OPEN]", "ldt[3]", "tss", "그 외"]):
        nbox(d, p, 1100 + i * 4050, 13700, 3900, 850, f, None, None, K.MUTED,
             s1=12)
    para(d, p, 22000, 4400, 9600, 9900,
         "signal — 32비트 pending 비트맵 (21장)\n"
         "sigaction[32] — 시그널별 처분 (27·28장)\n"
         "blocked — 검사에서 제외할 비트 (26장)\n"
         "exit_code — ZOMBIE가 부모에 남기는 값 (12장)\n"
         "state — RUNNING/ZOMBIE 전환의 당사자 (14장)\n"
         "pid·father — waitpid 탐색의 두 조건 (15장)\n"
         "pgrp·session·leader — tty 시그널·SIGHUP 전파 단위 (35장)\n\n"
         "system_call.s:48-53 은 이 필드들의 오프셋 상수다 — state=0, signal=12, "
         "sigaction=16, blocked=33*16 (26장).", 14)

    # 08 시스템 콜 번호와 라이브러리 경로
    p = d.slide("시스템 콜 번호와 라이브러리 경로", K.S_CODE,
                "lib/_exit.c:10-13 · lib/wait.c:11-16 · include/linux/sys.h:74-75 · "
                "번호는 include/unistd.h — 4회차 진입 경로의 복습")
    d.code_panel(p, "src/lib/_exit.c", 10, 13, 1100, 4400, 15200, 4400,
                 size=12, caption_extra="_exit — int $0x80, __NR_exit=1")
    d.code_panel(p, "src/lib/wait.c", 11, 16, 1100, 9300, 15200, 5300,
                 size=12, caption_extra="wait — waitpid(-1,…,0) 래퍼")
    d.table(p, 22000, 4400, [3400, 6600], [
        ["번호", "kernel/ 함수"],
        ["1", "sys_exit (exit.c:137)"],
        ["7", "sys_waitpid (exit.c:142)"],
        ["37", "sys_kill (exit.c:60)"],
        ["48", "sys_signal (signal.c:48)"],
        ["67", "sys_sigaction (signal.c:63)"],
        ["27 / 29", "sys_alarm / sys_pause (sched.c)"],
    ], row_h=780, size=13)
    d.code_panel(p, "src/include/linux/sys.h", 74, 75, 22000, 10400, 10600,
                 3100, size=12, caption_extra="sys_call_table 앞부분")
    para(d, p, 22000, 13800, 10600, 800,
         "exit() 가 아니라 _exit() — 0.11 libc 에는 atexit·flush 가 없다",
         12, K.MUTED)

    # 09 호출 순서도
    p = d.slide("호출 순서도: _exit에서 schedule까지", K.S_BG,
                "kernel/exit.c:102-135 — 상태 변화도(14장)가 아니라 함수 호출 순서다 · "
                "슬라이드 10–13이 이 순서대로 코드를 읽는다")
    steps = [
        ("sys_exit", "137-140", "(error_code&0xff)<<8"),
        ("do_exit", "102", "여기부터"),
        ("free_page_tables ×2", "106-107", "코드·데이터 세그먼트"),
        ("고아 처리", "108-114", "father=1 · ZOMBIE면 init에 SIGCHLD"),
        ("sys_close ×NR_OPEN", "115-117", "fd 테이블"),
        ("iput ×3", "118-123", "pwd·root·executable"),
        ("tty·수학 정리", "124-127", "leader면 tty pgrp=0"),
        ("kill_session", "128-129", "같은 session 전체 SIGHUP"),
        ("state=ZOMBIE·exit_code", "130-131", "여기서부터 좀비"),
        ("tell_father", "132", "부모의 SIGCHLD 비트"),
        ("schedule", "133", "돌아오지 않는다"),
    ]
    for i, (name, ref, note) in enumerate(steps):
        y = 4300 + i * 880
        d.text(p, 1100, y + 100, 800, 600, f"{i + 1:02d}", 14, K.TEAL, True)
        hot = i in (8, 10)
        nbox(d, p, 1950, y, 12600, 760, name, None,
             K.ORANGE if hot else K.PAPER, s1=14)
        d.text(p, 14850, y + 130, 2100, 500, "exit.c:" + ref, 11, K.MUTED)
        d.text(p, 17100, y + 130, 3700, 600, note, 11,
               K.ORANGE if hot else K.MUTED)
    para(d, p, 22000, 4400, 9600, 9800,
         "읽기 로드맵\n\n"
         "전반부 자원 반납 — 10장\n"
         "고아 입양 — 11장\n"
         "ZOMBIE 전환 — 12장\n"
         "tell_father·release — 13장\n"
         "상태 변화도 — 14장\n"
         "sys_waitpid — 15–17장\n\n"
         "schedule() 뒤의 return (-1) 은\n'just to suppress warnings' —\n"
         "도달하지 않는다(12장).", 14)
    d.banner(p, "반납 순서 = 페이지 테이블 → 고아 → fd → inode → tty·수학 → 세션 → ZOMBIE → 통지 → 양보")

    # ── 코드 10–18 (14는 상태도) ───────────────────────────────
    # 10 do_exit 전반부
    p = d.slide("코드: do_exit 전반부 — 자원 반납", K.S_CODE,
                "kernel/exit.c:102-135 중 앞부분 — 106-107(페이지 테이블) · 108-114(고아, "
                "다음 장) · 115-117(fd) · 118-129는 우측 해설")
    d.code_panel(p, "src/kernel/exit.c", 102, 107, 1100, 4400, 15200, 5150,
                 size=10, caption_extra="free_page_tables ×2 — 7회차 LDT와 연결")
    d.code_panel(p, "src/kernel/exit.c", 115, 117, 1100, 9750, 15200, 3650,
                 size=10, caption_extra="sys_close 루프 — fd 전부")
    for i, t in enumerate(["페이지 테이블 ×2 (106-107)", "fd 전부 (115-117)",
                           "inode ×3 (118-123)"]):
        nbox(d, p, 1100 + i * 4750, 13700, 4650, 800, t, None, K.TEAL, s1=12)
    para(d, p, 17000, 4400, 15600, 9800,
         "106-107 — free_page_tables(get_base(ldt[1·2]), get_limit(0x0f·0x17))\n"
         "코드·데이터 세그먼트 기준 페이지 테이블을 통째로 반납 — "
         "7회차 LDT 관용구 그대로(mm/memory.c:105-131)\n\n"
         "108-114 — 고아 입양: 다음 장(11)에서 코드로\n\n"
         "115-117 — 열린 fd마다 sys_close (6=close)\n\n"
         "118-123 — iput(pwd·root·executable) 후 NULL — "
         "09회차 exec가 남긴 executable도 여기서 놓는다. inode 내부는 12회차\n\n"
         "124-129 — 세션 리더였으면 tty pgrp=0 · kill_session(같은 session 전체 SIGHUP, 46-54)",
         14)

    # 11 고아 입양과 SIGCHLD 재통지
    p = d.slide("코드: do_exit 후반부 (1/2) — 고아 입양과 SIGCHLD 재통지", K.S_CODE,
                "kernel/exit.c:108-114 — 'assumption task[1] is always init'(112) · "
                "상태 변화도(14장)의 유지 조건 'father=1'과 연결")
    d.code(p, "src/kernel/exit.c", 108, 114, wrap_kr(
        "죽는 프로세스의 자식을 찾아\nfather = 1 로 재지정 — init 입양\n\n"
        "이미 ZOMBIE인 자식이면\nsend_sig(SIGCHLD, task[1], priv=1)\n— 새 부모 init 의 비트를 켠다\n\n"
        "priv=1: 권한 검사 없이(22장)", 9500, 15), expl_size=15)
    nbox(d, p, 1100, 12000, 4600, 900, "죽는 프로세스", "do_exit 진행 중",
         K.PAPER, s1=13, s2=11)
    d.text(p, 5850, 12250, 1000, 600, "→", 20, K.MUTED, True)
    nbox(d, p, 6950, 12000, 4600, 900, "자식 (ZOMBIE)", "father = 죽는 pid",
         None, K.ORANGE, K.ORANGE, K.ORANGE, 13, 11)
    d.text(p, 11700, 12250, 1000, 600, "→", 20, K.ORANGE, True)
    nbox(d, p, 12800, 12000, 4600, 900, "father = 1", "init = task[1] 이 거둔다",
         K.ORANGE, s1=13, s2=11)
    d.text(p, 17700, 12250, 1000, 600, "+", 20, K.TEAL, True)
    nbox(d, p, 18800, 12000, 13800, 900, "init->signal |= 1<<16 (SIGCHLD)",
         "send_sig(SIGCHLD, task[1], 1) — 입양받은 init이 waitpid로 거둘 수 있게",
         K.TEAL, s1=13, s2=11)
    d.banner(p, "부모가 먼저 죽어도 좀비는 버려지지 않는다 — init(task[1])이 항상 거둔다")

    # 12 ZOMBIE 전환·tell_father·schedule
    p = d.slide("코드: do_exit 후반부 (2/2) — ZOMBIE 전환·tell_father·schedule",
                K.S_CODE,
                "kernel/exit.c:128-135 — 130 state=ZOMBIE · 131 exit_code 보존 · "
                "132 tell_father · 133 schedule · 134 도달 불가")
    d.code(p, "src/kernel/exit.c", 128, 135, wrap_kr(
        "128-129 — 세션 리더면 kill_session\n같은 session 전체에 SIGHUP(46-54)\n\n"
        "130 — state = TASK_ZOMBIE\n이 태스크는 다시 스케줄되지 않는다\n\n"
        "131 — exit_code = code 보존\n부모가 받을 값(sys_exit 의 <<8 포함)\n\n"
        "132 — tell_father(부모 pid)\n부모의 SIGCHLD 비트(13장)\n\n"
        "133 — schedule(): 양보 후 끝\n134 — return (-1): 경고 억제용", 9500, 15),
        expl_size=15)
    nbox(d, p, 1100, 12600, 9400, 1900, "이후 남는 것",
         "task_struct 페이지 · task[] 슬롯\nstate=3 · exit_code · pid/father",
         K.ORANGE, s1=14, s2=12)
    nbox(d, p, 10900, 12600, 9400, 1900, "없어지는 것",
         "페이지 테이블 · fd · inode\n실행 코드(디스크에만 존재)", None, K.MUTED,
         s1=14, s2=12)
    d.banner(p, "ZOMBIE = 구조체만 남은 상태 — 실행 코드도 페이지도 없다 (상태 변화도 14장)")

    # 13 tell_father와 release
    p = d.slide("코드: tell_father와 release", K.S_CODE,
                "kernel/exit.c:83-94(tell_father) · 19-33(release) — "
                "'release는 항상 남이 호출한다', 유일한 예외는 96-99")
    d.code_panel(p, "src/kernel/exit.c", 83, 94, 1100, 4400, 15200, 8350,
                 size=10, caption_extra="부모 pid 탐색 → SIGCHLD 비트")
    d.code_panel(p, "src/kernel/exit.c", 23, 32, 17000, 4400, 15600, 7300,
                 size=10, caption_extra="release 본체 (19-33) — task[i]=NULL·free_page·schedule")
    para(d, p, 17000, 12000, 15600, 2600,
         "93 — task[i]->signal |= 1<<(SIGCHLD-1): 부모의 bit16 = 0x10000\n"
         "94 — return: 깨우지 않는다. 깨우는 코드는 schedule() 앞부분"
         "(sched.c:117-119)이다(§8)\n"
         "96-99 — 부모를 못 찾으면 printk(\"BAD BAD …\") 후 release(current)",
         13)
    nbox(d, p, 1100, 13100, 7300, 1500, "원칙 — 남이 호출한다",
         "do_exit 자신은 task_struct 페이지를 해제하지 않는다 — 그 위에서 실행 중. "
         "호출자는 부모의 sys_waitpid(176)", K.PAPER, s1=13, s2=11)
    nbox(d, p, 8800, 13100, 7500, 1500, "유일한 예외 — 스스로 release",
         "exit.c:98-99 tell_father 실패 시. 주석 96-97: 'This is not really OK. "
         "Must change it to make father 1'", None, K.ORANGE, K.ORANGE, K.ORANGE,
         13, 11)
    d.banner(p, "tell_father 는 비트만 켜고 끝난다 — 회수도 깨우기도 아직 아니다")

    # 14 상태 변화도 ① (핵심)
    p = d.slide("상태 변화도: RUNNING → ZOMBIE → 소멸", K.S_STATE,
                "kernel/exit.c:102-135·19-33·142-195 · sched.h:19-23 · mm/memory.c:33-37(oom) — "
                "오늘의 핵심 시각자료 ① (캡처 20·정답 40이 같은 그림을 재지시)")
    nbox(d, p, 1100, 4500, 6300, 1800, "TASK_RUNNING (0)",
         "실행 중 · 실행 가능", K.TEAL, s1=16, s2=12)
    d.text(p, 7550, 5100, 900, 800, "→", 24, K.PAPER, True)
    nbox(d, p, 8600, 4500, 6300, 1800, "do_exit 진행 중",
         "여전히 RUNNING — 페이지 테이블·fd·inode 반납 중", K.PAPER, s1=15, s2=11)
    d.text(p, 15050, 5100, 900, 800, "→", 24, K.ORANGE, True)
    nbox(d, p, 16100, 4500, 6300, 1800, "TASK_ZOMBIE (3)",
         "state=3 · exit_code 보존\nslot·task_struct 페이지 유지", K.ORANGE,
         s1=16, s2=11)
    d.text(p, 22550, 5100, 900, 800, "→", 24, K.MUTED, True)
    nbox(d, p, 23600, 4500, 7900, 1800, "소멸 — 존재 안 함",
         "task[i]=NULL · free_page(19-33)", None, K.MUTED, K.MUTED, K.MUTED,
         15, 11)
    d.text(p, 1100, 6450, 7500, 1600,
           "원인: _exit · 치명 시그널 DFL · oom(memory.c:33-37)", 11, K.PAPER)
    d.text(p, 8600, 6450, 7500, 1600,
           "전환 점: exit.c:130 — 자원 반납은 이미 끝난 뒤", 11, K.ORANGE, True)
    d.text(p, 16100, 6450, 15400, 1600,
           "원인: 부모의 sys_waitpid → release (171-178 · 19-33)", 11, K.MUTED)
    d.table(p, 1100, 8000, [6600, 9900, 15000], [
        ["전환", "원인 (함수·줄)", "변경 데이터"],
        ["RUNNING → ZOMBIE", "_exit·치명 시그널 DFL·oom / exit.c:130",
         "페이지 테이블·fd·inode 반납, state=3, exit_code=code"],
        ["ZOMBIE → 소멸", "부모 sys_waitpid → release / 171-178·19-33",
         "cutime/cstime 합산, put_fs_long(code), task[i]=NULL, free_page"],
    ], row_h=900, size=13)
    nbox(d, p, 1100, 11000, 15200, 1100, "유지 — 부모가 wait 하지 않으면 ZOMBIE 영구",
         None, K.PAPER, s1=13)
    nbox(d, p, 17000, 11000, 15600, 1100, "유지 — 부모가 먼저 죽으면 father=1",
         "init이 거둔다 (11장)", K.PAPER, s1=13, s2=11)
    d.outline(p, 1100, 12400, 31500, 2150, K.TEAL, 90)
    d.text(p, 1350, 12520, 30500, 500,
           "부수 상태 — 부모(수거자) 쪽 서브 다이어그램", 13, K.TEAL, True)
    nbox(d, p, 1350, 13150, 8200, 1100, "부모 TASK_INTERRUPTIBLE (1)",
         "sys_waitpid 대기 중 (exit.c:187)", None, K.PAPER, K.PAPER, None, 13, 11)
    d.text(p, 9700, 13380, 900, 700, "→", 20, K.ORANGE, True)
    nbox(d, p, 10700, 13150, 9200, 1100, "① tell_father — 비트만 켠다",
         "signal |= 1<<16 (exit.c:132·93)", K.ORANGE, s1=13, s2=11)
    d.text(p, 20050, 13380, 900, 700, "→", 20, K.TEAL, True)
    nbox(d, p, 21050, 13150, 11200, 1100, "② schedule()이 깨운다 — RUNNING (0)",
         "sched.c:117-119: 시그널 받은 INTERRUPTIBLE 검사", K.TEAL, s1=13, s2=11)
    d.text(p, 29800, 14650, 2800, 450, "Linux 0.11", 9, K.MUTED)

    # 15 sys_waitpid 탐색 조건
    p = d.slide("코드: sys_waitpid — 자식 탐색 조건", K.S_CODE,
                "kernel/exit.c:142-164 — &LAST_TASK 역순 탐색 · pid 필터는 23장 비교와 "
                "같은 색 언어 · verify_area 는 8회차 COW 연결")
    d.code_panel(p, "src/kernel/exit.c", 142, 152, 1100, 4400, 19700, 7850,
                 size=10, caption_extra="verify_area·repeat·father 조건")
    for i, (t, sub, col) in enumerate([
            ("pid > 0", "그 pid 하나만", K.TEAL),
            ("pid == 0", "내 pgrp 와 같은 pgrp", K.TEAL),
            ("pid == -1", "조건 없음 — 전부", K.ORANGE),
            ("pid < -1", "pgrp == -pid", K.TEAL)]):
        nbox(d, p, 1100 + i * 4750, 12500, 4650, 1800, t, sub, col, s1=15, s2=12)
    para(d, p, 22000, 4400, 9600, 9800,
         "150 — &LAST_TASK → &FIRST_TASK 역순\n151-152 — 빈 슬롯·자기 자신 제외\n"
         "153-154 — father != current->pid 제외:\n     내가 낳은 자식만 본다\n\n"
         "155-164 — pid 필터 4갈래(아래 색칠,\n23장 sys_kill 과 같은 색 언어)\n\n"
         "147 — verify_area(stat_addr,4):\n부모 주소 공간에 4바이트 쓰기 전 검사.\n"
         "8회차 write_verify·verify_area 와\n같은 COW 방어(fork.c:24-37).", 14)
    d.banner(p, "대상 결정은 두 겹 — '내 자식(father)' + 'pid 필터' · 통과한 자식의 state 로 다음 분기(16장)")

    # 16 sys_waitpid 상태별 분기
    p = d.slide("코드: sys_waitpid — 상태별 분기: STOPPED·ZOMBIE·기타", K.S_CODE,
                "kernel/exit.c:165-182 — switch 3갈래 · ZOMBIE 갈래가 release 를 부른다"
                "(상태 변화도 14장 전환 ②)")
    d.code_panel(p, "src/kernel/exit.c", 165, 170, 1100, 4400, 9900, 5750,
                 size=12, caption_extra="TASK_STOPPED — WUNTRACED")
    d.code_panel(p, "src/kernel/exit.c", 171, 178, 11600, 4400, 9900, 6150,
                 size=10, caption_extra="TASK_ZOMBIE — 회수의 핵심")
    d.code_panel(p, "src/kernel/exit.c", 179, 182, 1100, 10800, 9900, 3600,
                 size=9, caption_extra="default — 살아 있음 표시")
    para(d, p, 11600, 10800, 21000, 3600,
         "STOPPED(166-170) — WUNTRACED 아니면 continue(건너뜀). 아니면 0x7f 기록 후 pid 반환.\n"
         "ZOMBIE(171-178) — cutime/cstime 합산 → release(*p) → put_fs_long(code) → pid 반환.\n"
         "기타(179-182) — flag=1: '살아 있는 자식이 있다' — 대기 루프(17장)로 넘어간다.",
         14)
    d.banner(p, "release 를 부르는 곳은 여기뿐 — 상태 변화도(14장)의 ZOMBIE → 소멸 전환이 이 안에 있다")

    # 17 sys_waitpid 대기와 재시작
    p = d.slide("코드: sys_waitpid — 대기와 재시작: INTERRUPTIBLE·schedule·-EINTR",
                K.S_CODE,
                "kernel/exit.c:184-194 — 상태 변화도(14장) 부수 상태(부모)의 코드 모습 · "
                "WNOHANG 즉시 반환도 여기")
    d.code(p, "src/kernel/exit.c", 184, 194, wrap_kr(
        "184 — flag=1: 살아 있는 자식 있음\n\n185-186 — WNOHANG 이면 즉시 0\n'거둘 것 없음' 을 뜻한다\n\n"
        "187-188 — TASK_INTERRUPTIBLE 로 자고\nschedule() — CPU 양보\n\n"
        "189 — 깨어나며 SIGCHLD 비트만 지움\n(&= ~(1<<(SIGCHLD-1)))\n\n"
        "190 — 다른 시그널 없으면 goto repeat\n192 — 있으면 -EINTR (다른 시그널이 먼저)\n"
        "194 — 자식이 없으면 -ECHILD", 9500, 15), expl_size=15, size=10)
    d.flow(p, [
        ("repeat 탐색", "exit.c:148-182"),
        ("살아 있는 자식", "flag=1 → WNOHANG? 0 : 잠듦"),
        ("TASK_INTERRUPTIBLE", "187 — schedule() 로 양보"),
        ("SIGCHLD 비트", "189 — 지우고 goto repeat"),
        ("다른 시그널", "192 — -EINTR 반환"),
    ], y=12400, h=2100, title_size=15)
    d.banner(p, "부모의 잠 = TASK_INTERRUPTIBLE — SIGCHLD 로 깨어나도 거둘 ZOMBIE가 없으면 다시 잔다")

    # 18 비교 ① waitpid options
    p = d.slide("비교: waitpid options — 0.11이 정의한 옵션 전부", K.S_CMP,
                "include/sys/wait.h:10-18 · kernel/exit.c:139·166-170·184-188 — "
                "범위: 옵션 3개 전부(0.11 정의가 전부)")
    d.table(p, 1100, 4400, [4600, 8300, 8400, 10200], [
        ["옵션", "동작 (kernel/exit.c)", "반환값·기록값", "0.11 사실"],
        ["0 (기본)", "ZOMBIE가 나올 때까지 잠든다 (187-188)",
         "자식 pid · status에 exit_code", "wait() = waitpid(-1,…,0) (lib/wait.c:15)"],
        ["WNOHANG (wait.h:10)", "살아 있는 자식만 있으면 즉시 0 반환 (185-186)",
         "0 — '거둘 것 없음'", "자식이 아예 없으면 -ECHILD (194)"],
        ["WUNTRACED (wait.h:11)", "STOPPED 자식도 보고 0x7f 기록 (166-170)",
         "자식 pid · status = 0x7f",
         "헤더 주석 'not supported'(wait.h:9) — SIGSTOP을 TASK_STOPPED로 "
         "만드는 코드가 0.11에는 없다"],
    ], row_h=1500, size=14)
    para(d, p, 1100, 11100, 31500, 3200,
         "status 해석 — WEXITSTATUS(s) = (s>>8)&0xFF (wait.h:15). sys_exit 가 "
         "(error_code&0xff)<<8 (exit.c:139)로 밀어 올린 자리다.\n"
         "시그널으로 죽으면 do_exit(1<<(signr-1)) 이라 하위 바이트에 비트 값이 남는다"
         "(signal.c:100, 27장) — 현대 WTERMSIG 와 같다고 단정하지 않는다(§8).\n"
         "WIFSTOPPED(s) = (s&0xFF)==0x7F (wait.h:14) — 설계는 있지만 0.11에서 값을 "
         "만드는 길은 WUNTRACED 갈래뿐이고, 그 값조차 발생하지 않는다.", 15)
    d.banner(p, "옵션은 이 세 가지가 전부 — wait4·waitid는 0.11에 없다 (42장 현대 비교)")

    # ── 시연 A 19–20 ───────────────────────────────────────────
    # 19 시연 A 계획
    p = d.slide("시연 A 계획: 자식 종료와 부모 깨어남", K.S_DEMO,
                "중단점 do_exit·sys_waitpid (tell_father는 static — 심볼 없으면 do_exit 안에서 s/n) · "
                "lab/ QEMU i386 + GDB(target remote) · 셸에서 ls 실행으로 유발 · 원본 수정 없음")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — 중단점 · 관찰",
              "# lab/ make debug → gdb tools/system · target remote :1234 · c\n"
              "(gdb) b do_exit\n"
              "# 셸에 ls 입력 → 자식이 마지막 _exit\n"
              "Breakpoint 1, do_exit (code=0) at kernel/exit.c:102\n"
              "(gdb) p current->pid        # 자식(ls) pid\n"
              "(gdb) p current->father     # 부모(셸) pid\n"
              "(gdb) p current->state      # 0 — 아직 RUNNING(반납 직전)\n"
              "# s/n 진행 → tell_father 호출 확인(132) · 130 통과 후\n"
              "(gdb) p current->state      # 3 — TASK_ZOMBIE\n"
              "(gdb) b sys_waitpid ; c\n"
              "# do_exit → schedule 후 부모가 여기서 깨어난다\n"
              "(gdb) p current->pid        # 이제 부모\n"
              "(gdb) p/x current->signal   # 기대 0x10000 = 1<<16\n"
              "(gdb) p current->state      # 0 — schedule()이 깨움(1→0)", start=12)
    para(d, p, 22000, 4300, 9600, 10100,
         "관찰 대상(§5 A)\n\n"
         "· 자식 state 0 → 3 (TASK_ZOMBIE)\n"
         "· 부모 state 1 → 0 (schedule이 깨움)\n"
         "· 부모 signal = 0x10000 (1<<16, SIGCHLD)\n\n"
         "환경\n\n"
         "· lab/ QEMU i386 + GDB(target remote)\n"
         "· 원본 수정 없음 — 셸 ls 로 유발\n"
         "· 줄 번호·심볼(_ 접두)은 lab 기준\n\n"
         "기대 출력과 캡처 01·02는 다음 장(20).", 14)
    d.banner(p, "수치(비트값)는 코드 추론, 캡처는 실제 관찰 — 슬라이드에서 구분해 말한다(§7·§8)")

    # 20 시연 A 캡처
    p = d.slide("시연 A 캡처: ZOMBIE 전환과 release", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 사전 캡처 준비 전: "
                "예상 출력(실측 아님) · 상태 변화도(14장) ZOMBIE·소멸 칸과 대응 표시")
    d.placeholder_output(p, 1100, 4100, 15200, 10450,
                         "(gdb) b do_exit ; c              # 셸에서 ls 입력\n"
                         "Breakpoint 1, do_exit (code=0) at kernel/exit.c:102\n"
                         "(gdb) p current->pid ; p current->father\n"
                         "$1 = 8    # 자식(ls)   $2 = 5    # 부모(셸)\n"
                         "(gdb) p current->state\n"
                         "$3 = 0    # 아직 RUNNING — 반납 직전\n"
                         "(gdb) b sys_waitpid ; c    # do_exit 종료 후 부모\n"
                         "Breakpoint 2, sys_waitpid (pid=-1, ..., options=0)\n"
                         "(gdb) p/x current->signal\n"
                         "$4 = 0x10000    # 1<<16 = SIGCHLD (tell_father)\n"
                         "(gdb) p current->state\n"
                         "$5 = 0    # schedule()이 깨움 — 부모 state 1→0",
                         "01-do-exit-zombie.png")
    d.placeholder_output(p, 16900, 4100, 15700, 10450,
                         "(gdb) c                  # sys_waitpid 안 — ZOMBIE 자식\n"
                         "Breakpoint 2, sys_waitpid (pid=-1, stat_addr=0x2f8c,\n"
                         "    options=0) at kernel/exit.c:142\n"
                         "(gdb) p (*p)->state\n"
                         "$6 = 3        # TASK_ZOMBIE — 껍데기만 남음\n"
                         "(gdb) p/x (*p)->exit_code\n"
                         "$7 = 0x0      # (0&0xff)<<8 · exit(1)이면 0x100\n"
                         "# release 직전 — cutime/cstime 합산 후 (172-173)\n"
                         "(gdb) p (*p)->pid ; p/x task[8]\n"
                         "$8 = 8\n"
                         "$9 = 0x0      # release 후 task[8] = NULL — 소멸\n"
                         "# 상태 변화도(14장) 전환 ②의 실측",
                         "02-waitpid-release.png")
    d.banner(p, "좌: 자식 state 0→3 · 부모 signal 0x10000 / 우: ZOMBIE의 exit_code → release 후 "
                "task[8]=0x0 — 각주: lab/ QEMU i386 · GDB · 수정 없음", 14800, 14)

    # ── 시그널 21–35 ───────────────────────────────────────────
    # 21 시그널이란
    p = d.slide("시그널이란 무엇인가 — 0.11 기준", K.S_BG,
                "include/linux/sched.h:83(signal) · include/signal.h:12-34(번호표) — "
                "첫 등장 용어: pending(§7) · '메시지가 아니라 플래그'")
    for row, y in ((0, 4900), (1, 6050)):
        for i in range(16):
            bit = 16 + i if row == 0 else i
            x = 1100 + i * 1180
            hot = bit in (1, 16)
            kill = bit == 8
            if hot:
                d.shape(p, x, y, 1130, 950, K.ORANGE)
                col, sz = K.INK, 13
            elif kill:
                d.shape(p, x, y, 1130, 950, K.TEAL)
                col, sz = K.INK, 13
            else:
                d.outline(p, x, y, 1130, 950, K.MUTED, 50)
                col, sz = K.MUTED, 12
            d.text(p, x + 150, y + 220, 850, 520, str(bit), sz, col, True)
    d.text(p, 1100, 4200, 15200, 600,
           "task_struct.signal — int 1개 (sched.h:83) · 윗줄 bit 16 … 31", 12,
           K.TEAL, True)
    d.text(p, 1100, 7100, 8000, 600, "bit 0 … 15 (아랫줄) — 왼쪽이 낮은 비트", 12, K.MUTED)
    d.text(p, 2300, 7750, 6600, 600, "SIGINT=2 → bit1 = 0x2", 13, K.ORANGE, True)
    d.text(p, 9900, 7750, 7000, 600, "SIGKILL=9 → bit8 = 0x80 (32장)", 13, K.TEAL, True)
    d.text(p, 1100, 8500, 15200, 700, "SIGCHLD=17 → bit16 = 0x10000 — 오늘 관찰 값",
           14, K.ORANGE, True)
    para(d, p, 1100, 9400, 19700, 4900,
         "번호표(include/signal.h:12-34) — 1 SIGHUP · 2 SIGINT · 3 SIGQUIT · 9 SIGKILL · "
         "11 SIGSEGV · 14 SIGALRM · 15 SIGTERM · 17 SIGCHLD · 19 SIGSTOP … 22 SIGTTOU.\n"
         "23~32번은 정의 없음 — 비트 자리만 남는다.\n\n"
         "전달은 언제나 두 단계: 보내는 쪽이 비트를 켜고(send_sig·tell_father·tty_intr·alarm), "
         "받는 쪽이 커널에서 사용자로 돌아가는 순간에만 검사한다(ret_from_sys_call).\n"
         "같은 시그널 두 번은 한 번으로 합쳐진다 — 큐가 없다(§8).", 14)
    d.banner(p, "메시지가 아니라 플래그다 — pending = 켜져 있지만 아직 처리 전인 비트(§7)")

    # 22 보내는 쪽: send_sig와 sys_kill
    p = d.slide("코드: 보내는 쪽 — send_sig와 sys_kill", K.S_CODE,
                "kernel/exit.c:35-44(send_sig) · 60-81(sys_kill) · 46-54(kill_session) · "
                "kernel/sched.c:117-119 — 보내는 쪽은 상대를 깨우지 않는다")
    d.code_panel(p, "src/kernel/exit.c", 35, 44, 1100, 4400, 15200, 7300,
                 size=10, caption_extra="권한 3조건 → 비트 OR")
    d.code_panel(p, "src/kernel/exit.c", 65, 79, 17000, 4400, 15600, 9300,
                 size=9, caption_extra="sys_kill 네 갈래 while 루프 (60-81)")
    para(d, p, 1100, 12050, 15200, 900,
         "권한 3조건: priv ∨ current->euid==p->euid ∨ suser() → p->signal |= 1<<(sig-1) (exit.c:39-40)",
         15, K.ORANGE, True)
    para(d, p, 1100, 13200, 15200, 1300,
         "kill_session(46-54): 세션 리더가 죽을 때 같은 session 전체에 SIGHUP — "
         "do_exit:128-129에서 호출(09장 순서도)", 13, K.MUTED)
    para(d, p, 17000, 13900, 15600, 700,
         "깨우는 것은 send_sig가 아니라 schedule() 앞부분(sched.c:117-119)이다(§8)",
         13, K.ORANGE, True)
    d.banner(p, "kill 반환 시점에는 아무 일도 일어나지 않았다 — 비트 하나만 켜졌을 뿐")

    # 23 비교 ② sys_kill pid 4갈래
    p = d.slide("비교: sys_kill의 pid 인자 — 4갈래 전부", K.S_CMP,
                "kernel/exit.c:60-81 — 범위: pid 인자 갈래 전부 · 권한 인자 priv(0/1)와 "
                "retval 누적 방식까지 (15장 waitpid 필터와 같은 색 언어)")
    d.table(p, 1100, 4400, [4200, 9100, 4300, 7900, 6000], [
        ["pid", "대상 (exit.c)", "priv", "필터 조건", "반환"],
        ["pid == 0", "내 pgrp 전체 (65-68)", "1 — 무검사",
         "(*p)->pgrp == current->pid", "오류 누적"],
        ["pid > 0", "그 pid 하나 (69-72)", "0", "(*p)->pid == pid",
         "성공 0"],
        ["pid == -1", "모든 태스크 (73-75)", "0", "조건 없음 — 전부",
         "오류 누적"],
        ["pid < -1", "pgrp == -pid (76-79)", "0", "(*p)->pgrp == -pid",
         "오류 누적"],
    ], row_h=1250, size=14)
    para(d, p, 1100, 11200, 31500, 3200,
         "retval 에 err 를 누적(67-68 등) — 일부 대상이 실패(-EPERM·-EINVAL)해도 나머지에 계속 보내고,"
         "마지막 오류가 반환된다.\n"
         "priv=1(무검사)은 pid==0, 즉 자기 그룹에만 — send_sig 의 권한 3조건(22장)을 건너뛴다.\n"
         "시연 B(36장)는 pid>0 갈래 · Ctrl-C(35장)는 sys_kill 을 거치지 않고 tty_intr 이 "
         "pgrp 조건으로 직접 비트를 켠다 — kill_pg 라는 함수는 0.11에 없다(§8).", 15)
    d.banner(p, "kill(2)의 4갈래가 sys_kill 하나에 다 들어 있다 — 그룹 전용 함수 없음")

    # 24 받는 쪽은 언제 검사하는가
    p = d.slide("받는 쪽은 언제 검사하는가 — 두 곳뿐", K.S_CODE,
                "kernel/system_call.s:12-15(주석 원문) · 189-197(timer_interrupt 꼬리) — "
                "'보내는 즉시'가 아니라 '다음 복귀 시점'")
    auto_pane(d, p, 1100, 4400, 19700, 4000,
              "kernel/system_call.s:12-15 — Linus 주석 (원문)",
              "NOTE: This code handles signal-recognition, which happens\n"
              "every time after a timer-interrupt and after each system\n"
              "call. Ordinary interrupts don't handle signal-recognition,\n"
              "as that would clutter them up totally unnecessarily.",
              start=12)
    nbox(d, p, 1100, 8800, 19700, 1000,
         "① 시스템 콜: call sys_call_table → … → ret_from_sys_call (101)",
         None, K.TEAL, s1=13)
    nbox(d, p, 1100, 9900, 19700, 1000,
         "② 타이머(IRQ 0): _timer_interrupt → do_timer → jmp ret_from_sys_call (197)",
         None, K.ORANGE, s1=13)
    nbox(d, p, 1100, 11000, 19700, 1000,
         "일반 인터럽트(hd·floppy·키보드): 검사 없음 — 'clutter' 때문에 (주석 14-15)",
         None, K.MUTED, K.MUTED, K.MUTED, 13)
    d.code_panel(p, "src/kernel/system_call.s", 189, 197, 22000, 4400, 10600,
                 6300, size=9, caption_extra="타이머도 결국 ret_from_sys_call 로")
    para(d, p, 22000, 11000, 10600, 3400,
         "왜 하필 이 두 곳?\n\n"
         "· 시스템 콜 — 커널 일을 마치고 사용자에게 돌아가는 길\n"
         "· 타이머 — 10ms마다 무조건 오는 길\n\n"
         "이 두 지점만 지나면 사용자 모드 복귀가 보장된다 — 25장의 조건 검사와 이어진다.",
         13)
    d.banner(p, "Ctrl-C가 즉시 반응하지 않을 수 있는 이유 ① — 검사는 복귀 시점에만 존재한다")

    # 25 검사 조건
    p = d.slide("코드: 검사 조건 — 사용자 모드로 돌아갈 때만", K.S_CODE,
                "kernel/system_call.s:101-108 · kernel/sched.c:111-120 — task[0] 제외 · "
                "CS==0x0f · OLDSS==0x17 · '깨우기(schedule)'와 '검사(ret_from_sys_call)' 두 단계")
    d.code_panel(p, "src/kernel/system_call.s", 101, 108, 1100, 4400, 15200,
                 7100, size=12, caption_extra="세 조건을 모두 통과해야 후보")
    for i, (t, sub) in enumerate([("① current != task[0]",
                                    "\"task[0] cannot have signals\" (102)"),
                                   ("② CS == 0x0f",
                                    "복귀할 코드 세그먼트가 사용자 (105)"),
                                   ("③ OLDSS == 0x17",
                                    "복귀할 스택도 사용자 (107)")]):
        nbox(d, p, 1100 + i * 4750, 11900, 4650, 1300, t, sub, K.PAPER,
             s1=13, s2=11)
    para(d, p, 1100, 13400, 15200, 1200,
         "하나라도 아니면 3f 로 점프 — 레지스터 복원 후 iret 만 (121-128)", 13,
         K.MUTED)
    d.code_panel(p, "src/kernel/sched.c", 111, 120, 17000, 4400, 15600, 7300,
                 size=10, caption_extra="schedule() 앞부분 — alarm·깨우기")
    para(d, p, 17000, 12100, 15600, 2500,
         "커널 모드에 머무는 태스크는 이번에 검사받지 않는다 — pending 유지(31장).\n"
         "schedule() 앞부분(117-119)은 시그널 받은 INTERRUPTIBLE 을 RUNNING 으로 "
         "돌릴 뿐 — 실제 처분은 ret_from_sys_call 이 한다.", 13)
    d.banner(p, "Ctrl-C가 즉시가 아닌 이유 ② — 커널 모드에 머무는 동안은 비트가 켜져 있기만 하다")

    # 26 ret_from_sys_call 시그널 선택
    p = d.slide("코드: ret_from_sys_call — 시그널 한 개 선택", K.S_CODE,
                "kernel/system_call.s:109-120 — signal & ~blocked → bsfl → btrl → call do_signal · "
                "한 번에 한 개, 가장 작은 번호 우선")
    d.code(p, "src/kernel/system_call.s", 109, 120, wrap_kr(
        "109-112 — signal & ~blocked\n마스크에 가려지지 않은 비트만\n\n"
        "113 — bsfl: 최하위 set 비트\n= 가장 작은 번호 우선\n114 — 없으면 3f (iret만)\n\n"
        "115 — btrl: 비트를 내린다\npending 은 여기서 사라진다\n\n"
        "116-117 — incl 로 번호 복원(비트→signr)\n118-119 — pushl %ecx; call _do_signal\n\n"
        "인자 13개 = 스택 배치 주석(17-31) 그대로\n— 29장에서 확인", 9500, 14),
        expl_size=14, size=9)
    d.flow(p, [
        ("signal & ~blocked", "후보 비트 (109-112)"),
        ("bsfl", "최하위 = 최소 번호 (113)"),
        ("btrl", "비트 내림 (115)"),
        ("incl", "signr 완성 (117)"),
        ("call do_signal", "한 개만 처리 (118-119)"),
    ], y=12300, h=2150, title_size=15)
    d.banner(p, "예: signal=0x10006, blocked=0 → signr=2 (SIGINT) 먼저 — 나머지는 다음 복귀 때")

    # 27 do_signal 처분 결정
    p = d.slide("코드: do_signal — 처분 결정", K.S_CODE,
                "kernel/signal.c:82-103 · kernel/exit.c:137-140 — 처분(disposition) 용어 첫 등장(§7) · "
                "3갈래 색은 다음 장(28) 분기도와 같다")
    d.code_panel(p, "src/kernel/signal.c", 87, 95, 1100, 4400, 15200, 7300,
                 size=10, caption_extra="sa 포인터·SIG_IGN 판정")
    d.code_panel(p, "src/kernel/signal.c", 96, 103, 17000, 4400, 15600, 6600,
                 size=11, caption_extra="SIG_DFL·SA_ONESHOT")
    nbox(d, p, 1100, 12000, 4650, 2400, "sa_handler == 1",
         "SIG_IGN — 그냥 return\n비트는 이미 내려왔다", K.TEAL, s1=13, s2=12)
    nbox(d, p, 5900, 12000, 4650, 2400, "sa_handler == 0",
         "SIG_DFL — SIGCHLD면 return\n아니면 do_exit(1<<(signr-1))", K.ORANGE,
         s1=13, s2=12)
    nbox(d, p, 10700, 12000, 5600, 2400, "핸들러 주소",
         "SA_ONESHOT이면 NULL 로\n→ 프레임 구성(29-30장)", K.PAPER, s1=13, s2=12)
    para(d, p, 17000, 11300, 15600, 3100,
         "특이점 — do_exit 인자는 시그널 번호가 아니라 비트 값 1<<(signr-1).\n"
         "SIGINT 면 do_exit(2) → exit_code 하위 바이트에 2가 남는다.\n"
         "sys_exit 의 (error_code&0xff)<<8 (exit.c:139)와 대비 — WTERMSIG 해석을 "
         "현대와 동일하게 단정하지 않는다(§8).", 13)
    d.banner(p, "0.11의 SIG_DFL 은 '종료' 하나 — 정지·코어·무시 세분화가 없다(SIGCHLD 예외)")

    # 28 비교 ③ 시그널 처분 (핵심)
    p = d.slide("비교: 시그널 처분 — sa_handler 값 전부", K.S_CMP,
                "include/signal.h:45-46 · kernel/signal.c:82-103 · fs/exec.c:322-323 — "
                "오늘의 핵심 시각자료 ② · 캡처 04(37장)=핸들러 갈래 · 06(39장)=기본 갈래 · Linux 0.11")
    nbox(d, p, 1100, 5600, 5800, 1600, "do_signal(signr) 진입",
         "비트는 이미 내려옴(26장 btrl)", K.PAPER, s1=15, s2=11)
    d.text(p, 7000, 6100, 900, 800, "→", 24, K.TEAL, True)
    nbox(d, p, 8000, 4250, 7600, 1500, "SIG_DFL (0)", "signal.h:45 — 등록 안 한 초기값",
         K.TEAL, s1=14, s2=11)
    nbox(d, p, 8000, 6000, 7600, 1500, "SIG_IGN (1)", "signal.h:46", K.TEAL,
         s1=14, s2=11)
    nbox(d, p, 8000, 7750, 7600, 1500, "핸들러 주소", "sa_handler = 사용자 함수",
         K.ORANGE, s1=14, s2=11)
    d.text(p, 15750, 4650, 700, 700, "→", 20, K.TEAL, True)
    d.text(p, 15750, 6400, 700, 700, "→", 20, K.TEAL, True)
    d.text(p, 15750, 8150, 700, 700, "→", 20, K.ORANGE, True)
    nbox(d, p, 16600, 4250, 16000, 1500,
         "SIGCHLD → return (아무 일 없음) / 그 외 → do_exit(1<<(signr-1))",
         "종료 하나뿐 — 세분화 없음", K.PAPER, s1=13, s2=11)
    nbox(d, p, 16600, 6000, 16000, 1500, "그냥 return — 아무 일 없음",
         "비트는 켜졌다가 do_signal 에서 버려질 뿐 — '막는' 게 아니다(43장 오해)",
         K.PAPER, s1=13, s2=11)
    nbox(d, p, 16600, 7750, 16000, 1500,
         "SA_ONESHOT 이면 sa_handler=NULL → 프레임 구성(29-30장) → iret 로 핸들러",
         "핸들러는 사용자 모드에서 실행된다", K.PAPER, s1=13, s2=11)
    d.table(p, 1100, 9900, [4400, 8000, 7600, 11500], [
        ["처분값", "do_signal 동작", "비트·sa_handler 변화", "등록·해제 경로"],
        ["SIG_DFL (0)", "SIGCHLD: return / 그 외: do_exit (96-101)",
         "비트는 26장에서 이미 내려옴",
         "초기값 · exec 시 32개 전부 리셋(exec.c:322-323)"],
        ["SIG_IGN (1)", "return (94-95)", "같음",
         "sys_signal(signal.c:58-59) · sys_sigaction"],
        ["핸들러 주소", "스택 프레임 구성 후 사용자 모드에서 실행(29장)",
         "ONESHOT이면 NULL(102-103) · blocked |= sa_mask(118)",
         "sys_signal: ONESHOT|NOMASK 고정(56) · sys_sigaction(63-80) · "
         "fork는 sigaction 상속, pending은 상속 안 함(34장) · SIGKILL 등록 거부(32장)"],
    ], row_h=1150, size=12)

    # 29 do_signal 프레임 구성
    p = d.slide("코드: do_signal — 핸들러 프레임 구성", K.S_CODE,
                "kernel/signal.c:104-118 · kernel/system_call.s:17-31 — 인자 13개가 배치 주석과 "
                "1:1 · sa_restorer 용어 첫 등장(§7)")
    d.code_panel(p, "src/kernel/signal.c", 104, 118, 1100, 4400, 9900, 10000,
                 size=9,
                 caption_extra="put_fs_long 순서: restorer→signr→[blocked]→eax→ecx→edx→eflags→old_eip")
    d.code_panel(p, "src/kernel/system_call.s", 17, 31, 11600, 4400, 9900,
                 10000, size=9,
                 caption_extra="스택 배치 주석 — do_signal 인자와 1:1")
    d.banner(p, "인자 13개(eax·ebx·ecx·edx·fs·es·ds·eip·cs·eflags·esp·ss + signr)는 배치 주석 그대로 — "
                "C 매개변수는 스택 사본이라 *(&eip)·*(&esp) 로 쓴다", 14800, 15)

    # 30 스택 전/후 (핵심)
    p = d.slide("그림: 핸들러 호출 전후 사용자 스택", K.S_STATE,
                "kernel/signal.c:104-118 — 오늘의 핵심 시각자료 ③ · 2컷 · "
                "캡처 04(37장)의 x/8wx esp 값과 1:1 · Linux 0.11")
    d.text(p, 1100, 4200, 15200, 600, "① 시스템 콜 직전 — 평범한 사용자 스택",
           16, K.TEAL, True)
    d.outline(p, 1400, 5600, 6800, 950, K.MUTED, 50)
    d.text(p, 1650, 5800, 6300, 550, "… 사용 중인 지역 변수 …", 13, K.MUTED)
    d.outline(p, 1400, 6650, 6800, 950, K.MUTED, 50)
    d.text(p, 1650, 6850, 6300, 550, "(빈 스택 공간)", 13, K.MUTED)
    d.text(p, 8400, 6800, 1600, 700, "esp →", 16, K.PAPER, True)
    nbox(d, p, 1100, 8300, 15200, 900, "SA_NOMASK면 7칸 — blocked 칸이 없다 (105)",
         None, None, K.MUTED, s1=12)
    d.shape(p, 1100, 9400, 15200, 2200, K.INK)
    d.text(p, 1400, 9600, 14600, 500, "do_signal 이 바꾼 것", 14, K.TEAL, True)
    d.text(p, 1400, 10200, 14600, 1300,
           "*(&eip) = sa_handler — iret 의 목적지\n*(&esp) -= longs — 7 또는 8칸(28·32바이트)\n"
           "put_fs_long 8회 — 아래 오른쪽 그림의 순서대로", 13, K.PAPER)
    d.text(p, 17000, 4200, 15600, 600, "② do_signal 직후 — 프레임 8칸 적재",
           16, K.ORANGE, True)
    cells = [("old_eip", "원래 실행 위치 — 최종 복귀점", K.PAPER),
             ("eflags", None, K.PAPER),
             ("edx", None, K.PAPER),
             ("ecx", None, K.PAPER),
             ("eax", None, K.PAPER),
             ("blocked", "SA_NOMASK 아니면 저장(111-112)", None),
             ("signr = 2", "핸들러 첫 인자 — [esp+4]", K.ORANGE),
             ("sa_restorer", "핸들러 ret 목적지 — [esp]", K.ORANGE)]
    for i, (name, note, fill) in enumerate(cells):
        y = 5000 + i * 850
        nbox(d, p, 17300, y, 7300, 790, name, None,
             fill if fill else K.PAPER,
             K.INK if fill else (K.MUTED if fill is None else K.INK),
             None, (K.MUTED if fill is None else None), 13)
        if note:
            d.text(p, 25000, y + 150, 7600, 550, note, 11, K.MUTED)
    d.text(p, 17300, 11800, 1600, 550, "esp →", 15, K.ORANGE, True)
    d.text(p, 19600, 11900, 13000, 500, "esp -= longs*4 (106) → 위에서부터 채운다",
           12, K.ORANGE, True)
    d.flow(p, [
        ("iret", "EIP = sa_handler\nCS = 사용자(0x0f)"),
        ("핸들러 실행", "인자 signr = [esp+4]\n사용자 모드"),
        ("ret", "→ sa_restorer 로"),
        ("sa_restorer", "레지스터 복원\n(사용자 라이브러리 코드)"),
        ("원래 EIP", "old_eip 복귀 —\n'두 번째 복귀'"),
    ], y=12550, h=1950, title_size=14)
    d.banner(p, "커널은 두 번째 복귀(레지스터 복원·old_eip)를 사용자 코드 sa_restorer 에 맡긴다 — "
                "다시 커널로 들어오지 않는다", 14800, 14)

    # 31 상태 변화도 ② 시그널 생애 (핵심)
    p = d.slide("상태 변화도: 시그널 한 개의 생애", K.S_STATE,
                "kernel/exit.c:35-44·83-100 · system_call.s:109-120 · signal.c:82-119 · "
                "sched.c:113-115 · tty_io.c:111-120 — 태스크 상태도(14장)와 별개(혼합 금지) · "
                "Linux 0.11")
    nodes = [("없음", "비트 0", None, K.MUTED, K.MUTED),
             ("pending", "비트 1 — signal |= 1<<(n-1)", K.ORANGE, K.INK, None),
             ("처리 중", "비트 0 (btrl) — do_signal", K.TEAL, K.INK, None),
             ("핸들러 실행 중", "사용자 모드 — 프레임 위에서", K.PAPER, K.INK, None),
             ("복귀", "원래 EIP — sa_restorer 후", K.TEAL, K.INK, None)]
    for i, (t, sub, fill, c1, edge) in enumerate(nodes):
        nbox(d, p, 1100 + i * 6500, 5300, 5500, 1700, t, sub, fill, c1, c2=None,
             edge=edge, s1=16, s2=10)
        if i < 4:
            d.text(p, 1100 + i * 6500 + 5550, 5750, 900, 800, "→", 24, K.TEAL, True)
    tlabels = [("send_sig(exit.c:40)·tell_father(93)\ntty_intr(tty_io.c:119)·alarm(sched.c:114)", 4700),
               ("ret_from_sys_call:115\nbsfl·btrl (113-115)", 11200),
               ("처분값 — 3갈래\n(28장)", 17700),
               ("sa_restorer\n(사용자 코드)", 24200)]
    for text, x in tlabels:
        d.text(p, x, 7250, 4800, 1000, text, 11, K.PAPER)
    d.outline(p, 6600, 8500, 13000, 1400, K.MUTED, 60)
    d.text(p, 6850, 8650, 12500, 1000,
           "blocked 에 가려짐 — signal & ~blocked (110-112) 에서 빠진다.\n"
           "sa_mask·ssetmask 로 해제될 때까지 pending 유지 — 가림이지 처분이 아니다.",
           12, K.MUTED)
    d.text(p, 12300, 7950, 900, 600, "↕", 20, K.MUTED, True)
    d.table(p, 1100, 10200, [5300, 9700, 16500], [
        ["전환", "원인 (줄)", "변경 데이터"],
        ["없음 → pending", "send_sig·tell_father·tty_intr·alarm",
         "signal 비트 1개 ON"],
        ["pending → 처리 중", "ret_from_sys_call (system_call.s:113-117)",
         "signal 비트 OFF (btrl) · signr 확정"],
        ["처리 중 → 핸들러", "do_signal 처분값 (signal.c:93-103)",
         "사용자 ESP·EIP · sa_handler(ONESHOT이면 NULL) · blocked |= sa_mask"],
        ["핸들러 → 복귀", "sa_restorer (사용자 코드)",
         "레지스터·EIP 복원 — 커널 관여 없음"],
    ], row_h=800, size=13)
    d.banner(p, "유지 조건 — 커널 모드에 머무는 동안 pending 유지(25장) · signal 필드와 태스크 state 는 별개다")

    # 32 SIGKILL
    p = d.slide("코드: SIGKILL은 왜 못 잡는가", K.S_CODE,
                "kernel/signal.c:52-53·68-69·24 · kernel/sched.c:24 — 등록 거부 3곳 + _BLOCKABLE · "
                "SIGSTOP은 등록이 거부되지 않는 비대칭")
    d.code_panel(p, "src/kernel/signal.c", 50, 53, 1100, 4400, 15200, 4200,
                 size=11, caption_extra="sys_signal — SIGKILL 거부 → -1")
    d.code_panel(p, "src/kernel/signal.c", 66, 69, 17000, 4400, 15600, 4200,
                 size=11, caption_extra="sys_sigaction — 같은 거부 → -1")
    d.code_panel(p, "src/kernel/signal.c", 22, 25, 1100, 9100, 15200, 3900,
                 size=11, caption_extra="ssetmask — SIGKILL 비트를 깎는다")
    d.code_panel(p, "src/kernel/sched.c", 23, 24, 17000, 9100, 15600, 3100,
                 size=12, caption_extra="_BLOCKABLE — SIGKILL·SIGSTOP 제외")
    para(d, p, 17000, 12500, 15600, 2100,
         "signal(SIGKILL, h) 도 signal(SIGKILL, SIG_IGN) 도 모두 -1 —\n"
         "처분을 바꾸는 경로 자체가 막힌다. SIGSTOP은 이 검사에 없어 등록 가능하지만,\n"
         "TASK_STOPPED 로 만드는 코드가 0.11에는 없다(18장·§8 비대칭).", 13)
    d.banner(p, "결론 — SIGKILL은 어떤 경로로도 SIG_DFL을 벗어나지 못한다 → 항상 do_exit")

    # 33 sys_signal vs sys_sigaction
    p = d.slide("코드: sys_signal vs sys_sigaction", K.S_CODE,
                "kernel/signal.c:48-61 · 63-80 · 15-26(sgetmask·ssetmask) — "
                "두 인터페이스 모두 current->sigaction[] 에 쓴다")
    d.code_panel(p, "src/kernel/signal.c", 48, 61, 1100, 4400, 15200, 9450,
                 size=10, caption_extra="signal — ONESHOT|NOMASK 고정·restorer 인자")
    d.code_panel(p, "src/kernel/signal.c", 70, 80, 17000, 4400, 15600, 7850,
                 size=10, caption_extra="sigaction 꼬리 — sa_mask 조정 (63-80)")
    para(d, p, 17000, 12500, 15600, 2100,
         "signal(): flags = SA_ONESHOT|SA_NOMASK 고정(56) — 한 번 쓰고 기본 복귀,\n"
         "핸들러 중 마스크 저장 없음. restorer 를 세 번째 인자로 받는다(57).\n"
         "sigaction(): 사용자 구조체 통째 복사 — SA_NOMASK 아니면 자기 번호를\n"
         "sa_mask 에 추가(78). blocked 조회·설정은 sgetmask/ssetmask(15-26).", 13)
    d.banner(p, "두 인터페이스, 하나의 저장소 — current->sigaction[32] · 등록 거부·리셋 규칙은 28장 표에")

    # 34 fork·exec·wait와 시그널 상태
    p = d.slide("코드: fork·exec·wait와 시그널 상태", K.S_CODE,
                "kernel/fork.c:84-89 · fs/exec.c:318-323 · kernel/exit.c:187-192 · "
                "kernel/sched.c:144-148 — 생애 사건 4개 타임라인")
    d.code_panel(p, "src/kernel/fork.c", 84, 89, 1100, 4400, 15200, 4750,
                 size=9, caption_extra="fork — 자식 signal=0 (86)")
    d.code_panel(p, "src/fs/exec.c", 318, 323, 17000, 4400, 15600, 4750,
                 size=9, caption_extra="exec — 핸들러 32개 전부 NULL")
    d.code_panel(p, "src/kernel/exit.c", 187, 192, 1100, 9500, 15200, 4750,
                 size=9, caption_extra="waitpid 깨어남 — SIGCHLD만 지움")
    d.code_panel(p, "src/kernel/sched.c", 144, 148, 17000, 9500, 15600, 4750,
                 size=9, caption_extra="pause — 같은 방식으로 잠듦")
    d.banner(p, "fork: pending 은 물려주지 않는다(sigaction[] 은 *p=*current 로 상속) · "
                "exec: 처분 전부 리셋 · wait·pause: 시그널을 받고 깬다", 14800, 14)

    # 35 Ctrl-C 경로
    p = d.slide("코드: Ctrl-C 경로 — 키보드에서 do_exit까지", K.S_CODE,
                "kernel/chr_drv/tty_io.c:19-20(INTMASK) · 111-120(tty_intr) · 200-208(ISIG 분기) — "
                "tty 내부는 13회차 · 'kill_pg는 0.11에 없다'(§8)")
    d.flow(p, [
        ("키보드 IRQ 1", "입력 큐로"),
        ("copy_to_cooked", "INTR_CHAR 만나면\n(tty_io.c:200-203)"),
        ("tty_intr(tty, INTMASK)", "111-120"),
        ("pgrp 일치 태스크", "signal |= 0x2\n(119)"),
        ("ret_from_sys_call", "다음 복귀 시\n(24-26장)"),
        ("do_signal → DFL", "do_exit(1<<1)\n(signal.c:100)"),
    ], y=4300, h=3300, title_size=15)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 111, 120, 1100, 7900, 15200,
                 6700, size=9, caption_extra="tty_intr 본체 — pgrp 일치 태스크에 비트 OR")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 200, 203, 17000, 7900, 15600,
                 4200, size=11, caption_extra="copy_to_cooked — ISIG·INTR_CHAR")
    para(d, p, 17000, 12300, 15600, 2300,
         "INTMASK = 1<<(SIGINT-1) (tty_io.c:19) = 0x2\n"
         "kill_pg 라는 함수는 0.11에 없다 — tty 쪽 함수는 tty_intr(tty_io.c:111)이 전부다.\n"
         "tty 큐·cook 처리 내부는 13회차 «터미널 I/O»에서.", 13)
    d.banner(p, "'어디까지 가는가'의 답 — 비트 하나까지: 실제로 죽는 건 그 프로세스가 다음에 "
                "사용자 모드로 돌아가는 순간이다(41장). 이후 경로는 24-27장과 완전히 같다", 14800, 14)

    # ── 시연 B·C 36–39 ─────────────────────────────────────────
    # 36 시연 B 계획
    p = d.slide("시연 B 계획: kill과 핸들러 프레임", K.S_DEMO,
                "중단점 sys_kill·do_signal · 게스트 테스트 프로그램 signal(SIGINT,h); pause(); — "
                "lab/에 추가한 사용자 바이너리(커널 원본 미수정, §8)")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — kill 전달과 프레임 관찰",
              "# 게스트: signal(SIGINT, handler); pause();  백그라운드 실행\n"
              "# 셸: kill -2 <pid>\n"
              "(gdb) b sys_kill\n"
              "Breakpoint 1, sys_kill (pid=7, sig=2) at kernel/exit.c:60\n"
              "(gdb) p pid ; p sig          # pid>0 갈래(23장)\n"
              "(gdb) finish\n"
              "(gdb) p/x task[N]->signal    # 기대 0x2 = 1<<1 (SIGINT)\n"
              "(gdb) b do_signal ; c\n"
              "Breakpoint 2, do_signal (signr=2, ...) at kernel/signal.c:82\n"
              "(gdb) p signr                # 2\n"
              "(gdb) p/x sa->sa_handler     # 핸들러 주소 (!= 0, 1)\n"
              "# signal.c:118 직전 — 프레임 확인\n"
              "(gdb) p/x esp ; x/8wx esp\n"
              "# 기대 [sa_restorer][2][blocked][eax][ecx][edx][eflags][old_eip]\n"
              "(gdb) finish ; info registers eip   # eip = 핸들러", start=11)
    para(d, p, 22000, 4300, 9600, 10100,
         "절차\n\n"
         "1. 게스트에서 테스트 프로그램 실행\n"
         "   (signal(SIGINT,h) 등록 후 pause)\n"
         "2. 셸에서 kill -2 <pid>\n"
         "3. sys_kill — 인자·비트 확인\n"
         "4. do_signal — signr·sa_handler\n"
         "5. signal.c:118 직전 esp·x/8wx esp\n"
         "6. finish 후 eip = 핸들러 주소\n\n"
         "기대 프레임(30장 그림과 1:1):\n"
         "[sa_restorer, 2, blocked, eax, ecx,\n edx, eflags, old_eip]\n"
         "— SA_NOMASK(signal 등록)면 7칸\n\n"
         "핸들러 없는 기본 경로는 ls 에 kill -9 로 대체.", 13)
    d.banner(p, "테스트 프로그램은 lab/ 추가 바이너리 — 커널 원본 수정이 아님을 캡처 각주에 쓴다(§5·§8)")

    # 37 시연 B 캡처
    p = d.slide("시연 B 캡처: 시그널 비트와 핸들러 프레임", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음(테스트 프로그램은 lab/ 추가 사용자 바이너리) · "
                "캡처 날짜 — 예상 출력(실측 아님)")
    d.placeholder_output(p, 1100, 4100, 15200, 10450,
                         "# 게스트: signal(SIGINT, handler); pause(); 실행\n"
                         "# 셸: kill -2 7\n"
                         "(gdb) b sys_kill ; c\n"
                         "Breakpoint 1, sys_kill (pid=7, sig=2)\n"
                         "    at kernel/exit.c:60\n"
                         "(gdb) p pid ; p sig\n"
                         "$1 = 7    $2 = 2      # pid>0 갈래(23장)\n"
                         "(gdb) finish\n"
                         "(gdb) p/x task[4]->signal      # pid 7 태스크\n"
                         "$3 = 0x2    # 1<<1 — SIGINT pending\n"
                         "# 핸들러 없는 기본 경로(대체):\n"
                         "# ls 에 kill -9 → signal = 0x80 → do_exit",
                         "03-kill-signal-bit.png")
    d.placeholder_output(p, 16900, 4100, 15700, 10450,
                         "(gdb) b do_signal ; c      # kill 직후 복귀 시점\n"
                         "Breakpoint 2, do_signal (signr=2, eax=0, ...)\n"
                         "(gdb) p signr ; p/x sa->sa_handler\n"
                         "$4 = 2    $5 = 0x2a04   # 핸들러 주소\n"
                         "# signal.c:118 직전 — 사용자 스택 프레임\n"
                         "(gdb) p/x esp ; x/8wx esp\n"
                         "0x2f9c: 0x0000299c  0x00000002   # restorer·signr\n"
                         "0x2fa4: 0x00000000  0x00000005   # blocked·eax\n"
                         "0x2fac: 0x00000000  0x00000246   # ecx·edx\n"
                         "0x2fb4: 0x00000202  0x000028f1   # eflags·old_eip\n"
                         "(gdb) finish ; info registers eip\n"
                         "eip 0x2a04   # iret 후 핸들러 — 30장 그림과 1:1",
                         "04-do-signal-frame.png")
    d.banner(p, "우측 프레임 값은 29장 나열 순서·30장 그림·기대 프레임과 1:1 — esp·eip 변화를 확인한다",
            14800, 14)

    # 38 시연 C 계획
    p = d.slide("시연 C 계획: Ctrl-C", K.S_DEMO,
                "참조 수준 — 시간 남을 때만 라이브 · QEMU 콘솔 입력과 GDB 중단이 겹치면 키 입력이 "
                "늦게 전달될 수 있어 사전 캡처(05·06)를 기본으로 게시(§11)")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — tty_intr 조건부 중단·do_signal",
              "# 게스트: sleep 100 (또는 무한 루프) 실행 후 Ctrl-C\n"
              "(gdb) b tty_intr if mask==2\n"
              "# 조건부 중단점이 안 걸리면 b tty_intr + p mask 수동 확인\n"
              "Breakpoint 3, tty_intr (tty=..., mask=2)\n"
              "    at kernel/chr_drv/tty_io.c:111\n"
              "(gdb) p tty->pgrp            # 대상 프로세스 그룹\n"
              "(gdb) p/x task[N]->signal\n"
              "# 기대 0x2 — pgrp == tty->pgrp 인 태스크 전부(118-119)\n"
              "(gdb) b do_signal ; c\n"
              "Breakpoint 4, do_signal (signr=2, ...)\n"
              "(gdb) p sa->sa_handler\n"
              "# 기대 0 (SIG_DFL) — sleep 은 핸들러 없음\n"
              "(gdb) s\n"
              "# 한 단계 뒤 do_exit 진입 — 처분 분기(28장)의 기본 갈래", start=12)
    para(d, p, 22000, 4300, 9600, 10100,
         "절차\n\n"
         "1. 오래 도는 명령(sleep 100 등)\n"
         "2. Ctrl-C 입력\n"
         "3. tty_intr 중단 — pgrp·비트\n"
         "4. do_signal — signr=2·DFL\n"
         "5. do_exit 진입 확인\n\n"
         "관찰 대상(§5 C)\n"
         "· tty->pgrp — 배달 단위\n"
         "· signal = 0x2 (INTMASK)\n"
         "· sa_handler==0 → do_exit\n\n"
         "실패 시 대체 — 사전 캡처(05·06)\n기본 게시 · -serial/콘솔 각주", 13)
    d.banner(p, "처음부터 '사전 캡처 기본'으로 안내한다 — 라이브는 시간이 남을 때만(§5 C-1)")

    # 39 시연 C 캡처
    p = d.slide("시연 C 캡처: tty_intr에서 do_exit까지", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 사전 캡처는 모서리 '기존 기록' "
                "라벨 · QEMU -serial/콘솔 설정 각주")
    d.placeholder_output(p, 1100, 4100, 15200, 10450,
                         "# 게스트: sleep 100 실행 후 Ctrl-C 입력\n"
                         "Breakpoint 3, tty_intr (tty=0x5c78, mask=2)\n"
                         "    at kernel/chr_drv/tty_io.c:111\n"
                         "(gdb) p tty->pgrp\n"
                         "$1 = 35      # sleep 100 태스크의 pgrp\n"
                         "(gdb) p/x task[6]->signal\n"
                         "$2 = 0x2     # INTMASK — pgrp 일치 태스크\n"
                         "(gdb) p task[6]->pgrp\n"
                         "$3 = 35      # 조건: pgrp == tty->pgrp (118)\n"
                         "# 35장 도식의 tty_intr 단계 실관찰\n"
                         "# 사전 캡처 — 모서리 '기존 기록' 라벨\n"
                         "# QEMU -serial/콘솔 설정: 각주",
                         "05-ctrl-c-tty-intr.png")
    d.placeholder_output(p, 16900, 4100, 15700, 10450,
                         "(gdb) b do_signal ; c      # 다음 복귀 시점\n"
                         "Breakpoint 4, do_signal (signr=2, ...)\n"
                         "    at kernel/signal.c:82\n"
                         "(gdb) p signr ; p/x sa->sa_handler\n"
                         "$4 = 2    $5 = 0x0\n"
                         "# sa_handler == 0 → SIG_DFL — 핸들러 없음\n"
                         "(gdb) s      # 한 단계 진행\n"
                         "do_exit (code=2) at kernel/exit.c:102\n"
                         "# do_exit(1<<1) — SIGINT 기본 처분 = 종료\n"
                         "# 분기도(28장) 기본 갈래의 실관찰\n"
                         "# 사전 캡처 — 모서리 '기존 기록' 라벨\n"
                         "# 캡처 05·06 세트로 게시",
                         "06-ctrl-c-do-exit.png")
    d.banner(p, "좌: pgrp 일치 태스크에 signal=0x2 / 우: sa_handler=0 → do_exit(1<<1) — "
                "35장 경로·28장 기본 갈래의 실관찰", 14800, 14)

    # ── 정답 40–41 ─────────────────────────────────────────────
    # 40 질문의 답 1
    p = d.slide("질문의 답 1: 자식이 죽으면 부모는 어떻게 아는가", K.S_ANS,
                "kernel/exit.c:130-132·83-94·142-195 · kernel/sched.c:117-119 — "
                "상태 변화도(14장) 미니 재지시")
    d.flow(p, [
        ("1 — ZOMBIE 로 남는다", "do_exit 에서 자원만 반납하고\nstate=TASK_ZOMBIE (exit.c:130-132)"),
        ("2 — SIGCHLD 비트", "tell_father 가 부모 signal 의\nbit16(0x10000)을 켠다 (exit.c:93)"),
        ("3 — 회수", "waitpid 중 부모가 schedule() 검사로\n깨어나 release·exit_code 수령 (171-178)"),
    ], y=4300, h=3000, title_size=16)
    nbox(d, p, 1100, 7900, 6600, 1200, "자식 RUNNING (0)", None, K.TEAL, s1=13)
    d.text(p, 7900, 8100, 700, 600, "→", 20, K.PAPER, True)
    nbox(d, p, 8800, 7900, 6600, 1200, "자식 ZOMBIE (3)", "do_exit (130)",
         K.ORANGE, s1=13, s2=11)
    d.text(p, 15600, 8100, 700, 600, "→", 20, K.MUTED, True)
    nbox(d, p, 16500, 7900, 6100, 1200, "소멸", "sys_waitpid → release (176)",
         None, K.MUTED, K.MUTED, K.MUTED, 13, 11)
    nbox(d, p, 1100, 9700, 6600, 1200, "부모 INTERRUPTIBLE (1)",
         "sys_waitpid 대기 (187)", None, K.PAPER, K.PAPER, None, 13, 11)
    d.text(p, 7900, 9900, 700, 600, "→", 20, K.ORANGE, True)
    nbox(d, p, 8800, 9700, 6600, 1200, "부모 RUNNING (0)",
         "schedule() 이 깨운다 (sched.c:117-119)", K.TEAL, s1=13, s2=11)
    para(d, p, 16500, 9700, 16100, 1300,
         "전체 그림은 상태 변화도(14장) — 여기선 미니 재지시.", 13, K.MUTED)
    qbox(d, p, 1100, 11400, 31500, 2000, "두 단계를 분리해 말한다 (§8)",
         "tell_father 는 부모를 깨우지 않는다 — 비트만 켠다(exit.c:93). 깨우는 코드는 "
         "schedule() 앞부분(sched.c:117-119)이다. 'SIGCHLD가 부모를 깨운다'고 한마디로 말하지 않는다.",
         K.ORANGE, 14)
    d.banner(p, "자원은 스스로 반납하고 껍데기는 부모가 거둔다 — 두 단계 분리가 답의 뼈대")

    # 41 질문의 답 2
    p = d.slide("질문의 답 2: Ctrl-C는 어디까지 가는가", K.S_ANS,
                "kernel/chr_drv/tty_io.c:111-120·200-208 · system_call.s:101-128 · "
                "signal.c:82-103 — 경로 도식(35장) 축약 재활용")
    d.flow(p, [
        ("키 Ctrl-C", "키보드 IRQ →\ntty 큐"),
        ("tty_intr", "pgrp 일치 태스크\nsignal |= 0x2"),
        ("다음 복귀 때", "ret_from_sys_call —\n사용자 모드면 검사"),
        ("do_signal", "처분값 3갈래\n(28장)"),
        ("핸들러 없으면", "do_exit(1<<1)\n— SIGINT 기본 = 종료"),
    ], y=4300, h=2900, title_size=15)
    qbox(d, p, 1100, 7600, 15200, 3100, "한계 — 말하지 말아야 할 것 (§8)",
         "커널 모드에서 TASK_UNINTERRUPTIBLE 로 잠든 프로세스(디스크 I/O 대기 등)는 "
         "Ctrl-C로 깨우지 못한다 — schedule()의 검사(117-119) 대상이 아니다. "
         "'Ctrl-C는 항상 통한다'고 말하지 않는다.", K.ORANGE, 14)
    qbox(d, p, 17000, 7600, 15600, 3100, "그럼 왜 대개 즉시 반응하는가",
         "셸·sleep 처럼 사용자 모드에서 대기 중이면 다음 틱(IRQ 0, 최대 10ms) 안에 "
         "ret_from_sys_call 을 지나 do_signal 까지 도달한다 — 타이머도 같은 지점으로 합류한다(24장).",
         K.TEAL, 14)
    qbox(d, p, 1100, 11000, 31500, 2400, "답 — 한 문장",
         "Ctrl-C 는 '비트 하나'까지 간다. 실제로 죽는 건 그 프로세스가 다음에 사용자 모드로 "
         "돌아가는 순간(ret_from_sys_call → do_signal → do_exit)이다.",
         K.ORANGE, 15)
    d.banner(p, "핵심 질문 2 종결 — 35장 경로 도식을 축약해 그대로 재활용했다")

    # ── 정리 42–46 ─────────────────────────────────────────────
    # 42 현대 커널과의 차이
    p = d.slide("현대 커널과의 차이 (짧게)", K.S_BG,
                "0.11 ↔ 현대 대비 — 'Linux 0.11에는 없다/다르다' 명시(§1) · 14회차에서 다시 자세히")
    d.table(p, 1100, 4400, [15750, 15750], [
        ["Linux 0.11 (1991)", "현대 커널"],
        ["pending = task_struct.signal 32비트 하나 — 큐 없음",
         "sigpending 큐 + 실시간 시그널(번호 순·누적 전달)"],
        ["핸들러 복귀 = sa_restorer — 사용자 라이브러리 코드",
         "커널 제공 trampoline(vdso/sigreturn) — 커널이 복귀 처리"],
        ["TASK_ZOMBIE (3)", "EXIT_ZOMBIE·EXIT_DEAD 세분화"],
        ["대기 = waitpid — 옵션 2개(18장)", "wait4·waitid·WNOWAIT 등"],
        ["SIGSTOP 등록 가능하지만 정지시키는 코드 없음(32장)",
         "SIGSTOP/SIGCONT 실제 정지·재개"],
    ], row_h=1100, size=14)
    para(d, p, 1100, 11400, 31500, 3000,
         "이름과 번호는 그대로 계승됐다 — SIGKILL=9·SIGINT=2, SIG_DFL/SIG_IGN, do_exit 이라는 "
         "함수 이름까지. 오늘 읽은 '비트 + 복귀 시점 검사' 구조가 현대 시그널의 뼈다.\n"
         "SIGKILL 못 잡기(32장)·좀비의 두 단계 회수(14장)도 원리가 같다.", 15)
    d.banner(p, "현대 이야기는 여기서 접는다 — 14회차 «종합»에서 전체 비교")

    # 43 흔한 오해
    p = d.slide("흔한 오해 네 가지", K.S_BG,
                "kernel/exit.c:35-44 · kernel/signal.c:94-103·104-118 — §8 원문 그대로 오해↔사실")
    qbox(d, p, 1100, 4300, 31500, 2400,
         "오해 1 — 'kill은 프로세스를 즉시 죽인다'",
         "사실 — send_sig 는 p->signal 비트만 켠다(exit.c:40). 대상이 다음에 사용자 모드로 "
         "돌아갈 때 ret_from_sys_call 이 발견해 do_exit 로 끝난다(24-27장).", K.TEAL, 14)
    qbox(d, p, 1100, 6850, 31500, 2400,
         "오해 2 — '좀비는 버그다'",
         "사실 — 설계다. 자원은 반납했으나 exit_code·슬롯을 남겨 부모가 회수하도록 한다(14장). "
         "부모가 wait 하지 않으면 영구히 남는 것도 설계 동작이다.", K.TEAL, 14)
    qbox(d, p, 1100, 9400, 31500, 2400,
         "오해 3 — 'SIG_IGN은 시그널을 막는다'",
         "사실 — 비트는 켜졌다가 do_signal 에서 버려질 뿐이다(94-95). '막는' 역할은 blocked "
         "마스크(26장) — 검사 자체를 건너뛴다.", K.TEAL, 14)
    qbox(d, p, 1100, 11950, 31500, 2400,
         "오해 4 — '핸들러는 커널이 호출한다'",
         "사실 — 커널은 프레임을 쌓고 iret 할 뿐(104-118). 핸들러는 사용자 모드에서 시작하고 "
         "복귀는 사용자 코드 sa_restorer 가 한다(29-30장).", K.TEAL, 14)
    d.banner(p, "네 오해 모두 '비트만 켜고 복귀 시점에 처리한다'는 두 단계 구조에서 나온다")

    # 44 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(45) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "do_exit() 는 왜 자기 task_struct 페이지를 free_page 하지 않는가?", K.TEAL, 15)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2",
         "kill(pid, SIGINT) 가 반환된 직후, 대상 프로세스는 이미 핸들러를 실행했는가?",
         K.TEAL, 15)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3",
         "signal(SIGKILL, h) 의 반환값과 이유는?", K.TEAL, 15)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4",
         "waitpid(-1, &st, WNOHANG) 이 0을 반환했다. 자식 상태는?", K.TEAL, 15)

    # 45 이해 확인 정답
    p = d.slide("이해 확인 정답", K.S_QUIZ,
                "정답과 근거 줄 번호 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "A1",
         "그 페이지 위의 커널 스택에서 지금 실행 중이기 때문. 해제는 다른 태스크가 "
         "sys_waitpid → release() (exit.c:19-33)로 한다. 부모를 못 찾는 예외(exit.c:98-99)만 "
         "자신이 release(current).", K.ORANGE, 14)
    qbox(d, p, 1100, 6850, 31500, 2400, "A2",
         "아니다. send_sig 는 p->signal 비트만 켠다(exit.c:40). 대상이 다음에 시스템 콜/타이머에서 "
         "사용자 모드로 복귀할 때 ret_from_sys_call (system_call.s:109-119)이 검사한다.",
         K.ORANGE, 14)
    qbox(d, p, 1100, 9400, 31500, 2400, "A3",
         "-1. sys_signal 이 signum==SIGKILL 을 거부한다(signal.c:52-53). sigaction 도 같다"
         "(signal.c:68-69). 또한 ssetmask 는 SIGKILL 비트를 깎는다(signal.c:24).", K.ORANGE, 14)
    qbox(d, p, 1100, 11950, 31500, 2400, "A4",
         "살아 있는(ZOMBIE가 아닌) 자식이 최소 하나 있고 거둘 ZOMBIE는 없다 — flag=1 이고 "
         "options & WNOHANG 이면 즉시 0 (exit.c:179-186). 자식이 아예 없으면 -ECHILD(exit.c:194).",
         K.ORANGE, 14)

    # 46 정리와 다음 회차
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "다음 11회차 — read()가 디스크에 실제로 접근하는 때는 언제인가? · "
                "오늘로 파트 D «프로그램의 일생» 마무리")
    d.cards(p, [
        ("오늘 세 함수",
         "do_exit — 자원 반납 후\nZOMBIE 로 남는다\n\nsys_waitpid — 자다가\nSIGCHLD 로 깨어나 회수\n\n"
         "do_signal — 복귀 직전\n처분 결정·프레임 구성"),
        ("11회차 예고",
         "read()가 디스크에 실제로\n접근하는 때는 언제인가?\n\n오늘 do_exit 가 부른\n"
         "iput·sys_close 의 뒤편 —\n버퍼 캐시로 이동\n(fs/buffer.c·blk_drv/)"),
        ("파트 D 마무리",
         "06 fork → 09 exec →\n10 종료·대기·시그널\n\n«프로세스 생애» 축 완성\n\n"
         "다음은 «파일·저장» 축\n(11 버퍼 캐시 · 12 파일 시스템)"),
    ], y=4400, h=8200)
    d.banner(p, "프로세스는 사라져도 열어둔 파일은 남는다 — 11회차 «버퍼 캐시와 블록 장치»")


if __name__ == "__main__":
    K.run(globals())
