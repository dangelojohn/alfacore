# SPDX-License-Identifier: LGPL-3.0-only
"""Technical Service Bulletin (TSB) document.

TSBs are the manufacturer's accumulated diagnostic wisdom — known patterns,
recommended procedures, calibration updates. They are the substrate of the
Pro-tier diagnostic edge.

Per Service Plan §8 — TSBs are chunked, embedded into Qdrant, and retrieved
during diagnosis as context for the LLM. This module owns the document
side; the RAG retrieval lives in the diagnosis pipeline (Sprint 6+).
"""

from odoo import _, api, fields, models


class AlfaTsb(models.Model):
    _name = "alfa_tsb.tsb"
    _description = "Technical Service Bulletin"
    _inherit = ["mail.thread"]
    _order = "issued_date desc, id desc"

    name = fields.Char(
        required=True,
        tracking=True,
        help="TSB title, e.g. 'Turbo Wastegate Rattle Diagnosis (Giorgio 2.0L)'.",
    )
    bulletin_number = fields.Char(
        required=True,
        copy=False,
        index=True,
        help="Manufacturer's bulletin identifier, e.g. '07-080-21'.",
    )
    manufacturer = fields.Char(default="Alfa Romeo", required=True)
    issued_date = fields.Date(tracking=True)
    superseded_by_id = fields.Many2one("alfa_tsb.tsb", string="Superseded By")
    supersedes_id = fields.Many2one("alfa_tsb.tsb", string="Supersedes")

    summary = fields.Text(translate=True)
    symptoms = fields.Text(
        translate=True, help="Plain-language symptoms the customer or technician reports."
    )
    procedure = fields.Text(translate=True, help="Step-by-step repair / diagnostic procedure.")

    # Source document
    source_url = fields.Char()
    document_attachment_id = fields.Many2one("ir.attachment", string="Source PDF")
    full_text = fields.Text(help="Extracted plain text. Source of truth for chunking.")

    # Fitment
    fits_platform_ids = fields.Many2many(
        "alfa_fleet.platform", relation="alfa_tsb_platform_rel", string="Affected Platforms"
    )
    fits_engine_ids = fields.Many2many(
        "alfa_fleet.engine", relation="alfa_tsb_engine_rel", string="Affected Engines"
    )
    affected_year_from = fields.Integer()
    affected_year_to = fields.Integer()

    # Related diagnostics
    related_dtc_codes = fields.Char(
        help="Comma-separated DTC codes this TSB addresses, e.g. 'P0234,P200A'."
    )

    # Ingestion state
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("published", "Published"),
            ("chunked", "Chunked"),
            ("indexed", "Indexed (Qdrant)"),
            ("retired", "Retired"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    chunk_ids = fields.One2many("alfa_tsb.chunk", "tsb_id", string="Chunks")
    chunk_count = fields.Integer(compute="_compute_chunk_stats", store=True)
    indexed_chunk_count = fields.Integer(compute="_compute_chunk_stats", store=True)
    indexed_at = fields.Datetime()

    _bulletin_num_uniq = models.Constraint(
        "UNIQUE(bulletin_number, manufacturer)",
        "Bulletin number must be unique per manufacturer.",
    )

    @api.depends("chunk_ids.indexed_at")
    def _compute_chunk_stats(self):
        for tsb in self:
            tsb.chunk_count = len(tsb.chunk_ids)
            tsb.indexed_chunk_count = len(tsb.chunk_ids.filtered("indexed_at"))

    def action_chunk(self):
        """Split full_text into chunks for embedding.

        Naive chunker — splits on paragraph boundaries with a max char window.
        Claude Code can swap for a smarter splitter (sentence tokenizer,
        recursive character splitter) keeping the same model contract.
        """
        Chunk = self.env["alfa_tsb.chunk"]
        for tsb in self:
            if not tsb.full_text:
                continue
            # Clear existing chunks (re-chunking)
            tsb.chunk_ids.unlink()
            paragraphs = [p.strip() for p in tsb.full_text.split("\n\n") if p.strip()]
            CHUNK_MAX_CHARS = 1500
            chunks_vals = []
            current = ""
            idx = 0
            for para in paragraphs:
                if len(current) + len(para) > CHUNK_MAX_CHARS and current:
                    chunks_vals.append(
                        {
                            "tsb_id": tsb.id,
                            "chunk_index": idx,
                            "text": current.strip(),
                        }
                    )
                    idx += 1
                    current = para
                else:
                    current = (current + "\n\n" + para) if current else para
            if current:
                chunks_vals.append(
                    {
                        "tsb_id": tsb.id,
                        "chunk_index": idx,
                        "text": current.strip(),
                    }
                )
            if chunks_vals:
                Chunk.create(chunks_vals)
            tsb.state = "chunked"
            tsb.message_post(body=_("Chunked into %d chunks.") % len(chunks_vals))

    def action_index_to_qdrant(self):
        """Trigger Qdrant indexing of all chunks. Stub — see qdrant_client."""
        client = self.env["alfa_tsb.qdrant_client"]
        for tsb in self:
            client.index_chunks(tsb.chunk_ids)
            tsb.state = "indexed"
            tsb.indexed_at = fields.Datetime.now()
