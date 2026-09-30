#!/usr/bin/env python3
"""Check discovery, index freshness, content exclusions, anchors and shared UI contracts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from search_common import ROOT, Document, clean, excluded, published_pages


def tool(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'Tools' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = tool('build-search-index')
ui = tool('sync-search-ui')
versions = tool('version-static-assets')


class SearchContracts(unittest.TestCase):
    def test_index_is_current_and_deterministic(self):
        expected = builder.rendered_index()
        self.assertEqual((ROOT / 'data/search-index.json').read_text(), expected)
        self.assertEqual(expected, builder.rendered_index())

    def test_published_destinations_and_anchors(self):
        data = builder.build_index()
        pages = dict(published_pages())
        self.assertEqual({e['url'].split('#')[0] for e in data['entries']}, set(pages))
        for entry in data['entries']:
            path, _, anchor = entry['url'].partition('#')
            self.assertIn(path, pages)
            if anchor:
                document = Document(pages[path].read_text()).root
                self.assertIsNotNone(document.find(lambda n: n.attrs.get('id') == anchor))
            if 'successor' in entry:
                self.assertIn(entry['successor']['url'], pages)

    def test_chrome_and_promotional_content_excluded(self):
        document = Document('<main><h1>Useful subject</h1><nav>Navigation noise</nav>'
                            '<section id="how-helps"><h2>Repeated product pitch</h2></section>'
                            '<div class="am-search">Search chrome</div><p>Private networking</p>'
                            '<script>secretNoise</script><footer>Footer noise</footer></main>').root
        self.assertEqual(clean(document.text(excluded)), 'Useful subject Private networking')
        self.assertEqual([clean(n.text()) for n in document.all(lambda n:n.tag == 'h2', excluded)], [])

    def test_new_sitemap_page_discovered_without_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'guides/new-topic').mkdir(parents=True)
            (root / 'guides/new-topic/index.html').write_text('<main><h1>New subject</h1></main>')
            (root / 'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://azuremastery.app/guides/new-topic/</loc></url></urlset>')
            (root / 'data').mkdir()
            (root / 'data/exam-counts.json').write_text((ROOT / 'data/exam-counts.json').read_text())
            self.assertEqual(builder.build_index(root)['entries'][0]['url'], '/guides/new-topic/')

    def test_shared_ui_idempotence_and_accessibility(self):
        for _, page in published_pages():
            text = page.read_text()
            self.assertEqual(ui.render_page(page, text), text, page)
            document = Document(text).root
            ids = [n.attrs['id'] for n in document.all(lambda n: 'id' in n.attrs)]
            self.assertEqual(len(ids), len(set(ids)), f'Duplicate IDs: {page}')
            self.assertEqual(text.count('data-search-open'), 1)
            self.assertEqual(text.count('id="am-search-dialog"'), 1)
            self.assertIn('aria-labelledby="am-search-title"', text)
            self.assertIn('aria-live="polite"', text)
            self.assertEqual(versions.render(page, text), text, f'Unversioned search assets: {page}')

    def test_published_exam_metadata_matches_snapshot(self):
        entries = [e for e in builder.build_index()['entries'] if e['kind'] == 'exam']
        snapshot = json.loads((ROOT / 'data/exam-counts.json').read_text())
        self.assertEqual({e['examCodes'][0] for e in entries}, set(snapshot['names']))
        for entry in entries:
            code = entry['examCodes'][0]
            self.assertIn(snapshot['names'][code], entry['title'])
            self.assertEqual(entry['status'] != 'current', code in snapshot['retired'])


if __name__ == '__main__':
    unittest.main()
