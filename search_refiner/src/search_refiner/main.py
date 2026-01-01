import asyncio
import sys
from pathlib import Path

from flatagents import FlatMachine


async def run(query: str):
    """Search web and refine results to key findings."""
    machine_file = Path(__file__).parent.parent.parent / 'machine.yml'
    machine = FlatMachine(config_file=str(machine_file))

    result = await machine.execute(input={"query": query})

    if "summary" in result:
        print(result["summary"])
    elif "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(result)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "latest developments in AI agents"
    asyncio.run(run(query))
