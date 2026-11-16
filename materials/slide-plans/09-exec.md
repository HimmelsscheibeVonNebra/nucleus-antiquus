# 09회차 상세 슬라이드 제작 계획 — exec()와 프로그램 실행

- 기준: materials/course-plan.md `# 09. exec()와 프로그램 실행` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/09-exec.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 41장 → 이 계획 47장 (+6)
- 로드맵 위치: 파트 D «프로그램의 일생» · 09/15

## 1. 회차 개요

- 핵심 질문: **PID는 그대로인데 프로그램은 어떻게 바뀌는가?**
- 학습 목표 (course-plan 원문 계승):
  1. `execve()` 한 호출이 `lib/execve.c`의 `int $0x80` → `system_call.s`의 `_sys_execve` → `fs/exec.c`의 `do_execve`에 도달하고, 커널 스택에 저장된 EIP/ESP를 **덮어써서** 돌아가는 경로를 설명할 수 있다.
  2. a.out 헤더(`struct exec`)의 필드와 0.11이 받아들이는 형식(ZMAGIC만)·거부 조건(ENOEXEC 등)을 읽고, 실행 파일 하나가 어느 검사에서 걸리는지 말할 수 있다.
  3. "돌이킬 수 없는 지점"(exec.c:318) 이후 `free_page_tables`·`change_ldt`·`create_tables`가 주소 공간을 비우고 새 LDT 리밋과 인자 페이지만 남기는 과정을 태스크 데이터 변화로 추적할 수 있다.
  4. exec가 코드를 읽지 않는다는 점(요구 적재)과, 새 프로그램의 첫 명령이 08회차의 `do_no_page`로 적재된다는 연결을 설명할 수 있다.
  5. GDB에서 `do_execve`를 멈춰 LDT 베이스/리밋·`eip[0]`·`eip[3]`·`executable`이 바뀌고 `pid`는 그대로임을 관찰할 수 있다.
- 읽을 소스 범위 (원본 src 기준 — course-plan 원문 계승):

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

- 상태 변화도·비교 범위 (course-plan 원문 계승): 상태 변화도 ① 한 태스크의 "프로그램 상태"(구 프로그램 실행 중 → 검사 중 → 주소 공간 비움 → 새 프로그램 첫 명령 fetch → 코드 페이지 적재됨, 전환 원인·변경/유지 데이터 포함), 상태 변화도 ② 인자 문자열의 위치 변화(사용자 문자열 → page[31..] 꼭대기 → 64MB 끝 매핑 → 포인터 배열·argc → `eip[3]=p`), 비교 ① 실행 파일 형식(매직 3가지 + `#!` 스크립트 + 그 외 전부), 비교 ② do_execve의 오류 반환 경로(ENOENT, EACCES, ENOEXEC, ENOMEM 전부와 정의만 있는 E2BIG), 비교 ③ `copy_strings`의 `from_kmem` 3가지(0/1/2 전부).

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 09. exec()와 프로그램 실행 | 표지 | 대제목 `09. exec()와 프로그램 실행` · 부제(핵심 질문 원문): "PID는 그대로인데 프로그램은 어떻게 바뀌는가?" · 원 계획 부제 문구 "같은 몸, 다른 프로그램" · 우상단 `Linux 0.11` 배지 + `1991`, 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `09/15 · 파트 D «프로그램의 일생»` | — | 표지 배지·푸터(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "PID는 그대로인데 프로그램은 어떻게 바뀌는가?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치, 오늘 실제 다루는 단계만 강조 · 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다름(빠짐없이 강조) · 원 "지도" 슬라이드의 미니 지도 범례 계승 | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 D «프로그램의 일생»의 09만 ORANGE 강조(파트 D 첫 회차) · 완료(TEAL) 01–08 · 오늘(ORANGE) 09 · 이후(MUTED) 10–15 · 오늘 한 줄 문구와 08→09·09→10 연결 문구는 §3 명세 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | fs/ 계층의 fs/exec.c와 include/a.out.h를 진한 TEAL로 강조 · 오늘의 데이터 흐름 화살표(ORANGE): execve → do_execve → 파일 읽기(namei·헤더 bread) → copy_strings → change_ldt·brk 설정 → IP/SP 설정(eip[0]·eip[3]) → ret 0이면 main()부터 · 보조 화살표: iret 뒤 첫 fetch #PF → do_no_page(mm/memory.c) 적재 · 누적 강조(옅은 TEAL) 01–08 영역은 §3 명세 | fs/exec.c(§1 읽기 범위) · include/a.out.h:6-15 · kernel/system_call.s:200-205 · mm/memory.c:365-397 | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 셸이 명령을 실행하는 두 호출 | 배경 | `fork()` 뒤 자식이 `execve(path, argv, envp)` — 셸의 기본 패턴 · 06회차 fork 그림에 exec 상자 추가 · "fork는 몸을 복제, exec는 몸 안의 프로그램을 교체" · 1회차에서 본 `init → fork → execve("/bin/sh")`(main.c:179-184)가 오늘의 입구 | init/main.c:162-165, 179-184, 190-200 | 06회차 fork 그림 + exec 상자(ORANGE) 추가 |
| 06 | 코드: 사용자 쪽 — lib/execve.c 10줄 | 배경 | `lib/execve.c:7-10` 전체 + `unistd.h:172-184` 매크로 전개: eax=11(`__NR_execve`, unistd.h:71), ebx=file, ecx=argv, edx=envp, `int $0x80`, 음수면 `errno=-res; return -1` · 4회차 write()와 같은 틀임을 확인 | lib/execve.c:7-10 · include/unistd.h:71, 172-184 · include/linux/sys.h:12, 74-76 | 코드 인용(`_syscall3` 전개 주석) |
| 07 | 커널 스택 프레임과 eip 포인터 | 배경 | `system_call.s:35-46` 오프셋 표: EIP=0x1C, CS=0x20, EFLAGS=0x24, OLDESP=0x28 · `system_call.s:80-93` 진입부 복습: 인자 push, ds/es=0x10, fs=0x17, `call _sys_call_table(,%eax,4)` · 그림: 커널 스택 프레임에서 `eip[0]`=EIP, `eip[1]`=CS, `eip[2]`=EFLAGS, `eip[3]`=OLDESP · 오늘의 마지막 두 줄(344-345)이 여기 쓴다고 예고 | kernel/system_call.s:35-46, 80-93 | 커널 스택 프레임 그림(§4 — 04회차 프레임 그림 재사용) |
| 08 | 코드: _sys_execve — 저장된 EIP의 주소를 넘긴다 | 배경 | `system_call.s:200-205`: `lea EIP(%esp),%eax; pushl %eax; call _do_execve` · 저장된 EIP의 **주소**를 첫 인자로 넘김 — do_execve가 커널 스택 프레임을 직접 덮어쓸 수 있는 이유 · 값이 아니라 주소라는 점을 크게 강조 | kernel/system_call.s:200-205 · kernel/system_call.s:35-46(참조) | 코드 인용(`lea EIP(%esp),%eax` 하이라이트) |
| 09 | a.out 파일은 어떻게 생겼나 | 배경 | 그림: [헤더 32B][패딩 → 1024B][텍스트 a_text][데이터 a_data][심볼…] · 메모리 배치: 텍스트 0부터, 데이터 그 뒤, bss a_bss, 스택은 64MB 끝에서 아래로 · `a_entry`(보통 0) · ZMAGIC = "텍스트가 1KB 경계에서 시작해 블록 단위로 읽기 좋음" | include/a.out.h:6-15, 30-34, 42-45, 92-93 | a.out 파일 레이아웃 그림(§4) |
| 10 | 0.11 사용자 주소 공간 한 장 | 배경 | 논리 0 ~ 64MB: [텍스트][데이터][bss][brk→힙 ↑] … [↓스택][인자·환경 페이지 ≤32장]64MB · `end_code`, `end_data`, `brk`, `start_stack`이 각각 어디를 가리키는지 · 07회차 64MB 칸과 동일 그림 | fs/exec.c:334-346 · fs/exec.c:39 | 64MB 주소 공간 그림(§4 — 07회차 그림 재사용 + 인자 페이지 추가) |
| 11 | 오늘 읽을 함수 지도 | 배경 | execve(라이브러리) → _system_call → _sys_execve → do_execve → {namei, bread, copy_strings, free_page_tables, change_ldt→put_page, create_tables} → iret → #PF → do_no_page · 호출 순서도(상태도와 구분) · 오늘 첫 등장 함수 위치 표시 | fs/exec.c(§1 읽기 범위) · kernel/system_call.s:200-205 · mm/memory.c:365-397 | 함수 호출 그래프 도형(§4) |
| 12 | 코드: struct exec와 매직 | 코드 | `a.out.h:6-15`, `21-28`: 필드 설명(a_magic, a_text, a_data, a_bss, a_syms, a_entry, a_trsize, a_drsize), `0413` 8진수 = 0x10B · `N_TXTOFF`(42-45): ZMAGIC이면 `_N_HDROFF+32` = `SEGMENT_SIZE`(92-93, 1024) → `BLOCK_SIZE`와 같아야 함(exec.c:305) | include/a.out.h:6-15, 21-28, 40, 42-45, 92-93 · include/linux/fs.h:49 · fs/exec.c:305 | 코드 인용 + 필드→역할 주석 |
| 13 | 코드: do_execve 진입 | 코드 | `fs/exec.c:182-203`: 인자 `eip`(커널 스택 포인터), `tmp`, filename/argv/envp(사용자 포인터, fs로 읽음) · `(0xffff & eip[1]) != 0x000f` → 커널 모드 호출 panic(1회차 move_to_user_mode 뒤 CS=0x0f와 연결) · `p = 128KB-4` · `namei`(12회차 예고) → ENOENT · `count`로 argc/envc | fs/exec.c:182-203 · fs/exec.c:75-85 | 코드 인용(eip 인자·panic 조건 하이라이트) |
| 14 | 코드: 권한 검사와 setuid | 코드 | `fs/exec.c:204-220`: `S_ISREG` 아니면 EACCES · `e_uid/e_gid`(S_ISUID/S_ISGID면 파일 소유자) · `i>>=6`/`>>=3`로 소유자/그룹/기타 비트 선택, 실행 비트 없고 (어떤 x비트도 없거나 non-suser)면 **ENOEXEC**(EACCES가 아님에 주목) | fs/exec.c:204-220 · include/errno.h:27, 31, 32 | 코드 인용(비트 선택식 하이라이트) |
| 15 | 코드: 헤더 읽기 — bread와 첫 블록 | 코드 | `fs/exec.c:221-225`: 첫 블록 `bread(i_dev, i_zone[0])` → `ex` 복사 · a.out 파일은 항상 1블록(1024B)째에 헤더(ZMAGIC 배치) · 읽기 실패 시 EACCES(비교 ② 32장에서 총정리) | fs/exec.c:221-225 · include/linux/fs.h:49 | 코드 인용 + 09장 a.out 그림의 헤더 칸 참조 |
| 16 | 코드: 형식 검사 — ZMAGIC·재배치·크기·N_TXTOFF | 코드 | `fs/exec.c:298-309`: ZMAGIC 아님 / 재배치 정보 있음 / text+data+bss > 48MB / 파일 크기 부족 → ENOEXEC · `N_TXTOFF != BLOCK_SIZE` → printk 후 ENOEXEC · "0.11이 받아들이는 실행 파일은 ZMAGIC 하나"를 못 박음 | fs/exec.c:298-309 · include/a.out.h:30-34, 42-45 · include/linux/fs.h:49 | 코드 인용(4가지 거부 조건 색 구분) |
| 17 | 코드: #! 스크립트 (1/2) — 파싱 | 코드 | `fs/exec.c:226-256`: `b_data[0..1]=="#!"`이고 `!sh_bang`일 때만 · 버퍼 1022바이트, 첫 줄, 공백 건너뜀, 인터프리터 경로·이름(`/` 뒤)·선택 인자 분리 · 빈 줄이면 ENOEXEC | fs/exec.c:226-256 | 코드 인용 + 스크립트 첫 줄 예시 |
| 18 | 코드: #! 스크립트 (2/2) — argv 재구성과 재시작 | 코드 | `fs/exec.c:257-297`: 처음 한 번만 envp/argv[1..] 복사(261-264), 그 위에 스크립트 파일명(from_kmem=1), 인터프리터 인자·이름(from_kmem=2)을 **역순**으로 얹어 argv = [interp, i_arg, script, 원래 argv[1..]] · `set_fs(get_ds())` 후 `namei(interp)`, `goto restart_interp` · sh_bang=1이라 두 번째 #!은 처리하지 않음(중첩 불가) | fs/exec.c:257-297 · fs/exec.c:226(sh_bang 조건) | 코드 인용 + argv 재구성 스택 미니 그림 |
| 19 | 코드: copy_strings — 거꾸로 채우는 128KB | 코드 | `fs/exec.c:104-152`: argc부터 역순, 각 문자열 길이 세고(`len`), `p`를 줄이며 `page[p/PAGE_SIZE]`가 없으면 `get_free_page`, 바이트 단위 `get_fs_byte` · from_kmem에 따른 `set_fs` 토글 · 반환값 p = 남은 공간 오프셋 · 그림: page[31] 꼭대기에서 왼쪽으로 자라는 문자열 | fs/exec.c:104-152 · fs/exec.c:39 | 코드 인용 + page[] 채우기 그림(§4) |
| 20 | 코드: 돌이킬 수 없는 지점 | 코드 | `fs/exec.c:318-327`: 주석 "point of no return" · `iput(구 executable)`, `executable = inode` · 32개 `sa_handler = NULL`(시그널 핸들러는 구 프로그램의 주소이므로) · `close_on_exec` 비트가 켜진 fd `sys_close` · 이 뒤로는 오류 반환 없음 | fs/exec.c:318-327 | 코드 인용(318행 주석 원문 강조) |
| 21 | 코드: 주소 공간 비우기 | 코드 | `fs/exec.c:328-332`: `free_page_tables(get_base(ldt[1]), get_limit(0x0f))`, 데이터도 동일 — 07회차 함수가 모든 PTE·페이지·테이블을 반납(공유 페이지는 count만 감소) · `last_task_used_math` 정리 · `do_exit`(exit.c:106-107)와 같은 두 줄임을 대비 | fs/exec.c:328-332 · mm/memory.c:105-131 · kernel/exit.c:102-107, 122-123 | 코드 인용(두 줄 박스 — 10회차 do_exit 대비 표시) |
| 22 | 코드: change_ldt (1/2) — 리밋만 바꾸고 베이스는 그대로 | 코드 | `fs/exec.c:154-177` 전반: `code_limit = (a_text+4095)&~4095`, `data_limit = 0x4000000` · `code_base = get_base(ldt[1])`(fork 때 nr×64MB, fork.c:52-55)를 **그대로** 다시 set_base, `set_limit`×2 · "베이스 불변·리밋만 교체"가 오늘의 대명제 | fs/exec.c:154-177(전반) · kernel/fork.c:52-55 | 코드 인용(베이스·리밋 계산식 하이라이트) |
| 23 | 코드: change_ldt (2/2) — 인자 페이지를 64MB 끝에 매핑 | 코드 | `fs/exec.c:154-177` 후반: `pushl $0x17; pop %fs`(새 리밋 반영) · 인자 페이지를 `data_base + 64MB - 4KB×k`에 `put_page`(page[i]가 있는 것만) · 반환 data_limit · 물리 페이지 이동 없이 PTE만 새로 놓는다는 점(상태도 ② 30장 연결) | fs/exec.c:154-177(후반) · fs/exec.c:104-152(page[]) | 코드 인용 + 64MB 끝 매핑 미니 그림 |
| 24 | 코드: create_tables — 새 스택 꼭대기 | 코드 | `fs/exec.c:46-70` + `333-334`: `p += 64MB - 128KB` 로 p를 새 논리 주소로 환산 · 4바이트 정렬, envp 배열(envc+1), argv 배열(argc+1), `envp, argv, argc` 순으로 push(56-58) · 문자열을 훑며 포인터 채움 · 그림: 스택 꼭대기 레이아웃 [argc][argv][envp][argv[0..]][NULL][envp[0..]][NULL][문자열…]64MB | fs/exec.c:46-70, 333-334 | 코드 인용 + 스택 레이아웃 그림(§4) |
| 25 | 코드: 태스크 필드 갱신 | 코드 | `fs/exec.c:335-343` 전반: `end_code=a_text`, `end_data=a_text+a_data`, `brk=+a_bss`, `start_stack=p&~0xfff`, `euid/egid` · 10장 주소 공간 그림의 네 포인터가 여기서 정해짐 | fs/exec.c:335-343(전반) · fs/exec.c:334-346 | 코드 인용 + 10장 그림 포인터 재지시 |
| 26 | 코드: 꼬리 0 채움 — 첫 do_no_page를 일으키는 쓰기 | 코드 | `fs/exec.c:341-343`: `a_text+a_data`부터 페이지 끝까지 `put_fs_byte(0,…)` · 이 쓰기가 **첫 do_no_page**(디스크 갈래, 08회차 380-396)를 일으켜 마지막 데이터 페이지가 적재되고 bss 앞부분이 0이 됨 · "exec가 코드를 읽지 않는다"의 첫 증거 | fs/exec.c:341-343 · mm/memory.c:365-397 | 코드 인용 + 08회차 do_no_page 그림 참조 |
| 27 | 코드: 마법의 두 줄 — eip[0], eip[3] | 코드 | `fs/exec.c:344-346`: `eip[0] = ex.a_entry`(커널 스택의 저장된 EIP), `eip[3] = p`(저장된 ESP) · `return 0` → `_sys_execve`의 `ret` → `ret_from_sys_call` → `iret`가 **새 EIP/ESP**로 복귀 · CS/SS는 0x0f/0x17 그대로지만 LDT 리밋이 달라짐 · 그림: 프레임의 두 칸이 덮어써진 모습 | fs/exec.c:344-346 · kernel/system_call.s:35-46, 200-205 | 코드 인용 + 프레임 덮어쓰기 그림(§4) |
| 28 | 코드: 첫 명령은 아직 메모리에 없다 | 코드 | iret 후 CS:EIP=0x0f:a_entry fetch → PTE 부재 → #PF(U=1,P=0) → `do_no_page`(memory.c:365-397): `tmp=0 < end_data`, `share_page`(같은 /bin/sh가 떠 있으면 공유!), 아니면 `bmap`×4+`bread_page` · 08회차 시연 B와 동일 장면 | mm/memory.c:365-397 · fs/exec.c:221-225(헤더만 읽음) | 코드 인용 + 요구 적재 타임라인 |
| 29 | 상태 변화도 ①: 태스크의 프로그램 상태 | 상태도 | 상태 5개: 구 프로그램 실행 / 검사 중(복귀 가능) / 주소 공간 비움(318~333) / 새 프레임 준비(334~346) / 새 프로그램 첫 폴트 · 각 전환의 원인(줄)과 변경 데이터 vs 유지 데이터 표(pid·father·pwd·root·uid·LDT 베이스·열린 fd(비 close-on-exec)는 유지) · 호출 순서도 아님을 명시 | fs/exec.c:318-346 · kernel/fork.c:52-55 | 상태 변화도 ①(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 30 | 상태 변화도 ②: 인자 문자열의 네 위치 | 상태도 | (1) 구 사용자 공간 → (2) 커널 물리 페이지 page[] 꼭대기(copy_strings) → (3) 새 공간 64MB 끝에 매핑(change_ldt put_page, 물리 페이지 이동 없음) → (4) 그 아래 포인터 배열과 argc(create_tables) · 변경 데이터: page[32], PTE 32개, 새 스택 메모리 · 유지 조건: 문자열은 한 번만 복사됨 | fs/exec.c:104-152, 154-177, 46-70, 333-334 | 상태 변화도 ②(§4 상세 명세) |
| 31 | 비교 ①: 실행 파일 형식 — 받아들이는 것과 거부하는 것 | 비교 | 범위: a.out 매직 3가지 + #! + 기타 · 열: 매직 값, 메모리 배치 특성, 0.11 처리(ZMAGIC만 허용: 299행 / OMAGIC·NMAGIC: ENOEXEC / #!: 1회 재시작 226-297 / 기타: ENOEXEC), 이유(요구 적재는 블록 정렬된 텍스트가 필요) · ELF는 1991년에 없음(현대 비교 한 줄) | include/a.out.h:21-28 · fs/exec.c:298-309(299행), 226-297 | 실행 파일 형식 비교표(§4) |
| 32 | 비교 ②: 오류 반환 경로 전부 | 비교 | ENOENT(199-200 파일 없음, 290-293 인터프리터 없음) / EACCES(205-208 정규 파일 아님, 221-224 첫 블록 읽기 실패) / ENOEXEC(216-220 실행 권한 없음, 243-246 #! 빈 줄, 299-304 형식, 305-309 TXTOFF) / ENOMEM(281-284, 313-316 copy_strings 0) · 모두 318 이전 → 구 프로그램으로 복귀, 라이브러리가 errno 설정 · **E2BIG**: errno.h:26에 정의만 있고 exec.c는 쓰지 않음(인자 초과는 128KB 페이지 부족 → ENOMEM 경로) | fs/exec.c:199-220, 221-225, 243-246, 281-284, 290-293, 298-316 · include/errno.h:21, 26, 27, 31, 32 | 오류 경로 비교표(조건·줄·되돌림 가능 여부 열) |
| 33 | 비교 ③: copy_strings의 from_kmem 0/1/2 | 비교 | 범위: 3가지 전부 · 문자열 위치 / 포인터 배열 위치 / fs 조작 시점(115-116, 118-123, 136-143) / 호출처(0: 262-263·311-312 사용자 argv, 1: 273 커널에 있는 `&filename` 배열+사용자 문자열, 2: 276·279 인터프리터 이름·인자 모두 커널 buf) | fs/exec.c:104-152 · fs/exec.c:262-263, 273, 276, 279, 311-312 | from_kmem 3분지 비교표 |
| 34 | 시연 준비 | 시연 | lab 심볼: `do_execve`, `sys_execve`, `change_ldt`(static이지만 -g로 보임), `current` · 줄 번호는 lab 소스 기준이므로 `list do_execve`로 확인 후 중단점 · 사용자 문자열은 `x/s (char*)current->start_code + (long)filename`으로 읽는다(fs 세그먼트 보정) | —(시연 전략) | GDB 명령 블록 |
| 35 | 시연 A-1: do_execve 진입 시점 | 시연 | `b do_execve`, 셸에 `ls` 입력 → 정지 · `p current->pid`(자식 pid), `x/s (char*)current->start_code+(long)filename`(기대 "/bin/ls" 또는 "/usr/bin/ls") · `p/x current->ldt[1]`, `p/x current->ldt[2]`, `p/x current->ldt[1].a & 0xffff`(코드 리밋, 페이지 단위: 셸의 텍스트 크기) · `p current->executable->i_num`(셸 inode), `p/x eip[0]`, `p/x eip[3]`(셸의 복귀 EIP/ESP) | fs/exec.c:182-203(관찰 대상) | GDB 명령 블록 · 캡처 01(§5) |
| 36 | 캡처 A-1: 진입 시점 값 | 캡처 | GDB 캡처 게시 · 각주: QEMU i386 TCG, lab 빌드, 수정 없음 · 옆에 "바뀔 값 / 그대로일 값" 체크리스트(ldt 리밋·executable·eip[0]·eip[3] = 바뀜, pid·베이스 = 그대로) | fs/exec.c:182-203(관찰 대상) | materials/09-exec/captures/01-do-execve-entry.png(§5) |
| 37 | 시연 A-2: 마법의 두 줄 전후 | 시연 | `b exec.c:<eip[0]= 줄>`(src 344에 해당, lab에서 `list`로 확인), `c` · 정지 시 `p/x ex`(a_magic=0x10b, a_text, a_data, a_bss, a_entry), `p/x current->ldt[1].a & 0xffff`(새 코드 리밋 = (a_text+4095)>>12), `p/x current->ldt[2].a & 0xffff`(0x4000 = 64MB/4KB) · `p current->executable->i_num`(바뀜), `p current->pid`(그대로), `p/x eip[0]`(아직 셸 값) → `next` 2회 → `p/x eip[0]`(= a_entry), `p/x eip[3]`(64MB 바로 아래, 예 0x3ffffxx) | fs/exec.c:344-346, 154-177, 318-343(관찰 대상) | GDB 명령 블록 · 캡처 02·03(§5) |
| 38 | 캡처 A-2: eip[0]/eip[3] 전후 | 캡처 | 전/후 캡처 2장 게시 · 상태도 ①의 "새 프레임 준비" 행 표시 · `x/4wx eip[3] + current->start_code`로 [argc][argv][envp] 확인(선형 주소 보정) — 캡처 포함 | fs/exec.c:344-346 · fs/exec.c:46-70(관찰 대상) | 02-eip-before.png · 03-eip-after.png(§5) |
| 39 | 시연 B: iret 뒤 첫 폴트 | 시연 | `b do_no_page` 추가 후 `c` · 정지 시 `p/x address - current->start_code` → 기대: 341-343 꼬리 0 채움이 먼저면 `end_data` 페이지, 아니면 0(엔트리) · `bt` · `finish` 후 `x/8xb current->start_code`에 새 프로그램 코드 · 그 다음 `c` → 사용자 모드에서 첫 명령 실행 중 `Ctrl-C`, `p/x $eip`(작은 값), `p/x $cs`(0xf) | mm/memory.c:365-397 · fs/exec.c:341-343(관찰 대상) | GDB 명령 블록 · 캡처 04·05(§5) |
| 40 | 캡처 B: 같은 pid, 다른 코드 | 캡처 | A-1의 pid와 같은 pid에서 `x/8xb`가 다른 바이트(셸 vs ls)임을 나란히 게시 · 각주: 공유 중이면 share_page로 적재되어 디스크 읽기 없이 PTE 5일 수 있음(관찰과 추론 구분) | mm/memory.c:365-397(관찰 대상) | 04-do-no-page-first-fault.png · 05-same-pid-new-code.png(§5) |
| 41 | 시연 C(선택): #! 스크립트의 재시작 | 시연 | 게스트에서 `echo '#!/bin/sh' > /tmp/t.sh; echo 'echo hi' >> /tmp/t.sh; chmod +x /tmp/t.sh` · `b exec.c:<S_ISREG 검사 줄>`(src 205) · `/tmp/t.sh` 실행 → 같은 do_execve 호출 안에서 중단점 2회: 두 번째에 `p sh_bang`=1, `p argc`(+1 이상), `x/s`로 inode가 /bin/sh임을 확인(`p inode->i_num`) · 실패 시 사전 캡처 | fs/exec.c:204-220, 226-297(관찰 대상) | GDB 명령 블록 · 캡처 06(§5) |
| 42 | 질문의 답 (1): PID가 그대로인 이유 | 정답 | exec는 `task[nr]` 구조체를 만들지도 지우지도 않는다 · 바뀌는 것은 그 구조체 안의 `executable`, `ldt` 리밋, `end_code/end_data/brk/start_stack`, `sigaction`, 일부 fd, 그리고 **커널 스택에 저장된 EIP/ESP** · pid·father·pwd·root·uid는 손대지 않음(318-346에 없음) | fs/exec.c:318-346 | 요점 강조 박스(변경/유지 2열) |
| 43 | 질문의 답 (2): 프로그램이 바뀌는 실제 순간 | 정답 | `free_page_tables`로 구 페이지가 사라지고(07), `eip[0]=a_entry`로 복귀 지점이 바뀌고(iret), 첫 fetch의 #PF를 `do_no_page`가 새 inode에서 채운다(08) · 세 회차가 한 줄로 이어지는 그림 · 현대 커널: ELF 로더 + mmap이지만 "폴트로 적재"는 같다 한 줄 | fs/exec.c:328-332, 344-346 · mm/memory.c:365-397 | 세 회차 연결 그림(§4) |
| 44 | 오늘 코드가 쓰는 데이터 요약 | 정리 | `struct exec ex`, `page[32]`, `p`, `eip[]`, `current->{executable, ldt, end_code, end_data, brk, start_stack, sigaction, close_on_exec, euid, egid}` · 함수×데이터 교차표 | fs/exec.c(§1 읽기 범위) · include/a.out.h:6-15 | 함수×데이터 교차표 |
| 45 | 이해 확인 질문 | 확인 | 4문항 질문만 게시(§6 원문 그대로) · eip 첫 인자와 eip[3] / LDT 베이스 불변과 바뀌는 것 / exec 뒤 코드를 언제 누가 읽는가 / 실행 권한 없음·디렉터리의 errno | (§6 질문 원문) | 문항 4개 텍스트 |
| 46 | 이해 확인 정답 | 확인 | 정답과 근거 줄 번호(§6 원문 그대로) · 1번: `lea EIP(%esp)` 커널 스택 저장 EIP 위치(system_call.s:201-202), eip[1]=CS·eip[2]=EFLAGS·eip[3]=OLDESP(35-46), 344-345가 덮어씀 · 2번: 베이스(nr×64MB)는 fork.c:52-55 고정, change_ldt(exec.c:162-167)는 리밋만 · 3번: 헤더 1블록만 bread(221-225), 첫 폴트를 do_no_page(memory.c:365-397)가 블록 4개 읽기 · 4번: 실행 비트 없음 → ENOEXEC(216-219, EACCES가 아님), 디렉터리 → EACCES(205-207) | (§6 정답 원문) | 정답 4개 텍스트 |
| 47 | 정리·다음 회차 예고 | 정리 | fork(06)·주소(07)·COW(08)·exec(09) 묶음 완료 · 10회차 "자식이 죽으면 부모는 어떻게 아는가? Ctrl-C는 어디까지 가는가?" — 오늘 본 `do_exit`의 같은 두 줄(exit.c:106-107)과 `sigaction` 초기화가 왜 필요했는지로 연결 · 미리 볼 파일: kernel/exit.c, kernel/signal.c | kernel/exit.c:102-107, 122-123 | 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: D «프로그램의 일생» · 09/15 — 파트 D의 첫 회차(09 exec → 10 종료·시그널). 완료(TEAL) 01–08, 오늘(ORANGE + 굵은 테두리) 09, 이후(MUTED) 10–15.
- 오늘 한 줄 문구: "같은 몸(pid·태스크 구조체), 다른 프로그램 — execve"
- 08→오늘 연결 화살표 문구: "08: fork 뒤 자식의 첫 쓰기 폴트를 봤다 → 09: fork로 만든 자식이 exec로 새 프로그램을 불러오면 — PID는 그대로인데 프로그램은 어떻게 바뀌는가?"
- 오늘→10 연결 화살표 문구: "09: exec로 새 프로그램이 첫 명령부터 실행됐다 → 10: 실행한 프로그램이 끝나면 — exit·wait·시그널"
- 원 "지도" 슬라이드(원 02) 내용 계승: "06 fork → 07 주소 변환 → 08 COW → 09 exec → 10 종료" 순서 라벨을 완료 상자 06·07·08과 이후 상자 10의 연결 라벨로 살리고, "1회차에서 본 `init → fork → execve("/bin/sh")`(main.c:179-184)가 오늘의 입구" 문구를 오늘 상자 보조 라벨로 계승. 미니 지도 범례는 슬라이드 02 오늘의 길에서 계승.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL): fs/ 계층의 fs/exec.c(do_execve·copy_strings·change_ldt·create_tables). include/a.out.h(struct exec·ZMAGIC·N_TXTOFF)는 fs/exec.c 상자 옆 라벨로 표시한다.
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): execve(사용자, lib/execve.c) → int 0x80 → _sys_execve(kernel/system_call.s) → do_execve(fs/exec.c) → 파일 읽기(namei·헤더 bread) → copy_strings → change_ldt·brk 설정 → IP/SP 설정(eip[0]=a_entry·eip[3]=p) → ret 0이면 main()부터(iret).
- 보조 화살표(ORANGE, 2번째 — 00-common §2가 허용하는 1–2개 안): iret 뒤 첫 명령 fetch #PF → do_no_page(mm/memory.c)가 `current->executable` inode에서 코드 페이지 적재(08회차 연계).
- 누적 강조(옅은 TEAL, 01–08): 파트 A — boot/bootsect.s·boot/setup.s·boot/head.s·init/main.c(01–03, init/main.c는 오늘 execve 호출처로도 등장) / 파트 B — kernel/system_call.s·kernel/asm.s·kernel/traps.c(04, system_call.s는 오늘 주 화살표의 경유점), include/linux/sched.h·kernel/sched.c(05), kernel/fork.c(06, fork.c:52-55이 베이스 불변의 근거) / 파트 C — mm/memory.c·boot/head.s(07), mm/page.s·mm/memory.c(08, do_no_page는 오늘 보조 화살표의 종점).

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(09 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 09 ORANGE, 01–08 TEAL, 10–15 MUTED, 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(fs/exec.c 강조) | 도형 다이어그램 | §3 명세 그대로 — fs/exec.c·include/a.out.h 강조 + 데이터 흐름 화살표 2 | 전 회차 공통 골격 + 08 누적 영역 |
| 07 | 커널 스택 프레임과 eip[0..3] | 도형 | 프레임 상자에서 EIP(0x1C)·CS(0x20)·EFLAGS(0x24)·OLDESP(0x28) 네 칸 강조, 각 칸에 eip[0..3] 인덱스 라벨, 344-345가 덮어쓸 두 칸 점선 예고 | 04회차 시스템 콜 프레임 그림 |
| 09 | a.out 파일 레이아웃 | 도형 | [헤더 32B][패딩 → 1024B][텍스트 a_text][데이터 a_data][심볼…] 세로 매핑, 아래에 메모리 배치(텍스트 0부터·데이터 그 뒤·bss a_bss·스택 64MB 끝) 대응선 | — |
| 10 | 0.11 사용자 주소 공간 64MB | 도형 | [텍스트][데이터][bss][brk→힙 ↑] … [↓스택][인자·환경 페이지 ≤32장]64MB · end_code/end_data/brk/start_stack 포인터 화살표 | 07회차 64MB 칸 그림 |
| 11 | 오늘의 함수 호출 그래프 | 도형 | execve → _system_call → _sys_execve → do_execve → {namei, bread, copy_strings, free_page_tables, change_ldt→put_page, create_tables} → iret → #PF → do_no_page · 상태도 아님을 명시 | 08회차 함수 그래프 양식 |
| 19 | copy_strings page[] 채우기 | 도형 | page[31] 꼭대기에서 왼쪽(아래 번지)으로 자라는 문자열들, p 감소 방향 화살표, page[p/PAGE_SIZE] 없으면 get_free_page 표시 | — |
| 24 | create_tables 스택 꼭대기 레이아웃 | 도형 | 64MB 끝에서 아래로 [argc][argv][envp][argv[0..]][NULL][envp[0..]][NULL][문자열…] — 10장 64MB 그림의 스택 영역 확대 | 10장(동일 시각 언어) |
| 27 | 프레임 두 칸 덮어쓰기 | 도형 | 07장 프레임 그림에서 eip[0](=ex.a_entry)·eip[3](=p) 두 칸만 ORANGE로 덮어쓴 모습, iret 복귀 화살표 | 07장 그림 축약 재활용 |
| 29 | 상태 변화도 ① (핵심) | 도형 상태 다이어그램 | 상태 5개(구 프로그램 실행 / 검사 중(복귀 가능) / 주소 공간 비움 318~333 / 새 프레임 준비 334~346 / 새 프로그램 첫 폴트) + 전환 원인 줄 번호 라벨 + 변경/유지 데이터 하단 표 | — |
| 30 | 상태 변화도 ② (핵심) | 도형 + 표 | 인자 문자열의 네 위치: (1) 구 사용자 공간 → (2) page[] 꼭대기(copy_strings) → (3) 64MB 끝 매핑(change_ldt put_page, 물리 페이지 이동 없음) → (4) 포인터 배열·argc(create_tables) → eip[3]=p | — |
| 31 | 실행 파일 형식 비교표 | 표 | 열: 매직 값 / 메모리 배치 특성 / 0.11 처리 / 이유 — ZMAGIC(0413)·OMAGIC(0407)·NMAGIC(0410)·#!·기타 5행 | — |
| 43 | 세 회차 연결 그림 | 도형 | 07 free_page_tables(구 페이지 반납) → 09 eip[0]=a_entry(iret 복귀 지점 교체) → 08 do_no_page(새 inode에서 적재) 한 줄 타임라인 | 07·08회차 도식 언어 |

핵심 시각자료 상세 명세 — 상태 변화도 ① (슬라이드 29·42가 같은 시각 언어를 공유):

- 공통 시각 언어: 상태는 둥근 상자, 전환은 화살표 + 원인(줄 번호) 라벨. 구 프로그램 관련 MUTED, 오늘의 전환(execve 진입 이후) ORANGE, 새 프로그램·유지 데이터 TEAL. 우하단 `Linux 0.11` 라벨.
- 슬라이드 29 (상태 5 + 전환 4): `구(舊) 프로그램 실행 중` → (execve 진입, 검사 통과 전: 실패 시 원상 복귀 가능) `검사 중` → (318 이후) `주소 공간 비움: executable=새 inode, 페이지 테이블 0, LDT 리밋 새 값, 인자 페이지 32장만 매핑` → (iret) `새 프로그램 첫 명령 fetch` → (do_no_page) `코드 페이지 적재됨`. 하단 표 두 열: 변경되는 데이터(`executable`, `ldt[1..2]` 리밋, `pg_dir[16nr..]`, `brk/end_code/end_data/start_stack`, `sigaction`, `filp`(close_on_exec), `euid/egid`, 커널 스택의 EIP/ESP) vs 유지되는 데이터(`pid`, `father`, `pwd/root`, `uid/gid`, `ldt` 베이스, `tss`의 나머지, 나머지 fd).
- 캡처 슬라이드 36·38이 "검사 중 → 주소 공간 비움" 전후를, 39·40이 "새 프로그램 첫 폴트" 상태를 재지시한다.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/09-exec/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A-1 | 01-do-execve-entry.png | `b do_execve` · 셸 `ls` · `p current->pid` · `x/s (char*)current->start_code+(long)filename` · `p/x current->ldt[1].a & 0xffff` · `p current->executable->i_num` · `p/x eip[0]` · `p/x eip[3]` | 진입 시점: 자식 pid, "/bin/ls"류 경로, 셸 텍스트 페이지 수 리밋, 셸 inode, 셸의 복귀 EIP/ESP | 사전 캡처 3장 중 "진입"(각주 "lab 빌드, 수정 없음, 값은 부팅마다 다름") |
| A-2 전 | 02-eip-before.png | `b exec.c:<eip[0]= 줄>`(src 344 상당, `list`로 확인) · `c` · `p/x ex` · `p/x current->ldt[1].a & 0xffff` · `p/x current->ldt[2].a & 0xffff` · `p current->executable->i_num` · `p current->pid` · `p/x eip[0]` | `a_magic=0x10b`(0413)·a_text·a_data·a_bss·a_entry, 새 코드 리밋=(a_text+4095)>>12, 데이터 리밋 0x4000, 새 inode, pid 불변, eip[0] 아직 셸 값 | 사전 캡처 "344 직전" |
| A-2 후 | 03-eip-after.png | `next` 2회 · `p/x eip[0]` · `p/x eip[3]` · `x/4wx (long)eip[3] + current->start_code` | eip[0]=a_entry, eip[3]=0x3ffffxx 근처, [argc][argv][envp] 배열 | 사전 캡처 "next 후" |
| B | 04-do-no-page-first-fault.png | `b do_no_page` · `c` · `p/x address - current->start_code` · `p error_code` · `bt` | 첫 폴트 주소(0=엔트리 또는 end_data 페이지), backtrace `do_no_page ← page_fault`, (341-343 쓰기라면 U=0 에러 코드 — 커널 부재 케이스) | 사전 캡처 2장 중 첫 폴트 |
| B | 05-same-pid-new-code.png | `finish` 후 `x/8xb current->start_code` · `c` → 사용자 모드 첫 명령 중 `Ctrl-C` · `p/x $eip` · `p/x $cs` | A-1 pid와 같은 pid에서 다른 코드 바이트(셸 vs ls), 작은 값 $eip, $cs=0xf, (공유 중이면 PTE 하위 5 — 관찰과 추론 구분) | 사전 캡처 2장 중 코드 확인 |
| C(선택) | 06-shebang-restart.png | 게스트 `/tmp/t.sh` 생성(`#!/bin/sh`, `echo hi`)·`chmod +x` · `b exec.c:<S_ISREG 줄>`(src 205 상당) · 실행 → 2회 정지 · `p sh_bang` · `p argc` · `p inode->i_num` | 2회째 sh_bang=1, argc 증가, inode=/bin/sh, `hi` 출력 | 사전 캡처 1장 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜`(00-common §7). inode 번호·주소·리밋 값은 lab 디스크 이미지에 따라 다르다.

## 6. 이해 확인 질문과 정답

질문은 슬라이드 45, 정답은 슬라이드 46에 게시(원문 계승).

1. **Q.** `do_execve`의 첫 인자 `eip`는 무엇을 가리키며, `eip[3]`은 무엇인가?
   **A.** `_sys_execve`가 `lea EIP(%esp)`로 넘긴 커널 스택의 저장된 EIP 위치(system_call.s:201-202). 프레임 오프셋(35-46)상 `eip[1]`=CS, `eip[2]`=EFLAGS, `eip[3]`=OLDESP(사용자 ESP). 344-345가 이 둘을 덮어쓴다.
2. **Q.** exec 뒤에도 LDT **베이스**가 그대로인 이유는? 바뀌는 것은 무엇인가?
   **A.** 베이스(nr×64MB)는 태스크 슬롯이 정하며 fork.c:52-55에서 고정. `change_ldt`(exec.c:162-167)는 같은 베이스를 다시 쓰고 리밋만 바꾼다(코드: 텍스트 페이지 올림, 데이터: 64MB).
3. **Q.** exec가 성공했는데도 `/bin/ls`의 코드가 아직 메모리에 없다. 언제, 누가 읽는가?
   **A.** `do_execve`는 헤더 1블록만 `bread`(221-225)한다. iret 뒤 첫 명령 fetch(또는 341-343의 꼬리 0 채움 쓰기)가 부재 폴트를 내고 `do_no_page`(memory.c:365-397)가 `executable` inode에서 블록 4개를 읽는다.
4. **Q.** 실행 권한이 없는 파일을 exec하면 0.11은 어떤 errno를 돌려주는가? 파일이 디렉터리라면?
   **A.** 실행 비트 없음 → ENOEXEC(exec.c:216-219, EACCES가 아님). 정규 파일이 아니면(디렉터리) → EACCES(205-207). 둘 다 318 이전이라 구 프로그램으로 돌아가고 라이브러리가 errno를 설정한다.

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| execve | 프로그램을 교체하는 시스템 콜(번호 11, `__NR_execve`) | 05 |
| `_syscall3` | 인자 3개 시스템 콜 래퍼 매크로(`int $0x80`, eax=번호, ebx/ecx/edx 인자, 음수면 errno) | 06 |
| `sys_execve` | `sys_call_table[]` 11번 어셈블리 스텁 — 저장된 EIP의 주소를 do_execve에 전달 | 08 |
| `do_execve` | fs/exec.c의 본체: 검사 → 인자 복사 → 주소 공간 교체 → EIP/ESP 덮어쓰기 | 08 |
| a.out | 0.11의 실행 파일 형식(include/a.out.h) | 09 |
| `struct exec` | a.out 헤더 구조: a_magic·a_text·a_data·a_bss·a_syms·a_entry·a_trsize·a_drsize | 12 |
| OMAGIC/NMAGIC/ZMAGIC | a.out 매직 0407·0410·0413 — 0.11은 ZMAGIC만 허용 | 12 |
| `N_TXTOFF` | 텍스트의 파일 내 시작 오프셋(ZMAGIC이면 SEGMENT_SIZE=1024) | 12 |
| `SEGMENT_SIZE` | a.out 세그먼트 정렬 크기(1024) — 텍스트는 파일 1024바이트부터 | 12 |
| `#!`(shebang) | 스크립트 첫 줄의 인터프리터 지정 — do_execve가 1회 재시작 | 17 |
| 인터프리터 | `#!`로 지정된 실제 실행 파일(예: /bin/sh) | 17 |
| `restart_interp` | `#!` 파싱 후 `namei(interp)`부터 다시 검사하는 goto 레이블 | 18 |
| `copy_strings` | 문자열을 page[] 꼭대기부터 거꾸로 복사하는 함수 | 19 |
| `from_kmem` | copy_strings의 인자 출처 구분 0/1/2(문자열·포인터 배열의 사용자/커널 공간 조합) | 18 |
| `MAX_ARG_PAGES` | 인자+환경 페이지 상한 32(=128KB) | 19 |
| `change_ldt` | 코드·데이터 리밋 재설정과 인자 페이지 매핑(베이스는 불변) | 22 |
| `create_tables` | 새 스택 꼭대기에 argc·argv·envp 배열을 구성 | 24 |
| 돌이킬 수 없는 지점(point of no return) | exec.c:318 — 이 뒤로는 오류 반환 없음 | 20 |
| `close_on_exec` | exec 시 자동으로 닫을 fd 표시 비트 | 20 |
| setuid/setgid(`S_ISUID/S_ISGID`) | 실행 파일 소유자의 euid/egid를 물려주는 비트 | 14 |
| `end_code`·`end_data`·`brk`·`start_stack` | 태스크의 코드·데이터·힙·스택 경계 필드 | 10 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- "exec가 새 프로세스를 만든다"고 말하지 않는다. `task[nr]`·pid는 그대로이며 내용물만 교체된다.
- "exec가 프로그램을 메모리에 읽어 들인다"고 말하지 않는다. 0.11의 exec는 헤더 1KB만 읽고, 코드·데이터는 폴트가 날 때 `do_no_page`가 읽는다.
- "exec가 LDT를 새로 만든다"고 말하지 않는다. 베이스는 그대로, 리밋만 바뀐다.
- 실행 권한 없음의 errno를 EACCES라고 말하지 않는다. 0.11은 ENOEXEC를 돌려준다(216-219). 현대 리눅스(EACCES)와 다르다.
- E2BIG를 0.11 exec의 오류로 소개하지 않는다. `errno.h:26`에 정의만 있다. 128행 `p-len<0`은 `p`가 unsigned라 실질적으로 걸리지 않으며 인자 초과는 페이지 할당 실패 → ENOMEM으로 나타난다(코드 추론, 실험 아님).
- `#!` 처리를 "재귀적으로 인터프리터를 찾는다"고 하지 않는다. `sh_bang` 때문에 한 번만 처리한다(226, 261).
- "ELF"를 0.11 맥락에서 쓰지 않는다. 비교 ① 말미의 한 줄 대비만.
- 시연 캡처의 inode 번호·주소·리밋 값은 lab 디스크 이미지에 따라 다르다. 각주에 환경과 수정 여부를 적는다. lab 줄 번호는 src와 다를 수 있으므로 슬라이드의 줄 번호는 src 기준임을 명시한다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 핵심 질문과 지도(로드맵·구조도로 오늘 위치 — 파트 D 개막) |
| 05–11 | 17 | 배경: 셸의 두 호출(fork+exec), 라이브러리 → 시스템 콜 → sys_execve, 커널 스택 프레임과 eip 포인터, a.out 파일 그림, 주소 공간, 함수 지도 |
| 12–19 | 24 | 코드: 헤더·매직, do_execve 진입과 검사, #! 처리, copy_strings |
| 20–28 | 22 | 코드: 돌이킬 수 없는 지점, free_page_tables, change_ldt, create_tables, eip/esp 덮어쓰기, 첫 폴트 |
| 29–33 | 15 | 상태 변화도 2장 + 비교 3장 |
| 34–41 | 25 | 강사 시연 A/B/C (do_execve 정지, LDT·eip 변화, #! 재시작) + 캡처 |
| 42–44 | 7 | 질문의 답 + 오늘 코드가 쓰는 데이터 요약 |
| 45–47 | 5 | 이해 확인·정리·예고 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞부분 5, 배경 17, 코드 24+22, 상태도·비교 15, 시연 25, 답 7, 마무리 5.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(41행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07+08(분할) · 원 06→09 · 원 07→10 · 원 08→11 · 원 09→12 · 원 10→13 · 원 11→14 · 원 12→15+16(분할) · 원 13→17 · 원 14→18 · 원 15→19 · 원 16→20 · 원 17→21 · 원 18→22+23(분할) · 원 19→24 · 원 20→25+26(분할) · 원 21→27 · 원 22→28 · 원 23→29 · 원 24→30 · 원 25→31 · 원 26→32 · 원 27→33 · 원 28→34 · 원 29→35 · 원 30→36 · 원 31→37 · 원 32→38 · 원 33→39 · 원 34→40 · 원 35→41 · 원 36→42 · 원 37→43 · 원 38→44 · 원 39→45 · 원 40→46 · 원 41→47.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| 프레임 그림·_sys_execve 분할 | 원 05 → 새 07+08 | 오프셋 표(35-46)+진입부 복습(80-93)+프레임 그림과 `lea EIP(%esp)` 코드(200-205)를 한 장에 담기엔 밀도가 높음 — 그림 전용 슬라이드 확보 (+1) |
| 헤더 읽기·형식 검사 분할 | 원 12 → 새 15+16 | 코드 2스크린 분량(221-225와 298-309 두 덩어리) — bread 헤더 읽기와 ZMAGIC·크기·N_TXTOFF 검사로 분리 (+1) |
| change_ldt 분할 | 원 18 → 새 22+23 | 리밋·베이스 계산(154-177 전반)과 인자 페이지 매핑 put_page(후반) — "베이스 불변" 메시지와 매핑 메커니즘을 각각 강조 (+1) |
| 태스크 필드·꼬리 0 채움 분할 | 원 20 → 새 25+26 | 필드 갱신(335-343 전반)과 341-343의 첫 do_no_page 연결은 서로 다른 메시지 — 08회차 연결을 전용 슬라이드로 (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02 "지도"→로드맵/구조, 원 36·37 "정리"→정답, 원 39·40 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 41장 → 47장 (+6) | 목표 범위 44–50 안(00-common §5) |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- lab/ 빌드의 심볼명(`do_execve` vs `_do_execve`, `sys_execve`, `change_ldt` — static이지만 -g로 보임, 슬라이드 34)과 줄 번호 확인 — 슬라이드 37·41의 "src 344·205 상당 줄은 lab에서 `list`로 확인" 각주의 근거 확보 (course-plan "PPTX 제작 전 확인 목록"의 심볼명·줄 번호 해당분).
- 사전 캡처 확보: 시연 A 3장(진입 · 344 직전 · next 후 = §5의 01·02·03), 시연 B 2장(04·05), 시연 C 1장(06) — 파일명 규칙 `materials/09-exec/captures/<두자리순번>-<설명>.png` (course-plan 확인 목록의 "각 회차 사전 캡처 파일명 규칙" 해당분).
- 게스트 환경 확인: 셸의 `ls` 경로("/bin/ls" 또는 "/usr/bin/ls" — 슬라이드 35 기대 출력), `/tmp` 쓰기 가능과 `chmod +x`(시연 C의 `/tmp/t.sh`), `/bin/sh` 존재.
- 캡처 각주에 lab 빌드·QEMU i386·GDB·수정 여부·캡처 날짜 필수 기재 — inode 번호·주소·리밋 값은 lab 디스크 이미지에 따라 다름(§8 마지막 항목). lab 줄 번호는 src와 다를 수 있으므로 슬라이드 줄 번호는 src 기준임을 각주로 명시.
- 이전 회차 자산 재사용 확인: 06회차 fork 그림(슬라이드 05), 07회차 64MB 칸 그림(슬라이드 10), 04회차 시스템 콜 프레임 그림(슬라이드 07), 08회차 do_no_page 자료(슬라이드 26·28·39).
