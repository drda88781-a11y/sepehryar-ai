"""
Comprehensive Pydantic models for database schema representation,
incorporating Sepehryar ERP Persian dictionary annotations.
"""
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

# Persian dictionary for core Sepehryar tables
SEPEHRYAR_TABLE_DICTIONARY: dict[str, str] = {
    "Master": "دفتر کل، معین، تفصیلی و مانده تجمعی حساب‌ها و طرف‌حساب‌ها",
    "TR": "دفتر روزنامه تفصیلی، ریز اسناد مالی، ریز فاکتورها و تراکنش‌های کالا و انبار",
    "TblPerson": "پرونده اشخاص، مشتریان، تأمین‌کنندگان، بانک‌ها و پرسنل",
    "TblSanad": "سربرگ اسناد حسابداری (شماره سند، تاریخ، شرح، نوع سند)",
    "TblParam": "ساختار درختی کدینگ حسابداری (سرفصل کل و معین)",
    "TblHesabText": "عناوین و شرح متنی حساب‌های تفصیلی",
    "TblKala": "کاتالوگ کالاها و خدمات (شناسه، نام، واحدها، موجودی Mande و قیمت Bprice)",
    "TblAnbar": "انبارها و موقعیت‌های نگهداری کالا",
    "TblBarCode": "بارکدهای کالا و واحدهای فرعی",
    "Check": "اسناد دریافتنی (چک‌های عادی و صیادی دریافتی از مشتریان)",
    "CheckPardakht": "اسناد پرداختنی (چک‌های صادره به طرف‌حساب‌ها)",
    "TblBank": "فهرست بانک‌های پایه کشور",
    "TblTypeTR": "انواع تراکنش‌ها، فاکتورهای خرید، فروش، برگشتی و حواله‌ها",
    "TblTypeSanadBank": "انواع رویدادها و عملیات بانکی، پوز و فیش واریزی",
    "TblTarazname": "درخت و ساختار ترازنامه و صورت‌های مالی",
    "TblReports": "تنظیمات و تعاریف گزارش‌های پیشرفته سیستم",
    "TblRptFactor": "قالب‌ها و تعاریف چاپ فاکتورها",
    "PayRol_TblPersonal": "اطلاعات پرسنلی حقوق و دستمزد",
    "PayRol_TblJob": "مشاغل و عناوین شغلی حقوق و دستمزد (۲۰۸۷ ردیف شغل مصوب بیمه)",
    "PayRol_TblGroupItem": "گروه‌بندی اقلام حقوق و دستمزد (عوامل حکمی، مزایا، کسورات)",
    "PayRol_TblItems": "اقلام و فیلدهای محاسباتی حقوق و دستمزد",
    "Payrol_TblTaxGovSetting": "تنظیمات جدول مالیات بر درآمد حقوق مصوب دولت و پلکان‌های معافیت",
    "PayRol_TblHokm": "احکام کارگزینی پرسنل و مبالغ پایه حقوق",
    "PayRol_TblKarkard": "کارکرد ماهانه پرسنل (روز کارکرد، اضافه کار، مرخصی، غیبت)",
    "Bime_Setting": "تنظیمات بیمه تأمین اجتماعی، درصدها (۷٪ سهم کارگر، ۲۳٪ کارفرما) و کدهای کارگاه",
    "Bime_DocType": "انواع مدارک و اسناد ارسالی به سازمان تأمین اجتماعی (دیسکت DSKKAR00 و DSKWOR00)",
    "Vam_Aghsat": "جدول اقساط و زمان‌بندی بازپرداخت وام و تسهیلات و وصولی‌ها",
    "BOM_Header": "سربرگ فرمول ساخت و بهای تمام‌شده تولید (BOM)",
    "SearchHeasab": "ویوی جامع و مرجع تراز ۳ سطحی (کد و نام کل، معین، تفصیلی، مانده و وضعیت بدهکار/بستانکار)",
    "TblDefultHesab": "حساب‌های پیش‌فرض ثبت خودکار سیستم (فروش ۴۰۰، خرید ۵۰۰، چک ۱۱۲، افتتاحیه ۹۰۰)",
    "TblTypeSanad": "انواع سند مالی (۱: معمولی، ۲: افتتاحیه، ۳: اختتامیه، ۴: سود و زیان)",
    "TblStateSanad": "وضعیت‌های سند مالی (۱: عادی، ۲: یادداشت، ۳: تأییدشده، ۴: تأیید نهایی قطعی)",
    "TblCheck_State": "وضعیت‌های چک صیادی (۰: نزد صندوق، ۱: در جریان وصول بانک، ۲: وصول، ۳: برگشتی، ۴: خرج شده)",
    "TblUnit": "واحدهای اصلی سنجش کالا (عدد، کیلو، رول، کارتن، متر، دستگاه و ...)",
    "TblDetailKala": "بارکدها، کدهای فنی و تنوع کالاهای انبار",
    "Day_Factor": "سربرگ فاکتورهای فروش، خدمات و سفارشات روزانه",
    "Day_AvamelFactor": "عوامل کاهنده و افزاینده فاکتور (تخفیف، مالیات ارزش افزوده، کرایه)",
    "TblAvamelTolid": "عوامل و سربار فرمول تولید (BOM) و محاسبه بهای تمام‌شده",
}

# Persian dictionary for common Sepehryar column fields
SEPEHRYAR_COLUMN_DICTIONARY: dict[str, str] = {
    # TblPerson & Person Identity
    "Sh_ozviat": "شناسه یکتا طرف‌حساب / شخص (کلید اصلی TblPerson)",
    "personcod": "شناسه شخص در دفتر کل Master متصل به Sh_ozviat",
    "PersonId": "شناسه شخص صادرکننده یا دریافت‌کننده چک متصل به Sh_ozviat",
    "Taraf": "شناسه طرف‌حساب تراکنش در جدول TR متصل به Sh_ozviat",
    "Name": "نام شخص / عنوان حساب / نام کالا یا انبار",
    "Famil": "نام خانوادگی طرف‌حساب",
    "Sh_sh": "شماره شناسنامه طرف‌حساب یا شماره حساب بانکی",
    "codmeli": "کد ملی شخص یا شناسه ملی شرکت",
    "Cod_Egh": "شماره اقتصادی طرف‌حساب",
    "Tell": "شماره تلفن طرف‌حساب",
    "Mobile": "شماره همراه طرف‌حساب",
    "Addres_mk": "نشانی محل کار",
    "Addres_home": "نشانی منزل",
    "Type": "نوع شخص (۱: مشتری، ۲: تأمین‌کننده، ۳: ویزیتور، ۴: حساب بانکی)",
    "BuyerType": "نوع خریدار (۱: مشتری، ۲: تأمین‌کننده)",
    "Status": "وضعیت فعال یا غیرفعال طرف‌حساب",
    "BlackList": "پرچم لیست سیاه مشتریان بدحساب",
    # Accounting & Ledger
    "Srfsl": "کد سرفصل کل حسابداری",
    "Moin": "کد سرفصل معین حسابداری",
    "HSB": "کد حساب تفصیلی در Master, TR, TblHesabText",
    "Hesab": "کد حساب تفصیلی شخص در TblPerson",
    "Bed": "مبلغ بدهکار (گردش بدهکار در TR و مانده بدهکار در Master)",
    "Bes": "مبلغ بستانکار (گردش بستانکار در TR و مانده بستانکار در Master)",
    "MandeS": "مانده ابتدای دوره حساب در Master",
    "MandeT": "مانده پایان دوره حساب در Master",
    "Sanad": "شماره سند حسابداری (کلید اصلی TblSanad)",
    "SanadM": "شماره سند حسابداری در ردیف تراکنش TR متصل به TblSanad.Sanad",
    "Date": "تاریخ ثبت سند یا تاریخ تراکنش به فرمت شمسی (مثلاً ۱۴۰۵/۰۱/۰۱)",
    "DateR": "تاریخ واقعه مالی یا ثبت سند در TR و Check",
    "Sharh": "شرح سند / شرح ردیف تراکنش / شرح چک",
    "TypeSanad": "نوع سند مالی (۱: معمولی، ۲: افتتاحیه، ۳: اختتامیه، ۴: سود و زیان)",
    "Sodor": "شناسه یکتای ردیف تراکنش در جدول TR (کلید اصلی TR)",
    # Trading & Inventory
    "Factor": "شماره فاکتور خرید یا فروش در جدول TR",
    "GRP": "کد نوع عملیات فاکتور/تراکنش در TR متصل به TblTypeTR.ID",
    "IDKala": "شناسه یکتای کالا در TblKala",
    "Idkala": "شناسه کالا در ردیف تراکنش TR متصل به TblKala.IDKala",
    "IDAnbar": "شناسه انبار در جدول TblKala متصل به TblAnbar.ID",
    "IdAnbr": "شناسه انبار در جدول TR متصل به TblAnbar.ID",
    "Mande": "موجودی آنلاین و لحظه‌ای کالا در TblKala",
    "Bprice": "آخرین نرخ یا قیمت خرید کالا (Base Price)",
    "TED": "تعداد یا مقدار کالا در تراکنش فاکتور TR",
    "Fee": "فی یا نرخ واحد کالا در فاکتور TR",
    "Takh": "مبلغ تخفیف ردیف فاکتور در TR",
    "Mabkh": "مبلغ خالص ردیف فاکتور در TR",
    "BaghaliCode": "کد بارکد اصلی کالا",
    # Cheques & Banking
    "serial": "شماره سریال برگ چک",
    "mab": "مبلغ ریالی چک",
    "DateChek": "تاریخ سررسید چک",
    "DatePas": "تاریخ وصول یا پاس شدن چک",
    "SayadNum": "شناسه یکتای ۱۶ رقمی صیادی چک",
    "State": "وضعیت چک (۰: نزد صندوق، ۱: پاس‌شده، ۲: برگشتی، ۳: در جریان وصول، ۴: باطل‌شده)",
}


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_nullable: bool = True
    is_identity: bool = False
    is_computed: bool = False
    default_value: Optional[str] = None
    ordinal_position: int = 0
    description: Optional[str] = None


class ConstraintMetadata(BaseModel):
    name: str
    constraint_type: str  # 'PK', 'FK', 'UNIQUE', 'CHECK', 'DEFAULT'
    columns: list[str] = Field(default_factory=list)
    referenced_table: Optional[str] = None
    referenced_columns: list[str] = Field(default_factory=list)


class IndexMetadata(BaseModel):
    name: str
    is_unique: bool = False
    is_primary: bool = False
    columns: list[str] = Field(default_factory=list)


class TriggerMetadata(BaseModel):
    name: str
    table_name: str
    is_disabled: bool = False
    is_instead_of: bool = False
    events: list[str] = Field(default_factory=list)  # INSERT, UPDATE, DELETE


class StoredProcMetadata(BaseModel):
    name: str
    schema_name: str = "dbo"
    parameters: list[dict[str, Any]] = Field(default_factory=list)


class ViewMetadata(BaseModel):
    name: str
    schema_name: str = "dbo"
    columns: list[str] = Field(default_factory=list)


class RelationshipMetadata(BaseModel):
    fk_name: str
    source_table: str
    source_columns: list[str]
    target_table: str
    target_columns: list[str]
    is_inferred: bool = False
    description: Optional[str] = None


class TableMetadata(BaseModel):
    name: str
    schema_name: str = "dbo"
    row_count: int = 0
    size_kb: int = 0
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    description: Optional[str] = None
    columns: dict[str, ColumnMetadata] = Field(default_factory=dict)
    primary_keys: list[str] = Field(default_factory=list)
    constraints: list[ConstraintMetadata] = Field(default_factory=list)
    indexes: list[IndexMetadata] = Field(default_factory=list)
    triggers: list[TriggerMetadata] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    database_name: str
    server_name: str
    scanned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tables: dict[str, TableMetadata] = Field(default_factory=dict)
    views: list[ViewMetadata] = Field(default_factory=list)
    stored_procedures: list[StoredProcMetadata] = Field(default_factory=list)
    triggers: list[TriggerMetadata] = Field(default_factory=list)
    relationships: list[RelationshipMetadata] = Field(default_factory=list)
    dictionary_annotations_count: int = 0

    @property
    def total_tables(self) -> int:
        return len(self.tables)

    @property
    def total_views(self) -> int:
        return len(self.views)

    @property
    def total_procs(self) -> int:
        return len(self.stored_procedures)

    @property
    def total_triggers(self) -> int:
        return len(self.triggers)
