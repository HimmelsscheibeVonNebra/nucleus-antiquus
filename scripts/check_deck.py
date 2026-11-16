#!/usr/bin/env python3
"""공용 덱 검사기 — 사용: /usr/bin/python3 scripts/check_deck.py scripts/make_NN_<slug>.py

덱 모듈의 SESSION(장수·슬러그·회차)과 CHECKS(captions/required/prereq/
structure_nodes/capture_slides)를 읽어 PPTX를 검사한다.
검사: 장수 · Linux 0.11 머리글/푸터/페이지 번호 · 본문 10단계 미니 지도(05장부터) ·
표지 배지 · 로드맵 7파트 · 구조도 필수 노드 · 코드 캡션(src/ 원본 줄) ·
필수 내용 · 선수개념 순서 · 캡처(실제 이미지 또는 '실측 아님' 예상 출력 패널).
"""

import importlib.util
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
STAGES = ["질문", "지도", "배경", "코드", "상태도", "비교", "시연", "정답", "확인", "정리"]
PARTS = ["«입문·부팅»", "«실행의 길»", "«메모리»", "«프로그램의 일생»",
         "«파일·저장»", "«터미널»", "«종합·실습»"]


def main():
    deck_path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / "output"
    spec = importlib.util.spec_from_file_location("deck_mod", deck_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    S, C = mod.SESSION, getattr(mod, "CHECKS", {})
    slug, total, no = S["slug"], S["total"], S["no"]

    with zipfile.ZipFile(out_dir / f"{slug}.pptx") as archive:
        assert archive.testzip() is None, "Damaged PPTX archive"
        paths = sorted((n for n in archive.namelist()
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                       key=lambda n: int(re.search(r"slide(\d+)", n)[1]))
        assert len(paths) == total, f"Expected {total} slides, found {len(paths)}"
        footer = f"Linux 0.11 커널 강좌 · {no}/15 · {slug}"
        texts, pics = [], []
        for path in paths:
            tree = ET.fromstring(archive.read(path))
            texts.append("".join(node.text or "" for node in tree.findall(".//a:t", NS)))
            pics.append(b"<p:pic" in archive.read(path))
        for number, tree, text in zip(range(1, total + 1),
                                      [ET.fromstring(archive.read(p)) for p in paths], texts):
            assert "LINUX 0.11" in text, f"Slide {number}: missing header version mark"
            assert footer in text, f"Slide {number}: missing footer"
            assert f"{number:02d} / {total}" in text, f"Slide {number}: page number"
            assert len(tree.findall(".//p:sp", NS)) >= 8, f"Slide {number}: few editable shapes"
            if number >= 5:
                for label in STAGES:
                    assert label in text, f"Slide {number}: missing stage '{label}'"
        assert "1991" in texts[0] and "Linux 0.11" in texts[0], "Slide 1: missing badge"
        assert S["question"].split("\n")[0][:12] in (texts[0] + texts[1]), \
            "Slide 1/2: missing core question"
        for part in PARTS:
            assert part in texts[2], f"Slide 3 roadmap: missing '{part}'"
        assert "오늘" in texts[2], "Slide 3 roadmap: missing today mark"
        for node in C.get("structure_nodes", ["system_call.s"]):
            assert node in texts[3], f"Slide 4 structure: missing '{node}'"
        joined = "\n".join(texts)
        for required in C.get("required", []):
            assert required in joined, f"Missing required content: {required}"
        for number, caption in C.get("captions", {}).items():
            assert caption in texts[number - 1], \
                f"Slide {number}: missing caption {caption}"
        for concept, caption in C.get("prereq", []):
            assert joined.index(concept) < joined.index(caption), \
                f"Prerequisite comes too late: {concept}"

        captures = ROOT / "materials" / slug / "captures"
        capture_slides = C.get("capture_slides", [])
        have_live = captures.exists() and any(captures.glob("*.png"))
        for number in capture_slides:
            if have_live:
                assert pics[number - 1], f"Slide {number}: no embedded capture"
            else:
                assert ("실측 아님" in texts[number - 1]
                        or "기존 기록" in texts[number - 1]), \
                    f"Slide {number}: capture slide needs image or 예상 출력(실측 아님) panel"
    print(f"PASS: {slug} — {total} slides, version marks, maps, roadmap/structure, "
          "captions, prerequisites, captures")


if __name__ == "__main__":
    main()
