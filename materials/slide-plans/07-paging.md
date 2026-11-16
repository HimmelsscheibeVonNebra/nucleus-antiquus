# 07회차 상세 슬라이드 제작 계획 — 주소 변환과 페이지 관리

- 기준: materials/course-plan.md `# 07. 주소 변환과 페이지 관리` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/07-paging.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 41장 → 이 계획 47장 (+6)
- 로드맵 위치: 파트 C «메모리» · 07/15

## 1. 회차 개요

**핵심 질문**: 같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가?

**학습 목표** (원천 계승):

1. 논리 주소(선택자:오프셋) → 선형 주소 → 물리 주소의 3단계 변환을 Linux 0.11 기준으로 손으로 계산할 수 있다.
2. 0.11이 태스크 번호 `nr`마다 선형 공간을 64MB 단위(`nr * 0x4000000`)로 나누어 쓰는 방식과, 그 값이 LDT 베이스·`start_code`에 어떻게 기록되는지 설명할 수 있다.
3. `boot/head.s`의 `setup_paging`이 만든 페이지 디렉터리·4개 페이지 테이블(16MB identity mapping)과 PTE 하위 비트 P/RW/US의 의미를 읽을 수 있다.
4. `mm/memory.c`의 `mem_map[]`이 물리 페이지 상태(미사용 0 / 사용 중 n / 커널 영역 USED)를 어떻게 추적하며 `get_free_page`·`free_page`·`copy_page_tables`·`put_page`가 그것을 어떻게 바꾸는지 설명할 수 있다.
5. GDB에서 CR3·페이지 디렉터리·페이지 테이블 항목을 직접 덤프해 한 주소를 물리 주소로 변환하고, 두 태스크의 같은 논리 주소가 다른 물리 페이지에 닿는 것을 확인할 수 있다.

**읽을 소스 범위** (파일:줄, 원본 src/ 기준 — 그대로 계승, §2 근거 열의 원천):

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
| mm/memory.c | 197-219 | `put_page`: 디렉터리 항목 없으면 테이블 할당, `page\|7` 기록 |
| mm/memory.c | 399-411 | `mem_init`: 전부 USED로 채운 뒤 `start_mem..end_mem` 범위만 0 |
| mm/memory.c | 413-430 | `calc_mem`: 빈 페이지 수, `pg_dir[i]`별 사용 페이지 수 출력 |

**상태 변화도·비교 범위** (원천 계승):

- 상태 변화도 ①: 물리 페이지 한 장의 상태(`mem_map[n]` 값 기준) — USED(100) / 0 / 1 / ≥2와 전환 원인(`mem_init`, `get_free_page`, `free_page`, `copy_page_tables`, 08회차 `un_wp_page`).
- 상태 변화도 ②: 태스크의 선형 공간 상태 — 생성 전(디렉터리 항목 0) → `copy_mem` 배정 + 테이블 복사(P=1,RW=0) → `put_page` 추가(P=1,RW=1) → `free_page_tables` 해제.
- 비교 ①: 주소의 종류(논리/선형/물리 3가지 전부).
- 비교 ②: PTE 하위 비트 값(`0`, `5`, `7` 전부 — 다른 조합은 0.11이 만들지 않음).
- 비교 ③: 세그먼트 디스크립터 출처(GDT와 LDT 2가지).

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 07. 주소 변환과 페이지 관리 | 표지 | • 대제목 `07. 주소 변환과 페이지 관리` • 부제(핵심 질문 원문 전체): "같은 숫자 주소가 두 프로세스에서 왜 다른 메모리를 가리키는가?" • 보조 한 줄(원 계획 부제 계승): "`int x;` 의 주소 `0x1234`가 셸과 `ls`에서 서로 다른 RAM 셀인 이유" • 우상단 `Linux 0.11` 배지 + `1991`, 회차 정보 `07/15 · 파트 C «메모리»` | — (course-plan 15회차 지도 표 07 행) | 표지 레이아웃(00-common §1·§2) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | • 핵심 질문 1문장 큰 글씨(원문 그대로) • 오늘의 길 = 10단계 미니 지도를 본문 크기로 — 이 회차는 질문·지도·배경·코드·상태도·비교·시연·정답·확인·정리 10단계 전부를 다룸(전 단계 강조, "오늘은 다루지 않음" 없음) • 세 표(LDT, pg_dir, mem_map)가 오늘의 답 재료임을 한 줄로 예고 | — (course-plan 07 절 핵심 질문) | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | • 15회차 7파트 타임라인, 오늘(07) ORANGE 채움 + 굵은 테두리 • 완료 01–06 TEAL, 이후 08–15 MUTED • 오늘 한 줄 문구·06→07·07→08 연결 화살표 문구는 §3 명세 • 파트 C «메모리»(07 주소 변환 · 08 페이지 폴트·CoW)의 첫 회차임을 강조 — 원 지도 슬라이드의 "06(fork)에서 이어지고 08(COW)·09(exec)가 오늘의 표를 그대로 쓴다" 내용 계승 | — (15회차 로드맵, 공통 골격) | 로드맵 다이어그램(§3 명세) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | • 오늘 범위 진한 TEAL: mm/ 상자의 mm/memory.c(오늘의 중심), boot/head.s(setup_paging), include/linux/sched.h(ldt·tss의 cr3) + CR3/pg_dir 연결 라벨 • ORANGE 데이터 흐름 화살표: 논리 주소 → 세그먼트(LDT) → 선형 주소 → 페이지 디렉터리·테이블 → 물리 주소(§3 명세) • 누적 강조(옅은 TEAL) 01–06 영역: boot/*.s·init/main.c·kernel/system_call.s·sched.c·fork.c • 범위 밖 상자는 MUTED 외곽선 실루엣 | mm/memory.c · boot/head.s · include/linux/sched.h (지도 표 07 행 주요 소스) | 구조 다이어그램(§3 명세) |
| 05 | 1회차에서 본 그림을 다시: 주소는 세 번 바뀐다 | 배경 | • 프로그램이 쓰는 숫자 = 논리 주소 — 1회차 15장(선형/물리 구분) 확장 • 세그먼트 베이스를 더한 값 = 선형 주소 • 페이지 표로 찾은 RAM 위치 = 물리 주소 • 오늘의 로드맵: 두 화살표(세그먼트 유닛·페이징 유닛)를 차례로 열어 본다 | include/linux/sched.h:104-106 · boot/head.s:198-219, 234-238 | 세 상자(논리→선형→물리)와 두 화살표 그림(§4) |
| 06 | 1단계: 선택자 0x17이 베이스가 되는 과정 | 배경 | • `0x17` = index 2, TI=1(LDT), RPL=3 • CPU는 현재 LDT의 2번 항목에서 베이스·리밋을 읽는다 • 2회차에서 본 디스크립터 8바이트 그림에 베이스 비트가 흩어져 있는 모습 — `_get_base`가 조립하는 이유 | include/linux/sched.h:104-106, 188-231 · include/linux/head.h:4-9 | 디스크립터 8바이트 베이스 비트 그림(02회차 재사용) |
| 07 | 2단계: 선형 주소 32비트의 분해 | 배경 | • [31:22] 디렉터리 인덱스(10비트) / [21:12] 테이블 인덱스(10비트) / [11:0] 페이지 내 오프셋(12비트) • 예: `0x04001234` → dir 16, table 1, offset 0x234 • 1024×1024×4KB = 4GB 그림 | boot/head.s:198-219 · mm/memory.c:150-189 | 10/10/12 비트 분해 + 4GB 그림(§4) |
| 08 | 2단계 계속: CR3 → 디렉터리 → 테이블 → 페이지 | 배경 | • CR3가 디렉터리 물리 주소 • 디렉터리 항목(PDE)에서 테이블 물리 주소, 테이블 항목(PTE)에서 페이지 물리 주소 • 0.11은 CR3=0 고정(`tss.cr3=&pg_dir`, `pg_dir`=0) • 그림에 "0.11은 디렉터리 하나를 모든 태스크가 공유" 표기 | include/linux/sched.h:113-131 · include/linux/head.h:4-9 · boot/head.s:15-16, 213-219 | CR3→디렉터리→테이블→페이지 그림(§4) |
| 09 | 0.11 소스의 관용구: `(addr>>20)&0xffc`, `(addr>>10)&0xffc` | 배경 | • `>>22`로 인덱스를 구해 `*4`하는 것과 `>>20 & 0xffc`가 같은 값임을 비트 그림으로 • 테이블 쪽도 동일(`>>10 & 0xffc`) • memory.c에서 이 식이 반복됨(115, 160-161, 207, 256-257)을 미리 보여 코드 읽기 부담을 줄인다 | mm/memory.c:115, 160-161, 207, 256-257 | 관용구 비트 동치 그림(§4) |
| 10 | 왜 64MB씩인가: 태스크 번호가 곧 선형 공간 위치 | 배경 | • `nr * 0x4000000`(fork.c:52) • 64MB = 디렉터리 항목 16개 • 태스크 0은 0~64MB(실제 640KB), 1은 64MB~, 2는 128MB~ … 최대 64개 • 그림: 4GB 선형 공간을 64MB 칸으로 나눈 띠 • 오늘 질문의 절반이 여기서 풀린다고 예고 | kernel/fork.c:39-61 · include/linux/sched.h:88 | 4GB 64MB 칸 띠 그림(§4) |
| 11 | 코드: head.s setup_paging (1/2) 테이블 채우기 | 코드 | • `boot/head.s:198-212` 발췌 • `rep stosl`로 5페이지를 0으로 • `_pg_dir`에 `pg0+7`…`pg3+7` • `0xfff007`에서 0x1000씩 빼며 뒤에서부터 PTE 기록 • 결과 그림: pg0[0]=0x000007, pg3[1023]=0xfff007 — 16MB identity mapping | boot/head.s:15-16, 108-124, 198-212 | 코드 발췌 + 16MB identity mapping 결과 그림(§4) |
| 12 | 코드: head.s setup_paging (2/2) 켜기 | 코드 | • `boot/head.s:213-219` 발췌 • `xorl %eax; movl %eax,%cr3` (디렉터리=물리 0) • `orl $0x80000000,%eax; movl %eax,%cr0` • `ret`가 135-141에서 밀어 둔 `_main`으로 간다 • 1회차 27장과 중복이므로 "이제 비트의 의미를 다 안다" 톤으로 짧게 | boot/head.s:135-141, 213-219 | 코드 발췌 |
| 13 | 코드: PTE 한 항목의 비트: P / RW / US | 코드 | • 32비트 PTE 그림: [31:12] 페이지 물리 주소, bit0 P, bit1 R/W, bit2 U/S • `+7` = 111b = 존재·쓰기 가능·사용자 접근 가능 • `&~2`는 R/W만 끈다 • 다음 회차 COW가 이 1비트로 동작한다고 예고 | boot/head.s:198-219 · mm/memory.c:173-189, 197-219 | 32비트 PTE 비트 그림(§4, 08회차 재사용) |
| 14 | 코드: 태스크 0의 LDT — INIT_TASK | 코드 | • `include/linux/sched.h:113-131` 중 ldt 부분 `{0x9f,0xc0fa00}`,`{0x9f,0xc0f200}` 해독 • 베이스 0, 리밋 0x9f(G=1이므로 640KB) • 코드 DPL3(0xfa)·데이터 DPL3(0xf2) • `tss.cr3=&pg_dir` • "태스크 0의 논리 주소 = 선형 주소"인 이유 | include/linux/sched.h:113-131 | 코드 발췌 + 디스크립터 해독 표 |
| 15 | 코드: fork.c copy_mem (1/2) — 자식 칸 배정 계산 | 코드 | • `kernel/fork.c:39-61` 전반 발췌 • `get_limit(0x0f)`/`get_limit(0x17)` — 부모의 코드·데이터 리밋 조사 • `get_base(current->ldt[1])` — 부모 베이스 읽기 • `nr*0x4000000`을 새 코드/데이터 베이스로 계산해 `p->start_code`에 기록 | kernel/fork.c:39-61 · include/linux/sched.h:188-231 | 코드 발췌(원 계획 13장 전반 분할, 사유 §10) |
| 16 | 코드: fork.c copy_mem (2/2) — 베이스 설치와 테이블 복사 | 코드 | • `kernel/fork.c:39-61` 후반 발췌 • `set_base(p->ldt[1])`/`set_base(p->ldt[2])` — 자식 LDT에 새 베이스 설치 • `copy_page_tables(old, new, limit)` 호출 • 실패 시 `free_page_tables`로 되돌림 • 그림: 부모 칸→자식 칸 | kernel/fork.c:39-61 · mm/memory.c:150-189 | 코드 발췌 + 부모 칸→자식 칸 그림(§4) |
| 17 | 코드: 디스크립터에서 베이스 꺼내기/넣기 | 코드 | • `sched.h:188-198`(`_set_base`), `214-226`(`_get_base`), `228-231`(`get_limit`은 `lsll` 명령) • 베이스 32비트가 바이트 2,3,4,7에 흩어진 그림 • 매크로의 `movb`가 그 바이트를 모으는 대응 • 읽기만 하고 암기하지 않는다고 안내 | include/linux/sched.h:188-231 | 코드 발췌 + 베이스 바이트 분산 그림(§4) |
| 18 | 코드: mem_map — 물리 페이지 장부 | 코드 | • `mm/memory.c:43-57` 발췌 • `LOW_MEM 0x100000`, `PAGING_PAGES 3840`(15MB/4KB) • `MAP_NR(addr)=(addr-1MB)>>12`, `USED 100`, `static unsigned char mem_map[3840]` • 1MB 아래는 장부에 없음(커널·BIOS 영역, 공유해도 세지 않음) • 그림: 16MB 물리 메모리 띠와 바이트 배열의 대응 | mm/memory.c:39-57 | 코드 발췌 + 16MB 띠↔mem_map 대응 그림(§4) |
| 19 | 코드: mem_init — 장부 초기화 | 코드 | • `mm/memory.c:399-411` + `init/main.c:112-126` 발췌 • 전부 USED로 채운 뒤 `main_memory_start..memory_end`만 0 • main.c에서 memory_end(최대 16MB)와 buffer_memory_end(1/2/4MB) 결정 • QEMU 기본(16MB)에서 버퍼 4MB → 장부에서 할당 가능한 구간은 4MB~16MB | mm/memory.c:399-411 · init/main.c:112-126 | 코드 발췌 + 16MB 띠에 USED/0 구간 표시 |
| 20 | 코드: get_free_page (1/2) — "첫 번째(사실은 마지막)" 빈 페이지 찾기 | 코드 | • `mm/memory.c:63-83` 인라인 어셈블리 전반을 줄 단위로 • `std; repne scasb`로 mem_map 끝에서 0 탐색 • `movb $1,1(%edi)`로 1 표시 • 찾지 못하면 0 반환 | mm/memory.c:63-83 | 코드 발췌 + mem_map 탐색 방향 표시(원 계획 17장 분할, 사유 §10) |
| 21 | 코드: get_free_page (2/2) — 물리 주소를 만들어 반환 | 코드 | • `mm/memory.c:63-83` 후반 • `sall $12; addl LOW_MEM`으로 물리 주소 계산 • `rep stosl`로 4KB 0 채움 • 반환값은 물리 주소임을 강조 | mm/memory.c:63-83 | 코드 발췌 |
| 22 | 코드: free_page — 감소시키고, 0이면 panic | 코드 | • `mm/memory.c:89-99` 발췌 • `addr<LOW_MEM`이면 무시(커널 영역) • `HIGH_MEMORY` 이상이면 panic • `mem_map[n]--`가 0이 아니면 반환, 이미 0이었으면 "trying to free free page" • 공유 카운트가 여기서 줄어든다 | mm/memory.c:89-99 | 코드 발췌 |
| 23 | 코드: put_page — 선형 주소에 물리 페이지 붙이기 | 코드 | • `mm/memory.c:197-219` 발췌 • `page_table=(address>>20)&0xffc` → PDE 없으면 `get_free_page()`로 테이블 만들고 `\|7`, 있으면 테이블 주소 • `page_table[(address>>12)&0x3ff] = page\|7` • 그림: 디렉터리 항목 생성 분기 • "no need for invalidate" 주석의 이유(새 항목 추가는 TLB에 없던 것) | mm/memory.c:197-219 | 코드 발췌 + 디렉터리 항목 생성 분기 그림(§4) |
| 24 | 코드: copy_page_tables (1/2) — 디렉터리 단위 복사 | 코드 | • `mm/memory.c:150-172` 발췌 • 4MB 정렬 검사, `from_dir/to_dir` 계산 • `to_dir`에 이미 있으면 panic • 새 테이블 `get_free_page()`, `*to_dir = table\|7` • `nr = (from==0)?0xA0:1024` (태스크 0에서 복사할 땐 160페이지=640KB만) | mm/memory.c:150-172 | 코드 발췌 |
| 25 | 코드: copy_page_tables (2/2) — PTE 복사와 공유 카운트 | 코드 | • `mm/memory.c:173-189` 발췌 • `this_page &= ~2`(RW 제거) 후 자식 PTE에 기록 • `this_page > LOW_MEM`이면 부모 PTE도 읽기 전용으로 바꾸고 `mem_map[]++` • 마지막 `invalidate()`(CR3 재적재=TLB 비움) • 그림: 부모/자식 PTE가 같은 물리 페이지를 가리키고 카운트 2 | mm/memory.c:173-189 | 코드 발췌 + 부모/자식 PTE 공유 그림(§4, 08회차 재사용) |
| 26 | 코드: free_page_tables — 4MB 단위로 전부 반납 | 코드 | • `mm/memory.c:105-131` 발췌 • 정렬 검사, `from==0` panic • 디렉터리 항목마다 테이블 1024개 PTE의 페이지 `free_page` • 테이블 페이지 자체도 `free_page`, PDE=0, `invalidate()` • exit(10회차)·exec(09회차)가 호출 | mm/memory.c:105-131 | 코드 발췌 |
| 27 | 상태 변화도 ①: 물리 페이지 한 장의 일생 | 상태도 | • 상태: `USED`(커널/버퍼, 영구) / `0` 미사용 / `1` 단독 소유 / `n≥2` 공유 • 전환: `mem_init`→USED 또는 0, `get_free_page` 0→1, `copy_page_tables` 1→2 (RW=0으로), `free_page` n→n-1, 1→0 • 변경 데이터: `mem_map[MAP_NR]` 바이트 1개 + 해당 PTE • 유지 조건: 카운트는 PTE 개수와 일치해야 하며 1MB 아래는 세지 않음 • (08회차에서 `un_wp_page` 전환 추가 예고) | mm/memory.c:39-57, 63-99, 150-189, 399-411 | 상태 다이어그램(§4) |
| 28 | 상태 변화도 ②: 태스크 선형 공간의 상태 | 상태도 | • 상태: 비어 있음(PDE 16개 모두 0) → 배정됨(`copy_mem`: LDT 베이스=nr×64MB, 테이블 복사, 모든 PTE RW=0) → 사용 중(`put_page`/08회차 폴트로 PTE 추가·RW=1) → 해제됨(`free_page_tables`) • 전환 원인·변경 데이터(ldt[1],ldt[2],start_code,pg_dir[16nr..16nr+15],mem_map) • 호출 순서도가 아니라 상태 표임을 명시 | kernel/fork.c:39-61 · mm/memory.c:105-131, 150-189, 197-219 | 상태 다이어그램(§4) |
| 29 | 비교 ① (1/2): 논리 / 선형 / 물리 주소 — 누가 만들고 어느 표로 | 비교 | • 범위: 한 접근이 거치는 주소 3가지 전부 • 열 "누가 만드나": 컴파일러·링커 / CPU 세그먼트 유닛 / CPU 페이징 유닛 • 열 "변환 표": LDT·GDT / pg_dir+pg_table / 없음 • 표 행 3개(논리·선형·물리)를 읽기 쉽게 앞 축 2개만 배치(분할 사유 §10) | kernel/fork.c:52-55 · boot/head.s:198-212 · mm/memory.c:197-219, 399-411 | 비교표(원 계획 25장 전반 분할) |
| 30 | 비교 ① (2/2): 논리 / 선형 / 물리 주소 — 설정 코드와 GDB | 비교 | • 열 "0.11에서 설정하는 코드": fork.c:52-55 / head.s:198-212·memory.c put_page / mem_init • 열 "GDB에서 보는 법": `p/x current->start_code` / `x/` 선형 / `x/` 물리는 identity 매핑 덕분에 커널 선형으로 읽음 • 시연(슬라이드 34–40)에서 이 열을 그대로 사용한다고 예고 | kernel/fork.c:52-55 · boot/head.s:198-212 · mm/memory.c:197-219, 399-411 | 비교표(원 계획 25장 후반 분할) |
| 31 | 비교 ②: 0.11이 실제로 만드는 PTE 하위 비트 조합 | 비교 | • 범위: PTE 하위 3비트 조합 중 0.11 커널이 생성하는 값 전부 • `0`(부재: free_page_tables, 초기 상태) • `5`=101b(P+US, RW=0: copy_page_tables 173-180 결과, try_to_share) • `7`=111b(P+RW+US: head.s 0xfff007, put_page, un_wp_page) • "US=0(커널 전용) 페이지는 0.11에 없다 — 커널 보호는 세그먼트 DPL이 담당" 명시 • 사용 여부·전환 조건·관련 소스 | mm/memory.c:105-131, 150-189, 197-219 · boot/head.s:198-219 | 비교표 |
| 32 | 비교 ③: 선택자가 참조하는 표 — GDT와 LDT | 비교 | • 범위: CPU가 선택자를 해석할 때 쓰는 표 2개 전부 • GDT: 0x08 커널 코드, 0x10 커널 데이터(베이스 0, 16MB, head.s:234-238) • GDT: `_TSS(n)`/`_LDT(n)`(sched.h:155-156) • LDT: 0x0f 코드, 0x17 데이터(태스크별, 베이스 nr×64MB) • 어느 쪽이 `lldt`로 바뀌는지(switch_to의 ljmp가 TSS의 ldt 필드로 교체) | boot/head.s:234-238 · include/linux/sched.h:153-158 · kernel/sched.c:385-405 | 비교표 |
| 33 | 시연 준비: lab 환경과 심볼 이름 | 시연 | • `lab/`은 yuan-xy 빌드(GNU as)라 심볼에 `_`가 없음(`pg_dir`, `mem_map`, `task`, `current`) • `make debug` → `gdb tools/system` → `target remote :1234` • 캡처 각주 양식: "QEMU i386, lab 빌드, 소스 수정 없음" | — (lab/ 환경 안내, src/ 줄 번호 해당 없음) | 터미널 명령 나열 |
| 34 | 시연 A-1: CR3와 페이지 디렉터리 읽기 | 시연 | • 셸 프롬프트까지 부팅 후 GDB Ctrl-C • `monitor info registers`에서 CR3=00000000, CR0에 PG(0x80000000) 켜짐 (대체: `p/x $cr3`는 gdbstub 버전에 따라 없을 수 있음) • `x/4wx 0` → `0x00001007 0x00002007 0x00003007 0x00004007` 기대 • `x/wx 0x40`(pg_dir[16], 태스크 1)·`x/wx 0x80`(pg_dir[32], 태스크 2)가 0이 아닌 값 | boot/head.s:198-219 (기대값 근거: head.s:203-206) | 시연 절차 슬라이드, 캡처는 슬라이드 35 |
| 35 | 캡처 A-1: info registers / x/4wx 0 | 캡처 | • 실제 GDB 출력 캡처 게시 • 하단 각주: 실행 환경·수정 없음 • 옆에 손 계산: 0x1007 → 테이블 물리 주소 0x1000, 비트 7=P+RW+US • "head.s:203-206의 결과를 지금 눈으로 확인" 표기 | boot/head.s:203-206 | 01-info-registers-cr3.png · 02-x4wx-0-pg-dir.png (§5) |
| 36 | 시연 A-2: 한 주소를 손으로 변환하기 | 시연 | • 대상 태스크 고르기: `p task[2]->pid`, `p/x task[2]->start_code`(기대 0x8000000), `p task[2]->executable->i_num` • 사용자 논리 주소 0 → 선형 0x8000000 → dir 32 → `x/wx 0x80` → 테이블 주소 T → `x/wx T` → PTE → 물리 주소 F • 검증: `x/16xb F` 와 `x/16xb 0x8000000`의 바이트가 같다(둘 다 a.out 텍스트 첫 바이트) | kernel/fork.c:52-53 | 시연 절차 슬라이드, 캡처는 슬라이드 37 |
| 37 | 캡처 A-2: 두 경로로 읽은 같은 16바이트 | 캡처 | • GDB 캡처 2개 나란히(물리 F로 읽은 것, 선형으로 읽은 것) • 각주에 "물리 주소로 읽을 수 있는 이유 = 커널이 0~16MB를 identity 매핑(head.s:198-212)" • 이것은 관찰 결과이고 "같은 내용"은 추론이 아닌 캡처라고 구분 | boot/head.s:198-212 | 03-task2-start-code.png · 04-task2-pde-pte.png · 05-physical-16bytes.png · 06-linear-16bytes.png (§5) |
| 38 | 시연 B: 두 태스크의 같은 논리 주소 비교 | 시연 | • 태스크 1(init: `p/x task[1]->start_code` = 0x4000000, `x/wx 0x40`)과 태스크 2(셸)에 대해 논리 주소 0의 PTE를 각각 구함 • 기대: 태스크 1은 물리 0x0(커널 head.s 코드, copy_page_tables의 `nr=0xA0` 특례로 커널 저지대 공유) • 태스크 2는 ≥ 4MB 영역의 페이지 • "숫자 0이 두 번 나오지만 PTE가 다르다"를 표로 | mm/memory.c:142-148, 150-189 (177 `&~2`) | 시연 절차 슬라이드, 캡처는 슬라이드 39 |
| 39 | 캡처 B: 태스크 1 vs 태스크 2 PTE | 캡처 | • 두 PTE 캡처와 `mem_map` 조회: `p mem_map[(F-0x100000)>>12]`(셸 페이지 기대 1 또는 공유 시 ≥2) • 태스크 1 페이지는 <LOW_MEM이라 장부에 없음(`free_page`가 무시하는 이유) • 각주: 관찰값은 부팅 시점마다 다를 수 있음 | mm/memory.c:89-99, 150-189 | 08-task1-pde-pte.png · 09-kernel-first-bytes.png · 10-task1-linear-first-bytes.png · 07-mem-map-lookup.png (§5) |
| 40 | 시연 C(선택): calc_mem 호출로 장부 요약 보기 | 시연 | • `call calc_mem()` → 콘솔에 "N pages free (of 3840)", "Pg-dir[16] uses k pages", "Pg-dir[32] uses k pages" • 실패(함수 호출 중 트랩)하면 사전 캡처로 대체 • 기대: 태스크마다 디렉터리 인덱스 16·32·48…에만 항목이 있음 = 64MB 간격 | mm/memory.c:413-430 | 시연 절차 슬라이드 + 11-calc-mem-output.png (§5) |
| 41 | 관찰 vs 추론 — 오늘 시연에서 무엇을 직접 보았나 | 시연 | • 관찰(캡처): CR3=0·PG 켜짐, pg_dir[0..3]=`0x00001007`…`0x00004007`, 두 경로의 같은 16바이트, 태스크 1·2의 서로 다른 PTE • 추론(소스 읽기): 그 값들이 head.s:198-219·fork.c:39-61·memory.c:150-189의 결과라는 대응 • 유의: PTE 값·mem_map 값은 부팅마다 달라질 수 있다 — 슬라이드 기대값은 "형태"(00-common §7 구분 규칙) | boot/head.s:198-219 · kernel/fork.c:39-61 · mm/memory.c:150-189 | 관찰/추론 2열 정리표(신설, 사유 §10) |
| 42 | 질문의 답 (1): 선택자는 같아도 LDT가 다르다 | 정답 | • 두 프로세스 모두 CS=0x0f, DS=0x17이지만 `lldt`로 걸린 LDT가 다르고 그 베이스가 nr×64MB로 다르다 → 선형 주소부터 다르다 • 그림: 같은 0x1234가 0x4001234와 0x8001234로 갈라짐 | kernel/fork.c:39-61 · include/linux/sched.h:104-106, 153-158 | 0x1234 갈라짐 그림(§4) |
| 43 | 질문의 답 (2): 선형이 달라서 PDE/PTE도 다르다 | 정답 | • 디렉터리 인덱스 16과 32는 서로 다른 페이지 테이블 → 서로 다른 물리 페이지 • 단, fork 직후엔 같은 물리 페이지를 RW=0으로 공유(카운트 2) — "다른 메모리"가 되는 순간은 08회차 • 현대 리눅스는 LDT 대신 프로세스마다 CR3(디렉터리)를 바꾼다는 한 줄 대비 | mm/memory.c:150-189 | 요약 도식 |
| 44 | 오늘 코드가 쓰는 데이터 한 장 요약 | 정리 | • `ldt[1..2]`(베이스/리밋), `start_code`, `pg_dir[1024]`(물리 0) • 페이지 테이블(물리 0x1000~0x4000 + get_free_page로 만든 것), `mem_map[3840]`, `HIGH_MEMORY` • 어느 함수가 어느 데이터를 쓰는지 교차표 | include/linux/head.h:4-9 · include/linux/sched.h:88, 104-106 · mm/memory.c:39-57 · boot/head.s:15-16, 108-124 | 교차표 |
| 45 | 이해 확인 질문 | 확인 | • §6의 4문항을 먼저 질문만 표시, 클릭 후 정답(슬라이드 46) • 문항 1: 태스크 번호 3의 사용자 논리 주소 `0x1000`은 선형 주소·디렉터리 인덱스가 얼마인가 • 문항 2: `get_free_page()`의 반환값은 선형 주소인가 물리 주소인가 • 문항 3: `copy_page_tables`가 부모 PTE에서도 RW 비트를 끄는 이유와 그 줄은 • 문항 4: `mem_map[]`에 1MB 아래 페이지가 없는데 `free_page(0x5000)`을 부르면 어떻게 되는가 | kernel/fork.c:52 · mm/memory.c:70-71, 91, 177-180 | 4문항 목록 |
| 46 | 이해 확인 정답 | 정답 | • 정답 1: 베이스 3×0x4000000 = 0xC000000, 선형 0xC001000, 디렉터리 인덱스 = 0xC001000>>22 = 48, 테이블 인덱스 1 • 정답 2: 물리 주소(memory.c:70-71 `sall $12; addl LOW_MEM`) — 커널 세그먼트 베이스 0 + 0~16MB identity 매핑 • 정답 3: 둘 중 누가 먼저 쓰든 폴트가 나서 복사(COW) — memory.c:177 `this_page &= ~2`, 180 `*from_page_table = this_page`, 단 LOW_MEM 아래는 제외(179 조건) • 정답 4: `addr < LOW_MEM`이면 그냥 반환(memory.c:91) • 근거 줄 번호를 정답 옆에 표기 | kernel/fork.c:52 · mm/memory.c:70-71, 91, 177-180 | 정답 4항 + 줄 번호 |
| 47 | 정리·다음 회차 예고 | 정리 | • 오늘의 세 표(LDT, pg_dir, mem_map) • 08회차: "fork 뒤 자식이 변수를 바꾸면 부모의 값은 왜 그대로인가?" — 오늘 본 `&~2`와 `mem_map[]++`가 폴트 핸들러에서 어떻게 풀리는지 • 미리 볼 파일: mm/page.s, memory.c 221-272 | mm/page.s · mm/memory.c:221-272 | 3표 미니 다이어그램 + 08 예고 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: C «메모리» (07 주소 변환 · 08 페이지 폴트·CoW) — **파트 C의 첫 회차**. 골격은 00-common §2의 7파트 타임라인.
- 상태: 완료(TEAL 채움) = 01, 02, 03, 04, 05, 06 · 오늘(ORANGE 채움 + 굵은 테두리) = 07 · 이후(MUTED 외곽선) = 08–15.
- 오늘 한 줄 문구(오늘 상자 아래): "논리 → 선형(LDT 베이스) → 물리(페이지 테이블) — 주소 세 단계와 물리 페이지 장부 mem_map".
- 06 → 오늘 연결 화살표 문구: "06: fork가 `copy_mem`·`copy_page_tables`로 무언가를 복사해 두었다 → 07: 그것이 건드린 페이지 디렉터리·테이블 구조를 정면으로 해부한다".
- 오늘 → 08 연결 화살표 문구: "08: 오늘 RW=0(`&~2`)으로 읽기 전용 공유한 페이지에 쓰면 무슨 일이 벌어지는가 — 페이지 폴트".
- 범례(완료/오늘/이후) + 우하단 `Linux 0.11` 라벨.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일·계층(진한 TEAL):
  - mm/ 상자의 **mm/memory.c** — 오늘의 중심(get_free_page·free_page·put_page·copy_page_tables·free_page_tables·mem_map·mem_init·calc_mem).
  - **boot/head.s** — setup_paging이 만든 페이지 디렉터리·테이블과 CR3 적재.
  - **include/linux/sched.h** — `ldt[3]`(104-106)과 `tss`의 cr3 필드(113-131). CR3/pg_dir 라벨을 mm/ 상자와 연결선으로 잇는다.
- 오늘의 데이터 흐름 화살표(ORANGE, 1개): 출발 = 사용자 공간 상자(read()/write() 등 메모리 접근) → 경유 = LDT(include/linux/sched.h)에서 선형 주소 생성 → 페이지 디렉터리·테이블(boot/head.s가 만들고 mm/memory.c가 유지) → 도착 = 하드웨어 라인의 물리 RAM. 라벨: "논리 주소 → 세그먼트(LDT) → 선형 주소 → 페이지 디렉터리·테이블 → 물리 주소".
- 누적 강조(옅은 TEAL, 01–06 영역): boot/bootsect.s·boot/setup.s·boot/head.s(01–03), init/main.c(03), kernel/system_call.s(04), kernel/sched.c(05), kernel/fork.c(06). include/linux/sched.h는 05·06에서 이미 다룬 파일 — 오늘은 ldt/cr3 관점으로 진하게 재강조.
- 계층 경계(CPL=3/0, IRQ) 라벨과 우하단 `Linux 0.11` 라벨 유지, 범위 밖 상자는 MUTED 실루엣.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵 — 파트 C 진입 | 도형 다이어그램 | 7파트 타임라인, 07 ORANGE+굵은 테두리, 완료 01–06 TEAL, 이후 08–15 MUTED, 연결 화살표 2개(§3 문구), 범례·Linux 0.11 라벨 | 공통 골격(00-common §2) 최초 제작, 이후 회차 재사용 |
| 04 | 커널 전체 구조도 — 오늘 범위 | 도형 다이어그램 | mm/memory.c·boot/head.s·include/linux/sched.h 진한 TEAL, 주소 변환 흐름 화살표 ORANGE, 01–06 영역 옅은 TEAL(§3 명세) | 공통 골격(00-common §2) 최초 제작 |
| 05 이후 전 본문 | 상단 미니 지도 띠 | 공통 컴포넌트 | 10단계 띠, 현재 단계 ORANGE 점+라벨(00-common §3) | 전 회차 공통 |
| 05 | 3단계 주소 변환 그림 | 도형 | 논리→선형→물리 세 상자, 세그먼트 유닛·페이징 유닛 화살표 2개 | 01회차 15장 그림 확장 |
| 06 | LDT 디스크립터 베이스 비트 그림 | 도형 | 8바이트 디스크립터에서 베이스 비트가 흩어진 위치, 0x17 선택자 해석 | 02회차 디스크립터 그림 재사용 |
| 07 | 선형 주소 32비트 분해 그림 | 도형 | 10/10/12 비트 3단 분해 + 1024×1024×4KB = 4GB | 신규 |
| 08 | CR3→디렉터리→테이블→페이지 그림 | 도형 | 두 단계 색인 구조, "0.11은 디렉터리 하나를 모든 태스크가 공유" 표기 | 신규 |
| 09 | 관용구 비트 동치 그림 | 도형 | `>>22` 후 `*4`와 `>>20 & 0xffc`의 동치, 테이블 쪽 `>>10 & 0xffc` | 신규 |
| 10 | 4GB 64MB 칸 띠 그림 | 도형 | 태스크 0(0~64MB, 실제 640KB)·1(64MB~)·2(128MB~)… 칸 배정, 디렉터리 항목 16개 눈금 | 신규 |
| 11 | 16MB identity mapping 결과 그림 | 도형 | pg_dir[0..3]→pg0~pg3, pg0[0]=0x000007, pg3[1023]=0xfff007 | 01회차 27장(페이징 켜기) 그림 재활용·확장 |
| 13 | 32비트 PTE 비트 그림 | 도형 | [31:12] 페이지 물리 주소, bit0 P, bit1 R/W, bit2 U/S | 신규(08회차 재사용) |
| 16 | 부모 칸→자식 칸 그림 | 도형 | copy_mem의 64MB 칸 배정과 copy_page_tables 호출, 실패 시 free_page_tables | 슬라이드 10 그림 재사용·확장 |
| 17 | 베이스 바이트 분산 그림 | 도형 | 베이스 32비트가 바이트 2,3,4,7에 흩어진 모습과 매크로 movb의 대응 | 02회차 재사용 |
| 18 | 16MB 띠 ↔ mem_map 대응 그림 | 도형 | 16MB 물리 메모리 띠와 mem_map[3840] 바이트 배열 인덱스 대응, 1MB 아래 제외 표시 | 슬라이드 10 그림 변형 |
| 23 | 디렉터리 항목 생성 분기 그림 | 도형 | put_page의 PDE 없음→get_free_page+`\|7` / 있음→테이블 재사용 분기 | 신규 |
| 25 | 부모/자식 PTE 공유 그림 | 도형 | 두 PTE가 같은 물리 페이지를 가리키고 mem_map 카운트 2, 양쪽 RW=0 | 신규(08회차 재사용) |
| 27 | 물리 페이지 상태 변화도 | 도형 상태 다이어그램 | USED/0/1/n≥2 상자와 mem_init·get_free_page·copy_page_tables·free_page 전환 화살표, 유지 조건 각주 | 신규 |
| 28 | 태스크 선형 공간 상태 변화도 | 도형 상태 다이어그램 | 비어 있음→배정됨→사용 중→해제됨, 전환 원인·변경 데이터(ldt[1],ldt[2],start_code,pg_dir[16nr..16nr+15],mem_map) | 신규 |
| 42 | 0x1234 갈라짐 그림 | 도형 | 같은 논리 0x1234가 0x4001234와 0x8001234로 분기 | 슬라이드 10 그림 재사용 |

## 5. 캡처 목록 (강사 시연)

캡처 보관처: `materials/07-paging/captures/` (두 자리 순번-설명.png). 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜`. 사전 캡처는 모서리에 `기존 기록` 라벨. 중단점은 전 시연 공통 "없음(정지 상태 관찰)" — 셸 프롬프트까지 부팅 후 GDB Ctrl-C.

| 시연 | 캡처 파일 (materials/07-paging/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A-1 (슬라이드 34–35) | 01-info-registers-cr3.png | `monitor info registers` (중단점 없음, Ctrl-C 후) | CR3=00000000, CR0에 PG(0x80000000) 켜짐. `p/x $cr3`는 gdbstub 버전에 따라 없을 수 있음 | 동일 파일명 사전 캡처(`기존 기록` 라벨) |
| A-1 (슬라이드 34–35) | 02-x4wx-0-pg-dir.png | `x/4wx 0` | `0x00001007 0x00002007 0x00003007 0x00004007` (head.s:203-206) + `x/wx 0x40`·`x/wx 0x80`이 0이 아닌 값 | 사전 캡처 |
| A-2 (슬라이드 36–37) | 03-task2-start-code.png | `p task[2]->pid`, `p/x task[2]->start_code` | start_code 기대 0x8000000 (fork.c:52-53). 셸이 task[2]가 아니면 `p *task[1]@6` 식으로 executable != 0인 슬롯 탐색 | 사전 캡처 |
| A-2 (슬라이드 36–37) | 04-task2-pde-pte.png | `x/wx 0x80`, `x/wx T` (T = PDE 값 & 0xfffff000) | 태스크 2 PDE(값 끝이 7), 논리 주소 0의 PTE → 물리 주소 F = 값 & 0xfffff000, 하위 비트 5 또는 7(공유 여부) | 사전 캡처 |
| A-2 (슬라이드 37) | 05-physical-16bytes.png | `x/16xb F` | 물리 경로로 읽은 16바이트(a.out 텍스트 첫 바이트) | 사전 캡처 |
| A-2 (슬라이드 37) | 06-linear-16bytes.png | `x/16xb 0x8000000` | 선형 경로로 읽은 16바이트 — 05와 같은 바이트열 | 사전 캡처 |
| A-2 (슬라이드 39 재사용) | 07-mem-map-lookup.png | `p mem_map[(F-0x100000)>>12]` | 1(단독) 또는 2 이상(같은 실행 파일을 다른 태스크가 공유 중) | 사전 캡처 |
| B (슬라이드 38–39) | 08-task1-pde-pte.png | `p/x task[1]->start_code`, `x/wx 0x40`, `x/wx T1` | start_code=0x4000000, 태스크 1 논리 0 PTE 기대 물리 0x00000000 하위 비트 5 (memory.c:177 `&~2`) | 사전 캡처 2장 |
| B (슬라이드 39) | 09-kernel-first-bytes.png | `x/8xb 0` | 커널 head.s 첫 바이트 `movl $0x10,%eax` = `b8 10 00 00 00` | 사전 캡처 |
| B (슬라이드 39) | 10-task1-linear-first-bytes.png | `x/8xb 0x4000000` | 태스크 1 논리 주소 0의 바이트열이 09와 같은지 — 커널 저지대 공유(1MB 아래라 mem_map 미집계) | 사전 캡처 |
| C (슬라이드 40) | 11-calc-mem-output.png | `call calc_mem()` (실패 시 Ctrl-C 후 `return`) | `NNNN pages free (of 3840)`, `Pg-dir[16] uses k pages`, `Pg-dir[32] uses k pages` … 인덱스는 16의 배수만 | 사전 캡처 |

시연 A의 전체 대체 자료는 위 1~7의 사전 캡처 PNG 7장(각주: QEMU i386 TCG, lab 빌드, 수정 없음), 시연 B는 사전 캡처 2장(08·09/10 병합 분량), 시연 C는 11로 대체한다(원천 강사 시연 절 계승).

## 6. 이해 확인 질문과 정답 (해당 슬라이드 번호 명시)

질문은 슬라이드 45, 정답은 슬라이드 46에 게시.

1. **Q.** 태스크 번호 3의 사용자 논리 주소 `0x1000`은 선형 주소 얼마인가? 디렉터리 인덱스는?
   **A.** 베이스 3×0x4000000 = 0xC000000, 선형 0xC001000. 디렉터리 인덱스 = 0xC001000>>22 = 48, 테이블 인덱스 1. (fork.c:52, 슬라이드 07·10)
2. **Q.** `get_free_page()`의 반환값은 선형 주소인가 물리 주소인가? 커널이 그 값을 바로 포인터처럼 쓸 수 있는 이유는?
   **A.** 물리 주소(memory.c:70-71 `sall $12; addl LOW_MEM`). 커널 세그먼트 베이스가 0이고 0~16MB가 identity 매핑이라 선형=물리로 바로 접근 가능.
3. **Q.** `copy_page_tables`가 자식 PTE뿐 아니라 부모 PTE에서도 RW 비트를 끄는 이유는? 어느 줄인가?
   **A.** 둘 중 누가 먼저 쓰든 폴트가 나서 복사(COW)가 일어나게 하려고. memory.c:177 `this_page &= ~2`, 180 `*from_page_table = this_page`. 단 LOW_MEM 아래 페이지는 부모 쪽을 바꾸지 않는다(179 조건).
4. **Q.** `mem_map[]`에 1MB 아래 페이지가 없는데, `free_page(0x5000)`을 부르면 어떻게 되는가?
   **A.** `addr < LOW_MEM`이면 그냥 반환(memory.c:91). 커널·BIOS 영역은 장부 밖이고 해제되지 않는다.

## 7. 처음 등장하는 용어 (용어 | 정의 | 첫 등장 슬라이드)

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 논리 주소 / 선형 주소 / 물리 주소 (logical / linear / physical address) | 프로그램이 쓰는 선택자:오프셋 주소 / 세그먼트 베이스를 더한 32비트 주소 / 페이지 표를 거쳐 도달한 실제 RAM 주소 | 05 |
| 페이지 디렉터리(PDE) / 페이지 테이블(PTE) | 선형 주소 상위 10비트·중간 10비트로 색인되는 2단 변환 표와 그 항목들 | 07 |
| CR3 | 페이지 디렉터리의 물리 시작 주소를 담는 레지스터 — 0.11은 0 고정(`tss.cr3=&pg_dir`) | 08 |
| 64MB 태스크 슬롯(`nr * 0x4000000`) / `start_code` | 태스크 번호 nr에 nr*0x4000000 선형 공간을 배정하는 규칙과 그 시작을 기록한 task_struct 필드 | 10 |
| identity mapping | 선형 주소와 물리 주소가 같아지도록 일대일로 연결한 매핑 — head.s가 0~16MB에 생성 | 11 |
| P / R/W / U/S 비트 | PTE 하위 비트 — 존재(bit0), 읽기/쓰기(bit1), 사용자/관리자(bit2) | 13 |
| `mem_map` / `LOW_MEM` / `MAP_NR` / `USED` | 물리 페이지 장부 바이트 배열과 그 기준 — LOW_MEM=1MB(장부 대상 시작), MAP_NR(addr)=(addr-1MB)>>12, USED=100(커널·버퍼 영역 표시) | 18 |
| `get_free_page` | mem_map에서 빈 물리 페이지를 찾아 1로 표시하고 4KB를 0으로 채워 물리 주소로 반환 | 20 |
| `free_page` | mem_map 카운트를 감소 — 이미 0이면 panic("trying to free free page") | 22 |
| `HIGH_MEMORY` | 관리 상한 물리 주소 — 이상을 해제하면 panic | 22 |
| `put_page` | 물리 페이지를 주어진 선형 주소의 PTE에 `page\|7`로 연결 | 23 |
| TLB와 `invalidate()`(CR3 재적재) | 주소 변환 캐시(TLB)를 CR3 재적재로 비우는 memory.c 매크로 — 캐시 전체가 아님 | 23 |
| `copy_page_tables` | 디렉터리 단위로 페이지 테이블만 복사해 부모·자식이 물리 페이지를 RW=0으로 공유 | 24 |
| `free_page_tables` | 4MB 단위로 테이블 내 모든 PTE의 페이지와 테이블 페이지 자체를 반납 | 26 |

## 8. 흔한 오해 / 말하지 말아야 할 것

- "0.11도 프로세스마다 페이지 디렉터리를 바꾼다"고 말하지 않는다. 0.11은 CR3=0 하나를 전 태스크가 공유하고 LDT 베이스(64MB 칸)로 구분한다. 현대 리눅스와의 차이는 슬라이드 43에서 한 줄만.
- `get_free_page`가 주는 값을 "가상 주소"라고 부르지 않는다. 물리 주소이며, 커널이 바로 접근하는 것은 identity 매핑 때문이다.
- `mem_map` 카운트가 "참조 중인 프로세스 수"라고 단정하지 않는다. 정확히는 그 물리 페이지를 가리키는 PTE 수(1MB 이상 영역에 한함)다.
- `copy_page_tables`가 "메모리를 복사한다"고 말하지 않는다. 복사되는 것은 페이지 테이블(PTE)뿐이고 데이터 페이지는 공유된다. 실제 복사는 08회차의 `un_wp_page`.
- 태스크 0의 리밋 640KB와 `copy_page_tables`의 `nr=0xA0` 특례를 "버그"라고 하지 않는다. 의도된 설계(memory.c:142-148 주석).
- `invalidate()`를 "캐시 비우기"라고 하지 않는다. TLB(주소 변환 캐시)만 비운다.
- 시연 캡처의 PTE 값·mem_map 값은 부팅마다 달라질 수 있다. 슬라이드의 기대값은 "형태"이고, 구체 숫자는 캡처에 있는 것을 읽는다.

## 9. 120분 운영안 (새 슬라이드 번호: 범위 | 분 | 진행)

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 5 | 표지·핵심 질문, 로드맵(파트 C 진입)·구조도로 오늘 범위 확인 |
| 05–10 | 18 | 배경: 3단계 주소, 선택자→베이스(LDT), 선형 주소 비트 분해, 페이지 디렉터리/테이블 |
| 11–17 | 20 | 코드: head.s setup_paging, PTE 비트, 64MB 분할(copy_mem), INIT_TASK/LDT 디스크립터 |
| 18–26 | 22 | 코드: mem_map, mem_init, get_free_page, free_page, put_page, copy_page_tables, free_page_tables |
| 27–32 | 15 | 상태 변화도 2장 + 비교 3종(논리/선형/물리는 2장 분할) |
| 33–41 | 25 | 강사 시연 A/B/C (CR3·pg_dir 덤프, 손 변환, 두 태스크 비교) + 캡처 해설 + 관찰 vs 추론 |
| 42–44 | 8 | 질문의 답: 같은 주소가 왜 다른 메모리인가 (2단 설명) + 데이터 요약 |
| 45–47 | 7 | 이해 확인 질문·정답, 정리·다음 회차 예고 |

단계별 분 배분(5+18+20+22+15+25+8+7=120)은 원진 유지, 슬라이드 범위만 새 번호로 갱신.

## 10. 기존 계획 대비 변경·증가

총 41장 → 47장 (+6). 증가 내역 (00-common §5 우선순위 순):

1. **표준 앞부분 확장 (+2)** — 기존 "01 제목 + 02 지도" 2장을 00-common §2 표준 앞부분 4장(표지/질문/로드맵/구조)으로. 기존 "지도" 슬라이드는 슬라이드 03 로드맵 다이어그램으로 대체·흡수하며, 그 내용(06 fork에서 이어짐, 08 COW·09 exec가 오늘의 표를 그대로 씀, 상단 미니 지도 안내)은 §3 연결 화살표 문구와 슬라이드 02로 계승.
2. **copy_mem 분할 (+1, 슬라이드 15–16)** — `kernel/fork.c:39-61` 전체 인용 + 부모 칸→자식 칸 그림이 한 장에 2스크린 이상.
3. **get_free_page 분할 (+1, 슬라이드 20–21)** — 인라인 어셈블리 줄 단위 해설(scasb 탐색 ~ 물리 주소 계산·0 채움)이 밀도 높음.
4. **비교 ① 분할 (+1, 슬라이드 29–30)** — 비교 축 4개(누가 만드나/변환 표/설정 코드/GDB 보는 법)로 00-common §5의 "축 3개 이상" 분할 기준에 해당.
5. **관찰 vs 추론 구분 슬라이드 신설 (+1, 슬라이드 41)** — 00-common §7 "시연 뒤 관찰 vs 추론 구분 슬라이드 1장" 규정. 기존 계획에는 캡처 슬라이드 각주(원 32장)에만 묻어 있던 내용을 독립 슬라이드로.

유형 어휘 갱신 (내용 변화 없음, 00-common §3 어휘로 명칭만 정리): 원 "제목"→표지, 원 "지도"→로드맵(흡수), 원 "정리"(질문의 답 1·2)→정답, 원 "질문"(이해 확인)→확인/정답.

계승 대응 (원천 슬라이드 표 41행 전부 계승, 누락 없음): 원 01→01 · 원 02(지도)→03 흡수 · 원 03–12→05–14 · 원 13→15–16(분할) · 원 14→17 · 원 15–16→18–19 · 원 17→20–21(분할) · 원 18–22→22–26 · 원 23–24→27–28 · 원 25→29–30(분할) · 원 26–27→31–32 · 원 28–35→33–40 · 원 36–41→42–47. 신규 슬라이드: 02, 04, 41.

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- `lab/` 빌드의 심볼명·줄 번호 확인: yuan-xy 빌드(GNU as)라 심볼에 `_`가 없음(`pg_dir`, `mem_map`, `task`, `current`) — 슬라이드 33 안내·§5 캡처 각주와 실제 빌드가 일치하는지 제작 시점 재검증. 코드 캡션은 원본 `src/` 줄 번호 그대로, `lab/` 캡처 병치 시 "lab/ 수정본(심볼 `_` 접두 등 차이)" 각주.
- QEMU gdbstub에서 `$cr3`, GDTR 노출 여부 — 안 되면 `monitor info registers`로 대체 (시연 A-1·§5 01번 캡처, 원천도 "`p/x $cr3`는 gdbstub 버전에 따라 없을 수 있음" 명시).
- 사전 캡처 확보 점검: `materials/07-paging/captures/`에 §5의 11종(01–11)이 두 자리 순번-설명.png 규칙으로 존재하는지 — 없는 항목은 시연 전 날 확보 후 `기존 기록` 라벨.
- 시연 기대값은 "형태"임을 슬라이드에 명시 (§8 오해 항목): PTE 값·mem_map 값은 부팅마다 달라질 수 있음.
- 08회차 연계 자료(루트 이미지 fork-write 테스트 프로그램 등)는 07 제작 범위 밖 — 슬라이드 47 예고 문구만 원천 그대로 유지.
