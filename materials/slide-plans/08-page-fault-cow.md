# 08회차 상세 슬라이드 제작 계획 — 페이지 폴트와 Copy-on-Write

- 기준: materials/course-plan.md `# 08. 페이지 폴트와 Copy-on-Write` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/08-page-fault-cow.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 40장 → 이 계획 46장 (+6)
- 로드맵 위치: 파트 C «메모리» · 08/15

## 1. 회차 개요

- 핵심 질문: **fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?**
- 학습 목표 (course-plan 원문 계승):
  1. 페이지 폴트(#PF, 벡터 14)가 발생했을 때 CPU가 남기는 정보(CR2, 에러 코드 P/W/U 비트)와 `mm/page.s`가 그것을 `do_no_page`/`do_wp_page`로 나누는 기준을 설명할 수 있다.
  2. `do_wp_page` → `un_wp_page`가 공유 페이지(`mem_map[n]≥2`, RW=0)를 새 페이지로 복사하고 카운트를 줄이는 과정을 PTE·mem_map 값 변화로 추적할 수 있다.
  3. `do_no_page`의 세 갈래(빈 페이지 / 다른 태스크와 공유 / 실행 파일에서 읽기)를 구분하고, 0.11의 "요구 적재(demand loading)"가 exec와 어떻게 연결되는지 설명할 수 있다.
  4. 80386에서 커널(ring 0) 쓰기가 R/W 비트를 무시하기 때문에 `write_verify`/`verify_area`가 필요한 이유를 설명할 수 있다.
  5. GDB에서 fork 직후 첫 쓰기 폴트를 잡아 `mem_map` 카운트와 PTE가 복사 전후로 바뀌는 것을 관찰할 수 있다.
- 읽을 소스 범위 (원본 src 기준 — course-plan 원문 계승):

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

- 상태 변화도·비교 범위 (course-plan 원문 계승): 상태 변화도 ① 선형 페이지(PTE) 한 칸의 상태, 상태 변화도 ② fork→쓰기 시나리오의 부모·자식·mem_map 3자 상태, 비교 ① 에러 코드 P/W/U 8가지, 비교 ② `do_no_page`의 세 갈래, 비교 ③ 쓰기 폴트를 일으키는 주체 2가지.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 08. 페이지 폴트와 Copy-on-Write | 표지 | 대제목 `08. 페이지 폴트와 Copy-on-Write` · 부제(핵심 질문 원문): "fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?" · 원 계획 부제 문구 "복사하지 않고 복사한 척하기" · 우상단 `Linux 0.11` 배지 + `1991`, 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `08/15 · 파트 C «메모리»` | — | 표지 배지·푸터(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치, 오늘 실제 다루는 단계만 강조 · 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다님(빠짐없이 강조) · 원 "지도" 슬라이드의 미니 지도 범례 계승 | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 C «메모리»의 08만 ORANGE 강조 · 완료(TEAL) 01–07 · 오늘(ORANGE) 08 · 이후(MUTED) 09–15 · 오늘 한 줄 문구: "공유된 읽기 전용 페이지, 첫 쓰기 폴트에 그때 복사 — Copy-on-Write" · 07→08 연결 문구와 08→09 연결 문구는 §3 명세 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | mm/ 계층의 mm/page.s·mm/memory.c를 진한 TEAL로 강조 · 오늘의 데이터 흐름 화살표(ORANGE): 쓰기 접근 → 페이지 폴트(CR2·오류 코드) → page_fault → do_no_page/do_wp_page → 새 페이지 할당·복사 · 보조 흐름 화살표: sys_read(fs/read_write.c:64) → verify_area(kernel/fork.c:24-37) → write_verify → un_wp_page(커널 쓰기는 폴트가 없는 경로) · 누적 강조(옅은 TEAL) 01–07 영역은 §3 명세 | kernel/traps.c:57, 199 · mm/page.s:12-40 · mm/memory.c(§1 읽기 범위) · kernel/fork.c:24-37 · fs/read_write.c:64 | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 복습: 07회차 끝의 상태 | 배경 | fork 직후 그림: 부모 PTE=5, 자식 PTE=5, 같은 물리 페이지, `mem_map=2` · copy_page_tables 복습 — 177 `&= ~2`, 180 부모 PTE 갱신, 183 `mem_map[]++` · "여기서 자식이 `x=1`을 실행하면?" 질문으로 오늘 시작 | mm/memory.c:150-189 | 07회차 fork 직후 PTE·mem_map 그림 재사용 |
| 06 | 폴트는 4회차에서 본 예외의 하나다 | 배경 | IDT 벡터 14, 트랩 게이트(traps.c:199 `set_trap_gate(14,&page_fault)`, 선언 kernel/traps.c:57) · 4회차 인터럽트 프레임 그림에 **에러 코드 4바이트가 추가**된 모양 · 복귀 시 `iret` 전에 에러 코드를 걷어내야 함 → page.s 15·33의 트릭 예고 | kernel/traps.c:57, 199 · mm/page.s:15, 33 | 4회차 인터럽트 프레임 그림 재사용 + 에러 코드 4바이트 추가(ORANGE) |
| 07 | CPU가 남기는 정보 (1): CR2 — 폴트를 낸 선형 주소 | 배경 | CR2 = 폴트를 낸 선형 주소, CPU가 페이지 폴트(#PF, 벡터 14) 발생 시 자동 저장 · 핸들러는 CR2와 에러 코드 이 둘만으로 무엇을 할지 정한다 · page.s의 `movl %cr2,%edx` push로 C 함수 인자(address)가 됨(12장에서 코드로 확인) | mm/page.s:12-40 | CR2→선형 주소를 가리키는 화살표 그림 |
| 08 | CPU가 남기는 정보 (2): 에러 코드 P/W/U | 배경 | bit0 P: 0=부재, 1=보호 위반 · bit1 W/R: 1=쓰기 · bit2 U/S: 1=사용자 모드 · 3비트 표 그림 · 0.11 page.s가 실제로 보는 비트는 bit0 P뿐(13장·28장에서 다룸)을 표 하단에 예고 | mm/page.s:12-40 | 에러 코드 3비트(P/W/U) 표(§4) |
| 09 | 80386의 함정: ring 0 쓰기는 R/W 비트를 무시한다 | 배경 | 386에는 CR0.WP가 없다(486부터) · 커널이 사용자 버퍼에 쓸 때(read()의 buf) 공유 페이지여도 폴트가 나지 않아 부모 페이지를 덮어쓸 수 있음 · 커널이 먼저 `verify_area`로 흉내 내야 함 · 오늘 비교 ③(30장)의 근거 | kernel/fork.c:24-37 · fs/read_write.c:64 | 386/486 CR0.WP 유무 대비 박스 |
| 10 | 요구 적재(demand loading): 없으면 그때 가져온다 | 배경 | memory.c:7-21 Linus 주석(01.12.91, 02.12.91) · exec는 헤더만 읽고 `current->executable`에 inode만 남김(exec.c:11-18 주석) · 실제 코드/데이터는 부재 폴트 때 디스크에서 · "30개 /bin/sh를 6MB에서" 일화 | mm/memory.c:7-21 · fs/exec.c:11-18(주석) | Linus 주석 인용 블록 |
| 11 | 오늘 읽을 함수 지도 | 배경 | page.s → do_wp_page → un_wp_page / do_no_page → {get_empty_page, share_page→try_to_share, bread_page+put_page} / verify_area → write_verify → un_wp_page · 호출 그래프(상태도와 구분 표기) · 오늘 첫 등장 함수 8개(do_no_page, do_wp_page, un_wp_page, write_verify, verify_area, get_empty_page, share_page, try_to_share) 위치 표시 | mm/page.s:12-40 · mm/memory.c:221-397 · kernel/fork.c:24-37 | 함수 호출 그래프 도형(§4) |
| 12 | 코드: page.s — 에러 코드를 eax와 바꾸는 트릭 | 코드 | mm/page.s:14-27 · `xchgl %eax,(%esp)`로 에러 코드를 eax에, eax를 스택에 보관(push 한 번 절약) · ds/es/fs=0x10 · `movl %cr2,%edx; pushl %edx; pushl %eax` → C 인자 (error_code, address) · 스택 그림 | mm/page.s:14-27 | xchgl 전후 스택 그림(§4) |
| 13 | 코드: page.s — 어느 핸들러로 가는가 | 코드 | mm/page.s:28-40 · `testl $1,%eax`: P=0 → `_do_no_page`, P=1 → `_do_wp_page` · `addl $8,%esp`로 인자 제거, pop 순서, `iret` · **W/U 비트는 보지 않음**을 강조(비교 ① 28장에서 다룸) | mm/page.s:28-40 | `testl $1` 2갈래 분기 도식(미니) |
| 14 | 코드: do_wp_page — PTE 주소 계산 | 코드 | mm/memory.c:247-259 · `#if 0` CODE_SPACE 검사(estdio가 코드 영역에 쓰기 때문에 꺼 둠, 250-251 주석 · CODE_SPACE 매크로는 mm/memory.c:49-50) · PDE=`*(address>>20&0xffc)`, PTE 주소=`(PDE&0xfffff000)+((address>>10)&0xffc)` → `un_wp_page(&PTE)` · 07회차 관용구 재등장 | mm/memory.c:247-259 · mm/memory.c:49-50 | 코드 인용 + PTE 주소 계산식 하이라이트 |
| 15 | 코드: un_wp_page — 두 갈래 | 코드 | mm/memory.c:221-238 · 판정: `old_page>=LOW_MEM && mem_map==1` — 카운트 하나로 복사 여부 결정 · (a) 갈래: `*table_entry \|= 2; invalidate()` (복사 없음: 상대가 이미 복사해 갔거나 fork 전 상태) · (b) 갈래: `get_free_page()`, `mem_map[old]--`, `*table_entry = new\|7`, `invalidate()`, `copy_page(old,new)` · 그림은 다음 장(16)에서 | mm/memory.c:221-238 | 코드 인용((a)/(b) 갈래 색 구분) |
| 16 | 그림: 공유 페이지가 쓰기 폴트로 분리된다 — un_wp_page 복사 전/후 | 상태도 | 오늘의 핵심 그림: 공유 읽기 전용 페이지 → 쓰기 폴트 → 분리 · 복사 전: 부모 PTE=A(하위 5), 자식 PTE=A(하위 5), 같은 물리 페이지 A, `mem_map[A]=2` · 자식 쓰기 폴트((b)갈래): 자식 PTE=B(하위 7) 새 페이지, `copy_page(A,B)`, `mem_map[A]=1`·`mem_map[B]=1` · 부모 쓰기 폴트((a)갈래): A(하위 5)→A(하위 7) 제자리 승격, 복사 없음 · 대응 코드 mm/memory.c:226-237 | mm/memory.c:221-238 | 핵심 상태 변화 그림(§4 상세 명세) |
| 17 | 코드: write_verify / verify_area — 폴트 없는 COW | 코드 | verify_area(kernel/fork.c:24-37): 논리→선형(`+get_base(current->ldt[2])`) 후 4KB마다 write_verify · write_verify(mm/memory.c:261-272): PDE 없으면 통과(부재는 나중에 do_no_page가 처리), PTE 하위 2비트가 `01`(present, non-writable)이면 `un_wp_page` · 호출처: `sys_read`가 `verify_area(buf,count)` 호출(fs/read_write.c:64), kernel/sys.c:108, 159, 224 | mm/memory.c:261-272 · kernel/fork.c:24-37 · fs/read_write.c:64 · kernel/sys.c:108, 159, 224 | 코드 인용 + 논리→선형 변환 미니 그림 |
| 18 | 코드: copy_page와 invalidate | 코드 | `copy_page(from,to)`(mm/memory.c:54-55): `rep movsl` 1024회 = 4KB · `invalidate()`(mm/memory.c:39-40): `movl $0,%cr3` = TLB 전체 무효화 · un_wp_page가 PTE를 바꾼 뒤 invalidate를 **먼저** 하고 복사하는 순서(235-237) — 복사 중엔 새 페이지가 이미 매핑됨 | mm/memory.c:54-55, 39-40 · mm/memory.c:235-237 | 코드 인용(`rep movsl`·`movl %cr3` 하이라이트) |
| 19 | 코드: do_no_page (1/3) — 어디서 온 폴트인가 | 코드 | mm/memory.c:365-377 · `address &= 0xfffff000`, `tmp = address - current->start_code`(태스크 내 오프셋) · `!executable \|\| tmp >= end_data` → `get_empty_page(address)` 후 return (스택·bss·힙: 0으로 채운 빈 페이지) | mm/memory.c:365-377 · include/linux/sched.h:88, 100 | 코드 인용 + start_code/end_data 개념 바 |
| 20 | 코드: get_empty_page | 코드 | mm/memory.c:274-282 · `get_free_page` + `put_page`, 실패 시 `free_page(tmp)`(0이어도 무시됨, 91행) 후 `oom()` · `oom()`(mm/memory.c:33-37): "out of memory" 출력 후 `do_exit(SIGSEGV)`(include/signal.h:23 `SIGSEGV 11`) · "메모리 부족 = 프로세스 죽음" 정책 | mm/memory.c:274-282 · mm/memory.c:33-37, 91 · include/signal.h:23 | 코드 인용 |
| 21 | 코드: do_no_page (2/3) — 같은 프로그램을 돌리는 다른 태스크와 공유 | 코드 | mm/memory.c:378-379 + share_page(344-363) · `executable->i_count<2`면 포기, task[] 역순 탐색, 같은 executable이면 try_to_share · 연결: exec.c가 inode를 `current->executable`에 두는 이유 | mm/memory.c:378-379, 344-363 · include/linux/sched.h:100 | 코드 인용 + task[] 탐색 도식 |
| 22 | 코드: try_to_share — clean 페이지만 공유 | 코드 | mm/memory.c:292-334 · 상대 PDE/PTE 계산(start_code 오프셋 더함) · `(phys_addr & 0x41) != 0x01` → bit6(Dirty)=1이면 공유 안 함(Accessed는 bit5) · LOW_MEM~HIGH_MEMORY 범위 확인, 내 PDE 없으면 테이블 생성 · 양쪽 PTE RW=0(`&= ~2`), `mem_map[]++` · 그림: 두 태스크의 PTE가 하나의 페이지를 공유(5,5,count+1) | mm/memory.c:292-334 | 코드 인용 + 두 태스크 공유 그림(§4) |
| 23 | 코드: do_no_page (3/3a) — block 계산과 bmap×4 | 코드 | mm/memory.c:380-397(전반) · `block = 1 + tmp/BLOCK_SIZE`(헤더 1블록 건너뜀), `BLOCK_SIZE`(1024) · `bmap`(fs/inode.c:140-143: 파일 블록 → 디스크 블록)을 연속 4블록에 호출 · 다음 장(24)에서 `bread_page`로 이어짐 | mm/memory.c:380-397 · fs/inode.c:140-143 | 코드 인용 + block 산식 하이라이트 |
| 24 | 코드: do_no_page (3/3b) — bread_page·bss 0 채움·put_page | 코드 | mm/memory.c:380-397(후반) · `bread_page(page, i_dev, nr)`(fs/buffer.c:296-315: 블록 4개를 한 페이지에 읽음) · `end_data` 넘는 꼬리를 0으로(387-392) · `put_page`(mm/memory.c:197-219 복습) · 실패 시 `free_page`+`oom` | mm/memory.c:380-397 · fs/buffer.c:296-315 · mm/memory.c:197-219 | 코드 인용 + 페이지 4블록 레이아웃 그림(§4) |
| 25 | 코드로 본 "폴트 뒤 재실행" | 코드 | `iret` 후 CPU는 **같은 명령**을 다시 실행한다(폴트는 fault형 예외: 저장된 EIP가 폴트 명령 자신) · page.s가 레지스터를 모두 복원하는 이유 · 4회차 트랩/폴트 구분 복습 한 줄 | mm/page.s:12-40 | 폴트→같은 명령 재실행 타임라인 그림 |
| 26 | 상태 변화도 ①: 선형 페이지(PTE) 한 칸의 상태 | 상태도 | 상태 4개: `부재(0)` / `단독 RW(7, count 1)` / `공유 RO(5, count≥2)` / `RO지만 단독(5, count 1)` · 전환: put_page(부재→7), copy_page_tables·try_to_share(7→5, count+1), 쓰기 폴트 un_wp_page(b)(5,n→새 7, 상대 count-1), un_wp_page(a)(5,count1→7), free_page_tables(→0) · 변경 데이터·유지 조건(PTE 수 = count) 표 | mm/memory.c:150-189, 197-219, 221-238, 292-334 | 상태 변화도 ①(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 27 | 상태 변화도 ②: fork 뒤 쓰기 시나리오의 3자 상태 | 상태도 | 열: 부모 PTE / 자식 PTE / 물리 페이지 A count / 물리 페이지 B count · fork 전 (7,—,1,—) → fork 후 (5,5,2,—) → 자식 쓰기 폴트 (5,7→B,1,1) → 부모 쓰기 폴트 (7,7→B,1,1: un_wp_page (a)갈래, 복사 없음) · 각 행의 전환 원인 줄 번호 | mm/memory.c:150-189(fork) · mm/memory.c:221-238(두 쓰기 폴트) | 상태 변화도 ② 3자 표(§4 상세 명세) |
| 28 | 비교 ①: 에러 코드 P/W/U 8가지 | 비교 | 범위: 3비트 조합 전부 — 표 (U,W,P) → 의미 → 0.11에서 발생? → 가는 곳 · (1,0,0) 사용자 읽기 부재 → do_no_page / (1,1,0) 사용자 쓰기 부재 → do_no_page / (1,1,1) 사용자 쓰기 보호 → do_wp_page(COW) · (1,0,1) 사용자 읽기 보호 → 0.11 PTE는 모두 US=1이라 발생하지 않음 / (0,0,1) 발생 없음 · (0,0,0)·(0,1,0) 커널이 사용자 메모리 접근 중 부재 → do_no_page(예: 아직 적재 안 된 버퍼를 read가 채울 때) · (0,1,1) 커널 쓰기 보호 → **386에서는 폴트 자체가 없음** → verify_area · 표 하단: page.s가 P만 본다 | mm/page.s:28-40 · kernel/fork.c:24-37 | 8조합 비교표 |
| 29 | 비교 ②: 부재 페이지를 채우는 세 갈래 | 비교 | 범위: do_no_page의 모든 선택지 · 빈 페이지(조건 `!executable \|\| tmp>=end_data`, 374-376, 내용 0) · 공유(`share_page` 성공, 378, 내용 다른 태스크 페이지, RO) · 디스크(380-396, 내용 a.out 블록 4개 + 꼬리 0) · 각 갈래가 mem_map에 미치는 영향(+1 신규 / 기존 +1 / +1 신규) | mm/memory.c:365-397, 274-282, 344-363 | 세 갈래 비교표 |
| 30 | 비교 ③: 쓰기 위반을 처리하는 두 경로 | 비교 | 범위: 사용자 코드의 쓰기 / 커널의 사용자 공간 쓰기 — 2가지 · 사용자: CPU #PF → page.s → do_wp_page → un_wp_page · 커널: 폴트 없음 → 시스템 콜 진입부 verify_area(fork.c:24-37) → write_verify → un_wp_page · 둘 다 `un_wp_page`로 수렴 · 호출처 목록(read_write.c:64, sys.c:108/159/224) | mm/page.s:28-40 · mm/memory.c:247-272 · kernel/fork.c:24-37 · fs/read_write.c:64 · kernel/sys.c:108, 159, 224 | 두 경로 비교 도식·표 |
| 31 | 숫자로 보는 fork + 자식 쓰기 | 코드 | 07회차 시연 환경 기준 예시 표 · 셸(부모) 페이지 k개 → fork 후 자식 PTE k개 추가, mem_map 각 +1 · 자식이 스택 한 페이지에 쓰면 그 페이지만 count 2→1, 새 페이지 count 1 · "복사된 페이지 수 = 실제로 쓴 페이지 수" · 실제 수치는 캡처 값으로 바꿀 것임을 각주 | mm/memory.c:150-189, 221-238 | 예시 수치 표(07회차 시연 값 기반) |
| 32 | 시연 준비: 어떤 쓰기가 첫 폴트를 내는가 | 시연 | fork에서 돌아온 직후 사용자 코드의 첫 `push`/`call`이 스택 페이지에 쓴다 → 부모든 자식이든 fork 직후 **스택 페이지**가 첫 COW 대상 · 따라서 셸에서 아무 명령을 쳐도 `do_wp_page`가 즉시 걸린다 — 테스트 프로그램 없이도 시연 가능 · (선택) 게스트 gcc로 `cow.c`(전역 변수 쓰기 전후 `getpid`) 컴파일 | —(시연 전략) | (선택) cow.c 코드 블록 |
| 33 | 시연 A-1: fork 직후 쓰기 폴트 잡기 | 시연 | 환경: lab/ `make debug`, `gdb tools/system`, `target remote :1234`, `c`, 셸 프롬프트 확인 · 중단점 `b un_wp_page`(do_wp_page보다 PTE 포인터 `table_entry`를 바로 볼 수 있어 편함), 셸에 `ls` 입력 → 셸이 fork → 정지 · `p current->pid`(부모 셸 pid 또는 자식 pid — 스케줄 순서에 따라 다름), `bt`(기대: `un_wp_page ← do_wp_page ← page_fault`) · `p/x *table_entry` → 기대 `0x....005`(P+US, RW=0), A = 값 & 0xfffff000 · `p mem_map[(A-0x100000)>>12]` → 기대 2 · `p/x $cr2` 또는 `up` 후 `p/x address` | mm/memory.c:221-238 · mm/page.s:12-40 | GDB 명령 블록 · 캡처 01(§5) |
| 34 | 캡처 A-1: 복사 전 | 캡처 | GDB 로그 캡처 게시 · 옆에 상태도 ②의 "(5,5,2)" 행 표시 · 각주: lab/ 빌드 · QEMU i386 TCG · GDB · 수정 없음 · 캡처 날짜 | mm/memory.c:221-238(관찰 대상) | materials/08-page-fault-cow/captures/01-un-wp-page-before.png(§5) |
| 35 | 시연 A-2: un_wp_page 통과 후 | 시연 | `finish` 후 같은 PTE 재조회: `p/x *(unsigned long*)<PTE 주소>`(기대 하위 비트 7, 상위 주소 B≠A) · `p mem_map[(A-0x100000)>>12]`(기대 1), `p mem_map[(B-0x100000)>>12]`(기대 1) · `x/4wx A`와 `x/4wx B` 내용 동일(복사 직후) · 이어서 `c` → 상대 태스크의 쓰기 폴트에서 (a)갈래(`\|= 2`, 복사 없음)인지 확인: `p/x *table_entry` 하위 5, `p mem_map[...]` 1 → `finish` 후 같은 주소에 하위 7(제자리 승격) | mm/memory.c:226-237 | GDB 명령 블록 · 캡처 02·03(§5) |
| 36 | 캡처 A-2: 복사 후 | 캡처 | 두 번째 캡처 게시 · 상태도 ② "(5,7→B,1,1)" 행 표시 · "어느 쪽(부모/자식)이 먼저 폴트를 냈는지는 스케줄 순서에 따라 다름"을 각주로 · 상대 태스크 (a)갈래 제자리 승격 캡처 03 병행 게시 | mm/memory.c:226-237(관찰 대상) | 02-un-wp-page-after.png · 03-un-wp-page-promote.png(§5) |
| 37 | 시연 B: 요구 적재 — do_no_page 관찰 | 시연 | `b do_no_page`(A의 중단점은 `delete` 또는 `disable`), 셸에서 새 명령(예: `ls`) → exec 직후 첫 정지 · `p/x address`, `p/x current->start_code`, `p address - current->start_code`(기대 0 = 엔트리 페이지) · `p error_code`(기대 4 또는 6: U=1,P=0), `p current->executable->i_num` · `finish` 후 PTE가 7이 되고 `x/8xb address`에 a.out 코드 · 다음 정지는 스택(`tmp >= end_data` 갈래) | mm/memory.c:365-397 | GDB 명령 블록 · 캡처 04·05(§5) |
| 38 | 캡처 B-1: 코드 페이지 — 디스크 갈래 | 캡처 | 코드 페이지(디스크 갈래) 캡처 — `address - start_code` = 0(엔트리 `a_entry`=0의 페이지), `error_code` 4 또는 6, `finish` 후 `x/8xb address`의 코드 바이트 · 비교 ②의 "디스크" 행과 연결 · 각주: lab 소스 줄 번호는 src와 다를 수 있음 · 캡처 각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 | mm/memory.c:380-397(관찰 대상) | 04-do-no-page-code.png(§5) |
| 39 | 캡처 B-2: 스택 페이지 — 빈 페이지 갈래 | 캡처 | 스택 페이지(빈 페이지 갈래) 캡처 — `p/x address`가 64MB 칸 끝 근처(`start_code + 0x4000000 - ...`), `tmp >= end_data` 갈래 · 비교 ②의 "빈 페이지" 행과 연결 · 각주: lab 소스 줄 번호는 src와 다를 수 있음 · 캡처 각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜 | mm/memory.c:374-376(관찰 대상) | 05-do-no-page-stack.png(§5) |
| 40 | 시연 C(선택): 커널 쓰기는 폴트가 없다 | 시연 | `b write_verify`, 셸에서 `cat`에 입력 → read() 경로의 `verify_area`가 호출되는 것을 `bt`로 확인(기대: `verify_area ← sys_read ← system_call`) · 실패 시 사전 캡처(06) · 각주: 줄 번호는 lab 기준 | mm/memory.c:261-272 · kernel/fork.c:24-37 | GDB 명령 블록 · (대체) 06-write-verify-bt.png(§5) |
| 41 | 질문의 답 (1): 부모의 값이 그대로인 이유 | 정답 | fork는 PTE만 복사하고 둘 다 RO(5)로 · 자식의 쓰기 → #PF(U=1,W=1,P=1) → do_wp_page → un_wp_page (b)갈래 → 자식 PTE만 새 페이지 B로 · 부모 PTE는 여전히 A · 그림 한 장 | mm/memory.c:150-189, 221-238 | 답 그림 한 장(부모 A·자식 B, §4) |
| 42 | 질문의 답 (2): 그래서 fork는 싸다 | 정답 | 복사되는 것은 "쓴 페이지"뿐 · exec가 곧 따라오면(09회차) 대부분 페이지는 복사되지 않고 free_page_tables로 반납 · 현대 커널도 같은 원리(단, WP 비트가 있어 커널 쓰기도 폴트) | mm/memory.c:150-189 · fs/exec.c(09회차 연계) | 요점 강조 박스 |
| 43 | 오늘 코드가 쓰는 데이터 요약 | 정리 | CR2, 에러 코드, PTE 하위 비트(0/5/7)와 bit6 Dirty, `mem_map`, `current->start_code/end_data/executable` · 함수×데이터 교차표 | include/linux/sched.h:88, 100 · mm/memory.c(§1 읽기 범위) | 함수×데이터 교차표 |
| 44 | 이해 확인 질문 | 확인 | 4문항 질문만 게시(§6 원문 그대로) · 핸들러 선택 비트 / un_wp_page 복사 없이 `\|= 2`인 경우 / read(fd,buf,n)의 buf가 공유 페이지일 때 보호 / exec 직후 첫 명령 페이지 | mm/page.s:28 · mm/memory.c:226-229 · fs/read_write.c:64 · mm/memory.c:380-394(정답 근거) | 문항 4개 텍스트 |
| 45 | 이해 확인 정답 | 확인 | 정답과 근거 줄 번호(§6 원문 그대로) · 1번: bit0 P만(`testl $1,%eax`, page.s:28) · 2번: LOW_MEM 이상 && `mem_map[]==1`(memory.c:226-229) · 3번: 386 ring 0 쓰기는 폴트 없음 → `verify_area(buf,count)`(read_write.c:64) → write_verify → un_wp_page · 4번: 없다 — 첫 fetch가 부재 폴트 → do_no_page가 `bmap`/`bread_page`로 읽어 `put_page`(memory.c:380-394) | (§6 정답 근거와 동일) | 정답 4개 텍스트 |
| 46 | 정리·다음 회차 예고 | 정리 | 09회차 "PID는 그대로인데 프로그램은 어떻게 바뀌는가?" · 오늘 본 do_no_page가 exec 직후 프로그램을 실제로 적재한다 · 미리 볼 파일: fs/exec.c, include/a.out.h · 파트 C «메모리» 마무리 — 07(주소 변환)·08(폴트·CoW)로 메모리 축 완결 | —(09회차 예고) | 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: C «메모리» · 08/15 — 파트 C의 마지막 회차(07 주소 변환 → 08 페이지 폴트·CoW). 완료(TEAL) 01–07, 오늘(ORANGE + 굵은 테두리) 08, 이후(MUTED) 09–15.
- 오늘 한 줄 문구: "공유된 읽기 전용 페이지, 첫 쓰기 폴트에 그때 복사 — Copy-on-Write"
- 07→오늘 연결 화살표 문구: "07: 페이지 테이블의 R/W 비트가 0인 공유 페이지를 봤다 → 08: 그 페이지에 쓰면 무슨 일이 일어나는가"
- 오늘→09 연결 화살표 문구: "08: fork 뒤 대부분 페이지는 복사되지 않은 채 exec로 이어진다 → 09: fork로 만든 자식이 exec로 새 프로그램을 불러오면 — PID는 그대로인데 프로그램은 어떻게 바뀌는가?"
- 원 "지도" 슬라이드(원 02) 내용 계승: 완료 상자 07에는 "PTE·mem_map 표를 그대로 사용" 연결 라벨, 이후 상자 09에는 "exec가 오늘의 do_no_page를 호출" 연결 라벨. 미니 지도 범례는 슬라이드 02 오늘의 길에서 계승.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL): mm/ 계층의 mm/page.s(폴트 진입 어셈블리)와 mm/memory.c(do_wp_page·un_wp_page·write_verify·do_no_page·share_page·try_to_share).
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): 쓰기 접근 → 페이지 폴트(CR2·오류 코드) → page_fault(mm/page.s) → do_no_page/do_wp_page(mm/memory.c) → 새 페이지 할당·복사.
- 보조 화살표(ORANGE, 2번째 — 00-common §2가 허용하는 1–2개 안): sys_read(fs/read_write.c:64) → verify_area(kernel/fork.c:24-37) → write_verify(mm/memory.c) → un_wp_page — 커널 쓰기는 폴트가 없어 커널이 직접 흉내 내는 경로.
- 누적 강조(옅은 TEAL, 01–07): 파트 A — boot/bootsect.s·boot/setup.s·boot/head.s·init/main.c(01–03) / 파트 B — kernel/system_call.s·kernel/asm.s·kernel/traps.c(04), include/linux/sched.h·kernel/sched.c(05), kernel/fork.c(06) / 파트 C — mm/memory.c(07, 오늘 진한 강조와 겹침). kernel/traps.c·kernel/fork.c는 오늘 보조 화살표의 경유점이므로 라벨 유지.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(08 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 08 ORANGE, 01–07 TEAL, 09–15 MUTED, 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(mm/ 강조) | 도형 다이어그램 | §3 명세 그대로 — mm/page.s·mm/memory.c 강조 + 데이터 흐름 화살표 2 | 전 회차 공통 골격 + 07 누적 영역 |
| 06 | 폴트 프레임 = 인터럽트 프레임 + 에러 코드 4바이트 | 도형 | 4회차 인터럽트 프레임(SS:ESP·EFLAGS·CS:EIP) 아래에 에러 코드 4바이트 추가(ORANGE), iret 전 걷어내는 지점 표시 | 04회차 인터럽트 프레임 그림 |
| 08 | 에러 코드 3비트(P/W/U) 표 | 표 | bit0 P(0=부재, 1=보호 위반) / bit1 W(1=쓰기) / bit2 U(1=사용자 모드) — 비트·값·의미 3열 | — |
| 11 | 오늘의 함수 호출 그래프 | 도형 | page_s → do_wp_page → un_wp_page / do_no_page → {get_empty_page, share_page → try_to_share, bread_page+put_page} / verify_area → write_verify → un_wp_page · 상태도 아님을 명시 | 07회차 함수 관계도 양식 |
| 12 | page.s 스택 그림 | 도형 | `xchgl %eax,(%esp)` 전후 스택 상태: 에러 코드·eax 보관·CR2 push 순서와 C 인자 (error_code, address) 위치 | 04회차 시스템 콜 스택 그림 양식 |
| 16 | 공유 페이지 → 쓰기 폴트 → 분리 (핵심) | 도형 상태 그림 | 아래 상세 명세(3컷) | 07회차 PTE·mem_map 도식 언어 |
| 22 | try_to_share 공유 그림 | 도형 | 두 태스크의 PTE(5,5)가 하나의 물리 페이지를 가리키고 `mem_map[]++`로 count+1 | 07회차 도식 언어 |
| 24 | do_no_page 디스크 갈래 페이지 레이아웃 | 도형 | 헤더 1블록 건너뜀(`block = 1 + tmp/BLOCK_SIZE`), a.out 블록 4개(1024×4) + `end_data` 넘는 꼬리 0(bss) | — |
| 26 | 상태 변화도 ① (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(상태 4 + 전환 6) | — |
| 27 | 상태 변화도 ② (핵심) | 표 + 도형 | 아래 상세 명세(3자 4열×4행) | — |
| 41 | 질문의 답 그림 | 도형 | 부모 PTE=A(5)·자식 PTE=A(5)에서 자식만 B(7)로 분리된 최종 컷 — 16장 그림 축약 재활용 | 16장(동일 시각 언어) |

핵심 시각자료 상세 명세 — "공유 읽기 전용 페이지 → 쓰기 폴트 → 분리" 상태 변화도 (슬라이드 16·26·27이 같은 시각 언어를 공유):

- 공통 시각 언어: 물리 페이지는 상자, PTE는 "A(하위 5)" 형태 라벨(프레임 주소 + PTE 하위 비트), `mem_map` 카운트는 페이지 상자의 배지. 공유 상태 TEAL, 오늘의 전환(쓰기 폴트→분리) ORANGE, 부재·과거 MUTED. 우하단 `Linux 0.11` 라벨.
- 슬라이드 16 (3컷): (1) 복사 전 — 부모 PTE=A(5), 자식 PTE=A(5), 같은 물리 페이지 A, 배지 `mem_map[A]=2`. (2) 자식 쓰기 폴트 — CR2·에러 코드(W=1, P=1) 화살표가 자식 PTE에 닿고 un_wp_page (b)갈래: 새 페이지 B 할당, `copy_page(A,B)` 화살표, 자식 PTE=B(7), 배지 `mem_map[A]=1`·`mem_map[B]=1`. (3) 부모 쓰기 폴트 — un_wp_page (a)갈래: A(5) → A(7) 제자리 승격, 복사 없음(점선 표시).
- 슬라이드 26 (상태 노드 4개 + 전환 6개): 노드 — `부재(0)` / `단독 RW(7, count 1)` / `공유 RO(5, count≥2)` / `RO지만 단독(5, count 1)`. 전환 화살표마다 원인 라벨 — put_page(부재→7), copy_page_tables·try_to_share(7→5, count+1), 쓰기 폴트 un_wp_page(b)(공유 5→새 7, 상대 count-1), un_wp_page(a)(단독 5→7), free_page_tables(→부재). 하단 표: 전환별 변경 데이터(PTE 1개 + `mem_map` 1~2바이트 + 복사 시 4KB 페이지 내용)와 유지 조건(PTE 수 = count).
- 슬라이드 27 (3자 표): 열 4개 — 부모 PTE / 자식 PTE / 물리 페이지 A count / 물리 페이지 B count. 행 4개 — fork 전 (7,—,1,—) / fork 후 (5,5,2,—) / 자식 쓰기 폴트 (5,7→B,1,1) / 부모 쓰기 폴트 (7,7→B,1,1, (a)갈래 복사 없음). 각 행 왼쪽에 전환 원인 줄 번호(mm/memory.c:177·180·183 / 226-237 / 226-229). 캡처 슬라이드 34·36·38·39가 이 표의 해당 행을 재지시한다.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/08-page-fault-cow/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A-1 | 01-un-wp-page-before.png | `b un_wp_page` · 셸 `ls` · `p current->pid` · `bt` · `p/x *table_entry` · `p mem_map[(A-0x100000)>>12]` | PTE 하위 5(P+US, RW=0), `mem_map`=2, backtrace `un_wp_page ← do_wp_page ← page_fault` | 같은 절차 사전 캡처(각주 "lab 빌드, 수정 없음, 값은 부팅마다 다름") |
| A-2 | 02-un-wp-page-after.png | `finish` 후 PTE 재조회 · `p mem_map[(A-0x100000)>>12]` · `p mem_map[(B-0x100000)>>12]` · `x/4wx A` · `x/4wx B` | PTE 하위 7, B≠A, count 1/1, A·B 내용 동일(복사 직후) | 사전 캡처 |
| A-2 보강 | 03-un-wp-page-promote.png | `c` → 다음 정지 · `p/x *table_entry` · `p mem_map[...]` · `finish` | 상대 태스크 (a)갈래: 하위 5 → 7 제자리 승격, 복사 없음 | 사전 캡처 |
| B 코드 페이지 | 04-do-no-page-code.png | `b do_no_page` · 셸 새 명령 `ls` · `p/x address` · `p address - current->start_code` · `p error_code` · `p current->executable->i_num` · `finish` 후 `x/8xb address` | 엔트리 페이지(오프셋 0), `error_code` 4 또는 6, finish 후 PTE 7·코드 바이트 | 사전 캡처 2장 중 코드 페이지 |
| B 스택 페이지 | 05-do-no-page-stack.png | `c` → 다음 정지 · `p/x address` · `p/x current->start_code` | 64MB 칸 끝 근처 주소, `tmp >= end_data` 갈래 | 사전 캡처 중 스택 페이지 |
| C(선택) | 06-write-verify-bt.png | `b write_verify` · 셸 `cat` 후 한 줄 입력 · `bt` | `verify_area ← sys_read ← system_call` | 사전 캡처 1장 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜`(00-common §7).

## 6. 이해 확인 질문과 정답

질문은 슬라이드 44, 정답은 슬라이드 45에 게시(원문 계승).

1. **Q.** `page.s`는 에러 코드의 어느 비트만 보고 핸들러를 고르는가? W 비트는 어디서 쓰이는가?
   **A.** bit0 P만 (`testl $1,%eax`, page.s:28). W/U 비트는 0.11 핸들러가 쓰지 않는다. do_wp_page는 "present인데 폴트" = 쓰기 보호 위반으로 가정한다.
2. **Q.** `un_wp_page`가 복사 없이 `|= 2`만 하는 경우는 언제인가?
   **A.** 페이지가 LOW_MEM 이상이고 `mem_map[]==1`일 때(memory.c:226-229). 상대 태스크가 이미 자기 복사본으로 갈아탔거나, 공유가 끝난 경우.
3. **Q.** `read(fd, buf, n)`에서 buf가 fork로 공유 중인 페이지에 있으면 커널은 어떻게 부모 페이지를 보호하는가?
   **A.** 386은 ring 0 쓰기에 R/W 비트를 적용하지 않으므로 폴트가 나지 않는다. `sys_read`가 먼저 `verify_area(buf,count)`(read_write.c:64) → `write_verify` → `un_wp_page`로 미리 분리한다.
4. **Q.** exec 직후 프로그램의 첫 명령 페이지는 메모리에 있는가? 없다면 누가 언제 채우는가?
   **A.** 없다. 첫 명령 fetch가 부재 폴트(P=0)를 내고 `do_no_page`가 `bmap`/`bread_page`로 a.out 블록 4개를 읽어 `put_page`한다(memory.c:380-394).

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 페이지 폴트(#PF, 벡터 14) | 페이지 부재 또는 보호 위반 시 발생하는 예외(IDT 벡터 14) | 06 |
| CR2 | 폴트를 낸 선형 주소를 담는 CPU 레지스터 | 07 |
| 에러 코드 P/W/U | 폴트 원인 3비트: P(부재/보호), W(쓰기), U(사용자 모드) | 08 |
| 쓰기 보호 폴트 | present인 페이지에 쓰기가 걸려 발생하는 폴트(P=1) | 08 |
| Copy-on-Write(COW) | 첫 쓰기가 일어난 그때 페이지를 복사해 분리하는 기법(제목·부제 "복사하지 않고 복사한 척하기") | 01 |
| 요구 적재(demand loading) | 페이지가 필요해진(부재 폴트) 그때 디스크에서 읽는 방식 | 10 |
| do_no_page | P=0 폴트 처리: 빈 페이지/공유/디스크 세 갈래로 부재 페이지를 채움 | 11 |
| do_wp_page | P=1 쓰기 보호 폴트 처리, PTE 주소를 계산해 un_wp_page 호출 | 11 |
| un_wp_page | mem_map 카운트로 복사/제자리 승격을 판정, 실제 페이지 분리 수행 | 11 |
| write_verify | PTE가 present+non-writable이면 un_wp_page로 선제 분리 | 11 |
| verify_area | 시스템 콜 진입부에서 사용자 버퍼 페이지마다 write_verify 호출 | 11 |
| get_empty_page | get_free_page+put_page로 0으로 채운 새 페이지 확보 | 11 |
| share_page | 같은 executable을 실행 중인 태스크를 찾아 공유 시도 | 11 |
| try_to_share | clean(Dirty=0) 상대 페이지와 양쪽 RW=0으로 공유, `mem_map[]++` | 11 |
| Dirty 비트(PTE bit6) | 페이지에 쓰기가 있었는지 표시하는 PTE 비트(Accessed는 bit5) | 22 |
| oom() | "out of memory" 출력 후 `do_exit(SIGSEGV)` | 20 |
| SIGSEGV | 세그먼테이션 위반 시그널(11) | 20 |
| bmap | 파일 블록 → 디스크 블록 변환(fs/inode.c) | 23 |
| bread_page | 블록 4개를 한 페이지에 읽음(fs/buffer.c) | 11(함수 지도)·본문 24 |
| BLOCK_SIZE(1024) | Linux 0.11의 블록 크기 | 23 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- "fork가 메모리를 복사한다"고 말하지 않는다. fork는 PTE를 복사하고, 데이터 페이지 복사는 첫 쓰기 폴트 때 `un_wp_page`가 한다.
- "부모는 원본, 자식은 복사본"이라고 단정하지 않는다. 먼저 쓰는 쪽이 새 페이지를 받는다(스케줄 순서에 따라 부모가 먼저일 수도 있다). 캡처의 pid로 확인시킨다.
- 에러 코드의 W/U 비트로 0.11이 분기한다고 말하지 않는다. P 비트만 본다.
- "커널이 사용자 페이지에 쓰면 폴트가 나서 COW가 된다"고 말하지 않는다. 386에는 CR0.WP가 없어 폴트가 없고, `verify_area`가 대신한다. 현대 CPU/커널과의 차이는 42장에서 한 줄만.
- `do_wp_page`의 `#if 0` CODE_SPACE를 "코드 영역 쓰기는 막힌다"고 설명하지 않는다. 꺼져 있다(249-254).
- `try_to_share`의 `0x41` 검사에서 bit6을 "Accessed"라고 하지 않는다. Dirty 비트다(Accessed는 bit5).
- `oom()`이 "메모리를 회수한다"고 말하지 않는다. 메시지 출력 후 프로세스를 SIGSEGV로 종료할 뿐이다(memory.c:33-37).
- 시연의 `mem_map` 값·물리 주소는 환경에 따라 달라진다. 캡처 각주에 lab 빌드·수정 여부를 반드시 적는다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 핵심 질문과 지도(로드맵·구조도로 오늘 위치) |
| 05–11 | 17 | 배경: 폴트는 예외다, CR2·에러 코드, 07회차 복습(5와 7, count), 요구 적재 개념 |
| 12–18 | 22 | 코드: traps.c 등록, page.s, do_wp_page, un_wp_page+핵심 그림, write_verify/verify_area, copy_page/invalidate |
| 19–25 | 20 | 코드: do_no_page 세 갈래, get_empty_page, share_page/try_to_share, bread_page·bss 0 채움, 폴트 뒤 재실행 |
| 26–31 | 16 | 상태 변화도 2장 + 비교 3장 + fork 시나리오 표 |
| 32–40 | 25 | 강사 시연 A/B/C(fork 후 첫 쓰기 폴트, mem_map 전후; do_no_page 요구 적재; write_verify) + 캡처 |
| 41–43 | 8 | 질문의 답 + 오늘 코드가 쓰는 데이터 요약 |
| 44–46 | 7 | 이해 확인·정리·예고 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞부분 5, 배경 17, 코드 22+20, 상태도·비교 16, 시연 25, 답 8, 마무리 7.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(40행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07+08(분할) · 원 06→09 · 원 07→10 · 원 08→11 · 원 09→12 · 원 10→13 · 원 11→14 · 원 12→15+16(분할) · 원 13→17 · 원 14→18 · 원 15→19 · 원 16→20 · 원 17→21 · 원 18→22 · 원 19→23+24(분할) · 원 20→25 · 원 21→26 · 원 22→27 · 원 23→28 · 원 24→29 · 원 25→30 · 원 26→31 · 원 27→32 · 원 28→33 · 원 29→34 · 원 30→35 · 원 31→36 · 원 32→37 · 원 33→38+39(분할) · 원 34→40 · 원 35→41 · 원 36→42 · 원 37→43 · 원 38→44 · 원 39→45 · 원 40→46.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| CR2·에러 코드 분할 | 원 05 → 새 07+08 | 레지스터 개념(CR2)과 3비트 표(에러 코드)를 한 장에 담기엔 밀도가 높음 — 각각 그림·표를 확보 (+1) |
| un_wp_page 코드·그림 분할 | 원 12 → 새 15+16 | 00-common §5 우선순위 3(코드+그림 분리) — "공유→쓰기 폴트→분리" 그림이 오늘의 핵심 시각자료이므로 전용 슬라이드 배정 (+1) |
| do_no_page (3/3) 분할 | 원 19 → 새 23+24 | block 계산·bmap×4와 bread_page·bss 0 채움·put_page가 코드 2스크린 분량 (+1) |
| 캡처 B 분할 | 원 33 → 새 38+39 | 코드 페이지(디스크 갈래)·스택 페이지(빈 페이지 갈래) 캡처 2장을 각각 게시 — 비교 ②의 행과 1:1 연결 (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02 "지도"→로드맵/구조, 원 35·36 "정리"→정답, 원 38·39 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 40장 → 46장 (+6) | 목표 범위 44–50 안(00-common §5) |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- 루트 이미지 안 fork-write 테스트 프로그램(08) 준비: 슬라이드 32의 (선택) `cow.c`(전역 변수 쓰기 전후 `getpid`) — 게스트 gcc 유무 확인, 없으면 사전 빌드 바이너리 또는 사전 캡처로 대체 (course-plan "PPTX 제작 전 확인 목록"의 08 해당분).
- lab/ 빌드의 심볼명(`_page_fault` vs `page_fault`, `_do_no_page`/`_do_wp_page`/`_un_wp_page`/`_write_verify`의 `_` 접두 유무)과 줄 번호 확인 — 슬라이드 38·39의 "lab 소스 줄 번호는 src와 다를 수 있음" 각주의 근거 확보.
- QEMU gdbstub에서 `$cr2` 노출 여부(슬라이드 33 시연 A-1) — 안 되면 `up` 후 `p/x address`로 대체 (course-plan 확인 목록의 "$cr3, GDTR 노출 여부" 확인과 동일 계열).
- 사전 캡처 확보: 시연 A 절차 2–7에 해당하는 4장(§5의 01·02·03 + 여유 1장), 시연 B 2장(04·05), 시연 C 1장(06) — 파일명 규칙 `materials/08-page-fault-cow/captures/<두자리순번>-<설명>.png`.
- 07회차 자산 재사용 확인: 슬라이드 05의 fork 직후 PTE·mem_map 그림, 슬라이드 31 예시 수치 표의 07회차 시연 값.
- 캡처 각주에 lab 빌드·수정 여부·캡처 날짜 필수 기재 — `mem_map` 값·물리 주소는 부팅마다 다름(§8 마지막 항목).
