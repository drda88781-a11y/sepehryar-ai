using System;
using System.IO;
using System.Windows;

namespace SepehryarWPF
{
    public static class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "startup.log");
            File.WriteAllText(logPath, "Main entered at: " + DateTime.Now + "\n");
            try
            {
                var app = new App();
                File.AppendAllText(logPath, "App instance created at: " + DateTime.Now + "\n");
                app.InitializeComponent();
                File.AppendAllText(logPath, "InitializeComponent completed at: " + DateTime.Now + "\n");
                app.Run();
                File.AppendAllText(logPath, "app.Run() returned at: " + DateTime.Now + "\n");
            }
            catch (Exception ex)
            {
                File.AppendAllText(logPath, "FATAL EXCEPTION: " + ex.ToString() + "\n");
                MessageBox.Show("خطا در اجرای برنامه:\n\n" + ex.Message + "\n\nجزئیات در startup.log ذخیره شد.", "خطا در استارت SepehryarWPF", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
