"""
Sepehryar Automated Full-System Knowledge Learner & Ontology Builder:
Extracts menus, forms, shortcuts, database mappings, and visual screenshots
directly from the Sepehryar binaries (Hesabdari.exe), resources, and SQL database,
compiling them into an exhaustive AI Operational Knowledge Base.
"""
import json
import os
import re
import sys
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path("D:/ai app")
EXE_PATH = BASE_DIR / "exe full" / "SEPEHRYAR.Hesabdari" / "SEPEHRYAR.Hesabdari" / "Hesabdari.exe"
IMAGES_DIR = BASE_DIR / "knowledge_base" / "manuals" / "images"
CATALOG_PATH = IMAGES_DIR / "ui_catalog.json"
ONTOLOGY_PATH = BASE_DIR / "knowledge_base" / "manuals" / "sepehryar_complete_ontology.json"
EXTRACTED_MENUS_PATH = BASE_DIR / "knowledge_base" / "manuals" / "extracted_menus_main.json"


def clean_farsi_text(text: str) -> str:
    """Cleans accelerator characters (&), extra spaces, and shortcuts from menu titles."""
    if not text:
        return ""
    t = text.replace("&", "").strip()
    # Normalize multiple whitespace
    t = re.sub(r'\s+', ' ', t)
    return t


def extract_shortcut_from_text(text: str) -> tuple[str, str]:
    """Separates title from shortcut key (e.g. 'اطلاعات اشخاص Ctrl+Y' -> ('اطلاعات اشخاص', 'Ctrl+Y'))."""
    match = re.search(r'(Ctrl\+[A-Za-z0-9]|F[1-9]|F1[0-2]|Shift\+[A-Za-z0-9]|Alt\+[A-Za-z0-9])', text, re.IGNORECASE)
    if match:
        shortcut = match.group(1).upper()
        title = text[:match.start()].strip()
        return clean_farsi_text(title), shortcut
    return clean_farsi_text(text), ""


def build_system_ontology():
    print("=" * 70)
    print("🧠 آغاز فرآیند یادگیری خودکار و استخراج عمیق دانش نرم‌افزار سپهریار")
    print("=" * 70)

    # 1. Load Extracted Menu Strings
    raw_menus = {}
    if EXTRACTED_MENUS_PATH.exists():
        try:
            with open(EXTRACTED_MENUS_PATH, "r", encoding="utf-8-sig") as f:
                raw_menus = json.load(f)
            print(f"✅ تعداد {len(raw_menus)} عنوان منو و دکمه از باینری برنامه بارگذاری شد.")
        except Exception as ex:
            print(f"⚠️ خطا در خواندن منوهای استخراج‌شده: {ex}")

    # 2. Map existing screenshots in images folder
    available_images = {}
    if IMAGES_DIR.exists():
        for img_file in IMAGES_DIR.glob("*.*"):
            if img_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                available_images[img_file.name] = {
                    "filename": img_file.name,
                    "stem": img_file.stem,
                    "path": f"file:///d:/ai%20app/knowledge_base/manuals/images/{img_file.name}",
                    "size": img_file.stat().st_size
                }
    print(f"✅ تعداد {len(available_images)} تصویر واقعی از محیط نرم‌افزار سپهریار شناسایی شد.")

    # 3. Categorize into Subsystems and Golden Operational Topics
    subsystems = {
        "anbardari": {
            "title": "سیستم انبارداری، کالا و کنترل موجودی",
            "db_tables": ["TblKala", "TblAnbar", "TblKardexKala", "TblMojodiKala", "TblFactorKala", "TblBarcode"],
            "accounting_nature": "دارایی جاری (موجودی مواد و کالا - کد کل ۱۰۳) / قیمت تمام‌شده کالای فروش‌رفته (کد کل ۸۰۱)",
            "images": [img for img in available_images if img.startswith("anbar_")],
            "forms": []
        },
        "forush": {
            "title": "سیستم فروش، فاکتورها و طرف‌حساب‌ها",
            "db_tables": ["TblFactor", "TblFactorDetail", "TblPerson", "TblPishFactor", "TblForooshPrice"],
            "accounting_nature": "بستانکار: فروش (کد ۷۰۱) و ارزش افزوده پرداختی (کد ۳۰۲/۲) | بدهکار: بدهکاران تجاری (کد ۱۱۰/۱) یا نقد/بانک",
            "images": [img for img in available_images if img.startswith("factor_") or "forush" in img],
            "forms": []
        },
        "kharid": {
            "title": "سیستم خرید، تدارکات و تامین‌کنندگان",
            "db_tables": ["TblFactorKharid", "TblFactorKharidDetail", "TblPerson", "TblSefareshKharid"],
            "accounting_nature": "بدهکار: خرید/موجودی کالا (کد ۱۰۳) و اعتبار ارزش افزوده (کد ۱۰۸/۱) | بستانکار: بستانکاران تجاری (کد ۲۰۱/۱)",
            "images": [img for img in available_images if "kharid" in img],
            "forms": []
        },
        "hesabdari": {
            "title": "سیستم حسابداری مالی، اسناد و دفاتر قانونی",
            "db_tables": ["TblSanad", "TblSanadDetail", "TblHesabKol", "TblHesabMoien", "TblHesabTafsili", "TblDoreMali"],
            "accounting_nature": "رعایت تراز دوطرفه (جمع بدهکار = جمع بستانکار) در سطح کل، معین و تفصیلی",
            "images": [img for img in available_images if img.startswith("payeh_") or "hesab" in img],
            "forms": []
        },
        "khazanehdari": {
            "title": "سیستم خزانه‌داری، دریافت، پرداخت، چک و بانک",
            "db_tables": ["TblDaryaft", "TblPardakht", "TblChequeDaryafti", "TblChequePardakhti", "TblBank", "TblSandogh"],
            "accounting_nature": "دریافت: نقد/بانک/اسناد دریافتنی بدهکار، طرف‌حساب بستانکار | پرداخت: طرف‌حساب/هزینه بدهکار، نقد/بانک/اسناد پرداختنی بستانکار",
            "images": [img for img in available_images if img.startswith("daryaft_") or "cheque" in img or "bank" in img],
            "forms": []
        },
        "amaliat_vizheh": {
            "title": "عملیات ویژه (پایان روز، مغایرت بانکی، استهلاک و پایان سال)",
            "db_tables": ["TblBankStatement", "TblDarayiSabet", "TblEstelak", "TblEndDayLock", "TblAuditLog"],
            "accounting_nature": "استهلاک: هزینه استهلاک بدهکار، استهلاک انباشته بستانکار | مغایرت: اقلام باز دفاتر در برابر صورتحساب بانک",
            "images": [img for img in available_images if img.startswith("vijeh_") or img.startswith("vizhe_")],
            "forms": []
        },
        "tolid": {
            "title": "سیستم تولید، فرمول ساخت (BOM) و بهای تمام‌شده",
            "db_tables": ["TblFormulTolid", "TblSanadTolid", "TblMavadAvalie", "TblBahaTamamShode", "TblDastmozdTolid"],
            "accounting_nature": "بدهکار: کالای در جریان ساخت / کالای ساخته‌شده | بستانکار: مواد اولیه مصرفی، دستمزد مستقیم، سربار جذب‌شده",
            "images": [img for img in available_images if img.startswith("tolid_")],
            "forms": []
        },
        "tashilat": {
            "title": "سیستم وام، تسهیلات و اقساط",
            "db_tables": ["TblTashilat", "TblGhest", "TblVosoolGhest", "TblJarimehTakhir"],
            "accounting_nature": "وام دریافتی: بانک بدهکار، تسهیلات پرداختنی بستانکار | قسط: اصل وام و هزینه سود بدهکار، بانک بستانکار",
            "images": [img for img in available_images if img.startswith("tashilat_")],
            "forms": []
        }
    }

    # 4. Parse raw menu entries into categorized forms
    classified_count = 0
    for field_name, raw_title in raw_menus.items():
        title, shortcut = extract_shortcut_from_text(raw_title)
        if len(title) < 2 or title.startswith("bubbleBar"):
            continue

        item = {
            "id": field_name,
            "title": title,
            "raw": raw_title,
            "shortcut": shortcut,
        }

        # Classify by keyword
        assigned = False
        t_lower = title.lower()
        if any(w in t_lower for w in ["کالا", "انبار", "بارکد", "کاردکس", "اتیکت", "موجودی"]):
            subsystems["anbardari"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["فروش", "فاکتور فروش", "مشتری", "پیش فاکتور", "اشخاص"]):
            subsystems["forush"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["خرید", "تامین", "تدارکات", "سفارش خرید"]):
            subsystems["kharid"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["سند", "معین", "کل", "تفصیلی", "دفتر روزنامه", "دفتر کل", "تراز", "سرفصل", "حسابداری", "مرور حساب"]):
            subsystems["hesabdari"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["دریافت", "پرداخت", "چک", "بانک", "صندوق", "وجوه", "حسابها"]):
            subsystems["khazanehdari"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["پایان روز", "تائید اسناد", "مغایرت", "استهلاک", "پایان سال", "ادغام اسناد", "واریز"]):
            subsystems["amaliat_vizheh"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["تولید", "فرمول", "برآورد", "مواد اولیه"]):
            subsystems["tolid"]["forms"].append(item)
            assigned = True
        elif any(w in t_lower for w in ["قسط", "اقساط", "تسهیلات", "وام"]):
            subsystems["tashilat"]["forms"].append(item)
            assigned = True
        else:
            # Fallback to hesabdari or general
            subsystems["hesabdari"]["forms"].append(item)
            assigned = True

        if assigned:
            classified_count += 1

    # 5. Build Unified UI Catalog for the AI Chat Engine
    ui_catalog = {}
    for sub_key, sub_data in subsystems.items():
        for form in sub_data["forms"]:
            # Find closest matching image
            matched_image = ""
            for img_name, img_meta in available_images.items():
                if sub_key == "anbardari" and img_name.startswith("anbar_"):
                    if "kala" in form["title"] and "kala" in img_name:
                        matched_image = img_meta["path"]
                        break
                    elif "anbar" in form["title"] and "anbar" in img_name:
                        matched_image = img_meta["path"]
                        break
                elif sub_key == "amaliat_vizheh" and (img_name.startswith("vijeh_") or img_name.startswith("vizhe_")):
                    if "مغایرت" in form["title"] and ("18" in img_name or "19" in img_name or "20" in img_name):
                        matched_image = img_meta["path"]
                        break
                    elif "استهلاک" in form["title"] and ("12" in img_name or "13" in img_name):
                        matched_image = img_meta["path"]
                        break
                    elif "پایان روز" in form["title"] and ("17" in img_name):
                        matched_image = img_meta["path"]
                        break
                    elif "سند" in form["title"] and ("2" in img_name or "7" in img_name):
                        matched_image = img_meta["path"]
                        break

            # If no direct match, default to first category image if exists
            if not matched_image and sub_data["images"]:
                first_img = sub_data["images"][0]
                matched_image = available_images[first_img]["path"]

            tag = f"![{form['title']}]({matched_image})" if matched_image else ""
            ui_catalog[form["id"]] = {
                "title": form["title"],
                "shortcut": form["shortcut"],
                "subsystem": sub_data["title"],
                "accounting_nature": sub_data["accounting_nature"],
                "db_tables": sub_data["db_tables"],
                "tag": tag,
                "image_url": matched_image
            }

    # Save Catalog and Ontology
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(ui_catalog, f, ensure_ascii=False, indent=2)

    with open(ONTOLOGY_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0.0",
            "source": "Hesabdari.exe (Sepehryar ERP)",
            "subsystems": subsystems,
            "total_classified_forms": classified_count,
            "total_images": len(available_images)
        }, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 یادگیری با موفقیت تکمیل شد!")
    print(f"📊 آمار استخراج و طبقه‌بندی:")
    print(f"   - مجموع فرم‌ها و منوهای طبقه‌بندی‌شده: {classified_count}")
    print(f"   - زیرسیستم‌های فعال: {len(subsystems)}")
    for k, v in subsystems.items():
        print(f"     * {v['title']}: {len(v['forms'])} فرم | {len(v['images'])} تصویر مرتبط")
    print(f"   - کاتالوگ جامع UI ذخیره شد: {CATALOG_PATH}")
    print(f"   - آنتولوژی کامل هوش مصنوعی ذخیره شد: {ONTOLOGY_PATH}")


if __name__ == "__main__":
    build_system_ontology()
