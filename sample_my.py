# -*- coding: utf-8 -*-
# sample_C204.py

import random
from gavrptw.core2 import gaVRPTW2


def main():
    random.seed(64)
    instName = 'my'
    unitCost = 8.0
    initCost = 100.0
    waitCost = 1.0
    delayCost = 1.5
    indSize = 20
    popSize = 200
    cxPb = 0.85
    mutPb = 0.02
    NGen = 30
    exportCSV = False

    gaVRPTW2(
        instName=instName,
        unitCost=unitCost,
        initCost=initCost,
        waitCost=waitCost,
        delayCost=delayCost,
        indSize=indSize,
        popSize=popSize,
        cxPb=cxPb,
        mutPb=mutPb,
        NGen=NGen,
        exportCSV=False
    )


if __name__ == '__main__':
    main()