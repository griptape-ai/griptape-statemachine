from griptape.structures import Workflow, Agent
from griptape.tools import WebScraper,WebSearch
from griptape.drivers import DuckDuckGoWebSearchDriver, OpenAiChatPromptDriver
from griptape.tasks import PromptTask
# TODO: Create the different necessary tasks


class WebSearchAgent:

    websearch_workflow:Workflow = Workflow(prompt_driver=OpenAiChatPromptDriver(model="gpt-4o"),id="websearch")

    def __init__(self,information:str) -> None:

        self.create_keywords_task(information)

    def search(self) -> str:
        results = self.websearch_workflow.run()
        if results.output:
            return results.output.value
        return ""

    def create_keywords_task(self,information:str) -> None:
        #TODO: Create three different queries given the following keywords
        pass


# TODO: Add different tasks:
#First task - determine different
query_key_task = PromptTask("Get the best key")
save_key_task = PromptTask("Save the keys")
web_search_task = PromptTask("Search the web. Going to have the same parent task but use different input")



