"""
Custom domain exceptions with dual-layer messages (User-Friendly Persian + Technical Details).
"""
from typing import Optional, Any


class SepehryarBaseException(Exception):
    """
    Base exception for all Sepehryar AI Engine errors.
    Ensures users receive helpful Persian instructions while preserving full technical details for logs.
    """
    def __init__(
        self,
        user_message: str,
        technical_details: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        self.user_message = user_message
        self.technical_details = technical_details or (str(original_exception) if original_exception else "")
        self.original_exception = original_exception
        self.context = context or {}
        super().__init__(f"{user_message} | Technical: {self.technical_details}")


class DatabaseConnectionError(SepehryarBaseException):
    """Raised when connecting to SQL Server fails."""
    def __init__(
        self,
        user_message: str = "ارتباط با سرور پایگاه داده برقرار نشد. لطفاً وضعیت سرویس SQL Server و مشخصات اتصال را بررسی کنید.",
        technical_details: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, original_exception, context)


class DatabaseScanError(SepehryarBaseException):
    """Raised when scanning schema objects fails."""
    def __init__(
        self,
        user_message: str = "خطا در اسکن ساختار دیتابیس رخ داد. امکان استخراج کامل جداول یا روابط وجود ندارد.",
        technical_details: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, original_exception, context)


class QueryExecutionError(SepehryarBaseException):
    """Raised when safe SQL execution fails."""
    def __init__(
        self,
        user_message: str = "اجرای کوئری در پایگاه داده با خطا مواجه شد.",
        technical_details: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, original_exception, context)


class SafeSQLViolationError(SepehryarBaseException):
    """Raised when a query violates read-only or security rules."""
    def __init__(
        self,
        user_message: str = "دستور SQL به دلیل نقض قوانین ایمنی و مجوز فقط-خواندنی مسدود شد.",
        technical_details: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, context=context)


class SecurityViolationError(SepehryarBaseException):
    """Raised on security violation (unauthorized access, token mismatch, forbidden keyword)."""
    def __init__(
        self,
        user_message: str = "عملیات به دلیل محدودیت‌های امنیتی لغو شد.",
        technical_details: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, context=context)


class OfflineViolationError(SepehryarBaseException):
    """Raised when an attempt to connect to external internet is blocked."""
    def __init__(
        self,
        user_message: str = "ارتباط خارجی مسدود است. سامانه در حالت ۱۰۰٪ آفلاین و محلی اجرا می‌شود.",
        technical_details: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, context=context)


class StorageError(SepehryarBaseException):
    """Raised when SQLite storage operations fail."""
    def __init__(
        self,
        user_message: str = "خطا در ذخیره‌سازی داده‌های محلی سامانه رخ داد.",
        technical_details: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, original_exception, context)


class ConfigurationError(SepehryarBaseException):
    """Raised when invalid configuration is detected."""
    def __init__(
        self,
        user_message: str = "تنظیمات سامانه نامعتبر است. لطفاً فایل تنظیمات را بازبینی فرمایید.",
        technical_details: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(user_message, technical_details, context=context)
