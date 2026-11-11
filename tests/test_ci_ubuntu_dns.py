"""The build fallback stays bounded and never accepts arbitrary hosts/IP text."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

path=Path(__file__).resolve().parents[1]/'tools/beta_release/ubuntu_dns.py'
spec=importlib.util.spec_from_file_location('ubuntu_dns',path)
dns=importlib.util.module_from_spec(spec);spec.loader.exec_module(dns)


def test_dns_answers_are_public_ipv4_and_deduplicated():
    assert dns.ipv4_answers({'Status':0,'Answer':[{'type':5,'data':'canonical.example'},
        {'type':1,'data':'185.125.190.81'},{'type':1,'data':'185.125.190.81'}]})==['185.125.190.81']
    for document in [{'Status':2}, {'Status':0}, *[{'Status':0,'Answer':[{'type':1,'data':value}]}
        for value in ['127.0.0.1','10.0.0.1','169.254.169.254','224.0.0.1','::1','185.125.190.81 evil.example']]]:
        with pytest.raises(ValueError):dns.ipv4_answers(document)


def test_system_dns_keeps_hosts_untouched_and_clears_old_output(tmp_path):
    output=tmp_path/'hosts';output.write_text('old data')
    def resolve(argv,**kwargs):
        assert argv==['getent','ahostsv4','archive.ubuntu.com'] and kwargs['timeout']==6
        return SimpleNamespace(returncode=0,stdout='185.125.190.81 STREAM archive.ubuntu.com')
    dns.prepare(output,resolver=resolve,fetch=lambda:pytest.fail('unnecessary external DNS request'))
    assert output.read_text()==''


def test_failed_system_dns_emits_only_the_fixed_archive_host(tmp_path):
    output=tmp_path/'hosts'
    dns.prepare(output,resolver=lambda *a,**k:SimpleNamespace(returncode=2,stdout=''),fetch=lambda:['185.125.190.81'])
    assert output.read_text()=='185.125.190.81 archive.ubuntu.com\n'
    with pytest.raises(ValueError):
        dns.prepare(output,resolver=lambda *a,**k:SimpleNamespace(returncode=2,stdout=''),fetch=lambda:['127.0.0.1'])
    assert output.read_text()==''
