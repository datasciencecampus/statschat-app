# this script is to be run when docker image is constructed so that the required models
# would be included in the image and don't need to be downloaded on each instance start

from statschat import load_config
from statschat.generative.llm import Inquirer

try:
    CONFIG = load_config(name="main")
    params = {**CONFIG["db"], **CONFIG["search"]}
    inquirer = Inquirer(**params)
except Exception as e:
    print(e)
    inquirer = None
