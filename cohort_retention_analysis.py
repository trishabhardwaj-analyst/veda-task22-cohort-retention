from pathlib import Path
import io
import urllib.request
import zipfile
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
OUTPUT_DIR = ROOT / 'outputs'
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

UCI_URL = 'https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip'
RAW_XLSX = DATA_DIR / 'online_retail_II.xlsx'


def download_dataset():
    if RAW_XLSX.exists():
        return RAW_XLSX
    print('[1/7] Downloading UCI Online Retail II...')
    with urllib.request.urlopen(UCI_URL, timeout=180) as response:
        content = response.read()
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        names = [n for n in z.namelist() if n.lower().endswith('.xlsx')]
        if not names:
            raise FileNotFoundError('No XLSX file found in the UCI ZIP.')
        with z.open(names[0]) as src, open(RAW_XLSX, 'wb') as dst:
            dst.write(src.read())
    return RAW_XLSX


def standardize_columns(df):
    mapping = {}
    for c in df.columns:
        k = str(c).strip().lower().replace('_', '').replace(' ', '')
        if k in {'invoiceno', 'invoice'}:
            mapping[c] = 'InvoiceNo'
        elif k == 'stockcode':
            mapping[c] = 'StockCode'
        elif k == 'description':
            mapping[c] = 'Description'
        elif k == 'quantity':
            mapping[c] = 'Quantity'
        elif k == 'invoicedate':
            mapping[c] = 'InvoiceDate'
        elif k in {'unitprice', 'price'}:
            mapping[c] = 'UnitPrice'
        elif k in {'customerid', 'customer'}:
            mapping[c] = 'CustomerID'
        elif k == 'country':
            mapping[c] = 'Country'
    return df.rename(columns=mapping)


def load_raw(path):
    print('[2/7] Loading workbook...')
    xl = pd.ExcelFile(path)
    frames = []
    for sheet in xl.sheet_names:
        part = pd.read_excel(path, sheet_name=sheet)
        part = standardize_columns(part)
        required = {'InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country'}
        missing = required - set(part.columns)
        if missing:
            raise ValueError(f'Missing columns in {sheet}: {sorted(missing)}')
        frames.append(part)
        print(f'  {sheet}: {len(part):,} rows')
    raw = pd.concat(frames, ignore_index=True)
    return raw


def clean_transactions(raw):
    print('[3/7] Cleaning transactions...')
    df = raw.copy()
    raw_rows = len(df)
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
    df['CustomerID'] = pd.to_numeric(df['CustomerID'], errors='coerce')
    df = df.dropna(subset=['InvoiceNo','InvoiceDate','Quantity','UnitPrice','CustomerID'])
    df['InvoiceNo'] = df['InvoiceNo'].astype(str)
    df = df[~df['InvoiceNo'].str.upper().str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    df = df.drop_duplicates()
    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    df['InvoiceMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
    stats = {
        'raw_rows': raw_rows,
        'clean_rows': len(df),
        'customers': df['CustomerID'].nunique(),
        'orders': df['InvoiceNo'].nunique(),
        'countries': df['Country'].nunique(),
        'first_date': df['InvoiceDate'].min().date().isoformat(),
        'last_date': df['InvoiceDate'].max().date().isoformat(),
        'revenue': round(df['Revenue'].sum(), 2),
    }
    return df, stats


def build_cohort(df):
    print('[4/7] Building customer cohorts...')
    first_purchase = (
        df.groupby('CustomerID', as_index=False)['InvoiceDate']
          .min()
          .rename(columns={'InvoiceDate':'FirstPurchaseDate'})
    )
    first_purchase['CohortMonth'] = first_purchase['FirstPurchaseDate'].dt.to_period('M')
    customer_cohorts = first_purchase[['CustomerID','FirstPurchaseDate','CohortMonth']].copy()

    tx = df[['CustomerID','InvoiceNo','InvoiceDate','InvoiceMonth']].drop_duplicates()
    tx = tx.merge(customer_cohorts[['CustomerID','CohortMonth']], on='CustomerID', how='left')
    tx['ActivityMonth'] = pd.to_datetime(tx['InvoiceMonth']).dt.to_period('M')
    tx['PeriodNumber'] = (
        (tx['ActivityMonth'].dt.year - tx['CohortMonth'].dt.year) * 12
        + (tx['ActivityMonth'].dt.month - tx['CohortMonth'].dt.month)
    )
    active = tx[['CustomerID','CohortMonth','ActivityMonth','PeriodNumber']].drop_duplicates()

    cohort_sizes = (
        customer_cohorts.groupby('CohortMonth')['CustomerID']
        .nunique().rename('CohortCustomers').reset_index()
    )
    counts = (
        active.groupby(['CohortMonth','PeriodNumber'])['CustomerID']
        .nunique().rename('ActiveCustomers').reset_index()
    )
    counts = counts.merge(cohort_sizes, on='CohortMonth', how='left')
    counts['RetentionRate'] = counts['ActiveCustomers'] / counts['CohortCustomers']

    count_pivot = counts.pivot(index='CohortMonth', columns='PeriodNumber', values='ActiveCustomers').sort_index()
    pct_pivot = counts.pivot(index='CohortMonth', columns='PeriodNumber', values='RetentionRate').sort_index()
    size_series = cohort_sizes.set_index('CohortMonth')['CohortCustomers']
    return customer_cohorts, counts, count_pivot, pct_pivot, size_series


def save_outputs(df, stats, customer_cohorts, counts, count_pivot, pct_pivot, sizes):
    print('[5/7] Saving tables and heatmap...')
    df[['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country','Revenue']].to_csv(
        OUTPUT_DIR / 'clean_transactions.csv', index=False
    )
    customer_cohorts.to_csv(OUTPUT_DIR / 'customer_cohorts.csv', index=False)
    counts.sort_values(['CohortMonth','PeriodNumber']).to_csv(OUTPUT_DIR / 'cohort_retention_long.csv', index=False)
    count_pivot.to_csv(OUTPUT_DIR / 'cohort_retention_counts.csv')
    pct_pivot.to_csv(OUTPUT_DIR / 'cohort_retention_percent.csv')
    sizes.reset_index().to_csv(OUTPUT_DIR / 'cohort_sizes.csv', index=False)

    monthly = df.groupby('InvoiceMonth').agg(
        ActiveCustomers=('CustomerID','nunique'),
        Orders=('InvoiceNo','nunique'),
        Revenue=('Revenue','sum')
    ).reset_index()
    monthly['Revenue'] = monthly['Revenue'].round(2)
    monthly.to_csv(OUTPUT_DIR / 'monthly_activity.csv', index=False)

    # Cohort heatmap
    fig, ax = plt.subplots(figsize=(15, 8))
    data = pct_pivot.copy()
    data.index = data.index.astype(str)
    data.columns = [f'M{int(c)}' for c in data.columns]
    im = ax.imshow(data.values, aspect='auto', vmin=0, vmax=1)
    ax.set_title('Cohort Retention Heatmap')
    ax.set_xlabel('Months Since Signup / First Purchase')
    ax.set_ylabel('Signup Cohort Month')
    ax.set_xticks(np.arange(len(data.columns)))
    ax.set_xticklabels(data.columns, rotation=45, ha='right')
    ax.set_yticks(np.arange(len(data.index)))
    ax.set_yticklabels(data.index)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data.iat[i, j]
            if pd.notna(val):
                ax.text(j, i, f'{val:.0%}', ha='center', va='center', fontsize=7)
    fig.colorbar(im, ax=ax, label='Retention Rate')
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'cohort_retention_heatmap.png', dpi=180, bbox_inches='tight')
    plt.close(fig)

    # Retention curves for first 12 months for selected early cohorts
    fig, ax = plt.subplots(figsize=(12, 7))
    selected = list(pct_pivot.index[:min(8, len(pct_pivot.index))])
    for cohort in selected:
        row = pct_pivot.loc[cohort]
        row = row[row.index <= 12]
        ax.plot(row.index, row.values, marker='o', label=str(cohort))
    ax.set_title('Retention Curves — First Cohorts')
    ax.set_xlabel('Months Since First Purchase')
    ax.set_ylabel('Retention Rate')
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(title='Cohort', fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'retention_curves.png', dpi=180, bbox_inches='tight')
    plt.close(fig)

    kpis = pd.DataFrame([
        ['Raw transaction rows', stats['raw_rows']],
        ['Clean transaction rows', stats['clean_rows']],
        ['Customers analyzed', stats['customers']],
        ['Orders analyzed', stats['orders']],
        ['Countries represented', stats['countries']],
        ['First transaction date', stats['first_date']],
        ['Last transaction date', stats['last_date']],
        ['Total revenue', stats['revenue']],
        ['Cohorts', len(sizes)],
    ], columns=['Metric','Value'])
    kpis.to_csv(OUTPUT_DIR / 'kpis.csv', index=False)


def write_insights(pct_pivot, sizes):
    lines = ['# Cohort Retention Insights', '',
             'These insights are generated from the actual UCI Online Retail II data after the script is run.', '']
    if len(pct_pivot):
        max_period = min(3, int(max(pct_pivot.columns)))
        eligible = pct_pivot[pct_pivot.index <= pct_pivot.index[-1]]
        lines += [f'- **Month 0 retention:** 100% by definition because the cohort is defined by the first purchase month.',
                  f'- **Month {max_period} retention:** compare cohorts horizontally to identify how quickly customer activity falls after acquisition.',
                  '- **Best cohort:** identify the cohort with the highest retention at a common month, rather than comparing cohorts with unequal observation windows.',
                  '- **Cohort maturity matters:** recent cohorts have fewer observable months and should not be judged against older cohorts on long-term retention.',
                  '- **Business use:** use weak early retention cohorts to investigate acquisition quality, onboarding, product fit and repeat-purchase campaigns.']
    lines += ['', '## Recommended actions',
              '1. Build a 30/60/90-day repeat-purchase journey for newly acquired customers.',
              '2. Compare acquisition months with unusually weak early retention and review marketing/product changes during those periods.',
              '3. Trigger personalized offers before the normal drop-off point visible in the cohort curves.',
              '4. Track cohort retention monthly in Power BI rather than relying only on aggregate customer counts.',
              '5. Avoid causal claims: cohort differences show association and timing, not proof that a campaign or event caused retention changes.']
    (OUTPUT_DIR / 'insights.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    path = download_dataset()
    raw = load_raw(path)
    df, stats = clean_transactions(raw)
    customer_cohorts, counts, count_pivot, pct_pivot, sizes = build_cohort(df)
    save_outputs(df, stats, customer_cohorts, counts, count_pivot, pct_pivot, sizes)
    write_insights(pct_pivot, sizes)
    print('[7/7] Complete. See outputs/.')
    print(pd.DataFrame([
        ['Clean rows', stats['clean_rows']],
        ['Customers', stats['customers']],
        ['Orders', stats['orders']],
        ['Revenue', stats['revenue']],
        ['Cohorts', len(sizes)]
    ], columns=['Metric','Value']).to_string(index=False))


if __name__ == '__main__':
    main()
