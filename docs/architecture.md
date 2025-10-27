# Architecture Documentation

## System Overview

Distributed Synchronization System adalah implementasi lengkap dari sistem terdistribusi yang menggabungkan tiga komponen utama:

1. **Distributed Lock Manager** - Menggunakan Raft Consensus
2. **Distributed Queue System** - Dengan Consistent Hashing
3. **Distributed Cache Coherence** - Implementasi MESI Protocol

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│                   (Applications & Services)                     │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                       API Gateway Layer                         │
│              (Load Balancing & Request Routing)                 │
└────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Node 1     │      │   Node 2     │      │   Node 3     │
│  (Leader)    │◄────►│ (Follower)   │◄────►│ (Follower)   │
│              │      │              │      │              │
│ ┌──────────┐ │      │ ┌──────────┐ │      │ ┌──────────┐ │
│ │Lock Mgr  │ │      │ │Lock Mgr  │ │      │ │Lock Mgr  │ │
│ │          │ │      │ │          │ │      │ │          │ │
│ └──────────┘ │      │ └──────────┘ │      │ └──────────┘ │
│ ┌──────────┐ │      │ ┌──────────┐ │      │ ┌──────────┐ │
│ │Queue Node│ │      │ │Queue Node│ │      │ │Queue Node│ │
│ │          │ │      │ │          │ │      │ │          │ │
│ └──────────┘ │      │ └──────────┘ │      │ └──────────┘ │
│ ┌──────────┐ │      │ ┌──────────┐ │      │ ┌──────────┐ │
│ │Cache Node│ │      │ │Cache Node│ │      │ │Cache Node│ │
│ │  (MESI)  │ │      │ │  (MESI)  │ │      │ │  (MESI)  │ │
│ └──────────┘ │      │ └──────────┘ │      │ └──────────┘ │
│              │      │              │      │              │
│ ┌──────────┐ │      │ ┌──────────┐ │      │ ┌──────────┐ │
│ │Raft Core │ │      │ │Raft Core │ │      │ │Raft Core │ │
│ └──────────┘ │      │ └──────────┘ │      │ └──────────┘ │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │   Redis Persistence   │
                  │  (Message Storage)    │
                  └───────────────────────┘
```

## Component Details

### 1. Raft Consensus Layer

**Purpose**: Provides distributed consensus untuk semua komponen

**Key Features**:
- Leader election dengan randomized timeouts
- Log replication untuk state consistency
- Safety guarantees (Election Safety, Leader Append-Only, etc.)
- Network partition tolerance

**States**:
- `FOLLOWER`: Default state, menerima AppendEntries dari leader
- `CANDIDATE`: Competing untuk menjadi leader
- `LEADER`: Menangani semua client requests

**Message Types**:
- `RequestVote`: Untuk leader election
- `AppendEntries`: Untuk log replication dan heartbeat
- `ClientRequest`: Untuk client operations

### 2. Distributed Lock Manager

**Purpose**: Menyediakan distributed locking dengan deadlock detection

**Lock Types**:
- **Shared Lock**: Multiple readers dapat hold lock bersamaan
- **Exclusive Lock**: Hanya satu writer dapat hold lock

**Deadlock Detection**:
- Menggunakan wait-for graph
- Cycle detection algorithm
- Automatic deadlock resolution dengan aborting youngest transaction

**Lock Acquisition Flow**:
```
Client Request
    │
    ▼
Submit to Raft Consensus
    │
    ▼
Log Replication
    │
    ▼
State Machine Apply
    │
    ▼
Check Lock Availability
    │
    ├─► Available → Grant Lock
    │
    └─► Unavailable → Add to Wait Queue
            │
            ▼
        Deadlock Check
```

### 3. Distributed Queue System

**Purpose**: Message queue dengan at-least-once delivery guarantee

**Key Components**:

**Consistent Hashing**:
- Virtual nodes untuk load balancing
- Minimal data movement saat node join/leave
- Deterministic partition assignment

**Message Flow**:
```
Producer
    │
    ▼
Partition Selection (Consistent Hashing)
    │
    ▼
Append to Partition Queue
    │
    ▼
Persist to Redis
    │
    ▼
Consumer Poll
    │
    ▼
Message Delivery
    │
    ▼
Acknowledgment
    │
    ├─► ACK Received → Delete from Redis
    │
    └─► Timeout → Redeliver
```

**Delivery Guarantee**:
- At-least-once delivery
- Pending ACK tracking
- Automatic redelivery pada timeout

### 4. Distributed Cache Coherence

**Purpose**: Maintain cache consistency across nodes dengan MESI protocol

**MESI States**:

| State | Description | Valid | Dirty |
|-------|-------------|-------|-------|
| **M**odified | Cache has exclusive, modified copy | ✓ | ✓ |
| **E**xclusive | Cache has exclusive, clean copy | ✓ | ✗ |
| **S**hared | Cache has shared, clean copy | ✓ | ✗ |
| **I**nvalid | Cache line is invalid | ✗ | ✗ |

**State Transitions**:

```
Read Hit:
I → S/E (fetch from memory)
S → S (no change)
E → E (no change)
M → M (no change)

Write:
I → M (invalidate others)
S → M (invalidate others)
E → M (no invalidation needed)
M → M (no change)

Invalidation:
M → I (writeback required)
E → I (no writeback)
S → I (no writeback)
```

**Cache Coherence Protocol**:
```
Write Operation
    │
    ▼
Check Current State
    │
    ├─► Modified → Update locally
    │
    ├─► Exclusive → Transition to M, update
    │
    ├─► Shared → Invalidate others, transition to M
    │
    └─► Invalid → Fetch, invalidate others, write
```

**LRU Replacement**:
- OrderedDict untuk O(1) access dan update
- Automatic eviction saat capacity exceeded
- Size tracking dan monitoring

## Communication Layer

**Network Transport**:
- HTTP-based dengan aiohttp
- Async I/O untuk high concurrency
- Automatic retry dan timeout handling

**Failure Detection**:
- Phi Accrual Failure Detector
- Probabilistic failure detection
- Heartbeat-based monitoring

## Data Persistence

**Redis Integration**:
- Message persistence untuk queue
- State backup untuk recovery
- Automatic cleanup dengan TTL

## Performance Optimizations

1. **Async I/O**: Non-blocking operations untuk semua network calls
2. **Batching**: Log entries batched untuk replication
3. **Pipelining**: Multiple requests processed simultaneously
4. **Caching**: Frequently accessed data cached locally
5. **Connection Pooling**: Reuse connections untuk efficiency

## Scalability Considerations

**Horizontal Scaling**:
- Add more nodes ke cluster
- Consistent hashing ensures minimal reshuffling
- Leader election automatically adapts

**Vertical Scaling**:
- Increase cache size per node
- More worker threads untuk processing
- Larger message buffers

## Fault Tolerance

**Network Partitions**:
- Raft guarantees consistency dengan quorum
- Minority partitions become read-only
- Automatic healing saat partition resolved

**Node Failures**:
- Automatic leader re-election
- Message redelivery dari persistence
- Cache coherence maintained

**Data Loss Prevention**:
- Write-ahead logging
- Redis persistence
- Replication across nodes

## Security (Optional Bonus)

**Encryption**:
- TLS untuk inter-node communication
- Data encryption at rest

**Authentication**:
- JWT tokens untuk client authentication
- Certificate-based node authentication

**Authorization**:
- RBAC untuk resource access
- Audit logging untuk compliance

## Monitoring & Metrics

**Prometheus Metrics**:
- Request counts dan latencies
- Lock statistics
- Queue sizes
- Cache hit rates
- Raft consensus metrics
- System resources (CPU, Memory, Network)

**Logging**:
- Structured logging dengan Loguru
- Multiple log levels
- Log rotation dan compression
- Centralized log aggregation

## API Endpoints (To be implemented with FastAPI)

### Lock Manager
- `POST /lock/acquire` - Acquire lock
- `POST /lock/release` - Release lock
- `GET /lock/status/{resource_id}` - Get lock status

### Queue
- `POST /queue/produce` - Produce message
- `GET /queue/consume` - Consume message
- `POST /queue/ack` - Acknowledge message

### Cache
- `GET /cache/read/{key}` - Read from cache
- `POST /cache/write` - Write to cache
- `DELETE /cache/invalidate/{key}` - Invalidate cache line

### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /status` - System status

## Deployment Architecture

**Docker Deployment**:
```
docker-compose.yml
├── redis (persistence)
├── node-1 (leader candidate)
├── node-2 (follower)
├── node-3 (follower)
└── prometheus (monitoring)
```

**Kubernetes Deployment** (Bonus):
```
StatefulSet:
├── distributed-node-0
├── distributed-node-1
└── distributed-node-2

Services:
├── distributed-headless (for peer discovery)
└── distributed-external (for client access)
```

## References

1. **Raft Consensus**: "In Search of an Understandable Consensus Algorithm" - Diego Ongaro, John Ousterhout
2. **MESI Protocol**: "Computer Architecture: A Quantitative Approach" - Hennessy & Patterson
3. **Consistent Hashing**: "Consistent Hashing and Random Trees" - Karger et al.
4. **Failure Detection**: "The φ Accrual Failure Detector" - Hayashibara et al.
