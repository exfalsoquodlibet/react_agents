import re
from typing import Optional, Callable
from react_agents_from_scratch import tools


def parse_llm_output(response: str) -> dict[str, str]:
    """Parse the LLM output into structured components."""
    patterns = {
        "thought": r"Thought\s*\d*:\s*(.*?)(?:\s*Action\s*(?:\d+:|:)|Action Input\s*(?:\d+:|:)|Observation\s*(?:\d+:|:)|Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "action": r"Action\s*(?:\d+:|:)\s*(.*?)(?:\s*Action Input\s*(?:\d+:|:)|Observation\s*(?:\d+:|:)|Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "action_input": r"Action Input\s*(?:\d+:|:)\s*(.*?)(?:\s*Observation\s*(?:\d+:|:)|Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "observation": r"Observation\s*(?:\d+:|:)\s*(.*?)(?:\s*Eureka Thought\s*(?:\d+:|:)|Final Answer\s*(?:\d+:|:)|$)",
        "eureka_thought": r"Eureka Thought\s*(?:\d+:|:)\s*(.*?)(?:\s*Final Answer\s*(?:\d+:|:)|$)",
        "final_answer": r"Final Answer\s*(?:\d+:|:)\s*(.*)"
    }
    
    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, response, re.DOTALL)
        extracted_data[key] = match.group(1).strip() if match else None
    
    return extracted_data


def format_react_loop(react_loop: dict[str, str]) -> Optional[tuple[str, str]]:
    """Format a single ReAct loop iteration as a string.
    
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
    components = []
    
    # order of components
    ordered_keys = ['thought', 'action', 'action_input', 'observation', 'eureka_thought', 'final_answer']
    
    for key in ordered_keys:
        if react_loop.get(key):
            formatted_key = ' '.join(word.capitalize() for word in key.split('_'))
            components.append(f"{formatted_key} : {react_loop[key]}")
    
    return '\n'.join(components)

def react_agent(question: str, llm_brain_call: Callable, prompt_template: str, tools: dict, max_iterations: int = 10) -> Optional[str]:
    """
    Execute the ReAct agent loop.
    
    Args:
        question: The user's question
        llm_brain_call: The function to call the LLM agentic brain
        prompt_template: The template for the ReAct prompt
        tools: Dictionary of available tools
        max_iterations: Maximum number of iterations before giving up
        
    Returns:
        Optional[str]: The final answer if found, None otherwise
    """
    prompt = prompt_template.format(question=question)
    full_conversation: list[dict[str, str]] = []
    iterations = 0
    
    while iterations < max_iterations:
        # get LLM response
        response = llm_brain_call(prompt)
        if not response:
            print("No response from LLM. Exiting loop.")
            return None
            
        # parse the response
        react_step = parse_llm_output(response)
        
        # check for final answer
        if react_step.get('final_answer'):

            # format full react history
            full_conversation.append(react_step)
            conversation_text = "\n\n".join(
                format_react_loop(step) 
                for _, step in enumerate(full_conversation)
            )

            # return answer, and full history 
            print(f"\n\nFinal answer found in {iterations + 1} iterations.\n")
            return react_step['final_answer'], conversation_text
            
        # execute action if present and get observation
        if react_step.get('action'):
            action_name = react_step['action'].strip()
            action_input = react_step.get('action_input', '').strip('"')
            
            # Execute the tool
            if action_name in tools:
                try:
                    observation = tools[action_name](action_input)
                    react_step['observation'] = observation if observation else "No results found."
                except Exception as e:
                    react_step['observation'] = f"Error occurred while executing action: {str(e)}"
            else:
                react_step['observation'] = f"Error: Invalid action '{action_name}'. Must be one of {list(tools.keys())}"
        
        # add step to conversation history
        full_conversation.append(react_step)
        
        # format conversation history
        conversation_text = "\n\n".join(
            format_react_loop(step) 
            for _, step in enumerate(full_conversation)
        )
        
        # update prompt with conversation history
        prompt = f"{prompt_template.format(question=question)}\n{conversation_text}"
        # print(f"** React step {iterations + 1}: {conversation_text} **\n\n")

        iterations += 1
    
    print("Maximum iterations reached without finding a final answer.")
    return None

def main(question: str, llm_brain_call: Callable, prompt_template: str, tools: dict) -> Optional[str]:
    """
    Main entry point for the ReAct agent.
    
    Args:
        question: The user's question
        prompt_template: The template for the ReAct prompt
        tools: Dictionary of available tools
        
    Returns:
        Optional[str]: The final answer if found, None otherwise
    """
    return react_agent(question, llm_brain_call, prompt_template, tools)


if __name__ == "__main__":
    from react_agents_from_scratch.openai_react import call_llm
    from react_agents_from_scratch.utils import read_prompt_from_txt
    REACT_AGENT_PROMPT = read_prompt_from_txt("react_agents_from_scratch/openai_react/prompts/react_agent_prompt.txt")

    tools = {
        'search_govuk': tools.search_govuk,
        'search_govuk_services': tools.search_govuk_services,
        'ask_user': tools.ask_user
    }

    user_question = input("Please enter your question: ")
    answer, _ = main(
        question=user_question,
        llm_brain_call=call_llm.get_llm_response,
        prompt_template=REACT_AGENT_PROMPT,
        tools=tools
    )
    if answer:
        print(f"Here is an answer for you! \n: {answer} \n\n")
    else:
        print("No answer found.\n\n")
    