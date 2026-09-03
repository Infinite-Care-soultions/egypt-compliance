from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str | None = None


class LoginCredentials(BaseModel):
    client_id: str
    client_secret: str
    scope: str = Field(default="InvoicingAPI")
    on_behalf_of: str | None = None
