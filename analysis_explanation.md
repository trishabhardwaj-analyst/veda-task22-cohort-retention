# Task 22 — Cohort Retention Basics: Explanation

## 1. What is a cohort?
A cohort is a group of customers who share a common starting event. For this task, the cohort is defined by the **month of the customer's first recorded purchase**.

Example: if 120 customers made their first purchase in March 2010, they form the March 2010 cohort.

## 2. What is retention?
Retention asks: **how many customers from the original cohort are still active after a given number of months?**

Formula:

`Retention % = Active customers from cohort in period / Original cohort customers × 100`

Month 0 is normally 100% because the cohort is created from customers who were active in their first-purchase month.

## 3. Why use months since signup?
Using a relative period such as M0, M1, M2 ... makes different acquisition months comparable.

- M0 = first-purchase month
- M1 = one month after first purchase
- M2 = two months after first purchase
- M3 = three months after first purchase

## 4. Data cleaning
The analysis:
1. Combines both sheets of Online Retail II.
2. Converts InvoiceDate to datetime.
3. Converts Quantity, UnitPrice and CustomerID to numeric values.
4. Removes rows without customer/date/quantity/price information.
5. Excludes cancellation invoices beginning with `C`.
6. Keeps Quantity > 0 and UnitPrice > 0.
7. Removes exact duplicates.
8. Calculates Revenue = Quantity × UnitPrice.

## 5. Cohort construction
For each customer:
- Find their earliest valid InvoiceDate.
- Convert that date to the first day of its month.
- Assign that month as CohortMonth.

For each customer activity month:
- Calculate the month difference between ActivityMonth and CohortMonth.
- Count unique customers by CohortMonth and PeriodNumber.

## 6. Heatmap
The heatmap has:
- Rows = cohort/signup month.
- Columns = months since first purchase.
- Cells = retention percentage.

Darker/higher cells represent stronger retention; lower cells indicate customer drop-off.

## 7. Business interpretation
The most important comparison is horizontal within a row. If a cohort drops sharply from M0 to M1, the business has a weak first-repeat-purchase problem.

Compare the same period across rows to identify stronger or weaker acquisition cohorts.

## 8. Important limitation
Recent cohorts have less observation time. A cohort acquired near the end of the dataset cannot have a valid M12 comparison. Blank cells are therefore expected and should not be treated as zero retention.

## 9. Business recommendations
- Build a structured first-90-day onboarding journey.
- Use a second-purchase incentive around the typical first drop-off period.
- Compare acquisition campaigns/months with cohort quality.
- Create reactivation journeys for customers approaching inactivity.
- Monitor cohort retention monthly in Power BI.
