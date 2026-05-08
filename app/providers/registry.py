from app.config import Settings, get_settings
from app.providers.base import ProviderClient
from app.providers.bestbuy import BestBuyProvider
from app.providers.coming_soon import ComingSoonProvider
from app.providers.ebay import EbayProvider


def get_provider_clients(settings: Settings | None = None) -> list[ProviderClient]:
    app_settings = settings or get_settings()

    coming_soon_reason = "Official API/feed integration is planned for this retailer."
    return [
        EbayProvider(app_settings),
        BestBuyProvider(app_settings),
        ComingSoonProvider(app_settings, name="amazon", label="Amazon", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="jcpenney", label="JCPenney", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="kohls", label="Kohl's", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="walmart", label="Walmart", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="target", label="Target", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="macys", label="Macy's", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="newegg", label="Newegg", reason=coming_soon_reason),
        ComingSoonProvider(app_settings, name="tigerdirect", label="TigerDirect", reason=coming_soon_reason),
    ]


def get_provider_map(settings: Settings | None = None) -> dict[str, ProviderClient]:
    return {provider.name: provider for provider in get_provider_clients(settings)}
