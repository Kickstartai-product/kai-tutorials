from ortools.sat.python import cp_model
import itertools
import csv
from pathlib import Path

def solve_assignment_ortools():
    # Setup data directory path
    data_dir = Path(__file__).parent.parent / 'data'
    
    # Parse the addresses
    with open(data_dir / 'address_list.csv', 'r') as f:
        addresses = [addr.strip() for addr in f.readlines()[1:] if addr.strip()]
    N = len(addresses)
    SECTION_SIZE = 23

    # Parse last year's course assignments
    previous_hosts = {}
    with open(data_dir / 'last_year_courses.csv', 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 2:
                address, course = row[0].strip(), int(row[1])
                if address in addresses:
                    previous_hosts[address] = course

    # Parse historical triplets into all historical combinations
    historical_pairs = set()
    with open(data_dir / 'last_year_assignments.csv', 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 3:
                triplet = [addr.strip() for addr in row[:3]]
                valid_pairs = [(a1, a2) for a1, a2 in itertools.combinations(triplet, 2)
                              if a1 in addresses and a2 in addresses]
                historical_pairs.update(valid_pairs)

    # Create the model
    model = cp_model.CpModel()

    # Generate valid triplets
    valid_triplets = []
    for i in range(N):
        other_indices = [j for j in range(N) if j != i]
        for pair in itertools.combinations(other_indices, 2):
            valid_triplets.append((i, pair[0], pair[1]))

    print(f"Problem size: {N} addresses, {len(valid_triplets)} valid triplets")

    # Create variables and constraints
    # Decision variables y_t and x_t,p
    y = {t: model.NewBoolVar(f'y_{t}') for t in valid_triplets}
    
    pos_assign = {}
    for t in valid_triplets:
        first_addr = addresses[t[0]]
        for pos in range(N):
            section = pos // SECTION_SIZE + 1
            if first_addr not in previous_hosts or previous_hosts[first_addr] != section:
                pos_assign[t, pos] = model.NewBoolVar(f'x_{t}_{pos}')

    # Constraints
    # Each triplet must be assigned to exactly one position if used
    for t in valid_triplets:
        model.Add(sum(pos_assign.get((t, pos), 0) for pos in range(N)) == y[t])

    # Each position must be assigned exactly one triplet
    for pos in range(N):
        model.Add(sum(pos_assign.get((t, pos), 0) for t in valid_triplets) == 1)

    # Each person must appear in exactly three triplets
    for person in range(N):
        model.Add(sum(y[t] for t in valid_triplets if person in t) == 3)

    # Each person must appear exactly once in each section
    for person in range(N):
        for section in range(3):
            start = section * SECTION_SIZE
            end = (section + 1) * SECTION_SIZE
            model.Add(sum(pos_assign.get((t, pos), 0)
                         for t in valid_triplets if person in t
                         for pos in range(start, end)
                         if (t, pos) in pos_assign) == 1)

    # Each person must be a host exactly once
    for person in range(N):
        model.Add(sum(y[t] for t in valid_triplets if t[0] == person) == 1)

    # Each pair of people can appear together at most once
    all_pairs = list(itertools.combinations(range(N), 2))
    for pair in all_pairs:
        model.Add(sum(y[t] for t in valid_triplets 
                     if pair[0] in t and pair[1] in t) <= 1)

    # Historical pairs tracking
    # Decision variables w.r.t. historical pair tracking
    historical_pairs_list = list(historical_pairs)
    historical_pair_used = [model.NewBoolVar(f'hist_pair_{i}') 
                           for i in range(len(historical_pairs))]

    # Constraints for historical pairs
    for idx, historical_pair in enumerate(historical_pairs_list):
        addr1, addr2 = historical_pair
        addr1_idx = addresses.index(addr1)
        addr2_idx = addresses.index(addr2)
        
        model.Add(sum(y[t] for t in valid_triplets 
                     if addr1_idx in t and addr2_idx in t) <= historical_pair_used[idx])

    # Objective: Minimize the use of historical pairs
    model.Minimize(sum(historical_pair_used))

    # Solve with logging enabled
    print("\nStarting optimization...")
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    solver.parameters.max_time_in_seconds = 60*60  # 60-minute timeout
    solver.parameters.num_search_workers = 8  # Parallel search
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\nSolution found with objective value: {solver.ObjectiveValue()}")
        solution = [None] * N
        for t in valid_triplets:
            for pos in range(N):
                if (t, pos) in pos_assign and solver.Value(pos_assign[t, pos]) == 1:
                    triplet_addresses = tuple(addresses[i] for i in t)
                    solution[pos] = triplet_addresses
        return solution, addresses
    else:
        print("\nNo solution found!")
        return None, None

def write_solution_to_csv(solution, output_filename=None):
    """
    Write the solution to a CSV file with the following format:
    Position, Host, Guest1, Guest2, Section
    """
    if not solution:
        print("No solution to write to CSV!")
        return

    # If no output filename is provided, create one in the data directory
    if output_filename is None:
        output_dir = Path(__file__).parent.parent / 'data'
        output_filename = output_dir / 'assignment_solution.csv'
    
    # Ensure output directory exists
    output_filename.parent.mkdir(parents=True, exist_ok=True)

    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['Position', 'Host', 'Guest1', 'Guest2', 'Section'])
        
        # Write solution rows
        for position, triplet in enumerate(solution):
            if triplet:
                section = (position // 23) + 1  # Calculate section (1, 2, or 3)
                writer.writerow([
                    position + 1,  # Position (1-based)
                    triplet[0],    # Host
                    triplet[1],    # Guest1
                    triplet[2],    # Guest2
                    section        # Section number
                ])

def run_solver():
    """
    Main function to run the solver and output results
    """
    solution, _ = solve_assignment_ortools()
    if solution:
        print("\nWriting solution to CSV...")
        write_solution_to_csv(solution)
        print("Solution has been written to data/assignment_solution.csv")
        
        # Also print to console for verification
        print("\nFinal Solution:")
        for i, triplet in enumerate(solution):
            print(f"Position {i+1} (Section {(i // 23) + 1}): {triplet}")

if __name__ == '__main__':
    run_solver()