
# Food Knowledge Graph API

The Food Knowledge Graph API provides access to a database of ingredients and recipes. It allows users to retrieve information about recipes based on common ingredients.
---

## Features

- Retrieve information about ingredients
- Explore graph-based recipes based on ingredients
- Find recipes that match your given ingredients
- Filter ingredients by category and search for recipes by ingredients

## Setup

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd FoodKG
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables:**

    Create a `.env` file in the project root directory and add the following environment variables:

    ```
    NEO4J_URI=<your-neo4j-uri>
    NEO4J_USER=<your-neo4j-username>
    NEO4J_PASSWORD=<your-neo4j-password>
    SECRET_KEY=<your-secret-key>
    ```

4. **Run the application:**
    For API:
    ```bash
    flask run
    
    ```
    For Web App:
    ```bash
    npm run start
    
    ```

5. **Access the API:**

    The API will be accessible at `http://localhost:5000`.

## Contributing

Contributions are welcome! If you'd like to contribute to the project, please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature-name`)
5. Create a new Pull Request
