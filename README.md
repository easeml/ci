# Usage

The Ease.ml CI&CD can be used as a stand-alone library or deployed as a CI&CD service.

# Ease.ml CI&CD as a library

install the library
```commandline
pip install git+https://github.com/easeml/cicd
```

within the python kernel with the installed library
```python
from easeml_cicd.core.utils import SampleCalculator
# location of ci&cd config file
config_path=".easeml.yml"
# initialize the sample calculator with the config file
sc=SampleCalculator(config_path)
# Cacluate the number of samples needed
N = sc.calculate_n()
```
A jupyter notebook showcasing this can be found [here](notebooks/SimpleSampleCalculation.ipynb)

# Ease.ml CI&CD on buildbot

Ease.ml/CI&CD can be deployed as a service interfacing with a github repository, 
deploying models as containers with docker, managing the encrypted datasets and notifying users by email 
the results of their ML CI&CD pipeline. For this buildbot is used as a base and Easeml/CI&CD is used as a plugin 

# Prerequisites
- Buildbot
- Docker (Docker containers running the ML models are spawned as part of the CI&CD process)

## Overview

1. [Create buildbot master/worker](https://docs.buildbot.net/current/tutorial/firstrun.html#creating-a-master)
2. Install this package
3. Set the master configuration, e.g. [master.cfg](example_master_cfg/master.cfg)
4. Run buildbot
5. Configure your github repository to use buildbot's endpoint for CI&CD
