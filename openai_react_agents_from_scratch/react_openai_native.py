from openai import OpenAI
import requests
import json
import re
import os
from dotenv import load_dotenv
from openai_react_agents_from_scratch import tools

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Set up Google Search API key and engine ID
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


# tools = [tools.search_govuk, tools.ask_user]


def parse_llm_output(response):
    thought = ""
    action = ""
    action_input = ""
    final_answer = ""

    # split the response into lines
    lines = response.split('\n')
    for line in lines:
        if line.startswith("Action:"):
            action = line[len("Action:"):].strip()
        elif line.startswith("Action Input:"):
            action_input = line[len("Action Input:"):].strip()
        elif line.startswith("Final Answer:"):
            final_answer = line[len("Final Answer:"):].strip()
        elif not action and not action_input and not final_answer:
            # assume the first part of the response is the thought if no other labels are found
            thought += line.strip() + " "

    thought = thought.strip()
    return thought, action, action_input, final_answer


def react_agent(question, user_input_func: callable = None, max_iterations=10):
    prompt_template = """
    The year is 2024 and you are an AI assistant for the UK Government helping users navigate official government guidance 
    and services.
    Answer the following question as best you can. 
    
    You have access to the following tools:
    1. search_govuk: This tool searches only gov.uk websites for official UK government information. 
        Use this tool whenever a search is needed to find official government sources. Do not simulate searches; use the tool.
    2. ask_user: This tool allows you to ask the user for additional information that you need to answer their question.

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [search_govuk, ask_user]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer that I should provide
    Final Answer: the final answer to the original input question. Always include a reference to the source of the information.

    Begin!

    Question: {question}
    Thought:
    """
    
    # Initial prompt
    prompt = prompt_template.format(question=question)
    full_response = ""
    steps = []
    iterations = 0

    while iterations < max_iterations:
        response = tools.get_llm_response(prompt)
        if not response:
            print("No response from LLM. Exiting loop.")
            break

        print(f"###\nLLM Response: {response} \n###\n")  # Debug statement
        thought, action, action_input, final_answer = parse_llm_output(response)

        if thought:
            full_response += f"{thought}\n"
            steps.append(("Thought", thought))


        # print(f"Action: #{action}#, Action Input: {action_input}, Final Answer: {final_answer}")  # Debug statement
        if action == "search_govuk":
            steps.append(("Action", "Google Search"))
            steps.append(("Action Input", action_input))
            observation = tools.search_govuk(query=action_input, min_results=1)
            # print(f"Google Search observation: {observation}")  # Debug statement
            if observation:
                full_response += f"Observation: {observation}\nThought: "
                steps.append(("Observation", f"Query: {action_input}\nResult: {observation}"))
            else:
                full_response += "Observation: No results found.\nThought: "
                steps.append(("Observation", f"Query: {action_input}\nNo results found."))
        elif action == "ask_user" and user_input_func:
            user_response = user_input_func(action_input)
            steps.append(("Action", "Ask User"))
            steps.append(("Action Input", action_input))
            if user_response:
                full_response += f"User Response: {user_response}\nThought: "
                steps.append(("Observation", f"Question: {action_input}\nUser Response: {user_response}"))
            else:
                full_response += "User did not provide a response.\nThought: "
                steps.append(("Observation", f"Question: {action_input}\nNo response provided."))
        elif final_answer:
            full_response += f"Final Answer: {final_answer}"
            steps.append(("Final Answer", final_answer))
            break
        else:
            print("No valid action or final answer found. Exiting loop.")
            break

        # Update the prompt with the full response so far
        prompt = prompt_template.format(question=question) + f"\n{full_response}"
        iterations += 1

    if iterations == max_iterations:
        print("Maximum iterations reached without finding a final answer.")

    return final_answer, steps

def main(question: str):
    final_answer, steps = react_agent(question, user_input_func=tools.ask_user)
    
    print("*****************************")
    print("\nAgent's reasoning process:")
    # for step_type, step_content in steps:
    #     print(f"\n{step_type}:")
    #     print(step_content)
    print(steps)

    print("\nEnd of reasoning process.\n")
    
    print(f"ANSWER: {final_answer}")
    return final_answer
    
if __name__ == "__main__":
    user_question = input("Please enter your question: ")
    main(user_question)