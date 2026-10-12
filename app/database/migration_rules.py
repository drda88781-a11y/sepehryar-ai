"""
Migration Rules & Schema Mapping Engine:
Provides semantic contracts, polarity resolution, clean entity extraction,
and atomic validation for migrating accounting data into Sepehryar ERP.
"""
import re
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.core.logger import get_logger

logger = get_logger("database.migration_rules")


class MigrationValidationReport(BaseModel):
    is_valid: bool
    total_debit: int
    total_credit: int
    difference: int
    total_records: int
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CleanPersonContract(BaseModel):
    clean_name: str
    clean_famil: str = ""
    mobile: str = ""
    tell: str = ""
    type_code: int = 1  # 1=Customer, 2=Supplier, 3=Marketer, 4=Bank
    moin_code: int = 1  # 1 for customers, 2 for banks/cash
    srfsl_code: int = 110


class MigrationRulesEngine:
    """Intelligent ETL rules and validations tailored for Sepehryar ERP targets."""

    PHONE_REGEX = re.compile(r'(?:09\d{9}|0\d{10}|\b\d{7,8}\b)')
    MOBILE_REGEX = re.compile(r'(09\d{9})')

    @classmethod
    def detect_source_system(cls, table_or_column_names: list[str]) -> str:
        """Heuristically identify the legacy accounting source system."""
        names = {n.lower().strip() for n in table_or_column_names}

        # Holoo signatures
        if any("mandebed" in n or "hesab_moin" in n or "mandebes" in n for n in names):
            return "Holoo"
        # Mahak signatures
        if any("accdetailscollection" in n or "persondetails" in n for n in names):
            return "Mahak"
        # Baran 360 signatures
        if any("remainaccount" in n and "product" in n for n in names):
            return "Baran360"
        # Sepidar signatures
        if any("sls." in n or "acc.voucher" in n for n in names):
            return "Sepidar"
        # Excel generic
        return "Excel_or_Standard"

    @classmethod
    def resolve_polarity(
        cls,
        source_system: str,
        balance: Optional[float] = None,
        bed: Optional[float] = None,
        bes: Optional[float] = None
    ) -> tuple[int, int]:
        """
        Converts legacy balance into strictly positive atomic (Bed, Bes) for Sepehryar.
        """
        int_bed = int(bed or 0)
        int_bes = int(bes or 0)

        # If explicit Bed and Bes provided
        if int_bed > 0 or int_bes > 0:
            if int_bed >= int_bes:
                return (int_bed - int_bes, 0)
            else:
                return (0, int_bes - int_bed)

        # If signed balance provided
        bal = int(balance or 0)
        if source_system == "Baran360":
            # In Baran 360: RemainAccount < 0 is Debtor (بدهکار به ما)
            if bal < 0:
                return (abs(bal), 0)
            elif bal > 0:
                return (0, bal)
            return (0, 0)

        # Standard: Positive balance is Debtor (Bed), negative is Creditor (Bes)
        if bal > 0:
            return (bal, 0)
        elif bal < 0:
            return (0, abs(bal))
        return (0, 0)

    @classmethod
    def clean_person_fields(
        cls,
        raw_name: str,
        raw_mobile: Optional[str] = None,
        raw_tell: Optional[str] = None,
        is_bank: bool = False
    ) -> CleanPersonContract:
        """
        Separates embedded phone numbers from name, validates 11-digit mobile, and assigns Sepehryar Type.
        """
        name_str = str(raw_name or "").strip()
        mob_str = str(raw_mobile or "").strip()
        tel_str = str(raw_tell or "").strip()

        # Extract mobile numbers embedded inside name text
        embedded_phones = cls.MOBILE_REGEX.findall(name_str)
        if embedded_phones and not mob_str:
            mob_str = embedded_phones[0]
            name_str = cls.MOBILE_REGEX.sub("", name_str).strip()

        # Clean trailing landlines or noise from name
        name_str = re.sub(r'[\d\-–_]{4,}', '', name_str).strip()
        name_str = re.sub(r'\s+', ' ', name_str)

        # Clean mobile string
        mob_digits = re.sub(r'\D', '', mob_str)
        if len(mob_digits) == 10 and mob_digits.startswith("9"):
            mob_digits = "0" + mob_digits
        valid_mobile = mob_digits if len(mob_digits) == 11 and mob_digits.startswith("09") else ""

        # Clean landline
        tel_digits = re.sub(r'\D', '', tel_str)
        valid_tell = tel_digits if len(tel_digits) >= 7 else ""

        type_code = 4 if is_bank else 1
        moin_code = 2 if is_bank else 1
        srfsl_code = 100 if is_bank else 110

        return CleanPersonContract(
            clean_name=name_str or "بدون نام",
            mobile=valid_mobile,
            tell=valid_tell,
            type_code=type_code,
            moin_code=moin_code,
            srfsl_code=srfsl_code
        )

    @classmethod
    def validate_opening_balance(
        cls,
        records: list[dict[str, Any]]
    ) -> MigrationValidationReport:
        """
        Verifies 100% atomic equality between Total Debit and Total Credit for Opening Voucher.
        """
        total_bed = 0
        total_bes = 0
        errors = []
        warnings = []

        for idx, r in enumerate(records, start=1):
            bed = int(r.get("Bed") or r.get("bed") or 0)
            bes = int(r.get("Bes") or r.get("bes") or 0)

            if bed < 0 or bes < 0:
                errors.append(f"ردیف {idx}: مقادیر منفی در گردش بدهکار/بستانکار مجاز نیست.")
            if bed > 0 and bes > 0:
                warnings.append(f"ردیف {idx}: آرتیکل همزمان دارای بدهکار و بستانکار است؛ بهتر است تفکیک یا خالص‌سازی شود.")

            total_bed += bed
            total_bes += bes

        diff = abs(total_bed - total_bes)
        is_valid = (diff == 0) and len(errors) == 0

        if diff != 0:
            errors.append(f"عدم تراز سند افتتاحیه: جمع بدهکار ({total_bed:,}) با جمع بستانکار ({total_bes:,}) مغایرت دارد. اختلاف: {diff:,} ریال.")

        return MigrationValidationReport(
            is_valid=is_valid,
            total_debit=total_bed,
            total_credit=total_bes,
            difference=diff,
            total_records=len(records),
            errors=errors,
            warnings=warnings
        )

    @classmethod
    def validate_personcod_sync(
        cls,
        master_records: list[dict[str, Any]],
        person_ids: set[int]
    ) -> list[str]:
        """
        Verifies that every Master record with a personcod links to an existing TblPerson.Sh_ozviat.
        """
        orphan_errors = []
        for r in master_records:
            pc = r.get("personcod")
            hsb = r.get("HSB")
            if pc and int(pc) not in person_ids:
                orphan_errors.append(
                    f"حساب تفصیلی {hsb}: کد شخص {pc} در جدول TblPerson یافت نشد (ارتباط درختی شکسته است)."
                )
        return orphan_errors


migration_engine = MigrationRulesEngine()
