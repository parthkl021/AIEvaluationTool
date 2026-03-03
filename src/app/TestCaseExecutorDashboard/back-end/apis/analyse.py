from fastapi import APIRouter, HTTPException,Depends

from services.analyse import get_analyse_service

router = APIRouter()
from dependencies import get_db

@router.get("/analyse/{RunName}")
def get_analyse(RunName: str,db=Depends(get_db)):
    try:
        return get_analyse_service(RunName,db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
