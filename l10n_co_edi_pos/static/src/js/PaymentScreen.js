odoo.define('l10n_co_edi_jorels_pos.PaymentScreen', function(require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    const JPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            setup() {
                super.setup();
            }
            toggleIsToElectronicInvoice() {
                this.currentOrder.set_to_electronic_invoice(!this.currentOrder.is_to_electronic_invoice());
                this.render(true);
            }
            async _postPushOrderResolve(order, order_server_ids) {
                try {
                    if (order.is_to_invoice()) {
                        const result = await this.rpc({
                            model: 'pos.order',
                            method: 'get_invoice',
                            args: [order_server_ids],
                        }).then(function (invoice) {
                            return invoice;
                        });
                        order.set_invoice(result || null);
                    }
                } finally {
                    return super._postPushOrderResolve(...arguments);
                }
            }
        };

    Registries.Component.extend(PaymentScreen, JPaymentScreen);

    return PaymentScreen;
});