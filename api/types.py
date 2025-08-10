from pydantic import BaseModel, HttpUrl


class CarfaxOut(BaseModel):
    status: str
    file: HttpUrl

class CheckBalanceOut(BaseModel):
    balance: float