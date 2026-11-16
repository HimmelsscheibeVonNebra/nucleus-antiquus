# 02회차 상세 슬라이드 제작 계획 — x86 보호 모드와 소스 읽기 도구

- 기준: materials/course-plan.md `# 02. x86 보호 모드와 소스 읽기 도구` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/02-protected-mode.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 40장 → 이 계획 46장 (+6)
- 로드맵 위치: 파트 A «입문·부팅» · 02/15

## 1. 회차 개요

- **핵심 질문**: 선택자 하나가 어떻게 주소가 되는가? GDB로 커널을 멈추면 무엇이 보이는가?
- **학습 목표** (course-plan 원문 계승):
  1. 선택자(index/TI/RPL) → 설명표(GDT/LDT) 항목 → base/limit/권한 → 선형 주소 → (페이징) 물리 주소의 경로를 손으로 따라갈 수 있다.
  2. 0.11의 GDT 초기 항목(head.s)과 task_struct 안의 LDT·TSS 항목(sched.h)을 64비트 값으로 해독한다.
  3. IDT 게이트의 종류(인터럽트/트랩/태스크)와 DPL이 `set_intr_gate`/`set_trap_gate`/`set_system_gate` 매크로에서 어떻게 비트로 들어가는지 읽는다.
  4. 권한 전환 시 스택이 TSS의 ss0/esp0로 바뀌고 CPU가 무엇을 push하는지 상태도로 설명한다.
  5. VS Code + QEMU `-s -S` + GDB로 lab/ 커널을 `main`에서 멈추고 레지스터·스택·GDT 메모리를 직접 관찰한다.
- **읽을 소스 범위** (원본 src/ 기준, 원천 표 그대로):

| 파일 | 줄 | 내용 |
|---|---|---|
| include/linux/head.h | 4-9 | `desc_struct {a,b}`, `desc_table[256]`, `extern idt,gdt,pg_dir` |
| include/linux/head.h | 11-18 | GDT_NUL/CODE/DATA/TMP, LDT_NUL/CODE/DATA 색인 |
| boot/head.s | 17-31 | startup_32: `movl $0x10,%eax` 세그먼트 로드, `lss _stack_start,%esp`, setup_idt/setup_gdt 호출 후 재로드 |
| boot/head.s | 78-93 | setup_idt: 256개 항목을 ignore_int 인터럽트 게이트(0x8E00)로 채우고 `lidt` |
| boot/head.s | 105-107 | setup_gdt: `lgdt gdt_descr` |
| boot/head.s | 222-229 | idt_descr / gdt_descr (limit 256*8-1, base) |
| boot/head.s | 232-238 | `_idt` 256×8 바이트, `_gdt` 4개 .quad(NULL, code 0x00c09a0000000fff, data 0x00c0920000000fff, TMP) + 252개 여유 |
| boot/setup.s | 205-224 | setup 단계의 임시 gdt(8Mb)·idt_48·gdt_48 — head.s와 대조용 |
| include/asm/system.h | 22-31 | `_set_gate`: `0x8000+(dpl<<13)+(type<<8)`, 선택자 0x0008 |
| include/asm/system.h | 33-40 | set_intr_gate(14,dpl0) / set_trap_gate(15,dpl0) / set_system_gate(15,dpl3) |
| include/asm/system.h | 42-50 | `_set_seg_desc` (세그먼트 설명자 비트 배치의 C 표현) |
| include/asm/system.h | 52-66 | `_set_tssldt_desc`, set_tss_desc(0x89), set_ldt_desc(0x82), limit 104 |
| include/linux/sched.h | 51-76 | `tss_struct` (esp0/ss0, cr3, eip, eflags, 범용·세그먼트 레지스터, ldt) |
| include/linux/sched.h | 103-106 | task_struct 안의 `ldt[3]`(0 nul, 1 cs, 2 ds&ss)와 `tss` |
| include/linux/sched.h | 123-133 | INIT_TASK의 ldt `{0x9f,0xc0fa00}`,`{0x9f,0xc0f200}`, tss `{0, PAGE_SIZE+&init_task, 0x10, ... 0x17 ..., _LDT(0), 0x80000000}` |
| include/linux/sched.h | 149-158 | FIRST_TSS_ENTRY 4, FIRST_LDT_ENTRY 5, `_TSS(n)`/`_LDT(n)`, ltr/lldt |
| include/linux/sched.h | 188-231 | `_set_base`/`_set_limit`/`_get_base`/`get_limit`(lsll) — 설명자 필드 조작 |
| kernel/sched.c | 58-72 | init_task, `user_stack[PAGE_SIZE>>2]`, `stack_start = {&user_stack[...], 0x10}` |
| kernel/sched.c | 385-412 | sched_init: GDT 4·5번에 TSS0/LDT0 설치, 나머지 클리어, `ltr(0)`,`lldt(0)` (상세는 03·05회차) |
| kernel/fork.c | 46-55 | copy_mem: `get_base(current->ldt[1])`, `set_base(p->ldt[1..2], ...)` — LDT가 태스크별인 이유 (예고만) |

- **상태 변화도 범위** (원천 3종 → 새 슬라이드 번호): ① 세그먼트 레지스터의 두 부분 → 19장 · ② 권한 전환 시 스택 → 24장 · ③ GDB 세션 → 30장.
- **모드·선택지 비교 범위** (원천 3종 → 새 슬라이드 번호): ① 설명표(GDT/LDT/IDT) → 07장 · ② IDT 게이트 종류(태스크 5/인터럽트 14/트랩 15) → 22장 · ③ 설명자 분류(S 비트) → 16장. 권한(CPL/DPL/RPL)은 세 가지 필드로만 비교하고 CPU 모드와 섞지 않는다(23장).

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 02. x86 보호 모드와 소스 읽기 도구 (표지) | 표지 | 대제목 `02. x86 보호 모드와 소스 읽기 도구` · 부제 = 핵심 질문 원문 전체 "선택자 하나가 어떻게 주소가 되는가? GDB로 커널을 멈추면 무엇이 보이는가?" · 우상단 `Linux 0.11` 배지 + `1991`, 부제 줄 `Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)` · 회차 정보 `02/15 · 파트 A «입문·부팅»` | —(course-plan 15회차 지도 표 02행) | 배지·푸터: 공통 규격 §1 |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 두 문장을 큰 글씨로(원문 그대로) · "오늘 끝에 이 두 질문에 답한다" 선언(원래 01장 문구 계승) · 오늘의 길: 10단계 미니 지도에서 오늘 실제 단계(배경·코드·상태도·비교·시연·정답·확인·정리) 강조, 질문·지도는 앞부분 01–04에서 이미 밟음 | —(course-plan 02 절 핵심 질문) | 10단계 미니 지도(공통 §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 15회차 7파트 타임라인(공통 §2 골격), 파트 A «입문·부팅» 중 01 완료(TEAL ■)·02 오늘(ORANGE ▶)·03 이후(□), 파트 B–G 전부 □ · 오늘 한 줄 문구와 01→02·02→03 연결 화살표 문구는 §3 명세 · 원래 "15회차 지도" 슬라이드(01 입문 → 02 도구·구조 → 03 부팅 경로 흐름)를 이 다이어그램으로 대체·흡수 | —(course-plan 15회차 지도 표) | 로드맵 도형(공통 §2 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | 오늘 파일 진한 TEAL: include/linux/head.h · boot/head.s · include/asm/system.h · include/linux/sched.h (+ kernel/sched.c·kernel/fork.c·boot/setup.s 보조 강조, 골격의 커널 공간에 '부트·헤더' 묶음 상자로 표기 — §3) · 데이터 흐름 화살표 2개(ORANGE): 논리 주소 → 선택자·GDT/LDT → 선형 주소 / 이벤트 → IDT 게이트 → CPL0 핸들러 · 누적 강조(01회차) boot/·init/main.c 옅은 TEAL | §3 명세 (include/linux/head.h · boot/head.s · include/asm/system.h · include/linux/sched.h) | 구조도 도형(공통 §2 골격) |
| 05 | 1회차 복습: 두 주소 모델 | 배경 | 실주소 모드 `seg*16+off` 공식 · 보호 모드 "선택자→설명자→base+off" · 그림 두 개 나란히로 대조 · 01회차 부팅 흐름(bootsect→setup→head→main)에서 이 모델 전환이 일어난 지점 복기 | —(1회차 요약: course-plan 01 절) | 그림 2개 나란히 |
| 06 | 선택자 16비트 해부 | 배경 | index(13비트)/TI(1)/RPL(2) 비트필드 그림 · 0.11 상수 4개 해독표: 0x08(idx1,GDT,0) · 0x10(idx2,GDT,0) · 0x0f(idx1,LDT,3) · 0x17(idx2,LDT,3) · "선택자 = 주소가 아니라 표의 색인"(§8 오해 방지) | boot/head.s:18 · include/asm/system.h:3-6 · include/linux/sched.h:130 | 비트필드 그림 + 해독표 |
| 07 | 설명표 비교: GDT / LDT / IDT | 비교 | 80386의 세 표 전부 — 로드 명령 lgdt/lldt/lidt, 레지스터 GDTR/LDTR/IDTR, 선택 방식(TI=0/TI=1/벡터 번호) · 항목 크기 8바이트 · 0.11 사용처: head.s:92,106(lidt/lgdt) / sched.c:405(lldt) — 모두 사용 | boot/head.s:78-93 · 105-107 · kernel/sched.c:385-412 | 비교표(3열) |
| 08 | GDTR·IDTR의 실제 값 — head.s | 코드 | head.s:222-229 `idt_descr`/`gdt_descr` 코드 · limit 256*8-1, base `_idt`/`_gdt` · `lgdt`/`lidt`가 읽는 6바이트(limit 2 + base 4) 구조 | boot/head.s:222-229 | 코드 인용 |
| 09 | 표는 두 번 만들어진다 — setup.s 대조 | 코드 | setup.s:218-224의 임시 표: gdt(limit 0x800, base 0x9xxxx)·idt_48·gdt_48 · setup 단계 임시 표 → head.s 본 표로 교체되는 흐름 · "표는 두 번 만들어진다" — 03회차가 이 순서를 다룸(43장 연결) | boot/setup.s:205-224 | 코드 2블록 병치(head.s 대비 setup.s) |
| 10 | head.s의 GDT 원문 | 코드 | head.s:232-238 `_gdt` 4개 .quad: NULL · 0x00c09a0000000fff · 0x00c0920000000fff · TMP, 이어 `.fill 252,8,0` · "252개 여유가 LDT·TSS 자리"(sched.h:150-151 주석) — 15장 슬롯 그림·36장 시연 B-3과 연결 | boot/head.s:232-238 · include/linux/sched.h:149-158 | 코드 인용 + GDT 슬롯 그림(항목 0–5) |
| 11 | 세그먼트 설명자 64비트 해부 — 비트 배치 | 배경 | 64비트 레이아웃 그림: base(32)·limit(20)·G·D/B·P·DPL·S·type · base·limit 필드가 8바이트 안에 비선형으로 흩어진 위치 강조 · 다음 장에서 이 그림으로 실제 값을 해독 | include/asm/system.h:42-50 | 64비트 레이아웃 그림 |
| 12 | GDT 코드·데이터 설명자 해독 | 코드 | `0x00c09a0000000fff` 해독: base 0, limit 0xfff, G=1 → 16MB, P=1 DPL=0 S=1 type=0xA(code exec/read) · 0x92 → data r/w(0x00c0920000000fff 동일 절차) · system.h:42-50 `_set_seg_desc`의 OR 식을 11장 그림 필드에 하나씩 대응 | boot/head.s:232-238 · include/asm/system.h:42-50 | 해독표 + 코드 인용 |
| 13 | task_struct 안의 LDT | 코드 | sched.h:103-104 `ldt[3]` 주석 "0 - zero 1 - cs 2 - ds&ss" · INIT_TASK sched.h:125-126 `{0x9f,0xc0fa00}`/`{0x9f,0xc0f200}` 해독: limit 0x9f(G=1 → 640KB, 주석 sched.h:111), DPL=3, 코드/데이터 · "왜 DPL 3인가" 질문으로 던지기(답은 23장·41장) | include/linux/sched.h:103-106 · 123-133 | 코드 인용 + 해독표 |
| 14 | 설명자 필드를 만지는 매크로 | 코드 | sched.h:188-212 `_set_base`/`_set_limit`/`set_base`/`set_limit` · 흩어진 base 바이트(+2,+4,+7)를 `rorl`로 채우는 코드 · fork.c:54-55에서 자식 LDT base를 바꾸는 한 줄(06회차 예고) | include/linux/sched.h:188-231 · kernel/fork.c:46-55 | 코드 인용 + base 필드 흩어짐 그림 |
| 15 | 시스템 설명자: TSS·LDT | 코드 | system.h:52-66 `_set_tssldt_desc`: limit 104, type 0x89(TSS available) / 0x82(LDT) · sched.h:153-158 FIRST_TSS_ENTRY 4, `_TSS(n)=16n+32`, `_LDT(n)=16n+40` → TSS0 선택자 0x20, LDT0 0x28 · sched.c:392-393, 404-405 `ltr(0)`,`lldt(0)` (상세는 03·05회차) | include/asm/system.h:52-66 · include/linux/sched.h:149-158 · kernel/sched.c:385-412 | 코드 인용 + GDT 슬롯 배치 그림 |
| 16 | 설명자 분류 비교 | 비교 | S 비트 기준: 코드/데이터(S=1) vs 시스템(S=0: TSS, LDT, 게이트) · 각 유형의 0.11 생성 매크로(`_set_seg_desc` / `_set_tssldt_desc` / `_set_gate`)와 사용 여부 | include/asm/system.h:42-66 · include/linux/sched.h:103-106 | 비교표 |
| 17 | tss_struct와 "숨은 스택" | 코드 | sched.h:51-76 구조체: esp0/ss0, cr3, eip, eflags, 범용·세그먼트 레지스터, ldt · esp0/ss0는 CPL0 진입 시 CPU가 자동 로드 · INIT_TASK sched.h:128: esp0 = `PAGE_SIZE+&init_task`, ss0=0x10 → task_union의 페이지 끝(sched.c:53-58) | include/linux/sched.h:51-76 · 123-133 · kernel/sched.c:53-58 | 코드 인용 + 구조체 그림 |
| 18 | 선택자 → 선형 → 물리: 전체 경로 | 배경 | 그림: `0x17:0x1234` → LDTR → LDT[2] → base+0x1234 = 선형 → CR3/페이지 테이블 → 물리 · 오늘은 선형까지, 페이징은 07회차 · 커널 세그먼트(base 0)는 선형=오프셋 | include/linux/sched.h:188-231 · boot/head.s:232-238 | 전체 경로 그림(핵심 질문 1의 답 구도) |
| 19 | 상태 변화도 1: 세그먼트 레지스터의 두 부분 | 상태도 | 상태 = {보이는 선택자 값, 보이지 않는 캐시(base/limit/attr)} · `lgdt`는 GDTR만 바꾸고 캐시는 불변 · `mov %ax,%ds`/`jmpi`/`lss`가 설명표를 읽어 캐시 갱신 — 다음 로드까지 유지 · head.s:26-31 재로드 코드 인용(주석 "reload all the segment registers after changing gdt") | boot/head.s:17-31 · 105-107 | 상태도(두 부분 + 갱신 트리거) |
| 20 | IDT 게이트 64비트 해부 — 비트 배치 | 배경 | 게이트 레이아웃 그림: 선택자(16)·offset(32)·P·DPL·type · 세그먼트 설명자(11장)와 같은 8바이트이지만 배치가 다름 · 다음 장에서 실제 매크로·값과 대응 | include/asm/system.h:22-31 · boot/head.s:78-93 | 64비트 레이아웃 그림 |
| 21 | `_set_gate`와 setup_idt의 0x8E00 | 코드 | system.h:22-31 `_set_gate`: `%0 = 0x8000+(dpl<<13)+(type<<8)`, eax=0x00080000 → 선택자 0x0008 · head.s:79-82 setup_idt의 0x8E00과 동일 비트 확인(P=1, DPL=0, type=14) | include/asm/system.h:22-31 · boot/head.s:78-93 | 코드 인용 + 비트 대응 표 |
| 22 | 게이트 종류 비교 (IDT, 80386) | 비교 | 태스크(5)/인터럽트(14)/트랩(15) 전부 · 차이: 인터럽트 게이트는 진입 시 IF 클리어 · 0.11: system.h:33-40 → set_intr_gate(14,dpl0) / set_trap_gate(15,dpl0) / set_system_gate(15,dpl3) — 태스크 게이트 미사용 · 콜 게이트는 IDT가 아닌 GDT/LDT용(범위 밖 한 줄) | include/asm/system.h:33-40 | 비교표(type·IF·DPL·사용) |
| 23 | 권한: CPL / DPL / RPL | 배경 | 세 필드 정의와 검사 규칙 한 줄씩 — 데이터 세그먼트: max(CPL,RPL) ≤ DPL · 게이트: CPL ≤ 게이트 DPL · `int $0x80`이 CPL3에서 되는 이유 = set_system_gate의 dpl 3(sched.c:411) · `int3`(traps.c:188)도 같은 이유 | include/asm/system.h:33-40 · kernel/sched.c:411 · kernel/traps.c:188 | 3필드 비교표 |
| 24 | 상태 변화도 2: 권한 전환과 스택 | 상태도 | CPL3 실행 → 게이트 통과 → TSS.ss0/esp0 로드 → SS,ESP,EFLAGS,CS,EIP push → 핸들러(CPL0) → `iret` → CPL3 복귀 · 변경 데이터 표기: SS/ESP/CS/EIP/EFLAGS · system.h:1-14 move_to_user_mode가 이 프레임을 "거꾸로 만든다"(01회차 연결) | include/linux/sched.h:53-54 · kernel/fork.c:93-94 · include/asm/system.h:1-14 | 상태도(스택 프레임 그림) |
| 25 | lab/ 환경 지도 | 배경 | src(원본, 인용 기준) vs lab(yuan-xy 기반, 현대 GCC·QEMU i386 실행본) · 심볼 이름·줄 번호가 다를 수 있음 경고(§11 확인 목록) · 빌드 산출물: Image, system/System.map | —(lab/ 구조 · course-plan 운영 원칙) | 디렉터리 구조 그림 |
| 26 | QEMU `-s -S` | 배경 | `-s` = gdbstub :1234 · `-S` = CPU 정지 상태로 시작 · 정지 직후 상태(real mode, EIP 0xfff0, CS 0xf000)는 아직 BIOS 전 · 재설정·종료 방법 | —(lab/ 실행 스크립트 · QEMU i386) | 텍스트 강조 중심 |
| 27 | GDB 연결과 실행 제어 명령 | 배경 | `target remote :1234` 연결, `symbol-file`(lab/tools/system ELF) 심볼 로드 · `b main`, `c`, `si`/`n`, `bt` — 각 명령이 무엇을 하는가 한 줄씩 | —(lab/tools/system · GDB) | 명령표 |
| 28 | GDB 관찰 명령 — 무엇을 읽는가 | 배경 | `info registers` — 레지스터(선택자 값) · `x/8xw $esp` — 스택 메모리 · `x/8xw &gdt` — 커널 데이터 메모리 · `p/x $cr0` — 제어 레지스터(노출 여부는 §11 확인) | —(GDB) | 명령표(읽는 대상 열) |
| 29 | VS Code 연결 | 캡처 | launch.json(gdb remote :1234, program=system ELF) 핵심 항목 · Breakpoints·Registers·Memory 패널 캡처 · 터미널 GDB와 같은 정보를 다르게 보여줄 뿐임을 명시 | —(lab/ launch.json) | 캡처 01-vscode-debug-panels.png |
| 30 | 상태 변화도 3: GDB 세션 | 상태도 | QEMU `-S` 정지(EIP=0xfff0, real mode) → `target remote` 연결 → `b main`/`c` → 중단(보호 모드, 페이징 ON) → `si`/`n`/`c` · 각 상태에서 가능한 명령 | —(lab/ · QEMU -s -S · GDB) | 상태도 |
| 31 | 시연 A-1: `b main` 도달 | 시연 | 시연 A 절차: 터미널1 `qemu-system-i386 ... -s -S`(lab/의 실행 스크립트), 터미널2 `gdb lab/tools/system`(ELF) → `target remote :1234` → `b main`(init/main.c:104 원본 기준) → `c` · 터미널 캡처: `Breakpoint 1, main () at init/main.c:NN` · 각주: lab/ 수정본, QEMU i386 TCG, 줄 번호는 lab 기준 | init/main.c:104(원본 기준 중단점) | 캡처 02-gdb-break-main.png · 대체 build/gdb-main.txt |
| 32 | 시연 A-2: `info registers` | 캡처 | 캡처: cs=0x0008, ds/es/fs/gs/ss=0x0010 · eflags에서 IF=0 · cr0 비트0(PE)·비트31(PG)=1, cr3=0 · 06장 해독표와 대조 · cr0의 MP/EM/ET는 FPU 유무에 따라 다름(head.s:43-61) — 전체 값은 "관찰 결과"로만 | boot/head.s:17-31 · 43-61 | 캡처 03-info-registers.png |
| 33 | 시연 A-3: `x/8xw $esp` | 캡처 | 캡처: 스택 최상단에 L6 복귀 주소와 0,0,0(head.s:136-140의 push) · esp가 `user_stack` 끝 근처(sched.c:67-72)임을 `p &user_stack`으로 확인 | boot/head.s:136-140 · kernel/sched.c:67-72 | 캡처 04-stack-dump-esp.png |
| 34 | 시연 B-1: GDT 베이스 찾기 | 시연 | 시연 B 절차: QEMU 모니터 `info registers`의 `GDT=` 줄(base·limit) 캡처 · GDB `p &gdt`가 같은 값인지 대조 · GDB 원격에서 GDTR이 직접 안 보이면 모니터를 쓴다는 설명(§11 확인 항목) | boot/head.s:222-229 | 캡처 05-gdt-base-monitor-vs-gdb.png |
| 35 | 시연 B-2: `x/8xw &gdt` (main 진입 시점) | 캡처 | 캡처 기대: `0x00000000 0x00000000 0x00000fff 0x00c09a00 0x00000fff 0x00c09200 0x00000000 0x00000000` · head.s:234-237 원문과 1:1 대조(리틀엔디언 순서 주의) | boot/head.s:232-238 | 캡처 06-gdt-dump-at-main.png |
| 36 | 시연 B-3: sched_init 이후 GDT | 캡처 | `b sched_init`→`finish` 뒤 `x/4xw &gdt[4]` · TSS0(type 0x89, limit 0x68=104, system.h:53)·LDT0(0x82) 설명자가 채워짐 · 전후 비교 그림 — 10장 GDT 슬롯 그림·15장 근거와 연결 · sched.c:392-393 근거 | kernel/sched.c:385-412 · include/asm/system.h:52-66 | 캡처 07-gdt-dump-after-sched-init.png + 전후 비교 그림 |
| 37 | 시연 C-1: LDT 항목 읽기 | 시연 | 시연 C 절차: `p/x init_task.task.ldt`(또는 `x/6xw &init_task.task.ldt`) · 관찰: 0x9f/0xc0fa00, 0x9f/0xc0f200 · 13장 해독과 대조 | include/linux/sched.h:125-126 | 캡처 08-init-task-ldt.png |
| 38 | 시연 C-2: IDT 항목 읽기 | 캡처 | `x/2xw &idt[0x80]`(sched_init 이후): 하위 워드 0x0008(선택자), 상위에 0xEF00(P=1,DPL=3,type 15) + system_call 주소 · `x/2xw &idt[0x20]`는 0x8E00(인터럽트 게이트) — 21·22장과 대조 | include/asm/system.h:22-40 | 캡처 09-idt-entries-0x80-0x20.png |
| 39 | 시연 C-3: 선택자 로드 추적 | 캡처 | head.s:18-22 위치에서 `si`로 `mov %ax,%ds` 전후 `info registers ds` 비교 · 값은 바뀌지만 base/limit는 GDB에 안 보임(캐시는 숨겨짐)을 체험 — 19장 상태도 1 확인 · 선택 항목: head.s 초기(페이징 전) 중단은 불안정할 수 있어 실패 시 사전 캡처 | boot/head.s:17-31 | 캡처 10-heads-segment-reload.png · 대체 사전 캡처 |
| 40 | 관찰 vs 추론 | 배경 | 표: 캡처로 본 것 — 레지스터 값, 메모리 덤프 / 소스에서 추론한 것 — 캐시 갱신, CPU의 push 순서, 권한 검사 · 혼동 금지(§8) | —(이 회차 시연·코드 전체) | 2열 표 |
| 41 | 답 1: 선택자가 주소가 되는 법 | 정답 | 06·11–12·18장을 한 장으로: `0x17:off` → LDT[2].base + off · 0.11에서 task 0은 base 0 · 자식은 fork.c:54-55에서 `nr*0x4000000`(06회차) | include/linux/sched.h:123-133 · kernel/fork.c:54-55 | 경로 그림 재사용(18장) |
| 42 | 답 2: 멈춘 커널에서 보이는 것 | 정답 | 보이는 것: 레지스터(선택자·CR0·EFLAGS), 스택(복귀 주소), 설명표(메모리 덤프) · 보이지 않는 것: 세그먼트 캐시, TLB | —(시연 A·B·C 관찰 종합) | 요약 표 |
| 43 | 다음 회차와의 연결 | 정리 | 03회차: 이 표들이 "언제" 만들어지는지 — setup.s 임시 GDT → head.s GDT → sched_init TSS/LDT · 04회차: 게이트를 "통과"하는 순간 | boot/setup.s · boot/head.s · kernel/sched.c | 로드맵 화살표 문구 재사용(§3) |
| 44 | 이해 확인 질문 | 확인 | 6문항, 정답 포함(§6 원문 그대로) · 개인 묵상 후 함께 풀이 · 정답 슬라이드 근거는 §6의 슬라이드 번호 | —(§6) | 문항 나열 |
| 45 | 정리 | 정리 | 선택자→설명자→base · 세 표(GDT/LDT/IDT) · 게이트 3종 · 권한 3필드 · GDB 5명령 | —(이 회차 전체) | 요약 표 |
| 46 | 03회차 예고 | 정리 | "부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?" · 다음 회차 핵심 질문 예고 | —(course-plan 03 절) | 없음 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- **파트**: 파트 A «입문·부팅» (01 CPU·어셈블리 · 02 보호 모드 · 03 부팅·초기화). 완료(TEAL ■) = 01. 오늘(ORANGE ▶) = 02. 이후(□) = 03–15 전부.
- **오늘 한 줄 문구**: "보호 모드의 표 — 선택자·GDT·IDT를 읽고 GDB로 직접 확인한다".
- **01→02 연결 화살표 문구**: "01: 부팅 흐름(bootsect→setup→head)을 따라가며 보호 모드 진입까지만 봤다 → 02: 그 보호 모드가 주소를 만드는 선택자·GDT 설명표를 읽는다".
- **02→03 연결 화살표 문구**: "02: 설명표가 '무엇'인지 해독했다 → 03: 그 표들이 '언제' 만들어지는가 — setup.s 임시 GDT → head.s GDT → sched_init TSS/LDT".

### 슬라이드 04 커널 구조도 — 오늘 범위

- **하이라이트 파일(진한 TEAL)**: include/linux/head.h · boot/head.s · include/asm/system.h · include/linux/sched.h — 공통 §2 골격에 헤더·부트 상자가 없으므로 커널 공간 상단에 '부트·헤더(오늘)' 묶음 상자로 추가하고 골격 나머지는 유지.
- **보조 강조**: kernel/sched.c(sched_init — GDT 4·5번 설치) · kernel/fork.c(copy_mem, 06회차 예고) · boot/setup.s(임시 표 대조용).
- **오늘의 데이터 흐름 화살표(ORANGE 2개)**: ① 논리 주소(세그먼트:오프셋) → 선택자 → GDT/LDT → base+오프셋 = 선형 주소(→ CR3/페이지 테이블은 07회차, 점선) · ② 이벤트(인터럽트/`int`) → IDT 게이트 → CPL0 핸들러(TSS ss0/esp0 스택).
- **누적 강조할 01 영역(옅은 TEAL)**: boot/(bootsect.s·setup.s)와 init/main.c — 01회차가 다룬 부팅 흐름. setup.s는 01 누적 영역이자 오늘 대조 자료(09장)로 라벨 병기.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 과정 로드맵 | 도형 | 공통 §2 골격, 파트 A의 01 ■·02 ▶, 연결 화살표 2개와 문구 | 없음(공용 골격 최초 제작 — 03회차부터 재사용) |
| 04 | 커널 전체 구조도 | 도형 | 공통 §2 골격 + §3 명세(오늘 파일 4종, 흐름 화살표 2개, 01 누적 영역) | 없음(공용 골격 최초 제작) |
| 05 | 두 주소 모델 비교 그림 | 도형 2개 나란히 | 좌: 실주소 seg*16+off, 우: 보호 모드 선택자→설명자→base+off | 없음 |
| 06 | 선택자 16비트 비트필드 그림 | 도형 + 표 | index(13)/TI(1)/RPL(2) 분할, 상수 4개 해독표 | 없음 |
| 07 | 설명표 비교표 | 표 | GDT/LDT/IDT × 로드 명령·레지스터·선택 방식·항목 크기·0.11 사용처 | 없음 |
| 10 | GDT 슬롯 그림 | 도형 | 항목 0–5 배치(NULL·code·data·TMP·TSS0·LDT0), 252 여유 | 없음(36장 전후 비교에서 재사용) |
| 11 | 세그먼트 설명자 64비트 레이아웃 | 도형 | base(32)·limit(20)·G·D/B·P·DPL·S·type 비트 배치 | 없음(12장 해독에서 재사용) |
| 14 | base 필드 흩어짐 그림 | 도형 | 설명자 8바이트에서 base 바이트(+2,+4,+7) 위치와 `rorl` 회전 | 없음 |
| 15 | GDT 슬롯 배치 그림(시스템 설명자) | 도형 | FIRST_TSS_ENTRY 4, `_TSS(n)=16n+32`, `_LDT(n)=16n+40` → 선택자 0x20/0x28 | 10장 그림 확장 |
| 16 | 설명자 분류표 | 표 | S=1/S=0 × 형식·생성 매크로·0.11 사용 | 없음 |
| 18 | 선택자→선형→물리 경로 그림 | 도형 | 0x17:0x1234 → LDTR → LDT[2] → base+0x1234 → 선형 → CR3/페이지 테이블(점선, 07회차) | 없음(41장에서 재사용) |
| 19 | 상태 변화도 1 | 도형 | 보이는 선택자 / 숨은 캐시 두 상자, lgdt(캐시 불변)·재로드(갱신) 화살표 | 없음 |
| 20 | 게이트 설명자 64비트 레이아웃 | 도형 | 선택자(16)·offset(32)·P·DPL·type 배치 | 없음(21장 비트 대응에서 재사용) |
| 22 | 게이트 종류 비교표 | 표 | 태스크(5)/인터럽트(14)/트랩(15) × IF·DPL·0.11 사용 | 없음 |
| 24 | 상태 변화도 2 | 도형 | CPL3 스택 → TSS.ss0/esp0 → CPL0 스택 push(SS,ESP,EFLAGS,CS,EIP) → iret 복귀 | 없음 |
| 30 | 상태 변화도 3 | 도형 | QEMU 정지 → 연결 → 중단점 → 중단 → step/continue → 종료 | 없음 |
| 36 | GDT 전후 비교 그림 | 도형 | main 진입 시(항목 0–3) vs sched_init 뒤(항목 4·5 채워짐) | 10장 그림 재사용 |
| 40 | 관찰 vs 추론 표 | 표 | 캡처로 본 것 / 소스에서 추론한 것 2열 | 없음 |

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/02-protected-mode/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| (준비) VS Code 연결 — 29장 | 01-vscode-debug-panels.png | launch.json(gdb remote :1234, program=system ELF) | Breakpoints·Registers·Memory 패널 | 사전 캡처 스크린샷 |
| A. main에서 멈추기 — 31장 | 02-gdb-break-main.png | 터미널1 `qemu-system-i386 ... -s -S`(lab/ 실행 스크립트) · 터미널2 `gdb lab/tools/system` → `target remote :1234` → `b main`(init/main.c:104 원본 기준) → `c` | `Breakpoint 1, main () at init/main.c:NN` 도달 | 사전 캡처 `build/gdb-main.txt`(기존 기록 표시) |
| A. main에서 멈추기 — 32장 | 03-info-registers.png | `info registers` | cs=0x0008 / ds·es·fs·gs·ss 0x0010 / eflags IF=0 / cr0 PE=1·PG=1 / cr3=0 (MP/EM/ET는 관찰 결과로만 — head.s:43-61) | 사전 캡처 `build/gdb-main.txt` |
| A. main에서 멈추기 — 33장 | 04-stack-dump-esp.png | `x/8xw $esp` · `p &user_stack` | L6 복귀 주소와 0,0,0(head.s:136-140), esp ≈ user_stack 끝(sched.c:67-72) | 사전 캡처 |
| B. GDT 덤프 전후 비교 — 34장 | 05-gdt-base-monitor-vs-gdb.png | QEMU 모니터 `info registers`(GDT= 줄) · GDB `p &gdt` | GDTR base·limit와 `&gdt` 일치 여부(GDB 원격에서 GDTR 미노출 시 모니터 사용) | 사전 캡처 |
| B. GDT 덤프 전후 비교 — 35장 | 06-gdt-dump-at-main.png | `x/8xw &gdt` | `0x00000000 0x00000000 0x00000fff 0x00c09a00 0x00000fff 0x00c09200 0x00000000 0x00000000`(리틀엔디언) | 사전 캡처(전) |
| B. GDT 덤프 전후 비교 — 36장 | 07-gdt-dump-after-sched-init.png | `b sched_init` → `c` → `finish` → `x/4xw &gdt[4]` | 항목 4 = TSS0(type 0x89, limit 0x68=104, system.h:53)·항목 5 = LDT0(0x82) 채워짐(sched.c:392-393) | 사전 캡처 두 장(전/후) |
| C. LDT·IDT·선택자 로드 — 37장 | 08-init-task-ldt.png | `p/x init_task.task.ldt`(또는 `x/6xw &init_task.task.ldt`) | 0x9f/0xc0fa00, 0x9f/0xc0f200(sched.h:125-126) | 사전 캡처 |
| C. LDT·IDT·선택자 로드 — 38장 | 09-idt-entries-0x80-0x20.png | `x/2xw &idt[0x80]` · `x/2xw &idt[0x20]`(sched_init 이후) | IDT[0x80] 하위 0x0008·상위 0xEF00(P=1,DPL=3,type 15) + system_call 주소 / IDT[0x20] 0x8E00 | 사전 캡처 |
| C. LDT·IDT·선택자 로드 — 39장 | 10-heads-segment-reload.png | `b *0`(또는 lab의 startup 심볼) → `si` 반복 → `info registers ds` | head.s:18-22 `mov %ax,%ds` 전후 ds 값 변화 — base/limit 캐시는 GDB에 안 보임 | 선택 항목 — 심볼 주소 0 근처라 불안정 시 사전 캡처 |

공통 각주(전 캡처): "lab/(yuan-xy/Linux-0.11 기반 수정본), QEMU i386, TCG. 줄 번호·심볼명은 lab 기준이며 슬라이드 인용은 src/ 원본."

## 6. 이해 확인 질문과 정답

슬라이드 44에서 6문항 모두 제시·풀이한다(원천 원문 계승).

1. 선택자 0x17을 index/TI/RPL로 나누면? — index 2, TI=1(LDT), RPL=3. (0001 0111b)
2. `lgdt`를 실행하면 DS가 가리키는 세그먼트의 base가 바로 바뀌는가? — 아니오. 세그먼트 레지스터를 다시 로드해야 캐시가 갱신된다(head.s:26-31). (근거 슬라이드 19)
3. `0x00c09a0000000fff`에서 limit는 몇 바이트인가? — 0xfff+1 페이지 × 4KB = 16MB (G=1). (근거 슬라이드 12)
4. `set_system_gate`와 `set_trap_gate`의 유일한 차이는? — DPL 3 vs 0 (system.h:36-40). 둘 다 type 15(트랩 게이트). (근거 슬라이드 21·22)
5. CPL3에서 `int $0x80`으로 진입할 때 커널 스택 포인터는 어디서 오는가? — 현재 태스크 TSS의 ss0/esp0 (sched.h:53-54). (근거 슬라이드 17·24)
6. GDB `info registers`에서 보이지 않는 세그먼트 정보는? — 설명자 캐시(base/limit/attr). 선택자 값만 보인다. (근거 슬라이드 19·42)

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 선택자(index/TI/RPL) | 세그먼트 레지스터에 넣는 16비트 값 — 상위 13비트 색인, TI 1비트로 GDT/LDT 선택, 하위 2비트 RPL | 06 |
| 설명자(descriptor) | 설명표의 8바이트 항목 — base/limit/권한/형식 비트 배치 | 05 |
| GDTR/LDTR/IDTR | 세 설명표의 base·limit를 저장하는 CPU 레지스터(lgdt/lldt/lidt로 로드) | 07 |
| base/limit/G 비트 | 세그먼트 시작 주소(32비트)·크기(20비트)·크기 배율(G=1이면 4KB 단위) | 11 |
| DPL/RPL/CPL | 설명자·게이트의 요구 권한 / 선택자에 실린 요청 권한 / 현재 실행 특권 | 23 |
| S 비트(시스템 설명자) | S=1 코드·데이터, S=0 시스템(TSS·LDT·게이트) | 11 |
| TSS(esp0/ss0) | 태스크 상태 세그먼트 — CPL0 진입 시 CPU가 esp0/ss0에서 커널 스택을 가져옴 | 15 |
| 게이트(인터럽트/트랩/태스크) | IDT 항목 — 핸들러 선택자·오프셋과 진입 규칙(type 14/15/5) | 20 |
| 세그먼트 캐시(숨은 부분) | 세그먼트 레지스터의 보이지 않는 base/limit/attr 사본 — 재로드 시에만 갱신 | 19 |
| 선형 주소 | base+오프셋으로 만든 주소 — 페이징의 입력(07회차) | 18 |
| `lgdt`/`lidt`/`lldt`/`ltr` | GDTR/IDTR/LDTR/TR 적재 명령 | 07 |
| `lss` | SS와 ESP를 한 번에 로드하는 명령(head.s의 `lss _stack_start,%esp`) | 19 |
| gdbstub | QEMU가 `-s`로 여는 GDB 원격 디버깅 서버(:1234) | 26 |
| `-s -S` | QEMU 옵션 — gdbstub 개통 / CPU 정지 상태로 시작 | 26 |
| `target remote` | GDB에서 gdbstub에 접속하는 명령 | 27 |
| `x/8xw` | 메모리를 4바이트 워드 16진수 8개로 덤프하는 GDB 명령 | 28 |
| QEMU 모니터 | QEMU 자체 모니터 콘솔 — `info registers`로 GDTR 등 CPU 상태 표시 | 34 |
| System.map | 빌드 산출 심볼 주소표(lab/ 빌드) | 25 |

## 8. 흔한 오해 / 말하지 말아야 할 것

- "선택자 = 주소"라고 말하지 않는다. 선택자는 표의 색인이다.
- 0x0f/0x17이 "GDT 1·2번"이라고 말하지 않는다. TI=1이므로 LDT 항목이다.
- GDB `info registers`의 cr0 전체 값을 미리 단정하지 않는다(FPU 유무로 MP/EM이 달라짐, head.s:43-61).
- 페이징(선형→물리)은 오늘 범위 밖. "0.11 사용자 주소 = 물리 주소"라고 말하지 않는다.
- lab/의 줄 번호·심볼(`main` vs `_main`)이 src/와 다를 수 있음을 숨기지 않는다.
- 세그먼트 캐시 갱신, CPU의 push 순서는 **코드 추론·아키텍처 문서 근거**이며 GDB로 직접 본 것이 아니다.
- 태스크 게이트·콜 게이트는 "존재하지만 0.11은 쓰지 않는다"까지만 말한다.
- x86-64의 세그먼테이션 축소는 14회차 비교로 미룬다.

## 9. 120분 운영안

| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 표준 앞부분: 표지·핵심 질문 선언, 로드맵·구조도로 오늘 위치 (구 01–02 "핵심 질문, 15회차 지도") |
| 05–10 | 15 | 1회차 복습(실주소 vs 보호 모드), 선택자 구조, 설명표 비교, GDTR·IDTR 실제 값(head.s·setup.s 대조 포함) |
| 11–18 | 20 | 설명자 해독: 64비트 레이아웃, head.s GDT, LDT(INIT_TASK), TSS·LDT 시스템 설명자, 주소 변환 경로 |
| 19–24 | 15 | 세그먼트 레지스터 상태도, 게이트와 IDT, 권한(CPL/DPL/RPL), 스택과 권한 전환 상태도 |
| 25–30 | 15 | 도구 준비: lab/ 구조, VS Code, QEMU `-s -S`, GDB 연결 상태도 |
| 31–39 | 30 | 강사 시연 A/B/C (main 중단, 레지스터·스택, GDT 덤프 전후 비교) |
| 40–43 | 10 | 관찰 결과와 코드 추론의 대조, 선택자→주소 답 정리 |
| 44–46 | 10 | 이해 확인 질문, 정리·03회차 예고 |

## 10. 기존 계획 대비 변경·증가

- **앞부분 확장 (+2)**: 구 01(제목·핵심 질문)을 01 표지 + 02 핵심 질문과 오늘의 길로 분리. 구 02(15회차 지도)는 03 로드맵 다이어그램으로 대체·흡수(01 입문→02 도구·구조→03 부팅 경로 흐름은 §3 연결 문구로 보존)하고 04 커널 구조도를 신설 — 공통 규격 §2 표준 앞부분.
- **구 06 → 08+09 분할 (+1)**: 코드 두 화면 분량(head.s:222-229와 setup.s 대조) — 각 코드 블록에 캡션·해설 공간 확보.
- **구 08 → 11+12 분할 (+1)**: 그림+코드 혼합 — 64비트 레이아웃 그림(배경)과 실제 값 해독·`_set_seg_desc` 대응(코드) 분리.
- **구 16 → 20+21 분할 (+1)**: 그림+코드 혼합 — 게이트 레이아웃 그림과 `_set_gate`·0x8E00 비트 대응 분리.
- **구 22 → 27+28 분할 (+1)**: 명령 10개를 실행 제어(target remote/symbol-file/b/c/si/n/bt)와 관찰(info registers/x/8xw $esp/x/8xw &gdt/p/x $cr0)로 분리.
- **유형 어휘 정비(장수 변동 없음)**: 구 "제목"→표지, 구 "지도"→로드맵(03)·정리(43), 구 38 "질문"→확인, 구 35·36 "정리"→정답, 구 25 "시연·캡처"→시연 — 공통 규격 §3 어휘로 통일. 슬라이드 간 상호 참조도 새 번호로 갱신(구 "04장 해독표"→06, 구 "09장 해독"→13, 구 "04·08·14장"→06·11–12·18).
- 합계: 40장 → 46장 (+6). 목표 범위 44–50 안(공통 규격 §5).

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- lab/ 빌드 심볼명 확인: `main` vs `_main`, `gdt` vs `_gdt`, `init_task` — 시연 A(`b main`)·B(`p &gdt`)·C(`p/x init_task.task.ldt`) 명령이 그대로 동작하는지, 안 되면 `_` 접두로 수정하고 각주에 명시.
- QEMU gdbstub에서 `$cr3`·GDTR 노출 여부 — 미노출 시 QEMU 모니터 `monitor info registers`(시연 B-1의 `GDT=` 줄)로 대체, 32장의 cr3=0은 "관찰 결과"로만 서술.
- lab/ init/main.c의 `main` 줄 번호(원본 104 기준 캡션과 lab 캡처 `main () at init/main.c:NN`의 NN 차이) — 31장 각주에 반영.
- 시연 C-3의 `b *0`(또는 lab의 startup 심볼) 부근 중단 안정성 — 페이징 전 주소 0 근처는 GDB가 불안정할 수 있음, 실패 시 사전 캡처로 전환(선택 항목).
- 사전 캡처 자산 점검: `build/gdb-main.txt`, GDT 덤프 전/후 두 장 — 존재하면 `materials/02-protected-mode/captures/`로 복사하고 화면 모서리에 `기존 기록` 라벨(공통 규격 §7).
- 신규 캡처 파일명 규칙 준수: `materials/02-protected-mode/captures/<두자리순번>-<설명>.png`(§5 목록 01–10).
- VS Code 디버그 패널 캡처(01-vscode-debug-panels.png)의 launch.json 항목이 lab/ 빌드 산출물(system ELF)과 일치하는지.
