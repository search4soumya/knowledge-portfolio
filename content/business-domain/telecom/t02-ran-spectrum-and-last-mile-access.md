---
id: T02
domain: telecom
category: Network
title: RAN, spectrum, and last-mile access
slug: ran-spectrum-and-last-mile-access
order: 2
---

Access is the part of a telecom network that customers can see and that finance can depreciate. Radio access (RAN), fiber to the home, cable plant, and wholesale last-mile leases are where most of the capital sits. Software teams who have only designed cloud APIs underestimate two things: spectrum is a licensed scarce good, and a cell site is a building with power, backhaul, and a landlord.

## Concept

**Spectrum** is the right to radiate in a band in a geography. Low bands travel far and penetrate walls; they carry fewer bits. Mid bands are the workhorse of 4G and 5G. High bands (mmWave) are short-range capacity. A coverage map is a physics document, not a marketing slide. When a product manager asks for "nationwide 5G for a latency-sensitive app," the access answer is a band plan and a site list, not a Kubernetes namespace.

**RAN** is the radio units, distributed units, and centralized units that turn spectrum into a bearer. Classic RAN kept most of that in a vendor cabinet at the site. Open RAN and vRAN pull some functions into a data center or a far edge. That does not make RAN a microservice. Timing, fronthaul bandwidth, and vendor interop still dominate. A site that loses GPS sync is a radio outage, not an application retry.

**Backhaul** is the circuit from the site to the aggregation site or the core. Microwave, dark fiber, or a leased Ethernet line. If backhaul is congested, the cell looks "down" to the user even when the radio is fine. Capacity planning is therefore radio *and* transport.

**Fixed access** (GPON, XGS-PON, DOCSIS, Ethernet) has a different inventory: optical line terminals, splitters, taps, drop cables, customer premises equipment. The business process is similar — qualify an address, reserve a port, dispatch a technician — but the objects are not cells.

## How this shows up in systems

Inventory must know every site, sector, antenna, and fiber strand, including what is planned versus live. Activation for mobile is usually "provision the SIM and the core"; activation for fiber is a truck roll and a port on an OLT. Do not force both through the same "create resource" API unless the API can represent a human visit and a physical port reservation.

Performance management collects counters from every cell and every OLT port. Those counters are the truth about congestion. A digital channel that promises a speed tier without reading those counters will oversell.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Vendor-integrated RAN | Fast rollout, one throat to choke | Lock-in; hard to mix radios and baseband |
| Open / vRAN | You want to place compute and shop vendors | Integration, timing, and a skilled ops team |
| Lease last-mile instead of building | MVNO or a new city | You do not control coverage or repair time |

Ask what physical resource is reserved when the customer clicks Buy. If the answer is only a row in a catalog, access will fail the order after the money is taken.
