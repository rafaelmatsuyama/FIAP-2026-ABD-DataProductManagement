import pathlib
import site
import sys

def patch_protobuf():
    packages = site.getsitepackages()
    patched = False
    for pkg in packages:
        p = pathlib.Path(pkg) / "google" / "protobuf" / "internal" / "api_implementation.py"
        if p.exists():
            text = p.read_text(encoding="utf-8")
            if "except (ImportError, TypeError):" in text:
                print("[OK] Protobuf ja esta com o patch de compatibilidade aplicado.")
                return
            if "except ImportError:" in text:
                new_text = text.replace("except ImportError:", "except (ImportError, TypeError):")
                p.write_text(new_text, encoding="utf-8")
                print("[OK] Patch de compatibilidade do Protobuf aplicado com sucesso.")
                patched = True
                break
    if not patched:
        print("[INFO] Arquivo api_implementation.py do Protobuf nao precisou de patch.")

if __name__ == "__main__":
    patch_protobuf()
