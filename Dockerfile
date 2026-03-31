FROM nginx:latest

# remove página padrão do nginx
RUN rm -rf /usr/share/nginx/html/*

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]