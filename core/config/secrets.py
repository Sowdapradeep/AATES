import os
import sys
import json
import logging
from core.config.settings import settings

logger = logging.getLogger("secrets_manager")

def verify_aws_startup_prerequisites() -> None:
    """Verifies critical AWS prerequisites before application startup.
    
    Logs warning diagnostic advice on failure instead of exiting.
    """
    # Skip checks in testing or local dev profiles to prevent unit test regressions
    if settings.app.env in ["testing", "development"]:
        return

    # Check if we should enforce AWS checks
    if not settings.aws.secrets_manager_enabled and settings.app.env != "production":
        return

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.error("boto3 package not found.")
        return

    session = boto3.Session()

    # 1. Verify secrets manager secret exists
    if settings.aws.secrets_manager_enabled:
        try:
            sm = session.client("secretsmanager", region_name=settings.aws.region)
            sm.describe_secret(SecretId=settings.aws.secret_name)
        except ClientError as e:
            logger.error(f"AWS Secrets Manager secret '{settings.aws.secret_name}' does not exist or is inaccessible: {str(e)}")
            
    # 2. Verify S3 bucket exists
    try:
        s3 = session.client("s3", region_name=settings.aws.region)
        s3.head_bucket(Bucket=settings.aws.s3_bucket)
    except ClientError as e:
        logger.error(f"Amazon S3 bucket '{settings.aws.s3_bucket}' does not exist or is inaccessible: {str(e)}")

    # 3. Verify Bedrock accessibility
    try:
        bedrock = session.client("bedrock", region_name=settings.aws.region)
        bedrock.list_foundation_models()
    except ClientError as e:
        logger.error(f"Amazon Bedrock API is not accessible: {str(e)}")


def fetch_and_apply_secrets() -> None:
    """Queries AWS Secrets Manager at boot time to inject production credentials dynamically.
    
    Loads configuration maps into settings dynamically.
    """
    if not settings.aws.secrets_manager_enabled:
        logger.info("AWS Secrets Manager is disabled. Skipping credential injection.")
        # Perform prerequisites checks anyway if production
        verify_aws_startup_prerequisites()
        return

    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=settings.aws.region)
        secret_name = settings.aws.secret_name
        
        logger.info(f"Querying AWS Secrets Manager for secret ID: {secret_name}")
        response = client.get_secret_value(SecretId=secret_name)
        
        if "SecretString" in response:
            payload = json.loads(response["SecretString"])
            
            # Map parameters dynamically
            if "openai_api_key" in payload:
                settings.ai.openai_api_key = payload["openai_api_key"]
            if "gemini_api_key" in payload:
                settings.ai.gemini_api_key = payload["gemini_api_key"]
            elif "GEMINI_API_KEY" in payload:
                settings.ai.gemini_api_key = payload["GEMINI_API_KEY"]
            if "stability_api_key" in payload:
                settings.ai.stability_api_key = payload["stability_api_key"]
            if "elevenlabs_api_key" in payload:
                settings.ai.elevenlabs_api_key = payload["elevenlabs_api_key"]
            if "groq_api_key" in payload:
                settings.ai.groq_api_key = payload["groq_api_key"]
            elif "GROQ_API_KEY" in payload:
                settings.ai.groq_api_key = payload["GROQ_API_KEY"]
            if "bedrock_region" in payload:
                settings.ai.bedrock_region = payload["bedrock_region"]
            elif "AWS_REGION" in payload:
                settings.ai.bedrock_region = payload["AWS_REGION"]
            if "bedrock_model_mappings" in payload:
                settings.ai.bedrock_model_mappings = payload["bedrock_model_mappings"]
            if "db_url" in payload:
                settings.db.url = payload["db_url"]
            if "jwt_secret" in payload:
                settings.security.secret_key = payload["jwt_secret"]
            if "cloudwatch_logs_enabled" in payload:
                settings.aws.cloudwatch_logs_enabled = payload["cloudwatch_logs_enabled"]
            if "cloudwatch_log_group" in payload:
                settings.aws.cloudwatch_log_group = payload["cloudwatch_log_group"]
            if "BEDROCK_REASONING_MODEL" in payload:
                settings.ai.bedrock_reasoning_model = payload["BEDROCK_REASONING_MODEL"]
            if "BEDROCK_FAST_MODEL" in payload:
                settings.ai.bedrock_fast_model = payload["BEDROCK_FAST_MODEL"]
            if "BEDROCK_EMBEDDING_MODEL" in payload:
                settings.ai.bedrock_embedding_model = payload["BEDROCK_EMBEDDING_MODEL"]
            if "BEDROCK_IMAGE_MODEL" in payload:
                settings.ai.bedrock_image_model = payload["BEDROCK_IMAGE_MODEL"]
                
            # Map publishing credentials
            if "youtube_client_id" in payload:
                settings.publishing.youtube_client_id = payload["youtube_client_id"]
            if "youtube_client_secret" in payload:
                settings.publishing.youtube_client_secret = payload["youtube_client_secret"]
            if "youtube_refresh_token" in payload:
                settings.publishing.youtube_refresh_token = payload["youtube_refresh_token"]
            if "youtube_channel_id" in payload:
                settings.publishing.youtube_channel_id = payload["youtube_channel_id"]
            if "meta_app_id" in payload:
                settings.publishing.meta_app_id = payload["meta_app_id"]
            if "meta_app_secret" in payload:
                settings.publishing.meta_app_secret = payload["meta_app_secret"]
            if "instagram_access_token" in payload:
                settings.publishing.instagram_access_token = payload["instagram_access_token"]
            if "instagram_business_account_id" in payload:
                settings.publishing.instagram_business_account_id = payload["instagram_business_account_id"]
            if "facebook_page_id" in payload:
                settings.publishing.facebook_page_id = payload["facebook_page_id"]
                
            logger.info("Credentials successfully injected from AWS Secrets Manager.")
            
    except Exception as e:
        logger.error(
            f"Failed to retrieve secrets from AWS Secrets Manager ({str(e)}). "
            f"Halting startup."
        )
        sys.exit(1)

    # Fail-fast validations for production mode
    if settings.app.env == "production":
        if settings.security.secret_key in (None, "", "supersecretkey_change_me_in_production", "local_dev_secret_key_do_not_use_in_prod"):
            logger.critical("PRODUCTION DEPLOYMENT ERROR: JWT secret key is not set or using default fallback! Halting startup.")
            sys.exit(1)
        if "sqlite" in settings.db.url.lower():
            logger.critical("PRODUCTION DEPLOYMENT ERROR: SQLite database is configured for production! Halting startup.")
            sys.exit(1)

    # Perform final S3 and Bedrock validation checks
    verify_aws_startup_prerequisites()
