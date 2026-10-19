"""Canonical installation preserves identities and rolls back partial replacement."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import test_pdebench_examples as examples
ROOT = examples.ROOT
from utils.PDEBench.installation import install, verify_installed, PAYLOAD
from caeoj_tools.public_examples import INSTALLATION, BINDING, verify_public_examples
from utils.publish_dist import publish
from utils.prepare_harbor import prepare


class InstallationTests(unittest.TestCase):
    entries = examples.PublicExampleTests.entries
    aliases = examples.PublicExampleTests.aliases
    prepared = examples.PublicExampleTests.prepared
    def test_install_and_replace_rollback_and_tamper(self):
        with self.prepared() as (workspace, selection, disk), tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            target=Path(tmp)/'target'
            shutil.copytree(workspace,target,ignore=shutil.ignore_patterns('workspace.json','cases','reference','samples','evidence','transactions','public-examples.json'))
            result=install(workspace,selection,target)
            self.assertEqual(result['case_count'],20)
            task=next(target.glob('qbank/*/*/advection-1d'))
            self.assertEqual(len(verify_public_examples(task)),2)
            publish('advection-1d',root=target)
            self.assertEqual(prepare('advection-1d',root=target)['cases'],20)
            with self.assertRaisesRegex(RuntimeError,'--replace'):install(workspace,selection,target)
            receipt=(task/INSTALLATION).read_bytes();inp=(task/'cases/001/input.h5').read_bytes()
            original=shutil.copytree
            def failed(src,dst,*a,**kw):
                if Path(dst)==task/'samples':raise OSError('simulated install interruption')
                return original(src,dst,*a,**kw)
            with patch('utils.PDEBench.installation.shutil.copytree',failed),self.assertRaises(OSError):
                install(workspace,selection,target,replace=True)
            self.assertEqual((task/INSTALLATION).read_bytes(),receipt)
            self.assertEqual((task/'cases/001/input.h5').read_bytes(),inp)
            self.assertEqual(verify_installed(selection,target)['case_count'],20)
            marker=task/BINDING;old=marker.read_bytes();marker.unlink()
            with self.assertRaisesRegex(ValueError,'coverage'):publish('advection-1d',root=target)
            marker.write_bytes(old)
            (task/'cases/001/input.h5').write_bytes(inp+b'altered')
            with self.assertRaisesRegex(ValueError,'modified'):verify_public_examples(task)
            (task/'cases/001/input.h5').write_bytes(inp)
            (task/INSTALLATION).write_text('{"status":"installing"}')
            with self.assertRaisesRegex(ValueError,'Incomplete'):prepare('advection-1d',root=target)
            (task/INSTALLATION).write_bytes(receipt)
            self.assertEqual(install(workspace,selection,target,replace=True)['case_count'],20)

    def test_install_without_public_aliases(self):
        with patch.object(self, 'aliases', return_value={}), self.prepared() as (workspace, selection, disk), tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            target=Path(tmp)/'target'
            shutil.copytree(workspace,target,ignore=shutil.ignore_patterns('workspace.json','cases','reference','samples','evidence','transactions'))
            self.assertEqual(install(workspace,selection,target)['case_count'],20)
            task=next(target.glob('qbank/*/*/advection-1d'))
            self.assertEqual(verify_public_examples(task),[])
