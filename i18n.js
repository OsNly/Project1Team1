const switcher = document.getElementById('lang-switch');
switcher.addEventListener('change', () => {
  const lang = switcher.value;
  const params = new URLSearchParams(window.location.search);
  params.set('lang', lang);
  window.location.search = params.toString();
});
