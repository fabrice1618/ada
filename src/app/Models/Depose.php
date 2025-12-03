<?php

/**
 * Depose Model
 *
 * Represents a student submission (depose) in the system.
 */
class Depose extends Model
{
    /**
     * The table associated with the model
     *
     * @var string
     */
    protected string $table = 'deposes';

    /**
     * The primary key for the model
     *
     * @var string
     */
    protected string $primaryKey = 'iddeposes';

    /**
     * The attributes that are mass assignable
     *
     * @var array
     */
    protected array $fillable = [
        'nom',
        'prenom',
        'datedepot',
        'url',
        'nomfichieroriginal',
        'nomfichierstockage',
        'iddevoirs'
    ];

    /**
     * Get all submissions for a specific devoir
     *
     * @param int $idDevoir
     * @return array
     */
    public function getByDevoir(int $idDevoir): array
    {
        return $this->where('iddevoirs', $idDevoir);
    }

    /**
     * Get submissions by student name
     *
     * @param string $nom
     * @param string $prenom
     * @return array
     */
    public function getByStudent(string $nom, string $prenom): array
    {
        $sql = "SELECT * FROM {$this->table} WHERE nom = ? AND prenom = ? ORDER BY datedepot DESC";
        $stmt = $this->query($sql, [$nom, $prenom]);
        return $stmt ? $stmt->fetchAll() : [];
    }

    /**
     * Get the latest submissions
     *
     * @param int $limit
     * @return array
     */
    public function getLatest(int $limit = 10): array
    {
        $sql = "SELECT * FROM {$this->table} ORDER BY datedepot DESC LIMIT ?";
        $stmt = $this->query($sql, [$limit]);
        return $stmt ? $stmt->fetchAll() : [];
    }

    /**
     * Count submissions for a specific devoir
     *
     * @param int $idDevoir
     * @return int
     */
    public function countByDevoir(int $idDevoir): int
    {
        $sql = "SELECT COUNT(*) as count FROM {$this->table} WHERE iddevoirs = ?";
        $stmt = $this->query($sql, [$idDevoir]);

        if ($stmt) {
            $result = $stmt->fetch();
            return (int) ($result['count'] ?? 0);
        }

        return 0;
    }

    /**
     * Get submission with associated devoir information
     *
     * @param int $id
     * @return array|null
     */
    public function findWithDevoir(int $id): ?array
    {
        $sql = "SELECT d.*, dev.shortcode, dev.datelimite
                FROM {$this->table} d
                LEFT JOIN devoirs dev ON d.iddevoirs = dev.iddevoirs
                WHERE d.{$this->primaryKey} = ?
                LIMIT 1";
        $stmt = $this->query($sql, [$id]);

        if ($stmt) {
            $result = $stmt->fetch();
            return $result ?: null;
        }

        return null;
    }

    /**
     * Create a new submission with automatic timestamp
     *
     * @param array $data
     * @return int|false
     */
    public function createSubmission(array $data)
    {
        // Automatically set submission date if not provided
        if (!isset($data['datedepot'])) {
            $data['datedepot'] = date('Y-m-d H:i:s');
        }

        return $this->create($data);
    }
}
