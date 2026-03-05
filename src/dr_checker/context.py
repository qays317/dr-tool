import os
import boto3
from typing import Optional, Tuple, Dict, Any


class Context:
    """
    Image URI sources priority:
      1) CLI args (passed to Context)
      2) ENV vars (DRCHECK_PRIMARY_IMAGE_URI / DRCHECK_DR_IMAGE_URI)
      3) config.yaml (ecs.images.primary_uri / ecs.images.dr_uri)
    """

    def __init__(
        self,
        config,
        primary_image_uri: Optional[str] = None,
        dr_image_uri: Optional[str] = None,
    ):
        self.config = config

        self._primary_image_uri_cli = primary_image_uri
        self._dr_image_uri_cli = dr_image_uri

        self.session = boto3.Session()
        self._clients: Dict[Tuple[str, Optional[str]], Any] = {}

    def client(self, service: str, region: Optional[str] = None):
        key = (service, region)
        if key in self._clients:
            return self._clients[key]

        c = self.session.client(service, region_name=region) if region else self.session.client(service)
        self._clients[key] = c
        return c

    # ---- ECS Image URI resolution ----
    def ecs_primary_image_uri(self) -> Optional[str]:
        return (
            self._primary_image_uri_cli
            or os.getenv("DRCHECK_PRIMARY_IMAGE_URI")
            or self.config.ecs_primary_image_uri
        )

    def ecs_dr_image_uri(self) -> Optional[str]:
        return (
            self._dr_image_uri_cli
            or os.getenv("DRCHECK_DR_IMAGE_URI")
            or self.config.ecs_dr_image_uri
        )
