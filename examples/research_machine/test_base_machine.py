from __future__ import annotations

import json
import logging
from abc import abstractmethod
from re import search
from typing import TYPE_CHECKING, cast

from griptape.drivers import OpenAiChatPromptDriver, GoogleWebSearchDriver
from griptape.events import BaseEvent, EventBus, EventListener, FinishStructureRunEvent
from griptape.rules import Rule, Ruleset
from griptape.structures import Agent
from griptape.tools import WebScraper, WebSearch
from griptape.utils import dict_merge
from statemachine import State, StateMachine
from statemachine.factory import StateMachineMetaclass
from research_machine.webscrape_workflow import WebScrapeWorkflow
from research_machine.webscrape_workflow import WebSearchWorkflow


from griptape_statemachine.parsers import ConfigParser

logger = logging.getLogger(__name__)
logging.getLogger("griptape").setLevel(logging.ERROR)

if TYPE_CHECKING:
    from pathlib import Path

    from griptape.structures import Structure
    from griptape.tools import BaseTool
    from statemachine.event import Event


class BaseMachine(StateMachine):
    """Base class for a machine.


    Attributes:
        config_file (str): The path to the configuration file.
        config (dict): The configuration data.
        gradio_outputs (list[str]): Outputs to render to gradio.
    """

    def __init__(self, config_file: str, **kwargs) -> None:
        self.config_parser = ConfigParser(Path(config_file))
        self.current_organization: str = str(kwargs.get("current_organization"))
        self.current_user: str = str(kwargs.get("current_user"))
        self.config = self.config_parser.parse()
        self.last_user_input: str | None = None
        self.gradio_outputs: list[str] = []

        self._structures: dict[str, Agent] = {}

        def on_event(event: BaseEvent) -> None:
            print(f"Received Griptape event: {json.dumps(event.to_dict(), indent=2)}")
            self.send(
                "send_event",
                event_={"type": "griptape_event", "value": event.to_dict()},
            )

        EventBus.add_event_listener(
            EventListener(on_event, event_types=[FinishStructureRunEvent])
        )

        internal_state = self.file_manager.get_user_state(
            self.current_organization, self.current_user
        )

        super().__init__(start_value=internal_state["state"])

    @property
    def available_events(self) -> list[str]:
        return self.current_state.transitions.unique_events

    @property
    def step_state(self) -> dict:
        return self.file_manager.get_step_state(
            self._current_user_progress["module"],
            self._current_user_progress["step"],
            self.current_organization,
        )

    @step_state.setter
    def step_state(self, state: dict) -> None:
        self.file_manager.update_step_state(
            self._current_user_progress["module"],
            self._current_user_progress["step"],
            state,
            self.current_organization,
        )

    @property
    @abstractmethod
    def tools(self) -> dict[str, BaseTool]:
        """Returns the Tools for the machine."""
        ...

    @property
    def _current_state_config(self) -> dict:
        return self.config["states"][self.current_state_value]

    @classmethod
    def from_definition(cls, definition: dict, **extra_kwargs) -> BaseMachine:
        """
        Creates a StateMachine class from a dictionary definition, using the StateMachineMetaclass metaclass.
        It maps the definition to the StateMachineMetaclass parameters and then creates the class.

        Example usage with a traffic light machine:

        >>> machine = BaseMachine.from_definition(
        ...     "TrafficLightMachine",
        ...     {
        ...         "states": {
        ...             "green": {"initial": True},
        ...             "yellow": {},
        ...             "red": {},
        ...         },
        ...         "events": {
        ...             "transitions": [
        ...                 {"from": "green", "to": "yellow"},
        ...                 {"from": "yellow", "to": "red"},
        ...                 {"from": "red", "to": "green"},
        ...             ]
        ...         },
        ...     }
        ... )

        """

        states_instances = {
            state_id: State(**state_kwargs, value=state_id)
            for state_id, state_kwargs in definition["states"].items()
        }

        events = {}
        for event_name, transitions in definition["events"].items():
            for transition_data in transitions:
                source = states_instances[transition_data["from"]]
                target = states_instances[transition_data["to"]]

                transition = source.to(
                    target,
                    event=event_name,
                    cond=transition_data.get("cond"),
                    unless=transition_data.get("unless"),
                    on=transition_data.get("on"),
                    internal=transition_data.get("internal"),
                )

                if event_name in events:
                    events[event_name] |= transition
                else:
                    events[event_name] = transition

        attrs_mapper = {**extra_kwargs, **states_instances, **events}

        return cast(
            BaseMachine,
            StateMachineMetaclass(cls.__name__, (cls,), attrs_mapper)(**extra_kwargs),
        )

    @classmethod
    def from_config_file(
        cls,
        config_file: str,
        current_organization: Path,
        current_user: Path,
        **extra_kwargs,
    ) -> BaseMachine:
        """Creates a StateMachine class from a configuration file."""
        config_parser = ConfigParser(Path(config_file))
        config = config_parser.parse()
        extra_kwargs["config_file"] = config_file
        extra_kwargs["current_organization"] = current_organization
        extra_kwargs["current_user"] = current_user

        definition_states = {
            state_id: {
                "initial": state_value.get("initial", False),
                "final": state_value.get("final", False),
            }
            for state_id, state_value in config["states"].items()
        }
        definition_events = {
            event_name: list(event_value["transitions"])
            for event_name, event_value in config["events"].items()
        }
        definition = {"states": definition_states, "events": definition_events}

        return cls.from_definition(definition, **extra_kwargs)

    @abstractmethod
    def start_machine(self) -> None:
        """Starts the machine."""
        ...

    def reset_structures(self) -> None:
        """Resets the structures."""
        self._structures = {}

    def on_enter_state(self, source: State, state: State, event: Event) -> None:
        print(f"Transitioning from {source} to {state} with event {event}")

    def get_structure(self, structure_id: str) -> Structure:
        global_structure_config = self.config["structures"][structure_id]
        state_structure_config = self._current_state_config.get("structures", {}).get(
            structure_id, {}
        )
        structure_config = dict_merge(global_structure_config, state_structure_config)

        if structure_id not in self._structures:
            # Initialize Structure with all the expensive setup
            # TODO: Is this something we could replace with assistants?
            if "websearch" in structure_id.lower():
                # TODO: Input API key and search id
                structure = WebSearchWorkflow()
            elif "webscrape" in structure_id.lower():
                # TODO: Create the webscrape tool
                # Uses TrafilaturaWebScraperDriver as its base driver.
                # Can change this and can change text chunking
                structure = WebScrapeWorkflow()
            else:
                structure = Agent(
                    id=structure_id,
                    prompt_driver=OpenAiChatPromptDriver(
                        model=structure_config.get("model", "gpt-4o"),
                    ),
                )

            self._structures[structure_id] = structure

        # Create a new clone with state-specific stuff
        # TODO: Do I need to modify for the webscrape because does it want rules... i can also give it no rules in teh config.yaml
        structure = self._structures[structure_id]
        structure = Agent(
            id=structure.id,
            prompt_driver=structure.prompt_driver,
            conversation_memory=structure.conversation_memory,
            # Including the websearch or webscrape information
            tools=structure.tools,
            rulesets=[
                *self._get_structure_rulesets(structure_config.get("ruleset_ids", [])),
                *self._get_structure_artifacts(
                    structure_config.get("artifact_ids", [])
                ),
            ],
        )
        print(f"Structure: {structure_id}")
        for ruleset in structure.rulesets:
            for rule in ruleset.rules:
                print(f"Rule: {rule.value}")
        return structure

    def _get_structure_rulesets(self, ruleset_ids: list[str]) -> list[Ruleset]:
        ruleset_configs = [
            self.config["rulesets"][ruleset_id] for ruleset_id in ruleset_ids
        ]

        # Convert ruleset configs to Rulesets
        return [
            Ruleset(
                name=ruleset_config["name"],
                rules=[Rule(rule) for rule in ruleset_config["rules"]],
            )
            for ruleset_config in ruleset_configs
        ]

    def _get_structure_artifacts(self, artifact_ids: list[str]) -> list[Ruleset]:
        artifact_configs = {
            artifact_id: self.config["artifacts"][artifact_id]
            for artifact_id in artifact_ids
        }

        artifacts = {}
        for artifact_id, artifact_config in artifact_configs.items():
            artifact_level = artifact_config["level"]
            waterline = artifact_config["waterline"]
            artifact_data = self.file_manager.get_artifact(
                self.config, artifact_id, self.current_organization, self.current_user
            )

            if artifact_level not in artifacts:
                artifacts[artifact_level] = {}
            if waterline not in artifacts[artifact_level]:
                artifacts[artifact_level][waterline] = []
            artifacts[artifact_level][waterline].append(artifact_data)

        rulesets = []
        if artifacts:
            val = (
                "Here are Artifacts for the organization and specific founder you're talking to."
                '"Above Waterline" artifacts are those that are public information.'
                '"Below Waterline" artifacts are those that are private information and should only be used for your own understanding.'
                f"{json.dumps(artifacts, indent=2)}"
            )
            rulesets = [
                Ruleset(
                    name="Artifact",
                    rules=[Rule(val)],
                )
            ]
        else:
            rulesets = []

        return rulesets
