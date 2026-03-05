from dr_checker.base import BaseCheck
from dr_checker.result import CheckResult


def parse_ecr_tag_uri(uri: str):
    """
    Expects tag form:
      <acct>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>
    Returns (repo, tag) or (None, None).
    """
    if not uri or ".amazonaws.com/" not in uri or ":" not in uri:
        return None, None

    repo_and_tag = uri.split(".amazonaws.com/", 1)[1].strip()
    if ":" not in repo_and_tag:
        return None, None

    repo, tag = repo_and_tag.rsplit(":", 1)
    return repo, tag


class EcsReadinessCheck(BaseCheck):
    name = "ECS Readiness"
    severity = "CRITICAL"

    config_flag = "ecs_enabled"
    requires = ["AWS Identity"]

    def run(self, context):
        # 1) Task definition exists
        ecs = context.client("ecs", region=context.config.primary_region)
        family = context.config.ecs_task_family

        resp = ecs.list_task_definitions(
            familyPrefix=family,
            sort="DESC",
            maxResults=1
        )
        arns = resp.get("taskDefinitionArns", [])
        if not arns:
            return CheckResult(self.name, "FAIL", f"TaskDefinition '{family}' not found")

        # 2) Resolve image URIs: runtime > config
        primary_uri = context.ecs_primary_image_uri()
        dr_uri = context.ecs_dr_image_uri()

        if not primary_uri or not dr_uri:
            return CheckResult(
                self.name,
                "FAIL",
                "Missing image URIs: provide --runtime-dir OR set ecs.images.primary_uri / ecs.images.dr_uri in config.yaml"
            )

        # 3) Validate images exist in ECR
        ok1, msg1 = self._image_exists(context, primary_uri, context.config.primary_region)
        ok2, msg2 = self._image_exists(context, dr_uri, context.config.dr_region)

        if not ok1 or not ok2:
            return CheckResult(self.name, "FAIL", f"Primary: {msg1} | DR: {msg2}")

        return CheckResult(self.name, "PASS", f"TaskDef ✅ | Primary: {msg1} | DR: {msg2}")

    def _image_exists(self, context, uri: str, region: str):
        repo, tag = parse_ecr_tag_uri(uri)
        if not repo:
            return False, f"Invalid ECR URI '{uri}'"

        ecr = context.client("ecr", region=region)

        try:
            ecr.describe_images(repositoryName=repo, imageIds=[{"imageTag": tag}])
            return True, f"{repo}:{tag} exists"
        except Exception as e:
            s = str(e)
            if "RepositoryNotFoundException" in s:
                return False, f"Repo '{repo}' not found"
            if "ImageNotFoundException" in s:
                return False, f"Image tag '{tag}' not found in repo '{repo}'"
            if "AccessDenied" in s or "not authorized" in s.lower():
                return False, "Access denied to ECR (check IAM)"
            return False, f"ECR error: {s}"
