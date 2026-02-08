/**
 * Tests pour MedicationEnrichment
 * 
 * Pour exécuter :
 * npm test MedicationEnrichment.test.ts
 */

import { enrichMedication, clearEnrichmentCache, getEnrichmentCacheSize } from '../MedicationEnrichment';

describe('MedicationEnrichment', () => {
  beforeEach(() => {
    // Vider le cache avant chaque test
    clearEnrichmentCache();
  });

  describe('enrichMedication', () => {
    it('devrait enrichir un médicament avec la base locale', async () => {
      // Sertraline devrait être dans medication_energy_impacts
      const result = await enrichMedication('Sertraline', '50', 'mg');
      
      expect(result.success).toBe(true);
      expect(result.source).toBe('local_cache');
      expect(result.atc_code).toBeDefined();
      expect(result.confidence).toBe('high');
    }, 10000); // Timeout 10s

    it('devrait enrichir un médicament via BDPM API', async () => {
      // Doliprane devrait être trouvé dans BDPM
      const result = await enrichMedication('Doliprane', '500', 'mg');
      
      expect(result.success).toBe(true);
      expect(result.source).toBe('bdpm_api');
      expect(result.active_substance).toBeDefined();
      expect(result.laboratory).toBeDefined();
    }, 15000);

    it('devrait gérer un médicament inconnu gracieusement', async () => {
      const result = await enrichMedication('MedicamentInconnu123', '100', 'mg');
      
      // Devrait échouer mais ne pas crash
      expect(result).toBeDefined();
      expect(result.success).toBe(false);
    }, 15000);

    it('devrait utiliser le cache pour les appels répétés', async () => {
      // Premier appel
      await enrichMedication('Doliprane', '500', 'mg');
      
      // Vérifier que le cache a une entrée
      expect(getEnrichmentCacheSize()).toBeGreaterThan(0);
      
      // Deuxième appel (devrait être instantané depuis le cache)
      const start = Date.now();
      const result = await enrichMedication('Doliprane', '500', 'mg');
      const duration = Date.now() - start;
      
      expect(duration).toBeLessThan(50); // < 50ms depuis le cache
      expect(result.success).toBe(true);
    }, 20000);

    it('devrait normaliser correctement les noms de médicaments', async () => {
      // Tester différentes variantes du même médicament
      const result1 = await enrichMedication('doliprane', '500', 'mg');
      const result2 = await enrichMedication('DOLIPRANE', '500', 'mg');
      const result3 = await enrichMedication('Doliprane®', '500', 'mg');
      
      // Toutes les variantes devraient donner le même résultat
      expect(result1.active_substance).toBe(result2.active_substance);
      expect(result2.active_substance).toBe(result3.active_substance);
    }, 30000);
  });

  describe('Cache management', () => {
    it('devrait vider le cache correctement', () => {
      // Le cache devrait être vide au départ (beforeEach)
      expect(getEnrichmentCacheSize()).toBe(0);
    });

    it('devrait incrémenter la taille du cache', async () => {
      expect(getEnrichmentCacheSize()).toBe(0);
      
      await enrichMedication('Doliprane', '500', 'mg');
      expect(getEnrichmentCacheSize()).toBe(1);
      
      await enrichMedication('Aspirine', '100', 'mg');
      expect(getEnrichmentCacheSize()).toBe(2);
    }, 30000);
  });
});

/**
 * Tests manuels à exécuter dans l'app
 */
export const manualTests = {
  /**
   * Test 1 : Médicament dans la base locale
   */
  async testLocalCache() {
    console.log('\n=== Test 1 : Base Locale ===');
    const result = await enrichMedication('Sertraline', '50', 'mg');
    console.log('Résultat:', JSON.stringify(result, null, 2));
  },

  /**
   * Test 2 : BDPM API
   */
  async testBDPM() {
    console.log('\n=== Test 2 : BDPM API ===');
    const result = await enrichMedication('Doliprane', '500', 'mg');
    console.log('Résultat:', JSON.stringify(result, null, 2));
  },

  /**
   * Test 3 : GPT-4o (si configuré)
   */
  async testGPT4o() {
    console.log('\n=== Test 3 : GPT-4o ===');
    const result = await enrichMedication('Mirtazapine', '15', 'mg');
    console.log('Résultat:', JSON.stringify(result, null, 2));
  },

  /**
   * Test 4 : Batch (plusieurs médicaments)
   */
  async testBatch() {
    console.log('\n=== Test 4 : Batch ===');
    const medications = [
      { name: 'Doliprane', dosage: '500', unit: 'mg' },
      { name: 'Sertraline', dosage: '50', unit: 'mg' },
      { name: 'Levothyrox', dosage: '100', unit: 'µg' },
      { name: 'Ibuprofène', dosage: '400', unit: 'mg' },
    ];

    for (const med of medications) {
      const result = await enrichMedication(med.name, med.dosage, med.unit);
      console.log(`\n${med.name}:`, {
        success: result.success,
        atc_code: result.atc_code,
        source: result.source,
        confidence: result.confidence,
      });
    }
  },

  /**
   * Exécuter tous les tests
   */
  async runAll() {
    await this.testLocalCache();
    await this.testBDPM();
    await this.testGPT4o();
    await this.testBatch();
    
    console.log('\n=== Tests terminés ===');
    console.log('Cache size:', getEnrichmentCacheSize());
  },
};

// Pour exécuter les tests manuels depuis l'app :
// import { manualTests } from './services/__tests__/MedicationEnrichment.test';
// await manualTests.runAll();
