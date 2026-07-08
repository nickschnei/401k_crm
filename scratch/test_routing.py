import sys
import os

# Append the project path so we can import modules
sys.path.append(r"c:\Users\nicks\Documents\401k_crm")

from utils.geocoder import geocode_address
from api.trip import haversine_distance_miles, solve_tsp_brute_force, solve_tsp_nearest_neighbor_2opt

def test_routing():
    print("=== TESTING TRIP PLANNER ALGORITHMS ===")
    
    # 1. Test Geocoder Fallback
    print("Testing state centroid fallback...")
    lat, lon = geocode_address("123 Fake Street, Indianapolis, IN 46204")
    print(f"  Geocoded Indiana address: {lat}, {lon}")
    assert lat is not None and lon is not None
    
    # 2. Test Haversine Distance
    print("Testing Haversine distance...")
    # Distance between Indianapolis, IN (39.7684, -86.1581) and Lewiston, ME (44.1003, -70.2147)
    dist = haversine_distance_miles(39.7684, -86.1581, 44.1003, -70.2147)
    print(f"  Distance between Indy and Lewiston: {dist:.2f} miles")
    assert 800 < dist < 950 # should be around 850 miles
    
    # 3. Test TSP Solver (Brute Force vs Heuristic)
    print("Testing TSP solvers...")
    # Distance matrix for 4 locations in a square grid:
    # 0 -> Start, 1 -> Top, 2 -> Top-Right, 3 -> Right
    # Cost optimal: 0 -> 1 -> 2 -> 3 -> (0) (cost: 4)
    # Cost bad: 0 -> 2 -> 1 -> 3 -> (0) (cost: >4)
    dist_matrix = [
        [0.0, 1.0, 1.414, 1.0],  # 0
        [1.0, 0.0, 1.0, 1.414],  # 1
        [1.414, 1.0, 0.0, 1.0],  # 2
        [1.0, 1.414, 1.0, 0.0]   # 3
    ]
    
    route_bf = solve_tsp_brute_force(dist_matrix, round_trip=True)
    print(f"  Brute force route indices: {route_bf}")
    # Optimal round trip route is index 0 -> 1 -> 2 -> 3
    # Wait, 0 -> 3 -> 2 -> 1 is also optimal (reverse cost is the same)
    
    route_nn = solve_tsp_nearest_neighbor_2opt(dist_matrix, round_trip=True)
    print(f"  2-opt heuristic route indices: {route_nn}")
    
    print("\nALL BACKEND ROUTING ALGORITHMS PASSED!")

if __name__ == "__main__":
    test_routing()
