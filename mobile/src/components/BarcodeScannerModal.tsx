/**
 * Modal de scan de code-barres pour médicaments
 * Utilise expo-camera pour scanner les codes-barres GS1 (CIP13)
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Modal, 
  TouchableOpacity, 
  ActivityIndicator,
  Alert,
  Platform,
  Animated
} from 'react-native';
import { Camera, CameraView, useCameraPermissions } from 'expo-camera';
import { X, Camera as CameraIcon, AlertCircle } from 'lucide-react-native';
import { PressableScale } from './PressableScale';
import { getUnsupportedCountryMessage } from '../utils/barcodeCountry';

interface BarcodeScannerModalProps {
  visible: boolean;
  onClose: () => void;
  onBarcodeScanned: (barcode: string) => void;
}

export function BarcodeScannerModal({ 
  visible, 
  onClose, 
  onBarcodeScanned 
}: BarcodeScannerModalProps) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRequestingPermission, setIsRequestingPermission] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [lastScannedCode, setLastScannedCode] = useState<string | null>(null);
  
  // Animation de la ligne de scan
  const scanLineAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Reset scanned state when modal opens
    if (visible) {
      console.log('[BarcodeScanner] 📱 Modal ouvert');
      setScanned(false);
      setIsProcessing(false);
      setIsRequestingPermission(false);
      setCameraError(null);
      setLastScannedCode(null);
      
      // Démarrer l'animation de scan
      Animated.loop(
        Animated.sequence([
          Animated.timing(scanLineAnim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(scanLineAnim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [visible, scanLineAnim]);

  useEffect(() => {
    // Log des changements de permission (seulement si modal visible)
    if (visible) {
      console.log('[BarcodeScanner] 🔐 Permission state changed:', {
        permission,
        granted: permission?.granted,
        canAskAgain: permission?.canAskAgain,
        status: permission?.status
      });
    }
  }, [permission, visible]);

  const handleRequestPermission = async () => {
    console.log('[BarcodeScanner] 🔵 handleRequestPermission APPELÉ');
    console.log('[BarcodeScanner] État avant appel:', JSON.stringify({
      granted: permission?.granted,
      canAskAgain: permission?.canAskAgain,
      status: permission?.status
    }));
    
    try {
      setIsRequestingPermission(true);
      
      // 🔴 PROTECTION : Si canAskAgain = false, ne PAS appeler requestPermission()
      // expo-camera crashe si on tente de demander la permission quand elle est définitivement refusée
      if (permission?.canAskAgain === false) {
        console.log('[BarcodeScanner] ⚠️ canAskAgain = false, ne pas appeler requestPermission()');
        console.log('[BarcodeScanner] 📱 Affichage alert pour aller dans Réglages iOS');
        
        Alert.alert(
          'Accès Caméra Requis',
          'L\'accès à la caméra a été refusé. Pour utiliser le scanner, activez la caméra dans les réglages iOS :\n\nRéglages → Pulse → Appareil photo → Activer',
          [{ text: 'Compris', onPress: () => {
            // Optionnel : Fermer le modal
            onClose();
          }}]
        );
        return;
      }
      
      console.log('[BarcodeScanner] 🎥 Permission peut être demandée, appel de requestPermission()...');
      
      // Protection : si requestPermission n'existe pas, erreur
      if (typeof requestPermission !== 'function') {
        throw new Error('requestPermission n\'est pas une fonction');
      }
      
      // Appeler requestPermission() - iOS affichera le popup natif
      const result = await requestPermission();
      console.log('[BarcodeScanner] ✅ Résultat reçu:', JSON.stringify(result, null, 2));
      
      if (!result.granted) {
        console.log('[BarcodeScanner] ❌ Permission non accordée dans le popup');
        // L'utilisateur a cliqué "Ne pas autoriser" dans le popup natif
        // On reste sur l'écran, il peut réessayer
      } else {
        console.log('[BarcodeScanner] ✅ Permission ACCORDÉE ! Caméra va s\'ouvrir');
      }
    } catch (error) {
      console.error('[BarcodeScanner] ❌❌❌ CRASH/ERREUR:', error);
      console.error('[BarcodeScanner] Stack:', error instanceof Error ? error.stack : 'No stack');
      
      Alert.alert(
        'Erreur',
        'Une erreur est survenue. Veuillez activer la caméra dans Réglages iOS.',
        [{ text: 'OK' }]
      );
    } finally {
      console.log('[BarcodeScanner] 🔵 handleRequestPermission TERMINÉ');
      setIsRequestingPermission(false);
    }
  };

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    if (scanned || isProcessing) return;

    // Empêcher les scans multiples du même code
    if (lastScannedCode === data) {
      console.log('[BarcodeScanner] 🚫 Code déjà scanné, ignoré:', data);
      return;
    }

    console.log('[BarcodeScanner] 📊 Code scanné:', { 
      type, 
      data, 
      length: data.length,
      isQR: type.toLowerCase().includes('qr')
    });
    setScanned(true);
    setIsProcessing(true);
    setLastScannedCode(data);

    try {
      const cleanedData = data.trim();
      let cip13 = '';
      
      console.log('[BarcodeScanner] 🔍 Extraction du code médicament...');
      console.log('[BarcodeScanner] 📄 Contenu brut:', cleanedData);
      console.log('[BarcodeScanner] 📄 Type:', type);
      
      // 1. Si c'est déjà un code à 13 chiffres (code-barres EAN-13)
      if (/^\d{13}$/.test(cleanedData)) {
        cip13 = cleanedData;
        console.log('[BarcodeScanner] ✅ Code-barres EAN-13 direct:', cip13);
      }
      // 2. Si c'est un DataMatrix ou QR avec format GS1
      // Format GS1: commence par "01" suivi du GTIN14
      // Exemple: 01034009300913572188026252604381310VWA25001A17280831
      else if (cleanedData.startsWith('01') && cleanedData.length > 16) {
        // Extraire le GTIN14 (14 chiffres après "01")
        const gtin14 = cleanedData.substring(2, 16);
        // On envoie le GTIN14 complet au backend (pas de conversion ici)
        cip13 = gtin14;
        console.log('[BarcodeScanner] 📦 Format GS1 DataMatrix détecté');
        console.log('[BarcodeScanner] 📦 GTIN14 extrait:', gtin14);
      }
      // 3. Si c'est un QR code ou DataMatrix avec des données structurées
      else {
        console.log('[BarcodeScanner] 📱 QR/DataMatrix détecté, extraction...');
        
        // Essayer d'extraire un code à 13 chiffres (CIP13)
        // Format possible: 3400123456789
        const match13 = cleanedData.match(/\d{13}/);
        if (match13) {
          cip13 = match13[0];
          console.log('[BarcodeScanner] ✅ CIP13 (13 chiffres) extrait:', cip13);
        } else {
          // Essayer d'extraire un CIP7 (7 chiffres) et le convertir
          const match7 = cleanedData.match(/\d{7}/);
          if (match7) {
            // Ajouter le préfixe 3400 pour les médicaments français
            cip13 = '3400' + match7[0] + '00'; // Padding basique
            console.log('[BarcodeScanner] ⚠️ CIP7 détecté, conversion en CIP13:', cip13);
          } else {
            // Essayer de trouver n'importe quel code numérique
            const anyNumber = cleanedData.match(/\d+/);
            if (anyNumber && anyNumber[0].length >= 7) {
              cip13 = anyNumber[0].padEnd(13, '0').substring(0, 13);
              console.log('[BarcodeScanner] ⚠️ Code numérique trouvé, tentative:', cip13);
            }
          }
        }
      }
      
      // Validation finale
      // Accepter les CIP13 (13 chiffres) et GTIN14 (14 chiffres)
      if (cip13 && (cip13.length === 13 || cip13.length === 14) && /^\d{13,14}$/.test(cip13)) {
        // Vérifier que c'est bien un médicament français
        // CIP13 commence par "3400", GTIN14 commence par "0340"
        const isFrenchMedication = cip13.startsWith('3400') || cip13.startsWith('0340');
        
        if (isFrenchMedication) {
          console.log('[BarcodeScanner] ✅ Code médicament français valide, envoi au backend');
          onBarcodeScanned(cip13);
          onClose();
        } else {
          console.log('[BarcodeScanner] ⚠️ Code non-français détecté:', cip13);
          console.log('[BarcodeScanner] 💡 Suggestion de recherche manuelle');
          
          // Message personnalisé selon le pays
          const countryMessage = getUnsupportedCountryMessage(cip13);
          
          Alert.alert(
            countryMessage.title,
            countryMessage.message,
            [
              { 
                text: 'Rechercher par nom', 
                onPress: () => {
                  // Fermer le scanner et laisser l'utilisateur rechercher manuellement
                  onClose();
                }
              },
              { 
                text: 'Réessayer le scan', 
                onPress: () => { 
                  setScanned(false); 
                  setIsProcessing(false); 
                  setLastScannedCode(null); 
                } 
              }
            ]
          );
          setIsProcessing(false);
        }
      } else {
        console.log('[BarcodeScanner] ❌ Impossible d\'extraire un code valide');
        console.log('[BarcodeScanner] 📄 Contenu complet:', cleanedData);
        
        Alert.alert(
          'Code non reconnu',
          `Impossible d'extraire le code médicament.\n\nContenu détecté:\n${cleanedData.substring(0, 150)}${cleanedData.length > 150 ? '...' : ''}\n\nVeuillez réessayer ou contacter le support.`,
          [
            { 
              text: 'Réessayer', 
              onPress: () => { 
                setScanned(false); 
                setIsProcessing(false); 
                setLastScannedCode(null); 
              } 
            },
            { text: 'Annuler', onPress: onClose }
          ]
        );
        setIsProcessing(false);
      }
    } catch (error) {
      console.error('[BarcodeScanner] ❌ Erreur:', error);
      Alert.alert(
        'Erreur',
        'Une erreur est survenue lors du scan.',
        [{ 
          text: 'Réessayer', 
          onPress: () => { 
            setScanned(false); 
            setIsProcessing(false); 
            setLastScannedCode(null); 
          } 
        }]
      );
      setIsProcessing(false);
    }
  };

  if (!visible) return null;

  // Chargement des permissions
  if (!permission) {
    return (
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={onClose}
      >
        <View style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.title}>Scanner un médicament</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#5E5CE6" />
            <Text style={styles.loadingText}>Chargement de la caméra...</Text>
          </View>
        </View>
      </Modal>
    );
  }

  // Permission non accordée - toujours essayer de demander via popup natif iOS
  if (!permission.granted) {
    // Si la permission a été refusée définitivement, on affiche un message différent
    const isDefinitelyDenied = permission.canAskAgain === false && permission.status === 'denied';
    console.log('[BarcodeScanner] 🎥 Permission non accordée, isDefinitelyDenied:', isDefinitelyDenied);
    
    return (
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={onClose}
      >
        <View style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.title}>Scanner un médicament</Text>
            <View style={styles.placeholder} />
          </View>
          
          <View style={styles.permissionContainer}>
            <View style={styles.iconCircle}>
              {isDefinitelyDenied ? (
                <AlertCircle size={48} color="#FF9500" strokeWidth={2} />
              ) : (
                <CameraIcon size={48} color="#5E5CE6" strokeWidth={2} />
              )}
            </View>
            <Text style={styles.permissionTitle}>
              {isDefinitelyDenied ? 'Permission Refusée' : 'Accès à la caméra'}
            </Text>
            <Text style={styles.permissionText}>
              {isDefinitelyDenied 
                ? 'L\'accès à la caméra a été refusé. Pour utiliser le scanner, veuillez activer l\'accès à la caméra dans les réglages de votre iPhone.'
                : 'Pour scanner le code-barres de votre médicament, nous avons besoin d\'accéder à votre caméra.'
              }
            </Text>
            {isDefinitelyDenied && (
              <Text style={[styles.permissionText, { marginTop: 12, fontSize: 14, color: '#636366' }]}>
                Réglages → Pulse → Appareil photo → Activer
              </Text>
            )}
            <PressableScale
              onPress={handleRequestPermission}
              style={[
                styles.permissionButton,
                isRequestingPermission && styles.permissionButtonDisabled
              ]}
              disabled={isRequestingPermission}
            >
              {isRequestingPermission ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.permissionButtonText}>
                  {isDefinitelyDenied ? 'Réessayer' : 'Autoriser'}
                </Text>
              )}
            </PressableScale>
          </View>
        </View>
      </Modal>
    );
  }

  // Erreur caméra
  if (cameraError) {
    return (
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={onClose}
      >
        <View style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <X size={24} color="#FFFFFF" />
            </TouchableOpacity>
            <Text style={styles.title}>Scanner un médicament</Text>
            <View style={styles.placeholder} />
          </View>
          
          <View style={styles.permissionContainer}>
            <View style={styles.iconCircle}>
              <AlertCircle size={48} color="#FF3B30" strokeWidth={2} />
            </View>
            <Text style={styles.permissionTitle}>Erreur Caméra</Text>
            <Text style={styles.permissionText}>
              {cameraError}
            </Text>
            <PressableScale
              onPress={onClose}
              style={styles.permissionButton}
            >
              <Text style={styles.permissionButtonText}>Fermer</Text>
            </PressableScale>
          </View>
        </View>
      </Modal>
    );
  }

  // Scanner actif - Permission accordée !
  console.log('[BarcodeScanner] ✅ 📷 Permission accordée ! Rendu du CameraView');
  
  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color="#FFFFFF" />
          </TouchableOpacity>
          <Text style={styles.title}>Scanner un médicament</Text>
          <View style={styles.placeholder} />
        </View>

        <View style={styles.cameraContainer}>
          <CameraView
            style={styles.camera}
            facing="back"
            autofocus="on"
            barcodeScannerSettings={{
              barcodeTypes: [
                'qr',
                'ean13',
                'ean8',
                'upc_a',
                'upc_e',
                'code128',
                'code39',
                'datamatrix',
              ],
            }}
            onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          />

          {/* Overlay de ciblage */}
          <View style={styles.overlay}>
            <View style={styles.overlayTop} />
            <View style={styles.overlayMiddle}>
              <View style={styles.overlaySide} />
              <View style={styles.scanArea}>
                <View style={[styles.corner, styles.cornerTopLeft]} />
                <View style={[styles.corner, styles.cornerTopRight]} />
                <View style={[styles.corner, styles.cornerBottomLeft]} />
                <View style={[styles.corner, styles.cornerBottomRight]} />
                
                {/* Ligne de scan animée */}
                {!scanned && !isProcessing && (
                  <Animated.View 
                    style={[
                      styles.scanLine,
                      {
                        transform: [{
                          translateY: scanLineAnim.interpolate({
                            inputRange: [0, 1],
                            outputRange: [0, 240], // Hauteur augmentée de la zone de scan
                          }),
                        }],
                      },
                    ]}
                  />
                )}
              </View>
              <View style={styles.overlaySide} />
            </View>
            <View style={styles.overlayBottom}>
              {!scanned && !isProcessing && (
                <View style={styles.instructionContainer}>
                  <AlertCircle size={20} color="#FFFFFF" />
                  <Text style={styles.instructionText}>
                    Placez le QR code ou code-barres dans le cadre
                  </Text>
                </View>
              )}
              {isProcessing && (
                <View style={styles.processingContainer}>
                  <ActivityIndicator size="small" color="#FFFFFF" />
                  <Text style={styles.processingText}>Recherche en cours...</Text>
                </View>
              )}
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 60 : 20,
    paddingBottom: 16,
    backgroundColor: '#000000',
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  placeholder: {
    width: 40,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    color: '#8E8E93',
    fontSize: 16,
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 20,
  },
  iconCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 24,
  },
  permissionButton: {
    backgroundColor: '#5E5CE6',
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 14,
    marginTop: 12,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  permissionButtonDisabled: {
    opacity: 0.6,
  },
  permissionButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'transparent',
  },
  overlayTop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  overlayMiddle: {
    flexDirection: 'row',
  },
  overlaySide: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  scanArea: {
    width: 300,
    height: 240,
    position: 'relative',
    overflow: 'hidden',
  },
  scanLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: '#5E5CE6',
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
  corner: {
    position: 'absolute',
    width: 50,
    height: 50,
    borderColor: '#5E5CE6',
  },
  cornerTopLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderTopLeftRadius: 8,
  },
  cornerTopRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderTopRightRadius: 8,
  },
  cornerBottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderBottomLeftRadius: 8,
  },
  cornerBottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderBottomRightRadius: 8,
  },
  overlayBottom: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 32,
  },
  instructionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(94, 92, 230, 0.2)',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  instructionText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  processingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  processingText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
});
