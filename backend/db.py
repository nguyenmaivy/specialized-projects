import os
import logging
import socket
import uuid
import json
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _build_dsn() -> Optional[str]:
    # Ưu tiên 1: Dùng POSTGRES_DSN nếu có trong .env
    dsn = os.getenv("POSTGRES_DSN")
    if dsn:
        return dsn

    # Ưu tiên 2: Dùng biến môi trường (dành cho Docker)
    host = os.getenv("POSTGRES_HOST")
    if host:
        # If the configured host cannot be resolved on this machine (e.g. 'postgres'
        # when running outside Docker), fall back to localhost so local dev works.
        try:
            socket.getaddrinfo(host, int(os.getenv("POSTGRES_PORT", "5432")))
        except Exception:
            logging.getLogger(__name__).warning(
                "POSTGRES_HOST '%s' cannot be resolved locally; falling back to 'localhost'",
                host,
            )
            host = "localhost"

        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "sales_dashboard")
        user = os.getenv("POSTGRES_USER", "sales_user")
        password = os.getenv("POSTGRES_PASSWORD", "123456")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

    # Ưu tiên 3: Chạy local trên Windows/Mac (không Docker) → dùng localhost
    # Bạn có thể đổi sang "127.0.0.1" nếu localhost không hoạt động
    return f"postgresql+psycopg://sales_user:123456@localhost:5432/sales_dashboard"


_dsn = _build_dsn()
ENGINE: Optional[Engine] = create_engine(_dsn, pool_pre_ping=True) if _dsn else None


def is_db_enabled() -> bool:
    return ENGINE is not None


def init_db() -> None:
    if ENGINE is None:
        return

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS datasets (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            source_type TEXT NOT NULL CHECK (source_type IN ('file', 'postgres', 'seed')),
            created_by TEXT,
            is_active BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES datasets(id),
            source_details JSONB NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'succeeded', 'failed')),
            row_count BIGINT,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS column_mappings (
            id UUID PRIMARY KEY,
            ingestion_run_id UUID NOT NULL REFERENCES ingestion_runs(id),
            mapping_json JSONB NOT NULL,
            confidence_overall NUMERIC,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orders_fact (
            dataset_id UUID NOT NULL REFERENCES datasets(id),
            order_id TEXT NOT NULL,
            order_date DATE NOT NULL,
            customer_id TEXT NOT NULL,
            customer_name TEXT,
            region TEXT NOT NULL,
            category TEXT NOT NULL,
            sales NUMERIC NOT NULL,
            profit NUMERIC,
            discount NUMERIC,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (dataset_id, order_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES datasets(id),
            filters_json JSONB NOT NULL,
            computed_kpis_json JSONB,
            sales_trend_json JSONB,
            category_sales_json JSONB,
            region_sales_json JSONB,
            forecast_json JSONB,
            rfm_json JSONB,
            status TEXT NOT NULL DEFAULT 'succeeded',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS analysis_widgets (
            id UUID PRIMARY KEY,
            analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id),
            widget_type TEXT NOT NULL CHECK (widget_type IN ('insight', 'risk', 'what_if')),
            severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
            title TEXT NOT NULL,
            content_markdown TEXT NOT NULL,
            evidence_json JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_orders_fact_dataset_order_date ON orders_fact(dataset_id, order_date)",
        "CREATE INDEX IF NOT EXISTS idx_orders_fact_dataset_region ON orders_fact(dataset_id, region)",
        "CREATE INDEX IF NOT EXISTS idx_orders_fact_dataset_category ON orders_fact(dataset_id, category)",
        "CREATE INDEX IF NOT EXISTS idx_orders_fact_dataset_customer ON orders_fact(dataset_id, customer_id)",
        """
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id UUID PRIMARY KEY,
            dataset_id UUID REFERENCES datasets(id),
            source_filename TEXT NOT NULL,
            chunk_index INT NOT NULL DEFAULT 0,
            content_text TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_knowledge_docs_dataset ON knowledge_documents(dataset_id)",
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id UUID PRIMARY KEY,
            analysis_run_id UUID REFERENCES analysis_runs(id),
            user_message TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_chat_history_analysis_run ON chat_history(analysis_run_id)",
    ]

    with ENGINE.begin() as conn:
        for stmt in ddl_statements:
            conn.execute(text(stmt))


def get_active_dataset_id() -> Optional[str]:
    if ENGINE is None:
        return None
    with ENGINE.begin() as conn:
        result = conn.execute(
            text("SELECT id::text FROM datasets WHERE is_active = TRUE ORDER BY created_at DESC LIMIT 1")
        ).scalar()
    return result


def set_active_dataset(dataset_id: str) -> None:
    if ENGINE is None:
        return
    with ENGINE.begin() as conn:
        conn.execute(text("UPDATE datasets SET is_active = FALSE WHERE is_active = TRUE"))
        conn.execute(
            text("UPDATE datasets SET is_active = TRUE WHERE id = :dataset_id"),
            {"dataset_id": dataset_id},
        )


def create_dataset(name: str, source_type: str, created_by: str = "system", is_active: bool = False) -> str:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    dataset_id = str(uuid.uuid4())
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO datasets (id, name, source_type, created_by, is_active)
                VALUES (:id, :name, :source_type, :created_by, :is_active)
                """
            ),
            {
                "id": dataset_id,
                "name": name,
                "source_type": source_type,
                "created_by": created_by,
                "is_active": is_active,
            },
        )
    return dataset_id


def get_dataset_by_name(name: str) -> Optional[Dict[str, Any]]:
    if ENGINE is None:
        return None
    with ENGINE.begin() as conn:
        row = conn.execute(
            text("SELECT id::text AS id, name, source_type, is_active FROM datasets WHERE name = :name LIMIT 1"),
            {"name": name},
        ).mappings().first()
    return dict(row) if row else None


def list_datasets(limit: int = 50) -> List[Dict[str, Any]]:
    """List datasets (debug / UI inspection)."""
    if ENGINE is None:
        return []
    try:
        with ENGINE.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id::text AS id, name, source_type, is_active, created_at
                    FROM datasets
                    ORDER BY created_at DESC
                    LIMIT :lim
                    """
                ),
                {"lim": limit},
            ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []


def insert_orders(dataset_id: str, df: pd.DataFrame) -> int:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")

    required_columns = [
        "order_id",
        "order_date",
        "customer_id",
        "customer_name",
        "region",
        "category",
        "sales",
        "profit",
        "discount",
    ]
    for column in required_columns:
        if column not in df.columns:
            if column in ("profit", "discount", "customer_name"):
                df[column] = None
            else:
                raise ValueError(f"Missing required column: {column}")

    prepared_df = df[required_columns].copy()
    prepared_df["order_id"] = prepared_df["order_id"].astype(str)
    prepared_df["customer_id"] = prepared_df["customer_id"].astype(str)
    prepared_df["order_date"] = pd.to_datetime(prepared_df["order_date"]).dt.date
    prepared_df = prepared_df.where(pd.notnull(prepared_df), None)
    records = prepared_df.to_dict(orient="records")
    for rec in records:
        rec["dataset_id"] = dataset_id

    insert_sql = text(
        """
        INSERT INTO orders_fact (
            dataset_id, order_id, order_date, customer_id, customer_name, region, category, sales, profit, discount
        ) VALUES (
            :dataset_id, :order_id, :order_date, :customer_id, :customer_name, :region, :category, :sales, :profit, :discount
        )
        ON CONFLICT (dataset_id, order_id) DO NOTHING
        """
    )
    with ENGINE.begin() as conn:
        conn.execute(insert_sql, records)
    return len(records)


def create_ingestion_run(dataset_id: str, source_details: Dict[str, Any]) -> str:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    ingestion_run_id = str(uuid.uuid4())
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO ingestion_runs (id, dataset_id, source_details, status)
                VALUES (:id, :dataset_id, CAST(:source_details AS JSONB), 'running')
                """
            ),
            {
                "id": ingestion_run_id,
                "dataset_id": dataset_id,
                "source_details": json.dumps(source_details),
            },
        )
    return ingestion_run_id


def update_ingestion_run(
    ingestion_run_id: str,
    status: str,
    row_count: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE ingestion_runs
                SET status = :status, row_count = :row_count, error_message = :error_message
                WHERE id = :id
                """
            ),
            {
                "id": ingestion_run_id,
                "status": status,
                "row_count": row_count,
                "error_message": error_message,
            },
        )


def save_column_mapping(ingestion_run_id: str, mapping_json: Dict[str, Any], confidence_overall: Optional[float] = None) -> None:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO column_mappings (id, ingestion_run_id, mapping_json, confidence_overall)
                VALUES (:id, :ingestion_run_id, CAST(:mapping_json AS JSONB), :confidence_overall)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "ingestion_run_id": ingestion_run_id,
                "mapping_json": json.dumps(mapping_json),
                "confidence_overall": confidence_overall,
            },
        )


def load_active_orders() -> pd.DataFrame:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    dataset_id = get_active_dataset_id()
    if not dataset_id:
        return pd.DataFrame()
    query = text(
        """
        SELECT
            order_id,
            order_date,
            customer_id,
            customer_name,
            region,
            category,
            sales,
            profit,
            discount
        FROM orders_fact
        WHERE dataset_id = :dataset_id
        """
    )
    with ENGINE.begin() as conn:
        df = pd.read_sql_query(query, conn, params={"dataset_id": dataset_id})
    return df


def seed_default_dataset_from_csv(csv_path: str) -> Optional[str]:
    if ENGINE is None or not os.path.exists(csv_path):
        return None

    existing = get_dataset_by_name("default_sample_superstore")
    if existing:
        if not existing["is_active"]:
            set_active_dataset(existing["id"])
        return existing["id"]

    source_df = pd.read_csv(csv_path, encoding="latin-1")
    normalized = source_df.rename(
        columns={
            "Order ID": "order_id",
            "Order Date": "order_date",
            "Customer ID": "customer_id",
            "Customer Name": "customer_name",
            "Region": "region",
            "Category": "category",
            "Sales": "sales",
            "Profit": "profit",
            "Discount": "discount",
        }
    )
    dataset_id = create_dataset(
        name="default_sample_superstore",
        source_type="seed",
        created_by="system",
        is_active=True,
    )
    insert_orders(dataset_id, normalized)
    return dataset_id


def save_analysis_run(dataset_id: str, filters: Dict[str, Any], computed: Dict[str, Any]) -> str:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    analysis_run_id = str(uuid.uuid4())
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO analysis_runs (
                    id, dataset_id, filters_json,
                    computed_kpis_json, sales_trend_json, category_sales_json, region_sales_json, forecast_json, rfm_json
                ) VALUES (
                    :id, :dataset_id, CAST(:filters_json AS JSONB),
                    CAST(:kpis_json AS JSONB), CAST(:sales_trend_json AS JSONB), CAST(:category_sales_json AS JSONB),
                    CAST(:region_sales_json AS JSONB), CAST(:forecast_json AS JSONB), CAST(:rfm_json AS JSONB)
                )
                """
            ),
            {
                "id": analysis_run_id,
                "dataset_id": dataset_id,
                "filters_json": json.dumps(filters),
                "kpis_json": json.dumps(computed.get("kpis", {})),
                "sales_trend_json": json.dumps(computed.get("sales_trend", [])),
                "category_sales_json": json.dumps(computed.get("category_sales", [])),
                "region_sales_json": json.dumps(computed.get("region_sales", [])),
                "forecast_json": json.dumps(computed.get("forecast", [])),
                "rfm_json": json.dumps(computed.get("rfm", {})),
            },
        )
    return analysis_run_id


def get_analysis_run(analysis_run_id: str) -> Optional[Dict[str, Any]]:
    if ENGINE is None:
        return None
    with ENGINE.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    id::text AS id,
                    dataset_id::text AS dataset_id,
                    filters_json,
                    computed_kpis_json,
                    sales_trend_json,
                    category_sales_json,
                    region_sales_json,
                    forecast_json,
                    rfm_json,
                    created_at
                FROM analysis_runs
                WHERE id = :id
                LIMIT 1
                """
            ),
            {"id": analysis_run_id},
        ).mappings().first()
    return dict(row) if row else None


def save_widgets(analysis_run_id: str, widgets: List[Dict[str, Any]]) -> None:
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    if not widgets:
        return
    rows = []
    for widget in widgets:
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "analysis_run_id": analysis_run_id,
                "widget_type": widget.get("widget_type"),
                "severity": widget.get("severity", "medium"),
                "title": widget.get("title", ""),
                "content_markdown": widget.get("content_markdown", ""),
                "evidence_json": json.dumps(widget.get("evidence_json", {})),
            }
        )

    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO analysis_widgets (
                    id, analysis_run_id, widget_type, severity, title, content_markdown, evidence_json
                ) VALUES (
                    :id, :analysis_run_id, :widget_type, :severity, :title, :content_markdown, CAST(:evidence_json AS JSONB)
                )
                """
            ),
            rows,
        )


def get_latest_widgets(analysis_run_id: str) -> List[Dict[str, Any]]:
    if ENGINE is None:
        return []
    with ENGINE.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    id::text AS id, widget_type, severity, title, content_markdown, evidence_json, created_at
                FROM analysis_widgets
                WHERE analysis_run_id = CAST(:analysis_run_id AS UUID)
                ORDER BY created_at ASC
                """
            ),
            {"analysis_run_id": analysis_run_id},
        ).mappings().all()
    return [dict(r) for r in rows]


def get_widget_by_id(widget_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single widget by its id."""
    if ENGINE is None:
        return None
    with ENGINE.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id::text AS id, analysis_run_id::text AS analysis_run_id, widget_type, severity, title, content_markdown, evidence_json, created_at
                FROM analysis_widgets
                WHERE id = CAST(:id AS UUID)
                LIMIT 1
                """
            ),
            {"id": widget_id},
        ).mappings().first()
    return dict(row) if row else None


# ─── Knowledge Documents ───────────────────────────────────────────────────────


def save_knowledge_chunks(dataset_id: str, source_filename: str, chunks: List[str]) -> None:
    """Save text chunks extracted from uploaded documents (PDF/DOC/TXT)."""
    if ENGINE is None:
        raise RuntimeError("PostgreSQL is not configured")
    if not chunks:
        return
    rows = [
        {
            "id": str(uuid.uuid4()),
            "dataset_id": dataset_id,
            "source_filename": source_filename,
            "chunk_index": idx,
            "content_text": chunk,
        }
        for idx, chunk in enumerate(chunks)
    ]
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO knowledge_documents (id, dataset_id, source_filename, chunk_index, content_text)
                VALUES (:id, :dataset_id, :source_filename, :chunk_index, :content_text)
                """
            ),
            rows,
        )


def search_knowledge(dataset_id: Optional[str], query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search knowledge documents by keyword relevance. Returns matching chunks."""
    if ENGINE is None:
        return []
    keywords = [kw.strip() for kw in query.lower().split() if len(kw.strip()) >= 2]
    if not keywords:
        # Fallback: return most recent chunks
        sql = text(
            """
            SELECT id::text, source_filename, chunk_index, content_text
            FROM knowledge_documents
            WHERE (CAST(:dataset_id AS UUID) IS NULL OR dataset_id = CAST(:dataset_id AS UUID))
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        with ENGINE.begin() as conn:
            rows = conn.execute(sql, {"dataset_id": dataset_id, "lim": limit}).mappings().all()
        return [dict(r) for r in rows]

    # Build keyword-based search using ILIKE for each keyword
    conditions = " OR ".join([f"LOWER(content_text) LIKE :kw{i}" for i in range(len(keywords))])
    sql = text(
        f"""
        SELECT id::text, source_filename, chunk_index, content_text
        FROM knowledge_documents
        WHERE (CAST(:dataset_id AS UUID) IS NULL OR dataset_id = CAST(:dataset_id AS UUID))
          AND ({conditions})
        ORDER BY created_at DESC
        LIMIT :lim
        """
    )
    params: Dict[str, Any] = {"dataset_id": dataset_id, "lim": limit}
    for i, kw in enumerate(keywords):
        params[f"kw{i}"] = f"%{kw}%"

    with ENGINE.begin() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [dict(r) for r in rows]


def get_all_knowledge_for_dataset(dataset_id: Optional[str], limit: int = 20) -> List[Dict[str, Any]]:
    """Get all knowledge document chunks for a dataset (for injecting into AI context)."""
    if ENGINE is None:
        return []
    sql = text(
        """
        SELECT source_filename, chunk_index, content_text
        FROM knowledge_documents
        WHERE (CAST(:dataset_id AS UUID) IS NULL OR dataset_id = CAST(:dataset_id AS UUID))
        ORDER BY source_filename, chunk_index
        LIMIT :lim
        """
    )
    with ENGINE.begin() as conn:
        rows = conn.execute(sql, {"dataset_id": dataset_id, "lim": limit}).mappings().all()
    return [dict(r) for r in rows]


# ─── Chat History ──────────────────────────────────────────────────────────────


def save_chat_history(analysis_run_id: str, user_message: str, assistant_response: str) -> None:
    """Save a chat Q&A pair for context memory."""
    if ENGINE is None:
        return
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO chat_history (id, analysis_run_id, user_message, assistant_response)
                VALUES (:id, :analysis_run_id, :user_message, :assistant_response)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "analysis_run_id": analysis_run_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
            },
        )


def get_recent_chat_history(analysis_run_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """Get recent chat history for an analysis run (for context injection)."""
    if ENGINE is None:
        return []
    sql = text(
        """
        SELECT user_message, assistant_response
        FROM chat_history
        WHERE analysis_run_id = CAST(:analysis_run_id AS UUID)
        ORDER BY created_at DESC
        LIMIT :lim
        """
    )
    with ENGINE.begin() as conn:
        rows = conn.execute(sql, {"analysis_run_id": analysis_run_id, "lim": limit}).mappings().all()
    # Return in chronological order (reverse the DESC result)
    return [dict(r) for r in reversed(rows)]


# ─── Raw Data Sample ───────────────────────────────────────────────────────────


def get_raw_data_sample(dataset_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get a sample of raw order data from PostgreSQL for AI context."""
    if ENGINE is None:
        return []
    ds_id = dataset_id or get_active_dataset_id()
    if not ds_id:
        return []
    sql = text(
        """
        SELECT order_id, order_date::text, customer_id, customer_name,
               region, category, sales::float, profit::float, discount::float
        FROM orders_fact
        WHERE dataset_id = :dataset_id
        ORDER BY order_date DESC
        LIMIT :lim
        """
    )
    with ENGINE.begin() as conn:
        rows = conn.execute(sql, {"dataset_id": ds_id, "lim": limit}).mappings().all()
    return [dict(r) for r in rows]


def get_data_statistics(dataset_id: Optional[str] = None) -> Dict[str, Any]:
    """Get summary statistics from orders_fact for AI context."""
    if ENGINE is None:
        return {}
    ds_id = dataset_id or get_active_dataset_id()
    if not ds_id:
        return {}
    sql = text(
        """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT order_id) as unique_orders,
            COUNT(DISTINCT customer_id) as unique_customers,
            COUNT(DISTINCT category) as category_count,
            COUNT(DISTINCT region) as region_count,
            MIN(order_date)::text as earliest_date,
            MAX(order_date)::text as latest_date,
            SUM(sales)::float as total_sales,
            SUM(profit)::float as total_profit,
            AVG(discount)::float as avg_discount
        FROM orders_fact
        WHERE dataset_id = :dataset_id
        """
    )
    with ENGINE.begin() as conn:
        row = conn.execute(sql, {"dataset_id": ds_id}).mappings().first()
    return dict(row) if row else {}

