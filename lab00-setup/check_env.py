"""Sanity check script for MBA ABD - DPM Environment.

Validates installation of Python runtime, DuckDB, datacontract-cli, and upcoming tools.
"""

import importlib.util
import shutil
import sys


def check_module(module_name: str, display_name: str) -> bool:
    """Check if a Python module is installed."""
    try:
        spec = importlib.util.find_spec(module_name)
    except (ModuleNotFoundError, ValueError, AttributeError):
        spec = None

    if spec is not None:
        print(f"  [OK] {display_name}: Installed and importable.")
        return True
    print(f"  [WARN] {display_name}: Not found via Python import.")
    return False


def check_cli(binary_name: str, display_name: str) -> bool:
    """Check if a CLI binary is available on system PATH."""
    path = shutil.which(binary_name)
    if path:
        print(f"  [OK] CLI `{binary_name}` ({display_name}): Available on PATH.")
        return True
    print(f"  [WARN] CLI `{binary_name}` ({display_name}): Not found on PATH.")
    return False


def main():
    print("=" * 65)
    print("  [*] MBA ABD - DPM: ENVIRONMENT & DEPENDENCY VERIFICATION")
    print("=" * 65)

    py_ver = sys.version_info
    print(f"  [OK] Python Runtime: v{py_ver.major}.{py_ver.minor}.{py_ver.micro}")

    results_aula01 = []
    print("\n--- 1. Core Tooling (Session 01: Data Products & Contracts) ---")
    results_aula01.append(check_module("duckdb", "DuckDB Python Engine"))
    results_aula01.append(check_module("datacontract", "datacontract-cli (ODCS Engine)"))
    results_aula01.append(check_module("pandas", "Pandas DataFrame"))
    results_aula01.append(check_module("pyarrow", "Apache Arrow (Parquet Engine)"))

    results_proximas = []
    print("\n--- 2. Tooling for Upcoming Sessions (Sessions 02 & 03) ---")
    results_proximas.append(check_module("dbt", "dbt-core (Session 02)"))
    results_proximas.append(check_module("dbt.adapters.duckdb", "dbt-duckdb Adapter (Session 02)"))
    results_proximas.append(check_module("soda", "Soda Core Engine (Session 03)"))

    print("\n" + "=" * 65)
    if all(results_aula01):
        print("  [OK] ENVIRONMENT 100% READY FOR SESSION 01 LABS!")
        if not all(results_proximas):
            print("  (Tools for Sessions 02 & 03 will be installed in upcoming labs)")
    else:
        print("  [WARN] CORE PACKAGES MISSING FOR SESSION 01.")
        print("  Run: pip install -r ../requirements-aula01.txt")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
