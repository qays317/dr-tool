from dr_checker.base import BaseCheck
from dr_checker.result import CheckResult


class S3StorageReadinessCheck(BaseCheck):
    name = "S3 Storage Readiness"
    severity = "MEDIUM"

    # إذا تريدها اختيارية أضف storage.enabled في config
    # config_flag = "s3_enabled"

    requires = ["AWS Identity"]

    def run(self, context):
        msgs = []
        failed = False

        primary_bucket = getattr(context.config, "primary_media_s3_bucket", None)
        dr_bucket = getattr(context.config, "dr_media_s3_bucket", None)

        if not primary_bucket or not dr_bucket:
            # لا نعمل FAIL لأن مشاريع كثيرة لا تستخدم S3 media
            return CheckResult(
                self.name,
                "SKIP",
                "S3 buckets not configured (primary_media_s3_bucket / dr_media_s3_bucket missing)"
            )

        # S3 is global-ish, but we can use regional clients for consistency
        s3_primary = context.client("s3", region=context.config.primary_region)
        s3_dr = context.client("s3", region=context.config.dr_region)

        ok, detail = self._head_bucket(s3_primary, primary_bucket)
        if ok:
            msgs.append(f"Primary Bucket ✅ ('{primary_bucket}')")
        else:
            failed = True
            msgs.append(f"Primary Bucket ❌ ('{primary_bucket}': {detail})")

        ok, detail = self._head_bucket(s3_dr, dr_bucket)
        if ok:
            msgs.append(f"DR Bucket ✅ ('{dr_bucket}')")
        else:
            failed = True
            msgs.append(f"DR Bucket ❌ ('{dr_bucket}': {detail})")

        if failed:
            return CheckResult(self.name, "FAIL", " | ".join(msgs))

        return CheckResult(self.name, "PASS", " | ".join(msgs))

    def _head_bucket(self, s3_client, bucket: str):
        try:
            s3_client.head_bucket(Bucket=bucket)
            return True, "accessible"
        except Exception as e:
            msg = str(e)
            if "404" in msg or "Not Found" in msg:
                return False, "not found"
            if "403" in msg or "AccessDenied" in msg or "Forbidden" in msg:
                return False, "access denied (check IAM/bucket policy)"
            return False, msg
