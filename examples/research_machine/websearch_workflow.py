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
    #TODO: Choose google web search or DuckDuckGo
    # Turn Keywords and context into a query string
    query = ""
    for keyword in input["Keywords"]:
         query += f"'{keyword}' "
    query += input["Context"]
    web_search_driver = DuckDuckGoWebSearchDriver(
        results_count=5, #change later if I want 
    )
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

class WebSearchWorkflow:

    websearch_workflow:Workflow = Workflow(id="websearch")

    def parse_dictionary_and_add_tasks(self, task:CodeExecutionTask)->TextArtifact:
        searches = task.parent_outputs["query_keyword_task"]
        searches = json.loads(searches)
        search_1 = create_search_task(searches["1"],"1")
        search_2 = create_search_task(searches["2"],"2")
        search_3 = create_search_task(searches["3"],"3")
        # Add this combining task..
        next_task = self.get_combining_task()
        task.add_children([search_1,search_2,search_3])
        for child in task.children:
            child.add_child(next_task)
        return TextArtifact("Beginning the search.")

    def __init__(self,information:str) -> None:
         self.add_keywords_task(information)
         self.add_code_execution_task()
         # Can add comparing task at the end! perhaps...

    def search(self) -> str:
        results = self.websearch_workflow.run()
        #print(StructureVisualizer(structure=self.websearch_workflow).to_url())
        if results.output:
            return results.output.value
        return ""

    def add_keywords_task(self,information:str) -> None:
        query_task = PromptTask(
             f"""Select keywords and broader context from the information provided to create three different outputs.
             This is the information provided: {information}""",  # noqa: S608
             rules=[
                  Rule("Keywords should be surrounded by double quotes."),
                  Rule("You are an agent that specializes in creating queries to get the most relevant websearch results."),
                  Rule("Context doesn't need to be surrounded by double quotes."),
                  Rule("Context should be less than or equal to 3 sentences."),
                  Rule("Vary the number of keywords between outputs, with no more than 5 keywords at most."),
                  Rule("Output should be in a json, with each key being a number and each output being the content of the query."),
                  Rule("The query should be a dictionary organized into Keywords and Context."),
                  Rule("No markdown, code snippets, code blocks, or backticks.")

                  # maybe create a rule about length and number of keywords.
                  # is outputting as {1:{"Keywords":[], "Context":str}}
             ],
             id="query_keyword_task")
        self.websearch_workflow.add_task(query_task)

    def add_code_execution_task(self) -> None:
         code_execution_task = CodeExecutionTask(run_fn=self.parse_dictionary_and_add_tasks,parent_ids=["query_keyword_task"],id="add_searches_task")
         self.websearch_workflow.add_task(code_execution_task)

    #TODO: I'm already hardcoding the names in here - is it worth it to not do dynamically adding to the list?
    def get_combining_task(self) -> PromptTask: 
        return PromptTask(
            f"""Using the input from {{{{parent_outputs}}}}, combine them all into a list of website urls.""",
            id="combining_lists",
            rules=[
                Rule("You are an agent that specializes in determining trustworthy and reputable websites."),
                Rule("Only keep the reputable and trustworthy websites from the list."),
                Rule(f"""Only keep the websites that are the most relevant to the search queries {{{{parent_outputs['query_keyword_task']}}}}"""),
                Rule("Return as a list of URLs")
            ],
            parent_ids=["websearch_1","websearch_2","websearch_3"]
        )


if __name__ == "__main__":
     information = "The fast-fashion industry faces increasing pressure to reduce its environmental impact and improve sustainability practices. Fast-fashion retailers struggle to balance consumer demand for trendy, affordable clothing with the need to minimize waste, reduce carbon emissions, and ensure ethical labor practices throughout their supply chains. The industry must find innovative solutions to extend product lifecycles, incorporate recycled materials, and create more transparent and responsible manufacturing processes without significantly increasing costs or compromising style offerings."
     agent = WebSearchWorkflow(information)
     output = agent.search()



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