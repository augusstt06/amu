from pydantic import BaseModel

class Restaurant(BaseModel):
    id: str
    name: str
    category: str
    address: str
    road_address: str
    phone: str
    place_url: str
    map_x: float
    map_y: float
    district: str