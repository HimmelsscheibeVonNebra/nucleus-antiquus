#!/usr/bin/env python3
"""12회차 덱 — 파일 시스템: inode·경로 탐색·I/O (output/12-filesystem.pptx)

계획: materials/slide-plans/12-filesystem.md (§2 표 44행 1:1 · §3 앞부분 명세 ·
§4 다이어그램 명세 — 08 대응 구조도·16 탐색 커서 상태도·20 m_inode 상태도 ·
§5 캡처 5종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="12", total=44, slug="12-filesystem",
    part_no="E", part="«파일·저장»",
    title="12. 파일 시스템: inode·경로 탐색·I/O",
    question='"/etc/rc"라는 문자열이 어떻게 디스크 블록이 되는가?',
    done=11,
    today_line='문자열 "/etc/rc" → inode → 블록 번호 — bread가 받던 번호의 계산 계층',
    next_lines=[
        "11 → 12   bread가 받던 블록 번호를 누가 계산하는가 — namei·iget·bmap",
        '12 → 13   sys_read의 S_ISCHR 분기 rw_char — open("/dev/tty0")도 오늘의 sys_open을 지난다',
        "13 예고   키보드에서 누른 글자가 read()까지 — 파트 F «터미널» · 파트 E 마무리",
    ],
    road_note=("11 버퍼 위에 12 파일 시스템 — 모든 디스크 읽기는 11회차 bread를 지난다 · "
               "09 exec의 namei·10 do_exit의 iput이 오늘 본문"),
    STRUCT=dict(
        teal=["fs", "blk"],
        today=[("fs/namei.c", "namei·open_namei"),
               ("fs/inode.c", "iget·read_inode·bmap"),
               ("fs/open.c", "sys_open·fd"),
               ("fs/read_write.c", "sys_read/write 분기"),
               ("fs/file_dev.c·fs.h", "file_read·구조체·세 표")],
        flow='"/etc/rc" → sys_open → open_namei·find_entry → iget·read_inode·bmap → bread',
        up="↑ read() 반환",
        user='sh · cat /etc/rc — open·read',
    ),
)

CHECKS = dict(
    captions={
        6: "src/include/linux/fs.h:83-91",
        7: "src/include/linux/fs.h:93-105",
        8: "src/include/linux/fs.h:116-122",
        9: "src/fs/super.c:242-251",
        10: "src/fs/super.c:124-136",
        12: "src/fs/namei.c:237-248",
        13: "src/fs/namei.c:249-258",
        14: "src/fs/namei.c:104-110",
        15: "src/fs/namei.c:278-294",
        17: "src/fs/inode.c:250-262",
        18: "src/fs/inode.c:300-312",
        19: "src/fs/inode.c:176-192",
        21: "src/fs/inode.c:77-88",
        23: "src/fs/bitmap.c:83-93",
        26: "src/fs/namei.c:346-359",
        27: "src/fs/namei.c:392-407",
        28: "src/fs/namei.c:47-53",
        30: "src/fs/open.c:144-161",
        31: "src/fs/read_write.c:66-80",
        33: "src/fs/file_dev.c:22-33",
        34: "src/fs/file_dev.c:60-77",
    },
    required=[
        "/etc/rc", "namei", "open_namei", "get_dir", "find_entry", "dir_namei",
        "iget", "read_inode", "iput", "bmap", "create_block", "i_zone",
        "dir_entry", "d_inode", "m_inode", "SUPER_MAGIC", "0x137F",
        "mount_root", "read_super", "s_firstdatazone", "s_imap", "s_zmap",
        "inode_table", "file_table", "filp", "f_pos", "f_count", "i_count",
        "i_dirt", "ACC_MODE", "\\004\\002\\006\\377", "O_EXCL", "O_APPEND",
        "O_TRUNC", "O_CREAT", "MAY_EXEC", "permission", "new_block",
        "new_inode", "add_entry", "file_read", "file_write", "sys_open",
        "sys_close", "sys_read", "sys_write", "rw_char", "block_read",
        "read_pipe", "put_fs_byte", "get_fs_byte", "bread", "brelse",
        "getblk", "truncate", "구멍", "ROOT_INO", "NR_INODE", "NR_FILE",
        "NR_OPEN", "wait_on_inode", "i_mount", "s_imount", "NO_TRUNCATE",
        "check_disk_change", "verify_area", "dcache", "s_max_size",
        "INODES_PER_BLOCK", "DIR_ENTRIES_PER_BLOCK", "find_first_zero",
        "clear_block", "sync_dev", "do_execve", "umask", "suser",
    ],
    prereq=[
        ("bread", "src/fs/super.c:124-136"),
        ("dir_entry", "src/fs/namei.c:104-110"),
        ("i_zone", "src/fs/inode.c:300-312"),
        ("filp", "src/fs/open.c:144-161"),
    ],
    structure_nodes=["namei.c", "inode.c", "open.c", "read_write.c",
                     "file_dev.c", "fs.h", "buffer.c", "system_call.s"],
    capture_slides=[25, 37, 38],
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


def ph_panel(d, p, x, y, w, h, body, name):
    """좁은 패널용 캡처 예정 패널 — 캡션을 패널 폭에 맞춰 줄인다(파일명만)."""
    d.shape(p, x, y, w, h, 0x071A24)
    cap = f"예상 출력 — 실측 아님 · {name}"
    d.text(p, x + 350, y + 250, w - 700, 600, cap,
           K.fit_size(cap, 12, w - 700, min_size=9), K.TEAL)
    lines = body.split("\n")
    size = 11
    while (size > 8
           and (1150 + len(lines) * size * 58 > h - 300
                or max((K.text_width(l, size) for l in lines), default=0)
                > (w - 800) * 1.12)):
        size -= 1
    d.text(p, x + 350, y + 1150, w - 700, h - 1450, body, size, K.PAPER,
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


def arrow(d, p, x, y, glyph, size=24, color=K.TEAL, w=1400, h=900):
    d.text(p, x, y, w, h, glyph, size, color, True)


def qbox(d, p, x, y, w, h, tag, body, tag_color, size=14):
    d.shape(p, x, y, w, h, K.INK)
    d.shape(p, x, y, w, 130, tag_color)
    d.text(p, x + 250, y + 320, w - 500, 500, tag, 15, tag_color, True)
    para(d, p, x + 250, y + 950, w - 500, h - 1150, body, size, K.PAPER)


def populate(d):
    # ── 배경 05–11 ────────────────────────────────────────────
    # 05 디스크 위의 배치 (MINIX 1.0 형식)
    p = d.slide("디스크 위의 배치 (MINIX 1.0 형식)", K.S_BG,
                "fs/super.c:100-165(141-151) · fs/inode.c:303-304 · include/linux/fs.h:36-46 — MINIX 1.0 형식 그대로")
    d.outline(p, 1100, 4300, 13600, 750, K.MUTED, 60)
    d.text(p, 1350, 4390, 13100, 500, "블록 0 — 부트 블록 (bootsect가 들어 있던 자리)", 13, K.MUTED)
    d.shape(p, 1100, 5130, 13600, 950, K.TEAL)
    d.text(p, 1350, 5170, 13100, 480, "블록 1 — 슈퍼 블록 · d_super_block (fs.h:146-155)", 15, K.INK, True)
    d.text(p, 1350, 5650, 13100, 430, "s_ninodes · s_nzones · 비트맵 크기 · s_firstdatazone · s_magic", 12, K.INK)
    d.shape(p, 1100, 6160, 13600, 950, K.PAPER)
    d.text(p, 1350, 6200, 13100, 480, "블록 2 … — inode 비트맵 imap × s_imap_blocks", 15, K.INK, True)
    d.text(p, 1350, 6720, 13100, 430, "비트맵 1블록 = 8192비트 — 사용 중 inode에 1", 12, K.INK)
    d.shape(p, 1100, 7190, 13600, 950, K.PAPER)
    d.text(p, 1350, 7230, 13100, 480, "다음 — 존 비트맵 zmap × s_zmap_blocks", 15, K.INK, True)
    d.text(p, 1350, 7750, 13100, 430, "사용 중 데이터 블록(존)에 1", 12, K.INK)
    d.shape(p, 1100, 8220, 13600, 1050, K.ORANGE)
    d.text(p, 1350, 8260, 13100, 480, "inode 표 — d_inode 32B × INODES_PER_BLOCK(32)", 15, K.INK, True)
    d.text(p, 1350, 8780, 13100, 430, "inode 번호는 이 표 안의 순번 (1부터)", 12, K.INK)
    d.shape(p, 1100, 9350, 13600, 1050, K.PAPER)
    d.text(p, 1350, 9390, 13100, 480, "s_firstdatazone … — 데이터 존 (s_nzones개)", 15, K.INK, True)
    d.text(p, 1350, 9910, 13100, 430, "파일 내용·디렉터리 엔트리 배열이 들어가는 곳", 12, K.INK)
    d.outline(p, 1100, 10480, 13600, 750, K.MUTED, 60)
    d.text(p, 1350, 10570, 13100, 500, "… 마지막 블록 — 크기는 슈퍼 블록이 정한다", 13, K.MUTED)
    nbox(d, p, 15500, 4900, 17100, 1800, "s_magic != SUPER_MAGIC(0x137F) → 마운트 실패",
         "read_super 검사 — super.c:132-136 · fs.h:41", K.INK, K.TEAL, K.PAPER, s1=15, s2=12)
    nbox(d, p, 15500, 6900, 17100, 1800, "read_super — block=2에서 비트맵 bread 시작",
         "imap 블록 → zmap 블록 차례로 — super.c:141-151", K.INK, K.ORANGE, K.PAPER, s1=15, s2=12)
    d.text(p, 15050, 7620, 800, 500, "◀", 18, K.ORANGE, True)
    nbox(d, p, 15500, 8900, 17100, 2000, "read_inode 산식 — inode.c:303-304",
         "block = 2 + s_imap_blocks + s_zmap_blocks + (i_num-1)/32",
         K.INK, K.ORANGE, K.PAPER, s1=15, s2=13)
    d.text(p, 15050, 9720, 800, 500, "◀", 18, K.ORANGE, True)
    nbox(d, p, 15500, 11100, 17100, 1800, "존(zone) = 데이터 블록",
         "s_log_zone_size=0 — 존과 블록이 같다, 1024B (§7 용어)", None, K.TEAL, K.TEAL, K.MUTED, s1=15, s2=12)
    para(d, p, 15500, 13100, 17100, 1400,
         "1블록 1024B — inode 32개(fs.h:55) · dir_entry 64개(fs.h:56). "
         "이 배치가 오늘 모든 산식의 기준이다.", 15)
    d.banner(p, "문자열이 아니라 번호의 세계 — 슈퍼 블록이 배치를, inode 번호가 표 안 위치를 정한다")

    # 06 네 구조체: 디스크 형식
    p = d.slide("네 구조체: 디스크 형식", K.S_CODE,
                "include/linux/fs.h:55-56, 83-91, 146-155, 157-160 · fs/super.c:248-249 — 디스크에 있는 그대로의 형식")
    d.code_panel(p, "src/include/linux/fs.h", 83, 91, 1100, 4300, 15700, 6300,
                 size=9, caption_extra="d_inode 32B")
    d.code_panel(p, "src/include/linux/fs.h", 146, 155, 17800, 4300, 14800, 6800,
                 size=9, caption_extra="")
    d.code_panel(p, "src/include/linux/fs.h", 157, 160, 1100, 10800, 13100, 3800,
                 size=9, caption_extra="dir_entry 16B")
    d.code_panel(p, "src/include/linux/fs.h", 55, 56, 15200, 10800, 17400, 2800,
                 size=9, caption_extra="1블록 32/64개")
    para(d, p, 17800, 11400, 14800, 3200,
         "d_inode 32B = mode 2 + uid 2 + size 4 + time 4 + gid 1 + nlinks 1 + zone[9] 18\n\n"
         "dir_entry 16B = inode 번호 2B + 이름 14B(NAME_LEN) — 디렉터리는 이 16B의 배열.\n"
         "sizeof(d_inode)이 32가 아니면 부팅이 중단된다(super.c:248-249).", 14)
    d.banner(p, "디스크 형식은 세 가지 — 슈퍼 블록·inode·디렉터리 엔트리 · 이름은 dir_entry에만 있다")

    # 07 네 구조체: 메모리 형식
    p = d.slide("네 구조체: 메모리 형식", K.S_CODE,
                "include/linux/fs.h:93-114, 124-144 · fs/inode.c:307-309 — 디스크 형식 위에 살아 있는 필드가 얹힌다")
    d.code_panel(p, "src/include/linux/fs.h", 93, 105, 1100, 4300, 15200, 8400,
                 size=9, caption_extra="")
    d.code_panel(p, "src/include/linux/fs.h", 106, 114, 16900, 4300, 15700, 6300,
                 size=9, caption_extra="메모리 전용")
    d.code_panel(p, "src/include/linux/fs.h", 133, 137, 16900, 10800, 15700, 4000,
                 size=8, caption_extra="메모리부")
    d.shape(p, 1100, 12900, 7600, 1500, K.TEAL)
    d.text(p, 1350, 13000, 7100, 450, "d_inode와 동일한 앞 32B", 14, K.INK, True)
    d.text(p, 1350, 13500, 7100, 450, "read_inode가 덮어쓰는 영역 (307-309)", 12, K.INK)
    d.shape(p, 8800, 12900, 7500, 1500, K.ORANGE)
    d.text(p, 9050, 13000, 7000, 450, "m_inode 확장 필드 (101-113)", 14, K.INK, True)
    d.text(p, 9050, 13500, 7000, 450, "i_count·i_lock·i_dirt 등", 11, K.INK)
    d.banner(p, "read_inode:307-309 — 앞 32B만 덮어쓴다 · s_imount는 마운트 지점 연결(17장)")

    # 08 세 개의 표 — 핵심 대응 구조도
    p = d.slide("세 개의 표", K.S_CODE,
                "include/linux/fs.h:116-122, 157-164 · include/linux/sched.h:102 — 핵심 그림: fd → file → inode → 디스크")
    d.text(p, 1100, 4120, 17400, 500, "① task_struct.filp[NR_OPEN=20] — 태스크마다 (sched.h:102)", 13, K.TEAL, True)
    for i in range(20):
        x = 1100 + i * 815
        if i == 3:
            d.shape(p, x, 4650, 800, 1100, K.ORANGE)
            d.text(p, x + 80, 4850, 640, 500, "3", 14, K.INK, True)
        elif i < 3:
            d.shape(p, x, 4650, 800, 1100, K.TEAL)
            d.text(p, x + 80, 4850, 640, 500, str(i), 14, K.INK, True)
        else:
            d.outline(p, x, 4650, 800, 1100, K.MUTED, 50)
    d.text(p, 1100, 5820, 17400, 430, "fd 0·1·2 = tty — fd는 이 배열의 인덱스일 뿐", 12, K.MUTED)
    d.text(p, 13600, 6290, 3000, 600, "↓ fd 3", 12, K.TEAL, True)
    d.text(p, 1100, 6420, 17400, 500, "② file_table[NR_FILE=64] — 전역 공유, f_count로 생존", 13, K.TEAL, True)
    for i, (label, sub, muted) in enumerate([
            ("…", "f_count=2", True), ("file_table[i]", "f_count=1 · f_pos=0\nf_inode →", False),
            ("…", "", True), ("…", "", True)]):
        x = 1100 + i * 4350
        if muted:
            d.outline(p, x, 7000, 4100, 1500, K.MUTED, 50)
            d.text(p, x + 200, 7500, 3700, 500, label, 14, K.MUTED, True)
        else:
            d.shape(p, x, 7000, 4100, 1500, K.ORANGE)
            d.text(p, x + 200, 7150, 3700, 450, label, 13, K.INK, True)
            d.text(p, x + 200, 7650, 3700, 800, sub, 11, K.INK)
    d.text(p, 13600, 8690, 3000, 600, "↓ f_inode", 12, K.TEAL, True)
    d.text(p, 1100, 8820, 17400, 500, "③ inode_table[NR_INODE=32] — 전역 공유, i_count로 생존", 13, K.TEAL, True)
    for i, (label, sub, muted) in enumerate([
            ("…", "root #1", True), ("…", "etc #k", True),
            ("inode_table[j]", "rc #m · i_zone[9]\ni_count·i_dirt", False),
            ("…", "", True)]):
        x = 1100 + i * 4350
        if muted:
            d.outline(p, x, 9400, 4100, 1700, K.MUTED, 50)
            d.text(p, x + 200, 9550, 3700, 500, label, 14, K.MUTED, True)
            d.text(p, x + 200, 10100, 3700, 500, sub, 12, K.MUTED)
        else:
            d.shape(p, x, 9400, 4100, 1700, K.ORANGE)
            d.text(p, x + 200, 9520, 3700, 450, label, 13, K.INK, True)
            d.text(p, x + 200, 10020, 3700, 1000, sub, 11, K.INK)
    d.text(p, 13600, 11290, 3000, 600, "↓ i_zone[0]", 12, K.TEAL, True)
    d.text(p, 1100, 11420, 17400, 500, "④ 디스크 — super_block[8] · inode 블록 · 데이터 블록", 13, K.TEAL, True)
    d.shape(p, 1100, 12000, 5100, 1300, K.PAPER)
    d.text(p, 1350, 12100, 4600, 450, "inode 블록", 13, K.INK, True)
    d.text(p, 1350, 12600, 4600, 450, "2+imap+zmap+(m-1)/32", 11, K.INK)
    d.shape(p, 6400, 12000, 5100, 1300, K.TEAL)
    d.text(p, 6650, 12100, 4600, 450, "데이터 블록 z", 13, K.INK, True)
    d.text(p, 6650, 12600, 4600, 450, "rc.i_zone[0] — m의 내용", 11, K.INK)
    d.outline(p, 11700, 12000, 6600, 1300, K.MUTED, 50)
    d.text(p, 11950, 12100, 6100, 450, "super_block[8]", 13, K.MUTED, True)
    d.text(p, 11950, 12600, 6100, 450, "imap·zmap 버퍼를 붙잡고 있음", 11, K.MUTED)
    d.code_panel(p, "src/include/linux/fs.h", 116, 122, 19300, 4300, 13300, 5700,
                 size=10, caption_extra="")
    d.code_panel(p, "src/include/linux/fs.h", 162, 164, 19300, 10200, 13300, 4400,
                 size=11, caption_extra="")
    d.banner(p, "① 빈 fd ② f_count++ 후 open_namei ③ f_* 채움 — fork는 filp 복사로 f_count 증가")

    # 09 부팅 때 만들어진 초기 상태
    p = d.slide("부팅 때 만들어진 초기 상태", K.S_CODE,
                "fs/super.c:242-281 · kernel/blk_drv/hd.c:158 — 11회차 sys_setup → mount_root → 부팅 출력 \"N/M free blocks\"")
    d.code_panel(p, "src/fs/super.c", 242, 251, 1100, 4300, 15200, 6800,
                 size=9, caption_extra="d_inode 32B 검사")
    d.code_panel(p, "src/fs/super.c", 256, 268, 16900, 4300, 15700, 8300,
                 size=9, caption_extra="iget(ROOT_DEV, 1)")
    para(d, p, 1100, 11400, 15200, 3200,
         "이어지는 269-280 — zmap·imap 비트를 하나씩 세서 부팅 화면에 "
         "\"%d/%d free blocks\"·\"%d/%d free inodes\"를 출력한다(274·280). "
         "11회차 sys_setup(hd.c:158)이 mount_root를 부른 뒤 처음 보는 줄이다.", 15)
    para(d, p, 16900, 12800, 15700, 1700,
         "265 주석 — root inode는 s_isup·s_imount·pwd·root 네 곳에서 참조 → i_count += 3 (논리 4참조).", 14, K.ORANGE, True)
    d.banner(p, "모든 경로 탐색의 출발점 — current->root·pwd가 여기서 생긴다 (inode #1)")

    # 10 코드: read_super
    p = d.slide("코드: read_super", K.S_CODE,
                "fs/super.c:100-165 — 빈 슬롯 → bread(dev,1) → magic 검사 → 비트맵 블록 bread")
    d.code_panel(p, "src/fs/super.c", 124, 136, 1100, 4300, 15200, 8300,
                 size=9, caption_extra="블록 1 · magic 0x137F")
    d.code_panel(p, "src/fs/super.c", 141, 152, 16900, 4300, 15700, 7800,
                 size=9, caption_extra="block=2 비트맵")
    d.shape(p, 16900, 12400, 4400, 2000, K.PAPER)
    d.text(p, 17150, 12550, 3900, 450, "super_block", 13, K.INK, True)
    d.text(p, 17150, 13100, 3900, 450, "s_imap·s_zmap", 11, K.INK)
    for i in range(4):
        d.text(p, 21500 + i * 2800, 12450, 2700, 400, "→", 13, K.TEAL, True)
        d.shape(p, 21600 + i * 2800, 12900, 2500, 1100, K.TEAL)
        d.text(p, 21650 + i * 2800, 13050, 2400, 500, f"버퍼 {i}", 12, K.INK, True)
    para(d, p, 16900, 14100, 15700, 500,
         "brelse하지 않고 보관 — 슈퍼 블록이 평생 붙잡는 버퍼 · 0번 비트 예약 |= 1 (161-162)", 12)
    d.banner(p, "비트맵은 디스크 블록 그 자체 — 버퍼 캐시 위에 올려두고 커널이 비트를 직접 바꾼다")

    # 11 호출 순서도: open("/etc/rc") 전체
    p = d.slide('호출 순서도: open("/etc/rc") 전체', K.S_BG,
                "fs/open.c:138-185 · fs/namei.c:228-410 · fs/inode.c:244-338 — 상태 변화도가 아니라 호출 순서다")
    chain = [
        ("sys_open (open.c:138)", "빈 fd · file_table 슬롯", K.PAPER, 850),
        ("open_namei (namei.c:337)", "플래그 해석 · 권한", K.PAPER, 850),
        ("dir_namei (namei.c:278)", "마지막 구성 요소 분리", K.PAPER, 850),
        ("get_dir (namei.c:228)", "'/' → root inode 1", K.PAPER, 850),
        ("구성 요소마다 반복", "find_entry(91) → bread(디렉터리 블록)\niget(244) → read_inode(294) → bread(inode 블록)", K.ORANGE, 2400),
        ('find_entry("rc") → iget', "de->inode = m 획득", K.PAPER, 850),
        ("f_mode·f_flags·f_inode·f_pos 채움", "open.c:179-183 → fd 반환", K.TEAL, 850),
    ]
    y = 4300
    for i, (l1, l2, fill, h) in enumerate(chain):
        if fill is K.ORANGE:
            nbox(d, p, 1100, y, 14000, h, l1, l2, fill, s1=16, s2=12)
        else:
            nbox(d, p, 1100, y, 14000, h, l1, None, fill, s1=15)
            d.text(p, 15600, y + 180, 5300, 700, l2, 12, K.MUTED)
        if i < len(chain) - 1:
            arrow(d, p, 7500, y + h - 60, "↓", 16, K.ORANGE, 900, 450)
        y += h + 260
    nbox(d, p, 22000, 4300, 10600, 1750, "11회차 — bread(dev, block)",
         "fs/buffer.c — 여기로 모인다", K.TEAL, s1=15, s2=12)
    para(d, p, 22000, 6300, 10600, 3400,
         "이 흐름 안의 bread 호출 3곳 —\n"
         "· read_super:124 (블록 1)\n"
         "· find_entry:129 (디렉터리 블록)\n"
         "· read_inode:305 (inode 블록)\n"
         "모든 디스크 읽기는 bread 하나로 (11회차).", 14)
    para(d, p, 22000, 10000, 10600, 4400,
         "상자는 함수 호출, 화살표는 시간 순서 — 데이터의 상태 변화는 "
         "16장(탐색 커서)·20장(m_inode 슬롯)이 다룬다. 값 k·m은 25장 캡처에서.", 14,
         K.MUTED)
    d.banner(p, "open은 아직 파일 내용을 읽지 않는다 — 디렉터리 블록과 inode 블록만 (42장 오해 3)")

    # ── 코드 12–15 (16은 상태도) ──────────────────────────────
    # 12 get_dir 시작점
    p = d.slide("코드: get_dir 시작점", K.S_CODE,
                "fs/namei.c:237-248 — root·pwd 검사 · 첫 글자 '/' 판정 · 참조 하나 빌림")
    d.code_panel(p, "src/fs/namei.c", 237, 248, 1100, 4300, 19700, 7800,
                 size=9, caption_extra="i_count++ — 탐색 동안 붙잡는다")
    para(d, p, 22000, 4300, 10000, 5400,
         "root·pwd가 없으면 panic — 부팅 때 mount_root가 만들어 둔 것(09장).\n\n"
         "첫 글자가 '/' → current->root, 아니면 current->pwd — 상대·절대 경로가 "
         "여기서 갈린다.\n\n248: inode->i_count++ — 탐색하는 동안 회수되지 않게 "
         "참조 하나를 빌린다.", 15)
    d.text(p, 22000, 10000, 10000, 500, "경로 문자열은 사용자 공간에 있다 (4회차)", 13, K.TEAL, True)
    nbox(d, p, 22000, 10600, 10000, 1300, '사용자 DS — pathname "/etc/rc"',
         None, K.PAPER, s1=13)
    d.text(p, 22200, 11950, 9600, 400, "↓ get_fs_byte — %fs 세그먼트로 한 글자씩", 12, K.ORANGE, True)
    nbox(d, p, 22000, 12450, 10000, 1100, "커널 — 글자 단위로 판정", None, K.TEAL, s1=13)
    para(d, p, 22000, 13700, 10000, 800,
         "match()의 fs repe cmpsb도 같은 이유 (63-78).", 12, K.MUTED)
    d.banner(p, "get_fs_byte — 커널이 사용자 포인터를 직접 역참조하지 않는 0.11의 규칙")

    # 13 get_dir 반복
    p = d.slide("코드: get_dir 반복", K.S_CODE,
                "fs/namei.c:249-269 · permission(40-54) — 디렉터리인지·MAY_EXEC 검사 후 구성 요소별 반복")
    d.code_panel(p, "src/fs/namei.c", 249, 258, 1100, 4300, 12800, 6800,
                 size=9, caption_extra="권한 검사")
    d.code_panel(p, "src/fs/namei.c", 259, 269, 14700, 4300, 17900, 7300,
                 size=9, caption_extra="find_entry → iget")
    pairs = [
        ("빌림 — 248", "root.i_count\n1 → 2", K.TEAL),
        ("find_entry — 129", "bread(dev, i_zone[0])\nbh b_count = 1", K.PAPER),
        ("돌려줌 — 265-266", "brelse(bh) → 0\niput(root) → 1", K.PAPER),
        ("다시 빌림 — 267", "iget(idev, inr)\netc.i_count = 1", K.ORANGE),
    ]
    for i, (t, s, fill) in enumerate(pairs):
        x = 1100 + i * 8050
        nbox(d, p, x, 11800, 7300, 2600, t, s, fill, s1=14, s2=12)
        if i < 3:
            d.text(p, x + 7400, 12600, 700, 600, "→", 20, K.TEAL, True)
    d.banner(p, "빌리고 → 돌려주고 → 다시 빌린다 — 모든 단계에서 참조 수가 짝을 이룬다 (263-268)")

    # 14 find_entry
    p = d.slide("코드: find_entry", K.S_CODE,
                "fs/namei.c:91-153 · match(63-78) — '..' 특수 처리(112-126) · 스캔 루프(133-152)는 발췌")
    d.code_panel(p, "src/fs/namei.c", 104, 110, 1100, 4300, 19700, 5500,
                 size=10, caption_extra="14자 초과는 잘림 — NO_TRUNCATE 미정의 (§8)")
    d.code_panel(p, "src/fs/namei.c", 143, 149, 1100, 9900, 19700, 4700,
                 size=8, caption_extra="match 적중 — 버퍼 잡은 채 반환")
    para(d, p, 22000, 4300, 10000, 5600,
         "· 104-105 — NO_TRUNCATE 미정의, 15자 이상은 14자로 잘림(§8)\n"
         "· 107 — entries = i_size/16\n"
         "· 112-126 — '..' 처리: 자기 root에서는 '.', 마운트 지점 root에서는 "
         "sb->s_imount로 교체(119-124)\n"
         "· 127-132 — i_zone[0] 블록 bread\n"
         "· 134-142 — 블록 끝마다 bmap(*dir, i/64)로 다음", 13)
    d.text(p, 22000, 10100, 10000, 500, "디렉터리 블록 = dir_entry[64] (i_zone[0])", 13, K.TEAL, True)
    for i, nm in enumerate([".", "..", "etc", "bin", "dev", "usr", "tmp", "…"]):
        x = 22000 + i * 1250
        if nm == "etc":
            d.shape(p, x, 10700, 1150, 1000, K.ORANGE)
            d.text(p, x + 100, 10950, 950, 500, nm, 12, K.INK, True)
            d.text(p, x + 100, 11750, 1300, 400, "▲ match", 11, K.ORANGE, True)
        else:
            d.outline(p, x, 10700, 1150, 1000, K.MUTED, 50)
            d.text(p, x + 100, 10950, 950, 500, nm, 12, K.MUTED)
    para(d, p, 22000, 12300, 10000, 2200,
         "match(namelen, name, de) — 이름은 fs 세그먼트, de->name은 커널 버퍼(63-78).\n"
         "버퍼를 잡은 채 반환 — 호출자가 de->inode를 읽고 brelse한다(§8).", 13)
    d.banner(p, "64칸을 순서대로 훑는 선형 탐색 — 정렬·인덱스 없음 (dcache는 현대 이야기, 41장)")

    # 15 dir_namei와 namei
    p = d.slide("코드: dir_namei와 namei", K.S_CODE,
                "fs/namei.c:278-294, 313-329 — get_dir으로 마지막 디렉터리, basename은 호출자의 find_entry가")
    d.code_panel(p, "src/fs/namei.c", 278, 294, 1100, 4300, 15200, 9400,
                 size=8, caption_extra="마지막 '/' 뒤가 basename")
    d.code_panel(p, "src/fs/namei.c", 313, 329, 16900, 4300, 15700, 9400,
                 size=8, caption_extra="'/usr/' 특례 · i_atime")
    d.banner(p, "호출처 — do_execve(exec.c:199) · sys_chdir · sys_mount(super.c:206·214)")

    # ── 상태도 16 ─────────────────────────────────────────────
    p = d.slide('상태 변화도: 경로 탐색 커서 "/etc/rc"', K.S_STATE,
                "fs/namei.c:91-330 · fs/inode.c:244-292 — 노드 = (현재 디렉터리 inode, 남은 문자열, 빌린 참조) · k·m은 기호(값은 25장)")
    nodes = [
        ('(root #1, "etc/rc")', "root.i_count = 3+1", "mount_root가 만듦\n(09장)"),
        ('(etc #k, "rc")', "etc.i_count = 1", "find_entry·iget으로\n교체된 커서"),
        ('etc #k · basename', "namelen = 2", "dir_namei 반환 —\n문자열 끝(257-258)"),
        ("(rc #m)", "m.i_count = 1", "namei 반환 —\ni_atime 갱신(326)"),
    ]
    xs = [1100, 9400, 17700, 26000]
    for i, (title, ref, note) in enumerate(nodes):
        x = xs[i]
        fill = K.PAPER if i in (1, 2) else K.TEAL
        d.shape(p, x, 6600, 6400, 2500, fill)
        d.text(p, x + 250, 6700, 5900, 550, title, 16, K.INK, True)
        d.text(p, x + 250, 7350, 5900, 500, ref, 13, K.INK)
        d.text(p, x + 250, 7900, 5900, 900, note, 11, K.INK)
        para(d, p, x, 9300, 6400, 800,
             "유지 조건 — 디렉터리(S_ISDIR) + MAY_EXEC", 11, K.TEAL, True)
    trans = [
        (7000, 'find_entry("etc", 3)', "bread(dev, root.i_zone[0])에서\ndir_entry {inode=k, \"etc\"} 적중",
         "iput(root): 2→1 · iget(dev,k): 1\nbh b_count 1→0 (brelse 265)", 8050),
        (15300, "get_dir — 문자열 끝", "'/'가 더 없으면 현재 inode 반환\n(257-258) · c=get_fs_byte로 확인",
         "참조 그대로 — etc.i_count=1\n버퍼 없음", 16350),
        (23600, 'namei: find_entry("rc", 2)', "bread(etc.i_zone[0])에서\ndir_entry {inode=m, \"rc\"} 적중",
         "iput(etc)·iget(dev,m)\ni_atime·i_dirt 갱신 (326-327)", 24650),
    ]
    for x, t1, t2, chg, ax in trans:
        d.text(p, x, 4600, 6900, 500, t1, 14, K.ORANGE, True)
        d.text(p, x, 5150, 6900, 1100, t2, 11, K.PAPER)
        d.text(p, ax, 7250, 900, 700, "→", 26, K.ORANGE, True)
        d.text(p, x, 10400, 6900, 500, "변경 데이터", 11, K.TEAL, True)
        d.text(p, x, 10850, 6900, 1100, chg, 11, K.PAPER)
    para(d, p, 1100, 12400, 31500, 1300,
         "커서 = (디렉터리 inode, 남은 문자열). 구성 요소 하나가 처리될 때마다 inode가 교체되고 "
         "참조는 iput·iget 쌍으로 정확히 맞춰진다(13장). 실제 k·m 값은 캡처(25장)에서만 — "
         "루트 이미지마다 다르다(§8).", 14)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)
    d.banner(p, '"/etc/rc"는 두 번의 find_entry로 끝난다 — root와 etc의 블록을 하나씩 읽을 뿐', 14000, 18)

    # ── 코드 17–19 ────────────────────────────────────────────
    # 17 iget
    p = d.slide("코드: iget", K.S_CODE,
                "fs/inode.c:244-292 · get_empty_inode(194-226) — 빈 슬롯을 먼저 확보하고 선형 탐색")
    d.code_panel(p, "src/fs/inode.c", 250, 262, 1100, 4300, 15200, 8300,
                 size=9, caption_extra="빈 슬롯 먼저 확보")
    d.code_panel(p, "src/fs/inode.c", 263, 280, 16900, 4300, 15700, 9800,
                 size=8, caption_extra="i_mount → ROOT_INO로")
    d.text(p, 1100, 12700, 15200, 500, "inode_table[32] — 선형 탐색 (해시 없음, §8)", 13, K.TEAL, True)
    for i in range(32):
        x = 1100 + i * 460
        if i == 7:
            d.shape(p, x, 13100, 430, 700, K.ORANGE)
        elif i == 15:
            d.shape(p, x, 13100, 430, 700, K.TEAL)
        elif i % 3:
            d.shape(p, x, 13100, 430, 700, K.PAPER)
        else:
            d.outline(p, x, 13100, 430, 700, K.MUTED, 40)
    para(d, p, 1100, 13900, 15200, 600,
         "주황 = 적중(i_count++) · 청록 = i_mount → ROOT_INO 재탐색 · 빈 칸 = empty", 11)
    d.banner(p, "32슬롯뿐 — 빈 슬롯은 잠들 수 있는 get_empty_inode를 먼저 얻어 둔다 (250)")

    # 18 read_inode
    p = d.slide("코드: read_inode", K.S_CODE,
                "fs/inode.c:294-312 — 원 16 분할 1/2 · 산식이 05장 디스크 배치의 inode 표 위치와 일치한다")
    d.code_panel(p, "src/fs/inode.c", 300, 312, 1100, 4300, 19700, 8300,
                 size=9, caption_extra="lock → 산식 → bread → 32B 복사")
    d.shape(p, 22000, 4300, 10000, 1900, K.ORANGE)
    d.text(p, 22300, 4420, 9400, 700, "block = 2 + s_imap_blocks", 16, K.INK, True)
    d.text(p, 22300, 5150, 9400, 800, "+ s_zmap_blocks + (i_num-1)/32", 16, K.INK, True)
    para(d, p, 22000, 6300, 10000, 700, "05장 배치 그림 재지시 — inode 표 위치", 13, K.TEAL, True)
    for i, t in enumerate(["블록 0 부트", "블록 1 슈퍼", "imap 블록들", "zmap 블록들"]):
        nbox(d, p, 22000, 7100 + i * 880, 10000, 780, t, None, None, K.MUTED, s1=12)
    d.shape(p, 22000, 10620, 10000, 1100, K.ORANGE)
    d.text(p, 22300, 10720, 9400, 500, "inode 표 — (n-1)/32번째 블록", 14, K.INK, True)
    d.text(p, 22300, 11240, 9400, 450, "그 안 (n-1)%32번째 32B 슬롯", 12, K.INK)
    nbox(d, p, 22000, 11900, 10000, 780, "s_firstdatazone … 데이터 존", None, None, K.MUTED, s1=12)
    para(d, p, 22000, 12900, 10000, 1700,
         "307-309 — 앞 32B만 덮어쓴다(07장) · write_inode(314-338)는 같은 산식의 반대.", 13)
    d.banner(p, "inode 번호는 순번, 블록 번호는 산식의 결과 — 두 번호를 혼동하지 않는다 (42장 오해 1)")

    # 19 iput
    p = d.slide("코드: iput", K.S_CODE,
                "fs/inode.c:150-192 — 원 16 분할 2/2 · 앞부분 특례(154-174)는 오른쪽 · 10회차 do_exit의 iput 세 번과 연결")
    d.code_panel(p, "src/fs/inode.c", 176, 192, 1100, 4300, 15200, 9400,
                 size=8, caption_extra="분기 4갈래")
    steps = [
        ("i_pipe? — 157-166", "파이프 특례 — 페이지 반납", None),
        ("i_dev==0? — 167-170", "감소만", None),
        ("S_ISBLK? — 171-174", "sync_dev(i_zone[0])", None),
        ("i_count>1 → 감소만", "176-179", K.PAPER),
        ("i_nlinks==0 → 삭제", "truncate + free_inode — 180-184", K.ORANGE),
        ("i_dirt → write_inode", "후 goto repeat — 185-189", K.PAPER),
    ]
    d.text(p, 22000, 4150, 10000, 500, "iput 분기 결정 트리", 14, K.TEAL, True)
    y = 4700
    for t, s, fill in steps:
        if fill is None:
            d.outline(p, 22000, y, 10000, 1050, K.MUTED, 60)
            d.text(p, 22250, y + 140, 9500, 450, t, 13, K.MUTED, True)
            d.text(p, 22250, y + 590, 9500, 420, s, 11, K.MUTED)
        else:
            d.shape(p, 22000, y, 10000, 1050, fill)
            d.text(p, 22250, y + 140, 9500, 450, t, 13, K.INK, True)
            d.text(p, 22250, y + 590, 9500, 420, s, 11, K.INK)
        y += 1200
    para(d, p, 22000, y + 100, 10000, 2600,
         "write_inode:331-334 — inode 블록 버퍼에 b_dirt=1, 11회차 지연 쓰기로 기록. "
         "10회차 do_exit이 iput 세 번.", 13)
    d.banner(p, "i_count가 0에 도달하면 슬롯은 get_empty_inode의 재사용 후보가 된다 — 20장 상태도로")

    # ── 상태도 20 ─────────────────────────────────────────────
    p = d.slide("상태 변화도: m_inode 슬롯", K.S_STATE,
                "fs/inode.c:72-338 — 캡처 25·37장의 i_count·i_num 값이 이 상태도의 해당 상태를 재지시한다 (각주)")
    st = [
        ("비어 있음", "i_count=0 · i_dev=0", None, K.MUTED),
        ("읽는 중", "i_lock=1 · 잠금 배지", "read_inode 진행", K.ORANGE),
        ("메모리 상주", "i_count >= 1", "단독 참조", K.TEAL),
        ("공유", "i_count >= 2", "여러 filp 참조", K.TEAL),
        ("반납 중", "iput 진행", "write_inode·truncate", K.ORANGE),
    ]
    xs20 = [1100, 7750, 14400, 21050, 27700]
    for i, (t, s, s2, col) in enumerate(st):
        x = xs20[i]
        if col is K.MUTED:
            d.outline(p, x, 4500, 4900, 1800, K.MUTED, 70)
            d.text(p, x + 200, 4720, 4500, 500, t, 15, K.MUTED, True)
            d.text(p, x + 200, 5240, 4500, 600, s, 11, K.MUTED)
        else:
            d.shape(p, x, 4500, 4900, 1800, col)
            d.text(p, x + 200, 4720, 4500, 500, t, 15, K.INK, True)
            d.text(p, x + 200, 5240, 4500, 600, s, 11, K.INK)
        if s2:
            d.text(p, x + 200, 5780, 4500, 400, s2, 10, K.INK)
    badge(d, p, 15200, 3880, 3400, "* i_dirt=1 더러움", K.PAPER, 550, 11)
    badge(d, p, 21850, 3880, 3400, "* i_dirt=1 더러움", K.PAPER, 550, 11)
    tl = [
        (4100, "get_empty_inode\n194-226", "memset 0 · i_count=1"),
        (10750, "read_inode\n294-312", "32B 복사 · i_lock=0"),
        (17400, "iget 적중 262\nsys_open·fork", "i_count ++"),
        (24050, "iput — i_count>1\n감소만 (176-179)", "i_count −− → 상주로"),
    ]
    for x, t, c in tl:
        d.text(p, x, 6420, 4900, 800, t, 10, K.ORANGE, True)
        d.text(p, x, 7600, 4900, 550, c, 10, K.PAPER)
    for ax in (6300, 12950, 19600, 26250):
        d.text(p, ax, 5050, 800, 600, "→", 18, K.ORANGE, True)
    para(d, p, 1100, 8200, 31500, 2000,
         "더러움(i_dirt=1) 배지의 원인 — file_write(77) · namei:326-327, iput의 write_inode로 벗는다.\n"
         "반납 중 → 비어 있음 — iput이 i_count==1이면(175·190): i_nlinks==0 → truncate+free_inode(180-184) · "
         "i_dirt면 write_inode 후 repeat(185-189).", 12, K.ORANGE, True)
    d.table(p, 1100, 10250, [3900, 7200, 11600, 8800], [
        ["전환", "원인 (inode.c)", "변경 데이터", "유지 조건"],
        ["비어 → 읽는 중", "get_empty_inode 194-226", "i_dev·i_num·i_count=1 (memset 0)", "i_count>0 슬롯은 재사용 안 함"],
        ["읽는 중 → 상주", "read_inode 294-312", "디스크 inode 32B · i_lock=0", "lock 중 wait_on_inode 대기"],
        ["상주 ↔ 공유 · 더러움", "iget 262 · sys_open·fork · file_write", "i_count ±1 · i_dirt=1 (write_inode b_dirt=1)", "i_count = 참조 filp 수"],
        ["상주 → 반납 → 비어", "iput 175-192", "i_count→0 · truncate·free_inode 가능", "i_nlinks==0이면 실제 삭제"],
    ], row_h=830, size=12)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 코드 21–23 (22 배경) ──────────────────────────────────
    # 21 bmap
    p = d.slide("코드: bmap — 직접·단일 간접·이중 간접", K.S_CODE,
                "fs/inode.c:72-148 — 파일 내 블록 번호를 i_zone 지도로 디스크 블록 번호로 · 그림은 다음 장(22)")
    d.code_panel(p, "src/fs/inode.c", 77, 88, 1100, 4300, 15200, 7700,
                 size=9, caption_extra="block<7 직접")
    d.code_panel(p, "src/fs/inode.c", 90, 107, 16900, 4300, 15700, 9800,
                 size=8, caption_extra="단일 간접 i_zone[7]")
    d.outline(p, 1100, 12250, 15200, 1100, K.ORANGE, 110)
    d.text(p, 1400, 12450, 14600, 700,
           "상한 7 + 512 + 512×512 블록 (79-80) · create=1이면 new_block", 15, K.ORANGE, True)
    d.text(p, 1400, 13450, 14600, 650,
           "create_block(145-148) = _bmap(create=1) — 파일을 키우는 쪽만 할당", 13, K.PAPER)
    d.text(p, 1400, 14150, 14600, 500,
           "이중 간접 i_zone[8] — 같은 패턴이 한 단계 더 (109-137)", 13, K.PAPER)
    d.banner(p, "bmap = 읽기(0) · create_block = 쓰기(1) — 같은 _bmap, 간접 블록도 bread로 읽는다")

    # 22 파일 1개의 블록 지도
    p = d.slide("그림: 파일 1개의 블록 지도", K.S_BG,
                "fs/inode.c:72-138 · include/linux/fs.h:124-155 — 직접 7 · 간접 512 · 이중 간접 512×512")
    d.shape(p, 1100, 4300, 5300, 9600, K.PAPER)
    d.text(p, 1350, 4400, 4800, 500, "m_inode — i_zone[9]", 15, K.INK, True)
    for i in range(9):
        fill = K.ORANGE if i >= 7 else K.TEAL
        d.shape(p, 1200, 5050 + i * 980, 5100, 820, fill)
        if i < 7:
            lab = f"i_zone[{i}] — 블록 번호"
        elif i == 7:
            lab = "i_zone[7] — 간접 블록"
        else:
            lab = "i_zone[8] — 이중 간접"
        d.text(p, 1450, 5220 + i * 980, 4800, 500, lab, 11, K.INK, True)
    d.text(p, 7000, 4150, 5600, 500, "직접 — 7블록 · 7 KiB", 14, K.TEAL, True)
    for i in range(7):
        d.shape(p, 7000, 4700 + i * 1100, 5600, 950, K.TEAL)
        d.text(p, 7200, 4900 + i * 1100, 5200, 500, f"데이터 블록 (i_zone[{i}])", 12, K.INK, True)
    d.text(p, 13200, 4150, 8000, 500, "단일 간접 — 512블록 · 512 KiB", 14, K.ORANGE, True)
    nbox(d, p, 13200, 4700, 8000, 1700, "간접 블록 (i_zone[7])", "1024B = unsigned short × 512", K.ORANGE, s1=13, s2=11)
    arrow(d, p, 16700, 6500, "↓", 20, K.ORANGE)
    nbox(d, p, 13200, 6900, 8000, 1700, "데이터 블록 512개", "번호표 배열 → 실제 블록", K.PAPER, s1=13, s2=11)
    d.text(p, 13200, 8950, 8000, 500, "이중 간접 — 512×512블록 · 256 MiB", 14, K.ORANGE, True)
    nbox(d, p, 13200, 9450, 8000, 1700, "1차 블록 (i_zone[8])", "u16 × 512 — 각 항목이 2차 블록", K.ORANGE, s1=13, s2=11)
    arrow(d, p, 16700, 11200, "↓", 20, K.ORANGE)
    nbox(d, p, 13200, 11600, 8000, 1700, "2차 블록 → 데이터 512×512개", "block>>9 → block&511 (119·130)", K.PAPER, s1=13, s2=11)
    d.shape(p, 22000, 4700, 10600, 1500, K.ORANGE)
    d.text(p, 22300, 4820, 10000, 550, "file_read: bmap(inode, f_pos/1024)", 16, K.INK, True)
    d.text(p, 22300, 5450, 10000, 500, "f_pos 0…1023 → 블록 0 → i_zone[0]", 13, K.INK)
    para(d, p, 22000, 6500, 10600, 4400,
         "최대 = 7 + 512 + 512×512 = 262,663 블록 ≈ 256.5 MiB (79-80)\n\n"
         "s_max_size — 슈퍼 블록의 상한 필드(mkfs 기입). 작은 파일은 직접 7칸으로 끝 — "
         "간접 블록 읽기가 없다.", 15)
    nbox(d, p, 22000, 11100, 10600, 1500, "s_log_zone_size = 0",
         "존 = 블록 = 1024B (§7) — 지도 단위와 I/O 단위가 같다", None, K.TEAL, K.TEAL, K.MUTED, s1=14, s2=11)
    para(d, p, 22000, 12900, 10600, 1400,
         "file_write는 create_block으로 지도 칸을 채운다(23장).", 14)
    d.banner(p, "파일 = 번호표 상자들의 연쇄 — inode 하나가 최대 256 MiB까지 가리킨다")

    # 23 new_block과 new_inode
    p = d.slide("코드: new_block과 new_inode", K.S_CODE,
                "fs/bitmap.c:75-105, 136-168 — 비트맵에서 첫 0비트를 찾아 1로 만든다 (05장 배치 그림 연결)")
    d.code_panel(p, "src/fs/bitmap.c", 83, 93, 1100, 4300, 15200, 7300,
                 size=9, caption_extra="zmap 첫 0비트")
    d.code_panel(p, "src/fs/bitmap.c", 100, 104, 16900, 4300, 15700, 4600,
                 size=10, caption_extra="getblk 후 0으로 채움")
    d.code_panel(p, "src/fs/bitmap.c", 156, 162, 16900, 9100, 15700, 5300,
                 size=10, caption_extra="new_inode 발췌")
    d.text(p, 1100, 11900, 15200, 500, "존 비트맵 s_zmap[i] — 첫 0비트가 곧 새 블록", 13, K.TEAL, True)
    for i, b in enumerate(["1", "1", "1", "0", "1", "1", "0", "…"]):
        x = 1100 + i * 1900
        if i == 3:
            d.shape(p, x, 12500, 1750, 1100, K.ORANGE)
        else:
            d.shape(p, x, 12500, 1750, 1100, K.PAPER)
        d.text(p, x + 200, 12750, 1350, 600, b, 16, K.INK, True)
    d.text(p, 5600, 13700, 900, 500, "▲ j", 12, K.ORANGE, True)
    para(d, p, 9200, 12550, 7100, 1900,
         "블록 번호 = j + i×8192 + s_firstdatazone − 1 (93)\n"
         "set_bit 후 b_dirt=1(92) — 비트맵 버퍼가 곧 디스크.\n"
         "clear_block으로 0으로 채우고 b_uptodate=1 (100-102).", 13)
    d.banner(p, "inode도 블록도 같은 방식 — 비트맵의 첫 빈칸 · new_inode는 i_count=1로 태어난다")

    # ── 시연 24–25 ────────────────────────────────────────────
    # 24 시연 A 계획
    p = d.slide('시연 A 계획: namei("/etc/rc")', K.S_DEMO,
                "fs/namei.c:91-330 · fs/inode.c:244-338 · init/main.c:179-183 — lab/ QEMU i386 + GDB · 심볼 _ 접두 주의(§11)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — namei 추적 계획",
              '(gdb) b namei ; b find_entry ; b iget\n'
              '(gdb) c        # 게스트 셸: cat /etc/rc\n'
              '#  부팅 직후 init의 open을 잡으려면 b open_namei 후 c\n'
              'Breakpoint 1, namei (pathname=0x2fe8 ...)\n'
              '    at fs/namei.c:303\n'
              '(gdb) c        # find_entry 1회차\n'
              '(gdb) p (*dir)->i_num     # 1 — root\n'
              '(gdb) p namelen           # 3 — "etc"\n'
              '#  x/s name은 커널 DS 기준 — 엉뚱한 곳을 가리킴\n'
              '#  → namelen·de->name(커널 버퍼)으로 확인 (§5)\n'
              '(gdb) b namei.c:145 ; c   # 반환 직전\n'
              '(gdb) p *de   # {inode=k, name="etc"}\n'
              '(gdb) c        # find_entry 2회차 — "rc"\n'
              '(gdb) p (*dir)->i_num ; p namelen   # k, 2\n'
              '(gdb) c ; p *de   # {inode=m, name="rc"}\n'
              'Breakpoint 3, iget (dev=774, nr=m)\n'
              '(gdb) finish   # namei 반환값\n'
              '(gdb) p *$     # i_num=m · i_zone[0]=z', start=11)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· find_entry 1회차 — root(i_num=1)에서 \"etc\" 적중 → k\n"
         "· 2회차 — etc(k)에서 \"rc\" 적중 → m\n"
         "· iget 진입 dev·nr\n"
         "· namei 반환 inode — i_mode·i_size·i_zone[0]=z\n\n"
         "16장 상태도의 기호 k·m·z를 이 값으로 채운다.\n\n"
         "캡처 01-03은 다음 장(25).\n"
         "값은 lab 루트 이미지 기준 — 이미지마다 다르다(§8).", 14)
    d.banner(p, "fs 세그먼트 함정 — 경로 문자열 검사는 x/s 대신 namelen·de->name으로 (§11)")

    # 25 시연 A 캡처
    p = d.slide("시연 A 캡처", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 캡처 파일 materials/12-filesystem/captures/01-05 · k·m·z는 예시(§8)")
    ph_panel(d, p, 1100, 4300, 10100, 10100,
             "# 1회차 — root에서 \"etc\"\n"
             "(gdb) p (*dir)->i_num\n"
             "$1 = 1        # root\n"
             "(gdb) p namelen\n"
             "$2 = 3        # \"etc\"\n"
             "(gdb) b namei.c:145\n"
             "(gdb) c\n"
             "(gdb) p *de\n"
             "$3 = {inode = 6,\n"
             "      name = \"etc\"}\n"
             "#  k = 6 (예시)",
             "01-find-entry-etc.png")
    ph_panel(d, p, 11800, 4300, 10100, 10100,
             "# 2회차 — etc(k)에서 \"rc\"\n"
             "(gdb) c\n"
             "(gdb) p (*dir)->i_num\n"
             "$4 = 6        # etc\n"
             "(gdb) p namelen\n"
             "$5 = 2        # \"rc\"\n"
             "(gdb) c ; p *de\n"
             "$6 = {inode = 15,\n"
             "      name = \"rc\"}\n"
             "(gdb) p dev ; p nr\n"
             "$7 = 774 ; $8 = 15\n"
             "#  m = 15 — iget(774, 15)",
             "02-find-entry-rc.png")
    ph_panel(d, p, 22500, 4300, 10100, 10100,
             "# namei 반환 inode\n"
             "(gdb) finish\n"
             "Value returned is ...\n"
             "(gdb) p *$\n"
             "$9 = {i_mode = 0100644,\n"
             "      i_size = 814,\n"
             "      i_num = 15,\n"
             "      i_zone = {165, ...}}\n"
             "#  z = i_zone[0] = 165\n"
             "#  (예시 — 실측 아님)\n"
             "#\n"
             "#  16장 상태도에 대입",
             "03-namei-return-inode.png")
    para(d, p, 1100, 14600, 31500, 1600,
         "왼쪽부터 01·02·03 — 찾은 디렉터리의 i_num(1→k), 각 회차 de->inode(k→m), 반환 inode의 "
         "i_num=m·i_zone[0]=z. i_mode 0100644 = 일반 파일·0644.", 13)

    # ── 코드 26–27 ────────────────────────────────────────────
    # 26 open_namei 1/2
    p = d.slide("코드: open_namei (1/2) — 엔트리 없음·생성", K.S_CODE,
                "fs/namei.c:337-410 전반 — 원 23 분할 1/2 · O_CREAT 경로 (후반 검사는 27장)")
    d.code_panel(p, "src/fs/namei.c", 346, 359, 1100, 4300, 15200, 8800,
                 size=9, caption_extra="umask·O_TRUNC")
    d.code_panel(p, "src/fs/namei.c", 378, 390, 16900, 4300, 15700, 7800,
                 size=10, caption_extra="O_CREAT 생성 경로")
    para(d, p, 1100, 13250, 31500, 1350,
         "엔트리 없음(361-377) — O_CREAT 없으면 -ENOENT · new_inode로 만들고 add_entry가 이름을 쓴다: "
         "de->inode = i_num (385-386).", 13)
    d.banner(p, "umask 반영(348) · mode |= I_REGULAR(349) — 생성 파일은 처음부터 일반 파일")

    # 27 open_namei 2/2
    p = d.slide("코드: open_namei (2/2) — 엔트리 있음·검사", K.S_CODE,
                "fs/namei.c:392-410 후반 · permission(40-54) — 원 23 분할 2/2 · O_EXCL 콜아웃")
    d.code_panel(p, "src/fs/namei.c", 392, 407, 1100, 4300, 19700, 9800,
                 size=9, caption_extra="O_EXCL · permission · O_TRUNC")
    para(d, p, 22000, 4300, 10000, 4700,
         "검사 순서 — 1. O_EXCL → -EEXIST (396-397) · 2. iget(398) · "
         "3. 디렉터리 쓰기 → -EPERM (400) · 4. permission(inode, ACC_MODE(flag)) (401) · "
         "5. O_TRUNC → truncate (406-407) → *res_inode (408)", 14)
    d.outline(p, 22000, 9200, 10000, 2800, K.ORANGE, 110)
    d.text(p, 22500, 9350, 9000, 500, "0.11 특이 동작 — O_EXCL", 15, K.ORANGE, True)
    para(d, p, 22500, 9900, 9000, 1900,
         "O_CREAT 없이도 검사된다(396-397) — POSIX 의미로 설명하지 않는다(§8). "
         "슬라이드 43의 Q3.", 14, K.ORANGE)
    d.banner(p, "읽기/쓰기 허용은 이 시점에만 검사된다 — sys_read는 pipe 외 모드를 다시 보지 않는다(§8)")

    # ── 비교 28–29 ────────────────────────────────────────────
    # 28 접근 모드
    p = d.slide("비교: 접근 모드 (O_ACCMODE 값 4가지 전부)", K.S_CMP,
                "fs/namei.c:21, 40-54 · fs/open.c:179 · fs/read_write.c:67 — ACC_MODE 표 원문으로 전수 조사")
    d.table(p, 1100, 4300, [5600, 4300, 7600, 14000], [
        ["접근 모드", "flag 하위 2비트", "ACC_MODE[mask] → 요구", "permission 결과 (47-53)"],
        ["O_RDONLY (0)", "00", "\\004 → MAY_READ(4)", "소유자 r 비트 검사 — 읽기"],
        ["O_WRONLY (1)", "01", "\\002 → MAY_WRITE(2)", "소유자 w 비트 검사 — 쓰기"],
        ["O_RDWR (2)", "10", "\\006 → 6 (READ|WRITE)", "r·w 둘 다 검사"],
        ["3 (정의 안 됨)", "11", "\\377 → 모든 비트", "(mode&mask&7)==mask 불가 — 사실상 거부, suser()만 통과(51)"],
    ], row_h=950, size=14)
    d.code_panel(p, "src/fs/namei.c", 47, 53, 1100, 9350, 15200, 5250,
                 size=9, caption_extra="")
    para(d, p, 16900, 9300, 15700, 5300,
         'namei.c:21 — #define ACC_MODE(x) ("\\004\\002\\006\\377"[(x)&O_ACCMODE]) : 배열 인덱스로 요구 마스크를 얻는다.\n\n'
         "0.11 특이점 — f_mode에는 접근 모드가 아니라 i_mode가 통째로 저장된다(open.c:179). "
         "sys_read:67의 f_mode&1은 pipe 전용 검사다(§8).", 13)
    d.banner(p, "2비트짜리 값 네 가지 전부 — 세 번째까지가 상식, 네 번째(3)는 사실상 거부")

    # 29 나머지 open 플래그
    p = d.slide("비교: 나머지 open 플래그 (fcntl.h 전부)", K.S_CMP,
                "include/fcntl.h:7-17 · fs/namei.c·fs/file_dev.c·fs/fcntl.c — 정의된 것과 검사되는 것을 분리한다")
    d.table(p, 1100, 4300, [5300, 3400, 11000, 11800], [
        ["플래그 (값)", "판정", "검사·동작 위치", "비고"],
        ["O_CREAT (00100)", "커널이 검사", "open_namei namei.c:362·370-390", "없으면 생성 — new_inode·add_entry (26장)"],
        ["O_EXCL (00200)", "커널이 검사", "namei.c:396-397", "있으면 -EEXIST — O_CREAT 없이도 검사(27장)"],
        ["O_TRUNC (01000)", "커널이 검사", "namei.c:346-347·406-407", "접근 모드 없으면 O_WRONLY 강제"],
        ["O_APPEND (02000)", "커널이 검사", "file_dev.c:60-61·85 · fcntl.c:67-68", "쓰기 위치를 i_size로 (34장)"],
        ["O_NONBLOCK=O_NDELAY (04000)", "저장만", "fcntl.c:67-68 (F_SETFL)", "어디서도 검사 안 함 — '비차단 지원'이라 말하지 않는다(§8)"],
        ["O_NOCTTY (00400)", "무시", "없음 (fcntl.h:6 주석)", "참조하는 코드가 없다"],
    ], row_h=1100, size=13)
    para(d, p, 1100, 12300, 31500, 1500,
         "fcntl.h:11-17의 플래그 전부 — '정의되었다'와 '검사된다'는 다르다. F_SETFL이 저장하는 것도 "
         "O_APPEND·O_NONBLOCK 둘뿐이다(fcntl.c:67-68).", 15)
    d.banner(p, "open 플래그 읽는 법 — 값(fcntl.h) → 검사 위치 → 판정 3단계")

    # ── 코드 30–31 ────────────────────────────────────────────
    # 30 sys_open
    p = d.slide("코드: sys_open", K.S_CODE,
                "fs/open.c:138-185 · init/main.c:180-181 — fd → file_table → open_namei 순서 (08장 구조도 재지시)")
    d.code_panel(p, "src/fs/open.c", 144, 161, 1100, 4300, 12800, 9800,
                 size=8, caption_extra="슬롯 확보")
    d.code_panel(p, "src/fs/open.c", 174, 184, 14700, 4300, 17900, 7300,
                 size=9, caption_extra="f_mode = i_mode 복사")
    para(d, p, 14700, 11800, 17900, 2700,
         "tty 특례(162-175) — major 4면 제어 터미널 지정 · 블록 장치는 check_disk_change(177-178) · "
         "init은 close(0) 뒤 open으로 fd 0(main.c:180-181)", 13)
    d.banner(p, "① 빈 fd ② f_count++ 후 open_namei(157) ③ f_* 채움 — 실패면 158-160 되돌림")

    # 31 sys_read / sys_write 분기
    p = d.slide("코드: sys_read / sys_write 분기", K.S_CODE,
                "fs/read_write.c:55-103 — if 사다리 전체는 다음 표(32)로 · rw_char은 13회차")
    d.code_panel(p, "src/fs/read_write.c", 66, 80, 1100, 4300, 15200, 9300,
                 size=9, caption_extra="sys_read 분기")
    d.code_panel(p, "src/fs/read_write.c", 93, 102, 16900, 4300, 15700, 6800,
                 size=9, caption_extra="S_ISDIR 없음")
    ladder_r = ["i_pipe → read_pipe", "S_ISCHR → rw_char", "S_ISBLK → block_read",
                "S_ISDIR|S_ISREG → file_read", "그 외 → -EINVAL"]
    ladder_w = ["i_pipe → write_pipe", "S_ISCHR → rw_char", "S_ISBLK → block_write",
                "S_ISREG → file_write", "그 외 → -EINVAL"]
    d.text(p, 16900, 11350, 7400, 450, "sys_read 사다리", 12, K.TEAL, True)
    d.text(p, 24700, 11350, 7900, 450, "sys_write 사다리", 12, K.TEAL, True)
    for i in range(5):
        y = 11800 + i * 520
        for x, lab, wd in ((16900, ladder_r[i], 7400), (24700, ladder_w[i], 7900)):
            if i == 3 and x == 24700:
                d.shape(p, x, y, wd, 460, K.ORANGE)
                d.text(p, x + 150, y + 40, wd - 300, 380, lab, 11, K.INK, True)
            else:
                nbox(d, p, x, y, wd, 460, lab, None,
                     K.PAPER if i < 4 else None, K.INK if i < 4 else K.MUTED, s1=11)
    d.banner(p, "공통 검사(60-64) — fd·count·verify_area(64) · 쓰기 사다리는 디렉터리가 빠진다")

    # ── 비교 32 ───────────────────────────────────────────────
    p = d.slide("비교: 파일 종류별 read/write 경로", K.S_CMP,
                "fs/read_write.c:66-80, 93-102 — sys_read의 i_mode 분기 전부 · sys_write와의 차이 포함")
    d.table(p, 1100, 4300, [5000, 9200, 8700, 8600], [
        ["종류 (i_mode)", "sys_read (66-80)", "sys_write (93-102)", "비고"],
        ["pipe (i_pipe)", "read_pipe — f_mode&1 검사(67)", "write_pipe — f_mode&2(94)", "f_mode 비트 검사는 pipe뿐"],
        ["문자 장치 S_ISCHR", "rw_char(READ, i_zone[0], …) (69)", "rw_char(WRITE, i_zone[0], …) (96)", "i_zone[0]=장치 번호 — 13회차"],
        ["블록 장치 S_ISBLK", "block_read(i_zone[0], …) (71)", "block_write(…) (98)", "버퍼 캐시 직접 (fs/block_dev.c)"],
        ["디렉터리 S_ISDIR", "file_read — count를 i_size로(73-74)", "-EINVAL (사다리에 없음)", "읽기만 — sys_read:72"],
        ["일반 파일 S_ISREG", "file_read (77)", "file_write (100)", "오늘의 본류 — 33·34장"],
        ["그 외", "printk + -EINVAL (79-80)", "printk + -EINVAL (101-102)", "위 5종 외에는 없음"],
    ], row_h=1080, size=13)
    para(d, p, 1100, 12900, 31500, 1600,
         "i_zone[0]이 장치 파일에서는 장치 번호로 재사용된다 — 같은 필드, 문맥별 의미(31장). "
         "디렉터리도 file_read로 읽는다: 내용은 dir_entry 16B의 배열일 뿐(42장 오해 2).", 15)
    d.banner(p, "read는 5갈래, write는 4갈래 — 빠진 하나가 디렉터리 쓰기다")

    # ── 코드 33–34 ────────────────────────────────────────────
    # 33 file_read
    p = d.slide("코드: file_read", K.S_CODE,
                "fs/file_dev.c:17-46 — 원 29 분할 1/2 · bmap + bread + put_fs_byte · 구멍 경로")
    d.code_panel(p, "src/fs/file_dev.c", 22, 33, 1100, 4300, 15200, 7800,
                 size=9, caption_extra="bmap + bread | NULL")
    d.code_panel(p, "src/fs/file_dev.c", 34, 42, 16900, 4300, 15700, 6300,
                 size=9, caption_extra="put_fs_byte · 구멍")
    d.outline(p, 16900, 10900, 15700, 1900, K.ORANGE, 110)
    d.text(p, 17200, 11050, 15100, 500, "구멍(hole) — bmap이 0을 반환한 구간", 15, K.ORANGE, True)
    d.text(p, 17200, 11600, 15100, 450, "디스크를 읽지 않고 0으로 채워 돌려준다 (39-42)", 12, K.ORANGE)
    d.text(p, 17200, 12100, 15100, 450, "쓰기는 반대로 create_block이 새 블록을 할당 (65 · 34장)", 12, K.ORANGE)
    para(d, p, 1100, 12150, 15200, 2400,
         "chars = MIN(BLOCK_SIZE−offset, left)(31)로 블록 경계마다 자른다 · 읽은 뒤 i_atime 갱신(44) — "
         "읽기도 inode를 더럽힌다 · bmap·bread 실패면 읽은 만큼 반환(45).", 14)
    d.banner(p, "file_read — 계산된 블록 번호로 데이터를 되돌리는 길 (04장 보조 화살표의 실체)")

    # 34 file_write
    p = d.slide("코드: file_write", K.S_CODE,
                "fs/file_dev.c:48-90 — 원 29 분할 2/2 · O_APPEND·create_block·b_dirt=1(71) — 11회차 연결")
    d.code_panel(p, "src/fs/file_dev.c", 60, 77, 1100, 4300, 15200, 9800,
                 size=8, caption_extra="71: b_dirt=1")
    d.code_panel(p, "src/fs/file_dev.c", 79, 86, 16900, 4300, 15700, 5800,
                 size=9, caption_extra="get_fs_byte 루프")
    para(d, p, 16900, 10400, 15700, 4100,
         "· 71 bh->b_dirt = 1 — 11회차 지연 쓰기의 그 줄\n"
         "· create_block(65) = _bmap(create=1) — new_block 할당(23장)\n"
         "· 부분 쓰기 → 먼저 bread(67) · i_size 확장(75-78) · i_mtime(84)", 14)
    d.banner(p, "쓰기의 흔적은 두 곳 — 데이터 블록 버퍼의 b_dirt와 inode의 i_dirt (write_inode, 19장)")

    # ── 시연 35–38 ────────────────────────────────────────────
    # 35 시연 B 계획
    p = d.slide("시연 B 계획: open_namei와 fd 슬롯", K.S_DEMO,
                "fs/open.c:138-185 · fs/namei.c:337-410 — lab/ QEMU i386 + GDB · 줄 번호는 lab 기준(src와 다를 수 있음, §11)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — sys_open·fd 슬롯 계획",
              "(gdb) b sys_open ; b open.c:184\n"
              "(gdb) c   # 게스트 셸: cat /etc/rc\n"
              "#  open.c:184 줄번호는 lab 소스에서 확인 (§11)\n"
              "Breakpoint 1, sys_open (filename=...,\n"
              "    flag=0, mode=0)\n"
              "(gdb) p/o flag       # 0 — O_RDONLY\n"
              "(gdb) p current->filp[0]@3\n"
              "$1 = {0x37d80, 0x37dc0, 0x37e00}\n"
              "#                   ^ 0·1·2 = tty inode\n"
              "(gdb) c     # fd 루프(open.c:156) 통과 후\n"
              "(gdb) p fd           # 3 — 셸이 0-2 사용\n"
              "(gdb) p f - file_table   # 슬롯 인덱스\n"
              "(gdb) c     # open_namei 반환 후\n"
              "(gdb) p inode->i_num ; p/o inode->i_mode\n"
              "(gdb) c     # open.c:184 — f 필드 직후\n"
              "(gdb) p *f   # f_inode·f_pos=0·f_flags", start=11)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· flag=0 — O_RDONLY(28장 표 1행)\n"
         "· filp[0..2] — 셸의 표준 입출력(tty inode)\n"
         "· fd=3 — 가장 작은 빈 번호(145-147)\n"
         "· f - file_table — ②번 슬롯(08장)\n"
         "· *f — f_inode(rc#m)·f_pos=0·f_flags\n\n"
         "캡처 04는 37장.\n\n"
         "sys_open이 세 자료구조를 잇는 순서(30장)를 그대로 본다.", 14)
    d.banner(p, "08장 대응 구조도의 실측 — fd 3 → file_table[i] → inode_table[rc#m]")

    # 36 시연 C 계획
    p = d.slide("시연 C 계획: file_read → bmap → bread", K.S_DEMO,
                "fs/file_dev.c:17-46 · fs/inode.c:72-148 · fs/buffer.c — 문자열→블록의 마지막 고리 · 11회차 시연 A와 로그 공유 가능(§5)")
    auto_pane(d, p, 1100, 4300, 19700, 10100, "GDB — 블록 번호 일치 계획",
              "(gdb) b file_read ; b bmap ; b bread\n"
              "(gdb) c   # 같은 cat /etc/rc 이어서\n"
              "Breakpoint 1, file_read (inode=...,\n"
              "    filp=..., buf=..., count=...)\n"
              "    at fs/file_dev.c:17\n"
              "(gdb) p filp->f_pos    # 0\n"
              "(gdb) p count          # 읽기 요청량\n"
              "(gdb) finish   # bmap(inode, f_pos/1024)\n"
              "Value returned is z\n"
              "#                   ^ 디스크 블록 번호\n"
              "(gdb) c\n"
              "Breakpoint 3, bread (dev=774, block=z)\n"
              "    at fs/buffer.c:142\n"
              "(gdb) p dev ; p block  # block == z\n"
              "#  dev=0x306 — 루트 장치(이미지 설정별, §11)\n"
              "#  bmap 반환 = 시연 A의 i_zone[0] = 165", start=11)
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 포인트\n\n"
         "· file_read 진입 — f_pos=0, count\n"
         "· bmap 반환값 z = 시연 A(25장)의 rc i_zone[0]\n"
         "· bread 진입 block=z 일치\n"
         "· dev — 루트 장치 번호(0x306 예시)\n\n"
         "이 일치가 \"/etc/rc\"라는 문자열이 디스크 블록이 되는 마지막 고리다 — 39장 답 체인의 7·8번.\n\n"
         "캡처 05는 38장.", 14)
    d.banner(p, "bmap의 반환값과 bread의 인자가 같은 숫자 — 오늘 120분의 결론 미리 보기")

    # 37 시연 B 캡처
    p = d.slide("시연 B 캡처: fd 슬롯과 file_table", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 값은 예시(실측 아님) · cat은 공유 라이브러리 없이 단일 open(§2 추론)")
    d.placeholder_output(p, 1100, 4300, 19700, 10100,
                         "(gdb) b sys_open ; b open.c:184 ; c\n"
                         "#  게스트 셸: cat /etc/rc\n"
                         "Breakpoint 1, sys_open (flag=0, mode=0)\n"
                         "(gdb) p/o flag\n"
                         "$1 = 0                    # O_RDONLY\n"
                         "(gdb) p current->filp[0]@3\n"
                         "$2 = {0x37d80, 0x37dc0, 0x37e00}   # 0·1·2 = tty\n"
                         "(gdb) c                  # open.c:156 통과 후\n"
                         "(gdb) p fd\n"
                         "$3 = 3                    # 셸이 0-2를 쓰므로\n"
                         "(gdb) p f - file_table\n"
                         "$4 = 12                   # file_table[12]\n"
                         "(gdb) c                  # open.c:184\n"
                         "(gdb) p *f\n"
                         "$5 = {f_mode = 0100644, f_flags = 0, f_count = 1,\n"
                         "      f_inode = 0x21a0, f_pos = 0}\n"
                         "(gdb) p f->f_inode->i_num\n"
                         "$6 = 15                   # m — 시연 A와 동일",
                         "04-sys-open-fd-slot.png")
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 대상(§5)\n\n"
         "· flag=0 — O_RDONLY\n"
         "· filp[0..2] — tty inode\n"
         "· fd=3, file_table[12]\n"
         "· f_mode=0100644 — i_mode가 통째로(§8)\n"
         "· f_pos=0 — 열린 파일마다(08장)\n"
         "· f_inode->i_num = m(=15) — 25장 캡처와 동일 inode\n\n"
         "08장 구조도의 ①②③이 실제로 어떻게 채워지는지 보여준다.", 14)
    d.banner(p, "f_mode=0100644는 접근 모드가 아니라 i_mode의 복사다 — 28장 특이점의 실측 (§8)")

    # 38 시연 C 캡처
    p = d.slide("시연 C 캡처: bmap과 bread의 블록 번호 일치", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 11회차 시연 A와 같은 로그를 공유해도 된다(§5)")
    d.placeholder_output(p, 1100, 4300, 19700, 10100,
                         "(gdb) b file_read ; b bmap ; b bread ; c\n"
                         "Breakpoint 1, file_read (filp=..., count=1024)\n"
                         "(gdb) p filp->f_pos\n"
                         "$7 = 0\n"
                         "(gdb) finish             # bmap(inode, 0/1024)\n"
                         "Value returned is 165\n"
                         "#                        ^ z — 시연 A의 i_zone[0]\n"
                         "(gdb) c\n"
                         "Breakpoint 3, bread (dev=774, block=165)\n"
                         "    at fs/buffer.c:142\n"
                         "(gdb) p dev\n"
                         "$8 = 774                 # 0x306 — 루트 장치\n"
                         "(gdb) p block\n"
                         "$9 = 165                 # z와 일치!\n"
                         "#\n"
                         "#  bmap 반환 165 == bread block 165\n"
                         "#  = 25장 $9 의 i_zone[0]",
                         "05-bmap-bread-block-match.png")
    para(d, p, 22000, 4300, 10000, 10100,
         "관찰 대상(§5)\n\n"
         "· f_pos=0 → 파일 블록 0\n"
         "· bmap 반환 z=165\n"
         "· bread(dev=0x306, block=165)\n\n"
         "세 숫자가 같다 — 문자열 \"/etc/rc\"가 디스크 블록 번호 165가 된 순간.\n\n"
         "39장 답 체인의 7·8번에 이 값을 넣는다. 실제 I/O는 캐시 미스일 때만(11회차) — "
         "open이 이미 읽었을 수 있다.", 14)
    d.banner(p, "z=165(예시) — 시연 A(25장)의 i_zone[0]·시연 C의 bread 인자가 한 숫자로 만난다")

    # ── 정답 39 ───────────────────────────────────────────────
    p = d.slide('질문의 답: "/etc/rc" → 디스크 블록', K.S_ANS,
                "fs/namei.c · fs/inode.c · fs/file_dev.c — 오늘 전체 · 11장 호출 순서도에 값(k·m·z)을 채운 최종판")
    steps = [
        ('문자열 "/etc/rc"', "사용자 공간 — get_fs_byte로 한 글자씩 (12장)", K.PAPER),
        ("'/' → current->root", "inode 1 — 부팅 때 mount_root가 (09장)", K.TEAL),
        ('bread(root.i_zone[0])', '64 dir_entry 중 "etc" → inode k (14장·16장)', K.PAPER),
        ("read_inode(k)", "bread(2+imap+zmap+(k-1)/32) — etc inode 적재 (18장)", K.ORANGE),
        ("bread(etc.i_zone[0])", 'dir_entry 중 "rc" → inode m', K.PAPER),
        ("read_inode(m)", "같은 산식 — rc inode 적재 · i_zone[9] 지도 확보", K.ORANGE),
        ("rc.i_zone[0] = z", "bmap(f_pos/1024) — 파일 블록 0 (21장·22장)", K.PAPER),
        ("bread(dev, z) → put_fs_byte", "file_read — 사용자 버퍼로 (33장)", K.TEAL),
    ]
    for i, (t, s, fill) in enumerate(steps):
        col = i % 2
        row = i // 2
        x = 1100 + col * 16100
        y = 4300 + row * 2400
        nbox(d, p, x, y, 14400 if col == 0 else 15500, 2000,
             f"{i + 1}  {t}", s, fill, s1=15, s2=11)
        if col == 0:
            d.text(p, 15700, y + 650, 1000, 600, "→", 22, K.ORANGE, True)
        elif row < 3:
            d.text(p, 8000, y + 2000, 1000, 450, "↓", 18, K.ORANGE, True)
    para(d, p, 1100, 13700, 31500, 700,
         "예시 값 — k=6 · m=15 · z=165 (25·38장 캡처).", 13, K.MUTED)
    d.banner(p, "디스크 접근은 모두 bread — 실제 I/O는 캐시 미스일 때뿐(11회차) · open은 디렉터리·inode 블록만")

    # ── 배경 40–42 ────────────────────────────────────────────
    # 40 세 표의 수명 정리
    p = d.slide("세 표의 수명 정리", K.S_BG,
                "include/linux/fs.h:157-164 · fs/open.c:187-208 · fs/inode.c:150-226 — 08장 대응 구조도 재사용")
    d.table(p, 1100, 4300, [4600, 3100, 8400, 7400, 8000], [
        ["표 (크기)", "소유", "누가 증가", "누가 감소", "0이 되면"],
        ["filp[NR_OPEN=20]\n(sched.h:102)", "태스크마다", "sys_open(156) · fork 복사 · dup", "sys_close(201) · do_exit", "슬롯 NULL — fd 번호 재사용"],
        ["file_table[NR_FILE=64]", "전역 공유", "sys_open — f_count++ (156)", "sys_close — 0이면 iput (204-206)", "f_count=0 — 슬롯 재사용"],
        ["inode_table[NR_INODE=32]", "전역 공유", "iget(262) · get_empty_inode(224)", "iput — 분기 4갈래 (176-192)", "i_count=0 — get_empty_inode 후보"],
    ], row_h=1450, size=13)
    para(d, p, 1100, 10400, 31500, 4200,
         "증가·감소가 짝으로 맞는다 — fork는 filp 배열을 통째로 복사해 f_count만 올리고(06회차), "
         "do_exit은 filp를 비우며 iput을 세 번 부른다(10회차).\n"
         "file_table은 inode보다 늘 나이가 짧다 — f_count가 먼저 0이 되고 그때 iput으로 i_count를 내린다"
         "(open.c:204-206). 08장 그림의 아래 두 단이 사라지는 순간이다.", 15)
    d.banner(p, "열기는 아래에서부터 채우고 닫기는 위에서부터 비운다 — filp → file_table → inode_table")

    # 41 현대 커널과의 차이
    p = d.slide("현대 커널과의 차이 (짧게)", K.S_BG,
                "—(현대 비교 · 14회차 연결) — 'Linux 0.11에는 없다/다르다'고만 짚고 넘어간다 (01장 약속)")
    d.table(p, 1100, 4300, [9000, 9000, 13500], [
        ["Linux 0.11 (오늘)", "현대 커널", "비고"],
        ["inode_table[32] 고정", "슬랩 캐시 + 해시", "iget 선형 탐색 → dcache·inode 캐시"],
        ["namei 선형 디렉터리 탐색", "dcache + 경로 워크", "14자 고정 → 가변 길이 dentry"],
        ["i_zone[9] 직접·간접·이중", "ext4 extent 트리", "3단계 간접 → 연속 범위 표현"],
        ["sys_read의 if 사다리", "VFS file_operations", "종류별 분기 → f_op->read 테이블"],
        ["dir_entry 16B 고정", "가변 길이 엔트리", "이름 14자 제한 사라짐 · dt_type 추가"],
    ], row_h=1150, size=14)
    para(d, p, 1100, 11800, 31500, 2700,
         "뼈대는 같다 — 경로 → inode → 블록 매핑 → 디바이스. 다른 것은 규모와 간접 계층이다. "
         "VFS 계층화(file_operations)가 오늘의 if 사다리를 어떻게 대체하는지는 14회차에서 다시 본다.", 15)
    d.banner(p, "현대 자료를 읽을 때 주의 — inode는 해시 캐시, 경로는 dcache, 파일은 extent — 0.11에는 모두 없다")

    # 42 흔한 오해
    p = d.slide("흔한 오해", K.S_BG,
                "fs/inode.c:303-309 · fs/read_write.c:72 · fs/open.c:179 — 오해 4개 반박 (§8 원문 계승)")
    qbox(d, p, 1100, 4300, 15200, 4800, "오해 1",
         "\"inode 번호가 블록 번호다\" — 아니다. 번호는 inode 표 안의 순번이고, 블록은 산식 "
         "2 + s_imap_blocks + s_zmap_blocks + (n-1)/32 로 구한다(inode.c:303-309). "
         "블록 안 위치는 (n-1)%32.", K.TEAL, 14)
    qbox(d, p, 16900, 4300, 15700, 4800, "오해 2",
         "\"디렉터리는 특별한 파일 종류다\" — 내용은 dir_entry 16B의 배열인 일반 블록 나열이고, "
         "file_read로 읽는다(sys_read:72). 커널이 특별 취급하는 것은 쓰기 금지(쓰기 사다리에 없음)뿐.", K.TEAL, 14)
    qbox(d, p, 1100, 9400, 15200, 4800, "오해 3",
         "\"open이 파일 내용을 읽는다\" — open이 읽는 것은 디렉터리 블록과 inode 블록뿐. "
         "데이터 블록은 read가 처음 요청할 때 file_read의 bread로 읽는다(33장). "
         "\"open하면 디스크를 n번 읽는다\"는 수치를 단정하지 않는다(§8).", K.ORANGE, 14)
    qbox(d, p, 16900, 9400, 15700, 4800, "오해 4",
         "\"f_mode는 접근 모드다\" — 0.11은 i_mode를 통째로 복사해 둔다(open.c:179). "
         "현대 커널의 f_mode(FMODE_READ 등)와 같다고 말하지 않는다. 모드 재검사는 pipe뿐(read_write.c:67·94).", K.ORANGE, 14)
    d.banner(p, "번호·디렉터리·open·f_mode — 오늘 가장 헷갈리기 쉬운 네 지점 (§8)")

    # 43 이해 확인 (정답 포함)
    p = d.slide("이해 확인 (정답 포함)", K.S_QUIZ,
                "fs/inode.c:303-309 · fs/namei.c:257-258, 285-292, 315, 396-397 · fs/file_dev.c:28-29, 39-42, 65 — 원문 계승(§6)")
    qbox(d, p, 1100, 4300, 15200, 4800, "Q1 · 정답",
         "Q. inode 번호 n의 디스크 inode가 들어 있는 블록 번호는?\n"
         "A. 2 + s_imap_blocks + s_zmap_blocks + (n-1)/32, 블록 안 위치는 (n-1)%32 "
         "(inode.c:303-309). 1블록 1024B에 32B inode 32개(fs.h:55).", K.TEAL, 14)
    qbox(d, p, 16900, 4300, 15700, 4800, "Q2 · 정답",
         "Q. get_dir(\"/etc/rc\")가 반환하는 inode는? \"rc\"는 누가 처리하는가?\n"
         "A. etc 디렉터리의 inode — '/'가 더 없으면 현재 inode 반환(257-258). \"rc\"는 dir_namei가 "
         "basename으로 잘라(285-292) find_entry가 처리(315·360).", K.TEAL, 13)
    qbox(d, p, 1100, 9400, 15200, 4800, "Q3 · 정답",
         "Q. open(path, O_WRONLY|O_EXCL, 0)을 이미 존재하는 파일에 하면?\n"
         "A. -EEXIST — open_namei은 O_CREAT 여부와 무관하게 flag & O_EXCL을 검사한다"
         "(396-397). POSIX와 다른 0.11 동작.", K.ORANGE, 14)
    qbox(d, p, 16900, 9400, 15700, 4800, "Q4 · 정답",
         "Q. file_read에서 bmap이 0을 반환하면 어떻게 되는가?\n"
         "A. 디스크를 읽지 않고 그 구간을 0으로 채워 돌려준다(file_dev.c:28-29·39-42) — "
         "구멍(hole). file_write는 반대로 create_block으로 할당한다(65).", K.ORANGE, 14)
    d.banner(p, "네 문항 모두 오늘 코드에서 한 번 이상 직접 보았다 — 18·15·27·33장")

    # 44 정리와 다음 회차
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "13회차 — 터미널 I/O · 파트 E «파일·저장» 마무리 — 11(버퍼 캐시)·12(파일 시스템)로 저장 축 완결")
    d.cards(p, [
        ("오늘의 함수 체인",
         "namei → get_dir →\nfind_entry → iget →\nread_inode → bmap\n→ bread\n\n문자열이 블록 번호가\n되는 전 과정"),
        ("세 표와 수명",
         "filp[20] — 태스크별\nfile_table[64] — f_count\ninode_table[32] — i_count\n\n증가·감소 짝이 맞는다\n(08·20·40장)"),
        ("13회차 예고 — 터미널",
         "키보드에서 누른 글자가\nread()까지 전달되는가?\n\n오늘 sys_read의 S_ISCHR\n분기 rw_char로 들어간다\n— 파트 F «터미널»"),
    ], y=4400, h=8200)
    d.banner(p, '문자열 "/etc/rc" → inode → 블록 번호 — 11회차 bread가 받던 번호를 오늘 계산했다')


if __name__ == "__main__":
    K.run(globals())
