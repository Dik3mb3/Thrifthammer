$out = 'C:/Users/khleu/ThriftHammer/gen_c5.py'
$lines = [System.Collections.Generic.List[string]]::new()
function AL([string]$s) { $lines.Add($s) }

AL 'import os, decimal'
AL ''
AL 'fp = os.path.join(chr(67)+chr(58), os.sep+chr(85)+chr(115)+chr(101)+chr(114)+chr(115), chr(107)+chr(104)+chr(108)+chr(101)+chr(117), chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(72)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114), chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(104)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114), chr(112)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)+chr(115), chr(109)+chr(97)+chr(110)+chr(97)+chr(103)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116), chr(99)+chr(111)+chr(109)+chr(109)+chr(97)+chr(110)+chr(100)+chr(115), chr(112)+chr(111)+chr(112)+chr(117)+chr(108)+chr(97)+chr(116)+chr(101)+chr(95)+chr(112)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)+chr(115)+chr(46)+chr(112)+chr(121))'
AL 'with open(fp, chr(114), encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)) as f:'
AL '    c = f.read()'
AL 'print(chr(76)+chr(105)+chr(110)+chr(101)+chr(115)+chr(58), len(c.splitlines()))'
AL ''
AL 'NL = chr(10); Q = chr(39); S12 = chr(32)*12; S13 = chr(32)*13; EN = chr(8211)'
AL ''
AL 'def entry(name, cat, faction, sku, price, d1, d2):'
AL '    fs = Q + faction + Q if faction else chr(78)+chr(111)+chr(110)+chr(101)'
AL '    return NL.join(['
AL '        S12 + chr(40) + Q + name + Q + chr(44)+chr(32) + Q + cat + Q + chr(44)+chr(32) + fs + chr(44),'
AL '        S13 + Q + sku + Q + chr(44)+chr(32)+chr(100)+chr(101)+chr(99)+chr(105)+chr(109)+chr(97)+chr(108)+chr(46)+chr(68)+chr(101)+chr(99)+chr(105)+chr(109)+chr(97)+chr(108)+chr(40) + Q + price + Q + chr(41)+chr(44),'
AL '        S13 + Q + d1 + Q + chr(44),'
AL '        S13 + Q + d2 + Q + chr(41)+chr(44),'
AL '    ])'
AL ''
AL 'products = ['

[System.IO.File]::WriteAllLines($out, $lines, [System.Text.Encoding]::UTF8)
Write-Host 'Header written'