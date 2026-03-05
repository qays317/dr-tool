from dr_checker.base import BaseCheck
from dr_checker.result import CheckResult


class EcsReadinessCheck(BaseCheck):
    name = "ECS Readiness"
    severity = "CRITICAL"

    config_flag = "ecs_enabled"
    requires = ["AWS Identity"]

    def run(self, context):

        ecs = context.client("ecs", region=context.config.primary_region)
        family = context.config.ecs_task_family

        # -------------------------
        # 1) Check Task Definition
        # -------------------------
        resp = ecs.list_task_definitions(
            familyPrefix=family,
            sort="DESC",
            maxResults=1
        )

        arns = resp.get("taskDefinitionArns", [])

        if not arns:
            return CheckResult(
                self.name,
                "FAIL",
                f"TaskDefinition '{family}' not found"
            )

        # -------------------------
        # 2) Read images
        # -------------------------
        primary_uri = context.get_primary_image_uri()
        dr_uri = context.get_dr_image_uri()
        
        if not primary_uri or not dr_uri:
            return CheckResult(
                self.name,
                "FAIL",
                "Missing image URIs: provide --runtime-dir OR set primary_ecr_image_uri/dr_ecr_image_uri in config.yaml"
            )

        # -------------------------
        # 3) Check images in ECR
        # -------------------------
        ok1 = self.image_exists(context, primary_uri, context.config.primary_region)
        ok2 = self.image_exists(context, dr_uri, context.config.dr_region)

        if not ok1 or not ok2:
            return CheckResult(
                self.name,
                "FAIL",
                "ECR image missing in one of the regions"
            )

        return CheckResult(
            self.name,
            "PASS",
            "Task definition and images are ready"
        )

    def image_exists(self, context, uri, region):

        repo, tag = uri.split(".amazonaws.com/")[1].split(":")

        ecr = context.client("ecr", region=region)

        try:
            ecr.describe_images(
                repositoryName=repo,
                imageIds=[{"imageTag": tag}]
            )
            return True
        except Exception:
            return False
