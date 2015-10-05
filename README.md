
SGSchema
========

This project aims to assist interaction with Shotgun via its API by applying knowledge of the server's schema.

The initial use case is to assist tool developers in being able to operate on Shotgun instances with slightly different schemas. Differences can accrue due to human mistakes while creating fields, or due to the initial schemas being different across the history of Shotgun.

You may provide aliases and tags for entity types and fields, as well as automatically detect and use the common ``"sg_"`` prefix on fields.

This project is tightly integrated into [SGSession](https://github.com/westernx/sgsession), and used in all operations.
