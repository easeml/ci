# Usage

The Ease.ml/CI can be used as a stand-alone library or deployed as a CI&CD service.

# Ease.ml/CI as a library

install the library
```commandline
pip install git+https://github.com/easeml/ci
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

# Ease.ml/CI on buildbot

Ease.ml/CI can be deployed as a service interfacing with a github repository, 
deploying models as containers with docker, managing the encrypted datasets and notifying users by email 
the results of their ML CI&CD pipeline. For this buildbot is used as a base and Easeml/CI&CD is used as a plugin 

# Prerequisites
- Buildbot
- Docker (ML model are run as docker containers)
- A public ip or domain name and access configured to the required port, e.g. http://ec2-18-219-109-220.us-east-2.compute.amazonaws.com:8010


## Overview

1. Provision a server or cluster with a publicly reachable ip/domain name and port,e.g. http://ec2-18-219-109-220.us-east-2.compute.amazonaws.com:8010 
2. Install Docker and enable execution without sudo, e.g. https://docs.docker.com/engine/install/ubuntu/, https://docs.docker.com/engine/install/linux-postinstall/
3. [Create buildbot master/worker](https://docs.buildbot.net/current/tutorial/firstrun.html#creating-a-master)
4. Install this package on the worker and master, i.e. `pip install git+https://github.com/easeml/cicd`, on their respective virtual environments
5. Customize and Set the master configuration, e.g. [master.cfg](example_master_cfg/master.cfg)
6. Register a GitHub app
   - Generate the GitHub app's `service_private_key.pem`
   - Register the webhook's location, e.g. http://ec2-18-222-118-176.us-east-2.compute.amazonaws.com:8010/change_hook/github
   - Enable control over check runs
7. Structure and configure your GitHub repository to use the GitHub app, e.g. https://github.com/leaguilar/VLDB2019
8. Set keys
   - GitHub access keys in `$HOME/.easeml/keys/service_private_key.pem`, (this is the key required for the GitHub app to access the repository)
   - Data decryption and encryption keys:
     - `$HOME/.easeml/keys/easeml_priv.asc`
     - `$HOME/.easeml/keys/easeml_pub.asc` 
10. Run buildbot

## Citations

```bibtex
@inproceedings{renggli2019mlsys,
 author = {Cedric Renggli and Bojan Karlaš and Bolin Ding and Feng Liu and Kevin Schawinski and Wentao Wu and Ce Zhang},
 booktitle = {Proceedings of Machine Learning and Systems},
 title = {Continuous Integration of Machine Learning Models with ease.ml/ci: A Rigorous Yet Practical Treatment},
 year = {2019}
}

@inproceedings{karlas2020sigkdd,
 author = {Bojan Karlaš and Matteo Interlandi and Cedric Renggli and Wentao Wu and Ce Zhang and Deepak Mukunthu Iyappan Babu and Jordan Edwards and Chris Lauren and Andy Xu and Markus Weimer},
 booktitle = {Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining},
 title = {Building continuous integration services for machine learning},
 year = {2020}
}
```
