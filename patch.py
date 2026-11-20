"""Aplica as falas PT-BR nos scripts Ink do Am I Nima.

Uso: python patch.py <data.unity3d original> <saida.unity3d>
Requer: pip install UnityPy
"""
import glob, json, os, re, sys
import UnityPy

INK_ASSETS = ("AmINimaAlvin", "Obsession")  # ordem define os IDs de falas/*.txt
TAG = re.compile(r"\{[^}]*\}|<[^>]*>")


def walk(x, fn):
    """Aplica fn em cada texto narrativo '^...' do Ink (fora de str/tags), que é o que aparece na tela."""
    if isinstance(x, list):
        out, ctx = [], None
        for e in x:
            if e in ("str", "#"): ctx = e
            elif e in ("/str", "/#"): ctx = None
            if isinstance(e, str) and e.startswith("^") and ctx is None and e[1:].strip():
                out.append("^" + fn(e[1:]))
            elif isinstance(e, (list, dict)): out.append(walk(e, fn))
            else: out.append(e)
        return out
    if isinstance(x, dict):
        return {k: (walk(v, fn) if isinstance(v, (list, dict)) else v) for k, v in x.items()}
    return x


def load_pt():
    d = {}
    for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "traducao", "falas", "*.txt"))):
        for line in open(f, encoding="utf-8").read().split("\n"):
            if line:
                i, t = line.split("|", 1)
                d[int(i)] = t
    return d


def main(src, out):
    pt = load_pt()
    env = UnityPy.load(src)
    assets = {}
    for o in env.objects:
        if o.type.name == "TextAsset":
            d = o.read()
            if d.m_Name in INK_ASSETS: assets[d.m_Name] = d
    assert set(assets) == set(INK_ASSETS), f"assets Ink não encontrados: {set(INK_ASSETS) - set(assets)}"

    trees, en = {}, []
    for name in INK_ASSETS:
        raw = assets[name].m_Script
        if isinstance(raw, bytes): raw = raw.decode("utf-8")
        trees[name] = json.loads(raw.lstrip("﻿"))
        walk(trees[name]["root"], lambda s: (en.append(s) if s not in en else None) or s)

    # Confere se a tradução bate com esta versão do jogo antes de escrever qualquer coisa.
    assert len(en) == len(pt), f"jogo tem {len(en)} falas, tradução tem {len(pt)} (versão diferente do jogo?)"
    for i, s in enumerate(en):
        assert TAG.findall(s) == TAG.findall(pt[i]), f"tags diferentes na fala {i}: {s!r}"
    m = {s: pt[i] for i, s in enumerate(en)}

    for name in INK_ASSETS:
        trees[name]["root"] = walk(trees[name]["root"], m.__getitem__)
        assets[name].m_Script = "﻿" + json.dumps(trees[name], ensure_ascii=False, separators=(",", ":"))
        assets[name].save()
    open(out, "wb").write(env.file.save(packer="lz4"))
    print(f"ok: {len(en)} falas traduzidas -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
