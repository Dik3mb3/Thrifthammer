"""
apply_batch_fixes_apr2026j
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Delete craftworlds-wraithguard (duplicate of aeldari-wraithguard, GW SKU 46-26)
- Kharseth: fix ebay_search_name, set eBay URL
- Warlock Skyrunner: copy NK + eBay URLs from Farseer Skyrunner (dual kit)
- Starfang: copy eBay URL from Vyper, update ebay_search_name (dual kit)
- Yvraine: add 'triumvirate' avoid keyword, update eBay URL to correct listing
- The Visarch: add 'triumvirate' avoid keyword, update eBay URL to correct listing
- The Yncarne: set eBay URL (was showing not_available)
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product


class Command(BaseCommand):
    help = "Apr-2026-j: Aeldari duplicate delete, dual-kit URL sync, Ynnari keyword fixes."

    def _set_ebay_url(self, product, url):
        """Update or create the eBay CurrentPrice row for a product."""
        cp, _ = CurrentPrice.objects.get_or_create(
            product=product,
            retailer_id=6,
            defaults={"price": None, "url": "", "in_stock": False, "not_available": True},
        )
        cp.url = url
        cp.not_available = False
        cp.save()

    def handle(self, *args, **options):

        # ── Delete duplicate Wraithguard (craftworlds-wraithguard, SKU 46-26) ─
        deleted_count, _ = Product.objects.filter(slug="craftworlds-wraithguard").delete()
        if deleted_count:
            self.stdout.write("  Deleted craftworlds-wraithguard (duplicate SKU 46-26)")
        else:
            self.stdout.write(self.style.WARNING("  craftworlds-wraithguard not found, skipping"))

        # ── Kharseth: fix search name + eBay URL ─────────────────────────────
        try:
            p = Product.objects.get(slug="aeldari-kharseth")
            p.ebay_search_name = "Aeldari Kharseth"
            p.save()
            self._set_ebay_url(
                p,
                "https://www.ebay.com/itm/356501702415"
                "?_skw=Kharseth"
                "&itmmeta=01KNJSBVGZDRZKAAEAHDCZ3SRE"
                "&hash=item530128470f:g:doAAAeSw8rRpv4wG"
                "&itmprp=enc%3AAQALAAAA0GfYFPkwiKCW4ZNSs2u11xA9L2pDZk6jVWKleiB4x7HTwquU5x"
                "BO1LDn%2FaRqEMk51eMIAAxwzgy2uB6eVP6daaDnUDzfTfShwE4Bf%2B3Dlpbwmvk%2FboDr"
                "6NnsCIU%2FktjbVoUPaND6y9hVf7QlAaRIn3vm43u8uc7RMCsLhBJzbQYptcfErynH13Oj05"
                "ejDoCbl82l2K1lXAFQBhoMErT8oNVzo0qcf259zUY6ZgsNifumLsAGBxA3XKk0kVIShdqY%2B"
                "JMfqJxJ%2BcPXcxf7IqUHD90%3D%7Ctkp%3ABk9SR9a4r9msZw",
            )
            self.stdout.write("  Updated Kharseth: search name + eBay URL")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  aeldari-kharseth not found"))

        # ── Warlock Skyrunner: copy NK + eBay URLs from Farseer Skyrunner ────
        try:
            farseer = Product.objects.get(slug="aeldari-farseer-skyrunner")
            warlock = Product.objects.get(slug="aeldari-warlock-skyrunner")

            for rid in (3, 6):  # NK, eBay
                src = CurrentPrice.objects.filter(product=farseer, retailer_id=rid, not_available=False).first()
                if src and src.url:
                    dst, _ = CurrentPrice.objects.get_or_create(
                        product=warlock,
                        retailer_id=rid,
                        defaults={"price": None, "url": "", "in_stock": False, "not_available": True},
                    )
                    dst.url = src.url
                    dst.price = src.price
                    dst.in_stock = src.in_stock
                    dst.not_available = False
                    dst.save()
                    self.stdout.write(f"  Warlock Skyrunner r{rid}: copied from Farseer Skyrunner")
        except Product.DoesNotExist as e:
            self.stdout.write(self.style.WARNING(f"  Warlock/Farseer Skyrunner not found: {e}"))

        # ── Starfang: copy eBay URL from Vyper, update search name ───────────
        try:
            vyper = Product.objects.get(slug="aeldari-vyper")
            starfang = Product.objects.get(slug="aeldari-starfang")

            starfang.ebay_search_name = "Vyper Aeldari Warhammer"
            starfang.save()

            src = CurrentPrice.objects.filter(product=vyper, retailer_id=6, not_available=False).first()
            if src and src.url:
                dst, _ = CurrentPrice.objects.get_or_create(
                    product=starfang,
                    retailer_id=6,
                    defaults={"price": None, "url": "", "in_stock": False, "not_available": True},
                )
                dst.url = src.url
                dst.price = src.price
                dst.in_stock = src.in_stock
                dst.not_available = False
                dst.save()
                self.stdout.write("  Starfang: search name updated + eBay URL copied from Vyper")
        except Product.DoesNotExist as e:
            self.stdout.write(self.style.WARNING(f"  Starfang/Vyper not found: {e}"))

        # ── Yvraine: add 'triumvirate' avoid keyword + fix eBay URL ──────────
        try:
            p = Product.objects.get(slug="aeldari-yvraine")
            kws = set((p.ebay_negative_keywords or "").split())
            kws.add("triumvirate")
            p.ebay_negative_keywords = " ".join(sorted(kws))
            p.save()
            self._set_ebay_url(
                p,
                "https://www.ebay.com/itm/186318290415"
                "?_skw=yvraine+40k"
                "&itmmeta=01KNJSMFW8QTQN8513GE687VTB"
                "&hash=item2b616f7def:g:Sa8AAOSwJxdl3jr0"
                "&itmprp=enc%3AAQALAAAA8GfYFPkwiKCW4ZNSs2u11xDAY01tcMrX9djKkf%2B6WtQtaB8o9"
                "y%2BiURAxB%2BHKVmSgRRBaxUkANK%2B1MZ7pz%2FlnuZp5U52pDkkGRihnFeRBVpJnDMKA71"
                "cWcRopNT1Y2XHr2BwZKr2eZQ9%2BXMwWGNpG5ScZSd6VtQnwrreojSrtrE5mXUEuvOChtiXL"
                "ZWCu6C2fBS8CQbOnZ6cegvYD9gUhrjpbe34z2SuyA3PKDe9NcfopZn1NCJQNG4pdwNk54QxOI"
                "xr2HumZSrSfsU8SlsHo8UWcy6uwrqLzEK%2F1Zdh9P1k06e0TVwMpdw0O97vRUmanNA%3D%3D"
                "%7Ctkp%3ABk9SR7b-0dmsZw",
            )
            self.stdout.write("  Yvraine: added 'triumvirate' avoid kw + updated eBay URL")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  aeldari-yvraine not found"))

        # ── The Visarch: add 'triumvirate' avoid keyword + fix eBay URL ──────
        try:
            p = Product.objects.get(slug="aeldari-the-visarch")
            kws = set((p.ebay_negative_keywords or "").split())
            kws.add("triumvirate")
            p.ebay_negative_keywords = " ".join(sorted(kws))
            p.save()
            self._set_ebay_url(
                p,
                "https://www.ebay.com/itm/177491019940"
                "?_skw=visarch+40k"
                "&epid=5055673722"
                "&itmmeta=01KNJSPWX54FWACPF16X53V6WG"
                "&hash=item29534a08a4:g:bV8AAeSwF69pAi5L"
                "&itmprp=enc%3AAQALAAAA0GfYFPkwiKCW4ZNSs2u11xAcoqykf7zkZXkWG7%2FITTJCRoedx"
                "q6JWglOPwIep0a%2FoDSFXy6QXsHyjrmG8hwr4l47R%2FMT4TA7wwvQ8%2Fsyt0Xx8hmp7Po4"
                "vWll6z2GIAfUkz%2BAR%2BTFrQPdsKFpRCTEWsQygdBZrgZiRgvSYkJKuSl8biMio4KrVLV4"
                "Dl5ttZfRi%2BPm4J3HiYFctlYRG7nAql%2FfuLb7R3%2B7oh5ksygLhiCOYTN3UHbACBqqY"
                "ScFDYgnzt8Q2hOcr4YzTR18ckYQFk%3D%7Ctkp%3ABk9SR-7O29msZw",
            )
            self.stdout.write("  The Visarch: added 'triumvirate' avoid kw + updated eBay URL")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  aeldari-the-visarch not found"))

        # ── The Yncarne: set eBay URL ─────────────────────────────────────────
        try:
            p = Product.objects.get(slug="aeldari-the-yncarne")
            self._set_ebay_url(
                p,
                "https://www.ebay.com/itm/177491019927"
                "?_skw=The+Yncarne"
                "&epid=13055163771"
                "&itmmeta=01KNJSV5AFR2NHATQ8ECC68M2D"
                "&hash=item29534a0897:g:MHgAAeSwW6JpAi4f"
                "&itmprp=enc%3AAQALAAAA8GfYFPkwiKCW4ZNSs2u11xBBhiLdpErtnKBwrIDIJpz%2FHNRCk9"
                "OvY2rGLDN%2BdNF7feYFJcJ2zKql%2FsnXxNC6Q7peFti3XwVu5vUZl6gPiesCRmQiv20fjZe"
                "EpaIP5WNIEV%2FnM88XkWIPwDtSK9mXmJ72lI3Cw4XLYofbZur50AXQ%2BBfOyDFuX886ukZI"
                "j%2Bu7cWrxRV5r%2BkKkrl1QlgxBokm9D%2BqDIpC%2BPSeZYBuKVaaW4YVBfIoxaJ0Zo02TA"
                "%2BPJjettZIksOJ4OnhR02n1Z8plK%2BxMp6nCJXhYhgP%2FcEmFGWwd0R7a2Kl8KRQHFMlXF"
                "Pw%3D%3D%7Ctkp%3ABk9SR7TV7NmsZw",
            )
            self.stdout.write("  The Yncarne: eBay URL set")
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING("  aeldari-the-yncarne not found"))

        self.stdout.write(self.style.SUCCESS("Done."))
