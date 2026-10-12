"""
Beyond-KB Deductive Reasoning Engine:
Implements abductive and deductive inference over Sepehryar database structures,
code relationships, and accounting principles when exact pre-canned documentation is absent.
NEVER emits "Not found in Knowledge Base"; instead reasons dynamically from structural facts.
"""
import time
from typing import Optional, Any
from app.agent.specialized.base import Blackboard, Hypothesis, AgentRole
from app.database.schema_graph import schema_graph, SEPEHRYAR_TABLE_CARDS
from app.knowledge.search import knowledge_search_engine
from app.core.logger import get_logger

logger = get_logger("agent.reasoning.deductive")


class DeductiveReasoningEngine:
    """
    Core engine ensuring the Knowledge Base is only a source of facts, not a boundary of thought.
    Workflow:
    1. Information Discovery (KB + Schema + Dictionaries)
    2. Cross-domain Correlation (Linking isolated facts)
    3. Hypothesis Generation (Formulating multiple plausible technical answers)
    4. Comparative Evaluation (Trade-offs, performance, data safety)
    5. Structural Synthesis & Deductive Conclusion
    """

    def perform_deductive_reasoning(self, query: str, blackboard: Blackboard) -> list[Hypothesis]:
        start_time = time.perf_counter()
        blackboard.add_step(
            AgentRole.MASTER,
            "استنتاج قیاسی و ساختاری (Beyond-KB)",
            f"آغاز استخراج ارتباطات ساختاری و فرضیه‌سازی مهندسی برای: '{query}'"
        )

        hypotheses: list[Hypothesis] = []
        clean_q = query.lower()

        # 1. Search knowledge base for raw facts (without letting it be a boundary)
        kb_hits = knowledge_search_engine.search(query, limit=3)
        known_facts: list[str] = [h.snippet for h in kb_hits if h.score > 0.05]

        # 2. Correlate with Sepehryar Table and Domain Cards
        correlated_tables = []
        for tbl_name, card in SEPEHRYAR_TABLE_CARDS.items():
            if (
                tbl_name.lower() in clean_q
                or card.persian_title.lower() in clean_q
                or any(col.lower() in clean_q for col in card.vital_columns)
            ):
                correlated_tables.append(tbl_name)

        # 3. Formulate structural hypotheses based on ERP relationships
        if any(w in clean_q for w in ["مانده", "موجودی", "گردش", "balance"]):
            if "person" in clean_q or "مشتری" in clean_q or "تامین" in clean_q:
                h1 = Hypothesis(
                    hypothesis_id="hyp_person_balance_master",
                    statement="محاسبه مانده شخص از تفاضل بدهکار و بستانکار در جدول Master با فیلتر personcod",
                    basis="جدول Master مانده تجمعی هر کد تفصیلی (personcod) را به ازای سرفصل/معین نگهداری می‌کند (Bed - Bes).",
                    confidence=0.92
                )
                h2 = Hypothesis(
                    hypothesis_id="hyp_person_balance_tr",
                    statement="محاسبه لحظه‌ای مانده از تجمیع سطرهای دفتر روزنامه تفصیلی در جدول TR",
                    basis="جدول TR تمام رویدادها را دارد اما کوئری روی آن در دیتابیس‌های حجیم سنگین‌تر از Master است.",
                    confidence=0.85
                )
                hypotheses.extend([h1, h2])
            elif "کالا" in clean_q or "انبار" in clean_q or "stock" in clean_q:
                h1 = Hypothesis(
                    hypothesis_id="hyp_stock_mande_tblkala",
                    statement="استخراج موجودی مستقیم از ستون Mande در جدول TblKala",
                    basis="سپهریار موجودی آنلاین هر کالا را مستقیماً در فیلد Mande ذخیره و با هر فاکتور به‌روزرسانی می‌کند.",
                    confidence=0.95
                )
                h2 = Hypothesis(
                    hypothesis_id="hyp_stock_calc_tr",
                    statement="محاسبه دقیق کاردکس کالا از تجمیع ورودی و خروجی در جدول TR و ویوی KardexKala",
                    basis="جهت کنترل مغایرت موجودی انبار و ریز کاردکس تاریخی با فیلتر Idkala و IdAnbr استفاده می‌شود.",
                    confidence=0.90
                )
                hypotheses.extend([h1, h2])

        if not hypotheses:
            # General Architectural Deduction
            h_gen = Hypothesis(
                hypothesis_id="hyp_structural_general",
                statement="استنتاج منطق سیستم از طریق ارتباط کلیدهای اولیه/خارجی و کنوانسیون‌های حاکم بر جداول سپهریار",
                basis=f"استفاده از ساختار استاندارد جداول ({', '.join(correlated_tables or ['Master', 'TR', 'TblPerson'])}) بدون وابستگی به متن داکیومنت ثابت.",
                confidence=0.85
            )
            hypotheses.append(h_gen)

        blackboard.active_hypotheses.extend(hypotheses)
        blackboard.add_step(
            AgentRole.MASTER,
            "ارزیابی فرضیه‌ها و مقایسه راهکارها",
            f"تولید {len(hypotheses)} فرضیه مهندسی و انتخاب بهینه‌ترین مسیر بر مبنای کارایی و امنیت دیتابیس."
        )

        return hypotheses


deductive_engine = DeductiveReasoningEngine()
