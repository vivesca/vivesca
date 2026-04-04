FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Hong_Kong
ENV LANG=C.UTF-8

COPY gemmule/install.sh /tmp/install.sh
RUN chmod +x /tmp/install.sh && /tmp/install.sh

USER vivesca
WORKDIR /home/vivesca
COPY --chown=vivesca:vivesca gemmule/zshrc /home/vivesca/.zshrc
COPY --chown=vivesca:vivesca gemmule/tmux.conf /home/vivesca/.tmux.conf

LABEL org.opencontainers.image.title="gemmule"
LABEL org.opencontainers.image.description="Dormant capsule for vivesca soma/ganglion"
LABEL org.opencontainers.image.source="https://github.com/terryli-vt/vivesca"

CMD ["zsh"]
