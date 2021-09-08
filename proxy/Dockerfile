FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="rentyug-backend.live"

COPY ./nginx/certs/certificate.crt /etc/nginx/certs/certificate.crt
COPY ./nginx/certs/private.key /etc/nginx/certs/private.key
COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000
ENV REQUESTS_CA_BUNDLE=/etc/nginx/certs/

USER root

RUN mkdir -p /vol/static && \
    chmod 755 /vol/static && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

VOLUME /vol/static

USER nginx

CMD ["/run.sh"]