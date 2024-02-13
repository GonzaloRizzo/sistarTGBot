from .providers import SistarbancProvider, ItauProvider
from typing import Union

# from .providers import ItauProvider, SistarbancProvider

Provider = Union[
    ItauProvider,
    SistarbancProvider,
]


class ProviderCache:
    cache = {}

    providers: dict[str, type[Provider]] = {
        'itau': ItauProvider,
        "sistarbanc": SistarbancProvider,
    }

    def get(self, provider_name, credentials_env) -> Provider:
        cache_key = (provider_name, credentials_env)

        if cache_key not in self.cache:
            self.cache[cache_key] = self.providers[provider_name](credentials_env)

        return self.cache[cache_key]
