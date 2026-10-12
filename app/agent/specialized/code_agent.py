"""
Code Agent: Specialist in Sepehryar application code (.NET / C# / Backend Services),
software architecture patterns, database-to-code mapping, procedure callers,
refactoring, and clean code generation.
"""
import time
from typing import Optional, Any
from app.agent.specialized.base import BaseSpecializedAgent, AgentRole, AgentTask, AgentResult, Blackboard
from app.core.logger import get_logger

logger = get_logger("agent.code_agent")


class CodeAgent(BaseSpecializedAgent):
    """
    Expert in Sepehryar Application Code & Software Engineering:
    - Analyzes .NET / C# and Python integration patterns
    - Maps Database entities (Tables/Views/SPs) to C# Models & DTOs
    - Implements Repository and Service Layer patterns
    - Discovers and refactors Stored Procedure calling methods
    - Suggests architectural improvements and prevents memory/connection leaks
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.CODE,
            persian_title="متخصص کد و معماری نرم‌افزار سپهریار",
            description="تحلیل کد پروژه، معماری لایه‌ای، نگاشت دیتابیس به کدهای C# / .NET، متدهای فراخوانی پروسیجر و ریفکتورینگ."
        )

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "تحلیل و تولید کد نرم‌افزار",
            f"طراحی مدل‌ها، لایه دسترسی به داده (DAL) و متدهای کلاینت/سرویس برای: '{task.goal}'"
        )

        query = task.goal.lower()
        findings: list[str] = []
        artifacts: dict[str, Any] = {}
        warnings: list[str] = []

        # Check blackboard for SP or tables
        sp_name = blackboard.agent_results.get(AgentRole.PROCEDURE.value, AgentResult(task_id="", role=AgentRole.PROCEDURE)).artifacts.get("sp_name", "usp_Sepehryar_Operation")
        db_res = blackboard.agent_results.get(AgentRole.DATABASE.value)
        target_tables = db_res.artifacts.get("target_tables", ["Master", "TblPerson"]) if db_res else ["Master", "TblPerson"]

        findings.append("الگوی لایه‌ای Clean Architecture / Repository Pattern برای اتصال به پایگاه داده سپهریار اعمال شد.")
        findings.append(f"تولید متد فراخوانی ایمن برای پروسیجر پایگاه داده: `{sp_name}` با مدیریت بسته شدن کانکشن‌ها (`using`).")

        # C# Enterprise Service & DTO implementation
        csharp_code = f"""// =====================================================================
// Sepehryar ERP Core - Enterprise Data Access Layer (C# / .NET)
// Feature: {task.goal}
// =====================================================================
using System;
using System.Data;
using Microsoft.Data.SqlClient;
using System.Threading.Tasks;

namespace Sepehryar.Core.Data
{{
    /// <summary>
    /// مدل داده‌ای خروجی عملیات در سیستم مالی سپهریار
    /// </summary>
    public class SepehryarOperationResult
    {{
        public bool IsSuccess {{ get; set; }}
        public int ResultCode {{ get; set; }}
        public string Message {{ get; set; }} = string.Empty;
    }}

    /// <summary>
    /// سرویس فراخوانی پروسیجرهای هسته سپهریار با مدیریت اتصال و بازگشت بهینه
    /// </summary>
    public class SepehryarDataService
    {{
        private readonly string _connectionString;

        public SepehryarDataService(string connectionString)
        {{
            _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));
        }}

        /// <summary>
        /// اجرای ایمن پروسیجر {sp_name} همراه با پارامترهای خروجی
        /// </summary>
        public async Task<SepehryarOperationResult> ExecuteOperationAsync(int operationCode, int userId, int fiscalYear)
        {{
            using var connection = new SqlConnection(_connectionString);
            using var command = new SqlCommand("dbo.{sp_name}", connection)
            {{
                CommandType = CommandType.StoredProcedure,
                CommandTimeout = 45 // ثانیه
            }};

            // تنظیم پارامترهای ورودی
            command.Parameters.Add("@OperationCode", SqlDbType.Int).Value = operationCode;
            command.Parameters.Add("@UserID", SqlDbType.Int).Value = userId;
            command.Parameters.Add("@FiscalYear", SqlDbType.Int).Value = fiscalYear;

            // تنظیم پارامترهای خروجی
            var resultCodeParam = new SqlParameter("@ResultCode", SqlDbType.Int)
            {{
                Direction = ParameterDirection.Output
            }};
            var messageParam = new SqlParameter("@ResultMessage", SqlDbType.NVarChar, 500)
            {{
                Direction = ParameterDirection.Output
            }};

            command.Parameters.Add(resultCodeParam);
            command.Parameters.Add(messageParam);

            try
            {{
                await connection.OpenAsync();
                await command.ExecuteNonQueryAsync();

                int code = (int)(resultCodeParam.Value ?? -1);
                string message = (string)(messageParam.Value ?? "نامشخص");

                return new SepehryarOperationResult
                {{
                    IsSuccess = (code == 0),
                    ResultCode = code,
                    Message = message
                }};
            }}
            catch (SqlException ex)
            {{
                // لاگ خطای اتصال یا اجرای SQL
                return new SepehryarOperationResult
                {{
                    IsSuccess = false,
                    ResultCode = ex.Number,
                    Message = $"خطای SQL Server: {{ex.Message}}"
                }};
            }}
        }}
    }}
}}
"""

        artifacts["generated_csharp_code"] = csharp_code
        blackboard.generated_code = csharp_code

        warnings.append("در لایه نرم‌افزار، مقادیر بازگشتی خطا (کدهای منفی) باید به پیام‌های قابل درک در رابط کاربر نگاشت شوند.")
        warnings.append("همواره از متدهای ناهمگام (Async) به همراه CommandTimeout کنترل‌شده استفاده کنید تا از فریز شدن فرم‌های ویندوزی کلاینت جلوگیری شود.")

        duration = (time.perf_counter() - start_time) * 1000
        summary = "طراحی معماری کد C# و کدهای دسترسی به داده بر اساس استاندارد Clean Code و مدیریت بهینه Connection به انجام رسید."

        result = AgentResult(
            task_id=task.task_id,
            role=self.role,
            success=True,
            summary=summary,
            findings=findings,
            artifacts=artifacts,
            warnings=warnings,
            execution_time_ms=round(duration, 2)
        )
        blackboard.record_result(result)
        return result
