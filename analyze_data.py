import pandas as pd

df = pd.read_csv('data/raw/accessories/cases_sales.csv')
df['total_qty'] = df['pureqty'] + df['impureqty']

print("TOP 20 SELLING PRODUCTS:")
top_products = df.nlargest(20, 'total_qty')
for i, row in top_products.iterrows():
    print(f"{row['total_qty']:4.0f} | {row['brand']:10} | {row['product_name'][:50]}")

print(f"\nHigh sellers (>300): {len(df[df['total_qty'] > 300])}")
print(f"Medium sellers (100-300): {len(df[(df['total_qty'] >= 100) & (df['total_qty'] <= 300)])}")
print(f"Low sellers (<100): {len(df[df['total_qty'] < 100])}")
