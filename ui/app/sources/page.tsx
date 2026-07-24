"use client";

import {
  FormEvent,
  ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react";

import AppShell from "@/components/layout/AppShell";
import ConnectorLifecycle from "@/components/connectors/ConnectorLifecycle";
import PageHeader from "@/components/ui/PageHeader";
import Panel from "@/components/ui/Panel";
import Badge from "@/components/ui/Badge";
import MetricCard from "@/components/ui/MetricCard";
import { apiFetch } from "@/lib/api";


type Connector = {
  connector_id: number;
  project_id: number;
  connector_code: string;
  connector_type_name: string;
  connector_category: string;
  connector_name: string;
  connector_status: string;
  domain_code: string | null;
  domain_name: string | null;

  connection_config:
    Record<string, unknown> | null;

  secret_reference: string | null;

  datasets: number;
  columns: number;

  last_tested_at: string | null;
  last_discovered_at: string | null;

  latest_run_status: string | null;
  latest_run_at: string | null;

  created_at: string | null;
};


type ConnectorType = {
  connector_type_id: number;
  connector_code: string;
  connector_name: string;
  connector_category: string;
  description: string | null;
};


type Domain = {
  domain_code: string;
  domain_name: string;
};


type Dataset = {
  dataset_id: number;
  name: string;
  object_type: string;
  location: string | null;
  row_count: number | null;
  column_count: number | null;
  domain_code: string | null;
  created_at: string | null;
  first_discovered_at?: string | null;
  last_discovered_at?: string | null;
};


type DiscoveryRun = {
  connector_discovery_run_id: number;
  run_status: string;
  run_message: string | null;
  datasets_discovered: number;
  columns_discovered: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};


type ConnectorForm = {
  connector_id?: number;

  connector_code: string;
  connector_name: string;
  business_domain: string;

  account: string;
  user: string;
  password: string;
  warehouse: string;
  role: string;

  database_name: string;
  schema_name: string;
  table_name: string;
  table_limit: string;
};


const EMPTY_FORM: ConnectorForm = {
  connector_code: "SNOWFLAKE",
  connector_name: "",
  business_domain: "",

  account: "",
  user: "",
  password: "",
  warehouse: "",
  role: "",

  database_name: "",
  schema_name: "",
  table_name: "",
  table_limit: "20",
};


export default function SourcesPage() {
  const [
    connectors,
    setConnectors,
  ] = useState<Connector[]>([]);

  const [
    connectorTypes,
    setConnectorTypes,
  ] = useState<ConnectorType[]>([]);

  const [
    domains,
    setDomains,
  ] = useState<Domain[]>([]);

  const [
    selected,
    setSelected,
  ] = useState<Connector | null>(null);

  const [
    datasets,
    setDatasets,
  ] = useState<Dataset[]>([]);

  const [
    runs,
    setRuns,
  ] = useState<DiscoveryRun[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [
    action,
    setAction,
  ] = useState<string | null>(null);

  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");

  const [
    showForm,
    setShowForm,
  ] = useState(false);

  const [
    form,
    setForm,
  ] = useState<ConnectorForm>(
    EMPTY_FORM
  );

  const [
    file,
    setFile,
  ] = useState<File | null>(null);


  useEffect(() => {
    void initialise();
  }, []);


  async function initialise() {
    setLoading(true);
    setError("");

    try {
      const [
        sourceData,
        typeData,
        domainData,
      ] = await Promise.all([
        apiFetch<Connector[]>(
          "/sources"
        ),

        apiFetch<ConnectorType[]>(
          "/sources/types"
        ),

        apiFetch<Domain[]>(
          "/domains"
        ),
      ]);

      const connectorList =
        Array.isArray(sourceData)
          ? sourceData
          : [];

      setConnectors(connectorList);

      setConnectorTypes(
        Array.isArray(typeData)
          ? typeData
          : []
      );

      setDomains(
        Array.isArray(domainData)
          ? domainData
          : []
      );

      if (connectorList.length > 0) {
        await selectConnector(
          connectorList[0],
          false
        );
      }
    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to load Enterprise Connectors."
        )
      );
    } finally {
      setLoading(false);
    }
  }


  async function refreshConnectors(
    preferredId?: number
  ) {
    const sourceData =
      await apiFetch<Connector[]>(
        "/sources"
      );

    const connectorList =
      Array.isArray(sourceData)
        ? sourceData
        : [];

    setConnectors(connectorList);

    const target =
      connectorList.find(
        (item) =>
          item.connector_id
          === preferredId
      )
      || connectorList[0]
      || null;

    if (target) {
      await selectConnector(
        target,
        false
      );
    } else {
      setSelected(null);
      setDatasets([]);
      setRuns([]);
    }
  }


  async function selectConnector(
    connector: Connector,
    clearMessages = true
  ) {
    setSelected(connector);

    if (clearMessages) {
      setError("");
      setSuccess("");
    }

    setDetailLoading(true);

    try {
      const [
        datasetData,
        runData,
      ] = await Promise.all([
        apiFetch<Dataset[]>(
          `/sources/${connector.connector_id}/datasets`
        ),

        apiFetch<DiscoveryRun[]>(
          `/sources/${connector.connector_id}/runs`
        ),
      ]);

      setDatasets(
        Array.isArray(datasetData)
          ? datasetData
          : []
      );

      setRuns(
        Array.isArray(runData)
          ? runData
          : []
      );
    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to load connector details."
        )
      );

      setDatasets([]);
      setRuns([]);
    } finally {
      setDetailLoading(false);
    }
  }


  function openCreate() {
    setForm({
      ...EMPTY_FORM,
    });

    setFile(null);
    setShowForm(true);
    setError("");
    setSuccess("");
  }


  function openEdit() {
    if (!selected) {
      return;
    }

    const config =
      selected.connection_config
      || {};

    setForm({
      connector_id:
        selected.connector_id,

      connector_code:
        selected.connector_code,

      connector_name:
        selected.connector_name,

      business_domain:
        selected.domain_code || "",

      account:
        String(
          config.account || ""
        ),

      user:
        String(
          config.user || ""
        ),

      password:
        String(
          config.password || ""
        ),

      warehouse:
        String(
          config.warehouse || ""
        ),

      role:
        String(
          config.role || ""
        ),

      database_name:
        String(
          config.database_name || ""
        ),

      schema_name:
        String(
          config.schema_name || ""
        ),

      table_name:
        String(
          config.table_name || ""
        ),

      table_limit:
        String(
          config.table_limit || "20"
        ),
    });

    setFile(null);
    setShowForm(true);
  }


  async function saveConnector(
    event: FormEvent
  ) {
    event.preventDefault();

    setAction("save");
    setError("");
    setSuccess("");

    const connectionConfig =
      form.connector_code
      === "SNOWFLAKE"
        ? {
            account:
              form.account.trim(),

            user:
              form.user.trim(),

            password:
              form.password,

            warehouse:
              form.warehouse.trim(),

            role:
              form.role.trim()
              || null,

            database_name:
              form.database_name.trim(),

            schema_name:
              form.schema_name.trim(),

            table_name:
              form.table_name.trim()
              || null,

            table_limit:
              Number(
                form.table_limit || 20
              ),

            discovery_scope:
              form.table_name.trim()
                ? "TABLE"
                : "SCHEMA",
          }
        : {};


    try {
      let connectorId =
        form.connector_id;

      if (connectorId) {
        await apiFetch(
          `/sources/${connectorId}`,
          {
            method: "PUT",

            body: JSON.stringify({
              connector_name:
                form.connector_name.trim(),

              business_domain:
                form.business_domain
                || null,

              connection_config:
                connectionConfig,
            }),
          }
        );
      } else {
        const created =
          await apiFetch<{
            connector_id: number;
          }>(
            "/sources",
            {
              method: "POST",

              body: JSON.stringify({
                project_id: 1,

                connector_code:
                  form.connector_code,

                connector_name:
                  form.connector_name.trim(),

                business_domain:
                  form.business_domain
                  || null,

                connection_config:
                  connectionConfig,
              }),
            }
          );

        connectorId =
          created.connector_id;
      }

      if (
        file
        && connectorId
      ) {
        const uploadPayload =
          new FormData();

        uploadPayload.append(
          "file",
          file
        );

        await apiFetch(
          `/sources/${connectorId}/upload`,
          {
            method: "POST",
            body: uploadPayload,
          }
        );
      }

      setShowForm(false);

      setSuccess(
        form.connector_id
          ? "Connector updated."
          : "Connector created."
      );

      await refreshConnectors(
        connectorId
      );
    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to save connector."
        )
      );
    } finally {
      setAction(null);
    }
  }


  async function testConnection() {
    if (!selected) {
      return;
    }

    await apiFetch(
      `/sources/${selected.connector_id}/test`,
      {
        method: "POST",
      }
    );

    await refreshConnectors(
      selected.connector_id
    );
  }


  async function discoverAssets() {
    if (!selected) {
      return;
    }

    await apiFetch(
      `/sources/${selected.connector_id}/discover`,
      {
        method: "POST",

        body: JSON.stringify({
          run_profiling: true,
        }),
      }
    );

    await refreshConnectors(
      selected.connector_id
    );
  }


  async function removeConnector() {
    if (!selected) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete connector "${selected.connector_name}"?`
      );

    if (!confirmed) {
      return;
    }

    setAction("delete");
    setError("");
    setSuccess("");

    try {
      await apiFetch(
        `/sources/${selected.connector_id}`,
        {
          method: "DELETE",
        }
      );

      setSuccess(
        "Connector deleted."
      );

      await refreshConnectors();
    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to delete connector."
        )
      );
    } finally {
      setAction(null);
    }
  }


  const totals = useMemo(
    () => ({
      datasets:
        connectors.reduce(
          (sum, item) =>
            sum
            + Number(
              item.datasets || 0
            ),
          0
        ),

      columns:
        connectors.reduce(
          (sum, item) =>
            sum
            + Number(
              item.columns || 0
            ),
          0
        ),

      connected:
        connectors.filter(
          (item) =>
            item.connector_status
            === "CONNECTED"
        ).length,
    }),
    [connectors]
  );


  return (
    <AppShell>
      <section className="sources-page">
        <div className="flex items-start justify-between gap-6">
          <PageHeader
            label="Enterprise Connectors"
            title="Connect and understand your enterprise"
            description="Configure systems and files, discover active assets, build business understanding and prepare Enterprise Intelligence."
          />

          <button
            type="button"
            onClick={openCreate}
            className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-500"
          >
            Add Connector
          </button>
        </div>

        <div className="mb-8 grid grid-cols-1 gap-5 xl:grid-cols-4">
          <MetricCard
            label="Connectors"
            value={connectors.length}
          />

          <MetricCard
            label="Connected"
            value={totals.connected}
          />

          <MetricCard
            label="Active Datasets"
            value={totals.datasets}
          />

          <MetricCard
            label="Active Columns"
            value={totals.columns}
          />
        </div>

        {error && (
          <Notice tone="error">
            {error}
          </Notice>
        )}

        {success && (
          <Notice tone="success">
            {success}
          </Notice>
        )}

        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-10 text-slate-500">
            Loading Enterprise Connectors...
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <Panel
              title="Connector Registry"
              subtitle="Configured enterprise systems and files."
            >
              <div className="space-y-3">
                {connectors.map(
                  (connector) => (
                    <button
                      type="button"
                      key={
                        connector.connector_id
                      }
                      onClick={() =>
                        void selectConnector(
                          connector
                        )
                      }
                      className={[
                        "w-full rounded-2xl border p-4 text-left transition",

                        selected?.connector_id
                        === connector.connector_id
                          ? "border-indigo-400 bg-indigo-50"
                          : "border-slate-200 bg-white hover:border-indigo-300",
                      ].join(" ")}
                    >
                      <div className="flex justify-between gap-3">
                        <div>
                          <p className="font-bold text-slate-950">
                            {
                              connector.connector_name
                            }
                          </p>

                          <p className="mt-1 text-sm text-slate-500">
                            {
                              connector.connector_type_name
                            }
                          </p>
                        </div>

                        <Badge
                          tone={statusTone(
                            connector.connector_status
                          )}
                        >
                          {
                            connector.connector_status
                          }
                        </Badge>
                      </div>

                      <div className="mt-4 flex justify-between text-sm text-slate-500">
                        <span>
                          {
                            connector.datasets
                            || 0
                          }{" "}
                          active datasets
                        </span>

                        <span>
                          {
                            connector.domain_code
                            || "No domain"
                          }
                        </span>
                      </div>
                    </button>
                  )
                )}

                {connectors.length === 0 && (
                  <Empty text="No connectors are configured yet." />
                )}
              </div>
            </Panel>

            <div className="space-y-6 xl:col-span-2">
              <Panel
                title={
                  selected?.connector_name
                  || "Connector Details"
                }
                subtitle="Connection details and current asset scope."
              >
                {selected ? (
                  <>
                    <div className="rounded-3xl bg-gradient-to-br from-indigo-50 to-fuchsia-50 p-6">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">
                            {
                              selected.connector_type_name
                            }
                          </p>

                          <h2 className="mt-2 text-3xl font-bold text-slate-950">
                            {
                              selected.connector_name
                            }
                          </h2>

                          <p className="mt-3 text-slate-600">
                            {
                              selected.domain_name
                              || "No business workspace assigned"
                            }
                          </p>
                        </div>

                        <Badge
                          tone={statusTone(
                            selected.connector_status
                          )}
                        >
                          {
                            selected.connector_status
                          }
                        </Badge>
                      </div>
                    </div>

                    <div className="my-6 grid grid-cols-1 gap-4 md:grid-cols-4">
                      <SmallMetric
                        label="Active Datasets"
                        value={
                          selected.datasets
                          || 0
                        }
                      />

                      <SmallMetric
                        label="Active Columns"
                        value={
                          selected.columns
                          || 0
                        }
                      />

                      <SmallMetric
                        label="Last Test"
                        value={formatDate(
                          selected.last_tested_at
                        )}
                      />

                      <SmallMetric
                        label="Last Discovery"
                        value={formatDate(
                          selected.last_discovered_at
                        )}
                      />
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <ActionButton
                        disabled={!!action}
                        onClick={openEdit}
                      >
                        Configure
                      </ActionButton>

                      <button
                        type="button"
                        disabled={!!action}
                        onClick={() =>
                          void removeConnector()
                        }
                        className="rounded-xl border border-red-200 px-4 py-2.5 font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </>
                ) : (
                  <Empty text="Select or create an Enterprise Connector." />
                )}
              </Panel>

              {selected && (
                <Panel
                  title="Connector Lifecycle"
                  subtitle="Progress from connectivity to Enterprise Intelligence."
                >
                  <ConnectorLifecycle
                    connectorId={
                      selected.connector_id
                    }
                    connectorStatus={
                      selected.connector_status
                    }
                    onTestConnection={
                      testConnection
                    }
                    onDiscoverAssets={
                      discoverAssets
                    }
                    onLifecycleChanged={
                      async () => {
                        await refreshConnectors(
                          selected.connector_id
                        );
                      }
                    }
                  />
                </Panel>
              )}

              {selected && (
                <Panel
                  title="Active Datasets"
                  subtitle="Assets included in the connector's latest successful discovery."
                >
                  {detailLoading ? (
                    <p className="text-slate-500">
                      Loading connector assets...
                    </p>
                  ) : datasets.length > 0 ? (
                    <div className="space-y-3">
                      {datasets.map(
                        (dataset) => (
                          <div
                            key={
                              dataset.dataset_id
                            }
                            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                          >
                            <div className="flex justify-between gap-4">
                              <div>
                                <p className="font-semibold text-slate-950">
                                  {
                                    dataset.name
                                  }
                                </p>

                                <p className="mt-1 text-sm text-slate-500">
                                  {
                                    dataset.object_type
                                  }{" "}
                                  ·{" "}
                                  {
                                    dataset.domain_code
                                    || "UNKNOWN"
                                  }
                                </p>

                                {dataset.location && (
                                  <p className="mt-1 break-all text-xs text-slate-400">
                                    {
                                      dataset.location
                                    }
                                  </p>
                                )}
                              </div>

                              <Badge tone="neutral">
                                {
                                  dataset.column_count
                                  || 0
                                }{" "}
                                columns
                              </Badge>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  ) : (
                    <Empty text="No active datasets have been discovered for this connector." />
                  )}
                </Panel>
              )}

              {selected && (
                <Panel
                  title="Discovery History"
                  subtitle="Historical connector executions remain available even when the active scope changes."
                >
                  {runs.length > 0 ? (
                    <div className="space-y-3">
                      {runs
                        .slice(0, 5)
                        .map((run) => (
                          <div
                            key={
                              run.connector_discovery_run_id
                            }
                            className="flex items-center justify-between rounded-2xl border border-slate-200 p-4"
                          >
                            <div>
                              <p className="font-semibold text-slate-950">
                                Asset Discovery #
                                {
                                  run.connector_discovery_run_id
                                }
                              </p>

                              <p className="mt-1 text-sm text-slate-500">
                                {
                                  run.run_message
                                  || "Connector execution"
                                }{" "}
                                ·{" "}
                                {formatDateTime(
                                  run.created_at
                                )}
                              </p>
                            </div>

                            <div className="text-right">
                              <Badge
                                tone={statusTone(
                                  run.run_status
                                )}
                              >
                                {
                                  run.run_status
                                }
                              </Badge>

                              <p className="mt-2 text-xs text-slate-400">
                                {
                                  run.datasets_discovered
                                  || 0
                                }{" "}
                                datasets ·{" "}
                                {
                                  run.columns_discovered
                                  || 0
                                }{" "}
                                columns
                              </p>
                            </div>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <Empty text="No discovery executions have been recorded." />
                  )}
                </Panel>
              )}
            </div>
          </div>
        )}
      </section>

      {showForm && (
        <ConnectorModal
          form={form}
          setForm={setForm}
          connectorTypes={connectorTypes}
          domains={domains}
          file={file}
          setFile={setFile}
          saving={action === "save"}
          onClose={() =>
            setShowForm(false)
          }
          onSubmit={saveConnector}
        />
      )}
    </AppShell>
  );
}


function ConnectorModal({
  form,
  setForm,
  connectorTypes,
  domains,
  file,
  setFile,
  saving,
  onClose,
  onSubmit,
}: {
  form: ConnectorForm;

  setForm:
    (value: ConnectorForm) => void;

  connectorTypes:
    ConnectorType[];

  domains:
    Domain[];

  file:
    File | null;

  setFile:
    (file: File | null) => void;

  saving:
    boolean;

  onClose:
    () => void;

  onSubmit:
    (event: FormEvent) => void;
}) {
  const isFile = [
    "CSV",
    "JSON",
    "PDF",
  ].includes(
    form.connector_code
  );

  function set(
    field: keyof ConnectorForm,
    value: string
  ) {
    setForm({
      ...form,
      [field]: value,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-6">
      <form
        onSubmit={onSubmit}
        className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-8 shadow-2xl"
      >
        <div className="mb-6 flex items-start justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">
              Enterprise Connector
            </p>

            <h2 className="mt-2 text-3xl font-bold text-slate-950">
              {form.connector_id
                ? "Configure connector"
                : "Add connector"}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-500 hover:text-slate-950"
          >
            Close
          </button>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Field label="Connector type">
            <select
              disabled={
                !!form.connector_id
              }
              value={
                form.connector_code
              }
              onChange={(event) =>
                set(
                  "connector_code",
                  event.target.value
                )
              }
              className="input"
            >
              {connectorTypes.map(
                (type) => (
                  <option
                    key={
                      type.connector_code
                    }
                    value={
                      type.connector_code
                    }
                  >
                    {
                      type.connector_name
                    }
                  </option>
                )
              )}
            </select>
          </Field>

          <Field label="Connector name">
            <input
              required
              value={
                form.connector_name
              }
              onChange={(event) =>
                set(
                  "connector_name",
                  event.target.value
                )
              }
              className="input"
            />
          </Field>

          <Field label="Business workspace">
            <select
              value={
                form.business_domain
              }
              onChange={(event) =>
                set(
                  "business_domain",
                  event.target.value
                )
              }
              className="input"
            >
              <option value="">
                No workspace
              </option>

              {domains.map(
                (domain) => (
                  <option
                    key={
                      domain.domain_code
                    }
                    value={
                      domain.domain_code
                    }
                  >
                    {
                      domain.domain_name
                    }
                  </option>
                )
              )}
            </select>
          </Field>
        </div>

        {form.connector_code
          === "SNOWFLAKE" && (
          <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2">
            <Field label="Account">
              <input
                required
                value={form.account}
                onChange={(event) =>
                  set(
                    "account",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="User">
              <input
                required
                value={form.user}
                onChange={(event) =>
                  set(
                    "user",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="Password">
              <input
                required
                type="password"
                value={
                  form.password
                }
                onChange={(event) =>
                  set(
                    "password",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="Warehouse">
              <input
                required
                value={
                  form.warehouse
                }
                onChange={(event) =>
                  set(
                    "warehouse",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="Role">
              <input
                value={form.role}
                onChange={(event) =>
                  set(
                    "role",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="Database">
              <input
                required
                value={
                  form.database_name
                }
                onChange={(event) =>
                  set(
                    "database_name",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="Schema">
              <input
                required
                value={
                  form.schema_name
                }
                onChange={(event) =>
                  set(
                    "schema_name",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>

            <Field label="Optional table">
              <input
                value={
                  form.table_name
                }
                onChange={(event) =>
                  set(
                    "table_name",
                    event.target.value
                  )
                }
                className="input"
                placeholder="Leave empty to discover the schema"
              />
            </Field>

            <Field label="Schema table limit">
              <input
                min="1"
                max="500"
                type="number"
                disabled={
                  Boolean(
                    form.table_name.trim()
                  )
                }
                value={
                  form.table_limit
                }
                onChange={(event) =>
                  set(
                    "table_limit",
                    event.target.value
                  )
                }
                className="input"
              />
            </Field>
          </div>
        )}

        {isFile && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6">
            <label className="block text-sm font-semibold text-slate-700">
              Upload{" "}
              {form.connector_code}{" "}
              file
            </label>

            <input
              required={
                !form.connector_id
              }
              type="file"
              accept={fileAccept(
                form.connector_code
              )}
              onChange={(event) =>
                setFile(
                  event.target.files?.[0]
                  || null
                )
              }
              className="mt-3 block w-full text-sm text-slate-600"
            />

            {file && (
              <p className="mt-2 text-sm text-indigo-600">
                {file.name}
              </p>
            )}
          </div>
        )}

        {form.connector_code
          === "POSTGRESQL" && (
          <Notice tone="info">
            PostgreSQL can be registered, but
            Test Connection and Asset Discovery
            will be enabled after its connector
            engine is implemented.
          </Notice>
        )}

        <div className="mt-8 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-5 py-3 font-semibold text-slate-700"
          >
            Cancel
          </button>

          <button
            disabled={saving}
            type="submit"
            className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white disabled:opacity-50"
          >
            {saving
              ? "Saving..."
              : "Save Connector"}
          </button>
        </div>
      </form>
    </div>
  );
}


function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-slate-700">
        {label}
      </span>

      {children}
    </label>
  );
}


function SmallMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-lg font-bold text-slate-950">
        {value}
      </p>
    </div>
  );
}


function Empty({
  text,
}: {
  text: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
      {text}
    </div>
  );
}


function ActionButton({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
    >
      {children}
    </button>
  );
}


function Notice({
  children,
  tone,
}: {
  children: ReactNode;
  tone:
    | "error"
    | "success"
    | "info";
}) {
  const classes =
    tone === "error"
      ? "border-red-200 bg-red-50 text-red-700"
      : tone === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-indigo-200 bg-indigo-50 text-indigo-700";

  return (
    <div
      className={`mb-6 rounded-2xl border p-4 ${classes}`}
    >
      {children}
    </div>
  );
}


function statusTone(
  status: string
):
  | "primary"
  | "success"
  | "neutral"
  | "warning"
  | "danger" {
  if (
    [
      "CONNECTED",
      "COMPLETED",
    ].includes(status)
  ) {
    return "success";
  }

  if (
    [
      "DISCOVERING",
      "RUNNING",
      "PENDING",
    ].includes(status)
  ) {
    return "primary";
  }

  if (
    [
      "ERROR",
      "FAILED",
    ].includes(status)
  ) {
    return "danger";
  }

  if (status === "CONFIGURED") {
    return "warning";
  }

  return "neutral";
}


function formatDate(
  value: string | null
): string {
  return value
    ? new Date(
        value
      ).toLocaleDateString()
    : "Not yet";
}


function formatDateTime(
  value: string | null
): string {
  return value
    ? new Date(
        value
      ).toLocaleString()
    : "N/A";
}


function fileAccept(
  code: string
): string {
  if (code === "CSV") {
    return ".csv";
  }

  if (code === "JSON") {
    return ".json";
  }

  if (code === "PDF") {
    return ".pdf";
  }

  return "";
}


function getMessage(
  error: unknown,
  fallback: string
): string {
  return error instanceof Error
    ? error.message
    : fallback;
}