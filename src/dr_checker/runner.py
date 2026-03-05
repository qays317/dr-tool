from dr_checker.result import CheckResult


class Runner:
    """
    Orchestrates check execution.
    Applies:
      - config_flag gating
      - requires gating
      - exception isolation (ERROR result)
    """

    def __init__(self, context, checks):
        self.context = context
        self.checks = checks
        self.results_by_name = {}  # check.name -> status

    def run_all(self):
        results = []

        for check in self.checks:
            # -----------------------------------------
            # 1) Config flag gating (SKIP before run)
            # -----------------------------------------
            if check.config_flag:
                enabled = getattr(self.context.config, check.config_flag, False)
                if not enabled:
                    r = CheckResult(
                        name=check.name,
                        status="SKIP",
                        message=f"Disabled by config: {check.config_flag}=false",
                        severity=getattr(check, "severity", None),
                    )
                    results.append(r)
                    self.results_by_name[check.name] = r.status
                    continue

            # -----------------------------------------
            # 2) Dependency gating (SKIP before run)
            # -----------------------------------------
            unmet_dep = None
            for dep_name in getattr(check, "requires", []):
                dep_status = self.results_by_name.get(dep_name)
                if dep_status != "PASS":
                    unmet_dep = dep_name
                    break

            if unmet_dep:
                r = CheckResult(
                    name=check.name,
                    status="SKIP",
                    message=f"Dependency not met: {unmet_dep}",
                    severity=getattr(check, "severity", None),
                )
                results.append(r)
                self.results_by_name[check.name] = r.status
                continue

            # -----------------------------------------
            # 3) Execute check (isolate exceptions)
            # -----------------------------------------
            try:
                r = check.run(self.context)

                # Ensure severity is always set on result
                if getattr(r, "severity", None) is None:
                    r.severity = getattr(check, "severity", None)

            except Exception as e:
                r = CheckResult(
                    name=check.name,
                    status="ERROR",
                    message=f"Exception: {e}",
                    severity=getattr(check, "severity", None),
                )

            results.append(r)
            self.results_by_name[check.name] = r.status

        return results

    def print_report(self, results):
        print("\nDR Readiness Report")
        print("=" * 60)

        for r in results:
            sev = f"{r.severity}" if r.severity else "-"
            print(f"[{r.status:<5}] [{sev:<8}] {r.name}")
            if r.message:
                print(f"  {r.message}")

        print("=" * 60)
