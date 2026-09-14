# 📊 Cohort Retention Analysis – VEDA Technology Task 22

## 📌 Project Overview

This project focuses on **Cohort Retention Analysis** using the **Online Retail II** dataset.

The objective is to group customers into cohorts based on their **first purchase month** and analyze how many customers continue to make purchases in the following months.

The project was completed as part of the **VEDA Technology Data Analytics Track – Level 2, Day 22 / Task 22: Cohort Retention Basics**.

---

## 🎯 Objective

> Build a cohort retention table by signup/first-purchase month and understand customer retention over time.

The analysis answers questions such as:

- When did customers make their first purchase?
- How many customers returned in subsequent months?
- Which customer cohorts have better retention?
- How does retention change as customer age increases?
- What patterns can be identified from the retention heatmap?

---

## 📂 Dataset

### Online Retail II

The project uses the **Online Retail II** dataset.

The dataset contains transaction-level information from a UK-based online retailer covering approximately two years.

### Important Columns

| Column | Description |
|---|---|
| `InvoiceNo` | Invoice/transaction number |
| `StockCode` | Product code |
| `Description` | Product description |
| `Quantity` | Quantity purchased |
| `InvoiceDate` | Date and time of transaction |
| `UnitPrice` | Price per unit |
| `CustomerID` | Unique customer identifier |
| `Country` | Customer country |

Revenue is calculated as:

```text
Revenue = Quantity × UnitPrice
