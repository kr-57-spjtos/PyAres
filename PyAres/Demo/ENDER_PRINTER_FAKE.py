# -*- coding: utf-8 -*-
# Fake version of ENDER_PRINTER.py, so that I can test it when I don't have printer access
import time
import random
from PyAres import AresDeviceService, AresDataType, DeviceSchemaEntry, DeviceCommandDescriptor
import numpy as np

def sign(number: float) -> int:
    if number == 0:
        return 0
    if number > 0:
        return 1
    return -1

class FakePrinter:
    def __init__(self, port="/dev/tty.usbserial-11220", baudrate=250000): # Port switched to work on Mac, may fail on Windows.
        self.port = port
        self.baudrate = baudrate
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.target_bed_temp = 25.0
        self.print_speed = 100.0
        self.temp = 25.0
        self.print_z_height = 5.0
        self.rt = False # Set to true to simulate time taken for command completion

    def send_gcode(self, command: str):
        print(command.strip() + "\n")
        time.sleep(0.5*self.rt) # Build in time for processing and communication
        if command == "M105":
            return f"T:{round(self.temp -3.4, 2)} /0.00 B:{round(self.temp, 2)} /0.00 @:0 B@:0"
        else:
            return (command.strip() + "\n")

    # Getter functions for parameter space
    def get_bed_temperature(self):
        raw = self.send_gcode("M105")
        # bed_match = re.search(r"B:([\d.]+)", raw)
        # Made a function to get temperature.
        if raw.find("B:") > 0:
            bed_match = (raw[raw.find("B:") + 2:]).split(" ")[0]
            print(f"Get bed temp got printer response {raw}")
            print(f"Temp is {bed_match} C")
            return float(bed_match)
        else:
            return 0.0

    def get_print_speed(self):
        """Returns the print speed."""
        return self.print_speed

    def get_z_height(self):
        """Returns the Z height."""
        return self.current_z

    '''
    def get_pressure(self):
        """Simulates reading the pressure."""
        print("[Hardware] Retrieving the current pressure...")
        return { "current_pressure": self.pressure }
    '''

    def move_to(self, x: float, y: float, z: float):
        # Signature MUST match keys in move_schema exactly
        cmd = f"G0 X{x} Y{y} Z{z} F1000"
        self.send_gcode(cmd)
        distance = np.linalg.norm(np.array((self.current_x - x, self.current_y - y, self.current_z - z)))
        time.sleep((round(distance * 3/50 ) + 3) * self.rt) # Wait for printer to finish moving
        self.current_x, self.current_y, self.current_z = x, y, z
        print(self.send_gcode("M114"))
        print(f"X:{self.current_x} Y:{self.current_y} Z:{self.current_z}")
        return {"status": "moved"}

    def print(self, length: float):
        # Signature MUST match keys in print_schema exactly
        # Set z height beforehand.
        z_cmd = f"G0 Z{self.print_z_height} F1000"
        self.send_gcode(z_cmd)
        cmd = f"G1 X{self.current_x + length} Y{self.current_y} F{self.print_speed}"
        self.send_gcode(cmd)
        self.current_x += length
        return {"status": "printed"}

    def set_bed_temp(self, target_temp=0.0, wait=False):
        # Signature MUST match keys in temp_schema exactly
        cmd = "M190" if wait else "M140"
        self.send_gcode(f"{cmd} S{target_temp}")
        if wait==True:
            print("Waiting for printer bed to heat/cool")
            heat_or_cool = sign(target_temp - self.temp)
            while not (target_temp - 0.5 < float(self.temp) < target_temp + 0.5):
                time.sleep(1)
                self.temp += heat_or_cool * 0.35 #Gradually move towards target temperature
        else:
            self.temp = self.target_bed_temp = target_temp
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

    def wait_for_printer(self, number: float):
        print(number)
        # This is a half-point method meant to make the printer wait for all commands to be finished. I'm not sure
        # if it will work but I will try.
        # M400 is meant to make the printer wait and finish moves.
        self.send_gcode("M400")
        time.sleep(random.randint(3,6))
        print("Printer caught up with commands.")
        return {"output": "Waited for printer"}

    def home_axes(self):
        print("[Hardware] Homing...")
        self.send_gcode("G28")
        self.current_x = self.current_y = 150.0
        self.current_z = 10.0
        return {"result": "Home Success"}

    # Probe bed for bed leveling. Intended for use with bilinear ABL, probing grid 2x2 points.
    def probe_bed(self,  y_size, x_size, y_min=0.0, x_min=0.0):
        print(f"[Hardware] Probing bed from X {x_min} to X {x_min + x_size}, and from Y {y_min} to Y {y_min + y_size}.")
        self.send_gcode(f"G29 F{y_min} B{y_min + y_size} L{x_min} R{x_min + x_size}")
        return {"result": "Probe Success"}
    
    """
    def probe_bed(self,  y_size, x_size, y_min=0.0, x_min=0.0, use_current_position=True):
        if use_current_position:
            print(f"[Hardware] Probing bed from X {self.current_x} to X {self.current_x + x_size}, and from Y {self.current_y} to Y {self.current_y + y_size}.")
            self.send_gcode(f"G29 F{self.current_y} B{self.current_y + y_size} L{self.current_x} R{self.current_x + x_size}")
        else: 
            print(f"[Hardware] Probing bed from X {x_min} to X {x_min + x_size}, and from Y {y_min} to Y {y_min + y_size}.")
            self.send_gcode(f"G29 F{y_min} B{y_min + y_size} L{x_min} R{x_min + x_size}")
        return {"result": "Probe Success"}
    """

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
            DeviceCommandDescriptor("Print", "Length to extrude",
                                    {"length": DeviceSchemaEntry(AresDataType.NUMBER, "X", "mm")}, {}),
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
            DeviceCommandDescriptor("Probe Bed", "G28 Homing", {"y_size": DeviceSchemaEntry(AresDataType.NUMBER, "Y length of probing grid", "mm"),
                                                                "x_size": DeviceSchemaEntry(AresDataType.NUMBER, "X length of probing grid", "mm"),
                                                                 "y_min": DeviceSchemaEntry(AresDataType.NUMBER, "Y minimum to probe", "mm"),
                                                                 "x_min": DeviceSchemaEntry(AresDataType.NUMBER, "X minimum to probe", "mm")},
                                    {"result": DeviceSchemaEntry(AresDataType.STRING, "Result", "")}),
            printer.probe_bed
        )
        #,"use_current_position": DeviceSchemaEntry(AresDataType.BOOLEAN, "Use current position as min x and y of probing grid. Overrides min x and min y", "")

        # 5. Wait for printer (Added an output schema to force the button to render)
        service.add_new_command(
            DeviceCommandDescriptor("Wait for Printer", "G400",
                                    {"number": DeviceSchemaEntry(AresDataType.NUMBER, "random number", "mm")},{}),
            printer.wait_for_printer
        )

        # 6. Read Parameters (Lambda last)
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