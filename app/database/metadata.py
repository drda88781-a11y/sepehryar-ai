"""
Comprehensive Pydantic models for database schema representation,
incorporating Sepehryar ERP Persian dictionary annotations.
"""
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

# Persian dictionary for core Sepehryar tables
SEPEHRYAR_TABLE_DICTIONARY: dict[str, str] = {
    "TblKala": "کالاها و خدمات (شناسه، نام، بارکد، گروه‌بندی و قیمت)",
    "TblPerson": "اشخاص، طرف‌حساب‌ها، مشتریان، تأمین‌کنندگان و بانک‌ها",
    "TR": "ریز اقلام فاکتورها، تراکنش‌های کالا و اسناد انبار",
    "Master": "سربرگ فاکتورها، حواله‌ها و اسناد خرید و فروش",
    "TblSanad": "ریز اسناد حسابداری و بدهکار/بستانکار آرتیکل‌ها",
    "TblSanadMaster": "سربرگ اسناد حسابداری (شماره، تاریخ، شرح کلی)",
    "TblHesab": "کدینگ حساب‌ها (کل، معین، تفصیلی)",
    "TblAnbar": "انبارها و موقعیت‌های فیزیکی نگهداری کالا",
    "TblCheck": "اطلاعات چک‌های دریافتی و پرداختی",
    "TblBank": "حساب‌های بانکی و صندوق‌های نقدی",
    "TblFactor": "فاکتورهای خرید، فروش و برگشتی",
    "TblReports": "تنظیمات و تعاریف گزارش‌های پیشرفته سیستم",
    "TblUser": "کاربران و سطوح دسترسی نرم‌افزار",
    "PayRol_TblGroupItem": "گروه‌بندی اقلام حقوق و دستمزد",
    "PayRol_TblItems": "اقلام و فیلدهای حقوق و دستمزد",
}

# Persian dictionary for common Sepehryar column fields
SEPEHRYAR_COLUMN_DICTIONARY: dict[str, str] = {
    "IDKala": "شناسه یکتا کالا",
    "NameKala": "نام کالا",
    "CodeKala": "کد کالا",
    "Barcode": "بارکد کالا",
    "Vahed": "واحد اصلی سنجش کالا",
    "GhimatForosh": "قیمت فروش نقدی",
    "GhimatKharid": "آخرین قیمت خرید",
    "Mogodi": "موجودی کالا",
    "IDPerson": "شناسه یکتای طرف حساب",
    "Name": "نام شخص / شرکت",
    "Family": "نام خانوادگی / نام تکمیلی",
    "Code": "کد تفصیلی شخص",
    "CodeMelli": "کد ملی شخص",
    "Tel": "شماره تلفن",
    "Mobile": "شماره همراه",
    "Address": "نشانی",
    "Type": "نوع شخص (۱: مشتری، ۲: تأمین‌کننده، ۴: بانک)",
    "RemainAccount": "مانده حساب شخص",
    "Bedehkar": "مبلغ بدهکار",
    "Bestankar": "مبلغ بستانکار",
    "Mab": "مبلغ ریالی آرتیکل / قلم تراکنش",
    "Ted": "تعداد کالا در فاکتور",
    "Fee": "فی / نرخ واحد کالا",
    "Tarikh": "تاریخ ثبت شمسی (مثلاً ۱۴۰۳/۰۵/۰۱)",
    "SanadNo": "شماره سند حسابداری",
    "Sharh": "شرح سند / شرح ردیف",
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
