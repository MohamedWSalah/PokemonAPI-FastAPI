from array import array
from ctypes import Array
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request,status
from fastapi.responses import JSONResponse
from pydantic import BaseModel,validator
from hashing import Hash
from jwt import create_access_token, verify_token,getUserName
from oauth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson.objectid import ObjectId

app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pymongo import MongoClient
#I left the username and password plain on purpose :)
mongodb_uri = 'mongodb+srv://moon:moon@cluster0.gejee.mongodb.net/Pokemon?retryWrites=true&w=majority'
port = 8000
client = MongoClient(mongodb_uri, port)
db = client["User"]


class User(BaseModel):
    username: str
    password: str
    pokemons: Optional[List[str]] = None
class Login(BaseModel):
	username: str
	password: str



credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.get("/")
def read_root(current_user:User = Depends(get_current_user)):
	return {"data":"Fail"}

@app.post('/register')
def create_user(request:User):
    user = db["users"].find_one({"username":request.username})
    print(user)
    if user:
        return{"status_code":status.HTTP_406_NOT_ACCEPTABLE,"response":"Username already exists"}
    else:
        hashed_pass = Hash.bcrypt(request.password)
        user_object = dict(request)
        user_object["password"] = hashed_pass
        user_id = db["users"].insert_one(user_object)
        # print(user)
        return {"status_code":status.HTTP_200_OK,"response":"account created successfully"}

@app.post('/login')
def login(request:OAuth2PasswordRequestForm = Depends()):
	user = db["users"].find_one({"username":request.username})
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f'No user found with this {request.username} username')
	if not Hash.verify(user["password"],request.password):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = 'Wrong Username or password')
	access_token = create_access_token(data={"user": user["username"] })
	return {"access_token": access_token, "token_type": "bearer"}

@app.post('/addPokemon')
async def addPokemon(token: str, pokemonName: str):
    
    verify_token(token,credentials_exception)
    payload = getUserName(token)
    currentUser  = payload['user'];
    addPoke =  db["users"].find_one({"username":currentUser})
    if addPoke:
        pokeArr = addPoke['pokemons']
        if pokemonName in pokeArr:
            return{"status_code":status.HTTP_406_NOT_ACCEPTABLE,"response":"Pokemon already exists"}
        pokeArr.append(pokemonName)
        updateUser = db["users"].update_one({"_id":addPoke["_id"]},{"$set":{"pokemons":pokeArr}})
    if updateUser:
        return {"status_code":status.HTTP_200_OK,"response":"Pokemon added successfully"}
    
    return {"data":"done"}
    