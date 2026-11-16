# 회차별 상세 슬라이드 제작 계획 — 인덱스

- 원천 설계: [`../course-plan.md`](../course-plan.md) (15회차 PPTX 전체 설계, 2026-11-08)
- 이 디렉터리의 파일은 course-plan을 **슬라이드 단위로 확장한 제작 직전 계획**이다.
  PPTX 제작(`scripts/make_slides.py` 계열 확장)은 이 계획을 입력으로 한다.
- 산출물은 회차당 **PPTX 하나뿐** (`output/NN-<slug>.pptx`, CLAUDE.md). 다른 발표 형식 없음.

## 공통 규격 (모든 회차에 적용 — 각 계획 파일은 반복 기술하지 않음)

[`00-common.md`](00-common.md):

1. **Linux 0.11 버전 표시** — 표지 배지(1991) + 전 슬라이드 푸터 `Linux 0.11 커널 강좌 · NN/15` + 코드 캡션 `src/파일:줄`.
2. **표준 앞부분 01–04** — 표지 / 핵심 질문+오늘의 길 / **과정 로드맵 다이어그램(현재 회차 강조)** / **커널 전체 구조 다이어그램(오늘 범위 강조)**. 기존 계획의 "15회차 지도" 1장을 이 두 다이어그램으로 대체·확장했다.
3. **상단 미니 지도** — 본문 전 슬라이드에 10단계 진행 띠, 현재 단계 ORANGE 강조.
4. **장수 정책** — 기존 38–42장 → 44–50장 확장 허용.
5. 색 팔레트(make_slides.py 동일), 캡처·출처 규칙, 회차별 문서 템플릿.

## 회차별 계획 파일

| 회차 | 파트 | 제목 | 계획 파일 | 장수(기존→계획) |
|---|---|---|---|---|
| 01 | A 입문·부팅 | CPU·어셈블리 입문과 부팅부터 셸까지 | [01-overview.md](01-overview.md) | 42(제작분)→48 |
| 02 | A 입문·부팅 | x86 보호 모드와 소스 읽기 도구 | [02-protected-mode.md](02-protected-mode.md) | 40→46 |
| 03 | A 입문·부팅 | 부팅과 커널 초기화 | [03-boot-init.md](03-boot-init.md) | 40→47 |
| 04 | B 실행의 길 | 인터럽트·예외·시스템 콜 | [04-interrupts-syscall.md](04-interrupts-syscall.md) | 42→48 |
| 05 | B 실행의 길 | 태스크와 스케줄링 | [05-scheduling.md](05-scheduling.md) | 42→48 |
| 06 | B 실행의 길 | fork()와 프로세스 생성 | [06-fork.md](06-fork.md) | 42→48 |
| 07 | C 메모리 | 주소 변환과 페이지 관리 | [07-paging.md](07-paging.md) | 41→47 |
| 08 | C 메모리 | 페이지 폴트와 Copy-on-Write | [08-page-fault-cow.md](08-page-fault-cow.md) | 40→46 |
| 09 | D 프로그램의 일생 | exec()와 프로그램 실행 | [09-exec.md](09-exec.md) | 41→47 |
| 10 | D 프로그램의 일생 | 종료·대기·시그널 | [10-exit-signal.md](10-exit-signal.md) | 40→46 |
| 11 | E 파일·저장 | 버퍼 캐시와 블록 장치 | [11-buffer-cache.md](11-buffer-cache.md) | 38→46 |
| 12 | E 파일·저장 | 파일 시스템: inode·경로 탐색·I/O | [12-filesystem.md](12-filesystem.md) | 38→44 |
| 13 | F 터미널 | 터미널 I/O | [13-tty.md](13-tty.md) | 42→49 |
| 14 | G 종합·실습 | 종합: 셸 명령 한 줄의 전체 경로와 현대 커널 비교 | [14-capstone.md](14-capstone.md) | 40→46 |
| 15 | G 종합·실습 | 커널 수정 실습: 새 시스템 콜과 스케줄러 변경 | [15-kernel-lab.md](15-kernel-lab.md) | 42→48 |

총 약 610장 → 704장. 장수의 목표 범위는 44–50장(00-common §5)이며 위 값은 각 계획 문서 서두의
선언과 일치한다(2026-11-08 검증: 15개 문서 전수 일치, 번호 연속·유형 어휘·표준 앞부분 01–04 반영 확인).

## 제작 순서 제안

1. 회차 순서대로 `materials/slide-plans/NN-*.md` 확정 (원천: course-plan 해당 절).
2. 회차별 캡처 확보 → `materials/<slug>/captures/` (계획 §5 목록).
3. `scripts/make_slides.py`에 공통 프레임(배지·푸터·미니 지도·로드맵·구조도 도형) 구현 후
   회차별 본문 채움. `scripts/check_slides.py`에 버전 표시·미니 지도 검사 추가.
4. 완성: `output/NN-<slug>.pptx`.

## 메모

- 기존 `output/*.odp`, `output/*.html`은 폐기 대상(CLAUDE.md). 이 계획과 무관하다.
- 소스 줄 번호는 Kernel.org 원본 `src/` 기준. `lab/` 빌드 심볼·줄 차이는 각 계획 §11 확인 목록에서
  제작 시점에 검증한다.
