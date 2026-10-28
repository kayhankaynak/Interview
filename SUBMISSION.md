# Product Catalog Backend

I created a simple REST API using Python and FastAPI. It supports creating, retrieving, updating, and deleting products. Clients can also list products, filter by category and price range, and paginate the results.

For the demonstration I used SQLite because it keeps the project easy to run. In a real environment I would use PostgreSQL. A relational database is a good fit because product data is structured, SKUs must be unique, and the main queries filter predictable fields such as category and price.

The database includes indexes for category and price. Prices are stored as integer cents to avoid rounding issues. Pagination limits the amount of data returned in each request, and the maximum page size is 100.

For basic scaling, the API can run as multiple instances behind a load balancer while PostgreSQL acts as the shared database. If read traffic grows significantly, I would consider caching popular products or adding read replicas. I would only add those components when monitoring shows they are needed.

I intentionally kept the implementation small and easy to explain. It demonstrates the required API behavior and sensible design choices without presenting itself as a complete production system.
