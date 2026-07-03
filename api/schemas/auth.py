from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(
        description="Email address of the user to register.",
        examples=["user@example.com"],
    )


class RegisterResponse(BaseModel):
    email: EmailStr = Field(
        description="Email address of the registered user.",
        examples=["user@example.com"],
    )
    api_key: str = Field(
        description="Generated API key. Store this safely — it will not be shown again.",
        examples=["dGhpcyBpcyBhIHNhbXBsZSBrZXk"],
    )
    credits: int = Field(
        description="Number of credits assigned to the new account.",
        examples=[10],
    )
    message: str = Field(
        description="Informational message.",
        examples=["Store this key safely — it will not be shown again."],
    )
