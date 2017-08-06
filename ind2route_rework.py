# -*- coding: utf-8 -*-

import os
import random
from json import load
from csv import DictWriter
from deap import base, creator, tools
BASE_DIR = '/home/alexbouril/py-ga-VRPTW-master'
#from utils import makeDirsForFile, exist

instName = 'my'
jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
with open(jsonFile) as f:
    inst = load(f)
ind = [x for x in range(1, 101)]


def printRoute(route, merge=False):
    routeStr = '0'
    subRouteCount = 0
    for subRoute in route:
        subRouteCount += 1
        subRouteStr = '0'
        for customerID in subRoute:
            subRouteStr = subRouteStr + ' - ' + str(customerID)
            routeStr = routeStr + ' - ' + str(customerID)
        subRouteStr = subRouteStr + ' - 0'
        if not merge:
            print( '  Vehicle %d\'s route: %s' % (subRouteCount, subRouteStr))
        routeStr = routeStr + ' - 0'
    if merge:
        print( routeStr)
    return


def ind2route(individual, instance):
    route = []
    vehicleCapacity = instance['vehicle_capacity']
    deportDueTime =  instance['deport']['due_time']
    # Initialize a sub-route
    subRoute = []
    vehicleLoad = 0
    elapsedTime = 0
    lastCustomerID = 0
    for customerID in individual:
        # Update vehicle load
        demand = instance['customer_%d' % customerID]['demand']
        updatedVehicleLoad = vehicleLoad + demand
        # Update elapsed time
        serviceTime = instance['customer_%d' % customerID]['service_time']
        returnTime = instance['distance_matrix'][customerID][0]
        updatedElapsedTime = elapsedTime + instance['distance_matrix'][lastCustomerID][customerID] + serviceTime + returnTime
        # Validate vehicle load and elapsed time
        if (updatedVehicleLoad <= vehicleCapacity) and (updatedElapsedTime <= deportDueTime):
            # Add to current sub-route
            subRoute.append(customerID)
            vehicleLoad = updatedVehicleLoad
            elapsedTime = updatedElapsedTime - returnTime
        else:
            # Save current sub-route
            route.append(subRoute)
            # Initialize a new sub-route and add to it
            subRoute = [customerID]
            vehicleLoad = demand
            elapsedTime = instance['distance_matrix'][0][customerID] + serviceTime
        # Update last customer ID
        lastCustomerID = customerID
    if subRoute != []:
        # Save current sub-route before return if not empty
        route.append(subRoute)
    return route


def evalVRPTW(individual, instance, unitCost=1.0, initCost=0, waitCost=0, delayCost=0):
    totalCost = 0
    route = ind2route(individual, instance)
    totalCost = 0
    for subRoute in route:
        subRouteTimeCost = 0
        subRouteDistance = 0
        elapsedTime = 0
        lastCustomerID = 0
        for customerID in subRoute:
            # Calculate section distance
            distance = instance['distance_matrix'][lastCustomerID][customerID]
            # Update sub-route distance
            subRouteDistance = subRouteDistance + distance
            # Calculate time cost
            arrivalTime = elapsedTime + distance
            timeCost = waitCost * max(instance['customer_%d' % customerID]['ready_time'] - arrivalTime, 0) + delayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)
            # Update sub-route time cost
            subRouteTimeCost = subRouteTimeCost + timeCost
            # Update elapsed time
            elapsedTime = arrivalTime + instance['customer_%d' % customerID]['service_time']
            # Update last customer ID
            lastCustomerID = customerID
        # Calculate transport cost
        subRouteDistance = subRouteDistance + instance['distance_matrix'][lastCustomerID][0]
        subRouteTranCost = initCost + unitCost * subRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTimeCost + subRouteTranCost
        # Update total cost
        totalCost = totalCost + subRouteCost
    fitness = 1.0 / totalCost
    return fitness,


def ind2route2(individual, instance):
    route = [] #ok
    vehicleCapacity = instance['vehicle_capacity']
    deportDueTime = instance['deport']['due_time']
    dumpTime = instance['dump_time']
    # Initialize a sub-route
    subRoute = []
    vehicleLoad = 0
    elapsedTime = 0
    lastCustomerID = 0
    for customerID in individual:
        # Update vehicle load
        demand = instance['customer_%d' % customerID]['demand']
        updatedVehicleLoad = vehicleLoad + demand
        # Update elapsed time
        serviceTime = instance['customer_%d' % customerID]['service_time']
        returnTime = instance['distance_matrix'][customerID][0]
        updatedElapsedTime = elapsedTime + instance['distance_matrix'][lastCustomerID][customerID] + serviceTime + returnTime
        # Validate vehicle load and elapsed time
        if (updatedVehicleLoad <= vehicleCapacity) and (updatedElapsedTime <= deportDueTime):
            # Add to current sub-route
            subRoute.append(customerID)
            vehicleLoad = updatedVehicleLoad
            elapsedTime = updatedElapsedTime - returnTime
        elif (updatedVehicleLoad >=vehicleCapacity) and (updatedElapsedTime <= deportDueTime):#ADDED
            """  
            Step 1: Go to the dump!
            reset everything to the job before the current job and go the dump instead of the current job
            note that -1 represents the dump site
            lastToDump: distance from previous job to the dump
            dumpToCurrent: distance from dump to depot
            """
            lastToDump = instance['distance_matrix'][lastCustomerID][-1]
            dumpToCurrent= instance['distance_matrix'][-1][customerID]
            #print("hello,  the current customer is "+str(customerID)+", lastToDump = "+str(lastToDump)+", dumpToCurrent = "+str(dumpToCurrent))
            updatedElapsedTime = elapsedTime + lastToDump + dumpTime + dumpToCurrent + serviceTime + returnTime
            """
            Step 2: check if we can do the current job!
                the job needs to be completed before deportDueTime
            """
            if(updatedElapsedTime <= deportDueTime):
                """
                if the current job can be completed before deportDueTime, then lets add it to the subroute
                """
                subRoute.append(customerID)
                vehicleLoad = updatedVehicleLoad
                elapsedTime = updatedElapsedTime - returnTime

            else:#(updatedElapsedTime > deportDueTime):
                """
                if the current job can NOT be completed before deportDueTime, then well assume that the
                truck went to the dump and then back to the depot.  If it's a little late back to the depot, oh well.
                Now, let's...
                1. end the current subroute 
                2. add the current job to a new subroute
                """
                # Save current sub-route
                route.append(subRoute)
                # Initialize a new sub-route and add to it
                subRoute = [customerID]
                vehicleLoad = demand
                elapsedTime = instance['distance_matrix'][0][customerID] + serviceTime
        else: #(updatedElapsedTime > deportDueTime)
            #Save current sub-route
            route.append(subRoute)
            # Initialize a new sub-route and add to it
            subRoute = [customerID]
            vehicleLoad = demand
            elapsedTime = instance['distance_matrix'][0][customerID] + serviceTime
        # Update last customer ID
        lastCustomerID = customerID
    if subRoute != []:
        # Save current sub-route before return if not empty
        route.append(subRoute)
    return route

def printRoute2(route, instance, merge=False):
    #note that -1 represents the dump site
    vehicleCapacity = instance['vehicle_capacity']
    routeStr = '0'
    subRouteCount = 0
    vehicleLoad = 0
    for subRoute in route:
        vehicleLoad = 0
        subRouteCount += 1
        subRouteStr = '0'
        for customerID in subRoute:
            demand = instance['customer_%d' % customerID]['demand']
            updatedVehicleLoad = vehicleLoad + demand
            if(updatedVehicleLoad>vehicleCapacity):
                subRouteStr = subRouteStr + ' (-1)' + ' - ' + str(customerID)
                vehicleLoad = demand
                routeStr = routeStr + ' (-1)' + ' - ' + str(customerID)
            else:
                subRouteStr = subRouteStr + ' - ' + str(customerID)
                routeStr = routeStr + ' - ' + str(customerID)
                vehicleLoad = updatedVehicleLoad
        subRouteStr = subRouteStr + ' - 0'
        if not merge:
            print ('  Vehicle %d\'s route: %s' % (subRouteCount, subRouteStr))
        routeStr = routeStr + ' - 0'
    if merge:
        print (routeStr)
    return


def evalVRPTW2(individual, instance, unitCost=1.0, initCost=0, waitCost=0, delayCost=0):
    totalCost = 0
    vehicleCapacity = instance['vehicle_capacity']
    route = ind2route2(individual, instance)
    totalCost = 0
    for subRoute in route:
        subRouteTimeCost = 0
        subRouteDistance = 0
        elapsedTime = 0
        lastCustomerID = 0
        vehicleLoad = 0
        for customerID in subRoute:
            demand = instance['customer_%d' % customerID]['demand']
            updatedVehicleLoad = vehicleLoad + demand
            if (updatedVehicleLoad > vehicleCapacity):
                #we have to go the dump before servicing the current customerID
                dummy = 1
                previousToDump = instance['distance_matrix'][lastCustomerID][-1]
                dumpToCurrent = instance['distance_matrix'][-1][customerID]
                distance = previousToDump + dumpToCurrent
                subRouteDistance = subRouteDistance + distance
                arrivalTime = elapsedTime + distance + instance['dump_time']
                timeCost = waitCost * max(instance['customer_%d' % customerID]['ready_time'] - arrivalTime, 0) + delayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)
                subRouteTimeCost = subRouteTimeCost + timeCost
                elapsedTime = arrivalTime + instance['customer_%d' % customerID]['service_time']
                lastCustomerID = customerID
                vehicleLoad = demand
            else:
                #if we did not have to go to the dump before servicing the current customerID
                dummy = 2
                distance = instance['distance_matrix'][lastCustomerID][customerID]
                subRouteDistance = subRouteDistance + distance
                arrivalTime = elapsedTime + distance
                timeCost = waitCost * max(instance['customer_%d' % customerID]['ready_time'] - arrivalTime, 0) + delayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)
                subRouteTimeCost = subRouteTimeCost + timeCost
                elapsedTime = arrivalTime + instance['customer_%d' % customerID]['service_time']
                lastCustomerID = customerID
                vehicleLoad = updatedVehicleLoad

            """            
            # Calculate section distance
            distance = instance['distance_matrix'][lastCustomerID][customerID]
            # Update sub-route distance
            subRouteDistance = subRouteDistance + distance
            # Calculate time cost
            arrivalTime = elapsedTime + distance
            timeCost = waitCost * max(instance['customer_%d' % customerID]['ready_time'] - arrivalTime, 0) + delayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)
            # Update sub-route time cost
            subRouteTimeCost = subRouteTimeCost + timeCost
            # Update elapsed time
            elapsedTime = arrivalTime + instance['customer_%d' % customerID]['service_time']
            # Update last customer ID
            lastCustomerID = customerID
            """
        # Calculate transport cost
        subRouteDistance = subRouteDistance + instance['distance_matrix'][lastCustomerID][0]
        subRouteTranCost = initCost + unitCost * subRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTimeCost + subRouteTranCost
        # Update total cost
        totalCost = totalCost + subRouteCost
    fitness = 1.0 / totalCost
    return fitness


#------------------------------------------------------------------------------
rou = ind2route(ind, inst)
print(rou)
printRoute(rou)
print(evalVRPTW(ind, inst, 1, 2, 1, 1))
print("#######################################################################")
rou2 = ind2route2(ind, inst)
print(rou2)
printRoute2(rou2, inst)
print(evalVRPTW2(ind, inst, 1, 2, 1, 1))

