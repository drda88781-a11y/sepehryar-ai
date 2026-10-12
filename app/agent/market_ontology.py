"""
Semantic Market Ontology: translates colloquial Persian bazaar and business terms
into accurate accounting concepts, database entities, and filter parameters.
"""
import re
from typing import Optional
from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    category: str  # 'person', 'product', 'bank', 'cheque', 'time', 'metric'
    original_term: str
    normalized_value: str
    confidence: float = 0.9


class SemanticIntent(BaseModel):
    concept: str  # e.g., 'person_balance', 'bank_balance', 'cheque_status', 'inventory_stock', 'profit_margin'
    sub_concept: Optional[str] = None
    extracted_names: list[str] = Field(default_factory=list)
    extracted_codes: list[int] = Field(default_factory=list)
    time_filter: Optional[str] = None
    numeric_condition: Optional[str] = None


class MarketOntologyParser:
    """Parses natural language financial questions into structured accounting intents."""

    BANK_KEYWORDS = {
        "صادرات": "صادرات",
        "ملت": "ملت",
        "ملی": "ملی",
        "سامان": "سامان",
        "تجارت": "تجارت",
        "سپه": "سپه",
        "پاسارگاد": "پاسارگاد",
        "پارسیان": "پارسیان",
        "کشاورزی": "کشاورزی",
        "مسکن": "مسکن",
        "رفاه": "رفاه",
        "صندوق": "صندوق",
    }

    CHEQUE_STATUS_KEYWORDS = {
        "برگشتی": "bargashti",
        "واخواست": "bargashti",
        "پاس شده": "passed",
        "وصول شده": "passed",
        "وصول نشده": "pending",
        "نزد صندوق": "in_hand",
        "در جریان": "in_collection",
        "خوابیده به حساب": "in_collection",
        "خرج شده": "spent",
    }

    PERSON_TITLE_PREFIXES = [
        "آقای", "اقای", "خانم", "جناب", "شرکت", "فروشگاه", "هایپر", "بازرگانی", "مشتری", "همکار"
    ]

    @classmethod
    def clean_person_name(cls, query: str) -> Optional[str]:
        """Extract person or company name from natural language query."""
        # Find phrases after common keywords like 'حساب', 'گردش', 'مانده', 'فلانی', 'به'
        patterns = [
            r"(?:حساب|گردش|مانده|صورتحساب|طرف\s*حساب|طلب|بدهی|فاکتورهای)\s+([^\d\?؟!،]+)",
            r"(?:به|از)\s+([^\d\?؟!،]+?)(?:\s+(?:چقدر|بدهکار|طلبکار|داره|هست))",
        ]
        for pat in patterns:
            m = re.search(pat, query)
            if m:
                raw = m.group(1).strip()
                # Remove titles
                for pfx in cls.PERSON_TITLE_PREFIXES:
                    raw = re.sub(rf"^{pfx}\s+", "", raw).strip()
                # Stop at common verbs or stop-words
                raw = re.split(r"\s+(?:چقدر|چند|چیه|است|رو|را|در|با|برای|سال)\b", raw)[0].strip()
                if len(raw) > 2 and not any(w in raw for w in ["کالا", "انبار", "بانک", "چک", "فروش", "سود"]):
                    return raw
        return None

    @classmethod
    def parse_query(cls, query: str) -> SemanticIntent:
        """Analyze query and classify into detailed accounting concept."""
        q_norm = query.replace("ي", "ی").replace("ك", "ک").strip()
        q_lower = q_norm.lower()

        extracted_names: list[str] = []
        extracted_codes: list[int] = []

        # Find account / customer code if mentioned
        code_matches = re.findall(r"\b(\d{3,6})\b", q_norm)
        for c in code_matches:
            if not c.startswith("140"):  # skip years like 1403, 1405
                extracted_codes.append(int(c))

        # Check for Bank balances
        if any(w in q_lower for w in ["بانک", "حساب بانکی", "موجودی بانک", "نقد و بانک", "صندوق"]):
            matched_bank = None
            for b_key, b_val in cls.BANK_KEYWORDS.items():
                if b_key in q_lower:
                    matched_bank = b_val
                    break
            return SemanticIntent(
                concept="bank_balance",
                sub_concept=matched_bank or "all_banks",
                extracted_names=[matched_bank] if matched_bank else []
            )

        # Check for Cheques
        if any(w in q_lower for w in ["چک", "چکها", "صیاد", "صیادی", "اسناد دریافتنی", "اسناد پرداختنی"]):
            sub = "all"
            for k_fa, k_en in cls.CHEQUE_STATUS_KEYWORDS.items():
                if k_fa in q_lower:
                    sub = k_en
                    break
            is_payment = any(w in q_lower for w in ["پرداختی", "صادره", "دادیم", "کشیدیم"])
            return SemanticIntent(
                concept="cheques_paid" if is_payment else "cheques_received",
                sub_concept=sub
            )

        # Check for Person Turnover / Balance
        person_name = cls.clean_person_name(q_norm)
        if person_name:
            extracted_names.append(person_name)

        if any(w in q_lower for w in ["طلبکار", "بدهکار", "بستانکار", "تامین کننده", "تأمین کننده", "مانده حساب", "گردش حساب", "صورتحساب", "چقدر بدهکاره", "چقدر طلبکاره", "چقدر بستانکاره"]):
            if extracted_names or extracted_codes:
                return SemanticIntent(
                    concept="specific_person_balance",
                    extracted_names=extracted_names,
                    extracted_codes=extracted_codes
                )
            elif any(w in q_lower for w in ["طلبکار", "بستانکار", "تامین کننده", "تأمین کننده"]):
                return SemanticIntent(concept="top_creditors")
            else:
                return SemanticIntent(concept="top_debtors")

        # Check for Profit & Margins
        if any(w in q_lower for w in ["سود", "سود ناخالص", "حاشیه سود", "زیان", "سودده ترین", "سودآوری"]):
            return SemanticIntent(concept="profit_and_margins")

        # Check for Opening Voucher / Trial Balance
        if any(w in q_lower for w in ["تراز افتتاحیه", "سند افتتاحیه", "اول دوره", "تراز آزمایشی", "تراز کل", "تراز معین"]):
            return SemanticIntent(concept="trial_balance_or_opening")

        # Check for Inventory & Product Stock
        if any(w in q_lower for w in ["موجودی", "انبار", "کالا", "کالاها", "اجناس", "اتمام موجودی", "ناموجود", "ته انبار", "خاک خورده", "راکد", "پرفروش"]):
            sub = "available"
            if any(w in q_lower for w in ["اتمام", "ناموجود", "صفر", "تموم", "ندارن", "نداره", "فاقد موجودی", "بدون موجودی"]):
                sub = "out_of_stock"
            elif any(w in q_lower for w in ["کم", "حداقل", "کسری"]):
                sub = "low_stock"
            elif any(w in q_lower for w in ["راکد", "خاک خورده", "ته انبار", "بدون فروش"]):
                sub = "slow_moving"
            elif any(w in q_lower for w in ["پرفروش", "بیشترین فروش"]):
                sub = "top_selling"
            return SemanticIntent(
                concept="inventory_stock",
                sub_concept=sub
            )

        # Check for Invoices & Sales
        if any(w in q_lower for w in ["فروش", "فاکتور", "تراکنش", "خرید"]):
            return SemanticIntent(concept="sales_invoices")

        return SemanticIntent(concept="general_query")
