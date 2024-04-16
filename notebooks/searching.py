# I've been using this when I want to poke around the guts of a particular
# search engine

# %%
# %load_ext autoreload
# %autoreload 2
import os

from statschat import load_config
from statschat.generative.llm import Inquirer

# %%
os.chdir("..")  # to reload saved embedding DB

# %%
# %%
CONFIG = load_config(name="main")
params = {**CONFIG["db"], **CONFIG["search"]}
params["generative_model_name"] = "gemini-pro"

# %%
searcher = Inquirer(**params)

# %%
docs = searcher.similarity_search(
    query="how many people watched the coronation?", return_dicts=True
)
docs

# %%
res = searcher.query_texts(
    query="how many people watched the coronation?", docs=docs[:3]
)
res

# %%
qs = [
    "how many people watched the coronation?",
    "what is UK population?",
    "What is the latest rate of CPIH inflation?",
    "What is GDP value?",
    "How many people died in March 2023?",
]

# %%
for q in qs:
    _, _, response = searcher.make_query(q)
    print(q, response)
# %%
