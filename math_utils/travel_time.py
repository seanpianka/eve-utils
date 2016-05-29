
import math
import random

import numpy
from scipy import integrate
from scipy import optimize

au = 149597870700.0

def compute_approach_time(travel_distance, max_speed, align_time):
    
    inv_x = 1 / (align_time * 0.72135)
    
    #return the velocity at time t
    def velocity(t):
        return max_speed * (1 - math.exp(-t * inv_x))
    
    #return the position at time t
    #this is really hard to calculate directly so we'll just integrate velocity from 0
    def remaining_distance(t):
        (result, error) = integrate.quad(velocity, 0, t)
        return result - travel_distance
    
    return optimize.brentq(remaining_distance, -1, travel_distance / max_speed * 2, xtol=0.01)

def compute_warp_time(warp_distance, max_speed, max_warp_speed):
    
    max_warp_speed_au = max_warp_speed/au
    
    accel_constant = max_warp_speed_au
    decel_constant = min(max_warp_speed_au/3, 2)

    #compute the speed we'll need to accelerate up to if we ignore the max warp speed
    speed = accel_constant * decel_constant * warp_distance / (accel_constant + decel_constant)
    
    #compute the speed at which we exit warp - described by ccp masterplan here:
    #https://forums.eveonline.com/default.aspx?g=posts&m=3902148#post3902148
    exit_velocity = min(100, 0.5 * max_speed)

    if(speed > max_warp_speed):
        #we hit max warp speed, so we have to break this into 2 parts
        
        #the first part is the time taken to accelerate/decelerate from max warp speed
        acceleration_distance = (accel_constant + decel_constant) * max_warp_speed / (accel_constant * decel_constant)
        
        accel_time = -math.log((accel_constant + decel_constant)/(acceleration_distance * decel_constant))/accel_constant
        decel_time = -math.log((accel_constant + decel_constant)/(acceleration_distance * accel_constant))/decel_constant
        
        #the second part is the flat warp speed
        flat_distance = warp_distance - acceleration_distance
        flat_time = flat_distance / max_warp_speed

    else:
        accel_time = -math.log((accel_constant + decel_constant)/(warp_distance * decel_constant))/accel_constant
        decel_time = -math.log((accel_constant + decel_constant)/(warp_distance * accel_constant))/decel_constant
        flat_time = 0
        
    #the ship doesn't come out of warp at max speed or 1/ms, it comes out at the exit_velocity
    #instead of incorporating that into the formulas above, just subtract the deceleration time from exit_velocity to 1
    return flat_time + accel_time + decel_time - math.log(exit_velocity/decel_constant)/decel_constant
