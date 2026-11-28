#!/usr/bin/env bash
# Instala a tradução PT-BR do Am I Nima (jogo completo ou demo) no Linux / Steam Deck (Proton).
# Uso: ./install.sh ["/caminho/para/Am I Nima" ou "/caminho/para/Am I Nima Demo"]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STEAM="${STEAM_DIR:-$HOME/.local/share/Steam}"
GAME="${1:-$STEAM/steamapps/common/Am I Nima}"
[ -d "$GAME" ] || GAME="$STEAM/steamapps/common/Am I Nima Demo"
case "$GAME" in *Demo|*Demo/) PASTA=traducao; APPID=3317110;; *) PASTA=completo; APPID=3224600;; esac
DATA="$GAME/Am I Nima_Data"
PREFIX="$STEAM/steamapps/compatdata/$APPID/pfx/user.reg"
BEPINEX=https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.6/BepInEx_win_x64_5.4.23.6.zip
XUNITY=https://github.com/bbepis/XUnity.AutoTranslator/releases/download/v5.6.3.1/XUnity.AutoTranslator-BepInEx-5.6.3.1.zip

[ -f "$DATA/data.unity3d" ] || { echo "Jogo não encontrado em: $GAME"; exit 1; }
command -v uv >/dev/null || { echo "Precisa do uv: https://docs.astral.sh/uv/"; exit 1; }

echo "== Falas (data.unity3d)"
# Arquivo mais novo que a última instalação = a Steam atualizou o jogo; o .orig é da versão velha.
MARCA="$DATA/.ptbr_instalado"
AA="$DATA/StreamingAssets/aa"
for f in "$DATA/data.unity3d" "$AA/catalog.json" "$AA/StandaloneWindows64/localization-assets-english(en)_assets_all.bundle"; do
  if [ -f "$MARCA" ] && [ -f "$f.orig" ] && [ "$f" -nt "$MARCA" ]; then echo "atualizado pela Steam: $(basename "$f")"; rm -f "$f.orig"; fi
done
[ -f "$DATA/data.unity3d.orig" ] || cp "$DATA/data.unity3d" "$DATA/data.unity3d.orig"
uv run -q --with UnityPy --with numpy --with TypeTreeGeneratorAPI --with fonttools python "$HERE/patch.py" "$DATA/data.unity3d.orig" "$DATA/data.unity3d.tmp" "$PASTA"
mv "$DATA/data.unity3d.tmp" "$DATA/data.unity3d"
touch "$MARCA"

echo "== BepInEx + XUnity.AutoTranslator"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/bep.zip" "$BEPINEX"
curl -fsSL -o "$TMP/xu.zip" "$XUNITY"
unzip -oq "$TMP/bep.zip" -d "$GAME"
unzip -oq "$TMP/xu.zip" -d "$GAME"
mkdir -p "$GAME/BepInEx/config" "$GAME/BepInEx/Translation/pt/Text"
cp "$HERE/AutoTranslatorConfig.ini" "$GAME/BepInEx/config/"
cp "$HERE/$PASTA/AmINima_ptBR.txt" "$HERE/$PASTA/AmINima_resizer.txt" "$GAME/BepInEx/Translation/pt/Text/"
# busca da biblioteca em português (só o jogo completo tem essa busca)
[ "$PASTA" = completo ] && mkdir -p "$GAME/BepInEx/plugins" && cp "$HERE/plugin/AmINima.BuscaPtBr.dll" "$GAME/BepInEx/plugins/"
# sem isso o jogo desativa o objeto do BepInEx e o plugin não roda
CFG="$GAME/BepInEx/config/BepInEx.cfg"
if [ -f "$CFG" ]; then sed -i 's/^HideManagerGameObject = false/HideManagerGameObject = true/' "$CFG"
else printf '[Chainloader]\nHideManagerGameObject = true\n' > "$CFG"; fi

echo "== Proton: carregar winhttp.dll do BepInEx"
if [ -f "$PREFIX" ]; then
  if ! grep -q '^"winhttp"="native,builtin"' "$PREFIX"; then
    cp "$PREFIX" "$PREFIX.bak-ptbr"
    python3 - "$PREFIX" <<'EOF'
import sys
p = sys.argv[1]; t = open(p, encoding="utf-8", errors="surrogateescape").read()
h = "[Software\\\\Wine\\\\DllOverrides]"
if h in t:
    j = t.index("\n", t.index(h))
    if t[j + 1:].startswith("#time"): j = t.index("\n", j + 1)
    t = t[:j + 1] + '"winhttp"="native,builtin"\n' + t[j + 1:]
else:
    t += "\n" + h + ' 1795200000\n"winhttp"="native,builtin"\n'
open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
EOF
  fi
  echo "ok (feche o jogo antes de instalar, senão o Proton sobrescreve isso)"
else
  echo "Prefixo do Proton não existe ainda: abra o jogo uma vez e rode de novo,"
  echo "ou use nas opções de inicialização da Steam: WINEDLLOVERRIDES=\"winhttp=n,b\" %command%"
fi
echo "Pronto!"
