using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using SepehryarWPF.Services;

namespace SepehryarWPF
{
    public partial class MainWindow : Window
    {
        private readonly BrainApiClient _apiClient = new BrainApiClient();
        private SpotlightWindow _spotlightWindow;

        public MainWindow()
        {
            InitializeComponent();
            Loaded += MainWindow_Loaded;
        }

        public void SetSpotlightWindow(SpotlightWindow spotlight)
        {
            _spotlightWindow = spotlight;
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            LoadIntegrationSnippet();
            LoadReportsCatalog();
        }

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        private void BtnMinimize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            var res = MessageBox.Show("آیا مایلید برنامه در پس‌زمینه فعال بماند تا با فشردن کلید میانبر Ctrl+Space در هر زمان باز شود؟\n\n(با انتخاب 'خیر' برنامه به طور کامل بسته می‌شود)", 
                                      "دستیار هوشمند سپهریار", 
                                      MessageBoxButton.YesNo, 
                                      MessageBoxImage.Question);
            if (res == MessageBoxResult.Yes)
            {
                Hide();
            }
            else
            {
                Application.Current.Shutdown();
            }
        }

        private void BtnOpenSpotlight_Click(object sender, RoutedEventArgs e)
        {
            if (_spotlightWindow != null)
            {
                _spotlightWindow.ToggleVisibility();
            }
        }

        private void Nav_Click(object sender, RoutedEventArgs e)
        {
            RadioButton rb = sender as RadioButton;
            if (rb != null && rb.Tag != null)
            {
                int index = int.Parse(rb.Tag.ToString());
                PageChat.Visibility = index == 0 ? Visibility.Visible : Visibility.Collapsed;
                PageHub.Visibility = index == 1 ? Visibility.Visible : Visibility.Collapsed;
                PageReports.Visibility = index == 2 ? Visibility.Visible : Visibility.Collapsed;
                PageSettings.Visibility = index == 3 ? Visibility.Visible : Visibility.Collapsed;
            }
        }

        #region Chat Tab

        private void ChipChat_Click(object sender, RoutedEventArgs e)
        {
            Button btn = sender as Button;
            if (btn != null)
            {
                string text = btn.Content.ToString();
                text = Regex.Replace(text, @"^[^\w\s\u0600-\u06FF]+", "").Trim();
                TxtChatInput.Text = text;
                BtnChatSend_Click(sender, e);
            }
        }

        private void TxtChatInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                BtnChatSend_Click(sender, e);
                e.Handled = true;
            }
        }

        private async void BtnChatSend_Click(object sender, RoutedEventArgs e)
        {
            string query = TxtChatInput.Text.Trim();
            if (string.IsNullOrEmpty(query)) return;

            TxtChatInput.Clear();
            AddUserMessage(query);

            Border loadingBorder = AddSystemMessage("⏳ در حال تحلیل و پردازش...");
            BtnChatSend.IsEnabled = false;

            try
            {
                var resp = await _apiClient.AskCopilotAsync(query);
                PanelChatHistory.Children.Remove(loadingBorder);
                AddAssistantMessage(resp);
            }
            catch (Exception ex)
            {
                PanelChatHistory.Children.Remove(loadingBorder);
                AddSystemMessage("❌ خطا در دریافت پاسخ: " + ex.Message);
            }
            finally
            {
                BtnChatSend.IsEnabled = true;
                ScrollChat.ScrollToBottom();
            }
        }

        private void AddUserMessage(string text)
        {
            var border = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(26, 38, 54)),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(12),
                Margin = new Thickness(50, 0, 0, 10),
                HorizontalAlignment = HorizontalAlignment.Right
            };
            var tb = new TextBlock
            {
                Text = text,
                Foreground = (Brush)FindResource("BrushCyan"),
                FontFamily = (FontFamily)FindResource("MainFont"),
                FontWeight = FontWeights.SemiBold,
                TextWrapping = TextWrapping.Wrap
            };
            border.Child = tb;
            PanelChatHistory.Children.Add(border);
        }

        private Border AddSystemMessage(string text)
        {
            var border = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(22, 27, 34)),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(10),
                Margin = new Thickness(0, 0, 50, 10)
            };
            var tb = new TextBlock
            {
                Text = text,
                Foreground = (Brush)FindResource("BrushTextMuted"),
                FontFamily = (FontFamily)FindResource("MainFont"),
                TextWrapping = TextWrapping.Wrap
            };
            border.Child = tb;
            PanelChatHistory.Children.Add(border);
            return border;
        }

        private void AddAssistantMessage(CopilotResponse resp)
        {
            var border = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(20, 26, 35)),
                BorderBrush = (Brush)FindResource("BrushBorder"),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(14),
                Margin = new Thickness(0, 0, 50, 10)
            };

            var stack = new StackPanel();

            if (!string.IsNullOrEmpty(resp.Topic))
            {
                stack.Children.Add(new TextBlock
                {
                    Text = "🧠 " + resp.Topic,
                    Foreground = (Brush)FindResource("BrushCyan"),
                    FontWeight = FontWeights.Bold,
                    FontFamily = (FontFamily)FindResource("MainFont"),
                    Margin = new Thickness(0, 0, 0, 8)
                });
            }

            RenderMarkdownToStack(stack, resp.FormattedMarkdown);

            border.Child = stack;
            PanelChatHistory.Children.Add(border);
        }

        private void RenderMarkdownToStack(StackPanel container, string markdown)
        {
            if (string.IsNullOrWhiteSpace(markdown)) return;

            // Split by code blocks first: ```...```
            var codeBlockRegex = new Regex(@"```(?:sql|csharp|python)?\r?\n([\s\S]*?)```", RegexOptions.Multiline);
            int lastIndex = 0;

            foreach (Match match in codeBlockRegex.Matches(markdown))
            {
                // 1. Text before this code block
                if (match.Index > lastIndex)
                {
                    string textSegment = markdown.Substring(lastIndex, match.Index - lastIndex);
                    RenderTextAndImages(container, textSegment);
                }

                // 2. The code block itself
                string code = match.Groups[1].Value.Trim();
                RenderCodeBox(container, code);

                lastIndex = match.Index + match.Length;
            }

            // 3. Any trailing text after last code block
            if (lastIndex < markdown.Length)
            {
                string trailing = markdown.Substring(lastIndex);
                RenderTextAndImages(container, trailing);
            }
        }

        private void RenderCodeBox(StackPanel container, string code)
        {
            var codeCard = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(13, 17, 23)),
                BorderBrush = new SolidColorBrush(Color.FromRgb(48, 54, 61)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(6),
                Padding = new Thickness(10),
                Margin = new Thickness(0, 6, 0, 10)
            };

            var codeLayout = new StackPanel();

            // Header bar for code box
            var headerGrid = new Grid { Margin = new Thickness(0, 0, 0, 6) };
            headerGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            headerGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var lblCodeType = new TextBlock
            {
                Text = "💻 اسکریپت آماده T-SQL / C#",
                Foreground = new SolidColorBrush(Color.FromRgb(56, 189, 248)),
                FontSize = 11,
                FontWeight = FontWeights.Bold,
                VerticalAlignment = VerticalAlignment.Center
            };
            Grid.SetColumn(lblCodeType, 0);
            headerGrid.Children.Add(lblCodeType);

            var btnCopy = new Button
            {
                Content = "📋 کپی کد",
                Padding = new Thickness(8, 2, 8, 2),
                FontSize = 11,
                Style = (Style)FindResource("OutlineBtn")
            };
            btnCopy.Click += (s, ev) =>
            {
                try
                {
                    Clipboard.SetText(code);
                    btnCopy.Content = "✓ کپی شد!";
                    Task.Delay(2000).ContinueWith(_ => Dispatcher.Invoke(new Action(() => btnCopy.Content = "📋 کپی کد")));
                }
                catch { }
            };
            Grid.SetColumn(btnCopy, 1);
            headerGrid.Children.Add(btnCopy);
            codeLayout.Children.Add(headerGrid);

            // Code content: LeftToRight!
            var txtCode = new TextBox
            {
                Text = code,
                Background = Brushes.Transparent,
                BorderThickness = new Thickness(0),
                Foreground = new SolidColorBrush(Color.FromRgb(88, 166, 255)),
                FontFamily = new FontFamily("Consolas, Courier New"),
                FontSize = 12,
                FlowDirection = FlowDirection.LeftToRight,
                TextWrapping = TextWrapping.NoWrap,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                IsReadOnly = true
            };
            codeLayout.Children.Add(txtCode);

            codeCard.Child = codeLayout;
            container.Children.Add(codeCard);
        }

        private void RenderTextAndImages(StackPanel container, string text)
        {
            var lines = text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            var paragraphBuffer = new StringBuilder();

            void FlushParagraph()
            {
                if (paragraphBuffer.Length > 0)
                {
                    string pText = paragraphBuffer.ToString().Trim();
                    if (!string.IsNullOrEmpty(pText))
                    {
                        var tb = new TextBox
                        {
                            Text = pText,
                            Background = Brushes.Transparent,
                            BorderThickness = new Thickness(0),
                            Foreground = (Brush)FindResource("BrushTextPrimary"),
                            FontFamily = (FontFamily)FindResource("MainFont"),
                            FontSize = 13,
                            TextWrapping = TextWrapping.Wrap,
                            IsReadOnly = true,
                            FlowDirection = FlowDirection.RightToLeft,
                            Margin = new Thickness(0, 0, 0, 6)
                        };
                        container.Children.Add(tb);
                    }
                    paragraphBuffer.Clear();
                }
            }

            foreach (var rawLine in lines)
            {
                string line = rawLine.Trim();

                // Check for image syntax: ![caption](path)
                var imgMatch = Regex.Match(line, @"!\[(.*?)\]\((.*?)\)");
                if (imgMatch.Success)
                {
                    FlushParagraph();

                    string caption = imgMatch.Groups[1].Value.Trim();
                    string rawPath = imgMatch.Groups[2].Value.Trim();

                    // Normalize path: file:///d:/ai%20app/... or local Windows path
                    string localPath = rawPath.Replace("file:///", "").Replace("%20", " ");
                    if (localPath.StartsWith("/") && localPath.Length > 2 && localPath[2] == ':')
                    {
                        localPath = localPath.Substring(1); // remove leading slash from /d:/...
                    }

                    if (File.Exists(localPath))
                    {
                        RenderImageCard(container, caption, localPath);
                    }
                    continue;
                }

                // Check for Headings: ## or ###
                if (line.StartsWith("## ") || line.StartsWith("### "))
                {
                    FlushParagraph();
                    string headerText = line.TrimStart('#').Trim();
                    var headerTb = new TextBlock
                    {
                        Text = headerText,
                        Foreground = line.StartsWith("## ") ? Brushes.White : new SolidColorBrush(Color.FromRgb(56, 189, 248)),
                        FontSize = line.StartsWith("## ") ? 14 : 13,
                        FontWeight = FontWeights.Bold,
                        FontFamily = (FontFamily)FindResource("MainFont"),
                        FlowDirection = FlowDirection.RightToLeft,
                        Margin = new Thickness(0, 8, 0, 4)
                    };
                    container.Children.Add(headerTb);
                    continue;
                }

                // Check for horizontal rule: ---
                if (line == "---")
                {
                    FlushParagraph();
                    var sep = new Separator
                    {
                        Background = (Brush)FindResource("BrushBorder"),
                        Margin = new Thickness(0, 6, 0, 6)
                    };
                    container.Children.Add(sep);
                    continue;
                }

                paragraphBuffer.AppendLine(rawLine);
            }

            FlushParagraph();
        }

        private void RenderImageCard(StackPanel container, string caption, string filePath)
        {
            var imgCard = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(18, 24, 36)),
                BorderBrush = new SolidColorBrush(Color.FromRgb(38, 51, 77)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(8),
                Margin = new Thickness(0, 8, 0, 10),
                HorizontalAlignment = HorizontalAlignment.Center
            };

            var stack = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center };

            if (!string.IsNullOrEmpty(caption))
            {
                var lblCaption = new TextBlock
                {
                    Text = "📷 " + caption,
                    Foreground = new SolidColorBrush(Color.FromRgb(56, 189, 248)),
                    FontSize = 11,
                    FontWeight = FontWeights.SemiBold,
                    FontFamily = (FontFamily)FindResource("MainFont"),
                    Margin = new Thickness(0, 0, 0, 6),
                    HorizontalAlignment = HorizontalAlignment.Center
                };
                stack.Children.Add(lblCaption);
            }

            try
            {
                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.CacheOption = BitmapCacheOption.OnLoad;
                bitmap.UriSource = new Uri(filePath, UriKind.Absolute);
                bitmap.EndInit();

                var img = new Image
                {
                    Source = bitmap,
                    Stretch = Stretch.Uniform,
                    MaxHeight = 440,
                    MaxWidth = 720
                };
                stack.Children.Add(img);
            }
            catch { }

            imgCard.Child = stack;
            container.Children.Add(imgCard);
        }

        #endregion

        #region Integration Hub Tab

        private void LoadIntegrationSnippet()
        {
            TxtClientSnippet.Text = @"// کلاس آماده کلاینت C# جهت فراخوانی در پروژه تبدیل و گزارش‌ساز
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

public class SepehryarBrainClient
{
    private static readonly HttpClient client = new HttpClient();
    private const string ApiUrl = ""http://127.0.0.1:8080/api/copilot/ask"";
    private const string Token = ""sepehryar-local-token-change-in-prod"";

    public static async Task<string> AskBrainAsync(string question)
    {
        var json = ""{\""query\"":\"""" + question + ""\""}"";
        var content = new StringContent(json, Encoding.UTF8, ""application/json"");
        var req = new HttpRequestMessage(HttpMethod.Post, ApiUrl) { Content = content };
        req.Headers.Add(""Authorization"", ""Bearer "" + Token);

        var resp = await client.SendAsync(req);
        return await resp.Content.ReadAsStringAsync();
    }
}";
        }

        private void BtnCopyClientCode_Click(object sender, RoutedEventArgs e)
        {
            Clipboard.SetText(TxtClientSnippet.Text);
            BtnCopyClientCode.Content = "✓ کپی شد!";
            Task.Delay(2000).ContinueWith(new Action<Task>(_ => Dispatcher.Invoke(new Action(() => BtnCopyClientCode.Content = "📋 کپی کامل کد C#"))));
        }

        private async void BtnTestPing_Click(object sender, RoutedEventArgs e)
        {
            BtnTestPing.IsEnabled = false;
            TxtPingResult.Text = "در حال ارسال پینگ...";
            try
            {
                var sw = Stopwatch.StartNew();
                bool ok = await _apiClient.CheckHealthAsync();
                sw.Stop();
                TxtPingResult.Text = ok ? string.Format("✅ ارتباط برقرار است ({0}ms)", sw.ElapsedMilliseconds) : "❌ سرویس در دسترس نیست.";
                TxtPingResult.Foreground = ok ? new SolidColorBrush(Color.FromRgb(74, 222, 128)) : new SolidColorBrush(Color.FromRgb(248, 113, 113));
            }
            finally
            {
                BtnTestPing.IsEnabled = true;
            }
        }

        #endregion

        #region Reports Catalog Tab

        private void LoadReportsCatalog()
        {
            try
            {
                ReportCatalogService.LoadCatalog();
                TxtReportCount.Text = string.Format("{0} قالب گزارش Stimulsoft", ReportCatalogService.TotalReportsCount);
                ListReports.ItemsSource = ReportCatalogService.Search("");
            }
            catch { }
        }

        private void TxtReportSearch_TextChanged(object sender, TextChangedEventArgs e)
        {
            string q = TxtReportSearch.Text;
            var results = ReportCatalogService.Search(q);
            ListReports.ItemsSource = results;
        }

        private void ListReports_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            // Selected report
        }

        #endregion
    }
}
