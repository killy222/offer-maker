# Railway MinIO service — use this folder as the service root (Root Directory: deploy/minio).
# The official image ENTRYPOINT is "minio"; CMD must be the "server" subcommand only.
FROM minio/minio:latest

VOLUME ["/data"]

EXPOSE 9000 9001

CMD ["server", "/data", "--console-address", ":9001"]
