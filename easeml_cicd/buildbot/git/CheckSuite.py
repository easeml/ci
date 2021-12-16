from buildbot.www.hooks.github import GitHubEventHandler
from twisted.python import log
from twisted.internet import defer
from dateutil.parser import parse as dateparse

class CheckSuiteHandler(GitHubEventHandler):

    def handle_check_suite(self, payload, event):
    
        log.msg("%%% ",payload)
        log.msg("2%%% ",payload['action'])
        if (payload['action']=='completed'):
            log.msg("3%%% ",payload['action'])
            return ([], 'git')
        # This field is unused:
        user = None
        # user = payload['pusher']['name']
        repo = payload['repository']['name']
        repo_url = payload['repository']['html_url']
        # NOTE: what would be a reasonable value for project?
        # project = request.args.get('project', [''])[0]
        project = payload['repository']['full_name']
        
        check_name='all'
        inst_id=payload['installation']['id']

        # Inject some additional white-listed event payload properties
        properties = self.extractProperties(payload)
        changes = self._process_check(payload['check_suite'], user, repo, repo_url, project,
                                       event, properties,check_name,inst_id)

        log.msg("Received {} changes from github".format(len(changes)))

        return changes, 'git'

    def handle_check_run(self, payload, event):
        # This field is unused:
        log.msg("%%% ",payload)
        user = None
        # user = payload['pusher']['name']
        repo = payload['repository']['name']
        repo_url = payload['repository']['html_url']
        # NOTE: what would be a reasonable value for project?
        # project = request.args.get('project', [''])[0]
        project = payload['repository']['full_name']

        # Inject some additional white-listed event payload properties
        properties = self.extractProperties(payload)
        
        check_name=payload['check_run']['name']
        inst_id=payload['installation']['id']
        
        return ([], 'git') #Ignore for the time being
        #changes = self._process_check(payload['check_run']['check_suite'], user, repo, repo_url, project,
        #                               event, properties,check_name,inst_id_or_token)

        #log.msg("Received {} changes from github".format(len(changes)))
        
        #return changes, 'git'
    def handle_push(self, payload, event):
        return ([], 'git') #Ignore for the time being
        
        
    def _process_check(self, payload, user, repo, repo_url, project, event,
                        properties,check_name,inst_id):
        """
        Consumes the JSON as a python object and actually starts the build.

        :arguments:
            payload
                Python Object that represents the JSON sent by GitHub Service
                Hook.
        """
        changes = []
        #refname = payload['ref']


        #TODO, Ignore conditions
        # We only care about regular heads or tags
        #match = re.match(r"^refs/(heads|tags)/(.+)$", refname)
        #if not match:
        #    log.msg("Ignoring refname `{}': Not a branch".format(refname))
        #    return changes
        #category = None  # None is the legacy category for when hook only supported push
        #if match.group(1) == "tags":
        #    category = "tag"
        #        if payload.get('deleted'):
        #    log.msg("Branch `{}' deleted, ignoring".format(branch))
        #    return changes

        branch = payload['head_branch']


        # check skip pattern in commit message. e.g.: [ci skip] and [skip ci]
        head_msg = payload['head_commit'].get('message', '')
        if self._has_skip(head_msg):
            return changes
        #commits = payload['commits']
        #if payload.get('created'):
        #    commits = [payload['head_commit']]
        
        commits = [payload['head_commit']]
        for commit in commits:
            files = []
            for kind in ('added', 'modified', 'removed'):
                files.extend(commit.get(kind, []))

            when_timestamp = dateparse(commit['timestamp'])

            log.msg("New revision: {}".format(commit['id'][:8]))

            change = {
                'author': '{} <{}>'.format(commit['author']['name'],
                                           commit['author']['email']),
                'files': files,
                'comments': commit['message'],
                'revision': commit['id'],
                'when_timestamp': when_timestamp,
                'branch': branch,
                'revlink': "{}/commit/{}".format(repo_url,commit['id']), #commit['url'],
                'repository': repo_url,
                'project': project,
                'properties': {
                    #'github_distinct': commit.get('distinct', True),
                    'event': event,
                    'app_id': payload['app']['id'],
                    'inst_id_or_token':inst_id,
                    'check_name':check_name
                }#,
                #'category': category

            }
            # Update with any white-listed github event properties
            change['properties'].update(properties)

            if callable(self._codebase):
                change['codebase'] = self._codebase(payload)
            elif self._codebase is not None:
                change['codebase'] = self._codebase

            changes.append(change)

        return changes

        return changes, 'git'
