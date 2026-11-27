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
        Logger.LogInfo("Nomes de falante traduzidos na tabela Keywords");
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
