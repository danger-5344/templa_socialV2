import asyncio
import tempfile
from pathlib import Path
from django.core.files.base import ContentFile

# Snapshot defaults
SNAPSHOT_WIDTH = 800
SNAPSHOT_HEIGHT = 600
SNAPSHOT_BG = "#ffffff"  # white background

HTML_WRAPPER = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{
    margin: 0;
    background: {bg};
    font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }}
  .canvas {{
    width: 100%;
    height: 100%;
    overflow: auto;
    padding: 16px;
    box-sizing: border-box;
  }}
  /* Avoid super long emails pushing beyond viewport; let it scroll */
  .content {{
    width: 600px;
    margin: 0 auto;
  }}
</style>
</head>
<body>
  <div class="canvas">
    <div class="content">
      {inner_html}
    </div>
  </div>
</body>
</html>
"""

async def _render_with_playwright(full_html: str, width: int, height: int) -> bytes:
    from playwright.async_api import async_playwright

    # Write HTML to a temp file and open with file:// to avoid spinning a server
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "preview.html"
        html_path.write_text(full_html, encoding="utf-8")

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height, "deviceScaleFactor": 1})
            await page.goto(html_path.as_uri(), wait_until="load")
            # Optional: wait a tick for web fonts/images
            await page.wait_for_timeout(200)
            png_bytes = await page.screenshot(full_page=False, type="png")
            await browser.close()
            return png_bytes

def render_html_to_snapshot_content(html: str, width: int = SNAPSHOT_WIDTH, height: int = SNAPSHOT_HEIGHT, bg: str = SNAPSHOT_BG) -> ContentFile:
    """Render the given HTML into a PNG snapshot and return a Django ContentFile."""
    full_html = HTML_WRAPPER.format(inner_html=html or "<div></div>", bg=bg)
    png = asyncio.run(_render_with_playwright(full_html, width, height))
    return ContentFile(png)
