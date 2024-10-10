from __future__ import annotations

from typing import TYPE_CHECKING

from griptape_statemachine.machines.base_machine import BaseMachine

if TYPE_CHECKING:
    from griptape.tools import BaseTool


class LighthouseMachine(BaseMachine):
    """State machine for StartStak Lighthouse."""

    @property
    def tools(self) -> dict[str, BaseTool]:
        return {}

    def start_machine(self) -> None:
        """Starts the machine."""
        self.send("next_state")

    def on_enter_keywords(self) -> None:
        """Pulls information from the founder summary. Sorts into words that need to be directly present, and larger context.
        This can start as one file with all of the information, and slowly narrow itself down until it reaches a good solution.
        """

    def on_event_keywords(self, _event) -> None:
        """
        Several different types of events. Can we send events to keywords from websearch and webscrape? I think it's possible.
        Websearch is where it's critical to get the right websites, but it's hard to say which websites are accurate without a webscrape.
        Agents necessary:
        - Websearch expert agent - Is an expert at picking out keywords for websearches
            - You're taking a bunch of information and either cutting it down to 75% or increasing it by 10%
        - Auditor agent:
            - When has this been refined to be the best it can be? should this come from another source? Can websearch or webscrape send events to keywords?
        """

    def on_exit_keywords(self) -> None:
        """Finalize and format the information that we've decided is good - for now!
        store this in an artifact. Each time the artifact will move to a different set. Will keep previous information and current information.
        """

    def on_enter_websearch(self) -> None:
        """This step will peform the first websearch.
        - Websearch agent (performs the websearch)
        - Reputable agent
            - Filters through the websearch for reputable results. Knows what makes a website reputable and not a blog etc.
        - Relevancy agent
            - Takes the keywords search and picks the most relevant results
            - The searches with the most keywords?
        """

    def on_event_websearch(self, _event) -> None:
        pass

    def on_enter_webscrape(self) -> None:
        """
        - Relevancy agent
            - Takes the keywords search and compare it - how relevant is the information to the search?
        """
