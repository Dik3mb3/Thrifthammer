import os, decimal

fp = os.path.join('C:', os.sep, 'Users', 'khleu', 'ThriftHammer', 'Thrifthammer', 'products', 'management', 'commands', 'populate_products.py')
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()
print('File read. Lines:', len(c.splitlines()))

NL = chr(10)
S12 = chr(32)*12
S16 = chr(32)*16
Q = chr(39)
DEC = 'decimal.Decimal('

def J(*args): return NL.join(args)

# CHANGE 3
bg = 'Boxed Games'
old3_marker = S12 + chr(35) + chr(32) + chr(45)*4 + chr(32) + bg + chr(32) + chr(45)*4
if old3_marker in c:
    print('CHANGE 3: marker found, doing regex replace'
    import re
    pattern = r'(            # ---- Boxed Games ----.*?            \\),)' + chr(0))  # placeholder
else:
    print('CHANGE 3: marker not found'
print('Done')