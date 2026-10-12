"""
Tests for Dual-Mode Cognitive Behavior:
1. User Guide / Operational Mode: Manual tutorials with embedded screenshots, ZERO SQL/C# code.
2. Direct Programming Mode: Production-grade T-SQL stored procedures without conversational filler.
"""
import pytest
from app.agent.orchestrator import agent_orchestrator
from app.agent.cognitive_engine import cognitive_engine


@pytest.mark.parametrize("query,expected_keyword,expected_image", [
    ("تعریف کالا", "انبارداری", "anbar_img4_taarife_kala.png"),
    ("نحوه تعریف انبار چگونه است؟", "تعریف انبار", "anbar_img3_form_anbar.png"),
    ("باجه ثبت سند در سپهریار چیست؟", "باجه ثبت سند", "vizhe_image2.png"),
    ("مغایرت بانکی چطور گرفته میشه؟", "رفع مغایرت بانکی", "vizhe_image18.png"),
    ("جستجوی سند با F10", "F10", "vizhe_image3.png"),
    ("محاسبه استهلاک دارایی", "استهلاک", "vizhe_image12.png"),
    ("دریافت وجه", "فرم دریافت وجه", "vizhe_image28.png"),
    ("پرداخت وجه و دستور پرداخت چک", "دستور پرداخت چک", "vizhe_image25.png"),
    ("انتقال وجه بین حساب‌ها", "انتقال وجه", "vizhe_image32.png"),
    ("عملیات پایان روز و تایید اسناد", "پایان روز", "vizhe_image17.png"),
])
def test_user_guide_operational_mode(query, expected_keyword, expected_image):
    """Verifies that operational queries return visual tutorials with images and ZERO SQL code."""
    res = agent_orchestrator.process_query(query)
    answer = res.persian_answer

    # Must contain expected operational guidance
    assert expected_keyword in answer
    # Must contain the relevant screenshot link
    assert expected_image in answer
    assert "file:///d:/ai%20app/knowledge_base/manuals/images/" in answer

    # STRICT RULE: Must NOT contain programming SQL instructions
    assert "INSERT INTO" not in answer
    assert "CREATE TABLE" not in answer
    assert "ALTER TABLE" not in answer


def test_direct_code_procedure_mode():
    """Verifies that procedure requests return direct production T-SQL without filler."""
    query = "یک پروسیجر برای لیست مشتریان بدهکار بنویس"
    res = agent_orchestrator.process_query(query)
    answer = res.persian_answer

    # Must contain direct procedure code
    assert "CREATE OR ALTER PROCEDURE dbo.usp_GetDebtorCustomers" in answer
    assert "Master" in answer
    assert "TblPerson" in answer
    assert "personcod" in answer

    # Must NOT have conversational essays or multi-agent brainstorm chatter
    assert "## 🧠 راهکار مهندسی Sepehryar AI Core" not in answer
    assert "Beyond-KB Inference" not in answer
