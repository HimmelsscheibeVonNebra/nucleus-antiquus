# 11회차 상세 슬라이드 제작 계획 — 버퍼 캐시와 블록 장치

- 기준: materials/course-plan.md `# 11. 버퍼 캐시와 블록 장치` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/11-buffer-cache.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 38장 → 이 계획 46장 (+8)
- 로드맵 위치: 파트 E «파일·저장» · 11/15

## 1. 회차 개요

- 핵심 질문: **read()가 디스크에 실제로 접근하는 때는 언제인가?**
- 학습 목표 (course-plan 원문 계승):
  1. 파일 시스템이 디스크를 직접 읽지 않고 항상 `bread()` → `getblk()`를 거쳐 **버퍼 캐시**를 통과하며, 실제 디스크 접근은 `b_uptodate==0`일 때만 `ll_rw_block()`으로 일어남을 코드로 보일 수 있다.
  2. `struct buffer_head`의 네 플래그 `b_uptodate`/`b_dirt`/`b_lock`/`b_count`가 각각 누구에 의해 언제 바뀌는지 상태 변화도로 설명할 수 있다.
  3. 요청(`struct request`)이 `make_request` → `add_request`에서 어떻게 큐에 들어가고(`IN_ORDER` 엘리베이터), `do_hd_request`가 어떻게 컨트롤러에 명령을 내리며, `hd_interrupt` → `read_intr`가 어떻게 데이터를 옮기고 `end_request`로 버퍼를 깨우는지 호출 순서로 추적할 수 있다.
  4. 동기화 지점(`wait_on_buffer`, `lock_buffer`, `sleep_on`/`wake_up`)이 "인터럽트는 데이터만 바꾸고 플래그는 호출자가 바꾼다"는 원칙(`buffer.c:7–13`)으로 어떻게 배치되었는지 말할 수 있다.
  5. 읽기 요청 종류(READ/READA/WRITE/WRITEA)와 큐 삽입 정책의 선택지를 범위 안에서 빠짐없이 비교할 수 있다.
- 읽을 소스 범위 (원본 src 기준 — course-plan 원문 계승):

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

- 상태 변화도·비교 범위 (course-plan 원문 계승, 이 계획의 슬라이드 번호 연결):
  - 상태 변화도 ① buffer_head 한 개 — 상태를 (`b_uptodate`, `b_dirt`, `b_lock`, `b_count`) 4-튜플로 본다. 주요 상태: `free`(0,0,0,0, `b_dev=0`) → `claimed`(0,0,0,1; `getblk` 243–249) → `reading`(0,0,1,1; `make_request:105`) → `uptodate`(1,0,0,1; `end_request:113–114`) → `dirty`(1,1,0,n; `file_write` 등이 `b_dirt=1`) → `writing`(1,0,1,n; `add_request:71`이 `b_dirt=0`, `lock_buffer`) → `released`(1,0,0,0; `brelse:258`) → 재사용 시 `getblk`가 `BADNESS` 최소 버퍼 선택. 전환 원인·변경 데이터·유지 조건을 각 화살표에 적는다. → **슬라이드 16**
  - 상태 변화도 ② request 한 개 — `dev=-1`(빈 슬롯) → 채워짐(`make_request:133–141`) → 큐 삽입/즉시 실행(`add_request`) → `CURRENT`(컨트롤러 명령 발행) → 섹터별 인터럽트로 `nr_sectors` 감소 → `end_request`가 `dev=-1`, `CURRENT=next`. → **슬라이드 33(신규)**
  - 비교 ① `ll_rw_block`의 `rw` 값 전부 — `READ`/`WRITE`/`READA`/`WRITEA`(`fs.h:26–29`). 잠긴 버퍼 처리, 큐 부족 시 동작, 호출처. → **슬라이드 25**
  - 비교 ② `add_request`가 새 요청을 넣을 수 있는 자리 전부 — (a) 큐 비어 있음 → 즉시 `request_fn` 호출, (b) `IN_ORDER` 조건을 만족하는 중간 자리, (c) 꼬리. `IN_ORDER`의 세 비교 키(cmd, dev, sector)와 READ 우선 규칙. → **슬라이드 27**
  - 비교 ③ `make_request`가 요청 슬롯을 찾는 시작점 — READ는 `request+NR_REQUEST`(32개 전부), WRITE는 `request+21`(앞 2/3)만. → **슬라이드 24(코드)와 슬라이드 25 표의 "슬롯 범위" 행으로 흡수**
  - 혼합 금지: 버퍼 상태(플래그)와 요청 큐 정책을 한 슬라이드에 섞지 않는다 — 상태도 ①(16)과 ②(33)를 분리해 유지.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 11. 버퍼 캐시와 블록 장치 | 표지 | 대제목 `11. 버퍼 캐시와 블록 장치` · 부제(핵심 질문 원문): "read()가 디스크에 실제로 접근하는 때는 언제인가?" · 원 계획 부제 문구 계승: "read() 한 번에 디스크는 몇 번 도는가 — 0번, 1번, 그 이상?" · 우상단 `Linux 0.11` 배지 + `1991` · 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `11/15 · 파트 E «파일·저장»` | — | 표지 배지·푸터(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "read()가 디스크에 실제로 접근하는 때는 언제인가?" · 길잡이 문구 계승: "read() 한 번에 디스크는 몇 번 도는가 — 0번, 1번, 그 이상?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치, 오늘 실제 다루는 단계만 강조 · 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다름(빠짐없이 강조) | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 E «파일·저장»의 11만 ORANGE 강조 · 완료(TEAL) 01–10, 이후(MUTED) 12–15 · 오늘 한 줄 문구와 10→11·11→12 연결 화살표 문구는 §3 명세 · 원 "지도" 슬라이드 내용 계승: 06~10의 프로세스 축이 끝나고 11(버퍼)·12(파일 시스템)·13(tty)의 I/O 축이 시작됨 · 12회차의 `namei`가 오늘 `bread`를 부른다는 화살표(11→12 문구에 반영) | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | fs/buffer.c(fs/ 계층)와 kernel/blk_drv/ll_rw_blk.c·kernel/blk_drv/hd.c(blk_drv/ 계층)를 진한 TEAL로 강조 — 오늘은 fs/와 blk_drv/ 두 계층에 걸침 · 오늘의 데이터 흐름 화살표(ORANGE): bread → getblk(히트 시 즉시 반환) → 미스 시 ll_rw_block → do_hd_request·hd_out → 하드웨어(IRQ14) → hd_interrupt → read_intr → end_request → wake_up → 잠든 bread 깨움 · kernel/sched.c의 sleep_on·wake_up(05회차 복습) 경유 표시 · 누적 강조(옅은 TEAL) 01–10 영역은 §3 명세 | fs/buffer.c(§1 읽기 범위) · kernel/blk_drv/ll_rw_blk.c · kernel/blk_drv/hd.c · kernel/system_call.s:221–250 · kernel/sched.c:151–165, 188–194 | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 디스크와 메모리의 속도 차이 | 배경 | 1991년 IDE 디스크 탐색 ms 단위 vs 메모리 ns 단위 · 같은 블록을 읽는 요청은 매우 흔함(디렉터리, inode 블록, 비트맵) · 그래서 "읽은 적 있으면 메모리에서 준다"는 캐시 · 오늘 핵심 질문으로 연결: read()가 매번 디스크에 가는 것은 아니다 | —(배경 개념) | 디스크 탐색 ms vs 메모리 ns 비교 바 |
| 06 | 단위 정리: 섹터, 블록, 장치 번호 | 배경 | 섹터 512B(하드웨어), 블록 1024B = 2섹터(`fs.h:49`, `make_request:136–137`의 `<<1`과 `nr_sectors=2`) · 장치 번호 `MAJOR`/`MINOR`(`fs.h:33–34`), 하드디스크 major 3(`hd.c:25`), 루트 `0x306`(`bootsect.s:43`) = 2번째 드라이브 1번 파티션 · 첫 사용처: `sys_setup`이 파티션 표를 `bread(0x300+drive*5, 0)`로 읽음(`hd.c:71–160`, 135–153) — 버퍼 캐시가 부팅에도 이미 필요 | include/linux/fs.h:33–34, 47–49 · kernel/blk_drv/ll_rw_blk.c:136–137 · kernel/blk_drv/hd.c:25, 71–160 · boot/bootsect.s:43 | 섹터 2개 = 블록 1개 도식 + 0x306 번호 분해 그림(§4) |
| 07 | 메모리 지도에서 버퍼 영역 | 코드 | 커널 `end` ~ `buffer_memory_end`(`init/main.c:117–122`) 사이 — 3회차 메모리 지도 재사용 · `buffer_init`(buffer.c:348–381): 헤더는 `end`에서 위로, 데이터 블록은 끝에서 아래로, 640K~1M 구멍 건너뜀(372–373) · 결과 `NR_BUFFERS` · 초기화 순서: `blk_dev_init` → `buffer_init` → `hd_init` → `sti`(init/main.c:126–137) · 부팅 캡처의 "N buffers = M bytes buffer space" 줄과 연결 | init/main.c:117–122, 126–137 · fs/buffer.c:30–34, 348–381 · include/linux/fs.h:47–49 | 3회차 메모리 지도 재사용 + 버퍼 영역 확대도(§4) · (기존 기록) 부팅 캡처 |
| 08 | struct buffer_head | 코드 | `fs.h:68–81` 전체 · `b_data`(1024B 포인터), `b_blocknr`, `b_dev`, 플래그 4개, `b_wait`(잠든 태스크), 해시 체인 `b_prev/b_next`, free list `b_prev_free/b_next_free` · 다음 장(09)에서 플래그 4개의 뜻, 슬라이드 11에서 링크 4개의 쓰임 | include/linux/fs.h:68–81 · fs/buffer.c:30–34 | 헤더 하나와 그 데이터 블록 그림(§4) |
| 09 | 네 플래그의 뜻 | 배경 | 표로 정리: `b_uptodate` — 데이터가 디스크 내용과 같은가 · `b_dirt` — 메모리가 디스크보다 새로운가 · `b_lock` — I/O 진행 중이라 손대면 안 되는가 · `b_count` — 지금 쓰는 사람 수 · 각각 "누가 1로, 누가 0으로"를 다음 슬라이드들에서 채운다 — 완성형은 상태 변화도 ①(슬라이드 16) | include/linux/fs.h:68–81 · fs/buffer.c:7–13 | 4플래그 × 뜻 × 1로 만드는 주체/0으로 만드는 주체 표 |
| 10 | 두 개의 자료구조: 해시 테이블과 free list — 코드 | 코드 | `buffer.c:128–129` `hash(dev,block) = hash_table[(dev^block)%307]` — `NR_HASH` 307 버킷 · `buffer.c:131–174` `remove_from_queues`/`insert_into_queues`/`find_buffer` · 해시 체인은 "찾기", free list는 "재사용 순서"(LRU 비슷: 삽입은 항상 꼬리) · 그림은 다음 장(11)에서 | fs/buffer.c:30–34, 128–129, 131–174 · include/linux/fs.h:47–49 | 코드 인용 + `hash` 산식 하이라이트 |
| 11 | 그림: 한 버퍼가 두 목록에 산다 — 해시 체인과 free list | 배경 | 307개 버킷의 해시 테이블: 같은 (`dev`,`block`) 버퍼를 버킷 하나의 이중 연결(`b_prev/b_next`)에서 찾음 · 원형 free list: 재사용 후보 순서, 삽입은 항상 꼬리(`insert_into_queues`) · 같은 `buffer_head` 하나가 해시 체인과 free list(`b_prev_free/b_next_free`)에 동시에 연결 · `b_count>0` 버퍼는 free list에 남아 있어도 `getblk`가 건너뜀(슬라이드 13) | fs/buffer.c:128–174, 205–227 · include/linux/fs.h:47–49 | 해시/free list 구조도(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 12 | 코드: bread | 코드 | `buffer.c:267–281` · `getblk`로 헤더 확보 → `b_uptodate`면 즉시 반환(디스크 0번) → 아니면 `ll_rw_block(READ,bh)` + `wait_on_buffer` → 다시 `b_uptodate` 검사 → 실패면 `brelse` 후 NULL · 핵심 질문에 대한 첫 답: "`b_uptodate`가 0일 때만" | fs/buffer.c:267–281 · kernel/blk_drv/ll_rw_blk.c:145–165 | 코드 인용 + 히트/미스 분기 미니 도식 |
| 13 | 코드: getblk 전반부 (찾기와 고르기) | 코드 | `buffer.c:205–227` · `get_hash_table`(183–196: 찾고 `b_count++` 후 `wait_on_buffer`, 깨어난 뒤 재확인) → 없으면 free list 순회에서 `b_count==0` 중 `BADNESS = dirt*2 + lock` 최소 선택, 0이면 즉시 중단 → 하나도 없으면 `sleep_on(&buffer_wait)` | fs/buffer.c:183–196, 205–227 | 코드 인용 + `BADNESS` 공식 하이라이트 |
| 14 | 코드: getblk 후반부 (확정) | 코드 | `buffer.c:228–251` · `wait_on_buffer` → `b_count` 재검사 → `b_dirt`면 `sync_dev` 후 재검사 → 자는 동안 누가 같은 블록을 넣었는지 `find_buffer` 재확인 → `b_count=1, b_dirt=0, b_uptodate=0` → 해시 체인 옮김 · "goto repeat가 네 번"인 이유 = 잠들 때마다 세상이 바뀐다 | fs/buffer.c:228–251 · fs/buffer.c:59–82(sync_dev 호출) | 코드 인용 + `goto repeat` 위치 4곳 표시 |
| 15 | 코드: brelse와 wait_on_buffer | 코드 | `buffer.c:253–261`: `wait_on_buffer` 후 `b_count--`, 0 미만이면 panic, `wake_up(&buffer_wait)` · `buffer.c:36–42`: `cli` → `while(b_lock) sleep_on(&b_wait)` → `sti` · `sleep_on`(`sched.c:151–165`)이 `*p`를 체인으로 쓰는 방식 5회차 복습 | fs/buffer.c:253–261, 36–42 · kernel/sched.c:151–165 | 코드 인용 + `sleep_on` 대기 큐 체인 미니 그림(05회차 재사용) |
| 16 | 상태 변화도 ①: buffer_head 플래그 | 상태도 | 4-튜플 상태도 · free(0,0,0,0) —getblk 243–245→ claimed(0,0,0,1) —make_request 105 lock_buffer→ reading(0,0,1,1) —end_request 113–114→ uptodate(1,0,0,1) —brelse→ cached(1,0,0,0) —getblk 적중→ (1,0,0,1) —쓰기 `b_dirt=1`→ dirty(1,1,0,n) —add_request 71 + lock→ writing(1,0,1,n) —end_request→ (1,0,0,n) · 각 전환에 원인 함수와 바뀌는 필드, 유지 조건(`b_count>0`이면 재사용 대상 아님; `b_lock`이면 플래그 변경 금지) · 4-튜플 값은 코드 추론임을 각주(§8) | fs/buffer.c:205–251, 253–261 · kernel/blk_drv/ll_rw_blk.c:42–57, 64–86, 88–143 · kernel/blk_drv/blk.h:109–125 | 상태 변화도 ①(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 17 | 동기화 원칙: 인터럽트는 데이터만 | 배경 | `buffer.c:7–13` 주석 인용 — "인터럽트는 데이터만 바꾸고 플래그는 호출자가 바꾼다" · 인터럽트 핸들러(`read_intr`)는 `port_read`로 `b_data`만 채우고, 플래그는 `end_request`(인터럽트 문맥이지만 블록 계층의 코드) 한 곳에서만 · `wait_on_buffer`의 `cli/sti`가 필요한 이유: `b_lock` 검사와 `sleep_on` 사이에 인터럽트가 `unlock`하면 영원히 잠듦 | fs/buffer.c:7–13, 36–42 · kernel/blk_drv/hd.c:250–267 · kernel/blk_drv/blk.h:109–125 | 주석 인용 블록 + 검사와 sleep 사이 경쟁 타임라인 미니 그림 |
| 18 | sync: 더러운 버퍼는 언제 디스크로 가는가 | 코드 | `buffer.c:44–57` `sys_sync`(inode 먼저, 전체 버퍼 순회) · `59–82` `sync_dev`(장치 하나, 두 번 순회) · 호출처: `getblk:232`(더러운 버퍼 재사용 전), `iput`(12회차), `sys_umount` · 0.11에는 주기적 flush 데몬이 없다 — 명시 | fs/buffer.c:44–82, 232 | 코드 인용 + 호출처 목록 박스 |
| 19 | bread_page와 breada (참조) | 코드 | `buffer.c:296–315` 4블록 동시 요청 후 대기(9회차 `do_no_page`가 사용) · `322–346` 미리읽기 · `breada:336`의 `ll_rw_block(READA,bh)`가 `tmp`가 아닌 `bh`를 넘기는 원본 그대로의 코드를 보여주고 "원본의 오타로 보이며 lab에서는 수정하지 않았다"고 각주 | fs/buffer.c:296–346 | 코드 인용 + `bh` 전달 부분 하이라이트(원본 소스 사실 — course-plan "원본 소스 사실" 계승) |
| 20 | 시연 A 계획: 같은 블록 두 번 읽기 | 시연 | 중단점 `bread`, `ll_rw_block` · 셸에서 `cat /etc/rc`를 두 번 · 관찰: 첫 번째 `bread`에서 `p bh->b_uptodate`=0 → `ll_rw_block` 진입 · 두 번째는 `getblk` 반환 직후 `b_uptodate`=1 → `ll_rw_block` 미진입, `b_count` 값 · 부팅 직후(캐시가 거의 비어 있음)에서 시작 | fs/buffer.c:267–281 | GDB 명령 블록 · 캡처 01·02·03(§5) |
| 21 | 시연 A 캡처 | 캡처 | GDB 로그 두 묶음(첫 실행/두 번째 실행)과 `info breakpoints`의 hit count 차이 · 기대 출력: 첫 번째 `$ = 0 '\000'` 후 `ll_rw_block` 중단, 두 번째 `$ = 1 '\001'` 후 바로 다음 `bread` · 각주: lab/ QEMU i386 + GDB, 원본 미수정, 부팅 직후 상태(캐시 비어 있음)에서 시작 · "`cat`이 inode·디렉터리 블록도 읽어 `bread` hit가 여러 번"임을 미리 말함 | fs/buffer.c:267–281(관찰 대상) | materials/11-buffer-cache/captures/01·02·03(§5) |
| 22 | 블록 계층의 자료구조 | 코드 | `blk.h:23–33` `struct request`(dev=-1이면 빈 슬롯, sector, nr_sectors, buffer, waiting, bh, next) · `blk.h:45–48` `blk_dev_struct`(request_fn, current_request) · `ll_rw_blk.c:21–40` `request[32]`와 `blk_dev[7]` 초기값 · `hd_init:345`가 `request_fn=do_hd_request` 등록 · 그림: `blk_dev[3].current_request` → 연결 리스트 | kernel/blk_drv/blk.h:15, 23–33, 40–48 · kernel/blk_drv/ll_rw_blk.c:21–40 · kernel/blk_drv/hd.c:343–349 | 코드 인용 + request 큐 구조 그림(§4) |
| 23 | 코드: ll_rw_block과 make_request 전반부 | 코드 | `ll_rw_blk.c:145–155` major 검사 · `88–109`: READA/WRITEA는 잠겨 있으면 포기, `lock_buffer`, 이미 `b_uptodate`(READ)거나 `!b_dirt`(WRITE)면 unlock 후 리턴 — 두 번째 "디스크에 안 가는 지점" | kernel/blk_drv/ll_rw_blk.c:42–57, 88–109, 145–155 | 코드 인용 + 조기 리턴 조건 하이라이트 |
| 24 | 코드: make_request 후반부 (슬롯 찾기) | 코드 | `ll_rw_blk.c:110–143` · READ는 32개 전체, WRITE는 앞 21개에서 역순으로 `dev<0` 탐색 · 없으면 READA/WRITEA는 포기, 아니면 `sleep_on(&wait_for_request)` · 슬롯 채움: `sector = b_blocknr<<1`, `nr_sectors=2`, `buffer=b_data`, `bh=bh` · 비교 ③(슬롯 찾기 시작점)의 코드 근거 | kernel/blk_drv/ll_rw_blk.c:110–143 · kernel/blk_drv/blk.h:15 | 코드 인용 + 32칸 슬롯 배열의 탐색 범위 도식(§4) |
| 25 | 비교 ①: ll_rw_block의 rw 값 (범위: 4종 전부) | 비교 | 표 · `READ`(0)/`WRITE`(1)/`READA`(2)/`WRITEA`(3) (`fs.h:26–29`) · 잠긴 버퍼: READ/WRITE 대기, READA/WRITEA 포기(`96–97`) · 슬롯 없음: 대기 vs 포기(`125–128`) · 슬롯 범위: READ 32개, WRITE 21개(`115–118`) — 비교 ③ 흡수 · 호출처: `bread`/`sync`/`breada` · WRITEA는 0.11에서 호출처 없음을 명시 | include/linux/fs.h:26–29 · kernel/blk_drv/ll_rw_blk.c:88–143 | 4행 비교표 |
| 26 | 코드: add_request | 코드 | `ll_rw_blk.c:64–86` · `cli`; `req->bh->b_dirt=0`(큐에 들어가는 순간 "더러움"을 버림 — 이후 쓰기는 새 dirt) · 큐 비면 `current_request=req; sti; request_fn()` · 아니면 `IN_ORDER` 조건을 만족하는 자리까지 전진 후 삽입 | kernel/blk_drv/ll_rw_blk.c:64–86 · kernel/blk_drv/blk.h:40–43 | 코드 인용 + `b_dirt=0` 라인 하이라이트 |
| 27 | 비교 ②: 큐 삽입 정책 (범위: add_request의 삽입 위치 3가지) | 비교 | (a) 빈 큐 → 즉시 실행(`72–77`) · (b) `tmp` 뒤에 삽입: `(IN_ORDER(tmp,req) \|\| !IN_ORDER(tmp,tmp->next)) && IN_ORDER(req,tmp->next)`(`78–82`) — 한 방향으로 오르다 꺾이는 지점을 허용하는 단방향 엘리베이터 · (c) 꼬리(`for` 종료) · `IN_ORDER`(`blk.h:40–43`) 키: cmd(READ<WRITE 우선), dev, sector · 단 삽입 지점 탐색은 `tmp->next`가 있는 동안이라 첫 요소(`CURRENT`) 앞에는 절대 넣지 않음 | kernel/blk_drv/ll_rw_blk.c:64–86 · kernel/blk_drv/blk.h:40–43 | 3갈래 삽입 도식(§4) |
| 28 | 코드: do_hd_request | 코드 | `hd.c:294–341` · `INIT_REQUEST`(`blk.h:127–136`: 큐 비면 return, 잠금 검사) → `MINOR`로 파티션 → `hd[dev].start_sect` 더함 → `divl` 두 번으로 sec/head/cyl → reset/recalibrate 처리 → WRITE면 `hd_out(…, WIN_WRITE, &write_intr)` + DRQ 폴링 + 첫 섹터 `port_write`; READ면 `hd_out(…, WIN_READ, &read_intr)`만 하고 **리턴** · "리턴한다"가 핵심: CPU는 다른 일을 하러 간다 | kernel/blk_drv/hd.c:294–341 · kernel/blk_drv/blk.h:109–136 · kernel/blk_drv/hd.c:56–65 | 코드 인용 + sec/head/cyl 계산 하이라이트 |
| 29 | 코드: hd_out | 코드 | `hd.c:180–200` · `do_hd = intr_addr` 후 포트 7개에 outb, 마지막 `outb(cmd, ++port)` · 명령 한 번에 이번 완료 인터럽트의 핸들러 주소를 지정 — 하드웨어와 소프트웨어의 접점 · `port_read`/`port_write`(`hd.c:56–65`)와 이어짐 | kernel/blk_drv/hd.c:180–200, 56–65 | 코드 인용 + 포트 7개 명령 순서 표 |
| 30 | 코드: hd_interrupt | 코드 | `system_call.s:221–250` · 레지스터 저장, EOI(0xA0, 0x20), `xchgl _do_hd,%edx`로 핸들러를 꺼내면서 NULL로, 없으면 `unexpected_hd_interrupt`, `call *%edx` · `hd_init:346`의 IDT 0x2E = IRQ14 · 04회차 인터럽트 진입 절차(저장→EOI) 복습 | kernel/system_call.s:221–250 · kernel/blk_drv/hd.c:343–349 | 코드 인용 + `xchgl`의 원자적 핸들러 회수 하이라이트 |
| 31 | 코드: read_intr | 코드 | `hd.c:250–267` · `win_result` 오류면 `bad_rw_intr` · `port_read(HD_DATA, CURRENT->buffer, 256)`(256워드=512B), `buffer+=512`, `sector++` · `nr_sectors` 남으면 `do_hd=&read_intr`로 재무장 후 리턴 · 0이면 `end_request(1)` + `do_hd_request()`(다음 요청 시작) | kernel/blk_drv/hd.c:242–292, 250–267 | 코드 인용 + 섹터 2회 인터럽트 타임라인(§4) |
| 32 | 코드: end_request | 코드 | `blk.h:109–125` · `b_uptodate=uptodate`, `unlock_buffer`(→`wake_up(&b_wait)`), `wake_up(&waiting)`, `wake_up(&wait_for_request)`, `dev=-1`, `CURRENT=next` · 슬라이드 17 원칙("플래그는 end_request 한 곳")의 코드 근거 · `extern inline`이라 심볼 중단점이 안 걸릴 수 있음(§8, 시연 B는 `hd.c:265` 줄 중단점 사용) | kernel/blk_drv/blk.h:109–125 · kernel/blk_drv/ll_rw_blk.c:42–57 | 코드 인용 + 깨우는 대상 3개(`b_wait`·`waiting`·`wait_for_request`) 도식(§4) |
| 33 | 상태 변화도 ②: request 한 개의 일생 | 상태도 | `dev=-1`(빈 슬롯) → 채워짐(`make_request:133–141`: dev·sector·nr_sectors·buffer·bh 기입) → 큐 삽입/즉시 실행(`add_request`: 빈 큐면 `request_fn` 즉시) → `CURRENT`(컨트롤러 명령 발행, `do_hd_request`) → 섹터별 인터럽트로 `nr_sectors` 감소(`read_intr`, 2→1→0) → `end_request`가 `dev=-1`, `CURRENT=next` · 각 전환의 원인 함수·변경 필드 표기 · 버퍼 플래그 상태도 ①(16)과는 섞지 않음(혼합 금지 원칙) | kernel/blk_drv/ll_rw_blk.c:88–143, 64–86 · kernel/blk_drv/blk.h:109–136 · kernel/blk_drv/hd.c:294–341 | 상태 변화도 ②(§4 상세 명세 — 신규) |
| 34 | 호출 순서도: bread 한 번의 전체 경로 | 배경 | 왼쪽 열(프로세스 문맥): `bread` → `getblk` → `ll_rw_block` → `make_request`(lock) → `add_request` → `do_hd_request` → `hd_out` → 리턴 → `wait_on_buffer` → `sleep_on` → `schedule` · 오른쪽 열(인터럽트 문맥, 2회): `hd_interrupt` → `read_intr` → `port_read` …(2번째) → `end_request` → `wake_up` · 다시 왼쪽: 깨어남 → `b_uptodate` 확인 → 반환 · 상태 변화도(16·33)와 다른 "순서도"임을 명시 | fs/buffer.c · kernel/blk_drv/ll_rw_blk.c · kernel/blk_drv/hd.c · kernel/system_call.s:221–250 · kernel/sched.c:151–165, 188–194 | 2열 호출 순서도(§4) |
| 35 | 시연 B 계획: 인터럽트 후 b_uptodate 반전 | 시연 | 중단점 `do_hd_request`, `read_intr`, `end_request`(inline이므로 `hd.c:265` 줄 번호로), 그리고 `bread` 복귀 지점(`buffer.c:277`) · 관찰: `do_hd_request`에서 `p *CURRENT`(sector, nr_sectors=2, `bh->b_lock`=1, `bh->b_uptodate`=0), `read_intr` 두 번 hit(`p CURRENT->nr_sectors` 2→1→0), `end_request` 직후 `p CURRENT->bh->b_uptodate`=1, `b_lock`=0, `buffer.c:277`에서 `p bh->b_uptodate`=1 · 주의: `end_request` 안에서 `CURRENT`가 `next`로 바뀌므로 미리 `set $bh = CURRENT->bh` | kernel/blk_drv/hd.c:294–341, 250–267 · kernel/blk_drv/blk.h:109–125 · fs/buffer.c:277 | GDB 명령 블록 · 캡처 04·05·06·07(§5) |
| 36 | 시연 B 캡처 | 캡처 | GDB 로그: `info registers eip`가 인터럽트 문맥(`read_intr`)에 있을 때 `p current->pid`가 "우연히 실행 중이던" 태스크(종종 task 0)임을 보여 "인터럽트는 누구의 문맥도 아니다"를 실제 관찰로 · `b_uptodate` 0→1 전후 · 각주: lab/ QEMU, `-drive if=ide`, 원본 미수정 · 인터럽트 중단점은 타이밍에 따라 `write_intr`가 먼저 걸릴 수 있어 조건부 중단 사용 | kernel/blk_drv/hd.c:250–267(관찰 대상) | materials/11-buffer-cache/captures/04·05·06·07(§5) |
| 37 | 시연 C 계획: 쓰기와 sync | 시연 | 셸에서 `echo x > /tmp/f`(12회차 `file_write`가 `b_dirt=1`) · 중단점 `sys_sync`, `add_request` · 관찰: `sync` 전 `b_dirt=1`, `add_request:71`에서 0으로, 이어 `write_intr` · 시간 부족 시 사전 캡처로 대체하고 "0.11은 `sync`를 부르지 않으면 더러운 버퍼가 디스크로 가지 않는다(재사용 시 제외)"만 강조 | fs/buffer.c:44–82 · kernel/blk_drv/ll_rw_blk.c:64–86, 70–71 | GDB 명령 블록 · 캡처 08(§5) |
| 38 | 시연 C 캡처 | 캡처 | `add_request` 진입 `p req->bh->b_dirt`=1, 한 줄 뒤 0 · `p req->cmd`=1 · `write_intr` hit · "0.11은 `sync`를 부르지 않으면 더러운 버퍼가 디스크로 가지 않는다(재사용 시 제외)" 강조 · 시간 부족 시 (기존 기록) 사전 캡처로 대체 | kernel/blk_drv/ll_rw_blk.c:70–71(관찰 대상) · kernel/blk_drv/hd.c:242–292 | materials/11-buffer-cache/captures/08(§5) |
| 39 | 질문의 답: read()가 디스크에 접근하는 때 | 정답 | 세 관문을 모두 통과할 때만: (1) `getblk`가 해시에서 못 찾거나 찾았어도 `b_uptodate==0`(`bread:273`), (2) `make_request`의 `rw==READ && b_uptodate` 재검사(`106`), (3) 요청 슬롯이 있을 때 — 그제야 `do_hd_request`가 포트에 명령 · 그 외에는 모두 메모리 복사 · "접근한다"의 실제 뜻은 "명령을 내리고 잠든다; 데이터는 인터럽트가 가져온다" | fs/buffer.c:273 · kernel/blk_drv/ll_rw_blk.c:106 · kernel/blk_drv/hd.c:294–341 | 세 관문 통과 경로 도식(§4) |
| 40 | 전체 그림: 계층과 경계 | 배경 | 3층 그림: 파일 시스템(12회차: `bread`를 부름) / 버퍼 캐시(`buffer.c`: 블록 단위, 장치 무관) / 블록 장치 드라이버(`ll_rw_blk.c` + `hd.c`: 섹터·포트) · 경계를 넘는 호출은 `ll_rw_block` 하나, 돌아오는 통로는 `end_request`의 `wake_up` 하나 | fs/buffer.c · kernel/blk_drv/ll_rw_blk.c · kernel/blk_drv/hd.c | 3층 계층 그림(§4) |
| 41 | 현대 커널과의 차이 (짧게) | 배경 | 1024B 고정 버퍼 → 페이지 캐시 + bio · 32개 request 배열 → 블록 멀티큐 · 단방향 엘리베이터 → mq-deadline/BFQ · `sync` 수동 → writeback 스레드와 dirty ratio · PIO `insw` → DMA · 14회차에서 다시 | —(현대 커널 대조 · 14회차에서 재개) | 0.11 vs 현대 5행 대조표 |
| 42 | 흔한 오해 | 배경 | (1) "`bread`가 디스크를 읽는다" — 보통은 안 읽는다 · (2) "`read_intr`가 프로세스를 깨운다" — `end_request`의 `wake_up`이 `state=0`으로 바꿀 뿐, 실행은 다음 `schedule` · (3) "`b_dirt=1`이면 곧 디스크에 써진다" — `sync`나 재사용 전까지 메모리에만 · (4) "요청 큐는 FIFO" — `IN_ORDER` 엘리베이터이고 READ가 WRITE보다 앞선다 | fs/buffer.c · kernel/blk_drv/ll_rw_blk.c · kernel/blk_drv/blk.h:40–43 · kernel/sched.c:188–194 | 오해 × 정정 4행 표 |
| 43 | 수치 참고 (코드 추론) | 코드 | `NR_HASH` 307 · `NR_REQUEST` 32(쓰기는 21) · 블록 1024B, 섹터 2개/블록 · `MAX_ERRORS` 7 · 부팅 캡처의 실제 `NR_BUFFERS` · "추론"과 "캡처"를 열로 분리 | include/linux/fs.h:47–49 · kernel/blk_drv/blk.h:15 · kernel/blk_drv/hd.c:34–35 | 추론/캡처 2열 수치표 · (기존 기록) 부팅 캡처의 buffers 줄 |
| 44 | 이해 확인 질문 | 확인 | 4문항 질문만 게시(§6 원문 그대로) · `bread`가 디스크 명령을 내리지 않고 돌아오는 두 지점 / `do_hd_request`의 READ 후 행동과 데이터 반입 주체 / `b_dirt`를 1·0으로 만드는 주체 / WRITE 요청이 큐에 가득 찰 수 있는가 | (§6 정답 근거와 동일) | 문항 4개 텍스트 |
| 45 | 이해 확인 정답 | 확인 | 정답과 근거 줄 번호(§6 원문 그대로) · 1번: (1) `b_uptodate`=1(`buffer.c:273–274`), (2) `make_request` 재검사(`ll_rw_blk.c:106–109`) · 2번: `hd_out`으로 명령만 쓰고 리턴(`hd.c:337–338`), 데이터는 `read_intr`의 `port_read` · 3번: 1 = 버퍼를 고친 파일 시스템 코드(12회차), 0 = `add_request`(`ll_rw_blk.c:70–71`)·`getblk`(`buffer.c:244`)·`invalidate_buffers`(`95`) · 4번: 아니다 — WRITE는 `request[0..20]`만(`115–118`), `IN_ORDER`에서 READ 우선(`blk.h:40–43`) | (§6 정답 근거와 동일) | 정답 4개 텍스트 |
| 46 | 정리와 다음 회차 | 정리 | 오늘 함수 6개(`bread`, `getblk`, `brelse`, `ll_rw_block`, `do_hd_request`, `read_intr`)와 플래그 4개를 한 장에 · 다음 12회차: "/etc/rc라는 문자열이 어떻게 디스크 블록이 되는가?" — 오늘의 `bread(dev, block)`에서 `block`이 어디서 오는지 · 파트 E «파일·저장» 계속 | include/linux/fs.h:68–81(플래그 4개) · —(12회차 예고) | 함수 6개·플래그 4개 요약판 + 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: E «파일·저장» · 11/15 — **파트 E의 첫 회차**(11 버퍼 캐시·블록 → 12 파일 시스템). 완료(TEAL) 01–10, 오늘(ORANGE + 굵은 테두리) 11, 이후(MUTED) 12–15.
- 오늘 한 줄 문구: "프로세스 축이 끝나고 I/O 축이 시작된다 — read()는 버퍼 캐시를 지나, 필요할 때만 디스크로"
- 10→오늘 연결 화살표 문구: "10: 프로세스가 죽어도 남는 것 — 열어둔 파일과 디스크 내용 → 11: 그 남는 디스크 내용이 메모리로 오가는 길, 버퍼 캐시를 연다"
- 오늘→12 연결 화살표 문구: "11: `bread(dev, block)`의 `block`을 누가 어디서 계산하는가 → 12: inode·경로 탐색(`namei`)이 블록 번호를 계산한다 — 12회차의 `namei`가 오늘 `bread`를 부른다"
- 원 "지도" 슬라이드(원 02) 내용 계승: 완료 상자 묶음 06–10에 "프로세스 축" 라벨, 이후 상자 12(파일 시스템)·13(tty)에 "I/O 축" 라벨을 붙여 축 전환을 한눈에 보게 한다. 미니 지도 범례는 슬라이드 02 오늘의 길에서 계승.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL): fs/ 계층의 **fs/buffer.c**(버퍼 캐시 — 블록 단위, 장치 무관)과 blk_drv/ 계층의 **kernel/blk_drv/ll_rw_blk.c**(요청 큐)·**kernel/blk_drv/hd.c**(하드디스크 드라이버). 오늘 주제 자체가 fs/ ↔ blk_drv/ 계층 경계를 다룬다.
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표 — 읽기 경로 한 바퀴): `bread`(fs/buffer.c) → `getblk`(히트 시 즉시 반환, 미스 시 계속) → `ll_rw_block` → `make_request`·`add_request`(kernel/blk_drv/ll_rw_blk.c) → `do_hd_request`·`hd_out`(kernel/blk_drv/hd.c) → 하드웨어(IRQ14) → `hd_interrupt`(kernel/system_call.s:221–250) → `read_intr` → `end_request` → `wake_up`(kernel/sched.c:188–194) → 잠들어 있던 `bread`로 복귀.
- 보조 화살표(ORANGE, 2번째 — 쓰기·동기화 경로): 파일 시스템의 쓰기(`b_dirt=1`) → `sync_dev`/`sys_sync`(fs/buffer.c:44–82) → WRITE 요청(ll_rw_blk.c) → `write_intr`(hd.c:242–292).
- 누적 강조(옅은 TEAL, 01–10): 파트 A — boot/bootsect.s·boot/setup.s·boot/head.s·init/main.c(01–03; 오늘은 boot/bootsect.s:43 `ROOT_DEV`과 init/main.c:126–137 초기화 순서 `blk_dev_init` → `buffer_init` → `hd_init` → `sti`를 경유) / 파트 B — kernel/system_call.s·kernel/asm.s·kernel/traps.c(04; 오늘 `hd_interrupt`가 같은 파일의 인터럽트 진입 절차를 재사용), include/linux/sched.h·kernel/sched.c(05; `sleep_on`/`wake_up` 복습 — 151–165·188–194), kernel/fork.c·mm/memory.c(06), mm/memory.c(07) / 파트 C — mm/page.s·mm/memory.c(07–08; 08의 `do_no_page`가 `bread_page`를 호출 — fs/buffer.c:296–315) / 파트 D — fs/exec.c(09), kernel/exit.c·kernel/signal.c(10). fs/ 계층의 namei.c·inode.c는 12회차 예고로 라벨만 유지.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(11 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 11 ORANGE, 01–10 TEAL("프로세스 축" 라벨), 12–15 MUTED("I/O 축" 라벨), 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(buffer.c·blk_drv 강조) | 도형 다이어그램 | §3 명세 그대로 — fs/buffer.c + ll_rw_blk.c·hd.c 강조, 읽기 경로 순환 화살표 + 쓰기·sync 보조 화살표 | 전 회차 공통 골격 + 01–10 누적 영역 |
| 06 | 섹터·블록·장치 번호 분해 그림 | 도형 | 섹터 2개 = 블록 1개(1024B) 막대, `0x306` = major 3 + minor 6(2번째 드라이브 1번 파티션) 분해 | — |
| 07 | 메모리 지도의 버퍼 영역 | 도형 | 3회차 메모리 지도 재사용 — 커널 `end` ~ `buffer_memory_end` 사이, 헤더는 `end`에서 위로·데이터 블록은 끝에서 아래로 마주 보며 자람, 640K~1M 구멍 건너뜀 표시 | 03회차 메모리 지도 |
| 08 | buffer_head와 데이터 블록 | 도형 | 헤더 상자(대표 필드 라벨: `b_dev`·`b_blocknr`·플래그 4개·`b_wait`·링크 4개)와 `b_data`가 가리키는 1024B 블록 | — |
| 11 | 해시 테이블·free list 구조도 (핵심) | 도형 다이어그램 | 아래 상세 명세 | — |
| 16 | 상태 변화도 ① buffer_head (핵심) | 도형 상태 다이어그램 | 아래 상세 명세 | — |
| 22 | request 큐 구조 그림 | 도형 | `request[32]` 슬롯 배열(빈 슬롯은 `dev=-1` 음영)과 `blk_dev[3]`의 `request_fn=do_hd_request`·`current_request` → 연결 리스트 | — |
| 24 | 슬롯 탐색 범위 도식 | 도형 | 32칸 중 READ는 전체·WRITE는 앞 21칸만 탐색, 역순 탐색 방향 화살표, `wait_for_request` 대기 표시 | — |
| 27 | 큐 삽입 3갈래 도식 | 도형 | (a) 빈 큐 → 즉시 실행, (b) `IN_ORDER` 중간 삽입(한 방향으로 오르다 꺾이는 지점 허용), (c) 꼬리 — `CURRENT` 앞에는 불가능함을 점선으로 표시, 키 3개(cmd·dev·sector) 범례 | — |
| 31 | read_intr 섹터 반복 타임라인 | 도형(작음) | `nr_sectors` 2→1→0, `buffer+=512`, `do_hd=&read_intr` 재무장, 0에서 `end_request(1)` + `do_hd_request()` | — |
| 32 | end_request 깨움 대상 3개 | 도형(작음) | `b_wait`(버퍼 기다림)·`waiting`(요청 기다림)·`wait_for_request`(슬롯 기다림) 3방향 `wake_up` 화살표 + `dev=-1`·`CURRENT=next` | — |
| 33 | 상태 변화도 ② request (핵심) | 도형 상태 다이어그램 | 아래 상세 명세 | — |
| 34 | 호출 순서도 — 두 문맥 | 도형 2열 순서도 | 왼쪽 프로세스 문맥 열, 오른쪽 인터럽트 문맥 열(섹터 인터럽트 2회), 잠듦(`sleep_on`→`schedule`)과 깨어남(`wake_up`→`b_uptodate` 확인→반환) 화살표 | 04회차 인터럽트 진출입 그림 양식 |
| 39 | 세 관문 도식 | 도형 | 관문 3개(`bread:273`의 `b_uptodate` 검사 → `make_request:106` 재검사 → 요청 슬롯)를 모두 통과할 때만 `do_hd_request`가 포트에 명령 — 나머지는 메모리 복사 | — |
| 40 | 3층 계층 그림 | 도형 | 파일 시스템 / 버퍼 캐시 / 블록 드라이버 3층, 하향 호출 `ll_rw_block` 1개·상향 복귀 `end_request`의 `wake_up` 1개 | 슬라이드 04 골격의 축약 |

핵심 시각자료 상세 명세 — 오늘의 중심 그림 세 가지(11·16·33은 같은 시각 언어를 공유):

- 공통 시각 언어: 버퍼·요청은 상자, 상태는 상자의 배지(4-튜플 또는 대표 필드), 전환은 화살표에 원인 함수 라벨. 기본 상태 TEAL 테두리, 진행 중(`b_lock=1`)·빈 슬롯은 MUTED/INK, 오늘 시연으로 관찰할 전환은 ORANGE. 우하단 `Linux 0.11` 라벨.
- 슬라이드 11 해시/free list 구조도: (1) 307칸 해시 테이블 중 3개 버킷을 확대 — `hash_table[(dev^block)%307]` 버킷에서 시작하는 이중 연결(`b_prev`/`b_next`), "같은 (`dev`,`block`)은 버킷 하나에 모임" · (2) 원형 free list — `free_list`에서 `b_prev_free`/`b_next_free`로 닫힌 고리, 삽입은 항상 꼬리(`insert_into_queues`), 재사용 후보 순서 · (3) 같은 `buffer_head` 상자 하나가 두 그림에 동시 등장 — "한 버퍼가 두 목록에 산다"(실선 = 해시 체인, 점선 = free list로 링크 종류 구분) · (4) 예시 버퍼 하나(`dev=0x306` 등)를 ORANGE로 강조하고 `b_count>0` 배지를 달아 "free list에 남아 있어도 `getblk`가 건너뛴다"를 표시.
- 슬라이드 16 상태 변화도 ①: 노드 = 4-튜플 상태 8개 — `free`(0,0,0,0) / `claimed`(0,0,0,1) / `reading`(0,0,1,1) / `uptodate`(1,0,0,1) / `cached`(1,0,0,0) / `dirty`(1,1,0,n) / `writing`(1,0,1,n) / 쓰기 완료 후 (1,0,0,n) — `uptodate` 재획득(getblk 적중)은 `uptodate` 노드로 되돌아오는 화살표. 전환 라벨 — free→claimed: `getblk` 243–245 / claimed→reading: `make_request` 105 `lock_buffer` / reading→uptodate: `end_request` 113–114(ORANGE — 시연 B의 관찰 대상) / uptodate→cached: `brelse` / cached→uptodate: `getblk` 적중 / uptodate→dirty: 쓰기 `b_dirt=1` / dirty→writing: `add_request` 71 + lock / writing→(1,0,0,n): `end_request`. 하단 표: 전환별 변경 데이터(플래그 비트)와 유지 조건(`b_count>0`이면 재사용 대상 아님; `b_lock`이면 플래그 변경 금지). 각주: "4-튜플 값은 코드 추론 — 캡처 관찰값만 '관찰' 표기"(§8 계승).
- 슬라이드 33 상태 변화도 ②: 노드 6개 — 빈 슬롯(`dev=-1`) → 채워짐(`make_request:133–141`가 dev·sector·nr_sectors·buffer·bh 기입) → 큐 삽입 또는 즉시 실행(`add_request`: 빈 큐면 `request_fn` 즉시) → `CURRENT`(`do_hd_request`가 컨트롤러에 명령 발행) → 섹터 인터럽트마다 `nr_sectors` 2→1→0(`read_intr`, 자기 루프 화살표 + `buffer+=512`) → 완료(`end_request`: `dev=-1`로 반납, `CURRENT=next` — 다음 요청으로 이어지는 출발 화살표). 전환마다 원인 함수·변경 필드 라벨. 상태도 ①(버퍼 플래그)과 한 장에 섞지 않는다(혼합 금지 원칙). 시연 B 캡처 05의 `nr_sectors` 2→1→0 관찰과 노드를 연결하는 대응 표시.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/11-buffer-cache/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A-1 첫 실행 | 01-bread-first-uptodate0.png | `b bread` · `b ll_rw_block` · 게스트 `cat /etc/rc` · `p dev` · `p block` · `n`으로 `buffer.c:273`까지 · `p bh->b_uptodate` · `c` | 첫 `bread`에서 `b_uptodate` = `$ = 0 '\000'`, 이어 `ll_rw_block` 중단 | 사전 캡처 로그(첫 실행분) — "`cat`이 inode·디렉터리 블록도 읽어 `bread` hit가 여러 번"임을 미리 말함 |
| A-2 두 번째 실행 | 02-bread-second-uptodate1.png | 게스트 `cat /etc/rc` 재실행 · 같은 `block`에서 `p bh->b_uptodate` · `p bh->b_count` | `b_uptodate` = `$ = 1 '\001'` 후 바로 다음 `bread`, `b_count` 값 | 사전 캡처 로그(두 번째 실행분) |
| A 증빙 | 03-info-breakpoints-hitcount.png | `info breakpoints` | `bread`와 `ll_rw_block`의 hit count 차이(두 번째 실행은 `ll_rw_block` 증가 없음) | 사전 캡처 |
| B-1 | 04-do-hd-request-current.png | `b do_hd_request` · `p *CURRENT` · `p *CURRENT->bh` · `p current->pid` | sector·nr_sectors=2, `bh->b_lock`=1, `bh->b_uptodate`=0, 요청한 프로세스 pid | 사전 캡처 |
| B-2 | 05-read-intr-nr-sectors.png | `b read_intr`(필요시 조건부 `if CURRENT->nr_sectors==1`) · `p CURRENT->nr_sectors` · `p current->pid` | `nr_sectors` 2→1→0, 인터럽트 시점 `current->pid`(요청자와 다를 수 있음) | 인터럽트 중단점이 QEMU IDE 타이밍으로 불안정하면 조건부 중단 또는 사전 캡처 |
| B-3 | 06-end-request-flag-flip.png | `b hd.c:265`(`end_request(1)` 직전 — inline이라 줄 중단점) · `set $bh = CURRENT->bh` · `n` 후 `p $bh->b_uptodate` · `p $bh->b_lock` · `b buffer.c:277`에서 `p bh->b_uptodate` | `b_uptodate` 0→1, `b_lock` 1→0, `bread` 복귀 지점에서 `b_uptodate`=1 | 사전 캡처 — `end_request` 안에서 `CURRENT`가 `next`로 바뀌므로 `$bh` 세팅 후 관찰 |
| B-4 | 07-interrupt-context-pid.png | `read_intr` 중단 시 `info registers eip` · `p current->pid` | eip가 `read_intr`(인터럽트 문맥)에 있는데 `current->pid`는 "그때 실행 중이던 태스크"(종종 task 0) — 인터럽트는 누구의 문맥도 아님 | 사전 캡처 — 어느 태스크가 잡힐지는 실행마다 다름을 각주 |
| C | 08-write-path-dirt-sync.png | `b add_request` · `b write_intr` · 게스트 `echo x > /tmp/f; sync` · `p req->bh->b_dirt` · `p req->cmd` | `add_request` 진입 시 `b_dirt`=1 → 한 줄 뒤 0(`ll_rw_blk.c:70–71`), `req->cmd`=1, `write_intr` hit | 사전 캡처 — 시간 부족 시 이것만으로 대체하고 "0.11은 `sync`를 부르지 않으면 더러운 버퍼가 디스크로 가지 않는다(재사용 시 제외)"만 강조 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜`(00-common §7). 시연 A는 부팅 직후(캐시 비어 있음)에서 시작함을 각주에 추가.

## 6. 이해 확인 질문과 정답

질문은 슬라이드 44, 정답은 슬라이드 45에 게시(원문 계승).

1. **Q.** `bread(dev, b)`가 디스크 명령을 내리지 않고 돌아오는 두 지점의 조건은?
   **A.** (1) `getblk`가 돌려준 버퍼의 `b_uptodate`가 1(`buffer.c:273–274`). (2) 그 사이에 다른 프로세스가 읽기를 끝내 `make_request`의 재검사 `rw==READ && bh->b_uptodate`(`ll_rw_blk.c:106–109`)에 걸림.
2. **Q.** `do_hd_request()`는 READ 명령을 내린 뒤 무엇을 하는가? 데이터는 누가 메모리에 넣는가?
   **A.** `hd_out`으로 포트에 명령만 쓰고 **리턴**한다(`hd.c:337–338`). 데이터는 IRQ14 → `hd_interrupt`(`system_call.s:221–250`) → `read_intr`(`hd.c:250–267`)의 `port_read`가 섹터마다 512B씩 `CURRENT->buffer`로 옮긴다.
3. **Q.** `b_dirt`는 누가 1로 만들고 누가 0으로 만드는가?
   **A.** 1: 버퍼를 고친 파일 시스템 코드(예: `file_write`, `new_block`, `write_inode`; 12회차). 0: `add_request`가 쓰기 요청을 큐에 넣는 순간(`ll_rw_blk.c:70–71`), `getblk`가 새로 할당할 때(`buffer.c:244`), `invalidate_buffers`(`95`).
4. **Q.** 큐에 WRITE 요청이 가득 찰 수 있는가?
   **A.** 아니다. WRITE는 `request[0..20]`(앞 2/3)만 탐색하고(`ll_rw_blk.c:115–118`), 나머지 11개는 READ 전용이다. 또 `IN_ORDER`에서 `cmd` 비교로 READ가 WRITE보다 앞에 삽입된다(`blk.h:40–43`).

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 버퍼 캐시(buffer cache) | 디스크 블록의 메모리 복사본과 그 메타데이터(`buffer_head`) 집합 | 01 |
| 블록 / 섹터 | 1024B 파일 시스템 단위 / 512B 하드웨어 단위. 0.11은 1블록 = 2섹터 | 06 |
| `b_uptodate` / `b_dirt` / `b_lock` / `b_count` | 디스크와 같음 / 디스크보다 새로움 / I/O 중 / 사용자 수 | 09 |
| 해시 체인 / free list | (`dev`,`block`)으로 찾는 연결 / 재사용 순서를 위한 원형 연결 | 10 |
| 요청(request) 큐 | 장치별 `current_request`로 시작하는 `struct request` 연결 리스트 | 22 |
| 엘리베이터(elevator) 정렬 | 섹터 번호 순으로 요청을 삽입해 헤드 이동을 줄이는 정책(`IN_ORDER`) | 26 |
| 미리읽기(read-ahead, READA) | 지금 필요하지 않은 블록을 미리 요청하되 자원 부족이면 포기 | 19 |
| PIO(`insw`/`outsw`) | CPU가 포트에서 워드 단위로 직접 옮기는 입출력. DMA 아님 | 31 |
| IRQ14 / 0x2E | 하드디스크 인터럽트 선과 그 IDT 벡터(`hd_init`) | 30 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- `getblk`는 LRU라고 단정하지 않는다. free list 꼬리 삽입 + `BADNESS` 최소 선택이며, "오래된 것부터"는 근사 설명임을 말한다.
- `end_request`는 `blk.h`의 `extern inline`이라 심볼 중단점이 안 걸릴 수 있다. 줄 번호 중단점(`hd.c:265`)을 쓰고, 캡처 각주에 적는다.
- `breada:336`의 `ll_rw_block(READA,bh)`는 원본 그대로이며 lab에서 고치지 않았다. "버그"라고 단정하기보다 "tmp를 의도한 것으로 보인다"로 말한다.
- `add_request`의 삽입 탐색은 `tmp->next`가 있는 동안만 돌므로 현재 실행 중인 요청 앞에는 끼어들지 않는다. "항상 섹터 순 정렬"이라고 말하지 않는다.
- 0.11에는 주기적 writeback이 없다. "커널이 알아서 쓴다"고 말하지 않는다. `sync`, 버퍼 재사용(`getblk:231–232`), `iput`의 `sync_dev`(12회차)만이 경로다.
- 인터럽트 문맥에서 `current`는 요청자가 아니라 "그때 실행 중이던 태스크"다. 시연 B 캡처에서 이를 실제 관찰로 보여주되, 어느 태스크가 잡힐지는 실행마다 다르다고 말한다.
- 상태 변화도의 4-튜플 값은 코드 추론이며, 캡처에서 관찰된 값만 "관찰"로 표기한다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 4 | 핵심 질문과 지도(로드맵·구조도로 오늘 위치 — 파트 E «파일·저장» 개시) |
| 05–11 | 16 | 배경: 왜 캐시인가, 블록·섹터·장치 번호, 메모리 배치, `buffer_head` 필드, 네 플래그, 해시·free list 그림 |
| 12–19 | 24 | `bread`/`getblk`/`brelse` 코드, 플래그 상태 변화도 ①, 동기화 원칙, `sync`, `breada` |
| 20–21 | 8 | 시연 A (bread 두 번: 첫 번째는 디스크, 두 번째는 캐시 적중) |
| 22–33 | 24 | 요청 큐: `ll_rw_block`→`make_request`→`add_request`, `IN_ORDER` 비교, `do_hd_request`, `hd_out`/`hd_interrupt`→`read_intr`→`end_request`, request 상태 변화도 ② |
| 34–38 | 14 | 호출 순서도, 시연 B (`do_hd_request` → 인터럽트 → `b_uptodate` 0→1), 시연 C (쓰기 경로와 `sync`) |
| 39–43 | 14 | 질문의 답(세 관문), 전체 그림, 현대 커널 비교, 흔한 오해, 수치 참고 |
| 44–46 | 6 | 이해 확인(질문·정답)과 정리·다음 회차 예고 |
| 예비 | 10 | 질의응답, 시연 재시도 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞부분 4, 배경 16, 버퍼 캐시 코드·상태도 24, 시연 A 8, 요청 큐 24, 순서도·시연 B/C 14, 답·정리 14, 이해 확인·정리 6, 예비 10.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(38행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07 · 원 06→08 · 원 07→09 · 원 08→10+11(분할) · 원 09→12 · 원 10→13 · 원 11→14 · 원 12→15 · 원 13→16 · 원 14→17 · 원 15→18 · 원 16→19 · 원 17→20 · 원 18→21 · 원 19→22 · 원 20→23 · 원 21→24 · 원 22→25 · 원 23→26 · 원 24→27 · 원 25→28 · 원 26→29+30(분할) · 원 27→31+32(분할) · (신규 33 상태 변화도 ②: request) · 원 28→34 · 원 29→35 · 원 30→36 · 원 31→37+38(분할) · 원 32→39 · 원 33→40 · 원 34→41 · 원 35→42 · 원 36→43 · 원 37→44+45(분할) · 원 38→46.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| 해시/free list 코드·그림 분할 | 원 08 → 새 10+11 | 00-common §5 우선순위 3(코드+그림 분리) — "한 버퍼가 두 목록에 산다" 구조도가 오늘의 핵심 시각자료이므로 전용 슬라이드 배정 (+1) |
| hd_out/hd_interrupt 분할 | 원 26 → 새 29+30 | hd.c(포트 명령)와 system_call.s(어셈블리 핸들러) 두 파일의 코드가 한 장에 2스크린 분량 — 인터럽트 진입 절차(04회차 복습)에 독립 슬라이드 (+1) |
| read_intr/end_request 분할 | 원 27 → 새 31+32 | 데이터 이동(인터럽트)과 플래그·깨우기(블록 계층)를 나눠, 동기화 원칙(슬라이드 17)의 코드 근거를 end_request 장에 집중 (+1) |
| 시연 C 계획·캡처 분할 | 원 31 → 새 37+38 | 시연 A(20/21)·B(35/36)와 동일한 계획/캡처 2장 패턴으로 통일 (+1) |
| 이해 확인 질문·정답 분할 | 원 37 → 새 44+45 | 표준 뒷부분(00-common §4) — 질문 제시와 정답 공개를 분리해 문제 풀이 시간 확보 (+1) |
| 신규: 상태 변화도 ② request | (없음) → 새 33 | course-plan 상태 변화도 범위가 버퍼(buffer_head)와 요청(request) 두 그림을 선언하는데 원 슬라이드 표에는 request 그림이 없었음 — 요청 큐 코드(22–32)를 마친 직후 배정, "버퍼 상태와 요청 큐 정책 혼합 금지" 원칙도 지킴 (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02 "지도"→로드맵/구조, 원 32 "정리"→정답, 원 37 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 38장 → 46장 (+8) | 00-common §5 확장 한도 +8 안, 목표 범위 44–50 안 |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- lab/ 빌드의 심볼명(`bread` vs `_bread`, `ll_rw_block` vs `_ll_rw_block`, `do_hd` vs `_do_hd`, `current` vs `_current` 등 `_` 접두 유무)과 줄 번호 확인 — 캡처 각주 "lab/ 수정본(심볼 `_` 접두 등 차이)"의 근거 확보 (course-plan "PPTX 제작 전 확인 목록" 1번 항목의 11 해당분).
- `end_request`가 `blk.h`의 `extern inline`이라 심볼 중단점 불가 — 시연 B의 줄 중단점 `hd.c:265`가 lab 빌드에서 같은 줄인지 확인, 다르면 lab 줄 번호로 각목 갱신.
- QEMU 실행 옵션 `-drive if=ide`에서 하드디스크 인터럽트 타이밍 확인 — 시연 B의 조건부 중단(`read_intr`에 `if CURRENT->nr_sectors==1`) 사전 검증, 불안정하면 사전 캡처로 전환.
- 루트 이미지 안 `/etc/rc`(시연 A가 `cat /etc/rc` 두 번)와 "아직 읽지 않은 파일"(시연 B: `cat /usr/...` 또는 부팅 직후 첫 `ls /`) 준비 — `/etc/rc`의 inode·블록 번호는 12회차 자료와 연계 (course-plan 확인 목록의 "루트 이미지 안 /etc/rc" 항목).
- 사전 캡처 8장 확보(§5의 01–08) — 파일명 규칙 `materials/11-buffer-cache/captures/<두자리순번>-<설명>.png` (course-plan 확인 목록의 사전 캡처 규칙). 시연 A 캡처는 "부팅 직후 상태(캐시 비어 있음)에서 시작" 각주 필수.
- 3회차 부팅 캡처의 "N buffers = M bytes buffer space" 줄 재사용 가능 확인 — 슬라이드 07·43에서 인용 (기존 기록 라벨).
- 캡처 각주에 lab 빌드·수정 여부·캡처 날짜 필수 기재 — 인터럽트 문맥의 `current->pid` 등 부팅마다 달라지는 값임을 명시(§8).
