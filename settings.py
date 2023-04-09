import json
from pathlib import Path


class Settings:
    def __init__(self, filename):
        self.filename = Path(filename)
        self.load()

    def load(self):
        if self.filename.exists():
            with self.filename.open() as f:
                self.configuration = json.load(f)
        else:
            self.configuration = {}

    def save(self):
        with self.filename.open("w") as f:
            json.dump(self.configuration, f, indent=2)

    def get(self, key, default=None):
        return self.configuration.get(key, default)

    def set(self, key, value):
        self.configuration[key] = value

    def __getitem__(self, key):
        return self.configuration[key]

    def __setitem__(self, key, value):
        self.configuration[key] = value

    def __delitem__(self, key):
        del self.configuration[key]

    def __contains__(self, key):
        return key in self.configuration
