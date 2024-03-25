FROM node:lts-alpine
COPY package.json /code/
WORKDIR /code/
RUN npm install
ENV PATH /code/node_modules/.bin:$PATH
COPY . /code/app/
WORKDIR /code/app
EXPOSE 5173
CMD npm run build
