# Support fans that are enabled when temperature exceeds a set threshold
#
# Copyright (C) 2016-2020  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import statistics

from . import fan

KELVIN_TO_CELSIUS = -273.15
MAX_FAN_TIME = 5.0
AMBIENT_TEMP = 25.0
PID_PARAM_BASE = 255.0


class TemperatureFan:
    def __init__(self, config):
        self.name = config.get_name().split()[1]
        self.printer = config.get_printer()
        self.fan = fan.Fan(config, default_shutdown_speed=1.0)
        self.min_temp = config.getfloat("min_temp", minval=KELVIN_TO_CELSIUS)
        self.max_temp = config.getfloat("max_temp", above=self.min_temp)
        pheaters = self.printer.load_object(config, "heaters")
        self.sensor = pheaters.setup_sensor(config)
        self.sensor.setup_minmax(self.min_temp, self.max_temp)
        self.sensor.setup_callback(self.temperature_callback)
        pheaters.register_sensor(config, self)
        self.speed_delay = self.sensor.get_report_time_delta()
        self.max_speed_conf = config.getfloat(
            "max_speed", 1.0, above=0.0, maxval=1.0
        )
        self.max_speed = self.max_speed_conf
        self.min_speed_conf = config.getfloat(
            "min_speed", 0.3, minval=0.0, maxval=1.0
        )
        self.min_speed = self.min_speed_conf
        self.last_temp = 0.0
        self.last_temp_time = 0.0
        self.target_temp_conf = config.getfloat(
            "target_temp",
            40.0 if self.max_temp > 40.0 else self.max_temp,
            minval=self.min_temp,
            maxval=self.max_temp,
        )
        self.target_temp = self.target_temp_conf
        algos = {
            "watermark": ControlBangBang,
            "pid": ControlPID,
            "curve": ControlCurve,
        }
        algo = config.getchoice("control", algos)
        self.control = algo(self, config)
        self.next_speed_time = 0.0
        self.last_speed_value = 0.0
        gcode = self.printer.lookup_object("gcode")
        gcode.register_mux_command(
            "SET_TEMPERATURE_FAN_TARGET",
            "TEMPERATURE_FAN",
            self.name,
            self.cmd_SET_TEMPERATURE_FAN_TARGET,
            desc=self.cmd_SET_TEMPERATURE_FAN_TARGET_help,
        )

    def set_speed(self, read_time, value):
        if value <= 0.0:
            value = 0.0
        elif value < self.min_speed:
            value = self.min_speed
        if self.target_temp <= 0.0:
            value = 0.0
        if (
            read_time < self.next_speed_time or not self.last_speed_value
        ) and abs(value - self.last_speed_value) < 0.05:
            # No significant change in value - can suppress update
            return
        speed_time = read_time + self.speed_delay
        self.next_speed_time = speed_time + 0.75 * MAX_FAN_TIME
        self.last_speed_value = value
        self.fan.set_speed(speed_time, value)

    def temperature_callback(self, read_time, temp):
        self.last_temp = temp
        self.control.temperature_callback(read_time, temp)

    def get_temp(self, eventtime):
        return self.last_temp, self.target_temp

    def get_min_speed(self):
        return self.min_speed

    def get_max_speed(self):
        return self.max_speed

    def get_status(self, eventtime):
        status = self.fan.get_status(eventtime)
        status["temperature"] = round(self.last_temp, 2)
        status["target"] = self.target_temp
        status["control"] = self.control.get_type()
        return status

    def is_adc_faulty(self):
        if self.last_temp > self.max_temp or self.last_temp < self.min_temp:
            return True
        return False

    cmd_SET_TEMPERATURE_FAN_TARGET_help = (
        "Sets a temperature fan target and fan speed limits"
    )

    def cmd_SET_TEMPERATURE_FAN_TARGET(self, gcmd):
        temp = gcmd.get_float("TARGET", None)
        if temp is not None and self.control.get_type() == "curve":
            raise gcmd.error("Setting Target not supported for control curve")
        min_speed = gcmd.get_float("MIN_SPEED", self.min_speed)
        max_speed = gcmd.get_float("MAX_SPEED", self.max_speed)
        if min_speed > max_speed:
            raise self.printer.command_error(
                "Requested min speed (%.1f) is greater than max speed (%.1f)"
                % (min_speed, max_speed)
            )
        self.set_min_speed(min_speed)
        self.set_max_speed(max_speed)
        self.set_temp(self.target_temp_conf if temp is None else temp)

    def set_temp(self, degrees):
        if degrees and (degrees < self.min_temp or degrees > self.max_temp):
            raise self.printer.command_error(
                "Requested temperature (%.1f) out of range (%.1f:%.1f)"
                % (degrees, self.min_temp, self.max_temp)
            )
        self.target_temp = degrees

    def set_min_speed(self, speed):
        if speed and (speed < 0.0 or speed > 1.0):
            raise self.printer.command_error(
                "Requested min speed (%.1f) out of range (0.0 : 1.0)" % (speed)
            )
        self.min_speed = speed

    def set_max_speed(self, speed):
        if speed and (speed < 0.0 or speed > 1.0):
            raise self.printer.command_error(
                "Requested max speed (%.1f) out of range (0.0 : 1.0)" % (speed)
            )
        self.max_speed = speed


######################################################################
# Bang-bang control algo
######################################################################


class ControlBangBang:
    def __init__(self, temperature_fan, config):
        self.temperature_fan = temperature_fan
        self.reverse = config.getboolean("reverse", False)
        self.max_delta = config.getfloat("max_delta", 2.0, above=0.0)
        self.heating = False

    def temperature_callback(self, read_time, temp):
        current_temp, target_temp = self.temperature_fan.get_temp(read_time)
        if (
            self.heating != self.reverse
            and temp >= target_temp + self.max_delta
        ):
            self.heating = self.reverse
        elif (
            self.heating == self.reverse
            and temp <= target_temp - self.max_delta
        ):
            self.heating = not self.reverse
        if self.heating:
            self.temperature_fan.set_speed(read_time, 0.0)
        else:
            self.temperature_fan.set_speed(
                read_time, self.temperature_fan.get_max_speed()
            )

    def get_type(self):
        return "watermark"


######################################################################
# Proportional Integral Derivative (PID) control algo
######################################################################

PID_SETTLE_DELTA = 1.0
PID_SETTLE_SLOPE = 0.1


class ControlPID:
    def __init__(self, temperature_fan, config):
        self.temperature_fan = temperature_fan
        self.reverse = config.getboolean("reverse", False)
        self.Kp = config.getfloat("pid_Kp") / PID_PARAM_BASE
        self.Ki = config.getfloat("pid_Ki") / PID_PARAM_BASE
        self.Kd = config.getfloat("pid_Kd") / PID_PARAM_BASE
        self.min_deriv_time = config.getfloat("pid_deriv_time", 2.0, above=0.0)
        imax = config.getfloat(
            "pid_integral_max", self.temperature_fan.get_max_speed(), minval=0.0
        )
        self.temp_integ_max = imax / self.Ki
        self.prev_temp = AMBIENT_TEMP
        self.prev_temp_time = 0.0
        self.prev_temp_deriv = 0.0
        self.prev_temp_integ = 0.0

    def temperature_callback(self, read_time, temp):
        current_temp, target_temp = self.temperature_fan.get_temp(read_time)
        time_diff = read_time - self.prev_temp_time
        # Calculate change of temperature
        temp_diff = temp - self.prev_temp
        if time_diff >= self.min_deriv_time:
            temp_deriv = temp_diff / time_diff
        else:
            temp_deriv = (
                self.prev_temp_deriv * (self.min_deriv_time - time_diff)
                + temp_diff
            ) / self.min_deriv_time
        # Calculate accumulated temperature "error"
        temp_err = target_temp - temp
        temp_integ = self.prev_temp_integ + temp_err * time_diff
        temp_integ = max(0.0, min(self.temp_integ_max, temp_integ))
        # Calculate output
        co = self.Kp * temp_err + self.Ki * temp_integ - self.Kd * temp_deriv
        bounded_co = max(0.0, min(self.temperature_fan.get_max_speed(), co))
        if not self.reverse:
            self.temperature_fan.set_speed(
                read_time,
                max(
                    self.temperature_fan.get_min_speed(),
                    self.temperature_fan.get_max_speed() - bounded_co,
                ),
            )
        else:
            self.temperature_fan.set_speed(
                read_time, max(self.temperature_fan.get_min_speed(), bounded_co)
            )
        # Store state for next measurement
        self.prev_temp = temp
        self.prev_temp_time = read_time
        self.prev_temp_deriv = temp_deriv
        if co == bounded_co:
            self.prev_temp_integ = temp_integ

    def get_type(self):
        return "pid"


class ControlCurve:
    def __init__(self, temperature_fan, config, controlled_fan=None):
        self.temperature_fan = temperature_fan
        self.controlled_fan = (
            temperature_fan if controlled_fan is None else controlled_fan
        )
        self.curve_table = []
        points = config.getlists(
            "points", seps=(",", "\n"), parser=float, count=2
        )
        for temp, pwm in points:
            current_point = [temp, pwm]
            if current_point is None:
                continue
            if len(current_point) != 2:
                raise temperature_fan.printer.config_error(
                    "Point needs to have exactly one temperature and one speed "
                    "value."
                )
            if temp > temperature_fan.target_temp:
                raise temperature_fan.printer.config_error(
                    "Temperature in point can not exceed max_temp."
                )
            if temp < temperature_fan.min_temp:
                raise temperature_fan.printer.config_error(
                    "Temperature in point can not fall below min_temp."
                )
            if pwm > temperature_fan.get_max_speed():
                raise temperature_fan.printer.config_error(
                    "Speed in point can not exceed max_speed."
                )
            if pwm < temperature_fan.get_min_speed():
                raise temperature_fan.printer.config_error(
                    "Speed in point can not fall below min_speed."
                )
            for _temp, _pwm in self.curve_table:
                if _temp == temp:
                    raise temperature_fan.printer.config_error(
                        "Temperature can not exist twice in curve table."
                    )
            self.curve_table.append(current_point)
        if len(self.curve_table) < 2:
            raise temperature_fan.printer.config_error(
                "At least two points need to be defined for curve in "
                "temperature_fan."
            )
        self.curve_table.sort(key=lambda p: p[0])
        self.cooling_hysteresis = config.getfloat("cooling_hysteresis", 0.0)
        self.heating_hysteresis = config.getfloat("heating_hysteresis", 0.0)
        self.smooth_readings = config.getint("smooth_readings", 10, minval=1)
        self.stored_temps = []
        for i in range(self.smooth_readings):
            self.stored_temps.append(0.0)
        self.last_temp = 0.0

    def temperature_callback(self, read_time, temp):
        def _interpolate(below, above, temp):
            return (
                (below[1] * (above[0] - temp)) + (above[1] * (temp - below[0]))
            ) / (above[0] - below[0])

        temp = self.smooth_temps(temp)
        if temp <= self.curve_table[0][0]:
            self.controlled_fan.set_speed(read_time, self.curve_table[0][1])
            return
        if temp >= self.curve_table[-1][0]:
            self.controlled_fan.set_speed(read_time, self.curve_table[-1][1])
            return

        below = [
            self.curve_table[0][0],
            self.curve_table[0][1],
        ]
        above = [
            self.curve_table[-1][0],
            self.curve_table[-1][1],
        ]
        for config_temp in self.curve_table:
            if config_temp[0] < temp:
                below = config_temp
            else:
                above = config_temp
                break
        self.controlled_fan.set_speed(
            read_time, _interpolate(below, above, temp)
        )

    def smooth_temps(self, current_temp):
        if (
            self.last_temp - self.cooling_hysteresis
            <= current_temp
            <= self.last_temp + self.heating_hysteresis
        ):
            temp = self.last_temp
        else:
            temp = current_temp
        self.last_temp = temp
        for i in range(1, len(self.stored_temps)):
            self.stored_temps[i] = self.stored_temps[i - 1]
        self.stored_temps[0] = temp
        return statistics.median(self.stored_temps)

    def get_type(self):
        return "curve"


def load_config_prefix(config):
    return TemperatureFan(config)
