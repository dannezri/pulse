import ExpoModulesCore
import HealthKit

/**
 * Module Expo pour HealthKit (lecture uniquement)
 * Permet de lire les données de pas et de fréquence cardiaque depuis HealthKit
 */
public class PulseHealthkitModule: Module {
  private let healthStore = HKHealthStore()
  
  public func definition() -> ModuleDefinition {
    Name("PulseHealthkit")

    // Vérifie si HealthKit est disponible sur cet appareil
    AsyncFunction("isAvailable") { () -> Bool in
      return HKHealthStore.isHealthDataAvailable()
    }
    
    // Demande les autorisations HealthKit (lecture uniquement)
    AsyncFunction("requestAuthorization") { (promise: Promise) in
      guard HKHealthStore.isHealthDataAvailable() else {
        promise.reject("HEALTHKIT_NOT_AVAILABLE", "HealthKit n'est pas disponible sur cet appareil")
        return
      }
      
      // Types de données à lire (lecture uniquement, pas d'écriture)
      var readTypes: Set<HKObjectType> = []
      
      if let stepType = HKQuantityType.quantityType(forIdentifier: .stepCount) {
        readTypes.insert(stepType)
        print("[PulseHealthkit] ✅ Demande permission: Pas")
      }
      if let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate) {
        readTypes.insert(heartRateType)
        print("[PulseHealthkit] ✅ Demande permission: Fréquence cardiaque")
      }
      if let dietaryEnergyType = HKQuantityType.quantityType(forIdentifier: .dietaryEnergyConsumed) {
        readTypes.insert(dietaryEnergyType)
        print("[PulseHealthkit] ✅ Demande permission: Calories")
      }
      if let dietaryCarbsType = HKQuantityType.quantityType(forIdentifier: .dietaryCarbohydrates) {
        readTypes.insert(dietaryCarbsType)
        print("[PulseHealthkit] ✅ Demande permission: Glucides")
      }
      
      // Note: Les corrélations (HKCorrelationType) ne peuvent pas être demandées dans requestAuthorization
      // Elles peuvent être lues via des requêtes sans autorisation explicite
      
      print("[PulseHealthkit] Total de types à autoriser:", readTypes.count)
      
      if readTypes.isEmpty {
        promise.reject("INVALID_TYPE", "Aucun type de données HealthKit valide")
        return
      }
      
      // Demander uniquement les permissions de lecture
      self.healthStore.requestAuthorization(toShare: [], read: readTypes) { success, error in
        if let error = error {
          promise.reject("AUTHORIZATION_ERROR", "Erreur lors de la demande d'autorisation: \(error.localizedDescription)")
          return
        }
        promise.resolve(success)
      }
    }
    
    // Lit les données de pas sur une période donnée
    AsyncFunction("readSteps") { (fromISO: String, toISO: String, promise: Promise) in
      guard HKHealthStore.isHealthDataAvailable() else {
        promise.reject("HEALTHKIT_NOT_AVAILABLE", "HealthKit n'est pas disponible")
        return
      }
      
      guard let stepType = HKQuantityType.quantityType(forIdentifier: .stepCount) else {
        promise.reject("INVALID_TYPE", "Type de données pas invalide")
        return
      }
      
      // Parser les dates ISO 8601
      let formatter = ISO8601DateFormatter()
      formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
      
      guard let fromDate = formatter.date(from: fromISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: fromISO)
      }(), let toDate = formatter.date(from: toISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: toISO)
      }() else {
        promise.reject("INVALID_DATE", "Format de date invalide. Utilisez ISO 8601")
        return
      }
      
      // Créer le prédicat pour la période
      let predicate = HKQuery.predicateForSamples(withStart: fromDate, end: toDate, options: .strictStartDate)
      
      // Créer la requête
      let query = HKSampleQuery(
        sampleType: stepType,
        predicate: predicate,
        limit: HKObjectQueryNoLimit,
        sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
      ) { _, samples, error in
        if let error = error {
          promise.reject("QUERY_ERROR", "Erreur lors de la lecture des pas: \(error.localizedDescription)")
          return
        }
        
        guard let quantitySamples = samples as? [HKQuantitySample] else {
          promise.resolve([])
          return
        }
        
        // Convertir en format normalisé
        let results = quantitySamples.map { sample -> [String: Any] in
          let count = Int(sample.quantity.doubleValue(for: HKUnit.count()))
          return [
            "start": formatter.string(from: sample.startDate),
            "end": formatter.string(from: sample.endDate),
            "count": count
          ]
        }
        
        promise.resolve(results)
      }
      
      self.healthStore.execute(query)
    }
    
    // Lit les données de fréquence cardiaque sur une période donnée
    AsyncFunction("readHeartRate") { (fromISO: String, toISO: String, promise: Promise) in
      guard HKHealthStore.isHealthDataAvailable() else {
        promise.reject("HEALTHKIT_NOT_AVAILABLE", "HealthKit n'est pas disponible")
        return
      }
      
      guard let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate) else {
        promise.reject("INVALID_TYPE", "Type de données fréquence cardiaque invalide")
        return
      }
      
      // Parser les dates ISO 8601
      let formatter = ISO8601DateFormatter()
      formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
      
      guard let fromDate = formatter.date(from: fromISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: fromISO)
      }(), let toDate = formatter.date(from: toISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: toISO)
      }() else {
        promise.reject("INVALID_DATE", "Format de date invalide. Utilisez ISO 8601")
        return
      }
      
      // Créer le prédicat pour la période
      let predicate = HKQuery.predicateForSamples(withStart: fromDate, end: toDate, options: .strictStartDate)
      
      // Créer la requête
      let query = HKSampleQuery(
        sampleType: heartRateType,
        predicate: predicate,
        limit: HKObjectQueryNoLimit,
        sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
      ) { _, samples, error in
        if let error = error {
          promise.reject("QUERY_ERROR", "Erreur lors de la lecture de la fréquence cardiaque: \(error.localizedDescription)")
          return
        }
        
        guard let quantitySamples = samples as? [HKQuantitySample] else {
          promise.resolve([])
          return
        }
        
        // Convertir en format normalisé
        let results = quantitySamples.map { sample -> [String: Any] in
          let bpm = Int(sample.quantity.doubleValue(for: HKUnit(from: "count/min")))
          return [
            "time": formatter.string(from: sample.startDate),
            "bpm": bpm
          ]
        }
        
        promise.resolve(results)
      }
      
      self.healthStore.execute(query)
    }
    
    // Lit les données de nutrition (calories, glucides) sur une période donnée
    AsyncFunction("readNutrition") { (fromISO: String, toISO: String, promise: Promise) in
      print("[PulseHealthkit] 🍎 readNutrition appelé")
      print("[PulseHealthkit] Période:", fromISO, "à", toISO)
      
      guard HKHealthStore.isHealthDataAvailable() else {
        promise.reject("HEALTHKIT_NOT_AVAILABLE", "HealthKit n'est pas disponible")
        return
      }
      
      let formatter = ISO8601DateFormatter()
      formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
      
      guard let fromDate = formatter.date(from: fromISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: fromISO)
      }(), let toDate = formatter.date(from: toISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: toISO)
      }() else {
        promise.reject("INVALID_DATE", "Format de date invalide. Utilisez ISO 8601")
        return
      }
      
      print("[PulseHealthkit] Dates parsées - De:", fromDate, "à:", toDate)
      
      let predicate = HKQuery.predicateForSamples(withStart: fromDate, end: toDate, options: .strictStartDate)
      
      var results: [[String: Any]] = []
      let group = DispatchGroup()
      
      // Calories
      if let energyType = HKQuantityType.quantityType(forIdentifier: .dietaryEnergyConsumed) {
        print("[PulseHealthkit] 🔍 Recherche de calories...")
        group.enter()
        let query = HKSampleQuery(
          sampleType: energyType,
          predicate: predicate,
          limit: HKObjectQueryNoLimit,
          sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
        ) { _, samples, error in
          defer { group.leave() }
          if let error = error {
            print("[PulseHealthkit] ❌ Erreur lecture calories:", error.localizedDescription)
            return
          }
          if let quantitySamples = samples as? [HKQuantitySample] {
            print("[PulseHealthkit] ✅ Trouvé", quantitySamples.count, "échantillons de calories")
            for sample in quantitySamples {
              let calories = Int(sample.quantity.doubleValue(for: HKUnit.kilocalorie()))
              print("[PulseHealthkit]   - ", calories, "kcal à", sample.startDate)
              results.append([
                "type": "calories",
                "value": calories,
                "logged_at": formatter.string(from: sample.startDate)
              ])
            }
          } else {
            print("[PulseHealthkit] ⚠️ Aucun échantillon de calories trouvé")
          }
        }
        self.healthStore.execute(query)
      }
      
      // Glucides
      if let carbsType = HKQuantityType.quantityType(forIdentifier: .dietaryCarbohydrates) {
        print("[PulseHealthkit] 🔍 Recherche de glucides...")
        group.enter()
        let query = HKSampleQuery(
          sampleType: carbsType,
          predicate: predicate,
          limit: HKObjectQueryNoLimit,
          sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
        ) { _, samples, error in
          defer { group.leave() }
          if let error = error {
            print("[PulseHealthkit] ❌ Erreur lecture glucides:", error.localizedDescription)
            return
          }
          if let quantitySamples = samples as? [HKQuantitySample] {
            print("[PulseHealthkit] ✅ Trouvé", quantitySamples.count, "échantillons de glucides")
            for sample in quantitySamples {
              let carbs = Int(sample.quantity.doubleValue(for: HKUnit.gram()))
              print("[PulseHealthkit]   - ", carbs, "g à", sample.startDate)
              results.append([
                "type": "carbs",
                "value": carbs,
                "logged_at": formatter.string(from: sample.startDate)
              ])
            }
          } else {
            print("[PulseHealthkit] ⚠️ Aucun échantillon de glucides trouvé")
          }
        }
        self.healthStore.execute(query)
      }
      
      group.notify(queue: .main) {
        print("[PulseHealthkit] 📊 Total nutrition retourné:", results.count, "entrées")
        promise.resolve(results)
      }
    }
    
    // Lit les données de médicaments sur une période donnée
    // Les apps tierces comme MyTherapy stockent les médicaments dans HealthKit
    AsyncFunction("readMedications") { (fromISO: String, toISO: String, promise: Promise) in
      print("[PulseHealthkit] 💊 readMedications appelé")
      print("[PulseHealthkit] Période:", fromISO, "à", toISO)
      
      guard HKHealthStore.isHealthDataAvailable() else {
        promise.reject("HEALTHKIT_NOT_AVAILABLE", "HealthKit n'est pas disponible")
        return
      }
      
      let formatter = ISO8601DateFormatter()
      formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
      
      guard let fromDate = formatter.date(from: fromISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: fromISO)
      }(), let toDate = formatter.date(from: toISO) ?? {
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: toISO)
      }() else {
        promise.reject("INVALID_DATE", "Format de date invalide")
        return
      }
      
      print("[PulseHealthkit] Dates parsées - De:", fromDate, "à:", toDate)
      
      let predicate = HKQuery.predicateForSamples(withStart: fromDate, end: toDate, options: .strictStartDate)
      var results: [[String: Any]] = []
      let group = DispatchGroup()
      
      // Rechercher les corrélations qui peuvent contenir des médicaments
      // Les apps tierces utilisent souvent des corrélations avec des métadonnées
      if let correlationType = HKCorrelationType.correlationType(forIdentifier: .food) {
        print("[PulseHealthkit] 🔍 Recherche de corrélations (médicaments)...")
        group.enter()
        let query = HKSampleQuery(
          sampleType: correlationType,
          predicate: predicate,
          limit: HKObjectQueryNoLimit,
          sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]
        ) { _, samples, error in
          defer { group.leave() }
          if let error = error {
            print("[PulseHealthkit] ❌ Erreur lecture corrélations:", error.localizedDescription)
            return
          }
          if let correlations = samples as? [HKCorrelation] {
            print("[PulseHealthkit] ✅ Trouvé", correlations.count, "corrélations")
            for correlation in correlations {
              // Extraire les métadonnées qui peuvent contenir des infos de médicaments
              if let metadata = correlation.metadata,
                 let medicationName = metadata["HKMedicationName"] as? String ?? metadata["name"] as? String {
                print("[PulseHealthkit]   - Médicament:", medicationName, "à", correlation.startDate)
                results.append([
                  "name": medicationName,
                  "logged_at": formatter.string(from: correlation.startDate),
                  "metadata": metadata
                ])
              }
            }
          } else {
            print("[PulseHealthkit] ⚠️ Aucune corrélation trouvée")
          }
        }
        self.healthStore.execute(query)
      }
      
      group.notify(queue: .main) {
        print("[PulseHealthkit] 💊 Total médicaments retournés:", results.count, "entrées")
        promise.resolve(results)
      }
    }
    
    // Lit les données de symptômes sur une période donnée
    // Note: HealthKit ne fournit pas de type standard pour les symptômes
    AsyncFunction("readSymptoms") { (fromISO: String, toISO: String, promise: Promise) in
      // Retourne un tableau vide car symptom n'est pas un type HealthKit standard
      promise.resolve([])
    }
    
    // Lit les données de selles sur une période donnée
    // Note: HealthKit ne fournit pas de type standard pour les selles
    AsyncFunction("readStool") { (fromISO: String, toISO: String, promise: Promise) in
      // Retourne un tableau vide car bowelMovement n'est pas un type HealthKit standard
      promise.resolve([])
    }
  }
}
