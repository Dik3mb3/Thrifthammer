# Prompt: Adding UK Retailer Prices to ThriftHammer

Use this prompt at the start of any session where you are adding GW UK prices,
other UK retailer prices, or onboarding a brand-new UK retailer to the site.

---

## What you are working on

ThriftHammer has a fully isolated UK version of the site at `/uk/products/`.
It is completely separate from the US version at `/products/`.  The two sides
share the same Product catalog but have different views, templates, and price
records.  UK prices are in GBP (£).  US prices are in USD ($).

---

## How UK price isolation works

Every retailer that sells in GBP has `is_uk = True` on its `Retailer` model
record (field added in migration 0062).  All UK view queries filter with
`retailer__is_uk=True`; all US view queries exclude with
`retailer__is_uk=False/not True`.  **This field is the sole mechanism that
prevents UK prices from leaking onto US pages.**  It requires no code change
when a new UK retailer is added — setting `is_uk=True` on the Retailer record
is sufficient.

Current UK retailers in production:
| Retailer slug          | Name                 |
|------------------------|----------------------|
| `games-workshop-uk`    | Games Workshop UK    |
| `ebay-uk`              | eBay UK              |
| `amazon-uk`            | Amazon UK            |

---

## File map — UK-only files (never touch the US equivalents)

| Purpose                    | UK file                                              | US equivalent (DO NOT TOUCH) |
|----------------------------|------------------------------------------------------|------------------------------|
| Product list view          | `products/views_uk.py`                               | `products/views.py`          |
| URL config                 | `products/urls_uk.py`                                | `products/urls.py`           |
| List template              | `templates/products/product_list_uk.html`            | `templates/products/product_list.html` |
| Detail template            | `templates/products/product_detail_uk.html`          | `templates/products/product_detail.html` |
| Price seed commands        | `products/management/commands/seed_gw_uk_<faction>_prices.py` | (US seed commands) |

---

## Task A — Adding GW UK prices for a new faction

### Step 1: Get the data from the user

Ask the user for each product:
- `gw_sku` (e.g. `59-10`) — must match an existing Product in the DB
- Product name (for readability in the command)
- GBP price as a `Decimal` (e.g. `35.50`)
- Full GW UK product page URL (e.g. `https://www.warhammer.com/en-GB/shop/...`)

**NEVER invent, guess, or use placeholder prices or URLs.**  If a value is
missing, ask before writing any code.

### Step 2: Create the seed command

File: `products/management/commands/seed_gw_uk_<faction>_prices.py`

Use `seed_gw_uk_admech_prices.py` as the exact template.  Key rules:

```python
retailer, created = Retailer.objects.get_or_create(
    slug='games-workshop-uk',
    defaults={
        'name': 'Games Workshop UK',
        'website': 'https://www.warhammer.com/en-GB/',
        'country': 'UK',
        'is_active': True,
        'is_uk': True,          # <-- REQUIRED. Never omit this.
    },
)
```

The `get_or_create` is idempotent — `games-workshop-uk` already exists in
production, so `is_uk: True` in defaults only fires on first creation.
Still include it so the command stays self-documenting and correct if run
against a fresh DB.

For each product, use `update_or_create` on `CurrentPrice`:

```python
product = Product.objects.get(gw_sku=sku)
product.msrp_gbp = gbp_price
product.save(update_fields=['msrp_gbp'])

CurrentPrice.objects.update_or_create(
    product=product,
    retailer=retailer,
    defaults={
        'price': gbp_price,
        'url': gw_uk_url,
        'in_stock': True,
        'not_available': False,
    },
)
```

### Step 3: Add to Procfile

Insert immediately **after** the last `seed_gw_uk_*` command and **before**
`python manage.py clear_cache`:

```
&& python manage.py seed_gw_uk_<faction>_prices || true
```

### Step 4: Run against production via Railway CLI (before pushing)

```powershell
cd C:\Users\khleu\ThriftHammer\Thrifthammer
$env:DATABASE_URL = "<DATABASE_PUBLIC_URL from railway variables --service Postgres --json>"
python manage.py seed_gw_uk_<faction>_prices
```

Show the user the output and confirm it seeded the expected number of rows with
zero skipped before proceeding.

### Step 5: Commit and push only when the user says so

Never push without explicit approval.

---

## Task B — Onboarding a brand-new UK retailer (e.g. Element Games, Wayland Games)

### Step 1: Create the Retailer record

The Retailer must be created with `is_uk=True`.  Do this inside the seed
command's `get_or_create` call:

```python
retailer, created = Retailer.objects.get_or_create(
    slug='element-games',
    defaults={
        'name': 'Element Games',
        'website': 'https://elementgames.co.uk/',
        'country': 'UK',
        'is_active': True,
        'is_uk': True,          # <-- REQUIRED. Never omit this.
    },
)
```

**If `is_uk=True` is missing, the retailer's prices will leak onto US pages.**
This is a critical data integrity rule.

### Step 2: Create the seed command

Same pattern as GW UK.  The command creates the Retailer and seeds
`CurrentPrice` records.

### Step 3: No migration needed

`is_uk` already exists on the Retailer model.  No schema change is required
when adding a new UK retailer — just set `is_uk=True` in the seed command.

### Step 4: Add to Procfile and deploy as in Task A.

---

## Absolute rules — read before writing any code

1. **Never touch the US side.**  Do not edit `products/views.py`,
   `products/urls.py`, any US template, or any existing US seed/populate
   command.  If a change seems to require touching the US side, stop and
   explain why to the user before proceeding.

2. **Never use placeholder data.**  No invented prices, guessed URLs, or
   approximate GBP values.  If a real value is not available, leave the field
   null and tell the user what is missing.

3. **Never run `populate_products` or any existing populate command.**  Only
   create new targeted seed commands.  populate_products.py is not in the
   Procfile and does not run on Railway — data set there never reaches
   production.

4. **Every new UK retailer must have `is_uk=True`.**  This is non-negotiable.
   Forgetting it causes UK GBP prices to appear as USD on US product pages.

5. **Never add retailer slugs to a frozenset or hardcoded list.**  The
   `Retailer.is_uk` field replaced all slug-based filtering.  If you find
   yourself writing `frozenset({...})` or `slug__in=[...]` for UK isolation,
   stop — you are doing it wrong.

6. **Never push without explicit user approval.**  Run the seed command against
   production via Railway CLI first, show the output, then wait for "go".

7. **Be transparent about every production write.**  Before running any command
   against the production DB, state exactly what it will do (rows created,
   fields updated, retailer created/reused).  After running, report the actual
   output.

8. **Easy revert.**  Each seed command is idempotent via `update_or_create`.
   To undo a bad seed: delete the `CurrentPrice` rows via Django shell or
   admin.  The `Retailer` record can be deactivated (`is_active=False`) to
   hide it without deleting.

---

## Quick reference — Railway CLI commands

```powershell
# Get production DB public URL
railway variables --service Postgres --json

# Run a management command against production
$env:DATABASE_URL = "<DATABASE_PUBLIC_URL>"
python manage.py <command>
```

The internal DB URL (`postgres.railway.internal`) is NOT reachable from
localhost.  Always use the public URL when running commands locally against
production.
