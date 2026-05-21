"""Drive the deployed gemini-multi-agent-orchestra Cloud Run app through
Playwright, record real screen footage of the 3-agent orchestra
functioning, save as MP4.

Output: ~60-90s WebM/MP4 showing the actual deployed Streamlit dashboard
loading, accepting a research question, walking the researcher → analyst
→ writer orchestra through the Bright Data MCP tools, and rendering the
verbatim labeled-section answer. This is the "footage that shows the
Project functioning on the platform(s) for which it was built" that
DoraHacks judges expect.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "https://gemini-multi-agent-orchestra-1029931682737.us-central1.run.app/"
OUT_DIR = Path("/Users/ubl/gemini-multi-agent-orchestra/.video-build")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_DIR = OUT_DIR / "playwright-videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    print("[1/4] launching Chromium (headed but offscreen)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        print(f"[2/4] navigating to {URL} ...")
        page.goto(URL, wait_until="networkidle", timeout=120_000)
        # Streamlit takes a beat to render after networkidle.
        page.wait_for_selector("text=gemini-multi-agent-orchestra", timeout=60_000)
        print("    dashboard rendered")
        time.sleep(2)

        # Make sure the sidebar question is what the demo narrates.
        question = (
            "Rank the top 3 AI coding agents launched in May 2026 by "
            "adoption and cite their announcement URLs verbatim."
        )
        # The Streamlit textarea is the first textarea on the page.
        textareas = page.locator("textarea")
        if textareas.count() > 0:
            textareas.first.fill(question)
            print(f"    question set: {question[:60]}...")
            time.sleep(1.5)

        # Click "Run orchestra" — Streamlit's buttons have a wrapping
        # kind=primary.
        print("[3/4] clicking Run orchestra and waiting for the writer's "
              "response...")
        page.locator("button", has_text="Run orchestra").first.click()
        # Wait for the spinner to appear (means the orchestra started).
        page.wait_for_selector("text=Running the orchestra", timeout=120_000)
        print("    orchestra started running")
        # Wait for that text to disappear (writer done).
        page.wait_for_selector("text=Running the orchestra",
                               state="detached", timeout=300_000)
        print("    orchestra finished")
        # Wait for the final HANDOFF TRACE label to confirm full render.
        try:
            page.wait_for_selector("text=HANDOFF TRACE", timeout=60_000)
        except Exception:
            page.wait_for_selector("text=ANSWER", timeout=30_000)
        print("    final answer rendered")
        # Dwell on the final result so the recording captures it clearly.
        time.sleep(5)
        # Scroll through the answer to show all sections.
        page.mouse.wheel(0, 200)
        time.sleep(2)
        page.mouse.wheel(0, 200)
        time.sleep(2)
        page.mouse.wheel(0, 300)
        time.sleep(2)
        page.mouse.wheel(0, 300)
        time.sleep(3)

        print("[4/4] closing context to flush the recording...")
        context.close()
        browser.close()

    # Find the recorded webm
    webms = sorted(VIDEO_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if not webms:
        sys.exit("no recording produced")
    webm = webms[-1]
    size = webm.stat().st_size / (1024 * 1024)

    # Transcode to MP4 with H.264 + AAC silence (so it concats cleanly later).
    mp4 = OUT_DIR / "real_footage.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(webm),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-shortest",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k",
        str(mp4),
    ], check=True)

    # Probe duration
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    print(f"\nDONE: {mp4}  ({size:.1f} MB webm, {float(dur):.1f}s mp4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
