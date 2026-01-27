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
      guard let stepType = HKQuantityType.quantityType(forIdentifier: .stepCount),
            let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate) else {
        promise.reject("INVALID_TYPE", "Type de données HealthKit invalide")
        return
      }
      
      // Demander uniquement les permissions de lecture
      self.healthStore.requestAuthorization(toShare: [], read: [stepType, heartRateType]) { success, error in
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
  }
}
