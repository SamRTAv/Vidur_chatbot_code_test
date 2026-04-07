from nemoguardrails.actions import action

@action(name="my_custom_string_check_action")
async def my_custom_string_check_action(context: dict, llm_task_manager, llm):
    user_input = context.get("user_message")
    
    # 1. Grab your custom prompt using the task manager
    prompt = llm_task_manager.render_task_prompt(
        task="my_custom_string_check",
        context={"user_input": user_input}
    )
    
    # 2. Call the LLM directly to get the response
    response = await llm.ainvoke(prompt)
    
    # Extract the text (handles both raw strings and LangChain message objects)
    if hasattr(response, "content"):
        response_text = response.content.strip().lower()
    else:
        response_text = str(response).strip().lower()
    
    # 3. Parse the output safely in Python
    if "unsafe and should be flagged" in response_text:
        return "unsafe and should be flagged"

    elif "safe but should be flagged" in response_text:
        return "safe but should be flagged"

    else:
        return "safe and should not be flagged"