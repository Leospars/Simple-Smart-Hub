#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "env.h"

#define LED_PIN 22 //Built-in LED
#define TEMP_SENSOR 5 
#define MOTION_PIN 12

OneWire oneWire(TEMP_SENSOR); // For DS18B20 Temp Sensor
DallasTemperature tempSensor(&oneWire);

void setup()
{
  Serial.begin(115200);
  pinMode(TEMP_SENSOR, INPUT);
  tempSensor.begin();

  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTION_PIN, INPUT);
  digitalWrite(LED_PIN, LOW);
}

void loop()
{
  tempSensor.requestTemperatures();
  delay(20);
  float temp = tempSensor.getTempCByIndex(0);
  Serial.print("Temperature: ");
  Serial.println(temp);

  bool presence = digitalRead(MOTION_PIN);
  if(presence){
Serial.println("Detecting motion");
  }else {
    Serial.println("Waiting.. no-one here");
  }

  // Blink the LED
  digitalWrite(LED_PIN, HIGH);
  delay(250);
  digitalWrite(LED_PIN, LOW);
  delay(750);
}