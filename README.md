# RadiSYS
RadiSYS is a software suite for 3d radiation shielding optimization and radiation effects analysis 
## Screenshot
![RadiSYS GUI](radsys.png?raw=true "RadiSYS")

## RadiSys Features  

* Graphical user interface
* Import 3d geometry directly  from CAD files (step, iges, stl etc)
* Material management 
* Construction of models with both GUI tools and python scripts 
* Earth radiation belt models AE8, AP8 integrated
* Radiation analysis with different engines supported
  * Geant4
  * Built-in numerical simulation modules, suitable for x-rays, protons and heavy ions
* Built-in modules for analysis of 

  *  Total ionizing dose
  *  Dose distribution 
  *  Displacement damage
  *  Single event rate



# Installation


Install cq-editor using conda


activate conda

conda activate base

create a file radsys:

```python
 

import re
import sys

from cq_editor.__main__ import main
if __name__ == '__main__':
 sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
sys.exit(main())[readonly] 11 lines, 226 bytes
```

# ToDo list:

-- replace the meshing code with the version written in c++

how to run:
/opt/conda/bin/radsy
