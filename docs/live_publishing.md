# Phase 13 — Live Publishing Provider Integration

This document outlines the architecture, setup instructions, validation mechanisms, and fallback/rollback procedures for the production YouTube Shorts and Instagram Reels publishing providers.

---

## 1. Secrets Manager Schema
All credentials are loaded dynamically at boot time from AWS Secrets Manager.
**Secret Name**: `aates-production-secrets`

Ensure the secret string contains the following fields:

```json
{
  "youtube_client_id": "YOUR_YOUTUBE_CLIENT_ID",
  "youtube_client_secret": "YOUR_YOUTUBE_CLIENT_SECRET",
  "youtube_refresh_token": "YOUR_YOUTUBE_REFRESH_TOKEN",
  "youtube_channel_id": "YOUR_YOUTUBE_CHANNEL_ID",
  "meta_app_id": "YOUR_META_APP_ID",
  "meta_app_secret": "YOUR_META_APP_SECRET",
  "instagram_access_token": "YOUR_INSTAGRAM_LONG_LIVED_ACCESS_TOKEN",
  "instagram_business_account_id": "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID",
  "facebook_page_id": "YOUR_FACEBOOK_PAGE_ID"
}
```

No credentials are ever read from env files or hardcoded.

---

## 2. OAuth & Authentication Details

### YouTube (OAuth 2.0 Refresh Flow)
YouTube requires user authorization to upload videos. We use the server-side OAuth 2.0 Web Server Flow to generate a long-lived **refresh token**. 
At publish time:
1. `YouTubePublisher` requests a fresh temporary access token from Google's OAuth 2.0 server (`https://oauth2.googleapis.com/token`) using the client ID, client secret, and refresh token.
2. The refreshed access token is passed in the Authorization header to initiate and complete resumable upload requests.

### Instagram (Meta Graph API Long-Lived Token Flow)
Instagram Reels are published via Meta's Graph API. 
1. Generate a **long-lived User/Page access token** (valid for 60 days) or a non-expiring Page access token.
2. The publisher verifies this token against the target Instagram Business Account ID before starting Reel container creation.

---

## 3. Autonomous Publishing Workflows

### YouTube Shorts Upload Pipeline
```
[Local Video File] 
       │
       ▼
[Retrieve Access Token via Refresh Token]
       │
       ▼
[Initiate Resumable Upload Session] ──► Returns Upload URL
       │
       ▼
[Stream Video File (PUT binary to Upload URL)]
       │
       ▼
[Set Video Thumbnail (POST metadata)]
       │
       ▼
[Upload SRT Subtitles (Multipart POST)]
```

### Instagram Reels Upload Pipeline (S3 Bridge)
Meta Graph API Reels upload requires a publicly accessible video URL.
```
[Local Video File]
       │
       ▼
[Upload to S3 Temporary Key]
       │
       ▼
[Generate Presigned S3 URL (1h expiry)]
       │
       ▼
[Create Instagram Media Container (POST /media)]
       │
       ▼
[Poll Container Ingestion Status (GET status_code == FINISHED)]
       │
       ▼
[Publish Media Container (POST /media_publish)]
```

---

## 4. Verification Checklists

### Production Upload Sanity
Verify integration status using:
- **YouTube Verification**: `POST /v1/publishing/verify/youtube`
- **Instagram Verification**: `POST /v1/publishing/verify/instagram`

### Safe Production Mode (Default)
To prevent accidental public posts during testing, safe mode is **on** by default:
- **YouTube**: Videos are uploaded as **Private**.
- **Instagram**: Reel upload stops after container creation (acting as a Draft container).

To enable public scheduling:
1. Confirm verification endpoints report `verified: true`.
2. Toggle `"safe_production_mode": false` in the execution metadata.

---

## 5. Rollback Procedures
If a publishing pipeline fails or is compromised:
1. **Disable Provider**: Set `youtube_enabled = False` / `instagram_enabled = False` in settings or block them via Secrets Manager. The engine will gracefully fall back to `MockYouTubePublisher` and `MockInstagramPublisher`.
2. **Revoke OAuth Grants**: Revoke Google app access from the Google API console and Instagram App tokens from Meta Developer Portal.
3. **Purge In-Flight Jobs**: Use `/v1/runtime/queues` or Redis CLI to purge/flush queued publishing items.
