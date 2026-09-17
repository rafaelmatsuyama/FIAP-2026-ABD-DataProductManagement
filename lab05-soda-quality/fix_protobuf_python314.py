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
                print("[OK] Protobuf compatibility patch is already applied.")
                return
            if "except ImportError:" in text:
                new_text = text.replace("except ImportError:", "except (ImportError, TypeError):")
                p.write_text(new_text, encoding="utf-8")
                print("[OK] Protobuf compatibility patch applied successfully.")
                patched = True
                break
    if not patched:
        print("[INFO] Protobuf api_implementation.py file did not require patching.")

if __name__ == "__main__":
    patch_protobuf()
