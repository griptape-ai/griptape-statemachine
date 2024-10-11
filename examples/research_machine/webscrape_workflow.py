from typing import Text
from griptape.structures import Workflow, Agent
from griptape.drivers import DuckDuckGoWebSearchDriver, OpenAiChatPromptDriver, AnthropicPromptDriver, GoogleWebSearchDriver
from griptape.tasks import PromptTask, BaseTask, CodeExecutionTask, ToolkitTask
from griptape.rules import Rule, Ruleset
from griptape.artifacts import BaseArtifact, TextArtifact
from griptape.tools import WebSearchTool
from dotenv import load_dotenv
from griptape.configs import defaults_config
from griptape.configs.drivers import DriversConfig
from griptape.utils import StructureVisualizer
import json
# TODO: Create the different necessary tasks

load_dotenv()
defaults_config.Defaults.drivers_config = DriversConfig(
     prompt_driver = OpenAiChatPromptDriver(model="gpt-4o"),
)
# TODO: Test a different model. 
# defaults_config.Defaults.drivers_config = DriversConfig(
#     prompt_driver = AnthropicPromptDriver(
#     model="claude-3-5-sonnet-20240620",
#      ),
# )

def create_search_task(input:dict, number:str) -> BaseTask:
   #TODO: Pick the websearch!
    web_search_tool = WebSearchTool(
        web_search_driver=web_search_driver,
    )
    task = ToolkitTask(
        f"""Complete a web search using exactly this input as your query. Input='{query}'""",
        tools=[web_search_tool],
        id=f"websearch_{number}",
        parent_ids=["add_searches_task"]
        )
    return task

def create_scrape_task(input:dict) -> BaseTask:
    return PromptTask()

class WebScrapeWorkflow:

    webscrape_workflow:Workflow = Workflow(id="webscrape")


    def __init__(self,urls:list) -> None:
         self.add_webscrape_tasks(urls)
         #self.add_code_execution_task()
         # Can add comparing task at the end! perhaps...

    def search(self) -> str:
        results = self.webscrape_workflow.run()
        #print(StructureVisualizer(structure=self.websearch_workflow).to_url())
        if results.output:
            return results.output.value
        return ""

    def add_webscrape_tasks(self,urls:list) -> None:
        for url in urls:
            self.webscrape_workflow.add_task(PromptTask())

    def add_code_execution_task(self) -> None:
         pass



if __name__ == "__main__":
     urls = []
     agent = WebScrapeWorkflow(urls)
     output = agent.search()

