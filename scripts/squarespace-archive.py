#!/usr/bin/env python3
"""
FDJ Squarespace Archive Script
Downloads all content, images, and structured data from lafamiliadejesus.com
Uses Squarespace JSON API for structured content extraction.
Image CDN: images.squarespace-cdn.com - append ?format=original for full resolution.
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE_URL = "https://www.lafamiliadejesus.com"
SITE_ID = "55f9d72de4b00b2feb733943"
ARCHIVE_DIR = Path(__file__).parent.parent
MEDIA_DIR = ARCHIVE_DIR / "media" / "images"
PAGES_DIR = ARCHIVE_DIR / "pages"
DATA_DIR = ARCHIVE_DIR / "data"
CONTENT_DIR = ARCHIVE_DIR / "content"

PAGES = {
    "home": "/",
    "ministerios": "/new-folder-4",
    "varones-valientes": "/varones-valientes",
    "isha": "/isha-1",
    "generacion-usada-x-dios": "/generacion-usada-x-dios-1",
    "soldaditos-de-jesus": "/soldaditos-de-jesus",
    "sermones": "/sermones-1",
    "podcast": "/podcast",
    "donar": "/donar",
    "beliefs": "/latin-church-north-houston",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es,en;q=0.5",
}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  JSON fetch failed for {url}: {e}")
        return None


def fetch_raw(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️  Raw fetch failed for {url}: {e}")
        return ""


def clean_sqsp_image_url(url):
    """Convert Squarespace CDN URL to full-resolution original."""
    if not url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    if "squarespace-cdn.com" in url or "squarespace.com/static" in url:
        # Remove format/sizing params and append ?format=original
        url = re.sub(r'\?.*$', '', url)
        url = url + "?format=original"
    return url


def extract_all_images(obj, found=None):
    """Recursively extract all image URLs from Squarespace JSON data."""
    if found is None:
        found = set()
    if isinstance(obj, dict):
        # Image URL fields
        for key in ("assetUrl", "imageUrl", "logoImageUrl", "thumbnailUrl",
                    "originalImageUrl", "mediaUrl", "url", "src"):
            val = obj.get(key)
            if isinstance(val, str) and ("squarespace" in val or "sqspcdn" in val):
                cleaned = clean_sqsp_image_url(val)
                if cleaned:
                    found.add(cleaned)
        # Recurse into all values
        for v in obj.values():
            if isinstance(v, (dict, list)):
                extract_all_images(v, found)
    elif isinstance(obj, list):
        for item in obj:
            extract_all_images(item, found)
    return found


def extract_text_content(obj, lines=None, depth=0):
    """Extract readable text content from Squarespace JSON."""
    if lines is None:
        lines = []
    if isinstance(obj, dict):
        # Text block
        if obj.get("type") == "text" and "value" in obj:
            lines.append(obj["value"])
        elif "body" in obj and isinstance(obj["body"], str):
            lines.append(obj["body"])
        elif "title" in obj and isinstance(obj["title"], str):
            lines.append(f"## {obj['title']}")
        elif "description" in obj and isinstance(obj["description"], str):
            lines.append(obj["description"])
        for v in obj.values():
            if isinstance(v, (dict, list)):
                extract_text_content(v, lines, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            extract_text_content(item, lines, depth)
    return lines


def url_to_filename(url):
    """Convert CDN URL to a safe, meaningful filename."""
    # Strip query params
    clean = re.sub(r'\?.*$', '', url)
    # Extract the path
    path = urllib.parse.urlparse(clean).path
    # Get last component
    parts = path.rstrip('/').split('/')
    # Find the original filename part (usually after hash/)
    filename = parts[-1] if parts else "image"
    filename = urllib.parse.unquote(filename)
    # Sanitize
    filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    if not filename or filename == "_":
        filename = f"image_{hash(url) & 0xFFFF:04x}.jpg"
    # Ensure extension
    if '.' not in filename.split('/')[-1]:
        filename += ".jpg"
    return filename


def download_file(url, dest_dir, filename=None):
    """Download a file to dest_dir/filename. Skip if exists."""
    if not filename:
        filename = url_to_filename(url)
    dest = dest_dir / filename
    # Handle collisions
    if dest.exists():
        print(f"  ✓ {filename}")
        return dest, True
    try:
        req = urllib.request.Request(url, headers={**HEADERS, "Accept": "image/*,*/*"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            # Check content type for real extension
            ct = resp.getheader("Content-Type", "")
            if "jpeg" in ct and not filename.lower().endswith((".jpg", ".jpeg")):
                filename = filename.rsplit(".", 1)[0] + ".jpg"
                dest = dest_dir / filename
            elif "png" in ct and not filename.lower().endswith(".png"):
                filename = filename.rsplit(".", 1)[0] + ".png"
                dest = dest_dir / filename
            dest.write_bytes(data)
            print(f"  ↓ {filename} ({len(data)//1024}KB)")
            return dest, True
    except Exception as e:
        print(f"  ✗ {filename}: {e}")
        return dest, False


def main():
    for d in [MEDIA_DIR, PAGES_DIR, DATA_DIR, CONTENT_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    all_image_urls = set()
    all_page_data = {}
    all_content = {}

    print("=" * 65)
    print("FDJ SQUARESPACE ARCHIVE")
    print(f"Site: {BASE_URL}")
    print(f"Site ID: {SITE_ID}")
    print("=" * 65)

    # ─── PHASE 1: Fetch all page JSON + HTML ───────────────────────
    print("\n📄 PHASE 1: Fetching page data via JSON API...")
    for name, path in PAGES.items():
        json_url = BASE_URL + path + "?format=json"
        print(f"\n  [{name}] {json_url}")

        data = fetch_json(json_url)
        if data:
            # Save raw JSON
            (DATA_DIR / f"{name}.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            all_page_data[name] = data

            # Extract images
            imgs = extract_all_images(data)
            print(f"    🖼️  {len(imgs)} images found")
            all_image_urls.update(imgs)

            # Extract text
            text_lines = extract_text_content(data)
            if text_lines:
                content_text = "\n\n".join(text_lines)
                (CONTENT_DIR / f"{name}.txt").write_text(content_text, encoding="utf-8")
                all_content[name] = text_lines
                print(f"    📝 {len(text_lines)} text blocks")
        else:
            print(f"    ⚠️  JSON unavailable - fetching raw HTML")
            html = fetch_raw(BASE_URL + path)
            if html:
                (PAGES_DIR / f"{name}.html").write_text(html, encoding="utf-8")
                # Try extracting squarespace CDN URLs from HTML
                cdn_pattern = r'https://images\.squarespace-cdn\.com/[^\s"\',)>]+'
                matches = re.findall(cdn_pattern, html)
                for m in matches:
                    cleaned = clean_sqsp_image_url(m)
                    if cleaned:
                        all_image_urls.add(cleaned)
                print(f"    📄 HTML saved, {len(matches)} CDN refs found")

        time.sleep(1.2)

    # ─── PHASE 2: Download the logo at full res ────────────────────
    logo_url = f"https://images.squarespace-cdn.com/content/v1/{SITE_ID}/1570677394284-CBF7LMJLIF2P58KU1HM6/Logo+FDJ+black.png?format=original"
    all_image_urls.add(logo_url)

    # ─── PHASE 3: Save master manifest ────────────────────────────
    manifest = {
        "site": BASE_URL,
        "site_id": SITE_ID,
        "platform": "Squarespace",
        "archived_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages": list(PAGES.keys()),
        "total_images": len(all_image_urls),
        "image_urls": sorted(all_image_urls),
        "contact": {
            "address": "14935 Lillja Road, Houston, TX, 77060",
            "phone": "+1 832-215-6080",
            "email": "lafamiliadejesustx@gmail.com",
        },
        "social": {
            "facebook": "https://www.facebook.com/fdjtx",
            "youtube": "https://www.youtube.com/channel/UC6USKJPB0orT8nprqciSjcg",
            "instagram": "https://www.instagram.com/fdjtx/",
        },
        "sister_churches": {
            "fdj_el_salvador": "https://www.facebook.com/lafamilia.dejesus",
            "rios_de_vida_reus": "http://riosdevidareus.es",
        },
    }
    (DATA_DIR / "archive-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"\n📋 Manifest saved — {len(all_image_urls)} total image URLs")

    # ─── PHASE 4: Download all images at full resolution ──────────
    print(f"\n📥 PHASE 4: Downloading {len(all_image_urls)} images at full resolution...")
    print("-" * 65)

    url_list = sorted(all_image_urls)
    success, failed = 0, 0
    for i, url in enumerate(url_list, 1):
        print(f"[{i:02d}/{len(url_list)}]", end=" ")
        filename = url_to_filename(url)
        # Avoid duplicate filenames
        existing = list(MEDIA_DIR.glob(f"{filename.rsplit('.', 1)[0]}*"))
        if existing:
            filename = f"{filename.rsplit('.', 1)[0]}_{i:02d}.{filename.rsplit('.', 1)[-1]}"
        _, ok = download_file(url, MEDIA_DIR, filename)
        if ok:
            success += 1
        else:
            failed += 1
        time.sleep(0.6)

    # ─── SUMMARY ──────────────────────────────────────────────────
    downloaded = list(MEDIA_DIR.iterdir())
    total_size = sum(f.stat().st_size for f in downloaded if f.is_file())

    print(f"\n{'=' * 65}")
    print(f"✅ ARCHIVE COMPLETE")
    print(f"   Pages archived:  {len(all_page_data)}/{len(PAGES)}")
    print(f"   Images downloaded: {success} / {len(url_list)}")
    print(f"   Failed:          {failed}")
    print(f"   Total size:      {total_size / 1024 / 1024:.1f} MB")
    print(f"   Location:        {ARCHIVE_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    main()
