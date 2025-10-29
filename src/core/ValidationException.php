<?php

/**
 * Validation Exception
 *
 * Thrown when validation fails and carries a redirect response
 */
class ValidationException extends Exception
{
    /**
     * @var Response Redirect response with flashed errors
     */
    protected Response $response;

    /**
     * Constructor
     *
     * @param Response $response Redirect response
     * @param string $message Exception message
     * @param int $code Exception code
     * @param Throwable|null $previous Previous exception
     */
    public function __construct(Response $response, string $message = 'Validation failed', int $code = 0, Throwable $previous = null)
    {
        parent::__construct($message, $code, $previous);
        $this->response = $response;
    }

    /**
     * Get the redirect response
     *
     * @return Response
     */
    public function getResponse(): Response
    {
        return $this->response;
    }
}
