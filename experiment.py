import os
from agents.value_agent import ValuerAgent
from agents.deal_agent import DealAgent
from agents.assess_agent import AssessorAgent
from config import AGENT_SETTINGS
import time


#config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# variables
model_performance_improvement = [0.4, 0.5]
capacity = ["small", "medium", "large"]
data_entrophy = ["low", "medium", "high"]
data_life = ["short", "medium", "long"]
history = ["short", "medium", "long"]
market = ["small", "medium", "large"]

start_time = time.time()

i = 0
for s_mpi in model_performance_improvement:
    for s_cap in capacity:
        for s_de in data_entrophy:
            for s_dl in data_life:
                for s_hist in history:
                    for s_mark in market:
                        for b_mpi in ["NULL", s_cap]:
                            for b_cap in ["NULL", s_de]:
                                for b_de in ["NULL", s_dl]:
                                    for b_dl in ["NULL", s_hist]:
                                        for b_hist in ["NULL", s_mark]:
                                            for b_market in ["NULL", s_mpi]:
                                                i += 1
                                                argu = {
                                                    "model_performance_improvement": (s_mpi, b_mpi),
                                                    "capacity": (s_cap, b_cap),
                                                    "data_entrophy": (s_de, b_de),
                                                    "data_life": (s_dl, b_dl),
                                                    "history": (s_hist, b_hist),
                                                    "market": (s_mark, b_market)
                                                }
                                                buying_valuer = ValuerAgent(AGENT_SETTINGS["valuing_agent"])
                                                buyer_value = buying_valuer.analyze(b_mpi, b_cap, b_de, b_dl, b_hist, b_market)
                                                selling_valuer = ValuerAgent(AGENT_SETTINGS["valuing_agent"])
                                                seller_value = selling_valuer.analyze(s_mpi, s_cap, s_de, s_dl, s_hist, s_mark)
                                                print(f"{i}: Valuer Agent completed")

                                                deal_agent = DealAgent(AGENT_SETTINGS["deal_agent"], i)
                                                deal = deal_agent.analyze(buyer_value, seller_value)
                                                log_2 = deal["log"]
                                                print(f"{i}: Deal Agent completed")

                                                assessor = AssessorAgent(AGENT_SETTINGS["assess_agent"], deal)
                                                log_3 = assessor.analyze()
                                                with open(f"assessments\{i}.txt", "w") as file:
                                                    file.write("Arguments:\n")
                                                    file.write(str(argu)+"\n")
                                                    file.write(log_3)
                                                print(f"{i}: Assessor Agent completed")

                                                with open(f"log\{i}.txt", "w") as file:
                                                    file.write("Arguments:\n")
                                                    file.write(str(argu)+"\n")
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
end_time = time.time()
print(f"Time taken: {end_time-start_time}")
print("————————————————————————All experiments completed————————————————————————")


