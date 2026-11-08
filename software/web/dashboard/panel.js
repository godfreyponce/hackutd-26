// While the hub is offline the dashboard cannot know the latest numbers, so the
// counters and box card values show this instead of the last ones it saw.
export const OFFLINE_TEXT = '--';

export function panelValues(values, hub) {
  if (hub !== 'offline') return values;
  return Object.fromEntries(Object.keys(values).map((id) => [id, OFFLINE_TEXT]));
}
