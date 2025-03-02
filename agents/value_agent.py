from typing import Dict, Any, List
from agents import BaseAgent

class ValuerAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.role = f"""You are a valuer agent. You will be given several traits of a data product.
                Your job is to analyze these traits and determine the value of the product.
                Give a expect price, a reason, and a confidence level after analyzing the traits.
                """


    def analyze(self, mpi, cap, de, dl, hist, market) -> Dict[str, Any]:
        """
        Analyze the given traits and return a dict
        """
        instructions = f"""Here are the traits and definitions:
        Model Performance Improvement (MPI): {mpi}
        Capacity: {cap}
        Data Entrophy: {de}
        Data Life: {dl}
        History: {hist}
        Market: {market}
        If any of the traits are NULL, it means that the trait is not available.

        Please analyze the traits and determine an expected price of the product.
        """

        strategy = f"""Here are some strategies to consider:
        - Consider the market size and demand for the product.
        - If too many traits are NULL, you shouldn't be confident in your valuation.
        - Do not answer with your trait data.
        """

        format = f"""
        Answer format:
        - Expected price: [price] (No $, no commas in the price. For example, 1000, not $1,000.)
        - Reason: [reason]
        - Confidence level: [confidence]

        """

        prompt = f"{self.role}\n{instructions}\n{strategy}\n{format}"
        response = self._create_prompt(self.role, prompt)
        result = self._parse_response(response)
        return result
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the response and return a dict
        """
        lines = response.splitlines()
        price = None
        reason = None
        confidence = None
        for line in lines:
            if line.startswith("- Expected price:"):
                price = line.split(":")[1].strip()
            elif line.startswith("- Reason:"):
                reason = line.split(":")[1].strip()
            elif line.startswith("- Confidence level:"):
                confidence = line.split(":")[1].strip()
        return {"price": price, "reason": reason, "confidence": confidence}

