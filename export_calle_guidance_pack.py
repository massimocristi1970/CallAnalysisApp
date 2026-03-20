from __future__ import annotations

import csv
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
CUSTOMER_SENTIMENT_PATH = ROOT / "customer_sentiment.py"
OUTPUT_DIR = ROOT / "exports" / "calle_guidance_pack"


POSITIVE_CATEGORY_DESCRIPTIONS = {
    "Customer Understanding": {
        "why_important": "Shows the agent is checking understanding, slowing down where needed, and making information easier for the customer to follow.",
        "recommended_response_style": "Use plain language, confirm understanding, invite questions, and summarise dates, amounts, and next steps clearly.",
    },
    "Fair Treatment": {
        "why_important": "Shows the customer is being treated respectfully and without unnecessary pressure, especially where affordability or vulnerability may be relevant.",
        "recommended_response_style": "Be calm, non-judgmental, transparent about consequences, and avoid pushing the customer into unaffordable or unsuitable actions.",
    },
    "Vulnerability Handling": {
        "why_important": "Shows the agent has recognised or responded appropriately to signs of distress, health issues, bereavement, reduced understanding, or other vulnerability indicators.",
        "recommended_response_style": "Slow down, acknowledge the situation, reduce pressure, offer support or flexibility where available, and check what help or adjustments would make things easier.",
    },
    "Financial Difficulty": {
        "why_important": "Shows the agent is exploring affordability and priority commitments rather than simply chasing payment.",
        "recommended_response_style": "Focus on affordability, income and expenditure, priority bills, sustainable arrangements, and practical options such as holds, reduced payments, or reviews.",
    },
    "Resolution & Support": {
        "why_important": "Shows the agent is moving the call forward with clear actions, ownership, and next steps.",
        "recommended_response_style": "Explain what will happen next, confirm actions taken, send confirmation where possible, and check whether the customer needs anything else.",
    },
}


VULNERABILITY_SIGNAL_GROUPS = OrderedDict(
    [
        (
            "acute_distress_or_safeguarding",
            {
                "why_important": "Potential immediate welfare, safeguarding, or severe distress risk.",
                "recommended_response_style": "Prioritise safety, de-escalate, avoid pressure, and follow safeguarding or escalation procedures immediately.",
                "matcher": lambda term: any(
                    token in term
                    for token in [
                        "suicide",
                        "giving up",
                        "breaking point",
                        "mental breakdown",
                        "psychosis",
                        "sectioned",
                        "domestic violence",
                        "abused",
                        "abusive",
                        "coercion",
                        "restraining order",
                        "refuge",
                        "harassment",
                        "police",
                        "scam",
                        "manipulated",
                    ]
                ),
            },
        ),
        (
            "mental_health_or_cognitive",
            {
                "why_important": "Customer may have reduced resilience, reduced understanding, or need a slower and more supportive approach.",
                "recommended_response_style": "Use simple language, repeat key information, check understanding, and ask whether any support or reasonable adjustments would help.",
                "matcher": lambda term: any(
                    token in term
                    for token in [
                        "vulnerable",
                        "mental health",
                        "depression",
                        "anxiety",
                        "stress",
                        "adhd",
                        "autism",
                        "disorientated",
                        "lacks understanding",
                        "overwhelmed",
                        "therapist",
                        "medication",
                        "bipolar",
                        "ptsd",
                        "memory",
                        "confus",
                    ]
                ),
            },
        ),
        (
            "health_bereavement_or_life_event",
            {
                "why_important": "Customer circumstances may be materially affected by illness, bereavement, injury, or major life disruption.",
                "recommended_response_style": "Acknowledge the situation, avoid unnecessary probing, offer flexibility, and reduce pressure while still explaining options clearly.",
                "matcher": lambda term: any(
                    token in term
                    for token in [
                        "terminal",
                        "cancer",
                        "death",
                        "diagnosis",
                        "injury",
                        "long term sick",
                        "rehabilitation",
                        "funeral",
                        "grieving",
                        "bereavement",
                        "illness",
                        "surgery",
                        "chronic pain",
                        "mobility issues",
                        "child unwell",
                    ]
                ),
            },
        ),
        (
            "financial_hardship_and_basic_needs",
            {
                "why_important": "Customer may be unable to maintain payments without harming essential living costs or priority commitments.",
                "recommended_response_style": "Explore affordability first, discuss priority bills, consider smaller payments or holds, and avoid unaffordable commitments.",
                "matcher": lambda term: any(
                    token in term
                    for token in [
                        "can't afford",
                        "no money",
                        "no income",
                        "skip meals",
                        "heating or eating",
                        "foodbank",
                        "rent arrears",
                        "mortgage arrears",
                        "council tax arrears",
                        "utility bills",
                        "zero disposable income",
                        "negative budget",
                        "financial difficulty",
                        "financial difficulties",
                        "financial trouble",
                        "overdrawn",
                        "priority bills",
                        "priority debts",
                        "energy arrears",
                        "disconnection notice",
                        "cutoff notice",
                        "job loss",
                        "redundancy",
                        "made redundant",
                        "between jobs",
                        "overcommitted",
                    ]
                ),
            },
        ),
        (
            "housing_or_stability_risk",
            {
                "why_important": "Customer may be experiencing housing instability or other major life disruption that affects their ability to engage normally.",
                "recommended_response_style": "Use a supportive and practical approach, avoid pressure, and focus on stability and realistic next steps.",
                "matcher": lambda term: any(
                    token in term
                    for token in [
                        "homeless",
                        "sofa surfing",
                        "temporary accommodation",
                        "eviction",
                        "zero hours contract",
                        "casual work",
                        "gig economy",
                    ]
                ),
            },
        ),
    ]
)


UNHAPPY_SECTION_METADATA = OrderedDict(
    [
        (
            "Frustration and complaints (negative)",
            {
                "slug": "frustration_and_complaints",
                "why_important": "Signals dissatisfaction, loss of trust, or an elevated risk of complaint if the interaction is not handled well.",
                "recommended_response_style": "Acknowledge the frustration, avoid defensiveness, take ownership of next steps, and explain what will happen clearly.",
            },
        ),
        (
            "Escalation requests",
            {
                "slug": "escalation_requests",
                "why_important": "Shows the customer believes normal resolution has failed or wants the matter reviewed by someone more senior.",
                "recommended_response_style": "Stay calm, explain the escalation path clearly, capture the issue accurately, and avoid obstructing legitimate escalation.",
            },
        ),
        (
            "Urgency",
            {
                "slug": "urgency_signals",
                "why_important": "Shows time pressure and may indicate heightened emotional risk or practical consequences if delayed.",
                "recommended_response_style": "Set realistic expectations, prioritise immediate clarifications, and be explicit about timelines and what can be done now.",
            },
        ),
        (
            "Skepticism and doubt",
            {
                "slug": "skepticism_and_doubt",
                "why_important": "Shows the customer may not trust the explanation they are being given.",
                "recommended_response_style": "Use transparent explanations, avoid jargon, and restate the reason, evidence, and next step in simple terms.",
            },
        ),
        (
            "Confusion and problems",
            {
                "slug": "confusion_and_problems",
                "why_important": "Shows the customer may not understand what is happening or may be struggling to complete the required action.",
                "recommended_response_style": "Break the task into smaller steps, check understanding, and avoid overwhelming the customer with too much information at once.",
            },
        ),
    ]
)


def clean_phrase(text: str) -> str:
    text = str(text).strip()
    text = text.replace("\u2026", "...")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \"'")


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = clean_phrase(item)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def read_config_text() -> str:
    return CONFIG_PATH.read_text(encoding="utf-8")


def parse_yaml_section_of_lists(text: str, section_name: str) -> Dict[str, List[str]]:
    lines = text.splitlines()
    in_section = False
    current_key = None
    result: Dict[str, List[str]] = OrderedDict()

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        if not in_section:
            if stripped == f"{section_name}:":
                in_section = True
            continue

        if stripped and indent == 0 and stripped.endswith(":"):
            break

        if not stripped or stripped.startswith("#"):
            continue

        if indent == 2 and stripped.endswith(":") and not stripped.startswith("-"):
            current_key = stripped[:-1].strip()
            result[current_key] = []
            continue

        if indent >= 4 and stripped.startswith("-") and current_key:
            value = stripped[1:].strip()
            result[current_key].append(clean_phrase(value))

    return {key: unique_preserve_order(value) for key, value in result.items()}


def parse_pattern_sections(path: Path, list_name: str) -> Dict[str, List[str]]:
    text = path.read_text(encoding="utf-8")
    target = f"{list_name} = ["
    start = text.find(target)
    if start == -1:
        raise ValueError(f"Could not find {list_name} in {path}")

    start = text.find("[", start)
    depth = 0
    end = None
    for index in range(start, len(text)):
        char = text[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        raise ValueError(f"Could not parse {list_name} list boundaries in {path}")

    block = text[start + 1 : end]
    sections: Dict[str, List[str]] = OrderedDict()
    current_section = "uncategorised"
    sections[current_section] = []

    for raw_line in block.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_section = stripped.lstrip("#").strip()
            sections.setdefault(current_section, [])
            continue

        values = re.findall(r'r"([^"]+)"', stripped)
        values += re.findall(r"r'([^']+)'", stripped)
        for value in values:
            sections.setdefault(current_section, []).append(clean_phrase(value))

    return {key: unique_preserve_order(value) for key, value in sections.items() if value}


def group_vulnerability_terms(keywords: Dict[str, List[str]]) -> List[Dict[str, object]]:
    grouped: List[Dict[str, object]] = []
    assigned = set()

    for group_name, meta in VULNERABILITY_SIGNAL_GROUPS.items():
        phrases: List[str] = []
        for terms in keywords.values():
            for term in terms:
                if term in assigned:
                    continue
                if meta["matcher"](term.lower()):
                    phrases.append(term)
                    assigned.add(term)

        if phrases:
            grouped.append(
                {
                    "signal_group": group_name,
                    "why_important": meta["why_important"],
                    "recommended_response_style": meta["recommended_response_style"],
                    "terms": unique_preserve_order(phrases),
                }
            )

    remaining = []
    for terms in keywords.values():
        for term in terms:
            if term not in assigned:
                remaining.append(term)

    if remaining:
        grouped.append(
            {
                "signal_group": "other_relevant_vulnerability_or_hardship_terms",
                "why_important": "Additional terms already treated as risk or support indicators by the app.",
                "recommended_response_style": "Treat as a cue to assess whether a more supportive or lower-pressure response is needed.",
                "terms": unique_preserve_order(remaining),
            }
        )

    return grouped


def build_pack() -> Dict[str, object]:
    config_text = read_config_text()
    call_type_category_map = parse_yaml_section_of_lists(config_text, "call_type_category_map")
    agent_behaviour = parse_yaml_section_of_lists(config_text, "agent_behaviour_phrases")
    keywords = parse_yaml_section_of_lists(config_text, "keywords")
    customer_pattern_sections = parse_pattern_sections(CUSTOMER_SENTIMENT_PATH, "CUSTOMER_PATTERNS")

    positive_language = []
    for category, phrases in agent_behaviour.items():
        description = POSITIVE_CATEGORY_DESCRIPTIONS.get(
            category,
            {
                "why_important": "This category is scored positively by the app.",
                "recommended_response_style": "Use this language where appropriate and keep the response clear, supportive, and practical.",
            },
        )
        positive_language.append(
            {
                "category": category,
                "why_important": description["why_important"],
                "recommended_response_style": description["recommended_response_style"],
                "example_phrases": unique_preserve_order(list(phrases)),
            }
        )

    vulnerability_terms = {
        priority: unique_preserve_order(list(terms))
        for priority, terms in keywords.items()
    }

    vulnerability_signals = group_vulnerability_terms(vulnerability_terms)

    unhappy_customer_signals = []
    for section_name, meta in UNHAPPY_SECTION_METADATA.items():
        phrases = customer_pattern_sections.get(section_name, [])
        if not phrases:
            continue
        unhappy_customer_signals.append(
            {
                "signal_group": meta["slug"],
                "why_important": meta["why_important"],
                "recommended_response_style": meta["recommended_response_style"],
                "example_phrases": phrases,
            }
        )

    recommended_principles = [
        {
            "scenario": "When vulnerability is indicated",
            "guidance": "Slow the conversation down, check understanding, reduce pressure, and offer support or flexibility before focusing on payment or process.",
        },
        {
            "scenario": "When the customer sounds unhappy or frustrated",
            "guidance": "Acknowledge the emotion first, avoid sounding scripted or defensive, then explain the fix or escalation path clearly.",
        },
        {
            "scenario": "When affordability or hardship is indicated",
            "guidance": "Prioritise sustainable outcomes, explore income and expenditure, and avoid setting commitments that could worsen the customer’s position.",
        },
        {
            "scenario": "When explaining actions or next steps",
            "guidance": "Use short plain-English explanations, confirm dates and amounts, and check whether the customer wants anything repeated or sent in writing.",
        },
    ]

    return {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "Shareable guidance pack for Calle AI based on the language, signals, and scoring themes already used inside CallAnalysisApp.",
            "source_files": ["config.yaml", "customer_sentiment.py", "analyser.py"],
        },
        "call_type_category_map": call_type_category_map,
        "positive_language": positive_language,
        "vulnerability_keywords_by_priority": vulnerability_terms,
        "vulnerability_signals": vulnerability_signals,
        "unhappy_customer_signals": unhappy_customer_signals,
        "recommended_response_principles": recommended_principles,
    }


def write_json(pack: Dict[str, object]) -> Path:
    path = OUTPUT_DIR / "calle_guidance_pack.json"
    path.write_text(json.dumps(pack, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def write_csv(pack: Dict[str, object]) -> Path:
    path = OUTPUT_DIR / "calle_guidance_pack.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "section",
                "group_or_category",
                "priority",
                "term_or_phrase",
                "why_important",
                "recommended_response_style",
                "source",
            ],
        )
        writer.writeheader()

        for item in pack["positive_language"]:
            for phrase in item["example_phrases"]:
                writer.writerow(
                    {
                        "section": "positive_language",
                        "group_or_category": item["category"],
                        "priority": "",
                        "term_or_phrase": phrase,
                        "why_important": item["why_important"],
                        "recommended_response_style": item["recommended_response_style"],
                        "source": "config.yaml:agent_behaviour_phrases",
                    }
                )

        for priority, terms in pack["vulnerability_keywords_by_priority"].items():
            for term in terms:
                writer.writerow(
                    {
                        "section": "vulnerability_keyword",
                        "group_or_category": "keyword_flag",
                        "priority": priority,
                        "term_or_phrase": term,
                        "why_important": "The app treats this as a term worth flagging in call content.",
                        "recommended_response_style": "Treat this as a cue to assess whether a more supportive or lower-pressure response is needed.",
                        "source": "config.yaml:keywords",
                    }
                )

        for item in pack["vulnerability_signals"]:
            for term in item["terms"]:
                writer.writerow(
                    {
                        "section": "vulnerability_signal_group",
                        "group_or_category": item["signal_group"],
                        "priority": "",
                        "term_or_phrase": term,
                        "why_important": item["why_important"],
                        "recommended_response_style": item["recommended_response_style"],
                        "source": "config.yaml:keywords",
                    }
                )

        for item in pack["unhappy_customer_signals"]:
            for phrase in item["example_phrases"]:
                writer.writerow(
                    {
                        "section": "unhappy_customer_signal",
                        "group_or_category": item["signal_group"],
                        "priority": "",
                        "term_or_phrase": phrase,
                        "why_important": item["why_important"],
                        "recommended_response_style": item["recommended_response_style"],
                        "source": "customer_sentiment.py:CUSTOMER_PATTERNS",
                    }
                )

        for item in pack["recommended_response_principles"]:
            writer.writerow(
                {
                    "section": "recommended_response_principle",
                    "group_or_category": item["scenario"],
                    "priority": "",
                    "term_or_phrase": item["guidance"],
                    "why_important": "High-level guidance inferred from the app's scoring and customer-signal logic.",
                    "recommended_response_style": item["guidance"],
                    "source": "Derived from config.yaml and customer_sentiment.py",
                }
            )
    return path


def write_markdown(pack: Dict[str, object]) -> Path:
    path = OUTPUT_DIR / "calle_guidance_pack.md"
    lines: List[str] = []
    lines.append("# Calle AI Guidance Pack")
    lines.append("")
    lines.append("This pack summarises the language, terms, and signal types currently used in CallAnalysisApp for positive scoring, vulnerability detection, and unhappy-customer detection.")
    lines.append("")
    lines.append(f"Generated: {pack['metadata']['generated_at_utc']}")
    lines.append("")
    lines.append("## 1. Call-Type Category Mapping")
    lines.append("")
    for call_type, categories in pack["call_type_category_map"].items():
        lines.append(f"- **{call_type}**: {', '.join(categories)}")
    lines.append("")
    lines.append("## 2. Positive / Desired Agent Language")
    lines.append("")
    for item in pack["positive_language"]:
        lines.append(f"### {item['category']}")
        lines.append("")
        lines.append(f"- Why it matters: {item['why_important']}")
        lines.append(f"- Recommended response style: {item['recommended_response_style']}")
        lines.append("- Example phrases:")
        for phrase in item["example_phrases"][:30]:
            lines.append(f"  - {phrase}")
        if len(item["example_phrases"]) > 30:
            lines.append(f"  - ... plus {len(item['example_phrases']) - 30} more phrases in the JSON/CSV export")
        lines.append("")
    lines.append("## 3. Vulnerability Signals")
    lines.append("")
    for item in pack["vulnerability_signals"]:
        lines.append(f"### {item['signal_group']}")
        lines.append("")
        lines.append(f"- Why it matters: {item['why_important']}")
        lines.append(f"- Recommended response style: {item['recommended_response_style']}")
        lines.append(f"- Example terms: {', '.join(item['terms'][:20])}")
        if len(item["terms"]) > 20:
            lines.append(f"- Additional terms available in export: {len(item['terms']) - 20}")
        lines.append("")
    lines.append("## 4. Unhappy Customer Signals")
    lines.append("")
    for item in pack["unhappy_customer_signals"]:
        lines.append(f"### {item['signal_group']}")
        lines.append("")
        lines.append(f"- Why it matters: {item['why_important']}")
        lines.append(f"- Recommended response style: {item['recommended_response_style']}")
        lines.append("- Example phrases:")
        for phrase in item["example_phrases"][:20]:
            lines.append(f"  - {phrase}")
        if len(item["example_phrases"]) > 20:
            lines.append(f"  - ... plus {len(item['example_phrases']) - 20} more phrases in the JSON/CSV export")
        lines.append("")
    lines.append("## 5. Recommended Response Principles")
    lines.append("")
    for item in pack["recommended_response_principles"]:
        lines.append(f"- **{item['scenario']}**: {item['guidance']}")
    lines.append("")
    lines.append("## 6. Source Notes")
    lines.append("")
    lines.append("- Positive language and call-type mapping come from `config.yaml`.")
    lines.append("- Unhappy-customer signals come from `customer_sentiment.py` pattern matching.")
    lines.append("- The recommended response principles are a cleaned summary derived from the app's current scoring and signal logic.")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pack = build_pack()
    json_path = write_json(pack)
    csv_path = write_csv(pack)
    markdown_path = write_markdown(pack)

    summary = {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(markdown_path),
        "positive_categories": len(pack["positive_language"]),
        "vulnerability_groups": len(pack["vulnerability_signals"]),
        "unhappy_signal_groups": len(pack["unhappy_customer_signals"]),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
