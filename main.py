from fastapi import FastAPI, Body, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import Response

from src.config.creds import MONGODB_URL, ADMIN_USERNAME, SCRAPER_PSWD_HASH

import motor.motor_asyncio
from models import UserModel, UpdateUserModel, UserLoginModel, SbirRequest, SamRequest, DomainsRequest
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.utils.utlils import hash
from typing import Annotated
from werkzeug.utils import secure_filename

from src.services.rag.retriever import Retriever
from src.services.rag.loader import Loader
from src.services.scrapers.sbir import SbirScraper
from src.services.scrapers.samgov import SamScraper
from src.services.llm.llm import generate_rating, get_domains
from src.config.config import COMPANY_DATA_QUERY
from datetime import datetime
import json


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


#MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.rfp_scraper
users_collection = db.get_collection("users")


@app.get("/")
async def root():
    return {"message": "RFP Scraper API"}


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    hashed_password = hash(form_data.password)
    if not hashed_password == SCRAPER_PSWD_HASH and not form_data.username == ADMIN_USERNAME:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"message": "Logged in successfully"}


from fastapi import HTTPException, status

@app.post("/login", response_description="User Login")
async def login(user_data: UserLoginModel):
    # Find the user in the database by email
    user = await users_collection.find_one({"email": user_data.email})

    if not user:
        # User doesn't exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with the provided email does not exist",
        )

    # Verify the password
    if not user["password"] == user_data.password:
        # Incorrect password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    # User exists and password is correct
    return {"message": "Login successful", "id": str(user["_id"]), "name": user["name"]}


@app.post("/signup", response_description="Add new user", response_model=None, response_model_by_alias=False)
async def create_user(user: UserModel = Body(...)):
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {user.email} already exists",
        )

    try:
        new_user = await users_collection.insert_one(user.model_dump(by_alias=True))
    except DuplicateKeyError as e:
        # Handle the case where the _id is not unique
        if 'duplicate key error' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {user.id} already exists",
            )
        # Re-raise any other DuplicateKeyError
        raise

    return {"message": f"User created successfully", "id": str(new_user.inserted_id), "name": user.name}



@app.put(
    "/users/{id}",
    response_description="Update existing user",
    response_model=None,
    response_model_by_alias=False
)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    user = {k: v for k, v in user.model_dump(by_alias=True).items() if v is not None}
    if len(user) >= 1:
        update_result = await users_collection.find_one_and_update({"_id": ObjectId(id)}, {"$set": user}, return_document=ReturnDocument.AFTER)
        if update_result is not None:
            return {"message": f"User {id} has been updated successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"User {id} not found")

    raise HTTPException(status_code=404, detail=f"User {id} not found")


@app.delete(
    "/users/{id}",
    response_description="Delete existing user",
)
async def delete_user(id: str):
    delete_user = await users_collection.delete_one({"_id": ObjectId(id)})
    if delete_user.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    raise HTTPException(status_code=404, detail=f"User {id} not found")


@app.post("/upload_file")
async def upload_file(user_id: str = Form(...) , file: UploadFile = File(...)):
    
    #Sanity check
    user_id = secure_filename(user_id)

    if user_id == '' or user_id is None:
        raise HTTPException(status_code=400, detail="Corrupted user id")

    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=402, detail="File must be a pdf")
        content = await file.read()
    else:
        raise HTTPException(status_code=400, detail="No file provided")
 

    with open(f"temp.pdf", "wb") as f:
        f.write(content)
        
    loader = Loader()
    docs = loader.load_document("temp.pdf")
    retriever = Retriever(user_id)
    
    retriever.add_documents(docs)
        
    return {"status": "Document uploaded successfully"}


@app.get("/get-sbir")
async def get_sbir(request: SbirRequest):

    #sanity check
    user_id = secure_filename(request.user_id)

    if request.user_id == '' or request.user_id is None:
        raise HTTPException(status_code=400, detail="Corrupted user id")
    
    if request.date_from and request.date_to:
        date_from = datetime.strptime(str(request.date_from), '%Y-%m-%d %H:%M:%S')
        date_to = datetime.strptime(str(request.date_to), '%Y-%m-%d %H:%M:%S')
    else:
        raise HTTPException(status_code=400, detail="Error in date format, please ensure date is in the format YYYY-MM-DD")

    scraper = SbirScraper(request.user_id)
    return scraper.scrape(user_id=user_id, date_from=date_from, date_to=date_to, rate=request.rate)


@app.get("/get-sam")
async def get_sam(request: SamRequest):
    
    #sanity check
    user_id = secure_filename(request.user_id)

    if user_id == '' or user_id is None:
        raise HTTPException(status_code=400, detail="Corrupted user id")

    scraper = SamScraper(user_id)
    return scraper.scrape(user_id, request.rate)



@app.post("/get-rating")
async def get_rating(user_id:str, title:str, proposal_description:str):
    
    retriever = Retriever(user_id)
    
    docs = retriever.get_query_docs(COMPANY_DATA_QUERY, k=3)
    
    try:
        res, e = generate_rating(title, proposal_description, company_description=docs)
        return {"rating": res}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    


@app.get("/get-domain")
async def get_domain(request: DomainsRequest):
    
    if request.platform == "sbir.gov":
         scraper = SbirScraper(request.user_id)
    elif request.platform == "sam.gov":
        scraper = SamScraper(request.user_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    try:
        domains = get_domains(company_data=scraper.docs)
        
        results = {}
        
        for domain in domains.keys():
            temp_res = {}
            for domain_name in domains[domain]:
                print(f"Scraping {domain_name}...")
                temp_res[domain_name] = scraper.scrape(user_id=request.user_id, keywords=domain_name, rate=True)
            results[domain] = temp_res
        return results
    
    
    # with open("temp.json", "r") as f:
    #     results = json.load(f)
        
    

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    