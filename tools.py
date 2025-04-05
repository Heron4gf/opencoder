# tools.py

import os
import os.path # Explicit import for clarity
import logging
import subprocess
from agents import function_tool
from api.context_handler import get_context # Assuming this context handler exists and works

logger = logging.getLogger(__name__)

# --- Configuration ---
SHELL_TIMEOUT = 60 # Increased timeout slightly
TODO_FILENAME = "todo.md" # Define as constant

# --- Console Formatting ---
GREEN_PREFIX = "\033[92m"
YELLOW_PREFIX = "\033[93m" # Added for warnings/non-critical info
RED_PREFIX = "\033[91m"
RESET_COLOR = "\033[0m"

# --- Helper Functions ---

def announce_execution_output(tool_name: str, execution_details: str, status: str, output: str):
    """Announces the result of a tool execution to context and console."""
    prefix = GREEN_PREFIX if status == "success" else RED_PREFIX
    console_output = f"{prefix}{tool_name}: {RESET_COLOR}{execution_details} -> {status.upper()}"
    if output and status != "success": # Only show output details on console for errors
        console_output += f"\n{YELLOW_PREFIX}Output: {RESET_COLOR}{output}"
    elif status == "success" and output and output not in ["successful", "successful, tree updated", "File content appended into the chat history"]:
         # Optionally show non-generic success output
         console_output += f"\n{YELLOW_PREFIX}Output: {RESET_COLOR}{output}"

    print(console_output)

    # Add concise info to agent context
    context_message = f"Tool: {tool_name}\nAction: {execution_details}\nStatus: {status}\nOutput: {output}"
    get_context().add_system_message(context_message)

def get_parent_dir(filepath: str) -> str:
    """Safely gets the parent directory of a path."""
    return os.path.dirname(os.path.abspath(filepath))

def _build_tree(root: str, prefix: str = "") -> str:
    """Recursive helper to build the directory tree string."""
    tree = ""
    try:
        # Sort entries, directories first, then files
        entries = sorted(os.listdir(root), key=lambda x: (not os.path.isdir(os.path.join(root, x)), x.lower()))
    except OSError as e:
        # Handle cases where listing is not possible (e.g., permissions) early
        return f"{prefix}└── [Error listing directory: {e.strerror}]\n"

    for index, entry in enumerate(entries):
        path = os.path.join(root, entry)
        connector = "└── " if index == len(entries) - 1 else "├── "
        tree += f"{prefix}{connector}{entry}\n"
        if os.path.isdir(path):
            # Check for recursion depth or other limits if necessary
            new_prefix = prefix + ("    " if index == len(entries) - 1 else "│   ")
            tree += _build_tree(path, new_prefix) # Recursive call
    return tree

def get_and_update_tree(target_path: str) -> str:
    """
    Generates a directory tree string starting from target_path.
    Updates the context with the generated tree.
    Handles cases where the path is not a valid directory.
    """
    abs_path = os.path.abspath(target_path)
    tool_name = "GetTree (Helper)"
    action_details = f"Generate tree for '{target_path}'"

    if not os.path.exists(abs_path):
        error_msg = f"Error: Path does not exist: '{target_path}'"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    if not os.path.isdir(abs_path):
        error_msg = f"Error: Path is not a directory: '{target_path}'"
        # This specifically addresses the original NotADirectoryError source
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

    try:
        tree_str = f"{os.path.basename(abs_path)}\n" # Start with the root folder name
        tree_str += _build_tree(abs_path)
        get_context().add_file(f"tree_of_{os.path.basename(abs_path)}", tree_str)
        # Announce is usually done by the calling tool, but could announce here if needed
        # announce_execution_output(tool_name, action_details, "success", "Tree generated and added to context")
        return tree_str
    except OSError as e:
        logger.exception(f"Error building tree for '{target_path}':")
        error_msg = f"Error generating tree for '{target_path}': {e.strerror}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except Exception as e:
        logger.exception(f"Unexpected error building tree for '{target_path}':")
        error_msg = f"Error: Unexpected error generating tree for '{target_path}': {str(e)}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

def _write_to_file_internal(filepath: str, content: str) -> bool:
    """Internal helper to write content to a file. Returns True on success, False on error."""
    abs_filepath = os.path.abspath(filepath)
    parent_dir = get_parent_dir(abs_filepath)
    try:
        # Ensure parent directory exists
        if not os.path.exists(parent_dir):
             os.makedirs(parent_dir, exist_ok=True) # exist_ok=True prevents error if dir already exists
             logger.info(f"Created directory: {parent_dir}")

        with open(abs_filepath, "w", encoding='utf-8') as f: # Use utf-8 encoding
            f.write(content)
        get_context().add_file(filepath, content) # Update context on successful write
        return True
    except (OSError, IOError) as e: # Catch file system related errors
        logger.exception(f"Error writing file '{filepath}':")
        # Don't announce here, let the caller handle it
        return False
    except Exception as e:
        logger.exception(f"Unexpected error writing file '{filepath}':")
        return False

# --- Tool Functions ---

@function_tool
def ShellExec(command: str) -> str:
    """
    Executes one or more shell commands separated by newlines or semicolons.

    Args:
        command: The shell command(s) to execute.

    Returns:
        A string containing the results of each command execution, including stdout or stderr.
        Returns an error message if the execution fails.
    """
    results = []
    tool_name = "ShellExec"
    action_details = f"Execute shell command(s)"
    try:
        # Split the input command string into individual commands
        commands = [cmd.strip() for line in command.splitlines() for cmd in line.split(';') if cmd.strip()]
        if not commands:
            return "Error: No valid command provided."

        for i, cmd in enumerate(commands):
            cmd_details = f"Executing command ({i+1}/{len(commands)}): '{cmd}'"
            output = ""
            status = "error" # Default to error
            try:
                result = subprocess.run(
                    cmd,
                    shell=True, # Be cautious with shell=True due to security risks if command is user-influenced
                    capture_output=True,
                    text=True,
                    encoding='utf-8', # Be explicit about encoding
                    timeout=SHELL_TIMEOUT,
                    check=False # Don't raise exception on non-zero exit code, handle manually
                )
                if result.returncode == 0:
                    output = result.stdout.strip() if result.stdout else "[No standard output]"
                    status = "success"
                    announce_execution_output(tool_name, cmd_details, status, output)
                else:
                    output = result.stderr.strip() if result.stderr else f"[No standard error, exit code: {result.returncode}]"
                    announce_execution_output(tool_name, cmd_details, status, output)

            except subprocess.TimeoutExpired:
                output = f"Error: Command '{cmd}' timed out after {SHELL_TIMEOUT} seconds."
                announce_execution_output(tool_name, cmd_details, status, output)
            except FileNotFoundError: # Often happens if the command itself isn't found
                 output = f"Error: Command not found: '{cmd.split()[0]}'"
                 announce_execution_output(tool_name, cmd_details, status, output)
            except Exception as e:
                logger.exception(f"Exception during shell command '{cmd}':")
                output = f"Error: Exception occurred executing '{cmd}': {str(e)}"
                announce_execution_output(tool_name, cmd_details, status, output)

            results.append(f"Command: {cmd}\nStatus: {status.upper()}\nOutput:\n{output}")

        return "\n\n".join(results)

    except Exception as e:
        # Catch errors in command parsing itself
        logger.exception("Outer ShellExec error:")
        error_msg = f"Error: Failed to parse or prepare commands: {str(e)}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

@function_tool
def DeleteFile(filepath: str) -> str:
    """
    Deletes the specified file.

    Args:
        filepath: The path to the file to delete.

    Returns:
        A success message or an error message string.
    """
    tool_name = "DeleteFile"
    action_details = f"Delete file: '{filepath}'"
    abs_filepath = os.path.abspath(filepath)
    parent_dir = get_parent_dir(abs_filepath)

    try:
        if not os.path.exists(abs_filepath):
             error_msg = f"Error: File not found: '{filepath}'"
             announce_execution_output(tool_name, action_details, "error", error_msg)
             return error_msg
        if os.path.isdir(abs_filepath):
             error_msg = f"Error: Path is a directory, not a file: '{filepath}'"
             announce_execution_output(tool_name, action_details, "error", error_msg)
             return error_msg

        os.remove(abs_filepath)
        get_context().delete_file(filepath) # Update context
        get_and_update_tree(parent_dir) # Update tree of the PARENT directory
        success_msg = f"File deleted successfully: '{filepath}'"
        announce_execution_output(tool_name, action_details, "success", "successful, tree updated")
        return success_msg
    except PermissionError as e:
        logger.warning(f"Permission error deleting file '{filepath}': {e}")
        error_msg = f"Error: Permission denied deleting file: '{filepath}'"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except OSError as e:
        logger.exception(f"OS error deleting file '{filepath}':")
        error_msg = f"Error deleting file '{filepath}': {e.strerror}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except Exception as e:
        logger.exception(f"Unexpected error deleting file '{filepath}':")
        error_msg = f"Error: Unexpected error deleting file '{filepath}': {str(e)}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

@function_tool
def ReadFile(filepath: str) -> str:
    """
    Reads the content of the specified file.

    Args:
        filepath: The path to the file to read.

    Returns:
        The content of the file as a string, or an error message string.
    """
    tool_name = "ReadFile"
    action_details = f"Read file: '{filepath}'"
    abs_filepath = os.path.abspath(filepath)

    try:
        if not os.path.exists(abs_filepath):
             error_msg = f"Error: File not found: '{filepath}'"
             announce_execution_output(tool_name, action_details, "error", error_msg)
             return error_msg
        if os.path.isdir(abs_filepath):
             error_msg = f"Error: Path is a directory, not a file: '{filepath}'"
             announce_execution_output(tool_name, action_details, "error", error_msg)
             return error_msg

        with open(abs_filepath, "r", encoding='utf-8') as f: # Specify encoding
            content = f.read()
        get_context().add_file(filepath, content) # Add to context AFTER successful read
        announce_execution_output(tool_name, action_details, "success", "File content read and added to context")
        return content # Return the actual content
    except PermissionError as e:
        logger.warning(f"Permission error reading file '{filepath}': {e}")
        error_msg = f"Error: Permission denied reading file: '{filepath}'"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except (OSError, IOError) as e:
        logger.exception(f"Error reading file '{filepath}':")
        error_msg = f"Error reading file '{filepath}': {e.strerror}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except Exception as e:
        logger.exception(f"Unexpected error reading file '{filepath}':")
        error_msg = f"Error: Unexpected error reading file '{filepath}': {str(e)}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

@function_tool
def WriteAndCreateFile(filepath: str, content: str) -> str:
    """
    Writes content to a file, creating the file and any necessary directories if they don't exist.
    Overwrites the file if it already exists.

    Args:
        filepath: The path to the file to write.
        content: The string content to write to the file.

    Returns:
        A success message or an error message string.
    """
    tool_name = "WriteAndCreateFile"
    action_details = f"Write to file: '{filepath}'"
    abs_filepath = os.path.abspath(filepath)
    parent_dir = get_parent_dir(abs_filepath)

    if _write_to_file_internal(abs_filepath, content):
        get_and_update_tree(parent_dir) # Update tree of the PARENT directory
        success_msg = f"File written successfully: '{filepath}'"
        announce_execution_output(tool_name, action_details, "success", "successful, tree updated")
        return success_msg
    else:
        # Error details are logged and printed by _write_to_file_internal or its callees
        error_msg = f"Error: Failed to write to file '{filepath}'. Check logs for details."
        # Announce failure here as the internal function doesn't
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg # Return generic error, specific logged already

@function_tool
def RenameAndMoveFile(source_path: str, dest_path: str) -> str:
    """
    Renames or moves a file or directory from source_path to dest_path.

    Args:
        source_path: The current path of the file or directory.
        dest_path: The new path for the file or directory.

    Returns:
        A success message or an error message string.
    """
    tool_name = "RenameAndMoveFile"
    action_details = f"Move '{source_path}' to '{dest_path}'"
    abs_source = os.path.abspath(source_path)
    abs_dest = os.path.abspath(dest_path)
    source_parent_dir = get_parent_dir(abs_source)
    dest_parent_dir = get_parent_dir(abs_dest)

    try:
        if not os.path.exists(abs_source):
            error_msg = f"Error: Source path not found: '{source_path}'"
            announce_execution_output(tool_name, action_details, "error", error_msg)
            return error_msg

        # Ensure destination directory exists before moving
        if not os.path.exists(dest_parent_dir):
             os.makedirs(dest_parent_dir, exist_ok=True)
             logger.info(f"Created directory: {dest_parent_dir}")

        os.rename(abs_source, abs_dest)
        get_context().rename_file(source_path, dest_path) # Update context

        # Update trees of both source and destination parent directories if they differ
        get_and_update_tree(source_parent_dir)
        if source_parent_dir != dest_parent_dir:
            get_and_update_tree(dest_parent_dir)

        success_msg = f"Moved successfully from '{source_path}' to '{dest_path}'"
        announce_execution_output(tool_name, action_details, "success", "successful, tree(s) updated")
        return success_msg
    except PermissionError as e:
        logger.warning(f"Permission error moving '{source_path}' to '{dest_path}': {e}")
        error_msg = f"Error: Permission denied moving '{source_path}' to '{dest_path}'"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except FileExistsError:
         error_msg = f"Error: Destination path already exists: '{dest_path}'"
         announce_execution_output(tool_name, action_details, "error", error_msg)
         return error_msg
    except OSError as e:
        logger.exception(f"OS error moving '{source_path}' to '{dest_path}':")
        error_msg = f"Error moving '{source_path}' to '{dest_path}': {e.strerror}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except Exception as e:
        logger.exception(f"Unexpected error moving '{source_path}' to '{dest_path}':")
        error_msg = f"Error: Unexpected error moving '{source_path}': {str(e)}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

@function_tool
def CreateFolder(folder_path: str) -> str:
    """
    Creates a new directory, including any necessary parent directories.

    Args:
        folder_path: The path of the directory to create.

    Returns:
        A success message or an error message string (e.g., if it already exists).
    """
    tool_name = "CreateFolder"
    action_details = f"Create folder: '{folder_path}'"
    abs_folder_path = os.path.abspath(folder_path)
    parent_dir = get_parent_dir(abs_folder_path)

    try:
        if os.path.exists(abs_folder_path):
            if os.path.isdir(abs_folder_path):
                # Considered a non-error, maybe just inform?
                info_msg = f"Folder already exists: '{folder_path}'"
                announce_execution_output(tool_name, action_details, "success", info_msg) # Report as success but mention existence
                return info_msg
            else:
                # Path exists but is a file
                error_msg = f"Error: Path exists but is a file, not a folder: '{folder_path}'"
                announce_execution_output(tool_name, action_details, "error", error_msg)
                return error_msg

        os.makedirs(abs_folder_path, exist_ok=True) # exist_ok=True redundant due to check, but safe
        get_and_update_tree(parent_dir) # Update tree of the PARENT directory
        success_msg = f"Folder created successfully: '{folder_path}'"
        announce_execution_output(tool_name, action_details, "success", "successful, tree updated")
        return success_msg
    except PermissionError as e:
        logger.warning(f"Permission error creating folder '{folder_path}': {e}")
        error_msg = f"Error: Permission denied creating folder: '{folder_path}'"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except OSError as e:
        logger.exception(f"OS error creating folder '{folder_path}':")
        error_msg = f"Error creating folder '{folder_path}': {e.strerror}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg
    except Exception as e:
        logger.exception(f"Unexpected error creating folder '{folder_path}':")
        error_msg = f"Error: Unexpected error creating folder '{folder_path}': {str(e)}"
        announce_execution_output(tool_name, action_details, "error", error_msg)
        return error_msg

@function_tool
def GetTree(path: str = '.') -> str:
    """
    Gets the directory tree structure starting from the specified path. Defaults to current directory.

    Args:
        path: The starting path for the directory tree. Defaults to '.' (current directory).

    Returns:
        A string representing the directory tree, or an error message string.
    """
    tool_name = "GetTree"
    action_details = f"Get tree structure for path: '{path}'"
    # Call the internal helper which handles context update and error checking
    tree_result = get_and_update_tree(path)

    # Announce the final outcome of the tool call
    if tree_result.startswith("Error:"):
        # Error was already announced by get_and_update_tree, just return it
        return tree_result
    else:
        announce_execution_output(tool_name, action_details, "success", "Tree generated and added to context")
        return tree_result


@function_tool
def ReadTODO() -> str:
    """Reads the content of the predefined TODO file (todo.md)."""
    tool_name = "ReadTODO"
    action_details = f"Read file: '{TODO_FILENAME}'"
    # Reuse the generic ReadFile logic but announce specifically
    content = ReadFile(TODO_FILENAME)
    # ReadFile already announces, so we might not need another announcement here,
    # unless we want to explicitly log the use of ReadTODO vs ReadFile.
    # If ReadFile returned an error, content will contain the error message.
    return content

@function_tool
def WriteTODO(content: str) -> str:
    """Writes (overwrites) content to the predefined TODO file (todo.md)."""
    tool_name = "WriteTODO"
    action_details = f"Write to file: '{TODO_FILENAME}'"
    # Reuse the generic WriteAndCreateFile logic
    result = WriteAndCreateFile(TODO_FILENAME, content)
    # WriteAndCreateFile already announces.
    # If it failed, result contains the error message. If success, it contains the success message.
    # We can modify the message slightly if needed.
    if result.startswith("Error:"):
        return result # Propagate error
    else:
        return f"TODO file ('{TODO_FILENAME}') updated successfully." # Customize success message


# --- Tool Registration ---

def get_tools():
    """Returns a list of all available tool functions."""
    return [
        ShellExec,
        DeleteFile,
        ReadFile,
        WriteAndCreateFile,
        RenameAndMoveFile,
        CreateFolder,
        GetTree,
        ReadTODO,
        WriteTODO,
    ]