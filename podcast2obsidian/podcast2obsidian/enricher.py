from dataclasses import dataclass
from importlib import resources

from jinja2 import Template
from openai import OpenAI


@dataclass
class EnrichResult:
    theses: str
    references: str


def load_prompt(transcript: str) -> str:
    """Load the enrich.md prompt template and render with transcript."""
    prompt_file = resources.files("podcast2obsidian.prompts").joinpath("enrich.md")
    template_text = prompt_file.read_text(encoding="utf-8")
    template = Template(template_text)
    return template.render(transcript=transcript)


def enrich(transcript: str, api_key: str, model: str) -> EnrichResult:
    """Send transcript to OpenAI and parse theses + references from response."""
    prompt = load_prompt(transcript)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content
    if not content:
        return EnrichResult(theses="(LLM returned empty response)", references="")

    return _parse_response(content)


def _parse_response(content: str) -> EnrichResult:
    """Parse LLM response into theses and references sections."""
    theses = ""
    references = ""

    sections = content.split("## ")
    for section in sections:
        if section.startswith("Основные тезисы"):
            theses = section.removeprefix("Основные тезисы").strip()
        elif section.startswith("Референсы"):
            references = section.removeprefix("Референсы").strip()

    return EnrichResult(theses=theses, references=references)
