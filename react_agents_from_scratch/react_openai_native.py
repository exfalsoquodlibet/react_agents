from openai import OpenAI
import requests
import json
import re
import os
from dotenv import load_dotenv
from datetime import datetime
from react_agents_from_scratch import tools
from react_agents_from_scratch.utils import read_prompt_from_txt

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Set up Google Search API key and engine ID
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

REACT_AGENT_PROMPT = read_prompt_from_txt("react_agents_from_scratch/openai_react/prompts/react_agent_prompt.txt")

# tools = [tools.search_govuk, tools.ask_user]

def parse_llm_output(response: str) -> dict[str, str]:
    
    patterns = {
        "thought": r"Thought\s*\d*:\s*(.*?)(?:\s*Action\s*(?:\d+:|:)|Action Input\s*(?:\d+:|:)|Observation\s*(?:\d+:|:)|Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "action": r"Action\s*(?:\d+:|:)\s*(.*?)(?:\s*Action Input\s*(?:\d+:|:)|Observation\s*(?:\d+:|:)|Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "action_input": r"Action Input\s*(?:\d+:|:)\s*(.*?)(?:\s*Observation\s*(?:\d+:|:)|Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "observation": r"Observation\s*(?:\d+:|:)\s*(.*?)(?:\s*Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "eureka_thought": r"Eureka Thought\s*(?:\d+:|:)\s*(.*?)(?:\s*Final Answer\s*(?:\d+:|:)|$)",
        "final_answer": r"Final Answer\s*(?:\d+:|:)\s*(.*)"
    }

    # extract data using regex
    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, response, re.DOTALL)
        extracted_data[key] = match.group(1).strip() if match else None
    
    return extracted_data


def format_react_loop_as_string(react_loop: dict[str, str], iteration_idx) -> str:
    """
    Example input:
        {
            "thought": "This is the first thought", 
            "action": "search_govuk",
            "action_input": "How to
            register for self-assessment",
            "observation": "This is the first observation",
            "eureka_thought": "This is the eureka thought",
            "final_answer": "This is the final answer"
        }
    Example output:
        Thought : This is the first thought
        Action : search_govuk
        Action Input : How to register for self-assessment
        Observation : This is the first observation
        Eureka Thought: This is the eureka thought
        Final Answer: This is the final answer
    """
    if react_loop.get('final_answer'):
        # return "\n".join([f"{' '.join([k.capitalize() for k in key.split('_')])} {iteration_idx}: {value}" if key in set(['thought', 'action', 'action_input', 'observation']) else f"{key.capitalize()}: {value}" for key, value in react_loop.items()])
        return "\n".join([f"{' '.join([k.capitalize() for k in key.split('_')])} : {value}" for key, value in react_loop.items()])
    else:
        # return "\n".join([f"{' '.join([k.capitalize() for k in key.split('_')])} {iteration_idx}: {value}" for key, value in react_loop.items() if key in set(['thought', 'action', 'action_input', 'observation'])])
        return "\n".join([f"{' '.join([k.capitalize() for k in key.split('_')])} : {value}" for key, value in react_loop.items() if key in set(['thought', 'action', 'action_input', 'observation'])])




def react_agent(question, prompt_template=REACT_AGENT_PROMPT, max_iterations=10):
    
    # Initial prompt
    prompt = prompt_template.format(question=question)
    full_conversation = []
    iterations = 0

    while iterations < max_iterations:
        print(f"###\nPrompt: {prompt} \n###\n")  # Debug statement
        print("*****************************")
        
        # get LLM response
        response = tools.get_llm_response(prompt)
        if not response:
            print("No response from LLM. Exiting loop.")
            break

        # parse the LLM response
        react_step = parse_llm_output(response) 

        # print(f"###\n Response: {response} \n###\n\n")
        # print(f"***\n React step: {react_step}*** \n\n")   

        # check if we have a final answer
        if react_step.get('final_answer'):
            print("Final answer found!")
            return react_step.get('final_answer')

        # Process actions if no final answer
        if react_step.get('action'):
            # get observation from executing the action
            try:
                if react_step.get('action') == "search_govuk":
                    action_input = react_step.get('action_input', '').strip('"')
                    observation = tools.search_govuk(query=action_input, min_results=3)
                    react_step['observation'] = observation if observation else "No results found."
                
                elif react_step.get('action') == "ask_user":
                    user_response = tools.ask_user(react_step.get('action_input'))
                    react_step['observation'] = f"The user responds: {user_response}" if user_response else "No response from user."
                
                else:
                    react_step['observation'] = f"Error: Invalid action '{react_step.get('action')}'. Must be one of [search_govuk, ask_user]"
            
            except Exception as e:
                react_step['observation'] = f"Error occurred while executing action: {str(e)}"
        
        # add this react step to conversation history
        full_conversation.append(react_step)
        
        # format the entire conversation history
        conversation_text = "\n\n".join([
            format_react_loop_as_string(step, idx + 1) 
            for idx, step in enumerate(full_conversation)
        ])

        print(f"&&&&&& \n Full conversation: {conversation_text} &&&&&\n\n")
        
        # Update prompt with full conversation history
        prompt = f"{prompt_template.format(question=question)}\n{conversation_text}"
        
        iterations += 1

    print("Maximum iterations reached without finding a final answer.")
    return None
        

     
def main(question: str):
    return react_agent(question)
    
    # print("*****************************")
    # print("\nAgent's reasoning process:")
    # # for step_type, step_content in steps:
    # #     print(f"\n{step_type}:")
    # #     print(step_content)
    # print(steps)

    # print("\nEnd of reasoning process.\n")
    
    # print(f"ANSWER: {final_answer}")
    # return final_answer
    
if __name__ == "__main__":
    user_question = input("Please enter your question: ")
    main(user_question)