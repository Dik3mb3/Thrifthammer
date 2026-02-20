filepath = r'C:\Users\khleu\ThriftHammer\Thrifthammer\products\management\commands\populate_products.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

changes_ok = 0

# CHANGE 1: Replace Boxed Games category with Kill Team
old1 = ('Boxed Games', 'Two-player and starter box sets with everything to play.')
new1 = ('Kill Team', 'Skirmish-scale combat in the 41st Millennium and Mortal Realms.')
if old1 in content:
    content = content.replace(old1, new1)
    print('CHANGE 1: OK - Boxed Games category replaced with Kill Team')
    changes_ok += 1
else:
    print('CHANGE 1: FAILED - pattern not found')

# CHANGE 2: Replace Tower of Games with eBay in retailers
old2 = (
                {\n
                    'name': 'Tower of Games',\n
                    'website': 'https://www.towerofgames.com',\n
                    'country': 'US',\n
                },
)
new2 = (
                {\n
                    'name': 'eBay',\n
                    'website': 'https://www.ebay.com',\n
                    'country': 'US',\n
                },
)
if old2 in content:
    content = content.replace(old2, new2)
    print('CHANGE 2: OK - Tower of Games replaced with eBay in retailers')
    changes_ok += 1
else:
    print('CHANGE 2: FAILED - pattern not found')

print(f'Changes so far: {changes_ok}')
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved.')
