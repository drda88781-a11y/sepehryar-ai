# معماری سامانه Sepehryar AI Engine (Phase 1 & 2)

## ۱. نمای کلی معماری لایه‌ای (Layered Architecture)

```
┌────────────────────────────────────────────────────────┐
│             رابط کاربری PySide6 (فارسی / RTL)          │
│   (داشبورد | تحلیل دیتابیس | Query Explorer | سلامت)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│            لایه‌ی سرویس‌ها و ابزارها (Tools Layer)      │
│  (inspect_database, inspect_table, run_safe_select, …) │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
┌─────────────▼─────────────┐ ┌───────────▼──────────────┐
│  Database Intelligence    │ │  Local SQLite Repository │
│  - Deep Schema Scanner    │ │  - App Config & Settings │
│  - Safe SQL Validator     │ │  - Scanned Meta JSON     │
│  - Relationships Engine   │ │  - Structured Audit Log  │
└─────────────┬─────────────┘ └──────────────────────────┘
              │
┌─────────────▼─────────────┐
│  pyodbc Connection Mgr    │
│  (Windows / SQL Auth)     │
└─────────────┬─────────────┘
              │
┌─────────────▼─────────────┐
│  Microsoft SQL Server     │
│  (Sepehr_hesabico_1403)   │
└───────────────────────────┘
```

## ۲. مشخصات مؤلفه‌ها

### ۱.۲. Offline Guard (`app.core.offline_guard`)
* مسدودسازی فعال در سطح سوکت برای جلوگیری از ارسال بسته‌ها به IPهای عمومی اینترنت.
* صرفاً ارتباط با آدرس‌های Loopback (`127.0.0.1`, `localhost`) و شبکه‌های محلی مجاز شناخته می‌شود.

### ۲.۲. Deep Database Scanner (`app.database.scanner`)
* با استفاده از کاتالوگ ویوهای سیستمی (`sys.tables`, `sys.columns`, `sys.indexes`, `sys.dm_db_partition_stats`) اطلاعات متادیتا را بدون اعمال قفل روی جداول کاری سازمان استخراج می‌کند.
* نگاشت هوشمند دیکشنری تخصصی سپهریار به ساختار فنی جداول.

### ۳.۲. Safe SQL Engine (`app.database.safe_sql`)
* لایه امنیتی جداگانه که تمام دستورات ورودی را اعتبارسنجی می‌کند.
* دستورات مخرب یا ساختاری (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) بلافاصله قبل از رسیدن به پایگاه داده ریجکت می‌شوند.
* ماسک‌سازی فیلدهای حساس (کد ملی، شماره همراه، کلمات عبور).

### ۴.۲. لایه ذخیره‌سازی محلی SQLite (`app.storage.repository`)
* ذخیره ساختار متادیتا برای دسترسی فوری و بدون نیاز به کوئری مجدد.
* فعال‌سازی حالت پیشرفته WAL (Write-Ahead Logging) و Foreign Keys در دیتابیس محلی `app.db`.
