# cbpi-OneWireTweaks

## Introduction

Plugin for [CraftBeerPi3](http://web.craftbeerpi.com/) [[GitHub](https://github.com/Manuel83/craftbeerpi3)].
This CraftBeerPi 3.0 plugin was based on [OneWireAdvanced](https://github.com/jangevaare/cbpi-OneWireAdvanced/), that is no longer being maintained. It provides a new sensor type called OneWireTweaks. This plugin attempts to provide even more control over DS18B20 temperature readings in CraftBeerPi. It allows setting of:

- sensor calibration based on quadratic error, that is standard for DS18B20.Based on a quadratic regression it is possible to determine the bias,linear coeficient and quatratic coeficient
- sensor precision, allowing faster temperature reading
- exponential moving average,to reduce noise from the sensor output
- low and high value filters,
- update interval, and,
- alert options.

## Installation

- Clone the repo into the CBPi3 _plugins_ directory:

```
cd craftbeerpi3/modules/plugins   ### CHANGE THIS TO YOUR CBPi3 DIRECTORY
git clone https://github.com/diogavila/cbpi-OneWireTweaks.git
```

For one-liners:

```
git clone https://github.com/diogavila/cbpi-OneWireTweaks.git ~/craftbeerpi3/modules/plugins/OneWireTweaks
```

- Restart CraftBeerPi3.

```
sudo /etc/init.d/craftbeerpiboot restart
```

## Usage

All you need to do is install the plugin, set the sensors as OneWireTweaks and set the desired parameters.

## Author

- [Diogo d'Ávila](https://github.com/diogavila)

## Preview

<center><img src="OneWireAdvanced.png" width="480" alt="Sensor configuration options"></center>
