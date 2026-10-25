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

// Age the recorded observation; never turn a historical feed into a live claim.
for (const time of document.querySelectorAll("[data-feed-time]")) {
  const status = time.parentElement?.querySelector("[data-feed-freshness]");
  if (!status) continue;
  const observed = Date.parse(time.getAttribute("datetime") || "");
  const ageHours = (Date.now() - observed) / 3600000;
  if (!Number.isFinite(observed) || ageHours < -1) {
    status.textContent = "Observation time unavailable or inconsistent; not a live feed.";
  } else if (ageHours > 48) {
    status.textContent = "STALE: recorded more than 48 hours ago. Not a live feed.";
  } else {
    status.textContent = "Dated source observations only; not live scores or slot availability.";
  }
}
