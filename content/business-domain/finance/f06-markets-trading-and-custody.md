---
id: F06
domain: finance
category: Payments
title: Markets, trading, and custody
slug: markets-trading-and-custody
order: 6
---

Markets businesses buy and sell instruments and hold them for clients or for the house. The objects are orders, executions, positions, cash, and safekeeping. Latency and matching get the blog posts. The failures that close firms are position breaks, failed settlements, and a custody book that does not match the depository.

## Concept

**Order and execution.** A client or a desk places an order. A venue or a dealer executes. The fill has a price, a quantity, and a time. Your order management must be able to say what was requested versus what was done. Partial fills are normal.

**Position and PnL.** Positions are long or short by instrument, book, and account. Intraday PnL is mark-to-market. Official PnL is a close. If the trading UI and the books disagree, the books win and the UI is wrong.

**Settlement.** T+1 or T+2, delivery versus payment, a CSD or a custodian. A trade that executed is not a trade that settled. Fails, buy-ins, and corporate actions (splits, dividends) change positions without a new customer order.

**Custody.** Who holds the asset, in whose name, with what segregation. Client assets are not the firm's inventory. Mixing them is how you get a famous insolvency. Your data model must tag beneficial owner and safekeeping place.

## Design implications

Idempotent order ids and execution ids. Market connections replay. A duplicate fill is a wrong position.

Corporate actions are a product. A system that only stores "quantity of AAPL" will break on a split. Keep instrument reference data as a dated object.

Retail brokerage is still this model, with a simpler venue set and a heavier compliance wrapper (suitability, pattern day trader, best execution disclosures). Do not invent a "shares wallet" that cannot process a dividend.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| OMS plus position plus custody, reconciled to market | Any real broker or asset manager | Expensive, correct |
| Display-only prices, no books | A content app | You are not a broker |
| Omnibus everything | Operational ease | You cannot prove segregation |

Ask where a fill becomes a position, where a position becomes a settlement instruction, and how client assets are labeled. If those are one Mongo collection, you have a demo desk, not a market franchise.
