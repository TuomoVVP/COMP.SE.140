FROM node:14-alpine

RUN apk add --no-cache bash

WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 3000
CMD [ "node", "index.js" ]
