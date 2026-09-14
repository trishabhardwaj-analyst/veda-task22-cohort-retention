# Power BI Build Guide — Cohort Retention Basics

## 1. Load data
Import these files after running `cohort_retention_analysis.py`:
- `outputs/clean_transactions.csv`
- `outputs/customer_cohorts.csv`
- `outputs/cohort_retention_long.csv`

## 2. Relationships
Create:
- `CustomerCohorts[CustomerID]` → `Transactions[CustomerID]`
- One customer can have many transaction rows.

For the simplest dashboard, the precomputed `cohort_retention_long.csv` can be used directly for the heatmap.

## 3. Main visuals
### KPI cards
- Total Revenue
- Active Customers
- Total Orders
- Repeat Purchase Rate

### Cohort heatmap
Use a Matrix:
- Rows: `CohortMonth`
- Columns: `PeriodNumber`
- Values: `RetentionPercent`

Apply conditional formatting to `RetentionPercent`.

### Retention curve
Use a Line Chart:
- X-axis: `PeriodNumber`
- Y-axis: `RetentionPercent`
- Legend: `CohortMonth`

### Monthly activity
Use a Line Chart:
- X-axis: `InvoiceMonth`
- Y-axis: `ActiveCustomers`

## 4. Recommended page layout
1. Header: **Cohort Retention Analysis — Online Retail II**
2. Four KPI cards
3. Large retention heatmap
4. Retention curves
5. Monthly active customers / revenue trend
6. Slicers for Country and Cohort Month

## 5. Interpretation
- A row is one signup/first-purchase cohort.
- M0 is the cohort's starting month and should be approximately 100%.
- M1 shows the share of that original cohort active one month later.
- Lower values mean faster customer drop-off.
- Compare cohorts at the same period number.

## 6. Screenshot for submission
Take one clean dashboard screenshot showing:
- all KPI cards,
- the full cohort heatmap,
- at least one retention curve,
- slicers,
- and a readable title.
Save it under `screenshots/` as `dashboard_preview.png`.
