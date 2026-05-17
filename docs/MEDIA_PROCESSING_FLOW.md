# BarkMind — Media Processing Flow

**Date:** 2026-05-17

---

## Upload Flow (Sequence)

```
Client                     Router                    Storage           Background Task    DB
  │                          │                          │                    │             │
  │ POST /cases/{id}/media   │                          │                    │             │
  ├─────────────────────────►│                          │                    │             │
  │                          │ 1. Check case exists     │                    │             │
  │                          ├─────────────────────────────────────────────────────────►│
  │                          │◄────────────────────────────────────────────────────────│
  │                          │                          │                    │             │
  │                          │ 2. Validate declared MIME│                    │             │
  │                          │ 3. Read 16 header bytes  │                    │             │
  │                          │ 4. Check magic bytes     │                    │             │
  │ ◄─ 415 if mismatch ──────│                          │                    │             │
  │                          │                          │                    │             │
  │                          │ 5. Stream file to disk   │                    │             │
  │                          ├────────────────────────►│                    │             │
  │                          │ 6. Enforce size limit    │                    │             │
  │ ◄─ 413 if too large ─────│                          │                    │             │
  │                          │                          │                    │             │
  │                          │ 7. Insert case_media row (status=pending)    │             │
  │                          ├─────────────────────────────────────────────────────────►│
  │                          │ 8. await db.commit()                          │             │
  │                          ├─────────────────────────────────────────────────────────►│
  │                          │                          │                    │             │
  │                          │ 9. Schedule background task                   │             │
  │                          │─────────────────────────────────────────────►│             │
  │                          │                          │                    │             │
  │ ◄─ 201 (status=pending) ─│                          │                    │             │
  │                          │                          │                    │             │
  │                          │                          │ 10. asyncio.to_thread(_process_sync)
  │                          │                          │◄───────────────────┤             │
  │                          │                          │ generate thumbnails│             │
  │                          │                          │ extract metadata   │             │
  │                          │                          ├───────────────────►│             │
  │                          │                          │                    │             │
  │                          │                          │ 11. Update DB record (status=ready)
  │                          │                          │                    ├────────────►│
  │                          │                          │                    │             │
  │ GET .../media/{id}/status│                          │                    │             │
  ├─────────────────────────►│                          │                    │             │
  │ ◄─ {status=ready, thumbs}│                          │                    │             │
```

---

## Image Processing Detail

```
Source File (JPEG/PNG/WebP)
    │
    ▼ PIL Image.open()
    │
    ▼ ImageOps.exif_transpose()   ← correct camera rotation
    │
    ▼ .convert("RGB")             ← normalize mode (RGBA → RGB, palette → RGB)
    │
    ├─── sm: thumbnail(200×200) → JPEG quality=85
    ├─── md: thumbnail(400×400) → JPEG quality=85  [primary]
    └─── lg: thumbnail(800×800) → JPEG quality=85
```

---

## Video Processing Detail

```
Source File (MP4/MOV/WebM)
    │
    ▼ ffprobe -show_streams -show_format
    │  → {width, height, duration, codec}
    │
    ▼ Choose seek time:
    │  min(2.0s, max(0.0s, duration-0.5s))
    │  Fallback candidates: [2.0, 1.0, 0.5, 0.0]
    │
    ▼ ffmpeg -ss {seek} -i {input} -frames:v 1 -vf scale=400:-2 -q:v 2 raw_md.jpg
    │
    ▼ PIL Image.open(raw_md.jpg)
    │
    ├─── sm: thumbnail(200×200) → JPEG quality=85
    ├─── md: copy of raw frame → JPEG quality=85  [primary]
    └─── lg: thumbnail(800×800) → JPEG quality=85
    │
    └─ raw_md.jpg deleted
```

---

## Frame Extraction (Future — Not Active)

```
When triggered (Phase 4/5 multimodal AI):

Source Video
    │
    ▼ ffmpeg -vf fps=0.5,scale=800:-2 -frames:v 50
    │
    └─ media/cases/{id}/frames/
          {media_id}_frame_0001.jpg
          {media_id}_frame_0002.jpg
          ... (max 50 frames)
    │
    ▼ Frame paths returned to AI service
    │
    ▼ POST to Claude API (multimodal) per frame
    │
    ▼ Store per-frame behavioral observations
```

---

## File Layout After Processing

```
media/
  cases/
    {case_id}/
      original/
        {uuid}.jpg            ← original uploaded file
      thumbnails/
        {uuid}_sm.jpg         ← 200px max
        {uuid}_md.jpg         ← 400px max (primary)
        {uuid}_lg.jpg         ← 800px max
      derived/                ← empty (future use)
      frames/                 ← empty (future use)
```

---

## DB Record After Processing

```
case_media:
  id:                 {uuid}
  processing_status:  ready
  stored_path:        cases/{case_id}/original/{uuid}.jpg
  thumbnail_path:     cases/{case_id}/thumbnails/{uuid}_md.jpg
  thumbnails:         {
                        "sm": "cases/{id}/thumbnails/{uuid}_sm.jpg",
                        "md": "cases/{id}/thumbnails/{uuid}_md.jpg",
                        "lg": "cases/{id}/thumbnails/{uuid}_lg.jpg"
                      }
  width_px:           {image width}
  height_px:          {image height}
  duration_seconds:   null (image) / {float} (video)
  size_bytes:         {bytes}
```

---

## Error Handling

| Error Condition | Result | DB State |
|---|---|---|
| Invalid MIME header | 415 before DB write | No record created |
| Magic bytes mismatch | 415 after reading 16 bytes | No record created, no file written |
| File too large (streaming) | 413, file deleted | No record created |
| Disk write failure | 500, file deleted | No record created |
| Thumbnail generation fails | Background task logs error | `processing_status='failed'` |
| ffprobe timeout | Video metadata empty | Thumbnails still attempted |
| ffmpeg frame extraction fails | All seek candidates tried | `processing_status='failed'` if all fail |
