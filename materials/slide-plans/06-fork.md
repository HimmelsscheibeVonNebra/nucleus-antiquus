# 06회차 상세 슬라이드 제작 계획 — fork()와 프로세스 생성

- 기준: materials/course-plan.md `# 06. fork()와 프로세스 생성` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/06-fork.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 42장 → 이 계획 48장 (+6)
- 로드맵 위치: 파트 B «실행의 길» · 06/15 (파트 B의 마지막 회차 — 완료 회차 01–05)

## 1. 회차 개요

**핵심 질문**: fork() 이후 부모와 자식은 어디에서 다시 실행되는가?

**학습 목표** (course-plan 원문 계승):

1. `fork()`가 `_syscall0` → `int $0x80` → `sys_call_table[2]` → `_sys_fork`(어셈블리) → `find_empty_process` → `copy_process`로 이어지는 경로를 04회차 프레임 그림 위에 겹쳐 그린다.
2. `copy_process`의 17개 인자가 전부 **`_system_call`과 `_sys_fork`가 push한 스택 값**임을 확인하고, 인자 이름과 스택 슬롯을 1:1로 대응시킨다.
3. `copy_process`가 새 `task_struct`를 한 페이지에 만들고 TSS를 채우는 순서를 읽으며, `tss.eax = 0`, `tss.eip = eip`, `tss.esp = esp`가 "자식이 `fork()` 직후 사용자 코드에서 0을 받는" 메커니즘임을 05회차 TSS 전환과 연결해 설명한다.
4. fork에서 **복사되는 것**(task_struct 본문, LDT base, 페이지 테이블 항목)과 **공유되는 것**(`struct file`·inode는 카운트 증가, 물리 페이지는 읽기 전용 공유)을 구분하고, 각 항목의 소스 줄을 가리킨다.
5. GDB에서 `copy_process`에 멈춰 부모·자식 두 `task_struct`를 비교하고 `task[nr]->tss.eax == 0`을 눈으로 확인한다.

**읽을 소스 범위** (원본 src/ 기준, course-plan 원문 계승):

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

**상태 변화도 / 모드·선택지 비교 범위** (원문 계승, 슬라이드 번호는 새 계획 번호로 환산):

- **상태 변화도 (필수, 슬라이드 28 · 원천 23)**: 범위 = "새 태스크 슬롯 `task[nr]`의 생애 초기". 상태: `비어 있음(task[nr]==NULL)` → `[find_empty_process가 nr 반환]` `예약됨(아직 NULL)` → `[get_free_page, task[nr]=p]` `페이지 확보` → `[*p=*current; state=UNINTERRUPTIBLE]` `부모 복사본(실행 불가)` → `[TSS 채움, copy_mem, 카운트 증가, GDT 등록]` `자식 준비` → `[state=TASK_RUNNING]` `실행 가능` → `[schedule → switch_to(nr)]` `자식 실행 중(사용자 모드, eax=0)`. 실패 전환: `copy_mem` 실패 → `task[nr]=NULL; free_page` → `비어 있음`. 각 화살표에 변경 데이터(`task[]`, `state`, `tss.*`, `ldt[].base`, `f_count`, `i_count`, GDT 항목)와 유지 조건(UNINTERRUPTIBLE 동안 `schedule()`이 고르지 않음).
- **부모 쪽 상태 (슬라이드 29 · 원천 24)**: 부모는 `copy_process` 내내 RUNNING·`current`. `sys_fork` 반환 후 `ret_from_sys_call`로 `iret` → 사용자 모드, EAX=last_pid. 자식과 부모의 "다시 실행되는 지점"을 한 그림에.
- **모드·선택지 비교 (필수, 슬라이드 30 · 원천 25)**: 범위 = "fork 시 자식이 받는 각 자원의 처리 방식". 선택지(처리 방식): ① 값 복사(`*p=*current`로 복사 후 일부 덮어씀) ② 새로 만듦 ③ 참조 공유 + 카운트 증가 ④ 페이지 테이블 복사 + 물리 페이지 읽기 전용 공유. 행(자원): `task_struct` 본문·시그널·시간(①, fork.c:81–91) / 커널 스택·TSS·pid·LDT base(②, 77–112, copy_mem 52–55) / `filp[]`·`pwd`·`root`·`executable`(③, 120–128) / 사용자 코드·데이터 페이지(④, copy_mem 56, memory.c:177–184). 축: 소스 줄, 자식이 바꾸면 부모에 보이는가, 해제 시점(`do_exit` 대칭 줄). CPU 모드·태스크 상태와 섞지 않는다.
- **보조 비교 (슬라이드 32 · 원천 27)**: 범위 = "`fork()` 반환값" — 부모(EAX=`last_pid`>0, fork.c:132) / 자식(EAX=0, `tss.eax`=0, fork.c:97) / 실패(EAX<0 → `_syscall0`이 `errno=-__res; return -1`, 원인 `find_empty_process`/`get_free_page`/`copy_mem`).

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 06. fork()와 프로세스 생성 | 표지 | 대제목 `06. fork()와 프로세스 생성` · 부제 = 핵심 질문 원문 "fork() 이후 부모와 자식은 어디에서 다시 실행되는가?" · 우상단 `Linux 0.11` 배지 + `1991`(ORANGE 채움) · 부제 아래 `Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)`(MUTED) · 회차 정보 `06/15 · 파트 B «실행의 길»` | — (course-plan 15회차 지도 표) | 표지 프레임(공통) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 1문장 큰 글씨(원문 그대로) · 답 예고(원천 표지 계승): "둘 다 `int $0x80` 다음 명령, 단 EAX가 다르다" — 끝에 GDB 시연 C로 보인다고 예고 · 오늘의 길 10단계 미니 지도 — 오늘은 질문→정리 10단계 전부 진행(지도 = 슬라이드 03·04), 비워 두는 단계 없음 · 재료 표시: 04(프레임)·05(TSS·`switch_to`) | — | 10단계 미니 지도(공통) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 15회차 A–G 타임라인: 완료 01–05(TEAL) · 오늘 06(ORANGE 채움+굵은 테두리, 파트 B의 마지막) · 이후 07–15(MUTED) · 앞→오늘·오늘→뒤 연결 화살표 2개와 문구(§3 명세) · 오늘 한 줄 문구(§3 명세) · 우하단 범례 + `Linux 0.11` 라벨 | — | 15회차 로드맵 도형(§4) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | 오늘 범위 TEAL 채움 = kernel/fork.c · kernel/system_call.s(kernel/ 프로세스 영역) + mm/memory.c(mm/ 메모리 영역 — 두 계층에 걸침) · ORANGE 데이터 흐름 화살표 1개: sys_fork → verify_area → copy_process → copy_mem → copy_page_tables(kernel/ → mm/로 건너는 마지막 구간 강조) · 누적 강조(옅은 TEAL) = 01–05 영역(§3 명세) · 사용자 공간 `init`·`sh`의 `fork()` 호출 지점 = 출발점 라벨(점선) | kernel/fork.c · kernel/system_call.s · mm/memory.c | 커널 전체 구조도(§4) |
| 05 | `fork()`의 약속 | 배경 | 사용자 관점 약속: 한 번 부르면 두 번 돌아온다 · 반환값: 부모에게 자식 pid, 자식에게 0, 실패 -1 · `init()`의 `if (!(pid=fork()))` 패턴 — 자식은 execve, 부모는 wait · 표어: "같은 코드, 같은 지점, 다른 값" | init/main.c:179–188 | main.c:179–188 코드 인용, 부모/자식 분기 2색 하이라이트 |
| 06 | 최초의 fork: main.c | 코드 | `move_to_user_mode()` 직후 task 0이 `fork()` → task 1(`init()`) · 코드: `if (!fork()) { init(); }` · `static inline _syscall0(int,fork)` — fork가 inline이어야 하는 이유: task 0의 사용자 스택이 자식과 공유되므로 함수 호출로 스택을 쓰면 안 됨(주석 12–24) · task 0의 특수성은 05에서 다룬 것으로 간단히만 | init/main.c:12–24, 137–140 | 코드 인용 2스크린(주석 12–24, 본문 137–140) |
| 07 | `_syscall0(int,fork)` | 코드 | `unistd.h:133–144` 전개: `int fork(void){ long __res; asm("int $0x80":"=a"(__res):"0"(2)); … }` · `__NR_fork=2`(unistd.h:62) → `sys.h:74` sys_call_table 세 번째 항목 `sys_fork` · 04회차 `_syscall3`과 차이는 인자 없음뿐 | include/unistd.h:62, 133–144 · include/linux/sys.h:74 | 코드 인용 + 매크로 전개 대비 |
| 08 | 04회차 프레임 다시 | 코드 | `system_call.s:17–31` 12슬롯 스택 배치 주석 그림 재게시 · `_system_call:80–94`가 push한 ds/es/fs/edx/ecx/ebx + CPU가 push한 eip/cs/eflags/esp/ss · 예고: "이 스택이 자식의 TSS 재료가 된다" | kernel/system_call.s:17–31, 80–94 | 04회차 프레임 12슬롯 그림 재게시(§4) |
| 09 | `sys_fork`는 C 함수가 아니다 | 코드 | `sys.h:3` `extern int sys_fork();` 선언뿐 — 정의는 `system_call.s:208–219` 어셈블리 · 이유: `copy_process`에 넘길 레지스터(gs, esi, edi, ebp)가 `_system_call`에서 push되지 않았으므로 어셈블리에서 추가 push 필요 | include/linux/sys.h:3 · kernel/system_call.s:208–219 | 코드 인용(선언 vs 정의 대비) |
| 10 | `_sys_fork` 한 줄씩 (1): nr 확보와 실패 복귀 | 코드 | `system_call.s:208–211`: 209 `call _find_empty_process` → eax=nr · 210–211 nr이 음수면 `1: ret`(실패 — `-EAGAIN`이 그대로 사용자 반환 경로) · `find_empty_process` 내부 읽기는 슬라이드 14에서 | kernel/system_call.s:208–211 · include/errno.h:30 | 코드 인용 + 흐름 화살표 |
| 11 | `_sys_fork` 한 줄씩 (2): 5개 push와 `call _copy_process` | 코드 | 212–216 `push %gs; pushl %esi; pushl %edi; pushl %ebp; pushl %eax`(nr) — C 호출 규약 역순으로 `copy_process` 인자 완성 · 217 `call _copy_process` · 218 `addl $20,%esp`(5개 정리) · 219 `ret` → `_system_call:95`의 `pushl %eax` | kernel/system_call.s:212–219, 95 | 코드 인용 + push 스택 성장 그림 |
| 12 | 17개 인자 = 스택 17슬롯 | 코드 | `fork.c:68–71` 시그니처와 스택 그림 나란히 · 분류: `nr,ebp,edi,esi,gs`(sys_fork가 push) / `none`(`_system_call`의 `call _sys_call_table`이 남긴 복귀 주소) / `ebx,ecx,edx,fs,es,ds`(_system_call push) / `eip,cs,eflags,esp,ss`(CPU push) · C 함수는 그저 스택을 인자로 읽는다 | kernel/fork.c:68–71 · kernel/system_call.s:17–31, 80–94, 208–219 | 17슬롯↔인자 1:1 대응 그림(§4) |
| 13 | `none`의 정체 | 코드 | `_sys_fork`는 `call`로 들어왔으므로 `_system_call:94`의 복귀 주소가 ebx 아래에 있다 · `copy_process`는 이를 `none`으로 받아 무시 · 그림: `call` 두 번(`_sys_call_table` → `_sys_fork`, `_sys_fork` → `_copy_process`)의 복귀 주소 위치 | kernel/system_call.s:94 · kernel/fork.c:68–71 | call 두 번 복귀 주소 위치 그림(§4) |
| 14 | `find_empty_process` | 코드 | `last_pid`(fork.c:22) 증가, 음수 넘침 시 1 · `repeat`: 살아 있는 task 중 같은 pid가 있으면 다시 증가 · `task[1..63]` 중 NULL인 첫 인덱스 반환, 없으면 `-EAGAIN`(errno.h:30) · pid와 슬롯 번호 nr이 다른 값임을 강조 | kernel/fork.c:135–147, 22 · include/errno.h:30 | 코드 인용 + repeat 루프 도식 |
| 15 | pid vs nr | 배경 | 표: pid = 전역 증가, 사용자에게 보이는 번호 / nr = `task[]` 인덱스 1~63, TSS·LDT GDT 위치 `_TSS(nr)`, 선형 주소 base `nr*0x4000000` · 같은 pid 1이라도 재부팅마다 nr은 같고, pid 100번대도 nr은 작을 수 있음 · 이 대응이 이해 확인 4번·07회차 예고의 기초 | kernel/fork.c:135–147, 52 · include/linux/sched.h:155–156 | pid vs nr 2열 비교표(§4) |
| 16 | `copy_process` (1): 페이지 하나 = task_struct + 커널 스택 | 코드 | `get_free_page()`(memory.c:63) → 4 KiB 한 페이지 · `task[nr]=p`, `*p = *current` — 구조체 대입 한 줄로 부모 전부 복사 · 주석 "doesn't copy the supervisor stack": 자식 커널 스택은 비어 있다 · 따라서 자식은 커널 안의 어디로도 "돌아갈" 곳이 없고 TSS의 eip/esp로 곧장 사용자 모드로 간다 | kernel/fork.c:77–81 · mm/memory.c:63 | 페이지 배치 그림(task_struct + 빈 커널 스택) |
| 17 | `copy_process` (2): 덮어쓰는 필드 | 코드 | `state=TASK_UNINTERRUPTIBLE`(아직 고르지 말 것), `pid=last_pid`, `father=current->pid` · `counter=priority`(05: 새 태스크는 꽉 찬 타임 슬라이스), `signal=0`, `alarm=0`, `leader=0`, 시간 0, `start_time=jiffies` · 복사된 채 남는 것: `priority`, `blocked`, `sigaction[]`, uid/gid, `umask`, `tty`, `close_on_exec` | kernel/fork.c:82–91 | 코드 인용 + 복사/덮어씀 2색 표시 |
| 18 | `copy_process` (3): TSS 채우기 — esp0·ss0·eip·eflags·eax | 코드 | 93 `esp0 = PAGE_SIZE+(long)p`(커널 스택 = 자기 페이지 끝, 05의 esp0), 94 `ss0=0x10` · 95 `eip=eip`(int 0x80 다음 명령), 96 `eflags` · **97 `eax = 0`** — "자식은 0을 받는다"의 시드 · 05회차 `tss_struct`(sched.h:51–76) 필드 이름과 대조 | kernel/fork.c:92–97 · include/linux/sched.h:51–76 | TSS 필드 채움 지도 (1)(§4) |
| 19 | `copy_process` (3): TSS 채우기 — 범용 레지스터·세그먼트·ldt | 코드 | 98–104 ecx/edx/ebx/esp/ebp/esi/edi = 스택 값 그대로, `esp=esp`(부모의 사용자 ESP) · 105–110 세그먼트 `& 0xffff` · 111 `ldt=_LDT(nr)`, 112 `trace_bitmap` · 그림: 04 프레임 슬롯 → TSS 필드 화살표 | kernel/fork.c:98–112 · include/linux/sched.h:155–156 | TSS 필드 채움 지도 (2)(§4) |
| 20 | 왜 `tss.eax = 0`이 "자식은 0을 받는다"가 되는가 | 코드 | 05회차 `switch_to`(sched.h:171–184): `ljmp` TSS 전환 시 CPU가 TSS의 eax…eip…esp를 전부 로드 · 자식이 처음 선택되면 레지스터 = TSS 값 → EIP는 `int $0x80` 다음, CS=0x0f(사용자), EAX=0 · `_syscall0`의 `"=a"(__res)`가 0을 읽어 `return 0` · 부모는 `ret_from_sys_call`의 `popl %eax`로 `last_pid` | kernel/fork.c:97 · include/linux/sched.h:171–184 · include/unistd.h:133–144 · kernel/system_call.s:95, 121 | switch_to TSS 복원 개념도(§4, 05 재게시) |
| 21 | `copy_process` (4): `copy_mem` | 코드 | `get_limit(0x0f)`/`get_limit(0x17)` 현재 LDT 한계, `get_base(current->ldt[1]/[2])` · 48–51 코드·데이터 base가 다르면 panic(분리 I&D 금지) · 52 `new_base = nr*0x4000000`(64 MiB × nr), 53–55 `p->start_code`, `set_base(ldt[1])`, `set_base(ldt[2])` · 56 `copy_page_tables(old,new,data_limit)` 실패 시 `free_page_tables` 되돌림 + `-ENOMEM` | kernel/fork.c:39–61 · include/linux/sched.h:211–212, 226 · include/errno.h:31 | 코드 인용 |
| 22 | 자식의 주소 공간은 "번호 × 64 MiB" | 배경 | 그림: 선형 주소 공간 4 GiB를 nr별 64 MiB 칸으로 · 부모 nr=1 → 0x4000000, 자식 nr=2 → 0x8000000 · 사용자 코드의 주소 0은 LDT base 덕에 서로 다른 선형 주소 · 07회차 핵심 질문("같은 숫자 주소가 두 프로세스에서 왜 다른 메모리")의 절반이 여기 — 페이징은 07로 넘김 | kernel/fork.c:52–55 | 4 GiB nr×64 MiB 칸 그림(§4) |
| 23 | `copy_process` (5): 공유 카운트 | 코드 | `filp[i]->f_count++`(fs.h:119) · `pwd/root/executable->i_count++`(fs.h:107) · 포인터는 `*p=*current`로 이미 복사됐고 같은 객체를 가리키므로 카운트만 증가 | kernel/fork.c:120–128 · include/linux/fs.h:107, 119 | 코드 인용 + 같은 객체 가리킴 그림 |
| 24 | `copy_process` (6): GDT 등록·RUNNING·반환 | 코드 | 129–130 GDT에 TSS/LDT 설명자 등록(`set_tss_desc`/`set_ldt_desc`, system.h:65–66) · `_TSS(n)`·`_LDT(n)` GDT 인덱스 계산 복습(sched.h:155–156) · 131 `state=TASK_RUNNING` "do this last" · 132 `return last_pid` | kernel/fork.c:129–132 · include/linux/sched.h:155–156 · include/asm/system.h:65–66 | 코드 인용 + GDT 슬롯 그림(02·05 재활용) |
| 25 | `copy_page_tables`: 결과만 (참고) | 코드 | 오늘 읽는 범위: 163–171 새 페이지 테이블 한 장 `get_free_page`, 디렉터리 항목 `\|7` · 172 `from==0`이면 0xA0개 = task 0의 640 KiB만 · 177 `this_page &= ~2`(쓰기 금지), 179–184 `mem_map[]++` 부모 항목도 쓰기 금지로 바꿈 · 187 `invalidate()`(memory.c:39, CR3 재로드) · 내부 비트 의미는 07, 쓰기 시 일어나는 일은 08 | mm/memory.c:150–189, 39 | 코드 인용(읽는 줄만 하이라이트) |
| 26 | 복사된 것은 "표", 공유된 것은 "페이지" | 배경 | 그림: 부모 페이지 테이블 → 자식 페이지 테이블(새 페이지, 항목 복사) → 둘 다 같은 물리 페이지를 R/O로 · `mem_map` 카운트 2 · "fork는 메모리를 복사하지 않는다"의 정확한 의미 · 08회차 예고: 자식이 쓸 때 어떻게 되는지 | mm/memory.c:163–184 | 페이지 테이블 복사·R/O 공유 그림(§4) |
| 27 | 자식의 첫 실행 경로 | 코드 | 05 `schedule()`(sched.c:104–142): 자식 counter=priority(가득)이므로 곧 선택될 가능성 높음 · `switch_to(nr)` → `ljmp` → CPU가 자식 TSS 로드 · CS:EIP = 0x0f:(int 0x80 다음) → `_syscall0` 뒷부분 `if (__res>=0) return 0` · 자식은 `ret_from_sys_call`을 거치지 않는다(커널 스택이 비어 있으므로) | kernel/sched.c:104–142 · include/linux/sched.h:171–184 · include/unistd.h:133–144 | 실행 경로 순서도 |
| 28 | 상태 변화도: `task[nr]` 슬롯의 탄생 | 상태도 | 상태 6개(비어 있음 → 예약 → 페이지 확보 → 부모 복사본·UNINTERRUPTIBLE → 자식 준비 → RUNNING → 자식 실행 중) — 원천 표기 그대로 · 각 화살표에 원인 코드(fork.c 줄), 변경 데이터(`task[nr]`, `state`, `tss.*`, `ldt[].base`, `f_count`, `i_count`, GDT), 유지 조건(UNINTERRUPTIBLE 동안 `schedule()` 선택 제외) · 실패 화살표: 115–118 `task[nr]=NULL; free_page` → 비어 있음 | kernel/fork.c:77–132 | 상태 다이어그램(§4) |
| 29 | 두 태스크가 다시 실행되는 지점 | 상태도 | 한 그림에 부모·자식 병렬 · 부모: `copy_process` return → `_sys_fork ret` → `_system_call:95 pushl %eax` → `ret_from_sys_call` → `iret` → 사용자, EAX=pid · 자식: (나중에) `switch_to` → TSS → 사용자, EAX=0 · 공통: 같은 EIP, 같은 ESP 값(단 선형 주소는 base가 달라 다른 페이지 테이블을 통함), 같은 EFLAGS · 상태도와 구분되는 "호출 순서도" | kernel/fork.c:92–97, 132 · kernel/system_call.s:95, 208–219 · include/linux/sched.h:171–184 | 부모·자식 재개 지점 순서도(§4) |
| 30 | 비교: 자식이 받는 자원의 처리 방식 | 비교 | 행 = 자원: `task_struct` 본문·시그널·시간(① 값 복사, fork.c:81–91) / 커널 스택·TSS·pid·LDT base(② 새로 만듦, 77, 92–112, 52–55) / `filp[]`·`pwd`·`root`·`executable`(③ 참조 공유+카운트, 120–128) / 사용자 코드·데이터 페이지(④ 테이블 복사+R/O 공유, 56, memory.c:177–184) · 열: 소스 줄 · 자식이 바꾸면 부모에 보이는가(아니오/아니오/예: f_pos 공유/08회차 전까지 쓰기 불가) · 해제 대칭: `do_exit`(exit.c:106–107, 115–123), `release`(exit.c:20–33) · CPU 모드·태스크 상태와 섞지 않는다 | kernel/fork.c:56, 77–128 · mm/memory.c:177–184 · kernel/exit.c:20–33, 106–123 | 자원 처리 비교표(§4) |
| 31 | `f_count`가 뜻하는 것 | 코드 | `struct file`(fs.h:116–119)은 열린 파일 하나의 오프셋(`f_pos`)을 가짐 · 부모·자식이 같은 `struct file`을 가리키므로 한쪽이 `write`하면 다른 쪽 `f_pos`도 움직임 · `do_exit`의 `sys_close`(exit.c:115–117)가 카운트를 줄임 · 12회차에서 inode와 함께 다시 | include/linux/fs.h:116–119 · kernel/fork.c:120–122 · kernel/exit.c:115–117 | 코드 인용 + f_pos 공유 그림 |
| 32 | 비교: `fork()` 반환값 세 가지 | 비교 | 부모: `last_pid`(fork.c:132 → EAX 슬롯 → `popl %eax`) · 자식: 0(fork.c:97 `tss.eax`) · 실패: `-EAGAIN`(find_empty_process 146, get_free_page 실패 79, copy_mem 실패 118) → `_syscall0:142–143` `errno=11; return -1` · 열: 값, 출처 줄, 사용자 코드 분기(`main.c:179–186`) | kernel/fork.c:79, 97, 118, 132, 146 · include/unistd.h:142–143 · init/main.c:179–186 | 반환값 3행 비교표(§4) |
| 33 | 시연 환경 | 시연 | lab QEMU `-s -S` + GDB `target remote :1234`, 셸 프롬프트까지 부팅 후 중단점 · 트리거: `copy_process`는 셸이 명령을 실행할 때마다 호출 — 게스트 셸에서 `ls` 한 번 · 심볼명은 lab 빌드 기준(`info functions copy_process`) · 실패 시 사전 캡처 | kernel/fork.c:68 | 터미널·GDB 레이아웃 안내 |
| 34 | 시연 A: `break copy_process`, 인자 확인 | 시연 | 게스트 `ls` → `copy_process` 정지 · `info args`로 nr, eip, cs, eflags, esp, ss 확인 — 인자에 eax 없음! · `p/x cs`=0xf, `p/x ss`=0x17, `p/x eip`(사용자 주소, `int 0x80` 다음) · `p nr`, `p last_pid` | kernel/fork.c:68–71 · kernel/system_call.s:17–31 | 실화면 투영(캡처는 35) |
| 35 | 캡처 A: `info args` | 캡처 | 17개 인자 값 캡처 게시 · 슬라이드 12 스택 그림과 대조: `none`은 커널 주소(`_system_call` 안), `cs`=0xf/`ss`=0x17는 사용자 · 각주: lab 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 | kernel/fork.c:68–71 | materials/06-fork/captures/01-info-args-17params.png |
| 36 | 시연 B-1: 두 `task_struct` 비교 | 시연 | `finish`(copy_process 반환, Value returned = pid) 직후 · `p *current`와 `p *task[nr]`를 pid/father/state/counter/priority/start_time/filp[0] 필드만 추려 비교 · 필드 지정: `p current->pid`, `p task[<nr>]->pid`, `p task[<nr>]->father`, `p task[<nr>]->state`, `p task[<nr>]->filp[0]`, `p current->filp[0]` | kernel/fork.c:82–91, 120–128 | 실화면 투영(캡처는 37) |
| 37 | 캡처 B-1: 부모·자식 필드 대조 | 캡처 | 두 열 표로 캡처: pid 다름, father = 부모 pid, state 둘 다 0 · counter(자식 = priority) · `filp[0]` 같은 포인터, `filp[0]->f_count` 증가 · 각주 포함 | kernel/fork.c:82–91, 120–128 | materials/06-fork/captures/02-task-parent-vs-child.png |
| 38 | 시연 B-2: `tss.eax == 0`, `tss.eip` | 시연 | `p task[<nr>]->tss.eax`(0), `p/x task[<nr>]->tss.eip`, `p/x task[<nr>]->tss.esp`, `p/x task[<nr>]->tss.cs`(0xf) · `p/x task[<nr>]->tss.esp0`(= task 페이지 + 0x1000), `p/x task[<nr>]->tss.ldt`, `p/x task[<nr>]->ldt[2]`(base 비트에 nr*0x4000000) · `p/x current->tss.eax`는 아직 전환 전 값이라 의미 없음을 설명 | kernel/fork.c:92–112 | 실화면 투영(캡처는 39) |
| 39 | 캡처 B-2: 자식 TSS | 캡처 | 캡처: `tss.eax=0`, `tss.eip`=시연 A의 `eip` 인자와 동일 · `tss.esp0`=`task[nr]`+4096 · 각주 포함 | kernel/fork.c:93–97 | materials/06-fork/captures/03-child-tss.png |
| 40 | 시연 C: 자식이 처음 실행되는 순간 | 시연 | `break *<tss.eip 값>`(사용자 주소) — 부모도 같은 EIP를 지나므로 걸릴 때마다 `p/x $eax` 확인: 한 번은 pid, 한 번은 0 · `p/x $cs`=0xf, `p/x $eax` · 부모·자식 중 누가 먼저 걸리는지는 실행마다 다름을 미리 말함 | kernel/fork.c:95–97 · include/linux/sched.h:171–184 | 실화면 투영(캡처는 41) |
| 41 | 캡처 C: 같은 EIP, 다른 EAX | 캡처 | 두 번 정지 캡처: 같은 `$eip`, `$eax`=pid / 0 — 질문에 대한 실물 답 · 각주: 환경·순서는 실행마다 다름 · 관찰(EIP·EAX 값)과 추론(TSS 로드 순서)을 구분 | kernel/fork.c:95–97 | materials/06-fork/captures/04-same-eip-two-eax.png |
| 42 | 관찰 vs 추론 | 시연 | 관찰(캡처 01–04): cs=0xf/ss=0x17, `tss.eax==0`, `tss.eip`==시연 A eip, `filp[0]` 같은 주소·`f_count`≥2, 같은 `$eip`에서 `$eax` pid/0 · 추론(코드): 자식은 TSS 복원으로 곧장 사용자 모드(`switch_to` ljmp), 부모는 `ret_from_sys_call`→`iret`, 순서 비보장 이유(counter·`schedule()`) · 캡처 각주 필수 항목 재확인(00-common §7) | kernel/fork.c:77–132 · kernel/system_call.s:80–95, 208–219 · kernel/sched.c:104–142 | 관찰/추론 두 열 표(§4) |
| 43 | 질문의 답 | 정답 | 답: "둘 다 `int $0x80` 다음 명령에서. 부모는 `ret_from_sys_call`→`iret`로, 자식은 `switch_to`→TSS 복원으로 도착하며, 차이는 EAX(pid vs 0)와 LDT base(선형 주소)뿐." · 경로 두 줄(부모/자식) + 파일:줄 표기 · 슬라이드 41 캡처가 이 답의 실물 근거 | kernel/system_call.s:95, 121, 208–219 · kernel/fork.c:92–97, 132 · include/linux/sched.h:171–184 | 두 경로 나란히 정리(29 그림 축소판) |
| 44 | fork가 하지 않는 일 | 정리 | 메모리 복사 — 페이지 테이블만 복사(실제 복사는 쓰기 시점, 08) · 커널 스택 복사 — 비어 있음(TSS로 직행) · `struct file` 복사 — 공유 + 카운트(12) · 프로그램 교체 — 09 exec · 각 항목에 해당 회차 번호 | kernel/fork.c:56, 77–81, 120–128 · mm/memory.c:150–189 | 4항목 회차 매핑 표 |
| 45 | 흔한 오해 바로잡기 | 정리 | "자식은 `copy_process`에서 반환해 돌아온다" — 아니다, 커널 스택이 없어 TSS에서 곧장 사용자로 · "fork는 메모리를 복제한다" — R/O 공유 · "pid = task 인덱스" — 별개 · "`*p=*current`가 전부 복사하니 파일도 복사된다" — 포인터 복사 = 공유 | kernel/fork.c:77–81, 97, 120–128, 135–147 · mm/memory.c:177–184 | 오해/실제 대조 4행 |
| 46 | 현대 커널 한 줄 | 정리 | 현대 Linux `fork`/`clone`도 `copy_process`라는 이름이 남아 있고 COW도 같다 · 차이: 자식의 첫 실행은 `ret_from_fork` 커널 스택 프레임으로 돌아간다(TSS 전환 아님) · 상세 비교는 14회차 · "0.11에는 없다/다르다" 명시 | — (원본 src/ 밖 — 현대 커널 참고, 14회차 상세) | 한 줄 비교 강조 |
| 47 | 이해 확인 질문 | 확인 | §6의 4문항 게시 · 각 문항 옆에 관련 슬라이드 번호(18·20·43 / 16 / 31 / 22·26) 표시 · 정답은 강사 구두 공개 후 §6 원문으로 정리 | kernel/fork.c 전반 | 4문항 나열 |
| 48 | 정리와 다음 회차 | 정리 | 정리 4줄: 진입 경로 `_syscall0`→`sys_call_table[2]`→`_sys_fork`→`copy_process` · 자원 = 값 복사·새로 만듦·참조 공유·R/O 페이지 · 자식 첫 실행 = TSS 복원, EAX=0 · 07 예고: "`nr*0x4000000` base와 `copy_page_tables`가 만든 표 — 같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가?" · 08 예고: "`this_page &= ~2` 뒤 자식이 쓰면?" | kernel/fork.c:39–61 · mm/memory.c:150–189, 177 | 정리 4줄 + 07·08 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: B «실행의 길» (04 인터럽트·시스템 콜 · 05 스케줄링 · 06 fork) — 06은 파트 B의 마지막 회차.
- 완료(TEAL) = 01–05, 오늘(ORANGE 채움 + 굵은 테두리) = 06, 이후(MUTED) = 07–15.
- 오늘 한 줄 문구: **"여섯째 태스크를 만드는 `copy_process` — TSS에 출발점을 심는다"**.
- 앞→오늘 연결 화살표 문구: **"05: `switch_to`가 TSS를 통째로 복원한다 → 06: 그 TSS를 새로 채우는 곳, 여섯째 태스크를 만드는 `copy_process`"**.
- 오늘→뒤 연결 화살표 문구: **"06: `copy_page_tables`가 페이지를 어떻게 복사하는가(오늘은 결과만) → 07: 주소 변환 — 같은 숫자 주소가 왜 다른 메모리를 가리키는가"**.
- 원천 "15회차 지도" 슬라이드 내용 계승: 재료 = 04(프레임)·05(TSS·`switch_to`) · 07·08(페이지 테이블·COW)은 오늘 `copy_mem`에서 "결과만" 보고 넘기는 부분 · 09(exec)·10(exit/wait)은 fork의 뒤.
- 우하단 범례(■ 완료 TEAL · ▶ 오늘 ORANGE · □ 이후 MUTED) + `Linux 0.11` 라벨.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트(TEAL 채움): **kernel/fork.c, kernel/system_call.s**(kernel/ 프로세스 영역 — 진입 sys_call_table 포함) + **mm/memory.c**(mm/ 메모리 영역 — kernel/와 mm/ 두 계층에 걸침).
- 오늘의 데이터 흐름 화살표(ORANGE, 1개 체인): **sys_fork → verify_area → copy_process → copy_mem → copy_page_tables** — kernel/에서 mm/로 건너는 마지막 구간(copy_mem → copy_page_tables)을 굵게.
- 누적 강조(옅은 TEAL, 01–05 영역): boot/bootsect.s·boot/setup.s·boot/head.s(01–03), init/main.c(01·03), kernel/system_call.s·kernel/asm.s·kernel/traps.c(04), include/unistd.h·include/linux/sys.h(04), kernel/sched.c·include/linux/sched.h(02·05), include/asm/system.h(02).
- 사용자 공간 박스의 `init`·`sh` 라벨에 "오늘의 출발점 — `fork()` 호출" 점선 라벨(04회차 프레임의 위쪽 절반과 이어짐).
- 계층 경계(CPL=3/CPL=0, IRQ) 라벨 + 우하단 `Linux 0.11` 라벨은 공통 골격 그대로.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵 (파트 A–G) | 도형 | 파트 A–G 상자 15칸, 완료 01–05 TEAL·오늘 06 ORANGE·이후 07–15 MUTED, 연결 화살표 2개+문구(§3), 우하단 범례·Linux 0.11 라벨 | 공통 골격(04·05와 동일) |
| 04 | 커널 전체 구조도 | 도형 | kernel/fork.c·kernel/system_call.s·mm/memory.c TEAL 채움, ORANGE 흐름 화살표(sys_fork→verify_area→copy_process→copy_mem→copy_page_tables), 01–05 영역 옅은 TEAL(§3) | 공통 골격 + 04·05 강조 영역 |
| 08 | 시스템 콜 진입 12슬롯 스택 프레임 | 도형 | ds/es/fs/edx/ecx/ebx(_system_call push) + eip/cs/eflags/esp/ss(CPU push) 슬롯 세로 그림 | 04회차 프레임 그림 재게시 |
| 12 | 17슬롯 ↔ `copy_process` 인자 대응 | 도형 | 좌 = 스택 다이어그램, 우 = fork.c:68–71 시그니처, push 주체별 색 구분(sys_fork 5개 / none / _system_call 6개 / CPU 5개) | 04회차 프레임 골격 |
| 13 | `call` 두 번과 복귀 주소 위치 | 도형 | `_system_call:94` call → `_sys_fork` → `call _copy_process` 스택 단면, 복귀 주소 2개 위치 표시(ebx 아래 none 강조) | 슬라이드 12 그림 확장 |
| 15 | pid vs nr 비교표 | 표 | pid/nr 두 열 — 발급 방식·범위·용도(GDT `_TSS(nr)`, 선형 base `nr*0x4000000`)·보이는 주체 | — |
| 18 | TSS 필드 채움 지도 (1) | 도형 | fork.c:92–97 — esp0/ss0/eip/eflags/eax가 어느 스택 슬롯·상수에서 오는지 화살표, 97 `eax=0` ORANGE 강조 | 05 tss_struct 그림 |
| 19 | TSS 필드 채움 지도 (2) | 도형 | fork.c:98–112 — 범용 레지스터(스택 값 그대로), 세그먼트 `& 0xffff`, `ldt=_LDT(nr)` | 05 tss_struct·02 GDT/LDT 그림 |
| 20 | `switch_to` TSS 복원 개념도 | 도형 | ljmp → CPU가 TSS의 eax…eip…esp 전부 로드 → 사용자 모드 진입(CS=0x0f, EAX=0) | 05 switch_to 그림 재게시 |
| 22 | 선형 주소 공간 nr×64 MiB 칸 | 도형 | 4 GiB 가로 띠를 64 MiB 칸으로, task 0·nr=1(0x4000000)·nr=2(0x8000000) 표시, 같은 논리 주소가 선형 주소로 갈라지는 화살표 | — (07회차에서 확장 재사용) |
| 26 | 페이지 테이블 복사·R/O 공유 | 도형 | 부모 디렉터리→테이블→물리 페이지, 자식 새 테이블(항목 복사), 양쪽 같은 물리 페이지 R/O, `mem_map` 카운트 2 | — (07·08에서 확장 재사용) |
| 28 | `task[nr]` 슬롯 상태 변화도 | 상태 다이어그램 | 상태 6개(§1 범위 그대로), 화살표마다 fork.c 줄·변경 데이터·유지 조건, 실패 전환(115–118) 별도 색 | — |
| 29 | 부모·자식 재개 지점 순서도 | 도형 | 부모 경로(copy_process→ret→ret_from_sys_call→iret)와 자식 경로(switch_to→TSS→사용자) 병렬, 같은 EIP 도착점 정렬 | 05 schedule·switch_to 골격 |
| 30 | 자원 처리 방식 비교표 | 표 | 행 4자원 × 선택지 ①–④, 열 = 소스 줄·부모 가시성·해제 대칭 | — |
| 32 | 반환값 세 가지 비교표 | 표 | 부모/자식/실패 × 값·출처 줄·사용자 분기 | — |
| 37 | 부모·자식 필드 대조 캡처 프레임 | 캡처 프레임 | 캡처 02를 두 열 표로 정리(pid/father/state/counter/filp[0]/f_count) | — |
| 41 | 같은 EIP 두 번 정지 나란히 | 캡처 프레임 | 캡처 04 두 화면 나란히, `$eax` 값만 ORANGE 강조 | — |
| 42 | 관찰 vs 추론 두 열 | 표 | 좌 = 관찰(캡처 01–04에서 읽은 값), 우 = 추론(코드 근거 + 회차 예고) | — |

상단 미니 지도(10단계 띠)·푸터(`Linux 0.11 커널 강좌 · 06/15 · 06-fork` + `MM / 48`)·표지 배지는 공통 프레임(scripts/make_slides.py)이므로 이 목록에서 제외한다.

## 5. 캡처 목록 (강사 시연)

공통: lab QEMU `-s -S`, GDB `target remote :1234`, 셸 프롬프트까지 부팅 후 중단점. 트리거는 게스트 셸에서 `ls`(셸이 fork → exec). 심볼명은 lab 빌드 기준.

| 시연 | 캡처 파일(materials/06-fork/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A. `copy_process` 인자 (슬라이드 34–35) | 01-info-args-17params.png | `break copy_process` · 게스트 `ls` · `info args` · `p/x cs` · `p/x ss` · `p/x eip` · `p/x esp` · `p nr` · `p last_pid` | `cs=0xf`, `ss=0x17`, `eip`·`esp`는 사용자 공간 값(작은 주소, 셸 바이너리 내부), `nr`은 비어 있던 작은 인덱스(예: 2~4), `last_pid` = 곧 자식 pid, 인자 목록에 `eax`가 없음 | 사전 캡처 1장 |
| B-1. 부모·자식 `task_struct` (슬라이드 36–37) | 02-task-parent-vs-child.png | `finish`(Value returned = pid) · `set $c = task[<nr>]` · `p $c->pid` · `p $c->father` · `p current->pid` · `p $c->state` · `p $c->counter` · `p $c->priority` · `p $c->filp[0]` · `p current->filp[0]` · `p $c->filp[0]->f_count` | `father == current->pid`, `state == 0`, `counter == priority`, `filp[0]` 두 값이 같은 주소, `f_count` ≥ 2 | 사전 캡처 2장(필드 대조, TSS) |
| B-2. 자식 TSS (슬라이드 38–39) | 03-child-tss.png | `p $c->tss.eax` · `p/x $c->tss.eip` · `p/x $c->tss.esp` · `p/x $c->tss.cs` · `p/x $c->tss.esp0` · `p/x $c` · `p/x $c->tss.ldt` | `tss.eax == 0`, `tss.eip` == 시연 A의 `eip`, `tss.esp0 == (long)$c + 0x1000`, `tss.ldt == (nr<<4)+(5<<3)` | 사전 캡처(위 B와 동일 세트) |
| C. 같은 EIP, 다른 EAX (슬라이드 40–41) | 04-same-eip-two-eax.png | `break *<시연 B의 tss.eip>` · `delete` 나머지 · `c` → `p/x $eax` · `p/x $cs` · `c` → 다시 `p/x $eax` | 두 번 정지, 같은 `$eip`, `$cs=0xf`, `$eax`가 한 번은 pid(양수), 한 번은 0 — 순서는 스케줄러에 달림(자식 counter가 가득이라 자식이 먼저인 경우가 많으나 보장 아님) | 사용자 주소 중단점이 QEMU gdbstub에서 같은 선형 주소를 쓰는 다른 태스크에도 걸릴 수 있음 → `$eax`·`current->pid`로 걸러낸다. 실패 시 사전 캡처 2장 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜`. 사전 캡처는 화면 모서리에 `기존 기록` 라벨.

## 6. 이해 확인 질문과 정답 (해당 슬라이드 번호 명시)

게시 슬라이드: **47** (관련 시연·캡처 = 34–41).

1. **Q.** `copy_process`의 인자에 `eax`가 없는데 자식의 EAX는 어떻게 정해지는가? 부모의 반환 EAX는? — (관련 슬라이드 18·20·43) **A.** 자식: `p->tss.eax = 0`(fork.c:97)을 직접 쓴다. 부모: `copy_process`가 `last_pid`를 반환(132) → `_sys_fork ret` → `_system_call:95 pushl %eax` → `ret_from_sys_call:121 popl %eax` → `iret`.
2. **Q.** `*p = *current`(fork.c:81) 한 줄이 복사하는 것과 복사하지 않는 것을 하나씩. — (관련 슬라이드 16·17) **A.** 복사: `task_struct` 전체(pid, filp 포인터, ldt, tss 포함, 이후 일부 덮어씀). 미복사: 같은 페이지 뒤쪽의 커널 스택(주석 "doesn't copy the supervisor stack") — 그래서 자식은 커널 안에서 돌아갈 곳이 없고 TSS로 바로 사용자 모드.
3. **Q.** 부모가 fork 직후 `write(fd,…)`를 두 번 하면 자식의 `fd` 오프셋은? — (관련 슬라이드 23·31) **A.** 같이 움직인다. `filp[fd]`가 같은 `struct file`을 가리키고(`*p=*current`로 포인터 복사, 120–122는 `f_count`만 증가) `f_pos`가 그 안에 있다(fs.h:116–119).
4. **Q.** `copy_mem`이 `nr*0x4000000`을 base로 쓰는데, 자식이 사용자 주소 0x1000을 읽으면 선형 주소는? 이 주소에 대응하는 물리 페이지는 부모와 같은가? — (관련 슬라이드 21·22·26) **A.** 선형 주소 = `nr*0x4000000 + 0x1000`. 물리 페이지는 **같다**(`copy_page_tables`가 항목을 복사하고 `this_page &= ~2`로 양쪽 R/O, memory.c:177–180). 쓰기 전까지 공유. 쓰면 08회차.

## 7. 처음 등장하는 용어 (용어 | 정의 | 첫 등장 슬라이드)

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| `copy_process` | 새 task_struct를 만들고 TSS·LDT·공유 카운트를 채우는 fork의 본체. | 03(로드맵 연결 문구) → 본문 16 |
| `find_empty_process` | 새 pid와 빈 `task[]` 인덱스(nr)를 정함. | 10(호출) → 본문 14 |
| nr(태스크 번호) | `task[]` 인덱스. pid와 다름. | 10 → 대비 표 15 |
| `last_pid` | 마지막으로 발급한 pid. | 14 |
| `copy_mem` | LDT base 설정 + 페이지 테이블 복사 호출. | 04(구조도 화살표) → 본문 21 |
| LDT base `nr*0x4000000` | 태스크별 64 MiB 선형 주소 칸. | 15 → 그림 22 |
| `copy_page_tables` | 페이지 테이블 복사(물리 페이지는 공유). 07·08회차 상세. | 04(구조도 화살표) → 본문 25 |
| `mem_map` | 물리 페이지별 참조 카운트 배열. | 25 → 그림 26 |
| `f_count` / `i_count` | `struct file` / inode 공유 카운트. | 23 → 심화 31 |
| `tss.esp0` | 자식이 다음에 커널로 들어올 때 쓸 커널 스택(자기 페이지 끝). | 18 |
| `-EAGAIN` / `-ENOMEM` | fork 실패 코드(errno.h:30–31). | 14 / 21 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 그대로 계승)

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

## 9. 120분 운영안 (새 슬라이드 번호: 범위 | 분 | 진행)

단계별 분 배분은 원천(5·15·20·25·10·15·22·5·3 = 120분)을 그대로 유지했다.

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 핵심 질문, 표준 앞부분 — 로드맵·구조도로 "05 TSS 전환·04 프레임 위에 올라감"을 강조 |
| 05–09 | 15 | 배경: `fork()` 사용법과 두 번 반환, main.c의 최초 fork, `_syscall0`·`sys_fork` 진입 |
| 10–15 | 20 | `_sys_fork` 어셈블리(2장), 17개 인자와 스택 슬롯 대응, `none`의 정체, `find_empty_process`, pid vs nr |
| 16–24 | 25 | `copy_process` 한 구역씩: 페이지 확보·복사, 덮어쓰는 필드, TSS 채우기(2장), eax=0 메커니즘, `copy_mem`, 공유 카운트, GDT·RUNNING |
| 25–27 | 10 | `copy_page_tables` 참고(결과만), "표 복사·페이지 공유" 그림, 자식의 첫 실행 경로 |
| 28–32 | 15 | 상태 변화도 2장, 자원 처리 비교, `f_count`, 반환값 비교 |
| 33–42 | 22 | 강사 시연 A/B/C + 캡처 + 관찰 vs 추론 |
| 43–46 | 5 | 질문의 답, fork가 하지 않는 일, 오해 정리, 현대 커널 한 줄 |
| 47–48 | 3 | 이해 확인, 정리·07·08 예고 |

## 10. 기존 계획 대비 변경·증가

합계: 기존 42장 → 이 계획 48장 (+6). 원천 슬라이드 계획 표의 42행은 전부 계승되었다(버린 행 없음).

| # | 변경 | 장 수 | 사유 |
|---|---|---|---|
| 1 | 원천 02 "15회차 지도" 1장 → 슬라이드 03 로드맵 + 슬라이드 04 구조도 2장으로 대체·흡수 | +1 | 00-common §2 표준 앞부분(지도 1장 → 다이어그램 2장) |
| 2 | 슬라이드 02 "핵심 질문과 오늘의 길" 신설 | +1 | 00-common §2 표준 앞부분 — 원천 01의 핵심 질문·답 예고 문구를 계승 |
| 3 | 원천 08 "`_sys_fork` 한 줄씩" → 슬라이드 10·11 분할 (208–211 / 212–219) | +1 | 코드 2스크린 초과 — 어셈블리 12줄 전체를 줄별로 읽으며 한 화면에 안 들어감 |
| 4 | 원천 15 "`copy_process` (3): TSS 채우기" → 슬라이드 18·19 분할 (92–97 / 98–112) | +1 | 코드 2스크린 + 04 프레임→TSS 화살표 그림 병기 분량 |
| 5 | 원천 19 "`copy_process` (5): 공유 카운트·GDT·RUNNING" → 슬라이드 23·24 분할 (120–128 / 129–132) | +1 | 성격이 다른 두 주제(참조 공유 vs GDT 등록·state 전환)가 한 장에 섞여 있었음 |
| 6 | 슬라이드 42 "관찰 vs 추론" 신설 | +1 | 00-common §7 "시연 뒤 관찰 vs 추론 구분 슬라이드 1장 유지" — 원천 캡처 C 슬라이드 각주에만 있던 내용을 독립 슬라이드로 승격 |
| 7 | 유형 조정(장 수 변동 없음): 원천 37 "정리"→"정답"(슬라이드 43), 원천 41 "질문"→"확인"(슬라이드 47), 원천 40 "배경"→"정리"(슬라이드 46) | 0 | 00-common §3 미니 지도 단계 대응(정답·확인 단계가 빈 채로 끝나지 않도록) |
| 8 | 그 외 원천 03–42의 모든 행은 순서·내용·줄 번호 그대로 새 번호로 계승 | 0 | 원천 보존 원칙 |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- `lab/` 빌드의 심볼명(`copy_process` vs `_copy_process`, `find_empty_process`, `sys_call_table` vs `_sys_call_table`)과 줄 번호 차이 확인 — 시연·캡처 슬라이드 각주에 "lab/ 수정본 (심볼 `_` 접두 등 차이)" 명시 (course-plan 47행).
- GDB 심볼 접근: `task`, `current`, `last_pid`, `jiffies` 및 `p *task[<nr>]` 구조체 인쇄 가능 여부 — 출력이 지나치게 크면 필드 지정 프린트(`p $c->pid` 등)로 대체.
- QEMU gdbstub에서 사용자 주소 중단점(`break *<tss.eip>`) 동작 여부와, 같은 선형 주소를 쓰는 다른 태스크에도 걸리는 현상 — 시연 C의 `$eax`·`current->pid` 필터 준비.
- 트리거 재현: 게스트 셸 프롬프트에서 `ls` 한 번 → `copy_process` 정지 확인(`info functions copy_process`로 심볼 사전 확인).
- 사전 캡처 확보·보관: `materials/06-fork/captures/` 두 자리 순번-설명.png 규칙(01–04, §5 목록) (course-plan 50행).
- 캡처 각주 필수 항목 통일: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜`, 사전 캡처는 `기존 기록` 라벨.
- `tss.ldt == (nr<<4)+(5<<3)` 기대값 검증용으로 GDB 세션에서 `p/x $c->tss.ldt` 사전 실행(캡처 B-2 관찰 대상).
