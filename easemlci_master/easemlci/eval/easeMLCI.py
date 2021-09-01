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

#This should be specific to the data format and type
#This one assumes one line per sample
#TODO cleanup
class DataManager:
    def __init__(self,client,project):
        self.base_path="data_test/"
        self.base_data_file="test.txt"
        self.client=client
        self.project=project

    #TODO Redundant in easemlCI move to lib
    def CommandBase(self,command):
        try:
            proc = subprocess.run(command,stdout=PIPE, stderr=PIPE, check=True)
            print(proc.stderr.decode("utf-8"))
            print(proc.stdout.decode("utf-8"))
            return proc.returncode
        except Exception as e:
            print(e.stderr.decode("utf-8"))
            print(e.stdout.decode("utf-8"))
            print(e)
            return e.returncode
                
    #TODO Redundant in easemlCI move to lib
    def decryptData(self,in_file=None):
    
        if not in_file:
            in_file=self.base_path+self.base_data_file+".enc"
    
        fpath=os.getenv("HOME")+"/.easeml/"
        command=["easemlDecryptData",fpath+'keys/easeml_priv.asc',in_file]
        return self.CommandBase(command)
    
    #TODO Redundant in easemlCI move to lib
    def encryptData(self,in_file=None,out_file=None):
        if not in_file or not out_path:
            in_file=self.base_path+self.base_data_file
            out_file=self.base_path+self.base_data_file+".enc"
        fpath=os.getenv("HOME")+"/.easeml/"
        command=["easemlEncryptData",fpath+'keys/easeml_pub.asc',in_file,out_file]
        return self.CommandBase(command)
    
    def PushChangedFiles2(self,file_list = None):
        command=("git add "+" ".join(file_list)).split()
        self.CommandBase(command)
        
        commit_message = 'Released exhausted Dataset and Updated Test Dataset [skip ci]'
        command=["git","commit", "-m {}".format(commit_message)]
        self.CommandBase(command)
        
        app_name='easeMLbot'
        token = self.client.auth_token
        command=("git push https://{}:{}@github.com/{}.git".format(app_name,token,self.project)).split()
        self.CommandBase(command)

    def PushChangedFiles(self,file_list = None):
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
                
    def ExtractSamples(self,N):
        print("Extracting Samples:",N)
        with open(self.base_path+self.base_data_file,"r") as f, open(self.base_path+self.base_data_file+".use", "w") as out_use:
            try:
                for x in range(N):
                    line=next(f)
                    out_use.write(line)
            except:
                print("Not enough samples to continue")
                return False
        os.remove(self.base_path+self.base_data_file)
        os.rename(self.base_path+self.base_data_file+".use",self.base_path+self.base_data_file)
        return True
        
    def ReleaseSamples(self,N):
        self.decryptData()
        with open(self.base_path+self.base_data_file) as f, open(self.base_path+self.base_data_file+".used", "w") as out_use, open(self.base_path+self.base_data_file+".unused", "w") as out_unused:
            for x in range(N):
                line=next(f)
                out_use.write(line)
            for line in f:
                out_unused.write(line)
            
        os.remove(self.base_path+self.base_data_file)
        os.rename(self.base_path+self.base_data_file+".unused",self.base_path+self.base_data_file)
        self.encryptData()
        self.PushChangedFiles2(file_list=[self.base_path+self.base_data_file+'.enc',self.base_path+self.base_data_file+".used"])
        ##Commit decrypted data
            

class Clause:
    def __init__(self,delta,err):
        self.expConst=delta
        self.err=err
        self.varConsts=[]
        self.vars=[]
    def __repr__(self):
        return "<Test err:{} expConst:{} vars:{} varConsts:{}  b:%s>".format(self.err, self.expConst, self.vars, self.varConsts)

    def __str__(self):
        return "err:{}, expConst:{}, Vars:{}, varConsts:{}".format(self.err, self.expConst, self.vars, self.varConsts)


class EaseMLCI:
    def __init__(self,name,client,app_id,inst_id,project,revision,branch,fname='.easeml.yml'):
        self.name=name
        self.client = client
        self.app_id = app_id
        self.inst_id = inst_id
        self.project = project
        self.revision = revision
        self.branch = branch

        self.N=0
        self.configName=fname
        self.maxSteps = 0
        self.currentStep = 0
        self.lastAcc=0
        self.acc=0
        self.pdifference=0
        self.fail_type=0
        self.releaseData=False

        self.AllClauses=[]
        self.AllParsedClauses=[]
        
        self.msgHtml_rel=''
        self.msgHtml_error=''
        
        with open(fname,'r') as f:
            self.dprop=yaml.load(f,Loader=yaml.UnsafeLoader)
        self.parseProperties()

    def parseProperties(self):
        #print(self.dprop['ml'][6])
        self.script=self.dprop['ml'][0]['script']
        self.condition = self.dprop['ml'][1]['condition']
        self.condition = "".join(self.condition.split())
        self.parseConditions(self.condition)
        self.reliability=self.dprop['ml'][2]['reliability']
        self.mode = self.dprop['ml'][3]['mode']
        self.adaptivity = self.dprop['ml'][4]['adaptivity']
        self.maxSteps = self.dprop['ml'][5]['steps']
        self.dataMode = self.dprop['ml'][6]['dataMode']
        self.email = self.dprop['ml'][7]['email']
    def printProp(self):
        print(self.dprop)

    def calculateN(self):
        #TODO IMPORTANT RV should be provided by the user see below(?)
        print(self.adaptivity)
        print(self.condition)
        maxN=0
        if self.adaptivity=='none' or self.adaptivity=='hybrid':
            for clause in self.AllClauses:

                eps = clause.err
                rv = len(clause.vars)
                delta = (1 - self.reliability) / (rv*len(self.AllClauses)*self.maxSteps)
                allN = []
                for var, const in zip(clause.vars, clause.varConsts):
                    N = self.SHB(rv, const, delta, eps)
                    allN.append(N)
                maxN=max(maxN,np.max(allN))
        elif self.adaptivity=='full':
            for clause in self.AllClauses:

                eps=clause.err
                rv = len(clause.vars)
                delta = (1 - self.reliability) / (rv*len(self.AllClauses)*(2 ** self.maxSteps))
                allN=[]
                for var,const in zip(clause.vars,clause.varConsts):
                    N=self.SHB(rv,const,delta,eps)
                    allN.append(N)
                maxN=max(maxN,np.max(allN))
        N=int(round(maxN+0.5,0))
        print(N)
        return N

    #Standard Hoeffding bound
    def SHB(self, rv, c, delta, eps):
        return -c**2.0 * rv**2.0 * np.log(delta) / (2.0*(eps**2.0))
    #Optimized bound with p equal
    def SHB_P(self,rv,c,delta, p, eps):
        frac = eps / p;
        return -c**2.0 * rv**2.0 * np.log(delta) / (p * ((1 + frac) * np.log(1 + frac) - frac))

    def parseConditions(self,condition):

        #Separate into clauses
        self.C=condition.split('/\\')

        self.AllClauses=[]
        self.AllParsedClauses=[]
        #Separate error tolerance
        for clause in self.C:
            CE=clause.split('+/-')

            #Check the decomposiself.nametion in exp over o,n,d and error
            assert len(CE) == 2
            #Check no reminding division operators
            assert '/' not in CE[0]
            assert '/' not in CE[1]

            #Using @ to replace > and < simultaneusly
            assert '@' not in CE[0]
            
            assert 'n' in CE[0] or 'd' in CE[0] or 'o' in CE[0]
            self.AllParsedClauses.append(CE[0])
            
            CE[0]= CE[0].replace('<','@')
            CE[0] = CE[0].replace('>', '@')
            CE[0] = CE[0].split('@')

            #STRONG ASSUMTIONS HERE, NEED TO BE CHECKED
            pClause = Clause(float(CE[0][-1]),float(CE[1]))
            del CE[0][-1]

            #TODO How to deal with d*n*o (is this necessary?)
            #TODO How to deal with + - constants (is this necessary?)
            #Using @ to replace reminding +/-/*(?)

            allVarCons=[]
            for vars_and_cons in CE[0]:
                vars_and_cons = vars_and_cons.replace('*', '')
                vars_and_cons = vars_and_cons.replace('+', '@')
                vars_and_cons = vars_and_cons.replace('-', '@')
                vars_and_cons = vars_and_cons.split('@')
                allVarCons.extend(vars_and_cons)

            def CheckAllVars(vars,vc,pClause):
                for var in vars:
                    if var in vc:
                        pClause.vars.append(var)
                        vc = vc.replace(var,'')
                        if vc == '':
                            pClause.varConsts.append(1.0)
                        else:
                            pClause.varConsts.append(float(vc))
            vars=['n','o','d']
            for vc in allVarCons:
                CheckAllVars(vars,vc,pClause)

            self.AllClauses.append(pClause)

            #TODO DOUBLE CHECK ALL THE LOGIC HERE
            print(pClause)
    
    def CheckFileChanged(self,fname=None,lrevnum=1):
        command=['git','diff',"--exit-code",'{}~{}'.format(self.revision,lrevnum),'{}'.format(self.revision),fname]
        try:
            proc = subprocess.run(command,stdout=PIPE, stderr=PIPE, check=True)
            print("No change")
            print(proc.stderr.decode("utf-8"))
            print(proc.stdout.decode("utf-8"))
            return proc.returncode
        except Exception as e:
            if (e.returncode==1):
                print("Changed")
                return e.returncode
            print('Error with command: "'+' '.join(command)+'"')
            print(e.stderr.decode("utf-8"))
            print(e.stdout.decode("utf-8"))
            print(e)
            #exit(1)
            return e.returncode     
           
    def GetCurrentAndTotalRun(self):
        max_rev=50 #maximum distance from head to check
        for i in range(1,max_rev+1):
            print("### Checking data from revision -{}".format(i))
            try:
                data=self.client.list_checks(self.revision+'~'+str(i))
            except Exception as e:
                print("Didn't find previous data, assuming initial commit")
                print(">>> No data found starting from zero")             
                return 0,0,0,0,1
            
            for check_run in data['check_runs']:
                if check_run['name'] == self.name:
                    rawtext=check_run['output']['text']
                    if not rawtext:
                        continue
    
                    
                    start = '<!--'
                    end = '-->'
                    print("$$ ",check_run)
                    result = re.search('%s(.*)%s' % (start, end), rawtext).group(1)
                    d=json.loads(result)
                    if not 'acc' in d.keys():
                        continue
                    
                    
                    if d['acc'] == 0:
                        acc=d['last_acc']
                    else:
                        acc=d['acc']
                    
                    print("### Found data {}".format(d))
                    return d['current'],d['total'],acc,d['fail_type'],i
                    #Fail types 0 - No failure
                    #(negative) Not running model
                    #    docker -1 couldn't build the docker image
                    #    docker -2 couldn't run the docker container
                    #    not enough samples -3 
                    #(positive) Model ran but didn't pass the checks

        
        print(">>> No data found starting from zero")             
        return 0,0,0,0,1
    
    def PreCheck(self):
   
        data_manager=DataManager(self.client,self.project)
        data_manager.decryptData()
       
        optimization=False #True

        self.N=0
        if not optimization:
            #Extract N samples
            self.N=self.calculateN()
        else:
            ################################
            #Not implemented yet
            ################################
            
            #Calculate N_unlabeled
            #Run the model on N_unlabeled unlabeled samples
            #Evaluate the expression to calculate N 
            # ...
            self.N =0 
            raise Exception #Inform

        
        currStep,totalSteps,self.lastAcc,self.fail_type,lrevnum=self.GetCurrentAndTotalRun()
        changedYML=self.CheckFileChanged(".easeml.yml",lrevnum)
        changedData=self.CheckFileChanged("data_test/test.txt.enc",lrevnum)
        print("token = ",self.client.auth_token)
        print("Status: ChangedYML={} ChangedData={} currStep={} totalSteps={} ".format(changedYML,changedData, currStep,totalSteps))
        if (changedYML or changedData) and currStep>0 and totalSteps>1 and currStep<totalSteps:
            ##TODO (?) IGNORE CHANGES
            #raise Exception("Error: Changes without finalizing all steps: ChangedYML={} ChangedData={} currStep={} totalSteps={} ".format(changedYML,changedData, currStep,totalSteps))
            self.msgHtml_error+="<br>Warning: Changes in the parameters without finalizing all steps <br> <b>Restarting counters<b>"
            currStep=0
            totalSteps=self.maxSteps           
        
        if currStep+1 == totalSteps:
            ##This is the last step
            assert(totalSteps==self.maxSteps)
            if self.fail_type>=0:
                self.currentStep=currStep+1
            else:
                self.currentStep=currStep
            self.releaseData=True
            if not data_manager.ExtractSamples(self.N):
                self.fail_type=-3
                self.msgHtml_error+="<br>Error: <b>Not enough samples to perform operation<b>"
                return False
            #TODO INFORM 
        else:
            ##This is an intermediate step
            if currStep >= totalSteps:
                currStep=0
            
            if totalSteps:
                assert(totalSteps==self.maxSteps)
            if self.fail_type>=0:
                self.currentStep=currStep+1
            else:
                self.currentStep=currStep
            if not data_manager.ExtractSamples(self.N):
                self.fail_type=-3
                self.msgHtml_error+="<br>Error: <b>Not enough samples to perform operation<b>"
                return False
            self.fail_type=0
        return True        

    def PosCheck(self,acc):
        full_pattern = re.compile('[0-9\+\*\-\.<>]|_')
        def re_replace(string):
            return re.sub(full_pattern, '', string)
        self.acc=acc
        
        passed=True
        for CE in self.AllParsedClauses:
            CE =CE.replace('o',str(self.lastAcc))
            CE =CE.replace('n',str(self.acc))
            CE =CE.replace('d',str(self.pdifference))

            SEMPTY=re_replace(CE)
            assert not SEMPTY

            result=eval(CE)
            ##ASUMES ONLY "AND" contitions are allowed
            if not result:
               passed=False 
        
        if not passed and self.fail_type>=0:
            self.fail_type=1
               
        data_manager=DataManager(self.client,self.project)

        #For workshop = False
        self.releaseData=True
        if self.releaseData:
            data_manager.ReleaseSamples(self.N)
            self.msgHtml_rel="<br/>The exhausted data has been released"
    
        return True


if __name__ == "__main__":
    #emlci=EaseMLCI('./')
    #emlci.EaseMLCI_CHECK()
    pass

