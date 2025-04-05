# api/agent_runner.py
from agents import Runner
from .context import Context

class AgentRunner():
    def __init__(self, agent, context: Context):
        self.agent = agent
        self.context = context

    async def run(self, input) -> str:
        self.context.add_user_message(input)
        response = await Runner.run(starting_agent=self.agent, input=self.context.serialize())
        final_output = response.final_output.strip()
        self.context.add_system_message(final_output)
        return final_output