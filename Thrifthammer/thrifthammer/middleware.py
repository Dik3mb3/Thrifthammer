"""
Custom middleware for ThriftHammer.

ContentSecurityPolicyMiddleware adds a Content-Security-Policy header to
every response.  The policy is intentionally permissive on script-src and
style-src because the project ships a large amount of inline JS/CSS in
Django templates.  Future work: migrate inline scripts to external files
and switch script-src from 'unsafe-inline' to strict nonces or hashes.
"""


class ContentSecurityPolicyMiddleware:
    """
    Append a Content-Security-Policy response header to every request.

    Placed after SecurityMiddleware / WhiteNoiseMiddleware in MIDDLEWARE so
    it runs for both dynamic Django responses and static-file responses.
    Does not overwrite a CSP header already set by a view (e.g. the admin).
    """

    # External origins used by the site — update here when adding new ones.
    _POLICY = (
        # Restrict all unspecified fetch types to same origin.
        "default-src 'self'; "

        # Scripts: same-origin + inline (required for all template <script>
        # blocks) + Google Tag Manager / Analytics.
        "script-src 'self' 'unsafe-inline' "
        "https://www.googletagmanager.com "
        "https://www.google-analytics.com "
        "https://tagmanager.google.com; "

        # Styles: same-origin + inline (required for style="" attributes
        # throughout templates) + Google Fonts CSS.
        "style-src 'self' 'unsafe-inline' "
        "https://fonts.googleapis.com; "

        # Fonts: same-origin + Google Fonts CDN.
        "font-src 'self' "
        "https://fonts.gstatic.com; "

        # Images: same-origin + data URIs + all HTTPS.
        # Broad HTTPS allowance required: product images are hosted on GW,
        # Amazon, and other retailer CDNs whose domains are not fixed.
        "img-src 'self' data: https:; "

        # Fetch / XHR: same-origin (watchlist toggle, army-calc save,
        # search autocomplete) + Google Analytics collection endpoint.
        "connect-src 'self' "
        "https://www.google-analytics.com "
        "https://analytics.google.com "
        "https://www.googletagmanager.com; "

        # No iframes, objects, or embeds.
        "frame-src 'none'; "
        "object-src 'none'; "

        # Prevent the page from being framed (belt-and-suspenders with
        # X_FRAME_OPTIONS = 'DENY' in settings.py).
        "frame-ancestors 'none'; "

        # Forms may only submit to the same origin.
        "form-action 'self'; "

        # Prevent <base href="..."> injection attacks.
        "base-uri 'self'; "

        # Automatically upgrade any stray HTTP sub-resource requests to HTTPS.
        "upgrade-insecure-requests;"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = self._POLICY
        return response
