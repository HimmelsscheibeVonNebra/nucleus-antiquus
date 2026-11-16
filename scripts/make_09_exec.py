#!/usr/bin/env python3
"""09회차 덱 — exec()와 프로그램 실행 (output/09-exec.pptx)

계획: materials/slide-plans/09-exec.md (§2 표 47행 1:1 · §3 앞부분 명세 ·
§4 다이어그램 명세 · §5 캡처 6종 · §6 이해 확인 · §8 오해 금지).
캡처 미확보 — materials/09-exec/captures/ 확보 전까지 placeholder_output.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="09", total=47, slug="09-exec",
    part_no="D", part="«프로그램의 일생»",
    title="09. exec()와 프로그램 실행",
    question="PID는 그대로인데 프로그램은 어떻게 바뀌는가?",
    done=8,
    today_line="같은 몸(pid·태스크 구조체), 다른 프로그램 — execve",
    next_lines=[
        "08 → 09   fork 뒤 자식의 첫 쓰기 폴트를 봤다 → fork로 만든 자식이 exec로 새 프로그램을 불러오면 — PID는 그대로인데 프로그램은 어떻게 바뀌는가?",
        "09 → 10   exec로 새 프로그램이 첫 명령부터 실행됐다 → 실행한 프로그램이 끝나면 — exit·wait·시그널 (오늘 본 exit.c:106-107 두 줄·sigaction 초기화가 단서)",
        "1회차 입구 — init → fork → execve(\"/bin/sh\")(main.c:179-184) · 06 fork → 07 주소 변환 → 08 COW → 오늘 09 exec → 10 종료",
    ],
    road_note=("10단계 전부를 밟는다 — 질문(02장)에서 정리(47장)까지 빠짐없이. "
               "앞의 로드맵·구조도(03·04장)가 원 '지도' 슬라이드를 대신하며, "
               "미니 지도 범례는 02장의 10단계 띠다."),
    STRUCT=dict(
        teal=["fs"],
        today=[("exec.c", "do_execve · copy_strings"),
               ("a.out.h", "struct exec · ZMAGIC")],
        flow="execve → do_execve → namei·bread → copy_strings → change_ldt → eip[0]·eip[3]",
        up="↑ iret → main()",
        user="sh · 셸이 fork+execve로 명령을 실행",
    ),
)

CHECKS = dict(
    captions={
        5: "src/init/main.c:179-184",
        6: "src/lib/execve.c:7-10",
        7: "src/kernel/system_call.s:35-46",
        8: "src/kernel/system_call.s:200-205",
        12: "src/include/a.out.h:6-15",
        13: "src/fs/exec.c:182-193",
        14: "src/fs/exec.c:204-220",
        15: "src/fs/exec.c:221-225",
        16: "src/fs/exec.c:298-309",
        17: "src/fs/exec.c:226-238",
        18: "src/fs/exec.c:273-284",
        19: "src/fs/exec.c:117-131",
        20: "src/fs/exec.c:318-327",
        21: "src/fs/exec.c:328-332",
        22: "src/fs/exec.c:154-167",
        23: "src/fs/exec.c:168-177",
        24: "src/fs/exec.c:51-63",
        25: "src/fs/exec.c:335-340",
        26: "src/fs/exec.c:341-343",
        27: "src/fs/exec.c:344-346",
        28: "src/mm/memory.c:372-386",
        47: "src/kernel/exit.c:106-107",
    },
    required=[
        "do_execve", "copy_strings", "change_ldt", "create_tables",
        "ZMAGIC", "OMAGIC", "N_TXTOFF", "SEGMENT_SIZE",
        "point of no return", "MAX_ARG_PAGES", "free_page_tables",
        "close_on_exec", "sh_bang", "restart_interp",
        "ENOEXEC", "EACCES", "ENOENT", "ENOMEM", "E2BIG", "eip[3]",
    ],
    prereq=[
        ("fork", "src/init/main.c:179-184"),
        ("free_page_tables", "src/fs/exec.c:328-332"),
        ("do_no_page", "src/mm/memory.c:372-386"),
        ("iret", "src/fs/exec.c:344-346"),
    ],
    structure_nodes=["system_call.s", "exec.c", "a.out.h", "memory.c",
                     "main.c"],
    capture_slides=[36, 38, 40, 41],
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


def auto_pane(d, p, x, y, w, h, caption, text, start=12, cap=K.TEAL):
    lines = text.split("\n")

    def fits(s):
        return (1150 + len(lines) * s * 58 <= h - 150
                and max((K.text_width(l, s) for l in lines), default=0)
                <= (w - 800) * 1.12)
    size = start
    while size > 8 and not fits(size):
        size -= 1
    d.shape(p, x, y, w, h, 0x071A24)
    d.text(p, x + 350, y + 250, w - 700, 600, caption,
           K.fit_size(caption, 12, w - 700, min_size=9), cap)
    d.text(p, x + 350, y + 1150, w - 700, h - 1450, text, size, K.PAPER,
           mono=True)


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


def qbox(d, p, x, y, w, h, tag, body, tag_color, size=14):
    d.shape(p, x, y, w, h, K.INK)
    d.shape(p, x, y, w, 130, tag_color)
    d.text(p, x + 250, y + 320, w - 500, 500, tag, 15, tag_color, True)
    para(d, p, x + 250, y + 950, w - 500, h - 1150, body, size, K.PAPER)


def populate(d):
    # ── 배경 05–11 ────────────────────────────────────────────
    # 05 셸이 명령을 실행하는 두 호출
    p = d.slide("셸이 명령을 실행하는 두 호출", K.S_BG,
                "init/main.c:162-165(argv·envp 배열) · 179-184 · 190-200 — 1회차의 init execve가 오늘의 입구")
    d.code_panel(p, "src/init/main.c", 179, 184, 1100, 4400, 14200, 5100,
                 size=10, caption_extra="init() — 첫 execve(/bin/sh)")
    nbox(d, p, 16900, 4400, 15700, 1350, "셸 (부모, pid 4)",
         "fork() — 06회차", K.TEAL, s1=16, s2=12)
    d.text(p, 24300, 5800, 900, 700, "↓", 22, K.TEAL, True)
    nbox(d, p, 16900, 6550, 15700, 1350, "자식 (pid 7)",
         "셸의 복제 — 아직 같은 프로그램", None, K.MUTED, s1=16, s2=12)
    badge(d, p, 16900, 8100, 15700, 'execve("/bin/ls", argv, envp) — 오늘',
          K.ORANGE, 750, 14)
    d.text(p, 24300, 8900, 900, 700, "↓", 22, K.ORANGE, True)
    nbox(d, p, 16900, 9650, 15700, 1350, "같은 pid 7 — 프로그램은 /bin/ls",
         "몸은 그대로, 내용물 교체", K.ORANGE, s1=16, s2=12)
    para(d, p, 16900, 11300, 15700, 3100,
         "fork는 몸을 복제하고(06) exec는 몸 안의 프로그램을 교체한다(오늘).\n"
         "셸의 기본 패턴: fork → 자식이 execve → 부모는 wait(10회차).", 15)
    para(d, p, 1100, 9900, 14200, 4600,
         "main.c:190-200 — 로그인 셸 루프. 같은 구조로 자식에서 "
         "execve(\"/bin/sh\", argv, envp), 실패하면 _exit.\n"
         "162-165의 argv_rc·envp_rc·argv·envp가 그 인자다.\n\n"
         "1회차에서 'init이 셸을 띄운다'고 본 장면이 정확히 오늘 코드의 호출처 — "
         "슬라이드의 줄 번호는 src 기준이다.", 15)
    d.banner(p, "fork(06) → exec(09) → exit·wait(10) — 파트 D «프로그램의 일생»의 축")

    # 06 사용자 쪽 — lib/execve.c
    p = d.slide("코드: 사용자 쪽 — lib/execve.c 딱 10줄", K.S_BG,
                "lib/execve.c:7-10 · unistd.h:71, 172-183 · linux/sys.h:12, 74-76 — 4회차 write()와 같은 틀")
    d.code_panel(p, "src/lib/execve.c", 7, 10, 1100, 4400, 15200, 3900,
                 size=9, caption_extra="파일 전체 — 실질은 이 한 줄")
    d.code_panel(p, "src/include/unistd.h", 172, 183, 1100, 8600, 15200,
                 7300, size=8, caption_extra="_syscall3 매크로 전개")
    d.text(p, 16900, 4400, 15700, 700, "매크로 전개 — 무엇이 어디에 들어가나",
           16, K.TEAL, True)
    nbox(d, p, 16900, 5200, 15700, 1150, "eax = 11 — __NR_execve (unistd.h:71)",
         "ebx=file · ecx=argv · edx=envp", None, K.PAPER, s1=14, s2=12)
    nbox(d, p, 16900, 6500, 15700, 1000, "int $0x80 — 4회차와 같은 명령",
         None, K.PAPER, s1=14)
    nbox(d, p, 16900, 7650, 15700, 1150, "call _sys_call_table(,%eax,4)",
         "sys.h:74-76 — 11번째 = sys_execve", None, K.PAPER, s1=14, s2=12)
    nbox(d, p, 16900, 8950, 15700, 1150,
         "__res < 0 → errno = -__res; return -1", "실패만 라이브러리가 가공",
         None, K.PAPER, s1=14, s2=12)
    para(d, p, 16900, 10300, 15700, 4100,
         "4회차 write()와 완전히 같은 틀 — 번호(11)와 인자만 다르다.\n"
         "인자 3개라 _syscall3: ebx·ecx·edx. 성공하면 이 라이브러리로 돌아오는 "
         "일은 없다(27장).", 15)
    d.banner(p, "실패한 execve는 -1과 errno로 돌아온다 — 성공하면 돌아오지 않는다")

    # 07 커널 스택 프레임과 eip 포인터
    p = d.slide("커널 스택 프레임과 eip 포인터", K.S_BG,
                "kernel/system_call.s:35-46(오프셋) · 80-93(진입부 복습) — 04회차 시스템 콜 프레임 그림 재사용")
    d.code_panel(p, "src/kernel/system_call.s", 35, 46, 1100, 4400, 15200,
                 7900, size=9, caption_extra="EIP=0x1C · OLDESP=0x28")
    d.text(p, 16900, 4400, 15700, 700, "커널 스택 프레임 — 위가 낮은 주소",
           16, K.TEAL, True)
    frames = [
        ("EBX ECX EDX FS ES DS — 0x00~0x18", "system_call이 push한 인자·세그먼트", None, K.MUTED),
        ("EIP 0x1C — eip[0]", "exec.c:344가 a_entry로 덮어쓴다", K.ORANGE, None),
        ("CS 0x20 — eip[1]", "0x0f — 사용자 코드 세그먼트", None, K.PAPER),
        ("EFLAGS 0x24 — eip[2]", "플래그 — 오늘 건드리지 않음", None, K.PAPER),
        ("OLDESP 0x28 — eip[3]", "exec.c:345가 새 스택 p로 덮어쓴다", K.ORANGE, None),
        ("OLDSS 0x2C", "0x17 — 사용자 데이터 세그먼트", None, K.PAPER),
    ]
    fy = 5150
    for l1, l2, fill, edge in frames:
        nbox(d, p, 16900, fy, 15700, 1080, l1, l2, fill=fill, edge=edge,
             s1=14, s2=11)
        fy += 1230
    para(d, p, 16900, 12700, 15700, 1900,
         "진입부 복습(80-93): push ds·es·fs·edx·ecx·ebx → ds·es=0x10, fs=0x17 → "
         "call _sys_call_table(,%eax,4)", 14)
    para(d, p, 1100, 12500, 15200, 1900,
         "do_execve의 첫 인자 eip는 이 프레임의 EIP 칸 주소(다음 장) — "
         "eip[0..3]은 그 배열에 대한 첨자 접근이다.", 14)
    d.banner(p, "eip[0]=EIP · eip[1]=CS · eip[2]=EFLAGS · eip[3]=OLDESP — 마지막 두 줄(344-345)이 여기에 쓴다")

    # 08 _sys_execve
    p = d.slide("코드: _sys_execve — 저장된 EIP의 주소를 넘긴다", K.S_BG,
                "kernel/system_call.s:200-205 · 오프셋은 35-46(앞장) — 값이 아니라 주소라는 점이 오늘의 열쇠")
    d.code_panel(p, "src/kernel/system_call.s", 200, 205, 1100, 4400, 15200,
                 6200, size=13, caption_extra="6줄 전체 — 어셈블리 스텁")
    nbox(d, p, 16900, 4400, 15700, 1700, "lea EIP(%esp),%eax",
         "EIP = 0x1C — 저장된 EIP 필드의 주소를 계산", K.ORANGE, s1=20, s2=12)
    para(d, p, 16900, 6400, 15700, 7800,
         "pushl %eax — 그 주소가 do_execve의 첫 인자 eip.\n\n"
         "값(EIP 안의 숫자)이 아니라 그 칸의 주소다 — 그래서 do_execve는 커널 스택 "
         "프레임을 직접 읽고 쓸 수 있다(eip[0]=…, eip[3]=…).\n\n"
         "addl $4,%esp(204) — 넘긴 인자 한 개를 스택에서 걷는다.\n"
         "ret(205) — do_execve의 반환값이 eax로 돌아가 ret_from_sys_call로.", 15)
    para(d, p, 1100, 10900, 15200, 3500,
         "sys_call_table[11] = sys_execve(sys.h:74-76) — C가 아니라 어셈블리 스텁인 "
         "이유: 커널 스택 프레임 주소를 C 인자로 넘기는 일이 어셈블리에서는 lea 한 줄이기 "
         "때문이다. sys_fork(208-)도 같은 사정으로 어셈블리다(06회차).", 14)
    d.banner(p, "값이 아니라 주소 — do_execve가 시스템 콜의 복귀점을 통째로 바꾸는 이유")

    # 09 a.out 파일은 어떻게 생겼나
    p = d.slide("a.out 파일은 어떻게 생겼나", K.S_BG,
                "include/a.out.h:6-15 · 42-45 · 92-93 — ZMAGIC: 텍스트는 파일 1024바이트부터")
    d.text(p, 1100, 4150, 14200, 600, "파일 — a.out (ZMAGIC)", 15, K.TEAL, True)
    file_rows = [
        ("struct exec 헤더 — 32바이트(8×4)", K.TEAL, 1000),
        ("패딩 — 텍스트까지 1024B 맞춤", None, 900),
        ("텍스트 — a_text 바이트", K.PAPER, 1900),
        ("데이터 — a_data 바이트", K.PAPER, 1500),
        ("심볼 a_syms · 재배치 a_trsize/a_drsize — 보통 0", None, 1000),
    ]
    fy = 4800
    for l1, fill, h in file_rows:
        nbox(d, p, 1100, fy, 14200, h, l1, None, fill, s1=14)
        fy += h + 150
    d.text(p, 16900, 4150, 15700, 600, "메모리 — 논리 0부터 (64MB 칸 안)",
           15, K.TEAL, True)
    mem_rows = [
        ("텍스트 — 논리 0 · a_entry(보통 0)에서 시작", K.PAPER, 1900),
        ("데이터 — a_data", K.PAPER, 1500),
        ("bss — a_bss · 0으로 채움(26장)", K.PAPER, 1300),
        ("… 빈 공간 · brk ↑ …", None, 1100),
        ("스택 — 64MB 끝에서 아래로(10장)", K.PAPER, 1200),
    ]
    my = 4800
    for l1, fill, h in mem_rows:
        nbox(d, p, 16900, my, 15700, h, l1, None, fill, s1=14)
        my += h + 150
    d.text(p, 15450, 5600, 1000, 800, "→", 22, K.TEAL, True)
    d.text(p, 15450, 7600, 1000, 800, "→", 22, K.TEAL, True)
    d.text(p, 15250, 5050, 1500, 500, "건너뜀", 12, K.ORANGE, True)
    para(d, p, 1100, 12700, 31500, 1900,
         "ZMAGIC(0413) = 텍스트가 1KB(=블록) 경계에서 시작 — 요구 적재가 블록 단위로 읽기 좋다(28장).\n"
         "N_TXTOFF(ZMAGIC) = _N_HDROFF+32 = SEGMENT_SIZE(1024) = BLOCK_SIZE(fs.h:49) — "
         "exec.c:305가 같은지 검사한다.", 15)
    d.banner(p, "a_entry는 보통 0 — eip[0]에 그대로 들어간다(344)")

    # 10 0.11 사용자 주소 공간 한 장
    p = d.slide("0.11 사용자 주소 공간 한 장 — 64MB", K.S_BG,
                "fs/exec.c:39(MAX_ARG_PAGES 32) · 334-346 — 07회차 64MB 칸과 같은 그림, 안의 내용이 오늘 교체된다")
    d.outline(p, 1100, 4300, 15200, 10300, K.LINE, 120)
    d.text(p, 1350, 4400, 14600, 500, "논리 주소 0", 12, K.MUTED)
    seg_rows = [
        ("텍스트 — end_code = a_text", K.TEAL, 1750),
        ("데이터 — end_data = a_text + a_data", K.PAPER, 1400),
        ("bss — brk = end_data + a_bss (힙 시작)", K.PAPER, 1100),
        ("… 빈 공간 — sbrk가 brk을 늘린다 …", None, 2300),
        ("스택 ↓ — start_stack = p & 0xfffff000", K.PAPER, 1100),
        ("인자·환경 페이지 ≤ 32장(128KB) — change_ldt가 64MB 끝에 매핑", K.ORANGE, 1300),
    ]
    sy = 5000
    for l1, fill, h in seg_rows:
        nbox(d, p, 1400, sy, 14600, h, l1, None, fill, s1=14)
        sy += h + 150
    d.text(p, 1400, 14300, 14600, 500, "64MB = 0x4000000 — LDT 데이터 리밋(exec.c:161)",
           12, K.MUTED)
    para(d, p, 16900, 4300, 15700, 10200,
         "오늘 정해지는 네 포인터(exec.c:335-338)\n\n"
         "end_code = a_text\nend_data = a_text + a_data\n"
         "brk = end_data + a_bss — 힙의 시작\n"
         "start_stack = p & 0xfffff000 — 인자 꼭대기\n\n"
         "start_code = 0은 오늘도 없다 — 베이스 자체라 그대로(fork.c:52-55).\n\n"
         "인자·환경 페이지: copy_strings가 page[32]에 쌓고(19장) change_ldt가 이 "
         "영역에 매핑한다(23장) — 64MB 리밋의 맨 끝 128KB.", 15)

    # 11 오늘 읽을 함수 지도
    p = d.slide("오늘 읽을 함수 지도", K.S_BG,
                "호출 순서도 — 상태 변화도가 아님(29·30장) · ● = 오늘 첫 등장 (namei·copy_strings·change_ldt·create_tables)")
    top = [("execve — lib/execve.c:10", "int $0x80 · eax=11"),
           ("_system_call — system_call.s:80", "sys_call_table[11]"),
           ("_sys_execve — system_call.s:200", "lea EIP(%esp)")]
    for i, (l1, l2) in enumerate(top):
        x = 1100 + i * 10575
        nbox(d, p, x, 4400, 9700, 1400, l1, l2, None, K.PAPER, s1=14, s2=12)
        if i < 2:
            d.text(p, x + 9800, 4900, 800, 600, "→", 20, K.TEAL, True)
    d.text(p, 15800, 5850, 900, 600, "↓", 22, K.ORANGE, True)
    nbox(d, p, 7600, 6400, 18200, 1300, "do_execve ● — fs/exec.c:182",
         "오늘의 본체: 검사 → 인자 복사 → 주소 공간 교체 → EIP/ESP 덮어쓰기",
         K.PAPER, s1=16, s2=12)
    d.text(p, 15800, 7750, 900, 600, "↓", 22, K.ORANGE, True)
    fns = [("namei ●", "inode — 199\n(12회차 예고)"),
           ("bread", "헤더 1블록\n221-225"),
           ("copy_strings ●", "page[] 꼭대기\n104-152"),
           ("free_page_tables", "구 공간 반납\n328 (07회차)"),
           ("change_ldt ●", "리밋+put_page\n154-177"),
           ("create_tables ●", "새 스택\n46-70")]
    for i, (l1, l2) in enumerate(fns):
        x = 1100 + i * 5320
        nbox(d, p, x, 8300, 4880, 1600, l1, l2, None,
             K.TEAL if "●" in l1 else K.PAPER, s1=14, s2=11)
    nbox(d, p, 1100, 10200, 15200, 1300,
         "eip[0] = ex.a_entry · eip[3] = p — return 0 (344-346)",
         None, K.ORANGE, s1=15)
    d.text(p, 16600, 10550, 900, 600, "→", 22, K.ORANGE, True)
    nbox(d, p, 17700, 10200, 13800, 1300,
         "iret — 새 0x0f:a_entry fetch → #PF → do_no_page 적재 (mm/memory.c:365 · 08회차)",
         None, K.TEAL, s1=13)
    para(d, p, 1100, 11900, 31500, 1000,
         "같은 do_execve 안의 #! 재시작(restart_interp, 17-18장)은 이 그림의 되돌이 화살이다.", 14)
    d.banner(p, "execve → _sys_execve → do_execve → … → eip[0]·eip[3] → ret 0이면 main()부터")

    # ── 코드 12–28 ────────────────────────────────────────────
    # 12 struct exec와 매직
    p = d.slide("코드: struct exec와 매직", K.S_CODE,
                "include/a.out.h:6-15 · 21-28 · 92-93 · fs/exec.c:305 · linux/fs.h:49 — 헤더 32B가 실행 파일의 설계도")
    d.code_panel(p, "src/include/a.out.h", 6, 15, 1100, 4400, 14200, 6800,
                 size=9, caption_extra="struct exec — 필드 8개")
    d.code_panel(p, "src/include/a.out.h", 92, 93, 1100, 11400, 14200, 3100,
                 size=11, caption_extra="i386 정의 — 1KB 세그먼트")
    d.code_panel(p, "src/include/a.out.h", 21, 28, 16900, 4400, 15700, 5800,
                 size=9, caption_extra="매직 3가지 — 8진수")
    para(d, p, 16900, 10500, 15700, 4100,
         "0413(8진수) = 0x10B — ZMAGIC만 exec가 받는다(299).\n"
         "a_syms: 심볼 길이 — 크기 검사(301)에만 등장.\n"
         "a_trsize·a_drsize: 재배치 — 0이어야 한다(299).\n"
         "a_entry: 첫 명령 논리 주소 — eip[0]에 들어간다(344).", 14)
    d.banner(p, "N_TXTOFF(ZMAGIC) = _N_HDROFF+32 = SEGMENT_SIZE = 1024 = BLOCK_SIZE — exec.c:305 검사")

    # 13 do_execve 진입
    p = d.slide("코드: do_execve 진입", K.S_CODE,
                "fs/exec.c:182-203 · count() 75-85 — eip만 커널 포인터, filename·argv·envp는 fs로 읽는 사용자 포인터")
    d.code_panel(p, "src/fs/exec.c", 182, 193, 1100, 4400, 14200, 8000,
                 size=9, caption_extra="선언부 — 12줄")
    d.code_panel(p, "src/fs/exec.c", 195, 202, 16900, 4400, 15700, 5800,
                 size=9, caption_extra="진입 검사 — 8줄")
    para(d, p, 16900, 10500, 15700, 4100,
         "(0xffff & eip[1]) != 0x000f — CS가 사용자(0x0f)가 아니면 panic(195-196). "
         "커널 모드 호출은 프레임에 OLDESP가 없다. 1회차 move_to_user_mode가 만든 값.\n\n"
         "page[32] = 0 초기화(197-198).\n"
         "p = 4096×32-4 = 128KB-4(193) — 꼭대기 시작.\n"
         "namei(199) 실패 → ENOENT · count(75-85)로 argc·envc.", 14)
    nbox(d, p, 1100, 12700, 7000, 1500, "page[0..31] = 0",
         "인자·환경 쌓을 커널 페이지", None, K.MUTED, s1=15, s2=11)
    nbox(d, p, 8400, 12700, 7000, 1500, "p = 128KB - 4",
         "page[31] 꼭대기에서 4B 아래", None, K.PAPER, s1=15, s2=11)
    d.banner(p, "첫 인자 eip — 커널 스택 프레임 포인터. 나머지 셋은 사용자 포인터(fs 세그먼트)")

    # 14 권한 검사와 setuid
    p = d.slide("코드: 권한 검사와 setuid", K.S_CODE,
                "fs/exec.c:204-220 · include/errno.h — 실행 비트 없음은 ENOEXEC, EACCES가 아니다(§8)")
    d.code_panel(p, "src/fs/exec.c", 204, 220, 1100, 4400, 19700, 9600,
                 size=8, caption_extra="restart_interp부터 17줄")
    para(d, p, 22000, 4400, 10000, 10000,
         "S_ISREG 아니면 EACCES(205-207) — 디렉터리·장치 파일.\n\n"
         "i >>= 6(213): 호출자=소유자 → 소유자 비트.\n"
         ">>= 3(215): 그룹 일치 → 그룹 비트.\n"
         "아니면 기타 비트 — 셋 중 하나만 본다.\n\n"
         "실행 비트(i&1) 없고 (파일에 x 비트 && suser())도 아니면 → ENOEXEC(216-219).\n\n"
         "S_ISUID/S_ISGID → e_uid/e_gid = 파일 소유자(210-211) — 339-340에서 반영.", 14)
    d.banner(p, "정규 파일 아님 → EACCES · 실행 비트 없음 → ENOEXEC — 서로 다른 errno다")

    # 15 헤더 읽기
    p = d.slide("코드: 헤더 읽기 — bread와 첫 블록", K.S_CODE,
                "fs/exec.c:221-225 · include/linux/fs.h:49 — ZMAGIC 배치라 헤더는 항상 1블록째(09장)")
    d.code_panel(p, "src/fs/exec.c", 221, 225, 1100, 4400, 19700, 4800,
                 size=11, caption_extra="5줄 — 첫 블록 읽기")
    para(d, p, 22000, 4400, 9500, 4600,
         "bread(i_dev, i_zone[0]) — 파일의 첫 직접 블록.\n\n"
         "ex = *(struct exec *)bh->b_data(225) — 버퍼에서 32B 복사.\n\n"
         "실패(NULL) → EACCES(222) — 32장 비교 ②.", 14)
    nbox(d, p, 1100, 9600, 4600, 1400, "블록 0", "헤더 32B + 패딩",
         K.TEAL, s1=14, s2=11)
    for i in range(3):
        nbox(d, p, 6000 + i * 5000, 9600, 4800, 1400, f"블록 {i + 1}",
             "a_text 앞부분", None, K.PAPER, s1=14, s2=11)
    nbox(d, p, 21100, 9600, 11500, 1400, "… 이어서 a_text·a_data",
         "요구 적재 대상 — 오늘은 안 읽는다", None, K.MUTED, s1=14, s2=11)
    para(d, p, 1100, 11400, 19700, 3000,
         "a.out(ZMAGIC)은 헤더가 항상 첫 블록에 — N_TXTOFF=BLOCK_SIZE 검사(305)가 보장한다.\n"
         "brelse는 #! 분기(236)와 정상 경로(298)에서 각각 — 헤더 검사가 끝나면 즉시 버퍼를 돌려준다.", 15)
    d.banner(p, "exec가 디스크에서 읽는 것은 헤더 1블록뿐 — 요구 적재(exec.c:11-18 주석)")

    # 16 형식 검사
    p = d.slide("코드: 형식 검사 — ZMAGIC·재배치·크기·N_TXTOFF", K.S_CODE,
                "fs/exec.c:298-309 · a.out.h:30-34(N_BADMAG) — 0.11이 받아들이는 실행 파일은 ZMAGIC 하나")
    d.code_panel(p, "src/fs/exec.c", 298, 309, 1100, 4400, 19700, 8000,
                 size=9, caption_extra="12줄 — 다섯 검사")
    items = [
        ("① N_MAGIC(ex) != ZMAGIC", "OMAGIC·NMAGIC도 거부 — 299"),
        ("② a_trsize || a_drsize", "재배치 정보 — 299"),
        ("③ text+data+bss > 0x3000000", "48MB 초과 — 300"),
        ("④ i_size < …+a_syms+N_TXTOFF", "파일이 더 짧다 — 301"),
        ("⑤ N_TXTOFF != BLOCK_SIZE", "printk 후 ENOEXEC — 305-308"),
    ]
    iy = 4400
    for l1, l2 in items:
        nbox(d, p, 22000, iy, 9500, 1600, l1, l2, None, K.PAPER, s1=13, s2=11)
        iy += 1750
    d.banner(p, "다섯 검사 전부 → ENOEXEC — 아직 318 이전이라 되돌릴 수 있다")

    # 17 #! 스크립트 (1/2)
    p = d.slide("코드: #! 스크립트 (1/2) — 파싱", K.S_CODE,
                "fs/exec.c:226-256 — b_data[0..1]=='#!' && !sh_bang 일 때만 · 버퍼 1022B, 첫 줄만")
    d.code_panel(p, "src/fs/exec.c", 226, 238, 1100, 4400, 14200, 8600,
                 size=9, caption_extra="조건과 버퍼 — 13줄")
    d.code_panel(p, "src/fs/exec.c", 239, 256, 16900, 4400, 15700, 10000,
                 size=8, caption_extra="첫 줄 파싱 — 18줄")
    auto_pane(d, p, 1100, 13300, 14200, 2600,
              "예시 — /tmp/t.sh (시연 C · 41장)",
              "#!/bin/sh      ← b_data[0..1] == '#', '!'\n"
              "echo hi        ← 나머지 줄은 인터프리터(/bin/sh)가 읽는다", start=12)
    d.text(p, 1100, 16200, 31500, 600,
           "빈 줄이면(인터프리터 이름 없음) ENOEXEC(243-246) — 공백 건너뛰기(241) 뒤 *cp=='\\0'인 경우.", 12, K.MUTED)

    # 18 #! 스크립트 (2/2)
    p = d.slide("코드: #! 스크립트 (2/2) — argv 재구성과 재시작", K.S_CODE,
                "fs/exec.c:257-297 — 문자열을 역순으로 얹고 namei(interp) 후 goto restart_interp · 중첩 불가")
    d.code_panel(p, "src/fs/exec.c", 261, 264, 1100, 4400, 14200, 4400,
                 size=11, caption_extra="처음 한 번만 — 원래 envp·argv[1..]")
    d.code_panel(p, "src/fs/exec.c", 288, 296, 1100, 9100, 14200, 6300,
                 size=9, caption_extra="재시작 — 9줄")
    d.code_panel(p, "src/fs/exec.c", 273, 284, 16900, 4400, 15700, 8000,
                 size=9, caption_extra="역순 얹기 — 12줄")
    auto_pane(d, p, 16900, 12700, 15700, 2100,
              "argv 재구성 결과 — from_kmem 1(273)·2(276·279)",
              "argv = [ i_name, i_arg(있다면), filename, argv[1], … ]   # argc +3", start=12)
    d.banner(p, "goto restart_interp(296) — 같은 do_execve 안에서 /bin/sh로 다시 검사한다 · "
                "sh_bang=1이라 #!의 #!는 없다", 14800, 17)

    # 19 copy_strings
    p = d.slide("코드: copy_strings — 거꾸로 채우는 128KB", K.S_CODE,
                "fs/exec.c:104-152 · MAX_ARG_PAGES 32(39) — argc-1부터 0까지, p를 줄이며 page[] 꼭대기에 복사")
    d.code_panel(p, "src/fs/exec.c", 117, 131, 1100, 4400, 15200, 8500,
                 size=8, caption_extra="루프 앞부분 — 15줄")
    d.code_panel(p, "src/fs/exec.c", 132, 147, 16900, 4400, 15700, 9000,
                 size=8, caption_extra="바이트 복사 — 16줄")
    nbox(d, p, 1100, 13800, 14200, 900,
         "page[31] 꼭대기 — argv[argc-1]부터 argv[0]까지 아래 번지로 자란다", None,
         K.TEAL, s1=13)
    nbox(d, p, 15700, 13800, 4400, 900, "p ↓ 감소", None, K.ORANGE, s1=13)
    nbox(d, p, 20500, 13800, 12100, 900,
         "없는 page[p/4096]는 그때 get_free_page(138-140)", None, K.PAPER, s1=13)
    d.banner(p, "반환 p = 남은 공간 오프셋 — 0이면 실패(ENOMEM 경로, 32장)")

    # 20 돌이킬 수 없는 지점
    p = d.slide("코드: 돌이킬 수 없는 지점 — point of no return", K.S_CODE,
                "fs/exec.c:318-327 — 318행 주석 원문 'OK, This is the point of no return' · 이 뒤로 오류 반환 없음")
    d.code_panel(p, "src/fs/exec.c", 318, 327, 1100, 4400, 19700, 7000,
                 size=9, caption_extra="10줄 — 318행 주석은 원문 참조")
    para(d, p, 22000, 4400, 10000, 10000,
         "iput(구 executable) 후 새 inode(319-321) — 이 순간부터 inode는 새 프로그램 것.\n\n"
         "sigaction[32].sa_handler = NULL(322-323) — 구 프로그램 주소의 핸들러는 새 공간에 없다.\n\n"
         "close_on_exec 비트 fd를 sys_close(324-326) — 'exec하면 닫아라' 표시.\n\n"
         "이후(328-)에는 exec_error 레이블로 가는 길이 없다.", 14)
    d.outline(p, 1100, 11700, 19700, 2200, K.ORANGE, 120)
    d.text(p, 1400, 12050, 19000, 1400,
           "여기부터 execve는 되돌릴 수 없다 — 실패해도 구 프로그램은 이미 없다",
           17, K.ORANGE, True)
    d.banner(p, "시그널 핸들러·일부 fd 정리 — 구 프로그램의 흔적 지우기가 시작된다")

    # 21 주소 공간 비우기
    p = d.slide("코드: 주소 공간 비우기", K.S_CODE,
                "fs/exec.c:328-332 · mm/memory.c:105-131(07회차) · kernel/exit.c:106-107 — do_exit와 같은 두 줄")
    d.code_panel(p, "src/fs/exec.c", 328, 332, 1100, 4400, 15200, 4600,
                 size=10, caption_extra="두 줄 + math 정리")
    d.code_panel(p, "src/kernel/exit.c", 106, 107, 1100, 9300, 15200, 3000,
                 size=10, caption_extra="do_exit의 같은 두 줄 — 10회차")
    para(d, p, 16900, 4400, 15700, 8600,
         "free_page_tables(base, limit) — 07회차가 읽은 함수(mm/memory.c:105-131).\n\n"
         "4MB 단위로: PTE가 가리키는 물리 페이지 반납(공유 중이면 mem_map count만 감소, "
         "08회차) → 페이지 테이블 페이지 반납 → pg_dir 항목 0.\n\n"
         "코드(ldt[1]·0x0f 리밋)와 데이터(ldt[2]·0x17 리밋)를 각각 지운다(328-329).\n\n"
         "last_task_used_math 정리(330-332) — 10회차 do_exit에도 같은 모양이 나온다.", 14)
    nbox(d, p, 16900, 13000, 7300, 1300, "exec.c:328-329", "프로그램 교체",
         None, K.TEAL, s1=14, s2=11)
    d.text(p, 24350, 13350, 900, 700, "=", 22, K.ORANGE, True)
    nbox(d, p, 25300, 13000, 7300, 1300, "exit.c:106-107", "프로그램 종료(10)",
         None, K.TEAL, s1=14, s2=11)
    d.banner(p, "구 프로그램의 64MB가 사라진다 — 남는 것은 change_ldt가 새로 얹을 인자 페이지뿐")

    # 22 change_ldt (1/2)
    p = d.slide("코드: change_ldt (1/2) — 리밋만 바꾸고 베이스는 그대로", K.S_CODE,
                "fs/exec.c:154-167 · kernel/fork.c:52-55(new_data_base = nr * 0x4000000) — 오늘의 대명제")
    d.code_panel(p, "src/fs/exec.c", 154, 167, 1100, 4400, 19700, 8900,
                 size=9, caption_extra="14줄 — 전반")
    para(d, p, 22000, 4400, 10000, 6800,
         "code_limit = text_size+4095 & ~0xFFF(159-160) — a_text를 페이지로 올림.\n"
         "data_limit = 0x4000000(161) — 항상 64MB.\n\n"
         "code_base = get_base(ldt[1])(162) — 읽어서\n"
         "set_base(같은 값)(164·166) — 다시 쓴다.\n"
         "set_limit×2(165·167) — 리밋만 새 값.", 14)
    badge(d, p, 22000, 11400, 9500, "베이스 불변 · 리밋만 교체", K.TEAL, 800, 16)
    para(d, p, 22000, 12400, 10000, 2200,
         "베이스 nr×64MB는 fork.c:52-55가 태스크 슬롯에서 정했다 — exec는 절대 바꾸지 않는다(§8).", 13)
    d.banner(p, "LDT를 새로 만들지 않는다 — 같은 디스크립터에 리밋만 다시 쓴다")

    # 23 change_ldt (2/2)
    p = d.slide("코드: change_ldt (2/2) — 인자 페이지를 64MB 끝에 매핑", K.S_CODE,
                "fs/exec.c:168-177 — pushl $0x17; pop %fs · put_page(page[i], data_base) — 물리 페이지 이동 없음")
    d.code_panel(p, "src/fs/exec.c", 168, 177, 1100, 4400, 19700, 7300,
                 size=10, caption_extra="10줄 — 후반")
    para(d, p, 22000, 4400, 10000, 9500,
         "pushl $0x17; pop %fs(169) — 새 데이터 리밋을 fs에 즉시 반영. 이후 put_fs_*는 새 세그먼트 기준.\n\n"
         "data_base = code_base+64MB에서 시작해 한 페이지씩 내려가며(170-172)\n"
         "page[i]가 있는 칸만 put_page(173-174) — copy_strings가 안 만든 page는 건너뛴다.\n\n"
         "put_page는 PTE만 만든다 — 문자열 물리 페이지는 그대로다(30장 ③).\n\n"
         "return data_limit(176) — 333에서 p 보정에 쓴다.", 14)
    nbox(d, p, 1100, 12100, 6600, 1500, "page[i]",
         "커널이 잡은 물리 페이지 — 그대로", None, K.PAPER, s1=14, s2=11)
    d.text(p, 7900, 12400, 2000, 700, "→", 22, K.ORANGE, True)
    d.text(p, 7600, 13150, 3000, 500, "put_page — PTE만", 12, K.ORANGE, True)
    nbox(d, p, 10000, 12100, 10800, 1500, "베이스+64MB-4KB×(32-i)",
         "새 공간 64MB 끝 — 논리 주소만 새로", None, K.TEAL, s1=14, s2=11)
    d.banner(p, "문자열은 한 번만 복사된다 — 바뀌는 것은 매핑(PTE)뿐")

    # 24 create_tables
    p = d.slide("코드: create_tables — 새 스택 꼭대기", K.S_CODE,
                "fs/exec.c:46-70 · 333-334 — p += change_ldt(...)-128KB 로 논리 주소 환산 후 argc·argv·envp 구성")
    d.code_panel(p, "src/fs/exec.c", 51, 63, 1100, 4400, 14200, 8500,
                 size=9, caption_extra="13줄 — sp 계산과 push")
    d.code_panel(p, "src/fs/exec.c", 64, 69, 16900, 4400, 15700, 5300,
                 size=10, caption_extra="6줄 — envp 채우고 반환")
    d.code_panel(p, "src/fs/exec.c", 333, 334, 16900, 10000, 15700, 3000,
                 size=10, caption_extra="호출처 — p 환산")
    d.text(p, 25600, 13050, 7000, 500, "높은 주소 (64MB 쪽) →", 12, K.TEAL, True)
    strip = [("argc", 2800, K.ORANGE), ("argv", 2800, K.ORANGE),
             ("envp", 2800, K.ORANGE), ("argv[0..argc-1]·NULL", 6300, K.PAPER),
             ("envp[0..envc-1]·NULL", 6300, K.PAPER), ("문자열…", 7800, K.TEAL)]
    sx = 1100
    for l1, w, fill in strip:
        nbox(d, p, sx, 13400, w, 1000, l1, None, fill, s1=13)
        sx += w + 300
    d.banner(p, "sp에서 envp·argv·argc 순으로 push(56-58) — 문자열은 이미 그 위에 있다(copy_strings)")

    # 25 태스크 필드 갱신
    p = d.slide("코드: 태스크 필드 갱신", K.S_CODE,
                "fs/exec.c:335-340 — 한 줄 중첩 대입(335-337) · start_stack(338) · euid·egid(339-340)")
    d.code_panel(p, "src/fs/exec.c", 335, 340, 1100, 4400, 15200, 5400,
                 size=11, caption_extra="6줄")
    ptrs = [("end_code", "a_text", K.TEAL), ("end_data", "a_text+a_data", K.TEAL),
            ("brk", "end_data+a_bss", K.ORANGE),
            ("start_stack", "p & 0xfffff000", K.ORANGE)]
    px = 1100
    for l1, l2, col in ptrs:
        nbox(d, p, px, 10300, 3500, 1600, l1, l2, None, col, s1=14, s2=11)
        px += 3800
    para(d, p, 1100, 12200, 15200, 2400,
         "10장 64MB 그림의 네 포인터가 이 여섯 줄에서 정해진다. start_code는 없다 — "
         "베이스 자체라 그대로(fork.c:52-55).", 14)
    para(d, p, 16900, 4400, 15700, 10200,
         "current->brk = a_bss +\n  (end_data = a_data +\n  (end_code = a_text));\n"
         "— 안쪽부터 대입한다(335-337).\n\n"
         "brk는 sbrk/malloc의 기준점 — 힙의 시작.\n\n"
         "start_stack = p & 0xfffff000(338) — create_tables가 돌려준 sp의 페이지.\n\n"
         "euid·egid(339-340) — setuid 파일이면 14장에서 계산한 파일 소유자 값이 "
         "드디어 current에 반영된다.", 15)
    d.banner(p, "a_entry는 아직 안 썼다 — 다음 두 장(26-27)이 마무리한다")

    # 26 꼬리 0 채움
    p = d.slide("코드: 꼬리 0 채움 — 첫 do_no_page를 일으키는 쓰기", K.S_CODE,
                "fs/exec.c:341-343 · mm/memory.c:372-377(380-396) — exec 자신의 쓰기가 페이지를 적재한다")
    d.code_panel(p, "src/fs/exec.c", 341, 343, 1100, 4400, 14200, 3800,
                 size=12, caption_extra="3줄")
    d.code_panel(p, "src/mm/memory.c", 372, 377, 16900, 4400, 15700, 5100,
                 size=10, caption_extra="do_no_page 진입 — 08회차")
    chain = [
        ("put_fs_byte(0, i++) — a_text+a_data부터", "i는 4096 경계까지(342) — fs 세그먼트로 쓴다", K.PAPER),
        ("쓰기가 없는 페이지에 닿는다 → #PF (P=0)", "do_execve의 마지막 동작이 폴트를 낸다", K.ORANGE),
        ("do_no_page — share_page 우선, 아니면 디스크", "bmap×4 + bread_page(380-394) — 새 inode로", K.TEAL),
    ]
    cy = 8500
    for l1, l2, col in chain:
        nbox(d, p, 1100, cy, 14200, 1700, l1, l2, None, col, s1=13, s2=11)
        if cy < 11900:
            d.text(p, 7900, cy + 1720, 900, 600, "↓", 18, K.ORANGE, True)
        cy += 2050
    para(d, p, 16900, 9900, 15700, 4700,
         "적재된 페이지에 이미 쓴 0이 남는다 — 마지막 데이터 페이지 꼬리+bss 시작이 0이 되는 순간.\n\n"
         "'exec가 코드를 읽지 않는다(exec.c:11-18 주석)'의 첫 증거 — exec조차 데이터를 "
         "직접 안 읽고 폴트에 맡긴다.", 14)
    d.banner(p, "요구 적재의 시작점 — exec의 마지막 쓰기조차 폴트가 처리한다")

    # 27 마법의 두 줄
    p = d.slide("코드: 마법의 두 줄 — eip[0], eip[3]", K.S_CODE,
                "fs/exec.c:344-346 · system_call.s:200-205 — 커널은 새 프로그램을 '실행'하지 않는다")
    d.code_panel(p, "src/fs/exec.c", 344, 346, 1100, 4400, 14200, 4000,
                 size=13, caption_extra="344행 주석 'magic happens :-)'")
    nbox(d, p, 16900, 4400, 7600, 1500, "EIP ← ex.a_entry", "eip[0] — 344",
         K.ORANGE, s1=16, s2=12)
    nbox(d, p, 25000, 4400, 7600, 1500, "OLDESP ← p", "eip[3] — 345",
         K.ORANGE, s1=16, s2=12)
    para(d, p, 16900, 6200, 15700, 2200,
         "07장 프레임의 두 칸이 덮어써졌다. CS·SS는 진입 때 값(0x0f·0x17) 그대로 — "
         "세그먼트는 그대로, 리밋이 새 프로그램이다.", 14)
    d.flow(p, [("eip[0]=a_entry", "344 — 저장된 EIP"),
               ("return 0", "346"),
               ("ret_from_sys_call", "system_call.s:101"),
               ("iret", "새 EIP·ESP로 복귀")], y=8700, h=2600)
    para(d, p, 1100, 11700, 14200, 2900,
         "_sys_execve의 ret(205) → ret_from_sys_call → iret — 프레임의 새 EIP·ESP로 복귀하면 "
         "그곳은 새 프로그램의 main()이다. ret 0은 시스템 콜 응답일 뿐 새 프로그램은 못 본다.", 14)
    d.banner(p, "execve는 성공하면 돌아오지 않는다 — 복귀하는 순간 이미 다른 프로그램이다")

    # 28 첫 명령은 아직 메모리에 없다
    p = d.slide("코드: 첫 명령은 아직 메모리에 없다", K.S_CODE,
                "mm/memory.c:372-386 · fs/exec.c:221-225 — 헤더만 읽었으니 첫 fetch는 반드시 폴트다")
    d.code_panel(p, "src/mm/memory.c", 372, 386, 1100, 4400, 19700, 9500,
                 size=9, caption_extra="do_no_page 핵심 15줄 — 08회차와 같은 코드")
    steps = [
        ("① iret — CS:EIP = 0x0f:a_entry", "첫 명령 fetch — PTE 부재"),
        ("② #PF (U=1, P=0)", "page.s → do_no_page(365)"),
        ("③ share_page 우선(378)", "같은 /bin/sh면 공유 — 디스크 안 읽음"),
        ("④ bmap×4 + bread_page", "새 inode에서 블록 4개 = 페이지 1개(380-386)"),
    ]
    ty = 4400
    for l1, l2 in steps:
        nbox(d, p, 22000, ty, 9500, 1900, l1, l2, None, K.PAPER, s1=13, s2=11)
        ty += 2100
    para(d, p, 22000, 13100, 10000, 1500,
         "exec.c:221-225 — 읽은 것은 헤더 1블록. 08회차 시연 B와 동일 장면, inode만 새 executable.", 12)
    d.banner(p, "코드를 가져오는 것은 exec가 아니라 첫 폴트다 — 요구 적재")

    # ── 상태도 29–30 ──────────────────────────────────────────
    # 29 상태 변화도 ①
    p = d.slide("상태 변화도 ①: 태스크의 프로그램 상태", K.S_STATE,
                "fs/exec.c:318-346 — 상태 5개·전환 4개(호출 순서도 아님) · 캡처 36·38장=전환 ②③, 39·40장=상태 ⑤")
    states = [
        ("구(舊) 프로그램 실행 중", "execve 직전 — 셸 등", None, K.MUTED),
        ("검사 중", "182-316 — 되돌릴 수 있음", None, K.PAPER),
        ("주소 공간 비움", "318-333 — 공간 교체", K.ORANGE, None),
        ("새 프레임 준비", "334-346 — eip·brk", K.ORANGE, None),
        ("새 프로그램 첫 폴트", "iret → #PF → 적재", None, K.TEAL),
    ]
    sx = 1100
    for l1, l2, fill, edge in states:
        nbox(d, p, sx, 5300, 5600, 2300, l1, l2, fill=fill, edge=edge,
             s1=15, s2=11)
        if sx < 27000:
            d.text(p, sx + 5650, 6100, 800, 700, "→", 22, K.ORANGE, True)
        sx += 6475
    trans = [("execve 진입", 3900), ("318 — point of no return", 10400),
             ("iret (344-345)", 16900), ("첫 fetch #PF", 23400)]
    for t, tx in trans:
        d.text(p, tx, 7900, 6400, 600, t, 13, K.ORANGE, True)
    qbox(d, p, 1100, 9000, 15400, 5200, "변경되는 데이터",
         "executable · ldt[1]·ldt[2] 리밋 · 페이지 테이블 전부(pg_dir 항목·PTE) · "
         "brk·end_code·end_data·start_stack · sigaction 32개 · close_on_exec fd · "
         "euid·egid · 커널 스택의 EIP/ESP", K.ORANGE, 14)
    qbox(d, p, 16900, 9000, 15400, 5200, "유지되는 데이터",
         "pid · father · pwd·root · uid/gid · ldt 베이스(start_code) · tss 나머지 · "
         "close_on_exec 외 fd · state·counter 등 스케줄 정보", K.TEAL, 14)
    d.text(p, 29300, 14500, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # 30 상태 변화도 ②
    p = d.slide("상태 변화도 ②: 인자 문자열의 네 위치", K.S_STATE,
                "fs/exec.c:104-152 · 154-177 · 46-70·333-334 — 문자열은 한 번만 복사, 이후는 매핑·포인터만")
    locs = [
        ("① 구 사용자 공간", "argv·envp 문자열 — fork가 물려준 페이지", None, K.MUTED),
        ("② page[] 꼭대기", "copy_strings(104-152) — 거꾸로", None, K.PAPER),
        ("③ 64MB 끝 매핑", "put_page(171-174) — 물리 이동 없음", K.ORANGE, None),
        ("④ 포인터 배열·argc", "create_tables(46-70) — eip[3]=p", None, K.TEAL),
    ]
    lx = 1100
    for l1, l2, fill, edge in locs:
        nbox(d, p, lx, 4700, 7300, 2300, l1, l2, fill=fill, edge=edge,
             s1=15, s2=11)
        if lx < 25000:
            d.text(p, lx + 7350, 5500, 700, 700, "→", 22, K.ORANGE, True)
        lx += 8033
    d.outline(p, 1100, 7600, 19700, 6600, K.LINE, 100)
    d.text(p, 1400, 7700, 19000, 600,
           "page[] — 커널에 임시로 쌓는 128KB (MAX_ARG_PAGES 32)", 14, K.TEAL, True)
    prows = [
        ("128KB 경계 — page[31] 꼭대기 (p 시작: 128KB-4)", K.TEAL),
        ("… envp[envc-1] · argv[argc-1] 문자열 (먼저 복사 — 높은 주소)", None),
        ("… 중간 문자열들 …", None),
        ("argv[0] — 마지막에 복사 (가장 낮은 주소)", None),
        ("빈 공간 — p가 여기까지 내려왔다 (반환 p = 남은 오프셋)", None),
        ("page[0] — 안 쓴 칸은 0 · change_ldt가 있는 것만 매핑(173-174)", None),
    ]
    py = 8400
    for l1, fill in prows:
        nbox(d, p, 1400, py, 19100, 800, l1, None, fill, s1=13)
        py += 950
    para(d, p, 21800, 7600, 10800, 6600,
         "변경: page[32] 배열 · PTE 32개 · 새 스택 메모리(argc·포인터 배열)\n\n"
         "유지: 문자열 내용 — 한 번만 복사된다.\n②→③은 매핑만, ②→④는 포인터만.\n\n"
         "#!라면 ②에서 i_name·i_arg·filename이 추가로 얹힌다(18장).\n\n"
         "eip[3]=p가 이 꼭대기를 새 ESP로 지정한다(345).", 15)
    d.banner(p, "문자열은 한 번만 복사된다 — 이후에는 PTE와 포인터 배열만 바뀐다")

    # ── 비교 31–33 ────────────────────────────────────────────
    # 31 실행 파일 형식
    p = d.slide("비교 ①: 실행 파일 형식 — 받아들이는 것과 거부하는 것", K.S_CMP,
                "include/a.out.h:21-28 · fs/exec.c:299(298-309) · 226-297 — 받아들이는 것은 ZMAGIC 하나")
    d.table(p, 1100, 4400, [5300, 8900, 8300, 9000], [
        ["형식", "메모리 배치 특성", "0.11 처리", "왜"],
        ["ZMAGIC 0413", "텍스트 1KB(SEGMENT_SIZE) 정렬", "받아들인다 — 유일(299)", "블록 단위 요구 적재에 맞음"],
        ["OMAGIC 0407", "impure — 텍스트·데이터 한 덩어리", "ENOEXEC(299)", "블록 정렬 아님 — 요구 적재 불가"],
        ["NMAGIC 0410", "pure — 헤더 직후 텍스트", "ENOEXEC(299)", "N_TXTOFF(1024) 기대와 불일치"],
        ["#! 스크립트", "실행 파일 아님 — 첫 줄 지시", "1회 재시작(226-297)", "인터프리터(/bin/sh)를 exec"],
        ["그 외 전부", "매직 3개 아님 — ELF 등", "ENOEXEC(N_BADMAG)", "a.out.h:30-34"],
    ], row_h=1300, size=14)
    para(d, p, 1100, 12600, 31500, 1900,
         "현대 비교 한 줄: 오늘날 리눅스는 ELF — ELF는 1991년에 없었다. mmap 기반이지만 "
         "'폴트가 나야 적재'라는 정신(demand paging)은 그대로다.", 15)

    # 32 오류 반환 경로
    p = d.slide("비교 ②: 오류 반환 경로 전부", K.S_CMP,
                "fs/exec.c · include/errno.h:21·26·27·31·32 — 전부 318 이전 = 구 프로그램으로 복귀 · E2BIG은 정의만(§8)")
    d.table(p, 1100, 4400, [4600, 16800, 10100], [
        ["errno", "조건 (fs/exec.c)", "결과"],
        ["ENOENT 2", "namei 실패(199-200) · 인터프리터 없음(290-293)", "복귀 + page[] 해제"],
        ["EACCES 13", "정규 파일 아님(205-208) · 첫 블록 읽기 실패(221-224)", "복귀 + inode iput"],
        ["ENOEXEC 8", "실행 비트 없음(216-220) · #! 빈 줄(243-246) · 형식(299-304) · N_TXTOFF(305-309)", "복귀"],
        ["ENOMEM 12", "copy_strings 실패(281-284 · 313-316)", "복귀"],
        ["E2BIG 7", "errno.h:26 정의만 — exec.c는 안 씀", "(일어나지 않음 — 초과는 ENOMEM 경로)"],
    ], row_h=1200, size=14)
    para(d, p, 1100, 12100, 31500, 2600,
         "공통점: 전부 318 이전에 return — 구 프로그램이 그대로 계속되고 lib/execve.c의 _syscall3이 "
         "errno=-res를 정리해 -1로 돌려준다(06장).\n"
         "exec_error2(347-348): iput 후 exec_error1(349-351): page[] 해제 — 두 레이블이 되돌리기를 담당한다.", 15)
    d.banner(p, "실패한 execve는 아무 일 없었던 것처럼 돌아간다 — 318 이후에는 길이 없다")

    # 33 from_kmem
    p = d.slide("비교 ③: copy_strings의 from_kmem 0/1/2", K.S_CMP,
                "fs/exec.c:92-98 주석 · 115-116·118-123·136-143(set_fs 토글) — fs 세그먼트 묘기")
    d.table(p, 1100, 4400, [3300, 3900, 3900, 9800, 10600], [
        ["from_kmem", "argv* 문자열", "argv** 배열", "fs 조작 (exec.c)", "호출처 · 내용"],
        ["0", "사용자", "사용자", "set_fs 없음 — fs=0x17 그대로", "262-263 · 311-312 — 통상 경로"],
        ["1", "커널", "사용자", "배열 읽기만 new_fs(118-123)", "273 — &filename 배열 + 사용자 문자열"],
        ["2", "커널", "커널", "진입 시 new_fs · 페이지마다 복원(115-116·136-143)", "276·279 — i_arg·i_name (커널 buf)"],
    ], row_h=1300, size=14)
    auto_pane(d, p, 1100, 10000, 16000, 4700,
              "exec.c:95-98 — 주석 원문의 표",
              "from_kmem     argv *        argv **\n"
              "   0          user space    user space\n"
              "   1          kernel space  user space\n"
              "   2          kernel space  kernel space", start=13)
    para(d, p, 17800, 10000, 14800, 4700,
         "왜 세 가지인가 — #! 처리 중에는 인터프리터 이름(i_name·i_arg)은 커널 buf에, "
         "원래 argv는 사용자 공간에 있어 한 호출 안에 출처가 섞인다.\n\n"
         "fs 적재는 비싸므로 꼭 필요할 때만 토글한다(주석 100-102).", 14)

    # ── 시연 34–41 ────────────────────────────────────────────
    # 34 시연 준비
    p = d.slide("시연 준비: 심볼과 기본 기법", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 TCG · GDB — 줄 번호는 lab 기준(슬라이드는 src 기준) · 값은 부팅마다 다름")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — 심볼·기본 기법",
              "# 심볼: do_execve · sys_execve · change_ldt(static, -g로 보임) · current\n"
              "(gdb) list do_execve        # lab 소스의 줄 — src와 다를 수 있음\n"
              "(gdb) b do_execve\n"
              "# 사용자 포인터는 fs 세그먼트 보정해 읽는다:\n"
              "(gdb) x/s (char*)current->start_code + (long)filename\n"
              "#   논리 주소(오프셋) + start_code(베이스) = 선형 주소\n"
              "(gdb) p/x current->ldt[1].a & 0xffff     # 코드 리밋 — 페이지 단위\n"
              "(gdb) p/x current->ldt[2].a & 0xffff     # 데이터 리밋 — 0x4000 기대\n"
              "(gdb) p current->executable->i_num       # 실행 파일 inode\n"
              "# inode·주소·리밋 값은 lab 디스크 이미지에 따라 다르다", start=11)
    para(d, p, 22000, 4300, 9500, 10100,
         "시연 구성\n\n"
         "A 진입(35-36장) — 바뀔 값·그대로 값 목록\n"
         "B 마법의 두 줄 전후(37-38장) — ldt·executable·eip[0]·eip[3]\n"
         "C 첫 폴트(39-40장) — 같은 pid, 다른 코드\n"
         "선택 #!(41장) — restart_interp 재시작\n\n"
         "중단점 줄은 lab 소스에서 list로 확인한다 — src 344·205 상당 줄이 목표.", 15)
    d.banner(p, "값은 예시(실측 아님) — 캡처 확보 전까지 각 장의 예상 출력로 대체한다")

    # 35 시연 A-1
    p = d.slide("시연 A-1: do_execve 진입 시점", K.S_DEMO,
                "fs/exec.c:182-203 관찰 — 진입 시점의 값은 전부 '셸의 것' · src 줄 번호 기준")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — do_execve 진입",
              "(gdb) b do_execve ; c\n"
              "# 셸 프롬프트에서 ls 입력 → 자식이 execve → 정지\n"
              "Breakpoint 1, do_execve (eip=0x37f4c, tmp=0, filename=0x2f68,\n"
              "    argv=0x2fe10, envp=0x2fe30) at fs/exec.c:182\n"
              "(gdb) p current->pid\n"
              "$1 = 7                    # fork로 생긴 자식 — 셸과 pid 다름\n"
              "(gdb) x/s (char*)current->start_code + (long)filename\n"
              "0x4002f68:  \"/bin/ls\"     # 또는 /usr/bin/ls — 배치에 따라\n"
              "(gdb) p/x current->ldt[1].a & 0xffff\n"
              "$2 = 0x23                 # 셸 코드 리밋(페이지 수, 예시)\n"
              "(gdb) p current->executable->i_num\n"
              "$3 = 41                   # 아직 셸의 inode\n"
              "(gdb) p/x eip[0] ; p/x eip[3]\n"
              "$4 = 0x2f1c   $5 = 0x3fffd2c    # 셸의 복귀 EIP/ESP(예시)", start=10)
    para(d, p, 22000, 4300, 9500, 10100,
         "관찰 포인트\n\n"
         "· p current->pid — 자식 pid\n"
         "· x/s — \"/bin/ls\" 경로 확인\n"
         "· ldt[1] 리밋 — 셸 텍스트 크기\n"
         "· executable — 셸의 inode\n"
         "· eip[0]·eip[3] — 셸 복귀 지점\n\n"
         "37-38장에서 이 값들이 어떻게 바뀌는지 본다.\n"
         "캡처 01 = 다음 장(36).", 15)

    # 36 캡처 A-1
    p = d.slide("캡처 A-1: 진입 시점 값", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 TCG · GDB · 수정 없음 · 캡처 날짜 — 값은 부팅마다 다름(§5 각주)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) b do_execve ; c        # 셸에 ls → 자식이 execve\n"
                         "Breakpoint 1, do_execve (eip=0x37f4c, ...) at fs/exec.c:182\n"
                         "(gdb) p current->pid\n"
                         "$1 = 7              # fork로 생긴 자식 pid\n"
                         "(gdb) x/s (char*)current->start_code + (long)filename\n"
                         "0x4002f68:  \"/bin/ls\"\n"
                         "(gdb) p/x current->ldt[1].a & 0xffff\n"
                         "$2 = 0x23           # 셸 코드 리밋(페이지, 예시)\n"
                         "(gdb) p current->executable->i_num\n"
                         "$3 = 41             # 셸의 inode — 아직\n"
                         "(gdb) p/x eip[0] ; p/x eip[3]\n"
                         "$4 = 0x2f1c  $5 = 0x3fffd2c   # 셸 복귀 EIP/ESP",
                         "01-do-execve-entry.png")
    para(d, p, 22000, 4150, 9500, 10300,
         "바뀔 값(37-38장)\n\n"
         "· ldt[1] 리밋 — 셸 → ls 텍스트\n"
         "· executable — 셸 inode → ls inode\n"
         "· eip[0] — 셸 복귀 EIP → a_entry\n"
         "· eip[3] — 셸 ESP → 새 스택 p\n\n"
         "그대로일 값\n\n"
         "· pid = 7 · ldt 베이스(start_code)\n"
         "· CS 0x0f · SS 0x17 — 세그먼트 자체", 15)

    # 37 시연 A-2
    p = d.slide("시연 A-2: 마법의 두 줄 전후", K.S_DEMO,
                "fs/exec.c:344-346·154-177·318-343 관찰 — src 344 상당 줄은 lab에서 list로 확인")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — eip[0] 대입 줄에서 정지",
              "(gdb) b exec.c:<eip[0]= 줄> ; c    # src 344 상당 — list 확인\n"
              "Breakpoint 2, do_execve (...) at fs/exec.c:344\n"
              "(gdb) p/x ex\n"
              "{a_magic = 0x10b, a_text = 0x5b90, a_data = 0x520, a_bss = 0x7c4,\n"
              " a_syms = 0, a_entry = 0x0, a_trsize = 0, a_drsize = 0}\n"
              "                     # 0413(8진수) = 0x10b — ZMAGIC\n"
              "(gdb) p/x current->ldt[1].a & 0xffff\n"
              "$6 = 0x6              # (a_text+4095)&~4095 >> 12 — 페이지 올림\n"
              "(gdb) p/x current->ldt[2].a & 0xffff\n"
              "$7 = 0x4000           # 64MB/4KB — 데이터 리밋\n"
              "(gdb) p current->executable->i_num ; p current->pid\n"
              "$8 = 96   $9 = 7      # inode 바뀜 · pid 불변!\n"
              "(gdb) p/x eip[0]\n"
              "$10 = 0x2f1c          # 아직 셸 값 → next 2회면 바뀐다(38장)", start=10)
    para(d, p, 22000, 4300, 9500, 10100,
         "관찰 포인트\n\n"
         "· ex.a_magic = 0x10b — ZMAGIC\n"
         "· 코드 리밋 = a_text 페이지 올림\n"
         "· 데이터 리밋 = 0x4000\n"
         "· inode 바뀜 · pid 불변\n"
         "· eip[0] 아직 셸 값\n\n"
         "next 2회 → eip[0]=a_entry,\n"
         "eip[3]=64MB 바로 아래(38장).\n"
         "x/4wx로 [argc][argv][envp] 확인.", 15)

    # 38 캡처 A-2
    p = d.slide("캡처 A-2: eip[0]/eip[3] 전후", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 상태도 ①(29장) '새 프레임 준비' 행의 실측")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) b exec.c:<eip[0]= 줄> ; c      # src 344 상당\n"
                         "(gdb) p/x ex.a_magic ; p/x ex.a_entry\n"
                         "$1 = 0x10b    $2 = 0x0    # ZMAGIC · 엔트리 0\n"
                         "(gdb) p/x current->ldt[1].a & 0xffff\n"
                         "$3 = 0x6         # 새 코드 리밋 — a_text 올림\n"
                         "(gdb) p/x current->ldt[2].a & 0xffff\n"
                         "$4 = 0x4000      # 데이터 리밋 64MB\n"
                         "(gdb) p current->executable->i_num ; p current->pid\n"
                         "$5 = 96   $6 = 7  # inode 바뀜 · pid 불변\n"
                         "(gdb) p/x eip[0]\n"
                         "$7 = 0x2f1c      # 아직 셸의 복귀 EIP",
                         "02-eip-before.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) next ; next       # 344-345 두 줄 실행 직후\n"
                         "(gdb) p/x eip[0] ; p/x eip[3]\n"
                         "$8 = 0x0        # = ex.a_entry — 새 EIP\n"
                         "$9 = 0x3fffc54  # 64MB 바로 아래 — 새 ESP\n"
                         "(gdb) x/4wx (long)eip[3] + current->start_code\n"
                         "0x43fffc54:  0x00000001  0x43fffd20\n"
                         "             0x43ffff90  0x43fffd30\n"
                         "# [argc=1][argv][envp][argv[0]] — create_tables",
                         "03-eip-after.png")
    para(d, p, 1100, 14600, 31500, 1700,
         "전(02) — 리밋·inode는 바뀌고 eip[0]은 아직 셸 값 · 후(03) — eip[0]=a_entry·eip[3]=새 스택. "
         "x/4wx는 선형 주소 보정(오프셋+start_code)으로 [argc][argv][envp]를 확인한다.", 14)

    # 39 시연 B
    p = d.slide("시연 B: iret 뒤 첫 폴트", K.S_DEMO,
                "mm/memory.c:365-397 · fs/exec.c:341-343 — 첫 폴트 주소로 '무엇이 먼저'였는지 알 수 있다")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — do_no_page 추가",
              "(gdb) b do_no_page ; disable 2 ; c\n"
              "# ls 실행이 이어진다 — 첫 폴트에서 정지\n"
              "Breakpoint 3, do_no_page (error_code=4, address=0x4000000)\n"
              "    at mm/memory.c:365\n"
              "(gdb) p/x address - current->start_code\n"
              "$13 = 0x0        # 0이면 엔트리(a_entry) fetch가 먼저\n"
              "                 # end_data 페이지면 341-343 0채움이 먼저\n"
              "(gdb) p error_code\n"
              "$14 = 4          # U=1, P=0 — 사용자 fetch 부재\n"
              "(gdb) bt\n"
              "#0 do_no_page (mm/memory.c:365)\n"
              "#1 page_fault  (mm/page.s:32)\n"
              "(gdb) finish ; x/8xb current->start_code\n"
              "0x4000000: 0x83 0xe5 0xf0 0x0e ...   # 새 코드!\n"
              "(gdb) c          # 사용자 모드 첫 명령 중 Ctrl-C\n"
              "(gdb) p/x $eip ; p/x $cs\n"
              "$15 = 0x12   $16 = 0xf    # 작은 EIP · 사용자 CS", start=10)
    para(d, p, 22000, 4300, 9500, 10100,
         "관찰 포인트\n\n"
         "· 첫 폴트 주소 — 0(엔트리) 또는\n  end_data 페이지(꼬리 0채움)\n"
         "· error_code 4 — U=1, P=0\n"
         "· bt — do_no_page ← page_fault\n"
         "· finish 후 코드 바이트\n"
         "· $eip 작은 값 · $cs=0xf\n\n"
         "캡처 04·05 = 다음 장(40).\n"
         "341-343 쓰기가 먼저면 U=0 — 관찰로 구분한다.", 15)

    # 40 캡처 B
    p = d.slide("캡처 B: 같은 pid, 다른 코드", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 공유 중이면 PTE 하위 5, 디스크 읽기 없음(관찰/추론 구분)")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) b do_no_page ; disable 2 ; c     # 첫 폴트\n"
                         "Breakpoint 3, do_no_page (error_code=4, address=0x4000000)\n"
                         "    at mm/memory.c:365\n"
                         "(gdb) p/x address - current->start_code\n"
                         "$1 = 0x0        # 엔트리(a_entry=0) — 첫 fetch\n"
                         "(gdb) p error_code\n"
                         "$2 = 4          # U=1, P=0\n"
                         "(gdb) bt\n"
                         "#0 do_no_page  mm/memory.c:365\n"
                         "#1 page_fault  mm/page.s:32",
                         "04-do-no-page-first-fault.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) finish ; x/8xb current->start_code    # 같은 pid=7\n"
                         "0x4000000: 0x83 0xe5 0xf0 0x0e 0x36 ...\n"
                         "# 36장 진입 시점과 비교 — 셸이 아닌 ls 코드\n"
                         "(gdb) c            # 사용자 첫 명령 중 Ctrl-C\n"
                         "(gdb) p/x $eip ; p/x $cs\n"
                         "$3 = 0x12   $4 = 0xf\n"
                         "# 논리 EIP 작은 값 + CS=0xf — 새 프로그램\n"
                         "# 공유 중이면 PTE 하위 5 — 관찰/추론 구분(§8)",
                         "05-same-pid-new-code.png")
    para(d, p, 1100, 14600, 31500, 1700,
         "같은 pid, 다른 코드 바이트 — 36장 A-1의 x/s·inode와 나란히 게시. 같은 ls가 이미 떠 있으면 "
         "share_page로 적재되어 디스크 읽기 없이 PTE 하위 5일 수 있다 — 캡처만으로는 구분 안 되니 관찰과 추론을 나눠 말한다.", 14)

    # 41 시연 C(선택)
    p = d.slide("시연 C(선택): #! 스크립트의 재시작", K.S_DEMO,
                "fs/exec.c:204-220·226-297 — 게스트에서 /tmp/t.sh 생성 · 실패 시 아래 사전 캡처(06)로 대체")
    auto_pane(d, p, 1100, 4300, 14200, 10100, "게스트 + GDB — 두 번 정지",
              "# 게스트에서:\n"
              "# echo '#!/bin/sh' > /tmp/t.sh\n"
              "# echo 'echo hi' >> /tmp/t.sh\n"
              "# chmod +x /tmp/t.sh\n"
              "(gdb) b exec.c:<S_ISREG 줄>    # src 205 상당\n"
              "(gdb) c\n"
              "# /tmp/t.sh 실행 → 같은 호출 안에서 2회 정지\n"
              "(gdb) p sh_bang\n"
              "$1 = 0          # 첫 정지 — 아직 스크립트 검사\n"
              "(gdb) c\n"
              "(gdb) p sh_bang ; p argc ; p inode->i_num\n"
              "$2 = 1  $3 = 4  $4 = 41\n"
              "# 2회째: sh_bang=1 · argc +3 · inode=/bin/sh\n"
              "# 계속 진행 → hi 출력", start=10)
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) p sh_bang ; p argc ; p inode->i_num\n"
                         "$2 = 1   $3 = 4   $4 = 41\n"
                         "# 두 번째 정지 — restart_interp 뒤\n"
                         "# sh_bang=1 : 두 번째 루프임을 증명\n"
                         "# argc=4   : [sh][i_arg?][t.sh][원래 인자]\n"
                         "# inode=41 : /bin/sh — 인터프리터\n"
                         "(계속)  # 게스트에 hi 출력",
                         "06-shebang-restart.png")
    para(d, p, 1100, 14600, 14200, 1700,
         "같은 do_execve 호출 안에서 중단점이 2회 걸리는 것이 이 시연의 증거다 — 재귀가 아니라 goto 재시작(18장).", 14)

    # ── 정답 42–43 ────────────────────────────────────────────
    # 42 질문의 답 (1)
    p = d.slide("질문의 답 (1): PID가 그대로인 이유", K.S_ANS,
                "fs/exec.c:318-346 — exec는 task[nr] 구조체를 만들지도 지우지도 않는다")
    nbox(d, p, 1100, 4300, 31500, 1600,
         "exec는 task[nr] 구조체를 만들지도 지우지도 않는다 — pid는 그 슬롯의 번호다",
         None, K.TEAL, s1=19)
    qbox(d, p, 1100, 6300, 15400, 6400, "바뀌는 것",
         "executable(inode) · ldt[1]·ldt[2] 리밋 · 페이지 테이블 전부 · "
         "end_code·end_data·brk·start_stack · sigaction 32개 · close_on_exec fd · "
         "euid·egid · 그리고 커널 스택에 저장된 EIP/ESP(eip[0]·eip[3])", K.ORANGE, 15)
    qbox(d, p, 16900, 6300, 15400, 6400, "손대지 않는 것",
         "pid · father · pwd·root · uid·gid · ldt 베이스(start_code) · tss의 나머지 · "
         "close_on_exec에 없는 fd · state·counter 등 — 318-346 어디에도 나오지 않는다", K.TEAL, 15)
    d.banner(p, "PID는 '몸'의 번호 — exec는 몸 안의 프로그램(주소 공간·복귀점)만 교체한다")

    # 43 질문의 답 (2)
    p = d.slide("질문의 답 (2): 프로그램이 바뀌는 실제 순간", K.S_ANS,
                "fs/exec.c:328-332·344-346 · mm/memory.c:365-397 — 07·08·09 세 회차가 한 줄로 이어진다")
    d.flow(p, [
        ("07 — free_page_tables", "구 프로그램의 페이지·테이블 반납(exec.c:328-329)\n공유 중이면 count만 감소"),
        ("09 — eip[0]=a_entry", "iret 복귀 지점을 새 엔트리로(344-345)\n같은 pid, 새 EIP·ESP"),
        ("08 — do_no_page", "첫 fetch #PF → 새 inode에서\n블록 4개 적재(memory.c:380-394)"),
    ], y=4700, h=3400)
    para(d, p, 1100, 8700, 31500, 3300,
         "비우고(07) → 복귀 지점을 바꾸고(09) → 채우는 것은 첫 폴트가(08) — 세 회차가 exec 한 번에서 만난다.\n"
         "'프로그램이 바뀌는 실제 순간'은 iret가 새 a_entry로 복귀하는 그 한 명령이다 — "
         "그 전까지는 언제든 이전 프로그램이다(29장 상태도).", 16)
    d.outline(p, 1100, 12300, 31500, 2000, K.TEAL, 100)
    d.text(p, 1400, 12650, 30900, 1300,
           "현대 커널: ELF 로더 + mmap — 도구는 다르지만 '폴트가 나야 적재'는 같다(demand paging)",
           16, K.TEAL, True)

    # ── 정리·확인 44–47 ────────────────────────────────────────
    # 44 데이터 요약
    p = d.slide("오늘 코드가 쓰는 데이터 요약", K.S_WRAP,
                "fs/exec.c(§1 읽기 범위) · include/a.out.h:6-15 — 함수×데이터 교차표")
    d.table(p, 1100, 4400, [5200, 11800, 14500], [
        ["함수 (exec.c)", "읽는 것", "바꾸는 것"],
        ["count 75-85", "argv·envp (사용자, fs)", "— 개수만 반환"],
        ["copy_strings 104-152", "문자열 — from_kmem별 fs 토글", "page[32] · p"],
        ["change_ldt 154-177", "ldt[1..2] 베이스 · page[]", "ldt 리밋 2개 · PTE 32개(put_page)"],
        ["create_tables 46-70", "page[]의 문자열", "새 스택 argc·argv·envp 배열"],
        ["free_page_tables 328-329", "ldt 베이스·리밋", "페이지 테이블 전부 · mem_map"],
        ["do_execve 182-346", "eip[] · inode·ex · argv·envp", "current->{executable·sigaction·brk·end_*·start_stack·euid·egid} · filp · eip[0]·eip[3]"],
    ], row_h=1050, size=13)
    d.banner(p, "재료 셋 — struct exec ex · page[32]와 p · eip[] (그리고 current의 필드들)")

    # 45 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(46) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "do_execve의 첫 인자 eip는 무엇을 가리키며, eip[3]은 무엇인가?", K.TEAL, 15)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2",
         "exec 뒤에도 LDT 베이스가 그대로인 이유는? 바뀌는 것은 무엇인가?", K.TEAL, 15)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3",
         "exec가 성공했는데도 /bin/ls의 코드가 아직 메모리에 없다. 언제, 누가 읽는가?", K.TEAL, 15)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4",
         "실행 권한이 없는 파일을 exec하면 0.11은 어떤 errno를 돌려주는가? 파일이 디렉터리라면?",
         K.TEAL, 15)

    # 46 이해 확인 정답
    p = d.slide("이해 확인 정답", K.S_QUIZ,
                "근거 줄 번호 포함 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "A1",
         "_sys_execve가 lea EIP(%esp)로 넘긴 커널 스택의 저장된 EIP 위치(system_call.s:201-202). "
         "프레임 오프셋(35-46)상 eip[1]=CS, eip[2]=EFLAGS, eip[3]=OLDESP(사용자 ESP). "
         "344-345가 이 둘을 덮어쓴다.", K.ORANGE, 14)
    qbox(d, p, 1100, 6850, 31500, 2400, "A2",
         "베이스(nr×64MB)는 태스크 슬롯이 정하며 fork.c:52-55에서 고정. "
         "change_ldt(exec.c:162-167)는 같은 베이스를 다시 쓰고 리밋만 바꾼다 "
         "(코드: 텍스트 페이지 올림, 데이터: 64MB).", K.ORANGE, 14)
    qbox(d, p, 1100, 9400, 31500, 2400, "A3",
         "do_execve는 헤더 1블록만 bread(221-225)한다. iret 뒤 첫 명령 fetch"
         "(또는 341-343의 꼬리 0 채움 쓰기)가 부재 폴트를 내고 do_no_page"
         "(memory.c:365-397)가 executable inode에서 블록 4개를 읽는다.", K.ORANGE, 14)
    qbox(d, p, 1100, 11950, 31500, 2400, "A4",
         "실행 비트 없음 → ENOEXEC(exec.c:216-219, EACCES가 아님). "
         "정규 파일이 아니면(디렉터리) → EACCES(205-207). 둘 다 318 이전이라 "
         "구 프로그램으로 돌아가고 라이브러리가 errno를 설정한다.", K.ORANGE, 14)

    # 47 정리·다음 회차 예고
    p = d.slide("정리·다음 회차 예고", K.S_WRAP,
                "kernel/exit.c:102-107·122-123 — 10회차는 오늘 본 두 줄·sigaction 초기화가 왜 필요했는지로 시작한다")
    d.cards(p, [
        ("파트 D «프로그램의 일생» 개막",
         "06 fork — 몸 복제\n07 주소 변환 — 64MB 칸\n08 COW — 첫 쓰기 복사\n"
         "09 exec — 오늘\n\n10 종료·시그널"),
        ("10회차 예고",
         "자식이 죽으면 부모는\n어떻게 아는가?\nCtrl-C는 어디까지 가는가?\n\n"
         "exit·wait·시그널"),
        ("오늘↔10 연결",
         "exec.c:328-329 두 줄이\ndo_exit(아래 패널)에도 있다\nsigaction 초기화(322-323)\n"
         "close_on_exec 정리도 재회\n미리 볼 파일: exit.c·signal.c"),
    ], y=4400, h=7400)
    d.code_panel(p, "src/kernel/exit.c", 106, 107, 1100, 12100, 15200, 3000,
                 size=9, caption_extra="do_exit — 10회차에서 다시 본다")
    para(d, p, 16900, 12100, 15700, 3000,
         "exec와 exit가 같은 두 줄로 주소 공간을 지운다 — 09에서 보고 10에서 완성한다.\n"
         "같은 몸, 다른 프로그램이었던 exec — 끝나면 몸도 반납한다.", 15)


if __name__ == "__main__":
    K.run(globals())
