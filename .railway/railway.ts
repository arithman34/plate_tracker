import { defineRailway, github, postgres, preserve, project, redis, service, volume } from "railway/iac";

export default defineRailway(() => {
  const plate_tracker = github("arithman34/plate_tracker", { checkSuites: false });

  const Postgres = postgres("Postgres", { region: "sfo" });
  Postgres.networking = { privateNetworkEndpoint: "postgres" };
  const Redis = redis("Redis", { region: "sfo" });
  Redis.deploy = { startCommand: "/bin/sh -c \"rm -rf $RAILWAY_VOLUME_MOUNT_PATH/lost+found/ && exec docker-entrypoint.sh redis-server --requirepass $REDIS_PASSWORD --save 60 1 --dir $RAILWAY_VOLUME_MOUNT_PATH\"" };
  Redis.networking = { privateNetworkEndpoint: "redis" };
  const redisVolume = volume("redis-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "sfo", sizeMB: 5000 });
  const postgresVolume = volume("postgres-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "sfo", sizeMB: 5000 });
  const sharedVars = {
    DATABASE_URL: Postgres.env.DATABASE_URL,
    REDIS_URL: Redis.env.REDIS_URL,
    POSTGRES_USER: Postgres.env.POSTGRES_USER,
    POSTGRES_PASSWORD: Postgres.env.POSTGRES_PASSWORD,
    POSTGRES_DB: Postgres.env.POSTGRES_DB,
    AWS_ACCESS_KEY_ID: preserve(),
    AWS_SECRET_ACCESS_KEY: preserve(),
    AWS_REGION: preserve(),
    S3_BUCKET: preserve(),
  };

  const worker = service("worker", {
    source: plate_tracker,
    replicas: { "sfo": 1 },
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile.worker" },
    deploy: { restartPolicyType: "ON_FAILURE", restartPolicyMaxRetries: 3 },
    variables: sharedVars,
  });
  const api = service("api", {
    source: plate_tracker,
    replicas: { "sfo": 1 },
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile.api" },
    deploy: { healthcheckPath: "/health", healthcheckTimeout: 100, restartPolicyType: "ON_FAILURE", restartPolicyMaxRetries: 3 },
    variables: sharedVars,
    networking: { serviceDomains: { "default": {} } },
  });

  return project("plate-tracker", {
    resources: [Postgres, worker, Redis, api, redisVolume, postgresVolume],
  });
});
