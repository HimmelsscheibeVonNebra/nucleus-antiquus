#!/usr/bin/env python3
"""Check the session-01 deck (48 slides, PPTX-only) without third-party packages.

기준: materials/slide-plans/01-overview.md · 공통 규격 materials/slide-plans/00-common.md
검사: 장수, Linux 0.11 버전 표시(머리글·배지·푸터), 본문 10단계 미니 지도(05장부터),
페이지 번호, 편집 가능한 도형, 로드맵·구조도 필수 요소, 코드 캡션(src/ 원본 줄),
선수 개념이 원본 코드보다 먼저 등장, 캡처 이미지 삽입("기존 기록" 대체 라벨).
"""

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
STAGES = ["질문", "지도", "배경", "코드", "상태도", "비교", "시연", "정답", "확인", "정리"]
EXPECTED_SLIDES = 48
FOOTER = "Linux 0.11 커널 강좌 · 01/15 · 01-overview"


def slide_texts(archive, paths):
    texts = []
    for path in paths:
        tree = ET.fromstring(archive.read(path))
        texts.append("".join(node.text or "" for node in tree.findall(".//a:t", NS)))
    return texts


def main():
    with zipfile.ZipFile(ROOT / "output/01-overview.pptx") as archive:
        assert archive.testzip() is None, "Damaged PPTX archive"
        paths = sorted((name for name in archive.namelist()
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
                       key=lambda name: int(re.search(r"slide(\d+)", name)[1]))
        assert len(paths) == EXPECTED_SLIDES, \
            f"Expected {EXPECTED_SLIDES} slides, found {len(paths)}"

        trees = [ET.fromstring(archive.read(path)) for path in paths]
        texts = ["".join(node.text or "" for node in tree.findall(".//a:t", NS))
                 for tree in trees]
        joined = "\n".join(texts)

        for number, tree, text in zip(range(1, EXPECTED_SLIDES + 1), trees, texts):
            assert "LINUX 0.11" in text, f"Slide {number}: missing header version mark"
            assert FOOTER in text, f"Slide {number}: missing Linux 0.11 footer"
            assert f"{number:02d} / {EXPECTED_SLIDES}" in text, f"Slide {number}: page number"
            assert len(tree.findall(".//p:sp", NS)) >= 8, \
                f"Slide {number}: missing editable shapes"
            if number >= 5:
                for label in STAGES:
                    assert label in text, f"Slide {number}: missing stage '{label}'"

        # 표준 앞부분 (00-common §2)
        assert "1991" in texts[0] and "Linux 0.11" in texts[0], "Slide 1: missing badge"
        assert "셸이 나오기 전에 누가 실행되는가?" in texts[0], "Slide 1: missing question"
        for label in STAGES:
            assert label in texts[1], f"Slide 2: missing today-road '{label}'"
        for part in ["«입문·부팅»", "«실행의 길»", "«메모리»", "«프로그램의 일생»",
                     "«파일·저장»", "«터미널»", "«종합·실습»", "오늘"]:
            assert part in texts[2], f"Slide 3 roadmap: missing '{part}'"
        for node in ["bootsect.s", "setup.s", "head.s", "main.c", "lib/",
                     "system_call.s", "blk_drv", "chr_drv", "IRQ"]:
            assert node in texts[3], f"Slide 4 structure: missing '{node}'"

        # 본문 필수 내용 (계획 §2 대응)
        for required in [
                "피연산자 순서", "pushl $7", "popl %eax", "설명용 예시",
                "Virtual-8086", "Ring 3", "CR0.PG", "EFLAGS.IF",
                "O_RDONLY", "O_WRONLY", "O_RDWR", "BIOS", "lmsw", "jmpi 0,8",
                "move_to_user_mode", "for(;;) pause()", 'execve("/bin/sh"',
                "관찰", "추론", "task 0"]:
            assert required in joined, f"Missing required content: {required}"

        # 코드 캡션 — src/ 원본 줄 번호 (계획 §1 읽을 소스 범위)
        captions = {28: "src/boot/setup.s:191-193", 30: "src/boot/head.s:198-218",
                    35: "src/init/main.c:126-137", 36: "src/include/asm/system.h:1-14",
                    38: "src/init/main.c:138-148", 41: "src/init/main.c:172-175",
                    42: "src/init/main.c:194-200", 40: "src/include/fcntl.h:7-10"}
        for number, caption in captions.items():
            assert caption in texts[number - 1], f"Slide {number}: missing caption {caption}"

        # 선수 개념이 원본 코드보다 먼저 (배경 → 코드 순서)
        for concept in ["피연산자 순서", "레지스터", "선택자는 주소가 아니라"]:
            assert joined.index(concept) < joined.index("src/boot/setup.s:191-193"), \
                f"Prerequisite comes too late: {concept}"

        # 캡처 이미지 (CLAUDE.md — 없으면 사전 캡처를 '기존 기록'으로)
        media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        assert media, "No embedded capture image"
        captures = ROOT / "materials/01-overview/captures"
        have_live = any((captures / name).exists()
                        for name in ["01-qemu-boot.png", "03-shell-commands.png"])
        for number in (25, 44):
            has_pic = b"<p:pic" in archive.read(paths[number - 1])
            assert has_pic, f"Slide {number}: no embedded capture"
            if not have_live:
                assert "기존 기록" in texts[number - 1], \
                    f"Slide {number}: fallback capture must carry '기존 기록' label"

    print(f"PASS: {EXPECTED_SLIDES} slides — version marks, footers, 10-stage maps, "
          "roadmap/structure diagrams, code captions, prerequisites, captures")


if __name__ == "__main__":
    main()
