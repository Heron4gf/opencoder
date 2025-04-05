from typing import Dict, List # Import List as well for type hinting methods

class Context():
    def __init__(self):
        self.messages: List[str] = []
        self.files: Dict[str, str] = {}

    def get_everything(self) -> List[str]: # Add return type hint
        everything = []
        everything.extend(self.messages)


        files_array = []
        # Now self.files is an actual dictionary, so .items() will work
        for key, value in self.files.items():
            files_array.append(f"{key}: {value}")

        everything.extend(files_array)
        return everything
    
    def serialize(self) -> str:
        return "\n".join(self.get_everything())
        

    def add_user_message(self, message: str): # Add type hint
        self.messages.append(f"user: {message}")

    def add_system_message(self, message: str): # Add type hint
        self.messages.append(f"system: {message}")


    def add_file(self, filename: str, content: str): # Add type hints
        self.files[filename] = content

    def rename_file(self, old_filename: str, new_filename: str): # Add type hints
        # Add check to prevent KeyError if old_filename doesn't exist
        if old_filename in self.files:
            self.files[new_filename] = self.files.pop(old_filename)
        else:
            print(f"Warning: File '{old_filename}' not found for renaming.")


    def delete_file(self, filename: str): # Add type hints
        # Use pop with a default or check existence to avoid KeyError
        if filename in self.files:
            del self.files[filename]
            # Or use: self.files.pop(filename, None) # Removes if exists, does nothing otherwise
        else:
             print(f"Warning: File '{filename}' not found for deletion.")
