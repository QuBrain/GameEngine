import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# Pfade konfigurieren
GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option")
MANAGED_DIR = GAME_DIR / "NuclearOption_Data" / "Managed"
TARGET_DLL = MANAGED_DIR / "Assembly-CSharp.dll"

WORK_DIR = Path("./no_code_analysis").resolve()
TOOLS_DIR = WORK_DIR / "tools"
DECOMPILED_DIR = WORK_DIR / "source"
ILSPYCMD_EXE = TOOLS_DIR / "ilspycmd.exe"


def check_prerequisites():
    if not TARGET_DLL.exists():
        print(f"[!] Fehler: Datei nicht gefunden:\n    {TARGET_DLL}")
        print("    Stelle sicher, dass das Spiel dort installiert ist.")
        return False
    return True


def setup_ilspycmd():
    """Lädt die fertige ILSpy CLI automatisch von GitHub herunter falls nicht vorhanden."""
    if ILSPYCMD_EXE.exists():
        return True

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    print(
        "[*] ILSpyCmd wird von GitHub heruntergeladen (einmalige Einrichtung)..."
    )

    try:
        # Neueste Release-Metadaten von GitHub abfragen
        api_url = "https://api.github.com/repos/icsharpcode/ILSpy/releases/latest"
        req = urllib.request.Request(
            api_url, headers={"User-Agent": "Python-Decompiler"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())

        # Nach portablem Windows x64 ZIP suchen
        download_url = None
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if "windows" in name and "x64" in name and name.endswith(".zip"):
                download_url = asset.get("browser_download_url")
                break

        # Fallback falls Name abweicht
        if not download_url:
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break

        if not download_url:
            print("[!] Konnte keinen passenden Release-Download finden.")
            return False

        print(f"[*] Lade herunter: {download_url}")
        with urllib.request.urlopen(
            urllib.request.Request(
                download_url, headers={"User-Agent": "Python-Decompiler"}
            )
        ) as resp:
            zip_bytes = resp.read()

        print("[*] Entpacke Werkzeuge...")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            z.extractall(TOOLS_DIR)

        if not ILSPYCMD_EXE.exists():
            # Rekursiv suchen, falls in Unterordner entpackt
            found = list(TOOLS_DIR.rglob("ilspycmd.exe"))
            if found:
                shutil.copy(found[0], ILSPYCMD_EXE)
            else:
                print(
                    f"[!] ilspycmd.exe konnte im Paket nicht gefunden werden."
                )
                return False

        print("[+] ILSpyCmd erfolgreich eingerichtet.\n")
        return True

    except Exception as e:
        print(f"[!] Fehler beim automatischen Download: {e}")
        print("    Du kannst ILSpy manuell von GitHub herunterladen und die")
        print(f"    'ilspycmd.exe' in folgenden Ordner legen: {TOOLS_DIR}")
        return False


def run_decompilation():
    """Dekompiliert die Assembly-CSharp.dll in C#-Dateien."""
    if (
        DECOMPILED_DIR.exists()
        and any(DECOMPILED_DIR.iterdir())
        and any(DECOMPILED_DIR.rglob("*.cs"))
    ):
        print(f"[+] Bereits dekompiliert in: {DECOMPILED_DIR}")
        return True

    DECOMPILED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Dekompiliere {TARGET_DLL.name}...")
    print("    Das kann ca. 30–60 Sekunden dauern...")

    cmd = [
        str(ILSPYCMD_EXE),
        "-p",  # Als Projekt entpacken (organisiert in .cs Dateien)
        "-o",
        str(DECOMPILED_DIR),
        str(TARGET_DLL),
    ]

    res = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if res.returncode != 0:
        print("[!] Fehler beim Dekompilieren:")
        print(res.stderr)
        return False

    print(f"[+] Fertig! C#-Quelldateien liegen in: {DECOMPILED_DIR}\n")
    return True


def search_classes(keyword: str):
    """Sucht nach Klassendefinitionen."""
    print(f"\n--- Suche nach Klassen mit '{keyword}' ---")
    results = []
    for p in DECOMPILED_DIR.rglob("*.cs"):
        if keyword.lower() in p.stem.lower():
            results.append(p)
            print(f"• {p.stem} -> ({p.relative_to(DECOMPILED_DIR)})")

    if not results:
        print("Keine Klassen gefunden.")
    return results


def search_text_in_files(query: str, max_matches=15):
    """Durchsucht alle Quelldateien nach Methoden, Variablen oder Texten."""
    print(f"\n--- Volltextsuche nach '{query}' ---")
    matches = 0
    q_lower = query.lower()

    for p in DECOMPILED_DIR.rglob("*.cs"):
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    if q_lower in line.lower():
                        print(
                            f"[{p.name}:{line_no}] {line.strip()[:140]}"
                        )  # max 140 Zeichen pro Zeile
                        matches += 1
                        if matches >= max_matches:
                            print(
                                f"\n... Begrenzt auf {max_matches} Treffer."
                            )
                            return
        except Exception:
            continue

    if matches == 0:
        print("Keine Vorkommen gefunden.")


def view_file(class_name: str):
    """Gibt den Inhalt einer gefundenen Klasse aus."""
    candidates = list(DECOMPILED_DIR.rglob(f"{class_name}.cs"))
    if not candidates:
        print(f"Klasse oder Datei '{class_name}.cs' nicht gefunden.")
        return

    target = candidates[0]
    print(f"\n--- Inhalt von {target.name} (erste 80 Zeilen) ---")
    with open(target, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:80], 1):
            print(f"{i:3d} | {line}", end="")
        if len(lines) > 80:
            print(
                f"\n... ({len(lines) - 80} weitere Zeilen in {target.relative_to(WORK_DIR)})"
            )


def interactive_cli():
    """Einfaches Terminal-Menü zum Untersuchen des Spielcodes."""
    while True:
        print("\n" + "=" * 50)
        print("Nuclear Option Code Explorer")
        print("=" * 50)
        print("1. Nach Klassen/Dateinamen suchen")
        print("2. Volltextsuche (Methoden, Felder, Variablen)")
        print("3. C#-Klasse anzeigen (Vorschau)")
        print("4. Windows Explorer im Quellcode-Ordner öffnen")
        print("q. Beenden")

        choice = input("\nWähle eine Option: ").strip()

        if choice == "1":
            term = input("Klassenname / Begriff: ").strip()
            if term:
                search_classes(term)
        elif choice == "2":
            term = input("Suchbegriff: ").strip()
            if term:
                search_text_in_files(term)
        elif choice == "3":
            cname = input(
                "Exakter Klassenname (ohne .cs, z. B. Unit): "
            ).strip()
            if cname:
                view_file(cname)
        elif choice == "4":
            os.startfile(str(DECOMPILED_DIR))
        elif choice.lower() in ("q", "quit", "exit"):
            break


def main():
    if not check_prerequisites():
        return

    if not setup_ilspycmd():
        return

    if not run_decompilation():
        return

    # Interaktiven Explorer starten
    interactive_cli()


if __name__ == "__main__":
    main()