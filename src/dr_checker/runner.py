class Runner:
    def __init__(self, context, checks):
        self.context = context
        self.checks = checks
        self.results_by_name = {}

    def run_all(self):
        results = []

        for check in self.checks:
            # config_flag
            if getattr(check, "config_flag", None):
                flag = check.config_flag
                if not getattr(self.context.config, flag, False):
                    r = CheckResult(check.name, "SKIP", f"Disabled by config: {flag}=false")
                    results.append(r)
                    self.results_by_name[check.name] = r.status
                    continue

            # requires
            unmet = None
            for dep in getattr(check, "requires", []):
                if self.results_by_name.get(dep) != "PASS":
                    unmet = dep
                    break
            if unmet:
                r = CheckResult(check.name, "SKIP", f"Dependency not met: {unmet}")
                results.append(r)
                self.results_by_name[check.name] = r.status
                continue

            # run
            try:
                r = check.run(self.context)
            except Exception as e:
                r = CheckResult(check.name, "ERROR", str(e))

            results.append(r)
            self.results_by_name[check.name] = r.status

        return results

    def print_report(self, results):
        for r in results:
            print(f"[{r.status}] {r.name} - {r.message}")
