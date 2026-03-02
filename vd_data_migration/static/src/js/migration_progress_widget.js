/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc"; // standalone function in Odoo 17+

const BATCH_SIZE = 100; // NFR-04

export class MigrationProgressWidget extends Component {
    static template = "vd_data_migration.MigrationProgressWidget";
    static props = { ...standardFieldProps };

    setup() {
        // In Odoo 17+ rpc is a standalone function, NOT a service.
        // useService("rpc") no longer exists.
        this.notification = useService("notification");
        this._stopped     = false;

        const data = this.props.record.data;

        this.state = useState({
            progress:      data.progress       ?? 0,
            label:         data.progress_label ?? "",
            batchesLoaded: 0,
            status:        this._mapWizardState(data.state),
            stats: {
                created: data.stats_created ?? 0,
                updated: data.stats_updated ?? 0,
                errors:  data.stats_errors  ?? 0,
            },
        });

        onMounted(() => {
            if (this.props.record.data.state === "loading") {
                this.startImport(); // intentionally not awaited
            }
        });
    }

    // ── Import orchestration ─────────────────────────────────────────

    async startImport() {
        const data       = this.props.record.data;
        const wizardId   = data.id;
        const startBatch = data.start_batch_number ?? 1;
        const total      = data.record_count_source ?? 0;

        this._stopped            = false;
        this.state.status        = "running";
        this.state.batchesLoaded = 0;
        this.state.stats         = { created: 0, updated: 0, errors: 0 };

        let offset    = (startBatch - 1) * BATCH_SIZE;
        let processed = offset;

        // ── OUTER LOOP: batches ──────────────────────────────────
        outerLoop: while (true) {
            if (this._stopped) break;

            let batchData;
            try {
                batchData = await rpc("/vd_migration/fetch_batch", {
                    wizard_id: wizardId,
                    offset,
                    limit: BATCH_SIZE,
                });
            } catch (err) {
                this.state.status = "error";
                this.notification.add(
                    `Помилка завантаження батчу: ${err.message}`,
                    { type: "danger", sticky: true },
                );
                return;
            }

            if (batchData.error) {
                this.state.status = "error";
                this.notification.add(
                    `Помилка: ${batchData.error}`,
                    { type: "danger", sticky: true },
                );
                return;
            }

            const records = batchData.records ?? [];
            if (records.length === 0) break;

            // ── INNER LOOP: per-record ─────────────────────────
            for (const record of records) {
                if (this._stopped) break outerLoop;

                let result;
                try {
                    result = await rpc("/vd_migration/process_record", {
                        wizard_id: wizardId,
                        record,
                    });
                } catch (err) {
                    this.state.stats.errors += 1;
                    processed += 1;
                    this._updateProgress(processed, total);
                    continue;
                }

                if (!result.error) {
                    this.state.stats.created += result.created ?? 0;
                    this.state.stats.updated += result.updated ?? 0;
                    this.state.stats.errors  += result.errors  ?? 0;
                } else {
                    this.state.stats.errors += 1;
                }

                processed += 1;
                this._updateProgress(processed, total);
            }

            offset += records.length;
            this.state.batchesLoaded += 1;
        }

        // ── Finalize ──────────────────────────────────────────
        const finalState = this._stopped ? "stopped" : "done";
        this.state.status = finalState;

        try {
            await rpc("/vd_migration/finalize", {
                wizard_id: wizardId,
                state:     finalState,
                stats:     { ...this.state.stats },
            });
        } catch (err) {
            this.notification.add(
                `Помилка збереження результатів: ${err.message}`,
                { type: "warning", sticky: false },
            );
        }

        const { created, updated, errors } = this.state.stats;
        const thisRunCount = processed - (startBatch - 1) * BATCH_SIZE;

        if (finalState === "done") {
            this.notification.add(
                `Завершено. Створено: ${created} | Оновлено: ${updated} | Помилок: ${errors}`,
                { type: "success", sticky: true },
            );
        } else {
            this.notification.add(
                `Зупинено. Оброблено: ${thisRunCount} записів.`,
                { type: "warning", sticky: true },
            );
        }
    }

    stopImport() {
        this._stopped = true;
    }

    // ── Computed getters ──────────────────────────────────────────

    get statusLabel() {
        return {
            idle:    "Очікування...",
            running: "Завантаження...",
            done:    "Завершено",
            stopped: "Зупинено",
            error:   "Помилка",
        }[this.state.status] ?? "";
    }

    get statusClass() {
        return {
            idle:    "text-muted",
            running: "text-primary fw-semibold",
            done:    "text-success fw-semibold",
            stopped: "text-warning fw-semibold",
            error:   "text-danger fw-semibold",
        }[this.state.status] ?? "";
    }

    // ── Private helpers ──────────────────────────────────────────

    _updateProgress(processed, total) {
        this.state.progress = total > 0
            ? Math.round((processed / total) * 100)
            : 0;
        this.state.label = `${processed} / ${total} записів`;
    }

    _mapWizardState(wizardState) {
        return { loading: "running", done: "done", stopped: "stopped" }[wizardState] ?? "idle";
    }
}

registry.category("fields").add("vd_migration_progress", {
    component:      MigrationProgressWidget,
    displayName:    "Migration Progress",
    supportedTypes: ["integer"],
});
