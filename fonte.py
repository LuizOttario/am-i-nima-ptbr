"""Desenha letras acentuadas (ã, é, ç, …) na fonte pixelada NotJamScrawl9 do jogo completo.

A fonte do pensamento interno é um atlas SDF estático sem acentos; sem isto o jogo pega
essas letras de outra fonte e elas ficam com cara diferente. Aqui cada letra é lida como
grade de "pixels" da fonte, o acento é desenhado na mesma grade e o SDF é gerado com a
mesma escala das letras originais. O atlas cresce de 512x512 para 512x1024 (as letras
originais não mudam de lugar).
"""
import numpy as np
from PIL import Image

FONTE = "NotJamScrawl9 SDF"
U = 45.14 / 7  # tamanho de um "pixel" da fonte no atlas (o "i" tem 7 de altura)

# acentos em células (coluna, linha), linha 0 = mais baixa
ACENTO = {
    "agudo": [(0, 0), (1, 1)],
    "grave": [(1, 0), (0, 1)],
    "circ": [(0, 0), (1, 1), (2, 0)],
    "til": [(0, 0), (1, 1), (2, 0), (3, 1)],
}
import unicodedata
NOVAS = {}
for base, acentos in {"a": "agudo grave circ til", "e": "agudo circ", "i": "agudo", "o": "agudo circ til", "u": "agudo"}.items():
    for nome in acentos.split():
        for b in (base, base.upper()):
            ch = {"agudo": "́", "grave": "̀", "circ": "̂", "til": "̃"}[nome]
            NOVAS[unicodedata.normalize("NFC", b + ch)] = (b, nome)
NOVAS["ç"] = ("c", "cedilha")
NOVAS["Ç"] = ("C", "cedilha")


def grade(alpha, rect, pad):
    """Lê a letra do atlas (alpha com y para cima) como matriz booleana de células [linha][coluna], linha 0 = base."""
    x, y, w, h = rect
    cols, rows = round(w / U), round(h / U)
    g = np.zeros((rows, cols), bool)
    for r in range(rows):
        for c in range(cols):
            g[r, c] = alpha[int(y + (r + 0.5) * U), int(x + (c + 0.5) * U)] >= 128
    return g


def compor(g, base, nome):
    """Devolve (grade nova, quantas linhas ficaram abaixo da linha de base)."""
    rows, cols = g.shape
    if nome == "cedilha":
        meio = cols // 2
        nova = np.zeros((rows + 2, cols), bool)
        nova[2:] = g
        nova[1, meio] = True
        nova[0, meio - 1] = True
        return nova, 2
    if base == "i":  # tira o pingo do i antes de pôr o acento
        g = g[:5].copy()
        rows = 5
    forma = ACENTO[nome]
    aw = max(c for c, _ in forma) + 1
    ah = max(r for _, r in forma) + 1
    nova = np.zeros((rows + 1 + ah, cols), bool)
    nova[:rows] = g
    off = (cols - aw + 1) // 2
    for c, r in forma:
        nova[rows + 1 + r, off + c] = True
    return nova, 0


def mascara(gr, pad):
    """Grade de células -> máscara em pixels do atlas (y para cima), com margem pad."""
    rows, cols = gr.shape
    w, h = int(np.ceil(cols * U)), int(np.ceil(rows * U))
    ys, xs = np.mgrid[0:h + 2 * pad, 0:w + 2 * pad]
    c = np.floor((xs - pad + 0.5) / U).astype(int)
    r = np.floor((ys - pad + 0.5) / U).astype(int)
    ok = (c >= 0) & (c < cols) & (r >= 0) & (r < rows)
    m = np.zeros(xs.shape, bool)
    m[ok] = gr[r[ok], c[ok]]
    return m, w, h


def dist(m):
    """Distância com sinal (px) até a borda, positiva dentro."""
    pts_in = np.argwhere(m)
    pts_out = np.argwhere(~m)
    idx = np.indices(m.shape).reshape(2, -1).T
    def mind(src, dst):
        out = np.full(len(src), 1e9)
        for k in range(0, len(dst), 512):
            d = ((src[:, None, :] - dst[None, k:k + 512, :]) ** 2).sum(-1)
            out = np.minimum(out, d.min(1))
        return np.sqrt(out)
    flat = m.reshape(-1)
    sd = np.zeros(len(idx))
    sd[flat] = mind(idx[flat], pts_out) - 0.5
    sd[~flat] = -(mind(idx[~flat], pts_in) - 0.5)
    return sd.reshape(m.shape)


def calibrar(alpha, rect, pad):
    """Acha alpha = a*dist + b usando uma letra original (o 'a')."""
    x, y, w, h = rect
    g = grade(alpha, rect, pad)
    m, _, _ = mascara(g, pad)
    reg = alpha[y - pad:y - pad + m.shape[0], x - pad:x - pad + m.shape[1]].astype(float)
    sd = dist(m)[:reg.shape[0], :reg.shape[1]]
    sel = (reg > 5) & (reg < 250)
    a, b = np.polyfit(sd[sel], reg[sel], 1)
    return a, b


def gerar(d, alpha):
    """d = typetree do TMP_FontAsset; alpha = atlas (H, W) uint8 com y para cima. Devolve (d, alpha novo)."""
    pad = d["m_AtlasPadding"]
    gi = {g["m_Index"]: g for g in d["m_GlyphTable"]}
    ch = {c["m_Unicode"]: c["m_GlyphIndex"] for c in d["m_CharacterTable"]}
    rect = lambda g: (g["m_GlyphRect"]["m_X"], g["m_GlyphRect"]["m_Y"], g["m_GlyphRect"]["m_Width"], g["m_GlyphRect"]["m_Height"])
    a, b = calibrar(alpha, rect(gi[ch[ord("a")]]), pad)
    H, W = alpha.shape
    novo = np.zeros((H * 2, W), np.uint8)
    novo[:H] = alpha
    cx, cy, linha = pad, H + pad, 0
    prox = max(gi) + 1
    extra = {}
    for c, (base, nome) in NOVAS.items():
        if ord(c) in ch: continue
        gb = gi[ch[ord(base)]]
        gr, abaixo = compor(grade(alpha, rect(gb), pad), base, nome)
        extra[c] = (gr, abaixo, gb["m_Metrics"], None)
    # pontuação tipográfica a partir de glifos que já existem
    def copia(src, larg=None):
        g = gi[ch[ord(src)]]
        gr = grade(alpha, rect(g), pad)
        if larg: gr = np.repeat(gr[:, :1], larg, axis=1)
        return gr
    ponto = copia(".")
    ret = np.zeros((ponto.shape[0], ponto.shape[1] * 3 + 2), bool)
    for k in range(3): ret[:, k * (ponto.shape[1] + 1):k * (ponto.shape[1] + 1) + ponto.shape[1]] = ponto
    m_ponto = gi[ch[ord(".")]]["m_Metrics"]
    pont = {"…": (ret, ".", None), "‘": (copia("'"), "'", None), "’": (copia("'"), "'", None),
            "“": (copia('"'), '"', None), "”": (copia('"'), '"', None),
            "–": (copia("-"), "-", None), "—": (copia("-", round(gi[ch[ord("-")]]["m_GlyphRect"]["m_Width"] / U) + 2), "-", None)}
    for c, (gr, src, _) in pont.items():
        if ord(c) in ch: continue
        ms = gi[ch[ord(src)]]["m_Metrics"]
        extra[c] = (gr, 0, ms, ms["m_HorizontalBearingY"])  # mesma altura do glifo de origem
    for c, (gr, abaixo, mb, topo_fixo) in extra.items():
        m, w, h = mascara(gr, pad)
        sdf = np.clip(a * dist(m) + b, 0, 255).astype(np.uint8)
        if cx + m.shape[1] > W:
            cx, cy, linha = pad, cy + linha, 0
        assert cy + m.shape[0] <= 2 * H, "atlas cheio"
        novo[cy - pad:cy - pad + m.shape[0], cx - pad:cx - pad + m.shape[1]] = np.maximum(
            novo[cy - pad:cy - pad + m.shape[0], cx - pad:cx - pad + m.shape[1]], sdf)
        topo = topo_fixo if topo_fixo is not None else (gr.shape[0] - abaixo) * U
        d["m_GlyphTable"].append({
            "m_Index": prox,
            "m_Metrics": {"m_Width": gr.shape[1] * U, "m_Height": gr.shape[0] * U,
                          "m_HorizontalBearingX": mb["m_HorizontalBearingX"], "m_HorizontalBearingY": topo,
                          "m_HorizontalAdvance": max(mb["m_HorizontalAdvance"], gr.shape[1] * U + U)},
            "m_GlyphRect": {"m_X": cx, "m_Y": cy, "m_Width": w, "m_Height": h},
            "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0})
        d["m_CharacterTable"].append({"m_ElementType": 1, "m_Unicode": ord(c), "m_GlyphIndex": prox, "m_Scale": 1.0})
        prox += 1
        cx += m.shape[1] + pad
        linha = max(linha, m.shape[0] + pad)
    d["m_AtlasHeight"] = H * 2
    return d, novo, len(extra)


def previa(d, alpha, texto, caminho):
    """Desenha um texto com o atlas (só para conferir)."""
    gi = {g["m_Index"]: g for g in d["m_GlyphTable"]}
    ch = {c["m_Unicode"]: c["m_GlyphIndex"] for c in d["m_CharacterTable"]}
    img = np.zeros((90, 60 * len(texto)), np.uint8)
    x = 5
    for c in texto:
        if ord(c) not in ch: x += 30; continue
        g = gi[ch[ord(c)]]; r = g["m_GlyphRect"]; m = g["m_Metrics"]
        reg = alpha[r["m_Y"]:r["m_Y"] + r["m_Height"], r["m_X"]:r["m_X"] + r["m_Width"]]
        reg = (reg >= 128).astype(np.uint8)[::-1] * 255
        top = int(70 - m["m_HorizontalBearingY"])
        hh, ww = reg.shape
        img[max(top, 0):top + hh, x:x + ww] = np.maximum(img[max(top, 0):top + hh, x:x + ww], reg[max(-top, 0):])
        x += int(m["m_HorizontalAdvance"])
    Image.fromarray(img[:, :x + 5]).save(caminho)


def aplicar(env, managed):
    """Aplica na fonte dentro do bundle carregado pelo UnityPy. managed = pasta Managed do jogo."""
    from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
    alvo = None
    for o in env.objects:
        if o.type.name != "MonoBehaviour": continue
        try:
            mb = o.read(check_read=False)
            if mb.m_Name == FONTE and mb.m_Script.read().m_ClassName == "TMP_FontAsset": alvo = o
        except Exception: pass
    if alvo is None:
        return 0  # demo ou outra versão: sem essa fonte
    g = TypeTreeGenerator("2022.3.4f1"); g.load_local_dll_folder(managed)
    nodes = g.get_nodes_up("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
    d = alvo.read_typetree(nodes, wrap=False, check_read=False)
    if any(c["m_Unicode"] == ord("ã") for c in d["m_CharacterTable"]): return 0
    t = d["m_AtlasTextures"][0]
    tex = alvo.assets_file.files[t["m_PathID"]].read()
    alpha = np.array(tex.image.getchannel("A"))[::-1].copy()  # imagem vem de cima pra baixo
    d, novo, n = gerar(d, alpha)
    img = Image.new("RGBA", (novo.shape[1], novo.shape[0]), (255, 255, 255, 0))
    img.putalpha(Image.fromarray(novo[::-1]))
    tex.set_image(img)
    tex.save()
    alvo.save_typetree(d, nodes)
    # o material guarda o tamanho do atlas
    m = d["material"]
    mat = alvo.assets_file.files[m["m_PathID"]].read()
    for par in mat.m_SavedProperties.m_Floats:
        if par[0] == "_TextureHeight": mat.m_SavedProperties.m_Floats[mat.m_SavedProperties.m_Floats.index(par)] = (par[0], float(novo.shape[0]))
    mat.save()
    return n
