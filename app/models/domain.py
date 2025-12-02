from dataclasses import dataclass
from jinja2 import Template
from typing import Any

# Assuming Jinja2 is used for templating

@dataclass
class Prompt:
    id: str
    purpose: str
    name: str
    template: str
    version: int = 1

    def update(self, template: str):
        self.template = template
        self.version += 1

    def render(self, parameters: dict[str, Any]) -> str:
        template: Template = Template(self.template)
        return template.render(parameters)