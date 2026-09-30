"""Shared, dependency-free discovery and HTML reading for public site search."""
from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def find(self, predicate):
        if predicate(self):
            return self
        return next((found for child in self.children if isinstance(child, Node)
                     if (found := child.find(predicate))), None)

    def all(self, predicate, excluded=None):
        if excluded and excluded(self):
            return
        if predicate(self):
            yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.all(predicate, excluded)

    def text(self, excluded=None):
        if excluded and excluded(self):
            return ''
        return ' '.join(child.text(excluded) if isinstance(child, Node) else child
                        for child in self.children)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node('document')
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def clean(value):
    return re.sub(r'\s+', ' ', value).strip()


def published_pages(root=ROOT):
    """Use canonical sitemap paths, scoped to the Azure Mastery site."""
    pages = []
    for node in ET.parse(root / 'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        url = urlsplit(node.text)
        if url.hostname != 'azuremastery.app':
            continue
        path = url.path
        if path.startswith('/apps/') and path not in {
            '/apps/AzureMastery/support.html', '/apps/AzureMastery/privacy.html',
            '/apps/AzureMastery/terms.html',
        }:
            continue
        file = root / path.lstrip('/')
        if path.endswith('/'):
            file /= 'index.html'
        if not file.is_file() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Missing or invalid published search page: {path}')
        pages.append((path, file))
    if len({path for path, _ in pages}) != len(pages):
        raise ValueError('Duplicate sitemap paths')
    return sorted(pages)


def excluded(node):
    classes = node.attrs.get('class', '').split()
    return (node.tag in {'script', 'style', 'svg', 'noscript', 'nav', 'header', 'footer', 'button'}
            or node.attrs.get('aria-hidden') == 'true'
            or node.attrs.get('id') in {'how-helps', 'question-types', 'cert-paths', 'related', 'guides', 'faqs'}
            or any(c.startswith(('am-search', 'social-follow', 'exam-inline-cta', 'guide-inline-cta',
                                  'mobile-cta-bar', 'cta-band', 'cta-final', 'question-types', 'qt__')) for c in classes))


def content_root(document):
    return (document.find(lambda n: n.tag == 'main')
            or document.find(lambda n: 'container' in n.attrs.get('class', '').split())
            or document.find(lambda n: n.tag == 'body'))
