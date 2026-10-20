"""v2 draft bridge tests; authoritative physical candidate tests remain separate."""
import copy
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import review_candidate_v2 as v2

class NewCandidateTests(unittest.TestCase):
    def setUp(self):
        self.result={'status':'CANDIDATE_BYTES_STATICALLY_VERIFIED_PENDING_ANDROID',
                     'apk_sha256':v2.APK_SHA256,'apk_bytes':v2.APK_BYTES,'elf_total':97,'arm64':96,
                     'signed':False,'installed':False,'android_runtime_validated':False,
                     'distribution_allowed':False,'historical_contract_modified':False}

    def test_pinned_physical_result_accepted(self):
        v2.check_physical_result(self.result)
        self.assertNotEqual(v2.APK_SHA256,v2.historical.APK_SHA256)

    def test_metadata_only_result_cannot_seed_v2(self):
        self.result['status']='CANDIDATE_METADATA_REVIEWED_BYTES_NOT_VERIFIED'
        with self.assertRaises(ValueError):v2.check_physical_result(self.result)

    def test_historical_apk_not_reused(self):
        self.result['apk_sha256']=v2.historical.APK_SHA256
        with self.assertRaises(ValueError):v2.check_physical_result(self.result)

    def test_wrong_length_rejected(self):
        self.result['apk_bytes']+=1
        with self.assertRaises(ValueError):v2.check_physical_result(self.result)

    def test_incomplete_elf_counts_rejected(self):
        for key in ('elf_total','arm64'):
            original=self.result[key];self.result[key]-=1
            with self.assertRaises(ValueError):v2.check_physical_result(self.result)
            self.result[key]=original

    def test_runtime_or_signing_claims_rejected(self):
        for key in ('signed','installed','android_runtime_validated','distribution_allowed','historical_contract_modified'):
            self.result[key]=True
            with self.assertRaises(ValueError):v2.check_physical_result(self.result)
            self.result[key]=False

    def test_authoritative_physical_verifier_is_reused(self):
        apk=Path('/synthetic/not-a-real-apk')
        with patch.object(v2.candidate,'review',return_value=self.result)as verify:
            result=v2.prepare(apk)
        verify.assert_called_once_with(v2.EVIDENCE,apk)
        self.assertFalse(result['runtime_contract_activated'])
        self.assertFalse(result['apk_signing_authorized'])
        self.assertIsNone(result['certificate_sha256'])
        self.assertEqual(len(result['cases']),12)
        self.assertEqual(len(result['wheel_sha256']),18)

    def test_authoritative_rejection_propagates(self):
        with patch.object(v2.candidate,'review',side_effect=ValueError('SYNTHETIC_REJECTION')):
            with self.assertRaisesRegex(ValueError,'SYNTHETIC_REJECTION'):v2.prepare(Path('/synthetic/apk'))

    def test_changed_authoritative_pin_requires_review(self):
        with patch.object(v2.candidate,'review',return_value=self.result),patch.object(v2.candidate,'SOURCE_HEAD','0'*40):
            with self.assertRaises(ValueError):v2.prepare(Path('/synthetic/apk'))

    def test_v1_hash_protected(self):
        with patch.object(v2.candidate,'review',return_value=self.result),patch.object(v2,'V1_SHA256','0'*64):
            with self.assertRaises(ValueError):v2.prepare(Path('/synthetic/apk'))

    def test_private_writer_exclusive_and_restrictive(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'draft.json';v2.write_private(p,{'certificate_sha256':None})
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)
            with self.assertRaises(ValueError):v2.write_private(p,{})

    def test_writer_rejects_repository_and_symlink(self):
        with self.assertRaises(ValueError):v2.write_private(v2.ROOT/'not-created.json',{})
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'link.json';p.symlink_to(Path(d)/'missing.json')
            with self.assertRaises(ValueError):v2.write_private(p,{})
