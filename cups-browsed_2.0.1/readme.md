## explo/cups-browsed
#### CVE-2024-47076, CVE-2024-47175, CVE-2024-47176, CVE-2024-47177

### Sources
- [evilsocket/Attacking UNIX Systems via CUPS, Part I](https://www.evilsocket.net/2024/09/26/Attacking-UNIX-systems-via-CUPS-Part-I/)
- [cups-browsed Security Advisory](https://github.com/OpenPrinting/cups-browsed/security/advisories/GHSA-rj88-6mr5-rcw8)
- [OpenPrinting News Flash - cups-browsed Remote Code Execution vulnerability](https://openprinting.github.io/OpenPrinting-News-Flash-cups-browsed-Remote-Code-Execution-vulnerability)
- [RFC 2911](https://datatracker.ietf.org/doc/html/rfc291)
- [OpenPrinting/cups-browsed Patch](https://github.com/OpenPrinting/cups-browsed/commit/1d1072a0de573b7850958df614e9ec5b73ea0e0d)

----

Setting printer attributes based on the [ippserver](https://github.com/h2g2bob/ipp-server/blob/3e4a6d8aad4409c280c6df2d1718b3803e38e813/ippserver/behaviour.py#L206) python library allows a rouge printer to be created with custom attributes. An example of this is given in [cups-browsed Security Advisory](https://github.com/OpenPrinting/cups-browsed/security/advisories/GHSA-rj88-6mr5-rcw8).

[RFC 2911](https://datatracker.ietf.org/doc/html/rfc2911), namely [Section 4.2.11](https://datatracker.ietf.org/doc/html/rfc2911#section-4.2.11) yields useful information about printer attributes used to identify `'the medium that the Printer uses for all impressions of the Job'`. 
<pre>
There is also an additional Printer attribute named "media-ready"
which differs from "media-supported" in that legal values only
include the subset of "media-supported" values that are physically
loaded and ready for printing with no operator intervention required. 
If an IPP object supports "media-supported", it NEED NOT support
"media-ready".</pre>

<br>

Referencing back to [evilsocket/Attacking UNIX Systems via CUPS, Part I](https://www.evilsocket.net/2024/09/26/Attacking-UNIX-systems-via-CUPS-Part-I/), `'media-supported'` served as an injection template for the foomatic-rip arbitrary remote command execution (CVE-2024-47177 | cups-filters), which essentially allowed command invocation via the printer's attributes.

---- 

Exploitation of `CVE-2024-47176 | cups-browsed` (i.e. `binds on UDP INADDR_ANY:631 trusting any packet from any source to trigger a Get-Printer-Attributes IPP request to an attacker controlled URL.`) only served useful for printer service discovery in local networks. As such, [Zerconf](https://github.com/python-zeroconf/python-zeroconf) was leveraged to create a rogue IPP service over TCP, broadcasting it to mDNS/Bonjour for discovery. With this in place, by sending the malicious UDP packet (`CVE-2024-47176`) the target is linked to the rogue printer. 

Subsequent print requests will force the printer attributes to be written to a PPD file and assuming the `FoomaticRIPCommandLine` PPD parameter is present, arbitrary command execution occurs (`CVE-2024-47076`/`CVE-2024-47175`/`CVE-2024-47177`).

----

As per [OpenPrinting/Overhyped](https://openprinting.github.io/OpenPrinting-News-Flash-cups-browsed-Remote-Code-Execution-vulnerability/#overhyped), `CUPS/cups-browsed setups are there usually only in NAT-protected local networks with desktop machines and print servers.`.`In addition, the remote code execution only happens when a user actually prints a job on the fake printer. Actually assigned scores ended up between 8.4 and 9.1.`.

As of, `Oct 1 2024`, `Legacy CUPS browsing is not needed any more by cups-browsed`. Assuming your [packages](./ubuntu22.04.1_packages.txt) are up-to-date, the patch is already present ([help](https://openprinting.github.io/OpenPrinting-News-Flash-cups-browsed-Remote-Code-Execution-vulnerability/#what-should-you-do-to-get-protected)).