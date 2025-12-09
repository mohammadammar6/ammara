FROM jenkins/jenkins:lts

# Install docker CLI inside Jenkins container
USER root
RUN apt-get update && apt-get install -y docker.io \
    && rm -rf /var/lib/apt/lists/*

# Back to jenkins user
USER jenkins
