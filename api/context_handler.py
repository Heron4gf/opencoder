# api/context_handler.py
from .context import Context

context = Context()

def get_context():
    global context
    return context