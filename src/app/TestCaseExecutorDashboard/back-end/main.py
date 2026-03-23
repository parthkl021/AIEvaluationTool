import os
from fastapi import FastAPI, HTTPException, Query, WebSocket, BackgroundTasks,WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from services.ws_manager import ws_manager 
from openpyxl import Workbook, load_workbook
import threading
from typing import Optional, List,Literal
import tempfile
import socket
import psutil
import os
import re
from urllib.parse import urlparse
# import mysql.connector
import json
import uvicorn
import asyncio
# from mysql.connector import Error
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import sys
import randomname
from collections import defaultdict
from schemas import TestRunResponse,TestRunDetailsResponse,FilterResponse,AllFiltersResponse,TestRunSummaryResponse,TestRunFullResponse,RunEvaluationSummaryResponse,EvaluationItemResponse,ConversationResponse,TestCaseResponse,FullConversationResponse, TimelineEvent,NewTestRun,ContinueRunRequest
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import datetime
from datetime import datetime
from lib.orm import DB
from lib.data import Target, Run, RunDetail, Conversation

from lib.orm.tables import TestRuns
from lib.interface_manager import InterfaceManagerClient  # Import the InterfaceManagerClient from the lib directory
from configuration.database import get_db
from configuration.database import db
from configuration.paths import profile_path
from apis.testruns import router as testruns_router
from apis.filters import router as filters_router
from apis.analyse import router as analyse_router
from apis.conversations import router as conversations_router

from utils.port import check_service, ensure_interface_manager_port_running, stop_interface_manager, watch_chrome_and_kill_im, watch_im_process

# db_url = (
#             f"mysql+mysqlconnector://"
#             f"{os.getenv('DB_USER')}:"
#             f"{os.getenv('DB_PASSWORD')}@"
#             f"{os.getenv('DB_HOST')}:"
#             f"{os.getenv('DB_PORT')}/"
#             f"{os.getenv('DB_NAME')}"
#         )


## Configure DB and port connection  (using config.json for flexibility)

config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}


port_config = config.get("port", {})
BACKEND_PORT = int(port_config.get("back-end", 7000))


# Resolve project root (this file → importer → app → src → project_root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))


interface_manager_root=os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
interface_manager_config = os.path.join(
    interface_manager_root,
    "interface_manager",
    "config.json"
)

if not os.path.exists(interface_manager_config):
    raise RuntimeError(
        f"Interface Manager config.json not found at {interface_manager_config}"
    )

back_end_root=os.path.abspath(os.path.join(os.path.dirname(__file__)))
print(f"Back-end root resolved to: {back_end_root}")

template_path = os.path.join(
    back_end_root,
    "templates",
    "Reports.xlsx"
)

wb = load_workbook(template_path)



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(testruns_router)
app.include_router(filters_router)
app.include_router(analyse_router)
app.include_router(conversations_router)


def load_config():
    with open(config_path , "r") as f:
        return json.load(f)

def is_error_response(response):
    error_indicators = [
        "chat not found",
        "[error: max retries exceeded]",
        "[error: connection refused]",
        "no response received"
    ]
    return len(response) == 0 or any(indicator in response[0]['response'].lower() for indicator in error_indicators)

## to check if interface_manager is running ##

# def ensure_interface_manager_running(
#     config_path: str,
#     timeout: float = 1.5
# ):
#     # 1️⃣ Read config.json
#     try:
#         with open(config_path, "r") as f:
#             config = json.load(f)
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to read Interface Manager config: {str(e)}"
#         )

#     # 2️⃣ Extract base_url
#     base_url = config.get("base_url")
#     if not base_url:
#         raise HTTPException(
#             status_code=500,
#             detail="base_url missing in Interface Manager config"
#         )

#     # 3️⃣ Parse host & port
#     parsed = urlparse(base_url)
#     host = parsed.hostname
#     port = parsed.port

#     if not host or not port:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Invalid base_url in Interface Manager config: {base_url}"
#         )

#     # 4️⃣ TCP port check
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.settimeout(timeout)

#     try:
#         result = sock.connect_ex((host, port))
#         if result != 0:
#             raise HTTPException(
#                 status_code=503,
#                 detail=f"Interface Manager is not running at {host}:{port}"
#             )
#     finally:
#         sock.close()

## WebSocket for real-time updates

@app.websocket("/ws/test-run")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
       

async def step(ws_payload, delay=0.1):
    await ws_manager.send_all(ws_payload)
    await asyncio.sleep(delay)


    
# @app.get("/test-runs/{run_name}/summary", response_model=TestRunSummaryResponse)
# def get_test_run_summary(run_name: str):
#     try:
        
#         run = db.get_run_by_name(run_name)
#         if not run:
#             raise HTTPException(status_code=404, detail="Run not found")

#         # If you store target_id on run, use it to fetch target -> domain
#         domain_name = None
#         if getattr(run, "target_id", None):
#             target = db.get_target_by_id(run.target_id)
#             if target:
#                 domain_name = getattr(target, "target_domain", None)

#         return TestRunSummaryResponse(
#             run_id=run.run_id,
#             run_name=run.run_name,
#             target=run.target,
#             domain=domain_name,
#             status=run.status,
#             start_ts=run.start_ts,
#             end_ts=run.end_ts
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))    
    

    
@app.get(
    "/testcases/{testcase_name}",
    response_model=TestCaseResponse
)
def get_conversation(testcase_name: str):
    
    testcase = db.get_testcase_by_name(testcase_name)
    if not testcase:
        raise HTTPException(status_code=404, detail="Testcase not found")
    return TestCaseResponse(
        user_prompt=testcase.prompt.user_prompt,
        system_prompt=testcase.prompt.system_prompt
    )




@app.post("/start-run")
def start_run(data: NewTestRun, background_tasks: BackgroundTasks):
    ensure_interface_manager_port_running(interface_manager_config)  
    if data.testPlan:
        ### Initialising the form variables
        print("Starting new test run...")
        target = data.target
        target = re.sub(r"\s*\(.*?\)", "", target)

        
        plan_name = data.testPlan
        test_case_id = data.testCaseId
        metric_name = data.metric 
        domain_name = data.domain if data.domain else None
        lang_name = data.language if data.language else None
        provided_run_name = data.runName.strip() if data.runName else None
        if test_case_id and metric_name:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'testCaseId' or 'metric', not both."
            )
        try:
            max_test_cases = int(data.maxTestCases)
            print(max_test_cases)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="maxTestCases must be a valid number"
            )
        

        if provided_run_name:
            run_name = provided_run_name
        else:
            run_name = randomname.generate('v/*','adj/*','n/*','ip/*').replace("/", "-")
        start_time = datetime.now().isoformat()
        run = Run(target=target, run_name=run_name, start_ts=start_time)
        run_id = db.add_or_update_testrun(run)
        print(f"Starting run: {run_name} with run id {run_id}")
        
        if plan_name is None:
            print(f"No test plan found with name {plan_name}.")
            return
        print(f"Starting run with Test Plan: {plan_name}")

        if test_case_id:
            testcases = db.get_testcase_by_name(test_case_id)
            if not testcases:
                raise HTTPException(
                    status_code=500,
                    detail=f"Test case ID '{test_case_id}' does not exist"
                )
           
            testcases = [testcases]
            total_testcases = len(testcases)
            print(f"Length of testcases: {len(testcases)}")
            print(type(testcases))
            
            run.status = "RUNNING"
            db.add_or_update_testrun(run=run)
            
            
            background_tasks.add_task(
                execute_testcases,
                run_name,
                run_id,
                plan_name,
                target,
                
                testcases,
                run
            )

        elif metric_name:
            # metric_name = db.get_metric_name(metric_id=metric_id)  
            is_metric_in_plan = db.is_metric_in_testplan(metric_name=metric_name, plan_name=plan_name)  
            if not is_metric_in_plan:
                return
            testcases = db.get_testcases_by_metric(
                metric_name=metric_name,
                n=max_test_cases,
                lang_names=lang_name,
                domain_name=domain_name
            ) 
            if not testcases:
                print("No Test cases Found")
                return
            #     ## Get the metric from the provided ID 
            total_testcases = len(testcases)
            # metric = db.get_metric_by_id(metric_id=metric_id)
            # if metric is None:
            #     print("No Metric Found")
            #     return
            run.status = "RUNNING"
            db.add_or_update_testrun(run=run)
            background_tasks.add_task(
                execute_testcases,
                run_name,
                run_id,
                plan_name,
                target,
                
                testcases,
                run
            )
            

        else:
            testcases = db.get_testcases_by_testplan(plan_name=plan_name, n=max_test_cases, lang_names=lang_name, domain_name=domain_name)
            if not testcases:
                print("No Test cases Found")
                return
            total_testcases = len(testcases)   
            run.status = "RUNNING"
            db.add_or_update_testrun(run=run)
            background_tasks.add_task(
                execute_testcases,
                run_name,
                run_id,
                plan_name,
                target,
                
                testcases,
                run
            )
        
        return {
            "status": "success",
            "runId": run_id,
            "runName": run_name,
            "testPlanName": plan_name,
            "metricName": metric_name,
            "target": target,
            "totalTestCases": total_testcases,
            
        }
        
    else:
        return("Test Plan ID is mandatory")

@app.post("/continue-run")
def continue_run(data: ContinueRunRequest):
    # 1️⃣ Get run by name
    run = db.get_run_by_name(data.run_name)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # 2️⃣ Get run details
    details = db.get_run_details_by_run_id(run.run_id)
    print(f"Run {data.run_name} has {run} details")
    print(f"Found {len(details)} details for run {data.run_name}")
    return {
        "run": run,
        "details": details
    }

@app.post("/continue-run-with-plan")
def continue_run_with_plan(data: NewTestRun, background_tasks: BackgroundTasks):
    ensure_interface_manager_port_running(interface_manager_config)
    run = db.get_run_by_name(data.runName)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # 🔒 Safety check
    

    # 🔄 Reopen if completed
    if run.status == "COMPLETED":
        run.status = "RUNNING"
        run.end_ts = None
        db.add_or_update_testrun(run=run, override=True)

    run_id = run.run_id
    run_name = run.run_name
    

    
    plan_name = data.testPlan
    metric_name = data.metric
    testcase_id=data.testCaseId
    if testcase_id and metric_name:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'testCaseId' or 'metric', not both."
            )
    
    
    if not plan_name:
        raise HTTPException(status_code=400, detail="Test Plan is required")

    try:
        max_test_cases = int(data.maxTestCases)
    except:
        raise HTTPException(status_code=400, detail="Invalid maxTestCases")

    # 🔥 Fetch testcases
    if metric_name:
        testcases = db.get_testcases_by_metric(
            metric_name=metric_name,
            n=max_test_cases,
            lang_names=data.language,
            domain_name=data.domain
        )
    elif testcase_id:
        testcases = db.get_testcase_by_name(testcase_id)
        if not testcases:
            raise HTTPException(
                status_code=500,
                detail=f"Test case ID '{testcase_id}' does not exist"
            )    
        testcases = [testcases]
        total_testcases = len(testcases)
    else:
        testcases = db.get_testcases_by_testplan(
            plan_name=plan_name,
            n=max_test_cases,
            lang_names=data.language,
            domain_name=data.domain
        )

    if not testcases:
        raise HTTPException(status_code=400, detail="No testcases found")

    # 🚀 Launch background execution
    background_tasks.add_task(
        execute_testcases,
        run_name,
        run_id,
        plan_name,
        run.target,
        testcases,
        run
    )

    return {
        "status": "continued",
        "runId": run_id,
        "runName": run_name,
        "addedPlan": plan_name,
        "totalTestCases": len(testcases)
    }


async def execute_testcases(
    run_name,
    run_id,
    plan_name,
    target,
    
    testcases,
    run
):
    print(f"🚀 Background execution started for run {run_id}")
    
    client = None
    try:
        print("started")
        stop_watcher = threading.Event()
        watcher_thread = threading.Thread(
                target=watch_im_process,
                args=(interface_manager_config, profile_path, stop_watcher),  
                daemon=True
            )
        watcher_thread.start()
        agent_name = target
        application_name = target
        target_obj = db.get_target_by_name(target)
        application_url = target_obj.target_url
        APPLICATION_TYPE_MAP = {
            "WhatsApp": "WHATSAPP_WEB",
            "WebApp": "WEBAPP",
            "API": "API"
        }
        print("target object", target_obj)
        if target_obj.target_type not in APPLICATION_TYPE_MAP:
            raise ValueError(f"Unsupported target_type: {target_obj.target_type}")

        application_type = APPLICATION_TYPE_MAP[target_obj.target_type]

        client = InterfaceManagerClient(
            base_url="http://localhost:8000",
            application_type=application_type,
            agent_name=agent_name
        )
        await ws_manager.send_all({
            "type": "RUN_STARTED",
            "runId": run_id,
            "total": len(testcases)
        })

        try:
            client.sync_config({
                "application_name": application_name,
                "application_type": application_type,
                "agent_name": agent_name,
                "application_url": application_url
            })
            client.apply_server_config()
        except Exception as e:
            print(f"Interface manager setup failed for run {run_id}: {e}")
            run.status = "FAILED"
            run.end_ts = datetime.now().isoformat()
            db.add_or_update_testrun(run=run)
            await ws_manager.send_all({
                "type": "RUN_FINISHED",
                "runId": run_id,
                "status": "FAILED",
                "error": str(e)
            })
            return
        print("⏳ Waiting for WhatsApp to be ready...")
        

        print("✅ Starting testcase loop!")
        for index, testcase in enumerate(testcases, start=1):
            
            rundetail = None
            try:
                rundetail = RunDetail(
                    run_name=run_name,
                    plan_name=plan_name,
                    metric_name=testcase.metric,
                    testcase_name=testcase.name
                )
                rundetail_id = db.add_or_update_testrun_detail(rundetail)
                run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
                if run_status is not None and run_status == "COMPLETED":
                    print(f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution.")
                    continue

                message_to_agent = testcase.prompt.user_prompt or ""
                if testcase.prompt.system_prompt:
                    message_to_agent = testcase.prompt.system_prompt + " " + message_to_agent

                conv = Conversation(
                    target=target,
                    run_detail_id=rundetail_id,
                    testcase=testcase.name
                )
                conv_id = db.add_or_update_conversation(conversation=conv)
                print(f"A new conversation is created with ID: {conv_id}")

                rundetail.status = "RUNNING"
                db.add_or_update_testrun_detail(rundetail)
                conv.prompt_ts = datetime.now().isoformat()
                db.add_or_update_conversation(conversation=conv)

                await step({
                    "type": "STEP_UPDATE",
                    "runId": run_id,
                    "testcaseIndex": index,
                    "step": 1,
                    "status": "DONE"
                })
                await ws_manager.send_all({
                    "type": "STEP_UPDATE",
                    "runId": run_id,
                    "testcaseIndex": index,
                    "step": 2,
                    "status": "RUNNING"
                })
                response_from_agent = client.chat(
                    chat_id=testcase.testcase_id,
                    prompt_list=[message_to_agent]
                )
                await step({
                    "type": "STEP_UPDATE",
                    "runId": run_id,
                    "testcaseIndex": index,
                    "step": 2,
                    "status": "DONE"
                })
                agent_response = response_from_agent.json().get("response", "")
                
                if is_error_response(agent_response):
                    print(f"No response received from the agent for test case 1.")
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                    continue

                conv.response_ts = datetime.now().isoformat()
                conv.agent_response = agent_response[0]['response']
                db.add_or_update_conversation(conversation=conv)

                await step({
                    "type": "STEP_UPDATE",
                    "runId": run_id,
                    "testcaseIndex": index,
                    "step": 3,
                    "status": "DONE"
                })
                await step({
                    "type": "STEP_UPDATE",
                    "runId": run_id,
                    "testcaseIndex": index,
                    "step": 4,
                    "status": "DONE"
                })
                await step({
                    "type": "TESTCASE_FINISHED",
                    "runId": run_id,
                    "current": index
                })
                rundetail.status = "COMPLETED"
                db.add_or_update_testrun_detail(rundetail)
            except Exception as e:
                print(f"Testcase execution failed for run {run_id}, testcase index {index}: {e}")
                if rundetail is not None:
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                continue

        stop_watcher.set()        
        run.end_ts = datetime.now().isoformat()
        run.status = "COMPLETED"
        
        db.add_or_update_testrun(run=run)
        await ws_manager.send_all({
            "type": "RUN_FINISHED",
            "runId": run_id,
            "status": "COMPLETED"
        })
        print(f"🏁 Background execution finished for run {run_id}")

    except Exception as e:
        print(f"Background execution failed for run {run_id}: {e}")
        run.status = "FAILED"
        run.end_ts = datetime.now().isoformat()
        db.add_or_update_testrun(run=run)
        try:
            await ws_manager.send_all({
                "type": "RUN_FINISHED",
                "runId": run_id,
                "status": "FAILED",
                "error": str(e)
            })
        except Exception as ws_error:
            print(f"Failed to push RUN_FINISHED for failed run {run_id}: {ws_error}")
    finally:
        if client is not None:
            try:
                client.close()
            except:
                print(f"Client close failed (IM already dead): {e}")    



@app.get("/targets/{target_name}/metadata")
def get_target_metadata(target_name: str):

    clean_target_name = re.sub(
        r"\s*\(.*?\)", 
        "", 
        target_name
    ).strip()

    target = db.get_target_by_name(clean_target_name)

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    return {
        "domains": (
            [target.target_domain]
            if isinstance(target.target_domain, str)
            else target.target_domain
        ),
        "languages": target.target_languages or []
    }

@app.get("/__dev/config")
def dev_config():
    if not os.getenv("DEV_CONFIG_ENABLED"):
        print("Dev config is disabled.")
        raise HTTPException(status_code=404)
        
    print("Accessed dev config endpoint")
    return load_config()
    
@app.post("/__dev/config")
async def update_config(request: Request):
    

    data = await request.json()

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)

    return {"message": "Config updated"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=True
    )
