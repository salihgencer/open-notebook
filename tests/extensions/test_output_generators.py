import pytest

from extensions.outputs.study_guide import StudyGuideGenerator
from extensions.outputs.faq import FAQGenerator
from extensions.outputs.timeline import TimelineGenerator
from extensions.outputs.briefing import BriefingGenerator
from extensions.outputs.registry import OutputRegistry


@pytest.fixture
def registry():
    reg = OutputRegistry()
    reg.register(StudyGuideGenerator)
    reg.register(FAQGenerator)
    reg.register(TimelineGenerator)
    reg.register(BriefingGenerator)
    return reg


def test_all_generators_registered(registry):
    types = registry.list_types()
    assert "study_guide" in types
    assert "faq" in types
    assert "timeline" in types
    assert "briefing" in types


def test_study_guide_prompt_contains_sections():
    gen = StudyGuideGenerator()
    prompt = gen.build_prompt(context="AI fundamentals", language="en")
    assert "AI fundamentals" in prompt
    assert "en" in prompt


def test_faq_prompt_contains_context():
    gen = FAQGenerator()
    prompt = gen.build_prompt(context="Machine learning basics", language="tr")
    assert "Machine learning basics" in prompt
    assert "tr" in prompt


def test_timeline_prompt_contains_context():
    gen = TimelineGenerator()
    prompt = gen.build_prompt(context="History of computing", language="en")
    assert "History of computing" in prompt


def test_briefing_prompt_contains_context():
    gen = BriefingGenerator()
    prompt = gen.build_prompt(context="Quarterly report data", language="tr")
    assert "Quarterly report data" in prompt


def test_each_generator_has_required_fields():
    for GenClass in [StudyGuideGenerator, FAQGenerator, TimelineGenerator, BriefingGenerator]:
        gen = GenClass()
        assert gen.name, f"{GenClass.__name__} missing name"
        assert gen.title, f"{GenClass.__name__} missing title"
        assert gen.description, f"{GenClass.__name__} missing description"
        assert len(gen.sections) > 0, f"{GenClass.__name__} has no sections"
