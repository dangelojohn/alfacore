# SPDX-License-Identifier: LGPL-3.0-only
"""Qdrant collection metadata — tracks what we've configured on the server."""

from odoo import fields, models


class AlfaQdrantCollection(models.Model):
    _name = "alfa_tsb.qdrant_collection"
    _description = "Qdrant Collection"
    _order = "name"

    name = fields.Char(required=True, copy=False)
    vector_size = fields.Integer(
        required=True,
        default=1024,
        help="Dimension of the embedding vectors. Must match embedding model.",
    )
    distance_metric = fields.Selection(
        [
            ("cosine", "Cosine"),
            ("dot", "Dot Product"),
            ("euclid", "Euclidean"),
        ],
        default="cosine",
        required=True,
    )
    embedding_model = fields.Char(default="bge-large-en-v1.5")
    point_count = fields.Integer(help="Last known point count on the server.")
    last_synced_at = fields.Datetime()
    qdrant_host = fields.Char(default="qdrant.zfs531.lan")
    qdrant_port = fields.Integer(default=6333)

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "Collection name must be unique.",
    )
