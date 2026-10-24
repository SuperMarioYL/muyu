#!/usr/bin/env python3
"""Record docs/assets/demo-muyu-score.gif from a REAL terminal session.

How it works (no simulated output, ever):
  1. spawn bash in a pty, type each demo command character by character
     (the pty echoes the typing — what you see is what was typed);
  2. stream the command's real output through pyte, a VT100 emulator,
     snapshotting the screen after every chunk, with wall-clock timing;
  3. render the frames with Pillow and assemble the GIF.

This is the macOS-local fallback used when vhs cannot capture frames;
docs/demo.tape remains the CI-side regeneration path (same demo script).

Note: this records the offline score/check loop. The rewrite pass needs a
configured MUYU_API_KEY; its before/after outputs ship as examples/*.md and
the full-loop gif is a manual residue step (BUILD_SETUP_NEXT_STEPS.md).

Usage: python3 docs/record_demo.py
Requires: muyu importable in the recording venv, pip packages pyte + pillow,
macOS system fonts Menlo + Hiragino Sans GB.
"""

import os
import pty
import select
import sys
import tempfile
import time
import unicodedata

import pyte
from PIL import Image, ImageDraw, ImageFont

COLS, ROWS = 118, 37
CELL_W, CELL_H = 10, 20
BG = (10, 7, 13)
FG = (253, 238, 246)
ACCENT = (230, 86, 106)
MUTED = (140, 126, 130)

TYPE_DELAY = 0.018      # per keystroke
QUIET_DONE = 0.35       # silence that marks a finished command
FRAME_MIN = 0.04        # minimum frame duration
TRAIL_PAUSE = 2.0

MENLO = "/System/Library/Fonts/Menlo.ttc"
CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"

COMMANDS = [
    "muyu score examples/draft-1.md",
    "muyu score examples/draft-2.md",
    "muyu check examples/native-1.md --baseline 40",
    "muyu presets",
]


def display_width(text):
    w = 0
    for ch in text:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


class Recorder:
    def __init__(self):
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.frames = []  # (duration_seconds, Image)
        self.last_snap = None

    def snapshot(self, duration):
        img = Image.new("RGB", (COLS * CELL_W, ROWS * CELL_H), BG)
        draw = ImageDraw.Draw(img)
        cy, cx = self.screen.cursor.y, self.screen.cursor.x
        for y in range(ROWS):
            for x in range(COLS):
                ch = self.screen.buffer[y][x].data
                if not ch or ch == " ":
                    continue
                if unicodedata.east_asian_width(ch) in ("W", "F"):
                    font = FONT_CJK
                else:
                    font = FONT_ASCII
                draw.text((x * CELL_W, y * CELL_H + 2), ch, font=font, fill=FG)
        # block cursor
        draw.rectangle(
            [cx * CELL_W, cy * CELL_H, (cx + 1) * CELL_W - 1, (cy + 1) * CELL_H - 1],
            fill=(60, 45, 42),
        )
        if self.frames and self.frames[-1][1] == img:
            self.frames[-1] = (self.frames[-1][0] + duration, img)
        else:
            self.frames.append((max(duration, FRAME_MIN), img))
        self.last_snap = img

    def feed(self, data, duration):
        self.stream.feed(data)
        self.snapshot(duration)

    def read_until_prompt(self, master, timeout=20.0):
        """Read until a fresh shell prompt line appears (or timeout)."""
        start = last_read = time.time()
        buf = b""
        while time.time() - start < timeout:
            r, _, _ = select.select([master], [], [], 0.03)
            if r:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                buf += data
                last_read = time.time()
                self.feed(data, 0.04)
                continue
            if b"$ " in buf.replace(b"\r\n", b"\n").split(b"\n")[-1] and time.time() - last_read > QUIET_DONE:
                break
        return buf

    def type_command(self, master, command):
        for ch in command:
            os.write(master, ch.encode())
            self.feed(b"", 0)  # echo arrives asynchronously; read loop handles it
            deadline = time.time() + TYPE_DELAY
            while time.time() < deadline:
                r, _, _ = select.select([master], [], [], 0)
                if r:
                    try:
                        data = os.read(master, 65536)
                    except OSError:
                        return
                    if data:
                        self.feed(data, TYPE_DELAY)
                else:
                    time.sleep(0.002)
        os.write(master, b"\r")
        start = last_read = time.time()
        while time.time() - start < 25.0:
            r, _, _ = select.select([master], [], [], 0.03)
            if r:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                self.feed(data, 0.05)
                last_read = time.time()
            elif time.time() - last_read > QUIET_DONE:
                break
        self.snapshot(TRAIL_PAUSE / 3)


def record(master, commands):
    rec = Recorder()
    rec.read_until_prompt(master)
    rec.snapshot(0.6)
    for i, cmd in enumerate(commands):
        rec.type_command(master, cmd)
        print(f"  [{i + 1}/{len(commands)}] {cmd}", file=sys.stderr)
    rec.snapshot(TRAIL_PAUSE)
    return rec


def main():
    out_path = os.path.join(os.path.dirname(__file__), "assets/demo-muyu-score.gif")
    # run from the repo root so the data/ walk-up finds tells + platforms and
    # the examples/ paths resolve
    workdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env.update({
        "TERM": "xterm-256color",
        "PS1": "$ ",
        "COLUMNS": str(COLS),
        "LINES": str(ROWS),
        "BASH_SILENCE_DEPRECATION_WARNING": "1",
    })

    pid, master = pty.fork()
    if pid == 0:
        os.chdir(workdir)
        os.execvpe("bash", ["bash", "--noprofile", "--norc"], env)

    import fcntl
    import struct
    import termios

    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))

    rec = record(master, COMMANDS)
    os.close(master)
    os.waitpid(pid, 0)
    transcript = os.environ.get("MUYU_DEMO_TRANSCRIPT")
    if transcript:
        with open(transcript, "w") as fh:
            for line in rec.screen.display:
                fh.write(line.rstrip() + "\n")

    frames = [img for _, img in rec.frames]
    durations = [int(d * 1000) for d, _ in rec.frames]
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size = os.path.getsize(out_path)
    print(f"wrote {out_path} ({len(frames)} frames, {size / 1024:.0f} KiB)", file=sys.stderr)


if __name__ == "__main__":
    FONT_ASCII = ImageFont.truetype(MENLO, 17)
    FONT_CJK = ImageFont.truetype(CJK, 17)
    main()
