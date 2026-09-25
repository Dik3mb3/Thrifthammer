# Prompt: Adding UK Retailer Prices to ThriftHammer

Use this prompt at the start of any session where you are adding GW UK prices,
other UK retailer prices, or onboarding a brand-new UK retailer to the site.

**Rewritten 2026-09-25** after the `/uk/products/` implementation was
consolidated (the old isolated UK views/templates were deleted) and after a
real "GW MSRP" mislabeling bug was found and fixed. Read this whole file
before writing any code — several rules below correct mistakes made earlier
in that same session. Do not rely on a prior memory of this file; re-read it
fresh each time, since it is kept in sync with the live codebase.

---

## What you are working on

ThriftHammer has ONE product list view, ONE product detail view, and ONE pair
of templates. They serve BOTH `/products/...` (US) and `/uk/products/...`
(UK) — there is no separate UK codebase anymore. UK prices are in GBP (£).
US prices are in USD ($). Which one a request sees is decided entirely by
data (`Retailer.is_uk`) and a per-request `region` variable, never by which
file runs.

**Do not recreate a parallel UK-only view/template/URL set.** That was tried
once (`views_uk.py`, `product_list_uk.html`, `product_detail_uk.html`), it
quietly stopped getting updates the moment new features shipped only on the
US side, and it was deleted for exactly that reason. If a UK-specific need
comes up, it almost always belongs as a branch inside the shared
view/template (see "How region is resolved" below), not a new file.

---

## How UK price isolation works (unchanged, still the one true mechanism)

Every retailer that sells in GBP has `is_uk = True` on its `Retailer` model
record (field added in migration `0062_retailer_is_uk.py`). All UK-facing
queries filter with `retailer__is_uk=True` (or `.exclude(retailer__is_uk=True)`
on the US side). **This field is the sole mechanism that prevents UK prices
from leaking onto US pages.** It requires no code change when a new UK
retailer is added — setting `is_uk=True` on the Retailer record is
sufficient. **Never** write `frozenset({...})` or `slug__in=[...]` for UK
isolation — a stale slug list has caused real leaks before (see
`send_friday_deals.py`'s code comment about the `firestorm-games` incident).

Current UK retailers in production (`Retailer.objects.filter(is_uk=True)`):

| Retailer slug            | Name                    | Category it serves        |
|---------------------------|-------------------------|----------------------------|
| `games-workshop-uk`       | Games Workshop UK       | All GW game systems        |
| `ebay-uk`                  | eBay UK                 | All categories             |
| `amazon-uk`                 | Amazon UK                | All categories (books)     |
| `firestorm-games`          | Firestorm Games         | All categories (UK retailer, slug has no `-uk` suffix — this is the one that caused the past leak, see above) |
| `mantic-games-uk`          | Mantic Games UK         | Halo: Flashpoint           |
| `asmodee-uk`                | Asmodee UK               | Marvel Crisis Protocol, Star Wars Legion/Shatterpoint |
| `catalyst-game-labs-uk`    | Catalyst Game Labs UK   | Battletech                 |
| `wyrd-games-uk`             | Wyrd Games UK            | Malifaux                   |
| `trench-crusade-uk`         | Trench Crusade UK        | Trench Crusade             |

This list will grow. Re-query it (`Retailer.objects.filter(is_uk=True)`)
rather than trusting this table if it's been a while — it's a snapshot, not
a live source.

---

## How region is resolved (the actual current architecture)

`products/views.py` — `product_list()`, `product_detail()`,
`search_autocomplete()` — each resolve region the same way, near the top of
the function:

```python
if request.path.startswith('/uk/'):
    region = 'uk'
else:
    region_param = request.GET.get('region', '').strip()
    if region_param in ('us', 'uk'):
        request.session['region'] = region_param
    region = request.session.get('region', 'us')
```

`products/urls_uk.py` (app_name `products_uk`) routes `/uk/products/...` to
these exact same functions — it does not import a separate `views_uk`
module. `/uk/products/` and `/products/?region=uk` (or a session that
already has `region=uk` set) both work and both resolve to `region='uk'`;
the path-prefix form is what the site's own nav/UK-region emails use, the
query-param form is an older mechanism kept for backward compatibility
(email links from before the `/uk/` prefix existed still work).

**Every internal link must be region-aware or it silently drops UK context
on click.** Never hardcode `{% url 'products:detail' slug %}` in a shared
template. Use the context-processor-provided variables instead, computed
once in `products/context_processors.py`'s `site_stats()`:

```django
{% url products_list_url_name %}
{% url products_detail_url_name product.slug %}
{% url products_autocomplete_url_name %}
```

These resolve to `products:list`/`products_uk:list` etc. depending on the
already-resolved `region`. This was the actual root cause of a real bug this
session (related-product cards and breadcrumbs silently jumping a UK visitor
back to the US URL) — check any new template you add against this pattern.

**Every hardcoded `$` in a shared template is a latent bug.** Always branch:
`{% if region == 'uk' %}£{% else %}${% endif %}` — including inside
`<script>` blocks (autocomplete dropdowns have bitten this twice: once in
`base.html`, once in `product_list.html`, both independent hardcoded-`$`
bugs in separate JS blocks that the first fix didn't catch).

---

## Two label rules that must never regress (fixed 2026-09-25, do not re-add per-category hardcoding)

**1. MSRP label.** `product_detail.html`, `my_collection.html`,
`price_alert.html` (+ its plain-text twin in `send_price_alerts.py`),
`army_calculator.html`, `view_army.html` all say plain **"MSRP"** — never
"GW MSRP". This used to be hardcoded to "GW MSRP" everywhere except Paint &
Supplies, which was wrong for every non-GW category (Halo: Flashpoint,
Battletech, Warmachine, Malifaux, Star Wars Legion/Shatterpoint, Marvel
Crisis Protocol). **Do not add a new per-category exception when you onboard
a new non-GW category — the generic label already covers it.**

**2. "View Official Listing" button.** `product_detail.html`'s external
link button (shown when `product.gw_url` is set) says **"View Official
Listing"** for every category — never "View on GW". This used to hardcode
"View on Asmodee" / "View on Wyrd Games" / "View on Trench Crusade" as three
special cases and fell through to "View on GW" for everything else,
including Warmachine and Battletech (a Warmachine product's `gw_url` field
actually holds a `warmachine.gg` URL, not a warhammer.com one — the field
name is legacy, it really means "this category's official store URL").
**Do not add a new per-category label here either.**

If you ever find yourself writing
`{% if product.category.slug == '...' %}...{% endif %}` for a label in
these two spots, stop — that pattern was already tried, already caused a
real user-visible bug, and was deliberately removed.

---

## The `msrp_gbp` rule — read this carefully, it is more nuanced than it used to be

`Product.msrp_gbp` drives the "MSRP" reference line AND the discount-badge
percentage on the UK product page. The view logic
(`products/views.py`, `product_detail()`) is:

```python
gw_cp_uk = <live CurrentPrice from retailer.slug == 'games-workshop-uk'>
gw_ref_price = gw_cp_uk.price if gw_cp_uk else product.msrp_gbp
```

**This lookup is hardcoded to `games-workshop-uk` specifically — it does
NOT check any other retailer, no matter how "official" that retailer is for
the category.** So for a non-GW category (no `games-workshop-uk` row exists
at all), the "MSRP" line depends entirely on `product.msrp_gbp` being set by
something else. If it's `None`, the UK page silently shows no MSRP line and
no discount badge, even if a real price exists in the comparison table. This
is not cosmetic — it's a real functional gap, and it's exactly what
happened with the first Mantic Games UK import in this session (fixed by
also writing `msrp_gbp`, see below).

**The rule:**
- For a genuine GW game system, `msrp_gbp` is written by `games-workshop-uk`
  only. Never let another UK retailer's price overwrite it — a competitor's
  price is a matching aid, not the MSRP (see `feedback_msrp_never_overwritten_by_rrp`
  in project memory).
- For a **non-GW** category with no `games-workshop-uk` row at all, decide
  **with the user, per category** whether that category's own actual
  publisher-official UK retailer should populate `msrp_gbp` instead (e.g.
  Mantic Games UK for Halo: Flashpoint — confirmed explicitly with the user
  2026-09-25: "Mantic is the main MSRP row for Halo Flashpoint"). **Do not
  decide this yourself and do not assume it generalizes to the next non-GW
  category without asking again** — a retailer being "the publisher's own
  store" for one game system doesn't mean the next new UK retailer you
  onboard is automatically that category's MSRP source too.
- Whichever retailer is approved as the MSRP source, the write must always
  be **create-only** — guard with `if product.msrp_gbp is None:` before
  setting it, exactly like `seed_gw_uk_admech_prices.py` does. Never
  unconditionally overwrite on every redeploy; a live price-verification run
  (or a manual correction) may have already updated it since the seed
  command was written.

---

## File map (current — single implementation)

| Purpose                    | File                                                 |
|------------------------------|--------------------------------------------------------|
| Product list / detail / search view | `products/views.py` (region resolved per-request, see above) |
| US URL config               | `products/urls.py` (`app_name = 'products'`)             |
| UK URL config                | `products/urls_uk.py` (`app_name = 'products_uk'`, routes to the same `views.py` functions) |
| List template                | `templates/products/product_list.html` (branches on `region`) |
| Detail template               | `templates/products/product_detail.html` (branches on `region`) |
| Region-aware URL names         | `products/context_processors.py` → `site_stats()` → `products_list_url_name` / `products_detail_url_name` / `products_autocomplete_url_name` |
| GW UK price seed commands       | `products/management/commands/seed_gw_uk_<faction>_prices.py` |
| Other UK retailer seed commands  | `products/management/commands/seed_<retailer>_uk_<category>_prices.py` (same pattern, see Task B) |

There is no `views_uk.py`, `product_list_uk.html`, or `product_detail_uk.html`
— those were deleted 2026-09-25. If you see a reference to them anywhere
(a stale comment, a stray import), that reference is wrong; do not use it as
a cue to recreate the files.

---

## Task A — Adding GW UK prices for a new faction

### Step 1: Get the data from the user

Ask the user for each product:
- `gw_sku` (e.g. `59-10`) — must match an existing Product in the DB
- Product name (for readability in the command)
- GBP price as a `Decimal` (e.g. `35.50`)
- Full GW UK product page URL (e.g. `https://www.warhammer.com/en-GB/shop/...`)

**NEVER invent, guess, or use placeholder prices or URLs.** If a value is
missing, ask before writing any code.

### Step 2: Create the seed command

File: `products/management/commands/seed_gw_uk_<faction>_prices.py`

Use `seed_gw_uk_admech_prices.py` as the exact template:

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

For each product:

```python
product = Product.objects.get(gw_sku=sku)
if product.msrp_gbp is None:            # create-only — never resets a live value
    product.msrp_gbp = gbp_price
    product.save(update_fields=['msrp_gbp'])

cp_defaults = {'url': gw_uk_url, 'in_stock': True, 'not_available': False}
CurrentPrice.objects.update_or_create(
    product=product,
    retailer=retailer,
    defaults=cp_defaults,                              # never resets price on re-run
    create_defaults={**cp_defaults, 'price': gbp_price},  # only sets price on first create
)
```

The `create_defaults` split matters: on every redeploy this command re-runs
(see Step 3), and it must not stomp a price a live updater has since
changed. Only `url`/`in_stock`/`not_available` get reaffirmed on every run;
`price` is set once, at creation.

### Step 3: Add to Procfile

Insert immediately **after** the last `seed_gw_uk_*` (or other UK seed)
command and **before** `python manage.py clear_cache`:

```
&& python manage.py seed_gw_uk_<faction>_prices || true
```

**Every UK retailer seed command belongs in the Procfile, not just GW UK's**
(policy confirmed with the user 2026-09-25) — including a one-time,
user-supplied spreadsheet import. A checked-in, git-tracked command survives
a DB reset or a fresh Railway instance; a one-off `manage.py shell -c`
write does not and leaves no audit trail. Never leave retailer price data
as a direct, uncommitted DB write.

### Step 4: Run it

```bash
cd C:\Users\khleu\ThriftHammer\Thrifthammer
python manage.py seed_gw_uk_<faction>_prices
```

**No Railway CLI override is needed for this.** `Thrifthammer/.env` already
points `DATABASE_URL` directly at the production Postgres instance (via
Railway's public proxy), so a plain local `python manage.py <command>` is
already live on production — confirm this is still true (`grep DATABASE_URL
.env`) before assuming it, since it's an unusual setup and could change.
(See "Fallback: Railway CLI" below for the old override method, kept only in
case `.env` ever stops pointing at production directly.)

Show the user the output and confirm it seeded the expected number of rows
with zero skipped before proceeding.

### Step 5: Commit and push only when the user says so

Never push without explicit approval — running the seed command already put
the data on production (Step 4); committing/pushing is a separate, later
decision.

---

## Task B — Onboarding a brand-new UK retailer

Covers both a recurring/repeatable source (e.g. a future live UK scraper)
and a one-time import (e.g. a user-supplied spreadsheet, like the Mantic
Games UK / Halo: Flashpoint batch on 2026-09-25). Both get a checked-in seed
command — see Step 3 of Task A for why.

### Step 1: Create the Retailer record

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

**If `is_uk=True` is missing, the retailer's prices will leak onto US
pages.** This is a critical data integrity rule.

### Step 2: Create the seed command

File: `products/management/commands/seed_<retailer>_uk_<category>_prices.py`
(e.g. `seed_mantic_uk_halo_flashpoint_prices.py` — read that file, it's now
the canonical worked example for this task, including the `msrp_gbp`
create-only decision documented in its own docstring).

```python
_PRICES = [
    # (gw_sku, gbp_price, url, in_stock)
    ('HALO-019', Decimal('25.00'), 'https://www.manticgames.com/...', True),
    ...
]

for gw_sku, gbp_price, url, in_stock in _PRICES:
    product = Product.objects.get(gw_sku=gw_sku)   # SKUs must already exist — never create products here

    # Only if the user confirmed this retailer is the category's MSRP source —
    # see "The msrp_gbp rule" above. Omit entirely if not confirmed.
    if product.msrp_gbp is None:
        product.msrp_gbp = gbp_price
        product.save(update_fields=['msrp_gbp'])

    cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'GBP'}
    CurrentPrice.objects.update_or_create(
        product=product,
        retailer=retailer,
        defaults=cp_defaults,
        create_defaults={**cp_defaults, 'price': gbp_price},
    )
```

**SKUs must already exist in the catalog.** This task is for matching a new
retailer's prices onto existing products, never for creating new Product
rows — that's a separate, explicitly-approved task (see project rules on
`populate_products`). If the retailer's data includes products with no
matching `gw_sku`, or the catalog has SKUs the retailer's data doesn't
cover, **report both as explicit lists and ask the user** rather than
guessing a fuzzy name match.

**A sold-out/unavailable listing still gets a real price row.** Keep the
real price, set `in_stock=False`, leave `not_available=False` — do not
clear the price to `None` or set `not_available=True` just because a
listing is temporarily out of stock (confirmed with the user 2026-09-25).

### Step 3: No migration needed

`is_uk` already exists on the Retailer model. No schema change is required.

### Step 4: Add to Procfile and run, as in Task A Steps 3–4.

---

## Absolute rules — read before writing any code

1. **Never touch the US side.** Do not edit `products/views.py`'s US-only
   branches, `products/urls.py`, or any existing US seed/populate command
   in a way that changes US behavior. `products/views.py` and the two
   shared templates ARE the correct place to add UK logic now — that's not
   "touching the US side" as long as the `region == 'us'` branch is
   unchanged. If genuinely unsure whether a change affects US output, stop
   and ask.

2. **Never use placeholder data.** No invented prices, guessed URLs, or
   approximate GBP values. If a real value is not available, leave the
   field null and tell the user what is missing.

3. **Never run `populate_products` or any existing populate command.** Only
   create new targeted seed commands. `populate_products.py` is not in the
   Procfile and does not run on Railway — data set there never reaches
   production.

4. **Every new UK retailer must have `is_uk=True`.** Non-negotiable.
   Forgetting it causes UK GBP prices to appear as USD on US product pages.

5. **Never add retailer slugs to a frozenset or hardcoded list.** The
   `Retailer.is_uk` field replaced all slug-based filtering.

6. **Never hardcode a per-category label exception** for "MSRP" or the
   official-listing button text. See the label rules section above — this
   exact mistake has already happened and been fixed once.

7. **`msrp_gbp` is a per-category judgment call outside genuine GW games.**
   Always confirm with the user which retailer (if any) should populate it
   for a new non-GW category — never assume, never carry the decision over
   from a different category. Always write it create-only.

8. **Every UK retailer's seed command is checked into git and added to the
   Procfile** — including one-time spreadsheet imports. Never leave UK
   price data as an uncommitted direct DB write.

9. **Never push without explicit user approval.** Running a seed command
   against production (Step 4 above) is not the same thing as pushing —
   the command already writes to production directly; git push is a
   separate later decision.

10. **Be transparent about every production write.** Before running any
    command against the production DB, state exactly what it will do (rows
    created, fields updated, retailer created/reused). After running,
    report the actual output — not the expected output.

11. **Easy revert.** Each seed command is idempotent via `update_or_create`.
    To undo a bad seed: delete the `CurrentPrice` rows via Django shell or
    admin. The `Retailer` record can be deactivated (`is_active=False`) to
    hide it without deleting.

12. **Every internal link a new template adds must use
    `products_list_url_name` / `products_detail_url_name` /
    `products_autocomplete_url_name`**, never a hardcoded
    `{% url 'products:...' %}`. See "How region is resolved" above.

---

## Production writes — current reality (confirmed 2026-09-25)

`Thrifthammer/.env` hardcodes `DATABASE_URL` to the production Postgres
instance's public Railway proxy. **A plain local `python manage.py
<command>` already writes directly to production — no Railway CLI env
override needed.** Re-verify this before relying on it
(`grep DATABASE_URL .env`), since it's an unusual setup that could change.

### Fallback: Railway CLI (only if `.env` no longer points at production)

```powershell
# Get production DB public URL
railway variables --service Postgres --json

# Run a management command against production
$env:DATABASE_URL = "<DATABASE_PUBLIC_URL>"
python manage.py <command>
```

The internal DB URL (`postgres.railway.internal`) is NOT reachable from
localhost — always use the public URL if this fallback is ever needed.
