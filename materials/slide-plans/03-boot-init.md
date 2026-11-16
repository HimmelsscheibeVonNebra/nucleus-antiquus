# 03회차 상세 슬라이드 제작 계획 — 부팅과 커널 초기화

- 기준: materials/course-plan.md `# 03. 부팅과 커널 초기화` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/03-boot-init.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 40장 → 이 계획 47장 (+7)
- 로드맵 위치: 파트 A «입문·부팅» · 03/15

## 1. 회차 개요

**핵심 질문** (원문 그대로, 슬라이드 01·02·45에 사용)

부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?

**학습 목표** (원문 그대로)

1. BIOS → bootsect.s(0x7c00→0x90000) → setup.s(0x90200) → head.s(0x0) → main()의 메모리 배치와 적재 순서를 그림으로 그릴 수 있다.
2. 각 단계에서 PE / PG / IF / CPL 네 비트가 **어느 명령 때문에** 바뀌는지 줄 번호로 짚는다.
3. setup.s의 임시 GDT·A20·8259 재프로그래밍과 head.s의 IDT/GDT 재구성·페이징 설정이 "같은 표를 두 번 만드는" 이유를 설명한다.
4. main()의 초기화 함수 9개(mem_init … floppy_init)를 범주(메모리/게이트/장치/스케줄러)로 분류하고 각 함수가 **어떤 자료구조를 채우는지** 말한다.
5. `sti` → `move_to_user_mode` → 첫 `fork()` 까지의 상태 변화를 GDB로 확인한다.

**읽을 소스 범위** (파일:줄, 원본 src 기준 — 원천 절에서 그대로 계승)

| 파일 | 줄 | 내용 |
|---|---|---|
| Makefile | 41-43 | `Image = build bootsect setup system` — 디스크 이미지 배치 |
| boot/bootsect.s | 34-43 | SETUPLEN 4, BOOTSEG 0x07c0, INITSEG 0x9000, SETUPSEG 0x9020, SYSSEG 0x1000, ROOT_DEV |
| boot/bootsect.s | 46-62 | 자기 자신을 0x90000으로 복사, `jmpi go,INITSEG`, 스택 0x9000:0xFF00 |
| boot/bootsect.s | 67-79 | load_setup: `int 0x13` 서비스 2로 setup 4섹터를 0x90200에 적재, 실패 시 재시도 |
| boot/bootsect.s | 92-110 | "Loading system ..." 출력(int 0x10), `read_it`로 system을 0x10000에 적재, `kill_motor` |
| boot/bootsect.s | 117-139 | 루트 장치 결정, `jmpi 0,SETUPSEG` |
| boot/bootsect.s | 151-196 | read_it: 64KB 경계 검사, 트랙 단위 읽기 루프 (강사 참조) |
| boot/bootsect.s | 249-253 | `.org 508` root_dev, `boot_flag 0xAA55` |
| boot/setup.s | 36-105 | BIOS에서 커서·확장 메모리(int 0x15 ah=0x88 → [2])·비디오·hd0/hd1 파라미터를 0x90000-0x901FF에 저장 |
| boot/setup.s | 109 | `cli` — IF=0 |
| boot/setup.s | 113-126 | system을 0x10000 → 0x00000으로 이동(do_move) |
| boot/setup.s | 130-134 | `lidt idt_48`, `lgdt gdt_48` |
| boot/setup.s | 138-144 | A20 활성화(8042) |
| boot/setup.s | 154-179 | 8259A 재프로그래밍: IRQ → 0x20-0x2F, 마스크 0xFF |
| boot/setup.s | 191-193 | `mov ax,#1` / `lmsw ax` / `jmpi 0,8` — PE=1, 32비트 코드로 |
| boot/setup.s | 205-224 | 임시 gdt(8Mb), idt_48(0,0), gdt_48 |
| boot/head.s | 17-36 | startup_32: 세그먼트 0x10, `lss _stack_start`, setup_idt/setup_gdt, 재로드, A20 검사 루프 |
| boot/head.s | 43-65 | CR0의 MP/EM 설정, check_x87 |
| boot/head.s | 78-93 | setup_idt: 256개 ignore_int 게이트, `lidt` |
| boot/head.s | 105-107 | setup_gdt: `lgdt` |
| boot/head.s | 114-133 | pg0~pg3(.org 0x1000-0x4000), tmp_floppy_area |
| boot/head.s | 135-144 | after_page_tables: 0,0,0,L6,_main push → `jmp setup_paging`; L6 무한루프 |
| boot/head.s | 150-170 | ignore_int: "Unknown interrupt" printk |
| boot/head.s | 198-218 | setup_paging: 5페이지 클리어, pg_dir[0..3]=pgN+7, 16MB identity 채움, CR3=0, CR0.PG=1, `ret` → main |
| boot/head.s | 222-238 | idt_descr/gdt_descr, _idt, _gdt |
| init/main.c | 23-26 | `static inline _syscall0(int,fork)` / pause / setup / sync — 스택을 쓰지 않는 이유 주석 11-22 |
| init/main.c | 58-60 | EXT_MEM_K(0x90002), DRIVE_INFO(0x90080), ORIG_ROOT_DEV(0x901FC) — setup.s가 남긴 값 읽기 |
| init/main.c | 104-137 | main(): memory_end/buffer_memory_end 계산, 초기화 9함수, `sti()`, `move_to_user_mode()` |
| init/main.c | 138-149 | 첫 `fork()`, 자식 `init()`, 부모 `for(;;) pause();` |
| include/asm/system.h | 1-14 | move_to_user_mode: 0x17/esp/eflags/0x0f/1f push → iret → ds·es·fs·gs=0x17 |
| include/asm/system.h | 16-17 | sti/cli |
| include/unistd.h | 133-145 | `_syscall0`: `int $0x80`, eax=__NR_name |
| mm/memory.c | 43-47, 57 | LOW_MEM 0x100000, PAGING_PAGES, MAP_NR, USED 100, mem_map[] |
| mm/memory.c | 399-411 | mem_init: 1MB 이상 페이지를 USED로 채운 뒤 [start_mem,end_mem)만 0으로 |
| kernel/traps.c | 181-208 | trap_init: 0-16 트랩/시스템 게이트, 17-47 reserved, IRQ2/IRQ13 마스크 해제, 39 parallel |
| kernel/blk_drv/ll_rw_blk.c | 157-165 | blk_dev_init: request[] 32개 dev=-1 |
| kernel/chr_drv/tty_io.c | 105-109 | tty_init: rs_init + con_init |
| kernel/chr_drv/serial.c | 37-44 | rs_init: 게이트 0x23/0x24, IRQ3/4 마스크 해제 |
| kernel/chr_drv/console.c | 683-684 | con_init 끝: 게이트 0x21 키보드, IRQ1 마스크 해제 |
| kernel/chr_drv/tty_io.c | 347-349 | chr_dev_init: 빈 함수 |
| init/main.c | 76-96 | time_init: CMOS 읽기 → startup_time |
| kernel/sched.c | 46 | LATCH = 1193180/HZ |
| kernel/sched.c | 53-72 | task_union, init_task, task[], user_stack, stack_start |
| kernel/sched.c | 385-412 | sched_init: GDT TSS0/LDT0, task[1..] NULL, NT 클리어, ltr/lldt, 8253 타이머, 게이트 0x20, IRQ0 해제, 게이트 0x80 |
| fs/buffer.c | 348-381 | buffer_init: 버퍼 헤더·데이터 블록 연결(640KB-1MB 구멍 건너뜀), hash_table 초기화 |
| kernel/blk_drv/hd.c | 343-349 | hd_init: 게이트 0x2E, IRQ2/14 해제 |
| kernel/blk_drv/floppy.c | 457-462 | floppy_init: 게이트 0x26, IRQ6 해제 |
| kernel/system_call.s | 80-94 | _system_call 진입(04회차 본편, 오늘은 fork가 도달하는 곳만) |
| kernel/system_call.s | 208-219 | _sys_fork → copy_process (06회차 예고) |
| kernel/sched.c | 144-149 | sys_pause: TASK_INTERRUPTIBLE + schedule() |

**상태 변화도 / 모드·선택지 비교 범위** (원문 계승, 슬라이드 번호는 이 계획 기준)

- **상태 변화도(필수) — 단계별 PE/PG/IF/CPL + 실행 주소·스택**: 원천 12행 표 전체(§4 상세 명세). 이 계획에서는 세 장에 나눠 게시 — 중간 1(슬라이드 19, BIOS~`jmpi 0,8` 상단 6행), 중간 2(슬라이드 25, head.s 구간 행), 종합(슬라이드 36, 12행 전체 + 전환 횟수 세기). "변경되는 데이터"는 CR0·EFLAGS·CS/SS 선택자·ESP, "유지 조건"은 다음 전환 명령까지. IF는 표시 지점 값.
- **모드·선택지 비교 1 — 커널 적재 단계가 실행되는 세그먼트/주소** (원천 → 슬라이드 07): bootsect(0x07c0→0x9000) / setup(0x9020) / system(0x1000→0x0000). 각 단계의 적재자(BIOS / bootsect / bootsect+setup 이동), 크기 제한(512B / 4섹터 / SYSSIZE 0x3000 클릭), 관련 줄.
- **모드·선택지 비교 2 — 하드웨어 IRQ 0~15 전체** (원천 → 슬라이드 31): setup.s:176-179에서 전부 마스크한 뒤 초기화 함수가 **열어주는** IRQ만 표시 — IRQ0 타이머(sched.c:410), IRQ1 키보드(console.c:684), IRQ2 캐스케이드(traps.c:205, hd.c:347), IRQ3/4 시리얼(serial.c:43), IRQ6 플로피(floppy.c:461), IRQ13 FPU(traps.c:206), IRQ14 HD(hd.c:348). 나머지(5,7,8-12,15)는 마스크 유지. 열린 IRQ와 설치된 게이트 번호(0x20+n)·게이트 종류(intr/trap)를 같은 표에.
- **모드·선택지 비교 3 — main()이 설치하는 게이트 종류** (원천 → 슬라이드 32): set_trap_gate / set_intr_gate / set_system_gate 세 매크로 전부와 어느 함수가 어느 것을 쓰는지(traps.c:185-207, sched.c:409-411, hd.c:346, floppy.c:460, serial.c:39-40, console.c:683). 02회차의 게이트 비교를 "누가 언제"로 확장.

## 2. 전체 슬라이드 목록

공통 프레임(00-common §1·§3): 전 슬라이드 푸터 `Linux 0.11 커널 강좌 · 03/15 · 03-boot-init` + `MM / 47`, 본문(05번부터) 상단 10단계 미니 지도, 코드 캡션은 `src/` 기준.

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 03. 부팅과 커널 초기화 | 표지 | 대제목 `03. 부팅과 커널 초기화`, 부제 = 핵심 질문 "부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?" · 우상단 `Linux 0.11` 배지 + `1991`(ORANGE 채움·PAPER 글자) · 부제 아래 `Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)` · 회차 정보 `03/15 · 파트 A «입문·부팅»` · 네 비트(PE/PG/IF/CPL)를 오늘의 추적 대상으로 제시(구 01 계승) | —(표지, 인용 없음) | 배지(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 1문장 큰 글씨(원문 그대로) · 오늘의 길 = 10단계 미니 지도를 본문 크기로, 이 회차는 10단계 전부를 밟는다 — 상태도 19·25·36, 비교 07·31·32, 시연 37-42, 정답 45, 확인 44 · 예고: 강의 끝에 상태 변화 표(36)와 GDB 시연 A/B/C로 네 비트의 전환을 눈으로 확인 · 추적 대상 네 비트 재확인 PE/PG/IF/CPL | —(핵심 질문 원문) | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 15회차 7파트 타임라인 골격에서 파트 A «입문·부팅» 묶음 표시 · 완료 TEAL: 01 CPU·어셈블리, 02 보호 모드 · 오늘 ORANGE + 굵은 테두리: 03 — 파트 A의 마지막 회차 · 이후 MUTED: 04–15 · 오늘 한 줄 문구 + 앞→오늘·오늘→뒤 연결 화살표 2개(문구는 §3 명세) · 구 02 "15회차 지도" 내용(02 표 구조 → 03 표가 만들어지는 때 → 04 게이트 통과) 흡수 | —(로드맵 골격: 00-common §2) | 로드맵 도형(§3 명세) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | Linux 0.11 전체 구조도에서 오늘 파일 4개 TEAL 강조: boot/bootsect.s, boot/setup.s, boot/head.s, init/main.c · 오늘의 데이터 흐름 화살표 ORANGE: ROM BIOS → bootsect.s → setup.s → head.s → main() · 누적 강조(옅은 TEAL) 01–02 영역: 01의 boot/setup.s·boot/head.s·init/main.c 개관, 02의 include/linux/head.h·include/asm/system.h·include/linux/sched.h(GDT/LDT·TSS 도구) · 나머지 상자는 MUTED 실루엣, 계층 경계 CPL·IRQ 라벨 유지 | —(구조도 골격: 00-common §2) | 구조도 도형 + 부팅 경로 경유지(§3 명세) |
| 05 | 디스크 이미지의 배치 | 배경 | Makefile:41-42 `tools/build bootsect setup system` — 이미지가 이 순서로 디스크에 놓인다 · 그림: 섹터 1 bootsect(510바이트 + 0xAA55 부트 섹터 서명, bootsect.s:249-253 `.org 508` root_dev, boot_flag 0xAA55) · 섹터 2-5 setup(SETUPLEN 4섹터) · 섹터 6부터 system(head.s + main.c) · 오늘 강의 = 이 세 덩어리가 각각 어디로 옮겨져 실행되는가 | Makefile:41-43 · boot/bootsect.s:34-43, 249-253 | 디스크 이미지 배치 그림 |
| 06 | 메모리 지도 (적재 전후) | 배경 | 그림 적재 전: 0x7c00 bootsect(BIOS가 내려놓음) · 그림 적재 후: 0x90000 bootsect(자기 복사), 0x90200 setup, 0x10000 system → setup이 0x00000으로 이동 · 0x90000-0x901FF BIOS 파라미터 영역, 0x9FF00 스택(0x9000:0xFF00) · bootsect.s:34-39 상수 인용: SETUPLEN 4, BOOTSEG 0x07c0, INITSEG 0x9000, SETUPSEG 0x9020, SYSSEG 0x1000 | boot/bootsect.s:34-43, 46-62 · boot/setup.s:113-126 | 메모리 지도 그림(적재 전/후 나란히) |
| 07 | 적재 단계 비교 | 비교 | 비교 1: bootsect / setup / system 세 단계가 실행되는 세그먼트와 주소 · 축 5개: 적재 주소(0x07c0→0x9000 / 0x9020 / 0x1000→0x0000), 적재자(BIOS / bootsect / bootsect+setup 이동), 크기 제한(512B / 4섹터 / SYSSIZE 0x3000 클릭), 실행 모드(16비트 real / 16비트 real / 32비트 protected), 어셈블러(as86 / as86 / GNU as) | boot/bootsect.s:34-43, 67-79, 117-139, 151-196 · boot/setup.s:113-126 | 적재 단계 비교 표(3행 5축) |
| 08 | 추적 대상 네 비트 다시 보기 | 배경 | 1회차 18장 참조표 재게시: PE(CR0.0), PG(CR0.31), IF(EFLAGS.9), CPL(CS.RPL) · 이 네 비트가 오늘 상태 표(19·25·36)의 열 머리글 · 각 비트가 오늘 몇 번 바뀌는지 세어 본다고 예고 — PE 1회, PG 1회, IF 2회, CPL 1회 | boot/setup.s:109, 191-193 · boot/head.s:214-217 · init/main.c:136 · include/asm/system.h:1-14 | 네 비트 참조표(01회차 18장 재사용) |
| 09 | bootsect.s: 자기 복사 | 코드 | bootsect.s:46-62 코드 — `rep movw` 256워드로 자기 자신 512바이트를 0x90000(INITSEG)으로 복사 · `jmpi go,INITSEG` — CS를 0x9000으로 갱신하고 go부터 재실행 · 스택 설정 0x9000:0xFF00(ss/sp) · 상태 표시: CS 0x07c0→0x9000, SS:SP 생김 · 캡션 src/boot/bootsect.s:46-62 | boot/bootsect.s:34-43, 46-62 | 자기 복사 전후 주소 인서트 그림 |
| 10 | bootsect.s: setup 적재 | 코드 | bootsect.s:67-79 load_setup 코드 · `int 0x13` ah=2 서비스로 섹터 2부터 4개(SETUPLEN)를 ES:BX = 0x9000:0x0200(=0x90200)에 적재 · 실패 시 ah=0 리셋 후 재시도 무한루프(주석 21-23) — 실패 처리가 없는 최소 코드임을 보임 · 캡션 src/boot/bootsect.s:67-79 | boot/bootsect.s:67-79, 21-23 | — |
| 11 | bootsect.s: "Loading system ..." | 코드 | bootsect.s:92-110 코드 + 메시지 원문(244-247) · `int 0x10` ah=0x13으로 문자열 출력 · 같은 구간에서 `read_it` 호출로 system을 0x10000(SYSSEG)에 적재 개시, `kill_motor`로 플로피 모터 정지 · QEMU 캡처: 부팅 직후 이 문자열이 찍힌 화면(각주: lab/, QEMU i386, 캡처 날짜) · 캡션 src/boot/bootsect.s:92-110 | boot/bootsect.s:92-110, 244-247 | materials/03-boot-init/captures/01-loading-system-message.png |
| 12 | bootsect.s: system 적재 루프 read_it | 코드 | bootsect.s:151-196 read_it — 강사 참조 흐름도 · 64KB 경계 검사(경계마다 ES/AX 조정) · 트랙 단위 읽기 루프(현재 트랙·헤드·섹터 추적, `int 0x13` 반복) · 코드 전체를 읽지 않고 "ES가 0x1000씩 전진"하며 system을 0x10000 위로 쌓는 구조만 짚는다 · 캡션 src/boot/bootsect.s:151-196 | boot/bootsect.s:151-196 | read_it 흐름도 |
| 13 | bootsect.s: 루트 장치와 setup 점프 | 코드 | bootsect.s:117-139 — root_dev가 0이면 sectors 수로 플로피 종류 결정 · 루트 장치 번호를 결정해 저장 · `jmpi 0,SETUPSEG` — CS=0x9020, EIP=0으로 setup에 제어 이전 · 상태: CS=0x9020, 여전히 real mode, IF=1 · 캡션 src/boot/bootsect.s:117-139 | boot/bootsect.s:117-139, 249-253 | — |
| 14 | setup.s: BIOS에게 묻기 | 코드 | setup.s:36-105 표 — 커서→[0], 확장 메모리(int 0x15 ah=0x88)→[2], 비디오→[4..12], hd0→[0x80], hd1→[0x90]을 0x90000-0x901FF에 저장 · main.c:58-60이 같은 주소(EXT_MEM_K 0x90002, DRIVE_INFO 0x90080, ORIG_ROOT_DEV 0x901FC)를 읽는다는 연결 · "왜 지금 모아두는가" — protected 모드로 넘어가면 BIOS 호출 불가 · 캡션 src/boot/setup.s:36-105 | boot/setup.s:36-105 · init/main.c:58-60 | BIOS 파라미터 ↔ 저장 주소 ↔ main.c 대응 표 |
| 15 | setup.s: `cli`와 system 이동 | 코드 | setup.s:109 `cli` — IF=0, 이제 BIOS 인터럽트 사용 불가(setup.s:181-182 주석) · setup.s:113-126 do_move: system을 0x10000 → 0x00000으로 64KB씩, 0x90000 직전까지 이동 · "왜 0으로 옮기는가"(head.s:10-12 주석) · 캡션 src/boot/setup.s:109, 113-126 | boot/setup.s:109, 113-126, 181-182 · boot/head.s:10-12 | system 이동 전후 메모리 그림(06 그림 재사용) |
| 16 | setup.s: 임시 GDT·IDT | 코드 | setup.s:130-134 `lidt idt_48`(limit 0) / `lgdt gdt_48` · setup.s:205-224 원문: 임시 gdt — code/data 8Mb, base 0, idt_48(0,0), gdt_48 · 02회차 head.s GDT(16Mb)와 나란히 — "표는 두 번" 만들어진다 · 8Mb 한계·0x9xxxx 위치 문제는 이해 확인 문항 3으로 연결 · 캡션 src/boot/setup.s:130-134, 205-224 | boot/setup.s:130-134, 205-224 · boot/head.s:222-238 | 임시 GDT(8Mb) vs head.s GDT(16Mb) 나란히 보기 |
| 17 | setup.s: A20과 8259 | 코드 | setup.s:138-144 A20 활성화(8042 — 0xD1/0xDF 출력) · setup.s:154-179 8259A 재프로그래밍: ICW1-4로 IRQ를 0x20-0x2F로 옮기고 마스크 0xFF(전부 차단) · `.word 0x00eb,0x00eb` = jmp $+2 지연 · 마스크 0xFF는 main()의 초기화 함수가 하나씩 여는 초기 상태(슬라이드 31 비교 2 예고) · 캡션 src/boot/setup.s:138-144, 154-179 | boot/setup.s:138-144, 154-179, 176-179 | — |
| 18 | setup.s: `lmsw`와 `jmpi 0,8` | 코드 | setup.s:191-193 3줄: `mov ax,#1` / `lmsw ax` / `jmpi 0,8` · `lmsw`로 PE=1(CR0 비트0) — 그 직후 `jmpi 0,8`로 CS=0x0008(임시 GDT 1번 디스크립터), EIP=0 → 32비트 코드 시작 · `lmsw` 직후에도 세그먼트 레지스터는 옛값 — far jump로 다시 실어야 한다(1회차 25-26장 복습) · 인용은 191-193(186-190은 주석 — 기존 01 자료 186-193 표기의 정정) · 캡션 src/boot/setup.s:191-193 | boot/setup.s:191-193, 205-224 | — |
| 19 | 상태도(중간 1): real → protected | 상태도 | BIOS~setup 끝까지의 PE/PG/IF/CPL 행만 표시(§4 종합 표의 상단 6행) · 각 행의 전환 원인 줄 번호: int 0x19 / bootsect.s:56,61-62 / bootsect.s:139 / setup.s:109 / setup.s:191-192 / setup.s:193 · "CPL은 real mode에서 정의되지 않음"을 '—'로 표기 · 종합(36)의 미리보기 역할 | —(원천 상태 변화도 표 — §4 명세) | 상태 변화 표(전반 6행) |
| 20 | head.s: 첫 32비트 명령 | 코드 | head.s:17-23 startup_32 — ds/es/fs/gs=0x10 재적재 · `lss _stack_start,%esp`(sched.c:67-72 user_stack 끝, ss=0x10) · 상태: 커널 스택 생김(0x10:user_stack 끝), CS는 `jmpi 0,8`의 0x0008 유지 · PG는 아직 0 — 주소 0에서 실행 중 · 캡션 src/boot/head.s:17-36 | boot/head.s:17-36 · kernel/sched.c:53-72 | — |
| 21 | head.s: IDT/GDT 다시 만들기 | 코드 | head.s:24-31, 78-93, 105-107 — setup_idt는 256개 항목 전부 ignore_int(0x8E00)로 채우고 `lidt`, setup_gdt는 `lgdt`뿐 · setup.s의 임시 표를 커널 이미지 안의 표로 교체 — 재로드 이유(02회차 상태도 1) · ignore_int(150-170) "Unknown interrupt"는 04회차가 덮어쓸 기본 핸들러 · 그 뒤 A20 검사 루프(33-36) · 캡션 src/boot/head.s:24-31, 78-93, 105-107 | boot/head.s:24-36, 78-93, 105-107, 150-170, 222-238 | — |
| 22 | head.s: CR0와 x87 | 코드 | head.s:43-49 — `andl $0x80000011`(PG,PE,ET 보존), `orl $2`(MP 설정) · head.s:54-65 check_x87 — FPU 유무에 따라 CR0의 MP/EM 값이 달라짐 · CR0 전체 값은 FPU 유무로 달라진다 — 시연 B에서 관찰할 값, 단정하지 않는다 · 캡션 src/boot/head.s:43-65 | boot/head.s:43-65 | CR0 비트 분해 그림(0x80000011) |
| 23 | head.s: main 호출 프레임 | 코드 | head.s:135-144 after_page_tables 코드 — `pushl $0`×3(main 인자), `pushl $L6`(main 복귀 주소 = 무한루프), `pushl $_main`, `jmp setup_paging` · setup_paging의 `ret`(head.s:218)이 `_main`을 pop → main 진입 · "call이 아니라 ret로 들어간다" · L6 무한루프(142-143) — main이 반환해도 재부팅이 아님 · 캡션 src/boot/head.s:135-144 | boot/head.s:135-144, 198-218 | main 진입 프레임 그림(스택 5워드) |
| 24 | head.s: setup_paging | 코드 | head.s:198-218 코드 — pg_dir(0x0)~pg3 5페이지 클리어(배치는 head.s:114-133 pg0~pg3, .org 0x1000-0x4000) · pg_dir[0..3]=pgN+7 · 0xfff007부터 거꾸로 채움 — 16MB identity mapping · CR3=0, CR0.PG=1(head.s:214-217) → 상태: PG=1 · 그림: pg_dir이 startup 코드를 덮어씀(head.s:10-12) · 캡션 src/boot/head.s:198-218 | boot/head.s:114-133, 198-218, 10-12 | 페이지 테이블 구조·덮어쓰기 그림 |
| 25 | 상태도(중간 2): head.s 구간 | 상태도 | head 구간 행만 표시(§4 종합 표의 head~main 진입 행) · PE=1 유지, PG 0→1(head.s:217), IF 0 유지, CPL 0 · 스택 생성(head.s:23 `lss`), CS 0x0008 유지 · main() 진입 행 — head.s:218 `ret`(전환 원인) · 캡션 없음(표 슬라이드) | —(원천 상태 변화도 표 — §4 명세) | 상태 변화 표(head 구간 행) |
| 26 | main(): setup이 남긴 값 읽기와 메모리 경계 | 코드 | main.c:58-60 — EXT_MEM_K(0x90002), DRIVE_INFO(0x90080), ORIG_ROOT_DEV(0x901FC): setup.s가 0x90000-0x901FF에 남긴 값 읽기(슬라이드 14 연결) · main.c:110-122 — memory_end=1MB+EXT_MEM_K, 상한 16MB, buffer_memory_end 1/2/4MB 규칙 · 그림: [0,1MB) 커널 / [1MB,buffer_end) 버퍼 / [main_memory_start,memory_end) 페이지 풀 · 캡션 src/init/main.c:110-122 | init/main.c:58-60, 104-137 · mm/memory.c:43-47, 57 | 메모리 경계 3구간 그림 |
| 27 | main(): 초기화 9함수 범주표 | 배경 | main.c:126-135 순서대로 9함수 · 범주: 메모리(mem_init) / 게이트(trap_init) / 장치 표(blk_dev_init, chr_dev_init=빈 함수, tty_init) / 시간(time_init) / 스케줄러(sched_init) / 버퍼(buffer_init) / 블록 장치(hd_init, floppy_init) · 각 함수의 "채우는 자료구조" 한 칸: mem_map / IDT 게이트 / request[] 32개 dev=-1 / (빈 함수) / rs_init+con_init / startup_time / GDT TSS0·LDT0·task[] / 버퍼 헤더·데이터 블록 / 게이트·request_fn · 이 표가 슬라이드 28-33의 목차 | init/main.c:104-137, 76-96 · mm/memory.c:399-411 · kernel/traps.c:181-208 · kernel/blk_drv/ll_rw_blk.c:157-165 · kernel/chr_drv/tty_io.c:105-109, 347-349 · kernel/sched.c:385-412 · fs/buffer.c:348-381 · kernel/blk_drv/hd.c:343-349 · kernel/blk_drv/floppy.c:457-462 | 초기화 9함수 범주표 |
| 28 | mem_init | 코드 | memory.c:399-411 코드 — mem_map 전부 USED(100)로 채운 뒤 [start_mem,end_mem)만 0으로 · 상수: LOW_MEM 0x100000, PAGING_PAGES, MAP_NR, USED 100(memory.c:43-47, 57) · 1MB 이상 페이지만 페이지 풀로 — 슬라이드 26의 [main_memory_start,memory_end) 구간과 연결 · 캡션 src/mm/memory.c:399-411 · (구 26 전반 분할) | mm/memory.c:399-411, 43-47, 57 · init/main.c:110-122 | mem_map 채우기 순서 그림(USED → 0) |
| 29 | trap_init | 코드 | traps.c:181-208 코드 — 0-16 트랩/시스템 게이트 개별 설치 · 17-47 reserved로 채운 뒤 45(irq13), 39(parallel)만 덮음 · IRQ2/IRQ13 마스크 해제(205-206) · 게이트 3종(set_trap/set_intr/set_system)의 차이는 슬라이드 32 비교 3에서 · 캡션 src/kernel/traps.c:181-208 · (구 26 후반 분할) | kernel/traps.c:181-208 | 예외 번호 표(0-16, 45, 39) |
| 30 | sched_init | 코드 | sched.c:385-412 코드 — GDT 4·5번에 TSS0/LDT0 설치(02회차 30장 캡처 재사용) · task[1..63]=NULL, NT 클리어, `ltr(0)`/`lldt(0)` · 8253 타이머: LATCH = 1193180/HZ(sched.c:46) · 게이트 0x20(timer) 설치 + IRQ0 마스크 해제(410) · 게이트 0x80(system_call, DPL3) 설치(411) — 04회차 연결고리 · 캡션 src/kernel/sched.c:385-412 | kernel/sched.c:385-412, 46, 53-72 | 02회차 30장 GDT 캡처 재사용 |
| 31 | 비교 2: IRQ 0~15 전체와 열리는 순서 | 비교 | 표 16행(IRQ 0~15) — 마스크 초기값: setup.s:176-179에서 전부 1(차단) · 어느 함수가 어느 비트를 0으로 여는가: IRQ0 타이머(sched.c:410), IRQ1 키보드(console.c:684), IRQ2 캐스케이드(traps.c:205, hd.c:347), IRQ3/4 시리얼(serial.c:43), IRQ6 플로피(floppy.c:461), IRQ13 FPU(traps.c:206), IRQ14 HD(hd.c:348) · 나머지(5,7,8-12,15)는 마스크 유지 명시 · 열린 IRQ와 설치된 게이트 번호(0x20+n)·게이트 종류(intr/trap)를 같은 표에 | boot/setup.s:176-179 · kernel/sched.c:410 · kernel/chr_drv/console.c:683-684 · kernel/traps.c:205-206 · kernel/blk_drv/hd.c:346-348 · kernel/chr_drv/serial.c:37-44 · kernel/blk_drv/floppy.c:457-462 | IRQ 0~15 비교 표(16행) |
| 32 | 비교 3: main()이 설치하는 게이트 3종 | 비교 | set_trap_gate(type 15, DPL 0) / set_intr_gate(type 14, DPL 0) / set_system_gate(type 15, DPL 3) — 세 매크로 전부 · 어느 함수가 어느 것을 쓰는지: traps.c:185-207, sched.c:409-411, hd.c:346, floppy.c:460, serial.c:39-40, console.c:683 · 02회차의 게이트 비교를 "누가 언제"로 확장 · "왜 timer는 intr, 키보드는 trap인가"는 04·13회차로 넘김(사실만 표시) | kernel/traps.c:185-207 · kernel/sched.c:409-411 · kernel/blk_drv/hd.c:346 · kernel/blk_drv/floppy.c:460 · kernel/chr_drv/serial.c:39-40 · kernel/chr_drv/console.c:683 | 게이트 3종 비교 표 |
| 33 | buffer_init·hd_init·floppy_init | 코드 | buffer.c:348-381 — 버퍼 헤더는 앞에서, 데이터 블록은 buffer_end에서 거꾸로 연결 · 640KB-1MB 구멍 회피(372-373), hash_table 초기화 · hd.c:343-349 — 게이트 0x2E, IRQ2/14 해제 · floppy.c:457-462 — 게이트 0x26, IRQ6 해제 · 상세는 11회차 — 오늘은 "범주표의 칸을 채우는" 관찰만 · 캡션 src/fs/buffer.c:348-381 | fs/buffer.c:348-381 · kernel/blk_drv/hd.c:343-349 · kernel/blk_drv/floppy.c:457-462 | 버퍼 헤더/데이터 대칭 연결 그림 |
| 34 | `sti()`와 move_to_user_mode | 코드 | main.c:136-137 — `sti()`(IF 0→1, system.h:16), `move_to_user_mode()` · system.h:1-14 — 0x17/esp/eflags/0x0f/1f push → iret → ds·es·fs·gs=0x17 · iret 프레임 그림(0x17, esp, eflags, 0x0f, 1f) · 상태: IF=1, CPL 0→3, CS 0x0008→0x000f, SS 0x10→0x17, ESP 값 그대로(같은 user_stack) · 캡션 src/include/asm/system.h:1-14 | init/main.c:136-137 · include/asm/system.h:1-14, 16-17 | move_to_user_mode iret 프레임 그림 |
| 35 | 첫 fork()와 pause() | 코드 | main.c:23-26 `static inline _syscall0(int,fork)` / pause / setup / sync — 스택을 쓰지 않는 이유 주석(main.c:11-22: 커널 공간 fork는 COW 없음 → 스택 사용 금지) · unistd.h:133-145 `_syscall0`: `int $0x80`, eax=__NR_name · main.c:138-148 — 첫 `fork()`, 자식 `init()`, 부모 `for(;;) pause()` · system_call.s:80-94 진입(04회차 본편 — 오늘은 fork가 도착하는 곳만), system_call.s:208-219 `_sys_fork` → copy_process(06회차 예고) · sys_pause(sched.c:144-149): TASK_INTERRUPTIBLE + schedule() | init/main.c:23-26, 11-22, 138-148 · include/unistd.h:133-145 · kernel/system_call.s:80-94, 208-219 · kernel/sched.c:144-149 | — |
| 36 | 상태 변화도(종합): 부트 섹터에서 fork까지 | 상태도 | 원천 12행 표 전체(§4 상세 명세) — 단계 / PE / PG / IF / CPL / CS:EIP 위치 / 스택 / 전환 원인(줄) · 각 비트가 바뀌는 횟수를 세어 본다 — PE 1회, PG 1회, IF 2회, CPL 1회 · 값이 바뀌는 칸만 강조(TEAL 굵게), 유지 칸은 MUTED — 19·25에서 본 행의 합본 · 이 표가 핵심 질문의 답(슬라이드 45) 재료 | —(원천 상태 변화도 12행 표 — §4 명세) | 상태 변화 표·타임라인(12행 8열, §4 명세) |
| 37 | 시연 A: QEMU `-S` 직후부터 setup까지 | 시연 | 명령: `qemu-system-i386 ... -s -S` + QEMU 모니터(`-monitor stdio` 또는 Ctrl-Alt-2), GDB `target remote :1234` · `b *0x7c00` → `c` → 모니터 `info registers` · `b *0x90200`(setup) → `c` → 모니터 `info registers` · 관찰: `CR0=` 비트0=0, `EFL=` IF 비트(0x200), `CS =07c0`/`9020`, `SS:SP` · 주의: SeaBIOS가 0x7c00으로 점프하는 방식은 BIOS 구현에 따라 CS:IP 표기가 다를 수 있음(각주) | —(lab/ 시연 — 원천 강사 시연 A) | — |
| 38 | 캡처 A: 실주소 모드 레지스터 | 캡처 | (1) 정지 직후, (2) 0x7c00, (3) 0x90200에서의 `info registers` 3장 나란히 · 기대 출력: 0x7c00에서 CS=0x07c0(또는 0000:7c00 — BIOS 따라), 0x90200에서 CS=0x9020, 스택 0x9000:0xFF00(bootsect.s:61-62), IF=1(아직 cli 전) · 각주: QEMU 모니터 형식, lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · (구 34에서 분할) | boot/bootsect.s:61-62 · boot/setup.s:109, 191-193 | materials/03-boot-init/captures/02-a1-reset-registers.png · 03-a2-bootsect-0x7c00.png · 04-a3-setup-0x90200.png |
| 39 | 시연 B: PE·PG 켜지는 순간 | 시연 | GDB `b *0x0`(head.s startup_32, setup.s:193 직후 — 페이징 전) → `c` → `p/x $cr0`(비트0=1, 비트31=0) · `b *setup_paging`(lab 심볼) → `c` → `si`를 `ret`(head.s:218) 직전까지 → `p/x $cr0` 비트31=1 · 관찰: CR0 비트0·비트31, CR3=0, `si` 한 번으로 EIP가 `main`이 되는지(ret이 _main을 pop) · 주의: 주소 0 근처는 페이징 후 pg_dir로 덮이므로(head.s:10-12) 중단점은 반드시 페이징 전에 소비하고 삭제(`d`) | —(lab/ 시연 — 원천 강사 시연 B) | — |
| 40 | 캡처 B: CR0 비트0·비트31 | 캡처 | head 진입 직후 `p/x $cr0`(하위 바이트 0x11 또는 0x13/0x15 — FPU 여부, head.s:43-61)와 setup_paging `ret` 직후(0x8000xxxx) 2장 나란히 · CR0 전체 값은 관찰 결과로만 말한다 · CR3=0, ret 후 EIP=main 확인 · 각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · (구 35에서 분할) | boot/head.s:43-65, 198-218, 10-12 | materials/03-boot-init/captures/05-b1-head-entry-cr0.png · 06-b2-after-paging-cr0.png |
| 41 | 시연 C: main → sti → 사용자 모드 → fork | 시연 | `b main` → `c` → `info registers`(cs 0x0008, IF=0) · `b init/main.c:138`(lab 줄 번호 확인) → `c` → `info registers`(cs 0x000f, ss 0x0017, IF=1) · `x/8xw $esp` → ESP는 move_to_user_mode 전후 같은 값(system.h:2,4) · `si`로 `int $0x80` 진입 직후 `info registers`(cs 0x0008, esp가 init_task 페이지 끝 근처 — sched.h:128 esp0) · fork 내부(copy_process)로는 들어가지 않고 `finish`로 빠져나와 eax(부모 0이 아님)만 확인 | —(lab/ 시연 — 원천 강사 시연 C) | — |
| 42 | 캡처 C: 사용자 모드 진입과 int 0x80 | 캡처 | main 진입(cs=0x0008, IF=0) / main.c:138(cs=0x000f, ss=0x0017, IF=1, `x/8xw $esp`) / `int $0x80` 진입 직후(cs=0x0008, esp≈TSS esp0) 3장 · CPL 전환이 CS 하위 2비트로 보임 — ESP가 move_to_user_mode 전후 같고 int 0x80 뒤에만 esp0로 바뀜 · 각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 · (구 36에서 분할) | init/main.c:136-138 · include/asm/system.h:1-14 | materials/03-boot-init/captures/07-c1-main-entry-registers.png · 08-c2-user-mode-registers.png · 09-c3-int80-entry-registers.png |
| 43 | 관찰 vs 추론 | 배경 | 관찰(캡처로 본 것): CR0, CS/SS, EFLAGS, 스택 덤프 · 추론(코드로 추론한 것): BIOS 내부, int 0x13 동작, CPU 내부 캐시, iret의 권한 검사 · lab과 src 차이(심볼·줄 번호) — 캡처 각주 5항목 재확인(lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음 · 캡처 날짜) | —(시연 A·B·C 종합) | 관찰/추론 2열 정리 |
| 44 | 이해 확인 질문 | 확인 | §6의 6문항 게시(원천 전문 계승) · 정답은 클릭 후 표시 · 문항 예: bootsect가 자신을 0x90000으로 옮기는 이유는? / PE 비트를 1로 만드는 명령과 파일:줄은? / move_to_user_mode 뒤 ESP 값은 바뀌는가? | —(§6 문항) | —(클릭 후 정답 표시) |
| 45 | 핵심 질문의 답 | 정답 | 핵심 질문의 답(원문): "PE는 setup.s:192, PG는 head.s:217, IF는 setup.s:109에서 0·main.c:136에서 1, CPL은 system.h:8에서 3" · 네 비트의 전환 횟수: PE 1회, PG 1회, IF 2회, CPL 1회 · 상태 변화 표(36)의 해당 칸을 다시 가리키며 확인 · (구 39 전반 분할) | boot/setup.s:109, 192 · boot/head.s:217 · init/main.c:136 · include/asm/system.h:8 | 상태 변화 표(36)의 해당 칸 하이라이트 |
| 46 | 정리 | 정리 | 세 단계(bootsect → setup → head)의 역할 한 줄씩 · 두 번의 GDT(setup.s 임시 8Mb 표 → head.s 16Mb 표) · 네 비트의 전환 횟수(PE 1회, PG 1회, IF 2회, CPL 1회) · main의 9함수 범주와 채우는 자료구조 · 첫 fork — main이 끝난 뒤의 세계 · (구 39 후반 분할) | boot/bootsect.s · boot/setup.s · boot/head.s · init/main.c | — |
| 47 | 04회차 예고 | 정리 | "write(1, ...) 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?" — 오늘 설치한 게이트 0x80을 통과하는 순간 · 오늘 sched_init이 연 게이트 0x80(system_call.s 진입)과 trap_init의 예외 게이트가 04회차의 무대 · 다음 회차 읽을 소스: kernel/system_call.s, kernel/asm.s, kernel/traps.c, include/unistd.h, include/linux/sys.h | kernel/sched.c:411 · include/unistd.h:133-145 | — |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트 배치: **파트 A «입문·부팅»(01·02·03)** — 오늘 03은 파트 A의 마지막 회차 / 파트 B «실행의 길»(04·05·06) / 파트 C «메모리» 이후 전부.
- 상태: 완료 TEAL = 01 CPU·어셈블리 입문과 부팅부터 셸까지, 02 x86 보호 모드와 소스 읽기 도구 · 오늘 ORANGE + 굵은 테두리 = 03 · 이후 MUTED = 04~15.
- 오늘 한 줄 문구: "부트 섹터 512바이트에서 main()까지 — 네 비트 PE/PG/IF/CPL이 어느 명령에서 바뀌는지 줄 번호로 추적한다"
- 02→03 연결 화살표 문구: "02: 선택자·GDT라는 표의 구조를 익혔다 → 03: 그 표가 만들어지는 때를 본다 — 02의 도구로 부팅 경로 전체를 정밀 추적, setup.s의 임시 표와 head.s의 표, '같은 표를 두 번 만드는' 이유까지"
- 03→04 연결 화살표 문구: "03: main()이 초기화를 마치고 move_to_user_mode로 셸이 살아난다 → 04: 게이트 통과 — main이 끝난 뒤 셸의 write가 도착할 곳 = 오늘 sched_init이 연 게이트 0x80, 인터럽트·시스템 콜"
- 완료·이후 회차 목록: 완료 01–02, 오늘 03, 이후 04–15. 우하단 범례(■ 완료 / ▶ 오늘 / □ 이후) + `Linux 0.11` 라벨.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(TEAL 진하게): boot/bootsect.s, boot/setup.s, boot/head.s, init/main.c. 구조도 골격(00-common §2)에는 boot/ 상자가 없으므로 하드웨어 경계선(IRQ 라벨 줄) 바로 위에 "부팅 경로" 경유지 3개(bootsect.s → setup.s → head.s)를 추가 도형으로 놓고 init/main.c는 공통 상자(main.c·printk)에서 진하게 강조. 이 경유지 표시는 이 회차가 처음이고 07회차(head.s 페이징)·14회차(종합)까지 재사용한다.
- 오늘의 데이터 흐름 화살표(ORANGE, 출발→경유→도착): ROM BIOS(`int 0x19`) → boot/bootsect.s(0x7c00→0x90000) → boot/setup.s(0x90200) → boot/head.s(0x0) → init/main.c `main()` — 끝점을 사용자 공간 상자(init·sh)와 이어 주석 "move_to_user_mode 뒤 셸"(04회차 연결).
- 누적 강조(옅은 TEAL, 01–02 완료 분): 01의 boot/setup.s·boot/head.s·init/main.c(개관) + 02의 include/linux/head.h·include/asm/system.h·include/linux/sched.h(GDT/LDT·TSS 도구). 오늘 파일과 겹치는 boot/head.s·init/main.c는 오늘 강조(진한 TEAL)로 덮어 씀.
- 나머지 상자(진입 kernel/system_call.s·sys_call_table, kernel/, mm/, fs/ 나머지, blk_drv/, chr_drv/)는 MUTED 외곽선 실루엣. 계층 경계(CPL=3/0)·IRQ 하단 라벨(8259A PIC · 8253 타이머(IRQ 0) · 키보드(IRQ 1) · 하드디스크(IRQ 14))은 골격 그대로. 우하단 `Linux 0.11` 라벨.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 02 | 오늘의 길 미니 지도 | 띠 도형 | 10단계 띠, 이 회차는 10단계 전부 강조(상태도 19·25·36, 비교 07·31·32, 시연 37-42, 정답 45) | 공통 프레임(00-common §3) |
| 03 | 15회차 로드맵 | 도형 다이어그램 | 파트 A–G 골격, 완료 01–02·오늘 03(파트 A 마지막)·이후 04–15, 연결 화살표 2개 + 오늘 한 줄 문구 | 로드맵 골격 전 회차 공통 |
| 04 | 커널 구조도 + 부팅 경로 | 도형 다이어그램 | 오늘 파일 4개 TEAL + ROM→bootsect→setup→head.s→main 화살표, 하드웨어 경계 위 '부팅 경로' 경유지 3개 추가 | 구조도 골격 전 회차 공통(경유지는 신규 — 07·14회차 재사용) |
| 05 | 디스크 이미지 배치 그림 | 섹터 도식 | 섹터1 bootsect(510B+0xAA55) / 섹터2-5 setup(SETUPLEN 4) / 섹터6- system | 신규 |
| 06 | 메모리 지도(적재 전후) | 메모리 맵 도식 | 0x7c00 → 0x90000 bootsect, 0x90200 setup, 0x10000 system → 0x00000 이동, 0x90000-0x901FF BIOS 파라미터, 0x9FF00 스택 | 신규(07회차 주소 변환에서 재활용) |
| 07 | 적재 단계 비교 표 | 표 | 3행 × 5축: 적재 주소 · 적재자 · 크기 제한 · 실행 모드 · 어셈블러 | 신규 |
| 08 | 네 비트 참조표 | 표 | PE(CR0.0) · PG(CR0.31) · IF(EFLAGS.9) · CPL(CS.RPL) | 01회차 18장 재사용 |
| 12 | read_it 흐름도 | 흐름 도식 | 64KB 경계 검사 · 트랙 단위 루프, "ES가 0x1000씩 전진"만 강조 | 신규 |
| 14 | BIOS 파라미터 대응 표 | 표 | setup.s 저장 주소 [0]/[2]/[4..12]/[0x80]/[0x90] ↔ main.c:58-60 EXT_MEM_K·DRIVE_INFO·ORIG_ROOT_DEV | 신규 |
| 19 | 상태 변화 표(중간 1) | 표/타임라인 | §4 하단 명세 표의 상단 6행(BIOS~`jmpi 0,8`) | 신규(36 종합 표의 부분) |
| 22 | CR0 비트 분해 그림 | 비트 도식 | `andl $0x80000011`(PG,PE,ET 보존) · `orl $2`(MP), FPU 유무별 관찰 값(0x11/0x13/0x15) | 신규 |
| 23 | main 진입 프레임 그림 | 스택 도식 | `pushl $0`×3, L6, _main → setup_paging의 `ret`가 pop | 신규 |
| 24 | 페이지 테이블·덮어쓰기 그림 | 메모리 도식 | pg_dir~pg3 5페이지, pg_dir[0..3]=pgN+7, 16MB identity, pg_dir이 startup 코드를 덮어씀(head.s:10-12) | 신규(07회차 페이징 기초 자료) |
| 25 | 상태 변화 표(중간 2) | 표/타임라인 | §4 하단 명세 표의 head~main 진입 행 | 19와 동일 형식 |
| 26 | 메모리 경계 3구간 그림 | 메모리 맵 도식 | [0,1MB) 커널 / [1MB,buffer_end) 버퍼 / [main_memory_start,memory_end) 페이지 풀 | 06 그림 변형 |
| 27 | 초기화 9함수 범주표 | 표 | 범주(메모리/게이트/장치/시간/스케줄러/버퍼/블록) × 채우는 자료구조 | 신규 |
| 29 | 예외 번호 표 | 표 | 0-16 게이트 + 17-47 reserved + 45(irq13)·39(parallel) | 신규 |
| 31 | IRQ 0~15 비교 표 | 표 | 16행: 마스크 초기값(setup.s:176-179 전부 1) → 여는 함수·줄, 게이트 번호(0x20+n)·종류, 미사용(5,7,8-12,15) 명시 | 신규 |
| 32 | 게이트 3종 비교 표 | 표 | set_trap_gate / set_intr_gate / set_system_gate × 사용 함수·벡터 | 02회차 게이트 비교 확장 |
| 33 | 버퍼 대칭 연결 그림 | 메모리 도식 | 헤더(앞) · 데이터(buffer_end에서 거꾸로) · 640KB-1MB 구멍 회피(372-373) | 신규(11회차 예고) |
| 34 | move_to_user_mode iret 프레임 그림 | 스택 도식 | push 0x17/esp/eflags/0x0f/1f → iret → ds·es·fs·gs=0x17 | 신규(04회차에서 재사용) |
| 36 | 상태 변화 표·타임라인(종합) | 표+타임라인 | 12행 × 8열 전체 — 아래 상세 명세 | 19·25 합본, 이 강좌 전체에서 가장 중요한 1장 |
| 38·40·42 | 캡처 게시 프레임 | 캡처 레이아웃 | 각주 5항목(lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음 · 캡처 날짜) + 모니터/GDB 형식 표기 | 공통 규칙(00-common §7) |
| 43 | 관찰 vs 추론 2열 | 2열 정리 | 캡처로 본 것(CR0, CS/SS, EFLAGS, 스택 덤프) / 코드에서 추론한 것(BIOS 내부, int 0x13 동작, CPU 내부 캐시, iret 권한 검사) | 신규 |
| 본문 전 | 미니 지도 띠 | 띠 도형 | 10단계, 현재 단계만 ORANGE 점 + 라벨 | 공통 프레임(00-common §3) |

### 슬라이드 36 상태 변화 표(종합) 상세 명세 — 이 회차의 핵심 시각자료

원천 "상태 변화도(필수)" 12행 표를 그대로 게시한다(값·줄 번호 변경 금지).

| 단계 | PE | PG | IF | CPL | CS:EIP 위치 | 스택 | 전환 원인(줄) |
|---|---|---|---|---|---|---|---|
| BIOS → bootsect 진입 | 0 | 0 | 1 | — (real) | 0x07c0:0 | BIOS 것 | int 0x19 |
| bootsect 이동 후 | 0 | 0 | 1 | — | 0x9000:go | 0x9000:0xFF00 | bootsect.s:56,61-62 |
| setup 진입 | 0 | 0 | 1 | — | 0x9020:0 | 유지 | bootsect.s:139 |
| setup `cli` | 0 | 0 | **0** | — | | | setup.s:109 |
| setup `lmsw` | **1** | 0 | 0 | 0 | 0x9020:… | | setup.s:191-192 |
| `jmpi 0,8` | 1 | 0 | 0 | 0 | 0x0008:0 | 아직 없음 | setup.s:193 |
| head `lss _stack_start` | 1 | 0 | 0 | 0 | | 0x10:user_stack 끝 | head.s:23 |
| head setup_paging | 1 | **1** | 0 | 0 | | | head.s:214-217 |
| main() 진입 | 1 | 1 | 0 | 0 | 0x0008:main | L6,0,0,0 위 | head.s:218 `ret` |
| `sti()` | 1 | 1 | **1** | 0 | | | main.c:136 |
| move_to_user_mode | 1 | 1 | 1 | **3** | 0x000f:1f | 0x17:같은 esp | system.h:2-8 |
| fork() 진입 | 1 | 1 | 0(게이트) → 1 | 0 → 3 | | TSS esp0 | main.c:138, unistd.h:137 |

제작 규칙: 12행을 한 장에 — 왼쪽에 단계 타임라인 눈금(ROM → bootsect → setup → head.s → main), 오른쪽에 표. 값이 바뀌는 칸만 TEAL 굵게, 나머지 MUTED(ORANGE는 '지금' 표시 전용이라 이 표에서는 쓰지 않음 — 다만 강의 중 해당 행을 짚을 때만 포인터로 표시). "변경되는 데이터"는 CR0·EFLAGS·CS/SS 선택자·ESP, "유지 조건"은 다음 전환 명령까지, IF는 표시 지점 값(원천 문구 계승). 빈 칸(스택·CS:EIP)은 "이전 행과 동일"을 뜻하는 회색 처리. 행 길이가 12행이므로 글자 크기 하한을 지키고, 19·25에서 이미 본 행임을 활용해 강의 중 재열람 속도를 확보. 이 표의 4개 강조 칸(setup.s:109, setup.s:192, head.s:217, system.h:8 계열)이 슬라이드 45(핵심 질문의 답)에서 다시 하이라이트된다.

## 5. 캡처 목록 (강사 시연)

공통 환경(원천 "강사 시연" 공통문 계승): "lab/(yuan-xy/Linux-0.11 기반 수정본), QEMU i386 TCG, SeaBIOS. 줄 번호·심볼은 lab 기준, 슬라이드 인용은 src/ 원본." QEMU를 `-s -S`(gdbstub, 시작 정지)로 띄우고 GDB `target remote :1234` 또는 QEMU 모니터(`-monitor stdio`/Ctrl-Alt-2)로 관찰. 실행 실패 대비 사전 캡처(모서리에 `기존 기록` 라벨, 00-common §7).

| 시연 | 캡처 파일(materials/03-boot-init/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| 사전(슬라이드 11) | 01-loading-system-message.png | QEMU 부팅 화면(중단 없음) | "Loading system ..." 메시지 원문(bootsect.s:244-247) | 기존 자산 `build/boot.png`(00-common §7) |
| A | 02-a1-reset-registers.png | `-s -S` 정지 직후 모니터 `info registers` | `CR0=00000010`(PE=0), EFL의 IF, 초기 CS | 사전 캡처 3장(기존 기록 라벨) |
| A | 03-a2-bootsect-0x7c00.png | GDB `b *0x7c00` → `c` → 모니터 `info registers` | CS=0x07c0(또는 0000:7c00 — BIOS 구현에 따라 다를 수 있음을 각주), SS:SP, IF=1(cli 전) | 사전 캡처 3장 |
| A | 04-a3-setup-0x90200.png | GDB `b *0x90200` → `c` → 모니터 `info registers` | CS=0x9020, 스택 0x9000:0xFF00(bootsect.s:61-62), IF=1 | 사전 캡처 3장 |
| B | 05-b1-head-entry-cr0.png | GDB `b *0x0`(페이징 전) → `c` → `p/x $cr0` | CR0 비트0=1·비트31=0 — 하위 바이트 0x11 또는 0x13/0x15(FPU 여부, head.s:43-61) | 사전 캡처 |
| B | 06-b2-after-paging-cr0.png | `b *setup_paging`(lab 심볼) → `si` → `ret`(head.s:218) 직전/직후 `p/x $cr0` | CR0=0x8000xxxx(비트31=1), CR3=0, ret 후 EIP=main | 사전 캡처 |
| C | 07-c1-main-entry-registers.png | GDB `b main` → `c` → `info registers` | cs=0x0008, IF=0 | 사전 캡처 3장 |
| C | 08-c2-user-mode-registers.png | `b init/main.c:138`(lab 줄 번호 확인) → `c` → `info registers`, `x/8xw $esp` | cs=0x000f, ss=0x0017, IF=1, ESP는 move_to_user_mode 전후 같은 값(system.h:2,4) | 사전 캡처 3장 |
| C | 09-c3-int80-entry-registers.png | `si`로 `int $0x80` 진입 직후 `info registers` | cs=0x0008, esp가 init_task 페이지 끝 근처(TSS esp0, sched.h:128), eax=fork 반환값은 `finish`로 확인 | 사전 캡처 3장 |

## 6. 이해 확인 질문과 정답 (해당 슬라이드 번호 명시)

슬라이드 44에 6문항 게시(원천 전문 계승 — 00-common §4의 4문항 표준보다 많지만 원천 그대로 둔다), 정답은 클릭 후 표시.

1. **Q.** bootsect가 자신을 0x90000으로 옮기는 이유는? **A.** system을 0x10000부터 적재하고 setup이 다시 0x00000으로 옮길 때 자리를 비우기 위해(bootsect.s:10-11 주석, setup.s:113-126).
2. **Q.** PE 비트를 1로 만드는 명령과 파일:줄은? **A.** `lmsw ax`, setup.s:192. 그 직후 `jmpi 0,8`로 32비트 코드 세그먼트 진입(193).
3. **Q.** GDT를 두 번 만드는 이유는? **A.** setup.s:205-216 임시 표는 0x9xxxx에 있어 버퍼 영역에 덮일 수 있고 8Mb 한계; head.s:234-238이 커널 이미지 안의 16Mb 표로 교체(head.s:96-103 주석, 02회차).
4. **Q.** main()은 call로 호출되는가? **A.** 아니오. head.s:140 `pushl $_main` 뒤 setup_paging의 `ret`(218)이 pop하여 진입. 복귀 주소는 L6 무한루프(142-143).
5. **Q.** IF가 0에서 1이 되는 지점은? **A.** main.c:136 `sti()`. 그 전에는 setup.s:109 `cli` 이후 줄곧 0 (8259 마스크도 0xFF, setup.s:176-179).
6. **Q.** move_to_user_mode 뒤 ESP 값은 바뀌는가? **A.** 아니오. 현재 esp를 push했다가 iret으로 그대로 복원(system.h:2,4). SS만 0x10→0x17. 커널 스택(esp0)은 다음 인터럽트/시스템 콜 때 TSS에서 로드.

## 7. 처음 등장하는 용어 (용어 | 정의 | 첫 등장 슬라이드)

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 부트 섹터 서명 0xAA55 | 섹터 511·512번째 바이트의 매직 넘버. BIOS가 부팅 가능 디스크로 인식하는 표식(bootsect.s:249-253 boot_flag) | 05 |
| `int 0x13`/`int 0x10`/`int 0x15`(BIOS 서비스) | 디스크 읽기 / 화면 문자열 출력 / 확장 메모리 용량 조회 — real mode ROM BIOS가 제공 | 10 |
| INITSEG/SETUPSEG/SYSSEG | bootsect.s:34-43의 적재 주소 상수 — 0x9000 / 0x9020 / 0x1000 | 06 |
| `jmpi` | CS까지 갱신하는 far jump 명령 | 09 |
| A20 | 주소 버스 21번째 선. 켜야 1MB 넘는 주소에 접근 가능 | 17 |
| 8042 | 키보드 컨트롤러. A20 게이트 출력을 가짐 | 17 |
| 8259A(ICW, 마스크) | 프로그래밍 가능 인터럽트 컨트롤러(PIC). ICW 4개로 IRQ→벡터 재배치, 마스크로 개별 차단 | 17 |
| `lmsw` | CR0 하위 16비트를 적재하는 명령. PE 비트를 켠다 | 18 |
| identity mapping | 선형 주소 = 물리 주소가 되도록 페이지 테이블을 채우는 매핑(head.s는 16MB를 이렇게 채움) | 24 |
| pg_dir/pg0~pg3 | 페이지 디렉터리와 페이지 테이블 4장(head.s:114-133, .org 0x1000-0x4000) | 24 |
| CR3 | 페이지 디렉터리 기준 주소를 담는 레지스터. setup_paging이 0을 적재 | 24 |
| `lss` | SS와 ESP를 메모리에서 한 번에 적재하는 명령 | 20 |
| user_stack/stack_start | task 0용 사용자 스택(sched.c)과 그 시작 기술자 | 20 |
| task_union | task_struct와 커널 스택을 1페이지에 겹친 공용체(sched.c:53-72) | 30 |
| mem_map | 물리 페이지당 1바이트짜리 사용중 맵(mm/memory.c) | 27 |
| request[] | 블록 장치 요청 큐. blk_dev_init이 32개 dev=-1로 초기화(ll_rw_blk.c:157-165) | 27 |
| buffer_head | 버퍼 블록 하나의 헤더. buffer_init이 앞쪽에 배열 | 27 |
| LATCH/8253 | 8253 타이머 재적재 값 LATCH = 1193180/HZ(sched.c:46) | 30 |
| `_syscall0` | 인자 없는 시스템 콜 인라인 매크로 — `int $0x80`, eax=__NR_name(unistd.h:133-145) | 35 |
| inline 시스템 콜 | main()이 스택 없이 쓰기 위해 함수 호출 대신 인라인으로 펼친 시스템 콜(main.c:11-22 주석) | 35 |
| COW(예고만) | copy-on-write. 06·08회차 본편 — 오늘은 main.c:11-22 주석(커널 공간 fork는 COW 없음)만 언급 | 35 |

## 8. 흔한 오해 / 말하지 말아야 할 것 (원천 전문 계승)

- "CPL은 real mode에서 0"이라고 말하지 않는다. real mode에는 권한 수준이 없다('—').
- `lmsw` 직후 바로 32비트 코드가 실행된다고 말하지 않는다. `jmpi 0,8`로 CS를 다시 로드해야 한다(1회차 25장).
- setup.s:109 `cli` 전까지 IF=1이지만 "BIOS 인터럽트 핸들러가 setup에서도 계속 동작한다"고 말하지 않는다(cli 뒤 BIOS 사용 불가, setup.s:181-182 주석).
- head.s의 CR0 전체 값을 단정하지 않는다(FPU 유무, head.s:43-61). 관찰 결과로만 말한다.
- "main()이 반환하면 재부팅"이라고 말하지 않는다. L6 무한루프(head.s:142-143)에 머문다.
- 첫 fork의 실패 처리는 없다(main.c:138 주석). 실패 시 어떻게 되는지 추측해서 말하지 않는다.
- move_to_user_mode는 새 프로세스·새 스택을 만들지 않는다. task 0이 자기 user_stack을 CPL3에서 계속 쓴다.
- `chr_dev_init`은 빈 함수(tty_io.c:347-349)임을 숨기지 않는다.
- QEMU 모니터 `info registers`와 GDB `info registers`는 형식이 다르다. 캡처에 어느 쪽인지 표기한다.
- 0.11의 identity mapping을 "현대 커널도 같다"고 말하지 않는다(14회차 비교).

## 9. 120분 운영안 (새 슬라이드 번호)

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 핵심 질문, 오늘의 길, 표준 앞부분 — 로드맵·구조도에서 오늘 위치(파트 A 마지막, 04 직전) |
| 05–08 | 12 | 디스크 이미지 배치, 메모리 지도, 적재 단계 비교, 네 비트 재고 |
| 09–13 | 18 | bootsect.s: 복사·setup 적재·system 적재·jmpi |
| 14–19 | 20 | setup.s: BIOS 파라미터·cli·이동·임시 GDT·A20·8259·lmsw + 상태도(중간 1) |
| 20–25 | 18 | head.s: 세그먼트·스택·IDT/GDT 재구성·페이징·main 호출 프레임 + 상태도(중간 2) |
| 26–33 | 20 | main(): 메모리 경계, 초기화 9함수 범주, mem_init·trap_init, sched_init, IRQ 비교, 게이트 3종, buffer/hd/floppy |
| 34–42 | 17 | sti, move_to_user_mode, 첫 fork, 상태 변화도 종합 + 강사 시연 A/B/C·캡처 |
| 43–47 | 10 | 관찰 vs 추론, 이해 확인, 핵심 질문의 답, 정리·04회차 예고 |

(단계별 분 배분은 원천 운영안 그대로 — 5+12+18+20+18+20+17+10 = 120분.)

## 10. 기존 계획 대비 변경·증가

총 40장 → 47장(+7). 원천 슬라이드 계획 표의 40행은 전부 계승(폐기 없음). 번호 대응:

| 구 번호 | 신규 번호 | 비고 |
|---|---|---|
| 01 | 01 | 표지로 계승(유형 `제목`→`표지`) |
| 02 | 03 | "15회차 지도" 1장 → 로드맵 다이어그램으로 대체·흡수(02 표 구조 → 03 표가 만들어지는 때 → 04 게이트 통과 연결은 §3 화살표 문구로 계승) |
| (신규) | 02, 04 | 표준 앞부분 추가(00-common §2): 핵심 질문+오늘의 길 / 커널 구조도 |
| 03–25 | 05–27 | 순서 그대로 +2 |
| 26 | 28–29 | 분할: mem_init(mm/memory.c:399-411) / trap_init(kernel/traps.c:181-208) — 서로 다른 두 파일·두 자료구조(mem_map vs IDT 게이트) 인용이 한 장에 안 들어가는 밀도(00-common §5 분할 기준) |
| 27–33 | 30–36 | 순서 그대로 +3 |
| 34 | 37–38 | 분할: 시연 절차 / 캡처 게시 — 유형 `시연·캡처`는 00-common §3 어휘 밖이라 시연+캡처 2장으로 |
| 35 | 39–40 | 분할: 시연 B / 캡처 B(같은 사유) |
| 36 | 41–42 | 분할: 시연 C / 캡처 C(같은 사유) |
| 37 | 43 | 순서 계승(+6), 유형 `배경` 유지 |
| 38 | 44 | 순서 계승(+6), 유형 `질문`→`확인`(00-common §3 어휘) |
| 39 | 45–46 | 분할: 핵심 질문의 답(정답 단계 슬라이드) / 정리(세 단계·두 번의 GDT·네 비트의 전환 횟수·main의 9함수·첫 fork) — 답 문장이 미니 지도 '정답' 단계를 홀로 이루도록 |
| 40 | 47 | 순서 계승(+7) |

증가 내역 요약: 표준 앞부분 +2(구 지도 1장이 로드맵+구조도 2장으로), 밀도 분할 +2(구 26·39), 시연·캡처 분할 +3(구 34·35·36). 상태 변화 표(종합)는 이 회차의 핵심 시각자료이므로 분할하지 않고 §4 상세 명세대로 한 장(36)에 완결하며, 대신 중간 상태도 2장(19·25)이 이미 행을 나눠 예고한다.

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- `lab/` 빌드의 심볼명 `_` 접두 여부 확인: `_main` vs `main`, `_stack_start`, `setup_paging`, `_system_call` 등 — 시연 전 GDB `info functions main`, `info functions setup_paging`으로 확인(course-plan 확인 목록 45행 적용). 슬라이드 코드 인용은 `src/` 기준, 캡처 각주는 `lab/` 기준으로 분리해 섞지 않는다.
- QEMU gdbstub에서 `$cr0`, `$cr3` 노출 여부 — 안 되면 `monitor info registers`로 대체(course-plan 확인 목록 46행, 시연 B가 직접 의존).
- 시연 C의 `b init/main.c:138` — lab 빌드에서 해당 줄이 `src/`와 같은지 확인(다르면 lab 줄 번호로 설정, 캡처 각주에 명시).
- setup.s `lmsw` 구간 인용은 `191-193`(186-190은 주석 — 기존 01 자료의 `186-193` 표기 정정, course-plan "원본 소스 사실" 43행). 슬라이드 18·45와 §6 문항 2, 01회차 자료 재사용분(구 25-26장 복습 인용 포함)에 옛 표기가 남지 않도록 최종 확인.
- 사전 캡처 자산 `build/boot.png` 등 존재 여부와 `기존 기록` 라벨(00-common §7) — 시연 A 3장, B 2장, C 3장의 대체 자료.
- 신규 캡처 보관처 `materials/03-boot-init/captures/` 디렉터리 생성(파일명 두 자리 순번-설명.png, §5 목록 9개 파일).
- QEMU 모니터 `info registers`와 GDB `info registers`의 출력 형식 차이 — 캡처 A(모니터)와 캡처 B·C(GDB)에 각각 어느 쪽인지 표기(원천 오해 목록 반영).
- 0x7c00 직후 CS:IP 표기가 BIOS(SeaBIOS) 구현에 따라 다를 수 있음 — 캡처 A 각주 처리(원천 시연 A 주의문 계승).
