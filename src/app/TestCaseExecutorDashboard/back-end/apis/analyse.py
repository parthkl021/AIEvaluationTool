from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from services.analyse import get_analyse_status_service, start_analyse_service

router = APIRouter()
from configuration.database import get_db

@router.get("/analyse/{RunName}")
def get_analyse(RunName: str, background_tasks: BackgroundTasks, db=Depends(get_db), mode: str = Query("rerun_all")):
    print(f"[API] Received analysis request for run '{RunName}' with mode '{mode}'")
    try:
        return start_analyse_service(RunName, db=db, background_tasks=background_tasks, mode=mode)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyse/{RunName}/status")
def get_analyse_status(RunName: str):
    try:
        return get_analyse_status_service(RunName)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
