# Isolated local staging

`compose.staging.yml` only accepts prebuilt image references. It never builds and no GitHub branch triggers it. Every run must set a unique `APISTRA_COMPOSE_PROJECT`, loopback-only ports, and the three candidate image tags. The named internal network and state volume are scoped by that project identifier.

All containers run as UID/GID 10001, read-only, without Linux capabilities, with `no-new-privileges`, bounded PIDs, CPU and memory. Runtime configuration is external. CAP-00 requires no application secret; later capabilities must use protected secret references rather than Compose literals.
