"""
Deterministic diagnostic rule engine checking SQL Server services, ports,
disk space, memory, and database responsiveness.
"""
from enum import Enum
from typing import Any, Optional
import psutil
from pydantic import BaseModel, Field
from app.config.settings import settings
from app.core.logger import get_logger
from app.database.connection import db_connection_manager

logger = get_logger("diagnostics")


class SystemHealthStatus(str, Enum):
    HEALTHY = "healthy"      # Green
    WARNING = "warning"      # Amber
    CRITICAL = "critical"    # Red


class CheckItemResult(BaseModel):
    title: str
    status: SystemHealthStatus
    value: str
    message: str
    recommendation: Optional[str] = None


class DiagnosticReport(BaseModel):
    overall_status: SystemHealthStatus
    checks: list[CheckItemResult] = Field(default_factory=list)
    warnings_count: int = 0
    critical_count: int = 0


def check_cpu_and_ram() -> list[CheckItemResult]:
    """Check CPU utilization and available RAM."""
    results = []
    # CPU
    cpu_pct = psutil.cpu_percent(interval=0.2)
    cpu_status = SystemHealthStatus.HEALTHY
    rec = None
    if cpu_pct > 90:
        cpu_status = SystemHealthStatus.CRITICAL
        rec = "مصرف پردازنده بسیار بالاست. پردازش‌های سنگین روی سرور را متوقف کنید."
    elif cpu_pct > 75:
        cpu_status = SystemHealthStatus.WARNING
        rec = "بار پردازشی نسبتاً زیاد است."

    results.append(CheckItemResult(
        title="مصرف پردازنده (CPU)",
        status=cpu_status,
        value=f"{cpu_pct}%",
        message="وضعیت پردازنده عادی است." if cpu_status == SystemHealthStatus.HEALTHY else "فشار پردازشی بالا",
        recommendation=rec
    ))

    # RAM
    mem = psutil.virtual_memory()
    used_gb = round(mem.used / (1024**3), 1)
    total_gb = round(mem.total / (1024**3), 1)
    ram_pct = mem.percent
    ram_status = SystemHealthStatus.HEALTHY
    ram_rec = None
    if ram_pct > 90:
        ram_status = SystemHealthStatus.CRITICAL
        ram_rec = "حافظه RAM سرور تقریباً پر شده است. ممکن است عملکرد SQL Server کند شود."
    elif ram_pct > 80:
        ram_status = SystemHealthStatus.WARNING
        ram_rec = "مصرف حافظه بالا است."

    results.append(CheckItemResult(
        title="حافظه موقت (RAM)",
        status=ram_status,
        value=f"{used_gb} GB از {total_gb} GB ({ram_pct}%)",
        message="میزان حافظه آزاد کافی است." if ram_status == SystemHealthStatus.HEALTHY else "کمبود حافظه موقت",
        recommendation=ram_rec
    ))
    return results


def check_disk_space() -> list[CheckItemResult]:
    """Check free space on system and database drives."""
    results = []
    # Check drive C: and D: (where database files reside)
    for drive in ["C:\\", "D:\\"]:
        try:
            usage = psutil.disk_usage(drive)
            free_gb = round(usage.free / (1024**3), 1)
            total_gb = round(usage.total / (1024**3), 1)
            used_pct = usage.percent

            status = SystemHealthStatus.HEALTHY
            rec = None
            if free_gb < 5:
                status = SystemHealthStatus.CRITICAL
                rec = f"فضای آزاد درایو {drive} کمتر از ۵ گیگابایت است! خطر توقف نوشتن فایل‌های LDF/MDF پایگاه داده."
            elif free_gb < 15 or used_pct > 85:
                status = SystemHealthStatus.WARNING
                rec = f"فضای آزاد درایو {drive} رو به اتمام است. فایل‌های لاگ یا بک‌آپ‌های قدیمی را پاکسازی کنید."

            results.append(CheckItemResult(
                title=f"فضای دیسک (درایو {drive[:2]})",
                status=status,
                value=f"{free_gb} GB آزاد از {total_gb} GB",
                message=f"درایو دارای {free_gb} GB فضای خالی است.",
                recommendation=rec
            ))
        except Exception:
            continue
    return results


def check_sql_service_status() -> CheckItemResult:
    """Check if SQL Server Windows Service is running."""
    service_names = [
        f"MSSQL${settings.sql_instance}" if settings.sql_instance else None,
        "MSSQLSERVER",
        "MSSQL$SEPEHRYAR2019",
        "MSSQL$SQLEXPRESS",
    ]
    service_names = [s for s in service_names if s]

    found_service = None
    for name in service_names:
        try:
            svc = psutil.win_service_get(name)
            found_service = svc
            break
        except Exception:
            continue

    if not found_service:
        # Check by searching any service with MSSQL
        for svc in psutil.win_service_iter():
            if "mssql" in svc.name().lower():
                found_service = svc
                break

    if not found_service:
        return CheckItemResult(
            title="سرویس SQL Server در ویندوز",
            status=SystemHealthStatus.WARNING,
            value="نامشخص / سرویس پیش‌فرض یافت نشد",
            message="سرویس محلی پیدا نشد (ممکن است روی سرور راه دور شبکه باشد).",
            recommendation="در صورت نصب محلی، سرویس SQL Server را در services.msc بررسی فرمایید."
        )

    status_str = found_service.status()
    if status_str == "running":
        return CheckItemResult(
            title="سرویس SQL Server در ویندوز",
            status=SystemHealthStatus.HEALTHY,
            value=f"فعال ({found_service.name()})",
            message="سرویس پایگاه داده در ویندوز در حال اجرا است."
        )
    else:
        return CheckItemResult(
            title="سرویس SQL Server در ویندوز",
            status=SystemHealthStatus.CRITICAL,
            value=f"متوقف ({status_str})",
            message=f"سرویس {found_service.name()} متوقف شده است.",
            recommendation="سرویس SQL Server را در کنترل پنل ویندوز یا با دستور 'net start' راه‌اندازی کنید."
        )


def check_sql_database_connection() -> CheckItemResult:
    """Check direct queryable connectivity to target SQL Server database."""
    ok, msg, _ = db_connection_manager.test_connection(
        server=settings.sql_server,
        database=settings.sql_database
    )
    if ok:
        return CheckItemResult(
            title="ارتباط با دیتابیس سپهریار",
            status=SystemHealthStatus.HEALTHY,
            value="متصل (OK)",
            message=f"اتصال به '{settings.sql_database}' برقرار است."
        )
    else:
        return CheckItemResult(
            title="ارتباط با دیتابیس سپهریار",
            status=SystemHealthStatus.CRITICAL,
            value="قطع ارتباط",
            message=msg,
            recommendation="نام سرور، دیتابیس، نام کاربری یا مجوز دسترسی Windows Auth را بررسی کنید."
        )


def run_full_system_diagnosis() -> DiagnosticReport:
    """Run all health checks and aggregate status."""
    checks = []
    checks.extend(check_cpu_and_ram())
    checks.extend(check_disk_space())
    checks.append(check_sql_service_status())
    checks.append(check_sql_database_connection())

    criticals = sum(1 for c in checks if c.status == SystemHealthStatus.CRITICAL)
    warnings = sum(1 for c in checks if c.status == SystemHealthStatus.WARNING)

    overall = SystemHealthStatus.HEALTHY
    if criticals > 0:
        overall = SystemHealthStatus.CRITICAL
    elif warnings > 0:
        overall = SystemHealthStatus.WARNING

    return DiagnosticReport(
        overall_status=overall,
        checks=checks,
        warnings_count=warnings,
        critical_count=criticals
    )
