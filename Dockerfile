
FROM squidfunk/mkdocs-material AS builder


WORKDIR /docs

# Kopioi koko projekti (mkdocs.yml, docs/, img/, jne.)
COPY . .

# staattinen sivusto kansioon /site
RUN mkdocs build --clean --site-dir /site


# 2. Nginx vaihe
FROM nginx:alpine

# Korvataan Nginxin oletuskonffi
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Kopioidaan rakennettu sivusto Nginxin juureen
COPY --from=builder /site /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
