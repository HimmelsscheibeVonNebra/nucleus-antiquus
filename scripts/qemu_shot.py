#!/usr/bin/env python3
"""qemu_shot — Linux 0.11 실제 화면·GDB 세션 자동 캡처 (Docker QEMU 기반).

사용법 (프로젝트 루트에서):
  python3 scripts/qemu_shot.py boot   OUT.png [--wait 초]        # 부팅 화면
  python3 scripts/qemu_shot.py type   OUT.png "echo hi\\nls /\\n"  # 부팅 후 키 입력 화면
  python3 scripts/qemu_shot.py sym    do_timer                    # System.map 주소 조회
  python3 scripts/qemu_shot.py gdb    OUT.png CMDS.gdb [--key 초:텍스트]
      CMDS.gdb 의 {sym:이름} 은 lab/System.map 주소(0x…)로 치환된다.
      --key "3:a\\n" — gdb 실행 3초 후 모니터로 키를 보낸다(인터럽트 유발용).

출력 PNG 는 실제 QEMU VGA 스크린덤프(screendump) 또는 실측 GDB 배치 출력의
터미널 렌더링이다. 캡처 환경: lab/ 빌드 · QEMU(i386, TCG) · -snapshot · 네트워크 없음.
"""

import argparse
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "nucleus-qemu:latest"
DOCKERFILE = """FROM debian:bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \\
    qemu-system-x86 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
"""
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MON_PORT = 4444   # 컨테이너 내 QEMU 모니터
GDB_PORT = 1234   # 컨테이너 내 gdbstub


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw).stdout


def ensure_image():
    ids = sh(["docker", "images", "-q", IMAGE]).strip()
    if not ids:
        subprocess.run(["docker", "build", "-t", IMAGE, "-"], input=DOCKERFILE,
                       text=True, check=True, capture_output=True)


class Qemu:
    """headless QEMU in docker: monitor·gdbstub 포트를 호스트로 매핑."""

    def __init__(self, extra_args=()):
        ensure_image()
        self.mon = free_port()
        self.gdb = free_port()
        args = ["docker", "run", "-d", "--rm",
                "-v", f"{ROOT}:/work", "-w", "/work",
                "-p", f"127.0.0.1:{self.mon}:{MON_PORT}",
                "-p", f"127.0.0.1:{self.gdb}:{GDB_PORT}",
                IMAGE, "qemu-system-i386",
                "-accel", "tcg", "-m", "16M", "-boot", "a",
                "-display", "none",
                "-drive", "file=lab/Image,format=raw,if=floppy",
                "-drive", "file=lab/hdc-0.11.img,format=raw,if=ide",
                "-nic", "none", "-snapshot",
                "-monitor", f"tcp:0.0.0.0:{MON_PORT},server,nowait",
                *extra_args]
        self.cid = sh(args).strip()[:12]
        self._wait_port(self.mon)

    def _wait_port(self, port, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    return
            except OSError:
                time.sleep(0.3)
        raise RuntimeError(f"port {port} not ready")

    def monitor(self, cmd, timeout=6):
        with socket.create_connection(("127.0.0.1", self.mon), timeout=3) as s:
            s.settimeout(timeout)
            time.sleep(0.2)
            try:
                s.recv(4096)                       # (qemu) 배너 버림
            except OSError:
                pass
            s.sendall(cmd.encode() + b"\n")
            data = b""
            end = time.time() + timeout
            while time.time() < end:
                try:
                    chunk = s.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                data += chunk
                if b"(qemu)" in data[-16:]:
                    break
            return data.decode("utf-8", "replace")

    def screendump(self, out_png: Path):
        self.monitor("screendump /tmp/dump.ppm")   # 컨테이너 내부 경로
        time.sleep(0.4)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(out_png) + ".ppm"
        subprocess.run(["docker", "cp", f"{self.cid}:/tmp/dump.ppm", tmp],
                       check=True, capture_output=True)
        from PIL import Image
        Image.open(tmp).save(out_png)
        Path(tmp).unlink(missing_ok=True)
        return out_png

    def send_text(self, text, settle=1.5):
        for key in text_to_keys(text):
            self.monitor(f"sendkey {key}")
            time.sleep(0.03)
        time.sleep(settle)

    def stop(self):
        subprocess.run(["docker", "kill", self.cid], capture_output=True)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


KEYMAP = {" ": "spc", "\n": "ret", "\t": "tab", "-": "minus", "=": "equal",
          "[": "bracket_left", "]": "bracket_right", ";": "semicolon",
          "'": "apostrophe", "`": "grave_accent", "\\": "backslash", ",": "comma",
          ".": "dot", "/": "slash", "_": "shift-minus", "+": "shift-equal",
          "?": "shift-slash", "!": "shift-1", "@": "shift-2", "#": "shift-3",
          "$": "shift-4", "%": "shift-5", "^": "shift-6", "&": "shift-7",
          "*": "shift-8", "(": "shift-9", ")": "shift-0", ":": "shift-semicolon",
          '"': "shift-apostrophe", "<": "shift-comma", ">": "shift-dot",
          "~": "shift-grave_accent", "{": "shift-bracket_left",
          "}": "shift-bracket_right", "|": "shift-backslash"}


def text_to_keys(text):
    keys = []
    for ch in text:
        if ch in KEYMAP:
            keys.append(KEYMAP[ch])
        elif ch.isalpha():
            keys.append(("shift-" + ch.lower()) if ch.isupper() else ch.lower())
        elif ch.isdigit():
            keys.append(ch)
        else:
            raise ValueError(f"매핑 없는 문자: {ch!r}")
    return keys


def symbol_addr(name):
    text = (ROOT / "lab/System.map").read_text()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2] == name:
            return f"0x{parts[0]}"
    raise KeyError(f"System.map에 심볼 없음: {name}")


def render_text_png(text, out_png, header):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(FONT, 19)
    small = ImageFont.truetype(FONT, 15)
    lines, width = [], 0
    for raw in text.rstrip().splitlines():
        for i in range(0, max(len(raw), 1), 100):
            seg = raw[i:i + 100]
            lines.append(seg)
            width = max(width, small.getlength(seg) if False else font.getlength(seg))
    pad, lh = 28, 30
    W = int(width) + pad * 2 + 6
    H = pad * 2 + lh * (len(lines) + 1) + 12
    img = Image.new("RGB", (max(W, 900), max(H, 260)), (8, 20, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 44], fill=(13, 37, 49))
    d.text((pad, 11), header, font=small, fill=(0x75, 0xD5, 0xC5))
    y = 58
    for seg in lines:
        d.text((pad, y), seg, font=font, fill=(0xE8, 0xE6, 0xDC))
        y += lh
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)


def cmd_boot(out, wait):
    q = Qemu()
    try:
        time.sleep(wait)
        q.screendump(out)
    finally:
        q.stop()
    print(f"captured {out}")


def cmd_type(out, text, wait):
    q = Qemu()
    try:
        time.sleep(wait)
        q.send_text(text, settle=2.0)
        q.screendump(out)
    finally:
        q.stop()
    print(f"captured {out}")


def cmd_gdb(out, cmds_path, key):
    q = Qemu(extra_args=["-S", "-gdb", f"tcp:0.0.0.0:{GDB_PORT}"])
    try:
        raw = Path(cmds_path).read_text()
        body = []
        for line in raw.splitlines():
            body.append(re.sub(r"\{sym:([A-Za-z0-9_]+)\}",
                               lambda m: symbol_addr(m.group(1)), line))
        script = "\n".join(body)
        import tempfile as _tf
        script_file = _tf.NamedTemporaryFile("w", suffix=".gdb", delete=False)
        script_file.write(script + "\n")
        script_file.close()
        gdb_proc = subprocess.Popen(
            ["gdb", "-q", "-batch",
             "-ex", "set pagination off", "-ex", "set confirm off",
             "-ex", "set height 0", "-ex", "set width 0",
             "-ex", "target remote 127.0.0.1:%d" % q.gdb,
             "-x", script_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        if key:
            delay, text = key.split(":", 1)
            time.sleep(float(delay))
            q.send_text(text, settle=0.5)
        try:
            out_text, _ = gdb_proc.communicate(script, timeout=90)
        except subprocess.TimeoutExpired:
            gdb_proc.kill()
            out_text, _ = gdb_proc.communicate()
        render_text_png(out_text or "(gdb 출력 없음)", out,
                        "gdb — target remote :1234 · Linux 0.11 lab/ 빌드 · QEMU i386 TCG · 실측")
    finally:
        q.stop()
    print(f"captured {out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("boot"); b.add_argument("out"); b.add_argument("--wait", type=float, default=6)
    t = sub.add_parser("type"); t.add_argument("out"); t.add_argument("text"); t.add_argument("--wait", type=float, default=6)
    s = sub.add_parser("sym"); s.add_argument("name")
    g = sub.add_parser("gdb"); g.add_argument("out"); g.add_argument("cmds"); g.add_argument("--key")
    a = ap.parse_args()
    if a.cmd == "boot":
        cmd_boot(Path(a.out), a.wait)
    elif a.cmd == "type":
        cmd_type(Path(a.out), a.text, a.wait)
    elif a.cmd == "sym":
        print(symbol_addr(a.name))
    elif a.cmd == "gdb":
        cmd_gdb(Path(a.out), a.cmds, a.key)


if __name__ == "__main__":
    main()
