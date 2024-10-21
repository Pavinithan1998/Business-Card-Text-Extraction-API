
# Business Card Text Extraction API

## Overview

The **Business Card Text Extraction API** provides an interface for extracting structured information from business card images. It supports two primary methods for extracting data:
1. **OCR and NER-based extraction** using PaddleOCR, spaCy, and regular expressions.
2. **GPT-based extraction** using the OpenAI GPT-4 Vision model to directly analyze the image and extract structured information in JSON format.

This API is integrated with Azure AD for authentication using JWT tokens.

## Features

- **Extract Data from Business Cards**: Extracts key information such as email, phone numbers, agent name, company name, and web presence (social media, website).
- **Azure AD JWT Authentication**: Ensures secure access using Azure Active Directory and JWT token validation. 
- **OCR-based Extraction**: Uses PaddleOCR for text extraction and spaCy for entity recognition.
- **GPT-4 Vision-based Extraction**: Uses OpenAI's GPT-4 Vision model to directly analyze the image and return structured information.

## Installation

### Prerequisites

- Python 3.8 or above
- Access to OpenAI GPT-4 API
- Azure AD credentials (Tenant ID, Client ID, Secret)

### Clone the Repository

```bash
git clone https://github.com/your-username/business-card-extraction.git
cd business-card-extraction
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set up Environment Variables

Create a `.env` file in the root of the project and add the following variables:

```bash
# .env file

AUTH_AZURE_TENANT_ID=<your_azure_tenant_id>
AUTH_AZURE_CLIENT_ID=<your_azure_client_id>
AUTH_AZURE_SECRET=<your_azure_client_secret>
OPENAI_API_KEY=<your_openai_api_key>
```

### Install spaCy Model

Since the API uses spaCy for Named Entity Recognition (NER), you need to download the `en_core_web_sm` model:

```bash
python -m spacy download en_core_web_sm
```

### Running the API

You can run the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

This will start the server at `http://127.0.0.1:8000/`. You can access the API docs at:

```
http://127.0.0.1:8000/api/business_card_text_extraction/docs
```

### Endpoints

#### 1. Root Endpoint

- **URL**: `/`
- **Method**: `GET`
- **Description**: Basic root endpoint.

#### 2. Business Card Text Extraction (OCR + NER)

- **URL**: `/api/business_card_text_extraction/extract_text`
- **Method**: `GET`
- **Description**: Upload an image of a business card. Extract text using OCR and structure it in JSON format using NER.
- **Request**:
    - `image`: The business card image file (JPEG, PNG, etc.).
- **Response**:
    - Structured JSON output with email, phone numbers, agent name, company name, address, and web presence (website, Facebook, Instagram, Twitter).

#### 3. Business Card Text Extraction (GPT-4 Vision)

- **URL**: `/api/business_card_text_extraction/extract_text_using_gpt`
- **Method**: `GET`
- **Description**: Upload an image of a business card. Extract structured information directly from the image using GPT-4 Vision.
- **Request**:
    - `image`: The business card image file (JPEG, PNG, etc.).
- **Response**:
    - Structured JSON output with email, phone numbers, agent name, company name, and web presence (website, Facebook, Instagram, Twitter).

#### 4. Who Am I (JWT Protected)

- **URL**: `/api/business_card_text_extraction/whoami`
- **Method**: `GET`
- **Description**: Returns information about the authenticated user based on the JWT token.

## Security

This API uses JWT token validation to authenticate requests. Ensure that Azure AD credentials and the OpenAI API key are securely stored in environment variables.

## Environment Variables

Ensure the following environment variables are set in your `.env` file:

- `AUTH_AZURE_TENANT_ID`: Your Azure AD tenant ID.
- `AUTH_AZURE_CLIENT_ID`: Your Azure AD client ID.
- `AUTH_AZURE_SECRET`: Your Azure AD client secret.
- `OPENAI_API_KEY`: Your OpenAI API key for accessing GPT-4.


