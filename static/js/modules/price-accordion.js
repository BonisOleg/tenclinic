export function initPriceAccordion() {
  const items = document.querySelectorAll('.price-accordion');
  if (!items.length) {
    return;
  }

  const desktopQuery = window.matchMedia('(min-width: 768px)');

  const targetId = () => {
    const hash = window.location.hash.replace(/^#/, '');
    if (!hash) {
      return '';
    }
    try {
      return decodeURIComponent(hash);
    } catch (error) {
      return hash;
    }
  };

  const syncOpenState = () => {
    const id = targetId();
    items.forEach((item) => {
      item.open = desktopQuery.matches || item.id === id;
    });
    if (!id) {
      return;
    }
    const target = document.getElementById(id);
    if (target) {
      target.scrollIntoView();
    }
  };

  syncOpenState();
  desktopQuery.addEventListener('change', syncOpenState);
  window.addEventListener('hashchange', syncOpenState);
}
