"""Build the handbook ebook (PDF + EPUB) from the MkDocs sources.

    python scripts/build_ebook.py [--version v1.0]

Pipeline:
  1. `mkdocs build -f mkdocs-ebook.yml` renders every nav page into a single
     print page (mkdocs-print-site-plugin), styled exactly like the site.
  2. Headless Chromium (Playwright) opens that page, so client-side JS
     (syntax highlighting, tabs) has run, and prints it to PDF.
  3. The rendered chapter HTML is handed to pandoc to produce the EPUB.

Requires: pip install -r requirements-ebook.txt, `playwright install chromium`
(or a local Chrome), and pandoc on PATH. Output goes to dist/.
"""

import argparse
import datetime
import functools
import http.server
import pathlib
import subprocess
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "build" / "ebook-site"
DIST_DIR = ROOT / "dist"
EBOOK_DIR = ROOT / "ebook"

TITLE = "Software Engineering Handbook"
AUTHOR = "Gaurav Bharti"
BASENAME = "software-engineering-handbook"


def default_version():
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return datetime.date.today().isoformat()


def build_print_site():
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-q", "-f", "mkdocs-ebook.yml"],
        cwd=ROOT,
        check=True,
    )


def serve(directory):
    """Serve the built site on a free localhost port; returns the base URL."""
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}"


def launch_browser(p):
    try:
        return p.chromium.launch()
    except Exception:
        # No bundled Chromium (e.g. local machine without `playwright install`):
        # fall back to the installed Google Chrome.
        return p.chromium.launch(channel="chrome")


def render(base_url, version):
    """Print the PDF and return the rendered chapter HTML for the EPUB."""
    pdf_path = DIST_DIR / f"{BASENAME}-{version}.pdf"
    footer = (
        '<div style="width:100%; font-size:8px; color:#888; padding:0 14mm;'
        ' font-family:Roboto, Helvetica, Arial, sans-serif;'
        ' display:flex; justify-content:space-between;">'
        f"<span>{TITLE} · {version}</span>"
        '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span>'
        "</div>"
    )

    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page()
        page.goto(f"{base_url}/print_page/", wait_until="networkidle", timeout=180_000)
        page.add_style_tag(path=str(EBOOK_DIR / "ebook.css"))
        page.emulate_media(media="print")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=footer,
            margin={"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"},
        )
        # EPUB input: the chapters only (pandoc builds its own TOC), with headings
        # shifted by nav depth so "Backend Engineering > Caching > Redis" nests
        # as h1 > h2 > h3 instead of every level being an h1.
        chapters = page.evaluate(
            """() => {
                const root = document.querySelector('#print-site-page').cloneNode(true);
                root.querySelectorAll('#print-site-cover-page, .headerlink, .md-clipboard, .md-code__nav')
                    .forEach(e => e.remove());
                root.querySelector('#print-page-toc')?.closest('section')?.remove();

                const depth = el => {
                    let d = 0;
                    for (let p = el.parentElement; p && p !== root; p = p.parentElement)
                        if (p.matches('section.md-section')) d++;
                    return d;
                };
                const retag = (h, level) => {
                    const n = document.createElement('h' + Math.min(level, 6));
                    for (const a of h.attributes) n.setAttribute(a.name, a.value);
                    n.innerHTML = h.innerHTML;
                    h.replaceWith(n);
                };
                for (const sec of root.querySelectorAll('section.md-section')) {
                    const h = sec.querySelector(':scope > h1');
                    if (h) retag(h, depth(sec) + 1);
                }
                // A page's first heading is its chapter title; everything after it nests
                // one level below, since most pages use several H1s for their sections.
                for (const sec of root.querySelectorAll('section.print-page:not(.md-section)')) {
                    const d = depth(sec);
                    const [title, ...rest] = sec.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    if (!title) continue;
                    retag(title, d + 1);
                    for (const h of rest) retag(h, +h.tagName[1] + d + 1);
                }
                // Flatten: pandoc reads <section> as a div and loses headings nested in it.
                for (const sec of [...root.querySelectorAll('section')].reverse())
                    sec.replaceWith(...sec.childNodes);
                return root.innerHTML;
            }"""
        )
        browser.close()

    print(f"PDF  -> {pdf_path.relative_to(ROOT)}")
    return chapters


def build_epub(chapters_html, version):
    html_path = ROOT / "build" / "ebook-chapters.html"
    html_path.write_text(
        f"<!doctype html><html><head><meta charset='utf-8'><title>{TITLE}</title>"
        f"</head><body>{chapters_html}</body></html>",
        encoding="utf-8",
    )
    epub_path = DIST_DIR / f"{BASENAME}-{version}.epub"
    subprocess.run(
        [
            "pandoc", str(html_path),
            "--from", "html",
            "--to", "epub3",
            "--output", str(epub_path),
            "--toc", "--toc-depth=3",
            "--split-level=3",
            "--css", str(EBOOK_DIR / "epub.css"),
            "--metadata", f"title={TITLE}",
            "--metadata", f"author={AUTHOR}",
            "--metadata", f"date={datetime.date.today().isoformat()}",
            "--metadata", "lang=en",
            "--quiet",
            "--metadata", f"subtitle=Edition {version}",
        ],
        check=True,
    )
    print(f"EPUB -> {epub_path.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", default=default_version())
    args = parser.parse_args()

    DIST_DIR.mkdir(exist_ok=True)
    build_print_site()
    chapters = render(serve(SITE_DIR), args.version)
    build_epub(chapters, args.version)


if __name__ == "__main__":
    main()
