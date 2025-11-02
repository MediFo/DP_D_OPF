"""
Power Grid Topology Parser
Extracts network topology from MATPOWER case files
"""

import re
from typing import List, Tuple, Set
from pathlib import Path


def parse_matpower_case(case_file: str) -> List[Tuple[int, int]]:
    """
    Parse MATPOWER case file to extract bus connections

    Args:
        case_file: Path to MATPOWER .m file

    Returns:
        List of (bus_from, bus_to) tuples representing connected buses
    """
    case_path = Path(case_file)
    if not case_path.exists():
        raise FileNotFoundError(f"Case file not found: {case_file}")

    with open(case_path, 'r') as f:
        content = f.read()

    # Find the mpc.branch section
    # Format: mpc.branch = [ ... ];
    branch_match = re.search(r'mpc\.branch\s*=\s*\[(.*?)\];', content, re.DOTALL)

    if not branch_match:
        raise ValueError(f"Could not find mpc.branch data in {case_file}")

    branch_data = branch_match.group(1)

    # Parse each line of branch data
    # Each line has: fbus tbus r x b rateA rateB rateC ratio angle status angmin angmax
    # We only need columns 0 (fbus) and 1 (tbus)
    connections = []

    for line in branch_data.strip().split('\n'):
        # Remove comments
        line = re.sub(r'%.*$', '', line).strip()
        if not line:
            continue

        # Extract numbers from the line
        numbers = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', line)

        if len(numbers) >= 2:
            fbus = int(float(numbers[0]))
            tbus = int(float(numbers[1]))
            connections.append((fbus, tbus))

    return connections


def get_bus_neighbors(case_file: str, num_buses: int = None) -> dict:
    """
    Get neighbor mapping for each bus in the power grid

    Args:
        case_file: Path to MATPOWER .m file
        num_buses: Number of buses (if None, inferred from connections)

    Returns:
        Dictionary mapping bus_id -> list of neighbor bus_ids
    """
    connections = parse_matpower_case(case_file)

    # Build neighbor map
    neighbors = {}

    for fbus, tbus in connections:
        # Add bidirectional connections
        if fbus not in neighbors:
            neighbors[fbus] = set()
        if tbus not in neighbors:
            neighbors[tbus] = set()

        neighbors[fbus].add(tbus)
        neighbors[tbus].add(fbus)

    # Convert sets to sorted lists
    neighbors = {bus: sorted(list(neighs)) for bus, neighs in neighbors.items()}

    # If num_buses specified, ensure all buses are in the map
    if num_buses:
        for bus_id in range(1, num_buses + 1):
            if bus_id not in neighbors:
                neighbors[bus_id] = []

    return neighbors


def get_grid_statistics(case_file: str) -> dict:
    """
    Get statistics about the power grid topology

    Args:
        case_file: Path to MATPOWER .m file

    Returns:
        Dictionary with grid statistics
    """
    connections = parse_matpower_case(case_file)
    neighbors = get_bus_neighbors(case_file)

    num_buses = len(neighbors)
    num_lines = len(connections)

    # Calculate degree distribution
    degrees = [len(neighs) for neighs in neighbors.values()]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    min_degree = min(degrees) if degrees else 0

    return {
        'num_buses': num_buses,
        'num_lines': num_lines,
        'avg_connections_per_bus': avg_degree,
        'max_connections': max_degree,
        'min_connections': min_degree,
        'connections': connections,
        'neighbors': neighbors
    }


def visualize_topology(case_file: str):
    """
    Print a visualization of the power grid topology

    Args:
        case_file: Path to MATPOWER .m file
    """
    stats = get_grid_statistics(case_file)

    print(f"\nPower Grid Topology: {Path(case_file).name}")
    print("=" * 60)
    print(f"Buses: {stats['num_buses']}")
    print(f"Lines: {stats['num_lines']}")
    print(f"Average connections per bus: {stats['avg_connections_per_bus']:.2f}")
    print(f"Max connections: {stats['max_connections']}")
    print(f"Min connections: {stats['min_connections']}")

    print("\nBus Connections:")
    for bus_id in sorted(stats['neighbors'].keys()):
        neighs = stats['neighbors'][bus_id]
        print(f"  Bus {bus_id:2d} → {neighs}")


# Test
if __name__ == "__main__":
    import sys

    # Test with case files
    test_files = [
        "../testbeds/pglib_opf_case14_ieee.m",
        "../testbeds/pglib_opf_case30_ieee.m"
    ]

    for case_file in test_files:
        try:
            visualize_topology(case_file)
        except Exception as e:
            print(f"Error processing {case_file}: {e}")
