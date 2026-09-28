#!/usr/bin/env python3
"""Fetch and verify the MakeHuman human-body system (CC0 assets) into odyssey/.cache/makehuman/.

    python3 odyssey/body/fetch_makehuman.py            # download what is missing, verify all, write manifest
    python3 odyssey/body/fetch_makehuman.py --refresh  # re-download everything

Sources -- only hosts reachable from the sandbox proxy, no git clone, no GitHub API:

  gh/makehuman/...   raw.githubusercontent.com/makehumancommunity/makehuman @ MH_SHA
                     base mesh (base.obj), default rig + weights, modifier JSON, eyes, every .target.
                     Every asset file carries the header "This asset was explicitly released as CC0 in
                     september 2020"; LICENSE.md section C says the bundled assets are CC0 1.0.
  gh/mpfb2/...       raw.githubusercontent.com/makehumancommunity/mpfb2 @ MPFB_SHA
                     default / game_engine / mixamo rigs + skin weights as JSON (CC0, LICENSE.md section C).
  ubuntu/...         archive.ubuntu.com bionic/universe makehuman-data_1.1.1-1_all.deb, i.e. the
                     MakeHuman 1.1.1 *system assets*: clothes, hair, eyebrows, eyelashes, teeth, tongue,
                     skins + textures, proxies, poses.  The GitHub repo that used to host them
                     (makehumancommunity/makehuman-assets) now returns 404 and the community file server
                     is blocked, so this Ubuntu package is the reachable copy.
                     Trust chain: InRelease (gpgv + /usr/share/keyrings/ubuntu-archive-keyring.gpg)
                     -> sha256(Packages.xz) -> sha256(.deb) -> md5 of every extracted file (deb md5sums).
                     These 2016 files still carry an "AGPLv3" header; the copyright holders re-released
                     all MakeHuman bundled assets (base mesh, proxies, targets, textures, any MHCLO asset,
                     poses) as CC0 in September 2020 -- see gh/makehuman/LICENSE.md section C.

Compiled meshes: the 1.1.1 package ships each clothes/hair/eyebrow mesh as a compiled .npz
(coord, texco, fvert, fuvs, ...) instead of .obj; the .mhclo fitting data is plain text.  Both are
checked against each other here (number of .mhclo reference rows == number of mesh vertices).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import io
import json
import lzma
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_DEST = HERE.parent / ".cache" / "makehuman"

MH_REPO, MH_SHA = "makehumancommunity/makehuman", "a8bc2d54ff0ac92e78ff71431b1023eda42bf482"
MPFB_REPO, MPFB_SHA = "makehumancommunity/mpfb2", "3edf9df0551765be43563d047888cf7877eb89b4"
RAW = "https://raw.githubusercontent.com/{repo}/{sha}/{path}"

UBUNTU = "http://archive.ubuntu.com/ubuntu"
UBUNTU_SUITE = "bionic"
UBUNTU_KEYRING = "/usr/share/keyrings/ubuntu-archive-keyring.gpg"
DEB_PKG, DEB_VER = "makehuman-data", "1.1.1-1"
DEB_ROOT = "usr/share/makehuman/data/"
# application-only folders of the package that are not needed for a body model
DEB_SKIP_DIRS = {"themes", "icons", "languages", "shaders", "povray", "scenes"}

MH_FILES = [
    "LICENSE.md", "LICENSE.ASSETS.md",
    "makehuman/data/3dobjs/base.obj", "makehuman/data/3dobjs/base.mhclo",
    "makehuman/data/rigs/default.mhskel", "makehuman/data/rigs/default_weights.mhw",
    "makehuman/data/modifiers/modeling_modifiers.json", "makehuman/data/modifiers/modeling_modifiers_desc.json",
    "makehuman/data/modifiers/modeling_sliders.json",
    "makehuman/data/modifiers/measurement_modifiers.json", "makehuman/data/modifiers/measurement_modifiers_desc.json",
    "makehuman/data/modifiers/measurement_sliders.json",
    "makehuman/data/modifiers/bodyshapes_modifiers.json", "makehuman/data/modifiers/bodyshapes_modifiers_desc.json",
    "makehuman/data/modifiers/bodyshapes_sliders.json",
    "makehuman/data/eyes/high-poly/high-poly.mhclo", "makehuman/data/eyes/high-poly/high-poly.obj",
    "makehuman/data/eyes/low-poly/low-poly.mhclo", "makehuman/data/eyes/low-poly/low-poly.obj",
    "makehuman/data/skins/default.mhmat",
    "makehuman/data/litspheres/skinmat_asian.png",
    "makehuman/data/eyes/materials/brown.mhmat", "makehuman/data/eyes/materials/brown_eye.png",
]  # the other eye colours exist only in the 1.1.1 package (ubuntu/.../data/eyes/materials/)

MPFB_FILES = ["LICENSE.md", "LICENSE.ASSETS.md", "src/mpfb/data/targets/target.json"] + [
    f"src/mpfb/data/rigs/standard/{kind}.{rig}.json"
    for rig in ("default", "game_engine", "mixamo") for kind in ("rig", "weights")]

UA = {"User-Agent": "odyssey-fetch-makehuman/1.0"}


class NotFound(Exception):
    pass


def http_get(url: str, retries: int = 5) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFound(url)
            last = e
        except Exception as e:  # network hiccup through the proxy
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {last}")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------
# per-file validation (parses the file; returns a short summary string or raises)

def _text(b: bytes) -> str:
    return b.decode("utf-8", errors="strict")


def check_obj(b: bytes) -> str:
    nv = nt = nf = 0
    for line in _text(b).splitlines():
        if line.startswith("v "):
            nv += 1
        elif line.startswith("vt "):
            nt += 1
        elif line.startswith("f "):
            nf += 1
    if nv == 0 or nf == 0:
        raise ValueError("no vertices/faces")
    return f"obj v={nv} vt={nt} f={nf}"


def parse_target(b: bytes):
    idx, vec = [], []
    for line in _text(b).splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split()
        idx.append(int(p[0]))
        vec.append((float(p[1]), float(p[2]), float(p[3])))
    return np.asarray(idx, np.int64), np.asarray(vec, np.float64).reshape(-1, 3)


def check_target(b: bytes) -> str:
    i, v = parse_target(b)
    if len(i) and (i.min() < 0 or i.max() >= 19158):
        raise ValueError("vertex index out of hm08 range")
    return f"target n={len(i)}"


def parse_mhclo(text: str) -> dict:
    """Header fields + number of vertex-reference rows of a .mhclo/.proxy file.

    As in MakeHuman's own parser, the reference rows ("i0 i1 i2 w0 w1 w2 dx dy dz", or a single
    vertex index) follow a "verts <n>" line; ordinary keyword lines may be interleaved and do not
    end the block, only "delete_verts" does.
    """
    out = {"obj_file": None, "material": None, "name": None, "basemesh": None,
           "license": [], "author": [], "n_ref": 0}
    in_verts = False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            if "cc0" in s.lower():
                out["license"].append(s.lstrip("# ").strip())
            continue
        p = s.split()
        if in_verts and re.fullmatch(r"-?\d+", p[0]):
            if len(p) in (1, 9):
                out["n_ref"] += 1
            continue
        key = p[0]
        if key == "verts":
            in_verts = True
        elif key == "delete_verts":
            in_verts = False
        elif key in ("obj_file", "material", "name", "basemesh"):
            out[key] = " ".join(p[1:])
        elif key == "license":
            out["license"].append(" ".join(p[1:]))
        elif key == "author":
            out["author"].append(" ".join(p[1:]))
    return out


def check_image(b: bytes) -> str:
    from PIL import Image
    im = Image.open(io.BytesIO(b))
    im.verify()
    im = Image.open(io.BytesIO(b))
    return f"image {im.format} {im.size[0]}x{im.size[1]} {im.mode}"


def check_npz(b: bytes) -> str:
    d = np.load(io.BytesIO(b), allow_pickle=False)
    if "coord" in d.files:
        return f"npz mesh v={len(d['coord'])} f={len(d['fvert'])} uv={len(d['texco'])}"
    return f"npz keys={len(d.files)}"


def validate(path: str, b: bytes) -> str:
    ext = os.path.splitext(path)[1].lower()
    if len(b) == 0:
        if ext == ".mhuv":  # data/uvs/default.mhuv is a 0-byte placeholder in the 1.1.1 package
            return "empty placeholder (as packaged)"
        raise ValueError("empty file")
    if ext == ".obj":
        return check_obj(b)
    if ext == ".target":
        return check_target(b)
    if ext in (".png", ".jpg", ".jpeg", ".thumb"):
        return check_image(b)
    if ext == ".npz":
        return check_npz(b)
    if ext in (".json", ".mhskel", ".mhw"):
        d = json.loads(_text(b))
        return f"json {type(d).__name__} len={len(d)}"
    if ext in (".mhclo", ".proxy"):
        m = parse_mhclo(_text(b))
        return f"mhclo obj_file={m['obj_file']} ref_rows={m['n_ref']}"
    if ext == ".mhmat":
        t = _text(b)
        if not re.search(r"^name\s", t, re.M):
            raise ValueError("mhmat without name")
        return "mhmat"
    if ext == ".bvh":
        if not _text(b).lstrip().startswith("HIERARCHY"):
            raise ValueError("not a BVH")
        return "bvh"
    if ext in (".md", ".txt", ".meta", ".mhpose", ".csv", ".list", ".mhuv", ".mhanim", ".mht", ".ini", ".gz"):
        return f"file {len(b)} bytes"
    return f"file {len(b)} bytes"


def header_license(b: bytes) -> str | None:
    head = b[:1500].decode("utf-8", errors="ignore")
    if "released as CC0" in head:
        return "CC0-1.0 (file header: explicitly released as CC0 in september 2020)"
    if "licensed AGPLv3" in head or "AGPL" in head:
        return "AGPLv3 (2016 file header)"
    return None


# ----------------------------------------------------------------------------------------------

class Fetcher:
    def __init__(self, dest: Path, refresh: bool, jobs: int):
        self.dest = dest
        self.refresh = refresh
        self.jobs = jobs
        self.entries: list[dict] = []
        self.missing: list[dict] = []
        self.errors: list[str] = []

    # -- GitHub raw -----------------------------------------------------------------------------
    def gh_one(self, repo: str, sha: str, path: str, local_root: str, license_default: str) -> dict | None:
        url = RAW.format(repo=repo, sha=sha, path=path)
        local = self.dest / local_root / path
        fetched = False
        if local.exists() and local.stat().st_size > 0 and not self.refresh:
            b = local.read_bytes()
        else:
            try:
                b = http_get(url)
            except NotFound:
                self.missing.append({"url": url, "path": path})
                return None
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(b)
            fetched = True
        e = {"local_path": str(local.relative_to(self.dest)), "source": f"github:{repo}@{sha[:7]}",
             "url": url, "bytes": len(b), "sha256": sha256(b), "fetched_now": fetched,
             "http_status": 200 if fetched else None}
        try:
            e["check"] = validate(path, b)
            e["ok"] = True
        except Exception as ex:
            e["check"], e["ok"] = f"INVALID: {ex}", False
            self.errors.append(f"{e['local_path']}: {ex}")
        e["license"] = header_license(b) or license_default
        return e

    def gh_many(self, repo, sha, paths, local_root, license_default):
        out = []
        with cf.ThreadPoolExecutor(self.jobs) as ex:
            futs = [ex.submit(self.gh_one, repo, sha, p, local_root, license_default) for p in paths]
            for f in cf.as_completed(futs):
                r = f.result()
                if r:
                    out.append(r)
        out.sort(key=lambda e: e["local_path"])
        self.entries.extend(out)
        return out

    # -- Ubuntu archive -------------------------------------------------------------------------
    def ubuntu(self) -> dict:
        arch = self.dest / "archives"
        arch.mkdir(parents=True, exist_ok=True)
        info = {}
        inrel_url = f"{UBUNTU}/dists/{UBUNTU_SUITE}/InRelease"
        inrel = http_get(inrel_url)
        (arch / f"ubuntu-{UBUNTU_SUITE}-InRelease").write_bytes(inrel)
        gv = subprocess.run(["gpgv", "--keyring", UBUNTU_KEYRING, str(arch / f"ubuntu-{UBUNTU_SUITE}-InRelease")],
                            capture_output=True, text=True)
        info["inrelease"] = {"url": inrel_url, "sha256": sha256(inrel), "gpgv_ok": gv.returncode == 0,
                             "gpgv_output": (gv.stderr + gv.stdout).strip().splitlines()[-3:]}
        if gv.returncode != 0:
            raise RuntimeError("InRelease signature check failed:\n" + gv.stderr)
        rel_sums = {}
        sect = None
        for line in inrel.decode().splitlines():
            if re.match(r"^[A-Za-z0-9-]+:", line):
                sect = line.split(":")[0]
                continue
            if sect == "SHA256" and line.startswith(" "):
                h, size, name = line.split()
                rel_sums[name] = (h, int(size))

        def indexed(name):
            url = f"{UBUNTU}/dists/{UBUNTU_SUITE}/{name}"
            b = http_get(url)
            h, size = rel_sums[name]
            if sha256(b) != h or len(b) != size:
                raise RuntimeError(f"{name}: sha256 mismatch with signed InRelease")
            return url, b

        pk_url, pk = indexed("universe/binary-amd64/Packages.xz")
        src_url, src = indexed("universe/source/Sources.xz")
        info["packages_index"] = {"url": pk_url, "sha256": sha256(pk), "matches_inrelease": True}
        info["sources_index"] = {"url": src_url, "sha256": sha256(src), "matches_inrelease": True}

        stanza = None
        for s in lzma.decompress(pk).decode().split("\n\n"):
            if re.search(rf"^Package: {re.escape(DEB_PKG)}$", s, re.M) and re.search(rf"^Version: {re.escape(DEB_VER)}$", s, re.M):
                stanza = s
        if not stanza:
            raise RuntimeError("makehuman-data not in Packages index")
        (arch / "makehuman-data.Packages-stanza.txt").write_text(stanza + "\n")
        field = lambda k: re.search(rf"^{k}: (.+)$", stanza, re.M).group(1).strip()
        deb_url = f"{UBUNTU}/{field('Filename')}"
        deb_path = arch / os.path.basename(field("Filename"))
        if deb_path.exists() and not self.refresh and sha256_file(deb_path) == field("SHA256"):
            fetched = False
        else:
            b = http_get(deb_url)
            deb_path.write_bytes(b)
            del b
            fetched = True
        got = sha256_file(deb_path)
        if got != field("SHA256") or deb_path.stat().st_size != int(field("Size")):
            raise RuntimeError("deb sha256/size mismatch with Packages index")
        info["deb"] = {"url": deb_url, "local_path": str(deb_path.relative_to(self.dest)), "bytes": deb_path.stat().st_size,
                       "sha256": got, "sha256_expected_from_packages_index": field("SHA256"), "fetched_now": fetched}

        # source stanza: the original upstream tarball carries the 1.1.1 license.txt
        sst = None
        for s in lzma.decompress(src).decode().split("\n\n"):
            if re.search(r"^Package: makehuman$", s, re.M) and re.search(rf"^Version: {re.escape(DEB_VER)}$", s, re.M):
                sst = s
        if sst:
            (arch / "makehuman.Sources-stanza.txt").write_text(sst + "\n")
            directory = re.search(r"^Directory: (.+)$", sst, re.M).group(1).strip()
            m = re.search(r"^Checksums-Sha256:\n((?: .+\n?)+)", sst, re.M)
            sums = {l.split()[2]: (l.split()[0], int(l.split()[1])) for l in m.group(1).strip("\n").splitlines()}
            orig = [n for n in sums if n.endswith(".orig.tar.bz2")][0]
            lic_local = self.dest / "ubuntu" / "makehuman-1.1.1-orig" / "makehuman" / "license.txt"
            lic_fetched = False
            if not lic_local.exists() or self.refresh:
                lic_fetched = True
                ob = http_get(f"{UBUNTU}/{directory}/{orig}")
                if sha256(ob) != sums[orig][0]:
                    raise RuntimeError("orig tarball sha256 mismatch with Sources index")
                with tarfile.open(fileobj=io.BytesIO(ob), mode="r:bz2") as tf:
                    lb = tf.extractfile("makehuman-1.1.1/makehuman/license.txt").read()
                lic_local.parent.mkdir(parents=True, exist_ok=True)
                lic_local.write_bytes(lb)
                del ob
            lb = lic_local.read_bytes()
            self.entries.append({
                "local_path": str(lic_local.relative_to(self.dest)), "source": "ubuntu:makehuman_1.1.1.orig.tar.bz2",
                "url": f"{UBUNTU}/{directory}/{orig}#makehuman-1.1.1/makehuman/license.txt",
                "bytes": len(lb), "sha256": sha256(lb), "ok": True, "fetched_now": lic_fetched,
                "check": f"extracted from orig tarball, sha256 {sums[orig][0]} verified against signed Sources index",
                "license": "license text (1.1.1: AGPL + CC0 option for exports)"})

        # extract the .deb (ar archive -> data.tar.xz), verify each member against md5sums
        members = self._read_ar(deb_path)
        with tarfile.open(fileobj=io.BytesIO(members["control.tar.gz"]), mode="r:gz") as tf:
            md5s = {}
            for line in tf.extractfile("./md5sums").read().decode().splitlines():
                h, p = line.split(None, 1)
                md5s[p.strip()] = h
        data_name = [k for k in members if k.startswith("data.tar")][0]
        root = self.dest / "ubuntu" / f"{DEB_PKG}_{DEB_VER}"
        n_ok = 0
        with tarfile.open(fileobj=io.BytesIO(members[data_name]), mode="r:*") as tf:
            for ti in tf:
                if not ti.isfile():
                    continue
                name = ti.name[2:] if ti.name.startswith("./") else ti.name
                keep = False
                if name.startswith(DEB_ROOT):
                    rel = name[len(DEB_ROOT):]
                    top = rel.split("/")[0]
                    keep = "/" in rel and top not in DEB_SKIP_DIRS or rel == "targets.npz"
                elif name.startswith("usr/share/makehuman/licenses/") or name.startswith("usr/share/doc/makehuman-data/"):
                    keep = True
                if not keep:
                    continue
                b = tf.extractfile(ti).read()
                local = root / name
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(b)
                md5_ok = hashlib.md5(b).hexdigest() == md5s.get(name)
                e = {"local_path": str(local.relative_to(self.dest)), "source": f"ubuntu:{deb_path.name}",
                     "url": f"{deb_url}#{name}", "bytes": len(b), "sha256": sha256(b), "md5_matches_deb_md5sums": md5_ok,
                     "fetched_now": fetched}
                try:
                    e["check"] = validate(name, b)
                    e["ok"] = md5_ok
                except Exception as ex:
                    e["check"], e["ok"] = f"INVALID: {ex}", False
                if not e["ok"]:
                    self.errors.append(f"{e['local_path']}: {e['check']} md5_ok={md5_ok}")
                hl = header_license(b)
                e["license"] = ("CC0-1.0 (MakeHuman bundled asset, re-released CC0 Sept 2020 per makehuman LICENSE.md §C)"
                                + (f"; header says {hl}" if hl else ""))
                if "/licenses/" in name or "/doc/" in name:
                    e["license"] = "license/doc file"
                self.entries.append(e)
                n_ok += md5_ok
        info["deb_extracted_files"] = n_ok
        info["extract_root"] = str(root.relative_to(self.dest))
        return info

    @staticmethod
    def _read_ar(path: Path) -> dict:
        out = {}
        with open(path, "rb") as f:
            if f.read(8) != b"!<arch>\n":
                raise RuntimeError("not an ar archive")
            while True:
                hdr = f.read(60)
                if len(hdr) < 60:
                    break
                name = hdr[:16].decode().strip().rstrip("/")
                size = int(hdr[48:58].decode().strip())
                out[name] = f.read(size)
                if size % 2:
                    f.read(1)
        return out


def target_names_from_modifiers(dest: Path) -> set[str]:
    names = set()
    mod = dest / "gh/makehuman/makehuman/data/modifiers"
    for fn in ("modeling_modifiers.json", "measurement_modifiers.json", "bodyshapes_modifiers.json"):
        for grp in json.loads((mod / fn).read_text()):
            g = grp["group"]
            if g.startswith("macrodetails"):
                continue
            for m in grp["modifiers"]:
                t = m.get("target")
                if not t:
                    continue
                if "min" in m and "max" in m:
                    for side in [m["min"], m.get("mid"), m["max"]]:
                        if side:
                            names.add(f"targets/{g}/{t}-{side}")
                else:
                    names.add(f"targets/{g}/{t}")
    return names


def cross_check(dest: Path, entries: list[dict]) -> dict:
    """Compare GitHub text assets with the independently packaged 1.1.1 compiled copies."""
    res = {}
    deb = dest / "ubuntu" / f"{DEB_PKG}_{DEB_VER}" / DEB_ROOT
    gh = dest / "gh/makehuman/makehuman/data"
    # base mesh
    coords = []
    for line in (gh / "3dobjs/base.obj").read_text().splitlines():
        if line.startswith("v "):
            coords.append([float(x) for x in line.split()[1:4]])
    coords = np.asarray(coords)
    bn = np.load(deb / "3dobjs/base.npz")
    res["base_obj_vs_1.1.1_base_npz"] = {"n_obj": len(coords), "n_npz": int(len(bn["coord"])),
                                         "max_abs_diff": float(np.abs(coords - bn["coord"]).max()) if len(coords) == len(bn["coord"]) else None}
    # targets: text (master) vs compiled int16*1000 (1.1.1), compared as dense (19158,3) deltas.
    # hm08 vertices 0..13379 are the skin surface, 13380.. are helper geometry (tights, skirt, hair, joints).
    tn = np.load(deb / "targets.npz")
    identical = sparse_only = 0
    helper_only, body_changed = [], []
    for e in entries:
        lp = e["local_path"]
        if not lp.endswith(".target") or not lp.startswith("gh/makehuman/"):
            continue
        key = lp.split("makehuman/data/")[1][:-len(".target")]
        if key + ".index" not in tn.files:
            continue
        i, v = parse_target((dest / lp).read_bytes())
        ci, cv = tn[key + ".index"].astype(np.int64), tn[key + ".vector"].astype(np.float64) / 1000.0
        if len(i) == len(ci) and np.array_equal(i, ci) and (len(v) == 0 or np.abs(v - cv).max() < 1.5e-3):
            identical += 1
            continue
        A = np.zeros((19158, 3)); A[i] = v
        B = np.zeros((19158, 3)); B[ci] = cv
        changed = np.nonzero(np.abs(A - B).max(1) > 1.5e-3)[0]
        if len(changed) == 0:
            sparse_only += 1          # same deltas, only the set of listed ~zero rows differs
        elif (changed < 13380).any():
            body_changed.append(f"{key}: {int((changed < 13380).sum())} skin verts, {int((changed >= 13380).sum())} helper verts")
        else:
            helper_only.append(key)
    res["targets_master_vs_1.1.1_compiled"] = {
        "note": "master (2024) .target text vs the targets.npz compiled into the 1.1.1 (2017) package",
        "identical": identical, "same_deltas_different_sparsity": sparse_only,
        "changed_helper_geometry_only": len(helper_only),
        "changed_on_skin_surface": len(body_changed), "changed_on_skin_surface_list": body_changed,
        "changed_helper_geometry_only_examples": helper_only[:10]}
    # every mhclo in the deb: reference rows == compiled mesh vertex count
    bad, good = [], 0
    for mh in sorted(list(deb.rglob("*.mhclo")) + list(deb.rglob("*.proxy"))):
        if mh.parent.name == "3dobjs":
            continue  # base.mhclo / a7_converter.proxy map the old alpha7 mesh onto hm08, not wearables
        m = parse_mhclo(mh.read_text(errors="replace"))
        if not m["obj_file"]:
            continue
        npz = mh.parent / (os.path.splitext(m["obj_file"])[0] + ".npz")
        if not npz.exists():
            bad.append(f"{mh.relative_to(deb)}: missing {npz.name}")
            continue
        nv = len(np.load(npz)["coord"])
        if nv == m["n_ref"]:
            good += 1
        else:
            bad.append(f"{mh.relative_to(deb)}: ref_rows={m['n_ref']} mesh_v={nv}")
    res["deb_mhclo_vs_npz"] = {"consistent": good, "problems": bad}
    return res


RECOMMENDED = {
    "base_mesh": "gh/makehuman/makehuman/data/3dobjs/base.obj",
    "skeleton_default_163": "gh/makehuman/makehuman/data/rigs/default.mhskel",
    "skin_weights_default": "gh/makehuman/makehuman/data/rigs/default_weights.mhw",
    "rig_game_engine_json": "gh/mpfb2/src/mpfb/data/rigs/standard/rig.game_engine.json",
    "weights_game_engine_json": "gh/mpfb2/src/mpfb/data/rigs/standard/weights.game_engine.json",
    "rig_mixamo_json": "gh/mpfb2/src/mpfb/data/rigs/standard/rig.mixamo.json",
    "weights_mixamo_json": "gh/mpfb2/src/mpfb/data/rigs/standard/weights.mixamo.json",
    "target_macro_universal": "gh/makehuman/makehuman/data/targets/macrodetails/universal-male-young-averagemuscle-averageweight.target",
    "target_macro_universal_slim": "gh/makehuman/makehuman/data/targets/macrodetails/universal-male-young-averagemuscle-minweight.target",
    "target_race_asian": "gh/makehuman/makehuman/data/targets/macrodetails/asian-male-young.target",
    "target_height_max": "gh/makehuman/makehuman/data/targets/macrodetails/height/male-young-averagemuscle-averageweight-maxheight.target",
    "target_proportions_ideal": "gh/makehuman/makehuman/data/targets/macrodetails/proportions/male-young-averagemuscle-averageweight-idealproportions.target",
    "eyes_mesh": "gh/makehuman/makehuman/data/eyes/high-poly/high-poly.obj",
    "eyes_mhclo": "gh/makehuman/makehuman/data/eyes/high-poly/high-poly.mhclo",
    "eyes_texture_brown": "gh/makehuman/makehuman/data/eyes/materials/brown_eye.png",
    "skin_material_young_asian_male": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}skins/young_asian_male/young_asian_male.mhmat",
    "skin_texture_young_male": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}skins/textures/young_lightskinned_male_diffuse3.png",
    "eyebrows": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}eyebrows/eyebrow001/eyebrow001.mhclo",
    "eyelashes": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}eyelashes/eyelashes01/eyelashes01.mhclo",
    "teeth": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}teeth/teeth_base/teeth_base.mhclo",
    "tongue": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}tongue/tongue01/tongue01.mhclo",
    "top_and_trousers_long_sleeve_shirt_jeans": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}clothes/male_casualsuit01/male_casualsuit01.mhclo",
    "shoes_black_leather": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}clothes/shoes03/shoes03.mhclo",
    "hair_short_messy": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}hair/short02/short02.mhclo",
    "pose_standing": f"ubuntu/{DEB_PKG}_{DEB_VER}/{DEB_ROOT}poses/standing01.bvh",
}


def _jsonable(o):
    return o.item() if hasattr(o, "item") else str(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--jobs", type=int, default=12)
    a = ap.parse_args()
    dest = a.dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    F = Fetcher(dest, a.refresh, a.jobs)
    t0 = time.time()

    print("[1/4] Ubuntu archive: makehuman-data 1.1.1 (system assets)")
    ub = F.ubuntu()
    print(f"      deb ok, {ub['deb_extracted_files']} files extracted + md5-verified")

    print("[2/4] GitHub raw: makehuman @", MH_SHA[:7])
    lic_mh = "CC0-1.0 (makehuman LICENSE.md §C: bundled assets are CC0)"
    F.gh_many(MH_REPO, MH_SHA, MH_FILES, "gh/makehuman", lic_mh)
    tnpz = np.load(dest / "ubuntu" / f"{DEB_PKG}_{DEB_VER}" / DEB_ROOT / "targets.npz")
    names = {k[:-len(".index")] for k in tnpz.files if k.endswith(".index")}
    json_names = target_names_from_modifiers(dest)
    all_names = sorted(names | json_names)
    print(f"      targets: {len(names)} from 1.1.1 targets.npz, {len(json_names)} from modifier JSON, union {len(all_names)}")
    F.gh_many(MH_REPO, MH_SHA, [f"makehuman/data/{n}.target" for n in all_names], "gh/makehuman", lic_mh)

    print("[3/4] GitHub raw: mpfb2 @", MPFB_SHA[:7])
    F.gh_many(MPFB_REPO, MPFB_SHA, MPFB_FILES, "gh/mpfb2", "CC0-1.0 (mpfb2 LICENSE.md §C: rigs, targets, JSON mesh data are CC0)")

    print("[4/4] cross-checks")
    xc = cross_check(dest, F.entries)
    print(json.dumps(xc, indent=1, default=_jsonable)[:2000])

    for k, v in RECOMMENDED.items():
        if not (dest / v).exists():
            F.errors.append(f"recommended {k} missing: {v}")

    by_source = {}
    for e in F.entries:
        s = by_source.setdefault(e["source"], {"files": 0, "bytes": 0, "ok": 0})
        s["files"] += 1
        s["bytes"] += e["bytes"]
        s["ok"] += bool(e.get("ok"))
    manifest = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "generator": "odyssey/body/fetch_makehuman.py",
        "dest": str(dest),
        "sources": {
            "makehuman": {"repo": MH_REPO, "commit": MH_SHA, "via": "raw.githubusercontent.com"},
            "mpfb2": {"repo": MPFB_REPO, "commit": MPFB_SHA, "via": "raw.githubusercontent.com"},
            "ubuntu": ub,
        },
        "license_summary": (
            "All assets CC0-1.0. GitHub makehuman/mpfb2 asset files: CC0 by file header and by each repo's LICENSE.md "
            "section C (code is AGPL/GPL but no code is used). Ubuntu makehuman-data 1.1.1 files: 2016 headers say AGPLv3 "
            "(1.1.1 license.txt: AGPL with CC0 option for exports); the copyright holders (Data Collection AB, Joel Palmius, "
            "Jonas Hauquier) re-released every MakeHuman bundled asset -- base mesh and proxies, targets, textures, any "
            "MHCLO-based clothes/hair/eyebrows, poses -- under CC0 1.0 in September 2020 (makehuman LICENSE.md §C, "
            "gh/makehuman/LICENSE.md). Brand marks in some textures (e.g. a Nike swoosh on shoes06, a MakeHuman logo on "
            "the casualsuit t-shirts) are trademarks, not waived by CC0: avoid or paint out."),
        "summary": {"files": len(F.entries), "ok": sum(bool(e.get("ok")) for e in F.entries),
                    "errors": F.errors, "not_found_404": F.missing, "by_source": by_source,
                    "seconds": round(time.time() - t0, 1)},
        "cross_checks": xc,
        "recommended": RECOMMENDED,
        "files": sorted(F.entries, key=lambda e: e["local_path"]),
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1, default=_jsonable))
    print(f"manifest: {dest/'manifest.json'}  files={len(F.entries)} ok={manifest['summary']['ok']} "
          f"errors={len(F.errors)} 404={len(F.missing)}")
    return 0 if not F.errors else 1


if __name__ == "__main__":
    sys.exit(main())
