-- Module 7: Additional Tools — Text-to-SQL + Web Search
-- Adds sales_data table, web search settings, and tool_calls column on messages

-- ────────────────────────────────────────────────────────────────────────
-- Section 1: sales_data table (no RLS — secured via sql_reader role)
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_date DATE NOT NULL,
    customer_name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    region TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'shipped', 'delivered', 'returned'))
);

-- Seed sample data (idempotent — only inserts if table is empty)
INSERT INTO sales_data (order_date, customer_name, product_name, category, quantity, unit_price, region, status)
SELECT * FROM (VALUES
    ('2026-01-05'::DATE, 'Alice Johnson',   'Wireless Mouse',      'Electronics',  2,  29.99, 'North', 'delivered'),
    ('2026-01-08'::DATE, 'Bob Smith',        'USB-C Hub',           'Electronics',  1,  49.99, 'South', 'delivered'),
    ('2026-01-12'::DATE, 'Carol Williams',   'Standing Desk',       'Furniture',    1, 399.99, 'East',  'shipped'),
    ('2026-01-15'::DATE, 'David Brown',      'Mechanical Keyboard', 'Electronics',  3,  89.99, 'West',  'delivered'),
    ('2026-01-20'::DATE, 'Eve Davis',        'Monitor Arm',         'Furniture',    2,  54.99, 'North', 'pending'),
    ('2026-01-25'::DATE, 'Frank Miller',     'Webcam HD',           'Electronics',  1,  79.99, 'South', 'delivered'),
    ('2026-02-01'::DATE, 'Grace Wilson',     'Desk Lamp',           'Furniture',    4,  34.99, 'East',  'delivered'),
    ('2026-02-05'::DATE, 'Henry Taylor',     'Laptop Stand',        'Furniture',    1,  44.99, 'West',  'shipped'),
    ('2026-02-10'::DATE, 'Ivy Anderson',     'Wireless Mouse',      'Electronics',  5,  29.99, 'North', 'delivered'),
    ('2026-02-15'::DATE, 'Jack Thomas',      'USB-C Hub',           'Electronics',  2,  49.99, 'South', 'returned'),
    ('2026-02-20'::DATE, 'Karen Martinez',   'Standing Desk',       'Furniture',    1, 399.99, 'East',  'pending'),
    ('2026-02-25'::DATE, 'Leo Garcia',       'Mechanical Keyboard', 'Electronics',  1,  89.99, 'West',  'delivered')
) AS v(order_date, customer_name, product_name, category, quantity, unit_price, region, status)
WHERE NOT EXISTS (SELECT 1 FROM sales_data LIMIT 1);

-- ────────────────────────────────────────────────────────────────────────
-- Section 2: Web search columns on global_settings
-- ────────────────────────────────────────────────────────────────────────
ALTER TABLE global_settings
    ADD COLUMN IF NOT EXISTS web_search_provider TEXT DEFAULT 'tavily',
    ADD COLUMN IF NOT EXISTS web_search_api_key TEXT,
    ADD COLUMN IF NOT EXISTS web_search_enabled BOOLEAN DEFAULT false;

-- ────────────────────────────────────────────────────────────────────────
-- Section 3: tool_calls column on messages
-- ────────────────────────────────────────────────────────────────────────
ALTER TABLE messages ADD COLUMN IF NOT EXISTS tool_calls JSONB;
