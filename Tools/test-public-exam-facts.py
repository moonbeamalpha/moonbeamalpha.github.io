#!/usr/bin/env python3
"""Regressions for reviewed public exam facts; no app checkout or network needed.

The dated receipt records official evidence, not app catalogue values. Recheck
sources when changing facts. These checks do not certify question-bank alignment.
"""
import html
import json
import re
import unittest
from datetime import datetime
from pathlib import Path

from search_common import Document, clean, published_pages
from importlib.machinery import SourceFileLoader

ROOT = Path(__file__).resolve().parent.parent
FACTS = json.loads((ROOT / 'Tools/public-exam-facts-20261012.json').read_text())
conversion = SourceFileLoader('public_conversion', str(ROOT / 'Tools/sync-conversion-ui.py')).load_module()


def page(code):
    return (ROOT / 'exams' / code.lower() / 'index.html').read_text()


def section(source, identifier):
    return re.search(r'<section\b[^>]*id="' + identifier + r'".*?</section>', source, re.S)[0]


def visible(source):
    source = re.sub(r'<script\b.*?</script>', '', source, flags=re.S)
    return clean(Document(source).root.text())


class PublicExamFacts(unittest.TestCase):
    def test_official_assessment_durations_across_pages_and_guides(self):
        for code, fact in FACTS['assessmentDurations'].items():
            with self.subTest(code=code):
                value = re.search(r'>Duration</span><span[^>]+>(.*?)</span>', page(code))[1]
                self.assertEqual(value, f"{fact['minutes']} minutes")
                self.assertNotRegex(visible(page(code)), r'100[- ]minute(?:s)?|100-min duration')
        for slug in ['how-to-pass-ab-620', 'how-to-pass-ai-103', 'how-to-pass-ai-200', 'how-to-pass-sc-500']:
            source = (ROOT / 'guides' / slug / 'index.html').read_text()
            self.assertIn('>120 minutes</span>', source)
        for slug in ['ai-103-vs-ai-200', 'ab-620-vs-ab-410']:
            source = (ROOT / 'guides' / slug / 'index.html').read_text()
            self.assertNotIn('100 minutes', source)

    def test_role_based_seat_time_is_not_promised(self):
        for _, file in published_pages():
            self.assertNotRegex(file.read_text(), r'\((?:120|140)[- ](?:min(?:ute)?s?|minute)[- ]seat\)', str(file))

    def test_future_dates_are_separate_from_document_updates(self):
        for code, fact in FACTS['futureEnglishOutlines'].items():
            source = page(code)
            notice = re.search(r'<p id="blueprint-notice".*?</p>', source, re.S)[0]
            self.assertIn(f'data-blueprint-effective="{fact["effectiveDate"]}"', notice)
            self.assertIn('Earlier sittings use the preceding outline', notice)
            self.assertIn('document update', notice)
            self.assertIn(fact['sourceURL'], notice)
            date = datetime.strptime(fact['effectiveDate'], '%Y-%m-%d').strftime('%-d %B %Y')
            self.assertIn(date, notice)
            self.assertIn(date, next(x for x in (ROOT / 'llms.txt').read_text().splitlines() if x.startswith('- [' + code)))

    def test_undated_guides_do_not_gain_effective_dates(self):
        for code, fact in FACTS['undatedSkillsGuides'].items():
            source = page(code)
            self.assertNotIn('Skills measured ·', source)
            date = datetime.strptime(fact['documentUpdated'], '%Y-%m-%d').strftime('%-d %B %Y')
            self.assertIn('guide updated ' + date, source)
        self.assertNotIn('26 July 2026', page('AI-300'))
        self.assertNotIn('30–40', visible(page('AB-731')))

    def test_sc500_is_a_qualifying_path_to_sc100(self):
        source = page('SC-100')
        for area in ['cert-paths', 'related']:
            self.assertIn('href="/exams/sc-500/"', section(source, area))
        for source in [page('SC-500'), (ROOT / 'guides/sc-500-vs-az-500/index.html').read_text()]:
            text = visible(source)
            self.assertNotRegex(text, r'(?:does not|doesn.t) (?:currently )?list SC-500|not SC-500|Not currently\.')
            self.assertIn('SC-100', text)
        path = next(x for x in re.findall(r'<article class="cert-path">.*?</article>', page('SC-500'), re.S)
                    if 'href="/exams/sc-100/"' in x)
        self.assertNotIn('href="/exams/sc-200/"', path)

    def test_expert_credential_prerequisites_are_not_optional(self):
        text = visible(page('AB-100'))
        self.assertIn('passing AB-100 alone does not earn the Expert credential', text)
        self.assertIn('at least one qualifying Associate certification', text)
        self.assertNotIn('the single exam that earns', visible(page('AZ-305')))
        for article in re.findall(r'<article class="cert-path">.*?</article>', page('AI-500'), re.S):
            if '<span class="cert-path__chip-code">AI-500</span>' in article:
                self.assertIn('href="/exams/ai-103/"', article)
        self.assertNotIn('single exam earns', (ROOT / 'llms.txt').read_text())

    def test_authored_roadmap_and_generated_classification_agree(self):
        home = (ROOT / 'index.html').read_text()
        metadata = conversion.exam_metadata(home)
        self.assertEqual(metadata['PL-900'][0], 'Fundamentals')
        self.assertEqual(metadata['GH-300'][0], 'Associate')  # shared Associate / Intermediate row
        snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
        self.assertEqual(conversion.exam_tier('GH-300', snapshot, metadata)[1], 'Intermediate')
        for source in [home, (ROOT / 'exams/index.html').read_text()]:
            card = next(n for n in Document(source).root.all(lambda n: n.tag == 'a')
                        if n.attrs.get('href') == '/exams/gh-300/' and
                        any('certification-badge' in b.attrs.get('class', '').split()
                            for b in n.all(lambda b: b.tag == 'span')))
            self.assertIsNotNone(card.find(lambda n: n.attrs.get('data-tier') == 'INTERMEDIATE'))
            self.assertIn('Intermediate', clean(card.text()))

    def test_pl900_keeps_power_pages_business_value(self):
        text = visible(page('PL-900'))
        self.assertIn('standalone Power Pages domain was removed', text)
        self.assertIn('Power Pages business value remains', text)
        self.assertNotIn('five joint-heaviest', text)
        self.assertIn('four areas weighted 20–25%', text)

    def test_github_renewal_policy_is_credential_specific(self):
        foundations = visible(page('GH-900'))
        self.assertIn('renewal is not required', foundations)
        self.assertNotRegex(foundations, r'valid for (?:two|2) years|re-sit GH-900')
        copilot = visible(page('GH-300'))
        for fact in ['two-year validity', 'six-month extension', 'already-expired credential', 'learn@github.com']:
            self.assertIn(fact, copilot)
        self.assertNotIn('renewed by re-examination', copilot)

    def test_no_invented_beta_graduation(self):
        text = visible(page('AI-500'))
        self.assertNotIn('currently in beta', text)
        self.assertNotIn('scores are released after', text)
        self.assertIn('without a beta label', text)
        self.assertIn('currently a beta exam', visible(page('AB-650')))
        self.assertNotIn('Became generally available on', (ROOT / 'guides/how-to-pass-sc-500/index.html').read_text())

    def test_review_and_retake_guidance_is_not_universal_one_way(self):
        for code in json.loads((ROOT / 'data/exam-counts.json').read_text())['exams']:
            text = visible(page(code))
            self.assertNotRegex(text, r'flag-and-review (?:off|switched off|turned off)|no flicking back|no jumping back to flag-and-review', code)
            self.assertNotIn('Second and third retakes', text, code)
            self.assertNotIn('fifth retakes', text, code)

    def test_internal_navigation_targets_exist(self):
        from urllib.parse import urlsplit, unquote
        for _, file in published_pages():
            for href in re.findall(r'href="([^"]+)"', file.read_text()):
                url = urlsplit(html.unescape(href))
                if url.scheme or url.netloc or not href.startswith(('/', '#')):
                    continue
                target = ROOT / unquote(url.path.lstrip('/')) if url.path else file
                if target.is_dir():
                    target /= 'index.html'
                if target.suffix != '.html':
                    continue
                self.assertTrue(target.exists(), (file, href))
                if url.fragment:
                    self.assertRegex(target.read_text(), r'\bid=[\'"]' + re.escape(url.fragment) + r'[\'"]', (file, href))


if __name__ == '__main__':
    unittest.main()
