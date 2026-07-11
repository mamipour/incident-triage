#!/usr/bin/env python3
"""Generate synthetic incident data for triage search."""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 42
INCIDENT_COUNT = 300
OUTPUT_PATH = Path("data/incidents.json")

ENVIRONMENTS = ["dev", "qa", "stage", "prod"]
SEVERITIES = ["critical", "high", "medium", "low"]

SERVICES = [
    "payment-api",
    "user-auth",
    "notification-service",
    "inventory-db",
    "checkout-frontend",
    "order-processor",
    "search-indexer",
    "analytics-pipeline",
    "cdn-edge",
    "billing-service",
    "support-portal",
    "mobile-backend",
    "fraud-detection",
    "recommendation-engine",
    "webhook-dispatcher",
    "audit-logger",
    "image-resizer",
    "subscription-manager",
    "geo-routing-service",
    "document-parser",
    "metrics-collector",
    "feature-flags-service",
    "session-store",
    "email-gateway",
]

TAGS_POOL = [
    "timeout",
    "database",
    "api",
    "memory",
    "deployment",
    "cache",
    "networking",
    "auth",
    "latency",
    "error-rate",
    "disk",
    "queue",
    "ssl",
    "config",
    "rate-limit",
    "dns",
    "kubernetes",
    "ddos",
    "migration",
    "webhook",
    "cron",
    "secrets",
    "graphql",
    "storage",
    "third-party",
    "failover",
    "monitoring",
    "rollback",
    "saturation",
    "data-corruption",
    "incident-response",
]

REFERENCE_NOW = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)
SIX_MONTHS_AGO = REFERENCE_NOW - timedelta(days=183)

SCENARIOS = [
    {
        "title": "{service} returning 503 errors in {environment}",
        "description": (
            "Users reported widespread failures when calling {service}. "
            "Error rate spiked to {pct}% in {environment}. Logs show upstream "
            "connection timeouts and circuit breaker trips."
        ),
        "resolution_summary": (
            "Scaled {service} replicas and restarted unhealthy pods. "
            "Root cause was connection pool exhaustion under peak load."
        ),
        "tags": ["timeout", "api", "error-rate"],
    },
    {
        "title": "Database connection pool exhausted on {service}",
        "description": (
            "Monitoring alerted on {service} in {environment}: all database "
            "connections in use. Queries queued and request latency exceeded "
            "30 seconds."
        ),
        "resolution_summary": (
            "Increased pool size and terminated long-running queries. "
            "Added index on hot table to reduce lock contention."
        ),
        "tags": ["database", "timeout", "latency"],
    },
    {
        "title": "Authentication failures after {service} deploy",
        "description": (
            "Following a deployment to {environment}, {service} began rejecting "
            "valid tokens. Login success rate dropped sharply across regions."
        ),
        "resolution_summary": (
            "Rolled back the deployment and rotated signing keys. "
            "Updated config validation to catch mismatched issuer URLs."
        ),
        "tags": ["auth", "deployment", "config"],
    },
    {
        "title": "Memory leak detected in {service} ({environment})",
        "description": (
            "Heap usage on {service} climbed steadily over 48 hours in "
            "{environment}. OOM kills restarted pods every few hours."
        ),
        "resolution_summary": (
            "Identified unclosed cache entries in recent release. "
            "Hotfixed memory cleanup and scheduled full redeploy."
        ),
        "tags": ["memory", "deployment", "api"],
    },
    {
        "title": "Redis cache miss storm impacting {service}",
        "description": (
            "{service} in {environment} experienced a cache stampede after "
            "TTL expiry. Database load surged and p99 latency degraded."
        ),
        "resolution_summary": (
            "Enabled request coalescing and staggered cache TTLs. "
            "Warmed critical keys before peak traffic."
        ),
        "tags": ["cache", "database", "latency"],
    },
    {
        "title": "SSL certificate expiry on {service} load balancer",
        "description": (
            "Clients could not reach {service} in {environment} due to an "
            "expired TLS certificate on the load balancer."
        ),
        "resolution_summary": (
            "Renewed certificate and updated auto-renewal alerts. "
            "Verified chain trust across all edge nodes."
        ),
        "tags": ["ssl", "networking", "config"],
    },
    {
        "title": "Message queue backlog on {service}",
        "description": (
            "Consumer lag on {service} in {environment} exceeded one million "
            "messages. Downstream order processing stalled."
        ),
        "resolution_summary": (
            "Scaled consumer workers and replayed dead-letter queue. "
            "Fixed poison message handler that blocked partition reads."
        ),
        "tags": ["queue", "latency", "error-rate"],
    },
    {
        "title": "Rate limiting misconfiguration on {service}",
        "description": (
            "Legitimate traffic to {service} in {environment} was throttled "
            "after a config change lowered rate limits too aggressively."
        ),
        "resolution_summary": (
            "Restored previous rate limit thresholds and added staged rollout "
            "for gateway policy updates."
        ),
        "tags": ["rate-limit", "config", "api"],
    },
    {
        "title": "Disk space critical on {service} nodes",
        "description": (
            "Several {service} hosts in {environment} reached 98% disk usage. "
            "Log rotation failed and write operations began failing."
        ),
        "resolution_summary": (
            "Expanded volumes and purged stale audit logs. "
            "Tuned log retention and added disk usage alerts."
        ),
        "tags": ["disk", "deployment", "error-rate"],
    },
    {
        "title": "Intermittent network partition affecting {service}",
        "description": (
            "{service} in {environment} lost connectivity to a dependency zone "
            "for 12 minutes. Retries caused retry storms across services."
        ),
        "resolution_summary": (
            "Network team restored BGP routing. Added jittered backoff and "
            "bulkhead isolation between dependency calls."
        ),
        "tags": ["networking", "timeout", "api"],
    },
    {
        "title": "DNS resolution failures for {service} in {environment}",
        "description": (
            "Internal clients failed to resolve the {service} hostname in "
            "{environment}. Resolver timeouts caused cascading health check "
            "failures across dependent services."
        ),
        "resolution_summary": (
            "Fixed stale NS records and reduced negative cache TTL. "
            "Added synthetic DNS probes to catch resolver drift early."
        ),
        "tags": ["dns", "networking", "monitoring"],
    },
    {
        "title": "Pod crash loop on {service} after config rollout",
        "description": (
            "{service} pods in {environment} entered CrashLoopBackOff after "
            "a config map update. Startup probes never passed and traffic "
            "shift stalled at {pct}% capacity."
        ),
        "resolution_summary": (
            "Reverted config map and patched invalid environment variable "
            "references. Added schema validation to the deploy pipeline."
        ),
        "tags": ["kubernetes", "deployment", "config"],
    },
    {
        "title": "Third-party API outage blocking {service}",
        "description": (
            "{service} in {environment} depends on an external vendor API that "
            "returned sustained 502 responses. Fallback logic did not activate "
            "and checkout flows failed."
        ),
        "resolution_summary": (
            "Enabled degraded-mode responses and cached last-known-good data. "
            "Opened vendor ticket and documented failover runbook steps."
        ),
        "tags": ["third-party", "api", "failover"],
    },
    {
        "title": "Suspected data corruption in {service} records",
        "description": (
            "Support escalations reported inconsistent account states served by "
            "{service} in {environment}. Audit sampling found mismatched version "
            "fields on {pct}% of recent writes."
        ),
        "resolution_summary": (
            "Paused write path, restored from point-in-time backup, and "
            "replayed events through a repaired serializer."
        ),
        "tags": ["data-corruption", "database", "rollback"],
    },
    {
        "title": "DDoS traffic spike targeting {service}",
        "description": (
            "Edge metrics showed a {pct}× increase in anonymous requests "
            "against {service} in {environment}. Origin CPU saturated and "
            "legitimate users saw elevated error rates."
        ),
        "resolution_summary": (
            "Activated WAF rules and geo-fenced suspicious ASNs. "
            "Scaled edge capacity and enabled challenge mode for abusive IPs."
        ),
        "tags": ["ddos", "networking", "saturation"],
    },
    {
        "title": "Feature flag misconfiguration in {service}",
        "description": (
            "A flag rollout enabled experimental code for all tenants on "
            "{service} in {environment}. Error dashboards spiked within minutes "
            "of the change."
        ),
        "resolution_summary": (
            "Disabled the flag globally and restricted future rollouts to "
            "canary cohorts with automatic rollback thresholds."
        ),
        "tags": ["config", "deployment", "error-rate"],
    },
    {
        "title": "Schema migration timeout on {service} database",
        "description": (
            "An online migration against {service} in {environment} held "
            "table locks for over 20 minutes. Write traffic blocked and "
            "support tickets increased sharply."
        ),
        "resolution_summary": (
            "Cancelled migration, applied changes in smaller batches, and "
            "scheduled remaining steps during a maintenance window."
        ),
        "tags": ["migration", "database", "latency"],
    },
    {
        "title": "Log pipeline drop causing blind spots for {service}",
        "description": (
            "Log shipping from {service} in {environment} fell to near zero. "
            "On-call engineers lost visibility while customer-impacting errors "
            "continued."
        ),
        "resolution_summary": (
            "Restarted log agents and increased buffer limits. "
            "Added alerts on ingest rate anomalies per service."
        ),
        "tags": ["monitoring", "disk", "queue"],
    },
    {
        "title": "Cold start latency regression on {service}",
        "description": (
            "Serverless instances of {service} in {environment} took up to "
            "12 seconds to become ready. Autoscaling added capacity too slowly "
            "during a traffic burst."
        ),
        "resolution_summary": (
            "Pre-warmed minimum instances and trimmed startup dependencies. "
            "Tuned autoscaling signals to react on queue depth."
        ),
        "tags": ["latency", "saturation", "deployment"],
    },
    {
        "title": "Webhook delivery failures from {service}",
        "description": (
            "{service} in {environment} failed to deliver outbound webhooks "
            "after TLS cipher policy tightened. Partner integrations missed "
            "{pct}% of expected callbacks."
        ),
        "resolution_summary": (
            "Restored compatible cipher suites and retried failed deliveries "
            "from the dead-letter store with idempotency keys."
        ),
        "tags": ["webhook", "ssl", "third-party"],
    },
    {
        "title": "Session store unavailable for {service}",
        "description": (
            "Users were logged out repeatedly from {service} in {environment}. "
            "Session cluster nodes reported split-brain and rejected writes."
        ),
        "resolution_summary": (
            "Forced quorum recovery, rebuilt replica set, and extended session "
            "TTL temporarily while caches repopulated."
        ),
        "tags": ["auth", "cache", "failover"],
    },
    {
        "title": "CDN cache serving stale assets for {service}",
        "description": (
            "Customers saw outdated UI assets from {service} in {environment}. "
            "CDN purge jobs failed silently and edge nodes kept old bundles."
        ),
        "resolution_summary": (
            "Issued manual global purge and fixed purge API credentials. "
            "Added post-deploy verification of asset hashes."
        ),
        "tags": ["cache", "deployment", "config"],
    },
    {
        "title": "Scheduled cron job failed on {service}",
        "description": (
            "A nightly reconciliation job for {service} in {environment} "
            "did not run for three days. Billing adjustments backlog grew "
            "to {pct} thousand records."
        ),
        "resolution_summary": (
            "Re-enabled cron scheduler after token expiry fix and backfilled "
            "missed runs with throttled batch workers."
        ),
        "tags": ["cron", "queue", "error-rate"],
    },
    {
        "title": "Secrets rotation broke {service} credentials",
        "description": (
            "Automated secret rotation updated database credentials for "
            "{service} in {environment} but running pods kept stale values. "
            "Connection errors spiked across all zones."
        ),
        "resolution_summary": (
            "Triggered rolling restart after rotation and wired secret reload "
            "hooks into the deployment controller."
        ),
        "tags": ["secrets", "deployment", "database"],
    },
    {
        "title": "GraphQL N+1 query storm on {service}",
        "description": (
            "A new client release issued deeply nested GraphQL queries against "
            "{service} in {environment}. Database CPU hit {pct}% and API "
            "latency exceeded SLOs."
        ),
        "resolution_summary": (
            "Added query cost limits and DataLoader batching for hot resolvers. "
            "Blocked offending client version at the gateway."
        ),
        "tags": ["graphql", "database", "latency"],
    },
    {
        "title": "Load test accidentally run against {service} in {environment}",
        "description": (
            "Engineering triggered a load test profile against live {service} "
            "in {environment}. Synthetic traffic overwhelmed production pools "
            "and displaced real user sessions."
        ),
        "resolution_summary": (
            "Stopped the test harness, restored traffic routing, and enforced "
            "environment guardrails in the load testing tool."
        ),
        "tags": ["saturation", "config", "incident-response"],
    },
    {
        "title": "Timezone handling bug in {service} reports",
        "description": (
            "Daily aggregation jobs for {service} in {environment} shifted "
            "boundaries after DST change. Financial reports showed duplicate "
            "and missing transactions."
        ),
        "resolution_summary": (
            "Patched timezone conversion to use UTC internally and rebuilt "
            "affected report partitions."
        ),
        "tags": ["config", "data-corruption", "cron"],
    },
    {
        "title": "Race condition caused duplicate charges in {service}",
        "description": (
            "Concurrent requests to {service} in {environment} bypassed "
            "idempotency checks under retry storms. Approximately {pct} "
            "customers received duplicate charges."
        ),
        "resolution_summary": (
            "Deployed distributed lock around payment intent creation and "
            "issued refunds for affected transactions."
        ),
        "tags": ["api", "database", "error-rate"],
    },
    {
        "title": "File upload failures on {service} storage backend",
        "description": (
            "Multipart uploads to {service} in {environment} failed with "
            "403 errors. Object storage IAM policy changes blocked the "
            "service account used by the API tier."
        ),
        "resolution_summary": (
            "Restored storage permissions and added policy diff checks to "
            "infrastructure CI before apply."
        ),
        "tags": ["storage", "config", "auth"],
    },
    {
        "title": "Email delivery backlog from {service}",
        "description": (
            "Transactional emails from {service} in {environment} queued for "
            "over six hours. Provider rate limits were exceeded during a "
            "marketing campaign overlap."
        ),
        "resolution_summary": (
            "Throttled bulk sends, prioritized password-reset traffic, and "
            "negotiated temporary provider limit increase."
        ),
        "tags": ["queue", "third-party", "latency"],
    },
]


def random_created_at(rng: random.Random) -> str:
    span_seconds = int((REFERENCE_NOW - SIX_MONTHS_AGO).total_seconds())
    offset = rng.randint(0, span_seconds)
    created = SIX_MONTHS_AGO + timedelta(seconds=offset)
    return created.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def pick_tags(rng: random.Random, scenario_tags: list[str]) -> list[str]:
    extra = rng.sample(
        [tag for tag in TAGS_POOL if tag not in scenario_tags],
        k=rng.randint(0, 2),
    )
    tags = list(dict.fromkeys(scenario_tags + extra))
    return sorted(tags)


def generate_incidents() -> list[dict]:
    rng = random.Random(SEED)
    incidents: list[dict] = []

    for index in range(1, INCIDENT_COUNT + 1):
        scenario = SCENARIOS[(index - 1) % len(SCENARIOS)]
        environment = ENVIRONMENTS[(index - 1) % len(ENVIRONMENTS)]
        service = SERVICES[(index - 1) % len(SERVICES)]
        severity = SEVERITIES[rng.choice(range(len(SEVERITIES)))]
        pct = rng.randint(5, 45)

        context = {
            "service": service,
            "environment": environment,
            "pct": pct,
        }

        incidents.append(
            {
                "id": f"INC-{index:05d}",
                "created_at": random_created_at(rng),
                "environment": environment,
                "service": service,
                "severity": severity,
                "title": scenario["title"].format(**context),
                "description": scenario["description"].format(**context),
                "resolution_summary": scenario["resolution_summary"].format(**context),
                "tags": pick_tags(rng, scenario["tags"]),
            }
        )

    return incidents


def main() -> None:
    if OUTPUT_PATH.exists():
        print(f"{OUTPUT_PATH} already exists — skipping generation.")
        sys.exit(0)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    incidents = generate_incidents()
    OUTPUT_PATH.write_text(
        json.dumps(incidents, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(incidents)} incidents at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
