#!/usr/bin/env python3
"""15회차 덱 — 커널 수정 실습: 새 시스템 콜과 스케줄러 변경
(output/15-kernel-lab.pptx)

계획: materials/slide-plans/15-kernel-lab.md (§2 표 48행 1:1 · §3 앞부분 명세 —
로드맵 01–14 완료·15 종강 · 구조도 수정 대상 4파일 + 흐름 · §4 상태 변화도
'변경 하나의 생애' 명세 · §5 캡처 13종(미확보 — 예상 출력 패널) · §6 이해 확인 ·
§8 오해 금지).

레이아웃 메모(자기 검수 반영): placeholder 본문은 줄 12·폭 60자 이내 ·
banner 20pt 는 40단위(한글 기준) 이내 · cards 본문은 줄 수 × 930 + 2800 이하 ·
nbox 부제는 줄바꿈 없음(짧게) · 표 총폭 31500 이내 · 패널 하단 14400 이내.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="15", total=48, slug="15-kernel-lab",
    part_no="G", part="«종합·실습»",
    title="15. 커널 수정 실습: 새 시스템 콜과 스케줄러 변경",
    question="커널을 바꾸면 어디서 어떻게 확인하는가?",
    done=14,
    today_line="14회차까지 읽기만 했다 — 이제 직접 바꾼다: 수정 → 빌드 → 부팅 → 검증",
    next_lines=[
        "14 → 15   14: 셸 명령 한 줄의 전체 경로를 읽고 현대 커널과 비교만 했다",
        "           → 15: 이제 그 커널을 직접 바꾼다 — 새 시스템 콜과 schedule() 재계산 규칙을 고치고 빌드·부팅·검증까지 완결",
        "종강 — 15/15 완료 · 파트 A–G «종합·실습» 완결 · 다음 회차 없음",
    ],
    road_note=("실습 회차 — 질문·지도·배경·코드·상태도·비교·시연·캡처·정답·확인·정리 전 단계를 지난다.\n"
               "오늘의 두 파트: Part A 새 시스템 콜 hello(n) — 커널이 printk로 인사하고 pid+n을 돌려준다,\n"
               "Part B schedule() 재계산 규칙 변경 — nice 준 자식과 안 준 자식의 완주 시간 비교.\n"
               "두 실습 모두 9장 상태도의 다섯 상태(미적재→수정→빌드→부팅→검증)를 한 바퀴씩 돈다."),
    STRUCT=dict(
        teal=["entry", "proc"],
        today=[("include/unistd.h", "시스템 콜 번호 __NR_*"),
               ("include/linux/sys.h", "sys_call_table[]"),
               ("kernel/system_call.s", "진입 어셈블리"),
               ("kernel/sched.c", "스케줄러 schedule()")],
        flow="새 시스템 콜 번호 → sys_call_table 등록 → 커널 함수 → 재빌드 → QEMU 부팅 → 게스트에서 호출 확인",
        up="↑ hello(n) 반환 r = pid + n",
        user="./hello · sched2 — 오늘 직접 만들어 넣는 게스트 프로그램",
    ),
)

CHECKS = dict(
    captions={
        7: "src/kernel/Makefile:27-32",
        12: "src/include/unistd.h:127-131",
        13: "src/include/linux/sys.h:70-77",
        14: "src/kernel/system_call.s:72-82",
        15: "src/kernel/sys.c:16-30",
        16: "src/kernel/system_call.s:80-95",
        17: "src/include/asm/segment.h:1-10",
        18: "src/lib/close.c:7-10",
        26: "src/kernel/sched.c:124-141",
        27: "src/kernel/sched.c:330-335",
        28: "src/kernel/sched.c:378-383",
        30: "src/kernel/sched.c:136-139",
        31: "src/kernel/sys.c:156-162",
        37: "src/kernel/chr_drv/tty_io.c:298-301",
    },
    required=[
        "__NR_hello", "sys_call_table", "nr_system_calls", "sys_hello",
        "bad_sys_call", "sched_pick", "get_fs_byte", "put_fs_long",
        "sys_nice", "switch_to", "do_timer", "심벌 파일", "재진입",
        "hello: pid=", "p sys_call_table[72]", "SCHED_FLAT", "r=-1 errno=1",
    ],
    prereq=[
        ("sys_call_table", "src/include/linux/sys.h:70-77"),
        ("sys_hello", "src/kernel/sys.c:16-30"),
        ("schedule", "src/kernel/sched.c:124-141"),
        ("counter", "src/kernel/sched.c:136-139"),
        ("errno", "src/lib/close.c:7-10"),
    ],
    structure_nodes=["system_call.s", "sys.h", "unistd.h", "sched.c",
                     "sys.c", "sys_call_table"],
    capture_slides=[21, 22, 23, 24, 25, 33, 34, 35, 36, 37, 43],
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
               K.fit_size(l2, s2, w - 500, min_size=8), c2v)


def badge(d, p, x, y, w, text, fill=K.ORANGE, h=700, size=13):
    d.shape(p, x, y, w, h, fill)
    d.text(p, x + 150, y + (h - 520) // 2, w - 300, 520, text,
           K.fit_size(text, size, w - 300, min_size=9), K.INK, True)


def qbox(d, p, x, y, w, h, tag, body, tag_color, size=13):
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


# ── 상태 변화도 "변경 하나의 생애" (09 · 38 공통 시각 언어) ──────
LIFE_STATES = [
    ("미적재", "src만 읽음"),
    ("수정됨", "lab/ 파일 편집"),
    ("빌드됨", "build.sh — 새 Image·심벌"),
    ("부팅됨", "run.sh — 새 커널이 메모리에"),
    ("검증됨", "기대 출력 / GDB 값 일치"),
]
LIFE_CAUSES = ["편집", "make", "QEMU 기동", "관찰 비교"]


def draw_life(d, p, tracks=False):
    """상태 5 가로 타임라인 + 전환 원인 + 되돌림 + 유지 조건.
    tracks=True 면 38장 — A·B 두 바퀴 궤적과 깨뜨리기 되돌림을 덧그린다."""
    w, gap = 5600, 875
    for i, (name, sub) in enumerate(LIFE_STATES):
        x = 1100 + i * (w + gap)
        if i < 4:
            nbox(d, p, x, 4700, w, 1700, name, sub, K.TEAL, s1=17, s2=9)
        else:
            nbox(d, p, x, 4700, w, 1700, name, sub, None, K.TEAL,
                 edge=K.TEAL, s1=17, s2=9)
        if i < 4:
            d.text(p, x + w + 130, 5150, 650, 800, "→", 20, K.TEAL, True)
            if not tracks:
                d.text(p, x + w - 262, 6480, 1400, 980, LIFE_CAUSES[i],
                       9, K.MUTED, True)
    if tracks:
        para(d, p, 1100, 6480, 31500, 800,
             "Part A (21–25장) — 다섯 상태를 한 바퀴 · 깨뜨리기(24장): 검증됨→수정됨 되돌림",
             13, K.ORANGE, True)
        para(d, p, 1100, 7280, 31500, 800,
             "Part B (33–35장) — 두 번째 바퀴: 원본 측정 → sched.c 변경 → 재측정",
             13, K.ORANGE, True)
    else:
        para(d, p, 1100, 7580, 31500, 900,
             "변경 데이터 — lab/ 소스 → 오브젝트 · Image · tools/system 심벌 → "
             "메모리의 sys_call_table · schedule 코드 → 로그", 13, K.PAPER)
        para(d, p, 1100, 8480, 31500, 900,
             "↩  되돌림 전환(점선) — git checkout · 원본 복사 : 부팅됨·검증됨 → 수정됨 · "
             "빌드 실패 시 '수정됨'에 머무른다", 12, K.MUTED)
    d.text(p, 1100, 9480, 8000, 500, "유지 조건", 13, K.TEAL, True)
    conds = ["src/는 변하지 않는다",
             "빌드 실패 시 '수정됨'에 머무름",
             "심벌 파일과 Image가 같은 빌드일 때만 '검증됨'"]
    cw = 10100
    for i, c in enumerate(conds):
        nbox(d, p, 1100 + i * (cw + 100), 10050, cw, 1300, c,
             None, None, K.MUTED, s1=12)
    d.text(p, 28900, 11400, 3700, 500, "Linux 0.11", 9, K.MUTED)
    if tracks:
        d.banner(p, "두 실습이 다섯 상태를 두 바퀴 돌았다 — 궤적이 곧 오늘 진행 순서")
    else:
        d.banner(p, "오늘 두 실습 모두 이 다섯 상태를 두 바퀴 돈다 — 지금 어디인지 항상 말한다")


# ── 슬라이드 05–48 (§2 표 1:1) ────────────────────────────────
def populate(d):
    # ── 04 구조도 뒤처리 — kernel/sys.c 라벨 + 보조 흐름 ────────
    page4 = d.pages.getByIndex(3)
    for i in range(page4.getCount()):
        sh = page4.getByIndex(i)
        try:
            txt = sh.getString()
        except Exception:
            continue
        if txt.startswith("Linux 0.11 · 오늘"):
            sh.setString("보조 흐름 — 타이머 틱 → do_timer → schedule() 재계산 규칙"
                         "(sched.c:136-139) 변경 → GDB p sched_pick 관찰 · "
                         "누적 강조 01–14 전 계층(마지막 회차)")
    d.outline(page4, 1400, 12300, 14900, 1200, K.TEAL, 70)
    d.text(page4, 1650, 12480, 14500, 480,
           "kernel/sys.c — sys_hello 의 자리 (오늘 함수를 추가하는 파일)", 13,
           K.TEAL, True)
    d.text(page4, 1650, 12980, 14500, 420,
           "Makefile OBJS에 sys.o 포함 — 빌드 규칙 수정 불필요 (07장)", 11, K.TEAL)

    # ── 03 로드맵 뒤처리 — 종강 마커 ────────────────────────────
    page3 = d.pages.getByIndex(2)
    badge(d, page3, 23500, 9150, 5100, "종강 — 15/15 완료", K.ORANGE, 900, 15)

    # ── 05 왜 이 회차인가 (배경) ────────────────────────────────
    p = d.slide("왜 이 회차인가 — 회차 대체 노트", K.S_BG,
                "course-plan 원문 계승 — 슬라이드 한 장으로 게시하고 이 노트로 끝낸다 (§1)")
    qbox(d, p, 1100, 4300, 31500, 4700, "회차 대체 노트 (원문)",
         "원래 계획에 있던 \"현대 커널 모듈\"과 \"sched_ext\" 두 회차는 선택되지 않은 현대 커널 VM이 "
         "필요하여 제외했고, 그 자리를 이 회차(0.11을 직접 고치고 QEMU+GDB로 확인하는 실습)로 대체한다.\n"
         "현대 커널과의 대응은 14회차 비교 슬라이드가 개념 수준에서만 담당한다.\n"
         "현대 커널 시스템 콜 추가 절차·sched_ext는 이 노트로 끝낸다.", K.TEAL, 15)
    for i, (t, sub) in enumerate([
            ("빠진 두 회차", "현대 커널 모듈 · sched_ext\n현대 커널 VM 미선택으로 제외\n이 노트로 언급을 종료"),
            ("대신 오늘", "0.11을 직접 고치고\nQEMU+GDB로 확인하는 실습\n수정 → 빌드 → 부팅 → 검증"),
            ("그래도 같은 질문", "\"바꾸면 어디서 확인하나\"에\n답한다는 점은 그대로다\n— 읽기에서 바꾸기로")]):
        nbox(d, p, 1100 + i * 10600, 9400, 10300, 3100, t, sub,
             K.PAPER, s1=16, s2=11)
    d.banner(p, "14회차까지 읽기만 했다 — 오늘은 직접 바꾸고 어디서 확인하는지 밟는다")

    # ── 06 lab/ 와 src/ 를 다시 구분한다 (배경) ─────────────────
    p = d.slide("lab/ 와 src/ 를 다시 구분한다", K.S_BG,
                "1회차 20장 재사용 · 오늘 편집은 lab/에서만 · 슬라이드 줄 번호는 src/ 기준 — lab의 줄 번호는 다를 수 있다")
    nbox(d, p, 1100, 4300, 15200, 2800, "src/ — Kernel.org 원본",
         "읽기·인용 전용 — 절대 편집하지 않는다\n줄 번호의 기준 (00-common §1)\n참조 좌표는 모두 여기", K.PAPER, s1=16, s2=10)
    nbox(d, p, 17200, 4300, 15400, 2800, "lab/ — 실행·수정본",
         "yuan-xy/Linux-0.11 기반 실행본\n현대 gcc/gas로 빌드 · QEMU i386\n오늘 편집은 lab/에서만", K.PAPER, s1=16, s2=10)
    d.table(p, 1100, 7300, [8100, 6700, 8200, 8500], [
        ["같은 경로의 파일", "src/ 에서는", "lab/ 에서는", "오늘 역할"],
        ["include/unistd.h", "번호 원문 인용", "__NR_hello 72 추가", "A-1 번호"],
        ["include/linux/sys.h", "extern·표 원문", "sys_hello 등록", "A-2 표"],
        ["kernel/system_call.s", "nr_system_calls = 72", "73으로 수정", "A-3 상한"],
        ["kernel/sys.c", "stub 본보기", "sys_hello 함수 추가", "A-4 함수"],
        ["kernel/sched.c", "재계산 원문", "priority → 15", "B-3 스케줄러"],
    ], row_h=1150, size=13)
    d.banner(p, "GDB b 파일:줄 은 lab 기준 실제 줄로 — 캡션은 src 기준 (§8)")

    # ── 07 build.sh — 빌드와 두 산출물 (배경) ────────────────────
    p = d.slide("build.sh — 빌드와 두 산출물", K.S_BG,
                "lab/에서 make → Image · 심벌 파일 tools/system — 실제 스크립트 옵션은 캡처로 확인 (§11)")
    chain(d, p, 4250, [
        ("lab/ 소스", "수정된 네 파일"),
        ("make", "kernel/Makefile 등"),
        ("Image", "부팅 이미지"),
        ("tools/system", "GDB 심벌 파일"),
    ], h=1500)
    d.code_panel(p, "src/kernel/Makefile", 27, 32,
                 1100, 6100, 15200, 4200, size=11,
                 caption_extra="OBJS — sys.o·sched.o 포함")
    para(d, p, 17200, 6100, 15400, 4600,
         "OBJS(sys.o·sched.o 포함) — 새 함수를 sys.c에 두면 Makefile 수정 불필요.\n\n"
         "심벌 파일(tools/system) — GDB가 함수 이름을 주소로 바꾸는 근거.\n"
         "옛 심벌이면 중단점 불일치 — 41장 실패 표.", 14)
    d.banner(p, "산출물 사슬: lab/ 소스 → 오브젝트 → Image·심벌 — 둘은 같은 빌드여야 한다")

    # ── 08 run.sh 와 GDB 연결 (배경) ────────────────────────────
    p = d.slide("run.sh 와 GDB 연결", K.S_BG,
                "실행 절차 — 부팅 전 Image·심벌 일치 확인이 오늘 실패 예방의 절반이다 (39장 체크리스트)")
    auto_pane(d, p, 1100, 4300, 19700, 7300,
              "콘솔 — QEMU 기동과 GDB 연결",
              "$ scripts/run.sh        # QEMU -S -s 기동\n"
              "$ gdb lab/tools/system\n"
              "(gdb) target remote :1234\n"
              "(gdb) b sys_hello\n"
              "(gdb) info files      # 심벌 확인\n"
              "(gdb) c", start=13)
    para(d, p, 22000, 4300, 10000, 7300,
         "부팅 전 확인 3단계\n\n"
         "1. run.sh 의 Image가 방금 빌드한 것인가 — 타임스탬프\n"
         "2. GDB file 이 방금 tools/system 인가\n"
         "3. 중단점 pending = 심벌 불일치 — info files 로 확인\n\n"
         "캡처 각주 — 이 회차 캡처는 모두 \"수정 있음(내용 명시)\" (00-common §7)", 13)
    d.banner(p, "Image 도 심벌 도 '방금 것'인지 부팅 전에 확인 — 옛 파일이 흔한 실패의 원인")

    # ── 09 상태 변화도: 변경 하나의 생애 (상태도) ────────────────
    p = d.slide("상태 변화도 — 변경 하나의 생애", K.S_STATE,
                "오늘의 핵심 시각 자료(§4) — 전환 원인(편집/make/QEMU/관찰)·변경 데이터·유지 조건·되돌림 포함")
    draw_life(d, p, tracks=False)

    # ── 10 비교 ②: 무엇으로 확인할 것인가 (비교) ────────────────
    p = d.slide("비교 ②: 무엇으로 확인할 것인가", K.S_CMP,
                "검증 수단 6가지 — printk 가 schedule() 안에서 재진입 위험인 근거: printk.c:21-41 → tty_io.c:299 · 323")
    d.table(p, 1100, 4400, [5300, 9800, 9400, 7000], [
        ["검증 수단", "무엇을 보여 주나", "어디서는 쓰면 안 되나", "재현성"],
        ["사용자 프로그램 출력", "결과 값·출력 순서 — 최종 사실", "제한 없음", "pid 등 부팅마다 변동"],
        ["반환값 · errno", "실패 원인 1차 좁히기", "errno=1 남발 — 14장 함정", "안정적"],
        ["printk", "커널 내부 경로·시점", "schedule() 안 — 재진입 위험", "출력 순서 섞일 수 있음"],
        ["GDB 중단점", "경로 통과 여부·시점", "멈춤 — 실시간 관찰 아님", "정확"],
        ["GDB 변수 관찰", "p sys_call_table[72] · p sched_pick", "관찰 중 정지", "정확"],
        ["QEMU 화면 캡처", "사용자가 본 그림 — 기록", "증거 보관용 — 분석 아님", "1회성"],
    ], row_h=1300, size=12)
    para(d, p, 1100, 13700, 31500, 800,
         "핵심 행 — printk → tty_write(printk.c:21-41) → write_q 차면 sleep_if_full(tty_io.c:299) → "
         "schedule()(323) 재진입 위험.", 13)
    d.banner(p, "스케줄러 관찰은 GDB 변수가 1순위 — printk는 재진입 위험을 알고 쓰는 2순위")

    # ── 11 오늘의 두 실습 미리 보기 (배경) ──────────────────────
    p = d.slide("오늘의 두 실습 미리 보기", K.S_BG,
                "두 실습 모두 9장 상태도의 다섯 상태를 한 바퀴씩 돈다 — 편집 위치 / 빌드 / 확인 카드")
    nbox(d, p, 1100, 4300, 15200, 5200, "Part A — 새 시스템 콜 hello(n)",
         "커널이 printk로 인사하고 pid+n을 돌려준다\n\n"
         "편집 — unistd.h 번호 · sys.h 표 · system_call.s 상한 · sys.c 함수(sys_hello)\n"
         "빌드 — scripts/build.sh\n"
         "확인 — ./hello 출력 · GDB p sys_call_table[72]", K.PAPER, s1=17, s2=12)
    nbox(d, p, 17200, 4300, 15400, 5200, "Part B — schedule() 재계산 규칙 변경",
         "nice 준 자식과 안 준 자식의 완주 시간을 바꾼다\n\n"
         "편집 — kernel/sched.c:136-139 ((*p)->priority → 15)\n"
         "빌드 — scripts/build.sh\n"
         "확인 — ./sched2 두 자식 end jiffies · GDB p sched_pick", K.PAPER, s1=17, s2=12)
    d.banner(p, "같은 절차를 두 바퀴: 수정 → 빌드 → 부팅 → 검증 — 다른 것은 '무엇을 바꾸나'뿐")

    # ── 12 A-1. 번호: __NR_hello 72 (코드) ──────────────────────
    p = d.slide("A-1. 번호 — __NR_hello 72", K.S_CODE,
                "include/unistd.h:58, 60–131, 185 — #ifdef __LIBRARY__ 안, 마지막 번호 71 다음에 붙인다")
    d.code_panel(p, "src/include/unistd.h", 127, 131,
                 1100, 4300, 15200, 4200, size=11,
                 caption_extra="before — 마지막 번호 확인")
    auto_pane(d, p, 17200, 4300, 15400, 4200,
              "after — lab/include/unistd.h (추가 줄)",
              "#define __NR_hello\t72\n"
              "\n"
              "/* __NR_setregid 71 의 다음 줄 —\n"
              "   #ifdef __LIBRARY__ (58) …\n"
              "   #endif (185) 안에 둔다 */", start=12)
    nbox(d, p, 1100, 9000, 9900, 3400, "__LIBRARY__ 안이어야 한다",
         "_syscallN 매크로가 같은 조건부\n블록(58–185)에 있다 — 밖에\n두면 매크로가 안 보인다", K.PAPER, s1=14, s2=11)
    nbox(d, p, 11200, 9000, 9900, 3400, "번호 = 표 인덱스",
         "sys_call_table[] 끝에 붙일\n슬롯(72번, 0부터)과 일치 —\n순서가 곧 번호 (13장)", K.PAPER, s1=14, s2=11)
    nbox(d, p, 21300, 9000, 11300, 3400, "확인: 마지막 번호는 71",
         "__NR_setreuid 70 · __NR_setregid 71\n(unistd.h:130-131)\n→ 다음 빈 번호는 72", K.PAPER, s1=14, s2=11)
    d.banner(p, "첫 조각은 단 한 줄 — 이 번호가 표·상한과 어긋나면 모든 게 어긋난다")

    # ── 13 A-2. 표: sys_call_table[] 끝에 sys_hello (코드) ───────
    p = d.slide("A-2. 표 — sys_call_table[] 끝에 sys_hello", K.S_CODE,
                "include/linux/sys.h:1-72 extern 목록 · 74-86 표 — 순서가 곧 번호, 72번(0부터) 슬롯이 열린다")
    d.code_panel(p, "src/include/linux/sys.h", 70, 77,
                 1100, 4300, 15200, 4900, size=9,
                 caption_extra="before — extern 목록 말미와 표 머리")
    auto_pane(d, p, 17200, 4300, 15400, 4900,
              "after — lab/include/linux/sys.h (추가)",
              "extern int sys_hello();\n"
              "\n"
              "/* 72행 sys_setregid 선언 뒤 ·\n"
              "   86행 표 끝 */\n"
              "sys_setreuid,sys_setregid, sys_hello };", start=11)
    slots = [("0 sys_setup", "표 머리"), ("…", "번호 = 순서"),
             ("71 sys_setregid", "마지막 슬롯"), ("72 sys_hello", "오늘 추가 — 채워진다")]
    for i, (t, sub) in enumerate(slots):
        x = 1100 + i * 7960
        nbox(d, p, x, 9600, 7600, 1650, t, sub,
             K.ORANGE if i == 3 else None,
             K.INK if i == 3 else K.MUTED, s1=14, s2=10)
        if i < 3:
            d.text(p, x + 7640, 10050, 400, 600, "→", 14, K.TEAL, True)
    para(d, p, 1100, 11400, 31500, 900,
         "선언(extern)을 빠뜨리면 암시적 선언 경고/오류 — 현대 gcc(lab) 기준, 확인 필요 사항(§11).", 13)
    d.banner(p, "extern 선언 1줄 + 표 끝 1단어 — sys_call_table[72] 자리가 생긴다")

    # ── 14 A-3. 상한: nr_system_calls = 73 (코드) ────────────────
    p = d.slide("A-3. 상한 — nr_system_calls = 73", K.S_CODE,
                "kernel/system_call.s:61 → 73 수정 · 81-82 범위 검사 · 72-74 bad_sys_call — 24장에서 깨뜨려 본다")
    d.code_panel(p, "src/kernel/system_call.s", 72, 82,
                 1100, 4300, 15200, 6800, size=10,
                 caption_extra="bad_sys_call 과 진입 검사")
    vsteps = [("eax = 72 (hello)", "int $0x80 진입 — 번호"),
              ("cmpl $nr_system_calls-1,%eax", "81행 — 상한과 비교"),
              ("ja bad_sys_call", "82행 — 72 > 71 이면 점프"),
              ("movl $-1,%eax; iret", "72-74행 — 오류 코드 없이 -1"),
              ("_syscall1 → errno = 1", "EPERM — \"권한 없음\"처럼 보임")]
    for i, (t, sub) in enumerate(vsteps):
        y = 4300 + i * 2050
        nbox(d, p, 17200, y, 15400, 1900, t, sub,
             K.ORANGE if i >= 3 else K.PAPER, s1=14, s2=10)
        if i < 4:
            d.text(p, 27200, y + 1930, 500, 500, "↓", 14, K.ORANGE, True)
    badge(d, p, 1100, 11400, 15200,
          "수정: 61행 nr_system_calls = 72 → 73 — 안 올리면 eax=72가 bad_sys_call 로 간다", K.ORANGE, 800)
    para(d, p, 1100, 12400, 15200, 1600,
         "함정 — _syscall1(unistd.h:146-157)은 음수 반환을 errno로 바꾸므로 '권한 없음'처럼 보인다.\n"
         "24장 시연에서 실제로 재현해 본다.", 14)
    d.banner(p, "번호·표·상한 세 곳이 일치해야 한다 — 상한은 따로 적혀 있어 손으로 맞춘다")

    # ── 15 A-4. 함수: sys_hello in kernel/sys.c (코드) ───────────
    p = d.slide("A-4. 함수 — sys_hello in kernel/sys.c", K.S_CODE,
                "kernel/sys.c:16-48 stub 옆 · 본보기 sched.c:348-356 · Makefile OBJS에 sys.o — 빌드 규칙 수정 불필요")
    d.code_panel(p, "src/kernel/sys.c", 16, 30,
                 1100, 4300, 15200, 9600, size=9,
                 caption_extra="-ENOSYS stub 들 — 새 함수의 자리")
    auto_pane(d, p, 17200, 4300, 15400, 4400,
              "추가 — lab/kernel/sys.c",
              "int sys_hello(long n)\n"
              "{\n"
              "    printk(\"hello: pid=%d n=%ld\\n\\r\",\n"
              "           current->pid, n);\n"
              "    return current->pid + n;\n"
              "}", start=11)
    d.code_panel(p, "src/kernel/sched.c", 348, 356,
                 17200, 8900, 15400, 5500, size=8,
                 caption_extra="가장 작은 시스템 콜의 본보기")
    d.banner(p, "커널 함수 = printk 한 줄 + 계산 한 줄 — 나머지는 등록(번호·표·상한)이 전부")

    # ── 16 A-4b. 인자가 커널 함수에 도착하는 길 (코드) ───────────
    p = d.slide("A-4b. 인자가 커널 함수에 도착하는 길", K.S_CODE,
                "kernel/system_call.s:80-100 · 86-88 역순 push — ebx가 스택 top = C 함수의 첫 인자")
    d.code_panel(p, "src/kernel/system_call.s", 80, 95,
                 1100, 4300, 15200, 9500, size=9,
                 caption_extra="진입 — 인자 push 와 세그먼트")
    nbox(d, p, 17200, 4300, 15400, 1650, "eax = 72 (__NR_hello)",
         "시스템 콜 번호 — int $0x80 직전에", K.PAPER, s1=14, s2=10)
    nbox(d, p, 17200, 6150, 15400, 1650, "ebx = 100 (인자 n)",
         "_syscall1 의 \"b\" 제약이 ebx로 실는다", K.PAPER, s1=14, s2=10)
    nbox(d, p, 17200, 8000, 15400, 650, "pushl %edx  (86)", None, K.MUTED, s1=12)
    nbox(d, p, 17200, 8730, 15400, 650, "pushl %ecx  (87)", None, K.MUTED, s1=12)
    nbox(d, p, 17200, 9460, 15400, 750, "pushl %ebx  (88) ← 스택 top",
         None, K.TEAL, s1=13)
    d.text(p, 24500, 10280, 600, 600, "↓", 16, K.ORANGE, True)
    nbox(d, p, 17200, 10900, 15400, 1650, "C 함수 첫 인자 = ebx → n = 100",
         "call _sys_call_table(,%eax,4) (94)", K.ORANGE, s1=14, s2=10)
    para(d, p, 17200, 12700, 15400, 1500,
         "역순 push(edx→ecx→ebx)라 ebx가 스택 top.\n"
         "92-93행 fs=0x17 — 17장의 get_fs_* 근거.", 13)
    d.banner(p, "인자는 ebx/ecx/edx → 스택 → C 함수 첫 인자 — 어셈블리와 C가 스택에서 만난다")

    # ── 17 A-4′. 사용자 포인터를 받는다면 (코드) ─────────────────
    p = d.slide("A-4′. 사용자 포인터를 받는다면", K.S_CODE,
                "확장안 sys_hello2(char *buf) — ds=0x10 커널 / fs=0x17 사용자 · 오늘 기본 실습은 정수 인자만으로 피한다")
    d.code_panel(p, "src/include/asm/segment.h", 1, 10,
                 1100, 4300, 15200, 6600, size=9,
                 caption_extra="get_fs_* — 사용자 주소의 유일한 경로")
    d.code_panel(p, "src/kernel/sys.c", 156, 166,
                 17200, 4300, 15400, 7000, size=9,
                 caption_extra="sys_times — put_fs_long 본보기")
    nbox(d, p, 1100, 11600, 15200, 2900, "*buf 직접 읽기 — 금지",
         "ds=0x10(커널)이라 buf 번지는\n엉뚱한 메모리 — 쓰레기값·폴트", None, K.ORANGE, s1=14, s2=11)
    nbox(d, p, 17200, 11600, 15400, 2900, "get_fs_byte / put_fs_byte",
         "fs=0x17(system_call.s:89-93)로\n사용자 데이터 접근 + verify_area", K.TEAL, s1=14, s2=11)
    d.banner(p, "포인터 인자는 get_fs_* 규칙과 함께만 — hello(n)은 정수라 이 문제를 피한다")

    # ── 18 A-5. 사용자 프로그램 hello.c (코드) ───────────────────
    p = d.slide("A-5. 사용자 프로그램 hello.c", K.S_CODE,
                "lib/close.c:7-10 형태 그대로 — _syscall1(int,hello,long,n) · 기대: printk 한 줄 + r = pid + 100")
    auto_pane(d, p, 1100, 4300, 15200, 9900,
              "hello.c — 게스트에서 컴파일할 프로그램",
              "#define __LIBRARY__\n"
              "#include <unistd.h>\n"
              "\n"
              "#define __NR_hello 72\n"
              "/* 게스트 헤더가 옛것이면 직접 정의 */\n"
              "\n"
              "_syscall1(int, hello, long, n)\n"
              "\n"
              "int main(void)\n"
              "{\n"
              "    long r = hello(100);\n"
              "    printf(\"r=%d errno=%d\\n\", r, errno);\n"
              "    return 0;\n"
              "}", start=10)
    d.code_panel(p, "src/lib/close.c", 7, 10,
                 17200, 4300, 15400, 3600, size=10,
                 caption_extra="사용자 래퍼의 표준 형태")
    d.code_panel(p, "src/init/main.c", 23, 24,
                 17200, 8100, 15400, 2500, size=10,
                 caption_extra="커널 안에서도 같은 매크로")
    para(d, p, 17200, 10900, 15400, 3400,
         "_syscall1 전개(unistd.h:146-157) — \"b\"((long)(a)) 가 인자를 ebx로,\n"
         "음수면 errno = -__res; return -1.\n\n"
         "main.c:23-24 — 커널 안에서도 같은 매크로(fork 래퍼).", 13)
    d.banner(p, "게스트 프로그램 5줄이면 충분하다 — 나머지는 커널 쪽 등록이 한다")

    # ── 19 게스트 안에서 컴파일하기 (배경) ───────────────────────
    p = d.slide("게스트 안에서 컴파일하기", K.S_BG,
                "lab 환경 의존 사항은 '확인 필요'로 사전 점검 — 안 되면 사전 캡처로 대체한다고 말한다 (§8)")
    chain(d, p, 4250, [
        ("hello.c · sched2.c", "게스트 홈 디렉터리"),
        ("gcc 1.40 (lab 루트 FS)", "hdc 이미지 — 포함 여부 확인"),
        ("a.out", "0.11 형식 바이너리"),
        ("./hello · ./sched2", "게스트에서 실행"),
    ], h=1500)
    for i, (t, sub) in enumerate([
            ("경로 ① 게스트 안 컴파일", "lab 루트 FS(hdc)의 gcc 1.40으로\ngcc -o hello hello.c\n(§11 확인: gcc 포함 여부)"),
            ("경로 ② 이미지에 넣기", "호스트에서 minix fs 마운트 후\n소스 파일만 넣기\n(마운트 가능 여부 확인 필요)"),
            ("범위 밖 · 대체", "호스트 현대 gcc로 0.11 a.out은\n오늘 범위 밖\n불가하면 사전 빌드 바이너리 사용")]):
        nbox(d, p, 1100 + i * 10600, 6100, 10300, 3300, t, sub,
             K.PAPER, s1=14, s2=11)
    para(d, p, 1100, 9700, 31500, 2400,
         "sched2(31장)도 같은 경로를 쓴다. 컴파일이 막히면 사전 빌드 바이너리를 루트 FS에 넣어 둔 이미지로\n"
         "같은 관찰을 하거나 사전 캡처로 대체하고 수강생에게 그렇게 말한다(§8 마지막 항목).", 14)
    d.banner(p, "확인 필요 사항은 사전 점검 — 현장에서 처음 알게 되는 일을 만들지 않는다")

    # ── 20 비교 ①: 변경 위치별 빌드 범위와 증상 (비교) ───────────
    p = d.slide("비교 ①: 변경 위치별 빌드 범위와 증상", K.S_CMP,
                "여섯 곳 — 어느 파일 / 빌드 범위 / 틀렸을 때 증상 · 검증 수단 열은 42장 완성판에서 채운다")
    d.table(p, 1100, 4400, [5200, 8400, 9200, 8700], [
        ["변경 위치", "어느 파일", "빌드 범위", "틀렸을 때 증상"],
        ["사용자 프로그램", "hello.c", "게스트 gcc 재컴파일만", "컴파일 오류 또는 errno"],
        ["__NR_* 번호", "include/unistd.h", "헤더 → lib/init 재컴파일", "__NR_hello undeclared"],
        ["sys_call_table[]", "include/linux/sys.h", "sys.h → sched.o 등 재컴파일", "잘못된 함수 호출"],
        ["nr_system_calls", "kernel/system_call.s", "system_call.o", "EPERM처럼 보임"],
        ["새 커널 함수", "kernel/sys.c", "sys.o", "링크 오류 undefined sys_hello"],
        ["schedule()", "kernel/sched.c", "sched.o", "동작 변화만 — 오류 없음"],
    ], row_h=1350, size=13)
    para(d, p, 1100, 13950, 31500, 700,
         "핵심 — 컴파일·링크가 잡아 주는 오류와 잡지 못하는 오류(nr_system_calls·schedule)가 갈린다.", 13)
    d.banner(p, "어디를 고치느냐에 따라 다시 빌드되는 범위와 터지는 증상이 달라진다")

    # ── 21 시연 A-1: 편집과 빌드 (시연) ──────────────────────────
    p = d.slide("시연 A-1: 편집과 빌드", K.S_DEMO,
                "캡처 01·02 — lab/ 빌드 · QEMU i386 · GDB · 수정 있음(sys_hello 추가) · 캡처 날짜는 확보 시 기재")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "lab/ $ git diff\n"
                         " include/unistd.h\n"
                         "+#define __NR_hello  72\n"
                         " include/linux/sys.h\n"
                         "+extern int sys_hello();\n"
                         "+ sys_setreuid,sys_setregid, sys_hello };\n"
                         " kernel/system_call.s\n"
                         "-nr_system_calls = 72\n"
                         "+nr_system_calls = 73\n"
                         " kernel/sys.c  +int sys_hello(long n) { ... }",
                         "01-hello-four-file-diff.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "절차\n\n"
         "1. lab/에서 네 파일 수정\n"
         "   (diff 화면 — 왼쪽)\n"
         "2. scripts/build.sh\n"
         "   기대: 경고 없이 Image 생성\n"
         "3. nm tools/system | grep sys_hello\n"
         "   심벌 존재 — 밑줄 접두는 lab\n"
         "   툴체인 기준(§11)\n\n"
         "관찰 대상\n"
         "· 네 곳 일치: 번호 = 표 인덱스\n"
         "  = nr_system_calls-1\n\n"
         "실패 시 대체 — lab-hello/\n"
         "사전 준비 브랜치·디렉터리", 12)
    d.banner(p, "첫 빌드는 경고 없이 끝나야 — implicit declaration 이 보이면 선언부터 다시")

    # ── 22 시연 A-2: 부팅과 실행 (시연) ──────────────────────────
    p = d.slide("시연 A-2: 부팅과 실행", K.S_DEMO,
                "캡처 03 — lab 수정본(sys_hello 추가), 2026-xx 빌드 · 각주에 빌드 시점을 명시한다")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "~ # ./hello\n"
                         "hello: pid=14 n=100\n"
                         "r=114 errno=0\n"
                         "~ #\n"
                         "\n"
                         "/* 관찰: 화면 두 줄\n"
                         "   추론: sys_call_table[72]가\n"
                         "   sys_hello — 23장 GDB로 확인 */",
                         "03-guest-hello-run.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "절차\n\n"
         "1. scripts/run.sh — 새 Image 부팅\n"
         "2. 게스트에서 ./hello\n\n"
         "기대 출력\n"
         "· hello: pid=N n=100 — 커널 printk\n"
         "· r=N+100 errno=0 — 사용자 printf\n\n"
         "관찰 vs 추론 (00-common §7)\n"
         "· 관찰 — 화면의 두 줄\n"
         "· 추론 — 표[72]가 sys_hello\n"
         "  (23장 GDB로 확인)", 12)
    d.banner(p, "커널 한 줄·사용자 한 줄이 같은 화면에 — 경계 양쪽이 동시에 보인다")

    # ── 23 시연 A-3: GDB로 표와 진입 확인 (시연) ─────────────────
    p = d.slide("시연 A-3: GDB로 표와 진입 확인", K.S_DEMO,
                "캡처 04 — b sys_hello 진입에서 p n · p current->pid · bt · p sys_call_table[72]")
    auto_pane(d, p, 1100, 4150, 15200, 10300,
              "GDB — 진입·인자·표 확인",
              "(gdb) b sys_hello\n"
              "(gdb) c              # 게스트에서 ./hello\n"
              "Breakpoint 1, 0x... in sys_hello\n"
              "(gdb) p n\n"
              "$1 = 100\n"
              "(gdb) p current->pid\n"
              "$2 = 14\n"
              "(gdb) bt\n"
              "#0  sys_hello (n=100)\n"
              "#1  system_call — int $0x80 진입 프레임\n"
              "(gdb) p sys_call_table[72]\n"
              "$3 = {int (...) ()} 0x... <sys_hello>", start=11)
    d.placeholder_output(p, 17200, 4150, 15400, 6400,
                         "(gdb) p sys_call_table[72]\n"
                         "$3 = {int (...) ()} 0x... <sys_hello>\n"
                         "\n"
                         "/* 관찰: 표[72] = sys_hello 주소\n"
                         "   관찰: n = 100, bt에\n"
                         "   system_call 프레임 */",
                         "04-gdb-sys-call-table-72.png")
    para(d, p, 17200, 10800, 15400, 3600,
         "주의 — 진입 시 p/x $eax 는 이미 호출 후이므로 진입 값이 아니다.\n"
         "b sys_hello 진입에서 보는 것이 정확하다.\n\n"
         "기대: n = 100 · pid = 게스트 값.", 13)
    d.banner(p, "표[72] 주소 = sys_hello — 등록이 실제 메모리에 적용됐음을 GDB가 증명한다")

    # ── 24 시연 A-4: 일부러 깨뜨리기 (시연) ──────────────────────
    p = d.slide("시연 A-4: 일부러 깨뜨리기", K.S_DEMO,
                "캡처 05 — nr_system_calls 를 72로 되돌려 재현하는 14장 함정 · 시간 없으면 사전 캡처로 대체")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "# nr_system_calls = 72 로 되돌리고 재빌드·재부팅\n"
                         "~ # ./hello\n"
                         "r=-1 errno=1\n"
                         "\n"
                         "(gdb) b bad_sys_call\n"
                         "Breakpoint 2, bad_sys_call ()\n"
                         "\n"
                         "/* 관찰: r=-1 errno=1\n"
                         "   관찰: bad_sys_call 적중\n"
                         "   → 원인: 상한 미갱신 */",
                         "05-eperm-bad-sys-call.png")
    steps = [("① 되돌림", "nr_system_calls = 72 (61행)"),
             ("② 재빌드·재부팅", "build.sh · run.sh"),
             ("③ ./hello", "r=-1 errno=1 — EPERM"),
             ("④ GDB", "b bad_sys_call 적중"),
             ("⑤ 복구", "다시 73으로 — 정상 복귀")]
    for i, (t, sub) in enumerate(steps):
        y = 4300 + i * 2050
        nbox(d, p, 17200, y, 15400, 1800, t, sub, K.PAPER, s1=14, s2=10)
        if i < 4:
            d.text(p, 24600, y + 1800, 500, 500, "↓", 14, K.ORANGE, True)
    d.banner(p, "증상(errno=1) → 원인(상한) 역추적 연습 — 흔한 실패 1위를 직접 만들어 본다")

    # ── 25 시연 A 캡처 모음 (캡처) ───────────────────────────────
    p = d.slide("시연 A 캡처 모음", K.S_DEMO,
                "캡처 01–05 중 4장 재게시 · 모두 lab 수정본 · 캡처마다 관찰 vs 추론 구분 한 줄 (00-common §7)")
    d.placeholder_output(p, 1100, 4100, 15400, 5000,
                         "$ scripts/build.sh\n"
                         "$ nm tools/system | grep sys_hello\n"
                         "0000.... T sys_hello",
                         "02-build-log-nm-sys-hello.png")
    d.placeholder_output(p, 17200, 4100, 15400, 5000,
                         "~ # ./hello\n"
                         "hello: pid=14 n=100\n"
                         "r=114 errno=0",
                         "03-guest-hello-run.png")
    d.placeholder_output(p, 1100, 9300, 15400, 5000,
                         "(gdb) p sys_call_table[72]\n"
                         "$3 = ... <sys_hello>\n"
                         "/* 관찰: 등록 확인 */",
                         "04-gdb-sys-call-table-72.png")
    d.placeholder_output(p, 17200, 9300, 15400, 5000,
                         "~ # ./hello\n"
                         "r=-1 errno=1\n"
                         "/* 관찰: 깨뜨린 경우 */",
                         "05-eperm-bad-sys-call.png")
    d.banner(p, "빌드 로그·게스트 출력·GDB 확인·깨뜨린 경우 — 등록 절차의 증거 묶음")

    # ── 26 B-1. 원본 schedule() (코드) ───────────────────────────
    p = d.slide("B-1. 원본 schedule() — 선택 루프와 재계산", K.S_CODE,
                "kernel/sched.c:104-142 재구조화 — 깨우기(110-120) · 선택(124-135) · 재계산(136-139) · switch_to(141)")
    d.code_panel(p, "src/kernel/sched.c", 124, 141,
                 1100, 4300, 15200, 9500, size=8,
                 caption_extra="선택 루프 · 재계산 · switch_to")
    parts = [("시그널 깨우기", "110-120 — alarm·신호 있는\nINTERRUPTIBLE → RUNNING"),
             ("선택 루프", "124-135 — state==TASK_RUNNING\n&& counter > c : RUNNING 중 최대"),
             ("재계산", "136-139 — counter =\n(counter>>1) + priority : 전 태스크"),
             ("switch_to(next)", "141 — TSS 전환으로 다음 태스크")]
    for i, (t, sub) in enumerate(parts):
        y = 4300 + i * 2450
        nbox(d, p, 17200, y, 15400, 2200, t, sub, K.PAPER, s1=15, s2=10)
        if i < 3:
            d.text(p, 24600, y + 2200, 500, 500, "↓", 14, K.ORANGE, True)
    d.banner(p, "재계산은 잠든 태스크도 포함 — 깨어나면 counter가 쌓여 유리하다")

    # ── 27 B-1b. counter의 생애 (코드) ───────────────────────────
    p = d.slide("B-1b. counter의 생애 — do_timer·fork·INIT_TASK", K.S_CODE,
                "감소(do_timer:332) · 초기화(fork.c:85) · 재계산(sched.c:136-139) · INIT_TASK 15/15 (sched.h:113-114)")
    d.code_panel(p, "src/kernel/sched.c", 330, 335,
                 1100, 4300, 9900, 4400, size=10,
                 caption_extra="do_timer 말미 — 감소")
    d.code_panel(p, "src/kernel/fork.c", 83, 86,
                 11500, 4300, 9700, 4400, size=10,
                 caption_extra="fork — 초기화")
    nbox(d, p, 21800, 4300, 10800, 4400, "INIT_TASK — 태스크 0",
         "sched.h:113-114 — { 0,15,15, … }\n= state 0 · counter 15 · priority 15\nsched.h:4 — NR_TASKS 64",
         K.PAPER, s1=14, s2=11)
    d.table(p, 1100, 9100, [7600, 11800, 12100], [
        ["시점", "코드", "counter 값"],
        ["타이머 틱마다", "do_timer — sched.c:332 --current->counter", "1씩 감소"],
        ["fork 시", "fork.c:85 p->counter = p->priority", "priority로 초기화"],
        ["모두 0일 때", "sched.c:136-139 (counter>>1)+priority", "재충전 — 전 태스크"],
        ["태스크 0 (기준)", "sched.h:113-114 INIT_TASK { 0,15,15,… }", "15 · priority 15"],
    ], row_h=1100, size=12)
    d.banner(p, "counter 는 세 규칙(감소·초기화·재충전)이 만든 값 — B-3은 재충전만 바꾼다")

    # ── 28 B-2. nice가 바꾸는 것 (코드) ──────────────────────────
    p = d.slide("B-2. nice가 바꾸는 것", K.S_CODE,
                "kernel/sched.c:378-383 sys_nice — priority -= increment (0보다 클 때만) · 측정은 33장 시연")
    d.code_panel(p, "src/kernel/sched.c", 378, 383,
                 1100, 4300, 15200, 4400, size=11,
                 caption_extra="sys_nice")
    d.table(p, 17200, 4300, [4200, 5400, 5800], [
        ["태스크", "priority", "재계산 후 counter"],
        ["A — 그대로", "15", "≈ 15 + …"],
        ["B — nice(10)", "5", "≈ 5 + …"],
        ["기대", "A가 약 3배 자주 뽑힘", "코드 추론"],
    ], row_h=1100, size=13)
    para(d, p, 1100, 9100, 31500, 1400,
         "재계산(counter = (counter>>1) + priority)이 priority 비중을 그대로 반영하므로, nice(10)으로 15→5가 된 자식 B는\n"
         "매 틱마다 받는 counter가 적어 완주가 늦어진다.", 15)
    para(d, p, 1100, 10700, 31500, 1400,
         "\"약 3배\"는 코드 읽기로만 나온 추론 — 실제 비율은 루프 길이·QEMU TCG 속도·다른 태스크(셸·init) 영향을 받는다.\n"
         "33장 시연에서 sched_pick 관찰값과 나란히 놓고 '경향'으로만 확인한다(§8).", 14)
    d.banner(p, "nice 는 counter 재충전량을 줄여 우선순위를 만든다 — 재충전식이 수정 대상")

    # ── 29 비교 ③: 오늘 가능한 정책 변형 (비교) ──────────────────
    p = d.slide("비교 ③: 오늘 가능한 정책 변형", K.S_CMP,
                "kernel/sched.c:104-142 위의 변형 4개 — 바꾸는 줄 / 두 프로세스 기대 결과 / 위험 · 오늘 구현은 ②")
    d.table(p, 1100, 4400, [5600, 9600, 8600, 7700], [
        ["정책", "바꾸는 줄", "두 프로세스 기대 결과", "위험"],
        ["① 원본 (기준)", "없음 — 136-139 그대로", "nice 준 B가 늦게 완주", "없음"],
        ["② 우선순위 무시", "136-139 의 priority → 15\n(또는 (counter>>1)+15 고정)", "두 자식이 같은 몫", "nice 무력화 — 기능 상실"],
        ["③ 라운드 로빈", "선택 루프(124-135)를 current\n다음 첫 RUNNING 으로 · 조건 제거", "번갈아 실행", "재계산 if (c) break 와\n충돌 — 0 counter 루프"],
        ["④ 깨어난 태스크 부스트", "wake_up 시 counter += k", "잠듦에서 깬 태스크 유리", "기아 가능"],
    ], row_h=1800, size=12)
    d.banner(p, "오늘 구현은 ② — 가장 작은 diff(3줄)로 효과가 확실하고 sched2 로 보인다")

    # ── 30 B-3. 변경 diff (코드) ─────────────────────────────────
    p = d.slide("B-3. 변경 diff — 3줄", K.S_CODE,
                "sched.c:136-139의 (*p)->priority 를 상수 15로 · 선택 루프는 그대로 — 바뀌는 것은 재충전량뿐")
    d.code_panel(p, "src/kernel/sched.c", 136, 139,
                 1100, 4300, 15200, 4200, size=11,
                 caption_extra="before — 원본 재계산")
    auto_pane(d, p, 17200, 4300, 15400, 4200,
              "after — lab/kernel/sched.c (3줄 diff)",
              "-  (*p)->counter = ((*p)->counter >> 1) +\n"
              "-          (*p)->priority;\n"
              "+  (*p)->counter = ((*p)->counter >> 1) +\n"
              "+          15;    /* SCHED_FLAT */", start=9)
    nbox(d, p, 1100, 9000, 15200, 3000, "선택 규칙은 유지된다",
         "선택 루프(124-135)는 그대로 — counter 최대 태스크를 뽑는\n규칙 자체는 변하지 않는다.\n바뀌는 것은 counter가 다시 채워지는 양뿐.", K.PAPER, s1=14, s2=11)
    nbox(d, p, 17200, 9000, 15400, 3000, "토글 안 (#define)",
         "#define SCHED_FLAT 으로 원본/수정본을\n한 줄로 전환 —\nA/B 비교 빌드에 쓴다.", K.PAPER, s1=14, s2=11)
    d.banner(p, "nice 로 낮춘 priority 가 재충전에 반영되지 않는다 — 같은 몫을 받는다")

    # ── 31 B-4. 두 프로세스 테스트 sched2.c (코드) ───────────────
    p = d.slide("B-4. 두 프로세스 테스트 sched2.c", K.S_CODE,
                "fork 두 번 — A 그대로 · B nice(10) · 같은 길이 빈 루프 · times(&t)(sys.c:156-166, 반환값 jiffies)로 측정")
    auto_pane(d, p, 1100, 4300, 19700, 10300,
              "sched2.c — 완주 시간 비교 프로그램",
              "#define N 30000000L   /* 게스트 속도에 맞춰 조정 */\n"
              "int main(void)\n"
              "{\n"
              "    struct tms t;  long t0, t1;\n"
              "    if (fork() == 0) {             /* 자식 A */\n"
              "        t0 = times(&t);\n"
              "        for (volatile long i=0; i<N; i++) ;\n"
              "        t1 = times(&t);\n"
              "        printf(\"A: start=%ld end=%ld\\n\", t0, t1);\n"
              "        _exit(0);\n"
              "    }\n"
              "    if (fork() == 0) {             /* 자식 B */\n"
              "        nice(10);                   /* priority 15 -> 5 */\n"
              "        ... 자식 A 와 같은 루프 ...\n"
              "        printf(\"B: start=%ld end=%ld\\n\", t0, t1);\n"
              "        _exit(0);\n"
              "    }\n"
              "    wait(NULL); wait(NULL);        /* 부모는 두 번 */\n"
              "    return 0;\n"
              "}", start=9)
    d.code_panel(p, "src/kernel/sys.c", 156, 162,
                 17200, 4300, 15400, 4200, size=10,
                 caption_extra="sys_times — 테스트의 시계")
    para(d, p, 17200, 8750, 15400, 5750,
         "측정 장치\n"
         "· times(&t) 반환값 = jiffies\n"
         "  (sys_times — sys.c:156-166)\n"
         "· start·end jiffies 를 각자 출력\n\n"
         "비교 지표\n"
         "· 두 자식의 end jiffies 차이\n"
         "· nice(10) → priority 15→5\n"
         "  (sys_nice — sched.c:378-383)", 13)
    d.banner(p, "같은 루프, 다른 nice — 정책이 완주 시간 차이로 드러나게 만든다")

    # ── 32 B-5. 관찰 장치 두 가지 (코드) ────────────────────────
    p = d.slide("B-5. 관찰 장치 두 가지", K.S_CODE,
                "(a) GDB 카운터 sched_pick — 1순위 · (b) printk — 재진입 위험(10장)을 알고 쓰는 2순위")
    auto_pane(d, p, 1100, 4300, 15200, 5300,
              "(a) GDB 카운터 [1순위] — sched.c 추가",
              "long sched_pick[NR_TASKS];\n"
              "\n"
              "/* switch_to(next) 직전 (141행 앞) */\n"
              "sched_pick[next]++;\n"
              "\n"
              "/* GDB */ (gdb) p sched_pick", start=11)
    auto_pane(d, p, 17200, 4300, 15400, 5300,
              "(b) printk [2순위] — 전환될 때만, 짧게",
              "if (next != last_next)\n"
              "    printk(\"[%d]\", task[next]->pid);\n"
              "\n"
              "/* 재진입 위험(10장)을 알고 쓴다 */", start=11)
    chain(d, p, 10000, [
        ("printk", "printk.c:21-41"),
        ("tty_write", "write_q로 복사"),
        ("sleep_if_full", "tty_io.c:299"),
        ("schedule()", "tty_io.c:323 — 재진입!"),
    ], h=1700)
    para(d, p, 1100, 12000, 31500, 2000,
         "전역 배열 sched_pick 은 GDB p 로 읽기만 해 schedule() 안에서 안전하다 — 관찰 도구가 관찰 대상을 바꾸지 않는다.\n"
         "(a) 카운터 추가 빌드(sys_hello 유지)가 33장 원본 측정의 기준 빌드다.", 14)
    d.banner(p, "관찰 도구는 대상을 바꾸지 않아야 한다 — 그래서 GDB 변수가 1순위다")

    # ── 33 시연 B-1: 원본 커널에서 측정 (시연) ────────────────────
    p = d.slide("시연 B-1: 원본 커널에서 측정", K.S_DEMO,
                "캡처 06·07 — 수정 전 lab(sys_hello 유지, sched_pick 카운터 추가 빌드) · 값은 환경 의존 — 경향만")
    d.placeholder_output(p, 1100, 4150, 15200, 7000,
                         "~ # ./sched2\n"
                         "A: start=1004  end=2871\n"
                         "B: start=1004  end=2954\n"
                         "~ #\n"
                         "/* 관찰: A의 end가 B보다 작음\n"
                         "   — A 먼저 완주 */",
                         "06-sched2-orig-run.png")
    d.placeholder_output(p, 17200, 4150, 15400, 7000,
                         "(gdb) p sched_pick\n"
                         "$1 = {0, 0, 0, 0, 312, 105, 0, ...}\n"
                         "/* task[4]=A, task[5]=B\n"
                         "   관찰: A 값이 B의 약 3배 (경향) */",
                         "07-gdb-sched-pick-orig.png")
    para(d, p, 1100, 11500, 31500, 2800,
         "기대 — A의 end jiffies가 B보다 훨씬 작다(먼저 완주). GDB p sched_pick 도 A 인덱스가 B의 약 3배.\n"
         "28장 \"약 3배\" 추론과 관찰을 나란히 — 환경 의존이므로 경향만 결론으로 삼는다(§8).", 13)
    d.banner(p, "수정 전 측정이 기준선 — 비교 없는 수정 후 측정은 아무것도 증명하지 못한다")

    # ── 34 시연 B-2: 수정 후 재측정 (시연) ───────────────────────
    p = d.slide("시연 B-2: 수정 후 재측정", K.S_DEMO,
                "캡처 08·09·10 — lab 수정본(sched flat) · 같은 루프 길이 · 30장 diff 적용 → build.sh → run.sh")
    d.placeholder_output(p, 1100, 4150, 15200, 7000,
                         "~ # ./sched2\n"
                         "A: start=1310  end=3548\n"
                         "B: start=1310  end=3561\n"
                         "~ #\n"
                         "/* 관찰: 두 end가 비슷 —\n"
                         "   같은 몫 */",
                         "09-sched2-flat-run.png")
    d.placeholder_output(p, 17200, 4150, 15400, 7000,
                         "(gdb) p sched_pick\n"
                         "$1 = {0, 0, 0, 0, 233, 229, 0, ...}\n"
                         "/* 관찰: 두 값 비슷 (약 1:1) */",
                         "10-gdb-sched-pick-flat.png")
    para(d, p, 1100, 11500, 31500, 2800,
         "기대 — 두 자식의 end jiffies가 비슷해지고 sched_pick 두 값도 비슷(약 1:1).\n"
         "캡처 08(3줄 diff 적용 화면·경고 없는 재빌드)도 같은 단계에서 확보한다.", 13)
    d.banner(p, "같은 테스트, 다른 커널 — 변수는 재계산 줄 하나뿐이라 차이가 그 탓임을 안다")

    # ── 35 시연 B-3: GDB로 재계산 순간 보기 (시연) ───────────────
    p = d.slide("시연 B-3: GDB로 재계산 순간 보기", K.S_DEMO,
                "캡처 11 — b sched.c:137 조건 if c==0 (실제 줄은 lab 기준) · 재계산 전후 counter 비교")
    auto_pane(d, p, 1100, 4150, 15200, 10300,
              "GDB — 재계산 루프에서 멈춰 값 보기",
              "(gdb) b sched.c:137 if c == 0\n"
              "/* 실제 줄 번호는 lab 기준 — 현장 확인 */\n"
              "(gdb) c\n"
              "Breakpoint 3, schedule () at sched.c:137\n"
              "(gdb) p task[2]->counter\n"
              "$1 = 0        /* 재계산 직전 */\n"
              "(gdb) p task[2]->priority\n"
              "$2 = 15\n"
              "(gdb) p task[3]->priority\n"
              "$3 = 5\n"
              "(gdb) next    /* 재계산 통과 */\n"
              "(gdb) p task[2]->counter\n"
              "$4 = 15       /* (0>>1)+15 */\n"
              "(gdb) p task[3]->counter\n"
              "$5 = 5        /* 원본 — 15/5 반영 */", start=10)
    d.placeholder_output(p, 17200, 4150, 15400, 7000,
                         "원본   : counter 15 / 5\n"
                         "         priority 반영됨\n"
                         "수정본 : counter 15 / 15\n"
                         "         같은 몫 — priority 무시\n"
                         "/* 관찰: 재계산 전후 값 */",
                         "11-gdb-recalc-counter.png")
    para(d, p, 17200, 11400, 15400, 3000,
         "task[2]·task[3] = 두 자식 가정 —\n"
         "인덱스는 실행 시 확인.\n"
         "수정본에서는 두 counter가\n"
         "같은 값으로 충전된다.", 13)
    d.banner(p, "정책 변경의 효과를 실행 중 값(counter)으로 본다 — 상태가 바뀐 것이다")

    # ── 36 시연 B 캡처 모음 (캡처) ───────────────────────────────
    p = d.slide("시연 B 캡처 모음 — 원본 vs 수정본", K.S_DEMO,
                "캡처 06–11 재구성 · 측정값은 루프 길이·QEMU TCG 속도 의존 — \"경향\"으로만 말한다 (§8)")
    d.placeholder_output(p, 1100, 4100, 15400, 5000,
                         "[원본] ./sched2\n"
                         "A: start=1004 end=2871\n"
                         "B: start=1004 end=2954",
                         "06-sched2-orig-run.png")
    d.placeholder_output(p, 17200, 4100, 15400, 5000,
                         "[수정본 sched flat] ./sched2\n"
                         "A: start=1310 end=3548\n"
                         "B: start=1310 end=3561",
                         "09-sched2-flat-run.png")
    d.placeholder_output(p, 1100, 9300, 15400, 5000,
                         "[원본] p sched_pick\n"
                         "{..., 312, 105, ...}  A:B 약 3:1",
                         "07-gdb-sched-pick-orig.png")
    d.placeholder_output(p, 17200, 9300, 15400, 5000,
                         "[수정본] p sched_pick\n"
                         "{..., 233, 229, ...}  약 1:1\n"
                         "[재계산] 원본 15/5 · 수정본 15/15",
                         "10-gdb-sched-pick-flat.png")
    d.banner(p, "관찰(약 3:1 → 약 1:1)이 28장 추론을 확정 — 차이는 재계산 줄 하나에서 왔다")

    # ── 37 printk를 schedule에 넣었더니 (선택 캡처) ──────────────
    p = d.slide("printk를 schedule에 넣었더니 (선택)", K.S_DEMO,
                "캡처 12 — 32장 (b) 관측 켠 빌드 · 강사 시연 C 대응 — 시간 부족 시 생략 가능")
    d.placeholder_output(p, 1100, 4150, 15200, 7300,
                         "~ # ./sched2\n"
                         "[4][5][4][5][4][4][5][4][5][4]\n"
                         "A: start=...  end=...\n"
                         "B: start=...  end=...\n"
                         "/* 관찰: 출력은 나온다.\n"
                         "   write_q가 차면 멈춤 가능 */",
                         "12-printk-in-schedule.png")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 298, 301,
                 17200, 4150, 15400, 3000, size=8,
                 caption_extra="sleep_if_full")
    for i, (t, sub) in enumerate([
            ("tty_write", "write_q 로 복사"),
            ("sleep_if_full", "tty_io.c:299-301 — 큐 차면 잠듦"),
            ("schedule()", "tty_io.c:321-323 — 재진입 위험")]):
        y = 7350 + i * 1800
        nbox(d, p, 17200, y, 15400, 1600, t, sub,
             K.ORANGE if i == 2 else K.PAPER, s1=13, s2=10)
        if i < 2:
            d.text(p, 24600, y + 1600, 500, 450, "↓", 12, K.ORANGE, True)
    para(d, p, 1100, 12800, 23800, 1600,
         "실제로 깨졌다면 그 화면을 캡처로, 안 깨졌다면 \"운이 좋았다\"고 말하고 코드 근거(299-301 · 321-323)를 보인다.\n"
         "schedule() 안의 printk 는 언제나 이 위험을 짊어진다 — 그래서 32장 (a)가 기본 관찰 장치다.", 13)
    d.outline(p, 25600, 12850, 7000, 1000, K.TEAL, 60)
    d.text(p, 25700, 13080, 6800, 550, "선택 — 시간 부족 시 생략", 13, K.TEAL, True)
    d.banner(p, "출력이 나왔다고 안전한 게 아니다 — 큐가 찬 순간이 위험의 조건이다")

    # ── 38 상태 변화도 다시: 두 실습이 지난 길 (상태도) ───────────
    p = d.slide("상태 변화도 다시 — 두 실습이 지난 길", K.S_STATE,
                "9장 상태도 + A·B 두 바퀴 궤적 · A-4 깨뜨리기(24장)의 검증됨→수정됨 되돌림(ORANGE)")
    draw_life(d, p, tracks=True)

    # ── 39 재빌드·검증 체크리스트 (정리) ─────────────────────────
    p = d.slide("재빌드·검증 체크리스트", K.S_WRAP,
                "여섯 단계 — 매 실습 바퀴마다 처음부터 끝까지 소리 내어 점검한다")
    d.table(p, 1100, 4400, [3800, 13100, 14600], [
        ["단계", "확인할 것", "근거 · 실패 증상"],
        ["편집 전", "src/가 아닌 lab/인가 — 경로 확인", "src/ 편집 금지 — '출력 없음' 실패로 이어짐"],
        ["편집 후", "네 곳 번호 일치: __NR_hello = 표 인덱스 = nr_system_calls-1", "12–14장 — 어긋나면 EPERM·잘못된 호출"],
        ["빌드", "build.sh 종료 코드 · 경고 중 implicit declaration", "extern 선언 누락 감지 (13장)"],
        ["부팅", "run.sh의 Image가 방금 빌드한 것인가 — 타임스탬프", "옛 Image면 '수정했는데 그대로' (41장)"],
        ["GDB", "file이 방금 tools/system인가 — info files · pending 여부", "pending = 심벌 불일치 (41장)"],
        ["검증", "기대 출력과 실제 출력을 슬라이드에 나란히", "관찰 vs 추론 구분 (00-common §7)"],
    ], row_h=1450, size=12)
    d.banner(p, "체크리스트가 곧 핵심 질문의 절차화 — 어디서(단계) 어떻게(수단) 확인하는가")

    # ── 40 흔한 실패 ①: 시스템 콜 쪽 (정리) ──────────────────────
    p = d.slide("흔한 실패 ① — 시스템 콜 쪽", K.S_WRAP,
                "증상 → 원인 역추적 표 — 24장에서 하나를 직접 재현해 봤다")
    d.table(p, 1100, 4400, [8300, 11600, 11600], [
        ["증상", "원인", "근거"],
        ["errno=1, r=-1", "nr_system_calls 미갱신 — bad_sys_call", "system_call.s:61, 72-74 · unistd.h:146-157"],
        ["__NR_hello undeclared", "__LIBRARY__ 누락 또는 게스트 헤더가 옛것", "unistd.h:58, 133-157"],
        ["undefined reference sys_hello", "함수 파일이 OBJS에 없거나 이름 불일치", "kernel/Makefile:27-32"],
        ["쓰레기 값 · 페이지 폴트", "사용자 포인터 직접 역참조", "asm/segment.h — 17장 규칙"],
        ["출력 없음", "src/를 고침 — lab/만 바뀌어야 한다", "§8 첫 항목 — 경로 확인 (39장)"],
    ], row_h=1650, size=13)
    d.banner(p, "증상을 읽는 힘이 실습의 실력 — 빌드·링크가 잡지 못하는 오류가 위험하다")

    # ── 41 흔한 실패 ②: 빌드·도구 쪽 (정리) ──────────────────────
    p = d.slide("흔한 실패 ② — 빌드·도구 쪽", K.S_WRAP,
                "도구 쪽 4가지 — 심벌 이름 차이는 lab 툴체인 기준 확인 필요 사항(§11)")
    d.table(p, 1100, 4400, [8300, 11600, 11600], [
        ["증상", "원인", "근거"],
        ["중단점이 안 걸림", "옛 tools/system을 GDB에 로드 — 심벌 불일치", "심벌 파일 = 이번 빌드 (07장)"],
        ["_sys_call_table vs sys_call_table", "src(옛 gas, 밑줄 접두)와 lab(현대 gas)의 심벌 차이", "§11 확인 목록 — nm 결과로 기록"],
        ["수정했는데 그대로", "run.sh가 다른 Image 경로를 봄", "타임스탬프 확인 (08장)"],
        ["부팅 멈춤", "nr_system_calls를 표 길이보다 크게 — 표 밖 NULL 호출", "system_call.s:61 — 번호·상한 일치"],
    ], row_h=1700, size=13)
    para(d, p, 1100, 13100, 31500, 1500,
         "공통 패턴 — '내 수정은 옳았는데 도구가 옛것을 보여 줬다'. 빌드 산출물(Image·심벌)과 실행 대상의 일치가 전제다.", 14)
    d.banner(p, "옛 심벌·옛 이미지 — 커널이 틀린 게 아니라 보는 창이 과거일 뿐이다")

    # ── 42 비교 ①(완성): 변경 위치 × 검증 수단 (비교) ────────────
    p = d.slide("비교 ①(완성) — 변경 위치 × 검증 수단", K.S_CMP,
                "20장 표에 검증 수단 열을 채운 완성판 — 10장 검증 수단 6가지와 짝지은다")
    d.table(p, 1100, 4400, [5000, 7500, 8700, 10300], [
        ["변경 위치", "어느 파일", "틀렸을 때 증상", "검증 수단"],
        ["사용자 프로그램", "hello.c", "컴파일 오류 · errno", "프로그램 출력 · errno"],
        ["__NR_* 번호", "include/unistd.h", "undeclared", "컴파일러 메시지 → 헤더 수정"],
        ["sys_call_table[]", "include/linux/sys.h", "잘못된 함수 호출", "GDB p sys_call_table[72]"],
        ["nr_system_calls", "kernel/system_call.s", "EPERM처럼 보임", "GDB b bad_sys_call"],
        ["새 커널 함수", "kernel/sys.c", "undefined sys_hello", "printk · b sys_hello"],
        ["schedule()", "kernel/sched.c", "동작만 변화 — 오류 없음", "sched_pick · jiffies 비교 · 재계산 중단점"],
    ], row_h=1450, size=12)
    d.banner(p, "어디를 바꿨느냐가 어떻게 확인할지를 정한다 — 위치마다 짝이 정해져 있다")

    # ── 43 변경을 되돌리고 남기는 법 (정리) ──────────────────────
    p = d.slide("변경을 되돌리고 남기는 법", K.S_WRAP,
                "캡처 13 — lab/의 변경은 패치로 남기고 원본 복구 · src/는 끝까지 무변경임을 증명한다")
    d.placeholder_output(p, 1100, 4150, 15200, 7300,
                         "lab/ $ git diff > build/15-hello.patch\n"
                         "lab/ $ git diff > build/15-sched-flat.patch\n"
                         "lab/ $ git checkout -- .\n"
                         "lab/ $ wc -l build/15-hello.patch\n"
                         "     12 build/15-hello.patch\n"
                         "\n"
                         "$ diff -r src/ src-pristine/\n"
                         "$   /* 출력 없음 = src/ 무변경 */",
                         "13-src-diff-r-untouched.png")
    steps = [("① 패치 저장", "git diff > build/15-*.patch — 두 실습 각각"),
             ("② 원본 복구", "git checkout — lab/를 깨끗하게"),
             ("③ 재적용 가능", "다음 학기에 patch -p1 < … 로 재현"),
             ("④ src/ 무변경 증명", "diff -r — 출력 없음이 증거")]
    for i, (t, sub) in enumerate(steps):
        y = 4300 + i * 1950
        nbox(d, p, 17200, y, 15400, 1700, t, sub, K.PAPER, s1=14, s2=10)
        if i < 3:
            d.text(p, 24600, y + 1700, 500, 500, "↓", 14, K.ORANGE, True)
    para(d, p, 1100, 11700, 15200, 2400,
         "오늘 산출물 — 패치 2개(hello·sched flat)와 캡처들. 패치는 lab/ 상태를 그대로 재현하는 단위다.\n"
         "9장 상태도의 되돌림 전환을 실제로 한 번 밟아 보는 것이기도 하다.", 13)
    d.banner(p, "변경은 자산이 된다 — 패치로 남기면 다음에 같은 실험 환경이 돌아온다")

    # ── 44 핵심 질문의 답 (정답) ─────────────────────────────────
    p = d.slide("핵심 질문의 답", K.S_ANS,
                "9장 상태도 축약 재인용 + 네 조건 — 질문(02장)에 대한 오늘의 종합 답")
    d.outline(p, 1100, 4300, 31500, 4300, K.ORANGE, 110)
    d.text(p, 1500, 4600, 30700, 3700,
           "\"커널을 바꾸면 (1) 변경이 사는 자리에 따라 빌드 범위가 다르고,\n"
           "(2) 그 자리에 맞는 수단 — 사용자 출력 / errno, printk, GDB 표·변수·중단점 — 으로,\n"
           "(3) 같은 빌드의 심벌 파일을 들고,\n"
           "(4) 수정 전과 후를 나란히 놓고 확인한다.\"", 20, K.ORANGE, True)
    for i, (name, sub) in enumerate(LIFE_STATES):
        x = 1100 + i * 6475
        nbox(d, p, x, 9100, 5600, 1500, name, sub,
             K.TEAL if i < 4 else None, s1=14, s2=8)
        if i < 4:
            d.text(p, x + 5630, 9450, 600, 600, "→", 14, K.TEAL, True)
    para(d, p, 1100, 11000, 31500, 3200,
         "네 조건과 다섯 상태의 대응 — (1) 자리 = 수정됨→빌드됨 전이의 범위 · (2) 수단 = 부팅됨→검증됨의 방법 ·\n"
         "(3) 심벌 = 빌드됨의 유지 조건 · (4) 전후 비교 = 검증됨의 정의.\n"
         "20장(위치별 범위)·10장(수단)·42장(위치×수단 짝)이 이 네 조건의 전개였다.", 14)
    d.banner(p, "바꾼 곳을 알면 확인할 곳이 보인다 — 확인은 같은 빌드 안에서 일어난다")

    # ── 45 15회차 되돌아보기 (로드맵) ────────────────────────────
    p = d.slide("15회차 되돌아보기 — 핵심 질문 15개", K.S_MAP,
                "01 \"셸이 나오기 전에 누가 실행되는가?\"부터 오늘 질문까지 · 오늘 수정 두 지점(시스템 콜 표·schedule) 표시")
    qs = [
        ("01", "셸이 나오기 전에\n누가 실행되는가?", False, False),
        ("02", "선택자 하나가 어떻게\n주소가 되는가?", False, False),
        ("03", "512B에서 main()까지\nCPU 상태는?", False, False),
        ("04", "write(1, ...) 이 어떻게\n커널에 왕복하는가?", False, True),
        ("05", "타이머 틱 한 번에\n태스크는 어떻게 바뀌나?", False, True),
        ("06", "fork() 후 부모·자식은\n어디서 다시 실행되나?", False, False),
        ("07", "같은 주소가 왜 다른\n메모리를 가리키나?", False, False),
        ("08", "자식이 바꿔도 부모 값은\n왜 그대로인가?", False, False),
        ("09", "PID 그대로 프로그램은\n어떻게 바뀌나?", False, False),
        ("10", "자식이 죽으면 부모는\n어떻게 아는가?", False, False),
        ("11", "read()가 디스크에\n가는 때는 언제인가?", False, False),
        ("12", "\"/etc/rc\"가 어떻게\n디스크 블록이 되나?", False, False),
        ("13", "누른 글자가 read()까지\n어떻게 전달되나?", False, False),
        ("14", "`ls /` 한 줄에 배운 것이\n모두 등장하는가?", False, False),
        ("15", "커널을 바꾸면 어디서\n어떻게 확인하는가?", True, False),
    ]
    for i, (no, q, today, touched) in enumerate(qs):
        row, col = divmod(i, 5)
        x = 1100 + col * 6400
        y = 4150 + row * 3200
        if today:
            nbox(d, p, x, y, 6100, 2900, no, q, K.ORANGE, s1=16, s2=11)
        else:
            nbox(d, p, x, y, 6100, 2900, no, q, K.PAPER, K.INK,
                 edge=K.TEAL if touched else None, s1=16, s2=11)
        if i < 14 and col < 4:
            d.text(p, x + 6130, y + 1100, 300, 600, "→", 13, K.TEAL, True)
    para(d, p, 1100, 13350, 31500, 1200,
         "TEAL 테두리 04·05 — 오늘 수정한 두 지점(14회차 지도의 테두리 = 시스템 콜 표, 박스 ⑨ = schedule). "
         "읽기(01–14)가 바꾸기(15)로 이어졌다.", 12, K.MUTED)
    d.banner(p, "15개 질문이 모두 같은 문서(src/)에서 답됐다 — 마지막은 그 문서를 고쳐서 답했다")

    # ── 46 이해 확인 질문 (확인) ─────────────────────────────────
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(47) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4200, 31500, 2600, "Q1",
         "`__NR_hello 72`, 표 끝에 `sys_hello`를 넣고 빌드했는데 `./hello`가 `r=-1 errno=1`이다. 가장 먼저 의심할 곳은?",
         K.TEAL, 13)
    qbox(d, p, 1100, 6800, 31500, 2600, "Q2",
         "새 시스템 콜이 사용자 버퍼 포인터를 받는다. 커널에서 `buf[0]`을 그냥 읽으면 왜 안 되는가?",
         K.TEAL, 13)
    qbox(d, p, 1100, 9400, 31500, 2600, "Q3",
         "재계산 식의 `priority`를 상수 15로 바꾸면 선택 규칙(counter 최대)도 바뀌는가? 두 자식의 결과는 왜 같아지는가?",
         K.TEAL, 13)
    qbox(d, p, 1100, 12000, 31500, 2600, "Q4",
         "스케줄러 관찰에 printk 대신 `sched_pick[]` 카운터를 1순위로 두는 이유는?", K.TEAL, 13)

    # ── 47 이해 확인 정답 (확인) ─────────────────────────────────
    p = d.slide("이해 확인 정답", K.S_QUIZ,
                "근거 줄 번호 포함 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4200, 31500, 2600, "A1",
         "kernel/system_call.s:61의 `nr_system_calls`. 72인 채면 `cmpl $nr_system_calls-1,%eax; ja bad_sys_call`"
         "(81–82)로 `-1`이 돌아오고, `_syscall1`(unistd.h:146–157)이 그것을 `errno=1`로 바꾼다.", K.ORANGE, 13)
    qbox(d, p, 1100, 6800, 31500, 2600, "A2",
         "시스템 콜 진입 시 ds/es는 커널 세그먼트 0x10, 사용자 데이터는 fs=0x17(system_call.s:89–93). "
         "사용자 주소는 `get_fs_byte/put_fs_byte`(asm/segment.h)로만 접근해야 하며, `sys_times`(sys.c:156–166)가 본보기다.",
         K.ORANGE, 13)
    qbox(d, p, 1100, 9400, 31500, 2600, "A3",
         "선택 규칙(sched.c:124–135)은 그대로다. 바뀐 것은 counter가 다시 채워지는 양(136–139)뿐이며, "
         "nice로 낮춘 priority가 더 이상 반영되지 않아 두 자식이 같은 몫을 받는다.", K.ORANGE, 13)
    qbox(d, p, 1100, 12000, 31500, 2600, "A4",
         "`printk`는 `tty_write`를 부르고(printk.c:29–39), `tty_write`는 `sleep_if_full`·`schedule()`을 부를 수 있어"
         "(tty_io.c:299, 323) `schedule()` 안에서 재진입할 위험이 있다. 전역 배열은 GDB `p`로 읽기만 하면 된다.",
         K.ORANGE, 13)

    # ── 48 정리와 과정 마무리 (정리) ─────────────────────────────
    p = d.slide("정리와 과정 마무리 — 종강", K.S_WRAP,
                "오늘 산출물과 더 해 볼 것 · 자료는 PPTX 1개뿐 — 15회차 파트 A–G «종합·실습» 완결")
    d.cards(p, [
        ("오늘 산출물",
         "패치 2개 — hello · sched flat\ncapture 13종 예정\nsrc/ 무변경 확인 (43장)"),
        ("더 해 볼 것 — 검증 짝",
         "사용자 포인터 콜 — get_fs_*\n라운드 로빈 — sched2 완주\nwake_up 부스트 — 기아 관찰"),
        ("과정 완결",
         "파트 A–G «종합·실습» 완결\n15/15 — 종강\n자료는 PPTX 1개뿐"),
    ], y=4250, h=7500)
    d.outline(p, 1100, 11950, 31500, 1400, K.ORANGE, 100)
    d.text(p, 1400, 12200, 30900, 1000,
           "종강 — 읽기(01–14)에서 바꾸기(15)로: \"커널을 바꾸면 어디서 어떻게 확인하는가?\"에 스스로 답한다",
           18, K.ORANGE, True)
    para(d, p, 1100, 13500, 31500, 1000,
         "다음 학기 반복은 패치 재적용(43장) · 체크리스트(39장) · 흔한 실패 표(40–41장)부터 다시 읽는다.", 14)


if __name__ == "__main__":
    K.run(globals())
