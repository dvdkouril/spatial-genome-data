FROM node:24-slim
WORKDIR /app
COPY hello.js .
# Run as the non-root "node" user (uid 1000), as CERIT requires.
USER node
CMD ["node", "hello.js"]
