#!/usr/bin/env python3
"""Self-test for sync-marketing-counts.py's per-domain count patching (Task B3a).

Exercises patch_domain_counts() and check_domain_mismatches() in isolation,
against in-memory HTML fixtures rather than the real exams/ tree, so it stays
cheap and doesn't depend on the app repo. Run directly:

  python3 Tools/test-domain-counts.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def _load_sync_tool():
    # Filename has a hyphen, so it can't be a plain `import` -- load by path,
    # same trick validate-marketing-seo.py uses for update-sitemap-lastmod.py.
    path = os.path.join(ROOT, "sync-marketing-counts.py")
    spec = importlib.util.spec_from_file_location("sync_marketing_counts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sync = _load_sync_tool()

failures = []


def check(label: str, condition: bool) -> None:
    status = "ok" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        failures.append(label)


print("patch_domain_counts:")

# A span whose domain id is in the snapshot gets its digits rewritten, and the
# surrounding tag is left byte-for-byte otherwise.
page = ('<article class="domain"><p class="domain__inventory">'
        '<span class="domain__count" data-domain="az104-identity">0</span> '
        'exam-scoped practice questions in the app</p></article>')
text, seen = sync.patch_domain_counts(page, {"az104-identity": 85})
check("known domain id is rewritten to the snapshot count",
      '<span class="domain__count" data-domain="az104-identity">85</span>' in text)
check("seen returns exactly the ids found on the page", seen == {"az104-identity"})

# A page with two spans, one matched and one not in the snapshot: the matched
# one is rewritten, the unmatched one is left untouched (never a guessed or
# zeroed number) -- check_domain_mismatches() is what surfaces the gap.
page2 = ('<span class="domain__count" data-domain="az104-identity">0</span>'
         '<span class="domain__count" data-domain="az104-typo">0</span>')
text2, seen2 = sync.patch_domain_counts(page2, {"az104-identity": 85})
check("matched span rewritten in a mixed page",
      '<span class="domain__count" data-domain="az104-identity">85</span>' in text2)
check("unmatched span left untouched (still 0)",
      '<span class="domain__count" data-domain="az104-typo">0</span>' in text2)
check("seen includes both ids, matched and unmatched",
      seen2 == {"az104-identity", "az104-typo"})

# A page with no domain__count span at all (every page today) is a no-op.
page3 = '<p>Around 8-15 questions per sitting.</p>'
text3, seen3 = sync.patch_domain_counts(page3, {"az104-identity": 85})
check("page without any span is returned unchanged", text3 == page3)
check("seen is empty for a page with no span", seen3 == set())


print("check_domain_mismatches:")


class FakePatcher:
    def __init__(self):
        self.problems = 0


# Page ids exactly match the snapshot -> no problems, exit-worthy state clean.
p = FakePatcher()
sync.check_domain_mismatches(
    p,
    domain_counts_all={"AZ-104": {"az104-identity": 85, "az104-storage": 104}},
    page_domains={"AZ-104": {"az104-identity", "az104-storage"}},
)
check("matching ids on both sides raise no problems", p.problems == 0)

# Page carries a domain id absent from the snapshot (typo, or a domain the
# snapshot doesn't know) -> one problem, and it must exit 1 under --check per
# the brief.
p = FakePatcher()
sync.check_domain_mismatches(
    p,
    domain_counts_all={"AZ-104": {"az104-identity": 85}},
    page_domains={"AZ-104": {"az104-identity", "az104-bogus"}},
)
check("a page domain id missing from the snapshot is one problem", p.problems == 1)

# Snapshot has a domain the page never rendered a span for -> also one problem.
p = FakePatcher()
sync.check_domain_mismatches(
    p,
    domain_counts_all={"AZ-104": {"az104-identity": 85, "az104-storage": 104}},
    page_domains={"AZ-104": {"az104-identity"}},
)
check("a snapshot domain missing from the page is one problem", p.problems == 1)

# A page with an empty seen-set (no domain__count span at all) is skipped
# entirely, even if the snapshot has domains for that exam and even for a code
# the snapshot has never heard of (a retired exam with no scorecard) --
# untouched pages must never fail.
p = FakePatcher()
sync.check_domain_mismatches(
    p,
    domain_counts_all={"AZ-104": {"az104-identity": 85}},
    page_domains={"AZ-104": set(), "AI-102": set()},
)
check("pages with no domain__count span are never flagged", p.problems == 0)

print()
if failures:
    print(f"{len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("all checks passed.")
