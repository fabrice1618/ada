<?php

/**
 * User Model
 *
 * Represents a user in the system.
 */
class User extends Model
{
    /**
     * The table associated with the model
     *
     * @var string
     */
    protected string $table = 'users';

    /**
     * The primary key for the model
     *
     * @var string
     */
    protected string $primaryKey = 'id';

    /**
     * The attributes that are mass assignable
     *
     * @var array
     */
    protected array $fillable = [
        'username',
        'email'
    ];

    /**
     * Enable automatic timestamps
     * Note: Set to false because users table doesn't have timestamp columns yet
     *
     * @var bool
     */
    protected bool $timestamps = false;

    /**
     * Find a user by username
     *
     * @param string $username
     * @return array|null
     */
    public function findByUsername(string $username): ?array
    {
        return $this->findBy('username', $username);
    }

    /**
     * Find a user by email
     *
     * @param string $email
     * @return array|null
     */
    public function findByEmail(string $email): ?array
    {
        return $this->findBy('email', $email);
    }

    /**
     * Check if a username already exists
     *
     * @param string $username
     * @return bool
     */
    public function usernameExists(string $username): bool
    {
        return $this->findByUsername($username) !== null;
    }

    /**
     * Check if an email already exists
     *
     * @param string $email
     * @return bool
     */
    public function emailExists(string $email): bool
    {
        return $this->findByEmail($email) !== null;
    }
}
