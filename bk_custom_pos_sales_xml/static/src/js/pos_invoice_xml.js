/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        const order = this.pos.get_order();
        const orderlines = order.get_orderlines();

        // Check if any product barcode is missing
        const missingBarcode = orderlines.find(line => !line.get_product().barcode);

        if (missingBarcode) {
            await this.popup.add(ErrorPopup, {
                title: "Missing Barcode",
                body: `The product "${missingBarcode.get_product().display_name}" has no barcode. Please add one before proceeding.`,
            });
            return; // Stop Sales
        }

        // Generate XML
        const doc = document.implementation.createDocument("", "", null);
        const root = doc.createElement("Invoice");

        const number = order.name?.split("/")[1] || order.name;

        const _createElementWithText = (tag, text) => {
            const el = doc.createElement(tag);
            el.textContent = text;
            return el;
        };

        const _formatDate = (dateString) => {
            const date = new Date(dateString);
            return `${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}.${date.getFullYear()}`;
        };

        root.appendChild(_createElementWithText("Invoice_Type", "Invoice"));
        root.appendChild(_createElementWithText("Reference_Number", number));
        root.appendChild(_createElementWithText("Invoice_Date", _formatDate(order.date_order)));
        root.appendChild(_createElementWithText("Customer_Code", order.partner_ref || ""));
        root.appendChild(_createElementWithText("Customer_Name", order.get_partner()?.name || "Walking Customer"));
        root.appendChild(_createElementWithText("Customer_TIN", order.get_partner()?.vat || ""));
        root.appendChild(_createElementWithText("Payment_Type", "Cash"));
        root.appendChild(_createElementWithText("Invoice_DiscOrAdd_Amount", "0.00"));

        for (const line of orderlines) {
            const item = doc.createElement("Line_Items");
            item.appendChild(_createElementWithText("Item_ID", line.get_product().barcode));
            item.appendChild(_createElementWithText("Item_Description", line.get_product().display_name));
            item.appendChild(_createElementWithText("Item_Quantity", String(line.get_quantity())));
            item.appendChild(_createElementWithText("Item_UOM", line.get_unit()?.name || "Unit"));
            item.appendChild(_createElementWithText("Item_Unit_Price", line.get_unit_price().toFixed(2)));
            item.appendChild(_createElementWithText("Item_Tax_Percent", (line.get_tax() || 0).toFixed(2)));
            item.appendChild(_createElementWithText("Item_DiscOrAdd_Amount", line.get_discount().toFixed(2)));

            root.appendChild(item);
        }

        doc.appendChild(root);
        //trigger Download
        const serializer = new XMLSerializer();
        const xmlString = serializer.serializeToString(doc);

        const blob = new Blob([xmlString], { type: "application/xml" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        const filename = `Invoice_${order.name || order.uid}.xml`;

        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Continue
        await super._finalizeValidation();
    },
});

