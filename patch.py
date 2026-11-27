"""Aplica as falas PT-BR nos scripts Ink do Am I Nima.

Uso: python patch.py <data.unity3d original> <saida.unity3d> [pasta]
  pasta: "traducao" (demo, padrão) ou "completo" (jogo completo)
Requer: pip install UnityPy (jogo completo: também numpy TypeTreeGeneratorAPI fonttools)
"""
import glob, json, os, re, sys
import UnityPy

INK_ASSETS = ("AmINimaAlvin", "Obsession")  # ordem define os IDs de falas/*.txt (o jogo completo só tem o 1º)
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


def is_choice(x, i, j):
    """Texto logo após "ev" cuja avaliação termina num ponto de escolha {"*": ...} (outras condições além de brainspace)."""
    if i < 2 or x[i - 2] != "ev" or "/ev" not in x[j:]: return False
    k = x.index("/ev", j)
    return k + 1 < len(x) and isinstance(x[k + 1], dict) and "*" in x[k + 1]


def choices(x, fn):
    """Aplica fn no texto das escolhas (os pensamentos arrastáveis): o 1º str de uma escolha, antes do teste de brainspace."""
    if isinstance(x, list):
        x = list(x)
        for i, e in enumerate(x):
            if isinstance(e, str) and e.startswith("^") and i and x[i - 1] == "str":
                j = i + 1
                while j < len(x) and x[j] == "#":  # pode ter várias tags (#id:..., #next)
                    j = x.index("/#", j) + 1
                if x[j:j + 1] == ["/str"] and (x[j + 1:j + 2] in ([{"VAR?": "brainspace"}], ["choiceCnt"]) or is_choice(x, i, j)):
                    x[i] = "^" + fn(e[1:])
            elif isinstance(e, (list, dict)): x[i] = choices(e, fn)
        return x
    if isinstance(x, dict):
        return {k: (choices(v, fn) if isinstance(v, (list, dict)) else v) for k, v in x.items()}
    return x


def load_pt(pasta, *sub):
    d = {}
    for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), pasta, *sub))):
        for line in open(f, encoding="utf-8").read().split("\n"):
            if line:
                i, t = line.split("|", 1)
                d[int(i)] = t
    return d


def main(src, out, pasta="traducao"):
    pt, ptc = load_pt(pasta, "falas", "*.txt"), load_pt(pasta, "escolhas.txt")
    env = UnityPy.load(src)
    assets = {}
    for o in env.objects:
        if o.type.name == "TextAsset":
            d = o.read()
            if d.m_Name in INK_ASSETS: assets[d.m_Name] = d
    names = [n for n in INK_ASSETS if n in assets]
    assert names, "nenhum script Ink encontrado (arquivo errado?)"

    trees, en, enc = {}, [], []
    for name in names:
        raw = assets[name].m_Script
        if isinstance(raw, bytes): raw = raw.decode("utf-8")
        trees[name] = json.loads(raw.lstrip("﻿"))
        walk(trees[name]["root"], lambda s: (en.append(s) if s not in en else None) or s)
        choices(trees[name]["root"], lambda s: (enc.append(s) if s not in enc else None) or s)

    # Confere se a tradução bate com esta versão do jogo antes de escrever qualquer coisa.
    assert len(en) == len(pt), f"jogo tem {len(en)} falas, tradução tem {len(pt)} (versão diferente do jogo?)"
    for i, s in enumerate(en):
        assert TAG.findall(s) == TAG.findall(pt[i]), f"tags diferentes na fala {i}: {s!r}"
    assert len(enc) == len(ptc), f"jogo tem {len(enc)} escolhas, tradução tem {len(ptc)}"
    m = {s: pt[i] for i, s in enumerate(en)}
    mc = {s: ptc[i] for i, s in enumerate(enc)}

    for name in names:
        trees[name]["root"] = choices(walk(trees[name]["root"], m.__getitem__), mc.__getitem__)
        assets[name].m_Script = "﻿" + json.dumps(trees[name], ensure_ascii=False, separators=(",", ":"))
        assets[name].save()
    if pasta == "completo":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import fonte
        n = fonte.aplicar(env, os.path.join(os.path.dirname(os.path.abspath(src)), "Managed"))
        print(f"fonte: {n} letras desenhadas")
        fonte.aplicar_nima(env)  # cópia no data.unity3d (antes da troca de fonte por idioma)
        print(f"fonte Nima (pacote de fontes): {fonte.aplicar_addressables(os.path.dirname(os.path.abspath(src)))} letras desenhadas")
    open(out, "wb").write(env.file.save(packer="lz4"))
    print(f"ok: {len(en)} falas e {len(enc)} escolhas traduzidas -> {out}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4): sys.exit(__doc__)
    main(*sys.argv[1:])
