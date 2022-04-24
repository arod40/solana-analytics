from typing import Union
from pathlib import Path
import json


class JSONable:
    @classmethod
    def from_dict(cls, dict: dict):
        raise NotImplementedError

    @classmethod
    def from_json(cls, jsonish: Union[str, Path, dict]):
        if isinstance(jsonish, Path):
            jsonish = jsonish.read_text()
        if isinstance(jsonish, str):
            jsonish = json.loads(jsonish)
        return cls.from_json_dict(jsonish)

    def to_json(self):
        raise NotImplementedError


class Model(JSONable):
    @property
    def can_change(self):
        raise NotImplementedError


class Report(JSONable):
    def __init__(self, metadata: JSONable):
        self.metadata = metadata

    @classmethod
    def capture(cls, metadata: JSONable):
        raise NotImplementedError

    def plot(self):
        raise NotImplementedError
