import os

# Output file path using chr()
fp_out = os.path.join(
    chr(67)+chr(58), os.sep+chr(85)+chr(115)+chr(101)+chr(114)+chr(115),
    chr(107)+chr(104)+chr(108)+chr(101)+chr(117),
    chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(72)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114),
    chr(112)+chr(97)+chr(116)+chr(99)+chr(104)+chr(95)+chr(99)+chr(51)+chr(46)+chr(112)+chr(121)
)

Q = chr(39)
NL = chr(10)

def line(*parts):
    return ''.join(str(p) for p in parts)

def ql(s):
    return Q + s + Q

def decl(v):
    return 'decimal.Decimal(' + Q + v + Q + ')'

S12 = ' ' * 12
S16 = ' ' * 16

# Build the target file content
fp_target = os.path.join(
    chr(67)+chr(58), os.sep+chr(85)+chr(115)+chr(101)+chr(114)+chr(115),
    chr(107)+chr(104)+chr(108)+chr(101)+chr(117),
    chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(72)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114),
    chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(104)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114),
    chr(112)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)+chr(115),
    chr(109)+chr(97)+chr(110)+chr(97)+chr(103)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116),
    chr(99)+chr(111)+chr(109)+chr(109)+chr(97)+chr(110)+chr(100)+chr(115),
    chr(112)+chr(111)+chr(112)+chr(117)+chr(108)+chr(97)+chr(116)+chr(101)+chr(95)+chr(112)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)+chr(115)+chr(46)+chr(112)+chr(121)
)

with open(fp_target, 'r', encoding='utf-8') as f:
    c = f.read()

print('File read. Lines:', len(c.splitlines()))

# ----------------------------------------------------------------
# CHANGE 3: Replace Boxed Games products block
# ----------------------------------------------------------------
marker_start = S12 + '# ---- Boxed Games ----'
kt001_end_line = S16 + ql('Cult operatives, terrain, and full Kill Team rules.') + ','

if marker_start in c:
    start_idx = c.find(marker_start)
    end_search = c.find(kt001_end_line, start_idx)
    if end_search != -1:
        close_paren = S12 + '),'
        end_idx = c.find(close_paren, end_search) + len(close_paren)

        # Build new block
        def entry(name, cat, faction_or_none, sku, price, *desc_lines):
            faction_str = ql(faction_or_none) if faction_or_none else 'None'
            lines = [
                S12 + '(',
                S16 + ql(name) + ',',
                S16 + ql(cat) + ', ' + faction_str + ',',
                S16 + ql(sku) + ', decimal.Decimal(' + ql(price) + '),',
            ]
            for dl in desc_lines:
                lines.append(S16 + ql(dl))
            lines.append(S12 + '),')
            return NL.join(lines)

        new_block = NL.join([
            S12 + '# ---- Starter Sets (40K) ----',
            entry('Leviathan (10th Edition Starter Set)', 'Warhammer 40,000', None, '40-02', '145.00',
                  'The huge 10th Edition launch box. Contains Space Marine ',
                  'and Tyranid forces, a 376-page hardback rulebook, dice, ',
                  'and terrain. Superb value.,'),
            entry('Warhammer 40,000 Starter Set', 'Warhammer 40,000', None, '40-03', '50.00',
                  'A compact starter with push-fit Space Marines and Tyranids, ',
                  'a small rulebook, and all you need to play your first game.,'),
            entry('Combat Patrol: Space Marines', 'Warhammer 40,000', 'Space Marines', '71-02', '105.00',
                  'A ready-to-play Combat Patrol force of Space Marines: ',
                  'Captain, Redemptor Dreadnought, Intercessors, and Outriders.,'),
            S12 + '# ---- Starter Sets (AoS) ----',
            entry('Age of Sigmar Warrior Starter Set', 'Age of Sigmar', None, '80-15', '35.00',
                  'The perfect introduction to Age of Sigmar: Stormcast Eternals ',
                  'vs Kruleboyz Orks, with a Getting Started guide.,'),
            S12 + '# ---- Horus Heresy Starter ----',
            entry('Horus Heresy: Age of Darkness', 'Horus Heresy', None, 'HH-001', '180.00',
                  'The massive Horus Heresy launch box. 54 plastic Mk VI Space ',
                  'Marines, vehicles, and the complete rulebook.,'),
            S12 + '# ---- Kill Team ----',
            entry('Kill Team: Nightmare', 'Kill Team', None, 'KT-001', '130.00',
                  'A Kill Team box with Chaos Legionaries vs Wyrmblade Genestealer ',
                  'Cult operatives, terrain, and full Kill Team rules.,'),
            entry('Kill Team: Into the Dark', 'Kill Team', None, 'KT-002', '130.00',
                  'A Kill Team box set featuring Veteran Guardsmen vs Intercession ',
                  'Squad operatives with a space hulk terrain board.,'),
            entry('Kill Team: Starter Set', 'Kill Team', None, 'KT-003', '65.00',
                  'The essential Kill Team starter box with two warbands, terrain, ',
                  'tokens, dice, and the complete condensed rules.,'),
        ])

        c = c[:start_idx] + new_block + NL + c[end_idx:]
        print('CHANGE 3: OK')
    else:
        print('CHANGE 3: FAILED - end search failed')
else:
    print('CHANGE 3: FAILED - start marker not found')

with open(fp_target, 'w', encoding='utf-8') as f:
    f.write(c)
print('Saved. Boxed Games count now:', c.count('Boxed Games'))
