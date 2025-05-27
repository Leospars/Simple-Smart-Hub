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
#define FAN_PIN 21

OneWire oneWire(TEMP_SENSOR); // For DS18B20 Temp Sensor
DallasTemperature tempSensor(&oneWire);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);
HTTPClient http;

int isTimeGreater(String, String);

template<typename T>
void serialPrint(T arg) {
  Serial.print(arg);
}

template<typename T, typename... Args>
void serialPrint(T first, Args... args) {
  Serial.print(first);
  serialPrint(args...);
}

template<typename T, typename... Args>
void serialPrintln(T first, Args... args) {
  Serial.print(first);
  serialPrint(args...);
  Serial.println();
}

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

  timeClient.begin();
  timeClient.setTimeOffset(-5 * 3600); // Set offset to GMT-5 (EST)
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
    String presence_str = "false";
    if(presence){
      Serial.println("Detecting motion");
      presence_str = "true";
    }
    else {
      Serial.println("Nothing moving here 😔🚶‍♂️");
      presence_str = "false";
    }

    //Get timestamp
    while(!timeClient.update()){
      timeClient.forceUpdate();
      Serial.println("Forced update time");
    }
    String timestamp = timeClient.getFormattedDate();

    String body = "{\"temperature\": " + String(temp) + ","
                    "\"presence\": " + presence_str + ","
                    "\"datetime\": \"" + timestamp + "\""
                  "}";
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
      delay(100);
      return;
    }  
    serialPrint("Post Request Response code: ", responseCode, "\r\n\n");

    http.begin(SETTINGS_ENDPOINT);
    responseCode = http.GET();
    if(responseCode <= 0){
      Serial.print("> Error code: ");
      Serial.println(responseCode);
      http.end();
      delay(100);
      return;
    }

    String response = http.getString();
    serialPrintln("User settings: ", response);

    JsonDocument settings;
    DeserializationError deserialize_error = deserializeJson(settings, response);

    if(deserialize_error.code() > 0){
      Serial.print("Error Deserializing code: ");
      Serial.println(deserialize_error.code());
      http.end();
      delay(100);
      return;
    }
    
    // Polling to check user set thresholds
    if(temp > float(settings["user_temp"])){
      digitalWrite(FAN_PIN, HIGH);
    }

    // Date Time format: "datetime": "2023-02-23T18:22:28"
    String time_now =  timestamp.substring(11);
    serialPrintln("Time now: ", time_now);

    if (isTimeGreater(time_now, settings["light_time_off"]) >= 0)
    {
      Serial.println("Keep Light Off");
      digitalWrite(LED_PIN, LOW);
    } else if (isTimeGreater(time_now, settings["user_light"]) >= 0){
      Serial.println("Keep Light On");
      digitalWrite(LED_PIN, HIGH);
    }
  }

  delay(1000);
}

/* Time Format: "time": "18:22:28"
  Returns, 1 if t1 > t2 and 0 if equal and -1 t2 is greater
*/
int isTimeGreater(String t1, String t2){
  uint hr1, min1, sec1, hr2, min2, sec2;

  try{
    hr1 = t1.substring(0,2).toInt();
    min1 = t1.substring(3,5).toInt();
    sec1 = t1.substring(6,8).toInt();

    hr2 = t2.substring(0,2).toInt();
    min2 = t2.substring(3,5).toInt();
    sec2 = t2.substring(6,8).toInt();
  }
  catch(int error){
    throw Serial.println("Invalid Time String Format");
  }

  serialPrint("T1: ", hr1, ":", min1, ":", sec1, "\r\n");
  serialPrint("T2: ", hr2, ":", min2, ":", sec2, "\r\n");
  long unsigned int epoch_t1 = hr1 * 3600 + min1 * 60 + sec1;
  long unsigned int epoch_t2 = hr2 * 3600 + min2 * 60 + sec2;

  if (epoch_t1 > epoch_t2)
    return 1;
  else if (epoch_t1 == epoch_t2) 
    return 0;
  else return -1;
}