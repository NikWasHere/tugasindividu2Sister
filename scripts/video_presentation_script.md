# 🎥 Script Presentasi Video - Distributed Synchronization System

**Durasi Target:** 10-15 menit  
**Format:** Screen recording + narasi bahasa Indonesia  
**Platform Upload:** YouTube (unlisted/public)

---

## 📋 CHECKLIST PERSIAPAN

### Before Recording:
- [ ] Install semua dependencies (`pip install -r requirements.txt`)
- [ ] Test run semua komponen (unit tests, Docker, benchmarks)
- [ ] Siapkan terminal windows yang clean
- [ ] Siapkan browser untuk demo API
- [ ] Buka Postman/Insomnia atau gunakan API client script
- [ ] Siapkan text editor untuk show code highlights
- [ ] Check audio quality microphone
- [ ] Close aplikasi yang tidak perlu (notifikasi, etc)

### Recording Tools:
- **Screen Recording:** OBS Studio / Camtasia / Bandicam / Windows Game Bar
- **Audio:** Built-in mic atau external mic (pastikan clear)
- **Resolution:** 1920x1080 (Full HD) recommended
- **Frame Rate:** 30 FPS minimum

---

## 🎬 STRUKTUR VIDEO

### **SEGMENT 1: PENDAHULUAN** (1-2 menit)

**[SCENE: Slide atau Title Screen]**

**Script Narasi:**
```
Assalamualaikum warahmatullahi wabarakatuh.
Selamat [pagi/siang/sore], perkenalkan nama saya [NAMA ANDA], 
NIM [NIM ANDA], dari Program Studi [PRODI ANDA].

Pada kesempatan ini, saya akan mempresentasikan Tugas Individu 2
mata kuliah Sistem Terdistribusi tentang implementasi sistem
Distributed Synchronization.

Sistem yang saya bangun ini mencakup tiga komponen utama:
1. Distributed Lock Manager dengan Raft Consensus
2. Distributed Queue System dengan Consistent Hashing
3. Distributed Cache Coherence dengan MESI Protocol

Semua komponen ini dicontainerize menggunakan Docker dan dilengkapi
dengan comprehensive testing serta performance benchmarking.

Mari kita mulai dengan arsitektur sistem.
```

**Visual:** 
- Show title slide dengan nama, NIM, judul tugas
- Transition ke desktop/IDE

---

### **SEGMENT 2: ARSITEKTUR & OVERVIEW** (2-3 menit)

**[SCENE: Show Project Structure]**

**Script Narasi:**
```
Pertama, mari kita lihat struktur project yang telah saya buat.

[OPEN: VS Code atau File Explorer showing project structure]

Seperti yang Anda lihat, project ini terorganisir dengan baik:
- Folder 'src' berisi implementasi core algorithms
- Folder 'tests' untuk unit dan integration tests
- Folder 'benchmarks' untuk performance analysis
- Folder 'docker' untuk containerization
- Dan 'docs' untuk dokumentasi lengkap

[OPEN: docs/architecture.md atau show diagram]

Ini adalah arsitektur sistem secara keseluruhan. 
Kita memiliki 3 node yang membentuk cluster menggunakan Raft consensus.
Setiap node dapat berfungsi sebagai:
- Lock Manager untuk distributed locking
- Queue Node untuk message queuing
- Cache Node untuk distributed caching

Komunikasi antar node menggunakan HTTP dengan aiohttp,
dan semua metrics dikumpulkan menggunakan Prometheus.
```

**Visual:**
- Show project folder structure
- Open architecture.md dan scroll highlights
- Show diagram (jika ada)
- Open beberapa file penting (raft.py, lock_manager.py) untuk preview

**[SCENE: Show Docker Setup]**

**Script Narasi:**
```
[OPEN: docker/docker-compose.yml]

Untuk deployment, saya menggunakan Docker Compose dengan konfigurasi ini.
Ada 3 node yang berjalan di port 8001, 8002, dan 8003,
ditambah Redis untuk persistence dan Prometheus untuk monitoring.

Sekarang mari kita jalankan sistem ini.
```

**Visual:**
- Show docker-compose.yml
- Highlight service definitions

---

### **SEGMENT 3: LIVE DEMONSTRATION** (5-7 menit)

#### **Part A: Starting the System** (1 menit)

**[SCENE: Terminal]**

**Script Narasi:**
```
[OPEN: Terminal/PowerShell]

Saya akan start semua containers menggunakan Docker Compose.

[TYPE & RUN: cd docker]
[TYPE & RUN: docker-compose up -d]

Sekarang kita tunggu beberapa saat hingga semua container ready.

[TYPE & RUN: docker-compose ps]

Seperti yang Anda lihat, semua containers sudah running.
Mari kita check health status.

[TYPE & RUN: docker logs distributed-sync-node-1-1 --tail 20]

Perfect! Node 1 sudah melakukan leader election dan cluster sudah terbentuk.
```

**Visual:**
- Show terminal commands
- Show docker-compose output
- Show container logs

#### **Part B: Distributed Lock Manager Demo** (2 menit)

**[SCENE: Split screen - Terminal + Browser/Postman]**

**Script Narasi:**
```
Sekarang mari kita test Distributed Lock Manager.

[OPEN: Browser atau Postman]

Saya akan acquire exclusive lock pada resource "database-1".

[SHOW API Request]
POST http://localhost:8001/lock/acquire
{
  "resource_id": "database-1",
  "transaction_id": "tx-001",
  "lock_type": "exclusive",
  "timeout": 30
}

[SEND REQUEST & SHOW RESPONSE]

Sukses! Kita mendapat lock dengan lock_id.

Sekarang saya coba acquire lock yang sama dari node lain
dengan transaction berbeda.

[SHOW SECOND REQUEST to localhost:8002]
POST http://localhost:8002/lock/acquire
{
  "resource_id": "database-1",
  "transaction_id": "tx-002",
  "lock_type": "exclusive",
  "timeout": 30
}

[SEND & SHOW RESPONSE]

Seperti yang diharapkan, request ini akan wait atau ditolak
karena resource sudah di-lock oleh tx-001.

Sekarang kita release lock pertama.

[SHOW RELEASE REQUEST]
POST http://localhost:8001/lock/release
{
  "resource_id": "database-1",
  "transaction_id": "tx-001",
  "lock_id": "[lock_id dari response pertama]"
}

Dan sekarang tx-002 bisa mendapat lock-nya.

Ini mendemonstrasikan bahwa distributed locking bekerja dengan benar
across multiple nodes.
```

**Visual:**
- Show API requests and responses
- Use Postman or API client script
- Show logs if needed

#### **Part C: Distributed Queue Demo** (2 menit)

**[SCENE: Browser/Postman]**

**Script Narasi:**
```
Selanjutnya, mari kita test Distributed Queue System.

Saya akan produce beberapa messages ke queue "orders".

[SHOW API REQUEST]
POST http://localhost:8001/queue/produce
{
  "topic": "orders",
  "message": {
    "order_id": "ORD-001",
    "product": "Laptop",
    "quantity": 2
  },
  "priority": 1
}

[SEND REQUEST]

Message berhasil di-produce dengan message_id.

Sekarang saya produce beberapa messages lagi.

[PRODUCE 2-3 more messages]

Baik, sekarang kita consume messages dari node yang berbeda.

[SHOW CONSUME REQUEST to localhost:8002]
POST http://localhost:8002/queue/consume
{
  "topic": "orders",
  "consumer_id": "consumer-1",
  "max_messages": 2
}

[SEND & SHOW RESPONSE]

Kita berhasil consume 2 messages. Perhatikan bahwa messages
ini menggunakan consistent hashing untuk distribution,
sehingga messages bisa tersebar di berbagai partitions.

Sekarang kita acknowledge messages yang sudah diprocess.

[SHOW ACK REQUEST]
POST http://localhost:8002/queue/acknowledge
{
  "topic": "orders",
  "message_ids": ["[message_id_1]", "[message_id_2]"],
  "consumer_id": "consumer-1"
}

Dengan acknowledgment ini, messages tidak akan di-redeliver lagi.
```

**Visual:**
- Show produce/consume/ack requests
- Show multiple messages
- Highlight message_ids

#### **Part D: Distributed Cache Demo** (2 menit)

**[SCENE: Browser/Postman]**

**Script Narasi:**
```
Terakhir, mari kita test Distributed Cache dengan MESI protocol.

Saya akan write data ke cache di node 1.

[SHOW WRITE REQUEST]
POST http://localhost:8001/cache/write
{
  "key": "user:1001",
  "value": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}

[SEND REQUEST]

Data berhasil di-write dalam state Modified.

Sekarang kita read dari node 2.

[SHOW READ REQUEST to localhost:8002]
GET http://localhost:8002/cache/read?key=user:1001

[SEND & SHOW RESPONSE]

Data berhasil dibaca dan sekarang ada di cache node 2
dalam state Shared.

Jika kita write lagi di node 1, cache di node 2 akan
otomatis di-invalidate untuk maintain coherence.

[SHOW WRITE REQUEST to node 1 again]
POST http://localhost:8001/cache/write
{
  "key": "user:1001",
  "value": {
    "name": "John Doe Updated",
    "email": "john.updated@example.com"
  }
}

Dan jika kita read lagi dari node 2, data akan di-fetch ulang
dengan nilai yang updated.

[SHOW READ from node 2 again]

Perfect! MESI protocol bekerja dengan baik untuk maintain
cache coherence across nodes.
```

**Visual:**
- Show write/read requests
- Show cache states if available via metrics/logs
- Demonstrate invalidation

---

### **SEGMENT 4: TESTING & PERFORMANCE** (2-3 menit)

**[SCENE: Terminal]**

**Script Narasi:**
```
Sekarang mari kita lihat hasil testing dan performance benchmarks.

[OPEN: Terminal]

Saya sudah prepare automated testing script.

[TYPE & RUN: python scripts/automated_test.py --all]

Script ini akan menjalankan:
- Unit tests untuk semua komponen
- Integration tests
- Performance benchmarks
- Dan generate reports

[SHOW OUTPUT while running]

Seperti yang Anda lihat, semua unit tests passed.

[WAIT for completion or skip to results]

Mari kita lihat hasil performance benchmarks.

[OPEN: reports/performance/ folder]
[SHOW: generated plots/graphs]

Ini adalah grafik latency untuk lock operations.
Seperti yang terlihat, median latency sekitar 5-10ms,
dengan p99 di bawah 50ms.

[SHOW: throughput graph]

Untuk throughput, sistem bisa handle sekitar 1000-2000
operations per second untuk lock manager.

[SHOW: queue performance]

Queue system menunjukkan throughput yang lebih tinggi,
sekitar 5000-8000 messages per second.

[SHOW: cache performance]

Dan cache operations sangat cepat, dengan latency
di bawah 5ms untuk hits.

Semua hasil ini membuktikan bahwa sistem yang saya bangun
memiliki performance yang baik dan memenuhi requirements.
```

**Visual:**
- Run automated test script (or show pre-recorded results)
- Show performance graphs/charts
- Show test coverage report if available

**[SCENE: Show Code Quality]**

**Script Narasi:**
```
[OPEN: Test coverage report in browser]

Dari hasil testing, kita juga mendapat code coverage report.
Coverage mencapai [X%], yang menunjukkan bahwa sebagian besar
code sudah ter-cover oleh tests.

[OPTIONAL: Show some test code]

Ini contoh salah satu unit test untuk lock manager,
mendemonstrasikan testing untuk deadlock detection.
```

**Visual:**
- Show coverage HTML report
- Briefly show test code example

---

### **SEGMENT 5: KESIMPULAN & PENUTUP** (1-2 menit)

**[SCENE: Back to slides or desktop]**

**Script Narasi:**
```
Baik, untuk kesimpulan.

Pada video ini saya telah mendemonstrasikan implementasi lengkap
sistem Distributed Synchronization yang mencakup:

1. Distributed Lock Manager menggunakan Raft Consensus Algorithm
   dengan fitur deadlock detection yang mampu handle exclusive
   dan shared locks.

2. Distributed Queue System dengan Consistent Hashing untuk
   partitioning dan at-least-once delivery guarantee.

3. Distributed Cache Coherence menggunakan MESI Protocol
   untuk maintain data consistency across nodes.

Semua komponen sudah di-containerize menggunakan Docker,
dilengkapi dengan comprehensive testing suite,
performance benchmarking, dan dokumentasi lengkap.

Dari hasil testing, sistem menunjukkan:
- Lock latency median ~5-10ms
- Queue throughput ~5000-8000 msg/s
- Cache hit latency <5ms
- High availability dengan automatic leader election

Untuk detail lebih lanjut, silakan check:
- Repository GitHub: [URL jika ada]
- Dokumentasi lengkap di folder docs/
- Performance reports di folder reports/

Terima kasih atas perhatiannya.
Wassalamualaikum warahmatullahi wabarakatuh.
```

**Visual:**
- Show summary slide
- Show project structure one more time
- Show README or documentation
- End screen dengan contact info/GitHub link

---

## 🎬 POST-PRODUCTION

### Editing Checklist:
- [ ] Cut dead air dan pauses yang terlalu lama
- [ ] Add intro/outro bumper (optional)
- [ ] Add background music at low volume (optional)
- [ ] Add text overlay untuk highlight penting
- [ ] Add zoom-in untuk code atau terminal yang kecil
- [ ] Check audio levels (normalize jika perlu)
- [ ] Add chapters/timestamps (YouTube)

### Export Settings:
- **Format:** MP4 (H.264)
- **Resolution:** 1920x1080
- **Bitrate:** 8-10 Mbps
- **Audio:** AAC, 192 kbps

### YouTube Upload:
- **Title:** "Tugas Individu 2 - Distributed Synchronization System - [NAMA] - [NIM]"
- **Description:** Include project description, GitHub link, timestamps
- **Tags:** distributed systems, raft consensus, docker, python, async
- **Thumbnail:** Create custom thumbnail dengan title dan visual menarik

### Timestamps untuk YouTube Description:
```
0:00 - Pendahuluan
1:00 - Arsitektur Sistem
3:00 - Live Demo: Lock Manager
5:00 - Live Demo: Queue System
7:00 - Live Demo: Cache Coherence
9:00 - Testing & Performance
11:00 - Kesimpulan
```

---

## 💡 TIPS & BEST PRACTICES

### Recording Tips:
1. **Rehearse dulu** - Practice run minimal 2x sebelum final recording
2. **Speak clearly** - Tidak terlalu cepat, jelas pronounce technical terms
3. **Show, don't just tell** - Lebih banyak demo, less slides
4. **Handle errors gracefully** - Jika ada error, explain dan fix live
5. **Keep it concise** - Target 12-13 menit, max 15 menit

### Common Mistakes to Avoid:
- ❌ Berbicara terlalu cepat atau monoton
- ❌ Terminal font terlalu kecil (use 16-18pt minimum)
- ❌ Tidak explain apa yang sedang dilakukan
- ❌ Skip error handling (show it works AND handles errors)
- ❌ Tidak prepare demo data beforehand
- ❌ Audio quality buruk atau ada background noise

### What to Emphasize:
- ✅ **Raft Consensus** - Explain leader election briefly
- ✅ **Deadlock Detection** - Show or mention wait-for graph
- ✅ **Consistent Hashing** - Explain partitioning concept
- ✅ **MESI Protocol** - Show state transitions
- ✅ **Performance** - Highlight metrics and graphs
- ✅ **Testing** - Show coverage and automated tests
- ✅ **Docker** - Demonstrate easy deployment

---

## 📊 DEMO DATA PREPARATION

Prepare these sample data BEFORE recording:

### Lock Manager Test Data:
```json
// Acquire Lock 1
{"resource_id": "database-1", "transaction_id": "tx-001", "lock_type": "exclusive", "timeout": 30}

// Acquire Lock 2 (conflict)
{"resource_id": "database-1", "transaction_id": "tx-002", "lock_type": "exclusive", "timeout": 30}

// Shared locks
{"resource_id": "file-1", "transaction_id": "tx-003", "lock_type": "shared", "timeout": 30}
{"resource_id": "file-1", "transaction_id": "tx-004", "lock_type": "shared", "timeout": 30}
```

### Queue Test Data:
```json
// Messages to produce
{"topic": "orders", "message": {"order_id": "ORD-001", "product": "Laptop", "quantity": 2}, "priority": 1}
{"topic": "orders", "message": {"order_id": "ORD-002", "product": "Mouse", "quantity": 5}, "priority": 2}
{"topic": "orders", "message": {"order_id": "ORD-003", "product": "Keyboard", "quantity": 3}, "priority": 1}
```

### Cache Test Data:
```json
// Cache writes
{"key": "user:1001", "value": {"name": "John Doe", "email": "john@example.com"}}
{"key": "user:1002", "value": {"name": "Jane Smith", "email": "jane@example.com"}}
{"key": "product:2001", "value": {"name": "Laptop", "price": 15000000}}
```

---

## ✅ FINAL CHECKLIST

Before uploading:
- [ ] Video length 10-15 minutes ✓
- [ ] All components demonstrated ✓
- [ ] Audio clear and audible ✓
- [ ] Screen readable (font size) ✓
- [ ] No sensitive information shown (passwords, tokens, etc) ✓
- [ ] Intro and outro included ✓
- [ ] GitHub link included in description ✓
- [ ] Timestamps added to description ✓
- [ ] Custom thumbnail created ✓
- [ ] Video uploaded to YouTube ✓
- [ ] Link added to README.md ✓

**Good luck dengan video recording! 🎬🚀**
