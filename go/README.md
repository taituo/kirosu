# Kirosu Go Support

Kirosu is designed to be language-agnostic. While the Hub and primary Agent implementation are in Python, Go workers can easily participate in the swarm.

## Protocol
The Hub communicates via JSON-RPC over TCP (JSONL).

### Request Format
```json
{"id": "uuid", "method": "lease", "params": {"worker_id": "go-worker-1", "max_tasks": 1, "lease_seconds": 300}}
```

### Response Format
```json
{"id": "uuid", "result": {"tasks": [...]}, "error": null}
```

## Implementation Plan
1.  Create a Go struct matching the `Task` schema.
2.  Implement a `HubClient` in Go that connects to the TCP socket.
3.  Implement the worker loop: `lease` -> `process` -> `ack`.

*Coming Soon: Official `kirosu-go` SDK.*
