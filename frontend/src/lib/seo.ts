import { useEffect } from 'react';

const SITE = 'WANO CTF';

function setMeta(selector: string, attr: 'name' | 'property', key: string, content: string): void {
  let tag = document.head.querySelector<HTMLMetaElement>(selector);
  if (!tag) {
    tag = document.createElement('meta');
    tag.setAttribute(attr, key);
    document.head.appendChild(tag);
  }
  tag.setAttribute('content', content);
}

/**
 * Per-route SEO: keeps `document.title` and the description/OG tags in sync with
 * the active console screen so deep links share accurately.
 */
export function useDocumentTitle(title: string, description?: string): void {
  useEffect(() => {
    const full = title === SITE ? `${SITE} — Enter the Digital Warzone` : `${title} · ${SITE}`;
    document.title = full;
    setMeta('meta[property="og:title"]', 'property', 'og:title', full);
    if (description) {
      setMeta('meta[name="description"]', 'name', 'description', description);
      setMeta('meta[property="og:description"]', 'property', 'og:description', description);
      setMeta('meta[name="twitter:description"]', 'name', 'twitter:description', description);
    }
  }, [title, description]);
}
