from extensions.outputs.base import BaseOutputGenerator
from extensions.outputs.registry import OutputRegistry


class MockGenerator(BaseOutputGenerator):
    name = "mock_output"
    title = "Mock Output"
    description = "A mock output for testing"
    sections = ["intro", "body"]
    prompt_template = "Generate a {output_type} about:\n{context}\nLanguage: {language}"

    def format_output(self, raw_text: str) -> str:
        return f"# Mock Output\n\n{raw_text}"


def test_base_generator_has_required_attributes():
    gen = MockGenerator()
    assert gen.name == "mock_output"
    assert gen.title == "Mock Output"
    assert gen.sections == ["intro", "body"]


def test_base_generator_builds_prompt():
    gen = MockGenerator()
    prompt = gen.build_prompt(context="Some context about AI", language="tr")
    assert "Some context about AI" in prompt
    assert "tr" in prompt


def test_format_output():
    gen = MockGenerator()
    result = gen.format_output("Test content")
    assert result.startswith("# Mock Output")
    assert "Test content" in result


def test_registry_discovers_generators():
    registry = OutputRegistry()
    registry.register(MockGenerator)
    assert "mock_output" in registry.list_types()
    gen = registry.get("mock_output")
    assert isinstance(gen, MockGenerator)


def test_registry_returns_none_for_unknown():
    registry = OutputRegistry()
    assert registry.get("nonexistent") is None
