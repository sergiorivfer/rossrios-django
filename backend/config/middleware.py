class RegionMiddleware:
    """
    Define request.region en cada request.
    Prioridad:
      1) subdominio (ca.* / us.*)
      2) session["region"]
      3) default CA
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = (request.get_host() or "").split(":")[0].lower()

        region = None
        if host.startswith("ca."):
            region = "CA"
        elif host.startswith("us."):
            region = "US"

        if not region:
            region = request.session.get("region")

        if region not in ("CA", "US"):
            region = "CA"

        request.region = region
        request.session["region"] = region

        return self.get_response(request)