import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # Fixes the issue of : multiple instances of the OpenMP runtime being initialized 
import jwt
import json
import base64
import logging
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.request import urlopen
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from fastapi import FastAPI, UploadFile, HTTPException, Header, Depends, File
from extract_usin_llm import (
    # llama_create_json_from_text,
    analyze_image_and_append_recommendation_llm
)

from extract import extract_text_from_image, restructure_extracted_text_to_json

logger = logging.getLogger(__name__)

load_dotenv()
tenant_id = os.getenv("AUTH_AZURE_TENANT_ID")
client_id = os.getenv("AUTH_AZURE_CLIENT_ID")
secret = os.getenv("AUTH_AZURE_SECRET")
jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys?appid={client_id}"
issuer_url = f"https://sts.windows.net/{tenant_id}/"
audience = f"api://{client_id}"
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Business Card Text Extraction API",
    docs_url="/api/business_card_text_extraction/docs",
    redoc_url="/api/business_card_text_extraction/redoc",
    openapi_url="/api/business_card_text_extraction/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # FIXME: Update this line to allow only specific origins in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScoresData(BaseModel):
    scores: dict

def get_jwks():
    try:
        jwks = json.loads(urlopen(jwks_url).read())
        return jwks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch JWKS: {str(e)}")

def find_rsa_key(jwks, unverified_header):
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    raise HTTPException(status_code=400, detail="Public key not found in JWKS")

def ensure_bytes(key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    return key

def decode_value(val):
    decoded = base64.urlsafe_b64decode(ensure_bytes(val) + b'==')
    return int.from_bytes(decoded, 'big')

def rsa_pem_from_jwk(jwk):
    try:
        return RSAPublicNumbers(
            n=decode_value(jwk['n']),
            e=decode_value(jwk['e'])
        ).public_key(default_backend()).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting JWK to PEM: {str(e)}")

def verify_token(authorization: str = Header(...)):
    token = authorization.split("Bearer ")[-1]
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = find_rsa_key(jwks, unverified_header)
        public_key = rsa_pem_from_jwk(rsa_key)

        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer_url,
            options={"verify_signature": True} 
        )
        return decoded_token

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        print(f"Invalid Token Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Token validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token validation failed: {str(e)}")
    
@app.get("/")
async def read_root():
    return {"message": "/api/business_card_text_extraction - Root '/'"}

@app.get("/api/business_card_text_extraction")
async def read_root():
    return {"message": "Welcome to the Business Card Text Extraction API"}

@app.get("/api/business_card_text_extraction/whoami")
async def whoami(
    decoded_token: dict = Depends(verify_token)
):
    try:
        decoded_token = verify_token()
        return {"status": "ok", "username": decoded_token.get("name")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.get("/api/business_card_text_extraction/extract_text")
async def extract_text(
    image: UploadFile = File(...),
    # decoded_token: dict = Depends(verify_token)       # disabled since this assignment does not require authentication
):
    """Extract text from an image using OCR and restructure it to JSONusing NER."""
    # user_name = decoded_token.get("name")
    if image.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image file.")
    try:
        image_data = await image.read()
        extracted_text = extract_text_from_image(image_data)
        print("Text was extracted", type(extracted_text))
        restructured_text_01 = restructure_extracted_text_to_json(extracted_text)
        # restructured_text_02 = llama_create_json_from_text(extracted_text)   # Can try if you want to use LLAMA model for text extraction instead of using regex and spacy. 
        logger.info(f"Extracted text.") # for user: {user_name}")
        return JSONResponse(status_code=200, content={"message": "Text extracted successfully.", "extracted text": extracted_text, "final data 01": restructured_text_01}) #"final data 02": restructured_text_02})
    except Exception as e:
        logger.error(f"Failed to extract text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")
    
@app.get("/api/business_card_text_extraction/extract_text_using_gpt")
async def extract_text_using_gpt(
    image: UploadFile = File(...),
    # decoded_token: dict = Depends(verify_token)       # disabled since this assignment does not require authentication
):
    """Extract text from an image using GPT-4 Vision model."""
    # user_name = decoded_token.get("name")
    if image.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image file.")
    try:
        image_data = await image.read()
        restructured_text_01 = analyze_image_and_append_recommendation_llm(image_data, openai_api_key)
        logger.info(f"Extracted text.") # for user: {user_name}")
        return JSONResponse(status_code=200, content={"message": "Text extracted successfully.", "final data 01": restructured_text_01}) #"final data 02": restructured_text_02})
    except Exception as e:
        logger.error(f"Failed to extract text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, debug=True)