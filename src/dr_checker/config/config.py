import yaml
import os


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, path: str):
        if not os.path.isfile(path):
            raise ConfigError(f"Config file not found: {path}")

        with open(path, "r") as f:
            try:
                self.raw = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML format: {e}")

        if not isinstance(self.raw, dict):
            raise ConfigError("Config root must be a YAML mapping")

        self._load_regions()
        self._load_dr()
        self._load_rds()
        self._load_ecs()

    # -------------------------
    # Loaders
    # -------------------------

    def _load_regions(self):
        regions = self.raw.get("regions")
        if not regions:
            raise ConfigError("Missing 'regions' section")

        self.primary_region = regions.get("primary")
        self.dr_region = regions.get("dr")

        if not self.primary_region or not self.dr_region:
            raise ConfigError("Both regions.primary and regions.dr are required")

    def _load_dr(self):
        dr = self.raw.get("dr")
        if not dr:
            raise ConfigError("Missing 'dr' section")

        self.dr_mode = dr.get("mode", "cold")
        self.rpo_minutes = dr.get("rpo_minutes")

        if self.rpo_minutes is None:
            raise ConfigError("dr.rpo_minutes is required")

    def _load_rds(self):
        rds = self.raw.get("rds", {})
        self.rds_enabled = bool(rds.get("enabled", False))

        if not self.rds_enabled:
            return

        snapshot = rds.get("snapshot")
        if not snapshot:
            raise ConfigError("rds.snapshot is required when rds.enabled=true")

        tag = snapshot.get("tag")
        if not tag or not tag.get("key") or not tag.get("value"):
            raise ConfigError("rds.snapshot.tag.key and value are required")

        self.rds_snapshot_type = snapshot.get("type", "automated")
        self.rds_snapshot_tag_key = tag["key"]
        self.rds_snapshot_tag_value = tag["value"]

    def _load_ecs(self):
        ecs = self.raw.get("ecs", {})
        self.ecs_enabled = bool(ecs.get("enabled", False))

        if not self.ecs_enabled:
            return

        cluster_tag = ecs.get("cluster_tag")
        if not cluster_tag:
            raise ConfigError("ecs.cluster_tag is required when ecs.enabled=true")

        self.ecs_cluster_tag_key = cluster_tag.get("key")
        self.ecs_cluster_tag_value = cluster_tag.get("value")
        self.ecs_task_family = ecs.get("task_definition_family")

        if not self.ecs_cluster_tag_key or not self.ecs_cluster_tag_value:
            raise ConfigError("ecs.cluster_tag.key and value are required")

        if not self.ecs_task_family:
            raise ConfigError("ecs.task_definition_family is required")
