"""Synthetic infrastructure tests. Never launch Android, ADB or unshare."""
from pathlib import Path
from types import SimpleNamespace
import os
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import empty_avd_boot as boot


class EmptyBootTests(unittest.TestCase):
    def network(self, links=None, routes=None, parent='net:[1]', current='net:[2]'):
        with patch.object(boot, 'network_identity', return_value=current), \
             patch.object(boot.os, 'readlink', return_value='net:[1]'):
            boot.isolation_check(parent, links if links is not None else [{'ifname':'lo','flags':['UP']}],
                                 routes if routes is not None else [], [])

    def test_fresh_loopback_namespace_allowed(self):
        self.network(routes=[{'dst':'127.0.0.0/8','dev':'lo'}])

    def test_existing_namespace_rejected(self):
        with self.assertRaises(ValueError):self.network(current='net:[1]')

    def test_forged_parent_rejected(self):
        with self.assertRaises(ValueError):self.network(parent='net:[9]')

    def test_external_interface_rejected(self):
        with self.assertRaises(ValueError):self.network(links=[{'ifname':'lo','flags':['UP']},{'ifname':'eth0'}])

    def test_default_gateway_rejected_even_on_loopback(self):
        for row in [{'dev':'lo','dst':'default'},{'dev':'lo','gateway':'127.0.0.1'},{}]:
            with self.subTest(route=row),self.assertRaises(ValueError):self.network(routes=[row])

    def test_down_loopback_rejected(self):
        with self.assertRaises(ValueError):self.network(links=[{'ifname':'lo','flags':[]}])

    def test_proxy_preload_and_adb_environment_not_inherited(self):
        with patch.dict(os.environ, {'HTTPS_PROXY':'SYNTHETIC','LD_PRELOAD':'SYNTHETIC','ADB_SERVER_SOCKET':'SYNTHETIC'}):
            env=boot.clean_environment(Path('/sdk'),Path('/user'),Path('/avd'))
        self.assertNotIn('HTTPS_PROXY',env);self.assertNotIn('LD_PRELOAD',env)
        self.assertEqual(env['ADB_SERVER_SOCKET'],'tcp:127.0.0.1:5037')
        self.assertEqual(env['ADB_MDNS_AUTO_CONNECT'],'0')

    def test_previously_booted_avd_rejected(self):
        with tempfile.TemporaryDirectory()as t:
            home=Path(t);name=boot.AVDS['api24-4k'];d=home/(name+'.avd');d.mkdir()
            sdk=home/'sdk'
            (home/(name+'.ini')).write_text('path='+str(d)+'\n')
            (d/'config.ini').write_text('abi.type=arm64-v8a\nimage.sysdir.1='+boot.IMAGE_DIRS['api24-4k']+'\n')
            self.assertEqual(boot.check_fresh_avd(home,'api24-4k',sdk),name)
            (home/(name+'.ini')).write_text('path=/unreviewed/personal.avd\n')
            with self.assertRaises(ValueError):boot.check_fresh_avd(home,'api24-4k',sdk)
            (home/(name+'.ini')).write_text('path='+str(d)+'\n')
            (d/'userdata-qemu.img').write_text('SYNTHETIC')
            with self.assertRaises(ValueError):boot.check_fresh_avd(home,'api24-4k',sdk)

    def test_exact_api35_and_no_bridge_required(self):
        boot.check_guest({'api':35},'arm64-16k','package:android','Accounts: 0','0')
        for env,bridge in [({'api':37},'0'),({'api':35},'1')]:
            with self.assertRaises(ValueError):boot.check_guest(env,'arm64-16k','package:android','Accounts: 0',bridge)

    def test_accounts_and_preinstalled_clients_rejected(self):
        for packages,accounts in [('package:com.exteraless.app','Accounts: 0'),('package:android','Accounts: 1'),('package:android','unverified')]:
            with self.assertRaises(ValueError):boot.check_guest({'api':24},'api24-4k',packages,accounts,'')

    def test_blocked_host_never_invokes_namespace_or_android(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);home=root/'homes';home.mkdir()
            args=SimpleNamespace(timeout=600,sdk=root/'sdk',archives=root/'images',avd_home=home,
                                 user_home=home,output=root/'new-private')
            with patch.object(boot.host,'probe',return_value={'blockers':['SYNTHETIC_DENIAL']}), \
                 patch.object(boot.subprocess,'run')as run, patch.object(boot.subprocess,'Popen')as popen:
                with self.assertRaisesRegex(ValueError,'Host preflight BLOCKED'):boot.launch(args)
                run.assert_not_called()
                popen.assert_not_called()
            self.assertTrue((args.output/'preflight.json').is_file())

    def test_guest_validation_reuses_existing_runner(self):
        import run_lab
        self.assertIs(boot.preflight,run_lab.preflight)
        self.assertIs(boot.Adb,run_lab.Adb)

    def test_materialized_image_tampering_rejected(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);archives=root/'archives';archives.mkdir();sdk=root/'sdk'
            destination=sdk/boot.IMAGE_DIRS['api24-4k'];destination.mkdir(parents=True)
            (destination/'kernel-ranchu').write_bytes(b'SYNTHETIC_KERNEL')
            with zipfile.ZipFile(archives/boot.host.IMAGES['api24-4k']['filename'],'w')as z:
                z.writestr('arm64-v8a/kernel-ranchu',b'SYNTHETIC_KERNEL')
            boot.verify_materialized(sdk,archives,'api24-4k')
            (destination/'kernel-ranchu').write_bytes(b'SYNTHETIC_CORRUPTION')
            with self.assertRaisesRegex(ValueError,'differs'):boot.verify_materialized(sdk,archives,'api24-4k')

    def test_duplicate_avd_paths_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):boot.ini('path=/one\npath=/two\n')
