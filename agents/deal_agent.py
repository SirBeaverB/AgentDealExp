from typing import Dict, Any, List
from agents import BaseAgent
from agents.memory_agent import MemorySummaryAgent
import re

class DealAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any], i: int):
        super().__init__(config)
        self.i = i
        self.max_rounds = 8
        self.roles = [
            {
            "name": "Buyer",
            "description": f"""You are a buyer of a data product. You are about to enter a negotiation.
            Your goal is to get the lowest price possible for the data product.
            When making an offer, always start by stating your price. Do not mention other numbers.
            Do not reapeat the price offered by the seller unless you agree with it.
            You are truly willing to reach a deal before the dealing rounds end.
            Here are some strategies to consider:
            - Start with a lower price than your expected value to leave room for negotiation.
            - Be prepared to adjust your price based on the seller's counteroffers.
            """
            },
            {
            "name": "Seller",
            "description": f"""You are a seller of a data product. You are about to enter a negotiation.
            Your goal is to get the highest price possible for the data product.
            When making an offer, always start by stating your price. Do not mention other numbers.
            Do not reapeat the price offered by the buyer unless you agree with it.
            You are truly willing to reach a deal before the dealing rounds end.
            Here are some strategies to consider:
            - Start with a higher price than your expected value to leave room for negotiation.
            - Be prepared to adjust your price based on the buyer's counteroffers.
            """
            }
        ]
        self.memory_summarizer = MemorySummaryAgent(config=config)
        self.mid_term_memory = []
        self.short_term_memory = []

    def analyze(self, buyer_value: Dict[str, Any], seller_value: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Receive value from the valuing agent,
        and execute the deal.
        '''
        buyer_expected_price = buyer_value.get("expected_price", {})
        buyer_reason = buyer_value.get("reason", {})
        buyer_confidence = buyer_value.get("confidence", {})

        seller_expected_price = seller_value.get("expected_price", {})
        seller_reason = seller_value.get("reason", {})
        seller_confidence = seller_value.get("confidence", {})

        enhanced_roles = []
        for role in self.roles:
            role_info = role.copy()
            if role["name"] == "Buyer":
                context_additions = f"""
                Consider the following additional context while dealing:
                You expect the price to be: {buyer_expected_price} 
                This is because: {buyer_reason} 
                Your confidence in this valuation is {buyer_confidence}.
                """
            if role["name"] == "Seller":
                context_additions = f"""
                Consider the following additional context while dealing:
                You expect the price to be: {seller_expected_price} 
                This is because: {seller_reason} 
                Your confidence in this valuation is {seller_confidence}.
                """
            role_info["description"] = role_info["description"] + context_additions
            enhanced_roles.append(role_info)
        

        deal_rounds = self.conduct_deal_round(buyer_value, seller_value, enhanced_roles)
        final_price = self.extract_final_price(deal_rounds)
        log = self.extract_log(deal_rounds)

        execution_result = {
            "deal_analysis": final_price,
            "deal_rounds": deal_rounds,
            "final_price": final_price,
            "log": log
        }

        return execution_result

    def conduct_deal_round(self, buyer_value: Dict[str, Any], seller_value: Dict[str, Any], 
                     enhanced_roles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deal_rounds = []
        for round_num in range(self.max_rounds):
            round_results = []
            buyer_price = None
            seller_price = None
            for role_info in reversed(enhanced_roles):
                if round_num == 0:
                    role = role_info["description"]
                else:
                    role = f"""
                    You are the {role_info['name']} in this deal.
                    Continue focusing on your domain.
                    You may change your price freely this round. 
                    State your price first while speaking by saying "I offer [price]."
                    Do not repeat the price offered by the other party, unless you agree with it.
                    """
                perspective_name = role_info["name"]
                additional_content = f"""
                Round {round_num + 1} of deal ({perspective_name.upper()}):
                Mid-term Memory (accumulated):
                {self._get_mid_term_info()}
                Short-term Memory (last round only):
                {self._get_short_term_info()}
                Previous Prices:
                {self.format_deal_rounds(deal_rounds)}
                You can get the offered price from the other party last round from your short-term memory.
                Instructions:
                - Provide a price for the data product. State your price by saying "I offer [price]. [Your reasoning]." 
                - No commas in the price. For example, 1000, not 1,000.
                - Consider accepting the offer if the other party’s price is no more than 100 $ different from yours.
                - You can change your price from last round.
                - If you agree with the other party's price, you can accept it by repeating the accepted price first.
                - Keep it concise and deal-like. Use adjective-rich language and convey your confidence, which was offered to you previously.
                - Remember that you have {self.max_rounds - round_num} rounds left.
                """

                response = self._create_prompt(role, additional_content)
                price = self.get_price(response)
                round_results.append({
                    "round": round_num + 1,
                    "perspective": perspective_name,
                    "price": price,
                    "log": response,
                })

                if perspective_name == "Buyer":
                    buyer_price = price
                elif perspective_name == "Seller":
                    seller_price = price

                self.memory_summarizer.add_to_short_term_memory(self.short_term_memory, response)

            deal_rounds.extend(round_results)

            if buyer_price is not None and seller_price is not None and abs(buyer_price - seller_price) <= 10:
                break

            last_round_num = round_results[-1]['round']
            this_round_data = [r['log'] for r in round_results if r['round'] == last_round_num]
            round_summary = self.memory_summarizer.summarize_speeches(this_round_data)
            self.short_term_memory.clear()
            self.memory_summarizer.add_to_short_term_memory(self.short_term_memory, round_summary)
            self.memory_summarizer.add_to_mid_term_memory(self.mid_term_memory, round_summary)
        survey(self)
        return deal_rounds


    def get_price(self, response: str) -> float:
        '''
        Extract the price from the response.
        '''
        # Extract the price from the response.
        # The price should be the first number found in the response.
        match = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', response)
        if match:
            return float(match.group(0))
        else:
            raise ValueError("Price not found in response.")

    def extract_final_price(self, deal_rounds: List[Dict[str, Any]]) -> str:
        '''
        Extract the final price from the deal rounds.
        '''
        if not deal_rounds:
            return "No deal rounds conducted."
        if len(deal_rounds) < 2:
            return "No deal."
        
        final_price = deal_rounds[-1]["price"]
        previous_price = deal_rounds[-2]["price"]
        
        if final_price - previous_price <= 10:
            return (final_price + previous_price) / 2
        else:
            return "No deal."
        
    def extract_log(self, deal_rounds: List[Dict[str, Any]]) -> str:
        '''
        Extract the log from the deal rounds.
        '''
        if not deal_rounds:
            return "No deal rounds conducted."
        log = "\n".join([f"Round {r['round']} ({r['perspective']}): {r['log']}" for r in deal_rounds])
        return log
        
    
    def format_deal_rounds(self, deal_rounds: List[Dict[str, Any]]) -> str:
        if not deal_rounds:
            return "No previous rounds."
        
        formatted_rounds = []
        for round_data in deal_rounds:
            formatted_rounds.append(
                f"Round {round_data['round']} ({round_data['perspective'].upper()}):\n"
                f"{round_data['price']}\n"
            )
        
        return "\n".join(formatted_rounds)

    def _get_mid_term_info(self) -> str:
        if not self.mid_term_memory:
            return "No mid-term memory recorded."
        return " | ".join(self.mid_term_memory)

    def _get_short_term_info(self) -> str:
        if not self.short_term_memory:
            return "No short-term memory recorded."
        return self.short_term_memory[-1]


def survey(self):
    for role in self.roles:
        role_info = role.copy()
        perspective_name = role_info["name"]
        additional_content = f"""
        You are the {perspective_name} in this deal.
        Here is a brief summary of the dealing process:
        {self._get_mid_term_info()}
        Now, please answer the following survey question based on your experience in the deal, answer as briefly as possible:
        - On a scale of 1 to 10, how fair was the final price in your opinion?
        - On a scale of 1 to 10, how confident are you during the dealing process?
        please give your answer strictly in this format:
        1. [your answer]
        2. [your answer]
        """
        response = self._create_prompt(role_info["description"], additional_content)
        with open(f"survey_result\{self.i}_survey_response_{perspective_name}.txt", "w", encoding="utf-8") as file:
            file.write(f"Survey response from {perspective_name}:\n")
            file.write(response)