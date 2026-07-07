# 🔋 SMBus Battery Analyzer PRO+

Este projeto é um analisador e diagnosticador de baterias inteligentes de notebooks baseado no protocolo global **Smart Battery Data Specification (SMBus)**. Utilizando um Arduino (via emulação de I2C por software) e uma interface gráfica moderna em Python (Tkinter), a ferramenta realiza leituras elétricas precisas e decodifica registradores internos da BMS em tempo real, permitindo identificar falhas físicas e estados de segurança de forma visual.

![Interface Pro](https://img.shields.io/badge/UI-Tkinter%20Dark%20Mode-blue)
![Arduino](https://img.shields.io/badge/Hardware-Arduino%20Uno%2FNano-orange)
![SMBus](https://img.shields.io/badge/Protocol-SMBus%20%2F%20I2C-green)

---

## 🚀 Recursos Principais

- **Leitura Universal SMBus:** Monitoramento estável de Tensão ($mV$), Corrente ($mA$), Capacidade Restante ($mAh$), Capacidade Total ($mAh$), Contagem de Ciclos e Temperatura ($°C$).
- **Diagnóstico Estrito de Falhas (Fim das Deduções):**
  - **BMS Hardware Protections:** Identifica alertas de proteção ativos como `OVER_CHARGED`, `TERMINATE_CHARGE`, `OVER_TEMP` e `TERMINATE_DISCHARGE`.
  - **Permanent Failure Decoder:** Avalia o comportamento da bateria e acusa textualmente falhas permanentes de hardware, como **`CELL UNDERVOLTAGE / HW TRIP`** (Subtensão crítica por tempo de estoque) ou **`OPERATIONAL (STANDBY / FULL)`**.
- **Protocol Error Tracker:** Monitora os 4 bits inferiores do registrador `BatteryStatus (0x16)` para capturar erros nativos do barramento (ex: *BMS Busy, Rejected Command, Unsupported Command, Access Denied*).
- **Interface Gráfica PRO+:** Painel responsivo em modo escuro estruturado em Tkinter com arquitetura multi-threading (evita o travamento da interface durante a coleta serial).

---

## 🛠️ Arquitetura do Projeto

O projeto é composto por dois componentes principais que trabalham de forma integrada:

1. **Firmware do Arduino (`finalbtty.ino`):** Atua como uma ponte de hardware. Ele interroga os registradores hexadecimais da bateria usando a biblioteca `SoftwareWire` (linhas SDA/SCL emuladas), trata inteiros com sinal (corrente negativa) e empacota todos os dados em uma string **JSON atômica** enviada a 115200 baud pela porta serial.
2. **Aplicação Desktop Python (`app2.py`):** Captura o buffer serial de forma assíncrona, faz o parse do JSON e atualiza os cartões de métricas da interface gráfica, gerenciando localmente as conversões matemáticas (como *Decikelvin para Celsius*).

---

## 🔌 Esquema de Ligação (Hardware)

Para realizar a análise em bancada, faça as conexões entre o Arduino e o conector da bateria de notebook seguindo o pinout abaixo:

| Pino da Bateria | Pino do Arduino | Observação |
| :--- | :--- | :--- |
| **GND** (Negativo) | **GND** | **Obrigatório:** Referência comum de sinal. |
| **SDA** (Data) | **A2** | Linha de dados I2C. |
| **SCL** (Clock) | **A3** | Linha de clock I2C. |
| **SYS_PRES** (ID) | **GND** | *Opcional/Recomendado:* Algumas marcas (Dell/HP) exigem este pino aterrado para "acordar" a BMS. |

⚠️ **IMPORTANTE:** O barramento I2C requer resistores de **Pull-up**. Conecte um resistor de $4.7\text{ k}\Omega$ a $10\text{ k}\Omega$ do pino **A2 para o 5V** do Arduino, e outro do pino **A3 para o 5V**.

---

## 💻 Instalação e Execução

### 1. Gravação do Arduino
1. Abra o arquivo `finalbtty.ino` na Arduino IDE.
2. Certifique-se de ter a biblioteca `SoftwareWire` instalada.
3. Selecione a sua placa (Uno, Nano, Mega) e compile/grave o código.

### 2. Configuração do Ambiente Python
Certifique-se de ter o Python 3.8+ instalado e instale a dependência de comunicação serial:

```bash
pip install pyserial
