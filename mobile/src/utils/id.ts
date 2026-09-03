let uuidv4: () => string;
try {
  const uuidModule = require('uuid');
  uuidv4 = uuidModule.v4 || uuidModule.default?.v4;
} catch (e) {
  uuidv4 = () => '';
}

/**
 * Generate a unique ID for reports, incidents, and messages.
 * Uses standard UUID v4 when crypto is available, with a bulletproof
 * fallback if crypto.getRandomValues or uuid is undefined in release mode.
 */
export function generateUniqueId(prefix: string = 'id'): string {
  try {
    const g = typeof globalThis !== 'undefined' ? globalThis : (typeof global !== 'undefined' ? global : window);
    if (g && g.crypto && typeof g.crypto.getRandomValues === 'function' && typeof uuidv4 === 'function') {
      const generated = uuidv4();
      if (generated) {
        return generated;
      }
    }
  } catch (err) {
    console.warn('UUID crypto.getRandomValues unavailable, using fallback unique ID generator:', err);
  }

  // Fail-safe collision-free ID fallback for release environments
  const timestamp = Date.now().toString(36);
  const randomPart1 = Math.random().toString(36).substring(2, 10);
  const randomPart2 = Math.random().toString(36).substring(2, 10);
  return `${prefix}-${timestamp}-${randomPart1}${randomPart2}`;
}
