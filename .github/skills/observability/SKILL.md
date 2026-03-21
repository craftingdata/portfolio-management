---
name: observability
description: Monitoring, logging, and tracing guidance (Application Insights, structured logs, metrics, alerting).
---

# When This Skill Applies

- Instrumenting application telemetry and alerts
- Troubleshooting production incidents using logs and metrics
- Setting up Application Insights and custom metrics

Key points:

- Integrate Application Insights via `AzureLogHandler` and export custom metrics where needed.
- Use structured logging with `extra` fields that identify slug, request, revision, or operation context.
- Define alerting thresholds for critical metrics (error rate, latency, failed health checks) and hook alerts to runbooks.
- Use slug, revision, and request correlation consistently when diagnosing ACA behavior.
- Repo split note: observability primitives (logging/tracing/metrics) are Azure Shell underpinnings used by all plugins; avoid domain-specific branching inside the observability layer.

Sample prompts (use to trigger this skill):

- "How should I add structured logging and request correlation for slug-scoped container app operations?"
- "What Application Insights alerts should back Shire deploy and runtime health?"

Logging example (structured):

```python
logger.info("Slug operation", extra={
    "slug": slug,
    "request_id": request_id,
    "revision": revision_name,
})
```

Quick checks:

- Ensure `APPLICATIONINSIGHTS_CONNECTION_STRING` is set in App Configuration / Key Vault and not as raw env var.
- Create alerts for 5xx rate > 1% and avg latency > 1000ms.

## References

- `docs/runbooks.md`
- `docs/security-architecture-soc2.md`
