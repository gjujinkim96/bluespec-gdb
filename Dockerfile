# syntax=docker/dockerfile:1

FROM ubuntu:20.04
WORKDIR /build

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    autoconf \
    automake \
    autotools-dev \
    curl \
    python3 \
    python3-pip \
    libmpc-dev \
    libmpfr-dev \
    libgmp-dev \
    gawk \
    build-essential \
    bison \
    flex \
    texinfo \
    gperf \
    libtool \
    patchutils \
    bc \
    zlib1g-dev \
    libexpat-dev \
    ninja-build \
    git \
    cmake \
    libglib2.0-dev \
    libgmp10 \
    tcl-dev \
    pkg-config \
    iverilog \
    libelf-dev \
    wget \
    lsb-release \
    software-properties-common \
    gnupg2 \
    apt-transport-https \
    gcc \
    vim \
    libncurses5-dev libncursesw5-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN bash -c "curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh"
ENV PATH="/root/.ghcup/bin:$PATH"
RUN ghcup install ghc --set recommended
RUN cabal update && cabal v1-install regex-compat syb old-time split

RUN git clone --recursive https://github.com/B-Lang-org/bsc
WORKDIR /build/bsc
RUN make install-src && mv inst /opt/bsc

WORKDIR /build
RUN git clone https://github.com/riscv/riscv-gnu-toolchain
WORKDIR /build/riscv-gnu-toolchain
RUN git submodule update --init --recursive

ENV PATH="/opt/riscv/bin:$PATH"
RUN ./configure --prefix=/opt/riscv
RUN make

ENV PATH="/opt/bsc/bin:$PATH"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.9 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build/CA_Summer_Project
COPY CA_Summer_Project .

WORKDIR /build/CA_Summer_Project/lab4/src/
RUN ./risc-v -d -p

WORKDIR /build/CA_Summer_Project/lab4/gdbstub
RUN make XLEN=32 exe_gdbstub_tcp_tcp_RV32

WORKDIR /build/CA_Summer_Project/lab4/gdbstub/Run
COPY xmls/*  .

WORKDIR /build/CA_Summer_Project/lab4/gdbstub/Run/types_helper
COPY help_scripts/types_helper/*.py .

WORKDIR /home
COPY run_scripts .

ENTRYPOINT [ "tail", "-f", "/dev/null"]
