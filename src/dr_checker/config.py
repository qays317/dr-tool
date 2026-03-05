# dr_checker/config.py
import yaml


class ConfigError(Exception):
    """Raised when config.yaml is missing/invalid or required fields are absent."""
    pass


class Config:
    """
    Loads tool configuration from YAML.

    Expected structure (minimal):

    regions:
      primary: us-east-1
      dr: ca-central-1

    ecs:
      enabled: true
      task_definition_family: wordpress-task
      images:
        primary_uri: ""   # optional if runtime is provided
        dr_uri: ""        # optional if runtime is provided

    rds:
      enabled: true
      engine: mysql
      snapshot:
        type: automated
        tag:
          key: app
          value: wordpress

    s3 (optional - our S3 check will SKIP if buckets not provided):
      media:
        primary_bucket: wordpress-media-primary-2004
        dr_bucket: wordpress-media-dr-2004

    cloudfront (optional):
      distribution_id: E1234567890
    """

    def __init__(self, path: str):
        self.path = path
        data = self._load_yaml(path)

        # -------------------------
        # Regions (required)
        # -------------------------
        regions = data.get("regions", {}) or {}
        self.primary_region = regions.get("primary")
        self.dr_region = regions.get("dr")

        if not self.primary_region or not self.dr_region:
            raise ConfigError("regions.primary and regions.dr are required")

        # -------------------------
        # ECS (optional - gated by ecs.enabled)
        # -------------------------
        ecs = data.get("ecs", {}) or {}
        self.ecs_enabled = bool(ecs.get("enabled", False))
        self.ecs_task_family = ecs.get("task_definition_family")

        ecs_images = ecs.get("images", {}) or {}
        self.ecs_primary_image_uri = ecs_images.get("primary_uri") or None
        self.ecs_dr_image_uri = ecs_images.get("dr_uri") or None

        if self.ecs_enabled and not self.ecs_task_family:
            raise ConfigError("ecs.task_definition_family is required when ecs.enabled=true")

        # -------------------------
        # RDS (optional - gated by rds.enabled)
        # -------------------------
        rds = data.get("rds", {}) or {}
        self.rds_enabled = bool(rds.get("enabled", False))
        self.rds_engine = rds.get("engine") or None

        snap = rds.get("snapshot", {}) or {}
        self.rds_snapshot_type = snap.get("type", "automated")  # automated|manual
        tag = snap.get("tag", {}) or {}
        self.rds_snapshot_tag_key = tag.get("key") or None
        self.rds_snapshot_tag_value = tag.get("value") or None

        # RPO optional (used by RDS readiness check if you implemented freshness)
        dr = data.get("dr", {}) or {}
        self.rpo_minutes = int(dr.get("rpo_minutes", 60))

        # minimal validation for RDS if enabled
        if self.rds_enabled:
            if not self.rds_engine:
                raise ConfigError("rds.engine is required when rds.enabled=true")
            if not self.rds_snapshot_tag_key or not self.rds_snapshot_tag_value:
                raise ConfigError("rds.snapshot.tag.key and rds.snapshot.tag.value are required when rds.enabled=true")

        # -------------------------
        # S3 buckets (optional)
        # -------------------------
        s3 = data.get("s3", {}) or {}
        media = s3.get("media", {}) or {}
        self.primary_media_s3_bucket = media.get("primary_bucket") or None
        self.dr_media_s3_bucket = media.get("dr_bucket") or None

        # -------------------------
        # CloudFront (optional)
        # -------------------------
        cloudfront = data.get("cloudfront", {}) or {}
        self.cloudfront_distribution_id = cloudfront.get("distribution_id") or None

    # -------------------------
    # Internal helpers
    # -------------------------
    def _load_yaml(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                return loaded if isinstance(loaded, dict) else {}
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read config {path}: {e}")
