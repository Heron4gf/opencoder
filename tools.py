# tools.py

import os
import logging
from agents import function_tool
import subprocess
from api.context_handler import get_context

logger = logging.getLogger(__name__)

GREEN_PREFIX = "\033[92m"
RED_PREFIX = "\033[91m"
RESET_COLOR = "\033[0m"


def get_tools():
    return [
        ShellExec,
        CreateFile,
        DeleteFile,
        ReadFile,
        WriteFile,
        RenameAndMoveFile,
        CreateFolder,
        GetTree
    ]

@function_tool
def ShellExec(command: str) -> str:
    results = []
    try:
        # Split the input command string into individual commands by newlines and semicolons.
        commands = [cmd.strip() for line in command.splitlines() for cmd in line.split(';') if cmd.strip()]
        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                else:
                    output = f"Error: {result.stderr.strip()}"
            except Exception as e:
                output = f"Exception occurred: {str(e)}"
                print(f"{RED_PREFIX}Command failed: {RESET_COLOR}{str(e)}")
            results.append(f"Command: {cmd}\nOutput:\n{output}")
            print(f"{GREEN_PREFIX}Executed command: {cmd}")
        return "\n\n".join(results)
    except Exception as e:
        logger.exception("ShellExecTool error:")
        print(f"{RED_PREFIX}Exception occurred: {RESET_COLOR}{str(e)}")
        return f"Exception occurred: {str(e)}"


@function_tool
def CreateFile(filepath: str, content: str) -> str:
    try:
        with open(filepath, "w") as f:
            f.write(content)
            get_and_update_tree(filepath)
        print(f"{GREEN_PREFIX}File created: {RESET_COLOR}{filepath}")
        return f"File created: {filepath}"
    except Exception as e:
        logger.exception("CreateFileTool error:")
        return f"Error creating file: {str(e)}"

@function_tool
def DeleteFile(filepath: str) -> str:
    try:
        os.remove(filepath)
        get_context().delete_file(filepath)
        get_and_update_tree(filepath)
        print(f"{GREEN_PREFIX}File deleted: {RESET_COLOR}{filepath}")
        return f"File deleted: {filepath}"
    except Exception as e:
        logger.exception("DeleteFileTool error:")
        return f"Error deleting file: {str(e)}"

@function_tool
def ReadFile(filepath: str) -> str:
    try:
        with open(filepath, "r") as f:
            content = f.read()
            get_context().add_file(filepath, content)
        print(f"{GREEN_PREFIX}File read {filepath}")
        return content
    except Exception as e:
        print(f"{RED_PREFIX}Error reading file: {RESET_COLOR}{str(e)}")
        logger.exception("ReadFileTool error:")
        return f"Error reading file: {str(e)}"

@function_tool
def WriteFile(filepath: str, content: str) -> str:
    try:
        with open(filepath, "w") as f:
            f.write(content)
            get_context().add_file(filepath, content)
        print(f"{GREEN_PREFIX}File written: {RESET_COLOR}{filepath}")
        return f"File written: {filepath}"
    except Exception as e:
        print(f"{RED_PREFIX}Error writing file: {RESET_COLOR}{str(e)}")
        logger.exception("WriteFileTool error:")
        return f"Error writing file: {str(e)}"

@function_tool
def RenameAndMoveFile(source_path: str, dest_path: str) -> str:
    try:
        os.rename(source_path, dest_path)
        get_context().rename_file(source_path, dest_path)
        print(f"{GREEN_PREFIX}File moved from {RESET_COLOR}{source_path} {GREEN_PREFIX}to {RESET_COLOR}{dest_path}")
        return f"File moved from {source_path} to {dest_path}"
    except Exception as e:
        logger.exception("MoveFileTool error:")
        print(f"{RED_PREFIX}Error moving file: {RESET_COLOR}{str(e)}")
        return f"Error moving file: {str(e)}"


@function_tool
def CreateFolder(folder_path: str) -> str:
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            get_and_update_tree(folder_path)
            print(f"{GREEN_PREFIX}Folder created: {RESET_COLOR}{folder_path}")
            return f"Folder created: {folder_path}"
        else:
            print(f"{RED_PREFIX}Folder already exists: {RESET_COLOR}{folder_path}")
            return f"Folder already exists: {folder_path}"
    except Exception as e:
        logger.exception("CreateFolderTool error:")
        print(f"{RED_PREFIX}Error creating folder: {RESET_COLOR}{str(e)}")
        return f"Error creating folder: {str(e)}"

@function_tool
def GetTree(path: str) -> str:
    print(f"{GREEN_PREFIX}Getting tree for path: {RESET_COLOR}{path}")
    return get_and_update_tree(path)


def get_and_update_tree(path: str) -> str:
    try:
        def build_tree(root: str, prefix: str = "") -> str:
            entries = sorted(os.listdir(root))
            tree = ""
            for index, entry in enumerate(entries):
                path = os.path.join(root, entry)
                connector = "└── " if index == len(entries) - 1 else "├── "
                tree += f"{prefix}{connector}{entry}\n"
                if os.path.isdir(path):
                    new_prefix = prefix + ("    " if index == len(entries) - 1 else "│   ")
                    tree += build_tree(path, new_prefix)
            return tree

        tree = build_tree(path)
        get_context().add_file("tree of path: "+path, tree)
        return tree
    except Exception as e:
        logger.exception("ListFilesTool error:")
        print(f"{RED_PREFIX}Error listing files: {RESET_COLOR}{str(e)}")
        return f"Error listing files: {str(e)}"
