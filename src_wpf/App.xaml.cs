using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Interop;
using SepehryarWPF.Services;

namespace SepehryarWPF
{
    public partial class App : Application
    {
        private GlobalHotkey _hotkey;
        private SpotlightWindow _spotlight;
        private MainWindow _main;
        private readonly BrainApiClient _apiClient = new BrainApiClient();

        public App()
        {
            DispatcherUnhandledException += (s, ev) =>
            {
                File.WriteAllText("crash.log", ev.Exception.ToString());
                MessageBox.Show(ev.Exception.ToString(), "Sepehryar WPF Error");
            };
            AppDomain.CurrentDomain.UnhandledException += (s, ev) =>
            {
                File.WriteAllText("crash.log", ev.ExceptionObject.ToString());
            };
        }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "startup.log");
            File.AppendAllText(logPath, "App.OnStartup entered at: " + DateTime.Now + "\n");

            try
            {
                File.AppendAllText(logPath, "1. Task.Run daemon starting...\n");
                // 1. Ensure local AI brain daemon is active in background
                Task.Run(new Func<Task>(async () =>
                {
                    try { await _apiClient.EnsureDaemonRunningAsync(); } catch { }
                }));

                File.AppendAllText(logPath, "2. Creating SpotlightWindow...\n");
                _spotlight = new SpotlightWindow();
                File.AppendAllText(logPath, "SpotlightWindow created successfully.\n");

                File.AppendAllText(logPath, "3. Creating MainWindow...\n");
                _main = new MainWindow();
                File.AppendAllText(logPath, "MainWindow created successfully.\n");

                _main.SetSpotlightWindow(_spotlight);
                this.MainWindow = _main;

                File.AppendAllText(logPath, "4. Showing MainWindow...\n");
                _main.Show();
                File.AppendAllText(logPath, "MainWindow.Show() completed.\n");

                // 3. Register Global Hotkey (Ctrl + Space) on Main Window HWND
                File.AppendAllText(logPath, "5. Registering Global Hotkey...\n");
                var helper = new WindowInteropHelper(_main);
                _hotkey = new GlobalHotkey();
                _hotkey.HotkeyPressed += () =>
                {
                    _spotlight.Dispatcher.Invoke(new Action(() =>
                    {
                        _spotlight.ToggleVisibility();
                    }));
                };
                bool hotkeyRegistered = _hotkey.Register(helper.Handle);
                File.AppendAllText(logPath, "Global Hotkey registered: " + hotkeyRegistered + "\n");
            }
            catch (Exception ex)
            {
                File.AppendAllText(logPath, "STARTUP FATAL ERROR: " + ex.ToString() + "\n");
                MessageBox.Show(ex.ToString(), "Sepehryar WPF Startup Error");
            }
        }

        protected override void OnExit(ExitEventArgs e)
        {
            if (_hotkey != null)
            {
                _hotkey.Dispose();
            }
            base.OnExit(e);
        }
    }
}
