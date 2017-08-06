import random

def cxPartialyMatched(ind1, ind2):
    size = min(len(ind1), len(ind2))
    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
    print(cxpoint1)
    print(cxpoint2)
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

x = [7, 6, 1,2,3,4,5,8,9,10]
y = [4,3,10,9,8,6,7,2,1,5]
print(cxPartialyMatched(x,y))
print(x[1:3] + y)
