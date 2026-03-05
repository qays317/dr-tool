import sys
import json
import argparse

from dr_checker.config import Config, ConfigError
from dr_checker.context import Context
from dr_checker.runner import Runner
from dr_checker.checks.global.aws_identity import AwsIdentityCheck
from dr_checker.checks.rds.rds_snapshot_readiness import RdsSnapshotReadinessCheck
from dr_checker.checks.ecs.ecs_readiness import EcsReadinessCheck
from dr_checker.checks.storage.s3_readiness import S3StorageReadinessCheck
from dr_checker.checks.cloudfront.cloudfront_failover import CloudFrontFailoverCheck


SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "CRITICAL": 3}


def main():
    parser = argparse.ArgumentParser(prog="dr-checker")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    parser.add_argument("--runtime-dir", default=None, help="Optional runtime directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on", choices=["LOW", "MEDIUM", "CRITICAL"], default="CRITICAL")
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

    try:
        results = runner.run_all()
    except Exception as e:
        # خطأ عام غير متوقع
        if args.format == "json":
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"ERROR: {e}")
        return 3

    # تحديد هل يوجد FAIL نعتبره قاتل بناءً على fail-on
    fail_threshold = SEVERITY_ORDER[args.fail_on]

    fatal_fails = [
        r for r in results
        if r.status == "FAIL" and SEVERITY_ORDER.get(r.severity, 0) >= fail_threshold
    ]

    exit_code = 2 if fatal_fails else 0

    if args.format == "json":
        payload = {
            "summary": {
                "total": len(results),
                "pass": sum(1 for r in results if r.status == "PASS"),
                "fail": sum(1 for r in results if r.status == "FAIL"),
                "skip": sum(1 for r in results if r.status == "SKIP"),
                "warn": sum(1 for r in results if r.status == "WARN"),
                "fail_on": args.fail_on,
                "exit_code": exit_code,
            },
            "checks": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        runner.print_report(results)
        print(f"\nExit code: {exit_code} (fail-on={args.fail_on})")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
