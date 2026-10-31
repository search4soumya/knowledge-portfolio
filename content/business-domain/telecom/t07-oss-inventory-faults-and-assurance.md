---
id: T07
domain: telecom
category: Operations
title: "OSS: inventory, faults, and assurance"
slug: oss-inventory-faults-and-assurance
order: 7
---

OSS is how the operator knows what the network *is* and whether it is *ok*. Inventory without assurance is a spreadsheet. Assurance without inventory is a storm of alarms with no owner. Together they are the difference between a planned change and an outage you cannot explain.

## Concept

**Resource inventory.** Sites, racks, cards, ports, wavelengths, VLANs, IP pools, cells, and the logical services that ride them. Planned, reserved, in-service, and retired are different states. An order that reserved a port last week owns that port until it is released. If inventory and the live device disagree, the live device wins for operations and inventory must be reconciled — not the other way around.

**Service inventory.** The customer-facing instance: this subscription uses this APN, this VLAN, this phone number. Service inventory is how care answers "what does this customer have?" without reading the core like a debugger.

**Fault management.** Devices emit alarms. Correlation turns twenty alarms into one incident ("the aggregation router is down, so these cells are dark"). Severity, clearance, and ticketing must be boring and reliable. A new AI layer that cannot clear a flap will not save you.

**Performance and assurance.** Counters and KPIs: attach success, drop rate, throughput, fiber light levels. SLA reports for enterprises are produced here. Capacity planning reads the same data. If you only look at tickets, you will miss the cell that is slow but not down.

**Workforce.** Some work needs a person: a fiber drop, a card swap, a site visit. The job, the skill, the parts, and the appointment are OSS objects. Digital channels that promise "same-day install" are making a workforce claim.

## Design implications

Discovery from the network should update inventory continuously. Manual-only inventory dies the first time a field engineer patches a port and tells nobody.

Change management (a maintenance window on a router) should suppress the expected alarms and be visible to care. A change that is invisible to the incident system is how you page the wrong team.

Do not feed raw SNMP into the customer app. Feed a service health object: this subscription is degraded because its serving cell is congested. That requires the join from T01: service to resource to metric.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Reconciled inventory plus correlated faults | Any network you cannot hold in one vendor GUI | Integration; you must fund reconciliation |
| Vendor-only OSS | Single-vendor access or core | Multi-vendor and multi-domain go dark |
| Tickets without topology | Small team | You cannot do impact analysis |

Ask how a cell outage becomes a list of affected enterprise circuits and consumer cells. If that list is built by hand, assurance is not a system yet.
