# dr-tool

```text
dr-checker/
├── dr_checker/
│   ├── __init__.py
│   │
│   ├── config.py          # قراءة + validation لـ config.yaml
│   ├── context.py         # AWS session + clients
│   ├── base.py            # BaseCheck
│   ├── result.py          # CheckResult
│   ├── runner.py          # orchestration
│   │
│   ├── checks/
│   │   ├── __init__.py
│   │   │
│   │   ├── global/
│   │   │   ├── __init__.py
│   │   │   └── aws_identity.py
│   │   │
│   │   ├── rds/
│   │   │   ├── __init__.py
│   │   │   ├── snapshot_freshness.py
│   │   │   ├── snapshot_availability.py
│   │   │   └── restore_feasibility.py
│   │   │
│   │   ├── ecs/
│   │   │   ├── __init__.py
│   │   │   ├── task_definition_exists.py
│   │   │   └── image_exists.py
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── ecr_repository.py
│   │   │   └── s3_dr_bucket.py
│   │   │
│   │   └── edge/
│   │       ├── __init__.py
│   │       └── cloudfront_failover.py
│   │
│   └── main.py            # CLI entrypoint
│
├── examples/
│   └── config.yaml
│
├── README.md
└── pyproject.toml

```

Every Check must adhere to this contract

Inside every check file:

```text
class SomethingCheck(BaseCheck):
    name = "Human readable name"
    severity = "CRITICAL | MEDIUM | LOW"

    def run(self, context) -> CheckResult:
        ...

```







