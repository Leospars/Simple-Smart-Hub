## ESP32 Dev Sensor Unit
## Objectives

- Read temperature and motion from environment
  
- Send POST requests to server at set interval to update database with current environment state which will then be retireived and updated on the website
 
## Additional Details
Post request outline
```jsx
POST /state

{
    "temperature": 23.42,
    "presence": true,
    "datetime": "2023-02-23T18:22:28"
}

```

GET settings example
```jsx
    GET /settings?_id={_id}

    {
      "_id": {database defined _id}
    	"user_temp": 30, 
      "user_light": "18:30:00", 
      "light_time_off": "22:30:00"
    }
```


Example `env.h` for user specific details
```c
#ifndef ENV_H
#define ENV_H

#define WOKWI_SSID "Wokwi-GUEST"
#define WOKWI_PWD ""
#define CHANNEL 6
#define IS_WOKWI true

const char* SSID = "ssid";
const char* PWD = "********";
const char* ENDPOINT = "http://127.0.0.1:8000/state";

#endif // ENV_H
```

NTPClient Library was sourced from [taranais/NTPClient](https://github.com/taranais/NTPClient) to get the `timeClient.getFormattedDate` method which is not available in the PIO NTPClient Library