#!/usr/bin/env python3
"""Check the exported first-session deck without third-party packages."""

import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
MAP = ["전체 지도", "CPU·메모리", "어셈블리", "부팅·보호", "init·셸", "관찰·정리"]
EXPECTED_SLIDES = 42


def main():
    with zipfile.ZipFile(ROOT / "output/01-overview.pptx") as archive:
        assert archive.testzip() is None, "Damaged PPTX archive"
        paths = sorted((name for name in archive.namelist()
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
                       key=lambda name: int(re.search(r"slide(\d+)", name)[1]))
        assert len(paths) == EXPECTED_SLIDES, f"Expected {EXPECTED_SLIDES} slides, found {len(paths)}"
        all_text = []
        for number, path in enumerate(paths, 1):
            tree = ET.fromstring(archive.read(path))
            text = "".join(node.text or "" for node in tree.findall(".//a:t", NS))
            assert all(label in text for label in MAP), f"Slide {number}: missing situation map"
            assert f"{number:02d}" in text, f"Slide {number}: missing page number"
            assert len(tree.findall(".//p:sp", NS)) >= 10, "Missing editable shapes"
            all_text.append(text)
        joined = "\n".join(all_text)
        for required in ["상태 변화도", "권한 변화도", "exec 변화도", "Virtual-8086",
                         "Ring 0", "Ring 1", "Ring 2", "Ring 3", "CR0.PG", "EFLAGS.IF",
                         "src/init/main.c", "src/boot/setup.s", "src/boot/head.s",
                         "메모리 주소와 값", "레지스터", "어셈블리 읽기", "피연산자 순서",
                         "pushl $7", "popl %eax", "BIOS", "O_RDONLY", "O_WRONLY", "O_RDWR"]:
            assert required in joined, f"Missing required content: {required}"
        for concept, source in [("어셈블리 읽기", "src/boot/setup.s:191-193"),
                                ("페이징: CPU", "src/boot/head.s:213-218"),
                                ("프로그램·프로세스·PID", "src/init/main.c:136-140")]:
            assert joined.index(concept) < joined.index(source), f"Prerequisite comes too late: {concept}"
    pdf = ROOT / "output/01-overview.pdf"
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    assert re.search(rf"Pages:\s+{EXPECTED_SLIDES}\b", info), "PDF slide count mismatch"
    text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    pages = text.split("\f")
    assert len(pages) == EXPECTED_SLIDES + 1, "Rendered page count mismatch"
    assert all("LINUX 0.11" in page for page in pages[:EXPECTED_SLIDES]), "Blank rendered slide"
    assert "전원 투입" in text and "Virtual-8086" in text, "Missing rendered text"
    print(f"PASS: {EXPECTED_SLIDES} PPTX/PDF slides, editable shapes, maps, prerequisites, diagrams, modes")


if __name__ == "__main__":
    main()
