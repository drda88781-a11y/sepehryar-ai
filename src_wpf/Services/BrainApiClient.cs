using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace SepehryarWPF.Services
{
    public class CopilotResponse
    {
        public bool Success { get; set; }
        public string Topic { get; set; }
        public string FormattedMarkdown { get; set; }
        public string SolutionScript { get; set; }
        public string ScriptLanguage { get; set; }
        public List<string> RulesAndGotchas { get; set; }
        public List<string> ValidationChecklist { get; set; }
        public double DurationMs { get; set; }
        public string ErrorMessage { get; set; }

        public CopilotResponse()
        {
            RulesAndGotchas = new List<string>();
            ValidationChecklist = new List<string>();
            ScriptLanguage = "sql";
        }
    }

    public class BrainApiClient
    {
        private static readonly HttpClient _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(45) };
        private readonly string _baseUrl;
        private readonly string _token;

        public BrainApiClient(string baseUrl = "http://127.0.0.1:8080", string token = "sepehryar-local-token-change-in-prod")
        {
            _baseUrl = (baseUrl ?? "").TrimEnd('/');
            _token = token;
        }

        public async Task<bool> EnsureDaemonRunningAsync()
        {
            string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "startup.log");
            try { File.AppendAllText(logPath, "EnsureDaemonRunningAsync checking health...\n"); } catch { }
            bool isUp = await CheckHealthAsync();
            if (isUp)
            {
                try { File.AppendAllText(logPath, "Daemon is already running.\n"); } catch { }
                return true;
            }

            // Try to auto-start backend
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string venvPython = @"C:\Users\khodealidr\.venv\Scripts\python.exe";
                string runPy = Path.GetFullPath(Path.Combine(baseDir, @"..\run.py"));

                ProcessStartInfo psi = null;

                if (File.Exists(venvPython) && File.Exists(runPy))
                {
                    psi = new ProcessStartInfo
                    {
                        FileName = venvPython,
                        Arguments = string.Format("\"{0}\" --server", runPy),
                        WorkingDirectory = Path.GetDirectoryName(runPy),
                        CreateNoWindow = true,
                        UseShellExecute = false,
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                }
                else
                {
                    string exePath = Path.Combine(baseDir, "SepehryarAI.exe");
                    if (!File.Exists(exePath))
                    {
                        string parentDist = Path.GetFullPath(Path.Combine(baseDir, @"..\..\..\dist\SepehryarAI.exe"));
                        if (File.Exists(parentDist)) exePath = parentDist;
                    }

                    if (File.Exists(exePath))
                    {
                        psi = new ProcessStartInfo
                        {
                            FileName = exePath,
                            Arguments = "--server",
                            WorkingDirectory = Path.GetDirectoryName(exePath),
                            CreateNoWindow = true,
                            UseShellExecute = false,
                            WindowStyle = ProcessWindowStyle.Hidden
                        };
                    }
                }

                if (psi != null)
                {
                    Process p = Process.Start(psi);
                    for (int i = 0; i < 25; i++)
                    {
                        await Task.Delay(500);
                        if (await CheckHealthAsync())
                        {
                            return true;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                try { File.AppendAllText(logPath, "EnsureDaemonRunningAsync exception: " + ex.Message + "\n"); } catch { }
            }

            return false;
        }

        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var resp = await _httpClient.GetAsync(_baseUrl + "/health");
                if (!resp.IsSuccessStatusCode) return false;
                var body = await resp.Content.ReadAsStringAsync();
                return body.Contains("0.1.0") || body.Contains("Sepehr") || body.Contains("sepehryar");
            }
            catch
            {
                return false;
            }
        }

        public async Task<CopilotResponse> AskCopilotAsync(string query)
        {
            var sw = Stopwatch.StartNew();

            // 1. Primary: Try Main Chat Endpoint (/api/chat)
            try
            {
                var chatResp = await TryChatAsync(query, sw);
                if (chatResp != null && chatResp.Success)
                {
                    return chatResp;
                }
            }
            catch { }

            // 2. Secondary: Try Sepehryar AI Core Brain endpoint (/api/brain/solve)
            try
            {
                var brainResp = await TryBrainSolveAsync(query, sw);
                if (brainResp != null && brainResp.Success)
                {
                    return brainResp;
                }
            }
            catch { }

            // 3. Fallback: Try agent query endpoint (/api/agent/query)
            return await QueryAgentAsync(query);
        }

        private async Task<CopilotResponse> TryChatAsync(string query, Stopwatch sw)
        {
            var payload = new Dictionary<string, string>();
            payload["query"] = query;
            payload["session_id"] = "wpf_client";
            string json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var req = new HttpRequestMessage(HttpMethod.Post, _baseUrl + "/api/chat")
            {
                Content = content
            };
            req.Headers.Add("Authorization", "Bearer " + _token);

            var resp = await _httpClient.SendAsync(req);
            if (!resp.IsSuccessStatusCode)
            {
                return null;
            }

            string respJson = await resp.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(respJson);
            var root = doc.RootElement;

            sw.Stop();
            var result = new CopilotResponse();
            result.Success = true;
            result.DurationMs = sw.ElapsedMilliseconds;
            result.Topic = "پاسخ هوشمند سپهریار";
            result.FormattedMarkdown = root.TryGetProperty("persian_answer", out var pa) ? (pa.GetString() ?? "") : "";

            if (root.TryGetProperty("sql_plan", out var sp) && sp.ValueKind == JsonValueKind.Object)
            {
                if (sp.TryGetProperty("generated_sql", out var gsql) && gsql.ValueKind == JsonValueKind.String)
                {
                    result.SolutionScript = gsql.GetString();
                    result.ScriptLanguage = "sql";
                }
            }

            return result;
        }

        private async Task<CopilotResponse> TryBrainSolveAsync(string query, Stopwatch sw)
        {
            var payload = new Dictionary<string, string>();
            payload["query"] = query;
            payload["session_id"] = "wpf_spotlight";
            string json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var req = new HttpRequestMessage(HttpMethod.Post, _baseUrl + "/api/brain/solve")
            {
                Content = content
            };
            req.Headers.Add("Authorization", "Bearer " + _token);

            var resp = await _httpClient.SendAsync(req);
            if (!resp.IsSuccessStatusCode)
            {
                return null;
            }

            string respJson = await resp.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(respJson);
            var root = doc.RootElement;

            sw.Stop();
            var result = new CopilotResponse();
            result.Success = true;
            result.DurationMs = sw.ElapsedMilliseconds;
            result.Topic = "🧠 دستیار و معمار هوشمند سپهریار (AI Core)";
            result.FormattedMarkdown = root.TryGetProperty("solution_markdown", out var sm) ? sm.GetString() : "";

            string sp = root.TryGetProperty("generated_sp", out var gsp) ? gsp.GetString() : "";
            string sql = root.TryGetProperty("generated_sql", out var gsql) ? gsql.GetString() : "";
            string code = root.TryGetProperty("generated_code", out var gcode) ? gcode.GetString() : "";

            result.SolutionScript = !string.IsNullOrEmpty(sp) ? sp : (!string.IsNullOrEmpty(sql) ? sql : code);
            result.ScriptLanguage = !string.IsNullOrEmpty(sp) || !string.IsNullOrEmpty(sql) ? "sql" : "csharp";

            if (root.TryGetProperty("safety_checks", out var sc) && sc.ValueKind == JsonValueKind.Array)
            {
                foreach (var c in sc.EnumerateArray())
                {
                    result.ValidationChecklist.Add(c.GetString());
                }
            }

            return result;
        }

        private async Task<CopilotResponse> TryCopilotAskAsync(string query, Stopwatch sw)
        {
            var payload = new Dictionary<string, string>();
            payload["query"] = query;
            string json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var req = new HttpRequestMessage(HttpMethod.Post, _baseUrl + "/api/copilot/ask")
            {
                Content = content
            };
            req.Headers.Add("Authorization", "Bearer " + _token);

            var resp = await _httpClient.SendAsync(req);
            if (!resp.IsSuccessStatusCode)
            {
                return null;
            }

            string respJson = await resp.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(respJson);
            var root = doc.RootElement;

            sw.Stop();
            var result = new CopilotResponse();
            result.Success = true;
            result.DurationMs = sw.ElapsedMilliseconds;
            result.Topic = root.TryGetProperty("topic", out var top) ? top.GetString() : "پاسخ هوش مصنوعی سپهریار";
            result.FormattedMarkdown = root.TryGetProperty("formatted_markdown", out var fm) ? fm.GetString() : "";
            result.SolutionScript = root.TryGetProperty("solution_script", out var ss) ? ss.GetString() : "";
            result.ScriptLanguage = root.TryGetProperty("script_language", out var sl) ? sl.GetString() : "sql";

            if (root.TryGetProperty("rules_and_gotchas", out var rg) && rg.ValueKind == JsonValueKind.Array)
            {
                foreach (var g in rg.EnumerateArray())
                {
                    result.RulesAndGotchas.Add(g.GetString());
                }
            }

            return result;
        }

        public async Task<CopilotResponse> QueryAgentAsync(string query, string priorError = null)
        {
            var sw = Stopwatch.StartNew();
            try
            {
                var payload = new Dictionary<string, string>();
                payload["query"] = query;
                string json = JsonSerializer.Serialize(payload);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var req = new HttpRequestMessage(HttpMethod.Post, _baseUrl + "/api/agent/query")
                {
                    Content = content
                };
                req.Headers.Add("Authorization", "Bearer " + _token);

                var resp = await _httpClient.SendAsync(req);
                sw.Stop();

                if (resp.IsSuccessStatusCode)
                {
                    string respJson = await resp.Content.ReadAsStringAsync();
                    using var doc = JsonDocument.Parse(respJson);
                    var root = doc.RootElement;

                    string ans = root.TryGetProperty("persian_answer", out var pa) ? pa.GetString() : "";
                    string sp = root.TryGetProperty("generated_sp", out var gsp) ? gsp.GetString() : "";
                    string sql = root.TryGetProperty("generated_sql", out var gsql) ? gsql.GetString() : "";

                    var result = new CopilotResponse();
                    result.Success = true;
                    result.FormattedMarkdown = ans;
                    result.SolutionScript = !string.IsNullOrEmpty(sp) ? sp : sql;
                    result.ScriptLanguage = "sql";
                    result.Topic = "پاسخ هوشمند Sepehryar AI Core";
                    result.DurationMs = sw.ElapsedMilliseconds;
                    return result;
                }

                // If even /api/agent/query failed
                var errResult = new CopilotResponse();
                errResult.Success = false;
                errResult.ErrorMessage = "سرویس پس‌زمینه پاسخی ارسال نکرد (کد خطا: " + resp.StatusCode.ToString() + ")";
                errResult.FormattedMarkdown = "⚠️ ارتباط با سرویس هوش مصنوعی محلی برقرار نشد (" + resp.StatusCode.ToString() + ").\nلطفاً از اجرای سرویس اطمینان حاصل کنید.";
                return errResult;
            }
            catch (Exception ex)
            {
                sw.Stop();
                var exResult = new CopilotResponse();
                exResult.Success = false;
                exResult.ErrorMessage = ex.Message;
                exResult.FormattedMarkdown = "❌ عدم دسترسی به سرویس هوش مصنوعی محلی (127.0.0.1:8080).\nعلت: " + ex.Message;
                return exResult;
            }
        }
    }
}
