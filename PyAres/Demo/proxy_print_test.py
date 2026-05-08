from PyAres import AresDeviceService, AresDataType, DeviceSchemaEntry, DeviceCommandDescriptor

#import random
# --- PART 1: The Simulated Hardware ---
class VirtualPrinter:
    def __init__(self):
        self.target_temp = 25.0 # Start at room temp
        self.print_speed = 100.0 # Start at 100mm/minm
        self.z_height = 0.5 # Start at 0.5 mm
        self.pressure = 30 #Start at 30 kPa
        #self.print_score = random.randint(1, 100)
    
    def set_temperature(self, temp: float):
        """Simulates setting the heater."""
        print(f"[Hardware] Heating to {temp}°C...")
        self.target_temp = temp
        return {} # Return empty dict if no data needs to be sent back
    
    def set_print_speed(self, speed: float):
        """Simulates setting the print speed."""
        print(f"[Hardware] Setting print speed to {speed} mm/min...")
        self.print_speed = speed
        return {} # Return empty dict if no data needs to be sent back

    def set_z_height(self, z_height: float):
        """Simulates setting the Z height."""
        print(f"[Hardware] Setting Z height to {z_height} mm...")
        self.z_height = z_height
        return {} # Return empty dict if no data needs to be sent back

    def set_pressure(self, pressure: float):
        """Simulates setting the pressure."""
        print(f"[Hardware] Setting pressure to {pressure} kPa...")
        self.pressure = pressure
        return {} # Return empty dict if no data needs to be sent back

    def get_temperature(self):
        """Simulates reading the temperature."""
        # In a real device, you'd read a serial port here.
        print("[Hardware] Retrieving the current temperature...")
        return { "current_temp": self.target_temp }
    
    def get_print_speed(self):
        """Returns the print speed."""
        print("[Hardware] Retrieving the current print speed...")
        return { "current_speed": self.print_speed }

    def get_z_height(self):
        """Returns the Z height."""
        print("[Hardware] Retrieving the current Z height...")
        return { "current_z_height": self.z_height }

    def get_pressure(self):
        """Simulates reading the pressure."""
        print("[Hardware] Retrieving the current pressure...")
        return { "current_pressure": self.pressure }

    def get_state(self):
        """Required: Tells ARES the current status for logging."""
        return { "current_temp": self.target_temp, "current_speed": self.print_speed, 
                "current_z_height": self.z_height, "current_pressure": self.pressure}

    def safe_mode(self):
        """Required: A safety fallback (e.g., turn off heat)."""
        print("[Hardware] SAFE MODE TRIGGERED: Heater off.")
        self.target_temp = 0.0
        self.print_speed = 0.0

# --- PART 2: The Ares Service Wrapper ---
if __name__ == "__main__":
    # 1. Initialize the hardware
    myprinter = VirtualPrinter()

    # 2. Define the Service Info
    service = AresDeviceService(
        myprinter.safe_mode,
        myprinter.get_state,
        "My Virtual Printer",    # Device Name
        "A simulated lab printer", # Description
        "1.0.0"                   # Version
    )

    # 3. Define Set Commands:
    # This schema tells ARES to draw a Number Input box in the UI
    input_schema = { 
        "temp": DeviceSchemaEntry(AresDataType.NUMBER, "Target Temperature", "Celsius") 
    }
    set_cmd = DeviceCommandDescriptor(
        "Set Temperature", 
        "Sets the printer target temperature", 
        input_schema, 
        {} # No output expected
    )
    service.add_new_command(set_cmd, myprinter.set_temperature)
    input_schema = { 
        "speed": DeviceSchemaEntry(AresDataType.NUMBER, "Target Speed", "mm/min") 
    }
    set_cmd = DeviceCommandDescriptor(
        "Set Speed", 
        "Sets the printer target speed", 
        input_schema, 
        {} # No output expected
    )
    service.add_new_command(set_cmd, myprinter.set_print_speed)
    input_schema = { 
        "z_height": DeviceSchemaEntry(AresDataType.NUMBER, "Z Height", "mm") 
    }
    set_cmd = DeviceCommandDescriptor(
        "Set Z Height", 
        "Sets the distance between the printer and the bed", 
        input_schema, 
        {} # No output expected
    )
    service.add_new_command(set_cmd, myprinter.set_z_height)
    input_schema = { 
        "pressure": DeviceSchemaEntry(AresDataType.NUMBER, "Pressure", "kPa") 
    }
    set_cmd = DeviceCommandDescriptor(
        "Set Pressure", 
        "Sets the nozzle's pressure", 
        input_schema, 
        {} # No output expected
    )
    service.add_new_command(set_cmd, myprinter.set_pressure)

    # 4. Define Command: Get Temperature
    # This schema tells ARES to expect a number back
    output_schema = { 
        "temp": DeviceSchemaEntry(AresDataType.NUMBER, "Target Temperature", "Celsius") 
    }
    get_cmd = DeviceCommandDescriptor(
        "get Temp", 
        "gets the printer target temperature", 
        {}, # No input needed
        output_schema 
    )
    service.add_new_command(get_cmd, myprinter.get_temperature)
    output_schema = { 
        "speed": DeviceSchemaEntry(AresDataType.NUMBER, "Target Speed", "mm/min") 
    }
    get_cmd = DeviceCommandDescriptor(
        "get Speed", 
        "gets the printer target speed", 
        {}, # No input needed
        output_schema
    )
    service.add_new_command(get_cmd, myprinter.get_print_speed)
    output_schema = { 
        "z_height": DeviceSchemaEntry(AresDataType.NUMBER, "Z Height", "mm") 
    }
    get_cmd = DeviceCommandDescriptor(
        "get Z Height", 
        "gets the distance between the printer and the bed", 
        {}, # No input needed
        output_schema
    )
    service.add_new_command(get_cmd, myprinter.get_z_height)
    output_schema = { 
        "pressure": DeviceSchemaEntry(AresDataType.NUMBER, "Pressure", "kPa") 
    }
    get_cmd = DeviceCommandDescriptor(
        "get Pressure", 
        "gets the nozzle's pressure", 
        {}, # No input needed
        output_schema
    )
    service.add_new_command(get_cmd, myprinter.get_pressure)

    # 5. Start the Service
    # This will block and listen for ARES connections
    print("Virtual Printer Service Running...")
    service.start()
