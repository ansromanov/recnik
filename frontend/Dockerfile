FROM node:18-alpine AS build

# Accept build argument for ResponsiveVoice API key
ARG REACT_APP_RESPONSIVEVOICE_API_KEY
ENV REACT_APP_RESPONSIVEVOICE_API_KEY=$REACT_APP_RESPONSIVEVOICE_API_KEY

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
