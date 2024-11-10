from api.services.llama_index_service import index_documents, query_pdf_text, clear_files_directory
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from api.database.database import get_db
from api.models.pdf_model import PDFDocument
from api.utils.pymupdf_extract import extract_text_from_pdf

# Create a new APIRouter instance
router = APIRouter()

@router.get("/")
async def root():
    return {"FASTAPI": "Welcome to the FASTAPI application"}

@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Dynamically set the file location path
        file_location = os.path.join(os.getcwd(), "files", file.filename)

        # Check if the file already exists
        if os.path.exists(file_location):
            raise HTTPException(status_code=400, detail="File already exists")

        # Ensure the files directory exists
        if not os.path.exists(os.path.dirname(file_location)):
            os.makedirs(os.path.dirname(file_location))

        # Save the file
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Extract the text from the PDF file
        extract_text_from_pdf(file.filename)

        # Add the document to the database
        new_document = PDFDocument(file_name=file.filename, upload_date=str(datetime.utcnow()))
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        # Index the documents
        index_documents("files")

        return {"status": "success", "message": "File uploaded and indexed successfully"}

    except HTTPException as he:
        print(he)
        raise he   
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/")
async def query_pdf(query: str):
    try:
        # Query the indexed PDFs
        response = query_pdf_text(query)
        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/clear-document-store")
async def clear_document_store_endpoint():
    return clear_files_directory()

@router.post("/get-all-documents")
async def get_all_documents():
    try:
        documents = []
        for document in os.listdir("files"):
            documents.append(document)
        return {"documents": documents}
    except Exception as e:
        return {"error": str(e)}
