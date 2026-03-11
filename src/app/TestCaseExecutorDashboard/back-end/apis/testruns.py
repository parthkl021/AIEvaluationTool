import os
import sys
from typing import Optional, List,Literal
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemas import TestRunFullResponse,TestRunResponse,NewTestRun, FilterResponse
from services.testruns import get_test_run_service,get_all_test_runs_service,get_metrics_by_plan_service
from dependencies import get_db

router = APIRouter()

@router.get(
    "/test-runs/{run_name}",
    response_model=TestRunFullResponse
)
def get_test_run(
    run_name: str,
    metric: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db = Depends(get_db)
):
    try:
        return get_test_run_service(db, run_name, metric, status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/get_all_test_runs",
    response_model=List[TestRunResponse],
)
def get_all_test_runs(
    domain: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Literal["end_ts", "start_ts"] = Query("end_ts"),
    order: Literal["asc", "desc"] = Query("desc"),
    db=Depends(get_db),
):
    try:
        return get_all_test_runs_service(
            db=db,
            domain=domain,
            target=target,
            status=status,
            sort_by=sort_by,
            order=order,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/get_metrics_by_plan/{plan_name}", response_model=list[FilterResponse])
def get_metrics_by_plan(plan_name: str, db=Depends(get_db)):
    try:
        return get_metrics_by_plan_service(db=db, plan_name=plan_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))        
    
    