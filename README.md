```markdown
# opencoder

## Overview

`opencoder` is a project designed to interface with OpenAI's client and SDK, providing functionalities similar to ClaudeCoder, enriched with OpenRouter and Helicone integration.

## Project Structure

```
opencoder/
│
├── .env                  # Environment variables file
├── .git                  # Git repository metadata
│   ├── ...
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License for the project
├── README.md             # Project overview and instructions
├── __pycache__           # Compiled Python files
├── api/                  # API-related implementation
│   ├── __init__.py
│   ├── agent.py          # Agent definition
│   ├── agent_runner.py   # Handles agent execution
│   ├── context.py        # Context management for the agent
│   └── context_handler.py # Provides access to the context
├── load_client.py        # Client loader for OpenAI API
├── main.py               # Main execution script
└── tools.py              # Utility functions and tools
```

## Installation

To use `opencoder`, ensure you have Python 3.7 or higher installed. Clone the repository and install required dependencies using:

```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory.
2. Add your API keys:

   ```plaintext
   OPENROUTER_API_KEY=your_openrouter_api_key
   HELICONE_API_KEY=your_helicone_api_key
   ```

## Usage

Run the main script to start chatting with the agent:

```bash
python main.py
```

The agent will prompt you for input, and you can ask for file management tasks or coding inquiries.

## API Structure

### Agent

- **`get_agent(tools, selected_model)`**: Returns a configured agent instance.

### Agent Runner

- **`AgentRunner(agent, context)`**: Initializes an agent runner with a specified agent and context for state management.
    - **`run(input)`**: Executes the agent with provided input, returning the final output.

### Context

- **`Context()`**: Maintains the state of conversation and files.
    - **Methods**:
        - `add_user_message(message)`: Adds a user message to the context.
        - `add_system_message(message)`: Records the system's response.
        - `add_file(filename, content)`: Saves a file in the context.
        - `rename_file(old_filename, new_filename)`: Renames a file in the context.
        - `delete_file(filename)`: Removes a file from the context.

### Tools

The project includes several tools that enhance the capabilities of the agent:

- **ShellExec**: Executes shell commands and returns the output.
- **CreateFile**: Creates a new file with specified content.
- **DeleteFile**: Deletes a specified file.
- **ReadFile**: Reads and returns the content of a file.
- **WriteFile**: Writes content to an existing file.
- **RenameAndMoveFile**: Moves and/or renames files.
- **CreateFolder**: Creates a new directory.
- **GetTree**: Provides a hierarchical view of files in a directory.

## Logging

The project uses Python's logging module to log errors and important information throughout execution. Adjust logging levels as needed.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Commit and push your changes.
5. Create a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```

This documentation includes information about the project structure, installation, usage, API methods, tools, logging, contribution guidelines, and licensing, aiming to provide a thorough overview for developers and users alike.