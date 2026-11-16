# 12회차 상세 슬라이드 제작 계획 — 파일 시스템: inode·경로 탐색·I/O

- 기준: materials/course-plan.md `# 12. 파일 시스템: inode·경로 탐색·I/O` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/12-filesystem.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 38장 → 이 계획 44장 (+6)
- 로드맵 위치: 파트 E «파일·저장» · 12/15

## 1. 회차 개요

- 핵심 질문: **"/etc/rc"라는 문자열이 어떻게 디스크 블록이 되는가?**
- 학습 목표 (course-plan 원문 계승):
  1. MINIX 1.0 파일 시스템의 디스크 배치(부트 블록, 슈퍼 블록, inode 비트맵, 존 비트맵, inode 표, 데이터 존)와 그 메모리 상대(`super_block`, `m_inode`, `file`)를 그릴 수 있다.
  2. `namei("/etc/rc")`가 `get_dir` → `find_entry` → `iget` → `read_inode` → `bread`를 반복하며 루트 inode 1번에서 시작해 `rc`의 inode 번호를 얻는 과정을 한 단계씩 추적할 수 있다.
  3. `bmap()`이 파일 내 블록 번호를 `i_zone[0..6]`(직접), `i_zone[7]`(단일 간접), `i_zone[8]`(이중 간접)으로 디스크 블록 번호로 바꾸는 규칙과 상한(7+512+512²)을 설명할 수 있다.
  4. `sys_open`이 fd 슬롯 → `file_table` 슬롯 → `open_namei`의 순서로 세 자료구조를 연결하고, `sys_read`/`sys_write`가 `i_mode` 종류에 따라 `file_read`/`rw_char`/`block_read`/`read_pipe`로 갈라지는 구조를 말할 수 있다.
  5. `open()` 플래그 중 0.11 커널이 실제로 검사하는 것과 정의만 된 것을 소스로 구분할 수 있다.
- 읽을 소스 범위 (원본 src 기준 — course-plan 원문 계승):

| 파일 | 줄 | 내용 |
|---|---|---|
| include/linux/fs.h | 36–46 | NAME_LEN 14, ROOT_INO 1, I_MAP_SLOTS/Z_MAP_SLOTS 8, SUPER_MAGIC 0x137F, NR_OPEN 20, NR_INODE 32, NR_FILE 64, NR_SUPER 8 |
| include/linux/fs.h | 55–56 | INODES_PER_BLOCK(=32), DIR_ENTRIES_PER_BLOCK(=64) |
| include/linux/fs.h | 83–91 | struct d_inode (32B, 디스크 형식) |
| include/linux/fs.h | 93–114 | struct m_inode (메모리 형식: 앞부분은 d_inode와 동일 배치) |
| include/linux/fs.h | 116–122 | struct file |
| include/linux/fs.h | 124–155 | struct super_block, struct d_super_block |
| include/linux/fs.h | 157–164 | struct dir_entry(16B), inode_table[], file_table[], super_block[] |
| include/sys/stat.h | 30–34 | S_ISREG/S_ISDIR/S_ISCHR/S_ISBLK/S_ISFIFO |
| include/fcntl.h | 7–17 | O_ACCMODE … O_NDELAY |
| fs/super.c | 27–29 | super_block[NR_SUPER], ROOT_DEV |
| fs/super.c | 56–72 | get_super() |
| fs/super.c | 100–165 | read_super() — 블록 1 읽기, magic 검사, 비트맵 블록 2.. 읽기 |
| fs/super.c | 242–281 | mount_root() — iget(ROOT_DEV, ROOT_INO), pwd/root, free 개수 출력 |
| fs/inode.c | 15 | inode_table[NR_INODE] |
| fs/inode.c | 72–148 | _bmap(), bmap(), create_block() |
| fs/inode.c | 150–192 | iput() |
| fs/inode.c | 194–226 | get_empty_inode() |
| fs/inode.c | 244–292 | iget() — 표 검색, 마운트 지점 건너뛰기, read_inode |
| fs/inode.c | 294–338 | read_inode(), write_inode() — inode 번호 → 블록 번호 산식 |
| fs/namei.c | 21, 29–31 | ACC_MODE, MAY_EXEC/WRITE/READ |
| fs/namei.c | 40–54 | permission() |
| fs/namei.c | 63–66 | match() 시작 (fs 세그먼트 비교, 참조) |
| fs/namei.c | 91–153 | find_entry() — .. 특수 처리, 디렉터리 블록 순회 |
| fs/namei.c | 228–270 | get_dir() — / 또는 pwd에서 시작, 구성 요소별 반복 |
| fs/namei.c | 278–294 | dir_namei() — 마지막 구성 요소 분리 |
| fs/namei.c | 303–330 | namei() |
| fs/namei.c | 337–410 | open_namei() — O_CREAT/O_EXCL/O_TRUNC/권한 |
| fs/open.c | 138–185 | sys_open() — fd, file_table, tty 특례, f_* 채우기 |
| fs/open.c | 187–208 | sys_creat(), sys_close() |
| fs/read_write.c | 55–81 | sys_read() — 종류별 분기 |
| fs/read_write.c | 83–103 | sys_write() |
| fs/file_dev.c | 17–46 | file_read() — bmap + bread + put_fs_byte |
| fs/file_dev.c | 48–90 | file_write() — create_block + b_dirt=1, O_APPEND |
| fs/bitmap.c | 75–105 | new_block() — 존 비트맵에서 첫 0비트, getblk + clear_block |
| fs/bitmap.c | 136–168 | new_inode() — inode 비트맵에서 첫 0비트 |
| fs/fcntl.c | 47–72 | sys_fcntl() — F_SETFL이 저장하는 플래그 |
| include/linux/sched.h | 102 | task_struct.filp[NR_OPEN] |
| init/main.c | 179–183 | init의 open("/etc/rc", O_RDONLY, 0) → fd 0 |
| fs/exec.c | 199 | do_execve가 namei(filename) 사용 (9회차 연결) |

- 상태 변화도·비교 범위 (course-plan 원문 계승): 상태 변화도 ① m_inode 슬롯 한 개(비어 있음 → 읽는 중 → 메모리 상주 → 공유 → 더러움 → 반납 → 비어 있음, 전환 원인·변경 데이터·유지 조건 표기), 상태 변화도 ② 경로 탐색 커서(상태 = (현재 디렉터리 inode, 남은 문자열), ("/" → root inode 1, "etc/rc") → find_entry("etc") → (etc inode, "rc") → dir_namei 반환 → find_entry("rc") → rc inode 번호 → iget, 각 단계의 i_count 오르내리는 쌍 표시), 비교 ① open() 접근 모드 O_ACCMODE 2비트의 값 전부(O_RDONLY(0)/O_WRONLY(1)/O_RDWR(2)/3(정의되지 않은 조합) — ACC_MODE 표 "\004\002\006\377", namei.c:21), 비교 ② include/fcntl.h:11–17의 나머지 플래그 전부(O_CREAT, O_EXCL, O_NOCTTY, O_TRUNC, O_APPEND, O_NONBLOCK(=O_NDELAY)), 비교 ③ sys_read의 i_mode 분기 전부(pipe / S_ISCHR / S_ISBLK / S_ISDIR·S_ISREG / 그 외(-EINVAL), sys_write에서는 S_ISDIR가 빠지는 차이). 혼합 금지: inode 상태와 open 플래그, 파일 종류 분기는 각각 별도 슬라이드.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 12. 파일 시스템: inode·경로 탐색·I/O | 표지 | 대제목 `12. 파일 시스템: inode·경로 탐색·I/O` · 부제(핵심 질문 원문): ""/etc/rc"라는 문자열이 어떻게 디스크 블록이 되는가?" · 원 계획 부제 문구 계승: "11회차의 `bread(dev, block)` — 그 `block`은 누가 정하는가" · 우상단 `Linux 0.11` 배지 + `1991` · 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `12/15 · 파트 E «파일·저장»` | — | 표지 배지·푸터(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: ""/etc/rc"라는 문자열이 어떻게 디스크 블록이 되는가?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치, 오늘 실제 다루는 단계만 강조 · 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다름(빠짐없이 강조) · 원 표지의 부제 "11회차의 `bread(dev, block)` — 그 `block`은 누가 정하는가"를 오늘의 길 시작 멘트로 계승 | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 E «파일·저장»의 12만 ORANGE 강조 · 완료(TEAL) 01–11 · 오늘(ORANGE + 굵은 테두리) 12 · 이후(MUTED) 13–15 · 오늘 한 줄 문구: "문자열 "/etc/rc" → inode → 블록 번호 — 11회차 `bread`가 받던 번호를 계산하는 계층" · 11→12·12→13 연결 화살표 문구는 §3 명세 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | fs/ 계층의 fs/namei.c·fs/inode.c·fs/open.c·fs/read_write.c·fs/file_dev.c와 include/linux/fs.h를 진한 TEAL로 강조 · 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): 문자열 "/etc/rc" → sys_open(fs/open.c) → open_namei·get_dir·find_entry(fs/namei.c) → iget·read_inode·bmap(fs/inode.c) → 블록 번호 → 11회차 fs/buffer.c의 `bread`로 · 보조 화살표: sys_read(fs/read_write.c) → file_read(fs/file_dev.c) → `put_fs_byte`로 사용자 버퍼 — 번호를 받아 데이터를 되돌리는 길 · 누적 강조(옅은 TEAL) 01–11 영역은 §3 명세 | include/linux/fs.h · fs/namei.c · fs/inode.c · fs/open.c · fs/read_write.c · fs/file_dev.c · fs/buffer.c(11회차) | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 디스크 위의 배치 (MINIX 1.0 형식) | 배경 | 블록 0 부트, 1 슈퍼 블록, 2.. inode 비트맵(`s_imap_blocks`개), 존 비트맵(`s_zmap_blocks`개), inode 표, `s_firstdatazone`부터 데이터 · `read_super`의 `block=2` 시작(`super.c:141–151`)과 `read_inode`의 산식 `2 + s_imap_blocks + s_zmap_blocks + (i_num-1)/32`(`inode.c:303–304`)를 그림 위에 겹쳐 표시 · `SUPER_MAGIC` 0x137F 검사 위치 표시 | fs/super.c:100–165(141–151) · fs/inode.c:303–304 · include/linux/fs.h:36–46 | 디스크 배치 그림(§4 — 블록 번호 축 + 산식 겹침) |
| 06 | 네 구조체: 디스크 형식 | 코드 | `fs.h:83–91` `d_inode` 32B(`i_zone[9]`) · `fs.h:146–155` `d_super_block` · `fs.h:157–160` `dir_entry` 16B = inode 번호 2B + 이름 14B · 1블록에 inode 32개, 디렉터리 엔트리 64개(`fs.h:55–56`) · `mount_root:248–249`의 `sizeof(d_inode)==32` 검사 | include/linux/fs.h:55–56, 83–91, 146–155, 157–160 · fs/super.c:248–249 | 구조체 메모리 맵(디스크 형식 3종 나란히) |
| 07 | 네 구조체: 메모리 형식 | 코드 | `fs.h:93–114` `m_inode` = `d_inode` 앞부분 + `i_wait/i_dev/i_num/i_count/i_lock/i_dirt/i_pipe/i_mount…` · `read_inode:307–309`가 `*(struct d_inode *)inode = …`로 앞 32B만 덮어쓰는 이유 · `fs.h:124–144` `super_block`의 `s_imap[8]/s_zmap[8]`(비트맵 버퍼를 계속 붙들고 있음), `s_isup/s_imount` | include/linux/fs.h:93–114, 124–144 · fs/inode.c:307–309 | d_inode 위에 m_inode 확장 필드를 겹친 그림 |
| 08 | 세 개의 표 | 코드 | `fs.h:162–164`: `inode_table[32]`, `file_table[64]`, `super_block[8]`, 그리고 태스크별 `filp[20]`(`sched.h:102`) · 그림: `filp[fd]` → `file_table[i]` → `inode_table[j]` → 디스크 · `struct file`(`fs.h:116–122`)의 `f_pos`가 "열린 파일마다"임을 강조(fork로 공유 가능) | include/linux/fs.h:116–122, 157–164 · include/linux/sched.h:102 | 경로→inode→file→fd 대응 구조도(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 09 | 부팅 때 만들어진 초기 상태 | 코드 | `mount_root`(`super.c:242–281`): `file_table` 초기화, `read_super(ROOT_DEV)`, `iget(ROOT_DEV, 1)`, `i_count += 3`(`265`: isup/imount/pwd/root 네 곳에서 참조), `current->pwd = current->root = mi`, free 블록·inode 세기 · 부팅 캡처의 "N/M free blocks" 줄과 연결 · 11회차의 `sys_setup` → `mount_root` 호출(`hd.c:158`) | fs/super.c:242–281 · kernel/blk_drv/hd.c:158 | 부팅 캡처 "N/M free blocks" 줄(기존 자산) 인용 |
| 10 | 코드: read_super | 코드 | `super.c:100–165` · 빈 `super_block[]` 슬롯 찾기 → `bread(dev,1)` → `d_super_block` 복사 → `s_magic != 0x137F`면 실패(`132`) · 비트맵 블록을 `bread`로 차례로 읽어 `s_imap[i]/s_zmap[i]`에 **brelse하지 않고** 보관 · `s_imap[0]->b_data[0] \|= 1`, `s_zmap[0]->b_data[0] \|= 1`(0번은 예약, `161–162`) | fs/super.c:100–165 | 코드 인용 + 비트맵 버퍼를 놓지 않는 super_block 그림(05 그림 연결) |
| 11 | 호출 순서도: open("/etc/rc") 전체 | 배경 | 세로 호출 순서: `sys_open` → `open_namei` → `dir_namei` → `get_dir` → [`find_entry` → `bread` ×n, `iget` → `read_inode` → `bread`] ×구성요소 → `find_entry("rc")` → `iget` → 반환 → `f_*` 채움 → fd · 오른쪽에 11회차 `bread` 상자를 작게 반복 · "상태 변화도가 아니라 호출 순서"라고 명시 | fs/open.c:138–185 · fs/namei.c:228–410 · fs/inode.c:244–338 | 호출 순서도(§4 — 세로 체인 + 11회차 bread 상자) |
| 12 | 코드: get_dir 시작점 | 코드 | `namei.c:228–248` · `root`/`pwd` 존재 검사, 첫 글자가 `/`면 `current->root`, 아니면 `current->pwd`, 빈 문자열은 NULL · `inode->i_count++`(참조 하나 빌림) · `get_fs_byte`로 사용자 공간 문자열을 한 글자씩 읽는 이유(4회차 fs 세그먼트) | fs/namei.c:228–248 | 코드 인용 + fs 세그먼트 개념 미니 그림(4회차 재사용) |
| 13 | 코드: get_dir 반복 | 코드 | `namei.c:249–269` · 디렉터리인지·`MAY_EXEC` 권한(`permission`, `40–54`) 검사 → `/`까지 이름 길이 세기 → 문자열 끝이면 현재 inode 반환(마지막 요소는 처리하지 않음) → `find_entry` → `inr`/`idev` 보관 → `brelse(bh)`, `iput(inode)` → `iget(idev, inr)` · 참조 수가 "빌리고 돌려주고 다시 빌리는" 쌍으로 맞춰지는 것을 색으로 표시 | fs/namei.c:249–269 · fs/namei.c:40–54 | 코드 인용 + i_count 빌림/반납 쌍 색 표시 |
| 14 | 코드: find_entry | 코드 | `namei.c:91–153` · 이름 길이 14 초과 시 잘림(`104–105`, `NO_TRUNCATE` 미정의) · `entries = i_size/16` · `..` 특수 처리(`112–126`: 자기 root에서는 `.`으로, 마운트 지점 root에서는 `s_imount`로 교체) · `i_zone[0]`부터 `bread`, 블록 끝나면 `bmap(*dir, i/64)`로 다음 블록(`137–138`), `match`로 비교 · 찾으면 **버퍼를 잡은 채** 반환(호출자가 `de->inode`를 읽고 `brelse`) | fs/namei.c:91–153 · fs/namei.c:63–66(match) | 코드 인용 + 디렉터리 블록 안 dir_entry 64개 스캔 그림 |
| 15 | 코드: dir_namei와 namei | 코드 | `namei.c:278–294`: `get_dir`로 마지막 디렉터리 얻고, 문자열을 다시 훑어 마지막 `/` 뒤를 `basename`, 길이를 `namelen`으로 · `namei.c:303–330`: `namelen==0`이면(`/usr/) 디렉터리 자체 반환, 아니면 `find_entry` → `iget` → `i_atime` 갱신·`i_dirt=1` · 호출처: `do_execve`(`exec.c:199`), `sys_chdir`, `sys_mount`(`super.c:206,214`) | fs/namei.c:278–294, 303–330 · fs/exec.c:199 · fs/super.c:206, 214 | 코드 인용 + 호출처 목록 박스(09회차 연결) |
| 16 | 상태 변화도: 경로 탐색 커서 "/etc/rc" | 상태도 | 상태 (dir inode, 남은 문자열, 빌린 참조): `(root#1, "etc/rc", root.i_count+1)` → `find_entry("etc",3)`: `bread(dev, root.i_zone[0])`에서 `dir_entry{inode=k, "etc"}` → `iput(root)`, `iget(dev,k)` → `(etc#k, "rc", etc.i_count=1)` → 문자열 끝 → `dir_namei` 반환 `(etc#k, basename="rc", namelen=2)` → `find_entry("rc")` → `iput(etc)`, `iget(dev, m)` → `rc#m` · 전환 원인·변경 데이터(`i_count`, 버퍼 `b_count`)·유지 조건(각 단계에서 디렉터리여야 하고 `MAY_EXEC`) · 실제 k, m 값은 시연 A에서 채움 | fs/namei.c:91–330 · fs/inode.c:244–292 | 탐색 커서 상태 변화도(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 17 | 코드: iget | 코드 | `inode.c:244–292` · `get_empty_inode`를 **먼저** 확보(잠들 수 있으므로), `inode_table` 선형 탐색(`dev,nr` 일치), `wait_on_inode` 후 재확인, `i_count++` · `i_mount`면 그 슈퍼 블록의 루트(`ROOT_INO`)로 바꿔 다시 탐색(`263–280`) · 못 찾으면 `empty`에 `i_dev/i_num` 넣고 `read_inode` · 32개 슬롯뿐임을 강조 | fs/inode.c:244–292 · fs/inode.c:194–226 | 코드 인용 + inode_table 32슬롯 선형 탐색 그림 |
| 18 | 코드: read_inode | 코드 | (원 16 분할 1/2) `inode.c:294–312` · `lock_inode`, `get_super`, 블록 산식, `bread`, 32B 복사, `brelse`, `unlock` · 산식 `2 + s_imap_blocks + s_zmap_blocks + (i_num-1)/32`(`inode.c:303–304`)가 슬라이드 05 그림의 inode 표 위치와 일치함을 확인 | fs/inode.c:294–312 | 코드 인용 + 산식→05 디스크 배치 그림 재지시 |
| 19 | 코드: iput | 코드 | (원 16 분할 2/2) `inode.c:150–192` · pipe 특례, `i_dev==0` 특례, 블록 장치면 `sync_dev` · `i_count>1`이면 감소만 · `i_nlinks==0`이면 `truncate`+`free_inode` · `i_dirt`면 `write_inode` 후 `goto repeat` · 10회차 `do_exit`의 `iput` 세 번과 연결 | fs/inode.c:150–192 · kernel/exit.c(10회차 연결) | 코드 인용 + iput 분기 결정 미니 트리 |
| 20 | 상태 변화도: m_inode 슬롯 | 상태도 | 상태: 비어 있음 / 읽는 중(`i_lock`) / 상주 / 공유(`i_count≥2`) / 더러움 / 반납 중 · 전환 원인: `get_empty_inode:194–226`, `read_inode`, `iget` 적중, `sys_open`·`fork`, `file_write`·`namei:326–327`, `iput` · 변경 데이터: `i_dev/i_num`, `i_count`, `i_lock`, `i_dirt`, 디스크 inode 블록(`write_inode:331–334`가 `b_dirt=1`) · 유지 조건: `i_count>0`이면 `get_empty_inode`가 재사용하지 않음 | fs/inode.c:72–338(상태 전환 전체) | m_inode 슬롯 상태 변화도(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 21 | 코드: bmap — 직접·단일 간접·이중 간접 | 코드 | `inode.c:72–138` · `block<7` → `i_zone[block]` · `<7+512` → `i_zone[7]`이 가리키는 블록의 `unsigned short[512]`에서 읽음 · 그 이상 → `i_zone[8]` → 2단계 · 상한 `7+512+512*512`(`79–80`) · `create` 인자가 1이면 `new_block`으로 채움(`create_block`, `145–148`) · 간접 블록도 `bread`로 읽으므로 버퍼 캐시의 혜택을 받음 | fs/inode.c:72–148 | 코드 인용 → 다음 장(22) 블록 지도 그림으로 |
| 22 | 그림: 파일 1개의 블록 지도 | 배경 | `i_zone[0..6]` 직접 7개(7 KiB), `i_zone[7]` → 512개(512 KiB), `i_zone[8]` → 512×512개 · 최대 파일 크기 계산과 `s_max_size` · `file_read`가 `f_pos/1024`를 넣어 디스크 블록을 얻는 화살표 | fs/inode.c:72–138 · include/linux/fs.h:124–155 | 파일 블록 지도 그림(§4 — 직접·간접·이중 간접 3단) |
| 23 | 코드: new_block과 new_inode | 코드 | `bitmap.c:75–105`: `s_zmap[i]`에서 `find_first_zero`, `set_bit`, `b_dirt=1`(비트맵 버퍼), 블록 번호 = `j + i*8192 + s_firstdatazone - 1`, `getblk` 후 `clear_block`, `b_uptodate=1, b_dirt=1`(디스크를 읽지 않고 0으로 채움) · `bitmap.c:136–168`: 같은 방식으로 inode 번호, `i_count=1, i_nlinks=1, i_dirt=1` | fs/bitmap.c:75–105, 136–168 | 코드 인용 + 비트맵 첫 0비트 그림(05 배치 그림 연결) |
| 24 | 시연 A 계획: namei("/etc/rc") | 시연 | 중단점 `namei`, `find_entry`, `iget` · 게스트 셸에서 `cat /etc/rc`(또는 부팅 직후 init의 `open("/etc/rc")`를 잡기 위해 `b open_namei` 후 `c`) · 관찰: `find_entry` 진입마다 `x/3s name`(fs 세그먼트이므로 `x/s` 대신 `p/c`로 바이트 확인 또는 `namelen`), `p (*dir)->i_num` · 반환 후 `p (*res_dir)->inode`, `p (*res_dir)->name` · `iget` 진입 `p nr` · `namei` 반환값 `p *$`로 `i_num`, `i_size`, `i_zone[0]` | fs/namei.c:91–330 · fs/inode.c:244–292 · init/main.c:179–183 | GDB 명령 블록 · 캡처 01–03(§5) |
| 25 | 시연 A 캡처 | 캡처 | GDB 로그: `find_entry` 1회차 `(*dir)->i_num=1`, 찾은 `de->inode=<k>`, `de->name="etc"` · 2회차 `(*dir)->i_num=<k>`, `de->inode=<m>`, `name="rc"` · `namei` 반환 inode `i_num=<m>`, `i_mode=0100644`(예시), `i_size`, `i_zone[0]=<데이터 블록>` · 각주: lab/ QEMU i386 + GDB, 원본 미수정, 루트 이미지에 따라 k·m 값이 다름 · 슬라이드 16의 상태도에 이 값을 채워 넣는다 | fs/namei.c:91–330 · fs/inode.c:244–338(관찰 대상) | 01-find-entry-etc.png · 02-find-entry-rc.png · 03-namei-return-inode.png(§5) |
| 26 | 코드: open_namei (1/2) — 엔트리 없음·생성 | 코드 | (원 23 분할 1/2) `namei.c:337–410` 전반 · `O_TRUNC`인데 접근 모드 없으면 `O_WRONLY` 강제(`346–347`), `mode`에 umask·`I_REGULAR` · `dir_namei`, `namelen==0`(디렉터리 자체 열기) 특례 · 엔트리 없음: `O_CREAT` 아니면 `-ENOENT`, 있으면 `MAY_WRITE` 검사 → `new_inode` → `add_entry` → `de->inode = i_num; bh->b_dirt=1`(`385–386`) | fs/namei.c:337–410 · fs/bitmap.c:136–168(new_inode) | 코드 인용(생성 경로 하이라이트) |
| 27 | 코드: open_namei (2/2) — 엔트리 있음·검사 | 코드 | (원 23 분할 2/2) `namei.c:337–410` 후반 · 엔트리 있음: `O_EXCL`이면 `-EEXIST`(`396–397`), `iget` · 디렉터리를 쓰기로 열면 `-EPERM` · `permission(inode, ACC_MODE(flag))` · `O_TRUNC`면 `truncate` · 콜아웃: `O_EXCL`은 `O_CREAT` 없이도 검사되는 0.11 특이 동작(POSIX와 다름) | fs/namei.c:337–410 · fs/namei.c:40–54(permission) | 코드 인용(검사 경로 하이라이트) + O_EXCL 콜아웃 |
| 28 | 비교: 접근 모드 (범위: O_ACCMODE 값 4가지 전부) | 비교 | 표 · `O_RDONLY`(0) → `MAY_READ`(4) · `O_WRONLY`(1) → `MAY_WRITE`(2) · `O_RDWR`(2) → 6 · `3` → `0377`(모든 비트 요구 → 사실상 거부) · 근거 `namei.c:21` `ACC_MODE` 표 `"\004\002\006\377"`와 `permission`(`40–54`)의 `(mode & mask & 7) == mask` · `f_mode`가 아닌 `i_mode`가 `f_mode`에 저장되는 0.11 특이점(`open.c:179`) · `sys_read:67`의 `f_mode&1`은 pipe 전용 | fs/namei.c:21, 40–54 · fs/open.c:179 · fs/read_write.c:67 | O_ACCMODE 4값 비교표 |
| 29 | 비교: 나머지 open 플래그 (범위: fcntl.h:11–17 전부) | 비교 | 표 · `O_CREAT`: `open_namei:362`, 없으면 생성 · `O_EXCL`: `396`, 있으면 `-EEXIST`(O_CREAT 없이도 검사됨) · `O_TRUNC`: `346`, `406–407` · `O_APPEND`: `file_write:60–61, 85`, `fcntl:67–68` · `O_NONBLOCK`/`O_NDELAY`: `fcntl:67–68`이 저장만 하고 어디서도 검사 안 함 · `O_NOCTTY`: 어디서도 참조 안 함(`fcntl.h:6` 주석) · 각 행에 "커널이 검사함/저장만/무시" 표시 | include/fcntl.h:7–17 · fs/namei.c:346–407 · fs/file_dev.c:60–61, 85 · fs/fcntl.c:67–68 | 플래그별 검사 위치 비교표(3단계 판정) |
| 30 | 코드: sys_open | 코드 | `open.c:138–185` · `filp[]`에서 빈 fd(가장 작은 번호), `close_on_exec` 비트 지움 · `file_table`에서 `f_count==0` 슬롯 · `filp[fd]=f; f_count++`를 **먼저** 하고 `open_namei` 실패 시 되돌림 · tty 특례(major 4/5), 블록 장치면 `check_disk_change` · `f_mode=i_mode, f_flags=flag, f_count=1, f_inode, f_pos=0` · init의 `close(0); open("/etc/rc")`가 fd 0을 받는 이유(`main.c:180–181`) | fs/open.c:138–185 · init/main.c:180–181 | 코드 인용 + fd·file_table 슬롯 확보 순서 그림(08 구조도 재지시) |
| 31 | 코드: sys_read / sys_write 분기 | 코드 | `read_write.c:55–81`, `83–103` · 공통 검사 → `i_pipe` → `S_ISCHR`(→`rw_char`, 13회차) → `S_ISBLK`(→`block_read`) → `S_ISDIR\|\|S_ISREG`(읽기만; `count`를 `i_size`로 자름) → `file_read` · 쓰기는 `S_ISREG`만 `file_write` · `inode->i_zone[0]`이 장치 파일에서는 장치 번호라는 재사용 | fs/read_write.c:55–103 | 코드 인용 + if 사다리 도식(다음 비교표로 연결) |
| 32 | 비교: 파일 종류별 read/write 경로 (범위: sys_read의 분기 전부) | 비교 | 표 · pipe(`i_pipe`): `read_pipe`/`write_pipe`, `f_mode&1/&2` 검사 · 문자 장치: `rw_char(READ/WRITE, i_zone[0], …)` · 블록 장치: `block_read/block_write`(버퍼 캐시 직접) · 디렉터리: 읽기만 `file_read`, 쓰기는 `-EINVAL` · 일반 파일: `file_read/file_write` · 그 외: `printk` + `-EINVAL` · 각 행에 소스 줄(`read_write.c:66–80`, `93–102`) | fs/read_write.c:66–80, 93–102 | 파일 종류별 경로 비교표 |
| 33 | 코드: file_read | 코드 | (원 29 분할 1/2) `file_dev.c:17–46` · `bmap(inode, f_pos/1024)` → 0이면 구멍(0으로 채움, `39–42`), 아니면 `bread` → `put_fs_byte` 루프 → `brelse` · `i_atime` 갱신 | fs/file_dev.c:17–46 · fs/inode.c:72–148(bmap) | 코드 인용 + 구멍(hole) 경로 콜아웃 |
| 34 | 코드: file_write | 코드 | (원 29 분할 2/2) `file_dev.c:48–90` · `O_APPEND`면 `pos=i_size` · `create_block`(없으면 할당), `bread`(부분 쓰기 때문에 읽음), `b_dirt=1`(`71`), `i_size` 확장 · `get_fs_byte` 루프, `i_mtime` · 11회차 `b_dirt`가 1이 되는 바로 그 줄 | fs/file_dev.c:48–90 · fs/inode.c:145–148(create_block) | 코드 인용 + `b_dirt=1`(`71`) 하이라이트(11회차 연결) |
| 35 | 시연 B 계획: open_namei와 fd 슬롯 | 시연 | 중단점 `sys_open`, `open_namei` · 게스트에서 `cat /etc/rc` · 관찰: `sys_open` 진입 `p flag`, `p current->filp[0]@3`(0,1,2는 tty), `open.c:156` 이후 `p fd`, `p f - file_table` · `open_namei` 반환 후 `p inode->i_num`, `p/o inode->i_mode` · `open.c:184`에서 `p *f`(`f_inode`, `f_pos=0`, `f_flags`) | fs/open.c:138–185 · fs/namei.c:337–410 | GDB 명령 블록 · 캡처 04(§5) |
| 36 | 시연 C 계획: file_read → bmap → bread | 시연 | 중단점 `file_read`, `bmap`, `bread` · 관찰: `file_read` 진입 `p filp->f_pos`, `p count` · `bmap` 반환값(디스크 블록 번호) = 시연 A의 `i_zone[0]` · `bread` 진입 `p block`이 같은 값 · 이것이 "문자열 → 블록"의 마지막 고리 | fs/file_dev.c:17–46 · fs/inode.c:72–148 · fs/buffer.c(bread) | GDB 명령 블록 · 캡처 05(§5) |
| 37 | 시연 B 캡처: fd 슬롯과 file_table | 캡처 | (원 32 분할 1/2) GDB 로그: `fd=3`(셸이 0,1,2를 쓰므로), `f_count=1`, `f_inode->i_num=<m>` · 각주: lab/ QEMU, 원본 미수정 | fs/open.c:138–185(관찰 대상) | 04-sys-open-fd-slot.png(§5) |
| 38 | 시연 C 캡처: bmap과 bread의 블록 번호 일치 | 캡처 | (원 32 분할 2/2) GDB 로그: `bmap`의 `$ = <z>`와 `bread`의 `block=<z>`가 일치 · 각주: lab/ QEMU, 원본 미수정 · `cat`이 `/etc/rc`를 읽기 전에 공유 라이브러리가 없으므로 다른 open은 없음(추론) | fs/file_dev.c:17–46 · fs/inode.c:72–148 · fs/buffer.c(bread)(관찰 대상) | 05-bmap-bread-block-match.png(§5) |
| 39 | 질문의 답: "/etc/rc" → 디스크 블록 | 정답 | 한 장 요약 체인: 문자열 `/` → `current->root`(inode 1, 부팅 때 `mount_root`) → `root.i_zone[0]` 블록을 `bread` → 64개 `dir_entry` 중 `"etc"` → inode k → `read_inode`가 `2+imap+zmap+(k-1)/32` 블록을 `bread` → `etc.i_zone[0]` 블록에서 `"rc"` → inode m → `read_inode` → `rc.i_zone[0]` = 데이터 블록 z → `file_read`가 `bread(dev, z)` · 디스크 접근은 모두 `bread`를 통해서만, 실제 I/O는 캐시 미스일 때만(11회차) | fs/namei.c · fs/inode.c · fs/file_dev.c(오늘 전체) | 답 체인 그림 한 장(§4 — 슬라이드 11 최종판) |
| 40 | 세 표의 수명 정리 | 배경 | `filp[fd]`: 태스크 소유, `sys_close`·`do_exit`에서 비움 · `file_table[]`: `f_count`로 공유(fork·dup), 0이 되면 `iput`(`open.c:204–206`) · `inode_table[]`: `i_count`로 공유, 0이 되면 재사용 후보 · 각각 "누가 증가, 누가 감소"를 표로 | include/linux/fs.h:157–164 · fs/open.c:187–208 · fs/inode.c:150–226 | 세 표 수명 비교표(08 대응 구조도 재사용) |
| 41 | 현대 커널과의 차이 (짧게) | 배경 | 고정 32개 inode 표 → 슬랩 캐시 + 해시 · `namei` 선형 디렉터리 탐색 → dcache · 14자 이름·16B 엔트리 → 가변 길이 · `i_zone[9]` → ext4 extent · VFS 계층(`file_operations`)으로 `sys_read`의 `if` 사다리 대체 · 14회차에서 다시 | —(현대 비교 · 14회차 연결) | 현대 비교 5항목 표 |
| 42 | 흔한 오해 | 배경 | (1) "inode 번호가 블록 번호" — 번호는 inode 표 안의 순번이고 블록은 산식으로 구한다 · (2) "디렉터리는 특별한 파일 종류" — `file_read`로 읽을 수 있는 일반 블록 나열이다(`sys_read:72`) · (3) "open이 파일 내용을 읽는다" — 디렉터리 블록과 inode 블록만 읽고 데이터 블록은 `read` 때 읽는다 · (4) "`f_mode`는 접근 모드" — 0.11은 `i_mode`를 복사해 둔다 | fs/inode.c:303–309 · fs/read_write.c:72 · fs/open.c:179 | 오해 4개 반박 카드 |
| 43 | 이해 확인 (정답 포함) | 확인 | §6의 4문항 질문·정답 게시 · 1번 inode 블록 산식 · 2번 `get_dir` 반환값과 `basename` 처리 · 3번 `O_WRONLY\|O_EXCL` 동작(POSIX와 다른 0.11) · 4번 `bmap` 반환 0 = 구멍 | fs/inode.c:303–309 · fs/namei.c:257–258, 285–292, 315, 360, 396–397 · fs/file_dev.c:28–29, 39–42, 65(정답 근거) | 문항·정답 4세트 텍스트 |
| 44 | 정리와 다음 회차 | 정리 | 오늘 함수 체인(`namei` → `iget` → `read_inode` → `bmap` → `bread`)과 세 표 · 다음 13회차: "키보드에서 누른 글자가 read()까지 어떻게 전달되는가?" — 오늘 `sys_read`의 `S_ISCHR` 분기 `rw_char`로 들어간다 · 파트 E «파일·저장» 마무리 — 11(버퍼 캐시)·12(파일 시스템)로 저장 축 완결 | —(13회차 예고) | 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: E «파일·저장» · 12/15 — 파트 E의 마지막 회차(11 버퍼 캐시·블록 장치 → 12 파일 시스템). 완료(TEAL) 01–11, 오늘(ORANGE + 굵은 테두리) 12, 이후(MUTED) 13–15.
- 오늘 한 줄 문구: "문자열 "/etc/rc" → inode → 블록 번호 — 11회차 `bread`가 받던 번호를 계산하는 계층"
- 11→오늘 연결 화살표 문구: "11: `bread(dev, block)`가 블록 번호를 받아 디스크를 읽었다 → 12: 그 `block` 번호를 누가 계산했는가 — 오늘의 `namei`·`iget`·`bmap`"
- 오늘→13 연결 화살표 문구: "12: `sys_read`의 `S_ISCHR` 분기가 `rw_char`로 문자 장치에 보냈다 — `open("/dev/tty0")`도 오늘의 `sys_open`·`open_namei`를 지난다 → 13: 터미널 I/O — 키보드에서 누른 글자가 read()까지 어떻게 전달되는가?"
- 원 "지도" 슬라이드(원 02) 내용 계승: "11(버퍼) 위에 12(파일 시스템)가 올라감" — 완료 상자 11에 "오늘의 모든 디스크 읽기는 이 회차의 `bread`를 지남" 연결 라벨, 완료 상자 09에 "exec의 `namei`(`exec.c:199`)가 오늘 본문", 완료 상자 10에 "`do_exit`의 `iput`이 오늘 본문" 연결 라벨. 미니 지도 범례는 슬라이드 02 오늘의 길에서 계승.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL): fs/ 계층의 fs/namei.c(경로 탐색 `namei`·`open_namei`), fs/inode.c(`iget`·`read_inode`·`iput`·`bmap`), fs/open.c(`sys_open`·`sys_close`), fs/read_write.c(`sys_read`/`sys_write` 분기), fs/file_dev.c(`file_read`/`file_write`) + include/linux/fs.h(네 구조체·세 표). fs/super.c·fs/bitmap.c·fs/fcntl.c도 읽기 범위에 포함되므로 보조 강조·라벨 유지.
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): 문자열 "/etc/rc"(사용자 공간) → sys_open(fs/open.c) → open_namei·get_dir·find_entry(fs/namei.c) → iget·read_inode·bmap(fs/inode.c) → 블록 번호 → 11회차 fs/buffer.c의 `bread`로.
- 보조 화살표(ORANGE, 2번째 — 00-common §2가 허용하는 1–2개 안): sys_read(fs/read_write.c) → file_read(fs/file_dev.c) → `put_fs_byte`로 사용자 버퍼 — 계산된 블록 번호로 데이터를 되돌려주는 길.
- 누적 강조(옅은 TEAL, 01–11): 파트 E — fs/buffer.c·kernel/blk_drv/ll_rw_blk.c·kernel/blk_drv/hd.c(11, 오늘 주 화살표의 도착점이므로 라벨 유지) / 파트 D — fs/exec.c(09, `do_execve`의 `namei`), kernel/exit.c·kernel/signal.c(10, `iput` 세 번) / 파트 A — boot/*·init/main.c(01–03) / 파트 B — kernel/system_call.s·kernel/sched.c·kernel/fork.c(04–06) / 파트 C — mm/memory.c·mm/page.s(07–08). "11회차 파일은 옅은 TEAL, 오늘 파일은 진한 TEAL" 누적 규칙 그대로.

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(12 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 12 ORANGE, 01–11 TEAL, 13–15 MUTED, 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(fs/ 강조) | 도형 다이어그램 | §3 명세 그대로 — fs/ 5파일 + include/linux/fs.h 강조 + 데이터 흐름 화살표 2 | 전 회차 공통 골격 + 11 누적 영역 |
| 05 | MINIX 1.0 디스크 배치 그림 | 도형 | 블록 번호 세로축(0 부트, 1 슈퍼 블록, 2.. imap, zmap, inode 표, s_firstdatazone.. 데이터) + `read_super`의 block=2 시작·`read_inode` 산식 겹침 표시 | — |
| 06 | 구조체 메모리 맵(디스크 형식) | 도형 | d_inode 32B·d_super_block·dir_entry 16B(inode 번호 2B + 이름 14B) 나란히, 1블록 32/64개 눈금 | — |
| 08 | 경로→inode→file→fd 대응 구조도 (핵심) | 도형 | 아래 상세 명세(4단 슬롯 + 예시 화살표) | 06회차 fork의 filp 복사 개념 연결 |
| 11 | open("/etc/rc") 호출 순서도 | 도형 | 세로 체인 sys_open → open_namei → dir_namei → get_dir → [find_entry → bread, iget → read_inode → bread] ×구성요소 → fd · 오른쪽 11회차 bread 상자 · "호출 순서이지 상태도 아님" 명시 | 09회차 호출 그래프 양식 |
| 14 | 디렉터리 블록 스캔 그림 | 도형 | 블록 안 dir_entry 64칸, match 비교 커서, 블록 끝나면 `bmap(*dir, i/64)`로 다음 블록 | — |
| 16 | 경로 탐색 커서 상태 변화도 (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(노드열 + 전환 라벨) | — |
| 17 | inode_table 32슬롯 탐색 그림 | 도형 | 32칸 선형 탐색, (dev,nr) 적중 칸과 empty 칸, i_mount 칸에서 ROOT_INO로 점프 | — |
| 20 | m_inode 슬롯 상태 변화도 (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(상태 6 + 전환 라벨 + 하단 표) | 05회차 태스크 상태 다이어그램 양식 |
| 22 | 파일 1개의 블록 지도 | 도형 | i_zone[0..6] 직접 7개·i_zone[7] 간접 512개·i_zone[8] 이중 간접 3단 구조 + f_pos/1024 → 디스크 블록 화살표 | — |
| 39 | 질문의 답 체인 그림 | 도형 | 슬라이드 11 호출 순서도에 기호(k, m, z)를 배치한 최종판 한 장 | 슬라이드 11 축약 재활용 |

핵심 시각자료 상세 명세 — 세 자료(08 대응 구조도, 16 탐색 커서 상태도, 20 m_inode 상태도)가 같은 시각 언어를 공유:

- 공통 시각 언어: 상자 = 자료구조·슬롯, TEAL = 확정된 대응·유지 중, ORANGE = 오늘의 전환·현재 커서, MUTED = 빈 슬롯·과거. inode 상자의 배지 = `i_count`, 자물쇠 아이콘 = `i_lock`, 별표 = `i_dirt`. 버퍼 상자의 배지 = `b_count`. 우하단 `Linux 0.11` 라벨.
- 슬라이드 08 (4단 슬롯): (1) task_struct의 `filp[20]` — fd 0–19 인덱스를 가진 가로 슬롯 띠. (2) `file_table[64]` — 각 칸에 `f_count`·`f_pos`·`f_flags`·`f_inode` 미니 필드. (3) `inode_table[32]` — 각 칸에 `i_dev`·`i_num`·`i_zone[9]` 요약 + `i_count` 배지·`i_lock` 자물쇠·`i_dirt` 별표. (4) 디스크 — super_block[8]·inode 블록·데이터 블록. 예시 화살표(TEAL): fd 3 → file_table[i] → inode_table[j](rc#m) → 데이터 블록 z. `sys_open`이 세 슬롯을 채우는 순서를 번호로 표시(① 빈 fd ② `f_count++` 후 `open_namei` ③ `f_mode/f_flags/f_inode/f_pos` 채움 — 원 26의 순서). 보조 표시: fork 시 `filp` 복사로 `f_count` 증가(06회차), `sys_close`로 감소 → 0이면 `iput`(`open.c:204–206`) — 수명 정리는 슬라이드 40이 같은 그림을 재사용.
- 슬라이드 16 (노드열 + 전환 라벨): 노드 = (현재 디렉터리 inode, 남은 문자열, 빌린 참조). 노드열 4개 — `(root#1, "etc/rc", root.i_count+1)` → `find_entry("etc",3)` → `(etc#k, "rc", etc.i_count=1)` → `dir_namei` 반환 `(etc#k, basename="rc", namelen=2)` → `find_entry("rc")` → `rc#m`. 각 전환 화살표에 원인 라벨(`find_entry`: `bread(dev, root.i_zone[0])`에서 `dir_entry{inode=k, "etc"}` · `iput(root)` + `iget(dev,k)` 등)과 변경 데이터(inode 교체, `i_count` ±1, 버퍼 `b_count` ±1). k, m은 기호로 두고 숫자는 캡처(슬라이드 25)에서만. 각 노드 아래 유지 조건 한 줄: 디렉터리여야 하고 `MAY_EXEC`(`permission`).
- 슬라이드 20 (상태 6 + 전환 + 하단 표): 상태 노드 — `비어 있음`(`i_count=0`, `i_dev=0`) / `읽는 중`(`i_lock=1`, `get_empty_inode`가 `i_dev/i_num` 설정 후 `read_inode`) / `메모리 상주`(`i_count≥1`, `i_lock=0`) / `공유`(`i_count≥2`) / `더러움`(`i_dirt=1` — 상주·공유 위에 겹침 배지로 표현 가능) / `반납 중`(`iput` 진행). 전환 화살표 원인 라벨 — `get_empty_inode`(inode.c:194–226), `read_inode`(294–312), `iget` 적중(244–292), `sys_open`→`f_inode`·`fork`의 `filp` 복사, `file_write`·`namei:326–327`(i_atime·`i_dirt=1`), `iput`(150–192: `i_count>1`이면 감소만 · 1이고 `i_nlinks==0`이면 `truncate`+`free_inode` · `i_dirt`면 `write_inode` 후 `goto repeat` — `write_inode:331–334`가 버퍼 `b_dirt=1`). 하단 표: 전환별 변경 데이터(`i_dev/i_num`, `i_count`, `i_lock`, `i_dirt`, 디스크 inode 블록)와 유지 조건(`i_count>0`이면 `get_empty_inode`가 재사용하지 않음). 캡처 슬라이드 25·37의 `i_count`·`i_num` 값이 이 상태도의 해당 상태를 재지시한다고 각주.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/12-filesystem/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A — find_entry 1회차 | 01-find-entry-etc.png | `b namei` · `b find_entry` · `b iget` · (필요시 `b open_namei` 후 `c` — `cat`이 `open_namei` 경로로 들어갈 경우) · 게스트 셸 `cat /etc/rc` · `p (*dir)->i_num` · `p namelen` · 반환 직전 `namei.c:145`에 중단점 두고 `p *de` | `find_entry` 1회차: `(*dir)->i_num=1`, `namelen=3`, `de->inode=k`, `de->name="etc"` | 사전 캡처 — 문자열은 fs 세그먼트(사용자 공간)에 있어 `x/s name`이 커널 DS 기준으로 엉뚱한 곳을 가리킬 수 있음 → `namelen`과 `de->name`(커널 버퍼)으로 확인 |
| A — find_entry 2회차·iget | 02-find-entry-rc.png | `c` → 다음 정지 · `p (*dir)->i_num` · `p namelen` · `namei.c:145`에서 `p *de` · `iget` 진입 `p dev`, `p nr` | 2회차: `(*dir)->i_num=k`, `namelen=2`, `de->inode=m`, `de->name="rc"` · `iget(dev, m)` | 사전 캡처 |
| A — namei 반환 | 03-namei-return-inode.png | `finish` 후 `p *inode`(또는 반환값 `p *$`) | 반환 inode: `i_num=m`, `i_mode=0100644`(예시), `i_size`, `i_zone[0]=z` | 사전 캡처 |
| B — fd 슬롯 | 04-sys-open-fd-slot.png | `b sys_open` · `b open.c:184` · 게스트 `cat /etc/rc` · `p/o flag` · `p current->filp[0]@3` · `open.c:156` 이후 `p fd` · `p f - file_table` · `open.c:184`에서 `p *f` | `flag=0`(O_RDONLY), `filp[0..2]`=tty inode, `fd=3`(셸이 0,1,2를 쓰므로), `f_count=1`, `f_pos=0`, `f_inode->i_num=m` | 사전 캡처 |
| C — 블록 번호 일치 | 05-bmap-bread-block-match.png | `b file_read` · `b bmap` · `b bread` · 같은 `cat`에서 계속 `c` · `p filp->f_pos` · `p count` · `bmap` `finish` 반환값 · `bread` 진입 `p block` · `p dev` | `file_read` 진입 `f_pos=0` · `bmap` 반환 z = 시연 A의 `i_zone[0]` · `bread`의 `block=z` 일치 · `dev=0x306`(루트 장치, 이미지 설정에 따라 다름) | 사전 캡처 · 11회차 시연 A와 같은 로그를 공유해도 됨 |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음 · 캡처 날짜`(00-common §7). inode 번호 k·m과 블록 번호 z는 lab 루트 이미지의 값이며 다른 이미지에서는 다르다(§8 마지막에서 두 번째 항목 참조).

## 6. 이해 확인 질문과 정답

질문과 정답은 슬라이드 43에 게시(원문 계승).

1. **Q.** inode 번호 n의 디스크 inode가 들어 있는 블록 번호는?
   **A.** `2 + s_imap_blocks + s_zmap_blocks + (n-1)/32`, 블록 안 위치는 `(n-1)%32`(`inode.c:303–309`). 1블록 1024B에 32B inode 32개(`fs.h:55`).
2. **Q.** `get_dir("/etc/rc")`가 반환하는 inode는 무엇이며, "rc"는 누가 처리하는가?
   **A.** `etc` 디렉터리의 inode. `get_dir`는 `/`가 더 없으면 현재 inode를 반환한다(`namei.c:257–258`). "rc"는 `dir_namei`가 `basename`으로 잘라(`285–292`) `namei`/`open_namei`의 `find_entry`가 처리한다(`315`, `360`).
3. **Q.** `open(path, O_WRONLY\|O_EXCL, 0)`을 **이미 존재하는** 파일에 하면 0.11은 어떻게 되는가?
   **A.** `-EEXIST`. `open_namei`는 엔트리를 찾은 뒤 `O_CREAT` 여부와 무관하게 `flag & O_EXCL`을 검사한다(`namei.c:396–397`). (POSIX와 다른 0.11 동작.)
4. **Q.** `file_read`에서 `bmap`이 0을 반환하면 어떻게 되는가?
   **A.** 디스크를 읽지 않고 그 구간을 0으로 채워 사용자에게 준다(`file_dev.c:28–29`, `39–42`). 파일의 "구멍(hole)". `file_write`는 반대로 `create_block`으로 블록을 새로 할당한다(`65`).

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 슈퍼 블록(super block) | 파일 시스템 전체 정보(inode 수, 존 수, 비트맵 크기, 첫 데이터 존, magic). 디스크 블록 1. | 05 |
| inode(i-node) | 파일 하나의 메타데이터와 블록 지도. 이름은 없음. 디스크 형식 `d_inode`, 메모리 형식 `m_inode`. | 05 |
| 존(zone) | MINIX 용어로 데이터 블록. 0.11에서 `s_log_zone_size=0`이라 존 = 블록. | 05 |
| 비트맵(imap/zmap) | inode와 존의 사용 여부 비트. 슈퍼 블록 바로 뒤에서 시작해 메모리의 `s_imap[]/s_zmap[]` 버퍼에 상주. | 05 |
| 디렉터리 엔트리(`dir_entry`) | 16B = inode 번호 2B + 이름 14B. 디렉터리 파일은 이 엔트리의 배열. | 06 |
| 마운트 지점(`i_mount`, `s_imount`) | 다른 파일 시스템의 루트로 바꿔 타는 inode. | 07 |
| 파일 구조체(`struct file`)와 fd | 열린 파일 하나의 위치(`f_pos`)와 플래그; fd는 태스크의 `filp[]` 인덱스. | 08 |
| 경로 탐색(path lookup, `namei`) | 문자열을 구성 요소로 잘라 디렉터리를 차례로 읽어 inode를 얻는 일. | 11 |
| iget | `inode_table`에서 (dev, nr)로 inode를 찾아 `i_count++`하고, 없으면 빈 슬롯에 `read_inode`로 적재. | 17 |
| 직접/간접/이중 간접 블록 | `i_zone[0..6]` / `i_zone[7]` / `i_zone[8]`. | 21 |
| bmap | 파일 내 블록 번호를 `i_zone` 지도로 디스크 블록 번호로 바꿈(fs/inode.c). | 21 |
| 구멍(hole) | `bmap`이 0인 구간. 읽으면 0, 쓰면 할당. | 33 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- `f_mode`에 `i_mode`가 저장된다(`open.c:179`). 현대 커널의 `f_mode`(FMODE_READ 등)와 같다고 말하지 않는다. 읽기/쓰기 허용은 `open_namei`의 `permission` 검사 시점에만 확인되며 이후 `sys_read`는 pipe 외에는 모드를 다시 보지 않는다.
- `O_NONBLOCK`과 `O_NOCTTY`는 정의만 있고 커널이 검사하지 않는다(`fcntl.h:6`, 검색 결과 `fcntl.c:67–68` 저장만). "비차단 I/O를 지원한다"고 말하지 않는다.
- `O_EXCL`은 `O_CREAT` 없이도 작동하는 0.11 특이 동작(`namei.c:396`)이다. POSIX 의미로 설명하지 않는다.
- `find_entry`는 버퍼를 잡은 채 반환한다. 호출자가 `brelse`를 잊으면 `b_count`가 새므로, "반환 즉시 해제"라고 말하지 않는다.
- `iget`은 선형 탐색이며 32개뿐이다. 성능 논의 시 "해시"라고 말하지 않는다(버퍼 캐시만 해시).
- 디렉터리 이름 14자 초과는 오류가 아니라 잘림(`NO_TRUNCATE` 미정의, `namei.c:27`, `104–105`). `unistd.h:8`의 `_POSIX_NO_TRUNC` 주석과 모순됨을 사실로만 말한다.
- 시연 캡처의 inode 번호(k, m)와 블록 번호(z)는 lab 루트 이미지의 값이며 다른 이미지에서는 다르다. 상태 변화도에는 기호로 두고 캡처에서만 숫자를 보인다.
- 데이터 블록 "접근"은 모두 `bread`를 통하므로 실제 디스크 I/O 여부는 11회차 규칙을 따른다. "open하면 디스크를 n번 읽는다"는 수치를 단정하지 않는다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–04 | 4 | 핵심 질문과 지도(오늘의 길·로드맵·구조도) |
| 05–11 | 18 | 배경: 디스크 배치, 네 구조체, 부팅 시 `mount_root`가 만든 초기 상태, read_super, open 전체 호출 순서 |
| 12–19 | 22 | 경로 탐색: `get_dir`/`find_entry`/`dir_namei`/`namei` 코드와 탐색 커서 상태도, `iget`/`read_inode`/`iput` |
| 20–23 | 12 | inode 슬롯 상태도, `bmap`, 파일 블록 지도, `new_block`/`new_inode` |
| 24–25 | 10 | 시연 A (`namei` 중단 → `/etc/rc`의 inode 번호와 `i_zone[0]`) |
| 26–34 | 20 | `open_namei`/`sys_open`과 플래그 비교, `sys_read` 분기 비교, `file_read`/`file_write`, `new_block`/`new_inode` 연결 |
| 35–38 | 10 | 시연 B (`open_namei`와 fd 슬롯), 시연 C (`file_read` → `bmap` → `bread`) |
| 39–42 | 12 | 질문의 답(문자열 → 블록 전체 경로), 현대 비교, 흔한 오해 |
| 43–44 | 6 | 이해 확인과 정리 |
| 예비 | 6 | 질의응답 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 4 / 18 / 22 / 12 / 10 / 20 / 10 / 12 / 6 + 예비 6 = 120분.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(38행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07 · 원 06→08 · 원 07→09 · 원 08→10 · 원 09→11 · 원 10→12 · 원 11→13 · 원 12→14 · 원 13→15 · 원 14→16 · 원 15→17 · 원 16→18+19(분할) · 원 17→20 · 원 18→21 · 원 19→22 · 원 20→23 · 원 21→24 · 원 22→25 · 원 23→26+27(분할) · 원 24→28 · 원 25→29 · 원 26→30 · 원 27→31 · 원 28→32 · 원 29→33+34(분할) · 원 30→35 · 원 31→36 · 원 32→37+38(분할) · 원 33→39 · 원 34→40 · 원 35→41 · 원 36→42 · 원 37→43 · 원 38→44.

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| read_inode·iput 분할 | 원 16 → 새 18+19 | 두 함수가 코드 2스크린 분량(inode.c:294–312 + 150–192) — read_inode는 05 디스크 배치 그림 재지시, iput은 분기 6갈래(감소만/truncate/write_inode/repeat)를 각각 배정 (+1) |
| open_namei 분할 | 원 23 → 새 26+27 | namei.c:337–410이 74행 — "엔트리 없음(생성)" 경로와 "엔트리 있음(검사)" 경로로 나눔 — O_EXCL 특이 동작(396–397) 콜아웃 확보 (+1) |
| file_read·file_write 분할 | 원 29 → 새 33+34 | 두 함수가 각각 한 슬라이드 분량 — 읽기(구멍, put_fs_byte)와 쓰기(O_APPEND, `b_dirt=1`의 71)를 나눠 11회차 연결 지점을 뚜렷이 (+1) |
| 시연 B·C 캡처 분할 | 원 32 → 새 37+38 | fd 슬롯 관찰(B)과 bmap-bread 블록 번호 일치(C)는 관찰 대상이 다름 — 캡처 파일도 분리(04·05) (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02 "지도"→로드맵/구조, 원 33 "정리"→정답, 원 37 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 38장 → 44장 (+6) | 목표 범위 44–50의 하단(00-common §5) — slide-plans README의 12회차 선언(38→44)과 일치 |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- 루트 이미지 안 `/etc/rc`의 inode·블록 번호 사전 확보 — 시연 A 관찰 값 k(etc inode)·m(rc inode)·z(데이터 블록)과 슬라이드 16 상태도·25 캡처에 채울 값. 루트 이미지에 따라 다르므로 제작 시점 lab/ 이미지에서 확정 (course-plan "PPTX 제작 전 확인 목록"의 12 해당분).
- lab/ 빌드의 심볼명(`_namei`/`_open_namei`/`_sys_open`/`_file_read`/`_bmap`/`_bread`/`_find_entry`/`_iget` 등 `_` 접두 유무)과 줄 번호 확인 — 슬라이드 24·35·36의 중단점 설정과 `b open.c:184` 줄 지정의 근거 확보.
- GDB의 fs 세그먼트 한계 사전 검증: `x/s name`이 커널 DS 기준이 되어 엉뚱한 곳을 가리킬 수 있음 — `namelen`·`de->name`(커널 버퍼) 확인 전략(§5 시연 A 대체)이 실제로 동작하는지 확인.
- 시연 C의 루트 장치 번호 확인(원안 관찰 값 `0x306`) — lab 이미지 설정(ROOT_DEV)에 따라 다름.
- 사전 캡처 확보: §5의 01–05 다섯 장 — 파일명 규칙 `materials/12-filesystem/captures/<두자리순번>-<설명>.png`. 시연 C는 11회차 시연 A 로그와 공유 허용.
- 부팅 캡처의 "N/M free blocks" 줄(`mount_root` 출력) 재사용 — 슬라이드 09 연결용 기존 자산 존재 확인.
- 원본 소스 사실 반영 검증: `O_EXCL`을 `O_CREAT` 없이 검사하는 점(namei.c:396–397)이 lab 소스에서도 동일한지, 슬라이드 27·29·43의 인용 줄 번호와 lab 줄 번호 차이를 각주로 처리.
