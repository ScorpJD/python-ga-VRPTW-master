# -*- coding: utf-8 -*-

import os
import random
from json import load
from csv import DictWriter
from deap import base, creator, tools
from . import BASE_DIR
#from utils import makeDirsForFile, exist

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
            note that 100 represents the dump site
            lastToDump: distance from previous job to the dump
            dumpToCurrent: distance from dump to depot
            """
            lastToDump = instance['distance_matrix'][lastCustomerID][100]
            dumpToCurrent= instance['distance_matrix'][100][customerID]
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
    #note that 100  represents the dump site
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
                subRouteStr = subRouteStr + ' (100)' + ' - ' + str(customerID)
                vehicleLoad = demand
                routeStr = routeStr + ' (100)' + ' - ' + str(customerID)
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
    #note that 100 is hardcoded as the dump site
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
                previousToDump = instance['distance_matrix'][lastCustomerID][100]
                dumpToCurrent = instance['distance_matrix'][100][customerID]
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
    return fitness,


def cxPartialyMatched(ind1, ind2):
    size = min(len(ind1), len(ind2))
    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
    temp1 = ind1[cxpoint1:cxpoint2+1] + ind2
    temp2 = ind1[cxpoint1:cxpoint2+1] + ind1
    ind1 = []
    for x in temp1:
        if x not in ind1:
            ind1.append(x)
    ind2 = []
    for x in temp2:
        if x not in ind2:
            ind2.append(x)
    return ind1, ind2


def mutInverseIndexes(individual):
    start, stop = sorted(random.sample(range(len(individual)), 2))
    individual = individual[:start] + individual[stop:start-1:-1] + individual[stop+1:]
    return individual,


def gaVRPTW2(instName, unitCost, initCost, waitCost, delayCost, indSize, popSize, cxPb, mutPb, NGen, exportCSV=False,
            customizeData=False):
    if customizeData:
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_customize')
    else:
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json')
    jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
    with open(jsonFile) as f:
        instance = load(f)
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    # Attribute generator
    toolbox.register('indexes', random.sample, range(1, indSize + 1), indSize)
    # Structure initializers
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indexes)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    # Operator registering
    toolbox.register('evaluate', evalVRPTW2, instance=instance, unitCost=unitCost, initCost=initCost, waitCost=waitCost,
                     delayCost=delayCost)
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', cxPartialyMatched)
    toolbox.register('mutate', mutInverseIndexes)
    pop = toolbox.population(n=popSize)
    # Results holders for exporting results to CSV file
    csvData = []
    print('Start of evolution')
    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    print('  Evaluated %d individuals' % len(pop))
    # Begin the evolution
    for g in range(NGen):
        print('-- Generation %d --' % g)
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxPb:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        for mutant in offspring:
            if random.random() < mutPb:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness
        invalidInd = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
        print('  Evaluated %d individuals' % len(invalidInd))
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x * x for x in fits)
        std = abs(sum2 / length - mean ** 2) ** 0.5
        print('  Min %s' % min(fits))
        print('  Max %s' % max(fits))
        print('Avg %s' % mean)
        print('  Std %s' % std)
        # Write data to holders for exporting results to CSV file
        if exportCSV:
            csvRow = {
                'generation': g,
                'evaluated_individuals': len(invalidInd),
                'min_fitness': min(fits),
                'max_fitness': max(fits),
                'avg_fitness': mean,
                'std_fitness': std,
            }
            csvData.append(csvRow)
    print('-- End of (successful) evolution --')
    bestInd = tools.selBest(pop, 1)[0]
    print('Best individual: %s' % bestInd)
    print('Fitness: %s' % bestInd.fitness.values[0])
    printRoute2(ind2route2(bestInd, instance), instance)
    print('Total cost: %s' % (1 / bestInd.fitness.values[0]))
    if exportCSV:
        csvFilename = '%s_uC%s_iC%s_wC%s_dC%s_iS%s_pS%s_cP%s_mP%s_nG%s.csv' % (instName, unitCost, initCost, waitCost, delayCost, indSize, popSize, cxPb, mutPb, NGen)
        csvPathname = os.path.join(BASE_DIR, 'results', csvFilename)
        print( 'Write to file: %s' % csvPathname)
        makeDirsForFile(pathname=csvPathname)
        if not exist(pathname=csvPathname, overwrite=True):
            with open(csvPathname, 'w') as f:
                fieldnames = ['generation', 'evaluated_individuals', 'min_fitness', 'max_fitness', 'avg_fitness', 'std_fitness']
                writer = DictWriter(f, fieldnames=fieldnames, dialect='excel')
                writer.writeheader()
                for csvRow in csvData:
                    writer.writerow(csvRow)


