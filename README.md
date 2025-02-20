# ReAct Agent Implementation

This repository contains an implementation of a ReAct (Reason+Act) agent from scratch. ReAct is an approach that combines reasoning and acting in an interleaved manner, allowing AI agents (i.e., LLM) to perform better planning and decision-making.

## Overview

ReAct agents follow a cycle of:
1. **Reasoning** about the current situation and goal
2. **Planning** the next action based on reasoning
3. **Acting** by executing the planned action
4. **Observing** the results and updating understanding


## Getting Started

### Prerequisites
- Python 3.10+
- Required packages listed in `requirements.txt`

To be defined in a `.env` (not vrsion controlled):
- OpenAI API KEY 
- GOOGLE API KEY for custom google search
- Google Custom Search Engine ID

### Installation

```bash
git clone https://github.com/yourusername/react-agent.git
cd react-agent
pip install -r requirements.txt
```

## Usage

Basic example of using the ReAct agent:

```shell
python -m react_agents_from_scratch.run_agent
```

then follow the prompt in the terminal to interact with the agent.



## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the ReAct paper: ["ReAct: Synergizing Reasoning and Acting in Language Models"](https://arxiv.org/abs/2210.03629)
- Inspired by various tutorials and implementations in the AI community