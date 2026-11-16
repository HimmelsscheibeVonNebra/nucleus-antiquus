# 14회차 상세 슬라이드 제작 계획 — 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교

- 기준: materials/course-plan.md `# 14. 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/14-capstone.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 40장 → 이 계획 46장 (+6)
- 로드맵 위치: 파트 G «종합·실습» · 14/15

## 1. 회차 개요

- 핵심 질문: **`ls /` 한 줄에 지금까지 배운 것이 어떻게 모두 등장하는가?**
- 학습 목표 (course-plan 원문 계승):
  1. 셸 프롬프트에서 `ls /`를 치고 결과가 화면에 나오기까지의 전체 경로를 **하나의 지도**로 그리고, 각 구간을 담당한 회차(04~13)와 핵심 함수(파일:줄)를 말한다.
  2. 그 경로에서 태스크 상태(RUNNING/INTERRUPTIBLE/UNINTERRUPTIBLE/ZOMBIE)가 바뀌는 지점과 원인을 짚는다 — 셸의 read 대기, 자식의 디스크 대기, 부모의 wait 대기.
  3. 시스템 콜 진입(`int $0x80`)·하드웨어 인터럽트(IRQ0/IRQ1/IRQ14)·예외(페이지 폴트 14번)가 같은 한 명령 안에서 각각 언제 일어나는지 구분한다.
  4. 0.11의 각 메커니즘에 대해 현대 Linux의 개념 수준 대응물을 이름으로 짝지우고, 이 강좌가 다루지 않은 범위를 명확히 안다.
  5. 30년 넘게 바뀌지 않은 설계(프로세스 모델, fd, fork/exec/wait, 시그널, 캐시 계층)를 한 문장씩으로 말한다.
- 읽을 소스 범위 (원본 src 기준 — course-plan 원문 계승): 새 범위는 없고 이전 회차의 핵심 지점을 "지도의 좌표"로 재인용한다. 모든 줄 번호는 grep/sed로 재확인함.

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
| read(dirfd) | 12 | fs/read_write.c:72–77 | `S_ISDIR \|\| S_ISREG` → `file_read` |
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

- 상태 변화도·비교 범위 (course-plan 원문 계승):
  - **상태 변화도(태스크 두 개의 동시 추적)**: 셸(부모)과 ls(자식)의 state를 시간축 하나에 나란히. 셸: RUNNING → INTERRUPTIBLE(tty_read, secondary.proc_list) → RUNNING(Enter) → fork → waitpid로 INTERRUPTIBLE → SIGCHLD/tell_father로 RUNNING → read로 다시 INTERRUPTIBLE. 자식: RUNNING(copy_process) → exec(상태 변화 없음, 주소 공간만 교체) → 페이지 폴트마다 UNINTERRUPTIBLE(bread→wait_on_buffer→sleep_on) ↔ RUNNING(hd_interrupt→end_request→wake_up) → write 중 RUNNING → do_exit로 ZOMBIE → release로 소멸. 각 전환의 원인·변경 데이터(state, counter, signal, b_lock/b_uptodate, exit_code)·유지 조건을 표로.
  - **모드·선택지 비교 ①(진입 방식)**: 범위 = `ls /` 한 번 동안 커널에 들어가는 **모든 종류의 진입** — 시스템 콜(0x80, system gate DPL3), 타이머 IRQ0(0x20, intr gate), 키보드 IRQ1(0x21, trap gate), 디스크 IRQ14(0x2E, hd_interrupt), 페이지 폴트 예외(14, trap gate). 열: 게이트 종류 / 등록 위치(파일:줄) / IF 자동 차단 여부 / 스택 전환 여부 / 이 명령에서 발생 시점.
  - **모드·선택지 비교 ②(0.11 vs 현대 — 개념 수준)**: 범위 = 이 강좌에서 다룬 0.11 메커니즘 전부(아래 슬라이드 33–39). 열: 0.11 메커니즘(파일:줄) / 현대 Linux 대응 개념 / 바뀐 이유 한 줄 / 이 강좌에서 다룸 여부.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 14. 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교 | 표지 | 대제목 `14. 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교` · 부제(핵심 질문 원문): "`ls /` 한 줄에 지금까지 배운 것이 어떻게 모두 등장하는가?" · 우상단 `Linux 0.11` 배지 + `1991`, 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `14/15 · 파트 G «종합·실습»` | — | 표지 배지·푸터(00-common §1) · 배경 QEMU `ls /` 결과 캡처(lab, 수정 없음) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "`ls /` 한 줄에 지금까지 배운 것이 어떻게 모두 등장하는가?" · 오늘의 두 부분 안내: (1) 전체 경로 지도, (2) 현대 커널 비교 · 원 "지도" 슬라이드(원 02) 문구 계승: "오늘은 새 소스가 아니라 04~13의 좌표를 하나의 경로에 꿰는 회차" · 오늘의 길: 10단계 미니 지도 — 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다님(빠짐없이 강조) | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 14만 ORANGE 강조 · 완료(TEAL) 01–13 전부, 이후(MUTED) 15 하나 · 오늘 한 줄 문구와 13→14·14→15 연결 화살표 문구는 §3 명세 · 파트 G «종합·실습»의 첫 회차 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위: `ls /` 전체 경로 | 구조 | 하이라이트 방식 특수(종합 회차): 누적 강조가 아니라 "전체 점등" — `ls /` 한 줄이 지나는 하위 시스템 전체 경로 화살표(ORANGE): 키보드 → sh → fork → exec(ls) → namei/inode → buffer → hd → console · 경로가 지나는 파일 상자 전부 진하게 · 세부 명세는 §3 | §1 읽기 범위 표 전체(경로가 지나는 파일 전부) | 커널 구조도(§3 명세 — 전체 점등 관점) |
| 05 | 오늘의 추적 규칙 | 배경 | 한 명령을 따라가며 세 가지만 기록: (1) 지금 어느 태스크가 RUNNING인가, (2) 커널에 어떻게 들어왔나(시스템 콜/IRQ/예외), (3) 어떤 자료구조가 바뀌었나 · 호출 순서도와 상태도를 구분한다는 2회차 약속 재확인 | — | 세 가지 기록 규칙 박스(상태·진입·데이터) |
| 06 | 큰 지도 (1판) | 구조 | 한 장짜리 지도: 9개 구간 박스를 시계 방향으로 — ① 키 입력·tty_read(13) ② fork(06) ③ exec(09) ④ 페이지 폴트 적재(08) ⑤ open/read "/"(12) ⑥ 버퍼 캐시·hd(11) ⑦ write → 콘솔(13) ⑧ exit/wait(10) ⑨ schedule(05) · 테두리 전체에 "int $0x80 진입/복귀(04)"와 "타이머 틱(05)"이 어디서나 끼어듦을 표시 · 이후 09–21(새 번호)에서 이 지도의 한 박스씩 확대 | §1 읽기 범위 표 전체(9개 구간 좌표) | 큰 지도 1판 다이어그램(§4 상세 명세) |
| 07 | 지도를 읽는 법: 세 축 | 배경 | 같은 지도에 세 종류의 화살표 범례: 실선=함수 호출, 점선=상태 변화(잠듦/깨움), 번개=하드웨어 인터럽트 · 타임라인 축(위)에 셸/ls 두 태스크 레인 | — | 세 축 화살표 범례 + 두 레인 타임라인 축(§4) |
| 08 | 전제: lab 환경의 셸과 ls | 배경 | lab 루트 FS의 `/bin/sh`와 `ls`는 외부 바이너리이며 소스는 이 강좌 범위 밖 · 실제 ls는 opendir/stat을 추가로 부르지만 오늘은 최소 경로(open·read·write·exit)만 추적한다고 선언 · 셸 내부 동작은 1회차 40장과 같이 "결과에서 추론"으로 표시 | —(전제 선언) | 선언 박스(lab 루트 FS의 /bin/sh·ls) |
| 09 | ① 키 입력 → 셸의 read가 깨어남 (13) | 코드 | 지도 박스 ① 확대 · keyboard.S:37–53·88–110 → tty_io.c:145–228 → wake_up(227) → tty_read(230–288)가 `put_fs_byte`로 "ls /\n" 5바이트 복사 · 셸 상태: INTERRUPTIBLE → RUNNING · 커널 진입 종류: IRQ1(글자마다), 복귀는 sys_read의 ret_from_sys_call | kernel/chr_drv/keyboard.S:37–53, 88–110 · kernel/chr_drv/tty_io.c:145–228, 227, 230–288 · fs/read_write.c:55–80 | 지도 박스 ① 확대도 + 셸 상태 전환 도식 |
| 10 | 시스템 콜 테두리 — 진입 (04) | 코드 | 지도 테두리 확대(전반) · system_call.s:80–100: `cmpl $nr_system_calls-1`, 세그먼트 설정(ds/es=0x10, fs=0x17), `call _sys_call_table(,%eax,4)` · 복귀 전 `state`/`counter` 검사 → `reschedule` | kernel/system_call.s:80–100 · kernel/sched.c:411 | 코드 인용(80–100) — 진입 어셈블리 |
| 11 | 시스템 콜 테두리 — 복귀와 실행 횟수 (04) | 코드 | 지도 테두리 확대(후반) · system_call.s:101–119: 사용자 모드 복귀 시 시그널 검사 → do_signal · 오늘 경로에서 이 코드가 최소 6번(read, fork, execve, open, read, write, exit, waitpid…) 실행됨을 표로 | kernel/system_call.s:101–119 · kernel/sched.c:411 | 시스템 콜 실행 횟수 표 |
| 12 | ② 셸이 fork한다 (06) | 코드 | 지도 박스 ② · system_call.s:208–219 → fork.c:68–133 · 복사되는 것(task_struct 한 페이지, LDT, TSS, filp 참조 카운트)과 공유되는 것(페이지, 읽기 전용으로 — memory.c:150–189, `mem_map[]++` 183) · `p->counter = p->priority`(85), 자식 state=RUNNING · 부모·자식 모두 `int $0x80` 복귀 지점에서 재개(6회차 답) | kernel/system_call.s:208–219 · kernel/fork.c:68–133, 85 · mm/memory.c:150–189, 183 | 복사/공유 2열 도식(§4, 06회차 도식 언어 재사용) |
| 13 | ③ 자식이 exec한다 (09) | 코드 | 지도 박스 ③ · system_call.s:200–205 → exec.c:182–353 · 이름 탐색(12회차와 같은 namei), a.out 헤더 읽기(bread 한 번 — 11회차), `free_page_tables`로 fork가 공유한 페이지 반납, `change_ldt`(333), `create_tables`(334), `eip[0] = ex.a_entry`(344) · PID 불변, 주소 공간만 교체(9회차 답) · 코드 자체는 아직 메모리에 없다는 점 강조 | kernel/system_call.s:200–205 · fs/exec.c:182–353, 333, 334, 344 | exec 단계 도식(§4, 09회차 도식 언어 재사용) |
| 14 | ④ 첫 명령어에서 페이지 폴트 (08) | 코드 | 지도 박스 ④ · iret로 `a_entry`에 가자마자 예외 14 → page.s:14–32 → `do_no_page`(memory.c:365–397): `current->executable`(374) → `bmap`(385) 4블록 → `bread_page`(386) → `put_page`(393) · 자식 state: 디스크 대기 동안 UNINTERRUPTIBLE · ls 바이너리 크기에 따라 몇 번 일어나는지는 시연 B(29장)에서 센다 | mm/page.s:14–32 · kernel/traps.c:199 · mm/memory.c:365–397, 374, 385, 386, 393 | 폴트 → do_no_page 시퀀스 도식(08회차 도식 언어 재사용) |
| 15 | ⑤ open("/") (12) | 코드 | 지도 박스 ⑤ · open.c:138–185 → namei.c:337–410 `open_namei` → `dir_namei`(278–294) → `get_dir`(228–270): 경로가 "/"뿐이므로 `current->root`의 inode를 그대로 → `iget`(inode.c:244–292, 캐시 히트면 디스크 접근 없음) · `file_table[]` 슬롯과 `filp[3]` 연결 | fs/open.c:138–185 · fs/namei.c:337–410, 278–294, 228–270 · fs/inode.c:244–292 | 경로 탐색 사슬 open_namei→dir_namei→get_dir→iget(12회차 언어 재사용) |
| 16 | ⑥ read(dirfd) → 디렉터리 블록 (12→11) | 코드 | 지도 박스 ⑤→⑥ · read_write.c:72–77 `S_ISDIR \|\| S_ISREG` → `file_read`(file_dev.c:17–46): `bmap`(inode.c:140–143)으로 논리 블록→물리 블록, `bread`(buffer.c:267–281) · 디렉터리 엔트리 `struct dir_entry`(fs.h:157–160, 16바이트) 그림 · 사용자 공간으로 `put_fs_byte` 루프 | fs/read_write.c:72–77 · fs/file_dev.c:17–46 · fs/inode.c:140–143 · fs/buffer.c:267–281 · include/linux/fs.h:157–160 | dir_entry 16바이트 구조 그림(§4, 12회차 그림 재사용) |
| 17 | ⑥ 버퍼 캐시 히트/미스 — 요청과 잠듦 (11) | 코드 | 지도 박스 ⑥ 확대(전반) · `getblk`(206–251) → 해시 히트면 끝 · 미스면 `ll_rw_block`(ll_rw_blk.c:145–155) → `make_request`(88–143) → `add_request`(64–86, `(dev->request_fn)()`) → `do_hd_request`(hd.c:294–341, `hd_out` 180–200에서 `do_hd=read_intr`) · `wait_on_buffer`(buffer.c:36–41, `sleep_on`) | fs/buffer.c:206–251, 36–41 · kernel/blk_drv/ll_rw_blk.c:145–155, 88–143, 64–86 · kernel/blk_drv/hd.c:294–341, 180–200 | 요청 경로 화살표(실선=호출, 07 범례 공유) |
| 18 | ⑥ 버퍼 캐시 완료 — IRQ14에서 깨어나기 (11) | 코드 | 지도 박스 ⑥ 확대(후반) · IRQ14 → `_hd_interrupt`(system_call.s:221–250) → `read_intr`(hd.c:250–267) → `end_request`(blk.h:109–125) → `unlock_buffer`(blk.h:101–107, `wake_up(&bh->b_wait)`) · 11회차 답: "read()가 디스크에 가는 때 = 캐시 미스일 때만" | kernel/system_call.s:221–250 · kernel/blk_drv/hd.c:250–267, 346 · kernel/blk_drv/blk.h:101–125, 106, 109–125 | 완료 경로 화살표(번개=IRQ 표기, 07 범례 공유) |
| 19 | ⑦ write(1, …) → 화면 (13) | 코드 | 지도 박스 ⑦ · ls가 결과를 write(1, …) → read_write.c:83–96 → `rw_char` → `tty_write`(290–326, ONLCR로 CR 삽입) → `con_write`(console.c:445–500, VGA 메모리에 2바이트씩) → `set_cursor`(600–616) · fd 1은 fork로 복사된 셸의 fd(1회차 37–38장의 open/dup) | fs/read_write.c:83–96 · kernel/chr_drv/tty_io.c:290–326 · kernel/chr_drv/console.c:445–500, 600–616 | write 경로 + VGA 2바이트 도식(13회차 도식 언어 재사용) |
| 20 | ⑧ exit와 wait (10) | 코드 | 지도 박스 ⑧ · `do_exit`(exit.c:102–135): `free_page_tables`(106–107), `iput`(118–122), `tell_father`(132, 83–100: 부모 signal에 SIGCHLD), `state = TASK_ZOMBIE`, `schedule()` · 셸 쪽: `sys_waitpid`(142–195)가 INTERRUPTIBLE로 자다가 깨어나 `exit_code` 회수 후 `release`(exit.c:19–33) · 10회차 답: "부모는 SIGCHLD로 안다" | kernel/exit.c:102–135, 106–107, 118–122, 132, 83–100, 142–195, 19–33 | 부모·자식 타임라인 미니(10회차 도식 언어 재사용) |
| 21 | ⑨ 그 사이 schedule은 몇 번? (05) | 코드 | 지도 박스 ⑨ · 경로 중 schedule() 호출 지점 목록: sleep_on/interruptible_sleep_on 안(tty_read·wait_on_buffer·waitpid), do_exit 끝, system_call.s:96–99 `reschedule`(counter==0 또는 state≠0), do_timer(sched.c:332–335, cpl≠0일 때만) · `schedule`(104–142) 선택 규칙과 `switch_to`(sched.h:171–184 `ljmp`) · 5회차 답과 연결 | kernel/sched.c:104–142, 305–336, 151–165, 167–186, 188–193 · kernel/system_call.s:96–99 · include/linux/sched.h:171–184 | schedule 호출 지점 목록 표 |
| 22 | 큰 지도 (2판: 좌표 기입) | 구조 | 06장의 지도에 각 박스마다 파일:줄 좌표와 진입 종류(syscall/IRQ/예외)를 채운 완성판 · 인쇄용 1장 | §1 읽기 범위 표 전체(각 박스 좌표·진입 종류) | 큰 지도 2판 완성판(§4) — 인쇄용 |
| 23 | 상태 변화도 (1/2): 셸과 ls 두 레인 | 상태도 | 시간축 하나에 셸(부모)과 ls(자식)의 state를 나란히 · 셸: RUNNING → INTERRUPTIBLE(tty_read, secondary.proc_list) → RUNNING(Enter) → fork → waitpid로 INTERRUPTIBLE → SIGCHLD/tell_father로 RUNNING → read로 다시 INTERRUPTIBLE · 자식: RUNNING(copy_process) → exec(상태 변화 없음, 주소 공간만 교체) → 페이지 폴트마다 UNINTERRUPTIBLE(bread→wait_on_buffer→sleep_on) ↔ RUNNING(hd_interrupt→end_request→wake_up) → write 중 RUNNING → do_exit로 ZOMBIE → release로 소멸 | §1 상태 변화도 범위(전환별 좌표는 §1 표) | 두 레인 상태 다이어그램(§4 핵심 상세 명세) |
| 24 | 상태 변화도 (2/2): 전환의 원인·데이터·유지 조건 | 상태도 | 각 전환의 원인(함수:줄)과 바뀐 필드 표: state, counter, signal, b_lock/b_uptodate, exit_code · 유지 조건: 줄 미완성, b_lock==1, 자식 ZOMBIE 없음 · ZOMBIE→소멸은 `release`에서 `task[]` 슬롯 NULL | kernel/exit.c:19–33 · (전환별 좌표는 §1 표) | 전환 상세 표(§4 상세 명세) |
| 25 | 비교 ①: 이 한 명령 동안의 커널 진입 다섯 종류 | 비교 | 표: 0x80 system gate(sched.c:411, DPL3, IF 유지) / IRQ0 0x20 intr gate(409, IF 차단) / IRQ1 0x21 trap gate(console.c:683, IF 유지) / IRQ14 0x2E intr gate(hd.c:346, IF 차단) / 예외 14 trap gate(traps.c:199) · 열: 게이트 종류 / 등록 위치(파일:줄) / IF 자동 차단 여부 / 스택 전환 여부(CPL3→0일 때만 TSS esp0) / 이 명령에서 발생 시점 | kernel/sched.c:409, 411 · kernel/chr_drv/console.c:683 · kernel/blk_drv/hd.c:346 · kernel/traps.c:199 | 진입 5종 비교표 |
| 26 | 데이터 흐름 한 장 | 코드 | "ls /\n" 5바이트가 read_q→secondary→셸 버퍼로 · "/" 디렉터리 1024바이트 블록이 hd→buffer→ls 버퍼로 · 출력 문자열이 ls 버퍼→write_q→0xb8000으로 · 복사 횟수와 `get_fs_byte/put_fs_byte`(fs=0x17) 경계를 표시 | kernel/chr_drv/tty_io.c(큐) · kernel/chr_drv/console.c(0xb8000) · fs/buffer.c | 세 데이터 흐름 다이어그램(§4) |
| 27 | 시연 A: 중단점 열 개로 한 명령 녹화 | 시연 | GDB에서 `b sys_fork`, `b do_execve`, `b do_no_page`, `b sys_open`, `b file_read`, `b bread`, `b do_hd_request`, `b con_write`, `b do_exit`, `b sys_waitpid`에 각각 `commands … p current->pid … c end`를 걸어 멈추지 않고 로그만 남김 · `set logging file build/gdb-14-ls.txt`, `set logging on`, `c` · 셸에 `ls /` 한 번 입력 후 로그를 지도 순서와 대조 | kernel/fork.c · fs/exec.c · mm/memory.c · fs/open.c · fs/file_dev.c · fs/buffer.c · kernel/blk_drv/hd.c · kernel/chr_drv/console.c · kernel/exit.c(중단점 대상 함수들) | GDB 명령 블록 · 캡처 01(§5) |
| 28 | 시연 A 캡처 | 캡처 | GDB 로그 캡처(lab, 수정 없음) · 각주: 중단점 순서가 지도 순서와 다른 곳(예: do_no_page가 exec 직후 여러 번, bread가 open 전에 exec 헤더 읽기로 먼저 등장)을 빨간 표시 — 관찰이 추론을 교정한 사례 | (관찰 — GDB 로그) | materials/14-capstone/captures/01-gdb-ls-breakpoint-log.png(§5) |
| 29 | 시연 B: 페이지 폴트와 디스크 접근 세기 | 시연 | `ignore` 카운트 대신 `b do_no_page` / `b do_hd_request`에 `commands silent; set $pf=$pf+1; c; end`로 횟수만 셈 · `ls /`를 두 번 실행해 두 번째에는 `do_hd_request` 횟수가 0 또는 크게 줄어드는지(버퍼 캐시 히트) 확인 · 기대: do_no_page는 두 번 모두 비슷(exec마다 새 페이지), do_hd_request는 두 번째가 감소 | mm/memory.c:365–397(do_no_page) · kernel/blk_drv/hd.c:294–341(do_hd_request) | GDB 명령 블록 · 캡처 02(§5) |
| 30 | 시연 B 캡처 | 캡처 | 두 번 실행의 카운트 표 캡처 · 각주: 정확한 숫자는 ls 바이너리 크기·루트 FS 이미지·QEMU 설정에 따라 다르므로 "경향"만 결론으로 | (관찰 — 카운트 표) | materials/14-capstone/captures/02-gdb-counts-two-runs.png(§5) |
| 31 | 관찰이 가르쳐 준 것 | 정리 | 추론(지도)과 관찰(로그)의 차이 3가지 정리: 순서 역전(exec 헤더 bread), 반복 횟수(폴트는 페이지 단위), 타이머 틱이 아무 데나 끼어듦(do_timer 로그를 함께 켜면 보임) | —(관찰 vs 추론) | 관찰/추론 차이 3가지 2열 정리 |
| 32 | 비교 ②를 읽는 규칙 | 배경 | "개념 수준" 선언: 현대 커널 소스를 읽지 않았고 VM도 없으므로 이름과 역할만 대응시킨다 · 버전 번호·줄 번호·성능 수치는 말하지 않는다 · 표의 4열(0.11 메커니즘·파일:줄 / 현대 개념 / 왜 바뀌었나 / 이 강좌에서 다룸 여부) | —(선언) | 비교 ② 공통 4열 머리글 |
| 33 | 비교 ②-1: 태스크와 문맥 전환 | 비교 | `task[64]` 고정 배열(sched.h:4, fork.c:141–143 선형 탐색) ↔ pid 해시·idr 기반 동적 관리 · `switch_to`의 TSS `ljmp`(sched.h:171–184) ↔ 소프트웨어 문맥 전환(TSS는 esp0/IO 비트맵용으로만) · `counter/priority`(sched.c:137–139) ↔ CFS·EEVDF 같은 가중 공정 스케줄러 · 단일 CPU 전제 ↔ 런큐 per-CPU | include/linux/sched.h:4, 171–184 · kernel/fork.c:141–143 · kernel/sched.c:137–139 | 비교 ② 공통 4열 표 |
| 34 | 비교 ②-2: 주소 공간 | 비교 | 태스크당 64MB 고정 세그먼트(fork.c:52 `nr*0x4000000`, exec.c:161) ↔ `mm_struct`와 VMA 목록으로 임의 배치 · 세그먼트+페이징 2단계 ↔ 평탄 세그먼트, 페이징만(다단계 페이지 테이블) · `mem_map[]` 바이트 참조 카운트(memory.c:183, 96–97) ↔ `struct page`와 버디/슬랩 할당기 | kernel/fork.c:52 · fs/exec.c:161 · mm/memory.c:183, 96–97 | 4열 표 |
| 35 | 비교 ②-3: 페이지 폴트·COW·적재 | 비교 | `do_no_page`가 실행 파일에서 직접 `bread_page`(memory.c:386) ↔ 페이지 캐시 기반 mmap 매핑과 파일 기반 폴트 처리 · `do_wp_page`/`un_wp_page`(247–259, 221–238) ↔ 같은 원리의 COW, 다만 익명 페이지·rmap·THP 등이 붙음 · 원리 동일, 자료구조 상이 | mm/memory.c:386, 247–259, 221–238 | 4열 표 |
| 36 | 비교 ②-4: 파일 시스템과 캐시 | 비교 | Minix fs 하나가 곧 "파일 시스템 코드"(namei.c, inode.c) ↔ VFS 계층(`inode`/`dentry`/`file` 객체와 연산 테이블) 아래에 여러 fs · `NR_INODE 32`, `NR_FILE 64`, `NR_OPEN 20`(fs.h:43–45) 고정 ↔ 동적 할당과 큰 한도 · `buffer_head` 해시(buffer.c:31, NR_HASH 307) 블록 캐시 ↔ 페이지 캐시(buffer_head는 보조) · 디렉터리를 read()로 읽음(read_write.c:72–77, getdents 없음 — unistd.h에 readdir 계열 번호 없음) ↔ getdents 계열 | fs/namei.c · fs/inode.c · include/linux/fs.h:43–45, 43–47 · fs/buffer.c:31 · fs/read_write.c:72–77 | 4열 표 |
| 37 | 비교 ②-5: 블록 I/O와 인터럽트 | 비교 | `request[]` 배열과 `do_hd=read_intr` 함수 포인터 콜백(hd.c:190, 262) ↔ 블록 계층(bio/요청 큐/멀티큐)과 드라이버 분리 · PIC 8259 + 고정 벡터(0x20/0x21/0x2E) ↔ APIC/IRQ 도메인, 상반부/하반부(softirq·threaded IRQ) · 인터럽트 안에서 `copy_to_cooked` 직접 실행 ↔ 지연 처리로 분리 | kernel/blk_drv/hd.c:190, 262 · kernel/chr_drv/tty_io.c:145–228(copy_to_cooked) | 4열 표 |
| 38 | 비교 ②-6: 터미널과 시스템 콜 표 | 비교 | 콘솔 1 + rs 2 고정(tty_io.c:51–92), con_write가 VGA에 직접 쓰기 ↔ tty 코어 + line discipline + 가상 콘솔/pty/프레임버퍼 · `sys_call_table[72]`(sys.h:74–86; system_call.s:61 `nr_system_calls = 72`)와 `int $0x80` ↔ 수백 개 표와 `syscall`/`sysenter` 빠른 진입, 아키텍처별 표 · 시그널 비트마스크 32개(`signal`/`blocked` long) ↔ 실시간 시그널·큐잉 | kernel/chr_drv/tty_io.c:51–92 · include/linux/sys.h:74–86 · kernel/system_call.s:61 | 4열 표 |
| 39 | 이 강좌가 다루지 않은 것 | 비교 | 분명히 표시: SMP/락킹/선점, 커널 모듈·sched_ext(15회차 노트 참조), 네트워킹, VFS 실제 코드, ext4 등 현대 fs, 가상 메모리의 스왑(0.11 swap 없음), 보안(권한 검사 일부만), 64비트, 전원 관리, 장치 트리/ACPI, 컨테이너·cgroup·namespace, 현대 부팅(UEFI·initramfs) · "0.11이 작아서 생략된 것"과 "강좌 범위라서 생략한 것"을 두 열로 구분 | —(범위 선언) | 두 열 구분 표("작아서 생략" vs "범위라서 생략") |
| 40 | 바뀌지 않은 것 | 정리 | 한 줄씩: 프로세스 = 주소 공간 + 커널 스택 + 상태; fd 번호로 파일·장치를 같은 read/write로 다룸; fork/exec/wait/exit 네 동작의 분업; 시그널 = 비동기 통지 비트; 캐시 미스일 때만 장치에 감; 잠들기·깨우기는 대기열과 상태 전환; 사용자/커널 경계는 항상 게이트를 통해서만 · 각 항목 옆에 오늘 지도에서의 위치 번호 | —(종합) | 7항목 리스트 + 지도 위치 번호 대응 |
| 41 | 왜 0.11로 배웠나 (성찰) | 정리 | 1만 줄 안에 위 7가지가 전부 있고 GDB로 한 명령을 끝까지 쫓을 수 있다는 점 · 반대로 0.11의 단순화(단일 CPU, 고정 배열, 동기 콘솔)가 현대 설계 결정의 이유를 보여 준다는 점 · 수강생에게 "현대 커널에서 같은 지도를 그린다면 어느 박스가 가장 많이 쪼개질까"를 묻고 넘어감(답: ⑥과 ⑨) | —(성찰) | 수강생 질문 박스(답: ⑥과 ⑨) |
| 42 | 핵심 질문의 답 | 정답 | 지도 2판을 축소해 다시 보이며 한 문장: "`ls /`는 13→06→04→09→08→12→11→13→10→05 순으로 10개 회차를 지나며, 그 사이 커널 진입은 시스템 콜·IRQ0/1/14·예외 14 다섯 종류가 섞여 일어난다." | §1 읽기 범위 표 전체(요약) | 큰 지도 2판 축소판(§4) |
| 43 | 이해 확인 질문 | 확인 | 4문항 질문만 게시(§6 원문 그대로) · 진입 종류 수 / exec 직후 코드의 메모리 여부와 적재 시점 / 두 번째 `ls /`의 디스크 접근·페이지 폴트 / `task[64]`와 TSS `ljmp`의 현대 대응 | (정답 근거 — §6) | 문항 4개 텍스트 |
| 44 | 이해 확인 정답 | 확인 | 정답과 근거 줄 번호(§6 원문 그대로) · 1번 다섯 종류(sched.c:411, 409, console.c:683, hd.c:346, traps.c:199) · 2번 없다 — `do_no_page`가 `bread_page`로 가져온다(exec.c:319–321, memory.c:365–397) · 3번 버퍼 캐시 `getblk` 해시 히트(buffer.c:206–251), `do_no_page`는 exec마다 재발 · 4번 pid 해시/idr 기반 동적 태스크 관리와 소프트웨어 문맥 전환 | kernel/sched.c:409, 411 · kernel/chr_drv/console.c:683 · kernel/blk_drv/hd.c:346 · kernel/traps.c:199 · fs/exec.c:319–321 · mm/memory.c:365–397 · fs/buffer.c:206–251 | 정답 4개 텍스트 |
| 45 | 정리 | 정리 | 오늘 만든 지도 2판과 두 레인 상태도, 비교표의 4열 규칙 · 수강생이 가져갈 것: 지도 1장(인쇄) | — | 지도 2판·두 레인 상태도 썸네일 |
| 46 | 다음 회차 예고 | 정리 | 15회차: 이 지도의 테두리(sys_call_table)에 항목 하나를 추가하고 박스 ⑨(schedule)의 선택 규칙을 바꾼 뒤 같은 GDB 방법으로 확인 · "읽기"에서 "바꾸기"로 | —(15회차 예고) | 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: G «종합·실습» · 14/15 — 파트 G의 첫 회차. 완료(TEAL) 01–13 전부(13개 상자), 오늘(ORANGE + 굵은 테두리) 14, 이후(MUTED)는 15 하나뿐(00-common §2 "14·15회차는 01–13 완료 처리" 규칙).
- 오늘 한 줄 문구: "한 줄(`ls /`)에 04–13의 좌표가 전부 등장한다 — 새 소스 없이 하나의 경로로 잇는다"
- 13→오늘 연결 화살표 문구: "이제 키보드 입력부터 디스크까지 전부 봤다 — 한 줄로 잇는다"
- 오늘→15 연결 화살표 문구: "직접 바꿔보자 — 커널 수정 실습"
- 원 "지도" 슬라이드(원 02) 내용 계승: "오늘은 새 소스가 아니라 04~13의 좌표를 하나의 경로에 꿰는 회차"임을 오늘 상자 아래 각주로 명시. 완료 상자 01–13은 전부 완료이므로 개별 라벨 없이 파트 라벨(A–G)만 유지.

### 슬라이드 04 커널 구조도 — 오늘의 범위

- 하이라이트 방식(특수 — 종합 회차): 누적 강조가 아니라 **"전체 점등"**. 오늘 다루는 범위 = "`ls /` 한 줄이 지나는 하위 시스템 전체"이므로, 지난 회차를 옅은 TEAL로 남기는 누적 방식 대신 경로가 지나는 파일 상자 전부를 동일하게 진하게(진한 TEAL) 채운다.
- 오늘의 전체 경로 화살표(ORANGE, 1개 — 출발→경유→도착): 키보드 → sh → fork → exec(ls) → namei/inode → buffer → hd → console. 사용자 공간(sh·ls)에서 시작해 커널 전 계층(프로세스·메모리·fs·blk_drv·chr_drv)을 지나 하드웨어(키보드·hd)와 콘솔까지 걸치는 큰 화살표.
- 경로가 지나는 파일(전부 진하게): kernel/chr_drv/keyboard.S·tty_io.c·console.c, kernel/system_call.s(모든 진입의 경유점 — 테두리), kernel/fork.c, mm/page.s·mm/memory.c(폴트 적재), fs/exec.c, fs/open.c·fs/namei.c·fs/inode.c·fs/read_write.c·fs/file_dev.c, fs/buffer.c, kernel/blk_drv/ll_rw_blk.c·hd.c, kernel/exit.c, kernel/sched.c(전 구간 경유). include/linux/sched.h·include/linux/fs.h·include/linux/sys.h·include/unistd.h는 라벨로 표시.
- 우하단 `Linux 0.11` 라벨 유지. "전체 점등"으로 누적 규칙을 대체한 이유(종합 회차 — 지난 01–13 파일이 곧 오늘 경로)를 각주 한 줄로 명시.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(14 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 01–13 TEAL, 14 ORANGE, 15만 MUTED, 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(`ls /` 전체 점등) | 도형 다이어그램 | §3 명세 그대로 — 하위 시스템 전체를 지나는 ORANGE 경로 화살표 + 지나는 파일 전부 진하게 | 전 회차 공통 골격(01–13 누적 영역을 전체 점등으로 대체) |
| 06 | 큰 지도 (1판) | 도형 다이어그램 | 아래 상세 명세 — 9개 구간 박스 ①–⑨ 시계 방향, 박스마다 회차 번호, 테두리에 "int $0x80 진입/복귀(04)"·"타이머 틱(05)" 상시 끼어듦 표시 | — |
| 07 | 세 축 화살표 범례·두 레인 타임라인 | 도형 | 실선=함수 호출 / 점선=상태 변화(잠듦/깨움) / 번개=하드웨어 인터럽트, 위쪽 타임라인 축에 셸·ls 두 레인 | — |
| 09 | 지도 박스 ① 확대도 | 도형 | 큰 지도(06)에서 박스 ①만 ORANGE 부각, keyboard.S → tty_io.c → wake_up(227) → tty_read 사슬 | 13회차 키 입력 경로 도식 |
| 12 | 복사/공유 2열 도식 | 도형 | fork에서 복사되는 것(task_struct 한 페이지, LDT, TSS, filp 참조 카운트)과 공유되는 것(페이지, 읽기 전용) 2열 | 06회차 fork 도식 |
| 13 | exec 단계 도식 | 도형 | namei → a.out 헤더 bread → free_page_tables → change_ldt·create_tables → eip[0] = ex.a_entry, PID 불변 강조 | 09회차 exec 도식 |
| 14 | 폴트 → do_no_page 시퀀스 | 도형 | iret(a_entry) → 예외 14 → page.s → do_no_page(current->executable → bmap 4블록 → bread_page → put_page) | 08회차 요구 적재 도식 |
| 15 | 경로 탐색 사슬 | 도형 | sys_open → open_namei → dir_namei → get_dir(current->root) → iget, file_table[]와 filp[3] 연결 | 12회차 namei 사슬 도식 |
| 16 | dir_entry 16바이트 구조 그림 | 도형 | `struct dir_entry`(fs.h:157–160) 16바이트 레이아웃 | 12회차 dir_entry 그림 |
| 17 | 버퍼 캐시 요청 경로 화살표 | 도형 | getblk(해시 히트/미스 분기) → ll_rw_block → make_request → add_request((dev->request_fn)()) → do_hd_request·hd_out → wait_on_buffer(sleep_on) | 11회차 버퍼·요청 도식 |
| 18 | 버퍼 캐시 완료 경로 화살표 | 도형 | 번개(IRQ14) → _hd_interrupt → read_intr → end_request → unlock_buffer(wake_up(&bh->b_wait)) → 잠든 bread 복귀 | 11회차 완료 경로 도식 |
| 19 | write 경로 + VGA 2바이트 도식 | 도형 | write(1, …) → rw_char → tty_write(ONLCR) → con_write(VGA 2바이트씩) → set_cursor | 13회차 console 도식 |
| 20 | exit/wait 부모·자식 타임라인 미니 | 도형 | do_exit(free_page_tables·iput·tell_father SIGCHLD·TASK_ZOMBIE·schedule)와 sys_waitpid(잠듦→깨어남→exit_code 회수→release) | 10회차 exit·wait 도식 |
| 21 | schedule 호출 지점 목록 표 | 표 | sleep_on/interruptible_sleep_on 안(tty_read·wait_on_buffer·waitpid), do_exit 끝, system_call.s:96–99 reschedule, do_timer(cpl≠0) | 05회차 schedule 자료 |
| 22 | 큰 지도 (2판: 좌표 기입) | 도형 다이어그램 | 아래 상세 명세 — 06장 골격에 각 박스 파일:줄 좌표와 진입 종류(syscall/IRQ/예외) 기입 완성판, 인쇄용 | 06장(동일 골격) |
| 23 | 두 레인 상태 변화도 (핵심) | 도형 상태 다이어그램 | 아래 상세 명세 | 07장 세 축 범례 공유 |
| 24 | 전환 상세 표 | 표 | 전환별 원인(함수:줄) · 변경 데이터(state, counter, signal, b_lock/b_uptodate, exit_code) · 유지 조건(줄 미완성, b_lock==1, 자식 ZOMBIE 없음) | — |
| 26 | 세 데이터 흐름 다이어그램 | 도형 | "ls /\n" 5바이트(read_q→secondary→셸 버퍼) / "/" 디렉터리 1024바이트(hd→buffer→ls 버퍼) / 출력 문자열(ls 버퍼→write_q→0xb8000), get_fs_byte/put_fs_byte(fs=0x17) 경계 표시 | 11·13회차 버퍼·큐 도식 |
| 42 | 큰 지도 2판 축소판 | 도형 | 22장 축소판 — 핵심 질문의 답 한 문장과 병치 | 22장(동일 자료 축소) |

핵심 시각자료 상세 명세 — 큰 지도 (슬라이드 06·22가 같은 골격을 공유):

- 골격: 9개 구간 박스를 시계 방향으로 — ① 키 입력·tty_read(13) ② fork(06) ③ exec(09) ④ 페이지 폴트 적재(08) ⑤ open/read "/"(12) ⑥ 버퍼 캐시·hd(11) ⑦ write → 콘솔(13) ⑧ exit/wait(10) ⑨ schedule(05). 지도 테두리 전체에 "int $0x80 진입/복귀(04)"와 "타이머 틱(05)"이 어디서나 끼어듦을 표시.
- 1판(06): 박스마다 회차 번호만 기입. 본문(09–21)은 이 지도의 해당 박스를 ORANGE로 부각해 확대한다는 규칙을 선언.
- 2판(22): 각 박스마다 파일:줄 좌표(§1 읽기 범위 표)와 진입 종류(syscall/IRQ/예외)를 기입한 완성판 — 인쇄용 1장.

핵심 시각자료 상세 명세 — 두 레인 상태 변화도 (슬라이드 23·24가 같은 시각 언어를 공유):

- 공통 시각 언어: 시간축 좌→우, 레인 2개(위: 셸(부모), 아래: ls(자식)). 상태 구간 표기 — RUNNING = TEAL 채움, INTERRUPTIBLE·UNINTERRUPTIBLE = MUTED 외곽선(잠듦), ZOMBIE = INK 채움 + PAPER 라벨, 소멸 = 점선 끝. 전환 화살표는 07장의 세 축 범례(실선=함수 호출, 점선=상태 변화, 번개=하드웨어 인터럽트)를 공유. 우하단 `Linux 0.11` 라벨.
- 셸 레인(원문 순서 그대로): RUNNING → INTERRUPTIBLE(tty_read, secondary.proc_list) → RUNNING(Enter) → fork → waitpid로 INTERRUPTIBLE → SIGCHLD/tell_father로 RUNNING → read로 다시 INTERRUPTIBLE.
- ls 레인(원문 순서 그대로): RUNNING(copy_process) → exec(상태 변화 없음, 주소 공간만 교체 — 같은 상태 지속 + 주석) → 페이지 폴트마다 UNINTERRUPTIBLE(bread→wait_on_buffer→sleep_on) ↔ RUNNING(hd_interrupt→end_request→wake_up) 왕복 화살표 → write 중 RUNNING → do_exit로 ZOMBIE → release로 소멸.
- 슬라이드 24 표: 전환별 3열 — 원인(함수:줄) / 변경 데이터(state, counter, signal, b_lock/b_uptodate, exit_code) / 유지 조건(줄 미완성, b_lock==1, 자식 ZOMBIE 없음). ZOMBIE→소멸은 `release`에서 `task[]` 슬롯 NULL.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/14-capstone/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A | 01-gdb-ls-breakpoint-log.png | `scripts/run.sh`로 QEMU `-S -s`, GDB `target remote :1234` · 중단점 10개(`sys_fork`, `do_execve`, `do_no_page`, `sys_open`, `file_read`, `bread`, `do_hd_request`, `con_write`, `do_exit`, `sys_waitpid`)마다 `commands` / `silent` / `printf "<name> pid=%d\n", current->pid` / `continue` / `end` · `set logging file build/gdb-14-ls.txt`, `set logging on`, `c`, 셸에 `ls /` 입력 | 로그에 찍힌 이름·pid 순서 · 셸 pid와 ls pid가 fork 직후 갈라지는 지점 · `do_no_page`의 연속 등장 · `bread`가 `do_execve` 직후(헤더)와 `file_read` 뒤(디렉터리 블록)에 각각 등장 · 마지막 `do_exit`(자식) → `sys_waitpid`(부모 — 셸이 먼저 waitpid에 들어가 있으므로 로그에는 fork 직후에 찍힘) | 사전 캡처 `build/gdb-14-ls.txt`(기존 기록 라벨) · 심벌 문제 시 `info functions sys_fork`로 실제 이름 확인 |
| B | 02-gdb-counts-two-runs.png | `set $pf=0`, `set $hd=0`; `b do_no_page` → `commands; silent; set $pf=$pf+1; c; end`; `b do_hd_request` → 같은 방식으로 `$hd` · `ls /` 실행 후 Ctrl-C로 GDB 복귀, `p $pf`, `p $hd` · 0으로 리셋 후 두 번째 `ls /` | 두 실행의 `$pf`(두 번 비슷 — exec마다 새 주소 공간)과 `$hd`(두 번째 감소 — 버퍼 캐시 히트) | 사전 캡처 표 `build/gdb-14-counts.txt` · QEMU 디스크 캐시 설정에 따라 호스트 측 캐시는 보이지 않으며 게스트 커널의 요청 횟수만 셈을 명시 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜`(00-common §7). 표지 배경의 QEMU `ls /` 출력 캡처(lab, 수정 없음)도 사전 확보.

## 6. 이해 확인 질문과 정답

질문은 슬라이드 43, 정답은 슬라이드 44에 게시(원문 계승).

1. **Q.** `ls /` 한 번 동안 커널에 들어가는 방법은 몇 종류이고 각각 무엇인가? **A.** 다섯 종류 — `int $0x80` 시스템 콜(sched.c:411), 타이머 IRQ0(409), 키보드 IRQ1(console.c:683), 디스크 IRQ14(hd.c:346), 페이지 폴트 예외 14(traps.c:199).
2. **Q.** exec가 끝난 직후 ls의 코드는 메모리에 있는가? 없다면 언제 들어오는가? **A.** 없다. `do_execve`는 `current->executable`만 바꾸고(exec.c:319–321) 첫 명령어 실행 시 예외 14 → `do_no_page`(memory.c:365–397)가 `bread_page`로 가져온다.
3. **Q.** 두 번째 `ls /`에서 디스크 접근이 줄어드는 이유와, 그래도 페이지 폴트는 줄지 않는 이유는? **A.** 디렉터리 블록·ls 바이너리 블록이 버퍼 캐시(`getblk` 해시 히트, buffer.c:206–251)에 남아 `ll_rw_block`을 안 부르지만, exec는 매번 새 주소 공간을 만들므로 `do_no_page`는 다시 일어난다(폴트 처리 안에서 bread_page가 캐시 히트할 뿐).
4. **Q.** 0.11의 `task[64]`와 TSS `ljmp` 전환을 현대 커널은 무엇으로 바꿨는가(개념 이름만)? **A.** pid 해시/idr 기반 동적 태스크 관리와 소프트웨어 문맥 전환(TSS는 커널 스택 포인터 등 최소 용도로만).

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 지도의 좌표 | 이 강좌에서 "파일:줄"을 가리키는 말. 오늘은 새 코드를 읽지 않고 좌표만 다시 쓴다 | 02 |
| 상반부/하반부(top/bottom half) | 인터럽트 처리기에서 즉시 할 일과 미룰 일의 분리(현대 개념, 이름만) | 37 |
| VFS / dentry | 여러 파일 시스템을 같은 객체·연산 표로 다루는 계층과 그 경로 이름 캐시(현대 개념, 이름만) | 36 |
| 페이지 캐시 / struct page | 파일 내용을 페이지 단위로 캐시하는 현대 구조와 물리 페이지 하나의 기술자(이름만) | 34(struct page) · 35(페이지 캐시) |
| VMA / mm_struct | 프로세스 주소 공간을 구간 목록으로 기술하는 현대 구조(이름만) | 34 |
| EEVDF/CFS | 현대 리눅스의 공정 스케줄러 이름(이름만, 동작 설명 안 함) | 33 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승 — 슬라이드 번호만 새 번호로 바꿈)

- 현대 커널 비교는 **개념 이름의 대응**으로 제한한다. 현대 소스의 파일·줄·버전·수치를 말하지 않는다(VM이 선택되지 않아 검증할 수 없음).
- 시연 로그의 중단점 순서를 "지도가 틀렸다"로 말하지 않는다. 지도는 논리 순서, 로그는 시간 순서이며 28장(시연 A 캡처, 원 23장)에 차이의 이유를 적어 둔다.
- `ls`가 open/read/write/exit만 부른다고 단정하지 않는다. 실제 바이너리는 stat·brk 등을 더 부를 수 있고, 오늘은 최소 경로를 추적한다고 08장(전제, 원 06장)에서 선언한다.
- 셸이 waitpid로 "자식이 끝날 때까지 폴링한다"고 말하지 않는다. INTERRUPTIBLE로 잠들고 `tell_father`의 시그널로 깨어난다(exit.c:83–100, 142–195).
- "두 번째 실행은 캐시 덕분에 디스크를 전혀 안 읽는다"고 단정하지 않는다. 버퍼 수·다른 접근에 따라 달라지며 시연 B는 경향만 보인다.
- 비교표에서 "현대 커널이 0.11보다 복잡하므로 나쁘다/좋다"는 평가를 하지 않는다. 바뀐 이유 열에는 요구 사항(SMP, 다중 fs, 큰 메모리)만 적는다.
- 15회차 노트와 연결: 원래 계획된 "현대 커널 모듈"·"sched_ext" 회차는 선택되지 않은 현대 커널 VM이 필요하여 15회차의 0.11 수정 실습으로 대체되었다. 오늘 비교 슬라이드(32–39, 원 27–34)가 그 두 주제를 개념 수준에서만 대신한다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–05 | 5 | 핵심 질문, 표준 앞부분(로드맵·구조도 — 전체 점등), 추적 규칙, 오늘의 두 부분(전체 경로 / 비교) 안내 |
| 06–08 | 10 | 큰 지도 1판: 9개 구간과 회차 번호, 추적 규칙(상태·진입·데이터), 세 축 범례와 전제(lab 셸·ls) |
| 09–22 | 45 | 지도 구간별 재방문(각 3~4분): 13→06→04→09→08→12→11→13→10→05, 각 구간 코드 5줄과 좌표 · 마지막에 큰 지도 2판(좌표 기입) 완성 |
| 23–26 | 10 | 두 태스크 상태 변화도(두 레인 그림·전환 표), 진입 방식 비교, 데이터 흐름 한 장 |
| 27–31 | 20 | 강사 시연 A/B(GDB로 `ls /` 한 번 동안 중단점 순서 기록, 페이지 폴트 횟수 세기) + 관찰이 가르쳐 준 것 |
| 32–39 | 20 | 현대 커널 비교 8장(개념 수준) + 다루지 않은 것 |
| 40–42 | 5 | "바뀌지 않은 것", 왜 0.11로 배웠나, 핵심 질문의 답 |
| 43–46 | 5 | 이해 확인, 정리·15회차 예고 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞부분 5, 지도·전제 10, 구간 재방문 45, 상태도·비교·데이터 흐름 10, 시연 20, 현대 비교 20, 답·성찰 5, 마무리 5.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(40행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07 · 원 06→08 · 원 07→09 · 원 08→10+11(분할) · 원 09→12 · 원 10→13 · 원 11→14 · 원 12→15 · 원 13→16 · 원 14→17+18(분할) · 원 15→19 · 원 16→20 · 원 17→21 · 원 18→22 · 원 19→23+24(분할) · 원 20→25 · 원 21→26 · 원 22→27 · 원 23→28 · 원 24→29 · 원 25→30 · 원 26→31 · 원 27→32 · 원 28→33 · 원 29→34 · 원 30→35 · 원 31→36 · 원 32→37 · 원 33→38 · 원 34→39 · 원 35→40 · 원 36→41 · 원 37→42 · 원 38→43+44(분할) · 원 39→45 · 원 40→46.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| 시스템 콜 테두리 분할 | 원 08 → 새 10+11 | 진입 어셈블리(80–100)와 복귀(101–119)·"최소 6번 실행" 횟수 표가 한 장에 담기엔 밀도가 높음 — 표에 전용 슬라이드 배정 (+1) |
| 버퍼 캐시·hd 분할 | 원 14 → 새 17+18 | 요청 경로(getblk→…→잠듦)와 완료 경로(IRQ14→…→깨어남)가 함수 10개짜리 사슬 — 코드 2스크린 분량 (+1) |
| 상태 변화도 분할 | 원 19 → 새 23+24 | 두 레인 시간축 그림과 전환 상세 표(원인·변경 데이터·유지 조건)를 각각 배정 — 오늘의 핵심 시각자료 (+1) |
| 이해 확인 분할 | 원 38 → 새 43+44 | 질문 4문항과 정답(클릭 후 표시)을 질문·정답 슬라이드로 분리 — 타 회차(08 등) 구성과 통일 (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02·04·18 "지도"→로드맵/구조, 원 37 "정리"→정답, 원 38 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 40장 → 46장 (+6) | 목표 범위 44–50 안(00-common §5) |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- lab/ 빌드의 심볼명과 줄 번호 확인 — 시연 A 중단점 10개 전부(`sys_fork`, `do_execve`, `do_no_page`, `sys_open`, `file_read`, `bread`, `do_hd_request`, `con_write`, `do_exit`, `sys_waitpid`)의 lab 툴체인 심벌명(`_` 접두 유무 — `system_call.s`의 `_sys_fork`는 lab 툴체인 기준으로 확인). 심벌 문제 시 `info functions sys_fork`로 실제 이름 확인 (course-plan "PPTX 제작 전 확인 목록" 1번 항목의 14 해당분).
- GDB `commands` / `silent` / `printf` / `continue` 자동 계속 로깅 절차가 QEMU gdbstub(i386 원격)에서 의도대로 "멈추지 않고 로그만 남기는지" 사전 점검 — 시연 A·B 전체 절차의 전제.
- 사전 캡처 확보: `build/gdb-14-ls.txt`(시연 A 대체), `build/gdb-14-counts.txt`(시연 B 대체), 표지 배경 QEMU `ls /` 출력(lab, 수정 없음). 회차별 신규 캡처 보관처는 `materials/14-capstone/captures/<두자리순번>-<설명>.png` (course-plan 확인 목록 4번 항목).
- 캡처 각주에 lab 빌드·수정 없음·캡처 날짜 필수 기재 — 카운트 수치는 ls 바이너리 크기·루트 FS 이미지·QEMU 설정에 의존하므로 "경향"만 결론으로(§8).
- 큰 지도 2판(22장)·두 레인 상태도(23·24장)의 인쇄용 출력물 확인 — 45장 "수강생이 가져갈 것: 지도 1장(인쇄)"의 물량.
