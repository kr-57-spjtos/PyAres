# -*- coding: utf-8 -*-
# Fake version of ENDER_PRINTER.py, so that I can test it when I don't have printer access
import time
import re
from PyAres import AresDeviceService, AresDataType, DeviceSchemaEntry, DeviceCommandDescriptor

class FakePrinter:
    def __init__(self, port="/dev/tty.usbserial-11220", baudrate=250000): # Port switched to work on Mac, may fail on Windows.
        self.port = port
        self.baudrate = baudrate
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.target_bed_temp = 0.0
        self.print_speed = 100.0
        self.temp = 25.0

    def send_gcode(self, command: str):
        print(command.strip() + "\n")
        return (command.strip() + "\n")

    # Getter functions for parameter space
    def get_bed_temperature(self):
        return self.temp

    def get_print_speed(self):
        """Returns the print speed."""
        print("[Hardware] Retrieving the current print speed...")
        return { "current_speed": self.print_speed }

    def get_z_height(self):
        """Returns the Z height."""
        print("[Hardware] Retrieving the current Z height...")
        return { "current_z_height": self.current_z }

    '''
    def get_pressure(self):
        """Simulates reading the pressure."""
        print("[Hardware] Retrieving the current pressure...")
        return { "current_pressure": self.pressure }
    '''

    def move_to(self, x=0.0, y=0.0, z=0.0):
        # Signature MUST match keys in move_schema exactly
        cmd = f"G0 X{x} Y{y} Z{z} F2000"
        self.send_gcode(cmd)
        self.current_x, self.current_y, self.current_z = x, y, z
        return {"status": "moved"}

    def print(self, x=0.0, y=0.0):
        # Signature MUST match keys in print_schema exactly
        cmd = f"G1 X{x} Y{y} F{self.print_speed}"
        self.send_gcode(cmd)
        self.current_x, self.current_y = x, y
        return {"status": "moved"}

    # Setter functions for parameter space
    def set_bed_temp(self, target_temp=0.0, wait=False):
        # Signature MUST match keys in temp_schema exactly
        self.target_bed_temp = target_temp
        cmd = "M190" if wait else "M140"
        self.send_gcode(f"{cmd} S{target_temp}")
        return {"status": "set"}

    def set_print_speed(self, speed: float):
        """Simulates setting the print speed."""
        print(f"[Hardware] Setting print speed to {speed} mm/min...")
        self.print_speed = speed
        return {} # Return empty dict if no data needs to be sent back

    def set_z_height(self, z_height: float):
        """Simulates setting the Z height."""
        print(f"[Hardware] Setting Z height to {z_height} mm...")
        self.move_to(self.current_x, self.current_y, z_height)
        return {} # Return empty dict if no data needs to be sent back

    '''
    def set_pressure(self, pressure: float):
        """Simulates setting the pressure."""
        print(f"[Hardware] Setting pressure to {pressure} kPa...")
        self.pressure = pressure
        return {} # Return empty dict if no data needs to be sent back
    '''

    def home_axes(self):
        print("[Hardware] Homing...")
        self.send_gcode("G28")
        self.current_x = self.current_y = self.current_z = 0.0
        return {"result": "Home Success"}

    # Probe bed for bed leveling. Intended for use with bilinear ABL, probing grid 2x2 points.
    def probe_bed(self, x_min: float, x_max: float, y_min: float, y_max: float):
        print(f"[Hardware] Probing bed from X {x_min} to X {x_max}, and from Y {y_min} to Y {y_max}.")
        self.send_gcode(f"G29 F{y_min} B{y_max} L{x_min} R{x_max}")
        return {"result": "Probe Success"}

    def get_state(self):
        actual_bed = self.get_bed_temperature()
        return {
            "x": self.current_x, "y": self.current_y, "z": self.current_z,
            "bed_temp_actual": actual_bed,
            "bed_temp_target": self.target_bed_temp
        }

    def safe_mode(self):
        self.send_gcode("M140 S0")
        self.send_gcode("G91")
        self.send_gcode("G1 Z15 F1000")
        self.send_gcode("G90")

if __name__ == "__main__":
        printer = FakePrinter()
        print("Connected to printer successfully.")
        service = AresDeviceService(
            printer.safe_mode, printer.get_state,
            "Fake Ender Printer", "(Fake) Motion and Bed Control",
            "1.0.0", port=7100
        )

        # 1. Move To and Print (Now with exact signature matching)
        service.add_new_command(
            DeviceCommandDescriptor("Move To", "XYZ Motion without extrusion",
                {"x": DeviceSchemaEntry(AresDataType.NUMBER, "X", "mm"),
                 "y": DeviceSchemaEntry(AresDataType.NUMBER, "Y", "mm"),
                 "z": DeviceSchemaEntry(AresDataType.NUMBER, "Z", "mm")}, {}),
            printer.move_to
        )

        service.add_new_command(
            DeviceCommandDescriptor("Print", "XY Motion with extrusion",
                                    {"x": DeviceSchemaEntry(AresDataType.NUMBER, "X", "mm"),
                                     "y": DeviceSchemaEntry(AresDataType.NUMBER, "Y", "mm")}, {}),
            printer.print
        )

        # 2. Set Params (Using target_temp to match hardware method)
        service.add_new_command(
            DeviceCommandDescriptor("Set Bed Temp", "Bed control",
                {"target_temp": DeviceSchemaEntry(AresDataType.NUMBER, "Temp", "C"),
                 "wait": DeviceSchemaEntry(AresDataType.BOOLEAN, "Wait?", "")}, {}),
            printer.set_bed_temp
        )

        service.add_new_command(
            DeviceCommandDescriptor("Set Print Speed", "Speed of printer when printing",
                                    {"speed": DeviceSchemaEntry(AresDataType.NUMBER, "Speed", "mm/min")}, {}),
            printer.set_print_speed
        )

        service.add_new_command(
            DeviceCommandDescriptor("Set Z Height", "Height of printer above the bed",
                                    {"z_height": DeviceSchemaEntry(AresDataType.NUMBER, "Length", "mm")}, {}),
            printer.set_z_height
        )

        # 3. Home Axes (Added an output schema to force the button to render)
        service.add_new_command(
            DeviceCommandDescriptor("Home Axes", "G28 Homing", {}, 
                {"result": DeviceSchemaEntry(AresDataType.STRING, "Result", "")}),
            printer.home_axes
        )

        # 4. Probe bed (Added an output schema to force the button to render)
        service.add_new_command(
            DeviceCommandDescriptor("Probe Bed", "G28 Homing", {"x_min": DeviceSchemaEntry(AresDataType.NUMBER, "X minimum to probe", "mm"),
                                                                "x_max": DeviceSchemaEntry(AresDataType.NUMBER, "X maximum to probe", "mm"),
                                                                 "y_min": DeviceSchemaEntry(AresDataType.NUMBER, "Y minimum to probe", "mm"),
                                                                "y_max": DeviceSchemaEntry(AresDataType.NUMBER, "Y maximum to probe", "mm")},
                                    {"result": DeviceSchemaEntry(AresDataType.STRING, "Result", "")}),
            printer.probe_bed
        )

        # 5. Read Parameters (Lambda last)
        service.add_new_command(
            DeviceCommandDescriptor("Get Bed Temp", "Thermistor Read", {}, 
                {"bed_actual": DeviceSchemaEntry(AresDataType.NUMBER, "Temp", "C")}),
            lambda: {"bed_actual": printer.get_bed_temperature()}
        )

        service.add_new_command(
            DeviceCommandDescriptor("Get Print Speed", "Internal recall", {},
                                    {"speed_current": DeviceSchemaEntry(AresDataType.NUMBER, "Speed", "mm/min")}),
            lambda: {"speed_current": printer.get_print_speed()}
        )

        service.add_new_command(
            DeviceCommandDescriptor("Get Z Height", "Internal recall", {},
                                    {"z_current": DeviceSchemaEntry(AresDataType.NUMBER, "Z Height", "mm")}),
            lambda: {"z_current": printer.get_z_height()}
        )

        print("Service Active on Port 7100.")
        service.start()
