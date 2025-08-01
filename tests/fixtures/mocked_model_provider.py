import json
from typing import Any, AsyncGenerator, Iterable, Optional, Type, TypeVar

from pydantic import BaseModel

from strands.types.content import Message, Messages
from strands.types.event_loop import StopReason
from strands.types.models.model import Model
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec

T = TypeVar("T", bound=BaseModel)


class MockedModelProvider(Model):
    """A mock implementation of the Model interface for testing purposes.

    This class simulates a model provider by returning pre-defined agent responses
    in sequence. It implements the Model interface methods and provides functionality
    to stream mock responses as events.
    """

    def __init__(self, agent_responses: Messages):
        self.agent_responses = agent_responses
        self.index = 0

    def format_chunk(self, event: Any) -> StreamEvent:
        return event

    def format_request(
        self, messages: Messages, tool_specs: Optional[list[ToolSpec]] = None, system_prompt: Optional[str] = None
    ) -> Any:
        return None

    def get_config(self) -> Any:
        pass

    def update_config(self, **model_config: Any) -> None:
        pass

    async def structured_output(
        self,
        output_model: Type[T],
        prompt: Messages,
    ) -> AsyncGenerator[Any, None]:
        pass

    async def stream(self, request: Any) -> AsyncGenerator[Any, None]:
        events = self.map_agent_message_to_events(self.agent_responses[self.index])
        for event in events:
            yield event

        self.index += 1

    def map_agent_message_to_events(self, agent_message: Message) -> Iterable[dict[str, Any]]:
        stop_reason: StopReason = "end_turn"
        yield {"messageStart": {"role": "assistant"}}
        for content in agent_message["content"]:
            if "text" in content:
                yield {"contentBlockStart": {"start": {}}}
                yield {"contentBlockDelta": {"delta": {"text": content["text"]}}}
                yield {"contentBlockStop": {}}
            if "toolUse" in content:
                stop_reason = "tool_use"
                yield {
                    "contentBlockStart": {
                        "start": {
                            "toolUse": {
                                "name": content["toolUse"]["name"],
                                "toolUseId": content["toolUse"]["toolUseId"],
                            }
                        }
                    }
                }
                yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(content["toolUse"]["input"])}}}}
                yield {"contentBlockStop": {}}

        yield {"messageStop": {"stopReason": stop_reason}}
