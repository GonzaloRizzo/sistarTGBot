from typing import Union

from . import ItauProvider, SistarbancProvider

Provider = Union[
    ItauProvider,
    SistarbancProvider,
]

# TODO: Implement some kind of decorator that registers providers when they are loaded
provider_registry: dict[str, type[Provider]] = {
    "itau": ItauProvider,
    "sistarbanc": SistarbancProvider,
}
