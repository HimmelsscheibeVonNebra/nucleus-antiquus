#!/usr/bin/env python3
"""deckkit 스모크 테스트 — 공통 프레임과 모든 도우미를 12장으로 점검한다.

실행: /usr/bin/python3 scripts/smoke_deck.py /tmp
출력: /tmp/smoke-deck.pptx (레포지터리 output/ 에는 쓰지 않는다)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckkit as K

SESSION = dict(
    no="05", total=14, slug="smoke-deck",
    part_no="B", part="«실행의 길»",
    title="99. 스모크 테스트 —\n킷 검증용 가상 회차",
    question="킷의 모든 도우미가 겹침 없이 그려지는가?",
    done=4,
    today_line="킷 검증 —\n모든 도우미를 한 번씩",
    next_lines=["04 → 05   이전 회차 연결 문구 테스트",
                "다음 회차 «가상» — 연결 문구 두 번째 줄",
                "세 번째 줄"],
    road_note="스모크 — 10단계 띠 아래 안내 문구 자리.",
    STRUCT=dict(teal=["proc", "entry", "main", "lib"],
                today=[("boot/head.s", "페이지 테이블"),
                       ("include/asm/system.h", "매크로 모음"),
                       ("include/linux/sched.h", "task_struct")],
                flow="IRQ 0 → _timer_interrupt → do_timer → schedule → switch_to → TSS 전환",
                up="↑ main → 셸",
                user="init · sh — 오늘 경로의 도착점"),
)

CHECKS = dict(
    captions={7: "src/boot/setup.s:191-193"},
    required=["자동 축소", "CR0.PE → 1", "기존 기록", "예상 출력"],
    prereq=[("자동 축소", "src/boot/setup.s:191-193")],
    structure_nodes=["system_call.s", "boot/head.s", "sched.h", "IRQ"],
    capture_slides=[11, 12],
)


def populate(d):
    p = d.slide("네 카드 + 배너", K.S_BG, "cards 자동 축소 확인 — 긴 제목")
    d.cards(p, [("짧은 제목", "본문\n둘째 줄"), ("아주 긴 카드 제목 자동 축소 테스트", "본문"),
                ("세 번째", "본문"), ("네 번째 카드", "본문")], h=6000)
    d.banner(p, "배너 한 줄 — cards 아래 배치, 겹침 없음.")

    p = d.slide("6항목 플로우", K.S_CMP, "flow 제목 자동 축소 확인")
    d.flow(p, [("BIOS", "펌웨어"), ("bootsect", "512B"), ("setup", "보호 모드"),
               ("head", "페이징"), ("main→task0", "pause 루프"), ("init→셸", "exec /bin/sh")], h=3100)
    d.text(p, 1100, 9300, 31500, 3000, "플로우 아래 본문 텍스트 세 줄.\n겹침 없는지 확인.\n세 번째 줄.", 20)

    p = d.slide("코드 자동 높이 + 해설", K.S_CODE, "code() — 패널 높이·글자 크기 자동")
    d.code(p, "src/boot/setup.s", 191, 193,
           "① mov — 준비\n② lmsw — PE=1\n③ jmpi — CS 교체\n\n해설 넉넉히 여덟 줄\n정도까지 안전하다.")

    p = d.slide("긴 코드 자동 축소", K.S_CODE, "code() — 14줄 인용이 12pt로 줄어드는지")
    d.code(p, "src/init/main.c", 126, 137,
           "초기화 호출 목록\n12줄 인용 테스트\n자동 크기 축소 확인", expl_size=16)

    p = d.slide("표 자동 축소", K.S_STATE, "table() — 셀 넘침 방지")
    d.table(p, 1100, 4500, [7000, 7000, 17500], [
        ["단계 · 원인", "상태 요약", "변경 데이터 (아주 긴 셀 텍스트 자동 축소 확인용)"],
        ["lmsw ax", "보호 모드", "CR0.PE → 1"],
        ["movl %eax,%cr0", "페이징 on", "CR0.PG → 1 · CR3 = pg_dir"],
    ], row_h=1600)
    d.banner(p, "표 아래 배너.")

    p = d.slide("상태도 예시 태그", K.S_STATE, "example_tag")
    d.example_tag(p)
    d.flow(p, [("시작", "EAX 미정"), ("movl $1,%eax", "EAX = 1"), ("addl $2,%eax", "EAX = 3")], h=4200)
    d.text(p, 1400, 10500, 30500, 2000, "본문 설명 두 줄.", 20)
    d.banner(p, "설명용 예시 태그가 우상단에 있는지.")

    p = d.slide("캡처 — 실측 아님 패널", K.S_DEMO, "placeholder_output")
    d.placeholder_output(p, 1100, 4300, 19700, 10200,
                         "Loading system ...\n3840 buffers = 3932160 bytes buffer space\n# echo boot-ok\nboot-ok",
                         "99-example.png")
    d.text(p, 22000, 4700, 10000, 9000, "우측 해설 — 관찰 대상·대체 자료를 적는다.", 17)

    p = d.slide("부팅 화면 — 기존 기록", K.S_DEMO, "picture + tag")
    d.picture(p, str(K.ROOT / "build/boot.png"), 1100, 4300, 19000, 11500, tag="기존 기록")
    d.text(p, 21800, 4700, 10800, 8000, "우측 해설 — 부팅 화면 캡처 대체.", 17)

    p = d.slide("code_panel 자유 배치", K.S_CODE, "code_panel — 두 패널 나란히")
    d.code_panel(p, "src/boot/head.s", 198, 218, 1100, 4300, 15200, 10200, size=10)
    d.code_panel(p, "src/boot/head.s", 135, 144, 17200, 4300, 15400, 6000, size=11)

    p = d.slide("정리", K.S_WRAP, "마지막 장")
    d.flow(p, [("A", "요약"), ("B", "요약"), ("C", "요약"), ("D", "요약")], h=3100)
    d.banner(p, "스모크 완료.")


if __name__ == "__main__":
    K.run(globals(), output_dir=sys.argv[1] if len(sys.argv) > 1 else "/tmp")
