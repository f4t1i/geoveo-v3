from geoveo.models import RoutePoint, GeoVeoJob

class RoutingService:
    def plan_route(self, job: GeoVeoJob) -> list[RoutePoint]:
        # deterministic stub for development and tests
        base_lat, base_lng = 53.566, 9.992
        points: list[RoutePoint] = []
        for i in range(8):
            points.append(RoutePoint(lat=base_lat + i * 0.0005, lng=base_lng + i * 0.0007, heading_deg=70))
        return points
