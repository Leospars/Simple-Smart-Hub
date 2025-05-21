### ESP32 Dev Sensor Unit
## Objectives

- Read temperature and motion from environment
  
- Send POST requests to server to update database with current state at set time intervals which will then be retireived and updated on the website
 
# Carried out by the esp32 module
```jsx
POST /state

{
    "temperature": float
    "presence": bool
    "datetime": "2023-02-23T18:22:28"
}

```
