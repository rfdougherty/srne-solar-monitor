/*
Solar Monitor

Solarmon is a solar monitor that uses a Modbus RTU client to read the data from a solar inverter.
Board: XIAO ESP32S3

Port: 502
IP: 192.168.1.69
*/

// =================================================================================================
// eModbus: Copyright 2020 by Michael Harwerth, Bert Melis and the contributors to ModbusClient
//               MIT license - see license.md for details
// =================================================================================================

#include <Arduino.h>
#include <ArduinoOTA.h>
#include <Streaming.h>
#include "HardwareSerial.h"
#include <WiFi.h>

// Modbus bridge include
#include "ModbusBridgeWiFi.h"
// Modbus RTU client include
#include "ModbusClientRTU.h"
// Turns out you need to edit Logging.h to change log level
#define LOG_LEVEL LOG_LEVEL_DEBUG
#include "Logging.h"

#ifndef MY_SSID
#define MY_SSID "myssid"
#endif
#ifndef MY_PASS
#define MY_PASS "mypassword"
#endif

#define STAT_LED 21 // LED_BUILTIN is GPIO21 on xiao s3
#define LED_ON LOW // On most boards this is LOW
#define RS485_RX 9 // D10 on XIAO ESP32S3
#define RS485_TX 8 // D09 on XIAO ESP32S3

char ssid[] = MY_SSID;                     // SSID and ...
char pass[] = MY_PASS;                     // password for the WiFi network used
uint16_t port = 502;                       // port of modbus server

// Create a ModbusRTU client instance
ModbusClientRTU MB;

// Create bridge
ModbusBridgeWiFi MBbridge;

// Setup() - initialization happens here
void setup() {
// Init Serial monitor
  Serial.begin(115200);
  //while (!Serial) {}
  delay(1000);
  Serial.println("__ OK __");

  pinMode(STAT_LED, OUTPUT);
  digitalWrite(STAT_LED, LOW);

// Init Serial2 conneted to the RTU Modbus
// (Fill in your data here!)
  RTUutils::prepareHardwareSerial(Serial2);
  Serial2.begin(9600, SERIAL_8N1, RS485_RX, RS485_TX);

// Connect to WiFi
  WiFi.begin(ssid, pass);
  delay(200);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
  IPAddress wIP = WiFi.localIP();
  Serial.printf("IP address: %u.%u.%u.%u\n", wIP[0], wIP[1], wIP[2], wIP[3]);

// Set RTU (RS485) Modbus message timeout
  MB.setTimeout(1000);
// Start ModbusRTU background task on core 1
  MB.begin(Serial2, 1);

// Define and start WiFi bridge
// ServerID 1: Server with remote serverID 1, accessed through RTU client MB
//             All FCs accepted, with the exception of FC 06
  MBbridge.attachServer(1, 1, ANY_FUNCTION_CODE, &MB);
  //MBbridge.denyFunctionCode(4, 6);

// Check: print out all combinations served to Serial
  MBbridge.listServer();

// Start the bridge. Args: port, # simultaneous clients allowed, milliseconds of inactivity to disconnect client
  MBbridge.start(port, 4, 600);

  ArduinoOTA
    .onStart([]() {
      String type;
      if (ArduinoOTA.getCommand() == U_FLASH)
        type = "sketch";
      else // U_SPIFFS
        type = "filesystem";

      // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
      Serial.println("Start updating " + type);
    })
    .onEnd([]() {
      Serial.println("\nEnd");
    })
    .onProgress([](unsigned int progress, unsigned int total) {
      Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
    })
    .onError([](ota_error_t error) {
      Serial.printf("Error[%u]: ", error);
      if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
      else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
      else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
      else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
      else if (error == OTA_END_ERROR) Serial.println("End Failed");
    });
  ArduinoOTA.begin();
  Serial.println("OTA begun");

  Serial.printf("Use the shown IP and port %d to send requests!\n", port);

  digitalWrite(STAT_LED, HIGH);

// Your output on the Serial monitor should start with:
//      __ OK __
//      .IP address: 192.168.178.74
//      [N] 1324| ModbusServer.cpp     [ 127] listServer: Server   4:  00 06
//      [N] 1324| ModbusServer.cpp     [ 127] listServer: Server   5:  03 04
//      Use the shown IP and port 502 to send requests!
}

// loop() - nothing done here today!
void loop() {
  char cmd;

  ArduinoOTA.handle();

  // Check if data is available to read from the serial port
  if (Serial.available() > 0) {
    cmd = Serial.read(); // Read the incoming character

    // Process the command using a switch statement
    switch (cmd) {
      case 's':
        Serial << F("Signal Strength: ") << WiFi.RSSI() << F(" dBm") << endl;
        //Serial.printf("Signal Strength: %d dBm\n", WiFi.RSSI());
        break;
      case '0':
        Serial.println("Do something else");
        break;
      default:
        Serial << F("Invalid command received: '") << cmd << F("'.") << endl;
        break;
    }
    // Clear the buffer (e.g., there is likely a newline)
    while (Serial.available() > 0)
      Serial.read();
  }

  heartbeat(1);
  yield();
}

void heartbeat(uint8_t num_blinks) {
  // if num_blinks==0, the led will stay on.
  static uint32_t prev_millis;
  static uint32_t prev_blink_millis;
  static uint8_t led_state;
  uint32_t cur_millis = millis();
  const uint32_t flash_interval = 3000;
  if (num_blinks == 0) {
    digitalWrite(STAT_LED, LED_ON);
    return;
  }
  if (led_state) {
    if (cur_millis - prev_blink_millis > 7) {
      // Toggle the led's state
      digitalWrite(STAT_LED, !digitalRead(STAT_LED));
      led_state--;
      prev_blink_millis = cur_millis;
    }
  } else {
    if (cur_millis - prev_millis > flash_interval) {
      digitalWrite(STAT_LED, LED_ON);
      led_state = (num_blinks - 1) * 2 + 1;
      prev_millis = cur_millis;
      prev_blink_millis = cur_millis;
    }
  }
}
