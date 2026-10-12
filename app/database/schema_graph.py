"""
Sepehryar Schema Knowledge Graph & Implicit Relationship Resolver:
Maintains the complete architectural map of Sepehryar ERP tables and generates
optimal, non-Cartesian JOIN paths for Dynamic Report Builders.
"""
from collections import deque
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.core.logger import get_logger

logger = get_logger("database.schema_graph")


class JoinEdge(BaseModel):
    source_table: str
    target_table: str
    join_condition: str
    join_type: str = "LEFT JOIN"
    description: str = ""
    cardinality: str = "N:1"  # '1:1', '1:N', 'N:1'


class TableIdentityCard(BaseModel):
    table_name: str
    persian_title: str
    category: str  # 'financial', 'operational', 'inventory', 'base_entity'
    primary_keys: list[str] = Field(default_factory=list)
    vital_columns: list[str] = Field(default_factory=list)
    indexed_columns: list[str] = Field(default_factory=list)
    business_notes: str = ""


# Comprehensive Catalog of Core Sepehryar Tables
SEPEHRYAR_TABLE_CARDS: dict[str, TableIdentityCard] = {
    "Master": TableIdentityCard(
        table_name="Master",
        persian_title="سرآمد و مانده دفتر کل، معین و تفصیلی",
        category="financial",
        primary_keys=["Srfsl", "Moin", "HSB"],
        vital_columns=["Srfsl", "Moin", "HSB", "Bed", "Bes", "personcod", "Etebar", "MandeS", "MandeT"],
        indexed_columns=["Srfsl", "Moin", "HSB", "personcod"],
        business_notes="مانده نهایی حساب از تفاضل (Bed - Bes) به دست می‌آید. فیلد personcod به TblPerson.Sh_ozviat متصل است."
    ),
    "TR": TableIdentityCard(
        table_name="TR",
        persian_title="دفتر روزنامه تفصیلی، اقلام فاکتورها و تراکنش‌ها",
        category="operational",
        primary_keys=["Sodor"],
        vital_columns=["Sodor", "Srfsl", "Moin", "HSB", "DateR", "Serial", "Sharh", "Idkala", "Factor", "TED", "Fee", "Mabkh", "SanadM", "Taraf", "GRP", "IdAnbr", "Bed", "Bes"],
        indexed_columns=["Factor", "SanadM", "Idkala", "Taraf", "Srfsl", "Moin", "HSB", "IdAnbr"],
        business_notes="مرکز ثقل تمام اسناد و فاکتورها. اقلام فاکتور و آرتیکل‌های سند مالی همگی در این جدول ثبت می‌شوند. فیلد GRP به TblTypeTR.ID متصل است."
    ),
    "TblPerson": TableIdentityCard(
        table_name="TblPerson",
        persian_title="پرونده اشخاص، مشتریان، تأمین‌کنندگان و بانک‌ها",
        category="base_entity",
        primary_keys=["Sh_ozviat"],
        vital_columns=["Sh_ozviat", "Name", "Famil", "Tell", "Mobile", "Srfsl", "Moin", "Hesab", "Type", "Etebar", "codmeli", "BuyerType", "Status"],
        indexed_columns=["Sh_ozviat", "Hesab", "Mobile", "Type"],
        business_notes="فیلد Type: ۱=مشتری، ۲=تأمین‌کننده، ۳=ویزیتور، ۴=بانک/صندوق. کلید اتصال اصلی Sh_ozviat است که در Master به personcod و در TR به Taraf پیوند می‌خورد."
    ),
    "TblHesabText": TableIdentityCard(
        table_name="TblHesabText",
        persian_title="عناوین و شرح متنی حساب‌ها (کل، معین، تفصیلی)",
        category="financial",
        primary_keys=["Srfsl", "Moin", "HSB"],
        vital_columns=["Srfsl", "Moin", "HSB", "Text"],
        indexed_columns=["Srfsl", "Moin", "HSB"],
        business_notes="عنوان نمایشی تمامی سطوح تفصیلی حساب‌ها در نرم‌افزار در این جدول نگهداری می‌شود."
    ),
    "TblParam": TableIdentityCard(
        table_name="TblParam",
        persian_title="کدینگ حسابداری (سرفصل‌های کل و معین)",
        category="financial",
        primary_keys=["Srfsl", "Moin"],
        vital_columns=["Srfsl", "Moin", "Name", "BdBs", "Cscod"],
        indexed_columns=["Srfsl", "Moin"],
        business_notes="تعریف نام سرفصل‌های کل (Moin=0) و معین (Moin>0). فیلد BdBs ماهیت بدهکار/بستانکار پیش‌فرض حساب است."
    ),
    "TblSanad": TableIdentityCard(
        table_name="TblSanad",
        persian_title="سربرگ اسناد حسابداری",
        category="financial",
        primary_keys=["Sanad"],
        vital_columns=["Sanad", "Date", "Sharh", "TypeSanad", "User_Id", "StateSanad"],
        indexed_columns=["Sanad", "Date"],
        business_notes="سند شماره ۱ همیشه سند افتتاحیه سال مالی است. ردیف‌های تفصیلی سند در جدول TR با ستون SanadM متناظر هستند."
    ),
    "TblKala": TableIdentityCard(
        table_name="TblKala",
        persian_title="کاتالوگ کالاها و خدمات انبار",
        category="inventory",
        primary_keys=["IDKala"],
        vital_columns=["IDKala", "Name", "IDAnbar", "BaghaliCode", "Unit1", "Unit2", "Mande", "Bprice", "GroupCode"],
        indexed_columns=["IDKala", "BaghaliCode", "Name", "IDAnbar"],
        business_notes="موجودی لحظه‌ای در فیلد Mande ذخیره می‌شود. بارکد کالا در فیلد BaghaliCode و آخرین قیمت خرید در Bprice است."
    ),
    "Check": TableIdentityCard(
        table_name="[Check]",
        persian_title="اسناد دریافتنی (چک‌های عادی و صیادی دریافتی)",
        category="financial",
        primary_keys=["Id"],
        vital_columns=["Id", "serial", "mab", "DateChek", "DateR", "Bank", "sharh", "State", "PersonId", "SayadNum"],
        indexed_columns=["serial", "DateChek", "State", "PersonId", "SayadNum"],
        business_notes="وضعیت State: ۰=نزد صندوق، ۱=پاس شده، ۲=برگشتی، ۳=در جریان وصول بانکی، ۴=باطل/استرداد. فیلد PersonId به TblPerson.Sh_ozviat متصل است."
    ),
    "CheckPardakht": TableIdentityCard(
        table_name="CheckPardakht",
        persian_title="اسناد پرداختنی (چک‌های صادره به اشخاص)",
        category="financial",
        primary_keys=["Id"],
        vital_columns=["Id", "serial", "mab", "DateChek", "DateR", "DatePas", "State", "PersonId", "SayadNum"],
        indexed_columns=["serial", "DateChek", "State", "PersonId", "SayadNum"],
        business_notes="چک‌های پرداختی شرکت به همراه شناسه ۱۶ رقمی صیاد در SayadNum. فیلد PersonId به TblPerson.Sh_ozviat متصل است."
    ),
    "TblAnbar": TableIdentityCard(
        table_name="TblAnbar",
        persian_title="انبارها و محل‌های نگهداری کالا",
        category="inventory",
        primary_keys=["ID"],
        vital_columns=["ID", "Name", "Officer", "Adress", "Sarfasl", "Moin", "Hsb"],
        indexed_columns=["ID"],
        business_notes="شناسه انبار در ستون ID قرار دارد و در جدول TblKala به فیلد IDAnbar و در TR به IdAnbr پیوند می‌خورد."
    ),
    "TblBarCode": TableIdentityCard(
        table_name="TblBarCode",
        persian_title="بارکدهای فرعی و چندگانه کالا",
        category="inventory",
        primary_keys=["Id"],
        vital_columns=["Id", "IdKala", "Barcod", "IdUnit"],
        indexed_columns=["Barcod", "IdKala"],
        business_notes="جدول بارکدهای فرعی و چندتایی کالا متصل به TblKala.IDKala."
    ),
    "TblTypeTR": TableIdentityCard(
        table_name="TblTypeTR",
        persian_title="انواع فاکتورها، تراکنش‌ها و حواله‌های سیستم",
        category="operational",
        primary_keys=["ID"],
        vital_columns=["ID", "Name", "Type"],
        indexed_columns=["ID"],
        business_notes="انواع تراکنش: ۱=پیش‌فاکتور، ۱۰۰=رسید انبار، ۱۰۳=خرید، ۱۰۴=برگشت فروش، ۲۰۰=حواله انبار، ۲۰۳=فروش، ۲۰۴=برگشت خرید. در TR به فیلد GRP متصل می‌شود."
    ),
    "TblReports": TableIdentityCard(
        table_name="TblReports",
        persian_title="تعاریف و تنظیمات گزارش‌های پیشرفته سیستم",
        category="operational",
        primary_keys=["ReportId"],
        vital_columns=["ReportId", "ProcedureName", "ReportName", "Group_Id"],
        indexed_columns=["ReportId"],
        business_notes="فهرست گزارش‌های داینامیک و پروسیجرهای متناظر ثبت شده در سپهریار."
    )
}

# The Definitive Matrix of Explicit and Implicit Relationships
SEPEHRYAR_RELATIONSHIPS: list[JoinEdge] = [
    # Master <-> TblPerson
    JoinEdge(
        source_table="Master",
        target_table="TblPerson",
        join_condition="Master.personcod = TblPerson.Sh_ozviat",
        description="ارتباط مانده تفصیلی حساب با پرونده شخص (کلید منطقی اصلی)",
        cardinality="N:1"
    ),
    # Master <-> TblHesabText
    JoinEdge(
        source_table="Master",
        target_table="TblHesabText",
        join_condition="Master.Srfsl = TblHesabText.Srfsl AND Master.Moin = TblHesabText.Moin AND Master.HSB = TblHesabText.HSB",
        description="ارتباط مانده سرفصل با عنوان متنی حسابداری",
        cardinality="1:1"
    ),
    # Master <-> TblParam
    JoinEdge(
        source_table="Master",
        target_table="TblParam",
        join_condition="Master.Srfsl = TblParam.Srfsl AND Master.Moin = TblParam.Moin",
        description="ارتباط مانده سرفصل با عنوان کل و معین حسابداری",
        cardinality="N:1"
    ),
    # TR <-> Master
    JoinEdge(
        source_table="TR",
        target_table="Master",
        join_condition="TR.Srfsl = Master.Srfsl AND TR.Moin = Master.Moin AND TR.HSB = Master.HSB",
        description="ارتباط تراکنش و آرتیکل با مانده سرآمد حساب",
        cardinality="N:1"
    ),
    # TR <-> TblPerson
    JoinEdge(
        source_table="TR",
        target_table="TblPerson",
        join_condition="TR.Taraf = TblPerson.Sh_ozviat",
        description="ارتباط طرف حساب فاکتور/تراکنش با پرونده شخص",
        cardinality="N:1"
    ),
    # TR <-> TblKala
    JoinEdge(
        source_table="TR",
        target_table="TblKala",
        join_condition="TR.Idkala = TblKala.IDKala",
        description="ارتباط سطر فاکتور با کاتالوگ کالا",
        cardinality="N:1"
    ),
    # TR <-> TblSanad
    JoinEdge(
        source_table="TR",
        target_table="TblSanad",
        join_condition="TR.SanadM = TblSanad.Sanad",
        description="ارتباط آرتیکل‌های مالی با سربرگ سند حسابداری",
        cardinality="N:1"
    ),
    # TR <-> TblAnbar
    JoinEdge(
        source_table="TR",
        target_table="TblAnbar",
        join_condition="TR.IdAnbr = TblAnbar.ID",
        description="ارتباط تراکنش انبار با مشخصات انبار",
        cardinality="N:1"
    ),
    # TR <-> TblTypeTR
    JoinEdge(
        source_table="TR",
        target_table="TblTypeTR",
        join_condition="TR.GRP = TblTypeTR.ID",
        description="ارتباط نوع عملیات/فاکتور با جدول تعاریف تراکنش‌ها",
        cardinality="N:1"
    ),
    # TblKala <-> TblAnbar
    JoinEdge(
        source_table="TblKala",
        target_table="TblAnbar",
        join_condition="TblKala.IDAnbar = TblAnbar.ID",
        description="ارتباط کالا با انبار پیش‌فرض نگهداری",
        cardinality="N:1"
    ),
    # Check <-> TblPerson
    JoinEdge(
        source_table="[Check]",
        target_table="TblPerson",
        join_condition="[Check].PersonId = TblPerson.Sh_ozviat",
        description="ارتباط صاحب چک دریافتی با پرونده شخص",
        cardinality="N:1"
    ),
    # CheckPardakht <-> TblPerson
    JoinEdge(
        source_table="CheckPardakht",
        target_table="TblPerson",
        join_condition="CheckPardakht.PersonId = TblPerson.Sh_ozviat",
        description="ارتباط گیرنده چک صادره با پرونده شخص",
        cardinality="N:1"
    ),
    # TblBarCode <-> TblKala
    JoinEdge(
        source_table="TblBarCode",
        target_table="TblKala",
        join_condition="TblBarCode.IdKala = TblKala.IDKala",
        description="ارتباط بارکد تکمیلی با کاتالوگ کالا",
        cardinality="N:1"
    )
]


class SchemaKnowledgeGraph:
    """Graph engine calculating optimal joins and table topologies."""

    def __init__(self):
        self.tables = SEPEHRYAR_TABLE_CARDS
        self.edges = SEPEHRYAR_RELATIONSHIPS
        self._adj: dict[str, list[JoinEdge]] = {}
        self._build_adjacency_map()

    def _normalize_name(self, name: str) -> str:
        return name.strip("[]").strip()

    def _build_adjacency_map(self):
        for e in self.edges:
            s = self._normalize_name(e.source_table)
            t = self._normalize_name(e.target_table)
            self._adj.setdefault(s, []).append(e)
            # Add reverse edge for bidirectional graph navigation
            reverse_edge = JoinEdge(
                source_table=e.target_table,
                target_table=e.source_table,
                join_condition=e.join_condition,
                join_type=e.join_type,
                description=f"معکوس: {e.description}",
                cardinality="1:N" if e.cardinality == "N:1" else ("N:1" if e.cardinality == "1:N" else "1:1")
            )
            self._adj.setdefault(t, []).append(reverse_edge)

    def get_table_card(self, table_name: str) -> Optional[TableIdentityCard]:
        norm = self._normalize_name(table_name)
        for k, card in self.tables.items():
            if self._normalize_name(k).lower() == norm.lower():
                return card
        return None

    def list_all_tables(self) -> list[dict[str, Any]]:
        return [card.model_dump() for card in self.tables.values()]

    def get_direct_relations(self, table_name: str) -> list[JoinEdge]:
        norm = self._normalize_name(table_name)
        return self._adj.get(norm, [])

    def find_join_path(self, start_table: str, end_table: str) -> Optional[list[JoinEdge]]:
        """
        Finds the shortest, non-Cartesian join chain between two tables using BFS.
        """
        start_norm = self._normalize_name(start_table)
        end_norm = self._normalize_name(end_table)

        if start_norm == end_norm:
            return []

        queue = deque([(start_norm, [])])
        visited = {start_norm}

        while queue:
            curr, path = queue.popleft()
            for edge in self._adj.get(curr, []):
                neighbor = self._normalize_name(edge.target_table)
                if neighbor == end_norm:
                    return path + [edge]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [edge]))

        return None

    def build_joined_report_query(
        self,
        tables: list[str],
        select_fields: list[str],
        where_clauses: Optional[list[str]] = None,
        order_by: Optional[str] = None,
        top_limit: int = 50
    ) -> str:
        """
        Synthesizes a complete, index-optimized SQL query connecting all requested tables.
        """
        if not tables:
            return "SELECT 1"

        base_table = tables[0]
        used_tables = {self._normalize_name(base_table)}
        joins_sql = []

        # Connect each additional table via shortest join path
        for target in tables[1:]:
            target_norm = self._normalize_name(target)
            if target_norm in used_tables:
                continue

            # Find path from any already connected table to target
            best_path = None
            for connected in list(used_tables):
                path = self.find_join_path(connected, target_norm)
                if path and (best_path is None or len(path) < len(best_path)):
                    best_path = path

            if best_path:
                for edge in best_path:
                    tgt = self._normalize_name(edge.target_table)
                    if tgt not in used_tables:
                        used_tables.add(tgt)
                        joins_sql.append(
                            f"{edge.join_type} dbo.{edge.target_table} WITH (NOLOCK) ON {edge.join_condition}"
                        )

        where_str = f"\nWHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        order_str = f"\nORDER BY {order_by}" if order_by else ""
        fields_str = ",\n    ".join(select_fields) if select_fields else "*"
        joins_str = "\n".join(joins_sql)

        query = f"""
SELECT TOP ({top_limit})
    {fields_str}
FROM dbo.{base_table} WITH (NOLOCK)
{joins_str}{where_str}{order_str}
        """.strip()

        return query


schema_graph = SchemaKnowledgeGraph()
