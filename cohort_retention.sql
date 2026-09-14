-- ============================================================
-- VEDA TECHNOLOGY - TASK 22
-- COHORT RETENTION BASICS
-- MySQL 8+
-- ============================================================

CREATE DATABASE IF NOT EXISTS cohort_retention;
USE cohort_retention;

-- Load outputs/clean_transactions.csv into this table first.
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    InvoiceNo VARCHAR(30),
    StockCode VARCHAR(50),
    Description VARCHAR(255),
    Quantity INT,
    InvoiceDate DATETIME,
    UnitPrice DECIMAL(12,4),
    CustomerID VARCHAR(30),
    Country VARCHAR(100),
    Revenue DECIMAL(16,4)
);

-- Example import (edit the path for your computer):
-- LOAD DATA LOCAL INFILE 'C:/path/to/outputs/clean_transactions.csv'
-- INTO TABLE transactions
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;

-- 1. Basic validation
SELECT COUNT(*) AS clean_rows,
       COUNT(DISTINCT CustomerID) AS customers,
       COUNT(DISTINCT InvoiceNo) AS orders,
       ROUND(SUM(Revenue),2) AS revenue
FROM transactions;

SELECT MIN(InvoiceDate) AS first_date,
       MAX(InvoiceDate) AS last_date
FROM transactions;

-- 2. First purchase / cohort month for each customer
DROP VIEW IF EXISTS customer_cohorts;
CREATE VIEW customer_cohorts AS
SELECT
    CustomerID,
    MIN(InvoiceDate) AS FirstPurchaseDate,
    DATE_FORMAT(MIN(InvoiceDate), '%Y-%m-01') AS CohortMonth
FROM transactions
GROUP BY CustomerID;

-- 3. Customer activity by month
DROP VIEW IF EXISTS customer_monthly_activity;
CREATE VIEW customer_monthly_activity AS
SELECT DISTINCT
    t.CustomerID,
    c.CohortMonth,
    DATE_FORMAT(t.InvoiceDate, '%Y-%m-01') AS ActivityMonth
FROM transactions t
JOIN customer_cohorts c ON t.CustomerID = c.CustomerID;

-- 4. Cohort period number
DROP VIEW IF EXISTS cohort_activity;
CREATE VIEW cohort_activity AS
SELECT
    CustomerID,
    CohortMonth,
    ActivityMonth,
    PERIOD_DIFF(
        DATE_FORMAT(ActivityMonth, '%Y%m'),
        DATE_FORMAT(CohortMonth, '%Y%m')
    ) AS PeriodNumber
FROM customer_monthly_activity;

-- 5. Cohort size
DROP VIEW IF EXISTS cohort_sizes;
CREATE VIEW cohort_sizes AS
SELECT CohortMonth,
       COUNT(DISTINCT CustomerID) AS CohortCustomers
FROM customer_cohorts
GROUP BY CohortMonth;

-- 6. Retention table
SELECT
    a.CohortMonth,
    a.PeriodNumber,
    COUNT(DISTINCT a.CustomerID) AS ActiveCustomers,
    s.CohortCustomers,
    ROUND(100 * COUNT(DISTINCT a.CustomerID) / s.CohortCustomers, 2) AS RetentionPercent
FROM cohort_activity a
JOIN cohort_sizes s ON a.CohortMonth = s.CohortMonth
GROUP BY a.CohortMonth, a.PeriodNumber, s.CohortCustomers
ORDER BY a.CohortMonth, a.PeriodNumber;

-- 7. Month 0, Month 1, Month 3 retention summary
SELECT
    CohortMonth,
    MAX(CASE WHEN PeriodNumber = 0 THEN RetentionPercent END) AS M0,
    MAX(CASE WHEN PeriodNumber = 1 THEN RetentionPercent END) AS M1,
    MAX(CASE WHEN PeriodNumber = 2 THEN RetentionPercent END) AS M2,
    MAX(CASE WHEN PeriodNumber = 3 THEN RetentionPercent END) AS M3,
    MAX(CASE WHEN PeriodNumber = 6 THEN RetentionPercent END) AS M6,
    MAX(CASE WHEN PeriodNumber = 12 THEN RetentionPercent END) AS M12
FROM (
    SELECT a.CohortMonth,
           a.PeriodNumber,
           100 * COUNT(DISTINCT a.CustomerID) / s.CohortCustomers AS RetentionPercent
    FROM cohort_activity a
    JOIN cohort_sizes s ON a.CohortMonth = s.CohortMonth
    GROUP BY a.CohortMonth, a.PeriodNumber, s.CohortCustomers
) x
GROUP BY CohortMonth
ORDER BY CohortMonth;

-- 8. Monthly active customers
SELECT DATE_FORMAT(InvoiceDate, '%Y-%m') AS ActivityMonth,
       COUNT(DISTINCT CustomerID) AS ActiveCustomers,
       COUNT(DISTINCT InvoiceNo) AS Orders,
       ROUND(SUM(Revenue),2) AS Revenue
FROM transactions
GROUP BY DATE_FORMAT(InvoiceDate, '%Y-%m')
ORDER BY ActivityMonth;
