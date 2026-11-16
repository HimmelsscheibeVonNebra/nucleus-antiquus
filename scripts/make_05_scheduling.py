#!/usr/bin/env python3
"""05회차 덱 — 태스크와 스케줄링 (output/05-scheduling.pptx)

계획: materials/slide-plans/05-scheduling.md (§2 표 48행 1:1 · §3 앞부분 명세 ·
§4 시각자료 목록 · §5 캡처 5종 · §6 이해 확인 · §8 오해 금지).
캡처 5종 실측 확보 — materials/05-scheduling/captures/ (36·38·40장 d.picture).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uno
import deckkit as K

SESSION = dict(
    no="05", total=48, slug="05-scheduling",
    part_no="B", part="«실행의 길»",
    title="05. 태스크와 스케줄링",
    question="타이머 틱 한 번에 실행 중인 태스크가 어떻게 바뀌는가?",
    done=4,
    today_line="틱 한 번 — 회계에서 TSS 전환까지",
    next_lines=[
        "04 → 05   _timer_interrupt에서 call _do_timer까지 봤다(04) → 그 다음 줄에서 실행 중인 태스크가 바뀐다(05)",
        "05 → 06   switch_to로 TSS 전환을 봤다(05) → task[1]은 누가 만드는가 — fork(06)",
        "05 ⋯ 10   ZOMBIE·sys_waitpid는 10(종료·대기·시그널)에서 다시 본다 — 점선 연결",
    ],
    road_note=("오늘은 질문·지도·배경·코드·상태도·비교·시연·정답·확인·정리 10단계 모두를 다룬다"
               " — '오늘은 다루지 않음' 단계는 없다.\n"
               "배경 05·16·31·46 · 코드 06–15·17·20–22·26–27·29–30·32–33 · 상태도 23–25 · "
               "비교 18·19·28 · 시연 34–41 · 정답 42–43 · 확인 47 · 정리 44·45·48"),
    STRUCT=dict(
        teal=["proc"],
        today=[("include/linux/sched.h", "task_struct·tss"),
               ("kernel/sched.c", "schedule·do_timer"),
               ("kernel/system_call.s", "_timer_interrupt")],
        flow="IRQ 0 → _timer_interrupt → do_timer → schedule → switch_to → TSS 전환",
        user="sh · 사용자 프로그램",
    ),
)

CHECKS = dict(
    captions={
        6: "src/include/linux/sched.h:78-92",
        7: "src/include/linux/sched.h:80-82",
        8: "src/include/linux/sched.h:51-63",
        9: "src/kernel/sched.c:53-65",
        10: "src/init/main.c:138-148",
        11: "src/kernel/sched.c:404-410",
        12: "src/kernel/system_call.s:176-189",
        13: "src/kernel/sched.c:305-317",
        14: "src/kernel/sched.c:319-331",
        15: "src/kernel/sched.c:332-335",
        17: "src/kernel/system_call.s:95-100",
        20: "src/kernel/sched.c:104-120",
        21: "src/kernel/sched.c:124-135",
        22: "src/kernel/sched.c:136-141",
        23: "src/include/linux/sched.h:19-23",
        26: "src/kernel/sched.c:151-165",
        27: "src/kernel/sched.c:167-177",
        29: "src/include/linux/sched.h:171-184",
        30: "src/include/linux/sched.h:173-180",
        32: "src/kernel/sched.c:385-401",
        33: "src/kernel/fork.c:93-94",
        48: "src/kernel/fork.c:95-97",
    },
    required=[
        "task_struct", "tss_struct", "counter", "priority", "jiffies", "current",
        "do_timer", "schedule", "switch_to", "ljmp", "TASK_RUNNING",
        "TASK_INTERRUPTIBLE", "TASK_UNINTERRUPTIBLE", "TASK_ZOMBIE",
        "TASK_STOPPED", "sleep_on", "wake_up", "interruptible_sleep_on",
        "ret_from_sys_call", "esp0", "LATCH", "utime", "stime", "비선점",
        "재충전", "타임 슬라이스", "대기 큐", "TSS 전환", "idle",
    ],
    prereq=[
        ("_timer_interrupt", "src/kernel/system_call.s:176-189"),
        ("do_timer", "src/kernel/sched.c:305-317"),
        ("switch_to", "src/include/linux/sched.h:171-184"),
    ],
    structure_nodes=["sched.h", "sched.c", "system_call.s", "IRQ", "TSS"],
    capture_slides=[36, 38, 40],
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


def ellipse(d, p, x, y, w, h, fill=None, edge=K.MUTED, lw=110, dash=False):
    sh = d.doc.createInstance("com.sun.star.drawing.EllipseShape")
    sh.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
    sh.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
    p.add(sh)
    if fill is None:
        sh.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "NONE")
    else:
        sh.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        sh.FillColor = fill
    sh.LineStyle = uno.Enum("com.sun.star.drawing.LineStyle", "SOLID")
    sh.LineColor = edge
    sh.LineWidth = lw
    if dash:
        try:
            dash_s = uno.createUnoStruct("com.sun.star.drawing.LineDash")
            dash_s.Style = uno.Enum(
                "com.sun.star.drawing.DashStyle", "RECTANGLE")
            dash_s.Dots = 0
            dash_s.DotLength = 0
            dash_s.Dashes = 3
            dash_s.DashLength = 200
            dash_s.Distance = 150
            sh.LineDash = dash_s
        except Exception:
            pass
    return sh


def etext(d, p, x, y, w, text, size=15, color=K.PAPER, sub=None,
          sub_size=11, sub_color=None):
    center = uno.Enum("com.sun.star.drawing.TextHorizontalAdjust", "CENTER")
    sh = d.text(p, x, y, w, 700, text, K.fit_size(text, size, w), color, True)
    sh.TextHorizontalAdjust = center
    if sub:
        sh2 = d.text(p, x, y + 700, w, 900, sub,
                     K.fit_size(sub, sub_size, w),
                     sub_color or (K.MUTED if color == K.PAPER else color))
        sh2.TextHorizontalAdjust = center


def frow(d, p, x, y, w, h, main, cap, fill=None, s1=15, s2=10, cap_w=5200):
    """경로 다이어그램 행 — 본문(좌)과 출처 캡션(우측 정렬)을 한 줄 안에.
    두 줄 nbox와 달리 캡션이 아래 박스와 겹치지 않는다."""
    if fill is None:
        d.outline(p, x, y, w, h, K.MUTED, 90)
    else:
        d.shape(p, x, y, w, h, fill)
    mwid = w - 900 - cap_w
    d.text(p, x + 300, y + (h - s1 * 44) // 2, mwid, s1 * 52, main,
           K.fit_size(main, s1, mwid, min_size=11), K.INK, True)
    d.text(p, x + w - 300 - cap_w, y + (h - s2 * 44) // 2, cap_w, s2 * 52,
           cap, K.fit_size(cap, s2, cap_w, min_size=8),
           K.INK if fill else K.MUTED, False)


def qbox(d, p, x, y, w, h, tag, body, tag_color, size=14):
    d.shape(p, x, y, w, h, K.INK)
    d.shape(p, x, y, w, 130, tag_color)
    d.text(p, x + 250, y + 320, w - 500, 500, tag, 15, tag_color, True)
    para(d, p, x + 250, y + 950, w - 500, h - 1150, body, size, K.PAPER)


def page_pic(d, p, x, y, w, h, stack_label, struct_label):
    """union task_union 한 페이지 그림 — 스택은 위에서 내려온다."""
    d.outline(p, x, y, w, h, K.LINE, 110)
    d.text(p, x, y - 620, w, 520,
           "PAGE_SIZE (4 KiB)", 11, K.TEAL, True)
    d.text(p, x + 250, y + 150, w - 500, 520, "— 페이지 끝 (esp0)", 11,
           K.ORANGE, True)
    d.text(p, x + 250, y + 900, w - 500, h - 3600, stack_label, 12, K.PAPER)
    d.shape(p, x + 250, y + h - 2300, w - 500, 2050, K.TEAL)
    d.text(p, x + 400, y + h - 2100, w - 800, 700, struct_label, 13, K.INK,
           True)
    d.text(p, x + 400, y + h - 1400, w - 800, 900,
           "페이지 시작에 배치", 10, K.INK)


def populate(d):
    # ── 배경 05 ───────────────────────────────────────────────
    # 05 태스크란 커널이 기억하는 한 묶음
    p = d.slide("태스크란 커널이 기억하는 한 묶음", K.S_BG,
                "include/linux/sched.h:78-107 — 06 fork에서 만들어지는 묶음을 오늘은 '갈아끼우는 장치'로 본다")
    para(d, p, 1100, 4400, 15200, 9800,
         "CPU는 하나, 프로그램은 여럿 — 동시에 돌리려면 '누가 어디까지 했는지'를 "
         "누군가 기억해야 한다.\n\n"
         "각 프로그램의 묶음 — 멈춘 지점 + 레지스터 + 메모리 + 파일 —을 "
         "task_struct 하나에 통째로 둔다.\n\n"
         "1회차의 '프로세스'와 같은 것 — 0.11 소스는 task라고 부른다"
         "(struct task_struct, sched.h:78).\n\n"
         "이 묶음은 06회차 fork의 copy_process가 만든다(예고 48장). "
         "오늘 보는 것은 완성된 묶음을 틱마다 갈아끼우는 장치다.", 17)
    nbox(d, p, 18000, 4500, 6600, 1500, "멈춘 지점 — tss.eip", None, K.PAPER,
         s1=14)
    nbox(d, p, 25400, 4500, 6600, 1500, "레지스터 — tss 전체", None, K.PAPER,
         s1=14)
    nbox(d, p, 18000, 6300, 6600, 1500, "메모리 — ldt (base)", None, K.PAPER,
         s1=14)
    nbox(d, p, 25400, 6300, 6600, 1500, "파일 — filp[NR_OPEN]", None, K.PAPER,
         s1=14)
    arrow(d, p, 20500, 7950, "↓", 22)
    arrow(d, p, 27900, 7950, "↓", 22)
    nbox(d, p, 19000, 9000, 12000, 1700, "struct task_struct",
         "sched.h:78-107 — task[] 슬롯 하나", K.TEAL, s1=17, s2=12)
    para(d, p, 17800, 11100, 14400, 3000,
         "묶음 단위로 저장·복원하면 프로그램 입장에서는 'CPU를 혼자 쓰는 것처럼' "
         "보인다 — 문맥(context) 교체.", 14, K.MUTED)
    d.banner(p, "묶음 하나 = task_struct 하나 — 오늘은 이 묶음을 틱마다 갈아끼우는 장치를 본다", 14800, 19)

    # ── 코드 06–15 ────────────────────────────────────────────
    # 06 struct task_struct 전체
    p = d.slide("struct task_struct 전체", K.S_CODE,
                "sched.h:78-107 · 앞 세 필드의 오프셋 = system_call.s:48-53 (state 0 · counter 4 · priority 8)")
    chips = [("80–85 하드코딩 state·counter·priority·signal", 0xB2EBDF),
             ("87–94 pid·시간 (utime·stime·alarm)", 0x8ADFD0),
             ("96–102 fs (pwd·root·executable·filp)", 0x5FCBB9),
             ("104 ldt (코드·데이터 세그먼트)", 0x3DB49F),
             ("106 tss (레지스터 저장소)", 0x2A9A88)]
    cw = (31500 - 4 * 400) // 5
    for i, (label, col) in enumerate(chips):
        badge(d, p, 1100 + i * (cw + 400), 4200, cw, label, col, 800, 12)
    d.code_panel(p, "src/include/linux/sched.h", 78, 92, 1100, 5200, 15200,
                 9200, size=9, caption_extra="다섯 구역 중 1–3구역")
    d.code_panel(p, "src/include/linux/sched.h", 93, 107, 16900, 5200, 15700,
                 9200, size=9, caption_extra="다섯 구역 중 3–5구역")
    d.banner(p, "\"hardcoded - don't touch\" — 앞 세 필드는 system_call.s:48-53의 오프셋과 맞아야 한다", 14700, 18)

    # 07 state, counter, priority
    p = d.slide("state, counter, priority — 앞 세 필드", K.S_CODE,
                "sched.h:80-82 · 주석과 실제 값(19-23) 대조 · INIT_TASK(113-114)는 counter=priority=15")
    d.code_panel(p, "src/include/linux/sched.h", 80, 82, 1100, 4400, 19700,
                 3400, size=14,
                 caption_extra="주석: -1 unrunnable, 0 runnable, >0 stopped")
    d.table(p, 1100, 8100, [5000, 6600, 8100], [
        ["주석(sched.h:80)", "실제 정의(19-23)", "의미"],
        ["0 runnable", "0 TASK_RUNNING", "실행 가능 — 이 중 current가 CPU"],
        ["-1 unrunnable", "1 TASK_INTERRUPTIBLE", "시그널로 깨울 수 있는 잠"],
        ["", "2 TASK_UNINTERRUPTIBLE", "이벤트 완료까지 안 깨는 잠"],
        [">0 stopped", "3 TASK_ZOMBIE · 4 TASK_STOPPED", "거두기 대기 · 정의뿐(진입 없음)"],
    ], row_h=1000, size=13)
    d.code_panel(p, "src/include/linux/sched.h", 113, 114, 22000, 4400, 10500,
                 3100, size=12, caption_extra="INIT_TASK — state 0 · 15 · 15")
    para(d, p, 22000, 7900, 10500, 6400,
         "counter — 남은 틱. do_timer가 매 틱 1씩 줄인다(sched.c:332).\n\n"
         "priority — 재충전 기준값. INIT_TASK는 둘 다 15.\n\n"
         "타임 슬라이스 = counter가 허용하는 연속 실행량.", 15)
    d.banner(p, "counter = 남은 틱, priority = 재충전 기준 — counter를 '우선순위'라 부르지 않는다(§8)", 14700, 18)

    # 08 struct tss_struct
    p = d.slide("struct tss_struct", K.S_CODE,
                "sched.h:51-76 · CPU가 태스크 전환 시 저장·복원하는 레지스터 전부 · i387은 FPU 상태")
    d.code_panel(p, "src/include/linux/sched.h", 51, 63, 1100, 4400, 10600,
                 8300, size=9, caption_extra="back_link … eflags")
    d.code_panel(p, "src/include/linux/sched.h", 64, 76, 12100, 4400, 10600,
                 8300, size=9, caption_extra="eax … i387")
    d.text(p, 23400, 4400, 9400, 600, "104바이트 배치 (0x00–0x67)", 14,
           K.TEAL, True)
    rows = [("0x00  back_link", False), ("0x04  esp0 ★", True),
            ("0x08  ss0 ★ (0x10)", True),
            ("0x0c–0x18  esp1/ss1/esp2/ss2", False),
            ("0x1c  cr3 ★", True), ("0x20  eip ★", True),
            ("0x24  eflags", False), ("0x28–0x44  eax–edi (8개)", False),
            ("0x48–0x5c  es·cs·ss·ds·fs·gs", False), ("0x60  ldt ★", True),
            ("0x64  trace_bitmap", False), ("0x68  i387 (108 B)", False)]
    for i, (label, hot) in enumerate(rows):
        nbox(d, p, 23400, 5100 + i * 710, 9400, 700, label, None,
             K.ORANGE if hot else None, K.INK, s1=12)
    d.banner(p, "esp0/ss0가 04회차 '커널 스택으로 전환'의 출처 — cr3·eip·ldt까지 전부 이 안에 있다", 14700, 18)

    # 09 task[], current, jiffies가 사는 곳
    p = d.slide("task[], current, jiffies가 사는 곳", K.S_CODE,
                "sched.c:53-72 · extern 선언은 sched.h:136-142 · 66-72 user_stack·stack_start는 03회차 복습")
    d.code_panel(p, "src/kernel/sched.c", 53, 65, 1100, 4400, 19700, 8300,
                 size=10, caption_extra="union task_union · init_task · jiffies · current · task[]")
    page_pic(d, p, 22100, 5000, 4400, 8300,
             "커널 스택\n\n위에서 ↓\n내려온다", "task_struct")
    para(d, p, 27000, 5000, 5600, 8300,
         "union task_union — task_struct와 4 KiB 커널 스택이 한 페이지.\n\n"
         "init_task = {INIT_TASK,} — 58\n\n"
         "current = &(init_task.task) — 62\n\n"
         "task[0] = &(init_task.task) — 65\n\n"
         "jiffies = 0 — 60, volatile", 14)
    d.banner(p, "task[NR_TASKS] · current · jiffies — 스케줄러의 전역 상태가 전부 sched.c 상단에 선다", 14800, 19)

    # 10 task 0은 무엇을 하는가
    p = d.slide("task 0은 무엇을 하는가", K.S_CODE,
                "init/main.c:138-148 (fork → init · for(;;) pause()) · sched.c:100-102 주석 · :126 next=0")
    d.code_panel(p, "src/init/main.c", 138, 148, 1100, 4400, 19700, 8300,
                 size=8, caption_extra="move_to_user_mode 뒤 — fork()와 무한 pause")
    auto_pane(d, p, 22000, 4400, 10500, 3400,
              "kernel/sched.c:100-102 — Linus 주석 발췌",
              "NOTE!!  Task 0 is the 'idle' task, which\n"
              "gets called when no other tasks can run.\n"
              "It can not be killed, and it cannot sleep.\n"
              "The 'state' information in task[0] is\n"
              "never used.")
    para(d, p, 22000, 8200, 10500, 6100,
         "main()은 fork()로 task[1](init)를 만들고 자신은 for(;;) pause() — "
         "move_to_user_mode(137) 뒤의 사용자 모드 무한 루프.\n\n"
         "schedule()의 next=0 기본값(126) — 뛸 태스크가 없으면 task 0이 CPU를 갖는다.\n\n"
         "main.c:142-146 주석 — task0의 pause()는 '다른 태스크가 있는지만 보고 돌아온다'.", 14)
    d.banner(p, "task 0 = idle — 죽지도 잠들지도 않는다, 아무도 못 뛰는 순간의 디폴트", 14800, 19)

    # 11 틱의 출처: 8253
    p = d.slide("틱의 출처: 8253", K.S_CODE,
                "sched.c:46, 406-410 · sched.h:5 HZ=100 — 04회차 IDT 게이트 표의 실체")
    d.code_panel(p, "src/kernel/sched.c", 46, 46, 1100, 4400, 9900, 2500,
                 size=13, caption_extra="LATCH = 1193180/HZ = 11931")
    d.code_panel(p, "src/kernel/sched.c", 404, 410, 1100, 7200, 9900, 6300,
                 size=11, caption_extra="ltr/lldt · 8253 · 게이트 · PIC")
    d.table(p, 11600, 4400, [4600, 10200, 6400], [
        ["설정", "값 · 내용", "소스"],
        ["LATCH", "1193180/HZ = 11931", "sched.c:46"],
        ["채널 0 모드 3", "outb_p(0x36, 0x43) — binary·mode 3", "sched.c:406"],
        ["카운터", "LSB·MSB → 포트 0x40", "sched.c:407-408"],
        ["IDT 게이트", "set_intr_gate(0x20, &timer_interrupt)", "sched.c:409"],
        ["PIC 마스크", "IRQ 0 해제 — inb(0x21) & ~0x01", "sched.c:410"],
        ["주기", "HZ=100 → 10 ms마다 IRQ 0", "sched.h:5"],
    ], row_h=1250, size=13)
    d.banner(p, "8253이 10 ms마다 IRQ 0 — sched_init이 카운터와 게이트를 세팅한다 (04회차 게이트 표 재사용)", 14700, 18)

    # 12 _timer_interrupt 다시 읽기
    p = d.slide("_timer_interrupt 다시 읽기", K.S_CODE,
                "system_call.s:176-197 — 04회차에서 call _do_timer 직전까지 봤다, 오늘은 그 뒤")
    d.code_panel(p, "src/kernel/system_call.s", 176, 189, 1100, 4400, 15200,
                 8800, size=9, caption_extra="진입 — push · 세그먼트 · jiffies++")
    d.code_panel(p, "src/kernel/system_call.s", 190, 197, 16900, 4400, 15700,
                 5900, size=9, caption_extra="EOI · cpl · call · 복귀")
    hi = [("189  incl _jiffies — jiffies는 커널 전체에서 여기서만 증가", K.TEAL),
          ("192-194  CS(%esp)&3 = CPL → push (0=커널, 3=사용자)", K.ORANGE),
          ("195  call _do_timer — 인자 cpl 한 개", K.PAPER),
          ("197  jmp ret_from_sys_call — 복귀 경로가 시스템 콜과 같다", K.PAPER)]
    for i, (t, col) in enumerate(hi):
        nbox(d, p, 16900, 11100 + i * 840, 15700, 760, t, None, col,
             K.INK, s1=12)
    d.banner(p, "같은 ret_from_sys_call — 이 복귀 경로가 (뒤에서 일어날) 스케줄 뒤 복귀를 가능하게 한다", 14700, 18)

    # 13 do_timer (1): 회계
    p = d.slide("do_timer (1): 회계", K.S_CODE,
                "sched.c:305-317 — beepcount(310-312)는 삐 소리 끄기, 본론은 cpl에 따른 utime/stime")
    d.code_panel(p, "src/kernel/sched.c", 305, 317, 1100, 4400, 19700, 9000,
                 size=10, caption_extra="do_timer(long cpl)")
    nbox(d, p, 22000, 4400, 10500, 1200, "사용자 모드 중 틱 — cpl=3", None,
         K.TEAL, s1=14)
    arrow(d, p, 26400, 5700, "↓", 20)
    nbox(d, p, 22000, 6500, 10500, 1100, "current->utime++ (315)", None,
         K.PAPER, K.INK, s1=13)
    nbox(d, p, 22000, 8200, 10500, 1200, "커널 모드 중 틱 — cpl=0", None,
         K.ORANGE, s1=14)
    arrow(d, p, 26400, 9500, "↓", 20)
    nbox(d, p, 22000, 10300, 10500, 1100, "current->stime++ (317)", None,
         K.PAPER, K.INK, s1=13)
    para(d, p, 22000, 11800, 10500, 2600,
         "틱이 온 순간 '누구의 시간인가'를 cpl 인자 하나로 가른다.", 14)
    d.banner(p, "틱 한 번 = 회계 — 사용자 모드 틱은 utime, 커널 모드 틱은 stime (current의 시간)", 14700, 18)

    # 14 do_timer (2): 타이머 리스트
    p = d.slide("do_timer (2): 타이머 리스트", K.S_CODE,
                "sched.c:319-331 · add_timer은 272-303 — 상대값 정렬 리스트, 플로피 모터용 (플로피는 11회차)")
    d.code_panel(p, "src/kernel/sched.c", 319, 331, 1100, 4400, 19700, 9000,
                 size=10, caption_extra="next_timer->jiffies-- · 만료 fn() 호출")
    nbox(d, p, 22000, 4400, 2400, 1200, "*next_timer", None, K.PAPER, s1=12)
    d.text(p, 24500, 4750, 700, 600, "→", 18, K.TEAL, True)
    nbox(d, p, 25300, 4400, 3300, 1200, "jiffies=2", "fn()", K.PAPER,
         s1=13, s2=11)
    d.text(p, 28700, 4750, 700, 600, "→", 18, K.TEAL, True)
    nbox(d, p, 29500, 4400, 3000, 1200, "jiffies=3", "fn → …", K.PAPER,
         s1=13, s2=11)
    para(d, p, 22000, 6100, 10500, 8300,
         "리스트 항목은 상대값 — 매 틱 머리의 jiffies를 1 깎고(320), 0 이하가 되면 "
         "fn()을 부르고 리스트에서 뺀다(321-328).\n\n"
         "add_timer(272-303) — 새 항목을 정렬된 자리에 끼워 넣으며 앞 항목에서 "
         "남은 틱을 차감해 저장한다.\n\n"
         "사용처는 플로피 모터 타이먍 등 — 'do_timer가 호출하는 부가 리스트'까지만 "
         "오늘은 본다(§8).", 14)
    d.banner(p, "do_timer의 부가 리스트 — 상대 카운트를 1씩 깎아 만료에 fn() (플로피 모터용)", 14700, 18)

    # 15 do_timer (3): counter와 cpl 조건
    p = d.slide("do_timer (3): counter와 cpl 조건", K.S_CODE,
                "sched.c:332-335 — 네 줄이 태스크 전환의 문지방 · 학습 목표 3의 핵심 조건")
    d.code_panel(p, "src/kernel/sched.c", 332, 335, 1100, 4400, 19700, 4800,
                 size=14, caption_extra="네 줄 전체")
    nbox(d, p, 22000, 4400, 10500, 1000, "counter-- > 0 → return", "계속 실행",
         K.PAPER, s1=13, s2=11)
    nbox(d, p, 22000, 5650, 10500, 1000, "counter = 0 · cpl = 0 → return",
         "커널 모드 — 그래도 계속", K.ORANGE, s1=13, s2=11)
    nbox(d, p, 22000, 6900, 10500, 1000, "counter = 0 · cpl ≠ 0",
         "schedule() 호출", K.TEAL, s1=13, s2=11)
    d.outline(p, 1100, 9700, 19700, 3600, K.ORANGE, 120)
    d.text(p, 1400, 10050, 19000, 1700,
           "커널 모드에서 틱이 오면 counter가 0이 돼도\nschedule()을 부르지 않는다",
           19, K.ORANGE, True)
    d.text(p, 1400, 12350, 19000, 800,
           "→ 0.11 커널 코드는 (타이머에 의해) 선점되지 않는다 — 비선점(non-preemptive) 커널",
           13, K.PAPER)
    para(d, p, 22000, 8300, 10500, 5900,
         "counter를 0으로 못 박는 333 — '이미 0' 상태를 남겨 다음 기회(시스템 콜 끝 "
         "95-100)에 스케줄되게 한다.\n\n"
         "cpl은 _timer_interrupt가 push한 값(192-194).", 14)
    d.banner(p, "if (!cpl) return; — 이 한 준이 '커널 모드 중에는 태스크가 안 바뀐다'를 만든다", 14700, 18)

    # 16 틱 한 번의 데이터 변화
    p = d.slide("틱 한 번의 데이터 변화", K.S_BG,
                "system_call.s:189 · sched.c:314-317, 332-335 — 빈 칸은 시연 A(35-36장)에서 실제 값으로 채운다")
    d.table(p, 1100, 4500, [7400, 6300, 6300, 11500], [
        ["데이터", "틱 전", "틱 후", "바꾸는 곳 (파일:줄)"],
        ["jiffies", "J", "J + 1", "system_call.s:189 — incl _jiffies"],
        ["current->counter", "c", "c − 1 (0이면 0으로)", "sched.c:332-333"],
        ["current->utime / stime", "u / s", "+1 (cpl로 갈림)", "sched.c:314-317"],
        ["next_timer->jiffies", "t", "t − 1 (≤0 → fn())", "sched.c:320"],
        ["current (태스크 자체)", "(보통) 그대로", "counter 0 · cpl≠0일 때만", "sched.c:335 → schedule()"],
    ], row_h=1200, size=14)
    para(d, p, 1100, 13100, 31500, 1500,
         "표의 J·c·u 값은 실행마다 다르다 — 시연 A(슬라이드 35-36)에서 display로 관찰한 "
         "값으로 이 표를 채운다. 태스크가 바뀌는 것은 마지막 행 조건일 때뿐이다.", 15)
    d.banner(p, "틱 한 번이 건드리는 데이터는 네 가지 — 태스크 교체는 'counter 0 + 사용자 모드'일 때만", 14700, 18)

    # 17 시스템 콜 끝에서도 스케줄 검사
    p = d.slide("시스템 콜 끝에서도 스케줄 검사", K.S_CODE,
                "system_call.s:95-100 · reschedule 76-78 — schedule()의 ret이 곧 ret_from_sys_call로 간다")
    d.code_panel(p, "src/kernel/system_call.s", 95, 100, 1100, 4400, 15200,
                 5800, size=12, caption_extra="state≠0 또는 counter==0 → reschedule")
    d.code_panel(p, "src/kernel/system_call.s", 76, 78, 1100, 10500, 15200,
                 3900, size=12, caption_extra="reschedule")
    steps = ["① cmpl $0,state(%eax) — 시스템 콜 안에서 잠들었다 깨어났는가 (97-98)",
             "② cmpl $0,counter(%eax) — 시간을 다 썼는가 (99-100)",
             "③ reschedule — pushl $ret_from_sys_call; jmp _schedule (77-78)",
             "④ schedule()의 ret → push해 둔 ret_from_sys_call으로 복귀"]
    for i, t in enumerate(steps):
        col = K.ORANGE if i == 2 else K.PAPER
        nbox(d, p, 16900, 4400 + i * 1750, 15700, 1500, t, None, col,
             K.INK, s1=13)
    d.text(p, 17400, 11550, 14500, 600,
           "스택 (위 = push 직후)", 12, K.TEAL, True)
    nbox(d, p, 17400, 12200, 14500, 900, "ret_from_sys_call — 반환 주소",
         None, K.ORANGE, K.INK, s1=13)
    nbox(d, p, 17400, 13200, 14500, 900, "schedule()의 ret이 여기를 팝", None,
         None, K.MUTED, s1=12)
    d.banner(p, "시스템 콜 복귀 직전의 두 번째 검사 — 커널 모드로 놓친 전환 기회를 여기서 만난다", 14800, 19)

    # ── 비교 18–19 ────────────────────────────────────────────
    # 18 네 경로 카드
    p = d.slide("비교 (1): schedule()이 불리는 네 경로 — 사례와 소스", K.S_CMP,
                "sched.c:332-335, 162, 178, 147 · system_call.s:95-100 · exit.c:133, 188, 29")
    cards = [
        ("a · 타이머 틱",
         "do_timer → schedule()\nsched.c:332-335\n\n조건: counter==0 그리고\ncpl≠0 (사용자 모드)\n\nIRQ 0 핸들러 안에서"),
        ("b · 시스템 콜 복귀 직전",
         "reschedule\nsystem_call.s:95-100\n\n조건: state≠0 또는\ncounter==0\n\npushl $ret_from_sys_call\n(76-78)"),
        ("c · 태스크 자발 호출",
         "sleep_on — sched.c:162\ninterruptible_sleep_on — 178\nsys_pause — 147\ndo_exit — exit.c:133\nsys_waitpid — exit.c:188\n\n잠들기 직전에 스스로"),
        ("d · release()",
         "release → schedule()\nexit.c:29\n\nZOMBIE를 거둔 뒤\n빈 task[] 슬롯 정리 후\n(소멸 경로 — 20-33)"),
    ]
    gap, total = 600, 31500
    width = (total - gap * 3) // 4
    for i, (title, body) in enumerate(cards):
        x = 1100 + i * (width + gap)
        d.shape(p, x, 4700, width, 8700, K.PAPER)
        d.shape(p, x, 4700, width, 150, K.TEAL if i % 2 == 0 else K.ORANGE)
        d.text(p, x + 550, 5050, width - 1100, 1500, title, 19, K.INK, True)
        d.text(p, x + 550, 6600, width - 1100, 6600,
               wrap_kr(body, (width - 1100) * 1.1, 13), 13, K.INK)
    d.banner(p, "schedule()은 타이머 인터럽트 핸들러의 전용이 아니다 — 네 경로 (a)–(d)가 부른다 (§8)", 14800, 19)

    # 19 네 경로 비교표
    p = d.slide("비교 (2): 네 경로 비교표 — 누가·어떤 상태·어디로", K.S_CMP,
                "축 3개 — 선점 정책·CPU 모드와 섞지 않는다 (계획 §1 비교 범위)")
    d.table(p, 1100, 4600, [3400, 7600, 8700, 11800], [
        ["경로", "누가 부르는가", "호출 직전 current->state", "복귀 지점"],
        ["a", "인터럽트 핸들러 — do_timer(sched.c:335)", "0 (RUNNING)",
         "ret_from_sys_call — system_call.s:197 jmp"],
        ["b", "시스템 콜 복귀부 — reschedule(95-100)", "0, 또는 잠들었다 깨어나 ≠0",
         "push해 둔 $ret_from_sys_call (76-78)"],
        ["c", "커널 함수(자발) — sleep_on 등", "1·2·3 — 호출 직전 상태 전환 후",
         "schedule() 다음 줄 — 잠든 태스크는 깨어난 뒤에 도달"],
        ["d", "커널 함수 — release(exit.c:29)", "3 — 거두어 지는 태스크",
         "살아 있는 호출자(sys_waitpid)로 반환"],
    ], row_h=1350, size=13)
    para(d, p, 1100, 12000, 31500, 2400,
         "a·b는 '인터럽트/시스템 콜 껍데기 안'에서, c·d는 '커널 함수 호출'로 — 복귀 지점의 "
         "차이가 표의 핵심이다. 전환이 일어나면 이전 태스크는 자신의 차례(깨어남)에 "
         "같은 지점으로 돌아온다.", 15)
    d.banner(p, "같은 schedule() — 부르는 자리에 따라 복귀 지점이 다르다", 14800, 19)

    # ── 코드 20–22 ────────────────────────────────────────────
    # 20 schedule() (1): 깨우기
    p = d.slide("schedule() (1): 깨우기", K.S_CODE,
                "sched.c:104-120 — 역순 순회(&LAST_TASK → &FIRST_TASK, task 0 제외) · _S/_BLOCKABLE은 23-24")
    d.code_panel(p, "src/kernel/sched.c", 104, 120, 1100, 4400, 19700, 10000,
                 size=9, caption_extra="alarm 만료 → SIGALRM · 시그널로 깨우기")
    para(d, p, 22000, 4400, 10500, 10000,
         "① alarm이 jiffies를 지났으면 SIGALRM 비트를 올린다(113-115) — alarm은 "
         "sys_alarm이 jiffies+HZ*초로 설정(344).\n\n"
         "② signal & ~(_BLOCKABLE & blocked)가 있고 INTERRUPTIBLE이면 "
         "RUNNING으로(117-119).\n\n"
         "_S(nr)=(1<<((nr)-1)), _BLOCKABLE=~(SIGKILL|SIGSTOP) — sched.c:23-24.\n\n"
         "state=2(UNINTERRUPTIBLE)는 이 문으로 못 깬다 — 깨우는 주체는 wake_up(26장).",
         14)
    d.banner(p, "schedule() 전반 = 깨우기 — 시그널로 깰 수 있는 잠은 INTERRUPTIBLE뿐이다", 14800, 19)

    # 21 schedule() (2): 고르기
    p = d.slide("schedule() (2): 고르기", K.S_CODE,
                "sched.c:124-135 — c=-1, next=0 기본값 · RUNNING이고 counter>c → next")
    d.code_panel(p, "src/kernel/sched.c", 124, 135, 1100, 4400, 19700, 8500,
                 size=9, caption_extra="while(1) 안의 역순 스캔")
    scan = ["task[63]", "task[62]", "…", "task[2]", "task[1]"]
    bx = 22000
    for i, t in enumerate(scan):
        w = 1200 if t != "…" else 900
        nbox(d, p, bx, 4400, w, 1200, t, None, K.PAPER, K.INK, s1=11)
        bx += w + 300
    d.text(p, 22000, 5850, 10500, 500, "◀— 역순 스캔 (p = &task[NR_TASKS] … --p)",
           13, K.ORANGE, True)
    para(d, p, 22000, 6600, 10500, 7700,
         ">(strict) — 동률이면 먼저 만난 쪽, 즉 인덱스 큰 태스크가 next에 남는다.\n\n"
         "next=0 기본값(126) — 아무도 조건을 못 맞추면 task 0.\n\n"
         "if (c) break; — c≠0이면 고르기 끝. c==0은 '모두 counter 0' → 재충전하고 "
         "다시 한 바퀴 스캔(다음 장).", 14)
    d.banner(p, "RUNNING이면서 counter 최대 — c==-1에서 시작해 역순으로 갱신, task 0은 루프 밖이다", 14800, 19)

    # 22 schedule() (3): 재충전 식
    p = d.slide("schedule() (3): 재충전 식", K.S_CODE,
                "sched.c:136-141 — for 문에 상태 검사 없음: 잠든 태스크도 재충전된다 (§8)")
    d.code_panel(p, "src/kernel/sched.c", 136, 141, 1100, 4400, 19700, 6200,
                 size=10, caption_extra="counter = (counter>>1) + priority — 전 태스크")
    d.table(p, 1100, 11000, [5200, 3600, 3600, 3600, 3700], [
        ["태스크", "priority", "재충전 전 counter", "counter >> 1", "새 counter"],
        ["A — 방금 0까지 실행", "15", "0", "0", "15"],
        ["B — 도중 깨어남", "15", "3", "1", "16"],
        ["C — 계속 잠듦", "15", "8", "4", "19"],
    ], row_h=700, size=13)
    para(d, p, 22000, 4400, 10500, 9800,
         "손계산 — priority 15, counter 0/3/8인 세 태스크는 15/16/19가 된다.\n\n"
         "오래 잠들어 counter가 남은 태스크가 깨어날 때 유리하다 — I/O 바운드 우대.\n\n"
         "이어서 switch_to(next) — 141. 매크로는 29-30장.", 15)
    d.banner(p, "counter = counter>>1 + priority — 재충전은 상태 무관, 'RUNNING만'이 아니다", 14800, 19)

    # ── 상태도 23–25 ──────────────────────────────────────────
    # 23 다섯 상태와 current
    p = d.slide("상태 변화도 (1): 다섯 상태와 current", K.S_STATE,
                "sched.h:19-23 — 값 0·1·2·3·4 · '실행 중'은 state 값이 아니라 current 표기다 (§8)")
    ellipse(d, p, 1300, 4400, 5700, 3900, fill=K.TEAL, edge=K.TEAL)
    center = uno.Enum("com.sun.star.drawing.TextHorizontalAdjust", "CENTER")
    sh = d.text(p, 1300, 5100, 5700, 800, "RUNNING (0)", 19, K.INK, True)
    sh.TextHorizontalAdjust = center
    badge(d, p, 1750, 6100, 4800, "current(실행 중) — CPU 점유", K.ORANGE,
          750, 12)
    sh = d.text(p, 1300, 7100, 5700, 700, "RUNNING 여럿 · current 하나", 10,
                K.INK)
    sh.TextHorizontalAdjust = center
    ellipse(d, p, 7800, 4300, 11700, 2800, edge=K.TEAL)
    etext(d, p, 7800, 4950, 11700, "INTERRUPTIBLE (1)", 15, K.TEAL,
          "시그널로 깨울 수 있는 잠")
    ellipse(d, p, 20300, 4300, 11700, 2800, edge=K.TEAL)
    etext(d, p, 20300, 4950, 11700, "UNINTERRUPTIBLE (2)", 15, K.TEAL,
          "이벤트 완료까지 안 깨는 잠")
    ellipse(d, p, 7800, 7500, 11700, 2800, edge=K.MUTED)
    etext(d, p, 7800, 8150, 11700, "ZOMBIE (3)", 15, K.MUTED,
          "exit_code 남기고 거두기 대기")
    ellipse(d, p, 20300, 7500, 11700, 2800, edge=K.MUTED, dash=True)
    etext(d, p, 20300, 8150, 11700, "STOPPED (4)", 15, K.MUTED,
          "진입 코드 없음 — 0.11 미구현")
    d.code_panel(p, "src/include/linux/sched.h", 19, 23, 1100, 10500, 19700,
                 3900, size=12, caption_extra="다섯 값의 정의")
    para(d, p, 22000, 10500, 10500, 3900,
         "STOPPED는 정의(sched.h:23)와 sys_waitpid의 case(exit.c:166)만 있다.\n\n"
         "'실행 중' 표기는 RUNNING 안의 별도 자리 — state 어디에도 '실행 중' 값은 없다.",
         13)
    d.banner(p, "state = 0·1·2·3·4 — '실행 중'은 state가 아니라 current가 가리키는 태스크다", 14800, 19)

    # 24 전환 원인과 소스
    p = d.slide("상태 변화도 (2): 전환 원인과 소스", K.S_STATE,
                "sched.c:146, 177, 161, 191, 117-119, 164, 180 · exit.c:187, 130, 176, 20-33 · fork.c:82, 131")
    ellipse(d, p, 1100, 4800, 4700, 2800, edge=K.TEAL)
    etext(d, p, 1100, 5750, 4700, "INTERRUPTIBLE", 12, K.TEAL, "(1)")
    ellipse(d, p, 1100, 10600, 4700, 2800, edge=K.TEAL)
    etext(d, p, 1100, 11550, 4700, "UNINTERRUPTIBLE", 12, K.TEAL, "(2)")
    ellipse(d, p, 13900, 6700, 4600, 3500, fill=K.TEAL, edge=K.TEAL)
    etext(d, p, 13900, 7750, 4600, "RUNNING (0)", 16, K.INK,
          "current = 이 태스크", 11, K.INK)
    ellipse(d, p, 26400, 6800, 3900, 2900, edge=K.MUTED)
    etext(d, p, 26400, 7800, 3900, "ZOMBIE (3)", 14, K.MUTED,
          "exit_code 저장")
    nbox(d, p, 26400, 11400, 3900, 2900, "소멸",
         "task[i]=NULL\nfree_page · release\n(exit.c:20-33)",
         None, K.MUTED, K.MUTED, K.MUTED, s1=14, s2=9)
    badge(d, p, 5900, 4600, 2000, "◀ 잠듦", K.TEAL, 650, 11)
    para(d, p, 8000, 4600, 5700, 1750,
         "sys_pause(sched.c:146) · interruptible_sleep_on(:177) · "
         "sys_waitpid(exit.c:187)", 10, K.TEAL, True)
    badge(d, p, 5900, 6500, 2000, "▶ 깨어남", K.ORANGE, 650, 11)
    para(d, p, 8000, 6500, 5700, 1750,
         "wake_up(:191) · schedule 117-119(시그널) · interruptible_sleep_on 180",
         10, K.ORANGE, True)
    badge(d, p, 5900, 10400, 2000, "◀ 잠듦", K.TEAL, 650, 11)
    para(d, p, 8000, 10400, 5700, 1750,
         "sleep_on(sched.c:161) · copy_process 생성 중(fork.c:82)", 10, K.TEAL,
         True)
    badge(d, p, 5900, 12300, 2000, "▶ 깨어남", K.ORANGE, 650, 11)
    para(d, p, 8000, 12300, 5700, 1750,
         "wake_up(:191) · sleep_on 164(연쇄) · copy_process 마지막(fork.c:131)",
         10, K.ORANGE, True)
    para(d, p, 18700, 7300, 6600, 1500,
         "do_exit(exit.c:130) — state=3 · exit_code 저장(131)", 11, K.MUTED,
         True)
    arrow(d, p, 25400, 8000, "→", 24, K.MUTED)
    arrow(d, p, 28100, 9850, "↓", 22, K.MUTED)
    para(d, p, 18700, 10900, 6600, 1100,
         "sys_waitpid → release(exit.c:176) — 좀비 거두기", 11, K.MUTED, True)
    para(d, p, 6300, 14200, 12500, 500,
         "STOPPED(4)로 들어가는 전환은 0.11에 없다 — 정의와 waitpid case뿐(23장).",
         12, K.MUTED)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)
    d.banner(p, "모든 전환은 함수 안의 대입 한 줄 — 원인과 줄 번호로 짚는다", 14800, 19)

    # 25 변경 데이터와 유지 조건
    p = d.slide("상태 변화도 (3): 변경 데이터와 유지 조건", K.S_STATE,
                "sched.c:124-140, 136-139 · exit.c:130, 20-33 — 호출 순서도(18-19장)와 다른 그림임을 명시")
    d.table(p, 1100, 4500, [4300, 11000, 8200, 8000], [
        ["상태", "상태에서 실제로 바뀌는 데이터", "유지 조건", "소스"],
        ["RUNNING (0)", "counter — current일 때만 매 틱 감소(332) · utime/stime +1(314-317)",
         "schedule()은 state==0만 고른다(132)", "sched.c:124-140"],
        ["INTERRUPTIBLE (1)", "state=1(146·177·exit.c:187) · 대기 큐 *p 연결(159-160)",
         "시그널(117-119)·wake_up(191)로 탈출", "sched.c:151-194"],
        ["UNINTERRUPTIBLE (2)", "state=2(161) · 대기 큐 *p 연결",
         "이벤트 wake_up까지만 — 시그널 무시", "sched.c:151-165"],
        ["ZOMBIE (3)", "state=3 · exit_code 저장(130-131)",
         "sys_waitpid→release 전까지 task[] 슬롯 유지", "exit.c:130·176·20-33"],
        ["STOPPED (4)", "(없음 — 진입 코드 없음)", "waitpid의 case뿐(166)",
         "sched.h:23·exit.c:166"],
    ], row_h=1400, size=13)
    para(d, p, 1100, 13100, 31500, 1500,
         "재충전(136-139)은 상태 무관 — 잠든 태스크의 counter도 오른다. "
         "이 표는 상태별 데이터 정리이지 호출 경로 비교(18-19장)가 아니다.", 14)
    d.banner(p, "schedule()은 state==0만 고른다 — 나머지 상태는 '기다리는 자리'일 뿐", 14800, 19)

    # ── 코드 26–27 ────────────────────────────────────────────
    # 26 sleep_on과 wake_up
    p = d.slide("sleep_on과 wake_up", K.S_CODE,
                "sched.c:151-165, 188-194 — tmp=*p; *p=current; (159-160) · 대기 큐는 07(용어)에 이어 실체")
    d.code_panel(p, "src/kernel/sched.c", 151, 165, 1100, 4400, 15200, 10000,
                 size=10, caption_extra="sleep_on — 대기 큐 이어 걸기")
    d.code_panel(p, "src/kernel/sched.c", 188, 194, 16900, 4400, 15700, 5700,
                 size=10, caption_extra="wake_up — 머리 하나만 깨운다")
    d.text(p, 16900, 10400, 15700, 600,
           "bh->b_wait 대기 큐 — 세 태스크가 잠든 모양", 13, K.TEAL, True)
    nbox(d, p, 16900, 11100, 2300, 2100, "*p", "(bh->b_wait)\n= task C", K.PAPER,
         s1=13, s2=10)
    d.text(p, 19300, 11800, 700, 600, ">", 20, K.TEAL, True)
    nbox(d, p, 20100, 11100, 3700, 2100, "task C — 머리",
         "스택의\ntmp → task B", K.PAPER, s1=13, s2=10)
    d.text(p, 23900, 11800, 700, 600, ">", 20, K.TEAL, True)
    nbox(d, p, 24700, 11100, 3700, 2100, "task B", "tmp → task A", K.PAPER,
         s1=13, s2=10)
    d.text(p, 28500, 11800, 700, 600, ">", 20, K.TEAL, True)
    nbox(d, p, 29300, 11100, 3300, 2100, "task A", "tmp = NULL", K.PAPER,
         s1=13, s2=10)
    para(d, p, 16900, 13500, 15700, 900,
         "wake_up은 머리(C)만 깨우고(191) — 깨어난 C가 tmp->state=0(164)으로 B를 깨운다: 연쇄",
         13, K.ORANGE, True)
    d.banner(p, "대기 큐 = 포인터 하나 + 각자 스택의 tmp — 커널에 별도 큐 자료구조가 없다", 14800, 19)

    # 27 interruptible_sleep_on
    p = d.slide("interruptible_sleep_on", K.S_CODE,
                "sched.c:167-186 · 깨움 짝은 schedule 117-119 · 사용처 tty_io.c:126, 136 (키 입력 대기)")
    d.code_panel(p, "src/kernel/sched.c", 167, 177, 1100, 4400, 15200, 7900,
                 size=10, caption_extra="진입 — *p=current")
    d.code_panel(p, "src/kernel/sched.c", 178, 186, 16900, 4400, 15700, 6800,
                 size=10, caption_extra="repeat — 머리 검사")
    nbox(d, p, 1100, 12600, 6600, 1800, "schedule()에서 깨어남", "잠든 원인·시그널 모두 가능",
         K.PAPER, s1=13, s2=10)
    d.text(p, 7900, 13200, 700, 600, ">", 20, K.TEAL, True)
    nbox(d, p, 8800, 12600, 6800, 1800, "*p != current ?", "내가 머리인가 (179)",
         K.PAPER, s1=13, s2=10)
    d.text(p, 15700, 13200, 700, 600, ">", 20, K.TEAL, True)
    nbox(d, p, 16600, 12600, 7600, 1800, "예 — 머리를 깨우고 repeat",
         "(**p).state=0; goto repeat (180-181)", K.ORANGE, s1=13, s2=10)
    nbox(d, p, 24600, 12600, 8000, 1800, "아니 — *p=NULL; tmp 깨움; 반환",
         "정상 복귀 (183-185)", K.TEAL, s1=13, s2=10)
    para(d, p, 16900, 11450, 15700, 900,
         "깨어났는데 머리가 아니면 머리를 깨우고 다시 잠든다 — 순서를 지킨다.", 13)
    d.banner(p, "시그널로 깨어날 수 있는 잠 — 그래서 schedule()의 깨우기(117-119)와 짝을 이룬다", 14800, 19)

    # ── 비교 28 ───────────────────────────────────────────────
    # 28 sleep_on vs interruptible_sleep_on
    p = d.slide("비교: sleep_on vs interruptible_sleep_on", K.S_CMP,
                "sched.c:151-165, 167-186 · 사용처 buffer.c:40, 225 / tty_io.c:126, 136")
    d.table(p, 1100, 4600, [6800, 11900, 12800], [
        ["축", "sleep_on (151-165)", "interruptible_sleep_on (167-186)"],
        ["설정 상태", "TASK_UNINTERRUPTIBLE = 2 (161)", "TASK_INTERRUPTIBLE = 1 (177)"],
        ["시그널로 깨는가", "아니오 — 117-119의 깨우기 대상 밖",
         "예 — 117-119에서 RUNNING으로 (짝)"],
        ["깨어난 뒤 재검사", "없음 — tmp만 깨우고 반환 (163-164)",
         "repeat — 내가 머리인지 재검사 (179-182)"],
        ["사용처", "buffer.c:40, 225 등 — 디스크 I/O 대기",
         "tty_io.c:126, 136 — 키 입력 대기"],
    ], row_h=1500, size=14)
    para(d, p, 1100, 12400, 31500, 2000,
         "같은 '포인터 하나 대기 큐'를 쓰지만 깨어나는 규칙이 다르다 — 시그널(10회차)을 "
         "받을 수 있느냐가 갈림이다.", 15)
    d.banner(p, "sleep_on은 이벤트만, interruptible_sleep_on은 시그널도 — 두 잠의 차이는 한 비트(state 2 vs 1)", 14800, 19)

    # ── 코드 29–30 ────────────────────────────────────────────
    # 29 switch_to (1)
    p = d.slide("switch_to(n) (1): 매크로 전문과 같은 태스크 검사", K.S_CODE,
                "sched.h:171-184 — 전문 · _TSS(n) 계산(149-164)은 슬라이드 32에서 다시 본다")
    d.code_panel(p, "src/include/linux/sched.h", 171, 184, 1100, 4400, 19700,
                 8800, size=9, caption_extra="매크로 전문 — 단계 ①–⑤")
    para(d, p, 22000, 4400, 10500, 9800,
         "① cmpl %%ecx,_current; je 1f — 같은 태스크면 아무것도 안 한다.\n\n"
         "② movw %%dx,%1 — __tmp.b의 하위 16비트에 _TSS(n) 선택자.\n\n"
         "③ xchgl %%ecx,_current — current 갱신.\n\n"
         "④ ljmp %0 — far jump = TSS 전환 (다음 장).\n\n"
         "⑤ 마지막 FPU 사용자 검사 — jne 1f / clts.\n\n"
         "인자: d = _TSS(n), c = task[n] (183).", 14)
    d.banner(p, "같은 태스크면 je 1f로 그냥 지나간다 — 전환 비용은 ljmp 한 번이 전부", 14800, 19)

    # 30 switch_to (2)
    p = d.slide("switch_to(n) (2): current 갱신과 ljmp·clts", K.S_CODE,
                "sched.h:173-180 발췌 — __tmp의 오프셋 필드(a)는 설정하지 않는다: 이해 확인 문항 4(47장)")
    d.code_panel(p, "src/include/linux/sched.h", 173, 180, 1100, 4400, 19700,
                 7600, size=13, caption_extra="xchgl · ljmp · clts")
    d.text(p, 22000, 4400, 10500, 600, "__tmp 구조 (sched.h:172)", 14, K.TEAL,
           True)
    nbox(d, p, 22500, 5050, 9500, 1600, "a — 4바이트 오프셋",
         "설정하지 않는다 — CPU가 무시", None, K.MUTED, K.MUTED, K.MUTED,
         s1=13, s2=10)
    nbox(d, p, 22500, 6900, 9500, 1600, "b — 하위 2바이트 = 선택자",
         "movw %%dx,%1 — _TSS(n)", K.TEAL, s1=13, s2=10)
    arrow(d, p, 26600, 6680, "↓", 20)
    nbox(d, p, 22500, 8900, 9500, 1650, "ljmp %0 — 6바이트 far 포인터",
         "선택자가 TSS 설명자 → 오프셋 무시, TSS 전환", K.ORANGE, s1=13, s2=10)
    arrow(d, p, 26600, 8530, "↓", 20)
    para(d, p, 22500, 10800, 9500, 3500,
         "새 EIP는 목적지 TSS의 eip 필드에서 온다 — 그래서 a를 설정할 이유가 없다.\n\n"
         "clts — 새 태스크가 마지막 FPU 사용자면 TS 플래그 클리어(178-180).",
         12)
    para(d, p, 1100, 12300, 19700, 1900,
         "xchgl %%ecx,_current(176) — 전환과 동시에 current가 새 태스크를 가리킨다. "
         "이 순서(ljmp 앞)라야 전환 직후의 current가 새 태스크다.", 14)
    d.banner(p, "ljmp %0 — __tmp에서 유효한 것은 선택자뿐: far jump 한 번이 TSS 전환이다", 14800, 19)

    # 31 ljmp가 TSS로 가면 CPU가 하는 일
    p = d.slide("ljmp가 TSS로 가면 CPU가 하는 일", K.S_BG,
                "sched.h:51-76, 128, 171-184 — 저장·복원은 코드가 아니라 CPU가 한다 (§8)")
    nbox(d, p, 1100, 4500, 10200, 6300, "이전 태스크의 TSS — ① 저장",
         "EIP = ljmp 다음 줄\neflags · eax–edi · esp·ebp·esi·edi\nes–gs · ldt · cr3 · esp0/ss0 전부",
         K.PAPER, s1=16, s2=12)
    nbox(d, p, 20600, 4500, 10200, 6300, "새 태스크의 TSS — ② 로드",
         "레지스터 전부 복원\nesp/ss = 커널 스택 교체\neip = 그 태스크가 멈춘 줄",
         K.PAPER, s1=16, s2=12)
    nbox(d, p, 12300, 4900, 7300, 2200, "ljmp → CPU의 TSS 전환",
         "한 명령 — 소스 코드 없음", K.ORANGE, s1=15, s2=11)
    nbox(d, p, 12300, 7600, 7300, 900, "TR ← 새 TSS 선택자", None, None,
         K.MUTED, s1=12)
    nbox(d, p, 12300, 8700, 7300, 900, "LDTR ← tss.ldt", None, None,
         K.MUTED, s1=12)
    nbox(d, p, 12300, 9800, 7300, 1500, "CR3 ← tss.cr3",
         "0.11은 모두 &pg_dir (sched.h:128)", None, K.MUTED, K.MUTED,
         K.MUTED, s1=12, s2=9)
    para(d, p, 1100, 11400, 31500, 2800,
         "커널 스택도 바뀐다 — ss/esp 복원(04회차 프레임의 반대 방향). 다시 선택되면 "
         "저장된 EIP(= ljmp 다음 줄)부터 재개한다.\n"
         "cr3은 태스크마다 다르지 않다 — 0.11은 pg_dir 하나뿐이고 주소 분리는 LDT "
         "base가 한다(06·07회차, §8).", 15)
    d.banner(p, "레지스터 저장·복원은 switch_to의 코드가 아니라 CPU가 TSS 한 덩어리로 한다", 14800, 19)

    # 32 sched_init
    p = d.slide("sched_init: TSS/LDT 설명자와 ltr", K.S_CODE,
                "sched.c:385-412 · _TSS(n)=(n<<4)+(4<<3) — sched.h:155 · 403 NT 클리어는 iret 보호")
    d.code_panel(p, "src/kernel/sched.c", 385, 401, 1100, 4400, 15200, 9300,
                 size=8, caption_extra="392-393 task0 TSS/LDT · 394-401 나머지 63슬롯 0")
    d.code_panel(p, "src/kernel/sched.c", 402, 412, 16900, 4400, 15700, 7300,
                 size=9, caption_extra="NT 클리어 · ltr/lldt · 8253 · 게이트")
    d.text(p, 16900, 11900, 15700, 600, "GDT — TSS/LDT 슬롯 (02회차 그림 골격)",
           13, K.TEAL, True)
    gdt = [("0", "null", False), ("1", "cs", False), ("2", "ds", False),
           ("3", "syscall", False), ("4", "TSS0 ★", True), ("5", "LDT0 ★", True),
           ("6", "TSS1", False), ("7", "LDT1", False)]
    for i, (num, label, hot) in enumerate(gdt):
        x = 16900 + i * 1950
        nbox(d, p, x, 12600, 1850, 1600, num, label,
             K.TEAL if hot else None, K.INK if hot else K.MUTED,
             None if hot else K.MUTED, s1=12, s2=9)
    para(d, p, 1100, 13850, 15200, 700,
         "_TSS(n) = (n<<4)+(4<<3) — sched.h:155 · 403 NT 클리어: iret가 태스크 복귀로 해석되지 않게",
         12, K.MUTED)
    d.banner(p, "부팅 시 GDT에 TSS/LDT 슬롯 64쌍을 파두고 ltr(0)·lldt(0)로 시작한다", 14800, 19)

    # 33 커널 스택과 tss.esp0
    p = d.slide("커널 스택과 tss.esp0", K.S_CODE,
                "sched.h:128 · fork.c:93(06회차) · sched.c:53-72 — 09장 그림 재사용 + esp0 화살표")
    d.code_panel(p, "src/include/linux/sched.h", 128, 131, 1100, 4400, 19700,
                 3800, size=9, caption_extra="INIT_TASK tss — esp0·ss0=0x10·cr3=&pg_dir")
    d.code_panel(p, "src/kernel/fork.c", 93, 94, 1100, 8500, 19700, 3200,
                 size=12, caption_extra="copy_process — 06회차 예고")
    para(d, p, 1100, 12100, 19700, 2300,
         "04회차: int 0x80 진입 시 CPU가 TSS의 ss0(=0x10)·esp0를 읽어 커널 스택으로 "
         "바꾼다 — 그 값이 어디서 오는가가 오늘의 답.\n"
         "모든 태스크가 자기 페이지 끝을 커널 스택으로 쓴다.", 14)
    page_pic(d, p, 23300, 5000, 4200, 8300,
             "커널 스택\n\nesp0가 가리키는\n페이지 끝에서\n시작", "task_struct")
    badge(d, p, 23300, 4200, 4200, "esp0 = PAGE_SIZE + p", K.ORANGE, 620, 12)
    d.banner(p, "esp0 = PAGE_SIZE + (long)p — 태스크마다 커널 스택 = 자기 4 KiB 페이지의 끝", 14800, 19)

    # ── 시연 34–41 ────────────────────────────────────────────
    # 34 시연 환경
    p = d.slide("시연 환경", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB — 심볼명·줄 번호는 lab 기준(src와 다를 수 있음)")
    auto_pane(d, p, 1100, 4300, 16800, 10200, "lab/ — 환경 체크리스트",
              "# QEMU -s -S · 부팅 완료(셸 프롬프트)까지 진행\n"
              "(gdb) target remote :1234\n"
              "(gdb) c\n"
              "\n"
              "# 심볼명 확인 — lab 빌드 기준\n"
              "(gdb) info functions do_timer\n"
              "#   do_timer / _do_timer (_ 접두 유무)\n"
              "#   schedule · current · jiffies · task 도 확인\n"
              "\n"
              "# 타이머 중단점은 10 ms마다 걸린다\n"
              "#   → cond · ignore · display 미리 설정\n"
              "#   → 관찰 뒤 반드시 delete", start=13)
    para(d, p, 19000, 4300, 13500, 6400,
         "중단점이 틱마다 걸리므로 '설정 → 관찰 → delete' 순서를 미리 정해 둔다.\n\n"
         "시연 C(둘째 태스크 확보)용 게스트 명령 — sleep 류·백그라운드 루프가 "
         "lab 이미지에서 되는지 사전 확인(§11).\n\n"
         "QEMU gdbstub 제약 — info registers tr · watch current 미지원 시 "
         "대체 경로(39장).", 14)
    nbox(d, p, 19000, 11000, 13500, 3400, "실패 시",
         "materials/05-scheduling/captures/ 의 사전 캡처 5종으로 대체 — "
         "'기존 기록' 라벨 규칙(§5·§11)", None, K.MUTED, K.MUTED, K.MUTED,
         s1=15, s2=12)
    d.banner(p, "오늘 시연 A·B·C — 중단점 do_timer · schedule · ljmp 주소", 14800, 19)

    # 35 시연 A
    p = d.slide("시연 A: break do_timer — jiffies와 counter", K.S_DEMO,
                "sched.c:305-336 대응 · display 관찰 · 수치는 실행마다 다르다 (§8)")
    auto_pane(d, p, 1100, 4300, 19700, 10200, "GDB — 틱 연속 관찰",
              "(gdb) break do_timer\n"
              "(gdb) display jiffies\n"
              "(gdb) display current->pid\n"
              "(gdb) display current->counter\n"
              "(gdb) display/x *(long*)($esp+4)\n"
              "#    ↑ cpl 인자 — $cpl 레지스터는 없다\n"
              "(gdb) c\n"
              "Breakpoint 1, do_timer (cpl=3) at kernel/sched.c:305\n"
              "#    ×5-6회 반복 — 관찰 후:\n"
              "(gdb) delete", start=13)
    para(d, p, 22000, 4300, 10000, 10200,
         "관찰 포인트\n\n"
         "· jiffies +1 (system_call.s:189)\n"
         "· 같은 pid의 counter −1 (sched.c:332)\n"
         "· cpl = 3 — 프롬프트 대기 중\n\n"
         "프롬프트 대기 중이면 current->pid = 0 (task 0, pause 루프)이고 "
         "cpl=3인 경우가 많다.\n\n"
         "counter가 0에 도달한 틱 다음 정지에서 pid가 바뀔 수 있다.\n\n"
         "슬라이드 16의 표를 이 값으로 채운다(36장).", 14)
    d.banner(p, "틱마다 jiffies +1 · counter −1 — 회계(13장)와 감소(15장)를 눈으로 확인한다", 14800, 19)

    # 36 캡처 A
    p = d.slide("캡처 A: 틱 연속 관찰", K.S_DEMO,
                "각주: lab 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 수치는 실행마다 다름(§8)")
    d.placeholder_output(p, 1100, 4150, 19700, 10300,
                         "(gdb) c\n"
                         "Breakpoint 1, do_timer (cpl=3) at kernel/sched.c:305\n"
                         "7: jiffies = 1284          8: current->pid = 0\n"
                         "9: current->counter = 7\n"
                         "10: /x *(long *)($esp+4) = 0x3\n"
                         "(gdb) c\n"
                         "Breakpoint 1, do_timer (cpl=3) at kernel/sched.c:305\n"
                         "7: jiffies = 1285          8: current->pid = 0\n"
                         "9: current->counter = 6\n"
                         "# jiffies +1 · counter -1 — 게스트는 셸 프롬프트 대기 중",
                         "10-tick-jiffies-counter.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· 연속 틱에서 jiffies 1씩 증가\n"
         "· 같은 pid의 counter 1씩 감소\n"
         "· cpl(=3) — 사용자 모드에서 온 틱\n\n"
         "각주: lab 빌드 · 수정 없음 · 게스트는 셸 프롬프트 대기 중 "
         "(대부분 task 0 또는 셸).\n\n"
         "슬라이드 16의 표를 이 값으로 채운다 — J=1284, c=7 → 1285, 6.", 14)

    # 37 시연 B
    p = d.slide("시연 B: counter가 0이 되는 순간", K.S_DEMO,
                "sched.c:94-142 대응 · bt로 호출자 확인 — 슬라이드 18-19 비교와 연결")
    auto_pane(d, p, 1100, 4300, 19700, 10200, "GDB — break schedule · bt · 태스크 표",
              "(gdb) delete\n"
              "(gdb) break schedule\n"
              "(gdb) c\n"
              "(gdb) bt\n"
              "# 기대 1: schedule <- do_timer <- _timer_interrupt\n"
              "# 기대 2: schedule <- sys_pause <- system_call\n"
              "#         (18-19장 네 경로와 연결)\n"
              "(gdb) p task[0]->state\n"
              "(gdb) p task[1]->pid ; p task[1]->state\n"
              "(gdb) p task[1]->counter ; p task[1]->priority\n"
              "(gdb) p *task[2]\n"
              "#    state·counter·priority·pid만 나열(존재하는 인덱스까지)", start=13)
    para(d, p, 22000, 4300, 10000, 10200,
         "절차\n\n"
         "1. delete 후 break schedule\n"
         "2. bt — 호출자가 do_timer인지\n"
         "   sys_pause 등인지 확인\n\n"
         "관찰 포인트\n\n"
         "· task[0]->state = 0 (idle)\n"
         "· task 1(init) — waitpid로 대기\n"
         "· 셸 — tty 입력 대기\n\n"
         "보통 task 1과 셸 모두 INTERRUPTIBLE(=1)이다(38장).", 14)
    d.banner(p, "counter가 0이 된 틱 — schedule의 호출자와 각 태스크의 state를 함께 본다", 14800, 19)

    # 38 캡처 B
    p = d.slide("캡처 B: bt와 태스크 표", K.S_DEMO,
                "각주: lab 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — lab 심볼/줄은 src와 다를 수 있음")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) bt\n"
                         "#0  schedule () at kernel/sched.c:104\n"
                         "#1  0x1d63 in do_timer (cpl=3)\n"
                         "    at kernel/sched.c:335\n"
                         "#2  0x2f1a in _timer_interrupt ()\n"
                         "    at system_call.s:195\n"
                         "# 또는: schedule <- sys_pause\n"
                         "#        <- system_call (system_call.s:80)",
                         "20-schedule-bt.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) p task[0]->state\n"
                         "$1 = 0    # task 0 — RUNNING(idle)\n"
                         "(gdb) p task[1]->pid ; p task[1]->state\n"
                         "$2 = 1  $3 = 1   # init — waitpid 대기\n"
                         "(gdb) p task[1]->counter ; p task[1]->priority\n"
                         "$4 = 15  $5 = 15\n"
                         "(gdb) p task[2]->state\n"
                         "$6 = 1   # 셸 — tty 입력 대기",
                         "21-task-state-counter.png")
    para(d, p, 1100, 14600, 31500, 1700,
         "task 1(init)은 waitpid로 INTERRUPTIBLE(=1), 셸은 tty 입력 대기로 "
         "INTERRUPTIBLE(=1)인 경우가 보통 — 각주 포함(§5).", 14)

    # 39 시연 C
    p = d.slide("시연 C: switch_to 전후 current", K.S_DEMO,
                "ljmp 1명령 관찰 — 실패 대응 포함 · 캡처는 40장(전/후 나란히)")
    auto_pane(d, p, 1100, 4300, 19700, 10200, "GDB — ljmp 주소 중단점",
              "# break schedule 뒤 finish가 안 되는 이유:\n"
              "#   switch_to의 ljmp가 다른 태스크로 건너뛴다\n"
              "(gdb) disassemble schedule   # ljmp 주소 <addr> 찾기\n"
              "(gdb) break *<addr>\n"
              "(gdb) c\n"
              "(gdb) p current->pid ; p/x $esp ; p/x $eip\n"
              "(gdb) stepi          # ljmp 1명령 = TSS 전환\n"
              "(gdb) p current->pid ; p/x $esp ; p/x $eip\n"
              "# 대체: watch current (hw watchpoint)\n"
              "# info registers tr 미지원 시 -> p/x $cs + $esp 상위 비트\n"
              "# 둘째 태스크: 게스트 백그라운드 명령 사전 실행", start=13)
    para(d, p, 22000, 4300, 10000, 10200,
         "관찰 포인트\n\n"
         "· 전환 전후 current->pid 변화\n"
         "· $esp — 다른 4 KiB 페이지\n"
         "· $eip — ljmp 바로 다음 명령\n\n"
         "실패 대응\n\n"
         "· stepi가 전환을 못 넘기면 break *<ljmp 다음 주소>로 재시도\n"
         "· 그래도 실패 시 사전 캡처 2장(30·31) — '기존 기록' 라벨", 14)
    d.banner(p, "전환 한 번 = ljmp 한 명령 — pid·커널 스택($esp)·재개 지점($eip)이 함께 바뀐다", 14800, 19)

    # 40 캡처 C
    p = d.slide("캡처 C: 전환 전/후", K.S_DEMO,
                "각주: lab 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 셸 외 둘째 태스크는 백그라운드 명령으로 확보(§11)")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) p current->pid\n"
                         "$6 = 2\n"
                         "(gdb) p/x $esp\n"
                         "$7 = 0x1cb4c   # 태스크 2 커널 스택\n"
                         "(gdb) p/x $eip\n"
                         "$8 = 0x15e2e   # ljmp 명령 (break *<addr>)",
                         "30-switch-before.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) stepi       # ljmp 실행 - TSS 전환\n"
                         "(gdb) p current->pid\n"
                         "$9  = 4          # 전환 후\n"
                         "(gdb) p/x $esp\n"
                         "$10 = 0x26f38    # 다른 4 KiB 페이지\n"
                         "(gdb) p/x $eip\n"
                         "$11 = 0x15e33    # ljmp 바로 다음 명령",
                         "31-switch-after.png")
    para(d, p, 1100, 14600, 31500, 1700,
         "전환 후 $eip가 ljmp 다음 명령(cmpl %%ecx,_last_task_used_math)인 점 — 저장된 "
         "EIP가 TSS에서 그대로 왔다(31장). 각주: 환경·수정 여부 기록.", 14)

    # 41 관찰 vs 추론
    p = d.slide("관찰 vs 추론 구분", K.S_DEMO,
                "오늘 실측(36·38·40장)과 소스 추론을 섞지 않는다 — 캡처 수치는 실행마다 다름(§8)")
    d.cards(p, [
        ("관찰 — 오늘 GDB로 본 것",
         "jiffies 증가 (do_timer 정지마다)\ncounter 감소 — 같은 pid에서\n"
         "bt — schedule의 호출자\n\ncurrent 변화 — pid·$esp·$eip\n(전환 전/후, 시연 C)"),
        ("추론 — 소스로 따라간 것",
         "TSS 내부 저장 순서 — CPU 동작이라\nGDB로 직접 보이지 않는다\n\n"
         "재충전 값 — 틱 수가 많아 시연 시간\n안에 반복 재현이 어렵다\n(손계산은 22장)\n\nTR·LDTR 갱신 — 문서+소스 근거"),
    ], y=4700, h=8300)
    d.banner(p, "'본 것'과 '읽은 것'을 나눠 말한다 — 캡처 수치를 '항상 이렇다'로 일반화하지 않는다", 14800, 19)

    # ── 정답 42–43 ────────────────────────────────────────────
    # 42 질문의 답 (1)
    p = d.slide("질문의 답 (1): 틱에서 schedule()까지", K.S_ANS,
                "system_call.s:176-197 · sched.c:305-336 — 경로 다이어그램 상반: 하드웨어→인터럽트→회계·조건")
    steps = [
        ("8253 — 10 ms 카운터 (LATCH 11931)", "kernel/sched.c:46 · 406-408", K.PAPER),
        ("IRQ 0 → IDT[0x20]", "sched.c:409 — 04회차 게이트 표", K.PAPER),
        ("_timer_interrupt — jiffies++", "system_call.s:189", K.PAPER),
        ("do_timer(cpl) — utime/stime 회계", "sched.c:305-317", K.PAPER),
        ("counter-- → 0이 되었는가", "sched.c:332-333 — 아니면 return", K.PAPER),
        ("cpl ≠ 0 (사용자 모드)인가", "sched.c:334 — 커널 모드(cpl=0)면 return", K.ORANGE),
        ("schedule()", "sched.c:335 — 하반은 다음 장", K.TEAL),
    ]
    for i, (l1, l2, col) in enumerate(steps):
        y = 4300 + i * 1440
        nbox(d, p, 2600, y, 19000, 1150, l1, l2, col, s1=15, s2=11)
        if i < 6:
            arrow(d, p, 11600, y + 1180, "↓", 18, K.TEAL)
    para(d, p, 23800, 4400, 7800, 9600,
         "각 단계에 파일:줄.\n\n"
         "여기까지가 '틱 한 번'의 상반 — 하드웨어 → 인터럽트 → 회계·조건.\n\n"
         "조건 두 개(counter 0 · cpl≠0)를 모두 통과해야 하반(선택·전환·복귀)으로 간다.",
         15)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # 43 질문의 답 (2)
    p = d.slide("질문의 답 (2): 선택·전환·복귀", K.S_ANS,
                "sched.c:104-142 · sched.h:171-184 · system_call.s:197 — 경로 다이어그램 하반")
    steps = [
        ("schedule() 진입", "sched.c:104", K.PAPER),
        ("깨우기 — alarm·시그널로 INTERRUPTIBLE을 RUNNING으로", "sched.c:104-120 (117-119)", K.PAPER),
        ("고르기 — RUNNING & counter 최대 / 모두 0이면 재충전하고 다시", "sched.c:124-140", K.PAPER),
        ("switch_to(next)", "sched.c:141 → sched.h:171", K.PAPER),
        ("ljmp — TSS 전환, CPU가 레지스터 저장·복원", "sched.h:177", K.ORANGE),
        ("새 태스크의 ljmp 다음 줄에서 재개", "sched.h:178 — 이전에 저장된 EIP", K.PAPER),
        ("… 그 태스크의 ret_from_sys_call", "system_call.s:197 · 101", K.PAPER),
        ("iret — 사용자 모드로", "system_call.s:128", K.TEAL),
    ]
    for i, (l1, l2, col) in enumerate(steps):
        y = 4300 + i * 1250
        nbox(d, p, 2600, y, 21000, 1000, l1, l2, col, s1=14, s2=10)
        if i < 7:
            arrow(d, p, 12600, y + 1010, "↓", 14, K.TEAL)
    para(d, p, 25600, 4400, 6000, 9600,
         "전환이 일어나지 않으면(같은 태스크) schedule()이 그냥 반환되고 ret_from_sys_call로 간다.\n\n"
         "잠든 태스크(c)는 깨어난 뒤 자기의 schedule() 다음 줄로 돌아온다(19장 표).",
         13)
    d.banner(p, "틱 한 번에 실행 태스크가 바뀌는 조건 = counter 0 + 사용자 모드(cpl≠0)", 14800, 20)

    # ── 정리 44–46 ────────────────────────────────────────────
    # 44 왜 커널 모드에서는 안 바꾸는가
    p = d.slide("왜 커널 모드에서는 안 바꾸는가", K.S_WRAP,
                "sched.c:334 · system_call.s:95-100 — 비선점의 이유와 값 · 현대의 선점은 14회차")
    d.code_panel(p, "src/kernel/sched.c", 333, 335, 1100, 4400, 15200, 3900,
                 size=13, caption_extra="if (!cpl) return; — 334")
    d.outline(p, 1100, 8900, 15200, 1900, K.ORANGE, 120)
    d.text(p, 1400, 9250, 14500, 1200, "if (!cpl) return;", 30, K.ORANGE,
           True)
    para(d, p, 1100, 11200, 15200, 3200,
         "0.11 커널은 비선점(non-preemptive) — 커널 모드 실행 중에는 타이머가 태스크를 "
         "바꾸지 않고, 스스로 schedule()을 부를 때만 전환된다.\n\n"
         "놓친 기회는 시스템 콜 끝의 검사(system_call.s:95-100)가 다음 문이 되어 준다.",
         15)
    nbox(d, p, 16900, 4400, 15700, 3000, "장점",
         "커널 데이터 경쟁이 거의 없다 — 전환 지점이 명시적 호출뿐이므로 락이 거의 불필요하다",
         K.PAPER, s1=16, s2=13)
    nbox(d, p, 16900, 7700, 15700, 3000, "비용",
         "긴 커널 작업(디스크 I/O 등) 중에는 사용자 응답이 계속 미뤄진다 — 틱이 와도 안 바뀐다",
         K.PAPER, s1=16, s2=13)
    nbox(d, p, 16900, 11000, 15700, 3000, "현대 커널",
         "선점 가능(preemptible) — 커널 안에서도 전환. 어떻게 바뀌었는지는 14회차",
         K.TEAL, s1=16, s2=13)
    d.banner(p, "커널 안은 안전하지만 느릴 수 있다 — 비선점은 선택이지 사고가 아니다", 14800, 19)

    # 45 흔한 오해 바로잡기
    p = d.slide("흔한 오해 바로잡기", K.S_WRAP,
                "§8 전문과 대응 — sched.h:19-23 · sched.c:124-140 · exit.c:166")
    d.cards(p, [
        ("schedule은\n타이머만 부른다",
         "아니다 — 네 경로 (a)-(d)가\n부른다(18-19장)\n\n인터럽트 핸들러 ≠\n스케줄러 전체"),
        ("counter는\n우선순위다",
         "counter = 남은 틱\npriority = 재충전 기준\n\n이름을 바꿔 부르면\n재충전 식이 흔들린다(22장)"),
        ("STOPPED\n상태가 있다",
         "정의(sched.h:23)와\nwaitpid case(exit.c:166)뿐\n\n들어가는 코드가 0.11에는\n없다(23장)"),
        ("task 0도\nschedule 대상",
         "선택 루프는\np > &FIRST_TASK —\ntask 0 제외\n\nnext=0은 '아무도 못 떠서'의\n기본값(126)"),
        ("switch_to가\n레지스터를 저장",
         "저장·복원은 ljmp를 본\nCPU가 TSS에 한다\n\n코드가 저장하는 건\n현대의 소프트웨어 전환"),
    ], y=4700, h=8600)
    d.banner(p, "오해 다섯 개 — 오늘 인용 줄 번호로 각각 반박 가능하다", 14800, 19)

    # 46 현대 커널 한 줄
    p = d.slide("현대 커널 한 줄", K.S_BG,
                "현대 이야기는 이 한 장으로 끝 — CFS·O(1) 등 정책 비교는 14회차 (§8)")
    d.text(p, 1100, 4200, 31500, 600, "Linux 0.11 (1991)", 16, K.TEAL, True)
    d.flow(p, [("틱", "8253 · IRQ 0\n10 ms"), ("회계", "do_timer\nutime/stime·counter--"),
               ("필요 시 선택", "schedule\nRUNNING·counter 최대"),
               ("전환", "switch_to ljmp\nTSS 전환")], y=4800, h=2700)
    d.text(p, 1100, 8000, 31500, 600, "현대 Linux", 16, K.TEAL, True)
    d.flow(p, [("틱", "tick · hrtimer\n주기·고해상도"), ("회계", "account_process_tick\n가상 실행시간"),
               ("선택", "CFS 등 정책\nvruntime 기준"),
               ("전환", "소프트웨어\n문맥 전환 — TSS 아님")], y=8600, h=2700)
    para(d, p, 1100, 11800, 31500, 2600,
         "TSS 전환 대신 소프트웨어 문맥 전환, 스케줄 정책도 다르다 — 그러나 "
         "'틱 → 회계 → 필요 시 선택 → 전환'의 골격과 state 개념은 그대로 남는다.\n"
         "오늘의 state 다섯 값도 현대의 TASK_* 이름으로 이어진다.", 15)
    d.banner(p, "구현과 정책은 바뀌어도 골격은 같다 — 틱·회계·선택·전환", 14800, 19)

    # ── 확인 47 ───────────────────────────────────────────────
    # 47 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답·근거 줄 번호는 계획 §6 (정답 클릭 후 표시) · 문항 원문 그대로")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "셸이 read() 안에서 키 입력을 기다리는 동안 타이머 틱이 100번 왔다. "
         "셸의 counter는 얼마나 줄었는가?", K.TEAL, 15)
    qbox(d, p, 1100, 6900, 31500, 2400, "Q2",
         "커널이 sys_write 중일 때 틱이 와서 counter가 0이 됐다. "
         "즉시 schedule()이 불리는가?", K.TEAL, 15)
    qbox(d, p, 1100, 9500, 31500, 2400, "Q3",
         "task 0의 pause()는 왜 영원히 잠들지 않는가?", K.TEAL, 15)
    qbox(d, p, 1100, 12100, 31500, 2400, "Q4",
         "switch_to(n)에서 ljmp의 목적지 오프셋(__tmp.a)은 "
         "왜 설정하지 않는가?", K.TEAL, 15)

    # ── 정리 48 ───────────────────────────────────────────────
    # 48 정리와 다음 회차
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "06회차 — fork · kernel/fork.c:97(예고) · 파트 B «실행의 길» 마지막 조각")
    d.text(p, 1100, 4200, 19700, 600, "정리 — 네 줄", 16, K.TEAL, True)
    d.text(p, 1100, 5000, 19700, 9000,
           "1  태스크 = task_struct + TSS 묶음 — task[] · current · jiffies가 관리한다\n"
           "2  틱 → do_timer → counter 감소 — 사용자 모드(cpl≠0)일 때만 schedule()\n"
           "3  schedule() = 깨우기 + 고르기(RUNNING·counter 최대)\n"
           "     + 재충전(counter = counter>>1 + priority — 상태 무관)\n"
           "4  전환 = switch_to의 ljmp — CPU가 TSS에 저장·복원, 커널 스택도 교체",
           17, K.PAPER, True)
    d.text(p, 22000, 4200, 10500, 600, "06회차 예고 — fork", 16, K.ORANGE,
           True)
    d.code_panel(p, "src/kernel/fork.c", 95, 97, 22000, 4900, 10500, 3600,
                 size=12, caption_extra="copy_process — tss.eax = 0")
    nbox(d, p, 22000, 8900, 5000, 1600, "부모", "eax = 자식 pid\nEIP = fork() 다음",
         K.PAPER, s1=14, s2=10)
    d.text(p, 27200, 9400, 800, 600, "≠", 20, K.ORANGE, True)
    nbox(d, p, 28100, 8900, 4400, 1600, "자식", "eax = 0 (:97)\n같은 EIP", K.TEAL,
         s1=14, s2=10)
    para(d, p, 22000, 10900, 10500, 3400,
         "task[1]은 누가 어떻게 만들었나? copy_process가 TSS의 eax를 0으로 두면 "
         "자식은 fork()에서 0을 받는다 — switch_to가 TSS를 통째로 복원하기 때문.",
         13, K.ORANGE)
    d.banner(p, "타이머 틱 한 번 = 회계 → 조건 → 선택 → TSS 전환 — 다음은 이 묶음을 만드는 fork", 14800, 19)


if __name__ == "__main__":
    K.run(globals())
