import math
import itertools
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from api.database import SessionLocal
from api.models import Prospect, Form5500Audit
from utils.auth import ClerkUser, get_current_user
from utils.geocoder import geocode_address

router = APIRouter()

class TripRequest(BaseModel):
    start_location: str
    eins: List[str]
    round_trip: bool = True

class TripStop(BaseModel):
    ein: Optional[str] = None
    name: str
    address: str
    lat: float
    lon: float
    distance_from_last: float
    leg_duration_minutes: float  # Estimate based on avg speed

class TripResponse(BaseModel):
    total_distance_miles: float
    total_duration_minutes: float
    stops: List[TripStop]

# ---------------------------------------------------------
# Fiduciary Distance & Route Solvers (TSP)
# ---------------------------------------------------------

def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth 
    in miles using the Haversine formula.
    """
    R = 3958.8  # Earth radius in miles
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_route_cost(route: List[int], dist_matrix: List[List[float]], round_trip: bool) -> float:
    """Calculates the total distance of a route."""
    cost = 0.0
    for i in range(len(route) - 1):
        cost += dist_matrix[route[i]][route[i+1]]
    if round_trip:
        cost += dist_matrix[route[-1]][route[0]]
    return cost

def solve_tsp_brute_force(dist_matrix: List[List[float]], round_trip: bool) -> List[int]:
    """
    Solves the Traveling Salesperson Problem exactly using brute-force.
    Guarantees global minimum. Fast for N <= 8.
    """
    n = len(dist_matrix)
    nodes_to_permute = list(range(1, n))
    
    best_route = [0] + nodes_to_permute
    best_cost = calculate_route_cost(best_route, dist_matrix, round_trip)
    
    for perm in itertools.permutations(nodes_to_permute):
        current_route = [0] + list(perm)
        current_cost = calculate_route_cost(current_route, dist_matrix, round_trip)
        if current_cost < best_cost:
            best_cost = current_cost
            best_route = current_route
            
    return best_route

def solve_tsp_nearest_neighbor_2opt(dist_matrix: List[List[float]], round_trip: bool) -> List[int]:
    """
    Solves TSP using nearest neighbor heuristic, followed by 2-opt swaps.
    Runs in milliseconds for larger datasets.
    """
    n = len(dist_matrix)
    unvisited = set(range(1, n))
    route = [0]
    
    # 1. Nearest Neighbor Heuristic
    current = 0
    while unvisited:
        next_node = min(unvisited, key=lambda node: dist_matrix[current][node])
        unvisited.remove(next_node)
        route.append(next_node)
        current = next_node
        
    # 2. 2-opt Swap Optimization
    # Performs local searches to untangle crossing paths
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 1):
            for j in range(i + 1, len(route)):
                if j - i == 1:
                    continue
                # Test swap
                new_route = route[:]
                new_route[i:j] = reversed(route[i:j])
                
                old_cost = calculate_route_cost(route, dist_matrix, round_trip)
                new_cost = calculate_route_cost(new_route, dist_matrix, round_trip)
                
                if new_cost < old_cost:
                    route = new_route
                    improved = True
                    
    return route

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@router.post("/planner", response_model=TripResponse)
async def plan_trip(
    request: TripRequest,
    current_user: ClerkUser = Depends(get_current_user)
):
    """
    Trip Planner Router Endpoint. Resolves coordinates for a starting location
    and a list of company EINs, solves the Traveling Salesperson Problem (TSP) 
    for the shortest route, and returns ordered itinerary stops.
    """
    db = SessionLocal()
    try:
        # 1. Geocode Start Location
        start_addr = request.start_location.strip()
        if not start_addr:
            raise HTTPException(status_code=400, detail="Start location cannot be empty.")
            
        try:
            start_lat, start_lon = geocode_address(start_addr)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to geocode start address: {str(e)}")
            
        # 2. Retrieve Company Addresses from local DB
        company_stops = []
        for ein in request.eins:
            normalized_ein = "".join(c for c in ein if c.isdigit())
            
            # Query the audit and prospects table
            prospect = db.query(Prospect).filter(Prospect.ein == normalized_ein).first()
            audit = db.query(Form5500Audit).filter(Form5500Audit.ein == normalized_ein).first()
            
            if not prospect:
                continue
                
            # If address exists in audit table, use it
            if audit and audit.dol_address:
                zip_str = str(audit.dol_zip).split('.')[0] if audit.dol_zip else ""
                addr_str = f"{audit.dol_address}, {audit.dol_city}, {audit.dol_state} {zip_str}"
            else:
                # Mock a search location based on prospect industry/provider
                addr_str = f"{prospect.employer_name}, Lewiston, ME"
                
            try:
                lat, lon = geocode_address(addr_str)
                company_stops.append({
                    "ein": prospect.ein,
                    "name": prospect.employer_name,
                    "address": addr_str,
                    "lat": lat,
                    "lon": lon
                })
            except Exception:
                # Skip if geocoding fails completely
                continue
                
        if not company_stops:
            raise HTTPException(status_code=400, detail="No valid target companies could be geocoded.")
            
        # 3. Build Node List and Distance Matrix
        # Node 0 is the Start Location
        all_nodes = [{
            "ein": None,
            "name": "Start Location",
            "address": start_addr,
            "lat": start_lat,
            "lon": start_lon
        }] + company_stops
        
        num_nodes = len(all_nodes)
        dist_matrix = [[0.0] * num_nodes for _ in range(num_nodes)]
        
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    dist_matrix[i][j] = 0.0
                else:
                    dist_matrix[i][j] = haversine_distance_miles(
                        all_nodes[i]["lat"], all_nodes[i]["lon"],
                        all_nodes[j]["lat"], all_nodes[j]["lon"]
                    )
                    
        # 4. Solve the TSP
        # If N <= 8, solve exactly using brute force, else use nearest neighbor + 2-opt
        if num_nodes <= 8:
            optimal_route_indices = solve_tsp_brute_force(dist_matrix, request.round_trip)
        else:
            optimal_route_indices = solve_tsp_nearest_neighbor_2opt(dist_matrix, request.round_trip)
            
        # 5. Format legs and aggregate calculations
        stops_result = []
        total_distance = 0.0
        
        # Build leg breakdowns
        for idx, node_idx in enumerate(optimal_route_indices):
            node = all_nodes[node_idx]
            
            if idx == 0:
                dist_from_last = 0.0
            else:
                prev_node_idx = optimal_route_indices[idx - 1]
                dist_from_last = dist_matrix[prev_node_idx][node_idx]
                
            total_distance += dist_from_last
            
            # Driving duration estimate: assume 45 mph average speed in sales route legs
            duration_minutes = (dist_from_last / 45.0) * 60.0
            
            stops_result.append(TripStop(
                ein=node["ein"],
                name=node["name"],
                address=node["address"],
                lat=node["lat"],
                lon=node["lon"],
                distance_from_last=round(dist_from_last, 1),
                leg_duration_minutes=round(duration_minutes, 1)
            ))
            
        # Add round-trip return stop if configured
        if request.round_trip:
            start_node = all_nodes[0]
            last_node_idx = optimal_route_indices[-1]
            dist_to_start = dist_matrix[last_node_idx][0]
            total_distance += dist_to_start
            duration_minutes = (dist_to_start / 45.0) * 60.0
            
            stops_result.append(TripStop(
                ein=None,
                name="Return to Start",
                address=start_node["address"],
                lat=start_node["lat"],
                lon=start_node["lon"],
                distance_from_last=round(dist_to_start, 1),
                leg_duration_minutes=round(duration_minutes, 1)
            ))
            
        # Total duration estimate: driving duration + 45 minutes on-site audit meeting per client stop
        total_driving_duration = (total_distance / 45.0) * 60.0
        # 45 mins meeting per company stop (excludes start and return stops)
        meeting_stops_count = len(company_stops)
        total_meeting_duration = meeting_stops_count * 45.0
        total_duration_minutes = total_driving_duration + total_meeting_duration
        
        return TripResponse(
            total_distance_miles=round(total_distance, 1),
            total_duration_minutes=round(total_duration_minutes, 1),
            stops=stops_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal route optimization failure: {str(e)}")
    finally:
        db.close()
