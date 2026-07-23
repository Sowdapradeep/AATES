import os
import sys
import logging

# Add root folder to pythonpath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

logger = logging.getLogger("aws_real_verifier")

def verify_aws_prerequisites() -> dict:
    """Verifies that actual AWS resources and credentials exist.
    
    If any resource is missing, raises ValueError identifying the missing prerequisite.
    """
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    verification_results = {}
    missing_prerequisites = []

    print("\n=======================================================")
    print("AATES AWS REAL DEPLOYMENT PREREQUISITE VERIFICATION")
    print("=======================================================\n")

    # 1. AWS Credentials & Authentication Check
    print("Checking AWS credentials...")
    session = boto3.Session()
    credentials = session.get_credentials()
    if not credentials:
        print("[-] FAIL: No active AWS credentials found. Please configure IAM User keys or run inside EC2 IAM Role.")
        missing_prerequisites.append("AWS IAM Credentials (CLI configuration or IAM Role)")
    else:
        print(f"[+] PASS: AWS Access Key ID detected: {credentials.access_key[:8]}...")
        verification_results["credentials"] = "PASS"

    # 2. Secrets Manager Check
    if "credentials" in verification_results:
        print(f"\nChecking AWS Secrets Manager ID '{settings.aws.secret_name}'...")
        try:
            sm_client = session.client("secretsmanager", region_name=settings.aws.region)
            sm_client.get_secret_value(SecretId=settings.aws.secret_name)
            print("[+] PASS: Successfully retrieved secret payload.")
            verification_results["secrets_manager"] = "PASS"
        except ClientError as e:
            err_code = e.response["Error"]["Code"]
            print(f"[-] FAIL: Secrets Manager verification failed: {err_code} - {str(e)}")
            missing_prerequisites.append(f"Secrets Manager Secret '{settings.aws.secret_name}'")
        except Exception as e:
            print(f"[-] FAIL: Secrets Manager connection error: {str(e)}")
            missing_prerequisites.append("Secrets Manager Connection")

    # 3. S3 Bucket Check
    if "credentials" in verification_results:
        print(f"\nChecking Amazon S3 Bucket '{settings.aws.s3_bucket}'...")
        try:
            s3_client = session.client("s3", region_name=settings.aws.region)
            s3_client.head_bucket(Bucket=settings.aws.s3_bucket)
            print("[+] PASS: Bucket exists and is accessible.")
            verification_results["s3_bucket"] = "PASS"
        except ClientError as e:
            print(f"[-] FAIL: Bucket {settings.aws.s3_bucket} not accessible: {str(e)}")
            missing_prerequisites.append(f"Amazon S3 Bucket '{settings.aws.s3_bucket}'")
        except Exception as e:
            print(f"[-] FAIL: S3 connection error: {str(e)}")
            missing_prerequisites.append("S3 Connection")

    # 4. Bedrock Access Check
    if "credentials" in verification_results:
        print("\nChecking Amazon Bedrock access...")
        try:
            bedrock_client = session.client("bedrock", region_name=settings.aws.region)
            bedrock_client.list_foundation_models()
            print("[+] PASS: Successfully listed Bedrock foundation models.")
            verification_results["bedrock"] = "PASS"
        except ClientError as e:
            print(f"[-] FAIL: Bedrock API access denied: {str(e)}")
            missing_prerequisites.append("Amazon Bedrock API Permission")
        except Exception as e:
            print(f"[-] FAIL: Bedrock connection error: {str(e)}")
            missing_prerequisites.append("Bedrock Connection")

    print("\n=======================================================")
    if missing_prerequisites:
        print("VERIFICATION FAILED: MISSING PREREQUISITES DETECTED")
        for item in missing_prerequisites:
            print(f" * MISSING: {item}")
        print("=======================================================\n")
        raise ValueError(f"Prerequisite verification failed. Missing: {', '.join(missing_prerequisites)}")
    
    print("ALL PREREQUISITES VERIFIED SUCCESSFULLY (PASS)")
    print("=======================================================\n")
    return verification_results

if __name__ == "__main__":
    try:
        verify_aws_prerequisites()
        sys.exit(0)
    except Exception as e:
        print(f"Execution halted: {str(e)}")
        sys.exit(1)
