from fastapi import FastAPI, Body, HTTPException, status
import motor.motor_asyncio
import os
from pydantic import BaseModel
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from typing import Optional, List


# creación de base de datos
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.get_database("Magneto-Freelance")
postulant_collection = db.get_collection("Postulant")
PyObjectId = Annotated[str, BeforeValidator(str)]


# clase usuarios
class Postulant(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    lastName: str = Field(...)
    cellphoneNumber: str = Field(...)
    email: str = Field(...)
    occupation: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class PostulantCollection(BaseModel):
    postulants: List[Postulant]

# clase empresas
class Company(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    description: str = Field(...)
    ubication: str = Field(...)
    type: str = Field(...)
    id: str = Field(...)
    cellphoneNumber: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


# = Field(...) es para que fastapi pueda validar los datos enviados a la base de datos.
# modelConfig es para que Mongo sepa de qué manera almacenar los datos.

# crear la ruta fastApi
app = FastAPI(title="Magneto-freelance-back")

#definicion de la ruta para hacer el create
@app.post(
    "/postulants/",
    response_description="Add new Postulant",
    response_model=Postulant,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_postulant(postulant: Postulant = Body(...)):
    new_postulant = await postulant_collection.insert_one(
        postulant.model_dump(by_alias=True, exclude=["id"])
    )
    created_postulant = await postulant_collection.find_one(
        {"_id": new_postulant.inserted_id}
    )
    return created_postulant

#definicion de la ruta get para traer los postulantes (read)
@app.get(
    "/postulants",
    response_description="Get postulants",
    response_model=PostulantCollection,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_postulant():
    return PostulantCollection(postulants=await postulant_collection.find().to_list(1000))
