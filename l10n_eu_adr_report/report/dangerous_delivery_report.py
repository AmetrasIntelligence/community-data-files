# Copyright 2019 Iryna Vyshnevska (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from itertools import groupby

from odoo import models


class DangerousDeliveryADR(models.AbstractModel):
    _name = "report.l10n_eu_adr_report.report_delivery_dangerous"
    _description = "Dangerous Delivery Report ADR"

    def _get_report_values(self, docids, data=None):
        docs = self.env["stock.picking"].browse(docids)
        data = data or {}
        docargs = {
            "doc_ids": docs.ids,
            "doc_model": "stock.picking",
            "docs": docs,
            "data": data.get("form", False),
            "page_lines": {"dg_lines": self._get_dangerous_goods_lines(docs)},
        }
        return docargs

    def _get_dangerous_goods_lines(self, pickings):
        lines = []
        for picking in pickings:
            if picking.state == "done":
                moves = picking.move_ids.filtered(lambda m: m.state == "done")
            else:
                moves = picking.move_ids
            dangerous_moves = moves.filtered(lambda m: m.product_id.is_dangerous)
            grouped_moves = groupby(
                sorted(dangerous_moves, key=lambda m: m.product_id.id),
                lambda m: m.product_id,
            )
            lines += [
                self._get_dangerous_goods_line_vals(product, list(product_moves))
                for product, product_moves in grouped_moves
            ]
        return lines

    def _get_dangerous_goods_line_vals(self, product, moves):
        qty = sum(
            m.quantity_done if m.state == "done" else m.product_uom_qty for m in moves
        )
        return {
            "product": product,
            "adr_class_id": "{}, {}, {}, {}, {}".format(
                product.adr_class_id.name,
                qty,
                product.adr_packing_instruction_ids.mapped("code"),
                qty * product.weight,
                product.adr_limited_quantity_uom_id.name,
            ),
            "packaging_type": product.adr_packing_instruction_ids.mapped("code"),
            "qty_amount": qty,
            "product_weight": product.weight,
            "column_index": str(product.adr_transport_category),
        }
