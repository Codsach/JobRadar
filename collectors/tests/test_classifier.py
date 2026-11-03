"""
Unit tests for collectors.classifier.
Tests rule-based category and level classification.
"""

from __future__ import annotations

import pytest

from collectors.classifier import classify_category, classify_level


@pytest.mark.parametrize(
    "title,expected_category",
    [
        ("Software Development Engineer", "SDE"),
        ("Senior Software Engineer", "SDE"),
        ("Full-Stack Developer", "SDE"),
        ("Frontend Engineer (React)", "SDE"),
        ("Backend Software Engineer - Python", "SDE"),
        ("iOS Developer", "SDE"),
        ("Android Engineer", "SDE"),
        ("SWE Intern", "SDE"),
        ("QA Engineer", "QA"),
        ("Senior SDET", "QA"),
        ("Quality Assurance Analyst", "QA"),
        ("Test Automation Engineer", "QA"),
        ("Software Tester", "QA"),
        ("IT Support Specialist", "IT Support"),
        ("Desktop Support Engineer", "IT Support"),
        ("Helpdesk Technician", "IT Support"),
        ("Systems Administrator", "IT Support"),
        ("Technical Support Specialist", "Technical Support"),
        ("Application Support Engineer", "Technical Support"),
        ("Customer Support Engineer", "Technical Support"),
        ("Cloud Engineer", "Cloud"),
        ("DevOps Engineer", "Cloud"),
        ("Site Reliability Engineer (SRE)", "Cloud"),
        ("Platform Engineer", "Cloud"),
        ("AWS Cloud Infrastructure Engineer", "Cloud"),
        ("Network Engineer", "Networking"),
        ("Network Administrator", "Networking"),
        ("NOC Engineer", "Networking"),
        ("Data Engineer", "Other Tech"),
        ("Cybersecurity Analyst", "Other Tech"),
        ("Solutions Architect", "Other Tech"),
        ("Generic Tech Lead", "Other Tech"),
    ],
)
def test_classify_category_positive(title: str, expected_category: str):
    assert classify_category(title) == expected_category


def test_classify_category_word_boundaries():
    # "asset" contains "sde"? No.
    # "waiter" or "bit" shouldn't trigger "it support"
    assert classify_category("Asset Manager") == "Other Tech"
    assert classify_category("Digital Assets Coordinator") == "Other Tech"


def test_classify_category_description_fallback():
    # If title is vague, uses description
    title = "Associate"
    desc = "You will work as a QA Engineer automating test scripts."
    assert classify_category(title, text=desc) == "QA"


@pytest.mark.parametrize(
    "title,desc,expected_level",
    [
        ("Software Engineer Intern", None, "fresher"),
        ("Graduate Trainee Engineer", None, "fresher"),
        ("Associate Software Engineer", None, "fresher"),
        ("Junior Web Developer", None, "fresher"),
        ("Software Engineer (0-2 years)", None, "fresher"),
        ("Software Developer", "Requires 0 to 1 year of experience", "fresher"),
        ("Entry Level Cloud Specialist", None, "fresher"),
        ("Senior SDE", None, "experienced"),
        ("Staff Engineer", None, "experienced"),
        ("Lead QA Architect", None, "experienced"),
        ("Principal Network Engineer", None, "experienced"),
        ("Engineering Manager", None, "experienced"),
        ("Software Engineer", "Must have 5+ years experience with Go", "experienced"),
        ("Software Engineer", "Build great products with Python", "unknown"),
        ("Technical Support Specialist", None, "unknown"),
    ],
)
def test_classify_level(title: str, desc: str | None, expected_level: str):
    assert classify_level(title, text=desc) == expected_level
