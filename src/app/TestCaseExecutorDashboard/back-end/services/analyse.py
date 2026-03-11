from fastapi import BackgroundTasks, HTTPException, logger
from lib.strategy.strategy_implementor import StrategyImplementor
from datetime import datetime
from threading import Lock
import os
import requests

from services.ws_manager import ws_manager

ollama_port = os.getenv("OLLAMA_URL")
gpu_url = os.getenv("GPU_URL")
print(f"Ollama URL: {ollama_port}")
print(f"GPU URL: {gpu_url}")

analysis_jobs = {}
analysis_jobs_lock = Lock()

def check_service(url: str, name: str):
    try:
        response = requests.get(url, timeout=3)
        print(f"Health check for {name} service at {url} returned status code {response.status_code}")
        if response.status_code < 400:
            return f"{name} service is reachable at {url}"
        if response.status_code >= 400:
            raise HTTPException(
                status_code=503,
                detail=f"{name} service is not healthy at {url}"
            )
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503,
            detail=f"{name} service is not reachable at {url}"
        )
    
def _set_analysis_job(run_name: str, **updates):
    with analysis_jobs_lock:
        current = analysis_jobs.get(run_name, {})
        current.update(updates)
        analysis_jobs[run_name] = current
        return current


def get_analyse_status_service(run_name: str):
    with analysis_jobs_lock:
        state = analysis_jobs.get(run_name)
        if not state:
            return {"run_name": run_name, "status": "IDLE"}
        return {"run_name": run_name, **state}


def start_analyse_service(run_name: str, db, background_tasks: BackgroundTasks):
    try:
        run = db.get_run_by_name(run_name=run_name)
        if not run:
            print(f"Run with name '{run_name}' not found.")
            raise HTTPException(
                status_code=404,
                detail=f"Run with name '{run_name}' not found."
            )
        if run.status != "COMPLETED":
            print(f"Run '{run_name}' is not completed. Current status: {run.status}")
            raise HTTPException(
                status_code=400,
                detail=f"Run '{run_name}' is not completed. Current status: {run.status}"
            )

        with analysis_jobs_lock:
            existing = analysis_jobs.get(run_name)
            if existing and existing.get("status") == "RUNNING":
                return {"run_name": run_name, "status": "running"}

        run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
        total_items = len(run_details) if run_details else 0
        _set_analysis_job(
            run_name,
            status="RUNNING",
            current=0,
            total=total_items,
            analysis_start_ts=datetime.now().isoformat(),
            analysis_end_ts=None,
            analysis_duration_seconds=None,
            last_update=None,
        )

        background_tasks.add_task(run_analyse_background_service, run_name, db)
        return {
            "run_name": run_name,
            "status": "started",
            "total": total_items,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_analyse_background_service(run_name: str, db):
    analysis_start_ts = datetime.now()
    try:
        await ws_manager.send_all({
            "type": "ANALYSIS_STARTED",
            "runName": run_name,
            "analysisStartTs": analysis_start_ts.isoformat(),
        })

        run = db.get_run_by_name(run_name=run_name)
        if not run:
            raise HTTPException(
                status_code=404,
                detail=f"Run with name '{run_name}' not found."
            )
        
        run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
        if not run_details:
            print(f"No run details found for run '{run_name}'.")
            raise HTTPException(
                status_code=404,
                detail=f"No run details found for run '{run_name}'."
            )
        ## step 1        
        # Group all run details by strategy + metric.
        grouped_run_details = {}
        for detail in run_details:  
            strategy_name = db.get_testcase_strategy_name(testcase_name=detail.testcase_name)
            if not strategy_name:
                logger.error(f"Strategy not found for testcase '{detail.testcase_name}' in run '{run.run_name}'.")
                continue
                    
            group_key = strategy_name + ":" + detail.metric_name
            if group_key not in grouped_run_details:
                grouped_run_details[group_key] = []
            grouped_run_details[group_key].append(detail)
        
        total_items = sum(len(group) for group in grouped_run_details.values())
        ## step 2
        _set_analysis_job(run_name, total=total_items)

        strategy = StrategyImplementor()
        completed = 0

        for group in grouped_run_details.keys():
            strategy_name, metric_name = group.split(":")
            strategy.set_metric_strategy(strategy_name=strategy_name, metric_name=metric_name)
            for detail in grouped_run_details[group]:
                if detail.status != "COMPLETED":
                    raise HTTPException(
                        status_code=404,
                        detail=f"Skipping incomplete run detail with ID {detail.detail_id} for run '{run.run_name}'. Current status: {detail.status}"
                    )
                testcase = db.get_testcase_by_name(detail.testcase_name)
                if not testcase:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Testcase '{detail.testcase_name}' not found for run '{run.run_name}'."
                    )
                
                    
                if not testcase.prompt:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Prompt not found for testcase '{detail.testcase_name}' in run '{run.run_name}'."
                    )
                    
                if not testcase.prompt.user_prompt:
                    raise HTTPException(
                        status_code=404,
                        detail=f"User prompt not found for testcase '{detail.testcase_name}' in run '{run.run_name}'."
                    )
                    
                conversation = db.get_conversation_by_id(detail.conversation_id)
                if not conversation:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Conversation with ID '{detail.conversation_id}' not found for run '{run.run_name}'."
                    )

                if not conversation.agent_response:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Agent response not found for conversation ID '{detail.conversation_id}' in run '{run.run_name}'."
                    )
                ## models fetching    
                score, reason = strategy.execute(testcase = testcase, conversation = conversation)
                
                conversation.evaluation_score = score
                conversation.evaluation_reason = reason
                conversation.evaluation_ts = datetime.now().isoformat()   
                db.add_or_update_conversation(conversation=conversation, override=True)
                completed += 1
                progress_payload = {
                    "type": "ANALYSIS_PROGRESS",
                    "runName": run_name,
                    "current": completed,
                    "total": total_items,
                    "testcaseName": detail.testcase_name,
                    "metricName": detail.metric_name,
                    "strategyName": strategy_name,
                    "detailId": detail.detail_id,
                    "score": float(score) if score is not None else None,
                }
                _set_analysis_job(
                    run_name,
                    current=completed,
                    last_update=progress_payload,
                )
                await ws_manager.send_all(progress_payload)

        analysis_end_ts = datetime.now()
        duration_seconds = int((analysis_end_ts - analysis_start_ts).total_seconds())
        _set_analysis_job(
            run_name,
            status="COMPLETED",
            analysis_start_ts=analysis_start_ts.isoformat(),
            analysis_end_ts=analysis_end_ts.isoformat(),
            analysis_duration_seconds=duration_seconds,
        )
        await ws_manager.send_all({
            "type": "ANALYSIS_FINISHED",
            "runName": run_name,
            "analysisStartTs": analysis_start_ts.isoformat(),
            "analysisEndTs": analysis_end_ts.isoformat(),
            "analysisDurationSeconds": duration_seconds,
        })
    except Exception as e:
        _set_analysis_job(
            run_name,
            status="FAILED",
            analysis_end_ts=datetime.now().isoformat(),
            error=str(e),
        )
        await ws_manager.send_all({
            "type": "ANALYSIS_FAILED",
            "runName": run_name,
            "error": str(e),
        })
