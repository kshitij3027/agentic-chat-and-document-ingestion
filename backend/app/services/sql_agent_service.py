"""SQL agent service for querying structured data."""
import ssl
import logging
import asyncpg

from app.config import get_settings

logger = logging.getLogger(__name__)

SALES_DATA_SCHEMA = """Table: sales_data
Columns:
  - id (UUID, primary key)
  - order_date (DATE) — e.g., '2026-01-05'
  - customer_name (TEXT) — e.g., 'Alice Johnson'
  - product_name (TEXT) — e.g., 'Wireless Mouse', 'USB-C Hub', 'Standing Desk'
  - category (TEXT) — 'Electronics' or 'Furniture'
  - quantity (INTEGER) — e.g., 1, 2, 5
  - unit_price (DECIMAL) — e.g., 29.99, 399.99
  - total_amount (DECIMAL, generated) — quantity * unit_price
  - region (TEXT) — 'North', 'South', 'East', 'West'
  - status (TEXT) — 'pending', 'shipped', 'delivered', 'returned'"""


async def execute_sql_query(sql: str) -> str:
    """
    Execute a read-only SQL query against the sales database.

    Uses a restricted sql_reader role that can only SELECT from sales_data.
    Returns formatted results or an error message string.
    """
    dsn = get_settings().sql_reader_database_url
    if not dsn:
        return "Error: SQL database connection is not configured."

    conn = None
    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        conn = await asyncpg.connect(dsn=dsn, ssl=ssl_ctx, statement_cache_size=0)
        await conn.execute("SET ROLE sql_reader")
        rows = await conn.fetch(sql)

        if not rows:
            return "Query returned 0 rows."

        return _format_results(rows)

    except asyncpg.InsufficientPrivilegeError as e:
        logger.error("SQL privilege error: %s", e)
        return "Error: Permission denied. Only SELECT queries on sales_data are allowed."
    except asyncpg.PostgresSyntaxError as e:
        logger.error("SQL syntax error: %s", e)
        return f"Error: SQL syntax error — {e}"
    except asyncpg.UndefinedTableError as e:
        logger.error("SQL table error: %s", e)
        return f"Error: Table not found — {e}"
    except asyncpg.UndefinedColumnError as e:
        logger.error("SQL column error: %s", e)
        return f"Error: Column not found — {e}"
    except Exception as e:
        logger.exception("SQL execution error")
        return f"Error: {e}"
    finally:
        if conn:
            await conn.close()


def _format_results(rows: list[asyncpg.Record]) -> str:
    """Format query results as a pipe-delimited ASCII table."""
    if not rows:
        return "Query returned 0 rows."

    headers = list(rows[0].keys())
    lines = [" | ".join(str(h) for h in headers)]
    lines.append("-" * len(lines[0]))

    display_rows = rows[:100]
    for row in display_rows:
        lines.append(" | ".join(str(row[h]) for h in headers))

    msg = f"Query returned {len(rows)} row(s)"
    if len(rows) > 100:
        msg += " (showing first 100)"
    return msg + ":\n\n" + "\n".join(lines)
