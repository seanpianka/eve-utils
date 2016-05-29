from django import forms

from static_dump.models import MapSolarSystem, MapRegion, Station

class SystemNameField(forms.CharField):
    def clean(self, value):
        value = super(SystemNameField, self).clean(value)
        
        if(value):
            if(MapSolarSystem.objects.filter(name=value).count() == 0):
                raise forms.ValidationError("Solar system '%s' not found"%(value))
            
        return value
    
class MultiSystemNameField(forms.CharField):
    def clean(self, value):
        value = super(MultiSystemNameField, self).clean(value)
        
        if(value):
            value_list = [v.strip() for v in value.split(',')]
            found_set = {n.lower() for n in MapSolarSystem.objects.filter(name__in=value_list).values_list('name',flat=True)}
            
            not_found = list()
            
            for v in value_list:
                if(v.lower() not in found_set):
                    not_found.append(v)
            
            if(len(not_found) > 0):
                raise forms.ValidationError("Solar system(s) not found: %s"%(', '.join(not_found)))
                
        return value
    

class StationNameField(forms.CharField):
    def clean(self, value):
        value = super(StationNameField, self).clean(value)
        
        if(value):
            if(Station.objects.filter(name=value).count() == 0):
                raise forms.ValidationError("Station '%s' not found"%(value))
        return value
    

class RegionNameField(forms.CharField):
    def clean(self, value):
        super(RegionNameField, self).clean(value)
        
        if(value):
            if(MapRegion.objects.filter(name=value).count() == 0):
                raise forms.ValidationError("Region '%s' not found"%(value))
            
        return value


class MultiRegionNameField(forms.CharField):
    def clean(self, value):
        super(MultiRegionNameField, self).clean(value)
        
        if(value):
            value_list = [v.strip() for v in value.split(',')]
            found_set = {n.lower() for n in MapRegion.objects.filter(name__in=value_list).values_list('name',flat=True)}
            
            not_found = list()
            
            for v in value_list:
                if(v.lower() not in found_set):
                    not_found.append(v)
            
            if(len(not_found) > 0):
                raise forms.ValidationError("Region(s) not found: %s"%(', '.join(not_found)))
                
        return value