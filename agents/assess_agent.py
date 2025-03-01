from typing import Dict, Any, List
from agents import BaseAgent

class AssessorAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any], log: Dict[str, Any]):
        super().__init__(config)
        self.log = log
        self.role = f"""You are an assessor. You will be offered a deal log, 
                and you will analyze and assess it by answer questions about it."""


    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the deal log and answer questions
        """
        description = f"""Here is the deal log:
        {self.log}
        """
        questions = f"""Please answer the following questions:
        1. what's the final price?
        2. Is the deal fair?

        answer the questions in the following format:
        1. [Your answer]
        2. [Your answer]
        """
        content = description + questions
        role = self.role
        prompt = self._create_prompt(role, content)
        return prompt
    


