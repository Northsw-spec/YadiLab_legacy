// Reveal authored HTML without reading or updating the project or simulator.
export function setupProtocolLessons(section) {
  for (const lesson of section.querySelectorAll(':scope > details')) {
    const test = lesson.querySelector('[data-lesson-test] select');
    const showOutcome = lesson.querySelector('[data-lesson-test] button');
    const result = lesson.querySelector('[data-lesson-result]');
    const outcomes = new Map(Array.from(lesson.querySelectorAll('[data-outcome]'),
      template => [template.dataset.outcome, template]));
    const answer = lesson.querySelector('[data-lesson-answer]');
    const sources = lesson.querySelector('[data-lesson-sources]');

    showOutcome.disabled = !test.value;
    test.addEventListener('change', () => {
      showOutcome.disabled = !test.value;
      result.replaceChildren();
    });
    showOutcome.addEventListener('click', () => {
      const outcome = outcomes.get(test.value);
      if (!outcome) return;

      const prepared = outcome.content.cloneNode(true);
      const review = prepared.querySelector('[data-lesson-review]');
      result.replaceChildren(prepared);
      if (!review) return;

      const controls = answer.content.cloneNode(true);
      const interpretation = controls.querySelector('select');
      const submit = controls.querySelector('button');
      const feedback = controls.querySelector('[data-lesson-feedback]');
      result.append(controls);

      submit.disabled = true;
      interpretation.addEventListener('change', () => {
        submit.disabled = !interpretation.value;
        feedback.textContent = '';
      });
      submit.addEventListener('click', () => {
        if (interpretation.value !== outcome.dataset.correct) {
          feedback.textContent = 'Underlaget räcker inte för den slutsatsen. Jämför de båda riktningarna eller mätpunkterna och försök igen.';
          return;
        }
        feedback.textContent = 'Tolkningen stöds av det förberedda utfallet.';
        submit.disabled = true;
        interpretation.disabled = true;
        result.append(review.content.cloneNode(true), sources.content.cloneNode(true));
      });
    });
  }
}
