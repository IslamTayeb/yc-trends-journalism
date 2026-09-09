"""Run every view through streamlit.testing with no eras and with three cuts. Run: uv run python dashboard/_apptest_run.py"""
import os
import sys
import time
from pathlib import Path

from streamlit.testing.v1 import AppTest

HERE = Path(__file__).resolve().parent
VIEWS = ["overview", "categories", "era_compare", "cooccurrence", "geography", "diversity", "companies", "rfs", "caveats"]
CUTS = ["Winter 2020", "Winter 2023", "Summer 2025"]

failures = 0
for scenario, state, years in [
    ("no eras / 2021+", {"cuts": [], "names": {}, "before_name": ""}, (2021, 2027)),
    ("3 cuts / 2016+", {"cuts": CUTS, "names": {"Winter 2023": "Post-GPT"}, "before_name": "Early"}, (2016, 2027)),
]:
    for v in VIEWS:
        os.environ["VIEW"] = v
        at = AppTest.from_file(str(HERE / "_apptest_page.py"), default_timeout=120)
        at.session_state["era_state"] = state
        at.session_state["years_rng"] = years
        t = time.time()
        at.run()
        errs = [e.value for e in at.exception] + [str(e.value)[:300] for e in at.error]
        status = "FAIL" if errs else "ok"
        failures += bool(errs)
        print(f"{status:4} {scenario:16} {v:12} {time.time()-t:5.1f}s  widgets: {len(at.main.children) if hasattr(at.main,'children') else '?'}"
              + (f"\n     {errs}" if errs else ""))
        if errs and at.exception:
            print("     " + str(at.exception[0].stack_trace)[-1500:].replace("\n", "\n     "))
print("APPTEST FAILURES:", failures)
sys.exit(1 if failures else 0)
