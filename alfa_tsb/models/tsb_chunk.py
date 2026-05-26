# SPDX-License-Identifier: LGPL-3.0-only
"""Chunk of a TSB document — the unit of Qdrant ingestion."""

from odoo import fields, models


class AlfaTsbChunk(models.Model):
    _name = "alfa_tsb.chunk"
    _description = "TSB Chunk"
    _order = "tsb_id, chunk_index"

    tsb_id = fields.Many2one("alfa_tsb.tsb", required=True, ondelete="cascade", index=True)
    chunk_index = fields.Integer(required=True)
    text = fields.Text(required=True)

    # Qdrant point reference
    qdrant_point_id = fields.Char(
        index=True, help="UUID/ULID of the point in Qdrant. Set after indexing."
    )
    qdrant_collection = fields.Char(default="alfa_tsb_v1")
    embedding_model = fields.Char(
        default="bge-large-en-v1.5", help="Embedding model used. Cache invalidation key."
    )
    indexed_at = fields.Datetime()

    _tsb_chunk_idx_uniq = models.Constraint(
        "UNIQUE(tsb_id, chunk_index)",
        "Chunk index must be unique within a TSB.",
    )
