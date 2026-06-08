# 📡 ESP32 + BMP280 — Dashboard de Monitoreo
> Caso de estudio · Maestría en Ingeniería de Software

Dashboard en tiempo real con histórico de temperatura, presión, altitud y señal WiFi.  
Stack: **ESP32 → Firebase RTDB → Streamlit Cloud** (100% gratuito)

---

## 🗂️ Estructura del proyecto

```
esp32-dashboard/
├── app.py                  ← Dashboard principal
├── requirements.txt        ← Dependencias Python
├── .gitignore              ← Protege tus credenciales
├── .streamlit/
│   └── secrets.toml        ← Variables secretas (NO subir a GitHub)
└── README.md
```

---

## ✅ Paso 1 — Verificar estructura en Firebase RTDB

Asegúrate de que tus datos llegan con esta estructura:

```json
{
  "lecturas": {
    "-NxAbc123": {
      "fecha":       "2025-06-05T10:30:00",
      "temperatura": 23.5,
      "presion":     1013.25,
      "altitud":     1580.0,
      "wifi":        -65
    },
    "-NxAbc124": { ... }
  }
}
```

**Nombres de campos requeridos exactos:**
| Campo | Tipo | Ejemplo |
|---|---|---|
| `fecha` | String ISO 8601 | `"2025-06-05T10:30:00"` |
| `temperatura` | Float | `23.5` |
| `presion` | Float | `1013.25` |
| `altitud` | Float | `1580.0` |
| `wifi` | Int (RSSI) | `-65` |

---

## ✅ Paso 2 — Obtener Service Account Key de Firebase

1. Ir a [Firebase Console](https://console.firebase.google.com)
2. Selecciona tu proyecto → ⚙️ **Configuración del proyecto**
3. Pestaña **"Cuentas de servicio"**
4. Clic en **"Generar nueva clave privada"** → descarga el JSON
5. Renómbralo `serviceAccountKey.json` y colócalo en la raíz del proyecto  
   ⚠️ **Nunca lo subas a GitHub** (está en `.gitignore`)

---

## ✅ Paso 3 — Configurar secrets.toml (local)

Edita `.streamlit/secrets.toml` con tus datos reales:

```toml
[firebase]
database_url = "https://MI-PROYECTO-default-rtdb.firebaseio.com"
nodo_raiz    = "lecturas"
```

---

## ✅ Paso 4 — Probar localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

Abre `http://localhost:8501` en tu navegador.

---

## ✅ Paso 5 — Subir a GitHub

```bash
git init
git add app.py requirements.txt .gitignore README.md
# NO agregues serviceAccountKey.json ni secrets.toml
git commit -m "feat: dashboard ESP32 BMP280"
git remote add origin https://github.com/TU_USUARIO/esp32-dashboard.git
git push -u origin main
```

---

## ✅ Paso 6 — Desplegar en Streamlit Cloud (gratis)

1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Clic en **"New app"** → conectar tu repositorio GitHub
3. Selecciona `app.py` como archivo principal
4. Ir a **"Advanced settings"** → **"Secrets"**
5. Pegar el contenido de tu `secrets.toml` (con los valores reales)
6. Clic **"Deploy"** → en ~2 minutos tendrás tu URL pública 🎉

### URL resultante:
```
https://tu-usuario-esp32-dashboard-app-XXXX.streamlit.app
```

Accesible desde cualquier navegador, móvil o PC.

---

## 🔌 Código ESP32 — Agregar campo RSSI (WiFi)

Si aún no envías el campo `wifi` (señal RSSI), agrega esto en tu sketch:

```cpp
// En el JSON que construyes antes de enviar a Firebase:
FirebaseJson json;
json.set("temperatura", bmp.readTemperature());
json.set("presion",     bmp.readPressure() / 100.0F);
json.set("altitud",     bmp.readAltitude(1013.25));
json.set("wifi",        WiFi.RSSI());          // ← agregar esta línea
json.set("fecha",       obtenerFechaISO());    // tu función de fecha
```

---

## 📊 Funcionalidades del dashboard

| Feature | Descripción |
|---|---|
| 🔵 Métricas en tiempo real | 5 tarjetas con los últimos valores |
| 📈 Gráfico histórico | Multi-variable, filtro por N registros |
| ⚡ Gráfico tiempo real | Últimas 20 lecturas con área rellena |
| 🗃️ Tabla de datos | Últimos 100 registros exportables |
| 🔄 Auto-refresh | Se actualiza cada 30 segundos automáticamente |

---

## 🎓 Para la maestría

Este proyecto demuestra:
- Arquitectura **IoT → Cloud → Dashboard**
- Integración **Firebase RTDB** con Python
- Visualización de datos en **tiempo real**
- Despliegue **serverless** sin infraestructura propia
- Seguridad de credenciales con **Secrets Management**
