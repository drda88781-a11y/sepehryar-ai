"""
Database relationships extraction (both declared SQL Server Foreign Keys and inferred heuristics).
"""
from typing import Any
import pyodbc
from app.core.logger import get_logger
from app.database.metadata import RelationshipMetadata, TableMetadata

logger = get_logger("relationships")

SQL_FOREIGN_KEYS_QUERY = """
SELECT 
    fk.name AS fk_name,
    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS source_schema,
    OBJECT_NAME(fk.parent_object_id) AS source_table,
    c_src.name AS source_column,
    OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS target_schema,
    OBJECT_NAME(fk.referenced_object_id) AS target_table,
    c_trg.name AS target_column
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.columns c_src ON fkc.parent_object_id = c_src.object_id AND fkc.parent_column_id = c_src.column_id
INNER JOIN sys.columns c_trg ON fkc.referenced_object_id = c_trg.object_id AND fkc.referenced_column_id = c_trg.column_id
ORDER BY source_table, fk_name;
"""


def extract_declared_relationships(conn: pyodbc.Connection) -> list[RelationshipMetadata]:
    """Query SQL Server sys catalog for declared foreign key constraints."""
    relationships: dict[str, RelationshipMetadata] = {}
    cursor = conn.cursor()
    try:
        cursor.execute(SQL_FOREIGN_KEYS_QUERY)
        for row in cursor.fetchall():
            fk_name = row.fk_name
            src_table = row.source_table
            src_col = row.source_column
            trg_table = row.target_table
            trg_col = row.target_column

            if fk_name not in relationships:
                relationships[fk_name] = RelationshipMetadata(
                    fk_name=fk_name,
                    source_table=src_table,
                    source_columns=[src_col],
                    target_table=trg_table,
                    target_columns=[trg_col],
                    is_inferred=False,
                    description=f"رابطه کلید خارجی رسمی: {src_table}.{src_col} -> {trg_table}.{trg_col}"
                )
            else:
                rel = relationships[fk_name]
                if src_col not in rel.source_columns:
                    rel.source_columns.append(src_col)
                if trg_col not in rel.target_columns:
                    rel.target_columns.append(trg_col)
    except Exception as e:
        logger.warning(f"Could not extract declared foreign keys: {e}")
    return list(relationships.values())


def infer_relationships_heuristically(
    tables: dict[str, TableMetadata],
    declared_relationships: list[RelationshipMetadata]
) -> list[RelationshipMetadata]:
    """
    Detect likely unconstrained relationships across Sepehryar tables.
    In ERPs, developers often omit formal FK constraints for speed, but follow column naming patterns.
    """
    declared_pairs = {
        (r.source_table.lower(), r.target_table.lower(), tuple(c.lower() for c in r.source_columns))
        for r in declared_relationships
    }

    inferred: list[RelationshipMetadata] = []
    # Identify primary key columns across all tables
    pk_map: dict[str, tuple[str, str]] = {}  # pk_name_lower -> (table_name, original_pk_name)
    for tbl_name, tbl_meta in tables.items():
        for pk in tbl_meta.primary_keys:
            pk_lower = pk.lower()
            if pk_lower not in pk_map:
                pk_map[pk_lower] = (tbl_name, pk)

    for tbl_name, tbl_meta in tables.items():
        for col_name, col_meta in tbl_meta.columns.items():
            col_lower = col_name.lower()
            # If this column matches a primary key in another table
            if col_lower in pk_map:
                target_table, target_pk = pk_map[col_lower]
                if target_table.lower() != tbl_name.lower():
                    pair_key = (tbl_name.lower(), target_table.lower(), (col_lower,))
                    if pair_key not in declared_pairs:
                        inferred.append(
                            RelationshipMetadata(
                                fk_name=f"INFERRED_{tbl_name}_{col_name}_{target_table}",
                                source_table=tbl_name,
                                source_columns=[col_name],
                                target_table=target_table,
                                target_columns=[target_pk],
                                is_inferred=True,
                                description=f"رابطه تخمینی (نام ستون همسان): {tbl_name}.{col_name} -> {target_table}.{target_pk}"
                            )
                        )
    return inferred
