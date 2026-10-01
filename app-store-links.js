/* Only public App Store placement tags are measured. Never search text or answers. */
(function () {
  'use strict';
  if (['localhost', '127.0.0.1'].includes(location.hostname)) return;
  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href]');
    if (!link || typeof window.gtag !== 'function') return;
    var url;
    try { url = new URL(link.href); } catch (_) { return; }
    if (url.hostname !== 'apps.apple.com' || !/\/id6760594569(?:\/|$)/.test(url.pathname)) return;
    var campaign = url.searchParams.get('ct') || 'site-untagged';
    if (!/^[a-z0-9-]{1,30}$/.test(campaign)) return;
    window.gtag('event', 'app_store_click', {store_campaign: campaign, transport_type: 'beacon'});
  });
})();
