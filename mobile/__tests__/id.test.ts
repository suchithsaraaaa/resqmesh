import { generateUniqueId } from '../src/utils/id';

describe('generateUniqueId Unit & Regression Tests', () => {
  it('INC-REG-001: Should generate valid non-empty unique ID with given prefix', () => {
    const id = generateUniqueId('report');
    expect(id).toBeDefined();
    expect(typeof id).toBe('string');
    expect(id.startsWith('report-')).toBe(true);
    expect(id.length).toBeGreaterThan(10);
  });

  it('INC-REG-002: Should generate unique values across multiple sequential calls', () => {
    const ids = new Set<string>();
    for (let i = 0; i < 100; i++) {
      const newId = generateUniqueId('incident');
      expect(ids.has(newId)).toBe(false);
      ids.add(newId);
    }
    expect(ids.size).toBe(100);
  });

  it('INC-REG-003: Should handle missing global crypto gracefully without throwing undefined is not a function', () => {
    const originalCrypto = (globalThis as any).crypto;
    try {
      // Intentionally break global.crypto to simulate release runtime edge case
      delete (globalThis as any).crypto;
      const fallbackId = generateUniqueId('fallback');
      expect(fallbackId).toBeDefined();
      expect(typeof fallbackId).toBe('string');
      expect(fallbackId.startsWith('fallback-')).toBe(true);
    } finally {
      (globalThis as any).crypto = originalCrypto;
    }
  });
});
