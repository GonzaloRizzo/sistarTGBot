from ghcr.io/puppeteer/puppeteer:19.9.1

WORKDIR app
COPY package.json package-lock.json .


USER root
RUN chown -R pptruser:pptruser package.json package-lock.json
USER pptruser
RUN npm install


COPY . .
EXPOSE 3000

CMD node main.mjs

