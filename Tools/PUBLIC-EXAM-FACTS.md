# Public exam copy review — 12 October 2026

This change reviews website facts against current official credential pages,
study guides, and policies. It does not audit question banks or deploy the site.
This content-only change starts from production `main` at
`ed71707123a0de6baaa8466885334b29c9d2b845`. Earlier draft #64 was stacked on
#63 and therefore inherited unapproved count updates; it is superseded by this
main-based review. Current live LLM counts were checked against main and match
all 35 exam pages: 12,758 exam-scoped questions, 12,700+ label, 30 exams and 29
paths. No app export is consumed. All images, count snapshots and practice
preview sources remain byte-identical to production. New counts must wait for
an App Store-approved release and Chris's explicit authorization.

`public-exam-facts-20261012.json` is a dated evidence receipt for public-copy
regressions. It is not a replacement for the app's canonical catalogue. Source
hashes identify the fetched official HTML; change facts only after rechecking
their sources. Run `python3 Tools/test-public-exam-facts.py` without network or
an app checkout. CI also runs it.

## Verified corrections

- **Assessment time:** AB-410, AB-620, AI-103, AI-200, AI-300, DP-750, DP-800,
  and SC-500 credential pages each state 120 minutes. The receipt records each
  URL. Page facts, relevant guide comparisons, FAQs, and pacing plans now agree.
  Practice plans use 120-minute study blocks without promising a different app
  simulator setting. Fixed role-based seat times were removed: Microsoft's
  [exam-experience policy](https://learn.microsoft.com/en-us/credentials/support/exam-duration-exam-experience)
  distinguishes assessment time, seat time, labs, and accommodations. Registration
  and sitting instructions determine the actual time.
- **Credential prerequisites:**
  [Azure Solutions Architect Expert](https://learn.microsoft.com/en-us/credentials/certifications/azure-solutions-architect/)
  requires Azure Administrator Associate alongside AZ-305;
  [DevOps Engineer Expert](https://learn.microsoft.com/en-us/credentials/certifications/devops-engineer/)
  requires a qualifying Associate credential alongside AZ-400.
  [Cybersecurity Architect Expert](https://learn.microsoft.com/en-us/credentials/certifications/cybersecurity-architect-expert/)
  accepts SC-500, SC-200, or SC-300. SC-500 and SC-100 prose, diagrams, and related
  links now agree. The retired AZ-500 reference page is preserved.
  [Agentic AI Business Solutions Architect Expert](https://learn.microsoft.com/en-us/credentials/certifications/agentic-ai-business-solutions-architect/)
  requires one qualifying Associate credential; its page links the full official
  list. Both engineering routes to
  [Multi-Agent AI Solutions Expert](https://learn.microsoft.com/en-us/credentials/certifications/multi-agent-ai-solutions-expert/)
  include AI-103. An Expert exam pass is separate from meeting credential requirements.
- **Classification:** PL-900 is in the authored Fundamentals roadmap row.
  GitHub Copilot is Intermediate, represented in the Associate / Intermediate row
  and generated cards. AZ-700's LLM summary agrees with the official
  [Azure Network Engineer Associate](https://learn.microsoft.com/en-us/credentials/certifications/azure-network-engineer-associate/)
  title. App-derived counts were preserved.
- **Renewal:**
  [GitHub Foundations](https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/)
  requires no renewal.
  [GitHub Copilot](https://learn.microsoft.com/en-us/credentials/certifications/github-copilot/)
  has a two-year validity period and a transition to Microsoft recertification,
  with six-month extensions for credentials expiring before the new process is
  available and a voucher route for already-expired credentials. Expiration and
  renewal deadlines should be checked in the holder's profile.
  [Credential retirement](https://learn.microsoft.com/en-us/credentials/support/credential-retirement)
  retains earned credentials as active until expiry and historical afterward;
  [renewal guidance](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification-faq)
  distinguishes certification retirement and final renewal deadlines from
  retirement of an exam. The unsupported inference that Beginner AB-731 means
  lifetime validity was removed; its profile is the authority for validity.
- **Blueprint prose:** the
  [PL-900 July 24 outline](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-900)
  retains Power Pages business value after removing its standalone domain. Four
  domains have 20–25% weights; business value is 5–10%. The
  [AI-200 outline](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200)
  has four areas, reflected in its introduction. The
  [DP-700 audience profile](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
  includes SQL, PySpark, and KQL. AI-500 summaries no longer claim shortened
  subgroup headings are verbatim. AI-300's guide was updated March 5, not July 26.
- **Navigation and retakes:** exam instructions support marking and review with
  restrictions after breaks and certain section transitions; public copy no
  longer says disabling review universally matches the real exam. The
  [retake policy](https://learn.microsoft.com/en-us/credentials/support/retake-policy)
  specifies 24 hours after the first failure, 14 days for subsequent attempts,
  and five total attempts within 12 months of the first attempt. The AB-650 beta
  exception remains. AI-500's current pages omit the beta label; no graduation
  date was inferred. Unsupported SC-500 July availability predictions were removed.

## Dates and future revisions

The ten upcoming English revisions are AB-100 / AB-900 (October 14), DP-700 /
DP-750 / DP-800 (October 19), SC-100 / SC-200 / SC-900 (October 21), DP-300
(October 27), and SC-300 (October 28). Each page links its guide and distinguishes
the effective date from the document update. Earlier sittings use the preceding
outline; localized versions can differ. Domain weights are unchanged by this
patch. Notices do not claim question-bank adoption or semantic review.

The published guides for AB-410, AB-650, AI-200, AI-300, AI-500, and SC-500 have
undated Skills measured headings. Their visible document update dates are
described as document updates, not silently promoted to effective dates.

## App coordination and review limits

The app metadata task owns timer changes, prerequisite registries, classification,
lifecycle, blueprint adoption and regenerated exports. This website patch consumes
none of its in-progress exports. The production/main count snapshot remains unchanged.
The primary dirty checkout is untouched. The separate app task owns app metadata, review-evidence repair and release
readiness. These website content corrections do not publish its unreleased counts.

Parent-thread messaging returned `thread not found` in this execution environment;
the final handoff carries these dependencies. Future notices can be updated once
the app task provides verified adoption evidence. The owner authorized deployment of these content-only corrections after count
parity and CI verification. The old count stack remains unmerged.

## Production count freeze

`production-count-freeze-20261012.json` records the checked live/main baseline.
`test-production-count-freeze.py` checks all exam totals and aggregate labels,
requires byte equality for the generated snapshot and practice-preview sources,
and protects every social image hash. The normal count tool is run from this
frozen website snapshot, with no `--refresh` or app-repo input. Generated FAQ,
search, cache references, LLM text and editorial/sitemap dates are updated while
all advertised question counts remain at production values.
