import sys
import argparse

from dr_checker.config import Config, ConfigError
from dr_checker.context import Context
from dr_checker.runner import Runner
from dr_checker.checks.global.aws_identity import AwsIdentityCheck
from dr_checker.checks.rds.rds_snapshot_readiness import RdsSnapshotReadinessCheck
from dr_checker.checks.ecs.ecs_readiness import EcsReadinessCheck
from dr_checker.checks.storage.s3_readiness import S3StorageReadinessCheck
from dr_checker.checks.cloudfront.cloudfront_failover import CloudFrontFailoverCheck



def exit_code(results):
    if any(r.status == "ERROR" for r in results):
        return 3
    if any(r.status == "FAIL" for r in results):
        return 2
    return 0


def main():
    parser = argparse.ArgumentParser(prog="dr-checker")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    parser.add_argument("--runtime-dir", default=None, help="Optional runtime directory")
    args = parser.parse_args()

    try:
        config = Config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}")
        return 1

    context = Context(config, runtime_dir=args.runtime_dir)

    checks = [
        AwsIdentityCheck(),
        RdsSnapshotReadinessCheck(),
        EcsReadinessCheck(),
        S3StorageReadinessCheck(),
        CloudFrontFailoverCheck(),
    ]

    runner = Runner(context, checks=checks)

    results = runner.run_all()
    runner.print_report(results)
    sys.exit(exit_code(results))


if __name__ == "__main__":
    sys.exit(main())
