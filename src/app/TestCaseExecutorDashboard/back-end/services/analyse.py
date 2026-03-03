from fastapi import HTTPException, logger
from lib.strategy.strategy_implementor import StrategyImplementor
from datetime import datetime
def get_analyse_service(run_name: str, db):
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
        run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
        if not run_details:
            print(f"No run details found for run '{run_name}'.")
            raise HTTPException(
                status_code=404,
                detail=f"No run details found for run '{run_name}'."
            )
        print(run_details)
        # let's group the all the run_details by strategy for computational convenience.
        grouped_run_details = {}
        for detail in run_details:  
            # fetch the strategy name assigned for the testcase
            strategy_name = db.get_testcase_strategy_name(testcase_name=detail.testcase_name)
            if not strategy_name:
                logger.error(f"Strategy not found for testcase '{detail.testcase_name}' in run '{run.run_name}'.")
                continue

            group_key = strategy_name + ":" + detail.metric_name
            if group_key not in grouped_run_details:
                grouped_run_details[group_key] = []
            grouped_run_details[group_key].append(detail)
            # return grouped_run_details
        strategy = StrategyImplementor()

        for group in grouped_run_details.keys():
            strategy_name, metric_name = group.split(":")
            # instead of initializing the strategyimplementor for every strategy, we just set its name and the metric name
            strategy.set_metric_strategy(strategy_name=strategy_name, metric_name=metric_name)
            for detail in grouped_run_details[group]:
                # let's ignore the incomplete test cases.
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
                    
                score, reason = strategy.execute(testcase = testcase, conversation = conversation)
                conversation.evaluation_score = score
                conversation.evaluation_reason = reason
                conversation.evaluation_ts = datetime.now().isoformat()   
                db.add_or_update_conversation(conversation=conversation, override=False)
                return {
                    "status": "success"
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
