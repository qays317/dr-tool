from dr_checker.base import BaseCheck
from dr_checker.result import CheckResult


class CloudFrontFailoverCheck(BaseCheck):

    name = "CloudFront Origin Failover"
    severity = "LOW"

    requires = ["AWS Identity"]

    def run(self, context):

        distribution_id = getattr(context.config, "cloudfront_distribution_id", None)

        if not distribution_id:
            return CheckResult(
                self.name,
                "SKIP",
                "CloudFront distribution not configured"
            )

        cf = context.client("cloudfront")

        try:
            resp = cf.get_distribution_config(Id=distribution_id)
        except Exception as e:
            return CheckResult(
                self.name,
                "FAIL",
                f"Cannot read distribution: {str(e)}"
            )

        dist_config = resp["DistributionConfig"]

        origin_groups = dist_config.get("OriginGroups", {}).get("Items", [])

        if not origin_groups:
            return CheckResult(
                self.name,
                "WARN",
                "No Origin Groups configured (failover disabled)"
            )

        group = origin_groups[0]

        members = group["Members"]["Items"]

        if len(members) < 2:
            return CheckResult(
                self.name,
                "WARN",
                "Origin Group has less than 2 origins"
            )

        failover_codes = group["FailoverCriteria"]["StatusCodes"]["Items"]

        return CheckResult(
            self.name,
            "PASS",
            f"Origin group configured (failover codes: {failover_codes})"
        )
