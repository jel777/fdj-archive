#!/usr/bin/env python3
"""
FDJ Church Photo Assessment Script
Analyzes all images in the fdj-archive for quality, blur, resolution, and EXIF metadata.
Outputs a graded report and curated folder.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ExifTags
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("WARNING: PIL not available")

try:
    import cv2
    import numpy as np
    CV2_OK = True
except ImportError:
    CV2_OK = False
    print("WARNING: cv2 not available, using PIL-based blur detection")

# ─── Paths ──────────────────────────────────────────────────────────────────
ARCHIVE_ROOT = Path("/Users/jasonluff/clawd/projects/fdj-archive")
MEDIA_ROOT = ARCHIVE_ROOT / "media"
CURATED_DIR = MEDIA_ROOT / "curated"
REPORT_PATH = ARCHIVE_ROOT / "PHOTO-ASSESSMENT-2026-03-13.md"

# ─── Helpers ────────────────────────────────────────────────────────────────

def blur_score_cv2(path):
    """OpenCV Laplacian variance blur detection."""
    img = cv2.imread(str(path))
    if img is None:
        return 0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def blur_score_pil(path):
    """PIL-based blur estimate using image statistics (fallback)."""
    try:
        img = Image.open(path).convert("L")
        import statistics
        pixels = list(img.getdata())
        # Approximate sharpness: std deviation of pixel values
        if len(pixels) < 2:
            return 0
        mean = sum(pixels) / len(pixels)
        variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
        return variance  # higher = more varied = likely sharper
    except Exception:
        return 0


def get_blur_info(path):
    if CV2_OK:
        score = blur_score_cv2(path)
    else:
        score = blur_score_pil(path)
    
    if score >= 500:
        label = "SHARP ⭐"
    elif score >= 100:
        label = "ACCEPTABLE"
    elif score >= 20:
        label = "SOFT"
    else:
        label = "BLURRY ❌"
    
    return score, label


def get_resolution_info(path):
    """Return (width, height, file_size_kb, mode, res_grade)."""
    try:
        img = Image.open(path)
        w, h = img.size
        mode = img.mode
        size_kb = path.stat().st_size / 1024
        
        if w >= 2000:
            grade = "HIGH RES 🔥"
        elif w >= 1000:
            grade = "MEDIUM RES"
        elif w >= 500:
            grade = "LOW RES"
        else:
            grade = "THUMBNAIL"
        
        return w, h, size_kb, mode, grade
    except Exception as e:
        return 0, 0, 0, "?", f"ERROR: {e}"


def get_exif_pil(path):
    """Basic EXIF via PIL."""
    try:
        img = Image.open(path)
        raw = img._getexif() if hasattr(img, '_getexif') else None
        if not raw:
            return {}
        tags = {ExifTags.TAGS.get(k, k): v for k, v in raw.items()}
        return tags
    except Exception:
        return {}


def get_exif_tool(path):
    """Full EXIF via exiftool."""
    try:
        result = subprocess.run(
            ["exiftool", "-j", "-DateTimeOriginal", "-Make", "-Model",
             "-GPSLatitude", "-GPSLongitude", "-ImageDescription", "-Copyright",
             "-CreateDate", "-FileSize", str(path)],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        return data[0] if data else {}
    except Exception:
        return {}


def format_exif_date(exif_data):
    """Extract date from exiftool output."""
    date_str = exif_data.get("DateTimeOriginal") or exif_data.get("CreateDate")
    if date_str and date_str != "-":
        # Format: "2019:10:10 15:30:00"
        try:
            dt = datetime.strptime(date_str[:19], "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return date_str
    return None


def format_camera(exif_data):
    make = exif_data.get("Make", "").strip()
    model = exif_data.get("Model", "").strip()
    if make and model:
        # Avoid "Apple Apple iPhone X" style
        if model.startswith(make):
            return model
        return f"{make} {model}"
    return model or make or None


def overall_grade(blur_label, res_grade, size_kb, is_background, is_solid, filename):
    """Assign A/B/C/D/F grade."""
    if is_solid or is_background:
        return "ASSET"
    
    if size_kb < 5:
        return "F"
    
    if res_grade == "ERROR" or res_grade.startswith("ERROR"):
        return "F"
    
    # Combine blur and resolution
    sharp = blur_label.startswith("SHARP") or blur_label.startswith("ACCEPTABLE")
    high_res = res_grade in ("HIGH RES 🔥",)
    med_res = res_grade in ("MEDIUM RES",)
    low_res = res_grade in ("LOW RES",)
    thumbnail = res_grade in ("THUMBNAIL",)
    
    blurry = blur_label.startswith("BLURRY")
    soft = blur_label.startswith("SOFT")
    
    if thumbnail:
        return "D"
    
    if blurry:
        return "D"
    
    if sharp and high_res:
        return "A"
    elif sharp and med_res:
        return "B"
    elif sharp and low_res:
        return "C"
    elif soft and high_res:
        return "B"
    elif soft and med_res:
        return "C"
    elif soft and low_res:
        return "C"
    else:
        return "D"


def infer_content_notes(filepath, exif_data):
    """Infer content description from filename and path."""
    p = str(filepath)
    fname = filepath.name.lower()
    
    notes = []
    
    # Special known files
    if "hayden-header" in fname:
        return "⚠️ SQUARESPACE TEMPLATE STOCK PHOTO — NOT an FDJ photo"
    if "solid-" in fname:
        return "Squarespace color background placeholder"
    if fname == "favicon.png":
        return "Site favicon/icon"
    if "logo_fdj" in fname or "logo fdj" in fname.replace("_"," "):
        return "FDJ church logo"
    if "Untitled-1" in filepath.name:
        return "Unknown/unnamed graphic"
    
    # By gallery dir
    if "/isha/" in p:
        notes.append("Isha women's ministry")
    elif "/soldaditos/" in p:
        notes.append("Soldaditos children's ministry")
    elif "/generacion/" in p:
        notes.append("Generacion youth ministry")
    elif "/home/" in p:
        notes.append("Home gallery")
    
    # By filename
    if "daughter_and_mother" in fname:
        notes.append("Mother and daughter portrait")
    elif "hombres_circulo" in fname:
        notes.append("Men's circle group photo")
    elif "pastor" in fname and "pastora" in fname:
        notes.append("Pastor and Pastora portrait")
    elif "pastor_preaching" in fname or "pastor preaching" in fname.replace("_"," "):
        notes.append("Pastor preaching")
    elif "in_worship" in fname or "worship" in fname:
        notes.append("Worship service")
    elif "image_from_back_of_church" in fname:
        notes.append("Church interior from back")
    elif "image_of_pastor_hugging" in fname:
        notes.append("Pastor and Pastora embrace")
    elif "family_fest" in fname:
        notes.append("Family Fest event group photo")
    elif "home-p" in fname:
        notes.append("Home hero/slider image")
    elif "dsc_0" in fname:
        # DSC = camera raw filename, likely DSLR
        parent = filepath.parent.name
        notes.append(f"{parent.capitalize()} ministry photo (DSLR)")
    elif "gud_" in fname:
        notes.append("Generacion Ud ministry photo")
    elif fname.startswith("169"):
        notes.append("Podcast/media thumbnail (timestamp filename)")
    
    return "; ".join(notes) if notes else "No content notes"


def recommendation(grade, filename, is_background, is_solid):
    fname = filename.lower()
    if "hayden-header" in fname:
        return "❌ DISCARD"
    if is_solid:
        return "⚠️ SKIP"
    if fname == "favicon.png":
        return "⚠️ SKIP"
    if fname.startswith("169") and grade in ("D", "F"):
        return "⚠️ SKIP"
    if grade == "A":
        return "🌟 RECOMMENDED"
    elif grade == "B":
        return "🌟 RECOMMENDED"
    elif grade == "C":
        return "✅ USABLE"
    elif grade in ("D", "F"):
        return "⚠️ SKIP"
    elif grade == "ASSET":
        return "⚠️ SKIP"
    return "⚠️ SKIP"


# ─── Curated filename mapping ────────────────────────────────────────────────
# Build as we go; we'll finalize after assessment

def curated_name(filepath, grade, content_notes):
    """Generate a descriptive curated filename."""
    fname = filepath.name.lower()
    ext = filepath.suffix.lower()
    parent = filepath.parent.name
    
    if "hayden-header" in fname:
        return None
    if "solid-" in fname:
        return None
    if fname == "favicon.png":
        return None
    
    if "logo_fdj" in fname:
        return f"logo_fdj_black{ext}"
    if "untitled-1" in fname:
        return f"graphic_fdj_unknown{ext}"
    if "daughter_and_mother_alt" in fname:
        return f"family_mother_daughter_alt{ext}"
    if "daughter_and_mother" in fname:
        return f"family_mother_daughter{ext}"
    if "hombres_circulo" in fname:
        return f"mens_ministry_circle{ext}"
    if "in_worship" in fname:
        return f"worship_service_congregation{ext}"
    if "pastor_preaching" in fname:
        return f"pastor_preaching{ext}"
    if "image_from_back_of_church" in fname:
        return f"church_interior_back{ext}"
    if "image_of_pastor_hugging_pastora" in fname or ("pastor" in fname and "pastora" in fname):
        return f"pastor_pastora_embrace{ext}"
    if "family_fest" in fname:
        return f"family_fest_group{ext}"
    if "home-p" in fname:
        return f"church_home_hero{ext}"
    if "image_24-05-2016" in fname:
        return f"church_event_2016{ext}"
    
    # DSC files from DSLR
    if fname.startswith("dsc_"):
        num = filepath.stem.split("_")[-1]
        if parent == "isha":
            return f"worship_women_isha_{num}{ext}"
        elif parent == "soldaditos":
            return f"children_ministry_soldaditos_{num}{ext}"
        elif parent == "generacion":
            return f"youth_ministry_generacion_{num}{ext}"
        return f"{parent}_{num}{ext}"
    
    # gud_ files
    if fname.startswith("gud_"):
        num = filepath.stem.split("_")[-1]
        return f"youth_ministry_generacion_{num:>02}{ext}"
    
    # Timestamp files (podcast icons)
    if fname[0].isdigit() and len(fname) > 10:
        return f"podcast_thumbnail_{filepath.stem}{ext}"
    
    return filepath.name


# ─── Main Assessment ─────────────────────────────────────────────────────────

def assess_all():
    # Find all images
    image_exts = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
    all_images = []
    for root, dirs, files in os.walk(MEDIA_ROOT):
        # Skip curated dir to avoid double-counting
        if "curated" in root:
            continue
        for f in sorted(files):
            p = Path(root) / f
            if p.suffix in image_exts:
                all_images.append(p)
    
    all_images.sort()
    print(f"\n📁 Found {len(all_images)} images to assess\n")
    
    results = []
    exif_dates = []
    
    for path in all_images:
        fname = path.name
        rel = path.relative_to(ARCHIVE_ROOT)
        
        print(f"  Analyzing: {rel}")
        
        is_solid = fname.lower().startswith("solid-")
        is_bg = fname.lower() in ["hayden-header.jpg"]
        is_favicon = fname.lower() == "favicon.png"
        
        # Resolution/size
        w, h, size_kb, mode, res_grade = get_resolution_info(path)
        
        # Blur
        if size_kb < 1:
            blur_val, blur_label = 0, "UNREADABLE"
        elif is_solid:
            blur_val, blur_label = 0, "N/A (solid color)"
        else:
            blur_val, blur_label = get_blur_info(path)
        
        # EXIF
        exif = get_exif_tool(path)
        pil_exif = get_exif_pil(path)
        
        date_taken = format_exif_date(exif)
        camera = format_camera(exif)
        
        if date_taken:
            try:
                exif_dates.append(datetime.strptime(date_taken, "%Y-%m-%d"))
            except Exception:
                pass
        
        # GPS
        gps_lat = exif.get("GPSLatitude")
        gps_lon = exif.get("GPSLongitude")
        has_gps = bool(gps_lat and gps_lon)
        
        # Grade
        grade = overall_grade(blur_label, res_grade, size_kb, is_bg, is_solid, fname)
        
        # Content notes
        content = infer_content_notes(path, exif)
        
        # Recommendation
        rec = recommendation(grade, fname, is_bg, is_solid)
        
        # Curated name
        c_name = curated_name(path, grade, content)
        
        results.append({
            "path": str(path),
            "rel": str(rel),
            "filename": fname,
            "is_solid": is_solid,
            "is_bg": is_bg,
            "w": w, "h": h,
            "size_kb": size_kb,
            "mode": mode,
            "res_grade": res_grade,
            "blur_score": round(blur_val, 1),
            "blur_label": blur_label,
            "grade": grade,
            "date_taken": date_taken,
            "camera": camera,
            "has_gps": has_gps,
            "content": content,
            "recommendation": rec,
            "curated_name": c_name,
        })
    
    return results, exif_dates


# ─── Report Generation ───────────────────────────────────────────────────────

def generate_report(results, exif_dates):
    lines = []
    lines.append("# FDJ Photo Assessment Report")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M CDT')}")
    lines.append(f"**Total Images Assessed:** {len(results)}")
    lines.append("")
    
    # Grade breakdown
    grade_counts = {}
    for r in results:
        g = r["grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1
    
    lines.append("## 📊 Grade Summary")
    lines.append("")
    for grade in ["A", "B", "C", "D", "F", "ASSET"]:
        count = grade_counts.get(grade, 0)
        if count:
            emoji = {"A": "🏆", "B": "✅", "C": "🟡", "D": "🔴", "F": "💀", "ASSET": "🎨"}.get(grade, "")
            lines.append(f"- {emoji} **Grade {grade}:** {count} images")
    lines.append("")
    
    rec_counts = {}
    for r in results:
        rc = r["recommendation"]
        rec_counts[rc] = rec_counts.get(rc, 0) + 1
    
    lines.append("## 🎯 Curation Summary")
    lines.append("")
    for rec in ["🌟 RECOMMENDED", "✅ USABLE", "⚠️ SKIP", "❌ DISCARD"]:
        count = rec_counts.get(rec, 0)
        if count:
            lines.append(f"- {rec}: {count} images")
    lines.append("")
    
    if exif_dates:
        oldest = min(exif_dates).strftime("%Y-%m-%d")
        newest = max(exif_dates).strftime("%Y-%m-%d")
        lines.append(f"**📅 EXIF Date Range:** {oldest} → {newest}")
        lines.append("")
    else:
        lines.append("**📅 EXIF Date Range:** No EXIF dates found")
        lines.append("")
    
    # Special warnings
    lines.append("## ⚠️ Special Flags")
    lines.append("")
    lines.append("- **hayden-header.jpg** — SQUARESPACE TEMPLATE STOCK PHOTO. This is NOT an FDJ church photo. Do NOT use on any FDJ materials.")
    lines.append("- **solid-\\*.jpg** — Squarespace color background placeholders (teal/red/gold). Not real photos.")
    lines.append("- **Timestamp-named PNGs (169\\*.png)** — Podcast episode artwork/thumbnails. Very small files, not usable as site photos.")
    lines.append("")
    
    # Sections by category
    sections = [
        ("🖼️ Primary Site Images (media/images/)", lambda r: "images" in r["rel"] and not r["is_solid"]),
        ("🎨 Background Assets (solid-*.jpg)", lambda r: r["is_solid"]),
        ("📸 Gallery: Isha (Women's Ministry)", lambda r: "/isha/" in r["path"]),
        ("📸 Gallery: Soldaditos (Children's Ministry)", lambda r: "/soldaditos/" in r["path"]),
        ("📸 Gallery: Generacion (Youth Ministry)", lambda r: "/generacion/" in r["path"]),
        ("📸 Gallery: Home", lambda r: "/gallery/home/" in r["path"]),
    ]
    
    lines.append("---")
    lines.append("")
    lines.append("## 📋 Detailed Assessment")
    lines.append("")
    
    for section_title, filter_fn in sections:
        section_items = [r for r in results if filter_fn(r)]
        if not section_items:
            continue
        
        lines.append(f"### {section_title}")
        lines.append("")
        
        for r in section_items:
            rec_icon = r["recommendation"].split()[0]
            lines.append(f"📸 **{r['filename']}**")
            lines.append(f"• Rec: {r['recommendation']}")
            lines.append(f"• Grade: {r['grade']} | Blur: {r['blur_label']} (score: {r['blur_score']}) | Res: {r['w']}×{r['h']} ({r['res_grade']})")
            lines.append(f"• File size: {r['size_kb']:.1f} KB | Mode: {r['mode']}")
            date_str = r['date_taken'] if r['date_taken'] else "No EXIF date"
            cam_str = r['camera'] if r['camera'] else "Unknown camera"
            lines.append(f"• Date taken: {date_str} | Camera: {cam_str}")
            if r['has_gps']:
                lines.append(f"• 📍 Has GPS coordinates")
            if r['curated_name']:
                lines.append(f"• Curated name: `{r['curated_name']}`")
            lines.append(f"• Notes: {r['content']}")
            lines.append("")
    
    # Curated folder manifest
    lines.append("---")
    lines.append("")
    lines.append("## 📁 Curated Folder Manifest")
    lines.append("")
    lines.append("Files copied to `media/curated/`:")
    lines.append("")
    
    curated = [r for r in results if r["recommendation"] in ("🌟 RECOMMENDED", "✅ USABLE") and r["curated_name"]]
    for r in curated:
        lines.append(f"- `{r['curated_name']}` ← `{r['rel']}`")
    
    lines.append("")
    lines.append(f"**Total curated: {len(curated)} images**")
    
    return "\n".join(lines)


# ─── Curated Copy ─────────────────────────────────────────────────────────────

def build_curated(results):
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    
    copied = []
    skipped = []
    name_counts = {}
    
    for r in results:
        if r["recommendation"] not in ("🌟 RECOMMENDED", "✅ USABLE"):
            continue
        if not r["curated_name"]:
            continue
        
        src = Path(r["path"])
        
        # Handle name collisions
        base_name = r["curated_name"]
        stem = Path(base_name).stem
        ext = Path(base_name).suffix
        if base_name in name_counts:
            name_counts[base_name] += 1
            dest_name = f"{stem}_{name_counts[base_name]}{ext}"
        else:
            name_counts[base_name] = 0
            dest_name = base_name
        
        dest = CURATED_DIR / dest_name
        
        try:
            shutil.copy2(src, dest)
            copied.append((src, dest))
            print(f"  ✅ Copied: {src.name} → curated/{dest_name}")
        except Exception as e:
            skipped.append((src, str(e)))
            print(f"  ❌ Failed: {src.name} — {e}")
    
    return copied, skipped


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("FDJ Photo Assessment")
    print("=" * 60)
    
    results, exif_dates = assess_all()
    
    print("\n📝 Generating report...")
    report = generate_report(results, exif_dates)
    REPORT_PATH.write_text(report)
    print(f"  ✅ Report: {REPORT_PATH}")
    
    print("\n📁 Building curated folder...")
    copied, skipped = build_curated(results)
    
    # Final summary
    grade_counts = {}
    for r in results:
        g = r["grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1
    
    rec_counts = {}
    for r in results:
        rc = r["recommendation"]
        rec_counts[rc] = rec_counts.get(rc, 0) + 1
    
    corrupt = [r for r in results if r["grade"] == "F"]
    
    print("\n" + "=" * 60)
    print("ASSESSMENT COMPLETE")
    print("=" * 60)
    print(f"\n📊 Total images assessed: {len(results)}")
    print("\nGrade Breakdown:")
    for grade in ["A", "B", "C", "D", "F", "ASSET"]:
        count = grade_counts.get(grade, 0)
        if count:
            print(f"  Grade {grade}: {count}")
    
    print(f"\n🌟 Recommended for use: {rec_counts.get('🌟 RECOMMENDED', 0)}")
    print(f"✅ Usable: {rec_counts.get('✅ USABLE', 0)}")
    print(f"⚠️  Skip/Background: {rec_counts.get('⚠️ SKIP', 0)}")
    print(f"❌ Discard: {rec_counts.get('❌ DISCARD', 0)}")
    
    print(f"\n💀 Corrupt/Failed downloads: {len(corrupt)}")
    if corrupt:
        for r in corrupt:
            print(f"  - {r['rel']}")
    
    if exif_dates:
        oldest = min(exif_dates).strftime("%Y-%m-%d")
        newest = max(exif_dates).strftime("%Y-%m-%d")
        print(f"\n📅 EXIF date range: {oldest} → {newest}")
    else:
        print("\n📅 EXIF date range: No dates found")
    
    print(f"\n📁 Curated folder: {CURATED_DIR} ({len(copied)} files)")
    print(f"📄 Report: {REPORT_PATH}")
    
    if skipped:
        print(f"\n⚠️  Failed to copy {len(skipped)} files:")
        for src, err in skipped:
            print(f"  - {src.name}: {err}")
