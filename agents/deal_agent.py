from typing import Dict, Any, List
from agents import BaseAgent
from agents.memory_agent import MemorySummaryAgent
import re

class DealAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any], i: int):
        super().__init__(config)
        self.i = i
        self.max_rounds = 5
        self.roles = [
            {
            "name": "Buyer",
            "description": f"""You are a buyer of a data product. You are about to enter a negotiation.
            Your goal is to get the lowest price possible for the data product.
            When making an offer, always start by stating your price.
            You are truly willing to reach a deal before the dealing rounds end.
            Here are some strategies to consider:
            - Start with a lower price than your expected value to leave room for negotiation.
            - Be prepared to adjust your price based on the seller's counteroffers.
            - Do not say any number other than your price.
            """
            },
            {
            "name": "Seller",
            "description": f"""You are a seller of a data product. You are about to enter a negotiation.
            Your goal is to get the highest price possible for the data product.
            When making an offer, always start by stating your price.
            You are truly willing to reach a deal before the dealing rounds end.
            Here are some strategies to consider:
            - Start with a higher price than your expected value to leave room for negotiation.
            - Be prepared to adjust your price based on the buyer's counteroffers.
            - Do not say any number other than your price.
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

    
    """
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        market_data = data.get("market_data", {})
        proposed_action = data.get("proposed_action", {})
        news_analysis = data.get("news_analysis", {})
        reflection_analysis = data.get("reflection_analysis", {})

        # Add context to roles based on other agents' analyses
        enhanced_roles = []
        for role in self.roles:
            role_info = role.copy()
            
            # Add context to role description
            context_additions = f""
            Consider the following additional context in your analysis:
            
            News Analysis:
            {news_analysis}
            
            Reflection Analysis:
            {reflection_analysis}
            ""
            
            role_info["description"] = role_info["description"] + context_additions
            enhanced_roles.append(role_info)
        
        # Use enhanced roles for debate
        debate_results = self._conduct_debate(market_data, proposed_action, enhanced_roles)
        
        final_analysis = self._synthesize_debate(debate_results)
        
        analysis_result = {
            "debate_analysis": final_analysis,
            "debate_rounds": debate_results,
            "timestamp": data.get("timestamp"),
            "confidence_score": self._calculate_confidence(debate_results, market_data)
        }
        
        self.save_to_memory(analysis_result)
        return analysis_result
    """
    
    def conduct_deal_round(self, buyer_value: Dict[str, Any], seller_value: Dict[str, Any], 
                     enhanced_roles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deal_rounds = []
        for round_num in range(self.max_rounds):
            round_results = []
            buyer_price = None
            seller_price = None
            for role_info in enhanced_roles:
                if round_num == 0:
                    role = role_info["description"]
                else:
                    role = f"""
                    You are the {role_info['name']} in this deal.
                    Continue focusing on your domain.
                    You may change your price freely this round.
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
                - Provide a price for the data product.
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

            deal_rounds.extend(round_results)

            if buyer_price is not None and seller_price is not None and buyer_price == seller_price:
                break

            last_round_num = round_results[-1]['round']
            this_round_data = [r['log'] for r in round_results if r['round'] == last_round_num]
            round_summary = self.memory_summarizer.summarize_speeches(this_round_data)
            self.short_term_memory.clear()
            self.memory_summarizer.add_to_short_term_memory(self.short_term_memory, round_summary)
            self.memory_summarizer.add_to_mid_term_memory(self.mid_term_memory, round_summary)
        survey(self)
        return deal_rounds


    '''def _conduct_debate(self, market_data: Dict[str, Any], proposed_action: Dict[str, Any], 
                       enhanced_roles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        debate_rounds = []
        stocks = sorted(market_data.keys())

        for round_num in range(self.debate_rounds):
            round_results = []
            for role_info in enhanced_roles:
                if round_num == 0:
                    role = role_info["description"]
                else:
                    role = f"""You are the {role_info['name']} analyst. Continue focusing on your domain.
                               You may change Bullish/Bearish stance freely this round.
                               You must explicitly refute or support previous round's differing opinions from the short-term memory.
                               If you maintain your previous stance, justify it against the arguments in short-term memory.
                               If you change your stance, explain why you changed in response to previous arguments.
                               """

                perspective_name = role_info["name"]

                stock_instructions = "\n".join(
                    [f"{i+1}. {symbol}: {market_data[symbol]}" for i, symbol in enumerate(stocks)]
                )

                content = f"""
                Round {round_num + 1} of debate ({perspective_name.upper()}):

                Market Data for each stock:
                {stock_instructions}

                Proposed Action:
                {proposed_action}

                Mid-term Memory (accumulated):
                {self._get_mid_term_info()}

                Short-term Memory (last round only):
                {self._get_short_term_info()}

                Previous Arguments:
                {self._format_previous_rounds(debate_rounds)}

                Instructions:
                - For each stock listed above, choose either Bullish or Bearish stance. You may change your stance from previous rounds.
                - You must explicitly address (refute or justify) viewpoints from the Short-term Memory that contradict your stance or reinforce it.
                - Provide a short but specific viewpoint (4-5 sentences max) referencing these arguments.
                - Format the output so that for each stock you produce exactly one line:
                    "Stock: SYMBOL - Bullish(or Bearish) Your short viewpoint"
                - Do this in the same order as the stocks are listed.
                - Keep it concise and debate-like. Use adjective-rich language to convey confidence and expertise.
                """

                response = self._create_prompt(role, content)
                round_results.append({
                    "round": round_num + 1,
                    "perspective": perspective_name,
                    "arguments": response
                })

            debate_rounds.extend(round_results)

            stock_stances = self._extract_stock_stances(round_results, stocks)

            last_round_num = round_results[-1]['round']
            this_round_data = [r['arguments'] for r in round_results if r['round'] == last_round_num]
            round_summary = self.memory_summarizer.summarize_speeches(this_round_data)
            self.short_term_memory.clear()
            self.memory_summarizer.add_to_short_term_memory(self.short_term_memory, round_summary)
            self.memory_summarizer.add_to_mid_term_memory(self.mid_term_memory, round_summary)

        return debate_rounds'''


    '''def _extract_stock_stances(self, round_data: List[Dict[str, Any]], stocks: List[str]) -> Dict[str, List[str]]:
        stances_per_stock = {s: [] for s in stocks}

        for r in round_data:
            arguments = r['arguments'].strip().split('\n')
            for line in arguments:
                line = line.strip().lower()
                if line.startswith("stock:"):
                    parts = line.split('-')
                    if len(parts) < 2:
                        continue
                    symbol_part = parts[0].replace("stock:", "").strip()
                    stance_part = parts[1].strip()
                    symbol = symbol_part
                    if symbol in stances_per_stock:
                        if stance_part.startswith("bullish"):
                            stances_per_stock[symbol].append("bullish")
                        elif stance_part.startswith("bearish"):
                            stances_per_stock[symbol].append("bearish")
                        else:
                            stances_per_stock[symbol].append("neutral")

        return stances_per_stock'''

    def get_price(self, response: str) -> float:
        '''
        Extract the price from the response.
        '''
        # Extract the price from the response.
        # The price should be the first number found in the response.
        match = re.search(r'\d+(\.\d+)?', response)
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
        
        if final_price == previous_price:
            return final_price
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
        

    '''def _synthesize_debate(self, debate_rounds: List[Dict[str, Any]]) -> str:
        role = """You are a senior market strategist tasked with synthesizing insights 
                    from five specialized analysts (fundamental, technical, risk, always_bull, always_bear) for multiple stocks."""
        
        content = f"""
        Synthesize the following debate rounds into a final analysis:

        Mid-term Memory (accumulated from all rounds):
        {self._get_mid_term_info()}

        Short-term Memory (just last round):
        {self._get_short_term_info()}
        
        Debate History:
        {self._format_previous_rounds(debate_rounds)}
        
        Instructions:
        - Provide a balanced final analysis for each stock considered.
        - For each stock, mention if there was more Bullish or Bearish consensus.
        - Provide a final recommendation considering all perspectives, including the extreme bull/bear, and overall risk/reward.
        """

        return self._create_prompt(role, content)'''
    
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
    '''
    def _format_previous_rounds(self, debate_rounds: List[Dict[str, Any]]) -> str:
        if not debate_rounds:
            return "No previous arguments."
        
        formatted_rounds = []
        for round_data in debate_rounds:
            formatted_rounds.append(
                f"Round {round_data['round']} ({round_data['perspective'].upper()}):\n"
                f"{round_data['arguments']}\n"
            )
        
        return "\n".join(formatted_rounds)'''

    def _get_mid_term_info(self) -> str:
        if not self.mid_term_memory:
            return "No mid-term memory recorded."
        return " | ".join(self.mid_term_memory)

    def _get_short_term_info(self) -> str:
        if not self.short_term_memory:
            return "No short-term memory recorded."
        return self.short_term_memory[-1]
'''
    def _calculate_confidence(self, debate_rounds: List[Dict[str, Any]], market_data: Dict[str, Any]) -> float:
        confidence = 0.5

        if not debate_rounds:
            return confidence

        total_rounds = max(r["round"] for r in debate_rounds)
        expert_roles = ["fundamental", "technical", "risk"]
        
        sum_of_weights = total_rounds * (total_rounds + 1) / 2.0
        increments = 0.0 

        domain_positive_terms = [
            'strong momentum', 'investor confidence', 'reinforcing a positive outlook', 'upward momentum', 
            'robust interest', 'healthy demand', 'resilience', 'favorable outlook', 'clearly', 'strongly', 
            'definitely', 'consistently', 'well-supported', 'firm evidence', 'high conviction', 'no doubt', 
            'strongly grounded', 'robust evidence', 'unwavering', 'highly credible', 'solid foundation',
            'conclusive', 'authoritative', 'well-substantiated'
        ]

        domain_negative_terms = [
            'regulatory scrutiny', 'downward movement', 'selling pressure', 'challenges', 'volatility', 'pressure',
            'possibly', 'might', 'unclear', 'uncertain', 'tentative', 'questionable', 'ambiguous', 'unverified', 
            'guesswork', 'speculation', 'lack of clarity', 'insufficient data', 'doubtfully', 'not guaranteed', 
            'inconclusive', 'skeptical', 'dubious', 'no clear evidence'
        ]


        for round_num in range(1, total_rounds + 1):
            current_round_experts = [r for r in debate_rounds if r["round"] == round_num and r["perspective"] in expert_roles]

            if len(current_round_experts) < 3:
                continue

            stock_stances = {}
            all_arguments_text = [] 
            
            for entry in current_round_experts:
                perspective = entry["perspective"]
                lines = entry["arguments"].strip().split('\n')
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.lower().startswith("stock:"):
                        parts = line_stripped.split('-', 1)
                        if len(parts) != 2:
                            continue
                        stock_part = parts[0].replace("Stock:", "").strip()
                        stance_part = parts[1].strip().lower()
                        if stance_part.startswith("bullish"):
                            stance = "bullish"
                        elif stance_part.startswith("bearish"):
                            stance = "bearish"
                        else:
                            stance = "neutral"

                        if stock_part not in stock_stances:
                            stock_stances[stock_part] = {}
                        stock_stances[stock_part][perspective] = stance
                    all_arguments_text.append(line_stripped.lower())

            round_weight = round_num
            for symbol, stances in stock_stances.items():
                if len(stances) == 3:
                    f_stance = stances.get("fundamental", "neutral")
                    t_stance = stances.get("technical", "neutral")
                    r_stance = stances.get("risk", "neutral")
                    if f_stance == t_stance == r_stance and f_stance in ["bullish", "bearish"]:
                        increments += 0.1 * round_weight
                    else:
                        increments -= 0.05 * round_weight
            
            text_joined = " ".join(all_arguments_text)
            domain_positive_count = sum(term in text_joined for term in domain_positive_terms)
            domain_negative_count = sum(term in text_joined for term in domain_negative_terms)
            increments += 0.005 * domain_positive_count * round_weight
            increments -= 0.005 * domain_negative_count * round_weight

        confidence += increments / sum_of_weights

        confidence = max(0.0, min(1.0, confidence))
        return confidence'''

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
            file.write(f"Survey response from {perspective_name}:")
            file.write(response)