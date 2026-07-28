import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils
import QtQuick3D.Helpers 

Item {
    id: root
    
    // --- VARIABLES CONECTADAS A PYTHON (Vuelo en tiempo real) ---
    property real q_w: 1.0
    property real q_x: 0.0
    property real q_y: 0.0
    property real q_z: 0.0
    
    // --- MAPEOS DE EJES (Desde el JSON) ---
    property string map_pitch: "X"
    property string map_roll: "Y"
    property string map_yaw: "Z"
    
    // --- INVERSIONES DE EJES (Desde el JSON) ---
    property bool invert_pitch: false
    property bool invert_roll: false
    property bool invert_yaw: false

    // --- OFFSETS DE CALIBRACIÓN (Desde el JSON) ---
    property real offset_pitch: 0
    property real offset_roll: 0
    property real offset_yaw: 0
    
    property real altura: 0 
    property string modeloUrl: ""

    // --- SEÑAL PARA ACTIVAR ANIMACIONES EN PYTHON ---
    signal modeloCargado() 

    // --- FUNCIÓN DE RUTEO MATEMÁTICO ---
    // Intercambia y/o invierte los valores del cuaternión en tiempo real
    function getMappedValue(mapAxis, invert) {
        let val = 0.0;
        if (mapAxis === "X") val = root.q_x;
        else if (mapAxis === "Y") val = root.q_y;
        else if (mapAxis === "Z") val = root.q_z;
        
        return invert ? -val : val;
    }

    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            clearColor: "#101829"  
            backgroundMode: SceneEnvironment.Color 
            
            lightProbe: Texture {
                textureData: ProceduralSkyTextureData {}
            }
            probeExposure: 1.5 
            
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        PerspectiveCamera {
          id: cameraMain
          y: 30
            z: 300 
        }

        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: 45
            brightness: 1.5
            ambientColor: "#222222" 
            castsShadow: true       
            shadowFactor: 50        
        }
        
        DirectionalLight {
            eulerRotation.x: -10
            eulerRotation.y: -60
            brightness: 0.8
            color: "#aaccff" 
        }

        Model {
            id: pisoGrid
            y: -15 - (root.altura * 0.5) 
            z: -50
            scale: Qt.vector3d(200, 200, 200) 
            geometry: GridGeometry {
                horizontalLines: 550
                verticalLines: 100
            }
            materials: [
                DefaultMaterial {
                    diffuseColor: "#555D66" 
                    lighting: DefaultMaterial.NoLighting
                    opacity: 0.2 
                }
            ]
        }

        // --- CONTENEDOR PRINCIPAL DEL CANSAT ---
        Node {
            id: modeloCanSat
            
            // 1. ROTACIÓN DINÁMICA (CUATERNIONES MAPADOS)
            // Qt3D ejes: X (Pitch), Y (Yaw), Z (Roll)
            rotation: Qt.quaternion(
                root.q_w, 
                root.getMappedValue(root.map_pitch, root.invert_pitch), // Eje X del modelo
                root.getMappedValue(root.map_yaw, root.invert_yaw),     // Eje Y del modelo
                root.getMappedValue(root.map_roll, root.invert_roll)    // Eje Z del modelo
            )

            // 2. NODO DE CALIBRACIÓN INTERNO
            // Aplica la corrección inicial que configuraste en tu ventana de inicio
            Node {
                eulerRotation.x: root.offset_pitch
                eulerRotation.y: root.offset_yaw
                eulerRotation.z: root.offset_roll

                RuntimeLoader {
                    id: glbLoader
                    source: root.modeloUrl
                    
                    // --- DETECTOR DE CARGA ---
                    onStatusChanged: {
                        if (status === RuntimeLoader.Success) {
                            console.log("[QML] Modelo 3D cargado. Disparando señal a Python...");
                            root.modeloCargado(); 
                        } else if (status === RuntimeLoader.Error) {
                            console.error("[QML] ERROR al cargar el modelo 3D:", errorString);
                        }
                    }
                }
            }
        }

        OrbitCameraController {
            anchors.fill: parent
            origin: modeloCanSat 
            camera: cameraMain   
        }
    }
}
