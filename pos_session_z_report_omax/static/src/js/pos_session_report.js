/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.report = useService("report");
    },
    async clickSessionZReport() {
        if (this.props.close) {
            this.props.close();
        }
        await this.report.doAction("pos_session_z_report_omax.action_report_session_z", [
            this.pos.session.id,
        ]);
    },
});

