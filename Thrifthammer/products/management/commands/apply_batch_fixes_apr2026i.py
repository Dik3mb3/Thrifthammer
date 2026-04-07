"""
apply_batch_fixes_apr2026i
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Codex: Thousand Sons — fix stale GW URL (404 -> current 2025 page)
- Howling Banshees — add ebay_negative_keywords "8028A", fix eBay URL
- Spiritseer — add ebay_negative_keywords "warlock llyanaa"
- Retag Khorne daemon products -> World Eaters faction
- Retag Nurgle daemon products -> Death Guard faction
- Retag Tzeentch daemon products -> Thousand Sons faction
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Faction, Product


class Command(BaseCommand):
    help = "Apr-2026-i: GW URL fix, eBay keyword fixes, daemon faction retags."

    def handle(self, *args, **options):
        updated = 0

        # ── Codex: Thousand Sons — fix GW URL ────────────────────────────────
        try:
            product = Product.objects.get(slug="codex-thousand-sons")
            cp, _ = CurrentPrice.objects.get_or_create(
                product=product, retailer_id=1,
                defaults={"price": None, "url": "", "in_stock": False, "not_available": True},
            )
            new_url = (
                "https://www.warhammer.com/en-US/shop/codex-thousand-sons-hb-2025-eng"
                "?queryID=c036998815859eb1ec5b4730eb018dc1"
            )
            cp.url = new_url
            cp.not_available = False
            cp.save()
            self.stdout.write(f"  Updated GW URL: {product.slug}")
            updated += 1
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  codex-thousand-sons not found"))

        # ── Howling Banshees — add avoid keyword + fix eBay URL ──────────────
        try:
            product = Product.objects.get(slug="aeldari-howling-banshees")
            existing = product.ebay_negative_keywords or ""
            kws = set(existing.split())
            kws.add("8028A")
            product.ebay_negative_keywords = " ".join(sorted(kws))
            product.save()
            # Fix eBay URL
            cp = CurrentPrice.objects.filter(product=product, retailer_id=6).first()
            if cp:
                cp.url = (
                    "https://www.ebay.com/itm/177331201329"
                    "?_skw=howling+banshees+40k"
                    "&epid=1401018977"
                    "&itmmeta=01KNJRGYR5EGHV3JF86K5GV7B1"
                    "&hash=item2949c36531:g:yCwAAeSwU29omjRC"
                    "&itmprp=enc%3AAQALAAAA0GfYFPkwiKCW4ZNSs2u11xA2%2B2Zx4YtyDPcyAPV%2BN9q"
                    "DwN5Hw7HW1t4z2wVQRyTj2hph8fIrcMwr2fYSBu8b0yTiEJjo%2FaltwCT3%2BQ6Yhd"
                    "AbXzrs2%2F%2BzQQF2je2kEpdt7j9CFWhvdee%2BPFTsDWvDEEpuWYwSfzyzUkIS1Ij5"
                    "VLZjEKFRCDXKSWcVATLOTPxHnBYuBWTECWPcIIOGFePc%2FVJ8dJUCZGpeAmsCCgZ5"
                    "qutOHEKaPlL8n7IDN6TOLrguv8Ax%2B%2BhzhiHA0aZqweq3INk%3D%7Ctkp%3A"
                    "Bk9SR5jsw9isZw"
                )
                cp.not_available = False
                cp.save()
            self.stdout.write(f"  Updated Howling Banshees: neg kws + eBay URL")
            updated += 1
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  aeldari-howling-banshees not found"))

        # ── Spiritseer — add avoid keywords ──────────────────────────────────
        try:
            product = Product.objects.get(slug="aeldari-spiritseer")
            existing = product.ebay_negative_keywords or ""
            kws = set(existing.split())
            kws.update({"warlock", "llyanaa"})
            product.ebay_negative_keywords = " ".join(sorted(kws))
            product.save()
            self.stdout.write(f"  Updated Spiritseer: neg kws")
            updated += 1
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  aeldari-spiritseer not found"))

        # ── Daemon faction retags ─────────────────────────────────────────────
        we = Faction.objects.get(slug="world-eaters")
        dg = Faction.objects.get(slug="death-guard")
        ts = Faction.objects.get(slug="thousand-sons")

        khorne_slugs = [
            "khorne-bloodcrushers",
            "khorne-bloodletters",
            "khorne-bloodthirster",
            "khorne-flesh-hounds",
            "khorne-skarbrand",
        ]
        nurgle_slugs = [
            "nurgle-beast-of-nurgle",
            "nurgle-great-unclean-one",
            "nurgle-nurglings",
            "nurgle-plaguebearers",
            "nurgle-plague-drones",
            "nurgle-rotigus",
        ]
        tzeentch_slugs = [
            "tzeentch-blue-horrors-brimstone-horrors",
            "tzeentch-flamers",
            "tzeentch-kairos-fateweaver",
            "tzeentch-lord-of-change",
            "tzeentch-pink-horrors",
            "tzeentch-screamers",
        ]

        for slug in khorne_slugs:
            n = Product.objects.filter(slug=slug).update(faction=we)
            if n:
                self.stdout.write(f"  Retagged {slug} -> World Eaters")
                updated += 1

        for slug in nurgle_slugs:
            n = Product.objects.filter(slug=slug).update(faction=dg)
            if n:
                self.stdout.write(f"  Retagged {slug} -> Death Guard")
                updated += 1

        for slug in tzeentch_slugs:
            n = Product.objects.filter(slug=slug).update(faction=ts)
            if n:
                self.stdout.write(f"  Retagged {slug} -> Thousand Sons")
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. {updated} changes applied."))
