# AATES Deployment Security & AWS Integration Guide

This guide defines the security guidelines, required permission matrices, IAM roles setup, Secrets Manager payload structures, and verification checklists required to securely deploy the AATES platform on AWS.

---

## AWS Permission Matrix (Least Privilege)

The AATES application runs under an IAM Role with a least-privilege policy. No hardcoded credentials should ever be stored.

| Service | Permissions Allowed | Target Resource | Purpose |
| --- | --- | --- | --- |
| **Secrets Manager** | `secretsmanager:GetSecretValue`, `secretsmanager:DescribeSecret` | `arn:aws:secretsmanager:us-east-1:345307375520:secret:aates-production-secrets-*` | Resolves API keys, JWT secret, DB URLs |
| **S3** | `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` | `arn:aws:s3:::aates-assets-345307375520`, `arn:aws:s3:::aates-assets-345307375520/*` | Read/write generated visuals & audio assets |
| **Bedrock** | `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:Converse`, `bedrock:ConverseStream`, `bedrock:ListFoundationModels` | `*` | Dynamic agent inference Converse API execution |
| **CloudWatch Logs** | `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:DescribeLogStreams`, `logs:PutLogEvents` | `arn:aws:logs:us-east-1:345307375520:log-group:aates-logs:*` | Structured JSON log stream |

For the complete Custom IAM policy JSON document, see [app_iam_policy.json](file:///c:/finished project/AATES/deployment/app_iam_policy.json).

---

## AWS Secrets Manager Config Structure

Create a secret in Secrets Manager named `aates-production-secrets` matching the expected schema. For the complete JSON template, see [secrets_manager_template.json](file:///c:/finished project/AATES/deployment/secrets_manager_template.json).

---

## Amazon S3 Configuration

Recommended bucket name: `aates-assets-345307375520`

Configure:
* **Block Public Access**: Enabled (ON)
* **Versioning**: Enabled (ON)
* **Default Encryption**: Enabled (ON - AES-256)

### S3 Directory Structure
* `universes/` - Lore files and story bible snapshots
* `seasons/` - Episodic beat outlines
* `episodes/` - Manifest definitions
* `storyboards/` - Visual panel layouts
* `images/` - Rendered keyframe scenes
* `videos/` - Composite video files
* `audio/` - Voice dialogue synthetic tracks
* `subtitles/` - SRT/VTT subtitle files
* `master-reels/` - Mixed final MP4 outputs
* `thumbnails/` - Cover images
* `logs/` - Audit outputs

---

## Infrastructure Verification Checklist

1. [ ] Create S3 Bucket `aates-assets-345307375520` in region `us-east-1`.
2. [ ] Create Secrets Manager secret `aates-production-secrets` containing the required keys payload.
3. [ ] Apply custom IAM Policy `app_iam_policy.json` to the deployment EC2 Instance Role.
4. [ ] Run verification verification suite:
   ```bash
   python scripts/verify_real_aws_deployment.py
   ```
