# Linux 0.11 커널 강좌 — 15회차 PPTX 전체 설계

작성일 2026-11-08. 이 문서는 **설계 문서**이며 PPTX는 아직 제작하지 않았다(01회차 42장은 기존 제작분을 유지). 회차별 상세 설계는 아래 각 절에 있다.

## 운영 원칙

- 회차별 산출물은 **PPTX 하나뿐** (`output/NN-<slug>.pptx`). ODP/HTML/PDF 등 다른 형식은 만들지 않는다 (`CLAUDE.md`).
- 회당 120분, 이론+실습(강사 시연) 통합. 과제·제출물·수강생 발표 없음.
- 읽기 기준은 `src/`(Kernel.org 원본), 실행·GDB 시연은 `lab/`(yuan-xy 수정본, QEMU i386). 슬라이드의 줄 번호는 `src/` 기준이며 `lab/` 줄 번호·심볼명(`_` 접두 유무)은 PPTX 제작 시 실제 빌드에서 확인한다.
- 모든 회차 공통 구성: 제목+핵심 질문 → 15회차 지도 → 배경 → 짧은 실제 코드 → **상태 변화도** → **모드·선택지 비교** → 강사 시연(실제 QEMU/GDB 캡처) → 질문의 답 → 이해 확인 → 정리·다음 회차. 각 슬라이드 상단에 현재 단계 미니 지도.
- 실제 관찰(캡처)과 코드 추론을 구분하고, 캡처에는 실행 환경·수정본 여부를 각주로 남긴다. 실행 실패 대비 사전 캡처를 준비한다.

## 15회차 지도

| 회차 | 제목 | 핵심 질문 | 장수 | 주요 소스 |
|---|---|---|---|---|
| 01 | CPU·어셈블리 입문과 부팅부터 셸까지 | 셸이 나오기 전에 누가 실행되는가? | 42 (기존) | boot/setup.s, boot/head.s, init/main.c |
| 02 | x86 보호 모드와 소스 읽기 도구 | 선택자 하나가 어떻게 주소가 되는가? GDB로 커널을 멈추면 무엇이 보이는가? | 40 | include/linux/head.h, boot/head.s, include/asm/system.h, include/linux/sched.h |
| 03 | 부팅과 커널 초기화 | 부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가? | 40 | boot/bootsect.s, boot/setup.s, boot/head.s, init/main.c |
| 04 | 인터럽트·예외·시스템 콜 | `write(1, ...)` 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가? | 42 | kernel/system_call.s, kernel/asm.s, kernel/traps.c, include/unistd.h, include/linux/sys.h |
| 05 | 태스크와 스케줄링 | 타이머 틱 한 번에 실행 중인 태스크가 어떻게 바뀌는가? | 42 | include/linux/sched.h, kernel/sched.c, kernel/system_call.s |
| 06 | fork()와 프로세스 생성 | fork() 이후 부모와 자식은 어디에서 다시 실행되는가? | 42 | kernel/fork.c, kernel/system_call.s, mm/memory.c |
| 07 | 주소 변환과 페이지 관리 | 같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가? | 41 | mm/memory.c, boot/head.s, include/linux/sched.h |
| 08 | 페이지 폴트와 Copy-on-Write | fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가? | 40 | mm/page.s, mm/memory.c |
| 09 | exec()와 프로그램 실행 | PID는 그대로인데 프로그램은 어떻게 바뀌는가? | 41 | fs/exec.c, include/a.out.h |
| 10 | 종료·대기·시그널 | 자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가? | 40 | kernel/exit.c, kernel/signal.c, kernel/system_call.s |
| 11 | 버퍼 캐시와 블록 장치 | read()가 디스크에 실제로 접근하는 때는 언제인가? | 38 | fs/buffer.c, kernel/blk_drv/ll_rw_blk.c, kernel/blk_drv/hd.c |
| 12 | 파일 시스템: inode·경로 탐색·I/O | "/etc/rc"라는 문자열이 어떻게 디스크 블록이 되는가? | 38 | include/linux/fs.h, fs/namei.c, fs/inode.c, fs/open.c, fs/read_write.c, fs/file_dev.c |
| 13 | 터미널 I/O | 키보드에서 누른 글자가 read()까지 어떻게 전달되는가? | 42 | kernel/chr_drv/keyboard.S, tty_io.c, console.c, include/linux/tty.h |
| 14 | 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교 | `ls /` 한 줄에 지금까지 배운 것이 어떻게 모두 등장하는가? | 40 | 01~13 인용 |
| 15 | 커널 수정 실습: 새 시스템 콜과 스케줄러 변경 | 커널을 바꾸면 어디서 어떻게 확인하는가? | 42 | include/unistd.h, include/linux/sys.h, kernel/system_call.s, kernel/sched.c |

총 약 610장. 15회차는 이전 계획의 "현대 커널 모듈(15)·sched_ext(16)" 두 회차를 대체한다 — 현대 커널 VM 환경이 미선정이므로 Linux 0.11 안에서 수정·재빌드·검증까지 완결하는 실습으로 통합했다.

## 설계 단계에서 확인한 원본 소스 사실 (슬라이드에 반영)

- `TASK_STOPPED`는 정의·검사되지만 0.11 어디에서도 대입되지 않는다 (05).
- `schedule()`의 역순 스캔 + 엄격한 `>` 때문에 counter가 같으면 높은 인덱스의 태스크가 선택된다 (05).
- `E2BIG`은 정의만 있고 `fs/exec.c`는 쓰지 않으며, 실행 권한 없음은 `EACCES`가 아니라 `ENOEXEC`를 반환한다 (09).
- `kill_pg`는 0.11에 없고 Ctrl-C 경로는 `tty_intr`이다 (10/13).
- `breada`가 `tmp` 대신 `bh`를 `ll_rw_block`에 넘기는 원본 버그, `O_EXCL`을 `O_CREAT` 없이 검사하는 점 (11/12).
- `L_ECHOE/L_ECHOK/L_ECHOKE`, `SUSPEND_CHAR`는 정의만 있고 호출되지 않으며, `tty->stopped`는 쓰기만 하고 읽지 않는다; 원본 `config.h`는 핀란드 키보드를 선택한다 (13).
- 기존 01 자료의 `setup.s:186-193` 인용은 `191-193`이 정확하다 (186-190은 주석).

## PPTX 제작 전 확인 목록 (lab/ 의존)

- `lab/` 빌드의 심볼명(`main` vs `_main`, `sys_call_table` vs `_sys_call_table`)과 줄 번호.
- QEMU gdbstub에서 `$cr3`, GDTR 노출 여부 — 안 되면 `monitor info registers`로 대체.
- 루트 이미지 안 `/etc/rc`의 inode·블록 번호(12), 시그널 핸들러·fork-write 테스트 프로그램(08/10), 게스트 gcc 유무(15).
- 각 회차 사전 캡처 파일명 규칙: `materials/NN-<slug>/captures/`.

---

# 01. CPU·어셈블리 입문과 부팅부터 셸까지

> **상태**: 기존 42장 PPTX(이미 제작·검증됨)를 **그대로 유지**한다. 변경 사항은 두 가지뿐이다.
> 1. 2장(과정 지도)과 매 장 상단 미니 지도를 **16회차 → 15회차**(SPEC의 고정 표)로 갱신한다.
> 2. 기존 해설에서 "시연"으로 표시된 22장(QEMU 부팅, echo/ls)과 40장(셸 명령 짧은 시연)에 **실제 QEMU 캡처**(lab/ 환경, 각주 포함)를 추가한다. 사전 캡처가 있으면 "기존 기록"으로 표시한다.
> 아래 표는 기존 구조를 요약한 것이며 슬라이드를 새로 설계하지 않는다.

## 핵심 질문
셸이 나오기 전에 누가 실행되는가?

## 학습 목표
1. CPU는 C 문장이 아니라 기계어를 실행하며, 명령 하나가 레지스터·메모리·플래그 중 무엇을 바꾸는지 말할 수 있다.
2. as86(목적지, 원본)과 AT&T(원본, 목적지) 두 어셈블리 문법의 피연산자 순서 차이를 구분한다.
3. 실주소 모드와 보호 모드, CPL 0/3, PE/PG/IF가 서로 다른 축임을 안다.
4. BIOS → bootsect → setup → head → main() → task 0/init → 셸의 전체 경로를 학습자의 말로 요약한다.
5. 프로그램·프로세스·PID·fd의 일상어 정의와 fork/exec/wait의 역할을 말한다.

## 읽을 소스 범위 (원본 src 기준, grep -n/sed -n 확인)
| 파일 | 줄 | 내용 |
|---|---|---|
| boot/setup.s | 191-193 | `lmsw ax` / `jmpi 0,8` — 보호 모드 진입 (기존 노트의 186-193은 설명 주석 186-190 포함) |
| boot/head.s | 135-144 | after_page_tables: main 인수·복귀 주소 push, `jmp setup_paging` |
| boot/head.s | 198-218 | setup_paging: 페이지 디렉터리/테이블 생성, CR3·PG 설정 |
| init/main.c | 104-149 | main(): 메모리 크기 계산, 초기화 호출, sti, move_to_user_mode, 첫 fork, pause 루프 |
| include/asm/system.h | 1-17 | move_to_user_mode (iret 프레임), sti/cli |
| init/main.c | 168-209 | init(): setup, tty open/dup, rc 자식, 셸 fork/wait 루프 |
| include/fcntl.h | 전체 | O_RDONLY/O_WRONLY/O_RDWR 접근 모드 |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도**(28장): 단계별 PE/PG/CPL/IF — BIOS(0/0/—/1) → setup `cli`(IF=0) → `lmsw`(PE=1) → head `setup_paging`(PG=1) → main `sti`(IF=1) → `move_to_user_mode`(CPL=3). 전환 원인은 각 명령, 변경 데이터는 CR0·EFLAGS·CS 선택자. "IF는 표시 지점의 값"이라는 주의 유지.
- **모드 비교**(29장): 80386 CPU 모드 = real-address / protected / virtual-8086 — 세 가지 전부. 0.11 경로는 real→protected, VM86 미사용.
- **권한 비교**(30장): CPL 0/1/2/3 전부. 0.11 주 경로는 0과 3.
- **제어 비트 비교**(31장): PG 0/1, IF 0/1.
- **open 접근 모드 비교**(37장): O_RDONLY/O_WRONLY/O_RDWR.

## 120분 운영안 (기존 유지)
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 수업 목표와 15회차 지도 |
| 03–07 | 18 | CPU·메모리·레지스터와 명령 실행 |
| 08–11 | 17 | 어셈블리 읽기와 스택 상태 추적 |
| 12–18 | 25 | 보호의 필요, 주소 변환, 이벤트와 제어 비트 |
| 19–24 | 15 | 실행 환경, QEMU 부팅 시연(실제 캡처), BIOS와 커널 경로 |
| 25–33 | 20 | 원본 코드와 모드·상태 변화 연결 |
| 34–40 | 15 | 프로세스·fd, init과 셸, 짧은 시연(실제 캡처) |
| 41–42 | 5 | 이해 확인과 정리 |

## 슬라이드 계획 (기존 42장 요약)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 제목·핵심 질문 | "셸이 나오기 전에 누가 실행되는가?" 질문만 남기고 시작. | 제목 |
| 02 | 15회차 지도 (**갱신**) | SPEC 고정 표 15행, 01 강조. 상단 미니 지도도 15회차로 교체. | 지도 |
| 03–07 | CPU·메모리·레지스터·명령 실행 | CPU/RAM/디스크/장치 역할, bit/byte/16진수, 주소와 값, EAX/AX·EIP/CS·ESP/SS, 읽기→해석→실행 모델과 jump. | 배경 |
| 08–11 | 어셈블리 읽기와 스택 | .c/.s/.o와 컴파일·어셈블·링크, as86 vs AT&T 문법(`mov ax,#0x9000` / `movl $0x10,%eax`), mov/add 뒤 EAX·플래그 변화 상태도, pushl/popl/call/ret의 ESP 변화 상태도(설명용 예시임을 명시). | 코드·상태도 |
| 12–15 | 보호의 필요와 주소 변환 | 사용자 실수로부터 커널 보호, 실주소 모드 세그먼트×16 vs 보호 모드 설명표, 선택자는 설명표 색인, GDT/LDT/IDT 한 줄 소개, 선형↔물리 주소(초기 매핑은 identity). | 배경·비교 |
| 16–18 | 이벤트와 제어 비트 | 장치 인터럽트/예외/소프트웨어 인터럽트 구분, 문맥(실행 위치·스택·상태)과 iret, PE/PG/IF/CPL 참조표. | 배경 |
| 19–21 | 실행 환경과 전체 지도 | 호스트/QEMU(TCG)/게스트, src vs lab vs build, BIOS→bootsect→setup→head→main→init→sh 전체 제어 흐름 지도. | 배경·지도 |
| 22 | QEMU 부팅 시연 (**실제 캡처 추가**) | lab/에서 QEMU 부팅 후 "Loading system ..." → 셸 프롬프트 → `echo`/`ls` 출력 캡처. 각주: lab/(yuan-xy 기반 수정본), QEMU i386 TCG, 원본과의 차이. | 시연·캡처 |
| 23–24 | BIOS와 커널 경로 | legacy BIOS와 부트 섹터, bootsect/setup/head의 책임 분담, A20·PIC 용어 풀이. | 배경 |
| 25–27 | 원본 코드 읽기 | setup.s:191-193 (`mov ax,#1`/`lmsw`/`jmpi 0,8`) 3줄 상태 추적; head.s:198-218 setup_paging 명령별 분석(27장은 심화 참조 가능); head.s:135-144의 main 주소 push와 ret. | 코드 |
| 28 | 부팅 단계별 상태 변화도 | PE/PG/CPL/IF를 단계별로 비교. 표시 지점의 값임을 명시. | 상태도 |
| 29–31 | 모드·권한·제어 비트 비교 | 80386 real/protected/VM86 전부; CPL 0~3 전부; PG 0/1·IF 0/1 각각. 범위를 섞지 않는다. | 비교 |
| 32–33 | main()의 초기화와 사용자 전환 | main.c:126-137 초기화 호출을 범주로 묶음(메모리/트랩/장치/스케줄러), `sti`; system.h:1-14 move_to_user_mode의 iret 프레임(33장 심화 참조 가능) — 같은 task의 권한 변화이지 새 프로세스가 아님. | 코드 |
| 34–36 | 프로세스·fork·init | 프로그램/프로세스/PID 일상어, main.c:138-148 첫 fork와 task 0 pause 루프, main.c:168-209 init의 rc 자식과 셸 재생성 루프. | 배경·코드 |
| 37–39 | fd·open·exec | fd 0/1/2 관례, O_RDONLY/O_WRONLY/O_RDWR 비교, main.c:172-175 open/dup, execve는 PID 유지·성공 시 미반환. | 비교·코드 |
| 40 | 셸 명령 짧은 시연 (**실제 캡처 추가**) | 셸에서 `ls`, `echo`, 내장 명령 실행 캡처. 화면 결과와 소스 추론 구분. 각주에 환경 표기. | 시연·캡처 |
| 41 | 이해 확인 질문 | 8문항(정답 포함) — 아래 참조. | 질문 |
| 42 | 정리·다음 회차 예고 | 부팅→커널 초기화→init→셸 요약, 02회차(보호 모드·GDB) 예고. | 정리 |

## 강사 시연
- **A. QEMU 부팅부터 셸까지** (22장): `lab/`에서 `make run`(또는 프로젝트 스크립트)으로 QEMU 실행. 관찰 대상: BIOS 메시지 → "Loading system ..." → 커널 버퍼/메모리 출력 → 셸 프롬프트. 기대 출력: `init` printf의 "xxx buffers = yyy bytes buffer space", "Free mem: ..." 뒤 `#` 프롬프트. `echo hello`, `ls /` 실행. 실패 시 대체: `build/boot.png` 사전 캡처("기존 기록" 표시).
- **B. 셸 명령 짧은 시연** (40장): 내장 명령(`cd`)과 외부 명령(`ls`) 각 1회. 관찰 대상: 결과 화면만; fork/exec 여부는 소스 추론임을 명시. 대체: 사전 캡처.
- GDB는 이번 회차에서 사용하지 않는다(02회차부터).

## 이해 확인 질문과 정답 (41장, 기존 유지)
1. CPU가 직접 실행하는 것은? — 기계어(C 문자열이 아님).
2. `[0x1000]`의 값을 12로 바꾸면 주소도 바뀌는가? — 아니오. 주소와 값은 별개.
3. as86 `mov ax,#1`과 AT&T `movl $1,%eax`의 차이는? — 피연산자 순서가 반대(목적지,원본 / 원본,목적지).
4. 사용자 프로그램은 어느 CPU 모드에서 실행되는가? — 보호 모드(CPL 3). real mode가 아님.
5. 첫 fork의 부모(task 0)는 무엇을 하는가? — `for(;;) pause();` 루프 (main.c:148).
6. 셸은 누가 실행하는가? — init이 fork한 자식에서 execve("/bin/sh") (main.c:194-200).
7. exec 뒤 PID는? — 그대로 유지, 주소 공간과 실행 이미지만 교체.
8. 셸이 종료되면 누가 회수하는가? — init의 `wait` 루프 (main.c:202-206), 그 뒤 새 셸을 다시 fork.

## 처음 등장하는 용어
BIOS, 부트 섹터, 레지스터(EAX/AX, EIP/CS, ESP/SS), 플래그, 스택(push/pop), 실주소 모드/보호 모드, 세그먼트/선택자, GDT/LDT/IDT, 선형 주소/물리 주소, 인터럽트/예외/소프트웨어 인터럽트, 문맥, PE/PG/IF/CPL, IRQ/PIC, A20, QEMU/TCG, 프로세스/PID, fork/exec/wait, fd/tty, init.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- 실주소 모드를 "제한이 없는 모드"라고 부르지 않는다.
- "인터럽트는 모두 장치에서 온다"고 말하지 않는다(int 0x80 시스템 콜).
- iret가 범용 레지스터를 자동 복구한다고 말하지 않는다.
- 상태도의 레지스터 값 예시는 설명용이며 실측이 아님을 명시한다.
- move_to_user_mode는 새 프로세스 생성이 아니라 같은 task의 권한 변경이다.
- 첫 fork는 성공을 가정한다(main.c:138 주석 "we count on this going ok").
- 현대 x86-64 long mode, UEFI, SMM은 범위 밖. 현대 호스트 커널과 0.11을 혼동하지 않게 한다.
- 캡처는 lab/(수정본)에서 얻은 것이며 슬라이드 인용 줄 번호는 src/ 원본 기준임을 각주로 분리한다.

---

# 02. x86 보호 모드와 소스 읽기 도구

## 핵심 질문
선택자 하나가 어떻게 주소가 되는가? GDB로 커널을 멈추면 무엇이 보이는가?

## 학습 목표
1. 선택자(index/TI/RPL) → 설명표(GDT/LDT) 항목 → base/limit/권한 → 선형 주소 → (페이징) 물리 주소의 경로를 손으로 따라갈 수 있다.
2. 0.11의 GDT 초기 항목(head.s)과 task_struct 안의 LDT·TSS 항목(sched.h)을 64비트 값으로 해독한다.
3. IDT 게이트의 종류(인터럽트/트랩/태스크)와 DPL이 `set_intr_gate`/`set_trap_gate`/`set_system_gate` 매크로에서 어떻게 비트로 들어가는지 읽는다.
4. 권한 전환 시 스택이 TSS의 ss0/esp0로 바뀌고 CPU가 무엇을 push하는지 상태도로 설명한다.
5. VS Code + QEMU `-s -S` + GDB로 lab/ 커널을 `main`에서 멈추고 레지스터·스택·GDT 메모리를 직접 관찰한다.

## 읽을 소스 범위 (원본 src 기준, grep -n/sed -n 확인)
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

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 1 — 세그먼트 레지스터의 두 부분**: 상태 = {보이는 선택자 값, 보이지 않는 캐시(base/limit/attr)}. 전환 원인: `lgdt`는 GDTR만 바꾸고 캐시는 **불변**; `mov %ax,%ds`/`jmpi`/`lss`가 설명표를 읽어 캐시를 갱신. head.s:24-31에서 setup_gdt 뒤 세그먼트를 **다시 로드**하는 이유. 유지 조건: 캐시는 다음 로드까지 유지(설명표를 메모리에서 바꿔도 즉시 반영 안 됨).
- **상태 변화도 2 — 권한 전환 시 스택**: 상태 = {CPL, SS:ESP, 스택 내용}. CPL3 → 인터럽트/`int` → CPU가 TSS.ss0/esp0 로드 → SS/ESP/EFLAGS/CS/EIP push(오류코드 포함 시 +1) → 핸들러 → `iret` → CPL3 복귀. 변경 데이터: SS/ESP/CS/EIP/EFLAGS. sched.h:53-54(esp0/ss0)와 fork.c:93-94를 근거로.
- **상태 변화도 3 — GDB 세션**: QEMU `-S` 정지(EIP=0xfff0, real mode) → `target remote` 연결 → `b main`/`c` → 중단(보호 모드, 페이징 ON) → `si`/`n`/`c`.
- **모드·선택지 비교 1 — 설명표(80386)**: GDT / LDT / IDT 전부. 각각 로드 명령(lgdt/lldt/lidt), 선택 방법(TI=0/TI=1/벡터 번호), 0.11 사용 여부(모두 사용), 관련 소스.
- **모드·선택지 비교 2 — IDT 게이트 종류(80386)**: 태스크 게이트(type 5) / 인터럽트 게이트(14) / 트랩 게이트(15) 전부. 전환 조건(IF 클리어 여부), 0.11 사용: 14·15만(system.h:33-40), 태스크 게이트 미사용. 콜 게이트는 IDT가 아닌 GDT/LDT용이라 범위 밖임을 한 줄로.
- **모드·선택지 비교 3 — 설명자 분류**: 코드/데이터(S=1) vs 시스템(S=0: TSS 0x89, LDT 0x82, 게이트). 0.11 사용 여부와 생성 매크로.
- 권한(CPL/DPL/RPL)은 세 가지 필드로만 비교하고 CPU 모드와 섞지 않는다.

## 120분 운영안
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문, 15회차 지도 |
| 03–07 | 15 | 1회차 복습(실주소 vs 보호 모드), 선택자 구조, 설명표 비교 |
| 08–14 | 20 | 설명자 해독: head.s GDT, LDT(INIT_TASK), TSS·LDT 시스템 설명자, 주소 변환 경로 |
| 15–19 | 15 | 게이트와 IDT, 권한(CPL/DPL/RPL), 스택과 권한 전환 상태도 |
| 20–24 | 15 | 도구 준비: lab/ 구조, VS Code, QEMU `-s -S`, GDB 연결 상태도 |
| 25–33 | 30 | 강사 시연 A/B/C (main 중단, 레지스터·스택, GDT 덤프 전후 비교) |
| 34–37 | 10 | 관찰 결과와 코드 추론의 대조, 선택자→주소 답 정리 |
| 38–40 | 10 | 이해 확인 질문, 정리·03회차 예고 |

## 슬라이드 계획
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 제목·핵심 질문 | "선택자 하나가 어떻게 주소가 되는가? GDB로 커널을 멈추면 무엇이 보이는가?" 두 질문을 오늘 끝에 답하겠다고 선언. | 제목 |
| 02 | 15회차 지도 | 고정 표, 02 강조. 01(입문)→02(도구·구조)→03(부팅 경로) 흐름 표시. | 지도 |
| 03 | 1회차 복습: 두 주소 모델 | 실주소 모드 `seg*16+off` vs 보호 모드 "선택자→설명자→base+off". 그림 두 개 나란히. | 배경 |
| 04 | 선택자 16비트 해부 | index(13비트)/TI(1)/RPL(2) 그림. 0.11 상수 4개 해독표: 0x08(idx1,GDT,0) 0x10(idx2,GDT,0) 0x0f(idx1,**LDT**,3) 0x17(idx2,**LDT**,3). 출처: head.s:18, system.h:3-6, sched.h:130. | 배경 |
| 05 | 설명표 비교: GDT / LDT / IDT | 80386의 세 표 전부. 로드 명령, 레지스터(GDTR/LDTR/IDTR), 선택 방식, 항목 크기 8바이트, 0.11 사용처(head.s:92,106 / sched.c:405 / head.s:92). | 비교 |
| 06 | GDTR·IDTR의 실제 값 | head.s:222-229 `idt_descr`/`gdt_descr` 코드: limit 256*8-1, base `_idt`/`_gdt`. setup.s:218-224의 임시 표(limit 0x800, base 0x9xxxx)와 대조 — "표는 두 번 만들어진다". | 코드 |
| 07 | head.s의 GDT 원문 | head.s:232-238 코드. NULL / 0x00c09a0000000fff / 0x00c0920000000fff / TMP / `.fill 252,8,0`. "252개 여유가 LDT·TSS 자리"(sched.h:150-151 주석). | 코드 |
| 08 | 세그먼트 설명자 64비트 해부 | 그림: base(32)·limit(20)·G·D/B·P·DPL·S·type. `0x00c09a0000000fff` 해독: base 0, limit 0xfff, G=1 → 16MB, P=1 DPL=0 S=1 type=0xA(code exec/read); 0x92 → data r/w. system.h:42-50 `_set_seg_desc`의 OR 식을 같은 그림에 대응. | 배경 |
| 09 | task_struct 안의 LDT | sched.h:103-104 `ldt[3]` 주석 "0 - zero 1 - cs 2 - ds&ss". INIT_TASK sched.h:125-126 `{0x9f,0xc0fa00}`/`{0x9f,0xc0f200}` 해독: limit 0x9f(G=1 → 640KB, 주석 sched.h:111), DPL=3, 코드/데이터. "왜 DPL 3인가"를 질문으로. | 코드 |
| 10 | 설명자 필드를 만지는 매크로 | sched.h:188-212 `_set_base`/`_set_limit`/`set_base`/`set_limit` — 흩어진 base 바이트(+2,+4,+7)를 `rorl`로 채우는 코드. fork.c:54-55에서 자식 LDT base를 바꾸는 한 줄(06회차 예고). | 코드 |
| 11 | 시스템 설명자: TSS·LDT | system.h:52-66 `_set_tssldt_desc`: limit 104, type 0x89(TSS available) / 0x82(LDT). sched.h:153-158 FIRST_TSS_ENTRY 4, `_TSS(n)=16n+32`, `_LDT(n)=16n+40` → TSS0 선택자 0x20, LDT0 0x28. sched.c:392-393, 404-405 `ltr(0)`,`lldt(0)`. | 코드 |
| 12 | 설명자 분류 비교 | S 비트 기준: 코드/데이터(S=1) vs 시스템(S=0: TSS, LDT, 게이트). 각 유형의 0.11 생성 매크로와 사용 여부. | 비교 |
| 13 | tss_struct와 "숨은 스택" | sched.h:51-76 구조체. esp0/ss0는 CPL0 진입 시 CPU가 자동 로드. INIT_TASK sched.h:128: esp0 = `PAGE_SIZE+&init_task`, ss0=0x10 → task_union의 페이지 끝(sched.c:53-58). | 코드 |
| 14 | 선택자 → 선형 → 물리: 전체 경로 | 그림: `0x17:0x1234` → LDTR → LDT[2] → base+0x1234 = 선형 → CR3/페이지 테이블 → 물리. 오늘은 선형까지, 페이징은 07회차. 커널 세그먼트(base 0)는 선형=오프셋. | 배경 |
| 15 | 상태 변화도 1: 세그먼트 레지스터의 두 부분 | 보이는 선택자 / 보이지 않는 캐시. `lgdt`는 캐시를 바꾸지 않음 → head.s:26-31 재로드 코드 인용(주석 "reload all the segment registers after changing gdt"). | 상태도 |
| 16 | IDT 게이트 64비트 해부 | 그림: 선택자(16)·offset(32)·P·DPL·type. system.h:22-31 `_set_gate`: `%0 = 0x8000+(dpl<<13)+(type<<8)`, eax=0x00080000 → 선택자 0x0008. head.s:79-82 setup_idt의 0x8E00과 동일 비트 확인. | 코드 |
| 17 | 게이트 종류 비교 (IDT, 80386) | 태스크(5)/인터럽트(14)/트랩(15) 전부. 차이: 인터럽트 게이트는 진입 시 IF 클리어. 0.11: system.h:33-40 → intr(14,dpl0)/trap(15,dpl0)/system(15,dpl3). 태스크 게이트 미사용. 콜 게이트는 IDT 밖. | 비교 |
| 18 | 권한: CPL / DPL / RPL | 세 필드 정의와 검사 규칙 한 줄씩(데이터 세그먼트: max(CPL,RPL) ≤ DPL; 게이트: CPL ≤ 게이트 DPL). `int $0x80`이 CPL3에서 되는 이유 = set_system_gate의 dpl 3 (sched.c:411). `int3`(traps.c:188)도 같은 이유. | 배경 |
| 19 | 상태 변화도 2: 권한 전환과 스택 | CPL3 실행 → 게이트 통과 → TSS.ss0/esp0 로드 → SS,ESP,EFLAGS,CS,EIP push → 핸들러(CPL0) → iret → 복귀. 변경 데이터 표기. system.h:1-14 move_to_user_mode가 이 프레임을 "거꾸로 만든다"는 1회차 연결. | 상태도 |
| 20 | lab/ 환경 지도 | src(원본, 인용 기준) vs lab(yuan-xy 기반, 현대 GCC·QEMU i386 실행본). 심볼 이름·줄 번호가 다를 수 있음을 경고. 빌드 산출물(Image, system/System.map). | 배경 |
| 21 | QEMU `-s -S` | `-s` = gdbstub :1234, `-S` = CPU 정지 상태로 시작. 정지 직후 상태(real mode, EIP 0xfff0, CS 0xf000)는 아직 BIOS 전. 재설정·종료 방법. | 배경 |
| 22 | GDB 연결과 기본 명령 | `target remote :1234`, `symbol-file`, `b main`, `c`, `info registers`, `x/8xw $esp`, `x/8xw &gdt`, `p/x $cr0`, `si`/`n`, `bt`. 각 명령이 "무엇을 읽는가"를 한 줄로. | 배경 |
| 23 | VS Code 연결 | launch.json(gdb remote :1234, program=system ELF) 핵심 항목과 Breakpoints·Registers·Memory 패널 캡처. 터미널 GDB와 같은 정보를 다르게 보여줄 뿐임을 명시. | 캡처 |
| 24 | 상태 변화도 3: GDB 세션 | QEMU 정지 → 연결 → 중단점 설정 → continue → 중단(멈춘 EIP·CPL) → step/continue → 종료. 각 상태에서 가능한 명령. | 상태도 |
| 25 | 시연 A-1: `b main` 도달 | 터미널 캡처: `Breakpoint 1, main () at init/main.c:NN`. 각주: lab/ 수정본, QEMU i386 TCG, 줄 번호는 lab 기준. | 시연·캡처 |
| 26 | 시연 A-2: `info registers` | 캡처: cs=0x0008, ds/es/fs/gs/ss=0x0010, eflags에서 IF=0, cr0 비트0(PE)·비트31(PG)=1, cr3=0. 04장 해독표와 대조. | 캡처 |
| 27 | 시연 A-3: `x/8xw $esp` | 캡처: 스택 최상단에 L6 복귀 주소와 0,0,0(head.s:136-140의 push). esp가 `user_stack` 끝 근처(sched.c:67-72)임을 `p &user_stack` 으로 확인. | 캡처 |
| 28 | 시연 B-1: GDT 베이스 찾기 | QEMU 모니터 `info registers`의 `GDT=` 줄(base·limit) 캡처 + GDB `p &gdt`가 같은 값인지 대조. GDB 원격에서 GDTR이 직접 안 보이면 모니터를 쓴다는 설명. | 캡처 |
| 29 | 시연 B-2: `x/8xw &gdt` (main 진입 시점) | 캡처 기대: `0x00000000 0x00000000 0x00000fff 0x00c09a00 0x00000fff 0x00c09200 0x00000000 0x00000000` — head.s:234-237 원문과 1:1 대조(리틀엔디언 순서 주의). | 캡처 |
| 30 | 시연 B-3: sched_init 이후 GDT | `b sched_init`→`finish` 뒤 `x/4xw &gdt[4]`: TSS0(type 0x89, limit 0x68)·LDT0(0x82) 설명자가 채워짐. 전후 비교 그림. sched.c:392-393 근거. | 캡처 |
| 31 | 시연 C-1: LDT 항목 읽기 | `p/x init_task.task.ldt` (또는 `x/6xw &init_task.task.ldt`): 0x9f/0xc0fa00, 0x9f/0xc0f200. 09장 해독과 대조. | 캡처 |
| 32 | 시연 C-2: IDT 항목 읽기 | `x/2xw &idt[0x80]` (sched_init 이후): 하위 워드 0x0008(선택자), 상위에 0xEF00(P=1,DPL=3,type 15) + system_call 주소. `x/2xw &idt[0x20]` 는 0x8E00(인터럽트 게이트). | 캡처 |
| 33 | 시연 C-3: 선택자 로드 추적 | head.s:18-22 위치에서 `si`로 `mov %ax,%ds` 전후 `info registers ds` 비교 — 값은 바뀌지만 base/limit는 GDB에 안 보임(캐시는 숨겨짐)을 체험. 대체: 사전 캡처. | 캡처 |
| 34 | 관찰 vs 추론 | 표: 캡처로 **본 것**(레지스터 값, 메모리 덤프) / 소스에서 **추론한 것**(캐시 갱신, CPU의 push 순서, 권한 검사). 혼동 금지. | 배경 |
| 35 | 답 1: 선택자가 주소가 되는 법 | 04·08·14장을 한 장으로: `0x17:off` → LDT[2].base + off. 0.11에서 task 0은 base 0, 자식은 fork.c:54-55에서 `nr*0x4000000`(06회차). | 정리 |
| 36 | 답 2: 멈춘 커널에서 보이는 것 | 레지스터(선택자·CR0·EFLAGS), 스택(복귀 주소), 설명표(메모리 덤프). 보이지 않는 것: 세그먼트 캐시, TLB. | 정리 |
| 37 | 다음 회차와의 연결 | 03회차는 이 표들이 "언제" 만들어지는지(setup.s 임시 GDT → head.s GDT → sched_init TSS/LDT), 04회차는 게이트를 "통과"하는 순간. | 지도 |
| 38 | 이해 확인 질문 | 6문항, 정답 포함(아래). | 질문 |
| 39 | 정리 | 선택자→설명자→base, 세 표, 게이트 3종, 권한 3필드, GDB 5명령. | 정리 |
| 40 | 03회차 예고 | "부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?" | 정리 |

## 강사 시연
- **A. main에서 멈추기** (25–27장)
  - 명령: 터미널1 `qemu-system-i386 ... -s -S` (lab/의 실행 스크립트 사용); 터미널2 `gdb lab/tools/system`(ELF) → `target remote :1234` → `b main` → `c`.
  - 중단점: `main` (init/main.c:104 원본 기준).
  - 관찰: `info registers` → cs 0x0008 / ds·es·fs·gs·ss 0x0010 / eflags IF=0 / cr0 PE=1·PG=1 / cr3=0; `x/8xw $esp` → L6 복귀 주소, 0, 0, 0.
  - 기대 출력: 위 값. cr0의 MP/EM/ET 비트는 FPU 유무에 따라 다르므로(head.s:43-61) 정확한 전체 값은 "관찰 결과"로만 말한다.
  - 대체: 사전 캡처 `build/gdb-main.txt`(기존 기록 표시).
- **B. GDT 덤프 전후 비교** (28–30장)
  - 명령: QEMU 모니터 `info registers`(GDT= 줄); GDB `p &gdt`, `x/8xw &gdt`; `b sched_init` → `c` → `finish` → `x/4xw &gdt[4]`.
  - 관찰: main 진입 시 항목 0–3만 유효(head.s:234-237), sched_init 뒤 항목 4(TSS0, 0x89)·5(LDT0, 0x82) 채워짐(sched.c:392-393).
  - 기대 출력: 29장 값; 항목 4의 상위 워드에 `0x..89..`, limit 0x68(=104, system.h:53).
  - 대체: 사전 캡처 두 장(전/후).
- **C. LDT·IDT·선택자 로드** (31–33장)
  - 명령: `p/x init_task.task.ldt`; `x/2xw &idt[0x80]`, `x/2xw &idt[0x20]`; head.s 초기 부분은 `b *0`(또는 lab의 startup 심볼)에서 `si` 반복 후 `info registers ds`.
  - 관찰: LDT 0x9f/0xc0fa00·0x9f/0xc0f200(sched.h:125-126); IDT[0x80] 상위 바이트 0xEF(P,DPL3,trap), IDT[0x20] 0x8E.
  - 대체: 사전 캡처. head.s 초기(페이징 전) 중단은 심볼 주소 0 근처라 GDB가 불안정할 수 있으므로 C-3는 선택 항목으로 두고 실패 시 캡처로 대체.
- 공통 각주: "lab/(yuan-xy/Linux-0.11 기반 수정본), QEMU i386, TCG. 줄 번호·심볼명은 lab 기준이며 슬라이드 인용은 src/ 원본."

## 이해 확인 질문과 정답
1. 선택자 0x17을 index/TI/RPL로 나누면? — index 2, TI=1(LDT), RPL=3. (0001 0111b)
2. `lgdt`를 실행하면 DS가 가리키는 세그먼트의 base가 바로 바뀌는가? — 아니오. 세그먼트 레지스터를 다시 로드해야 캐시가 갱신된다(head.s:26-31).
3. `0x00c09a0000000fff`에서 limit는 몇 바이트인가? — 0xfff+1 페이지 × 4KB = 16MB (G=1).
4. `set_system_gate`와 `set_trap_gate`의 유일한 차이는? — DPL 3 vs 0 (system.h:36-40). 둘 다 type 15(트랩 게이트).
5. CPL3에서 `int $0x80`으로 진입할 때 커널 스택 포인터는 어디서 오는가? — 현재 태스크 TSS의 ss0/esp0 (sched.h:53-54).
6. GDB `info registers`에서 보이지 않는 세그먼트 정보는? — 설명자 캐시(base/limit/attr). 선택자 값만 보인다.

## 처음 등장하는 용어
선택자(index/TI/RPL), 설명자(descriptor), GDTR/LDTR/IDTR, base/limit/G 비트, DPL/RPL/CPL, S 비트(시스템 설명자), TSS(esp0/ss0), 게이트(인터럽트/트랩/태스크), 세그먼트 캐시(숨은 부분), 선형 주소, `lgdt`/`lidt`/`lldt`/`ltr`, `lss`, gdbstub, `-s -S`, `target remote`, `x/8xw`, QEMU 모니터, System.map.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- "선택자 = 주소"라고 말하지 않는다. 선택자는 표의 색인이다.
- 0x0f/0x17이 "GDT 1·2번"이라고 말하지 않는다. TI=1이므로 LDT 항목이다.
- GDB `info registers`의 cr0 전체 값을 미리 단정하지 않는다(FPU 유무로 MP/EM이 달라짐, head.s:43-61).
- 페이징(선형→물리)은 오늘 범위 밖. "0.11 사용자 주소 = 물리 주소"라고 말하지 않는다.
- lab/의 줄 번호·심볼(`main` vs `_main`)이 src/와 다를 수 있음을 숨기지 않는다.
- 세그먼트 캐시 갱신, CPU의 push 순서는 **코드 추론·아키텍처 문서 근거**이며 GDB로 직접 본 것이 아니다.
- 태스크 게이트·콜 게이트는 "존재하지만 0.11은 쓰지 않는다"까지만 말한다.
- x86-64의 세그먼테이션 축소는 14회차 비교로 미룬다.

---

# 03. 부팅과 커널 초기화

## 핵심 질문
부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?

## 학습 목표
1. BIOS → bootsect.s(0x7c00→0x90000) → setup.s(0x90200) → head.s(0x0) → main()의 메모리 배치와 적재 순서를 그림으로 그릴 수 있다.
2. 각 단계에서 PE / PG / IF / CPL 네 비트가 **어느 명령 때문에** 바뀌는지 줄 번호로 짚는다.
3. setup.s의 임시 GDT·A20·8259 재프로그래밍과 head.s의 IDT/GDT 재구성·페이징 설정이 "같은 표를 두 번 만드는" 이유를 설명한다.
4. main()의 초기화 함수 9개(mem_init … floppy_init)를 범주(메모리/게이트/장치/스케줄러)로 분류하고 각 함수가 **어떤 자료구조를 채우는지** 말한다.
5. `sti` → `move_to_user_mode` → 첫 `fork()` 까지의 상태 변화를 GDB로 확인한다.

## 읽을 소스 범위 (원본 src 기준, grep -n/sed -n 확인)
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

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도(필수) — 단계별 PE/PG/IF/CPL + 실행 주소·스택**:
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
  "변경되는 데이터"는 CR0·EFLAGS·CS/SS 선택자·ESP, "유지 조건"은 다음 전환 명령까지. IF는 표시 지점 값.
- **모드·선택지 비교 1 — 커널 적재 단계가 실행되는 세그먼트/주소**: bootsect(0x07c0→0x9000) / setup(0x9020) / system(0x1000→0x0000). 각 단계의 적재자(BIOS / bootsect / bootsect+setup 이동), 크기 제한(512B / 4섹터 / SYSSIZE 0x3000 클릭), 관련 줄.
- **모드·선택지 비교 2 — 하드웨어 IRQ 0~15 전체**: setup.s:176-179에서 전부 마스크한 뒤 초기화 함수가 **열어주는** IRQ만 표시: IRQ0 타이머(sched.c:410), IRQ1 키보드(console.c:684), IRQ2 캐스케이드(traps.c:205, hd.c:347), IRQ3/4 시리얼(serial.c:43), IRQ6 플로피(floppy.c:461), IRQ13 FPU(traps.c:206), IRQ14 HD(hd.c:348). 나머지(5,7,8-12,15)는 마스크 유지. 열린 IRQ와 설치된 게이트 번호(0x20+n)·게이트 종류(intr/trap)를 같은 표에.
- **모드·선택지 비교 3 — main()이 설치하는 게이트 종류**: set_trap_gate / set_intr_gate / set_system_gate 세 매크로 전부와 어느 함수가 어느 것을 쓰는지(traps.c:185-207, sched.c:409-411, hd.c:346, floppy.c:460, serial.c:39-40, console.c:683). 02회차의 게이트 비교를 "누가 언제"로 확장.

## 120분 운영안
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문, 15회차 지도 |
| 03–06 | 12 | 디스크 이미지 배치, 메모리 지도, 적재 단계 비교 |
| 07–11 | 18 | bootsect.s: 복사·setup 적재·system 적재·jmpi |
| 12–17 | 20 | setup.s: BIOS 파라미터·cli·이동·임시 GDT·A20·8259·lmsw |
| 18–23 | 18 | head.s: 세그먼트·스택·IDT/GDT 재구성·페이징·main 호출 프레임 |
| 24–30 | 20 | main(): 메모리 경계, 초기화 9함수 범주, IRQ 비교, sti, move_to_user_mode, 첫 fork |
| 31–36 | 17 | 상태 변화도 종합 + 강사 시연 A/B/C |
| 37–40 | 10 | 관찰 vs 추론, 이해 확인, 정리·04회차 예고 |

## 슬라이드 계획
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 제목·핵심 질문 | "부트 섹터 512바이트에서 main()까지 CPU 상태는 어떻게 바뀌는가?" 네 비트(PE/PG/IF/CPL)를 오늘의 추적 대상으로 제시. | 제목 |
| 02 | 15회차 지도 | 고정 표, 03 강조. 02(표 구조)→03(표가 만들어지는 때)→04(게이트 통과). | 지도 |
| 03 | 디스크 이미지의 배치 | Makefile:41-42 `tools/build bootsect setup system`. 그림: 섹터1 bootsect(510B+0xAA55, bootsect.s:249-253) / 섹터2-5 setup(SETUPLEN 4) / 섹터6- system. | 배경 |
| 04 | 메모리 지도 (적재 전후) | 그림: 0x7c00 → 0x90000(bootsect), 0x90200(setup), 0x10000(system) → 0x00000(이동 후), 0x90000-0x901FF(BIOS 파라미터), 0x9FF00(스택). bootsect.s:34-39 상수 인용. | 배경 |
| 05 | 적재 단계 비교 | 비교 1: bootsect/setup/system — 적재자, 주소, 크기 한계, 실행 모드(16비트 real / 16비트 real / 32비트 protected), 어셈블러(as86/as86/GNU as). | 비교 |
| 06 | 추적 대상 네 비트 다시 보기 | 1회차 18장 참조표 재게시: PE(CR0.0), PG(CR0.31), IF(EFLAGS.9), CPL(CS.RPL). 오늘 표의 열 머리글. | 배경 |
| 07 | bootsect.s: 자기 복사 | bootsect.s:46-62 코드. `rep movw` 256워드, `jmpi go,INITSEG`, 스택 0x9000:0xFF00. 상태: CS 0x07c0→0x9000, SS:SP 설정. | 코드 |
| 08 | bootsect.s: setup 적재 | bootsect.s:67-79 코드. `int 0x13` ah=2, 섹터 2부터 4개를 ES:BX=0x9000:0x0200에. 실패 시 리셋·재시도 무한루프(주석 21-23). | 코드 |
| 09 | bootsect.s: "Loading system ..." | bootsect.s:92-110 코드 + 메시지 원문(244-247). `int 0x10` ah=0x13. **QEMU 캡처**: 부팅 직후 이 문자열이 찍힌 화면(각주: lab, QEMU i386). | 코드·캡처 |
| 10 | bootsect.s: system 적재 루프 | bootsect.s:151-196 read_it 흐름도(강사 참조): 64KB 경계·트랙·헤드 처리. 코드 전체를 읽지 않고 "ES가 0x1000씩 전진"만 짚는다. | 코드 |
| 11 | bootsect.s: 루트 장치와 setup 점프 | bootsect.s:117-139: root_dev가 0이면 sectors 수로 플로피 종류 결정, `jmpi 0,SETUPSEG`. 상태: CS=0x9020, 여전히 real, IF=1. | 코드 |
| 12 | setup.s: BIOS에게 묻기 | setup.s:36-105 표: 커서→[0], 확장메모리(int 0x15 ah=0x88)→[2], 비디오→[4..12], hd0→[0x80], hd1→[0x90]. main.c:58-60이 같은 주소를 읽는다는 연결. | 코드 |
| 13 | setup.s: `cli`와 system 이동 | setup.s:109 `cli`(IF=0, 이제 BIOS 인터럽트 사용 불가) → setup.s:113-126 do_move: 0x10000→0x00000 64KB씩, 0x90000 직전까지. "왜 0으로 옮기는가"(head.s:10-12 주석). | 코드 |
| 14 | setup.s: 임시 GDT·IDT | setup.s:130-134 `lidt idt_48`(limit 0) / `lgdt gdt_48`; setup.s:205-224 원문: code/data 8Mb, base 0. 02회차 head.s GDT(16Mb)와 나란히 — "표는 두 번". | 코드 |
| 15 | setup.s: A20과 8259 | setup.s:138-144 A20(8042 0xD1/0xDF); setup.s:154-179 ICW1-4로 IRQ를 0x20-0x2F로 옮기고 마스크 0xFF. `.word 0x00eb,0x00eb` = jmp $+2 지연. | 코드 |
| 16 | setup.s: `lmsw`와 `jmpi 0,8` | setup.s:191-193 3줄. 상태: PE=1, 그 다음 far jump로 CS=0x0008(임시 GDT 1번), EIP=0 → 32비트 코드. 1회차 25-26장 복습. | 코드 |
| 17 | 상태도(중간): real → protected | BIOS~setup 끝까지의 PE/PG/IF/CPL 행만 표시. 전환 원인 줄 번호. "CPL은 real mode에서 정의되지 않음"을 '—'로. | 상태도 |
| 18 | head.s: 첫 32비트 명령 | head.s:17-23: ds/es/fs/gs=0x10, `lss _stack_start,%esp`(sched.c:67-72 user_stack 끝, ss=0x10). 상태: 커널 스택 생김. | 코드 |
| 19 | head.s: IDT/GDT 다시 만들기 | head.s:24-31, 78-93, 105-107. setup_idt는 256개 전부 ignore_int(0x8E00), setup_gdt는 `lgdt`뿐. 재로드 이유(02회차 상태도 1). 그 뒤 A20 검사 루프(33-36). | 코드 |
| 20 | head.s: CR0와 x87 | head.s:43-49, 54-65: `andl $0x80000011`(PG,PE,ET 보존), `orl $2`(MP), check_x87. CR0 전체 값이 FPU 유무로 달라짐 — 시연에서 관찰할 값. | 코드 |
| 21 | head.s: main 호출 프레임 | head.s:135-144 코드: `pushl $0`×3(main 인수), `pushl $L6`(복귀), `pushl $_main`, `jmp setup_paging`. setup_paging의 `ret`(218)이 `_main`을 pop → main 진입. "call이 아니라 ret로 들어간다". | 코드 |
| 22 | head.s: setup_paging | head.s:198-218 코드: pg_dir(0x0)~pg3 5페이지 클리어, pg_dir[0..3]=pgN+7, 0xfff007부터 거꾸로 채움(16MB identity), CR3=0, CR0.PG=1. 그림: pg_dir이 startup 코드를 덮어씀(head.s:10-12). 상태: PG=1. | 코드 |
| 23 | 상태도(중간): head.s 구간 | PE=1 유지, PG 0→1(217), IF 0 유지, CPL 0, 스택 생성(23), CS 0x0008 유지. | 상태도 |
| 24 | main(): setup이 남긴 값 읽기와 메모리 경계 | main.c:58-60, 110-122: ROOT_DEV, drive_info, memory_end=1MB+EXT_MEM_K, 상한 16MB, buffer_memory_end 1/2/4MB 규칙. 그림: [0,1MB) 커널 / [1MB,buffer_end) 버퍼 / [main_memory_start,memory_end) 페이지 풀. | 코드 |
| 25 | main(): 초기화 9함수 범주표 | main.c:126-135 순서대로: 메모리(mem_init) / 게이트(trap_init) / 장치 표(blk_dev_init, chr_dev_init=빈 함수, tty_init) / 시간(time_init) / 스케줄러(sched_init) / 버퍼(buffer_init) / 블록 장치(hd_init, floppy_init). 각 함수의 "채우는 자료구조" 한 칸씩. | 배경 |
| 26 | mem_init과 trap_init | memory.c:399-411: mem_map 전부 USED(100) → [start,end)만 0. traps.c:181-208: 0-16 개별, 17-47 reserved, 45 irq13, 39 parallel; IRQ2/13 해제. | 코드 |
| 27 | sched_init | sched.c:385-412: GDT 4·5번 TSS0/LDT0(02회차 30장 캡처 재사용), task[1..63]=NULL, NT 클리어, `ltr(0)`/`lldt(0)`, 8253 LATCH(sched.c:46), 게이트 0x20(timer), IRQ0 해제, 게이트 0x80(system_call, DPL3). | 코드 |
| 28 | 비교 2: IRQ 0~15 전체와 열리는 순서 | 표 16행: 마스크 초기값(setup.s:176-179 전부 1) → 어느 함수가 어느 비트를 0으로(traps/sched/con/rs/hd/floppy). 게이트 번호·종류. 미사용 IRQ 명시. | 비교 |
| 29 | 비교 3: main()이 설치하는 게이트 3종 | set_trap_gate(15,dpl0) / set_intr_gate(14,dpl0) / set_system_gate(15,dpl3) — 사용 함수·벡터 목록. "왜 timer는 intr, 키보드는 trap인가"는 04·13회차로 넘김(사실만 표시). | 비교 |
| 30 | buffer_init·hd_init·floppy_init | buffer.c:348-381: 헤더는 앞에서, 데이터는 buffer_end에서 거꾸로, 640KB-1MB 구멍 회피(372-373); hd.c:343-349, floppy.c:457-462: request_fn 등록 + 게이트 + IRQ 해제. 상세는 11회차. | 코드 |
| 31 | `sti()`와 move_to_user_mode | main.c:136-137, system.h:1-14, 16. iret 프레임 그림(0x17, esp, eflags, 0x0f, 1f). 상태: IF=1, CPL 0→3, CS 0x0008→0x000f, SS 0x10→0x17, ESP 값 그대로(같은 user_stack). | 코드 |
| 32 | 첫 fork()와 pause() | main.c:23-26 inline `_syscall0`(unistd.h:133-145 `int $0x80`), main.c:138-148. 왜 inline인가(main.c:11-22 주석: 커널 공간 fork는 COW 없음 → 스택 사용 금지). system_call.s:208-219 → copy_process는 06회차. sys_pause(sched.c:144-149). | 코드 |
| 33 | 상태 변화도(종합): 부트 섹터에서 fork까지 | 위 12행 표 전체. PE/PG/IF/CPL + CS:EIP + 스택 + 전환 원인 줄. 각 비트가 바뀌는 횟수를 세어 본다(PE 1회, PG 1회, IF 2회, CPL 1회). | 상태도 |
| 34 | 시연 A: QEMU `-S` 직후부터 setup까지 | 캡처: QEMU 모니터 `info registers`를 (1) 정지 직후, (2) `b *0x7c00` 중단, (3) `b *0x90200`(setup) 중단에서 — `CR0=00000010`(PE=0), EFL의 IF, CS 값 변화. 각주: 모니터 출력은 QEMU 형식. | 시연·캡처 |
| 35 | 시연 B: PE·PG 켜지는 순간 | GDB `b *0x0`(head 시작, 페이징 전) → `p/x $cr0` → `b *setup_paging+N`(`ret` 직전) → `si` → `p/x $cr0` 비트31. 모니터 `info registers`의 `CR0=8000xxxx` 대조. 대체: 사전 캡처. | 시연·캡처 |
| 36 | 시연 C: main → sti → 사용자 모드 → fork | `b main`, `b *(move_to_user_mode 직후 1f 라벨)` 또는 main.c:138 줄 중단 → `info registers`: eflags IF=1, cs=0x000f, ss=0x0017; `x/8xw $esp`. `si`로 `int $0x80` 통과 직후 cs=0x0008, esp=TSS esp0 근처. | 시연·캡처 |
| 37 | 관찰 vs 추론 | 캡처로 본 것(CR0, CS/SS, EFLAGS, 스택 덤프) / 추론한 것(BIOS 내부, int 0x13 동작, CPU 내부 캐시, iret의 권한 검사). lab과 src 차이(심볼·줄 번호). | 배경 |
| 38 | 이해 확인 질문 | 6문항, 정답 포함(아래). | 질문 |
| 39 | 정리 | 세 단계·두 번의 GDT·네 비트의 전환 횟수·main의 9함수·첫 fork. 핵심 질문의 답: "PE는 setup.s:192, PG는 head.s:217, IF는 setup.s:109에서 0·main.c:136에서 1, CPL은 system.h:8에서 3". | 정리 |
| 40 | 04회차 예고 | "write(1, ...) 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?" — 오늘 설치한 게이트 0x80을 통과하는 순간. | 정리 |

## 강사 시연
- **A. 실주소 모드 구간 관찰** (34장)
  - 명령: `qemu-system-i386 ... -s -S` + QEMU 모니터(`-monitor stdio` 또는 Ctrl-Alt-2). GDB `target remote :1234` → `b *0x7c00` → `c` → 모니터 `info registers`; `b *0x90200` → `c` → 모니터 `info registers`.
  - 관찰: `CR0=` 비트0=0, `EFL=` IF 비트(0x200), `CS =07c0`/`9020`, `SS:SP`.
  - 기대 출력: 0x7c00에서 CS=0x07c0(또는 BIOS에 따라 0000:7c00), 0x90200에서 CS=0x9020, 스택 0x9000:0xFF00(bootsect.s:61-62). IF=1(아직 cli 전).
  - 대체: 사전 캡처 3장(기존 기록 표시). 주의: BIOS(SeaBIOS)가 0x7c00으로 점프하는 방식은 BIOS 구현에 따라 CS:IP 표기가 다를 수 있음을 각주.
- **B. PE·PG 전환 순간** (35장)
  - 명령: `b *0x0`(head.s startup_32, setup.s:193 직후) → `c` → `p/x $cr0`(비트0=1, 비트31=0); `b *setup_paging`(lab 심볼) → `c` → `si`를 `ret`(head.s:218) 직전까지 → `p/x $cr0` → 비트31=1.
  - 관찰: CR0 비트0, 비트31; CR3=0; 그 다음 `si` 한 번으로 EIP가 `main`이 되는지(ret이 _main을 pop).
  - 기대 출력: cr0 하위 바이트 0x11 또는 0x13/0x15(FPU 여부, head.s:43-61), 페이징 후 0x8000xxxx. 전체 값은 관찰 결과로만.
  - 대체: 사전 캡처. 주소 0 근처는 페이징 후 pg_dir로 덮이므로(head.s:10-12) 중단점은 반드시 페이징 전에 소비하고 삭제(`d`).
- **C. main → 사용자 모드 → 첫 fork** (36장)
  - 명령: `b main` → `c` → `info registers`(cs 0x0008, IF=0) → `b init/main.c:138`(lab 줄 번호 확인) → `c` → `info registers`(cs 0x000f, ss 0x0017, IF=1) → `x/8xw $esp` → `si`로 `int $0x80` 진입 → `info registers`(cs 0x0008, esp가 init_task 페이지 끝 근처, sched.h:128 esp0).
  - 관찰: CPL 전환이 CS 하위 2비트로 보임; ESP가 move_to_user_mode 전후로 **같은 값**(system.h:2,4)이고 int 0x80 뒤에만 esp0로 바뀜.
  - 기대 출력: 위. `fork` 내부(copy_process)로는 들어가지 않고 `finish`로 빠져나와 eax(부모 0이 아님)만 확인.
  - 대체: 사전 캡처 3장.
- 공통 각주: "lab/(yuan-xy/Linux-0.11 기반 수정본), QEMU i386 TCG, SeaBIOS. 줄 번호·심볼은 lab 기준, 슬라이드 인용은 src/ 원본."

## 이해 확인 질문과 정답
1. bootsect가 자신을 0x90000으로 옮기는 이유는? — system을 0x10000부터 적재하고 setup이 다시 0x00000으로 옮길 때 자리를 비우기 위해(bootsect.s:10-11 주석, setup.s:113-126).
2. PE 비트를 1로 만드는 명령과 파일:줄은? — `lmsw ax`, setup.s:192. 그 직후 `jmpi 0,8`로 32비트 코드 세그먼트 진입(193).
3. GDT를 두 번 만드는 이유는? — setup.s:205-216 임시 표는 0x9xxxx에 있어 버퍼 영역에 덮일 수 있고 8Mb 한계; head.s:234-238이 커널 이미지 안의 16Mb 표로 교체(head.s:96-103 주석, 02회차).
4. main()은 call로 호출되는가? — 아니오. head.s:140 `pushl $_main` 뒤 setup_paging의 `ret`(218)이 pop하여 진입. 복귀 주소는 L6 무한루프(142-143).
5. IF가 0에서 1이 되는 지점은? — main.c:136 `sti()`. 그 전에는 setup.s:109 `cli` 이후 줄곧 0 (8259 마스크도 0xFF, setup.s:176-179).
6. move_to_user_mode 뒤 ESP 값은 바뀌는가? — 아니오. 현재 esp를 push했다가 iret으로 그대로 복원(system.h:2,4). SS만 0x10→0x17. 커널 스택(esp0)은 다음 인터럽트/시스템 콜 때 TSS에서 로드.

## 처음 등장하는 용어
부트 섹터 서명 0xAA55, `int 0x13`/`int 0x10`/`int 0x15`(BIOS 서비스), INITSEG/SETUPSEG/SYSSEG, `jmpi`, A20, 8042, 8259A(ICW, 마스크), `lmsw`, identity mapping, pg_dir/pg0~pg3, CR3, `lss`, user_stack/stack_start, task_union, mem_map, request[], buffer_head, LATCH/8253, `_syscall0`, inline 시스템 콜, COW(예고만).

## 주의: 흔한 오해 / 말하지 말아야 할 것
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

---

# 04. 인터럽트·예외·시스템 콜

## 핵심 질문
`write(1, ...)` 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?

## 학습 목표 (3~5개)
1. IDT 항목(게이트)이 "번호 → 커널 진입점 + 권한 조건"을 저장하는 표임을 설명하고, `set_intr_gate`/`set_trap_gate`/`set_system_gate`의 차이를 비트(type, DPL) 수준에서 말한다.
2. `int $0x80`이 CPU에 일으키는 상태 변화(CPL 3→0, SS:ESP 교체, 프레임 push)를 스택 그림으로 그린다.
3. `lib/write.c` → `_syscall3` → `_system_call` → `sys_call_table[4]` → `sys_write` → `ret_from_sys_call` → `iret`까지 호출 순서를 소스 줄 번호와 함께 추적한다.
4. 하드웨어 인터럽트(타이머·키보드), CPU 예외(0~16), 소프트웨어 인터럽트(0x80)가 **같은 IDT 메커니즘**을 쓰되 진입 코드(`asm.s`/`system_call.s`)와 복귀 경로가 다른 이유를 설명한다.
5. GDB에서 `system_call`에 멈춰 `int 0x80`이 쌓은 프레임(EIP/CS/EFLAGS/OLDESP/OLDSS)을 직접 읽는다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
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

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 (필수 1장, 슬라이드 18)**: 한 태스크의 "실행 문맥" 상태 — `사용자(CPL3, SS=0x17)` → `[int 0x80]` → `커널 진입 프레임만 있음(CPL0, SS=0x10, ESP=tss.esp0 기준)` → `[push ds/es/fs/edx/ecx/ebx]` → `커널 C 호출 가능` → `[call sys_write]` → `C 함수 실행` → `[ret; pushl %eax]` → `ret_from_sys_call` → `[pop 7개 + iret]` → `사용자(CPL3)`. 각 화살표에 변하는 데이터(ESP, CS, DS, EAX)와 유지 조건(IF, 커널 스택 위치)을 적는다.
- **모드·선택지 비교 (필수 1장, 슬라이드 11)**: 범위 = "IDT에 넣을 수 있는 게이트 종류"로 한정. 선택지: 인터럽트 게이트(type 14) / 트랩 게이트(type 15) / 태스크 게이트(type 5). 비교 축: 0.11 사용 여부, IF 자동 클리어 여부, DPL, 사용하는 매크로, 관련 소스. 태스크 게이트는 "0.11은 사용 안 함"으로 명시.
- **보조 비교 (슬라이드 12)**: 범위 = "게이트 DPL" — DPL 0(사용자 `int n` 금지, #GP) vs DPL 3(허용). `set_system_gate`를 쓴 번호는 3,4,5,0x80 네 개뿐임을 `trap_init`/`sched_init`에서 확인.
- **보조 비교 (슬라이드 24)**: 범위 = "IDT 진입 후 레지스터 저장 코드" — `system_call.s`(syscall·timer) / `asm.s no_error_code` / `asm.s error_code` / `page.s` 네 경로의 push 목록·호출 규약·복귀 경로. CPU 모드·권한 비교와 섞지 않는다.

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문, 15회차 지도에서 위치(03 초기화 뒤, 05 스케줄링 앞) |
| 03–07 | 15 | 배경: 사용자 코드는 왜 커널 함수를 직접 못 부르는가, 이벤트 세 종류, IDT 복습 |
| 08–12 | 18 | 게이트 설명자 비트, `_set_gate` 매크로, 게이트 종류 비교, DPL 비교 |
| 13–17 | 20 | `write()` 사용자 쪽: `_syscall3` 전개, `__NR_write`, `int $0x80`이 쌓는 프레임 |
| 18–23 | 20 | 상태 변화도, `_system_call` 한 줄씩, `sys_call_table`, `sys_write`, `ret_from_sys_call`, iret |
| 24–28 | 15 | 예외·하드웨어 인터럽트 경로 비교: `asm.s`, `trap_init`, `timer_interrupt`, PIC |
| 29–36 | 20 | 강사 시연 A/B/C (GDB 프레임 관찰, `sys_write` 반환값, 0으로 나누기 예외) + 캡처 |
| 37–40 | 5 | 질문의 답, 오해 정리 |
| 41–42 | 2 | 이해 확인 질문, 정리·06 예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약 | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 04. 인터럽트·예외·시스템 콜 | 제목과 핵심 질문 "`write(1, ...)` 한 줄이 어떻게 커널 코드에 도착하고 돌아오는가?". 오늘 끝에 GDB 화면으로 답한다고 예고. | 제목 |
| 02 | 15회차 지도 | 15회차 표에서 04 강조. 03(초기화: `trap_init`/`sched_init`이 IDT를 채움)과 05(타이머 인터럽트가 스케줄러를 부름)의 연결선 표시. | 지도 |
| 03 | 왜 `call sys_write`가 안 되는가 | 사용자 CS=0x0f(LDT, CPL3)에서 커널 코드 세그먼트 0x08(DPL0)로의 far call은 #GP. CPL이 낮은 쪽으로 가려면 CPU가 허락한 통로(게이트)만 가능. 1~2회차의 CPL/DPL 표 재사용. | 배경 |
| 04 | 세 가지 진입 원인 | 하드웨어 인터럽트(장치·PIC, 번호 0x20~0x2F), CPU 예외(0~16, 명령 실행 중 발생), 소프트웨어 인터럽트(`int n` 명령, 0x80). 공통점: 번호 하나로 IDT를 찾는다. 차이: 발생 시점과 오류 코드 유무. | 배경 |
| 05 | IDT 한 항목 = 8바이트 게이트 | 2회차 IDT 복습. `boot/head.s:232` `_idt: .fill 256,8,0`, `idt_descr`(222–224), `setup_idt`(78–93)가 256개 전부 `ignore_int`로 채움. 그림: 선택자 0x0008 + 오프셋 + P/DPL/type 비트. | 코드 |
| 06 | `ignore_int`: 기본 핸들러 | `boot/head.s:150–170` 코드. "Unknown interrupt" 출력 후 iret. 수업 시작 시 모든 번호가 여기로 간다는 점 → 이후 `trap_init`/`sched_init`/장치 init이 덮어씀. | 코드 |
| 07 | 누가 언제 IDT를 덮어쓰는가 | `init/main.c:127` `trap_init()`, `:132` `sched_init()`, `tty_init`→`con_init`(`console.c:683`), `rs_init`(`serial.c:39–40`), `hd_init`(`hd.c:346`), `floppy_init`(`floppy.c:460`). 표: 번호 / 매크로 / 핸들러 / 파일:줄. | 코드 |
| 08 | `_set_gate` 매크로 해부 | `include/asm/system.h:22–31`. `"a"(0x00080000)` + `movw %dx,%ax` → 하위 4바이트 = 선택자 0x0008 ‖ 오프셋 하위 16비트. 상위 4바이트 = 오프셋 상위 16비트 ‖ `0x8000+(dpl<<13)+(type<<8)`. 비트 그림으로 P=1, DPL, type 위치 표시. | 코드 |
| 09 | 세 매크로의 차이는 두 숫자뿐 | `system.h:33–40`. `set_intr_gate` = (14,0), `set_trap_gate` = (15,0), `set_system_gate` = (15,3). type 14 vs 15 = 진입 시 IF 클리어 여부, DPL 0 vs 3 = 사용자 `int n` 허용 여부. | 코드 |
| 10 | 게이트 설명자 비트 배치 | 상위 워드 `0x8E00`(intr, DPL0) / `0x8F00`(trap, DPL0) / `0xEF00`(trap, DPL3) 계산 과정. `head.s:82`의 `$0x8E00`과 `_set_gate`의 식이 같은 값을 만든다는 것을 확인. | 코드 |
| 11 | 비교: IDT 게이트 종류 | 범위 = IDT에 넣을 수 있는 게이트. 표: 인터럽트 게이트(type 14) — 0.11 사용(0x20 타이머, 0x23/0x24 시리얼, 0x2E hd), 진입 시 IF=0 / 트랩 게이트(type 15) — 사용(예외 0~16, 0x21 키보드, 0x26 플로피, 0x80), IF 유지 / 태스크 게이트(type 5) — 0.11 미사용, TSS 전환. 각 행에 관련 소스 줄. | 비교 |
| 12 | 비교: 게이트 DPL 0 vs 3 | 범위 = 게이트 DPL. DPL0: 사용자 모드 `int n` 실행 시 #GP(13번) — 장치 IRQ·대부분 예외. DPL3: 허용 — `trap_init:188–190` int3/overflow/bounds, `sched_init:411` 0x80. 하드웨어 발생 인터럽트는 DPL 검사를 하지 않는다는 점 명시. | 비교 |
| 13 | 사용자 쪽 출발점: `lib/write.c` | `lib/write.c:7–10` 전체(4줄). `#define __LIBRARY__`가 `unistd.h:58`의 `#ifdef __LIBRARY__` 블록을 연다. `write`라는 함수는 매크로 전개 결과임을 보임. | 코드 |
| 14 | `_syscall3` 전개 | `include/unistd.h:172–183`. 전개 결과를 손으로 쓴 C 코드: `int write(int fd,const char *buf,off_t count){ long __res; asm("int $0x80":"=a"(__res):"0"(4),"b"(fd),"c"(buf),"d"(count)); ... }`. 레지스터 약속 표: EAX=번호, EBX/ECX/EDX=인자 1/2/3. | 코드 |
| 15 | `__NR_write = 4` 와 표의 4번 칸 | `unistd.h:60–64`와 `sys.h:74–75`를 나란히. `sys_call_table[4] == sys_write`. `system_call.s:61` `nr_system_calls = 72` = 표 길이(0~71, 마지막 `sys_setregid`=71, `unistd.h:131`). | 코드 |
| 16 | `int $0x80` 실행 순간 CPU가 하는 일 | 그림: IDT[0x80] 읽기 → DPL3 ≥ CPL3 통과 → TSS에서 ss0/esp0 로드(05회차의 `tss.esp0`) → 커널 스택에 SS, ESP, EFLAGS, CS, EIP 5개 push → CS=0x08, EIP=`_system_call`. 트랩 게이트이므로 IF 유지. | 배경 |
| 17 | 프레임 그림: `system_call.s:17–31` | 주석에 적힌 12개 슬롯을 그대로 그림으로. 위 5개(EIP~OLDSS)는 CPU가, 아래 7개(DS~EAX)는 코드가 push. `OLDESP = 0x28`, `OLDSS = 0x2C` 오프셋 정의(`:35–46`). GDB 시연에서 이 그림과 `x/12xw $esp`를 대조할 것 예고. | 코드 |
| 18 | 상태 변화도: 한 번의 시스템 콜 | 상태: 사용자 실행(CPL3, SS 0x17) → 커널 진입 프레임(CPL0, SS 0x10, 레지스터 미저장) → 커널 C 호출 가능(DS/ES=0x10, FS=0x17) → `sys_write` 실행 중 → 반환값 스택 저장(`pushl %eax`) → `ret_from_sys_call`(시그널 검사) → 사용자 실행. 각 전환의 원인 명령, 변경 데이터(ESP/CS/DS/EAX), 유지 조건(IF, 커널 스택 = task 페이지 끝). | 상태도 |
| 19 | `_system_call` 한 줄씩 (1) | `system_call.s:80–94`. 81–82 범위 검사→`bad_sys_call`(72–74, eax=-1). 83–88 push ds/es/fs/edx/ecx/ebx — "ebx,ecx,edx를 push하는 것이 C 인자 전달". 89–93 ds/es=0x10, fs=0x17. 94 `call _sys_call_table(,%eax,4)` = `sys_call_table[eax]()`. | 코드 |
| 20 | `sys_write`에 도착 | `fs/read_write.c:83–103`. 인자 `(fd,buf,count)` = 스택의 ebx/ecx/edx. fd 1 → `current->filp[1]` → 문자 장치면 `rw_char(WRITE,…)`(`:95–96`) → 13회차. 반환값은 EAX로 돌아옴. 오늘은 분기 조건만, 내부는 보지 않음. | 코드 |
| 21 | `_system_call` 한 줄씩 (2) | `system_call.s:95–100`. 95 `pushl %eax`(반환값 저장, 프레임 슬롯 EAX). 96–100 `current->state != 0` 또는 `counter == 0`이면 `reschedule`(76–78: ret_from_sys_call을 push하고 `jmp _schedule`) → 05회차 연결. | 코드 |
| 22 | `ret_from_sys_call` | `system_call.s:101–128`. 102–104 task[0]이면 건너뜀. 105–108 CS=0x0f, OLDSS=0x17 — "사용자에서 왔을 때만 시그널 처리". 109–120 `signal & ~blocked` 최하위 비트 → `do_signal`(10회차). 121–128 pop 7개 → `iret`. | 코드 |
| 23 | `iret`가 되돌리는 것 | iret는 EIP/CS/EFLAGS를 pop하고 CPL이 바뀌면 ESP/SS도 pop. 범용 레지스터는 되돌리지 않음 → 그래서 121–127의 pop이 먼저. EAX만은 `sys_write` 반환값으로 바뀐 채 돌아감 → `_syscall3`의 `__res`. | 코드 |
| 24 | 비교: 진입 후 레지스터 저장 코드 4종 | 범위 = IDT 진입 직후 저장 코드. `system_call.s _system_call`(ds/es/fs/edx/ecx/ebx, eax는 반환값 슬롯) / `_timer_interrupt`(176–183, eax까지 push) / `asm.s no_error_code`(19–39, 전 레지스터 + 가짜 오류코드 0) / `asm.s error_code`(97–117, CPU가 push한 오류코드를 eax로 교환) / `page.s`(14–27, CR2 push). 복귀: syscall·timer는 `ret_from_sys_call`, 나머지는 자체 pop+iret. | 비교 |
| 25 | `trap_init`: 예외 0~16 | `kernel/traps.c:181–208`. 표: 0 divide_error, 3/4/5 system_gate, 7 device_not_available(system_call.s:148), 13 general_protection, 14 page_fault(page.s), 16 coprocessor_error. 17~47을 `reserved`로 채운 뒤 45(irq13), 39(parallel)만 덮음(202–207). | 코드 |
| 26 | 오류 코드 있는 예외 vs 없는 예외 | `asm.s:19–51`(no_error_code: `pushl $0`으로 가짜 코드)과 `97–129`(error_code: `xchgl %eax,4(%esp)`). 둘 다 `lea 44(%esp)`로 프레임 포인터를 두 번째 인자로 → `do_xxx(long esp, long error_code)`(traps.c:87–100). 8/10/11/12/13/14가 오류 코드 있는 쪽. | 코드 |
| 27 | `die()`: 예외의 끝 | `traps.c:63–85`. esp[0..4] = EIP, CS, EFLAGS, ESP, SS 출력 → 17장 프레임 그림의 상위 5슬롯과 같은 배치. 마지막 `do_exit(11)`. 시연 C에서 실제 출력과 대조. | 코드 |
| 28 | 하드웨어 인터럽트: 타이머와 PIC | `sched.c:406–410` 8253 설정(LATCH=`1193180/HZ`, sched.c:46), `set_intr_gate(0x20,…)`, `outb(inb_p(0x21)&~0x01,0x21)` = IRQ0 마스크 해제. `system_call.s:176–197` `_timer_interrupt`: 189 `incl _jiffies`, 190–191 EOI(0x20→포트 0x20), 192–194 CS 하위 2비트 = CPL을 `do_timer` 인자로. 상세는 05회차. | 코드 |
| 29 | 시연 환경 | `lab/` QEMU i386 + GDB 원격(`target remote`). `src/` 줄 번호와 `lab/` 빌드 심볼은 별개임을 각주(심볼 접두 `_` 유무는 lab 빌드 기준). 실패 시 사전 캡처 사용. | 시연 |
| 30 | 시연 A: `break system_call` | 셸에서 `echo hi` 실행 → `system_call`에서 정지. `p/x $eax`(=4 기대), `p/x $ebx`(=1), `p/x $cs`(=0x8), `p/x $ss`(=0x10). | 시연 |
| 31 | 캡처 A-1: 진입 직후 레지스터 | GDB 로그 캡처. 각주: lab 빌드, 수정 없음, QEMU `-s -S`. 관찰: EAX=4=`__NR_write`, ECX=버퍼 주소(사용자 선형 주소), EDX=길이. | 캡처 |
| 32 | 캡처 A-2: `x/5xw $esp` | 진입 직후 커널 스택 5워드 = EIP, CS(0x0f), EFLAGS, OLDESP, OLDSS(0x17). 17장 그림과 나란히. "CS 하위 2비트 = 3 = 왔던 곳의 CPL"을 강조. | 캡처 |
| 33 | 시연 B: `sys_write` 반환과 `ret_from_sys_call` | `break sys_write` → `finish` → `p $eax`(쓴 바이트 수 기대). `break ret_from_sys_call` → `x/12xw $esp`로 12슬롯 전체 확인, EAX 슬롯 = 반환값. `stepi`로 `iret` 직후 `p/x $cs`=0x0f, `p/x $ss`=0x17. | 시연 |
| 34 | 캡처 B: iret 전후 | iret 직전/직후 레지스터 캡처 두 장 나란히. 변한 것: CS, SS, ESP, EIP. 안 변한 것: EAX(반환값). 각주: 환경·수정 여부. | 캡처 |
| 35 | 시연 C: 예외 — 0으로 나누기 | 사용자 프로그램(lab에 미리 넣은 `div0` 또는 셸에서 재현 가능한 것)으로 #DE 유발. `break do_divide_error` → `p/x *(long*)esp@5`로 EIP/CS/EFLAGS/ESP/SS, 콘솔의 `die()` 출력과 대조. 대체: 사전 캡처. | 시연 |
| 36 | 캡처 C: `divide error: 0000` | QEMU 콘솔 캡처(`traps.c:68–70` 출력 형식). EIP의 세그먼트 0x000f, SS 0x0017 확인. 각주: 테스트 프로그램은 lab 추가분(원본 src에 없음). | 캡처 |
| 37 | 질문의 답: `write(1,…)`의 왕복 | 한 장 흐름도: `write()`(lib) → `int $0x80` → IDT[0x80] → `_system_call` → `sys_call_table[4]` → `sys_write` → `pushl %eax` → `ret_from_sys_call` → `iret` → `__res`. 각 화살표에 파일:줄. | 정리 |
| 38 | 같은 메커니즘, 다른 세 입구 | 소프트웨어 `int 0x80`(사용자가 원함, DPL3) / 예외(CPU가 강제, 오류 코드 가능, `die`) / 하드웨어 IRQ(장치가 원함, PIC EOI 필요, 사용자 복귀 시 스케줄 가능). 오늘 본 소스를 세 열로 정리. | 정리 |
| 39 | 흔한 오해 바로잡기 | "`int 0x80`이 함수 호출이다"(아니다: 스택·CPL·세그먼트가 바뀐다), "iret가 모든 레지스터를 복원한다"(5개만), "트랩 게이트는 인터럽트 끔"(반대), "예외=에러"(page_fault는 정상 동작의 일부, 07·08회차). | 정리 |
| 40 | 현대 커널과의 연결(1장만) | x86-64 Linux는 `syscall` 명령과 MSR로 진입하지만 "번호→표→함수, 반환값→레지스터" 구조는 동일. 비교는 14회차에서. | 배경 |
| 41 | 이해 확인 질문 | 아래 "이해 확인 질문과 정답" 4문항. 정답은 클릭 후 표시. | 질문 |
| 42 | 정리와 다음 회차 | 오늘 정리 4줄. 05 예고: "`_timer_interrupt`가 `do_timer`를 불러 `schedule()`로 가면 `ret_from_sys_call`로 돌아오는 태스크가 바뀐다 — 어떻게?" `system_call.s:96–100`의 `reschedule`이 연결 고리. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
공통: `lab/`에서 QEMU를 `-s -S`(gdbstub, 시작 정지)로 띄우고 GDB에서 `target remote :1234`, 커널 심볼 로드. 부팅이 셸까지 간 뒤 중단점 설정. `src/` 줄 번호와 `lab/` 심볼 이름(`_` 접두 유무)은 다를 수 있으므로 시연 전 `info functions system_call`로 확인.

- **A. `int 0x80` 프레임 관찰**
  - 명령: `break system_call` → 게스트 셸에서 `echo hi` → 정지.
  - 관찰: `p/x $eax $ebx $ecx $edx`, `p/x $cs`, `p/x $ss`, `x/5xw $esp`.
  - 기대: EAX=0x4, EBX=0x1, CS=0x8, SS=0x10. 스택 5워드 중 두 번째(CS)=0xf, 다섯 번째(OLDSS)=0x17. (셸의 내부 동작에 따라 `write` 이전에 다른 시스템 콜이 먼저 걸릴 수 있음 → `cond`로 `$eax == 4` 조건 부여.)
  - 대체: 사전 캡처 `build/04-A-frame.png`(없으면 시연 전 만들어 둘 것).
- **B. 반환값과 iret**
  - 명령: `break sys_write`, `finish`, `p $eax`; `break ret_from_sys_call`, `x/12xw $esp`; `stepi` 반복으로 `iret` 통과, `p/x $cs`, `p/x $ss`, `p/x $esp`.
  - 기대: `finish` 후 EAX = 쓴 길이(예: 3 = "hi\n"). 12워드 중 첫 워드 = 같은 값. iret 후 CS=0xf, SS=0x17.
  - 대체: 사전 캡처 2장(iret 전/후).
- **C. 예외 경로(#DE)**
  - 명령: lab에 넣어 둔 0 나누기 사용자 프로그램 실행. `break do_divide_error` → `p/x ((long*)$esp)[2]`(esp 인자) 부근 5워드 덤프, `c`로 콘솔 `die()` 출력 확인.
  - 기대: 콘솔에 `divide error: 0000`, `EIP: 000f:...`, `ESP: 0017:...` 형식(`traps.c:68–70`), 이후 프로세스 종료(`do_exit(11)`), 셸 프롬프트 복귀.
  - 대체: 사전 캡처 콘솔 화면. 테스트 프로그램이 lab에 없으면 시연 C를 생략하고 캡처만 설명.

## 이해 확인 질문과 정답
1. **Q.** `set_system_gate(0x80,…)` 대신 `set_trap_gate(0x80,…)`를 쓰면 사용자 프로그램의 `write()`는 어떻게 되는가? **A.** 게이트 DPL이 0이 되어 CPL3에서의 `int $0x80`이 #GP(13번)를 일으킨다 → `general_protection` → `die()` → `do_exit(11)`. 시스템 콜이 아니라 프로세스 종료가 된다.
2. **Q.** `_system_call`에서 `pushl %ebx; pushl %ecx; pushl %edx` 순서가 아니라 `edx, ecx, ebx` 순으로 push하는 이유는? **A.** C 호출 규약에서 첫 인자가 가장 낮은 주소(ESP 바로 위)에 있어야 하므로 마지막에 push한 ebx가 `sys_write`의 `fd`, 그다음 ecx가 `buf`, edx가 `count`가 된다.
3. **Q.** `iret` 뒤 사용자 코드의 EAX에는 무엇이 있는가? **A.** `sys_write`의 반환값. `pushl %eax`(95)로 프레임의 EAX 슬롯에 저장했다가 `popl %eax`(121)로 꺼낸 값이며, `_syscall3`의 `"=a"(__res)`가 이를 받는다. 음수면 `errno = -__res`.
4. **Q.** 타이머 인터럽트(0x20)는 `set_intr_gate`, 키보드(0x21)는 `set_trap_gate`다. 진입 직후 EFLAGS.IF 값은 각각? **A.** 인터럽트 게이트는 진입 시 IF=0(다른 IRQ 차단), 트랩 게이트는 IF를 그대로 둔다(키보드 핸들러 중 타이머 인터럽트 가능). 소스: `system.h:33–37`, `sched.c:409`, `console.c:683`.

## 처음 등장하는 용어
- **게이트(gate)**: IDT 항목. 번호에 대응하는 진입 주소·코드 세그먼트·DPL·종류를 담는 8바이트.
- **인터럽트 게이트 / 트랩 게이트**: type 14 / 15. 진입 시 IF를 끄는지 여부만 다름.
- **태스크 게이트**: type 5, TSS 전환 방식. 0.11 미사용.
- **DPL(게이트의)**: 소프트웨어 `int n`을 허용하는 최대 CPL.
- **시스템 콜 번호(`__NR_*`)**: `sys_call_table` 인덱스.
- **`sys_call_table`**: 함수 포인터 배열(`fn_ptr`).
- **오류 코드(error code)**: 일부 예외에서 CPU가 추가로 push하는 32비트 값.
- **EOI**: PIC에 "처리 끝" 신호(포트 0x20에 0x20).
- **`jiffies`**: 타이머 틱 수. 05회차 핵심.
- **`ret_from_sys_call`**: 시스템 콜·타이머 공통 복귀 경로.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- `int $0x80`을 "특별한 call"로 설명하지 말 것. 스택이 커널 스택(`tss.esp0`)으로 바뀌고 CPL이 바뀐다는 점이 본질.
- "트랩 게이트는 인터럽트를 끈다"는 반대. 인터럽트 게이트가 IF를 끈다.
- `iret`가 범용 레지스터를 복원한다고 말하지 말 것(1회차 노트와 일관).
- `sys_write`의 내부(`rw_char`, `tty_write`)는 13회차. 오늘은 "도착했다"까지만.
- `do_signal`/시그널 비트 연산(109–120)은 "사용자로 돌아가기 직전에만 검사한다"까지만. 상세는 10회차.
- `page_fault`를 예외 목록에 넣되 "오류"라고 부르지 말 것. 07·08회차에서 정상 동작의 일부로 다룸.
- 하드웨어 인터럽트는 게이트 DPL 검사를 받지 않는다. "DPL0이면 장치 인터럽트가 사용자 모드에서 안 들어온다"고 말하지 말 것.
- `lab/` 심볼명과 `src/` 줄 번호를 섞지 말 것. 캡처에는 lab 기준, 슬라이드 인용은 src 기준.
- 현대 x86-64의 `syscall`/`sysret`·`entry_64.S`를 오늘 설명하지 말 것(14회차).

---

# 05. 태스크와 스케줄링

## 핵심 질문
타이머 틱 한 번에 실행 중인 태스크가 어떻게 바뀌는가?

## 학습 목표 (3~5개)
1. `task_struct`의 앞 세 필드(`state`, `counter`, `priority`)와 `tss`의 역할을 말하고, `task[NR_TASKS]`·`current`·`jiffies`가 어디에 정의되어 있는지 가리킨다.
2. `TASK_RUNNING / INTERRUPTIBLE / UNINTERRUPTIBLE / ZOMBIE / STOPPED` 다섯 상태의 전환 원인을 소스 줄 번호로 짚고, 0.11에서 실제로 `STOPPED`로 들어가는 코드가 없음을 확인한다.
3. `do_timer`가 `counter`를 1 줄여 0이 되면 **사용자 모드에서 온 경우에만** `schedule()`을 부르는 조건(`cpl`)을 설명한다.
4. `schedule()`의 선택 규칙(`state==RUNNING`이고 `counter` 최대)과 재충전 식 `counter = counter/2 + priority`를 손으로 계산한다.
5. `switch_to(n)`가 `ljmp`로 TSS 전환을 일으키며, 이때 CPU가 레지스터 전체를 TSS에 저장·복원함을 GDB로 확인한다(`current` 변화, `jiffies`, `current->counter`).

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| `include/linux/sched.h` | 4–5 | `NR_TASKS 64`, `HZ 100` |
| `include/linux/sched.h` | 19–23 | `TASK_RUNNING 0` … `TASK_STOPPED 4` |
| `include/linux/sched.h` | 51–76 | `struct tss_struct` — esp0/ss0, cr3, eip, eflags, eax…, 세그먼트, ldt, trace_bitmap, i387 |
| `include/linux/sched.h` | 78–107 | `struct task_struct` — 80–85 하드코딩 필드(state/counter/priority/signal/sigaction/blocked), 87–94 pid/father/시간, 96–102 fs 정보, 104 ldt[3], 106 tss |
| `include/linux/sched.h` | 113–134 | `INIT_TASK` — counter 15, priority 15, tss.esp0=`PAGE_SIZE+&init_task`, ss0=0x10, ldt 0x9f/0xc0fa00·0xc0f200 |
| `include/linux/sched.h` | 136–142 | `task[]`, `last_task_used_math`, `current`, `jiffies`, `CURRENT_TIME` |
| `include/linux/sched.h` | 144–147 | `add_timer`, `sleep_on`, `interruptible_sleep_on`, `wake_up` 선언 |
| `include/linux/sched.h` | 149–164 | `FIRST_TSS_ENTRY 4`, `_TSS(n)`, `_LDT(n)`, `ltr`, `lldt`, `str` |
| `include/linux/sched.h` | 165–184 | `switch_to(n)` — `cmpl %%ecx,_current`, `xchgl %%ecx,_current`, `ljmp %0`(TSS 선택자), `clts` |
| `kernel/sched.c` | 46 | `LATCH (1193180/HZ)` |
| `kernel/sched.c` | 53–72 | `union task_union`(task_struct + 4 KiB 스택), `init_task`, `jiffies`, `current`, `task[NR_TASKS]`, `user_stack`/`stack_start` |
| `kernel/sched.c` | 77–92 | `math_state_restore` (참고: `last_task_used_math`) |
| `kernel/sched.c` | 94–142 | `schedule()` — 111–120 alarm·시그널 깨우기, 124–140 선택 루프와 재충전, 141 `switch_to(next)` |
| `kernel/sched.c` | 144–149 | `sys_pause` — `TASK_INTERRUPTIBLE` 후 `schedule()` |
| `kernel/sched.c` | 151–165 | `sleep_on` — `*p = current`, `TASK_UNINTERRUPTIBLE`, 깨어난 뒤 `tmp->state=0` |
| `kernel/sched.c` | 167–186 | `interruptible_sleep_on` — `repeat:` 루프, `*p != current`면 다시 잠 |
| `kernel/sched.c` | 188–194 | `wake_up` — `(**p).state=0; *p=NULL` |
| `kernel/sched.c` | 266–303 | `timer_list`, `add_timer` (참고: 상대 jiffies 연결 리스트) |
| `kernel/sched.c` | 305–336 | `do_timer(long cpl)` — 314–317 utime/stime, 319–329 타이머 리스트, 332–335 counter 감소·cpl 검사·`schedule()` |
| `kernel/sched.c` | 338–346 | `sys_alarm` (jiffies 기준) |
| `kernel/sched.c` | 378–383 | `sys_nice` — priority 감소 |
| `kernel/sched.c` | 385–412 | `sched_init` — TSS0/LDT0 설명자, 나머지 task[] NULL, NT 클리어, `ltr(0)`/`lldt(0)`, 8253 설정, 0x20/0x80 게이트 |
| `kernel/system_call.s` | 48–53 | `state=0`, `counter=4`, `priority=8` 오프셋 (task_struct 앞부분과 일치) |
| `kernel/system_call.s` | 76–78 | `reschedule:` `pushl $ret_from_sys_call; jmp _schedule` |
| `kernel/system_call.s` | 95–100 | 시스템 콜 뒤 `state != 0` 또는 `counter == 0`이면 `reschedule` |
| `kernel/system_call.s` | 176–197 | `_timer_interrupt` — 189 `incl _jiffies`, 192–195 CPL 계산 후 `call _do_timer`, 197 `jmp ret_from_sys_call` |
| `kernel/exit.c` | 20–33 | `release()` — `task[i]=NULL; free_page; schedule()` |
| `kernel/exit.c` | 102–135 | `do_exit` — 130 `current->state = TASK_ZOMBIE`, 133 `schedule()` |
| `kernel/exit.c` | 165–182 | `sys_waitpid`의 `switch((*p)->state)` — `TASK_STOPPED`/`TASK_ZOMBIE` 분기 |
| `kernel/exit.c` | 184–193 | 자식이 아직 살아 있으면 `TASK_INTERRUPTIBLE`로 `schedule()` |
| `fs/buffer.c` | 40, 225, 260 | `sleep_on(&bh->b_wait)`, `sleep_on(&buffer_wait)`, `wake_up(&buffer_wait)` (UNINTERRUPTIBLE 예) |
| `kernel/chr_drv/tty_io.c` | 126, 136, 227 | `interruptible_sleep_on(&queue->proc_list)`, `wake_up(&tty->secondary.proc_list)` (INTERRUPTIBLE 예) |
| `init/main.c` | 138–148 | `fork()` 후 task 0은 `for(;;) pause();` — idle 태스크 |
| `kernel/fork.c` | 82, 85, 131 | `copy_process`가 `TASK_UNINTERRUPTIBLE`→`TASK_RUNNING`으로 두는 순서 (06회차 예고) |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 (필수, 슬라이드 20–21)**: 범위 = `task_struct.state` 값. 상태: RUNNING(0) / INTERRUPTIBLE(1) / UNINTERRUPTIBLE(2) / ZOMBIE(3) / STOPPED(4). 전환 원인과 소스:
  - RUNNING→INTERRUPTIBLE: `sys_pause`(sched.c:146), `interruptible_sleep_on`(:177), `sys_waitpid`(exit.c:187)
  - RUNNING→UNINTERRUPTIBLE: `sleep_on`(sched.c:161); 생성 중 `copy_process`(fork.c:82)
  - INTERRUPTIBLE→RUNNING: 시그널 도착 시 `schedule()` 앞부분(sched.c:117–119), `wake_up`(:191), `interruptible_sleep_on`의 `(**p).state=0`(:180)
  - UNINTERRUPTIBLE→RUNNING: `wake_up`(:191), `sleep_on`의 `tmp->state=0`(:164), `copy_process` 마지막(fork.c:131)
  - RUNNING→ZOMBIE: `do_exit`(exit.c:130)
  - ZOMBIE→소멸: `sys_waitpid`→`release`(exit.c:176, 20–33)
  - STOPPED: 정의(sched.h:23)와 `waitpid`의 case(exit.c:166)만 있고 **진입 코드 없음** — "0.11에 미구현"으로 표시
  - 변경되는 데이터: `state`, `counter`(RUNNING 선택 시 매 틱 감소), 대기 큐 포인터 `*p`. 유지 조건: `schedule()`은 `state==0`인 태스크만 고른다.
- **"실행 중"은 상태 값이 아님**: `current`가 가리키는 태스크 = CPU 점유. `state`에 "실행 중" 값은 없고 RUNNING 중 하나가 `current`일 뿐 — 상태도에 별도 표기.
- **모드·선택지 비교 (필수, 슬라이드 16)**: 범위 = "`schedule()`이 호출되는 경로". 선택지: (a) 타이머 틱에서 `do_timer`→`schedule`(cpl≠0 조건, sched.c:332–335), (b) 시스템 콜 복귀 직전 `reschedule`(system_call.s:95–100, state≠0 또는 counter==0), (c) 태스크 자발 호출 — `sleep_on`/`interruptible_sleep_on`/`sys_pause`/`do_exit`/`sys_waitpid`(sched.c:162,178,147; exit.c:133,188), (d) `release()`(exit.c:29). 비교 축: 누가 부르는가(인터럽트/시스템 콜/커널 함수), 현재 태스크 상태, 복귀 지점(`ret_from_sys_call`인가 호출자 다음 줄인가). 선점 정책이나 CPU 모드와 섞지 않는다.
- **보조 비교 (슬라이드 24)**: 범위 = `sleep_on` vs `interruptible_sleep_on` — 상태 값, 시그널로 깨어나는가, 사용처(buffer.c vs tty_io.c), `repeat` 루프 유무.

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문, 지도(04의 `timer_interrupt`에서 이어짐) |
| 03–08 | 18 | 배경: 태스크란 무엇인가, `task_struct`·`tss_struct`, `task[]`/`current`/`jiffies`, task 0 |
| 09–15 | 22 | 타이머 경로: 8253·`sched_init`, `_timer_interrupt`, `do_timer`, `counter` 감소, cpl 조건 |
| 16–19 | 15 | `schedule()` 호출 경로 비교, `schedule()` 본문, 재충전 식 계산 |
| 20–24 | 17 | 상태 변화도 2장, `sleep_on`/`wake_up`, 비교 |
| 25–28 | 13 | `switch_to`·TSS 전환, `sched_init`의 ltr/lldt, 커널 스택과 `esp0` |
| 29–36 | 20 | 강사 시연 A/B/C + 캡처 |
| 37–40 | 7 | 질문의 답, 오해 정리, 현대 커널 한 줄 |
| 41–42 | 3 | 이해 확인, 정리·06 예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약 | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 05. 태스크와 스케줄링 | 제목과 핵심 질문 "타이머 틱 한 번에 실행 중인 태스크가 어떻게 바뀌는가?". 04의 `_timer_interrupt`에서 `call _do_timer` 다음을 오늘 본다고 연결. | 제목 |
| 02 | 15회차 지도 | 15회차 표에서 05 강조. 04(인터럽트 진입)→05(틱·스케줄)→06(fork가 두 번째 태스크를 만든다). 10(exit/wait: ZOMBIE)과의 점선. | 지도 |
| 03 | 태스크란 커널이 기억하는 한 묶음 | CPU는 하나, 프로그램은 여럿. 각 프로그램의 "멈춘 지점 + 레지스터 + 메모리 + 파일" 묶음을 `task_struct` 하나에 둔다. 1회차 "프로세스"와 같은 것을 0.11 소스는 task라고 부름. | 배경 |
| 04 | `struct task_struct` 전체 | `sched.h:78–107` 전체를 한 화면에, 다섯 구역(80–85 하드코딩, 87–94 pid·시간, 96–102 fs, 104 ldt, 106 tss) 색 구분. "앞 세 필드는 `system_call.s:48–53`의 오프셋과 맞아야 한다"는 주석 강조. | 코드 |
| 05 | `state`, `counter`, `priority` | 80–82 세 줄. state 주석 `-1 unrunnable, 0 runnable, >0 stopped`와 실제 값(sched.h:19–23) 대조. counter = 남은 틱, priority = 재충전 기준. INIT_TASK(113–114)는 둘 다 15. | 코드 |
| 06 | `struct tss_struct` | `sched.h:51–76`. CPU가 태스크 전환 시 저장/복원하는 레지스터 전부 + esp0/ss0(04의 "커널 스택으로 전환" 출처) + cr3 + ldt. 그림: 104바이트 배치 요약. | 코드 |
| 07 | `task[]`, `current`, `jiffies`가 사는 곳 | `sched.c:53–72`. `union task_union` = task_struct와 4 KiB 커널 스택이 한 페이지. `init_task`, `current=&init_task.task`, `task[0]=…`, `jiffies=0`. 그림: 한 페이지 안에서 스택이 위에서 내려오는 모습. | 코드 |
| 08 | task 0은 무엇을 하는가 | `init/main.c:138–148` `fork()` 뒤 `for(;;) pause();`. `sched.c:100–102` 주석: task 0는 idle, 죽지 않고 잠들지 않음. `schedule()`에서 `next=0` 기본값(sched.c:126)이 "아무도 못 뛰면 task 0". | 코드 |
| 09 | 틱의 출처: 8253 | `sched.c:46` `LATCH=1193180/HZ`=11931, `:406–408` 모드 3 설정. HZ=100 → 10 ms마다 IRQ0. `:409` `set_intr_gate(0x20,…)`, `:410` PIC IRQ0 마스크 해제 — 04회차 게이트 표 재사용. | 코드 |
| 10 | `_timer_interrupt` 다시 읽기 | `system_call.s:176–197`. 189 `incl _jiffies`(여기서만 증가), 190–191 EOI, 192–194 `CS(%esp)&3`=CPL을 인자로 push, 195 `call _do_timer`, 197 `jmp ret_from_sys_call`. "복귀 경로가 시스템 콜과 같다"는 점이 스케줄 뒤 복귀를 가능하게 함. | 코드 |
| 11 | `do_timer` (1): 회계 | `sched.c:305–317`. `beepcount`, cpl에 따라 `utime`/`stime` 증가. 그림: 사용자 모드 중 틱 → utime, 커널 모드 중 틱 → stime. | 코드 |
| 12 | `do_timer` (2): 타이머 리스트 | `sched.c:319–331`. `next_timer->jiffies--`, 0 이하가 된 항목의 `fn()` 호출. `add_timer`(272–303)는 상대값 리스트라는 것만 한 줄. 플로피 모터용. | 코드 |
| 13 | `do_timer` (3): counter와 cpl 조건 | `sched.c:332–335` 네 줄. `if ((--current->counter)>0) return; current->counter=0; if (!cpl) return; schedule();`. 핵심: 커널 모드에서 틱이 오면 counter는 0이 돼도 `schedule()`을 **안 부른다** → 커널 코드는 선점되지 않음. | 코드 |
| 14 | 틱 한 번의 데이터 변화 | 표: 틱 전/후 `jiffies`, `current->counter`, `current->utime/stime`. counter가 1→0이 되는 틱에서만 `schedule()`. 시연 A에서 이 표를 실제 값으로 채운다 예고. | 배경 |
| 15 | 시스템 콜 끝에서도 스케줄 검사 | `system_call.s:95–100`. `state != 0`(시스템 콜 안에서 잠들었다 깨어난 경우) 또는 `counter == 0`이면 `reschedule`(76–78) → `ret_from_sys_call`을 반환 주소로 push하고 `jmp _schedule`. `schedule()`의 `ret`가 곧 `ret_from_sys_call`로 감. | 코드 |
| 16 | 비교: `schedule()`이 불리는 네 경로 | 범위 = `schedule()` 호출 지점. (a) `do_timer`(sched.c:335, cpl≠0·counter==0) / (b) `reschedule`(system_call.s:78) / (c) 자발적: `sleep_on`(:162), `interruptible_sleep_on`(:178), `sys_pause`(:147), `do_exit`(exit.c:133), `sys_waitpid`(exit.c:188) / (d) `release`(exit.c:29). 축: 호출자 종류, 호출 직전 `current->state`, `schedule()` 반환 후 어디로 가는가. | 비교 |
| 17 | `schedule()` (1): 깨우기 | `sched.c:104–120`. 역순 순회(`&LAST_TASK`→`&FIRST_TASK`, task 0 제외). alarm 만료 → SIGALRM 비트. `signal & ~(_BLOCKABLE & blocked)` 있고 INTERRUPTIBLE이면 RUNNING. `_S`/`_BLOCKABLE`(23–24). | 코드 |
| 18 | `schedule()` (2): 고르기 | `sched.c:124–135`. `c=-1, next=0`. RUNNING이고 `counter > c`인 태스크 → `next`. 역순 순회(`task[63]`→`task[1]`)에 `>`(strict)이므로 동률이면 **먼저 만난 인덱스 큰 쪽이 남는다**. `if (c) break;` — c==0이면 모두 counter 0 → 재충전. | 코드 |
| 19 | `schedule()` (3): 재충전 식 | `sched.c:136–139`. `counter = counter>>1 + priority` — **모든** 태스크(잠든 것 포함). 손계산 표: priority 15, counter 0/3/8인 세 태스크 → 15/16/19. 잠든 태스크는 깨어날 때 유리해짐(I/O 바운드 우대). 그다음 `switch_to(next)`(141). | 코드 |
| 20 | 상태 변화도 (1): 다섯 상태와 전환 | 상태 원 5개 + "current(실행 중)"는 RUNNING 안의 표시. 화살표마다 원인 함수와 줄: RUNNING→INTERRUPTIBLE(`sys_pause` 146, `interruptible_sleep_on` 177, `sys_waitpid` exit.c:187), RUNNING→UNINTERRUPTIBLE(`sleep_on` 161), →RUNNING(`wake_up` 191, `schedule` 117–119, `sleep_on` 164, `interruptible_sleep_on` 180), RUNNING→ZOMBIE(exit.c:130), ZOMBIE→소멸(`release` exit.c:27–28). STOPPED는 점선 + "진입 코드 없음". | 상태도 |
| 21 | 상태 변화도 (2): 변경 데이터와 유지 조건 | 표: 상태별로 변하는 데이터(`state`, `counter`(RUNNING·current일 때만 감소), 대기 큐 `*p`, `exit_code`(ZOMBIE)), 유지 조건(`schedule()`은 state==0만 선택, ZOMBIE는 `waitpid` 전까지 `task[]`에 남음), 재충전은 상태 무관. 호출 순서도(슬라이드 16)와 다른 그림임을 명시. | 상태도 |
| 22 | `sleep_on`과 `wake_up` | `sched.c:151–165`, `188–194`. `tmp=*p; *p=current;` — 대기 큐가 "포인터 하나 + 각자의 스택 변수 tmp"로 이어진 리스트. `wake_up`은 머리 하나만 깨우고, 깨어난 쪽이 `tmp->state=0`으로 다음을 깨움(164). 그림: 세 태스크가 `bh->b_wait`에 잠든 모양. | 코드 |
| 23 | `interruptible_sleep_on` | `sched.c:167–186`. `repeat:` — 깨어났는데 `*p != current`(내가 머리가 아님)이면 머리를 깨우고 다시 잠. 시그널로 깨어날 수 있으므로 `schedule()` 앞부분(117–119)과 짝. 사용처 `tty_io.c:126,136`. | 코드 |
| 24 | 비교: `sleep_on` vs `interruptible_sleep_on` | 범위 = 잠드는 두 함수. 축: 설정 상태(2 vs 1), 시그널로 깸(아니오/예), 깨어난 뒤 재검사(없음/`repeat`), 사용처(`buffer.c:40,225` 디스크 I/O / `tty_io.c:126,136` 키 입력 대기). | 비교 |
| 25 | `switch_to(n)` 매크로 | `sched.h:171–184`. `cmpl %%ecx,_current; je 1f` 같은 태스크면 아무것도 안 함. `movw %%dx,%1` — `__tmp.b`에 `_TSS(n)` 선택자. `xchgl %%ecx,_current` — `current` 갱신. `ljmp %0` — `__tmp`(오프셋 무시, 선택자만)로 far jump = TSS 전환. 이후 `clts` 조건. | 코드 |
| 26 | `ljmp`가 TSS로 가면 CPU가 하는 일 | 그림: 현재 레지스터 전부(EIP 포함 = `ljmp` 다음 줄) → `current` 이전 태스크의 TSS에 저장; 새 TSS에서 전부 로드; TR 갱신; LDTR 갱신(tss.ldt); CR3 — 0.11은 모두 `&pg_dir`(sched.h:128). "커널 스택도 바뀐다"(ss/esp 복원). 다시 선택되면 `ljmp` 다음 줄부터. | 배경 |
| 27 | `sched_init`: TSS/LDT 설명자와 ltr | `sched.c:385–412`. 392–393 task 0의 TSS/LDT를 GDT 4·5번에. 394–401 나머지 63개 슬롯 0으로. 403 NT 플래그 클리어(iret가 태스크 복귀로 해석되지 않게). 404–405 `ltr(0)`, `lldt(0)`. `_TSS(n)`=(n<<4)+(4<<3)(sched.h:155). | 코드 |
| 28 | 커널 스택과 `tss.esp0` | 04회차 `int 0x80` 시 CPU가 TSS의 ss0/esp0를 읽는다고 했다 → 그 값이 `PAGE_SIZE+(long)&init_task`(sched.h:128) / `copy_process`의 `PAGE_SIZE+(long)p`(fork.c:93, 06회차). 태스크마다 커널 스택이 자기 페이지 끝. `union task_union` 그림 재사용. | 코드 |
| 29 | 시연 환경 | lab QEMU `-s -S` + GDB. 중단점이 타이머 틱마다 걸리므로 `cond`·`ignore`·`display`를 미리 설정. 심볼명은 lab 빌드 기준 확인. 실패 시 사전 캡처. | 시연 |
| 30 | 시연 A: `break do_timer`, `jiffies`와 `counter` | `display jiffies`, `display current->pid`, `display current->counter`, `display $cpl`은 없으므로 `p/x *(long*)($esp+4)`(cpl 인자). `c` 5~6회 반복 → jiffies +1, counter -1 관찰. | 시연 |
| 31 | 캡처 A: 틱 연속 관찰 | GDB 로그: 연속 틱에서 jiffies 1씩 증가, 같은 pid의 counter 1씩 감소. 각주: lab 빌드, 수정 없음, 게스트는 셸 프롬프트 대기 중(대부분 task 0 또는 셸). 14장 표를 이 값으로 채움. | 캡처 |
| 32 | 시연 B: `counter`가 0이 되는 순간 | `break schedule`로 바꾸고 `bt` → 호출자가 `do_timer`인지 `reschedule`/`sleep_on`인지 확인(슬라이드 16 비교 연결). `p task[1]->state`, `p task[1]->counter` 등 살아 있는 태스크 나열(`p *task[i]`의 state/counter/priority/pid만). | 시연 |
| 33 | 캡처 B: `bt`와 태스크 표 | `bt` 출력(`schedule ← do_timer ← timer_interrupt` 또는 `schedule ← sys_pause ← system_call`)과 각 task의 state/counter/priority. 각주 포함. | 캡처 |
| 34 | 시연 C: `switch_to` 전후 `current` | `break schedule` 뒤 `finish`가 안 되는 이유(ljmp로 다른 태스크로 감) 설명. 대신 `watch current`(hw watchpoint) 또는 `switch_to`의 `ljmp` 주소에 `break` 후 `stepi` → `p current->pid`, `p/x $esp`(커널 스택이 다른 페이지로), `info registers tr`은 QEMU gdbstub이 안 줄 수 있음 → 대체는 `p/x $cs`와 `$esp` 상위 비트. | 시연 |
| 35 | 캡처 C: 전환 전/후 | 두 캡처 나란히: `current->pid`, `$esp`, `$eip`. 전환 후 `$eip`가 `ljmp` 다음 명령(`cmpl %%ecx,_last_task_used_math`)인 점. 각주: 환경·수정 여부. 셸 외에 둘째 태스크가 필요하면 백그라운드 명령 하나 실행. | 캡처 |
| 36 | 관찰 vs 추론 구분 | 오늘 실제 본 것: jiffies 증가, counter 감소, bt, current 변화. 소스로 추론한 것: TSS 내부 저장 순서(CPU 동작, GDB로 직접 안 보임), 재충전 값(틱 수가 많아 시연 시간 내 반복 재현은 어려움). | 캡처 |
| 37 | 질문의 답: 틱 한 번의 경로 | IRQ0 → IDT[0x20] → `_timer_interrupt`(`jiffies++`) → `do_timer(cpl)` → `counter--` → (0이고 cpl=3) `schedule()` → 깨우기 → 고르기/재충전 → `switch_to(next)` → `ljmp` TSS → 새 태스크의 `ljmp` 다음 줄 → … → 그 태스크의 `ret_from_sys_call` → `iret`. 각 단계에 파일:줄. | 정리 |
| 38 | 왜 커널 모드에서는 안 바꾸는가 | `do_timer`의 `if (!cpl) return;`(334). 0.11 커널은 비선점: 커널 안에서는 스스로 `schedule()`을 부를 때만 전환. 장점(락 불필요) / 비용(긴 커널 작업 중 응답 지연). 현대 커널의 선점은 14회차에서. | 정리 |
| 39 | 흔한 오해 바로잡기 | "schedule은 타이머만 부른다"(아니다, 슬라이드 16), "counter는 우선순위다"(남은 틱; priority가 기준), "STOPPED 상태가 있다"(정의만), "task 0도 schedule 대상"(루프는 `p > &FIRST_TASK`로 제외, next=0은 기본값), "switch_to가 레지스터를 직접 저장한다"(CPU가 TSS에). | 정리 |
| 40 | 현대 커널 한 줄 | 현대 Linux는 TSS 전환 대신 소프트웨어 문맥 전환, CFS 등 정책도 다름. 하지만 "틱 → 회계 → 필요 시 선택 → 전환"의 골격과 `state` 개념은 같다. 상세는 14회차. | 배경 |
| 41 | 이해 확인 질문 | 아래 4문항, 정답 클릭 후 표시. | 질문 |
| 42 | 정리와 다음 회차 | 정리 4줄. 06 예고: "`task[1]`은 누가 어떻게 만들었나? `copy_process`가 TSS의 `eax`를 0으로 두면 자식은 `fork()`에서 0을 받는다 — `switch_to`가 TSS를 통째로 복원하기 때문". | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
공통: lab QEMU `-s -S`, GDB `target remote :1234`. 부팅 완료(셸 프롬프트) 후 중단점. 틱 중단점은 10 ms마다 걸리므로 관찰 뒤 반드시 `delete`. 심볼명은 lab 빌드 기준(`info functions do_timer`로 확인).

- **A. 틱마다 `jiffies`·`counter`**
  - 명령: `break do_timer`, `display jiffies`, `display current->pid`, `display current->counter`, `display/x *(long*)($esp+4)`(cpl), `c` ×6.
  - 기대: jiffies가 1씩 증가. 같은 pid가 연속이면 counter가 1씩 감소. 프롬프트 대기 중이면 `current->pid`=0(task 0, `pause` 루프)이고 cpl=3인 경우가 많음. counter가 0에 도달한 틱 다음 정지에서 pid가 바뀔 수 있음.
  - 대체: 사전 캡처 로그 1장.
- **B. `schedule()`의 호출자와 태스크 표**
  - 명령: `delete`, `break schedule`, `c`, `bt`, `p task[0]->state`, `p task[1]->pid`, `p task[1]->state`, `p task[1]->counter`, `p task[1]->priority`(존재하는 인덱스까지).
  - 기대: `bt`에 `do_timer`/`timer_interrupt` 또는 `sys_pause`/`system_call`(task 0가 pause에서 부름). task 1(init)은 `waitpid`로 INTERRUPTIBLE(=1), 셸은 tty 입력 대기로 INTERRUPTIBLE(=1)인 경우가 보통.
  - 대체: 사전 캡처 2장.
- **C. `switch_to` 전후**
  - 명령: `schedule`에 멈춘 뒤 `disassemble`로 `ljmp` 주소를 찾아 `break *<addr>`, `c`, `p current->pid`, `p/x $esp`, `stepi`, `p current->pid`, `p/x $esp`, `p/x $eip`. 둘째 태스크 확보용으로 게스트 셸에서 `sleep` 류 명령이나 루프를 백그라운드로 실행해 둔다(lab 이미지에 있는 명령으로 사전 확인).
  - 기대: `stepi` 후 pid와 `$esp`(다른 4 KiB 페이지)가 바뀜. `$eip`는 `ljmp` 바로 다음 명령.
  - 대체: QEMU gdbstub에서 `stepi`가 `ljmp` 태스크 전환을 한 번에 넘기지 못하거나 멈추면, `break *<ljmp 다음 주소>`로 다시 시도. 그래도 실패하면 사전 캡처 2장.

## 이해 확인 질문과 정답
1. **Q.** 셸이 `read()` 안에서 키 입력을 기다리는 동안 타이머 틱이 100번 왔다. 셸의 `counter`는 얼마나 줄었는가? **A.** 0. `do_timer`는 `current->counter`만 줄이고(sched.c:332), 잠든 셸은 `current`가 아니다. 오히려 다른 태스크들이 모두 0이 되어 재충전이 일어나면 셸의 counter는 `counter/2 + priority`로 **늘어난다**(136–139).
2. **Q.** 커널이 `sys_write` 중일 때 틱이 와서 `counter`가 0이 됐다. 즉시 `schedule()`이 불리는가? **A.** 아니다. `do_timer`의 `if (!cpl) return;`(334) 때문에 커널 모드에서는 돌아간다. 대신 `sys_write`가 끝난 뒤 `system_call.s:99–100`의 `cmpl $0,counter; je reschedule`에서 `schedule()`로 간다.
3. **Q.** task 0의 `pause()`는 왜 영원히 잠들지 않는가? **A.** `sys_pause`가 `state=TASK_INTERRUPTIBLE`로 두고 `schedule()`을 불러도, `schedule()`의 선택 루프는 `c==0`일 때 `next=0`을 유지하므로(125–126) 뛸 태스크가 없으면 task 0로 `switch_to(0)`(현재와 같으면 아무것도 안 함)하고 `sys_pause`가 그냥 반환한다. `main.c:142–146` 주석.
4. **Q.** `switch_to(n)`에서 `ljmp`의 목적지 오프셋(`__tmp.a`)은 왜 설정하지 않는가? **A.** 선택자가 TSS 설명자를 가리키면 CPU는 오프셋을 무시하고 TSS 전환을 수행한다. 새 EIP는 목적지 TSS의 `eip` 필드에서 온다. `sched.h:171–177`.

## 처음 등장하는 용어
- **태스크(task)**: 0.11 소스에서 프로세스를 부르는 이름. `task_struct` 하나.
- **`current`**: CPU를 점유 중인 태스크 포인터.
- **`jiffies`**: 부팅 후 타이머 틱 수(HZ=100).
- **틱(tick)**: 8253이 만드는 10 ms 주기 IRQ0.
- **`counter` / `priority`**: 남은 시간 조각(틱) / 재충전 기준값.
- **타임 슬라이스**: counter가 가리키는 연속 실행 허용량.
- **대기 큐(`struct task_struct **p`)**: 잠든 태스크를 잇는 포인터 하나짜리 리스트.
- **TSS 전환**: 세그먼트 선택자가 TSS를 가리키는 far jump로 CPU가 레지스터를 저장·복원하는 x86 기능.
- **`esp0`/`ss0`**: 권한 0으로 진입할 때 쓸 커널 스택.
- **비선점(non-preemptive) 커널**: 커널 모드 실행 중에는 타이머가 태스크를 바꾸지 않음.
- **좀비(ZOMBIE)**: 종료했지만 부모가 `waitpid`로 거두기 전까지 `task[]`에 남은 상태.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- `TASK_STOPPED`로 들어가는 코드가 0.11에 없다. "SIGSTOP으로 멈춘다"고 말하지 말 것(정의와 `waitpid`의 case만 있음: sched.h:23, exit.c:166).
- "실행 중"은 `state` 값이 아니다. RUNNING 여러 개 중 `current` 하나가 CPU를 갖는다.
- `counter`를 "우선순위"라고 부르지 말 것. `priority`는 재충전량, `counter`는 남은 틱.
- 재충전 식은 **모든** 태스크(잠든 것 포함)에 적용된다. "RUNNING 태스크만 재충전"이라고 말하지 말 것(136–139는 상태 검사 없음).
- `schedule()`은 타이머 외에도 여러 곳에서 불린다(슬라이드 16). "타이머 인터럽트 핸들러 = 스케줄러"로 축약하지 말 것.
- `switch_to`가 레지스터를 "코드로" 저장한다고 말하지 말 것. `ljmp` 한 명령으로 CPU가 TSS에 저장·복원한다. 현대 커널의 소프트웨어 전환과 다르다.
- `tss.cr3`가 태스크마다 다르다고 말하지 말 것. 0.11은 모두 `pg_dir` 하나(sched.h:128)이고 주소 분리는 LDT base(06·07회차).
- `add_timer`/플로피 타이머는 "`do_timer`가 호출하는 부가 리스트"까지만. 플로피 드라이버는 11회차.
- 시연 A의 pid·counter 값은 실행마다 다르다. 캡처 값을 "항상 이렇다"고 말하지 말 것.
- CFS·O(1) 스케줄러 등 현대 정책 설명은 14회차. 오늘은 한 줄 비교만.

---

# 06. fork()와 프로세스 생성

## 핵심 질문
fork() 이후 부모와 자식은 어디에서 다시 실행되는가?

## 학습 목표 (3~5개)
1. `fork()`가 `_syscall0` → `int $0x80` → `sys_call_table[2]` → `_sys_fork`(어셈블리) → `find_empty_process` → `copy_process`로 이어지는 경로를 04회차 프레임 그림 위에 겹쳐 그린다.
2. `copy_process`의 17개 인자가 전부 **`_system_call`과 `_sys_fork`가 push한 스택 값**임을 확인하고, 인자 이름과 스택 슬롯을 1:1로 대응시킨다.
3. `copy_process`가 새 `task_struct`를 한 페이지에 만들고 TSS를 채우는 순서를 읽으며, `tss.eax = 0`, `tss.eip = eip`, `tss.esp = esp`가 "자식이 `fork()` 직후 사용자 코드에서 0을 받는" 메커니즘임을 05회차 TSS 전환과 연결해 설명한다.
4. fork에서 **복사되는 것**(task_struct 본문, LDT base, 페이지 테이블 항목)과 **공유되는 것**(`struct file`·inode는 카운트 증가, 물리 페이지는 읽기 전용 공유)을 구분하고, 각 항목의 소스 줄을 가리킨다.
5. GDB에서 `copy_process`에 멈춰 부모·자식 두 `task_struct`를 비교하고 `task[nr]->tss.eax == 0`을 눈으로 확인한다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| `include/unistd.h` | 62 | `__NR_fork 2` |
| `include/unistd.h` | 133–144 | `_syscall0` — `int $0x80`, 반환값 `"=a"(__res)` |
| `include/linux/sys.h` | 74 | `sys_call_table` 세 번째 항목 `sys_fork` |
| `init/main.c` | 12–24 | 주석 + `static inline _syscall0(int,fork)` — main에서 fork가 inline이어야 하는 이유(스택 사용 금지) |
| `init/main.c` | 137–140 | `move_to_user_mode(); if (!fork()) { init(); }` — 최초 fork |
| `init/main.c` | 179–188 | `init()`의 `if (!(pid=fork())) {…execve…} if (pid>0) while (pid != wait(&i))` — 반환값으로 부모/자식 분기 |
| `kernel/system_call.s` | 80–94 | `_system_call` — push ds/es/fs/edx/ecx/ebx, `call _sys_call_table(,%eax,4)` (04 복습) |
| `kernel/system_call.s` | 208–219 | `_sys_fork` — `call _find_empty_process`, 음수면 ret, `push %gs; pushl %esi; pushl %edi; pushl %ebp; pushl %eax(nr)`, `call _copy_process`, `addl $20,%esp` |
| `kernel/system_call.s` | 17–31 | 스택 배치 주석 — `copy_process` 인자 `ebx…ss`의 출처 |
| `kernel/fork.c` | 22 | `long last_pid=0` |
| `kernel/fork.c` | 24–37 | `verify_area` (참고: 08회차 COW 쓰기 검증) |
| `kernel/fork.c` | 39–61 | `copy_mem` — `get_limit(0x0f/0x17)`, 분리 I&D 금지 panic, `new_base = nr*0x4000000`, `set_base(ldt[1]/[2])`, `copy_page_tables` 실패 시 `free_page_tables` + `-ENOMEM` |
| `kernel/fork.c` | 68–71 | `copy_process` 시그니처 17개 인자 |
| `kernel/fork.c` | 77–81 | `get_free_page()` → `task[nr]=p` → `*p = *current` (구조체 통째 복사, 커널 스택은 미복사) |
| `kernel/fork.c` | 82–91 | state=UNINTERRUPTIBLE, pid, father, `counter=priority`, signal/alarm/leader 0, 시간 0, `start_time=jiffies` |
| `kernel/fork.c` | 92–112 | TSS 채우기 — 93 `esp0 = PAGE_SIZE+(long)p`, 94 `ss0=0x10`, 95 `eip=eip`, 96 `eflags`, **97 `eax = 0`**, 98–104 ecx/edx/ebx/esp/ebp/esi/edi, 105–110 세그먼트 `& 0xffff`, 111 `ldt=_LDT(nr)`, 112 `trace_bitmap` |
| `kernel/fork.c` | 113–114 | 수학 코프로세서 상태 저장 (참고) |
| `kernel/fork.c` | 115–119 | `copy_mem` 실패 시 `task[nr]=NULL; free_page(p); -EAGAIN` |
| `kernel/fork.c` | 120–128 | 공유 카운트 — `filp[i]->f_count++`, `pwd/root/executable->i_count++` |
| `kernel/fork.c` | 129–132 | GDT에 TSS/LDT 설명자 등록, `state = TASK_RUNNING` ("do this last"), `return last_pid` |
| `kernel/fork.c` | 135–147 | `find_empty_process` — `last_pid` 증가·중복 검사(`repeat`), 빈 `task[i]` 인덱스(1부터) 반환, 없으면 `-EAGAIN` |
| `include/linux/sched.h` | 51–76 | `tss_struct` (05 복습) — `copy_process` 92–112이 채우는 필드 |
| `include/linux/sched.h` | 155–156 | `_TSS(n)`, `_LDT(n)` — GDT 인덱스 계산 |
| `include/linux/sched.h` | 171–184 | `switch_to` — 자식이 처음 실행될 때 TSS 복원 경로 (05 복습) |
| `include/linux/sched.h` | 211–212, 226 | `set_base`, `set_limit`, `get_base` |
| `include/linux/sched.h` | 128 | INIT_TASK의 `tss.cr3 = &pg_dir` — 자식도 같은 값(`*p=*current`) |
| `mm/memory.c` | 150–189 | `copy_page_tables(from,to,size)` — 참고만: 158–159 4 MiB 정렬 panic, 163–171 디렉터리 항목·새 페이지 테이블, 172 `nr = (from==0)?0xA0:1024`, 177 `this_page &= ~2`(읽기 전용), 179–184 `mem_map[]++`와 부모도 읽기 전용, 187 `invalidate()` |
| `mm/memory.c` | 39 | `invalidate()` 매크로 (CR3 재로드) |
| `include/linux/fs.h` | 107, 119 | `m_inode.i_count`, `file.f_count` |
| `include/errno.h` | 30–31 | `EAGAIN 11`, `ENOMEM 12` |
| `kernel/exit.c` | 106–123 | 참고(대칭): `do_exit`가 `free_page_tables`, `sys_close`, `iput`로 fork의 복사·공유를 되돌리는 순서 (10회차) |
| `kernel/sched.c` | 104–142 | `schedule()` — 자식이 처음 선택되는 경로 (05 복습) |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 (필수, 슬라이드 23)**: 범위 = "새 태스크 슬롯 `task[nr]`의 생애 초기". 상태: `비어 있음(task[nr]==NULL)` → `[find_empty_process가 nr 반환]` `예약됨(아직 NULL)` → `[get_free_page, task[nr]=p]` `페이지 확보` → `[*p=*current; state=UNINTERRUPTIBLE]` `부모 복사본(실행 불가)` → `[TSS 채움, copy_mem, 카운트 증가, GDT 등록]` `자식 준비` → `[state=TASK_RUNNING]` `실행 가능` → `[schedule → switch_to(nr)]` `자식 실행 중(사용자 모드, eax=0)`. 실패 전환: `copy_mem` 실패 → `task[nr]=NULL; free_page` → `비어 있음`. 각 화살표에 변경 데이터(`task[]`, `state`, `tss.*`, `ldt[].base`, `f_count`, `i_count`, GDT 항목)와 유지 조건(UNINTERRUPTIBLE 동안 `schedule()`이 고르지 않음).
- **부모 쪽 상태 (슬라이드 24)**: 부모는 `copy_process` 내내 RUNNING·`current`. `sys_fork` 반환 후 `ret_from_sys_call`로 `iret` → 사용자 모드, EAX=last_pid. 자식과 부모의 "다시 실행되는 지점"을 한 그림에.
- **모드·선택지 비교 (필수, 슬라이드 25)**: 범위 = "fork 시 자식이 받는 각 자원의 처리 방식". 선택지(처리 방식): ① 값 복사(`*p=*current`로 복사 후 일부 덮어씀) ② 새로 만듦 ③ 참조 공유 + 카운트 증가 ④ 페이지 테이블 복사 + 물리 페이지 읽기 전용 공유. 행(자원): `task_struct` 본문·시그널·시간(①, fork.c:81–91) / 커널 스택·TSS·pid·LDT base(②, 77–112, copy_mem 52–55) / `filp[]`·`pwd`·`root`·`executable`(③, 120–128) / 사용자 코드·데이터 페이지(④, copy_mem 56, memory.c:177–184). 축: 소스 줄, 자식이 바꾸면 부모에 보이는가, 해제 시점(`do_exit` 대칭 줄). CPU 모드·태스크 상태와 섞지 않는다.
- **보조 비교 (슬라이드 27)**: 범위 = "`fork()` 반환값" — 부모(EAX=`last_pid`>0, fork.c:132) / 자식(EAX=0, `tss.eax`=0, fork.c:97) / 실패(EAX<0 → `_syscall0`이 `errno=-__res; return -1`, 원인 `find_empty_process`/`get_free_page`/`copy_mem`).

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문, 지도(05 TSS 전환·04 프레임 위에 올라감) |
| 03–07 | 15 | 배경: `fork()` 사용법과 두 번 반환, main.c의 최초 fork, `_syscall0`·`sys_fork` 진입 |
| 08–12 | 20 | `_sys_fork` 어셈블리, 17개 인자와 스택 슬롯 대응, `find_empty_process` |
| 13–19 | 25 | `copy_process` 한 구역씩: 페이지 확보·복사, TSS, `copy_mem`, 공유 카운트, GDT, RUNNING |
| 20–22 | 10 | `copy_page_tables` 참고(결과만), 자식이 0을 받는 메커니즘 |
| 23–27 | 15 | 상태 변화도 2장, 자원 처리 비교, 반환값 비교 |
| 28–36 | 22 | 강사 시연 A/B/C + 캡처 |
| 37–40 | 5 | 질문의 답, 오해 정리, 현대 커널 한 줄 |
| 41–42 | 3 | 이해 확인, 정리·07 예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약 | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 06. fork()와 프로세스 생성 | 제목과 핵심 질문 "fork() 이후 부모와 자식은 어디에서 다시 실행되는가?". 답은 "둘 다 `int $0x80` 다음 명령, 단 EAX가 다르다"임을 끝에 GDB로 보인다고 예고. | 제목 |
| 02 | 15회차 지도 | 06 강조. 04(프레임), 05(TSS·`switch_to`)가 재료. 07·08(페이지 테이블·COW)은 오늘 `copy_mem`에서 "결과만" 보고 넘기는 부분. 09(exec)·10(exit/wait)은 fork의 뒤. | 지도 |
| 03 | `fork()`의 약속 | 사용자 관점: 한 번 부르면 두 번 돌아온다. 부모에게 자식 pid, 자식에게 0, 실패 -1. `init/main.c:179–188` 코드로 `if (!(pid=fork()))` 패턴. "같은 코드, 같은 지점, 다른 값". | 배경 |
| 04 | 최초의 fork: main.c | `init/main.c:137–140`. `move_to_user_mode()` 직후 task 0이 `fork()` → task 1(`init()`). `main.c:12–24` 주석: fork가 inline이어야 하는 이유(task 0의 사용자 스택이 자식과 공유되므로 함수 호출로 스택을 쓰면 안 됨). | 코드 |
| 05 | `_syscall0(int,fork)` | `unistd.h:133–144` 전개: `int fork(void){ long __res; asm("int $0x80":"=a"(__res):"0"(2)); …}`. `__NR_fork=2`(unistd.h:62) → `sys.h:74`의 세 번째 `sys_fork`. 04회차 `_syscall3`과 차이는 인자 없음뿐. | 코드 |
| 06 | 04회차 프레임 다시 | `system_call.s:17–31` 12슬롯 그림 재게시. `_system_call:80–94`가 push한 ds/es/fs/edx/ecx/ebx + CPU가 push한 eip/cs/eflags/esp/ss. "이 스택이 자식의 TSS 재료가 된다"고 예고. | 코드 |
| 07 | `sys_fork`는 C 함수가 아니다 | `sys.h:3` `extern int sys_fork();`지만 정의는 `system_call.s:208–219`. 이유: `copy_process`에 넘길 레지스터(gs, esi, edi, ebp)가 `_system_call`에서 push되지 않았으므로 어셈블리에서 추가 push 필요. | 코드 |
| 08 | `_sys_fork` 한 줄씩 | `system_call.s:208–219`. 209 `call _find_empty_process` → eax=nr. 210–211 음수면 `1: ret`(실패). 212–216 `push %gs; pushl %esi; pushl %edi; pushl %ebp; pushl %eax`. 217 `call _copy_process`. 218 `addl $20,%esp`(5개 정리). 219 `ret` → `_system_call:95`의 `pushl %eax`. | 코드 |
| 09 | 17개 인자 = 스택 17슬롯 | `fork.c:68–71` 시그니처와 스택 그림을 나란히. `nr,ebp,edi,esi,gs`(sys_fork가 push) / `none`(= `call _copy_process`의 복귀 주소가 아니라 **`_system_call`의 `call _sys_call_table`이 남긴 복귀 주소**) / `ebx,ecx,edx,fs,es,ds`(_system_call push) / `eip,cs,eflags,esp,ss`(CPU push). C 함수는 그저 스택을 인자로 읽는다. | 코드 |
| 10 | `none`의 정체 | `_sys_fork`는 `call`로 들어왔으므로 `_system_call:94`의 복귀 주소가 ebx 아래에 있다. `copy_process`는 이를 `none`으로 받아 무시. 그림으로 `call` 두 번(`_sys_call_table` → `_sys_fork`, `_sys_fork` → `_copy_process`)의 복귀 주소 위치. | 코드 |
| 11 | `find_empty_process` | `fork.c:135–147`. `last_pid`(22) 증가, 음수 넘침 시 1. `repeat`: 살아 있는 task 중 같은 pid가 있으면 다시 증가. 그다음 `task[1..63]` 중 NULL인 첫 인덱스 반환. pid와 슬롯 번호 nr이 다른 값임을 강조. `-EAGAIN`(errno.h:30). | 코드 |
| 12 | pid vs nr | 표: pid(전역 증가, 사용자에게 보이는 번호) / nr(`task[]` 인덱스 1~63, TSS·LDT GDT 위치 `_TSS(nr)`, 선형 주소 base `nr*0x4000000`). 같은 pid 1이라도 재부팅마다 nr이 같고, pid 100번대도 nr은 작을 수 있음. | 배경 |
| 13 | `copy_process` (1): 페이지 하나 = task_struct + 커널 스택 | `fork.c:77–81`. `get_free_page()`(memory.c:63) → 4 KiB. `task[nr]=p`. `*p = *current` — 구조체 대입 한 줄로 부모 전부 복사. 주석 "doesn't copy the supervisor stack": 자식 커널 스택은 비어 있다 → 자식은 커널 안의 어디로도 "돌아갈" 곳이 없고 **TSS의 eip/esp로 곧장 사용자 모드로 간다**. | 코드 |
| 14 | `copy_process` (2): 덮어쓰는 필드 | `fork.c:82–91`. `state=TASK_UNINTERRUPTIBLE`(아직 고르지 말 것), `pid=last_pid`, `father=current->pid`, `counter=priority`(05: 새 태스크는 꽉 찬 타임 슬라이스), `signal=0`, `alarm=0`, `leader=0`, 시간 0, `start_time=jiffies`. 복사된 채 남는 것: `priority`, `blocked`, `sigaction[]`, uid/gid, `umask`, `tty`, `close_on_exec`. | 코드 |
| 15 | `copy_process` (3): TSS 채우기 | `fork.c:92–112`. `esp0 = PAGE_SIZE+(long)p`(커널 스택 = 자기 페이지 끝, 05의 esp0), `ss0=0x10`. `eip=eip`(int 0x80 다음 명령), `eflags`, **`eax=0`**, 나머지 레지스터 = 스택 값 그대로, `esp=esp`(부모의 사용자 ESP), 세그먼트 `&0xffff`, `ldt=_LDT(nr)`, `trace_bitmap=0x80000000`. 그림: 04 프레임 슬롯 → TSS 필드 화살표. | 코드 |
| 16 | 왜 `tss.eax = 0`이 "자식은 0을 받는다"가 되는가 | 05회차 `switch_to`: `ljmp`로 TSS 전환 시 CPU가 TSS의 eax…eip…esp를 전부 로드. 자식이 처음 선택되면 레지스터 = TSS 값 → EIP는 `int $0x80` 다음, CS=0x0f(사용자), EAX=0. `_syscall0`의 `"=a"(__res)`가 0을 읽어 `return 0`. 부모는 `ret_from_sys_call`의 `popl %eax`로 `last_pid`. | 코드 |
| 17 | `copy_process` (4): `copy_mem` | `fork.c:39–61`. `get_limit(0x0f)`/`(0x17)` 현재 LDT 한계, `get_base(current->ldt[1]/[2])`. 48–51 코드·데이터 base가 다르면 panic. 52 `new_base = nr*0x4000000`(64 MiB × nr). 53–55 `p->start_code`, `set_base(ldt[1])`, `set_base(ldt[2])`. 56 `copy_page_tables(old,new,data_limit)` 실패 시 되돌리고 `-ENOMEM`. | 코드 |
| 18 | 자식의 주소 공간은 "번호 × 64 MiB" | 그림: 선형 주소 공간 4 GiB에 nr별 64 MiB 칸. 부모 nr=1 → 0x4000000, 자식 nr=2 → 0x8000000. 사용자 코드의 주소 0은 LDT base 덕에 서로 다른 선형 주소. 07회차 핵심 질문("같은 숫자 주소가 두 프로세스에서 왜 다른 메모리")의 절반이 여기 있음을 짚고, 페이징은 07로 넘김. | 배경 |
| 19 | `copy_process` (5): 공유 카운트·GDT·RUNNING | `fork.c:120–132`. `filp[i]->f_count++`(fs.h:119), `pwd/root/executable->i_count++`(fs.h:107) — 포인터는 `*p=*current`로 이미 복사됐고 **같은 객체**를 가리키므로 카운트만. 129–130 GDT에 TSS/LDT 설명자(`set_tss_desc`/`set_ldt_desc`, system.h:65–66). 131 `state=TASK_RUNNING` "do this last". 132 `return last_pid`. | 코드 |
| 20 | `copy_page_tables`: 결과만 (참고) | `mm/memory.c:150–189`. 오늘 읽는 범위: 163–171(새 페이지 테이블 한 장 `get_free_page`, 디렉터리 항목 `|7`), 172(`from==0`이면 0xA0개 = task 0의 640 KiB만), 177 `this_page &= ~2`(쓰기 금지), 179–184(`mem_map[]++`, 부모 항목도 쓰기 금지로 바꿈), 187 `invalidate()`. 내부 비트 의미는 07, 쓰기 시 일어나는 일은 08. | 코드 |
| 21 | 복사된 것은 "표", 공유된 것은 "페이지" | 그림: 부모 페이지 테이블 → 자식 페이지 테이블(새 페이지, 항목 복사) → 둘 다 같은 물리 페이지를 R/O로. `mem_map` 카운트 2. "fork는 메모리를 복사하지 않는다"의 정확한 의미. 08회차에서 자식이 쓸 때 어떻게 되는지. | 배경 |
| 22 | 자식의 첫 실행 경로 | 05 `schedule()`: 자식 counter=priority(가득)이므로 곧 선택될 가능성 높음 → `switch_to(nr)` → `ljmp` → CPU가 자식 TSS 로드 → CS:EIP = 0x0f:(int 0x80 다음) → `_syscall0` 뒷부분 `if (__res>=0) return 0`. 자식은 `ret_from_sys_call`을 **거치지 않는다**(커널 스택이 비어 있으므로). | 코드 |
| 23 | 상태 변화도: `task[nr]` 슬롯의 탄생 | 상태 6개(비어 있음 → 예약 → 페이지 확보 → 부모 복사본·UNINTERRUPTIBLE → 자식 준비 → RUNNING → 자식 실행 중). 각 화살표에 원인 코드(fork.c 줄), 변경 데이터(`task[nr]`, `state`, `tss.*`, `ldt[].base`, `f_count`, `i_count`, GDT), 유지 조건(UNINTERRUPTIBLE 동안 `schedule()` 선택 제외). 실패 화살표: 115–118 → 비어 있음. | 상태도 |
| 24 | 두 태스크가 다시 실행되는 지점 | 한 그림에 부모·자식. 부모: `copy_process` return → `_sys_fork ret` → `_system_call:95 pushl %eax` → `ret_from_sys_call` → `iret` → 사용자, EAX=pid. 자식: (나중에) `switch_to` → TSS → 사용자, EAX=0. 공통: 같은 EIP, 같은 ESP 값(단 선형 주소는 base가 달라 다른 페이지 테이블을 통함), 같은 EFLAGS. 상태도와 구분되는 "호출 순서도". | 상태도 |
| 25 | 비교: 자식이 받는 자원의 처리 방식 | 범위 = fork 시 자원 처리. 행: task_struct 본문(값 복사, 81) / 커널 스택·TSS·pid·LDT base(새로 만듦, 77,92–112,52–55) / `filp[]`·`pwd`·`root`·`executable`(참조 공유+카운트, 120–128) / 사용자 페이지(테이블 복사+R/O 공유, 56, memory.c:177–184). 열: 소스 줄, 자식이 바꾸면 부모에 보이는가(아니오/아니오/**예**: f_pos 공유/08회차 전까지 쓰기 불가), 해제 대칭(`do_exit` exit.c:106–107, 115–123; `release` 20–33). | 비교 |
| 26 | `f_count`가 뜻하는 것 | `struct file`(fs.h:116–119)은 열린 파일 하나의 오프셋(`f_pos`)을 가짐. 부모·자식이 같은 `struct file`을 가리키므로 한쪽이 `write`하면 다른 쪽 `f_pos`도 움직임. `do_exit`의 `sys_close`(exit.c:115–117)가 카운트를 줄임. 12회차에서 inode와 함께 다시. | 코드 |
| 27 | 비교: `fork()` 반환값 세 가지 | 범위 = 반환값. 부모: `last_pid`(fork.c:132 → EAX 슬롯 → `popl %eax`). 자식: 0(fork.c:97 `tss.eax`). 실패: `-EAGAIN`(find_empty_process 146, get_free_page 실패 79, copy_mem 실패 118) → `_syscall0:142–143` `errno=11; return -1`. 열: 값, 출처 줄, 사용자 코드 분기(`main.c:179–186`). | 비교 |
| 28 | 시연 환경 | lab QEMU `-s -S` + GDB. `copy_process`는 셸이 명령을 실행할 때마다 호출되므로 게스트 셸에서 `ls` 한 번이 트리거. 심볼명은 lab 빌드 기준. 실패 시 사전 캡처. | 시연 |
| 29 | 시연 A: `break copy_process`, 인자 확인 | 게스트 `ls` → 정지. `info args`로 nr, eip, cs, eflags, esp, ss, eax 없음 확인(인자에 eax 없음!). `p/x cs`=0xf, `p/x ss`=0x17, `p/x eip`(사용자 주소, `int 0x80` 다음). `p nr`, `p last_pid`. | 시연 |
| 30 | 캡처 A: `info args` | 17개 인자 값 캡처. 09장 스택 그림과 대조: `none`은 커널 주소(`_system_call` 안), `cs`=0xf/`ss`=0x17는 사용자. 각주: lab 빌드, 수정 없음. | 캡처 |
| 31 | 시연 B: 두 `task_struct` 비교 | `finish`(copy_process 반환, 반환값 = pid) 직후: `p *current`와 `p *task[nr]`를 pid/father/state/counter/priority/start_time/filp[0] 필드만 추려 비교(`p current->pid`, `p task[<nr>]->pid`, `p task[<nr>]->father`, `p task[<nr>]->state`, `p task[<nr>]->filp[0]`, `p current->filp[0]`). | 시연 |
| 32 | 캡처 B-1: 부모·자식 필드 대조 | 두 열 표로 캡처: pid 다름, father = 부모 pid, state 둘 다 0, counter(자식 = priority), `filp[0]` **같은 포인터**, `filp[0]->f_count` 증가. 각주 포함. | 캡처 |
| 33 | 시연 B-2: `tss.eax == 0`, `tss.eip` | `p task[<nr>]->tss.eax`(0), `p/x task[<nr>]->tss.eip`, `p/x task[<nr>]->tss.esp`, `p/x task[<nr>]->tss.cs`(0xf), `p/x task[<nr>]->tss.esp0`(= task 페이지 + 0x1000), `p/x task[<nr>]->tss.ldt`, `p/x task[<nr>]->ldt[2]`(base 비트에 nr*0x4000000). `p/x current->tss.eax`는 아직 전환 전 값이라 의미 없음을 설명. | 시연 |
| 34 | 캡처 B-2: 자식 TSS | 캡처. `tss.eax=0`, `tss.eip`=시연 A의 `eip` 인자와 동일, `tss.esp0`=`task[nr]`+4096. 각주 포함. | 캡처 |
| 35 | 시연 C: 자식이 처음 실행되는 순간 | `break *<tss.eip 값>`(사용자 주소; 부모도 같은 EIP를 지나므로 걸릴 때마다 `p/x $eax` 확인: 한 번은 pid, 한 번은 0). `p/x $cs`=0xf, `p/x $eax`. 부모·자식 중 누가 먼저 걸리는지는 실행마다 다름을 미리 말함. | 시연 |
| 36 | 캡처 C: 같은 EIP, 다른 EAX | 두 번 정지 캡처: 같은 `$eip`, `$eax`=pid / 0. 질문에 대한 실물 답. 각주: 환경·순서는 실행마다 다름. 관찰(EIP·EAX 값)과 추론(TSS 로드 순서)을 구분. | 캡처 |
| 37 | 질문의 답 | "둘 다 `int $0x80` 다음 명령에서. 부모는 `ret_from_sys_call`→`iret`로, 자식은 `switch_to`→TSS 복원으로 도착하며, 차이는 EAX(pid vs 0)와 LDT base(선형 주소)뿐." 경로 두 줄 + 파일:줄. | 정리 |
| 38 | fork가 하지 않는 일 | 메모리 복사(페이지 테이블만), 커널 스택 복사(비움), `struct file` 복사(공유), 프로그램 교체(09 exec). 각각 어디서 하는지 회차 번호로. | 정리 |
| 39 | 흔한 오해 바로잡기 | "자식은 `copy_process`에서 반환해 돌아온다"(아니다, 자식은 커널 스택이 없어 TSS에서 곧장 사용자로), "fork는 메모리를 복제한다"(R/O 공유), "pid = task 인덱스"(별개), "`*p=*current`가 전부 복사하니 파일도 복사된다"(포인터 복사 = 공유). | 정리 |
| 40 | 현대 커널 한 줄 | 현대 Linux `fork`/`clone`은 `copy_process`라는 이름이 남아 있고 COW도 같지만, 자식의 첫 실행은 `ret_from_fork` 커널 스택 프레임으로 돌아간다(TSS 전환 아님). 비교는 14회차. | 배경 |
| 41 | 이해 확인 질문 | 아래 4문항. | 질문 |
| 42 | 정리와 다음 회차 | 정리 4줄. 07 예고: "`nr*0x4000000` base와 `copy_page_tables`가 만든 표 — 같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가?" 08 예고: "`this_page &= ~2` 뒤 자식이 쓰면?" | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
공통: lab QEMU `-s -S`, GDB `target remote :1234`, 셸 프롬프트까지 부팅 후 중단점. 트리거는 게스트 셸에서 `ls`(셸이 fork → exec). 심볼명은 lab 빌드 기준(`info functions copy_process`).

- **A. `copy_process` 인자**
  - 명령: `break copy_process`, 게스트 `ls`, `info args`, `p/x cs`, `p/x ss`, `p/x eip`, `p/x esp`, `p nr`, `p last_pid`.
  - 기대: `cs=0xf`, `ss=0x17`, `eip`·`esp`는 사용자 공간 값(작은 주소, 셸 바이너리 내부), `nr`은 비어 있던 작은 인덱스(예: 2~4), `last_pid` = 곧 자식 pid. 인자 목록에 `eax`가 없음.
  - 대체: 사전 캡처 1장.
- **B. 부모·자식 `task_struct`와 자식 TSS**
  - 명령: `finish`(Value returned = pid), 그 뒤 `set $c = task[<nr>]`, `p $c->pid`, `p $c->father`, `p current->pid`, `p $c->state`, `p $c->counter`, `p $c->priority`, `p $c->filp[0]`, `p current->filp[0]`, `p $c->filp[0]->f_count`, `p $c->tss.eax`, `p/x $c->tss.eip`, `p/x $c->tss.esp`, `p/x $c->tss.cs`, `p/x $c->tss.esp0`, `p/x $c`, `p/x $c->tss.ldt`.
  - 기대: `father == current->pid`, `state == 0`, `counter == priority`, `filp[0]` 두 값이 같은 주소, `f_count` ≥ 2, `tss.eax == 0`, `tss.eip` == 시연 A의 `eip`, `tss.esp0 == (long)$c + 0x1000`, `tss.ldt == (nr<<4)+(5<<3)`.
  - 대체: 사전 캡처 2장(필드 대조, TSS).
- **C. 같은 EIP, 다른 EAX**
  - 명령: `break *<시연 B의 tss.eip>`, `delete` 나머지, `c` → `p/x $eax`, `p/x $cs`, `c` → 다시 `p/x $eax`.
  - 기대: 두 번 정지, 같은 `$eip`, `$cs=0xf`, `$eax`가 한 번은 pid(양수), 한 번은 0. 순서는 스케줄러에 달림(자식 counter가 가득이라 자식이 먼저인 경우가 많으나 보장 아님).
  - 대체: 사용자 주소 중단점이 QEMU gdbstub에서 다른 태스크(같은 선형 주소를 쓰는 다른 프로세스)에도 걸릴 수 있음 → `$eax`·`current->pid`로 걸러낸다. 실패 시 사전 캡처 2장.

## 이해 확인 질문과 정답
1. **Q.** `copy_process`의 인자에 `eax`가 없는데 자식의 EAX는 어떻게 정해지는가? 부모의 반환 EAX는? **A.** 자식: `p->tss.eax = 0`(fork.c:97)을 직접 쓴다. 부모: `copy_process`가 `last_pid`를 반환(132) → `_sys_fork ret` → `_system_call:95 pushl %eax` → `ret_from_sys_call:121 popl %eax` → `iret`.
2. **Q.** `*p = *current`(fork.c:81) 한 줄이 복사하는 것과 복사하지 않는 것을 하나씩. **A.** 복사: `task_struct` 전체(pid, filp 포인터, ldt, tss 포함, 이후 일부 덮어씀). 미복사: 같은 페이지 뒤쪽의 커널 스택(주석 "doesn't copy the supervisor stack") — 그래서 자식은 커널 안에서 돌아갈 곳이 없고 TSS로 바로 사용자 모드.
3. **Q.** 부모가 fork 직후 `write(fd,…)`를 두 번 하면 자식의 `fd` 오프셋은? **A.** 같이 움직인다. `filp[fd]`가 같은 `struct file`을 가리키고(`*p=*current`로 포인터 복사, 120–122는 `f_count`만 증가) `f_pos`가 그 안에 있다(fs.h:116–119).
4. **Q.** `copy_mem`이 `nr*0x4000000`을 base로 쓰는데, 자식이 사용자 주소 0x1000을 읽으면 선형 주소는? 이 주소에 대응하는 물리 페이지는 부모와 같은가? **A.** 선형 주소 = `nr*0x4000000 + 0x1000`. 물리 페이지는 **같다**(`copy_page_tables`가 항목을 복사하고 `this_page &= ~2`로 양쪽 R/O, memory.c:177–180). 쓰기 전까지 공유. 쓰면 08회차.

## 처음 등장하는 용어
- **`copy_process`**: 새 task_struct를 만들고 TSS·LDT·공유 카운트를 채우는 fork의 본체.
- **`find_empty_process`**: 새 pid와 빈 `task[]` 인덱스(nr)를 정함.
- **nr(태스크 번호)**: `task[]` 인덱스. pid와 다름.
- **`last_pid`**: 마지막으로 발급한 pid.
- **`copy_mem`**: LDT base 설정 + 페이지 테이블 복사 호출.
- **LDT base `nr*0x4000000`**: 태스크별 64 MiB 선형 주소 칸.
- **`copy_page_tables`**: 페이지 테이블 복사(물리 페이지는 공유). 07·08회차 상세.
- **`mem_map`**: 물리 페이지별 참조 카운트 배열.
- **`f_count` / `i_count`**: `struct file` / inode 공유 카운트.
- **`tss.esp0`**: 자식이 다음에 커널로 들어올 때 쓸 커널 스택(자기 페이지 끝).
- **`-EAGAIN` / `-ENOMEM`**: fork 실패 코드(errno.h:30–31).

## 주의: 흔한 오해 / 말하지 말아야 할 것
- "자식도 `copy_process`에서 반환한다"고 말하지 말 것. 자식의 커널 스택은 비어 있고(fork.c:81 주석), 첫 실행은 `switch_to`의 TSS 복원으로 사용자 모드에 바로 도착한다.
- "fork가 메모리를 복사한다"고 말하지 말 것. 페이지 **테이블**을 복사하고 물리 페이지는 R/O로 공유(memory.c:177–184). 복사는 쓰기 시점(08회차).
- `copy_page_tables`의 비트 의미(P/RW/US, `|7`)와 `mem_map`·`LOW_MEM` 조건은 07회차. 오늘은 "항목 복사 + 쓰기 금지 + 카운트 증가"까지만.
- pid와 `task[]` 인덱스 nr을 섞지 말 것. GDT 위치·선형 base는 nr로, 사용자가 보는 번호는 pid.
- `*p = *current`를 "얕은 복사"라고만 말하면 포인터 필드(`filp[]`, `pwd` 등)가 공유된다는 결과를 반드시 덧붙일 것.
- `tss.cr3`는 자식도 부모와 같은 `pg_dir`(sched.h:128 값이 복사됨). "프로세스마다 페이지 디렉터리"는 0.11에 없다(07회차에서 다시).
- `verify_area`/`write_verify`(fork.c:24–37)는 COW 쓰기 검증이므로 08회차. 오늘은 파일에 있다는 것만.
- 시연 C에서 부모·자식 정지 순서는 실행마다 다르다. 캡처 순서를 규칙처럼 말하지 말 것.
- `main.c:12–24`의 inline 이유(task 0 사용자 스택 공유)는 간단히만. task 0의 특수성(스택 `user_stack`, sched.c:67–72)은 05에서 다룸.
- 현대 커널의 `clone` 플래그·`ret_from_fork`는 14회차.

---

# 07. 주소 변환과 페이지 관리

## 핵심 질문
같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가?

## 학습 목표 (3~5개)
1. 논리 주소(선택자:오프셋) → 선형 주소 → 물리 주소의 3단계 변환을 Linux 0.11 기준으로 손으로 계산할 수 있다.
2. 0.11이 태스크 번호 `nr`마다 선형 공간을 64MB 단위(`nr * 0x4000000`)로 나누어 쓰는 방식과, 그 값이 LDT 베이스·`start_code`에 어떻게 기록되는지 설명할 수 있다.
3. `boot/head.s`의 `setup_paging`이 만든 페이지 디렉터리·4개 페이지 테이블(16MB identity mapping)과 PTE 하위 비트 P/RW/US의 의미를 읽을 수 있다.
4. `mm/memory.c`의 `mem_map[]`이 물리 페이지 상태(미사용 0 / 사용 중 n / 커널 영역 USED)를 어떻게 추적하며 `get_free_page`·`free_page`·`copy_page_tables`·`put_page`가 그것을 어떻게 바꾸는지 설명할 수 있다.
5. GDB에서 CR3·페이지 디렉터리·페이지 테이블 항목을 직접 덤프해 한 주소를 물리 주소로 변환하고, 두 태스크의 같은 논리 주소가 다른 물리 페이지에 닿는 것을 확인할 수 있다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| boot/head.s | 15-16 | `_pg_dir` 심볼 = 물리 주소 0 (startup_32 바로 앞) |
| boot/head.s | 108-124 | `pg0`~`pg3` 페이지 테이블 4개(.org 0x1000~0x4000) |
| boot/head.s | 135-141 | `after_page_tables`: `pushl $_main` 후 `jmp setup_paging` |
| boot/head.s | 198-219 | `setup_paging`: 5페이지 0으로 채움, pg_dir[0..3]=pgN+7, 뒤에서부터 `0xfff007`로 PTE 채움, CR3=0, CR0.PG=1 |
| boot/head.s | 234-238 | `_gdt`: 커널 코드/데이터 세그먼트(베이스 0, 16MB) |
| include/linux/head.h | 4-9 | `desc_struct`, `extern unsigned long pg_dir[1024]` |
| include/linux/sched.h | 88 | `start_code,end_code,end_data,brk,start_stack` |
| include/linux/sched.h | 104-106 | `ldt[3]`(0 null, 1 cs, 2 ds&ss), `tss` |
| include/linux/sched.h | 113-131 | `INIT_TASK`: ldt `{0x9f,0xc0fa00}`,`{0x9f,0xc0f200}` (베이스 0, 640KB), tss.cr3=`&pg_dir` |
| include/linux/sched.h | 153-158 | `_TSS(n)`, `_LDT(n)`, `ltr`, `lldt` — GDT에서 태스크별 TSS/LDT 위치 |
| include/linux/sched.h | 188-231 | `_set_base`/`set_base`/`set_limit`/`_get_base`/`get_base`/`get_limit` (디스크립터 비트 분해·조립) |
| kernel/fork.c | 39-61 | `copy_mem`: `nr * 0x4000000`을 새 코드/데이터 베이스로, `p->start_code`, `copy_page_tables` 호출 |
| kernel/fork.c | 81, 111, 115-118, 129-131 | `*p = *current`, `tss.ldt=_LDT(nr)`, copy_mem 실패 처리, GDT에 TSS/LDT 등록 |
| kernel/sched.c | 385-405 | `sched_init`: task 0의 TSS/LDT 디스크립터 설치, `ltr(0)`, `lldt(0)` |
| include/asm/system.h | 65-66 | `set_tss_desc`/`set_ldt_desc` |
| init/main.c | 112-126 | `memory_end`, `buffer_memory_end`, `main_memory_start` 계산 후 `mem_init` 호출 |
| mm/memory.c | 39-57 | `invalidate()`, `LOW_MEM`, `PAGING_MEMORY/PAGES`, `MAP_NR`, `USED`, `mem_map[]` |
| mm/memory.c | 63-83 | `get_free_page`: `scasb`로 mem_map 뒤에서부터 0 탐색, 1로 표시, 페이지 0 채움 |
| mm/memory.c | 89-99 | `free_page`: `mem_map[]--`, 0을 또 해제하면 panic |
| mm/memory.c | 105-131 | `free_page_tables`: 4MB 단위, 테이블 내 모든 PTE의 페이지 해제 후 테이블 페이지 해제 |
| mm/memory.c | 150-189 | `copy_page_tables`: 디렉터리 항목 단위 복사, PTE의 RW 비트 제거(`&= ~2`), `mem_map[]++` |
| mm/memory.c | 197-219 | `put_page`: 디렉터리 항목 없으면 테이블 할당, `page|7` 기록 |
| mm/memory.c | 399-411 | `mem_init`: 전부 USED로 채운 뒤 `start_mem..end_mem` 범위만 0 |
| mm/memory.c | 413-430 | `calc_mem`: 빈 페이지 수, `pg_dir[i]`별 사용 페이지 수 출력 |

## 상태 변화도 / 모드·선택지 비교 범위
- 상태 변화도 ①: **물리 페이지 한 장의 상태** (`mem_map[n]` 값 기준) — `USED(100)`: 커널·버퍼 영역, 할당 불가 / `0`: 미사용 / `1`: 한 태스크가 소유 / `≥2`: 여러 태스크가 공유. 전환 원인: `mem_init`, `get_free_page`, `free_page`, `copy_page_tables`, (08회차에서) `un_wp_page`.
- 상태 변화도 ②: **태스크의 선형 공간 상태** — 생성 전(디렉터리 항목 0) → `copy_mem`으로 베이스 `nr*64MB` 배정 + 페이지 테이블 복사(P=1,RW=0) → 실행 중 `put_page`로 페이지 추가(P=1,RW=1) → `free_page_tables`로 전부 0.
- 비교 ①: **주소의 종류** (범위: 0.11에서 한 메모리 접근이 거치는 주소 3가지 — 논리/선형/물리). 각각 누가 만들고, 어느 표로 변환되며, 어느 소스가 설정하는지.
- 비교 ②: **PTE 하위 비트 값** (범위: 0.11 커널이 실제로 쓰는 PTE 하위 3비트 조합 전부 — `0`, `5`(P+US, 읽기 전용 공유), `7`(P+RW+US)). 다른 조합(예: US=0 커널 전용)은 0.11이 만들지 않음을 명시.
- 비교 ③: **세그먼트 디스크립터 출처** (범위: CPU가 선택자를 해석할 때 참조하는 표 2가지 — GDT(커널 0x08/0x10, TSSn/LDTn)와 LDT(0x0f/0x17)). 1~2회차 내용을 주소 변환 1단계로 재배치.

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문과 15회차 지도 |
| 03–08 | 18 | 배경: 3단계 주소, 선택자→베이스(LDT), 선형 주소 비트 분해, 페이지 디렉터리/테이블 |
| 09–14 | 20 | 코드: head.s setup_paging, PTE 비트, 64MB 분할(copy_mem), INIT_TASK/LDT 디스크립터 |
| 15–22 | 22 | 코드: mem_map, mem_init, get_free_page, free_page, put_page, copy_page_tables, free_page_tables |
| 23–27 | 15 | 상태 변화도 2장 + 비교 3장 |
| 28–35 | 25 | 강사 시연 A/B/C (CR3·pg_dir 덤프, 손 변환, 두 태스크 비교) + 캡처 해설 |
| 36–38 | 8 | 질문의 답: 같은 주소가 왜 다른 메모리인가 (2단 설명) |
| 39–41 | 7 | 이해 확인 질문, 정리·다음 회차 예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약 | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 07. 주소 변환과 페이지 관리 | 제목과 핵심 질문. 부제: "`int x;` 의 주소 `0x1234`가 셸과 `ls`에서 서로 다른 RAM 셀인 이유". | 제목 |
| 02 | 15회차 지도 — 지금 위치 | 15회차 표에 07 강조. 06(fork)에서 이어지고 08(COW)·09(exec)가 오늘의 표를 그대로 쓴다고 예고. 이후 모든 슬라이드 상단에 "배경→코드→상태→시연→답" 미니 지도. | 지도 |
| 03 | 1회차에서 본 그림을 다시: 주소는 세 번 바뀐다 | 1회차 15장(선형/물리 구분)을 확장. 프로그램이 쓰는 숫자(논리) → 세그먼트 베이스 더한 값(선형) → 페이지 표로 찾은 RAM 위치(물리). 세 상자와 두 화살표 그림. | 배경 |
| 04 | 1단계: 선택자 0x17이 베이스가 되는 과정 | 0x17 = index 2, TI=1(LDT), RPL=3. CPU는 현재 LDT의 2번 항목에서 베이스·리밋을 읽는다. 2회차에서 본 디스크립터 8바이트 그림에 베이스 비트가 흩어져 있는 모습(`_get_base`가 조립하는 이유). | 배경 |
| 05 | 2단계: 선형 주소 32비트의 분해 | [31:22] 디렉터리 인덱스(10비트) / [21:12] 테이블 인덱스(10비트) / [11:0] 페이지 내 오프셋(12비트). 예: `0x04001234` → dir 16, table 1, offset 0x234. 1024×1024×4KB = 4GB 그림. | 배경 |
| 06 | 2단계 계속: CR3 → 디렉터리 → 테이블 → 페이지 | CR3가 디렉터리 물리 주소. 디렉터리 항목(PDE)에서 테이블 물리 주소, 테이블 항목(PTE)에서 페이지 물리 주소. 0.11은 CR3=0 고정(`tss.cr3=&pg_dir`, `pg_dir`=0). 그림에 "0.11은 디렉터리 하나를 모든 태스크가 공유"를 표기. | 배경 |
| 07 | 0.11 소스의 관용구: `(addr>>20)&0xffc`, `(addr>>10)&0xffc` | `>>22`로 인덱스를 구해 `*4`하는 것과 `>>20 & 0xffc`가 같은 값임을 비트 그림으로. 테이블 쪽도 동일. memory.c에서 이 식이 반복됨(115, 160-161, 207, 256-257)을 미리 보여 코드 읽기 부담을 줄인다. | 배경 |
| 08 | 왜 64MB씩인가: 태스크 번호가 곧 선형 공간 위치 | `nr * 0x4000000`(fork.c:52). 64MB = 디렉터리 항목 16개. 태스크 0은 0~64MB(실제 640KB), 1은 64MB~, 2는 128MB~ … 최대 64개. 그림: 4GB 선형 공간을 64MB 칸으로 나눈 띠. 오늘 질문의 절반이 여기서 풀린다고 예고. | 배경 |
| 09 | 코드: head.s setup_paging (1/2) 테이블 채우기 | `boot/head.s:198-212` 발췌. `rep stosl`로 5페이지를 0으로, `_pg_dir`에 `pg0+7`…`pg3+7`, `0xfff007`에서 0x1000씩 빼며 뒤에서부터 PTE 기록. 결과 그림: pg0[0]=0x000007, pg3[1023]=0xfff007 — 16MB identity mapping. | 코드 |
| 10 | 코드: head.s setup_paging (2/2) 켜기 | `boot/head.s:213-219`. `xorl %eax; movl %eax,%cr3` (디렉터리=물리 0), `orl $0x80000000,%eax; movl %eax,%cr0`, `ret`가 135-141에서 밀어 둔 `_main`으로 간다. 1회차 27장과 중복이므로 "이제 비트의 의미를 다 안다" 톤으로 짧게. | 코드 |
| 11 | PTE 한 항목의 비트: P / RW / US | 32비트 PTE 그림: [31:12] 페이지 물리 주소, bit0 P, bit1 R/W, bit2 U/S. `+7` = 111b = 존재·쓰기 가능·사용자 접근 가능. `&~2`는 R/W만 끈다. 다음 회차 COW가 이 1비트로 동작한다고 예고. | 코드 |
| 12 | 코드: 태스크 0의 LDT — INIT_TASK | `include/linux/sched.h:113-131` 중 ldt 부분 `{0x9f,0xc0fa00},{0x9f,0xc0f200}` 해독: 베이스 0, 리밋 0x9f(G=1이므로 640KB), 코드 DPL3(0xfa)·데이터 DPL3(0xf2). `tss.cr3=&pg_dir`. "태스크 0의 논리 주소 = 선형 주소" 인 이유. | 코드 |
| 13 | 코드: fork.c copy_mem — 자식에게 새 칸 배정 | `kernel/fork.c:39-61` 전체. `get_limit(0x0f)/0x17`, `get_base(current->ldt[1])`, `nr*0x4000000`, `p->start_code`, `set_base(ldt[1]/[2])`, `copy_page_tables(old,new,limit)`. 실패 시 `free_page_tables`. 그림: 부모 칸→자식 칸. | 코드 |
| 14 | 코드: 디스크립터에서 베이스 꺼내기/넣기 | `sched.h:188-198`(`_set_base`), `214-226`(`_get_base`), `228-231`(`get_limit`은 `lsll` 명령). 베이스 32비트가 바이트 2,3,4,7에 흩어진 그림과 매크로의 `movb`가 그 바이트를 모으는 대응. 읽기만 하고 암기하지 않는다고 안내. | 코드 |
| 15 | 코드: mem_map — 물리 페이지 장부 | `mm/memory.c:43-57`. `LOW_MEM 0x100000`, `PAGING_PAGES 3840`(15MB/4KB), `MAP_NR(addr)=(addr-1MB)>>12`, `USED 100`, `static unsigned char mem_map[3840]`. 1MB 아래는 장부에 없음(커널·BIOS 영역, 공유해도 세지 않음). 그림: 16MB 물리 메모리 띠와 바이트 배열의 대응. | 코드 |
| 16 | 코드: mem_init — 장부 초기화 | `mm/memory.c:399-411` + `init/main.c:112-126`. 전부 USED로 채운 뒤 `main_memory_start..memory_end`만 0. main.c에서 memory_end(최대 16MB)와 buffer_memory_end(1/2/4MB) 결정. QEMU 기본(16MB)에서 버퍼 4MB → 장부에서 할당 가능한 구간은 4MB~16MB. | 코드 |
| 17 | 코드: get_free_page — "첫 번째(사실은 마지막)" 빈 페이지 | `mm/memory.c:63-83` 인라인 어셈블리를 줄 단위로: `std; repne scasb`로 mem_map 끝에서 0 탐색, `movb $1,1(%edi)`로 1 표시, `sall $12; addl LOW_MEM`으로 물리 주소, `rep stosl`로 4KB 0 채움, 없으면 0 반환. 반환값은 **물리 주소**임을 강조. | 코드 |
| 18 | 코드: free_page — 감소시키고, 0이면 panic | `mm/memory.c:89-99`. `addr<LOW_MEM`이면 무시(커널 영역), `HIGH_MEMORY` 이상이면 panic, `mem_map[n]--`가 0이 아니면 반환, 이미 0이었으면 "trying to free free page". 공유 카운트가 여기서 줄어든다. | 코드 |
| 19 | 코드: put_page — 선형 주소에 물리 페이지 붙이기 | `mm/memory.c:197-219`. `page_table=(address>>20)&0xffc` → PDE 없으면 `get_free_page()`로 테이블 만들고 `|7`, 있으면 테이블 주소. `page_table[(address>>12)&0x3ff] = page|7`. 그림: 디렉터리 항목 생성 분기. "no need for invalidate" 주석의 이유(새 항목 추가는 TLB에 없던 것). | 코드 |
| 20 | 코드: copy_page_tables (1/2) — 디렉터리 단위 복사 | `mm/memory.c:150-172`. 4MB 정렬 검사, `from_dir/to_dir` 계산, `to_dir`에 이미 있으면 panic, 새 테이블 `get_free_page()`, `*to_dir = table|7`, `nr = (from==0)?0xA0:1024` (태스크 0에서 복사할 땐 160페이지=640KB만). | 코드 |
| 21 | 코드: copy_page_tables (2/2) — PTE 복사와 공유 카운트 | `mm/memory.c:173-189`. `this_page &= ~2`(RW 제거) 후 자식 PTE에 기록, `this_page > LOW_MEM`이면 **부모 PTE도** 읽기 전용으로 바꾸고 `mem_map[]++`. 마지막 `invalidate()`(CR3 재적재=TLB 비움). 그림: 부모/자식 PTE가 같은 물리 페이지를 가리키고 카운트 2. | 코드 |
| 22 | 코드: free_page_tables — 4MB 단위로 전부 반납 | `mm/memory.c:105-131`. 정렬 검사, `from==0` panic, 디렉터리 항목마다 테이블 1024개 PTE의 페이지 `free_page`, 테이블 페이지 자체도 `free_page`, PDE=0, `invalidate()`. exit(10회차)·exec(09회차)가 호출. | 코드 |
| 23 | 상태 변화도 ①: 물리 페이지 한 장의 일생 | 상태: `USED`(커널/버퍼, 영구) / `0` 미사용 / `1` 단독 소유 / `n≥2` 공유. 전환: `mem_init`→USED 또는 0, `get_free_page` 0→1, `copy_page_tables` 1→2 (RW=0으로), `free_page` n→n-1, 1→0. 변경 데이터: `mem_map[MAP_NR]` 바이트 1개 + 해당 PTE. 유지 조건: 카운트는 PTE 개수와 일치해야 하며 1MB 아래는 세지 않음. | 상태도 |
| 24 | 상태 변화도 ②: 태스크 선형 공간의 상태 | 상태: 비어 있음(PDE 16개 모두 0) → 배정됨(`copy_mem`: LDT 베이스=nr×64MB, 테이블 복사, 모든 PTE RW=0) → 사용 중(`put_page`/08회차 폴트로 PTE 추가·RW=1) → 해제됨(`free_page_tables`). 전환 원인·변경 데이터(ldt[1],ldt[2],start_code,pg_dir[16nr..16nr+15],mem_map). 호출 순서도가 아니라 상태 표임을 명시. | 상태도 |
| 25 | 비교 ①: 논리 / 선형 / 물리 주소 | 범위: 한 접근이 거치는 주소 3가지 전부. 열: 누가 만드나(컴파일러·링커 / CPU 세그먼트 유닛 / CPU 페이징 유닛), 변환 표(LDT·GDT / pg_dir+pg_table / 없음), 0.11에서 설정하는 코드(fork.c:52-55 / head.s:198-212·memory.c put_page / mem_init), GDB에서 보는 법(`p/x current->start_code` / `x/` 선형 / `x/` 물리는 identity 매핑 덕분에 커널 선형으로 읽음). | 비교 |
| 26 | 비교 ②: 0.11이 실제로 만드는 PTE 하위 비트 조합 | 범위: PTE 하위 3비트 조합 중 0.11 커널이 생성하는 값 전부. `0`(부재: free_page_tables, 초기 상태), `5`=101b(P+US, RW=0: copy_page_tables 173-180 결과, try_to_share), `7`=111b(P+RW+US: head.s 0xfff007, put_page, un_wp_page). 사용 여부·전환 조건·관련 소스. "US=0(커널 전용) 페이지는 0.11에 없다 — 커널 보호는 세그먼트 DPL이 담당"을 명시. | 비교 |
| 27 | 비교 ③: 선택자가 참조하는 표 — GDT와 LDT | 범위: CPU가 선택자를 해석할 때 쓰는 표 2개 전부. GDT: 0x08 커널 코드, 0x10 커널 데이터(베이스 0, 16MB, head.s:234-238), `_TSS(n)`/`_LDT(n)`(sched.h:155-156). LDT: 0x0f 코드, 0x17 데이터(태스크별, 베이스 nr×64MB). 어느 쪽이 `lldt`로 바뀌는지(switch_to의 ljmp가 TSS의 ldt 필드로 교체). | 비교 |
| 28 | 시연 준비: lab 환경과 심볼 이름 | `lab/`은 yuan-xy 빌드(GNU as)라 심볼에 `_`가 없음(`pg_dir`, `mem_map`, `task`, `current`). `make debug` → `gdb tools/system` → `target remote :1234`. 캡처 각주 양식: "QEMU i386, lab 빌드, 소스 수정 없음". | 시연 |
| 29 | 시연 A-1: CR3와 페이지 디렉터리 읽기 | 셸 프롬프트까지 부팅 후 GDB Ctrl-C. `monitor info registers`에서 CR3=00000000, CR0에 PG(0x80000000) 켜짐. `x/4wx 0` → `0x00001007 0x00002007 0x00003007 0x00004007` 기대. `x/wx 0x40`(pg_dir[16], 태스크 1)·`x/wx 0x80`(pg_dir[32], 태스크 2)가 0이 아닌 값. | 시연 |
| 30 | 캡처 A-1: info registers / x/4wx 0 | 실제 GDB 출력 캡처. 하단 각주: 실행 환경·수정 없음. 옆에 손 계산: 0x1007 → 테이블 물리 주소 0x1000, 비트 7=P+RW+US. "head.s:203-206의 결과를 지금 눈으로 확인" 표기. | 캡처 |
| 31 | 시연 A-2: 한 주소를 손으로 변환하기 | 대상 태스크 고르기: `p task[2]->pid`, `p/x task[2]->start_code`(기대 0x8000000), `p task[2]->executable->i_num`. 사용자 논리 주소 0 → 선형 0x8000000 → dir 32 → `x/wx 0x80` → 테이블 주소 T → `x/wx T` → PTE → 물리 주소 F. 검증: `x/16xb F` 와 `x/16xb 0x8000000`의 바이트가 같다(둘 다 a.out 텍스트 첫 바이트). | 시연 |
| 32 | 캡처 A-2: 두 경로로 읽은 같은 16바이트 | GDB 캡처 2개 나란히(물리 F로 읽은 것, 선형으로 읽은 것). 각주에 "물리 주소로 읽을 수 있는 이유 = 커널이 0~16MB를 identity 매핑(head.s:198-212)"을 적고, 이것은 관찰 결과이고 "같은 내용"은 추론이 아닌 캡처라고 구분. | 캡처 |
| 33 | 시연 B: 두 태스크의 같은 논리 주소 비교 | 태스크 1(init: `p/x task[1]->start_code` = 0x4000000, `x/wx 0x40`)과 태스크 2(셸)에 대해 논리 주소 0의 PTE를 각각 구함. 기대: 태스크 1은 물리 0x0(커널 head.s 코드, copy_page_tables의 `nr=0xA0` 특례로 커널 저지대 공유), 태스크 2는 ≥ 4MB 영역의 페이지. "숫자 0이 두 번 나오지만 PTE가 다르다" 를 표로. | 시연 |
| 34 | 캡처 B: 태스크 1 vs 태스크 2 PTE | 두 PTE 캡처와 `mem_map` 조회: `p mem_map[(F-0x100000)>>12]`(셸 페이지 기대 1 또는 공유 시 ≥2), 태스크 1 페이지는 <LOW_MEM이라 장부에 없음(`free_page`가 무시하는 이유). 각주: 관찰값은 부팅 시점마다 다를 수 있음. | 캡처 |
| 35 | 시연 C(선택): calc_mem 호출로 장부 요약 보기 | `call calc_mem()` → 콘솔에 "N pages free (of 3840)", "Pg-dir[16] uses k pages", "Pg-dir[32] uses k pages". 실패(함수 호출 중 트랩)하면 사전 캡처로 대체. 기대: 태스크마다 디렉터리 인덱스 16·32·48…에만 항목이 있음 = 64MB 간격. | 시연 |
| 36 | 질문의 답 (1): 선택자는 같아도 LDT가 다르다 | 두 프로세스 모두 CS=0x0f, DS=0x17이지만 `lldt`로 걸린 LDT가 다르고 그 베이스가 nr×64MB로 다르다 → 선형 주소부터 다르다. 그림: 같은 0x1234가 0x4001234와 0x8001234로 갈라짐. | 정리 |
| 37 | 질문의 답 (2): 선형이 달라서 PDE/PTE도 다르다 | 디렉터리 인덱스 16과 32는 서로 다른 페이지 테이블 → 서로 다른 물리 페이지. 단, fork 직후엔 같은 물리 페이지를 RW=0으로 공유(카운트 2) — "다른 메모리"가 되는 순간은 08회차. 현대 리눅스는 LDT 대신 프로세스마다 CR3(디렉터리)를 바꾼다는 한 줄 대비. | 정리 |
| 38 | 오늘 코드가 쓰는 데이터 한 장 요약 | `ldt[1..2]`(베이스/리밋), `start_code`, `pg_dir[1024]`(물리 0), 페이지 테이블(물리 0x1000~0x4000 + get_free_page로 만든 것), `mem_map[3840]`, `HIGH_MEMORY`. 어느 함수가 어느 데이터를 쓰는지 교차표. | 정리 |
| 39 | 이해 확인 질문 | 아래 "이해 확인 질문과 정답" 4문항을 먼저 질문만, 클릭 후 정답. | 질문 |
| 40 | 이해 확인 정답 | 정답과 근거 줄 번호. | 질문 |
| 41 | 정리·다음 회차 예고 | 오늘의 세 표(LDT, pg_dir, mem_map). 08회차: "fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?" — 오늘 본 `&~2`와 `mem_map[]++`가 폴트 핸들러에서 어떻게 풀리는지. 미리 볼 파일: mm/page.s, memory.c 221-272. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
### A. CR3·페이지 디렉터리·페이지 테이블 덤프와 손 변환
- 환경: `lab/`에서 `make debug`(QEMU `-s -S`), 다른 터미널에서 `gdb tools/system`, `target remote :1234`, `c`. 셸 프롬프트가 나오면 GDB에서 Ctrl-C.
- 명령·관찰:
  1. `monitor info registers` → CR0에 PG 비트(0x80000000), CR3=0x00000000. (대체: `p/x $cr3`는 gdbstub 버전에 따라 없을 수 있음.)
  2. `x/4wx 0` → 기대 `0x00001007 0x00002007 0x00003007 0x00004007` (head.s:203-206).
  3. `p task[2]->pid`, `p/x task[2]->start_code` → 기대 `0x8000000` (fork.c:52-53). 셸이 task[2]가 아니면 `p *task[1]@6` 식으로 `executable != 0`인 슬롯을 찾는다.
  4. `x/wx 0x80` → 태스크 2의 PDE (값 끝이 7). 테이블 주소 T = 값 & 0xfffff000.
  5. `x/wx T` → 논리 주소 0의 PTE. 물리 주소 F = 값 & 0xfffff000. 하위 비트가 5인지 7인지 읽는다(공유 여부).
  6. `x/16xb F` 와 `x/16xb 0x8000000` 비교 → 같은 바이트열 기대.
  7. `p mem_map[(F-0x100000)>>12]` → 1(단독) 또는 2 이상(같은 실행 파일을 다른 태스크가 공유 중).
- 중단점: 없음(정지 상태 관찰). 
- 대체 자료: 위 1~7의 사전 캡처 PNG 7장(각주: QEMU i386 TCG, lab 빌드, 수정 없음).

### B. 두 태스크의 같은 논리 주소 비교
- 명령: `p/x task[1]->start_code`(0x4000000), `x/wx 0x40` → T1, `x/wx T1` → 태스크 1의 논리 0 PTE(기대 물리 0x00000000, 하위 비트 5 — copy_page_tables 177의 `&~2`). 태스크 2는 A의 결과 재사용.
- 관찰 대상: 두 PTE의 상위 20비트가 다름. `x/8xb 0`(커널 head.s 첫 바이트, `movl $0x10,%eax` = `b8 10 00 00 00`)과 `x/8xb 0x4000000`이 같은지 확인.
- 기대 출력: 태스크 1 = 커널 코드 공유(1MB 아래라 mem_map 미집계), 태스크 2 = 4MB 이상 영역의 개별 페이지.
- 대체 자료: 사전 캡처 2장.

### C. (선택) calc_mem()
- 명령: GDB에서 `call calc_mem()`. 출력은 QEMU 콘솔(printk).
- 기대 출력: `NNNN pages free (of 3840)`, `Pg-dir[16] uses k pages`, `Pg-dir[32] uses k pages` …(인덱스는 16의 배수만).
- 실패 조건: 함수 호출 중 인터럽트/스택 문제로 멈추면 `Ctrl-C` 후 `return` 하고 사전 캡처로 대체.

## 이해 확인 질문과 정답
1. **Q.** 태스크 번호 3의 사용자 논리 주소 `0x1000`은 선형 주소 얼마인가? 디렉터리 인덱스는?  
   **A.** 베이스 3×0x4000000 = 0xC000000, 선형 0xC001000. 디렉터리 인덱스 = 0xC001000>>22 = 48, 테이블 인덱스 1. (fork.c:52, 슬라이드 05·08)
2. **Q.** `get_free_page()`의 반환값은 선형 주소인가 물리 주소인가? 커널이 그 값을 바로 포인터처럼 쓸 수 있는 이유는?  
   **A.** 물리 주소(memory.c:70-71 `sall $12; addl LOW_MEM`). 커널 세그먼트 베이스가 0이고 0~16MB가 identity 매핑이라 선형=물리로 바로 접근 가능.
3. **Q.** `copy_page_tables`가 자식 PTE뿐 아니라 부모 PTE에서도 RW 비트를 끄는 이유는? 어느 줄인가?  
   **A.** 둘 중 누가 먼저 쓰든 폴트가 나서 복사(COW)가 일어나게 하려고. memory.c:177 `this_page &= ~2`, 180 `*from_page_table = this_page`. 단 LOW_MEM 아래 페이지는 부모 쪽을 바꾸지 않는다(179 조건).
4. **Q.** `mem_map[]`에 1MB 아래 페이지가 없는데, `free_page(0x5000)`을 부르면 어떻게 되는가?  
   **A.** `addr < LOW_MEM`이면 그냥 반환(memory.c:91). 커널·BIOS 영역은 장부 밖이고 해제되지 않는다.

## 처음 등장하는 용어
- 논리 주소 / 선형 주소 / 물리 주소 (logical / linear / physical address)
- 페이지 디렉터리(PDE), 페이지 테이블(PTE), CR3, identity mapping
- P / R/W / U/S 비트, TLB와 `invalidate()`(CR3 재적재)
- `mem_map`, `LOW_MEM`, `MAP_NR`, `USED`, `HIGH_MEMORY`
- 64MB 태스크 슬롯(`nr * 0x4000000`), `start_code`
- `get_free_page`, `free_page`, `put_page`, `copy_page_tables`, `free_page_tables`

## 주의: 흔한 오해 / 말하지 말아야 할 것
- "0.11도 프로세스마다 페이지 디렉터리를 바꾼다"고 말하지 않는다. 0.11은 CR3=0 하나를 전 태스크가 공유하고 LDT 베이스(64MB 칸)로 구분한다. 현대 리눅스와의 차이는 37장에서 한 줄만.
- `get_free_page`가 주는 값을 "가상 주소"라고 부르지 않는다. 물리 주소이며, 커널이 바로 접근하는 것은 identity 매핑 때문이다.
- `mem_map` 카운트가 "참조 중인 프로세스 수"라고 단정하지 않는다. 정확히는 그 물리 페이지를 가리키는 PTE 수(1MB 이상 영역에 한함)다.
- `copy_page_tables`가 "메모리를 복사한다"고 말하지 않는다. 복사되는 것은 페이지 테이블(PTE)뿐이고 데이터 페이지는 공유된다. 실제 복사는 08회차의 `un_wp_page`.
- 태스크 0의 리밋 640KB와 `copy_page_tables`의 `nr=0xA0` 특례를 "버그"라고 하지 않는다. 의도된 설계(memory.c:142-148 주석).
- `invalidate()`를 "캐시 비우기"라고 하지 않는다. TLB(주소 변환 캐시)만 비운다.
- 시연 캡처의 PTE 값·mem_map 값은 부팅마다 달라질 수 있다. 슬라이드의 기대값은 "형태"이고, 구체 숫자는 캡처에 있는 것을 읽는다.

---

# 08. 페이지 폴트와 Copy-on-Write

## 핵심 질문
fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?

## 학습 목표 (3~5개)
1. 페이지 폴트(#PF, 벡터 14)가 발생했을 때 CPU가 남기는 정보(CR2, 에러 코드 P/W/U 비트)와 `mm/page.s`가 그것을 `do_no_page`/`do_wp_page`로 나누는 기준을 설명할 수 있다.
2. `do_wp_page` → `un_wp_page`가 공유 페이지(`mem_map[n]≥2`, RW=0)를 새 페이지로 복사하고 카운트를 줄이는 과정을 PTE·mem_map 값 변화로 추적할 수 있다.
3. `do_no_page`의 세 갈래(빈 페이지 / 다른 태스크와 공유 / 실행 파일에서 읽기)를 구분하고, 0.11의 "요구 적재(demand loading)"가 exec와 어떻게 연결되는지 설명할 수 있다.
4. 80386에서 커널(ring 0) 쓰기가 R/W 비트를 무시하기 때문에 `write_verify`/`verify_area`가 필요한 이유를 설명할 수 있다.
5. GDB에서 fork 직후 첫 쓰기 폴트를 잡아 `mem_map` 카운트와 PTE가 복사 전후로 바뀌는 것을 관찰할 수 있다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| kernel/traps.c | 57, 199 | `void page_fault(void)` 선언, `set_trap_gate(14,&page_fault)` |
| mm/page.s | 12-40 | `_page_fault`: 에러 코드와 eax 교환, 세그먼트 설정, CR2 push, `testl $1,%eax`로 `_do_no_page`/`_do_wp_page` 분기, `iret` |
| mm/memory.c | 33-37 | `oom()`: "out of memory" 출력 후 `do_exit(SIGSEGV)` |
| mm/memory.c | 39-40, 54-55 | `invalidate()`(CR3 재적재), `copy_page(from,to)`(`rep movsl` 1024회) |
| mm/memory.c | 49-50 | `CODE_SPACE(addr)` (do_wp_page에서 `#if 0`으로 꺼져 있음) |
| mm/memory.c | 150-189 | `copy_page_tables` (복습: 177 `&= ~2`, 180 부모 PTE 갱신, 183 `mem_map[]++`) |
| mm/memory.c | 221-238 | `un_wp_page`: 카운트 1이면 RW만 켬, 아니면 새 페이지 할당·카운트 감소·PTE 교체·`copy_page` |
| mm/memory.c | 247-259 | `do_wp_page`: `#if 0` CODE_SPACE 검사, PTE 주소 계산 후 `un_wp_page` |
| mm/memory.c | 261-272 | `write_verify`: PDE 없으면 통과, PTE가 "present+non-writable"(하위 2비트 == 1)이면 `un_wp_page` |
| mm/memory.c | 274-282 | `get_empty_page`: `get_free_page`+`put_page`, 실패 시 `oom` |
| mm/memory.c | 292-334 | `try_to_share`: 상대 태스크 PTE가 clean(bit6 D=0)·present이면 양쪽 RW=0으로 공유, `mem_map[]++` |
| mm/memory.c | 344-363 | `share_page`: `executable->i_count<2`면 포기, 같은 executable 태스크 탐색 |
| mm/memory.c | 365-397 | `do_no_page`: 세 갈래 분기, `bmap`×4, `bread_page`, bss 부분 0 채움, `put_page` |
| mm/memory.c | 197-219 | `put_page` (복습) |
| kernel/fork.c | 20, 24-37 | `write_verify` extern, `verify_area`: 논리→선형(`get_base(ldt[2])`) 후 페이지마다 `write_verify` |
| fs/read_write.c | 64 | `sys_read`가 `verify_area(buf,count)` 호출 — 커널 쓰기 전에 COW 강제 |
| kernel/sys.c | 108, 159, 224 | `verify_area` 다른 호출처(sys_time, sys_times, sys_uname) |
| fs/buffer.c | 296-315 | `bread_page`: 블록 4개를 한 페이지에 읽음 |
| fs/inode.c | 140-143 | `bmap`: 파일 블록 → 디스크 블록 |
| include/signal.h | 23 | `SIGSEGV 11` |
| init/main.c | 11-20 | 주석: 커널 공간에서의 fork는 execve 전까지 COW가 없음(저지대 페이지) → main()이 스택을 쓰지 않는 이유 |
| include/linux/sched.h | 88, 100 | `start_code,end_code,end_data`, `executable` |

## 상태 변화도 / 모드·선택지 비교 범위
- 상태 변화도 ①: **한 선형 페이지(PTE)의 상태** — `부재(P=0)` → `존재·쓰기 가능(7)` → fork로 `존재·읽기 전용·공유(5, count≥2)` → 쓰기 폴트로 `존재·쓰기 가능·단독(7, count=1)` (상대 쪽은 count-1) / `부재`에서 읽기·쓰기 폴트로 `존재(7)` 또는 `공유(5)`. 전환 원인은 CPU 폴트 + 핸들러, 변경 데이터는 PTE 1개 + `mem_map` 1~2바이트 + (복사 시) 4KB 페이지 내용.
- 상태 변화도 ②: **fork→쓰기 시나리오의 부모·자식·mem_map 3자 상태** — (부모 PTE, 자식 PTE, count) 가 (7,—,1) → (5,5,2) → 자식 쓰기 → (5,7′,1 / 새 페이지 1) → 부모 쓰기 → (7,7′,1/1). 
- 비교 ①: **페이지 폴트 에러 코드 비트 조합** (범위: 하위 3비트 P/W/U 8가지 전부 — 사용자/커널 × 읽기/쓰기 × 부재/보호). 각 조합이 0.11에서 발생하는지, 어느 핸들러로 가는지, 커널 모드 쓰기 위반이 386에서 아예 폴트가 안 나는 사실.
- 비교 ②: **`do_no_page`의 세 갈래** (범위: 부재 페이지를 채우는 방법 3가지 전부 — 빈 페이지 / 다른 태스크와 공유 / 디스크에서 읽기). 선택 조건(`executable` 유무, `tmp >= end_data`, `share_page` 성공)·관련 소스.
- 비교 ③: **쓰기 폴트를 일으키는 주체** (범위: 2가지 — 사용자 코드의 쓰기 → CPU #PF → do_wp_page / 커널의 사용자 메모리 쓰기 → 폴트 없음 → `verify_area`가 `write_verify`로 선제 처리). 

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문과 지도 |
| 03–08 | 17 | 배경: 폴트는 예외다, CR2·에러 코드, 07회차 복습(5와 7, count), 요구 적재 개념 |
| 09–14 | 22 | 코드: traps.c 등록, page.s, do_wp_page, un_wp_page, write_verify/verify_area |
| 15–20 | 20 | 코드: do_no_page, get_empty_page, share_page/try_to_share, bread_page·bss 0 채움 |
| 21–26 | 16 | 상태 변화도 2장 + 비교 3장 + fork 시나리오 표 |
| 27–34 | 25 | 강사 시연 A/B (fork 후 첫 쓰기 폴트, mem_map 전후; do_no_page 요구 적재) + 캡처 |
| 35–37 | 8 | 질문의 답 |
| 38–40 | 7 | 이해 확인·정리·예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약 | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 08. 페이지 폴트와 Copy-on-Write | 제목과 핵심 질문. 부제: "복사하지 않고 복사한 척하기". | 제목 |
| 02 | 15회차 지도 — 지금 위치 | 07(주소 변환)의 PTE·mem_map 표를 그대로 사용, 09(exec)가 오늘의 do_no_page를 호출한다는 연결. 미니 지도 범례. | 지도 |
| 03 | 복습: 07회차 끝의 상태 | fork 직후 그림: 부모 PTE=5, 자식 PTE=5, 같은 물리 페이지, `mem_map=2`. "여기서 자식이 `x=1`을 실행하면?" 질문으로 시작. | 배경 |
| 04 | 폴트는 4회차에서 본 예외의 하나다 | IDT 벡터 14, 트랩 게이트(traps.c:199). 4회차 인터럽트 프레임 그림에 **에러 코드 4바이트가 추가**된 모양. 복귀 시 `iret` 전에 에러 코드를 걷어내야 함 → page.s 15·33의 트릭 예고. | 배경 |
| 05 | CPU가 남기는 두 가지 정보: CR2와 에러 코드 | CR2 = 폴트를 낸 선형 주소. 에러 코드 bit0 P(0=부재,1=보호 위반), bit1 W/R(1=쓰기), bit2 U/S(1=사용자 모드). 그림: 3비트 표. "핸들러는 이 둘만으로 무엇을 할지 정한다". | 배경 |
| 06 | 80386의 함정: ring 0 쓰기는 R/W 비트를 무시한다 | 386에는 CR0.WP가 없다(486부터). 커널이 사용자 버퍼에 쓸 때(read()의 buf) 공유 페이지여도 폴트가 나지 않아 부모 페이지를 덮어쓸 수 있음 → 커널이 먼저 `verify_area`로 흉내 내야 함. 오늘 비교 ③의 근거. | 배경 |
| 07 | 요구 적재(demand loading): 없으면 그때 가져온다 | memory.c:7-21 Linus 주석(01.12.91, 02.12.91). exec는 헤더만 읽고 `current->executable`에 inode만 남김(exec.c:11-18 주석) → 실제 코드/데이터는 부재 폴트 때 디스크에서. "30개 /bin/sh를 6MB에서" 일화. | 배경 |
| 08 | 오늘 읽을 함수 지도 | page.s → do_wp_page → un_wp_page / do_no_page → {get_empty_page, share_page→try_to_share, bread_page+put_page} / verify_area → write_verify → un_wp_page. 호출 그래프(상태도와 구분 표기). | 배경 |
| 09 | 코드: page.s — 에러 코드를 eax와 바꾸는 트릭 | `mm/page.s:14-27`. `xchgl %eax,(%esp)`로 에러 코드를 eax에, eax를 스택에 보관(push 한 번 절약). ds/es/fs=0x10. `movl %cr2,%edx; pushl %edx; pushl %eax` → C 인자 (error_code, address). 스택 그림. | 코드 |
| 10 | 코드: page.s — 어느 핸들러로 가는가 | `mm/page.s:28-40`. `testl $1,%eax`: P=0 → `_do_no_page`, P=1 → `_do_wp_page`. `addl $8,%esp`로 인자 제거, pop 순서, `iret`. **W/U 비트는 보지 않음**을 강조(비교 ①에서 다룸). | 코드 |
| 11 | 코드: do_wp_page — PTE 주소 계산 | `mm/memory.c:247-259`. `#if 0` CODE_SPACE 검사(estdio가 코드 영역에 쓰기 때문에 꺼 둠, 250-251 주석). PDE=`*(address>>20&0xffc)`, PTE 주소=`(PDE&0xfffff000)+((address>>10)&0xffc)` → `un_wp_page(&PTE)`. 07회차 관용구 재등장. | 코드 |
| 12 | 코드: un_wp_page — 두 갈래 | `mm/memory.c:221-238`. (a) `old_page>=LOW_MEM && mem_map==1` → `*table_entry |= 2; invalidate()` (복사 없음: 상대가 이미 복사해 갔거나 fork 전 상태). (b) 그 외 → `get_free_page()`, `mem_map[old]--`, `*table_entry = new|7`, `invalidate()`, `copy_page(old,new)`. 그림: 복사 전/후 PTE·count. | 코드 |
| 13 | 코드: write_verify / verify_area — 폴트 없는 COW | `mm/memory.c:261-272` + `kernel/fork.c:24-37`. verify_area: 논리→선형(`+get_base(current->ldt[2])`), 4KB마다 write_verify. write_verify: PDE 없으면 통과(부재는 나중에 do_no_page가 처리), PTE 하위 2비트가 `01`(present, non-writable)이면 un_wp_page. 호출처 `fs/read_write.c:64`. | 코드 |
| 14 | 코드: copy_page와 invalidate | `mm/memory.c:54-55`, `39-40`. `rep movsl` 1024회 = 4KB. `movl $0,%cr3` = TLB 전체 무효화. un_wp_page가 PTE를 바꾼 뒤 invalidate를 **먼저** 하고 복사하는 순서(235-237) — 복사 중엔 새 페이지가 이미 매핑됨. | 코드 |
| 15 | 코드: do_no_page (1/3) — 어디서 온 폴트인가 | `mm/memory.c:365-377`. `address &= 0xfffff000`, `tmp = address - current->start_code`(태스크 내 오프셋). `!executable || tmp >= end_data` → `get_empty_page(address)` 후 return (스택·bss·힙: 0으로 채운 빈 페이지). | 코드 |
| 16 | 코드: get_empty_page | `mm/memory.c:274-282`. `get_free_page` + `put_page`, 실패 시 `free_page(tmp)`(0이어도 무시됨, 91행) 후 `oom()` → `do_exit(SIGSEGV)`. "메모리 부족 = 프로세스 죽음" 정책. | 코드 |
| 17 | 코드: do_no_page (2/3) — 같은 프로그램을 돌리는 다른 태스크와 공유 | `mm/memory.c:378-379` + `344-363` share_page: `executable->i_count<2`면 포기, task[] 역순 탐색, 같은 executable이면 try_to_share. 연결: exec.c가 inode를 `current->executable`에 두는 이유. | 코드 |
| 18 | 코드: try_to_share — clean 페이지만 공유 | `mm/memory.c:292-334`. 상대 PDE/PTE 계산(start_code 오프셋 더함), `(phys_addr & 0x41) != 0x01` → bit6(Dirty)=1이면 공유 안 함, LOW_MEM~HIGH_MEMORY 범위 확인, 내 PDE 없으면 테이블 생성, 양쪽 PTE RW=0(`&= ~2`), `mem_map[]++`. 그림: 두 태스크의 PTE가 하나의 페이지를 공유(5,5,count+1). | 코드 |
| 19 | 코드: do_no_page (3/3) — 디스크에서 4블록 읽기 | `mm/memory.c:380-397`. `block = 1 + tmp/BLOCK_SIZE`(헤더 1블록 건너뜀), `bmap`×4, `bread_page(page, i_dev, nr)`(fs/buffer.c:296-315), `end_data` 넘는 꼬리를 0으로(387-392), `put_page`. 실패 시 `free_page`+`oom`. | 코드 |
| 20 | 코드로 본 "폴트 뒤 재실행" | iret 후 CPU는 **같은 명령**을 다시 실행한다(폴트는 fault형 예외: 저장된 EIP가 폴트 명령 자신). page.s가 레지스터를 모두 복원하는 이유. 4회차 트랩/폴트 구분 복습 한 줄. | 코드 |
| 21 | 상태 변화도 ①: 선형 페이지(PTE) 한 칸의 상태 | 상태: `부재(0)` / `단독 RW(7, count 1)` / `공유 RO(5, count≥2)` / `RO지만 단독(5, count 1)`. 전환: put_page(부재→7), copy_page_tables·try_to_share(7→5, count+1), 쓰기 폴트 un_wp_page(b)(5,n→새 7, 상대 count-1), un_wp_page(a)(5,count1→7), free_page_tables(→0). 변경 데이터·유지 조건(PTE 수 = count) 표. | 상태도 |
| 22 | 상태 변화도 ②: fork 뒤 쓰기 시나리오의 3자 상태 | 열: 부모 PTE / 자식 PTE / 물리 페이지 A count / 물리 페이지 B count. 행: fork 전 (7,—,1,—) → fork 후 (5,5,2,—) → 자식 쓰기 폴트 (5,7→B,1,1) → 부모 쓰기 폴트 (7,7→B,1,1: un_wp_page (a)갈래, 복사 없음). 각 행의 전환 원인 줄 번호. | 상태도 |
| 23 | 비교 ①: 에러 코드 P/W/U 8가지 | 범위: 3비트 조합 전부. 표: (U,W,P) → 의미 → 0.11에서 발생? → 가는 곳. (1,0,0) 사용자 읽기 부재 → do_no_page / (1,1,0) 사용자 쓰기 부재 → do_no_page / (1,1,1) 사용자 쓰기 보호 → do_wp_page(COW) / (1,0,1) 사용자 읽기 보호 → 0.11 PTE는 모두 US=1이라 발생하지 않음 / (0,0,0)·(0,1,0) 커널이 사용자 메모리 접근 중 부재 → do_no_page(예: 아직 적재 안 된 버퍼를 read가 채울 때) / (0,1,1) 커널 쓰기 보호 → **386에서는 폴트 자체가 없음** → verify_area / (0,0,1) 발생 없음. page.s가 P만 본다는 사실을 표 하단에. | 비교 |
| 24 | 비교 ②: 부재 페이지를 채우는 세 갈래 | 범위: do_no_page의 모든 선택지. 빈 페이지(조건 `!executable || tmp>=end_data`, 374-376, 내용 0) / 공유(`share_page` 성공, 378, 내용 다른 태스크 페이지, RO) / 디스크(380-396, 내용 a.out 블록 4개 + 꼬리 0). 각 갈래가 mem_map에 미치는 영향(+1 신규 / 기존 +1 / +1 신규). | 비교 |
| 25 | 비교 ③: 쓰기 위반을 처리하는 두 경로 | 범위: 사용자 쓰기 / 커널의 사용자 공간 쓰기. 사용자: CPU #PF → page.s → do_wp_page → un_wp_page. 커널: 폴트 없음 → 시스템 콜 진입부 verify_area(fork.c:24-37) → write_verify → un_wp_page. 둘 다 `un_wp_page`로 수렴. 호출처 목록(read_write.c:64, sys.c:108/159/224). | 비교 |
| 26 | 숫자로 보는 fork + 자식 쓰기 | 07회차 시연 환경 기준 예시 표: 셸(부모) 페이지 k개 → fork 후 자식 PTE k개 추가, mem_map 각 +1 → 자식이 스택 한 페이지에 쓰면 그 페이지만 count 2→1, 새 페이지 count 1. "복사된 페이지 수 = 실제로 쓴 페이지 수". 실제 수치는 캡처 값으로 바꿀 것임을 각주. | 코드 |
| 27 | 시연 준비: 어떤 쓰기가 첫 폴트를 내는가 | fork에서 돌아온 직후 사용자 코드의 첫 `push`/`call`이 스택 페이지에 쓴다 → 부모든 자식이든 fork 직후 **스택 페이지**가 첫 COW 대상. 따라서 셸에서 아무 명령을 쳐도 `do_wp_page`가 즉시 걸린다. 테스트 프로그램 없이도 시연 가능. (선택) 게스트 gcc로 `cow.c`(전역 변수 쓰기 전후 `getpid`) 컴파일. | 시연 |
| 28 | 시연 A-1: fork 직후 쓰기 폴트 잡기 | GDB: `b un_wp_page`, `c`. 셸에 `ls` 입력. 정지 시 `p current->pid`, `p/x *table_entry`(기대 하위 비트 5), `p/x (*table_entry & 0xfffff000)`=A, `p mem_map[(A-0x100000)>>12]`(기대 2), `bt`로 `do_wp_page ← page_fault` 확인, `p/x $cr2` 또는 `up` 후 `p/x address`. | 시연 |
| 29 | 캡처 A-1: 복사 전 | GDB 로그 캡처. 각주: QEMU i386 TCG, lab 빌드, 수정 없음. 옆에 상태도 ②의 "(5,5,2)" 행을 표시. | 캡처 |
| 30 | 시연 A-2: un_wp_page 통과 후 | `finish` 후 같은 PTE 재조회: `p/x *(unsigned long*)<PTE 주소>`(기대 하위 비트 7, 상위 주소 B≠A), `p mem_map[(A-0x100000)>>12]`(기대 1), `p mem_map[(B-0x100000)>>12]`(기대 1). `x/4wx A`와 `x/4wx B` 내용 동일(복사 직후). 이어서 `c` → 상대 태스크의 쓰기 폴트에서 (a)갈래(`|= 2`, 복사 없음)인지 확인. | 시연 |
| 31 | 캡처 A-2: 복사 후 | 두 번째 캡처. 상태도 ② "(5,7→B,1,1)" 행 표시. "어느 쪽(부모/자식)이 먼저 폴트를 냈는지는 스케줄 순서에 따라 다름"을 각주로. | 캡처 |
| 32 | 시연 B: 요구 적재 — do_no_page 관찰 | `b do_no_page`, 셸에서 새 명령(예: `ls`) → exec 직후 첫 정지. `p/x address`, `p/x current->start_code`, `p address - current->start_code`(기대 0 = 엔트리 페이지), `p error_code`(기대 4 또는 6: U=1,P=0), `p current->executable->i_num`. `finish` 후 PTE가 7이 되고 `x/8xb address`에 a.out 코드. 다음 정지는 스택(`tmp >= end_data` 갈래). | 시연 |
| 33 | 캡처 B: 부재 폴트 두 종류 | 코드 페이지(디스크 갈래)와 스택 페이지(빈 페이지 갈래) 캡처 2장. 비교 ②의 행과 연결. 각주: lab 소스 줄 번호는 src와 다를 수 있음. | 캡처 |
| 34 | 시연 C(선택): 커널 쓰기는 폴트가 없다 | `b write_verify`, 셸에서 `cat`에 입력 → `read()` 경로의 `verify_area`가 호출되는 것을 `bt`로 확인(sys_read ← system_call). 실패 시 사전 캡처. | 시연 |
| 35 | 질문의 답 (1): 부모의 값이 그대로인 이유 | fork는 PTE만 복사하고 둘 다 RO(5)로. 자식의 쓰기 → #PF(U=1,W=1,P=1) → do_wp_page → un_wp_page (b)갈래 → 자식 PTE만 새 페이지 B로. 부모 PTE는 여전히 A. 그림 한 장. | 정리 |
| 36 | 질문의 답 (2): 그래서 fork는 싸다 | 복사되는 것은 "쓴 페이지"뿐. exec가 곧 따라오면(09회차) 대부분 페이지는 복사되지 않고 free_page_tables로 반납. 현대 커널도 같은 원리(단, WP 비트가 있어 커널 쓰기도 폴트). | 정리 |
| 37 | 오늘 코드가 쓰는 데이터 요약 | CR2, 에러 코드, PTE 하위 비트(0/5/7)와 bit6 Dirty, `mem_map`, `current->start_code/end_data/executable`. 함수×데이터 교차표. | 정리 |
| 38 | 이해 확인 질문 | 4문항 질문만. | 질문 |
| 39 | 이해 확인 정답 | 정답과 근거 줄 번호. | 질문 |
| 40 | 정리·다음 회차 예고 | 09회차 "PID는 그대로인데 프로그램은 어떻게 바뀌는가?" — 오늘 본 do_no_page가 exec 직후 프로그램을 실제로 적재한다. 미리 볼 파일: fs/exec.c, include/a.out.h. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
### A. fork 뒤 첫 쓰기 폴트에서 mem_map 전후 관찰
- 환경: `lab/` `make debug`, `gdb tools/system`, `target remote :1234`, `c`, 셸 프롬프트 확인.
- 중단점: `b un_wp_page` (`do_wp_page`보다 PTE 포인터 `table_entry`를 바로 볼 수 있어 편함. `b do_wp_page`로 잡은 뒤 `p/x address`, `p error_code`를 먼저 보여 주고 `s`로 내려가도 됨).
- 절차:
  1. 셸에 `ls` 입력 → 셸이 fork → 정지.
  2. `p current->pid` (부모 셸 pid 또는 자식 pid — 스케줄 순서에 따라 다름), `bt` (기대: `un_wp_page ← do_wp_page ← page_fault`).
  3. `p/x *table_entry` → 기대 `0x....005` (P+US, RW=0). A = 값 & 0xfffff000.
  4. `p mem_map[(A-0x100000)>>12]` → 기대 2.
  5. `finish` → 돌아온 뒤 `p/x *(unsigned long*)$PTE`(3에서 `p table_entry`로 주소를 적어 둔다) → 기대 `0x....007`, 새 주소 B≠A.
  6. `p mem_map[(A-0x100000)>>12]` → 1, `p mem_map[(B-0x100000)>>12]` → 1.
  7. `c` → 다음 un_wp_page 정지(상대 태스크의 같은 논리 페이지일 수 있음). `p/x *table_entry` → 하위 5, `p mem_map[...]` → 1 → `finish` 후 같은 주소에 하위 7(복사 없음, (a)갈래).
- 기대 출력 요지: 복사 전 (5, count 2) → 복사 후 (7, 새 페이지, count 1/1) → 상대는 (5,count1) → (7) 제자리 승격.
- 대체 자료: 위 2~7의 사전 캡처 4장. 각주에 "lab 빌드, 수정 없음, 값은 부팅마다 다름".

### B. 요구 적재(do_no_page) 관찰
- 중단점: `b do_no_page` (A의 중단점은 `delete` 또는 `disable`).
- 절차: 셸에 명령 입력 → exec 직후 정지. `p/x address`, `p/x current->start_code`, `p (address & 0xfffff000) - current->start_code` → 기대 0 (엔트리 `a_entry`=0의 페이지). `p error_code` → 기대 4(U=1,W=0,P=0) 또는 6(쓰기). `p current->executable->i_num`. `finish` → `x/8xb address`에 코드 바이트. `c` → 다음 정지에서 `tmp >= end_data` 갈래(스택) 확인: `p/x address`가 64MB 칸 끝 근처(`start_code + 0x4000000 - ...`).
- 대체 자료: 사전 캡처 2장(코드 페이지·스택 페이지).

### C. (선택) write_verify 경로
- 중단점: `b write_verify`. 셸에서 `cat` 실행 후 한 줄 입력 → read()의 verify_area → 정지. `bt`에 `verify_area ← sys_read ← system_call` 기대. 각주: 줄 번호는 lab 기준.
- 대체 자료: 사전 캡처 1장.

## 이해 확인 질문과 정답
1. **Q.** `page.s`는 에러 코드의 어느 비트만 보고 핸들러를 고르는가? W 비트는 어디서 쓰이는가?  
   **A.** bit0 P만 (`testl $1,%eax`, page.s:28). W/U 비트는 0.11 핸들러가 쓰지 않는다. do_wp_page는 "present인데 폴트" = 쓰기 보호 위반으로 가정한다.
2. **Q.** `un_wp_page`가 복사 없이 `|= 2`만 하는 경우는 언제인가?  
   **A.** 페이지가 LOW_MEM 이상이고 `mem_map[]==1`일 때(memory.c:226-229). 상대 태스크가 이미 자기 복사본으로 갈아탔거나, 공유가 끝난 경우.
3. **Q.** `read(fd, buf, n)`에서 buf가 fork로 공유 중인 페이지에 있으면 커널은 어떻게 부모 페이지를 보호하는가?  
   **A.** 386은 ring 0 쓰기에 R/W 비트를 적용하지 않으므로 폴트가 나지 않는다. `sys_read`가 먼저 `verify_area(buf,count)`(read_write.c:64) → `write_verify` → `un_wp_page`로 미리 분리한다.
4. **Q.** exec 직후 프로그램의 첫 명령 페이지는 메모리에 있는가? 없다면 누가 언제 채우는가?  
   **A.** 없다. 첫 명령 fetch가 부재 폴트(P=0)를 내고 `do_no_page`가 `bmap`/`bread_page`로 a.out 블록 4개를 읽어 `put_page`한다(memory.c:380-394).

## 처음 등장하는 용어
- 페이지 폴트(#PF, 벡터 14), CR2, 에러 코드 P/W/U
- Copy-on-Write(COW), 쓰기 보호 폴트, 요구 적재(demand loading)
- `do_no_page`, `do_wp_page`, `un_wp_page`, `write_verify`, `verify_area`, `get_empty_page`, `share_page`, `try_to_share`
- Dirty 비트(PTE bit6), `oom()`, `SIGSEGV`
- `bmap`, `bread_page`, `BLOCK_SIZE`(1024)

## 주의: 흔한 오해 / 말하지 말아야 할 것
- "fork가 메모리를 복사한다"고 말하지 않는다. fork는 PTE를 복사하고, 데이터 페이지 복사는 첫 쓰기 폴트 때 `un_wp_page`가 한다.
- "부모는 원본, 자식은 복사본"이라고 단정하지 않는다. 먼저 쓰는 쪽이 새 페이지를 받는다(스케줄 순서에 따라 부모가 먼저일 수도 있다). 캡처의 pid로 확인시킨다.
- 에러 코드의 W/U 비트로 0.11이 분기한다고 말하지 않는다. P 비트만 본다.
- "커널이 사용자 페이지에 쓰면 폴트가 나서 COW가 된다"고 말하지 않는다. 386에는 CR0.WP가 없어 폴트가 없고, `verify_area`가 대신한다. 현대 CPU/커널과의 차이를 36장에서 한 줄만.
- `do_wp_page`의 `#if 0` CODE_SPACE를 "코드 영역 쓰기는 막힌다"고 설명하지 않는다. 꺼져 있다(249-254).
- `try_to_share`의 `0x41` 검사에서 bit6을 "Accessed"라고 하지 않는다. Dirty 비트다(Accessed는 bit5).
- `oom()`이 "메모리를 회수한다"고 말하지 않는다. 메시지 출력 후 프로세스를 SIGSEGV로 종료할 뿐이다(memory.c:33-37).
- 시연의 `mem_map` 값·물리 주소는 환경에 따라 달라진다. 캡처 각주에 lab 빌드·수정 여부를 반드시 적는다.

---

# 09. exec()와 프로그램 실행

## 핵심 질문
PID는 그대로인데 프로그램은 어떻게 바뀌는가?

## 학습 목표 (3~5개)
1. `execve()` 한 호출이 `lib/execve.c`의 `int $0x80` → `system_call.s`의 `_sys_execve` → `fs/exec.c`의 `do_execve`에 도달하고, 커널 스택에 저장된 EIP/ESP를 **덮어써서** 돌아가는 경로를 설명할 수 있다.
2. a.out 헤더(`struct exec`)의 필드와 0.11이 받아들이는 형식(ZMAGIC만)·거부 조건(ENOEXEC 등)을 읽고, 실행 파일 하나가 어느 검사에서 걸리는지 말할 수 있다.
3. "돌이킬 수 없는 지점"(exec.c:318) 이후 `free_page_tables`·`change_ldt`·`create_tables`가 주소 공간을 비우고 새 LDT 리밋과 인자 페이지만 남기는 과정을 태스크 데이터 변화로 추적할 수 있다.
4. exec가 코드를 읽지 않는다는 점(요구 적재)과, 새 프로그램의 첫 명령이 08회차의 `do_no_page`로 적재된다는 연결을 설명할 수 있다.
5. GDB에서 `do_execve`를 멈춰 LDT 베이스/리밋·`eip[0]`·`eip[3]`·`executable`이 바뀌고 `pid`는 그대로임을 관찰할 수 있다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| lib/execve.c | 7-10 | `_syscall3(int,execve,const char *,file,char **,argv,char **,envp)` |
| include/unistd.h | 71, 172-184 | `__NR_execve 11`, `_syscall3` 매크로(`int $0x80`, eax=번호, ebx/ecx/edx 인자, 음수면 errno) |
| include/linux/sys.h | 12, 74-76 | `sys_execve` 선언, `sys_call_table[]`에서 11번 |
| kernel/system_call.s | 35-46 | 커널 스택 프레임 오프셋 `EAX..OLDSS` (EIP=0x1C, CS=0x20, EFLAGS=0x24, OLDESP=0x28) |
| kernel/system_call.s | 80-93 | `_system_call`: 인자 push, ds/es=0x10, fs=0x17, `call _sys_call_table(,%eax,4)` |
| kernel/system_call.s | 200-205 | `_sys_execve`: `lea EIP(%esp),%eax; pushl %eax; call _do_execve` — 저장된 EIP의 **주소**를 넘김 |
| include/a.out.h | 6-15 | `struct exec`: a_magic, a_text, a_data, a_bss, a_syms, a_entry, a_trsize, a_drsize |
| include/a.out.h | 17-19, 21-28 | `N_MAGIC`, `OMAGIC 0407`, `NMAGIC 0410`, `ZMAGIC 0413` |
| include/a.out.h | 30-34, 40, 42-45, 92-93 | `N_BADMAG`, `_N_HDROFF`, `N_TXTOFF`(ZMAGIC이면 SEGMENT_SIZE), `PAGE_SIZE 4096`, `SEGMENT_SIZE 1024` → 텍스트는 파일 1024바이트부터 |
| include/linux/fs.h | 49 | `BLOCK_SIZE 1024` (exec.c:305 검사와 일치) |
| fs/exec.c | 7-18 | `#!` 처리는 tytso, 요구 적재 주석 |
| fs/exec.c | 39 | `MAX_ARG_PAGES 32` (인자+환경 최대 128KB) |
| fs/exec.c | 46-70 | `create_tables`: 새 사용자 스택에 envp/argv 포인터 배열과 argc·argv·envp를 쌓고 sp 반환 |
| fs/exec.c | 75-85 | `count`: NULL까지 포인터 개수 |
| fs/exec.c | 104-152 | `copy_strings`: 사용자/커널 문자열을 page[] 꼭대기부터 거꾸로 복사, from_kmem 0/1/2 |
| fs/exec.c | 154-177 | `change_ldt`: 코드 리밋=텍스트 페이지 올림, 데이터 리밋=64MB, fs=0x17 재적재, 인자 페이지를 64MB 끝에 put_page |
| fs/exec.c | 182-203 | `do_execve` 진입: supervisor 호출 panic, page[] 초기화, `namei`, argc/envc |
| fs/exec.c | 204-220 | `restart_interp`: 정규 파일 검사(EACCES), setuid/setgid, 실행 권한(ENOEXEC) |
| fs/exec.c | 221-225 | 첫 블록 `bread`, 헤더 복사 |
| fs/exec.c | 226-297 | `#!` 해석: 인터프리터 이름/인자 파싱, argv 재구성, `namei(interp)` 후 `goto restart_interp` |
| fs/exec.c | 298-309 | ZMAGIC·재배치 없음·크기 검사, `N_TXTOFF != BLOCK_SIZE` 검사 |
| fs/exec.c | 310-317 | 스크립트가 아니면 여기서 envp/argv 복사 |
| fs/exec.c | 318-333 | 돌이킬 수 없는 지점: executable 교체, sigaction 초기화, close_on_exec, `free_page_tables`×2, math, `change_ldt` |
| fs/exec.c | 334-346 | `create_tables`, brk/end_data/end_code, start_stack, euid/egid, 마지막 데이터 페이지 꼬리 0 채움, `eip[0]=a_entry`, `eip[3]=p` |
| fs/exec.c | 347-352 | `exec_error2`(iput) / `exec_error1`(인자 페이지 해제) |
| include/errno.h | 21, 26, 27, 31, 32 | `ENOENT 2`, `E2BIG 7`, `ENOEXEC 8`, `ENOMEM 12`, `EACCES 13` |
| kernel/exit.c | 102-107, 122-123 | `do_exit`도 같은 `free_page_tables` 두 줄과 `iput(executable)` 사용 |
| init/main.c | 162-165, 179-184, 190-200 | init이 자식에서 `execve("/bin/sh", ...)` 하는 두 곳 |
| mm/memory.c | 105-131, 365-397 | `free_page_tables`(복습), `do_no_page`(exec 직후 첫 적재) |
| kernel/fork.c | 52-55 | 베이스는 fork 때 정해지고 exec는 바꾸지 않음(change_ldt 162-166이 같은 베이스를 다시 씀) |

## 상태 변화도 / 모드·선택지 비교 범위
- 상태 변화도 ①: **한 태스크의 "프로그램 상태"** — `구(舊) 프로그램 실행 중` → (execve 진입, 검사 통과 전: 실패 시 원상 복귀 가능) `검사 중` → (318 이후) `주소 공간 비움: executable=새 inode, 페이지 테이블 0, LDT 리밋 새 값, 인자 페이지 32장만 매핑` → (iret) `새 프로그램 첫 명령 fetch` → (do_no_page) `코드 페이지 적재됨`. 전환 원인·변경되는 데이터(`executable`, `ldt[1..2]`, `pg_dir[16nr..]`, `brk/end_code/end_data/start_stack`, `sigaction`, `filp`(close_on_exec), `euid/egid`, 커널 스택의 EIP/ESP)·유지되는 데이터(`pid`, `father`, `pwd/root`, `uid/gid`, `ldt` **베이스**, `tss`의 나머지, 나머지 fd).
- 상태 변화도 ②: **인자 문자열의 위치 변화** — 사용자(구 주소 공간) 문자열 → `copy_strings`로 커널 물리 페이지 `page[31..]` 꼭대기부터 → `change_ldt`로 새 주소 공간 64MB 끝에 매핑 → `create_tables`가 그 아래에 포인터 배열·argc 쌓음 → `eip[3]=p`로 새 ESP.
- 비교 ①: **실행 파일 형식** (범위: `a.out.h`가 정의한 매직 3가지 + `#!` 스크립트 + 그 외 전부). OMAGIC(0407, 거부), NMAGIC(0410, 거부), ZMAGIC(0413, 유일하게 허용: 헤더 1KB 뒤 페이지 정렬 텍스트 → 요구 적재 가능), `#!`(인터프리터로 재시작, 1회만), 나머지(ENOEXEC).
- 비교 ②: **do_execve의 오류 반환 경로** (범위: exec.c가 실제로 반환하는 errno 전부 — ENOENT, EACCES, ENOEXEC, ENOMEM — 와 "정의만 있고 쓰이지 않는" E2BIG). 각 조건·줄·되돌릴 수 있는지(모두 318 이전).
- 비교 ③: **`copy_strings`의 `from_kmem` 3가지** (범위: 0/1/2 전부). 문자열·포인터 배열이 각각 사용자/커널 공간인 경우와 fs 레지스터 조작, 어느 호출에서 쓰이는지(311-312: 0 / 273: 1 / 276, 279: 2).

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–02 | 5 | 핵심 질문과 지도 |
| 03–08 | 17 | 배경: 라이브러리 → 시스템 콜 → sys_execve, 커널 스택 프레임과 eip 포인터, a.out 파일 그림 |
| 09–15 | 24 | 코드: 헤더·매직, do_execve 진입과 검사, #! 처리, copy_strings |
| 16–22 | 22 | 코드: 돌이킬 수 없는 지점, free_page_tables, change_ldt, create_tables, eip/esp 덮어쓰기, 첫 폴트 |
| 23–27 | 15 | 상태 변화도 2장 + 비교 3장 |
| 28–35 | 25 | 강사 시연 A/B/C (do_execve 정지, LDT·eip 변화, #! 재시작) + 캡처 |
| 36–38 | 7 | 질문의 답 |
| 39–41 | 5 | 이해 확인·정리·예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약 | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 09. exec()와 프로그램 실행 | 제목과 핵심 질문. 부제: "같은 몸, 다른 프로그램". | 제목 |
| 02 | 15회차 지도 — 지금 위치 | 06 fork → 07 주소 변환 → 08 COW → **09 exec** → 10 종료. 1회차에서 본 `init → fork → execve("/bin/sh")`(main.c:179-184)가 오늘의 입구. 미니 지도 범례. | 지도 |
| 03 | 셸이 명령을 실행하는 두 호출 | `fork()` 뒤 자식이 `execve(path, argv, envp)`. 06회차 fork 그림에 exec 상자 추가. "fork는 몸을 복제, exec는 몸 안의 프로그램을 교체". | 배경 |
| 04 | 코드: 사용자 쪽 — lib/execve.c 10줄 | `lib/execve.c:7-10` 전체 + `unistd.h:172-184` 매크로 전개: eax=11(`__NR_execve`, unistd.h:71), ebx=file, ecx=argv, edx=envp, `int $0x80`, 음수면 `errno=-res; return -1`. 4회차 write()와 같은 틀. | 배경 |
| 05 | 코드: system_call.s — 프레임과 sys_execve | `system_call.s:35-46` 오프셋 표와 `80-93` 진입부(복습), `200-205` `_sys_execve`: `lea EIP(%esp),%eax` = 저장된 EIP의 **주소**를 첫 인자로. 그림: 커널 스택 프레임에서 `eip[0]`=EIP, `eip[1]`=CS, `eip[2]`=EFLAGS, `eip[3]`=OLDESP. 오늘의 마지막 두 줄(344-345)이 여기 쓴다고 예고. | 배경 |
| 06 | a.out 파일은 어떻게 생겼나 | 그림: [헤더 32B][패딩 → 1024B][텍스트 a_text][데이터 a_data][심볼…]. 메모리 배치: 텍스트 0부터, 데이터 그 뒤, bss a_bss, 스택은 64MB 끝에서 아래로. `a_entry`(보통 0). ZMAGIC = "텍스트가 1KB 경계에서 시작해 블록 단위로 읽기 좋음". | 배경 |
| 07 | 0.11 사용자 주소 공간 한 장 | 논리 0 ~ 64MB. [텍스트][데이터][bss][brk→힙 ↑] … [↓스택][인자·환경 페이지 ≤32장]64MB. `end_code`, `end_data`, `brk`, `start_stack`이 각각 어디를 가리키는지. 07회차 64MB 칸과 동일 그림. | 배경 |
| 08 | 오늘 읽을 함수 지도 | execve(라이브러리) → _system_call → _sys_execve → do_execve → {namei, bread, copy_strings, free_page_tables, change_ldt→put_page, create_tables} → iret → #PF → do_no_page. 호출 순서도(상태도와 구분). | 배경 |
| 09 | 코드: struct exec와 매직 | `a.out.h:6-15`, `21-28`. 필드 설명, `0413` 8진수 = 0x10B. `N_TXTOFF`(42-45): ZMAGIC이면 `_N_HDROFF+32` = `SEGMENT_SIZE`(92-93, 1024) → `BLOCK_SIZE`와 같아야 함(exec.c:305). | 코드 |
| 10 | 코드: do_execve 진입 | `fs/exec.c:182-203`. 인자 `eip`(커널 스택 포인터), `tmp`, filename/argv/envp(사용자 포인터, fs로 읽음). `(0xffff & eip[1]) != 0x000f` → 커널 모드 호출 panic(1회차 move_to_user_mode 뒤 CS=0x0f와 연결). `p = 128KB-4`. `namei`(12회차 예고) → ENOENT. `count`로 argc/envc. | 코드 |
| 11 | 코드: 권한 검사와 setuid | `fs/exec.c:204-220`. `S_ISREG` 아니면 EACCES. `e_uid/e_gid`(S_ISUID/S_ISGID면 파일 소유자). `i>>=6`/`>>=3`로 소유자/그룹/기타 비트 선택, 실행 비트 없고 (어떤 x비트도 없거나 non-suser)면 **ENOEXEC**(EACCES가 아님에 주목). | 코드 |
| 12 | 코드: 헤더 읽기와 형식 검사 | `fs/exec.c:221-225`, `298-309`. `bread(i_dev, i_zone[0])`로 첫 블록 → `ex` 복사. ZMAGIC 아님 / 재배치 정보 있음 / text+data+bss > 48MB / 파일 크기 부족 → ENOEXEC. `N_TXTOFF != BLOCK_SIZE` → printk 후 ENOEXEC. | 코드 |
| 13 | 코드: #! 스크립트 (1/2) — 파싱 | `fs/exec.c:226-256`. `b_data[0..1]=="#!"`이고 `!sh_bang`일 때만. 버퍼 1022바이트, 첫 줄, 공백 건너뜀, 인터프리터 경로·이름(`/` 뒤)·선택 인자 분리. 빈 줄이면 ENOEXEC. | 코드 |
| 14 | 코드: #! 스크립트 (2/2) — argv 재구성과 재시작 | `fs/exec.c:257-297`. 처음 한 번만 envp/argv[1..] 복사(261-264), 그 위에 스크립트 파일명(from_kmem=1), 인터프리터 인자·이름(from_kmem=2)을 **역순**으로 얹어 argv = [interp, i_arg, script, 원래 argv[1..]]. `set_fs(get_ds())` 후 `namei(interp)`, `goto restart_interp`. sh_bang=1이라 두 번째 #!은 처리하지 않음(중첩 불가). | 코드 |
| 15 | 코드: copy_strings — 거꾸로 채우는 128KB | `fs/exec.c:104-152`. argc부터 역순, 각 문자열 길이 세고(`len`), `p`를 줄이며 `page[p/PAGE_SIZE]`가 없으면 `get_free_page`, 바이트 단위 `get_fs_byte`. from_kmem에 따른 `set_fs` 토글. 반환값 p = 남은 공간 오프셋. 그림: page[31] 꼭대기에서 왼쪽으로 자라는 문자열. | 코드 |
| 16 | 코드: 돌이킬 수 없는 지점 | `fs/exec.c:318-327`. 주석 "point of no return". `iput(구 executable)`, `executable = inode`, 32개 `sa_handler = NULL`(시그널 핸들러는 구 프로그램의 주소이므로), `close_on_exec` 비트가 켜진 fd `sys_close`. 이 뒤로는 오류 반환 없음. | 코드 |
| 17 | 코드: 주소 공간 비우기 | `fs/exec.c:328-332`. `free_page_tables(get_base(ldt[1]), get_limit(0x0f))`, 데이터도 동일 — 07회차 함수가 모든 PTE·페이지·테이블을 반납(공유 페이지는 count만 감소). `last_task_used_math` 정리. `do_exit`(exit.c:106-107)와 같은 두 줄임을 대비. | 코드 |
| 18 | 코드: change_ldt — 리밋만 바뀌고 베이스는 그대로 | `fs/exec.c:154-177`. `code_limit = (a_text+4095)&~4095`, `data_limit = 0x4000000`, `code_base = get_base(ldt[1])`(fork 때 nr×64MB, fork.c:52-55) 를 **그대로** 다시 set_base, `set_limit`×2. `pushl $0x17; pop %fs`(새 리밋 반영). 인자 페이지를 `data_base + 64MB - 4KB×k`에 `put_page`(page[i]가 있는 것만). 반환 data_limit. | 코드 |
| 19 | 코드: create_tables — 새 스택 꼭대기 | `fs/exec.c:46-70` + `333-334`. `p += 64MB - 128KB` 로 p를 새 논리 주소로 환산. 4바이트 정렬, envp 배열(envc+1), argv 배열(argc+1), `envp, argv, argc` 순으로 push(56-58). 문자열을 훑으며 포인터 채움. 그림: 스택 꼭대기 레이아웃 [argc][argv][envp][argv[0..]][NULL][envp[0..]][NULL][문자열…]64MB. | 코드 |
| 20 | 코드: 태스크 필드 갱신과 꼬리 0 채움 | `fs/exec.c:335-343`. `end_code=a_text`, `end_data=a_text+a_data`, `brk=+a_bss`, `start_stack=p&~0xfff`, `euid/egid`. 341-343: `a_text+a_data`부터 페이지 끝까지 `put_fs_byte(0,…)` → 이 쓰기가 **첫 do_no_page**(디스크 갈래, 08회차 380-396)를 일으켜 마지막 데이터 페이지가 적재되고 bss 앞부분이 0이 됨. | 코드 |
| 21 | 코드: 마법의 두 줄 — eip[0], eip[3] | `fs/exec.c:344-346`. `eip[0] = ex.a_entry`(커널 스택의 저장된 EIP), `eip[3] = p`(저장된 ESP). `return 0` → `_sys_execve`의 `ret` → `ret_from_sys_call` → `iret`가 **새 EIP/ESP**로 복귀. CS/SS는 0x0f/0x17 그대로지만 LDT 리밋이 달라짐. 그림: 프레임의 두 칸이 덮어써진 모습. | 코드 |
| 22 | 코드: 첫 명령은 아직 메모리에 없다 | iret 후 CS:EIP=0x0f:a_entry fetch → PTE 부재 → #PF(U=1,P=0) → `do_no_page`(memory.c:365-397): `tmp=0 < end_data`, `share_page`(같은 /bin/sh가 떠 있으면 공유!), 아니면 `bmap`×4+`bread_page`. 08회차 시연 B와 동일 장면. | 코드 |
| 23 | 상태 변화도 ①: 태스크의 프로그램 상태 | 상태 5개: 구 프로그램 실행 / 검사 중(복귀 가능) / 주소 공간 비움(318~333) / 새 프레임 준비(334~346) / 새 프로그램 첫 폴트. 각 전환의 원인(줄)과 변경 데이터 vs 유지 데이터 표(pid·father·pwd·root·uid·LDT 베이스·열린 fd(비 close-on-exec)는 유지). 호출 순서도 아님을 명시. | 상태도 |
| 24 | 상태 변화도 ②: 인자 문자열의 네 위치 | (1) 구 사용자 공간 → (2) 커널 물리 페이지 page[] 꼭대기(copy_strings) → (3) 새 공간 64MB 끝에 매핑(change_ldt put_page, 물리 페이지 이동 없음) → (4) 그 아래 포인터 배열과 argc(create_tables). 변경 데이터: page[32], PTE 32개, 새 스택 메모리. 유지 조건: 문자열은 한 번만 복사됨. | 상태도 |
| 25 | 비교 ①: 실행 파일 형식 — 받아들이는 것과 거부하는 것 | 범위: a.out 매직 3가지 + #! + 기타. 열: 매직 값, 메모리 배치 특성, 0.11 처리(ZMAGIC만 허용: 299행 / OMAGIC·NMAGIC: ENOEXEC / #!: 1회 재시작 226-297 / 기타: ENOEXEC), 이유(요구 적재는 블록 정렬된 텍스트가 필요). ELF는 1991년에 없음(현대 비교 한 줄). | 비교 |
| 26 | 비교 ②: 오류 반환 경로 전부 | 범위: do_execve가 반환하는 errno. ENOENT(199-200 파일 없음, 290-293 인터프리터 없음) / EACCES(205-208 정규 파일 아님, 221-224 첫 블록 읽기 실패) / ENOEXEC(216-220 실행 권한 없음, 243-246 #! 빈 줄, 299-304 형식, 305-309 TXTOFF) / ENOMEM(281-284, 313-316 copy_strings 0). 모두 318 이전 → 구 프로그램으로 복귀, 라이브러리가 errno 설정. **E2BIG**: errno.h:26에 정의만 있고 exec.c는 쓰지 않음(인자 초과는 128KB 페이지 부족 → ENOMEM 경로). | 비교 |
| 27 | 비교 ③: copy_strings의 from_kmem 0/1/2 | 범위: 3가지 전부. 문자열 위치 / 포인터 배열 위치 / fs 조작 시점(115-116, 118-123, 136-143) / 호출처(0: 262-263·311-312 사용자 argv, 1: 273 커널에 있는 `&filename` 배열+사용자 문자열, 2: 276·279 인터프리터 이름·인자 모두 커널 buf). | 비교 |
| 28 | 시연 준비 | lab 심볼: `do_execve`, `sys_execve`, `change_ldt`(static이지만 -g로 보임), `current`. 줄 번호는 lab 소스 기준이므로 `list do_execve` 로 확인 후 중단점. 사용자 문자열은 `x/s (char*)current->start_code + (long)filename` 으로 읽는다(fs 세그먼트 보정). | 시연 |
| 29 | 시연 A-1: do_execve 진입 시점 | `b do_execve`, 셸에 `ls` 입력 → 정지. `p current->pid`(자식 pid), `x/s (char*)current->start_code+(long)filename`(기대 "/bin/ls" 또는 "/usr/bin/ls"), `p/x current->ldt[1]`, `p/x current->ldt[2]`, `p/x current->ldt[1].a & 0xffff`(코드 리밋, 페이지 단위: 셸의 텍스트 크기), `p current->executable->i_num`(셸 inode), `p/x eip[0]`, `p/x eip[3]`(셸의 복귀 EIP/ESP). | 시연 |
| 30 | 캡처 A-1: 진입 시점 값 | GDB 캡처. 각주: QEMU i386 TCG, lab 빌드, 수정 없음. 옆에 "바뀔 값 / 그대로일 값" 체크리스트. | 캡처 |
| 31 | 시연 A-2: 마법의 두 줄 전후 | `b exec.c:<eip[0]= 줄>`(src 344에 해당, lab에서 `list`로 확인), `c`. 정지 시 `p/x ex`(a_magic=0x10b, a_text, a_data, a_bss, a_entry), `p/x current->ldt[1].a & 0xffff`(새 코드 리밋 = (a_text+4095)>>12), `p/x current->ldt[2].a & 0xffff`(0x4000 = 64MB/4KB), `p current->executable->i_num`(바뀜), `p current->pid`(그대로), `p/x eip[0]`(아직 셸 값) → `next` 2회 → `p/x eip[0]`(= a_entry), `p/x eip[3]`(64MB 바로 아래, 예 0x3ffffxx). | 시연 |
| 32 | 캡처 A-2: eip[0]/eip[3] 전후 | 전/후 캡처 2장. 상태도 ①의 "새 프레임 준비" 행 표시. `x/4wx eip[3] + current->start_code`로 [argc][argv][envp] 확인(선형 주소 보정) — 캡처 포함. | 캡처 |
| 33 | 시연 B: iret 뒤 첫 폴트 | `b do_no_page` 추가 후 `c`. 정지 시 `p/x address - current->start_code` → 기대: 341-343 꼬리 0 채움이 먼저면 `end_data` 페이지, 아니면 0(엔트리). `bt`. `finish` 후 `x/8xb current->start_code`에 새 프로그램 코드. 그 다음 `c` → 사용자 모드에서 첫 명령 실행 중 `Ctrl-C`, `p/x $eip`(작은 값), `p/x $cs`(0xf). | 시연 |
| 34 | 캡처 B: 같은 pid, 다른 코드 | A-1의 pid와 같은 pid에서 `x/8xb`가 다른 바이트(셸 vs ls)임을 나란히. 각주: 공유 중이면 share_page로 적재되어 디스크 읽기 없이 PTE 5일 수 있음(관찰과 추론 구분). | 캡처 |
| 35 | 시연 C(선택): #! 스크립트의 재시작 | 게스트에서 `echo '#!/bin/sh' > /tmp/t.sh; echo 'echo hi' >> /tmp/t.sh; chmod +x /tmp/t.sh`. `b exec.c:<S_ISREG 검사 줄>`(src 205). `/tmp/t.sh` 실행 → 같은 do_execve 호출 안에서 중단점 2회: 두 번째에 `p sh_bang`=1, `p argc`(+1 이상), `x/s`로 inode가 /bin/sh임을 확인(`p inode->i_num`). 실패 시 사전 캡처. | 시연 |
| 36 | 질문의 답 (1): PID가 그대로인 이유 | exec는 `task[nr]` 구조체를 만들지도 지우지도 않는다. 바뀌는 것은 그 구조체 안의 `executable`, `ldt` 리밋, `end_code/end_data/brk/start_stack`, `sigaction`, 일부 fd, 그리고 **커널 스택에 저장된 EIP/ESP**. pid·father·pwd·root·uid는 손대지 않음(318-346에 없음). | 정리 |
| 37 | 질문의 답 (2): 프로그램이 바뀌는 실제 순간 | `free_page_tables`로 구 페이지가 사라지고(07), `eip[0]=a_entry`로 복귀 지점이 바뀌고(iret), 첫 fetch의 #PF를 `do_no_page`가 새 inode에서 채운다(08). 세 회차가 한 줄로 이어지는 그림. 현대 커널: ELF 로더 + mmap이지만 "폴트로 적재"는 같다 한 줄. | 정리 |
| 38 | 오늘 코드가 쓰는 데이터 요약 | `struct exec ex`, `page[32]`, `p`, `eip[]`, `current->{executable, ldt, end_code, end_data, brk, start_stack, sigaction, close_on_exec, euid, egid}`. 함수×데이터 교차표. | 정리 |
| 39 | 이해 확인 질문 | 4문항 질문만. | 질문 |
| 40 | 이해 확인 정답 | 정답과 근거 줄 번호. | 질문 |
| 41 | 정리·다음 회차 예고 | fork(06)·주소(07)·COW(08)·exec(09) 묶음 완료. 10회차 "자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?" — 오늘 본 `do_exit`의 같은 두 줄(exit.c:106-107)과 `sigaction` 초기화가 왜 필요했는지로 연결. 미리 볼 파일: kernel/exit.c, kernel/signal.c. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
### A. do_execve에서 LDT 리밋·executable·eip/esp 변화 관찰 (pid 불변)
- 환경: `lab/` `make debug`, `gdb tools/system`, `target remote :1234`, `c`, 셸 프롬프트.
- 중단점: `b do_execve`; 이후 `list do_execve`로 lab 줄 번호를 확인해 `eip[0] = ex.a_entry` 줄(src exec.c:344 상당)에 `b exec.c:<줄>`.
- 절차·관찰·기대:
  1. 셸에 `ls` → `do_execve` 정지. `p current->pid` → N. `x/s (char*)current->start_code+(long)filename` → `"/bin/ls"`류. `p/x current->ldt[1].a & 0xffff` → 셸 텍스트 페이지 수. `p current->executable->i_num` → 셸 inode. `p/x eip[0]`, `p/x eip[3]` → 셸의 복귀 EIP·ESP.
  2. `c` → 344 상당 줄 정지. `p/x ex` → `a_magic = 0x10b`(0413), `a_entry = 0`(보통). `p/x current->ldt[1].a & 0xffff` → `(ex.a_text+4095)>>12`와 일치. `p/x current->ldt[2].a & 0xffff` → 0x4000. `p current->executable->i_num` → 새 inode. `p current->pid` → N (동일). `p/x get_base`에 해당하는 값: `p/x ((current->ldt[1].a>>16) | ((current->ldt[1].b&0xff)<<16) | (current->ldt[1].b&0xff000000))` → N번 슬롯 × 64MB, 1과 동일(베이스 불변).
  3. `next`×2 → `p/x eip[0]` = a_entry, `p/x eip[3]` = 0x3ffffxx 근처. `x/4wx (long)eip[3] + current->start_code` → `[argc][argv][envp]...`(argc=1 또는 인자 수+1).
- 대체 자료: 사전 캡처 3장(진입, 344 직전, next 후).

### B. iret 뒤 첫 do_no_page와 새 코드 확인
- 중단점: `b do_no_page`(A의 중단점은 유지해도 됨). `c`.
- 관찰: `p/x address - current->start_code`(0 또는 end_data 페이지), `p error_code`, `bt`(`do_no_page ← page_fault`; 341-343 쓰기라면 `put_fs_byte` 경로가 아니라 커널 쓰기이므로 U=0 에러 코드 — 비교 ①의 커널 부재 케이스를 실제로 봄). `finish` → `x/8xb current->start_code` → A-1 시점의 바이트와 다름.
- 기대 출력: 같은 pid, 다른 코드 바이트. 공유(share_page) 시 PTE 하위 5.
- 대체 자료: 사전 캡처 2장.

### C. (선택) #! 스크립트
- 게스트: `/tmp/t.sh` 생성(`#!/bin/sh`, `echo hi`), `chmod +x`.
- 중단점: `b exec.c:<S_ISREG 줄>`(src 205 상당). 스크립트 실행 → 2회 정지. 2회차에서 `p sh_bang`=1, `p argc`, `p inode->i_num`(= /bin/sh의 inode). `finish`가 아니라 `c`로 진행해 `hi` 출력 확인.
- 대체 자료: 사전 캡처 1장.

## 이해 확인 질문과 정답
1. **Q.** `do_execve`의 첫 인자 `eip`는 무엇을 가리키며, `eip[3]`은 무엇인가?  
   **A.** `_sys_execve`가 `lea EIP(%esp)`로 넘긴 커널 스택의 저장된 EIP 위치(system_call.s:201-202). 프레임 오프셋(35-46)상 `eip[1]`=CS, `eip[2]`=EFLAGS, `eip[3]`=OLDESP(사용자 ESP). 344-345가 이 둘을 덮어쓴다.
2. **Q.** exec 뒤에도 LDT **베이스**가 그대로인 이유는? 바뀌는 것은 무엇인가?  
   **A.** 베이스(nr×64MB)는 태스크 슬롯이 정하며 fork.c:52-55에서 고정. `change_ldt`(exec.c:162-167)는 같은 베이스를 다시 쓰고 리밋만 바꾼다(코드: 텍스트 페이지 올림, 데이터: 64MB).
3. **Q.** exec가 성공했는데도 `/bin/ls`의 코드가 아직 메모리에 없다. 언제, 누가 읽는가?  
   **A.** `do_execve`는 헤더 1블록만 `bread`(221-225)한다. iret 뒤 첫 명령 fetch(또는 341-343의 꼬리 0 채움 쓰기)가 부재 폴트를 내고 `do_no_page`(memory.c:365-397)가 `executable` inode에서 블록 4개를 읽는다.
4. **Q.** 실행 권한이 없는 파일을 exec하면 0.11은 어떤 errno를 돌려주는가? 파일이 디렉터리라면?  
   **A.** 실행 비트 없음 → ENOEXEC(exec.c:216-219, EACCES가 아님). 정규 파일이 아니면(디렉터리) → EACCES(205-207). 둘 다 318 이전이라 구 프로그램으로 돌아가고 라이브러리가 errno를 설정한다.

## 처음 등장하는 용어
- `execve`, `_syscall3`, `sys_execve`, `do_execve`
- a.out, `struct exec`, OMAGIC/NMAGIC/ZMAGIC, `N_TXTOFF`, `SEGMENT_SIZE`
- `#!`(shebang), 인터프리터, `restart_interp`
- `copy_strings`, `from_kmem`, `MAX_ARG_PAGES`, `change_ldt`, `create_tables`
- 돌이킬 수 없는 지점(point of no return), `close_on_exec`, setuid/setgid(`S_ISUID/S_ISGID`)
- `end_code`, `end_data`, `brk`, `start_stack`

## 주의: 흔한 오해 / 말하지 말아야 할 것
- "exec가 새 프로세스를 만든다"고 말하지 않는다. `task[nr]`·pid는 그대로이며 내용물만 교체된다.
- "exec가 프로그램을 메모리에 읽어 들인다"고 말하지 않는다. 0.11의 exec는 헤더 1KB만 읽고, 코드·데이터는 폴트가 날 때 `do_no_page`가 읽는다.
- "exec가 LDT를 새로 만든다"고 말하지 않는다. 베이스는 그대로, 리밋만 바뀐다.
- 실행 권한 없음의 errno를 EACCES라고 말하지 않는다. 0.11은 ENOEXEC를 돌려준다(216-219). 현대 리눅스(EACCES)와 다르다.
- E2BIG를 0.11 exec의 오류로 소개하지 않는다. `errno.h:26`에 정의만 있다. 128행 `p-len<0`은 `p`가 unsigned라 실질적으로 걸리지 않으며 인자 초과는 페이지 할당 실패 → ENOMEM으로 나타난다(코드 추론, 실험 아님).
- `#!` 처리를 "재귀적으로 인터프리터를 찾는다"고 하지 않는다. `sh_bang` 때문에 한 번만 처리한다(226, 261).
- "ELF"를 0.11 맥락에서 쓰지 않는다. 비교 ① 말미의 한 줄 대비만.
- 시연 캡처의 inode 번호·주소·리밋 값은 lab 디스크 이미지에 따라 다르다. 각주에 환경과 수정 여부를 적는다. lab 줄 번호는 src와 다를 수 있으므로 슬라이드의 줄 번호는 src 기준임을 명시한다.

---

# 10. 종료·대기·시그널

## 핵심 질문
자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?

## 학습 목표 (3~5개)
1. `_exit()`가 `do_exit()`에 도착해 자원을 반납하고 `TASK_ZOMBIE`로 남는 이유와, 누가 그 껍데기를 치우는지(`sys_waitpid` → `release`) 말할 수 있다.
2. 0.11의 시그널이 `task_struct.signal` 32비트 비트맵 한 개이며, 전달은 "보내는 쪽이 비트를 켜고, 받는 쪽이 커널에서 사용자로 돌아가는 순간(`ret_from_sys_call`)에만 검사한다"는 두 단계로 되어 있음을 설명할 수 있다.
3. `do_signal()`이 사용자 스택에 핸들러 프레임을 어떻게 쌓는지(복귀 주소 = `sa_restorer`, 인자 = signr, 저장 레지스터) 그림으로 그릴 수 있다.
4. `waitpid` 옵션(`WNOHANG`, `WUNTRACED`)과 시그널 처리 선택지(`SIG_DFL`/`SIG_IGN`/핸들러)를 각각 범위 안에서 빠짐없이 비교하고, `SIGKILL`이 왜 등록조차 거부되는지 소스로 보일 수 있다.
5. Ctrl-C가 tty 큐 → `tty_intr` → 프로세스 그룹 전체의 `signal` 비트 → 다음 커널 복귀 시 `do_signal` → 기본 동작 `do_exit`까지 가는 경로를 추적할 수 있다(tty 내부는 13회차).

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준)
| 파일 | 줄 | 내용 |
|---|---|---|
| `kernel/exit.c` | 19–33 | `release()` — task[] 슬롯 비우고 `free_page`, `schedule()` |
| `kernel/exit.c` | 35–44 | `send_sig()` — 권한 검사 후 `p->signal \|= 1<<(sig-1)` |
| `kernel/exit.c` | 46–54 | `kill_session()` — 같은 session 전체에 SIGHUP |
| `kernel/exit.c` | 60–81 | `sys_kill()` — pid 0 / >0 / -1 / <-1 네 갈래 |
| `kernel/exit.c` | 83–100 | `tell_father()` — 부모의 SIGCHLD 비트, 못 찾으면 `release(current)` |
| `kernel/exit.c` | 102–135 | `do_exit()` — 페이지 테이블·fd·inode 반납, 고아 입양, ZOMBIE, `tell_father`, `schedule()` |
| `kernel/exit.c` | 137–140 | `sys_exit()` — `(error_code&0xff)<<8` |
| `kernel/exit.c` | 142–195 | `sys_waitpid()` — 자식 탐색, STOPPED/ZOMBIE/기타 분기, 대기와 재시도 |
| `kernel/signal.c` | 15–26 | `sys_sgetmask`/`sys_ssetmask` — SIGKILL은 blocked에 못 넣음 |
| `kernel/signal.c` | 48–61 | `sys_signal()` — ONESHOT\|NOMASK로 등록, 이전 핸들러 반환 |
| `kernel/signal.c` | 63–80 | `sys_sigaction()` — 사용자 구조체 복사, sa_mask 조정 |
| `kernel/signal.c` | 82–119 | `do_signal()` — 처분 결정, 사용자 스택 프레임 구성 |
| `include/signal.h` | 12–34 | 시그널 번호 1~22 |
| `include/signal.h` | 37–39, 45–46, 48–53 | `SA_*`, `SIG_DFL`/`SIG_IGN`, `struct sigaction` |
| `kernel/system_call.s` | 17–31, 48–59 | 스택 배치 주석, task_struct/sigaction 오프셋 상수 |
| `kernel/system_call.s` | 101–128 | `ret_from_sys_call` — 시그널 검사와 `do_signal` 호출 |
| `kernel/system_call.s` | 176–197 | `timer_interrupt` — 틱 후에도 `ret_from_sys_call`로 합류 |
| `kernel/sched.c` | 24 | `_BLOCKABLE` — SIGKILL·SIGSTOP 제외 |
| `kernel/sched.c` | 104–119 | `schedule()` 앞부분 — alarm 및 "시그널 받은 INTERRUPTIBLE → RUNNING" |
| `kernel/sched.c` | 144–148 | `sys_pause()` |
| `kernel/sched.c` | 338–346 | `sys_alarm()` |
| `include/linux/sched.h` | 19–23, 83–89 | 태스크 상태 5종, `signal`/`sigaction[32]`/`blocked`/`exit_code`/`father`/`pgrp`/`session`/`leader` |
| `kernel/fork.c` | 86 | 자식 `p->signal = 0` (pending은 상속 안 됨) |
| `fs/exec.c` | 322–323 | exec 시 32개 핸들러 모두 NULL (SIG_DFL)로 초기화 |
| `kernel/chr_drv/tty_io.c` | 19–20, 111–120, 200–208 | `INTMASK`, `tty_intr()`, `copy_to_cooked`의 ISIG 분기 (참조만) |
| `init/main.c` | 179–187 | init의 fork → `wait(&i)` 루프 |
| `include/sys/wait.h` | 10–18 | `WNOHANG`/`WUNTRACED`, `WEXITSTATUS` 등 매크로 |
| `lib/wait.c` | 11–16 | `wait()` = `waitpid(-1, ..., 0)` |
| `lib/_exit.c` | 10–13 | `_exit()` = `int $0x80` with `__NR_exit` |
| `mm/memory.c` | 33–37 | `oom()` → `do_exit(SIGSEGV)` (커널이 직접 종료시키는 예) |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 (프로세스 생애 후반)**: `TASK_RUNNING` → (`_exit`/치명 시그널 기본 처리/`oom`) → `do_exit` 진행 중(아직 RUNNING, 자원 반납) → `TASK_ZOMBIE` (`state=3`, `exit_code` 보존, task[] 슬롯·`task_struct` 페이지 유지) → 부모의 `sys_waitpid`가 `release` → 슬롯 NULL, 페이지 해제(존재 안 함). 부모가 먼저 죽으면 `father=1`로 재지정 후 init이 거둠. 부수 상태: 부모 `TASK_INTERRUPTIBLE` (waitpid 중) → SIGCHLD 비트로 `schedule()`이 RUNNING 복귀.
- **상태 변화도 (시그널 1개의 생애)**: 없음 → `signal` 비트 켜짐(pending) → `blocked`에 가려짐/안 가려짐 → `ret_from_sys_call`에서 비트 내려감 → `do_signal`에서 처분 결정 → (핸들러면) 사용자 스택 프레임 → 핸들러 실행 → `sa_restorer` → 원래 EIP.
- **모드·선택지 비교 1 (범위: `sys_waitpid`의 `options` 비트 전부)**: `0`, `WNOHANG`, `WUNTRACED`. 0.11 헤더에 정의된 옵션은 이 둘뿐이다.
- **모드·선택지 비교 2 (범위: 한 시그널의 처분 `sa_handler` 값 전부)**: `SIG_DFL`(0), `SIG_IGN`(1), 사용자 함수 주소. 각각에서 SIGCHLD만 예외.
- **모드·선택지 비교 3 (범위: `sys_kill`의 `pid` 인자 4갈래)**: `0`, `>0`, `-1`, `<-1`.
- 혼합 금지: 태스크 상태(RUNNING/ZOMBIE)와 시그널 처분(DFL/IGN/handler)은 별도 슬라이드에 둔다.

## 120분 운영안
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–02 | 4 | 핵심 질문과 지도 |
| 03–07 | 14 | 배경: exit/wait/signal이 없던 시절의 문제, task_struct의 관련 필드, 9회차와의 연결 |
| 08–14 | 22 | `do_exit` 코드 읽기와 ZOMBIE 상태 변화도, `sys_waitpid` 코드와 옵션 비교 |
| 15–16 | 8 | 시연 A (do_exit → ZOMBIE → 부모 깨어남) |
| 17–26 | 24 | 시그널: 비트맵, 보내는 쪽(`send_sig`/`sys_kill`), 받는 쪽(`ret_from_sys_call`/`do_signal`), 프레임 구성, 처분 비교 |
| 27–30 | 10 | SIGKILL 특례, 마스크, exec/fork와 시그널, Ctrl-C 경로(참조) |
| 31–34 | 14 | 시연 B (kill + 핸들러 프레임), 시연 C (Ctrl-C, 사전 캡처 가능) |
| 35–38 | 12 | 질문의 답, 현대 커널 비교, 흔한 오해 |
| 39–40 | 6 | 이해 확인과 정리 |
| 예비 | 6 | 질의응답 |

## 슬라이드 계획
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 10. 종료·대기·시그널 | 제목과 핵심 질문 두 개. "자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?" 아래에 오늘 추적할 세 단어 `_exit`, `wait`, `signal`을 배치. | 제목 |
| 02 | 15회차 지도 — 10회차 위치 | 15회차 표. 06 fork → 09 exec → **10 exit/wait/signal**로 "프로세스 생애" 축이 완성됨을 강조. 11~13은 I/O 축. | 지도 |
| 03 | 9회차 복습: 셸이 명령을 실행하는 3단계 | fork → exec → ? 의 빈칸. 셸은 자식이 끝날 때까지 프롬프트를 내지 않는다. 그 "끝남"을 커널이 어떻게 알려주는지가 오늘 주제. | 배경 |
| 04 | 왜 종료는 두 단계인가 | 프로세스가 스스로 자기 `task_struct` 페이지를 해제하면서 그 위의 커널 스택에서 실행 중일 수 없다. 그래서 "자원 반납(스스로)"과 "껍데기 수거(남이)"를 분리. 좀비라는 이름의 뜻. | 배경 |
| 05 | task_struct에서 오늘 쓰는 필드 | `include/linux/sched.h:19–23` 상태 5종, `83–89`의 `signal`, `sigaction[32]`, `blocked`, `exit_code`, `pid/father/pgrp/session/leader`. 그림: 한 태스크 구조체에서 오늘 필드만 색칠. | 코드 |
| 06 | 시스템 콜 번호와 라이브러리 경로 | `lib/_exit.c:10–13` (`int $0x80`, `__NR_exit`=1), `lib/wait.c:11–16` (`wait`는 `waitpid(-1,…,0)`), `include/linux/sys.h:74–75`의 `sys_exit`, `sys_waitpid` 위치. 4회차 시스템 콜 진입과 연결. | 코드 |
| 07 | 호출 순서도: _exit에서 schedule까지 | `sys_exit` → `do_exit` → `free_page_tables` ×2 → 고아 처리 → `sys_close` ×NR_OPEN → `iput` ×3 → tty/수학 → `kill_session` → state/exit_code → `tell_father` → `schedule`. 상태 변화도와 구분해 "호출 순서"라고 명시. | 배경 |
| 08 | 코드: do_exit 전반부 (자원 반납) | `kernel/exit.c:102–123`. `free_page_tables(get_base(current->ldt[1]), get_limit(0x0f))` 두 줄은 7회차 LDT, `sys_close` 루프는 fd 테이블, `iput(pwd/root/executable)`은 12회차 예고. | 코드 |
| 09 | 코드: do_exit 후반부 (고아, 좀비, 통지) | `kernel/exit.c:108–114` 자식의 `father=1` 재지정과 이미 ZOMBIE인 자식에 대한 `send_sig(SIGCHLD, task[1], 1)`; `130–134` `state=TASK_ZOMBIE`, `exit_code=code`, `tell_father`, `schedule()`. `return (-1)` 주석은 도달 불가 설명. | 코드 |
| 10 | 코드: tell_father와 release | `exit.c:83–100` 부모 pid 탐색 후 `signal \|= 1<<(SIGCHLD-1)`, 못 찾으면 `printk("BAD BAD…")` 후 `release(current)`. `exit.c:19–33` `release`: `task[i]=NULL; free_page((long)p); schedule()`. "release는 항상 남이 호출한다"는 원칙과 유일한 예외. | 코드 |
| 11 | 상태 변화도: RUNNING → ZOMBIE → 소멸 | 상태: RUNNING / (do_exit 진행 중: 여전히 RUNNING) / ZOMBIE / 소멸. 전환 원인: `_exit`·치명 시그널 DFL·`oom`(`mm/memory.c:33–37`) / `exit.c:130` / 부모의 `sys_waitpid`→`release`. 변경 데이터: 페이지 테이블·fd·inode 반납, `state`, `exit_code`, `task[i]`, task_struct 페이지. 유지 조건: 부모가 wait 안 하면 ZOMBIE 영구; 부모 먼저 죽으면 `father=1`. | 상태도 |
| 12 | 코드: sys_waitpid 탐색 조건 | `exit.c:142–164`. `&LAST_TASK`에서 역순으로 `father==current->pid` 자식만 보고, `pid>0`/`pid==0`(같은 pgrp)/`pid<-1`(pgrp==-pid)/`pid==-1`(전부) 필터. `verify_area(stat_addr,4)`는 8회차 COW와 연결. | 코드 |
| 13 | 코드: sys_waitpid 상태별 분기와 대기 | `exit.c:165–194`. `TASK_STOPPED`(WUNTRACED 아니면 continue, 0x7f 기록), `TASK_ZOMBIE`(cutime/cstime 합산, `release`, `put_fs_long(code)`), default(`flag=1`). 이후 `flag`면 WNOHANG 검사 → `TASK_INTERRUPTIBLE`로 `schedule()` → 깨어나 SIGCHLD 비트를 지우며 다른 시그널 없으면 `goto repeat`, 있으면 `-EINTR`; 자식 없으면 `-ECHILD`. | 코드 |
| 14 | 비교: waitpid options (범위: 0.11이 정의한 옵션 전부) | 표. `0`: 자식 ZOMBIE까지 잠듦(`exit.c:187–188`). `WNOHANG`(`wait.h:10`): 살아있는 자식만 있으면 즉시 0 반환(`exit.c:185–186`). `WUNTRACED`(`wait.h:11`): STOPPED 자식도 보고, `0x7f` 기록(`exit.c:166–170`) — 단 0.11에는 SIGSTOP 처분에서 `TASK_STOPPED`로 만드는 코드가 없어 헤더 주석 "not supported"(`wait.h:9`)가 맞음을 명시. 반환값 해석은 `WEXITSTATUS`(`wait.h:15`)와 `sys_exit`의 `<<8`(`exit.c:139`). | 비교 |
| 15 | 시연 A 계획: 자식 종료와 부모 깨어남 | 중단점 `do_exit`, `tell_father`, `sys_waitpid`. 관찰: `current->pid`, `current->father`, `current->state`가 0→3으로, 부모 task의 `state` 1→0, `signal`에 SIGCHLD 비트. 명령 목록과 기대 출력. | 시연 |
| 16 | 시연 A 캡처 | GDB 로그: `p current->state` = 3 (`TASK_ZOMBIE`), `p/x task[N]->signal` = 0x10000, 이어 `sys_waitpid` 안에서 `release` 직전 `p (*p)->exit_code`. 각주: lab/ QEMU i386 + GDB, 원본 수정 없음, 셸에서 `ls`를 실행해 유발. | 캡처 |
| 17 | 시그널이란 무엇인가 (0.11 기준) | 32비트 정수 하나(`sched.h:83`)에 번호-1 비트. 큐 없음, 같은 시그널 두 번은 한 번. 번호표 `include/signal.h:12–34` (1 SIGHUP … 22 SIGTTOU). "메시지가 아니라 플래그"라는 한 문장. | 배경 |
| 18 | 보내는 쪽: send_sig와 sys_kill | `exit.c:35–44` `send_sig`: `priv \|\| euid 일치 \|\| suser()`면 `p->signal \|= 1<<(sig-1)`. `exit.c:60–81` `sys_kill`의 네 갈래. 보내는 쪽은 상대를 깨우지 않는다 — 깨우는 것은 `schedule()`(`sched.c:117–119`). | 코드 |
| 19 | 비교: sys_kill pid 인자 (범위: 4갈래 전부) | 표. `pid==0`: 내 pgrp 전체(priv=1, `exit.c:65–68`); `pid>0`: 그 pid(`69–72`); `pid==-1`: 모든 태스크(`73–75`); `pid<-1`: pgrp==-pid(`76–79`). 각 갈래의 권한 인자(priv 0/1)와 반환값 누적 방식. | 비교 |
| 20 | 받는 쪽은 언제 검사하는가 | `system_call.s:12–15` 주석: 타이머 인터럽트 후와 시스템 콜 후에만. `system_call.s:101–108`: task[0] 제외, `CS==0x0f`·`OLDSS==0x17` 즉 사용자 모드로 돌아갈 때만. 커널 모드에서 깨어난 시점은 검사 안 함 → "Ctrl-C가 즉시가 아닌 이유". `timer_interrupt`(`176–197`)도 같은 라벨로 합류. | 코드 |
| 21 | 코드: ret_from_sys_call 시그널 선택 | `system_call.s:109–120`: `signal & ~blocked` → `bsfl`로 최하위 비트(가장 작은 번호 우선) → `btrl`로 비트 내림 → `incl`로 번호 → `pushl %ecx; call _do_signal`. 한 번에 한 개만 처리, 나머지는 다음 복귀 때. | 코드 |
| 22 | 코드: do_signal 처분 결정 | `signal.c:82–103`. `sa_handler==1`(SIG_IGN) → return; `==0`(SIG_DFL) → SIGCHLD면 return, 아니면 `do_exit(1<<(signr-1))`; `SA_ONESHOT`이면 핸들러를 NULL로(한 번 쓰고 기본으로). `do_exit` 인자가 `1<<(signr-1)`이라 종료 코드 하위 바이트에 시그널이 남는 방식의 특이점 명시. | 코드 |
| 23 | 비교: 시그널 처분 (범위: sa_handler 값 전부) | 표. `SIG_DFL`(0, `signal.h:45`): 프로세스 종료(SIGCHLD 제외) — "정지/코어/무시" 세분화 없음. `SIG_IGN`(1, `signal.h:46`): 비트는 지워지고 아무 일 없음. 핸들러 주소: 사용자 스택 프레임 구성 후 사용자 모드에서 실행. 각 행에 전환 조건(`sys_signal`/`sys_sigaction`/exec 시 리셋 `fs/exec.c:322–323`)과 소스. | 비교 |
| 24 | 코드: do_signal 프레임 구성 | `signal.c:104–118`. `*(&eip)=sa_handler`로 iret가 핸들러로 가게 하고, `*(&esp) -= longs`(7 또는 8), `put_fs_long`으로 `sa_restorer, signr, [blocked], eax, ecx, edx, eflags, old_eip` 순서로 사용자 스택에 기록. `current->blocked \|= sa->sa_mask`. 인자가 C 매개변수이면서 스택의 복사본이라 `*(&eip)`로 쓰는 이유 설명(`system_call.s:17–31` 배치와 1:1). | 코드 |
| 25 | 그림: 핸들러 호출 전후 사용자 스택 | 왼쪽: 시스템 콜 직전 사용자 스택. 오른쪽: `do_signal` 후 — `[esp] = sa_restorer`(핸들러가 ret하면 여기로), `[esp+4]=signr`(핸들러의 첫 인자), 그 위에 old eax/ecx/edx/eflags/old_eip. `iret` → 핸들러 → `ret` → restorer(사용자 라이브러리 코드)가 레지스터 복원 후 old_eip로. 커널이 "두 번째 복귀"를 사용자 코드에 맡기는 구조. | 상태도 |
| 26 | 상태 변화도: 시그널 한 개의 생애 | 상태: 없음 / pending(비트 1) / blocked에 가려짐 / 처리 중(비트 0, do_signal) / 핸들러 실행 중(사용자) / 복귀. 전환 원인: `send_sig`·`tell_father`·`tty_intr`·alarm(`sched.c:113–115`) / `ret_from_sys_call:115` / 처분값. 변경 데이터: `signal`, `blocked`, 사용자 ESP·EIP, `sa_handler`(ONESHOT). 유지 조건: 커널 모드에 머무는 동안은 pending 유지. | 상태도 |
| 27 | SIGKILL은 왜 못 잡는가 | `signal.c:52–53`, `signal.c:68–69`: `signum==SIGKILL`이면 `sys_signal`/`sys_sigaction` 모두 `-1`. `signal.c:24`: `ssetmask`가 SIGKILL 비트를 깎음. `sched.c:24` `_BLOCKABLE`은 SIGKILL·SIGSTOP 제외 — 단 SIGSTOP은 등록은 거부되지 않음(0.11의 비대칭). 결론: SIGKILL은 항상 `SIG_DFL` → `do_exit`. | 코드 |
| 28 | sys_signal vs sys_sigaction | `signal.c:48–61`: `signal()`은 `SA_ONESHOT\|SA_NOMASK` 고정, restorer를 세 번째 인자로 받음. `signal.c:63–80`: `sigaction()`은 구조체 통째 복사, `SA_NOMASK` 아니면 자기 번호를 `sa_mask`에 추가. 둘 다 같은 `current->sigaction[]`에 쓴다. | 코드 |
| 29 | fork·exec·wait와 시그널 상태 | `fork.c:86` 자식 `signal=0`(pending 미상속, `sigaction[]`은 `*p = *current`로 상속). `exec.c:322–323` 핸들러 전부 NULL. `exit.c:189–192` waitpid가 깨어난 뒤 SIGCHLD만 지우고 다른 시그널이 있으면 `-EINTR`. `sched.c:144–148` `pause()`도 같은 방식으로 깨어남. | 코드 |
| 30 | Ctrl-C 경로 (참조: 13회차에서 상세) | 키보드 IRQ → `tty_io.c:200–203` `copy_to_cooked`가 `INTR_CHAR`를 만나면 `tty_intr(tty, INTMASK)` → `tty_io.c:111–120` `pgrp==tty->pgrp`인 모든 태스크에 비트 OR. 이후는 슬라이드 20–22와 동일. "어디까지 가는가"의 답: 비트 하나까지; 실제 죽는 건 그 프로세스가 다음에 사용자 모드로 돌아가는 순간. | 코드 |
| 31 | 시연 B 계획: kill과 핸들러 프레임 | 셸에서 `kill -2 <pid>`(또는 lab 테스트 프로그램이 `signal(SIGINT, h)` 등록 후 `pause()`). 중단점 `sys_kill`, `do_signal`. 관찰: 대상 `signal` 비트, `do_signal` 진입 시 `signr`, 리턴 직전 `esp`와 `x/8wx esp`(사용자 스택 프레임), `eip`가 핸들러 주소로 바뀜. | 시연 |
| 32 | 시연 B 캡처 | GDB 로그: `b do_signal` → `p signr`=2, `p/x sa_handler`, `finish` 직전 `x/8wx esp`에 restorer/2/eax/ecx/edx/eflags/old_eip. 각주: lab/의 테스트 프로그램은 수업용 추가 바이너리(원본 소스 미수정), 핸들러 없는 기본 경로는 `ls`에 `kill -9`로 대체. | 캡처 |
| 33 | 시연 C 계획: Ctrl-C | 셸에서 `sleep 100`(또는 무한 루프 프로그램) 후 Ctrl-C. 중단점 `tty_intr` 조건부(`mask==2`), `do_signal`. 관찰: `tty->pgrp`, 대상 태스크 `signal` 비트, `do_signal`에서 `sa_handler==0` → `do_exit`. 실패 시 대체: 사전 캡처(QEMU 콘솔 입력이 GDB 중단과 겹치면 키 입력이 늦게 전달될 수 있음). | 시연 |
| 34 | 시연 C 캡처 | 터미널 캡처: Ctrl-C 후 `tty_intr` 중단, `p tty->pgrp`, `p/x task[N]->signal`=0x2, 이어 `do_signal` 중단에서 `signr`=2, 한 단계 뒤 `do_exit` 진입. 각주: 원본 미수정, 캡처 시 QEMU `-serial`/콘솔 설정. | 캡처 |
| 35 | 질문의 답 1: 자식이 죽으면 부모는 어떻게 아는가 | 세 줄 요약: (1) 자식은 `do_exit`에서 자원만 반납하고 ZOMBIE로 남는다(`exit.c:130–132`). (2) `tell_father`가 부모 `signal`의 SIGCHLD 비트를 켠다. (3) 부모는 `sys_waitpid`에서 자고 있다가 `schedule()`의 시그널 검사로 깨어나(`sched.c:117–119`) ZOMBIE 자식을 `release`하고 `exit_code`를 받는다. | 정리 |
| 36 | 질문의 답 2: Ctrl-C는 어디까지 가는가 | 키 → tty 큐 → `tty_intr`가 프로세스 그룹의 비트를 켬 → 그 프로세스가 다음 시스템 콜/타이머 복귀 때 `ret_from_sys_call`이 발견 → `do_signal` → 핸들러가 없으면 `do_exit`. 커널 모드에서 잠든 프로세스(`TASK_UNINTERRUPTIBLE`)는 깨우지 못한다는 한계 명시. | 정리 |
| 37 | 현대 커널과의 차이 (짧게) | 비트맵 32개 → `sigpending` 큐와 실시간 시그널; `sa_restorer` 사용자 코드 → 커널 제공 trampoline/`sigreturn`; `TASK_ZOMBIE`는 이름만 `EXIT_ZOMBIE`로; `wait4`/`waitid`; SIGSTOP/SIGCONT 실제 정지. 14회차에서 다시 비교. | 배경 |
| 38 | 흔한 오해 | (1) "kill은 프로세스를 즉시 죽인다" — 비트만 켠다. (2) "좀비는 버그" — 설계다. (3) "SIG_IGN은 시그널을 막는다" — 비트는 켜졌다가 do_signal에서 버려진다. (4) "핸들러는 커널이 호출한다" — iret로 사용자 모드에서 시작하고 복귀는 사용자 restorer가 한다. | 배경 |
| 39 | 이해 확인 (정답 포함) | 아래 "이해 확인 질문과 정답" 4문항. 먼저 질문만 띄우고 클릭으로 정답 노출. | 질문 |
| 40 | 정리와 다음 회차 | 오늘 세 함수(`do_exit`, `sys_waitpid`, `do_signal`)의 역할 한 줄씩. 다음 11회차: "read()가 디스크에 실제로 접근하는 때는 언제인가?" — 오늘 `do_exit`가 호출한 `iput`과 `sys_close` 뒤에 있는 버퍼 캐시로 이동. | 정리 |

## 강사 시연
**A. 자식 종료 → ZOMBIE → 부모 깨어남**
- 환경: `lab/` QEMU i386 + GDB (`target remote`, 커널 심볼 로드). 원본 소스 미수정.
- 명령: `b do_exit`, `b tell_father`, `b sys_waitpid`, `c`. 게스트 셸에서 `ls`.
- 관찰: `do_exit` 진입 시 `p current->pid`, `p current->father`, `p current->state`(0). `tell_father` 진입 시 `p pid`(부모 pid), `finish` 후 `p/x task[<부모 인덱스>]->signal` (0x10000 = 1<<16). `do_exit:130` 지나 `p current->state` = 3. `sys_waitpid`에서 `p (*p)->state`=3, `p (*p)->exit_code`, `release` 직후 `p task[<자식 인덱스>]`= 0x0.
- 기대 출력: `$1 = 3`, `$2 = 0x10000`, 부모 `state` 1 → 0.
- 대체: `plan/`에 둘 사전 캡처 로그(슬라이드 16).

**B. kill → do_signal → 사용자 스택 프레임**
- 명령: 게스트에서 테스트 프로그램(`signal(SIGINT, handler); pause();`)을 백그라운드 실행, `kill -2 <pid>`. GDB: `b sys_kill`, `b do_signal`.
- 관찰: `sys_kill`에서 `p pid`, `p sig`; `finish` 후 대상 `p/x task[N]->signal`=0x2. `do_signal` 진입 `p signr`=2, `p/x sa->sa_handler`; `signal.c:118` 직전에서 `p/x esp`, `x/8wx esp` → `[sa_restorer, 2, blocked, eax, ecx, edx, eflags, old_eip]`(SA_NOMASK면 7개). `finish` 후 `info registers eip`는 핸들러 주소.
- 대체: 핸들러 없는 경로는 `ls`에 `kill -9` → `do_signal`에서 `sa_handler==0` → `do_exit` 진입을 보여줌. 테스트 프로그램 빌드 실패 시 사전 캡처.

**C. Ctrl-C (참조 수준)**
- 명령: 게스트에서 오래 도는 명령 실행 후 Ctrl-C. GDB: `b tty_intr if mask==2`, `b do_signal`.
- 관찰: `p tty->pgrp`, 대상 태스크 `signal` 비트, `do_signal`의 `signr`=2, 이어 `do_exit`.
- 대체: QEMU 콘솔 입력과 GDB 중단이 겹쳐 지연될 수 있으므로 사전 캡처를 기본으로 하고 시간 남을 때만 라이브.

## 이해 확인 질문과 정답
1. **Q.** `do_exit()`는 왜 자기 `task_struct` 페이지를 `free_page`하지 않는가?
   **A.** 그 페이지 위의 커널 스택에서 지금 실행 중이기 때문. 해제는 다른 태스크가 `sys_waitpid` → `release()`(`exit.c:19–33`)로 한다. 부모를 못 찾는 예외(`exit.c:98–99`)만 자신이 `release(current)`.
2. **Q.** `kill(pid, SIGINT)`가 반환된 직후, 대상 프로세스는 이미 핸들러를 실행했는가?
   **A.** 아니다. `send_sig`는 `p->signal` 비트만 켠다(`exit.c:40`). 대상이 다음에 시스템 콜/타이머에서 사용자 모드로 복귀할 때 `ret_from_sys_call`(`system_call.s:109–119`)이 검사한다.
3. **Q.** `signal(SIGKILL, h)`의 반환값과 이유는?
   **A.** `-1`. `sys_signal`이 `signum==SIGKILL`을 거부한다(`signal.c:52–53`). `sigaction`도 같다(`signal.c:68–69`). 또한 `ssetmask`는 SIGKILL 비트를 깎는다(`signal.c:24`).
4. **Q.** `waitpid(-1, &st, WNOHANG)`이 0을 반환했다. 자식 상태는?
   **A.** 살아 있는(ZOMBIE가 아닌) 자식이 최소 하나 있고 거둘 ZOMBIE는 없다. `flag=1`이고 `options & WNOHANG`이면 즉시 0(`exit.c:179–186`). 자식이 아예 없으면 `-ECHILD`(`exit.c:194`).

## 처음 등장하는 용어
- **좀비(ZOMBIE, `TASK_ZOMBIE`=3)**: 자원은 반납했지만 `task[]` 슬롯과 `exit_code`를 가진 채 부모의 wait를 기다리는 상태.
- **고아 입양(`father=1`)**: 부모가 먼저 종료하면 자식의 부모를 init(task[1])으로 바꾸는 것(`exit.c:108–114`).
- **pending 시그널**: `task_struct.signal`에 켜진 비트. 아직 처리 전.
- **blocked / 시그널 마스크**: `task_struct.blocked`; 켜진 비트의 시그널은 `ret_from_sys_call`이 건너뛴다.
- **처분(disposition)**: `sa_handler` 값에 따른 `SIG_DFL`/`SIG_IGN`/핸들러.
- **`sa_restorer`**: 핸들러가 `ret`했을 때 돌아갈 사용자 코드. 레지스터 복원과 원래 EIP 복귀를 맡는다.
- **프로세스 그룹(`pgrp`)·세션(`session`)·리더(`leader`)**: tty 시그널 배달 단위와 SIGHUP 전파 단위.
- **`SA_ONESHOT` / `SA_NOMASK`**: 한 번 쓰면 기본으로 되돌림 / 핸들러 실행 중 마스크를 저장·적용하지 않음.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- `tell_father`는 부모를 **깨우지 않는다**. 깨우는 코드는 `schedule()` 앞부분(`sched.c:117–119`)이다. "SIGCHLD가 부모를 깨운다"고 말할 때 이 두 단계를 분리해 말한다.
- 0.11의 `SIG_DFL`은 "종료" 하나뿐이다. 현대의 Term/Core/Stop/Ign 분류를 0.11에 투영하지 않는다. `TASK_STOPPED`로 보내는 코드는 0.11에 없다(`wait.h:9` 주석 "WUNTRACED not supported").
- `kill_pg`라는 함수는 0.11에 없다. tty 쪽 함수는 `tty_intr`(`tty_io.c:111`)이다.
- `do_signal`에서 `do_exit(1<<(signr-1))`의 인자는 "시그널 번호"가 아니라 비트 값이다. 종료 코드 해석을 현대 `WTERMSIG`와 같다고 단정하지 않는다.
- 시그널은 커널 모드 코드 실행 중에는 검사되지 않으므로, `TASK_UNINTERRUPTIBLE`로 자는 프로세스는 Ctrl-C로 못 깨운다. "Ctrl-C는 항상 통한다"고 말하지 않는다.
- 시연 B의 테스트 프로그램은 lab/에 추가한 사용자 바이너리이며 커널 원본 수정이 아님을 캡처 각주에 쓴다. 상태 변화도의 수치(비트값)는 코드 추론이고 GDB 캡처는 실제 관찰임을 구분한다.

---

# 11. 버퍼 캐시와 블록 장치

## 핵심 질문
read()가 디스크에 실제로 접근하는 때는 언제인가?

## 학습 목표 (3~5개)
1. 파일 시스템이 디스크를 직접 읽지 않고 항상 `bread()` → `getblk()`를 거쳐 **버퍼 캐시**를 통과하며, 실제 디스크 접근은 `b_uptodate==0`일 때만 `ll_rw_block()`으로 일어남을 코드로 보일 수 있다.
2. `struct buffer_head`의 네 플래그 `b_uptodate`/`b_dirt`/`b_lock`/`b_count`가 각각 누구에 의해 언제 바뀌는지 상태 변화도로 설명할 수 있다.
3. 요청(`struct request`)이 `make_request` → `add_request`에서 어떻게 큐에 들어가고(`IN_ORDER` 엘리베이터), `do_hd_request`가 어떻게 컨트롤러에 명령을 내리며, `hd_interrupt` → `read_intr`가 어떻게 데이터를 옮기고 `end_request`로 버퍼를 깨우는지 호출 순서로 추적할 수 있다.
4. 동기화 지점(`wait_on_buffer`, `lock_buffer`, `sleep_on`/`wake_up`)이 "인터럽트는 데이터만 바꾸고 플래그는 호출자가 바꾼다"는 원칙(`buffer.c:7–13`)으로 어떻게 배치되었는지 말할 수 있다.
5. 읽기 요청 종류(READ/READA/WRITE/WRITEA)와 큐 삽입 정책의 선택지를 범위 안에서 빠짐없이 비교할 수 있다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준)
| 파일 | 줄 | 내용 |
|---|---|---|
| `include/linux/fs.h` | 26–29 | `READ`/`WRITE`/`READA`/`WRITEA` |
| `include/linux/fs.h` | 33–34, 47–49 | `MAJOR`/`MINOR`, `NR_HASH` 307, `NR_BUFFERS`, `BLOCK_SIZE` 1024 |
| `include/linux/fs.h` | 68–81 | `struct buffer_head` |
| `fs/buffer.c` | 7–13 | 설계 원칙 주석 |
| `fs/buffer.c` | 30–34 | `start_buffer`, `hash_table`, `free_list`, `buffer_wait`, `NR_BUFFERS` |
| `fs/buffer.c` | 36–42 | `wait_on_buffer()` |
| `fs/buffer.c` | 44–82 | `sys_sync()`, `sync_dev()` |
| `fs/buffer.c` | 128–129 | `_hashfn`/`hash` 매크로 |
| `fs/buffer.c` | 131–174 | `remove_from_queues`, `insert_into_queues`, `find_buffer` |
| `fs/buffer.c` | 183–196 | `get_hash_table()` |
| `fs/buffer.c` | 205–251 | `BADNESS`, `getblk()` |
| `fs/buffer.c` | 253–261 | `brelse()` |
| `fs/buffer.c` | 267–281 | `bread()` |
| `fs/buffer.c` | 296–346 | `bread_page()`, `breada()` (참조) |
| `fs/buffer.c` | 348–381 | `buffer_init()` |
| `kernel/blk_drv/blk.h` | 15, 23–33 | `NR_REQUEST` 32, `struct request` |
| `kernel/blk_drv/blk.h` | 40–48 | `IN_ORDER`, `struct blk_dev_struct` |
| `kernel/blk_drv/blk.h` | 78–98 | 하드디스크용 `DEVICE_*` 매크로, `CURRENT`, `do_hd` 선언 |
| `kernel/blk_drv/blk.h` | 109–136 | `end_request()`, `INIT_REQUEST` |
| `kernel/blk_drv/ll_rw_blk.c` | 21–40 | `request[]`, `wait_for_request`, `blk_dev[]` |
| `kernel/blk_drv/ll_rw_blk.c` | 42–57 | `lock_buffer`/`unlock_buffer` |
| `kernel/blk_drv/ll_rw_blk.c` | 64–86 | `add_request()` |
| `kernel/blk_drv/ll_rw_blk.c` | 88–143 | `make_request()` |
| `kernel/blk_drv/ll_rw_blk.c` | 145–165 | `ll_rw_block()`, `blk_dev_init()` |
| `kernel/blk_drv/hd.c` | 25, 34–35, 56–65 | `MAJOR_NR` 3, `MAX_ERRORS`, `hd[]` 파티션 표, `port_read`/`port_write` |
| `kernel/blk_drv/hd.c` | 71–160 | `sys_setup()` — 파티션 표를 `bread(0x300+drive*5, 0)`로 읽음 (135–153) |
| `kernel/blk_drv/hd.c` | 180–200 | `hd_out()` — `do_hd = intr_addr` 후 포트에 명령 |
| `kernel/blk_drv/hd.c` | 242–292 | `bad_rw_intr`, `read_intr`, `write_intr`, `recal_intr` |
| `kernel/blk_drv/hd.c` | 294–341 | `do_hd_request()` |
| `kernel/blk_drv/hd.c` | 343–349 | `hd_init()` — IDT 0x2E, PIC 마스크 해제 |
| `kernel/system_call.s` | 221–250 | `hd_interrupt` — EOI, `xchgl _do_hd`, `call *%edx` |
| `kernel/sched.c` | 151–165, 188–194 | `sleep_on()`, `wake_up()` |
| `init/main.c` | 126–137 | `blk_dev_init` → `buffer_init` → `hd_init` → `sti` 순서 |
| `boot/bootsect.s` | 43 | `ROOT_DEV = 0x306` |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 (buffer_head 한 개)**: 상태를 (`b_uptodate`, `b_dirt`, `b_lock`, `b_count`) 4-튜플로 본다. 주요 상태: `free`(0,0,0,0, `b_dev=0`) → `claimed`(0,0,0,1; `getblk` 243–249) → `reading`(0,0,1,1; `make_request:105`) → `uptodate`(1,0,0,1; `end_request:113–114`) → `dirty`(1,1,0,n; `file_write` 등이 `b_dirt=1`) → `writing`(1,0,1,n; `add_request:71`이 `b_dirt=0`, `lock_buffer`) → `released`(1,0,0,0; `brelse:258`) → 재사용 시 `getblk`가 `BADNESS` 최소 버퍼 선택. 전환 원인·변경 데이터·유지 조건을 각 화살표에 적는다.
- **상태 변화도 (request 한 개)**: `dev=-1`(빈 슬롯) → 채워짐(`make_request:133–141`) → 큐 삽입/즉시 실행(`add_request`) → `CURRENT`(컨트롤러 명령 발행) → 섹터별 인터럽트로 `nr_sectors` 감소 → `end_request`가 `dev=-1`, `CURRENT=next`.
- **모드·선택지 비교 1 (범위: `ll_rw_block`의 `rw` 값 전부)**: `READ`/`WRITE`/`READA`/`WRITEA`(`fs.h:26–29`). 잠긴 버퍼 처리, 큐 부족 시 동작, 호출처.
- **모드·선택지 비교 2 (범위: `add_request`가 새 요청을 넣을 수 있는 자리 전부)**: (a) 큐 비어 있음 → 즉시 `request_fn` 호출, (b) `IN_ORDER` 조건을 만족하는 중간 자리, (c) 꼬리. `IN_ORDER`의 세 비교 키(cmd, dev, sector)와 READ 우선 규칙.
- **모드·선택지 비교 3 (범위: `make_request`가 요청 슬롯을 찾는 시작점)**: READ는 `request+NR_REQUEST`(32개 전부), WRITE는 `request+21`(앞 2/3)만.
- 혼합 금지: 버퍼 상태(플래그)와 요청 큐 정책을 한 슬라이드에 섞지 않는다.

## 120분 운영안
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–02 | 4 | 핵심 질문과 지도 |
| 03–08 | 16 | 배경: 왜 캐시인가, 블록·섹터·장치 번호, 메모리 배치, `buffer_head` 필드, `buffer_init` |
| 09–16 | 24 | `bread`/`getblk`/`brelse` 코드, 해시·free list 그림, 플래그 상태 변화도, 동기화 원칙 |
| 17–18 | 8 | 시연 A (bread 두 번: 첫 번째는 디스크, 두 번째는 캐시 적중) |
| 19–27 | 24 | 요청 큐: `ll_rw_block`→`make_request`→`add_request`, `IN_ORDER` 비교, `do_hd_request`, `hd_interrupt`→`read_intr`→`end_request` |
| 28–31 | 14 | 시연 B (`do_hd_request` → 인터럽트 → `b_uptodate` 0→1), 시연 C (쓰기 경로와 `sync`) |
| 32–36 | 14 | 질문의 답, 전체 그림, 현대 커널 비교, 흔한 오해 |
| 37–38 | 6 | 이해 확인과 정리 |
| 예비 | 10 | 질의응답, 시연 재시도 |

## 슬라이드 계획
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 11. 버퍼 캐시와 블록 장치 | 제목과 핵심 질문. 부제: "read() 한 번에 디스크는 몇 번 도는가 — 0번, 1번, 그 이상?" | 제목 |
| 02 | 15회차 지도 — 11회차 위치 | 15회차 표. 06~10의 프로세스 축이 끝나고 11(버퍼)·12(파일 시스템)·13(tty)의 I/O 축이 시작됨. 12회차의 `namei`가 오늘 `bread`를 부른다는 화살표. | 지도 |
| 03 | 디스크와 메모리의 속도 차이 | 배경: 1991년 IDE 디스크 탐색 ms 단위 vs 메모리 ns 단위. 같은 블록을 읽는 요청은 매우 흔함(디렉터리, inode 블록, 비트맵). 그래서 "읽은 적 있으면 메모리에서 준다"는 캐시. | 배경 |
| 04 | 단위 정리: 섹터, 블록, 장치 번호 | 섹터 512B(하드웨어), 블록 1024B = 2섹터(`fs.h:49`, `make_request:136–137`의 `<<1`과 `nr_sectors=2`). 장치 번호 `MAJOR`/`MINOR`(`fs.h:33–34`), 하드디스크 major 3(`hd.c:25`), 루트 `0x306`(`bootsect.s:43`) = 2번째 드라이브 1번 파티션. | 배경 |
| 05 | 메모리 지도에서 버퍼 영역 | 3회차 지도 재사용: 커널 `end` ~ `buffer_memory_end`(`init/main.c:117–122`) 사이. `buffer_init(buffer.c:348–381)`: 헤더는 `end`에서 위로, 데이터 블록은 끝에서 아래로, 640K~1M 구멍 건너뜀(`372–373`). 결과 `NR_BUFFERS`. 부팅 캡처의 "N buffers = M bytes buffer space" 줄과 연결. | 코드 |
| 06 | struct buffer_head | `fs.h:68–81` 전체. `b_data`(1024B 포인터), `b_blocknr`, `b_dev`, 플래그 4개, `b_wait`(잠든 태스크), 해시 체인 `b_prev/b_next`, free list `b_prev_free/b_next_free`. 그림: 헤더 하나와 그 데이터 블록. | 코드 |
| 07 | 네 플래그의 뜻 | 표. `b_uptodate`: 데이터가 디스크 내용과 같은가. `b_dirt`: 메모리가 디스크보다 새로운가. `b_lock`: I/O 진행 중이라 손대면 안 되는가. `b_count`: 지금 쓰는 사람 수. 각각 "누가 1로, 누가 0으로"를 다음 슬라이드들에서 채운다. | 배경 |
| 08 | 두 개의 자료구조: 해시 테이블과 free list | `buffer.c:128–129` `hash(dev,block) = hash_table[(dev^block)%307]`. `buffer.c:131–164` 제거/삽입: 해시 체인은 "찾기", free list는 "재사용 순서"(LRU 비슷: 삽입은 항상 꼬리). 그림: 307개 버킷과 원형 free list에 같은 헤더가 두 번 연결됨. | 코드 |
| 09 | 코드: bread | `buffer.c:267–281`. `getblk`로 헤더 확보 → `b_uptodate`면 즉시 반환(디스크 0번) → 아니면 `ll_rw_block(READ,bh)` + `wait_on_buffer` → 다시 `b_uptodate` 검사 → 실패면 `brelse` 후 NULL. 핵심 질문에 대한 첫 답: "`b_uptodate`가 0일 때만". | 코드 |
| 10 | 코드: getblk 전반부 (찾기와 고르기) | `buffer.c:205–227`. `get_hash_table`(183–196: 찾고 `b_count++` 후 `wait_on_buffer`, 깨어난 뒤 재확인) → 없으면 free list 순회에서 `b_count==0` 중 `BADNESS = dirt*2 + lock` 최소 선택, 0이면 즉시 중단 → 하나도 없으면 `sleep_on(&buffer_wait)`. | 코드 |
| 11 | 코드: getblk 후반부 (확정) | `buffer.c:228–251`. `wait_on_buffer` → `b_count` 재검사 → `b_dirt`면 `sync_dev` 후 재검사 → 자는 동안 누가 같은 블록을 넣었는지 `find_buffer` 재확인 → `b_count=1, b_dirt=0, b_uptodate=0` → 해시 체인 옮김. "goto repeat가 네 번"인 이유 = 잠들 때마다 세상이 바뀐다. | 코드 |
| 12 | 코드: brelse와 wait_on_buffer | `buffer.c:253–261`: `wait_on_buffer` 후 `b_count--`, 0 미만이면 panic, `wake_up(&buffer_wait)`. `buffer.c:36–42`: `cli` → `while(b_lock) sleep_on(&b_wait)` → `sti`. `sleep_on`(`sched.c:151–165`)이 `*p`를 체인으로 쓰는 방식 5회차 복습. | 코드 |
| 13 | 상태 변화도: buffer_head 플래그 | 4-튜플 상태도. free(0,0,0,0) —getblk 243–245→ claimed(0,0,0,1) —make_request 105 lock_buffer→ reading(0,0,1,1) —end_request 113–114→ uptodate(1,0,0,1) —brelse→ cached(1,0,0,0) —getblk 적중→ (1,0,0,1) —쓰기 `b_dirt=1`→ dirty(1,1,0,n) —add_request 71 + lock→ writing(1,0,1,n) —end_request→ (1,0,0,n). 각 전환에 원인 함수와 바뀌는 필드, 유지 조건(`b_count>0`이면 재사용 대상 아님; `b_lock`이면 플래그 변경 금지). | 상태도 |
| 14 | 동기화 원칙: 인터럽트는 데이터만 | `buffer.c:7–13` 주석 인용. 인터럽트 핸들러(`read_intr`)는 `port_read`로 `b_data`만 채우고, 플래그는 `end_request`(인터럽트 문맥이지만 블록 계층의 코드) 한 곳에서만. `wait_on_buffer`의 `cli/sti`가 필요한 이유: `b_lock` 검사와 `sleep_on` 사이에 인터럽트가 `unlock`하면 영원히 잠듦. | 배경 |
| 15 | sync: 더러운 버퍼는 언제 디스크로 가는가 | `buffer.c:44–57` `sys_sync`(inode 먼저, 전체 버퍼 순회), `59–82` `sync_dev`(장치 하나, 두 번 순회). 호출처: `getblk:232`(더러운 버퍼 재사용 전), `iput`(12회차), `sys_umount`. 0.11에는 주기적 flush 데몬이 없다 — 명시. | 코드 |
| 16 | bread_page와 breada (참조) | `buffer.c:296–315` 4블록 동시 요청 후 대기(9회차 `do_no_page`가 사용), `322–346` 미리읽기. `breada:336`의 `ll_rw_block(READA,bh)`가 `tmp`가 아닌 `bh`를 넘기는 원본 그대로의 코드를 보여주고 "원본의 오타로 보이며 lab에서는 수정하지 않았다"고 각주. | 코드 |
| 17 | 시연 A 계획: 같은 블록 두 번 읽기 | 중단점 `bread`, `ll_rw_block`. 셸에서 `cat /etc/rc`를 두 번. 관찰: 첫 번째 `bread`에서 `p bh->b_uptodate`=0 → `ll_rw_block` 진입. 두 번째는 `getblk` 반환 직후 `b_uptodate`=1 → `ll_rw_block` 미진입, `b_count` 값. | 시연 |
| 18 | 시연 A 캡처 | GDB 로그 두 묶음(첫 실행/두 번째 실행)과 `info breakpoints`의 hit count 차이. 각주: lab/ QEMU i386 + GDB, 원본 미수정, 부팅 직후 상태(캐시 비어 있음)에서 시작. | 캡처 |
| 19 | 블록 계층의 자료구조 | `blk.h:23–33` `struct request`(dev=-1이면 빈 슬롯, sector, nr_sectors, buffer, waiting, bh, next), `blk.h:45–48` `blk_dev_struct`(request_fn, current_request), `ll_rw_blk.c:21–40` `request[32]`와 `blk_dev[7]` 초기값. `hd_init:345`가 `request_fn=do_hd_request` 등록. 그림: `blk_dev[3].current_request` → 연결 리스트. | 코드 |
| 20 | 코드: ll_rw_block과 make_request 전반부 | `ll_rw_blk.c:145–155` major 검사. `88–109`: READA/WRITEA는 잠겨 있으면 포기, `lock_buffer`, 이미 `b_uptodate`(READ)거나 `!b_dirt`(WRITE)면 unlock 후 리턴 — 두 번째 "디스크에 안 가는 지점". | 코드 |
| 21 | 코드: make_request 후반부 (슬롯 찾기) | `ll_rw_blk.c:110–143`. READ는 32개 전체, WRITE는 앞 21개에서 역순으로 `dev<0` 탐색. 없으면 READA/WRITEA는 포기, 아니면 `sleep_on(&wait_for_request)`. 슬롯 채움: `sector = b_blocknr<<1`, `nr_sectors=2`, `buffer=b_data`, `bh=bh`. | 코드 |
| 22 | 비교: ll_rw_block의 rw 값 (범위: 4종 전부) | 표. `READ`(0)/`WRITE`(1)/`READA`(2)/`WRITEA`(3) (`fs.h:26–29`). 잠긴 버퍼: READ/WRITE 대기, READA/WRITEA 포기(`96–97`). 슬롯 없음: 대기 vs 포기(`125–128`). 슬롯 범위: READ 32개, WRITE 21개(`115–118`). 호출처: `bread`/`sync`/`breada`. WRITEA는 0.11에서 호출처 없음을 명시. | 비교 |
| 23 | 코드: add_request | `ll_rw_blk.c:64–86`. `cli`; `req->bh->b_dirt=0`(큐에 들어가는 순간 "더러움"을 버림 — 이후 쓰기는 새 dirt); 큐 비면 `current_request=req; sti; request_fn()`; 아니면 `IN_ORDER` 조건을 만족하는 자리까지 전진 후 삽입. | 코드 |
| 24 | 비교: 큐 삽입 정책 (범위: add_request의 삽입 위치 3가지) | (a) 빈 큐 → 즉시 실행(`72–77`). (b) `tmp` 뒤에 삽입: `(IN_ORDER(tmp,req) \|\| !IN_ORDER(tmp,tmp->next)) && IN_ORDER(req,tmp->next)`(`78–82`) — 한 방향으로 오르다 꺾이는 지점을 허용하는 단방향 엘리베이터. (c) 꼬리(`for` 종료). `IN_ORDER`(`blk.h:40–43`) 키: cmd(READ<WRITE 우선), dev, sector. 단 삽입 지점 탐색은 `tmp->next`가 있는 동안이라 첫 요소(`CURRENT`) 앞에는 절대 넣지 않음. | 비교 |
| 25 | 코드: do_hd_request | `hd.c:294–341`. `INIT_REQUEST`(`blk.h:127–136`: 큐 비면 return, 잠금 검사) → `MINOR`로 파티션 → `hd[dev].start_sect` 더함 → `divl` 두 번으로 sec/head/cyl → reset/recalibrate 처리 → WRITE면 `hd_out(…, WIN_WRITE, &write_intr)` + DRQ 폴링 + 첫 섹터 `port_write`; READ면 `hd_out(…, WIN_READ, &read_intr)`만 하고 **리턴**. "리턴한다"가 핵심: CPU는 다른 일을 하러 간다. | 코드 |
| 26 | 코드: hd_out과 hd_interrupt | `hd.c:180–200`: `do_hd = intr_addr` 후 포트 7개에 outb, 마지막 `outb(cmd, ++port)`. `system_call.s:221–250`: 레지스터 저장, EOI(0xA0, 0x20), `xchgl _do_hd,%edx`로 핸들러를 꺼내면서 NULL로, 없으면 `unexpected_hd_interrupt`, `call *%edx`. `hd_init:346`의 IDT 0x2E = IRQ14. | 코드 |
| 27 | 코드: read_intr와 end_request | `hd.c:250–267`: `win_result` 오류면 `bad_rw_intr`; `port_read(HD_DATA, CURRENT->buffer, 256)`(256워드=512B), `buffer+=512`, `sector++`, `nr_sectors` 남으면 `do_hd=&read_intr`로 재무장 후 리턴; 0이면 `end_request(1)` + `do_hd_request()`(다음 요청 시작). `blk.h:109–125` `end_request`: `b_uptodate=uptodate`, `unlock_buffer`(→`wake_up(&b_wait)`), `wake_up(&waiting)`, `wake_up(&wait_for_request)`, `dev=-1`, `CURRENT=next`. | 코드 |
| 28 | 호출 순서도: bread 한 번의 전체 경로 | 왼쪽 열(프로세스 문맥): `bread` → `getblk` → `ll_rw_block` → `make_request`(lock) → `add_request` → `do_hd_request` → `hd_out` → 리턴 → `wait_on_buffer` → `sleep_on` → `schedule`. 오른쪽 열(인터럽트 문맥, 2회): `hd_interrupt` → `read_intr` → `port_read` …(2번째) → `end_request` → `wake_up`. 다시 왼쪽: 깨어남 → `b_uptodate` 확인 → 반환. 상태 변화도(13)와 다른 "순서도"임을 명시. | 배경 |
| 29 | 시연 B 계획: 인터럽트 후 b_uptodate 반전 | 중단점 `do_hd_request`, `read_intr`, `end_request`(inline이므로 `hd.c:265` 줄 번호로), 그리고 `bread` 복귀 지점(`buffer.c:277`). 관찰: `do_hd_request`에서 `p *CURRENT`(sector, nr_sectors=2, `bh->b_lock`=1, `bh->b_uptodate`=0), `read_intr` 두 번 hit(`p CURRENT->nr_sectors` 2→1→0), `end_request` 직후 `p CURRENT->bh->b_uptodate`=1, `b_lock`=0, `buffer.c:277`에서 `p bh->b_uptodate`=1. | 시연 |
| 30 | 시연 B 캡처 | GDB 로그: `info registers eip`가 인터럽트 문맥(`read_intr`)에 있을 때 `p current->pid`가 "우연히 실행 중이던" 태스크(종종 task 0)임을 보여 "인터럽트는 누구의 문맥도 아니다"를 실제 관찰로. `b_uptodate` 0→1 전후. 각주: lab/ QEMU, `-drive if=ide`, 원본 미수정; 인터럽트 중단점은 타이밍에 따라 `write_intr`가 먼저 걸릴 수 있어 조건부 중단 사용. | 캡처 |
| 31 | 시연 C 계획·캡처: 쓰기와 sync | 셸에서 `echo x > /tmp/f`(12회차 `file_write`가 `b_dirt=1`). 중단점 `sys_sync`, `add_request`. 관찰: `sync` 전 `b_dirt=1`, `add_request:71`에서 0으로, 이어 `write_intr`. 시간 부족 시 사전 캡처로 대체하고 "0.11은 `sync`를 부르지 않으면 더러운 버퍼가 디스크로 가지 않는다(재사용 시 제외)"만 강조. | 시연 |
| 32 | 질문의 답: read()가 디스크에 접근하는 때 | 세 관문을 모두 통과할 때만: (1) `getblk`가 해시에서 못 찾거나 찾았어도 `b_uptodate==0`(`bread:273`), (2) `make_request`의 `rw==READ && b_uptodate` 재검사(`106`), (3) 요청 슬롯이 있을 때 — 그제야 `do_hd_request`가 포트에 명령. 그 외에는 모두 메모리 복사. 그리고 "접근한다"의 실제 뜻은 "명령을 내리고 잠든다; 데이터는 인터럽트가 가져온다". | 정리 |
| 33 | 전체 그림: 계층과 경계 | 3층 그림: 파일 시스템(12회차: `bread`를 부름) / 버퍼 캐시(`buffer.c`: 블록 단위, 장치 무관) / 블록 장치 드라이버(`ll_rw_blk.c` + `hd.c`: 섹터·포트). 경계를 넘는 호출은 `ll_rw_block` 하나, 돌아오는 통로는 `end_request`의 `wake_up` 하나. | 배경 |
| 34 | 현대 커널과의 차이 (짧게) | 1024B 고정 버퍼 → 페이지 캐시 + bio; 32개 request 배열 → 블록 멀티큐; 단방향 엘리베이터 → mq-deadline/BFQ; `sync` 수동 → writeback 스레드와 dirty ratio; PIO `insw` → DMA. 14회차에서 다시. | 배경 |
| 35 | 흔한 오해 | (1) "`bread`가 디스크를 읽는다" — 보통은 안 읽는다. (2) "`read_intr`가 프로세스를 깨운다" — `end_request`의 `wake_up`이 `state=0`으로 바꿀 뿐, 실행은 다음 `schedule`. (3) "`b_dirt=1`이면 곧 디스크에 써진다" — `sync`나 재사용 전까지 메모리에만. (4) "요청 큐는 FIFO" — `IN_ORDER` 엘리베이터이고 READ가 WRITE보다 앞선다. | 배경 |
| 36 | 수치 참고 (코드 추론) | `NR_HASH` 307, `NR_REQUEST` 32(쓰기는 21), 블록 1024B, 섹터 2개/블록, `MAX_ERRORS` 7, 부팅 캡처의 실제 `NR_BUFFERS`. "추론"과 "캡처"를 열로 분리. | 코드 |
| 37 | 이해 확인 (정답 포함) | 아래 4문항. | 질문 |
| 38 | 정리와 다음 회차 | 오늘 함수 6개(`bread`, `getblk`, `brelse`, `ll_rw_block`, `do_hd_request`, `read_intr`)와 플래그 4개를 한 장에. 다음 12회차: "/etc/rc라는 문자열이 어떻게 디스크 블록이 되는가?" — 오늘의 `bread(dev, block)`에서 `block`이 어디서 오는지. | 정리 |

## 강사 시연
**A. 같은 블록 두 번 읽기 — 캐시 적중**
- 환경: `lab/` QEMU i386 + GDB, 원본 미수정. 부팅 직후(캐시가 거의 비어 있음)에서 시작.
- 명령: `b bread`, `b ll_rw_block`, `c`. 게스트 셸 `cat /etc/rc`. 한 번 더 `cat /etc/rc`.
- 관찰: 첫 실행 — `bread` 진입 `p dev`, `p block`; `finish`를 쓰지 말고 `n`으로 `buffer.c:273`까지 가서 `p bh->b_uptodate`=0, `c`하면 `ll_rw_block` hit. 두 번째 실행 — 같은 `block`에서 `p bh->b_uptodate`=1, `p bh->b_count`, `ll_rw_block` hit 없음(`info breakpoints` hit count 비교).
- 기대 출력: 첫 번째 `$ = 0 '\000'` 후 `ll_rw_block` 중단, 두 번째 `$ = 1 '\001'` 후 바로 다음 `bread`.
- 대체: 사전 캡처 로그 2개(첫 실행/두 번째). `cat`이 inode·디렉터리 블록도 읽어 `bread` hit가 여러 번임을 미리 말함.

**B. do_hd_request → hd_interrupt → b_uptodate 0→1**
- 명령: `b do_hd_request`, `b read_intr`, `b hd.c:265`(`end_request(1)` 직전), `b buffer.c:277`. 게스트에서 아직 읽지 않은 파일 `cat /usr/...`(또는 부팅 직후 첫 `ls /`).
- 관찰: `do_hd_request`에서 `p *CURRENT`, `p *CURRENT->bh`(`b_lock=1`, `b_uptodate=0`); `p current->pid`(요청한 프로세스). `read_intr` 1회차 `p CURRENT->nr_sectors`=2, 2회차 =1, `p current->pid`(인터럽트 시점에 실행 중이던 태스크 — 요청자와 다를 수 있음). `hd.c:265`에서 `n` 후 `p CURRENT->bh->b_uptodate`... 주의: `end_request` 안에서 `CURRENT`가 `next`로 바뀌므로 그 전에 `set $bh = CURRENT->bh` 해 두고 `p $bh->b_uptodate`, `p $bh->b_lock`. `buffer.c:277`에서 `p bh->b_uptodate`=1.
- 기대 출력: `b_uptodate` 0 → 1, `b_lock` 1 → 0, `nr_sectors` 2 → 1 → 0.
- 대체: 인터럽트 중단점이 QEMU IDE 타이밍으로 불안정하면 `read_intr`에 `if CURRENT->nr_sectors==1` 조건을 달거나 사전 캡처 사용.

**C. 쓰기 경로와 sync (시간 여유 시)**
- 명령: `b add_request`, `b write_intr`. 게스트 `echo x > /tmp/f; sync`.
- 관찰: `add_request` 진입 `p req->bh->b_dirt`=1, 한 줄 뒤 0; `p req->cmd`=1; `write_intr` hit.
- 대체: 사전 캡처.

## 이해 확인 질문과 정답
1. **Q.** `bread(dev, b)`가 디스크 명령을 내리지 않고 돌아오는 두 지점의 조건은?
   **A.** (1) `getblk`가 돌려준 버퍼의 `b_uptodate`가 1(`buffer.c:273–274`). (2) 그 사이에 다른 프로세스가 읽기를 끝내 `make_request`의 재검사 `rw==READ && bh->b_uptodate`(`ll_rw_blk.c:106–109`)에 걸림.
2. **Q.** `do_hd_request()`는 READ 명령을 내린 뒤 무엇을 하는가? 데이터는 누가 메모리에 넣는가?
   **A.** `hd_out`으로 포트에 명령만 쓰고 **리턴**한다(`hd.c:337–338`). 데이터는 IRQ14 → `hd_interrupt`(`system_call.s:221–250`) → `read_intr`(`hd.c:250–267`)의 `port_read`가 섹터마다 512B씩 `CURRENT->buffer`로 옮긴다.
3. **Q.** `b_dirt`는 누가 1로 만들고 누가 0으로 만드는가?
   **A.** 1: 버퍼를 고친 파일 시스템 코드(예: `file_write`, `new_block`, `write_inode`; 12회차). 0: `add_request`가 쓰기 요청을 큐에 넣는 순간(`ll_rw_blk.c:70–71`), `getblk`가 새로 할당할 때(`buffer.c:244`), `invalidate_buffers`(`95`).
4. **Q.** 큐에 WRITE 요청이 가득 찰 수 있는가?
   **A.** 아니다. WRITE는 `request[0..20]`(앞 2/3)만 탐색하고(`ll_rw_blk.c:115–118`), 나머지 11개는 READ 전용이다. 또 `IN_ORDER`에서 `cmd` 비교로 READ가 WRITE보다 앞에 삽입된다(`blk.h:40–43`).

## 처음 등장하는 용어
- **버퍼 캐시(buffer cache)**: 디스크 블록의 메모리 복사본과 그 메타데이터(`buffer_head`) 집합.
- **블록 / 섹터**: 1024B 파일 시스템 단위 / 512B 하드웨어 단위. 0.11은 1블록 = 2섹터.
- **`b_uptodate` / `b_dirt` / `b_lock` / `b_count`**: 디스크와 같음 / 디스크보다 새로움 / I/O 중 / 사용자 수.
- **해시 체인 / free list**: `(dev,block)`으로 찾는 연결 / 재사용 순서를 위한 원형 연결.
- **요청(request) 큐**: 장치별 `current_request`로 시작하는 `struct request` 연결 리스트.
- **엘리베이터(elevator) 정렬**: 섹터 번호 순으로 요청을 삽입해 헤드 이동을 줄이는 정책(`IN_ORDER`).
- **미리읽기(read-ahead, READA)**: 지금 필요하지 않은 블록을 미리 요청하되 자원 부족이면 포기.
- **PIO(`insw`/`outsw`)**: CPU가 포트에서 워드 단위로 직접 옮기는 입출력. DMA 아님.
- **IRQ14 / 0x2E**: 하드디스크 인터럽트 선과 그 IDT 벡터(`hd_init`).

## 주의: 흔한 오해 / 말하지 말아야 할 것
- `getblk`는 LRU라고 단정하지 않는다. free list 꼬리 삽입 + `BADNESS` 최소 선택이며, "오래된 것부터"는 근사 설명임을 말한다.
- `end_request`는 `blk.h`의 `extern inline`이라 심볼 중단점이 안 걸릴 수 있다. 줄 번호 중단점(`hd.c:265`)을 쓰고, 캡처 각주에 적는다.
- `breada:336`의 `ll_rw_block(READA,bh)`는 원본 그대로이며 lab에서 고치지 않았다. "버그"라고 단정하기보다 "tmp를 의도한 것으로 보인다"로 말한다.
- `add_request`의 삽입 탐색은 `tmp->next`가 있는 동안만 돌므로 현재 실행 중인 요청 앞에는 끼어들지 않는다. "항상 섹터 순 정렬"이라고 말하지 않는다.
- 0.11에는 주기적 writeback이 없다. "커널이 알아서 쓴다"고 말하지 않는다. `sync`, 버퍼 재사용(`getblk:231–232`), `iput`의 `sync_dev`(12회차)만이 경로다.
- 인터럽트 문맥에서 `current`는 요청자가 아니라 "그때 실행 중이던 태스크"다. 시연 B 캡처에서 이를 실제 관찰로 보여주되, 어느 태스크가 잡힐지는 실행마다 다르다고 말한다.
- 상태 변화도의 4-튜플 값은 코드 추론이며, 캡처에서 관찰된 값만 "관찰"로 표기한다.

---

# 12. 파일 시스템: inode·경로 탐색·I/O

## 핵심 질문
"/etc/rc"라는 문자열이 어떻게 디스크 블록이 되는가?

## 학습 목표 (3~5개)
1. MINIX 1.0 파일 시스템의 디스크 배치(부트 블록, 슈퍼 블록, inode 비트맵, 존 비트맵, inode 표, 데이터 존)와 그 메모리 상대(`super_block`, `m_inode`, `file`)를 그릴 수 있다.
2. `namei("/etc/rc")`가 `get_dir` → `find_entry` → `iget` → `read_inode` → `bread`를 반복하며 루트 inode 1번에서 시작해 `rc`의 inode 번호를 얻는 과정을 한 단계씩 추적할 수 있다.
3. `bmap()`이 파일 내 블록 번호를 `i_zone[0..6]`(직접), `i_zone[7]`(단일 간접), `i_zone[8]`(이중 간접)으로 디스크 블록 번호로 바꾸는 규칙과 상한(7+512+512²)을 설명할 수 있다.
4. `sys_open`이 fd 슬롯 → `file_table` 슬롯 → `open_namei`의 순서로 세 자료구조를 연결하고, `sys_read`/`sys_write`가 `i_mode` 종류에 따라 `file_read`/`rw_char`/`block_read`/`read_pipe`로 갈라지는 구조를 말할 수 있다.
5. `open()` 플래그 중 0.11 커널이 실제로 검사하는 것과 정의만 된 것을 소스로 구분할 수 있다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준)
| 파일 | 줄 | 내용 |
|---|---|---|
| `include/linux/fs.h` | 36–46 | `NAME_LEN` 14, `ROOT_INO` 1, `I_MAP_SLOTS`/`Z_MAP_SLOTS` 8, `SUPER_MAGIC` 0x137F, `NR_OPEN` 20, `NR_INODE` 32, `NR_FILE` 64, `NR_SUPER` 8 |
| `include/linux/fs.h` | 55–56 | `INODES_PER_BLOCK`(=32), `DIR_ENTRIES_PER_BLOCK`(=64) |
| `include/linux/fs.h` | 83–91 | `struct d_inode` (32B, 디스크 형식) |
| `include/linux/fs.h` | 93–114 | `struct m_inode` (메모리 형식: 앞부분은 `d_inode`와 동일 배치) |
| `include/linux/fs.h` | 116–122 | `struct file` |
| `include/linux/fs.h` | 124–155 | `struct super_block`, `struct d_super_block` |
| `include/linux/fs.h` | 157–164 | `struct dir_entry`(16B), `inode_table[]`, `file_table[]`, `super_block[]` |
| `include/sys/stat.h` | 30–34 | `S_ISREG`/`S_ISDIR`/`S_ISCHR`/`S_ISBLK`/`S_ISFIFO` |
| `include/fcntl.h` | 7–17 | `O_ACCMODE` … `O_NDELAY` |
| `fs/super.c` | 27–29 | `super_block[NR_SUPER]`, `ROOT_DEV` |
| `fs/super.c` | 56–72 | `get_super()` |
| `fs/super.c` | 100–165 | `read_super()` — 블록 1 읽기, magic 검사, 비트맵 블록 2.. 읽기 |
| `fs/super.c` | 242–281 | `mount_root()` — `iget(ROOT_DEV, ROOT_INO)`, `pwd`/`root`, free 개수 출력 |
| `fs/inode.c` | 15 | `inode_table[NR_INODE]` |
| `fs/inode.c` | 72–148 | `_bmap()`, `bmap()`, `create_block()` |
| `fs/inode.c` | 150–192 | `iput()` |
| `fs/inode.c` | 194–226 | `get_empty_inode()` |
| `fs/inode.c` | 244–292 | `iget()` — 표 검색, 마운트 지점 건너뛰기, `read_inode` |
| `fs/inode.c` | 294–338 | `read_inode()`, `write_inode()` — inode 번호 → 블록 번호 산식 |
| `fs/namei.c` | 21, 29–31 | `ACC_MODE`, `MAY_EXEC/WRITE/READ` |
| `fs/namei.c` | 40–54 | `permission()` |
| `fs/namei.c` | 63–66 | `match()` 시작 (fs 세그먼트 비교, 참조) |
| `fs/namei.c` | 91–153 | `find_entry()` — `..` 특수 처리, 디렉터리 블록 순회 |
| `fs/namei.c` | 228–270 | `get_dir()` — `/` 또는 pwd에서 시작, 구성 요소별 반복 |
| `fs/namei.c` | 278–294 | `dir_namei()` — 마지막 구성 요소 분리 |
| `fs/namei.c` | 303–330 | `namei()` |
| `fs/namei.c` | 337–410 | `open_namei()` — O_CREAT/O_EXCL/O_TRUNC/권한 |
| `fs/open.c` | 138–185 | `sys_open()` — fd, `file_table`, tty 특례, `f_*` 채우기 |
| `fs/open.c` | 187–208 | `sys_creat()`, `sys_close()` |
| `fs/read_write.c` | 55–81 | `sys_read()` — 종류별 분기 |
| `fs/read_write.c` | 83–103 | `sys_write()` |
| `fs/file_dev.c` | 17–46 | `file_read()` — `bmap` + `bread` + `put_fs_byte` |
| `fs/file_dev.c` | 48–90 | `file_write()` — `create_block` + `b_dirt=1`, O_APPEND |
| `fs/bitmap.c` | 75–105 | `new_block()` — 존 비트맵에서 첫 0비트, `getblk` + `clear_block` |
| `fs/bitmap.c` | 136–168 | `new_inode()` — inode 비트맵에서 첫 0비트 |
| `fs/fcntl.c` | 47–72 | `sys_fcntl()` — `F_SETFL`이 저장하는 플래그 |
| `include/linux/sched.h` | 102 | `task_struct.filp[NR_OPEN]` |
| `init/main.c` | 179–183 | init의 `open("/etc/rc", O_RDONLY, 0)` → fd 0 |
| `fs/exec.c` | 199 | `do_execve`가 `namei(filename)` 사용 (9회차 연결) |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 (`m_inode` 슬롯 한 개)**: `비어 있음`(`i_count=0`, `i_dev=0`) → `읽는 중`(`get_empty_inode` → `i_dev/i_num` 설정, `read_inode`의 `i_lock=1`) → `메모리 상주`(`i_count≥1`, `i_lock=0`) → `공유`(`i_count` 증가: `iget` 적중, `sys_open`→`f_inode`, `fork`의 `filp` 복사) → `더러움`(`i_dirt=1`: `file_write`, `namei`의 atime) → `반납`(`iput`: `i_count>1`이면 감소만; 1이고 `i_nlinks==0`이면 `truncate`+`free_inode`; `i_dirt`면 `write_inode` 후 다시) → `비어 있음`. 전환 원인·변경 데이터·유지 조건을 표기.
- **상태 변화도 (경로 탐색 커서)**: 상태 = (현재 디렉터리 inode, 남은 문자열). `("/" → root inode 1, "etc/rc")` → `find_entry("etc")` → `(etc inode, "rc")` → `dir_namei` 반환 → `find_entry("rc")` → `rc inode` 번호 → `iget`. 각 단계에서 `i_count`가 오르내리는 쌍(`inode->i_count++` / `iput(inode)`)을 함께 표시.
- **모드·선택지 비교 1 (범위: `open()` 접근 모드 `O_ACCMODE` 2비트의 값 전부)**: `O_RDONLY`(0), `O_WRONLY`(1), `O_RDWR`(2), `3`(정의되지 않은 조합) — `ACC_MODE` 표 `"\004\002\006\377"`(`namei.c:21`)가 네 값에 각각 `MAY_READ`/`MAY_WRITE`/둘 다/`0377`(모든 비트)로 대응.
- **모드·선택지 비교 2 (범위: `include/fcntl.h:11–17`의 나머지 플래그 전부)**: `O_CREAT`, `O_EXCL`, `O_NOCTTY`, `O_TRUNC`, `O_APPEND`, `O_NONBLOCK`(=`O_NDELAY`). 커널이 검사하는 위치가 있는가(있음: `open_namei`/`file_write`/`fcntl`), 없음(헤더 주석 "isn't implemented yet" `fcntl.h:6`).
- **모드·선택지 비교 3 (범위: `sys_read`의 `i_mode` 분기 전부)**: pipe / `S_ISCHR` / `S_ISBLK` / `S_ISDIR`·`S_ISREG` / 그 외(`-EINVAL`). `sys_write`에서는 `S_ISDIR`가 빠지는 차이.
- 혼합 금지: inode 상태와 open 플래그, 파일 종류 분기는 각각 별도 슬라이드.

## 120분 운영안
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–02 | 4 | 핵심 질문과 지도 |
| 03–09 | 18 | 배경: 디스크 배치, 네 구조체, 부팅 시 `mount_root`가 만든 초기 상태 |
| 10–16 | 22 | 경로 탐색: `get_dir`/`find_entry`/`dir_namei`/`namei` 코드와 탐색 커서 상태도 |
| 17–20 | 12 | `iget`/`read_inode`/`iput`과 inode 슬롯 상태도, `bmap` |
| 21–22 | 10 | 시연 A (`namei` 중단 → `/etc/rc`의 inode 번호와 `i_zone[0]`) |
| 23–29 | 20 | `open_namei`/`sys_open`과 플래그 비교, `sys_read` 분기 비교, `file_read`/`file_write`, `new_block`/`new_inode` |
| 30–32 | 10 | 시연 B (`open_namei`와 fd 슬롯), 시연 C (`file_read` → `bmap` → `bread`) |
| 33–36 | 12 | 질문의 답(문자열 → 블록 전체 경로), 현대 비교, 흔한 오해 |
| 37–38 | 6 | 이해 확인과 정리 |
| 예비 | 6 | 질의응답 |

## 슬라이드 계획
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 12. 파일 시스템: inode·경로 탐색·I/O | 제목과 핵심 질문. 부제: "11회차의 `bread(dev, block)` — 그 `block`은 누가 정하는가". | 제목 |
| 02 | 15회차 지도 — 12회차 위치 | 15회차 표. 11(버퍼) 위에 12(파일 시스템)가 올라감, 09(exec)의 `namei`와 10(exit)의 `iput`이 오늘 함수임을 화살표로. | 지도 |
| 03 | 디스크 위의 배치 (MINIX 1.0 형식) | 그림: 블록 0 부트, 1 슈퍼 블록, 2.. inode 비트맵(`s_imap_blocks`개), 존 비트맵(`s_zmap_blocks`개), inode 표, `s_firstdatazone`부터 데이터. `read_super`의 `block=2` 시작(`super.c:141–151`)과 `read_inode`의 산식 `2 + s_imap_blocks + s_zmap_blocks + (i_num-1)/32`(`inode.c:303–304`)를 그림 위에 겹쳐 표시. | 배경 |
| 04 | 네 구조체: 디스크 형식 | `fs.h:83–91` `d_inode` 32B(`i_zone[9]`), `fs.h:146–155` `d_super_block`, `fs.h:157–160` `dir_entry` 16B = inode 번호 2B + 이름 14B. 1블록에 inode 32개, 디렉터리 엔트리 64개(`fs.h:55–56`). `mount_root:248–249`의 `sizeof(d_inode)==32` 검사. | 코드 |
| 05 | 네 구조체: 메모리 형식 | `fs.h:93–114` `m_inode` = `d_inode` 앞부분 + `i_wait/i_dev/i_num/i_count/i_lock/i_dirt/i_pipe/i_mount…`. `read_inode:307–309`가 `*(struct d_inode *)inode = …`로 앞 32B만 덮어쓰는 이유. `fs.h:124–144` `super_block`의 `s_imap[8]/s_zmap[8]`(비트맵 버퍼를 계속 붙들고 있음), `s_isup/s_imount`. | 코드 |
| 06 | 세 개의 표 | `fs.h:162–164`: `inode_table[32]`, `file_table[64]`, `super_block[8]`, 그리고 태스크별 `filp[20]`(`sched.h:102`). 그림: `filp[fd]` → `file_table[i]` → `inode_table[j]` → 디스크. `struct file`(`fs.h:116–122`)의 `f_pos`가 "열린 파일마다"임을 강조(fork로 공유 가능). | 코드 |
| 07 | 부팅 때 만들어진 초기 상태 | `mount_root`(`super.c:242–281`): `file_table` 초기화, `read_super(ROOT_DEV)`, `iget(ROOT_DEV, 1)`, `i_count += 3`(`265`: isup/imount/pwd/root 네 곳에서 참조), `current->pwd = current->root = mi`, free 블록·inode 세기. 부팅 캡처의 "N/M free blocks" 줄과 연결. 11회차의 `sys_setup` → `mount_root` 호출(`hd.c:158`). | 코드 |
| 08 | 코드: read_super | `super.c:100–165`. 빈 `super_block[]` 슬롯 찾기 → `bread(dev,1)` → `d_super_block` 복사 → `s_magic != 0x137F`면 실패(`132`) → 비트맵 블록을 `bread`로 차례로 읽어 `s_imap[i]/s_zmap[i]`에 **brelse하지 않고** 보관 → `s_imap[0]->b_data[0] \|= 1`, `s_zmap[0]->b_data[0] \|= 1`(0번은 예약, `161–162`). | 코드 |
| 09 | 호출 순서도: open("/etc/rc") 전체 | 세로 호출 순서: `sys_open` → `open_namei` → `dir_namei` → `get_dir` → [`find_entry` → `bread` ×n, `iget` → `read_inode` → `bread`] ×구성요소 → `find_entry("rc")` → `iget` → 반환 → `f_*` 채움 → fd. 오른쪽에 11회차 `bread` 상자를 작게 반복. "상태 변화도가 아니라 호출 순서"라고 명시. | 배경 |
| 10 | 코드: get_dir 시작점 | `namei.c:228–248`. `root`/`pwd` 존재 검사, 첫 글자가 `/`면 `current->root`, 아니면 `current->pwd`, 빈 문자열은 NULL. `inode->i_count++`(참조 하나 빌림). `get_fs_byte`로 사용자 공간 문자열을 한 글자씩 읽는 이유(4회차 fs 세그먼트). | 코드 |
| 11 | 코드: get_dir 반복 | `namei.c:249–269`. 디렉터리인지·`MAY_EXEC` 권한(`permission`, `40–54`) 검사 → `/`까지 이름 길이 세기 → 문자열 끝이면 현재 inode 반환(마지막 요소는 처리하지 않음) → `find_entry` → `inr`/`idev` 보관 → `brelse(bh)`, `iput(inode)` → `iget(idev, inr)`. 참조 수가 "빌리고 돌려주고 다시 빌리는" 쌍으로 맞춰지는 것을 색으로 표시. | 코드 |
| 12 | 코드: find_entry | `namei.c:91–153`. 이름 길이 14 초과 시 잘림(`104–105`, `NO_TRUNCATE` 미정의), `entries = i_size/16`, `..` 특수 처리(`112–126`: 자기 root에서는 `.`으로, 마운트 지점 root에서는 `s_imount`로 교체), `i_zone[0]`부터 `bread`, 블록 끝나면 `bmap(*dir, i/64)`로 다음 블록(`137–138`), `match`로 비교, 찾으면 **버퍼를 잡은 채** 반환(호출자가 `de->inode`를 읽고 `brelse`). | 코드 |
| 13 | 코드: dir_namei와 namei | `namei.c:278–294`: `get_dir`로 마지막 디렉터리 얻고, 문자열을 다시 훑어 마지막 `/` 뒤를 `basename`, 길이를 `namelen`으로. `namei.c:303–330`: `namelen==0`이면(`/usr/`) 디렉터리 자체 반환, 아니면 `find_entry` → `iget` → `i_atime` 갱신·`i_dirt=1`. 호출처: `do_execve`(`exec.c:199`), `sys_chdir`, `sys_mount`(`super.c:206,214`). | 코드 |
| 14 | 상태 변화도: 경로 탐색 커서 "/etc/rc" | 상태 (dir inode, 남은 문자열, 빌린 참조): `(root#1, "etc/rc", root.i_count+1)` →`find_entry("etc",3)`: `bread(dev, root.i_zone[0])`에서 `dir_entry{inode=k, "etc"}`→ `iput(root)`, `iget(dev,k)` → `(etc#k, "rc", etc.i_count=1)` → 문자열 끝 → `dir_namei` 반환 `(etc#k, basename="rc", namelen=2)` → `find_entry("rc")` → `iput(etc)`, `iget(dev, m)` → `rc#m`. 전환 원인·변경 데이터(`i_count`, 버퍼 `b_count`)·유지 조건(각 단계에서 디렉터리여야 하고 `MAY_EXEC`). 실제 k, m 값은 시연 A에서 채움. | 상태도 |
| 15 | 코드: iget | `inode.c:244–292`. `get_empty_inode`를 **먼저** 확보(잠들 수 있으므로), `inode_table` 선형 탐색(`dev,nr` 일치), `wait_on_inode` 후 재확인, `i_count++`, `i_mount`면 그 슈퍼 블록의 루트(`ROOT_INO`)로 바꿔 다시 탐색(`263–280`), 못 찾으면 `empty`에 `i_dev/i_num` 넣고 `read_inode`. 32개 슬롯뿐임을 강조. | 코드 |
| 16 | 코드: read_inode와 iput | `inode.c:294–312`: `lock_inode`, `get_super`, 블록 산식, `bread`, 32B 복사, `brelse`, `unlock`. `inode.c:150–192` `iput`: pipe 특례, `i_dev==0` 특례, 블록 장치면 `sync_dev`, `i_count>1`이면 감소만, `i_nlinks==0`이면 `truncate`+`free_inode`, `i_dirt`면 `write_inode` 후 `goto repeat`. 10회차 `do_exit`의 `iput` 세 번과 연결. | 코드 |
| 17 | 상태 변화도: m_inode 슬롯 | 상태: 비어 있음 / 읽는 중(`i_lock`) / 상주 / 공유(`i_count≥2`) / 더러움 / 반납 중. 전환 원인: `get_empty_inode:194–226`, `read_inode`, `iget` 적중, `sys_open`·`fork`, `file_write`·`namei:326–327`, `iput`. 변경 데이터: `i_dev/i_num`, `i_count`, `i_lock`, `i_dirt`, 디스크 inode 블록(`write_inode:331–334`가 `b_dirt=1`). 유지 조건: `i_count>0`이면 `get_empty_inode`가 재사용하지 않음. | 상태도 |
| 18 | 코드: bmap — 직접·단일 간접·이중 간접 | `inode.c:72–138`. `block<7` → `i_zone[block]`; `<7+512` → `i_zone[7]`이 가리키는 블록의 `unsigned short[512]`에서 읽음; 그 이상 → `i_zone[8]` → 2단계. 상한 `7+512+512*512`(`79–80`). `create` 인자가 1이면 `new_block`으로 채움(`create_block`, `145–148`). 간접 블록도 `bread`로 읽으므로 버퍼 캐시의 혜택을 받음. | 코드 |
| 19 | 그림: 파일 1개의 블록 지도 | `i_zone[0..6]` 직접 7개(7 KiB), `i_zone[7]` → 512개(512 KiB), `i_zone[8]` → 512×512개. 최대 파일 크기 계산과 `s_max_size`. `file_read`가 `f_pos/1024`를 넣어 디스크 블록을 얻는 화살표. | 배경 |
| 20 | 코드: new_block과 new_inode | `bitmap.c:75–105`: `s_zmap[i]`에서 `find_first_zero`, `set_bit`, `b_dirt=1`(비트맵 버퍼), 블록 번호 = `j + i*8192 + s_firstdatazone - 1`, `getblk` 후 `clear_block`, `b_uptodate=1, b_dirt=1`(디스크를 읽지 않고 0으로 채움). `bitmap.c:136–168`: 같은 방식으로 inode 번호, `i_count=1, i_nlinks=1, i_dirt=1`. | 코드 |
| 21 | 시연 A 계획: namei("/etc/rc") | 중단점 `namei`, `find_entry`, `iget`. 게스트 셸에서 `cat /etc/rc`(또는 부팅 직후 init의 `open("/etc/rc")`를 잡기 위해 `b open_namei` 후 `c`). 관찰: `find_entry` 진입마다 `x/3s name`(fs 세그먼트이므로 `x/s` 대신 `p/c`로 바이트 확인 또는 `namelen`), `p (*dir)->i_num`; 반환 후 `p (*res_dir)->inode`, `p (*res_dir)->name`; `iget` 진입 `p nr`; `namei` 반환값 `p *$`로 `i_num`, `i_size`, `i_zone[0]`. | 시연 |
| 22 | 시연 A 캡처 | GDB 로그: `find_entry` 1회차 `(*dir)->i_num=1`, 찾은 `de->inode=<k>`, `de->name="etc"`; 2회차 `(*dir)->i_num=<k>`, `de->inode=<m>`, `name="rc"`; `namei` 반환 inode `i_num=<m>`, `i_mode=0100644`(예시), `i_size`, `i_zone[0]=<데이터 블록>`. 각주: lab/ QEMU i386 + GDB, 원본 미수정, 루트 이미지에 따라 k·m 값이 다름. 슬라이드 14의 상태도에 이 값을 채워 넣는다. | 캡처 |
| 23 | 코드: open_namei | `namei.c:337–410`. `O_TRUNC`인데 접근 모드 없으면 `O_WRONLY` 강제(`346–347`), `mode`에 umask·`I_REGULAR`, `dir_namei`, `namelen==0`(디렉터리 자체 열기) 특례, 엔트리 없음: `O_CREAT` 아니면 `-ENOENT`, 있으면 `MAY_WRITE` 검사 → `new_inode` → `add_entry` → `de->inode = i_num; bh->b_dirt=1`(`385–386`). 엔트리 있음: `O_EXCL`이면 `-EEXIST`(`396–397`), `iget`, 디렉터리를 쓰기로 열면 `-EPERM`, `permission(inode, ACC_MODE(flag))`, `O_TRUNC`면 `truncate`. | 코드 |
| 24 | 비교: 접근 모드 (범위: O_ACCMODE 값 4가지 전부) | 표. `O_RDONLY`(0) → `MAY_READ`(4); `O_WRONLY`(1) → `MAY_WRITE`(2); `O_RDWR`(2) → 6; `3` → `0377`(모든 비트 요구 → 사실상 거부). 근거 `namei.c:21` `ACC_MODE`와 `permission`(`40–54`)의 `(mode & mask & 7) == mask`. 그리고 `f_mode`가 아닌 `i_mode`가 `f_mode`에 저장되는 0.11 특이점(`open.c:179`). `sys_read:67`의 `f_mode&1`은 pipe 전용. | 비교 |
| 25 | 비교: 나머지 open 플래그 (범위: fcntl.h:11–17 전부) | 표. `O_CREAT`: `open_namei:362`, 없으면 생성. `O_EXCL`: `396`, 있으면 `-EEXIST`(O_CREAT 없이도 검사됨). `O_TRUNC`: `346`, `406–407`. `O_APPEND`: `file_write:60–61, 85`, `fcntl:67–68`. `O_NONBLOCK`/`O_NDELAY`: `fcntl:67–68`이 저장만 하고 어디서도 검사 안 함. `O_NOCTTY`: 어디서도 참조 안 함(`fcntl.h:6` 주석). 각 행에 "커널이 검사함/저장만/무시" 표시. | 비교 |
| 26 | 코드: sys_open | `open.c:138–185`. `filp[]`에서 빈 fd(가장 작은 번호), `close_on_exec` 비트 지움, `file_table`에서 `f_count==0` 슬롯, `filp[fd]=f; f_count++`를 **먼저** 하고 `open_namei` 실패 시 되돌림, tty 특례(major 4/5), 블록 장치면 `check_disk_change`, `f_mode=i_mode, f_flags=flag, f_count=1, f_inode, f_pos=0`. init의 `close(0); open("/etc/rc")`가 fd 0을 받는 이유(`main.c:180–181`). | 코드 |
| 27 | 코드: sys_read / sys_write 분기 | `read_write.c:55–81`, `83–103`. 공통 검사 → `i_pipe` → `S_ISCHR`(→`rw_char`, 13회차) → `S_ISBLK`(→`block_read`) → `S_ISDIR\|\|S_ISREG`(읽기만; `count`를 `i_size`로 자름) → `file_read`. 쓰기는 `S_ISREG`만 `file_write`. `inode->i_zone[0]`이 장치 파일에서는 장치 번호라는 재사용. | 코드 |
| 28 | 비교: 파일 종류별 read/write 경로 (범위: sys_read의 분기 전부) | 표. pipe(`i_pipe`): `read_pipe`/`write_pipe`, `f_mode&1/&2` 검사. 문자 장치: `rw_char(READ/WRITE, i_zone[0], …)`. 블록 장치: `block_read/block_write`(버퍼 캐시 직접). 디렉터리: 읽기만 `file_read`, 쓰기는 `-EINVAL`. 일반 파일: `file_read/file_write`. 그 외: `printk` + `-EINVAL`. 각 행에 소스 줄(`read_write.c:66–80`, `93–102`). | 비교 |
| 29 | 코드: file_read와 file_write | `file_dev.c:17–46`: `bmap(inode, f_pos/1024)` → 0이면 구멍(0으로 채움, `39–42`), 아니면 `bread` → `put_fs_byte` 루프 → `brelse`; `i_atime` 갱신. `file_dev.c:48–90`: `O_APPEND`면 `pos=i_size`, `create_block`(없으면 할당), `bread`(부분 쓰기 때문에 읽음), `b_dirt=1`(`71`), `i_size` 확장, `get_fs_byte` 루프, `i_mtime`. 11회차 `b_dirt`가 1이 되는 바로 그 줄. | 코드 |
| 30 | 시연 B 계획: open_namei와 fd 슬롯 | 중단점 `sys_open`, `open_namei`. 게스트에서 `cat /etc/rc`. 관찰: `sys_open` 진입 `p flag`, `p current->filp[0]@3`(0,1,2는 tty), `open.c:156` 이후 `p fd`, `p f - file_table`; `open_namei` 반환 후 `p inode->i_num`, `p/o inode->i_mode`; `open.c:184`에서 `p *f`(`f_inode`, `f_pos=0`, `f_flags`). | 시연 |
| 31 | 시연 C 계획: file_read → bmap → bread | 중단점 `file_read`, `bmap`, `bread`. 관찰: `file_read` 진입 `p filp->f_pos`, `p count`; `bmap` 반환값(디스크 블록 번호) = 시연 A의 `i_zone[0]`; `bread` 진입 `p block`이 같은 값. 이것이 "문자열 → 블록"의 마지막 고리. | 시연 |
| 32 | 시연 B·C 캡처 | GDB 로그: `fd=3`(셸이 0,1,2를 쓰므로), `f_count=1`, `f_inode->i_num=<m>`; `bmap`의 `$ = <z>`와 `bread`의 `block=<z>`가 일치. 각주: lab/ QEMU, 원본 미수정; `cat`이 `/etc/rc`를 읽기 전에 공유 라이브러리가 없으므로 다른 open은 없음(추론). | 캡처 |
| 33 | 질문의 답: "/etc/rc" → 디스크 블록 | 한 장 요약 체인: 문자열 `/` → `current->root`(inode 1, 부팅 때 `mount_root`) → `root.i_zone[0]` 블록을 `bread` → 64개 `dir_entry` 중 `"etc"` → inode k → `read_inode`가 `2+imap+zmap+(k-1)/32` 블록을 `bread` → `etc.i_zone[0]` 블록에서 `"rc"` → inode m → `read_inode` → `rc.i_zone[0]` = 데이터 블록 z → `file_read`가 `bread(dev, z)`. 디스크 접근은 모두 `bread`를 통해서만, 실제 I/O는 캐시 미스일 때만(11회차). | 정리 |
| 34 | 세 표의 수명 정리 | `filp[fd]`: 태스크 소유, `sys_close`·`do_exit`에서 비움. `file_table[]`: `f_count`로 공유(fork·dup), 0이 되면 `iput`(`open.c:204–206`). `inode_table[]`: `i_count`로 공유, 0이 되면 재사용 후보. 각각 "누가 증가, 누가 감소"를 표로. | 배경 |
| 35 | 현대 커널과의 차이 (짧게) | 고정 32개 inode 표 → 슬랩 캐시 + 해시; `namei` 선형 디렉터리 탐색 → dcache; 14자 이름·16B 엔트리 → 가변 길이; `i_zone[9]` → ext4 extent; VFS 계층(`file_operations`)으로 `sys_read`의 `if` 사다리 대체. 14회차에서 다시. | 배경 |
| 36 | 흔한 오해 | (1) "inode 번호가 블록 번호" — 번호는 inode 표 안의 순번이고 블록은 산식으로 구한다. (2) "디렉터리는 특별한 파일 종류" — `file_read`로 읽을 수 있는 일반 블록 나열이다(`sys_read:72`). (3) "open이 파일 내용을 읽는다" — 디렉터리 블록과 inode 블록만 읽고 데이터 블록은 `read` 때 읽는다. (4) "`f_mode`는 접근 모드" — 0.11은 `i_mode`를 복사해 둔다. | 배경 |
| 37 | 이해 확인 (정답 포함) | 아래 4문항. | 질문 |
| 38 | 정리와 다음 회차 | 오늘 함수 체인(`namei` → `iget` → `read_inode` → `bmap` → `bread`)과 세 표. 다음 13회차: "키보드에서 누른 글자가 read()까지 어떻게 전달되는가?" — 오늘 `sys_read`의 `S_ISCHR` 분기 `rw_char`로 들어간다. | 정리 |

## 강사 시연
**A. namei("/etc/rc") — 디렉터리 엔트리에서 inode 번호까지**
- 환경: `lab/` QEMU i386 + GDB, 원본 미수정. 루트 이미지의 실제 inode 번호는 이미지에 따라 다름.
- 명령: `b find_entry`, `b iget`, `b namei`, `c`. 게스트 셸 `cat /etc/rc`. (`cat`이 `open`을 쓰므로 `namei`가 아닌 `open_namei` 경로로 들어갈 수 있다. 그 경우 `b open_namei`를 추가하고 `dir_namei`→`get_dir`→`find_entry` 흐름은 동일.)
- 관찰: `find_entry` 1회차 `p (*dir)->i_num`=1, `p namelen`=3; `finish` 후 `p *(struct dir_entry *)$`가 아니라 `p **res_dir`가 어려우므로 반환 직전 `namei.c:145`에 중단점을 두고 `p *de`(inode=k, name="etc"). 2회차 `(*dir)->i_num`=k, `namelen`=2, `p *de`(inode=m, name="rc"). `iget` 진입 `p dev`, `p nr`. 마지막 반환 inode `p *inode`(`i_num=m`, `i_size`, `i_zone[0]=z`).
- 기대 출력: 두 번의 `find_entry`, `de->inode` 값 k, m; `i_zone[0]` 값 z.
- 대체: 사전 캡처. 문자열은 fs 세그먼트(사용자 공간)에 있어 GDB `x/s name`이 커널 DS 기준으로 엉뚱한 곳을 가리킬 수 있음 → `namelen`과 `de->name`(커널 버퍼)으로 확인.

**B. open_namei → sys_open의 fd 슬롯**
- 명령: `b sys_open`, `b open.c:184`. 게스트 `cat /etc/rc`.
- 관찰: 진입 `p/o flag`(0 = O_RDONLY), `p current->filp[0]`, `[1]`, `[2]`(tty inode), `open.c:184`에서 `p fd`=3, `p f - file_table`, `p *f`(`f_count=1`, `f_pos=0`, `f_inode->i_num`=m).
- 대체: 사전 캡처.

**C. file_read → bmap → bread 블록 번호 일치**
- 명령: `b file_read`, `b bmap`, `b bread`. 같은 `cat`에서 계속 `c`.
- 관찰: `file_read` 진입 `p filp->f_pos`=0, `p count`; `bmap` `finish` 반환값 z; 이어지는 `bread` `p block`=z, `p dev`=0x306(루트 장치, 이미지 설정에 따라 다름).
- 대체: 사전 캡처. 11회차 시연 A와 같은 로그를 공유해도 됨.

## 이해 확인 질문과 정답
1. **Q.** inode 번호 n의 디스크 inode가 들어 있는 블록 번호는?
   **A.** `2 + s_imap_blocks + s_zmap_blocks + (n-1)/32`, 블록 안 위치는 `(n-1)%32`(`inode.c:303–309`). 1블록 1024B에 32B inode 32개(`fs.h:55`).
2. **Q.** `get_dir("/etc/rc")`가 반환하는 inode는 무엇이며, "rc"는 누가 처리하는가?
   **A.** `etc` 디렉터리의 inode. `get_dir`는 `/`가 더 없으면 현재 inode를 반환한다(`namei.c:257–258`). "rc"는 `dir_namei`가 `basename`으로 잘라(`285–292`) `namei`/`open_namei`의 `find_entry`가 처리한다(`315`, `360`).
3. **Q.** `open(path, O_WRONLY|O_EXCL, 0)`을 **이미 존재하는** 파일에 하면 0.11은 어떻게 되는가?
   **A.** `-EEXIST`. `open_namei`는 엔트리를 찾은 뒤 `O_CREAT` 여부와 무관하게 `flag & O_EXCL`을 검사한다(`namei.c:396–397`). (POSIX와 다른 0.11 동작.)
4. **Q.** `file_read`에서 `bmap`이 0을 반환하면 어떻게 되는가?
   **A.** 디스크를 읽지 않고 그 구간을 0으로 채워 사용자에게 준다(`file_dev.c:28–29`, `39–42`). 파일의 "구멍(hole)". `file_write`는 반대로 `create_block`으로 블록을 새로 할당한다(`65`).

## 처음 등장하는 용어
- **슈퍼 블록(super block)**: 파일 시스템 전체 정보(inode 수, 존 수, 비트맵 크기, 첫 데이터 존, magic). 디스크 블록 1.
- **inode(i-node)**: 파일 하나의 메타데이터와 블록 지도. 이름은 없음. 디스크 형식 `d_inode`, 메모리 형식 `m_inode`.
- **존(zone)**: MINIX 용어로 데이터 블록. 0.11에서 `s_log_zone_size=0`이라 존 = 블록.
- **비트맵(imap/zmap)**: inode와 존의 사용 여부 비트. 슈퍼 블록 바로 뒤에서 시작해 메모리의 `s_imap[]/s_zmap[]` 버퍼에 상주.
- **디렉터리 엔트리(`dir_entry`)**: 16B = inode 번호 2B + 이름 14B. 디렉터리 파일은 이 엔트리의 배열.
- **경로 탐색(path lookup, `namei`)**: 문자열을 구성 요소로 잘라 디렉터리를 차례로 읽어 inode를 얻는 일.
- **직접/간접/이중 간접 블록**: `i_zone[0..6]` / `i_zone[7]` / `i_zone[8]`.
- **파일 구조체(`struct file`)와 fd**: 열린 파일 하나의 위치(`f_pos`)와 플래그; fd는 태스크의 `filp[]` 인덱스.
- **마운트 지점(`i_mount`, `s_imount`)**: 다른 파일 시스템의 루트로 바꿔 타는 inode.
- **구멍(hole)**: `bmap`이 0인 구간. 읽으면 0, 쓰면 할당.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- `f_mode`에 `i_mode`가 저장된다(`open.c:179`). 현대 커널의 `f_mode`(FMODE_READ 등)와 같다고 말하지 않는다. 읽기/쓰기 허용은 `open_namei`의 `permission` 검사 시점에만 확인되며 이후 `sys_read`는 pipe 외에는 모드를 다시 보지 않는다.
- `O_NONBLOCK`과 `O_NOCTTY`는 정의만 있고 커널이 검사하지 않는다(`fcntl.h:6`, 검색 결과 `fcntl.c:67–68` 저장만). "비차단 I/O를 지원한다"고 말하지 않는다.
- `O_EXCL`은 `O_CREAT` 없이도 작동하는 0.11 특이 동작(`namei.c:396`)이다. POSIX 의미로 설명하지 않는다.
- `find_entry`는 버퍼를 잡은 채 반환한다. 호출자가 `brelse`를 잊으면 `b_count`가 새므로, "반환 즉시 해제"라고 말하지 않는다.
- `iget`은 선형 탐색이며 32개뿐이다. 성능 논의 시 "해시"라고 말하지 않는다(버퍼 캐시만 해시).
- 디렉터리 이름 14자 초과는 오류가 아니라 잘림(`NO_TRUNCATE` 미정의, `namei.c:27`, `104–105`). `unistd.h:8`의 `_POSIX_NO_TRUNC` 주석과 모순됨을 사실로만 말한다.
- 시연 캡처의 inode 번호(k, m)와 블록 번호(z)는 lab 루트 이미지의 값이며 다른 이미지에서는 다르다. 상태 변화도에는 기호로 두고 캡처에서만 숫자를 보인다.
- 데이터 블록 "접근"은 모두 `bread`를 통하므로 실제 디스크 I/O 여부는 11회차 규칙을 따른다. "open하면 디스크를 n번 읽는다"는 수치를 단정하지 않는다.

---

# 13. 터미널 I/O

## 핵심 질문
키보드에서 누른 글자가 read()까지 어떻게 전달되는가?

## 학습 목표 (3~5개)
1. 키보드 IRQ1 → `keyboard_interrupt` → 스캔 코드 변환 → `put_queue`(read_q)까지의 인터럽트 경로를 어셈블리 수준에서 설명한다.
2. `tty_struct`의 세 큐(read_q / secondary / write_q)와 head/tail 원형 버퍼 매크로(INC/DEC/EMPTY/FULL/LEFT/CHARS)의 의미를 읽는다.
3. `copy_to_cooked`가 수행하는 정규(canonical) 처리(ICRNL, ERASE/KILL, ECHO, ISIG → `tty_intr`)를 코드로 확인하고, 0.11이 실제로 참조하는 termios 플래그와 선언만 된 플래그를 구분한다.
4. `tty_read`가 `sleep_if_empty`로 잠들고 `wake_up(&secondary.proc_list)`로 깨어나는 상태 변화를 설명한다.
5. `tty_write` → `con_write`로 글자가 VGA 텍스트 메모리에 쓰이는 출력 경로와, `printk`가 같은 경로를 쓴다는 사실을 확인한다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| include/linux/tty.h | 14–34 | `TTY_BUF_SIZE`, `struct tty_queue`, INC/DEC/EMPTY/LEFT/LAST/FULL/CHARS/GETCH/PUTCH 매크로 |
| include/linux/tty.h | 36–43 | INTR_CHAR/QUIT_CHAR/ERASE_CHAR/KILL_CHAR/EOF_CHAR/START/STOP/SUSPEND_CHAR |
| include/linux/tty.h | 45–55 | `struct tty_struct`(termios, pgrp, stopped, write 함수 포인터, 세 큐), `tty_table[]` |
| include/linux/tty.h | 57–63 | `INIT_C_CC` 기본 제어 문자(^C=\003, DEL=\177, ^U=\025, ^D=\004 …) |
| kernel/chr_drv/keyboard.S | 21–30 | `size=1024`, head/tail/proc_list/buf 오프셋(tty_queue 구조와 일치해야 함), `mode`/`leds`/`e0` |
| kernel/chr_drv/keyboard.S | 37–77 | `_keyboard_interrupt`: inb $0x60, e0/e1 처리, `call key_table(,%eax,4)`, 0x61 포트 ack, EOI(0x20), `call _do_tty_interrupt`, iret |
| kernel/chr_drv/keyboard.S | 88–110 | `put_queue`: `_table_list[0]`(콘솔 read_q)에 바이트 저장, head 전진, 가득 차면 폐기, proc_list 태스크 state=0 |
| kernel/chr_drv/keyboard.S | 111–127 | ctrl/alt/unctrl/unalt → `mode` 비트 설정 |
| kernel/chr_drv/keyboard.S | 236–241 | `func_table`(F1 = ESC [ [ A …) |
| kernel/chr_drv/keyboard.S | 245–261 | `key_map`(KBD_FINNISH; config.h:19가 FINNISH 선택) |
| kernel/chr_drv/keyboard.S | 453–484 | `do_self`: key_map/shift_map/alt_map 선택, Ctrl/Caps 변환(−32, −64), `call put_queue` |
| kernel/chr_drv/keyboard.S | 502–509 | `key_table` 앞부분(스캔 코드 → 처리 루틴, 0x1D=ctrl) |
| kernel/chr_drv/keyboard.S | 530–540 | break 코드(≥0x80) 대부분 `none` |
| kernel/chr_drv/tty_io.c | 28–49 | `_L_FLAG/_I_FLAG/_O_FLAG`와 L_CANON, L_ISIG, L_ECHO, L_ECHOCTL, I_CRNL, I_NLCR, I_UCLC, I_NOCR, O_POST, O_NLCR, O_CRNL, O_NLRET, O_LCUC 매크로 |
| kernel/chr_drv/tty_io.c | 51–92 | `tty_table[]` 초기값: 콘솔 iflag=ICRNL, oflag=OPOST\|ONLCR, lflag=ISIG\|ICANON\|ECHO\|ECHOCTL\|ECHOKE; rs1/rs2는 변환 없음, B2400\|CS8 |
| kernel/chr_drv/tty_io.c | 99–103 | `table_list[]`(keyboard.S가 `_table_list`로 참조) |
| kernel/chr_drv/tty_io.c | 105–109 | `tty_init` → rs_init, con_init |
| kernel/chr_drv/tty_io.c | 111–120 | `tty_intr`: pgrp가 같은 모든 task의 `signal`에 마스크 OR |
| kernel/chr_drv/tty_io.c | 122–138 | `sleep_if_empty` / `sleep_if_full`(cli, `interruptible_sleep_on(&queue->proc_list)`) |
| kernel/chr_drv/tty_io.c | 145–228 | `copy_to_cooked`: read_q → secondary, CR/NL 변환, KILL/ERASE/STOP/START, ISIG(INTR/QUIT), `secondary.data++`(줄 수), ECHO → write_q, 끝에 `wake_up(&tty->secondary.proc_list)` |
| kernel/chr_drv/tty_io.c | 230–288 | `tty_read`: VTIME/VMIN, `sleep_if_empty(&tty->secondary)`, `put_fs_byte`, EOF/줄 단위 반환, 시그널 시 `-EINTR` |
| kernel/chr_drv/tty_io.c | 290–326 | `tty_write`: `sleep_if_full(&tty->write_q)`, OPOST/ONLCR(NL→CR NL), `tty->write(tty)`, 남으면 `schedule()` |
| kernel/chr_drv/tty_io.c | 342–345 | `do_tty_interrupt(tty)` → `copy_to_cooked(tty_table+tty)` |
| kernel/chr_drv/console.c | 39–47 | `ORIG_X/Y`, `ORIG_VIDEO_MODE/COLS/EGA_BX`(setup.s가 0x90000에 남긴 값) |
| kernel/chr_drv/console.c | 58–76 | 정적 변수: video_mem_start/end, origin, pos, x, y, state, attr |
| kernel/chr_drv/console.c | 445–500 | `con_write` 앞부분: `CHARS(write_q)`만큼 `GETCH` 후 state 0에서 인쇄 가능 문자를 `movw %ax,(pos)`로 VGA 메모리에 기록, 10/13/ERASE/8/9/7 처리, ESC → state 1 |
| kernel/chr_drv/console.c | 600–616 | `con_write` 끝: `set_cursor()` |
| kernel/chr_drv/console.c | 617–689 | `con_init`: 비디오 종류 판별(0xb0000/0xb8000), `set_trap_gate(0x21,&keyboard_interrupt)`, PIC 마스크 해제(`outb_p(inb_p(0x21)&0xfd,0x21)`), 0x61 포트 키보드 리셋 |
| kernel/chr_drv/serial.c | 53–59 | `rs_write`: 큐가 비어 있지 않으면 UART 송신 인터럽트 활성화(대비용) |
| kernel/chr_drv/tty_ioctl.c | 39–44 | `flush`: head=tail |
| kernel/chr_drv/tty_ioctl.c | 46–54 | `wait_until_sent`/`send_break` = 미구현(빈 함수) |
| kernel/chr_drv/tty_ioctl.c | 56–74 | `get_termios`/`set_termios`(바이트 복사, `change_speed`) |
| kernel/chr_drv/tty_ioctl.c | 115–204 | `tty_ioctl`: MAJOR 5(/dev/tty)는 `current->tty`, TCGETS/TCSETS/TCSETSF/TCFLSH/TIOCGPGRP/TIOCSPGRP/TIOCINQ 구현, 나머지 `-EINVAL` |
| fs/char_dev.c | 16–32 | `rw_ttyx`(minor 지정) / `rw_tty`(`current->tty`, 없으면 `-EPERM`) |
| fs/char_dev.c | 85–104 | `crw_table[]`(MAJOR 4=ttyx, 5=tty), `rw_char` 디스패치 |
| fs/read_write.c | 55–80 | `sys_read`: `S_ISCHR` → `rw_char(READ,inode->i_zone[0],…)` |
| fs/read_write.c | 83–96 | `sys_write`: `S_ISCHR` → `rw_char(WRITE,…)` |
| fs/open.c | 165–170 | open 시 리더 프로세스의 `current->tty` 설정과 `tty_table[].pgrp = current->pgrp` |
| kernel/sched.c | 110–120 | `schedule()` 앞부분: 시그널 받은 TASK_INTERRUPTIBLE을 RUNNING으로 |
| kernel/sched.c | 167–186 | `interruptible_sleep_on` |
| kernel/sched.c | 188–193 | `wake_up` |
| kernel/system_call.s | 101–119 | `ret_from_sys_call`: 사용자 모드 복귀 시 `signal` 비트 검사 → `do_signal` |
| kernel/printk.c | 21–41 | `printk`: vsprintf 후 fs=ds로 바꾸고 `_tty_write(0,…)` 호출 |
| include/termios.h | 83–106, 169–183 | iflag/oflag/lflag 상수(선언된 전체 목록 — 비교 슬라이드용) |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도 ①(데이터)**: 한 글자의 위치 — `[키보드 컨트롤러 0x60] → read_q(raw) → secondary(cooked) → 사용자 버퍼(put_fs_byte)`, 그리고 에코 분기 `→ write_q → VGA 메모리`. 각 전환의 원인(IRQ1 / do_tty_interrupt / tty_read 루프 / con_write), 변경되는 데이터(head, tail, secondary.data, pos/x/y), 유지 조건(FULL이면 폐기, EMPTY면 대기).
- **상태 변화도 ②(태스크)**: read()를 부른 셸 태스크 — `TASK_RUNNING → TASK_INTERRUPTIBLE(secondary.proc_list에 매달림) → TASK_RUNNING`. 전환 원인: `sleep_if_empty` / `wake_up(&secondary.proc_list)` 또는 시그널(`schedule()` 110–120행). 유지 조건: `EMPTY(secondary) || (L_CANON && !secondary.data && LEFT>20)`.
- **모드·선택지 비교 ①**: 범위 = `include/termios.h`에 선언된 c_iflag/c_oflag/c_lflag 플래그 전체. 각 플래그에 대해 `tty_io.c`가 실제로 검사하는지(grep 근거), 콘솔 초기값에 켜져 있는지, 어느 함수에서 쓰이는지.
- **모드·선택지 비교 ②**: 범위 = `tty_ioctl`의 cmd 전체(TCGETS…TIOCSSOFTCAR). 구현/부분 구현/`-EINVAL` 분류.
- **모드·선택지 비교 ③**: 범위 = 0.11 문자 장치 MAJOR 0~7(`crw_table[]`). 핸들러가 있는 것(1, 4, 5)과 NULL.

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–03 | 5 | 핵심 질문, 지도, 12회차 복습(파일 read가 장치 read로 갈라지는 지점) |
| 04–08 | 15 | 배경: 터미널·tty·raw/cooked, 원형 버퍼, tty_struct의 세 큐 |
| 09–15 | 25 | 코드 ①: keyboard_interrupt → key_table → do_self → put_queue, do_tty_interrupt |
| 16–22 | 25 | 코드 ②: copy_to_cooked의 정규 처리, tty_read, sleep/wake, 시그널(^C) |
| 23–26 | 10 | 상태 변화도 2장, 비교 ①(termios 플래그) |
| 27–31 | 20 | 강사 시연 A/B/C(GDB로 키 하나의 여정, ^C → -EINTR, stty 없이 ioctl로 ECHO 끄기) |
| 32–37 | 12 | 출력 경로: tty_write, con_write, printk, con_init, 비교 ②③ |
| 38–40 | 5 | 핵심 질문의 답, 전체 경로 재조립 |
| 41–42 | 3 | 이해 확인, 정리·다음 회차 예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약(2~3문장, 어떤 코드·그림·캡처가 들어가는지) | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 13. 터미널 I/O | 제목과 핵심 질문 "키보드에서 누른 글자가 read()까지 어떻게 전달되는가?". 배경에 QEMU 콘솔에서 `ls` 타이핑 중인 캡처(lab, 수정 없음). | 제목 |
| 02 | 15회차 지도와 오늘의 위치 | 15회차 표에서 13 강조. 11·12(블록 장치·파일 시스템)와 오늘(문자 장치)의 대비, 14(종합)로 이어짐을 화살표로 표시. | 지도 |
| 03 | 12회차에서 남긴 갈림길 | `sys_read`(fs/read_write.c:55–80)에서 `S_ISCHR` 분기가 `rw_char`로 간다는 코드 6줄. 파일 read와 장치 read가 같은 fd 인터페이스를 쓰지만 아래가 다르다는 그림. | 코드 |
| 04 | 터미널이란 무엇인가 | 1991년 PC의 "콘솔" = 키보드 + VGA 텍스트 화면, "rs" = 직렬 포트(0x3f8/0x2f8). 0.11의 tty 3개(tty_table[0..2])를 표로. 현대 가상 터미널·pty는 다루지 않음을 명시. | 배경 |
| 05 | raw와 cooked: 두 번 저장되는 글자 | 키보드가 보내는 것은 글자가 아니라 스캔 코드. 커널이 (1) 스캔 코드 → ASCII, (2) 줄 편집(백스페이스·^U)과 ^C 해석을 한 뒤에야 read()에 준다는 개념도. "cooked"라는 용어를 소개. | 배경 |
| 06 | 원형 버퍼 1024바이트 | `struct tty_queue`(tty.h:16–22)와 INC/EMPTY/LEFT/FULL/CHARS(24–30) 코드. head=쓰는 쪽, tail=읽는 쪽, `& (TTY_BUF_SIZE-1)`로 감는 그림. FULL은 LEFT==0, 즉 한 칸은 항상 비워 둔다는 점. | 코드 |
| 07 | tty_struct의 세 큐 | `struct tty_struct`(tty.h:45–53) 코드. read_q(인터럽트가 씀) / secondary(copy_to_cooked가 씀, tty_read가 읽음) / write_q(tty_write가 씀, con_write가 비움)의 역할 그림. `write` 함수 포인터가 콘솔은 `con_write`, rs는 `rs_write`. | 코드 |
| 08 | 콘솔 tty의 초기 termios | `tty_table[0]`(tty_io.c:51–65) 코드: iflag=ICRNL, oflag=OPOST\|ONLCR, lflag=ISIG\|ICANON\|ECHO\|ECHOCTL\|ECHOKE, `INIT_C_CC`(tty.h:63). rs 두 개는 변환 플래그가 0(66–91). 이 값들이 오늘 모든 분기의 기준. | 코드 |
| 09 | 키보드 인터럽트가 걸리기까지 | `con_init`(console.c:683–684): `set_trap_gate(0x21,&keyboard_interrupt)`와 PIC 마스크 비트1 해제. 4회차 IDT 그림을 재사용하여 IRQ1 → 벡터 0x21 → `_keyboard_interrupt`. | 코드 |
| 10 | keyboard_interrupt 읽기 (1) | keyboard.S:37–53. 레지스터·ds/es 저장, `inb $0x60`으로 스캔 코드, 0xe0/0xe1 접두 처리, `call key_table(,%eax,4)`. 스캔 코드가 함수 테이블 인덱스라는 그림. | 코드 |
| 11 | keyboard_interrupt 읽기 (2) | keyboard.S:54–77. 0x61 포트 bit7 토글(키보드 ack), EOI `outb %al,$0x20`, `pushl $0; call _do_tty_interrupt`, 복원 후 `iret`. 인터럽트 안에서 C 함수(copy_to_cooked)를 호출한다는 점과 tty_io.c:328–341 주석 소개. | 코드 |
| 12 | key_table과 do_self | key_table(502–509) 발췌(0x1D=ctrl, 나머지 do_self)와 break 코드는 `none`(530–540). `do_self`(453–484): mode 비트로 key_map/shift_map/alt_map 선택, Ctrl이면 `subb $64` → 'c'(0x63)가 ^C(0x03)가 되는 계산을 표로. | 코드 |
| 13 | put_queue: read_q에 넣기 | keyboard.S:88–110 전체. `_table_list`(tty_io.c:99–103)의 첫 항목=콘솔 read_q, `buf(%edx,%ecx)`에 저장, `andl $size-1`, tail과 같아지면 폐기(`je 3f`), head 갱신, proc_list가 있으면 state=0. head/tail 오프셋(21–26행)이 tty.h 구조와 손으로 맞춰진 점을 주의 표시. | 코드 |
| 14 | 조합 키와 modifier 상태 | ctrl/alt/unctrl/unalt(111–127)가 `mode` 바이트를 켜고 끔. F1~F12는 `func_table`(236–241)의 ESC [ [ A 4바이트 시퀀스가 put_queue로 들어감. 원본 config.h:19가 `KBD_FINNISH`를 선택함을 각주(lab 수정본 키맵은 확인 필요). | 코드 |
| 15 | do_tty_interrupt → copy_to_cooked | tty_io.c:342–345. 인터럽트 문맥에서 바로 cooked 처리로 넘어가는 호출 순서도: IRQ1 → keyboard_interrupt → put_queue → do_tty_interrupt(0) → copy_to_cooked(&tty_table[0]). 호출 순서도이지 상태도가 아님을 명시. | 코드 |
| 16 | copy_to_cooked (1) 루프와 CR/NL | tty_io.c:145–160. `while(!EMPTY(read_q) && !FULL(secondary))`, `GETCH`, 13→10(ICRNL), IGNCR, INLCR, IUCLC. 콘솔은 ICRNL만 켜져 있으므로 Enter(13)가 10으로 바뀜. | 코드 |
| 17 | copy_to_cooked (2) 줄 편집 | tty_io.c:161–199. ICANON일 때 KILL(^U)은 secondary.head를 줄 시작까지 DEC, ERASE(DEL=127)는 한 칸 DEC, 에코는 write_q에 127을 넣음. STOP/START는 `tty->stopped`만 바꿈(콘솔 출력에서 stopped를 검사하는 곳은 없음 — grep 결과 각주). | 코드 |
| 18 | copy_to_cooked (3) ISIG와 ^C | tty_io.c:200–209와 `tty_intr`(111–120). ^C가 `INTR_CHAR`와 같으면 `tty_intr(tty,INTMASK)` → pgrp가 같은 모든 task의 `signal`에 SIGINT 비트 OR, 글자는 secondary에 넣지 않고 `continue`. 10회차의 `ret_from_sys_call`(system_call.s:101–119) → `do_signal`로 연결. | 코드 |
| 19 | copy_to_cooked (4) 줄 카운트·에코·깨우기 | tty_io.c:210–228. 10 또는 EOF면 `secondary.data++`(완성된 줄 수), ECHO면 write_q에 넣고 `tty->write(tty)` 즉시 호출(제어문자는 ECHOCTL로 ^X 표기), `PUTCH(c,secondary)`, 루프 끝에 `wake_up(&tty->secondary.proc_list)`. | 코드 |
| 20 | tty_read (1) 잠들기 조건 | tty_io.c:230–260. VTIME/VMIN 처리(기본 VMIN=1, VTIME=0 → 그 분기 생략), `current->signal`이면 break, `EMPTY(secondary) || (L_CANON && !data && LEFT>20)`이면 `sleep_if_empty(&secondary)`. 정규 모드에서는 줄이 완성될 때까지 글자가 있어도 안 돌려준다는 점. | 코드 |
| 21 | tty_read (2) 복사와 반환 | tty_io.c:261–288. `GETCH(secondary,c)`, 10/EOF면 `data--`, EOF이고 ICANON이면 즉시 반환(길이 0 가능 → 사용자에겐 EOF), `put_fs_byte(c,b++)`, 정규 모드는 한 줄이라도 읽었으면 break. 시그널로 깨어나 0바이트면 `-EINTR`. | 코드 |
| 22 | sleep_if_empty와 wake_up | tty_io.c:122–128와 sched.c:167–186, 188–193 나란히. `cli()` 후 `while(!signal && EMPTY) interruptible_sleep_on(&proc_list)`. `wake_up`은 proc_list가 가리키는 한 태스크의 state=0. put_queue의 `movl $0,(%ecx)`(keyboard.S:106)도 같은 일을 read_q.proc_list에 하지만 0.11에서 read_q에 잠드는 코드는 없음(grep 근거 각주). | 코드 |
| 23 | 상태 변화도 ①: 글자 한 개의 위치 | 상태: 컨트롤러(0x60) → read_q → secondary → 사용자 버퍼; 분기 write_q → VGA. 전환 원인·변경 데이터(read_q.head / read_q.tail·secondary.head / secondary.tail·secondary.data / pos·x) ·유지 조건(FULL이면 폐기, EMPTY면 대기, FULL(secondary)이면 read_q에 남음). | 상태도 |
| 24 | 상태 변화도 ②: read()를 부른 태스크 | RUNNING → INTERRUPTIBLE(secondary.proc_list=current) → RUNNING. 전환 원인 3가지: wake_up(copy_to_cooked 끝), 시그널 보유 시 schedule()(sched.c:117–119), (VTIME 사용 시) alarm. 5·10회차 상태도와 같은 표기. 유지 조건: 줄 미완성 && 시그널 없음. | 상태도 |
| 25 | 비교 ①: termios 플래그 — 선언 vs 실제 참조 | 범위: include/termios.h 83–106(iflag), 169–183(lflag), oflag 99–106 전체. 표 열: 플래그 / tty_io.c가 검사(매크로 28–49행 + 사용처) / 콘솔 초기값. 참조됨: ICRNL·INLCR·IGNCR·IUCLC, OPOST·ONLCR·OCRNL·ONLRET·OLCUC, ISIG·ICANON·ECHO·ECHOCTL. 매크로만 있고 미사용: ECHOE·ECHOK·ECHOKE(정의 35–38행, 호출 없음). 미참조: IXON·IXOFF·ISTRIP·INPCK·PARMRK·ECHONL·NOFLSH·TOSTOP·IEXTEN 등. "선언됐다 ≠ 동작한다". | 비교 |
| 26 | 비교 ①-보충: c_cc 제어 문자 | tty.h:36–43의 8개 매크로 중 copy_to_cooked가 쓰는 것(INTR, QUIT, ERASE, KILL, EOF, START, STOP)과 선언만 된 것(SUSPEND — grep 결과 사용처 없음). 기본값 `INIT_C_CC` 해석표. | 비교 |
| 27 | 시연 A: 키 하나의 여정 (GDB) | 중단점 `keyboard_interrupt`, `copy_to_cooked`, `tty_read`. 셸 프롬프트에서 'a' 한 번. 각 중단점에서 `p tty_table[0].read_q.head/tail`, `p tty_table[0].secondary.head/tail/data`를 찍어 head가 1 전진 → secondary로 이동 → tty_read는 아직 잠든 채(줄 미완성)임을 기대 출력으로. | 시연 |
| 28 | 시연 A 캡처 | GDB 로그 캡처(lab, 수정 없음, `-S -s`). 각주: `keyboard_interrupt`는 어셈블리 심벌이라 `break`는 되지만 소스 줄 표시가 없음; 심벌 이름의 밑줄 접두 여부는 lab 툴체인 기준으로 확인. | 캡처 |
| 29 | 시연 B: Enter와 깨어남, ^C와 -EINTR | (1) Enter 입력 후 `copy_to_cooked` 끝(227행)에 중단점 → `p tty_table[0].secondary.data`=1, `p task[n]->state`가 0으로. (2) `cat` 실행 후 ^C: `tty_intr`에 중단점, `p task[n]->signal`의 SIGINT 비트, 이어서 `do_signal` 중단점. 기대: cat 종료, 프롬프트 복귀. | 시연 |
| 30 | 시연 B 캡처 | QEMU 화면 + GDB 로그. 코드 추론(시그널이 secondary에 들어가지 않음)과 관찰(cat이 죽고 ^C 글자 자체는 read로 전달되지 않음)을 구분해 표기. | 캡처 |
| 31 | 시연 C: ioctl로 ECHO 끄기 | 작은 사용자 프로그램(TCGETS → `c_lflag &= ~ECHO` → TCSETS → read 1줄 → 복원). tty_ioctl.c:126–133 경로. 기대: 입력이 화면에 안 보이다가 Enter 후 출력. 사전 캡처 대체 가능(stty 바이너리가 lab 루트 FS에 있는지 확인 필요). | 시연 |
| 32 | 출력 경로: write() → tty_write | sys_write(read_write.c:83–96) → rw_char → rw_ttyx → `tty_write`(tty_io.c:290–326). OPOST/ONLCR: '\n' 앞에 13 삽입(cr_flag), `sleep_if_full(&write_q)`, `tty->write(tty)`, 남으면 `schedule()`. | 코드 |
| 33 | con_write: VGA 텍스트 메모리에 쓰기 | console.c:445–470. `CHARS(write_q)`만큼 GETCH, state 0에서 `movw %ax,(pos)`(문자+attr 2바이트), pos+=2, x++, 줄 끝이면 `lf()`. 10→lf, 13→cr, 127→del, 8→백스페이스, 9→탭, 7→sysbeep. 끝에 `set_cursor()`(600–616). ESC 시퀀스 state 1/2는 범위 밖(간단 언급). | 코드 |
| 34 | con_init: 화면 종류와 인터럽트 등록 | console.c:617–689. setup.s가 0x90000에 남긴 ORIG_* (39–47)로 MDA/CGA/EGA 판별 → video_mem_start 0xb0000/0xb8000, 우상단에 "EGAc" 같은 표시 문자열, `gotoxy(ORIG_X,ORIG_Y)`, 키보드 게이트·PIC·0x61 리셋. 3회차 부팅 캡처의 우상단 문자열과 연결. | 코드 |
| 35 | printk도 같은 길 | printk.c:21–41: vsprintf 후 `push %fs; push %ds; pop %fs`로 fs를 커널 데이터로 바꾸고 `_tty_write(0, buf, i)` 호출. 15회차에서 printk를 쓸 때 "tty_write는 잠들 수 있다"(sleep_if_full)는 주의의 근거. | 코드 |
| 36 | 비교 ②: tty_ioctl의 명령 | 범위: tty_ioctl.c:125–203의 모든 case. 구현(TCGETS/TCSETS/TCSETSW/TCSETSF, TCGETA/TCSETA*, TCFLSH, TIOCGPGRP/TIOCSPGRP, TIOCOUTQ, TIOCINQ), 부분(TCSBRK — wait_until_sent/send_break가 빈 함수 46–54), 미구현 `-EINVAL`(TCXONC, TIOCEXCL/NXCL, TIOCSCTTY, TIOCSTI, TIOCGWINSZ/SWINSZ, TIOCM*, TIOCG/SSOFTCAR). | 비교 |
| 37 | 비교 ③: 문자 장치 MAJOR 0~7 | 범위: char_dev.c:85–93 `crw_table[]`. 1=rw_memory(그 안에서도 ram/mem/kmem은 -EIO, 3=null, 4=port만 동작), 4=rw_ttyx, 5=rw_tty(current->tty 없으면 -EPERM); 0,2,3,6,7은 NULL → `-ENODEV`. open.c:165–170의 리더 tty 결속도 함께. | 비교 |
| 38 | rs 콘솔과의 차이(짧게) | serial.c:53–59 `rs_write`는 큐에 글자가 있으면 UART 인터럽트만 켬(비동기). con_write는 호출 즉시 다 그림(동기). 같은 tty_write가 `tty->write` 포인터 하나로 두 장치를 다룬다는 점만 짚음. rs_io.s 상세는 범위 밖. | 배경 |
| 39 | 핵심 질문의 답 | 전체 경로를 한 장에: IRQ1 → keyboard_interrupt → key_table/do_self → put_queue(read_q.head++) → do_tty_interrupt → copy_to_cooked(secondary.head++, data++, echo→write_q→con_write) → wake_up → tty_read(secondary.tail++, put_fs_byte) → sys_read 반환. 각 화살표에 파일:줄. | 정리 |
| 40 | 오늘 만난 "0.11다운" 선택들 | 큐 오프셋을 어셈블리에 수동 기입(keyboard.S:21–26), 인터럽트 안에서 copy_to_cooked 직접 호출, wake_up은 태스크 하나만, 가득 차면 조용히 폐기(put_queue), ECHOE/ECHOK 매크로 미사용. 14회차 현대 커널 비교 예고. | 정리 |
| 41 | 이해 확인 | 아래 "이해 확인 질문과 정답" 4문항. 정답은 클릭 후 표시. | 질문 |
| 42 | 정리와 다음 회차 | 세 큐·두 상태도·플래그 표 요약. 14회차: `ls /` 한 줄이 1~13회차 전부를 지나가는 지도. 오늘의 tty_read/tty_write가 그 지도의 시작과 끝. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
- **A. 키 하나의 여정**
  - 명령: `scripts/run.sh`(QEMU `-S -s`) 후 GDB에서 `target remote :1234`, `b keyboard_interrupt`, `b copy_to_cooked`, `b tty_read`, `c`. 셸 프롬프트가 뜨면 QEMU 창에서 'a' 한 번.
  - 관찰: 첫 중단(keyboard_interrupt)에서 `p tty_table[0].read_q.head`, `p tty_table[0].read_q.tail`; `finish` 대신 `b put_queue` 추가 후 `p/x $al`(스캔 코드 0x1E) → put_queue 통과 뒤 `read_q.head`가 +1; copy_to_cooked 중단 → `n`으로 루프 한 바퀴 뒤 `p tty_table[0].secondary.head`, `p tty_table[0].secondary.data`(0 유지), `p tty_table[0].write_q.head`(에코로 +1); tty_read 중단점은 셸이 이미 잠들어 있어 이번에는 안 걸리고, Enter 후에 `tty_read` 루프 재진입(258–259행 `sleep_if_empty`·`continue` 이후)에서 걸림.
  - 기대 출력: head 값이 각 단계에서 정확히 1씩 전진, data는 Enter 전 0 / 후 1.
  - 대체: 사전 캡처 `build/gdb-13-keystroke.txt`(기존 기록으로 표시). 주의: 키 입력은 QEMU 창 포커스 필요; GDB가 멈춘 동안 누른 키의 break 코드가 뒤늦게 도착해 keyboard_interrupt가 두 번 걸림(두 번째는 `none`).
- **B. ^C → SIGINT → -EINTR**
  - 명령: 셸에서 `cat` 실행(stdin 대기). GDB `b tty_intr`, `b do_signal`. QEMU 창에서 Ctrl-C.
  - 관찰: `tty_intr`에서 `p tty->pgrp`, `p mask`(INTMASK=1<<1=2), 이후 `p task[2]->signal`(cat의 task 번호는 `p current->pid`로 확인) 비트1; `do_signal`에서 `p signr`=2. 이어서 cat이 종료되고 셸이 프롬프트를 다시 그림.
  - 기대 출력: `cat` 종료, 셸 프롬프트. secondary에는 ^C가 들어가지 않음(`p tty_table[0].secondary.head`가 변하지 않음).
  - 대체: 사전 캡처 `build/gdb-13-sigint.txt`. cat이 lab 루트 FS에 없으면 `sh`의 read 대기(빈 프롬프트)에 대해 같은 절차.
- **C. ioctl(TCSETS)로 ECHO 끄기**
  - 명령: lab 게스트 안에서 컴파일 가능한 환경이면 20줄짜리 C 프로그램(tcgetattr 대신 `ioctl(0,TCGETS,&t)`), 아니면 사전 빌드 바이너리를 루트 FS에 넣어 실행.
  - 관찰: 입력 중 화면에 글자가 안 나타남 → Enter → 프로그램이 읽은 줄을 출력 → 복원 후 다시 에코됨. GDB는 `b set_termios`에서 `p/x tty->termios.c_lflag` 전후 비교.
  - 기대 출력: c_lflag 0xa0b(ISIG|ICANON|ECHO|ECHOCTL|ECHOKE = 01|02|010|01000|04000 = 0xa0b) → ECHO 비트(010) 꺼진 0xa03.
  - 대체: 사전 캡처 `build/qemu-13-noecho.png`. 게스트에 컴파일러가 없고 바이너리 투입 절차가 준비되지 않았으면 코드 설명만.

## 이해 확인 질문과 정답
1. **Q.** 'a' 키를 눌렀다 뗐다. `keyboard_interrupt`는 몇 번 실행되고, `read_q.head`는 몇 번 전진하는가? **A.** 두 번(make 0x1E, break 0x9E). head는 한 번만 전진 — break 코드의 key_table 항목은 `none`(keyboard.S:530–540)이라 put_queue를 부르지 않는다.
2. **Q.** 정규 모드에서 "ab"까지 치고 Enter를 아직 안 눌렀다. `read()`는 2바이트를 돌려주는가? **A.** 아니다. tty_read(256–257행)는 `L_CANON && !secondary.data && LEFT>20`이면 `sleep_if_empty`로 다시 잠든다. secondary.data는 10 또는 EOF가 들어올 때만 증가(210–211행).
3. **Q.** ^C를 누르면 'c'(0x03)는 secondary에 들어가는가? 그 글자를 read()가 받는가? **A.** 들어가지 않는다. ISIG가 켜져 있으면 copy_to_cooked(200–204행)가 `tty_intr`만 호출하고 `continue`한다. read 중이던 태스크는 시그널 때문에 깨어나(sched.c:117–119) 0바이트면 `-EINTR`(tty_io.c:285–286)을 돌려받는다.
4. **Q.** `termios.h`에 `ECHOE`가 있고 tty_io.c:35에 `L_ECHOE` 매크로도 있다. ECHOE를 끄면 백스페이스 에코가 달라지는가? **A.** 달라지지 않는다. `L_ECHOE`는 정의만 되고 어디서도 호출되지 않는다(grep). ERASE 에코는 `L_ECHO`만 본다(182–187행).

## 처음 등장하는 용어
- 스캔 코드(scan code): 키보드 컨트롤러가 키 하나의 누름(make)/뗌(break)에 대해 보내는 1바이트 코드. 글자 코드가 아니다.
- raw / cooked(정규, canonical) 모드: 줄 편집·제어 문자 해석을 커널이 하는지(ICANON) 여부.
- termios / c_iflag·c_oflag·c_lflag·c_cc: 터미널 동작을 정하는 플래그 묶음과 제어 문자 배열.
- 원형 버퍼(ring buffer)와 head/tail: 고정 크기 배열을 끝에서 처음으로 감아 쓰는 큐.
- 에코(echo): 입력 글자를 커널이 화면에 되돌려 그리는 것. 셸이 하는 일이 아니다.
- pgrp / 전경 프로세스 그룹: 같은 tty에 묶인 태스크 집합. `tty_intr`가 시그널을 보내는 범위.
- VGA 텍스트 메모리(0xb8000): 문자·속성 2바이트씩 80×25로 배열된 화면 메모리.
- EOI(End Of Interrupt): PIC에 처리 완료를 알리는 `outb 0x20, 0x20`.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- "키보드 인터럽트가 read()를 직접 깨운다"고 말하지 않는다. 깨우는 것은 `copy_to_cooked` 끝의 `wake_up(&secondary.proc_list)`이며, put_queue의 state=0(106행)은 read_q.proc_list에 대한 것으로 0.11에서는 사용되지 않는 경로다.
- "wake_up은 기다리는 모든 태스크를 깨운다"고 말하지 않는다. 0.11의 wake_up은 proc_list가 가리키는 태스크 하나의 state만 0으로 만들고, 나머지는 interruptible_sleep_on의 `goto repeat`(sched.c:176–179) 연쇄로 깨어난다.
- termios.h의 플래그 목록을 "0.11이 지원하는 기능 목록"으로 소개하지 않는다. 비교 슬라이드 25의 표가 기준이다.
- 콘솔 출력이 인터럽트 기반이라고 말하지 않는다. con_write는 호출 즉시 VGA 메모리에 동기로 쓴다. 인터럽트 기반인 것은 rs(serial.c:53–59)뿐이다.
- `tty->stopped`(^S/^Q)가 콘솔 출력을 실제로 멈춘다고 말하지 않는다. 값만 바뀌고 읽는 곳이 어디에도 없다(grep `stopped` 결과: tty_io.c:60 초기값, 192·196 대입뿐).
- 원본은 KBD_FINNISH 키맵(config.h:19)이라, US 키보드 기준 기호 위치 설명과 다를 수 있다. lab 수정본의 키맵 설정을 먼저 확인하고 말한다.
- 현대 리눅스의 line discipline, pty, 가상 콘솔 전환은 14회차 비교에서 개념만 언급하고 오늘은 다루지 않는다.

---

# 14. 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교

## 핵심 질문
`ls /` 한 줄에 지금까지 배운 것이 어떻게 모두 등장하는가?

## 학습 목표 (3~5개)
1. 셸 프롬프트에서 `ls /`를 치고 결과가 화면에 나오기까지의 전체 경로를 **하나의 지도**로 그리고, 각 구간을 담당한 회차(04~13)와 핵심 함수(파일:줄)를 말한다.
2. 그 경로에서 태스크 상태(RUNNING/INTERRUPTIBLE/UNINTERRUPTIBLE/ZOMBIE)가 바뀌는 지점과 원인을 짚는다 — 셸의 read 대기, 자식의 디스크 대기, 부모의 wait 대기.
3. 시스템 콜 진입(`int $0x80`)·하드웨어 인터럽트(IRQ0/IRQ1/IRQ14)·예외(페이지 폴트 14번)가 같은 한 명령 안에서 각각 언제 일어나는지 구분한다.
4. 0.11의 각 메커니즘에 대해 현대 Linux의 개념 수준 대응물을 이름으로 짝지우고, 이 강좌가 다루지 않은 범위를 명확히 안다.
5. 30년 넘게 바뀌지 않은 설계(프로세스 모델, fd, fork/exec/wait, 시그널, 캐시 계층)를 한 문장씩으로 말한다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
새 범위는 없고 이전 회차의 핵심 지점을 "지도의 좌표"로 재인용한다. 모든 줄 번호는 grep/sed로 재확인함.

| 구간 | 회차 | 파일:줄 | 함수/지점 |
|---|---|---|---|
| 키 입력 → 셸 read 반환 | 13 | kernel/chr_drv/keyboard.S:37–77, 88–110 | `keyboard_interrupt`, `put_queue` |
| | 13 | kernel/chr_drv/tty_io.c:145–228, 230–288 | `copy_to_cooked`, `tty_read` |
| | 13 | fs/read_write.c:55–80 | `sys_read` → `rw_char` |
| 시스템 콜 진입/복귀 | 04 | kernel/system_call.s:80–100 | `_system_call`: `cmpl $nr_system_calls-1`, `call _sys_call_table(,%eax,4)`, state/counter 검사 → `reschedule` |
| | 04/10 | kernel/system_call.s:101–119 | `ret_from_sys_call`: 사용자 모드 복귀 시 시그널 → `do_signal` |
| | 04 | kernel/sched.c:409, 411 | `set_intr_gate(0x20,&timer_interrupt)`, `set_system_gate(0x80,&system_call)` |
| 셸 fork | 06 | kernel/system_call.s:208–219 | `_sys_fork`: `find_empty_process` → `copy_process` |
| | 06 | kernel/fork.c:68–133 | `copy_process`: task_struct 복사, `copy_mem`, tss, `p->counter = p->priority`(85), LDT/TSS 설정, `p->state = TASK_RUNNING` |
| | 06/07 | kernel/fork.c:39–66 | `copy_mem`: `nr * 0x4000000`(52), `copy_page_tables` |
| | 07/08 | mm/memory.c:150–189 | `copy_page_tables`: 읽기 전용 공유, `mem_map[this_page]++`(183) |
| exec | 09 | kernel/system_call.s:200–205 | `_sys_execve`: `lea EIP(%esp)` 전달 |
| | 09 | fs/exec.c:182–353 | `do_execve`: namei, a.out 헤더, `free_page_tables`, `change_ldt`(333), `create_tables`(334), `eip[0] = ex.a_entry`(344) |
| 페이지 폴트로 적재 | 08 | mm/page.s:14–32 | `_page_fault` → `do_no_page` / `do_wp_page` |
| | 08 | kernel/traps.c:199 | `set_trap_gate(14,&page_fault)` |
| | 08 | mm/memory.c:365–397 | `do_no_page`: `current->executable`(374), `share_page`(378), `get_free_page`(380), `bmap`(385)+`bread_page`(386), `put_page`(393) |
| | 08 | mm/memory.c:247–259, 221–238 | `do_wp_page` / `un_wp_page`(COW) |
| open("/") | 12 | fs/open.c:138–185 | `sys_open`: filp/file_table 할당, `open_namei` |
| | 12 | fs/namei.c:337–410, 278–294, 228–270, 91–153 | `open_namei`, `dir_namei`, `get_dir`, `find_entry` |
| | 12 | fs/inode.c:244–292, 140–143 | `iget`, `bmap` |
| read(dirfd) | 12 | fs/read_write.c:72–77 | `S_ISDIR || S_ISREG` → `file_read` |
| | 12 | fs/file_dev.c:17–46 | `file_read`: `bmap` → `bread` → 사용자 버퍼로 복사 |
| 버퍼 캐시 | 11 | fs/buffer.c:267–281, 206–251, 183–196, 36–41 | `bread`, `getblk`, `get_hash_table`, `wait_on_buffer`(`sleep_on(&bh->b_wait)`) |
| 블록 요청 → hd | 11 | kernel/blk_drv/ll_rw_blk.c:145–155, 88–143, 64–86; kernel/blk_drv/hd.c:346 `set_intr_gate(0x2E,&hd_interrupt)` | `ll_rw_block`, `make_request`, `add_request`(`(dev->request_fn)()`) |
| | 11 | kernel/blk_drv/hd.c:294–341, 250–267, 180–200 | `do_hd_request`, `read_intr`, `hd_out`(`do_hd = intr_addr`) |
| | 11 | kernel/system_call.s:221–250 | `_hd_interrupt`: EOI(0xA0), `xchgl _do_hd,%edx` 후 호출 |
| | 11 | kernel/blk_drv/blk.h:101–125 | `unlock_buffer`(`wake_up(&bh->b_wait)`, 106), `end_request`(109–125: `unlock_buffer`, `wake_up(&CURRENT->waiting)`) |
| write(1, …) → 화면 | 13 | kernel/chr_drv/tty_io.c:290–326, kernel/chr_drv/console.c:445–500, 600–616 | `tty_write`, `con_write`, `set_cursor` |
| exit / wait | 10 | kernel/exit.c:102–135, 83–100, 142–195 | `do_exit`(`free_page_tables`, `iput`, `tell_father`, `TASK_ZOMBIE`), `tell_father`, `sys_waitpid` |
| 스케줄링 | 05 | kernel/sched.c:104–142, 305–336 | `schedule`(counter 최대 선택, 재계산 137–139), `do_timer`(`--current->counter`, cpl 검사) |
| | 05 | include/linux/sched.h:171–184 | `switch_to`: `ljmp` TSS |
| | 05 | kernel/sched.c:151–165, 167–186, 188–193 | `sleep_on`, `interruptible_sleep_on`, `wake_up` |
| 상수(비교용) | 05/07/11/12 | include/linux/sched.h:4; kernel/fork.c:52; include/linux/fs.h:43–47 | `NR_TASKS 64`, 64MB/태스크, `NR_OPEN 20`, `NR_INODE 32`, `NR_FILE 64`, `NR_HASH 307` |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도(태스크 두 개의 동시 추적)**: 셸(부모)과 ls(자식)의 state를 시간축 하나에 나란히. 셸: RUNNING → INTERRUPTIBLE(tty_read, secondary.proc_list) → RUNNING(Enter) → fork → waitpid로 INTERRUPTIBLE → SIGCHLD/tell_father로 RUNNING → read로 다시 INTERRUPTIBLE. 자식: RUNNING(copy_process) → exec(상태 변화 없음, 주소 공간만 교체) → 페이지 폴트마다 UNINTERRUPTIBLE(bread→wait_on_buffer→sleep_on) ↔ RUNNING(hd_interrupt→end_request→wake_up) → write 중 RUNNING → do_exit로 ZOMBIE → release로 소멸. 각 전환의 원인·변경 데이터(state, counter, signal, b_lock/b_uptodate, exit_code)·유지 조건을 표로.
- **모드·선택지 비교 ①(진입 방식)**: 범위 = `ls /` 한 번 동안 커널에 들어가는 **모든 종류의 진입** — 시스템 콜(0x80, system gate DPL3), 타이머 IRQ0(0x20, intr gate), 키보드 IRQ1(0x21, trap gate), 디스크 IRQ14(0x2E, hd_interrupt), 페이지 폴트 예외(14, trap gate). 열: 게이트 종류 / 등록 위치(파일:줄) / IF 자동 차단 여부 / 스택 전환 여부 / 이 명령에서 발생 시점.
- **모드·선택지 비교 ②(0.11 vs 현대 — 개념 수준)**: 범위 = 이 강좌에서 다룬 0.11 메커니즘 전부(아래 슬라이드 28–34). 열: 0.11 메커니즘(파일:줄) / 현대 Linux 대응 개념 / 바뀐 이유 한 줄 / 이 강좌에서 다룸 여부.

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–03 | 5 | 핵심 질문, 지도, 오늘의 두 부분(전체 경로 / 비교) 안내 |
| 04–06 | 10 | 큰 지도 1판: 9개 구간과 회차 번호, 추적 규칙(상태·진입·데이터) |
| 07–18 | 45 | 지도 구간별 재방문(각 3~4분): 13→06→04→09→08→12→11→13→10→05, 각 구간 코드 5줄과 좌표 |
| 19–21 | 10 | 두 태스크 상태 변화도, 진입 방식 비교 |
| 22–26 | 20 | 강사 시연 A/B(GDB로 `ls /` 한 번 동안 중단점 순서 기록, 페이지 폴트 횟수 세기) |
| 27–34 | 20 | 현대 커널 비교 8장(개념 수준) + 다루지 않은 것 |
| 35–37 | 5 | "바뀌지 않은 것", 핵심 질문의 답 |
| 38–40 | 5 | 이해 확인, 정리·15회차 예고 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약(2~3문장, 어떤 코드·그림·캡처가 들어가는지) | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 14. 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교 | 제목과 핵심 질문. 배경에 QEMU에서 `ls /` 결과 캡처(lab, 수정 없음). | 제목 |
| 02 | 15회차 지도와 오늘의 위치 | 15회차 표에서 14 강조. 오늘은 새 소스가 아니라 04~13의 좌표를 하나의 경로에 꿰는 회차임을 명시. | 지도 |
| 03 | 오늘의 추적 규칙 | 한 명령을 따라가며 세 가지만 기록: (1) 지금 어느 태스크가 RUNNING인가, (2) 커널에 어떻게 들어왔나(시스템 콜/IRQ/예외), (3) 어떤 자료구조가 바뀌었나. 호출 순서도와 상태도를 구분한다는 2회차 약속 재확인. | 배경 |
| 04 | 큰 지도 (1판) | 한 장짜리 지도: 9개 구간 박스를 시계 방향으로 — ① 키 입력·tty_read(13) ② fork(06) ③ exec(09) ④ 페이지 폴트 적재(08) ⑤ open/read "/"(12) ⑥ 버퍼 캐시·hd(11) ⑦ write → 콘솔(13) ⑧ exit/wait(10) ⑨ schedule(05). 테두리 전체에 "int $0x80 진입/복귀(04)"와 "타이머 틱(05)"이 어디서나 끼어듦을 표시. 이후 07–18에서 이 지도의 한 박스씩 확대. | 지도 |
| 05 | 지도를 읽는 법: 세 축 | 같은 지도에 세 종류의 화살표 범례: 실선=함수 호출, 점선=상태 변화(잠듦/깨움), 번개=하드웨어 인터럽트. 타임라인 축(위)에 셸/ls 두 태스크 레인. | 배경 |
| 06 | 전제: lab 환경의 셸과 ls | lab 루트 FS의 `/bin/sh`와 `ls`는 외부 바이너리이며 소스는 이 강좌 범위 밖. 실제 ls는 opendir/stat을 추가로 부르지만 오늘은 최소 경로(open·read·write·exit)만 추적한다고 선언. 셸 내부 동작은 1회차 40장과 같이 "결과에서 추론"으로 표시. | 배경 |
| 07 | ① 키 입력 → 셸의 read가 깨어남 (13) | 지도 박스 ① 확대. keyboard.S:37–53·88–110 → tty_io.c:145–228 → wake_up(227) → tty_read(230–288)가 `put_fs_byte`로 "ls /\n" 5바이트 복사. 셸 상태: INTERRUPTIBLE → RUNNING. 커널 진입 종류: IRQ1(글자마다), 복귀는 sys_read의 ret_from_sys_call. | 코드 |
| 08 | 시스템 콜 테두리 (04) | 지도 테두리 확대. system_call.s:80–100: `cmpl $nr_system_calls-1`, 세그먼트 설정(ds/es=0x10, fs=0x17), `call _sys_call_table(,%eax,4)`, 복귀 전 `state`/`counter` 검사 → `reschedule`. 101–119: 시그널 검사 → do_signal. 오늘 경로에서 이 코드가 최소 6번(read, fork, execve, open, read, write, exit, waitpid…) 실행됨을 표로. | 코드 |
| 09 | ② 셸이 fork한다 (06) | 지도 박스 ②. system_call.s:208–219 → fork.c:68–133. 복사되는 것(task_struct 한 페이지, LDT, TSS, filp 참조 카운트)과 공유되는 것(페이지, 읽기 전용으로 — memory.c:150–189, `mem_map[]++` 183). `p->counter = p->priority`(85). 자식 state=RUNNING. 부모·자식 모두 `int $0x80` 복귀 지점에서 재개(6회차 답). | 코드 |
| 10 | ③ 자식이 exec한다 (09) | 지도 박스 ③. system_call.s:200–205 → exec.c:182–353. 이름 탐색(12회차와 같은 namei), a.out 헤더 읽기(bread 한 번 — 11회차), `free_page_tables`로 fork가 공유한 페이지 반납, `change_ldt`(333), `create_tables`(334), `eip[0] = ex.a_entry`(344). PID 불변, 주소 공간만 교체(9회차 답). 코드 자체는 아직 메모리에 없다는 점 강조. | 코드 |
| 11 | ④ 첫 명령어에서 페이지 폴트 (08) | 지도 박스 ④. iret로 `a_entry`에 가자마자 예외 14 → page.s:14–32 → `do_no_page`(memory.c:365–397): `current->executable`(374) → `bmap`(385) 4블록 → `bread_page`(386) → `put_page`(393). 자식 state: 디스크 대기 동안 UNINTERRUPTIBLE. ls 바이너리 크기에 따라 몇 번 일어나는지는 시연 B에서 센다. | 코드 |
| 12 | ⑤ open("/") (12) | 지도 박스 ⑤. open.c:138–185 → namei.c:337–410 `open_namei` → `dir_namei`(278–294) → `get_dir`(228–270): 경로가 "/"뿐이므로 `current->root`의 inode를 그대로 → `iget`(inode.c:244–292, 캐시 히트면 디스크 접근 없음). `file_table[]` 슬롯과 `filp[3]` 연결. | 코드 |
| 13 | ⑥ read(dirfd) → 디렉터리 블록 (12→11) | 지도 박스 ⑤→⑥. read_write.c:72–77 `S_ISDIR` → `file_read`(file_dev.c:17–46): `bmap`(inode.c:140–143)으로 논리 블록→물리 블록, `bread`(buffer.c:267–281). 디렉터리 엔트리 `struct dir_entry`(fs.h:157–160, 16바이트) 그림. 사용자 공간으로 `put_fs_byte` 루프. | 코드 |
| 14 | ⑥ 버퍼 캐시 히트/미스와 hd (11) | 지도 박스 ⑥ 확대. `getblk`(206–251) → 해시 히트면 끝. 미스면 `ll_rw_block`(ll_rw_blk.c:145–155) → `make_request`(88–143) → `add_request`(64–86, `(dev->request_fn)()`) → `do_hd_request`(hd.c:294–341, `hd_out` 180–200에서 `do_hd=read_intr`) → `wait_on_buffer`(buffer.c:36–41, `sleep_on`) … IRQ14 → `_hd_interrupt`(system_call.s:221–250) → `read_intr`(250–267) → `end_request`(blk.h:109–125) → `unlock_buffer`(101–107, `wake_up(&bh->b_wait)`). 11회차 답: "read()가 디스크에 가는 때 = 캐시 미스일 때만". | 코드 |
| 15 | ⑦ write(1, …) → 화면 (13) | 지도 박스 ⑦. ls가 결과를 write(1, …) → read_write.c:83–96 → `rw_char` → `tty_write`(290–326, ONLCR로 CR 삽입) → `con_write`(console.c:445–500, VGA 메모리에 2바이트씩) → `set_cursor`(600–616). fd 1은 fork로 복사된 셸의 fd(1회차 37–38장의 open/dup). | 코드 |
| 16 | ⑧ exit와 wait (10) | 지도 박스 ⑧. `do_exit`(exit.c:102–135): `free_page_tables`(106–107), `iput`(118–122), `tell_father`(132, 83–100: 부모 signal에 SIGCHLD), `state = TASK_ZOMBIE`, `schedule()`. 셸 쪽: `sys_waitpid`(142–195)가 INTERRUPTIBLE로 자다가 깨어나 `exit_code` 회수 후 `release`(exit.c:19–33). 10회차 답: "부모는 SIGCHLD로 안다". | 코드 |
| 17 | ⑨ 그 사이 schedule은 몇 번? (05) | 지도 박스 ⑨. 경로 중 schedule() 호출 지점 목록: sleep_on/interruptible_sleep_on 안(tty_read·wait_on_buffer·waitpid), do_exit 끝, system_call.s:96–99 `reschedule`(counter==0 또는 state≠0), do_timer(sched.c:332–335, cpl≠0일 때만). `schedule`(104–142) 선택 규칙과 `switch_to`(sched.h:171–184 `ljmp`). 5회차 답과 연결. | 코드 |
| 18 | 큰 지도 (2판: 좌표 기입) | 04장의 지도에 각 박스마다 파일:줄 좌표와 진입 종류(syscall/IRQ/예외)를 채운 완성판. 인쇄용 1장. | 지도 |
| 19 | 상태 변화도: 셸과 ls 두 레인 | 위 "상태 변화도" 범위대로 시간축 하나에 두 태스크. 각 전환에 원인(함수:줄)과 바뀐 필드(state/counter/signal/b_lock/exit_code), 유지 조건(줄 미완성, b_lock==1, 자식 ZOMBIE 없음). ZOMBIE→소멸은 `release`에서 `task[]` 슬롯 NULL. | 상태도 |
| 20 | 비교 ①: 이 한 명령 동안의 커널 진입 다섯 종류 | 표: 0x80 system gate(sched.c:411, DPL3, IF 유지) / IRQ0 0x20 intr gate(409, IF 차단) / IRQ1 0x21 trap gate(console.c:683, IF 유지) / IRQ14 0x2E intr gate(hd.c:346, IF 차단) / 예외 14 trap gate(traps.c:199). 열: 누가 발생시키나, 스택 전환(CPL3→0일 때만 TSS esp0), 오늘 경로에서 발생 시점. | 비교 |
| 21 | 데이터 흐름 한 장 | "ls /\n" 5바이트가 read_q→secondary→셸 버퍼로, "/" 디렉터리 1024바이트 블록이 hd→buffer→ls 버퍼로, 출력 문자열이 ls 버퍼→write_q→0xb8000으로. 복사 횟수와 `get_fs_byte/put_fs_byte`(fs=0x17) 경계를 표시. | 코드 |
| 22 | 시연 A: 중단점 열 개로 한 명령 녹화 | GDB에서 `b sys_fork`, `b do_execve`, `b do_no_page`, `b sys_open`, `b file_read`, `b bread`, `b do_hd_request`, `b con_write`, `b do_exit`, `b sys_waitpid`에 각각 `commands … p current->pid … c end`를 걸어 멈추지 않고 로그만 남김. `ls /` 한 번 입력 후 로그를 지도 순서와 대조. | 시연 |
| 23 | 시연 A 캡처 | GDB 로그 캡처(lab, 수정 없음). 각주: 중단점 순서가 지도 순서와 다른 곳(예: do_no_page가 exec 직후 여러 번, bread가 open 전에 exec 헤더 읽기로 먼저 등장)을 빨간 표시 — 관찰이 추론을 교정한 사례. | 캡처 |
| 24 | 시연 B: 페이지 폴트와 디스크 접근 세기 | `ignore` 카운트 대신 `b do_no_page` / `b do_hd_request`에 `commands silent; set $pf=$pf+1; c; end`로 횟수만 셈. `ls /`를 두 번 실행해 두 번째에는 `do_hd_request` 횟수가 0 또는 크게 줄어드는지(버퍼 캐시 히트) 확인. 기대: do_no_page는 두 번 모두 비슷(exec마다 새 페이지), do_hd_request는 두 번째가 감소. | 시연 |
| 25 | 시연 B 캡처 | 두 번 실행의 카운트 표 캡처. 각주: 정확한 숫자는 ls 바이너리 크기·루트 FS 이미지·QEMU 설정에 따라 다르므로 "경향"만 결론으로. | 캡처 |
| 26 | 관찰이 가르쳐 준 것 | 추론(지도)과 관찰(로그)의 차이 3가지 정리: 순서 역전(exec 헤더 bread), 반복 횟수(폴트는 페이지 단위), 타이머 틱이 아무 데나 끼어듦(do_timer 로그를 함께 켜면 보임). | 정리 |
| 27 | 비교 ②를 읽는 규칙 | "개념 수준" 선언: 현대 커널 소스를 읽지 않았고 VM도 없으므로 이름과 역할만 대응시킨다. 버전 번호·줄 번호·성능 수치는 말하지 않는다. 표의 4열(0.11 메커니즘·파일:줄 / 현대 개념 / 왜 바뀌었나 / 이 강좌에서 다룸 여부). | 배경 |
| 28 | 비교 ②-1: 태스크와 문맥 전환 | `task[64]` 고정 배열(sched.h:4, fork.c:141–143 선형 탐색) ↔ pid 해시·idr 기반 동적 관리. `switch_to`의 TSS `ljmp`(sched.h:171–184) ↔ 소프트웨어 문맥 전환(TSS는 esp0/IO 비트맵용으로만). `counter/priority`(sched.c:137–139) ↔ CFS·EEVDF 같은 가중 공정 스케줄러. 단일 CPU 전제 ↔ 런큐 per-CPU. | 비교 |
| 29 | 비교 ②-2: 주소 공간 | 태스크당 64MB 고정 세그먼트(fork.c:52 `nr*0x4000000`, exec.c:161) ↔ `mm_struct`와 VMA 목록으로 임의 배치. 세그먼트+페이징 2단계 ↔ 평탄 세그먼트, 페이징만(다단계 페이지 테이블). `mem_map[]` 바이트 참조 카운트(memory.c:183, 96–97) ↔ `struct page`와 버디/슬랩 할당기. | 비교 |
| 30 | 비교 ②-3: 페이지 폴트·COW·적재 | `do_no_page`가 실행 파일에서 직접 `bread_page`(memory.c:386) ↔ 페이지 캐시 기반 mmap 매핑과 파일 기반 폴트 처리. `do_wp_page`/`un_wp_page`(247–259, 221–238) ↔ 같은 원리의 COW, 다만 익명 페이지·rmap·THP 등이 붙음. 원리 동일, 자료구조 상이. | 비교 |
| 31 | 비교 ②-4: 파일 시스템과 캐시 | Minix fs 하나가 곧 "파일 시스템 코드"(namei.c, inode.c) ↔ VFS 계층(`inode`/`dentry`/`file` 객체와 연산 테이블) 아래에 여러 fs. `NR_INODE 32`, `NR_FILE 64`, `NR_OPEN 20`(fs.h:43–45) 고정 ↔ 동적 할당과 큰 한도. `buffer_head` 해시(buffer.c:31, NR_HASH 307) 블록 캐시 ↔ 페이지 캐시(buffer_head는 보조). 디렉터리를 read()로 읽음(read_write.c:72–77, getdents 없음 — unistd.h에 readdir 계열 번호 없음) ↔ getdents 계열. | 비교 |
| 32 | 비교 ②-5: 블록 I/O와 인터럽트 | `request[]` 배열과 `do_hd=read_intr` 함수 포인터 콜백(hd.c:190, 262) ↔ 블록 계층(bio/요청 큐/멀티큐)과 드라이버 분리. PIC 8259 + 고정 벡터(0x20/0x21/0x2E) ↔ APIC/IRQ 도메인, 상반부/하반부(softirq·threaded IRQ). 인터럽트 안에서 `copy_to_cooked` 직접 실행 ↔ 지연 처리로 분리. | 비교 |
| 33 | 비교 ②-6: 터미널과 시스템 콜 표 | 콘솔 1 + rs 2 고정(tty_io.c:51–92), con_write가 VGA에 직접 쓰기 ↔ tty 코어 + line discipline + 가상 콘솔/pty/프레임버퍼. `sys_call_table[72]`(sys.h:74–86; system_call.s:61 `nr_system_calls = 72`)와 `int $0x80` ↔ 수백 개 표와 `syscall`/`sysenter` 빠른 진입, 아키텍처별 표. 시그널 비트마스크 32개(`signal`/`blocked` long) ↔ 실시간 시그널·큐잉. | 비교 |
| 34 | 이 강좌가 다루지 않은 것 | 분명히 표시: SMP/락킹/선점, 커널 모듈·sched_ext(15회차 노트 참조), 네트워킹, VFS 실제 코드, ext4 등 현대 fs, 가상 메모리의 스왑(0.11 swap 없음), 보안(권한 검사 일부만), 64비트, 전원 관리, 장치 트리/ACPI, 컨테이너·cgroup·namespace, 현대 부팅(UEFI·initramfs). "0.11이 작아서 생략된 것"과 "강좌 범위라서 생략한 것"을 두 열로 구분. | 비교 |
| 35 | 바뀌지 않은 것 | 한 줄씩: 프로세스 = 주소 공간 + 커널 스택 + 상태; fd 번호로 파일·장치를 같은 read/write로 다룸; fork/exec/wait/exit 네 동작의 분업; 시그널 = 비동기 통지 비트; 캐시 미스일 때만 장치에 감; 잠들기·깨우기는 대기열과 상태 전환; 사용자/커널 경계는 항상 게이트를 통해서만. 각 항목 옆에 오늘 지도에서의 위치 번호. | 정리 |
| 36 | 왜 0.11로 배웠나 (성찰) | 1만 줄 안에 위 7가지가 전부 있고 GDB로 한 명령을 끝까지 쫓을 수 있다는 점. 반대로 0.11의 단순화(단일 CPU, 고정 배열, 동기 콘솔)가 현대 설계 결정의 이유를 보여 준다는 점. 수강생에게 "현대 커널에서 같은 지도를 그린다면 어느 박스가 가장 많이 쪼개질까"를 묻고 넘어감(답: ⑥과 ⑨). | 정리 |
| 37 | 핵심 질문의 답 | 지도 2판을 축소해 다시 보이며 한 문장: "`ls /`는 13→06→04→09→08→12→11→13→10→05 순으로 10개 회차를 지나며, 그 사이 커널 진입은 시스템 콜·IRQ0/1/14·예외 14 다섯 종류가 섞여 일어난다." | 정리 |
| 38 | 이해 확인 | 아래 4문항. 정답은 클릭 후 표시. | 질문 |
| 39 | 정리 | 오늘 만든 지도 2판과 두 레인 상태도, 비교표의 4열 규칙. 수강생이 가져갈 것: 지도 1장(인쇄). | 정리 |
| 40 | 다음 회차 예고 | 15회차: 이 지도의 테두리(sys_call_table)에 항목 하나를 추가하고 박스 ⑨(schedule)의 선택 규칙을 바꾼 뒤 같은 GDB 방법으로 확인. "읽기"에서 "바꾸기"로. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
- **A. 중단점 열 개로 한 명령 녹화**
  - 명령: `scripts/run.sh`로 QEMU `-S -s`, GDB `target remote :1234`. 아래 중단점마다 `commands` / `silent` / `printf "<name> pid=%d\n", current->pid` / `continue` / `end`: `sys_fork`(system_call.s의 `_sys_fork` 심벌명은 lab 툴체인 기준으로 확인), `do_execve`, `do_no_page`, `sys_open`, `file_read`, `bread`, `do_hd_request`, `con_write`, `do_exit`, `sys_waitpid`. `set logging file build/gdb-14-ls.txt`, `set logging on`, `c`. 셸에 `ls /` 입력.
  - 관찰: 로그에 찍힌 이름·pid 순서. 셸 pid와 ls pid가 fork 직후부터 갈라지는 지점, `do_no_page`의 연속 등장, `bread`가 `do_execve` 직후(헤더)와 `file_read` 뒤(디렉터리 블록)에 각각 등장, 마지막에 `do_exit`(자식) → `sys_waitpid` 복귀(부모, 실제로는 셸이 먼저 waitpid에 들어가 있으므로 로그에는 fork 직후에 찍힘).
  - 기대 출력: 지도 순서와 대체로 일치하되 23장에 적은 역전 두 곳이 보임.
  - 대체: 사전 캡처 `build/gdb-14-ls.txt`(기존 기록으로 표시). 심벌 문제로 중단점이 안 걸리면 `info functions sys_fork`로 실제 이름 확인.
- **B. 페이지 폴트·디스크 요청 횟수 세기**
  - 명령: `set $pf=0`, `set $hd=0`; `b do_no_page` → `commands; silent; set $pf=$pf+1; c; end`; `b do_hd_request` → 같은 방식으로 `$hd`. `ls /` 실행 후 Ctrl-C로 GDB 복귀, `p $pf`, `p $hd`, 0으로 리셋 후 두 번째 `ls /`.
  - 관찰: 두 실행의 `$pf`, `$hd`.
  - 기대 출력: `$pf`는 두 번 비슷(exec마다 새 주소 공간), `$hd`는 두 번째가 감소(버퍼 캐시 히트). 정확한 수치는 환경 의존임을 각주.
  - 대체: 사전 캡처 표 `build/gdb-14-counts.txt`. QEMU 디스크 캐시 설정에 따라 호스트 측 캐시는 보이지 않으며, 여기서 세는 것은 게스트 커널의 요청 횟수뿐임을 명시.

## 이해 확인 질문과 정답
1. **Q.** `ls /` 한 번 동안 커널에 들어가는 방법은 몇 종류이고 각각 무엇인가? **A.** 다섯 종류 — `int $0x80` 시스템 콜(sched.c:411), 타이머 IRQ0(409), 키보드 IRQ1(console.c:683), 디스크 IRQ14(hd.c:346), 페이지 폴트 예외 14(traps.c:199).
2. **Q.** exec가 끝난 직후 ls의 코드는 메모리에 있는가? 없다면 언제 들어오는가? **A.** 없다. `do_execve`는 `current->executable`만 바꾸고(exec.c:319–321) 첫 명령어 실행 시 예외 14 → `do_no_page`(memory.c:365–397)가 `bread_page`로 가져온다.
3. **Q.** 두 번째 `ls /`에서 디스크 접근이 줄어드는 이유와, 그래도 페이지 폴트는 줄지 않는 이유는? **A.** 디렉터리 블록·ls 바이너리 블록이 버퍼 캐시(`getblk` 해시 히트, buffer.c:206–251)에 남아 `ll_rw_block`을 안 부르지만, exec는 매번 새 주소 공간을 만들므로 `do_no_page`는 다시 일어난다(폴트 처리 안에서 bread_page가 캐시 히트할 뿐).
4. **Q.** 0.11의 `task[64]`와 TSS `ljmp` 전환을 현대 커널은 무엇으로 바꿨는가(개념 이름만)? **A.** pid 해시/idr 기반 동적 태스크 관리와 소프트웨어 문맥 전환(TSS는 커널 스택 포인터 등 최소 용도로만).

## 처음 등장하는 용어
- 지도의 좌표: 이 강좌에서 "파일:줄"을 가리키는 말. 오늘은 새 코드를 읽지 않고 좌표만 다시 쓴다.
- 상반부/하반부(top/bottom half): 인터럽트 처리기에서 즉시 할 일과 미룰 일의 분리(현대 개념, 이름만).
- VFS / dentry: 여러 파일 시스템을 같은 객체·연산 표로 다루는 계층과 그 경로 이름 캐시(현대 개념, 이름만).
- 페이지 캐시 / struct page: 파일 내용을 페이지 단위로 캐시하는 현대 구조와 물리 페이지 하나의 기술자(이름만).
- VMA / mm_struct: 프로세스 주소 공간을 구간 목록으로 기술하는 현대 구조(이름만).
- EEVDF/CFS: 현대 리눅스의 공정 스케줄러 이름(이름만, 동작 설명 안 함).

## 주의: 흔한 오해 / 말하지 말아야 할 것
- 현대 커널 비교는 **개념 이름의 대응**으로 제한한다. 현대 소스의 파일·줄·버전·수치를 말하지 않는다(VM이 선택되지 않아 검증할 수 없음).
- 시연 로그의 중단점 순서를 "지도가 틀렸다"로 말하지 않는다. 지도는 논리 순서, 로그는 시간 순서이며 23장에 차이의 이유를 적어 둔다.
- `ls`가 open/read/write/exit만 부른다고 단정하지 않는다. 실제 바이너리는 stat·brk 등을 더 부를 수 있고, 오늘은 최소 경로를 추적한다고 06장에서 선언한다.
- 셸이 waitpid로 "자식이 끝날 때까지 폴링한다"고 말하지 않는다. INTERRUPTIBLE로 잠들고 `tell_father`의 시그널로 깨어난다(exit.c:83–100, 142–195).
- "두 번째 실행은 캐시 덕분에 디스크를 전혀 안 읽는다"고 단정하지 않는다. 버퍼 수·다른 접근에 따라 달라지며 시연 B는 경향만 보인다.
- 비교표에서 "현대 커널이 0.11보다 복잡하므로 나쁘다/좋다"는 평가를 하지 않는다. 바뀐 이유 열에는 요구 사항(SMP, 다중 fs, 큰 메모리)만 적는다.
- 15회차 노트와 연결: 원래 계획된 "현대 커널 모듈"·"sched_ext" 회차는 선택되지 않은 현대 커널 VM이 필요하여 15회차의 0.11 수정 실습으로 대체되었다. 오늘 비교 슬라이드(27–34)가 그 두 주제를 개념 수준에서만 대신한다.

---

# 15. 커널 수정 실습: 새 시스템 콜과 스케줄러 변경

## 핵심 질문
커널을 바꾸면 어디서 어떻게 확인하는가?

> **노트(회차 대체 사유)**: 원래 계획에 있던 "현대 커널 모듈"과 "sched_ext" 두 회차는 선택되지 않은 현대 커널 VM이 필요하여 제외했고, 그 자리를 이 회차(0.11을 직접 고치고 QEMU+GDB로 확인하는 실습)로 대체한다. 현대 커널과의 대응은 14회차 비교 슬라이드가 개념 수준에서만 담당한다.

## 학습 목표 (3~5개)
1. 시스템 콜 하나를 추가하기 위해 손대야 하는 **네 곳**(`include/unistd.h`의 `__NR_*`, `include/linux/sys.h`의 `sys_call_table[]`, `kernel/system_call.s`의 `nr_system_calls`, 새 커널 함수)과 사용자 쪽 `_syscallN` 매크로의 관계를 설명한다.
2. `lab/`(실행·수정본)과 `src/`(원본)의 역할 차이를 지키며 `scripts/build.sh` → `scripts/run.sh` → GDB로 변경을 빌드·부팅·검증하는 순서를 수행한다.
3. `schedule()`의 선택 규칙(`counter` 최대값)과 재계산 규칙(`counter/2 + priority`)을 바꾸고, 두 프로세스 테스트와 `printk`/GDB 카운터로 그 효과를 관찰한다.
4. 변경이 "적용되지 않은 것처럼 보이는" 전형적 실패(nr_system_calls 미갱신, 사용자 포인터 직접 역참조, src/ 편집, 옛 심벌 파일)를 증상으로부터 역추적한다.
5. 변경 위치(사용자 프로그램 / 시스템 콜 표 / 커널 함수 / 스케줄러)마다 적합한 검증 수단(프로그램 출력 / errno / printk / GDB 중단점·변수)을 짝지운다.

## 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — 반드시 실제 소스 확인 후 기재)
| 파일 | 줄 | 내용 |
|---|---|---|
| include/unistd.h | 58, 60–131 | `#ifdef __LIBRARY__` 아래 `__NR_setup 0` … `__NR_setregid 71`(마지막 번호 71) |
| include/unistd.h | 133–144 | `_syscall0`: `int $0x80`, eax=`__NR_##name`, 음수면 `errno = -__res; return -1` |
| include/unistd.h | 146–157 | `_syscall1`: 인자 a를 `"b"`(ebx)로 전달 |
| include/unistd.h | 185 | `#endif /* __LIBRARY__ */` |
| include/linux/sys.h | 1–72 | `extern int sys_*();` 선언 목록(마지막 `sys_setregid` 72행) |
| include/linux/sys.h | 74–86 | `fn_ptr sys_call_table[] = { sys_setup, … , sys_setreuid, sys_setregid };` — 순서가 곧 번호 |
| kernel/system_call.s | 48–53 | task_struct 오프셋: `state=0`, `counter=4`, `signal=12`, `blocked=(33*16)` |
| kernel/system_call.s | 61 | `nr_system_calls = 72` |
| kernel/system_call.s | 72–74 | `bad_sys_call`: `movl $-1,%eax; iret` |
| kernel/system_call.s | 80–100 | `_system_call`: `cmpl $nr_system_calls-1,%eax; ja bad_sys_call`, ebx/ecx/edx가 인자, `fs=0x17`, `call _sys_call_table(,%eax,4)`, 복귀 전 state/counter 검사 |
| kernel/sched.c | 348–356 | `sys_getpid`, `sys_getppid` — 가장 작은 시스템 콜의 본보기 |
| kernel/sched.c | 378–383 | `sys_nice`: `priority -= increment`(0보다 클 때만) |
| kernel/sys.c | 16–48 | `-ENOSYS`만 돌려주는 stub들(`sys_ftime`, `sys_break`, `sys_ptrace`, `sys_stty`, `sys_gtty`, `sys_prof`) — 새 함수를 둘 위치의 본보기 |
| kernel/sys.c | 156–166 | `sys_times`: `utime/stime`을 `put_fs_long`으로 사용자에게, 반환값 `jiffies` — 테스트 프로그램의 시계 |
| kernel/Makefile | 27–32 | `OBJS`에 `sys.o`, `sched.o` 포함 → 새 함수를 sys.c에 두면 Makefile 수정 불필요 |
| lib/close.c | 7–10 | `#define __LIBRARY__` + `#include <unistd.h>` + `_syscall1(int,close,int,fd)` — 사용자 래퍼의 표준 형태 |
| init/main.c | 23–24 | `static inline _syscall0(int,fork)` — 커널 안에서도 같은 매크로로 래퍼를 만든 예 |
| kernel/printk.c | 21–41 | `printk`: `tty_write(0,…)` 호출 — 스케줄러 안에서 쓰면 안 되는 이유의 근거(`sleep_if_full`, `schedule()` 가능성: tty_io.c:299, 323) |
| kernel/sched.c | 104–142 | `schedule()`: 시그널 깨우기(110–120), 선택 루프(124–135: `state==TASK_RUNNING && counter > c`), 재계산(136–139: `counter = (counter>>1) + priority`), `switch_to(next)`(141) |
| kernel/sched.c | 305–336 | `do_timer`: `--current->counter`(332), 0이면 cpl≠0일 때만 `schedule()`(334–335) |
| kernel/fork.c | 85 | `p->counter = p->priority` — 새 태스크의 초기 counter |
| include/linux/sched.h | 113–114 | `INIT_TASK`의 `{ 0,15,15, …}` = state 0, counter 15, priority 15 |
| include/linux/sched.h | 4 | `NR_TASKS 64` |
| include/asm/segment.h | (전체) | `get_fs_byte/put_fs_byte/get_fs_long/put_fs_long` — 사용자 포인터를 커널에서 다루는 유일한 방법 |

## 상태 변화도 / 모드·선택지 비교 범위
- **상태 변화도(변경 하나의 생애)**: `미적재(src만 읽음)` → `수정됨(lab/ 파일 편집)` → `빌드됨(scripts/build.sh 성공, 새 Image·심벌 파일)` → `부팅됨(scripts/run.sh, 새 커널이 메모리에)` → `검증됨(기대 출력/GDB 값 일치)`. 전환 원인(편집 / make / QEMU 기동 / 관찰 비교), 변경되는 데이터(lab/ 소스 → 오브젝트·Image·`tools/system` 심벌 → 메모리의 `sys_call_table`·`schedule` 코드 → 로그), 유지 조건(src/는 변하지 않음; 빌드 실패 시 "수정됨"에 머무름; 심벌 파일과 Image가 같은 빌드일 때만 "검증됨"으로 갈 수 있음). 되돌림 전환(`git checkout`/원본 복사)도 표시.
- **모드·선택지 비교 ①(변경 위치)**: 범위 = 오늘 손대는 위치 전부 — 사용자 프로그램, `__NR_*` 번호, `sys_call_table[]`, `nr_system_calls`, 새 커널 함수, `schedule()`. 열: 어느 파일 / 빌드 범위(사용자만 재컴파일? 커널 전체?) / 틀렸을 때 증상 / 검증 수단.
- **모드·선택지 비교 ②(검증 수단)**: 범위 = 이 환경에서 쓸 수 있는 확인 방법 전부 — 사용자 프로그램 출력, 반환값·errno, `printk`, GDB 중단점, GDB 변수 관찰(`p sys_call_table[72]`, `p sched_count`), QEMU 화면 캡처. 열: 무엇을 보여 주나 / 어디서는 쓰면 안 되나(printk in schedule) / 재현성.
- **모드·선택지 비교 ③(스케줄러 정책 선택지)**: 범위 = 오늘 구현 가능한 `schedule()` 변형 — 원본(counter 최대 + 반감 재계산), 우선순위 무시(모두 같은 몫), 라운드 로빈(current 다음 RUNNING 선택), 단순 우선순위 부스트(대기에서 깨어난 태스크 counter 가산). 열: 바꾸는 줄 / 기대되는 두 프로세스 결과 / 위험(기아, 0 counter 루프).

## 120분 운영안 (표: 슬라이드 범위 | 분 | 진행)
| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–03 | 5 | 핵심 질문, 지도, 회차 대체 노트와 오늘의 두 파트 |
| 04–08 | 12 | 배경: lab vs src, build.sh/run.sh, 변경의 생애(상태도), 검증 수단 비교 |
| 09–16 | 25 | Part A 코드: 번호·표·카운트·함수·래퍼 다섯 조각, 사용자 포인터 규칙 |
| 17–21 | 20 | Part A 시연: 편집 → 빌드 → 부팅 → 실행 → GDB 확인, 일부러 nr_system_calls 빼고 재현 |
| 22–27 | 15 | Part B 코드: schedule 선택·재계산 규칙, 변경안 3개 비교, 테스트 프로그램 |
| 28–33 | 25 | Part B 시연: 원본 측정 → 수정 → 재측정, printk/GDB 카운터 |
| 34–38 | 10 | 체크리스트, 흔한 실패와 증상, 변경 위치 비교표 |
| 39–40 | 5 | 핵심 질문의 답, 15회차 전체 되돌아보기 |
| 41–42 | 3 | 이해 확인, 정리·과정 마무리 |

## 슬라이드 계획 (표: 번호 | 제목 | 내용 요약(2~3문장, 어떤 코드·그림·캡처가 들어가는지) | 유형)
| 번호 | 제목 | 내용 요약 | 유형 |
|---|---|---|---|
| 01 | 15. 커널 수정 실습: 새 시스템 콜과 스케줄러 변경 | 제목과 핵심 질문. 배경에 수정 커널이 부팅되어 `hello: pid=…` 출력을 낸 QEMU 캡처(lab 수정본, 사전 캡처). | 제목 |
| 02 | 15회차 지도와 오늘의 위치 | 15회차 표에서 15 강조. 14회차 지도(테두리 = 시스템 콜 표, 박스 ⑨ = schedule) 축소판을 옆에 두고 오늘 손댈 두 지점을 표시. | 지도 |
| 03 | 왜 이 회차인가 | 대체 사유 노트(위 블록) 한 장. "현대 커널 모듈·sched_ext → 0.11 직접 수정"으로 바뀐 이유(현대 커널 VM 미선택)와, 그래도 같은 질문("바꾸면 어디서 확인하나")에 답한다는 점. | 배경 |
| 04 | lab/ 와 src/ 를 다시 구분한다 | 1회차 20장 재사용: src = Kernel.org 원본(읽기·인용 전용), lab = yuan-xy/Linux-0.11 기반 실행본(현대 gcc/gas로 빌드, QEMU i386). 오늘 **편집은 lab/에서만**, 슬라이드 인용 줄 번호는 src/ 기준. 두 트리의 같은 파일 경로 표. | 배경 |
| 05 | build.sh / run.sh / GDB 연결 | `scripts/build.sh`(lab에서 make → `Image`, 심벌 파일 `tools/system`), `scripts/run.sh`(QEMU `-S -s`), GDB `file lab/tools/system; target remote :1234`. 각 단계의 산출물과 "심벌 파일 = 이번 빌드"여야 한다는 조건. 실제 스크립트 내용은 캡처로(확인 필요: 스크립트 옵션 이름). | 배경 |
| 06 | 상태 변화도: 변경 하나의 생애 | 미적재 → 수정됨 → 빌드됨 → 부팅됨 → 검증됨. 각 전환의 원인·데이터·유지 조건(위 범위 설명대로). 빌드 실패·부팅 실패·검증 불일치의 되돌림 화살표. 오늘 두 실습 모두 이 다섯 상태를 두 바퀴 돈다. | 상태도 |
| 07 | 비교 ②: 무엇으로 확인할 것인가 | 검증 수단 6가지 표(범위 설명대로). 핵심 행: `printk`는 `tty_write`(printk.c:21–41)를 부르므로 `schedule()` 안에서는 재진입 위험(tty_io.c:299 `sleep_if_full`, 323 `schedule()`) — 스케줄러 관찰은 GDB 변수가 1순위. | 비교 |
| 08 | 오늘의 두 실습 미리 보기 | Part A: `hello(n)` 시스템 콜 — 커널이 printk로 인사하고 `pid+n`을 돌려줌. Part B: `schedule()`의 재계산 규칙 변경 — nice 준 자식과 안 준 자식의 완주 시간 비교. 각각 "편집 위치 / 빌드 / 확인" 한 줄씩. | 배경 |
| 09 | A-1. 번호: `__NR_hello 72` | unistd.h:60–131 발췌(`__NR_setregid 71`이 마지막)와 추가 줄. `#ifdef __LIBRARY__`(58) 안에 있어야 매크로가 보인다는 점. 번호 = `sys_call_table[]` 인덱스이므로 표 끝에 붙일 것과 일치해야 함. | 코드 |
| 10 | A-2. 표: `sys_call_table[]` 끝에 `sys_hello` | sys.h:72 `extern int sys_setregid();` 뒤에 `extern int sys_hello();`, 86행 `sys_setreuid,sys_setregid };` → `…,sys_setregid, sys_hello };`. 표의 72번째(0부터) 슬롯이 된다는 그림. 선언 빠뜨리면 암시적 선언 경고/오류(현대 gcc 기준, 확인 필요). | 코드 |
| 11 | A-3. 상한: `nr_system_calls = 73` | system_call.s:61과 81–82 `cmpl $nr_system_calls-1,%eax; ja bad_sys_call`. 안 올리면 eax=72가 `bad_sys_call`(72–74)로 가서 `-1`을 돌려주는데, `_syscall1` 매크로는 음수를 `errno=1`(EPERM)로 바꿔 **"권한 없음"처럼 보인다**는 함정 미리 예고. | 코드 |
| 12 | A-4. 함수: `sys_hello` in kernel/sys.c | sys.c:16–48 stub들 옆에 추가: `int sys_hello(long n) { printk("hello: pid=%d n=%ld\n\r", current->pid, n); return current->pid + n; }`. 인자 n은 ebx로 들어와 첫 인자가 되는 구조(system_call.s:86–88 `pushl %edx; pushl %ecx; pushl %ebx`). Makefile:27–28에 sys.o가 이미 있어 빌드 규칙 수정 불필요. | 코드 |
| 13 | A-4′. 사용자 포인터를 받는다면 | 확장안 `sys_hello2(char *buf)`: 커널에서 `*buf`를 직접 읽으면 ds=0x10(커널)이라 엉뚱한 메모리. 반드시 `get_fs_byte/put_fs_byte`(asm/segment.h; sys_times의 `put_fs_long` 156–166이 본보기)와 `verify_area`. 1·2회차의 LDT/세그먼트(fs=0x17) 그림 재사용. 오늘 기본 실습은 정수 인자만 써서 이 문제를 피함. | 코드 |
| 14 | A-5. 사용자 프로그램 `hello.c` | lib/close.c:7–10 형태 그대로: `#define __LIBRARY__`, `#include <unistd.h>`, `#define __NR_hello 72`(게스트 헤더가 옛것이면 직접 정의), `_syscall1(int,hello,long,n)`, `main`에서 `r = hello(100); printf("r=%d errno=%d\n", r, errno);`. 기대: 화면에 커널 printk 한 줄 + `r=pid+100`. | 코드 |
| 15 | 게스트 안에서 컴파일하기 | lab 루트 FS(hdc 이미지)의 gcc 1.40으로 게스트 안에서 `gcc -o hello hello.c` (확인 필요: lab 이미지에 gcc 포함 여부). 대안: 호스트에서 이미지를 마운트해 소스 파일만 넣기(minix fs 마운트 가능 여부 확인 필요). 호스트 현대 gcc로 0.11 a.out 바이너리를 만드는 길은 오늘 범위 밖. | 배경 |
| 16 | 비교 ①: 변경 위치별 빌드 범위와 증상 | 표: 사용자 프로그램(게스트 gcc만 / 컴파일 오류 또는 errno) · `__NR_`(헤더 → lib/init 재컴파일 / `undeclared`) · `sys_call_table`(sys.h → sched.o 등 재컴파일 / 잘못된 함수 호출) · `nr_system_calls`(system_call.o / EPERM처럼 보임) · 새 함수(sys.o / 링크 오류 `undefined sys_hello`) · `schedule()`(sched.o / 동작 변화만, 오류 없음). | 비교 |
| 17 | 시연 A-1: 편집과 빌드 | lab/에서 네 파일 수정(diff 화면), `scripts/build.sh`. 기대: 경고 없이 `Image` 생성, `nm tools/system \| grep sys_hello`로 심벌 확인(심벌 밑줄 접두 여부는 lab 툴체인 기준). 실패 시 대체: 사전 준비된 `lab-hello` 브랜치/디렉터리. | 시연 |
| 18 | 시연 A-2: 부팅과 실행 | `scripts/run.sh`, 게스트에서 `./hello`. 기대 출력: `hello: pid=N n=100` 다음 줄 `r=N+100 errno=0`. 캡처에 "lab 수정본(sys_hello 추가), 2026-xx 빌드" 각주. | 시연 |
| 19 | 시연 A-3: GDB로 표와 진입 확인 | `b sys_hello`, `p sys_call_table[72]`(함수 주소가 sys_hello인지), 중단 시 `p/x $eax`는 이미 호출 후이므로 `b *system_call+N` 대신 `b sys_hello` 진입에서 `p n`, `p current->pid`, `bt`(system_call 프레임이 보이는지). 기대: `n = 100`. | 시연 |
| 20 | 시연 A-4: 일부러 깨뜨리기 | `nr_system_calls`를 72로 되돌려 재빌드·재부팅 → `./hello` 출력 `r=-1 errno=1`. GDB `b bad_sys_call`이 걸림. 다시 73으로 고쳐 복구. 증상→원인 역추적 연습. 시간 없으면 사전 캡처로 대체. | 시연 |
| 21 | 시연 A 캡처 모음 | 빌드 로그 / 게스트 출력 / GDB `p sys_call_table[72]` / 깨뜨린 경우의 `errno=1` 네 캡처. 모두 lab 수정본임을 각주. | 캡처 |
| 22 | B-1. 원본 schedule()을 다시 읽는다 | sched.c:124–135 선택 루프(RUNNING 중 counter 최대), 136–139 재계산(`(counter>>1)+priority`, RUNNING 아닌 태스크도 포함 → 잠든 태스크가 깨어나면 유리), 141 `switch_to`. do_timer 332–335(counter가 0이 되면 사용자 모드일 때만 schedule). fork.c:85(초기 counter=priority), INIT_TASK 15/15. | 코드 |
| 23 | B-2. nice가 바꾸는 것 | sched.c:378–383 `sys_nice`: `priority -= increment`(결과가 0보다 클 때만). 자식 B가 `nice(10)` → priority 5. 재계산 후 A는 counter≈15+…, B는 ≈5+… → A가 약 3배 자주 뽑힘(코드 추론, 측정으로 확인 예정). | 코드 |
| 24 | 비교 ③: 오늘 가능한 정책 변형 | 표: ① 원본 / ② 우선순위 무시(`counter = 15` 또는 `(counter>>1)+15`로 고정 — 두 자식이 같은 몫) / ③ 라운드 로빈(선택 루프를 "current 인덱스 다음부터 첫 RUNNING"으로, counter 조건 제거 — 단 재계산 루프 `if (c) break`와 충돌 주의) / ④ 깨어난 태스크 부스트(wake_up 시 counter += k). 열: 바꾸는 줄 / 두 프로세스 기대 결과 / 위험. 오늘 구현: ②(가장 작은 diff, 효과가 확실). | 비교 |
| 25 | B-3. 변경 diff | sched.c:136–139의 `(*p)->priority` 부분을 상수 `15`로(또는 `#define SCHED_FLAT`로 토글). 3줄 diff. 선택 루프는 그대로 두므로 "counter 최대" 규칙 자체는 유지 — 바뀌는 것은 counter가 다시 채워지는 양뿐. | 코드 |
| 26 | B-4. 두 프로세스 테스트 `sched2.c` | 부모가 `fork` 두 번; 자식 A는 그대로, 자식 B는 `nice(10)`; 각자 같은 길이의 빈 루프(수천만 회, 게스트 속도에 맞춰 조정)를 돌고 `times(&t)`(sys.c:156–166, 반환값 jiffies)로 시작·끝 jiffies를 찍어 `A: start=… end=…` 출력 후 `_exit`. 부모는 `wait` 두 번. 비교 지표: 두 자식의 끝 jiffies 차이. | 코드 |
| 27 | B-5. 관찰 장치 두 가지 | (a) GDB 카운터: sched.c에 `long sched_pick[NR_TASKS];` 추가, `switch_to(next)` 직전 `sched_pick[next]++` — printk 없이 GDB `p sched_pick`로 읽음(1순위). (b) printk: `if (next != last_next) printk("[%d]", task[next]->pid)`처럼 **전환될 때만, 짧게** — 재진입 위험(7장)을 알고 쓰는 2순위. | 코드 |
| 28 | 시연 B-1: 원본 커널에서 측정 | 수정 전 lab(A의 sys_hello는 유지)로 부팅, `./sched2`. 기대: A의 end jiffies가 B보다 훨씬 작음(A 먼저 완주). GDB `p sched_pick`에서 A 인덱스 값이 B의 약 3배(환경 의존, 경향만). | 시연 |
| 29 | 시연 B-2: 수정 후 재측정 | 25장 diff 적용 → `build.sh` → `run.sh` → `./sched2`. 기대: 두 자식의 end jiffies가 비슷, `sched_pick` 두 값이 비슷. 캡처 각주에 "lab 수정본(sched flat), 같은 루프 길이". | 시연 |
| 30 | 시연 B-3: GDB로 재계산 순간 보기 | `b sched.c:137`(재계산 루프) 조건 `if c==0`(실제 줄은 lab 기준) → `p task[2]->counter`, `p task[3]->counter`, `p task[2]->priority`, `p task[3]->priority` 재계산 전후. 원본은 15/5 차이가 counter에 반영, 수정본은 같은 값. | 시연 |
| 31 | 시연 B 캡처 모음 | 원본/수정본의 `sched2` 출력 두 장 + `p sched_pick` 두 장 + 재계산 GDB 로그. 관찰값과 23장의 "약 3배" 추론을 나란히 놓고 차이를 말함. | 캡처 |
| 32 | printk를 schedule에 넣었더니 | (선택) 27장 (b)를 켜고 돌린 화면: 출력은 나오지만 write_q가 차면 `sleep_if_full`→`schedule()` 재귀 가능. 실제로 깨졌다면 그 캡처, 안 깨졌다면 "운이 좋았다"고 말하고 코드 근거(tty_io.c:299–301, 321–323)를 보임. | 캡처 |
| 33 | 상태 변화도 다시: 두 실습이 지난 길 | 6장 상태도 위에 A와 B의 실제 전이 기록(A-4의 "깨뜨리기"는 검증됨→수정됨 되돌림 화살표). | 상태도 |
| 34 | 재빌드·검증 체크리스트 | 편집 전: `src/`가 아닌 `lab/`인가(경로 확인). 편집 후: 네 곳 번호 일치(`__NR_`=표 인덱스=`nr_system_calls-1`). 빌드: build.sh 종료 코드, 경고 중 `implicit declaration`. 부팅: run.sh의 Image가 방금 것인가(타임스탬프). GDB: `file`이 방금 `tools/system`인가(`info files`, 중단점이 "pending"이면 심벌 불일치). 검증: 기대 출력과 실제 출력을 슬라이드에 나란히. | 정리 |
| 35 | 흔한 실패 ①: 시스템 콜 쪽 | 증상→원인 표: `errno=1`, `r=-1` → nr_system_calls 미갱신(bad_sys_call); 컴파일 `__NR_hello undeclared` → `__LIBRARY__` 누락 또는 게스트 헤더 옛것; 링크 `undefined reference sys_hello` → 함수 파일이 OBJS에 없거나 이름 불일치; 쓰레기 값/페이지 폴트 → 사용자 포인터 직접 역참조(13장); 출력 없음 → src/를 고침. | 정리 |
| 36 | 흔한 실패 ②: 빌드·도구 쪽 | 중단점이 안 걸림 → 옛 `tools/system`을 GDB에 로드; `_sys_call_table` vs `sys_call_table` → src(옛 gas, 밑줄 접두)와 lab(현대 gas) 심벌 차이(확인 필요); 수정했는데 그대로 → run.sh가 다른 Image 경로를 봄; 부팅 멈춤 → `nr_system_calls`를 표 길이보다 크게 해 NULL 호출(표 밖 메모리). | 정리 |
| 37 | 비교 ①(완성): 변경 위치 × 검증 수단 | 16장 표에 검증 수단 열을 채운 완성판: 사용자 프로그램→출력·errno; 번호/표/카운트→GDB `p sys_call_table[72]`·`b bad_sys_call`; 커널 함수→printk·`b sys_hello`; 스케줄러→`sched_pick`·jiffies 비교·재계산 중단점. "어디를 바꿨느냐가 어떻게 확인할지를 정한다". | 비교 |
| 38 | 변경을 되돌리고 남기는 법 | lab/에서 diff를 저장(`git diff > build/15-hello.patch` 등), 원본 상태로 복구, 다음 학기에 재적용 가능하게. src/는 처음부터 끝까지 손대지 않았음을 `diff -r`로 확인하는 캡처. | 정리 |
| 39 | 핵심 질문의 답 | "커널을 바꾸면 (1) 변경이 사는 자리에 따라 빌드 범위가 다르고, (2) 그 자리에 맞는 수단 — 사용자 출력/errno, printk, GDB 표·변수·중단점 — 으로, (3) 같은 빌드의 심벌 파일을 들고, (4) 수정 전과 후를 나란히 놓고 확인한다." 상태도 다섯 상태 재등장. | 정리 |
| 40 | 15회차 되돌아보기 | 1회차 "셸이 나오기 전에 누가 실행되는가"부터 오늘 "바꾸면 어디서 확인하는가"까지 핵심 질문 15개를 한 줄씩. 14회차 지도 위에 오늘 수정한 두 지점 표시. | 지도 |
| 41 | 이해 확인 | 아래 4문항. 정답은 클릭 후 표시. | 질문 |
| 42 | 정리와 과정 마무리 | 오늘 산출물(패치 2개, 캡처), 더 해 볼 것(사용자 포인터 받는 시스템 콜, 라운드 로빈 변형, wake_up 부스트)과 각각의 검증 수단. 자료는 PPTX 1개뿐임을 상기. | 정리 |

## 강사 시연 (A/B…: 명령, GDB 중단점, 관찰 대상, 기대 출력, 대체 자료)
- **A. 새 시스템 콜 `hello(n)`**
  - 명령: lab/에서 (1) `include/unistd.h`에 `#define __NR_hello 72`(71 다음, `#ifdef __LIBRARY__` 안), (2) `include/linux/sys.h`에 `extern int sys_hello();`와 표 끝 `, sys_hello`, (3) `kernel/system_call.s` `nr_system_calls = 73`, (4) `kernel/sys.c`에 `sys_hello` 추가. `scripts/build.sh` → `scripts/run.sh`. 게스트에서 `hello.c` 작성·컴파일(게스트 gcc 사용 — 확인 필요) → `./hello`.
  - GDB 중단점: `b sys_hello`, `b bad_sys_call`(깨뜨리기 단계).
  - 관찰: `p sys_call_table[72]`, 중단 시 `p n`, `p current->pid`, `bt`; 깨뜨린 경우 `bad_sys_call` 중단과 게스트 `errno=1`.
  - 기대 출력: `hello: pid=N n=100` / `r=N+100 errno=0`; 깨뜨린 경우 `r=-1 errno=1`.
  - 대체: 사전 준비 디렉터리 `lab-hello/`와 캡처 `build/15-hello-ok.png`, `build/15-hello-eperm.png`, `build/gdb-15-hello.txt`(기존 기록으로 표시).
- **B. 스케줄러 재계산 규칙 변경**
  - 명령: (측정 1) A가 적용된 커널에서 `./sched2` 실행, GDB `p sched_pick`(사전에 27장 (a) 카운터를 추가한 빌드 사용). (수정) `kernel/sched.c` 재계산 식의 `priority`를 `15`로. `build.sh` → `run.sh`. (측정 2) `./sched2`, `p sched_pick`.
  - GDB 중단점: `b sched.c:<재계산 줄, lab 기준>`(원본 137행 근처) 조건부, `b sys_nice`(B가 priority 5가 되는지 `p current->priority`).
  - 관찰: 두 자식의 `end` jiffies 차이; `sched_pick[A]`, `sched_pick[B]`; 재계산 전후 `counter`.
  - 기대 출력: 원본 — A가 먼저 완주, pick 비율 약 3:1(경향); 수정 — 거의 동시 완주, pick 비율 약 1:1. 정확한 수치는 루프 길이·QEMU TCG 속도에 의존함을 각주.
  - 대체: 사전 캡처 `build/15-sched-orig.png`, `build/15-sched-flat.png`, `build/gdb-15-sched.txt`. 게스트에서 컴파일이 불가하면 사전 빌드된 `sched2` 바이너리를 루트 FS에 넣어 둔 이미지 사용(확인 필요).
- **C. (선택) printk in schedule 재진입**
  - 명령: 27장 (b) 코드를 켠 빌드로 `./sched2`.
  - 관찰: 출력 간격·멈춤 여부. 기대: 보통은 동작하나 write_q가 차면 멈출 수 있음(코드 추론). 대체: 캡처 1장 또는 생략.

## 이해 확인 질문과 정답
1. **Q.** `__NR_hello 72`, 표 끝에 `sys_hello`를 넣고 빌드했는데 `./hello`가 `r=-1 errno=1`이다. 가장 먼저 의심할 곳은? **A.** `kernel/system_call.s:61`의 `nr_system_calls`. 72인 채면 `cmpl $nr_system_calls-1,%eax; ja bad_sys_call`(81–82)로 `-1`이 돌아오고, `_syscall1`(unistd.h:146–157)이 그것을 `errno=1`로 바꾼다.
2. **Q.** 새 시스템 콜이 사용자 버퍼 포인터를 받는다. 커널에서 `buf[0]`을 그냥 읽으면 왜 안 되는가? **A.** 시스템 콜 진입 시 ds/es는 커널 세그먼트 0x10, 사용자 데이터는 fs=0x17(system_call.s:89–93). 사용자 주소는 `get_fs_byte/put_fs_byte`(asm/segment.h)로만 접근해야 하며, `sys_times`(sys.c:156–166)가 본보기다.
3. **Q.** 재계산 식의 `priority`를 상수 15로 바꾸면 선택 규칙(counter 최대)도 바뀌는가? 두 자식의 결과는 왜 같아지는가? **A.** 선택 규칙(sched.c:124–135)은 그대로다. 바뀐 것은 counter가 다시 채워지는 양(136–139)뿐이며, nice로 낮춘 priority가 더 이상 반영되지 않아 두 자식이 같은 몫을 받는다.
4. **Q.** 스케줄러 관찰에 printk 대신 `sched_pick[]` 카운터를 1순위로 두는 이유는? **A.** `printk`는 `tty_write`를 부르고(printk.c:29–39), `tty_write`는 `sleep_if_full`·`schedule()`을 부를 수 있어(tty_io.c:299, 323) `schedule()` 안에서 재진입할 위험이 있다. 전역 배열은 GDB `p`로 읽기만 하면 된다.

## 처음 등장하는 용어
- `_syscallN` 매크로: `int $0x80` 호출과 반환값·errno 변환을 만들어 주는 사용자 쪽 래퍼 생성 매크로(unistd.h:133–).
- `sys_call_table` / `nr_system_calls`: 번호→커널 함수 표와 그 상한. 둘은 따로 적혀 있어 손으로 맞춰야 한다.
- `bad_sys_call`: 범위 밖 번호가 가는 곳(system_call.s:72–74). 오류 코드 없이 `-1`.
- 심벌 파일(`tools/system`): GDB가 함수 이름을 주소로 바꾸는 데 쓰는 빌드 산출물. Image와 같은 빌드여야 한다.
- 재진입(reentrancy): 어떤 함수가 실행 중인데 그 안에서 같은 함수가 다시 불리는 상황. 오늘은 `schedule()`→`printk`→`tty_write`→`schedule()`.
- 패치(diff): 변경 전후 차이의 기록. lab/의 변경을 남기고 되돌리는 단위.

## 주의: 흔한 오해 / 말하지 말아야 할 것
- `src/`를 절대 편집하지 않는다. 슬라이드의 줄 번호는 모두 src 기준이고, lab의 줄 번호는 다를 수 있으므로 GDB `b 파일:줄`은 lab 기준으로 현장에서 확인한다.
- "sys_call_table에 넣으면 끝"이라고 말하지 않는다. `nr_system_calls`가 별도이며 미갱신 증상이 EPERM처럼 보인다는 점을 반드시 먼저 보인다.
- 사용자 포인터를 커널에서 직접 역참조하는 예제를 "일단 되니까"로 보여 주지 않는다. 기본 실습은 정수 인자만 쓰고, 포인터는 `get_fs_*` 규칙과 함께만 다룬다.
- 스케줄러 변경의 측정값(약 3:1 등)을 일반 법칙으로 말하지 않는다. 루프 길이, QEMU TCG, 다른 태스크(셸, init)의 영향이 있으므로 "경향"으로만.
- 오늘 바꾼 정책이 "더 좋은 스케줄러"라고 말하지 않는다. nice가 무력화되는 것은 기능 상실이며, 목적은 변경→확인 절차를 익히는 것이다.
- 현대 커널에서 시스템 콜을 추가하는 절차(syscall 표 파일, 아키텍처별 등)나 sched_ext를 설명하지 않는다. 그 주제는 VM 미선택으로 제외되었음을 3장의 노트로 끝낸다.
- 게스트 안 컴파일러·이미지 마운트·심벌 밑줄 접두 등 lab 환경 의존 사항은 "확인 필요"로 표시된 그대로 사전에 점검하고, 안 되면 사전 캡처로 대체한다고 수강생에게 말한다.

---
