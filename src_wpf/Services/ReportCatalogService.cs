using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace SepehryarWPF.Services
{
    public class ReportItem
    {
        public string FileName { get; set; }
        public string Path { get; set; }
        public string DataSourcesSummary { get; set; }
        public List<string> DataSources { get; set; }
        public List<string> Columns { get; set; }

        public ReportItem()
        {
            DataSources = new List<string>();
            Columns = new List<string>();
        }
    }

    public class ReportCatalogService
    {
        private static readonly List<ReportItem> _cachedReports = new List<ReportItem>();
        private static bool _isLoaded = false;

        public static int TotalReportsCount
        {
            get
            {
                LoadCatalog();
                return _cachedReports.Count;
            }
        }

        public static void LoadCatalog()
        {
            if (_isLoaded) return;
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string catalogPath = Path.Combine(baseDir, "data", "report_catalog.json");
                if (!File.Exists(catalogPath))
                {
                    catalogPath = Path.GetFullPath(Path.Combine(baseDir, @"..\..\..\data\report_catalog.json"));
                }

                if (File.Exists(catalogPath))
                {
                    string json = File.ReadAllText(catalogPath, System.Text.Encoding.UTF8);
                    using var doc = JsonDocument.Parse(json);

                    foreach (var prop in doc.RootElement.EnumerateObject())
                    {
                        var item = new ReportItem();
                        item.FileName = prop.Name;
                        if (prop.Value.TryGetProperty("path", out var p))
                        {
                            item.Path = p.GetString() ?? "";
                        }

                        if (prop.Value.TryGetProperty("datasources", out var ds) && ds.ValueKind == JsonValueKind.Object)
                        {
                            foreach (var dsProp in ds.EnumerateObject())
                            {
                                item.DataSources.Add(dsProp.Name);
                                if (dsProp.Value.ValueKind == JsonValueKind.Array)
                                {
                                    foreach (var col in dsProp.Value.EnumerateArray())
                                    {
                                        string colName = col.GetString();
                                        if (!string.IsNullOrEmpty(colName) && !item.Columns.Contains(colName))
                                        {
                                            item.Columns.Add(colName);
                                        }
                                    }
                                }
                            }
                        }

                        item.DataSourcesSummary = string.Join(", ", item.DataSources.Take(3));
                        _cachedReports.Add(item);
                    }
                    _isLoaded = true;
                }
            }
            catch
            {
                // Catalog optional
            }
        }

        public static List<ReportItem> Search(string query)
        {
            LoadCatalog();
            if (string.IsNullOrWhiteSpace(query))
            {
                return _cachedReports.Take(50).ToList();
            }

            string q = query.ToLower().Trim();
            return _cachedReports
                .Where(r => (r.FileName != null && r.FileName.ToLower().Contains(q)) ||
                            (r.DataSourcesSummary != null && r.DataSourcesSummary.ToLower().Contains(q)) ||
                            r.Columns.Any(c => c.ToLower().Contains(q)))
                .Take(50)
                .ToList();
        }

        public static List<ReportItem> GetAll()
        {
            LoadCatalog();
            return _cachedReports;
        }
    }
}
