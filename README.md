# Am I Nima Demo — Tradução PT-BR

Tradução não oficial, feita por fã, da demo de **Am I Nima** (HO! Games) para português do Brasil.

- **Falas e narração** (~1100 linhas do roteiro Ink): traduzidas direto nos assets do jogo.
- **Palavras, menus e descrições de objetos**: traduzidos na tela via [XUnity.AutoTranslator](https://github.com/bbepis/XUnity.AutoTranslator) (só com dicionário, sem tradutor online). Os nomes internos das palavras continuam em inglês, então as combinações do jogo não quebram.

Este repositório **não contém arquivos do jogo**: o `patch.py` lê o texto original da sua cópia instalada.

## Instalar — Linux / Steam Deck

Precisa de [`uv`](https://docs.astral.sh/uv/). Com o jogo **fechado**:

```bash
git clone https://github.com/LuizOttario/am-i-nima-ptbr
cd am-i-nima-ptbr
./install.sh
```

Se o jogo estiver em outra pasta: `./install.sh "/caminho/Am I Nima Demo"`.

## Instalar — Windows

1. Extraia o [BepInEx 5 x64](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.6) e o [XUnity.AutoTranslator-BepInEx](https://github.com/bbepis/XUnity.AutoTranslator/releases/tag/v5.6.3.1) na pasta do jogo.
2. Copie `AutoTranslatorConfig.ini` para `BepInEx/config/` e `traducao/AmINima_ptBR.txt` + `traducao/AmINima_resizer.txt` para `BepInEx/Translation/pt/Text/`.
3. Faça backup de `Am I Nima_Data/data.unity3d` (ex.: `data.unity3d.orig`) e rode:
   ```
   pip install UnityPy
   python patch.py "Am I Nima_Data/data.unity3d.orig" "Am I Nima_Data/data.unity3d"
   ```

## Desinstalar

Verifique a integridade dos arquivos na Steam e apague a pasta `BepInEx` e o `winhttp.dll` da pasta do jogo.

## Estrutura

- `traducao/falas/*.txt` — falas no formato `ID|texto`. Os IDs seguem a ordem do roteiro do jogo, e as tags (`{voice a=1}`, `<i>` etc.) precisam ficar iguais às do original.
- `traducao/escolhas.txt` — texto dos pensamentos que você arrasta para falar (`ID|texto`).
- `traducao/AmINima_ptBR.txt` — `Original=Tradução` para palavras e interface.
- `traducao/AmINima_resizer.txt` — encolhe a fonte das caixas onde o texto em PT não cabe.
- `patch.py` — confere se a tradução bate com a versão do jogo e aplica.

Achou algo em inglês ou um erro? Abra uma issue.
Am I Nima é © HO! Games. Projeto de fã, sem afiliação.
