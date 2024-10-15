from typing import Text
from attrs import field
from griptape.structures import Workflow, Agent
from griptape.drivers import DuckDuckGoWebSearchDriver, OpenAiChatPromptDriver, AnthropicPromptDriver, GoogleWebSearchDriver
from griptape.tasks import PromptTask, BaseTask, CodeExecutionTask, ToolkitTask
from griptape.rules import Rule, Ruleset
from griptape.artifacts import BaseArtifact, TextArtifact
from dotenv import load_dotenv
from griptape.configs import defaults_config
from griptape.configs.drivers import DriversConfig
from griptape.utils import StructureVisualizer
from griptape.tools import WebScraperTool
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


class WebScrapeWorkflow:

    webscrape_workflow:Workflow = Workflow(id="webscrape")
    information:str = ""
    urls:list = []


    def scrape(self,information:str,urls:list) -> str:
        self.information = information
        self.urls = urls
        self.add_webscrape_tasks(urls)
        self.add_combining_task(len(urls))
        self.format_output()
        results = self.webscrape_workflow.run()
        #print(StructureVisualizer(structure=self.webscrape_workflow).to_url())
        if results.output:
            return results.output.value
        return ""

    def create_scrape_task(self, input:str, number:int) -> BaseTask:
        #TODO: maybe modify the webscrape tool with different configurations
        web_scrape_tool = WebScraperTool()
        return ToolkitTask(
            f"""Complete a web scrape of this URL: {input} and output it in a dictionary with the url as the key.""",
            tools=[web_scrape_tool],
            id=f"webscrape_{number}",
            )

    def add_webscrape_tasks(self,urls:list) -> None:
        i = 1
        for url in urls:
            self.webscrape_workflow.add_task(self.create_scrape_task(url,i))
            i += 1

    def add_combining_task(self,number_of_tasks:int) -> None:
         parent_ids = [f"webscrape_{num}" for num in range(1,number_of_tasks+1)]
         task = PromptTask(
            f"""Given the input from {{{{parent_outputs}}}}, sort by relevancy to the query:{self.information} and combine all of the webscrape information into a json file in this format:
                urls:{{
                    url_value:{{
                        artical_title: x
                        website_title: x
                        url: x
                        summary: x
                        scraped_information: x
                    }}
                }}

            """,
             id="combine_web_scrapes",
             parent_ids=parent_ids,
             rules=[
                 Rule("Do not mix information. Keep all information with the url it was scraped from."),
                 Rule("Return as a json in this format. No backticks, no markdown, no code snippets."),
                 Rule("Use this list of urls : {self.urls} to match the urls to the webscrapes. Keep the full URL.")
             ]
         )
         self.webscrape_workflow.add_task(task)

    def format_output(self) -> None: 
        task = PromptTask(
            f"""Create and format a markdown file with {{{{parent_outputs}}}}""",
            id = "format_output",
            parent_ids=["combine_web_scrapes"],
            rules=[
                Rule("You are an agent that specializes in formatting research to be clear and readable."),
                Rule("Format it in markdown format"),
                Rule("""Format it with:
                     Title
                     url
                     Summary""")
            ]
        )
        self.webscrape_workflow.add_task(task)



if __name__ == "__main__":
     urls = [
    "https://www.unep.org/news-and-stories/story/environmental-costs-fast-fashion",
    "https://www.colorado.edu/ecenter/2023/10/02/how-fast-fashion-impacts-sustainability",
    "https://www.bbc.com/news/science-environment-60382624",
    ]
     info = "The fast-fashion industry faces increasing pressure to reduce its environmental impact and improve sustainability practices. Fast-fashion retailers struggle to balance consumer demand for trendy, affordable clothing with the need to minimize waste, reduce carbon emissions, and ensure ethical labor practices throughout their supply chains. The industry must find innovative solutions to extend product lifecycles, incorporate recycled materials, and create more transparent and responsible manufacturing processes without significantly increasing costs or compromising style offerings."
     agent = WebScrapeWorkflow()
     output = agent.scrape(info, urls)

