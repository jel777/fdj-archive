#!/bin/bash
# Download all gallery images discovered via browser rendering
# These weren't in the JSON API - they're in JS-rendered slideshows

DEST="$HOME/clawd/projects/fdj-archive/media/gallery"
mkdir -p "$DEST/isha" "$DEST/soldaditos" "$DEST/generacion" "$DEST/home" "$DEST/varones"

echo "=== Downloading Isha Gallery (6 photos) ==="
cd "$DEST/isha"
for img in DSC_0277.JPG DSC_0279.JPG DSC_0361.JPG DSC_0364.JPG DSC_0420.JPG DSC_0357.JPG; do
  HASH=$(echo "$img" | md5 | cut -c1-8)
  # Use the hash-based CDN URLs discovered
  case $img in
    DSC_0277.JPG) URL="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570679890605-89JX3VU83ZHVVKSA278C/DSC_0277.JPG?format=original" ;;
    DSC_0279.JPG) URL="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570679888684-3DQDSKJEMF7DF5DQPS0L/DSC_0279.JPG?format=original" ;;
    DSC_0361.JPG) URL="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570679968864-A2FB8ABWMN3B29LGOLJ4/DSC_0361.JPG?format=original" ;;
    DSC_0364.JPG) URL="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570679973393-UNY452WUT20ONVVJL96B/DSC_0364.JPG?format=original" ;;
    DSC_0420.JPG) URL="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570680038061-G7SQWZ0ZEPJJJ7NOMTFI/DSC_0420.JPG?format=original" ;;
    DSC_0357.JPG) URL="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570680080731-T3MDOGGWKD0XO4IOJ16A/DSC_0357.JPG?format=original" ;;
  esac
  echo -n "  $img → "
  curl -sL -o "$img" "$URL" && echo "$(du -h $img | cut -f1)" || echo "FAILED"
  sleep 0.5
done

echo ""
echo "=== Downloading Soldaditos Gallery (8 photos) ==="
cd "$DEST/soldaditos"
declare -A SOLD_URLS=(
  ["DSC_0020.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682032208-CQC6NPMXL6XN67SN1WUY/DSC_0020.JPG?format=original"
  ["DSC_0022.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682031946-114EKDCWRRJT12DYRTZ2/DSC_0022.JPG?format=original"
  ["DSC_0023.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682065146-8RPXUAZHENLX1096IUJP/DSC_0023.JPG?format=original"
  ["DSC_0025.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682065369-N2NOPT23NU4AYGAG9B9E/DSC_0025.JPG?format=original"
  ["DSC_0027.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682108733-1W2U2BO7K8O4HOMNEOM6/DSC_0027.JPG?format=original"
  ["DSC_0028.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682108063-S0LSMKC28KV61HVJU2LM/DSC_0028.JPG?format=original"
  ["DSC_0029.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682144522-H4D08DLHAR9I8HTG52AH/DSC_0029.JPG?format=original"
  ["DSC_0030.JPG"]="https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570682145874-ECLK5W6LTOCTX16TOYLT/DSC_0030.JPG?format=original"
)
for name in "${!SOLD_URLS[@]}"; do
  echo -n "  $name → "
  curl -sL -o "$name" "${SOLD_URLS[$name]}" && echo "$(du -h $name | cut -f1)" || echo "FAILED"
  sleep 0.5
done

echo ""
echo "=== Downloading Generacion Usada x Dios Gallery (21 photos) ==="
cd "$DEST/generacion"
# Main hero + Instagram-style grid photos
URLS=(
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1570680944083-KVNI03IYTKR2QLKAWJGJ/DSC_0212.JPG?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1543709289721-RSBZFCGSWV2I9F73L3HP/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1543013012522-O3IIREWTB8L87MNJEQFV/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1542924814001-HH473ZSWV9V2RDU6670M/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1542831237118-EUMLL5XB8SRPX971CTGS/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1542745927211-ZMAHS57SDE8TMFE2OJPR/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1542300180493-QIO7YK24P4BX4W6YHQ6U/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1542224655667-NSRWW265T2TZ3CAF6SEM/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1542047129781-IXDWGWN08GEZDQVK3O5N/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1541626960527-5AINKE5G0AQOFNNBTUSK/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1541095666967-H4URWQBV9K6USW5FAGPW/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1540694462630-1MWKFYFTCYQK84AMSM1K/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1540656720808-BU0W28V66FG9U8XMHH5Z/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1540585288031-TZ3MJ0AP7Y8WNPTD8S3O/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1540169893727-AE9D1ESA4DMG551X4MIK/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1538246654380-NT8G3IL9U9K1O28GDQ8K/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1537910594146-8VALJU73UYWWJ520YNWA/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1537643769509-FFHVLX9EF49KZW1FD2WD/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1537498598928-BM3G68F35HIRBIBEKY17/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1537054181366-V4IT0D3KWJRZYG7VZKDG/image-asset.jpeg?format=original"
  "https://images.squarespace-cdn.com/content/v1/55f9d72de4b00b2feb733943/1536071060117-G9SCZH2OCSUOFCB633RP/image-asset.jpeg?format=original"
)
i=1
for url in "${URLS[@]}"; do
  fname=$(printf "gud_%02d.jpg" $i)
  echo -n "  $fname → "
  curl -sL -o "$fname" "$url" && echo "$(du -h $fname | cut -f1)" || echo "FAILED"
  ((i++))
  sleep 0.5
done

echo ""
echo "=== SUMMARY ==="
echo "Isha: $(ls $DEST/isha | wc -l | tr -d ' ') files, $(du -sh $DEST/isha | cut -f1)"
echo "Soldaditos: $(ls $DEST/soldaditos | wc -l | tr -d ' ') files, $(du -sh $DEST/soldaditos | cut -f1)"
echo "Generacion: $(ls $DEST/generacion | wc -l | tr -d ' ') files, $(du -sh $DEST/generacion | cut -f1)"
echo "TOTAL gallery files: $(find $DEST -type f | wc -l | tr -d ' ')"
echo "TOTAL gallery size: $(du -sh $DEST | cut -f1)"
