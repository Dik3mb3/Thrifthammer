"""
apply_batch_fixes_apr2026k
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix category=None for 70 phase-2/3 products -> Warhammer 40,000 (id=1)
- Lokhust Destroyer Squadron: add 'green rods' avoid kws, fix eBay URL
- Tesseract Vault + Obelisk: fix search name, clear not_available so API can find listing
- Drop Pods: change search name to "Space Marine Drop Pods"
- Kayvaan Shrike: add SKU avoid 'tribute'
- Gladiator Valiant: change search name to "Space Marine Gladiator Valiant"
- Ork Trukk: add SKU avoid 'terrain wargaming'
- Codex: Space Marines: change search name to "Codex Space Marines 10th edition"
- Wazbom Blastajet / Blitza-Bommer / Burna-Bommer: block item ID 225443499300
- Lord of Change: (global '1997' keyword handled in ebay_api_client.py)
- Beast Snagga Boyz: add SKU avoid 'zodgrod'
- Logan Grimnar: add SKU avoid 'wolves rocks'
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product


class Command(BaseCommand):
    help = "Apr-2026-k: category fix, search name fixes, eBay URL/keyword fixes."

    def _add_neg_kws(self, product, *new_kws):
        """Merge new keywords into ebay_negative_keywords, deduplicating."""
        existing = set((product.ebay_negative_keywords or "").split())
        existing.update(k.lower() for k in new_kws)
        product.ebay_negative_keywords = " ".join(sorted(existing))
        product.save()

    def handle(self, *args, **options):
        wh40k = Category.objects.get(slug="warhammer-40000")

        # ── Fix category=None for all phase-2/3 products ─────────────────────
        no_cat = Product.objects.filter(
            batch_tag__in=["phase-2", "phase-3"], category__isnull=True
        )
        count = no_cat.count()
        no_cat.update(category=wh40k)
        # Bust list page cache after bulk update
        cache.add("product_list_generation", 0, timeout=None)
        cache.incr("product_list_generation")
        self.stdout.write(f"  Fixed category for {count} products -> Warhammer 40,000")

        # ── Lokhust Destroyer Squadron ────────────────────────────────────────
        try:
            p = Product.objects.get(slug="necron-lokhust-destroyer-squadron")
            self._add_neg_kws(p, "green", "rods")
            cp = CurrentPrice.objects.filter(product=p, retailer_id=6).first()
            if cp:
                cp.url = (
                    "https://www.ebay.com/itm/157813540131"
                    "?_skw=Lokhust+Destroyer+Squadron"
                    "&epid=6041914035"
                    "&itmmeta=01KNJT3G1WKQKTQRYM26SQ4JDZ"
                    "&hash=item24be6b8523:g:L9oAAeSwfQhpoTgl"
                    "&itmprp=enc%3AAQALAAAA4GfYFPkwiKCW4ZNSs2u11xBvVmxUH94z0ryyixcMiI%2FLaUu"
                    "FFCmBVBsyG2sbn5eLifjhcapDK4a5QluMsOZ3%2BWUEe24Au71O0i52NoDFVkvID7M116XC"
                    "%2FtdsFCHdFAGTB2RzwxlQTNMVPwutXmLY3M3JYB3cUnhGrbPE3Gl%2BFN2APxwEo80YT"
                    "%2FeC7Ud9TaHSyXK9SDu%2B3Pn7FOrL0qdSnF2dyQ%2FlKtspzd8m1jY3ZFKgYH7CM3BE"
                    "E9nfHP9vD7A4fV3BZDWXb8C41VM9QCiGup2hE0efko2csJN0L%2BwsUvOO%7Ctkp%3A"
                    "Bk9SR5KBjtqsZw"
                )
                cp.not_available = False
                cp.save()
            self.stdout.write("  Lokhust Destroyer Squadron: avoid kws + eBay URL fixed")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  necron-lokhust-destroyer-squadron not found"))

        # ── Tesseract Vault: fix search name, clear not_available ─────────────
        try:
            p = Product.objects.get(slug="necron-tesseract-vault")
            p.ebay_search_name = "Tesseract Vault Necron Warhammer"
            p.save()
            cp, _ = CurrentPrice.objects.get_or_create(
                product=p, retailer_id=6,
                defaults={"price": None, "url": "", "in_stock": False, "not_available": True},
            )
            cp.not_available = False
            cp.url = ""  # Let the API find it fresh
            cp.price = None
            cp.save()
            self.stdout.write("  Tesseract Vault: search name fixed, eBay row cleared for API")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  necron-tesseract-vault not found"))

        # ── Obelisk & Transcendent C'tan: same search name as Tesseract Vault ─
        try:
            p = Product.objects.get(slug="necron-obelisk")
            p.ebay_search_name = "Tesseract Vault Necron Warhammer"
            p.save()
            cp, _ = CurrentPrice.objects.get_or_create(
                product=p, retailer_id=6,
                defaults={"price": None, "url": "", "in_stock": False, "not_available": True},
            )
            cp.not_available = False
            cp.url = ""
            cp.price = None
            cp.save()
            self.stdout.write("  Obelisk & Transcendent C'tan: search name set, eBay cleared for API")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  necron-obelisk not found"))

        # ── Drop Pods: change search name ────────────────────────────────────
        try:
            p = Product.objects.get(slug="space-marine-drop-pods")
            p.ebay_search_name = "Space Marine Drop Pods Warhammer"
            p.save()
            self.stdout.write("  Drop Pods: search name updated")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  space-marine-drop-pods not found"))

        # ── Kayvaan Shrike: add SKU avoid 'tribute' ───────────────────────────
        try:
            p = Product.objects.get(slug="raven-guard-kayvaan-shrike")
            self._add_neg_kws(p, "tribute")
            self.stdout.write("  Kayvaan Shrike: added avoid 'tribute'")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  raven-guard-kayvaan-shrike not found"))

        # ── Gladiator Valiant: change search name ─────────────────────────────
        try:
            p = Product.objects.get(slug="space-marine-gladiator-valiant")
            p.ebay_search_name = "Space Marine Gladiator Valiant Warhammer"
            p.save()
            self.stdout.write("  Gladiator Valiant: search name updated")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  space-marine-gladiator-valiant not found"))

        # ── Ork Trukk: add SKU avoid 'terrain wargaming' ─────────────────────
        try:
            p = Product.objects.get(slug="ork-trukk")
            self._add_neg_kws(p, "terrain", "wargaming")
            self.stdout.write("  Ork Trukk: added avoid 'terrain wargaming'")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ork-trukk not found"))

        # ── Codex: Space Marines — search name ───────────────────────────────
        try:
            p = Product.objects.get(slug="codex-space-marines")
            p.ebay_search_name = "Codex Space Marines 10th edition Warhammer"
            p.save()
            self.stdout.write("  Codex: Space Marines: search name updated")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  codex-space-marines not found"))

        # ── Wazbom / Blitza / Burna Bommer: block item ID 225443499300 ────────
        for slug in ("ork-wazbom-blastajet", "ork-blitza-bommer", "ork-burna-bommer"):
            try:
                p = Product.objects.get(slug=slug)
                self._add_neg_kws(p, "225443499300")
                self.stdout.write(f"  {slug}: blocked item ID 225443499300")
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  {slug} not found"))

        # ── Beast Snagga Boyz: add SKU avoid 'zodgrod' ───────────────────────
        try:
            p = Product.objects.get(slug="ork-beast-snagga-boyz")
            self._add_neg_kws(p, "zodgrod")
            self.stdout.write("  Beast Snagga Boyz: added avoid 'zodgrod'")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ork-beast-snagga-boyz not found"))

        # ── Logan Grimnar: add SKU avoid 'wolves rocks' ───────────────────────
        try:
            p = Product.objects.get(slug="space-wolves-logan-grimnar")
            self._add_neg_kws(p, "wolves", "rocks")
            self.stdout.write("  Logan Grimnar: added avoid 'wolves rocks'")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  space-wolves-logan-grimnar not found"))

        self.stdout.write(self.style.SUCCESS("Done."))
