#!/usr/bin/env python3
"""Bouwt dist/Schatveld_Setup.zip — één bestand om naar een vriend te mailen met alles
om Schatveld op te zetten: de modpack, de datapack, de resource pack, de shaderpack, de
uitleg-webpagina en SETUP.txt."""
import os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FILES = [
    ("datapack/build/schatveld-world-1.21.10.mrpack",  "schatveld-world-1.21.10.mrpack"),
    ("datapack/build/schatveld_datapack.zip",          "schatveld_datapack.zip"),
    ("resourcepack/build/schatveld_resources.zip",     "schatveld_resources.zip"),
    ("datapack/build/schatveld-shaders-1.20.1.mrpack", "schatveld-shaders-1.20.1.mrpack"),
    ("docs/how-to-play.html",                          "how-to-play.html"),
    ("dist/SETUP.txt",                                 "SETUP.txt"),
]

def main():
    out = os.path.join(HERE, "Schatveld_Setup.zip")
    missing = [src for src, _ in FILES if not os.path.isfile(os.path.join(ROOT, src))]
    if missing:
        raise SystemExit("Ontbrekende build-artefacten (bouw eerst de packs):\n  " +
                         "\n  ".join(missing))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in FILES:
            z.write(os.path.join(ROOT, src), f"Schatveld/{arc}")
    size = os.path.getsize(out)
    print(f"setup-zip -> {out}  ({size} bytes, {len(FILES)} bestanden)")
    return out

if __name__ == "__main__":
    main()
