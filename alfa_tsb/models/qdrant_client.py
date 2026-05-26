# SPDX-License-Identifier: LGPL-3.0-only
"""Qdrant client — STUB.

Production implementation (Claude Code) wraps the qdrant-client Python SDK:

  from qdrant_client import QdrantClient
  from qdrant_client.http.models import PointStruct, VectorParams, Distance

Why stubbed: the embedding step needs a running Ollama server (or other
embedding endpoint) to convert chunk.text to a vector. Both Ollama and
Qdrant want to be tested with the actual stack running, not in CI fixtures.

Contract for downstream callers:
- index_chunks(chunks): take a recordset of alfa_tsb.chunk, embed each,
  upsert to Qdrant, write qdrant_point_id + indexed_at back to the records
- search(query_text, k=5, filter=None): embed the query, query Qdrant,
  return list of (chunk_id, score, text) tuples
- ensure_collection(collection_name, vector_size): idempotent collection
  creation, called once at module install
"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AlfaQdrantClient(models.AbstractModel):
    _name = "alfa_tsb.qdrant_client"
    _description = "Qdrant Client (stub)"

    @api.model
    def index_chunks(self, chunks):
        """Embed and upsert chunks. Stub — marks chunks as indexed without
        actually sending to Qdrant. Production wires real embedding + upsert.
        """
        if not chunks:
            return 0
        _logger.info(
            "Qdrant index_chunks: %d chunks. Stub implementation — no embed/upsert performed. "
            "Wire production embedding + Qdrant upsert in Claude Code (see qdrant_client.py).",
            len(chunks),
        )
        # Stub: pretend it worked so the workflow advances
        for c in chunks:
            c.qdrant_point_id = f"stub-{c.id}"
            c.indexed_at = fields.Datetime.now()
        return len(chunks)

    @api.model
    def search(self, query_text, k=5, filter_=None):
        """Semantic search. Stub returns empty list.

        Real implementation:
          1. Embed query_text → vector
          2. qdrant.search(collection=alfa_tsb_v1, query_vector=vector,
                           limit=k, query_filter=filter_)
          3. Hydrate results back to chunk records via qdrant_point_id
          4. Return [(chunk, score), ...]
        """
        _logger.info(
            "Qdrant search: query='%s' k=%d. Stub — no results returned. "
            "Wire production embedding + search in Claude Code.",
            query_text[:80],
            k,
        )
        return []

    @api.model
    def ensure_collection(self, collection_name="alfa_tsb_v1", vector_size=1024):
        """Idempotent collection creation. Stub — records the intent in
        alfa_tsb.qdrant_collection only; does not call Qdrant.
        """
        Collection = self.env["alfa_tsb.qdrant_collection"].sudo()
        existing = Collection.search([("name", "=", collection_name)], limit=1)
        if existing:
            return existing
        return Collection.create(
            {
                "name": collection_name,
                "vector_size": vector_size,
            }
        )
