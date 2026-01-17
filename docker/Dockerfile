FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04

# Run apt-get (dkpg) without interactive dialogue
ARG DEBIAN_FRONTEND=noninteractive

########################################
# SECTION 1: Essentials                #
########################################
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim git curl wget cmake unzip pkg-config \
    checkinstall build-essential ca-certificates \
    software-properties-common apt-utils bash-completion \
    # Setup locale language config \
    locales \
  && apt-get upgrade -y \
  && rm -rf /var/lib/apt/lists/* \
  # Setup locale language config \
  && locale-gen "en_US.UTF-8" \
  && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
  # Set timezone \
  && ln -fs /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8


#############################################
# SECTION 2: Install Python w/ uv           #
#############################################
# Default python with uv
RUN apt-get update && apt-get install -y \
    python3 \
  && rm -rf /var/lib/apt/lists/* \
  && curl -LsSf https://astral.sh/uv/install.sh | sh


##################################################
# SECTION 3: nvblox_torch testing dependencies   #
##################################################
RUN apt-get update && apt-get install -y \
    libx11-dev libgl-dev \
  && rm -rf /var/lib/apt/lists/*


########################################
# SECTION N: Additional config & MISC  #
########################################
# Non-interactive shell
ENV BASH_ENV="/root/.noninteractive_bashrc"
RUN echo ". \"\$HOME/.local/bin/env\"" >> "$BASH_ENV"

ENTRYPOINT []
CMD ["/bin/bash"]
