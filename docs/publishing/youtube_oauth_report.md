# YouTube OAuth & Verification Report (Phase 13.1)

**Generated:** 2026-07-17 03:28:18 UTC
**Status:** ✅ VERIFIED & ONLINE (OAuth Phase Active)

---

## 1. Google Cloud OAuth Configuration
- **OAuth Client ID**: `1033291409890-aom1h1fdlsqc4hkhplj46fngr3ra4rqd.apps.googleusercontent.com`
- **OAuth Client Secret**: `GOCSPX-H************repX`
- **Google Project ID**: `aates-studio`
- **Consent Screen Mode**: `Testing (OAuth App)`
- **Authorized Google Account**: `Verified (scopes approved)`
- **Verification Timestamp**: `2026-07-17 03:28:18 UTC`

---

## 2. OAuth Scopes Validation
- **Required Scopes Status**: ✅ ALL GRANTED
- **Granted Scopes**:
  - `https://www.googleapis.com/auth/youtube.force-ssl`
  - `https://www.googleapis.com/auth/youtube.readonly`
  - `https://www.googleapis.com/auth/youtube.upload`

---

## 3. Channel Verification
- **Channel ID**: `UCNZrTavbUchfVyHD-WycMvA`
- **Channel Title**: `SeriesWithUs`
- **Channel URL**: [https://youtube.com/channel/UCNZrTavbUchfVyHD-WycMvA](https://youtube.com/channel/UCNZrTavbUchfVyHD-WycMvA)
- **Upload Playlist ID**: `UUNZrTavbUchfVyHD-WycMvA`
- **Subscribers**: `0`
- **Video Count**: `0`

---

## 4. Token Refresh Verification
- **Refresh Token status**: ✅ VALID
- **Refresh Token Exchange test**: ✅ PASS (Successfully generated on-demand access token)
- **Access Token Storage**: 🔐 SECURE (Never stored in AWS Secrets Manager or source code)

---

## 5. AWS Secrets Manager Status
- **AWS Secrets Manager target**: `aates-production-secrets`
- **Merged Fields**:
  - `youtube_client_id`
  - `youtube_client_secret`
  - `youtube_refresh_token`
  - `youtube_channel_id`
  - `youtube_scopes`
- **Existing Config Keys Preserved**: ✅ YES (Merged, not overwritten)
