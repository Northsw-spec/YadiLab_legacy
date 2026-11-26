import {$, el} from './dom.js';

/* Presentation-only workspace layout: canonical network state is unchanged. */
function panelCard(title, nodes) {
  const card = el('details', {className:'dropdown-card', dataset:{dropdownCard:'true'}});
  const summary = el('summary', {}, title);
  const body = el('div', {className:'dropdown-body'});
  body.append(...nodes.filter(Boolean));
  card.append(summary, body);
  card.addEventListener('toggle', syncDropdownButton);
  return card;
}

function dropdownCards() {
  return [...document.querySelectorAll('.dropdown-card[data-dropdown-card="true"]')];
}

function syncDropdownButton() {
  const cards = dropdownCards();
  $('toggle-dropdowns').setAttribute('aria-pressed',
    String(cards.length > 0 && cards.every(card => card.open)));
}

export function setupWorkspacePanels() {
  const inventory = document.querySelector('.left-panel');
  const inventoryHeadings = [...inventory.querySelectorAll(':scope > .list-header')];
  inventory.replaceChildren(
    panelCard('Inventering', [
      inventory.querySelector('.panel-section:not(.action-stack)'),
      inventory.querySelector('.stats'), inventory.querySelector('.action-stack'),
      inventoryHeadings[0], $('node-list'), inventoryHeadings[1], $('link-list'),
      inventoryHeadings[2], $('zone-list'),
    ]),
    panelCard('Sparade projekt och mallar', [inventory.querySelector('.left-bottom')]),
  );
  const tools = document.querySelector('.right-panel');
  const panels = [...tools.querySelectorAll(':scope > .trace-panel')];
  const inspectorTitle = tools.querySelector(':scope > .inspector-title');
  const inspectorBody = tools.querySelector(':scope > .inspector-body');
  tools.replaceChildren(
    panelCard('Inspektör / egenskaper', [inspectorTitle, inspectorBody]),
    ...panels.map(panel => panelCard(
      panel.querySelector('h3')?.textContent?.trim() || panel.getAttribute('aria-label') || 'Diagnostik',
      [panel])),
  );
  $('toggle-dropdowns').addEventListener('click', () => {
    const cards = dropdownCards();
    const open = cards.some(card => !card.open);
    for (const card of cards) card.open = open;
    syncDropdownButton();
  });
  syncDropdownButton();
}

