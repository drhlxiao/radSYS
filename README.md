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

 
  3 # -*- coding: utf-8 -*-
  4 import re
  5 import sys
  6 
  7 from cq_editor.__main__ import main
  8 
  9 if __name__ == '__main__':
 10     sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
 11     sys.exit(main())[readonly] 11 lines, 226 bytes


# ToDo list:

-- replace the meshing code with the version written in c++

how to run:
/opt/conda/bin/radsy
