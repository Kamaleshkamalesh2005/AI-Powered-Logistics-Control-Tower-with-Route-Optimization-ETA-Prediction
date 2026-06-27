from fastapi import APIRouter

from app.schemas.route_optimization import OptimizeRouteRequest, OptimizeRouteResponse
from app.services.route_optimization import RouteOptimizationService

router = APIRouter(prefix="", tags=["route-optimization"])


@router.post(
    "/optimize-route",
    response_model=OptimizeRouteResponse,
    summary="Optimize a vehicle routing problem",
    description="Solves a capacity-constrained VRP with OR-Tools and falls back to a nearest-neighbor heuristic if the solver cannot converge within 5 seconds.",
)
async def optimize_route(payload: OptimizeRouteRequest) -> OptimizeRouteResponse:
    service = RouteOptimizationService()
    return service.optimize(payload)
