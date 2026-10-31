---
id: T03
domain: telecom
category: Network
title: Packet core, IMS, and session control
slug: packet-core-ims-and-session-control
order: 3
---

Once a device attaches, the core decides who it is, what it may do, and where its packets go. Voice that used to be a circuit is now a session in IMS on top of that packet path. The core is the system of record for *sessions*. BSS is the system of record for *contracts*. Confusing those two is how you get a phone that has a live bearer and a cancelled bill, or a paid bill and no data.

## Concept

**Attach and authentication.** The device presents an identity (IMSI / SUPI via the SIM). The core asks the subscriber database (HSS / UDM) for authentication vectors, runs AKA, and only then creates a session. If this hop is down, the radio can be perfect and nobody can register. High availability here is not optional decoration.

**Session and mobility.** In 4G the MME and SGW/PGW hold the session. In 5G the AMF, SMF, and UPF split control and user plane. The user plane (SGW/PGW-U or UPF) is the place packets are forwarded and where you can apply charging and policy taps. Mobility means the session survives a cell change. That is why core state is sticky and why "stateless like a web tier" is the wrong default.

**Policy and charging control.** PCRF / PCF tells the user plane the QoS and the charging rule: throttle video, allow a zero-rated partner, cut data when the prepaid wallet is empty. The decision is often real time. The enforcement is in the packet path. The wallet lives in charging (BSS). The interface between them is a contract you will debug at 2 a.m.

**IMS and voice.** VoLTE and VoNR are SIP sessions anchored in IMS (CSCF, TAS, MGCF for breakout). Voice quality is a QoS bearer plus a SIP dialog. Emergency calling, lawful intercept, and number portability all attach here. A "voice app" that bypasses IMS may be a product; it is not a substitute for the regulated telephony path.

## Design implications

Keep control plane and user plane separable so you can scale packet forwarding without cloning every SIP stack. Keep subscriber data (UDM/HSS) off the application team's CRM database. When you expose a network API to an enterprise — quality on demand, a slice, a private APN — you are exposing a session and policy object, not a REST resource that can be eventually consistent with a 30-second cache.

Lawful intercept and emergency services are not features you add after launch. They are constraints on how you log, how you route, and which vendor functions you are allowed to skip.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Vendor EPC / 5GC appliance | Predictable attach, certified features | Slow change; capacity steps are expensive |
| Cloud-native 5GC | Elastic user plane, CI for some functions | You now operate a telco-grade Kubernetes plus a core |
| OTT voice instead of IMS | Consumer chat, not the phone number | Regulators, emergency, and interconnect still want IMS |

In a review, draw one attach, one data session, and one voice call. Name the function that holds state for each. If a box is labeled "microservices," ask which of those three states it is allowed to lose.
