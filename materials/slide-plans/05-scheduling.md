# 05회차 상세 슬라이드 제작 계획 — 태스크와 스케줄링

- 기준: materials/course-plan.md `# 05. 태스크와 스케줄링` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/05-scheduling.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 42장 → 이 계획 48장 (+6)
- 로드맵 위치: 파트 B «실행의 길» · 05/15

## 1. 회차 개요

- **핵심 질문**: 타이머 틱 한 번에 실행 중인 태스크가 어떻게 바뀌는가?
- **학습 목표** (원천 그대로):
  1. `task_struct`의 앞 세 필드(`state`, `counter`, `priority`)와 `tss`의 역할을 말하고, `task[NR_TASKS]`·`current`·`jiffies`가 어디에 정의되어 있는지 가리킨다.
  2. `TASK_RUNNING / INTERRUPTIBLE / UNINTERRUPTIBLE / ZOMBIE / STOPPED` 다섯 상태의 전환 원인을 소스 줄 번호로 짚고, 0.11에서 실제로 `STOPPED`로 들어가는 코드가 없음을 확인한다.
  3. `do_timer`가 `counter`를 1 줄여 0이 되면 **사용자 모드에서 온 경우에만** `schedule()`을 부르는 조건(`cpl`)을 설명한다.
  4. `schedule()`의 선택 규칙(`state==RUNNING`이고 `counter` 최대)과 재충전 식 `counter = counter/2 + priority`를 손으로 계산한다.
  5. `switch_to(n)`가 `ljmp`로 TSS 전환을 일으키며, 이때 CPU가 레지스터 전체를 TSS에 저장·복원함을 GDB로 확인한다(`current` 변화, `jiffies`, `current->counter`).
- **읽을 소스 범위** (원본 src 기준, 원천의 줄 번호 그대로):
  - `include/linux/sched.h` 4–5, 19–23, 51–76, 78–107, 113–134, 136–142, 144–147, 149–164, 165–184
  - `kernel/sched.c` 46, 53–72, 77–92, 94–142, 144–149, 151–165, 167–186, 188–194, 266–303, 305–336, 338–346, 378–383, 385–412
  - `kernel/system_call.s` 48–53, 76–78, 95–100, 176–197
  - `kernel/exit.c` 20–33, 102–135, 165–182, 184–193
  - `fs/buffer.c` 40, 225, 260 · `kernel/chr_drv/tty_io.c` 126, 136, 227
  - `init/main.c` 138–148 · `kernel/fork.c` 82, 85, 131 (06회차 예고분)
- **상태 변화도 범위** (신규 슬라이드 23–25): `task_struct.state` 값 RUNNING(0)/INTERRUPTIBLE(1)/UNINTERRUPTIBLE(2)/ZOMBIE(3)/STOPPED(4). STOPPED는 정의(sched.h:23)와 `waitpid`의 case(exit.c:166)만 있고 진입 코드 없음 — "0.11에 미구현"으로 표시. "실행 중"은 상태 값이 아니라 `current`가 가리키는 태스크(RUNNING 안의 별도 표기).
- **비교 범위**: 필수 비교(신규 슬라이드 18–19) = `schedule()`이 호출되는 네 경로 (a)–(d), 축 = 누가 부르는가/현재 태스크 상태/복귀 지점. 보조 비교(신규 슬라이드 28) = `sleep_on` vs `interruptible_sleep_on`.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 05. 태스크와 스케줄링 | 표지 | ▪ 대제목 `05. 태스크와 스케줄링` ▪ 부제: 핵심 질문 "타이머 틱 한 번에 실행 중인 태스크가 어떻게 바뀌는가?" ▪ `Linux 0.11` 배지 + `1991`, 부제 한 줄 `Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)` ▪ 회차 정보 `05/15 · 파트 B «실행의 길»` ▪ 04의 `_timer_interrupt`에서 `call _do_timer` 다음을 오늘 본다고 연결 | — | 배지·부제·푸터 프레임(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | ▪ 핵심 질문 1문장 큰 글씨(원문 그대로) ▪ 오늘의 길: 10단계 미니 지도를 본문 크기로 — 오늘은 질문·지도·배경·코드·상태도·비교·시연·정답·확인·정리 10단계 모두를 다룸(상태도 23–25, 비교 18·19·28, 시연 34–41) ▪ "오늘은 다루지 않음" 단계 없음 | — | 10단계 미니 지도(전 단계 강조) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | ▪ 파트 A–G 타임라인에서 05만 ORANGE 강조 + 굵은 테두리 ▪ 완료(TEAL) 01–04, 이후(MUTED) 06–15 ▪ 오늘 한 줄 문구·연결 화살표 2개·10과의 점선은 §3 명세대로 ▪ 우하단 범례 + `Linux 0.11` 라벨 | —(§3 명세) | 로드맵 도형 다이어그램 |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | ▪ Linux 0.11 전체 구조도 골격 ▪ 오늘 범위 TEAL: `include/linux/sched.h`, `kernel/sched.c`, `kernel/system_call.s`(kernel/ 프로세스 계층) ▪ 오늘의 데이터 흐름 화살표 ORANGE: IRQ 0 타이머 → `_timer_interrupt` → `do_timer` → `schedule` → `switch_to` → TSS 전환 ▪ 누적 강조(옅은 TEAL) 01–04 영역은 §3 명세 ▪ 범위 밖 상자는 MUTED 실루엣(가리지 않음) | include/linux/sched.h · kernel/sched.c · kernel/system_call.s | 구조도 도형 다이어그램(§3) |
| 05 | 태스크란 커널이 기억하는 한 묶음 | 배경 | ▪ CPU는 하나, 프로그램은 여럿 ▪ 각 프로그램의 "멈춘 지점 + 레지스터 + 메모리 + 파일" 묶음을 `task_struct` 하나에 둔다 ▪ 1회차 "프로세스"와 같은 것을 0.11 소스는 task라고 부름 ▪ 오늘의 길: 이 묶음(06 fork에서 만들어짐)을 틱마다 갈아끼우는 장치를 본다 | include/linux/sched.h:78–107 | 불릿 + 묶음 개념 그림 |
| 06 | `struct task_struct` 전체 | 코드 | ▪ `sched.h:78–107` 전체를 한 화면에 ▪ 다섯 구역(80–85 하드코딩, 87–94 pid·시간, 96–102 fs, 104 ldt, 106 tss) 색 구분 ▪ "앞 세 필드는 `system_call.s:48–53`의 오프셋과 맞아야 한다"는 주석 강조 | include/linux/sched.h:78–107 · kernel/system_call.s:48–53 | 코드 캡션 sched.h:78–107 + 5구역 색 구분 |
| 07 | `state`, `counter`, `priority` | 코드 | ▪ 80–82 세 줄 ▪ state 주석 `-1 unrunnable, 0 runnable, >0 stopped`와 실제 값(sched.h:19–23) 대조 ▪ counter = 남은 틱, priority = 재충전 기준 ▪ INIT_TASK(113–114)는 둘 다 15 | include/linux/sched.h:80–82, 19–23, 113–114 | 코드 캡션 sched.h:80–82 + 주석·실제 값 대조 표 |
| 08 | `struct tss_struct` | 코드 | ▪ `sched.h:51–76` ▪ CPU가 태스크 전환 시 저장/복원하는 레지스터 전부 + esp0/ss0(04의 "커널 스택으로 전환" 출처) + cr3 + ldt ▪ 그림: 104바이트 배치 요약 | include/linux/sched.h:51–76 | 코드 캡션 sched.h:51–76 + 104바이트 배치 그림 |
| 09 | `task[]`, `current`, `jiffies`가 사는 곳 | 코드 | ▪ `sched.c:53–72` ▪ `union task_union` = task_struct와 4 KiB 커널 스택이 한 페이지 ▪ `init_task`, `current=&init_task.task`, `task[0]=…`, `jiffies=0` ▪ 그림: 한 페이지 안에서 스택이 위에서 내려오는 모습 | kernel/sched.c:53–72 · include/linux/sched.h:136–142 | 코드 캡션 sched.c:53–72 + task_union 한 페이지 그림 |
| 10 | task 0은 무엇을 하는가 | 코드 | ▪ `init/main.c:138–148` `fork()` 뒤 `for(;;) pause();` ▪ `sched.c:100–102` 주석: task 0는 idle, 죽지 않고 잠들지 않음 ▪ `schedule()`에서 `next=0` 기본값(sched.c:126)이 "아무도 못 뛰면 task 0" | init/main.c:138–148 · kernel/sched.c:100–102, 126 | 코드 캡션 main.c:138–148 + sched.c 주석 발췌 |
| 11 | 틱의 출처: 8253 | 코드 | ▪ `sched.c:46` `LATCH=1193180/HZ`=11931, `:406–408` 모드 3 설정 ▪ HZ=100 → 10 ms마다 IRQ0 ▪ `:409` `set_intr_gate(0x20,…)`, `:410` PIC IRQ0 마스크 해제 — 04회차 게이트 표 재사용 | kernel/sched.c:46, 406–410 · include/linux/sched.h:4–5 | 코드 캡션 sched.c:46, 406–410 + 04회차 게이트 표 재사용 |
| 12 | `_timer_interrupt` 다시 읽기 | 코드 | ▪ `system_call.s:176–197` ▪ 189 `incl _jiffies`(여기서만 증가), 190–191 EOI ▪ 192–194 `CS(%esp)&3`=CPL을 인자로 push, 195 `call _do_timer`, 197 `jmp ret_from_sys_call` ▪ "복귀 경로가 시스템 콜과 같다"는 점이 스케줄 뒤 복귀를 가능하게 함 | kernel/system_call.s:176–197 | 코드 캡션 system_call.s:176–197 + 줄 하이라이트(189, 192–195, 197) |
| 13 | `do_timer` (1): 회계 | 코드 | ▪ `sched.c:305–317` ▪ `beepcount`, cpl에 따라 `utime`/`stime` 증가 ▪ 그림: 사용자 모드 중 틱 → utime, 커널 모드 중 틱 → stime | kernel/sched.c:305–317 | 코드 캡션 sched.c:305–317 + utime/stime 회계 그림 |
| 14 | `do_timer` (2): 타이머 리스트 | 코드 | ▪ `sched.c:319–331` ▪ `next_timer->jiffies--`, 0 이하가 된 항목의 `fn()` 호출 ▪ `add_timer`(272–303)는 상대값 리스트라는 것만 한 줄 ▪ 플로피 모터용 | kernel/sched.c:319–331, 272–303 | 코드 캡션 sched.c:319–331 + add_timer 한 줄 각주 |
| 15 | `do_timer` (3): counter와 cpl 조건 | 코드 | ▪ `sched.c:332–335` 네 줄: `if ((--current->counter)>0) return; current->counter=0; if (!cpl) return; schedule();` ▪ 핵심: 커널 모드에서 틱이 오면 counter는 0이 돼도 `schedule()`을 **안 부른다** → 커널 코드는 선점되지 않음 | kernel/sched.c:332–335 | 코드 캡션 sched.c:332–335 네 줄 확대 + 조건 분기 강조 |
| 16 | 틱 한 번의 데이터 변화 | 배경 | ▪ 표: 틱 전/후 `jiffies`, `current->counter`, `current->utime/stime` ▪ counter가 1→0이 되는 틱에서만 `schedule()` ▪ 시연 A(슬라이드 35–36)에서 이 표를 실제 값으로 채운다 예고 | kernel/system_call.s:189 · kernel/sched.c:314–317, 332–335 | 틱 전/후 데이터 표(빈 칸 → 시연 A에서 채움) |
| 17 | 시스템 콜 끝에서도 스케줄 검사 | 코드 | ▪ `system_call.s:95–100` ▪ `state != 0`(시스템 콜 안에서 잠들었다 깨어난 경우) 또는 `counter == 0`이면 `reschedule`(76–78) ▪ `ret_from_sys_call`을 반환 주소로 push하고 `jmp _schedule` ▪ `schedule()`의 `ret`가 곧 `ret_from_sys_call`로 감 | kernel/system_call.s:95–100, 76–78 | 코드 캡션 system_call.s:95–100, 76–78 + 반환 주소 push 그림 |
| 18 | 비교 (1): `schedule()`이 불리는 네 경로 — 사례와 소스 | 비교 | ▪ (a) 타이머 틱에서 `do_timer`→`schedule`(cpl≠0 조건, sched.c:332–335) ▪ (b) 시스템 콜 복귀 직전 `reschedule`(system_call.s:95–100, state≠0 또는 counter==0) ▪ (c) 태스크 자발 호출 — `sleep_on`/`interruptible_sleep_on`/`sys_pause`/`do_exit`/`sys_waitpid`(sched.c:162,178,147; exit.c:133,188) ▪ (d) `release()`(exit.c:29) ▪ 각 경로 카드에 코드 캡션 1줄씩 | kernel/sched.c:332–335, 162, 178, 147 · kernel/system_call.s:95–100 · kernel/exit.c:133, 188, 29 | 네 경로 카드 4장(a–d) + 소스 캡션 |
| 19 | 비교 (2): 네 경로 비교표 — 누가·어떤 상태·어디로 | 비교 | ▪ 축 1 누가 부르는가: 인터럽트/시스템 콜/커널 함수 ▪ 축 2 현재 태스크 상태(호출 직전 `current->state`) ▪ 축 3 복귀 지점: `ret_from_sys_call`인가 호출자 다음 줄인가 ▪ 4행(경로 a–d)×3축 표 채우기 ▪ 선점 정책이나 CPU 모드와 섞지 않는다 | kernel/sched.c:332–335, 162, 178, 147 · kernel/system_call.s:95–100, 76–78 · kernel/exit.c:133, 188, 29 | 4행×3축 비교표 |
| 20 | `schedule()` (1): 깨우기 | 코드 | ▪ `sched.c:104–120` ▪ 역순 순회(`&LAST_TASK`→`&FIRST_TASK`, task 0 제외) ▪ alarm 만료 → SIGALRM 비트 ▪ `signal & ~(_BLOCKABLE & blocked)` 있고 INTERRUPTIBLE이면 RUNNING ▪ `_S`/`_BLOCKABLE`(23–24) | kernel/sched.c:104–120, 23–24 | 코드 캡션 sched.c:104–120 + `_S`/`_BLOCKABLE` 각주 |
| 21 | `schedule()` (2): 고르기 | 코드 | ▪ `sched.c:124–135` ▪ `c=-1, next=0` ▪ RUNNING이고 `counter > c`인 태스크 → `next` ▪ 역순 순회(`task[63]`→`task[1]`)에 `>`(strict)이므로 동률이면 **먼저 만난 인덱스 큰 쪽이 남는다** ▪ `if (c) break;` — c==0이면 모두 counter 0 → 재충전 | kernel/sched.c:124–135 | 코드 캡션 sched.c:124–135 + 역순 스캔 화살표 그림(task[63]→task[1]) |
| 22 | `schedule()` (3): 재충전 식 | 코드 | ▪ `sched.c:136–139` ▪ `counter = counter>>1 + priority` — **모든** 태스크(잠든 것 포함) ▪ 손계산 표: priority 15, counter 0/3/8인 세 태스크 → 15/16/19 ▪ 잠든 태스크는 깨어날 때 유리해짐(I/O 바운드 우대) ▪ 그다음 `switch_to(next)`(141) | kernel/sched.c:136–141 | 코드 캡션 sched.c:136–141 + 손계산 표 |
| 23 | 상태 변화도 (1): 다섯 상태와 `current` | 상태도 | ▪ 상태 원 5개: RUNNING(0) / INTERRUPTIBLE(1) / UNINTERRUPTIBLE(2) / ZOMBIE(3) / STOPPED(4) ▪ "current(실행 중)"는 RUNNING 안의 표기 — `state`에 "실행 중" 값은 없고 RUNNING 중 하나가 `current`일 뿐 ▪ STOPPED는 점선 원 + "진입 코드 없음(0.11에 미구현)" 표시 | include/linux/sched.h:19–23 | 상태 다이어그램(원 5개 + current 표기 + STOPPED 점선) |
| 24 | 상태 변화도 (2): 전환 원인과 소스 | 상태도 | ▪ RUNNING→INTERRUPTIBLE: `sys_pause`(sched.c:146), `interruptible_sleep_on`(:177), `sys_waitpid`(exit.c:187) ▪ RUNNING→UNINTERRUPTIBLE: `sleep_on`(sched.c:161); 생성 중 `copy_process`(fork.c:82) ▪ →RUNNING: `wake_up`(:191), `schedule` 117–119, `sleep_on` 164, `interruptible_sleep_on` 180, `copy_process` 마지막(fork.c:131) ▪ RUNNING→ZOMBIE: `do_exit`(exit.c:130); ZOMBIE→소멸: `sys_waitpid`→`release`(exit.c:176, 20–33) ▪ 화살표마다 원인 함수와 줄 번호 라벨 | kernel/sched.c:146, 177, 161, 191, 117–119, 164, 180 · kernel/exit.c:187, 130, 176, 20–33 · kernel/fork.c:82, 131 | 상태 전환 화살표 다이어그램(원인·줄 라벨) |
| 25 | 상태 변화도 (3): 변경 데이터와 유지 조건 | 상태도 | ▪ 표: 상태별로 변하는 데이터(`state`, `counter`(RUNNING·current일 때만 감소), 대기 큐 `*p`, `exit_code`(ZOMBIE)) ▪ 유지 조건: `schedule()`은 `state==0`인 태스크만 고른다, ZOMBIE는 `waitpid` 전까지 `task[]`에 남음 ▪ 재충전은 상태 무관 ▪ 호출 순서도(슬라이드 18–19)와 다른 그림임을 명시 | kernel/sched.c:124–140, 136–139 · kernel/exit.c:130, 20–33 | 상태별 변경 데이터·유지 조건 표 |
| 26 | `sleep_on`과 `wake_up` | 코드 | ▪ `sched.c:151–165`, `188–194` ▪ `tmp=*p; *p=current;` — 대기 큐가 "포인터 하나 + 각자의 스택 변수 tmp"로 이어진 리스트 ▪ `wake_up`은 머리 하나만 깨우고, 깨어난 쪽이 `tmp->state=0`으로 다음을 깨움(164) ▪ 그림: 세 태스크가 `bh->b_wait`에 잠든 모양 | kernel/sched.c:151–165, 188–194 | 코드 캡션 sched.c:151–165, 188–194 + 대기 큐 그림 |
| 27 | `interruptible_sleep_on` | 코드 | ▪ `sched.c:167–186` ▪ `repeat:` — 깨어났는데 `*p != current`(내가 머리가 아님)이면 머리를 깨우고 다시 잠 ▪ 시그널로 깨어날 수 있으므로 `schedule()` 앞부분(117–119)과 짝 ▪ 사용처 `tty_io.c:126,136` | kernel/sched.c:167–186, 117–119 · kernel/chr_drv/tty_io.c:126, 136 | 코드 캡션 sched.c:167–186 + `repeat` 흐름 강조 |
| 28 | 비교: `sleep_on` vs `interruptible_sleep_on` | 비교 | ▪ 축: 설정 상태(2 vs 1), 시그널로 깨는가(아니오/예), 깨어난 뒤 재검사(없음/`repeat`), 사용처(`buffer.c:40,225` 디스크 I/O / `tty_io.c:126,136` 키 입력 대기) | kernel/sched.c:151–165, 167–186 · fs/buffer.c:40, 225 · kernel/chr_drv/tty_io.c:126, 136 | 2행×4축 비교표 |
| 29 | `switch_to(n)` (1): 매크로 전문과 같은 태스크 검사 | 코드 | ▪ `sched.h:171–184` 매크로 전문을 한 화면에 + 단계 번호 ▪ `cmpl %%ecx,_current; je 1f` 같은 태스크면 아무것도 안 함 ▪ `movw %%dx,%1` — `__tmp.b`에 `_TSS(n)` 선택자 ▪ `_TSS(n)` 계산은 sched.h:149–164(슬라이드 32에서 다시) | include/linux/sched.h:171–184, 149–164 | 코드 캡션 sched.h:171–184 + 단계 번호 |
| 30 | `switch_to(n)` (2): `current` 갱신과 `ljmp`·`clts` | 코드 | ▪ `xchgl %%ecx,_current` — `current` 갱신 ▪ `ljmp %0` — `__tmp`(오프셋 무시, 선택자만)로 far jump = TSS 전환 ▪ 이후 `clts` 조건 ▪ `ljmp`의 목적지 오프셋(`__tmp.a`)은 설정하지 않는다 — 이해 확인 문항 4(슬라이드 47)와 연결 | include/linux/sched.h:171–184 | 코드 발췌(xchgl·ljmp·clts) + `__tmp` 구조 그림 |
| 31 | `ljmp`가 TSS로 가면 CPU가 하는 일 | 배경 | ▪ 현재 레지스터 전부(EIP 포함 = `ljmp` 다음 줄) → `current` 이전 태스크의 TSS에 저장; 새 TSS에서 전부 로드; TR 갱신; LDTR 갱신(tss.ldt) ▪ CR3 — 0.11은 모두 `&pg_dir`(sched.h:128) ▪ "커널 스택도 바뀐다"(ss/esp 복원) ▪ 다시 선택되면 `ljmp` 다음 줄부터 | include/linux/sched.h:51–76, 128, 171–184 | TSS 전환 그림(저장·로드·TR·LDTR·CR3·커널 스택 교체) |
| 32 | `sched_init`: TSS/LDT 설명자와 ltr | 코드 | ▪ `sched.c:385–412` ▪ 392–393 task 0의 TSS/LDT를 GDT 4·5번에 ▪ 394–401 나머지 63개 슬롯 0으로 ▪ 403 NT 플래그 클리어(iret가 태스크 복귀로 해석되지 않게) ▪ 404–405 `ltr(0)`, `lldt(0)`; `_TSS(n)`=(n<<4)+(4<<3)(sched.h:155) | kernel/sched.c:385–412 · include/linux/sched.h:155 | 코드 캡션 sched.c:385–412 + GDT TSS/LDT 슬롯 그림 |
| 33 | 커널 스택과 `tss.esp0` | 코드 | ▪ 04회차 `int 0x80` 시 CPU가 TSS의 ss0/esp0를 읽는다고 했다 ▪ 그 값이 `PAGE_SIZE+(long)&init_task`(sched.h:128) / `copy_process`의 `PAGE_SIZE+(long)p`(fork.c:93, 06회차) ▪ 태스크마다 커널 스택이 자기 페이지 끝 ▪ `union task_union` 그림 재사용 | include/linux/sched.h:128 · kernel/fork.c:93 · kernel/sched.c:53–72 | task_union 그림 재사용(09) + esp0 화살표 |
| 34 | 시연 환경 | 시연 | ▪ lab QEMU `-s -S` + GDB `target remote :1234`, 부팅 완료(셸 프롬프트) 후 중단점 ▪ 중단점이 타이머 틱마다(10 ms) 걸리므로 `cond`·`ignore`·`display`를 미리 설정, 관찰 뒤 반드시 `delete` ▪ 심볼명은 lab 빌드 기준 확인(`info functions do_timer`) ▪ 실패 시 사전 캡처(`기존 기록` 라벨) | —(lab/) | lab 환경 체크리스트 |
| 35 | 시연 A: `break do_timer`, `jiffies`와 `counter` | 시연 | ▪ `break do_timer`, `display jiffies`, `display current->pid`, `display current->counter` ▪ `display $cpl`은 없으므로 `p/x *(long*)($esp+4)`(cpl 인자) ▪ `c` 5~6회 반복 → jiffies +1, counter -1 관찰 ▪ 프롬프트 대기 중이면 `current->pid`=0(task 0, `pause` 루프)이고 cpl=3인 경우가 많음 ▪ counter가 0에 도달한 틱 다음 정지에서 pid가 바뀔 수 있음 | —(lab/ · kernel/sched.c:305–336 대응) | GDB 명령 스크립트 블록 |
| 36 | 캡처 A: 틱 연속 관찰 | 캡처 | ▪ GDB 로그: 연속 틱에서 jiffies 1씩 증가, 같은 pid의 counter 1씩 감소 ▪ 각주: lab 빌드, 수정 없음, 게스트는 셸 프롬프트 대기 중(대부분 task 0 또는 셸) ▪ 슬라이드 16의 표를 이 값으로 채움 | —(lab/) | materials/05-scheduling/captures/10-tick-jiffies-counter.png + 각주 |
| 37 | 시연 B: `counter`가 0이 되는 순간 | 시연 | ▪ `delete` 후 `break schedule`, `c`, `bt` ▪ 호출자가 `do_timer`인지 `reschedule`/`sleep_on`인지 확인(슬라이드 18–19 비교와 연결) ▪ `p task[0]->state`, `p task[1]->pid`, `p task[1]->state`, `p task[1]->counter`, `p task[1]->priority`(존재하는 인덱스까지) ▪ `p *task[i]`의 state/counter/priority/pid만 나열 | —(lab/ · kernel/sched.c:94–142 대응) | GDB 명령 스크립트 블록 |
| 38 | 캡처 B: `bt`와 태스크 표 | 캡처 | ▪ `bt` 출력(`schedule ← do_timer ← timer_interrupt` 또는 `schedule ← sys_pause ← system_call`)과 각 task의 state/counter/priority ▪ task 1(init)은 `waitpid`로 INTERRUPTIBLE(=1), 셸은 tty 입력 대기로 INTERRUPTIBLE(=1)인 경우가 보통 ▪ 각주 포함(lab 빌드·수정 없음·날짜) | —(lab/) | materials/05-scheduling/captures/20-schedule-bt.png, 21-task-state-counter.png + 각주 |
| 39 | 시연 C: `switch_to` 전후 `current` | 시연 | ▪ `break schedule` 뒤 `finish`가 안 되는 이유(ljmp로 다른 태스크로 감) 설명 ▪ 대신 `watch current`(hw watchpoint) 또는 `schedule`에 멈춘 뒤 `disassemble`로 `ljmp` 주소를 찾아 `break *<addr>`, `c`, `stepi` ▪ `p current->pid`, `p/x $esp`(커널 스택이 다른 페이지로), `p/x $eip` ▪ `info registers tr`은 QEMU gdbstub이 안 줄 수 있음 → 대체는 `p/x $cs`와 `$esp` 상위 비트 ▪ 둘째 태스크 확보용 백그라운드 명령 사전 실행(§5·§11) | —(lab/) | GDB 명령 스크립트 블록 + 실패 대응 흐름 |
| 40 | 캡처 C: 전환 전/후 | 캡처 | ▪ 두 캡처 나란히: `current->pid`, `$esp`, `$eip` ▪ 전환 후 `$eip`가 `ljmp` 다음 명령(`cmpl %%ecx,_last_task_used_math`)인 점 ▪ 각주: 환경·수정 여부 ▪ 셸 외에 둘째 태스크가 필요하면 백그라운드 명령 하나 실행 | —(lab/) | materials/05-scheduling/captures/30-switch-before.png, 31-switch-after.png 나란히 + 각주 |
| 41 | 관찰 vs 추론 구분 | 캡처 | ▪ 오늘 실제로 본 것: jiffies 증가, counter 감소, bt, current 변화 ▪ 소스로 추론한 것: TSS 내부 저장 순서(CPU 동작, GDB로 직접 안 보임), 재충전 값(틱 수가 많아 시연 시간 내 반복 재현은 어려움) | —(lab/ + src/ 추론) | 관찰 vs 추론 2열 표 |
| 42 | 질문의 답 (1): 틱에서 `schedule()`까지 | 정답 | ▪ IRQ0 → IDT[0x20] → `_timer_interrupt`(`jiffies++`) → `do_timer(cpl)` → `counter--` → (0이고 cpl=3) `schedule()` ▪ 각 단계에 파일:줄 ▪ 경로 다이어그램 상반부(하드웨어→인터럽트→회계·조건) | kernel/system_call.s:176–197 · kernel/sched.c:305–336 | 틱 한 번 경로 다이어그램 상반 |
| 43 | 질문의 답 (2): 선택·전환·복귀 | 정답 | ▪ `schedule()` → 깨우기 → 고르기/재충전 → `switch_to(next)` → `ljmp` TSS → 새 태스크의 `ljmp` 다음 줄 → … → 그 태스크의 `ret_from_sys_call` → `iret` ▪ 각 단계에 파일:줄 ▪ "틱 한 번에 실행 태스크가 바뀌는 조건 = counter 0 + 사용자 모드(cpl≠0)" 한 줄 강조 | kernel/sched.c:104–142 · include/linux/sched.h:171–184 · kernel/system_call.s:197 | 틱 한 번 경로 다이어그램 하반 |
| 44 | 왜 커널 모드에서는 안 바꾸는가 | 정리 | ▪ `do_timer`의 `if (!cpl) return;`(334) ▪ 0.11 커널은 비선점: 커널 안에서는 스스로 `schedule()`을 부를 때만 전환 ▪ 장점(락 불필요) / 비용(긴 커널 작업 중 응답 지연) ▪ 현대 커널의 선점은 14회차에서 | kernel/sched.c:334 · kernel/system_call.s:95–100 | 불릿 + 조건 코드 한 줄(334) |
| 45 | 흔한 오해 바로잡기 | 정리 | ▪ "schedule은 타이머만 부른다"(아니다, 슬라이드 18–19) ▪ "counter는 우선순위다"(남은 틱; priority가 기준) ▪ "STOPPED 상태가 있다"(정의만) ▪ "task 0도 schedule 대상"(루프는 `p > &FIRST_TASK`로 제외, next=0은 기본값) ▪ "switch_to가 레지스터를 직접 저장한다"(CPU가 TSS에) | include/linux/sched.h:19–23 · kernel/sched.c:124–140 · kernel/exit.c:166 | 오해 5개 카드(§8 전문과 대응) |
| 46 | 현대 커널 한 줄 | 배경 | ▪ 현대 Linux는 TSS 전환 대신 소프트웨어 문맥 전환, CFS 등 정책도 다름 ▪ 하지만 "틱 → 회계 → 필요 시 선택 → 전환"의 골격과 `state` 개념은 같다 ▪ 상세는 14회차 | —(14회차 예고) | 골격 4단계(틱→회계→선택→전환) 대응 그림 |
| 47 | 이해 확인 질문 | 확인 | ▪ 문항 1: 잠든 셸의 `counter`는 틱 100번에 얼마나 줄어나 ▪ 문항 2: `sys_write` 중 counter=0, 즉시 `schedule()`인가 ▪ 문항 3: task 0의 `pause()`는 왜 영원히 잠들지 않는가 ▪ 문항 4: `ljmp`의 목적지 오프셋(`__tmp.a`)은 왜 설정하지 않는가 ▪ 4문항, 정답 클릭 후 표시(정답은 §6) | —(§6 문항·정답) | 4문항 + 정답 표시 인터랙션 |
| 48 | 정리와 다음 회차 | 정리 | ▪ 정리 4줄: 태스크 = `task_struct`+TSS 묶음(`task[]`·`current`·`jiffies`) / 틱 → `do_timer` → counter 감소 → 사용자 모드일 때만 `schedule()` / `schedule()` = 깨우기 + 고르기(counter 최대) + 재충전(`counter = counter>>1 + priority`) / 전환 = `switch_to`의 `ljmp` → CPU가 TSS 저장·복원 ▪ 06 예고: "`task[1]`은 누가 어떻게 만들었나? `copy_process`가 TSS의 `eax`를 0으로 두면 자식은 `fork()`에서 0을 받는다 — `switch_to`가 TSS를 통째로 복원하기 때문" | kernel/fork.c:97(06 예고) | 정리 4줄 + 06 예고 패널 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: B «실행의 길» (04 인터럽트·시스템 콜 · 05 스케줄링 · 06 fork). 오늘 = 파트 B 가운데 상자.
- 완료(TEAL 채움): 01, 02, 03, 04. 오늘(ORANGE 채움 + 굵은 테두리): 05. 이후(MUTED 외곽선): 06–15.
- 오늘 한 줄 문구(05 상자 아래): "틱 한 번 — 회계에서 TSS 전환까지".
- 연결 화살표:
  - 04 → 05: "04: `_timer_interrupt`에서 `call _do_timer`까지 봤다 → 05: 그 다음 줄에서 실행 중인 태스크가 바뀐다".
  - 05 → 06: "05: `switch_to`로 TSS 전환을 봤다 → 06: `task[1]`은 누가 만드는가 — fork".
  - 점선(추가): 05 ↔ 10 — "ZOMBIE·`sys_waitpid`는 10(종료·대기·시그널)에서 다시 본다" (원천 지도 슬라이드의 10과의 점선 계승).
- 범례(완료/오늘/이후) + 우하단 `Linux 0.11` 라벨.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트(TEAL, 진하게): `include/linux/sched.h`(공통 영역에 표시), kernel/ 프로세스 계층 상자의 `kernel/sched.c`, 진입 계층의 `kernel/system_call.s`.
- 오늘의 데이터 흐름 화살표(ORANGE, 1개 계열): 8253 타이머(IRQ 0, 하드웨어 계층) → `kernel/system_call.s` `_timer_interrupt` → `kernel/sched.c` `do_timer` → `schedule` → `switch_to` → TSS 전환(GDT, 04회차에 이어 표시).
- 누적 강조(옅은 TEAL, 01–04 분): `boot/bootsect.s`·`boot/setup.s`·`boot/head.s`·`init/main.c`(01·03), `include/asm/system.h`·`include/linux/head.h`(02), `kernel/asm.s`·`kernel/traps.c`·`include/unistd.h`·`include/linux/sys.h`(04). `kernel/system_call.s`·`include/linux/sched.h`는 02·04에서 이미 등장했으나 오늘 파일이므로 진한 TEAL.
- 범위 밖 상자(mm/, fs/, blk_drv/, chr_drv/ 등)는 MUTED 외곽선 실루엣. 계층 경계(CPL=3/0, IRQ) 라벨 유지, 우하단 `Linux 0.11` 라벨.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 02 | 오늘의 길 미니 지표 | 상단 띠 | 10단계(질문–정리) 전부 강조 — 오늘은 빠지는 단계 없음 | 공통 프레임(00-common §3) |
| 03 | 15회차 로드맵 | 도형 다이어그램 | 파트 A–G 타임라인, 05 ORANGE·01–04 TEAL·06–15 MUTED, 화살표 2개 + 10과의 점선, 오늘 한 줄 문구, 범례·`Linux 0.11` | 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도 | 도형 다이어그램 | kernel/ 프로세스 상자 + sched.h·system_call.s 강조, IRQ 0→…→TSS 전환 ORANGE 흐름, 01–04 영역 옅은 TEAL | 공통 골격 + 04회차 강조 영역 |
| 05 | 태스크 묶음 개념 그림 | 개념 도형 | "멈춘 지점 + 레지스터 + 메모리 + 파일" 네 조각 → `task_struct` 한 상자 | — |
| 06 | task_struct 5구역 색 구분 | 코드 슬라이드 | 80–85/87–94/96–102/104/106 다섯 구역 TEAL 농도 차 | — |
| 08 | tss_struct 104바이트 배치 | 박스 다이어그램 | back_link~i387 필드 배치, esp0/ss0·cr3·eip·ldt 강조 | — |
| 09 | union task_union 한 페이지 | 메모리 그림 | 한 페이지 안 task_struct(아래)·커널 스택(위에서 내려옴), `PAGE_SIZE` 경계 | — |
| 11 | 8253·게이트 설정 표 | 표 | LATCH 11931·모드 3·`set_intr_gate(0x20,…)`·PIC 마스크 해제 | 04회차 게이트 표 |
| 13 | utime/stime 회계 그림 | 2분할 그림 | 사용자 모드 중 틱 → utime / 커널 모드 중 틱 → stime | — |
| 16 | 틱 전/후 데이터 표 | 표(빈 칸) | `jiffies`·`current->counter`·`current->utime/stime` 전/후 — 시연 A(슬라이드 36)에서 채움 | — |
| 17 | 반환 주소 push 그림 | 스택 도형 | `pushl $ret_from_sys_call; jmp _schedule` — `schedule()`의 `ret`이 곧 복귀 경로가 되는 모습 | 04회차 시스템 콜 프레임 |
| 18 | 네 경로 카드 | 카드 4장 | 경로 (a)–(d) 각각 코드 캡션 1줄 + 호출 지점 줄 번호 | — |
| 19 | 네 경로 비교표 | 표 | 4행(경로 a–d) × 3축(호출자 종류/호출 직전 상태/복귀 지점) | — |
| 21 | 역순 스캔 그림 | 배열 도형 | `task[63]`→`task[1]` 화살표, `>`(strict)로 동률 시 인덱스 큰 쪽 잔류 표시 | — |
| 22 | 재충전 손계산 표 | 표 | priority 15, counter 0/3/8인 세 태스크 → 15/16/19 | — |
| 23 | 다섯 상태 원 + current | 상태 다이어그램 | RUNNING 안 "current(실행 중)" 표기, STOPPED 점선 원 + "진입 코드 없음" 라벨 | — |
| 24 | 상태 전환 화살표 | 상태 다이어그램 | 전환마다 원인 함수·줄 번호 라벨(§2 슬라이드 24 내용 그대로) | — |
| 25 | 상태별 변경 데이터 표 | 표 | `state`·`counter`·`*p`·`exit_code` + 유지 조건 2줄 | — |
| 26 | 대기 큐 리스트 그림 | 포인터 연결 그림 | 세 태스크가 `bh->b_wait`에 잠든 모양, 각자 스택의 `tmp`로 이어짐 | — |
| 30 | `__tmp` 구조 그림 | 구조체 도형 | `__tmp.a`(오프셋, 무시됨)·`__tmp.b`(선택자) 2필드 | — |
| 31 | ljmp TSS 전환 그림 | 레지스터 흐름 그림 | 이전 TSS 저장 → 새 TSS 로드 → TR·LDTR 갱신 → CR3(`&pg_dir`) → 커널 스택(ss/esp) 교체 | — |
| 32 | GDT TSS/LDT 슬롯 그림 | 표 계열 도형 | GDT 4·5번(TSS0/LDT0) + 나머지 63슬롯 0, `_TSS(n)`=(n<<4)+(4<<3) | 02회차 GDT 그림 골격 |
| 33 | esp0 커널 스택 그림 | 메모리 그림 | 태스크마다 페이지 끝 커널 스택, `int 0x80` 진입 시 ss0/esp0 | 09 그림 재사용 + 04회차 프레임 |
| 42–43 | 틱 한 번 전체 경로 다이어그램 | 경로 그림 상·하반 | IRQ0→IDT[0x20]→`_timer_interrupt`→`do_timer`→`schedule`→`switch_to`→`ljmp`→`ret_from_sys_call`→`iret`, 단계마다 파일:줄 | 04회차 인터럽트 경로 그림 |
| 46 | 골격 4단계 대응 그림 | 2행 타임라인 | 0.11 "틱→회계→필요 시 선택→전환" vs 현대 "같은 골격, 다른 구현" 한 줄 | — |
| 48 | 06 예고 패널 | 2패널 도형 | 부모·자식이 같은 명령(`fork()` 다음)에서 EAX만 다른 모습 예고 | — |

## 5. 캡처 목록 (강사 시연)

캡처 순번 규칙: 십의 자리는 시연 블록(A=1x, B=2x, C=3x), 일의 자리는 같은 시연 안 순서 — 00-common §7 예시 `10-tick-jiffies-counter.png`와 동일 규칙. 모든 캡처 각주: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜`.

| 시연 | 캡처 파일(materials/05-scheduling/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A | 10-tick-jiffies-counter.png | `break do_timer`; `display jiffies`; `display current->pid`; `display current->counter`; `display/x *(long*)($esp+4)`; `c` ×6; 관찰 뒤 `delete` | jiffies 1씩 증가, 같은 pid의 counter 1씩 감소, cpl(프롬프트 대기 중 pid=0·cpl=3이 많음) | 사전 캡처 로그 1장(`기존 기록` 라벨) |
| B | 20-schedule-bt.png | `delete`; `break schedule`; `c`; `bt` | 호출자가 `do_timer`/`timer_interrupt` 또는 `sys_pause`/`system_call`(슬라이드 18–19 비교 연결) | 사전 캡처 |
| B | 21-task-state-counter.png | `p task[0]->state`; `p task[1]->pid`; `p task[1]->state`; `p task[1]->counter`; `p task[1]->priority`(존재하는 인덱스까지) | task 1(init)은 `waitpid`로 INTERRUPTIBLE(=1), 셸은 tty 입력 대기로 INTERRUPTIBLE(=1)인 경우가 보통 | 사전 캡처 2장 |
| C | 30-switch-before.png | `schedule`에서 `disassemble`로 `ljmp` 주소 검색; `break *<addr>`; `c`; `p current->pid`; `p/x $esp`; `p/x $eip` | 전환 전 pid·`$esp`(커널 스택 페이지)·`$eip` | `break *<ljmp 다음 주소>` 재시도, 그래도 실패 시 사전 캡처 2장 |
| C | 31-switch-after.png | `stepi`; `p current->pid`; `p/x $esp`; `p/x $eip` | pid·`$esp`(다른 4 KiB 페이지) 변화, `$eip`는 `ljmp` 바로 다음 명령 | 사전 캡처 2장(위와 세트) |

## 6. 이해 확인 질문과 정답 (해당 슬라이드 번호 명시 — 전부 슬라이드 47)

1. **Q.** 셸이 `read()` 안에서 키 입력을 기다리는 동안 타이머 틱이 100번 왔다. 셸의 `counter`는 얼마나 줄었는가? **A.** 0. `do_timer`는 `current->counter`만 줄이고(sched.c:332), 잠든 셸은 `current`가 아니다. 오히려 다른 태스크들이 모두 0이 되어 재충전이 일어나면 셸의 counter는 `counter/2 + priority`로 **늘어난다**(136–139).
2. **Q.** 커널이 `sys_write` 중일 때 틱이 와서 `counter`가 0이 됐다. 즉시 `schedule()`이 불리는가? **A.** 아니다. `do_timer`의 `if (!cpl) return;`(334) 때문에 커널 모드에서는 돌아간다. 대신 `sys_write`가 끝난 뒤 `system_call.s:99–100`의 `cmpl $0,counter; je reschedule`에서 `schedule()`로 간다.
3. **Q.** task 0의 `pause()`는 왜 영원히 잠들지 않는가? **A.** `sys_pause`가 `state=TASK_INTERRUPTIBLE`로 두고 `schedule()`을 불러도, `schedule()`의 선택 루프는 `c==0`일 때 `next=0`을 유지하므로(125–126) 뛸 태스크가 없으면 task 0로 `switch_to(0)`(현재와 같으면 아무것도 안 함)하고 `sys_pause`가 그냥 반환한다. `main.c:142–146` 주석.
4. **Q.** `switch_to(n)`에서 `ljmp`의 목적지 오프셋(`__tmp.a`)은 왜 설정하지 않는가? **A.** 선택자가 TSS 설명자를 가리키면 CPU는 오프셋을 무시하고 TSS 전환을 수행한다. 새 EIP는 목적지 TSS의 `eip` 필드에서 온다. `sched.h:171–177`.

## 7. 처음 등장하는 용어 (용어 | 정의 | 첫 등장 슬라이드)

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 태스크(task) | 0.11 소스에서 프로세스를 부르는 이름. `task_struct` 하나. | 05 |
| `counter` / `priority` | 남은 시간 조각(틱) / 재충전 기준값. | 07 |
| 타임 슬라이스 | counter가 가리키는 연속 실행 허용량. | 07 |
| `esp0`/`ss0` | 권한 0으로 진입할 때 쓸 커널 스택. | 08 |
| `current` | CPU를 점유 중인 태스크 포인터. | 09 |
| `jiffies` | 부팅 후 타이머 틱 수(HZ=100). | 09 |
| 틱(tick) | 8253이 만드는 10 ms 주기 IRQ0. | 11 |
| 비선점(non-preemptive) 커널 | 커널 모드 실행 중에는 타이머가 태스크를 바꾸지 않음. | 15 |
| 좀비(ZOMBIE) | 종료했지만 부모가 `waitpid`로 거두기 전까지 `task[]`에 남은 상태. | 23 |
| 대기 큐(`struct task_struct **p`) | 잠든 태스크를 잇는 포인터 하나짜리 리스트. | 26 |
| TSS 전환 | 세그먼트 선택자가 TSS를 가리키는 far jump로 CPU가 레지스터를 저장·복원하는 x86 기능. | 29 |

## 8. 흔한 오해 / 말하지 말아야 할 것

- `TASK_STOPPED`로 들어가는 코드가 0.11에 없다. "SIGSTOP으로 멈춘다"고 말하지 말 것(정의와 `waitpid`의 case만 있음: sched.h:23, exit.c:166).
- "실행 중"은 `state` 값이 아니다. RUNNING 여러 개 중 `current` 하나가 CPU를 갖는다.
- `counter`를 "우선순위"라고 부르지 말 것. `priority`는 재충전량, `counter`는 남은 틱.
- 재충전 식은 **모든** 태스크(잠든 것 포함)에 적용된다. "RUNNING 태스크만 재충전"이라고 말하지 말 것(136–139는 상태 검사 없음).
- `schedule()`은 타이머 외에도 여러 곳에서 불린다(슬라이드 18–19). "타이머 인터럽트 핸들러 = 스케줄러"로 축약하지 말 것.
- `switch_to`가 레지스터를 "코드로" 저장한다고 말하지 말 것. `ljmp` 한 명령으로 CPU가 TSS에 저장·복원한다. 현대 커널의 소프트웨어 전환과 다르다.
- `tss.cr3`가 태스크마다 다르다고 말하지 말 것. 0.11은 모두 `pg_dir` 하나(sched.h:128)이고 주소 분리는 LDT base(06·07회차).
- `add_timer`/플로피 타이머는 "`do_timer`가 호출하는 부가 리스트"까지만. 플로피 드라이버는 11회차.
- 시연 A의 pid·counter 값은 실행마다 다르다. 캡처 값을 "항상 이렇다"고 말하지 말 것.
- CFS·O(1) 스케줄러 등 현대 정책 설명은 14회차. 오늘은 한 줄 비교만.

## 9. 120분 운영안 (새 슬라이드 번호: 범위 | 분 | 진행)

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 핵심 질문, 로드맵·구조도(04의 `_timer_interrupt`에서 이어짐) |
| 05–10 | 18 | 배경: 태스크란 무엇인가, `task_struct`·`tss_struct`, `task[]`/`current`/`jiffies`, task 0 |
| 11–17 | 22 | 타이머 경로: 8253·`sched_init`, `_timer_interrupt`, `do_timer`, `counter` 감소, cpl 조건 |
| 18–22 | 15 | `schedule()` 호출 경로 비교, `schedule()` 본문, 재충전 식 계산 |
| 23–28 | 17 | 상태 변화도 3장, `sleep_on`/`wake_up`, 비교 |
| 29–33 | 13 | `switch_to`·TSS 전환, `sched_init`의 ltr/lldt, 커널 스택과 `esp0` |
| 34–41 | 20 | 강사 시연 A/B/C + 캡처 |
| 42–46 | 7 | 질문의 답, 오해 정리, 현대 커널 한 줄 |
| 47–48 | 3 | 이해 확인, 정리·06 예고 |

## 10. 기존 계획 대비 변경·증가

총 42장 → 48장 (+6). 원천 슬라이드 계획 표의 행은 하나도 버리지 않고 새 번호로 계승했다.

1. **앞부분 확장 (+2)**: 기존 01(제목)·02(15회차 지도) 2장 → 표준 앞부분 01–04 4장(표지/핵심 질문/로드맵/구조도, 00-common §2). 기존 02 지도의 내용(04→05→06 연결, 10(exit/wait: ZOMBIE)과의 점선)은 슬라이드 03 로드맵 §3 명세로 흡수.
2. **분할: 비교 네 경로 (+1)**: 기존 16 한 장(경로 4개 + 축 3개) → 18(사례·소스 카드)·19(3축 비교표) 두 장. 표 과밀 해소(00-common §5 증가분 우선순위 2).
3. **분할: 상태 변화도 (1) (+1)**: 기존 20 한 장(상태 원 5개 + 전환 화살표 10여 개) → 23(다섯 상태와 `current`)·24(전환 원인과 소스) 두 장. 다이어그램 전용 분할(우선순위 3). 기존 21은 25로.
4. **분할: `switch_to` (+1)**: 기존 25 한 장(매크로 5단계 전문 + 해설) → 29(매크로 전문·같은 태스크 검사)·30(`current` 갱신·`ljmp`·`clts`) 두 장. 코드 2스크린 분량 분리(우선순위 2).
5. **분할: 질문의 답 (+1)**: 기존 37 한 장(IRQ0→iret 전체 경로) → 42(틱에서 `schedule()`까지)·43(선택·전환·복귀) 두 장. 전체 경로 다이어그램 상·하반.
6. 유형 어휘 정렬: 기존 "제목"→표지, 이해 확인의 "질문"→확인, "질문의 답" 정리 슬라이드→정답(00-common §3 어휘). 본문 내용·줄 번호·함수명은 원천 그대로.
7. 슬라이드 상호 참조 갱신: 기존 14장 표→슬라이드 16, 기존 16 비교→슬라이드 18–19(슬라이드 25·37·45 및 §8에서).

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- lab 빌드의 심볼명 확인: `info functions do_timer`로 `do_timer` vs `_do_timer`(`_` 접두 유무) 및 `schedule`·`current`·`jiffies`·`task` 심볼 확인 — 슬라이드 34–40 시연 명령 전체가 이 심볼명에 의존.
- 틱 중단점 대응: `break do_timer`·`break schedule`이 10 ms마다 걸리는 것을 전제로 `cond`·`ignore` 설정 동작 확인, 관찰 뒤 `delete` 순서를 강사 노트에 고정.
- 셸 외 둘째 태스크 확보용 게스트 명령 사전 확인: lab 이미지에서 `sleep` 류 명령·루프 백그라운드 실행이 되는지(시연 C 전제) — 안 되면 대체 명령 확정.
- QEMU gdbstub 능력 확인: `stepi`가 `ljmp` 태스크 전환을 한 번에 넘기는지, `info registers tr`·`watch current`(hw watchpoint) 노출 여부 — 안 되면 `p/x $cs`·`$esp` 상위 비트·`break *<ljmp 다음 주소>` 대체 경로 확정.
- lab 줄 번호·코드 본문이 `src/`와 다른 부분 조사: 코드 캡션은 `src/` 기준 유지, 캡처 병지 시 "lab/ 수정본(심볼 `_` 접두 등 차이)" 각주 적용.
- 사전 캡처 확보: §5의 대체 자료 5종(10·20·21·30·31에 대응)을 `materials/05-scheduling/captures/`에 미리 확보, `기존 기록` 라벨 규칙 적용.
- 강사 노트: 시연 A pid·counter 값은 실행마다 다름(§8) — 캡처 수치를 "항상 이렇다"로 말하지 않도록 발표 멘트 고정.
