# The base image for circleci
FROM fedora:32 as upgrade

WORKDIR /simengine_setup
# Upgrade Fedora
RUN dnf upgrade -y

# Install build dependencies
FROM upgrade as build_dependencies
RUN dnf install -y 'dnf-command(builddep)'
RUN dnf install -y rpmdevtools
RUN dnf install -y fedora-packager
RUN dnf install -y wget

# Add neo4j repo
FROM build_dependencies as add_neo4j_repo
COPY ./setup/install-simengine/add-neo4j-repo .
RUN ./add-neo4j-repo

# Install spec files required packages
FROM add_neo4j_repo as specs_requires
COPY rpm/specfiles/*.spec specfiles/
RUN dnf builddep specfiles/*.spec -y
RUN requires_list=($(rpm --requires --specfile specfiles/*.spec | \
    sed --regexp-extended 's/[[:space:]]+[<>=]+[[:space:]]+/-/')) \
    && for requires_item in "${requires_list[@]}"; \
    do echo "DEPENDENCY=[$requires_item]"; sudo dnf --assumeyes install "$requires_item"; done

FROM specs_requires as entry_point
COPY docker-entrypoint.sh .

ENTRYPOINT ["/simengine_setup/docker-entrypoint.sh"]
