#!/usr/bin/env python3
"""Check the decision path, complete authored previews and static App Store handoff."""
import html
import importlib.util
import json
import re
import unittest
import tempfile
from urllib.parse import urlsplit, parse_qs
from search_common import ROOT, Document, clean, published_pages


def tool(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'Tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


conversion = tool('sync-conversion-ui')
seo = tool('optimise-marketing-seo')


class ConversionContracts(unittest.TestCase):
    def test_home_decision_path_and_current_cards(self):
        source = (ROOT / 'index.html').read_text(); doc = Document(source).root
        positions = [source.index('id="' + id + '"') for id in ['hero', 'features', 'exam-roadmap', 'try-a-question', 'pricing']]
        self.assertEqual(positions, sorted(positions))
        snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
        cards = list(doc.all(lambda n: 'exam-finder__card' in n.attrs.get('class', '').split()))
        self.assertEqual({n.attrs['href'].split('/')[-2].upper() for n in cards}, set(snapshot['exams']) - set(snapshot['retired']))
        for card in cards:
            code = card.attrs['href'].split('/')[-2].upper()
            self.assertIn(snapshot['names'][code].removeprefix('Microsoft '), clean(card.text()))

    def test_static_links_have_placement_and_provider(self):
        for _, page in published_pages():
            for link in Document(page.read_text()).root.all(lambda n: n.tag == 'a'):
                url = urlsplit(link.attrs.get('href', ''))
                if url.hostname != 'apps.apple.com': continue
                self.assertRegex(url.path, r'^/(?:gb/app/azure-mastery|app)/id6760594569$', page)
                query = parse_qs(url.query)
                self.assertEqual(query.get('pt'), ['128558698'], page)
                self.assertEqual(query.get('mt'), ['8'], page)
                self.assertTrue(0 < len(query.get('ct', [''])[0]) <= 30, page)

    def test_preview_has_full_prompt_and_every_rationale(self):
        samples = json.loads((ROOT / 'data/practice-previews.json').read_text())
        destinations = [(ROOT / 'exams' / code.lower() / 'index.html', questions) for code, questions in samples.items()]
        home_samples = json.loads((ROOT / 'data/home-practice.json').read_text())
        destinations.append((ROOT / 'index.html', [q for questions in home_samples.values() for q in questions]))
        for page, questions in destinations:
            source = page.read_text(); doc = Document(source).root
            if page.parent.name != ROOT.name:
                self.assertLess(source.index('id="question-types"'), source.index('id="what-is"'), page)
            for question in questions:
                quiz = doc.find(lambda n: n.attrs.get('data-question-id') == question['id'])
                self.assertIsNotNone(quiz, (page, question['id']))
                stem = quiz.find(lambda n: 'qt__viz-q' in n.attrs.get('class', '').split())
                self.assertEqual(clean(stem.text()), html.unescape(seo.clean_text(question['text'])))
                if question.get('context'):
                    self.assertIn(html.unescape(seo.clean_text(question['context'])), clean(quiz.text()))
                rationales = list(quiz.all(lambda n: 'qt__rationale' in n.attrs.get('class', '').split()))
                self.assertEqual(len(rationales), len(question['options']))
                for node, option in zip(rationales, question['options']):
                    self.assertEqual(clean(node.text()), html.unescape(seo.clean_text(question['optionRationales'][option['id']])))
            self.assertIn('<noscript><details class="qt__answer-fallback">', source)

    def test_selection_avoids_dependent_scenarios(self):
        full = {'id':'standalone', 'format':'singleSelect', 'text':'A complete self-contained question.',
                'options':[{'id':letter,'text':letter} for letter in 'ABC'], 'optionRationales':dict.fromkeys('ABC','Written reasoning')}
        dependent = dict(full, id='dependent', text='Which service?', caseStudyParentID='missing-case')
        self.assertEqual(seo.choose_question([dependent,full], 'singleSelect', options=True)['id'], 'standalone')

    def test_attribution_preserves_explicit_campaign_and_storefront(self):
        original = '<a class="btn-primary" href="https://apps.apple.com/gb/app/azure-mastery/id6760594569?ct=site-pro-options">Pro</a>'
        result = conversion.campaign_links(original, 'index.html')
        url = urlsplit(Document(result).root.find(lambda n: n.tag == 'a').attrs['href'])
        self.assertEqual(url.path, '/gb/app/azure-mastery/id6760594569')
        self.assertEqual(parse_qs(url.query)['ct'], ['site-pro-options'])
        self.assertEqual(conversion.campaign_links(result, 'index.html'), result)

    def test_measured_pages_include_one_download_handler(self):
        for _, page in published_pages():
            text = page.read_text()
            if re.search(r'gtag\([\'"]config[\'"]', text):
                self.assertEqual(len(re.findall(r'<script src="/app-store-links\.js', text)), 1, page)

    def test_generated_chrome_does_not_exempt_editorial_text(self):
        similarity = tool('check-page-similarity')
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.html') as fixture:
            fixture.write('<!-- conversion-hero:start -->\n' + conversion.EXAM_HERO_CHROME + '\n<!-- conversion-hero:end --><p>Distinct exam objectives</p>'); fixture.flush()
            self.assertEqual(similarity.extract_words(fixture.name), ['distinct', 'exam', 'objectives'])
            fixture.seek(0); fixture.truncate(); fixture.write('<!-- conversion-hero:start -->Injected editorial guidance<!-- conversion-hero:end -->'); fixture.flush()
            self.assertIn('injected', similarity.extract_words(fixture.name))
        home = (ROOT / 'index.html').read_text(); snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
        for _, page in published_pages():
            self.assertEqual(conversion.render(page,page.read_text(),snapshot,conversion.exam_metadata(home)),page.read_text(),page)

    def test_aggregate_measurement_preserves_unknown_values(self):
        report = tool('report-download-funnel')
        rows = report.aggregate([{'link_url':'https://apps.apple.com/app/id6760594569?ct=site-home-hero&pt=128558698', 'clicks':'20'},
                                 {'link_url':'https://example.com/?ct=site-home-hero','clicks':'100'},
                                 {'link_url':'https://apps.apple.com/app/id6760594569?ct=site-pro-options&pt=128558698','clicks':'7'}],
                                [{'campaign':'site-home-hero','first_time_downloads':'5'}, {'campaign':'site-home-qr','first_time_downloads':'8'},
                                 {'campaign':'site-pro-options','first_time_downloads':''}])
        self.assertEqual(rows[0]['downloads_per_click'], .25)
        self.assertEqual(rows[1]['outbound_clicks'], '')
        self.assertEqual(rows[2]['first_time_downloads'], '')
        named_rows = report.aggregate([{'store_campaign': 'site-home-hero', 'clicks': '20'}], [{'campaign': 'site-home-hero', 'first_time_downloads': '5'}])
        self.assertEqual(named_rows[0]['downloads_per_click'], .25)


if __name__ == '__main__':
    unittest.main()
