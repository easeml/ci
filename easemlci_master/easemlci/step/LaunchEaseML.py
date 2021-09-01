from twisted.python import log
from twisted.internet import defer
from buildbot.steps.shell import ShellCommand
from buildbot.process import remotecommand

class EaseML(ShellCommand):

    name = "easeML test suit"
    warnOnFailure = 1
    description = ["testing"]
    descriptionDone = ["test"]
    command = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def start(self):    
        all_changes = {}
        lchanges=self.build.allChanges()
        for lc in lchanges:
            d=lc.asChDict()
            all_changes.update(d)
        
        log.msg(all_changes)
        app_id=all_changes['properties']['app_id'][0]
        inst_id=all_changes['properties']['inst_id'][0]
        project=all_changes['project']
        revision=all_changes['revision']
        branch=all_changes['branch']
        
        warnings = []
        # create the actual RemoteShellCommand instance now
        kwargs = self.buildCommandKwargs(warnings)
        kwargs['command'].append("easeMLcore")
        kwargs['command'].append(app_id)
        kwargs['command'].append(inst_id)
        kwargs['command'].append(project)
        kwargs['command'].append(revision)
        kwargs['command'].append(branch)
        
        log.msg(kwargs['command'])
        cmd = remotecommand.RemoteShellCommand(**kwargs)
        self.setupEnvironment(cmd)

        self.startCommand(cmd, warnings)


