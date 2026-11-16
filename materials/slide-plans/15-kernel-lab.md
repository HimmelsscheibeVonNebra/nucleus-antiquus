# 15회차 상세 슬라이드 제작 계획 — 커널 수정 실습: 새 시스템 콜과 스케줄러 변경

- 기준: materials/course-plan.md `# 15. 커널 수정 실습: 새 시스템 콜과 스케줄러 변경` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/15-kernel-lab.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 42장 → 이 계획 48장 (+6)
- 로드맵 위치: 파트 G «종합·실습» · 15/15 (종강 회차)

## 1. 회차 개요

- 핵심 질문: **커널을 바꾸면 어디서 어떻게 확인하는가?**
- 회차 대체 노트 (course-plan 원문 계승, 슬라이드 05에서 한 장으로 게시): 원래 계획에 있던 "현대 커널 모듈"과 "sched_ext" 두 회차는 선택되지 않은 현대 커널 VM이 필요하여 제외했고, 그 자리를 이 회차(0.11을 직접 고치고 QEMU+GDB로 확인하는 실습)로 대체한다. 현대 커널과의 대응은 14회차 비교 슬라이드가 개념 수준에서만 담당한다.
- 학습 목표 (course-plan 원문 계승):
  1. 시스템 콜 하나를 추가하기 위해 손대야 하는 **네 곳**(`include/unistd.h`의 `__NR_*`, `include/linux/sys.h`의 `sys_call_table[]`, `kernel/system_call.s`의 `nr_system_calls`, 새 커널 함수)과 사용자 쪽 `_syscallN` 매크로의 관계를 설명한다.
  2. `lab/`(실행·수정본)과 `src/`(원본)의 역할 차이를 지키며 `scripts/build.sh` → `scripts/run.sh` → GDB로 변경을 빌드·부팅·검증하는 순서를 수행한다.
  3. `schedule()`의 선택 규칙(`counter` 최대값)과 재계산 규칙(`counter/2 + priority`)을 바꾸고, 두 프로세스 테스트와 `printk`/GDB 카운터로 그 효과를 관찰한다.
  4. 변경이 "적용되지 않은 것처럼 보이는" 전형적 실패(nr_system_calls 미갱신, 사용자 포인터 직접 역참조, src/ 편집, 옛 심벌 파일)를 증상으로부터 역추적한다.
  5. 변경 위치(사용자 프로그램 / 시스템 콜 표 / 커널 함수 / 스케줄러)마다 적합한 검증 수단(프로그램 출력 / errno / printk / GDB 중단점·변수)을 짝지운다.
- 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — course-plan 원문 계승):

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

- 상태 변화도·비교 범위 (course-plan 원문 계승): 상태 변화도(변경 하나의 생애) — `미적재(src만 읽음)` → `수정됨(lab/ 파일 편집)` → `빌드됨(scripts/build.sh 성공, 새 Image·심벌 파일)` → `부팅됨(scripts/run.sh, 새 커널이 메모리에)` → `검증됨(기대 출력/GDB 값 일치)`, 전환 원인·변경 데이터·유지 조건·되돌림 전환 포함 · 비교 ①(변경 위치) 6곳 — 사용자 프로그램, `__NR_*` 번호, `sys_call_table[]`, `nr_system_calls`, 새 커널 함수, `schedule()` · 비교 ②(검증 수단) 6가지 — 사용자 프로그램 출력, 반환값·errno, `printk`, GDB 중단점, GDB 변수 관찰, QEMU 화면 캡처 · 비교 ③(스케줄러 정책 선택지) 4개 — 원본, 우선순위 무시, 라운드 로빈, 단순 우선순위 부스트.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 15. 커널 수정 실습: 새 시스템 콜과 스케줄러 변경 | 표지 | 대제목 `15. 커널 수정 실습: 새 시스템 콜과 스케줄러 변경` · 부제(핵심 질문 원문): "커널을 바꾸면 어디서 어떻게 확인하는가?" · 우상단 `Linux 0.11` 배지 + `1991`, 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `15/15 · 파트 G «종합·실습»`, 푸터 `Linux 0.11 커널 강좌 · 15/15 · 15-kernel-lab` · 배경: 수정 커널이 부팅되어 `hello: pid=…` 출력을 낸 QEMU 캡처(lab 수정본, 사전 캡처) | — | 표지 배지·푸터(00-common §1) · 배경 사전 캡처 build/15-hello-ok.png(기존 기록) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "커널을 바꾸면 어디서 어떻게 확인하는가?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치 — 실습 회차라 질문·지도·배경·코드·상태도·비교·시연·캡처·정답·확인·정리 전 단계를 지나므로 전 단계 강조 · 오늘의 두 파트 한 줄 예고: Part A 새 시스템 콜 `hello(n)`, Part B `schedule()` 재계산 규칙 변경 · 원 "지도" 슬라이드의 미니 지도 범례 계승 | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 G «종합·실습»의 15만 ORANGE 강조 · 완료(TEAL) 01–14 전부, 이후(MUTED) 없음 — 15가 마지막 회차(종강 표시) · 오늘 한 줄 문구와 14→15 연결 문구는 §3 명세 · 원 "지도" 슬라이드의 "15회차 표에서 15 강조" 내용을 오늘 상자가 대체 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | 수정 대상 파일 4개 진한 TEAL: include/unistd.h(번호) · include/linux/sys.h(`sys_call_table[]`) · kernel/system_call.s(`nr_system_calls`) · kernel/sched.c(`schedule()`), kernel/ 상자에 kernel/sys.c 라벨 추가(`sys_hello`의 자리) · 오늘의 데이터 흐름 화살표(ORANGE): 새 시스템 콜 번호 → sys_call_table 등록 → 커널 함수 → 재빌드 → QEMU 부팅 → 게스트에서 호출 확인(§3 명세) · 보조 화살표: 타이머 틱 → `schedule()` 재계산 규칙 → GDB 관찰 · 누적 강조(옅은 TEAL) 01–14 전 계층 | include/unistd.h:58, 60–131 · include/linux/sys.h:1–72, 74–86 · kernel/system_call.s:61, 80–100 · kernel/sched.c:104–142 · kernel/sys.c:16–48 | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 왜 이 회차인가 | 배경 | 대체 사유 노트 원문: 원래 계획의 "현대 커널 모듈"·"sched_ext" 두 회차는 선택되지 않은 현대 커널 VM이 필요하여 제외 — 그 자리를 이 회차(0.11을 직접 고치고 QEMU+GDB로 확인하는 실습)로 대체 · 현대 커널과의 대응은 14회차 비교 슬라이드가 개념 수준에서만 담당 · 그래도 같은 질문("바꾸면 어디서 확인하나")에 답한다는 점 · 현대 커널 시스템 콜 추가 절차·sched_ext는 이 노트로 끝낸다고 명시 | —(course-plan 노트 원문) | 노트 인용 블록 |
| 06 | lab/ 와 src/ 를 다시 구분한다 | 배경 | 1회차 20장 재사용: src = Kernel.org 원본(읽기·인용 전용), lab = yuan-xy/Linux-0.11 기반 실행본(현대 gcc/gas로 빌드, QEMU i386) · 오늘 **편집은 lab/에서만**, 슬라이드 인용 줄 번호는 src/ 기준 — lab의 줄 번호는 다를 수 있음 각주 · 두 트리의 같은 파일 경로 표: include/unistd.h · include/linux/sys.h · kernel/system_call.s · kernel/sys.c · kernel/sched.c | —(lab/·src/ 운용 규칙) | 두 트리 같은 파일 경로 표 · 1회차 20장 재사용 |
| 07 | build.sh — 빌드와 두 산출물 | 배경 | `scripts/build.sh`: lab/에서 make → `Image`, 심벌 파일 `tools/system` 산출 · 산출물 사슬: lab/ 소스 → 오브젝트 → `Image`·`tools/system` 심벌 · "심벌 파일 = 이번 빌드"여야 한다는 조건 — 옛 심벌 파일이면 GDB 중단점 불일치(41장 실패 표 예고) · kernel/Makefile:27–32 `OBJS`에 `sys.o`, `sched.o` 포함 → 새 함수를 sys.c에 두면 Makefile 수정 불필요 · 실제 스크립트 내용은 캡처로(확인 필요: 스크립트 옵션 이름) | kernel/Makefile:27–32 | build.sh 내용 캡처(§11 확인 후) |
| 08 | run.sh 와 GDB 연결 | 배경 | `scripts/run.sh`: QEMU `-S -s` 기동 · GDB 연결: `file lab/tools/system; target remote :1234` · 부팅 전 확인: run.sh가 바라보는 Image가 방금 빌드한 것인가(타임스탬프) · GDB에서 `info files`·중단점 "pending" 여부로 심벌 일치 확인 · 캡처 각주 규칙(00-common §7) — 이 회차 캡처는 모두 "수정 있음(내용 명시)" | —(실행 절차) | run.sh·GDB 연결 콘솔 캡처(§11 확인 후) |
| 09 | 상태 변화도: 변경 하나의 생애 | 상태도 | 상태 5개: `미적재(src만 읽음)` → `수정됨(lab/ 파일 편집)` → `빌드됨(scripts/build.sh 성공, 새 Image·심벌 파일)` → `부팅됨(scripts/run.sh, 새 커널이 메모리에)` → `검증됨(기대 출력/GDB 값 일치)` · 전환 원인(편집 / make / QEMU 기동 / 관찰 비교)과 변경되는 데이터(lab/ 소스 → 오브젝트·Image·`tools/system` 심벌 → 메모리의 `sys_call_table`·`schedule` 코드 → 로그) · 유지 조건: src/는 변하지 않음, 빌드 실패 시 "수정됨"에 머무름, 심벌 파일과 Image가 같은 빌드일 때만 "검증됨"으로 갈 수 있음 · 되돌림 전환(`git checkout`/원본 복사) 화살표 · 오늘 두 실습 모두 이 다섯 상태를 두 바퀴 돈다 | —(§4 상세 명세) | 상태 변화도 다이어그램(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 10 | 비교 ②: 무엇으로 확인할 것인가 | 비교 | 검증 수단 6가지 표: 사용자 프로그램 출력 / 반환값·errno / `printk` / GDB 중단점 / GDB 변수 관찰(`p sys_call_table[72]`, `p sched_pick`) / QEMU 화면 캡처 — 열: 무엇을 보여 주나 / 어디서는 쓰면 안 되나 / 재현성 · 핵심 행: `printk`는 `tty_write`(printk.c:21–41)를 부르므로 `schedule()` 안에서는 재진입 위험(tty_io.c:299 `sleep_if_full`, 323 `schedule()`) · 스케줄러 관찰은 GDB 변수가 1순위 | kernel/printk.c:21–41 · kernel/chr_drv/tty_io.c:299, 323 | 검증 수단 6행 표 |
| 11 | 오늘의 두 실습 미리 보기 | 배경 | Part A: `hello(n)` 시스템 콜 — 커널이 printk로 인사하고 `pid+n`을 돌려줌 · Part B: `schedule()`의 재계산 규칙 변경 — nice 준 자식과 안 준 자식의 완주 시간 비교 · 각각 "편집 위치 / 빌드 / 확인" 한 줄씩 · 두 실습 모두 9장 상태도의 다섯 상태를 한 바퀴씩 돈다 | — | 두 실습 카드(편집 위치·빌드·확인 3행) |
| 12 | A-1. 번호: `__NR_hello 72` | 코드 | unistd.h:60–131 발췌(`__NR_setregid 71`이 마지막)와 추가 줄 `#define __NR_hello 72` · `#ifdef __LIBRARY__`(58) 안에 있어야 `_syscallN` 매크로가 보인다는 점(185 `#endif /* __LIBRARY__ */`) · 번호 = `sys_call_table[]` 인덱스이므로 표 끝에 붙일 슬롯과 일치해야 함 · 마지막 번호가 71이라는 사실 확인 | include/unistd.h:58, 60–131, 185 | unistd.h:60–131 말미 코드 인용 |
| 13 | A-2. 표: `sys_call_table[]` 끝에 `sys_hello` | 코드 | sys.h:1–72 `extern int sys_*();` 선언 목록(마지막 `sys_setregid` 72행) — 72행 `extern int sys_setregid();` 뒤에 `extern int sys_hello();` · 86행 `sys_setreuid,sys_setregid };` → `…,sys_setregid, sys_hello };` · 표의 72번째(0부터) 슬롯이 된다는 그림 — 순서가 곧 번호 · 선언 빠뜨리면 암시적 선언 경고/오류(현대 gcc 기준, 확인 필요) | include/linux/sys.h:1–72, 74–86 | 코드 인용 + 72번 슬롯 그림(§4) |
| 14 | A-3. 상한: `nr_system_calls = 73` | 코드 | system_call.s:61 `nr_system_calls = 72` → 73으로 · 81–82 `cmpl $nr_system_calls-1,%eax; ja bad_sys_call` 연결 · 안 올리면 eax=72가 `bad_sys_call`(72–74: `movl $-1,%eax; iret`)로 가서 `-1`을 돌려주는데, `_syscall1` 매크로는 음수를 `errno=1`(EPERM)로 바꿔 **"권한 없음"처럼 보인다**는 함정 미리 예고(24장 시연에서 재현) | kernel/system_call.s:61, 72–74, 81–82 · include/unistd.h:146–157 | bad_sys_call 경로 도식 + 코드 인용 |
| 15 | A-4. 함수: `sys_hello` in kernel/sys.c | 코드 | sys.c:16–48 `-ENOSYS`만 돌려주는 stub들(`sys_ftime`, `sys_break`, `sys_ptrace`, `sys_stty`, `sys_gtty`, `sys_prof`) 옆에 추가 — 새 함수를 둘 위치의 본보기 · 추가 코드: `int sys_hello(long n) { printk("hello: pid=%d n=%ld\n\r", current->pid, n); return current->pid + n; }` · 가장 작은 시스템 콜의 본보기 `sys_getpid`, `sys_getppid`(sched.c:348–356) · kernel/Makefile:27–32 `OBJS`에 sys.o가 이미 있어 빌드 규칙 수정 불필요 | kernel/sys.c:16–48 · kernel/sched.c:348–356 · kernel/Makefile:27–32 | stub 목록 + sys_hello 코드 인용 |
| 16 | A-4b. 인자가 커널 함수에 도착하는 길 | 코드 | 인자 n은 ebx로 들어와 첫 인자가 되는 구조 · system_call.s:80–100: ebx/ecx/edx가 인자, `fs=0x17`, `call _sys_call_table(,%eax,4)` · 86–88 `pushl %edx; pushl %ecx; pushl %ebx` — 역순 push라 ebx가 스택 top = C 함수의 첫 인자 · 스택 그림(§4)으로 확인 | kernel/system_call.s:80–100 · 86–88 | 인자 전달 스택 그림(§4) |
| 17 | A-4′. 사용자 포인터를 받는다면 | 코드 | 확장안 `sys_hello2(char *buf)` · 커널에서 `*buf`를 직접 읽으면 ds=0x10(커널)이라 엉뚱한 메모리 — 사용자 데이터는 fs=0x17(system_call.s:89–93) · 반드시 `get_fs_byte/put_fs_byte`(asm/segment.h 전체)와 `verify_area` — `sys_times`의 `put_fs_long`(sys.c:156–166)이 본보기 · 1·2회차의 LDT/세그먼트(fs=0x17) 그림 재사용 · 오늘 기본 실습은 정수 인자만 써서 이 문제를 피함 | include/asm/segment.h(전체) · kernel/sys.c:156–166 · kernel/system_call.s:89–93 | LDT/세그먼트 fs=0x17 그림 재사용(§4) |
| 18 | A-5. 사용자 프로그램 `hello.c` | 코드 | lib/close.c:7–10 형태 그대로: `#define __LIBRARY__`, `#include <unistd.h>`, `_syscall1(int,hello,long,n)` · `#define __NR_hello 72`(게스트 헤더가 옛것이면 직접 정의) · main에서 `r = hello(100); printf("r=%d errno=%d\n", r, errno);` · 기대: 화면에 커널 printk 한 줄 + `r=pid+100` · 참조: `_syscall0`(unistd.h:133–144), init/main.c:23–24 `static inline _syscall0(int,fork)` — 커널 안에서도 같은 매크로 | lib/close.c:7–10 · include/unistd.h:133–144, 146–157 · init/main.c:23–24 | hello.c 코드 블록 + lib/close.c 대조 |
| 19 | 게스트 안에서 컴파일하기 | 배경 | lab 루트 FS(hdc 이미지)의 gcc 1.40으로 게스트 안에서 `gcc -o hello hello.c`(확인 필요: lab 이미지에 gcc 포함 여부) · 대안: 호스트에서 이미지를 마운트해 소스 파일만 넣기(minix fs 마운트 가능 여부 확인 필요) · 호스트 현대 gcc로 0.11 a.out 바이너리를 만드는 길은 오늘 범위 밖 · `sched2`(31장)도 같은 경로 — 게스트 컴파일이 불가하면 사전 빌드 바이너리 사용 | —(lab 환경 점검 — §11) | 절차 도식(게스트 gcc → 대안 2단계) |
| 20 | 비교 ①: 변경 위치별 빌드 범위와 증상 | 비교 | 표 6행: 사용자 프로그램(게스트 gcc만 재컴파일 / 컴파일 오류 또는 errno) · `__NR_*`(헤더 → lib/init 재컴파일 / `undeclared`) · `sys_call_table`(sys.h → sched.o 등 재컴파일 / 잘못된 함수 호출) · `nr_system_calls`(system_call.o / EPERM처럼 보임) · 새 함수(sys.o / 링크 오류 `undefined sys_hello`) · `schedule()`(sched.o / 동작 변화만, 오류 없음) — 열: 어느 파일 / 빌드 범위 / 틀렸을 때 증상, 검증 수단 열은 42장 완성판에서 채움 | include/unistd.h:60–131 · include/linux/sys.h:74–86 · kernel/system_call.s:61 · kernel/sys.c(새 함수) · kernel/sched.c:104–142 | 변경 위치 6행 표 |
| 21 | 시연 A-1: 편집과 빌드 | 시연 | lab/에서 네 파일 수정(diff 화면): include/unistd.h · include/linux/sys.h · kernel/system_call.s · kernel/sys.c · `scripts/build.sh` — 기대: 경고 없이 `Image` 생성 · `nm tools/system \| grep sys_hello`로 심벌 확인(심벌 밑줄 접두 여부는 lab 툴체인 기준) · 실패 시 대체: 사전 준비된 `lab-hello` 브랜치/디렉터리 | include/unistd.h:60–131 · include/linux/sys.h:74–86 · kernel/system_call.s:61 · kernel/sys.c(sys_hello 추가) | 캡처 01·02(§5) |
| 22 | 시연 A-2: 부팅과 실행 | 시연 | `scripts/run.sh`로 새 Image 부팅 · 게스트에서 `./hello` · 기대 출력: `hello: pid=N n=100` 다음 줄 `r=N+100 errno=0` · 캡처에 "lab 수정본(sys_hello 추가), 2026-xx 빌드" 각주 | kernel/sys.c(sys_hello) · include/unistd.h:146–157 | 캡처 03(§5) |
| 23 | 시연 A-3: GDB로 표와 진입 확인 | 시연 | `b sys_hello` 진입에서 `p n`, `p current->pid`, `bt`(system_call 프레임이 보이는지) · `p sys_call_table[72]` — 함수 주소가 sys_hello인지 · 중단 시 `p/x $eax`는 이미 호출 후이므로 `b *system_call+N` 대신 `b sys_hello` 진입 사용 · 기대: `n = 100` | include/linux/sys.h:74–86 · kernel/system_call.s:80–100 | GDB 명령 블록 · 캡처 04(§5) |
| 24 | 시연 A-4: 일부러 깨뜨리기 | 시연 | `nr_system_calls`를 72로 되돌려 재빌드·재부팅 → `./hello` 출력 `r=-1 errno=1` · GDB `b bad_sys_call`이 걸림 · 다시 73으로 고쳐 복구 · 증상→원인 역추적 연습(14장 함정의 실물) · 시간 없으면 사전 캡처로 대체 | kernel/system_call.s:61, 72–74, 81–82 · include/unistd.h:146–157 | 캡처 05(§5) |
| 25 | 시연 A 캡처 모음 | 캡처 | 빌드 로그 / 게스트 출력 / GDB `p sys_call_table[72]` / 깨뜨린 경우의 `errno=1` 네 캡처 · 모두 lab 수정본임을 각주 · 캡처마다 "관찰 vs 추론" 구분 한 줄(00-common §7) | —(관찰 대상은 21–24장) | 캡처 01–05 중 4장 재게시(§5) |
| 26 | B-1. 원본 `schedule()`의 선택 루프와 재계산 | 코드 | sched.c:104–142 재구조화: 시그널 깨우기(110–120) · 선택 루프(124–135: `state==TASK_RUNNING && counter > c` — RUNNING 중 counter 최대) · 재계산(136–139: `counter = (counter>>1) + priority` — RUNNING 아닌 태스크도 포함 → 잠든 태스크가 깨어나면 유리) · `switch_to(next)`(141) | kernel/sched.c:104–142(110–120, 124–135, 136–139, 141) | sched.c:124–141 코드 인용(선택 루프·재계산 색 구분) |
| 27 | B-1b. counter의 생애: do_timer·fork·INIT_TASK | 코드 | `do_timer`(sched.c:305–336): `--current->counter`(332), 0이면 cpl≠0일 때만 `schedule()`(334–335) · fork.c:85 `p->counter = p->priority` — 새 태스크의 초기 counter · INIT_TASK(include/linux/sched.h:113–114)의 `{ 0,15,15, …}` = state 0, counter 15, priority 15 · include/linux/sched.h:4 `NR_TASKS 64` | kernel/sched.c:305–336 · kernel/fork.c:85 · include/linux/sched.h:113–114, 4 | counter 수지 표(감소·초기화·재계산) |
| 28 | B-2. nice가 바꾸는 것 | 코드 | sched.c:378–383 `sys_nice`: `priority -= increment`(결과가 0보다 클 때만) · 자식 B가 `nice(10)` → priority 5 · 재계산 후 A는 counter≈15+…, B는 ≈5+… → A가 약 3배 자주 뽑힘(코드 추론, 측정으로 확인 예정 — 33장 시연) | kernel/sched.c:378–383 | sys_nice 코드 인용 + priority·counter 수치 예시 |
| 29 | 비교 ③: 오늘 가능한 정책 변형 | 비교 | 표 4행: ① 원본 / ② 우선순위 무시(`counter = 15` 또는 `(counter>>1)+15`로 고정 — 두 자식이 같은 몫) / ③ 라운드 로빈(선택 루프를 "current 인덱스 다음부터 첫 RUNNING"으로, counter 조건 제거 — 단 재계산 루프 `if (c) break`와 충돌 주의) / ④ 깨어난 태스크 부스트(wake_up 시 counter += k) · 열: 바꾸는 줄 / 두 프로세스 기대 결과 / 위험(기아, 0 counter 루프) · 오늘 구현: ②(가장 작은 diff, 효과가 확실) | kernel/sched.c:104–142(변형 대상) | 정책 변형 4행 표(§4) |
| 30 | B-3. 변경 diff | 코드 | sched.c:136–139의 `(*p)->priority` 부분을 상수 `15`로(또는 `#define SCHED_FLAT`으로 토글) · 3줄 diff · 선택 루프는 그대로 두므로 "counter 최대" 규칙 자체는 유지 — 바뀌는 것은 counter가 다시 채워지는 양뿐 | kernel/sched.c:136–139 | 3줄 diff 블록(§4) |
| 31 | B-4. 두 프로세스 테스트 `sched2.c` | 코드 | 부모가 `fork` 두 번; 자식 A는 그대로, 자식 B는 `nice(10)` · 각자 같은 길이의 빈 루프(수천만 회, 게스트 속도에 맞춰 조정)를 돌고 `times(&t)`(sys.c:156–166, 반환값 `jiffies`)로 시작·끝 jiffies를 찍어 `A: start=… end=…` 출력 후 `_exit` · 부모는 `wait` 두 번 · 비교 지표: 두 자식의 끝 jiffies 차이 | kernel/sys.c:156–166 · kernel/sched.c:378–383 | sched2.c 코드 블록 |
| 32 | B-5. 관찰 장치 두 가지 | 코드 | (a) GDB 카운터: sched.c에 `long sched_pick[NR_TASKS];` 추가, `switch_to(next)` 직전 `sched_pick[next]++` — printk 없이 GDB `p sched_pick`로 읽음(1순위) · (b) printk: `if (next != last_next) printk("[%d]", task[next]->pid)`처럼 **전환될 때만, 짧게** — 재진입 위험(10장)을 알고 쓰는 2순위 | kernel/sched.c:141 · kernel/printk.c:21–41 · kernel/chr_drv/tty_io.c:299, 323 | (a)·(b) 코드 조각 대조 |
| 33 | 시연 B-1: 원본 커널에서 측정 | 시연 | 수정 전 lab(A의 sys_hello는 유지, 32장 (a) 카운터를 추가한 빌드)로 부팅, `./sched2` · 기대: A의 end jiffies가 B보다 훨씬 작음(A 먼저 완주) · GDB `p sched_pick`에서 A 인덱스 값이 B의 약 3배(환경 의존, 경향만) | kernel/sched.c:104–142 · kernel/sched.c:378–383 | 캡처 06·07(§5) |
| 34 | 시연 B-2: 수정 후 재측정 | 시연 | 30장 diff 적용 → `build.sh` → `run.sh` → `./sched2` · 기대: 두 자식의 end jiffies가 비슷, `sched_pick` 두 값이 비슷 · 캡처 각주에 "lab 수정본(sched flat), 같은 루프 길이" | kernel/sched.c:136–139 | 캡처 08·09·10(§5) |
| 35 | 시연 B-3: GDB로 재계산 순간 보기 | 시연 | `b sched.c:137`(재계산 루프) 조건 `if c==0`(실제 줄은 lab 기준) · `p task[2]->counter`, `p task[3]->counter`, `p task[2]->priority`, `p task[3]->priority` 재계산 전후 · 원본은 15/5 차이가 counter에 반영, 수정본은 같은 값 | kernel/sched.c:136–139(재계산 루프, 원본 137행 근처) | GDB 명령 블록 · 캡처 11(§5) |
| 36 | 시연 B 캡처 모음 | 캡처 | 원본/수정본의 `sched2` 출력 두 장 + `p sched_pick` 두 장 + 재계산 GDB 로그 · 관찰값과 28장의 "약 3배" 추론을 나란히 놓고 차이를 말함 · 측정값은 루프 길이·QEMU TCG 속도 의존 — "경향"으로만(§8) | —(관찰 대상은 33–35장) | 캡처 06–11 재구성(원본·수정본 나란히, §5) |
| 37 | printk를 schedule에 넣었더니 (선택) | 캡처 | 32장 (b)를 켜고 돌린 화면: 출력은 나오지만 write_q가 차면 `sleep_if_full`→`schedule()` 재귀 가능 · 실제로 깨졌다면 그 캡처, 안 깨졌다면 "운이 좋았다"고 말하고 코드 근거(tty_io.c:299–301, 321–323)를 보임 · 강사 시연 C 대응 — 시간 부족 시 생략 | kernel/printk.c:21–41 · kernel/chr_drv/tty_io.c:299–301, 321–323 | (선택) 캡처 12(§5) + 근거 코드 인용 |
| 38 | 상태 변화도 다시: 두 실습이 지난 길 | 상태도 | 9장 상태도 위에 A와 B의 실제 전이 기록 · A-4의 "깨뜨리기"(24장)는 검증됨→수정됨 되돌림 화살표 · 두 실습이 다섯 상태를 두 바퀴 돈 궤적 시각화 | —(9장 상태도 재사용) | 9장 상태도 + A·B 궤적 덧그리기(§4) |
| 39 | 재빌드·검증 체크리스트 | 정리 | 편집 전: `src/`가 아닌 `lab/`인가(경로 확인) · 편집 후: 네 곳 번호 일치(`__NR_` = 표 인덱스 = `nr_system_calls-1`) · 빌드: build.sh 종료 코드, 경고 중 `implicit declaration` · 부팅: run.sh의 Image가 방금 것인가(타임스탬프) · GDB: `file`이 방금 `tools/system`인가(`info files`, 중단점이 "pending"이면 심벌 불일치) · 검증: 기대 출력과 실제 출력을 슬라이드에 나란히 | —(체크리스트) | 체크리스트 6단계 표 |
| 40 | 흔한 실패 ①: 시스템 콜 쪽 | 정리 | 증상→원인 표: `errno=1`, `r=-1` → nr_system_calls 미갱신(bad_sys_call) · 컴파일 `__NR_hello undeclared` → `__LIBRARY__` 누락 또는 게스트 헤더 옛것 · 링크 `undefined reference sys_hello` → 함수 파일이 OBJS에 없거나 이름 불일치 · 쓰레기 값/페이지 폴트 → 사용자 포인터 직접 역참조(17장) · 출력 없음 → src/를 고침 | kernel/system_call.s:61, 72–74 · include/unistd.h:58, 133–157 · kernel/Makefile:27–32 · include/asm/segment.h | 증상→원인 표 5행 |
| 41 | 흔한 실패 ②: 빌드·도구 쪽 | 정리 | 중단점이 안 걸림 → 옛 `tools/system`을 GDB에 로드 · `_sys_call_table` vs `sys_call_table` → src(옛 gas, 밑줄 접두)와 lab(현대 gas) 심벌 차이(확인 필요) · 수정했는데 그대로 → run.sh가 다른 Image 경로를 봄 · 부팅 멈춤 → `nr_system_calls`를 표 길이보다 크게 해 NULL 호출(표 밖 메모리) | kernel/system_call.s:61 · (lab 툴체인 심벌 차이 — §11 확인) | 증상→원인 표 4행 |
| 42 | 비교 ①(완성): 변경 위치 × 검증 수단 | 비교 | 20장 표에 검증 수단 열을 채운 완성판 · 사용자 프로그램→출력·errno · 번호/표/카운트→GDB `p sys_call_table[72]`·`b bad_sys_call` · 커널 함수→printk·`b sys_hello` · 스케줄러→`sched_pick`·jiffies 비교·재계산 중단점 · "어디를 바꿨느냐가 어떻게 확인할지를 정한다" | include/linux/sys.h:74–86 · kernel/sched.c:104–142 등(§2 슬라이드 20·10 명세) | 변경 위치 × 검증 수단 완성 표 |
| 43 | 변경을 되돌리고 남기는 법 | 정리 | lab/에서 diff를 저장(`git diff > build/15-hello.patch` 등) · 원본 상태로 복구 · 다음 학기에 재적용 가능하게 · src/는 처음부터 끝까지 손대지 않았음을 `diff -r`로 확인하는 캡처 | —(lab/ git 운용) | 캡처 13(§5) — 패치 저장·src 무변경 확인 |
| 44 | 핵심 질문의 답 | 정답 | "커널을 바꾸면 (1) 변경이 사는 자리에 따라 빌드 범위가 다르고, (2) 그 자리에 맞는 수단 — 사용자 출력/errno, printk, GDB 표·변수·중단점 — 으로, (3) 같은 빌드의 심벌 파일을 들고, (4) 수정 전과 후를 나란히 놓고 확인한다." · 상태도 다섯 상태(9장) 재등장 — 답의 네 조건과 다섯 상태 대응 | —(§2 슬라이드 09·20·42 종합) | 9장 상태도 축약 재인용 + 4조건 강조 박스 |
| 45 | 15회차 되돌아보기 | 로드맵 | 1회차 "셸이 나오기 전에 누가 실행되는가?"부터 오늘 "커널을 바꾸면 어디서 어떻게 확인하는가?"까지 핵심 질문 15개를 한 줄씩 · 14회차 지도(테두리 = 시스템 콜 표, 박스 ⑨ = schedule) 위에 오늘 수정한 두 지점 표시 — 원 "지도" 슬라이드의 14회차 지도 축소판 계승 | —(01–14 회차 핵심 질문 인용) | 15개 핵심 질문 타임라인(§4) — 14회차 지도 축소판 재사용 |
| 46 | 이해 확인 질문 | 확인 | 4문항 질문만 게시(§6 원문 그대로), 정답은 47장에서 표시 · 1번 `r=-1 errno=1`의 첫 의심处 · 2번 사용자 버퍼 포인터를 커널에서 그냥 읽으면 안 되는 이유 · 3번 재계산 상수화가 선택 규칙을 바꾸는가 · 4번 스케줄러 관찰에 `sched_pick[]` 카운터가 1순위인 이유 | (§6 정답 근거와 동일) | 문항 4개 텍스트 |
| 47 | 이해 확인 정답 | 확인 | 정답과 근거 줄 번호(§6 원문 그대로) · 1번 kernel/system_call.s:61, 81–82 + `_syscall1`(unistd.h:146–157) · 2번 ds/es=0x10, fs=0x17(system_call.s:89–93) + `get_fs_byte/put_fs_byte`(asm/segment.h) + `sys_times`(sys.c:156–166) 본보기 · 3번 선택 규칙(sched.c:124–135)은 그대로, 바뀐 것은 재계산 양(136–139)뿐 · 4번 `printk`→`tty_write`(printk.c:29–39)→`sleep_if_full`·`schedule()`(tty_io.c:299, 323) 재진입 위험 | (§6 정답 근거와 동일) | 정답 4개 텍스트 |
| 48 | 정리와 과정 마무리 | 정리 | 오늘 산출물(패치 2개, 캡처) · 더 해 볼 것: 사용자 포인터 받는 시스템 콜, 라운드 로빈 변형, wake_up 부스트 — 각각의 검증 수단 짝지어 제시 · 자료는 PPTX 1개뿐임을 상기 · 15회차 전체 과정 마무리 — 파트 A–G «종합·실습» 완결 | —(마무리) | 종강 요약 박스(산출물·더 해 볼 것) |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: G «종합·실습» · 15/15 — 파트 G의 마지막 회차이자 과정 전체의 마지막(종강). 완료(TEAL) 01–14 전부, 오늘(ORANGE + 굵은 테두리) 15, 이후(MUTED) 없음.
- 오늘 한 줄 문구: "14회차까지 읽기만 했다 — 이제 직접 바꾼다: 수정 → 빌드 → 부팅 → 검증"
- 14→오늘 연결 화살표 문구: "14: 셸 명령 한 줄의 전체 경로를 읽고 현대 커널과 비교만 했다 → 15: 이제 그 커널을 직접 바꾼다 — 새 시스템 콜과 schedule() 재계산 규칙을 고치고 빌드·부팅·검증까지 완결"
- 오늘→다음 화살표: 없음(15가 마지막). 대신 **종강 표시** — 15 상자 오른쪽에 "종강 — 15/15 완료" 마커(ORANGE).
- 원 "지도" 슬라이드(원 02) 내용 계승: "15회차 표에서 15 강조"는 오늘 상자(ORANGE)가 대체. "14회차 지도(테두리 = 시스템 콜 표, 박스 ⑨ = schedule) 축소판을 옆에 두고 오늘 손댈 두 지점을 표시"는 슬라이드 04 구조도의 하이라이트 4파일 + 흐름 화살표가 대체하며, 14회차 지도 축소판 자체는 슬라이드 45 되돌아보기에서 재사용한다.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL, 오늘 수정 대상): include/unistd.h(`__NR_*` 번호 — 사용자/커널 경계의 int 0x80 번호 라벨 위치) · include/linux/sys.h(`sys_call_table[]` — 진입 행) · kernel/system_call.s(`nr_system_calls` — 진입 행) · kernel/sched.c(`schedule()` — kernel/ 프로세스 상자). 또한 kernel/ 프로세스 상자에 kernel/sys.c 라벨을 추가해 `sys_hello`의 자리를 보인다.
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): 새 시스템 콜 번호 `__NR_hello 72`(include/unistd.h) → sys_call_table 등록(include/linux/sys.h, 상한 kernel/system_call.s `nr_system_calls`) → 커널 함수 `sys_hello`(kernel/sys.c) → 재빌드(scripts/build.sh, 새 Image·`tools/system` 심벌) → QEMU 부팅(scripts/run.sh) → 게스트에서 호출 확인(`./hello` → `int 0x80` → kernel/system_call.s `_system_call` 경유).
- 보조 화살표(ORANGE, 2번째 — 00-common §2가 허용하는 1–2개 안): 타이머 틱 → `do_timer` → `schedule()` 재계산 규칙(kernel/sched.c:136–139) 변경 → GDB `p sched_pick` 관찰.
- 누적 강조(옅은 TEAL, 01–14): 마지막 회차이므로 전 계층 — boot/·init/main.c(01–03), kernel/system_call.s·kernel/asm.s·kernel/traps.c(04), include/linux/sched.h·kernel/sched.c(05), kernel/fork.c(06), mm/memory.c(07–08), fs/exec.c(09), kernel/exit.c·kernel/signal.c(10), fs/buffer.c·kernel/blk_drv/(11), fs/namei.c·fs/inode.c 등(12), kernel/chr_drv/(13), 14회차는 전체 인용. 오늘 진한 강조 파일과 겹치는 곳(kernel/system_call.s·kernel/sched.c 등)은 진한 TEAL로.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(15 강조·종강) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 15 ORANGE, 01–14 TEAL, 14→15 연결 화살표 1개, 종강 마커 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(수정 대상 4파일 강조) | 도형 다이어그램 | §3 명세 그대로 — unistd.h·sys.h·system_call.s·sched.c 진한 TEAL + 흐름 화살표 2, kernel/ 상자에 sys.c 라벨 추가 | 전 회차 공통 골격 + 14회차 누적 영역 |
| 09 | 상태 변화도 "변경 하나의 생애" (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(상태 5 + 전환 4 + 되돌림) | — |
| 10 | 검증 수단 6행 표 | 표 | 출력 / errno / printk / GDB 중단점 / GDB 변수 관찰 / QEMU 캡처 × 무엇을 보여주나·어디서는 안 되나·재현성 | — |
| 13 | sys_call_table 72번 슬롯 그림 | 도형 | 인덱스 0…71 채워진 슬롯 행 끝에 빈 72번 슬롯, `sys_hello`가 채워지는 모습 — "순서가 곧 번호" | 04회차 sys_call_table 도식 언어 |
| 14 | bad_sys_call 경로 도식 | 도형 | eax=72 → `cmpl $nr_system_calls-1,%eax; ja bad_sys_call`(81–82) → bad_sys_call(72–74) `-1` → `_syscall1`이 `errno=1`(EPERM)로 변환 — "권한 없음"처럼 보이는 경로 ORANGE | 04회차 시스템 콜 진입 도식 |
| 16 | 인자 전달 스택 그림 | 도형 | eax=72(번호), ebx=100(인자) → `pushl %edx; pushl %ecx; pushl %ebx`(86–88) → C 함수 `sys_hello(long n)`의 첫 인자 | 04회차 시스템 콜 스택 그림 양식 |
| 17 | 사용자 포인터와 fs=0x17 | 도형 | ds=0x10(커널)과 fs=0x17(사용자 데이터) 세그먼트 — `*buf` 직접 접근이 엉뚱한 메모리가 되는 이유와 `get_fs_byte` 경로 | 01·02회차 LDT/세그먼트 그림 재사용 |
| 20 | 변경 위치별 빌드 범위 표 | 표 | 6행 × (어느 파일 / 빌드 범위 / 증상) — §2 슬라이드 20 명세 | — |
| 26 | schedule() 코드 인용 | 코드 인용 | sched.c:104–142 중 선택 루프(124–135)·재계산(136–139)·switch_to(141) 하이라이트 | 05회차 schedule 인용 양식 |
| 27 | counter 수지 표 | 표 | counter의 감소(do_timer:332 `--current->counter`)·초기화(fork.c:85)·재계산(136–139)·INIT_TASK 15/15 | 05회차 counter 도식 |
| 29 | 정책 변형 비교표 | 표 | 4행 × (바꾸는 줄 / 두 프로세스 기대 결과 / 위험) — §2 슬라이드 29 명세 | — |
| 30 | 3줄 diff | 코드 인용(diff) | `(*p)->priority` → `15` 변경 diff 블록 + `#define SCHED_FLAT` 토글 안 | — |
| 38 | 상태 변화도(실습 궤적 덧그리기) | 도형 상태 다이어그램 | 09장 상태도에 Part A·B의 두 바퀴 궤적과 A-4 깨뜨리기의 검증됨→수정됨 되돌림 화살표 | 09장(동일 시각 언어) |
| 45 | 15회차 되돌아보기 타임라인 | 도형 다이어그램 | 핵심 질문 15개 한 줄 타임라인(01–15) 위에 오늘 수정 두 지점(시스템 콜 표·schedule) 표시 | 14회차 지도(테두리 = 시스템 콜 표, 박스 ⑨ = schedule) 축소판 · 원 02 "지도" 내용 계승 |

핵심 시각자료 상세 명세 — "변경 하나의 생애" 상태 변화도 (슬라이드 09·38이 같은 시각 언어를 공유):

- 공통 시각 언어: 상태 5개를 가로 타임라인 상자로 — `미적재`·`수정됨`·`빌드됨`·`부팅됨`(TEAL), `검증됨`(굵은 테두리 목표 상자). 순방향 전환 화살표 TEAL, 오늘 실습이 실제로 머무는 "지금" 상태 ORANGE 점, 되돌림 화살표 MUTED 점선. 우하단 `Linux 0.11` 라벨.
- 전환 라벨: 미적재→수정됨(원인: 편집 — lab/ 파일) / 수정됨→빌드됨(make — `Image`·`tools/system`) / 빌드됨→부팅됨(QEMU 기동 — 메모리의 `sys_call_table`·`schedule` 코드) / 부팅됨→검증됨(관찰 비교 — 기대 출력/GDB 값). 변경 데이터: lab/ 소스 → 오브젝트·Image·심벌 → 메모리 코드 → 로그.
- 유지 조건 박스(하단): src/는 변하지 않음 / 빌드 실패 시 "수정됨"에 머무름 / 심벌 파일과 Image가 같은 빌드일 때만 "검증됨"으로 갈 수 있음.
- 되돌림 전환: `git checkout`/원본 복사 — 부팅됨·검증됨 → 수정됨(MUTED 점선). 빌드 실패(수정됨에 머무름)·부팅 실패 되돌림 화살표.
- 슬라이드 38: 같은 그림에 Part A 궤적(한 바퀴)과 Part B 궤적(두 번째 바퀴)을 덧그리고, A-4 "깨뜨리기"(24장)의 검증됨→수정됨 되돌림 화살표를 ORANGE로 표시.

## 5. 캡처 목록 (강사 시연)

캡처 보관: `materials/15-kernel-lab/captures/<두자리순번>-<설명>.png`. 이 회차 캡처는 소스 diff·빌드 로그·재부팅 후 테스트 실행 화면 등 실습 산물을 포함한다.

| 단계 | 캡처 파일(materials/15-kernel-lab/captures/) | 명령 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A-1 편집 | 01-hello-four-file-diff.png | lab/ 네 파일 수정 화면: include/unistd.h `#define __NR_hello 72` · include/linux/sys.h extern·표 끝 · kernel/system_call.s `nr_system_calls = 73` · kernel/sys.c `sys_hello` | 네 곳 수정 diff — 번호·표 인덱스·상한 일치 | 사전 준비 디렉터리 `lab-hello/` |
| A-1 빌드 | 02-build-log-nm-sys-hello.png | `scripts/build.sh` · `nm tools/system \| grep sys_hello` | 경고 없는 빌드 로그, `Image` 생성, 심벌 존재(밑줄 접두 여부는 lab 툴체인 기준) | build/gdb-15-hello.txt(기존 기록) |
| A-2 실행 | 03-guest-hello-run.png | `scripts/run.sh` · 게스트 `./hello` | `hello: pid=N n=100` / `r=N+100 errno=0` | build/15-hello-ok.png(기존 기록) |
| A-3 GDB | 04-gdb-sys-call-table-72.png | `b sys_hello` · `p sys_call_table[72]` · `p n` · `p current->pid` · `bt` | 표[72] = sys_hello 주소, `n = 100`, system_call 프레임 | build/gdb-15-hello.txt(기존 기록) |
| A-4 깨뜨리기 | 05-eperm-bad-sys-call.png | `nr_system_calls` 72로 복귀·재빌드·재부팅 · `./hello` · `b bad_sys_call` | `r=-1 errno=1`, bad_sys_call 중단 | build/15-hello-eperm.png(기존 기록) |
| B-1 원본 실행 | 06-sched2-orig-run.png | `./sched2`(수정 전 lab, sys_hello는 유지, sched_pick 카운터 추가 빌드) | A의 end jiffies가 B보다 훨씬 작음(A 먼저 완주) | build/15-sched-orig.png(기존 기록) |
| B-1 GDB | 07-gdb-sched-pick-orig.png | `p sched_pick` | A 인덱스 값이 B의 약 3배(경향) | build/gdb-15-sched.txt(기존 기록) |
| B-2 diff·빌드 | 08-sched-flat-diff-build.png | sched.c 3줄 diff 적용 화면 · `scripts/build.sh` | `(*p)->priority` → `15`, 경고 없는 재빌드 | — |
| B-2 실행 | 09-sched2-flat-run.png | `scripts/run.sh` · `./sched2` | 두 자식의 end jiffies가 비슷 | build/15-sched-flat.png(기존 기록) |
| B-2 GDB | 10-gdb-sched-pick-flat.png | `p sched_pick` | 두 값이 비슷(약 1:1) | build/gdb-15-sched.txt(기존 기록) |
| B-3 재계산 | 11-gdb-recalc-counter.png | `b sched.c:137`(실제 줄은 lab 기준) 조건 `if c==0` · `p task[2]->counter` · `p task[3]->counter` · `p task[2]->priority` · `p task[3]->priority` | 재계산 전후 counter — 원본은 15/5 차이 반영, 수정본은 같은 값 | build/gdb-15-sched.txt(기존 기록) |
| C(선택) printk | 12-printk-in-schedule.png | 32장 (b) 코드를 켠 빌드로 `./sched2` | 출력 간격·멈춤 여부 — write_q가 차면 `sleep_if_full`→`schedule()` 재귀 가능 | 사전 캡처 1장 또는 생략 |
| 되돌리기 | 13-src-diff-r-untouched.png | `git diff > build/15-hello.patch` · src/ 원본 대조 `diff -r` | 패치 저장, src/ 무변경 확인 | — |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 있음(내용: sys_hello 추가 / sched flat / sched_pick 카운터) · 캡처 날짜`(00-common §7). 사전 캡처·기존 자산은 화면 모서리에 `기존 기록` 라벨.

## 6. 이해 확인 질문과 정답 (해당 슬라이드 번호 명시)

질문은 슬라이드 46, 정답은 슬라이드 47에 게시(원문 계승).

1. **Q.** `__NR_hello 72`, 표 끝에 `sys_hello`를 넣고 빌드했는데 `./hello`가 `r=-1 errno=1`이다. 가장 먼저 의심할 곳은? **A.** `kernel/system_call.s:61`의 `nr_system_calls`. 72인 채면 `cmpl $nr_system_calls-1,%eax; ja bad_sys_call`(81–82)로 `-1`이 돌아오고, `_syscall1`(unistd.h:146–157)이 그것을 `errno=1`로 바꾼다.
2. **Q.** 새 시스템 콜이 사용자 버퍼 포인터를 받는다. 커널에서 `buf[0]`을 그냥 읽으면 왜 안 되는가? **A.** 시스템 콜 진입 시 ds/es는 커널 세그먼트 0x10, 사용자 데이터는 fs=0x17(system_call.s:89–93). 사용자 주소는 `get_fs_byte/put_fs_byte`(asm/segment.h)로만 접근해야 하며, `sys_times`(sys.c:156–166)가 본보기다.
3. **Q.** 재계산 식의 `priority`를 상수 15로 바꾸면 선택 규칙(counter 최대)도 바뀌는가? 두 자식의 결과는 왜 같아지는가? **A.** 선택 규칙(sched.c:124–135)은 그대로다. 바뀐 것은 counter가 다시 채워지는 양(136–139)뿐이며, nice로 낮춘 priority가 더 이상 반영되지 않아 두 자식이 같은 몫을 받는다.
4. **Q.** 스케줄러 관찰에 printk 대신 `sched_pick[]` 카운터를 1순위로 두는 이유는? **A.** `printk`는 `tty_write`를 부르고(printk.c:29–39), `tty_write`는 `sleep_if_full`·`schedule()`을 부를 수 있어(tty_io.c:299, 323) `schedule()` 안에서 재진입할 위험이 있다. 전역 배열은 GDB `p`로 읽기만 하면 된다.

## 7. 처음 등장하는 용어 (용어 | 정의 | 첫 등장 슬라이드)

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| `_syscallN` 매크로 | `int $0x80` 호출과 반환값·errno 변환을 만들어 주는 사용자 쪽 래퍼 생성 매크로(unistd.h:133–) | 14(언급) · 본문 18 |
| `sys_call_table` / `nr_system_calls` | 번호→커널 함수 표와 그 상한. 둘은 따로 적혀 있어 손으로 맞춰야 한다. | 13 |
| `bad_sys_call` | 범위 밖 번호가 가는 곳(system_call.s:72–74). 오류 코드 없이 `-1`. | 14 |
| 심벌 파일(`tools/system`) | GDB가 함수 이름을 주소로 바꾸는 데 쓰는 빌드 산출물. Image와 같은 빌드여야 한다. | 7 |
| 재진입(reentrancy) | 어떤 함수가 실행 중인데 그 안에서 같은 함수가 다시 불리는 상황. 오늘은 `schedule()`→`printk`→`tty_write`→`schedule()`. | 10 |
| 패치(diff) | 변경 전후 차이의 기록. lab/의 변경을 남기고 되돌리는 단위. | 43 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- `src/`를 절대 편집하지 않는다. 슬라이드의 줄 번호는 모두 src 기준이고, lab의 줄 번호는 다를 수 있으므로 GDB `b 파일:줄`은 lab 기준으로 현장에서 확인한다.
- "sys_call_table에 넣으면 끝"이라고 말하지 않는다. `nr_system_calls`가 별도이며 미갱신 증상이 EPERM처럼 보인다는 점을 반드시 먼저 보인다.
- 사용자 포인터를 커널에서 직접 역참조하는 예제를 "일단 되니까"로 보여 주지 않는다. 기본 실습은 정수 인자만 쓰고, 포인터는 `get_fs_*` 규칙과 함께만 다룬다.
- 스케줄러 변경의 측정값(약 3:1 등)을 일반 법칙으로 말하지 않는다. 루프 길이, QEMU TCG, 다른 태스크(셸, init)의 영향이 있으므로 "경향"으로만.
- 오늘 바꾼 정책이 "더 좋은 스케줄러"라고 말하지 않는다. nice가 무력화되는 것은 기능 상실이며, 목적은 변경→확인 절차를 익히는 것이다.
- 현대 커널에서 시스템 콜을 추가하는 절차(syscall 표 파일, 아키텍처별 등)나 sched_ext를 설명하지 않는다. 그 주제는 VM 미선택으로 제외되었음을 5장의 노트로 끝낸다.
- 게스트 안 컴파일러·이미지 마운트·심벌 밑줄 접두 등 lab 환경 의존 사항은 "확인 필요"로 표시된 그대로 사전에 점검하고, 안 되면 사전 캡처로 대체한다고 수강생에게 말한다.

## 9. 120분 운영안 (새 슬라이드 번호: 범위 | 분 | 진행)

| 슬라이드 범위 | 분 | 진행 |
|---|---|---|
| 01–05 | 5 | 핵심 질문, 로드맵·구조도(지도), 회차 대체 노트와 오늘의 두 파트 |
| 06–11 | 12 | 배경: lab vs src, build.sh/run.sh/GDB, 변경의 생애(상태도), 검증 수단 비교 |
| 12–20 | 25 | Part A 코드: 번호·표·카운트·함수·래퍼 다섯 조각, 사용자 포인터 규칙 |
| 21–25 | 20 | Part A 시연: 편집 → 빌드 → 부팅 → 실행 → GDB 확인, 일부러 nr_system_calls 빼고 재현 |
| 26–32 | 15 | Part B 코드: schedule 선택·재계산 규칙, 변경안 3개 비교, 테스트 프로그램 |
| 33–38 | 25 | Part B 시연: 원본 측정 → 수정 → 재측정, printk/GDB 카운터 |
| 39–43 | 10 | 체크리스트, 흔한 실패와 증상, 변경 위치 비교표 |
| 44–45 | 5 | 핵심 질문의 답, 15회차 전체 되돌아보기 |
| 46–48 | 3 | 이해 확인, 정리·과정 마무리 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞 5, 배경 12, Part A 코드 25, Part A 시연 20, Part B 코드 15, Part B 시연 25, 실패·체크리스트 10, 답·되돌아보기 5, 이해 확인·마무리 3.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(42행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07+08(분할) · 원 06→09 · 원 07→10 · 원 08→11 · 원 09→12 · 원 10→13 · 원 11→14 · 원 12→15+16(분할) · 원 13→17 · 원 14→18 · 원 15→19 · 원 16→20 · 원 17→21 · 원 18→22 · 원 19→23 · 원 20→24 · 원 21→25 · 원 22→26+27(분할) · 원 23→28 · 원 24→29 · 원 25→30 · 원 26→31 · 원 27→32 · 원 28→33 · 원 29→34 · 원 30→35 · 원 31→36 · 원 32→37 · 원 33→38 · 원 34→39 · 원 35→40 · 원 36→41 · 원 37→42 · 원 38→43 · 원 39→44 · 원 40→45 · 원 41→46+47(분할) · 원 42→48.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| 빌드·실행 도구 분할 | 원 05 → 새 07+08 | build.sh 산출물(Image·심벌 파일·Makefile)과 run.sh·GDB 연결이 각각 캡처와 불릿을 필요로 하는 밀도 — 00-common §5 우선순위 3 (+1) |
| sys_hello 코드·인자 메커니즘 분할 | 원 12 → 새 15+16 | 함수 추가 위치·본보기(stub·Makefile)와 인자 도착 구조(`pushl %edx; pushl %ecx; pushl %ebx`, system_call.s:86–88)가 코드 2스크린 분량 (+1) |
| schedule 재독 분할 | 원 22 → 새 26+27 | 선택 루프·재계산(sched.c:104–142)과 counter 공급(do_timer·fork.c:85·INIT_TASK)이 서로 다른 파일의 코드 — 각각 코드 인용 확보 (+1) |
| 이해 확인 질문·정답 분할 | 원 41 → 새 46+47 | 질문만 먼저 게시하고 정답을 클릭 뒤 표시 — 표준 뒷부분 관행(00-common §4) (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02·40 "지도"→로드맵/구조, 원 39 "정리"→정답, 원 41 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 슬라이드 상호참조 갱신 | 원문 중 "7장"→10장, "13장"→17장, "16장 표"→20장 표, "23장"→28장, "25장 diff"→30장 diff, "27장"→32장, "6장 상태도"→9장 상태도 | 새 번호 체계로 재지정 — 줄 번호·수치·함수명·원어 표현은 원문 그대로 |
| 계 | 42장 → 48장 (+6) | 목표 범위 44–50 안(00-common §5) |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- 게스트 gcc 유무 확인 (course-plan "PPTX 제작 전 확인 목록"의 15 해당분): lab 루트 FS(hdc 이미지)의 gcc 1.40으로 슬라이드 18 `hello.c`·31 `sched2.c`의 게스트 안 컴파일이 되는지 — 안 되면 사전 빌드 바이너리를 루트 FS에 넣어 둔 이미지 사용(강사 시연 B 대체안) 또는 사전 캡처로 대체하고 수강생에게 그렇게 말한다(§8 마지막 항목).
- minix fs 호스트 마운트 가능 여부(슬라이드 19 대안) — 소스 파일만 이미지에 넣는 경로 점검.
- lab/ 빌드의 심벌명과 줄 번호 (course-plan 확인 목록 해당분): `sys_call_table` vs `_sys_call_table`(src는 옛 gas 밑줄 접두, lab은 현대 gas — 확인 필요) — 슬라이드 23 `p sys_call_table[72]`·41 실패 표의 근거. `nm tools/system \| grep sys_hello` 결과의 접두도 기록.
- 수정본(lab)에서의 줄 번호 확인: GDB `b sched.c:137`은 재계산 루프의 lab 기준 실제 줄로 교체(슬라이드 35) — 슬라이드 캡션은 src 기준, 현장 중단점은 lab 기준임을 각주(§8 첫 항목).
- scripts/build.sh·scripts/run.sh 스크립트 옵션 이름 확인(슬라이드 07–08 캡처용 — 원문 "확인 필요" 사항).
- sched_pick 관찰 빌드 사전 준비: 슬라이드 32 (a) `long sched_pick[NR_TASKS];`·`sched_pick[next]++`가 들어간 빌드 — 시연 B-1(33장) 측정과 사전 캡처의 기준이 되는 빌드.
- 사전 캡처·대체 자료 확보("기존 기록" 라벨): `build/15-hello-ok.png` · `build/15-hello-eperm.png` · `build/gdb-15-hello.txt` · `build/15-sched-orig.png` · `build/15-sched-flat.png` · `build/gdb-15-sched.txt` · 사전 준비 디렉터리 `lab-hello/` — 신규 캡처는 `materials/15-kernel-lab/captures/<두자리순번>-<설명>.png`(§5).
- 캡처 각주: 이 회차의 모든 캡처는 "수정 있음" — 내용(sys_hello 추가 / sched flat / sched_pick 카운터)을 각주에 명시(00-common §7).
