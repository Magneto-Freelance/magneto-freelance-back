from datetime import datetime, timedelta, timezone
from enum import Enum
import os
from typing import List, Optional, Union
import motor.motor_asyncio
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

# creación de base de datos
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
SECRET_KEY = os.environ.get("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.get_database("Magneto-Freelance")
postulant_collection = db.get_collection("Postulant")
company_collection = db.get_collection("Company")
offer_collection = db.get_collection("Offer")
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


class LoginType(str, Enum):
    postulant = "postulant"
    company = "company"


class LoginData(BaseModel):
    type: LoginType
    email: str
    password: str


class Offer(BaseModel):
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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI(title="Magneto-freelance-back")

# Esta middleware es para que el front se pueda conectar al back, es para darle "permiso"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def authenticate(
    type: LoginType, email: str, password: str
) -> Optional[Union[Postulant, Company]]:
    user = None
    if type == "postulant":
        user = await postulant_collection.find_one({"email": email})
    if type == "company":
        user = await company_collection.find_one({"email": email})

    if not user or not verify_password(password, user["password"]):
        return None

    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# definicion de la ruta para hacer el create
@app.post(
    "/postulants",
    response_description="Add new Postulant",
    response_model=Postulant,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_postulant(postulant: Postulant = Body(...)):
    postulant.password = get_password_hash(postulant.password)
    new_postulant = await postulant_collection.insert_one(
        postulant.model_dump(by_alias=True, exclude=["id"])
    )
    created_postulant = await postulant_collection.find_one(
        {"_id": new_postulant.inserted_id}
    )
    return created_postulant


# definicion de la ruta get para traer los postulantes (read)
@app.get(
    "/postulants",
    response_description="Get postulants",
    response_model=PostulantCollection,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_postulant():
    return PostulantCollection(
        postulants=await postulant_collection.find().to_list(1000)
    )


@app.post(
    "/companies",
    response_description="Add new Company",
    response_model=Company,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_company(company: Company = Body(...)):
    company.password = get_password_hash(company.password)
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
    "/offer",
    response_description="Add new Offer",
    response_model=Offer,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_offer(offer: Offer = Body(...)):
    new_offer = await offer_collection.insert_one(
        offer.model_dump(by_alias=True, exclude=["id"])
    )
    created_offer = await offer_collection.find_one({"_id": new_offer.inserted_id})
    return created_offer


@app.get(
    "/offer",
    response_description="Get offer",
    response_model=List[Offer],
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_offer(search: Optional[str] = None):
    if search:
        return await offer_collection.find({"title": {"$regex": search, "$options": "i"}}).to_list(1000)
    return await offer_collection.find().to_list(1000)


async def login_for_access_token(form_data: LoginData):
    user = await authenticate(form_data.type, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": {"email": form_data.email, "type": form_data.type}}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login(form_data: LoginData):
    return await login_for_access_token(form_data)