#!/usr/bin/env python3
"""Keep exam-page SEO and preview content aligned with the app.

This performs the repeatable, site-wide parts of the Search Console cleanup:

* concise, query-led title tags and descriptions;
* accurate question counts in metadata, schema and body copy;
* useful, exam-specific question previews sourced from the in-app banks;
* clean SoftwareApplication keywords and evergreen feature claims;
* consistent Answer Coach naming and privacy-safe provenance;
* matching JSON-LD modification dates.

sitemap.xml's <lastmod> is not written here -- see
Tools/update-sitemap-lastmod.py, which derives it from git history.

The exam-specific editorial copy remains in each HTML page. Run this after
question-bank updates so newly published pages do not inherit generic Azure
examples or stale metadata.

Usage:
  python3 Tools/optimise-marketing-seo.py
  python3 Tools/optimise-marketing-seo.py --check
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXAMS_DIR = ROOT / "exams"
DATA_FILE = ROOT / "data" / "exam-counts.json"
SITEMAP = ROOT / "sitemap.xml"
SEO_UPDATED = "2026-08-09"
SEO_UPDATED_OVERRIDES = {
    # New pages launched after the 2026-08-09 site-wide SEO pass.
    "AB-650": "2026-08-23",
    "AI-500": "2026-08-23",
    # Wave-1 de-templating pass (Task B, final-review fix wave).
    "AI-103": "2026-09-04",
    "AB-620": "2026-09-04",
    "AB-100": "2026-09-04",
    "SC-500": "2026-09-04",
    "AI-200": "2026-09-04",
    "AZ-104": "2026-09-04",
    "AZ-900": "2026-09-04",
    # Wave-2a de-templating pass (fundamentals cluster).
    "DP-900": "2026-09-05",
    "PL-900": "2026-09-05",
    "SC-900": "2026-09-05",
    "AB-900": "2026-09-05",
}
RETIRED_EXAMS = {
    "AI-900": {
        "date": "30 June 2026",
        "replacement": "AI-901",
        "replacement_label": "the current Azure AI Fundamentals exam",
    },
    "AI-102": {
        "date": "30 June 2026",
        "replacement": "AI-103",
        "replacement_label": "the current Azure AI apps and agents exam",
    },
    "DP-100": {
        "date": "1 June 2026",
        "replacement": "AI-300",
        "replacement_label": "a current machine-learning operations option",
    },
    "AZ-204": {
        "date": "31 July 2026",
        "replacement": "AI-200",
        "replacement_label": "Microsoft's replacement developer course and current AI cloud route",
    },
    "AZ-500": {
        "date": "31 August 2026",
        "replacement": "SC-500",
        "replacement_label": "Microsoft's Cloud and AI Security Engineer successor",
    },
}
RETIRING_EXAMS = {}
ACTIVE_SEO = {
    "AB-650": {
        "description": (
            "{count} AB-650 practice questions for AI Services Administrator Associate. Study "
            "Copilot administration, agent governance, and Purview on iPhone and iPad."
        ),
        "social_description": (
            "{count} AB-650 practice questions for Microsoft 365 Copilot administration, Agent 365 "
            "governance, and Purview data security. Adaptive exam prep for iPhone and iPad."
        ),
    },
    "AI-500": {
        "description": (
            "{count} AI-500 practice questions for Multi-Agent AI Solutions Expert. Study Microsoft "
            "Foundry, Agent Framework, orchestration, and security on iPhone and iPad."
        ),
        "social_description": (
            "{count} AI-500 practice questions for Microsoft Foundry, Agent Framework orchestration, "
            "evaluations, and agent security. Adaptive exam prep for iPhone and iPad."
        ),
    },
    "AB-410": {
        "description": (
            "{count} AB-410 practice questions for Intelligent Applications Builder. Study Dataverse, "
            "Power Apps, cloud flows, Power Fx, and AI Hub on iPhone and iPad."
        ),
        "social_description": (
            "{count} AB-410 practice questions for Dataverse, Power Apps, cloud flows, Power Fx, "
            "and AI Hub. Adaptive exam prep for iPhone and iPad."
        ),
    },
    "AZ-400": {
        "title": 'AZ-400 Practice Questions — {count} Qs for DevOps Engineer (2026)',
        "description": (
            "{count} AZ-400 practice questions for DevOps Engineer Expert. Study Azure Pipelines, "
            "GitHub Actions, security, deployments, and monitoring on iPhone and iPad."
        ),
        "social_description": (
            "{count} AZ-400 practice questions covering Azure Pipelines, GitHub Actions, security, "
            "deployments, and monitoring. Adaptive exam prep for iPhone and iPad."
        ),
    },
    "PL-300": {
        "title": 'PL-300 Practice Questions — {count} Qs for Power BI Analyst (2026)',
        "description": (
            "{count} PL-300 Power BI practice questions covering Power Query, DAX, data modelling, "
            "visualisation, and security. Adaptive exam prep for iPhone and iPad."
        ),
        "social_description": (
            "{count} PL-300 Power BI practice questions covering Power Query, DAX, modelling, "
            "visualisation, and security. Adaptive exam prep for iPhone and iPad."
        ),
    },
    "AI-103": {
        "description": (
            "{count} AI-103 practice questions for Developing AI Apps and Agents on Azure. "
            "Study Microsoft Foundry, RAG, agents, and Python on iPhone and iPad."
        ),
        "social_description": (
            "{count} AI-103 practice questions for Microsoft Foundry, RAG, agents, and Python. "
            "Adaptive exam prep for iPhone and iPad."
        ),
    },
    "AB-620": {
        "description": (
            "{count} AB-620 practice questions for the Copilot Studio AI Agent Builder exam. "
            "Study agents, Power Platform, integrations, and governance on iPhone and iPad."
        ),
        "social_description": (
            "{count} AB-620 practice questions for Copilot Studio, Power Platform integrations, "
            "and agent governance. Adaptive exam prep for iPhone and iPad."
        ),
    },
    "AI-901": {
        "title": 'AI-901 Practice Questions — {count} Qs for AI Fundamentals (2026)',
        "description": (
            "{count} AI-901 practice questions for the current Azure AI Fundamentals exam. "
            "Study AI concepts, Microsoft Foundry, and Python on iPhone and iPad."
        ),
        "social_description": (
            "{count} AI-901 practice questions for the current Azure AI Fundamentals exam, "
            "including Microsoft Foundry and Python. Free to start."
        ),
    },
    "AB-100": {
        "title": 'AB-100 Practice Questions — {count} Qs for AI Architect (2026)',
        "description": (
            '{count} AB-100 practice questions for Agentic AI Business Solutions Architect. Multi-agent architecture, governance, and Copilot — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} AB-100 practice questions for Agentic AI Business Solutions Architect. Multi-agent architecture, governance, and Copilot — updated for the 2026 exam.'
        ),
    },
    "AB-731": {
        "title": 'AB-731 Practice Questions — {count} Qs for AI Leadership (2026)',
        "description": (
            '{count} AB-731 practice questions for Microsoft AI Transformation Leader. AI strategy, adoption, and governance — free to start on iPhone and iPad.'
        ),
        "social_description": (
            '{count} AB-731 practice questions for Microsoft AI Transformation Leader. AI strategy, adoption, and governance — free to start on iPhone and iPad.'
        ),
    },
    "AB-900": {
        "title": 'AB-900 Practice Questions — {count} Qs for Copilot Admin (2026)',
        "description": (
            '{count} AB-900 practice questions for Copilot and Agent Administration Fundamentals. Microsoft 365, Copilot configuration, and agents — updated for 2026.'
        ),
        "social_description": (
            '{count} AB-900 practice questions for Copilot and Agent Administration Fundamentals. Microsoft 365, Copilot configuration, and agents — updated for 2026.'
        ),
    },
    "AI-200": {
        "title": 'AI-200 Practice Questions — {count} Qs for AI Developer (2026)',
        "description": (
            '{count} AI-200 practice questions for Azure AI Cloud Developer. Cloud-native AI apps, embeddings, and agent integration — exam-style prep on iPhone and iPad.'
        ),
        "social_description": (
            '{count} AI-200 practice questions for Azure AI Cloud Developer. Cloud-native AI apps, embeddings, and agent integration — exam-style prep on iPhone and iPad.'
        ),
    },
    "AI-300": {
        "title": 'AI-300 Practice Questions — {count} Qs for ML Ops Engineer (2026)',
        "description": (
            '{count} AI-300 practice questions for ML Operations Engineer. ML lifecycle, deployment, and monitoring on Azure — exam-style prep on iPhone and iPad.'
        ),
        "social_description": (
            '{count} AI-300 practice questions for ML Operations Engineer. ML lifecycle, deployment, and monitoring on Azure — exam-style prep on iPhone and iPad.'
        ),
    },
    "AZ-104": {
        "title": 'AZ-104 Practice Questions — {count} Qs for Azure Admin (2026)',
        "description": (
            '{count} AZ-104 practice questions for Microsoft Azure Administrator. Identities, storage, compute, networking, and monitoring — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} AZ-104 practice questions for Microsoft Azure Administrator. Identities, storage, compute, networking, and monitoring — updated for the 2026 exam.'
        ),
    },
    "AZ-305": {
        "title": 'AZ-305 Practice Questions — {count} Qs for Azure Architect (2026)',
        "description": (
            '{count} AZ-305 practice questions for Azure Solutions Architect Expert. Identity, data, business continuity, and infrastructure design — updated for 2026.'
        ),
        "social_description": (
            '{count} AZ-305 practice questions for Azure Solutions Architect Expert. Identity, data, business continuity, and infrastructure design — updated for 2026.'
        ),
    },
    "AZ-700": {
        "title": 'AZ-700 Practice Questions — {count} Qs for Network Engineer (2026)',
        "description": (
            '{count} AZ-700 practice questions for Azure Network Engineer. VNets, peering, ExpressRoute, load balancing, and network security — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} AZ-700 practice questions for Azure Network Engineer. VNets, peering, ExpressRoute, load balancing, and network security — updated for the 2026 exam.'
        ),
    },
    "AZ-900": {
        "title": 'AZ-900 Practice Questions — {count} Qs for Fundamentals (2026)',
        "description": (
            '{count} AZ-900 practice questions for Microsoft Azure Fundamentals. Cloud concepts, architecture, services, and pricing — free to start on iPhone and iPad.'
        ),
        "social_description": (
            '{count} AZ-900 practice questions for Microsoft Azure Fundamentals. Cloud concepts, architecture, services, and pricing — free to start on iPhone and iPad.'
        ),
    },
    "DP-300": {
        "title": 'DP-300 Practice Questions — {count} Qs for Database Admin (2026)',
        "description": (
            '{count} DP-300 practice questions for Azure Database Administrator. SQL deployment, security, performance tuning, and HA/DR — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} DP-300 practice questions for Azure Database Administrator. SQL deployment, security, performance tuning, and HA/DR — updated for the 2026 exam.'
        ),
    },
    "DP-700": {
        "title": 'DP-700 Practice Questions — {count} Qs for Fabric Engineer (2026)',
        "description": (
            '{count} DP-700 practice questions for Microsoft Fabric Data Engineer. Ingestion, transformation, lakehouses, and monitoring — exam-style prep on iPhone and iPad.'
        ),
        "social_description": (
            '{count} DP-700 practice questions for Microsoft Fabric Data Engineer. Ingestion, transformation, lakehouses, and monitoring — exam-style prep on iPhone and iPad.'
        ),
    },
    "DP-750": {
        "title": 'DP-750 Practice Questions — {count} Qs for Databricks (2026)',
        "description": (
            '{count} DP-750 practice questions for Azure Databricks Data Engineer. Spark, Delta Lake, pipelines, and governance — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} DP-750 practice questions for Azure Databricks Data Engineer. Spark, Delta Lake, pipelines, and governance — updated for the 2026 exam.'
        ),
    },
    "DP-800": {
        "title": 'DP-800 Practice Questions — {count} Qs for SQL AI Developer (2026)',
        "description": (
            '{count} DP-800 practice questions for Developing AI-Enabled Database Solutions. SQL, vector search, and intelligent apps — exam-style prep on iPhone and iPad.'
        ),
        "social_description": (
            '{count} DP-800 practice questions for Developing AI-Enabled Database Solutions. SQL, vector search, and intelligent apps — exam-style prep on iPhone and iPad.'
        ),
    },
    "DP-900": {
        "title": 'DP-900 Practice Questions — {count} Qs for Data Basics (2026)',
        "description": (
            '{count} DP-900 practice questions for Azure Data Fundamentals. Core data concepts, relational, non-relational, and analytics — free to start on iPhone and iPad.'
        ),
        "social_description": (
            '{count} DP-900 practice questions for Azure Data Fundamentals. Core data concepts, relational, non-relational, and analytics — free to start on iPhone and iPad.'
        ),
    },
    "GH-300": {
        "title": 'GH-300 Practice Questions — {count} Qs for GitHub Copilot (2026)',
        "description": (
            '{count} GH-300 practice questions for the GitHub Copilot certification. Copilot features, prompt skills, policies, and responsible AI — updated for 2026.'
        ),
        "social_description": (
            '{count} GH-300 practice questions for the GitHub Copilot certification. Copilot features, prompt skills, policies, and responsible AI — updated for 2026.'
        ),
    },
    "GH-900": {
        "title": 'GH-900 Practice Questions — {count} Qs for GitHub Basics (2026)',
        "description": (
            '{count} GH-900 practice questions for GitHub Foundations. Repositories, pull requests, Actions basics, and collaboration — free to start on iPhone and iPad.'
        ),
        "social_description": (
            '{count} GH-900 practice questions for GitHub Foundations. Repositories, pull requests, Actions basics, and collaboration — free to start on iPhone and iPad.'
        ),
    },
    "PL-900": {
        "title": 'PL-900 Practice Questions — {count} Qs for Power Platform (2026)',
        "description": (
            '{count} PL-900 practice questions for Power Platform Fundamentals. Power Apps, Automate, Power BI, and Copilot Studio basics — free to start on iPhone and iPad.'
        ),
        "social_description": (
            '{count} PL-900 practice questions for Power Platform Fundamentals. Power Apps, Automate, Power BI, and Copilot Studio basics — free to start on iPhone and iPad.'
        ),
    },
    "SC-100": {
        "title": 'SC-100 Practice Questions — {count} Qs for Cyber Architect (2026)',
        "description": (
            '{count} SC-100 practice questions for Microsoft Cybersecurity Architect. Zero Trust strategy, GRC, and security operations design — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} SC-100 practice questions for Microsoft Cybersecurity Architect. Zero Trust strategy, GRC, and security operations design — updated for the 2026 exam.'
        ),
    },
    "SC-200": {
        "title": 'SC-200 Practice Questions — {count} Qs for SOC Analyst (2026)',
        "description": (
            '{count} SC-200 practice questions for Security Operations Analyst. Defender XDR, Sentinel, KQL hunting, and incident response — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} SC-200 practice questions for Security Operations Analyst. Defender XDR, Sentinel, KQL hunting, and incident response — updated for the 2026 exam.'
        ),
    },
    "SC-300": {
        "title": 'SC-300 Practice Questions — {count} Qs for Identity Admin (2026)',
        "description": (
            '{count} SC-300 practice questions for Identity and Access Administrator. Entra ID, authentication, governance, and app access — updated for the 2026 exam.'
        ),
        "social_description": (
            '{count} SC-300 practice questions for Identity and Access Administrator. Entra ID, authentication, governance, and app access — updated for the 2026 exam.'
        ),
    },
    "SC-500": {
        "title": 'SC-500 Practice Questions — {count} Qs for Cloud Security (2026)',
        "description": (
            '{count} SC-500 practice questions for Cloud and AI Security Engineer — the AZ-500 successor. Identity, platform protection, and AI security, updated for 2026.'
        ),
        "social_description": (
            '{count} SC-500 practice questions for Cloud and AI Security Engineer — the AZ-500 successor. Identity, platform protection, and AI security, updated for 2026.'
        ),
    },
    "SC-900": {
        "title": 'SC-900 Practice Questions — {count} Qs for Security Basics (2026)',
        "description": (
            '{count} SC-900 practice questions for Security, Compliance, and Identity Fundamentals. Entra ID, Defender, and Purview basics — free to start on iPhone and iPad.'
        ),
        "social_description": (
            '{count} SC-900 practice questions for Security, Compliance, and Identity Fundamentals. Entra ID, Defender, and Purview basics — free to start on iPhone and iPad.'
        ),
    },
}
DEFAULT_APP_REPO = Path(
    os.environ.get("AZURE_MASTERY_APP_REPO", ROOT.parent / "AZ-104 Mastery")
)


def code_to_resource_name(code: str) -> str:
    return code.lower().replace("-", "") + "-questions.json"


def clean_text(value: str, limit: int | None = None) -> str:
    """Turn question-bank Markdown-ish prose into safe, compact HTML text."""
    value = re.sub(r"`([^`]+)`", r"\1", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    if limit and len(value) > limit:
        value = value[: limit - 1].rsplit(" ", 1)[0] + "…"
    return html.escape(value, quote=False)


def choose_question(questions: list[dict], format_name: str, *, options: bool = False) -> dict:
    candidates = [q for q in questions if q.get("format") == format_name]
    if options:
        candidates = [
            q for q in candidates
            if 3 <= len(q.get("options", [])) <= 6
            and all(len(o.get("text", "")) <= 105 for o in q.get("options", []))
        ]
    if not candidates:
        raise ValueError(f"question bank has no usable {format_name} sample")
    return min(
        candidates,
        key=lambda q: len(q.get("text", ""))
        + sum(len(o.get("text", "")) for o in q.get("options", [])),
    )


def option_list(question: dict, marker: str) -> str:
    correct = set(question.get("correctAnswers", []))
    items = []
    for option in question.get("options", []):
        selected = ' class="is-selected"' if option.get("id") in correct else ""
        items.append(
            f'              <li{selected}><span class="qt__viz-{marker}"></span>'
            f'{clean_text(option.get("text", ""), 90)}</li>'
        )
    return "\n".join(items)


def drag_sample(questions: list[dict]) -> tuple[str, list[str], str]:
    drag = next((q for q in questions if q.get("format") == "dragAndDrop" and q.get("options")), None)
    if drag:
        by_id = {o.get("id"): o.get("text", "") for o in drag.get("options", [])}
        ordered = [by_id[a] for a in drag.get("correctAnswers", []) if a in by_id]
        if len(ordered) < 3:
            ordered = [o.get("text", "") for o in drag.get("options", [])]
        return clean_text(drag.get("text", ""), 155), ordered[:5], "Drag-and-drop"

    match = choose_question(questions, "dragToMatch")
    sentences = [
        s.strip() for s in re.split(r"(?<=[.!?])\s+", match.get("explanation", ""))
        if len(s.strip()) > 15
    ]
    if len(sentences) < 3:
        sentences = [q.get("subTopic", q.get("domain", "Exam item")) for q in questions[:4]]
    return clean_text(match.get("text", ""), 155), sentences[:4], "Drag to match"


def interactive_sample(questions: list[dict]) -> tuple[str, str, str]:
    labels = {
        "hotArea": ("Hotspot", "Tap target"),
        "dropdownSelect": ("Dropdown selection", "Choose in context"),
        "dragToMatch": ("Drag to match", "Match concepts"),
    }
    for format_name in labels:
        sample = next((q for q in questions if q.get("format") == format_name), None)
        if sample:
            title, hint = labels[format_name]
            return clean_text(sample.get("text", ""), 170), title, hint
    raise ValueError("question bank has no interactive sample")


def case_sample(questions: list[dict]) -> tuple[str, str, list[str]]:
    case = choose_question(questions, "caseStudy")
    title = re.sub(r"^Case Study:\s*", "", case.get("text", ""), flags=re.I)
    sections = case.get("formatData", {}).get("sections", [])
    background = next(
        (s.get("content", "") for s in sections if s.get("title", "").lower() == "background"),
        case.get("explanation", ""),
    )
    by_id = {q.get("id"): q for q in questions}
    prompts = [
        by_id[qid].get("text", "")
        for qid in case.get("formatData", {}).get("subQuestionIDs", [])
        if qid in by_id
    ]
    if not prompts:
        requirements = next(
            (s.get("content", "") for s in sections if s.get("title", "").lower() == "requirements"),
            "",
        )
        prompts = [re.sub(r"^\d+[.)]\s*", "", line) for line in requirements.splitlines() if line.strip()]
    return clean_text(title, 80), clean_text(background, 170), prompts[:4]


def preview_articles(code: str, questions: list[dict]) -> str:
    single = choose_question(questions, "singleSelect", options=True)
    multi = choose_question(questions, "multiSelect", options=True)
    drag_prompt, drag_items, drag_title = drag_sample(questions)
    interactive_prompt, interactive_title, interactive_hint = interactive_sample(questions)
    case_title, case_background, case_prompts = case_sample(questions)
    case_intro = f"<strong>{case_title}</strong>" + (f" {case_background}" if case_background else "")

    single_correct = set(single.get("correctAnswers", []))
    wrong = next(o for o in single.get("options", []) if o.get("id") not in single_correct)
    rationale = single.get("optionRationales", {}).get(wrong.get("id"), single.get("explanation", ""))

    drag_html = "\n".join(
        '              <li><span class="qt__viz-drag-handle">⋮⋮</span>'
        f'<span class="qt__viz-drag-num">{i}</span>{clean_text(item, 72)}</li>'
        for i, item in enumerate(drag_items, 1)
    )
    case_html = "\n".join(
        '                <li><span class="qt__viz-case-num">'
        f'{i}</span>{clean_text(prompt, 82)}</li>'
        for i, prompt in enumerate(case_prompts, 1)
    )

    return f'''      <div class="question-types" data-preview-source="in-app-question-bank">

        <article class="qt">
          <div class="qt__viz" data-quiz="1">
            <p class="qt__viz-q">{clean_text(single.get("text", ""), 175)}</p>
            <ul class="qt__viz-options">
{option_list(single, "radio")}
            </ul>
          </div>
          <h3>Multiple choice</h3>
          <p>An original {code} practice-bank example with one correct answer. The app explains every option after you answer.</p>
          <span class="qt__hint">Exam-specific sample</span>
        </article>

        <article class="qt">
          <div class="qt__viz" data-quiz="1">
            <p class="qt__viz-q">{clean_text(multi.get("text", ""), 175)}</p>
            <ul class="qt__viz-options">
{option_list(multi, "checkbox")}
            </ul>
          </div>
          <h3>Multi-select</h3>
          <p>An original {code} multi-select practice item. Every required selection must be correct to earn the mark.</p>
          <span class="qt__hint">All-or-nothing</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <p class="qt__viz-q">{drag_prompt}</p>
            <ul class="qt__viz-drag">
{drag_html}
            </ul>
          </div>
          <h3>{drag_title}</h3>
          <p>An original {code} ordering prompt, rendered for touch on iPhone and iPad.</p>
          <span class="qt__hint">Interactive item</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <p class="qt__viz-q">{interactive_prompt}</p>
            <div class="qt__viz-hotspot">
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--1"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--2"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--3"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--4"></span>
              <span class="qt__viz-hotspot-mock-row qt__viz-hotspot-mock-row--5"></span>
              <span class="qt__viz-target"></span>
            </div>
          </div>
          <h3>{interactive_title}</h3>
          <p>An original {code} visual-context prompt, rendered for touch on iPhone and iPad.</p>
          <span class="qt__hint">{interactive_hint}</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <div class="qt__viz-case">
              <div class="qt__viz-case-scenario">
                {case_intro}
              </div>
              <ul class="qt__viz-case-questions">
{case_html}
              </ul>
            </div>
          </div>
          <h3>Case studies</h3>
          <p>An original {code} case-study scenario with linked questions that share the same requirements and environment.</p>
          <span class="qt__hint">Multi-question</span>
        </article>

        <article class="qt">
          <div class="qt__viz" aria-hidden="true">
            <div class="qt__viz-ai-wrong"><span class="qt__viz-ai-wrong-mark">✕</span>Your answer: {clean_text(wrong.get("text", ""), 72)}</div>
            <div class="qt__viz-ai-explain">
              <span class="qt__viz-ai-explain-mark">✨ Answer Coach:</span>{clean_text(rationale, 210)}
              <span class="qt__viz-ai-source">— grounded in authored certification guidance</span>
            </div>
          </div>
          <h3>Answer Coach</h3>
          <p>Answer Coach shows the correct reasoning and option-by-option rationale where available, then explains the misconception, key distinction, and rule to remember. Choose explanations after each question or at the end of a practice test; supported devices may optionally rewrite a note on-device only after grounding checks.</p>
          <span class="qt__hint qt__hint--purple">App exclusive</span>
        </article>

      </div>'''


def replace_once(text: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    text, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"expected one {label} replacement, found {count}")
    return text


def update_page(text: str, code: str, count: int, questions: list[dict], name: str) -> str:
    retired = RETIRED_EXAMS.get(code)
    retiring = RETIRING_EXAMS.get(code)
    if retired:
        replacement = retired["replacement"]
        title = f"{code} Retired Exam & {replacement} Next Step | Azure Mastery"
        description = (
            f"{code} retired on {retired['date']}. Review {count} practice questions and learn "
            f"about {replacement}, {retired['replacement_label']}."
        )
        social_description = (
            f"{code} retired on {retired['date']}. Keep {count} reference practice questions "
            f"and compare {replacement}, {retired['replacement_label']}."
        )
        h1 = f"{code} Retired Exam Practice &amp; Next Steps"
        feature_claim = f"{count} {code} reference practice questions mapped to the final Microsoft skills outline"
    elif retiring:
        replacement = retiring["replacement"]
        title = f"{code} Retirement & {replacement} Next Step | Azure Mastery"
        description = (
            f"{code} retires {retiring['date']}. Review {count} current practice questions or "
            f"move to {replacement}, {retiring['replacement_label']}."
        )
        social_description = (
            f"{code} retires {retiring['date']}. Prepare with {count} final-outline questions "
            f"or continue with {replacement}."
        )
        h1 = f"{code} Practice Questions &amp; {replacement} Next Step"
        feature_claim = f"{count} {code} practice questions mapped to the final Microsoft skills outline"
    else:
        active_seo = ACTIVE_SEO.get(code, {})
        title = active_seo.get(
            "title", f"{code} Practice Questions — {{count}} Qs & Exam Prep (2026)"
        ).format(count=count)
        description = active_seo.get(
            "description",
            (
                f"{{count}} {code} practice questions with Answer Coach rationales, adaptive "
                "study plans, and a full exam simulator — updated for the 2026 exam."
            ),
        ).format(count=count)
        social_description = active_seo.get(
            "social_description",
            (
                f"{count} {code} practice questions, private Answer Coach, adaptive study plans, "
                "and a full exam simulator. Free to start."
            ),
        ).format(count=count)
        h1 = f"{code} Practice Questions &amp; Exam Prep"
        feature_claim = f"{count} {code} practice questions mapped to the current Microsoft skills outline"
    keywords = (
        f"{code}, {code} practice questions, {code} exam prep, {code} practice test, "
        "Microsoft certification, iOS study app"
    )
    schema_keywords = (
        f"{code}, {code} practice questions, {code} exam prep, {code} mock exam, "
        "Microsoft certification, iOS study app, Answer Coach, adaptive study plan, exam score prediction"
    )

    text = replace_once(text, r"<title>.*?</title>", f"<title>{title}</title>", "title")
    text = replace_once(
        text, r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{description}">', "meta description",
    )
    text = replace_once(
        text, r'<meta name="keywords" content="[^"]*">',
        f'<meta name="keywords" content="{keywords}">', "meta keywords",
    )
    text = replace_once(
        text, r'<meta name="apple-itunes-app" content="[^"]*">',
        (
            '<meta name="apple-itunes-app" '
            f'content="app-id=6760594569, app-argument=azuremastery://exam/{code.lower()}">'
        ),
        "exam-scoped Smart App Banner",
    )
    text = replace_once(
        text, r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{title}">', "OpenGraph title",
    )
    text = replace_once(
        text, r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{social_description}">', "OpenGraph description",
    )
    text = replace_once(
        text, r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{title}">', "Twitter title",
    )
    text = replace_once(
        text, r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="{social_description}">', "Twitter description",
    )

    # Per-exam OG/Twitter card (Task A8). Guarded on the rendered JPEG actually
    # existing on disk, so a page is never pointed at an image that hasn't been
    # rendered yet -- run the social render in sync-marketing-counts.py first.
    # Pages this hasn't run for keep pointing at the shared images/og-image.png,
    # same as before this task.
    og_jpg = ROOT / "images" / "og" / f"{code.lower()}.jpg"
    if og_jpg.exists():
        image_url = f"https://azuremastery.app/images/og/{code.lower()}.jpg"
        alt = f"{code} — {html.escape(name, quote=False)} practice questions in Azure Mastery"
        text = replace_once(
            text, r'<meta property="og:image" content="[^"]*">',
            f'<meta property="og:image" content="{image_url}">', "OpenGraph image",
        )
        text = replace_once(
            text, r'<meta property="og:image:alt" content="[^"]*">',
            f'<meta property="og:image:alt" content="{alt}">', "OpenGraph image alt",
        )
        text = replace_once(
            text, r'<meta name="twitter:image" content="[^"]*">',
            f'<meta name="twitter:image" content="{image_url}">', "Twitter image",
        )
        text = text.replace(
            "<!-- OpenGraph / Twitter (cert-scoped title + description; reuses homepage OG image) -->",
            "<!-- OpenGraph / Twitter (cert-scoped title + description + per-exam card image) -->",
        )
        # og:image:width/height (Task A8 gap): apps/AzureMastery/og-exam.html
        # renders every per-exam card at a fixed 1200x630, same as the shared
        # og-image.html the homepage already declares these for -- see that
        # page's og:image block. Same exactly-once insert-or-replace shape as
        # og:image:type just below.
        if 'property="og:image:width"' in text:
            text = replace_once(
                text, r'<meta property="og:image:width" content="[^"]*">',
                '<meta property="og:image:width" content="1200">', "OpenGraph image width",
            )
        else:
            text = replace_once(
                text, r'(<meta property="og:image" content="[^"]*">\n)',
                r'\1  <meta property="og:image:width" content="1200">\n',
                "OpenGraph image width (insert)",
            )
        if 'property="og:image:height"' in text:
            text = replace_once(
                text, r'<meta property="og:image:height" content="[^"]*">',
                '<meta property="og:image:height" content="630">', "OpenGraph image height",
            )
        else:
            text = replace_once(
                text, r'(<meta property="og:image:width" content="[^"]*">\n)',
                r'\1  <meta property="og:image:height" content="630">\n',
                "OpenGraph image height (insert)",
            )
        if 'property="og:image:type"' in text:
            text = replace_once(
                text, r'<meta property="og:image:type" content="[^"]*">',
                '<meta property="og:image:type" content="image/jpeg">', "OpenGraph image type",
            )
        else:
            text = replace_once(
                text, r'(<meta property="og:image" content="[^"]*">\n)',
                r'\1  <meta property="og:image:type" content="image/jpeg">\n',
                "OpenGraph image type (insert)",
            )

    text = replace_once(
        text,
        r'("@type": "WebPage",.*?"name": ")[^"]*(",\s*"description": ")[^"]*(")',
        lambda m: m.group(1) + title.replace(" | Azure Mastery", "") + m.group(2) + description + m.group(3),
        "WebPage name and description",
        flags=re.S,
    )
    if code in ACTIVE_SEO:
        text = replace_once(
            text,
            r'("applicationSubCategory": "Exam Preparation",\s*"description": ")[^"]*(")',
            lambda m: m.group(1) + description + m.group(2),
            "SoftwareApplication description",
            flags=re.S,
        )
    updated_date = SEO_UPDATED_OVERRIDES.get(code, SEO_UPDATED)
    text = replace_once(
        text, r'("dateModified": ")\d{4}-\d{2}-\d{2}("\s*,)',
        rf'\g<1>{updated_date}\2', "dateModified",
    )
    text = replace_once(
        text, r'("keywords": ")[^"]*("\s*,\s*"featureList")',
        lambda m: m.group(1) + schema_keywords + m.group(2),
        "SoftwareApplication keywords",
        flags=re.S,
    )
    text = replace_once(
        text, rf'("featureList": \[\s*")\d+\s+{re.escape(code)}[^\"]*(")',
        rf'\g<1>{feature_claim}\2',
        "featureList question claim",
        flags=re.S,
    )
    if '"Private Answer Coach grounded in authored rationales"' not in text:
        text = replace_once(
            text,
            r'(\n\s*)("Knowledge decay tracking)',
            r'\1"Private Answer Coach grounded in authored rationales",\1\2',
            "Answer Coach feature claim",
            flags=re.S,
        )

    if "<strong>Answer Coach</strong>" not in text:
        answer_coach_copy = '''      <p>
        <strong>Answer Coach</strong> turns each missed answer into a private, grounded lesson: the misconception, key distinction, and rule to remember. It always uses authored certification guidance; on supported devices, an optional on-device model may rewrite the note only when it passes grounding checks.
      </p>
      <p>
        During your first week, <strong>Aura</strong> adapts the next step as you go. Every session ends with a concise recap of what changed, what to focus on, and the best follow-up.
      </p>
'''
        text = replace_once(
            text,
            r'(      <p>\s*Everything runs <strong>on-device</strong>\.)',
            answer_coach_copy + r'\1',
            "Answer Coach and Aura product copy",
            flags=re.S,
        )

    text = text.replace(
        "Everything runs <strong>on-device</strong>. Your answer history, your readiness gauge, your decay alerts — none of it leaves your iPhone or iPad. No account required to start, no tracking, no sync server. Privacy-first by design.",
        "Everything essential runs <strong>on-device</strong>. Your answer history, readiness gauge, and coaching stay private. Optional sync uses your private iCloud account; there is no Azure Mastery account, tracking, or external processing server.",
    )
    text = text.replace(
        " — all without sending a single byte off your device.",
        ". Core study stays on-device and works offline; optional sync uses your private iCloud account.",
    )
    text = text.replace(
        " All without sending a single byte off your device.",
        " Core study stays on-device and works offline; optional sync uses your private iCloud account.",
    )
    text = text.replace(
        "Everything runs on-device: your answer history and readiness gauge never leave your iPhone or iPad.",
        "Core study runs on-device and works offline; optional sync uses your private iCloud account.",
    )
    text = text.replace("/* Why Wrong AI */", "/* Answer Coach */")

    # Count corrections not covered by the existing sync script.
    text = re.sub(r"(full\s+)\d+(-question\s+bank)", rf"\g<1>{count}\2", text)

    # Make the visible primary heading match the high-intent query language.
    text = replace_once(
        text,
        rf'(<h1 class="display-large page-h1">\s*){re.escape(code)}.*?(—\s*<span class="page-h1-accent">)',
        rf'\g<1>{h1} \2',
        "page H1",
        flags=re.S,
    )

    # The two GitHub exam pages use a shorter layout without a preview section.
    if '<section id="question-types"' in text:
        preview = preview_articles(code, questions)
        text = replace_once(
            text,
            r'      <div class="question-types"(?: data-preview-source="[^"]+")?>.*?      </div>\s*</section>',
            preview + "\n    </section>",
            "question preview section",
            flags=re.S,
        )
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing files")
    parser.add_argument("--app-repo", type=Path, default=DEFAULT_APP_REPO)
    args = parser.parse_args()

    exam_data = json.loads(DATA_FILE.read_text())
    counts = exam_data["exams"]
    names = exam_data.get("names", {})
    changed: list[Path] = []

    for code, count in sorted(counts.items()):
        page = EXAMS_DIR / code.lower() / "index.html"
        resource = args.app_repo / "App" / "AzureMastery" / "Resources" / code_to_resource_name(code)
        if not page.exists() or not resource.exists():
            sys.exit(f"missing page or question bank for {code}: {page} / {resource}")
        questions = json.loads(resource.read_text())["questions"]
        before = page.read_text()
        after = update_page(before, code, count, questions, names.get(code, code))
        if after != before:
            changed.append(page)
            if not args.check:
                page.write_text(after)

    if changed:
        verb = "would update" if args.check else "updated"
        print(f"{verb} {len(changed)} files:")
        for path in changed:
            print(f"  {path.relative_to(ROOT)}")
        if args.check:
            sys.exit(1)
    else:
        print("SEO metadata and previews are in sync.")


if __name__ == "__main__":
    main()
