# Self-hosted Kodiak: ONNX Runtime + Express on CPU. Build from the repository root:
#
#   docker build -f server/Dockerfile -t kodiak-server .
#   docker run -p 8080:8080 -v /path/to/model-folder:/model:ro kodiak-server
#
# The model folder holds model.onnx, tokenizer.json and calibration.json (see server/README.md).
FROM node:22-slim
WORKDIR /app
COPY schema/kodiak-request.schema.json schema/
COPY server/package.json server/package-lock.json server/
RUN cd server && npm ci --omit=dev && npm cache clean --force
COPY server/src server/src
ENV KODIAK_MODEL=/model PORT=8080 NODE_ENV=production
EXPOSE 8080
USER node
CMD ["node", "server/src/server.js"]
