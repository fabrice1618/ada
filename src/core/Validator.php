<?php

/**
 * Validator Class
 *
 * Provides fluent validation for input data with 15+ built-in rules
 */
class Validator
{
    /**
     * @var array Data to validate
     */
    protected array $data;

    /**
     * @var array Validation rules
     */
    protected array $rules;

    /**
     * @var array Custom error messages
     */
    protected array $customMessages;

    /**
     * @var array Validation errors
     */
    protected array $errors = [];

    /**
     * @var array Default error messages
     */
    protected array $defaultMessages = [
        'required' => 'The :field field is required.',
        'email' => 'The :field must be a valid email address.',
        'min' => 'The :field must be at least :param characters.',
        'max' => 'The :field must not exceed :param characters.',
        'numeric' => 'The :field must be a number.',
        'integer' => 'The :field must be an integer.',
        'alpha' => 'The :field must contain only letters.',
        'alphanumeric' => 'The :field must contain only letters and numbers.',
        'url' => 'The :field must be a valid URL.',
        'match' => 'The :field must match :param.',
        'in' => 'The :field must be one of: :param.',
        'regex' => 'The :field format is invalid.',
        'unique' => 'The :field has already been taken.',
        'exists' => 'The selected :field is invalid.',
        'confirmed' => 'The :field confirmation does not match.',
    ];

    /**
     * Constructor
     *
     * @param array $data Data to validate
     * @param array $rules Validation rules
     * @param array $customMessages Custom error messages
     */
    public function __construct(array $data, array $rules, array $customMessages = [])
    {
        $this->data = $data;
        $this->rules = $rules;
        $this->customMessages = $customMessages;
    }

    /**
     * Create a new validator instance
     *
     * @param array $data Data to validate
     * @param array $rules Validation rules
     * @param array $customMessages Custom error messages
     * @return Validator
     */
    public static function make(array $data, array $rules, array $customMessages = []): Validator
    {
        return new static($data, $rules, $customMessages);
    }

    /**
     * Validate the data
     *
     * @return bool True if validation passes
     */
    public function validate(): bool
    {
        $this->errors = [];

        foreach ($this->rules as $field => $rulesString) {
            // Parse rules for this field
            $rules = $this->parseRules($rulesString);

            foreach ($rules as $rule) {
                list($ruleName, $parameters) = $this->parseRule($rule);

                // Get the value
                $value = $this->data[$field] ?? null;

                // Call validation method
                $method = 'validate' . ucfirst($ruleName);

                if (!method_exists($this, $method)) {
                    throw new Exception("Validation rule '{$ruleName}' does not exist.");
                }

                $passes = $this->$method($field, $value, $parameters);

                if (!$passes) {
                    $this->addError($field, $ruleName, $parameters);
                    break; // Stop validating this field on first failure
                }
            }
        }

        return empty($this->errors);
    }

    /**
     * Parse rules string into array
     *
     * @param string $rulesString Rules string (e.g., "required|email|min:5")
     * @return array
     */
    protected function parseRules(string $rulesString): array
    {
        return explode('|', $rulesString);
    }

    /**
     * Parse a single rule into name and parameters
     *
     * @param string $rule Rule string (e.g., "min:5" or "required")
     * @return array [ruleName, parameters]
     */
    protected function parseRule(string $rule): array
    {
        if (strpos($rule, ':') !== false) {
            list($ruleName, $params) = explode(':', $rule, 2);
            $parameters = explode(',', $params);
        } else {
            $ruleName = $rule;
            $parameters = [];
        }

        return [$ruleName, $parameters];
    }

    /**
     * Add an error message
     *
     * @param string $field Field name
     * @param string $rule Rule name
     * @param array $parameters Rule parameters
     * @return void
     */
    protected function addError(string $field, string $rule, array $parameters): void
    {
        $message = $this->getMessage($field, $rule, $parameters);

        if (!isset($this->errors[$field])) {
            $this->errors[$field] = [];
        }

        $this->errors[$field][] = $message;
    }

    /**
     * Get error message for a rule
     *
     * @param string $field Field name
     * @param string $rule Rule name
     * @param array $parameters Rule parameters
     * @return string
     */
    protected function getMessage(string $field, string $rule, array $parameters): string
    {
        // Check for custom message
        $key = "{$field}.{$rule}";
        if (isset($this->customMessages[$key])) {
            $message = $this->customMessages[$key];
        } elseif (isset($this->customMessages[$rule])) {
            $message = $this->customMessages[$rule];
        } else {
            $message = $this->defaultMessages[$rule] ?? 'The :field is invalid.';
        }

        // Replace placeholders
        $message = str_replace(':field', $this->formatFieldName($field), $message);
        $message = str_replace(':param', implode(', ', $parameters), $message);

        return $message;
    }

    /**
     * Format field name for display
     *
     * @param string $field Field name
     * @return string
     */
    protected function formatFieldName(string $field): string
    {
        return ucfirst(str_replace('_', ' ', $field));
    }

    /**
     * Check if validation failed
     *
     * @return bool
     */
    public function fails(): bool
    {
        return !empty($this->errors);
    }

    /**
     * Check if validation passed
     *
     * @return bool
     */
    public function passes(): bool
    {
        return empty($this->errors);
    }

    /**
     * Get all errors
     *
     * @return array
     */
    public function errors(): array
    {
        return $this->errors;
    }

    /**
     * Get errors for a specific field
     *
     * @param string $field Field name
     * @return array
     */
    public function error(string $field): array
    {
        return $this->errors[$field] ?? [];
    }

    /**
     * Get the first error for a field
     *
     * @param string $field Field name
     * @return string|null
     */
    public function first(string $field): ?string
    {
        return $this->errors[$field][0] ?? null;
    }

    // ==================== VALIDATION RULES ====================

    /**
     * Validate required field
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateRequired(string $field, $value, array $parameters): bool
    {
        if (is_null($value)) {
            return false;
        }

        if (is_string($value) && trim($value) === '') {
            return false;
        }

        if (is_array($value) && empty($value)) {
            return false;
        }

        return true;
    }

    /**
     * Validate email address
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateEmail(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true; // Use 'required' rule for mandatory fields
        }

        return filter_var($value, FILTER_VALIDATE_EMAIL) !== false;
    }

    /**
     * Validate minimum length or value
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateMin(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        $min = (int) $parameters[0];

        if (is_numeric($value)) {
            return $value >= $min;
        }

        return mb_strlen($value) >= $min;
    }

    /**
     * Validate maximum length or value
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateMax(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        $max = (int) $parameters[0];

        if (is_numeric($value)) {
            return $value <= $max;
        }

        return mb_strlen($value) <= $max;
    }

    /**
     * Validate numeric value
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateNumeric(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        return is_numeric($value);
    }

    /**
     * Validate integer value
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateInteger(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        return filter_var($value, FILTER_VALIDATE_INT) !== false;
    }

    /**
     * Validate alphabetic characters only
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateAlpha(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        return preg_match('/^[a-zA-Z]+$/', $value) === 1;
    }

    /**
     * Validate alphanumeric characters only
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateAlphanumeric(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        return preg_match('/^[a-zA-Z0-9]+$/', $value) === 1;
    }

    /**
     * Validate URL
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateUrl(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        return filter_var($value, FILTER_VALIDATE_URL) !== false;
    }

    /**
     * Validate field matches another field
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters (other field name)
     * @return bool
     */
    protected function validateMatch(string $field, $value, array $parameters): bool
    {
        if (empty($parameters)) {
            return false;
        }

        $otherField = $parameters[0];
        $otherValue = $this->data[$otherField] ?? null;

        return $value === $otherValue;
    }

    /**
     * Validate value is in a list
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters (list of allowed values)
     * @return bool
     */
    protected function validateIn(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        return in_array($value, $parameters);
    }

    /**
     * Validate value matches regex pattern
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters (regex pattern)
     * @return bool
     */
    protected function validateRegex(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        if (empty($parameters)) {
            return false;
        }

        $pattern = $parameters[0];
        return preg_match($pattern, $value) === 1;
    }

    /**
     * Validate value is unique in database
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters (table, column, except_id)
     * @return bool
     */
    protected function validateUnique(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        if (count($parameters) < 2) {
            throw new Exception("Unique rule requires table and column parameters.");
        }

        $table = $parameters[0];
        $column = $parameters[1];
        $exceptId = $parameters[2] ?? null;

        try {
            $db = Database::getInstance()->getConnection();

            $sql = "SELECT COUNT(*) FROM {$table} WHERE {$column} = ?";
            $params = [$value];

            if ($exceptId !== null) {
                $sql .= " AND id != ?";
                $params[] = $exceptId;
            }

            $stmt = $db->prepare($sql);
            $stmt->execute($params);
            $count = $stmt->fetchColumn();

            return $count == 0;
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Validate value exists in database
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters (table, column)
     * @return bool
     */
    protected function validateExists(string $field, $value, array $parameters): bool
    {
        if (is_null($value) || $value === '') {
            return true;
        }

        if (count($parameters) < 2) {
            throw new Exception("Exists rule requires table and column parameters.");
        }

        $table = $parameters[0];
        $column = $parameters[1];

        try {
            $db = Database::getInstance()->getConnection();

            $sql = "SELECT COUNT(*) FROM {$table} WHERE {$column} = ?";
            $stmt = $db->prepare($sql);
            $stmt->execute([$value]);
            $count = $stmt->fetchColumn();

            return $count > 0;
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Validate confirmed field (e.g., password_confirmation)
     *
     * @param string $field Field name
     * @param mixed $value Field value
     * @param array $parameters Rule parameters
     * @return bool
     */
    protected function validateConfirmed(string $field, $value, array $parameters): bool
    {
        $confirmationField = $field . '_confirmation';
        $confirmationValue = $this->data[$confirmationField] ?? null;

        return $value === $confirmationValue;
    }
}
