"use strict";

for (const button of document.querySelectorAll("[data-copy-note]")) {
  button.addEventListener("click", async () => {
    const note = button.getAttribute("data-copy-note") || "";
    try {
      await navigator.clipboard.writeText(note);
      const previous = button.textContent;
      button.textContent = "Copied";
      window.setTimeout(() => { button.textContent = previous; }, 1600);
    } catch (_error) {
      const target = button.closest(".note-box")?.querySelector("code");
      if (target) {
        const range = document.createRange();
        range.selectNodeContents(target);
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range);
        button.textContent = "Select and copy";
      }
    }
  });
}
