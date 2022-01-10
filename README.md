# Ease.ml/ci

![GitHub](https://img.shields.io/github/license/easeml/ci)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)

Ease.ml/ci is a library to support continuous testing and integration of machine learning models with statistical guarantees. It can be used as a stand-alone library or deployed as a CI&CD service.

### Why another CI/CD system

There exist many different CI/CD tools for classical software development (e.g., [Jenkins](https://www.jenkins.io/)). However, using them out-of-the box for continously testing machine learning models can lead to failures in production. The reason is firstly, that when testing an ML model with a fixed test set, one has to take into account the inherent randomness of ML. Secondly, when using the same test set multiple times, one has to make sure to not overfitt to it, even when only evaluating and having access to the outcome of test conditions. More details about the inherent challenges on how to test ML models can be found in our [blog post](https://ds3lab.ghost.io/ci/).

### Sample size estimator

The core component of ease.ml/ci is a sample size estimator. Given a test condition, the number of commits one itends to use the same test set, and the confidence bounds one has to guarantee, the sample size estimator will output the minimum number of samples required to satisfy these requirements.
This estimator can then be uses in a standalone fashion (i.e., as a library), or integreated in a CI/CD workflow (i.e., using GitHub action or buildbot). The later requires to also include functionalities on how to actually calculate quantities supported in the test conditions (like accuracy or difference in predictions of models), and how to notify the user to provide a new test set and replace the existing one in the system.

## Ease.ml/ci as a library

Install the library
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

## Ease.ml/ci as a GitHub action
Ease.ml/ci can be used within a GitHub Action.
### Prerequisites
- Ease.ML/ci repository structure
### Overview
1. Generate dataset encryption and decryption keys, by running the command.
```commandline
easeml_create_key
```
2. Base64 encode the keys and add them as a repository secret.
```commandline
cat easeml_pub.asc | base64 -w 0
```
```commandline
cat easeml_priv.asc | base64 -w 0
```
3. Store the keys as GitHub Secrets under the names `B64_EASEML_PUB` and `B64_EASEML_PRIV`.
4. Create a GitHub Action yaml under `.github/workflows/`, e.g. [easemlci.yml](example_github_action/easemlci.yml)

An example repository using Ease.ml/ci as a GitHub Action can be found here: https://github.com/leaguilar/ci_action

## Ease.ml/ci on buildbot

For heavier workloads Ease.ml/ci can be deployed as a service interfacing with a github repository, 
deploying models as containers with docker, managing the encrypted datasets and notifying users by email 
the results of their ML CI&CD pipeline. For this buildbot is used as a base and Easeml/CI&CD is used as a plugin 

### Prerequisites
- Ease.ML/ci repository structure
- Buildbot
- Docker (ML model are run as docker containers)
- A public ip or domain name and access configured to the required port, e.g. http://ec2-18-219-109-220.us-east-2.compute.amazonaws.com:8010


### Overview

A playlist with a detailed example of setting up the service can be found [here](https://www.youtube.com/playlist?list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m) and the videos are linked throughout the overview

1. Provision a server or cluster with a publicly reachable ip/domain name and port,e.g. http://ec2-18-219-109-220.us-east-2.compute.amazonaws.com:8010
   - **Videos:** [0.1](https://www.youtube.com/watch?v=iwB4yar9m_o&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=1), [0.2](https://www.youtube.com/watch?v=KSWz4-YUJ3I&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=2)
2. Install Docker and enable execution without sudo, e.g. https://docs.docker.com/engine/install/ubuntu/, https://docs.docker.com/engine/install/linux-postinstall/
   - **Videos:** [0.3](https://www.youtube.com/watch?v=FDOnDFG-XUo&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=3), [0.4](https://www.youtube.com/watch?v=kow6YYae6HI&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=4)
3. [Create buildbot master/worker](https://docs.buildbot.net/current/tutorial/firstrun.html#creating-a-master)
   - Install this package on the worker and master, i.e. `pip install git+https://github.com/easeml/cicd`, on their respective virtual environments
   - Customize and Set the master configuration, e.g. [master.cfg](example_master_cfg/master.cfg)
   - **Videos:** [1.1](https://www.youtube.com/watch?v=Nz688aDBE5A&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=5), [1.2](https://www.youtube.com/watch?v=tX1UjOnPGw4&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=6), [1.3](https://www.youtube.com/watch?v=ujg3oIEgBgs&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=7), [1.4](https://www.youtube.com/watch?v=4k-NPsWwFX8&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=8), [1.5](https://www.youtube.com/watch?v=HeKyNSi3UAE&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=9)
4. Register a GitHub app and link it to a repository
   - Generate the GitHub app's `service_private_key.pem`
   - Register the webhook's location, e.g. http://ec2-18-222-118-176.us-east-2.compute.amazonaws.com:8010/change_hook/github
   - Enable control over check runs
   - Structure and configure your GitHub repository to use the GitHub app, e.g. https://github.com/leaguilar/VLDB2019
   - **Videos:** [2.1](https://www.youtube.com/watch?v=ZFjZf2QCFpc&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=10), [2.2](https://www.youtube.com/watch?v=7x5TrE79ins&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=11) 
6. Set keys
   - GitHub access keys in `$HOME/.easeml/keys/service_private_key.pem`, (this is the key required for the GitHub app to access the repository)
   - Data decryption and encryption keys:
     - `$HOME/.easeml/keys/easeml_priv.asc`
     - `$HOME/.easeml/keys/easeml_pub.asc`
   - **Videos:** [3.1](https://www.youtube.com/watch?v=0r7qofwYG38&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=12)  
7. Run the service
   - **Videos:** [4.1](https://www.youtube.com/watch?v=eEYc_0nBysA&list=PLxziVpXjhWYhHFyM3qPRbJPpHTnn2TI0m&index=13)

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

@inproceedings{aguilar2021ease,
  title={Ease. ML: A Lifecycle Management System for Machine Learning},
  author={Aguilar Melgar, Leonel and Dao, David and Gan, Shaoduo and G{\"u}rel, Nezihe M and Hollenstein, Nora and Jiang, Jiawei and Karla{\v{s}}, Bojan and Lemmin, Thomas and Li, Tian and Li, Yang and others},
  booktitle={11th Annual Conference on Innovative Data Systems Research (CIDR 2021)(virtual)},
  year={2021},
  organization={CIDR}
}
```
