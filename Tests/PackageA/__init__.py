from PackageA.NestedPackage.EvenMore.ModuleC import NESTED
import PackageA.NestedPackage.EvenMore.ModuleC as MC

import NestedPackage as RelImport
from NestedPackage.EvenMore import ModuleC as RelMC

class SneakyClass:
    pass
    
def SneakyFunction():
    pass
    
SneakyConstant = 42
