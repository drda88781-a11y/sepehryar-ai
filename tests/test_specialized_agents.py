"""
Comprehensive tests for all 7 specialized agents in Sepehryar AI Core.
"""
from app.agent.specialized import (
    AgentRole,
    AgentTask,
    Blackboard,
    CriticVerdict,
    DatabaseAgent,
    SQLAgent,
    ProcedureAgent,
    CodeAgent,
    DebugAgent,
    ArchitectureAgent,
    CriticAgent,
)


def test_database_agent_schema_discovery():
    """Verify DatabaseAgent extracts tables, primary keys, and relationships."""
    agent = DatabaseAgent()
    blackboard = Blackboard(user_query="تحلیل ساختار جدول اشخاص و مانده حساب")
    task = AgentTask(task_id="t_db", role=AgentRole.DATABASE, goal="کشف ساختار جداول TblPerson و Master")

    result = agent.execute(task, blackboard)
    assert result.success is True
    assert result.role == AgentRole.DATABASE
    assert "TblPerson" in result.artifacts["target_tables"]
    assert "Master" in result.artifacts["target_tables"]
    assert len(result.findings) > 0
    assert any("Sh_ozviat" in f for f in result.findings)


def test_sql_agent_query_and_transaction_design():
    """Verify SQLAgent produces safe transactions for writes and NOLOCK for reads."""
    agent = SQLAgent()

    # Read query test
    bb_read = Blackboard(user_query="گزارش مانده مشتریان")
    bb_read.target_entities = ["Master", "TblPerson"]
    t_read = AgentTask(task_id="t_sql_read", role=AgentRole.SQL, goal="گزارش مانده مشتریان")
    res_read = agent.execute(t_read, bb_read)
    assert res_read.success is True
    assert "WITH (NOLOCK)" in res_read.artifacts["generated_sql"]

    # Write query test
    bb_write = Blackboard(user_query="درج رکورد اصلاحی")
    bb_write.target_entities = ["TblPerson"]
    t_write = AgentTask(task_id="t_sql_write", role=AgentRole.SQL, goal="ثبت و ویرایش وضعیت اشخاص")
    res_write = agent.execute(t_write, bb_write)
    assert res_write.success is True
    assert "BEGIN TRANSACTION" in res_write.artifacts["generated_sql"]
    assert "COMMIT TRANSACTION" in res_write.artifacts["generated_sql"]
    assert "XACT_STATE()" in res_write.artifacts["generated_sql"]


def test_procedure_agent_convention_enforcement():
    """Verify ProcedureAgent discovers patterns, checks triggers, and generates enterprise SP."""
    agent = ProcedureAgent()
    blackboard = Blackboard(user_query="ثبت فاکتور فروش")
    blackboard.target_entities = ["TR", "TRSub", "TblPerson"]
    task = AgentTask(task_id="t_proc", role=AgentRole.PROCEDURE, goal="نوشتن پروسیجر ثبت فاکتور تجاری")

    result = agent.execute(task, blackboard)
    assert result.success is True
    assert "generated_sp" in result.artifacts
    sp_code = result.artifacts["generated_sp"]
    assert "CREATE PROCEDURE" in sp_code
    assert "@ResultCode INT OUTPUT" in sp_code
    assert "@ResultMessage NVARCHAR(500) OUTPUT" in sp_code
    assert "BEGIN TRY" in sp_code
    assert "ROLLBACK TRANSACTION" in sp_code


def test_code_agent_csharp_service_generation():
    """Verify CodeAgent generates Clean Architecture C# data access service."""
    agent = CodeAgent()
    blackboard = Blackboard(user_query="کد فراخوانی پروسیجر ثبت شخص")
    blackboard.target_entities = ["TblPerson"]
    task = AgentTask(task_id="t_code", role=AgentRole.CODE, goal="ایجاد لایه DAL برای ثبت شخص در C#")

    result = agent.execute(task, blackboard)
    assert result.success is True
    cs_code = result.artifacts["generated_csharp_code"]
    assert "public class SepehryarDataService" in cs_code
    assert "using var connection = new SqlConnection" in cs_code
    assert "ExecuteNonQueryAsync" in cs_code


def test_debug_agent_rca_diagnostic_trajectory():
    """Verify DebugAgent performs multi-stage RCA (Error -> Trace -> Code -> SQL -> Data -> Root Cause)."""
    agent = DebugAgent()
    blackboard = Blackboard(user_query="خطای منفی شدن موجودی کالا")
    task = AgentTask(task_id="t_debug", role=AgentRole.DEBUG, goal="خطای کسری موجودی کالا در انبار (Negative Inventory)")

    result = agent.execute(task, blackboard)
    assert result.success is True
    chain = result.artifacts["diagnostic_chain"]
    assert len(chain) >= 5
    assert any("Mande" in c for c in chain)
    assert result.artifacts["remedy"] != ""


def test_architecture_agent_impact_and_no_touch():
    """Verify ArchitectureAgent identifies modules, impact matrices, and no-touch areas."""
    agent = ArchitectureAgent()
    blackboard = Blackboard(user_query="تغییر ساختار اسناد مالی")
    task = AgentTask(task_id="t_arch", role=AgentRole.ARCHITECTURE, goal="افزودن امکان جدید به اسناد مالی")

    result = agent.execute(task, blackboard)
    assert result.success is True
    assert result.artifacts["primary_module"] == "financial"
    assert len(result.artifacts["no_touch_areas"]) > 0
    assert len(result.artifacts["impacted_subsystems"]) > 0


def test_critic_agent_approves_safe_and_rejects_dangerous():
    """Verify CriticAgent gatekeeper catches data corruption risks and approves safe code."""
    agent = CriticAgent()

    # 1. Dangerous code test
    bb_danger = Blackboard(user_query="تست خطرناک")
    bb_danger.generated_sql = "DROP TABLE Master; DELETE FROM TblSanad;"
    rev_danger = agent.review_solution(bb_danger)
    assert rev_danger.verdict == CriticVerdict.REJECTED
    assert rev_danger.data_integrity_safe is False

    # 2. Safe transactional code test
    bb_safe = Blackboard(user_query="تست امن")
    bb_safe.generated_sp = """
    BEGIN TRY
        BEGIN TRANSACTION;
        UPDATE TblSanadD SET Bed = 1000, Bes = 1000 WHERE Radif = 1;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
    END CATCH
    """
    rev_safe = agent.review_solution(bb_safe)
    assert rev_safe.verdict in (CriticVerdict.APPROVED, CriticVerdict.APPROVED_WITH_WARNINGS)
    assert rev_safe.data_integrity_safe is True
