import re, subprocess

filepath = r"C:\Users\khleu\ThriftHammer\Thrifthammer\products\management\commands\populate_products.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Strategy: find the section we added (# === ADDITIONAL TAU ===)
# and replace the entire new additions section with cleaned versions
# that don't duplicate existing extended_data entries.

# Remove the duplicated new-section T'au block (lines 1723-1747 area)
# Find and remove: # === ADDITIONAL TAU === through # === ADDITIONAL AGE OF SIGMAR ===
old_tau_block_start = "            # === ADDITIONAL TAU ==="
old_tau_block_end = "            # === ADDITIONAL AGE OF SIGMAR ==="

start_idx = content.find(old_tau_block_start)
end_idx = content.find(old_tau_block_end)
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]
    print("Removed duplicate T'au section")

# Remove death guard duplicates section
old_dg_start = "\n            # ================================================================\n            # DEATH GUARD — more units\n            # ================================================================\n            ('Death Guard Plague Marines'"
old_dg_end = "            ('Death Guard Foetid Bloat-drone'"

# Find the second occurrence of Death Guard Plague Marines (the duplicate)
first_occ = content.find("'Death Guard Plague Marines'")
second_occ = content.find("'Death Guard Plague Marines'", first_occ + 1)
if second_occ != -1:
    # Find the section start before it
    sec_start = content.rfind("# ================================================================\n            # DEATH GUARD — more units", 0, second_occ)
    if sec_start != -1:
        # Find the end: next section comment or closing bracket
        sec_end_marker = "            # ================================================================\n            # HORUS HERESY — more units"
        sec_end = content.find(sec_end_marker, sec_start)
        if sec_end != -1:
            content = content[:sec_start] + content[sec_end:]
            print("Removed duplicate Death Guard section")

# Remove Astra Militarum duplicates
first_am = content.find("'Astra Militarum Infantry Squad'")
second_am = content.find("'Astra Militarum Infantry Squad'", first_am + 1)
if second_am != -1:
    sec_start = content.rfind("# ================================================================\n            # ASTRA MILITARUM — more units", 0, second_am)
    if sec_start != -1:
        sec_end_marker = "# ================================================================\n            # DEATH GUARD — more units"
        sec_end = content.find(sec_end_marker, sec_start)
        if sec_end != -1:
            content = content[:sec_start] + content[sec_end:]
            print("Removed duplicate Astra Militarum section")

# Remove AoS duplicates section  
old_aos_start = "            # === ADDITIONAL AGE OF SIGMAR ==="
aos_start_idx = content.find(old_aos_start)
if aos_start_idx != -1:
    # Find where the AoS section ends (next === section or closing bracket)
    aos_end_marker = "            # === ASTRA MILITARUM — more units ==="
    aos_end_idx = content.find(aos_end_marker, aos_start_idx)
    if aos_end_idx == -1:
        aos_end_marker = "            # === ADDITIONAL SPACE MARINES ==="
        aos_end_idx = content.find(aos_end_marker, aos_start_idx)
    if aos_end_idx == -1:
        # Try to find the section for astra militarum
        aos_end_marker = "            # ================================================================\n            # ASTRA MILITARUM"
        aos_end_idx = content.find(aos_end_marker, aos_start_idx)
    if aos_end_idx != -1:
        content = content[:aos_start_idx] + content[aos_end_idx:]
        print("Removed duplicate AoS section")
    else:
        print("Could not find AoS section end marker")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

result = subprocess.run(['python', '-m', 'py_compile', filepath], capture_output=True, text=True)
if result.returncode == 0:
    print("Syntax OK!")
else:
    print("Syntax error:", result.stderr[:500])
