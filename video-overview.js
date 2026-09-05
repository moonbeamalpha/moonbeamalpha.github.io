(() => {
  'use strict';
  const host = document.querySelector('[data-overview-player]');
  if (!host) return;
  const button = host.querySelector('button');
  button.hidden = false;
  button.addEventListener('click', () => {
    const player = document.createElement('iframe');
    player.title = 'Azure Mastery — Know When You’re Ready';
    player.src = 'https://www.youtube-nocookie.com/embed/-wVWR3WAOHM?autoplay=1&playsinline=1&rel=0';
    player.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
    player.referrerPolicy = 'strict-origin-when-cross-origin';
    player.allowFullscreen = true;
    host.replaceChildren(player);
    player.focus();
  }, { once: true });
})();
