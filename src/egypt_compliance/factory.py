from abc import ABC, abstractmethod

from egypt_compliance.client import ETAClient
from egypt_compliance.config import Environment, PREPROD, PROD


class ClientCreator(ABC):
    """Factory Method: subclasses decide which ETA client to instantiate."""

    @abstractmethod
    def create_client(self) -> ETAClient:
        raise NotImplementedError


class PreprodClientCreator(ClientCreator):
    def create_client(self) -> ETAClient:
        return ETAClient(config=PREPROD)


class ProdClientCreator(ClientCreator):
    def create_client(self) -> ETAClient:
        return ETAClient(config=PROD)


class ETAClientFactory:
    """Public facade over environment-specific creators."""

    _creators: dict[str, type[ClientCreator]] = {
        Environment.PREPROD.value: PreprodClientCreator,
        Environment.PROD.value: ProdClientCreator,
    }

    @classmethod
    def create(cls, environment: str | Environment) -> ETAClient:
        key = environment.value if isinstance(environment, Environment) else str(environment).lower()
        creator_cls = cls._creators.get(key)
        if creator_cls is None:
            valid = ", ".join(sorted(cls._creators))
            raise ValueError(f"Unknown environment {environment!r}. Expected one of: {valid}")
        return creator_cls().create_client()
