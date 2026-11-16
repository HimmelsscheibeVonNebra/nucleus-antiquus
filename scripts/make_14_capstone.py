#!/usr/bin/env python3
"""14회차 덱 — 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교
(output/14-capstone.pptx)

계획: materials/slide-plans/14-capstone.md (§2 표 46행 1:1 · §3 앞부분 명세 —
로드맵 01–13 완료·구조도 '전체 점등' · §4 큰 지도·두 레인 상태도 명세 ·
§5 캡처 2종 · §6 이해 확인 · §8 오해 금지).

레이아웃 메모(자기 검수 반영): cards 본문은 18pt 줄≈930단위이므로 4줄 이하 ·
chain/nbox 부제 1줄 · 패널 caption_extra는 짧게(캡션 11pt 최소폭 때문) ·
표 총폭은 우측 패널 x(17200)보다 작게.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="14", total=46, slug="14-capstone",
    part_no="G", part="«종합·실습»",
    title="14. 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교",
    question="`ls /` 한 줄에 지금까지 배운 것이 어떻게 모두 등장하는가?",
    done=13,
    today_line="한 줄(`ls /`)에 04–13의 좌표가 전부 등장한다\n— 새 소스 없이 하나의 경로로 잇는다",
    next_lines=[
        "13 → 14   이제 키보드 입력부터 디스크까지 전부 봤다 — 한 줄로 잇는다",
        "14 → 15   직접 바꿔보자 — 커널 수정 실습",
        "15회차 — 테두리(sys_call_table)와 ⑨(schedule)를 직접 고치고 같은 GDB 방법으로 확인",
    ],
    road_note=("오늘은 새 소스가 아니라 04~13의 '지도의 좌표'(파일:줄)를 하나의 경로에 꿰는 회차다.\n"
               "두 부품: (1) 전체 경로 지도 — 09–22장, (2) 현대 커널 비교 — 32–39장.\n"
               "10단계 전부를 빠짐없이 밟는다(질문부터 정리까지)."),
    STRUCT=dict(
        teal=["proc", "mm", "fs", "blk", "chr", "entry", "main", "lib"],
        today=[],
        flow="키보드 → sh → fork → exec(ls) → namei/inode → buffer → hd → console",
        up="↑ write(1, …) 화면 출력",
        user="sh · ls — 오늘 경로의 시작과 끝",
    ),
)

CHECKS = dict(
    captions={
        9: "src/kernel/chr_drv/keyboard.S:37-50",
        10: "src/kernel/system_call.s:80-92",
        11: "src/kernel/system_call.s:101-113",
        12: "src/kernel/fork.c:78-92",
        13: "src/fs/exec.c:328-338",
        14: "src/mm/memory.c:374-386",
        15: "src/fs/open.c:145-157",
        16: "src/fs/file_dev.c:24-38",
        17: "src/fs/buffer.c:267-280",
        18: "src/kernel/blk_drv/hd.c:257-267",
        19: "src/kernel/chr_drv/tty_io.c:302-315",
        20: "src/kernel/exit.c:118-133",
        21: "src/kernel/sched.c:130-142",
    },
    required=[
        "전체 점등", "지도의 좌표", "int $0x80", "nr_system_calls",
        "copy_process", "do_execve", "do_no_page", "getblk",
        "wait_on_buffer", "read_intr", "end_request", "unlock_buffer",
        "tell_father", "TASK_ZOMBIE", "sys_waitpid", "switch_to", "ljmp",
        "put_fs_byte", "0xb8000", "0x4000000", "VFS", "dentry",
        "페이지 캐시", "struct page", "mm_struct", "EEVDF", "getdents",
        "상반부", "con_write", "open_namei", "file_read",
        "do_hd_request", "wake_up", "release", "verify_area",
    ],
    prereq=[
        ("keyboard_interrupt", "src/kernel/chr_drv/keyboard.S:37-50"),
        ("copy_process", "src/kernel/fork.c:78-92"),
        ("do_execve", "src/fs/exec.c:328-338"),
        ("do_no_page", "src/mm/memory.c:374-386"),
        ("getblk", "src/fs/buffer.c:267-280"),
        ("switch_to", "src/kernel/sched.c:130-142"),
    ],
    structure_nodes=["system_call.s", "keyboard.S", "tty_io.c", "console.c",
                     "fork.c", "memory.c", "page.s", "exec.c", "buffer.c",
                     "hd.c", "sched.c", "exit.c"],
    capture_slides=[28, 30],
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
               K.fit_size(l2, s2, w - 500, min_size=8), c2v)


def badge(d, p, x, y, w, text, fill=K.ORANGE, h=700, size=13):
    d.shape(p, x, y, w, h, fill)
    d.text(p, x + 150, y + (h - 520) // 2, w - 300, 520, text,
           K.fit_size(text, size, w - 300, min_size=9), K.INK, True)


def qbox(d, p, x, y, w, h, tag, body, tag_color, size=14):
    d.shape(p, x, y, w, h, K.INK)
    d.shape(p, x, y, w, 130, tag_color)
    d.text(p, x + 250, y + 320, w - 500, 500, tag, 15, tag_color, True)
    para(d, p, x + 250, y + 950, w - 500, h - 1150, body, size, K.PAPER)


def chain(d, p, y, items, h=1500, gap=620, x=1100, total=31500,
          s1=13, s2=9):
    """가로 nbox 사슬 — items = [(제목, 부제 1줄), …]"""
    n = len(items)
    w = (total - (n - 1) * gap) // n
    for i, (t, sub) in enumerate(items):
        xi = x + i * (w + gap)
        nbox(d, p, xi, y, w, h, t, sub, K.PAPER, s1=s1, s2=s2)
        if i < n - 1:
            d.text(p, xi + w - 60, y + (h - 700) // 2, gap + 130, 700,
                   "→", 15, K.ORANGE, True)


def vchain(d, p, x, y, w, items, h=1500, gap=500, s1=14, s2=9):
    """세로 nbox 사슬 — 부제 1줄"""
    for i, (t, sub) in enumerate(items):
        yi = y + i * (h + gap)
        nbox(d, p, x, yi, w, h, t, sub, K.PAPER, s1=s1, s2=s2)
        if i < len(items) - 1:
            d.text(p, x + w // 2 - 350, yi + h + 40, 700, gap - 80, "↓",
                   16, K.ORANGE, True)


def listbox(d, p, x, y, w, h, title, body, size=14):
    """cards 모양의 리스트 박스 — 본문 글자 크기·줄 수를 직접 조정할 수 있다."""
    d.shape(p, x, y, w, h, K.PAPER)
    d.shape(p, x, y, w, 150, K.TEAL)
    d.text(p, x + 550, y + 650, w - 1100, 1600, title,
           K.fit_size(title, 21, w - 1100), K.INK, True)
    d.text(p, x + 550, y + 2600, w - 1100, h - 2900,
           wrap_kr(body, (w - 1100) * 0.97, size), size, K.INK)


RING_TITLES = ["① 키 입력·tty_read", "② fork", "③ exec", "④ 페이지 폴트 적재",
               "⑤ open·read \"/\"", "⑥ 버퍼 캐시·hd", "⑦ write → 콘솔",
               "⑧ exit·wait"]


def big_map(d, p, subs, detailed):
    """큰 지도 공통 골격 — 9박스 시계 방향 + 중앙 ⑨ + 테두리 2줄(04·05)."""
    w, dh = 9800, 2600 if not detailed else 2700
    xs = [1100, 11350, 21600]
    gap = 620 if not detailed else 540
    y0 = 4850
    ys = [y0, y0 + dh + gap, y0 + 2 * (dh + gap)]
    pos = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1)]
    for i in range(8):
        c, r = pos[i]
        nbox(d, p, xs[c], ys[r], w, dh, RING_TITLES[i], subs[i],
             K.PAPER, s1=16, s2=10)
    nbox(d, p, xs[1], ys[1], w, dh, "⑨ schedule", subs[8], K.TEAL,
         s1=16, s2=10)

    def glyph(g, gx, gy, size=18):
        d.text(p, gx, gy, 700, 800, g, size, K.ORANGE, True)

    top_gap_c = 1100 + w + (450 - 700) // 2
    mid_gap_c = 11350 + w + (450 - 700) // 2
    glyph("→", top_gap_c, ys[0] + dh // 2 - 350)
    glyph("→", mid_gap_c, ys[0] + dh // 2 - 350)
    glyph("↓", xs[2] + w // 2 - 350, ys[0] + dh + (gap - 800) // 2)
    glyph("↓", xs[2] + w // 2 - 350, ys[1] + dh + (gap - 800) // 2)
    glyph("←", mid_gap_c, ys[2] + dh // 2 - 350)
    glyph("←", top_gap_c, ys[2] + dh // 2 - 350)
    glyph("↑", xs[0] + w // 2 - 350, ys[2] + dh + (gap - 800) // 2)
    glyph("↑", xs[0] + w // 2 - 350, ys[1] + dh + (gap - 800) // 2)
    # 테두리 — 진입/복귀(04)와 타이머 틱(05)은 어디서나 끼어든다
    d.outline(p, 1100, 4130, 31500, 560, K.ORANGE, 70)
    d.text(p, 1400, 4210, 30900, 420,
           "테두리 — int $0x80 진입/복귀 (04) · sched.c:411 set_system_gate(0x80) · "
           "ret_from_sys_call → do_signal : 어느 구간에서나 끼어든다", 11, K.ORANGE, True)
    by = ys[2] + dh + 420
    d.outline(p, 1100, by, 31500, 560, K.ORANGE, 70)
    d.text(p, 1400, by + 80, 27500, 420,
           "테두리 — 타이머 틱 (05) · sched.c:409 IRQ0 · do_timer: "
           "--current->counter → cpl≠0이면 schedule", 11, K.ORANGE, True)
    d.text(p, 29300, by + 700, 3300, 450, "Linux 0.11", 9, K.MUTED)
    return by + 560  # 테두리 하단 — 이 아래부터 여분 텍스트 영역


def populate(d):
    # ── 슬라이드 04 뒤처리 — 종합 회차 각주(§3 '전체 점등' 사유 + 헤더 라벨) ──
    page4 = d.pages.getByIndex(3)
    for i in range(page4.getCount()):
        sh = page4.getByIndex(i)
        try:
            txt = sh.getString()
        except Exception:
            continue
        if txt.startswith("Linux 0.11 · 오늘"):
            sh.setString("Linux 0.11 · 오늘 14회차 — 종합 회차는 누적 대신 '전체 점등': "
                         "`ls /` 경로가 지나는 파일 전부 진한 TEAL")
    d.outline(page4, 10340, 10650, 21760, 1500, K.TEAL, 60)
    d.text(page4, 10600, 10790, 21300, 500,
           "include/ — sched.h · fs.h · sys.h · unistd.h", 13, K.TEAL, True)
    d.text(page4, 10600, 11400, 21300, 700,
           "경로 전체가 거치는 참조점 — 좌표는 22장 지도 2판에", 11, K.TEAL)

    # ── 05 오늘의 추적 규칙 (배경) ─────────────────────────────
    p = d.slide("오늘의 추적 규칙", K.S_BG,
                "한 명령을 따라가며 세 가지만 기록한다 — 나머지는 이 세 축으로 재배열된다")
    d.cards(p, [
        ("① 지금 누가 RUNNING인가",
         "매 순간 CPU는 정확히\n하나의 태스크에서 실행\n전환은 schedule()만\n— 오늘 지도 ⑨ (21장)"),
        ("② 커널에 어떻게 들어왔나",
         "시스템 콜 int $0x80\nIRQ 0 · 1 · 14\n예외 14 (페이지 폴트)\n다섯 종류뿐 — 25장 비교 ①"),
        ("③ 무엇이 바뀌었나",
         "state · counter · signal\nb_lock · b_uptodate\nexit_code · task[] 슬롯\n기록 표는 24장"),
    ], y=4600, h=6400)
    para(d, p, 1100, 11400, 31500, 2800,
         "호출 순서도(실선)와 상태 변화도(점선)는 다르다 — 2회차 약속 재확인.\n"
         "오늘 09–21장은 순서도(어느 함수가 어느 함수를 부르나)를, 23–24장은 상태도(누가 잠들고 깨나)를 그린다.",
         16)
    d.banner(p, "한 명령, 세 가지 기록 — 상태 · 진입 · 데이터")

    # ── 06 큰 지도 1판 (구조) ──────────────────────────────────
    p = d.slide("큰 지도 (1판) — `ls /`의 아홉 구간", K.S_MAP,
                "본문 09–21장은 이 지도의 해당 박스를 ORANGE로 부각해 확대한다 — 박스마다 회차 번호와 핵심 함수")
    free_y = big_map(d, p, [
        "13회차 — keyboard_interrupt · tty_read",
        "06회차 — sys_fork · copy_process",
        "09회차 — do_execve",
        "08회차 — do_no_page",
        "12회차 — open_namei · file_read",
        "11회차 — getblk · do_hd_request",
        "13회차 — tty_write · con_write",
        "10회차 — do_exit · sys_waitpid",
        "05회차 — schedule · switch_to\n중앙 — 모든 구간 사이",
    ], detailed=False)
    para(d, p, 1100, free_y + 120, 26000, 1300,
         "시계 방향 ①→⑧은 곧 시간 순서 — ⑨ schedule과 테두리(04·05)는 어느 구간에서나 끼어든다. "
         "2판(22장)이 좌표 기입 완성판이다.", 13, K.MUTED)

    # ── 07 지도를 읽는 법: 세 축 (배경) ────────────────────────
    p = d.slide("지도를 읽는 법: 세 축 — 화살표 범례와 두 레인", K.S_BG,
                "실선=함수 호출 · 점선=상태 변화(잠듦/깨움) · 번개(▽)=하드웨어 인터럽트 — 09–26장 전체의 범례")
    d.cards(p, [
        ("실선 — 함수 호출",
         "같은 문맥의 호출\nbread → getblk → …\n(09–21장 순서도)"),
        ("점선 — 상태 변화",
         "잠듦(sleep_on) ↔ 깨움(wake_up)\n(23–24장 상태도)"),
        ("▽ 번개 — 하드웨어",
         "IRQ1 · IRQ14 · IRQ0\nCPU 밖에서 끼어든다 (18장)"),
    ], y=4300, h=5400)
    # 두 레인 타임라인 축 (미니판 — 본판은 23장)
    d.shape(p, 5400, 10050, 26800, 70, K.LINE)
    d.text(p, 29500, 9700, 3100, 500, "시간 →", 13, K.MUTED, True)
    d.outline(p, 1100, 10450, 4100, 1200, K.TEAL, 70)
    d.text(p, 1300, 10680, 3800, 900, "셸 (부모) 레인", 14, K.TEAL, True)
    d.outline(p, 1100, 12050, 4100, 1200, K.ORANGE, 70)
    d.text(p, 1300, 12280, 3800, 900, "ls (자식) 레인", 14, K.ORANGE, True)
    for x, w, col, lab in [(5400, 5200, K.MUTED, "잠듦 — tty_read"),
                           (10720, 4800, K.TEAL, "RUNNING"),
                           (15640, 6600, K.MUTED, "잠듦 — waitpid"),
                           (22360, 4000, K.TEAL, "RUNNING"),
                           (26480, 5720, K.MUTED, "잠듦 — 다음 read")]:
        d.outline(p, x, 10530, w, 1000, col, 70)
        d.text(p, x + 200, 10730, w - 300, 600, lab, 11, col, True)
    d.outline(p, 13040, 12130, 5300, 1000, K.ORANGE, 70)
    d.text(p, 13240, 12330, 5000, 600, "자식 — fork 뒤에만 존재", 11,
           K.ORANGE, True)
    para(d, p, 1100, 13400, 31500, 1200,
         "두 레인 본판은 23장 — 같은 시간축에 셸과 ls의 state를 나란히 놓는다.", 15)

    # ── 08 전제: lab 환경의 셸과 ls (배경) ─────────────────────
    p = d.slide("전제: lab 환경의 셸과 ls", K.S_BG,
                "선언 슬라이드 — 오늘 추적 대상의 경계를 먼저 못박는다(§8: 'ls가 최소 경로만 부른다'고 단정하지 않는다)")
    d.cards(p, [
        ("lab 루트 FS의 바이너리",
         "/bin/sh 와 /bin/ls 는 외부 바이너리\n소스는 이 강좌 범위 밖\n오늘은 커널 쪽 좌표만 쓴다"),
        ("최소 경로 선언",
         "실제 ls는 opendir·stat 등 추가로 부름\n오늘은 최소 경로만 추적 —\nopen·read·write·exit\n(+ fork·execve·waitpid)"),
        ("셸 내부 — 결과에서 추론",
         "셸 구현도 범위 밖 — 1회차처럼\n관찰된 동작에서 추론\nread·fork·waitpid·read 반복이면\n설명이 남는다"),
    ], y=4400, h=6600)
    para(d, p, 1100, 11400, 31500, 3000,
         "추적 규칙(05장)도 이 전제 위에 있다 — 'ls / 한 번'은 곧 '셸의 read 1회 + fork 1회 + 자식의 "
         "execve·open·read·write·exit 1회씩 + 셸의 waitpid·read'로 세는 것이다.\n"
         "시연 A(27장)의 중단점 로그가 이 최소 경로를 실측으로 교정한다.", 15)
    d.banner(p, "오늘의 `ls /` = 최소 경로 open·read·write·exit — 그 외 호출은 로그로만 확인한다")

    # ── 09 ① 키 입력 (코드) ───────────────────────────────────
    p = d.slide("① 키 입력 → 셸의 read가 깨어남 (13)", K.S_CODE,
                "keyboard.S:37-53·88-110 → tty_io.c:145-228 → wake_up(227) → tty_read(230-288) — 13회차 좌표 재인용")
    chain(d, p, 4250, [
        ("▽ IRQ1 — 글자마다", "keyboard.S:37-53"),
        ("put_queue → read_q", "keyboard.S:88-110"),
        ("copy_to_cooked", "tty_io.c:145-228"),
        ("wake_up(227)", "tty_io.c:227"),
        ("tty_read 복사", "put_fs_byte ×5"),
    ], h=1600)
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 37, 50,
                 1100, 6000, 15200, 8400, size=9, caption_extra="13회차 IRQ1")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 261, 269,
                 17200, 6000, 15400, 6400, size=10, caption_extra="13회차")
    badge(d, p, 17200, 12700, 15400,
          "\"ls /\\n\" 5바이트 — do-while 루프로 한 글자씩", K.TEAL, 800)
    nbox(d, p, 17200, 13800, 15400, 600,
         "셸 state: INTERRUPTIBLE → RUNNING (Enter에서)", None, K.ORANGE,
         s1=12)
    para(d, p, 1100, 14550, 15200, 1600,
         "진입 종류 — 읽히는 동안 글자마다 IRQ1, 복귀는 sys_read의 ret_from_sys_call(10–11장).", 12)

    # ── 10 시스템 콜 테두리 — 진입 (코드) ──────────────────────
    p = d.slide("시스템 콜 테두리 — 진입 (04)", K.S_CODE,
                "kernel/system_call.s:80-100 · kernel/sched.c:411 set_system_gate(0x80,&system_call) — 지도의 바깥 테두리(전반)")
    d.code_panel(p, "src/kernel/system_call.s", 80, 92,
                 1100, 4400, 15200, 8750, size=10, caption_extra="04회차 진입")
    d.code_panel(p, "src/kernel/system_call.s", 93, 100,
                 17200, 4400, 15400, 6440, size=11, caption_extra="04회차")
    badge(d, p, 17200, 11100, 15400,
          "sched.c:411 — set_system_gate(0x80,&system_call) · DPL3", K.TEAL, 800)
    para(d, p, 17200, 12200, 15400, 2200,
         "movl $0x17,%edx → fs — 사용자 데이터 세그먼트.\n"
         "put_fs_byte/get_fs_byte 가 이 fs(0x17)로 경계를 넘는다(26장).", 13)

    # ── 11 시스템 콜 테두리 — 복귀와 실행 횟수 (코드) ───────────
    p = d.slide("시스템 콜 테두리 — 복귀와 실행 횟수 (04)", K.S_CODE,
                "kernel/system_call.s:101-119 — 사용자 모드 복귀 시 시그널 검사 → do_signal · 오늘 경로의 최소 6번")
    d.code_panel(p, "src/kernel/system_call.s", 101, 113,
                 1100, 4400, 15200, 8750, size=10, caption_extra="04회차 복귀")
    d.table(p, 17200, 4400, [4400, 3400, 7600], [
        ["시스템 콜", "번호", "지도 구간"],
        ["read — 셸", "3", "① 키 입력"],
        ["fork", "2", "② 셸의 fork"],
        ["execve", "11", "③ 자식의 exec"],
        ["open", "5", "⑤ open(\"/\")"],
        ["read — ls", "3", "⑤→⑥ 디렉터리 블록"],
        ["write", "4", "⑦ 결과 출력"],
        ["exit", "1", "⑧ 자식 종료"],
        ["waitpid", "7", "⑧ 셸 회수"],
    ], row_h=900, size=13)
    para(d, p, 17200, 12900, 15400, 1500,
         "이 표의 모든 행이 같은 어셈블리(80–119)를 지난다 — 번호는 include/unistd.h.", 13)

    # ── 12 ② 셸이 fork한다 (코드) ─────────────────────────────
    p = d.slide("② 셸이 fork한다 (06)", K.S_CODE,
                "system_call.s:208-219 → fork.c:68-133 · copy_mem(39-66) nr*0x4000000 · copy_page_tables(memory.c:150-189, 183)")
    d.code_panel(p, "src/kernel/system_call.s", 208, 219,
                 1100, 4400, 15200, 8200, size=10, caption_extra="06회차 fork")
    d.code_panel(p, "src/kernel/fork.c", 78, 92,
                 17200, 4400, 15400, 9025, size=9, caption_extra="06회차")
    nbox(d, p, 1100, 12950, 7350, 1400, "복사되는 것",
         "task_struct·LDT·TSS·filp 참조", K.PAPER, s1=13, s2=10)
    nbox(d, p, 8950, 12950, 7350, 1400, "공유되는 것",
         "페이지(RO) — mem_map[]++ (183)", K.PAPER, s1=13, s2=10)
    badge(d, p, 17200, 13750, 15400,
          "p->counter = p->priority (85) · 부모·자식 모두 int $0x80 복귀 지점에서 재개", K.ORANGE, 700)

    # ── 13 ③ 자식이 exec한다 (코드) ───────────────────────────
    p = d.slide("③ 자식이 exec한다 (09)", K.S_CODE,
                "system_call.s:200-205 → exec.c:182-353 · 333 change_ldt · 334 create_tables · 344 eip[0] — PID 불변")
    d.code_panel(p, "src/fs/exec.c", 328, 338,
                 1100, 4400, 15200, 7650, size=10, caption_extra="09회차")
    d.code_panel(p, "src/fs/exec.c", 339, 346,
                 17200, 4400, 15400, 6000, size=10, caption_extra="09회차 eip[0]")
    para(d, p, 17200, 10700, 15400, 1500,
         "코드 자체는 아직 메모리에 없다 — 다음 장(④)의 페이지 폴트가 가져온다.",
         15, K.ORANGE, True)
    d.flow(p, [
        ("namei", "12회차와 같은 탐색"),
        ("a.out 헤더 bread", "1블록 — 11회차 캐시"),
        ("free_page_tables", "공유 페이지 반납"),
        ("change_ldt·create_tables", "333 · 334"),
        ("eip[0] = a_entry", "344 — PID 불변"),
    ], y=12500, h=1900, title_size=14)

    # ── 14 ④ 첫 명령어에서 페이지 폴트 (코드) ──────────────────
    p = d.slide("④ 첫 명령어에서 페이지 폴트 (08)", K.S_CODE,
                "kernel/traps.c:199 set_trap_gate(14) · mm/page.s:14-32 · mm/memory.c:365-397 — 08회차 좌표 재인용")
    d.flow(p, [
        ("iret → a_entry", "exec가 저장한 주소"),
        ("예외 14", "첫 fetch — 매핑 없음"),
        ("page.s _page_fault", "CR2 · testl $1"),
        ("do_no_page", "memory.c:365-397"),
        ("bmap×4 → bread_page", "블록 4 = 페이지 1"),
        ("put_page", "393 — 같은 명령 재실행"),
    ], y=4150, h=2200, title_size=14)
    d.code_panel(p, "src/mm/page.s", 24, 32,
                 1100, 6500, 15200, 6550, size=10, caption_extra="08회차")
    d.code_panel(p, "src/mm/memory.c", 374, 386,
                 17200, 6500, 15400, 8035, size=9, caption_extra="08회차 세 갈래")
    badge(d, p, 1100, 13300, 15200,
          "자식 state — 디스크 대기 동안 UNINTERRUPTIBLE · 폴트 횟수는 시연 B(29장)에서 센다",
          K.ORANGE, 800)

    # ── 15 ⑤ open("/") (코드) ─────────────────────────────────
    p = d.slide("⑤ open(\"/\") (12)", K.S_CODE,
                "open.c:138-185 → namei.c:337-410 open_namei → 278-294 dir_namei → 228-270 get_dir → inode.c:244-292 iget")
    d.code_panel(p, "src/fs/open.c", 145, 157,
                 1100, 4400, 15200, 8035, size=9, caption_extra="12회차")
    vchain(d, p, 17200, 4400, 15400, [
        ("sys_open", "open.c:145-157 — 빈 filp·file 탐색"),
        ("open_namei", "namei.c:337-410"),
        ("dir_namei", "namei.c:278-294"),
        ("get_dir — 경로가 \"/\"뿐", "namei.c:241-245 — current->root"),
        ("iget", "inode.c:244-292 — 캐시 히트면 디스크 없음"),
    ])
    badge(d, p, 1100, 12800, 15200,
          "\"/\" 한 글자 → 탐색 없이 current->root → filp[fd] ↔ file_table[] 연결", K.TEAL, 800)
    para(d, p, 1100, 13800, 15200, 900,
         "dir_namei→get_dir→find_entry 사슬 전체는 12회차 — 오늘은 좌표만 지도에 얹는다.", 13)

    # ── 16 ⑥ read(dirfd) → 디렉터리 블록 (코드) ────────────────
    p = d.slide("⑥ read(dirfd) → 디렉터리 블록 (12→11)", K.S_CODE,
                "read_write.c:72-77 → file_dev.c:17-46 file_read · bmap(inode.c:140-143) → bread — 디렉터리도 read()다")
    d.code_panel(p, "src/fs/file_dev.c", 24, 38,
                 1100, 4400, 15200, 9025, size=9, caption_extra="12→11회차")
    d.code_panel(p, "src/fs/read_write.c", 72, 77,
                 17200, 4400, 15400, 5230, size=11, caption_extra="12회차 file_read")
    d.code_panel(p, "src/include/linux/fs.h", 157, 160,
                 17200, 9900, 15400, 4070, size=11, caption_extra="dir_entry")
    nbox(d, p, 1100, 13850, 2400, 600, "inode 2B", None, K.TEAL, s1=12)
    nbox(d, p, 3700, 13850, 2400, 600, "name 14B", None, K.TEAL, s1=12)
    nbox(d, p, 6300, 13850, 2400, 600, "inode 2B", None, K.MUTED, s1=12)
    nbox(d, p, 8900, 13850, 2400, 600, "name 14B", None, K.MUTED, s1=12)
    d.text(p, 11500, 13950, 5000, 500, "… ×64 — 1블록 1024B", 12, K.MUTED, True)
    para(d, p, 1100, 14650, 15200, 900,
         "ls 입장에서 디렉터리는 그냥 파일 — 해석(dir_entry)은 사용자 몫.", 12)

    # ── 17 ⑥ 버퍼 캐시 요청 (코드) ─────────────────────────────
    p = d.slide("⑥ 버퍼 캐시 히트/미스 — 요청과 잠듦 (11)", K.S_CODE,
                "buffer.c:267-281 bread · 206-251 getblk · ll_rw_blk.c:145-155·88-143·64-86 · hd.c:294-341 — 요청 경로")
    chain(d, p, 4150, [
        ("bread", "buffer.c:267-280"),
        ("getblk", "해시 히트면 끝"),
        ("ll_rw_block", "ll_rw_blk.c:145-155"),
        ("make_request", "ll_rw_blk.c:88-143"),
        ("add_request", "(dev->request_fn)()"),
        ("do_hd_request·hd_out", "do_hd = read_intr"),
    ], h=1600)
    d.code_panel(p, "src/fs/buffer.c", 267, 280,
                 1100, 5950, 15200, 8380, size=9, caption_extra="11회차")
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 72, 84,
                 17200, 5950, 15400, 8035, size=9, caption_extra="11회차")
    badge(d, p, 17200, 14100, 15400,
          "wait_on_buffer(buffer.c:36-41) — b_lock==1 동안 sleep_on(&bh->b_wait)",
          K.ORANGE, 700)

    # ── 18 ⑥ 버퍼 캐시 완료 (코드) ─────────────────────────────
    p = d.slide("⑥ 버퍼 캐시 완료 — IRQ14에서 깨어나기 (11)", K.S_CODE,
                "완료 경로 — 번개(▽IRQ14) 표기는 07장 범례 · 11회차 답: read()가 디스크에 가는 때 = 캐시 미스일 때만")
    chain(d, p, 4150, [
        ("▽ IRQ14", "0x2E — hd.c:346"),
        ("_hd_interrupt", "EOI · xchgl _do_hd"),
        ("read_intr", "hd.c:250-267"),
        ("end_request", "blk.h:109-125"),
        ("unlock_buffer", "wake_up(&bh->b_wait)"),
        ("잠든 bread 복귀", "b_uptodate=1 → 반환"),
    ], h=1600)
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 257, 267,
                 1100, 5950, 15200, 7650, size=10, caption_extra="11회차 완료")
    d.code_panel(p, "src/kernel/blk_drv/blk.h", 112, 124,
                 17200, 5950, 15400, 8035, size=9, caption_extra="11회차 깨움")
    badge(d, p, 1100, 14000, 15200,
          "hd.c:346 — set_intr_gate(0x2E,&hd_interrupt) · intr 게이트 = IF 자동 차단", K.TEAL, 700)
    badge(d, p, 17200, 14000, 15400,
          "call *%edx — do_hd 콜백 호출 뒤 iret (system_call.s:236-250)", K.TEAL, 700)

    # ── 19 ⑦ write → 화면 (코드) ──────────────────────────────
    p = d.slide("⑦ write(1, …) → 화면 (13)", K.S_CODE,
                "read_write.c:83-96 → tty_io.c:290-326 tty_write(ONLCR) → console.c:445-500 con_write → 313-316 set_cursor")
    chain(d, p, 4150, [
        ("write(1, …)", "fd 1 — fork로 물려받음"),
        ("rw_char", "read_write.c:83-96"),
        ("tty_write", "ONLCR — CR 삽입"),
        ("con_write", "VGA 2바이트씩"),
        ("set_cursor", "console.c:313-316"),
    ], h=1600)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 302, 315,
                 1100, 5950, 15200, 8380, size=9, caption_extra="13회차 ONLCR")
    d.code_panel(p, "src/kernel/chr_drv/console.c", 461, 466,
                 17200, 5950, 15400, 5230, size=11, caption_extra="13회차")
    nbox(d, p, 17200, 11500, 3600, 1600, "'l'", "문자", K.TEAL, s1=13, s2=10)
    nbox(d, p, 20900, 11500, 3600, 1600, "attr", "속성 바이트", K.TEAL, s1=13, s2=10)
    nbox(d, p, 24600, 11500, 3600, 1600, "'s'", "문자", K.MUTED, s1=13, s2=10)
    nbox(d, p, 28300, 11500, 3600, 1600, "attr", "속성 바이트", K.MUTED, s1=13, s2=10)
    para(d, p, 17200, 13350, 15400, 1400,
         "0xb8000 VGA 메모리 — outb 없이 메모리 쓰기만으로 화면이 바뀐다(13회차).", 12)

    # ── 20 ⑧ exit와 wait (코드) ───────────────────────────────
    p = d.slide("⑧ exit와 wait (10)", K.S_CODE,
                "exit.c:102-135 do_exit · 83-100 tell_father · 142-195 sys_waitpid · 19-33 release — 10회차 답: 부모는 SIGCHLD로 안다")
    d.code_panel(p, "src/kernel/exit.c", 118, 133,
                 1100, 4400, 15200, 9520, size=9, caption_extra="10회차 do_exit")
    d.code_panel(p, "src/kernel/exit.c", 87, 95,
                 17200, 4400, 15400, 6550, size=10, caption_extra="10회차 SIGCHLD")
    nbox(d, p, 17200, 11200, 7400, 1600, "자식 — ZOMBIE",
         "do_exit: state=4 · exit_code", K.INK, K.PAPER, K.PAPER, s1=13, s2=10)
    nbox(d, p, 25200, 11200, 7400, 1600, "release — 소멸",
         "exit.c:19-33 · task[nr]=NULL", None, K.MUTED, s1=13, s2=10)
    nbox(d, p, 17200, 12950, 15400, 1500, "부모 — waitpid 잠듦 → SIGCHLD로 깨어나 회수",
         "sys_waitpid — verify_area(exit.c:147) · 폴링 아님", None, K.ORANGE,
         s1=13, s2=10)

    # ── 21 ⑨ schedule은 몇 번? (코드) ─────────────────────────
    p = d.slide("⑨ 그 사이 schedule은 몇 번? (05)", K.S_CODE,
                "sched.c:104-142 schedule · 305-336 do_timer · 151-193 sleep_on/wake_up · system_call.s:96-99 reschedule — 05회차")
    d.table(p, 1100, 4400, [4600, 6300, 4600], [
        ["호출 지점", "함수 · 줄", "조건"],
        ["잠듦 안에서", "sleep_on → schedule\n(sched.c:162)", "tty_read·버퍼·waitpid"],
        ["do_exit 끝", "schedule (exit.c:133)", "자식 RUNNING 아님"],
        ["시스템 콜 복귀", "reschedule\n(system_call.s:96-99)", "state≠0·counter==0"],
        ["타이머 틱", "do_timer → schedule\n(sched.c:332-335)", "cpl≠0일 때만"],
    ], row_h=1150, size=11)
    d.code_panel(p, "src/kernel/sched.c", 130, 142,
                 17200, 4400, 15400, 8035, size=9, caption_extra="05회차")
    badge(d, p, 17200, 12800, 15400,
          "switch_to — sched.h:171-184 · ljmp TSS", K.TEAL, 700)
    badge(d, p, 17200, 13700, 15400,
          "do_timer — --current->counter, 커널 모드(cpl==0)면 참지 않는다", K.TEAL, 700)
    para(d, p, 1100, 10600, 15500, 3600,
         "한 번의 `ls /` 동안 schedule은 저 지점 전부에서 여러 번 불린다 — 정확한 횟수는 타이머 틱에 달렸다(관찰은 31장).\n"
         "선택 규칙은 언제나 같다: state==RUNNING인 태스크 중 counter 최대 → switch_to로 TSS 전환.", 14)

    # ── 22 큰 지도 2판 (구조) ──────────────────────────────────
    p = d.slide("큰 지도 (2판: 좌표 기입) — 완성판", K.S_MAP,
                "인쇄용 1장 — 각 박스에 파일:줄 좌표와 진입 종류(syscall/IRQ/예외)까지 기입 · 수강생이 가져간다(45장)")
    free_y = big_map(d, p, [
        "keyboard.S:37-77 · tty_io.c:145-288\n진입: IRQ1 + read(3)",
        "system_call.s:208-219 · fork.c:68-133\n진입: fork(2)",
        "system_call.s:200-205 · exec.c:182-353\n진입: execve(11)",
        "traps.c:199 · page.s:14-32 · memory.c:365-397\n진입: 예외 14",
        "open.c:138-185 · namei.c:228-410 · inode.c:244-292\n진입: open(5) · read(3)",
        "buffer.c:36-281 · ll_rw_blk.c:64-155 · hd.c:180-341\n진입: IRQ14(0x2E)",
        "tty_io.c:290-326 · console.c:445-616\n진입: write(4)",
        "exit.c:19-195\n진입: exit(1) · waitpid(7)",
        "sched.c:104-193 · sched.h:171-184\n상시 — 틱·잠듦·reschedule마다",
    ], detailed=True)
    para(d, p, 1100, free_y + 100, 26000, 1300,
         "헤더 참조점 — include/linux/sched.h · fs.h · sys.h · include/unistd.h(04장 라벨). "
         "줄 번호는 src/ 원본 기준, 실행은 lab/ — 00-common §1.", 12, K.MUTED)

    # ── 23 상태 변화도 1/2 (상태도) ────────────────────────────
    p = d.slide("상태 변화도 (1/2): 셸과 ls 두 레인", K.S_STATE,
                "시간축 좌→우 · RUNNING=TEAL · 잠듦(둘 다)=MUTED 외곽선 · ZOMBIE=INK · 범례는 07장 세 축")
    d.shape(p, 5400, 4380, 26800, 60, K.LINE)
    d.text(p, 29500, 4100, 3100, 500, "시간 →", 12, K.MUTED, True)
    for tx, lab in [(13040, "fork"), (16060, "exec"), (26420, "exit·SIGCHLD")]:
        d.text(p, tx, 4100, 3400, 500, lab, 10, K.ORANGE, True)
    d.outline(p, 1100, 4900, 4100, 1400, K.TEAL, 70)
    d.text(p, 1300, 5150, 3800, 1000, "셸 (부모)\npid 불변", 13, K.TEAL, True)
    d.outline(p, 1100, 8200, 4100, 1400, K.ORANGE, 70)
    d.text(p, 1300, 8450, 3800, 1000, "ls (자식)\nfork 뒤 존재 → 소멸", 12,
           K.ORANGE, True)
    parent = [
        (5400, 2200, "RUNNING", "read 진입 전", K.TEAL, K.INK),
        (7720, 5200, "INTERRUPTIBLE", "tty_read 대기", None, K.MUTED),
        (13040, 3000, "RUNNING", "Enter·fork()", K.TEAL, K.INK),
        (16160, 10600, "INTERRUPTIBLE", "waitpid 대기", None, K.MUTED),
        (26880, 2600, "RUNNING", "SIGCHLD 회수", K.TEAL, K.INK),
        (29600, 2600, "INTERRUPTIBLE", "다음 read", None, K.MUTED),
    ]
    for x, w, l1, l2, fill, col in parent:
        nbox(d, p, x, 4900, w, 1400, l1, l2, fill, col, s1=12, s2=9)
    child = [
        (13040, 2900, "RUNNING", "copy_process", K.TEAL, K.INK),
        (16060, 3200, "RUNNING (그대로)", "exec — 공간만", K.TEAL, K.INK),
        (19380, 4700, "UNINT ⇄ RUN", "폴트·미스 왕복", None, K.MUTED),
        (24200, 2100, "RUNNING", "write", K.TEAL, K.INK),
        (26420, 2600, "ZOMBIE", "exit_code 남김", K.INK, K.PAPER),
        (29140, 3060, "· · · 소멸 · · ·", "task[] NULL", None, K.MUTED),
    ]
    for x, w, l1, l2, fill, col in child:
        nbox(d, p, x, 8200, w, 1400, l1, l2, fill, col,
             c2=K.PAPER if fill is K.INK else None, s1=12, s2=9)
    para(d, p, 5400, 6650, 7400, 900,
         "글자마다 ▽IRQ1 → copy_to_cooked → wake_up(tty_io.c:227)", 10, K.MUTED)
    para(d, p, 16400, 6650, 10200, 900,
         "sys_waitpid(exit.c:142) — 자식 ZOMBIE 없으면 계속 잠듦", 10, K.MUTED)
    d.text(p, 14250, 6650, 900, 800, "↓", 20, K.ORANGE, True)
    para(d, p, 13100, 7500, 6800, 700, "fork — copy_process(fork.c:68)", 10,
         K.ORANGE, True)
    d.text(p, 27900, 6650, 900, 800, "↑", 20, K.ORANGE, True)
    para(d, p, 24500, 7500, 7700, 700, "tell_father — SIGCHLD 비트(exit.c:93)",
         10, K.ORANGE, True)
    para(d, p, 19500, 9900, 12200, 900,
         "잠듦 sleep_on(buffer.c:36-41) ↔ 깨움 ▽IRQ14 wake_up(blk.h:106) — 왕복", 10,
         K.MUTED)
    nbox(d, p, 5400, 10900, 8600, 700, "RUNNING — TEAL 채움", None,
         K.TEAL, s1=12)
    nbox(d, p, 14500, 10900, 9600, 700,
         "잠듦(INT/UNINT) — 외곽선만", None, K.MUTED, s1=12)
    nbox(d, p, 24600, 10900, 8000, 700, "ZOMBIE — INK 채움", None,
         K.INK, K.PAPER, s1=12)
    para(d, p, 1100, 11900, 31500, 2600,
         "exec는 state를 바꾸지 않는다 — 주소 공간만 교체한다(13장). 잠듦·깨움의 원인과 바뀌는 데이터는 다음 장 표에서.\n"
         "셸의 INTERRUPTIBLE↔RUNNING 반복(①)과 자식의 왕복(④⑥)이 같은 시간축에서 겹친다.", 14)

    # ── 24 상태 변화도 2/2 (상태도) ────────────────────────────
    p = d.slide("상태 변화도 (2/2): 전환의 원인·데이터·유지 조건", K.S_STATE,
                "ZOMBIE→소멸은 release(exit.c:19-33)에서 task[] 슬롯 NULL — 좌표는 §1 읽기 범위 표")
    d.table(p, 1100, 4400, [6800, 11100, 6700, 6900], [
        ["전환", "원인 (함수:줄)", "변경 데이터", "유지 조건"],
        ["셸 RUN → INT", "tty_read — interruptible_sleep_on(sched.c:167)", "state=1 · alarm", "줄(行) 미완성 — secondary 비었음"],
        ["셸 INT → RUN", "Enter — copy_to_cooked → wake_up(tty_io.c:227)", "state=0", "—"],
        ["자식 탄생 (RUN)", "copy_process — fork.c:80-85", "task[nr] · state=0 · counter=priority", "—"],
        ["자식 UNINT ⇄ RUN", "wait_on_buffer(buffer.c:36-41) ↔ ▽IRQ14 wake_up(blk.h:106)", "state · b_lock · b_uptodate", "b_lock==1인 동안 잠듦"],
        ["자식 RUN → ZOMBIE", "do_exit — exit.c:130-133", "state=4 · exit_code", "부모 회수 전까지"],
        ["셸 INT → RUN (회수)", "SIGCHLD — tell_father(exit.c:93) → sys_waitpid", "signal 비트 · exit_code 회수", "자식 ZOMBIE 없으면 계속 잠듦"],
        ["ZOMBIE → 소멸", "release — exit.c:19-33", "task[nr]=NULL · 페이지·fd 반납", "부모가 회수할 때만"],
    ], row_h=1180, size=12)
    para(d, p, 1100, 14000, 31500, 1400,
         "state: 0=RUNNING · 1=INTERRUPTIBLE · 2=UNINTERRUPTIBLE · 4=ZOMBIE (sched.h). "
         "같은 잠듦도 시그널로 깨일 수 있으면 INTERRUPTIBLE이다.", 13)

    # ── 25 비교 ① 진입 다섯 종류 (비교) ────────────────────────
    p = d.slide("비교 ①: 이 한 명령 동안의 커널 진입 다섯 종류", K.S_CMP,
                "게이트 종류·등록 위치·IF 자동 차단·스택 전환 — 04회차 구분의 종합판")
    d.table(p, 1100, 4400, [6200, 9200, 4400, 5300, 6400], [
        ["진입", "게이트 · 등록", "IF 자동 차단", "스택 전환", "이 명령에서 언제"],
        ["시스템 콜 int $0x80", "system gate(DPL3) · sched.c:411", "아니오 — 유지", "CPL3→0 · TSS esp0", "read·fork·execve·open·read·write·exit·waitpid"],
        ["타이머 IRQ0", "intr gate 0x20 · sched.c:409", "예 — 차단", "당시 CPL에 따라", "counter==0이면 어디서나"],
        ["키보드 IRQ1", "trap gate 0x21 · console.c:683", "아니오 — 유지", "입력 순간 CPL3→0", "글자 하나마다 (①)"],
        ["디스크 IRQ14", "intr gate 0x2E · hd.c:346", "예 — 차단", "잠든 뒤 커널 문맥", "캐시 미스 블록마다 (⑥)"],
        ["예외 14 — 페이지 폴트", "trap gate · traps.c:199", "아니오 — 유지", "첫 fetch CPL3→0", "exec 직후·페이지마다 (④)"],
    ], row_h=1350, size=13)
    para(d, p, 1100, 12800, 31500, 1800,
         "스택 전환은 'CPL3에서 발생했을 때만' TSS에서 esp0을 가져온다는 뜻이다 — 커널 안에서 난 IRQ는 같은 커널 스택에서 이어진다(04회차).\n"
         "IRQ0과 IRQ14가 IF를 차단하므로 완료 경로(18장)는 짧게 끝낸다.", 14)
    d.banner(p, "다섯 종류가 한 명령 안에 섞여 일어난다 — 핵심 질문의 답(42장)")

    # ── 26 데이터 흐름 한 장 (코드) ────────────────────────────
    p = d.slide("데이터 흐름 한 장 — 세 개의 복사 경로", K.S_CODE,
                "tty_io.c(큐) · fs/buffer.c · console.c(0xb8000) — 경계는 항상 get_fs_byte/put_fs_byte (fs=0x17, 10장)")
    flows = [
        ("입력 \"ls /\\n\" — 5바이트",
         [("키보드 ▽IRQ1", "scan code"), ("read_q", "keyboard.S:88"),
          ("copy_to_cooked", "tty_io.c:145"), ("secondary", "줄 버퍼"),
          ("셸 버퍼", "put_fs_byte ×5")],
         "echo 글자도 write_q로\n사용자에게 보인다"),
        ("파일 — 디렉터리 블록 1024B",
         [("hd ▽IRQ14", "블록 장치"), ("buffer", "bread·getblk"),
          ("file_read", "put_fs_byte 루프"), ("ls 버퍼", "dir_entry ×64")],
         "hd까지 가는 것은\n캐시 미스일 때뿐"),
        ("출력 — 결과 문자열",
         [("ls 버퍼", "write(1,…)"), ("write_q", "get_fs_byte"),
          ("con_write", "CR 삽입·해석"), ("0xb8000", "2바이트씩")],
         "커널이 곧 화면 —\noutb 없이 메모리 쓰기"),
    ]
    for fi, (title, items, foot) in enumerate(flows):
        y = 4350 + fi * 3200
        d.text(p, 1100, y, 10500, 700, title, 15, K.TEAL, True)
        chain(d, p, y + 800, items, h=1500, x=1100, total=24700, s1=12, s2=9)
        para(d, p, 26300, y + 850, 6300, 1500, foot, 11, K.MUTED)
    d.banner(p, "세 흐름 모두 경계에서 fs 세그먼트(0x17)로 사용자 공간을 넘는다 — 복사 횟수가 곧 비용")

    # ── 27 시연 A (시연) ───────────────────────────────────────
    p = d.slide("시연 A: 중단점 열 개로 한 명령 녹화", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜는 캡처 확보 시 기재 — 멈추지 않고 로그만 남긴다(§5)")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — 열 개 중단점 자동 계속 로깅",
              "(gdb) target remote :1234\n"
              "(gdb) set logging file build/gdb-14-ls.txt\n"
              "(gdb) set logging on\n"
              "(gdb) b sys_fork\n"
              "(gdb) commands\n"
              " > silent\n"
              " > printf \"sys_fork  pid=%d\\n\", current->pid\n"
              " > c\n"
              " > end\n"
              "# 나머지 9개도 같은 형식 —\n"
              "# do_execve do_no_page sys_open\n"
              "# file_read bread do_hd_request\n"
              "# con_write do_exit sys_waitpid\n"
              "(gdb) c      # 셸에서 ls / 입력", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "절차\n\n"
         "1. scripts/run.sh → QEMU -S -s ·\n"
         "   gdb tools/system · target remote\n"
         "2. 중단점 10개 × commands 자동 계속\n"
         "3. set logging on 후 ls / 한 번\n\n"
         "관찰 대상(§5)\n\n"
         "· 이름·pid 순서 전체\n"
         "· fork 직후 pid 갈라짐\n"
         "· do_no_page 연속 등장\n"
         "· bread 두 번 — exec 헤더·디렉터리\n"
         "· 마지막 do_exit(자식) →\n"
         "  sys_waitpid는 fork 직후(셸이 먼저\n"
         "  waitpid에 들어가 있으므로)", 13)
    d.banner(p, "지도(논리 순서)와 로그(시간 순서)를 대조한다 — 다음 장 캡처")

    # ── 28 시연 A 캡처 (캡처) ──────────────────────────────────
    p = d.slide("시연 A 캡처 — GDB 로그", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜는 확보 시 기재 — 값·순서는 부팅마다 다를 수 있다(§8)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) c\n"
                         "sys_fork       pid=4      # 셸 → 자식 5 태어남\n"
                         "sys_waitpid    pid=4      # 셸이 먼저 잠듦 ★\n"
                         "do_execve      pid=5\n"
                         "bread          pid=5      # a.out 헤더 — open보다 먼저 ★\n"
                         "do_no_page     pid=5\n"
                         "do_no_page     pid=5\n"
                         "do_no_page     pid=5      # 페이지 단위 반복 ★\n"
                         "sys_open       pid=5\n"
                         "file_read      pid=5\n"
                         "bread          pid=5      # 디렉터리 블록\n"
                         "do_hd_request  pid=5\n"
                         "con_write      pid=5\n"
                         "con_write      pid=5      # echo · 결과\n"
                         "do_exit        pid=5\n"
                         "# ★ = 지도 순서와 다른 곳 (아래 각주)",
                         "01-gdb-ls-breakpoint-log.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "각주 — 관찰이 추론을 교정\n\n"
         "★ sys_waitpid가 fork 직후:\n"
         "셸이 미리 waitpid로 잠들어 있어 로그 먼저.\n\n"
         "★ bread가 sys_open보다 먼저:\n"
         "exec가 a.out 헤더를 읽는 bread.\n\n"
         "★ do_no_page 반복:\n"
         "폴트는 4KB 페이지 단위다(29장에서 센다).\n\n"
         "지도가 틀린 게 아니라 순서가 다른 것 —\n"
         "논리 순서 vs 시간 순서(31장).", 13)

    # ── 29 시연 B (시연) ───────────────────────────────────────
    p = d.slide("시연 B: 페이지 폴트와 디스크 접근 세기", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜는 확보 시 기재 — 게스트 커널의 요청 횟수만 센다(§5)")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — commands silent 로 카운트만",
              "(gdb) set $pf=0\n"
              "(gdb) set $hd=0\n"
              "(gdb) b do_no_page\n"
              "(gdb) commands\n"
              " > silent\n"
              " > set $pf=$pf+1\n"
              " > c\n"
              " > end\n"
              "(gdb) b do_hd_request    # 같은 형식으로 $hd\n"
              "(gdb) c          # 1차 ls / → Ctrl-C\n"
              "(gdb) p $pf\n"
              "(gdb) p $hd\n"
              "# 0으로 리셋 뒤 2차 ls / —\n"
              "(gdb) set $pf=0\n"
              "(gdb) set $hd=0\n"
              "(gdb) c\n"
              "(gdb) p $pf\n"
              "(gdb) p $hd", start=12)
    para(d, p, 22000, 4300, 10000, 10100,
         "기대(§5)\n\n"
         "· $pf(do_no_page) — 두 번 모두\n"
         "  비슷: exec는 매번 새 주소 공간\n\n"
         "· $hd(do_hd_request) — 두 번째가\n"
         "  0 또는 크게 감소: 디렉터리·ls 블록이\n"
         "  버퍼 캐시에 남는다(getblk 해시 히트)\n\n"
         "폴트 처리 안의 bread_page는 캐시 히트 —\n"
         "폴트는 다시 일어나도 hd는 안 간다.\n\n"
         "호스트 측 QEMU 캐시는 안 보인다 —\n"
         "게스트 커널의 요청 횟수만 셈.", 13)
    d.banner(p, "ignore 대신 commands silent — 정지 없이 횟수만 기록한다")

    # ── 30 시연 B 캡처 (캡처) ──────────────────────────────────
    p = d.slide("시연 B 캡처 — 두 번 실행의 카운트", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜는 확보 시 기재 — 값은 예시, 경향만 결론(§8)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "실행         do_no_page($pf)   do_hd_request($hd)\n"
                         "------------------------------------------------\n"
                         "1차 ls /          23                9\n"
                         "2차 ls /          21                1\n"
                         "------------------------------------------------\n"
                         "$pf — 두 번 비슷 (exec마다 새 주소 공간)\n"
                         "$hd — 2차 감소     (버퍼 캐시 히트)\n"
                         "\n"
                         "# 숫자는 ls 크기·루트 FS 이미지·QEMU 설정에\n"
                         "# 따라 다르다 — 경향만 결론으로 말한다",
                         "02-gdb-counts-two-runs.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· $pf 비슷 — 페이지 폴트는 exec마다 재발\n"
         "  (새 주소 공간, memory.c:365-397)\n\n"
         "· $hd 감소 — 두 번째 read는\n"
         "  getblk 해시 히트(buffer.c:206-251)\n\n"
         "'두 번째는 디스크를 전혀 안 읽는다'고\n"
         "단정하지 않는다 — 버퍼 수·다른 접근에\n"
         "따라 달라진다(§8).", 13)

    # ── 31 관찰이 가르쳐 준 것 (정리) ──────────────────────────
    p = d.slide("관찰이 가르쳐 준 것 — 추론 vs 로그", K.S_WRAP,
                "시연 A·B 정리 — 지도는 논리 순서, 로그는 시간 순서 (관찰 vs 추론 구분 슬라이드)")
    d.table(p, 1100, 4400, [9200, 11300, 11000], [
        ["추론 (지도)", "관찰 (로그)", "무엇을 배웠나"],
        ["exec 뒤 바로 open이 온다", "do_execve 직후 bread(a.out 헤더)가 먼저", "순서 역전 — 논리 순서 ≠ 시간 순서"],
        ["폴트는 한두 번이면 충분", "do_no_page가 페이지 수만큼 반복", "반복 단위 = 4KB 페이지(08회차)"],
        ["요청-완료가 짝으로 이어진다", "do_timer 로그를 켜면 아무 데나 끼어듦", "타이머 틱 — 04·05회차의 테두리"],
        ["지도를 그리고 끝", "로그가 지도를 교정한다", "읽기(추론) → 관찰 → 수정 — 15회차도 같은 절차"],
    ], row_h=1750, size=13)
    d.banner(p, "지도는 버리지 않는다 — 관찰로 좌표에 시간 순서를 얹는다")

    # ── 32 비교 ② 규칙 (배경) ──────────────────────────────────
    p = d.slide("비교 ②를 읽는 규칙 — 개념 수준 선언", K.S_BG,
                "현대 커널 소스를 읽지 않았고 VM도 없다 — 이름과 역할만 대응시킨다(§8). 33–39장 공통 머리글")
    d.cards(p, [
        ("개념 수준 선언",
         "현대 소스 안 읽음 · VM 없음\n이름과 역할만 짝지운다\n(33–38장 공통 규칙)"),
        ("말하지 않는 것",
         "버전 번호 · 줄 번호 · 성능 수치\n검증 못 하는 것은 말하지 않는다\n(§8)"),
        ("평가 금지",
         "'복잡하니 나쁘다/좋다' 없음\n바뀐 이유엔 요구 사항만\n적는다"),
    ], y=4400, h=5700)
    d.table(p, 1100, 10600, [10000, 7500, 7600, 6400], [
        ["0.11 메커니즘 (파일:줄)", "현대 Linux 개념", "왜 바뀌었나", "이 강좌에서"],
        ["예 — task[64] 고정 배열 (sched.h:4)", "pid 해시·idr 동적 관리", "태스크 수 요구", "0.11 코드로 다룸"],
    ], row_h=1300, size=12)
    para(d, p, 1100, 13300, 31500, 1300,
         "이 4열이 33–38장 여섯 장의 공통 머리글이다 — 마지막 열은 '0.11 코드로 다룸 / 이름만' 둘뿐이다.", 14)
    d.banner(p, "현대 비교 = 개념 이름의 대응 — 그 이상도 이하도 아니다")

    # ── 33–38 비교 ②-1 … ②-6 (비교) ───────────────────────────
    CMP_HEAD = ["0.11 메커니즘 (파일:줄)", "현대 Linux 개념", "왜 바뀌었나", "이 강좌에서"]
    CMP_W = [10100, 7400, 7600, 6400]

    p = d.slide("비교 ②-1: 태스크와 문맥 전환", K.S_CMP,
                "sched.h:4 · 171-184 · fork.c:141-143 · sched.c:137-139 — 단일 CPU·고정 배열 시대의 설계")
    d.table(p, 1100, 4400, CMP_W, [
        CMP_HEAD,
        ["task[64] 고정 배열 — 선형 탐색 (sched.h:4 · fork.c:141-143)",
         "pid 해시 · idr 기반 동적 태스크 관리", "태스크 수 수천 · 생성·소멸 빈번", "0.11 코드로 다룸"],
        ["switch_to — TSS ljmp (sched.h:171-184)",
         "소프트웨어 문맥 전환 — TSS는 esp0·IO 비트맵용", "전환 비용 · 64비트에 ljmp 없음", "0.11 코드로 다룸"],
        ["counter/priority 재계산 (sched.c:137-139)",
         "CFS · EEVDF 같은 가중 공정 스케줄러", "반응성 · 공정성 요구", "이름만"],
        ["단일 CPU 전제 — 락 없음",
         "런큐 per-CPU · 락킹 · 선점", "SMP", "이름만(39장)"],
    ], row_h=1600, size=13)
    d.banner(p, "지도의 ⑨ schedule — 선택 규칙과 전환 방식이 바뀌었을 뿐 '누가 이어서 실행되는가'는 그대로")

    p = d.slide("비교 ②-2: 주소 공간", K.S_CMP,
                "fork.c:52 nr*0x4000000 · exec.c:161 · memory.c:183·96-97 — 64MB 칸과 mem_map[]")
    d.table(p, 1100, 4400, CMP_W, [
        CMP_HEAD,
        ["태스크당 64MB 고정 세그먼트 (fork.c:52 · exec.c:161)",
         "mm_struct + VMA 구간 목록 — 임의 배치", "큰 주소 공간 · 공유 라이브러리 · ASLR", "0.11 코드로 다룸"],
        ["세그먼트 + 2단 페이징",
         "평탄 세그먼트 · 다단계 페이지 테이블", "4GB 초과 · 64비트", "0.11 코드로 다룸(07회차)"],
        ["mem_map[] 바이트 참조 카운트 (memory.c:183 · 96-97)",
         "struct page + 버디/슬랩 할당기", "메모리 규모 · 파편화 관리", "0.11 다룸 · struct page는 이름만"],
    ], row_h=1600, size=13)
    d.banner(p, "'태스크마다 칸 하나'에서 '구간 목록'으로 — 지도의 ②③④가 사는 틀 자체가 바뀌었다")

    p = d.slide("비교 ②-3: 페이지 폴트 · COW · 적재", K.S_CMP,
                "memory.c:386 · 247-259 · 221-238 · 348-363(share_page) — 원리는 같다, 자료구조가 커졌다")
    d.table(p, 1100, 4400, CMP_W, [
        CMP_HEAD,
        ["do_no_page — 실행 파일에서 직접 bread_page (memory.c:386)",
         "페이지 캐시 기반 매핑 · 파일 기반 폴트 처리", "캐시 통합 · mmap 일반화", "0.11 다룸 · 페이지 캐시는 이름만"],
        ["do_wp_page / un_wp_page — COW (247-259 · 221-238)",
         "같은 원리의 COW + 익명 페이지 · rmap · THP", "규모 · 복사 회수 · 흩어진 매핑", "0.11 코드로 다룸"],
        ["share_page — 같은 executable 공유 (348-363)",
         "같은 파일 매핑의 페이지 공유", "다중 프로세스 라이브러리", "이름만"],
    ], row_h=1600, size=13)
    d.banner(p, "부재 폴트 → 채우기 → 첫 쓰기에 복사 — 30년 넘게 같은 원리다(08회차)")

    p = d.slide("비교 ②-4: 파일 시스템과 캐시", K.S_CMP,
                "namei.c · inode.c · fs.h:43-47 · buffer.c:31 · read_write.c:72-77 — Minix fs가 곧 fs 계층")
    d.table(p, 1100, 4400, CMP_W, [
        CMP_HEAD,
        ["Minix fs 하나가 곧 파일 시스템 코드 (namei.c · inode.c)",
         "VFS 계층 — inode/dentry/file 객체와 연산 테이블", "여러 파일 시스템 공존", "0.11 다룸 · VFS/dentry는 이름만"],
        ["NR_INODE 32 · NR_FILE 64 · NR_OPEN 20 (fs.h:43-45)",
         "동적 할당 · 큰 한도", "열린 파일 수 요구", "0.11 상수로 다룸"],
        ["buffer_head 해시 블록 캐시 (buffer.c:31 · NR_HASH 307)",
         "페이지 캐시 — buffer_head는 일부 경로 보조", "페이지 단위 통합", "0.11 코드로 다룸"],
        ["디렉터리도 read()로 (read_write.c:72-77 — getdents 없음)",
         "getdents 계열 시스템 콜", "구조화 · 가변 엔트리", "0.11 코드로 다룸"],
    ], row_h=1450, size=13)
    d.banner(p, "지도의 ⑤⑥ — 'open·read 하나로 전부'는 유지되되 계층이 갈라졌다")

    p = d.slide("비교 ②-5: 블록 I/O와 인터럽트", K.S_CMP,
                "hd.c:190·262 · tty_io.c:145-228(copy_to_cooked) — 함수 포인터 콜백과 PIC의 시대")
    d.table(p, 1100, 4400, CMP_W, [
        CMP_HEAD,
        ["request[] 배열 + do_hd=read_intr 함수 포인터 콜백 (hd.c:190 · 262)",
         "블록 계층 — bio · 요청 큐 · 멀티큐, 드라이버 분리", "병렬 장치 · 요청 융합", "0.11 코드로 다룸"],
        ["PIC 8259 + 고정 벡터 (0x20 · 0x21 · 0x2E)",
         "APIC · IRQ 도메인", "다중 코어 · MSI", "이름만"],
        ["인터럽트 안에서 copy_to_cooked 직접 실행 (tty_io.c:145-228)",
         "상반부/하반부 분리 — softirq · threaded IRQ", "지연 처리로 응답성", "이름만"],
    ], row_h=1600, size=13)
    d.banner(p, "요청 → 장치 → 완료 콜백 → 깨움(17–18장)의 뼈대는 그대로 — 큐와 지연 처리가 붙었다")

    p = d.slide("비교 ②-6: 터미널과 시스템 콜 표", K.S_CMP,
                "tty_io.c:51-92 · sys.h:74-86 · system_call.s:61 nr_system_calls = 72 — 콘솔 1 · 콜 72개")
    d.table(p, 1100, 4400, CMP_W, [
        CMP_HEAD,
        ["콘솔 1 + rs 2 고정 (tty_io.c:51-92) · con_write가 VGA에 직접",
         "tty 코어 + line discipline + 가상 콘솔 · pty · 프레임버퍼", "다중 터미널 · 그래픽", "0.11 코드로 다룸"],
        ["sys_call_table[72] · int $0x80 (sys.h:74-86 · system_call.s:61)",
         "수백 개 항목 · syscall/sysenter 빠른 진입 · 아키텍처별 표", "보안 · 성능 · 호환", "0.11 코드로 다룸"],
        ["시그널 = 비트마스크 32비트 (signal/blocked — long)",
         "실시간 시그널 · 시그널 큐잉", "더 많은 시그널 · 정보 전달", "0.11 코드로 다룸(10회차)"],
    ], row_h=1600, size=13)
    d.banner(p, "15회차 예고 — 이 표(sys_call_table)에 항목 하나를 직접 추가해 본다")

    # ── 39 다루지 않은 것 (비교) ───────────────────────────────
    p = d.slide("이 강좌가 다루지 않은 것", K.S_CMP,
                "두 열을 구분한다 — '0.11에 아예 없는 것'과 '있지만 강좌 범위 밖인 것'은 다르다(§8)")
    listbox(d, p, 1100, 4400, 15200, 7800, "0.11이 작아서 없는 것",
            "SMP · 락킹 · 선점\n"
            "네트워킹\n"
            "가상 메모리 스왑 (0.11에는 없음)\n"
            "64비트 · 멀티 아키텍처\n"
            "전원 관리 · 장치 트리 · ACPI\n"
            "컨테이너 · cgroup · namespace\n"
            "현대 부팅 — UEFI · initramfs", size=15)
    listbox(d, p, 17200, 4400, 15400, 7800, "강좌 범위라서 다루지 않은 것",
            "커널 모듈 · sched_ext (현대 — 15회차 노트:\n"
            "VM 미선택으로 15회차 0.11 실습으로 대체)\n"
            "VFS 실제 코드 · ext4 등 현대 fs (이름만)\n"
            "보안 — 권한 검사 일부만 다룸\n"
            "0.11 안에서도: floppy·ramdisk·serial 세부\n"
            "signal.c 전체(sys_sigaction 등)", size=15)
    para(d, p, 1100, 12600, 31500, 1800,
         "오늘 비교 슬라이드(32–38장)가 모듈·sched_ext 두 주제를 개념 수준에서만 대신한다 — 검증된 관찰이 없는 주제는\n"
         "이름만 짝지우고 넘어간다는 오늘의 규칙(32장)을 그대로 지킨다.", 15)
    d.banner(p, "'없는 것'과 '안 다룬 것' — 다음에 무엇을 배울지 정할 때 이 표가 지도가 된다")

    # ── 40 바뀌지 않은 것 (정리) ───────────────────────────────
    p = d.slide("바뀌지 않은 것", K.S_WRAP,
                "30년 넘게 유지된 설계 일곱 가지 — 각 항목 옆 번호는 오늘 지도(06장)의 위치")
    d.table(p, 1100, 4400, [23600, 7900], [
        ["한 문장", "지도 위치"],
        ["프로세스 = 주소 공간 + 커널 스택 + 상태", "② ③ ⑧"],
        ["fd 번호로 파일·장치를 같은 read/write로 다룬다", "⑤ ⑦"],
        ["fork / exec / wait / exit — 네 동작의 분업", "② ③ ⑧"],
        ["시그널 = 비동기 통지 비트", "⑧"],
        ["캐시 미스일 때만 장치에 간다", "⑥"],
        ["잠들기·깨우기 = 대기열과 상태 전환", "① ⑥ ⑧ ⑨"],
        ["사용자/커널 경계는 항상 게이트를 통해서만", "테두리 (04)"],
    ], row_h=1120, size=14)
    para(d, p, 1100, 13600, 31500, 900,
         "33–38장의 비교표가 바꾼 것은 '방법'이었다 — 이 일곱 문장의 '원리'는 그대로다.", 15)
    d.banner(p, "현대 커널도 이 일곱 문장으로 읽힌다 — 0.11이 좋은 교재인 이유")

    # ── 41 왜 0.11로 배웠나 (정리) ─────────────────────────────
    p = d.slide("왜 0.11로 배웠나 — 성찰", K.S_WRAP,
                "1만 줄 안에 오늘의 일곱 가지가 전부 있다 — 그리고 한 명령을 끝까지 추적할 수 있다")
    d.cards(p, [
        ("작아서 전부 보인다",
         "1만 줄 안에 지도 ①–⑨와\n일곱 문장(40장)이 전부 있다\nGDB로 `ls /` 한 줄을 끝까지\n추적할 수 있다(27·29장)"),
        ("단순화가 가르치는 것",
         "단일 CPU · 고정 배열 · 동기 콘솔\n없는 것들이 현대 설계의 '이유'를\n드러낸다(SMP·동시성·지연 처리)"),
        ("다음 단계",
         "15회차 — 같은 지도를 직접 수정\n테두리에 항목 하나\n⑨의 선택 규칙 변경"),
    ], y=4400, h=6400)
    qbox(d, p, 1100, 11200, 31500, 2300, "수강생에게",
         "현대 커널에서 같은 지도를 그린다면 어느 박스가 가장 많이 쪼개질까?",
         K.TEAL, 15)
    badge(d, p, 1100, 13700, 31500,
          "답 — ⑥ 버퍼·블록 계층(캐시·큐·드라이버 분리)과 ⑨ 스케줄러(런큐 per-CPU · 클래스)",
          K.ORANGE, 700)

    # ── 42 핵심 질문의 답 (정답) ───────────────────────────────
    p = d.slide("핵심 질문의 답", K.S_ANS,
                "22장 지도 2판의 축소판 — 질문(02장)으로 돌아와 한 문장으로 답한다")
    mini = [("13", "키 입력"), ("06", "fork"), ("04", "int $0x80"), ("09", "exec"),
            ("08", "폴트 적재"), ("12", "open·read"), ("11", "버퍼·hd"),
            ("13", "write"), ("10", "exit·wait"), ("05", "schedule")]
    for i, (no, lab) in enumerate(mini):
        x = 1100 + i * 3150
        hl = i in (2, 9)
        nbox(d, p, x, 4400, 2850, 1900, no, lab,
             K.ORANGE if hl else K.PAPER, s1=17, s2=10)
        if i < 9:
            d.text(p, x + 2870, 5050, 320, 600, "→", 13, K.TEAL, True)
    d.outline(p, 1100, 6700, 31500, 2700, K.ORANGE, 110)
    d.text(p, 1500, 6950, 30700, 2300,
           "\"`ls /`는 13→06→04→09→08→12→11→13→10→05 순으로 10개 회차를 지나며,\n"
           "그 사이 커널 진입은 시스템 콜 · IRQ0/1/14 · 예외 14 다섯 종류가 섞여 일어난다.\"",
           21, K.ORANGE, True)
    para(d, p, 1100, 9800, 31500, 4200,
         "ORANGE 두 박스 — 04(테두리: 모든 시스템 콜의 진입/복귀)와 05(중앙: 모든 잠듦 사이의 전환)는 특정 구간이 아니라\n"
         "지도 전체에 깔린 테두리·중심이어서 경로 어디에서나 등장한다.\n"
         "같은 한 줄에서 셸(부모)과 ls(자식) 두 태스크가 번갈아 RUNNING이었다(23장) — 그 사이 스케줄은 counter가 정했다(21장).\n"
         "다시 치는 두 번째 `ls /`는 디스크를 거의 안 갔다(30장) — 캐시가 남아 있기 때문이다.", 15)

    # ── 43 이해 확인 질문 (확인) ───────────────────────────────
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(44) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "`ls /` 한 번 동안 커널에 들어가는 방법은 몇 종류이고 각각 무엇인가?", K.TEAL, 15)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2",
         "exec가 끝난 직후 ls의 코드는 메모리에 있는가? 없다면 언제 들어오는가?", K.TEAL, 15)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3",
         "두 번째 `ls /`에서 디스크 접근이 줄어드는 이유와, 그래도 페이지 폴트는 줄지 않는 이유는?",
         K.TEAL, 15)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4",
         "0.11의 task[64]와 TSS ljmp 전환을 현대 커널은 무엇으로 바꿨는가(개념 이름만)?",
         K.TEAL, 15)

    # ── 44 이해 확인 정답 (확인) ───────────────────────────────
    p = d.slide("이해 확인 정답", K.S_QUIZ,
                "근거 줄 번호 포함 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "A1",
         "다섯 종류 — int $0x80 시스템 콜(sched.c:411), 타이머 IRQ0(409), 키보드 IRQ1(console.c:683), "
         "디스크 IRQ14(hd.c:346), 페이지 폴트 예외 14(traps.c:199).", K.ORANGE, 14)
    qbox(d, p, 1100, 6850, 31500, 2400, "A2",
         "없다. do_execve는 current->executable만 바꾸고(exec.c:319-321) 첫 명령어 실행 시 예외 14 → "
         "do_no_page(memory.c:365-397)가 bread_page로 가져온다.", K.ORANGE, 14)
    qbox(d, p, 1100, 9400, 31500, 2400, "A3",
         "디렉터리 블록·ls 바이너리 블록이 버퍼 캐시(getblk 해시 히트, buffer.c:206-251)에 남아 "
         "ll_rw_block을 안 부르지만, exec는 매번 새 주소 공간을 만들므로 do_no_page는 다시 일어난다.", K.ORANGE, 14)
    qbox(d, p, 1100, 11950, 31500, 2400, "A4",
         "pid 해시/idr 기반 동적 태스크 관리와 소프트웨어 문맥 전환(TSS는 커널 스택 포인터 등 최소 용도로만).",
         K.ORANGE, 14)

    # ── 45 정리 (정리) ─────────────────────────────────────────
    p = d.slide("정리 — 오늘 만든 것 세 가지", K.S_WRAP,
                "지도 2판 · 두 레인 상태도 · 비교 4열 규칙 — 다음 회차 실습의 준비물이 된다")
    d.cards(p, [
        ("큰 지도 2판 (06·22장)",
         "아홉 구간 ①–⑨ + 테두리(04)·\n중앙(05) — 시계 방향이 곧 시간\n2판 = 좌표·진입 종류 기입판\n인쇄용 1장"),
        ("두 레인 상태도 (23·24장)",
         "셸과 ls를 같은 시간축에\n— 잠듦·깨움·ZOMBIE·소멸\n전환마다 원인·데이터·\n유지 조건 표"),
        ("비교 ② 4열 (32–38장)",
         "0.11 메커니즘 / 현대 개념 /\n왜 바뀌었나 / 다룸 여부\n개념 수준 — 이름만 짝지움\n+ 다루지 않은 것(39장)"),
    ], y=4400, h=6600)
    d.outline(p, 1100, 11400, 31500, 1300, K.ORANGE, 90)
    d.text(p, 1400, 11650, 30900, 800,
           "수강생이 가져갈 것 — 지도 1장(인쇄): 22장 큰 지도 2판 완성판", 19, K.ORANGE, True)
    para(d, p, 1100, 13000, 31500, 1600,
         "다시 보기 — 경로 재방문(09–21장) · 상태도(23–25장) · 시연 절차(27·29장)는 각 회차 슬라이드가 원본이다.", 14)

    # ── 46 다음 회차 예고 (정리) ───────────────────────────────
    p = d.slide("다음 회차 예고 — 15. 커널 수정 실습", K.S_WRAP,
                "15회차 — 새 시스템 콜과 스케줄러 변경 · 파트 G «종합·실습» 마지막(15/15)")
    d.cards(p, [
        ("무엇을 바꾸나",
         "테두리 — sys_call_table에\n항목 하나 추가\n박스 ⑨ — schedule의 선택 규칙"),
        ("어떻게 확인하나",
         "오늘의 GDB 방법 그대로\n(27·29장 절차)\n중단점·카운트로 변경 전후 비교"),
        ("오늘에서 달라지는 것",
         "'읽기'에서 '바꾸기'로\n지도의 좌표가\n직접 수정 대상이 된다"),
    ], y=4400, h=6400)
    d.outline(p, 1100, 11200, 31500, 1600, K.ORANGE, 110)
    d.text(p, 1400, 11480, 30900, 1100,
           "15회차 — sys_call_table(테두리)과 schedule(⑨)을 직접 고치고,\n같은 GDB 방법으로 확인한다: \"읽기\"에서 \"바꾸기\"로",
           18, K.ORANGE, True)
    para(d, p, 1100, 13200, 31500, 1400,
         "가져갈 것 — 지도 2판(인쇄) · 두 레인 상태도 · 비교 ② 4열 규칙. 실습 환경은 lab/(Docker 빌드) 그대로다.", 14)


if __name__ == "__main__":
    K.run(globals())
