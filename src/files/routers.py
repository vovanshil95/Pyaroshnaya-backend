import os
import shutil

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

router = APIRouter(prefix='/files',
                   tags=['files'])

@router.post('')
async def post_file(file: UploadFile = File(...)):
    with open(f"../storage/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

@router.get('')
async def get_file(image: str):
    file_name = list(filter(lambda file_name: image == file_name[:-4], os.listdir('../storage')))[0]
    return FileResponse(f'../storage/{file_name}')

