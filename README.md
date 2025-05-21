# Simple Smart Hub

The goal of this project is to build an IoT solution that toggles a fan and a light based on temperature, time of day or motion, ith a user friendly interactive web interface: __[Simple Smart Hub Client](https://simple-smart-hub-client.netlify.app/)__.

The platform will require:

1. An Espressif ESP32 development module.
2. Two simple load/actuator components, eg. LEDs or a lamp and a fan.
3. A RESTful API written using the FastAPI Python framework.
   
4. A MongoDB database to store user setting and track enviroment changes.

The platform should also allow users to interact with the IoT devices through the use of a webpage.

## Requirements

The API should allow for effective communication among all components of the platform.

The IoT platform should include a feature that allows users to specify a temperature after which the fan should turn on.

The IoT platform should include a feature that allows users to specify a time after which the lights should turn on.

The IoT platform should include a feature that allows users to specify a time duration for which the lights should stay on.

The IoT platform should include a feature that uses a sensor to detect whether a person is present in the room.

The IoT platform should combine the temperature-based control, time-base control and presence detection features so that the controlled appliances only turns on if each set relevant conditions is met.

## UI

To provide users with greater control over the IoT platform, they should be able to customize various settings. For example, the user should be able to specify the temperature at which the fan should turn on. Similarly, the user should be able to customize the time after which the lights should turn on and the duration for which they should stay on. These customizable settings can be accessed via a web interface (https://simple-smart-hub-client.netlify.app/) that allows the user to input their preferred values. By providing these customization options, the IoT platform can be tailored to the specific needs of the user, making it more effective and user-friendly.

By implementing these features, the IoT platform can ensure that the lights only turn on when they are needed. This can save energy and reduce unnecessary light pollution. Additionally, the fan only turns on when the room temperature exceeds the user-specified temperature and a person is present. This can help save energy and create a more comfortable living environment.

## [ESP32 Program Details](https://github.com/Leospars/Simple-Smart-Hub/blob/main/embedded/README.md)

## [More Details](https://github.com/Leospars/Simple-Smart-Hub/blob/main/Simple%20Smart%20Hub.md)
