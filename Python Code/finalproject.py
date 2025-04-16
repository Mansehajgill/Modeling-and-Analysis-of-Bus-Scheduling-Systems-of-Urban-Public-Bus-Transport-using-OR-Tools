import pandas as pd
from ortools.linear_solver import pywraplp

# Load the data from your CSV
df = pd.read_csv('Bus_finaldataset.csv')

# Use a subset of routes for testing
num_routes_test = 93  # Adjust as needed
routes = df['Route Number'].values[:num_routes_test]
demand = df[['First Shift', 'Second Shift', 'Third Shift', 'Fourth Shift']].values[:num_routes_test]
trip_factors = df[['Trips of first shift', 'Trips of Second shift', 'Trips of Third shift', 'Trips of Fourth shift']].values[:num_routes_test]

# Parameters
fleet_size_type1 = 600
fleet_size_type2 = 90
capacity_type1 = 60
capacity_type2 = 90

# Cost parameters
cost_type1 = 100
cost_type2 = 150

# Define solver
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise Exception("Solver not available!")

# Decision variables (Integer values)
x = {}
y = {}
for i in range(len(routes)):
    for j in range(4):
        x[i, j] = solver.IntVar(0, solver.infinity(), f'x_{i}_{j}')
        y[i, j] = solver.IntVar(0, solver.infinity(), f'y_{i}_{j}')

# Shift-specific bus usage variables
shift_x = {}
shift_y = {}
for j in range(4):
    shift_x[j] = solver.IntVar(0, solver.infinity(), f'shift_x_{j}')
    shift_y[j] = solver.IntVar(0, solver.infinity(), f'shift_y_{j}')

# Objective function: Minimize total cost
objective_function = solver.Sum(x[i, j] * cost_type1 * trip_factors[i, j] + y[i, j] * cost_type2 * trip_factors[i, j] for i in range(len(routes)) for j in range(4))
solver.Minimize(objective_function)

# Constraints
for i in range(len(routes)):
    for j in range(4):
        # Demand satisfaction constraint
        solver.Add(x[i, j] * capacity_type1 * trip_factors[i, j] + y[i, j] * capacity_type2 * trip_factors[i, j] >= demand[i, j])

# Shift-specific bus usage constraints
for j in range(4):
    solver.Add(shift_x[j] == solver.Sum(x[i, j] for i in range(len(routes))))
    solver.Add(shift_y[j] == solver.Sum(y[i, j] for i in range(len(routes))))

# Shift-specific fleet size limitations
for j in range(4):
    solver.Add(shift_x[j] <= fleet_size_type1)
    solver.Add(shift_y[j] <= fleet_size_type2)

# Solve the model
status = solver.Solve()

# Extract and display results
if status == pywraplp.Solver.OPTIMAL:
    print("Optimal solution found!")
    schedule = []
    for i in range(len(routes)):
        for j in range(4):
            schedule.append([routes[i], j + 1, x[i, j].solution_value(), y[i, j].solution_value()])
    df_schedule = pd.DataFrame(schedule, columns=['Route', 'Shift', 'Type1_Buses', 'Type2_Buses'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    print(df_schedule)

    total_type1_buses = df_schedule['Type1_Buses'].sum()
    total_type2_buses = df_schedule['Type2_Buses'].sum()
    print(f"Total Type-1 buses used: {total_type1_buses}")
    print(f"Total Type-2 buses used: {total_type2_buses}")

    for j in range(4):
        print(f"Shift {j + 1}: Type-1 buses used = {shift_x[j].solution_value()}, Type-2 buses used = {shift_y[j].solution_value()}")

elif status == pywraplp.Solver.ABNORMAL or status == pywraplp.Solver.NOT_SOLVED:
    print("Solver did not find an optimal solution.")
elif status == pywraplp.Solver.INFEASIBLE:
    print("No feasible solution found. Check constraints.")
elif status == pywraplp.Solver.UNBOUNDED:
    print("The problem is unbounded.")
elif status == pywraplp.Solver.MODEL_INVALID:
    print("The model is invalid.")
else:
    print("Other error occurred.")