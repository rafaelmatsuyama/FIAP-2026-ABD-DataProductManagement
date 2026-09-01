"""Sanity check script for 8ABDR - DPM Environment.

Validates installation of Python runtime, DuckDB, datacontract-cli, dbt, and Soda Core.
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
        print(f"  [OK] CLI `{binary_name}` ({display_name}): Disponivel em {path}")
        return True
    print(f"  [AVISO] CLI `{binary_name}` ({display_name}): Nao encontrado no PATH.")
    return False


def main():
    print("=" * 65)
    print("  [*] MBA ABD - DPM: VERIFICACAO DE AMBIENTE & DEPENDENCIAS")
    print("=" * 65)

    py_ver = sys.version_info
    print(f"  [OK] Python Runtime: v{py_ver.major}.{py_ver.minor}.{py_ver.micro}")

    results = []
    print("\n--- 1. Bancos & Motores Analiticos ---")
    results.append(check_module("duckdb", "DuckDB Python Engine"))
    results.append(check_cli("duckdb", "DuckDB Interactive CLI"))

    print("\n--- 2. Data Contracts & Modelagem ---")
    results.append(check_module("datacontract", "datacontract-cli (ODCS Engine)"))
    results.append(check_cli("datacontract", "datacontract CLI"))

    print("\n--- 3. Analytics Engineering & Transformacao ---")
    results.append(check_module("dbt", "dbt-core"))
    results.append(check_module("dbt.adapters.duckdb", "dbt-duckdb Adapter"))

    print("\n--- 4. Data Quality & Observabilidade ---")
    results.append(check_module("soda", "Soda Core Engine"))

    print("\n" + "=" * 65)
    if all(results):
        print("  [OK] AMBIENTE 100% PRONTO PARA OS LABS DA DISCIPLINA!")
    else:
        print("  [AVISO] ALGUNS PACOTES OPCIONAIS NAO FORAM ENCONTRADOS.")
        print("  Execute 'pip install -r requirements.txt' para instalar as dependencias.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
