# FDJ Church Website Archive

**Archived:** March 13, 2026  
**Original URL:** www.lafamiliadejesus.com  
**Platform:** Squarespace (not Wix as initially thought)  
**Site ID:** `55f9d72de4b00b2feb733943`  
**Internal URL:** evan-roberts-xulw.squarespace.com

## Purpose

Complete archive of the original La Familia de Jesus church website before the domain is redirected to the new church website (Familia-Connect on Firebase/Vercel).

## What's Included

### `/media/images/` — Primary site images (34 files, ~15MB)
Downloaded at full resolution via Squarespace JSON API (`?format=original`)

Key files:
- `Logo_FDJ_black.png` — Church logo
- `family_fest_image.jpg` — Family fest event photo
- `image_of_pastor_hugging_pastora.jpg` — Pastor and Pastora Ortiz
- `image_from_back_of_church.jpg` — Church interior from rear
- `Daughter_and_Mother.jpg` — Mother-daughter worship moment
- `Untitled-1.png` — Church group photo (3300x2400)
- `Hombres_Circulo.jpg` — Men's circle/leadership photo

### `/media/gallery/` — JS-rendered slideshow galleries (38 files, ~6MB)
These images were NOT in the JSON API — extracted from rendered DOM via headless browser.

- `/isha/` — 6 photos (DSC_0277–DSC_0420) — Women's worship ministry
- `/soldaditos/` — 8 photos (DSC_0020–DSC_0030) — Children's ministry
- `/generacion/` — 21 photos (GUD youth group, Friendsgiving, camps, events)
- `/home/` — 3 photos (worship, pastor preaching, prayer)

### `/screenshots/` — Full-page screenshots of every page
Visual record of the complete site as it appeared on March 13, 2026.

### `/pages/` — Raw HTML of each page
Server-rendered HTML (JS framework loads content dynamically).

### `/data/` — Structured JSON data
- `archive-manifest.json` — Master manifest with all URLs, contact info, social links
- `home.json`, `podcast.json`, etc. — Page-level Squarespace JSON API responses
- `media-manifest.json` — Image URL inventory

### `/content/` — Extracted text content
Plain text extracted from JSON API responses for each page.

### `/wget-mirror/` — Traditional wget recursive mirror
Full recursive download including CSS, JS, and linked assets.

## Site Structure

| Page | Path | Content |
|------|------|---------|
| Home | `/` | Hero slideshow, mission statement, beliefs, calendar, social links |
| Ministerios | `/new-folder-4` | Ministry landing page |
| Varones Valientes | `/varones-valientes` | Men's ministry (vision, calendar) |
| Isha | `/isha-1` | Women's ministry (mission, vision, photo gallery) |
| Generación Usada x Dios | `/generacion-usada-x-dios-1` | Youth ministry (vision, Instagram-style photo grid) |
| Soldaditos de Jesus | `/soldaditos-de-jesus` | Children's ministry (vision, photo gallery) |
| Sermones | `/sermones-1` | Sermon video listing |
| Podcast | `/podcast` | 20+ sermon entries with titles, speakers, dates |
| Donar | `/donar` | Donation page |
| About/Beliefs | `/latin-church-north-houston` | Church history, mission, beliefs (bilingual) |

## Church Information (from site)

- **Name:** Iglesia La Familia de Jesus
- **Address:** 14935 Lillja Road, Houston, TX 77060
- **Phone:** +1 832-215-6080
- **Email:** lafamiliadejesustx@gmail.com
- **Facebook:** facebook.com/fdjtx
- **YouTube:** youtube.com/channel/UC6USKJPB0orT8nprqciSjcg
- **Instagram:** instagram.com/fdjtx

### Sister Churches
- La Familia de Jesus El Salvador (Facebook)
- Rios De Vida Reus, Spain (riosdevidareus.es)

## Wayback Machine

All 11 pages submitted to web.archive.org on March 13, 2026. Previously had **zero** snapshots.

## YouTube Videos Referenced
- Family Fest: https://www.youtube.com/watch?v=BV7YrBJC9C4
- Daughter and Mother: https://www.youtube.com/watch?v=h1bqA7ldL_U

## How to Use

Images are ready for direct use in the new FDJ website or any church materials:

```bash
# Browse all media
ls media/images/
ls media/gallery/*/

# View the structured data
cat data/archive-manifest.json | python3 -m json.tool

# View text content
cat content/beliefs.txt
```

## Scripts

- `scripts/squarespace-archive.py` — JSON API extraction + image download
- `scripts/download-gallery-images.sh` — Browser-rendered gallery image download
- `scripts/extract-and-download.py` — (Initial Wix-targeted script, superseded)
