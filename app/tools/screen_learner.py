"""
Sepehryar Smart Screen Learner (گزینه ۱):
ابزار ثبت و آموزش تصویری فرم‌های نرم‌افزار سپهریار
با فشردن کلید میانبر F9، از پنجره فعال نرم‌افزار سپهریار عکس می‌گیرد،
آن را نام‌گذاری کرده و مستقیماً به حافظه و کاتالوگ هوش مصنوعی اضافه می‌کند.
"""
import ctypes
from ctypes import wintypes
import json
import os
import re
import sys
import time
from pathlib import Path

# Set UTF-8
sys.stdout.reconfigure(encoding='utf-8')

try:
    from PIL import Image
    import keyboard
except ImportError:
    print("در حال بارگذاری پیش‌نیازها...")
    os.system(f'"{sys.executable}" -m pip install keyboard pillow pywin32-ctypes')
    from PIL import Image
    import keyboard

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

IMG_DIR = Path("D:/ai app/knowledge_base/manuals/images")
CATALOG_PATH = Path("D:/ai app/knowledge_base/manuals/images/ui_catalog.json")

SRCCOPY = 0x00CC0020


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]


def get_active_window():
    """Returns (hwnd, title, (left, top, right, bottom))."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, "", None

    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    title = buff.value.strip()

    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    return hwnd, title, bbox


def capture_window_rect(bbox, filepath):
    """Captures specific window rectangle using GDI."""
    left, top, right, bottom = bbox
    width = max(10, right - left)
    height = max(10, bottom - top)

    hdesktop = user32.GetDesktopWindow()
    hdc = user32.GetDC(hdesktop)
    memdc = gdi32.CreateCompatibleDC(hdc)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc, width, height)

    old_bmp = gdi32.SelectObject(memdc, hbitmap)
    gdi32.BitBlt(memdc, 0, 0, width, height, hdc, left, top, SRCCOPY)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf_size = width * height * 4
    buf = (ctypes.c_char * buf_size)()

    gdi32.GetDIBits(hdc, hbitmap, 0, height, ctypes.byref(buf), ctypes.byref(bmi), 0)
    img = Image.frombuffer('RGBA', (width, height), buf, 'raw', 'BGRA', 0, 1)
    img.convert('RGB').save(filepath, "PNG", optimize=True)

    gdi32.SelectObject(memdc, old_bmp)
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(hdesktop, hdc)


def sanitize_filename(title: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]', "", title)
    clean = clean.replace(" ", "_").strip("_")
    if not clean or len(clean) < 2:
        clean = f"sepehr_form_{int(time.time())}"
    return clean


def on_hotkey_pressed():
    """Triggered on F9 press."""
    try:
        hwnd, title, bbox = get_active_window()
        if not bbox or not title:
            print("\n⚠️ هیچ پنجره فعالی شناسایی نشد. لطفاً روی فرم مورد نظر در سپهریار کلیک کنید.")
            return

        safe_name = sanitize_filename(title)
        filename = f"live_{safe_name}.png"
        filepath = IMG_DIR / filename
        IMG_DIR.mkdir(parents=True, exist_ok=True)

        capture_window_rect(bbox, str(filepath))

        # Play system beep
        try:
            import winsound
            winsound.Beep(1200, 150)
        except Exception:
            pass

        # Update catalog
        catalog = {}
        if CATALOG_PATH.exists():
            try:
                with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
            except Exception:
                catalog = {}

        tag = f"![{title}](file:///d:/ai app/knowledge_base/manuals/images/{filename})"
        catalog[filename] = {
            "title": title,
            "filename": filename,
            "tag": tag,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        print(f"\n📸 عکس فرم «{title}» با موفقیت ذخیره شد!")
        print(f"   📁 فایل: {filename}")
        print(f"   🤖 هوش مصنوعی این فرم را شناخت و آماده استفاده در چت شد.\n")
        print("منتظر فرم بعدی... (کلید F9 را در هر پنجره دیگری بزنید، یا Ctrl+C برای خروج)")

    except Exception as ex:
        print(f"\n❌ خطا در ثبت اسکرین‌شات: {ex}")


def main():
    print("=" * 65)
    print("📸 دستیار هوشمند ثبت و آموزش فرم‌های سپهریار (Sepehryar UI Learner)")
    print("=" * 65)
    print("دستورالعمل ساده:")
    print("۱. نرم‌افزار سپهریار را باز کنید و وارد هر فرمی که مایلید بشوید.")
    print("۲. هر زمان در پنجره فرم بودید، کلید [ F9 ] را روی کیبورد فشار دهید.")
    print("۳. اسکریپت خودکار از فرم عکس می‌گیرد و آن را به مغز هوش مصنوعی الصاق می‌کند!")
    print("-" * 65)
    print("🎯 در حال گوش دادن به کلید [ F9 ] ... (برای خروج پنجره را ببندید یا Ctrl+C بزنید)\n")

    keyboard.add_hotkey('F9', on_hotkey_pressed)
    keyboard.wait()


if __name__ == "__main__":
    main()
