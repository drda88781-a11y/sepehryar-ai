using System;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using SepehryarWPF.Services;

namespace SepehryarWPF
{
    public partial class SpotlightWindow : Window
    {
        private readonly BrainApiClient _apiClient = new BrainApiClient();
        private bool _isPinned = true;

        public SpotlightWindow()
        {
            InitializeComponent();
            CenterTop();
            Loaded += (s, e) => CenterTop();

            TxtQuery.TextChanged += (s, e) =>
            {
                TxtPlaceholder.Visibility = string.IsNullOrEmpty(TxtQuery.Text) ? Visibility.Visible : Visibility.Collapsed;
            };
        }

        public void CenterTop()
        {
            var workArea = SystemParameters.WorkArea;
            Left = workArea.Left + (workArea.Width - Width) / 2;
            Top = workArea.Top + 20; // 20px clean margin from top of monitor
        }

        public void ToggleVisibility()
        {
            if (IsVisible)
            {
                Hide();
            }
            else
            {
                CenterTop();
                Show();
                Activate();
                TxtQuery.Focus();
                TxtQuery.SelectAll();
            }
        }

        private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        private void BtnToggleChips_Click(object sender, RoutedEventArgs e)
        {
            bool isVisible = PanelChips.Visibility == Visibility.Visible;
            PanelChips.Visibility = isVisible ? Visibility.Collapsed : Visibility.Visible;
            BtnToggleChips.Content = isVisible ? "⚡ میانبرها ▾" : "⚡ میانبرها ▴";
        }

        private void Window_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                if (BorderResult.Visibility == Visibility.Visible)
                {
                    BorderResult.Visibility = Visibility.Collapsed;
                    TxtQuery.Text = "";
                }
                else
                {
                    Hide();
                }
                e.Handled = true;
            }
        }

        private void TxtQuery_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                BtnSubmit_Click(sender, e);
                e.Handled = true;
            }
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Hide();
        }

        private void BtnPin_Click(object sender, RoutedEventArgs e)
        {
            _isPinned = !_isPinned;
            Topmost = _isPinned;
            BtnPin.Content = _isPinned ? "📌 پین" : "📍 شناور";
        }

        private void Chip_Click(object sender, RoutedEventArgs e)
        {
            Button btn = sender as Button;
            if (btn != null)
            {
                string text = btn.Content.ToString();
                text = Regex.Replace(text, @"^[^\w\s\u0600-\u06FF]+", "").Trim();
                TxtQuery.Text = text;
                BtnSubmit_Click(sender, e);
            }
        }

        private async void BtnSubmit_Click(object sender, RoutedEventArgs e)
        {
            string query = TxtQuery.Text.Trim();
            if (string.IsNullOrEmpty(query)) return;

            PrgLoading.Visibility = Visibility.Visible;
            BtnSubmit.IsEnabled = false;

            try
            {
                var response = await _apiClient.AskCopilotAsync(query);
                DisplayResponse(response);
            }
            catch (Exception ex)
            {
                BorderResult.Visibility = Visibility.Visible;
                TxtAnswer.Text = "خطا در پردازش: " + ex.Message;
            }
            finally
            {
                PrgLoading.Visibility = Visibility.Collapsed;
                BtnSubmit.IsEnabled = true;
            }
        }

        private void DisplayResponse(CopilotResponse resp)
        {
            BorderResult.Visibility = Visibility.Visible;
            TxtResultTopic.Text = string.IsNullOrEmpty(resp.Topic) ? "پاسخ هوش مصنوعی سپهریار" : resp.Topic;
            TxtTiming.Text = string.Format("⚡ زمان پردازش: {0:F0} میلی‌ثانیه", resp.DurationMs);

            string body = resp.FormattedMarkdown;

            // Extract code snippet if present
            string script = resp.SolutionScript;
            if (string.IsNullOrEmpty(script) && !string.IsNullOrEmpty(body))
            {
                var m = Regex.Match(body, @"```(?:sql|csharp|python)?\s*([\s\S]*?)```");
                if (m.Success)
                {
                    script = m.Groups[1].Value.Trim();
                }
            }

            if (!string.IsNullOrEmpty(script))
            {
                BorderCode.Visibility = Visibility.Visible;
                TxtCode.Text = script;
            }
            else
            {
                BorderCode.Visibility = Visibility.Collapsed;
            }

            TxtAnswer.Text = body;
        }

        private void BtnCopyCode_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(TxtCode.Text))
            {
                Clipboard.SetText(TxtCode.Text);
                BtnCopyCode.Content = "✓ کپی شد!";
                Task.Delay(2000).ContinueWith(_ => Dispatcher.Invoke(new Action(() => BtnCopyCode.Content = "📋 کپی اسکریپت")));
            }
        }
    }
}
