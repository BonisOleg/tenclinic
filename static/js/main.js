import { initNav } from './modules/nav.js?v=20260707c';
import { initReveal } from './modules/reveal.js?v=20260707c';
import { initAccordion } from './modules/accordion.js?v=20260706i';
import { initBooking } from './modules/booking.js?v=20260706i';
import { initHtmxCsrf } from './modules/htmx-csrf.js?v=20260706i';
import { initPriceAccordion } from './modules/price-accordion.js?v=20260925b';
import { initDoctorsFilters } from './modules/doctors-filters.js?v=20260706i';
import { initServicesFilters } from './modules/services-filters.js?v=20260708j';
import { initCustomSelectGlobal } from './modules/custom-select.js?v=20260706i';
import { initDateInputGlobal } from './modules/date-input.js?v=20260706i';

function initApp() {
  initNav();
  initReveal();
  initAccordion();
  initCustomSelectGlobal();
  initDateInputGlobal();
  initHtmxCsrf();
  initBooking();
  initPriceAccordion();
  initDoctorsFilters();
  initServicesFilters();
}

initApp();
