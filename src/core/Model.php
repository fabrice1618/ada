<?php

/**
 * Base Model Class
 *
 * Provides database interaction methods for child models.
 * Implements basic CRUD operations with prepared statements for security.
 */
class Model
{
    /**
     * Database connection instance
     *
     * @var PDO
     */
    protected PDO $db;

    /**
     * Table name (must be set in child classes)
     *
     * @var string
     */
    protected string $table = '';

    /**
     * Primary key column name
     *
     * @var string
     */
    protected string $primaryKey = 'id';

    /**
     * Fillable fields for mass assignment protection
     *
     * @var array
     */
    protected array $fillable = [];

    /**
     * Enable automatic timestamps (created_at, updated_at)
     *
     * @var bool
     */
    protected bool $timestamps = false;

    /**
     * Constructor - initializes database connection
     */
    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    /**
     * Get the table name
     *
     * @return string
     */
    protected function getTable(): string
    {
        return $this->table;
    }

    /**
     * Execute a raw SQL query with parameter binding
     *
     * @param string $sql
     * @param array $params
     * @return PDOStatement|false
     */
    protected function query(string $sql, array $params = [])
    {
        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            return $stmt;
        } catch (PDOException $e) {
            error_log("Query error: " . $e->getMessage() . " | SQL: " . $sql);
            return false;
        }
    }

    /**
     * Execute INSERT/UPDATE/DELETE query
     *
     * @param string $sql
     * @param array $params
     * @return bool
     */
    protected function execute(string $sql, array $params = []): bool
    {
        try {
            $stmt = $this->db->prepare($sql);
            return $stmt->execute($params);
        } catch (PDOException $e) {
            error_log("Execute error: " . $e->getMessage() . " | SQL: " . $sql);
            return false;
        }
    }

    // ===========================================
    // SELECT OPERATIONS
    // ===========================================

    /**
     * Fetch all records from the table
     *
     * @return array
     */
    public function all(): array
    {
        $sql = "SELECT * FROM {$this->getTable()}";
        $stmt = $this->query($sql);
        return $stmt ? $stmt->fetchAll() : [];
    }

    /**
     * Find a record by primary key
     *
     * @param mixed $id
     * @return array|null
     */
    public function find($id): ?array
    {
        $sql = "SELECT * FROM {$this->getTable()} WHERE {$this->primaryKey} = ? LIMIT 1";
        $stmt = $this->query($sql, [$id]);

        if ($stmt) {
            $result = $stmt->fetch();
            return $result ?: null;
        }

        return null;
    }

    /**
     * Fetch the first record
     *
     * @return array|null
     */
    public function first(): ?array
    {
        $sql = "SELECT * FROM {$this->getTable()} LIMIT 1";
        $stmt = $this->query($sql);

        if ($stmt) {
            $result = $stmt->fetch();
            return $result ?: null;
        }

        return null;
    }

    /**
     * Simple WHERE clause (field = value)
     *
     * @param string $field
     * @param mixed $value
     * @return array
     */
    public function where(string $field, $value): array
    {
        $sql = "SELECT * FROM {$this->getTable()} WHERE {$field} = ?";
        $stmt = $this->query($sql, [$value]);
        return $stmt ? $stmt->fetchAll() : [];
    }

    /**
     * Find records by a specific field value
     *
     * @param string $field
     * @param mixed $value
     * @return array|null
     */
    public function findBy(string $field, $value): ?array
    {
        $sql = "SELECT * FROM {$this->getTable()} WHERE {$field} = ? LIMIT 1";
        $stmt = $this->query($sql, [$value]);

        if ($stmt) {
            $result = $stmt->fetch();
            return $result ?: null;
        }

        return null;
    }

    // ===========================================
    // INSERT OPERATIONS
    // ===========================================

    /**
     * Create a new record
     *
     * @param array $data
     * @return int|false Returns inserted ID on success, false on failure
     */
    public function create(array $data)
    {
        // Filter data to only fillable fields
        $data = $this->filterFillable($data);

        if (empty($data)) {
            error_log("Create failed: No fillable fields provided");
            return false;
        }

        // Add timestamps if enabled
        if ($this->timestamps) {
            $data['created_at'] = date('Y-m-d H:i:s');
            $data['updated_at'] = date('Y-m-d H:i:s');
        }

        // Build INSERT query
        $fields = array_keys($data);
        $placeholders = array_fill(0, count($fields), '?');

        $sql = sprintf(
            "INSERT INTO %s (%s) VALUES (%s)",
            $this->getTable(),
            implode(', ', $fields),
            implode(', ', $placeholders)
        );

        try {
            $stmt = $this->db->prepare($sql);
            $result = $stmt->execute(array_values($data));

            if ($result) {
                return (int) $this->db->lastInsertId();
            }

            return false;
        } catch (PDOException $e) {
            error_log("Create error: " . $e->getMessage());
            return false;
        }
    }

    // ===========================================
    // UPDATE OPERATIONS
    // ===========================================

    /**
     * Update a record by primary key
     *
     * @param mixed $id
     * @param array $data
     * @return int Number of affected rows
     */
    public function update($id, array $data): int
    {
        // Filter data to only fillable fields
        $data = $this->filterFillable($data);

        if (empty($data)) {
            error_log("Update failed: No fillable fields provided");
            return 0;
        }

        // Add updated_at timestamp if enabled
        if ($this->timestamps) {
            $data['updated_at'] = date('Y-m-d H:i:s');
        }

        // Build UPDATE query
        $fields = array_keys($data);
        $setClause = implode(' = ?, ', $fields) . ' = ?';

        $sql = sprintf(
            "UPDATE %s SET %s WHERE %s = ?",
            $this->getTable(),
            $setClause,
            $this->primaryKey
        );

        try {
            $stmt = $this->db->prepare($sql);
            // Add ID to the end of values array
            $values = array_values($data);
            $values[] = $id;

            $stmt->execute($values);
            return $stmt->rowCount();
        } catch (PDOException $e) {
            error_log("Update error: " . $e->getMessage());
            return 0;
        }
    }

    // ===========================================
    // DELETE OPERATIONS
    // ===========================================

    /**
     * Delete a record by primary key
     *
     * @param mixed $id
     * @return bool
     */
    public function delete($id): bool
    {
        $sql = "DELETE FROM {$this->getTable()} WHERE {$this->primaryKey} = ?";

        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute([$id]);
            return $stmt->rowCount() > 0;
        } catch (PDOException $e) {
            error_log("Delete error: " . $e->getMessage());
            return false;
        }
    }

    // ===========================================
    // QUERY BUILDER METHODS
    // ===========================================

    /**
     * Query builder state
     *
     * @var array
     */
    protected array $queryBuilder = [
        'select' => '*',
        'where' => [],
        'orderBy' => [],
        'limit' => null,
        'offset' => null,
    ];

    /**
     * Select specific columns
     *
     * @param string|array $columns Columns to select
     * @return self
     */
    public function select($columns): self
    {
        if (is_array($columns)) {
            $this->queryBuilder['select'] = implode(', ', $columns);
        } else {
            $this->queryBuilder['select'] = $columns;
        }
        return $this;
    }

    /**
     * Add WHERE condition
     *
     * @param string $field Field name
     * @param string $operator Comparison operator
     * @param mixed $value Value to compare
     * @return self
     */
    public function whereCondition(string $field, string $operator, $value): self
    {
        $this->queryBuilder['where'][] = [
            'field' => $field,
            'operator' => $operator,
            'value' => $value,
        ];
        return $this;
    }

    /**
     * Add ORDER BY clause
     *
     * @param string $column Column to order by
     * @param string $direction Direction (ASC or DESC)
     * @return self
     */
    public function orderBy(string $column, string $direction = 'ASC'): self
    {
        $direction = strtoupper($direction);
        if (!in_array($direction, ['ASC', 'DESC'])) {
            $direction = 'ASC';
        }
        $this->queryBuilder['orderBy'][] = "{$column} {$direction}";
        return $this;
    }

    /**
     * Add LIMIT clause
     *
     * @param int $limit Number of records to return
     * @return self
     */
    public function limit(int $limit): self
    {
        $this->queryBuilder['limit'] = $limit;
        return $this;
    }

    /**
     * Add OFFSET clause
     *
     * @param int $offset Number of records to skip
     * @return self
     */
    public function offset(int $offset): self
    {
        $this->queryBuilder['offset'] = $offset;
        return $this;
    }

    /**
     * Execute the query builder and get results
     *
     * @return array
     */
    public function get(): array
    {
        $sql = $this->buildQuery();
        $params = $this->buildParams();

        $stmt = $this->query($sql, $params);
        $results = $stmt ? $stmt->fetchAll() : [];

        // Reset query builder
        $this->resetQueryBuilder();

        return $results;
    }

    /**
     * Build SQL query from query builder state
     *
     * @return string
     */
    protected function buildQuery(): string
    {
        $sql = "SELECT {$this->queryBuilder['select']} FROM {$this->getTable()}";

        // Add WHERE clauses
        if (!empty($this->queryBuilder['where'])) {
            $whereClauses = [];
            foreach ($this->queryBuilder['where'] as $condition) {
                $whereClauses[] = "{$condition['field']} {$condition['operator']} ?";
            }
            $sql .= " WHERE " . implode(' AND ', $whereClauses);
        }

        // Add ORDER BY
        if (!empty($this->queryBuilder['orderBy'])) {
            $sql .= " ORDER BY " . implode(', ', $this->queryBuilder['orderBy']);
        }

        // Add LIMIT
        if ($this->queryBuilder['limit'] !== null) {
            $sql .= " LIMIT {$this->queryBuilder['limit']}";
        }

        // Add OFFSET
        if ($this->queryBuilder['offset'] !== null) {
            $sql .= " OFFSET {$this->queryBuilder['offset']}";
        }

        return $sql;
    }

    /**
     * Build parameters array for prepared statement
     *
     * @return array
     */
    protected function buildParams(): array
    {
        $params = [];
        foreach ($this->queryBuilder['where'] as $condition) {
            $params[] = $condition['value'];
        }
        return $params;
    }

    /**
     * Reset query builder state
     *
     * @return void
     */
    protected function resetQueryBuilder(): void
    {
        $this->queryBuilder = [
            'select' => '*',
            'where' => [],
            'orderBy' => [],
            'limit' => null,
            'offset' => null,
        ];
    }

    // ===========================================
    // HELPER METHODS
    // ===========================================

    /**
     * Filter data array to only include fillable fields
     *
     * @param array $data
     * @return array
     */
    protected function filterFillable(array $data): array
    {
        if (empty($this->fillable)) {
            return $data;
        }

        return array_intersect_key(
            $data,
            array_flip($this->fillable)
        );
    }

    /**
     * Count total records in table
     *
     * @return int
     */
    public function count(): int
    {
        $sql = "SELECT COUNT(*) as count FROM {$this->getTable()}";
        $stmt = $this->query($sql);

        if ($stmt) {
            $result = $stmt->fetch();
            return (int) ($result['count'] ?? 0);
        }

        return 0;
    }

    /**
     * Check if a record exists by primary key
     *
     * @param mixed $id
     * @return bool
     */
    public function exists($id): bool
    {
        return $this->find($id) !== null;
    }
}
