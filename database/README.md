# Database Directory Structure

This directory contains all database-related files organized as follows:

```
database/
├── init.sql                    # Main database initialization script
├── performance_indexes.sql     # Performance optimization indexes
├── dumps/                      # Database dump files (organized by date)
│   └── YYYY-MM-DD/             # Dated subdirectories
├── serbian-vocabulary-app/     # Serbian vocabulary specific configurations
│   └── [existing SQL files]
└── migrations/                 # Database migration scripts (if applicable)
```

## Maintenance Guidelines

- **Dumps**: Create weekly backups using `pg_dump`
- **Migrations**: Use timestamped SQL files (e.g. 20240807-1430-add-users-table.sql)
- **Schema Changes**: Update init.sql and create matching migration
