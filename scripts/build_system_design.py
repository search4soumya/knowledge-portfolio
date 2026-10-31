"""Rebuild System Design case studies with blueprints and module notes."""

from __future__ import annotations

import html
import json
from pathlib import Path


def svg_blueprint(layers: list[tuple[str, list[str]]]) -> str:
    width = 920
    left = 108
    row_h = 92
    top = 22
    height = top + len(layers) * row_h + 18
    usable = width - left - 24
    parts = [
        f'<svg class="blueprint-svg" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="System blueprint">'
        f'<rect width="{width}" height="{height}" fill="#0a0e17" rx="10"/>'
    ]
    centers: list[list[tuple[float, float]]] = []
    for row, (label, names) in enumerate(layers):
        y = top + row * row_h
        parts.append(
            f'<text x="18" y="{y + 38}" fill="#f59e0b" font-size="12" '
            f'font-family="Consolas, monospace">{html.escape(label)}</text>'
        )
        count = max(1, len(names))
        box_w = min(196, (usable - (count - 1) * 12) / count)
        gap = 12
        total = count * box_w + (count - 1) * gap
        start = left + (usable - total) / 2
        row_centers: list[tuple[float, float]] = []
        for index, name in enumerate(names):
            x = start + index * (box_w + gap)
            cx, cy = x + box_w / 2, y + 34
            row_centers.append((cx, cy + 18))
            parts.append(
                f'<rect x="{x:.1f}" y="{y + 8:.1f}" width="{box_w:.1f}" height="52" '
                'rx="8" fill="#1a2234" stroke="#10b981" stroke-width="1.4"/>'
            )
            label_y = y + 39
            text = html.escape(name)
            parts.append(
                f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                f'fill="#f8fafc" font-size="11" font-family="Segoe UI, sans-serif">{text}</text>'
            )
        centers.append(row_centers)
        if row:
            for x1, y1 in centers[row - 1]:
                x2 = sum(x for x, _ in row_centers) / len(row_centers)
                y2 = row_centers[0][1] - 26
                parts.append(
                    f'<path d="M{x1:.1f} {y1 - 18:.1f} L{x1:.1f} {y1 + 6:.1f} '
                    f'L{x2:.1f} {y2:.1f}" fill="none" stroke="#64748b" stroke-width="1.1"/>'
                )
    parts.append("</svg>")
    return "".join(parts)


def module_html(index: int, module: dict[str, object]) -> str:
    concepts = "".join(
        f"<li>{html.escape(str(item))}</li>" for item in module["concepts"]
    )
    return (
        f'<section class="module-block" id="{html.escape(str(module["anchor"]))}">'
        f"<h3>{index}. {html.escape(str(module['name']))}</h3>"
        f"<p>{html.escape(str(module['context']))}</p>"
        f'<p class="module-concepts-label">Core concepts in this module</p>'
        f'<ul class="concept-list">{concepts}</ul>'
        "</section>"
    )


def article_html(system: dict[str, object]) -> str:
    layers: list[tuple[str, list[str]]] = [
        (str(label), [str(name) for name in names])
        for label, names in system["layers"]
    ]
    modules = "".join(
        module_html(index, module)
        for index, module in enumerate(system["modules"], start=1)
    )
    concept_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(module['name']))}</td>"
        f"<td>{html.escape(', '.join(str(item) for item in module['concepts']))}</td>"
        "</tr>"
        for module in system["modules"]
    )
    return f"""<h2>What this system is solving</h2>
          <p>{html.escape(str(system['summary']))}</p>
          <h2>System blueprint</h2>
          <figure class="blueprint">
            {svg_blueprint(layers)}
            <figcaption>{html.escape(str(system['caption']))}</figcaption>
          </figure>
          <p>{html.escape(str(system['blueprint_note']))}</p>
          <h2>Modules in the blueprint</h2>
          <p>Each box above is a real responsibility. The notes below explain what that module owns, why it exists, and which ideas you should be able to name in an interview or design review.</p>
          {modules}
          <h2>How the modules work together</h2>
          <p>{html.escape(str(system['together']))}</p>
          <div class="table-wrap">
            <table>
              <caption>Core concepts mapped to modules.</caption>
              <thead><tr><th>Module</th><th>Core concepts</th></tr></thead>
              <tbody>{concept_rows}</tbody>
            </table>
          </div>
          <div class="callout"><strong>Key takeaway:</strong> {html.escape(str(system['takeaway']))}</div>"""


SYSTEMS: list[dict[str, object]] = [
    {
        "slug": "twitter-x",
        "label": "Twitter / X",
        "summary": "A social timeline looks simple: write a short post, then read a river of posts from people you follow. The hard part is the imbalance. Reads vastly outnumber writes, a few accounts have tens of millions of followers, and people expect a fresh feed in a few hundred milliseconds. The design therefore splits write work, read work, and search, and it treats celebrity fan-out as a special case.",
        "caption": "Write path on the left of the flow, read path and search on the right, with shared stores at the bottom.",
        "blueprint_note": "The blueprint is a hybrid fan-out design. Ordinary posts are copied toward follower timelines at publish time. Very large accounts stay in a post store and are merged when someone opens the app. Search is a separate index, not a scan of the timeline cache.",
        "layers": [
            ("Clients", ["Mobile app", "Web client"]),
            ("Edge", ["API gateway"]),
            ("Services", ["Tweet service", "Fan-out workers", "Timeline service", "Search service"]),
            ("Data", ["Post store", "Follow graph", "Timeline cache", "Search index"]),
        ],
        "together": "A publish request is authenticated at the gateway, stored by the tweet service, and emitted as an event. Fan-out workers read the follow graph and write compact entries into timeline caches for ordinary followers. A home-timeline request asks the timeline service for those cached IDs, merges recent posts from a small celebrity set, filters deleted or muted content, and returns a cursor. Search never walks the cache; it queries its own inverted index. If a cache is missing, the timeline can be rebuilt from the post store and follow graph.",
        "takeaway": "Optimize the common read by doing work at publish time, then stop doing that work when the follower set becomes too large.",
        "modules": [
            {
                "name": "API gateway",
                "anchor": "api-gateway",
                "context": "Every mobile or web call lands here first. The gateway authenticates the session, applies per-user and per-IP limits, and routes writes to the tweet service and reads to timeline or search. It is also where you terminate TLS and attach a request ID. Keep this layer thin. If it starts composing timelines or talking to every store, one bad deploy can take the product down and you lose a clean place to shed load.",
                "concepts": ["Authentication", "Rate limiting", "Request routing", "Load shedding"],
            },
            {
                "name": "Tweet service",
                "anchor": "tweet-service",
                "context": "This is the source of truth for a post. It validates size and media, assigns a unique sortable ID, writes the post, and publishes an event. It does not walk millions of followers. That keeps the user-facing write fast and makes retries safe: the same client token should create one post, not two. Media binaries belong in object storage; this service stores only metadata and pointers.",
                "concepts": ["Write-ahead persistence", "Unique IDs", "Idempotent create", "Event outbox"],
            },
            {
                "name": "Fan-out workers",
                "anchor": "fan-out-workers",
                "context": "Workers consume the publish event and decide how to distribute it. For a typical account they push a lightweight reference into each follower's timeline cache. For an account with a huge audience they skip the copy and leave the post to be pulled later. This is the push-versus-pull decision. Workers must be able to pause, retry, and rebuild a slice of the graph without blocking the original writer.",
                "concepts": ["Timeline fan-out", "Push vs pull", "Backpressure", "Partial rebuild"],
            },
            {
                "name": "Timeline service",
                "anchor": "timeline-service",
                "context": "The home feed is a merge, not a dump of one list. The service reads cached entries for people you follow, adds recent posts from high-follower accounts, removes content you should not see, and pages with a cursor. Cursor pagination stays stable as new posts arrive; offset pagination does not. This module can be scaled by user shard because one person's feed does not need another person's cache.",
                "concepts": ["Read-time merge", "Cursor pagination", "Visibility filtering", "User sharding"],
            },
            {
                "name": "Search service",
                "anchor": "search-service",
                "context": "Search is a different product from the home feed. It needs an inverted index of terms, hashtags, and sometimes users. Indexing is asynchronous so a publish stays fast. Queries are served from replicas close to the reader. Do not reuse the timeline cache as a search engine; it is ordered by follow graph and time, not by term.",
                "concepts": ["Inverted index", "Async indexing", "Replica reads", "Query ranking"],
            },
            {
                "name": "Post store, follow graph, and caches",
                "anchor": "stores",
                "context": "The post store keeps durable posts. The follow graph answers who should receive or see a post. The timeline cache makes the common home-feed read cheap. The search index makes term lookup cheap. Each store has a different consistency need: a missing cache entry is recoverable, a missing post write is not, and a stale follow edge can leak or hide content. Design expiry, rebuild, and authorization around those differences.",
                "concepts": ["Source of truth vs cache", "Graph lookups", "Cache invalidation", "Hot-key handling"],
            },
        ],
    },
    {
        "slug": "youtube",
        "label": "YouTube",
        "summary": "Video is a two-sided system: creators upload large files that must be processed, and viewers stream those files from a nearby edge with changing network quality. The upload cannot live inside a single application server, and the playback path cannot depend on a long chain of business services. The blueprint therefore splits an asynchronous media pipeline from a cacheable playback path.",
        "caption": "Creators enter through upload and transcoding. Viewers enter through the CDN and playback service.",
        "blueprint_note": "Original bytes are immutable. Derived renditions are produced by workers and published only when complete. The player never downloads one giant file; it reads a manifest and small segments.",
        "layers": [
            ("Clients", ["Creator upload", "Viewer player"]),
            ("Edge", ["Upload API", "Video CDN"]),
            ("Services", ["Upload session", "Transcoder farm", "Catalog", "Playback service"]),
            ("Data", ["Object storage", "Metadata DB", "Job queue", "Manifests"]),
        ],
        "together": "A creator starts a resumable upload session, sends chunks to object storage, and commits. The catalog records a processing video and a worker queue receives a job. Transcoders produce renditions and a manifest. Only then does the catalog mark the video playable. A viewer asks the playback service for an authorized manifest URL; the player fetches segments from the CDN and switches bitrate as the buffer changes. Failed transcodes retry from the original object, not from a half-written output.",
        "takeaway": "Treat video as immutable objects plus an asynchronous pipeline; keep the viewer on a short, cacheable path.",
        "modules": [
            {
                "name": "Upload session",
                "anchor": "upload-session",
                "context": "Large files fail if you ask the browser to POST once. A session issues an upload ID, accepts chunks, records offsets, and lets the client resume. Integrity checks belong here so a retry does not create a second video. When the last chunk arrives, this module writes a completion event instead of transcoding inline. That keeps user-facing latency predictable and isolates a slow encoder from the upload API.",
                "concepts": ["Resumable upload", "Chunk checksums", "Idempotent commit", "Direct-to-storage"],
            },
            {
                "name": "Transcoder farm",
                "anchor": "transcoder-farm",
                "context": "Raw uploads are the wrong shape for phones, TVs, and poor networks. Workers read the original, produce several resolutions and codecs, package segments, and write a manifest. Jobs are pulled from a durable queue so a crashed worker does not lose the video. Outputs should be written to new keys and published atomically. Never overwrite the original; it is the only way to retry or re-encode later.",
                "concepts": ["Transcoding", "Job queues", "Immutable outputs", "Atomic publish"],
            },
            {
                "name": "Catalog",
                "anchor": "catalog",
                "context": "The catalog is the product database: title, owner, visibility, processing state, and pointers to manifests. It is not the video file. Viewers and search read this metadata. A video that is still processing must not appear as ready. Privacy and takedown checks belong here so a CDN URL is not enough to watch a private upload.",
                "concepts": ["Metadata vs blob", "State machine", "Authorization", "Eventual listing"],
            },
            {
                "name": "Playback service and CDN",
                "anchor": "playback-cdn",
                "context": "Playback should be a short control-plane call plus a data-plane fetch. The service authorizes the viewer and returns a manifest location, often with a signed URL. The CDN holds popular segments near the user. Adaptive bitrate is a player behavior: it measures buffer and bandwidth, then picks the next segment. If catalog or recommendations are down, an already authorized stream should still play.",
                "concepts": ["Signed URLs", "CDN caching", "Adaptive bitrate", "Control vs data plane"],
            },
            {
                "name": "Object storage, metadata, and jobs",
                "anchor": "youtube-data",
                "context": "Object storage keeps originals and renditions. The metadata database keeps product state. The job queue keeps work that may take minutes. These three fail differently: storage needs durability and lifecycle rules, metadata needs transactional state changes, and the queue needs retries without duplicate published videos. A consistent naming scheme for object keys makes cleanup and republish possible.",
                "concepts": ["Object immutability", "Lifecycle policies", "At-least-once jobs", "Key design"],
            },
        ],
    },
    {
        "slug": "netflix",
        "label": "Netflix",
        "summary": "Streaming a movie is mostly moving large, cacheable files to a living room. Choosing the title, personalizing the home screen, and authorizing the device are different problems. Netflix-style designs isolate those control-plane services and push bytes to an Open Connect-like CDN so a recommendation outage does not stop playback.",
        "caption": "Control plane services sit above origin storage. The viewer’s video path goes through the CDN, not through every microservice.",
        "blueprint_note": "Microservices are useful when they keep the playback path short. The important architectural choice is which calls are allowed to sit on the path of the next video segment.",
        "layers": [
            ("Clients", ["TV app", "Mobile / web"]),
            ("Edge", ["Open Connect CDN", "Playback API"]),
            ("Services", ["Identity", "Catalog", "Recommendations", "Playback auth"]),
            ("Data", ["Title metadata", "Viewing events", "Content origin"]),
        ],
        "together": "The client asks identity and playback auth for a license and nearby CDN hosts. Catalog and recommendations help the user choose a title, but once playback starts the player mostly talks to the CDN. Viewing events stream off to the side for ranking and billing. If recommendations fail, the app can show a smaller cached row. If a CDN node is overloaded, the client tries another host. Origin storage is a fallback, not the default path for a popular title.",
        "takeaway": "Resilience comes from removing nonessential services from the video path and placing content near viewers.",
        "modules": [
            {
                "name": "Open Connect CDN",
                "anchor": "open-connect",
                "context": "This is the data plane. Popular titles are pre-positioned on appliances or caches close to ISPs. The player downloads short segments. Because the files are immutable renditions, caches are simple and cheap. The design goal is that a Saturday-night hit never travels from a single origin to every household. Capacity planning here is about fill, eviction, and peering, not about adding more application servers.",
                "concepts": ["Edge caching", "Content pre-positioning", "Immutable segments", "Origin shielding"],
            },
            {
                "name": "Playback API and auth",
                "anchor": "playback-auth",
                "context": "Before bytes move, the device must be allowed to watch this title on this account. The playback API issues a short-lived license or token, chooses a CDN set, and records the session. It should not stream the movie itself. Keeping authorization in one place lets you revoke a device, enforce concurrency limits, and change CDN routing without touching every microservice.",
                "concepts": ["Short-lived licenses", "Device limits", "Session records", "Token expiry"],
            },
            {
                "name": "Identity, catalog, and recommendations",
                "anchor": "control-plane",
                "context": "These services make the product feel personal, but they have different availability needs. Identity must work to start a session. Catalog can serve a slightly stale title list. Recommendations can fail open to a default row. Treating them as independent microservices is useful only if the client has fallbacks. A chain of synchronous calls from the home screen to every personalization model is the opposite of resilience.",
                "concepts": ["Microservices", "Fallback UX", "Stale-OK reads", "Bulkheads"],
            },
            {
                "name": "Viewing events and origin",
                "anchor": "events-origin",
                "context": "Playback telemetry is valuable and dangerous. It should never block the next segment. Events go to a stream for quality metrics, recommendations, and billing. Origin storage holds the source files used to fill caches. The origin is expensive and far away, so only cache misses and new publishes should hit it. Separate the analytics pipeline from the path that keeps the picture moving.",
                "concepts": ["Async telemetry", "Event streams", "Cache fill", "Failure isolation"],
            },
        ],
    },
    {
        "slug": "uber",
        "label": "Uber",
        "summary": "Ride matching is a real-time marketplace. Riders want a car now, drivers move continuously, and the system must assign one driver to one trip even when two requests arrive together. The design splits fast-changing location data from durable trip state, then treats dispatch as a serialized decision.",
        "caption": "Rider and driver apps share a gateway. Location updates feed a geo index; dispatch writes the trip store.",
        "blueprint_note": "H3-like cells turn a map into buckets you can query. ETA is an estimate built from routing and recent traffic, not a promise stored as truth.",
        "layers": [
            ("Clients", ["Rider app", "Driver app"]),
            ("Edge", ["API gateway"]),
            ("Services", ["Trip service", "Dispatch", "ETA / routing", "Location ingest"]),
            ("Data", ["H3 geo index", "Trip store", "Maps / traffic"]),
        ],
        "together": "Drivers stream location points into ingest, which updates cells in the geo index. A rider request creates a trip in a requested state. Dispatch queries nearby cells, filters busy drivers, asks routing for ETAs, and attempts to lock one driver. The trip store is the authority: a compare-and-set changes the trip to assigned. Both apps subscribe to trip status. If the driver never accepts, the lease expires and dispatch tries again with a wider radius.",
        "takeaway": "Keep locations ephemeral and cheap; make assignment a single durable state change.",
        "modules": [
            {
                "name": "Location ingest",
                "anchor": "location-ingest",
                "context": "Phones send frequent, noisy GPS points. This module validates, smooths, and writes the latest point into a cell-based index. It should not open a database transaction for every ping. Old points expire so a driver who went offline disappears from search. Because drivers cross city boundaries, the ingest path must handle partition moves without creating two live locations for one vehicle.",
                "concepts": ["Geospatial indexing", "TTL locations", "Noisy GPS", "Hot city cells"],
            },
            {
                "name": "Dispatch",
                "anchor": "dispatch",
                "context": "Dispatch is the matcher. It searches nearby cells, applies product rules such as car type or rating, and proposes a driver. Two dispatchers can see the same idle driver, so the assignment must be fenced: a lease, a version number, or a unique active-trip constraint. Dispatch can retry with a larger radius, but it must never leave two confirmed trips on one driver.",
                "concepts": ["Matching", "Leases / fencing", "Idempotent assign", "Search radius"],
            },
            {
                "name": "ETA and routing",
                "anchor": "eta-routing",
                "context": "ETA combines map distance, live traffic, and pickup walking time. It is used to rank candidates and to set expectations, not to lock a car. Because routing is expensive, dispatch should ask it only for a shortlist. A degraded ETA service should fall back to straight-line time rather than block matching entirely.",
                "concepts": ["Routing graphs", "Traffic signals", "Approximate ETA", "Degraded fallback"],
            },
            {
                "name": "Trip service and trip store",
                "anchor": "trip-store",
                "context": "The trip is a state machine: requested, assigned, arriving, in progress, completed, canceled. Payments, receipts, and support all depend on this record. Location pings are not the trip. If the app dies, the store still knows who was assigned. Every transition should be recorded with who caused it so a dispute can be reconstructed.",
                "concepts": ["State machine", "Durable source of truth", "Compare-and-set", "Audit trail"],
            },
        ],
    },
    {
        "slug": "whatsapp",
        "label": "WhatsApp",
        "summary": "Chat feels instantaneous, but the network is not. People switch from wifi to mobile, lose signal in elevators, and expect a message that left their phone to arrive later. A WhatsApp-style system is a connection fabric plus durable per-device queues. Presence and typing are hints; message history is truth.",
        "caption": "Long-lived connections terminate at gateways. Durable queues sit behind the router so offline phones still receive mail.",
        "blueprint_note": "Erlang-style designs shine here because each connection can be a lightweight process. The architectural lesson is more general: isolate connections from durable delivery.",
        "layers": [
            ("Clients", ["Phone A", "Phone B"]),
            ("Edge", ["Connection gateway"]),
            ("Services", ["Message router", "Receipt service", "Presence"]),
            ("Data", ["Message store", "Offline queues", "Session store"]),
        ],
        "together": "A sender uploads an encrypted payload to its gateway. The router persists the message and enqueues it for each recipient device. If the device is connected, the gateway pushes it immediately and waits for a delivery ack. If not, the offline queue holds it. Read receipts are separate events so a lost ack does not resend forever. Presence updates expire quickly and are not written as permanent rows for every blink of connectivity.",
        "takeaway": "Reliable chat is durable queued delivery; 'online' is a short-lived hint.",
        "modules": [
            {
                "name": "Connection gateway",
                "anchor": "connection-gateway",
                "context": "This module holds millions of sockets. It authenticates a device, keeps a session, and forwards bytes to the router. It should store as little durable state as possible so you can add or restart gateways. When a phone reconnects, the gateway helps the client resume from a cursor rather than replaying the entire history. Health checks must distinguish 'process up' from 'can still push messages'.",
                "concepts": ["Long-lived connections", "Session resume", "Horizontal gateways", "Backpressure"],
            },
            {
                "name": "Message router",
                "anchor": "message-router",
                "context": "The router is the delivery brain. It looks up devices for a user, writes the message once, and places work on each device queue. It does not need the plaintext if end-to-end encryption is in use; it routes envelopes. Ordering is per conversation, not global. Fan-out to a large group should be asynchronous so the sender is not blocked on the slowest member.",
                "concepts": ["Per-device queues", "Envelope routing", "Conversation ordering", "Group fan-out"],
            },
            {
                "name": "Receipt and presence services",
                "anchor": "receipts-presence",
                "context": "Delivery and read receipts are themselves messages with a small payload. They must be idempotent because acks are retried. Presence is a TTL map: last seen, or a short 'online' flag. Mixing presence into the durable message table wastes writes and creates false precision. Users understand 'last seen recently' better than a blinking lie.",
                "concepts": ["Idempotent acks", "Read receipts", "TTL presence", "Eventual status"],
            },
            {
                "name": "Message store and offline queues",
                "anchor": "whatsapp-data",
                "context": "The store keeps conversation history and media pointers. Offline queues keep what has not been acknowledged by a device. Those are different retention rules. A queue can drop a payload after the device acknowledges; the store may keep it for new-device linking depending on the product. Encryption and multi-device pairing constrain what the server is allowed to read or re-encrypt.",
                "concepts": ["Durable history", "Ack-based deletion", "Multi-device", "Media pointers"],
            },
        ],
    },
    {
        "slug": "linkedin",
        "label": "LinkedIn",
        "summary": "A professional feed is an event-driven ranking system on top of a connection graph. The write is 'someone posted or interacted.' The read is 'show me a small set of items I am likely to care about, without violating privacy.' Kafka-style logs let many consumers reuse the same activity: feed, notifications, search, and analytics.",
        "caption": "Activity becomes an event once. Downstream consumers build candidates, ranks, and notifications from the same log.",
        "blueprint_note": "The graph tells you who could see an item. Ranking tells you who should see it now. Those jobs should not share one synchronous service call.",
        "layers": [
            ("Clients", ["App / web"]),
            ("Edge", ["API gateway"]),
            ("Services", ["Activity publisher", "Candidate gen", "Feed ranker", "Graph service"]),
            ("Data", ["Kafka log", "Connection graph", "Feature store", "Feed cache"]),
        ],
        "together": "A post or comment is written and emitted to the log. Candidate generation walks or samples the graph and writes possible feed entries. The ranker scores those entries with features from the feature store. A feed request reads a ranked slice, applies privacy again, and caches it briefly. Notifications and search consume the same log with their own offsets. If ranking is slow, the feed can show a simpler recency list rather than fail.",
        "takeaway": "Publish activity once; let independent consumers build the feed, notifications, and analytics.",
        "modules": [
            {
                "name": "Activity publisher",
                "anchor": "activity-publisher",
                "context": "This module records the user action and appends an event with a stable ID. The event is the contract. If it is incomplete, every downstream job is wrong. Use an outbox so the database write and the log write do not diverge. The publisher should not rank the feed. Its success metric is durable, ordered, replayable activity.",
                "concepts": ["Event outbox", "Stable event IDs", "Replay", "Contract versioning"],
            },
            {
                "name": "Connection graph service",
                "anchor": "graph-service",
                "context": "The graph stores who is connected, who follows whom, and which organizations a person belongs to. Feed and notifications query it, but they should not run unbounded traversals on the request path. Common questions become explicit APIs: first-degree connections, followers of this actor, members of this page. Privacy edges change, so consumers must be able to drop candidates that are no longer allowed.",
                "concepts": ["Graph APIs", "Bounded traversal", "Privacy edges", "Membership"],
            },
            {
                "name": "Candidate generation and ranker",
                "anchor": "candidates-ranker",
                "context": "Candidate generation is recall: gather more items than you will show. Ranking is precision: order them. Features include author affinity, recency, and inferred topics. Because models change, store the model version with the score. Ranking is expensive, so do it asynchronously for the next session when you can, and keep a cache of the last good list.",
                "concepts": ["Recall vs precision", "Feature store", "Model versioning", "Feed cache"],
            },
            {
                "name": "Kafka log",
                "anchor": "kafka-log",
                "context": "The log decouples producers from consumers. Feed builders, notification workers, and metrics can move at different speeds. Offsets make replay possible when a ranker is rewritten. Partition by actor or event type so related activity stays ordered. A log is not a database; consumers still need their own derived stores.",
                "concepts": ["Pub/sub log", "Consumer offsets", "Partition keys", "Derived read models"],
            },
        ],
    },
    {
        "slug": "instagram",
        "label": "Instagram",
        "summary": "Photo sharing combines a social graph, a media pipeline, and a feed. The image bytes are large and cacheable. The metadata is small and frequently queried. IDs must be unique across shards and roughly sortable by time so feeds can page without asking every shard for 'latest.'",
        "caption": "Uploads go to object storage first. The feed stores pointers, not JPEGs.",
        "blueprint_note": "Sharding is usually by user. That makes 'posts by this author' easy and 'global latest' hard, which is the right trade if the product is a personal feed.",
        "layers": [
            ("Clients", ["Camera upload", "Feed client"]),
            ("Edge", ["Upload API", "Media CDN"]),
            ("Services", ["Media pipeline", "Feed service", "ID generator"]),
            ("Data", ["Object storage", "Metadata shards", "Follow graph"]),
        ],
        "together": "The client uploads bytes to object storage, then calls the API with the object key. The ID generator issues a time-sortable ID. Metadata is written to the author's shard. The media pipeline creates thumbnails and a CDN-friendly variant. Feed delivery either pushes the post ID to follower inboxes or pulls recent posts from followed authors at read time. Deleted or hidden media must invalidate CDN paths, not only the metadata row.",
        "takeaway": "Keep blobs out of the database, and make feed rows point at immutable media variants.",
        "modules": [
            {
                "name": "Media pipeline",
                "anchor": "media-pipeline",
                "context": "This worker turns an original into thumbnails and display sizes. It should be asynchronous so the upload API returns quickly. Variants use new keys so a retry cannot serve a half-resized image. Strip GPS and other sensitive metadata unless the product explicitly keeps it. Failures retry from the original object.",
                "concepts": ["Async derivatives", "Immutable variants", "EXIF hygiene", "Retry from original"],
            },
            {
                "name": "Feed service",
                "anchor": "feed-service",
                "context": "The feed is a list of post IDs plus enough author data to render a cell. It can be precomputed for active users or merged at read time for sparse graphs. Celebrity fan-out has the same push/pull tension as Twitter. Authorization is rechecked on read because a switched account from public to private should not keep appearing in caches.",
                "concepts": ["Inbox vs fan-in", "Post pointers", "Rechecked privacy", "Active-user materialization"],
            },
            {
                "name": "ID generator",
                "anchor": "id-generator",
                "context": "A good photo ID is unique, compact, and roughly increasing with time. Snowflake-style IDs encode a timestamp and a machine identity so shards can generate IDs without a central lock. Random UUIDs work for uniqueness but make 'give me newer than X' clumsy and fragment indexes. The generator must survive clock skew and process restarts without collisions.",
                "concepts": ["Snowflake IDs", "Time-sortable keys", "Allocation ranges", "Clock safety"],
            },
            {
                "name": "Metadata shards and object storage",
                "anchor": "instagram-data",
                "context": "User-sharded metadata keeps an author's posts together. Object storage and the CDN carry the bytes. The follow graph decides feed membership. Cross-shard operations, such as a global report or a celebrity lookup, need their own access path. Plan how you will move a user when a shard overheats; that is harder than picking the first hash function.",
                "concepts": ["User sharding", "Object + CDN", "Hot users", "Resharding"],
            },
        ],
    },
    {
        "slug": "facebook-social-graph",
        "label": "Facebook social graph",
        "summary": "A social network is a graph of objects and associations: people, pages, posts, likes, memberships. Most product screens are a few named traversals, not arbitrary graph queries. TAO-style systems put a cache-aware graph layer in front of storage so 'friends of this user' stays fast while still having a durable backend.",
        "caption": "Clients call a graph API. TAO-like caches serve objects and edges; storage is the fallback and source of truth.",
        "blueprint_note": "Design the API around associations you will actually query. A general graph database query language on the request path is usually the wrong starting point for this product.",
        "layers": [
            ("Clients", ["Mobile / web"]),
            ("Edge", ["Graph API"]),
            ("Services", ["TAO cache layer", "Association service", "Invalidation"]),
            ("Data", ["Object store", "Edge store"]),
        ],
        "together": "A product request asks for an object and a typed edge list, such as members or reactions. The cache layer returns hot data and fills from storage on miss. Writes update storage, then publish invalidations so caches drop or version the changed edges. Privacy is applied at the graph API, not only in the client. Popular objects, such as a major page, need extra caching and careful write batching to avoid a hot partition.",
        "takeaway": "Turn social reads into named object/edge operations and cache those operations, not arbitrary queries.",
        "modules": [
            {
                "name": "Graph API",
                "anchor": "graph-api",
                "context": "This is the product contract: get object, get associations, create edge, delete edge. It enforces authentication and privacy, paginates large edge lists, and hides storage layout. If every app writes SQL against the edge table, you will never change sharding. Keep result sizes bounded; 'all friends of friends' is a request you should refuse or precompute.",
                "concepts": ["Named traversals", "Privacy checks", "Bounded pagination", "API as facade"],
            },
            {
                "name": "TAO-style cache layer",
                "anchor": "tao-cache",
                "context": "TAO popularized a two-level approach: a cache that understands objects and associations, backed by a sharded store. Reads go to the cache; writes go to storage and then invalidate. The cache is not just Redis-as-blob. It knows the graph operations, so it can serve 'assoc get' without assembling a response from many keys in the client.",
                "concepts": ["Association cache", "Read-heavy graph", "Write-through / invalidate", "Hot objects"],
            },
            {
                "name": "Association service and stores",
                "anchor": "association-store",
                "context": "Objects have a type and payload. Edges have a type, from-id, to-id, and time. Storage is sharded so a popular object's edges can be split. Secondary indexes support lookups in the reverse direction, such as 'pages this user likes.' Consistency matters most for privacy edges: a removed friend should not keep seeing cached content.",
                "concepts": ["Object/edge model", "Reverse indexes", "Sharded edge lists", "Privacy consistency"],
            },
            {
                "name": "Invalidation bus",
                "anchor": "invalidation",
                "context": "After a write, caches must learn that an edge changed. A lightweight invalidation message is usually better than pushing full objects everywhere. Consumers drop or reload one association list. If invalidations are lost, a TTL remains as a safety net. Version numbers help a reader detect that a cached edge list is older than a write it just performed.",
                "concepts": ["Cache invalidation", "Version tokens", "TTL safety net", "Lost-update protection"],
            },
        ],
    },
    {
        "slug": "dropbox-google-drive",
        "label": "Dropbox / Google Drive",
        "summary": "File sync is a metadata problem dressed as a storage problem. The bytes can be split, hashed, and stored once. The hard work is reconciling trees across devices: renames, offline edits, deletes, and two people changing the same file. The blueprint stores chunks immutably and lets a metadata service decide what the current tree is.",
        "caption": "Clients talk to metadata and chunk APIs. Devices learn about changes through a notification channel.",
        "blueprint_note": "Dedup is a storage optimization. Sync correctness comes from manifests, versions, and conflict rules, not from hashing alone.",
        "layers": [
            ("Clients", ["Desktop sync", "Mobile"]),
            ("Edge", ["Metadata API", "Chunk API"]),
            ("Services", ["Chunker / dedup", "Sync engine", "Notification"]),
            ("Data", ["Chunk store", "Manifest / tree", "Device cursors"]),
        ],
        "together": "A client hashes local chunks, asks which hashes the server already has, uploads the missing ones, and commits a new manifest for the file path. The metadata service assigns a version and notifies other devices. Those devices download missing chunks and apply the tree change. If two commits descend from the same parent, the service keeps a conflict copy instead of silently choosing. Garbage collection waits until no manifest references a chunk.",
        "takeaway": "Sync files as immutable chunks plus a transactional tree; never treat the latest upload as automatically correct.",
        "modules": [
            {
                "name": "Chunker and dedup",
                "anchor": "chunker",
                "context": "Files are split into chunks so a small edit does not re-upload a 2 GB video. Content hashes let the server skip bytes it already stores. Chunk size is a trade: tiny chunks increase metadata, huge chunks waste upload. Clients should encrypt or hash in a way that still allows the server to address chunks. This module must treat two identical PDFs from different users carefully if privacy requires per-namespace encryption.",
                "concepts": ["Content-defined chunking", "Hash addressing", "Upload resume", "Namespace privacy"],
            },
            {
                "name": "Sync engine and metadata",
                "anchor": "sync-engine",
                "context": "Metadata holds paths, permissions, versions, and the list of chunk hashes that make a file. Commits are transactional: a new tree either replaces the old one or is rejected as stale. Renames are metadata operations, not byte copies. Sharing a folder is an ACL change on a subtree, which is why metadata, not object storage, is the product database.",
                "concepts": ["Manifest commit", "Optimistic versions", "Rename as metadata", "ACLs on trees"],
            },
            {
                "name": "Notification service",
                "anchor": "sync-notify",
                "context": "Devices should not poll every few seconds. After a commit, this module wakes subscribed clients with a cursor. The client then fetches the delta. Notifications can be lossy if the cursor protocol is correct: a missed ping just means a later catch-up. This is cheaper and kinder to batteries than tight polling.",
                "concepts": ["Change notifications", "Device cursors", "Lossy ping, reliable delta", "Wake vs poll"],
            },
            {
                "name": "Chunk store and device cursors",
                "anchor": "drive-data",
                "context": "The chunk store is append-only object storage. Device cursors remember how far each client has applied the tree. Tombstones record deletes so a device that was offline does not resurrect a file. Garbage collection is delayed and reference-counted. If you delete bytes when the first user removes a file, you may destroy a chunk another namespace still needs.",
                "concepts": ["Immutable chunks", "Tombstones", "Reference counting", "Delayed GC"],
            },
        ],
    },
    {
        "slug": "url-shortener",
        "label": "URL shortener",
        "summary": "A shortener has two calls with opposite needs. Creating a link is a write with uniqueness and abuse checks. Opening a link is an extremely hot read that should be a single key lookup and a redirect. Analytics, preview pages, and custom aliases must stay off that redirect path unless you accept losing the performance that made the product useful.",
        "caption": "Create and redirect are different paths that share one key-value record.",
        "blueprint_note": "The short key is the entire API. Generate it carefully, store it simply, and cache the hottest keys.",
        "layers": [
            ("Clients", ["Create API", "Browser redirect"]),
            ("Edge", ["Write gateway", "Redirect edge"]),
            ("Services", ["Key allocator", "Redirect service", "Analytics"]),
            ("Data", ["KV store", "Hot cache", "Click queue"]),
        ],
        "together": "A create request validates the destination, asks the allocator for a unique key, and writes the mapping. A redirect request hits the edge cache or the key-value store and returns 301 or 302. The click is appended to a queue for later counts. Custom aliases take a transactional reservation so two teams cannot claim the same word. If the cache is wrong, the store wins; if the store is down, fail the create, and decide explicitly whether redirects fail open from cache.",
        "takeaway": "Make redirect a tiny lookup; put uniqueness and analytics everywhere else.",
        "modules": [
            {
                "name": "Key allocator",
                "anchor": "key-allocator",
                "context": "Keys can be random, hash-based, or issued from a counter encoded in base62. Random keys need enough bits to make collisions rare and a uniqueness check anyway. Hashing the destination makes the same URL collapse to one key, which may or may not be desired. Counters are simple but leak creation volume. Reserve custom aliases in the same transaction that writes the record.",
                "concepts": ["Key generation", "Collision handling", "Base62 encoding", "Alias reservation"],
            },
            {
                "name": "Redirect service and cache",
                "anchor": "redirect",
                "context": "This path should avoid joins, user profiles, and synchronous analytics. Read key, write a cache entry, return Location. Choose 301 if the mapping never changes, 302 if you need to keep seeing clicks at your edge. Signed or allow-listed destinations reduce phishing. A single viral key becomes a hot partition; replicate that entry widely instead of scaling the whole table.",
                "concepts": ["KV lookup", "HTTP redirect semantics", "Hot-key replication", "Safety checks"],
            },
            {
                "name": "Analytics",
                "anchor": "shortener-analytics",
                "context": "Clicks are a firehose. Drop them on a queue with the key, time, and coarse geography. Aggregate offline. If analytics is down, redirects should still work. Unique-click counts need a privacy-aware approximation, not a full replay of IP addresses in the request path.",
                "concepts": ["Async click events", "Approximate counts", "Privacy", "Decoupled metrics"],
            },
        ],
    },
    {
        "slug": "pastebin",
        "label": "Pastebin",
        "summary": "Pastebin is a small object store with public links, expiry, and a read-heavy traffic shape. Anyone can upload text; anyone with the link may read it. That combination makes abuse, accidental secrets, and sudden popularity the real design constraints. The body lives in object storage. Metadata answers whether the paste still exists and who may see it.",
        "caption": "Writes create an object and a metadata row. Reads check expiry, then hit cache or object storage.",
        "blueprint_note": "Expiry is both cleanup and authorization. A paste past its deadline must not be readable even if the blob is still on disk for a few minutes.",
        "layers": [
            ("Clients", ["Browser / API"]),
            ("Edge", ["Paste API", "Read cache"]),
            ("Services", ["Paste service", "Expiry sweeper", "Abuse filter"]),
            ("Data", ["Object storage", "Metadata index"]),
        ],
        "together": "A create call runs through abuse checks, stores the body under a random ID, and writes metadata with size, visibility, and expiry. A read loads metadata first. If the paste is expired or private, the service returns not found. Otherwise it serves from cache or storage and never executes the paste as HTML. A sweeper later deletes metadata and then the blob. Lifecycle rules on the bucket are a backup, not the only control.",
        "takeaway": "Separate the blob from the policy, and treat expiry as a read-time check.",
        "modules": [
            {
                "name": "Paste service",
                "anchor": "paste-service",
                "context": "This module issues IDs, enforces size limits, and stores metadata. Unlisted pastes rely on unguessable IDs; private pastes need a real owner check. Rendering must escape HTML so a paste cannot become a script on your domain. The service should not scan the entire object store to list a user's pastes; that is why metadata exists.",
                "concepts": ["Unguessable IDs", "Size limits", "Safe rendering", "Visibility modes"],
            },
            {
                "name": "Abuse filter",
                "anchor": "abuse-filter",
                "context": "Open upload is a spam magnet. Rate-limit by IP and account, detect malware or banned patterns, and require a challenge when volume spikes. Filters will be wrong sometimes, so keep an appeal or override path for trusted users. Do not wait for a human to review every paste before it is reachable if the product is 'instant share,' but do keep takedown fast.",
                "concepts": ["Rate limits", "Content scanning", "Takedown path", "Challenge / CAPTCHA"],
            },
            {
                "name": "Expiry sweeper",
                "anchor": "expiry-sweeper",
                "context": "A background job lists pastes whose deadline has passed, removes metadata, and deletes objects. Because jobs lag, the read path must also compare now to expiry. Storage lifecycle policies catch blobs the sweeper missed. Log deletions so you can explain why a link died.",
                "concepts": ["TTL as policy", "Read-time expiry", "Lifecycle rules", "Idempotent delete"],
            },
            {
                "name": "Read cache and object storage",
                "anchor": "paste-data",
                "context": "Popular pastes become hot keys. Cache the body and the metadata together so you do not serve a cached body after metadata says expired. Object storage holds the canonical bytes. Short pastes may live only in the database, but a single rule—'bodies in object storage'—is easier to operate once size grows.",
                "concepts": ["Read-heavy caching", "Coupled cache keys", "Object durability", "Hot pastes"],
            },
        ],
    },
    {
        "slug": "rate-limiter",
        "label": "Rate limiter",
        "summary": "A rate limiter is a policy engine in front of expensive work. It answers whether this caller may proceed now. The algorithm you pick encodes the product rule: token bucket allows bursts, sliding window smooths traffic, fixed window is simple and slightly unfair at boundaries. In a fleet of gateways the hard part is shared state and failure policy.",
        "caption": "Every request is identified, then decided against a small shared counter store before the API runs.",
        "blueprint_note": "If the limiter store is down you must choose fail-open or fail-closed. That choice is part of the design, not an afterthought.",
        "layers": [
            ("Clients", ["Any caller"]),
            ("Edge", ["API gateway"]),
            ("Services", ["Identity", "Limiter decision", "Metrics"]),
            ("Data", ["Counter store", "Policy config"]),
        ],
        "together": "The gateway extracts a key such as user, API token, or IP. The decision module reads policy, performs an atomic increment or token consume, and returns allow or retry-after. Metrics record both results. The application runs only on allow. Policies can stack: a global IP limit and a tighter limit on the search endpoint. Clock sources must be server-side so clients cannot reset their budget.",
        "takeaway": "A limiter is identity plus atomic state plus an explicit outage policy.",
        "modules": [
            {
                "name": "Identity",
                "anchor": "limiter-identity",
                "context": "Limits are meaningless if the key is wrong. Anonymous traffic uses IP and TLS fingerprints with care; authenticated traffic uses the user or API key. Expensive routes get their own key suffix so a cheap health check does not share budget with an export job. Identity must be cheap; a limiter that calls a remote user service on every request becomes the outage.",
                "concepts": ["Caller keys", "Route-specific budgets", "Cheap identification", "Multi-tenant fairness"],
            },
            {
                "name": "Limiter decision",
                "anchor": "limiter-decision",
                "context": "This module implements the algorithm. Token bucket stores a balance and a last refill time. Sliding window stores counts in time slots. The update must be atomic across gateways, usually with Redis-style scripts or compare-and-set. Return a retry-after with jitter so rejected clients do not retry in lockstep. Document what happens when this module cannot reach the store.",
                "concepts": ["Token bucket", "Sliding window", "Atomic counters", "Jittered retry-after"],
            },
            {
                "name": "Policy config",
                "anchor": "limiter-policy",
                "context": "Policies change without a redeploy: 100 requests per minute for free users, 10 per second for search, a temporary ban. Store them in a small config with versions. Operators need an emergency switch. Keep the number of policies small enough that every request does not evaluate a novel.",
                "concepts": ["Versioned policies", "Emergency kill switch", "Per-tier limits", "Composable rules"],
            },
            {
                "name": "Counter store and metrics",
                "anchor": "limiter-data",
                "context": "State is tiny and extremely hot. Use memory-speed storage with replication and short TTLs so dead keys vanish. Metrics should show reject rate by key class, not only totals, or you will miss a single abusive tenant. Do not log every decision at full cardinality; sample.",
                "concepts": ["Distributed counters", "Hot-key storage", "TTL hygiene", "Reject metrics"],
            },
        ],
    },
    {
        "slug": "ticketmaster-bookmyshow",
        "label": "Ticketmaster / BookMyShow",
        "summary": "Ticketing is inventory under a flash sale. Many people want the same seats at the same instant. The browser cannot own a seat. A hold is a short lease in a transactional inventory service, and payment is a later step that must not create a second sale if the client retries. An admission queue protects the database from becoming the waiting room.",
        "caption": "People wait in an admission queue. Seats move from available to held to sold in one inventory authority.",
        "blueprint_note": "If two checkouts can both mark seat A12 sold, the rest of the architecture does not matter. Start from a unique constraint or conditional update on the seat.",
        "layers": [
            ("Clients", ["Browser"]),
            ("Edge", ["Waiting room"]),
            ("Services", ["Inventory", "Seat lock", "Payment", "Order service"]),
            ("Data", ["Seat map", "Hold table", "Orders"]),
        ],
        "together": "Users receive a place in the waiting room and are admitted at a rate the core can handle. Selecting seats creates a hold with an expiry. Payment uses an idempotency key. On success the order service converts the hold to sold. A sweeper releases expired holds. If payment succeeds after the hold expired, reconciliation must either restore the seat sale or refund; it must not silently drop the money.",
        "takeaway": "Serialize seat state, and put a queue in front of that serializer when demand spikes.",
        "modules": [
            {
                "name": "Waiting room",
                "anchor": "waiting-room",
                "context": "This is load management, not shopping. It issues a signed token when a browser may enter checkout. The release rate matches inventory and payment capacity. Without it, you scale the storefront into a self-inflicted outage. The waiting room should be simple and separately scalable: it does not browse every seat map.",
                "concepts": ["Admission control", "Signed entry tokens", "Release rate", "Flash-sale shedding"],
            },
            {
                "name": "Inventory and seat lock",
                "anchor": "seat-lock",
                "context": "Each seat has a state: available, held, sold. A hold writes who owns it and when it expires. The write uses a condition so only one holder wins. Holds are short because abandoned browsers are common. Extending a hold is an explicit call, not an infinite reservation. Seat maps can be cached for display, but the lock always goes to the authority.",
                "concepts": ["Conditional updates", "Short leases", "Cached map, authoritative lock", "Expiry workers"],
            },
            {
                "name": "Payment and order service",
                "anchor": "ticketing-payment",
                "context": "Payment is slow and retries. The order record must survive a double callback. Convert hold to sold only after the processor confirms, and store the processor reference. The user-visible confirmation is derived from order state, not from the last browser response. This is a small saga: hold, charge, sell, or compensate.",
                "concepts": ["Idempotent payment", "Order state machine", "Compensation", "Webhook races"],
            },
        ],
    },
    {
        "slug": "airbnb",
        "label": "Airbnb",
        "summary": "Marketplace lodging has a soft search problem and a hard booking problem. Search can be a little stale. A double-booked apartment cannot. Availability calendars, ranking, and payments therefore live in different modules, and the booking path re-validates dates against a transactional store even if search showed the listing as open.",
        "caption": "Search reads a denormalized index. Booking writes reservations and only then updates search.",
        "blueprint_note": "Think of search as advertising and booking as inventory. The advertisement can lag; the inventory cannot.",
        "layers": [
            ("Clients", ["Guest app", "Host app"]),
            ("Edge", ["Search API", "Booking API"]),
            ("Services", ["Ranking", "Calendar", "Booking", "Payments"]),
            ("Data", ["Listing index", "Reservation store", "Calendar rows"]),
        ],
        "together": "Hosts publish listings and calendar rules. An indexer builds documents for search. Guests query ranking, then start a booking. Booking locks the date range, starts payment, and commits a reservation. Events update the search document so the listing disappears for those nights. If payment fails, the lock expires. Host cancellations and guest cancellations are explicit transitions with refund rules, not deletes of history.",
        "takeaway": "Let search be eventually consistent; make the reservation the strongly consistent record.",
        "modules": [
            {
                "name": "Search ranking",
                "anchor": "airbnb-ranking",
                "context": "Ranking mixes quality, price, location, and business goals. It reads a denormalized listing index, not the reservation table. That keeps search fast and independently scalable. Because the index lags, the UI should treat results as candidates. Filters such as 'entire home' belong in the index; 'available these exact dates' should be rechecked at booking even if also used as a search filter.",
                "concepts": ["Denormalized index", "Multi-signal ranking", "Stale availability", "Candidate vs commit"],
            },
            {
                "name": "Calendar",
                "anchor": "calendar",
                "context": "The calendar captures host rules: min stay, blocked dates, preparation time. It is the input to availability, not the reservation itself. Modeling this as per-listing date rows or ranges is a product choice with different update costs. Calendar edits must not silently erase existing reservations; they only change what new guests can book.",
                "concepts": ["Availability rules", "Range vs per-day rows", "Host constraints", "Non-destructive edits"],
            },
            {
                "name": "Booking service",
                "anchor": "booking",
                "context": "Booking inserts a reservation with a constraint that prevents overlapping stays, or it locks the listing dates in a transaction. It then starts payment as a saga. The guest receives a reservation ID immediately. Everything else—emails, search updates, host payouts—follows from events. Two guests clicking the same weekend is the race this module exists to win exactly once.",
                "concepts": ["Exclusion constraints", "Booking saga", "Reservation ID", "Race to lock"],
            },
            {
                "name": "Payments",
                "anchor": "airbnb-payments",
                "context": "Money may be authorized at request and captured after host acceptance, depending on the product. Payouts to hosts are delayed on purpose. Each movement needs a ledger entry and an idempotency key. Booking state and payment state can disagree briefly; a reconciler, not the guest refresh button, fixes that.",
                "concepts": ["Auth vs capture", "Idempotency", "Delayed payouts", "Reconciliation"],
            },
        ],
    },
    {
        "slug": "amazon-e-commerce",
        "label": "Amazon e-commerce",
        "summary": "Retail checkout is a long-running workflow across catalog, cart, inventory, payment, and fulfillment. No single database transaction spans the warehouse and the card network. The order becomes a saga: a durable state machine with steps and compensations. Inventory is reserved, not guessed from a cached count on the product page.",
        "caption": "The cart is intent. The order log is truth. Downstream services react to order events.",
        "blueprint_note": "A sold-out badge on the storefront is a hint. The reservation at checkout is the decision.",
        "layers": [
            ("Clients", ["Storefront"]),
            ("Edge", ["Commerce API", "CDN"]),
            ("Services", ["Cart", "Inventory", "Order workflow", "Payment", "Fulfillment"]),
            ("Data", ["Catalog", "Inventory ledgers", "Order log"]),
        ],
        "together": "Browsing hits cached catalog. Adding to cart writes intent, often without a hard reservation. Checkout creates an order, reserves stock, authorizes payment, and emits events. Fulfillment allocates a warehouse and later ships. If payment fails, reservations release. If an item cannot ship, compensation refunds or splits the order. The customer sees order state derived from the log, not from whatever page they last posted.",
        "takeaway": "Model checkout as a saga with reservations and compensations, not as one giant commit.",
        "modules": [
            {
                "name": "Cart",
                "anchor": "cart",
                "context": "The cart is a working document. It survives devices through an account ID or a signed cookie. It can hold items that later go out of stock. Do not put payment authorization in the cart. Price the cart at checkout time because promotions change. Merge guest and user carts carefully to avoid losing items or leaking another person's basket.",
                "concepts": ["Durable intent", "Price at checkout", "Cart merge", "No hard reservation"],
            },
            {
                "name": "Inventory",
                "anchor": "inventory",
                "context": "Inventory is a ledger of on-hand, reserved, and shipped units per SKU and location. Reservations use conditional decrements. Oversell happens when you decrement a cache. Multi-warehouse routing is a later choice; correctness starts with one atomic reservation record. Expired reservations return stock to the pool.",
                "concepts": ["Reservation ledger", "Conditional decrement", "Reservation TTL", "Location-level stock"],
            },
            {
                "name": "Order workflow",
                "anchor": "order-workflow",
                "context": "The order ID is the customer's handle on the saga. States include created, paid, allocated, shipped, and canceled. Each step records a command result so retries do not charge twice or ship twice. An outbox publishes events for email, fraud, and warehouse systems. Humans in support need the same state machine; they should not edit stock by folklore.",
                "concepts": ["Sagas", "Order state machine", "Outbox events", "Compensation"],
            },
            {
                "name": "Payment and fulfillment",
                "anchor": "pay-fulfill",
                "context": "Payment talks to a processor with idempotency keys. Fulfillment assigns warehouses, packing, and carriers. These modules should accept commands from the order workflow, not invent their own order IDs. Tracking numbers flow back as events. Partial shipment is a first-class state, not an exception buried in notes.",
                "concepts": ["Idempotent capture", "Warehouse allocation", "Partial shipment", "Event callbacks"],
            },
        ],
    },
    {
        "slug": "web-crawler",
        "label": "Web crawler",
        "summary": "A crawler is a distributed scheduler that downloads the web without becoming a denial-of-service tool. The frontier decides what to fetch next. Politeness limits how hard you hit one host. Dedup stops you from fetching the same page through a thousand URLs. Workers are replaceable; the frontier and seen-set are the system.",
        "caption": "Seeds enter the frontier. Fetchers pull work under per-host limits. Parsers emit new URLs back into the loop.",
        "blueprint_note": "If you only remember one rule, remember per-host concurrency. Throughput without politeness is just abuse.",
        "layers": [
            ("Clients", ["Seed / operator"]),
            ("Edge", ["Fetcher fleet"]),
            ("Services", ["Frontier", "Parser", "Dedup", "Politeness"]),
            ("Data", ["URL queues", "Seen index", "Content store"]),
        ],
        "together": "Operators load seeds. The frontier leases URLs to fetchers that respect robots rules and host budgets. Successful fetches go to content storage and to a parser. The parser extracts links, canonicalizes them, and asks dedup whether each URL is new. New URLs re-enter the frontier with a priority. Failures retry with backoff or go to a dead-letter queue. The seen index must be huge and approximate-tolerant; a rare re-fetch is better than unbounded growth.",
        "takeaway": "A crawler is a polite scheduler with a memory of URLs, not a loop that downloads links.",
        "modules": [
            {
                "name": "URL frontier",
                "anchor": "frontier",
                "context": "The frontier is a prioritized, partitioned queue of work. Priority might be site importance, recency, or change rate. Partition by host so one site cannot occupy every worker. Leases prevent two fetchers from taking the same URL. When a worker dies, the lease expires and the URL returns. This is the difference between a queue and a lost-work pile.",
                "concepts": ["Prioritized queues", "Host partitions", "Work leases", "Replay on timeout"],
            },
            {
                "name": "Politeness",
                "anchor": "politeness",
                "context": "Politeness reads robots.txt, crawl-delay, and your own per-host QPS budget. It is a gate in front of the fetcher, not a comment in a design doc. Some hosts need even stricter limits after errors. Identify your crawler honestly. Ignore this module and you will be banned, sued, or both, and your data will be biased toward whoever failed to block you.",
                "concepts": ["robots.txt", "Per-host QPS", "Backoff on errors", "Honest user-agent"],
            },
            {
                "name": "Dedup and parser",
                "anchor": "dedup-parser",
                "context": "Canonicalization strips tracking query params and session IDs before hashing. Dedup can use an exact store for recent URLs and a Bloom filter for the long tail. The parser extracts links and language, and it must bound HTML size so a huge page cannot explode memory. Content hashes detect that two URLs are the same document.",
                "concepts": ["URL canonicalization", "Bloom filters", "Content hashes", "Bounded parse"],
            },
            {
                "name": "Fetcher fleet and content store",
                "anchor": "fetch-store",
                "context": "Fetchers are stateless HTTP clients with timeouts, size limits, and sandboxing. They write raw content and fetch metadata: status, headers, time. The store is append-oriented so you can recrawl and keep history. Do not run JavaScript in the fetcher unless you have an isolated renderer farm; that is a different, more expensive module.",
                "concepts": ["Timeouts and size caps", "Stateless workers", "Fetch metadata", "Optional render farm"],
            },
        ],
    },
    {
        "slug": "search-autocomplete",
        "label": "Search autocomplete",
        "summary": "Autocomplete must answer in a few tens of milliseconds as a person types. That rules out a general search of the catalog on every keystroke. The system keeps a compact prefix index in memory, a small top-K list per prefix, and a cache for the hottest prefixes. Freshness is handled by rebuilding versions offline.",
        "caption": "Keystrokes hit a cache, then an in-memory prefix index. Offline jobs rebuild that index from logs and catalog.",
        "blueprint_note": "The online path only reads. Writers publish a new immutable index and flip a pointer.",
        "layers": [
            ("Clients", ["Search box"]),
            ("Edge", ["Suggest API", "Prefix cache"]),
            ("Services", ["Trie / FST lookup", "Top-K ranker", "Index builder"]),
            ("Data", ["In-memory index", "Query logs", "Catalog dump"]),
        ],
        "together": "The client debounces slightly and sends the current prefix. The API checks a tiny cache, then queries the in-memory index for completions. A ranker orders them by frequency, freshness, and safety. Offline, query logs and catalog changes build the next index version. A process loads the new version and then serves it. Bad terms are filtered before they ever reach the client.",
        "takeaway": "Precompute prefix answers and swap index versions; do not run full search on each keypress.",
        "modules": [
            {
                "name": "Suggest API and cache",
                "anchor": "suggest-api",
                "context": "This path is latency-critical. Cap prefix length, result count, and payload size. Cache full responses for popular prefixes such as 'a' or 'app' with a short TTL. The API should be read-only and cheap to clone in every region. Language and market belong in the cache key or you will suggest the wrong store.",
                "concepts": ["Tight SLIs", "Prefix cache", "Locale keys", "Result caps"],
            },
            {
                "name": "Trie / FST lookup",
                "anchor": "trie",
                "context": "A trie or finite-state transducer maps a prefix to a small set of completions in memory. This is why autocomplete is fast. The structure is built offline because updating a huge trie in place on the request path is painful. Compact representations matter; the whole hot index should fit in RAM on each replica.",
                "concepts": ["Tries", "Finite-state indexes", "Memory residency", "Immutable versions"],
            },
            {
                "name": "Top-K ranker",
                "anchor": "top-k",
                "context": "Many words share a prefix. You return only a handful. Ranking uses frequency, click-through, recency, and business rules. Safety filters remove spam and offensive completions. Personalization, if any, must be a cheap re-rank of a tiny list, not a new index walk.",
                "concepts": ["Top-K", "Frequency signals", "Safety filters", "Light personalization"],
            },
            {
                "name": "Index builder",
                "anchor": "index-builder",
                "context": "Batch jobs read query logs and catalog titles, clean them, and emit a new index artifact. Building is expensive and can fail; never mutate the live structure halfway. Atomic swap keeps the online path simple. Keep one previous version for rollback when a bad dictionary ships.",
                "concepts": ["Offline build", "Atomic swap", "Rollback version", "Log-derived dictionaries"],
            },
        ],
    },
    {
        "slug": "spotify",
        "label": "Spotify",
        "summary": "Music streaming looks like video streaming with smaller files and a stronger catalog of user-made playlists. Playback should work even if the recommendation model is unhappy. Audio segments are cacheable. Playlist edits are metadata. Listening history is an event stream that later trains recommendations.",
        "caption": "The player gets a token and then talks to the audio CDN. Playlists and recommendations stay on the control plane.",
        "blueprint_note": "A skipped song is an event, not a reason to stall the next segment.",
        "layers": [
            ("Clients", ["Player"]),
            ("Edge", ["Audio CDN", "Playback API"]),
            ("Services", ["Catalog", "Playlists", "Recommendations", "License token"]),
            ("Data", ["Audio objects", "Playlist DB", "Listen stream"]),
        ],
        "together": "The player asks for a license and a list of CDN hosts, then fetches encrypted segments. Playlist changes update the playlist database and invalidate a small cache. Listens go to a stream used for history and models. Recommendations compute offline and nearline; the home screen reads a prepared list. If recommendations fail, recently played and downloaded titles still work.",
        "takeaway": "Separate licensed, cacheable audio from playlist metadata and from recommendation batch jobs.",
        "modules": [
            {
                "name": "License token and playback API",
                "anchor": "spotify-license",
                "context": "Rights differ by country, device, and subscription. This module issues a short-lived token that the CDN or player can verify. It is also where offline download grants are recorded. Keep it independent from recommendation so billing and licensing outages are visible and rare, not tangled with a model release.",
                "concepts": ["Entitlement", "Short-lived tokens", "Territory rules", "Offline grants"],
            },
            {
                "name": "Audio CDN",
                "anchor": "audio-cdn",
                "context": "Tracks are encoded at a few bitrates and stored as objects. Popular tracks should already be at the edge. The player can switch bitrate between segments. Because tracks are smaller than movies, caching is easier, but catalog size is huge; not everything can be hot. Origin fill and popularity-based prewarm still matter.",
                "concepts": ["Multi-bitrate audio", "Edge cache", "Popularity prewarm", "Segment fetch"],
            },
            {
                "name": "Playlists",
                "anchor": "playlists",
                "context": "A playlist is an ordered list of track IDs with collaborators and a version. Concurrent edits need a version check or CRDT-like list if many people edit at once. The playlist is not the audio. Sharing a playlist shares metadata and entitlements, not a zip of files.",
                "concepts": ["Ordered lists", "Collaborative versions", "Track pointers", "Cache of playlist JSON"],
            },
            {
                "name": "Recommendations and listen stream",
                "anchor": "spotify-recs",
                "context": "Every play, skip, and completion is an event. Pipelines build features and candidate lists. The online service should read prepared rankings and apply a few rules, not train a model on the request. Deduplicate events so a retried client does not convince you someone looped a track 400 times.",
                "concepts": ["Listen events", "Nearline features", "Prepared rankings", "Event dedup"],
            },
        ],
    },
    {
        "slug": "slack-discord",
        "label": "Slack / Discord",
        "summary": "Team chat is real-time fan-out plus durable history. People expect a message to appear in every open client and to still be there tomorrow after a laptop sleeps. Gateways hold WebSockets. A message service persists first, then publishes. Presence and typing are ephemeral so they do not drown the database.",
        "caption": "WebSocket gateways sit in front. Durable messages and membership sit behind a pub/sub bus.",
        "blueprint_note": "If a client can reconnect and catch up from a sequence number, you can lose a gateway without losing the conversation.",
        "layers": [
            ("Clients", ["Desktop", "Mobile"]),
            ("Edge", ["WebSocket gateway"]),
            ("Services", ["Message API", "Channel router", "Presence", "Notify"]),
            ("Data", ["Message store", "Pub/sub", "Membership"]),
        ],
        "together": "A send call persists a message with a channel sequence, then publishes to the bus. Gateways subscribed to that channel push to connected clients. Offline users get a notification. On reconnect, the client asks for messages after its last sequence. Slow clients are disconnected from live push and told to catch up in batch so one bad laptop does not stall the channel.",
        "takeaway": "Persist, then fan-out, and give every client a cursor so realtime is an acceleration of history.",
        "modules": [
            {
                "name": "WebSocket gateway",
                "anchor": "ws-gateway",
                "context": "Gateways terminate sockets, authenticate, and subscribe the connection to a set of channels. They should be stateless relative to message history. Shard connections by user so a person does not split events across machines without a plan. Heartbeats detect dead phones. This layer is where you apply per-connection backpressure.",
                "concepts": ["WebSockets", "Connection sharding", "Heartbeats", "Slow-consumer handling"],
            },
            {
                "name": "Message API and store",
                "anchor": "message-api",
                "context": "The API is the write authority: permissions, attachments, edits, deletes. Messages get a monotonic sequence per channel. Edits and deletes are new events against that ID so late subscribers converge. Search is a derived index, not the store itself. Large channels need pagination that is stable as new messages arrive.",
                "concepts": ["Per-channel sequence", "Edit/delete events", "Permissioned writes", "Stable history pages"],
            },
            {
                "name": "Channel router and pub/sub",
                "anchor": "channel-router",
                "context": "Pub/sub carries live events to gateways. A channel with hundreds of thousands of members cannot be a single process doing a for-loop. Fan-out trees, partition the channel, or push to online members only and let others catch up. Membership changes must subscribe and unsubscribe gateways without dropping the persist step.",
                "concepts": ["Pub/sub fan-out", "Online vs history", "Membership updates", "Partitioned channels"],
            },
            {
                "name": "Presence and notifications",
                "anchor": "presence-notify",
                "context": "Typing indicators and online flags expire in seconds and should live in memory. Notifications go to devices that have no socket: push, email, or desktop. They must respect mute and mention rules. A notification is a derived event from a persisted message, so retries use the message ID.",
                "concepts": ["Ephemeral presence", "Mute rules", "Push fan-out", "Derived notifications"],
            },
        ],
    },
    {
        "slug": "zoom-google-meet",
        "label": "Zoom / Google Meet",
        "summary": "A meeting is a latency-sensitive media graph. Signaling sets up the room. WebRTC moves audio and video. An SFU forwards streams without mixing every tile into one video, which scales better than an MCU that composites a single layout on the server. Quality is managed continuously through estimates of loss and bandwidth.",
        "caption": "Signaling is a small control plane. Media flows through an SFU. TURN is only the fallback path.",
        "blueprint_note": "If you mix every participant into one server-side video, you pay encode cost on the server for every layout. An SFU forwards selected streams and lets the client decide what to decode.",
        "layers": [
            ("Clients", ["Meeting apps"]),
            ("Edge", ["Signaling", "TURN"]),
            ("Services", ["Meeting control", "SFU / media", "Recording"]),
            ("Data", ["Session state", "Quality logs"]),
        ],
        "together": "A client joins through signaling, receives meeting credentials, and negotiates WebRTC with an SFU in a nearby region. Media packets flow to the SFU, which forwards them to other participants. TURN is used only when direct or peer-reflexive paths fail. Meeting control handles mute, lobby, and host actions as small messages. Recording is a separate subscriber so a recorder crash does not end the live call.",
        "takeaway": "Keep signaling tiny, forward media through an SFU, and treat recording as another subscriber.",
        "modules": [
            {
                "name": "Signaling and meeting control",
                "anchor": "signaling",
                "context": "Signaling exchanges join, leave, SDP offers, and ice candidates. Meeting control applies host policies: mute all, lock the room, admit from lobby. This path is not the video. It must be highly available, but its bandwidth is small. Store just enough session state to reconnect a client that refreshed the tab without creating a second ghost participant.",
                "concepts": ["WebRTC signaling", "SDP / ICE", "Room policy", "Rejoin state"],
            },
            {
                "name": "SFU media servers",
                "anchor": "sfu",
                "context": "A Selective Forwarding Unit receives each sender's stream and forwards it to subscribers. It can drop a video layer when a viewer has little bandwidth instead of transcoding a full MCU layout. Place SFUs regionally. Admission control matters: a 500-person webinar is a different topology from a 3-person standup. Monitor packet loss, jitter, and RTT per stream.",
                "concepts": ["SFU vs MCU", "Simulcast / layers", "Regional placement", "Admission limits"],
            },
            {
                "name": "TURN fallback",
                "anchor": "turn",
                "context": "Some corporate networks block peer-to-peer. TURN relays media through a server you control. It is expensive, so it is a fallback, not the default. Health checks should prove that a client can reach at least one relay before you promise a meeting. Capacity here is a classic overflow pool.",
                "concepts": ["NAT traversal", "Relay cost", "Fallback only", "Reachability checks"],
            },
            {
                "name": "Recording and quality logs",
                "anchor": "recording",
                "context": "Recording subscribes like a hidden participant or taps the SFU. Write media to object storage in chunks so a crash loses seconds, not the hour. Quality logs (loss, bitrate, device) are analytics and should never block sending the next packet. Compliance may require consent flags before this module is allowed to start.",
                "concepts": ["Recording as subscriber", "Chunked storage", "QoS telemetry", "Consent"],
            },
        ],
    },
    {
        "slug": "google-maps",
        "label": "Google Maps",
        "summary": "Maps combine a static, cacheable picture of the world with a dynamic routing problem. Tiles are versioned images or vectors for each zoom and coordinate. Routing searches a road graph. Traffic updates the weights on that graph without forcing every phone to download a new planet.",
        "caption": "The viewport fetches tiles from a CDN. Routes are computed on regional graph replicas using live traffic weights.",
        "blueprint_note": "Do not rebuild tiles because a highway slowed down. Tiles are geography; traffic is a stream of weights.",
        "layers": [
            ("Clients", ["Map app"]),
            ("Edge", ["Tile CDN", "Maps API"]),
            ("Services", ["Tile service", "Routing", "Traffic", "Places"]),
            ("Data", ["Tile pyramid", "Road graph", "Traffic stream"]),
        ],
        "together": "The client asks for tiles covering the viewport and, separately, for a route. Tiles come from a versioned pyramid at the edge. Routing loads a graph partition, applies traffic weights, and returns a polyline plus ETA. Places search uses a geo index for businesses. Navigation keeps requesting traffic deltas, not a new set of basemap tiles, as the car moves.",
        "takeaway": "Split static geographic tiles from dynamic routing and traffic computation.",
        "modules": [
            {
                "name": "Tile service and CDN",
                "anchor": "tiles",
                "context": "The world is cut into tiles at many zoom levels. Each tile is immutable for a map version, which makes CDNs happy. Clients request only what is on screen plus a small prefetch. A new map release is a new version prefix, not an edit in place. Vector tiles move styling to the client; raster tiles are simpler images. Either way, the key is z/x/y plus version.",
                "concepts": ["Tile pyramids", "Immutable versions", "Viewport fetch", "CDN cache keys"],
            },
            {
                "name": "Routing",
                "anchor": "routing",
                "context": "Routing is a shortest-path search on a graph of road segments. Hierarchical techniques and contraction hierarchies keep city-scale queries fast. Alternate routes are bounded; you do not enumerate every path. Partition graphs so a regional replica can answer without loading the planet into one process. When traffic data is missing, fall back to free-flow speeds.",
                "concepts": ["Road graphs", "Shortest path", "Graph partitions", "Bounded alternatives"],
            },
            {
                "name": "Traffic",
                "anchor": "traffic",
                "context": "Probes from phones and historical averages update edge weights. This is a stream. Publish snapshots or deltas to routing replicas. Do not wait for a perfect global picture; a slightly stale weight is better than no route. Extreme incidents can also trigger reroute pushes to active navigations.",
                "concepts": ["Probe streams", "Weight updates", "Historical priors", "Reroute signals"],
            },
            {
                "name": "Places",
                "anchor": "places",
                "context": "Businesses and landmarks live in a geo index with attributes such as hours and category. This is closer to nearby search than to tile rendering. Ranking mixes distance and relevance. Hours can be stale, so show freshness and let the details page re-fetch. Places writes should not block tile reads.",
                "concepts": ["Geo documents", "Distance + relevance", "Freshness labels", "Decoupled writes"],
            },
        ],
    },
    {
        "slug": "food-delivery-swiggy",
        "label": "Food delivery (Swiggy)",
        "summary": "Food delivery coordinates three parties who do not share a process: customer, restaurant, and rider. The order is a state machine. Kitchen time and travel time are estimates that change. Assignment is a smaller version of ride dispatch, with the extra constraint that food is cooling on a counter.",
        "caption": "Three clients publish events into one order lifecycle. Dispatch assigns a rider; ETA combines kitchen and travel.",
        "blueprint_note": "The customer app should read order state, not compute it from independent restaurant and rider APIs.",
        "layers": [
            ("Clients", ["Customer", "Restaurant", "Rider"]),
            ("Edge", ["Order API", "Partner APIs"]),
            ("Services", ["Order lifecycle", "Kitchen", "Dispatch", "ETA", "Payments"]),
            ("Data", ["Order log", "Rider geo", "Menus"]),
        ],
        "together": "A customer places an order and pays. The restaurant accepts and later marks food ready. Dispatch searches nearby riders and leases one. Rider location updates refresh ETA. If the restaurant rejects or the rider vanishes, the order service transitions and may reassign or cancel with a refund. Notifications are derived from those transitions so the three apps do not invent conflicting stories.",
        "takeaway": "Put the order log in the center; treat kitchen and rider as actors that emit events into it.",
        "modules": [
            {
                "name": "Order lifecycle",
                "anchor": "order-lifecycle",
                "context": "This is the product database: placed, accepted, preparing, assigned, picked up, delivered, canceled. Every other module emits events; this module decides whether the transition is legal. Support tools should replay this log. Do not delete a canceled order; you need it for refunds and disputes. Timeouts matter: an unaccepted order cannot sit forever.",
                "concepts": ["Shared state machine", "Legal transitions", "Timeouts", "Support replay"],
            },
            {
                "name": "Kitchen / restaurant",
                "anchor": "kitchen",
                "context": "Restaurants accept, reject, and update prep time. Their systems are unreliable, so the app or a tablet POS should use idempotent commands. Menu and item availability belong here and should flow to the customer catalog asynchronously. A restaurant going offline mid-order is a first-class event, not an error string.",
                "concepts": ["Accept / reject", "Prep-time signals", "Menu availability", "Partner unreliability"],
            },
            {
                "name": "Dispatch and rider geo",
                "anchor": "food-dispatch",
                "context": "Assignment looks like Uber: geo cells, short leases, one rider one order (or a planned batch). Food adds stacking rules and pickup windows. A rider who accepts but never moves must be reassigned. Keep location data hot and the assignment durable on the order.",
                "concepts": ["Geo matching", "Assignment leases", "Batching rules", "Reassignment timers"],
            },
            {
                "name": "ETA and payments",
                "anchor": "food-eta-pay",
                "context": "ETA is kitchen remaining plus travel, with uncertainty. Show a range when inputs are poor. Payments usually authorize up front and capture on success, with refunds on cancel. Promos and delivery fees belong on the order, not only on a receipt PDF. Do not let the rider app invent prices.",
                "concepts": ["Composite ETA", "Uncertainty ranges", "Auth / capture / refund", "Priced on the order"],
            },
        ],
    },
    {
        "slug": "payment-system-stripe",
        "label": "Payment system (Stripe)",
        "summary": "A payment API must survive retries, ambiguous processor answers, and months of disputes. The user-facing charge is a state machine. The money movement is an append-only ledger. Idempotency keys make 'click twice' safe. Reconciliation assumes that your records and the card network will disagree and provides a job to explain the difference.",
        "caption": "Merchants call a payments API. A ledger records money. Webhooks and reconcilers keep merchants and processors aligned.",
        "blueprint_note": "If you only store a mutable 'balance' column, you cannot audit a charge. Always keep the journal.",
        "layers": [
            ("Clients", ["Checkout", "Merchant backend"]),
            ("Edge", ["Payments API"]),
            ("Services", ["Authorization", "Ledger", "Webhooks", "Reconciliation"]),
            ("Data", ["Payment store", "Ledger entries", "Processor reports"]),
        ],
        "together": "Checkout sends a charge with an idempotency key. Authorization talks to the processor and records an attempt. Ledger entries capture the merchant, customer, fees, and pending vs captured amounts. The API returns a stable payment object. Webhooks notify the merchant of the same state. Nightly files from the processor are compared to the ledger; mismatches become tickets, not silent balance edits.",
        "takeaway": "Retries, an append-only ledger, and reconciliation are the product—not just a call to a card network.",
        "modules": [
            {
                "name": "Payments API and idempotency",
                "anchor": "payments-api",
                "context": "The public contract is a payment object and a key the merchant repeats on retry. The first request stores the key and the eventual response. A second request with the same key returns the same object even if the first call timed out after the processor accepted the charge. Without this, you double-bill. Keys need a retention window and a hash of the request so a reused key with different amounts is rejected.",
                "concepts": ["Idempotency keys", "Stable payment objects", "Timeout races", "Request hashing"],
            },
            {
                "name": "Authorization",
                "anchor": "authorization",
                "context": "This module talks to card networks or banks. It models auth, capture, void, refund, and dispute as separate states. Network errors are not failures you can guess; you may need to query the processor or wait for a callback. Never invent a success because a library threw a timeout. Map processor codes into your own state so merchants do not learn every bank's dialect.",
                "concepts": ["Auth vs capture", "Processor ambiguity", "State mapping", "Query-on-timeout"],
            },
            {
                "name": "Ledger",
                "anchor": "ledger",
                "context": "A ledger is append-only entries that must balance. Available and pending balances are views over those entries. Fees, refunds, and chargebacks are new entries, not edits. This is how you answer 'why did this payout change' six months later. Double-entry is not ceremony; it is how money systems stay explainable.",
                "concepts": ["Append-only journal", "Double-entry", "Derived balances", "Immutable corrections"],
            },
            {
                "name": "Webhooks and reconciliation",
                "anchor": "webhooks-recon",
                "context": "Webhooks are at-least-once and can arrive out of order. Sign them, include an event ID, and tell merchants to be idempotent. Reconciliation compares processor settlement files to ledger totals. Differences are normal: timing, fees, partial refunds. A human-readable exception queue is part of the design. Do not 'fix' a mismatch by secretly editing yesterday's entry.",
                "concepts": ["Signed webhooks", "At-least-once events", "Settlement files", "Exception queues"],
            },
        ],
    },
    {
        "slug": "notification-service",
        "label": "Notification service",
        "summary": "Notifications look like 'send a message,' but the system is a router across push, email, and SMS with preferences, priority, and limited retries. The product emits an intent. Channel workers talk to vendors. A user who opted out of marketing must still receive a security code. Those are different pipelines, not a boolean.",
        "caption": "Intents enter a router. Per-channel queues isolate slow vendors. Attempts are recorded so retries stay honest.",
        "blueprint_note": "A notification is not sent until preferences, templates, and idempotency keys say it should be. Vendors fail; your attempt log is the memory.",
        "layers": [
            ("Clients", ["Product services"]),
            ("Edge", ["Notify API"]),
            ("Services", ["Router", "Templates", "Channel workers"]),
            ("Data", ["Preferences", "Attempt log", "Provider queues"]),
        ],
        "together": "A service posts an intent: user, template, priority, dedup key. The router checks preferences and quiet hours, renders a template, and enqueues one or more channel jobs. Workers call vendors and record attempts. Temporary failures retry with backoff; permanent failures stop. Security messages use a separate queue so a marketing blast cannot starve them. The original service can poll or subscribe to delivery state if it must.",
        "takeaway": "Separate intent from delivery, isolate vendors, and let priority plus preferences decide whether a retry is respectful.",
        "modules": [
            {
                "name": "Notify API and router",
                "anchor": "notify-router",
                "context": "The API accepts an intent, not a raw vendor payload. The router chooses channels, drops opted-out marketing, and enforces a dedup key so a retried order event does not SMS twice. Priority selects a queue. This is also where you reject unknown templates before they become poison pills in workers.",
                "concepts": ["Intent vs send", "Dedup keys", "Preference checks", "Priority queues"],
            },
            {
                "name": "Templates",
                "anchor": "templates",
                "context": "Templates keep copy and layout out of every microservice. They need versioning, locale, and a strict variable schema so a missing name cannot produce 'Hello {user}'. Render here, not in each worker, so email and push stay consistent. Preview in staging is part of safety.",
                "concepts": ["Versioned templates", "Locales", "Strict variables", "Preview"],
            },
            {
                "name": "Channel workers",
                "anchor": "channel-workers",
                "context": "One worker pool per vendor isolates timeouts. SMS outages should not block push. Workers record provider message IDs. Retries use exponential backoff and a maximum. Permanent errors such as invalid number go to a suppression list. Rate-limit yourself to stay under vendor caps.",
                "concepts": ["Per-vendor isolation", "Backoff", "Suppression lists", "Vendor rate caps"],
            },
            {
                "name": "Preferences and attempt log",
                "anchor": "prefs-attempts",
                "context": "Preferences are the user's contract. Attempt logs are yours: what you tried, when, and why it stopped. They power support and compliance. Retention should be long enough to debug and short enough to respect privacy. Do not use the attempt log as a marketing analytics warehouse without a plan.",
                "concepts": ["Opt-in / opt-out", "Audit of sends", "Retention", "Support traces"],
            },
        ],
    },
    {
        "slug": "distributed-message-queue-kafka",
        "label": "Distributed message queue (Kafka)",
        "summary": "Kafka is a replicated, partitioned commit log. Producers append. Consumers read at their own offsets. Order is per partition, not global. Replication keeps the log alive when a broker dies. Consumer groups divide partitions among workers. Application correctness still depends on what you do when you crash after processing but before committing an offset.",
        "caption": "Producers append to partitions. Brokers replicate logs. A consumer group shares those partitions and stores offsets.",
        "blueprint_note": "Think 'distributed log,' not 'smart queue that deletes on read.' Retention is time or size, and replay is a feature.",
        "layers": [
            ("Clients", ["Producers", "Consumers"]),
            ("Edge", ["Brokers"]),
            ("Services", ["Controller", "Replication", "Group coordinator"]),
            ("Data", ["Partition logs", "Offsets", "ISR set"]),
        ],
        "together": "A producer chooses a partition, usually by key, and waits for a configured ack. The leader broker appends and followers replicate. The controller manages leadership. Consumers in a group receive a partition assignment from the coordinator and commit offsets as they process. If a consumer dies, partitions rebalance. Hot keys pile onto one partition; that is a design mistake, not a broker bug.",
        "takeaway": "Partitions give you scale and local order; replication gives you durability; your handlers must still be idempotent.",
        "modules": [
            {
                "name": "Brokers and partition logs",
                "anchor": "brokers",
                "context": "A topic is split into partitions, each an ordered log on disk. Throughput scales with partitions, but a single key hashes to one partition. Retention lets consumers rewind. Disk layout and page cache are why sequential appends are fast. Choose partition count with future consumers in mind; shrinking is painful.",
                "concepts": ["Partitions", "Append-only logs", "Retention", "Key hashing"],
            },
            {
                "name": "Replication and controller",
                "anchor": "replication",
                "context": "Each partition has a leader and followers. The in-sync replica set lists who is caught up. Acks=all means the leader waits for ISR. The controller assigns leaders when a broker dies. Replication is not a backup to object storage; it is how the cluster survives a node loss. Unclean leader election is a durability choice you should understand before enabling.",
                "concepts": ["Leader / followers", "ISR", "Ack modes", "Controller failover"],
            },
            {
                "name": "Group coordinator",
                "anchor": "group-coordinator",
                "context": "A consumer group is a team sharing work. The coordinator assigns partitions so each partition has one active reader in the group. Rebalances pause work; cooperative protocols reduce that pause. Static membership helps rolling deploys. This module does not process messages; it decides who may.",
                "concepts": ["Consumer groups", "Rebalance", "Partition assignment", "Static membership"],
            },
            {
                "name": "Offsets",
                "anchor": "offsets",
                "context": "An offset is a bookmark. Commit too early and a crash loses messages. Commit too late and you reprocess. Exactly-once requires transactional producers or idempotent writes in the consumer. Lag is the distance between log end and committed offset; alert on time-to-drain, not only on a raw count.",
                "concepts": ["Offset commit", "At-least-once", "Idempotent consumers", "Consumer lag"],
            },
        ],
    },
    {
        "slug": "reddit",
        "label": "Reddit",
        "summary": "Forums generate a storm of tiny writes—votes and comments—and a smaller set of hot read pages. Raw votes should not update a single global counter row on every click. Comments form a tree that cannot be fetched unbounded. Ranking is a projection you can rebuild if the algorithm changes or abuse is reversed.",
        "caption": "Votes and comments are events. Scores and listing pages are derived. Caches sit in front of hot communities.",
        "blueprint_note": "If you store only the current score, you cannot undo a bot ring. Keep the raw vote.",
        "layers": [
            ("Clients", ["Web / app"]),
            ("Edge", ["API", "Listing cache"]),
            ("Services", ["Post service", "Vote aggregator", "Comment tree", "Ranker"]),
            ("Data", ["Posts", "Raw votes", "Materialized scores"]),
        ],
        "together": "A vote writes a raw event and a worker updates a sharded score. Listings read materialized rankings plus a cache. A comment stores a parent ID; the read path returns a depth-limited slice, with 'load more' for the rest. Moderation events flow through the same projections so a removed post disappears from caches. Abuse systems feed the ranker, they do not edit HTML.",
        "takeaway": "Keep raw interactions, materialize scores, and bound every tree read.",
        "modules": [
            {
                "name": "Post service",
                "anchor": "posts",
                "context": "Posts belong to a community and have visibility states: live, removed, spam, locked. The listing of a community is not a SELECT * FROM posts ORDER BY time. It is a ranked projection. Author edits are versioned so moderation can see what changed. Cross-posts are references, not copies of every comment.",
                "concepts": ["Community partition", "Visibility states", "Derived listings", "Edit history"],
            },
            {
                "name": "Vote aggregator",
                "anchor": "votes",
                "context": "Each user-post pair should vote at most once (or switch once). Write the raw vote, then update a counter shard. Popular posts need sharded counters or a buffer that flushes. Never lock a single score row for a viral thread. Changing your vote is a new event, not an in-place mystery.",
                "concepts": ["Raw vote log", "Sharded counters", "One vote per user", "Async score"],
            },
            {
                "name": "Comment tree",
                "anchor": "comments",
                "context": "Comments are a forest. Store parent IDs and maybe a materialized path. Reads request a root plus a depth and a sibling limit. Sort can be new, old, or ranked. Deep threads need lazy load. Deletes become tombstones so children still have a parent to hang from.",
                "concepts": ["Adjacency / path trees", "Depth limits", "Tombstones", "Ranked comments"],
            },
            {
                "name": "Ranker and listing cache",
                "anchor": "reddit-rank",
                "context": "Hot and best are functions of score, time, and sometimes controversy. Compute them in workers and cache community pages. Cache keys must include sort and filters. A removed post invalidates those keys. Rebuild is possible because raw votes still exist.",
                "concepts": ["Time-decay ranking", "Materialized hot lists", "Cache invalidation", "Rebuild from events"],
            },
        ],
    },
    {
        "slug": "pinterest",
        "label": "Pinterest",
        "summary": "Pinterest is a recommendation-heavy graph of users, boards, and pins. The home feed is not only 'people you follow.' It mixes that graph with related content and trends so a new account is not empty. Images are a CDN problem. Relationships and ranking features are a data problem.",
        "caption": "Pins enter storage and the graph. Candidate sources feed a ranker that builds the home feed.",
        "blueprint_note": "Cold start is a first-class module. If the only source is the follow graph, day-one users bounce.",
        "layers": [
            ("Clients", ["App / web"]),
            ("Edge", ["API", "Image CDN"]),
            ("Services", ["Pin ingest", "Graph", "Candidates", "Ranker"]),
            ("Data", ["Pin store", "Boards graph", "Feature store"]),
        ],
        "together": "A save or upload creates a pin and edges to a board. Ingest extracts image features. Candidate generation reads follows, similar pins, and trends. The ranker orders a bounded set using the feature store. The home feed API pages with a cursor and rechecks that a pin still exists and is allowed. Images never travel through the ranker; the client fetches them from the CDN using keys on the pin.",
        "takeaway": "Use several candidate sources, rank a small set, and keep image bytes on a CDN.",
        "modules": [
            {
                "name": "Pin ingest",
                "anchor": "pin-ingest",
                "context": "Ingest stores the image, extracts a signature for near-dup detection, and writes metadata. Scraped URLs need crawler politeness and spam checks. This pipeline is asynchronous so a save feels instant. The pin ID is the join key for graph edges and features.",
                "concepts": ["Media ingest", "Near-dup signatures", "Spam / crawl rules", "Async enrichment"],
            },
            {
                "name": "Graph",
                "anchor": "pinterest-graph",
                "context": "Users follow users and boards; pins belong to boards; pins can be related. These edges are candidate fuel. Store them in an access-oriented way: 'pins on this board,' 'followers of this board.' Unfollows and deletes must propagate so a private board does not keep leaking through a cached feed.",
                "concepts": ["User/board/pin edges", "Access-oriented queries", "Delete propagation", "Privacy"],
            },
            {
                "name": "Candidates and ranker",
                "anchor": "pinterest-rank",
                "context": "Candidates come from graph neighborhood, visual similarity, and popular topics. Each source should have a quota so one source cannot drown the feed. Ranking uses engagement and freshness. Offline jobs prepare most of this. Online, apply diversity rules so the feed is not twenty near-identical chairs.",
                "concepts": ["Multi-source recall", "Source quotas", "Diversity", "Prepared features"],
            },
            {
                "name": "Image CDN and feature store",
                "anchor": "pinterest-data",
                "context": "Images are resized variants on a CDN. The feature store holds embeddings and counters the ranker needs. Features are versioned because a model trained on last month's schema should not silently read new columns. Evict features for deleted pins.",
                "concepts": ["Image variants", "Feature versions", "Embedding lookup", "Deletion hygiene"],
            },
        ],
    },
    {
        "slug": "tinder",
        "label": "Tinder",
        "summary": "A dating app is geo-aware recommendation plus a tiny set of durable decisions: swipe left, swipe right, and match. Exact GPS should not be a product feature you leak. Candidates are generated in batches, filtered again at serve time, and swipes are append-only so a retry does not create two matches.",
        "caption": "Geo cells and preferences build a candidate stack. Swipes are logged. A mutual like opens a match.",
        "blueprint_note": "The stack you see is a recommendation. The swipe log is the contract. Matches are derived from two complementary likes.",
        "layers": [
            ("Clients", ["App"]),
            ("Edge", ["API"]),
            ("Services", ["Candidate gen", "Geo filter", "Swipe service", "Match service"]),
            ("Data", ["Profiles", "Geo cells", "Swipe log"]),
        ],
        "together": "A session asks for a batch. Geo filter keeps people in a coarse radius and preference window. The client swipes. Each swipe is written once. When a like is mutual, match service creates a conversation thread and notifies both sides. Blocks and reports remove people from future batches immediately. Distance is computed from cells, not from a live share of street address.",
        "takeaway": "Recommend in batches, persist swipes once, and derive matches; keep location coarse.",
        "modules": [
            {
                "name": "Candidate generation",
                "anchor": "tinder-candidates",
                "context": "This module builds a stack using preferences, past swipes, and activity. It should run ahead of the user so swiping feels instant. Exclude already-swiped IDs. For a new user, fall back to popular or recently active profiles in the area. Generation can be approximate; the serve path filters again.",
                "concepts": ["Batch stacks", "Negative filters", "Cold start", "Prefetch"],
            },
            {
                "name": "Geo filter",
                "anchor": "tinder-geo",
                "context": "People are indexed into cells. Query the current cell and neighbors, then widen. Do not return exact coordinates to the other user. Distance bands are enough. Travelers create a burst of writes; those should not explode a single city partition without overflow cells.",
                "concepts": ["Cell indexes", "Neighbor queries", "Privacy-preserving distance", "Travel bursts"],
            },
            {
                "name": "Swipe service",
                "anchor": "swipes",
                "context": "A swipe is unique on (from, to). Replay must not create a second like. Store direction and time. This log is also how you prevent showing the same person again. Rate-limit to reduce bots. The swipe service should not send chat messages; it emits an event if the like might complete a match.",
                "concepts": ["Idempotent swipes", "Uniqueness constraint", "Replay safety", "Bot rate limits"],
            },
            {
                "name": "Match service",
                "anchor": "matches",
                "context": "A match exists when both sides liked. Create it once, open a conversation, and notify. Unmatching is a state change that should hide history according to policy. This module is small and must be correct; duplicate matches confuse billing and chat authorization.",
                "concepts": ["Mutual like", "Exactly-once match", "Conversation grant", "Unmatch policy"],
            },
        ],
    },
    {
        "slug": "google-docs",
        "label": "Google Docs",
        "summary": "Collaborative editing is a consistency problem. Two people type in the same paragraph and both expect their words to remain. Operational Transformation (OT) rewrites incoming operations against a server order. CRDTs encode merge rules in the data type so replicas converge. Presence cursors are ephemeral. Version history is a snapshot plus a log you can compact.",
        "caption": "Editors send operations to a collaboration server. The op log is durable. Presence is not.",
        "blueprint_note": "Pick a merge rule first. The websocket is just the transport for that rule.",
        "layers": [
            ("Clients", ["Editors"]),
            ("Edge", ["Collab socket"]),
            ("Services", ["OT / CRDT engine", "Presence", "Snapshotter"]),
            ("Data", ["Op log", "Document store", "Versions"]),
        ],
        "together": "An editor connects, loads a snapshot plus recent ops, and sends local operations. The engine assigns a sequence (OT) or merges a CRDT state, then broadcasts to others. Presence pings show cursors. Periodically the snapshotter writes a checkpoint so a new client does not replay years of keystrokes. Comments and suggestions are objects with their own IDs so they can ride the same session without breaking the text merge.",
        "takeaway": "Define how concurrent edits converge, persist an operation log, and keep presence off that log.",
        "modules": [
            {
                "name": "Collaboration socket",
                "anchor": "collab-socket",
                "context": "This is a sticky session to a document shard so all live editors of a doc meet the same engine. On reconnect the client sends the last operation ID it applied. The socket should not be the database; if it dies, another instance must load the log. Authz is checked here: a viewer cannot submit edits.",
                "concepts": ["Sticky sessions", "Reconnect cursors", "Document sharding", "Edit vs view"],
            },
            {
                "name": "OT / CRDT engine",
                "anchor": "ot-crdt",
                "context": "OT transforms an operation against concurrent ones so the server's order still preserves intent. CRDTs give each insert an identity so replicas can merge without a single transformer. Both need operation IDs and a story for undo. Choose one family and keep it; mixing ad hoc string patches will diverge. Large docs may split into blocks to keep transforms cheap.",
                "concepts": ["Operational transformation", "CRDTs", "Intent preservation", "Block sharding"],
            },
            {
                "name": "Presence",
                "anchor": "docs-presence",
                "context": "Cursors and selections expire when a socket goes quiet. They are broadcast but not written into the document history. Storing them durably would explode the version list and lie after a laptop sleeps. Color and name are display metadata on the session, not on the paragraph.",
                "concepts": ["Ephemeral cursors", "Session metadata", "TTL presence", "No history pollution"],
            },
            {
                "name": "Snapshotter and version store",
                "anchor": "snapshots",
                "context": "The op log grows forever unless you checkpoint. A snapshot is a document state at a sequence. Older ops can be compacted after all clients are beyond them. Named versions are user-facing restore points. Compaction must not destroy legal evidence the product promised to keep.",
                "concepts": ["Checkpoints", "Log compaction", "Named versions", "Restore"],
            },
        ],
    },
    {
        "slug": "yelp-nearby-places",
        "label": "Yelp / nearby places",
        "summary": "Nearby search asks: what businesses around this point match a query, and which should appear first? Scanning every restaurant in the country is not an option. Geohashes and quadtrees bucket the map. Ranking then combines distance with review quality. The read path is heavy; writes to hours and reviews are eventually visible.",
        "caption": "A location query expands a few geo cells, fetches candidates, then ranks. Details are cached separately.",
        "blueprint_note": "Cell boundaries miss edge results, so you always search neighbors. Distance alone is a poor ranking function.",
        "layers": [
            ("Clients", ["App / web"]),
            ("Edge", ["Search API", "Details cache"]),
            ("Services", ["Geo index", "Ranker", "Reviews"]),
            ("Data", ["Business docs", "Geohash / quadtree", "Review store"]),
        ],
        "together": "The API receives a point, radius, and text. Geo index returns business IDs in the covering cells plus neighbors. Ranker fetches documents, applies filters such as open-now (rechecked if stale), and sorts. The client then loads details and photos from cache. A new review updates the review store and eventually the document's average; it should not lock the geo index. Hot downtown cells are split so one partition does not own all of a city center.",
        "takeaway": "Bound space with cells, rank a candidate set, and keep review writes off the search critical path.",
        "modules": [
            {
                "name": "Geo index",
                "anchor": "geo-index",
                "context": "Geohash encodes a point into a string prefix that nearby points share. Quadtrees recursively split space where density is high. Either structure turns 'near me' into a few bucket lookups. You must query neighbors because a restaurant across the hash boundary is still next door. Split hot cells; do not keep a single 'downtown' bucket forever.",
                "concepts": ["Geohash", "Quadtrees", "Neighbor cells", "Hot-cell splits"],
            },
            {
                "name": "Ranker",
                "anchor": "yelp-rank",
                "context": "Candidates are cheap; ranking is the product. Signals include distance, rating, review count, category match, and personal history. 'Open now' should be revalidated because hours change. Empty result sets should widen radius or relax filters rather than return a proud zero. Pagination uses a cursor over the ranked list.",
                "concepts": ["Distance + quality", "Open-now recheck", "Radius widening", "Cursors"],
            },
            {
                "name": "Reviews",
                "anchor": "reviews",
                "context": "Reviews are a write-heavy sidecar. They need moderation, spam detection, and an aggregate that can be recomputed. Do not average in place without remembering counts. Photos are objects on a CDN. A review is not a reason to rebuild the entire geo tree.",
                "concepts": ["Append reviews", "Moderation", "Recomputable aggregates", "Async document update"],
            },
            {
                "name": "Business documents and cache",
                "anchor": "yelp-docs",
                "context": "The search document is denormalized: name, coords, category, coarse hours, rating. Details pages can be richer and more cached. When a business moves, both the document and the geo bucket change. Tombestone closed businesses so old deep links explain why a pin vanished.",
                "concepts": ["Denormalized docs", "Details cache", "Move / rebucket", "Closed tombstones"],
            },
        ],
    },
]


def apply(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if len(SYSTEMS) != 30:
        raise SystemExit(f"Expected 30 systems, found {len(SYSTEMS)}")
    slugs = [str(system["slug"]) for system in SYSTEMS]
    if len(set(slugs)) != 30:
        raise SystemExit("Duplicate system slugs")
    data["system-design"] = {
        "title": "System Design",
        "deck": "Beginner-friendly case studies. Each page has a blueprint of the internal modules, an explanation of what every module owns, and the core concepts that module uses.",
        "kicker": "09 · Case studies",
        "sections": [
            {
                "slug": system["slug"],
                "label": system["label"],
                "html": article_html(system),
            }
            for system in SYSTEMS
        ],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(SYSTEMS)} system design blueprints to {path}")


if __name__ == "__main__":
    apply(Path(__file__).resolve().parents[1] / "content" / "manual_topics.json")
