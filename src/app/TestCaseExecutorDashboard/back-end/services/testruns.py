import os
import sys
from typing import Optional,List
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemas import TestRunFullResponse, TestRunSummaryResponse, TestRunDetailsResponse,TestRunResponse


def get_test_run_service(db, run_name: str, metric: Optional[str] = None, status: Optional[str] = None):
    try:
        print(metric, status)

        run = db.get_run_by_name(run_name)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        domain_name = None
        if getattr(run, "target_id", None):
            target = db.get_target_by_id(run.target_id)
            if target:
                domain_name = getattr(target, "target_domain", None)

        summary = TestRunSummaryResponse(
            run_id=run.run_id,
            run_name=run.run_name,
            target=run.target,
            domain=domain_name,
            status=run.status,
            start_ts=run.start_ts,
            end_ts=run.end_ts
        )

        details = db.get_all_run_details_by_run_name(run_name)

        details_response = []
        if metric:
            details = [d for d in details if d.metric_name == metric]

        if status:
            details = [d for d in details if d.status == status]

        for d in details:
            score = None
            if d.conversation_id:
                conv = db.get_conversation_by_id(d.conversation_id)
                if conv and conv.evaluation_score is not None:
                    score = float(conv.evaluation_score)

            details_response.append(
                TestRunDetailsResponse(
                    run_name=d.run_name,
                    testcase_name=d.testcase_name,
                    metric_name=d.metric_name,
                    plan_name=d.plan_name,
                    conversation_id=d.conversation_id,
                    status=d.status,
                    detail_id=d.detail_id,
                    score=score
                )
            )

        return TestRunFullResponse(
            summary=summary,
            details=details_response
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))