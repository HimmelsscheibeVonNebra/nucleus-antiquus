# nucleus-antiquus — 작업 규칙

## 강의 자료 형식: PPTX만 (only pptx)

- 회차별 강의 자료의 산출물은 **PPTX 하나뿐**이다. `output/NN-<slug>.pptx`.
- ODP, HTML, PDF, Markdown 슬라이드 등 **다른 발표 형식은 만들지 않는다**. 검토·배포용 변환본도 요청이 없으면 만들지 않는다.
- 기존 `output/*.odp`, `output/*.html`은 폐기 대상이며 갱신하지 않는다.
- 슬라이드 생성은 `scripts/make_slides.py` 계열로 재현 가능하게 하고, 결과는 `scripts/check_slides.py`로 검사한다.
- 슬라이드에는 실제 터미널 화면(QEMU 부팅 캡처, GDB 로그, 셸 출력)을 포함한다. 캡처가 없으면 사전 캡처(`build/boot.png` 등)를 "기존 기록"으로 표시한다.

## 과정 구조

- 15회차, 회당 120분, 이론+실습 통합. 회차 구성과 슬라이드 계획은 `materials/course-plan.md`를 따른다.
- 읽기 기준 소스는 `src/`(Kernel.org 원본), 실행·수정본은 `lab/`. 둘을 혼동하지 않고 슬라이드 인용은 `src/` 줄 번호를 쓴다.
- 자료 언어는 한국어, 코드·식별자·파일명은 원문.
