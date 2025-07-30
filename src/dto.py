from pydantic import BaseModel, Field


class NewSignUpEvent(BaseModel):
    """
    Data Transfer Object for a new sign-up event.
    """

    name: str = Field(..., description="Unique identifier for the user")
    phone: str = Field(..., description="Email address of the user")
    row: int = Field(..., description="Row number in the data source")
    timestamp: str = Field(
        ..., description="Timestamp of the sign-up event in ISO 8601 format"
    )


class SignUpEventResponse(BaseModel):
    """
    Response DTO for a sign-up event.
    """

    row: int = Field(..., description="Row number in the data source")
    contacted_by: str = Field(
        ..., description="Identifier of the user who contacted the new sign-up"
    )
    timestamp: str = Field(
        ..., description="Timestamp of the sign-up event in ISO 8601 format"
    )
