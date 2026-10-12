using System;
using System.Runtime.InteropServices;
using System.Windows.Interop;

namespace SepehryarWPF.Services
{
    public class GlobalHotkey : IDisposable
    {
        private const int WM_HOTKEY = 0x0312;
        private const uint MOD_CONTROL = 0x0002;
        private const uint MOD_NOREPEAT = 0x4000;
        private const uint VK_SPACE = 0x20;

        private readonly int _hotkeyId;
        private IntPtr _hWnd;
        private HwndSource _source;
        private bool _isRegistered;

        public event Action HotkeyPressed;

        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        public GlobalHotkey(int hotkeyId = 9001)
        {
            _hotkeyId = hotkeyId;
        }

        public bool Register(IntPtr hWnd)
        {
            if (_isRegistered) return true;
            _hWnd = hWnd;

            _source = HwndSource.FromHwnd(_hWnd);
            if (_source != null)
            {
                _source.AddHook(HwndHook);
            }

            // Register Ctrl + Space
            _isRegistered = RegisterHotKey(_hWnd, _hotkeyId, MOD_CONTROL | MOD_NOREPEAT, VK_SPACE);
            return _isRegistered;
        }

        private IntPtr HwndHook(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            if (msg == WM_HOTKEY && wParam.ToInt32() == _hotkeyId)
            {
                if (HotkeyPressed != null)
                {
                    HotkeyPressed();
                }
                handled = true;
            }
            return IntPtr.Zero;
        }

        public void Unregister()
        {
            if (_isRegistered && _hWnd != IntPtr.Zero)
            {
                UnregisterHotKey(_hWnd, _hotkeyId);
                if (_source != null)
                {
                    _source.RemoveHook(HwndHook);
                }
                _isRegistered = false;
            }
        }

        public void Dispose()
        {
            Unregister();
        }
    }
}
