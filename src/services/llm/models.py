from langchain_core.pydantic_v1 import BaseModel, Field


class Domains(BaseModel):
    main: list = Field(description="Main Domain(s) (e.g., Manufacturing) — the company's primary field(s) of expertise.")
    sub: list = Field(description="Sub Domain(s)(e.g., Electronics) — a narrower focus within the main domain(s).")
    adj: list = Field(description="Adjacent Domain(s) — areas closely related to the company's field(s) of expertise.")