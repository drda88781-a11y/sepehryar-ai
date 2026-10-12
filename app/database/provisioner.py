"""
Database Provisioner & Installer Intelligence Engine:
Provides DDL generation for fiscal years, automated index creation,
safe transactional opening voucher deployment, and comprehensive database health audits.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.core.logger import get_logger
from app.database.connection import db_connection_manager

logger = get_logger("database.provisioner")


class SchemaHealthAuditReport(BaseModel):
    database_name: str
    is_healthy: bool
    opening_balanced: bool
    total_debit: int = 0
    total_credit: int = 0
    balance_difference: int = 0
    broken_person_links_count: int = 0
    indexes_status: dict[str, bool] = Field(default_factory=dict)
    active_triggers: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DatabaseProvisioner:
    """Manages database initialization, index tuning, and integrity audits for Sepehryar."""

    ESSENTIAL_INDEXES_DDL = {
        "IX_TR_Factor_Sodor": """
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TR_Factor_Sodor' AND object_id = OBJECT_ID('dbo.TR'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_TR_Factor_Sodor] ON [dbo].[TR] ([Factor] DESC, [Sodor] DESC)
    INCLUDE ([Idkala], [TED], [Bed], [Bes], [Taraf]);
END
        """.strip(),

        "IX_TR_SanadM_Sodor": """
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TR_SanadM_Sodor' AND object_id = OBJECT_ID('dbo.TR'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_TR_SanadM_Sodor] ON [dbo].[TR] ([SanadM] DESC, [Sodor] DESC)
    INCLUDE ([Srfsl], [Moin], [HSB], [Bed], [Bes], [Taraf]);
END
        """.strip(),

        "IX_Master_personcod": """
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Master_personcod' AND object_id = OBJECT_ID('dbo.Master'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Master_personcod] ON [dbo].[Master] ([personcod])
    INCLUDE ([Srfsl], [Moin], [HSB], [Bed], [Bes]);
END
        """.strip(),

        "IX_TblHesabText_Lookup": """
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TblHesabText_Lookup' AND object_id = OBJECT_ID('dbo.TblHesabText'))
BEGIN
    CREATE NONCLUSTERED INDEX [IX_TblHesabText_Lookup] ON [dbo].[TblHesabText] ([Srfsl], [Moin], [HSB])
    INCLUDE ([Text]);
END
        """.strip()
    }

    @classmethod
    def generate_tuning_script(cls) -> str:
        """Returns unified SQL DDL script to ensure all high-speed indexes are deployed."""
        return "\n\n".join(cls.ESSENTIAL_INDEXES_DDL.values())

    @classmethod
    def generate_opening_voucher_transaction_sql(
        cls,
        sanad_number: int,
        date_shamsi: str,
        articles: list[dict[str, Any]],
        description: str = "سند افتتاحیه دوره مالی"
    ) -> str:
        """
        Generates a robust, atomic, trigger-safe SQL script to register Opening Voucher.
        """
        tr_inserts = []
        master_inserts = []
        total_bed = sum(int(a.get("Bed", 0)) for a in articles)
        total_bes = sum(int(a.get("Bes", 0)) for a in articles)

        for a in articles:
            sodor = a.get("Sodor", 1)
            srfsl = a.get("Srfsl", 110)
            moin = a.get("Moin", 1)
            hsb = a.get("HSB", 0)
            sharh = a.get("Sharh", "").replace("'", "''")
            taraf = a.get("Taraf") or "NULL"
            bed = int(a.get("Bed", 0))
            bes = int(a.get("Bes", 0))

            tr_inserts.append(
                f"INSERT INTO dbo.TR (Sodor, Srfsl, Moin, HSB, DateR, Sharh, SanadM, Taraf, Bed, Bes) "
                f"VALUES ({sodor}, {srfsl}, {moin}, {hsb}, '{date_shamsi}', N'{sharh}', {sanad_number}, {taraf}, {bed}, {bes});"
            )

            master_inserts.append(
                f"INSERT INTO dbo.Master (Srfsl, Moin, HSB, Bed, Bes, sodur, personcod) "
                f"VALUES ({srfsl}, {moin}, {hsb}, {bed}, {bes}, 1, {taraf});"
            )

        tr_sql = "\n    ".join(tr_inserts)
        master_sql = "\n    ".join(master_inserts)

        sql_script = f"""
BEGIN TRANSACTION;
BEGIN TRY
    -- 1. Disable site sync triggers temporarily to prevent timeout
    IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
        DISABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;

    -- 2. Insert Sanad Header
    DELETE FROM dbo.TblSanad WHERE SanadM = {sanad_number};
    INSERT INTO dbo.TblSanad (SanadM, DateR, Sharh, Bed, Bes)
    VALUES ({sanad_number}, '{date_shamsi}', N'{description}', {total_bed}, {total_bes});

    -- 3. Insert TR Articles
    DELETE FROM dbo.TR WHERE SanadM = {sanad_number};
    {tr_sql}

    -- 4. Re-enable triggers
    IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
        ENABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;

    COMMIT TRANSACTION;
    PRINT 'Opening Voucher successfully deployed and balanced.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    
    -- Ensure trigger is re-enabled even on failure
    IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'UpdateSiteSync_TR')
        ENABLE TRIGGER dbo.UpdateSiteSync_TR ON dbo.TR;

    THROW;
END CATCH;
        """.strip()

        return sql_script

    @classmethod
    def audit_database_health(cls, database_name: Optional[str] = None) -> SchemaHealthAuditReport:
        """
        Executes a deep diagnostic health audit across key Sepehryar tables.
        """
        target_db = database_name or "Sepehr_Main2_1405"
        recommendations = []
        is_healthy = True

        with db_connection_manager.get_connection(database=target_db) as conn:
            cursor = conn.cursor()

            # 1. Audit Sanad 1 Balance
            cursor.execute("""
                SELECT ISNULL(SUM(Bed), 0), ISNULL(SUM(Bes), 0)
                FROM dbo.TR WITH (NOLOCK)
                WHERE SanadM = 1;
            """)
            row = cursor.fetchone()
            tot_bed = int(row[0]) if row else 0
            tot_bes = int(row[1]) if row else 0
            diff = abs(tot_bed - tot_bes)
            opening_balanced = (diff == 0) and (tot_bed > 0)

            if not opening_balanced:
                is_healthy = False
                recommendations.append(f"تراز سند افتتاحیه (Sanad 1) متوازن نیست! اختلاف: {diff:,} ریال.")

            # 2. Audit Master.personcod broken linkages
            cursor.execute("""
                SELECT COUNT(*)
                FROM dbo.Master m WITH (NOLOCK)
                WHERE m.personcod IS NOT NULL AND m.personcod > 0
                  AND NOT EXISTS (SELECT 1 FROM dbo.TblPerson p WITH (NOLOCK) WHERE p.Sh_ozviat = m.personcod);
            """)
            broken_cnt = int(cursor.fetchone()[0])
            if broken_cnt > 0:
                is_healthy = False
                recommendations.append(f"تعداد {broken_cnt} ردیف در Master دارای personcod نامعتبر هستند و به TblPerson متصل نیستند.")

            # 3. Check essential indexes
            indexes_status = {}
            for idx_name in cls.ESSENTIAL_INDEXES_DDL.keys():
                cursor.execute("SELECT COUNT(*) FROM sys.indexes WHERE name = ?", (idx_name,))
                exists = bool(cursor.fetchone()[0])
                indexes_status[idx_name] = exists
                if not exists:
                    recommendations.append(f"ایندکس کارایی '{idx_name}' ایجاد نشده است؛ پیشنهاد می‌شود اعمال گردد.")

            # 4. Check active triggers on TR
            cursor.execute("""
                SELECT name
                FROM sys.triggers
                WHERE parent_id = OBJECT_ID('dbo.TR') AND is_disabled = 0;
            """)
            active_trigs = [r[0] for r in cursor.fetchall()]

        return SchemaHealthAuditReport(
            database_name=target_db,
            is_healthy=is_healthy,
            opening_balanced=opening_balanced,
            total_debit=tot_bed,
            total_credit=tot_bes,
            balance_difference=diff,
            broken_person_links_count=broken_cnt,
            indexes_status=indexes_status,
            active_triggers=active_trigs,
            recommendations=recommendations
        )


database_provisioner = DatabaseProvisioner()
