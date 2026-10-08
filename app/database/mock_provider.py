"""
Offline Mock/Demo Database Provider for Sepehryar ERP.
Provides full offline schemas, relationships, and realistic sample accounting data
without requiring an active SQL Server instance.
"""
from datetime import datetime, timezone
from typing import Any
from app.database.metadata import (
    DatabaseSchema,
    TableMetadata,
    ColumnMetadata,
    ConstraintMetadata,
    IndexMetadata,
    TriggerMetadata,
    StoredProcMetadata,
    ViewMetadata,
    RelationshipMetadata,
    SEPEHRYAR_TABLE_DICTIONARY,
    SEPEHRYAR_COLUMN_DICTIONARY,
)

# Realistic sample data for Sepehryar tables
MOCK_TABLE_ROWS: dict[str, list[dict[str, Any]]] = {
    "TblKala": [
        {"IDKala": 101, "CodeKala": "K-101", "NameKala": "لپ‌تاپ ایسوس مدل ZenBook 14", "Barcode": "6260123456789", "Vahed": "دستگاه", "GhimatForosh": 65000000, "GhimatKharid": 58000000, "Mogodi": 12},
        {"IDKala": 102, "CodeKala": "K-102", "NameKala": "مانیتور ۲۷ اینچ دل 4K", "Barcode": "6260123456790", "Vahed": "عدد", "GhimatForosh": 28000000, "GhimatKharid": 24000000, "Mogodi": 25},
        {"IDKala": 103, "CodeKala": "K-103", "NameKala": "کیبورد مکانیکی لاجیتک MX", "Barcode": "6260123456791", "Vahed": "عدد", "GhimatForosh": 8500000, "GhimatKharid": 7100000, "Mogodi": 40},
        {"IDKala": 104, "CodeKala": "K-104", "NameKala": "ماوس بی‌سیم لاجیتک Master 3S", "Barcode": "6260123456792", "Vahed": "عدد", "GhimatForosh": 6200000, "GhimatKharid": 5100000, "Mogodi": 30},
        {"IDKala": 105, "CodeKala": "K-105", "NameKala": "هارد اکسترنال ۲ ترابایت وسترن دیجیتال", "Barcode": "6260123456793", "Vahed": "عدد", "GhimatForosh": 4900000, "GhimatKharid": 4100000, "Mogodi": 50},
    ],
    "TblPerson": [
        {"IDPerson": 1, "Code": "110001", "Name": "شرکت آریا تجارت البرز", "Family": "(سهامی خاص)", "CodeMelli": "10103456789", "Tel": "021-88776655", "Mobile": "09121112233", "Type": 1, "RemainAccount": -150000000},
        {"IDPerson": 2, "Code": "110002", "Name": "بازرگانی پارس گستر نوین", "Family": "", "CodeMelli": "10109876543", "Tel": "021-44332211", "Mobile": "09123334455", "Type": 1, "RemainAccount": 85000000},
        {"IDPerson": 3, "Code": "201001", "Name": "صنایع الکترونیک خاورمیانه", "Family": "تأمین‌کننده قطعات", "CodeMelli": "10105556677", "Tel": "031-33221100", "Mobile": "09131119988", "Type": 2, "RemainAccount": 420000000},
        {"IDPerson": 4, "Code": "100001", "Name": "بانک ملت", "Family": "شعبه مرکزی - جاری ۴۴۵۵", "CodeMelli": "", "Tel": "021-82991", "Mobile": "", "Type": 4, "RemainAccount": 1250000000},
        {"IDPerson": 5, "Code": "100002", "Name": "بانک سامان", "Family": "شعبه سعادت‌آباد - جاری ۸۸۰۱", "CodeMelli": "", "Tel": "021-22001", "Mobile": "", "Type": 4, "RemainAccount": 680000000},
    ],
    "TR": [
        {"IDTR": 1, "IDKala": 101, "IdPerson": 1, "Tarikh": "1403/05/10", "Ted": 2, "Fee": 65000000, "Mab": 130000000, "SanadNo": 1042, "Sharh": "فروش لپ‌تاپ به آریا تجارت"},
        {"IDTR": 2, "IDKala": 102, "IdPerson": 1, "Tarikh": "1403/05/10", "Ted": 3, "Fee": 28000000, "Mab": 84000000, "SanadNo": 1042, "Sharh": "فروش مانیتور به آریا تجارت"},
        {"IDTR": 3, "IDKala": 103, "IdPerson": 2, "Tarikh": "1403/05/12", "Ted": 5, "Fee": 8500000, "Mab": 42500000, "SanadNo": 1045, "Sharh": "فروش کیبورد به پارس گستر"},
        {"IDTR": 4, "IDKala": 104, "IdPerson": 2, "Tarikh": "1403/05/12", "Ted": 5, "Fee": 6200000, "Mab": 31000000, "SanadNo": 1045, "Sharh": "فروش ماوس به پارس گستر"},
        {"IDTR": 5, "IDKala": 105, "IdPerson": 3, "Tarikh": "1403/05/15", "Ted": 20, "Fee": 4100000, "Mab": 82000000, "SanadNo": 1048, "Sharh": "خرید هارد اکسترنال از صنایع الکترونیک"},
    ],
    "TblSanad": [
        {"ID": 1, "SanadNo": 1042, "Tarikh": "1403/05/10", "IdHesab": "110-01", "Bedehkar": 214000000, "Bestankar": 0, "Sharh": "بدهکار شدن شرکت آریا تجارت بابت فاکتور ۱۰۴۲"},
        {"ID": 2, "SanadNo": 1042, "Tarikh": "1403/05/10", "IdHesab": "701-01", "Bedehkar": 0, "Bestankar": 214000000, "Sharh": "فروش ناخالص کالا فاکتور ۱۰۴۲"},
        {"ID": 3, "SanadNo": 1045, "Tarikh": "1403/05/12", "IdHesab": "110-02", "Bedehkar": 73500000, "Bestankar": 0, "Sharh": "بدهکار شدن پارس گستر فاکتور ۱۰۴۵"},
        {"ID": 4, "SanadNo": 1045, "Tarikh": "1403/05/12", "IdHesab": "701-01", "Bedehkar": 0, "Bestankar": 73500000, "Sharh": "فروش ناخالص کالا فاکتور ۱۰۴۵"},
    ],
    "TblAnbar": [
        {"IDAnbar": 1, "CodeAnbar": "01", "NameAnbar": "انبار مرکزی تجهیزات دیجیتال", "MasoulAnbar": "احمد رضایی", "Address": "تهران، شهرک صنعتی شمس‌آباد"},
        {"IDAnbar": 2, "CodeAnbar": "02", "NameAnbar": "انبار توزیع و پخش غرب", "MasoulAnbar": "علی مرادی", "Address": "تهران، کیلومتر ۱۴ جاده مخصوص"},
    ]
}


def get_mock_database_schema(db_name: str = "Sepehr_hesabico_1403") -> DatabaseSchema:
    """Generate a fully-formed DatabaseSchema instance for offline demo testing."""
    schema = DatabaseSchema(
        database_name=db_name,
        server_name=".\\SEPEHRYAR_DEMO",
        scanned_at=datetime.now(timezone.utc).isoformat()
    )

    # 1. TblKala
    tbl_kala = TableMetadata(
        name="TblKala",
        schema_name="dbo",
        row_count=len(MOCK_TABLE_ROWS["TblKala"]),
        size_kb=64,
        description=SEPEHRYAR_TABLE_DICTIONARY.get("TblKala"),
        primary_keys=["IDKala"],
        columns={
            "IDKala": ColumnMetadata(name="IDKala", data_type="int", is_nullable=False, is_identity=True, description="شناسه یکتا کالا", ordinal_position=1),
            "CodeKala": ColumnMetadata(name="CodeKala", data_type="varchar", max_length=50, description="کد کالا", ordinal_position=2),
            "NameKala": ColumnMetadata(name="NameKala", data_type="nvarchar", max_length=200, description="نام کالا", ordinal_position=3),
            "Barcode": ColumnMetadata(name="Barcode", data_type="varchar", max_length=50, description="بارکد کالا", ordinal_position=4),
            "Vahed": ColumnMetadata(name="Vahed", data_type="nvarchar", max_length=50, description="واحد اصلی کالا", ordinal_position=5),
            "GhimatForosh": ColumnMetadata(name="GhimatForosh", data_type="bigint", description="قیمت فروش", ordinal_position=6),
            "GhimatKharid": ColumnMetadata(name="GhimatKharid", data_type="bigint", description="قیمت خرید", ordinal_position=7),
            "Mogodi": ColumnMetadata(name="Mogodi", data_type="float", description="موجودی انبار", ordinal_position=8),
        },
        constraints=[
            ConstraintMetadata(name="PK_TblKala", constraint_type="PK", columns=["IDKala"])
        ],
        indexes=[
            IndexMetadata(name="PK_TblKala", is_unique=True, is_primary=True, columns=["IDKala"]),
            IndexMetadata(name="IX_TblKala_Barcode", is_unique=False, columns=["Barcode"])
        ],
        triggers=[
            TriggerMetadata(name="trg_TblKala_Audit", table_name="TblKala", events=["UPDATE", "DELETE"])
        ]
    )
    schema.tables["TblKala"] = tbl_kala

    # 2. TblPerson
    tbl_person = TableMetadata(
        name="TblPerson",
        schema_name="dbo",
        row_count=len(MOCK_TABLE_ROWS["TblPerson"]),
        size_kb=80,
        description=SEPEHRYAR_TABLE_DICTIONARY.get("TblPerson"),
        primary_keys=["IDPerson"],
        columns={
            "IDPerson": ColumnMetadata(name="IDPerson", data_type="int", is_nullable=False, is_identity=True, description="شناسه شخص", ordinal_position=1),
            "Code": ColumnMetadata(name="Code", data_type="varchar", max_length=20, description="کد تفصیلی", ordinal_position=2),
            "Name": ColumnMetadata(name="Name", data_type="nvarchar", max_length=150, description="نام", ordinal_position=3),
            "Family": ColumnMetadata(name="Family", data_type="nvarchar", max_length=150, description="نام خانوادگی / عنوان", ordinal_position=4),
            "CodeMelli": ColumnMetadata(name="CodeMelli", data_type="varchar", max_length=20, description="کد ملی", ordinal_position=5),
            "Tel": ColumnMetadata(name="Tel", data_type="varchar", max_length=50, description="تلفن", ordinal_position=6),
            "Mobile": ColumnMetadata(name="Mobile", data_type="varchar", max_length=50, description="موبایل", ordinal_position=7),
            "Type": ColumnMetadata(name="Type", data_type="int", description="نوع طرف حساب (۱: مشتری، ۲: تأمین‌کننده، ۴: بانک)", ordinal_position=8),
            "RemainAccount": ColumnMetadata(name="RemainAccount", data_type="bigint", description="مانده حساب", ordinal_position=9),
        },
        constraints=[
            ConstraintMetadata(name="PK_TblPerson", constraint_type="PK", columns=["IDPerson"])
        ],
        indexes=[
            IndexMetadata(name="PK_TblPerson", is_unique=True, is_primary=True, columns=["IDPerson"]),
            IndexMetadata(name="IX_TblPerson_Code", is_unique=True, columns=["Code"])
        ]
    )
    schema.tables["TblPerson"] = tbl_person

    # 3. TR (Transactions)
    tbl_tr = TableMetadata(
        name="TR",
        schema_name="dbo",
        row_count=len(MOCK_TABLE_ROWS["TR"]),
        size_kb=128,
        description=SEPEHRYAR_TABLE_DICTIONARY.get("TR"),
        primary_keys=["IDTR"],
        columns={
            "IDTR": ColumnMetadata(name="IDTR", data_type="bigint", is_nullable=False, is_identity=True, description="شناسه تراکنش", ordinal_position=1),
            "IDKala": ColumnMetadata(name="IDKala", data_type="int", is_nullable=False, description="شناسه کالا", ordinal_position=2),
            "IdPerson": ColumnMetadata(name="IdPerson", data_type="int", is_nullable=True, description="شناسه طرف حساب", ordinal_position=3),
            "Tarikh": ColumnMetadata(name="Tarikh", data_type="varchar", max_length=10, description="تاریخ تراکنش", ordinal_position=4),
            "Ted": ColumnMetadata(name="Ted", data_type="float", description="تعداد", ordinal_position=5),
            "Fee": ColumnMetadata(name="Fee", data_type="bigint", description="قیمت واحد", ordinal_position=6),
            "Mab": ColumnMetadata(name="Mab", data_type="bigint", description="مبلغ کل", ordinal_position=7),
            "SanadNo": ColumnMetadata(name="SanadNo", data_type="int", description="شماره سند", ordinal_position=8),
            "Sharh": ColumnMetadata(name="Sharh", data_type="nvarchar", max_length=300, description="شرح ردیف", ordinal_position=9),
        },
        constraints=[
            ConstraintMetadata(name="PK_TR", constraint_type="PK", columns=["IDTR"]),
            ConstraintMetadata(name="FK_TR_TblKala", constraint_type="FK", columns=["IDKala"], referenced_table="TblKala", referenced_columns=["IDKala"]),
            ConstraintMetadata(name="FK_TR_TblPerson", constraint_type="FK", columns=["IdPerson"], referenced_table="TblPerson", referenced_columns=["IDPerson"]),
        ],
        indexes=[
            IndexMetadata(name="PK_TR", is_unique=True, is_primary=True, columns=["IDTR"]),
            IndexMetadata(name="IX_TR_IDKala", is_unique=False, columns=["IDKala"]),
            IndexMetadata(name="IX_TR_IdPerson", is_unique=False, columns=["IdPerson"])
        ]
    )
    schema.tables["TR"] = tbl_tr

    # 4. TblSanad
    tbl_sanad = TableMetadata(
        name="TblSanad",
        schema_name="dbo",
        row_count=len(MOCK_TABLE_ROWS["TblSanad"]),
        size_kb=96,
        description=SEPEHRYAR_TABLE_DICTIONARY.get("TblSanad"),
        primary_keys=["ID"],
        columns={
            "ID": ColumnMetadata(name="ID", data_type="bigint", is_nullable=False, is_identity=True, description="شناسه آرتیکل", ordinal_position=1),
            "SanadNo": ColumnMetadata(name="SanadNo", data_type="int", is_nullable=False, description="شماره سند", ordinal_position=2),
            "Tarikh": ColumnMetadata(name="Tarikh", data_type="varchar", max_length=10, description="تاریخ سند", ordinal_position=3),
            "IdHesab": ColumnMetadata(name="IdHesab", data_type="varchar", max_length=30, description="کد حساب", ordinal_position=4),
            "Bedehkar": ColumnMetadata(name="Bedehkar", data_type="bigint", description="بدهکار", ordinal_position=5),
            "Bestankar": ColumnMetadata(name="Bestankar", data_type="bigint", description="بستانکار", ordinal_position=6),
            "Sharh": ColumnMetadata(name="Sharh", data_type="nvarchar", max_length=300, description="شرح آرتیکل", ordinal_position=7),
        },
        constraints=[
            ConstraintMetadata(name="PK_TblSanad", constraint_type="PK", columns=["ID"])
        ]
    )
    schema.tables["TblSanad"] = tbl_sanad

    # 5. TblAnbar
    tbl_anbar = TableMetadata(
        name="TblAnbar",
        schema_name="dbo",
        row_count=len(MOCK_TABLE_ROWS["TblAnbar"]),
        size_kb=32,
        description=SEPEHRYAR_TABLE_DICTIONARY.get("TblAnbar"),
        primary_keys=["IDAnbar"],
        columns={
            "IDAnbar": ColumnMetadata(name="IDAnbar", data_type="int", is_nullable=False, description="شناسه انبار", ordinal_position=1),
            "CodeAnbar": ColumnMetadata(name="CodeAnbar", data_type="varchar", max_length=10, description="کد انبار", ordinal_position=2),
            "NameAnbar": ColumnMetadata(name="NameAnbar", data_type="nvarchar", max_length=100, description="نام انبار", ordinal_position=3),
            "MasoulAnbar": ColumnMetadata(name="MasoulAnbar", data_type="nvarchar", max_length=100, description="مسئول انبار", ordinal_position=4),
            "Address": ColumnMetadata(name="Address", data_type="nvarchar", max_length=250, description="آدرس انبار", ordinal_position=5),
        },
        constraints=[
            ConstraintMetadata(name="PK_TblAnbar", constraint_type="PK", columns=["IDAnbar"])
        ]
    )
    schema.tables["TblAnbar"] = tbl_anbar

    # Relationships
    schema.relationships = [
        RelationshipMetadata(
            fk_name="FK_TR_TblKala",
            source_table="TR",
            source_columns=["IDKala"],
            target_table="TblKala",
            target_columns=["IDKala"],
            is_inferred=False,
            description="اتصال ریز اقلام فاکتور به کالا"
        ),
        RelationshipMetadata(
            fk_name="FK_TR_TblPerson",
            source_table="TR",
            source_columns=["IdPerson"],
            target_table="TblPerson",
            target_columns=["IDPerson"],
            is_inferred=False,
            description="اتصال ریز اقلام فاکتور به طرف حساب (مشتری/تأمین‌کننده)"
        ),
    ]

    # Stored Procedures
    schema.stored_procedures = [
        StoredProcMetadata(name="sp_TblFactor_Insert", schema_name="dbo"),
        StoredProcMetadata(name="sp_CheckPardakht_ShowData", schema_name="dbo"),
        StoredProcMetadata(name="sp_master_soodzianCnt", schema_name="dbo"),
        StoredProcMetadata(name="sp_TR_Anbargardani_ListMoghayerat", schema_name="dbo"),
    ]

    # Views
    schema.views = [
        ViewMetadata(name="VW_KalaMogodiTotal", schema_name="dbo", columns=["IDKala", "NameKala", "TotalMogodi"]),
        ViewMetadata(name="VW_PersonBalanceSummary", schema_name="dbo", columns=["IDPerson", "FullName", "BalanceType", "RemainAccount"]),
    ]

    # Count dictionary annotations
    annotated = sum(1 for t in schema.tables.values() if t.description)
    schema.dictionary_annotations_count = annotated

    return schema


def get_mock_sample_rows(table_name: str, limit: int = 20) -> list[dict[str, Any]]:
    """Return mock sample rows for a table."""
    rows = MOCK_TABLE_ROWS.get(table_name, [])
    return rows[:limit]
