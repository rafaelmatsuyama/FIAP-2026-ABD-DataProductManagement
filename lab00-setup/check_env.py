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
        print(f"  [OK] {display_name}: Instalado e importavel.")
        return True
    print(f"  [AVISO] {display_name}: Nao encontrado via Python import.")
    return False


def check_cli(binary_name: str, display_name: str) -> bool:
    """Check if a CLI binary is available on system PATH."""
    path = shutil.which(binary_name)
    if path:
        print(f"  [OK] CLI `{binary_name}` ({display_name}): Disponivel no PATH.")
        return True
    print(f"  [AVISO] CLI `{binary_name}` ({display_name}): Nao encontrado no PATH.")
    return False


def main():
    print("=" * 65)
    print("  [*] MBA ABD - DPM: VERIFICACAO DE AMBIENTE & DEPENDENCIAS")
    print("=" * 65)

    py_ver = sys.version_info
    print(f"  [OK] Python Runtime: v{py_ver.major}.{py_ver.minor}.{py_ver.micro}")

    results_aula01 = []
    print("\n--- 1. Ferramentas Essenciais (Aula 01: Data Products & Contracts) ---")
    results_aula01.append(check_module("duckdb", "DuckDB Python Engine"))
    results_aula01.append(check_module("datacontract", "datacontract-cli (ODCS Engine)"))
    results_aula01.append(check_module("pandas", "Pandas DataFrame"))
    results_aula01.append(check_module("pyarrow", "Apache Arrow (Parquet Engine)"))

    results_proximas = []
    print("\n--- 2. Ferramentas das Proximas Aulas (Aulas 02 e 03) ---")
    results_proximas.append(check_module("dbt", "dbt-core (Aula 02)"))
    results_proximas.append(check_module("dbt.adapters.duckdb", "dbt-duckdb Adapter (Aula 02)"))
    results_proximas.append(check_module("soda", "Soda Core Engine (Aula 03)"))

    print("\n" + "=" * 65)
    if all(results_aula01):
        print("  [OK] AMBIENTE 100% PRONTO PARA OS LABS DA AULA 01!")
        if not all(results_proximas):
            print("  (As ferramentas das Aulas 02 e 03 serao adicionadas nas proximas sessoes)")
    else:
        print("  [AVISO] FALTAM PACOTES ESSENCIAIS DA AULA 01.")
        print("  Execute: pip install -r ../requirements.txt")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
