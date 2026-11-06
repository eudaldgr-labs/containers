(() => {
  const storageKey = 'vegops-report-theme';
  const preferences = ['light', 'auto', 'dark'];
  const root = document.documentElement;
  const button = document.getElementById('theme-toggle');
  const label = document.querySelector('[data-theme-label]');
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  let preference = 'auto';
  try {
    const saved = localStorage.getItem(storageKey);
    if (preferences.includes(saved)) preference = saved;
  } catch (_) {}

  const apply = () => {
    if (preference === 'auto') delete root.dataset.theme;
    else root.dataset.theme = preference;
    button.dataset.themePreference = preference;
    label.textContent = preference[0].toUpperCase() + preference.slice(1);
    const next = preferences[(preferences.indexOf(preference) + 1) % preferences.length];
    const effective = preference === 'auto' ? (media.matches ? 'dark' : 'light') : preference;
    button.setAttribute('aria-label', `Color theme: ${preference}. Currently ${effective}. Switch to ${next}.`);
  };
  button.addEventListener('click', () => {
    preference = preferences[(preferences.indexOf(preference) + 1) % preferences.length];
    try {
      if (preference === 'auto') localStorage.removeItem(storageKey);
      else localStorage.setItem(storageKey, preference);
    } catch (_) {}
    apply();
  });
  media.addEventListener('change', apply);
  apply();
})();
