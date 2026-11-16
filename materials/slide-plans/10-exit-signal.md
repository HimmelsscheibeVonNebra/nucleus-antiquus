# 10회차 상세 슬라이드 제작 계획 — 종료·대기·시그널

- 기준: materials/course-plan.md `# 10. 종료·대기·시그널` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/10-exit-signal.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 40장 → 이 계획 46장 (+6)
- 로드맵 위치: 파트 D «프로그램의 일생» · 10/15

## 1. 회차 개요

- 핵심 질문: **자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?**
- 학습 목표 (course-plan 원문 계승):
  1. `_exit()`가 `do_exit()`에 도착해 자원을 반납하고 `TASK_ZOMBIE`로 남는 이유와, 누가 그 껍데기를 치우는지(`sys_waitpid` → `release`) 말할 수 있다.
  2. 0.11의 시그널이 `task_struct.signal` 32비트 비트맵 한 개이며, 전달은 "보내는 쪽이 비트를 켜고, 받는 쪽이 커널에서 사용자로 돌아가는 순간(`ret_from_sys_call`)에만 검사한다"는 두 단계로 되어 있음을 설명할 수 있다.
  3. `do_signal()`이 사용자 스택에 핸들러 프레임을 어떻게 쌓는지(복귀 주소 = `sa_restorer`, 인자 = signr, 저장 레지스터) 그림으로 그릴 수 있다.
  4. `waitpid` 옵션(`WNOHANG`, `WUNTRACED`)과 시그널 처리 선택지(`SIG_DFL`/`SIG_IGN`/핸들러)를 각각 범위 안에서 빠짐없이 비교하고, `SIGKILL`이 왜 등록조차 거부되는지 소스로 보일 수 있다.
  5. Ctrl-C가 tty 큐 → `tty_intr` → 프로세스 그룹 전체의 `signal` 비트 → 다음 커널 복귀 시 `do_signal` → 기본 동작 `do_exit`까지 가는 경로를 추적할 수 있다(tty 내부는 13회차).
- 읽을 소스 범위 (원본 src 기준 — course-plan 원문 계승):

| 파일 | 줄 | 내용 |
|---|---|---|
| kernel/exit.c | 19–33 | `release()` — task[] 슬롯 비우고 `free_page`, `schedule()` |
| kernel/exit.c | 35–44 | `send_sig()` — 권한 검사 후 `p->signal \|= 1<<(sig-1)` |
| kernel/exit.c | 46–54 | `kill_session()` — 같은 session 전체에 SIGHUP |
| kernel/exit.c | 60–81 | `sys_kill()` — pid 0 / >0 / -1 / <-1 네 갈래 |
| kernel/exit.c | 83–100 | `tell_father()` — 부모의 SIGCHLD 비트, 못 찾으면 `release(current)` |
| kernel/exit.c | 102–135 | `do_exit()` — 페이지 테이블·fd·inode 반납, 고아 입양, ZOMBIE, `tell_father`, `schedule()` |
| kernel/exit.c | 137–140 | `sys_exit()` — `(error_code&0xff)<<8` |
| kernel/exit.c | 142–195 | `sys_waitpid()` — 자식 탐색, STOPPED/ZOMBIE/기타 분기, 대기와 재시도 |
| kernel/signal.c | 15–26 | `sys_sgetmask`/`sys_ssetmask` — SIGKILL은 blocked에 못 넣음 |
| kernel/signal.c | 48–61 | `sys_signal()` — ONESHOT\|NOMASK로 등록, 이전 핸들러 반환 |
| kernel/signal.c | 63–80 | `sys_sigaction()` — 사용자 구조체 복사, sa_mask 조정 |
| kernel/signal.c | 82–119 | `do_signal()` — 처분 결정, 사용자 스택 프레임 구성 |
| include/signal.h | 12–34 | 시그널 번호 1~22 |
| include/signal.h | 37–39, 45–46, 48–53 | `SA_*`, `SIG_DFL`/`SIG_IGN`, `struct sigaction` |
| kernel/system_call.s | 17–31, 48–59 | 스택 배치 주석, task_struct/sigaction 오프셋 상수 |
| kernel/system_call.s | 101–128 | `ret_from_sys_call` — 시그널 검사와 `do_signal` 호출 |
| kernel/system_call.s | 176–197 | `timer_interrupt` — 틱 후에도 `ret_from_sys_call`로 합류 |
| kernel/sched.c | 24 | `_BLOCKABLE` — SIGKILL·SIGSTOP 제외 |
| kernel/sched.c | 104–119 | `schedule()` 앞부분 — alarm 및 "시그널 받은 INTERRUPTIBLE → RUNNING" |
| kernel/sched.c | 144–148 | `sys_pause()` |
| kernel/sched.c | 338–346 | `sys_alarm()` |
| include/linux/sched.h | 19–23, 83–89 | 태스크 상태 5종, `signal`/`sigaction[32]`/`blocked`/`exit_code`/`father`/`pgrp`/`session`/`leader` |
| kernel/fork.c | 86 | 자식 `p->signal = 0` (pending은 상속 안 됨) |
| fs/exec.c | 322–323 | exec 시 32개 핸들러 모두 NULL (SIG_DFL)로 초기화 |
| kernel/chr_drv/tty_io.c | 19–20, 111–120, 200–208 | `INTMASK`, `tty_intr()`, `copy_to_cooked`의 ISIG 분기 (참조만) |
| init/main.c | 179–187 | init의 fork → `wait(&i)` 루프 |
| include/sys/wait.h | 10–18 | `WNOHANG`/`WUNTRACED`, `WEXITSTATUS` 등 매크로 |
| lib/wait.c | 11–16 | `wait()` = `waitpid(-1, ..., 0)` |
| lib/_exit.c | 10–13 | `_exit()` = `int $0x80` with `__NR_exit` |
| mm/memory.c | 33–37 | `oom()` → `do_exit(SIGSEGV)` (커널이 직접 종료시키는 예) |

- 상태 변화도·비교 범위 (course-plan 원문 계승): 상태 변화도 ① 프로세스 생애 후반(RUNNING → do_exit 진행 중 → ZOMBIE → 소멸, 부수 상태로 부모 INTERRUPTIBLE), 상태 변화도 ② 시그널 1개의 생애(없음 → pending → blocked → 처리 → 핸들러 → 복귀), 비교 ① `sys_waitpid`의 options 비트 전부(`0`/`WNOHANG`/`WUNTRACED`), 비교 ② 한 시그널의 처분 `sa_handler` 값 전부(`SIG_DFL`/`SIG_IGN`/핸들러, SIGCHLD만 예외), 비교 ③ `sys_kill`의 pid 인자 4갈래(`0`/`>0`/`-1`/`<-1`). 혼합 금지: 태스크 상태(RUNNING/ZOMBIE)와 시그널 처분(DFL/IGN/handler)은 별도 슬라이드에 둔다.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 10. 종료·대기·시그널 | 표지 | 대제목 `10. 종료·대기·시그널` · 부제(핵심 질문 원문): "자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?" · 오늘 추적할 세 단어 `_exit`, `wait`, `signal` 배치(원 01 계승) · 우상단 `Linux 0.11` 배지 + `1991`, 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `10/15 · 파트 D «프로그램의 일생»` | — | 표지 배지·푸터(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치, 오늘 실제 다루는 단계만 강조 · 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다님(빠짐없이 강조) · 세 단어 `_exit`/`wait`/`signal`이 각각 코드·상태도·비교 어느 국면에 오는지 한 줄 안내 | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 D «프로그램의 일생»의 10만 ORANGE 강조 · 완료(TEAL) 01–09 · 이후(MUTED) 11–15 · 오늘 한 줄 문구와 09→10·10→11 연결 화살표 문구는 §3 명세 · 원 "지도" 슬라이드의 "06 fork → 09 exec → 10 exit/wait/signal로 «프로세스 생애» 축 완성, 11~13은 I/O 축" 내용을 완료·이후 상자 라벨로 계승 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | kernel/ 프로세스 계층의 kernel/exit.c·kernel/signal.c·kernel/system_call.s를 진한 TEAL로 강조 · 오늘의 데이터 흐름 화살표(ORANGE) 2개: `_exit` → `do_exit` → `TASK_ZOMBIE` → 부모의 `sys_waitpid` → `release`(회수) / Ctrl-C → `tty_intr`(kernel/chr_drv/tty_io.c) → signal 비트 → `ret_from_sys_call` → `do_signal` → SIGINT 전달 · 누적 강조(옅은 TEAL) 01–09 영역은 §3 명세 | kernel/exit.c:102–135, 142–195 · kernel/signal.c:82–119 · kernel/system_call.s:101–128 · kernel/chr_drv/tty_io.c:111–120 | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 9회차 복습: 셸이 명령을 실행하는 3단계 | 배경 | fork → exec → ? 의 빈칸 — 셸은 자식이 끝날 때까지 프롬프트를 내지 않는다 · 그 "끝남"을 커널이 어떻게 알려주는지가 오늘 주제 · init도 같은 구조: init/main.c:179–187의 fork → `wait(&i)` 루프 예고 · 오늘 세 단어 `_exit`/`wait`/`signal`이 이 빈칸을 채운다는 안내 | init/main.c:179–187 | fork→exec→? 3단계 빈칸 그림(§4) |
| 06 | 왜 종료는 두 단계인가 | 배경 | 프로세스가 스스로 자기 `task_struct` 페이지를 해제하면서 그 위의 커널 스택에서 실행 중일 수 없다 · 그래서 "자원 반납(스스로)"과 "껍데기 수거(남이)"를 분리 · 좀비라는 이름의 뜻 — 자원은 반납했으나 `exit_code`와 슬롯을 가진 채 남은 상태 · 오늘 상태 변화도(슬라이드 14)의 개념 틀 제시 | kernel/exit.c:19–33, 102–135 · include/linux/sched.h:19–23 | 두 단계 분리 도식(자원 반납/껍데기 수거) |
| 07 | task_struct에서 오늘 쓰는 필드 | 코드 | include/linux/sched.h:19–23 상태 5종(TASK_RUNNING 0 … TASK_STOPPED 4) · 83–89의 `signal`, `sigaction[32]`, `blocked`, `exit_code`, `pid/father/pgrp/session/leader` · 그림: 한 태스크 구조체에서 오늘 필드만 색칠 · 오늘 상태 변화도·비교가 전부 이 필드들로 표현됨을 예고 | include/linux/sched.h:19–23, 83–89 | task_struct 오늘 필드 색칠 그림(§4) |
| 08 | 시스템 콜 번호와 라이브러리 경로 | 코드 | lib/_exit.c:10–13 (`int $0x80`, `__NR_exit`=1) · lib/wait.c:11–16 (`wait`는 `waitpid(-1,…,0)`) · include/linux/sys.h:74–75의 sys_exit, sys_waitpid 위치(sys_call_table) · 4회차 시스템 콜 진입(번호 → 테이블 → kernel/)과 연결 | lib/_exit.c:10–13 · lib/wait.c:11–16 · include/linux/sys.h:74–75 | 시스템 콜 번호→함수 대응 미니 표(04회차 양식 재사용) |
| 09 | 호출 순서도: _exit에서 schedule까지 | 배경 | `sys_exit` → `do_exit` → `free_page_tables` ×2 → 고아 처리 → `sys_close` ×NR_OPEN → `iput` ×3 → tty/수학 → `kill_session` → state/exit_code → `tell_father` → `schedule` 세로 타임라인 · 상태 변화도(슬라이드 14)와 구분해 "호출 순서"라고 명시 · 슬라이드 10–13이 이 순서대로 코드를 읽는다는 로드맵 | kernel/exit.c:102–135 | 호출 순서 세로 도식(§4) |
| 10 | 코드: do_exit 전반부 (자원 반납) | 코드 | kernel/exit.c:102–123 · `free_page_tables(get_base(current->ldt[1]), get_limit(0x0f))` 두 줄은 7회차 LDT와 연결 · `sys_close` 루프는 fd 테이블 · `iput(pwd/root/executable)`은 12회차 예고 · `current->leader && current->tty >= 0`면 tty pgrp=0, `last_task_used_math` 정리 | kernel/exit.c:102–123 | 코드 인용(자원 종류별 하이라이트) |
| 11 | 코드: do_exit 후반부 (1/2) — 고아 입양과 SIGCHLD 재통지 | 코드 | kernel/exit.c:108–114 · 자식의 `father=1` 재지정 — 부모가 먼저 죽은 고아를 init(task[1])에 입양 · 이미 ZOMBIE인 자식에 대한 `send_sig(SIGCHLD, task[1], 1)` — 입양받은 init이 거둘 수 있게 비트를 켬 · "assumption task[1] is always init" 주석 · 상태 변화도(14)의 "부모 먼저 죽으면 father=1" 유지 조건과 연결 | kernel/exit.c:108–114 | 코드 인용(입양 갈래 하이라이트) |
| 12 | 코드: do_exit 후반부 (2/2) — ZOMBIE 전환·tell_father·schedule | 코드 | kernel/exit.c:130–134 · `current->state = TASK_ZOMBIE`, `current->exit_code = code` 보존 · `tell_father(current->father)` 후 `schedule()` — 다시 돌아오지 않음 · `return (-1)` 주석은 도달 불가 설명("just to suppress warnings") · 이 시점부터 이 태스크는 실행 코드·페이지 없이 구조체만 남음 | kernel/exit.c:130–134 | 코드 인용(ZOMBIE 전환 줄 하이라이트) |
| 13 | 코드: tell_father와 release | 코드 | exit.c:83–100 부모 pid 탐색 후 `signal \|= 1<<(SIGCHLD-1)` · 못 찾으면 `printk("BAD BAD…")` 후 `release(current)` · exit.c:19–33 `release`: `task[i]=NULL; free_page((long)p); schedule()` · "release는 항상 남이 호출한다"는 원칙과 유일한 예외(tell_father 실패 시 자신) | kernel/exit.c:83–100, 19–33 | 코드 인용(원칙·예외 콜아웃 박스) |
| 14 | 상태 변화도: RUNNING → ZOMBIE → 소멸 | 상태도 | 상태: RUNNING / (do_exit 진행 중: 여전히 RUNNING) / ZOMBIE / 소멸 · 전환 원인: `_exit`·치명 시그널 DFL·`oom`(mm/memory.c:33–37) / exit.c:130 / 부모의 `sys_waitpid`→`release` · 변경 데이터: 페이지 테이블·fd·inode 반납, `state`, `exit_code`, `task[i]`, task_struct 페이지 · 유지 조건: 부모가 wait 안 하면 ZOMBIE 영구, 부모 먼저 죽으면 `father=1` · 부수 상태: 부모 `TASK_INTERRUPTIBLE`(waitpid 중) → SIGCHLD 비트로 `schedule()`이 RUNNING 복귀 | kernel/exit.c:102–135, 142–195 · include/linux/sched.h:19–23 · mm/memory.c:33–37 | 핵심 상태 변화도(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 15 | 코드: sys_waitpid 탐색 조건 | 코드 | exit.c:142–164 · `&LAST_TASK`에서 역순으로 `father==current->pid` 자식만 보고 · `pid>0`/`pid==0`(같은 pgrp)/`pid<-1`(pgrp==-pid)/`pid==-1`(전부) 필터 · `verify_area(stat_addr,4)`는 8회차 COW와 연결 | kernel/exit.c:142–164 | 코드 인용 + 자식 필터 4갈래 미니 도식(23과 같은 색 언어) |
| 16 | 코드: sys_waitpid 상태별 분기 — STOPPED·ZOMBIE·기타 | 코드 | exit.c:165–182 · `TASK_STOPPED`: WUNTRACED 아니면 continue, 아니면 `0x7f` 기록 후 pid 반환(exit.c:166–170) · `TASK_ZOMBIE`: cutime/cstime 합산, `release(*p)`, `put_fs_long(code)` 후 pid 반환 · default: `flag=1`(살아 있는 자식이 있다는 표시) · 다음 장(17)의 대기 루프로 이어짐 | kernel/exit.c:165–194 | 코드 인용(switch 3갈래 색 구분) |
| 17 | 코드: sys_waitpid 대기와 재시작 — INTERRUPTIBLE·schedule·-EINTR | 코드 | exit.c:165–194(후반) · `flag`면 WNOHANG 검사 — 살아 있는 자식만 있으면 즉시 0 반환(exit.c:185–186) · 아니면 `TASK_INTERRUPTIBLE`로 `schedule()`(exit.c:187–188) · 깨어나 SIGCHLD 비트를 지우며(exit.c:189–192) 다른 시그널 없으면 `goto repeat`, 있으면 `-EINTR`; 자식 없으면 `-ECHILD`(exit.c:194) · 상태 변화도(14)의 부수 상태(부모)와 연결 | kernel/exit.c:165–194 | 코드 인용(대기 루프 사이클 화살표) |
| 18 | 비교: waitpid options (범위: 0.11이 정의한 옵션 전부) | 비교 | 표 · `0`: 자식 ZOMBIE까지 잠듦(exit.c:187–188) · `WNOHANG`(wait.h:10): 살아있는 자식만 있으면 즉시 0 반환(exit.c:185–186) · `WUNTRACED`(wait.h:11): STOPPED 자식도 보고 `0x7f` 기록(exit.c:166–170) — 단 0.11에는 SIGSTOP 처분에서 `TASK_STOPPED`로 만드는 코드가 없어 헤더 주석 "not supported"(wait.h:9)가 맞음을 명시 · 반환값 해석은 `WEXITSTATUS`(wait.h:15)와 `sys_exit`의 `<<8`(exit.c:139) | include/sys/wait.h:10–18 · kernel/exit.c:139, 166–170, 185–188 | 옵션 비교표(§4) |
| 19 | 시연 A 계획: 자식 종료와 부모 깨어남 | 시연 | 중단점 `do_exit`, `tell_father`, `sys_waitpid` · 관찰: `current->pid`, `current->father`, `current->state`가 0→3으로, 부모 task의 `state` 1→0, `signal`에 SIGCHLD 비트(0x10000 = 1<<16) · 명령 목록과 기대 출력 · 환경: lab/ QEMU i386 + GDB(target remote), 원본 수정 없음, 셸에서 `ls`를 실행해 유발 | kernel/exit.c:102–135, 142–195 | GDB 명령 블록 · 캡처 01·02(§5) |
| 20 | 시연 A 캡처 | 캡처 | GDB 로그: `p current->state` = 3 (`TASK_ZOMBIE`), `p/x task[N]->signal` = 0x10000 · 이어 `sys_waitpid` 안에서 `release` 직전 `p (*p)->exit_code`, `release` 직후 `p task[<자식 인덱스>]` = 0x0 · 상태 변화도(14)의 ZOMBIE·소멸 칸과 대응 표시 · 각주: lab/ QEMU i386 + GDB, 원본 수정 없음, 셸에서 `ls`를 실행해 유발 | kernel/exit.c(관찰 대상) | 01-do-exit-zombie.png · 02-waitpid-release.png(§5) |
| 21 | 시그널이란 무엇인가 (0.11 기준) | 배경 | 32비트 정수 하나(`sched.h:83`)에 번호-1 비트 · 큐 없음, 같은 시그널 두 번은 한 번 · 번호표 include/signal.h:12–34 (1 SIGHUP … 22 SIGTTOU) · "메시지가 아니라 플래그"라는 한 문장 · pending 용어 정의(§7) | include/linux/sched.h:83 · include/signal.h:12–34 | 32비트 비트맵 그림(§4) |
| 22 | 보내는 쪽: send_sig와 sys_kill | 코드 | exit.c:35–44 `send_sig`: `priv \|\| euid 일치 \|\| suser()`면 `p->signal \|= 1<<(sig-1)` · exit.c:60–81 `sys_kill`의 네 갈래 · 보내는 쪽은 상대를 깨우지 않는다 — 깨우는 것은 `schedule()`(`sched.c:117–119`) · kill_session(exit.c:46–54)은 세션 리더 종료 시 같은 session 전체에 SIGHUP(슬라이드 09 순서도와 연결) | kernel/exit.c:35–44, 46–54, 60–81 · kernel/sched.c:117–119 | 코드 인용(권한 검사 3조건 하이라이트) |
| 23 | 비교: sys_kill pid 인자 (범위: 4갈래 전부) | 비교 | 표 · `pid==0`: 내 pgrp 전체(priv=1, exit.c:65–68) · `pid>0`: 그 pid(69–72) · `pid==-1`: 모든 태스크(73–75) · `pid<-1`: pgrp==-pid(76–79) · 각 갈래의 권한 인자(priv 0/1)와 반환값 누적 방식(retval에 err 누적) | kernel/exit.c:60–81 | 4갈래 비교표(§4) |
| 24 | 받는 쪽은 언제 검사하는가 — 두 곳뿐 | 코드 | `system_call.s:12–15` 주석: 타이머 인터럽트 후와 시스템 콜 후에만 시그널 인식(signal-recognition) · `timer_interrupt`(`176–197`)도 `jmp ret_from_sys_call`로 합류 · 일반 인터럽트는 검사하지 않는다(clutter 방지 주석) · "보내는 즉시"가 아니라 "다음 복귀 시점" — 핵심 질문 2(Ctrl-C)의 뼈대 | kernel/system_call.s:12–15, 176–197 | 주석 인용 블록 + 두 합류 지점 미니 타임라인 |
| 25 | 받는 쪽의 검사 조건 — 사용자 모드로 돌아갈 때만 | 코드 | `system_call.s:101–108`: task[0] 제외("task[0] cannot have signals") · `CS==0x0f`·`OLDSS==0x17` 즉 사용자 모드로 돌아갈 때만 · 커널 모드에서 깨어난 시점은 검사 안 함 → "Ctrl-C가 즉시가 아닌 이유" · schedule() 앞부분(sched.c:104–119)의 "시그널 받은 INTERRUPTIBLE → RUNNING"과 이어지는 두 단계 구조 | kernel/system_call.s:101–108 · kernel/sched.c:104–119 | 코드 인용(CS/OLDSS 검사 하이라이트) |
| 26 | 코드: ret_from_sys_call 시그널 선택 | 코드 | `system_call.s:109–120`: `signal & ~blocked` → `bsfl`로 최하위 비트(가장 작은 번호 우선) → `btrl`로 비트 내림 → `incl`로 번호 → `pushl %ecx; call _do_signal` · 한 번에 한 개만 처리, 나머지는 다음 복귀 때 · 13개 인자가 스택 배치 주석(17–31) 그대로 전달됨을 예고(슬라이드 29에서 확인) | kernel/system_call.s:109–120 · kernel/system_call.s:17–31 | 코드 인용(비트 연산 4단계 하이라이트) |
| 27 | 코드: do_signal 처분 결정 | 코드 | `signal.c:82–103` · `sa_handler==1`(SIG_IGN) → return · `==0`(SIG_DFL) → SIGCHLD면 return, 아니면 `do_exit(1<<(signr-1))` · `SA_ONESHOT`이면 핸들러를 NULL로(한 번 쓰고 기본으로) · `do_exit` 인자가 `1<<(signr-1)`이라 종료 코드 하위 바이트에 시그널이 남는 방식의 특이점 명시(sys_exit의 `<<8`, exit.c:137–140와 대비) | kernel/signal.c:82–103 · kernel/exit.c:137–140 | 코드 인용(처분 3갈래 → 슬라이드 28 분기도와 같은 색) |
| 28 | 비교: 시그널 처분 (범위: sa_handler 값 전부) | 비교 | 표 · `SIG_DFL`(0, `signal.h:45`): 프로세스 종료(SIGCHLD 제외) — "정지/코어/무시" 세분화 없음 · `SIG_IGN`(1, `signal.h:46`): 비트는 지워지고 아무 일 없음 · 핸들러 주소: 사용자 스택 프레임 구성 후 사용자 모드에서 실행 · 각 행에 전환 조건(`sys_signal`/`sys_sigaction`/exec 시 리셋 `fs/exec.c:322–323`)과 소스 | include/signal.h:45–46 · kernel/signal.c:82–103 · fs/exec.c:322–323 | 핵심 처분 분기 다이어그램(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 29 | 코드: do_signal 프레임 구성 | 코드 | `signal.c:104–118` · `*(&eip)=sa_handler`로 iret가 핸들러로 가게 하고 · `*(&esp) -= longs`(7 또는 8), `put_fs_long`으로 `sa_restorer, signr, [blocked], eax, ecx, edx, eflags, old_eip` 순서로 사용자 스택에 기록 · `current->blocked \|= sa->sa_mask` · 인자가 C 매개변수이면서 스택의 복사본이라 `*(&eip)`로 쓰는 이유 설명(`system_call.s:17–31` 배치와 1:1) | kernel/signal.c:104–118 · kernel/system_call.s:17–31 | 코드 인용 + put_fs_long 나열 순서 하이라이트 |
| 30 | 그림: 핸들러 호출 전후 사용자 스택 | 상태도 | 왼쪽: 시스템 콜 직전 사용자 스택 · 오른쪽: `do_signal` 후 — `[esp] = sa_restorer`(핸들러가 ret하면 여기로), `[esp+4]=signr`(핸들러의 첫 인자), 그 위에 old eax/ecx/edx/eflags/old_eip · `iret` → 핸들러 → `ret` → restorer(사용자 라이브러리 코드)가 레지스터 복원 후 old_eip로 · 커널이 "두 번째 복귀"를 사용자 코드에 맡기는 구조 | kernel/signal.c:104–118 · kernel/system_call.s:17–31 | 사용자 스택 전/후 2컷 그림(§4 상세 명세) |
| 31 | 상태 변화도: 시그널 한 개의 생애 | 상태도 | 상태: 없음 / pending(비트 1) / blocked에 가려짐 / 처리 중(비트 0, do_signal) / 핸들러 실행 중(사용자) / 복귀 · 전환 원인: `send_sig`·`tell_father`·`tty_intr`·alarm(`sched.c:113–115`) / `ret_from_sys_call:115` / 처분값 · 변경 데이터: `signal`, `blocked`, 사용자 ESP·EIP, `sa_handler`(ONESHOT) · 유지 조건: 커널 모드에 머무는 동안은 pending 유지 · 태스크 상태도(14)와 혼합 금지 — 별도 슬라이드 | kernel/exit.c:35–44, 83–100 · kernel/system_call.s:109–120 · kernel/signal.c:82–119 · kernel/sched.c:113–115 · kernel/chr_drv/tty_io.c:111–120 | 시그널 생애 상태 다이어그램(§4 상세 명세) |
| 32 | SIGKILL은 왜 못 잡는가 | 코드 | `signal.c:52–53`, `signal.c:68–69`: `signum==SIGKILL`이면 `sys_signal`/`sys_sigaction` 모두 `-1` · `signal.c:24`: `ssetmask`가 SIGKILL 비트를 깎음 · `sched.c:24` `_BLOCKABLE`은 SIGKILL·SIGSTOP 제외 — 단 SIGSTOP은 등록은 거부되지 않음(0.11의 비대칭) · 결론: SIGKILL은 항상 `SIG_DFL` → `do_exit` | kernel/signal.c:52–53, 68–69, 24 · kernel/sched.c:24 | 코드 인용(거부 지점 3곳 하이라이트) |
| 33 | sys_signal vs sys_sigaction | 코드 | `signal.c:48–61`: `signal()`은 `SA_ONESHOT\|SA_NOMASK` 고정, restorer를 세 번째 인자로 받음 · `signal.c:63–80`: `sigaction()`은 구조체 통째 복사, `SA_NOMASK` 아니면 자기 번호를 `sa_mask`에 추가 · 둘 다 같은 `current->sigaction[]`에 쓴다 · `sys_sgetmask`/`sys_ssetmask`(15–26)로 blocked 조회·설정 | kernel/signal.c:15–26, 48–61, 63–80 | 코드 인용(두 인터페이스 나란히 배치) |
| 34 | fork·exec·wait와 시그널 상태 | 코드 | `fork.c:86` 자식 `signal=0`(pending 미상속, `sigaction[]`은 `*p = *current`로 상속) · `exec.c:322–323` 핸들러 전부 NULL · `exit.c:189–192` waitpid가 깨어난 뒤 SIGCHLD만 지우고 다른 시그널이 있으면 `-EINTR` · `sched.c:144–148` `pause()`도 같은 방식으로 깨어남 | kernel/fork.c:86 · fs/exec.c:322–323 · kernel/exit.c:189–192 · kernel/sched.c:144–148 | 코드 인용(생애 사건 4개 타임라인) |
| 35 | Ctrl-C 경로 (참조: 13회차에서 상세) | 코드 | 키보드 IRQ → `tty_io.c:200–203` `copy_to_cooked`가 `INTR_CHAR`를 만나면 `tty_intr(tty, INTMASK)` → `tty_io.c:111–120` `pgrp==tty->pgrp`인 모든 태스크에 비트 OR · 이후는 슬라이드 24–27과 동일(ret_from_sys_call → do_signal → 처분) · "어디까지 가는가"의 답: 비트 하나까지; 실제 죽는 건 그 프로세스가 다음에 사용자 모드로 돌아가는 순간 · `kill_pg`는 0.11에 없고 tty 쪽 함수는 `tty_intr`(`tty_io.c:111`)임을 명시 | kernel/chr_drv/tty_io.c:19–20, 111–120, 200–208 | Ctrl-C 경로 도식(§4) |
| 36 | 시연 B 계획: kill과 핸들러 프레임 | 시연 | 셸에서 `kill -2 <pid>`(또는 lab 테스트 프로그램이 `signal(SIGINT, h)` 등록 후 `pause()`) · 중단점 `sys_kill`, `do_signal` · 관찰: 대상 `signal` 비트, `do_signal` 진입 시 `signr`, 리턴 직전 `esp`와 `x/8wx esp`(사용자 스택 프레임), `eip`가 핸들러 주소로 바뀜 · 기대 프레임 `[sa_restorer, 2, blocked, eax, ecx, edx, eflags, old_eip]`(SA_NOMASK면 7개) | kernel/exit.c:60–81 · kernel/signal.c:82–119 | GDB 명령 블록 · 캡처 03·04(§5) |
| 37 | 시연 B 캡처 | 캡처 | GDB 로그: `b do_signal` → `p signr`=2, `p/x sa_handler`, `finish` 직전 `x/8wx esp`에 restorer/2/eax/ecx/edx/eflags/old_eip · `finish` 후 `info registers eip`는 핸들러 주소 · 스택 그림(30)의 값과 1:1 대응 표시 · 각주: lab/의 테스트 프로그램은 수업용 추가 바이너리(원본 소스 미수정), 핸들러 없는 기본 경로는 `ls`에 `kill -9`로 대체 | kernel/signal.c(관찰 대상) | 03-kill-signal-bit.png · 04-do-signal-frame.png(§5) |
| 38 | 시연 C 계획: Ctrl-C | 시연 | 셸에서 `sleep 100`(또는 무한 루프 프로그램) 후 Ctrl-C · 중단점 `tty_intr` 조건부(`mask==2`), `do_signal` · 관찰: `tty->pgrp`, 대상 태스크 `signal` 비트, `do_signal`에서 `sa_handler==0` → `do_exit` · 실패 시 대체: 사전 캡처(QEMU 콘솔 입력이 GDB 중단과 겹치면 키 입력이 늦게 전달될 수 있음) · 참조 수준 — 시간 남을 때만 라이브 | kernel/chr_drv/tty_io.c:111–120 · kernel/signal.c:82–103 | GDB 명령 블록 · 캡처 05·06(§5) |
| 39 | 시연 C 캡처 | 캡처 | 터미널 캡처: Ctrl-C 후 `tty_intr` 중단, `p tty->pgrp`, `p/x task[N]->signal`=0x2 · 이어 `do_signal` 중단에서 `signr`=2, 한 단계 뒤 `do_exit` 진입 · 각주: 원본 미수정, 캡처 시 QEMU `-serial`/콘솔 설정 · 사전 캡처는 모서리에 `기존 기록` 라벨 | kernel/chr_drv/tty_io.c(관찰 대상) | 05-ctrl-c-tty-intr.png · 06-ctrl-c-do-exit.png(§5) |
| 40 | 질문의 답 1: 자식이 죽으면 부모는 어떻게 아는가 | 정답 | 세 줄 요약: (1) 자식은 `do_exit`에서 자원만 반납하고 ZOMBIE로 남는다(`exit.c:130–132`) · (2) `tell_father`가 부모 `signal`의 SIGCHLD 비트를 켠다 · (3) 부모는 `sys_waitpid`에서 자고 있다가 `schedule()`의 시그널 검사로 깨어나(`sched.c:117–119`) ZOMBIE 자식을 `release`하고 `exit_code`를 받는다 · "tell_father는 깨우지 않는다"는 두 단계 구분 재강조 | kernel/exit.c:130–132, 83–100, 142–195 · kernel/sched.c:117–119 | 답 요약 박스 + 상태 변화도(14) 미니 재지시 |
| 41 | 질문의 답 2: Ctrl-C는 어디까지 가는가 | 정답 | 키 → tty 큐 → `tty_intr`가 프로세스 그룹의 비트를 켬 → 그 프로세스가 다음 시스템 콜/타이머 복귀 때 `ret_from_sys_call`이 발견 → `do_signal` → 핸들러가 없으면 `do_exit` · 커널 모드에서 잠든 프로세스(`TASK_UNINTERRUPTIBLE`)는 깨우지 못한다는 한계 명시 · 경로 도식(35) 미니 재활용 | kernel/chr_drv/tty_io.c:111–120, 200–208 · kernel/system_call.s:101–128 · kernel/signal.c:82–103 | 답 요약 박스 + 경로 도식(35) 축약 재활용 |
| 42 | 현대 커널과의 차이 (짧게) | 배경 | 비트맵 32개 → `sigpending` 큐와 실시간 시그널 · `sa_restorer` 사용자 코드 → 커널 제공 trampoline/`sigreturn` · `TASK_ZOMBIE`는 이름만 `EXIT_ZOMBIE`로 · `wait4`/`waitid` · SIGSTOP/SIGCONT 실제 정지 · 14회차에서 다시 비교 | —(현대 커널 참조 — 14회차 상세) | 0.11 ↔ 현대 대비 2열 표 |
| 43 | 흔한 오해 | 배경 | (1) "kill은 프로세스를 즉시 죽인다" — 비트만 켠다 · (2) "좀비는 버그" — 설계다 · (3) "SIG_IGN은 시그널을 막는다" — 비트는 켜졌다가 do_signal에서 버려진다 · (4) "핸들러는 커널이 호출한다" — iret로 사용자 모드에서 시작하고 복귀는 사용자 restorer가 한다 · §8 원문과 동일 | kernel/exit.c:35–44 · kernel/signal.c:94–103, 104–118 | 오해↔사실 2열 카드 |
| 44 | 이해 확인 질문 | 확인 | 4문항 질문만 게시(§6 원문 그대로) · do_exit와 task_struct 페이지 / kill 반환 직후 핸들러 실행 여부 / `signal(SIGKILL, h)` 반환값 / `waitpid(-1, &st, WNOHANG)`이 0을 반환한 경우의 자식 상태 | (§6 정답 근거와 동일) | 문항 4개 텍스트 |
| 45 | 이해 확인 정답 | 확인 | 정답과 근거 줄 번호(§6 원문 그대로) · 1번: 커널 스택 위 실행 중 — 해제는 `sys_waitpid` → `release()`(exit.c:19–33), 예외 exit.c:98–99 · 2번: 아니다 — `send_sig`는 비트만(exit.c:40), 검사는 `ret_from_sys_call`(system_call.s:109–119) · 3번: `-1`(signal.c:52–53, 68–69, 24) · 4번: 살아 있는 자식 최소 하나, 거둘 ZOMBIE 없음(exit.c:179–186), 자식 없으면 `-ECHILD`(exit.c:194) | (§6 정답 근거와 동일) | 정답 4개 텍스트 |
| 46 | 정리와 다음 회차 | 정리 | 오늘 세 함수(`do_exit`, `sys_waitpid`, `do_signal`)의 역할 한 줄씩 · 다음 11회차: "read()가 디스크에 실제로 접근하는 때는 언제인가?" · 오늘 `do_exit`가 호출한 `iput`과 `sys_close` 뒤에 있는 버퍼 캐시로 이동 · 파트 D «프로그램의 일생» 마무리 — 06 fork → 09 exec → 10 종료·대기·시그널로 «프로세스 생애» 축 완성 | —(11회차 예고) | 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: D «프로그램의 일생» · 10/15 — 파트 D의 마지막 회차(09 exec → 10 종료·대기·시그널). 완료(TEAL) 01–09, 오늘(ORANGE + 굵은 테두리) 10, 이후(MUTED) 11–15.
- 오늘 한 줄 문구: "자원은 스스로 반납하고 껍데기는 부모가 거둔다 — 종료·대기·시그널"
- 09→오늘 연결 화살표 문구: "09: fork로 만들고 exec로 갈아끼운 프로그램 → 10: 실행한 프로그램은 어떻게 끝나는가 — 종료·대기·시그널"
- 오늘→11 연결 화살표 문구: "10: do_exit가 부른 `iput`·`sys_close`의 뒤편 → 11: 프로세스가 죽어도 남는 것 — 열어둔 파일과 버퍼 캐시"
- 원 "지도" 슬라이드(원 02) 내용 계승: 완료 상자 축 라벨 "06 fork → 09 exec → 10 exit/wait/signal로 «프로세스 생애» 축 완성", 이후 상자 11–13 라벨 "I/O 축"(11 버퍼 캐시·블록, 12 파일 시스템, 13 터미널). 미니 지도 범례는 슬라이드 02 오늘의 길에서 계승.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL): kernel/ 프로세스 계층의 kernel/exit.c(`do_exit`·`sys_waitpid`·`release`·`send_sig`·`sys_kill`·`tell_father`), kernel/signal.c(`sys_signal`·`sys_sigaction`·`do_signal`), kernel/system_call.s(`ret_from_sys_call`의 시그널 검사·`do_signal` 호출).
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): `_exit`(int $0x80) → sys_exit → do_exit(kernel/exit.c) → TASK_ZOMBIE → 부모의 sys_waitpid(kernel/exit.c) → release(회수) — "종료 → zombie → 회수".
- 보조 화살표(ORANGE, 2번째 — 00-common §2가 허용하는 1–2개 안): Ctrl-C(키보드 IRQ) → tty_intr(kernel/chr_drv/tty_io.c) → 프로세스 그룹 태스크들의 signal 비트 → ret_from_sys_call(kernel/system_call.s) → do_signal(kernel/signal.c) → SIGINT 전달.
- 누적 강조(옅은 TEAL, 01–09): 파트 A — boot/bootsect.s·boot/setup.s·boot/head.s·init/main.c(01–03) / 파트 B — kernel/system_call.s·kernel/asm.s·kernel/traps.c(04), include/linux/sched.h·kernel/sched.c(05), kernel/fork.c(06) / 파트 C — mm/memory.c(07), mm/page.s(08) / 파트 D — fs/exec.c·include/a.out.h(09). kernel/sched.c(schedule()의 시그널 검사·sys_pause), kernel/fork.c(fork.c:86), init/main.c(wait 루프), mm/memory.c(oom), fs/exec.c(322–323 핸들러 리셋)은 오늘 참조 파일이므로 라벨 유지. kernel/chr_drv/tty_io.c는 보조 화살표의 경유점(13회차에서 상세).

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(10 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 10 ORANGE, 01–09 TEAL, 11–15 MUTED, 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(kernel/ 프로세스 계층 강조) | 도형 다이어그램 | §3 명세 그대로 — kernel/exit.c·kernel/signal.c·kernel/system_call.s 강조 + 데이터 흐름 화살표 2 | 전 회차 공통 골격 + 01–09 누적 영역 |
| 05 | fork → exec → ? 3단계 빈칸 | 도형 | 셸의 3단계 중 세 번째를 빈칸(ORANGE 점선) — "끝남을 커널이 어떻게 알리는가" | 09회차 셸 실행 3단계 그림 |
| 07 | task_struct 오늘 필드 색칠 그림 | 도형 | sched.h:19–23 상태 5종 + 83–89의 signal/sigaction[32]/blocked/exit_code/pid/father/pgrp/session/leader — 오늘 필드만 TEAL, 나머지 MUTED 실루엣 | 05회차 task_struct 그림 양식 |
| 09 | _exit→schedule 호출 순서도 | 도형 | sys_exit → do_exit → free_page_tables ×2 → 고아 처리 → sys_close ×NR_OPEN → iput ×3 → tty/수학 → kill_session → state/exit_code → tell_father → schedule 세로 타임라인 · "상태 변화도 아님(호출 순서)" 명시 | 08회차 함수 호출 그래프 양식 |
| 14 | 상태 변화도: 종료 → ZOMBIE → 회수 (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(노드 4 + 부수 상태 서브도) | 05회차 태스크 상태 다이어그램 언어 |
| 18 | waitpid options 비교표 | 표 | 0 / WNOHANG / WUNTRACED — 잠듦 여부·반환값·기록값·0.11 사실(WUNTRACED not supported) | — |
| 21 | 32비트 시그널 비트맵 그림 | 도형 | task_struct.signal 32비트 레이아웃, 번호-1 비트 매핑(예: SIGINT=2 → bit1, SIGCHLD=17 → bit16 = 0x10000) | — |
| 23 | sys_kill pid 4갈래 비교표 | 표 | pid==0 / pid>0 / pid==-1 / pid<-1 — 대상·권한 인자 priv(0/1)·반환값 누적(retval에 err) | — |
| 28 | 시그널 처분 분기 (핵심) | 표 + 도형 | 아래 상세 명세 — sa_handler 값 전부 3갈래 분기 | — |
| 30 | 핸들러 호출 전후 사용자 스택 (핵심) | 도형 2컷 | 아래 상세 명세(슬라이드 29·30·캡처 04가 같은 시각 언어 공유) | 04회차 시스템 콜 스택 그림 양식 |
| 31 | 시그널 한 개의 생애 상태 변화도 (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(노드 6 + 전환 5) | — |
| 35 | Ctrl-C 경로 도식 | 도형 | 키보드 IRQ → tty 큐 → copy_to_cooked(INTR_CHAR) → tty_intr(INTMASK) → pgrp 일치 태스크 signal 비트 → ret_from_sys_call → do_signal → do_exit · tty 내부는 13회차 예고 라벨 | 04회차 인터럽트 진입 그림 양식 |

핵심 시각자료 상세 명세 — "종료 → ZOMBIE → 회수" 상태 변화도 (슬라이드 14가 중심, 캡처 20·정답 40이 같은 그림을 재지시):

- 공통 시각 언어: 태스크 상태 노드는 상자(상태값 라벨: RUNNING 0 / INTERRUPTIBLE 1 / ZOMBIE 3 / 소멸), 전환 화살표에 원인 라벨(함수 + 줄 번호), 화살표 옆에 변경 데이터 작은 표. 오늘의 핵심 상태 ZOMBIE는 ORANGE, RUNNING·회수 완료는 TEAL, 소멸(존재 안 함)은 MUTED 점선. 우하단 `Linux 0.11` 라벨.
- 노드 4개: `TASK_RUNNING(0)` / `do_exit 진행 중(여전히 RUNNING — 페이지 테이블·fd·inode 반납 중)` / `TASK_ZOMBIE(3) — state=3, exit_code 보존, task[] 슬롯·task_struct 페이지 유지` / `소멸 — task[i]=NULL, 페이지 해제(더는 존재 안 함)`.
- 전환 화살표 2개: (1) RUNNING → do_exit 진행 중 → ZOMBIE — 원인 `_exit`·치명 시그널 기본 처리·`oom`(mm/memory.c:33–37), 전환 점 exit.c:130; 변경 데이터: 페이지 테이블·fd·inode 반납, `state=3`, `exit_code=code`. (2) ZOMBIE → 소멸 — 원인 부모의 `sys_waitpid` → `release`(exit.c:19–33); 변경 데이터: cutime/cstime 합산, `put_fs_long(code)`로 부모에 전달, `task[i]=NULL`, `free_page`.
- 유지 조건 라벨 2개: 부모가 wait하지 않으면 ZOMBIE 영구 / 부모가 먼저 죽으면 `father=1`로 init이 거둠(슬라이드 11과 연결).
- 부수 상태 서브 다이어그램(부모 쪽, 아래 별도 박스): 부모 `TASK_INTERRUPTIBLE`(waitpid 중, state 1) → SIGCHLD 비트가 켜진 채 `schedule()` 앞부분(sched.c:117–119)이 RUNNING 복귀 — "tell_father는 깨우지 않고 schedule()이 깨운다"는 두 단계를 화살표 2개로 분리 표현.
- 시그널 생애 상태도(31)와는 별도 다이어그램 — 태스크 상태와 시그널 처분의 혼합 금지(course-plan 원칙).

핵심 시각자료 상세 명세 — 시그널 처분 분기(기본/무시/핸들러) 비교 (슬라이드 27 코드·28 분기도가 같은 색 언어 공유):

- 형식: `do_signal` 진입(signr 확정, 비트는 이미 내려옴)을 맨 위에 두고 3갈래 분기 다이어그램 + 아래 비교표. 분기 판정값은 `sa_handler`.
- 갈래 1 `SIG_DFL(0)`(signal.h:45): SIGCHLD → return(아무 일 없음) / 그 외 → `do_exit(1<<(signr-1))` — 0.11에는 "정지/코어/무시" 세분화 없이 종료 하나뿐임을 라벨로 명시.
- 갈래 2 `SIG_IGN(1)`(signal.h:46): 그냥 return — 비트는 켜졌다가 do_signal에서 버려질 뿐("막는" 것이 아님 — 흔한 오해 43과 연결).
- 갈래 3 핸들러 주소: `SA_ONESHOT`이면 sa_handler=NULL(한 번 쓰고 기본으로) → 프레임 구성(슬라이드 29–30)으로 연결 화살표.
- 비교표 열: 처분값 / do_signal 동작 / signal 비트·sa_handler 변화 / 등록·해제 경로(sys_signal signal.c:48–61, sys_sigaction 63–80, exec 시 리셋 fs/exec.c:322–323). 캡처 04(핸들러 갈래)·06(기본 갈래 → do_exit)가 어느 갈래의 실관찰인지 재지시.

핵심 시각자료 상세 명세 — 사용자 스택 전/후(30)와 시그널 생애(31):

- 슬라이드 30 (2컷): 왼쪽 시스템 콜 직전 사용자 스택(평범한 상태). 오른쪽 do_signal 후 — esp가 longs(7 또는 8)×4 바이트 내려가고, esp에서 위로 `[sa_restorer][signr][blocked — SA_NOMASK 아니면][eax][ecx][edx][eflags][old_eip]` 적재, iret 후 EIP=sa_handler. 핸들러 `ret` → sa_restorer(사용자 라이브러리 코드)가 레지스터 복원 후 old_eip 복귀하는 화살표. 캡처 04의 `x/8wx esp` 값과 1:1 대응 칸 표시.
- 슬라이드 31 (노드 6 + 전환): 노드 — 없음 / pending(비트 1) / blocked에 가려짐 / 처리 중(비트 0, do_signal) / 핸들러 실행 중(사용자) / 복귀(원래 EIP). 전환 라벨 — send_sig·tell_father·tty_intr·alarm(sched.c:113–115) / ret_from_sys_call:115(bsfl·btrl) / 처분값(28의 3갈래) / sa_restorer. 유지 조건: 커널 모드에 머무는 동안 pending 유지. 시각 언어는 14와 공유하되 시그널 쪽 상태에 ORANGE.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/10-exit-signal/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A 전반 | 01-do-exit-zombie.png | `b do_exit` · `b tell_father` · 셸 `ls` · `p current->pid` · `p current->father` · `p current->state`(0) · `tell_father` 진입 시 `p pid`(부모 pid) · `finish` 후 `p/x task[<부모 인덱스>]->signal` · `do_exit:130` 통과 후 `p current->state` | `current->state` 0→3(TASK_ZOMBIE), 부모 signal = 0x10000(1<<16 = SIGCHLD), 부모 state 1→0 | `plan/` 사전 캡처 로그(슬라이드 20에 게시) |
| A 후반 | 02-waitpid-release.png | `b sys_waitpid` · `p (*p)->state`(3) · `p (*p)->exit_code` · `release` 직후 `p task[<자식 인덱스>]`(0x0) | ZOMBIE 자식의 exit_code, release 후 task[N]=0x0(슬롯 NULL) | 사전 캡처 로그 |
| B 전반 | 03-kill-signal-bit.png | 게스트 테스트 프로그램(`signal(SIGINT, handler); pause();`) 백그라운드 실행 · `kill -2 <pid>` · `b sys_kill` · `p pid` · `p sig` · `finish` 후 `p/x task[N]->signal` | sys_kill 인자(pid, sig), 대상 signal = 0x2 | 핸들러 없는 경로는 `ls`에 `kill -9`로 대체 |
| B 후반 | 04-do-signal-frame.png | `b do_signal` · `p signr`(2) · `p/x sa->sa_handler` · `signal.c:118` 직전 `p/x esp` · `x/8wx esp` · `finish` 후 `info registers eip` | 사용자 스택 프레임 [sa_restorer, 2, blocked, eax, ecx, edx, eflags, old_eip](SA_NOMASK면 7개), eip = 핸들러 주소 | 테스트 프로그램 빌드 실패 시 사전 캡처 |
| C-1 | 05-ctrl-c-tty-intr.png | 게스트에서 오래 도는 명령(`sleep 100` 등) 후 Ctrl-C · `b tty_intr if mask==2` · `p tty->pgrp` · `p/x task[N]->signal` | tty_intr 중단(INTMASK = 2), `pgrp==tty->pgrp` 태스크의 signal = 0x2 | 사전 캡처를 기본(QEMU 콘솔 입력과 GDB 중단이 겹치면 키 입력이 늦게 전달될 수 있음) |
| C-2 | 06-ctrl-c-do-exit.png | 이어 `b do_signal` · `p signr`(2) · 한 단계 뒤 `do_exit` 진입 | `sa_handler==0`(SIG_DFL) → `do_exit` 진입 — 처분 분기도(28)의 기본 갈래 실관찰 | 사전 캡처 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음(시연 B의 테스트 프로그램은 lab/에 추가한 사용자 바이너리 — 원본 소스 미수정) · 캡처 날짜`(00-common §7). 사전 캡처는 모서리에 `기존 기록` 라벨.

## 6. 이해 확인 질문과 정답

질문은 슬라이드 44, 정답은 슬라이드 45에 게시(원문 계승 — 원 39의 "먼저 질문만 띄우고 클릭으로 정답 노출"을 두 장으로 분리).

1. **Q.** `do_exit()`는 왜 자기 `task_struct` 페이지를 `free_page`하지 않는가?
   **A.** 그 페이지 위의 커널 스택에서 지금 실행 중이기 때문. 해제는 다른 태스크가 `sys_waitpid` → `release()`(`exit.c:19–33`)로 한다. 부모를 못 찾는 예외(`exit.c:98–99`)만 자신이 `release(current)`.
2. **Q.** `kill(pid, SIGINT)`가 반환된 직후, 대상 프로세스는 이미 핸들러를 실행했는가?
   **A.** 아니다. `send_sig`는 `p->signal` 비트만 켠다(`exit.c:40`). 대상이 다음에 시스템 콜/타이머에서 사용자 모드로 복귀할 때 `ret_from_sys_call`(`system_call.s:109–119`)이 검사한다.
3. **Q.** `signal(SIGKILL, h)`의 반환값과 이유는?
   **A.** `-1`. `sys_signal`이 `signum==SIGKILL`을 거부한다(`signal.c:52–53`). `sigaction`도 같다(`signal.c:68–69`). 또한 `ssetmask`는 SIGKILL 비트를 깎는다(`signal.c:24`).
4. **Q.** `waitpid(-1, &st, WNOHANG)`이 0을 반환했다. 자식 상태는?
   **A.** 살아 있는(ZOMBIE가 아닌) 자식이 최소 하나 있고 거둘 ZOMBIE는 없다. `flag=1`이고 `options & WNOHANG`이면 즉시 0(`exit.c:179–186`). 자식이 아예 없으면 `-ECHILD`(`exit.c:194`).

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 좀비(ZOMBIE, `TASK_ZOMBIE`=3) | 자원은 반납했지만 `task[]` 슬롯과 `exit_code`를 가진 채 부모의 wait를 기다리는 상태 | 06 |
| 고아 입양(`father=1`) | 부모가 먼저 종료하면 자식의 부모를 init(task[1])으로 바꾸는 것(`exit.c:108–114`) | 11 |
| pending 시그널 | `task_struct.signal`에 켜진 비트. 아직 처리 전 | 21 |
| blocked / 시그널 마스크 | `task_struct.blocked`; 켜진 비트의 시그널은 `ret_from_sys_call`이 건너뛴다 | 26 |
| 처분(disposition) | `sa_handler` 값에 따른 `SIG_DFL`/`SIG_IGN`/핸들러 | 27 |
| `sa_restorer` | 핸들러가 `ret`했을 때 돌아갈 사용자 코드. 레지스터 복원과 원래 EIP 복귀를 맡는다 | 29 |
| 프로세스 그룹(`pgrp`)·세션(`session`)·리더(`leader`) | tty 시그널 배달 단위와 SIGHUP 전파 단위 | 07 |
| `SA_ONESHOT` / `SA_NOMASK` | 한 번 쓰면 기본으로 되돌림 / 핸들러 실행 중 마스크를 저장·적용하지 않음 | 27 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- `tell_father`는 부모를 **깨우지 않는다**. 깨우는 코드는 `schedule()` 앞부분(`sched.c:117–119`)이다. "SIGCHLD가 부모를 깨운다"고 말할 때 이 두 단계를 분리해 말한다.
- 0.11의 `SIG_DFL`은 "종료" 하나뿐이다. 현대의 Term/Core/Stop/Ign 분류를 0.11에 투영하지 않는다. `TASK_STOPPED`로 보내는 코드는 0.11에 없다(`wait.h:9` 주석 "WUNTRACED not supported").
- `kill_pg`라는 함수는 0.11에 없다. tty 쪽 함수는 `tty_intr`(`tty_io.c:111`)이다.
- `do_signal`에서 `do_exit(1<<(signr-1))`의 인자는 "시그널 번호"가 아니라 비트 값이다. 종료 코드 해석을 현대 `WTERMSIG`와 같다고 단정하지 않는다.
- 시그널은 커널 모드 코드 실행 중에는 검사되지 않으므로, `TASK_UNINTERRUPTIBLE`로 자는 프로세스는 Ctrl-C로 못 깨운다. "Ctrl-C는 항상 통한다"고 말하지 않는다.
- 시연 B의 테스트 프로그램은 lab/에 추가한 사용자 바이너리이며 커널 원본 수정이 아님을 캡처 각주에 쓴다. 상태 변화도의 수치(비트값)는 코드 추론이고 GDB 캡처는 실제 관찰임을 구분한다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 4 | 핵심 질문과 지도(로드맵·구조도로 오늘 위치) |
| 05–09 | 14 | 배경: exit/wait/signal이 없던 시절의 문제, task_struct의 관련 필드, 9회차와의 연결 |
| 10–18 | 22 | `do_exit` 코드 읽기와 ZOMBIE 상태 변화도, `sys_waitpid` 코드와 옵션 비교 |
| 19–20 | 8 | 시연 A (do_exit → ZOMBIE → 부모 깨어남) |
| 21–31 | 24 | 시그널: 비트맵, 보내는 쪽(`send_sig`/`sys_kill`), 받는 쪽(`ret_from_sys_call`/`do_signal`), 프레임 구성, 처분 비교 |
| 32–35 | 10 | SIGKILL 특례, 마스크, exec/fork와 시그널, Ctrl-C 경로(참조) |
| 36–39 | 14 | 시연 B (kill + 핸들러 프레임), 시연 C (Ctrl-C, 사전 캡처 가능) |
| 40–43 | 12 | 질문의 답, 현대 커널 비교, 흔한 오해 |
| 44–46 | 6 | 이해 확인과 정리 |
| 예비 | 6 | 질의응답 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞부분 4, 배경 14, do_exit·waitpid 22, 시연 A 8, 시그널 24, 특례·Ctrl-C 10, 시연 B/C 14, 답·비교·오해 12, 확인·정리 6, 예비 6.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(40행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07 · 원 06→08 · 원 07→09 · 원 08→10 · 원 09→11+12(분할) · 원 10→13 · 원 11→14 · 원 12→15 · 원 13→16+17(분할) · 원 14→18 · 원 15→19 · 원 16→20 · 원 17→21 · 원 18→22 · 원 19→23 · 원 20→24+25(분할) · 원 21→26 · 원 22→27 · 원 23→28 · 원 24→29 · 원 25→30 · 원 26→31 · 원 27→32 · 원 28→33 · 원 29→34 · 원 30→35 · 원 31→36 · 원 32→37 · 원 33→38 · 원 34→39 · 원 35→40 · 원 36→41 · 원 37→42 · 원 38→43 · 원 39→44+45(분할) · 원 40→46.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| do_exit 후반부 분할 | 원 09 → 새 11+12 | 고아 입양(exit.c:108–114)과 ZOMBIE 전환·통지(exit.c:130–134)는 성격이 다른 두 주제에 코드 2스크린 분량 — 각각 하이라이트 확보 (+1) |
| sys_waitpid 분기·대기 분할 | 원 13 → 새 16+17 | 상태별 분기(STOPPED/ZOMBIE/기타)와 대기 루프(INTERRUPTIBLE → schedule → repeat/-EINTR)가 코드 2스크린 — 대기 루프는 상태 변화도(14) 부수 상태와도 연결 (+1) |
| 시그널 검사 시점·조건 분할 | 원 20 → 새 24+25 | "언제(타이머 후·시스템 콜 후 두 곳뿐, 주석 12–15 + timer_interrupt 176–197)"와 "조건(task[0] 제외, CS==0x0f·OLDSS==0x17, 101–108)"을 분리 — "Ctrl-C가 즉시가 아닌 이유"에 전용 슬라이드 배정 (+1) |
| 이해 확인 질문·정답 분할 | 원 39 → 새 44+45 | 원문 "먼저 질문만 띄우고 클릭으로 정답 노출"을 질문·정답 두 장으로 — 08회차 표준 구성과 동일 (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02 "지도"→로드맵/구조, 원 35·36 "정리"→정답, 원 39 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 40장 → 46장 (+6) | 목표 범위 44–50 안(00-common §5) |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- 루트 이미지 안 시그널 핸들러 테스트 프로그램(10 해당분) 준비: 시연 B용 `signal(SIGINT, handler); pause();` 프로그램 — 게스트 gcc 유무 확인, 없으면 사전 빌드 바이너리 또는 사전 캡처로 대체 (course-plan "PPTX 제작 전 확인 목록"의 시그널 핸들러 테스트 프로그램 항목). 테스트 프로그램은 lab/에 추가한 사용자 바이너리(커널 원본 수정 아님) — 캡처 각주 문구 확정.
- lab/ 빌드의 심볼명(`do_exit`/`_do_exit`, `sys_waitpid`/`_sys_waitpid`, `do_signal`/`_do_signal`, `sys_kill`/`_sys_kill`, `tty_intr`/`_tty_intr`의 `_` 접두 유무)과 줄 번호 확인 — 특히 `tell_father`는 static 함수라 lab 심볼 테이블에 없을 수 있음: `b tell_father`가 안 걸리면 `do_exit` 안에서 `s`/`n` 진행 또는 주소 중단점으로 대체.
- 조건부 중단점 `b tty_intr if mask==2` 동작 확인(시연 C) — 인라인·최적화 여부와 mask 인자 접근 가능성, 안 되면 `b tty_intr` + `p mask` 수동 확인.
- GDB에서 `task[N]` 배열 심볼 접근(`p/x task[<부모 인덱스>]->signal`, 기대 0x10000)과 `sys_waitpid` 프레임의 `p (*p)->exit_code` 지역 접근 확인 — 안 되면 `current`·`task` 주소 직접 조회로 대체.
- 시연 C 캡처 환경: QEMU `-serial`/콘솔 설정 — 콘솔 입력과 GDB 중단이 겹칠 때 키 입력 지연 대비, 원 계획대로 사전 캡처를 기본으로 하고 시간 남을 때만 라이브.
- 사전 캡처 확보: §5의 6장(01–06) — 파일명 규칙 `materials/10-exit-signal/captures/<두자리순번>-<설명>.png`, 사전 캡처는 모서리에 `기존 기록` 라벨. 시연 A 대체용 `plan/` 사전 캡처 로그 자산 확인.
- 슬라이드 줄 번호·심볼명은 src/ 기준으로 표기하고 lab/ 차이(줄 번호, `_` 접두)는 캡처 각주로 명시(00-common §1).
