"""RFC 792 router error wire format + actual routed error delivery to source."""
import copy
import hashlib
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from network_core.icmp_errors import (
    ICMPError, ICMP_DEST_UNREACHABLE, ICMP_TIME_EXCEEDED,
    parse_icmp_message,
)
from network_core.icmp import ICMPEcho
from network_core.icmp_ping import EchoExchange
from network_core.ipv4 import IPv4Trace
from network_core.ipv4_packet import IPv4Datagram, ICMP_PROTOCOL, checksum
from network_core.model import ProjectValidationError
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from test_ipv4_forwarding import lab, getport, multihop
from test_icmp_echo import routed_reply_lab


def sample_quote():
    echo = ICMPEcho(8, 0x0123, 0x4567, b"eight++").serialize()
    ip = IPv4Datagram("192.0.2.10", "203.0.113.20", 1, echo, ICMP_PROTOCOL)
    return ip.serialize()[:28]


def no_router_route():
    p = lab()
    p["nodes"][0]["staticRoutes"][0]["destination"] = "198.51.100.0/24"
    return p


class RouterErrorWireTests(unittest.TestCase):
    def test_rfc792_types_and_exact_original_header_plus_eight_bytes(self):
        quote=sample_quote()
        for kind in (3,11):
            with self.subTest(kind=kind):
                message=ICMPError(kind,0,quote)
                raw=message.serialize()
                self.assertEqual(len(raw),36)
                self.assertEqual(raw[:2],bytes([kind,0]))
                self.assertEqual(raw[4:8],b"\x00"*4)
                self.assertEqual(raw[8:],quote)
                self.assertEqual(checksum(raw),0)
                self.assertEqual(ICMPError.parse(raw),message)
                self.assertEqual(parse_icmp_message(raw),message)
                self.assertEqual(message.quoted_source,"192.0.2.10")
                self.assertEqual(message.quoted_destination,"203.0.113.20")
                self.assertEqual(message.quoted_protocol,1)

    def test_independent_zero_payload_echo_reference_quote(self):
        packet=IPv4Datagram("192.0.2.10","203.0.113.20",1,
                            ICMPEcho(8,0,0,b"").serialize(),ICMP_PROTOCOL)
        error=ICMPError(11,0,packet.serialize()[:28])
        raw=error.serialize()
        self.assertEqual(raw[8:28],packet.serialize()[:20])
        self.assertEqual(raw[28:36],bytes.fromhex("0800f7ff00000000"))
        self.assertEqual(ICMPError.parse(raw),error)

    def test_corrupt_checksum_unused_field_and_truncation_rejected(self):
        raw=ICMPError(11,0,sample_quote()).serialize()
        bad=[raw[:35],raw+b"\x00",b"",raw[:2]+b"\x00\x00"+raw[4:],
             raw[:4]+b"\x01"+raw[5:],raw[:12]+b"\x01"+raw[13:],
             raw[:19]+b"\x01"+raw[20:],b"\x03"+raw[1:],b"\x0b\x01"+raw[2:]]
        for data in bad:
            with self.subTest(data=str(data[:12])),self.assertRaises(ProjectValidationError):
                ICMPError.parse(data)
        for wrong in ("not-bytes",None,[],bytearray(raw)):
            with self.assertRaises(ProjectValidationError):
                ICMPError.parse(wrong)

    def test_rfc1122_special_address_quotes_rejected_even_with_valid_checksums(self):
        # Independent wire oracle: construct a valid RFC 791 IPv4 header
        # checksum and RFC 792 ICMP checksum around a forbidden IP address.
        # This must reject the address, not accidentally fail the checksum.
        import ipaddress

        for offset in (12, 16):
            for address in ("127.0.0.1", "127.20.30.40",
                            "0.0.0.1", "0.1.2.3"):
                with self.subTest(offset=offset, address=address):
                    quote = bytearray(sample_quote())
                    quote[offset:offset + 4] = ipaddress.IPv4Address(address).packed
                    quote[10:12] = bytes(2)
                    quote[10:12] = checksum(bytes(quote[:20])).to_bytes(2, "big")
                    self.assertEqual(checksum(bytes(quote[:20])), 0)
                    wire = bytes((ICMP_TIME_EXCEEDED, 0, 0, 0)) + bytes(4) + bytes(quote)
                    wire = wire[:2] + checksum(wire).to_bytes(2, "big") + wire[4:]
                    self.assertEqual(checksum(wire), 0)
                    with self.assertRaisesRegex(ProjectValidationError, "unusable original IPv4"):
                        ICMPError(ICMP_TIME_EXCEEDED, 0, bytes(quote))
                    with self.assertRaisesRegex(ProjectValidationError, "unusable original IPv4"):
                        ICMPError.parse(wire)
                    with self.assertRaisesRegex(ProjectValidationError, "unusable original IPv4"):
                        parse_icmp_message(wire)

        # The restriction is only on special wire-invalid addresses, not on
        # valid private or documentation networks commonly used by YadiLab.
        good = bytearray(sample_quote())
        good[12:16] = ipaddress.IPv4Address("192.168.50.10").packed
        good[10:12] = bytes(2)
        good[10:12] = checksum(bytes(good[:20])).to_bytes(2, "big")
        valid = ICMPError(ICMP_TIME_EXCEEDED, 0, bytes(good))
        self.assertEqual(ICMPError.parse(valid.serialize()), valid)

    def test_strict_types_codes_original_ipv4_and_nested_error_guard(self):
        q=sample_quote()
        for kind,code in ((0,0),(8,0),(3,1),(11,1),(11,True),(True,0),(-1,0)):
            with self.subTest(kind=kind,code=code),self.assertRaises(ProjectValidationError):
                ICMPError(kind,code,q)
        for bad in (q[:27],q+b"0",[],None,bytearray(q)):
            with self.subTest(bad=str(bad)[:15]),self.assertRaises(ProjectValidationError):
                ICMPError(11,0,bad)
        invalid=bytearray(q)
        invalid[0]=0x46
        with self.assertRaises(ProjectValidationError):
            ICMPError(3,0,bytes(invalid))
        invalid=bytearray(q)
        invalid[9]=17
        with self.assertRaises(ProjectValidationError):
            ICMPError(3,0,bytes(invalid))
        nested = IPv4Datagram("192.0.2.10","203.0.113.20",1,
                              bytes([11,0,0,0,0,0,0,0]),ICMP_PROTOCOL)
        with self.assertRaisesRegex(ProjectValidationError,"do not generate"):
            ICMPError(11,0,nested.serialize()[:28])


class RouterErrorSimulationTests(unittest.TestCase):
    def test_router_error_quote_requires_eight_original_data_bytes(self):
        # RFC 792's bounded codec needs the IPv4 header plus eight original
        # data octets. A protocol-253 datagram may legally have fewer than eight.
        # Its failed delivery remains observable, but no malformed ICMP error
        # candidate may be claimed.
        project = lab()
        for length in (0, 1, 7):
            with self.subTest(data_length=length):
                result = IPv4Trace(project).send(
                    "a", "eth0", "203.0.113.20", 1,
                    payload=b"x" * length,
                )
                self.assertEqual(result["status"], "TTL_EXPIRED")
                self.assertIsNone(result["routerErrorCandidate"])
                self.assertFalse(result["icmpSent"])
        complete = IPv4Trace(project).send(
            "a", "eth0", "203.0.113.20", 1, payload=b"12345678",
        )
        self.assertEqual(complete["status"], "TTL_EXPIRED")
        candidate = complete["routerErrorCandidate"]
        self.assertIsNotNone(candidate)
        self.assertEqual(len(bytes.fromhex(candidate["quotedIpv4Hex"])), 28)
        self.assertEqual(
            ICMPError(candidate["icmpType"], candidate["icmpCode"],
                      bytes.fromhex(candidate["quotedIpv4Hex"])).icmp_type,
            ICMP_TIME_EXCEEDED,
        )

    def test_no_nested_router_error_candidate_after_ttl_or_missing_route(self):
        # RFC 1812 4.3.2.7: no ICMP error is generated in response to an
        # existing ICMP error. Both original errors are valid wire packets.
        # The failing packet and its real transmissions must remain visible.
        for kind in (ICMP_TIME_EXCEEDED, ICMP_DEST_UNREACHABLE):
            payload = ICMPError(kind, 0, sample_quote()).serialize()
            for failure in ("TTL_EXPIRED", "NO_ROUTE"):
                with self.subTest(original_error=kind, failure=failure):
                    project = lab()
                    if failure == "NO_ROUTE":
                        getport(project, "r", "lan")["enabled"] = False
                    trace = IPv4Trace(project).send(
                        "a", "eth0", "203.0.113.20",
                        1 if failure == "TTL_EXPIRED" else 5,
                        protocol=ICMP_PROTOCOL, payload=payload,
                    )
                    self.assertEqual(trace["status"], failure)
                    self.assertIsNone(trace["routerErrorCandidate"])
                    self.assertEqual([step["node"] for step in trace["steps"]], ["a"])
                    self.assertEqual(
                        [wire["linkId"] for wire in trace["steps"][0]["ipv4Transmissions"]],
                        ["la", "lr1"],
                    )
                    self.assertTrue(trace["icmpSent"])

        # ICMP Echo is an informational message, not an ICMP error.
        # A router may still report an expired TTL for an Echo datagram.
        echo = ICMPEcho(8, 7, 9, b"payload!").serialize()
        allowed = IPv4Trace(lab()).send(
            "a", "eth0", "203.0.113.20", 1,
            protocol=ICMP_PROTOCOL, payload=echo,
        )
        self.assertEqual(allowed["status"], "TTL_EXPIRED")
        self.assertEqual(allowed["routerErrorCandidate"]["icmpType"], ICMP_TIME_EXCEEDED)

    def test_real_ttl_expired_router_sends_received_type11_reply(self):
        p=routed_reply_lab()
        before=copy.deepcopy(p)
        result=EchoExchange(p).ping("a","eth0","203.0.113.20",1,12,44)
        self.assertEqual(result["status"],"REQUEST_FAILED")
        self.assertFalse(result["replyMatched"])
        self.assertIsNone(result["reply"])
        self.assertEqual(result["request"]["status"],"TTL_EXPIRED")
        self.assertEqual([step["node"] for step in result["request"]["steps"]],["a"])
        error=result["icmpError"]
        self.assertIsNotNone(error)
        self.assertEqual(error["type"],ICMP_TIME_EXCEEDED)
        self.assertEqual(error["code"],0)
        self.assertEqual(error["status"],"RECEIVED")
        self.assertEqual(error["sourceNode"],"r")
        self.assertEqual(error["sourcePort"],"wan")
        self.assertEqual(error["trace"]["status"],"DELIVERED")
        self.assertEqual(error["trace"]["sourceIpv4"],"192.0.2.1")
        self.assertEqual(error["trace"]["receiver"],{"node":"a","port":"eth0"})
        self.assertEqual(error["quotedSourceIpv4"],"192.0.2.10")
        self.assertEqual(error["quotedDestinationIpv4"],"203.0.113.20")
        self.assertEqual(error["trace"]["deliveredDatagram"]["protocol"],1)
        self.assertTrue(error["trace"]["icmpSent"])
        self.assertEqual([v["linkId"] for v in error["trace"]["steps"][0]["ipv4Transmissions"]],
                         ["lr1","la"])
        self.assertEqual(p,before)

    def test_no_route_at_real_router_sends_received_type3_code0(self):
        p=no_router_route()
        result=EchoExchange(p).ping("a","eth0","198.51.100.20",4,2,9)
        self.assertEqual(result["status"],"REQUEST_FAILED")
        self.assertEqual(result["request"]["status"],"NO_ROUTE")
        error=result["icmpError"]
        self.assertIsNotNone(error)
        self.assertEqual(error["type"],ICMP_DEST_UNREACHABLE)
        self.assertEqual(error["code"],0)
        self.assertEqual(error["status"],"RECEIVED")
        self.assertEqual(error["trace"]["status"],"DELIVERED")
        self.assertEqual(error["trace"]["receiver"],{"node":"a","port":"eth0"})
        self.assertEqual(error["quotedDestinationIpv4"],"198.51.100.20")

    def test_error_return_route_wrong_interface_does_not_forge_delivery(self):
        p=routed_reply_lab()
        router=next(n for n in p["nodes"] if n["id"]=="r")
        router["staticRoutes"]=[{
            "id":"misroute-icmp","destination":"192.0.2.10/32",
            "nextHop":"203.0.113.20","outPort":"lan"
        }]
        result=EchoExchange(p).ping("a","eth0","203.0.113.20",1,2,4)
        self.assertEqual(result["request"]["status"],"TTL_EXPIRED")
        self.assertEqual(result["status"],"REQUEST_FAILED")
        self.assertEqual(result["icmpError"]["status"],"NOT_DELIVERED")
        self.assertEqual(result["icmpError"]["trace"]["status"],"SOURCE_INTERFACE_MISMATCH")
        self.assertEqual(result["icmpError"]["trace"]["steps"],[])
        self.assertFalse(result["replyMatched"])

    def test_host_source_no_route_has_no_generated_icmp(self):
        p=lab()
        p["nodes"][0].pop("staticRoutes")
        result=EchoExchange(p).ping("a","eth0","203.0.113.20",4,9,1)
        self.assertEqual(result["request"]["status"],"NO_ROUTE")
        self.assertIsNone(result["request"]["routerErrorCandidate"])
        self.assertIsNone(result["icmpError"])

    def test_arp_failure_without_router_reception_has_no_icmp(self):
        p=lab()
        getport(p,"sw-left","r")["vlan"]={"mode":"access","vlan":20}
        result=EchoExchange(p).ping("a","eth0","203.0.113.20",1,2,3)
        self.assertEqual(result["request"]["status"],"ARP_FAILED")
        self.assertIsNone(result["icmpError"])
        self.assertIsNone(result["reply"])

    def test_successful_echo_has_no_router_error(self):
        result=EchoExchange(routed_reply_lab()).ping("a","eth0","203.0.113.20",4,12,1)
        self.assertEqual(result["status"],"REPLIED")
        self.assertIsNone(result["icmpError"])
        self.assertTrue(result["replyMatched"])

    def test_failed_reverse_echo_without_return_route_not_invented_error(self):
        result=EchoExchange(lab()).ping("a","eth0","203.0.113.20",4,5,8)
        self.assertEqual(result["status"],"REPLY_FAILED")
        self.assertEqual(result["request"]["status"],"DELIVERED")
        self.assertIsNone(result["icmpError"])

    def test_ambiguous_routing_not_reported_as_net_unreachable(self):
        p=lab()
        p["nodes"][0]["staticRoutes"].append({
            "id":"also","destination":"203.0.113.0/24",
            "nextHop":"192.0.2.2","outPort":"eth0"})
        result=EchoExchange(p).ping("a","eth0","203.0.113.20",2,5,8)
        self.assertEqual(result["request"]["status"],"AMBIGUOUS_ROUTE")
        self.assertIsNone(result["icmpError"])

    def test_packet_codec_checks_icmp_error_before_any_arp_frame(self):
        p=lab()
        getport(p,"r","wan").pop("mac")
        trace=IPv4Trace(p)
        valid=ICMPError(11,0,sample_quote()).serialize()
        sent=trace.send("a","eth0","203.0.113.20",5,
                        protocol=ICMP_PROTOCOL,payload=valid)
        self.assertEqual(sent["status"],"ARP_FAILED")
        with self.assertRaisesRegex(ProjectValidationError,"checksum"):
            trace.send("a","eth0","203.0.113.20",5,
                       protocol=ICMP_PROTOCOL,
                       payload=valid[:2]+b"\x00\x00"+valid[4:])


class RouterErrorHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.server=LabHTTPServer(("127.0.0.1",0),ProjectStore(self.root))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=4)
        self.tmp.cleanup()

    def request(self,p):
        req=Request(self.base+"/api/icmp/echo",data=json.dumps(p).encode(),
                    headers={"Content-Type":"application/json"})
        try:
            with urlopen(req,timeout=10) as r:
                return r.status,json.loads(r.read())
        except HTTPError as e:
            return e.code,json.loads(e.read())

    def body(self,project=None,target="203.0.113.20",ttl=1):
        return {"project":project if project is not None else routed_reply_lab(),
                "sourceNode":"a","sourcePort":"eth0",
                "destinationIpv4":target,"ttl":ttl,"identifier":3,"sequence":7}

    def test_real_http_type11_reply_and_type3_unreachable(self):
        status,d=self.request(self.body())
        self.assertEqual(status,200)
        self.assertEqual(d["status"],"REQUEST_FAILED")
        self.assertEqual(d["icmpError"]["status"],"RECEIVED")
        self.assertEqual(d["icmpError"]["type"],11)
        self.assertFalse(d["replyMatched"])
        status,d=self.request(self.body(no_router_route(),"198.51.100.20",4))
        self.assertEqual(status,200)
        self.assertEqual(d["icmpError"]["status"],"RECEIVED")
        self.assertEqual(d["icmpError"]["type"],3)
        self.assertEqual(d["icmpError"]["code"],0)

    def test_real_http_time_exceeded_error_lost_on_return_has_no_nested_candidate(self):
        # a -> r -> r2: original Echo expires at r2. The resulting type 11
        # travels back via r, which has no route to a because its ingress
        # interface is deliberately narrower. Preserve the actual ICMP error
        # transmission and NO_ROUTE without proposing an error in reply.
        project = multihop()
        getport(project, "r", "wan")["ipv4"] = "192.0.2.1/30"
        r2 = next(node for node in project["nodes"] if node["id"] == "r2")
        r2["staticRoutes"] = [{
            "id": "icmp-return-via-r",
            "destination": "192.0.2.10/32",
            "nextHop": "203.0.113.1",
            "outPort": "in",
        }]
        original = copy.deepcopy(project)
        status, response = self.request(self.body(
            project, "198.51.100.20", 2,
        ))
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "REQUEST_FAILED")
        self.assertEqual(response["request"]["status"], "TTL_EXPIRED")
        error = response["icmpError"]
        self.assertEqual(error["type"], ICMP_TIME_EXCEEDED)
        self.assertEqual(error["status"], "NOT_DELIVERED")
        returned = error["trace"]
        self.assertEqual(returned["status"], "NO_ROUTE")
        self.assertIsNone(returned["routerErrorCandidate"])
        self.assertEqual([step["node"] for step in returned["steps"]], ["r2"])
        self.assertTrue(returned["steps"][0]["ipv4Transmissions"])
        self.assertTrue(returned["icmpSent"])
        self.assertEqual(project, original)

    def test_real_http_no_router_reception_does_not_claim_error(self):
        p=lab()
        getport(p,"sw-left","r")["vlan"]={"mode":"access","vlan":20}
        status,d=self.request(self.body(p))
        self.assertEqual(status,200)
        self.assertEqual(d["request"]["status"],"ARP_FAILED")
        self.assertIsNone(d["icmpError"])
        self.assertFalse(d["replyMatched"])

    def test_http_error_diagnostics_never_write_stored_document(self):
        p=routed_reply_lab()
        original=copy.deepcopy(p)
        saved=self.server.store.save("router-errors",p)
        raw=(self.root/"router-errors.yadilab").read_bytes()
        sha=hashlib.sha256(raw).hexdigest()
        self.assertEqual(saved["sha256"],sha)
        for _ in range(3):
            code,d=self.request(self.body(p))
            self.assertEqual(code,200)
            self.assertEqual(d["icmpError"]["status"],"RECEIVED")
        self.assertEqual(p,original)
        self.assertEqual(raw,(self.root/"router-errors.yadilab").read_bytes())
        self.assertEqual(self.server.store.read("router-errors")["sha256"],sha)


if __name__=="__main__":
    unittest.main()
