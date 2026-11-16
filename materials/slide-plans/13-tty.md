# 13회차 상세 슬라이드 제작 계획 — 터미널 I/O

- 기준: materials/course-plan.md `# 13. 터미널 I/O` 절 · 공통 규격: materials/slide-plans/00-common.md
- 산출물: output/13-tty.pptx (PPTX 하나뿐 — CLAUDE.md)
- 장수: 기존 계획 42장 → 이 계획 49장 (+7)
- 로드맵 위치: 파트 F «터미널» · 13/15

## 1. 회차 개요

- 핵심 질문: **키보드에서 누른 글자가 read()까지 어떻게 전달되는가?**
- 학습 목표 (course-plan 원문 계승):
  1. 키보드 IRQ1 → `keyboard_interrupt` → 스캔 코드 변환 → `put_queue`(read_q)까지의 인터럽트 경로를 어셈블리 수준에서 설명한다.
  2. `tty_struct`의 세 큐(read_q / secondary / write_q)와 head/tail 원형 버퍼 매크로(INC/DEC/EMPTY/FULL/LEFT/CHARS)의 의미를 읽는다.
  3. `copy_to_cooked`가 수행하는 정규(canonical) 처리(ICRNL, ERASE/KILL, ECHO, ISIG → `tty_intr`)를 코드로 확인하고, 0.11이 실제로 참조하는 termios 플래그와 선언만 된 플래그를 구분한다.
  4. `tty_read`가 `sleep_if_empty`로 잠들고 `wake_up(&secondary.proc_list)`로 깨어나는 상태 변화를 설명한다.
  5. `tty_write` → `con_write`로 글자가 VGA 텍스트 메모리에 쓰이는 출력 경로와, `printk`가 같은 경로를 쓴다는 사실을 확인한다.
- 읽을 소스 범위 (파일:줄 범위, 원본 src 기준 — course-plan 원문 계승):

| 파일 | 줄 | 내용 |
|---|---|---|
| include/linux/tty.h | 14–34 | `TTY_BUF_SIZE`, `struct tty_queue`, INC/DEC/EMPTY/LEFT/LAST/FULL/CHARS/GETCH/PUTCH 매크로 |
| include/linux/tty.h | 36–43 | INTR_CHAR/QUIT_CHAR/ERASE_CHAR/KILL_CHAR/EOF_CHAR/START/STOP/SUSPEND_CHAR |
| include/linux/tty.h | 45–55 | `struct tty_struct`(termios, pgrp, stopped, write 함수 포인터, 세 큐), `tty_table[]` |
| include/linux/tty.h | 57–63 | `INIT_C_CC` 기본 제어 문자(^C=\003, DEL=\177, ^U=\025, ^D=\004 …) |
| kernel/chr_drv/keyboard.S | 21–30 | `size=1024`, head/tail/proc_list/buf 오프셋(tty_queue 구조와 일치해야 함), `mode`/`leds`/`e0` |
| kernel/chr_drv/keyboard.S | 37–77 | `_keyboard_interrupt`: inb $0x60, e0/e1 처리, `call key_table(,%eax,4)`, 0x61 포트 ack, EOI(0x20), `call _do_tty_interrupt`, iret |
| kernel/chr_drv/keyboard.S | 88–110 | `put_queue`: `_table_list[0]`(콘솔 read_q)에 바이트 저장, head 전진, 가득 차면 폐기, proc_list 태스크 state=0 |
| kernel/chr_drv/keyboard.S | 111–127 | ctrl/alt/unctrl/unalt → `mode` 비트 설정 |
| kernel/chr_drv/keyboard.S | 236–241 | `func_table`(F1 = ESC [ [ A …) |
| kernel/chr_drv/keyboard.S | 245–261 | `key_map`(KBD_FINNISH; config.h:19가 FINNISH 선택) |
| kernel/chr_drv/keyboard.S | 453–484 | `do_self`: key_map/shift_map/alt_map 선택, Ctrl/Caps 변환(−32, −64), `call put_queue` |
| kernel/chr_drv/keyboard.S | 502–509 | `key_table` 앞부분(스캔 코드 → 처리 루틴, 0x1D=ctrl) |
| kernel/chr_drv/keyboard.S | 530–540 | break 코드(≥0x80) 대부분 `none` |
| kernel/chr_drv/tty_io.c | 28–49 | `_L_FLAG/_I_FLAG/_O_FLAG`와 L_CANON, L_ISIG, L_ECHO, L_ECHOCTL, I_CRNL, I_NLCR, I_UCLC, I_NOCR, O_POST, O_NLCR, O_CRNL, O_NLRET, O_LCUC 매크로 |
| kernel/chr_drv/tty_io.c | 51–92 | `tty_table[]` 초기값: 콘솔 iflag=ICRNL, oflag=OPOST\|ONLCR, lflag=ISIG\|ICANON\|ECHO\|ECHOCTL\|ECHOKE; rs1/rs2는 변환 없음, B2400\|CS8 |
| kernel/chr_drv/tty_io.c | 99–103 | `table_list[]`(keyboard.S가 `_table_list`로 참조) |
| kernel/chr_drv/tty_io.c | 105–109 | `tty_init` → rs_init, con_init |
| kernel/chr_drv/tty_io.c | 111–120 | `tty_intr`: pgrp가 같은 모든 task의 `signal`에 마스크 OR |
| kernel/chr_drv/tty_io.c | 122–138 | `sleep_if_empty` / `sleep_if_full`(cli, `interruptible_sleep_on(&queue->proc_list)`) |
| kernel/chr_drv/tty_io.c | 145–228 | `copy_to_cooked`: read_q → secondary, CR/NL 변환, KILL/ERASE/STOP/START, ISIG(INTR/QUIT), `secondary.data++`(줄 수), ECHO → write_q, 끝에 `wake_up(&tty->secondary.proc_list)` |
| kernel/chr_drv/tty_io.c | 230–288 | `tty_read`: VTIME/VMIN, `sleep_if_empty(&tty->secondary)`, `put_fs_byte`, EOF/줄 단위 반환, 시그널 시 `-EINTR` |
| kernel/chr_drv/tty_io.c | 290–326 | `tty_write`: `sleep_if_full(&tty->write_q)`, OPOST/ONLCR(NL→CR NL), `tty->write(tty)`, 남으면 `schedule()` |
| kernel/chr_drv/tty_io.c | 342–345 | `do_tty_interrupt(tty)` → `copy_to_cooked(tty_table+tty)` |
| kernel/chr_drv/console.c | 39–47 | `ORIG_X/Y`, `ORIG_VIDEO_MODE/COLS/EGA_BX`(setup.s가 0x90000에 남긴 값) |
| kernel/chr_drv/console.c | 58–76 | 정적 변수: video_mem_start/end, origin, pos, x, y, state, attr |
| kernel/chr_drv/console.c | 445–500 | `con_write` 앞부분: `CHARS(write_q)`만큼 `GETCH` 후 state 0에서 인쇄 가능 문자를 `movw %ax,(pos)`로 VGA 메모리에 기록, 10/13/ERASE/8/9/7 처리, ESC → state 1 |
| kernel/chr_drv/console.c | 600–616 | `con_write` 끝: `set_cursor()` |
| kernel/chr_drv/console.c | 617–689 | `con_init`: 비디오 종류 판별(0xb0000/0xb8000), `set_trap_gate(0x21,&keyboard_interrupt)`, PIC 마스크 해제(`outb_p(inb_p(0x21)&0xfd,0x21)`), 0x61 포트 키보드 리셋 |
| kernel/chr_drv/serial.c | 53–59 | `rs_write`: 큐가 비어 있지 않으면 UART 송신 인터럽트 활성화(대비용) |
| kernel/chr_drv/tty_ioctl.c | 39–44 | `flush`: head=tail |
| kernel/chr_drv/tty_ioctl.c | 46–54 | `wait_until_sent`/`send_break` = 미구현(빈 함수) |
| kernel/chr_drv/tty_ioctl.c | 56–74 | `get_termios`/`set_termios`(바이트 복사, `change_speed`) |
| kernel/chr_drv/tty_ioctl.c | 115–204 | `tty_ioctl`: MAJOR 5(/dev/tty)는 `current->tty`, TCGETS/TCSETS/TCSETSF/TCFLSH/TIOCGPGRP/TIOCSPGRP/TIOCINQ 구현, 나머지 `-EINVAL` |
| fs/char_dev.c | 16–32 | `rw_ttyx`(minor 지정) / `rw_tty`(`current->tty`, 없으면 `-EPERM`) |
| fs/char_dev.c | 85–104 | `crw_table[]`(MAJOR 4=ttyx, 5=tty), `rw_char` 디스패치 |
| fs/read_write.c | 55–80 | `sys_read`: `S_ISCHR` → `rw_char(READ,inode->i_zone[0],…)` |
| fs/read_write.c | 83–96 | `sys_write`: `S_ISCHR` → `rw_char(WRITE,…)` |
| fs/open.c | 165–170 | open 시 리더 프로세스의 `current->tty` 설정과 `tty_table[].pgrp = current->pgrp` |
| kernel/sched.c | 110–120 | `schedule()` 앞부분: 시그널 받은 TASK_INTERRUPTIBLE을 RUNNING으로 |
| kernel/sched.c | 167–186 | `interruptible_sleep_on` |
| kernel/sched.c | 188–193 | `wake_up` |
| kernel/system_call.s | 101–119 | `ret_from_sys_call`: 사용자 모드 복귀 시 `signal` 비트 검사 → `do_signal` |
| kernel/printk.c | 21–41 | `printk`: vsprintf 후 fs=ds로 바꾸고 `_tty_write(0,…)` 호출 |
| include/termios.h | 83–106, 169–183 | iflag/oflag/lflag 상수(선언된 전체 목록 — 비교 슬라이드용) |

- 상태 변화도·비교 범위 (course-plan 원문 계승):
  - **상태 변화도 ①(데이터)**: 한 글자의 위치 — `[키보드 컨트롤러 0x60] → read_q(raw) → secondary(cooked) → 사용자 버퍼(put_fs_byte)`, 그리고 에코 분기 `→ write_q → VGA 메모리`. 각 전환의 원인(IRQ1 / do_tty_interrupt / tty_read 루프 / con_write), 변경되는 데이터(head, tail, secondary.data, pos/x/y), 유지 조건(FULL이면 폐기, EMPTY면 대기).
  - **상태 변화도 ②(태스크)**: read()를 부른 셸 태스크 — `TASK_RUNNING → TASK_INTERRUPTIBLE(secondary.proc_list에 매달림) → TASK_RUNNING`. 전환 원인: `sleep_if_empty` / `wake_up(&secondary.proc_list)` 또는 시그널(`schedule()` 110–120행). 유지 조건: `EMPTY(secondary) || (L_CANON && !secondary.data && LEFT>20)`.
  - **모드·선택지 비교 ①**: 범위 = `include/termios.h`에 선언된 c_iflag/c_oflag/c_lflag 플래그 전체. 각 플래그에 대해 `tty_io.c`가 실제로 검사하는지(grep 근거), 콘솔 초기값에 켜져 있는지, 어느 함수에서 쓰이는지.
  - **모드·선택지 비교 ②**: 범위 = `tty_ioctl`의 cmd 전체(TCGETS…TIOCSSOFTCAR). 구현/부분 구현/`-EINVAL` 분류.
  - **모드·선택지 비교 ③**: 범위 = 0.11 문자 장치 MAJOR 0~7(`crw_table[]`). 핸들러가 있는 것(1, 4, 5)과 NULL.

## 2. 전체 슬라이드 목록

| 번호 | 제목 | 유형 | 내용 상세 | 근거 소스 (src/) | 시각자료·캡처 |
|---|---|---|---|---|---|
| 01 | 13. 터미널 I/O | 표지 | 대제목 `13. 터미널 I/O` · 부제(핵심 질문 원문): "키보드에서 누른 글자가 read()까지 어떻게 전달되는가?" · 우상단 `Linux 0.11` 배지 + `1991`, 부제 한 줄 "Kernel.org 원본 src/ 기준 · 실행은 lab/ (QEMU i386)" · 회차 정보 `13/15 · 파트 F «터미널»` | — | 표지 배경: QEMU 콘솔에서 `ls` 타이핑 중인 캡처(lab, 수정 없음) · 표지 배지·푸터(00-common §1) |
| 02 | 핵심 질문과 오늘의 길 | 질문 | 핵심 질문 원문 큰 글씨: "키보드에서 누른 글자가 read()까지 어떻게 전달되는가?" · 오늘의 길: 10단계 미니 지도를 본문 크기로 배치, 오늘 실제 다루는 단계만 강조 · 이 회차는 질문→지도→배경→코드→상태도→비교→시연→정답→확인→정리 전 단계를 다님(빠짐없이 강조) | — | 10단계 미니 지도(00-common §3) |
| 03 | 과정 로드맵 — 오늘의 위치 | 로드맵 | 파트 A–G 15회차 타임라인에서 파트 F «터미널»의 13만 ORANGE 강조 — 파트 F의 단독 회차 · 완료(TEAL) 01–12 · 이후(MUTED) 14–15 · 오늘 한 줄 문구: "누른 글자가 세 개의 큐를 지나 잠든 read()를 깨운다 — 터미널 I/O" · 12→13·13→14 연결 화살표 문구는 §3 명세 · 원 "지도" 슬라이드의 11·12(블록 장치·파일 시스템) 대비·14(종합) 연결 내용 계승 | — | 로드맵 다이어그램(§3 명세, 전 회차 공통 골격) |
| 04 | 커널 전체 구조 — 오늘의 범위 | 구조 | chr_drv/ 계층의 kernel/chr_drv/keyboard.S·kernel/chr_drv/tty_io.c·kernel/chr_drv/console.c와 include/linux/tty.h를 진한 TEAL로 강조 · 오늘의 데이터 흐름 화살표(ORANGE): 키보드 IRQ 1 → keyboard_interrupt → put_queue(큐) → read_q → copy_to_cooked(secondary) → tty_read → 프로세스의 read() · 보조 화살표: 에코·출력 분기 write_q → con_write → VGA 메모리 · fs/read_write.c(sys_read의 S_ISCHR 분기)·fs/char_dev.c(rw_char 디스패치)는 흐름의 경유점으로 라벨 · 누적 강조(옅은 TEAL) 01–12 영역은 §3 명세 | kernel/chr_drv/keyboard.S · kernel/chr_drv/tty_io.c · kernel/chr_drv/console.c · include/linux/tty.h · fs/read_write.c:55–80 · fs/char_dev.c:85–104 | 커널 구조도(§3 명세, 전 회차 공통 골격) |
| 05 | 12회차에서 남긴 갈림길 | 코드 | `sys_read`(fs/read_write.c:55–80)에서 `S_ISCHR` 분기가 `rw_char`로 간다는 코드 6줄 · 파일 read와 장치 read가 같은 fd 인터페이스를 쓰지만 아래가 다르다는 그림 · 12회차 open("/dev/tty0")의 inode가 문자 장치로 끝나던 지점 복습 | fs/read_write.c:55–80 | 파일 read / 장치 read 갈림길 그림(§4) |
| 06 | 터미널이란 무엇인가 | 배경 | 1991년 PC의 "콘솔" = 키보드 + VGA 텍스트 화면, "rs" = 직렬 포트(0x3f8/0x2f8) · 0.11의 tty 3개(tty_table[0..2])를 표로 · 현대 가상 터미널·pty는 다루지 않음을 명시 | include/linux/tty.h:45–55 · kernel/chr_drv/tty_io.c:51–92 | tty_table[0..2] 3항 표 |
| 07 | raw와 cooked: 두 번 저장되는 글자 | 배경 | 키보드가 보내는 것은 글자가 아니라 스캔 코드 · 커널이 (1) 스캔 코드 → ASCII, (2) 줄 편집(백스페이스·^U)과 ^C 해석을 한 뒤에야 read()에 준다는 개념도 · "cooked"라는 용어를 소개 · 에코(echo) — 입력 글자을 되돌려 그리는 것은 셸이 아니라 커널 | kernel/chr_drv/keyboard.S:453–484 · kernel/chr_drv/tty_io.c:145–228 | raw/cooked 개념도(§4) |
| 08 | 원형 버퍼 1024바이트 — 개념 | 배경 | 고정 크기 배열 1024칸을 끝에서 처음으로 감아 쓰는 큐 그림 · head=쓰는 쪽(생산자가 전진), tail=읽는 쪽(소비자가 전진) · `& (TTY_BUF_SIZE-1)`로 감기는 모습 · FULL은 LEFT==0, 즉 한 칸은 항상 비워 둔다는 점 | include/linux/tty.h:14–30 | 원형 버퍼 링 그림(§4 — 오늘 핵심 시각 언어의 기초) |
| 09 | 원형 버퍼 1024바이트 — 코드 | 코드 | `struct tty_queue`(tty.h:16–22): data·head·tail·proc_list·buf 코드 · INC/EMPTY/LEFT/FULL/CHARS(24–30) 매크로 · GETCH는 buf[tail]을 읽고 tail 전진, PUTCH는 buf[head]에 쓰고 head 전진 · keyboard.S가 이 구조 오프셋을 하드코딩한다는 예고(슬라이드 16) | include/linux/tty.h:16–34 | 코드 인용 + 매크로별 head/tail 동작 화살표 |
| 10 | tty_struct의 세 큐 | 코드 | `struct tty_struct`(tty.h:45–53) 코드 · read_q(인터럽트가 씀) / secondary(copy_to_cooked가 씀, tty_read가 읽음) / write_q(tty_write가 씀, con_write가 비움)의 역할 그림 · `write` 함수 포인터가 콘솔은 `con_write`, rs는 `rs_write` | include/linux/tty.h:45–55 | 세 큐 역할 그림(§4) |
| 11 | 콘솔 tty의 초기 termios | 코드 | `tty_table[0]`(tty_io.c:51–65) 코드: iflag=ICRNL, oflag=OPOST\|ONLCR, lflag=ISIG\|ICANON\|ECHO\|ECHOCTL\|ECHOKE · `INIT_C_CC`(tty.h:63) 기본 제어 문자 · rs 두 개는 변환 플래그가 0(66–91) · 이 값들이 오늘 모든 분기의 기준 | kernel/chr_drv/tty_io.c:51–92 · include/linux/tty.h:57–63 | 코드 인용 + iflag/oflag/lflag 초기값 강조 |
| 12 | 키보드 인터럽트가 걸리기까지 | 코드 | `con_init`(console.c:683–684): `set_trap_gate(0x21,&keyboard_interrupt)`와 PIC 마스크 비트1 해제 · 4회차 IDT 그림을 재사용하여 IRQ1 → 벡터 0x21 → `_keyboard_interrupt` · 게이트 등록이 콘솔 초기화 안에 있다는 점 | kernel/chr_drv/console.c:617–689(683–684) | 4회차 IDT 그림 재사용 + IRQ1→0x21 경로(§4) |
| 13 | keyboard_interrupt 읽기 (1) | 코드 | keyboard.S:37–53 · 레지스터·ds/es 저장, `inb $0x60`으로 스캔 코드 읽기 · 0xe0/0xe1 접두 처리 · `call key_table(,%eax,4)` · 스캔 코드가 함수 테이블 인덱스라는 그림 | kernel/chr_drv/keyboard.S:37–53 | 코드 인용 + 스캔 코드→key_table 인덱스 그림(§4) |
| 14 | keyboard_interrupt 읽기 (2) | 코드 | keyboard.S:54–77 · 0x61 포트 bit7 토글(키보드 ack) · EOI `outb %al,$0x20` · `pushl $0; call _do_tty_interrupt`, 복원 후 `iret` · 인터럽트 안에서 C 함수(copy_to_cooked)를 호출한다는 점과 tty_io.c:328–341 주석 소개 | kernel/chr_drv/keyboard.S:54–77 · kernel/chr_drv/tty_io.c:328–341(주석) | 코드 인용 + 핸들러 타임라인(스캔 코드 읽기→ack→EOI→do_tty_interrupt→iret) |
| 15 | key_table과 do_self | 코드 | key_table(502–509) 발췌(0x1D=ctrl, 나머지 do_self)와 break 코드는 `none`(530–540) · `do_self`(453–484): mode 비트로 key_map/shift_map/alt_map 선택 · Ctrl이면 `subb $64` → 'c'(0x63)가 ^C(0x03)가 되는 계산을 표로 | kernel/chr_drv/keyboard.S:502–509, 530–540, 453–484 | key_table 발췌 + Ctrl 변환 계산 표(§4) |
| 16 | put_queue: read_q에 넣기 | 코드 | keyboard.S:88–110 전체 · `_table_list`(tty_io.c:99–103)의 첫 항목=콘솔 read_q, `buf(%edx,%ecx)`에 저장, `andl $size-1` · tail과 같아지면 폐기(`je 3f`), head 갱신 · proc_list가 있으면 state=0 · head/tail 오프셋(21–26행)이 tty.h 구조와 손으로 맞춰진 점을 주의 표시 | kernel/chr_drv/keyboard.S:88–110, 21–30 · kernel/chr_drv/tty_io.c:99–103 | 코드 인용 + read_q head/tail 포인터 그림(슬라이드 08·09 시각 언어 재사용) |
| 17 | 조합 키와 modifier 상태 | 코드 | ctrl/alt/unctrl/unalt(111–127)가 `mode` 바이트를 켜고 끔 · F1~F12는 `func_table`(236–241)의 ESC [ [ A 4바이트 시퀀스가 put_queue로 들어감 · 원본 config.h:19이 `KBD_FINNISH`를 선택함을 각주(lab 수정본 키맵은 확인 필요) | kernel/chr_drv/keyboard.S:111–127, 236–241, 245–261 | mode 비트·func_table 도식 |
| 18 | do_tty_interrupt → copy_to_cooked | 코드 | tty_io.c:342–345: `do_tty_interrupt(tty)` → `copy_to_cooked(tty_table+tty)` · 인터럽트 문맥에서 바로 cooked 처리로 넘어가는 호출 순서도: IRQ1 → keyboard_interrupt → put_queue → do_tty_interrupt(0) → copy_to_cooked(&tty_table[0]) · 호출 순서도이지 상태도가 아님을 명시 | kernel/chr_drv/tty_io.c:342–345 | 입력 호출 순서도(§4) |
| 19 | copy_to_cooked (1) 루프와 CR/NL | 코드 | tty_io.c:145–160 · `while(!EMPTY(read_q) && !FULL(secondary))`, `GETCH` · 13→10(ICRNL), IGNCR, INLCR, IUCLC · 콘솔은 ICRNL만 켜져 있으므로 Enter(13)가 10으로 바뀜 | kernel/chr_drv/tty_io.c:145–160, 28–49 | 코드 인용 + CR/NL 변환 미니 표 |
| 20 | copy_to_cooked (2) 줄 편집 — KILL(^U) | 코드 | tty_io.c:161–176 · ICANON일 때 KILL(^U)은 secondary.head를 줄 시작까지 DEC · 지우는 동안 L_ECHO면 write_q에 127을 넣어 화면에서도 지움(c<32면 127 두 번) · `tty->write(tty)`로 즉시 반영 | kernel/chr_drv/tty_io.c:161–176 | 코드 인용 + secondary.head 후퇴 화살표 그림 |
| 21 | copy_to_cooked (2) 줄 편집 — ERASE와 STOP/START | 코드 | tty_io.c:177–199 · ERASE(DEL=127)는 secondary.head를 한 칸 DEC, 줄 시작(10)·EOF 직전이면 무시 · 에코는 write_q에 127을 넣음 · STOP/START는 `tty->stopped`만 바꿈(콘솔 출력에서 stopped를 검사하는 곳은 없음 — grep `stopped` 결과: tty_io.c:60 초기값, 192·196 대입뿐, 각주) | kernel/chr_drv/tty_io.c:177–199 | 코드 인용 + ERASE 한 칸 후퇴 그림 |
| 22 | copy_to_cooked (3) ISIG와 ^C | 코드 | tty_io.c:200–209와 `tty_intr`(111–120) · ^C가 `INTR_CHAR`와 같으면 `tty_intr(tty,INTMASK)` → pgrp가 같은 모든 task의 `signal`에 SIGINT 비트 OR · 글자는 secondary에 넣지 않고 `continue` · 10회차의 `ret_from_sys_call`(system_call.s:101–119) → `do_signal`로 연결 | kernel/chr_drv/tty_io.c:200–209, 111–120 · kernel/system_call.s:101–119 | 코드 인용 + ^C→signal→do_signal 연결 그림(§4) |
| 23 | copy_to_cooked (4) 줄 카운트·에코·깨우기 | 코드 | tty_io.c:210–228 · 10 또는 EOF면 `secondary.data++`(완성된 줄 수) · ECHO면 write_q에 넣고 `tty->write(tty)` 즉시 호출(제어문자는 ECHOCTL로 ^X 표기) · `PUTCH(c,secondary)`, 루프 끝에 `wake_up(&tty->secondary.proc_list)` | kernel/chr_drv/tty_io.c:210–228 | 코드 인용 + wake_up 화살표(상태 변화도 ②로 연결) |
| 24 | tty_read (1) 잠들기 조건 | 코드 | tty_io.c:230–260 · VTIME/VMIN 처리(기본 VMIN=1, VTIME=0 → 그 분기 생략) · `current->signal`이면 break · `EMPTY(secondary) \|\| (L_CANON && !data && LEFT>20)`이면 `sleep_if_empty(&secondary)` · 정규 모드에서는 줄이 완성될 때까지 글자가 있어도 안 돌려준다는 점 | kernel/chr_drv/tty_io.c:230–260 | 코드 인용 + 잠들기 조건 논리식 강조 |
| 25 | tty_read (2) 복사와 반환 | 코드 | tty_io.c:261–288 · `GETCH(secondary,c)`, 10/EOF면 `data--` · EOF이고 ICANON이면 즉시 반환(길이 0 가능 → 사용자에겐 EOF) · `put_fs_byte(c,b++)`, 정규 모드는 한 줄이라도 읽었으면 break · 시그널로 깨어나 0바이트면 `-EINTR` | kernel/chr_drv/tty_io.c:261–288 | 코드 인용 |
| 26 | sleep_if_empty와 wake_up | 코드 | tty_io.c:122–128과 sched.c:167–186, 188–193 나란히 · `cli()` 후 `while(!signal && EMPTY)`로 `interruptible_sleep_on(&proc_list)` · `wake_up`은 proc_list가 가리키는 한 태스크의 state=0 · put_queue의 `movl $0,(%ecx)`(keyboard.S:106)도 같은 일을 read_q.proc_list에 하지만 0.11에서 read_q에 잠드는 코드는 없음(grep 근거 각주) | kernel/chr_drv/tty_io.c:122–128 · kernel/sched.c:167–186, 188–193 · kernel/chr_drv/keyboard.S:106 | 좌우 대조 코드 인용 |
| 27 | 핵심 그림: 'a'+Enter — 큐와 잠든 셸의 4컷 | 상태도 | 오늘의 핵심 시각자료: 입력 큐·대기·깨우기 상태 변화를 4컷으로 · (1) 셸이 read() 직후 — 세 큐 모두 빈 상태(head==tail, data=0), 셸 태스크 TASK_INTERRUPTIBLE로 secondary.proc_list에 매달림 · (2) 'a' 입력 — put_queue로 read_q.head +1, 셸은 잠든 채(data=0) · (3) copy_to_cooked — read_q.tail +1(GETCH), secondary.head +1, data=0(줄 미완성), 에코는 write_q→con_write, wake_up 후에도 잠들기 조건이 참이면 다시 잠듦 · (4) Enter — 13이 10으로(ICRNL), data 0→1, wake_up → 셸이 GETCH으로 'a', 10을 꺼내 put_fs_byte, secondary.tail 전진, sys_read 반환 2 | kernel/chr_drv/keyboard.S:88–110 · kernel/chr_drv/tty_io.c:122–128, 145–228, 230–288 | 핵심 4컷 다이어그램(§4 상세 명세 — 오늘의 핵심 시각자료) |
| 28 | 상태 변화도 ①: 글자 한 개의 위치 | 상태도 | 상태: 컨트롤러(0x60) → read_q → secondary → 사용자 버퍼; 분기 write_q → VGA · 전환 원인(IRQ1 / do_tty_interrupt / tty_read 루프 / con_write) · 변경 데이터(read_q.head / read_q.tail·secondary.head / secondary.tail·secondary.data / pos·x) · 유지 조건(FULL이면 폐기, EMPTY면 대기, FULL(secondary)이면 read_q에 남음) | kernel/chr_drv/keyboard.S:37–110 · kernel/chr_drv/tty_io.c:145–288 · kernel/chr_drv/console.c:445–500 | 상태 변화도 ①(§4 상세 명세) |
| 29 | 상태 변화도 ②: read()를 부른 태스크 | 상태도 | RUNNING → INTERRUPTIBLE(secondary.proc_list=current) → RUNNING · 전환 원인 3가지: wake_up(copy_to_cooked 끝), 시그널 보유 시 schedule()(sched.c:117–119), (VTIME 사용 시) alarm · 5·10회차 상태도와 같은 표기 · 유지 조건: 줄 미완성 && 시그널 없음 | kernel/chr_drv/tty_io.c:122–128, 227 · kernel/sched.c:110–120, 167–193 | 상태 변화도 ②(§4 상세 명세 — 5·10회차 상태도 표기 재사용) |
| 30 | 비교 ①: termios 플래그 — 참조되는 것 | 비교 | 표 열: 플래그 / tty_io.c가 검사(매크로 28–49행 + 사용처) / 콘솔 초기값 · 범위: include/termios.h 83–106(iflag), 169–183(lflag), oflag 99–106 전체 중 참조 그룹 · 참조됨: ICRNL·INLCR·IGNCR·IUCLC, OPOST·ONLCR·OCRNL·ONLRET·OLCUC, ISIG·ICANON·ECHO·ECHOCTL | include/termios.h:83–106, 169–183 · kernel/chr_drv/tty_io.c:28–49 | 참조 플래그 표(iflag/oflag/lflag 3분류) |
| 31 | 비교 ①: termios 플래그 — 선언만 된 것 | 비교 | 매크로만 있고 미사용: ECHOE·ECHOK·ECHOKE(정의 35–38행, 호출 없음) · 미참조: IXON·IXOFF·ISTRIP·INPCK·PARMRK·ECHONL·NOFLSH·TOSTOP·IEXTEN 등 · 표 하단 교훈: "선언됐다 ≠ 동작한다" | kernel/chr_drv/tty_io.c:28–49(35–38) · include/termios.h:83–106, 169–183 | 미사용·미참조 플래그 표 |
| 32 | 비교 ①-보충: c_cc 제어 문자 | 비교 | tty.h:36–43의 8개 매크로 중 copy_to_cooked가 쓰는 것(INTR, QUIT, ERASE, KILL, EOF, START, STOP)과 선언만 된 것(SUSPEND — grep 결과 사용처 없음) · 기본값 `INIT_C_CC` 해석표(^C=\003, DEL=\177, ^U=\025, ^D=\004 …) | include/linux/tty.h:36–43, 57–63 | INIT_C_CC 해석표 |
| 33 | 시연 A: 키 하나의 여정 (GDB) | 시연 | 중단점 `keyboard_interrupt`, `copy_to_cooked`, `tty_read` · 셸 프롬프트에서 'a' 한 번 · 각 중단점에서 `p tty_table[0].read_q.head/tail`, `p tty_table[0].secondary.head/tail/data`를 찍어 head가 1 전진 → secondary로 이동 → tty_read는 아직 잠든 채(줄 미완성)임을 기대 출력으로 · 보조: `b put_queue` 후 `p/x $al`(스캔 코드 0x1E), Enter 후 `tty_read` 루프 재진입(258–259행 이후)에서 걸림 | kernel/chr_drv/tty_io.c:99–103, 145–228, 230–288 · kernel/chr_drv/keyboard.S:37–110 | GDB 명령 블록 · 캡처 01–03(§5) |
| 34 | 시연 A 캡처 | 캡처 | GDB 로그 캡처 게시(lab, 수정 없음, `-S -s`) · 관찰과 추론 구분: head 값의 전진·data의 0 유지는 관찰, "Enter 전까지 셸이 잠들어 있다"는 코드 추론 · 각주: `keyboard_interrupt`는 어셈블리 심벌이라 `break`는 되지만 소스 줄 표시가 없음; 심벌 이름의 밑줄 접두 여부는 lab 툴체인 기준으로 확인 | kernel/chr_drv/tty_io.c:145–228, 230–260(관찰 대상) | materials/13-tty/captures/01-keyboard-interrupt-scan-code.png · 02-copy-to-cooked-secondary.png · 03-enter-tty-read-return.png(§5) |
| 35 | 시연 B: Enter와 깨어남, ^C와 -EINTR | 시연 | (1) Enter 입력 후 `copy_to_cooked` 끝(227행)에 중단점 → `p tty_table[0].secondary.data`=1, `p task[n]->state`가 0으로 · (2) `cat` 실행 후 ^C: `tty_intr`에 중단점, `p task[n]->signal`의 SIGINT 비트, 이어서 `do_signal` 중단점 · 기대: cat 종료, 프롬프트 복귀 | kernel/chr_drv/tty_io.c:200–228, 111–120 · kernel/system_call.s:101–119 | GDB 명령 블록 · 캡처 04·05(§5) |
| 36 | 시연 B 캡처 | 캡처 | QEMU 화면 + GDB 로그 · 코드 추론(시그널이 secondary에 들어가지 않음)과 관찰(cat이 죽고 ^C 글자 자체는 read로 전달되지 않음)을 구분해 표기 · 상태 변화도 ②의 전환 2가지(wake_up, 시그널)가 실제로 일어나는 컷과 연결 | kernel/chr_drv/tty_io.c:111–120, 200–209(관찰 대상) | materials/13-tty/captures/04-enter-wake-secondary-data.png · 05-sigint-tty-intr-do-signal.png(§5) |
| 37 | 시연 C: ioctl로 ECHO 끄기 | 시연 | 작은 사용자 프로그램(TCGETS → `c_lflag &= ~ECHO` → TCSETS → read 1줄 → 복원) · tty_ioctl.c:126–133 경로 · 기대: 입력이 화면에 안 보이다가 Enter 후 출력 · GDB `b set_termios`에서 `p/x tty->termios.c_lflag` 전후(0xa0b → 0xa03) · 사전 캡처 대체 가능(stty 바이너리가 lab 루트 FS에 있는지 확인 필요) | kernel/chr_drv/tty_ioctl.c:56–74, 126–133 | 사용자 프로그램 코드 블록 + GDB 명령 블록 · 캡처 06·07(§5) |
| 38 | 시연 C 캡처 | 캡처 | QEMU 화면(입력 비에코 → Enter 후 출력 → 복원)과 GDB c_lflag 전후 캡처 · 관찰 vs 추론 구분: c_lflag 값 변화는 관찰, "에코를 꺼도 입력은 큐에 그대로 쌓인다"는 코드 추론 · 각주: lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜 | kernel/chr_drv/tty_ioctl.c:56–74, 126–133(관찰 대상) | materials/13-tty/captures/06-noecho-ioctl-screen.png · 07-set-termios-clflag.png(§5) |
| 39 | 출력 경로: write() → tty_write | 코드 | sys_write(read_write.c:83–96) → rw_char → rw_ttyx → `tty_write`(tty_io.c:290–326) · OPOST/ONLCR: '\n' 앞에 13 삽입(cr_flag) · `sleep_if_full(&write_q)`, `tty->write(tty)`, 남으면 `schedule()` | fs/read_write.c:83–96 · fs/char_dev.c:16–32, 85–104 · kernel/chr_drv/tty_io.c:290–326 | 코드 인용 + 출력 경로 미니 순서도 |
| 40 | con_write: VGA 텍스트 메모리에 쓰기 | 코드 | console.c:445–470 · `CHARS(write_q)`만큼 GETCH, state 0에서 `movw %ax,(pos)`(문자+attr 2바이트), pos+=2, x++, 줄 끝이면 `lf()` · 10→lf, 13→cr, 127→del, 8→백스페이스, 9→탭, 7→sysbeep · 끝에 `set_cursor()`(600–616) · ESC 시퀀스 state 1/2는 범위 밖(간단 언급) | kernel/chr_drv/console.c:445–500, 600–616 | 코드 인용 + VGA 메모리 셀(문자+attr 2바이트) 그림 |
| 41 | con_init: 화면 종류와 인터럽트 등록 | 코드 | console.c:617–689 · setup.s가 0x90000에 남긴 ORIG_* (39–47)로 MDA/CGA/EGA 판별 → video_mem_start 0xb0000/0xb8000, 우상단에 "EGAc" 같은 표시 문자열 · `gotoxy(ORIG_X,ORIG_Y)`, 키보드 게이트·PIC·0x61 리셋 · 3회차 부팅 캡처의 우상단 문자열과 연결 | kernel/chr_drv/console.c:617–689, 39–47 | 코드 인용 + 3회차 부팅 캡처(우상단 문자열) 병치 |
| 42 | printk도 같은 길 | 코드 | printk.c:21–41: vsprintf 후 `push %fs; push %ds; pop %fs`로 fs를 커널 데이터로 바꾸고 `_tty_write(0, buf, i)` 호출 · 15회차에서 printk를 쓸 때 "tty_write는 잠들 수 있다"(sleep_if_full)는 주의의 근거 | kernel/printk.c:21–41 | 코드 인용 |
| 43 | 비교 ②: tty_ioctl의 명령 | 비교 | 범위: tty_ioctl.c:125–203의 모든 case · 구현(TCGETS/TCSETS/TCSETSW/TCSETSF, TCGETA/TCSETA*, TCFLSH, TIOCGPGRP/TIOCSPGRP, TIOCOUTQ, TIOCINQ) · 부분(TCSBRK — wait_until_sent/send_break가 빈 함수 46–54) · 미구현 `-EINVAL`(TCXONC, TIOCEXCL/NXCL, TIOCSCTTY, TIOCSTI, TIOCGWINSZ/SWINSZ, TIOCM*, TIOCG/SSOFTCAR) | kernel/chr_drv/tty_ioctl.c:125–203, 46–54 | 구현/부분/미구현 3분류 표 |
| 44 | 비교 ③: 문자 장치 MAJOR 0~7 | 비교 | 범위: char_dev.c:85–93 `crw_table[]` · 1=rw_memory(그 안에서도 ram/mem/kmem은 -EIO, 3=null, 4=port만 동작), 4=rw_ttyx, 5=rw_tty(current->tty 없으면 -EPERM) · 0,2,3,6,7은 NULL → `-ENODEV` · open.c:165–170의 리더 tty 결속도 함께 | fs/char_dev.c:85–104, 16–32 · fs/open.c:165–170 | MAJOR 0~7 핸들러 표 |
| 45 | rs 콘솔과의 차이(짧게) | 배경 | serial.c:53–59 `rs_write`는 큐에 글자가 있으면 UART 송신 인터럽트만 켬(비동기) · con_write는 호출 즉시 다 그림(동기) · 같은 tty_write가 `tty->write` 포인터 하나로 두 장치를 다룬다는 점만 짚음 · rs_io.s 상세는 범위 밖 | kernel/chr_drv/serial.c:53–59 | 콘솔(동기)/rs(비동기) 대비 도식 |
| 46 | 핵심 질문의 답 | 정답 | 전체 경로를 한 장에: IRQ1 → keyboard_interrupt → key_table/do_self → put_queue(read_q.head++) → do_tty_interrupt → copy_to_cooked(secondary.head++, data++, echo→write_q→con_write) → wake_up → tty_read(secondary.tail++, put_fs_byte) → sys_read 반환 · 각 화살표에 파일:줄 | kernel/chr_drv/keyboard.S:37–110 · kernel/chr_drv/tty_io.c:145–288 · fs/read_write.c:55–80 | 전체 경로 다이어그램(§4) |
| 47 | 오늘 만난 "0.11다운" 선택들 | 정리 | 큐 오프셋을 어셈블리에 수동 기입(keyboard.S:21–26) · 인터럽트 안에서 copy_to_cooked 직접 호출 · wake_up은 태스크 하나만 · 가득 차면 조용히 폐기(put_queue) · ECHOE/ECHOK 매크로 미사용 · 14회차 현대 커널 비교 예고 | kernel/chr_drv/keyboard.S:21–30, 88–110 · kernel/chr_drv/tty_io.c:28–49, 342–345 | 요점 카드 5매 |
| 48 | 이해 확인 | 확인 | 아래 "이해 확인 질문과 정답"(§6) 4문항 질문만 게시 · 정답은 클릭 후 표시 · 문항: make/break와 read_q.head / 정규 모드에서 줄 완성 전 반환 여부 / ^C의 secondary·read() / ECHOE와 백스페이스 에코 | kernel/chr_drv/keyboard.S:530–540 · kernel/chr_drv/tty_io.c:210–211, 256–257, 200–204, 285–286, 35, 182–187(정답 근거) | 문항 4개 텍스트 |
| 49 | 정리와 다음 회차 | 정리 | 세 큐·두 상태도·플래그 표 요약 · 14회차: `ls /` 한 줄이 1~13회차 전부를 지나가는 지도 · 오늘의 tty_read/tty_write가 그 지도의 시작과 끝 | —(14회차 예고) | 다음 회차 예고 박스 |

## 3. 앞부분 다이어그램 회차별 명세

### 슬라이드 03 로드맵 — 오늘 위치

- 파트: F «터미널» · 13/15 — 파트 F는 이 회차 하나뿐인 단독 회차. 완료(TEAL) 01–12, 오늘(ORANGE + 굵은 테두리) 13, 이후(MUTED) 14–15.
- 오늘 한 줄 문구: "누른 글자가 세 개의 큐를 지나 잠든 read()를 깨운다 — 터미널 I/O"
- 12→오늘 연결 화살표 문구: "12: open("/dev/tty0")이 문자 장치로 가면 — 파일 read가 장치 read로 갈라지는 지점을 봤다 → 13: 그 문자 장치 chr_drv/ 안에서 키보드의 글자가 read()까지 오는 길"
- 오늘→14 연결 화살표 문구: "13: 입력(tty_read)·출력(tty_write)으로 01–13의 양 끝을 채웠다 → 14: 이제 01–13 전부 — 셸 명령 한 줄(`ls /`)로 전부 잇는 종합"
- 원 "지도" 슬라이드(원 02) 내용 계승: 완료 상자 11·12 아래 "블록 장치·파일 시스템" 라벨로 오늘(문자 장치)과의 대비를 살리고, 이후 상자 14에는 "종합" 연결 라벨. 미니 지도 범례는 슬라이드 02 오늘의 길에서 계승.

### 슬라이드 04 커널 구조도 — 오늘 범위

- 하이라이트 파일(진한 TEAL): 문자 장치(kernel/chr_drv/) 계층의 kernel/chr_drv/keyboard.S(인터럽트 핸들러·put_queue·key_map), kernel/chr_drv/tty_io.c(세 큐·copy_to_cooked·tty_read·tty_write·tty_intr), kernel/chr_drv/console.c(con_write·con_init), include/linux/tty.h(tty_queue·tty_struct·tty_table).
- 오늘의 데이터 흐름 화살표(ORANGE, 주 화살표): 키보드 IRQ 1 → keyboard_interrupt(kernel/chr_drv/keyboard.S) → put_queue(큐) → read_q → copy_to_cooked(secondary) → tty_read(kernel/chr_drv/tty_io.c) → 프로세스의 read() — 사용자 공간의 read()가 커널 chr_drv/를 거쳐 다시 사용자 버퍼(put_fs_byte)로 돌아오는 화살표.
- 보조 화살표(ORANGE, 2번째 — 00-common §2가 허용하는 1–2개 안): 에코·출력 분기 — write_q → con_write(kernel/chr_drv/console.c) → VGA 텍스트 메모리.
- 흐름 경유점 라벨: fs/read_write.c(sys_read·sys_write의 S_ISCHR 분기), fs/char_dev.c(rw_char → crw_table 디스패치), fs/open.c(open 시 current->tty·pgrp 결속) — 오늘 흐름이 fs/ 누적 영역 위를 지나는 지점.
- 누적 강조(옅은 TEAL, 01–12): 파트 A — boot/bootsect.s·boot/setup.s·boot/head.s·init/main.c(01–03) / 파트 B — kernel/system_call.s·kernel/asm.s·kernel/traps.c(04), include/linux/sched.h·kernel/sched.c(05), kernel/fork.c(06) / 파트 C — mm/memory.c·mm/page.s(07–08) / 파트 D — fs/exec.c(09), kernel/exit.c·kernel/signal.c(10) / 파트 E — fs/buffer.c·kernel/blk_drv/ll_rw_blk.c·kernel/blk_drv/hd.c(11), fs/namei.c·fs/inode.c·fs/open.c·fs/read_write.c(12).

## 4. 다이어그램·시각 자료 제작 목록

| 슬라이드 | 자료 이름 | 형식 | 내용 명세 | 재사용(이전 회차) |
|---|---|---|---|---|
| 03 | 15회차 로드맵(13 강조) | 도형 다이어그램 | §3 명세 그대로 — 파트 A–G 골격, 13 ORANGE(파트 F 단독 상자), 01–12 TEAL, 14–15 MUTED, 연결 화살표 2 | 전 회차 공통 골격(00-common §2) |
| 04 | 커널 전체 구조도(chr_drv/ 강조) | 도형 다이어그램 | §3 명세 그대로 — keyboard.S·tty_io.c·console.c·tty.h 강조 + 데이터 흐름 화살표 2 + fs/ 경유점 라벨 | 전 회차 공통 골격 + 01–12 누적 영역 |
| 05 | 파일 read / 장치 read 갈림길 | 도형 | sys_read의 S_ISCHR 분기가 갈라지는 Y자 — 한쪽은 12회차(파일), 다른 쪽은 오늘(rw_char → chr_drv/) | 12회차 read 경로 그림 양식 |
| 07 | raw/cooked 개념도 | 도형 | 키보드 → (1) 스캔 코드→ASCII → (2) 줄 편집·^C 해석 → read(); 아래로 에코 분기(화면) | — |
| 08 | 원형 버퍼 링 그림 | 도형 | 1024칸 링(일부만 전개) — head(쓰는 인덱스)·tail(읽는 인덱스) 포인터, `& (TTY_BUF_SIZE-1)` 감김 표시, FULL=LEFT==0로 항상 한 칸 비움 | — |
| 10 | 세 큐 역할 그림 | 도형 | read_q(인터럽트가 씀) → secondary(copy_to_cooked→tty_read) / write_q(tty_write→con_write) 생산자·소비자 화살표, write 함수 포인터(con_write/rs_write) | 슬라이드 08 링 그림(동일 시각 언어) |
| 12 | IRQ1 → IDT 벡터 0x21 경로 | 도형 | 4회차 IDT 그림 위에 IRQ1 → 벡터 0x21 → `_keyboard_interrupt` 경로 + PIC 마스크 비트1 해제 표시 | 04회차 IDT 그림 |
| 13 | 스캔 코드 = key_table 인덱스 | 도형 | 스캔 코드 바이트(예: 0x1E) → `key_table(,%eax,4)` 4바이트 함수 포인터 → do_self/ctrl/none | — |
| 15 | Ctrl 변환 계산 표 | 표 | `subb $64`: 'c'(0x63) − 64 = ^C(0x03) 등 · mode 비트로 key_map/shift_map/alt_map 선택 | — |
| 18 | 입력 호출 순서도 | 도형 | IRQ1 → keyboard_interrupt → put_queue → do_tty_interrupt(0) → copy_to_cooked(&tty_table[0]) — 호출 순서도(상태도 아님) 명시 | — |
| 22 | ^C → 시그널 연결 그림 | 도형 | INTR_CHAR → tty_intr(tty,INTMASK) → pgrp가 같은 task들의 signal 비트 OR → ret_from_sys_call → do_signal | 10회차 시그널 전달 그림 양식 |
| 27 | 핵심 그림: 'a'+Enter 4컷 (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(4컷) | — |
| 28 | 상태 변화도 ① (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(상태 4 + 에코 분기) | — |
| 29 | 상태 변화도 ② (핵심) | 도형 상태 다이어그램 | 아래 상세 명세(태스크 상태 3노드) | 05·10회차 상태도 표기 |
| 46 | 전체 경로 다이어그램 | 도형 | 핵심 질문의 답 전체 경로 — 화살표마다 파일:줄 라벨 | 슬라이드 27 4컷의 압축판 |

핵심 시각자료 상세 명세 — "입력 큐·대기·깨우기" 상태 변화 (슬라이드 27·28·29가 같은 시각 언어를 공유; 슬라이드 08·16의 링 그림이 그 기초):

- 공통 시각 언어: 각 tty_queue는 1024칸 원형 띠(링)를 일부 전개해 그린다. 쓰는 위치 head(쓰기 인덱스)와 읽는 위치 tail(읽기 인덱스)은 링 위의 포인터, secondary는 추가로 채운 양을 세는 data(완성된 줄 수 카운터) 배지를 단다. proc_list에 매달린 잠든 태스크는 큐 아래 작은 태스크 아이콘(state 라벨 부착)으로 표시. 큐에 쌓인 내용 TEAL, 오늘의 전환(글자 이동·깨우기) ORANGE, 빈 큐·과거 상태 MUTED. 우하단 `Linux 0.11` 라벨.
- 슬라이드 27 (4컷): (1) 셸이 read() 호출 직후 — read_q·secondary·write_q 모두 빈 링(head==tail), secondary의 data 배지 0, 셸 태스크 아이콘이 secondary.proc_list에 매달려 TASK_INTERRUPTIBLE(sleep_if_empty, tty_io.c:122–128). (2) 'a' 입력 — IRQ1 화살표 → put_queue로 read_q.head 0→1(buf[0]='a'), secondary 그대로, 셸은 잠든 채(data=0). read_q.proc_list는 비어 있어 put_queue의 state=0 코드(keyboard.S:106)는 아무 일도 하지 않는다는 각주. (3) do_tty_interrupt → copy_to_cooked — read_q.tail 0→1(GETCH), secondary.head 0→1(PUTCH), data는 0 유지(줄 미완성), 에코 분기 write_q에 'a' PUTCH 후 `tty->write(tty)`=con_write 즉시 호출, 루프 끝 wake_up(&tty->secondary.proc_list) → 셸 state=0이지만 잠들기 조건 `L_CANON && !data && LEFT>20`이 참이어 다시 잠듦. (4) Enter 입력 — 13이 ICRNL로 10으로 변환되어 PUTCH, secondary.data 0→1, wake_up → 셸이 깨어나 GETCH으로 'a', 10을 꺼내 put_fs_byte(사용자 버퍼), secondary.tail 1→3, sys_read가 2를 반환. 각 컷에 변경 필드와 유발 코드(파일:줄) 라벨.
- 슬라이드 28 (상태 노드 4 + 분기 1): 글자의 위치 — 컨트롤러(0x60) / read_q / secondary / 사용자 버퍼(put_fs_byte), 분기 write_q → VGA 메모리. 전환 화살표마다 원인 라벨(IRQ1·keyboard_interrupt / do_tty_interrupt·copy_to_cooked / tty_read 루프·GETCH / con_write)과 변경 데이터 라벨(read_q.head — put_queue, read_q.tail — GETCH, secondary.head — PUTCH, secondary.tail — GETCH, secondary.data — 10/EOF, pos·x — con_write). 하단 유지 조건 표: FULL이면 폐기(put_queue), EMPTY면 대기(sleep_if_empty), FULL(secondary)이면 read_q에 남음.
- 슬라이드 29 (태스크 상태 3노드): TASK_RUNNING → TASK_INTERRUPTIBLE(secondary.proc_list=current) → TASK_RUNNING. 전환 원인 3가지 — wake_up(&secondary.proc_list)(copy_to_cooked 끝, tty_io.c:227), 시그널 보유 시 schedule()(sched.c:117–119), (VTIME 사용 시) alarm. 유지 조건: 줄 미완성 && 시그널 없음. 5·10회차 상태도와 같은 노드 모양·색 표기를 재사용. 캡처 슬라이드 34·36·38이 이 다이어그램의 해당 전환을 재지시한다.

## 5. 캡처 목록 (강사 시연)

| 시연 | 캡처 파일(materials/13-tty/captures/) | 명령·중단점 | 관찰 대상 | 대체 자료 |
|---|---|---|---|---|
| A 키 입력 | 01-keyboard-interrupt-scan-code.png | `b keyboard_interrupt` · 셸 프롬프트에서 'a' · `p tty_table[0].read_q.head` · `p tty_table[0].read_q.tail` · `b put_queue` 후 `p/x $al` | 스캔 코드 0x1E(make), read_q.head +1 전진 | 사전 캡처 `build/gdb-13-keystroke.txt`("기존 기록" 라벨) |
| A cooked | 02-copy-to-cooked-secondary.png | `b copy_to_cooked` · `n`으로 루프 한 바퀴 · `p tty_table[0].secondary.head` · `p tty_table[0].secondary.data` · `p tty_table[0].write_q.head` | secondary.head +1, data 0 유지(줄 미완성), write_q.head +1(에코) | 사전 캡처(위와 같은 파일) |
| A Enter | 03-enter-tty-read-return.png | Enter 입력 · `tty_read` 루프 재진입(258–259행 이후) 중단점 | secondary.data 0→1, 셸 깨어남, sys_read 반환 | 사전 캡처(위와 같은 파일) |
| B Enter·깨어남 | 04-enter-wake-secondary-data.png | `b copy_to_cooked` 끝(227행) · Enter · `p tty_table[0].secondary.data` · `p task[n]->state` | secondary.data=1, 태스크 state=0 | 사전 캡처 `build/gdb-13-sigint.txt` |
| B ^C | 05-sigint-tty-intr-do-signal.png | 셸에서 `cat` · `b tty_intr` · `b do_signal` · QEMU 창에서 Ctrl-C · `p tty->pgrp` · `p task[n]->signal` | SIGINT 비트(INTMASK=1<<1=2), do_signal signr=2, cat 종료·^C는 secondary에 들어가지 않음 | 사전 캡처(위와 같은 파일; cat이 없으면 sh의 read 대기로 같은 절차) |
| C ECHO 끄기 | 06-noecho-ioctl-screen.png | 게스트에서 20줄 C 프로그램 `ioctl(0,TCGETS,&t)` → `c_lflag &= ~ECHO` → TCSETS → read 1줄 → 복원 | 입력 중 화면 비에코 → Enter 후 줄 출력 → 복원 후 재에코 | 사전 캡처 `build/qemu-13-noecho.png`(게스트 gcc·바이너리 투입 불가 시) |
| C 플래그 변화 | 07-set-termios-clflag.png | `b set_termios` · `p/x tty->termios.c_lflag` 전후 | c_lflag 0xa0b(ISIG\|ICANON\|ECHO\|ECHOCTL\|ECHOKE = 01\|02\|010\|01000\|04000) → ECHO 비트(010) 꺼진 0xa03 | 사전 캡처(위와 같은 파일) |

모든 캡처 각주 필수: `lab/ 빌드 · QEMU i386 · GDB · 수정 없음/있음(내용) · 캡처 날짜`(00-common §7). 시연 공통 주의: 키 입력은 QEMU 창 포커스 필요; GDB가 멈춘 동안 누른 키의 break 코드가 뒤늦게 도착해 `keyboard_interrupt`가 두 번 걸림(두 번째는 `none`).

## 6. 이해 확인 질문과 정답

질문과 정답은 슬라이드 48에 게시(정답은 클릭 후 표시 — 원문 계승).

1. **Q.** 'a' 키를 눌렀다 뗐다. `keyboard_interrupt`는 몇 번 실행되고, `read_q.head`는 몇 번 전진하는가? **A.** 두 번(make 0x1E, break 0x9E). head는 한 번만 전진 — break 코드의 key_table 항목은 `none`(keyboard.S:530–540)이라 put_queue를 부르지 않는다.
2. **Q.** 정규 모드에서 "ab"까지 치고 Enter를 아직 안 눌렀다. `read()`는 2바이트를 돌려주는가? **A.** 아니다. tty_read(256–257행)는 `L_CANON && !secondary.data && LEFT>20`이면 `sleep_if_empty`로 다시 잠든다. secondary.data는 10 또는 EOF가 들어올 때만 증가(210–211행).
3. **Q.** ^C를 누르면 'c'(0x03)는 secondary에 들어가는가? 그 글자를 read()가 받는가? **A.** 들어가지 않는다. ISIG가 켜져 있으면 copy_to_cooked(200–204행)가 `tty_intr`만 호출하고 `continue`한다. read 중이던 태스크는 시그널 때문에 깨어나(sched.c:117–119) 0바이트면 `-EINTR`(tty_io.c:285–286)을 돌려받는다.
4. **Q.** `termios.h`에 `ECHOE`가 있고 tty_io.c:35에 `L_ECHOE` 매크로도 있다. ECHOE를 끄면 백스페이스 에코가 달라지는가? **A.** 달라지지 않는다. `L_ECHOE`는 정의만 되고 어디서도 호출되지 않는다(grep). ERASE 에코는 `L_ECHO`만 본다(182–187행).

## 7. 처음 등장하는 용어

| 용어 | 정의 | 첫 등장 슬라이드 |
|---|---|---|
| 스캔 코드(scan code) | 키보드 컨트롤러가 키 하나의 누름(make)/뗌(break)에 대해 보내는 1바이트 코드. 글자 코드가 아니다 | 07 |
| raw / cooked(정규, canonical) 모드 | 줄 편집·제어 문자 해석을 커널이 하는지(ICANON) 여부 | 07 |
| 에코(echo) | 입력 글자를 커널이 화면에 되돌려 그리는 것. 셸이 하는 일이 아니다 | 07 |
| VGA 텍스트 메모리(0xb8000) | 문자·속성 2바이트씩 80×25로 배열된 화면 메모리 | 06 |
| 원형 버퍼(ring buffer)와 head/tail | 고정 크기 배열을 끝에서 처음으로 감아 쓰는 큐 | 08 |
| termios / c_iflag·c_oflag·c_lflag·c_cc | 터미널 동작을 정하는 플래그 묶음과 제어 문자 배열 | 11 |
| EOI(End Of Interrupt) | PIC에 처리 완료를 알리는 `outb 0x20, 0x20` | 14 |
| pgrp / 전경 프로세스 그룹 | 같은 tty에 묶인 태스크 집합. `tty_intr`가 시그널을 보내는 범위 | 22 |

## 8. 흔한 오해 / 말하지 말아야 할 것

(course-plan 원문 계승)

- "키보드 인터럽트가 read()를 직접 깨운다"고 말하지 않는다. 깨우는 것은 `copy_to_cooked` 끝의 `wake_up(&secondary.proc_list)`이며, put_queue의 state=0(106행)은 read_q.proc_list에 대한 것으로 0.11에서는 사용되지 않는 경로다.
- "wake_up은 기다리는 모든 태스크를 깨운다"고 말하지 않는다. 0.11의 wake_up은 proc_list가 가리키는 태스크 하나의 state만 0으로 만들고, 나머지는 interruptible_sleep_on의 `goto repeat`(sched.c:176–179) 연쇄로 깨어난다.
- termios.h의 플래그 목록을 "0.11이 지원하는 기능 목록"으로 소개하지 않는다. 비교 슬라이드 25의 표가 기준이다.
- 콘솔 출력이 인터럽트 기반이라고 말하지 않는다. con_write는 호출 즉시 VGA 메모리에 동기로 쓴다. 인터럽트 기반인 것은 rs(serial.c:53–59)뿐이다.
- `tty->stopped`(^S/^Q)가 콘솔 출력을 실제로 멈춘다고 말하지 않는다. 값만 바뀌고 읽는 곳이 어디에도 없다(grep `stopped` 결과: tty_io.c:60 초기값, 192·196 대입뿐).
- 원본은 KBD_FINNISH 키맵(config.h:19)이라, US 키보드 기준 기호 위치 설명과 다를 수 있다. lab 수정본의 키맵 설정을 먼저 확인하고 말한다.
- 현대 리눅스의 line discipline, pty, 가상 콘솔 전환은 14회차 비교에서 개념만 언급하고 오늘은 다루지 않는다.

## 9. 120분 운영안

| 슬라이드 | 분 | 진행 |
|---|---|---|
| 01–05 | 5 | 핵심 질문, 로드맵·구조 지도, 12회차 복습(파일 read가 장치 read로 갈라지는 지점) |
| 06–11 | 15 | 배경: 터미널·tty·raw/cooked, 원형 버퍼, tty_struct의 세 큐 |
| 12–18 | 25 | 코드 ①: keyboard_interrupt → key_table → do_self → put_queue, do_tty_interrupt |
| 19–26 | 25 | 코드 ②: copy_to_cooked의 정규 처리, tty_read, sleep/wake, 시그널(^C) |
| 27–32 | 10 | 상태 변화도 3장(핵심 그림 4컷 포함), 비교 ①(termios 플래그) |
| 33–38 | 20 | 강사 시연 A/B/C(GDB로 키 하나의 여정, ^C → -EINTR, stty 없이 ioctl로 ECHO 끄기) |
| 39–44 | 12 | 출력 경로: tty_write, con_write, printk, con_init, 비교 ②③ |
| 45–47 | 5 | rs와 콘솔의 차이(짧게), 핵심 질문의 답, 전체 경로 재조립 |
| 48–49 | 3 | 이해 확인, 정리·다음 회차 예고 |

(단계별 분 배분은 course-plan 원안과 동일하게 유지했다 — 앞부분 5, 배경 15, 코드 25+25, 상태도·비교 10, 시연 20, 출력·비교 12, 답 5, 마무리 3.)

## 10. 기존 계획 대비 변경·증가

원천 슬라이드 계획 표(42행)의 모든 행은 버리지 않고 아래와 같이 계승·확장했다.

원→새 번호 대응: 원 01→01 · 원 02(지도)→03+04(로드맵·구조도로 대체·흡수, 새 02 핵심 질문 추가) · 원 03→05 · 원 04→06 · 원 05→07 · 원 06→08+09(분할) · 원 07→10 · 원 08→11 · 원 09→12 · 원 10→13 · 원 11→14 · 원 12→15 · 원 13→16 · 원 14→17 · 원 15→18 · 원 16→19 · 원 17→20+21(분할) · 원 18→22 · 원 19→23 · 원 20→24 · 원 21→25 · 원 22→26 · 원 23→28 · 원 24→29 · 원 25→30+31(분할) · 원 26→32 · 원 27→33 · 원 28→34 · 원 29→35 · 원 30→36 · 원 31→37 · 원 32→39 · 원 33→40 · 원 34→41 · 원 35→42 · 원 36→43 · 원 37→44 · 원 38→45 · 원 39→46 · 원 40→47 · 원 41→48 · 원 42→49. 신규 슬라이드: 27(핵심 그림), 38(시연 C 캡처).

| 구분 | 원 → 새 | 사유 |
|---|---|---|
| 표준 앞부분 확장 | 원 01 표지 + 원 02 지도(2장) → 새 01–04(4장) | 00-common §2 — "지도" 1장을 로드맵(03)·구조도(04) 2장 다이어그램으로 대체·흡수, 핵심 질문 전용 슬라이드(02) 추가 (+2) |
| 원형 버퍼 분할 | 원 06 → 새 08+09 | 개념 그림(링·head/tail·FULL)과 코드(tty_queue 구조·매크로)를 한 장에 담기엔 밀도가 높음 — 링 그림은 오늘 핵심 시각 언어의 기초여서 전용 슬라이드 배정 (00-common §5 우선순위 3) (+1) |
| 줄 편집 분할 | 원 17 → 새 20+21 | tty_io.c:161–199이 KILL(^U)·ERASE·STOP/START 세 기능을 코드 2스크린 분량으로 포함 (00-common §5 우선순위 2) (+1) |
| 비교 ① 분할 | 원 25 → 새 30+31 | 비교 축 3개(참조됨/매크로만/미참조) × 플래그 그룹 3개(iflag/oflag/lflag)를 한 표에 담기엔 밀도 과다 (+1) |
| 핵심 그림 신규 | (신규) 새 27 | 이 회차의 핵심 시각자료 "입력 큐·대기·깨우기"(원형 큐의 head/tail/data와 잠든 셸)를 4컷 시나리오로 전용 배정 — 상태 변화도 ①②(28·29)의 구체 도입 (00-common §5 우선순위 3) (+1) |
| 시연 C 캡처 신규 | (신규) 새 38 | 시연 A/B에는 캡처 슬라이드이 있는데 C만 없음 — 형식 통일 + "관찰 vs 추론" 구분 게시 (00-common §7) (+1) |
| 유형 어휘 정렬 | 원 01 "제목"→표지, 원 02 "지도"→로드맵/구조, 원 39 "정리"→정답, 원 41 "질문"→확인 | 00-common §3 유형 어휘로 통일(내용은 원문 그대로) |
| 계 | 42장 → 49장 (+7) | 목표 범위 44–50 안(00-common §5) |

## 11. PPTX 제작 전 확인 목록 (lab/ 의존 — 이 회차 분)

- lab/ 빌드의 심볼명(`keyboard_interrupt` vs `_keyboard_interrupt`, `do_tty_interrupt`·`copy_to_cooked` 등의 `_` 접두 유무)과 줄 번호 — 슬라이드 34 각주(어셈블리 심벌 `break` 동작·소스 줄 표시 없음)의 근거 확보 (course-plan "PPTX 제작 전 확인 목록"의 심볼명 항목).
- 루트 이미지 안 `cat` 유무(시연 B) — 없으면 sh의 read 대기(빈 프롬프트)에 대해 같은 절차로 대체.
- 게스트 gcc 유무(시연 C, course-plan 확인 목록의 15 해당분과 동일 계열) — 20줄 C 프로그램 컴파일이 안 되면 사전 빌드 바이너리 투입 절차 또는 사전 캡처(`build/qemu-13-noecho.png`)로 대체. `stty` 바이너리가 lab 루트 FS에 있는지도 확인.
- lab 수정본의 키맵 설정 확인 — 원본 config.h:19는 `KBD_FINNISH` 선택. 슬라이드 17 각주와 §8의 전제(US 키보드 기준 설명과 다를 수 있음).
- 사전 캡처 확보: `build/gdb-13-keystroke.txt` · `build/gdb-13-sigint.txt` · `build/qemu-13-noecho.png`(모두 "기존 기록" 라벨) — 신규 캡처는 `materials/13-tty/captures/<두자리순번>-<설명>.png` 규칙(§5의 01–07).
- 캡처 각주에 lab 빌드·수정 여부·캡처 날짜 필수 기재 — 키보드 입력 시연은 QEMU 창 포커스 필요, GDB 정지 중 누른 키의 break 코드 도착으로 `keyboard_interrupt`가 두 번 걸림(두 번째는 `none`).
