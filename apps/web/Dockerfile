ARG NODE_BASE=node:24.19.0-bookworm-slim@sha256:a9f5f7c91a432850b2a8a7797adf5eadb6c733ceed61167806cee7ea7fbc29df
FROM ${NODE_BASE} AS build
WORKDIR /build
RUN corepack enable && corepack prepare pnpm@12.8.1 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web apps/web
ARG APISTRA_VERSION=0.0.0-dev
ARG APISTRA_COMMIT=unknown
ENV APISTRA_VERSION=${APISTRA_VERSION} APISTRA_COMMIT=${APISTRA_COMMIT} APISTRA_ENVIRONMENT=staging NEXT_PUBLIC_APISTRA_VERSION=${APISTRA_VERSION} NEXT_PUBLIC_APISTRA_COMMIT=${APISTRA_COMMIT} NEXT_PUBLIC_APISTRA_ENVIRONMENT=staging
RUN pnpm --filter @apistra/web build

FROM ${NODE_BASE} AS runtime
ARG APISTRA_VERSION=0.0.0-dev
ARG APISTRA_COMMIT=unknown
LABEL org.opencontainers.image.title="Apistra web" org.opencontainers.image.version="${APISTRA_VERSION}" org.opencontainers.image.revision="${APISTRA_COMMIT}" org.opencontainers.image.source="https://github.com/Apistra/Apistra"
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0 NEXT_TELEMETRY_DISABLED=1 APISTRA_VERSION=${APISTRA_VERSION} APISTRA_COMMIT=${APISTRA_COMMIT}
WORKDIR /app
COPY --from=build --chown=10001:10001 /build/apps/web/.next/standalone ./
COPY --from=build --chown=10001:10001 /build/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=10001:10001 /build/apps/web/public ./apps/web/public
USER 10001:10001
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
