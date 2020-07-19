# -*- coding: utf-8 -*-
import os
import subprocess
import time

from modules import cbpi
from modules.core.hardware import SensorActive
from modules.core.props import Property


def ifelse_celcius(x, y):
    if cbpi.get_config_parameter("unit", "C") == "C":
        return x
    else:
        return y


def get_sensors():
    try:
        arr = []
        for dirname in os.listdir("/sys/bus/w1/devices"):
            if dirname.startswith("28") or dirname.startswith("10"):
                arr.append(dirname)
        return arr
    except:
        return []


def set_precision(precision, address):
    if not 9 <= precision <= 12:
        raise ValueError(
            f"The given sensor precision '{precision}' is out of range (9-12)"
        )
    exitcode = subprocess.call(
        f"echo {precision} > /sys/bus/w1/devices/{address}/w1_slave", shell=True,
    )
    if exitcode != 0:
        raise UserWarning(
            "Failed to change resolution to {precision} bit. You might have to be root to change the precision"
        )


def get_temp(address):
    with open(
        f"/sys/bus/w1/devices/w1_bus_master1/{address}/w1_slave", "r"
    ) as content_file:
        content = content_file.read()
        if content.split("\n")[0].split(" ")[11] == "YES":
            return float(content.split("=")[-1]) / 1000
        else:
            return None


# Property descriptions
bias_description = "Sensor bias may be positive or negative."
linear_coef_description = "Linear calibration coeficient"
quadratic_coef_description = "Quadratic calibration coeficient"
alpha_description = "The parameter α determines the relative weighting of temperature readings in an exponential moving average. α must be >0 and <=1. At α=1, all weight is placed on the current reading. T_i = α*t_i + (1-α)*T_i-1)"
precision_description_C = "DS18B20 sensors can be set to provide 9 bit (0.5°C, 93.75ms conversion), 10 bit (0.25°C, 187.5ms conversion), 11 bit (0.125°C, 375 ms conversion), or 12 bit precision (0.0625°C, 750ms conversion)."
precision_description_F = "DS18B20 sensors can be set to provide 9 bit (0.9°F, 93.75ms conversion), 10 bit (0.45°F, 187.5ms conversion), 11 bit (0.225°F, 375 ms conversion), or 12 bit precision (0.1125°F, 750ms conversion)."
update_description = "The update interval is the target time between polling the temperature sensor in milliseconds. While there is sensor temperature conversion time based on precision (see precision description), there is also computational overhead associated with communicating with the sensor, checking for errors, and moving average calculation. An update interval < 2000ms is not recommended. <2000ms may lend to excess warning messages. This update interval may need to be higher on systems with many sensors. Software improvements may eventually lower this recommendation."
low_filter_description = "Values below the low value filter threshold will be ignored. Units automatically selected."
high_filter_description = "Values above the high value filter threshold will be ignored. Units automatically selected."
timeout_description = "0ms will disable these notifications completely"


@cbpi.sensor
class OneWireTweaks(SensorActive):
    a_address = Property.Select("Address", get_sensors())
    b_bias = Property.Number(
        ifelse_celcius("Bias (°C)", "Bias (°F)"),
        True,
        0.0,
        description=bias_description,
    )
    b_linear_coef = Property.Number(
        "Linear calibration coeficient", True, 1.0, description=linear_coef_description
    )
    b_quadratic_coef = Property.Number(
        "Quadratic calibration coeficient",
        True,
        0.0,
        description=quadratic_coef_description,
    )
    c_alpha = Property.Number(
        "Exponential moving average parameter (α)",
        True,
        1.0,
        description=alpha_description,
    )
    d_precision = Property.Select(
        "Precision (bits)",
        [9, 10, 11, 12],
        description=ifelse_celcius(precision_description_C, precision_description_F),
    )
    e_update_interval = Property.Number(
        "Update interval (ms)", True, 5000, description=update_description
    )
    f_low_filter = Property.Number(
        ifelse_celcius(
            "Low value filter threshold (°C)", "Low value filter threshold (°F)"
        ),
        True,
        ifelse_celcius(0, 32),
        description=low_filter_description,
    )
    f_high_filter = Property.Number(
        ifelse_celcius(
            "High value filter threshold (°C)", "High value filter threshold (°F)"
        ),
        True,
        ifelse_celcius(100, 212),
        description=high_filter_description,
    )
    g_timeout1 = Property.Number(
        "Filtered value notification duration (ms)",
        True,
        5000,
        description=timeout_description,
    )
    g_timeout2 = Property.Number(
        "Update error notification duration (ms)",
        True,
        5000,
        description=timeout_description,
    )
    __running = False

    def get_unit(self):
        return ifelse_celcius("°C", "°F")

    def stop(self):
        SensorActive.stop(self)

    def init(self):
        SensorActive.stop(self)
        SensorActive.init(self)

    def execute(self):
        # Convert all properties
        address = self.a_address
        bias = float(self.b_bias)
        linear_coef = float(self.b_linear_coef)
        quadratic_coef = float(self.b_quadratic_coef)
        alpha = float(self.c_alpha)
        precision = int(self.d_precision)
        update_interval = float(self.e_update_interval) / 1000.0
        low_filter = float(self.f_low_filter)
        high_filter = float(self.f_high_filter)
        timeout1 = float(self.g_timeout1)
        if timeout1 <= 0.0:
            notify1 = False
        else:
            notify1 = True

        timeout2 = float(self.g_timeout2)
        if timeout2 <= 0.0:
            notify2 = False
        else:
            notify2 = True

        # Error checking
        if not 0.0 < alpha <= 1.0:
            cbpi.notify(
                "OneWire Error", "α must be >0 and <= 1", timeout=None, type="danger"
            )
            raise ValueError("OneWire - α must be >0 and <= 1")
        elif update_interval < 1.0:
            cbpi.notify(
                "OneWire Error",
                "Update interval must be >= 1000ms",
                timeout=None,
                type="danger",
            )
            raise ValueError("OneWire - Update interval must be >= 1000ms")
        elif low_filter >= high_filter:
            cbpi.notify(
                "OneWire Error",
                "Low filter must be < high filter",
                timeout=None,
                type="danger",
            )
            raise ValueError("OneWire - Low filter must be < high filter")
        else:
            # Set precision in volatile SRAM
            try:
                set_precision(precision, address)
            except:
                cbpi.notify(
                    "OneWire Warning",
                    f"Could not change precision of {address}, may have insufficient permissions",
                    timeout=None,
                    type="warning",
                )
                cbpi.app.logger.info(
                    f"[{time.time()}] Could not change precision of {address}, may have insufficient permissions"
                )

            # Wait after attempting precision change before attempting to read temperature
            self.sleep(2.0)

            # Initialize previous value for exponential moving average
            last_temp = None

            # Initialize warning log count
            warn_count = 0

            # Running loop
            while self.is_running():
                if warn_count > 51:
                    # Notify after 50 warnings
                    cbpi.notify(
                        "OneWire Warning",
                        f"There have been >50 warnings logged associated with sensor {address}. It is suggested you recheck your hardware and/or adjust plugin settings",
                        type="warning",
                    )
                    # Reset the counter
                    warn_count = 0

                waketime = time.time() + update_interval
                current_temp = get_temp(address)
                current_temp_f = (current_temp * 9.0 / 5.0) + 32.0
                if current_temp != None:
                    # A temperature of 85 is a communication error code
                    if current_temp == 85.0:
                        # Count it
                        warn_count += 1
                        cbpi.notify(
                            "OneWire Warning",
                            f"Communication error with {address} detected",
                            type="warning",
                        )
                        cbpi.app.logger.info(
                            f"[{waketime}] Communication error with {address} detected"
                        )
                    # Proceed with valid temperature readings
                    else:
                        # Convert current temp and add bias if necessary
                        if self.get_config_parameter("unit", "C") == "C":
                            current_temp = (
                                quadratic_coef * current_temp ** 2
                                + linear_coef * current_temp
                                + bias
                            )
                        else:
                            current_temp = (
                                quadratic_coef * current_temp_f ** 2
                                + linear_coef * current_temp_f
                                + bias
                            )

                        # If inside filter limits...
                        if low_filter < current_temp < high_filter:
                            if last_temp != None:
                                exp_temp = current_temp * alpha + last_temp * (
                                    1.0 - alpha
                                )
                                self.data_received(round(exp_temp, 1))
                                last_temp = exp_temp
                            else:
                                self.data_received(round(current_temp, 1))
                                last_temp = current_temp

                        # Outside filter limits...
                        else:
                            # Count it
                            warn_count += 1
                            # Add to logger
                            cbpi.app.logger.info(
                                f"[{waketime}] {address} reading of {round(current_temp, 1)} filtered"
                            )

                            # Produce a notification if requested
                            if notify1:
                                cbpi.notify(
                                    "OneWire Warning",
                                    f"{address} reading of {round(current_temp, 1)} filtered",
                                    timeout=timeout1,
                                    type="warning",
                                )

                # Sleep until update required again
                if waketime <= time.time():
                    # Count it
                    warn_count += 1
                    # Add to logger
                    cbpi.app.logger.info(
                        f"[{waketime}] reading of {address} could not complete within update interval"
                    )
                    # Produce a notification if requested
                    if notify2:
                        cbpi.notify(
                            "OneWire Warning",
                            f"Reading of {address} could not complete within update interval",
                            timeout=timeout2,
                            type="warning",
                        )
                # Zzzz
                else:
                    self.sleep(waketime - time.time())

    @classmethod
    def init_global(self):
        try:
            call(["modprobe", "w1-gpio"])
            call(["modprobe", "w1-therm"])
        except:
            pass
