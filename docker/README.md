[![made-with](https://img.shields.io/badge/Built%20with-grey)]()
[![made-with-Python](https://img.shields.io/badge/Python-blue)](https://www.python.org/)
[![made-with-FastAPI](https://img.shields.io/badge/FastAPI-blue)](https://fastapi.tiangolo.com/)
[![made-with-elastic](https://img.shields.io/badge/elastic-blue)](https://www.elastic.co/)
[![made-with-MinIO](https://img.shields.io/badge/MinIO-blue)](https://min.io/)
[![made-with-RabbitMQ](https://img.shields.io/badge/RabbitMQ-blue)](https://www.rabbitmq.com/)

The following is a quick guide to use docker-compose to build Galaxy along with an ElasticSearch cluster and Kibana with security enabled.
- Create a docker compose .env file to contain the following variables:
  > **COMPOSE_PROJECT_NAME**=galaxy 
  > **CERTS_DIR**=/usr/share/elasticsearch/config/certificates
  > **VERSION**=7.11.1 #*or another version*
  > **ELASTIC_PASSWORD**=xx #*will update this variable later*

- Use the instances.yml file to identify the Elastic and Kibana instances to create certificates for
- Use the create-certs.yml compose file to generate the certificates for instances identified above:
  > sudo docker-compose -f create-certs.yml run --rm create_certs
- To list the certificates created :
  > sudo ls -l $(sudo docker volume inspect docker_certs | jq -r '.[0].Mountpoint')
- To bring up the containers:
  > sudo docker-compose -f docker-compose.yml up -d
- Run the elasticsearch-setup-passwords tool to generate passwords for all built-in users.
  > sudo docker exec es01 /bin/bash -c "bin/elasticsearch-setup-passwords auto --batch --url https://es01:9200"
- Update the ELASTIC_PASSWORD in the .env file to the password generated for the kibana_system user.
- Use docker-compose to restart the cluster and Kibana:
  > sudo docker-compose stop \
  > sudo docker-compose -f docker-compose.yml up -d