#!/usr/bin/env python3
"""
FDJ Archive Extractor
Fetches all pages of lafamiliadejesus.com and downloads all wixstatic.com media at full resolution.
Wix images are served with resize params; stripping them gives the original file.
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "https://www.lafamiliadejesus.com"
ARCHIVE_DIR = Path(__file__).parent.parent
MEDIA_DIR = ARCHIVE_DIR / "media" / "images"
PAGES_DIR = ARCHIVE_DIR / "pages"
DATA_DIR = ARCHIVE_DIR / "data"

PAGES = {
    "home": "/",
    "ministerios": "/new-folder-4",
    "varones-valientes": "/varones-valientes",
    "isha": "/isha-1",
    "generacion-usada-x-dios": "/generacion-usada-x-dios-1",
    "soldaditos-de-jesus": "/soldaditos-de-jesus",
    "iglesias-hermanas": "/iglesias-hermanas",
    "sermones": "/sermones-1",
    "podcast": "/podcast",
    "donar": "/donar",
    "donate": "/donate-mentor",
    "beliefs": "/latin-church-north-houston",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def fetch_page(url):
    """Fetch raw HTML from a page."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}")
        return ""

def extract_wixstatic_urls(html):
    """Extract all unique wixstatic.com media URLs from HTML/JS."""
    patterns = [
        # Standard image pattern with optional resize params
        r'https://static\.wixstatic\.com/media/[A-Za-z0-9_~\-\.]+(?:/v1/[^"\'>\s,)]+)?',
        # Direct media hash
        r'static\.wixstatic\.com/media/([A-Za-z0-9]+~mv2\.[a-zA-Z]+)',
        # Video thumbnails
        r'https://static\.wixstatic\.com/[A-Za-z0-9_/\-\.~]+\.(jpg|jpeg|png|gif|webp|svg)',
        # wix images API
        r'https://images\.wixstatic\.com/[^"\'>\s,)]+',
        # Video files  
        r'https://video\.wixstatic\.com/[^"\'>\s,)]+\.mp4',
    ]
    
    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                # Reconstruct full URL from capture group
                continue
            if m.startswith("http"):
                found.add(m)
    
    return found

def clean_wix_image_url(url):
    """
    Strip Wix resize parameters to get full-resolution original.
    
    Example:
    Input:  https://static.wixstatic.com/media/abc123~mv2.jpg/v1/fill/w_740,h_416,al_c,q_80/abc123~mv2.jpg
    Output: https://static.wixstatic.com/media/abc123~mv2.jpg
    
    Also handles:
    https://static.wixstatic.com/media/abc123~mv2.jpg/v1/crop/...
    """
    # Strip everything after /v1/ to get the base media URL
    cleaned = re.sub(r'/v1/(?:fill|fit|crop|scale)[^"\']*', '', url)
    # Also remove duplicate filename at end (Wix repeats the filename)
    cleaned = re.sub(r'(/media/[A-Za-z0-9_~\-\.]+)\1$', r'\1', cleaned)
    return cleaned.strip()

def url_to_filename(url):
    """Convert a URL to a safe local filename, preserving the original name."""
    path = urllib.parse.urlparse(url).path
    # Extract original filename if it has ~mv2 pattern
    match = re.search(r'([A-Za-z0-9_]+~mv2[^/]*$)', path)
    if match:
        name = match.group(1)
        # Clean up URL-encoded chars
        name = urllib.parse.unquote(name)
        return name
    
    # Fall back to last path component
    name = path.rstrip('/').split('/')[-1]
    name = urllib.parse.unquote(name)
    if not name or name in ['fill', 'crop', 'fit']:
        name = f"image_{hash(url) & 0xFFFFFF:06x}.jpg"
    return name

def download_file(url, dest_path):
    """Download a file to dest_path, skip if exists."""
    if dest_path.exists():
        print(f"  ✓ Already exists: {dest_path.name}")
        return True
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            dest_path.write_bytes(content)
            size_kb = len(content) / 1024
            print(f"  ↓ {dest_path.name} ({size_kb:.1f} KB)")
            return True
    except Exception as e:
        print(f"  ✗ Failed {url}: {e}")
        return False

def main():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    all_media_urls = set()
    page_data = {}
    
    print("=" * 60)
    print("FDJ ARCHIVE EXTRACTOR")
    print("=" * 60)
    
    # Step 1: Fetch all pages and extract media URLs
    for page_name, page_path in PAGES.items():
        url = BASE_URL + page_path
        print(f"\n📄 Fetching: {page_name} ({url})")
        
        html = fetch_page(url)
        if not html:
            continue
        
        # Save raw HTML
        html_file = PAGES_DIR / f"{page_name}.html"
        html_file.write_text(html, encoding="utf-8")
        print(f"  💾 HTML saved ({len(html)} chars)")
        
        # Extract media URLs
        media_urls = extract_wixstatic_urls(html)
        clean_urls = set()
        for raw_url in media_urls:
            clean = clean_wix_image_url(raw_url)
            clean_urls.add(clean)
        
        print(f"  🖼️  Found {len(clean_urls)} media URLs")
        all_media_urls.update(clean_urls)
        
        page_data[page_name] = {
            "url": url,
            "html_size": len(html),
            "media_count": len(clean_urls),
            "media_urls": sorted(clean_urls),
        }
        
        time.sleep(1)  # Be polite to the server
    
    # Step 2: Save URL manifest
    manifest_path = DATA_DIR / "media-manifest.json"
    manifest = {
        "site": BASE_URL,
        "archived_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_urls": len(all_media_urls),
        "pages": page_data,
        "all_media_urls": sorted(all_media_urls),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n📋 Manifest saved: {manifest_path}")
    print(f"   Total unique media URLs: {len(all_media_urls)}")
    
    # Step 3: Download all media
    print(f"\n📥 Downloading {len(all_media_urls)} media files...")
    print("-" * 60)
    
    success, failed = 0, 0
    url_list = sorted(all_media_urls)
    
    for i, url in enumerate(url_list, 1):
        print(f"[{i}/{len(url_list)}]", end=" ")
        filename = url_to_filename(url)
        dest = MEDIA_DIR / filename
        
        if download_file(url, dest):
            success += 1
        else:
            failed += 1
        
        time.sleep(0.5)  # Rate limit
    
    print(f"\n{'=' * 60}")
    print(f"✅ Downloaded: {success} files")
    print(f"❌ Failed: {failed} files")
    print(f"📁 Saved to: {MEDIA_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
