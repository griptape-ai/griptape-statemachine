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
# TODO: Create the different necessary tasks

load_dotenv()
defaults_config.Defaults.drivers_config = DriversConfig(
     prompt_driver = OpenAiChatPromptDriver(model="gpt-4o"),
)
# defaults_config.Defaults.drivers_config = DriversConfig(
#     prompt_driver = AnthropicPromptDriver(
#     model="claude-3-5-sonnet-20240620",
#      ),
# )

def create_search_task(input:dict, number:str) -> BaseTask:
    #TODO: Choose google web search or DuckDuckGo
    # Turn Keywords and context into a query string
    query = ""
    for keyword in input["Keywords"]:
         query += f"'{keyword}' "
    query += input["Context"]
    web_search_driver = DuckDuckGoWebSearchDriver(
        results_count=7, #change later if I want 
    )
    web_search_tool = WebSearchTool(
        web_search_driver=web_search_driver,
    )
    task = ToolkitTask(
        f"""Complete a web search using this as your query: {query}""",
        tools=[web_search_tool],
        id=f"websearch_{number}",
        parent_ids=["add_searches_task"]
        )
    return task

def create_scrape_task(input:dict) -> BaseTask:
    return PromptTask()

class WebSearchAgent:

    websearch_workflow:Workflow = Workflow(id="websearch")

    def parse_dictionary_and_add_tasks(self, task:CodeExecutionTask)->TextArtifact:
        searches = task.parent_outputs["query_keyword_task"]
        if type(searches) is dict :
             search_1 = create_search_task(searches[1],"1")
             search_2 = create_search_task(searches[2],"2")
             search_3 = create_search_task(searches[3],"3")
             task.add_child(search_1)
             self.websearch_workflow.insert_task(parent_tasks=[task],task=search_1,child_tasks=[])
             self.websearch_workflow.add_tasks(search_1,search_2,search_3)
        return TextArtifact(task.parent_outputs["query_keyword_task"])

    def __init__(self,information:str) -> None:
         self.add_keywords_task(information)
         self.add_code_execution_task()
         # Can add comparing task at the end! perhaps...

    def search(self) -> str:
        results = self.websearch_workflow.run()
        print(StructureVisualizer(structure=self.websearch_workflow).to_url())
        if results.output:
            return results.output.value
        return ""

    def add_keywords_task(self,information:str) -> None:
        #TODO: Create three different queries given the following keywords
        query_task = PromptTask(
             f"""Select keywords and broader context from the information provided to create three different outputs.
             This is the information provided: {information}""",  # noqa: S608
             rules=[
                  Rule("Keywords should be surrounded by double quotes."),
                  Rule("Context doesn't need to be surrounded by double quotes."),
                  Rule("Context should be less than or equal to 3 sentences."),
                  Rule("Vary the number of keywords between outputs, with no more than 5 keywords at most."),
                  Rule("Output should be in a dictionary, with each key being a number and each output being the content of the query.")
                  # maybe create a rule about length and number of keywords.
                  # is outputting as {1:{"Keywords":[], "Context":str}}
             ],
             id="query_keyword_task")
        self.websearch_workflow.add_task(query_task)

    def add_code_execution_task(self) -> None:
         code_execution_task = CodeExecutionTask(run_fn=self.parse_dictionary_and_add_tasks,parent_ids=["query_keyword_task"],id="add_searches_task")
         self.websearch_workflow.add_task(code_execution_task)
         # TODO: add three code execution tasks, one for each of the keywords!



    # TODO: Add different tasks:
    #First task - determine different
    web_search_task = PromptTask("Search the web. Going to have the same parent task but use different input")



if __name__ == "__main__":
     information = "The fast-fashion industry faces increasing pressure to reduce its environmental impact and improve sustainability practices. Fast-fashion retailers struggle to balance consumer demand for trendy, affordable clothing with the need to minimize waste, reduce carbon emissions, and ensure ethical labor practices throughout their supply chains. The industry must find innovative solutions to extend product lifecycles, incorporate recycled materials, and create more transparent and responsible manufacturing processes without significantly increasing costs or compromising style offerings."
     agent = WebSearchAgent(information)
     output = agent.search()
     print(output)



#  web_search_driver = GoogleWebSearchDriver(
    #       results_count=7, #change if I want 
    #       language="en",
    #       country="us",
    #       api_key="GOOGLE_API_KEY",
    #       search_id="GOOGLE_API_SEARCH_ID"
    #  )
    # extra_schema_properties={
    #         "search":{
    #             schema.Literal(
    #                     "exactTerms",
    #             )
    #         }
    #         }