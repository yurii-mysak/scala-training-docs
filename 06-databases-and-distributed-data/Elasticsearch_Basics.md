# Elasticsearch Basics – Text Analysis & Inverted Index

---

## 1 · Why Elasticsearch?

* Full‑text search with relevance scoring.  
* Near‑real‑time indexing (~1 s refresh).  
* Horizontal scaling with sharding + replicas.

---

## 2 · Inverted Index

Documents → token stream → posting list:

```
Token  ->  DocIDs
"scala" -> [1, 4, 7]
"java"  -> [2, 7]
```

Enables O(1) term lookup.

---

## 3 · Text Analysis Pipeline

1. **Character filters** (HTML strip).  
2. **Tokenizer** (standard, whitespace).  
3. **Token filters** (lowercase, stemmer, stop words).

Custom analyzer example:

```json
"analysis": {
  "analyzer": {
    "blog_analyzer": {
      "type": "custom",
      "tokenizer": "standard",
      "filter": ["lowercase","english_stemmer"]
    }
  }
}
```

---

## 4 · Sharding & Replicas

* Index split into *primary shards*; each shard an LSM‑based segment library.  
* Replicas provide HA & search fan‑out.  
* Rebalancing via `cluster.routing.allocation.*` settings.

---

## 5 · Query DSL snippets

```json
{
  "query": {
    "bool": {
      "must":   {"match": {"body":"scala"}},
      "filter": {"term":  {"status":"PUBLISHED"}}
    }
  }
}
```

---

## 6 · Tuning tips

| Tip | Benefit |
|-----|---------|
| Use `keyword` sub‑field for exact matches | Avoid analysing IDs |
| Increase `refresh_interval` | Higher bulk ingest throughput |
| Avoid large fields in `_source` | Reduce heap usage |

