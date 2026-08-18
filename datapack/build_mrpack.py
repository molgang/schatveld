#!/usr/bin/env python3
"""build_mrpack — bouwt launch-klare Modrinth .mrpack-bestanden met ECHTE mod-versies
(sha512 + downloads uit de Modrinth-API). Twee packs:

  1. schatveld-shaders-1.20.1.mrpack  — de Iris-workaround voor Apple Silicon.
     macOS geeft max OpenGL 4.1; Iris ≥1.7 eist 4.3 → crasht op Mac. Iris 1.6.17 +
     Sodium 0.5.3 op MC 1.20.1 draaien shaders NATIEF op GL 4.1. Shaderpack:
     Complementary Reimagined (4.1-compatibel). Iris-config zet de shader meteen aan.

  2. schatveld-world-1.21.10.mrpack   — de rijkere spelwereld (de brain-game).
     Sodium/Lithium/FerriteCore/EntityCulling + EMF/ETF + BetterArcheology + fabric-api.
     Geen Iris (zou op Mac 4.1 crashen); de resource pack + datapack zitten in overrides/.
"""
import json, os, ssl, sys, urllib.parse, urllib.request, zipfile

API = "https://api.modrinth.com/v2"
UA = {"User-Agent": "schatveld/2.0 (develuse@gmail.com)"}
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)

# macOS' systeem-Python mist vaak de CA-bundel; gebruik certifi als die er is.
try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _CTX = ssl.create_default_context()


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
        return json.load(r)


def resolve(slug, mc, loaders, pin=None):
    """Zoek de beste versie van een project; return een mrpack-file-dict."""
    qs = urllib.parse.urlencode({
        "loaders": json.dumps(loaders),
        "game_versions": json.dumps([mc]),
    })
    vs = _get(f"{API}/project/{slug}/version?{qs}")
    if pin:
        vs = [v for v in vs if pin in v["version_number"]] or vs
    if not vs:
        raise RuntimeError(f"geen versie voor {slug} @ {mc} {loaders}")
    v = vs[0]
    f = next((f for f in v["files"] if f.get("primary")), v["files"][0])
    return {
        "slug": slug,
        "version": v["version_number"],
        "file": {
            "path": None,  # door de aanroeper gezet (mods/ of shaderpacks/)
            "hashes": {"sha1": f["hashes"]["sha1"], "sha512": f["hashes"]["sha512"]},
            "env": {"client": "required", "server": "required"},
            "downloads": [f["url"]],
            "fileSize": f["size"],
        },
        "filename": f["filename"],
    }


def make_pack(out_name, version_id, name, summary, mc, loader_ver,
              mods, shaders=(), overrides_dirs=(), client_only=()):
    files = []
    for slug, pin in mods:
        r = resolve(slug, mc, ["fabric"], pin)
        r["file"]["path"] = f"mods/{r['filename']}"
        if slug in client_only:
            r["file"]["env"] = {"client": "required", "server": "unsupported"}
        files.append(r["file"])
        print(f"   mod  {slug:22s} {r['version']}")
    for slug, pin in shaders:
        r = resolve(slug, mc, ["iris"], pin)
        r["file"]["path"] = f"shaderpacks/{r['filename']}"
        r["file"]["env"] = {"client": "required", "server": "unsupported"}
        files.append(r["file"])
        print(f"   shad {slug:22s} {r['version']}")

    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": version_id,
        "name": name,
        "summary": summary,
        "files": files,
        "dependencies": {"minecraft": mc, "fabric-loader": loader_ver},
    }

    out = os.path.join(BUILD, out_name)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("modrinth.index.json", json.dumps(index, indent=2))
        for od in overrides_dirs:
            src, arc = od  # (absoluut pad, pad-in-overrides)
            if os.path.isfile(src):
                z.write(src, f"overrides/{arc}")
            elif os.path.isdir(src):
                for root, _, fns in os.walk(src):
                    for fn in fns:
                        full = os.path.join(root, fn)
                        rel = os.path.relpath(full, src)
                        z.write(full, f"overrides/{arc}/{rel}")
    print(f"-> {out}  ({len(files)} downloads, {len(overrides_dirs)} overrides)")
    return out, index


def main():
    fabric_loader = "0.19.3"

    # config-override om Iris meteen met de shader te starten (in overrides/)
    iris_cfg_dir = os.path.join(BUILD, "_iris_cfg", "config")
    os.makedirs(iris_cfg_dir, exist_ok=True)
    with open(os.path.join(iris_cfg_dir, "iris.properties"), "w") as fh:
        fh.write("enableShaders=true\n"
                 "shaderPack=ComplementaryReimagined_r5.8.1.zip\n"
                 "maxShadowRenderDistance=32\n")

    print("[1/2] Shader-showcase (Iris-workaround, MC 1.20.1, macOS-native GL 4.1)")
    make_pack(
        "schatveld-shaders-1.20.1.mrpack",
        version_id="2.0-shaders",
        name="Schatveld — Shader Showcase (macOS-native)",
        summary="Iris 1.6.17 + Sodium 0.5.3 + Complementary Reimagined op MC 1.20.1 — "
                "shaders die WEL op Apple Silicon (OpenGL 4.1) draaien.",
        mc="1.20.1", loader_ver=fabric_loader,
        mods=[("fabric-api", None), ("sodium", "0.5.3"), ("iris", "1.6.17"),
              ("lithium", None), ("ferrite-core", None), ("entityculling", None)],
        shaders=[("complementary-reimagined", "r5.8.1")],
        client_only={"sodium", "iris", "entityculling"},
        overrides_dirs=[(os.path.join(BUILD, "_iris_cfg", "config"), "config")],
    )

    rp = os.path.join(os.path.dirname(HERE), "resourcepack", "build",
                      "schatveld_resources.zip")
    dp = os.path.join(BUILD, "schatveld_datapack.zip")
    print("\n[2/2] Rijkere spelwereld (MC 1.21.10, brain-game + BetterArcheology)")
    overrides = []
    if os.path.isfile(rp):
        overrides.append((rp, "resourcepacks/schatveld_resources.zip"))
    if os.path.isfile(dp):
        overrides.append((dp, "schatveld_datapack.zip"))  # los meegeleverd voor de wereld
    make_pack(
        "schatveld-world-1.21.10.mrpack",
        version_id="2.0-world",
        name="Schatveld — Wereld (One Brain, Two Worlds)",
        summary="De rijkere Schatveld-marschwereld: Sodium/Lithium + EMF/ETF + "
                "BetterArcheology + fabric-api, met resource pack en datapack.",
        mc="1.21.10", loader_ver=fabric_loader,
        mods=[("fabric-api", None), ("sodium", None), ("lithium", None),
              ("ferrite-core", None), ("entityculling", None),
              ("entity-model-features", None), ("entitytexturefeatures", None),
              ("better-archeology", None)],
        client_only={"sodium", "entityculling", "entity-model-features",
                     "entitytexturefeatures"},
        overrides_dirs=overrides,
    )
    print("\nklaar.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FOUT:", e, file=sys.stderr)
        sys.exit(1)
