from unittest.mock import patch, MagicMock
from podcast2obsidian.enricher import enrich, load_prompt, EnrichResult


def test_load_prompt_renders_template():
    rendered = load_prompt("This is a test transcript.")
    assert "This is a test transcript." in rendered
    assert "Основные тезисы" in rendered


def test_enrich_result_fields():
    result = EnrichResult(theses="- Тезис 1", references="- **Книга:** Test")
    assert result.theses == "- Тезис 1"
    assert result.references == "- **Книга:** Test"


@patch("podcast2obsidian.enricher.OpenAI")
def test_enrich_calls_openai_and_parses_response(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    llm_response = """## Основные тезисы

- Тезис первый
- Тезис второй

## Референсы

- **Книга:** "Test Book" — Author"""

    mock_message = MagicMock()
    mock_message.content = llm_response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response

    result = enrich("transcript text", api_key="sk-test", model="gpt-5.4-mini-2026-03-17")

    assert "Тезис первый" in result.theses
    assert "Test Book" in result.references
    mock_client.chat.completions.create.assert_called_once()


@patch("podcast2obsidian.enricher.OpenAI")
def test_enrich_handles_no_references(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    llm_response = """## Основные тезисы

- Тезис единственный

## Референсы

Референсы не обнаружены."""

    mock_message = MagicMock()
    mock_message.content = llm_response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response

    result = enrich("text", api_key="sk-test", model="gpt-5.4-mini-2026-03-17")

    assert "Тезис единственный" in result.theses
    assert "не обнаружены" in result.references
