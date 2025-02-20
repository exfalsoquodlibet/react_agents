from functools import partial
from react_agents_from_scratch.openai_react import call_llm
from react_agents_from_scratch.react_agent_naive import main
from react_agents_from_scratch import tools
from react_agents_from_scratch.utils import read_prompt_from_txt, format_and_save_markdown

REACT_AGENT_PROMPT = read_prompt_from_txt("react_agents_from_scratch/openai_react/prompts/react_agent_prompt.txt")

tools = {
        'search_govuk': partial(tools.search_govuk, min_results=3),
        'search_govuk_services': partial(tools.search_govuk_services, page=1, min_results=6),
        'ask_user': tools.ask_user
    }

user_question = input("Please enter your question: ")
    
answer, react_history = main(
        question=user_question,
        llm_brain_call=call_llm.get_llm_response,
        prompt_template=REACT_AGENT_PROMPT,
        tools=tools
    )
if answer:
    print("\n")
    print(f"**Here is an answer for you!\n\n** \n: {answer} \n\n")
else:
    print("No answer found.\n\n")

format_and_save_markdown(react_history, "react_history.md")

# print("\n\n\n\n\n")
# print("##############################################")
# print("ReAct loop:")
# print("\n\n")
# print(react_history)