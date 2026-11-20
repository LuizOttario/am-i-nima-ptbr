#!/usr/bin/env bash
# Instala a tradução PT-BR do Am I Nima Demo (Linux / Steam Deck, via Proton).
# Uso: ./install.sh ["/caminho/para/Am I Nima Demo"]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STEAM="${STEAM_DIR:-$HOME/.local/share/Steam}"
GAME="${1:-$STEAM/steamapps/common/Am I Nima Demo}"
DATA="$GAME/Am I Nima_Data"
PREFIX="$STEAM/steamapps/compatdata/3317110/pfx/user.reg"
BEPINEX=https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.6/BepInEx_win_x64_5.4.23.6.zip
XUNITY=https://github.com/bbepis/XUnity.AutoTranslator/releases/download/v5.6.3.1/XUnity.AutoTranslator-BepInEx-5.6.3.1.zip

[ -f "$DATA/data.unity3d" ] || { echo "Jogo não encontrado em: $GAME"; exit 1; }
command -v uv >/dev/null || { echo "Precisa do uv: https://docs.astral.sh/uv/"; exit 1; }

echo "== Falas (data.unity3d)"
[ -f "$DATA/data.unity3d.orig" ] || cp "$DATA/data.unity3d" "$DATA/data.unity3d.orig"
uv run -q --with UnityPy python "$HERE/patch.py" "$DATA/data.unity3d.orig" "$DATA/data.unity3d.tmp"
mv "$DATA/data.unity3d.tmp" "$DATA/data.unity3d"

echo "== BepInEx + XUnity.AutoTranslator"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/bep.zip" "$BEPINEX"
curl -fsSL -o "$TMP/xu.zip" "$XUNITY"
unzip -oq "$TMP/bep.zip" -d "$GAME"
unzip -oq "$TMP/xu.zip" -d "$GAME"
mkdir -p "$GAME/BepInEx/config" "$GAME/BepInEx/Translation/pt/Text"
cp "$HERE/AutoTranslatorConfig.ini" "$GAME/BepInEx/config/"
cp "$HERE/traducao/AmINima_ptBR.txt" "$HERE/traducao/AmINima_resizer.txt" "$GAME/BepInEx/Translation/pt/Text/"

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
