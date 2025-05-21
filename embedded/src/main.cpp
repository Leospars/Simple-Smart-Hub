#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#include <ArduinoJson.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <NTPClient.h>
#include <string.h>
#include "env.h"

#define LED_PIN 22
#define TEMP_SENSOR 5 
#define MOTION_PIN 12

OneWire oneWire(TEMP_SENSOR); // For DS18B20 Temp Sensor
DallasTemperature tempSensor(&oneWire);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);

void setup()
{
  Serial.begin(115200);
  pinMode(TEMP_SENSOR, INPUT);
  tempSensor.begin();

  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTION_PIN, INPUT);
  digitalWrite(LED_PIN, LOW);

  if (IS_WOKWI)
    WiFi.begin(WOKWI_SSID, WOKWI_PWD, CHANNEL);
  else
    WiFi.begin(SSID, PWD);

  bool led_state = false;
  Serial.begin(115200);
  Serial.print("Connecting ");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(100);
    Serial.print(".");
    digitalWrite(LED_PIN, led_state);
    led_state = !led_state;
    delay(200);
  }
  
  digitalWrite(LED_PIN, LOW);

  Serial.print("\nConnected to with IP: ");
  Serial.println(WiFi.localIP());
}

void loop()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    tempSensor.requestTemperatures();
    delay(20);
    float temp = tempSensor.getTempCByIndex(0);

    Serial.print("Temperature: ");
    Serial.println(temp);

    bool presence = digitalRead(MOTION_PIN);
    if(presence)
      Serial.println("Detecting motion");
    else 
      Serial.println("Waiting.. no-one here");

    // Blink the LED
    digitalWrite(LED_PIN, presence);

    //Get timestamp
    timeClient.begin();
    while(!timeClient.update()){
      timeClient.forceUpdate();
      Serial.print("Forced update time");
    }
    String timestamp = timeClient.getFormattedDate();

    HTTPClient http;
    String body = "{\"temperature\": " + String(temp) + ",\
                    \"presence\": " + String(presence) + ",\
                    \"datetime\": \"" + timestamp + "\",\
                  }";
    Serial.print("body: ");
    Serial.println(body);

    http.begin(ENDPOINT); 
    http.addHeader("Content-Type", "application/json");
    
    int responseCode = http.POST(body);
    if (responseCode <= 0)
    {
      Serial.print("> Error code: ");
      Serial.println(responseCode);
      http.end();
      delay(200);
      return;
    }  
  }

  delay(1000);
}
