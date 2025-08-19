// Simple helpers for API requests and DOM selection

export async function apiFetch(url) {
  // Fetch JSON data with same-origin credentials
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}
// Shorthand query selectors
export const $ = (sel, root=document) => root.querySelector(sel);
export const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

// Basic DOM utilities
export function setText(el, t){ if (el) el.textContent = t; }
export function show(el, disp="inline"){ if (el) el.style.display = disp; }
export function hide(el){ if (el) el.style.display = "none"; }

