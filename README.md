# Final_Project

## Application Links
[![Codelabs](https://img.shields.io/badge/Codelabs-blue?style=for-the-badge)](https://codelabs-preview.appspot.com/?file_id=1fbWTNJO9v0mllZLa48zSFKu5GM6kTl0HLQQcBGkoPVE/edit#0)

[![Video](https://img.shields.io/badge/Video-CC6699?style=for-the-badge)](https://www.youtube.com/watch?v=_0TWwnpgJ0c)

[![Application Link](https://img.shields.io/badge/Application-green?style=for-the-badge)](http://34.122.119.16:8501/)

## Problem Statement

The challenge in contemporary online fashion retail lies in meeting the visual and style-centric expectations of consumers. This project addresses the gap between consumer preferences and current online store offerings by introducing a one-stop solution for small-scale platforms. Users can upload images or input text to specify clothing preferences, receiving personalized recommendations through advanced image recognition and natural language processing. Vendors benefit from intuitive catalog management tools. The technology stack includes orchestration, cloud computation, web application development, dockerization, embedding generation, database querying, and deployment, aiming for a seamless user experience. Limitations include a focus on small-scale platforms, recommendation accuracy tied to database quality, and the need for continuous updates.

## Architecture Diagram
![fashion_discovery_platform](https://github.com/BigDataIA-Fall2023-Team4/Final_Project/assets/113845871/77d882dc-9be0-48f5-81ae-e6ce9938dfbc)



## Technology Stack
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![GCP provider](https://img.shields.io/badge/GCP-orange?style=for-the-badge&logo=google-cloud&color=orange)](https://cloud.google.com/?hl=en)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/)
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=purple)](https://www.python.org/)
[![Apache Airflow](https://img.shields.io/badge/apacheairflow-2A667F?style=for-the-badge&logo=ApacheAirflow&logoColor=black)](https://airflow.apache.org/)
[![Pinecone](https://img.shields.io/badge/Pinecone-A100FF?style=for-the-badge)](https://www.pinecone.io/)
[![Langchain](https://img.shields.io/badge/Langchain-073B5A?style=for-the-badge)](https://www.langchain.com/)
[![OpenAI Clip](https://img.shields.io/badge/openai-6BA539?style=for-the-badge&logo=OpenAI&logoColor=black)](https://openai.com/)
[![Docker](https://img.shields.io/badge/docker-29F1FB?style=for-the-badge&logo=Docker&logoColor=black)](https://www.docker.com/)
[![Amazon S3](https://img.shields.io/badge/amazons3-535D6C?style=for-the-badge&logo=amazons3&logoColor=black)](https://aws.amazon.com/s3/)

## Project Structure:


## Running the Application
- The application contains two roles to authenticate, the first one being the application user or potential buyer and the second one as the vendor or application owner.
- New users can sign up then log in and old users can directly login with their registered credentials. The vendor role is pre-assigned a credential to use that for accessing the catalog.
- The user has access to search for the desired products either by uploading a similar image or by describing the product as a text to the chatbot
- The user can also see the last seen products which are recorded in a SQL database while the user browses the application
- The product search feature converts the user’s input into 512 dimension embeddings to query over the Pinecone vector database and displays back the top three similar products available in the product catalog
- The vendor can use this application to either add more products in batch by uploading a CSV file with product information and images or delete any products by feeding its product id
- The application also validates if the product information in CSV file is consistent with the product images uploaded by the user


## References:
- ChatGPT: https://chat.openai.com/
- LangChain: https://python.langchain.com/docs/get_started/introduction
- OpenAI CLIP: https://towardsdatascience.com/quick-fire-guide-to-multi-modal-ml-with-openais-clip-2dad7e398ac0 
- Fast API: https://fastapi.tiangolo.com/
- Airflow: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- Pinecone: https://www.pinecone.io/learn/vector-database/
- Docker: https://www.docker.com/#
- JWT Tokens: https://jwt.io/introduction
- ScraperAPI: https://www.scraperapi.com/blog/how-to-scrape-amazon-product-data/ 


## Team Contribution:

| Name            | Contribution % | Contributions |
|-----------------|----------------|---------------|
| Naman Gupta     |     33.3%      | Architecture Planning, OpenAI's CLIP Implementation, Database Querying, Data Scraping, ChatBot Development, Documentation            |
| Jagruti Agrawal |     33.3%      | Architecture Planning, LangChain Implementation, Catalog Management Implementation, VM Deployment and Dockerization, Documentation           |
| Divyesh Rajput  |     33.3%      | Architecture Planning, Airflow Pipeline Implementation, Application UI development, API Endpoints Building            |
