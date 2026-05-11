from urllib import request

from PyAres import *

import random

def plan(request: PlanRequest) -> PlanResponse:
    print("Planning Requested!")
    gpdoods = []
    nelder_mead = False
    param_dict = {}
    prev_param_dict = {}

    for param in request.parameters:
        # Add the previous value to the dict
        prev_param_dict[param.name] = param.param_history[-1].planned_value

        if param.planner_name == "GPRDood":
            gpdoods.append(param)

        if param.planner_name == "Random Planner":
            new_value = random_planner(param)
            param_dict[param.name] = new_value

        elif param.planner_name == "Gradual Planner":
            new_value = gradual_planner(param)
            param_dict[param.name] = new_value

        elif param.planner_name == "Nelder Mead Planner":
            #Nelder Mead needs all planner args passed at once
            nelder_mead = True
            break

        else:
            print("Invalid planner name detected... defaulting to random")
            new_value = random_planner(param)
            param_dict[param.name] = new_value

    # Add the data to the data store
    data_store.append(prev_param_dict)

    if nelder_mead:
            #Pass all params and results to the algorithm
            param_dict = nelder_mead_planner(list(request.parameters), request.analysis_results)

    return PlanResponse(parameter_names=list(param_dict.keys()), parameter_values=list(param_dict.values()))


def random_planner(param: PlanningParameter) -> float:
    if param.data_type == AresDataType.NUMBER:
        return random.uniform(param.minimum_value, param.maximum_value)

    else:
        print("Found a non-number....")
        return 0


def gradual_planner(param: PlanningParameter) -> float:
    if (param.data_type == AresDataType.NUMBER):
        if len(param.param_history) == 0:
            return param.minimum_value

        previous_value = param.param_history[-1].planned_value
        previous_value += 5

        if previous_value > param.maximum_value:
            return param.minimum_value

        else:
            return previous_value

    else:
        return 0


def nelder_mead_planner(params: list, results) -> list:
    def get_centroid() -> dict:
        new_point = {}
        for axis in request.parameters:
            new_point[axis.name] = 0
            for point in best_points:
                new_point[axis.name] += point[axis.name]
            new_point[axis.name] = new_point[axis.name] / len(best_points)
        return new_point
    # Using the params list and the list of results, use the nelder-mead method to
    # Approximate a new point (local maximum) to test
    # Return the point as new_vals
    new_vals = {}
    n = len(results)
    if n <= 5:
        best_points.append(data_store[-1])
        # If the simplex doesn't have enough points, make a new point
        for i in range(n):
            new_vals[request.parameters[i].name] = (results[i] + (i - 1 == n) *
                                                    (request.parameters[i].maximum_value - request.parameters[i].minimum_value))

        return new_vals
    elif n == 6:
        # Not super efficient, but if we have the first new point, then
    else:
        # Apply nelder-mead algorithm:
        # Sort results:
        outcomes = list(results.sort())
        # Find centroid of all points but x










if __name__ == "__main__":
    # Basic details about your planner
    name = "Python Test Planner"
    version = "1.0.0"
    description = "This is a test planner to demonstrate working with PyAres to create planners!"
    pythonDemoPlanner = AresPlannerService(plan, name, description, version)

    # Add Supported Types
    pythonDemoPlanner.add_supported_type(AresDataType.NUMBER)

    # Add Planner Options
    pythonDemoPlanner.add_planner_option("Random Planner", "A planner that returns random values", "1.0.0")
    pythonDemoPlanner.add_planner_option("Gradual Planner",
                                         "A planner that gradually increases a value based on the values history",
                                         "1.0.0")

    # Data store of all values
    data_store = []

    # Data store of best values for use in nelder-mead planner
    best_points = []

    # Add Planner Settings
    pythonDemoPlanner.add_setting("String Setting", AresDataType.STRING)
    pythonDemoPlanner.add_setting("Number Setting", AresDataType.NUMBER)
    pythonDemoPlanner.add_setting("Boolean Setting", AresDataType.BOOLEAN)
    pythonDemoPlanner.add_setting("String Array Setting", AresDataType.STRING_ARRAY)
    pythonDemoPlanner.add_setting("Constrained Strings", AresDataType.STRING_ARRAY, True, ["One", "Two", "Three"])
    pythonDemoPlanner.add_setting("Number Array Setting", AresDataType.NUMBER_ARRAY)
    pythonDemoPlanner.add_setting("Constrained Numbers", AresDataType.NUMBER_ARRAY, True, [1, 2, 3])

    # Set Planner Timeout
    pythonDemoPlanner.set_timeout(60)

    # Start Your Planner Service
    pythonDemoPlanner.start()
