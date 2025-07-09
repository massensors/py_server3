# from pydantic import BaseModel
#
#
# class MeasureDataRequest(BaseModel):
#     deviceId: str
#     speed: str
#     rate: str
#     total: str
#     currentTime: str
#
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "deviceId": "145267893",
#                 "speed": "1.23",
#                 "rate": "45.67",
#                 "total": "1234.56",
#                 "currentTime": "2024-01-01 12:34:56"
#             }
#         }