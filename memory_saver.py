# Simple memory manager
class MemorySaver:
    def __init__(self):
        self.memory = []

    def add_user(self, text):
        self.memory.append({"role": "user", "content": text})

    def add_bot(self, text):
        self.memory.append({"role": "assistant", "content": text})

    def get_memory(self):
        return self.memory.copy()