import os
from agents.value_agent import ValuerAgent
from agents.deal_agent import DealAgent
from agents.assess_agent import AssessorAgent

from config import AGENT_SETTINGS
#config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# variables
b_model_performance_improvement = [0.4, "NULL", 0.4, 0.5]
b_capacity = ["NULL", "small", "medium", "large"]
b_data_entrophy = ["NULL", "low", "medium", "high"]
b_data_life = ["short", "NULL", "short", "medium", "long"]
b_history = ["NULL", "short", "medium", "long"]
b_market = ["NULL", "small", "medium", "large"]

s_model_performance_improvement = [0.4, 0.5]
s_capacity = ["small", "medium", "large"]
s_data_entrophy = ["low", "medium", "high"]
s_data_life = ["short", "medium", "long"]
s_history = ["short", "medium", "long"]
s_market = ["small", "medium", "large"]

# Loop through each combination
i = 0
for b_mpi in b_model_performance_improvement:
    for b_cap in b_capacity:
        for b_de in b_data_entrophy:
            for b_dl in b_data_life:
                for b_hist in b_history:
                    for b_market in b_market:
                        for s_mpi in s_model_performance_improvement:
                            for s_cap in s_capacity:
                                for s_de in s_data_entrophy:
                                    for s_dl in s_data_life:
                                        for s_hist in s_history:
                                            for s_market in s_market:
                                                i += 1
                                                buying_valuer = ValuerAgent(AGENT_SETTINGS["valuing_agent"])
                                                buyer_value = buying_valuer.analyze(b_mpi, b_cap, b_de, b_dl, b_hist, b_market)
                                                selling_valuer = ValuerAgent(AGENT_SETTINGS["valuing_agent"])
                                                seller_value = selling_valuer.analyze(s_mpi, s_cap, s_de, s_dl, s_hist, s_market)
                                                print(f"{i}: Valuer Agent completed")

                                                deal_agent = DealAgent(AGENT_SETTINGS["deal_agent"], i)
                                                deal = deal_agent.analyze(buyer_value, seller_value)
                                                log_2 = deal["log"]
                                                print(f"{i}: Deal Agent completed")

                                                assessor = AssessorAgent(AGENT_SETTINGS["assess_agent"], deal)
                                                log_3 = assessor.analyze()
                                                with open(f"assessments\{i}.txt", "w") as file:
                                                    file.write(log_3)
                                                print(f"{i}: Assessor Agent completed")

                                                with open(f"log\{i}.txt", "w") as file:
                                                    file.write("Buying Valuer:\n")
                                                    file.write(str(buyer_value)+"\n")
                                                    file.write("Selling Valuer:\n")
                                                    file.write(str(seller_value)+"\n")
                                                    file.write("Dealing Process:\n")
                                                    file.write(log_2)
                                                print(f"Experiment {i} completed")
                                                break
                                            break
                                        break
                                    break
                                break
                            break
                        break
                    break
                break
            break
        break
    break
print("————————————————————————All experiments completed————————————————————————")


