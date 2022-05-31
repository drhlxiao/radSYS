# radSYS
radiation analysis software
# Installation

Follow the steps at https://github.com/CadQuery/CQ-editor
Install cq-editor using conda

Then find cq-editor source code under cq_editor folder, and then replace 
the source code with the source code here.
/opt/conda/lib/python3.9/site-packages/cq_editor

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
