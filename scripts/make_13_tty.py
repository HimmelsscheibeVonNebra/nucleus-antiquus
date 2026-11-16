#!/usr/bin/env python3
"""13회차 덱 — 터미널 I/O (output/13-tty.pptx)

계획: materials/slide-plans/13-tty.md (§2 표 49행 1:1 · §3 앞부분 명세 ·
§4 상태 변화도 명세 — 'a'+Enter 4컷 · §5 캡처 7종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="13", total=49, slug="13-tty",
    part_no="F", part="«터미널»",
    title="13. 터미널 I/O",
    question="키보드에서 누른 글자가 read()까지 어떻게 전달되는가?",
    done=12,
    today_line="누른 글자가 세 개의 큐를 지나 잠든 read()를 깨운다 — 터미널 I/O",
    next_lines=[
        "12 → 13   파일 read ↔ 장치 read 갈림길(S_ISCHR → rw_char)을 봤다 → chr_drv/에서 키보드 글자가 read()까지",
        "13 → 14   13: 입력 tty_read·출력 tty_write으로 01–13의 양 끝을 채웠다 → 14: ls / 한 줄로 전부를 잇는 종합",
        "파트 F «터미널»은 이 회차 하나 — 11·12 완료 상자 «블록 장치·파일 시스템» · 14 상자 «종합»",
    ],
    road_note=("오늘은 10단계 전부를 밟는다 — 질문(흐름) → 지도(로드맵·구조) → 배경(터미널·원형 버퍼) →\n"
               "코드(keyboard.S → tty_io.c → console.c) → 상태도('a'+Enter 4컷·두 상태도) → 비교(termios·ioctl·MAJOR)\n"
               "→ 시연(GDB 3종) → 정답 → 확인 → 정리 — 12회차 open(\"/dev/tty0\")의 갈림길에서 시작한다."),
    STRUCT=dict(
        teal=["chr"],
        today=[("chr_drv/keyboard.S", "키보드 인터럽트"),
               ("chr_drv/tty_io.c", "copy_to_cooked·tty_read"),
               ("chr_drv/console.c", "con_write·con_init"),
               ("include/linux/tty.h", "tty_queue·세 큐")],
        flow="IRQ 1 → keyboard_interrupt → read_q → copy_to_cooked → tty_read → read()",
        up="↑ put_fs_byte → read() 반환",
        user="sh — read()로 키보드 입력을 기다린다",
    ),
)

CHECKS = dict(
    captions={
        5: "src/fs/read_write.c:55-68",
        9: "src/include/linux/tty.h:16-27",
        10: "src/include/linux/tty.h:45-55",
        11: "src/kernel/chr_drv/tty_io.c:51-65",
        12: "src/kernel/chr_drv/console.c:682-687",
        13: "src/kernel/chr_drv/keyboard.S:37-53",
        14: "src/kernel/chr_drv/keyboard.S:66-77",
        15: "src/kernel/chr_drv/keyboard.S:502-510",
        16: "src/kernel/chr_drv/keyboard.S:88-101",
        17: "src/kernel/chr_drv/keyboard.S:111-127",
        18: "src/kernel/chr_drv/tty_io.c:342-345",
        19: "src/kernel/chr_drv/tty_io.c:145-160",
        20: "src/kernel/chr_drv/tty_io.c:161-176",
        21: "src/kernel/chr_drv/tty_io.c:177-190",
        22: "src/kernel/chr_drv/tty_io.c:200-209",
        23: "src/kernel/chr_drv/tty_io.c:210-218",
        24: "src/kernel/chr_drv/tty_io.c:249-260",
        25: "src/kernel/chr_drv/tty_io.c:261-272",
        26: "src/kernel/chr_drv/tty_io.c:122-128",
        39: "src/kernel/chr_drv/tty_io.c:298-313",
        40: "src/kernel/chr_drv/console.c:445-462",
        41: "src/kernel/chr_drv/console.c:39-47",
        42: "src/kernel/printk.c:21-28",
        45: "src/kernel/chr_drv/serial.c:53-59",
    },
    required=[
        "keyboard_interrupt", "put_queue", "key_table", "do_self",
        "do_tty_interrupt", "copy_to_cooked", "read_q", "secondary",
        "write_q", "tty_read", "tty_write", "con_write", "con_init",
        "sleep_if_empty", "wake_up", "put_fs_byte", "tty_intr", "ICANON",
        "ECHOCTL", "ISIG", "ICRNL", "INIT_C_CC", "ECHOE", "VTIME", "VMIN",
        "-EINTR", "0xb8000", "0x60", "0x1E", "EOI", "table_list", "TCGETS",
        "crw_table", "rw_char", "-ENODEV", "-EPERM", "KBD_FINNISH",
        "stopped", "INTMASK", "set_cursor", "printk", "KILL_CHAR",
        "ERASE_CHAR", "EOF_CHAR", "interruptible_sleep_on",
        "선언됐다 ≠ 동작한다", "raw", "cooked",
    ],
    prereq=[
        ("S_ISCHR", "src/kernel/chr_drv/keyboard.S:88-101"),
        ("원형 버퍼", "src/kernel/chr_drv/tty_io.c:145-160"),
        ("ICANON", "src/kernel/chr_drv/tty_io.c:249-260"),
        ("wake_up", "src/kernel/chr_drv/tty_io.c:261-272"),
    ],
    structure_nodes=["keyboard.S", "tty_io.c", "console.c", "tty.h", "IRQ"],
    capture_slides=[34, 36, 38],
)


# ── 로컬 도우미 (deckkit 불변) ─────────────────────────────────
def wrap_kr(text, width, size):
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


def qstrip(d, p, x, y, w, name, cells, head, tail, data=None, hot=None,
           data_hot=False):
    """원형 큐 띠(일부 전개) — 채운 칸 PAPER/변경 칸 ORANGE, head·tail 마커,
    secondary는 data 배지(완성된 줄 수)."""
    n = len(cells)
    badge_w = 1500 if data is not None else 0
    cw = (w - badge_w) // n
    if name:
        d.text(p, x, y, w, 360, name, 11, K.TEAL, True)
    cy = y + 470
    for i, ch in enumerate(cells):
        cx = x + i * cw
        if ch is None:
            d.outline(p, cx, cy, cw - 130, 820, K.MUTED, 50)
        else:
            d.shape(p, cx, cy, cw - 130, 820,
                    K.ORANGE if i == hot else K.PAPER)
            d.text(p, cx + 70, cy + 130, cw - 270, 560, ch, 14, K.INK, True)
    my = cy + 860
    if head == tail:
        d.text(p, x + head * cw - 80, my, cw + 1400, 380,
               "▲ head=tail", 10, K.MUTED, True)
        ret = my + 420
    else:
        d.text(p, x + head * cw - 80, my, cw + 200, 380, "▲ head", 10,
               K.ORANGE, True)
        d.text(p, x + tail * cw - 80, my + 320, cw + 200, 380, "▲ tail",
               10, K.TEAL, True)
        ret = my + 740
    if data is not None:
        d.shape(p, x + n * cw + 120, cy + 60, 1360, 700,
                K.ORANGE if data_hot else K.TEAL)
        d.text(p, x + n * cw + 120, cy + 210, 1360, 480, f"data = {data}",
               11, K.INK, True)
    return ret


E6 = [None] * 6


def populate(d):
    # ── 코드 05 (12회차 복습) ──────────────────────────────────
    p = d.slide("갈림길: 파일 read와 장치 read — sys_read의 S_ISCHR", K.S_CODE,
                "12회차 — open(\"/dev/tty0\")의 inode가 문자 장치(S_IFCHR)로 끝나던 지점에서 오늘 시작한다")
    d.code_panel(p, "src/fs/read_write.c", 55, 68, 1100, 4400, 15200, 8900,
                 size=10)
    nbox(d, p, 16900, 4400, 15700, 1100, "sys_read(fd, buf, count)",
         "fd가 가리키는 inode의 i_mode로 갈라진다", K.PAPER, s1=14, s2=11)
    nbox(d, p, 16900, 5900, 15700, 1000, "S_ISCHR → rw_char(READ, i_zone[0])",
         "오늘 — chr_drv/ 터미널", K.ORANGE, s1=13, s2=11)
    nbox(d, p, 16900, 7100, 15700, 900, "S_ISREG / S_ISDIR → file_read",
         "12회차 — 파일", None, K.MUTED, s1=13, s2=11)
    nbox(d, p, 16900, 8200, 15700, 900, "S_ISBLK → block_read",
         "11회차 — 블록 장치", None, K.MUTED, s1=13, s2=11)
    para(d, p, 16900, 9300, 15700, 4000,
         "같은 read() 인터페이스 — 아래가 다르다. 12회차에 open(\"/dev/tty0\")으로 "
         "연 inode는 문자 장치였고, 그 길이 오늘 120분의 주인공 chr_drv/ 이다.", 14)
    d.banner(p, "같은 read() — inode의 종류(S_IFMT)가 아래층을 갈라놓는다")

    # ── 배경 06 터미널이란 ─────────────────────────────────────
    p = d.slide("터미널이란 무엇인가 — 1991년의 콘솔과 직렬 포트", K.S_BG,
                "include/linux/tty.h:45-55 · tty_io.c:51-92 — 'tty'는 teletype에서 온 이름 · VGA 텍스트 메모리(0xb8000) 80×25")
    d.cards(p, [
        ("콘솔 = tty_table[0]",
         "키보드(IRQ 1) + VGA 텍스트 화면\n0xb8000 — 문자+속성 2바이트\nwrite = con_write"),
        ("직렬 포트 rs = tty_table[1..2]",
         "0x3f8(COM1) · 0x2f8(COM2)\nc_cflag = B2400|CS8 · 변환 0\nwrite = rs_write"),
        ("현대와의 경계",
         "가상 터미널 전환 · pty ·\nline discipline 계층은 없음\n14회차에서 개념만 비교"),
    ], y=4400, h=4600)
    d.table(p, 1100, 9600, [2800, 8200, 5200, 14200], [
        ["인덱스", "장치", "write 함수", "초기 플래그 (tty_io.c:51-92)"],
        ["0", "콘솔 (키보드+VGA)", "con_write",
         "iflag ICRNL · oflag OPOST|ONLCR · lflag ISIG|ICANON|ECHO|ECHOCTL|ECHOKE"],
        ["1", "rs1 — 0x3f8", "rs_write", "변환 플래그 전부 0 · c_cflag B2400|CS8"],
        ["2", "rs2 — 0x2f8", "rs_write", "변환 플래그 전부 0 · c_cflag B2400|CS8"],
    ], row_h=900, size=13)
    d.banner(p, "tty 3개 — 커널은 이 표 하나(tty_table[])로 세 터미널을 다룬다", 13900, 17)

    # ── 배경 07 raw / cooked ───────────────────────────────────
    p = d.slide("raw와 cooked: 두 번 저장되는 글자", K.S_BG,
                "keyboard.S:453-484 do_self · tty_io.c:145-228 copy_to_cooked — 오늘의 용어 정리 장")
    nbox(d, p, 1100, 4400, 4800, 1300, "키보드 컨트롤러",
         "누름·뗌마다 1바이트", None, K.MUTED, s1=15, s2=11)
    arrow(d, p, 6050, 4650, "→", 24, K.ORANGE)
    d.text(p, 5750, 3850, 3200, 400, "스캔 코드", 12, K.ORANGE, True)
    nbox(d, p, 7600, 4400, 7000, 1300, "(1) 스캔 코드 → ASCII",
         "do_self — key_map/shift_map/alt_map", K.PAPER, s1=14, s2=11)
    arrow(d, p, 14850, 4650, "→", 24, K.ORANGE)
    nbox(d, p, 16400, 4400, 6300, 1300, "read_q — raw",
         "아직 줄 편집 전", K.TEAL, s1=15, s2=11)
    nbox(d, p, 23800, 4400, 8700, 1300, "(2) 줄 편집 · ^C 해석",
         "copy_to_cooked — 백스페이스·^U·^C·CR/NL", K.PAPER, s1=13, s2=11)
    arrow(d, p, 27600, 5750, "↓", 22, K.ORANGE)
    nbox(d, p, 23800, 6100, 8700, 1100, "secondary — cooked",
         "줄 단위로 완성된 입력", K.TEAL, s1=14, s2=11)
    arrow(d, p, 27600, 7250, "↓", 22, K.TEAL)
    nbox(d, p, 23800, 8100, 8700, 1000, "read() → 셸",
         "tty_read — put_fs_byte", K.ORANGE, s1=14, s2=11)
    arrow(d, p, 19300, 5850, "↘", 22, K.TEAL)
    nbox(d, p, 1100, 6900, 17800, 1100,
         "L_ECHO → write_q → con_write → VGA",
         "에코(echo) — 입력 글자를 화면에 되돌려 그린다", K.PAPER,
         s1=14, s2=11)
    d.table(p, 1100, 8600, [6400, 12600, 12500], [
        ["용어", "정의", "처리 주체"],
        ["스캔 코드", "키 하나의 누름(make)/뗌(break) 1바이트 — 글자 아님", "keyboard.S"],
        ["raw / cooked", "줄 편집·제어 문자 해석을 커널이 하는지(ICANON) 여부", "copy_to_cooked"],
        ["에코", "입력 글자를 화면에 되돌려 그리기 — 셸의 일이 아니다", "L_ECHO → con_write"],
    ], row_h=900, size=13)
    d.banner(p, "키보드는 글자를 주지 않는다 — 커널이 두 단계에 걸쳐 '읽을 수 있는 줄'로 만든다", 12700, 17)

    # ── 배경 08 원형 버퍼 개념 ─────────────────────────────────
    p = d.slide("원형 버퍼 1024바이트 — 개념", K.S_BG,
                "include/linux/tty.h:14-30 — 이 링 그림이 오늘 핵심 시각 언어다(16·27·28장)")
    d.text(p, 1100, 4250, 28000, 500,
           "tty_queue.buf[1024] — 1024칸 중 앞부분만 전개한 모습", 15, K.TEAL, True)
    letters = list("abcde")
    for i in range(12):
        cx = 1400 + i * 2300
        if i < 5:
            d.shape(p, cx, 5100, 2100, 1000, K.TEAL)
            d.text(p, cx + 200, 5350, 1700, 550, letters[i], 18, K.INK, True)
        else:
            d.outline(p, cx, 5100, 2100, 1000, K.MUTED, 60)
            d.text(p, cx + 200, 5350, 1700, 550, f"{i}", 13, K.MUTED)
    d.text(p, 1400, 6250, 2100, 400, "▲ tail", 12, K.TEAL, True)
    d.text(p, 12900, 6250, 2100, 400, "▲ head", 12, K.ORANGE, True)
    d.text(p, 1400, 4750, 5000, 400, "읽는 쪽 — 소비자가 전진", 12, K.TEAL, True)
    d.text(p, 11800, 4750, 5000, 400, "쓰는 쪽 — 생산자가 전진", 12, K.ORANGE, True)
    d.text(p, 27600, 4750, 5400, 700, "↻  1023 다음은 0", 15, K.ORANGE, True)
    arrow(d, p, 2900, 6800, "↻  마지막 칸 다음 → 처음으로 감는다 — INC(a) = (a+1) & 1023",
          15, K.ORANGE, 15000, 700)
    d.cards(p, [
        ("head — 쓰는 인덱스",
         "PUTCH 가 buf[head] 에 쓰고\nhead 전진\n(put_queue · tty_write)"),
        ("tail — 읽는 인덱스",
         "GETCH 가 buf[tail] 을 읽고\ntail 전진\n(copy_to_cooked · tty_read)"),
        ("FULL = LEFT == 0",
         "LEFT = (tail-head-1)\n        & 1023\n한 칸은 항상 비워둔다\n→ 1024칸에 최대 1023자"),
    ], y=8000, h=4400)
    d.banner(p, "고정 크기 배열을 끝에서 처음으로 감아 쓴다 — malloc 없는 커널의 큐")

    # ── 코드 09 원형 버퍼 코드 ─────────────────────────────────
    p = d.slide("원형 버퍼 — 코드: struct tty_queue와 매크로", K.S_CODE,
                "include/linux/tty.h:16-34 · GETCH/PUTCH는 31-34 · keyboard.S:21-26이 이 구조 오프셋을 하드코딩한다(16장)")
    d.code_panel(p, "src/include/linux/tty.h", 16, 27, 1100, 4400, 15200,
                 7750, size=10)
    d.code_panel(p, "src/include/linux/tty.h", 28, 34, 16900, 4400, 15700,
                 5000, size=10)
    para(d, p, 1100, 12400, 15200, 2000,
         "INC(a) = (a+1) & 1023 — 1023 다음 0으로 감긴다.\n"
         "EMPTY head==tail · LEFT (tail-head-1)&1023 · FULL !LEFT — 빈 큐와 가득 찬 큐를 "
         "한 칸 차이로 구분한다.", 14)
    nbox(d, p, 16900, 9600, 15700, 1100, "GETCH(queue,c) — 소비",
         "c = buf[tail]; INC(tail) — read_q·secondary·write_q를 읽는 쪽", K.PAPER,
         s1=14, s2=10)
    nbox(d, p, 16900, 10900, 15700, 1100, "PUTCH(c,queue) — 생산",
         "buf[head] = c; INC(head) — put_queue·tty_write·에코", K.PAPER,
         s1=14, s2=10)
    badge(d, p, 16900, 12300, 15700,
          "예고 — keyboard.S:23-26이 오프셋(head=4·tail=8…)을 상수로 기입(16장)", K.TEAL, 700, 12)
    d.banner(p, "EMPTY · FULL · CHARS — 전부 head/tail 산술이다. 큐의 전부가 정수 두 개다", 14700, 16)

    # ── 코드 10 세 큐 ──────────────────────────────────────────
    p = d.slide("tty_struct의 세 큐", K.S_CODE,
                "include/linux/tty.h:45-55 — 세 큐의 생산자·소비자가 오늘 코드 읽기의 지도다")
    d.code_panel(p, "src/include/linux/tty.h", 45, 55, 1100, 4400, 19700,
                 6600, size=9)
    nbox(d, p, 1100, 11400, 3600, 1100, "키보드 IRQ 1", "put_queue", None,
         K.MUTED, s1=13, s2=11)
    arrow(d, p, 4750, 11650, "→", 22, K.ORANGE)
    nbox(d, p, 6100, 11400, 4400, 1100, "read_q", "raw — 인터럽트가 씀",
         K.TEAL, s1=15, s2=11)
    arrow(d, p, 10550, 11650, "→", 22, K.ORANGE)
    d.text(p, 10100, 10850, 5400, 400, "copy_to_cooked", 12, K.TEAL, True)
    nbox(d, p, 12000, 11400, 4400, 1100, "secondary",
         "cooked — tty_read가 읽음", K.TEAL, s1=15, s2=11)
    arrow(d, p, 16450, 11650, "→", 22, K.ORANGE)
    nbox(d, p, 17900, 11400, 4600, 1100, "read()",
         "put_fs_byte — 사용자 버퍼", K.ORANGE, s1=15, s2=11)
    d.text(p, 6100, 12650, 10300, 700,
           "에코 분기 — L_ECHO면 write_q에도 ↓",
           13, K.TEAL, True)
    nbox(d, p, 6100, 13300, 4400, 1000, "write_q", "tty_write가 씀", K.TEAL,
         s1=14, s2=11)
    arrow(d, p, 10550, 13550, "→", 22, K.ORANGE)
    nbox(d, p, 12000, 13300, 5300, 1000, "tty->write(tty)",
         "콘솔 con_write · rs rs_write", K.PAPER, s1=14, s2=10)
    arrow(d, p, 17350, 13550, "→", 22, K.ORANGE)
    nbox(d, p, 17900, 13300, 4600, 1000, "VGA 0xb8000 / UART",
         "con_write·rs_write", K.PAPER, s1=13, s2=10)

    # ── 코드 11 초기 termios ───────────────────────────────────
    p = d.slide("콘솔 tty의 초기 termios — tty_table[0]", K.S_CODE,
                "tty_io.c:51-65 · INIT_C_CC include/linux/tty.h:57-63 · rs 1·2는 66-91 변환 플래그 0")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 51, 65, 1100, 4400, 19700,
                 10000, size=10)
    auto_pane(d, p, 22000, 4400, 10600, 5400,
              "INIT_C_CC — tty.h:63 기본 제어 문자",
              "\\003 \\034 \\177 \\025 \\004\n"
              "\\0 \\1 \\0 \\021 \\023 \\032\n"
              "\\0 \\022 \\017 \\027 \\026 \\0\n"
              "\n"
              "^C=INTR  ^\\=QUIT  DEL=ERASE\n"
              "^U=KILL  ^D=EOF  ^Q=START\n"
              "^S=STOP  ^Z=SUSPEND(선언만)", 12)
    para(d, p, 22000, 10100, 10600, 4300,
         "iflag=ICRNL — Enter(13)을 10(NL)으로\n"
         "oflag=OPOST|ONLCR — 출력 \\n 앞에 13\n"
         "lflag=ISIG|ICANON|ECHO|ECHOCTL|ECHOKE\n"
         "write=con_write · 세 큐 0으로 시작\n\n"
         "rs 1·2(66-91): 변환 플래그 전부 0, B2400|CS8, rs_write", 14)
    d.banner(p, "이 초기값 하나가 줄 편집·에코·^C·CR/NL 변환을 모두 켠다 — 오늘 모든 분기의 기준")

    # ── 코드 12 인터럽트 등록 ──────────────────────────────────
    p = d.slide("키보드 인터럽트가 걸리기까지 — con_init의 게이트 등록", K.S_CODE,
                "kernel/chr_drv/console.c:617-689 · 683-684 — 4회차 IDT 그림의 재사용")
    d.code_panel(p, "src/kernel/chr_drv/console.c", 682, 687, 1100, 4400,
                 15200, 4450, size=11)
    nbox(d, p, 1100, 9100, 15200, 1000, "왜 콘솔 초기화 안에?",
         "con_init이 화면·키보드를 함께 소유 — main()이 부팅 중 호출(3회차)",
         K.PAPER, s1=14, s2=11)
    para(d, p, 1100, 10300, 15200, 4100,
         "683: set_trap_gate(0x21, &keyboard_interrupt) — IDT 벡터 0x21(=IRQ 1 + 0x20)에 트랩 게이트 등록.\n"
         "684: outb_p(inb_p(0x21)&0xfd, 0x21) — PIC 마스크 레지스터의 비트1(IRQ 1)을 해제.\n"
         "685-687: 0x61 포트 토글 — 키보드 컨트롤러 리셋(14장 ack와 같은 포트).", 14)
    nbox(d, p, 16900, 4400, 4200, 950, "키보드 IRQ 1", None, K.ORANGE, s1=12)
    arrow(d, p, 18300, 5400, "↓", 22, K.ORANGE)
    nbox(d, p, 16900, 6100, 4200, 950, "8259 PIC", "마스크 비트1 해제",
         K.PAPER, s1=13, s2=10)
    arrow(d, p, 18300, 7100, "↓", 22, K.ORANGE)
    nbox(d, p, 16900, 7800, 4200, 950, "벡터 0x21", "IRQ + 0x20", K.PAPER,
         s1=13, s2=10)
    arrow(d, p, 18300, 8800, "↓", 22, K.ORANGE)
    nbox(d, p, 16900, 9500, 4200, 950, "IDT[0x21]", "trap gate", K.PAPER,
         s1=13, s2=10)
    arrow(d, p, 18300, 10500, "↓", 22, K.ORANGE)
    nbox(d, p, 16900, 11200, 4200, 950, "_keyboard_interrupt",
         "keyboard.S:37", K.TEAL, s1=12, s2=10)
    d.text(p, 21500, 4500, 11100, 9800,
           "인텔 설계: 외부 인터럽트는\nPIC가 CPU의 INTR에 알리고\nCPU는 IDT에서 벡터를 찾는다.\n\n"
           "0x21 = 33 = 0x20(IRQ 0 기준) + 1\n\n"
           "4회차에서 본 IDT 구조가\n그대로 재사용된다 —\n오늘은 그 표의 0x21칸이\n채워지는 순간이다.", 15)

    # ── 코드 13 keyboard_interrupt (1) ─────────────────────────
    p = d.slide("keyboard_interrupt 읽기 (1): 스캔 코드 읽기와 디스패치", K.S_CODE,
                "kernel/chr_drv/keyboard.S:37-53 — 레지스터 저장 → inb $0x60 → key_table 점프")
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 37, 53, 1100, 4400,
                 15200, 9600, size=9)
    nbox(d, p, 16900, 4400, 15700, 1000, "inb $0x60 → al = 스캔 코드",
         "예: 'a' 누름 = 0x1E · 뗌 = 0x9E", K.ORANGE, s1=14, s2=11)
    arrow(d, p, 24100, 5450, "↓", 22, K.ORANGE)
    nbox(d, p, 16900, 6150, 15700, 950, "call key_table(,%eax,4)",
         "스캔 코드 × 4 = 테이블 오프셋 — 코드가 곧 인덱스", K.PAPER, s1=14, s2=11)
    arrow(d, p, 24100, 7150, "↓", 22, K.ORANGE)
    for i, (nm, sub) in enumerate([("do_self", "글자 키 대부분"),
                                   ("ctrl / lshift / alt …", "mode 비트 변경"),
                                   ("none", "빈 칸·break 코드 대부분"),
                                   ("func / cursor", "F키·화살표")]):
        nbox(d, p, 16900 + (i % 2) * 8050, 7850 + (i // 2) * 1150, 7650, 1050,
             nm, sub, K.TEAL if i == 0 else K.PAPER, s1=13, s2=10)
    para(d, p, 16900, 10300, 15700, 3700,
         "0xe0/0xe1 접두(확장 키)는 e0 플래그에 기록하고 jmp e0_e1 — 다음 바이트가 진짜 스캔 코드.\n"
         "ds·es를 0x10(커널 데이터)으로 — 인터럽트는 어떤 문맥에서도 온다.", 14)

    # ── 코드 14 keyboard_interrupt (2) ─────────────────────────
    p = d.slide("keyboard_interrupt 읽기 (2): ack · EOI · do_tty_interrupt", K.S_CODE,
                "kernel/chr_drv/keyboard.S:54-77 — 핸들러 안에서 C 함수 copy_to_cooked까지 호출 · 주석은 tty_io.c:328-341(18장)")
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 54, 65, 1100, 4400,
                 15200, 7750, size=10)
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 66, 77, 16900, 4400,
                 15700, 7750, size=10)
    d.text(p, 1130, 12350, 15200, 400, "0x61 토글 = 키보드에 '받았다'고 알리는 ack",
           12, K.TEAL, True)
    d.text(p, 17130, 12350, 15700, 400, "EOI — PIC에 처리 완료 통보(인터럽트 재허용)",
           12, K.TEAL, True)
    d.flow(p, [("inb $0x60", "스캔 코드"), ("key_table", "do_self 등"),
               ("0x61 토글", "ack"), ("EOI 0x20", "PIC 허용"),
               ("do_tty_interrupt(0)", "copy_to_cooked"), ("iret", "복귀")],
           y=12900, h=1500, title_size=13)

    # ── 코드 15 key_table과 do_self ────────────────────────────
    p = d.slide("key_table과 do_self: 스캔 코드에서 글자로", K.S_CODE,
                "keyboard.S:502-510(key_table) · 453-461(맵 선택) · Ctrl 계산 466-477 · break 코드는 530-540")
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 502, 510, 1100, 4400,
                 14500, 6150, size=8)
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 453, 461, 15900, 4400,
                 16300, 6150, size=10)
    d.table(p, 1100, 10800, [5200, 4400, 10400, 10400], [
        ["mode 조건", "변환", "계산", "결과"],
        ["ctrl|caps (0x4c)", "subb $32", "'c'(0x63) − 32 = 0x43", "'C' — 대문자화"],
        ["ctrl (0x0c)", "subb $64", "'C'(0x43) − 64 = 0x03", "^C — 제어 문자"],
        ["left alt (0x10)", "orb $0x80", "'a'(0x61) | 0x80 = 0xe1", "Alt 접두 문자"],
    ], row_h=780, size=13)
    para(d, p, 1100, 14050, 31500, 600,
         "누름(make)·뗌(break)이 각각 한 번 — break 코드(≥0x80)의 key_table 항목은 대부분 none이라 read_q에 아무 것도 안 넣는다.", 13)

    # ── 코드 16 put_queue ──────────────────────────────────────
    p = d.slide("put_queue: read_q에 넣기", K.S_CODE,
                "keyboard.S:88-110 · _table_list = tty_io.c:99-103 · 큐 오프셋 상수 = keyboard.S:21-26 — 손으로 맞춘 이중 관리")
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 88, 101, 1100, 4400,
                 15200, 8850, size=10)
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 102, 109, 16900, 4400,
                 15700, 5550, size=10)
    qstrip(d, p, 17000, 10300, 15500, "read_q 직후 — buf[0]='a'",
           ["a"] + E6[1:], 1, 0, hot=0)
    para(d, p, 1100, 13500, 15200, 1000,
         "가득 차면(전진한 head가 tail과 같으면) je 3f — 폐기. 알림도 카운트도 없다(47장).", 14)
    para(d, p, 16900, 12800, 15700, 1700,
         "_table_list[0] = &tty_table[0].read_q (tty_io.c:99-103)\n"
         "movl $0,(%ecx)(106) — proc_list 태스크 깨우기. 단 0.11엔 read_q에 잠드는 코드가 없다(26장 grep).", 12)

    # ── 코드 17 modifier ───────────────────────────────────────
    p = d.slide("조합 키와 modifier 상태 — mode 바이트와 func_table", K.S_CODE,
                "keyboard.S:111-127(ctrl/alt) · 239-242(func_table) · 244-261(key_map) · config.h:19 = KBD_FINNISH")
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 111, 127, 1100, 4400,
                 15200, 9600, size=9)
    d.code_panel(p, "src/kernel/chr_drv/keyboard.S", 239, 242, 16900, 4400,
                 15700, 3350, size=11)
    d.table(p, 16900, 8100, [4400, 11300], [
        ["mode 비트", "의미"],
        ["01 · 02", "왼쪽 · 오른쪽 shift"],
        ["04 · 10", "ctrl · alt (e0 접두면 ×2)"],
        ["20", "alt-gr — alt_map 선택"],
        ["40 · 80", "caps lock · 토글 마커"],
    ], row_h=800, size=13)
    para(d, p, 16900, 12400, 15700, 1600,
         "F1 = ESC [ [ A — func_table의 0x415b5b1b가 4바이트 한 번에 put_queue.\n"
         "원본 config.h:19은 KBD_FINNISH — US 키보드 기준 설명과 기호 위치가 다를 수 있음(lab 키맵 확인, §8).", 13)
    d.banner(p, "ctrl은 do_self의 계산(−32·−64)에, shift·alt는 맵 선택과 mode 비트에 — 층이 다르다", 14200, 15)

    # ── 코드 18 do_tty_interrupt ───────────────────────────────
    p = d.slide("do_tty_interrupt → copy_to_cooked: 인터럽트 안의 cooked 처리", K.S_CODE,
                "tty_io.c:342-345 — 세 줄짜리 경유 함수 · 328-341의 Linus 주석이 설계 의도를 말한다")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 342, 345, 1100, 4400,
                 15200, 3350, size=11)
    auto_pane(d, p, 1100, 8000, 15200, 6400,
              "tty_io.c:328-341 — Linus 주석(발췌, 원문)",
              "\"Jeh, sometimes I really like the 386.\n"
              " This routine is called from an interrupt,\n"
              " and there should be absolutely no problem\n"
              " with sleeping even in an interrupt (I hope).\n"
              " Of course, if somebody proves me wrong, I'll\n"
              " hate intel for all time :-). We'll have to\n"
              " be careful and see to reinstating the interrupt\n"
              " chips before calling this, though.\"\n"
              "                    — EOI 를 먼저 보내는 이유(14장)", 12)
    steps = [("IRQ 1", "키보드"), ("keyboard_interrupt", "keyboard.S:37"),
             ("put_queue", "read_q 저장 — 88"),
             ("do_tty_interrupt(0)", "tty_io.c:342"),
             ("copy_to_cooked", "&tty_table[0] — 145")]
    for i, (t, s) in enumerate(steps):
        nbox(d, p, 16900, 4400 + i * 2050, 15700, 1150, t, s, K.PAPER,
             s1=14, s2=10)
        if i < 4:
            arrow(d, p, 24100, 5560 + i * 2050, "↓", 20, K.ORANGE)
    para(d, p, 16900, 13000, 15700, 1400,
         "호출 순서도다 — 상태 변화는 27-29장의 상태도로 본다.", 14, K.TEAL, True)

    # ── 코드 19 copy_to_cooked (1) ─────────────────────────────
    p = d.slide("copy_to_cooked (1): 루프와 CR/NL 변환", K.S_CODE,
                "tty_io.c:145-160 · 플래그 매크로 28-49 — 콘솔은 ICRNL만 켜져 있다")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 145, 160, 1100, 4400,
                 15200, 9070, size=9)
    d.table(p, 16900, 4400, [3900, 4800, 7000], [
        ["입력", "플래그(매크로)", "결과"],
        ["13 CR", "ICRNL (켬)", "10 NL — Enter"],
        ["13 CR", "IGNCR (끔)", "폐기 continue"],
        ["10 NL", "INLCR (끔)", "13 CR"],
        ["그 외", "IUCLC (끔)", "tolower(c)"],
    ], row_h=800, size=13)
    para(d, p, 16900, 8700, 15700, 5700,
         "루프 조건 — !EMPTY(read_q) && !FULL(secondary)\n"
         "read_q가 비거나 secondary가 가득 찰 때까지 한 글자씩 GETCH.\n\n"
         "주의 — I_NOCR 매크로(tty_io.c:43)가 검사하는 플래그는\n"
         "IGNCR이다. 이름(NOCR)과 실제(IGNCR)가 다르다.\n\n"
         "콘솔 초기값(iflag=ICRNL)에서는 13→10 변환만 일어난다 —\n"
         "Enter가 read()에 10(NL) 한 글자로 도착하는 이유.", 14)

    # ── 코드 20 copy_to_cooked (2) KILL ────────────────────────
    p = d.slide("copy_to_cooked (2): 줄 편집 — KILL(^U)", K.S_CODE,
                "tty_io.c:161-176 — secondary.head를 줄 시작까지 되감는다 · LAST 매크로(tty.h:28)")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 161, 176, 1100, 4400,
                 15200, 9070, size=9)
    d.text(p, 16900, 4400, 15700, 500, "^U 입력 전 secondary — \"ls -l\" 치던 중",
           14, K.TEAL, True)
    qstrip(d, p, 16900, 5000, 15700, None,
           ["l", "s", " ", "-", "l"] + E6[5:], 5, 0)
    arrow(d, p, 24100, 7550, "↓  ^U (KILL_CHAR)", 15, K.ORANGE, 4400, 600)
    qstrip(d, p, 16900, 8300, 15700, "후 — head가 줄 시작까지 DEC",
           E6, 0, 0)
    para(d, p, 16900, 10600, 15700, 3800,
         "루프: EMPTY || LAST==10(줄 시작) || EOF 직전까지\n"
         "에코 — L_ECHO면 write_q에 127(DEL): c<32면 두 번(^X 표기 지움)\n"
         "tty->write(tty)로 매번 즉시 화면 반영 — 지워지는 게 눈에 보인다", 14)

    # ── 코드 21 copy_to_cooked (2) ERASE/STOP ──────────────────
    p = d.slide("copy_to_cooked (2): ERASE(DEL)와 STOP/START", K.S_CODE,
                "tty_io.c:177-199 — grep stopped → tty_io.c:60(초기값) · 192·196(대입)뿐 — 읽는 곳 없음(§8)")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 177, 190, 1100, 4400,
                 15200, 8100, size=9)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 191, 199, 16900, 4400,
                 15700, 6100, size=10)
    qstrip(d, p, 16900, 10700, 15700, "ERASE — head 한 칸 DEC + 에코 127",
           ["l", "s"] + E6[2:], 2, 0)
    para(d, p, 1100, 12800, 15200, 1600,
         "줄 시작(LAST==10)이나 EOF 직전이면 continue로 무시 — 줄 경계를 지워지지 않게 지킨다.", 14)
    d.outline(p, 16900, 12850, 15700, 1550, K.ORANGE, 110)
    d.text(p, 17150, 13100, 15200, 1200,
           "^S/^Q는 tty->stopped만 바꾼다(192·196).\n"
           "이 값을 읽는 곳이 없다(grep) — 콘솔 출력은 실제로 멈추지 않는다.", 13, K.ORANGE, True)

    # ── 코드 22 ISIG ^C ────────────────────────────────────────
    p = d.slide("copy_to_cooked (3): ISIG와 ^C — tty_intr", K.S_CODE,
                "tty_io.c:200-209 · tty_intr 111-120 · INTMASK=1<<(SIGINT-1)=2 · system_call.s:101-119(10회차)")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 200, 209, 1100, 4400,
                 15200, 6100, size=10)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 111, 120, 16900, 4400,
                 15700, 6100, size=10)
    chain = [("^C = INTR_CHAR(0x03)", "do_self의 −64 결과 · 201"),
             ("tty_intr(tty, INTMASK)", "200-204 · continue — 큐에 안 넣음"),
             ("task[i]->signal |= 2", "pgrp 같은 모든 태스크 (117-120)"),
             ("schedule()", "sched.c:117-119 → RUNNING"),
             ("ret_from_sys_call", "system_call.s:101-119"),
             ("do_signal", "10회차 — cat 종료")]
    for i, (t, s) in enumerate(chain):
        x = 1100 + (i % 3) * 10400
        y = 11000 + (i // 3) * 1750
        nbox(d, p, x, y, 9200, 1450, t, s, K.PAPER, s1=14, s2=10)
        if i % 3 < 2:
            arrow(d, p, x + 9350, y + 350, "→", 20, K.ORANGE)
    para(d, p, 1100, 14350, 31500, 600,
         "^C 글자(0x03)는 secondary에 넣지 않는다(continue) — read()로 전달되지 않고 시그널 경로로만 간다.", 14)

    # ── 코드 23 줄 카운트·에코·깨우기 ──────────────────────────
    p = d.slide("copy_to_cooked (4): 줄 카운트 · 에코 · 깨우기", K.S_CODE,
                "tty_io.c:210-228 — data는 '완성된 줄 수' 카운터 · 끝의 wake_up이 잠든 read()를 깨운다")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 210, 218, 1100, 4400,
                 15200, 6150, size=10)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 219, 228, 16900, 4400,
                 15700, 6700, size=10)
    d.flow(p, [("c==10 || EOF", "data++ (210-211)\n완성된 줄 수"),
               ("L_ECHO", "write_q→con_write\n(212-222)"),
               ("tty->write(tty)", "즉시 호출 (223)"),
               ("PUTCH(c, secondary)", "cooked 큐에 (225)"),
               ("wake_up(227)", "잠든 셸 깨움\n→ 상태도 ②(29장)")],
           y=11400, h=2900, title_size=13)

    # ── 코드 24 tty_read (1) ───────────────────────────────────
    p = d.slide("tty_read (1): 잠들기 조건", K.S_CODE,
                "tty_io.c:237-260 · VTIME/VMIN은 INIT_C_CC 기본(\\0, \\1)으로 분기 생략 — 오늘은 정규 모드 길만")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 237, 248, 1100, 4400,
                 15200, 7750, size=10)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 249, 260, 16900, 4400,
                 15700, 7750, size=10)
    para(d, p, 16900, 12500, 15700, 1900,
         "VTIME/VMIN(240-248): 기본 VMIN=1, VTIME=0이면\n"
         "time 분기는 생략 — alarm 편성도 없다.\n"
         "current->signal이면 즉시 break(254-255).", 13)
    d.outline(p, 1100, 12500, 15200, 1900, K.ORANGE, 120)
    d.text(p, 1350, 12700, 14700, 1600,
           "EMPTY(secondary) ||\n"
           "  (L_CANON && !secondary.data && LEFT>20)\n"
           "→ sleep_if_empty — 줄이 완성(data≥1)돼야 돌려준다", 14, K.ORANGE, True)

    # ── 코드 25 tty_read (2) ───────────────────────────────────
    p = d.slide("tty_read (2): 복사와 반환", K.S_CODE,
                "tty_io.c:261-288 — GETCH → put_fs_byte · EOF 길이 0 · 시그널이면 -EINTR(285-286)")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 261, 272, 1100, 4400,
                 15200, 7750, size=10)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 273, 288, 16900, 4400,
                 15700, 9070, size=9)
    para(d, p, 1100, 12500, 15200, 1900,
         "· 10 또는 EOF를 만나 data-- (263-264)\n"
         "· EOF && ICANON → 그대로 반환 — 길이 0 가능, 사용자에겐 EOF(265-266)\n"
         "· 정규 모드에서 한 줄이라도 읽었으면 break(278-280)", 14)
    para(d, p, 16900, 13700, 15700, 700,
         "시그널으로 깨어나 0바이트면 -EINTR — 시연 B(35장)가 보여주는 값.", 13,
         K.ORANGE, True)

    # ── 코드 26 sleep/wake 대조 ────────────────────────────────
    p = d.slide("sleep_if_empty와 wake_up — 좌우 대조", K.S_CODE,
                "tty_io.c:122-128 · sched.c:167-186 · 188-193 — 잠든 쪽과 깨우는 쪽을 나란히 놓는다")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 122, 128, 1100, 4400,
                 15200, 5000, size=11)
    d.code_panel(p, "src/kernel/sched.c", 188, 193, 1100, 9600, 15200, 4450,
                 size=11)
    d.code_panel(p, "src/kernel/sched.c", 167, 186, 16900, 4400, 15700,
                 9950, size=8)
    para(d, p, 1100, 14250, 31500, 700,
         "wake_up은 proc_list가 가리키는 태스크 하나만 깨운다 — 나머지는 repeat 연쇄(sched.c:176-179). "
         "put_queue의 movl $0,(%ecx)(keyboard.S:106)도 같은 일이지만 0.11엔 read_q에 잠드는 코드가 없다(grep).", 12)

    # ── 상태도 27 핵심 4컷 ─────────────────────────────────────
    p = d.slide("핵심 그림: 'a'+Enter — 큐와 잠든 셸의 4컷", K.S_STATE,
                "오늘의 핵심 시각자료 — 큐의 head/tail/data와 셸 상태를 같이 본다 · 값은 도식(실측은 34·36장 캡처)")
    cuts = [
        ("① read() 직후 — 셸 잠듦", "세 큐 모두 head==tail · data=0",
         (E6[:], 0, 0, None), (E6[:], 0, 0, 0), (E6[:], 0, 0, "write_q"),
         ("셸 — TASK_INTERRUPTIBLE", "secondary.proc_list = 셸"),
         "tty_io.c:122-128 — sleep_if_empty 로\nsecondary.proc_list 에 매달려 잠든다"),
        ("② 'a' 입력 — read_q만", "IRQ 1 → put_queue",
         (["a"] + E6[1:], 1, 0, 0), (E6[:], 0, 0, 0), (E6[:], 0, 0, "write_q"),
         ("셸 — 잠든 채", "data=0 → 줄 미완성"),
         "keyboard.S:88-110 — buf[0]='a', head 0→1\nread_q.proc_list 비어 106행은 무동작"),
        ("③ copy_to_cooked — 이동", "do_tty_interrupt(0)",
         (E6[:], 1, 1, None), (["a"] + E6[1:], 1, 0, 0),
         (E6[:], 1, 1, "write_q — 에코 'a' → con_write"),
         ("wake_up → 조건 참 → 다시 잠듦", "data=0 — 24장 조건"),
         "tty_io.c:145-228 — read_q.tail++(GETCH)\nsecondary.head++(PUTCH) · data 0 유지"),
        ("④ Enter — data 1, 깨어남", "13 → 10 (ICRNL)",
         (E6[:], 0, 0, None), (["a", "\\n"] + E6[2:], 2, 0, 1),
         (E6[:], 1, 1, "write_q — 에코 \\n → 10·13"),
         ("셸 — TASK_RUNNING", "sys_read 반환 2 ('a','\\n')"),
         "151-153 13→10 · 210-211 data++ · 227 wake_up\n→ 261-272 GETCH → put_fs_byte, tail 0→2"),
    ]
    for ci, (ctitle, cevent, rq, sq, wq, task, caption) in enumerate(cuts):
        x = 1100 + ci * 8100
        d.text(p, x, 4250, 7700, 550, ctitle, 15, K.ORANGE, True)
        d.text(p, x, 4800, 7700, 400, cevent, 12, K.TEAL, True)
        qstrip(d, p, x, 5300, 7700, "read_q", rq[0], rq[1], rq[2], hot=rq[3])
        qstrip(d, p, x, 7350, 7700, "secondary", sq[0], sq[1], sq[2],
               data=sq[3], hot=0 if sq[3] == 0 and ci in (2,) else
               (1 if ci == 3 else None), data_hot=ci == 3)
        qstrip(d, p, x, 9550, 7700, wq[3], wq[0], wq[1], wq[2])
        nbox(d, p, x, 11800, 7700, 950, task[0], task[1],
             K.ORANGE if ci in (0, 3) else (K.PAPER if ci == 2 else None),
             s1=12, s2=10)
        para(d, p, x, 13000, 7700, 1500, caption, 11)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 상태도 28 글자의 위치 ──────────────────────────────────
    p = d.slide("상태 변화도 ①: 글자 한 개의 위치", K.S_STATE,
                "노드 4 + 에코 분기 1 — 전환마다 원인(코드)과 변경 데이터(head·tail·data·pos)를 붙인다")
    nodes = [("키보드 컨트롤러", "포트 0x60", None, 1100),
             ("read_q", "raw — 스캔→ASCII", K.TEAL, 9600),
             ("secondary", "cooked — 줄 단위", K.TEAL, 18100),
             ("사용자 버퍼", "put_fs_byte → read()", K.ORANGE, 26600)]
    for t, s, fill, x in nodes:
        nbox(d, p, x, 5300, 5200, 1300, t, s, fill,
             K.INK if fill else K.MUTED, s1=15, s2=10)
    trans = [("put_queue\n88-110", "read_q.head++"),
             ("copy_to_cooked\n145-228", "read_q.tail++\nsecondary.head++"),
             ("tty_read · GETCH\n261-272", "secondary.tail++\ndata--")]
    for i, (cause, data) in enumerate(trans):
        ax = 6300 + i * 8500
        d.text(p, ax, 4900, 1400, 900, "→", 30, K.ORANGE, True)
        d.text(p, ax - 900, 4300, 3100, 700, cause.split("\n")[0], 10, K.TEAL, True)
        d.text(p, ax - 900, 6750, 3100, 900, data, 10, K.ORANGE, True)
    d.text(p, 17700, 6700, 6600, 600, "L_ECHO(212) → write_q — 에코 분기", 10,
           K.TEAL, True)
    d.text(p, 20300, 7300, 1000, 600, "↓", 20, K.ORANGE, True)
    nbox(d, p, 17700, 7900, 6600, 1000, "write_q", "에코·출력 (tty_write가 씀)",
         K.TEAL, s1=14, s2=10)
    d.text(p, 24300, 8000, 1700, 600, "→", 26, K.ORANGE, True)
    d.text(p, 24250, 7500, 2300, 500, "con_write", 10, K.ORANGE, True)
    nbox(d, p, 26000, 7900, 6600, 1000, "VGA 텍스트 메모리", "0xb8000 — 문자+attr 2바이트",
         K.PAPER, s1=13, s2=10)
    d.table(p, 1100, 9600, [6600, 11400, 12500], [
        ["상태(큐)", "유지 조건 — 머무는 이유", "근거"],
        ["read_q", "FULL이면 새 글자 폐기 — 알림 없음", "put_queue je 3f (keyboard.S:96-97)"],
        ["secondary", "FULL(secondary)이면 read_q에 남는다", "copy_to_cooked 루프 조건 (149)"],
        ["잠든 태스크", "EMPTY면 대기 — 줄 완성까지", "sleep_if_empty (tty_io.c:122-128)"],
    ], row_h=850, size=13)
    d.banner(p, "한 글자는 두 번 저장된다 — read_q(raw)와 secondary(cooked), 에코는 write_q까지 세 번", 13300, 16)

    # ── 상태도 29 태스크 상태 ──────────────────────────────────
    p = d.slide("상태 변화도 ②: read()를 부른 태스크", K.S_STATE,
                "5·10회차 상태도 표기 재사용 — 캡처 34·36·38장이 전환 ①·②를 재지시한다")
    nbox(d, p, 1100, 5300, 8800, 1500, "TASK_RUNNING",
         "셸이 read(0, buf, 80) 호출 — sys_read → tty_read 진입", K.TEAL,
         s1=17, s2=11)
    arrow(d, p, 10150, 5750, "→", 30, K.ORANGE)
    nbox(d, p, 12100, 5300, 8800, 1500, "TASK_INTERRUPTIBLE",
         "secondary.proc_list = current — 큐에 매달림", K.PAPER, s1=17, s2=11)
    d.text(p, 1100, 7060, 20000, 500,
           "RUNNING → INTERRUPTIBLE : sleep_if_empty (tty_io.c:122-128) — cli 후 while(!signal && EMPTY)",
           12, K.TEAL, True)
    arrow(d, p, 21150, 5750, "→", 30, K.ORANGE)
    nbox(d, p, 23100, 5300, 9500, 1500, "TASK_RUNNING",
         "sys_read 반환 — put_fs_byte로 채운 buf", K.TEAL, s1=17, s2=11)
    causes = [
        ("① wake_up(&secondary.proc_list)", "copy_to_cooked 끝 — tty_io.c:227"),
        ("② 시그널 보유 시 schedule()", "sched.c:117-119 — ^C면 -EINTR"),
        ("③ (VTIME 사용 시) alarm", "tty_read 250-252 — 기본값으론 미사용"),
    ]
    for i, (t, s) in enumerate(causes):
        nbox(d, p, 1100, 7600 + i * 1300, 20000, 1150, t, s,
             K.ORANGE if i == 0 else K.PAPER, s1=14, s2=11)
    d.outline(p, 22100, 7600, 10500, 3750, K.ORANGE, 110)
    d.text(p, 22350, 7850, 10000, 800, "유지 조건", 16, K.ORANGE, True)
    para(d, p, 22350, 8750, 10000, 2400,
         "줄 미완성 && 시그널 없음\n\nEMPTY || (L_CANON && !data && LEFT>20) — 참인 동안 계속 잠든다", 14)
    para(d, p, 1100, 11800, 31500, 2400,
         "전환 ①은 Enter가 줄을 완성할 때(27장 ④컷), ②는 ^C(22장) — 두 경로 모두 시연 B(35·36장)로 실측한다.\n"
         "wake_up은 태스크 하나만 깨운다 — 나머지는 interruptible_sleep_on의 repeat 연쇄(sched.c:176-179, §8).", 14)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 비교 30 참조 플래그 ────────────────────────────────────
    p = d.slide("비교 ①: termios 플래그 — 실제로 참조되는 것", K.S_CMP,
                "tty_io.c:28-49의 검사 매크로 + 사용처(grep 근거) + 콘솔 초기값 — 이 표가 기준이다(§8)")
    d.table(p, 1100, 4300, [5000, 8200, 11600, 5600], [
        ["플래그", "검사 매크로 (tty_io.c)", "사용 함수", "콘솔 초기값"],
        ["ICRNL", "I_CRNL (42)", "copy_to_cooked 151-153 — 13→10", "켬"],
        ["INLCR", "I_NLCR (41)", "copy_to_cooked 157-158 — 10→13", "끔"],
        ["IGNCR", "I_NOCR (43) — 이름 주의", "copy_to_cooked 154-155 — 폐기", "끔"],
        ["IUCLC", "I_UCLC (40)", "copy_to_cooked 159-160 — tolower", "끔"],
        ["OPOST", "O_POST (45)", "tty_write 304 — 출력 후처리 총 스위치", "켬"],
        ["ONLCR", "O_NLCR (46)", "tty_write 309-313 — \\n 앞에 13", "켬"],
        ["OCRNL", "O_CRNL (47)", "tty_write 305-306 — \\r→\\n", "끔"],
        ["ONLRET", "O_NLRET (48)", "tty_write 307-308 — \\n→\\r", "끔"],
        ["OLCUC", "O_LCUC (49)", "tty_write 314-315 — 대문자화", "끔"],
        ["ISIG", "L_ISIG (33)", "copy_to_cooked 200-209 — ^C·^\\", "켬"],
        ["ICANON", "L_CANON (32)", "161 · 256-257 · 265 · 278 — 정규 모드", "켬"],
        ["ECHO", "L_ECHO (34)", "167 · 182 · 212 — 에코 총 스위치", "켬"],
        ["ECHOCTL", "L_ECHOCTL (37)", "copy_to_cooked 217-220 — ^X 표기", "켬"],
    ], row_h=660, size=12)
    d.banner(p, "iflag 4 + oflag 5 + lflag 4 — 이 13개만 코드가 본다", 13800, 16)

    # ── 비교 31 선언만 된 플래그 ───────────────────────────────
    p = d.slide("비교 ①: termios 플래그 — 선언만 된 것", K.S_CMP,
                "include/termios.h:83-106 · 169-183 — 헤더의 전체 목록은 '0.11 지원 기능 목록'이 아니다(§8)")
    auto_pane(d, p, 1100, 4300, 15200, 4600,
              "매크로는 있으나 호출 없음 — tty_io.c:35-38",
              "L_ECHOE(tty)   /* 35 */\n"
              "L_ECHOK(tty)   /* 36 */\n"
              "L_ECHOKE(tty)  /* 38 */\n"
              "\n"
              "grep L_ECHOE → 정의 한 곳뿐, 사용처 없음\n"
              "L_ECHOK · L_ECHOKE 도 같다\n"
              "\n"
              "단 ECHOKE는 콘솔 초기 lflag 에 켜져 있다(56행) —\n"
              "켜져 있어도 검사하는 코드가 없으니 아무 일도 하지 않는다", 12)
    auto_pane(d, p, 16900, 4300, 15700, 4600,
              "매크로조차 없음 — termios.h 선언만",
              "c_iflag: IGNBRK BRKINT IGNPAR PARMRK\n"
              "         INPCK ISTRIP IXON IXANY IXOFF IMAXBEL\n"
              "c_lflag: XCASE ECHONL NOFLSH TOSTOP ECHOPRT\n"
              "         FLUSHO PENDIN IEXTEN\n"
              "c_oflag: OFILL OFDEL ONOCR + 지연 비트\n"
              "         (NLDLY CRDLY TABDLY ...)\n"
              "\n"
              "0.11 코드(tty_io.c)에는 이들을 검사하는\n"
              "매크로 자체가 존재하지 않는다", 12)
    d.text(p, 1100, 9020, 31500, 400,
           "선언됐다 ≠ 동작한다 — 판정은 grep이다 (참조 13개 목록은 30장)", 15,
           K.ORANGE, True)
    d.table(p, 1100, 9500, [7600, 11800, 11100], [
        ["그룹", "선언(termios.h)", "0.11에서의 실체"],
        ["ERASE 계열 에코", "ECHOE · ECHOK · ECHOKE", "매크로만(35-38) — ERASE 에코는 L_ECHO만 본다(182-187)"],
        ["흐름 제어", "IXON · IXOFF · IXANY", "미참조 — ^S/^Q는 stopped 값 변경뿐(21장)"],
        ["입력 정제", "ISTRIP · INPCK · PARMRK · …", "미참조 — 패리티·비트 스트립 없음"],
        ["기타 lflag", "ECHONL · NOFLSH · TOSTOP · IEXTEN · …", "미참조 — 기능 없음"],
    ], row_h=950, size=12)

    # ── 비교 32 c_cc ───────────────────────────────────────────
    p = d.slide("비교 ①-보충: c_cc 제어 문자 — INIT_C_CC 해석", K.S_CMP,
                "include/linux/tty.h:36-43(매크로) · 57-63(기본값) — copy_to_cooked가 쓰는 7개와 선언만 1개")
    d.table(p, 1100, 4300, [4200, 4200, 3800, 7600, 10700], [
        ["문자", "기본값", "표기", "copy_to_cooked 사용처", "상태"],
        ["VINTR", "\\003", "^C", "201 — INTR_CHAR → tty_intr", "사용"],
        ["VQUIT", "\\034", "^\\", "205 — QUIT_CHAR → tty_intr", "사용"],
        ["VERASE", "\\177", "DEL", "177 — head 한 칸 DEC", "사용"],
        ["VKILL", "\\025", "^U", "162 — 줄 시작까지 DEC", "사용"],
        ["VEOF", "\\004", "^D", "210 · 263 · 265 — data·즉시 반환", "사용"],
        ["VSTART", "\\021", "^Q", "195 — stopped=0", "사용"],
        ["VSTOP", "\\023", "^S", "191 — stopped=1", "사용"],
        ["VSUSP", "\\032", "^Z", "없음 — SUSPEND_CHAR(tty.h:43) 매크로만", "선언만"],
    ], row_h=760, size=13)
    auto_pane(d, p, 22000, 4300, 10600, 4200,
              "INIT_C_CC — tty.h:63 원문",
              "\"\\003\\034\\177\\025\\004\\0\\1\\0\n"
              " \\021\\023\\032\\0\\022\\017\\027\\026\\0\"\n"
              "\n"
              "^X 표기 = 'X' − 64\n"
              "^C = 0x43 − 0x40 = 0x03\n"
              "DEL(\\177)은 문자 아닌 0x7f — do_self 결과 그대로", 12)
    para(d, p, 22000, 8800, 10600, 3000,
         "VTIME(\\0)·VMIN(\\1)도 이 배열 한가운데 있다(tty_read 240-241) —\n"
         "기본값에선 비활성 분기(24장).\n\n"
         "사용자는 ioctl TCSETS로 이 값을 바꾼다 — 시연 C(37장).", 14)
    para(d, p, 1100, 11200, 19700, 2000,
         "SUSPEND(^Z)는 매크로만 — VSUSP 배열 칸은 있지만 읽는 코드가 없다.\n"
         "tty_io.c:21의 TSTPMASK 선언도 결국 쓰이지 않는다(grep) — 시그널 구현은 SIGINT·SIGQUIT뿐.", 14)

    # ── 시연 33 A ──────────────────────────────────────────────
    p = d.slide("시연 A: 키 하나의 여정 (GDB)", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 줄 번호는 lab 기준(src와 다를 수 있음) · 키 입력은 QEMU 창 포커스 필요")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — 중단점 3개와 'a' 한 번",
              "# lab/: make debug → gdb tools/system → target remote :1234 → c\n"
              "(gdb) b keyboard_interrupt\n"
              "(gdb) b copy_to_cooked\n"
              "(gdb) b tty_read\n"
              "(gdb) c              # QEMU 창을 클릭해 포커스!\n"
              "# 셸 프롬프트에서 'a' 한 번\n"
              "Breakpoint 1, 0x2a7c in keyboard_interrupt ()\n"
              "# 어셈블리 심벌 — break 되지만 소스 줄 표시 없음\n"
              "(gdb) b put_queue ; c\n"
              "Breakpoint 2, 0x2b1f in put_queue ()\n"
              "(gdb) p/x $al\n"
              "$1 = 0x1e           # 'a' make — 다음 정지는 0x9e(break→none)\n"
              "(gdb) finish ; p tty_table[0].read_q.head\n"
              "$2 = 1              # head 0→1 — 한 번만 전진\n"
              "(gdb) c\n"
              "Breakpoint 3, copy_to_cooked (tty=0x5d44)\n"
              "    at chr_drv/tty_io.c:145\n"
              "(gdb) n             # 루프 한 바퀴 통과\n"
              "(gdb) p tty->secondary.head ; p tty->secondary.data ; p tty->write_q.head\n"
              "$3 = 1  $4 = 0  $5 = 1\n"
              "(gdb) c             # tty_read 는 아직 — Enter 전까지 안 걸린다", 12)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· put_queue 후 read_q.head = 1\n"
         "· copy_to_cooked 후 secondary.head = 1\n"
         "· data = 0 유지 — 줄 미완성\n"
         "· write_q.head = 1 — 에코 분기\n"
         "· tty_read 중단점은 안 걸림(잠든 채)\n\n"
         "관찰 vs 추론 — head·data 값은 관찰,\n"
         "\"Enter 전까지 셸이 잠들어 있다\"는 코드 추론.\n\n"
         "주의 — GDB가 멈춘 동안 누른 키의 break 코드가\n"
         "뒤늦게 도착해 keyboard_interrupt가 두 번 걸린다\n"
         "(두 번째는 none — 15장).\n"
         "심벌 밑줄(_keyboard_interrupt) 접두는\n"
         "lab 툴체인 기준으로 확인(§11).", 14)

    # ── 캡처 34 ────────────────────────────────────────────────
    p = d.slide("시연 A 캡처 — 기대 출력", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜는 캡처 시 기입 — 관찰(head·data 값)과 추론(셸 잠듦)을 구분해 게시")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) b keyboard_interrupt ; c\n"
                         "Breakpoint 1, 0x2a7c in keyboard_interrupt ()\n"
                         "# QEMU 창에서 'a'\n"
                         "Breakpoint 1, 0x2a7c in keyboard_interrupt ()\n"
                         "(gdb) b put_queue ; c\n"
                         "Breakpoint 2, 0x2b1f in put_queue ()\n"
                         "(gdb) p/x $al\n"
                         "$1 = 0x1e        # 'a' make 스캔 코드\n"
                         "(gdb) finish\n"
                         "(gdb) p tty_table[0].read_q.head ; .tail\n"
                         "$2 = 1  $3 = 0   # head 0→1 전진",
                         "01-keyboard-interrupt-scan-code.png")
    d.placeholder_output(p, 16900, 4150, 15700, 5000,
                         "(gdb) b copy_to_cooked ; c\n"
                         "Breakpoint 3, copy_to_cooked (tty=0x5d44) :145\n"
                         "(gdb) p tty_table[0].secondary.head ; .data\n"
                         "$4 = 0  $5 = 0\n"
                         "(gdb) n ×8      # 루프 한 바퀴\n"
                         "(gdb) p tty_table[0].secondary.head ; .data\n"
                         "$6 = 1  $7 = 0  # 이동 · data 유지\n"
                         "(gdb) p tty_table[0].write_q.head\n"
                         "$8 = 1          # 에코 분기",
                         "02-copy-to-cooked-secondary.png")
    d.placeholder_output(p, 16900, 9350, 15700, 5100,
                         "# Enter 입력 — 13 → 10 (ICRNL)\n"
                         "Breakpoint 4, tty_read (channel=0, buf=0x…, nr=80)\n"
                         "    at chr_drv/tty_io.c:230\n"
                         "(gdb) p tty_table[0].secondary.data\n"
                         "$9 = 1          # 완성된 줄 수\n"
                         "(gdb) finish\n"
                         "Value returned is 2\n"
                         "                # 'a','\\n' 두 바이트 — sys_read 반환",
                         "03-enter-tty-read-return.png")

    # ── 시연 35 B ──────────────────────────────────────────────
    p = d.slide("시연 B: Enter와 깨어남 · ^C와 -EINTR", K.S_DEMO,
                "tty_io.c:200-228 · 111-120 · sched.c:117-119 — 상태 변화도 ②의 전환 ①·②를 실측한다")
    auto_pane(d, p, 1100, 4300, 19700, 10100,
              "GDB — (1) Enter·깨어남 (2) ^C",
              "# (1) Enter 와 깨어남 — wake_up 직후\n"
              "(gdb) b tty_io.c:227 ; delete 1 2 3 4 ; c\n"
              "# QEMU 창에서 Enter\n"
              "Breakpoint 5, copy_to_cooked (tty=0x5d44) :227\n"
              "(gdb) p tty_table[0].secondary.data\n"
              "$10 = 1            # 완성된 줄 수\n"
              "(gdb) p task[4]->state\n"
              "$11 = 0            # 셸 TASK_RUNNING — 깨어남\n"
              "\n"
              "# (2) cat 실행 후 ^C\n"
              "(gdb) b tty_intr ; b do_signal ; disable 5 ; c\n"
              "# 셸에서 cat 실행 → QEMU 창에서 Ctrl-C\n"
              "Breakpoint 6, tty_intr (tty=0x5d44, mask=2)\n"
              "    at chr_drv/tty_io.c:111\n"
              "(gdb) p tty->pgrp ; p/x task[4]->signal\n"
              "$12 = 35  $13 = 0x2   # INTMASK = 1<<(SIGINT-1) = 2\n"
              "(gdb) c\n"
              "Breakpoint 7, do_signal (signr=2, ...) at kernel/signal.c\n"
              "# 기대: cat 종료, 프롬프트 복귀\n"
              "# ^C 글자(0x03)는 read 로는 전달되지 않는다", 12)
    para(d, p, 22000, 4300, 10000, 10100,
         "(1) 관찰\n\n"
         "· secondary.data = 1\n"
         "· task 상태 0 — wake_up 실측\n\n"
         "(2) 관찰\n\n"
         "· tty_intr mask=2(SIGINT)\n"
         "· signal 비트 0x2 세트\n"
         "· do_signal signr=2 — cat 종료\n\n"
         "추론(코드) — ^C 글자는 continue로\n"
         "secondary에 들어가지 않는다(200-204).\n"
         "읽던 태스크는 시그널로 깨어나\n"
         "0바이트면 -EINTR(285-286).\n\n"
         "cat 이 없으면 sh 의 read 대기로\n"
         "같은 절차를 밟는다(§11).", 14)

    # ── 캡처 36 ────────────────────────────────────────────────
    p = d.slide("시연 B 캡처 — 기대 출력", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜는 캡처 시 기입 — 상태 변화도 ②의 전환 ①(wake_up)·②(시그널) 컷")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "(gdb) b tty_io.c:227 ; c      # Enter\n"
                         "Breakpoint 5, copy_to_cooked (tty=0x5d44)\n"
                         "    at chr_drv/tty_io.c:227\n"
                         "(gdb) p tty_table[0].secondary.data\n"
                         "$10 = 1        # 0 → 1 (210-211)\n"
                         "(gdb) p task[4]->state\n"
                         "$11 = 0        # TASK_RUNNING\n"
                         "(gdb) p tty_table[0].secondary.tail\n"
                         "$12 = 0        # 아직 안 읽음 — 깨어나서 읽는다\n"
                         "(gdb) finish\n"
                         "Value returned is 2             # 'a','\\n'",
                         "04-enter-wake-secondary-data.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) b tty_intr ; b do_signal ; c\n"
                         "# cat 실행 → QEMU 창에서 Ctrl-C\n"
                         "Breakpoint 6, tty_intr (tty=0x5d44, mask=2) :111\n"
                         "(gdb) p tty->pgrp\n"
                         "$13 = 35       # 전경 pgrp\n"
                         "(gdb) p/x task[4]->signal\n"
                         "$14 = 0x2      # SIGINT 비트 — pgrp 같은 모두\n"
                         "(gdb) c\n"
                         "Breakpoint 7, do_signal (signr=2, ...)\n"
                         "# QEMU 화면: cat 이 죽고 프롬프트 복귀\n"
                         "# 관찰: ^C 글자가 에코되지 않고(ECHOCTL 표기 없음)\n"
                         "#       read 로도 전달되지 않는다 — 시그널 경로만",
                         "05-sigint-tty-intr-do-signal.png")
    para(d, p, 1100, 14600, 31500, 1600,
         "왼쪽(04) = 상태 변화도 ②의 전환 ① wake_up · 오른쪽(05) = 전환 ② 시그널 — \"시그널이 secondary에 들어가지 않는다\"는 "
         "코드 추론(200-204 continue)이고, cat 종료·^C 미전달은 관찰이다.", 13)

    # ── 시연 37 C ──────────────────────────────────────────────
    p = d.slide("시연 C: ioctl로 ECHO 끄기", K.S_DEMO,
                "tty_ioctl.c:56-74(get/set_termios) · 126-133(TCGETS/TCSETS) — stty 없이 20줄 프로그램으로")
    auto_pane(d, p, 1100, 4300, 15200, 10100,
              "noecho.c — 게스트 gcc (없으면 사전 빌드 바이너리 투입)",
              "#include <termios.h>\n"
              "#include <unistd.h>\n"
              "\n"
              "int main(void)\n"
              "{\n"
              "    struct termios t;\n"
              "    char buf[100];\n"
              "    ioctl(0, TCGETS, &t);   /* 1. 현재 값 */\n"
              "    t.c_lflag &= ~ECHO;     /* 2. ECHO 비트 끄기 */\n"
              "    ioctl(0, TCSETS, &t);   /* 3. 다시 설정 */\n"
              "    read(0, buf, sizeof buf); /* 4. 한 줄 — 화면엔 안 보임 */\n"
              "    ioctl(0, TCGETS, &t);\n"
              "    t.c_lflag |= ECHO;      /* 5. 복원 */\n"
              "    ioctl(0, TCSETS, &t);\n"
              "    return 0;\n"
              "}", 12)
    auto_pane(d, p, 16900, 4300, 15700, 6300,
              "GDB — c_lflag 전후",
              "(gdb) b set_termios ; c\n"
              "Breakpoint 8, set_termios (tty=0x5d44, ...) :66\n"
              "(gdb) p/x tty->termios.c_lflag\n"
              "$15 = 0xa0b\n"
              "# ISIG|ICANON|ECHO|ECHOCTL|ECHOKE\n"
              "#  = 01|02|010|01000|04000 (8진)\n"
              "(gdb) finish ; c        # 프로그램이 TCSETS\n"
              "Breakpoint 8, set_termios (tty=0x5d44, ...) :66\n"
              "(gdb) p/x tty->termios.c_lflag\n"
              "$16 = 0xa03             # ECHO(010) 꺼짐", 12)
    para(d, p, 16900, 10900, 15700, 3500,
         "경로 — ioctl(0,TCGETS) → tty_ioctl(115)\n"
         "  MAJOR 5(/dev/tty) → current->tty(121)\n"
         "  → get_termios(56-64) / set_termios(66-74)\n\n"
         "기대 — 입력 중 화면 비에코 → Enter 후 줄 출력 → 복원 후 재에코.\n"
         "gcc가 없으면 사전 빌드 바이너리 투입 또는 사전 캡처\n"
         "build/qemu-13-noecho.png(\"기존 기록\" 라벨)로 대체(§11).", 13)

    # ── 캡처 38 ────────────────────────────────────────────────
    p = d.slide("시연 C 캡처 — 기대 출력", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음(사전 캡처는 \"기존 기록\" 라벨) · 캡처 날짜는 캡처 시 기입")
    d.placeholder_output(p, 1100, 4150, 15200, 10300,
                         "# ./noecho\n"
                         "(입력하는 동안 화면에 아무 것도 안 뜬다)\n"
                         "hello\n"
                         "#                ← Enter 후 비로소 줄이 출력되고\n"
                         "                   프롬프트 복귀 — 복원 후에는 다시 에코된다\n"
                         "\n"
                         "QEMU 화면 관찰\n"
                         "· 입력 중 비에코 — c_lflag ECHO 비트 꺼짐\n"
                         "· Enter 후 출력 — read 가 돌아온 뒤 프로그램이 출력\n"
                         "· 복원 후 재에코 — ECHO 비트 복귀",
                         "06-noecho-ioctl-screen.png")
    d.placeholder_output(p, 16900, 4150, 15700, 10300,
                         "(gdb) b set_termios ; c\n"
                         "Breakpoint 8, set_termios (tty=0x5d44, ...) :66\n"
                         "(gdb) p/x tty->termios.c_lflag\n"
                         "$15 = 0xa0b       # ISIG|ICANON|ECHO|ECHOCTL|ECHOKE\n"
                         "(gdb) finish ; c\n"
                         "Breakpoint 8, set_termios (tty=0x5d44, ...) :66\n"
                         "(gdb) p/x tty->termios.c_lflag\n"
                         "$16 = 0xa03       # ECHO(010) 비트만 꺼짐\n"
                         "\n"
                         "관찰 = c_lflag 값 변화 · 추론 = \"에코를 꺼도 입력은\n"
                         "큐에 그대로 쌓인다\" — L_ECHO 분기만 건너뛸 뿐",
                         "07-set-termios-clflag.png")

    # ── 코드 39 출력 경로 ──────────────────────────────────────
    p = d.slide("출력 경로: write() → tty_write", K.S_CODE,
                "fs/read_write.c:83-96 · fs/char_dev.c:16-32·85-104 · tty_io.c:290-326 — OPOST/ONLCR와 sleep_if_full")
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 298, 313, 1100, 4400,
                 15200, 9070, size=9)
    d.code_panel(p, "src/kernel/chr_drv/tty_io.c", 314, 326, 16900, 4400,
                 15700, 7585, size=9)
    para(d, p, 16900, 12200, 15700, 2200,
         "ONLCR — '\\n' 앞에 13을 먼저 PUTCH(cr_flag)\n"
         "cr_flag는 static(292) — tty끼리 공유되는 잔재\n\n"
         "sleep_if_full(299) — write_q가 가득이면 잠든다\n"
         "남았으면 schedule()(323) — con_write가 비워줄 때까지", 13)
    para(d, p, 1100, 13650, 31500, 800,
         "sys_write(read_write.c:83-96) → rw_char(char_dev.c:95-104) → rw_ttyx(21-25) → tty_write(290) → tty->write(tty) = con_write", 14)

    # ── 코드 40 con_write ──────────────────────────────────────
    p = d.slide("con_write: VGA 텍스트 메모리에 쓰기", K.S_CODE,
                "console.c:445-471(state 0) · set_cursor 604 · ESC 시퀀스(state 1/2)는 범위 밖 — 간단 언급만")
    d.code_panel(p, "src/kernel/chr_drv/console.c", 445, 462, 1100, 4400,
                 15200, 9070, size=8)
    d.code_panel(p, "src/kernel/chr_drv/console.c", 463, 471, 16900, 4400,
                 15700, 6100, size=10)
    d.shape(p, 17200, 11000, 3000, 1100, K.TEAL)
    d.text(p, 17300, 11300, 2800, 600, "0x61  'a'", 15, K.INK, True)
    d.text(p, 20300, 11300, 900, 600, "+", 20, K.ORANGE, True)
    d.shape(p, 21300, 11000, 3000, 1100, K.TEAL)
    d.text(p, 21400, 11300, 2800, 600, "0x07  attr", 15, K.INK, True)
    d.text(p, 24500, 11050, 8200, 1000,
           "= pos 한 칸(2바이트) — movw %ax,(pos)\npos += 2 · x++", 13, K.ORANGE, True)
    para(d, p, 16900, 12400, 15700, 2100,
         "10·11·12 → lf() · 13 → cr() · DEL → del()\n8 → 백스페이스 · 9 → 탭 · 7 → sysbeep()\n"
         "27(ESC) → state 1 — ANSI 시퀀스 해석(범위 밖)\n루프 끝 set_cursor()(604) — 하드웨어 커서 동기화", 13)

    # ── 코드 41 con_init ───────────────────────────────────────
    p = d.slide("con_init: 화면 종류 판별과 인터럽트 등록", K.S_CODE,
                "console.c:39-47(ORIG_*) · 629-644(판별) · 682-687(등록) — 3회차 부팅 화면 우상단의 4문자가 여기서 온다")
    d.code_panel(p, "src/kernel/chr_drv/console.c", 39, 47, 1100, 4400,
                 14500, 6150, size=10)
    d.code_panel(p, "src/kernel/chr_drv/console.c", 629, 644, 15900, 4400,
                 16300, 8190, size=8)
    para(d, p, 1100, 10800, 14500, 2300,
         "ORIG_* 는 setup.s가 0x90000에 남긴 값(2회차) —\n"
         "ORIG_VIDEO_MODE==7이면 단색(0xb0000), 아니면 색(0xb8000).\n"
         "display_desc(\"EGAc\" 등)를 화면 우상단에 직접 쓴다(668-675) —\n"
         "3회차 부팅 캡처의 우상단 4문자가 바로 이것.", 13)
    nbox(d, p, 1100, 13300, 14500, 1100,
         "gotoxy → set_trap_gate(0x21,…) → PIC 해제 → 0x61 리셋",
         "682-687 — 12장의 등록 코드, con_init 의 마지막", K.PAPER, s1=12, s2=11)
    para(d, p, 15900, 12900, 16300, 1500,
         "video_mem_end 는 종류별로 다르다 — 0xb8000(EGAm) · 0xb2000(MDA) · 0xbc000(EGAc) · 0xba000(CGA).\n"
         "스크롤·커서 계산의 기준이 되는 정적 변수들(58-76)이 여기서 한 번 정해진다.", 13)

    # ── 코드 42 printk ─────────────────────────────────────────
    p = d.slide("printk도 같은 길", K.S_CODE,
                "kernel/printk.c:21-41 — vsprintf 후 fs를 커널 데이터로 바꿔 _tty_write(0,…) 호출")
    d.code_panel(p, "src/kernel/printk.c", 21, 28, 1100, 4400, 15200, 6100,
                 size=10)
    d.code_panel(p, "src/kernel/printk.c", 29, 41, 1100, 10800, 15200, 3650,
                 size=9)
    para(d, p, 16900, 4400, 15700, 5600,
         "push %fs / push %ds / pop %fs —\n"
         "fs를 사용자 데이터에서 커널 데이터로.\n"
         "그래야 tty_write 의 get_fs_byte 가\n"
         "커널 버퍼 buf 를 읽는다.\n\n"
         "_tty_write(0, buf, i) — channel 0 = 콘솔.\n"
         "커널 메시지는 곧 콘솔 tty_write 다.", 14)
    d.outline(p, 16900, 10300, 15700, 4100, K.ORANGE, 110)
    d.text(p, 17150, 10550, 15200, 3600,
           "주의 — tty_write는 잠들 수 있다\n"
           "sleep_if_full(&write_q)(299) — 인터럽트 문맥의 printk 는\n"
           "잠재적으로 위험하다(실제로 write_q가 가득 찰 일은 드물다).\n"
           "15회차에서 이 경고가 다시 쓰인다.", 14, K.ORANGE, True)
    d.banner(p, "커널 메시지와 사용자 출력이 같은 큐·같은 함수를 쓴다 — write_q → con_write")

    # ── 비교 43 tty_ioctl ──────────────────────────────────────
    p = d.slide("비교 ②: tty_ioctl의 명령 — 구현 / 부분 / 미구현", K.S_CMP,
                "tty_ioctl.c:115-204 — cmd 전체(TCGETS…TIOCSSOFTCAR) 분류 · MAJOR 5는 current->tty(121)")
    d.table(p, 1100, 4300, [4200, 16200, 10100], [
        ["분류", "명령", "내용 · 근거"],
        ["구현", "TCGETS · TCSETS · TCSETSW · TCSETSF\nTCGETA · TCSETA · TCSETAW · TCSETAF",
         "get/set_termios(56-107) — TCSETSF/AF는 flush 먼저"],
        ["구현", "TCFLSH · TIOCGPGRP · TIOCSPGRP\nTIOCOUTQ · TIOCINQ",
         "flush · pgrp 읽기/쓰기 · 큐 길이(CHARS)"],
        ["부분", "TCSBRK", "wait_until_sent·send_break가 빈 함수(46-54) — 항상 0 반환"],
        ["미구현 -EINVAL", "TCXONC · TIOCEXCL · TIOCNXCL · TIOCSCTTY\nTIOCSTI · TIOCGWINSZ · TIOCSWINSZ",
         "\"not implemented\" 주석 그대로"],
        ["미구현 -EINVAL", "TIOCMGET · TIOCMBIS · TIOCMBIC · TIOCMSET\nTIOCGSOFTCAR · TIOCSSOFTCAR (+ default)",
         "\"not implemented\" 주석 그대로"],
    ], row_h=1500, size=12)
    para(d, p, 1100, 13500, 31500, 1000,
         "termios 구조체는 17바이트 통째로 바이트 복사(56-74) — 검증 없이 사용자 값을 그대로 믿는다.", 14)
    d.banner(p, "선언된 명령 27개 중 온전히 동작하는 묶음은 절반 — \"선언됐다 ≠ 동작한다\" 또 한 번", 14600, 16)

    # ── 비교 44 MAJOR ──────────────────────────────────────────
    p = d.slide("비교 ③: 문자 장치 MAJOR 0~7 — crw_table[]", K.S_CMP,
                "fs/char_dev.c:85-104 · rw_tty 27-32(-EPERM) · open 결속 fs/open.c:165-170")
    d.table(p, 1100, 4300, [3000, 6400, 21100], [
        ["MAJOR", "핸들러", "내용"],
        ["0", "NULL", "nodev — rw_char이 -ENODEV(99)"],
        ["1", "rw_memory", "ram/mem/kmem은 -EIO · null은 0 채움 · port만 실제 동작"],
        ["2", "NULL", "/dev/fd — 플로피 문자 접근 없음"],
        ["3", "NULL", "/dev/hd — 하드는 블록 장치로만(11회차)"],
        ["4", "rw_ttyx", "tty_read/tty_write(minor 직접) — /dev/tty0 · /dev/ttyS0…"],
        ["5", "rw_tty", "current->tty 사용 — 없으면 -EPERM(27-32) · /dev/tty"],
        ["6", "NULL", "/dev/lp — 프린터 미구현"],
        ["7", "NULL", "unnamed pipes — 파이프는 파일 계층(12회차)"],
    ], row_h=850, size=13)
    para(d, p, 1100, 12300, 31500, 2400,
         "open.c:165-170 — 세션 리더가 MAJOR 4 장치를 열면 current->tty = MINOR, tty_table[MINOR].pgrp = current->pgrp.\n"
         "이 결속이 ^C(tty_intr, 22장)의 대상을 정한다 — 디스패치의 마지막 조각.\n"
         "NULL 다섯 개(0·2·3·6·7)는 핸들러 등록 자체가 없다 — 이 표가 곧 지원 목록이다.", 14)

    # ── 배경 45 rs ─────────────────────────────────────────────
    p = d.slide("rs와 콘솔의 차이 (짧게)", K.S_BG,
                "kernel/chr_drv/serial.c:53-59 — 인터럽트 기반 출력은 rs뿐 · rs_io.s 상세는 범위 밖(§8)")
    d.code_panel(p, "src/kernel/chr_drv/serial.c", 53, 59, 1100, 4400, 15200,
                 5000, size=11)
    d.cards(p, [
        ("con_write — 동기", "호출 즉시 VGA 메모리에\n다 그리고 돌아온다(40장)\n\n콘솔 출력은 인터럽트\n기반이 아니다(§8)"),
        ("rs_write — 비동기", "큐에 글자가 있으면\nUART 송신 인터럽트만\n켠다(outb IER bit1)\n\n나머지는 rs_io.s가\n(범위 밖)"),
    ], y=9800, h=4600)
    para(d, p, 16900, 4400, 15700, 5000,
         "같은 tty_write가 tty->write 함수 포인터\n하나로 두 장치를 다룬다(10장).\n\n"
         "포인터가 채워지는 곳 — tty_table 초기값:\n"
         "콘솔 = con_write(61) · rs = rs_write(74·87).\n\n"
         "read_q.data에 포트 주소를 숨겨 두는\n재활용(75·88 — 0x3f8/0x2f8)도 rs 만의 버릇.", 14)
    d.banner(p, "동기(콘솔) · 비동기(rs) — 선택은 장치 성질이, 인터페이스는 tty_write 가 같게")

    # ── 정답 46 ────────────────────────────────────────────────
    p = d.slide("핵심 질문의 답: 전체 경로", K.S_ANS,
                "keyboard.S:37-110 · tty_io.c:145-288 · read_write.c:55-80 — 각 화살표에 파일:줄 (27장 4컷의 압축판)")
    left = [("키보드 — 'a' 누름", "IRQ 1 · make 0x1E", None),
            ("keyboard_interrupt", "inb $0x60 → key_table(,%eax,4) — keyboard.S:37-53", K.PAPER),
            ("do_self → put_queue", "read_q.buf[0]='a' · head 0→1 — 453-484 · 88-110", K.PAPER),
            ("do_tty_interrupt(0)", "→ copy_to_cooked(&tty_table[0]) — tty_io.c:342-345", K.PAPER)]
    right = [("copy_to_cooked", "GETCH read_q · ICRNL 13→10 · PUTCH secondary · data++ · 에코→write_q→con_write — 145-228", K.TEAL),
             ("wake_up", "&secondary.proc_list — 셸 state=0 — 227", K.ORANGE),
             ("tty_read", "GETCH secondary → put_fs_byte(사용자 buf) — 261-272", K.ORANGE),
             ("sys_read 반환 2", "read() = 2 — 'a','\\n' — fs/read_write.c:55", K.ORANGE)]
    for i, (t, s, fill) in enumerate(left):
        nbox(d, p, 1100, 4300 + i * 2050, 15200, 1250, t, s, fill,
             s1=14, s2=10)
        if i < 3:
            arrow(d, p, 8000, 5560 + i * 2050, "↓", 20, K.ORANGE)
    arrow(d, p, 16600, 4900, "→", 30, K.ORANGE)
    for i, (t, s, fill) in enumerate(right):
        nbox(d, p, 17900, 4300 + i * 2050, 14800, 1250, t, s, fill,
             s1=14, s2=9)
        if i < 3:
            arrow(d, p, 24500, 5560 + i * 2050, "↓", 20, K.ORANGE)
    d.banner(p, "IRQ 1 → 세 큐 → wake_up → put_fs_byte — 인터럽트 길과 시스템 콜 길이 한 흐름에서 만난다", 12900, 16)

    # ── 정리 47 0.11다운 선택 ──────────────────────────────────
    p = d.slide("오늘 만난 \"0.11다운\" 선택들", K.S_WRAP,
                "kernel/chr_drv/keyboard.S:21-30·88-110 · tty_io.c:28-49·342-345 — 14회차 현대 커널 비교의 재료")
    d.cards(p, [
        ("큐 오프셋 수동 기입", "keyboard.S:21-26이 tty_queue\n오프셋(head=4·tail=8…)을\n어셈블리 상수로 유지\n\n구조가 바뀌면 둘 다 고친다"),
        ("인터럽트 안의 cooked 처리", "keyboard_interrupt가\ncopy_to_cooked를 직접 호출\n(EOI 후·iret 전)\n\nLinus: \"no problem\nwith sleeping…(I hope)\""),
    ], y=4400, h=4600)
    d.cards(p, [
        ("wake_up은 한 명", "proc_list가 가리키는 태스크\n하나만 state=0\n\n나머지는 repeat 연쇄로\n(sched.c:176-179)"),
        ("가득 차면 조용히 폐기", "put_queue je 3f(96-97)\n알림도 카운트도 없다\n\n가장 단순한 정책 —\n키 입력 몇 개는 잃어도 된다"),
        ("ECHOE·ECHOK 미사용", "매크로만 정의(35-36)\nERASE 에코는 L_ECHO만 본다\n(182-187)\n\n\"선언됐다 ≠ 동작한다\""),
    ], y=9300, h=4900)
    d.banner(p, "다섯 개 모두 1991년의 절충 — 14회차에서 현대 커널이 무엇을 어떻게 바꿨는지 본다", 14500, 16)

    # ── 확인 48 ────────────────────────────────────────────────
    p = d.slide("이해 확인", K.S_QUIZ,
                "4문항 — 정답(작은 글씨)과 근거 줄 번호 함께 · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "'a' 키를 눌렀다 뗐다. keyboard_interrupt는 몇 번 실행되고, read_q.head는 몇 번 전진하는가?\n"
         "정답 — 두 번(make 0x1E, break 0x9E) · head는 한 번만 — break의 key_table 항목은 none(530-540)",
         K.TEAL, 14)
    qbox(d, p, 1100, 6900, 31500, 2400, "Q2",
         "정규 모드에서 \"ab\"까지 치고 Enter를 아직 안 눌렀다. read()는 2바이트를 돌려주는가?\n"
         "정답 — 아니다. L_CANON && !data && LEFT>20이면 다시 잠든다(256-257) · data는 10/EOF에만 증가(210-211)",
         K.TEAL, 14)
    qbox(d, p, 1100, 9500, 31500, 2400, "Q3",
         "^C를 누르면 그 글자(0x03)는 secondary에 들어가는가? read()가 받는가?\n"
         "정답 — 안 들어간다(200-204 continue) · 시그널로 깨어나 0바이트면 -EINTR(285-286 · sched.c:117-119)",
         K.TEAL, 14)
    qbox(d, p, 1100, 12100, 31500, 2400, "Q4",
         "termios.h에 ECHOE가 있고 tty_io.c:35에 L_ECHOE 매크로도 있다. ECHOE를 끄면 백스페이스 에코가 달라지는가?\n"
         "정답 — 달라지지 않는다. L_ECHOE는 정의만 되고 호출되지 않는다(grep) · ERASE 에코는 L_ECHO만 본다(182-187)",
         K.TEAL, 14)

    # ── 정리 49 ────────────────────────────────────────────────
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "14회차 — 파트 G «종합·실습» · \"ls / 한 줄이 1~13회차 전부를 지나가는 지도\"")
    d.cards(p, [
        ("세 큐", "read_q(raw) — put_queue\nsecondary(cooked)\n  — copy_to_cooked\nwrite_q — tty_write→con_write\n\nhead/tail 버퍼 + data(줄 수)"),
        ("두 상태도", "① 글자의 위치\n  컨트롤러 → read_q\n  → secondary → 사용자 버퍼\n  (+ 에코 write_q → VGA)\n② 태스크 — RUNNING →\n  INTERRUPTIBLE → RUNNING"),
        ("플래그 표", "참조 13개 · 선언만 나머지\nioctl은 구현/부분/미구현\nMAJOR 0~7 — 핸들러 3개\n\n\"선언됐다 ≠ 동작한다\""),
    ], y=4400, h=7300)
    d.outline(p, 1100, 12100, 31500, 2300, K.ORANGE, 120)
    d.text(p, 1400, 12400, 30900, 1900,
           "14회차 예고 — ls / 한 줄: 셸 fork·exec → open·namei → bread·ll_rw_blk → … → tty_write 로 화면에 글자가 오는 전 과정\n"
           "오늘의 tty_read(시작)와 tty_write(끝)가 그 지도의 양 끝을 채웠다", 16, K.ORANGE, True)
    d.banner(p, "키보드에서 누른 글자가 세 큐를 지나 잠든 read()를 깨운다 — 핵심 질문의 답", 14600, 15)


if __name__ == "__main__":
    K.run(globals())
