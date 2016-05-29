from django.db import models

class Station(models.Model):
    id = models.IntegerField(primary_key=True)
    system = models.ForeignKey('MapSolarSystem')
    name = models.CharField(max_length=100, unique=True)

class MapRegion(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

class MapConstellation(models.Model):
    id = models.IntegerField(primary_key=True)
    region = models.ForeignKey('MapRegion')
    name = models.CharField(max_length=100, unique=True)

class MapSolarSystem(models.Model):
    id = models.IntegerField(primary_key=True)

    region = models.ForeignKey('MapRegion')
    constellation = models.ForeignKey('MapConstellation')

    name = models.CharField(max_length=100, unique=True)
    security_level = models.FloatField()

class GraphNode(models.Model):
    id = models.IntegerField(primary_key=True)
    system = models.ForeignKey('MapSolarSystem')

class GraphEdge(models.Model):
    origin = models.ForeignKey('GraphNode', related_name="edge_origins")
    destination = models.ForeignKey('GraphNode', related_name="edge_destinations")
    distance = models.FloatField(null=True)