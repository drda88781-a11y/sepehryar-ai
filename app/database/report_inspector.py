"""
Report & Template Inspector for Sepehryar ERP.
Discovers and explains exact columns, datasets, and Stimulsoft (.mrt) / Crystal (.rpt)
configurations for invoices, warehouse receipts, and financial reports.
"""
import json
import re
from pathlib import Path
from typing import Optional, Any
from app.config.settings import settings


class ReportInspector:
    """Specialized engine for querying Sepehryar report schemas, MRT datasets, and columns."""

    def __init__(self) -> None:
        self.catalog_path = settings.data_dir / "report_catalog.json"
        self._catalog: dict[str, Any] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        import sys
        candidates = [
            settings.data_dir / "report_catalog.json",
            Path(__file__).resolve().parent.parent.parent / "data" / "report_catalog.json",
        ]
        if getattr(sys, "frozen", False):
            bundle_p = Path(getattr(sys, "_MEIPASS", "")) / "data" / "report_catalog.json"
            candidates.insert(0, bundle_p)

        for p in candidates:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        self._catalog = json.load(f)
                    if self._catalog:
                        break
                except Exception:
                    pass

    def search_reports(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search reports by query keywords (e.g., 'A5', 'فاکتور', 'حواله', 'چک')."""
        if not self._catalog:
            self._load_catalog()

        q_norm = query.lower().replace("ي", "ی").replace("ك", "ک")
        keywords = re.findall(r"[\w\d]+", q_norm)

        # Keyword mapping for Persian to English report names
        kw_map = {
            "فاکتور": ["factor", "forush", "kharid"],
            "حواله": ["havale"],
            "چک": ["check", "chk"],
            "کالا": ["kala"],
            "انبار": ["anbar", "havale", "resid"],
            "استهلاک": ["estehlak"],
            "دارایی": ["darayi"],
            "پیش": ["pish"],
            "فیش": ["fish"],
            "رسید": ["resid"],
            "مشتری": ["customer", "moshtari"],
            "a5": ["a5"],
            "a4": ["a4"],
        }

        search_tokens = set(keywords)
        for k, v in kw_map.items():
            if k in q_norm:
                search_tokens.update(v)

        results = []
        for fname, data in self._catalog.items():
            score = 0
            fname_lower = fname.lower()
            for tok in search_tokens:
                if tok in fname_lower:
                    score += 3
            # Check in datasources and column names
            for ds, cols in data.get("datasources", {}).items():
                ds_lower = ds.lower()
                for tok in search_tokens:
                    if tok in ds_lower:
                        score += 2
                    for col in cols:
                        if tok == col.lower():
                            score += 1

            if score > 0:
                results.append((score, data))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def explain_report_structure(self, query: str) -> Optional[str]:
        """Generate detailed architectural explanation of columns and datasets for a report query."""
        reports = self.search_reports(query, limit=3)
        if not reports:
            return None

        primary = reports[0]
        fname = primary["file_name"]
        datasources = primary.get("datasources", {})

        # Friendly Persian translation of common dataset aliases
        ds_friendly = {
            "RptFatorForushKala": "اقلام و سطرهای کالای فاکتور",
            "RptFacorOnvan": "سربرگ فاکتور و اطلاعات خریدار",
            "RptFactorAmavel": "عوامل، کسورات و اضافات فاکتور (ارزش افزوده/کرایه)",
            "RptTasvieyFactor": "اطلاعات تسویه، پرداخت و دریافت فاکتور",
            "RptCompany": "مشخصات شرکت صادرکننده و امضاها",
            "RptHavaleKala": "اقلام و ردیف‌های حواله خروج انبار",
            "RptHavaleOnvan": "سربرگ حواله انبار و اطلاعات تحویل‌گیرنده",
        }

        # Friendly Persian translation of common columns
        col_friendly = {
            "name": "نام کالا / عنوان",
            "unit": "واحد سنجش",
            "ted": "تعداد کالا",
            "fi": "قیمت فی واحد",
            "mab": "مبلغ کل قلم",
            "takh": "مبلغ تخفیف سطر",
            "idkala": "کد کالا",
            "idanbar": "کد انبار",
            "shfactor": "شماره فاکتور",
            "custumcod": "کد مشتری",
            "datefactor": "تاریخ فاکتور",
            "sh_ozviat": "کد عضویت طرف حساب",
            "tell": "تلفن خریدار",
            "mobile": "شماره همراه خریدار",
            "address": "نشانی خریدار",
            "bedehi": "مانده بدهکاری قبلی مشتری",
            "sanad": "شماره سند مالی متناظر",
            "sharh": "شرح عامل / ردیف",
            "bed": "بدهکار",
            "bes": "بستانکار",
            "payan": "پیام پایانی فاکتور",
            "codeeghtesadi": "کد اقتصادی",
        }

        lines = [
            f"### 📄 تحلیل قالب و ستون‌های گزارش «{fname}» (Stimulsoft MRT)",
            f"این قالب گزارش در نرم‌افزار سپهریار بر پایه موتور **Stimulsoft Reports** پیاده‌سازی شده و داده‌های خود را از منابع و دیتاست‌های زیر تأمین می‌کند:\n"
        ]

        for ds_name, cols in datasources.items():
            friendly_name = ds_friendly.get(ds_name, ds_name)
            lines.append(f"#### 🔹 دیتاست `{ds_name}` ({friendly_name}):")
            lines.append(f"تعداد ستون‌ها: **{len(cols)} فیلد**")
            
            # Format columns with translations
            col_badges = []
            for c in cols:
                desc = col_friendly.get(c.lower())
                if desc:
                    col_badges.append(f"`{c}` ({desc})")
                else:
                    col_badges.append(f"`{c}`")
            
            lines.append("• " + "، ".join(col_badges[:15]))
            if len(cols) > 15:
                lines.append(f"*(و {len(cols) - 15} ستون دیگر)*")
            lines.append("")

        if len(reports) > 1:
            lines.append("#### 📑 سایر قالب‌های مشابه کشف‌شده در سپهریار:")
            for o in reports[1:]:
                lines.append(f"• `{o['file_name']}` (شامل دیتاست‌های: {', '.join(list(o.get('datasources', {}).keys())[:3])})")

        return "\n".join(lines)


report_inspector = ReportInspector()
