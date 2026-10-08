"""
Knowledge and Export tools for the Sepehryar Agent tool registry.
"""
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.knowledge.search import knowledge_search_engine
from app.tools.export import data_exporter
from app.tools.registry import register_tool


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(description="عبارت یا واژه مورد جستجو در مستندات پایگاه دانش")
    category: Optional[str] = Field(default=None, description="دسته‌بندی (مثلاً database یا errors)")
    limit: int = Field(default=5, description="حداکثر تعداد نتایج")


class SearchKnowledgeBaseOutput(BaseModel):
    query: str
    total_found: int
    results: list[dict[str, Any]]


class ExportDataInput(BaseModel):
    format: str = Field(default="csv", description="فرمت خروجی: csv یا json")
    output_filename: str = Field(description="نام فایل خروجی (مثلاً customers.csv)")
    rows: list[dict[str, Any]] = Field(description="لیست رکوردها برای ذخیره‌سازی")


class ExportDataOutput(BaseModel):
    success: bool
    filepath: str
    total_rows: int
    format: str


@register_tool(
    name="search_knowledge_base",
    description="جستجوی محلی و آفلاین در مستندات پایگاه دانش، ساختار سرفصل‌ها و راهنماهای رفع خطا",
    category="knowledge",
    input_model=SearchKnowledgeBaseInput,
    output_model=SearchKnowledgeBaseOutput
)
def search_knowledge_base(query: str, category: Optional[str] = None, limit: int = 5) -> SearchKnowledgeBaseOutput:
    results = knowledge_search_engine.search(query, limit=limit, category=category)
    formatted = [
        {
            "doc_title": r.doc_title,
            "heading": r.heading,
            "category": r.category,
            "snippet": r.snippet,
            "score": r.score,
        }
        for r in results
    ]
    return SearchKnowledgeBaseOutput(
        query=query,
        total_found=len(results),
        results=formatted
    )


@register_tool(
    name="export_data",
    description="استخراج و ذخیره‌سازی آفلاین نتایج جدول یا کوئری در فرمت‌های CSV (با انکودینگ UTF-8 BOM مخصوص اکسل فارسی) یا JSON",
    category="export",
    input_model=ExportDataInput,
    output_model=ExportDataOutput
)
def export_data(format: str, output_filename: str, rows: list[dict[str, Any]]) -> ExportDataOutput:
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    target_path = export_dir / output_filename

    fmt = format.lower().strip()
    if fmt == "json":
        saved_path = data_exporter.export_to_json(rows, target_path)
    else:
        # Default to CSV
        saved_path = data_exporter.export_to_csv(rows, target_path)

    return ExportDataOutput(
        success=True,
        filepath=saved_path,
        total_rows=len(rows),
        format=fmt
    )
