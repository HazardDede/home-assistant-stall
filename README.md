# Stall Binary sensor

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]](hacs)
![Project Maintenance][maintenance-shield]


> Home Assistant sensor to determine if a sensor was not updated for a given time

## Installation

**HACS**

1. Make sure the [HACS](https://github.com/custom-components/hacs) component is installed and working.
2. Add this github repository https://github.com/HazardDede/home-assistant-stall as custom integration repository in HACS settings.
3. Install the integration `stall` and update home assistant configuration accordingly. You need to restart home assistant for the changes to take effect.

**Manual**

1. Copy the `stall` folder into your `custom_components` folder that is located under the root of your `home assistant config`. 
If it does not exists you can create it (which probably means you never used a custom component before).


## Configuration

To integrate the `stall` binary sensor to your Home Assistant instance, you need to add the following section to your `configuration.yaml`:

Minimal example:

```yaml
# Will go into the `problem` state after 60 minutes 
# if no state change for sun.sun was experienced
binary_sensor:
  - platform: stall
    entities:
      - sun.sun  # The entity to track for changes
```

Full example:

```yaml
# Will go into the `problem` state after 1 minute 
# if no state change for sun.sun was experienced
binary_sensor:
  - platform: stall
    name: Sun (Stall)  # Override th default name of 'Stall'
    entities:
      - sun.sun
    threshold: 1  # in minutes
```

You can pass multiple entities to the `stall` binary sensor. If you do any state change
of the passed entities will reset the internal timer. So in short: It is not used to
track multiple entities, but a single device that could have multiple sensors.

Personally I use this to track environment sensor's who do track motion, illumination, temperature
but are battery powered. In the past it took me some time to figure out that a sensor is down due to battery drain
(because it does unfortunately report it's battery level pretty unreliable).


```yaml
# Will go into the `problem` state after 60 minutes
# after no state change from any of the passed entities was experienced.
binary_sensor:
  - platform: stall
    name: Device (Stall)  # Override th default name of 'Stall'
    entities:
      - sensor.temperature
      - sensor.illumination
      - binary_sensor.motion
    threshold: 60  # in minutes
```

If you want to track multiple entities independently you have to configure multiple sensors:

```yaml
binary_sensor:
  - platform: stall
    name: Sun (Stall)
    entities:
      - sun.sun
  - platform: stall
    name: Weather (Stall)
    entities:
      - weather.home
```


<!---->

***

[commits-shield]: https://img.shields.io/github/commit-activity/y/HazardDede/home-assistant-stall.svg?style=for-the-badge
[commits]: https://github.com/HazardDede/home-assistant-stall/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/HazardDede/home-assistant-stall.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Dennis%20Muth%20%40HazardDede-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/HazardDede/home-assistant-stall.svg?style=for-the-badge
[releases]: https://github.com/HazardDede/home-assistant-stall/releases