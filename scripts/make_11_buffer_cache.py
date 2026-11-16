#!/usr/bin/env python3
"""11회차 덱 — 버퍼 캐시와 블록 장치 (output/11-buffer-cache.pptx)

계획: materials/slide-plans/11-buffer-cache.md (§2 표 46행 1:1 · §3 앞부분 명세 ·
§4 다이어그램 명세 — 해시/free list·buffer_head 상태도·request 상태도 ·
§5 캡처 8종 · §6 이해 확인 · §8 오해 금지).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="11", total=46, slug="11-buffer-cache",
    part_no="E", part="«파일·저장»",
    title="11. 버퍼 캐시와 블록 장치",
    question="read()가 디스크에 실제로 접근하는 때는 언제인가?",
    done=10,
    today_line="프로세스 축이 끝나고 I/O 축이 시작된다 — read()는 버퍼 캐시를 지나, 필요할 때만 디스크로",
    next_lines=[
        "10 → 11   10: 프로세스가 죽어도 남는 것 — 열어둔 파일과 디스크 내용 → 11: 그 내용이 메모리로 오가는 길, 버퍼 캐시를 연다",
        "11 → 12   bread 의 block 을 누가 계산하는가 → 12회차 namei 가 계산한다 — namei 가 오늘 bread 를 부른다",
        "파트 E «파일·저장» — 11 버퍼 캐시·블록 장치 → 12 파일 시스템 · 12·13 회차가 «I/O 축»",
    ],
    road_note=("오늘은 10단계를 빠짐없이 밟는다(질문 → 정리).\n"
               "로드맵 축 전환: 06–10 «프로세스 축» → 11–13 «I/O 축» — 파트 E «파일·저장»의 첫 회차다."),
    STRUCT=dict(
        teal=["fs", "blk"],
        today=[("fs/buffer.c", "bread·getblk·brelse"),
               ("kernel/blk_drv/ll_rw_blk.c", "요청 큐"),
               ("kernel/blk_drv/hd.c", "하드디스크 드라이버")],
        flow="bread → getblk(히트/미스) → ll_rw_block → hd 인터럽트 → end_request → wake_up",
        up="↑ read() 반환",
        user="sh · 사용자 프로그램",
    ),
)

CHECKS = dict(
    captions={
        7: "src/init/main.c:126-137",
        8: "src/include/linux/fs.h:68-81",
        10: "src/fs/buffer.c:166-174",
        12: "src/fs/buffer.c:267-281",
        13: "src/fs/buffer.c:210-227",
        14: "src/fs/buffer.c:228-240",
        15: "src/fs/buffer.c:253-261",
        18: "src/fs/buffer.c:44-57",
        19: "src/fs/buffer.c:301-313",
        22: "src/kernel/blk_drv/blk.h:23-33",
        23: "src/kernel/blk_drv/ll_rw_blk.c:145-155",
        24: "src/kernel/blk_drv/ll_rw_blk.c:115-131",
        26: "src/kernel/blk_drv/ll_rw_blk.c:68-86",
        28: "src/kernel/blk_drv/hd.c:301-315",
        29: "src/kernel/blk_drv/hd.c:184-199",
        30: "src/kernel/system_call.s:221-234",
        31: "src/kernel/blk_drv/hd.c:250-267",
        32: "src/kernel/blk_drv/blk.h:109-125",
    },
    required=[
        "버퍼 캐시", "buffer_head", "b_uptodate", "b_dirt", "b_lock", "b_count",
        "bread", "getblk", "brelse", "BADNESS", "NR_HASH", "307", "hash_table",
        "free_list", "buffer_wait", "wait_on_buffer", "sleep_on", "wake_up",
        "ll_rw_block", "make_request", "add_request", "IN_ORDER", "NR_REQUEST",
        "wait_for_request", "do_hd_request", "hd_out", "read_intr", "write_intr",
        "end_request", "port_read", "nr_sectors", "MAJOR", "MINOR", "0x306",
        "sync_dev", "sys_sync", "READA", "WRITEA", "xchgl", "INIT_REQUEST",
        "MAX_ERRORS", "0x2E", "IRQ14", "buffer_init", "hd_init", "blk_dev",
    ],
    prereq=[
        ("버퍼 캐시", "src/fs/buffer.c:267-281"),
        ("sleep_on", "src/kernel/sched.c:151-165"),
        ("end_request", "src/kernel/blk_drv/hd.c:250-267"),
        ("wake_up", "src/kernel/blk_drv/blk.h:109-125"),
    ],
    structure_nodes=["buffer.c", "ll_rw_blk.c", "hd.c", "system_call.s",
                     "sched.c"],
    capture_slides=[21, 36, 38],
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


def capout(d, p, x, y, w, h, body, capture_name, size=12):
    """캡처 미확보 — 기대 출력 패널 + '실측 아님' + 캡처 파일명(두 줄 캡션)."""
    d.shape(p, x, y, w, h, 0x071A24)
    d.text(p, x + 350, y + 200, w - 700, 480, "예상 출력 — 실측 아님 · 캡처 예정",
           11, K.TEAL, True)
    d.text(p, x + 350, y + 660, w - 700, 420,
           f"materials/…/captures/{capture_name}", 9, K.MUTED, mono=True)
    lines = body.split("\n")
    avail = h - 1450
    s = size
    while s > 8 and len(lines) * s * 58 > avail:
        s -= 1
    d.text(p, x + 350, y + 1200, w - 700, avail, body, s, K.PAPER, mono=True)


def lab(d, p, x, y, w, text, size=12, color=K.TEAL, bold=True):
    d.text(p, x, y, w, 600, text, size, color, bold)


def populate(d):
    # ── 배경 05–11 ────────────────────────────────────────────
    # 05 디스크와 메모리의 속도 차이
    p = d.slide("디스크와 메모리의 속도 차이", K.S_BG,
                "1991년 IDE — 탐색 수 ms · 메모리 수십~수백 ns · 같은 블록을 다시 읽는 요청은 아주 흔하다")
    lab(d, p, 1100, 4150, 15000, "접근 지연 — 대략적인 크기 (실제 비율)", 14)
    d.shape(p, 6600, 4750, 23000, 950, K.ORANGE)
    d.text(p, 6800, 5000, 22000, 550, "하드디스크 탐색 — 약 10–20 ms (헤드 이동 + 회전 지연, 1991 IDE)",
           14, K.INK, True)
    d.text(p, 1100, 5050, 5300, 550, "하드디스크", 14, K.PAPER, True)
    d.shape(p, 6600, 6050, 480, 950, K.TEAL)
    d.text(p, 1100, 6350, 5300, 550, "메모리 (DRAM)", 14, K.PAPER, True)
    d.text(p, 7300, 6350, 22000, 550,
           "약 100 ns — 실제 비율(약 10만 배)로는 이 막대가 화면에 그려지지 않는다", 13, K.INK)
    d.cards(p, [
        ("느린 디스크",
         "탐색 + 회전 + 전송\n모두 ms 단위\n\nCPU·메모리는 ns 단위\n약 10만 배 차이"),
        ("같은 블록이 반복된다",
         "디렉터리 블록 · inode 블록\n비트맵 블록 —\n\nopen·read·write·lookup\n때마다 다시 읽힌다"),
        ("그래서 버퍼 캐시",
         "읽은 적 있으면 메모리에서\n준다 — fs/buffer.c\n\n디스크 접근은 필요할 때만\nll_rw_block 으로"),
    ], y=7600, h=6300)
    d.banner(p, "read()가 매번 디스크에 가는 것은 아니다 — 오늘 질문: 정확히 언제 가는가?")

    # 06 단위 정리: 섹터, 블록, 장치 번호
    p = d.slide("단위 정리: 섹터, 블록, 장치 번호", K.S_BG,
                "섹터 512B(하드웨어) · 블록 1024B(fs.h:49) · MAJOR/MINOR(fs.h:33-34) · ROOT_DEV 0x306(bootsect.s:43)")
    lab(d, p, 1100, 4150, 15000, "섹터 2개 = 블록 1개", 15)
    nbox(d, p, 1100, 4750, 5000, 1250, "섹터 512B", "하드웨어 단위", None, K.MUTED, s1=14, s2=11)
    nbox(d, p, 6300, 4750, 5000, 1250, "섹터 512B", None, None, K.MUTED, s1=14)
    arrow(d, p, 5650, 5000, "+", 22)
    d.text(p, 11300, 5050, 2000, 550, "= 합쳐서", 13, K.TEAL, True)
    nbox(d, p, 13200, 4750, 6800, 1250, "블록 1024B", "파일 시스템 단위 — fs.h:49",
         K.PAPER, s1=14, s2=11)
    para(d, p, 1100, 6300, 19700, 1500,
         "make_request 가 블록을 섹터로 바꾼다 — sector = b_blocknr<<1 · "
         "nr_sectors = 2 (ll_rw_blk.c:136-137)", 14)
    lab(d, p, 22000, 4150, 9500, "장치 번호 0x306 분해", 15)
    nbox(d, p, 22000, 4750, 9500, 1150, "ROOT_DEV = 0x306",
         "boot/bootsect.s:43", K.PAPER, s1=15, s2=11)
    arrow(d, p, 26500, 5950, "↓", 20)
    nbox(d, p, 22000, 6650, 4600, 1300, "MAJOR = 3",
         "hd.c:25 — 하드디스크", K.TEAL, s1=14, s2=11)
    nbox(d, p, 26900, 6650, 4600, 1300, "MINOR = 6",
         "6/5=드라이브 1(2번째)\n6%5=파티션 1", K.TEAL, s1=14, s2=10)
    para(d, p, 22000, 8200, 9500, 2000,
         "minor/5 = 드라이브 번호, minor%5 = 파티션 번호 (blk.h:83 DEVICE_NR) — "
         "드라이브마다 파티션 5칸(0=전체, 1–4)", 13)
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 136, 141, 1100, 8150, 15200, 4750,
                 size=11, caption_extra="sys_setup — 파티션 표")
    para(d, p, 1100, 13050, 15200, 1500,
         "버퍼 캐시는 부팅에도 이미 필요하다 — sys_setup(hd.c:71-160)이 "
         "bread(0x300+drive*5, 0)으로 파티션 표를 읽는다(135-153).", 13)
    d.banner(p, "블록 번호는 디스크 처음부터의 블록 순번 — 장치는 (major, minor) 한 쌍")

    # 07 메모리 지도에서 버퍼 영역
    p = d.slide("메모리 지도에서 버퍼 영역", K.S_CODE,
                "init/main.c:117-122 · buffer_init (buffer.c:348-381) · 3회차 메모리 지도 재사용 · (기존 기록) 부팅 캡처")
    d.code_panel(p, "src/init/main.c", 126, 137, 1100, 4400, 15200, 7300,
                 size=10, caption_extra="초기화 순서")
    para(d, p, 1100, 11900, 10400, 2600,
         "buffer_init(buffer_memory_end): 헤더는 커널 end 에서 위로(h++), 데이터 "
         "블록은 buffer_memory_end 에서 아래로(b -= 1024) 마주 보며 자란다.\n"
         "640K–1M 구멍은 372-373 (if (b==0x100000) b=0xA0000) — 건너뛴다. "
         "끝에서 free_list 원형 연결(376-378).", 13)
    d.picture(p, str(K.ROOT / "build" / "boot.png"), 11900, 12100, 9700, 2400)
    badge(d, p, 12000, 13700, 2800, "기존 기록", K.ORANGE, 700, 13)
    d.shape(p, 22300, 4600, 2600, 3000, 0x183340)
    d.text(p, 22450, 5000, 2300, 2000, "버퍼 데이터\n아래에서 위로", 12, K.PAPER, True)
    d.shape(p, 22300, 7700, 2600, 1000, K.INK)
    d.text(p, 22450, 7900, 2300, 700, "구멍 640K–1M\n건너뜀", 11, K.MUTED)
    d.shape(p, 22300, 8800, 2600, 2900, 0x183340)
    d.text(p, 22450, 9300, 2300, 2000, "커널 … end\n헤더가 위로", 12, K.PAPER, True)
    d.outline(p, 22300, 4600, 2600, 7100, K.TEAL, 80)
    d.text(p, 25200, 5150, 7000, 550, "buffer_memory_end (2M/4M)", 12, K.TEAL, True)
    d.text(p, 25200, 7900, 7000, 550, "0x100000 / 0xA0000", 12, K.MUTED)
    d.text(p, 25200, 10000, 7000, 550, "start_buffer = &end", 12, K.TEAL, True)
    d.text(p, 25200, 10800, 7000, 1100,
           "buffer_head 들이 연속으로 자라며\nNR_BUFFERS 로 결과 보고", 11, K.PAPER)

    # 08 struct buffer_head
    p = d.slide("struct buffer_head", K.S_CODE,
                "include/linux/fs.h:68-81 — 플래그 4개의 뜻은 다음 장(09), 링크 4개의 쓰임은 11장")
    d.code_panel(p, "src/include/linux/fs.h", 68, 81, 1100, 4400, 19700, 8950,
                 size=10)
    d.shape(p, 22100, 4500, 9500, 6700, K.PAPER)
    d.text(p, 22400, 4700, 8900, 600, "buffer_head 하나와 그 데이터 블록", 14,
           K.INK, True)
    rows = [
        ("b_data", "1024B 데이터 블록 포인터"),
        ("b_blocknr · b_dev", "이 버퍼의 정체 — (장치, 블록)"),
        ("b_uptodate·b_dirt·b_count·b_lock", "플래그 4개 (09장)"),
        ("b_wait", "잠들어 기다리는 태스크"),
        ("b_prev · b_next", "해시 체인 링크 (11장)"),
        ("b_prev_free · b_next_free", "free list 링크 (11장)"),
    ]
    for i, (f, m) in enumerate(rows):
        y = 5500 + i * 950
        d.text(p, 22400, y, 8900, 500, f, 13, K.TEAL if i < 4 else K.ORANGE, True)
        d.text(p, 22400, y + 430, 8900, 450, m, 11, K.INK)
    arrow(d, p, 26300, 11300, "↓ b_data", 16)
    nbox(d, p, 22100, 12200, 9500, 1500, "데이터 블록 1024B",
         "buffer_init 이 버퍼 영역에 배치 (07장)", K.TEAL, s1=14, s2=11)

    # 09 네 플래그의 뜻
    p = d.slide("네 플래그의 뜻", K.S_BG,
                "include/linux/fs.h:68-81 · 설계 원칙 buffer.c:7-13 — '플래그는 호출자가 바꾼다'")
    d.table(p, 1100, 4500, [4200, 7900, 9200, 10200], [
        ["플래그", "뜻", "1로 만드는 주체", "0으로 만드는 주체"],
        ["b_uptodate", "데이터가 디스크 내용과 같은가", "end_request — I/O 완료 (blk.h:113)",
         "getblk(245) · invalidate_buffers(95)"],
        ["b_dirt", "메모리가 디스크보다 새로운가", "버퍼를 고친 파일 시스템 코드 — 12회차",
         "add_request(71) · getblk(244) · invalidate(95)"],
        ["b_lock", "I/O 진행 중 — 손대면 안 되는가", "lock_buffer (ll_rw_blk.c:105)",
         "unlock_buffer — end_request (blk.h:114)"],
        ["b_count", "지금 쓰는 사람 수", "get_hash_table·getblk (190·243)", "brelse (258)"],
    ], row_h=1750, size=14)
    d.banner(p, "각각 '누가 1로, 누가 0으로' — 네 플래그가 함께 움직이는 완성형은 상태 변화도 ① (16장)",
            13600, 18)
    para(d, p, 1100, 14500, 31500, 900,
         "원칙(buffer.c:7-13): 인터럽트는 데이터만 바꾸고 플래그는 호출자가 바꾼다 — 17장에서 코드로 본다.",
         13, K.MUTED)

    # 10 두 개의 자료구조 — 코드
    p = d.slide("두 개의 자료구조: 해시 테이블과 free list — 코드", K.S_CODE,
                "buffer.c:128-129 · 131-174 — remove_from_queues / insert_into_queues / find_buffer")
    d.code_panel(p, "src/fs/buffer.c", 149, 164, 1100, 4400, 15200, 9100, size=9,
                 caption_extra="insert_into_queues — 꼬리+선두")
    d.code_panel(p, "src/fs/buffer.c", 166, 174, 16900, 4400, 15700, 6100,
                 size=10, caption_extra="find_buffer — 버킷 체인 순회")
    para(d, p, 16900, 10900, 15700, 3600,
         "_hashfn / hash 매크로(128-129) —\n"
         "hash(dev,block) = hash_table[(dev^block) % 307]\n"
         "NR_HASH = 307 버킷 (fs.h:47)\n\n"
         "해시 체인은 '찾기', free list는 '재사용 순서'다 — 삽입은 항상 꼬리(151-155). "
         "LRU와 비슷하지만 단정하지 않는다(§8).\n"
         "remove_from_queues(131-147)는 두 목록에서 모두 끊는다.", 14)
    d.banner(p, "같은 buffer_head 하나가 두 목록에 동시에 산다 — 그림은 다음 장(11)")

    # 11 해시/free list 구조도 (핵심 시각자료)
    p = d.slide("그림: 한 버퍼가 두 목록에 산다 — 해시 체인과 free list", K.S_BG,
                "buffer.c:128-174 · 205-227 — 실선 = 해시 체인(b_prev/b_next) · 회색 = free list(b_prev_free/b_next_free, 원형)")
    nbox(d, p, 1400, 4250, 4300, 1050, "hash_table[h2]",
         "(0x306^2)%307", None, K.MUTED, s1=13, s2=10)
    nbox(d, p, 9300, 4250, 4300, 1050, "hash_table[h1]",
         "(0x306^137)%307", None, K.MUTED, s1=13, s2=10)
    arrow(d, p, 3200, 5350, "↓", 18)
    arrow(d, p, 11100, 5350, "↓", 18)
    bhs = [
        ("bh1  (0x306, 2)", "(u,d,l,c)=(1,0,0,0)", K.PAPER, None),
        ("bh2  (0x306, 137)", "(1,0,0,1)  b_count>0", K.ORANGE, K.PAPER),
        ("bh4  (0x306, 341)", "(1,1,0,0)  dirty", K.PAPER, None),
        ("bh3  (0x306, 139)", "(0,0,0,0)  free", K.PAPER, None),
    ]
    for i, (t1, t2, fill, edge) in enumerate(bhs):
        x = 1100 + i * 7900
        nbox(d, p, x, 6100, 6900, 1900, t1, t2, fill, edge=edge, s1=14, s2=11)
    # 해시 체인(TEAL): h1 → bh2 → bh4 → ∅ / h2 → bh1 — 체인 화살표는 상자 위에
    d.text(p, 15500, 5800, 2000, 500, "b_next →", 12, K.TEAL, True)
    arrow(d, p, 24300, 6700, "→ ∅", 15, K.TEAL, 900, 700)
    # free list(회색, 원형): free_list → bh1 → bh3 → bh2 → bh4 → bh1
    d.text(p, 1100, 8350, 4000, 500, "free_list (원형)", 13, K.MUTED, True)
    arrow(d, p, 2200, 8850, "↓", 16, K.MUTED)
    badge(d, p, 9000, 8150, 6900, "getblk 가 건너뛴다 — b_count>0 (215)", K.ORANGE, 620, 11)
    d.text(p, 5600, 9100, 22000, 500,
           "free_list → bh1 → bh3 → bh2 → bh4 → (bh1 로 되돌아감 — 원형)", 13, K.MUTED)
    para(d, p, 1100, 9750, 31500, 2500,
         "① 같은 (dev, block) 버퍼는 버킷 하나의 이중 연결(b_prev/b_next)에 모인다 — 찾기용.\n"
         "② free list는 원형 — 재사용 후보 순서. 삽입은 항상 꼬리(insert_into_queues 151-155).\n"
         "③ bh2 는 두 목록에 동시에 연결되어 있다 — free list에 남아 있어도 b_count>0 이면 "
         "getblk 의 후보 순회에서 건너뛴다(215).", 15)
    d.banner(p, "버퍼 하나가 두 목록에 산다 — 해시(찾기)와 free list(재사용 순서)는 별개의 링크다")
    d.text(p, 29300, 16000, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 코드 12–19 (16은 상태도) ──────────────────────────────
    # 12 코드: bread
    p = d.slide("코드: bread", K.S_CODE,
                "buffer.c:267-281 — 핵심 질문에 대한 첫 답: b_uptodate 가 0일 때만 ll_rw_block")
    d.code(p, "src/fs/buffer.c", 267, 281,
           "① getblk(dev,block)\n   헤더 확보(13·14장)\n"
           "② b_uptodate==1\n   → 즉시 반환, 디스크 0번\n"
           "③ 아니면 ll_rw_block(READ,bh)\n"
           "④ wait_on_buffer — 잠듦\n   인터럽트가 깨워준다\n"
           "⑤ 다시 검사, 실패면\n   brelse 후 NULL",
           expl_size=15)
    nbox(d, p, 22100, 11400, 4600, 1500, "히트", "b_uptodate=1\n디스크 0번 · 즉시 반환",
         K.TEAL, s1=14, s2=11)
    arrow(d, p, 26800, 11850, "↔", 18, K.MUTED)
    nbox(d, p, 27400, 11400, 4600, 1500, "미스", "b_uptodate=0\nll_rw_block + 대기",
         K.ORANGE, s1=14, s2=11)

    # 13 코드: getblk 전반부
    p = d.slide("코드: getblk 전반부 (찾기와 고르기)", K.S_CODE,
                "buffer.c:205-227 · get_hash_table 183-196 — BADNESS 최소 선택, 하나도 없으면 잠듦")
    d.code_panel(p, "src/fs/buffer.c", 210, 227, 1100, 4400, 15200, 10100, size=9,
                 caption_extra="해시 확인 → free list 순회")
    d.code_panel(p, "src/fs/buffer.c", 183, 196, 16900, 4400, 15700, 7400,
                 size=8, caption_extra="b_count++ 후 재확인")
    para(d, p, 16900, 12000, 15700, 2500,
         "BADNESS(bh) = (b_dirt<<1) + b_lock (205)\n"
         "free list 를 한 바퀴 순회하며 b_count==0 중 최소 선택 — "
         "0이면 즉시 중단(219-220).\n"
         "후보가 하나도 없으면 sleep_on(&buffer_wait)(225) — brelse 가 깨운다(260).",
         13)
    d.banner(p, "BADNESS = b_dirt×2 + b_lock — '더러움'이 '잠김'보다 두 배 나쁘다 (buffer.c:205)")

    # 14 코드: getblk 후반부
    p = d.slide("코드: getblk 후반부 (확정)", K.S_CODE,
                "buffer.c:228-251 — 잠들 때마다 세상이 바뀐다: goto repeat 가 네 번 (226·230·235·240)")
    d.code_panel(p, "src/fs/buffer.c", 228, 240, 1100, 4400, 15200, 7600, size=9,
                 caption_extra="재검사 — wait·count·dirt")
    d.code_panel(p, "src/fs/buffer.c", 241, 251, 16900, 4400, 15700, 7200,
                 size=10, caption_extra="확정 — 플래그 초기화·이동")
    para(d, p, 1100, 12300, 15200, 2200,
         "goto repeat 4곳 — 226: 잠들고 옴(빈 버퍼 없었음) · 230: 깨어났더니 b_count>0 · "
         "235: b_dirt 처리 중 · 240: 자는 동안 같은 블록이 캐시에 들어옴.\n"
         "자는 동안 누가 같은 블록을 넣었는지 find_buffer 로 다시 확인(239).", 14)
    para(d, p, 16900, 11900, 15700, 2600,
         "확정(243-249): b_count=1 · b_dirt=0 · b_uptodate=0 →\n"
         "remove_from_queues → b_dev·b_blocknr 갱신 → insert_into_queues.\n"
         "여기서 b_uptodate=0 이 되므로 bread 는 ll_rw_block 을 부른다(12장).", 14)

    # 15 코드: brelse와 wait_on_buffer
    p = d.slide("코드: brelse와 wait_on_buffer", K.S_CODE,
                "buffer.c:253-261 · 36-42 · sleep_on sched.c:151-165 — 05회차 대기 큐 복습")
    d.code_panel(p, "src/fs/buffer.c", 36, 42, 1100, 4400, 15200, 4700, size=9,
                 caption_extra="cli / while(b_lock) / sti")
    d.code_panel(p, "src/fs/buffer.c", 253, 261, 1100, 9300, 15200, 5300, size=8,
                 caption_extra="brelse — 반납 후 깨우기")
    d.code_panel(p, "src/kernel/sched.c", 151, 165, 16900, 4400, 15700, 7800,
                 size=8, caption_extra="sleep_on — *p 체인")
    nbox(d, p, 16900, 12400, 4600, 1000, "task A (먼저 잠듦)", "tmp = A",
         None, K.MUTED, s1=12, s2=10)
    arrow(d, p, 21550, 12700, "←  *p", 14, K.TEAL, 1900, 600)
    nbox(d, p, 23500, 12400, 4600, 1000, "task B (나중에 잠듦)",
         "*p = B — 체인 머리", K.PAPER, s1=12, s2=10)
    arrow(d, p, 28100, 12700, "← wake_up", 14, K.ORANGE, 3200, 600)
    para(d, p, 16900, 13600, 15700, 900,
         "깨어난 B가 A를 깨운다(tmp->state=0) — 대기 큐가 체인으로 이어진다.", 13)

    # 16 상태 변화도 ①: buffer_head 플래그 (핵심)
    p = d.slide("상태 변화도 ①: buffer_head 플래그", K.S_STATE,
                "4-튜플 (b_uptodate, b_dirt, b_lock, b_count) — 값은 코드 추론, 캡처 관찰값만 '관찰' 표기(§8)")
    d.text(p, 1100, 4100, 18000, 450, "cached → uptodate 복귀 : getblk 적중 (get_hash_table 190)",
           11, K.TEAL, True)
    nodes_r1 = [
        ("free", "(0,0,0,0)\nb_dev=0", None, K.MUTED),
        ("claimed", "(0,0,0,1)", None, None),
        ("reading", "(0,0,1,1)", None, None),
        ("uptodate", "(1,0,0,1)", None, None),
        ("cached", "(1,0,0,0)", None, None),
    ]
    for i, (t1, t2, fill, edge) in enumerate(nodes_r1):
        x = 1100 + i * 6150
        nbox(d, p, x, 4550, 5600, 1650, t1, t2,
             fill, edge=edge or (K.TEAL if t1 != "free" else None), s1=16, s2=10)
    trans = [("getblk 243-245\nb_count=1", K.TEAL),
             ("make_request:105\nlock_buffer", K.TEAL),
             ("end_request 113-114\n(시연 B 관찰)", K.ORANGE),
             ("brelse 258\nb_count=0", K.TEAL)]
    for i, (t, c) in enumerate(trans):
        d.text(p, 6750 + i * 6150, 4900, 600, 600, "→", 22, c, True)
        d.text(p, 5750 + i * 6150, 6340, 2900, 1050, t, 10, c, True)
    d.text(p, 20100, 6520, 9000, 550, "↘ 쓰기 — b_dirt=1 (12회차)", 11, K.ORANGE, True)
    nodes_r2 = [
        ("written", "(1,0,0,n)  —  brelse → cached", 1100),
        ("writing", "(1,0,1,n)", 7250),
        ("dirty", "(1,1,0,n)", 13400),
    ]
    for t1, t2, x in nodes_r2:
        nbox(d, p, x, 7650, 5600, 1650, t1, t2, None, edge=K.TEAL, s1=16, s2=10)
    d.text(p, 13000, 8150, 600, 600, "←", 22, K.TEAL, True)
    d.text(p, 10200, 9460, 5600, 500, "add_request 70-71 — b_dirt=0 + lock", 10, K.TEAL, True)
    d.text(p, 6800, 8150, 600, 600, "←", 22, K.TEAL, True)
    d.text(p, 4100, 9460, 5600, 500, "end_request 113-114", 10, K.TEAL, True)
    d.table(p, 1100, 10700, [9200, 11900, 10400], [
        ["전환 (원인)", "변경 데이터 (플래그 비트)", "유지 조건"],
        ["getblk 할당 (free→claimed)", "b_count 0→1 · b_dirt=0 · b_uptodate=0 (243-245)",
         "b_count>0 이면 재사용 대상 아님 (215)"],
        ["lock_buffer (→reading/writing)", "b_lock 0→1 (ll_rw_blk.c:105 · add_request 71)",
         "b_lock=1 이면 플래그 변경 금지 — wait_on_buffer 대기"],
        ["end_request (→uptodate/written)", "b_uptodate=1 · b_lock=0 (blk.h:113-114)",
         "인터럽트 문맥 — 플래그를 바꾸는 유일한 곳(17장)"],
        ["brelse (→cached)", "b_count -1 (258)", "0 미만이면 panic (259)"],
    ], row_h=820, size=13)
    d.text(p, 29300, 14850, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # 17 동기화 원칙
    p = d.slide("동기화 원칙: 인터럽트는 데이터만", K.S_BG,
                "buffer.c:7-13 주석 · read_intr port_read(hd.c:250-267) · end_request(blk.h:109-125) · wait_on_buffer(36-42)")
    auto_pane(d, p, 1100, 4400, 16000, 5900, "fs/buffer.c:7-13 — 설계 원칙 주석 (원문)",
              "'buffer.c' implements the buffer-cache functions. Race-conditions have\n"
              "been avoided by NEVER letting a interrupt change a buffer (except for\n"
              "the data, of course), but instead letting the caller do it. NOTE! As\n"
              "interrupts can wake up a caller, some cli-sti sequences are needed to\n"
              "check for sleep-on-calls. These should be extremely quick, though\n"
              "(I hope).", start=13)
    para(d, p, 1100, 10600, 16000, 3800,
         "인터럽트 핸들러 read_intr 는 port_read 로 b_data 만 채운다(hd.c:257).\n"
         "플래그를 바꾸는 곳은 end_request (blk.h:113-114) 한 곳뿐 — 인터럽트 문맥이지만 "
         "블록 계층의 코드다.\n"
         "wait_on_buffer 의 cli/sti 가 필요한 이유 — 오른쪽 타임라인.", 15)
    d.text(p, 18000, 4400, 13500, 550, "검사와 sleep 사이의 경쟁 (cli 없다면)", 14,
           K.ORANGE, True)
    nbox(d, p, 18000, 5100, 13500, 1100, "① b_lock 검사 — 1이다", None, K.PAPER, s1=13)
    arrow(d, p, 24300, 6250, "↓", 18, K.MUTED)
    nbox(d, p, 18000, 6800, 13500, 1100, "② 인터럽트: unlock · wake_up — 깨울 태스크 없음",
         None, K.PAPER, s1=13)
    arrow(d, p, 24300, 7950, "↓", 18, K.MUTED)
    nbox(d, p, 18000, 8500, 13500, 1100, "③ sleep_on — 아무도 깨우지 못한다",
         None, K.ORANGE, s1=13)
    para(d, p, 18000, 9850, 13500, 4600,
         "wait_on_buffer(36-42)는 검사와 잠듦을 cli~sti 로 묶는다 — "
         "그 사이에 인터럽트가 들어와도 잠들기 전에 b_lock==0 을 보고 잠들지 않는다.\n\n"
         "05회차 복습: sleep_on 의 *p 체인과 wake_up — 15장 그림.", 15)

    # 18 sync
    p = d.slide("sync: 더러운 버퍼는 언제 디스크로 가는가", K.S_CODE,
                "buffer.c:44-57 sys_sync · 59-82 sync_dev — 0.11에는 주기적 flush 데몬이 없다(명시)")
    d.code_panel(p, "src/fs/buffer.c", 44, 57, 1100, 4400, 15200, 8900, size=10,
                 caption_extra="sys_sync — inode 먼저")
    d.code_panel(p, "src/fs/buffer.c", 64, 71, 16900, 4400, 15700, 5550,
                 size=10, caption_extra="sync_dev — 두 번 순회(64-80)")
    d.shape(p, 16900, 10300, 15700, 4200, K.INK)
    d.text(p, 17200, 10500, 15100, 550, "호출처 — dirty 가 디스크로 가는 길", 14,
           K.TEAL, True)
    d.text(p, 17200, 11200, 15100, 3100,
           "· getblk:231-232 — 더러운 버퍼를 재사용하기 전\n"
           "· iput — 12회차 · sys_umount\n"
           "· 사용자 sync 명령 → sys_sync\n"
           "그 외에는 없다 — 주기적 writeback 이 0.11에는 없다(§8)", 13, K.PAPER)
    para(d, p, 1100, 13600, 15200, 900,
         "sync_dev 가 두 번 순회하는 이유 — 첫 회가 inode 를 버퍼로 쓸 수 있어서(72 sync_inodes 후 재순회).",
         13, K.MUTED)

    # 19 bread_page와 breada
    p = d.slide("bread_page와 breada (참조)", K.S_CODE,
                "buffer.c:296-315 · 322-346 — 9회차 do_no_page 가 bread_page 를 호출(mm/memory.c:386)")
    d.code_panel(p, "src/fs/buffer.c", 301, 313, 1100, 4400, 15200, 7600, size=9,
                 caption_extra="bread_page — 4블록 동시 요청")
    para(d, p, 1100, 12300, 15200, 2200,
         "4블록 = 페이지 1개 — getblk 4번, 읽을 것만 ll_rw_block(READ) 한 다음 "
         "wait_on_buffer 로 모두 기다린 뒤 COPYBLK 로 페이지에 복사.\n"
         "READA 는 슬롯이 없으면 조용히 포기한다(make_request:125-128).", 14)
    d.code_panel(p, "src/fs/buffer.c", 328, 341, 16900, 4400, 15700, 8100, size=9,
                 caption_extra="breada — 336 행 주목")
    badge(d, p, 16900, 12700, 15700,
          "ll_rw_block(READA,bh) — tmp 를 의도한 것으로 보인다(§8)", K.ORANGE, 700, 13)
    para(d, p, 1100, 13800, 31500, 800,
         "336행은 원본 그대로이며 lab 에서도 수정하지 않았다 — '버그'라 단정하지 않고 'tmp를 의도한 것으로 보인다'로 읽는다.",
         13, K.MUTED)

    # ── 시연 A 20–21 ──────────────────────────────────────────
    # 20 시연 A 계획
    p = d.slide("시연 A 계획: 같은 블록 두 번 읽기", K.S_DEMO,
                "부팅 직후(캐시 거의 비어 있음)에서 시작 — lab/ 빌드 · QEMU i386 · GDB · 원본 미수정")
    auto_pane(d, p, 1100, 4400, 19700, 10100, "GDB — 중단점과 관찰 순서",
              "# ① 중단점\n"
              "(gdb) b bread\n"
              "(gdb) b ll_rw_block\n"
              "(gdb) c\n"
              "# ② 게스트: cat /etc/rc        ← 첫 실행\n"
              "(gdb) p dev ; p block\n"
              "(gdb) n      # buffer.c:273 까지 전진\n"
              "(gdb) p bh->b_uptodate\n"
              "#     기대 $ = 0 '\\000' → 이어 ll_rw_block 중단\n"
              "# ③ 게스트: cat /etc/rc        ← 두 번째 실행\n"
              "(gdb) p bh->b_uptodate\n"
              "#     기대 $ = 1 '\\001' → ll_rw_block 는 미진입\n"
              "(gdb) p bh->b_count\n"
              "# ④ 증빙\n"
              "(gdb) info breakpoints        # hit count 비교", start=12)
    para(d, p, 22000, 4400, 10000, 10100,
         "관찰 대상\n\n"
         "· 첫 bread — b_uptodate=0,\n  ll_rw_block 진입(디스크)\n"
         "· 두 번째 bread — b_uptodate=1,\n  ll_rw_block 미진입(캐시)\n"
         "· b_count 값 — 1\n\n"
         "주의\n"
         "· cat 이 inode·디렉터리 블록도\n  읽어 bread hit 는 여러 번\n"
         "· 부팅 직후 시작 — 캐시가 거의\n  비어 있어야 첫 미스가 잡힌다\n\n"
         "캡처 01·02·03 → 다음 장(21)", 14)

    # 21 시연 A 캡처
    p = d.slide("시연 A 캡처", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · 부팅 직후 상태(캐시 비어 있음)에서 시작 · cat 이 inode·디렉터리 블록도 읽어 bread hit는 여러 번")
    capout(d, p, 1100, 4150, 10000, 10300,
           "(gdb) c\n"
           "Breakpoint 1, bread (dev=0x306, block=137)\n"
           "    at fs/buffer.c:267\n"
           "(gdb) p bh->b_uptodate\n"
           "$1 = 0 '\\000'\n"
           "(gdb) c\n"
           "Breakpoint 2, ll_rw_block (rw=0,\n"
           "    bh=0x...) at ll_rw_blk.c:145\n"
           "# 디스크 명령 발행 — bread 275",
           "01-bread-first-uptodate0.png")
    capout(d, p, 11500, 4150, 10000, 10300,
           "(gdb) c\n"
           "Breakpoint 1, bread (dev=0x306, block=137)\n"
           "    at fs/buffer.c:267\n"
           "(gdb) p bh->b_uptodate\n"
           "$2 = 1 '\\001'\n"
           "(gdb) p bh->b_count\n"
           "$3 = 1\n"
           "# ll_rw_block 중단점은 도달하지 않음\n"
           "# — 캐시 적중, 디스크 0번",
           "02-bread-second-uptodate1.png")
    capout(d, p, 21900, 4150, 10500, 10300,
           "(gdb) info breakpoints\n"
           "Num Type       Enb What\n"
           "1   breakpoint y   bread\n"
           "    breakpoint hit: 12 times\n"
           "2   breakpoint y   ll_rw_block\n"
           "    breakpoint hit: 5 times\n"
           "# 두 번째 cat 뒤에도\n"
           "# bread hit만 늘고\n"
           "# ll_rw_block는 그대로",
           "03-info-breakpoints-hitcount.png")
    para(d, p, 1100, 14650, 31500, 800,
         "왼쪽=첫 실행(미스) · 가운데=두 번째(적중) · 오른쪽=hit count 증빙 — 수치는 예시(실측 아님).",
         12, K.MUTED)

    # ── 요청 큐 22–33 (25·27 비교, 33 상태도) ─────────────────
    # 22 블록 계층의 자료구조
    p = d.slide("블록 계층의 자료구조", K.S_CODE,
                "blk.h:15·23-33·40-48 · ll_rw_blk.c:21-40 · hd.c:343-349 — hd_init 이 request_fn 을 등록")
    d.code_panel(p, "src/kernel/blk_drv/blk.h", 23, 33, 1100, 4400, 15200, 7200,
                 size=10, caption_extra="빈 슬롯 표식")
    nbox(d, p, 1100, 11900, 2400, 1000, "blk_dev[3]", "major 3", K.TEAL,
         s1=13, s2=11)
    arrow(d, p, 3600, 12150, "→", 16, K.ORANGE, 700, 600)
    d.text(p, 3450, 12800, 4000, 450, "current_request", 11, K.ORANGE, True)
    for i, (t, f) in enumerate([("req A", K.PAPER), ("req B", K.PAPER), ("req C", None)]):
        nbox(d, p, 5200 + i * 3900, 11900, 3300, 1000, t,
             "dev=-1" if t == "req C" else None, f,
             edge=None if f else K.MUTED, s1=13, s2=10)
        if i < 2:
            arrow(d, p, 8570 + i * 3900, 12150, "→", 14, K.TEAL, 600, 500)
    d.text(p, 5200, 13100, 11000, 500, "request_fn = do_hd_request — hd_init(hd.c:345)이 등록",
           11, K.TEAL, True)
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 32, 40, 16900, 4400, 15700,
                 5600, size=9,
                 caption_extra="blk_dev[7] 초기값")
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 343, 349, 16900, 10300, 15700,
                 4300, size=10, caption_extra="hd_init — IDT 0x2E")
    para(d, p, 1100, 13800, 31500, 800,
         "blk_dev_init(ll_rw_blk.c:157-165)이 모든 request[i].dev = -1 로 초기화 — 32개(NR_REQUEST, blk.h:15).",
         13, K.MUTED)

    # 23 코드: ll_rw_block과 make_request 전반부
    p = d.slide("코드: ll_rw_block과 make_request 전반부", K.S_CODE,
                "ll_rw_blk.c:145-155 · 88-109 · lock_buffer 42-49 — 디스크에 '안 가는' 두 번째 지점")
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 145, 155, 1100, 4400,
                 15200, 7200, size=10)
    para(d, p, 1100, 11900, 15200, 2600,
         "lock_buffer(42-49): cli → while (b_lock) sleep_on(&b_wait) → b_lock=1 → sti.\n"
         "READA/WRITEA 는 버퍼가 이미 잠겨 있으면 그냥 포기한다(96-97) — 미리읽기는 "
         "선택이므로.\n잘못된 major 면 printk 후 반환(149-153).", 14)
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 95, 109, 16900, 4400,
                 15700, 8600, size=9,
                 caption_extra="조기 리턴 106-108")
    badge(d, p, 16900, 13200, 15700,
          "rw==READ && b_uptodate → unlock 후 return (106-108) — 디스크에 안 가는 둘째 관문",
          K.ORANGE, 700, 13)

    # 24 코드: make_request 후반부 (슬롯 찾기)
    p = d.slide("코드: make_request 후반부 (슬롯 찾기)", K.S_CODE,
                "ll_rw_blk.c:110-143 · NR_REQUEST 32(blk.h:15) — READ 32칸 전체, WRITE 앞 21칸만")
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 115, 131, 1100, 4400,
                 15200, 9600, size=9, caption_extra="슬롯 탐색 — 역순(--req)")
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 133, 142, 16900, 4400,
                 15700, 6650, size=10, caption_extra="슬롯 채움")
    d.text(p, 16900, 11300, 15700, 500, "request[32] 탐색 범위", 13, K.TEAL, True)
    for i in range(21):
        d.shape(p, 16900 + i * 500, 11900, 460, 800, K.TEAL)
    for i in range(11):
        d.outline(p, 27400 + i * 500, 11900, 460, 800, K.MUTED, 50)
    d.text(p, 16900, 12800, 10000, 500, "request[0..20] — WRITE 도 탐색(21칸)", 12, K.INK)
    d.text(p, 27400, 12800, 5400, 500, "[21..31] READ 전용", 12, K.MUTED)
    d.text(p, 16900, 13500, 15700, 500, "READ: 31 → 0 역순(32칸 전체) · WRITE: 20 → 0 역순(21칸)",
           12, K.ORANGE, True)
    para(d, p, 1100, 14200, 31500, 700,
         "슬롯이 비어 있지 않으면 — READA/WRITEA 는 포기, 아니면 sleep_on(&wait_for_request) 후 재시도(124-131).",
         13, K.MUTED)

    # 25 비교 ①: ll_rw_block의 rw 값
    p = d.slide("비교 ①: ll_rw_block의 rw 값 (범위: 4종 전부)", K.S_CMP,
                "fs.h:26-29 · ll_rw_blk.c:88-143 — 잠긴 버퍼·슬롯 부족·탐색 범위·호출처를 전부 비교")
    d.table(p, 1100, 4400, [4400, 6800, 8000, 4900, 7400], [
        ["rw (fs.h:26-29)", "잠긴 버퍼", "슬롯 없을 때", "슬롯 범위", "호출처"],
        ["READ = 0", "대기 — lock_buffer(45-46)", "sleep_on(&wait_for_request) 후 재시도 (129-130)",
         "32칸 전체 (115-116)", "bread · bread_page · breada"],
        ["WRITE = 1", "대기 — 같음", "sleep_on 후 재시도",
         "앞 21칸 (117-118)", "sys_sync · sync_dev"],
        ["READA = 2", "포기 — return (96-97)", "포기 — unlock 후 return (125-127)",
         "32칸", "breada(336)"],
        ["WRITEA = 3", "포기 — 같음", "포기 — 같음", "21칸", "0.11에 없음"],
    ], row_h=1650, size=13)
    d.banner(p, "WRITEA 는 0.11 어디서도 부르지 않는다 — fs.h:29 주석 \"silly, but somewhat useful\"", 13200, 17)
    para(d, p, 1100, 14100, 31500, 1300,
         "슬롯 범위 차이의 의도(주석 111-114) — 쓰기가 큐를 채우면 읽기가 막힌다. 마지막 1/3은 읽기 전용으로 비워둔다.",
         14)

    # 26 코드: add_request
    p = d.slide("코드: add_request", K.S_CODE,
                "ll_rw_blk.c:64-86 · IN_ORDER blk.h:40-43 — 큐에 들어가는 순간 '더러움'을 넘긴다")
    d.code_panel(p, "src/kernel/blk_drv/ll_rw_blk.c", 68, 86, 1100, 4400, 15200,
                 9600, size=8)
    badge(d, p, 16900, 4400, 15700, "req->bh->b_dirt = 0 — 71행", K.ORANGE, 800, 15)
    pane(d, p, 16900, 5500, 15700, 2900, "IN_ORDER — blk.h:40-43",
         "((s1)->cmd<(s2)->cmd || (s1)->cmd==(s2)->cmd &&\n"
         "((s1)->dev < (s2)->dev || ((s1)->dev == (s2)->dev &&\n"
         "(s1)->sector < (s2)->sector)))", 11)
    para(d, p, 16900, 8700, 15700, 5300,
         "키 순서 — cmd → dev → sector.\n"
         "READ(0) < WRITE(1): 읽기가 항상 앞에 온다.\n\n"
         "req->bh->b_dirt = 0 (71) — 큐에 들어간 순간 '더러움'을 요청이 가져간다. "
         "이후 같은 버퍼에 또 쓰면 새 b_dirt=1 이 쌓인다.\n\n"
         "큐가 비어 있으면 current_request=req; sti; request_fn() — 하드디스크면 "
         "do_hd_request 가 즉시 명령을 내린다. 아니면 IN_ORDER 자리까지 전진해 삽입(78-84) — "
         "비교 ②(27장).", 14)
    d.banner(p, "add_request 는 cli~sti 안에서 큐를 고친다(69·85) — 인터럽트와의 경쟁을 막는다")

    # 27 비교 ②: 큐 삽입 정책
    p = d.slide("비교 ②: 큐 삽입 정책 (범위: 삽입 위치 3가지)", K.S_CMP,
                "ll_rw_blk.c:64-86 · IN_ORDER blk.h:40-43 — 단방향 엘리베이터: 한 방향으로 오르다 꺾이는 지점까지만")
    cards = [
        ("(a) 빈 큐 — 즉시 실행 (72-77)",
         "current_request == NULL 이면\nreq 하나로 즉시 request_fn().", [("req(신규)", K.ORANGE)]),
        ("(b) IN_ORDER 중간 삽입 (78-82)",
         "(IN_ORDER(tmp,req) ||\n!IN_ORDER(tmp,tmp->next)) &&\nIN_ORDER(req,tmp->next)\n— 오르다 꺾이는 지점",
         [("CURRENT", None), ("A", K.PAPER), ("req", K.ORANGE), ("B", K.PAPER)]),
        ("(c) 꼬리 (for 종료, 83-84)",
         "조건이 끝내 안 맞으면 맨 뒤에.\n탐색은 tmp->next 가 있는 동안만.",
         [("CURRENT", None), ("A", K.PAPER), ("B", K.PAPER), ("req", K.ORANGE)]),
    ]
    for i, (title, body, boxes) in enumerate(cards):
        x = 1100 + i * 10800
        d.shape(p, x, 4400, 9900, 4700, K.PAPER)
        d.shape(p, x, 4400, 9900, 150, K.ORANGE if i % 2 else K.TEAL)
        d.text(p, x + 400, 4650, 9200, 700, title, 14, K.INK, True)
        d.text(p, x + 400, 5450, 9200, 1300, body, 12, K.INK)
        bx = x + 350
        for j, (t, f) in enumerate(boxes):
            w = 1850 if len(boxes) > 2 else 3200
            nbox(d, p, bx, 7000, w, 1000, t, None, f,
                 edge=K.MUTED if f is None else None, s1=10)
            if j < len(boxes) - 1:
                d.text(p, bx + w + 90, 7220, 350, 500, "→", 12, K.TEAL, True)
            bx += w + 530
        if i == 0:
            d.text(p, x + 400, 8250, 9200, 600, "→ sti; request_fn() 즉시", 12,
                   K.ORANGE, True)
    d.outline(p, 1100, 9300, 31500, 1200, K.ORANGE, 90)
    d.text(p, 1400, 9520, 30900, 800,
           "불가능 — CURRENT(실행 중인 요청) 앞에는 절대 삽입하지 않는다: 탐색 루프가 tmp->next 를 보며 전진하기만 한다(78)",
           14, K.ORANGE, True)
    d.code_panel(p, "src/kernel/blk_drv/blk.h", 40, 43, 1100, 10800, 15200, 3400,
                 size=11)
    para(d, p, 16900, 10800, 15700, 3600,
         "엘리베이터(elevator) 정렬 — 섹터 번호 순서로 끼워 넣어 헤드 이동을 줄인다.\n"
         "'항상 섹터 순 정렬'은 아니다(§8) — CURRENT 앞은 불가능하고 꺾이는 지점까지만 허용한다.\n"
         "READ 가 WRITE 보다 앞에 온다 — cmd 비교가 첫 키.", 14)

    # 28 코드: do_hd_request
    p = d.slide("코드: do_hd_request", K.S_CODE,
                "hd.c:294-341 · INIT_REQUEST blk.h:127-136 — READ 는 hd_out 만 하고 리턴: CPU는 다른 일을 하러 간다")
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 301, 315, 1100, 4400, 15200, 8600,
                 size=9, caption_extra="(1) INIT_REQUEST · divl×2")
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 328, 340, 16900, 4400, 15700, 7600,
                 size=9, caption_extra="(2) READ는 리턴")
    para(d, p, 16900, 12200, 15700, 2400,
         "INIT_REQUEST(blk.h:127-136) — 큐 비면 return, b_lock 검사.\n"
         "block += hd[dev].start_sect(308) — 파티션 시작 보정.\n"
         "reset·recalibrate 처리(316-327) — 오류 후 재보정.", 13)
    badge(d, p, 1100, 13300, 15200,
          "READ(hd.c:338): hd_out(…, WIN_READ, &read_intr) 그리고 리턴 — 데이터는 인터럽트가 가져온다",
          K.ORANGE, 700, 13)
    para(d, p, 1100, 14200, 31500, 700,
         "divl 두 번(310-313): block/sect → (cyl·head 나머지), 다시 /head → cyl — sec/head/cyl 세 좌표.",
         12, K.MUTED)

    # 29 코드: hd_out
    p = d.slide("코드: hd_out", K.S_CODE,
                "hd.c:180-200 · port_read/port_write hd.c:61-65 — 하드웨어와 소프트웨어의 접점")
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 184, 199, 1100, 4400, 15200, 9100,
                 size=9, caption_extra="do_hd 지정 · 포트 7개")
    d.table(p, 16900, 4400, [4400, 11300], [
        ["포트 순서", "내용"],
        ["HD_CMD (0x3F6)", "hd_info[drive].ctl — 제어 레지스터"],
        ["+1", "wpcom>>2 — 쓰기 보상"],
        ["+2", "nsect — 섹터 수(2)"],
        ["+3", "sect — 섹터 번호"],
        ["+4", "cyl 하위 8비트"],
        ["+5", "cyl 상위 8비트"],
        ["+6", "0xA0 | drive<<4 | head"],
        ["+7 (HD_DATA)", "cmd — WIN_READ/WIN_WRITE 발사"],
    ], row_h=900, size=12)
    para(d, p, 16900, 13000, 15700, 1600,
         "명령 한 번에 이번 완료 인터럽트의 핸들러 주소를 지정한다 — do_hd = intr_addr(190).\n"
         "port_read/port_write(61-65) — PIO(insw/outsw), CPU가 워드 단위로 직접 옮긴다.",
         14)

    # 30 코드: hd_interrupt
    p = d.slide("코드: hd_interrupt", K.S_CODE,
                "system_call.s:221-250 · hd_init hd.c:343-349 — IDT 0x2E = IRQ14 · 04회차 진입 절차(저장→EOI) 재사용")
    d.code_panel(p, "src/kernel/system_call.s", 221, 234, 1100, 4400, 15200, 8900,
                 size=10, caption_extra="저장 · EOI")
    d.code_panel(p, "src/kernel/system_call.s", 237, 250, 16900, 4400, 15700, 8900,
                 size=10, caption_extra="xchgl — 회수 · call")
    para(d, p, 1100, 13600, 31500, 1000,
         "xchgl _do_hd,%edx — 꺼내면서 NULL 로 바꾼다(원자적 회수). 비어 있으면 unexpected_hd_interrupt(241).\n"
         "set_intr_gate(0x2E, &hd_interrupt)(hd.c:346) — IRQ14, PIC 마스크 해제(347-348).",
         14)
    d.banner(p, "명령마다 핸들러를 do_hd 로 지정하고, 인터럽트가 xchgl 로 회수한다 — hd_out(190)과 짝", 15000, 17)

    # 31 코드: read_intr
    p = d.slide("코드: read_intr", K.S_CODE,
                "hd.c:250-267 · bad_rw_intr 242-248 — 256워드 = 512B = 섹터 1개, PIO(insw)로 직접 반입")
    d.code_panel(p, "src/kernel/blk_drv/hd.c", 250, 267, 1100, 4400, 15200, 10100,
                 size=9, caption_extra="오류·port_read·재무장·완료")
    lab(d, p, 16900, 4400, 15700, "섹터 2회 인터럽트 타임라인", 14)
    nbox(d, p, 16900, 5000, 15700, 2600, "IRQ14 — 1번째",
         "port_read(HD_DATA, CURRENT->buffer, 256) — 512B\n"
         "buffer += 512 · sector++ · nr_sectors 2→1\ndo_hd = &read_intr 재무장 후 리턴(261-263)",
         K.PAPER, s1=13, s2=11)
    arrow(d, p, 24300, 7650, "↓", 20, K.ORANGE)
    nbox(d, p, 16900, 8300, 15700, 2600, "IRQ14 — 2번째",
         "port_read 512B · nr_sectors 1→0\nend_request(1) — b_uptodate=1 · 깨우기(265)\n"
         "do_hd_request() — 다음 요청 시작(266)",
         K.ORANGE, edge=K.PAPER, s1=13, s2=11)
    badge(d, p, 16900, 11150, 15700, "nr_sectors 2 → 1 → 0 — 캡처 05(B-2)의 관찰 대상",
          K.TEAL, 700, 13)
    para(d, p, 16900, 12100, 15700, 2400,
         "win_result() 오류면 bad_rw_intr(252-255) — 오류 누적이 MAX_ERRORS 7(hd.c:34)을 넘으면 "
         "end_request(0).\n인터럽트 문맥에서는 잠들 수 없다 — hd.c 상단 주석(7-14).", 13)

    # 32 코드: end_request
    p = d.slide("코드: end_request", K.S_CODE,
                "blk.h:109-125 · unlock_buffer ll_rw_blk.c:51-57 — '플래그는 end_request 한 곳'(17장)의 코드 근거")
    d.code_panel(p, "src/kernel/blk_drv/blk.h", 109, 125, 1100, 4400, 15200, 9600,
                 size=9, caption_extra="플래그·깨우기·반납")
    nbox(d, p, 19000, 4600, 6600, 1100, "end_request(uptodate)",
         "blk.h:109 — 인터럽트 문맥", K.PAPER, s1=14, s2=10)
    for i, (t, m) in enumerate([
            ("wake_up(&b_wait)", "버퍼 기다림 — wait_on_buffer 로 잠든 bread"),
            ("wake_up(&waiting)", "요청 기다림 — 페이징용(0.11 미사용 시 NULL)"),
            ("wake_up(&wait_for_request)", "슬롯 기다림 — make_request 에서 잠든 호출자")]):
        y = 6200 + i * 1900
        arrow(d, p, 18700, y + 150, "→", 18, K.ORANGE if i != 1 else K.MUTED)
        nbox(d, p, 20100, y, 11400, 1700, t, m, None, edge=K.TEAL, s1=13, s2=11)
    badge(d, p, 20100, 12000, 5400, "dev = -1 (123)", K.TEAL, 620, 13)
    badge(d, p, 25900, 12000, 5600, "CURRENT = next (124)", K.TEAL, 620, 13)
    para(d, p, 20100, 13000, 11400, 1500,
         "unlock_buffer(113-114) — b_lock=0 후 wake_up(&b_wait).\n"
         "extern inline — 심볼 중단점이 안 걸릴 수 있다. 시연 B는 hd.c:265 줄 중단점(§8).",
         13)

    # 33 상태 변화도 ②: request 한 개의 일생 (핵심)
    p = d.slide("상태 변화도 ②: request 한 개의 일생", K.S_STATE,
                "buffer_head 상태도(16장)와는 섞지 않는다 — 혼합 금지 원칙 · 노드 ⑥과 캡처 05(B-2)의 nr_sectors 2→1→0 이 대응")
    r2 = [
        ("① 빈 슬롯", "dev = -1\nblk_dev_init (ll_rw_blk.c:162)", None, K.MUTED),
        ("② 채워짐", "dev·sector·nr_sectors·buffer·bh\nmake_request:133-141", None, K.TEAL),
        ("③ 큐 삽입 / 즉시 실행", "add_request — 빈 큐면 request_fn 즉시(72-77)",
         None, K.TEAL),
    ]
    for i, (t1, t2, f, e) in enumerate(r2):
        x = 1100 + i * 10400
        nbox(d, p, x, 4600, 9600, 2000, t1, t2, f, edge=e, s1=15, s2=10)
        if i < 2:
            arrow(d, p, x + 9700, 5200, "→", 20)
    r2b = [
        ("⑥ 완료", "end_request — dev=-1 · CURRENT=next\n다음 요청으로 출발", None, K.MUTED),
        ("⑤ 섹터 인터럽트", "read_intr — nr_sectors 2→1→0\nbuffer += 512 · do_hd 재무장(262)",
         K.ORANGE, K.PAPER),
        ("④ CURRENT", "do_hd_request — hd_out 으로\n컨트롤러에 명령 발행", None, K.TEAL),
    ]
    for i, (t1, t2, f, e) in enumerate(r2b):
        x = 1100 + i * 10400
        nbox(d, p, x, 8300, 9600, 2000, t1, t2, f, edge=e, s1=15, s2=10)
    # ④→⑤→⑥ 왼쪽 방향 화살표 (row2) + ③→④ 세로 연결
    d.text(p, 21150, 8900, 600, 600, "←", 20, K.ORANGE, True)
    d.text(p, 10750, 8900, 600, 600, "←", 20, K.TEAL, True)
    arrow(d, p, 26000, 6700, "↓", 20, K.TEAL)
    d.text(p, 27400, 6800, 6000, 500, "③→④ 큐 머리가 되면", 12, K.TEAL, True)
    para(d, p, 1100, 10800, 15000, 1500,
         "전환마다 원인 함수와 변경 필드: ② make_request(채움) · ③ add_request(연결·b_dirt=0) · "
         "④ hd_out(명령) · ⑤ read_intr(데이터·nr_sectors) · ⑥ end_request(반납·깨우기).", 14)
    d.table(p, 16900, 11100, [8300, 7400], [
        ["노드", "캡처 대응 (§5)"],
        ["④ CURRENT", "04-do-hd-request — p *CURRENT"],
        ["⑤ 섹터 인터럽트", "05-read-intr — nr_sectors 2→1→0"],
        ["⑥ 완료", "06-end-request — b_uptodate 0→1"],
    ], row_h=760, size=12)
    d.text(p, 29300, 14450, 3300, 450, "Linux 0.11", 9, K.MUTED)

    # ── 순서도·시연 B/C 34–38 ─────────────────────────────────
    # 34 호출 순서도
    p = d.slide("호출 순서도: bread 한 번의 전체 경로", K.S_BG,
                "상태 변화도(16·33장)가 아닌 순서도 — 왼쪽 프로세스 문맥 · 오른쪽 인터럽트 문맥(IRQ 14, 2회)")
    lab(d, p, 1100, 4150, 15200, "프로세스 문맥 (bread 호출자)", 15, K.TEAL)
    L = [
        ("bread (buffer.c:267)", "read() 요청의 실제 출발점"),
        ("getblk (205-251)", "해시 적중? 아니면 free list — 13·14장"),
        ("ll_rw_block (ll_rw_blk.c:145)", "b_uptodate=0 일 때만"),
        ("make_request (88)", "lock_buffer — b_lock=1 (105)"),
        ("add_request (64)", "IN_ORDER 삽입 — b_dirt=0 (71)"),
        ("do_hd_request (hd.c:294)", "hd_out — 포트에 명령 (338)"),
        ("리턴 → wait_on_buffer → sleep_on → schedule", "잠듦 — 05회차 복습"),
    ]
    for i, (t1, t2) in enumerate(L):
        y = 4700 + i * 1330
        nbox(d, p, 1100, y, 15200, 1200, t1, t2, K.PAPER, s1=13, s2=10)
        if i < len(L) - 1:
            arrow(d, p, 8300, y + 1180, "↓", 13, K.TEAL, 600, 450)
    lab(d, p, 17800, 4150, 13700, "인터럽트 문맥 (IRQ 14 — 섹터마다)", 15, K.ORANGE)
    R = [
        ("① hd_interrupt (system_call.s:221)", "xchgl _do_hd — read_intr 회수"),
        ("read_intr 1번째 (hd.c:250)", "port_read 512B · nr_sectors 2→1 · 재무장"),
        ("② hd_interrupt → read_intr 2번째", "port_read 512B · nr_sectors 1→0"),
        ("end_request(1) (blk.h:109)", "b_uptodate=1 · b_lock=0 · wake_up"),
    ]
    for i, (t1, t2) in enumerate(R):
        y = 4700 + i * 1600
        nbox(d, p, 17800, y, 13700, 1450, t1, t2, None, edge=K.ORANGE, s1=13, s2=10)
        if i < len(R) - 1:
            arrow(d, p, 24000, y + 1450, "↓", 14, K.ORANGE, 600, 500)
    arrow(d, p, 16400, 11750, "잠듦 …", 13, K.MUTED, 2400, 500)
    nbox(d, p, 17800, 11200, 13700, 1500, "깨어남 → b_uptodate 확인 → bread 반환",
         "wake_up 이 state=0으로 — 실행은 다음 schedule(42장)", K.TEAL, s1=13, s2=10)
    d.text(p, 16400, 5500, 1300, 2600, "명령 후\n리턴 ▶", 12, K.ORANGE, True)
    para(d, p, 1100, 14100, 31500, 800,
         "지점 주석 — make_request:105 에서 잠그고, end_request(blk.h:113-114)에서 푼다. 사이에 프로세스는 잠들어 있다.",
         13, K.MUTED)

    # 35 시연 B 계획
    p = d.slide("시연 B 계획: 인터럽트 후 b_uptodate 반전", K.S_DEMO,
                "lab/ 빌드 · QEMU i386(-drive if=ide) · GDB · 원본 미수정 — end_request 는 inline이라 줄 중단점(hd.c:265)")
    auto_pane(d, p, 1100, 4400, 19700, 10100, "GDB — 중단점과 관찰",
              "# end_request 는 blk.h 의 extern inline — 심볼 중단점 불가\n"
              "(gdb) b do_hd_request\n"
              "(gdb) b read_intr\n"
              "# 타이밍에 따라 write_intr 가 먼저 걸리면 조건부 사용:\n"
              "#   b read_intr if CURRENT->nr_sectors == 1\n"
              "(gdb) b hd.c:265        # end_request(1) 직전 줄 중단점\n"
              "(gdb) b buffer.c:277    # bread 복귀 지점\n"
              "(gdb) c                 # 게스트: cat /etc/rc (부팅 직후)\n"
              "# do_hd_request 에서\n"
              "(gdb) p *CURRENT        # sector·nr_sectors=2\n"
              "(gdb) p *CURRENT->bh    # b_lock=1 · b_uptodate=0\n"
              "(gdb) set $bh = CURRENT->bh\n"
              "#   CURRENT 는 end_request 안에서 next 로 바뀐다 — 미리 보관\n"
              "# read_intr 두 번 hit\n"
              "(gdb) p CURRENT->nr_sectors     # 2 → 1 → 0\n"
              "(gdb) p current->pid    # 인터럽트 문맥 — 요청자가 아님(§8)", start=12)
    para(d, p, 22000, 4400, 10000, 10100,
         "관찰 대상\n\n"
         "· do_hd_request — p *CURRENT\n  sector·nr_sectors=2\n  bh->b_lock=1 ·\n  bh->b_uptodate=0\n"
         "· read_intr 두 번 —\n  nr_sectors 2→1→0\n"
         "· hd.c:265 직후 —\n  $bh->b_uptodate=1 ·\n  $bh->b_lock=0\n"
         "· buffer.c:277 — 복귀 지점\n  b_uptodate=1\n\n"
         "주의 — set $bh 로 미리 보관(§8)\n캡처 04·05·06·07 → 36장", 14)

    # 36 시연 B 캡처
    p = d.slide("시연 B 캡처", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · 인터럽트 중단점은 타이밍에 따라 write_intr 가 먼저 걸릴 수 있어 조건부 중단 사용 · current->pid 는 실행마다 다름")
    capout(d, p, 1100, 4150, 15200, 5000,
           "(gdb) b do_hd_request ; c\n"
           "Breakpoint 1, do_hd_request () at hd.c:294\n"
           "(gdb) p *CURRENT\n"
           "{dev = 0x306, cmd = 0, sector = 274, nr_sectors = 2, ...}\n"
           "(gdb) p *CURRENT->bh\n"
           "{b_lock = 1 '\\001', b_uptodate = 0 '\\000', ...}",
           "04-do-hd-request-current.png")
    capout(d, p, 16900, 4150, 15700, 5000,
           "(gdb) b read_intr ; c\n"
           "Breakpoint 2, read_intr () at hd.c:250\n"
           "(gdb) p CURRENT->nr_sectors ; p current->pid\n"
           "$1 = 2        $2 = 0\n"
           "(gdb) c   # 두 번째 hit\n"
           "$3 = 1        $4 = 0   # task 0 — 인터럽트 문맥",
           "05-read-intr-nr-sectors.png")
    capout(d, p, 1100, 9350, 15200, 5000,
           "(gdb) b hd.c:265 ; set $bh = CURRENT->bh\n"
           "(gdb) n ; p $bh->b_uptodate ; p $bh->b_lock\n"
           "$5 = 1 '\\001'\n"
           "$6 = 0 '\\000'   # 0→1 · 1→0 반전\n"
           "(gdb) c   # b buffer.c:277\n"
           "(gdb) p bh->b_uptodate ; $7 = 1",
           "06-end-request-flag-flip.png")
    capout(d, p, 16900, 9350, 15700, 5000,
           "(gdb) info registers eip\n"
           "eip 0x...  <read_intr+..>  hd.c:250\n"
           "#  ← 인터럽트 문맥\n"
           "(gdb) p current->pid\n"
           "$8 = 0    # '그때 실행 중이던' 태스크\n"
           "# 인터럽트는 누구의 문맥도 아니다(§8)",
           "07-interrupt-context-pid.png")

    # 37 시연 C 계획
    p = d.slide("시연 C 계획: 쓰기와 sync", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 원본 미수정 — 시간 부족 시 다음 장 사전 캡처로 대체한다")
    auto_pane(d, p, 1100, 4400, 19700, 10100, "GDB — 쓰기 경로",
              "# 게스트: echo x > /tmp/f\n"
              "#   12회차 file_write 가 b_dirt=1 로 만든다\n"
              "# 게스트: sync\n"
              "(gdb) b sys_sync\n"
              "(gdb) b add_request\n"
              "(gdb) c\n"
              "Breakpoint 1, sys_sync () at fs/buffer.c:44\n"
              "(gdb) c\n"
              "Breakpoint 2, add_request (...) at ll_rw_blk.c:64\n"
              "(gdb) p req->bh->b_dirt\n"
              "#     기대 1 — 아직 더러움\n"
              "(gdb) n      # 70-71 사이 한 줄\n"
              "(gdb) p req->bh->b_dirt\n"
              "#     기대 0 — 큐에 넘어갔다\n"
              "(gdb) p req->cmd\n"
              "#     기대 1 (WRITE)\n"
              "(gdb) c\n"
              "Breakpoint 3, write_intr () at hd.c:269", start=12)
    para(d, p, 22000, 4400, 10000, 10100,
         "관찰 포인트\n\n"
         "· add_request 진입 —\n  b_dirt=1\n"
         "· 한 줄 뒤(ll_rw_blk.c:70-71)\n  — b_dirt=0\n"
         "· req->cmd = 1 (WRITE)\n"
         "· write_intr hit\n\n"
         "시간 부족 시\n"
         "다음 장(38) 사전 캡처로 대체하고\n"
         "'sync 를 부르지 않으면 더러운\n"
         "버퍼는 디스크로 가지 않는다\n"
         "(재사용 시 제외)'만 강조한다.", 14)

    # 38 시연 C 캡처
    p = d.slide("시연 C 캡처", K.S_DEMO,
                "lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 — 수치는 예시(실측 아님)")
    capout(d, p, 1100, 4150, 19700, 10300,
           "(gdb) b add_request ; b write_intr ; c\n"
           "# 게스트: echo x > /tmp/f ; sync\n"
           "Breakpoint 1, add_request (dev=0x37f0, req=0x...) at ll_rw_blk.c:64\n"
           "(gdb) p req->bh->b_dirt\n"
           "$1 = 1\n"
           "(gdb) n        # 70-71 사이\n"
           "(gdb) p req->bh->b_dirt\n"
           "$2 = 0         # 큐에 들어가는 순간 '더러움'을 넘김\n"
           "(gdb) p req->cmd\n"
           "$3 = 1         # WRITE\n"
           "(gdb) c\n"
           "Breakpoint 2, write_intr () at kernel/blk_drv/hd.c:269",
           "08-write-path-dirt-sync.png")
    para(d, p, 22000, 4150, 10000, 10300,
         "관찰 대상(§5)\n\n"
         "· add_request 진입 b_dirt=1 →\n  한 줄 뒤 0 (ll_rw_blk.c:70-71)\n"
         "· req->cmd = 1\n"
         "· write_intr hit — 29장 hd_out 이\n  지정한 &write_intr\n\n"
         "강조 — 0.11 은 sync 를 부르지\n않으면 더러운 버퍼가 디스크로\n가지 않는다(재사용 시 제외).\n주기적 writeback 은 없다(§8).",
         14)

    # ── 정답 39 ───────────────────────────────────────────────
    # 39 질문의 답
    p = d.slide("질문의 답: read()가 디스크에 접근하는 때", K.S_ANS,
                "세 관문을 모두 통과할 때만 do_hd_request 가 포트에 명령 — 관문 밖은 모두 메모리 복사")
    gates = [
        ("관문 1 — bread:273", "getblk 결과의 b_uptodate", "1이면 즉시 반환 — 디스크 0번"),
        ("관문 2 — make_request:106", "rw==READ && b_uptodate 재검사",
         "그 사이 누가 읽었으면 unlock 후 반환"),
        ("관문 3 — 슬롯", "request[0..31] 중 dev<0", "없으면 잠듦 — 확보될 때까지"),
    ]
    for i, (t, cond, fail) in enumerate(gates):
        x = 1100 + i * 10400
        nbox(d, p, x, 4700, 9600, 2400, t, cond, K.PAPER, s1=15, s2=12)
        arrow(d, p, x + 4300, 7120, "↓ 통과", 16, K.ORANGE)
        d.text(p, x + 200, 7900, 9200, 450, "탈락 시", 11, K.MUTED, True)
        d.text(p, x + 200, 8350, 9200, 900, fail, 12, K.MUTED)
        if i < 2:
            arrow(d, p, x + 9700, 5600, "→", 22, K.TEAL)
    nbox(d, p, 1100, 9550, 20000, 1700,
         "do_hd_request → hd_out — 포트에 WIN_READ 명령", "여기가 '디스크에 실제로 접근'하는 유일한 순간",
         K.ORANGE, s1=16, s2=12)
    para(d, p, 22000, 9550, 10500, 1700,
         "이후 잠들고 — read_intr·port_read 가\n데이터를 가져오고 end_request 가 깨운다.",
         14, K.INK)
    d.banner(p, "'접근한다'의 실제 뜻 — 명령을 내리고 잠든다; 데이터는 인터럽트가 가져온다", 11500, 19)
    para(d, p, 1100, 13400, 31500, 1400,
         "나머지 모든 read() 는 bread → getblk 해시 적중 → memcpy — 디스크는 돌지 않는다.\n"
         "같은 블록 두 번째 read()가 바로 그 경우다(시연 A, 20-21장).", 15)

    # ── 배경 40–42 ────────────────────────────────────────────
    # 40 전체 그림: 계층과 경계
    p = d.slide("전체 그림: 계층과 경계", K.S_BG,
                "경계를 넘는 하향 호출은 ll_rw_block 하나 · 돌아오는 상향 통로는 end_request 의 wake_up 하나")
    layers = [
        ("파일 시스템 — fs/namei.c · inode.c (12회차)",
         "bread(dev, block) 를 부른다 — block 번호를 계산해 온다"),
        ("버퍼 캐시 — fs/buffer.c",
         "블록 단위(1024B) · 장치 무관 — 해시 + free list · 플래그 4개"),
        ("블록 장치 드라이버 — kernel/blk_drv/ll_rw_blk.c · hd.c",
         "섹터(512B)·요청 큐·포트·인터럽트 — IN_ORDER 엘리베이터"),
    ]
    for i, (t, m) in enumerate(layers):
        y = 4700 + i * 2900
        fill = K.TEAL if i == 1 else K.PAPER
        nbox(d, p, 5300, y, 20500, 2600, t, m, fill, s1=16, s2=12)
    arrow(d, p, 2300, 5100, "ll_rw_block", 15, K.ORANGE, 3300, 700)
    d.text(p, 1800, 5800, 3600, 900, "↓ 하향 호출 1개\n(경계 횡단)", 12, K.ORANGE, True)
    arrow(d, p, 2300, 8000, "↓", 22, K.ORANGE)
    arrow(d, p, 2300, 10900, "↓", 22, K.ORANGE)
    arrow(d, p, 27400, 10900, "wake_up(end_request)", 13, K.ORANGE, 5400, 700)
    d.text(p, 26300, 5800, 5400, 900, "상향 복귀 1개 ↑\nb_uptodate=1 · 잠긴 호출자 기상",
           12, K.ORANGE, True)
    arrow(d, p, 28600, 8000, "↑", 22, K.ORANGE)
    arrow(d, p, 28600, 5100, "↑", 22, K.ORANGE)
    para(d, p, 5300, 13300, 26000, 1300,
         "위 두 층 사이의 약속 — bread/brelse 와 buffer_head. 아래 두 층 사이의 약속 — "
         "request 큐와 CURRENT. 각 층은 서로의 내부를 모른다.", 15)
    d.banner(p, "12회차의 namei 가 오늘 bread 를 부른다 — block 번호의 출처가 다음 이야기", 14800, 18)

    # 41 현대 커널과의 차이
    p = d.slide("현대 커널과의 차이 (짧게)", K.S_BG,
                "'Linux 0.11에는 없다 / 다르다' 확인만 — 14회차에서 다시 다룬다")
    d.table(p, 1100, 4500, [7000, 11000, 13500], [
        ["항목", "0.11 (1991)", "현대 커널"],
        ["캐시", "버퍼 캐시 — 1024B 고정 buffer_head", "페이지 캐시 + bio"],
        ["요청 큐", "request[32] 전역 배열 · 장치별 단일 큐", "블록 멀티큐 (per-CPU/sw)"],
        ["스케줄러", "단방향 엘리베이터 IN_ORDER", "mq-deadline · BFQ · kyber"],
        ["동기화", "sync 수동 호출 — flush 데몬 없음", "writeback 스레드 · dirty ratio"],
        ["전송", "PIO — port_read/port_write (insw)", "DMA · IRQ 공유"],
    ], row_h=1600, size=14)
    d.banner(p, "지금 읽은 구조가 어떻게 살아남았고 어떻게 갈아졌는지 — 14회차 «종합·실습»에서 재개", 14800, 18)

    # 42 흔한 오해
    p = d.slide("흔한 오해", K.S_BG,
                "buffer.c · ll_rw_blk.c · blk.h:40-43 · sched.c:188-194 — 오해 네 가지 × 정정")
    d.table(p, 1100, 4500, [9800, 21700], [
        ["오해", "정정"],
        ["\"bread 가 디스크를 읽는다\"",
         "보통은 안 읽는다 — b_uptodate=1 이면 메모리에서 즉시 반환 (buffer.c:273-274)"],
        ["\"read_intr 가 프로세스를 깨운다\"",
         "end_request 의 wake_up 이 state=0으로 바꿀 뿐 — 실행은 다음 schedule (sched.c:188-194)"],
        ["\"b_dirt=1 이면 곧 디스크에 써진다\"",
         "sync 나 재사용 전까지 메모리에만 — 주기적 writeback 은 없다 (§8)"],
        ["\"요청 큐는 FIFO\"",
         "IN_ORDER 엘리베이터다 — READ 가 WRITE 보다 앞선다 (blk.h:40-43)"],
    ], row_h=2000, size=15)
    d.banner(p, "인터럽트 문맥의 current 는 요청자가 아니라 '그때 실행 중이던 태스크'다 — 시연 B 캡처 07(§8)",
            13800, 17)

    # 43 수치 참고
    p = d.slide("수치 참고 (코드 추론)", K.S_CODE,
                "추론(소스 상수·산식)과 관찰(캡처)을 분리 — 관찰값은 부팅·실행마다 다를 수 있다")
    d.table(p, 1100, 4500, [5400, 7600, 8600], [
        ["항목", "값", "근거"],
        ["NR_HASH", "307 버킷", "fs.h:47 (추론)"],
        ["NR_REQUEST", "32 — WRITE 는 앞 21칸만", "blk.h:15 · ll_rw_blk.c:115-118 (추론)"],
        ["BLOCK_SIZE", "1024B = 섹터 2개", "fs.h:49 · ll_rw_blk.c:136-137 (추론)"],
        ["MAX_ERRORS", "7 — 넘으면 end_request(0)", "hd.c:34 (추론)"],
        ["루트 장치", "0x306 — major 3 · minor 6", "boot/bootsect.s:43 (추론)"],
        ["NR_BUFFERS", "'N buffers = M bytes buffer space'",
         "3회차 부팅 캡처 (기존 기록 · 관찰)"],
    ], row_h=1450, size=13)
    d.picture(p, str(K.ROOT / "build" / "boot.png"), 24300, 4700, 7300, 4100,
              tag="기존 기록")
    para(d, p, 24300, 9100, 7300, 1300,
         "buffer_init 의 결과가 부팅 때 한 번 보고된다 — 값은 buffer_memory_end 에 따라 달라진다.",
         12, K.MUTED)
    para(d, p, 1100, 13600, 22000, 900,
         "lab 빌드의 심볼(_ 접두)·줄 번호는 src 왔 다를 수 있다 — 캡처 각주의 근거(계획 §11).",
         12, K.MUTED)

    # ── 확인 44–45 ────────────────────────────────────────────
    # 44 이해 확인 질문
    p = d.slide("이해 확인 질문", K.S_QUIZ,
                "4문항 — 정답과 근거 줄 번호는 다음 장(45) · 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "Q1",
         "bread(dev, b) 가 디스크 명령을 내리지 않고 돌아오는 두 지점의 조건은?", K.TEAL, 16)
    qbox(d, p, 1100, 6850, 31500, 2400, "Q2",
         "do_hd_request() 는 READ 명령을 내린 뒤 무엇을 하는가? 데이터는 누가 메모리에 넣는가?",
         K.TEAL, 16)
    qbox(d, p, 1100, 9400, 31500, 2400, "Q3",
         "b_dirt 는 누가 1로 만들고 누가 0으로 만드는가?", K.TEAL, 16)
    qbox(d, p, 1100, 11950, 31500, 2400, "Q4",
         "큐에 WRITE 요청이 가득 찰 수 있는가?", K.TEAL, 16)

    # 45 이해 확인 정답
    p = d.slide("이해 확인 정답", K.S_QUIZ,
                "근거 줄 번호 포함 — 원문 그대로(계획 §6)")
    qbox(d, p, 1100, 4300, 31500, 2400, "A1",
         "(1) getblk 가 돌려준 버퍼의 b_uptodate 가 1 (buffer.c:273-274). "
         "(2) 그 사이에 다른 프로세스가 읽기를 끝내 make_request 의 재검사 "
         "rw==READ && bh->b_uptodate (ll_rw_blk.c:106-109)에 걸림.", K.ORANGE, 13)
    qbox(d, p, 1100, 6850, 31500, 2400, "A2",
         "hd_out 으로 포트에 명령만 쓰고 리턴한다 (hd.c:337-338). 데이터는 IRQ14 → "
         "hd_interrupt (system_call.s:221-250) → read_intr (hd.c:250-267)의 port_read 가 "
         "섹터마다 512B씩 CURRENT->buffer 로 옮긴다.", K.ORANGE, 13)
    qbox(d, p, 1100, 9400, 31500, 2400, "A3",
         "1: 버퍼를 고친 파일 시스템 코드 (예: file_write, new_block, write_inode; 12회차). "
         "0: add_request 가 쓰기 요청을 큐에 넣는 순간 (ll_rw_blk.c:70-71), getblk 가 새로 "
         "할당할 때 (buffer.c:244), invalidate_buffers (95).", K.ORANGE, 13)
    qbox(d, p, 1100, 11950, 31500, 2400, "A4",
         "아니다. WRITE 는 request[0..20] (앞 2/3)만 탐색하고 (ll_rw_blk.c:115-118), "
         "나머지 11개는 READ 전용이다. 또 IN_ORDER 에서 cmd 비교로 READ 가 WRITE 보다 "
         "앞에 삽입된다 (blk.h:40-43).", K.ORANGE, 13)

    # 46 정리와 다음 회차
    p = d.slide("정리와 다음 회차", K.S_WRAP,
                "12회차 — 파일 시스템: inode와 경로 탐색(namei) · 파트 E «파일·저장» 계속")
    d.cards(p, [
        ("오늘의 함수 6개",
         "bread — 조회·대기\n"
         "getblk — 해시·BADNESS\n"
         "brelse — 반납\n"
         "ll_rw_block — 계층 진입\n"
         "do_hd_request — 명령 발행\n"
         "read_intr — 반입·완료"),
        ("플래그 4개 (fs.h:68-81)",
         "b_uptodate — 디스크와 같음\n"
         "b_dirt — 디스크보다 새로움\n"
         "b_lock — I/O 진행 중\n"
         "b_count — 쓰는 사람 수\n"
         "상태도 ①(16장)·②(33장)"),
        ("12회차 예고",
         "\"/etc/rc라는 문자열이\n"
         "어떻게 디스크 블록이 되는가?\"\n\n"
         "오늘 bread 의 block 이\n"
         "어디서 오는지 — namei·inode\n"
         "파트 E «파일·저장» 계속"),
    ], y=4400, h=8600)
    d.banner(p, "read()는 버퍼 캐시를 지난다 — 디스크 명령은 세 관문을 모두 통과할 때만 한 번(39장)")


if __name__ == "__main__":
    K.run(globals())
