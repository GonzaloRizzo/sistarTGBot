from typing import Annotated, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator

from .providers.itau import ItauAccountTransaction, ItauCardAuthorization
from .providers.sistarbanc import SistarbancAuthorization, SistarbancMovement


class BaseAccount(BaseModel):
    type: str
    name: str
    credentials_env: str


class SistarbancMovementsAccount(BaseAccount):
    provider = "sistarbanc"
    transaction_model = SistarbancMovement

    type: Literal["sistarbanc_movements"]
    card_number: Optional[str]


class SistarbancAuthorizationsAccount(BaseAccount):
    provider = "sistarbanc"
    transaction_model = SistarbancAuthorization

    type: Literal["sistarbanc_authorizations"]
    card_number: Optional[str]


class ItauBankAccount(BaseAccount):
    provider = "itau"
    transaction_model = ItauAccountTransaction

    type: Literal["itau_bank_account"]
    id: str


class ItauCardAuthorizationsAccount(BaseAccount):
    provider = "itau"
    transaction_model = ItauCardAuthorization

    type: Literal["itau_card_authorizations"]
    card_number: Optional[str]
    id: str


Account = Annotated[
    Union[
        SistarbancMovementsAccount,
        SistarbancAuthorizationsAccount,
        ItauBankAccount,
        ItauCardAuthorizationsAccount,
    ],
    Field(discriminator="type"),
]


class Config(BaseModel):
    token: str
    target_chat: str
    accounts: list[Account]

    @validator("accounts", pre=True)
    def transform_accounts(cls, value: dict[str, dict]) -> list[dict]:
        return [{"name": k, **v} for k, v in value.items()]

    @classmethod
    def read_config(cls, file_path):
        with open(file_path) as f:
            return cls(**yaml.safe_load(f))
