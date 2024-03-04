import os
from typing import List, Optional
import motor.motor_asyncio
from fastapi import Body, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

# creación de base de datos
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.get_database("Magneto-Freelance")
postulant_collection = db.get_collection("Postulant")
company_collection = db.get_collection("Company")
ofert_collection = db.get_collection("Oferts")
PyObjectId = Annotated[str, BeforeValidator(str)]


# clase usuarios
class Postulant(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    username: str = Field(...)
    password: str = Field(...)
    email: str = Field(...)

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
    username: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class Ofert(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(...)
    employer: str = Field(...)
    description: str = Field(...)
    skills: str = Field(...)
    salary: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


# = Field(...) es para que fastapi pueda validar los datos enviados a la base de datos.
# modelConfig es para que Mongo sepa de qué manera almacenar los datos.

# crear la ruta fastApi
app = FastAPI(title="Magneto-freelance-back")

# Esta middleware es para que el front se pueda conectar al back, es para darle "permiso"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#definicion de la ruta para hacer el create
@app.post(
    "/postulants",
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


@app.post(
    "/companies",
    response_description="Add new Company",
    response_model=Company,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_company(company: Company = Body(...)):
    new_company = await company_collection.insert_one(
        company.model_dump(by_alias=True, exclude=["id"])
    )
    created_company = await company_collection.find_one(
        {"_id": new_company.inserted_id}
    )
    return created_company


@app.get(
    "/company",
    response_description="Get companies",
    response_model=List[Company], 
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_company():
    return await company_collection.find().to_list(1000)



@app.post(
    "/oferts",
    response_description="Add new Ofert",
    response_model=Ofert,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_ofert(ofert: Ofert = Body(...)):
    new_ofert = await ofert_collection.insert_one(
        ofert.model_dump(by_alias=True, exclude=["id"])
    )
    created_ofert= await ofert_collection.find_one(
        {"_id": new_ofert.inserted_id}
    )
    return created_ofert


@app.get(
    "/ofert",
    response_description="Get oferts",
    response_model=List[Ofert], 
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_oferts():
    return await ofert_collection.find().to_list(1000)