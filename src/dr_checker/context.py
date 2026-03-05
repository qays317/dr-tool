# dr_checker/context.py
import boto3
from typing import Optional, Tuple, Dict, Any

from dr_checker.runtime import Runtime


class Context:
    """
    Shared execution context:
    - config
    - runtime (optional)
    - boto3 session + cached clients

    runtime overrides config for dynamic values:
      runtime > config
    """

    def __init__(self, config, runtime_dir: Optional[str] = None):
        self.config = config
        self.runtime = Runtime(runtime_dir)
        self.session = boto3.Session()
        self._clients: Dict[Tuple[str, Optional[str]], Any] = {}

    def client(self, service: str, region: Optional[str] = None):
        """
        Get cached boto3 client for a service in a region.
        Region can be None for global services (e.g., cloudfront, sts).
        """
        key = (service, region)
        if key in self._clients:
            return self._clients[key]

        if region:
            c = self.session.client(service, region_name=region)
        else:
            c = self.session.client(service)

        self._clients[key] = c
        return c

    # -------------------------
    # ECS Image URI resolution
    # runtime > config
    # -------------------------
    def ecs_primary_image_uri(self) -> Optional[str]:
        return self.runtime.primary_ecr_image_uri or self.config.ecs_primary_image_uri

    def ecs_dr_image_uri(self) -> Optional[str]:
        return self.runtime.dr_ecr_image_uri or self.config.ecs_dr_image_uri
