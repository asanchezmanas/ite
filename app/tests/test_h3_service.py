# app/tests/test_h3_service.py

import pytest
from app.services.h3_service import h3_service, H3Service


class TestH3Service:
    """Tests para servicio H3"""
    
    def test_lat_lng_to_cell(self):
        """Convertir coordenadas a H3 cell"""
        # Barcelona
        lat, lng = 41.3851, 2.1734
        
        h3_index = h3_service.lat_lng_to_cell(lat, lng)
        
        assert h3_index is not None
        assert isinstance(h3_index, str)
        assert len(h3_index) == 15  # H3 index tiene 15 caracteres
    
    def test_cell_to_lat_lng(self):
        """Convertir H3 cell a coordenadas"""
        # Barcelona
        original_lat, original_lng = 41.3851, 2.1734
        h3_index = h3_service.lat_lng_to_cell(original_lat, original_lng)
        
        result_lat, result_lng = h3_service.cell_to_lat_lng(h3_index)
        
        # Debería estar muy cerca del original (dentro de margen de error)
        assert abs(result_lat - original_lat) < 0.01
        assert abs(result_lng - original_lng) < 0.01
    
    def test_cell_to_boundary(self):
        """Obtener vértices del hexágono"""
        lat, lng = 41.3851, 2.1734
        h3_index = h3_service.lat_lng_to_cell(lat, lng)
        
        boundary = h3_service.cell_to_boundary(h3_index)
        
        assert len(boundary) == 7  # Hexágono tiene 6 vértices + 1 repetido para cerrar
        assert all(isinstance(point, tuple) for point in boundary)
        assert all(len(point) == 2 for point in boundary)
    
    def test_polyline_to_cells(self):
        """Convertir polyline a cells"""
        # Polyline simple de ejemplo (Barcelona a Sagrada Familia)
        polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        
        cells = h3_service.polyline_to_cells(polyline)
        
        assert isinstance(cells, list)
        assert len(cells) > 0
        assert all(isinstance(cell, str) for cell in cells)
    
    def test_get_neighbors(self):
        """Obtener hexágonos vecinos"""
        lat, lng = 41.3851, 2.1734
        h3_index = h3_service.lat_lng_to_cell(lat, lng)
        
        neighbors = h3_service.get_neighbors(h3_index, k=1)
        
        assert len(neighbors) == 7  # 1 centro + 6 vecinos
        assert h3_index in neighbors
    
    def test_get_neighbors_k2(self):
        """Obtener vecinos de 2 anillos"""
        lat, lng = 41.3851, 2.1734
        h3_index = h3_service.lat_lng_to_cell(lat, lng)
        
        neighbors = h3_service.get_neighbors(h3_index, k=2)
        
        assert len(neighbors) == 19  # 1 + 6 + 12
    
    def test_get_area_cells(self):
        """Obtener cells en un área"""
        # Centro de Barcelona, radio 5 km
        lat, lng = 41.3851, 2.1734
        radius_km = 5
        
        cells = h3_service.get_area_cells(lat, lng, radius_km)
        
        assert isinstance(cells, list)
        assert len(cells) > 0
        # Con resolución 9 y 5km radio, debería haber muchos hexágonos
        assert len(cells) > 100
    
    def test_cells_distance(self):
        """Calcular distancia entre cells"""
        lat1, lng1 = 41.3851, 2.1734  # Barcelona
        lat2, lng2 = 41.3900, 2.1800  # Cerca de Barcelona
        
        cell1 = h3_service.lat_lng_to_cell(lat1, lng1)
        cell2 = h3_service.lat_lng_to_cell(lat2, lng2)
        
        distance = h3_service.cells_distance(cell1, cell2)
        
        assert isinstance(distance, int)
        assert distance >= 0
    
    def test_is_valid_cell(self):
        """Validar H3 cell"""
        lat, lng = 41.3851, 2.1734
        valid_cell = h3_service.lat_lng_to_cell(lat, lng)
        
        assert h3_service.is_valid_cell(valid_cell) is True
        assert h3_service.is_valid_cell("invalid") is False
        assert h3_service.is_valid_cell("") is False
    
    def test_get_city_stats(self):
        """Obtener estadísticas de zonas"""
        lat, lng = 41.3851, 2.1734
        cells = h3_service.get_area_cells(lat, lng, 2)
        
        stats = h3_service.get_city_stats(cells)
        
        assert "total_zones" in stats
        assert "total_area_km2" in stats
        assert "resolution" in stats
        assert stats["total_zones"] == len(cells)
        assert stats["total_area_km2"] > 0
    
    def test_get_city_stats_empty(self):
        """Estadísticas con lista vacía"""
        stats = h3_service.get_city_stats([])
        
        assert stats["total_zones"] == 0
        assert stats["total_area_km2"] == 0
    
    def test_different_resolutions(self):
        """Probar diferentes resoluciones"""
        lat, lng = 41.3851, 2.1734
        
        # Resolución 7 (más grande)
        service_res7 = H3Service(resolution=7)
        cell_res7 = service_res7.lat_lng_to_cell(lat, lng)
        
        # Resolución 10 (más pequeño)
        service_res10 = H3Service(resolution=10)
        cell_res10 = service_res10.lat_lng_to_cell(lat, lng)
        
        # Los índices deberían ser diferentes
        assert cell_res7 != cell_res10
        
        # Área de res7 debería ser mayor
        neighbors_res7 = service_res7.get_area_cells(lat, lng, 1)
        neighbors_res10 = service_res10.get_area_cells(lat, lng, 1)
        
        assert len(neighbors_res10) > len(neighbors_res7)


class TestPolylineDecoding:
    """Tests específicos para decodificación de polylines"""
    
    def test_decode_simple_polyline(self):
        """Decodificar polyline simple"""
        # Polyline de ejemplo
        polyline = "_p~iF~ps|U_ulLnnqC"
        
        points = h3_service._decode_polyline(polyline)
        
        assert isinstance(points, list)
        assert len(points) > 0
        assert all(isinstance(p, tuple) for p in points)
        assert all(len(p) == 2 for p in points)
    
    def test_decode_empty_polyline(self):
        """Decodificar polyline vacía"""
        points = h3_service._decode_polyline("")
        
        assert points == []
    
    def test_decode_real_polyline(self):
        """Decodificar polyline real de Strava"""
        # Polyline real simplificada
        polyline = "gvs~Fz}biVnB?@j@VjALj@P~@Pv@@d@Bx@?t@Ar@E~@G`A"
        
        points = h3_service._decode_polyline(polyline)
        
        assert len(points) > 5
        # Todos los puntos deberían tener coordenadas válidas
        assert all(-90 <= lat <= 90 for lat, lng in points)
        assert all(-180 <= lng <= 180 for lat, lng in points)
