"use client";

import { useEffect } from "react";

function isTypingTarget(target: EventTarget | null) {
  const element = target as HTMLElement | null;
  if (!element) return false;
  return ["INPUT", "TEXTAREA", "SELECT"].includes(element.tagName) || element.isContentEditable;
}

export function useShortcut(keys: string, handler: () => void) {
  useEffect(() => {
    let prefix: string | null = null;
    const onKeyDown = (event: KeyboardEvent) => {
      if (isTypingTarget(event.target)) return;
      const normalized = event.key.toLowerCase();
      if (keys === "mod+k" && normalized === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        handler();
      } else if (keys === "mod+b" && normalized === "b" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        handler();
      } else if (keys.includes(" ") && (prefix ? `${prefix} ${normalized}` : normalized) === keys) {
        event.preventDefault();
        prefix = null;
        handler();
      } else if (keys.startsWith(`${normalized} `)) {
        prefix = normalized;
      } else if (keys === normalized) {
        event.preventDefault();
        handler();
      } else {
        prefix = null;
      }
    };
    window.addEventListener("keydown", onKeydownCompat(onKeyDown));
    return () => window.removeEventListener("keydown", onKeydownCompat(onKeyDown));
  }, [handler, keys]);
}

function onKeydownCompat(handler: (event: KeyboardEvent) => void) {
  return handler;
}
