#!/usr/bin/env python3
import pandas as pd

# Load data and check iPhone 16 Plus Apple products
df = pd.read_csv('data/raw/accessories/cases_sales.csv')
df.columns = df.columns.str.strip()

# Get Apple iPhone 16 Plus products
apple_plus = df[(df['brand'] == 'Apple') & (df['series'].str.contains('iPhone 16 Plus', na=False))]

print('iPhone 16 Plus Apple products sorted by sales:')
print('=' * 70)
for _, row in apple_plus.sort_values('pureqty', ascending=False).iterrows():
    name = row['product_name']
    sales = row['pureqty']
    print(f'{sales:6.1f} | {name}')

print()
print('Color analysis:')
for _, row in apple_plus.sort_values('pureqty', ascending=False).iterrows():
    name = row['product_name'].lower()
    sales = row['pureqty']
    
    if 'clear' in name:
        color = 'clear'
    elif 'black' in name:
        color = 'black'
    elif 'fuchsia' in name:
        color = 'fuchsia'
    elif 'ultramarine' in name:
        color = 'ultramarine'
    elif 'lake green' in name:
        color = 'lake_green'
    elif 'denim' in name:
        color = 'denim'
    elif 'star fruit' in name:
        color = 'star_fruit'
    elif 'stone gray' in name:
        color = 'stone_gray'
    elif 'plum' in name:
        color = 'plum'
    else:
        color = 'other'
    
    print(f'{sales:6.1f} | {color:12} | {row["product_name"]}')
