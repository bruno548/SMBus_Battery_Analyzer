#include <SoftwareWire.h>

// ============================================
// SMBus Battery Analyzer - Versão Segura Estabilizada
// Software I2C usando: A2 = SDA | A3 = SCL
// ============================================

#define BATTERY_ADDR 0x0B

SoftwareWire myWire(A2, A3);

// ============================================
// READ WORD (Tratando inteiros de 16 bits)
// ============================================
uint16_t readWord(uint8_t reg) {
  myWire.beginTransmission(BATTERY_ADDR);
  myWire.write(reg);
  if (myWire.endTransmission(false) != 0) {
    return 0xFFFF;
  }
  myWire.requestFrom((uint8_t)BATTERY_ADDR, (uint8_t)2);
  if (myWire.available() < 2) {
    return 0xFFFF;
  }
  uint8_t low = myWire.read();
  uint8_t high = myWire.read();
  return (high << 8) | low;
}

// ============================================
// READ STRING (Com limpeza estrita de caracteres)
// ============================================
String readString(uint8_t reg) {
  myWire.beginTransmission(BATTERY_ADDR);
  myWire.write(reg);
  if (myWire.endTransmission(false) != 0) {
    return "ERR";
  }
  myWire.requestFrom((uint8_t)BATTERY_ADDR, (uint8_t)32);
  if (!myWire.available()) {
    return "N/A";
  }
  
  uint8_t length = myWire.read();
  String result = "";
  
  for (int i = 0; i < length; i++) {
    if (myWire.available()) {
      char c = myWire.read();
      if (isalnum(c) || c == ' ' || c == '-' || c == '_') {
        result += c;
      }
    }
  }
  result.trim();
  return (result.length() > 0) ? result : "UNKNOWN";
}

void setup() {
  Serial.begin(115200);
  myWire.begin();
}

void loop() {
  // Coletas estáveis do barramento SMBus
  uint16_t voltage   = readWord(0x09);
  int16_t  current   = readWord(0x0A); 
  uint16_t remCap    = readWord(0x0F);
  uint16_t fullCap   = readWord(0x10);
  uint16_t designCap = readWord(0x18);
  uint16_t temp      = readWord(0x08);
  uint16_t cycles    = readWord(0x17);
  uint16_t soc       = readWord(0x0D);

  // Registradores de alvos de carga e status do protocolo
  uint16_t chgCurrent = readWord(0x14); 
  uint16_t chgVoltage = readWord(0x15); 
  uint16_t battStatus = readWord(0x16); // Registrador universal estável

  String manufacturer = readString(0x20);
  String device       = readString(0x21);
  String chemistry    = readString(0x22);

  float health = -1;
  if (designCap != 0 && designCap != 0xFFFF && fullCap != 0xFFFF) {
    health = ((float)fullCap / (float)designCap) * 100.0;
  }

  // Montagem limpa e atômica do JSON
  String jsonOutput = "{";
  jsonOutput += "\"v\":" + String(voltage) + ",";
  jsonOutput += "\"i\":" + String(current) + ",";
  jsonOutput += "\"rc\":" + String(remCap) + ",";
  jsonOutput += "\"fc\":" + String(fullCap) + ",";
  jsonOutput += "\"dc\":" + String(designCap) + ",";
  jsonOutput += "\"t\":" + String(temp) + ",";
  jsonOutput += "\"cy\":" + String(cycles) + ",";
  jsonOutput += "\"soc\":" + String(soc) + ",";
  jsonOutput += "\"h\":" + String(health, 1) + ",";
  jsonOutput += "\"cc\":" + String(chgCurrent) + ",";
  jsonOutput += "\"cv\":" + String(chgVoltage) + ",";
  jsonOutput += "\"bs\":" + String(battStatus) + ",";
  jsonOutput += "\"mf\":\"" + manufacturer + "\",";
  jsonOutput += "\"dev\":\"" + device + "\",";
  jsonOutput += "\"chem\":\"" + chemistry + "\"";
  jsonOutput += "}";

  // Envia a linha inteira de uma vez para o Python
  Serial.println(jsonOutput);

  delay(1000); 
}