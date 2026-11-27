# Am I Nima — Tradução PT-BR

Tradução não oficial, feita por fã, de **Am I Nima** (HO! Games) para português do Brasil. Cobre o **jogo completo** (pasta `completo/`) e a **demo** (pasta `traducao/`).

- **Falas e narração**: ~10.300 linhas do roteiro Ink no jogo completo e ~1.100 na demo. São traduzidas direto nos assets do jogo, junto com os pensamentos que você arrasta para dizer.
- **Palavras, menus, tutorial e descrições de objetos**: traduzidos na tela via [XUnity.AutoTranslator](https://github.com/bbepis/XUnity.AutoTranslator), só com dicionário, sem tradutor online. Os nomes internos das palavras continuam em inglês, então as combinações do jogo não quebram.

Este repositório **não contém arquivos do jogo**. O `patch.py` lê o texto original da sua cópia instalada.

## Instalar — Linux / Steam Deck

Precisa de [`uv`](https://docs.astral.sh/uv/). Com o jogo **fechado**:

```bash
git clone https://github.com/LuizOttario/am-i-nima-ptbr
cd am-i-nima-ptbr
./install.sh
```

Sem argumento, o script instala no jogo completo, ou na demo se o completo não estiver instalado. Para outra pasta, passe o caminho: `./install.sh "/caminho/Am I Nima"`. Se o nome da pasta terminar em `Demo`, ele usa a tradução da demo.

## Instalar — Windows

Use `completo` para o jogo completo e `traducao` para a demo.

1. Extraia o [BepInEx 5 x64](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.6) e o [XUnity.AutoTranslator-BepInEx](https://github.com/bbepis/XUnity.AutoTranslator/releases/tag/v5.6.3.1) na pasta do jogo.
2. Copie `AutoTranslatorConfig.ini` para `BepInEx/config/`.
3. Copie `completo/AmINima_ptBR.txt` e `completo/AmINima_resizer.txt` para `BepInEx/Translation/pt/Text/`.
   No jogo completo, copie também `plugin/AmINima.BuscaPtBr.dll` para `BepInEx/plugins/`, para a busca de palavras aceitar o nome em português.
4. Faça backup de `Am I Nima_Data/data.unity3d` (ex.: `data.unity3d.orig`) e rode:
   ```
   pip install UnityPy numpy TypeTreeGeneratorAPI
   python patch.py "Am I Nima_Data/data.unity3d.orig" "Am I Nima_Data/data.unity3d" completo
   ```

## Desinstalar

Verifique a integridade dos arquivos na Steam. Depois apague a pasta `BepInEx` e o `winhttp.dll` da pasta do jogo.

## Estrutura

`completo/` (jogo completo) e `traducao/` (demo) têm os mesmos arquivos:

- `falas/*.txt` — falas no formato `ID|texto`. Os IDs seguem a ordem do roteiro do jogo, e as tags (`{voice a=1}`, `<i>` etc.) precisam ficar iguais às do original.
- `escolhas.txt` — pensamentos que você arrasta para falar (`ID|texto`).
- `AmINima_ptBR.txt` — `Original=Tradução` para palavras e interface.
- `AmINima_resizer.txt` — encolhe a fonte das caixas onde o texto em PT não cabe.

`fonte.py` desenha as letras acentuadas (ã, é, ç…) na fonte pixelada do pensamento interno, que não tem acentos, no mesmo estilo das outras letras.

`plugin/` tem um plugin BepInEx (código e DLL compilada) que faz a busca da biblioteca aceitar o nome em português, sem acentos.

`patch.py` confere se a tradução bate com a versão do jogo e aplica.

Se o jogo receber uma atualização, apague `Am I Nima_Data/data.unity3d.orig` (ele é da versão antiga) e rode a instalação de novo. Se o `patch.py` reclamar que a quantidade de falas mudou, a tradução precisa ser atualizada para a nova versão.

Achou algo em inglês ou um erro? Abra uma issue.
Am I Nima é © HO! Games. Projeto de fã, sem afiliação.
