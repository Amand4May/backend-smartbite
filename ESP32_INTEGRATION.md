# ESP32 Integration Guide

## Visão Geral

O SmartBite permite que um dispositivo ESP32 se comunique com o backend através de HTTP/REST. O ESP32 pode:
- Reportar seu status (online/offline)
- Receber comandos para dispensar ração
- Enviar dados do nível de ração
- Enviar sinais de keep-alive

---

## Fluxo de Comunicação

```
┌─────────┐                                    ┌─────────┐
│ Frontend│                                    │ Backend │
└────┬────┘                                    └────┬────┘
     │                                              │
     │ 1. User clica "Liberar ração"               │
     ├─────────────────────────────────────────────┤
     │ 2. POST /api/v1/feeders/{id}/feed-command/ │
     │                                              │
     │                   ┌──────────────────────────┤
     │                   │ 3. Envia comando para ESP32
     │                   │    {type: "feed", portion_g: 80, ...}
     │                   │                          │
     │                   │    ┌──────────────────────┼──┐
     │                   │    │ ESP32 Dispensa Ração │  │
     │                   │    └──────────────────────┼──┘
     │                   │                          │
     │                   ├─ 4. ESP32 Reporta Status│
     │                   │    {type: "feed_done",  │
     │                   │     dispensed_g: 79.5}  │
     │                   │                          │
     │ ◄─────────────────┼──────────────────────────┤
     │ 5. Success response                         │
```

---

## Endpoints ESP32

### 1. Registrar Dispositivo

**Endpoint:** `POST /api/v1/esp32/register/`  
**Autenticação:** JWT Token (usuário)

Registra um novo dispositivo ESP32 na conta do usuário.

```bash
curl -X POST http://localhost:8000/api/v1/esp32/register/ \
  -H "Authorization: Token seu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "ESP32_ABC123",
    "device_name": "Comedouro da Sala"
  }'
```

**Response:**
```json
{
  "id": "uuid-aqui",
  "serial_number": "ESP32_ABC123",
  "device_name": "Comedouro da Sala",
  "registered_at": "2025-01-15T10:00:00Z",
  "status": "offline",
  "message": "Dispositivo registrado com sucesso!"
}
```

---

### 2. Heartbeat / Status Report

**Endpoint:** `POST /api/v1/esp32/heartbeat/`  
**Autenticação:** Nenhuma (device pode reportar livremente)

O ESP32 reporta seu status periodicamente (a cada 30-60 segundos).

```bash
curl -X POST http://localhost:8000/api/v1/esp32/heartbeat/ \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "ESP32_ABC123",
    "status": "online",
    "food_level_percent": 75,
    "wifi_signal": -45,
    "temperature": 28.5,
    "last_dispense": "2025-01-15T10:30:00Z"
  }'
```

**Response:**
```json
{
  "received": true,
  "timestamp": "2025-01-15T10:32:15Z",
  "message": "Heartbeat recebido com sucesso."
}
```

---

### 3. Comando de Alimentação

**Endpoint:** `POST /api/v1/feeders/{feeder_id}/feed-command/`  
**Autenticação:** JWT Token (usuário)

Envia um comando para o ESP32 dispensar ração.

```bash
curl -X POST http://localhost:8000/api/v1/feeders/{feeder_id}/feed-command/ \
  -H "Authorization: Token seu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_grams": 80
  }'
```

**Response:**
```json
{
  "status": "command_sent",
  "command": {
    "type": "feed",
    "portion_g": 80,
    "log_id": null,
    "timestamp": "2025-01-15T10:35:00Z"
  },
  "message": "Comando enviado: dispensar 80g",
  "note": "Aguarde confirmação do dispositivo..."
}
```

---

## Protocolo de Mensagens

### Mensagens Backend → ESP32

#### 1. Comando de Alimentação

```json
{
  "type": "feed",
  "portion_g": 80.2,
  "log_id": 42,
  "timestamp": "2025-01-15T10:35:00Z"
}
```

**Campos:**
- `type`: Sempre "feed"
- `portion_g`: Quantidade em gramas (com decimais)
- `log_id`: ID do registro para rastreamento
- `timestamp`: Quando o comando foi gerado

**Resposta esperada:** `{type: "feed_done", ...}`

---

### Mensagens ESP32 → Backend

#### 1. Confirmação de Dispensação

```json
{
  "type": "feed_done",
  "dispensed_g": 79.5,
  "log_id": 42,
  "pet_id": "uuid-do-pet",
  "duration_ms": 3200,
  "timestamp": "2025-01-15T10:35:03Z"
}
```

**Campos:**
- `type`: "feed_done"
- `dispensed_g`: Quantidade real dispensada (medida pelo sensor)
- `log_id`: Deve corresponder ao comando recebido
- `pet_id`: ID do pet alimentado
- `duration_ms`: Tempo total da dispensação
- `timestamp`: Quando a dispensação terminou

#### 2. Relatório de Nível de Ração

```json
{
  "type": "weight",
  "weight_g": 450.0,
  "battery_percent": 95,
  "timestamp": "2025-01-15T10:32:00Z"
}
```

**Campos:**
- `type`: "weight"
- `weight_g`: Peso atual da ração (em gramas)
- `battery_percent`: Bateria do sensor (%)
- `timestamp`: Quando foi medido

#### 3. Keep-Alive / Ping

```json
{
  "type": "ping",
  "uptime_s": 86400,
  "wifi_signal": -45,
  "temperature_c": 28.5
}
```

**Campos:**
- `type`: "ping"
- `uptime_s`: Tempo que o ESP32 está ligado (segundos)
- `wifi_signal`: Intensidade do sinal WiFi (dBm)
- `temperature_c`: Temperatura interna (opcional)

---

## Implementação no ESP32

### Setup WiFi & Autenticação

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "sua-rede";
const char* WIFI_PASSWORD = "sua-senha";
const char* BACKEND_URL = "http://seu-backend.onrender.com/api/v1";
const char* SERIAL_NUMBER = "ESP32_ABC123";

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi conectado!");
}
```

### Registrar Dispositivo

```cpp
void registerDevice() {
  HTTPClient http;
  String url = String(BACKEND_URL) + "/esp32/register/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["serial_number"] = SERIAL_NUMBER;
  doc["device_name"] = "Comedouro SmartBite";
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 201) {
    String response = http.getString();
    Serial.println("Registrado com sucesso!");
    // Parse response para obter device_id se necessário
  }
  
  http.end();
}
```

### Enviar Heartbeat

```cpp
void sendHeartbeat() {
  HTTPClient http;
  String url = String(BACKEND_URL) + "/esp32/heartbeat/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<300> doc;
  doc["serial_number"] = SERIAL_NUMBER;
  doc["status"] = "online";
  doc["food_level_percent"] = readFoodLevel();
  doc["wifi_signal"] = WiFi.RSSI();
  doc["temperature"] = readTemperature();
  doc["last_dispense"] = getLastDispenseTime();
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    Serial.println("Heartbeat enviado!");
  }
  
  http.end();
}

// Chame a cada 30-60 segundos
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000; // 30 segundos

void loop() {
  unsigned long now = millis();
  
  if (now - lastHeartbeat > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = now;
  }
}
```

### Processar Comando

```cpp
void checkForCommands() {
  // Você pode:
  // 1. Fazer polling de um endpoint GET
  // 2. Usar WebSocket para receber comandos em tempo real
  // 3. Usar MQTT
  
  // Exemplo com polling:
  HTTPClient http;
  String url = String(BACKEND_URL) + "/feeders/" + FEEDER_ID + "/commands/";
  
  http.begin(url);
  // Adicione auth token se necessário
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<300> doc;
    deserializeJson(doc, response);
    
    if (doc["type"] == "feed") {
      dispenseFeed(doc["portion_g"].as<float>());
      reportSuccess(doc["log_id"]);
    }
  }
  
  http.end();
}

void dispenseFeed(float grams) {
  Serial.println("Dispensando " + String(grams) + "g");
  
  // Ative servo motor
  // Mede com sensor de peso
  
  float dispensed = readActualAmount(); // Lê sensor
  reportDispenseDone(dispensed);
}

void reportDispenseDone(float dispensedGrams) {
  HTTPClient http;
  String url = String(BACKEND_URL) + "/esp32/feed-done/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<300> doc;
  doc["type"] = "feed_done";
  doc["dispensed_g"] = dispensedGrams;
  doc["log_id"] = lastCommandLogId;
  doc["pet_id"] = CURRENT_PET_ID;
  doc["duration_ms"] = millis() - dispensStartTime;
  
  String payload;
  serializeJson(doc, payload);
  
  http.POST(payload);
  http.end();
}
```

---

## Tratamento de Erros

### ESP32 Offline

Se o heartbeat não for recebido por > 2 minutos, o dispositivo é marcado como offline e o frontend é notificado.

### Falha na Dispensação

Se `dispensed_g` for significativamente diferente do esperado, crie um alerta.

```
Esperado: 100g
Dispensado: 65g
Alerta: "Falha parcial na dispensação - possível entupimento"
```

---

## Testing

### Testar Heartbeat

```bash
curl -X POST http://localhost:8000/api/v1/esp32/heartbeat/ \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "TEST_123",
    "status": "online",
    "food_level_percent": 50,
    "wifi_signal": -45
  }'
```

### Testar Comando de Alimentação

```bash
# 1. Registrar
curl -X POST http://localhost:8000/api/v1/esp32/register/ \
  -H "Authorization: Token seu-token" \
  -H "Content-Type: application/json" \
  -d '{"serial_number":"TEST_123","device_name":"Teste"}'

# Copie o {feeder_id} retornado

# 2. Enviar comando
curl -X POST http://localhost:8000/api/v1/feeders/{feeder_id}/feed-command/ \
  -H "Authorization: Token seu-token" \
  -H "Content-Type: application/json" \
  -d '{"amount_grams": 100}'
```

---

## Melhorias Futuras

- [ ] WebSocket para comandos em tempo real
- [ ] MQTT para comunicação mais leve
- [ ] OTA (Over-the-Air) updates
- [ ] Certificados SSL/TLS
- [ ] Rate limiting
- [ ] Autenticação mTLS
