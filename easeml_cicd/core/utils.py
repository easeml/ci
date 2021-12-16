import yaml
import os
import numpy as np
import subprocess
from subprocess import PIPE

import base64
from github import Github
from github import InputGitTreeElement

import json
import re


# This should be specific to the data format and type
# This one assumes one line per sample
# TODO cleanup
class DataManager:
    def __init__(self, client, project):
        self.base_path = "data_test/"
        self.base_data_file = "test.txt"
        self.client = client
        self.project = project

    # TODO Redundant in easemlCI move to lib
    def command_base(self, command):
        try:
            proc = subprocess.run(command, stdout=PIPE, stderr=PIPE, check=True)
            print(proc.stderr.decode("utf-8"))
            print(proc.stdout.decode("utf-8"))
            return proc.returncode
        except Exception as e:
            print(e.stderr.decode("utf-8"))
            print(e.stdout.decode("utf-8"))
            print(e)
            return e.returncode

    # TODO Redundant in easemlCI move to lib
    def decrypt_data(self, in_file=None):

        if not in_file:
            in_file = self.base_path + self.base_data_file + ".enc"

        fpath = os.getenv("HOME") + "/.easeml/"
        command = ["easeml_decrypt_data", fpath + 'keys/easeml_priv.asc', in_file]
        return self.command_base(command)

    # TODO Redundant in easemlCI move to lib
    def encrypt_data(self, in_file=None, out_file=None):
        if not in_file or not out_file:
            in_file = self.base_path + self.base_data_file
            out_file = self.base_path + self.base_data_file + ".enc"
        fpath = os.getenv("HOME") + "/.easeml/"
        command = ["easeml_encrypt_data", fpath + 'keys/easeml_pub.asc', in_file, out_file]
        return self.command_base(command)

    def push_changed_files2(self, file_list=None):
        command = ("git add " + " ".join(file_list)).split()
        self.command_base(command)

        commit_message = 'Released exhausted Dataset and Updated Test Dataset [skip ci]'
        command = ["git", "commit", "-m {}".format(commit_message)]
        self.command_base(command)

        app_name = 'easeMLbot'
        token = self.client.auth_token
        command = ("git push https://{}:{}@github.com/{}.git".format(app_name, token, self.project)).split()
        self.command_base(command)

    def push_changed_files(self, file_list=None):
        token = self.client.auth_token
        g = Github(login_or_token=token)
        repo_obj = g.get_repo(self.project)
        commit_message = 'Released exhausted Dataset and Updated Test Dataset [skip ci]'
        master_ref = repo_obj.get_git_ref('heads/master')
        master_sha = master_ref.object.sha
        base_tree = repo_obj.get_git_tree(master_sha)
        element_list = list()
        for entry in file_list:
            with open(entry, 'rb') as input_file:
                data = input_file.read()
            data = base64.b64encode(data)
            blob = repo_obj.create_git_blob(data.decode("utf-8"), "base64")
            element = InputGitTreeElement(path=entry, mode='100644', type='blob', sha=blob.sha)
            element_list.append(element)
        tree = repo_obj.create_git_tree(element_list, base_tree)
        parent = repo_obj.get_git_commit(master_sha)
        commit = repo_obj.create_git_commit(commit_message, tree, [parent])
        master_ref.edit(commit.sha)

    def extract_samples(self, N):
        print("Extracting Samples:", N)
        with open(self.base_path + self.base_data_file, "r") as f, open(self.base_path + self.base_data_file + ".use",
                                                                        "w") as out_use:
            try:
                for x in range(N):
                    line = next(f)
                    out_use.write(line)
            except:
                print("Not enough samples to continue")
                return False
        os.remove(self.base_path + self.base_data_file)
        os.rename(self.base_path + self.base_data_file + ".use", self.base_path + self.base_data_file)
        return True

    def release_samples(self, N):
        self.decrypt_data()
        with open(self.base_path + self.base_data_file) as f, open(self.base_path + self.base_data_file + ".used",
                                                                   "w") as out_use, open(
            self.base_path + self.base_data_file + ".unused", "w") as out_unused:
            for x in range(N):
                line = next(f)
                out_use.write(line)
            for line in f:
                out_unused.write(line)

        os.remove(self.base_path + self.base_data_file)
        os.rename(self.base_path + self.base_data_file + ".unused", self.base_path + self.base_data_file)
        self.encrypt_data()
        self.push_changed_files2(
            file_list=[self.base_path + self.base_data_file + '.enc', self.base_path + self.base_data_file + ".used"])
        # Commit decrypted data


class Clause:
    def __init__(self, delta, err):
        self.exp_const = delta
        self.err = err
        self.var_consts = []
        self.vars = []

    def __repr__(self):
        return "<Test err:{} exp_const:{} vars:{} var_consts:{}  b:%s>".format(self.err, self.exp_const, self.vars,
                                                                               self.var_consts)

    def __str__(self):
        return "err:{}, exp_const:{}, vars:{}, var_consts:{}".format(self.err, self.exp_const, self.vars, self.var_consts)


# Standard Hoeffding bound
def shb(rv, c, delta, eps):
    return -c ** 2.0 * rv ** 2.0 * np.log(delta) / (2.0 * (eps ** 2.0))


# Optimized bound with p equal
def shb_p(self, rv, c, delta, p, eps):
    frac = eps / p
    return -c ** 2.0 * rv ** 2.0 * np.log(delta) / (p * ((1 + frac) * np.log(1 + frac) - frac))


class SampleCalculator:
    def __init__(self, fname='.easeml.yml'):
        self.max_steps = None
        self.C = None
        self.email = None
        self.data_mode = None
        self.adaptivity = None
        self.mode = None
        self.reliability = None
        self.condition = None
        self.script = None
        self.config_name = fname

        self.all_clauses = []
        self.all_parsed_clauses = []

        with open(fname, 'r') as f:
            self.dprop = yaml.load(f, Loader=yaml.UnsafeLoader)
        self.parse_properties()

    def calculate_n(self):
        # TODO IMPORTANT RV should be provided by the user see below(?)
        print(f" Adaptivity type: {self.adaptivity}")
        print(f" Conditions Evaluated: {self.condition}")
        maxN = 0
        if self.adaptivity == 'none' or self.adaptivity == 'hybrid':
            for clause in self.all_clauses:

                eps = clause.err
                rv = len(clause.vars)
                delta = (1 - self.reliability) / (rv * len(self.all_clauses) * self.max_steps)
                allN = []
                for var, const in zip(clause.vars, clause.var_consts):
                    N = shb(rv, const, delta, eps)
                    allN.append(N)
                maxN = max(maxN, np.max(allN))
        elif self.adaptivity == 'full':
            for clause in self.all_clauses:

                eps = clause.err
                rv = len(clause.vars)
                delta = (1 - self.reliability) / (rv * len(self.all_clauses) * (2 ** self.max_steps))
                allN = []
                for var, const in zip(clause.vars, clause.var_consts):
                    N = shb(rv, const, delta, eps)
                    allN.append(N)
                maxN = max(maxN, np.max(allN))
        N = int(round(maxN + 0.5, 0))
        # print(N)
        return N

    def parse_properties(self):
        # print(self.dprop['ml'][6])
        self.script = self.dprop['ml'][0]['script']
        self.condition = self.dprop['ml'][1]['condition']
        self.condition = "".join(self.condition.split())
        self.parse_conditions(self.condition)
        self.reliability = self.dprop['ml'][2]['reliability']
        self.mode = self.dprop['ml'][3]['mode']
        self.adaptivity = self.dprop['ml'][4]['adaptivity']
        self.max_steps = self.dprop['ml'][5]['steps']
        self.data_mode = self.dprop['ml'][6]['data_mode']
        self.email = self.dprop['ml'][7]['email']

    def print_prop(self):
        print(self.dprop)

    def parse_conditions(self, condition):

        # Separate into clauses
        self.C = condition.split('/\\')

        self.all_clauses = []
        self.all_parsed_clauses = []
        # Separate error tolerance
        for clause in self.C:
            CE = clause.split('+/-')

            # Check the decomposition in exp over o,n,d and error
            assert len(CE) == 2
            # Check no reminding division operators
            assert '/' not in CE[0]
            assert '/' not in CE[1]

            # Using @ to replace > and < simultaneously
            assert '@' not in CE[0]

            assert 'n' in CE[0] or 'd' in CE[0] or 'o' in CE[0]
            self.all_parsed_clauses.append(CE[0])

            CE[0] = CE[0].replace('<', '@')
            CE[0] = CE[0].replace('>', '@')
            CE[0] = CE[0].split('@')

            # STRONG ASSUMPTIONS HERE, NEED TO BE CHECKED
            pClause = Clause(float(CE[0][-1]), float(CE[1]))
            del CE[0][-1]

            # TODO How to deal with d*n*o (is this necessary?)
            # TODO How to deal with + - constants (is this necessary?)
            # Using @ to replace reminding +/-/*(?)

            allVarCons = []
            for vars_and_cons in CE[0]:
                vars_and_cons = vars_and_cons.replace('*', '')
                vars_and_cons = vars_and_cons.replace('+', '@')
                vars_and_cons = vars_and_cons.replace('-', '@')
                vars_and_cons = vars_and_cons.split('@')
                allVarCons.extend(vars_and_cons)

            def check_all_vars(eval_vars_, vc_, pClause_):
                for var in eval_vars_:
                    if var in vc_:
                        pClause_.vars.append(var)
                        vc_ = vc_.replace(var, '')
                        if vc_ == '':
                            pClause_.var_consts.append(1.0)
                        else:
                            pClause_.var_consts.append(float(vc_))

            eval_vars = ['n', 'o', 'd']
            for vc in allVarCons:
                check_all_vars(eval_vars, vc, pClause)

            self.all_clauses.append(pClause)

            # TODO DOUBLE CHECK ALL THE LOGIC HERE
            # print(self.all_clauses)

    def passes_tests(self, last_acc=None, acc=None, d=None):
        full_pattern = re.compile('[0-9\+\*\-\.<>]|_')

        def re_replace(string):
            return re.sub(full_pattern, '', string)

        passed = True
        for CE in self.all_parsed_clauses:
            CE = CE.replace('o', str(last_acc))
            CE = CE.replace('n', str(acc))
            CE = CE.replace('d', str(d))

            SEMPTY = re_replace(CE)
            assert not SEMPTY

            result = eval(CE)
            # ASSUMES ONLY "AND" conditions are allowed
            if not result:
                passed = False
        return passed


class EaseMLCICDRunnerSampleManager:
    def __init__(self, name, client, app_id, inst_id, project, revision, branch, fname='.easeml.yml'):
        self.name = name
        self.client = client
        self.app_id = app_id
        self.inst_id = inst_id
        self.project = project
        self.revision = revision
        self.branch = branch

        self.N = 0

        self.current_step = 0
        self.last_acc = 0
        self.acc = 0
        self.pdifference = 0
        self.fail_type = 0
        self.releaseData = False

        self.msgHtml_rel = ''
        self.msgHtml_error = ''

        self.sample_calculator = SampleCalculator(fname)
        self.max_steps = self.sample_calculator.max_steps

    def check_file_changed(self, fname=None, lrevnum=1):
        command = ['git', 'diff', "--exit-code", '{}~{}'.format(self.revision, lrevnum), '{}'.format(self.revision),
                   fname]
        try:
            proc = subprocess.run(command, stdout=PIPE, stderr=PIPE, check=True)
            print("No change")
            print(proc.stderr.decode("utf-8"))
            print(proc.stdout.decode("utf-8"))
            return proc.returncode
        except Exception as e:
            if (e.returncode == 1):
                print("Changed")
                return e.returncode
            print('Error with command: "' + ' '.join(command) + '"')
            print(e.stderr.decode("utf-8"))
            print(e.stdout.decode("utf-8"))
            print(e)
            # exit(1)
            return e.returncode

    def get_current_and_total_run(self):
        max_rev = 50  # maximum distance from head to check
        for i in range(1, max_rev + 1):
            print("### Checking data from revision -{}".format(i))
            try:
                data = self.client.list_checks(self.revision + '~' + str(i))
            except Exception as e:
                print("Didn't find previous data, assuming initial commit")
                print(">>> No data found starting from zero")
                return 0, 0, 0, 0, 1

            for check_run in data['check_runs']:
                if check_run['name'] == self.name:
                    rawtext = check_run['output']['text']
                    if not rawtext:
                        continue

                    start = '<!--'
                    end = '-->'
                    print("$$ ", check_run)
                    result = re.search('%s(.*)%s' % (start, end), rawtext).group(1)
                    d = json.loads(result)
                    if 'acc' not in d.keys():
                        continue

                    if d['acc'] == 0:
                        acc = d['last_acc']
                    else:
                        acc = d['acc']

                    print("### Found data {}".format(d))
                    return d['current'], d['total'], acc, d['fail_type'], i
                    # Fail types 0 - No failure
                    # (negative) Not running model
                    #    docker -1 couldn't build the docker image
                    #    docker -2 couldn't run the docker container
                    #    not enough samples -3 
                    # (positive) Model ran but didn't pass the checks

        print(">>> No data found starting from zero")
        return 0, 0, 0, 0, 1

    def set_last_acc(self, acc):
        self.last_acc = acc

    def pre_check(self):

        data_manager = DataManager(self.client, self.project)
        data_manager.decrypt_data()

        optimization = False  # True

        self.N = 0
        if not optimization:
            # Extract N samples
            self.N = self.sample_calculator.calculate_n()
        else:
            ################################
            # Not implemented yet
            ################################

            # Calculate N_unlabeled
            # Run the model on N_unlabeled unlabeled samples
            # Evaluate the expression to calculate N
            # ...
            self.N = 0
            raise Exception  # Inform

        curr_step, total_steps, self.last_acc, self.fail_type, lrevnum = self.get_current_and_total_run()
        changed_yml = self.check_file_changed(".easeml.yml", lrevnum)
        changed_data = self.check_file_changed("data_test/test.txt.enc", lrevnum)
        print("token = ", self.client.auth_token)
        print(
            "Status: ChangedYML={} ChangedData={} curr_step={} total_steps={} ".format(changed_yml, changed_data,
                                                                                       curr_step,
                                                                                       total_steps))
        if (changed_yml or changed_data) and curr_step > 0 and total_steps > 1 and curr_step < total_steps:
            # #TODO (?) IGNORE CHANGES raise Exception("Error: Changes without finalizing all steps: ChangedYML={}
            #  ChangedData={} curr_step={} total_steps={} ".format(changed_yml,changed_data, curr_step,total_steps))
            self.msgHtml_error += "<br>Warning: Changes in the parameters without finalizing all steps <br> " \
                                  "<b>Restarting counters<b> "
            curr_step = 0
            total_steps = self.sample_calculator.max_steps

        if curr_step + 1 == total_steps:
            # This is the last step
            assert (total_steps == self.sample_calculator.max_steps)
            if self.fail_type >= 0:
                self.current_step = curr_step + 1
            else:
                self.current_step = curr_step
            self.releaseData = True
            if not data_manager.extract_samples(self.N):
                self.fail_type = -3
                self.msgHtml_error += "<br>Error: <b>Not enough samples to perform operation<b>"
                return False
            # TODO INFORM
        else:
            # This is an intermediate step
            if curr_step >= total_steps:
                curr_step = 0

            if total_steps:
                assert (total_steps == self.sample_calculator.max_steps)
            if self.fail_type >= 0:
                self.current_step = curr_step + 1
            else:
                self.current_step = curr_step
            if not data_manager.extract_samples(self.N):
                self.fail_type = -3
                self.msgHtml_error += "<br>Error: <b>Not enough samples to perform operation<b>"
                return False
            self.fail_type = 0
        return True

    def pos_check(self, acc):
        self.acc = acc

        passed = self.sample_calculator.passes_tests(self.last_acc, self.acc, self.pdifference)

        if not passed and self.fail_type >= 0:
            self.fail_type = 1

        data_manager = DataManager(self.client, self.project)

        # For workshop = False
        self.releaseData = False
        if self.releaseData:
            data_manager.release_samples(self.N)
            self.msgHtml_rel = "<br/>The exhausted data has been released"

        return True
