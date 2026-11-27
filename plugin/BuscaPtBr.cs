// Faz a busca da biblioteca de palavras aceitar o nome em português.
// O jogo compara a busca só com o nome interno (inglês) em ConceptSearchTermsManager.IsMatch;
// aqui, se ele não achar, conferimos a tradução do dicionário do XUnity (sem acentos, sem maiúsculas).
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using BepInEx;
using HarmonyLib;
using UnityEngine.Localization.Settings;

[BepInPlugin("ptbr.aminima.busca", "Am I Nima PT-BR Busca", "1.0.0")]
public class BuscaPtBr : BaseUnityPlugin
{
    static readonly Dictionary<string, string> Pt = new Dictionary<string, string>();

    void Awake()
    {
        var dir = Path.Combine(Paths.BepInExRootPath, "Translation/pt/Text");
        foreach (var file in Directory.GetFiles(dir, "AmINima_ptBR.txt"))
            foreach (var line in File.ReadAllLines(file, Encoding.UTF8))
            {
                if (line.StartsWith("//")) continue;
                var i = line.IndexOf('=');
                if (i <= 0 || line.Contains("\\=")) continue;  // palavras não têm '=' escapado
                var k = line.Substring(0, i).Trim();
                if (!Pt.ContainsKey(k)) Pt[k] = Norm(line.Substring(i + 1));
            }
        var m = AccessTools.Method("ConceptSearchTermsManager:IsMatch");
        if (m == null) { Logger.LogError("ConceptSearchTermsManager.IsMatch não encontrado"); return; }
        new Harmony("ptbr.aminima.busca").Patch(m, postfix: new HarmonyMethod(typeof(BuscaPtBr), nameof(Postfix)));
        Logger.LogInfo("Busca em português ativa (" + Pt.Count + " termos)");
        UnityEngine.SceneManagement.SceneManager.sceneLoaded += (cena, modo) => Carregando();
    }

    // Tela de carregamento: "Carregando..." não cabe na caixa e quebra a linha; passa para a fonte
    // Nima (a da mente), sem quebra e encolhendo se precisar.
    void Carregando()
    {
        TMPro.TMP_FontAsset nima = null;
        foreach (var f in UnityEngine.Resources.FindObjectsOfTypeAll<TMPro.TMP_FontAsset>())
            if (f.name == "Nima SDF") nima = f;
        foreach (var t in UnityEngine.Resources.FindObjectsOfTypeAll<TMPro.TextMeshProUGUI>())
        {
            if (t.name != "Text Loading" || !t.gameObject.scene.IsValid()) continue;
            if (nima != null) t.font = nima;
            t.enableWordWrapping = false;
            t.enableAutoSizing = true; t.fontSizeMin = 18; t.fontSizeMax = t.fontSize;
            Logger.LogInfo("Tela de carregamento ajustada (fonte " + t.font.name + ")");
        }
    }

    // Nome de quem fala: o jogo põe a chave ("MOM") no rótulo e lê de volta para buscar na tabela
    // Keywords; se o XUnity traduzir o rótulo antes, a busca falha. Então o nome é traduzido na própria tabela.
    static readonly Dictionary<string, string> Falantes = new Dictionary<string, string> {
        { "MOM", "MÃE" }, { "YOU", "VOCÊ" }, { "LIFEGUARD", "SALVA-VIDAS" }, { "COACH", "TREINADOR" } };
    UnityEngine.Localization.Tables.StringTable feito;

    bool avisou;

    void Update()
    {
        if (!avisou) { avisou = true; Logger.LogInfo("Update ativo"); }
        if (!LocalizationSettings.InitializationOperation.IsDone) return;
        var loc = LocalizationSettings.SelectedLocale;
        if (loc == null || !loc.Identifier.Code.StartsWith("en")) return;
        var t = LocalizationSettings.StringDatabase.GetTable("Keywords");
        if (t == null || t == feito) return;  // tabela nova (ou recarregada) -> aplica de novo
        foreach (var kv in Falantes)
        {
            var e = t.GetEntry(kv.Key);
            if (e != null) e.Value = kv.Value;
        }
        feito = t;
        Carregando();  // a Nima só existe depois que as fontes do jogo carregam
        Logger.LogInfo("Nomes de falante traduzidos na tabela Keywords: MOM -> " + t.GetEntry("MOM")?.GetLocalizedString() + ", YOU -> " + t.GetEntry("YOU")?.GetLocalizedString());
        // autoteste: as fontes conseguem gerar as letras acentuadas sozinhas (sem fonte reserva)?
        foreach (var f in UnityEngine.Resources.FindObjectsOfTypeAll<TMPro.TMP_FontAsset>())
        {
            if (f.name != "Nima SDF" && f.name != "NotJamScrawl9 SDF") continue;
            uint[] faltando;
            f.HasCharacters("ãâáàéêíóôõúçÃÁÉÊÍÓÕÚÇ", out faltando, false, true);
            var sb = new StringBuilder();
            if (faltando != null) foreach (var u in faltando) sb.Append((char)u);
            Logger.LogInfo("Fonte " + f.name + ": " + (sb.Length == 0 ? "todas as letras acentuadas OK" : "faltando " + sb));
            if (sb.Length > 0)
            {
                var src = f.sourceFontFile;
                var err = src == null ? "src null" : UnityEngine.TextCore.LowLevel.FontEngine.LoadFontFace(src, f.faceInfo.pointSize).ToString();
                uint ia = 0, it = 0;
                bool ga = src != null && UnityEngine.TextCore.LowLevel.FontEngine.TryGetGlyphIndex('a', out ia);
                bool gt = src != null && UnityEngine.TextCore.LowLevel.FontEngine.TryGetGlyphIndex(0xE3, out it);
                Logger.LogInfo("diag " + f.name + ": modo=" + f.atlasPopulationMode + " src=" + (src == null ? "null" : src.name) + " load=" + err + " a=" + ga + "/" + ia + " ã=" + gt + "/" + it + " atlasReadable=" + (f.atlasTexture != null && f.atlasTexture.isReadable));
            }
        }
        // modo de teste: só com o arquivo BepInEx/ptbr_teste presente; desenha amostras e tira print
        if (File.Exists(Path.Combine(Paths.BepInExRootPath, "ptbr_teste")))
            StartCoroutine(Amostra(t.GetEntry("MOM")?.GetLocalizedString()));
    }

    System.Collections.IEnumerator Amostra(string mom)
    {
        var go = new UnityEngine.GameObject("ptbr_teste");
        var canvas = go.AddComponent<UnityEngine.Canvas>();
        canvas.renderMode = UnityEngine.RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 32000;
        var fundo = new UnityEngine.GameObject("fundo").AddComponent<UnityEngine.UI.Image>();
        fundo.transform.SetParent(go.transform, false);
        fundo.color = UnityEngine.Color.black;
        fundo.rectTransform.anchorMin = UnityEngine.Vector2.zero; fundo.rectTransform.anchorMax = UnityEngine.Vector2.one;
        fundo.rectTransform.offsetMin = fundo.rectTransform.offsetMax = UnityEngine.Vector2.zero;
        float y = -60;
        foreach (var f in UnityEngine.Resources.FindObjectsOfTypeAll<TMPro.TMP_FontAsset>())
        {
            if (f.name != "Nima SDF" && f.name != "NotJamScrawl9 SDF") continue;
            var tx = new UnityEngine.GameObject(f.name).AddComponent<TMPro.TextMeshProUGUI>();
            tx.transform.SetParent(go.transform, false);
            tx.font = f; tx.fontSize = 48; tx.color = UnityEngine.Color.white; tx.enableWordWrapping = false;
            tx.rectTransform.anchorMin = tx.rectTransform.anchorMax = new UnityEngine.Vector2(0, 1);
            tx.rectTransform.pivot = new UnityEngine.Vector2(0, 1);
            tx.rectTransform.anchoredPosition = new UnityEngine.Vector2(40, y);
            tx.rectTransform.sizeDelta = new UnityEngine.Vector2(1800, 200);
            tx.text = f.name + "\nEla não parece gostar de você. Ação, coração, pé, avó, irmã, João.\náàâã éê í óôõ ú ç  ÁÀÂÃ ÉÊ Í ÓÔÕ Ú Ç  … “ ” ‘ ’ —";
            y -= 260;
        }
        var nome = new UnityEngine.GameObject("nome").AddComponent<TMPro.TextMeshProUGUI>();
        nome.transform.SetParent(go.transform, false);
        nome.fontSize = 40; nome.color = UnityEngine.Color.green;
        nome.rectTransform.anchorMin = nome.rectTransform.anchorMax = new UnityEngine.Vector2(0, 1);
        nome.rectTransform.pivot = new UnityEngine.Vector2(0, 1);
        nome.rectTransform.anchoredPosition = new UnityEngine.Vector2(40, y);
        nome.rectTransform.sizeDelta = new UnityEngine.Vector2(1800, 100);
        nome.text = "Keywords[MOM] = " + mom;
        for (int i = 0; i < 10; i++) yield return null;
        var arq = Path.Combine(Paths.BepInExRootPath, "ptbr_teste.png");
        UnityEngine.ScreenCapture.CaptureScreenshot(arq);
        yield return new UnityEngine.WaitForSeconds(2);
        UnityEngine.Object.Destroy(go);
        Logger.LogInfo("Print de teste salvo em " + arq);
    }

    static void Postfix(string __0, string __1, ref bool __result)
    {
        if (__result || __0 == null || __1 == null) return;
        string pt;
        if (Pt.TryGetValue(__0.Trim('*', ' '), out pt)) __result = pt.Contains(Norm(__1));
        else if (Pt.TryGetValue(__1.Trim('*', ' '), out pt)) __result = pt.Contains(Norm(__0));
    }

    static string Norm(string s)
    {
        var sb = new StringBuilder();
        foreach (var c in s.Normalize(NormalizationForm.FormD))
            if (CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark) sb.Append(c);
        return sb.ToString().ToUpperInvariant();
    }
}
