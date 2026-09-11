"""
Management command: seed_nk_warhammer_40k_books_prices

Seeds Noble Knight Games BookFormatPrice rows (Paperback/Hardback only,
matching the eBay/Amazon physical-format scope) for the Warhammer 40,000
Books batch, sourced two ways:

  1. A user-provided spreadsheet scrape of Noble Knight's site (90 rows,
     mixing 40K/Horus Heresy/Age of Sigmar titles), cross-referenced against
     our 72-title catalog via 3 parallel research passes.
  2. Direct URLs the user supplied for titles the spreadsheet didn't cover,
     each fetched and verified live before inclusion (title/author/format/
     price/stock) -- Noble Knight, like Amazon, accepts manually-curated
     URLs (unlike eBay, which never does).

Every row here is a real, verified Noble Knight listing for the correct
book and format -- not_available is always False. Rows with price=None and
in_stock=False are real listings that are currently out of print/out of
stock; the URL is kept (per project convention) so affiliate credit still
fires on click-through and the price picks up automatically whenever Noble
Knight restocks.

Notable exclusions/decisions made while sourcing this batch:
  - Blackheart: Claws of the Maelstrom, The Relentless Dead: Noble Knight
    carries a similarly-titled or same-title listing, but in the wrong
    format only (Blackheart's NK match is actually a different book,
    "Huron Blackheart: Master of the Maelstrom"; Relentless Dead exists at
    NK only as Hardcover, we need Paperback) -- excluded.
  - The High Kahl's Oath (paperback): Noble Knight's only paperback listing
    is a used "Excellent" condition copy ($15 vs $25-30 for comparable new
    paperbacks in this batch) -- excluded as not a fair "new" price
    comparison, per the same convention used for the Horus Heresy batch.
  - Warboss: Noble Knight only carries this in Hardback; we need Paperback
    -- not carried.
  - Ghazghkull Thraka: Prophet of the Waaagh!: one Noble Knight listing
    sharing this exact title is actually a different, unrelated book
    (author "Denny Flowers", different plot) -- excluded; the correct
    listing (author Nate Crowley, matches our book) is used instead.
  - Ghosts of Cadia: Noble Knight's page shows author "Robert Rath", but
    our own research (cross-verified via multiple sources) confirmed the
    author is Rob Young -- user confirmed our attribution is correct, this
    is treated as a Noble Knight data error, not a different book, since
    title/format/premise all otherwise match.
  - Shadow of the Eighth: our GW-sourced data only has a Paperback edition,
    but Noble Knight carries a real Hardback edition too (confirmed via
    live fetch) -- included as a new Hardback price/format option for this
    product per explicit user instruction, even though no GW Hardback
    reference row exists for it (so this format has no MSRP/discount
    reference for now, same as any Amazon-only E-Book/Audio Book format).
  - Gaunt's Ghosts: The Victory (Part Two): Noble Knight's real, in-stock
    price is $195.00 -- a major outlier vs. every other paperback in this
    batch (~$16-25), but confirmed correct book/author/format. Shown as-is
    per explicit user instruction and the site's standing "no price
    ceiling" policy (same treatment as this exact title's $149.50 eBay
    price found earlier).

Not added to the Procfile -- run manually, on demand, same as the other
one-time seed commands introduced for the Books feature.

Usage:
    python manage.py seed_nk_warhammer_40k_books_prices
"""

from django.core.management.base import BaseCommand, CommandError

from prices.models import BookFormatPrice
from products.models import Product, Retailer

NK_AWID = '1576'

# (gw_sku, format, listing_title, price_or_None, url, in_stock)
NK_PRICES = [
    # -- From spreadsheet matches --
    ('BOOK-40K-043', 'softback', 'Leviathan', 16.49, 'https://www.nobleknight.com/P/2148143382/Leviathan', True),
    ('BOOK-40K-058', 'softback', 'Infinite and the Divine, The', 14.49, 'https://www.nobleknight.com/P/2147920776/The-Infinite-and-the-Divine', True),
    ('BOOK-40K-058', 'hardback', 'Infinite and the Divine, The', 31.95, 'https://www.nobleknight.com/P/2148506219/Infinite-and-the-Divine-The', True),
    ('BOOK-40K-035', 'softback', 'Renegades - Harrowmaster', 16.49, 'https://www.nobleknight.com/P/2148447830/Renegades---Harrowmaster', True),
    ('BOOK-40K-007', 'softback', 'Assassinorum Kingmaker', 14.49, 'https://www.nobleknight.com/P/2148029936/Assassinorum-Kingmaker', True),
    ('BOOK-40K-039', 'softback', 'Krieg - A Death Korps Novel', 14.49, 'https://www.nobleknight.com/P/2148352692/Krieg---A-Death-Korps-Novel', True),
    ('BOOK-40K-020', 'softback', 'Dark Imperium - Godblight', 14.49, 'https://www.nobleknight.com/P/2147996330/Dark-Imperium---Godblight', True),
    ('BOOK-40K-021', 'softback', 'Dark Imperium - Plague War (2nd Edition)', 14.49, 'https://www.nobleknight.com/P/2147986349/Dark-Imperium---Plague-War-2nd-Edition', True),
    ('BOOK-40K-011', 'softback', "Brutal Kunnin'", 14.49, 'https://www.nobleknight.com/P/2147835660/Brutal-Kunnin', True),
    ('BOOK-40K-003', 'softback', 'Ahriman - The Omnibus', 18.95, 'https://www.nobleknight.com/P/2147677517/Ahriman---The-Omnibus', True),
    ('BOOK-40K-047', 'softback', 'Night Lords - The Omnibus', 18.95, 'https://www.nobleknight.com/P/2148201358/Night-Lords---The-Omnibus', True),
    ('BOOK-40K-005', 'softback', 'Belisarius Cawl - Archmagos', 16.49, 'https://www.nobleknight.com/P/2148503864/Belisarius-Cawl---Archmagos', True),
    ('BOOK-40K-066', 'softback', 'Vagabond Squadron', 16.49, 'https://www.nobleknight.com/P/2148490480/Vagabond-Squadron', True),
    ('BOOK-40K-038', 'softback', 'Krakenblood', 16.49, 'https://www.nobleknight.com/P/2148490476/Krakenblood', True),
    ('BOOK-40K-070', 'softback', 'Voidscarred - An Aeldari Corsairs Novel', 16.49, 'https://www.nobleknight.com/P/2148485610/Voidscarred---An-Aeldari-Corsairs-Novel', True),
    ('BOOK-40K-072', 'softback', 'Yarrick - the Omnibus', 18.95, 'https://www.nobleknight.com/P/2148457730/Yarrick---the-Omnibus', True),
    ('BOOK-40K-049', 'softback', 'Paragon of Faith and Other Stories', 16.49, 'https://www.nobleknight.com/P/2148448506/Paragon-of-Faith-and-Other-Stories', True),
    ('BOOK-40K-012', 'softback', 'Carnage Unending', 14.49, 'https://www.nobleknight.com/P/2148448869/Carnage-Unending', True),
    ('BOOK-40K-013', 'hardback', 'Chem Dog', 27.95, 'https://www.nobleknight.com/P/2148426702/Chem-Dog', True),
    ('BOOK-40K-026', 'hardback', 'Faith & Fire (Anniversary Edition)', 31.95, 'https://www.nobleknight.com/P/2148426651/Faith-and-Fire-Anniversary-Edition', True),
    ('BOOK-40K-036', 'softback', 'Huron Blackheart - Master of the Maelstrom', 16.49, 'https://www.nobleknight.com/P/2148414896/Huron-Blackheart---Master-of-the-Maelstrom', True),
    ('BOOK-40K-033', 'hardback', 'Ghost Legion', 27.95, 'https://www.nobleknight.com/P/2148414900/Ghost-Legion', True),
    ('BOOK-40K-004', 'hardback', 'Apostle', 27.95, 'https://www.nobleknight.com/P/2148407533/Apostle', True),
    ('BOOK-40K-028', 'softback', 'Fulgrim - The Perfect Son', 16.49, 'https://www.nobleknight.com/P/2148397969/Fulgrim---The-Perfect-Son', True),
    ('BOOK-40K-027', 'softback', 'Farsight - Blade of Truth', 16.49, 'https://www.nobleknight.com/P/2148397968/Farsight---Blade-of-Truth', True),
    ('BOOK-40K-067', 'softback', 'Vaults of Terra - The Omnibus', 18.95, 'https://www.nobleknight.com/P/2148397967/Vaults-of-Terra---The-Omnibus', True),
    ('BOOK-40K-063', 'softback', 'Twice-Dead King, The - Omnibus', 18.95, 'https://www.nobleknight.com/P/2148373810/Twice-Dead-King-The---Omnibus', True),
    ('BOOK-40K-050', 'softback', 'Ravenor - The Omnibus', 22.95, 'https://www.nobleknight.com/P/2148320258/Ravenor---The-Omnibus', True),
    ('BOOK-40K-042', 'softback', 'Legends of the Wolf - The Omnibus', 22.95, 'https://www.nobleknight.com/P/2148298771/Legends-of-the-Wolf---The-Omnibus', True),
    ('BOOK-40K-017', 'softback', 'Da Big Dakka', 16.49, 'https://www.nobleknight.com/P/2148213953/Da-Big-Dakka', True),
    ('BOOK-40K-055', 'softback', 'Fall of Cadia, The', 16.49, 'https://www.nobleknight.com/P/2148176257/Fall-of-Cadia-The', True),
    ('BOOK-40K-031', 'softback', 'Genefather', 16.49, 'https://www.nobleknight.com/P/2148176259/Genefather', True),
    ('BOOK-40K-059', 'softback', 'Lion, The - Son of the Forest', 16.49, 'https://www.nobleknight.com/P/2148107855/Lion-The---Son-of-the-Forest', True),
    ('BOOK-40K-044', 'hardback', 'Longshot - An Astra Militarum Novel', 27.95, 'https://www.nobleknight.com/P/2148496203/Longshot---An-Astra-Militarum-Novel', True),
    ('BOOK-40K-065', 'softback', 'Tomb World', 16.49, 'https://www.nobleknight.com/P/2148485612/Tomb-World', True),
    ('BOOK-40K-062', 'softback', 'Remnant Blade, The', 16.49, 'https://www.nobleknight.com/P/2148485624/Remnant-Blade-The', True),
    ('BOOK-40K-068', 'softback', 'Veterans of the Fall - An Astra MIlitarum Novel', 16.49, 'https://www.nobleknight.com/P/2148457488/Veterans-of-the-Fall---An-Astra-MIlitarum-Novel', True),
    ('BOOK-40K-002', 'hardback', 'Aestred Thurga - Pyre of Faith', 18.95, 'https://www.nobleknight.com/P/2148448503/Aestred-Thurga---Pyre-of-Faith', True),
    ('BOOK-40K-022', 'hardback', 'Death Rider', 27.95, 'https://www.nobleknight.com/P/2148414864/Death-Rider', True),
    ('BOOK-40K-001', 'softback', 'Above and Beyond - A Lucille Von Shard Novel', 16.49, 'https://www.nobleknight.com/P/2148320230/Above-and-Beyond---A-Lucille-Von-Shard-Novel', True),

    # -- From user-provided links (verified live) --
    ('BOOK-40K-064', 'hardback', 'Wicked and the Warped, The', None, 'https://www.nobleknight.com/P/2148506224/Wicked-and-the-Warped-The', False),
    ('BOOK-40K-045', 'softback', 'Minka Lesk - The Last Whiteshield', 45.00, 'https://www.nobleknight.com/P/2148301802/Minka-Lesk---The-Last-Whiteshield', True),
    ('BOOK-40K-029', 'softback', "Gaunt's Ghosts - The Founding, Omnibus (2007 Edition)", 50.00, 'https://www.nobleknight.com/P/2147369581/Gaunts-Ghosts---The-Founding-Omnibus-2007-Edition', True),
    ('BOOK-40K-014', 'softback', 'Ciaphas Cain - Hero of the Imperium (2020 Printing)', None, 'https://www.nobleknight.com/P/2148301812/Ciaphas-Cain---Hero-of-the-Imperium-2020-Printing', False),
    ('BOOK-40K-041', 'softback', 'Legends of the Waaagh!', None, 'https://www.nobleknight.com/P/2148457477/Legends-of-the-Waaagh', False),
    ('BOOK-40K-056', 'softback', 'Green Tide, The - An Ork Omnibus', None, 'https://www.nobleknight.com/P/2148426662/Green-Tide-The---An-Ork-Omnibus', False),
    ('BOOK-40K-037', 'softback', 'Interceptor City', None, 'https://www.nobleknight.com/P/2148366131/Interceptor-City', False),
    ('BOOK-40K-046', 'softback', 'Morvenn Vahl - Spear of Faith', None, 'https://www.nobleknight.com/P/2148354524/Morvenn-Vahl---Spear-of-Faith', False),
    ('BOOK-40K-052', 'softback', 'Siege of Vraks', 25.00, 'https://www.nobleknight.com/P/2148334719/Siege-of-Vraks', True),
    ('BOOK-40K-053', 'softback', 'Dark Coil Damnation, The', None, 'https://www.nobleknight.com/P/2148335165/Dark-Coil-Damnation-The', False),
    ('BOOK-40K-040', 'softback', "Lazarus - Enmity's Edge", None, 'https://www.nobleknight.com/P/2148482923/Lazarus---Enmitys-Edge', False),
    ('BOOK-40K-015', 'softback', 'Ciaphas Cain #11 - Vainglorious', 30.00, 'https://www.nobleknight.com/P/2148301811/Ciaphas-Cain-11---Vainglorious', True),
    ('BOOK-40K-016', 'softback', 'Cypher - Lord of the Fallen', None, 'https://www.nobleknight.com/P/2148141193/Cypher---Lord-of-the-Fallen', False),
    ('BOOK-40K-032', 'softback', 'Ghazghkull Thraka - Prophet of the Waaagh!', None, 'https://www.nobleknight.com/P/2148335155/Ghazghkull-Thraka---Prophet-of-the-Waaagh', False),
    ('BOOK-40K-030', 'softback', "Gaunt's Ghosts - The Victory, Part 2", 195.00, 'https://www.nobleknight.com/P/2148301814/Gaunts-Ghosts---The-Victory-Part-2', True),
    ('BOOK-40K-060', 'softback', 'Macharian Crusade, The #1 - Angel of Fire', None, 'https://www.nobleknight.com/P/2148037180/Macharian-Crusade-The-1---Angel-of-Fire', False),
    ('BOOK-40K-054', 'hardback', 'Devastation of Baal, The', None, 'https://www.nobleknight.com/P/2148496200/Devastation-of-Baal-The', False),
    ('BOOK-40K-034', 'hardback', 'Ghosts of Cadia', None, 'https://www.nobleknight.com/P/2148496201/Ghosts-of-Cadia', False),
    ('BOOK-40K-006', 'hardback', 'Armageddon - Season of Fire', None, 'https://www.nobleknight.com/P/2148503534/Armageddon---Season-of-Fire', False),
    ('BOOK-40K-018', 'hardback', 'Da Freebooterz Code', None, 'https://www.nobleknight.com/P/2148457526/Da-Freebooterz-Code', False),
    ('BOOK-40K-025', 'softback', 'Dominion Genesis', 15.00, 'https://www.nobleknight.com/P/2148317121/Dominion-Genesis', True),
    ('BOOK-40K-051', 'hardback', 'Minka Lesk - Shadow of the Eighth', 65.00, 'https://www.nobleknight.com/P/2148141190/Minka-Lesk---Shadow-of-the-Eighth', True),
    ('BOOK-40K-048', 'softback', 'Once a Killer', None, 'https://www.nobleknight.com/P/2148118024/Once-a-Killer', False),
]


class Command(BaseCommand):
    """Seed Noble Knight BookFormatPrice rows for the Warhammer 40,000 Books batch."""

    help = 'Seeds verified Noble Knight Games prices for Warhammer 40,000 Books. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        nk_retailer = Retailer.objects.filter(slug='noble-knight-games').first()
        if not nk_retailer:
            raise CommandError('Noble Knight Games retailer not found.')

        created = updated = 0

        for gw_sku, fmt, listing_title, price, url, in_stock in NK_PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Product not found: {gw_sku}'))
                continue

            affiliate_url = f'{url}?awid={NK_AWID}'

            bfp, was_created = BookFormatPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                format=fmt,
                defaults={
                    'price': price,
                    'currency': 'USD',
                    'url': affiliate_url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': False,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

            status = f'${price:.2f}' if price is not None else ('out of stock' if not in_stock else 'in stock, no price')
            self.stdout.write(
                f"  {'Created' if was_created else 'Updated'}: {product.name} ({bfp.get_format_display()}) - {status}"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created} created, {updated} updated.'
        ))
