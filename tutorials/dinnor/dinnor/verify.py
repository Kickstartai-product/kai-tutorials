from typing import List, Tuple, Set
from collections import defaultdict
import itertools
import csv
from pathlib import Path

def parse_addresses(filepath: Path) -> List[str]:
    """Parse valid addresses from address list CSV."""
    with open(filepath, 'r') as f:
        addresses = [addr.strip() for addr in f.readlines()[1:] if addr.strip()]
    return addresses

def parse_previous_hosts(filepath: Path) -> dict:
    """Parse previous year's course assignments."""
    previous_hosts = {}
    with open(filepath, 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 2:
                address, course = row[0].strip(), int(row[1])
                previous_hosts[address] = course
    return previous_hosts

def parse_historical_pairs(filepath: Path, valid_addresses: List[str]) -> Set[Tuple[str, str]]:
    """Parse historical combinations."""
    historical_pairs = set()
    with open(filepath, 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 3:
                triplet = [addr.strip() for addr in row[:3]]
                valid_pairs = [(a1, a2) for a1, a2 in itertools.combinations(triplet, 2)
                              if a1 in valid_addresses and a2 in valid_addresses]
                historical_pairs.update(tuple(sorted(pair)) for pair in valid_pairs)
    return historical_pairs

def parse_solution(filepath: Path) -> List[Tuple[str, str, str]]:
    """Parse the solution from CSV file."""
    solution = []
    with open(filepath, 'r') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 4:  # Position, Host, Guest1, Guest2, Section
                solution.append((row[1], row[2], row[3]))
    return solution

def validate_dinner_solution(solution: List[Tuple[str, str, str]], 
                           valid_addresses: List[str],
                           previous_sections: dict,
                           historical_pairs: Set[Tuple[str, str]],
                           section_size: int = 23) -> bool:
    N = len(solution)
    all_valid = True
    
    def print_check(message: str, is_valid: bool) -> bool:
        check = "✓" if is_valid else "✗"
        print(f"{check} {message}")
        return is_valid
    
    def get_pairs(triplet: Tuple[str, str, str]) -> List[Tuple[str, str]]:
        return [tuple(sorted(pair)) for pair in itertools.combinations(triplet, 2)]
    
    # 1. Check basic structure and address validity
    print("\n=== Basic Structure and Address Checks ===")
    basic_valid = True
    
    # Check if all addresses are valid
    invalid_addresses = set()
    for triplet in solution:
        for addr in triplet:
            if addr not in valid_addresses:
                invalid_addresses.add(addr)
    
    basic_valid &= print_check(
        f"Solution has correct length (N={N})", 
        N == len(valid_addresses)
    )
    basic_valid &= print_check(
        "All entries are triplets", 
        all(len(t) == 3 for t in solution)
    )
    basic_valid &= print_check(
        "All addresses are valid",
        len(invalid_addresses) == 0
    )
    if invalid_addresses:
        print("Invalid addresses found:")
        for addr in invalid_addresses:
            print(f"  - {addr}")
    
    all_valid &= basic_valid
    
    # 2. Check participation constraints
    print("\n=== Participation Constraints ===")
    
    appearances = defaultdict(int)
    host_appearances = defaultdict(int)
    missing_addresses = set(valid_addresses)
    
    for pos, triplet in enumerate(solution):
        for person in triplet:
            appearances[person] += 1
            missing_addresses.discard(person)
        host_appearances[triplet[0]] += 1
    
    participation_valid = True
    
    appearance_violations = {addr: count for addr, count in appearances.items() 
                           if count != 3}
    host_violations = {addr: count for addr, count in host_appearances.items() 
                      if count != 1}
    
    if appearance_violations:
        print("\nAppearance violations:")
        for addr, count in appearance_violations.items():
            print(f"  - {addr}: appears {count} times (should be 3)")
    
    if host_violations:
        print("\nHost violations:")
        for addr, count in host_violations.items():
            print(f"  - {addr}: hosts {count} times (should be 1)")
    
    if missing_addresses:
        print("\nMissing addresses:")
        for addr in missing_addresses:
            print(f"  - {addr}")
    
    participation_valid &= print_check(
        "Each person appears exactly 3 times",
        len(appearance_violations) == 0
    )
    participation_valid &= print_check(
        "Each person hosts exactly once",
        len(host_violations) == 0
    )
    participation_valid &= print_check(
        "All addresses are used",
        len(missing_addresses) == 0
    )
    
    all_valid &= participation_valid
    
    # 3. Check section constraints
    print("\n=== Section Constraints ===")
    section_valid = True
    
    section_appearances = defaultdict(lambda: defaultdict(int))
    previous_section_violations = []
    
    for pos, triplet in enumerate(solution):
        section = pos // section_size + 1  # Sections are 1-based
        for person in triplet:
            section_appearances[person][section] += 1
            
        host = triplet[0]
        if host in previous_sections and section == previous_sections[host]:
            previous_section_violations.append(
                f"{host} is hosting in section {section} again"
            )
    
    section_violations = []
    for person, sections in section_appearances.items():
        if len(sections) != 3 or any(count != 1 for count in sections.values()):
            violations = [f"Section {s}: {c} times" for s, c in sections.items()]
            section_violations.append(f"  - {person}: {', '.join(violations)}")
    
    if section_violations:
        print("\nSection distribution violations:")
        for violation in section_violations:
            print(violation)
    
    if previous_section_violations:
        print("\nPrevious section violations:")
        for violation in previous_section_violations:
            print(f"  - {violation}")
    
    section_valid &= print_check(
        "Each person appears exactly once per section",
        len(section_violations) == 0
    )
    section_valid &= print_check(
        "No host is in same section as previous year",
        len(previous_section_violations) == 0
    )
    
    all_valid &= section_valid
    
    # 4. Check pair constraints
    print("\n=== Pair Constraints ===")
    pairs_valid = True
    
    used_pairs = set()
    duplicate_pairs = set()
    historical_pairs_used = set()
    
    for triplet in solution:
        triplet_pairs = get_pairs(triplet)
        for pair in triplet_pairs:
            if pair in used_pairs:
                duplicate_pairs.add(pair)
            used_pairs.add(pair)
            
            if pair in historical_pairs:
                historical_pairs_used.add(pair)
    
    if duplicate_pairs:
        print("\nDuplicate pairs found:")
        for pair in duplicate_pairs:
            print(f"  - {pair[0]} and {pair[1]}")
    
    if historical_pairs_used:
        print("\nHistorical pairs reused:")
        for pair in historical_pairs_used:
            print(f"  - {pair[0]} and {pair[1]}")
    
    pairs_valid &= print_check(
        "No pair appears more than once",
        len(duplicate_pairs) == 0
    )
    pairs_valid &= print_check(
        "No historical pairs are reused",
        len(historical_pairs_used) == 0
    )
    
    all_valid &= pairs_valid
    
    # Final verdict
    print("\n=== Final Verdict ===")
    print_check("All constraints satisfied", all_valid)
    
    return all_valid

def verify_solution():
    """Main function to verify the solution."""
    # Setup data directory path
    data_dir = Path(__file__).parent.parent / 'data'
    
    # Parse input data
    valid_addresses = parse_addresses(data_dir / 'address_list.csv')
    previous_sections = parse_previous_hosts(data_dir / 'last_year_courses.csv')
    historical_pairs = parse_historical_pairs(
        data_dir / 'last_year_assignments.csv',
        valid_addresses
    )
    
    # Parse the solution
    solution = parse_solution(data_dir / 'assignment_solution.csv')
    
    # Run the validation
    print("Running complete validation with all historical data...")
    return validate_dinner_solution(
        solution,
        valid_addresses=valid_addresses,
        previous_sections=previous_sections,
        historical_pairs=historical_pairs
    )

if __name__ == '__main__':
    verify_solution()