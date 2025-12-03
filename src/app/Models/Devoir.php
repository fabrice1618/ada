<?php

/**
 * Devoir Model
 *
 * Represents an assignment (devoir) in the system.
 */
class Devoir extends Model
{
    /**
     * The table associated with the model
     *
     * @var string
     */
    protected string $table = 'devoirs';

    /**
     * The primary key for the model
     *
     * @var string
     */
    protected string $primaryKey = 'iddevoirs';

    /**
     * The attributes that are mass assignable
     *
     * @var array
     */
    protected array $fillable = [
        'shortcode',
        'datelimite'
    ];

    /**
     * Find a devoir by shortcode
     *
     * @param string $shortcode
     * @return array|null
     */
    public function findByShortcode(string $shortcode): ?array
    {
        return $this->findBy('shortcode', $shortcode);
    }

    /**
     * Get all devoirs with a deadline after a specific date
     *
     * @param string $date Date in Y-m-d format
     * @return array
     */
    public function getUpcoming(string $date = null): array
    {
        $date = $date ?? date('Y-m-d');
        $sql = "SELECT * FROM {$this->table} WHERE datelimite >= ? ORDER BY datelimite ASC";
        $stmt = $this->query($sql, [$date]);
        return $stmt ? $stmt->fetchAll() : [];
    }

    /**
     * Get all devoirs with a deadline before a specific date
     *
     * @param string $date Date in Y-m-d format
     * @return array
     */
    public function getPast(string $date = null): array
    {
        $date = $date ?? date('Y-m-d');
        $sql = "SELECT * FROM {$this->table} WHERE datelimite < ? ORDER BY datelimite DESC";
        $stmt = $this->query($sql, [$date]);
        return $stmt ? $stmt->fetchAll() : [];
    }

    /**
     * Check if a devoir is still open (deadline not passed)
     *
     * @param int $id
     * @return bool
     */
    public function isOpen(int $id): bool
    {
        $devoir = $this->find($id);
        if (!$devoir) {
            return false;
        }

        return strtotime($devoir['datelimite']) >= strtotime(date('Y-m-d'));
    }
}
