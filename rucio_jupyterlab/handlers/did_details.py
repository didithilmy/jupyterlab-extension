import os
import tornado
import json
from urllib.parse import urlparse
from .base import RucioAPIHandler
from rucio_jupyterlab.db import get_db


class DIDDetailsHandler(RucioAPIHandler):
    STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
    STATUS_REPLICATING = "REPLICATING"
    STATUS_OK = "OK"
    STATUS_STUCK = "STUCK"

    @tornado.web.authenticated
    def get(self):
        namespace = self.get_query_argument('namespace')
        poll = self.get_query_argument('poll', '0') == '1'
        did = self.get_query_argument('did')
        scope, name = did.split(':')

        output = self.get_did_details(namespace, scope, name, poll)

        self.finish(json.dumps(output))

    def get_did_details(self, namespace, scope, name, force_fetch=False):
        rucio = self.rucio.for_instance(namespace)
        db = get_db()
        did = f'{scope}:{name}'

        attached_files = self.get_attached_files(
            namespace, rucio, db, scope, name, force_fetch)
        file_replicas = self.get_file_replicas(
            namespace, rucio, db, scope, name, attached_files, force_fetch)

        complete = True
        replicated_files = dict()
        for file_replica in file_replicas:
            file_did = file_replica.get('did')
            path = file_replica.get('path')
            replicated_files[file_did] = path
            if file_did not in attached_files:
                complete = False

        if len(replicated_files) == 0:
            complete = False

        status = DIDDetailsHandler.STATUS_NOT_AVAILABLE
        if not complete:
            status = self.get_did_status(rucio, scope, name)

        results = []
        for file_did in attached_files:
            if file_did in replicated_files:
                path = replicated_files[file_did]
                results.append(
                    dict(status=DIDDetailsHandler.STATUS_OK, did=file_did, path=path))
            else:
                results.append(dict(status=status, did=file_did, path=None))

        return results

    def get_attached_files(self, namespace, rucio, db, scope, name, force_fetch=False):
        did = f'{scope}:{name}'

        if not force_fetch:
            attached_files = db.get_attached_files(namespace, did)
        else:
            attached_files = None

        if attached_files == None:
            rucio_attached_files = rucio.get_files(scope, name)
            attached_files = [
                (x.get('scope') + ':' + x.get('name')) for x in rucio_attached_files
            ]
            db.set_attached_files(namespace, did, attached_files)

        return attached_files

    def get_file_replicas(self, namespace, rucio, db, scope, name, attached_files, force_fetch=False):
        complete = True
        file_replicas = []

        if force_fetch:
            complete = False
        else:
            for file_did in attached_files:
                pfn = db.get_file_replica(namespace, file_did)
                if pfn != None:
                    path = self.translate_pfn_to_path(rucio, pfn)
                    file_replicas.append(dict(did=file_did, path=path))
                else:
                    complete = False

        if not complete:
            file_replicas = []
            fetched_file_replicas = self.fetch_file_replicas(
                namespace, rucio, scope, name, attached_files)
            for file_replica in fetched_file_replicas:
                did = file_replica.get('did')
                pfn = file_replica.get('pfn')
                db.set_file_replica(namespace, file_did=did, pfn=pfn)

                path = self.translate_pfn_to_path(rucio, pfn)
                file_replicas.append(dict(did=did, path=path))

        return file_replicas

    def get_did_status(self, rucio, scope, name):
        status = DIDDetailsHandler.STATUS_NOT_AVAILABLE
        replication_rule = self.fetch_replication_rule_by_did(
            rucio, scope, name)
        if replication_rule != None:
            _, replication_status, _ = replication_rule
            status = self.parse_rule_status(replication_status)

        return status

    def fetch_file_replicas(self, namespace, rucio, scope, name, attached_files):
        destination_rse = rucio.instance_config.get('destination_rse')

        replicas = []
        rucio_replicas = rucio.get_replicas(scope, name)
        for rucio_replica in rucio_replicas:
            rses = rucio_replica['rses']
            states = rucio_replica['states']

            if (destination_rse in rses) and (destination_rse in states):
                if states[destination_rse] == 'AVAILABLE':
                    pfns = rses[destination_rse]
                    if len(pfns) > 0:
                        did = rucio_replica['scope'] + \
                            ':' + rucio_replica['name']
                        replica = dict(pfn=pfns[0], did=did)
                        replicas.append(replica)

        return replicas

    def fetch_replication_rule_by_did(self, rucio, scope, name):
        destination_rse = rucio.instance_config.get('destination_rse')

        rules = rucio.get_rules(scope, name)
        filtered_rules = []
        for rule in rules:
            if rule['rse_expression'] == destination_rse:
                filtered_rules.append(rule)

        if len(filtered_rules) > 0:
            replication_rule = filtered_rules[0]
            rule_id = replication_rule.get('id')
            status = self.parse_rule_status(replication_rule.get('state'))
            expires_at = replication_rule.get('expires_at')

            return (rule_id, status, expires_at)

        return None

    def parse_rule_status(self, status):
        if status == 'OK':
            status = DIDDetailsHandler.STATUS_OK
        elif status == 'REPLICATING':
            status = DIDDetailsHandler.STATUS_REPLICATING
        else:
            status = DIDDetailsHandler.STATUS_STUCK

        return status

    def translate_pfn_to_path(self, rucio, pfn):
        instance_config = rucio.instance_config
        prefix_path = instance_config.get('rse_mount_path')
        path_begins_at = instance_config.get('path_begins_at', 0)

        path = urlparse(pfn).path
        suffix_path = self.get_path_after_nth_slash(path, path_begins_at)
        return os.path.join(prefix_path, suffix_path)

    def get_path_after_nth_slash(self, path, n):
        return path.strip('/').split('/', n)[-1]
