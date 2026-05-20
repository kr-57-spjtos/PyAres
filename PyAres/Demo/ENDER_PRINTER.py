# -*- coding: utf-8 -*-
import serial
import time
import re
from PyAres import AresDeviceService, AresDataType, DeviceSchemaEntry, DeviceCommandDescriptor
import numpy as np

class CustomPrinterHardware:
    def __init__(self, port="/dev/tty.usbserial-1110", baudrate=250000): # Port switched to work on Mac, may fail on Windows.
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.target_bed_temp = 0.0
        self.print_speed = 100.0
        self.print_z_height = 5.0

    def connect(self):
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
            print("Connecting to printer motion system...")
            time.sleep(5) 
            self.ser.reset_input_buffer()
            self.send_gcode("G90") 
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
        
    def check_end(self, cmd: str, line: str) -> bool:
        # It should be possible to add more ending checks based on command here
        if cmd == "G28":
            while True:
                if line.find("X:") != -1:
                    break
        else: 
            while True:
                if "ok" in line.lower():
                    break
        return True

    def send_gcode(self, command):
        if not self.ser: return ""
        self.ser.write((command.strip() + "\n").encode('utf-8'))
        response = ""
        while True:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            print(line) # Set errors to ignore to copy format of probe_and_print because it worked there
            response += line + "\n"
            if self.check_end(command,line):
                break
        return response

    # Getter functions for parameter space
    def get_bed_temperature(self):
        raw = self.send_gcode("M105")
        #bed_match = re.search(r"B:([\d.]+)", raw)
        # Made a function to get temperature.
        print(raw)
        if raw.find("B:") > 0:
            bed_match = (raw[raw.find("B:") + 2:]).split(" ")[0]
            #print(f"Get bed temp got printer response {raw}")
            print(f"Temp is {bed_match} C")
            return float(bed_match) 
        else:
            return 0.0

    def get_print_speed(self):
        """Returns the print speed."""
        print("[Hardware] Retrieving the current print speed...")
        return self.print_speed

    def get_z_height(self):

        """Returns the Z height."""
        print("[Hardware] Retrieving the current Z height...")
        #raw = self.send_gcode("M114")
        #loc_match = re.search(r"B:([\d.]+)", raw)
        # Find the right line, and then look for the z coordinate. Split that part off and strip it 
        #z_coord = (str(loc_match.group(1)).split('Z ')[1]).split(" ")[0].strip()
        #return float(z_coord) if z_coord else 0.0
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
        time.sleep(round(distance * 3/50 ) + 3) # Wait for printer to finish moving
        self.current_x, self.current_y, self.current_z = x, y, z
        print(self.send_gcode("M114")) # Check where the printer is after moving. 
        time.sleep(1) # Wait for command to complete
        return {"status": "moved"}

    def print(self, length):
        # Signature MUST match keys in print_schema exactly
        # Set z height beforehand.
        z_cmd = f"G1 Z{self.print_z_height} F1000"
        self.send_gcode(z_cmd)
        cmd = f"G1 X{self.current_x + length} F{self.print_speed}"
        self.send_gcode(cmd)
        time.sleep(3 + length/self.print_speed) # Wait for printer to catch up. 
        self.current_x += length
        return {"status": "printed"}

    # Setter functions for parameter space
    def set_bed_temp(self, target_temp=0.0, wait=False):
        # Signature MUST match keys in temp_schema exactly
        print(f"[Hardware] Setting bed temp to {target_temp} mm...")
        self.target_bed_temp = target_temp
        cmd = "M190" if wait else "M140"
        self.send_gcode(f"{cmd} S{target_temp}")
        # Experimental code to force waiting for bed to heat. 
        if wait==True:
            while not (target_temp - 0.5 < float(self.get_bed_temperature()) < target_temp + 0.5):
                time.sleep(1)
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
        self.print_z_height = z_height
        return {} # Return empty dict if no data needs to be sent back

    '''
    def set_pressure(self, pressure: float):
        """Simulates setting the pressure."""
        print(f"[Hardware] Setting pressure to {pressure} kPa...")
        self.pressure = pressure
        return {} # Return empty dict if no data needs to be sent back
    '''

    def wait_for_printer(self):
        # This is a half-point method meant to make the printer wait for all commands to be finished. I'm not sure
        # if it will work but I will try.
        # M400 is meant to make the printer wait and finish moves.
        self.send_gcode("M400")
        return {"result": "Waited for printer"}

    def home_axes(self):
        print("[Hardware] Homing...")
        self.send_gcode("G28")
        self.current_x = self.current_y = self.current_z = 0.0
        time.sleep(40) 
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
    printer = CustomPrinterHardware()
    if printer.connect():
        print("Connected to printer successfully.")
        service = AresDeviceService(
            printer.safe_mode, printer.get_state,
            "Custom Head Printer", "Motion and Bed Control",
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
            DeviceCommandDescriptor("Probe Bed", "G28 Homing", {"x_min": DeviceSchemaEntry(AresDataType.NUMBER, "X minimum to probe", "mm"),
                                                                "x_max": DeviceSchemaEntry(AresDataType.NUMBER, "X maximum to probe", "mm"),
                                                                 "y_min": DeviceSchemaEntry(AresDataType.NUMBER, "Y minimum to probe", "mm"),
                                                                "y_max": DeviceSchemaEntry(AresDataType.NUMBER, "Y maximum to probe", "mm")},
                                    {"result": DeviceSchemaEntry(AresDataType.STRING, "Result", "")}),
            printer.probe_bed
        )

        # 5. Wait for printer (Added an output schema to force the button to render)
        service.add_new_command(
            DeviceCommandDescriptor("Wait for Printer", "G400",{}, {}),
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
