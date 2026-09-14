/* Keyboard behaviour for the symptom chips, kept out of the component.

   The chips are a single-select group, so they are radios rather than a row
   of buttons: only the selected chip is tabbable, and the arrow keys move
   the selection. */

/**
 * Given a key and the current index, returns the index the group should
 * move to — or null when the key is not one this group handles, so the
 * caller knows to leave the event alone.
 */
export const nextRadioIndex = (key, current, count) => {
  if (count === 0) return null;

  switch (key) {
    case "ArrowRight":
    case "ArrowDown":
      return (current + 1) % count;
    case "ArrowLeft":
    case "ArrowUp":
      return (current - 1 + count) % count;
    case "Home":
      return 0;
    case "End":
      return count - 1;
    default:
      return null;
  }
};
