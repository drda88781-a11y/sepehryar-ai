"""
Deep Cognitive Reasoning Engine for Sepehryar ERP:
Acts as a Senior ERP Architect and Software Engineer Copilot.
Delivers multi-stage analytical thinking, database gotchas, trigger warnings,
and ready-to-run transactional scripts for Sepehryar accounting and migrations.
"""
import re
from typing import Optional, Any
from app.core.logger import get_logger
from app.database.schema_graph import schema_graph, SEPEHRYAR_TABLE_CARDS
from app.knowledge.search import knowledge_search_engine
from app.database.live_schema_search import live_schema_searcher

logger = get_logger("agent.cognitive_engine")


class CognitiveThoughtStep:
    def __init__(self, stage: str, title: str, details: str):
        self.stage = stage
        self.title = title
        self.details = details


class SepehryarCognitiveResponse:
    def __init__(
        self,
        query: str,
        topic: str,
        analysis: str,
        rules_and_gotchas: list[str],
        solution_script: str,
        script_language: str,
        validation_checklist: list[str],
        thinking_steps: list[CognitiveThoughtStep],
        mode: str = "ENGINEERING"
    ):
        self.query = query
        self.topic = topic
        self.analysis = analysis
        self.rules_and_gotchas = rules_and_gotchas
        self.solution_script = solution_script
        self.script_language = script_language
        self.validation_checklist = validation_checklist
        self.thinking_steps = thinking_steps
        self.mode = mode

    def to_formatted_markdown(self) -> str:
        """Renders response according to mode (USER_GUIDE, DIRECT_CODE, or ENGINEERING)."""
        if self.mode == "USER_GUIDE":
            # Pure operational visual tutorial without code blocks or database developer jargon
            return self.analysis.strip()

        if self.mode == "DIRECT_CODE":
            # Direct code deliverable without long preambles
            notes = "\n".join(f"- {c}" for c in self.validation_checklist)
            res = f"### 💻 {self.topic}\n\n```{self.script_language}\n{self.solution_script.strip()}\n```"
            if notes:
                res += f"\n\n**نکات اجرایی:**\n{notes}"
            return res.strip()

        # Default multi-step engineering analysis
        gotchas_md = "\n".join(f"• ⚠️ {g}" for g in self.rules_and_gotchas)
        checklist_md = "\n".join(f"- [ ] {c}" for c in self.validation_checklist)

        return f"""
### 🧠 تحلیل عمیق مهندسی و معماری سپهریار: {self.topic}

#### ۱. شناخت ساختار و ماهیت مسئله:
{self.analysis}

#### ۲. الزامات حیاتی، تریگرها و تله‌های پنهان دیتابیس:
{gotchas_md}

#### ۳. راهکار فنی و اسکریپت استاندارد:
```{self.script_language}
{self.solution_script}
```

#### ۴. چک‌لیست اعتبارسنجی و تضمین سلامت دیتابیس:
{checklist_md}
        """.strip()


class SepehryarCognitiveEngine:
    """Specialized ERP developer brain synthesizing deep schema reasoning."""

    @classmethod
    def reason_and_solve(cls, query: str) -> SepehryarCognitiveResponse:
        q_norm = query.replace("ي", "ی").replace("ك", "ک").lower().strip()

        # Step 0: Operational User-Guide Manual Questions FIRST (Tutorials + Screenshots, ZERO code)
        from app.agent.manuals_guide import manuals_guide_engine
        user_guide_res = manuals_guide_engine.get_user_guide_response(query, q_norm)
        if user_guide_res:
            return user_guide_res

        # Step 0.1: Direct Code / Stored Procedure Requests (Clean production T-SQL, NO filler)
        direct_code_res = manuals_guide_engine.get_direct_code_response(query, q_norm)
        if direct_code_res:
            return direct_code_res

        # Step 1: Semantic Entity & Action Extraction
        action, target_table, detected_tables = cls._extract_action_and_table(q_norm)

        # 1. Specialized Dynamic SQL Operations (DELETE, UPDATE, INSERT) on Any Table
        if action in ("DELETE", "UPDATE", "INSERT") and target_table:
            return cls._reason_dynamic_sql_operation(query, action, target_table, q_norm)

        # 2. Schema Inspection & JOIN between tables
        if action in ("SCHEMA", "JOIN") or (action == "SELECT" and len(detected_tables) >= 2):
            return cls._reason_schema_and_relations(query, target_table, detected_tables, q_norm)

        # 3. High-level Accounting Workflows (بستن حسابها، سال مالی، انبارگردانی، مغایرت بانکی، راس‌گیری، استهلاک)
        if action == "WORKFLOW" or any(w in q_norm for w in ["بستن حساب", "سال مالی", "انبارگردانی", "مغایرت بانکی", "راس گیری", "استهلاک", "تایید اسناد", "پایان روز"]):
            return cls._reason_workflow_guidance(query, q_norm)

        # 4. Troubleshooting & Database Errors (Deadlock, Violation of PK, Unbalanced voucher, Negative kardex)
        if action == "TROUBLESHOOT" or any(w in q_norm for w in ["خطا", "ارور", "error", "قفل", "deadlock", "خراب", "دوبل", "ناپدید", "نامتوازن"]):
            return cls._reason_troubleshooting(query, target_table, q_norm)

        # 5. Specialized Walkthrough Topics:
        # 5.1 Data Migration & ETL from other systems (تبدیل داده و مهاجرت از هلو/محک/باران)
        if any(w in q_norm for w in ["تبدیل", "مهاجرت", "هلو", "محک", "باران", "سپیدار", "دشت", "انتقال داده", "migration", "etl"]):
            return cls._reason_migration_etl(query)

        # 5.2 Inserting Customers & Linking Accounts (ثبت شخص و اتصال حساب)
        has_person_target = any(w in q_norm for w in ["مشتری", "شخص", "طرف حساب", "اشخاص", "personcod", "شخص جدید", "مشتری جدید"])
        has_person_action = any(w in q_norm for w in ["ثبت", "تعریف", "ایجاد", "وصل", "اتصال", "اضافه", "افزودن"])
        if (has_person_target and has_person_action) or any(w in q_norm for w in ["ثبت شخص", "تعریف مشتری", "ایجاد مشتری", "ثبت مشتری", "personcod", "کد شخص", "وصل شخص", "sh_ozviat"]):
            return cls._reason_person_creation(query)

        # 5.3 Invoices and Sales Transactions (ثبت فاکتور فروش و تراکنش‌های TR)
        has_invoice_target = any(w in q_norm for w in ["فاکتور", "فاکتورها", "فروش", "خرید", "پیش فاکتور"])
        has_invoice_action = any(w in q_norm for w in ["ثبت", "صدور", "درج", "ایجاد", "tr", "ویرایش"])
        if ("فاکتور" in q_norm) or (has_invoice_target and has_invoice_action) or any(w in q_norm for w in ["ثبت فاکتور", "فاکتور فروش", "صدور فاکتور", "درج فاکتور", "فاکتور خرید", "ثبت فروش"]):
            return cls._reason_invoice_creation(query)

        # 5.4 Accounting Vouchers & Balance (ثبت سند حسابداری و بالانس تراز)
        has_voucher_target = any(w in q_norm for w in ["سند", "اسناد", "آرتیکل", "تراز", "افتتاحیه", "اختتامیه", "sanadm", "sanadd"])
        has_voucher_action = any(w in q_norm for w in ["ثبت", "درج", "ایجاد", "بالانس", "تراز", "توازن"])
        if (has_voucher_target and has_voucher_action) or any(w in q_norm for w in ["ثبت سند", "سند افتتاحیه", "آرتیکل", "سند حسابداری", "بالانس سند", "تراز سند"]):
            return cls._reason_voucher_creation(query)

        # 5.5 Cheques & Treasury (مدیریت و ثبت چک‌های دریافتی/پرداختی)
        if any(w in q_norm for w in ["چک", "اسناد دریافتنی", "اسناد پرداختنی", "وصول چک", "برگشت چک", "صیاد", "datechek"]):
            return cls._reason_cheque_management(query)

        # 5.6 Triggers, Concurrency & Deadlocks (تریگرها و قفل‌های دیتابیس)
        if any(w in q_norm for w in ["تریگر", "trigger", "deadlock", "قفل", "کند", "سرعت", "timeout", "nolock", "updatesitesync"]):
            return cls._reason_triggers_and_perf(query)

        # 5.7 Defining Accounts & Chart of Accounts Architecture (تعریف حساب، ساخت حساب، سرفصل و کدینگ)
        has_account_target = any(w in q_norm for w in ["حساب", "حسابها", "حساب‌ها", "سرفصل", "معین", "تفصیلی", "کدینگ", "tblhesab"])
        has_account_action = any(w in q_norm for w in ["تعریف", "ساخت", "ایجاد", "افزودن", "ثبت", "چجوری", "چطوری", "چطور", "چگونه", "نحوه", "روش", "طریقه", "یاد بده"])
        if (has_account_target and has_account_action) or any(w in q_norm for w in [
            "تعریف حساب", "ساخت حساب", "ایجاد حساب", "حساب تعریف", "افزودن حساب", "کدینگ حساب",
            "کدینگ", "سرفصل چیست", "معین چیست", "تفصیلی چیست", "حساب کل", "ساختار حساب", "سرفصل"
        ]):
            return cls._reason_account_definition(query)

        # 5.8 Products, Catalog & Inventory (کالاها، کاردکس انبار و بارکدها در TblKala)
        if any(w in q_norm for w in ["کالا", "کالاها", "انبار", "موجودی", "کاردکس", "tblkala", "بارکد"]):
            return cls._reason_inventory_and_goods(query)

        # 6. Fallback to Dynamic SQL on Target Table if detected
        if target_table:
            return cls._reason_dynamic_sql_operation(query, action or "SELECT", target_table, q_norm)

        # 7. Fallback to Dynamic Semantic & Manuals Synthesis (Replacing static count!)
        return cls._reason_dynamic_synthesis(query, q_norm)

    # --------------------------------------------------------------------------
    # Specialized Domain Reasoners
    # --------------------------------------------------------------------------

    @classmethod
    def _reason_person_creation(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "در سپهریار، اشخاص تنها یک رکورد متنی نیستند؛ هر شخص از یک‌سو در جدول پایه `TblPerson` "
            "و از سوی دیگر در جدول گردش حساب‌های `Master` دارای حساب تفصیلی متناظر است. "
            "ارتباط درختی نرم‌افزار متکی بر اتصال فیلد `Master.personcod` به `TblPerson.Sh_ozviat` می‌باشد."
        )
        gotchas = [
            "عدم مقداردهی `Master.personcod`: باعث می‌شود حساب شخص در دفتر کل درج شود اما در درختواره حساب‌ها و گزارشات اشخاص ناپدید گردد.",
            "تنظیم اشتباه فیلد `Type` در `TblPerson`: مشتری حتماً باید `Type=1`، تأمین‌کننده `Type=2` و بانک `Type=4` باشد.",
            "سرفصل معین: مشتریان تجاری باید ذیل سرفصل کل ۱۱۰ و معین ۱ (بدهکاران تجاری) قرار گیرند.",
            "ثبت در `TblHesabText`: عنوان شخص حتماً باید با کدهای `(Srfsl=110, Moin=1, HSB)` در `TblHesabText` نیز درج شود تا گریدها خالی نمایش داده نشوند.",
            "تفکیک شماره موبایل: متن نام نباید دارای شماره تلفن باشد و موبایل ۱۱ رقمی باید به ستون `Mobile` منتقل شود."
        ]
        sql = """
-- الگوی استاندارد و تراکنشی تعریف مشتری و اتصال حساب در سپهریار
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @ShOzviat INT = 2001;      -- کد عضویت یکتا
    DECLARE @HSB INT = 2001;            -- کد تفصیلی حساب
    DECLARE @Name NVARCHAR(100) = N'حسین محمودیان';
    DECLARE @Mobile VARCHAR(20) = '09134537853';

    -- ۱. درج در پرونده اشخاص
    INSERT INTO dbo.TblPerson (Sh_ozviat, Name, Tell, Mobile, Srfsl, Moin, Hesab, Type, Status)
    VALUES (@ShOzviat, @Name, '', @Mobile, 110, 1, @HSB, 1, 1);

    -- ۲. درج حساب در سرآمد مانده‌ها (اتصال حیاتی personcod)
    INSERT INTO dbo.Master (Srfsl, Moin, HSB, Bed, Bes, sodur, personcod, Masdood)
    VALUES (110, 1, @HSB, 0, 0, 1, @ShOzviat, 0);

    -- ۳. ثبت عنوان در فرهنگ سرفصل‌ها
    INSERT INTO dbo.TblHesabText (Srfsl, Moin, HSB, Text)
    VALUES (110, 1, @HSB, @Name);

    COMMIT TRANSACTION;
    PRINT 'مشتری با موفقیت ایجاد و به سرفصل‌های سپهریار متصل شد.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
        """.strip()

        checklist = [
            "بررسی یکتا بودن `Sh_ozviat` در `TblPerson` قبل از درج.",
            "اطمینان از تطابق `Master.personcod == TblPerson.Sh_ozviat`.",
            "تأیید درج سه‌گانه همزمان در `TblPerson`، `Master` و `TblHesabText` داخل یک Transaction اتمیک."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="تعریف اشخاص و ارتباط تفصیلی در درختواره حساب‌ها",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_invoice_creation(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "فاکتورها در سپهریار جدول سربرگ مجزا ندارند؛ اقلام فاکتور مستقیماً در جدول مرکزی `TR` "
            "با شماره فاکتور مثبت (`Factor > 0`) ثبت می‌شوند و با کد کالا (`Idkala`)، مشتری (`Taraf`)، "
            "تعداد (`TED`) و مبالغ بدهکار/بستانکار سازماندهی می‌گردند."
        )
        gotchas = [
            "تریگرهای حیاتی: جدول `TR` دارای تریگرهای فعال `UpdateSiteSync_TRInsert/Update/Delete` است. در ثبت دسته‌ای فاکتورها، اگر این تریگرها مدیریت نشوند برنامه با قفل و کندی شدید روبرو می‌شود.",
            "مبلغ فاکتور: در سپهریار فیلدی به نام `Mab` در جدول `TR` وجود ندارد؛ مبلغ قلم فاکتور همواره از جمع `(Bed + Bes)` استخراج می‌شود.",
            "ارتباط با انبار: فیلد `IdAnbr` باید به کد انبار معتبر در `TblAnbar` اشاره کند تا کاردکس تعدادی به‌درستی به‌روز شود.",
            "به‌روزرسانی مانده شخص: پس از درج فاکتور نسیه، ستون `Bed` شخص در جدول `Master` باید معادل مبلغ فاکتور افزایش یابد."
        ]
        sql = """
-- الگوی درج قلم فاکتور فروش در جدول TR با رعایت اصول کارایی
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @FactorNo INT = 140501;
    DECLARE @CustomerId INT = 1660;    -- Sh_ozviat مشتری
    DECLARE @KalaId INT = 101001;       -- IDKala کالا
    DECLARE @Quantity FLOAT = 2.0;
    DECLARE @TotalPrice BIGINT = 12000000; -- ریال
    DECLARE @DateR VARCHAR(10) = '1405/01/15';

    -- موقتاً غیرفعال‌سازی تریگرهای همگام‌سازی سایت در صورت ورود انبوه
    -- ALTER TABLE dbo.TR DISABLE TRIGGER UpdateSiteSync_TRInsert;

    INSERT INTO dbo.TR (
        Sodor, Srfsl, Moin, HSB, DateR, Serial, Sharh,
        Idkala, Factor, IdAnbr, TED, SanadM, Taraf, Bed, Bes
    )
    VALUES (
        (SELECT ISNULL(MAX(Sodor), 0) + 1 FROM dbo.TR WITH (NOLOCK)),
        110, 1, @CustomerId, @DateR, 1, N'فاکتور فروش اقلام',
        @KalaId, @FactorNo, 1, @Quantity, 0, @CustomerId, @TotalPrice, 0
    );

    -- به‌روزرسانی مانده بدهکاری مشتری در جدول Master
    UPDATE dbo.Master
    SET Bed = Bed + @TotalPrice
    WHERE Srfsl = 110 AND Moin = 1 AND HSB = @CustomerId;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
        """.strip()

        checklist = [
            "بررسی وجود کد کالا در `TblKala.IDKala` قبل از ثبت قلم فاکتور.",
            "تأیید فیلد `Taraf` به عنوان کلید مشتری (`TblPerson.Sh_ozviat`).",
            "استفاده از هینت `WITH (NOLOCK)` در محاسبات ماکزیمم شماره ردیف (`Sodor`)."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="معماری و منطق ثبت فاکتورهای فروش در جدول TR",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_voucher_creation(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "اسناد حسابداری شامل سربرگ سند در `TblSanad` و آرتیکل‌های بدهکار/بستانکار در `TR` می‌باشند. "
            "سند افتتاحیه همیشه دارای شماره سند ۱ (`SanadM = 1`) است و شرط اولیه اعتبار سیستم، تساوی مطلق "
            "جمع بدهکار با جمع بستانکار (`Diff = 0`) در این سند می‌باشد."
        )
        gotchas = [
            "عدم توازن سند: اگر حتی ۱ ریال اختلاف بین جمع Bed و جمع Bes باشد، ترازنامه سال مالی در سپهریار دچار عدم تطابق می‌شود.",
            "همگام‌سازی با Master: جمع آرتیکل‌های ثبت شده در سند ۱ باید دقیقاً با مقادیر اولیه ستون‌های `Bed` و `Bes` در جدول `Master` همسان باشد.",
            "حذف و جایگزینی سند: قبل از ثبت سند ۱، باید حتماً رکوردهای قبلی `SanadM=1` از هر دو جدول `TblSanad` و `TR` حذف شوند تا اسناد دوبل تولید نشوند."
        ]
        sql = """
-- الگوی تراکنشی ثبت سند افتتاحیه متوازن (Sanad 1)
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @Date VARCHAR(10) = '1405/01/01';
    DECLARE @SanadNo INT = 1;
    DECLARE @TotalAmount BIGINT = 5673732647511; -- مجموع تراز

    -- ۱. پاک‌سازی رکوردهای قبلی سند ۱
    DELETE FROM dbo.TblSanad WHERE SanadM = @SanadNo;
    DELETE FROM dbo.TR WHERE SanadM = @SanadNo;

    -- ۲. ثبت سربرگ سند
    INSERT INTO dbo.TblSanad (SanadM, DateR, Sharh, Bed, Bes)
    VALUES (@SanadNo, @Date, N'سند افتتاحیه دوره مالی ۱۴۰۵', @TotalAmount, @TotalAmount);

    -- ۳. ثبت آرتیکل‌های TR به همراه به‌روزرسانی متناظر جدول Master
    -- (هر آرتیکل با Srfsl, Moin, HSB, Bed, Bes درج می‌گردد)

    COMMIT TRANSACTION;
    PRINT 'سند افتتاحیه با تراز کامل در سپهریار مستقر شد.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
        """.strip()

        checklist = [
            "محاسبه تراز `SUM(Bed) == SUM(Bes)` قبل از شروع تراکنش.",
            "تطابق کدهای تفصیلی با جداول پایه اشخاص و نقد و بانک.",
            "بررسی صحت تاریخ شمسی به فرمت ۱۰ کاراکتری (مثلاً ۱۴۰۵/۰۱/۰۱)."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="معماری اسناد حسابداری و الزامات سند افتتاحیه",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_migration_etl(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "مهاجرت داده از نرم‌افزارهای هلو، محک، باران و سپیدار به سپهریار، نیازمند تطبیق معنایی است؛ "
            "زیرا مفاهیمی مانند کدینگ حساب‌ها، قطبیت مانده و تفکیک شماره موبایل در سیستم‌ها متفاوت است."
        )
        gotchas = [
            "تله قطبیت باران ۳۶۰: در نرم‌افزار باران، `RemainAccount < 0` به معنی بدهکار به ما است، در حالی که در هلو فیلدهای `MandeBed` و `MandeBes` جداگانه هستند.",
            "شماره‌های پنهان در نام: در اکثر سیستم‌های قدیمی، شماره موبایل در انتهای فیلد نام نوشته شده است؛ قبل از درج باید با Regex استخراج و تفکیک گردد.",
            "کدینگ بانک‌ها: بانک‌ها در سپهریار باید تفصیلی مستقل ذیل سرفصل ۱۰۰ معین ۲ داشته باشند و در `TblPerson` دارای `Type=4` باشند.",
            "تریگرهای سپهریار: در زمان Migration، حتماً تریگرهای سنگین همگام‌سازی روی `TR` را به حالت DISABLE درآورید."
        ]
        sql = r"""
# قطعه کد پایتون جهت تبدیل و پاک‌سازی رکورد اشخاص و محاسبه قطبیت برای سپهریار
import re

def transform_to_sepehryar_person(raw_name, raw_balance, source_system="Standard"):
    # ۱. استخراج شماره موبایل ۱۱ رقمی از متن نام
    mob_match = re.search(r'(09\d{9})', raw_name)
    mobile = mob_match.group(1) if mob_match else ""
    clean_name = re.sub(r'(?:09\d{9}|\d{7,10})', '', raw_name).strip()

    # ۲. محاسبه قطبیت بدهکار و بستانکار
    bal = int(raw_balance or 0)
    if source_system == "Baran360":
        bed = abs(bal) if bal < 0 else 0
        bes = bal if bal > 0 else 0
    else:
        bed = bal if bal > 0 else 0
        bes = abs(bal) if bal < 0 else 0

    return {
        "clean_name": clean_name,
        "mobile": mobile,
        "bed": bed,
        "bes": bes,
        "type": 1  # پیش‌فرض مشتری
    }
        """.strip()

        checklist = [
            "تشخیص خودکار سیستم مبدأ از روی اسامی ستون‌ها.",
            "اعمال تمیزکاری نام‌ها و شماره‌ها قبل از درج در TblPerson.",
            "محاسبه مجموع بدهکار و بستانکار کل فایل و مقایسه با تراز کل سیستم مبدأ."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="استراتژی و متدولوژی تبدیل داده از سایر نرم‌افزارهای ERP",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="python",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_cheque_management(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "چک‌ها در سپهریار در دو جدول مجزا مدیریت می‌شوند: `[Check]` برای اسناد دریافتنی مشتریان "
            "و `CheckPardakht` برای اسناد پرداختنی شرکت. هر چک دارای چرخه عمر وضعیتی (`State`) از ۰ تا ۳ است."
        )
        gotchas = [
            "کدهای وضعیت State: ۰=نزد صندوق، ۱=پاس/وصول شده، ۲=برگشتی/واخواست، ۳=در جریان وصول بانکی.",
            "ارتباط با طرف حساب: ستون `PersonId` در جدول چک‌ها به `TblPerson.Sh_ozviat` وصل است.",
            "سامانه صیاد: در چک‌های پرداختی جدید، شناسه ۱۶ رقمی صیاد در ستون `SayadNum` ذخیره می‌شود."
        ]
        sql = """
-- استخراج چک‌های نیازمند پیگیری با وضعیت و طرف حساب
SELECT 
    c.Id AS [شناسه چک],
    c.serial AS [شماره چک],
    c.mab AS [مبلغ ریال],
    c.DateChek AS [سررسید],
    c.Bank AS [بانک صادرکننده],
    p.Name AS [صاحب چک],
    p.Mobile AS [موبایل],
    CASE c.State
        WHEN 0 THEN N'نزد صندوق'
        WHEN 2 THEN N'برگشت خورده'
        WHEN 3 THEN N'خوابیده به حساب'
        ELSE N'سایر'
    END AS [وضعیت]
FROM dbo.[Check] c WITH (NOLOCK)
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON c.PersonId = p.Sh_ozviat
WHERE c.State IN (0, 2, 3)
ORDER BY c.DateChek ASC;
        """.strip()

        checklist = [
            "اطمینان از فرمت تاریخ سررسید شمسی (DateChek).",
            "بررسی اتصال چک‌های سررسیدشده به آرتیکل‌های واریز بانک در TR."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="مدیریت اسناد دریافتنی و پرداختنی و وضعیت‌های چک",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_triggers_and_perf(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "سیستم سپهریار در محیط‌های تحت شبکه و سرورهای چندکاربره کار می‌کند. "
            "عملیات حجیم بدون کنترل تریگرها و هینت‌های قفل می‌تواند کل سیستم را متوقف کند."
        )
        gotchas = [
            "تریگر UpdateSiteSync_TR: این تریگر با هر دستور INSERT یا UPDATE روی TR اجرا می‌شود؛ در ورود انبوه باید DISABLE شود.",
            "هینت WITH (NOLOCK): تمام کوئری‌های گزارش‌گیری و خواندن حتماً باید دارای WITH (NOLOCK) باشند تا از Shared Lock و Deadlock با اپراتورها جلوگیری شود.",
            "ایندکس‌های ضروری: اطمینان از وجود ایندکس‌های روی `(Factor, Sodor)` و `(SanadM, Sodor)` جهت سرعت بخشیدن به بازیابی."
        ]
        sql = """
-- الگوی امن اجرای عملیات دسته‌ای در دیتابیس سپهریار بدون ایجاد قفل
BEGIN TRY
    -- ۱. غیرفعال‌سازی تریگرهای سنگین
    IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
        DISABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;

    -- ۲. انجام عملیات Bulk با تراکنش کنترل‌شده

    -- ۳. فعال‌سازی مجدد تریگر
    IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
        ENABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;
END TRY
BEGIN CATCH
    -- تضمین فعال‌سازی تریگر حتی در صورت بروز خطا
    IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
        ENABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;
    THROW;
END CATCH;
        """.strip()

        checklist = [
            "استفاده همیشگی از بلوک TRY...CATCH برای تضمین Re-enable شدن تریگرها.",
            "استفاده انحصاری از WITH (NOLOCK) در کلیه دستورات SELECT."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="مدیریت تریگرها، کارایی تراکنش‌ها و پیشگیری از Deadlock",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_account_definition(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "تعریف حساب در نرم‌افزار حسابداری سپهریار بر اساس ساختار استاندارد ۴ سطحی حسابداری انجام می‌شود:\n"
            "**گروه حساب ➔ حساب کل (۳ رقمی) ➔ حساب معین (۱ تا ۳ رقمی) ➔ حساب تفصیلی (۱ تا ۶ رقمی)**.\n\n"
            "برای تعریف و فعال‌سازی حساب در سپهریار، دو مسیر وجود دارد:\n"
            "**۱. از طریق رابط کاربری نرم‌افزار (UI):**\n"
            "• **تعریف سرفصل کل و معین:** از منوی اصلی «حسابداری» ➔ «کدینگ حساب‌ها / سرفصل‌ها». ابتدا گروه (دارایی‌ها، بدهی‌ها، سرمایه، درآمد، هزینه) را انتخاب کرده، سپس حساب کل ۳ رقمی (مثلاً ۱۰۰ برای موجودی نقد و بانک، ۱۱۰ برای بدهکاران تجاری) و معین زیرمجموعه (مثلاً معین ۱ برای صندوق، معین ۲ برای بانک‌ها، معین ۱ برای مشتریان) را ثبت نمایید.\n"
            "• **تعریف طرف‌حساب و اشخاص تفصیلی:** از منوی «تعاریف» ➔ «اشخاص و طرف‌حساب‌ها» (کلید میانبر F2 جهت ایجاد جدید). نام شخص/شرکت، شماره موبایل و کد ملی را وارد کرده و نوع طرف‌حساب (Type) را انتخاب و به معین مربوطه متصل کنید.\n"
            "• **تعریف حساب بانکی و پوز:** از منوی «عملیات ویژه» ➔ «تعریف حساب جهت دریافت از بانک / تنظیمات فایل بانک» جهت تعریف شماره حساب، نام بانک، شعبه و اتصال به سرفصل معین ۱۰۰/۲.\n\n"
            "**۲. از طریق پایگاه داده و اسکریپت‌نویسی (SQL):**\n"
            "ایجاد حساب نیازمند ثبت همزمان در مثلث طلایی جداول زیر است:\n"
            "۱. `TblPerson`: اطلاعات هویتی و نوع حساب (Type)\n"
            "۲. `Master`: رکورد سرآمد مانده‌ها و ارتباط درختی (HSB و personcod)\n"
            "۳. `TblHesabText`: ثبت عنوان متنی سرفصل و تفصیلی"
        )
        gotchas = [
            "تله حیاتی Master.personcod: در جدول Master حتماً باید فیلد personcod برابر با Sh_ozviat شخص در TblPerson مقداردهی شود؛ در غیر این صورت حساب در درختواره طرف‌حساب‌ها و گزارشات نرم‌افزار ناپدید می‌گردد.",
            "تنظیم دقیق فیلد Type در TblPerson: مشتریان=1، تأمین‌کنندگان/فروشندگان=2، پرسنل=3، حساب‌های بانکی=4، صندوق‌ها=5. مقدار اشتباه باعث اختلال در فرم صدور فاکتور و وصول چک می‌شود.",
            "ثبت همزمان در TblHesabText: عنوان فارسی شخص/حساب باید با مقادیر (Srfsl, Moin, HSB) در جدول TblHesabText درج شود تا در گریدها و چاپ فاکتور نام حساب سفید نمایش داده نشود.",
            "کدینگ استاندارد معین: مشتریان تجاری حتماً در سرفصل کل 110 و معین 1، و بانک‌ها در سرفصل کل 100 و معین 2 درج شوند.",
            "جداسازی شماره موبایل: متن نام نباید حاوی شماره تماس باشد؛ موبایل حتماً در فیلد مستقل Mobile قرار گیرد."
        ]
        sql = """
-- الگوی تراکنشی و استاندارد تعریف حساب و تفصیلی در سپهریار
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @ShOzviat INT = 2005;        -- کد عضویت یکتا در پرونده اشخاص
    DECLARE @Srfsl INT = 110;           -- کد سرفصل کل (110 بدهکاران تجاری / 100 نقد و بانک)
    DECLARE @Moin INT = 1;              -- کد معین (1 مشتریان / 2 بانک‌ها)
    DECLARE @HSB INT = 2005;            -- کد تفصیلی حساب (معمولاً برابر با کد عضویت)
    DECLARE @Name NVARCHAR(100) = N'شرکت بازرگانی سپهر آریا';
    DECLARE @Mobile VARCHAR(20) = '09121234567';
    DECLARE @Type INT = 1;              -- 1=مشتری، 2=فروشنده، 4=بانک

    -- ۱. درج پرونده پایه در TblPerson
    INSERT INTO dbo.TblPerson (Sh_ozviat, Name, Tell, Mobile, Srfsl, Moin, Hesab, Type, Status)
    VALUES (@ShOzviat, @Name, '', @Mobile, @Srfsl, @Moin, @HSB, @Type, 1);

    -- ۲. درج در جدول Master و اتصال کلیدی personcod
    INSERT INTO dbo.Master (Srfsl, Moin, HSB, Bed, Bes, sodur, personcod, Masdood)
    VALUES (@Srfsl, @Moin, @HSB, 0, 0, 1, @ShOzviat, 0);

    -- ۳. ثبت عنوان در جدول عناوین حساب‌ها
    INSERT INTO dbo.TblHesabText (Srfsl, Moin, HSB, Text)
    VALUES (@Srfsl, @Moin, @HSB, @Name);

    COMMIT TRANSACTION;
    PRINT 'حساب با موفقیت در کدینگ و دفتر تفصیلی سپهریار تعریف و بالانس شد.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
        """.strip()

        checklist = [
            "تطابق کدهای Srfsl و Moin با ساختار کدینگ فعال سیستم.",
            "بررسی یکتایی Sh_ozviat در TblPerson و HSB در Master.",
            "اعتبارسنجی فیلد Type متناسب با ماهیت شخص (مشتری/فروشنده/بانک).",
            "اطمینان از برابری فیلد Master.personcod با TblPerson.Sh_ozviat.",
            "ثبت نام فارسی در TblHesabText با HSB متناظر."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="نحوه تعریف حساب و ساختار کدینگ در سپهریار (از محیط کاربری تا پایگاه داده)",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_coding_structure(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "سپهریار از سیستم کدینگ ۴ سطحی حسابداری استفاده می‌کند: "
            "گروه ➔ حساب کل (۳ رقمی) ➔ حساب معین (۱ تا ۳ رقمی) ➔ حساب تفصیلی (۱ تا ۶ رقمی)."
        )
        gotchas = [
            "سرفصل ۱۰۰: موجودی نقد و بانک (معین ۱: صندوق، معین ۲: بانک‌ها).",
            "سرفصل ۱۱۰: حساب‌های دریافتنی تجاری / مشتریان (معین ۱: مشتریان داخلی).",
            "سرفصل ۲۰۱: حساب‌های پرداختنی تجاری / تأمین‌کنندگان.",
            "سرفصل ۳۵۰: سود و زیان انباشته.",
            "سرفصل ۴۰۰: سرمایه اولیه و حقوق صاحبان سهام."
        ]
        sql = """
-- استخراج تراز کل و معین به تفکیک ساختار استاندارد کدینگ
SELECT 
    m.Srfsl AS [کد کل],
    m.Moin AS [کد معین],
    h.Text AS [عنوان سرفصل],
    SUM(m.Bed) AS [گردش بدهکار],
    SUM(m.Bes) AS [گردش بستانکار],
    (SUM(m.Bed) - SUM(m.Bes)) AS [مانده نهایی]
FROM dbo.Master m WITH (NOLOCK)
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON m.Srfsl = h.Srfsl AND m.Moin = h.Moin AND m.HSB = 0
GROUP BY m.Srfsl, m.Moin, h.Text
ORDER BY m.Srfsl, m.Moin;
        """.strip()

        checklist = [
            "تطابق سطوح کل و معین با استانداردهای گزارشگری مالیاتی و حسابداری.",
            "اطمینان از وجود عنوان سرفصل در TblHesabText برای تفصیلی ۰."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="ساختار استاندارد سطوح کدینگ حسابداری در سپهریار",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def _reason_inventory_and_goods(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            "در سپهریار، مشخصات کالاها و خدمات در جدول `TblKala` با کلید اصلی `Idkala` نگهداری می‌شود. "
            "موجودی انبار و کاردکس از طریق تجمیع رکوردهای تراکنش در جدول `TR` با فیلدهای `(Idkala, TED, IdAnbr)` "
            "محاسبه می‌گردد. همچنین برای سیستم‌های چندبارکده، بارکدهای جانبی در جدول `TblBarCode` متصل به `Idkala` ذخیره می‌شوند."
        )
        gotchas = [
            "عدم تغییر دستی موجودی: ویرایش مستقیم فیلد `Mogodi` در `TblKala` بدون ثبت تراکنش در جدول `TR` (حواله/رسید/فاکتور)، موجب اختلاف میان موجودی ظاهری و کاردکس واقعی انبار خواهد شد.",
            "مدیریت چندبارکدی: برای کالاهایی با چند بارکد مختلف، هرگز نباید کالای تکراری تعریف شود؛ بلکه باید بارکدهای ثانویه در جدول `TblBarCode` ثبت گردند.",
            "ارتباط با انبار: در تراکنش‌های انبارداری و فروش در جدول `TR`، مقداردهی ستون `IdAnbr` (کد انبار) الزامی است.",
            "واحدهای سنجش و ضرایب: نام واحد اصلی در `Vahed` و ضرایب بسته‌بندی در فرآیند تبدیل داده از سایر نرم‌افزارها باید با دقت نگاشت شوند."
        ]
        sql = """
-- الگوی استاندارد بررسی تعداد، موجودی و استخراج کاردکس کالا در سپهریار
SELECT 
    k.Idkala AS [کد کالا],
    k.Name AS [نام کالا],
    k.Vahed AS [واحد],
    k.Mogodi AS [موجودی اولیه/سیستمی],
    ISNULL(SUM(CASE WHEN tr.Factor > 0 THEN -tr.TED ELSE tr.TED END), 0) AS [گردش تراکنش‌ها در TR]
FROM dbo.TblKala k WITH (NOLOCK)
LEFT JOIN dbo.TR tr WITH (NOLOCK) ON k.Idkala = tr.Idkala
GROUP BY k.Idkala, k.Name, k.Vahed, k.Mogodi
ORDER BY k.Idkala;
        """.strip()

        checklist = [
            "اطمینان از یکتا بودن Idkala و عدم درج کدهای منفی یا تکراری.",
            "ثبت بارکدهای تکمیلی در جدول TblBarCode به جای تولید کالای تکراری.",
            "بررسی تخصیص صحیح کد انبار (IdAnbr) در سطرهای تراکنش TR."
        ]

        return SepehryarCognitiveResponse(
            query=query,
            topic="مدیریت کاتالوگ کالاها، انبارداری و کاردکس در TblKala",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    # --------------------------------------------------------------------------
    # Universal Dynamic Cognitive Handlers (CRUD, Schema, Workflows, Diagnostics)
    # --------------------------------------------------------------------------

    @classmethod
    def _extract_action_and_table(cls, q_norm: str) -> tuple[Optional[str], Optional[str], list[str]]:
        action = None
        if any(w in q_norm for w in ["delete", "حذف", "پاک کردن", "پاک کن", "حذف کن", "truncate", "drop", "بردار"]):
            action = "DELETE"
        elif any(w in q_norm for w in ["update", "ویرایش", "بروزرسانی", "اصلاح", "تغییر", "آپدیت", "ست کن"]):
            action = "UPDATE"
        elif any(w in q_norm for w in ["insert", "درج", "ثبت رکورد", "افزودن رکورد", "ایجاد رکورد"]):
            action = "INSERT"
        elif any(w in q_norm for w in ["join", "اتصال بین", "وصل کردن", "جوین", "ارتباط دو جدول"]):
            action = "JOIN"
        elif any(w in q_norm for w in ["ستون", "فیلد", "ساختار", "کلید", "نوع داده", "مشخصات جدول", "columns"]):
            action = "SCHEMA"
        elif any(w in q_norm for w in ["خطا", "ارور", "error", "قفل", "deadlock", "خراب", "دوبل", "ناپدید", "نامتوازن"]):
            action = "TROUBLESHOOT"
        elif any(w in q_norm for w in ["بستن حساب", "سال مالی", "انبارگردانی", "مغایرت بانکی", "راس گیری", "استهلاک", "تایید اسناد", "پایان روز"]):
            action = "WORKFLOW"
        elif any(w in q_norm for w in ["select", "واکشی", "کوئری", "گزارش", "لیست", "نمایش بده", "پیدا کن"]):
            action = "SELECT"

        words = re.findall(r'[a-zA-Z0-9_]+|[\u0600-\u06FF]+', q_norm)
        detected_tables = []

        if "tr" in words or "دفتر روزنامه" in q_norm or "تراکنش" in q_norm or "فاکتور" in q_norm or "اقلام فاکتور" in q_norm or "ریز فاکتور" in q_norm:
            detected_tables.append("TR")
        if "master" in words or "سرآمد" in q_norm or "کدینگ" in q_norm or "مانده حساب" in q_norm:
            detected_tables.append("Master")
        if any(w in words for w in ["person", "tblperson", "اشخاص", "مشتری", "شخص", "طرف حساب", "تامین کننده"]):
            detected_tables.append("TblPerson")
        if any(w in words for w in ["sanad", "tblsanad", "sanadm", "اسناد", "سند", "آرتیکل سند", "سطر سند"]):
            detected_tables.append("TblSanad")
            if "TR" not in detected_tables:
                detected_tables.append("TR")
        if any(w in words for w in ["kala", "tblkala", "کالا", "اجناس"]):
            detected_tables.append("TblKala")
        if any(w in words for w in ["anbar", "tblanbar", "انبار"]):
            detected_tables.append("TblAnbar")
        if any(w in words for w in ["checkpardakht"]) or "چک پرداختنی" in q_norm or "چک صادره" in q_norm:
            detected_tables.append("CheckPardakht")
        if any(w in words for w in ["check", "tblcheck", "چک"]):
            detected_tables.append("Check")
        if any(w in words for w in ["barcode", "tblbarcode", "بارکد"]):
            detected_tables.append("TblBarCode")
        if any(w in words for w in ["param", "tblparam", "سرفصل کل", "سرفصل معین"]):
            detected_tables.append("TblParam")
        if any(w in words for w in ["hesabtext"]) or "عنوان حساب" in q_norm:
            detected_tables.append("TblHesabText")

        target_table = detected_tables[0] if detected_tables else None
        return action, target_table, detected_tables

    @classmethod
    def _reason_dynamic_sql_operation(cls, query: str, action: str, table_name: str, q_norm: str) -> SepehryarCognitiveResponse:
        card = SEPEHRYAR_TABLE_CARDS.get(table_name)
        card_title = card.persian_title if card else table_name

        if action == "DELETE":
            if table_name in ("TR", "TRSub"):
                topic = "اسکریپت و اصول استاندارد حذف ایمن تراکنش‌ها و فاکتور از جدول TR"
                analysis = (
                    "جدول `TR` (دفتر روزنامه تفصیلی و تراکنش‌ها) شریان حیاتی داده‌های مالی و انبارداری در سپهریار است. "
                    "هر رکورد در این جدول نماینده یک سطر از فاکتور خرید/فروش، حواله/رسید انبار یا آرتیکل دفتر روزنامه است. "
                    "حذف مستقیم رکوردهای TR بدون توجه به رکوردهای وابسته در `TRSub` (ریز اقلام فاکتور) و تریگرهای سیستمی "
                    "موجب بروز خطاهای یکپارچگی، رکوردهای یتیم (Orphan) و برهم‌خوردن مانده سرآمد در جدول `Master` می‌گردد."
                )
                gotchas = [
                    "حذف آبشاری اقلام فاکتور: در صورتی که فاکتور دارای ریز کالا یا تخفیف باشد، ابتدا باید رکوردهای متناظر از جدول `TRSub` حذف شوند.",
                    "تریگر همگام‌سازی سایت (`UpdateSiteSync`): این تریگر روی جدول `TR` فعال است. در صورت حذف گروهی، باید تریگر مدیریت شود تا مانع کندی شدید یا قطعی تراکنش نشود.",
                    "تطبیق مانده در Master: پس از حذف رکوردهای بدهکار/بستانکار در TR، مانده حساب طرف‌حساب در `Master` باید کنترل یا همگام گردد.",
                    "اسناد حسابداری متناظر (`TblSanad`): اگر برای فاکتور سند مالی صادر شده باشد، فیلد `SanadM` نشان‌دهنده شماره سند متناظر است که باید تعیین تکلیف شود."
                ]
                sql = """-- اسکریپت استاندارد و تراکنشی حذف ایمن رکوردهای فاکتور و تراکنش از TR
BEGIN TRANSACTION;
BEGIN TRY
    -- مشخص کردن شماره فاکتور یا کد عطف صدور تراکنش
    DECLARE @FactorNo INT = 1052;     -- شماره فاکتور مورد نظر
    DECLARE @Sodor INT = NULL;         -- یا شماره عطف صدور تراکنش تکی (اختیاری)

    -- ۱. حذف ریز اقلام و ردیف‌های فرعی وابسته در TRSub (در صورت وجود جدول اقلام)
    IF OBJECT_ID('dbo.TRSub', 'U') IS NOT NULL
    BEGIN
        DELETE FROM dbo.TRSub
        WHERE Factor = @FactorNo OR (@Sodor IS NOT NULL AND Sodor = @Sodor);
    END;

    -- ۲. حذف رکوردهای اصلی تراکنش در دفتر روزنامه TR
    DELETE FROM dbo.TR
    WHERE Factor = @FactorNo OR (@Sodor IS NOT NULL AND Sodor = @Sodor);

    -- ۳. کنترل تراز مانده در Master
    -- (در صورت غیرفعال بودن تریگرهای اتوماتیک، اجرای کوئری اصلاح مانده توصیه می‌شود)

    COMMIT TRANSACTION;
    PRINT N'رکوردهای تراکنش TR و اقلام وابسته با موفقیت حذف شدند.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
    RAISERROR(N'خطا در فرآیند حذف رکوردهای TR: %s', 16, 1, @ErrMsg);
END CATCH;"""
                checklist = [
                    "تهیه فایل پشتیبان (Backup) سریع از پایگاه داده قبل از اجرای عملیات حذف.",
                    "بررسی وجود رکوردهای وابسته در TRSub و حذف آنها قبل از TR.",
                    "اطمینان از عدم قطعی شدن سند در TblSanad برای این تراکنش.",
                    "کنترل کاردکس کالاهای متصل به این فاکتور در TblKala.",
                    "تطبیق مانده بدهکار/بستانکار طرف‌حساب در جدول Master."
                ]
                return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

            elif table_name in ("TblSanad", "TblSanadD"):
                topic = "اسکریپت و الزامات استاندارد حذف اسناد مالی از TblSanad"
                analysis = (
                    "جدول `TblSanad` سربرگ اسناد حسابداری و جدول `TblSanadD` (یا رکوردهای مرتبط در `TR`) حاوی آرتیکل‌های مالی است. "
                    "حذف سند حسابداری در سپهریار نیازمند رعایت سلسله‌مراتب اسناد رسمی، بالانس ترازنامه و ممانعت از حذف اسناد کلیدی (مانند سند افتتاحیه ۱) است."
                )
                gotchas = [
                    "قفل سند افتتاحیه: سند شماره ۱ (سند افتتاحیه) پایه ترازنامه است و هرگز نباید به صورت دستی حذف گردد.",
                    "حذف سطرهای وابسته: قبل از حذف هدر سند، آرتیکل‌های متناظر با `SanadM` در جداول `TblSanadD` و `TR` باید پاک شوند.",
                    "شکاف در سریال اسناد: پس از حذف سند، فاصله در شماره اسناد ایجاد می‌شود که در حسابداری رسمی نیازمند بازچینی شماره اسناد است."
                ]
                sql = """-- اسکریپت استاندارد و تراکنشی حذف سند حسابداری در سپهریار
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @SanadM INT = 105; -- شماره سند حسابداری مورد نظر

    -- ۱. کنترل امنیتی: سند شماره ۱ (افتتاحیه) نباید حذف شود
    IF @SanadM = 1
    BEGIN
        RAISERROR(N'هشدار امنیتی: سند شماره ۱ (افتتاحیه) پایه سیستم است و امکان حذف آن وجود ندارد!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END;

    -- ۲. حذف سطرهای تفصیلی در TblSanadD (در صورت وجود)
    IF OBJECT_ID('dbo.TblSanadD', 'U') IS NOT NULL
    BEGIN
        DELETE FROM dbo.TblSanadD WHERE SanadM = @SanadM;
    END;

    -- ۳. حذف آرتیکل‌های متناظر در TR
    DELETE FROM dbo.TR WHERE SanadM = @SanadM;

    -- ۴. حذف سربرگ سند در TblSanad
    DELETE FROM dbo.TblSanad WHERE SanadM = @SanadM;

    COMMIT TRANSACTION;
    PRINT N'سند حسابداری و کلیه آرتیکل‌های آن با موفقیت حذف شدند.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
    RAISERROR(N'خطا در حذف سند حسابداری: %s', 16, 1, @ErrMsg);
END CATCH;"""
                checklist = [
                    "بررسی شماره سند و اطمینان از اینکه سند اختتامیه یا افتتاحیه نیست.",
                    "تطبیق تراز کل و معین پس از حذف سند.",
                    "اطمینان از حذف کلیه آرتیکل‌ها در TR و TblSanadD."
                ]
                return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

            elif table_name == "TblPerson":
                topic = "الگوی ایمن حذف و غیرفعال‌سازی اشخاص در TblPerson"
                analysis = (
                    "در پایگاه داده سپهریار، رکوردهای اشخاص (`TblPerson`) از طریق `Sh_ozviat` با رکوردهای گردش در `TR` "
                    "و مانده حساب در `Master.personcod` در ارتباط کلیدی هستند. حذف فیزیکی شخصی که دارای گردش مالی است، "
                    "منجر به نقض یکپارچگی ارجاعی و ناپدید شدن نام طرف‌حساب در گزارشات مالی می‌شود. بهترین شیوه، غیرفعال‌سازی (Soft Delete) است."
                )
                gotchas = [
                    "ممانعت از حذف اشخاص دارای گردش: اگر شخص دارای رکورد در `TR` یا مانده غیرصفر در `Master` باشد، حذف فیزیکی ممنوع است.",
                    "استفاده از فیلد Status: برای بستن حساب یا غیرفعال کردن شخص، مقدار `Status = 0` در جدول `TblPerson` قرار می‌گیرد.",
                    "قطع درختواره حساب‌ها: در صورت حذف فیزیکی شخص، باید رکورد متناظر در `Master` و `TblHesabText` نیز تعیین تکلیف شود."
                ]
                sql = """-- روش ۱: غیرفعال‌سازی استاندارد و ایمن شخص (Soft Delete - توصیه شده)
UPDATE dbo.TblPerson
SET Status = 0
WHERE Sh_ozviat = 2001; -- کد عضویت شخص

-- روش ۲: حذف فیزیکی مشروط (فقط در صورتی که هیچ تراکنش یا گردشی وجود نداشته باشد)
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @ShOzviat INT = 2001;

    IF EXISTS (SELECT 1 FROM dbo.TR WITH (NOLOCK) WHERE Taraf = @ShOzviat)
    BEGIN
        RAISERROR(N'امکان حذف فیزیکی وجود ندارد؛ این شخص دارای تراکنش در دفتر روزنامه (TR) است!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END;

    -- حذف عناوین حساب
    DELETE FROM dbo.TblHesabText WHERE Srfsl = 110 AND Moin = 1 AND HSB = @ShOzviat;
    -- حذف مانده سرآمد
    DELETE FROM dbo.Master WHERE Srfsl = 110 AND Moin = 1 AND HSB = @ShOzviat;
    -- حذف از پرونده اشخاص
    DELETE FROM dbo.TblPerson WHERE Sh_ozviat = @ShOzviat;

    COMMIT TRANSACTION;
    PRINT N'شخص فاقد تراکنش با موفقیت حذف شد.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    THROW;
END CATCH;"""
                checklist = [
                    "بررسی عدم وجود رکوردهای گردش در جدول TR برای این طرف‌حساب.",
                    "کنترل صفر بودن مانده بدهکار و بستانکار در جدول Master.",
                    "ترجیح استفاده از Soft Delete (Status = 0) نسبت به حذف فیزیکی."
                ]
                return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

            elif table_name == "TblKala":
                topic = "اسکریپت و الزامات حذف و غیرفعال‌سازی کالا در TblKala"
                analysis = (
                    "کالاها در سپهریار با شناسه `IDKala` به کاردکس انبار و سطرهای فاکتور در `TR` و بارکدها در `TblBarcode` متصل هستند. "
                    "حذف کالایی که در سال جاری یا دوره‌های گذشته فاکتور خرید/فروش یا حواله انبار داشته باشد، کاردکس را مخدوش می‌کند."
                )
                gotchas = [
                    "کنترل گردش انبار: قبل از حذف کالا، باید اطمینان حاصل شود که هیچ ردیف فاکتور یا حواله‌ای در `TR` برای `IDKala` وجود ندارد.",
                    "حذف بارکدهای اقماری: در صورت حذف فیزیکی، بارکدهای متناظر در `TblBarcode` نیز باید حذف شوند.",
                    "غیرفعال‌سازی کالا: روش مطمئن‌تر، تنظیم فیلد وضعیت کالا جهت عدم نمایش در فرم‌های فروش است."
                ]
                sql = """-- روش استاندارد حذف کالا مشروط به عدم وجود کاردکس
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @IDKala INT = 101001; -- کد کالای مورد نظر

    IF EXISTS (SELECT 1 FROM dbo.TR WITH (NOLOCK) WHERE Idkala = @IDKala)
    BEGIN
        RAISERROR(N'کالا دارای گردش در دفتر روزنامه و کاردکس انبار است و حذف فیزیکی آن مجاز نیست!', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END;

    -- ۱. حذف بارکدهای فرعی متصل
    IF OBJECT_ID('dbo.TblBarcode', 'U') IS NOT NULL
        DELETE FROM dbo.TblBarcode WHERE IDKala = @IDKala;

    -- ۲. حذف کالا از کاتالوگ اصلی
    DELETE FROM dbo.TblKala WHERE IDKala = @IDKala;

    COMMIT TRANSACTION;
    PRINT N'کالا و بارکدهای وابسته با موفقیت حذف شدند.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    THROW;
END CATCH;"""
                checklist = [
                    "اطمینان از صفر بودن موجودی لحظه‌ای (Mande = 0).",
                    "عدم وجود هرگونه سابقه در TR (حواله، رسید، فاکتور).",
                    "حذف بارکدهای متناظر در TblBarcode."
                ]
                return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

            else:
                # Generic DELETE on other tables
                pk_col = card.primary_keys[0] if card and card.primary_keys else "ID"
                topic = f"اسکریپت و ملاحظات حذف رکورد از جدول {table_name} ({card_title})"
                analysis = f"عملیات حذف در جدول `{table_name}` باید با کنترل کلیدهای وابسته و در قالب یک بلوک تراکنشی ایمن انجام پذیرد."
                gotchas = [
                    f"کلید اصلی جدول: `{pk_col}` می‌باشد.",
                    "تهیه پشتیبان قبل از اعمال دستورات DML الزامی است.",
                    "همیشه دستور DELETE باید مقید به شرط WHERE دقیق باشد."
                ]
                sql = f"""-- الگوی تراکنشی حذف رکورد از جدول {table_name}
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @TargetKey INT = 1001; -- مقدار کلید رکوردی که باید حذف شود

    DELETE FROM dbo.{table_name}
    WHERE {pk_col} = @TargetKey;

    COMMIT TRANSACTION;
    PRINT N'رکورد با موفقیت از {table_name} حذف گردید.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    THROW;
END CATCH;"""
                checklist = [
                    f"کنترل مقدار کلید {pk_col} قبل از اجرا.",
                    "بررسی رکوردهای وابسته در سایر جداول."
                ]
                return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        elif action == "UPDATE":
            pk_col = card.primary_keys[0] if card and card.primary_keys else "ID"
            topic = f"اسکریپت استاندارد ویرایش و بروزرسانی داده در جدول {table_name} ({card_title})"
            analysis = (
                f"ویرایش رکوردهای جدول `{table_name}` در سپهریار باید با رعایت نوع داده‌ها، "
                "قفل‌های همزمانی و حفظ توازن مقادیر مرتبط در سایر جداول صورت پذیرد."
            )
            gotchas = [
                "همیشه فیلتر WHERE مقید به کلید اصلی برای جلوگیری از بروزرسانی تصادفی کل جدول الزامی است.",
                "در صورت ویرایش مبالغ مالی یا موجودی کالا، تراز و کاردکس باید بازبینی شوند.",
                "در جداول دارای تریگر، تاثیر تریگرهای AFTER UPDATE باید لحاظ گردد."
            ]
            vital_cols = card.vital_columns[:3] if card else ["Status"]
            set_clauses = "\n        ".join([f"{col} = @New_{col}," for col in vital_cols[:-1]])
            if vital_cols:
                set_clauses += f"\n        {vital_cols[-1]} = @New_{vital_cols[-1]}"
            else:
                set_clauses = "Status = 1"

            sql = f"""-- الگوی استاندارد و تراکنشی ویرایش رکورد در {table_name}
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @TargetKey INT = 1001;
    DECLARE @New_Value NVARCHAR(100) = N'مقدار جدید';

    UPDATE dbo.{table_name}
    SET 
        {set_clauses}
    WHERE {pk_col} = @TargetKey;

    COMMIT TRANSACTION;
    PRINT N'بروزرسانی جدول {table_name} با موفقیت انجام شد.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    THROW;
END CATCH;"""
            checklist = [
                f"اطمینان از وجود رکورد با کلید {pk_col}.",
                "بررسی عدم ایجاد تناقض در سایر جداول مرتبط."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        else:
            # Default / SELECT on table
            topic = f"کوئری استاندارد و بهینه واکشی داده از جدول {table_name} ({card_title})"
            analysis = f"جدول `{table_name}` یکی از ساختارهای کلیدی در دسته‌بندی `{card.category if card else 'عمومی'}` سپهریار است."
            gotchas = [
                "استفاده از هینت WITH (NOLOCK) برای ممانعت از ایجاد قفل در دیتابیس عملیاتی.",
                "محدود کردن تعداد ردیف‌ها با TOP برای حفظ کارایی حافظه سرور."
            ]
            cols = ", ".join(card.vital_columns[:8]) if card else "*"
            sql = f"""-- کوئری استاندارد واکشی رکوردهای {table_name} با رعایت NOLOCK
SELECT TOP (100)
    {cols}
FROM dbo.{table_name} WITH (NOLOCK)
ORDER BY 1 DESC;"""
            checklist = [
                "استفاده از ایندکس مناسب در صورت اضافه کردن شرط WHERE.",
                "کنترل زمان پاسخگویی کوئری روی دیتابیس زنده."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

    @classmethod
    def _reason_schema_and_relations(cls, query: str, target_table: Optional[str], detected_tables: list[str], q_norm: str) -> SepehryarCognitiveResponse:
        # 1. Multi-table JOIN resolution
        if len(detected_tables) >= 2 or "join" in q_norm or "اتصال" in q_norm:
            t1 = detected_tables[0] if len(detected_tables) >= 1 else "TR"
            t2 = detected_tables[1] if len(detected_tables) >= 2 else "TblPerson"

            path = schema_graph.find_join_path(t1, t2)
            topic = f"مسیر ارتباطی و نحوه JOIN بین جدول {t1} و {t2} در سپهریار"
            analysis = (
                f"ارتباط بین جدول `{t1}` و `{t2}` در ساختار داده‌ای سپهریار بر اساس کلیدهای منطقی و رابطه‌ای زیر برقرار است. "
                "برای استخراج گزارشات ترکیبی و بدون ایجاد ضرب دکارتی (Cartesian Product)، مسیر بهینه استخراج گردید."
            )
            gotchas = [
                "رعایت همیشه هینت WITH (NOLOCK) در تمام جداول درون JOIN.",
                "استفاده از LEFT JOIN در صورت احتمال عدم وجود رکورد نظیر در جدول فرعی.",
                "انتخاب فیلدهای مورد نیاز به جای * برای سرعت بهینه."
            ]

            select_fields = ["t1.*", "t2.*"]
            join_sql = schema_graph.build_joined_report_query(
                tables=[t1, t2],
                select_fields=[f"{t1}.*", f"{t2}.*"],
                top_limit=50
            )

            checklist = [
                f"تطابق کلیدهای اتصال بین {t1} و {t2}.",
                "بررسی ایندکس بودن ستون‌های شرط JOIN."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, join_sql, "sql", checklist, [])

        # 2. Single table schema inspection
        table_name = target_table or "TR"
        card = SEPEHRYAR_TABLE_CARDS.get(table_name)
        topic = f"ساختار، ستون‌ها و کلیدهای جدول {table_name} ({card.persian_title if card else ''})"
        analysis = (
            f"جدول `{table_name}` در سپهریار دارای ساختار و فیلدهای کلیدی زیر است. "
            f"توضیحات بیزینس: {card.business_notes if card else 'جدول عملیاتی سپهریار.'}"
        )
        gotchas = [
            f"کلید اصلی (Primary Key): {', '.join(card.primary_keys) if card and card.primary_keys else 'مشخص نشده'}",
            f"ستون‌های دارای ایندکس: {', '.join(card.indexed_columns) if card and card.indexed_columns else 'ایندکس پیش‌فرض'}",
            "رعایت هینت WITH (NOLOCK) در پرس‌وجوها."
        ]
        vital_cols_str = ", ".join(card.vital_columns) if card else "*"
        sql = f"""-- استخراج ساختار و ۱۰ رکورد اول جدول {table_name}
SELECT TOP (10)
    {vital_cols_str}
FROM dbo.{table_name} WITH (NOLOCK);"""

        checklist = [
            "تطابق نام فیلدها با نسخه فعال دیتابیس.",
            "بررسی وابستگی‌های Foreign Key قبل از اعمال تغییرات."
        ]
        return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

    @classmethod
    def _reason_workflow_guidance(cls, query: str, q_norm: str) -> SepehryarCognitiveResponse:
        hits = knowledge_search_engine.search(query, limit=3)
        top_snippet = hits[0].snippet if hits else "فرآیندهای مالی و انبارداری در منوهای اختصاصی سپهریار پیاده‌سازی شده‌اند."

        if any(w in q_norm for w in ["انبار", "انبارگردانی", "کسری", "اضافی"]):
            topic = "راهنمای جامع فرآیند انبارگردانی و مدیریت کاردکس در سپهریار"
            analysis = (
                "در نرم‌افزار سپهریار، مدیریت انبارداری شامل دو بخش اصلی است: نخست «تعریف انبار و کالا» (با میان‌بر Ctrl+K) "
                "و سپس عملیات ورود و خروج کالا شامل رسید انبار، حواله خروج، جابجایی کالا بین انبارها و ثبت مغایرت انبارگردانی. "
                "تمامی خروجی‌ها و ورودی‌ها در جدول `TR` با کدهای انبار (`IdAnbr`) و تعداد (`TED`) ثبت و در کاردکس درج می‌شوند."
            )
            gotchas = [
                "تنظیم انبارداری دائمی: در فرم تعریف انبار، فیلد «تعیین حساب موجودی کالا» تنها در صورت فعال بودن انبارداری دائمی مجاز است.",
                "کنترل منفی شدن موجودی: در تب تنظیمات کالا می‌توان صدور فاکتور در شرایط موجودی منفی را مسدود یا مجاز کرد.",
                "ثبت مغایرت انبارگردانی: کسری یا اضافی انبارگردانی باید از طریق فرم رسید/حواله انبارگردانی ثبت شود تا با کاردکس تراز شود."
            ]
            sql = """-- کوئری استخراج گزارش موجودی و کسری/اضافی انبار در سپهریار
SELECT 
    k.IDKala AS [کد کالا],
    k.Name AS [نام کالا],
    k.Mande AS [موجودی لحظه‌ای کاردکس],
    ISNULL(SUM(CASE WHEN tr.Bed > 0 THEN tr.TED ELSE 0 END), 0) AS [ورود به انبار],
    ISNULL(SUM(CASE WHEN tr.Bes > 0 THEN tr.TED ELSE 0 END), 0) AS [خروج از انبار]
FROM dbo.TblKala k WITH (NOLOCK)
LEFT JOIN dbo.TR tr WITH (NOLOCK) ON k.IDKala = tr.Idkala
GROUP BY k.IDKala, k.Name, k.Mande
ORDER BY k.Name;"""
            checklist = [
                "ثبت تمامی فاکتورها و حواله‌های معوق قبل از شروع انبارگردانی.",
                "شمارش فیزیکی اقلام و تطبیق با ستون Mande در TblKala.",
                "صدور حواله کسری انبار یا رسید اضافی انبار جهت تراز صفر."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        elif any(w in q_norm for w in ["بستن حساب", "سال مالی", "اختتامیه"]):
            topic = "دستورالعمل بستن حساب‌های موقت، سند اختتامیه و افتتاح سال مالی جدید"
            analysis = (
                "فرآیند پایان سال مالی در سپهریار شامل ۳ گام اصلی است: "
                "۱) بستن حساب‌های موقت (سود و زیانی شامل درآمدها و هزینه‌ها) به حساب سود و زیان انباشته (سرفصل ۳۵۰). "
                "۲) صدور سند اختتامیه برای صفر کردن حساب‌های ترازنامه‌ای (دارایی‌ها و بدهی‌ها). "
                "۳) ایجاد دوره مالی جدید در جدول `TblDoreMali` و صدور خودکار سند افتتاحیه (سند شماره ۱)."
            )
            gotchas = [
                "تراز بودن سند افتتاحیه: در سند افتتاحیه جمع Bed و جمع Bes باید دقیقاً برابر باشند.",
                "مانده حساب‌های اشخاص: تمام مانده‌ها در سرفصل‌های ۱۱۰ و ۲۰۱ باید همراه با personcod یکتا به دوره جدید منتقل شوند.",
                "حفظ موجودی کالا: مانده انبار از طریق موجودی فیلد Mande کالا به عنوان موجودی اول دوره جدید ثبت می‌گردد."
            ]
            sql = """-- بررسی تراز حساب‌های موقت (هزینه‌ها و درآمدها) قبل از بستن سال مالی
SELECT 
    m.Srfsl AS [کد کل],
    m.Moin AS [کد معین],
    h.Text AS [عنوان سرفصل],
    SUM(m.Bed) AS [جمع بدهکار],
    SUM(m.Bes) AS [جمع بستانکار],
    (SUM(m.Bed) - SUM(m.Bes)) AS [مانده سود/زیانی]
FROM dbo.Master m WITH (NOLOCK)
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON m.Srfsl = h.Srfsl AND m.Moin = h.Moin AND m.HSB = 0
WHERE m.Srfsl >= 500 -- سرفصل‌های درآمد و هزینه
GROUP BY m.Srfsl, m.Moin, h.Text
ORDER BY m.Srfsl;"""
            checklist = [
                "کنترل عدم وجود سند پیش‌نویس یا تأیید نشده در باجه ثبت اسناد.",
                "ثبت استهلاک دارایی‌ها و ذخیره مالیات قبل از بستن حسابها.",
                "صدور سند اختتامیه و تراز بودن کامل سند افتتاحیه سال جدید."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        elif any(w in q_norm for w in ["مغایرت", "بانک"]):
            topic = "فرآیند مغایرت‌گیری اطلاعات بانک و شرکت در منوی عملیات ویژه سپهریار"
            analysis = (
                "در منوی «عملیات ویژه» سپهریار، فرم «مغایرت‌گیری اطلاعات بانک» امکان مقایسه گردش حساب بانک در دفاتر شرکت "
                "(سرفصل ۱۰۰ معین ۲) با فایل تراکنش‌های دریافتی از بانک (اکسل/متنی) را فراهم می‌آورد. سیستم اقلام باز را با کدگذاری رنگی تفکیک می‌کند."
            )
            gotchas = [
                "تعریف حساب بانکی: حساب بانک در TblPerson حتماً باید با Type=4 تعریف شده باشد.",
                "فرمت فایل بانک: تطابق فیلدهای تاریخ، شماره پیگیری و مبلغ واریز/برداشت با ستون‌های فرمت بانک الزامی است.",
                "اقلام باز: مواردی مانند واریزی‌های شناسایی‌نشده یا چک‌های صادره پاس‌نشده باید در صورت مغایرت باقی بمانند."
            ]
            sql = """-- استخراج گردش دفتر بانک شرکت جهت مقایسه با صورتحساب بانکی
SELECT 
    tr.DateR AS [تاریخ تراکنش],
    tr.Serial AS [شماره سند/پیگیری],
    tr.Sharh AS [شرح تراکنش],
    tr.Bed AS [واریز به بانک],
    tr.Bes AS [برداشت از بانک]
FROM dbo.TR tr WITH (NOLOCK)
WHERE tr.Srfsl = 100 AND tr.Moin = 2 -- موجودی بانک‌ها
ORDER BY tr.DateR DESC, tr.Sodor DESC;"""
            checklist = [
                "تنظیم فایل اکسل بانک متناسب با ساختار ورودی سپهریار.",
                "تطابق مانده نهایی دفتر بانک با مانده صورتحساب بانکی پس از کسر اقلام باز."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        else:
            topic = "راهنمای عملیات سیستم و مستندات رسمی سپهریار"
            analysis = top_snippet
            gotchas = [
                "کلیه عملیات ویژه (مانند باجه ثبت سند و مغایرت‌گیری) نیازمند تایید سرپرست مالی است.",
                "استفاده از کلید F10 برای جستجوی سریع اسناد و F5 برای ثبت نهایی فرم‌ها."
            ]
            sql = "-- کوئری استخراج خلاصه وضعیت سیستم\nSELECT COUNT(*) AS [تعداد اسناد] FROM dbo.TblSanad WITH (NOLOCK);"
            checklist = ["بررسی رویداد مالی منطبق بر مدارک مثبته."]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

    @classmethod
    def _reason_troubleshooting(cls, query: str, target_table: Optional[str], q_norm: str) -> SepehryarCognitiveResponse:
        if any(w in q_norm for w in ["deadlock", "قفل", "کند"]):
            topic = "عیب‌یابی خطای Deadlock و قفل شدن جداول هنگام ثبت سند و فاکتور"
            analysis = (
                "خطای Deadlock در سپهریار زمانی رخ می‌دهد که دو پروسس همزمان سعی در بروزرسانی جداول مرتبط "
                "(مانند `TR` و `Master`) داشته باشند در حالی که کوئری‌های گزارش‌گیری طولانی قفل مشترک (Shared Lock) نگه داشته‌اند. "
                "همچنین تریگر `UpdateSiteSync` می‌تواند زمان تراکنش را افزایش داده و ریسک بن‌بست را بالا ببرد."
            )
            gotchas = [
                "استفاده همیشگی از WITH (NOLOCK) در تمام گزارشات و واکشی‌های نرم‌افزار.",
                "کوتاه نگه داشتن زمان تراکنش‌ها (کوتاه کردن فاصله بین BEGIN TRAN و COMMIT).",
                "ترتیب یکسان دسترسی به جداول در کوئری‌ها (ابتدا TblPerson، سپس Master، سپس TR)."
            ]
            sql = """-- کوئری شناسایی پروسس‌های مسدودکننده (Blocking SPIDs) در SQL Server
SELECT 
    blocking_session_id AS [شناسه مسدودکننده (Blocker)],
    session_id AS [شناسه متوقف‌شده (Blocked)],
    wait_type AS [نوع انتظار],
    wait_time AS [مدت انتظار (ms)],
    wait_resource AS [منبع درگیر]
FROM sys.dm_exec_requests
WHERE blocking_session_id <> 0;"""
            checklist = [
                "بررسی وضعیت فعال بودن هینت NOLOCK در گزارشات استیمول‌سافت.",
                "بررسی لاگ‌های Deadlock در SQL Server Error Log."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        elif any(w in q_norm for w in ["تراز", "نامتوازن", "نامتعادل"]):
            topic = "عیب‌یابی و رفع خطای عدم تراز سند حسابداری در سپهریار"
            analysis = (
                "عدم تراز در سند حسابداری به این معناست که جمع بدهکار (`Bed`) با جمع بستانکار (`Bes`) "
                "در آرتیکل‌های یک سند مالی در `TblSanad` یا `TR` اختلاف دارد. این مسئله مانع از صدور سند قطعی و بستن سال مالی می‌شود."
            )
            gotchas = [
                "تطابق Bed و Bes در هر سند به صورت مجزا الزامی است.",
                "اسناد ایجاد شده توسط ابزارهای تبدیل داده باید قبل از تایید نهایی بالانس شوند.",
                "سند افتتاحیه (SanadM = 1) باید بدون کوچکترین ریال اختلاف تراز باشد."
            ]
            sql = """-- کوئری شناسایی اسناد حسابداری نامتوازن (فاقد تراز بدهکار و بستانکار)
SELECT 
    tr.SanadM AS [شماره سند],
    SUM(tr.Bed) AS [جمع بدهکار],
    SUM(tr.Bes) AS [جمع بستانکار],
    (SUM(tr.Bed) - SUM(tr.Bes)) AS [میزان اختلاف تراز]
FROM dbo.TR tr WITH (NOLOCK)
WHERE tr.SanadM > 0
GROUP BY tr.SanadM
HAVING (SUM(tr.Bed) - SUM(tr.Bes)) <> 0
ORDER BY tr.SanadM;"""
            checklist = [
                "اصلاح مبالغ آرتیکل‌های نامتعادل با ثبت ردیف بالانس‌کننده.",
                "کنترل مجدد تراز ۴ ستونی و ۸ ستونی دفتر کل."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        else:
            # Generic troubleshooting
            topic = "راهکار عیب‌یابی و تضمین سلامت پایگاه داده سپهریار"
            analysis = (
                f"برای رفع مشکل گزارش‌شده در «{query}»، ساختار رکوردهای کلیدی در جداول Master، TblPerson و TR "
                "از نظر کلیدهای یکتا، سلامت شاخص‌ها و عدم وجود رکوردهای ناقص (Orphan) بررسی می‌گردد."
            )
            gotchas = [
                "بررسی رکوردهای فاقد personcod در جدول Master.",
                "اطمینان از یکتایی کلیدهای Sh_ozviat در TblPerson."
            ]
            sql = """-- بررسی سلامت کلیدها و رکوردهای یتیم در سیستم
SELECT 
    m.Srfsl, m.Moin, m.HSB, m.personcod
FROM dbo.Master m WITH (NOLOCK)
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON m.personcod = p.Sh_ozviat
WHERE m.personcod > 0 AND p.Sh_ozviat IS NULL;"""
            checklist = [
                "رفع رکوردهای فاقد طرف‌حساب متناظر.",
                "تهیه بک‌آپ قبل از اجرای اسکریپت‌های اصلاحی."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

    @classmethod
    def _reason_dynamic_synthesis(cls, query: str, q_norm: str) -> SepehryarCognitiveResponse:
        # Search knowledge base including manuals
        hits = knowledge_search_engine.search(query, limit=2)
        if hits and hits[0].score > 0.04:
            hit = hits[0]
            topic = f"پاسخ هوشمند معماری و مستندات سپهریار: {hit.heading or hit.doc_title}"
            analysis = hit.snippet
            gotchas = [
                f"استناد از مستند رسمی: «{hit.doc_title}».",
                "رعایت استانداردهای تراکنشی و قفل‌گذاری در تعامل با داده‌های این بخش.",
                "استفاده از هینت WITH (NOLOCK) در کلیه استعلام‌های مرتبط."
            ]
            sql = """-- کوئری نمونه جهت استخراج داده‌های مرتبط با این موضوع
SELECT TOP (50) * 
FROM dbo.TR WITH (NOLOCK)
ORDER BY DateR DESC;"""
            checklist = [
                "تطابق رویداد با استاندارد حسابداری و رویه جاری شرکت.",
                "کنترل صحت ثبت‌ها از طریق باجه ثبت سند (F10)."
            ]
            return SepehryarCognitiveResponse(query, topic, analysis, gotchas, sql, "sql", checklist, [])

        return cls._reason_general_architecture(query)

    @classmethod
    def _reason_general_architecture(cls, query: str) -> SepehryarCognitiveResponse:
        analysis = (
            f"پرسش شما در ارتباط با «{query}» در ساختار هسته پایگاه داده سپهریار مورد تحلیل قرار گرفت. "
            "تمامی تعاملات برنامه‌نویسی با سپهریار باید با حفظ یکپارچگی سه‌گانه TblPerson، Master و TR "
            "و رعایت تریگرهای فعال و قفل‌های همزمانی صورت پذیرد."
        )
        gotchas = [
            "رعایت همیشه هینت WITH (NOLOCK) در پرس‌وجوها.",
            "حفظ انطباق کامل کلیدهای personcod با Sh_ozviat.",
            "عدم حذف مستقیم رکوردهای TR بدون در نظر گرفتن تراز TblSanad."
        ]
        sql = """-- بررسی وضعیت رکوردهای کلیدی سیستم
SELECT 
    (SELECT COUNT(*) FROM dbo.Master WITH (NOLOCK)) AS [تعداد کل حساب‌ها],
    (SELECT COUNT(*) FROM dbo.TblPerson WITH (NOLOCK)) AS [تعداد کل اشخاص],
    (SELECT COUNT(*) FROM dbo.TR WITH (NOLOCK)) AS [تعداد کل تراکنش‌ها];"""
        checklist = [
            "بررسی صحت اتصال ارتباطات ضمنی.",
            "کنترل تراز دوره مالی."
        ]
        return SepehryarCognitiveResponse(
            query=query,
            topic="اصول کلی معماری داده‌ها در سیستم سپهریار",
            analysis=analysis,
            rules_and_gotchas=gotchas,
            solution_script=sql,
            script_language="sql",
            validation_checklist=checklist,
            thinking_steps=[]
        )

    @classmethod
    def generate_script_for_scenario(
        cls,
        scenario: str,
        params: Optional[dict[str, Any]] = None,
        language: str = "sql"
    ) -> dict[str, Any]:
        """
        Synthesizes ready-to-run transactional scripts for specific ERP operations.
        """
        p = params or {}
        sc_norm = scenario.lower().strip()

        if sc_norm in ("create_person", "insert_customer", "person"):
            code = f"""
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @ShOzviat INT = {p.get("sh_ozviat", 2001)};
    DECLARE @HSB INT = {p.get("hsb", 2001)};
    DECLARE @Name NVARCHAR(100) = N'{p.get("name", "نام طرف حساب")}';
    DECLARE @Mobile VARCHAR(20) = '{p.get("mobile", "09120000000")}';
    DECLARE @Type INT = {p.get("type", 1)};
    DECLARE @Srfsl INT = {p.get("srfsl", 110)};
    DECLARE @Moin INT = {p.get("moin", 1)};

    INSERT INTO dbo.TblPerson (Sh_ozviat, Name, Tell, Mobile, Srfsl, Moin, Hesab, Type, Status)
    VALUES (@ShOzviat, @Name, '{p.get("tell", "")}', @Mobile, @Srfsl, @Moin, @HSB, @Type, 1);

    INSERT INTO dbo.Master (Srfsl, Moin, HSB, Bed, Bes, sodur, personcod, Masdood)
    VALUES (@Srfsl, @Moin, @HSB, 0, 0, 1, @ShOzviat, 0);

    INSERT INTO dbo.TblHesabText (Srfsl, Moin, HSB, Text)
    VALUES (@Srfsl, @Moin, @HSB, @Name);

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
            """.strip()

        elif sc_norm in ("create_invoice", "invoice", "sale"):
            code = f"""
BEGIN TRANSACTION;
BEGIN TRY
    DECLARE @Factor INT = {p.get("factor", 101)};
    DECLARE @Taraf INT = {p.get("taraf", 1660)};
    DECLARE @Idkala INT = {p.get("idkala", 101001)};
    DECLARE @TED FLOAT = {p.get("ted", 1.0)};
    DECLARE @Amount BIGINT = {p.get("amount", 1000000)};
    DECLARE @Date VARCHAR(10) = '{p.get("date", "1405/01/15")}';

    INSERT INTO dbo.TR (Sodor, Srfsl, Moin, HSB, DateR, Serial, Sharh, Idkala, Factor, IdAnbr, TED, SanadM, Taraf, Bed, Bes)
    VALUES (
        (SELECT ISNULL(MAX(Sodor), 0) + 1 FROM dbo.TR WITH (NOLOCK)),
        110, 1, @Taraf, @Date, 1, N'فاکتور فروش',
        @Idkala, @Factor, 1, @TED, 0, @Taraf, @Amount, 0
    );

    UPDATE dbo.Master
    SET Bed = Bed + @Amount
    WHERE Srfsl = 110 AND Moin = 1 AND HSB = @Taraf;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
            """.strip()

        elif sc_norm in ("disable_triggers", "trigger_wrapper"):
            code = """
-- الگوی امن مهار تریگر در پردازش‌های دسته‌ای
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
    DISABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;

-- دستورات درج یا به‌روزرسانی دسته‌ای خود را اینجا قرار دهید

IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
    ENABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;
            """.strip()

        else:
            code = "-- سناریوی درخواستی شناخته نشد؛ لطفاً create_person یا create_invoice را مشخص فرمایید."

        return {
            "scenario": scenario,
            "language": language,
            "script": code
        }

    @classmethod
    def lint_dataset(cls, scenario: str, dataset: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Lints proposed dataset against Sepehryar architectural rules before DB execution.
        """
        errors = []
        warnings = []
        recommendations = []

        for idx, row in enumerate(dataset, start=1):
            # Check 1: Phones inside name
            name = str(row.get("name") or row.get("Name") or "")
            if re.search(r'(09\d{9})', name):
                warnings.append(f"ردیف {idx}: شماره موبایل در متن نام شخص ('{name}') قرار دارد؛ باید تفکیک شود.")

            # Check 2: Missing or zero personcod in Master
            if "personcod" in row:
                pc = row.get("personcod")
                if not pc or int(pc) <= 0:
                    errors.append(f"ردیف {idx}: مقدار personcod مقداردهی نشده است (درختواره قطع می‌شود).")

            # Check 3: Polarity negativity
            bed = int(row.get("bed") or row.get("Bed") or 0)
            bes = int(row.get("bes") or row.get("Bes") or 0)
            if bed < 0 or bes < 0:
                errors.append(f"ردیف {idx}: مقادیر منفی در فیلدهای Bed یا Bes در دیتابیس مجاز نیستند.")

            # Check 4: Bank Type
            is_bank = bool(row.get("is_bank") or (row.get("Srfsl") == 100 and row.get("Moin") == 2))
            type_code = row.get("type") or row.get("Type")
            if is_bank and type_code != 4:
                errors.append(f"ردیف {idx}: برای حساب‌های بانکی فیلد Type در TblPerson حتماً باید مقدار ۴ داشته باشد.")

        if len(dataset) > 500:
            recommendations.append("تعداد رکوردها بیش از ۵۰۰ عدد است؛ حتماً تریگر UpdateSiteSync_TR قبل از ورود داده غیرفعال گردد.")

        is_safe = len(errors) == 0

        return {
            "scenario": scenario,
            "total_records": len(dataset),
            "is_safe": is_safe,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations
        }


cognitive_engine = SepehryarCognitiveEngine()
