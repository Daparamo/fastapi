from fastapi  import Depends, FastAPI, Body, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security.http import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Coroutine, Optional, List
from jwt_manager import create_token, validate_token
from fastapi.security import HTTPBearer
from config.database import Session, engine, Base
from models.movie import Movie as MovieModel
from fastapi.encoders import jsonable_encoder
app = FastAPI()
app.title = "First Api on FastApi"
app.version = "1.0.0"

Base.metadata.create_all(bind=engine)

class JWTBearer(HTTPBearer):
  async def __call__(self, request: Request): 
    auth = await super().__call__(request)
    data = validate_token(auth.credentials)
    if data['email'] != "daparamo":
      raise HTTPException(status_code=403, detail="Credenciales invalidas") 


class User(BaseModel):
  email:str
  password:str

class Movie(BaseModel):
  id:Optional[int] = None
  title: str = Field(max_length=50)
  overview: str = Field(min_length=15,max_length=500)
  year: int = Field(le=2024, ge=1800)
  rating: float = Field(le=10, gt=0.0)
  category: str = Field(min_length=5,max_length=500)

  class Config:
     json_schema_extra = {     
      "example": {    
        "id": 0,
        "title": "The Shawshank Redemption",
        "overview": "Two imprisoned men bond over a number of years",
        "year": 1994,
        "rating": 9.2,
        "category": "Drama"
      }
    }

movies = [
  {
    "id": 1,
    "title": "Avatar",
    "overview": "En un exuberante planeta llamado Pandora viven los Na'vi, seres que...",
    "year": "2009",
    "rating": 7.8,
    "category": "Acción"
  },
  {
    "id": 2,
    "title": "Avatar 2",
    "overview": "En un exuberante planeta llamado Pandora viven los Na'vi, seres que...",
    "year": "2023",
    "rating": 7.8,
    "category": "Acción"
  }
]

@app.post("/login",tags=["Auth"])
def login(user:User):
  if user.email == "daparamo" and user.password=="1234":
    token: str = create_token(user.model_dump())
    return JSONResponse(content=token, status_code=200)
  else:
    return JSONResponse(content={"message":"Invalid credentials"}, status_code=401)

@app.get("/movies",tags=["Movies"], response_model=List[Movie], status_code=200, dependencies=[Depends(JWTBearer())])
def get_movies() -> List[Movie]:
  db = Session()
  result = db.query(MovieModel).all()
  return JSONResponse(content=jsonable_encoder(result))

@app.get("/movies/{id}", tags=["Movies"], response_model=List[Movie])
def get_movie(id: int = Path(ge=1,le=2000)) ->List[Movie]:
  db = Session()
  result = db.query(MovieModel).filter(MovieModel.id == id).first()
  if not result:
    return JSONResponse(status_code=404, content=[])    
  else:
    return JSONResponse(status_code=200,content=jsonable_encoder(result))
  

@app.get("/movies/", tags=["Movies"], response_model=List[Movie], status_code=200)
def get_movies_by_category(category:str = '')->List[Movie]:
  db = Session()
  if category=='':
    result = db.query(MovieModel).all()
    return JSONResponse(status_code=200, content=jsonable_encoder(result))
  else:
    result = db.query(MovieModel).filter(MovieModel.category==category).all()
    return JSONResponse(content=jsonable_encoder(result))

@app.post("/movies", tags=["Movies"], response_model=dict, status_code=201)
def create_movie(movie:Movie)->dict:
  db = Session()
  new_movie = MovieModel(**movie.model_dump())  
  db.add(new_movie)
  db.commit()
  return JSONResponse(status_code=200, content={"msg":"Pelicula creada con exito"})

@app.put("/movies/{id}", tags=["Movies"], response_model=List[Movie], status_code=200)
def update_movie(id:int, movie:Movie) ->List[Movie]:
  db = Session()
  result = db.query(MovieModel).filter(MovieModel.id == id).first()
  if not result: 
    return JSONResponse(status_code=404, content={"msg":"No Encontrado"})
  else:
    result.title = movie.title
    result.overview = movie.overview
    result.year = movie.year
    result.rating = movie.rating
    result.category = movie.category
    db.commit()
    return JSONResponse(status_code=200, content=jsonable_encoder(result))
    
@app.delete("/movies/{id}",tags=["Movies"],response_model=List[Movie],status_code=200)
def delete_movie(id: int)->List[Movie]:
  db = Session()
  result = db.query(MovieModel).filter(MovieModel.id == id).delete()  
  db.commit()
  return JSONResponse(status_code=200, content={"msg":"Plicula Eliminada"})