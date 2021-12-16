from twisted.python import log
from twisted.internet import defer
from buildbot.process import buildstep


class EaseMLStep(buildstep.ShellMixin, buildstep.BuildStep):
    name = "easeML test suit"
    warnOnFailure = 1
    description = ["testing"]
    descriptionDone = ["test"]
    command = []

    def __init__(self, *args, **kwargs):
        kwargs = self.setupShellMixin(kwargs)
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        all_changes = {}
        lchanges = self.build.allChanges()
        for lc in lchanges:
            d = lc.asChDict()
            all_changes.update(d)
        log.msg("##### ALL CHANGES")
        log.msg(all_changes)
        app_id = all_changes['properties']['app_id'][0]
        inst_id = all_changes['properties']['inst_id_or_token'][0]
        project = all_changes['project']
        revision = all_changes['revision']
        branch = all_changes['branch']

        shell_command = []
        # create the actual RemoteShellCommand instance now
        shell_command.append("easeml_cicd_runner")
        shell_command.append(app_id)
        shell_command.append(inst_id)
        shell_command.append(project)
        shell_command.append(revision)
        shell_command.append(branch)

        log.msg("##### COMMAND")
        log.msg(shell_command)

        cmd = yield self.makeRemoteShellCommand(
            command=shell_command
        )
        yield self.runCommand(cmd)
        return cmd.results()