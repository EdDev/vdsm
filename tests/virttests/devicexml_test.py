#
# Copyright 2017 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA
#
# Refer to the README and COPYING files for full details of the license
#
from __future__ import absolute_import

import logging
import os.path

from vdsm.virt import vmdevices
from vdsm.virt import vmxml
from vdsm import constants

from monkeypatch import MonkeyPatchScope, MonkeyPatch
from testlib import permutations, expandPermutations
from testlib import XMLTestCase


@expandPermutations
class DeviceToXMLTests(XMLTestCase):

    PCI_ADDR = \
        'bus="0x00" domain="0x0000" function="0x0" slot="0x03" type="pci"'
    PCI_ADDR_DICT = {'slot': '0x03', 'bus': '0x00', 'domain': '0x0000',
                     'function': '0x0', 'type': 'pci'}

    def setUp(self):
        self.log = logging.getLogger('test.virt')
        self.conf = {
            'vmName': 'testVm',
            'vmId': '9ffe28b6-6134-4b1e-8804-1185f49c436f',
            'smp': '8',
            'maxVCpus': '160',
            'memSize': '1024',
            'memGuaranteedSize': '512',
        }

    def test_console_virtio(self):
        consoleXML = """
            <console type="pty">
                <target port="0" type="virtio"/>
            </console>"""
        dev = {
            'device': 'console',
            'specParams': {'consoleType': 'virtio'},
            'vmid': self.conf['vmId'],
        }
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getXML()), consoleXML)

    def test_console_serial(self):
        consoleXML = """
            <console type="pty">
                <target port="0" type="serial"/>
            </console>"""
        dev = {
            'device': 'console',
            'specParams': {'consoleType': 'serial'},
            'vmid': self.conf['vmId'],
        }
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getXML()), consoleXML)

    def test_console_default(self):
        consoleXML = """
            <console type="pty">
                <target port="0" type="virtio"/>
            </console>"""
        dev = {
            'device': 'console',
            'vmid': self.conf['vmId'],
        }
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getXML()), consoleXML)

    def test_serial_device(self):
        serialXML = """
            <serial type="pty">
                <target port="0"/>
            </serial>"""
        dev = {
            'device': 'console',
            'vmid': self.conf['vmId'],
        }
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getSerialDeviceXML()),
                            serialXML)

    def test_unix_socket_serial_device(self):
        path = "/var/run/ovirt-vmconsole-console/%s.sock" % self.conf['vmId']
        serialXML = """
            <serial type="unix">
                <source mode="bind" path="%s" />
                <target port="0" />
            </serial>""" % path
        dev = {
            'vmid': self.conf['vmId'],
            'device': 'console',
            'specParams': {
                'enableSocket': True
            }
        }
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getSerialDeviceXML()),
                            serialXML)

    def test_smartcard(self):
        smartcardXML = '<smartcard mode="passthrough" type="spicevmc"/>'
        dev = {'device': 'smartcard',
               'specParams': {'mode': 'passthrough', 'type': 'spicevmc'}}
        smartcard = vmdevices.core.Smartcard(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(smartcard.getXML()),
                            smartcardXML)

    def test_tpm(self):
        tpmXML = """
            <tpm model="tpm-tis">
                <backend type="passthrough">
                    <device path="/dev/tpm0"/>
                </backend>
            </tpm>
            """
        dev = {'device': 'tpm',
               'specParams': {'mode': 'passthrough',
                              'path': '/dev/tpm0', 'model': 'tpm-tis'}}
        tpm = vmdevices.core.Tpm(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(tpm.getXML()), tpmXML)

    @permutations([[None], [{}], [{'enableSocket': False}]])
    def test_console_pty(self, specParams):
        consoleXML = """
            <console type="pty">
                <target port="0" type="virtio"/>
            </console>"""
        dev = {'device': 'console'}
        if specParams is not None:
            dev['specParams'] = specParams
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getXML()), consoleXML)

    def test_console_socket(self):
        consoleXML = """
            <console type="unix">
                <source mode="bind" path="%s%s.sock" />
                <target port="0" type="virtio"/>
            </console>""" % (constants.P_OVIRT_VMCONSOLES,
                             self.conf['vmId'])
        dev = {'device': 'console', 'specParams': {'enableSocket': True}}
        dev['vmid'] = self.conf['vmId']
        console = vmdevices.core.Console(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(console.getXML()), consoleXML)

    def test_balloon(self):
        balloonXML = '<memballoon model="virtio"/>'
        dev = {'device': 'memballoon', 'type': 'balloon',
               'specParams': {'model': 'virtio'}}
        balloon = vmdevices.core.Balloon(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(balloon.getXML()), balloonXML)

    def test_rng(self):
        rngXML = """
            <rng model="virtio">
                <rate bytes="1234" period="2000"/>
                <backend model="random">/dev/random</backend>
            </rng>"""

        dev = {'type': 'rng', 'model': 'virtio', 'specParams':
               {'period': '2000', 'bytes': '1234', 'source': 'random'}}

        rng = vmdevices.core.Rng(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(rng.getXML()), rngXML)

    def test_watchdog(self):
        watchdogXML = '<watchdog action="none" model="i6300esb"/>'
        dev = {'device': 'watchdog', 'type': 'watchdog',
               'specParams': {'model': 'i6300esb', 'action': 'none'}}
        watchdog = vmdevices.core.Watchdog(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(watchdog.getXML()), watchdogXML)

    def test_sound(self):
        soundXML = '<sound model="ac97"/>'
        dev = {'device': 'ac97'}
        sound = vmdevices.core.Sound(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(sound.getXML()), soundXML)

    @permutations([
        [{'device': 'vga',
          'specParams': {'vram': '32768', 'heads': '2'}},
         """<video>
         <model heads="2" type="vga" vram="32768"/>
         </video>"""],
        [{'device': 'qxl',
          'specParams': {'vram': '65536', 'heads': '2', 'ram': '131072'}},
         """<video>
         <model heads="2" ram="131072" type="qxl" vram="65536"/>
         </video>"""],
        [{'device': 'qxl',
          'specParams': {'vram': '32768', 'heads': '2',
                         'ram': '65536', 'vgamem': '8192'}},
         """<video>
         <model heads="2" ram="65536" type="qxl" vgamem="8192" vram="32768"/>
         </video>"""]
    ])
    def test_video(self, dev_spec, video_xml):
        video = vmdevices.core.Video(self.log, **dev_spec)
        self.assertXMLEqual(vmxml.format_xml(video.getXML()), video_xml)

    def test_controller(self):
        devConfs = [
            {'device': 'ide', 'index': '0', 'address': self.PCI_ADDR_DICT},
            {'device': 'scsi', 'index': '0', 'model': 'virtio-scsi',
             'address': self.PCI_ADDR_DICT},
            {'device': 'scsi', 'index': '0', 'model': 'virtio-scsi',
             'address': self.PCI_ADDR_DICT, 'specParams': {}},
            {'device': 'scsi', 'model': 'virtio-scsi', 'index': '0',
             'specParams': {'ioThreadId': '0'},
             'address': self.PCI_ADDR_DICT},
            {'device': 'scsi', 'model': 'virtio-scsi', 'index': '0',
             'specParams': {'ioThreadId': 0},
             'address': self.PCI_ADDR_DICT},
            {'device': 'virtio-serial', 'address': self.PCI_ADDR_DICT},
            {'device': 'usb', 'model': 'ich9-ehci1', 'index': '0',
             'master': {'startport': '0'}, 'address': self.PCI_ADDR_DICT}]
        expectedXMLs = [
            """
            <controller index="0" type="ide">
                <address %s/>
            </controller>""",

            """
            <controller index="0" model="virtio-scsi" type="scsi">
                <address %s/>
            </controller>""",

            """
            <controller index="0" model="virtio-scsi" type="scsi">
                <address %s/>
            </controller>""",

            """
            <controller index="0" model="virtio-scsi" type="scsi">
                <address %s/>
                <driver iothread="0"/>
            </controller>""",

            """
            <controller index="0" model="virtio-scsi" type="scsi">
                <address %s/>
                <driver iothread="0"/>
            </controller>""",

            """
            <controller index="0" ports="16" type="virtio-serial">
                <address %s/>
            </controller>""",

            """
            <controller index="0" model="ich9-ehci1" type="usb">
                <master startport="0"/>
                <address %s/>
            </controller>"""]

        for devConf, xml in zip(devConfs, expectedXMLs):
            device = vmdevices.core.Controller(self.log, **devConf)
            self.assertXMLEqual(vmxml.format_xml(device.getXML()),
                                xml % self.PCI_ADDR)

    def test_redir(self):
        redirXML = """
            <redirdev type="spicevmc">
                <address %s/>
            </redirdev>""" % self.PCI_ADDR

        dev = {'device': 'spicevmc', 'address': self.PCI_ADDR_DICT}

        redir = vmdevices.core.Redir(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(redir.getXML()), redirXML)

    def test_memory_device(self):
        memoryXML = """<memory model='dimm'>
            <target>
                <size unit='KiB'>1048576</size>
                <node>0</node>
            </target>
        </memory>
        """
        params = {'device': 'memory', 'type': 'memory',
                  'size': 1024, 'node': 0}
        memory = vmdevices.core.Memory(self.log, **params)
        self.assertXMLEqual(vmxml.format_xml(memory.getXML()), memoryXML)

    @MonkeyPatch(vmdevices.network.supervdsm,
                 'getProxy', lambda: FakeProxy())
    def test_interface(self):
        interfaceXML = """
            <interface type="bridge"> <address %s/>
                <mac address="52:54:00:59:F5:3F"/>
                <model type="virtio"/>
                <source bridge="ovirtmgmt"/>
                <filterref filter="no-mac-spoofing"/>
                <boot order="1"/>
                <driver name="vhost" queues="7"/>
                <tune>
                    <sndbuf>0</sndbuf>
                </tune>
                <bandwidth>
                    <inbound average="1000" burst="1024" peak="5000"/>
                    <outbound average="128" burst="256"/>
                </bandwidth>
            </interface>""" % self.PCI_ADDR

        dev = {'nicModel': 'virtio', 'macAddr': '52:54:00:59:F5:3F',
               'network': 'ovirtmgmt', 'address': self.PCI_ADDR_DICT,
               'device': 'bridge', 'type': 'interface',
               'bootOrder': '1', 'filter': 'no-mac-spoofing',
               'specParams': {'inbound': {'average': 1000, 'peak': 5000,
                                          'burst': 1024},
                              'outbound': {'average': 128, 'burst': 256}},
               'custom': {'queues': '7'},
               'vm_custom': {'vhost': 'ovirtmgmt:true', 'sndbuf': '0'},
               }
        iface = vmdevices.network.Interface(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(iface.getXML()), interfaceXML)

    @MonkeyPatch(vmdevices.network.supervdsm,
                 'getProxy', lambda: FakeProxy())
    def test_interface_filter_parameters(self):
        interfaceXML = """
            <interface type="bridge"> <address %s/>
                <mac address="52:54:00:59:F5:3F"/>
                <model type="virtio"/>
                <source bridge="ovirtmgmt"/>
                <filterref filter="clean-traffic">
                    <parameter name='IP' value='10.0.0.1'/>
                    <parameter name='IP' value='10.0.0.2'/>
                </filterref>
                <boot order="1"/>
                <driver name="vhost"/>
                <tune>
                    <sndbuf>0</sndbuf>
                </tune>
            </interface>""" % self.PCI_ADDR

        dev = {
            'nicModel': 'virtio', 'macAddr': '52:54:00:59:F5:3F',
            'network': 'ovirtmgmt', 'address': self.PCI_ADDR_DICT,
            'device': 'bridge', 'type': 'interface',
            'bootOrder': '1', 'filter': 'clean-traffic',
            'filterParameters': [
                {'name': 'IP', 'value': '10.0.0.1'},
                {'name': 'IP', 'value': '10.0.0.2'},
            ],
            'vm_custom': {'vhost': 'ovirtmgmt:true', 'sndbuf': '0'},
        }

        iface = vmdevices.network.Interface(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(iface.getXML()), interfaceXML)

    @MonkeyPatch(vmdevices.network.supervdsm,
                 'getProxy', lambda: FakeProxy(
                     ovs_bridge={'name': 'ovirtmgmt', 'dpdk_enabled': False}))
    @MonkeyPatch(vmdevices.network.net_api, 'net2vlan', lambda x: 101)
    def test_interface_on_ovs_with_vlan(self):
        interfaceXML = """
            <interface type="bridge">
                <address %s/>
                <mac address="52:54:00:59:F5:3F"/>
                <model type="virtio"/>
                <source bridge="ovirtmgmt"/>
                <virtualport type="openvswitch" />
                <vlan>
                    <tag id="101" />
                </vlan>
                <filterref filter="no-mac-spoofing"/>
                <boot order="1"/>
                <driver name="vhost" queues="7"/>
                <tune>
                    <sndbuf>0</sndbuf>
                </tune>
            </interface>""" % self.PCI_ADDR

        dev = {
            'nicModel': 'virtio',
            'macAddr': '52:54:00:59:F5:3F',
            'network': 'ovirtmgmt',
            'address': self.PCI_ADDR_DICT,
            'device': 'bridge',
            'type': 'interface',
            'bootOrder': '1',
            'filter': 'no-mac-spoofing',
            'custom': {'queues': '7'},
            'vm_custom': {'vhost': 'ovirtmgmt:true', 'sndbuf': '0'},
        }
        iface = vmdevices.network.Interface(self.log, **dev)
        self.assertXMLEqual(vmxml.format_xml(iface.getXML()), interfaceXML)

    @permutations([
        # base_spec_params:
        [{}],
        [{'inbound': {'average': 512}, 'outbound': {'average': 512}}],
    ])
    def test_update_bandwidth_xml(self, base_spec_params):
        specParams = {
            'inbound': {
                'average': 1000,
                'peak': 5000,
                'floor': 200,
                'burst': 1024,
            },
            'outbound': {
                'average': 128,
                'peak': 256,
                'burst': 256,
            },
        }
        conf = {
            'device': 'network',
            'macAddr': 'fake',
            'network': 'default',
            'specParams': base_spec_params,
        }
        XML = u"""
        <interface type='network'>
          <mac address="fake" />
          <source bridge='default'/>
          <bandwidth>
            <inbound average='1000' peak='5000' floor='200' burst='1024'/>
            <outbound average='128' peak='256' burst='256'/>
          </bandwidth>
        </interface>
        """
        with MonkeyPatchScope([
            (vmdevices.network.supervdsm, 'getProxy', lambda: FakeProxy())
        ]):
            dev = vmdevices.network.Interface(self.log, **conf)
            vnic_xml = dev.getXML()
            vmdevices.network.update_bandwidth_xml(dev, vnic_xml, specParams)
            self.assertXMLEqual(vmxml.format_xml(vnic_xml), XML)


@expandPermutations
class ParsingHelperTests(XMLTestCase):

    ADDR = {
        'domain': '0x0000',
        'bus': '0x05',
        'slot': '0x11',
        'function': '0x3',
    }

    ALIAS = 'test0'

    def test_address_alias(self):
        params = {'alias': self.ALIAS}
        params.update(self.ADDR)
        XML = u"""<device type='fake'>
          <address domain='{domain}' bus='{bus}'
            slot='{slot}' function='{function}'/>
          <alias name='{alias}'/>
        </device>""".format(**params)
        found_addr, found_alias = vmdevices.core.parse_device_ident(
            vmxml.parse_xml(XML))
        self.assertEqual(found_addr, self.ADDR)
        self.assertEqual(found_alias, self.ALIAS)

    def test_missing_address(self):
        XML = u"""<device type='fake'>
          <alias name='{alias}'/>
        </device>""".format(alias=self.ALIAS)
        found_addr, found_alias = vmdevices.core.parse_device_ident(
            vmxml.parse_xml(XML))
        self.assertIs(found_addr, None)
        self.assertEqual(found_alias, self.ALIAS)

    def test_missing_alias(self):
        params = self.ADDR.copy()
        XML = u"""<device type='fake'>
          <address domain='{domain}' bus='{bus}'
            slot='{slot}' function='{function}'/>
        </device>""".format(**params)
        found_addr, found_alias = vmdevices.core.parse_device_ident(
            vmxml.parse_xml(XML))
        self.assertEqual(found_addr, self.ADDR)
        self.assertEqual(found_alias, '')

    def test_missing_address_alias(self):
        XML = u"<device type='fake' />"
        found_addr, found_alias = vmdevices.core.parse_device_ident(
            vmxml.parse_xml(XML))
        self.assertIs(found_addr, None)
        self.assertEqual(found_alias, '')

    def test_attrs(self):
        XML = u"<device type='fake' />"
        attrs = vmdevices.core.parse_device_attrs(
            vmxml.parse_xml(XML), ('type',)
        )
        self.assertEqual(attrs, {'type': 'fake'})

    def test_attrs_missing(self):
        XML = u"<device type='fake' />"
        attrs = vmdevices.core.parse_device_attrs(
            vmxml.parse_xml(XML), ('type', 'foo')
        )
        self.assertEqual(attrs, {'type': 'fake'})

    def test_attrs_partial(self):
        XML = u"<device foo='bar' ans='42' fizz='buzz' />"
        attrs = vmdevices.core.parse_device_attrs(
            vmxml.parse_xml(XML), ('foo', 'fizz')
        )
        self.assertEqual(attrs, {'foo': 'bar', 'fizz': 'buzz'})

    @permutations([
        # xml_data, dev_type
        [u'''<interface type='network' />''', 'network'],
        [u'''<console type="pty" />''', 'pty'],
        [u'''<controller type='usb' index='0' />''', 'usb'],
        [u'''<sound model="ac97"/>''', 'sound'],
        [u'''<tpm model='tpm-tis'/>''', 'tpm'],
    ])
    def test_parse_device_type(self, xml_data, dev_type):
        self.assertEqual(
            dev_type,
            vmdevices.core.parse_device_type(vmxml.parse_xml(xml_data))
        )

    @permutations([
        # xml_data, alias
        # well formed XMLs
        [u'''<interface><alias name="net0" /></interface>''', 'net0'],
        [u'''<console type="pty" />''', ''],
        # malformed XMLs
        [u'''<controller><alias>foobar</alias></controller>''', ''],
    ])
    def test_find_device_alias(self, xml_data, alias):
        self.assertEqual(
            alias,
            vmdevices.core.find_device_alias(vmxml.parse_xml(xml_data))
        )


class FakeProxy(object):

    def __init__(self, ovs_bridge=None):
        self._ovs_bridge = ovs_bridge

    def ovs_bridge(self, name):
        return self._ovs_bridge

    def appropriateHwrngDevice(self, vmid):
        pass

    def rmAppropriateHwrngDevice(self, vmid):
        pass


class FakeSupervdsm(object):

    def __init__(self, ovs_bridge=None):
        self._ovs_bridge = ovs_bridge

    def getProxy(self):
        return self

    def ovs_bridge(self, name):
        return self._ovs_bridge


# the alias is not rendered by getXML, so having it would make
# the test fail
_CONTROLLERS_XML = [
    [u"<controller type='virtio-serial' index='0' ports='16'>"
     u"<address type='pci' domain='0x0000' bus='0x00'"
     u" slot='0x07' function='0x0'/>"
     u"</controller>"],
    [u"<controller type='usb' index='0'>"
     u"<address type='pci' domain='0x0000' bus='0x00'"
     u" slot='0x01' function='0x2'/>"
     u"</controller>"],
    [u"<controller type='pci' index='0' model='pci-root' />"],
    [u"<controller type='ccid' index='0' />"],
    [u"<controller type='ide' index='0'/>"],
    [u"<controller type='scsi' index='0' model='virtio-scsi'>"
     u"<address type='pci' domain='0x0000' bus='0x00' slot='0x0b'"
     u" function='0x0'/>"
     u"<driver iothread='4'/>"
     u"</controller>"],
]

_GRAPHICS_DATA = [
    # graphics_xml, display_ip, meta, src_ports, expected_ports
    # listen on address, both port requested, some features disabled
    [
        u'''<graphics type='spice' port='{port}' tlsPort='{tls_port}'
                  autoport='yes' keymap='en-us'
                  defaultMode='secure' passwd='*****'
                  passwdValidTo='1970-01-01T00:00:01'>
          <clipboard copypaste='no'/>
          <filetransfer enable='no'/>
          <listen type='address' address='127.0.0.1'/>
        </graphics>''',
        '127.0.0.1',
        {'display_network': 'ovirt-test'},
        {'port': '5900', 'tls_port': '5901'},
        {'port': '-1', 'tls_port': '-1'},
    ],
    # listen on address, only insecure port requested
    [
        u'''<graphics type='vnc' port='{port}' autoport='yes'
                  keymap="en-us"
                  defaultMode="secure" passwd="*****"
                  passwdValidTo='1970-01-01T00:00:01'>
          <listen type='address' address='127.0.0.1'/>
        </graphics>''',
        '127.0.0.1',
        {'display_network': 'ovirt-test'},
        {'port': '5900', 'tls_port': '5901'},
        {'port': '-1', 'tls_port': '-1'},
    ],
    # listening on network
    [
        u'''<graphics type='vnc' port='{port}' autoport='yes'
                   keymap='en-us'
                   defaultMode="secure" passwd="*****"
                   passwdValidTo='1970-01-01T00:00:01'>
           <listen type='network' network='vdsm-ovirtmgmt'/>
        </graphics>''',
        '192.168.1.1',
        {},
        {'port': '5900', 'tls_port': '5901'},
        {'port': '-1', 'tls_port': '-1'},
    ],
    # listening on network, preserving autoselect
    [
        u'''<graphics type='vnc' port='{port}' autoport='yes'
                   keymap='en-us'
                   defaultMode="secure" passwd="*****"
                   passwdValidTo='1970-01-01T00:00:01'>
           <listen type='network' network='vdsm-ovirtmgmt'/>
        </graphics>''',
        '192.168.1.1',
        {},
        {'port': '-1', 'tls_port': '-1'},
        {'port': '-1', 'tls_port': '-1'},
    ],

]


@expandPermutations
class DeviceXMLRoundTripTests(XMLTestCase):

    def test_generic(self):
        # simplified version of channel XML, only for test purposes.
        # this should never be seen in the wild
        generic_xml = '<channel type="spicevmc" />'
        self._check_roundtrip(vmdevices.core.Generic, generic_xml)

    @permutations([
        # sound_xml
        [u'''<sound model="ac97"/>'''],
        [u'''<sound model='es1370'/>'''],
    ])
    def test_sound(self, sound_xml):
        self._check_roundtrip(vmdevices.core.Sound, sound_xml)

    def test_balloon(self):
        balloon_xml = u'''<memballoon model='virtio'>
          <address type='pci' domain='0x0000' bus='0x00' slot='0x04'
           function='0x0'/>
        </memballoon>'''
        self._check_roundtrip(vmdevices.core.Balloon, balloon_xml)

    @permutations([
        # console_type, is_serial
        ['virtio', False],
        ['serial', True],
    ])
    def test_console_pty(self, console_type, is_serial):
        console_xml = u'''<console type="pty">
            <target port="0" type="%s" />
        </console>''' % console_type
        self._check_roundtrip(
            vmdevices.core.Console, console_xml, meta={'vmid': 'VMID'}
        )

    @permutations([
        # console_type, is_serial
        ['virtio', False],
        ['serial', True],
    ])
    def test_console_pty_properties(self, console_type, is_serial):
        console_xml = u'''<console type="pty">
            <target port="0" type="%s" />
        </console>''' % console_type
        dev = vmdevices.core.Console.from_xml_tree(
            self.log,
            vmxml.parse_xml(console_xml),
            meta={'vmid': 'VMID'}
        )
        self.assertEqual(dev.isSerial, is_serial)

    @permutations([
        # console_type, is_serial
        ['virtio', False],
        ['serial', True],
    ])
    def test_console_unix_socket(self, console_type, is_serial):
        vmid = 'VMID'
        console_xml = u'''<console type='unix'>
          <source mode='bind' path='{sockpath}.sock' />
          <target type='{console_type}' port='0' />
        </console>'''.format(
            sockpath=os.path.join(constants.P_OVIRT_VMCONSOLES, vmid),
            console_type=console_type
        )
        self._check_roundtrip(
            vmdevices.core.Console, console_xml, meta={'vmid': vmid}
        )

    @permutations([
        # console_type, is_serial
        ['virtio', False],
        ['serial', True],
    ])
    def test_console_unix_socket_properties(self, console_type, is_serial):
        vmid = 'VMID'
        console_xml = u'''<console type='unix'>
          <source mode='bind' path='{sockpath}.sock' />
          <target type='{console_type}' port='0' />
        </console>'''.format(
            sockpath=os.path.join(constants.P_OVIRT_VMCONSOLES, vmid),
            console_type=console_type
        )
        dev = vmdevices.core.Console.from_xml_tree(
            self.log,
            vmxml.parse_xml(console_xml),
            meta={'vmid': vmid}
        )
        self.assertEqual(dev.isSerial, is_serial)
        self.assertEqual(dev.vmid, vmid)
        self.assertTrue(dev.specParams['enableSocket'])

    @permutations(_CONTROLLERS_XML)
    def test_controller(self, controller_xml):
        self._check_roundtrip(vmdevices.core.Controller, controller_xml)

    def test_smartcard(self):
        smartcard_xml = u'''<smartcard mode='passthrough' type='spicevmc'>
            <address type='ccid' controller='0' slot='0'/>
        </smartcard>'''
        self._check_roundtrip(vmdevices.core.Smartcard, smartcard_xml)

    def test_redir(self):
        redir_xml = u'''<redirdev bus='usb' type='spicevmc'>
          <address type='usb' bus='0' port='1'/>
        </redirdev>'''
        self._check_roundtrip(vmdevices.core.Redir, redir_xml)

    def test_video(self):
        video_xml = u'''<video>
          <address type='pci' domain='0x0000'
           bus='0x00' slot='0x02' function='0x0'/>
          <model type='qxl' ram='65536' vram='32768' vgamem='16384' heads='1'/>
        </video>'''
        self._check_roundtrip(vmdevices.core.Video, video_xml)

    @MonkeyPatch(vmdevices.core.supervdsm,
                 'getProxy', lambda: FakeProxy())
    def test_rng(self):
        rng_xml = u'''<rng model='virtio'>
            <rate period="2000" bytes="1234"/>
            <backend model='random'>/dev/random</backend>
        </rng>'''
        self._check_roundtrip(
            vmdevices.core.Rng, rng_xml, meta={'vmid': 'VMID'}
        )

    def test_tpm(self):
        tpm_xml = u'''<tpm model='tpm-tis'>
            <backend type='passthrough'>
                <device path='/dev/tpm0' />
            </backend>
        </tpm>'''
        self._check_roundtrip(vmdevices.core.Tpm, tpm_xml)

    def test_watchdog(self):
        watchdog_xml = u'''<watchdog model='i6300esb' action='reset'>
          <address type='pci' domain='0x0000' bus='0x00' slot='0x05'
           function='0x0'/>
        </watchdog>'''
        self._check_roundtrip(vmdevices.core.Watchdog, watchdog_xml)

    def test_memory(self):
        memory_xml = u'''<memory model='dimm'>
            <target>
                <size unit='KiB'>524288</size>
                <node>1</node>
            </target>
            <alias name='dimm0'/>
            <address type='dimm' slot='0' base='0x100000000'/>
        </memory>'''
        self._check_roundtrip(vmdevices.core.Memory, memory_xml)

    def test_lease(self):
        lease_xml = u'''<lease>
            <key>12523e3d-ad22-410c-8977-d2a7bf458a65</key>
            <lockspace>c2a6d7c8-8d81-4e01-9ed4-7eb670713448</lockspace>
            <target offset="1048576"
                    path="/dev/c2a6d7c8-8d81-4e01-9ed4-7eb670713448/leases"/>
        </lease>'''
        self._check_roundtrip(vmdevices.lease.Device, lease_xml)

    @permutations(_GRAPHICS_DATA)
    def test_graphics(self, graphics_xml, display_ip, meta,
                      src_ports, expected_ports):
        meta['vmid'] = 'VMID'
        ovs_bridge = None
        bridge_name = meta.get('display_network')
        if bridge_name is not None:
            ovs_bridge = {'name': bridge_name, 'dpdk_enabled': False}
        with MonkeyPatchScope([
            (vmdevices.graphics, 'supervdsm', FakeSupervdsm(ovs_bridge)),
            (vmdevices.graphics, '_getNetworkIp', lambda net: display_ip),
            (vmdevices.graphics.libvirtnetwork,
                'create_network', lambda net, vmid: None),
            (vmdevices.graphics.libvirtnetwork,
                'delete_network', lambda net, vmid: None),
        ]):
            self._check_roundtrip(
                vmdevices.graphics.Graphics,
                graphics_xml.format(**src_ports),
                meta=meta,
                expected_xml=graphics_xml.format(**expected_ports)
            )

    @MonkeyPatch(vmdevices.network.supervdsm,
                 'getProxy', lambda: FakeProxy())
    def test_interface(self):
        interface_xml = u'''
            <interface type="bridge">
                <address bus="0x00" domain="0x0000"
                    function="0x0" slot="0x03" type="pci"/>
                <mac address="52:54:00:59:F5:3F"/>
                <model type="virtio"/>
                <source bridge="ovirtmgmt"/>
                <filterref filter="no-mac-spoofing"/>
                <boot order="1"/>
                <driver name="vhost" queues="7"/>
                <tune>
                    <sndbuf>0</sndbuf>
                </tune>
                <bandwidth>
                    <inbound average="1000" burst="1024" peak="5000"/>
                    <outbound average="128" burst="256"/>
                </bandwidth>
            </interface>'''
        self._check_roundtrip(vmdevices.network.Interface, interface_xml)

    def _check_roundtrip(self, klass, dev_xml, meta=None, expected_xml=None):
        dev = klass.from_xml_tree(
            self.log,
            vmxml.parse_xml(dev_xml),
            {} if meta is None else meta
        )
        dev.setup()
        try:
            rebuilt_xml = vmxml.format_xml(dev.getXML(), pretty=True)
            # make troubleshooting easier
            print(rebuilt_xml)
            result_xml = dev_xml if expected_xml is None else expected_xml
            self.assertXMLEqual(rebuilt_xml, result_xml)
        finally:
            dev.teardown()
