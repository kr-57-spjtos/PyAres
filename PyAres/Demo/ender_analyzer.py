from PyAres import AresAnalyzerService, AnalysisRequest, Analysis, AresDataType, Outcome
import os
import json
from pathlib import Path

def analyze(request: AnalysisRequest) -> Analysis:
    print("Analyzing...")
    #Custom Analysis Logic
    temperature = request.inputs.get("Temperature")
    print_speed = request.inputs.get("Print_Speed")
    z_height = request.inputs.get("Z_Height")

    try:
        temperature = float(temperature)
    except:
        print(f"Temperature {temperature} was not a float")
        print(f"Temperature was a {type(temperature)}")
        temperature = 0.0

    try:
        print_speed = float(print_speed)
    except:
        print(f"Print Speed {print_speed} was not a float")
        print(f"Print Speed was a {type(print_speed)}")
        print_speed = 0.0

    try:
        z_height = float(z_height)
    except:
        print(f"Z Height {z_height} not a float")
        print(f"Z Height was a {type(z_height)}")
        z_height = 5.0

    print(f"Temperature: {temperature}")
    print(f"Print Speed: {print_speed}")
    print(f"Z Height: {z_height}")

    analysis = Analysis(result=temperature*print_speed/4)

    def store_data() -> None:
        params = {"temperature": temperature, "print_speed": print_speed, "z_height": z_height}
        all_data = {"params": params, "results": analysis}
        """
        # Make output dir for printer
        output_folder = f"/~/Desktop/Ares_json/{request.request_metadata.campaign_name}__{request.request_metadata.experiment_start_time}"
        os.makedirs(output_folder, exist_ok=True)

        # Update json file with params
        with open('/Users/katierasmussen/Desktop/StructuralColor/all_campaigns_Dec_10_2025_clean.json', 'a',
                      encoding='utf-8') as f:
                f.write(json.dumps(all_data))
        """

    store_data()
    return analysis


if __name__ == "__main__":
    #Basic details about your analyzer
    name = "Python Test Analyzer"
    version = "0.0.1"
    description = "This is a test analyzer to demonstrate working with PyAres to create analyzers!"
    pythonDemoAnalyzer = AresAnalyzerService(analyze, name, version, description)

    #Add Analysis Parameters
    pythonDemoAnalyzer.add_analysis_parameter("Temperature", AresDataType.NUMBER)
    pythonDemoAnalyzer.add_analysis_parameter("Print_Speed", AresDataType.NUMBER)
    pythonDemoAnalyzer.add_analysis_parameter("Z_Height", AresDataType.NUMBER)
    pythonDemoAnalyzer.add_setting(setting_name="", setting_type=AresDataType.NULL, optional=True, constraints=[])
    pythonDemoAnalyzer.start(wait_for_termination=True)

    pythonDemoAnalyzer.start()