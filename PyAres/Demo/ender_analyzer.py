from PyAres import AresAnalyzerService, AnalysisRequest, Analysis, AresDataType, Outcome

def analyze(request: AnalysisRequest) -> Analysis:
    #Custom Analysis Logic
    temperature = request.inputs.get("Temperature")
    print_speed = request.inputs.get("Print_Speed")
    z_height = request.inputs.get("Z_Height")

    if not isinstance(temperature, float):
        print("Temperature was not a float")
        temperature = 0.0

    if not isinstance(print_speed, float):
        print("Print Speed was not a float")
        print_speed = 0.0

    if not isinstance(z_height, float):
        print("Z Height was not a float")
        z_height = 5.0

    print(f"Temperature: {temperature}")
    print(f"Print Speed: {print_speed}")
    print(f"Z Height: {z_height}")

    analysis = Analysis(result=temperature*print_speed/4)
    return analysis


if __name__ == "__main__":
    #Basic details about your analyzer
    name = "Python Test Analyzer"
    version = "0.0.1"
    description = "This is a test analyzer to demonstrate working with PyAres to create analyzers!"
    pythonDemoAnalyzer = AresAnalyzerService(analyze, name, version, description)

    #Add Analysis Parameters
    pythonDemoAnalyzer.add_analysis_parameter("Temperature", AresDataType.NUMBER)
    pythonDemoAnalyzer.add_setting(setting_name="", setting_type=AresDataType.NULL, optional=True, constraints=[])
    pythonDemoAnalyzer.start(wait_for_termination=True)

    pythonDemoAnalyzer.start()