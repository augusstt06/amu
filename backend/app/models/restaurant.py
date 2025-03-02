from pydantic import BaseModel

class Restaurant(BaseModel):
    id: str
    name: str
    category: str
    description: str
    phone: str
    address: str
    map_x: float
    map_y: float