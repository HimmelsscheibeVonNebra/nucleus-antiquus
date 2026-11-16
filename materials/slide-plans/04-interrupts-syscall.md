# 04회차 상세 슬라이드 제작 계획 — 인터럽트·예외·시스템 콜

- 기준: materials/course-plan.md `# 04. 인터럽트·예외·시스템 콜` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/04-interrupts-syscall.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 42장 → 이 계획 48장 (+6)
- 로드맵 위치: 파트 B «실행의 길» · 04/15

## 1. 회차 개요

**핵심 질문** (원문 그대로, 슬라이드 01·02·43에 사용)

`write(1, ...)` 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?

**학습 목표** (원문 그대로)

1. IDT 항목(게이트)이 "번호 → 커널 진입점 + 권한 조건"을 저장하는 표임을 설명하고, `set_intr_gate`/`set_trap_gate`/`set_system_gate`의 차이를 비트(type, DPL) 수준에서 말한다.
2. `int $0x80`이 CPU에 일으키는 상태 변화(CPL 3→0, SS:ESP 교체, 프레임 push)를 스택 그림으로 그린다.
3. `lib/write.c` → `_syscall3` → `_system_call` → `sys_call_table[4]` → `sys_write` → `ret_from_sys_call` → `iret`까지 호출 순서를 소스 줄 번호와 함께 추적한다.
4. 하드웨어 인터럽트(타이머·키보드), CPU 예외(0~16), 소프트웨어 인터럽트(0x80)가 **같은 IDT 메커니즘**을 쓰되 진입 코드(`asm.s`/`system_call.s`)와 복귀 경로가 다른 이유를 설명한다.
5. GDB에서 `system_call`에 멈춰 `int 0x80`이 쌓은 프레임(EIP/CS/EFLAGS/OLDESP/OLDSS)을 직접 읽는다.

**읽을 소스 범위** (파일:줄, 원본 src 기준 — 원천 절에서 그대로 계승)

| 파일 | 줄 | 내용 |
|---|---|---|
| `lib/write.c` | 7–10 | `#define __LIBRARY__` 후 `_syscall3(int,write,int,fd,const char *,buf,off_t,count)` 한 줄 |
| `include/unistd.h` | 60–64 | `__NR_setup`=0 … `__NR_write`=4 |
| `include/unistd.h` | 133–144 | `_syscall0` (`int $0x80`, `"=a"(__res)`, `"0"(__NR_##name)`) |
| `include/unistd.h` | 172–183 | `_syscall3` (`"b"`,`"c"`,`"d"` 로 인자 전달, 음수면 `errno=-__res; return -1`) |
| `include/linux/sys.h` | 74–86 | `fn_ptr sys_call_table[]` — 인덱스 4가 `sys_write` |
| `include/asm/system.h` | 22–31 | `_set_gate(gate_addr,type,dpl,addr)` — `0x8000+(dpl<<13)+(type<<8)`, 선택자 `0x0008` |
| `include/asm/system.h` | 33–40 | `set_intr_gate`(type 14, DPL 0) / `set_trap_gate`(15, 0) / `set_system_gate`(15, 3) |
| `include/asm/system.h` | 1–14 | `move_to_user_mode()` — iret로 처음 CPL 3로 내려가는 프레임 (복습용) |
| `boot/head.s` | 78–93 | `setup_idt` — 256개 항목 전부 `ignore_int`로 채우고 `lidt` |
| `boot/head.s` | 150–170 | `ignore_int` — "Unknown interrupt" 출력 후 iret |
| `boot/head.s` | 222–224, 232 | `idt_descr`, `_idt: .fill 256,8,0` |
| `kernel/traps.c` | 181–208 | `trap_init` — 0~16번 예외 게이트, 17~47 `reserved`, 45번 `irq13`, 39번 `parallel_interrupt` |
| `kernel/traps.c` | 63–85 | `die()` (68–70 printk) — EIP/EFLAGS/ESP 출력 후 `do_exit(11)` |
| `kernel/traps.c` | 87–100 | `do_double_fault`/`do_general_protection`/`do_divide_error` |
| `kernel/asm.s` | 19–51 | `_divide_error` + `no_error_code` 공통 경로(오류 코드 없는 예외) |
| `kernel/asm.s` | 97–129 | `_double_fault` + `error_code` 공통 경로(오류 코드 있는 예외) |
| `kernel/asm.s` | 131–145 | `invalid_TSS`/`segment_not_present`/`stack_segment`/`general_protection` 진입 |
| `mm/page.s` | 14–40 | `_page_fault` — CR2 읽어 `do_no_page`/`do_wp_page` 분기 (07·08회차 예고) |
| `kernel/sched.c` | 385–412 | `sched_init` — 409 `set_intr_gate(0x20,&timer_interrupt)`, 410 PIC 마스크 해제, 411 `set_system_gate(0x80,&system_call)` |
| `kernel/system_call.s` | 17–31 | `ret_from_system_call` 시점 스택 배치 주석 |
| `kernel/system_call.s` | 35–53 | `EAX`…`OLDSS` 오프셋, `state`/`counter`/`signal`/`blocked` task_struct 오프셋 |
| `kernel/system_call.s` | 61 | `nr_system_calls = 72` |
| `kernel/system_call.s` | 72–78 | `bad_sys_call`(eax=-1, iret), `reschedule`(ret_from_sys_call push 후 `jmp _schedule`) |
| `kernel/system_call.s` | 80–100 | `_system_call` — 범위 검사, ds/es/fs 설정, `call _sys_call_table(,%eax,4)`, state/counter 검사 |
| `kernel/system_call.s` | 101–128 | `ret_from_sys_call` — task[0]·CPL·SS 검사, 시그널 처리, pop 7개 후 `iret` |
| `kernel/system_call.s` | 176–197 | `_timer_interrupt` — `incl _jiffies`, EOI, `call _do_timer`, `jmp ret_from_sys_call` |
| `fs/read_write.c` | 83–103 | `sys_write` — fd 검사, pipe/char/blk/reg 분기 |
| `fs/char_dev.c` | 95 | `rw_char` 선언 지점(13회차에서 상세) |
| `init/main.c` | 137, 151–160 | `move_to_user_mode()`; `printf`가 `write(1,printbuf,…)` 호출 |
| `kernel/chr_drv/console.c` | 683–684 | 참고: 키보드 IRQ1 = `set_trap_gate(0x21,&keyboard_interrupt)` + PIC 마스크 |
| `kernel/chr_drv/serial.c` | 39–43 | 참고: 시리얼 IRQ3/4 = `set_intr_gate(0x24/0x23,…)` |
| `kernel/blk_drv/hd.c` | 346–348 | 참고: 하드디스크 IRQ14 = `set_intr_gate(0x2E,&hd_interrupt)` |
| `kernel/blk_drv/floppy.c` | 460–461 | 참고: 플로피 IRQ6 = `set_trap_gate(0x26,&floppy_interrupt)` |
| `kernel/signal.c` | 82 | `do_signal` 시그니처(10회차에서 상세; `ret_from_sys_call`에서 호출됨만 언급) |

**상태 변화도 / 모드·선택지 비교 범위** (원문 계승, 슬라이드 번호는 이 계획 기준)

- **상태 변화도 (필수 1장, 원천 슬라이드 18 → 이 계획 슬라이드 21)**: 한 태스크의 "실행 문맥" 상태 — `사용자(CPL3, SS=0x17)` → `[int 0x80]` → `커널 진입 프레임만 있음(CPL0, SS=0x10, ESP=tss.esp0 기준)` → `[push ds/es/fs/edx/ecx/ebx]` → `커널 C 호출 가능` → `[call sys_write]` → `C 함수 실행` → `[ret; pushl %eax]` → `ret_from_sys_call` → `[pop 7개 + iret]` → `사용자(CPL3)`. 각 화살표에 변하는 데이터(ESP, CS, DS, EAX)와 유지 조건(IF, 커널 스택 위치)을 적는다.
- **모드·선택지 비교 (필수 1장, 원천 슬라이드 11 → 이 계획 슬라이드 13)**: 범위 = "IDT에 넣을 수 있는 게이트 종류"로 한정. 선택지: 인터럽트 게이트(type 14) / 트랩 게이트(type 15) / 태스크 게이트(type 5). 비교 축: 0.11 사용 여부, IF 자동 클리어 여부, DPL, 사용하는 매크로, 관련 소스. 태스크 게이트는 "0.11은 사용 안 함"으로 명시.
- **보조 비교 (원천 슬라이드 12 → 이 계획 슬라이드 14)**: 범위 = "게이트 DPL" — DPL 0(사용자 `int n` 금지, #GP) vs DPL 3(허용). `set_system_gate`를 쓴 번호는 3,4,5,0x80 네 개뿐임을 `trap_init`/`sched_init`에서 확인.
- **보조 비교 (원천 슬라이드 24 → 이 계획 슬라이드 27)**: 범위 = "IDT 진입 후 레지스터 저장 코드" — `system_call.s`(syscall·timer) / `asm.s no_error_code` / `asm.s error_code` / `page.s` 네 경로의 push 목록·호출 규약·복귀 경로. CPU 모드·권한 비교와 섞지 않는다.

## 2. 전체 슬라이드 목록

공통 프레임(00-common §1·§3): 전 슬라이드 푸터 `Linux 0.11 커널 강좌 · 04/15 · 04-interrupts-syscall` + `MM / 48`, 본문(05번부터) 상단 10단계 미니 지도, 코드 캡션은 `src/` 기준.

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 04. 인터럽트·예외·시스템 콜 | 표지 | 대제목 `04. 인터럽트·예외·시스템 콜`, 부제 = 핵심 질문 "`write(1, ...)` 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?" · 우상단 `Linux 0.11` 배지 + `1991`(ORANGE 채움·PAPER 글자), 부제 아래 `Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)` · 회차 정보 `04/15 · 파트 B «실행의 길»` · 오늘 끝에 GDB 화면으로 답한다고 예고(구 01 계승) | —(표지, 인용 없음) | 배지(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 1문장 큰 글씨(원문 그대로) · 오늘의 길 = 10단계 미니 지도를 본문 크기로, 오늘 실제 지나는 단계만 강조 — 이 회차는 질문/지도/배경/코드/상태도/비교/시연/정답/확인/정리 10단계 전부를 밟는 회차임을 표시 · 없는 단계 없음(상태도 21, 비교 13·14·27, 정답 43, 확인 47) · 예고: 오늘 끝에 GDB 화면(캡처 A-1·A-2·B)으로 답 확인 | —(핵심 질문 원문) | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 15회차 7파트 타임라인 골격에서 파트 B «실행의 길» 묶음 표시 · 완료 TEAL: 01 CPU·어셈블리, 02 보호 모드, 03 부팅·초기화 · 오늘 ORANGE + 굵은 테두리: 04 · 이후 MUTED: 05–15 · 오늘 한 줄 문구 + 앞→오늘·오늘→뒤 연결 화살표 2개(문구는 §3 명세) · 구 02 "15회차 지도" 내용(03 초기화 뒤·05 스케줄링 앞 연결) 흡수 | —(로드맵 골격: 00-common §2) | 로드맵 도형(§3 명세) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | Linux 0.11 전체 구조도에서 오늘 파일 5개 TEAL 강조: kernel/system_call.s, kernel/asm.s, kernel/traps.c, include/unistd.h, include/linux/sys.h · 오늘의 데이터 흐름 화살표 ORANGE: 사용자 write() → int 0x80 → sys_call_table → sys_write → iret · 누적 강조(옅은 TEAL) 01–03 영역: boot/, init/main.c · 나머지 상자는 MUTED 실루엣으로 남김(가리지 않음), 계층 경계 CPL=3/CPL=0·IRQ 라벨 유지 | —(구조도 골격: 00-common §2) | 구조도 도형(§3 명세) |
| 05 | 왜 `call sys_write`가 안 되는가 | 배경 | 사용자 CS=0x0f(LDT, CPL3)에서 커널 코드 세그먼트 0x08(DPL0)로의 far call은 #GP · CPL이 낮은 쪽으로 가려면 CPU가 허락한 통로(게이트)만 가능 · 1~2회차의 CPL/DPL 표 재사용 · 오늘의 질문 재정의: 그 통로가 곧 IDT 게이트다 | include/asm/system.h:1–14 · init/main.c:137 | CPL/DPL 표(01·02회차 재사용) |
| 06 | 세 가지 진입 원인 | 배경 | 하드웨어 인터럽트(장치·PIC, 번호 0x20~0x2F) · CPU 예외(0~16, 명령 실행 중 발생) · 소프트웨어 인터럽트(`int n` 명령, 0x80) · 공통점: 번호 하나로 IDT를 찾는다 · 차이: 발생 시점과 오류 코드 유무 | kernel/traps.c:181–208 · kernel/sched.c:385–412 · include/unistd.h:133–144 | 3열 구분표 |
| 07 | IDT 한 항목 = 8바이트 게이트 | 코드 | 2회차 IDT 복습 · `boot/head.s:232` `_idt: .fill 256,8,0`, `idt_descr`(222–224), `setup_idt`(78–93)가 256개 전부 `ignore_int`로 채움 · 그림: 선택자 0x0008 + 오프셋 + P/DPL/type 비트 · 캡션 src/boot/head.s:78–93 | boot/head.s:78–93 · boot/head.s:222–224, 232 | 게이트 8바이트 필드 그림 |
| 08 | `ignore_int`: 기본 핸들러 | 코드 | `boot/head.s:150–170` 코드 · "Unknown interrupt" 출력 후 iret · 수업 시작 시 모든 번호가 여기로 간다는 점 · 이후 `trap_init`/`sched_init`/장치 init이 덮어씀 · 캡션 src/boot/head.s:150–170 | boot/head.s:150–170 | — |
| 09 | 누가 언제 IDT를 덮어쓰는가 | 코드 | `init/main.c:127` `trap_init()`, `:132` `sched_init()` · `tty_init`→`con_init`(`console.c:683`), `rs_init`(`serial.c:39–40`), `hd_init`(`hd.c:346`), `floppy_init`(`floppy.c:460`) · 표: 번호 / 매크로 / 핸들러 / 파일:줄 · 캡션 src/init/main.c:127,132 | init/main.c:127, 132 · kernel/chr_drv/console.c:683–684 · kernel/chr_drv/serial.c:39–43 · kernel/blk_drv/hd.c:346–348 · kernel/blk_drv/floppy.c:460–461 | IDT 덮어쓰기 주체 표 |
| 10 | `_set_gate` 매크로 해부 | 코드 | `include/asm/system.h:22–31` · `"a"(0x00080000)` + `movw %dx,%ax` → 하위 4바이트 = 선택자 0x0008 ‖ 오프셋 하위 16비트 · 상위 4바이트 = 오프셋 상위 16비트 ‖ `0x8000+(dpl<<13)+(type<<8)` · 비트 그림으로 P=1, DPL, type 위치 표시 · 캡션 src/include/asm/system.h:22–31 | include/asm/system.h:22–31 | 8바이트 구성 비트 그림 |
| 11 | 세 매크로의 차이는 두 숫자뿐 | 코드 | `system.h:33–40` · `set_intr_gate` = (14,0), `set_trap_gate` = (15,0), `set_system_gate` = (15,3) · type 14 vs 15 = 진입 시 IF 클리어 여부 · DPL 0 vs 3 = 사용자 `int n` 허용 여부 · 캡션 src/include/asm/system.h:33–40 | include/asm/system.h:33–40 | 매크로 3종 비교 표 |
| 12 | 게이트 설명자 비트 배치 | 코드 | 상위 워드 `0x8E00`(intr, DPL0) / `0x8F00`(trap, DPL0) / `0xEF00`(trap, DPL3) 계산 과정 · `head.s:82`의 `$0x8E00`과 `_set_gate`의 식이 같은 값을 만든다는 것을 확인 · 캡션 src/boot/head.s:82 | boot/head.s:82 · include/asm/system.h:22–31 | 상위 워드 값 계산 표 |
| 13 | 비교: IDT 게이트 종류 | 비교 | 범위 = IDT에 넣을 수 있는 게이트 · 인터럽트 게이트(type 14) — 0.11 사용(0x20 타이머, 0x23/0x24 시리얼, 0x2E hd), 진입 시 IF=0 · 트랩 게이트(type 15) — 사용(예외 0~16, 0x21 키보드, 0x26 플로피, 0x80), IF 유지 · 태스크 게이트(type 5) — 0.11 미사용, TSS 전환 · 각 행에 관련 소스 줄 | kernel/sched.c:409, 411 · kernel/chr_drv/serial.c:39–43 · kernel/blk_drv/hd.c:346–348 · kernel/traps.c:181–208 · kernel/chr_drv/console.c:683–684 · kernel/blk_drv/floppy.c:460–461 | 게이트 종류 비교 표 |
| 14 | 비교: 게이트 DPL 0 vs 3 | 비교 | 범위 = 게이트 DPL · DPL0: 사용자 모드 `int n` 실행 시 #GP(13번) — 장치 IRQ·대부분 예외 · DPL3: 허용 — `trap_init:188–190` int3/overflow/bounds, `sched_init:411` 0x80 · `set_system_gate`을 쓴 번호는 3,4,5,0x80 네 개뿐임을 `trap_init`/`sched_init`에서 확인 · 하드웨어 발생 인터럽트는 DPL 검사를 하지 않는다는 점 명시 | kernel/traps.c:181–208(188–190) · kernel/sched.c:411 | DPL 비교 표 |
| 15 | 사용자 쪽 출발점: `lib/write.c` | 코드 | `lib/write.c:7–10` 전체(4줄) · `#define __LIBRARY__`가 `unistd.h:58`의 `#ifdef __LIBRARY__` 블록을 연다 · `write`라는 함수는 매크로 전개 결과임을 보임 · 캡션 src/lib/write.c:7–10 | lib/write.c:7–10 · include/unistd.h:58 | — |
| 16 | `_syscall3` 전개: 손으로 쓴 코드 | 코드 | `include/unistd.h:172–183` · 전개 결과를 손으로 쓴 C 코드: `int write(int fd,const char *buf,off_t count){ long __res; asm("int $0x80":"=a"(__res):"0"(4),"b"(fd),"c"(buf),"d"(count)); ... }` · 전개 결과와 원 매크로를 나란히 · 캡션 src/include/unistd.h:172–183 · (구 14 전반 분할) | include/unistd.h:172–183 | — |
| 17 | `_syscall3` 전개: 레지스터 약속 | 코드 | 레지스터 약속 표: EAX=번호, EBX/ECX/EDX=인자 1/2/3 · `"=a"(__res)`가 반환값을 받고 음수면 `errno=-__res; return -1` · `_syscall0`(`unistd.h:133–144`)의 `"int $0x80"`, `"=a"(__res)`, `"0"(__NR_##name)` 패턴과 같은 구조 확인 · (구 14 후반 분할) | include/unistd.h:172–183 · include/unistd.h:133–144 | 레지스터 약속 표 |
| 18 | `__NR_write = 4` 와 표의 4번 칸 | 코드 | `unistd.h:60–64`와 `sys.h:74–75`를 나란히 · `__NR_setup`=0 … `__NR_write`=4, `sys_call_table[4] == sys_write` · `system_call.s:61` `nr_system_calls = 72` = 표 길이(0~71, 마지막 `sys_setregid`=71, `unistd.h:131`) · 캡션 src/include/unistd.h:60–64 · src/include/linux/sys.h:74–75 | include/unistd.h:60–64 · include/linux/sys.h:74–86 · kernel/system_call.s:61 · include/unistd.h:131 | unistd.h·sys.h 나란히 보기 |
| 19 | `int $0x80` 실행 순간 CPU가 하는 일 | 배경 | 그림: IDT[0x80] 읽기 → DPL3 ≥ CPL3 통과 → TSS에서 ss0/esp0 로드(05회차의 `tss.esp0`) → 커널 스택에 SS, ESP, EFLAGS, CS, EIP 5개 push → CS=0x08, EIP=`_system_call` · 트랩 게이트이므로 IF 유지 · 개념도(코드 인용 아님) | kernel/system_call.s:17–31 · kernel/sched.c:411 | 진입 순서 그림 |
| 20 | 프레임 그림: `system_call.s:17–31` | 코드 | 주석에 적힌 12개 슬롯을 그대로 그림으로 · 위 5개(EIP~OLDSS)는 CPU가, 아래 7개(DS~EAX)는 코드가 push · `OLDESP = 0x28`, `OLDSS = 0x2C` 오프셋 정의(`:35–46`) · GDB 시연에서 이 그림과 `x/12xw $esp`를 대조할 것 예고 · 캡션 src/kernel/system_call.s:17–31 | kernel/system_call.s:17–31, 35–53 | 12슬롯 프레임 그림 |
| 21 | 상태 변화도: 한 번의 시스템 콜 | 상태도 | 상태: 사용자 실행(CPL3, SS 0x17) → 커널 진입 프레임(CPL0, SS 0x10, 레지스터 미저장) → 커널 C 호출 가능(DS/ES=0x10, FS=0x17) → `sys_write` 실행 중 → 반환값 스택 저장(`pushl %eax`) → `ret_from_sys_call`(시그널 검사) → 사용자 실행 · 각 전환의 원인 명령, 변경 데이터(ESP/CS/DS/EAX), 유지 조건(IF, 커널 스택 = task 페이지 끝) | kernel/system_call.s:80–128 · fs/read_write.c:83–103 | 상태 변화도(필수 1장) |
| 22 | `_system_call` 한 줄씩 (1) | 코드 | `system_call.s:80–94` · 81–82 범위 검사→`bad_sys_call`(72–74, eax=-1) · 83–88 push ds/es/fs/edx/ecx/ebx — "ebx,ecx,edx를 push하는 것이 C 인자 전달" · 89–93 ds/es=0x10, fs=0x17 · 94 `call _sys_call_table(,%eax,4)` = `sys_call_table[eax]()` · 캡션 src/kernel/system_call.s:80–94 | kernel/system_call.s:80–94, 72–78 | — |
| 23 | `sys_write`에 도착 | 코드 | `fs/read_write.c:83–103` · 인자 `(fd,buf,count)` = 스택의 ebx/ecx/edx · fd 1 → `current->filp[1]` → 문자 장치면 `rw_char(WRITE,…)`(`:95–96`) → 13회차 · 반환값은 EAX로 돌아옴 · 오늘은 분기 조건만, 내부는 보지 않음 · 캡션 src/fs/read_write.c:83–103 | fs/read_write.c:83–103 · fs/char_dev.c:95 | — |
| 24 | `_system_call` 한 줄씩 (2) | 코드 | `system_call.s:95–100` · 95 `pushl %eax`(반환값 저장, 프레임 슬롯 EAX) · 96–100 `current->state != 0` 또는 `counter == 0`이면 `reschedule`(76–78: ret_from_sys_call을 push하고 `jmp _schedule`) → 05회차 연결 · 캡션 src/kernel/system_call.s:95–100 | kernel/system_call.s:95–100, 72–78 | — |
| 25 | `ret_from_sys_call` | 코드 | `system_call.s:101–128` · 102–104 task[0]이면 건너뜀 · 105–108 CS=0x0f, OLDSS=0x17 — "사용자에서 왔을 때만 시그널 처리" · 109–120 `signal & ~blocked` 최하위 비트 → `do_signal`(10회차) · 121–128 pop 7개 → `iret` · 캡션 src/kernel/system_call.s:101–128 | kernel/system_call.s:101–128 · kernel/signal.c:82 | — |
| 26 | `iret`가 되돌리는 것 | 코드 | iret는 EIP/CS/EFLAGS를 pop하고 CPL이 바뀌면 ESP/SS도 pop · 범용 레지스터는 되돌리지 않음 → 그래서 121–127의 pop이 먼저 · EAX만은 `sys_write` 반환값으로 바뀐 채 돌아감 → `_syscall3`의 `__res` · 캡션 src/kernel/system_call.s:121–128 | kernel/system_call.s:121–128 · include/unistd.h:172–183 | — |
| 27 | 비교: 진입 후 레지스터 저장 코드 4종 | 비교 | 범위 = IDT 진입 직후 저장 코드 · `system_call.s _system_call`(ds/es/fs/edx/ecx/ebx, eax는 반환값 슬롯) / `_timer_interrupt`(176–183, eax까지 push) · `asm.s no_error_code`(19–39, 전 레지스터 + 가짜 오류코드 0) / `asm.s error_code`(97–117, CPU가 push한 오류코드를 eax로 교환) · `page.s`(14–27, CR2 push) · 복귀: syscall·timer는 `ret_from_sys_call`, 나머지는 자체 pop+iret | kernel/system_call.s:80–94, 176–183 · kernel/asm.s:19–39, 97–117 · mm/page.s:14–27 | 저장 코드 4종 비교 표 |
| 28 | `trap_init`: 예외 0~16 | 코드 | `kernel/traps.c:181–208` · 표: 0 divide_error, 3/4/5 system_gate, 7 device_not_available(system_call.s:148), 13 general_protection, 14 page_fault(page.s), 16 coprocessor_error · 17~47을 `reserved`로 채운 뒤 45(irq13), 39(parallel)만 덮음(202–207) · 캡션 src/kernel/traps.c:181–208 | kernel/traps.c:181–208 · kernel/system_call.s:148 · mm/page.s:14–40 | 예외 번호 표 |
| 29 | 오류 코드 없는 예외: `no_error_code` 경로 | 코드 | `asm.s:19–51` `_divide_error` 진입 · `pushl $0`으로 가짜 오류 코드를 push해 프레임 모양을 맞춤 · 공통 경로에서 C 핸들러 호출 · 캡션 src/kernel/asm.s:19–51 · (구 26 전반 분할) | kernel/asm.s:19–51 | — |
| 30 | 오류 코드 있는 예외: `error_code` 경로 | 코드 | `asm.s:97–129` `_double_fault` 진입 · `xchgl %eax,4(%esp)` — CPU가 push한 오류코드를 eax로 교환 · 29·30 두 경로 모두 `lea 44(%esp)`로 프레임 포인터를 두 번째 인자로 → `do_xxx(long esp, long error_code)`(traps.c:87–100) · 8/10/11/12/13/14가 오류 코드 있는 쪽 · 캡션 src/kernel/asm.s:97–129 | kernel/asm.s:97–129 · kernel/traps.c:87–100 | — |
| 31 | `die()`: 예외의 끝 | 코드 | `traps.c:63–85` · esp[0..4] = EIP, CS, EFLAGS, ESP, SS 출력(68–70 printk) → 20장 프레임 그림의 상위 5슬롯과 같은 배치 · 마지막 `do_exit(11)` · 시연 C에서 실제 출력과 대조 · 캡션 src/kernel/traps.c:63–85 | kernel/traps.c:63–85 | — |
| 32 | 하드웨어 인터럽트: 타이머와 PIC 설정 | 코드 | `sched.c:406–410` 8253 설정(LATCH=`1193180/HZ`, sched.c:46) · `set_intr_gate(0x20,…)`(409) · `outb(inb_p(0x21)&~0x01,0x21)` = IRQ0 마스크 해제(410) · 캡션 src/kernel/sched.c:406–410 · (구 28 전반 분할) | kernel/sched.c:385–412, 406–410 · kernel/sched.c:46 | — |
| 33 | `_timer_interrupt` 한 줄씩 | 코드 | `system_call.s:176–197` · 189 `incl _jiffies` · 190–191 EOI(0x20→포트 0x20) · 192–194 CS 하위 2비트 = CPL을 `do_timer` 인자로 · 상세는 05회차 · 캡션 src/kernel/system_call.s:176–197 | kernel/system_call.s:176–197 | — |
| 34 | 시연 환경 | 시연 | `lab/` QEMU i386 + GDB 원격(`target remote`) · QEMU를 `-s -S`(gdbstub, 시작 정지)로 띄우고 `target remote :1234`, 커널 심볼 로드 후 부팅이 셸까지 간 뒤 중단점 설정 · `src/` 줄 번호와 `lab/` 빌드 심볼은 별개임을 각주(심볼 접두 `_` 유무는 lab 빌드 기준) · 시연 전 `info functions system_call`으로 확인 · 실패 시 사전 캡처 사용 | —(lab/ 환경 규칙) | — |
| 35 | 시연 A: `break system_call` | 시연 | 셸에서 `echo hi` 실행 → `system_call`에서 정지 · `p/x $eax`(=4 기대), `p/x $ebx`(=1), `p/x $cs`(=0x8), `p/x $ss`(=0x10) · 셸의 내부 동작에 따라 `write` 이전에 다른 시스템 콜이 먼저 걸릴 수 있음 → `cond`로 `$eax == 4` 조건 부여 | kernel/system_call.s:80–94 | — |
| 36 | 캡처 A-1: 진입 직후 레지스터 | 캡처 | GDB 로그 캡처 · 관찰: EAX=4=`__NR_write`, ECX=버퍼 주소(사용자 선형 주소), EDX=길이 · 각주: lab 빌드, 수정 없음, QEMU `-s -S`, 캡처 날짜 | include/unistd.h:172–183 · kernel/system_call.s:80–94 | materials/04-interrupts-syscall/captures/01-a1-entry-registers.png |
| 37 | 캡처 A-2: `x/5xw $esp` | 캡처 | 진입 직후 커널 스택 5워드 = EIP, CS(0x0f), EFLAGS, OLDESP, OLDSS(0x17) · 20장 그림과 나란히 · "CS 하위 2비트 = 3 = 왔던 곳의 CPL"을 강조 · 각주: lab 빌드·수정 여부·캡처 날짜 | kernel/system_call.s:17–31 | materials/04-interrupts-syscall/captures/02-a2-stack-5words.png + 20장 그림 병치 |
| 38 | 시연 B: `sys_write` 반환과 `ret_from_sys_call` | 시연 | `break sys_write` → `finish` → `p $eax`(쓴 바이트 수 기대) · `break ret_from_sys_call` → `x/12xw $esp`로 12슬롯 전체 확인, EAX 슬롯 = 반환값 · `stepi`로 `iret` 통과 직후 `p/x $cs`=0x0f, `p/x $ss`=0x17 | fs/read_write.c:83–103 · kernel/system_call.s:95, 101–128 | — |
| 39 | 캡처 B: iret 전후 | 캡처 | iret 직전/직후 레지스터 캡처 두 장 나란히 · 변한 것: CS, SS, ESP, EIP · 안 변한 것: EAX(반환값) · 각주: 환경·수정 여부·캡처 날짜 | kernel/system_call.s:121–128 | materials/04-interrupts-syscall/captures/03-b1-before-iret.png · materials/04-interrupts-syscall/captures/04-b2-after-iret.png |
| 40 | 시연 C: 예외 — 0으로 나누기 | 시연 | 사용자 프로그램(lab에 미리 넣은 `div0` 또는 셸에서 재현 가능한 것)으로 #DE 유발 · `break do_divide_error` → `p/x *(long*)esp@5`로 EIP/CS/EFLAGS/ESP/SS, 콘솔의 `die()` 출력과 대조 · 테스트 프로그램이 lab에 없으면 시연 C를 생략하고 캡처만 설명 | kernel/asm.s:19–51 · kernel/traps.c:87–100 | — |
| 41 | 캡처 C: `divide error: 0000` | 캡처 | QEMU 콘솔 캡처(`traps.c:68–70` 출력 형식) · EIP의 세그먼트 0x000f, SS 0x0017 확인 · 각주: 테스트 프로그램은 lab 추가분(원본 src에 없음) | kernel/traps.c:63–85(68–70) | materials/04-interrupts-syscall/captures/05-c-divide-error-console.png |
| 42 | 관찰 vs 추론: 오늘 시연의 경계 | 시연 | 관찰(lab/ 캡처): 진입 직후 EAX/EBX/CS/SS, 스택 5·12워드, iret 전후 CS/SS/ESP, `divide error: 0000` 콘솔 · 추론(src/ 코드 읽기): TSS에서 ss0/esp0 로드 순서, 트랩 게이트라 IF 유지, `reschedule` 경로(96–100) · 캡처 각주 5항목 재확인: lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜 · (신규 — 00-common §7 "시연 뒤 관찰 vs 추론 구분 슬라이드 1장 유지") | —(시연 A·B·C 종합) | 관찰/추론 2열 정리 |
| 43 | 질문의 답: `write(1,…)`의 왕복 | 정답 | 한 장 흐름도: `write()`(lib) → `int $0x80` → IDT[0x80] → `_system_call` → `sys_call_table[4]` → `sys_write` → `pushl %eax` → `ret_from_sys_call` → `iret` → `__res` · 각 화살표에 파일:줄 | lib/write.c:7–10 · include/unistd.h:172–183 · kernel/sched.c:411 · kernel/system_call.s:80–128 · include/linux/sys.h:74–86 · fs/read_write.c:83–103 | 왕복 흐름도 |
| 44 | 같은 메커니즘, 다른 세 입구 | 정리 | 소프트웨어 `int 0x80`(사용자가 원함, DPL3) / 예외(CPU가 강제, 오류 코드 가능, `die`) / 하드웨어 IRQ(장치가 원함, PIC EOI 필요, 사용자 복귀 시 스케줄 가능) · 오늘 본 소스를 세 열로 정리 | kernel/system_call.s:80–100, 176–197 · kernel/asm.s:19–51, 97–129 · kernel/traps.c:63–85 · kernel/sched.c:385–412 | 세 입구 3열 정리 표 |
| 45 | 흔한 오해 바로잡기 | 정리 | "`int 0x80`이 함수 호출이다"(아니다: 스택·CPL·세그먼트가 바뀐다) · "iret가 모든 레지스터를 복원한다"(5개만) · "트랩 게이트는 인터럽트 끔"(반대) · "예외=에러"(page_fault는 정상 동작의 일부, 07·08회차) | include/asm/system.h:33–40 · kernel/system_call.s:121–128 · mm/page.s:14–40 | — |
| 46 | 현대 커널과의 연결(1장만) | 배경 | x86-64 Linux는 `syscall` 명령과 MSR로 진입하지만 "번호→표→함수, 반환값→레지스터" 구조는 동일 · 비교는 14회차에서 | —(현대 커널 참고, src/ 인용 없음) | — |
| 47 | 이해 확인 질문 | 확인 | §6의 4문항 표시 · 정답은 클릭 후 표시 · 문항 1 `set_trap_gate(0x80,…)`로 바꾸면? · 문항 2 push 순서가 ebx,ecx,edx인 이유? · 문항 3 iret 뒤 사용자 EAX에는? · 문항 4 타이머 0x20과 키보드 0x21의 진입 직후 IF 값? | kernel/sched.c:409, 411 · include/asm/system.h:33–40 · kernel/system_call.s:83–95, 121–128 · kernel/chr_drv/console.c:683–684 | —(클릭 후 정답 표시) |
| 48 | 정리와 다음 회차 | 정리 | 오늘 정리 4줄(안): 게이트 = 번호→진입점+권한 조건(type·DPL) / `int $0x80` → 5 push → `_system_call` → `sys_call_table[4]` → `sys_write` / `ret_from_sys_call` → `iret` 복귀, EAX=반환값 / 세 입구는 같은 IDT, 다른 진입·복귀 코드 · 05 예고: "`_timer_interrupt`가 `do_timer`를 불러 `schedule()`로 가면 `ret_from_sys_call`로 돌아오는 태스크가 바뀐다 — 어떻게?" · `system_call.s:96–100`의 `reschedule`이 연결 고리 | kernel/system_call.s:96–100, 176–197 | — |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트 배치: 파트 A «입문·부팅»(01·02·03) / **파트 B «실행의 길»(04·05·06)** / 파트 C–G 이후.
- 상태: 완료 TEAL = 01 CPU·어셈블리, 02 보호 모드, 03 부팅·초기화 · 오늘 ORANGE + 굵은 테두리 = 04 · 이후 MUTED = 05~15. 04는 파트 B의 첫 회차.
- 오늘 한 줄 문구: "`write(1, ...)` 한 줄이 `int $0x80`으로 커널에 들어가 `iret`로 돌아오는 길을 통째로 따라간다"
- 03→04 연결 화살표 문구: "03: `main()`이 `trap_init`/`sched_init`으로 IDT를 채웠다 → 04: main이 끝나고 셸이 살지만 그 순간부터 틱·입력이 도착한다"
- 04→05 연결 화살표 문구: "04: `int 0x80` 진입과 `ret_from_sys_call` 복귀를 봤다 → 05: `ret_from_sys_call`에서 이어지는 스케줄 — `_timer_interrupt`가 `do_timer`를 불러 `schedule()`로 가면 돌아오는 태스크가 바뀐다"
- 우하단 범례(■ 완료 / ▶ 오늘 / □ 이후) + `Linux 0.11` 라벨.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(TEAL 진하게): kernel/system_call.s, kernel/asm.s, kernel/traps.c, include/unistd.h, include/linux/sys.h — 구조도 골격의 "진입: kernel/system_call.s · sys_call_table (include/linux/sys.h)" 행이 오늘 중심. 흐름의 도착지 fs/read_write.c `sys_write`는 화살표 경유지로 표시(상자 전체 강조는 아님).
- 오늘의 데이터 흐름 화살표(ORANGE, 출발→경유→도착): 사용자 공간 `write()` →(`int 0x80`, 번호는 include/unistd.h)→ kernel/system_call.s `_system_call` → include/linux/sys.h `sys_call_table[4]` → fs/read_write.c `sys_write` →(`ret_from_sys_call` → `iret`)→ 사용자 공간 복귀.
- 누적 강조(옅은 TEAL, 01–03 완료 분): boot/(bootsect.s·setup.s·head.s), init/main.c.
- 나머지 상자(mm/, fs/ 나머지, blk_drv/, chr_drv/, 공통)는 MUTED 외곽선 실루엣. 계층 경계(CPL=3/0)·IRQ 하단 라벨(8259A PIC · 8253 타이머(IRQ 0) · 키보드(IRQ 1) · 하드디스크(IRQ 14))은 골격 그대로. 우하단 `Linux 0.11` 라벨.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 02 | 오늘의 길 미니 지도 | 띠 도형 | 10단계 띠, 이 회차는 10단계 전부 강조(없는 단계 없음) | 공통 프레임(00-common §3) |
| 03 | 15회차 로드맵 | 도형 다이어그램 | 파트 A–G 골격, 완료 01–03·오늘 04·이후 05–15, 연결 화살표 2개 + 오늘 한 줄 문구 | 로드맵 골격 전 회차 공통 |
| 04 | 커널 전체 구조도 | 도형 다이어그램 | 오늘 파일 5개 TEAL + 데이터 흐름 화살표 + 누적 강조 boot/·init/main.c | 구조도 골격 전 회차 공통, 03회차 강조 영역 누적 |
| 05 | CPL/DPL 표 | 표 | 사용자 CS=0x0f(CPL3) vs 커널 코드 세그먼트 0x08(DPL0), far call 시 #GP | 01·02회차 CPL/DPL 표 재사용 |
| 06 | 세 가지 진입 원인 3열 | 표 | IRQ(0x20~0x2F) / 예외(0~16) / 소프트웨어(0x80) + 공통점·차이 | 신규 |
| 07 | 게이트 8바이트 필드 그림 | 비트 도식 | 선택자 0x0008 + 오프셋 + P/DPL/type 비트 위치 | 02회차 IDT 복습 자료 연계 |
| 10 | `_set_gate` 8바이트 구성 그림 | 비트 도식 | 하위/상위 4바이트 구성식, P=1·DPL·type 위치 | 07 그림 확장 |
| 12 | 상위 워드 값 계산 표 | 표 | `0x8E00`/`0x8F00`/`0xEF00` 계산 과정 + `head.s:82` `$0x8E00` 대조 | 신규 |
| 13 | 게이트 종류 비교 표 | 표 | 축: 0.11 사용 여부 / IF 자동 클리어 / DPL / 매크로 / 관련 소스 | 신규 |
| 14 | DPL 비교 표 | 표 | DPL0(#GP) vs DPL3(허용), `set_system_gate` 번호 3,4,5,0x80 | 신규 |
| 17 | 레지스터 약속 표 | 표 | EAX=번호, EBX/ECX/EDX=인자 1/2/3, `"=a"(__res)`·음수 처리 | 신규 |
| 19 | `int $0x80` 진입 순서 그림 | 순서 도식 | IDT[0x80] → DPL 검사 → TSS ss0/esp0 → 5 push → CS=0x08·EIP=`_system_call` | 신규 |
| 20 | 12슬롯 프레임 그림 | 스택 도식 | `system_call.s:17–31` 주석 그대로, 위 5개 CPU push / 아래 7개 코드 push, `OLDESP=0x28`·`OLDSS=0x2C` | 신규 |
| 21 | 상태 변화도 | 상태 다이어그램 | §1 명세 그대로, 전환마다 원인 명령·변경 데이터·유지 조건 | 신규(필수) |
| 27 | 저장 코드 4종 비교 표 | 표 | push 목록·호출 규약·복귀 경로(§1 범위 문구 그대로) | 신규 |
| 28 | 예외 번호 표 | 표 | 0~16 게이트 + 17~47 `reserved` + 45(irq13)·39(parallel) | 신규 |
| 36–41 | 캡처 게시 프레임 | 캡처 레이아웃 | 각주 5항목(lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음 · 캡처 날짜) | 공통 규칙(00-common §7) |
| 42 | 관찰 vs 추론 2열 | 2열 정리 | 시연에서 관찰한 것 / 코드에서 추론한 것 분리 | 신규 |
| 43 | `write(1,…)` 왕복 흐름도 | 흐름 다이어그램 | 9개 노드 + 각 화살표에 파일:줄 | 21 상태도 변형 |
| 44 | 세 입구 3열 정리 표 | 표 | 소프트웨어 `int 0x80` / 예외 / 하드웨어 IRQ | 신규 |
| 본문 전 | 미니 지도 띠 | 띠 도형 | 10단계, 현재 단계만 ORANGE 점 + 라벨 | 공통 프레임(00-common §3) |

## 5. 캡처 목록 (강사 시연)

공통 환경(원천 "강사 시연" 공통문 계승): `lab/`에서 QEMU를 `-s -S`(gdbstub, 시작 정지)로 띄우고 GDB에서 `target remote :1234`, 커널 심볼 로드. 부팅이 셸까지 간 뒤 중단점 설정. `src/` 줄 번호와 `lab/` 심볼 이름(`_` 접두 유무)은 다를 수 있으므로 시연 전 `info functions system_call`로 확인.

| 시연 | 캡처 파일(materials/04-interrupts-syscall/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A | 01-a1-entry-registers.png | `break system_call` → 게스트 셸에서 `echo hi` → 정지(필요시 `cond $eax == 4`); `p/x $eax $ebx $ecx $edx`, `p/x $cs`, `p/x $ss` | EAX=0x4, EBX=0x1, CS=0x8, SS=0x10 · ECX=버퍼 주소(사용자 선형 주소), EDX=길이 | 사전 캡처 `build/04-A-frame.png`(없으면 시연 전 만들어 둘 것) |
| A | 02-a2-stack-5words.png | `x/5xw $esp` | 스택 5워드: EIP, CS=0xf, EFLAGS, OLDESP, OLDSS=0x17 | 사전 캡처 `build/04-A-frame.png` |
| B | 03-b1-before-iret.png | `break sys_write` → `finish` → `p $eax`; `break ret_from_sys_call` → `x/12xw $esp` | `finish` 후 EAX = 쓴 길이(예: 3 = "hi\n") · 12워드 중 첫 워드(EAX 슬롯) = 같은 값 | 사전 캡처 2장(iret 전/후) |
| B | 04-b2-after-iret.png | `stepi` 반복으로 `iret` 통과; `p/x $cs`, `p/x $ss`, `p/x $esp` | iret 후 CS=0xf, SS=0x17, ESP=사용자 스택 복귀 · EAX(반환값)는 불변 | 사전 캡처 2장(iret 전/후) |
| C | 05-c-divide-error-console.png | lab에 넣어 둔 0 나누기 사용자 프로그램 실행; `break do_divide_error` → `p/x ((long*)$esp)[2]` 부근 5워드 덤프 → `c` | 콘솔 `divide error: 0000`, `EIP: 000f:...`, `ESP: 0017:...` 형식(`traps.c:68–70`) · 이후 `do_exit(11)`로 프로세스 종료, 셸 프롬프트 복귀 | 사전 캡처 콘솔 화면 · 테스트 프로그램이 lab에 없으면 시연 C를 생략하고 캡처만 설명 |

## 6. 이해 확인 질문과 정답 (해당 슬라이드 번호 명시)

슬라이드 47에 4문항 게시, 정답은 클릭 후 표시.

1. **Q.** `set_system_gate(0x80,…)` 대신 `set_trap_gate(0x80,…)`를 쓰면 사용자 프로그램의 `write()`는 어떻게 되는가? **A.** 게이트 DPL이 0이 되어 CPL3에서의 `int $0x80`이 #GP(13번)를 일으킨다 → `general_protection` → `die()` → `do_exit(11)`. 시스템 콜이 아니라 프로세스 종료가 된다.
2. **Q.** `_system_call`에서 `pushl %ebx; pushl %ecx; pushl %edx` 순서가 아니라 `edx, ecx, ebx` 순으로 push하는 이유는? **A.** C 호출 규약에서 첫 인자가 가장 낮은 주소(ESP 바로 위)에 있어야 하므로 마지막에 push한 ebx가 `sys_write`의 `fd`, 그다음 ecx가 `buf`, edx가 `count`가 된다.
3. **Q.** `iret` 뒤 사용자 코드의 EAX에는 무엇이 있는가? **A.** `sys_write`의 반환값. `pushl %eax`(95)로 프레임의 EAX 슬롯에 저장했다가 `popl %eax`(121)로 꺼낸 값이며, `_syscall3`의 `"=a"(__res)`가 이를 받는다. 음수면 `errno = -__res`.
4. **Q.** 타이머 인터럽트(0x20)는 `set_intr_gate`, 키보드(0x21)는 `set_trap_gate`다. 진입 직후 EFLAGS.IF 값은 각각? **A.** 인터럽트 게이트는 진입 시 IF=0(다른 IRQ 차단), 트랩 게이트는 IF를 그대로 둔다(키보드 핸들러 중 타이머 인터럽트 가능). 소스: `system.h:33–37`, `sched.c:409`, `console.c:683`.

## 7. 처음 등장하는 용어 (용어 | 정의 | 첫 등장 슬라이드)

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 게이트(gate) | IDT 항목. 번호에 대응하는 진입 주소·코드 세그먼트·DPL·종류를 담는 8바이트 | 05 |
| 인터럽트 게이트 / 트랩 게이트 | type 14 / 15. 진입 시 IF를 끄는지 여부만 다름 | 11 |
| 태스크 게이트 | type 5, TSS 전환 방식. 0.11 미사용 | 13 |
| DPL(게이트의) | 소프트웨어 `int n`을 허용하는 최대 CPL | 11 |
| 시스템 콜 번호(`__NR_*`) | `sys_call_table` 인덱스 | 18 |
| `sys_call_table` | 함수 포인터 배열(`fn_ptr`) | 18 |
| 오류 코드(error code) | 일부 예외에서 CPU가 추가로 push하는 32비트 값 | 06 |
| EOI | PIC에 "처리 끝" 신호(포트 0x20에 0x20) | 33 |
| `jiffies` | 타이머 틱 수. 05회차 핵심 | 33 |
| `ret_from_sys_call` | 시스템 콜·타이머 공통 복귀 경로 | 20 |

## 8. 흔한 오해 / 말하지 말아야 할 것 (원천 전문 계승)

- `int $0x80`을 "특별한 call"로 설명하지 말 것. 스택이 커널 스택(`tss.esp0`)으로 바뀌고 CPL이 바뀐다는 점이 본질.
- "트랩 게이트는 인터럽트를 끈다"는 반대. 인터럽트 게이트가 IF를 끈다.
- `iret`가 범용 레지스터를 복원한다고 말하지 말 것(1회차 노트와 일관).
- `sys_write`의 내부(`rw_char`, `tty_write`)는 13회차. 오늘은 "도착했다"까지만.
- `do_signal`/시그널 비트 연산(109–120)은 "사용자로 돌아가기 직전에만 검사한다"까지만. 상세는 10회차.
- `page_fault`를 예외 목록에 넣되 "오류"라고 부르지 말 것. 07·08회차에서 정상 동작의 일부로 다룸.
- 하드웨어 인터럽트는 게이트 DPL 검사를 받지 않는다. "DPL0이면 장치 인터럽트가 사용자 모드에서 안 들어온다"고 말하지 말 것.
- `lab/` 심볼명과 `src/` 줄 번호를 섞지 말 것. 캡처에는 lab 기준, 슬라이드 인용은 src 기준.
- 현대 x86-64의 `syscall`/`sysret`·`entry_64.S`를 오늘 설명하지 말 것(14회차).

## 9. 120분 운영안 (새 슬라이드 번호)

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 핵심 질문, 표준 앞부분 — 로드맵·구조도에서 오늘 위치(03 초기화 뒤, 05 스케줄링 앞) |
| 05–09 | 15 | 배경: 사용자 코드는 왜 커널 함수를 직접 못 부르는가, 이벤트 세 종류, IDT 복습(`ignore_int`·덮어쓰기 주체) |
| 10–14 | 18 | 게이트 설명자 비트, `_set_gate` 매크로, 게이트 종류 비교, DPL 비교 |
| 15–20 | 20 | `write()` 사용자 쪽: `_syscall3` 전개(코드+레지스터 약속), `__NR_write`, `int $0x80`이 쌓는 프레임 |
| 21–26 | 20 | 상태 변화도, `_system_call` 한 줄씩, `sys_call_table`, `sys_write`, `ret_from_sys_call`, iret |
| 27–33 | 15 | 예외·하드웨어 인터럽트 경로 비교: `asm.s`, `trap_init`, `timer_interrupt`, PIC |
| 34–41 | 20 | 강사 시연 A/B/C (GDB 프레임 관찰, `sys_write` 반환값, 0으로 나누기 예외) + 캡처 |
| 42–46 | 5 | 관찰 vs 추론, 질문의 답, 오해 정리 |
| 47–48 | 2 | 이해 확인 질문, 정리·05 예고 |

## 10. 기존 계획 대비 변경·증가

총 42장 → 48장(+6). 원천 슬라이드 계획 표의 42행은 전부 계승(폐기 없음). 번호 대응:

| 구 번호 | 신규 번호 | 비고 |
|---|---|---|
| 01 | 01 | 표지로 계승(유형 `제목`→`표지`) |
| 02 | 03 | "15회차 지도" 1장 → 로드맵 다이어그램으로 대체·흡수(03 초기화·05 스케줄링 연결은 §3 화살표 문구로 계승) |
| (신규) | 02, 04 | 표준 앞부분 추가(00-common §2): 핵심 질문+오늘의 길, 커널 구조도 |
| 03–13 | 05–15 | 순서 그대로 +2 |
| 14 | 16–17 | 분할: 매크로 전개 코드 / 레지스터 약속 표 — 손으로 쓴 C 코드와 표가 한 장에 안 들어가는 밀도(00-common §5 분할 기준) |
| 15–25 | 18–28 | 순서 그대로 +3 |
| 26 | 29–30 | 분할: `no_error_code` 경로(asm.s:19–51) / `error_code` 경로+공통 인자(asm.s:97–129) — 어셈블리 인용 2개·2스크린 |
| 27 | 31 | 순서 계승(+4) |
| 28 | 32–33 | 분할: 8253·PIC 설정(sched.c:406–410) / `_timer_interrupt` 한 줄씩(system_call.s:176–197) — 서로 다른 두 파일 인용 |
| 29–36 | 34–41 | 순서 그대로 +5 |
| (신규) | 42 | 관찰 vs 추론 구분 슬라이드 — 00-common §7 "시연 뒤 관찰 vs 추론 구분 슬라이드 1장 유지" 반영, 원천 표에 빠져 있던 것 보강 |
| 37–42 | 43–48 | 순서 그대로 +6. 유형 갱신: 37 `정리`→`정답`, 41 `질문`→`확인`(00-common §3 어휘) |

증가 내역 요약: 표준 앞부분 +2(구 지도 1장이 로드맵+구조도 2장으로), 밀도 분할 +3(구 14·26·28), 관찰 vs 추론 신규 +1.

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- `lab/` 빌드의 심볼명 확인: `sys_call_table` vs `_sys_call_table`, `system_call` vs `_system_call`, `sys_write` vs `_sys_write`, `ret_from_sys_call`, `do_divide_error` — 시연 전 `info functions system_call`으로 확인. 슬라이드 코드 인용은 `src/` 기준, 캡처 각주는 `lab/` 기준으로 분리해 섞지 않는다.
- QEMU gdbstub에서 `$cs`, `$ss`, `$esp` 노출 및 `stepi`로 `iret` 통과 가능 여부 — 안 되면 `monitor info registers`로 대체(course-plan 확인 목록의 gdbstub 항목 이 회차 적용).
- `lab/` 루트 이미지에 0으로 나누기 테스트 프로그램(`div0`) 유무 — 없으면 시연 C를 생략하고 사전 캡처로 설명. 테스트 프로그램은 lab 추가분(원본 src에 없음)임을 캡처 각주에 명시.
- 사전 캡처 자산 `build/04-A-frame.png` 존재 여부 — 없으면 시연 전 만들어 둘 것. 시연 B용 iret 전/후 사전 캡처 2장도 준비.
- 신규 캡처 보관처 `materials/04-interrupts-syscall/captures/` 디렉터리 생성(파일명 두 자리 순번-설명.png, §5 목록 참조).
- `cond` 조건 중단점(`$eax == 4`) 동작 확인 — 셸의 내부 동작으로 `write` 이전에 다른 시스템 콜이 먼저 걸릴 수 있음.
