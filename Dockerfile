FROM node:20-alpine
WORKDIR /app

RUN apk add --no-cache build-base cairo-dev pango-dev jpeg-dev giflib-dev pixman-dev pkgconfig python3

COPY package*.json ./
RUN npm ci --omit=dev
COPY . .
CMD ["node", "index.js"]
